"""Equations and explicit interfaces for Kroll & Schulte (2014).

Reference: doi:10.1016/j.asoc.2014.08.034. See benchmarks/README.md for
state order, units, reproducibility limits, and corrections to printed tables.
No simulator silently replaces an unavailable industrial benchmark.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable
import hashlib
import json
import subprocess
import numpy as np


def _vector(value, n, name):
    value = np.asarray(value, dtype=float)
    if value.shape != (n,) or not np.all(np.isfinite(value)):
        raise ValueError(f"{name} must be a finite vector of length {n}")
    return value


def siso_step(y, y_previous, u):
    """Eq. (30): returns y[k+1], given y[k], y[k-1], u[k]."""
    return y * y_previous * (y + 2.5) / (1 + y*y*y_previous*y_previous) + u


def mimo_step(y, u):
    """Eq. (31); input/output order is [channel 1, channel 2]."""
    y, u = _vector(y, 2, "y"), _vector(u, 2, "u")
    return np.array([y[0], y[0]*y[1]]) / (1 + y[1]**2) + u


def artificial_data(n=1000, kind="siso", signal="train", seed=2014):
    """Synthetic Eq. (30)/(31) records; paper training size is 100000.

    y has n+1 rows; u[k] advances y[k] to y[k+1]. Initial states/history
    are zero (an explicit repository choice, not specified in the paper).
    """
    if not isinstance(n, (int, np.integer)) or n < 1:
        raise ValueError("n must be a positive integer")
    if kind not in {"siso", "mimo"} or signal not in {"train", "validation"}:
        raise ValueError("kind: siso/mimo; signal: train/validation")
    channels = 1 if kind == "siso" else 2
    rng = np.random.default_rng(seed)
    k = np.arange(n)
    if signal == "train":
        bound = 2 if kind == "siso" else 1
        u = rng.uniform(-bound, bound, (n, channels))
    else:
        u = np.sin(2*np.pi*k/25)[:, None]
        if kind == "mimo":
            u = np.column_stack([u[:, 0], np.cos(2*np.pi*k/25)])
    y = np.zeros((n+1, channels))
    for i in range(n):
        y[i+1] = (siso_step(y[i, 0], y[i-1, 0] if i else 0., u[i, 0])
                  if kind == "siso" else mimo_step(y[i], u[i]))
    return u, y


@dataclass(frozen=True)
class PendulumParameters:
    """Table 3 cart/pendulum parameters with explicit SI conventions.

    ``m`` and ``M`` are pendulum and cart masses in kg; ``l`` is the
    characteristic length in m used by the published equation, not an
    independently inferred rod geometry. ``joint_friction`` multiplies angular
    velocity in the joint torque (N m s), ``cart_coulomb`` is force in N,
    ``g`` is acceleration in m/s² and ``force_limit`` is the actuator bound in N.
    The field is evaluated by `pendulum_rhs`; rail impacts and stiction are absent.
    """
    m: float = 0.356
    M: float = 4.8
    l: float = 0.56
    joint_friction: float = 0.035
    cart_coulomb: float = 4.9
    g: float = 9.81
    force_limit: float = 120.


def pendulum_rhs(t, x, u, p=PendulumParameters()):
    """Eq. (32); x=[theta, theta_dot, cart_position, cart_velocity], SI.

    theta=0 is upright. Force saturation is explicit. The printed Coulomb
    sign law has sign(0)=0 and does not model sticking or rail impacts.
    """
    theta, omega, _, velocity = _vector(x, 4, "x")
    if min(p.m, p.M, p.l) <= 0:
        raise ValueError("m, M and l must be positive")
    force = np.clip(float(u), -p.force_limit, p.force_limit)
    friction = p.cart_coulomb*np.sign(velocity)
    a = 1/(p.m+p.M)
    s, c = np.sin(theta), np.cos(theta)
    ddtheta = (p.g*s - p.m*p.l*a*omega**2*c*s - a*c*(force-friction)
               - p.joint_friction*omega/(p.m*p.l))/(2*p.l-p.m*p.l*a*c*c)
    ddx = 2*a/(2-p.m*a*c*c)*(p.m*p.l*omega**2*s - .5*p.m*p.g*c*s
                            + force-friction + c*p.joint_friction*omega/(2*p.l))
    return np.array([omega, ddtheta, velocity, ddx])


def pneumatic_rhs(t, x, mass_flows, *, load_mass=3., kappa=1.4,
                  gas_constant=8.314, temperature=293.15):
    """Eqs. (33)-(34): x=[position,velocity,pI,pII], SI.

    mass_flows=[m1,m2,m3,m4,mbp] in kg/s, with the signs of Eq. (33).
    Valve equations are NOT supplied in the article. Kappa=1.4 is a
    documented ideal-air closure. The printed Rg=8.314 is dimensionally
    suspect for kg-based flow; pass 287.05 for a specific-air-gas variant.
    Eq. (33) omits a gravitational load despite the vertical schematic;
    no hidden gravity compensation is introduced here.
    """
    pos, vel, p1, p2 = _vector(x, 4, "x")
    m1, m2, m3, m4, mbp = _vector(mass_flows, 5, "mass_flows")
    area, volume = 2.8e-3, 5e-4
    if abs(pos) > .125 or min(p1,p2) <= 0 or load_mass <= 0:
        raise ValueError("pneumatic state/load outside admissible range")
    friction = 135*vel + 21*np.sign(vel)
    acc = (area*(p1-p2)-friction)/(load_mass+2.9)
    dp1 = kappa*(gas_constant*temperature*(m2-m1-mbp)-area*p1*vel)/(volume+area*pos)
    dp2 = kappa*(-gas_constant*temperature*(m4-m3-mbp)+area*p2*vel)/(volume-area*pos)
    return np.array([vel, acc, dp1, dp2])


def educational_valve_flows(voltage, p1, p2, conductance=1e-8):
    """Explicit linear mass-flow closure for practice, NOT the benchmark valve.

    Positive voltage fills I and empties II. Conductance has kg/(s Pa V).
    This deliberately simple closure omits choking and compressibility
    within the valve, and cannot validate the published pneumatic results.
    """
    v = float(np.clip(voltage, -10, 10))
    supply, exhaust = 9e5, 1e5
    if v >= 0:
        return np.array([0, conductance*v*max(supply-p1,0), 0,
                         conductance*v*max(p2-exhaust,0), 0])
    return np.array([conductance*(-v)*max(p1-exhaust,0), 0,
                     conductance*(-v)*max(supply-p2,0), 0, 0])


def hydrostatic_rhs(t, x, u, *, pump_speed, wheel_load=0.):
    """Literal numerical transcription of Eq. (35) and Table 5.

    x=[pump_angle,motor_angle,pressure_difference,motor_speed]. The paper
    mixes pressure/volume units and gains incompatible with its normalized
    angle bounds. This routine is a transcription exercise, not a validated
    SI simulator. Callers must report that qualification with any output.
    The final torque term follows printed V_P^max, not an unannounced V_M.
    """
    a_p, a_m, dp, omega = _vector(x,4,"x")
    u_p, u_m = _vector(u,2,"u")
    return np.array([
        (-a_p+241.67*u_p)/.13,
        (-a_m+283.33*u_m)/.22,
        10/1840.8*(145*a_p*pump_speed-170*a_m*omega-.14*dp),
        ((-6.12)**2*(-23.3)**2*.98*.697*145e-4*a_m*dp
         -.33*(-23.3)**2*omega-wheel_load*(-6.12)*(-23.3))/16512])


def three_tank_rhs(t, x, u, *, outlet_openings=(0.,0.,0.)):
    """Eq. (36), with optional explicitly marked drain/fault extension.

    x=[h1,h2,h3] m; u=[q1,q2] m3/s; time in seconds. All drains are closed
    for the paper's nominal equation. Area table units are corrected to m2.
    """
    h = _vector(x,3,"x")
    flow = _vector(u,2,"u")
    opening = _vector(outlet_openings,3,"outlet_openings")
    if np.any(h < 0) or np.any(h > .62) or np.any(flow < 0) or np.any(flow > 1e-4):
        raise ValueError("tank levels or pump flows outside Table 6 limits")
    if np.any(opening < 0) or np.any(opening > 1):
        raise ValueError("outlet openings must be in [0,1]")
    def q(d):
        return .5e-4*.48*np.sign(d)*np.sqrt(2*9.81*abs(d))
    q13, q32 = q(h[0]-h[2]), q(h[2]-h[1])
    drain = opening*.5e-4*.56*np.sqrt(2*9.81*h)
    return (np.array([-q13+flow[0], q32+flow[1], q13-q32])-drain)/.0154


def bioreactor_rhs(t, x, u, *, gamma=.4, beta=.02):
    """Eq. (37); state=[dimensionless biomass, substrate conversion]."""
    c1,c2 = _vector(x,2,"x")
    if gamma <= 0 or beta <= 0 or not (0 <= c1 <= 1 and 0 <= c2 <= 1):
        raise ValueError("bioreactor state/parameters outside physical domain")
    if u < 0:
        raise ValueError("feed flow cannot be negative")
    growth = c1*(1-c2)*np.exp(c2/gamma)
    return np.array([-c1*u+growth, -c2*u+growth*(1+beta)/(1+beta-c2)])


def bioreactor_sample(x, u, *, gamma=.4, beta=.02):
    """Paper's sampled model: FIFTY Euler steps of .01 per .5-unit hold."""
    state = _vector(x,2,"x").copy()
    for _ in range(50):
        state += .01*bioreactor_rhs(0,state,u,gamma=gamma,beta=beta)
    return state


CSTR_SP1 = np.array([3517.5,740.,87.,79.8])
CSTR_SP2 = np.array([2985.,960.,106.,100.7])
CSTR_U1 = np.array([8.256,-6.239])
CSTR_U2 = np.array([18.037,-4.556])


def cstr_rhs(t, x, u, *, feed_concentration=5100., gamma=.1):
    """Eqs. (39)-(43): x=[cA,cB,T,Tc], mol/m3 and degrees C; t in hours.

    u=[q/VR in h^-1, cooling in MJ/h]. Multiplication by 1000 converts
    MJ/h to kJ/h before the coolant balance. Printed temperature labels K
    contradict Eq. (41); Celsius is consistent with its +273.15 conversion.
    """
    ca,cb,temp,coolant = _vector(x,4,"x")
    dilution,cooling = _vector(u,2,"u")
    if temp <= -273.15 or coolant <= -273.15 or min(ca,cb,feed_concentration) < 0:
        raise ValueError("invalid CSTR state or feed")
    if not (5 <= dilution <= 35 and -8.5 <= cooling <= 0):
        raise ValueError("CSTR input outside Eqs. (42)-(43)")
    k1=1.287e12*np.exp(-9758.3/(temp+273.15))
    k2=9.043e6*np.exp(-8560/(temp+273.15))
    heat=-3.556e-4*(k1*(ca*4.2+cb*(-11.))+k2*ca*ca*(-41.85))
    return np.array([-k1*ca-k2*ca*ca+(feed_concentration-ca)*dilution,
                     k1*(ca-cb)-cb*dilution,
                     heat+30.8285*(coolant-temp)+(104.9-temp)*dilution,
                     86.688*(temp-coolant)+gamma*cooling*1000])


def column_a_rhs(t, state, inputs=(2.70629,3.20629,.5,.5,1.,.5,1.)):
    """82-state Column A balances, closed using NTNU's reference parameters.

    State is [x1..x41,M1..M41]; inputs=[L,V,D,B,F,zF,qF]. Time is min,
    flows kmol/min, holdups kmol, compositions mole fractions. The nominal
    reflux/boilup use NTNU precision (2.70629/3.20629) rather than rounded
    Table 9 values. Eq. (47)'s V[i+1] is corrected to V[i-1], consistent
    with Eqs. (48),(52) and the official colamod.m implementation.
    """
    state = _vector(state,82,"state")
    reflux,boilup,distillate,bottoms,feed,zf,qf = _vector(inputs,7,"inputs")
    x,m = state[:41],state[41:]
    if np.any(m <= 0) or np.any(x < 0) or np.any(x > 1):
        raise ValueError("Column A requires positive holdups and compositions in [0,1]")
    if min(reflux,boilup,distillate,bottoms,feed) < 0 or not (0<=zf<=1 and 0<=qf<=1):
        raise ValueError("invalid Column A feed or product flows")
    vapor=1.5*x[:-1]/(1+.5*x[:-1])
    v=np.full(40,boilup); v[20:] += (1-qf)*feed
    liquid=np.zeros(41)
    liquid[1:21]=3.70629+(m[1:21]-.5)/.063
    liquid[21:40]=2.70629+(m[21:40]-.5)/.063
    liquid[40]=reflux
    dm=np.zeros(41); dmx=np.zeros(41)
    for i in range(1,40):
        dm[i]=liquid[i+1]-liquid[i]+v[i-1]-v[i]
        dmx[i]=liquid[i+1]*x[i+1]-liquid[i]*x[i]+v[i-1]*vapor[i-1]-v[i]*vapor[i]
    dm[20]+=feed; dmx[20]+=feed*zf
    dm[0]=liquid[1]-v[0]-bottoms
    dmx[0]=liquid[1]*x[1]-v[0]*vapor[0]-bottoms*x[0]
    dm[-1]=v[-1]-reflux-distillate
    dmx[-1]=v[-1]*vapor[-1]-(reflux+distillate)*x[-1]
    return np.concatenate(((dmx-x*dm)/m,dm))


def column_a_lv_rhs(t,state,inputs=(2.70629,3.20629,1.,.5,1.),level_gain=10.):
    """LV configuration: D and B regulate holdups; L and V remain free.

    inputs=[L,V,F,zF,qF]. P level controllers and nonnegative outflows
    follow a documented educational configuration (gain 10 min^-1).
    """
    state=_vector(state,82,"state"); L,V,F,zF,qF=_vector(inputs,5,"inputs")
    D=max(0,.5+level_gain*(state[-1]-.5))
    B=max(0,.5+level_gain*(state[41]-.5))
    return column_a_rhs(t,state,[L,V,D,B,F,zF,qF])


def wind_matrices():
    """Eq. (56), using Table 10 and generator quantities at low-speed side."""
    mt,mb,n,jr,jg=436865.,4435.,3,38759227.,5025347.
    M=np.diag([mt+n*mb,n*mb,jr,jg]); M[0,1]=M[1,0]=n*mb
    D=np.diag([7e4,n*2e4,6215000.,6215000.]); D[2,3]=D[3,2]=-6215000.
    K=np.diag([1981900.,n*40000.,867637000.,867637000.]); K[2,3]=K[3,2]=-867637000.
    return M,D,K


class RotorMap:
    """Bilinear interpolation of a ROSCO rotor table, rejecting extrapolation.

    Parameters
    ----------
    path : path-like
        ROSCO text table containing pitch in degrees, tip-speed ratios, and
        power/thrust/torque coefficient matrices. The repository's later NREL
        5 MW map is under ``benchmarks/data``; it is not the recovered 2014 map.

    Notes
    -----
    Calling the instance with ``(tip_speed_ratio, pitch_radians)`` returns
    ``(CT, CQ)``. Both coordinates must stay within the table. ``sha256`` records
    the exact input bytes; ``cp``, ``ct`` and ``cq`` retain the coefficient grids.
    """
    def __init__(self, path):
        lines=Path(path).read_text(encoding="utf-8").splitlines()
        numeric=[np.fromstring(line,sep=" ") for line in lines if line.strip() and not line.lstrip().startswith("#")]
        self.pitch,self.tsr=numeric[0],numeric[1]
        rows=len(self.tsr)
        self.cp=np.vstack(numeric[3:3+rows])
        self.ct=np.vstack(numeric[3+rows:3+2*rows])
        self.cq=np.vstack(numeric[3+2*rows:3+3*rows])
        if any(z.shape!=(rows,len(self.pitch)) for z in [self.cp,self.ct,self.cq]):
            raise ValueError("invalid rotor-map dimensions")
        self.sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest()

    def __call__(self, tip_speed_ratio, pitch_radians):
        p=float(np.rad2deg(pitch_radians)); r=float(tip_speed_ratio)
        if not (self.pitch[0]<=p<=self.pitch[-1] and self.tsr[0]<=r<=self.tsr[-1]):
            raise ValueError("rotor operating point outside tabulated map; extrapolation forbidden")
        j=min(np.searchsorted(self.pitch,p,side="right")-1,len(self.pitch)-2)
        i=min(np.searchsorted(self.tsr,r,side="right")-1,len(self.tsr)-2)
        a=(r-self.tsr[i])/(self.tsr[i+1]-self.tsr[i]); b=(p-self.pitch[j])/(self.pitch[j+1]-self.pitch[j])
        def interp(z):
            return float((1-a)*((1-b)*z[i,j]+b*z[i,j+1])+a*((1-b)*z[i+1,j]+b*z[i+1,j+1]))
        return interp(self.ct),interp(self.cq)


def wind_rhs(t,state,inputs,aero_map):
    """Eqs. (55)-(58); state=[q(4),qdot(4),pitch], inputs=[wind,Tg,pitch_d].

    q=[tower deflection,relative blade-tip deflection,rotor angle,generator
    angle]; aero_map(lambda,beta) returns (CT,CQ). Pitch angles are radians.
    The bundled ROSCO map makes a documented later-map variant runnable.
    """
    state=_vector(state,9,"state"); wind,torque,pitch_d=_vector(inputs,3,"inputs")
    q,vel,beta=state[:4],state[4:8],state[8]
    veff=wind-vel[0]-vel[1]
    if veff<=0:
        raise ValueError("effective wind must be positive")
    ct,cq=aero_map(vel[2]*63/veff,beta)
    ft=.5*1.225*np.pi*63**2*ct*veff**2
    tr=.5*1.225*np.pi*63**3*cq*veff**2
    M,D,K=wind_matrices()
    acc=np.linalg.solve(M,np.array([ft,ft,tr,-torque])-D@vel-K@q)
    return np.r_[vel,acc,(pitch_d-beta)/.1]


def rk4(rhs,x0,dt,steps):
    """Fixed-step RK4 for short deterministic checks; no hidden clipping."""
    if dt<=0 or steps<1:
        raise ValueError("dt and steps must be positive")
    x=np.asarray(x0,dtype=float).copy(); result=[x.copy()]
    for i in range(steps):
        t=i*dt
        a=rhs(t,x); b=rhs(t+dt/2,x+dt*a/2)
        c=rhs(t+dt/2,x+dt*b/2); d=rhs(t+dt,x+dt*c)
        x=x+dt*(a+2*b+2*c+d)/6
        if not np.all(np.isfinite(x)):
            raise FloatingPointError(f"integration diverged at step {i+1}")
        result.append(x.copy())
    return np.asarray(result)


def load_io_csv(path, input_columns, output_columns, sample_time):
    """Read a supplied measured dataset without inventing samples or units.

    CSV must have named columns, finite numbers, and at least two rows.
    Source URL, units and split provenance belong in the adjacent manifest.
    """
    if sample_time<=0:
        raise ValueError("sample time must be positive")
    data=np.genfromtxt(path,delimiter=",",names=True,encoding="utf-8")
    names=set(data.dtype.names or [])
    if not set(input_columns+output_columns)<=names:
        raise ValueError("required input/output CSV columns are missing")
    u=np.column_stack([np.atleast_1d(data[k]) for k in input_columns])
    y=np.column_stack([np.atleast_1d(data[k]) for k in output_columns])
    if len(u)<2 or not np.all(np.isfinite(u)) or not np.all(np.isfinite(y)):
        raise ValueError("CSV requires at least two complete finite observations")
    return np.arange(len(u))*sample_time,u,y


class LocalARX:
    """Eight-local-model throttle architecture from section 4.1.

    Local regressors are [y[k-1],y[k-2],u[k-1],1]. Partition features are
    [y[k-1]-y[k-2],u[k-1]], standardized on training records only. K-means
    nearest-centroid PWA or inverse-distance TS weighting is an explicit
    teaching fit, not the paper's unavailable fitted partition parameters.
    """
    def __init__(self, rules=8, mode="soft", ridge=1e-8, seed=2014):
        if rules<1 or mode not in {"soft","crisp"} or ridge<=0:
            raise ValueError("invalid LocalARX configuration")
        self.rules,self.mode,self.ridge,self.seed=rules,mode,ridge,seed

    def _weights(self,z):
        dist=((z[:,None,:]-self.centers[None,:,:])**2).sum(axis=2)
        if self.mode=="crisp":
            w=np.zeros_like(dist); w[np.arange(len(z)),dist.argmin(axis=1)]=1
        else:
            w=1/np.maximum(dist,1e-12); w/=w.sum(axis=1,keepdims=True)
        return w

    def fit(self,u,y):
        """Fit partitions and ridge-regression coefficients on training data only.

        Parameters
        ----------
        u, y : array-like
            Aligned finite input/output records with at least
            ``max(20, 5*rules)`` samples. Physical units are inherited from the
            supplied data; canonical throttle conventions are percent and degrees.

        Returns
        -------
        LocalARX
            This fitted instance. Feature means/scales, centers and local
            coefficients are retained. Underdetermined crisp regions use the
            global ridge fit. Call this method only with the training experiment.
        """
        u=np.asarray(u,dtype=float).reshape(-1); y=np.asarray(y,dtype=float).reshape(-1)
        if len(u)!=len(y) or len(y)<max(20,5*self.rules) or not np.isfinite(np.r_[u,y]).all():
            raise ValueError("aligned finite u/y records with >=5*rules samples required")
        phi=np.column_stack([y[1:-1],y[:-2],u[1:-1],np.ones(len(y)-2)])
        z=np.column_stack([y[1:-1]-y[:-2],u[1:-1]])
        self.mean=z.mean(axis=0); self.scale=np.maximum(z.std(axis=0),1e-12)
        z=(z-self.mean)/self.scale
        rng=np.random.default_rng(self.seed)
        self.centers=z[rng.choice(len(z),self.rules,replace=False)].copy()
        for _ in range(50):
            labels=((z[:,None]-self.centers[None,:])**2).sum(axis=2).argmin(axis=1)
            old=self.centers.copy()
            for j in range(self.rules):
                if np.any(labels==j): self.centers[j]=z[labels==j].mean(axis=0)
            if np.max(np.abs(old-self.centers))<1e-10: break
        weights=self._weights(z)
        global_coef=np.linalg.solve(phi.T@phi+self.ridge*np.eye(4),phi.T@y[2:])
        self.coefficients=[]
        for j in range(self.rules):
            w=weights[:,j]
            # Empty/underdetermined crisp regions use the documented global fit.
            coef=(np.linalg.solve(phi.T@(w[:,None]*phi)+self.ridge*np.eye(4),phi.T@(w*y[2:]))
                  if np.count_nonzero(w>1e-12)>=4 else global_coef.copy())
            self.coefficients.append(coef)
        self.coefficients=np.asarray(self.coefficients)
        return self

    def predict(self,u,y,recursive=False):
        """Predict a separate record using measured or recursively predicted history.

        Parameters
        ----------
        u, y : array-like
            Aligned finite records of at least three samples. The first two
            output samples seed the prediction and are copied unchanged.
        recursive : bool
            False uses measured output lags (one-step prediction). True uses
            predicted outputs after the two seeds (free-run evaluation).

        Returns
        -------
        numpy.ndarray
            Prediction with the same length and output units as ``y``. Exclude
            the first two seed samples from error scores. Partitions and
            coefficients remain fixed; this method does not refit on test data.
        """
        u=np.asarray(u,dtype=float).reshape(-1); y=np.asarray(y,dtype=float).reshape(-1)
        if len(u)!=len(y) or len(y)<3 or not np.isfinite(np.r_[u,y]).all():
            raise ValueError("u/y records must be finite, aligned and at least length 3")
        prediction=y.copy()
        for k in range(2,len(y)):
            history=prediction if recursive else y
            z=np.array([[history[k-1]-history[k-2],u[k-1]]])
            weights=self._weights((z-self.mean)/self.scale)[0]
            phi=np.array([history[k-1],history[k-2],u[k-1],1.])
            prediction[k]=weights@(self.coefficients@phi)
            if not np.isfinite(prediction[k]):
                raise FloatingPointError("recursive predictor diverged")
        return prediction


def run_external(command, cwd, expected_output, metadata, timeout=300):
    """Run an installed official simulator and record its provenance.

    command is an argument list, never a shell string. The model-specific
    launcher remains user-supplied (MATLAB, OpenFAST or a compiled TE driver).
    A successful process must create a fresh expected output file.
    """
    if isinstance(command,str) or not command:
        raise ValueError("command must be a nonempty argument list")
    required={"model","source_url","source_sha256","version","solver","sample_time","seed"}
    if not required<=set(metadata):
        raise ValueError("external run metadata is incomplete")
    directory=Path(cwd).resolve(); output=(directory/expected_output).resolve()
    if not output.is_relative_to(directory):
        raise ValueError("expected output must stay inside the run directory")
    if output.exists():
        raise FileExistsError("use a fresh run directory to avoid accepting stale output")
    result=subprocess.run(list(command),cwd=directory,capture_output=True,text=True,
                          timeout=timeout,check=True,shell=False)
    if not output.is_file():
        raise RuntimeError("simulator exited without its expected output")
    record=dict(metadata,command=list(command),output=output.name,
                output_sha256=hashlib.sha256(output.read_bytes()).hexdigest())
    (directory/(output.name+".provenance.json")).write_text(json.dumps(record,indent=2),encoding="utf-8")
    return result

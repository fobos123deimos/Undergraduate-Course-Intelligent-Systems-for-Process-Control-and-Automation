"""Explicit SI pneumatic variant; not a recovered canonical valve calibration.

State: [position m, velocity m/s, chamber masses kg, chamber temperatures K].
See benchmarks/PNEUMATIC_AUDIT.md for primary sources and added assumptions.
The literal survey transcription remains in benchmarks.pneumatic_rhs.
"""
from dataclasses import dataclass, asdict
import numpy as np
from scipy.integrate import solve_ivp


@dataclass(frozen=True)
class Parameters:
    area: float = 2.8e-3
    half_stroke: float = .125
    midpoint_volume: float = 5e-4
    piston_mass: float = 2.9
    load_mass: float = 3.
    viscous: float = 135.
    coulomb: float = 21.
    valve_gain: float = 1e-4
    voltage_limit: float = 10.
    supply_pressure: float = 9e5
    exhaust_pressure: float = 1e5
    reservoir_temperature: float = 293.15
    universal_R: float = 8.31446261815324
    air_molar_mass: float = .0289644
    gamma: float = 1.4
    gravity: float = 9.81
    # The following closure values are teaching assumptions, not identified data.
    port_width: float = .002
    discharge_coefficient: float = .7
    bypass_area: float = 0.
    friction_velocity: float = .005
    wall_conductance: float = 0.
    wall_temperature: float = 293.15

    def __post_init__(self):
        values=asdict(self)
        if any(not np.isfinite(x) for x in values.values()):
            raise ValueError('parameters must be finite')
        positive=['area','half_stroke','midpoint_volume','piston_mass','valve_gain',
                  'voltage_limit','supply_pressure','exhaust_pressure',
                  'reservoir_temperature','universal_R','air_molar_mass','port_width',
                  'discharge_coefficient','friction_velocity','wall_temperature']
        if any(values[k]<=0 for k in positive) or self.gamma<=1:
            raise ValueError('positive physical coefficients and gamma > 1 required')
        if any(values[k]<0 for k in ['load_mass','viscous','coulomb','bypass_area','wall_conductance']):
            raise ValueError('mass, friction, leakage and heat transfer must be nonnegative')
        if self.discharge_coefficient>1 or self.supply_pressure<=self.exhaust_pressure:
            raise ValueError('invalid discharge coefficient or reservoir pressures')
        if self.residual_volume<=0:
            raise ValueError('midpoint volume must leave positive end volumes')

    @property
    def R(self): return self.universal_R/self.air_molar_mass
    @property
    def cv(self): return self.R/(self.gamma-1)
    @property
    def cp(self): return self.gamma*self.cv
    @property
    def total_mass(self): return self.piston_mass+self.load_mass
    @property
    def residual_volume(self): return self.midpoint_volume-self.area*self.half_stroke


def orifice_flow(p_a,p_b,t_a,t_b,area,p=Parameters()):
    """Signed a->b kg/s; isentropic reservoir-orifice closure with sonic limit.

    Actual upstream pressure and temperature are selected after flow reversal.
    Cd is an empirical factor. No finite-pipe or valve-spool dynamics included.
    """
    if not np.isrealobj([p_a,p_b,t_a,t_b,area]):raise ValueError('flow inputs must be real')
    if not np.all(np.isfinite([p_a,p_b,t_a,t_b,area])) or min(p_a,p_b,t_a,t_b)<=0 or area<0:
        raise ValueError('positive absolute pressures/temperatures and nonnegative area required')
    if p_a==p_b or area==0:return 0.
    direction=1. if p_a>p_b else -1.
    upstream,downstream,temp=(p_a,p_b,t_a) if direction>0 else (p_b,p_a,t_b)
    ratio=downstream/upstream;g=p.gamma;critical=(2/(g+1))**(g/(g-1))
    if ratio<=critical:
        phi=np.sqrt(g)*(2/(g+1))**((g+1)/(2*(g-1)))
    else:
        phi=np.sqrt(2*g/(g-1)*(ratio**(2/g)-ratio**((g+1)/g)))
    return direction*p.discharge_coefficient*area*upstream/np.sqrt(p.R*temp)*phi


def observe(state,p=Parameters()):
    if not np.isrealobj(state):raise ValueError('state must be real')
    z=np.asarray(state,dtype=float)
    if z.shape!=(6,) or not np.all(np.isfinite(z)) or min(z[2:])<=0:
        raise ValueError('six finite states with positive masses/temperatures required')
    if abs(z[0])>p.half_stroke+1e-12:raise ValueError('position exceeds declared stroke; no impact model')
    volumes=np.array([p.midpoint_volume+p.area*z[0],p.midpoint_volume-p.area*z[0]])
    pressures=z[2:4]*p.R*z[4:6]/volumes
    return pressures,volumes


def state_from_pressures(position=0.,velocity=0.,pressures=(5e5,5e5),temperatures=(293.15,293.15),p=Parameters()):
    if any(not np.isrealobj(value) for value in [position,velocity,pressures,temperatures]):
        raise ValueError('state inputs must be real')
    pressures=np.asarray(pressures,dtype=float);temperatures=np.asarray(temperatures,dtype=float)
    if pressures.shape!=(2,) or temperatures.shape!=(2,) or not np.all(np.isfinite(pressures)) or min(pressures)<=0:
        raise ValueError('two positive absolute chamber pressures required')
    volumes=np.array([p.midpoint_volume+p.area*position,p.midpoint_volume-p.area*position])
    state=np.r_[position,velocity,pressures*volumes/(p.R*temperatures),temperatures]
    observe(state,p)
    return state


def equilibrium(position=0.,mean_pressure=5e5,p=Parameters()):
    """Closed-valve vertical equilibrium with zero bypass and uniform temperature."""
    if p.bypass_area:raise ValueError('closed-valve unequal-pressure equilibrium requires zero bypass')
    difference=p.total_mass*p.gravity/p.area
    pressures=np.array([mean_pressure+difference/2,mean_pressure-difference/2])
    if min(pressures)<=p.exhaust_pressure or max(pressures)>=p.supply_pressure:
        raise ValueError('equilibrium pressures must lie inside reservoir pressures')
    temperature=p.wall_temperature if p.wall_conductance>0 else p.reservoir_temperature
    return state_from_pressures(position,0.,pressures,[temperature]*2,p)


def balances(state,voltage,p=Parameters(),external_force=0.):
    """Derivative and observable conservation terms, using absolute pressures.

    Positive x points upward. Positive external_force opposes that direction.
    Payload is constant within one simulation; mass attachment is not modeled.
    """
    if not np.isrealobj([voltage,external_force]):raise ValueError('inputs must be real')
    if not np.all(np.isfinite([voltage,external_force])):raise ValueError('finite inputs required')
    pressures,volumes=observe(state,p);z=np.asarray(state,dtype=float)
    u=float(np.clip(voltage,-p.voltage_limit,p.voltage_limit));spool=p.valve_gain*u
    opened=p.port_width*abs(spool)
    # Nodes: supply, exhaust, chamber I, chamber II; fixed named flow directions.
    node_p=np.r_[p.supply_pressure,p.exhaust_pressure,pressures]
    node_t=np.r_[[p.reservoir_temperature]*2,z[4:6]]
    areas=[opened if u<0 else 0.,opened if u>0 else 0.,
           opened if u<0 else 0.,opened if u>0 else 0.,p.bypass_area]
    links=[(2,1),(0,2),(0,3),(3,1),(2,3)]
    flows=np.zeros(5);mass_rate=np.zeros(2);enthalpy_rate=np.zeros(2)
    for j,((a,b),area) in enumerate(zip(links,areas)):
        q=orifice_flow(node_p[a],node_p[b],node_t[a],node_t[b],area,p)
        flows[j]=q;transport=q*p.cp*(node_t[a] if q>=0 else node_t[b])
        if a>=2:mass_rate[a-2]-=q;enthalpy_rate[a-2]-=transport
        if b>=2:mass_rate[b-2]+=q;enthalpy_rate[b-2]+=transport
    volume_rate=np.array([p.area*z[1],-p.area*z[1]])
    heat_rate=p.wall_conductance*(p.wall_temperature-z[4:6])
    energy_rate=enthalpy_rate+heat_rate-pressures*volume_rate
    temperature_rate=(energy_rate-p.cv*z[4:6]*mass_rate)/(p.cv*z[2:4])
    friction=p.viscous*z[1]+p.coulomb*np.tanh(z[1]/p.friction_velocity)
    acceleration=(p.area*(pressures[0]-pressures[1])-friction-p.total_mass*p.gravity-external_force)/p.total_mass
    derivative=np.r_[z[1],acceleration,mass_rate,temperature_rate]
    pressure_rate=p.R/volumes*(z[4:6]*mass_rate+z[2:4]*temperature_rate)-pressures*volume_rate/volumes
    return derivative,{'pressures':pressures,'volumes':volumes,'mass_flows':flows,
                       'mass_rate':mass_rate,'enthalpy_rate':enthalpy_rate,'heat_rate':heat_rate,
                       'internal_energy_rate':energy_rate,'pressure_rate':pressure_rate,
                       'friction':friction,'voltage':u,'spool_m':spool,'orifice_area_m2':opened}


def rhs(t,state,voltage,p=Parameters(),external_force=0.):
    return balances(state,voltage,p,external_force)[0]


def simulate(input_function,initial=None,p=Parameters(),duration=2.,samples=1001,rtol=1e-9,atol=1e-11):
    if duration<=0 or samples<2:raise ValueError('positive duration and at least two samples required')
    if initial is None:initial=equilibrium(p=p)
    observe(initial,p)
    result=solve_ivp(lambda t,x:rhs(t,x,input_function(t),p),(0,duration),initial,
                     t_eval=np.linspace(0,duration,samples),method='DOP853',rtol=rtol,atol=atol,max_step=.005)
    if not result.success:raise RuntimeError(result.message)
    return result.t,result.y.T


def identified_local_model(index):
    """Three reported Table 3 models, in deviation states [x,v,delta_p].

    Schulte/Hahn (2004): mass0 and6kg, positions0 and0.08m. These are local
    identified fits, not validation data or a global mass-flow calibration.
    Coulomb/gravity offsets are removed; no controller is recovered here.
    """
    table={1:(0.,0.,-26.,-8.7e6,1.1e10),3:(6.,0.,-11.,-8.9e6,1e10),
           15:(6.,.08,-14.,-1.06e7,1.24e10)}
    if index not in table:raise ValueError('only published local models 1, 3 and 15 are available')
    mass,position,ql,qdx,qxv=table[index];total=mass+2.9
    A=np.array([[0,1,0],[0,-135/total,2.8e-3/total],[0,qdx,ql]])
    B=np.array([0,0,qxv*1e-4]);C=np.array([1.,0,0])
    return {'index':index,'load_kg':mass,'position_m':position,'A':A,'B':B,'C':C,
            'pressure_coefficients':np.array([ql,qdx,qxv])}

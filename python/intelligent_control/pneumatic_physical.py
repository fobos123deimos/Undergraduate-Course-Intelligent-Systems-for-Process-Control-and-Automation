"""Conservative six-state pneumatic cylinder with explicit valve assumptions.

The state order is ``[position, velocity, mass I, mass II, temperature I,
temperature II]`` in m, m/s, kg, kg, K and K. Position is positive upward,
pressures are absolute Pa, voltage is in V and time is in seconds. Ideal-gas
chamber storage, enthalpy transport, wall heat exchange, gravity and regularized
friction enter the same balance. `orifice_flow` handles reversal and choking.

Start with `Parameters`, construct a vertical `equilibrium`, then call
`simulate` with a voltage function. `observe` converts mass/temperature states
to chamber pressures and volumes; `balances` exposes the conservation terms
used by `rhs`. `identified_local_model` separately returns three published
local fits, with their gravity/Coulomb offsets removed.

This is an SI teaching variant, not a recovered canonical valve calibration.
The repository's ``benchmarks/PNEUMATIC_AUDIT.md`` identifies primary sources
and added assumptions. Valve geometry/discharge, thermal data and friction
closure remain uncalibrated. The literal survey transcription remains in
`intelligent_control.benchmarks.pneumatic_rhs`.
"""
from dataclasses import dataclass, asdict
import numpy as np
from scipy.integrate import solve_ivp


@dataclass(frozen=True)
class Parameters:
    """Immutable geometry, reservoir and closure coefficients in SI units.

    Parameters
    ----------
    area : float
        Effective piston area in m².
    half_stroke : float
        Maximum position magnitude in m; impacts are not modeled.
    midpoint_volume : float
        Volume of each chamber at zero position, in m³.
    piston_mass, load_mass : float
        Moving piston and attached payload masses in kg.
    viscous, coulomb : float
        Viscous friction in N s/m and Coulomb amplitude in N.
    valve_gain : float
        Static spool displacement gain in m/V.
    voltage_limit : float
        Symmetric actuator-voltage saturation magnitude in V.
    supply_pressure, exhaust_pressure : float
        Absolute reservoir pressures in Pa.
    reservoir_temperature, wall_temperature : float
        Reservoir and cylinder-wall temperatures in K.
    universal_R, air_molar_mass : float
        Molar gas constant in J/(mol K) and air molar mass in kg/mol;
        `R` converts these to the mass-specific constant.
    gamma : float
        Heat-capacity ratio, greater than one.
    gravity : float
        Downward gravitational acceleration in m/s².
    port_width : float
        Slot width in m; opened area equals width times spool displacement.
    discharge_coefficient : float
        Orifice discharge factor in ``(0, 1]``.
    bypass_area : float
        Optional chamber-to-chamber bypass area in m².
    friction_velocity : float
        Positive velocity scale in m/s for the smooth Coulomb approximation.
    wall_conductance : float
        Heat conductance from the wall to each chamber in W/K.

    Notes
    -----
    The closure defaults are declared study choices, not identified apparatus
    data. Construction rejects invalid geometry, reservoir ordering and
    specified coefficient ranges. Payload is constant during a trajectory.
    """
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
    def R(self):
        """Mass-specific ideal-gas constant in J/(kg K)."""
        return self.universal_R/self.air_molar_mass
    @property
    def cv(self):
        """Constant-volume specific heat capacity in J/(kg K)."""
        return self.R/(self.gamma-1)
    @property
    def cp(self):
        """Constant-pressure specific heat capacity in J/(kg K)."""
        return self.gamma*self.cv
    @property
    def total_mass(self):
        """Total moving mechanical mass in kg."""
        return self.piston_mass+self.load_mass
    @property
    def residual_volume(self):
        """Minimum chamber volume at a stroke endpoint, in m³."""
        return self.midpoint_volume-self.area*self.half_stroke


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
    """Validate a six-state vector and recover chamber pressures and volumes.

    Parameters
    ----------
    state : array_like, shape (6,)
        ``[x, velocity, mass I, mass II, temperature I, temperature II]``
        in m, m/s, kg, kg, K and K. Masses and temperatures must be positive;
        position must remain within the declared stroke.
    p : Parameters, optional
        Geometry and specific-air coefficients.

    Returns
    -------
    pressures, volumes : numpy.ndarray, shape (2,)
        Absolute chamber pressures in Pa and volumes in m³, ordered I then II.

    Raises
    ------
    ValueError
        If the state is nonreal, nonfinite, incorrectly sized or outside the
        positive-mass/temperature or stroke domain.
    """
    if not np.isrealobj(state):raise ValueError('state must be real')
    z=np.asarray(state,dtype=float)
    if z.shape!=(6,) or not np.all(np.isfinite(z)) or min(z[2:])<=0:
        raise ValueError('six finite states with positive masses/temperatures required')
    if abs(z[0])>p.half_stroke+1e-12:raise ValueError('position exceeds declared stroke; no impact model')
    volumes=np.array([p.midpoint_volume+p.area*z[0],p.midpoint_volume-p.area*z[0]])
    pressures=z[2:4]*p.R*z[4:6]/volumes
    return pressures,volumes


def state_from_pressures(position=0.,velocity=0.,pressures=(5e5,5e5),temperatures=(293.15,293.15),p=Parameters()):
    """Construct a validated state by applying the ideal-gas law in each chamber.

    Parameters
    ----------
    position, velocity : float, optional
        Upward displacement in m and upward velocity in m/s.
    pressures, temperatures : array_like, shape (2,), optional
        Positive absolute pressures in Pa and temperatures in K, ordered I
        then II. Equal pressures are not a vertical mechanical equilibrium.
    p : Parameters, optional
        Geometry and specific-air coefficients.

    Returns
    -------
    numpy.ndarray, shape (6,)
        Position, velocity, chamber masses and temperatures in the module's
        state order. `observe` validates the resulting physical domain.
    """
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

    Parameters
    ----------
    state : array_like, shape (6,)
        Position, velocity, two masses and two temperatures, using SI units.
    voltage : float
        Valve command in V, clipped to the declared symmetric voltage limit.
        Positive voltage opens supply-to-I and II-to-exhaust ports.
    p : Parameters, optional
        Declared physical and closure coefficients.
    external_force : float, optional
        Additional downward force in N.

    Returns
    -------
    derivative : numpy.ndarray, shape (6,)
        State derivative per second.
    diagnostics : dict
        Chamber ``pressures`` (Pa), ``volumes`` (m³), ``mass_rate`` (kg/s),
        ``pressure_rate`` (Pa/s), and enthalpy/heat/internal-energy rates (W).
        ``mass_flows`` (kg/s) use signed directions I-to-exhaust,
        supply-to-I, supply-to-II, II-to-exhaust and I-to-II. Other fields
        expose signed resisting ``friction`` (N), applied ``voltage`` (V),
        ``spool_m`` and ``orifice_area_m2``. Flow enthalpy uses the actual
        upstream temperature even when a named port reverses direction.
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
    """Return the six-state derivative from `balances` for ODE integration.

    ``t`` is accepted for solver compatibility but is unused. ``voltage`` is
    the instantaneous scalar command in V, not a callable. State, parameter,
    external-force and derivative conventions are those of `balances`.
    """
    return balances(state,voltage,p,external_force)[0]


def simulate(input_function,initial=None,p=Parameters(),duration=2.,samples=1001,rtol=1e-9,atol=1e-11):
    """Integrate a voltage-driven cylinder using SciPy's DOP853 solver.

    Parameters
    ----------
    input_function : callable
        ``input_function(t)`` returns voltage in V for time in seconds.
    initial : array_like, shape (6,), optional
        Initial state in the module's order. If omitted, `equilibrium`
        constructs the closed-valve vertical equilibrium for ``p``.
    p : Parameters, optional
        Fixed parameters, including payload and voltage saturation.
    duration : float, optional
        Positive simulation horizon in seconds.
    samples : int, optional
        At least two evenly spaced returned samples, including both endpoints.
    rtol, atol : float, optional
        Relative and absolute solver tolerances. Internal steps are capped
        at 0.005 s independently of the output grid.

    Returns
    -------
    time : numpy.ndarray, shape (samples,)
        Sample times in seconds.
    states : numpy.ndarray, shape (samples, 6)
        Simulated positions, velocities, masses and temperatures.

    Notes
    -----
    This convenience function applies zero additional external force. Use
    `rhs` directly with a solver for other force inputs. Invalid physical
    trial states raise an error; there is no impact or stiction event model.
    """
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

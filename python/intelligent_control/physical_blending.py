"""Independent physical Blending Tank model with explicit units and offsets.

No historical MATLAB or Simulink source is loaded or executed. States are
``[X, V]``: solute mass fraction and liquid volume in m^3. Inputs are always
``[w1, w2, x1, x2, wout]``: mass flows in kg/min and dimensionless feed
fractions. Density is in kg/m^3; time is in minutes. Perfect mixing, constant
density and no reaction are assumed. No vessel capacity is specified.

The declared teaching density 1000 is a new explicit assumption, not a value
recovered from old rounded matrices. Linear models use deviations about an
equilibrium; an affine Taylor model includes a nonzero reference derivative.
"""
import numpy as np
from scipy.integrate import solve_ivp

DEFAULT_RHO = 1000.0
DEFAULT_INPUT = np.array([500., 200., .4, .75, 700.])
DEFAULT_STATE = np.array([.5, 2.])
INPUT_ORDER = ('w1', 'w2', 'x1', 'x2', 'wout')
STATE_ORDER = ('X', 'V')


def _positive(value, name):
    if isinstance(value, (bool, np.bool_)) or np.iscomplexobj(value):
        raise ValueError(f'{name} must be a finite positive scalar')
    try:
        value = np.asarray(value, dtype=float)
    except (TypeError, ValueError) as error:
        raise ValueError(f'{name} must be a finite positive scalar') from error
    if value.ndim != 0 or not np.isfinite(value) or value <= 0:
        raise ValueError(f'{name} must be a finite positive scalar')
    return float(value)


def _vector(value, length, name):
    if np.iscomplexobj(value):
        raise ValueError(f'{name} must be a finite real vector of length {length}')
    try:
        value = np.array(value, dtype=float, copy=True)
    except (TypeError, ValueError) as error:
        raise ValueError(f'{name} must be a finite real vector of length {length}') from error
    if value.shape != (length,) or not np.all(np.isfinite(value)):
        raise ValueError(f'{name} must be a finite real vector of length {length}')
    return value


def _state(state):
    state = _vector(state, 2, 'state [X,V]')
    if not 0 <= state[0] <= 1 or state[1] <= 0:
        raise ValueError('State requires 0 <= X <= 1 and V > 0')
    return state


def _inputs(inputs):
    inputs = _vector(inputs, 5, 'inputs [w1,w2,x1,x2,wout]')
    if np.any(inputs[[0, 1, 4]] < 0):
        raise ValueError('Mass flows must be nonnegative')
    if np.any(inputs[2:4] < 0) or np.any(inputs[2:4] > 1):
        raise ValueError('Feed mass fractions must lie in [0,1]')
    return inputs


def _field(state, inputs, rho):
    """Unchecked field for an integrator's internal trial stages only."""
    fraction, volume = state
    w1, w2, x1, x2, wout = inputs
    if volume <= 0 or not np.all(np.isfinite(state)):
        raise ArithmeticError('Integrator left the positive-volume domain')
    return np.array([(w1*(x1-fraction)+w2*(x2-fraction))/(rho*volume),
                     (w1+w2-wout)/rho])


def rhs(state, inputs=DEFAULT_INPUT, rho=DEFAULT_RHO):
    """Return [dX/dt,dV/dt], with validated physical inputs and state.

    The solute balance is d(rho*V*X)/dt = w1*x1+w2*x2-wout*X.
    Eliminating dV/dt cancels the explicit outlet term in dX/dt. Outlet
    flow still affects concentration indirectly through the changing volume.
    """
    return _field(_state(state), _inputs(inputs), _positive(rho, 'rho'))


def equilibrium(inputs=DEFAULT_INPUT, volume=2., rho=DEFAULT_RHO):
    """Find the equilibrium composition at a chosen positive volume.

    A constant volume requires wout=w1+w2. With zero total inlet the
    concentration is not uniquely determined, so this constructor rejects it.
    Volume itself is a free equilibrium coordinate, not an asymptotically
    stable state: its linear dynamics include an integrator.
    """
    u = _inputs(inputs); volume = _positive(volume, 'volume')
    _positive(rho, 'rho')
    total = u[0]+u[1]
    if total <= 0:
        raise ValueError('A unique equilibrium composition requires positive total inlet')
    if abs(total-u[4]) > 1e-12*max(1., total, u[4]):
        raise ValueError('Equilibrium volume requires wout = w1+w2')
    return np.array([(u[0]*u[2]+u[1]*u[3])/total, volume])


def jacobians(state, inputs=DEFAULT_INPUT, rho=DEFAULT_RHO):
    """Exact Jacobians at any physical point, not necessarily equilibrium."""
    x, u, rho = _state(state), _inputs(inputs), _positive(rho, 'rho')
    fraction, volume = x
    w1, w2, x1, x2, _ = u
    scale = 1/(rho*volume)
    derivative = _field(x, u, rho)
    a = np.array([[-(w1+w2)*scale, -derivative[0]/volume], [0., 0.]])
    b = np.array([[(x1-fraction)*scale, (x2-fraction)*scale,
                   w1*scale, w2*scale, 0.],
                  [1/rho, 1/rho, 0., 0., -1/rho]])
    return a, b


def linearize(inputs=DEFAULT_INPUT, volume=2., rho=DEFAULT_RHO):
    """Equilibrium model: delta_x_dot=A delta_x+B delta_u; x=x_eq+delta_x.

    Feeding absolute inputs into B or treating delta_x as absolute physical
    states changes the model. Use affine_rhs for a local expansion away from
    equilibrium, and retain its constant reference derivative.
    """
    u, rho = _inputs(inputs), _positive(rho, 'rho')
    x = equilibrium(u, volume, rho)
    a, b = jacobians(x, u, rho)
    return {'x_eq': x, 'u_eq': u, 'A': a, 'B': b,
            'C': np.eye(2), 'D': np.zeros((2, 5)), 'rho': rho,
            'state_order': STATE_ORDER, 'input_order': INPUT_ORDER}


def affine_rhs(state, inputs, reference_state, reference_inputs, rho=DEFAULT_RHO):
    """Local affine Taylor field fbar+A(x-xbar)+B(u-ubar).

    This is a frozen local approximation, not an exact global nonlinear model
    or a trajectory-dependent linearization. In particular a filling point
    retains its nonzero volume derivative.
    """
    x, u = _state(state), _inputs(inputs)
    xbar, ubar, rho = _state(reference_state), _inputs(reference_inputs), _positive(rho, 'rho')
    a, b = jacobians(xbar, ubar, rho)
    return _field(xbar, ubar, rho)+a@(x-xbar)+b@(u-ubar)


def transfer_functions(inputs=DEFAULT_INPUT, volume=2., rho=DEFAULT_RHO):
    """Reduced zero-initial-deviation transfer functions at equilibrium.

    Coefficients use descending powers of s. Channels with identically zero
    response have numerator [0] and denominator [1]. Other concentration
    channels have a stable first-order denominator; volume channels have the
    genuine pole at zero. No artificial uncancelled common factor is retained.
    """
    model = linearize(inputs, volume, rho)
    pole = -model['A'][0, 0]
    result = {}
    for row, output in enumerate(STATE_ORDER):
        for col, source in enumerate(INPUT_ORDER):
            gain = float(model['B'][row, col])
            result[f'{output}/{source}'] = {
                'numerator': [gain],
                'denominator': [1.] if gain == 0 else [1., float(pole) if row == 0 else 0.]}
    return result


def constant_input_solution(time, initial_state, inputs=DEFAULT_INPUT, rho=DEFAULT_RHO):
    """Analytical trajectory from elapsed time zero for constant inputs.

    Valid for balanced flow, filling and draining until V=0. A scalar time
    returns shape (2,); a time vector returns (n,2). The expression uses log1p
    to retain precision near balanced flow. This function does not replace
    the numerical solver used by simulate.
    """
    initial, u, rho = _state(initial_state), _inputs(inputs), _positive(rho, 'rho')
    if np.iscomplexobj(time):
        raise ValueError('Elapsed time must be a finite nonnegative scalar or vector')
    time = np.asarray(time, dtype=float)
    if time.ndim > 1 or not np.all(np.isfinite(time)) or np.any(time < 0):
        raise ValueError('Elapsed time must be a finite nonnegative scalar or vector')
    total, imbalance = u[0]+u[1], u[0]+u[1]-u[4]
    volume = initial[1]+imbalance*time/rho
    if np.any(volume <= 0):
        raise ValueError('Requested analytical trajectory reaches an empty tank')
    if total == 0:
        fraction = np.full_like(time, initial[0])
    else:
        target = (u[0]*u[2]+u[1]*u[3])/total
        exponent = (-total*time/(rho*initial[1]) if imbalance == 0 else
                    -total/imbalance*np.log1p(imbalance*time/(rho*initial[1])))
        fraction = target+(initial[0]-target)*np.exp(exponent)
    return np.stack((fraction, volume), axis=-1)


def simulate(initial_state, time, inputs=DEFAULT_INPUT, rho=DEFAULT_RHO,
             minimum_volume=1e-6):
    """Integrate piecewise-constant physical inputs with solve_ivp.

    ``time`` is a strictly increasing vector; ``initial_state`` belongs to
    time[0]. Inputs are one length-five vector or exactly (len(time)-1,5),
    held over each consecutive interval. All planned interval volumes are
    checked analytically before integration. The whole request is rejected if
    any volume reaches or crosses minimum_volume; no post-emptying values or
    silently clipped solution are returned. This matches the native MATLAB/
    Octave implementation. Upper vessel capacity is outside this model.
    """
    initial, rho = _state(initial_state), _positive(rho, 'rho')
    minimum_volume = _positive(minimum_volume, 'minimum_volume')
    if initial[1] <= minimum_volume:
        raise ValueError('Initial volume must exceed minimum_volume')
    if np.iscomplexobj(time):
        raise ValueError('Time must be a finite strictly increasing vector')
    time = np.array(time, dtype=float, copy=True)
    if time.ndim != 1 or len(time) < 2 or not np.all(np.isfinite(time)) or np.any(np.diff(time) <= 0):
        raise ValueError('Time must be a finite strictly increasing vector with at least two samples')
    if np.iscomplexobj(inputs):
        raise ValueError('Inputs must be real')
    schedule = np.array(inputs, dtype=float, copy=True)
    if schedule.shape == (5,):
        schedule = np.tile(_inputs(schedule), (len(time)-1, 1))
    elif schedule.shape == (len(time)-1, 5):
        schedule = np.array([_inputs(row) for row in schedule])
    else:
        raise ValueError('Input schedule must have shape (5,) or (len(time)-1,5)')
    volumes = initial[1]+np.cumsum(np.diff(time)*(schedule[:, 0]+schedule[:, 1]-schedule[:, 4])/rho)
    if not np.all(np.isfinite(volumes)) or np.any(volumes <= minimum_volume):
        raise ValueError('Planned trajectory reaches minimum_volume; shorten the horizon or change flows')
    states = np.empty((len(time), 2)); states[0] = initial
    for k, u in enumerate(schedule):
        solution = solve_ivp(lambda _, state: _field(state, u, rho),
                             (time[k], time[k+1]), states[k], method='RK45',
                             rtol=1e-9, atol=1e-11, t_eval=[time[k+1]])
        if not solution.success:
            raise RuntimeError(f'Tank integration failed on interval {k}: {solution.message}')
        states[k+1] = solution.y[:, -1]
    if (not np.all(np.isfinite(states)) or np.any(states[:, 1] <= 0) or
            np.any(states[:, 0] < -1e-8) or np.any(states[:, 0] > 1+1e-8)):
        raise ArithmeticError('Numerical solution violated the physical state domain')
    return {'t': time, 'state': states, 'inputs': schedule,
            'rho': rho, 'minimum_volume': minimum_volume}

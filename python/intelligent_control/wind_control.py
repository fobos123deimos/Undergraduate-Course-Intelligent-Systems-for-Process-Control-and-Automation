"""Operating-point LQR and parallel distributed compensation for a wind turbine.

The eight regulation states are tower deflection (m), relative blade deflection
(m), shaft torsion (rad), tower/blade velocities (m/s), rotor/generator speeds
(rad/s) and pitch (rad). Generator quantities are referred to the low-speed
side. Absolute common rotation is eliminated from the nine-state plant.
Commands are generator torque (N m) and requested pitch (rad); wind is in m/s
and time in seconds.

Use `default_map` to load the bundled later ROSCO table, `design` to obtain
local LQR laws and `simulate` to compare scheduled PDC with a fixed-gain
baseline. `controller` applies explicit torque/pitch magnitude and slew
limits. `variant_rhs` exposes a rigid-structure reduction and a separately
declared second-order pitch actuator.

The gains and experiments are a new reproducible design exercise, not recovery
of the article's fitted controller or Table 12. Local Riccati and pole checks
do not establish global nonlinear stability. The source, plant-map version,
information assumptions and comparison protocol are documented in the
repository's ``benchmarks/WIND_CONTROL.md``.
"""
from pathlib import Path
import numpy as np
from scipy.linalg import solve_continuous_are
from scipy.optimize import brentq
from .benchmarks import RotorMap, wind_rhs

STATE_SCALE = np.array([1., 5., .01, .2, 1., .1, .1, .1])
INPUT_SCALE = np.array([1e6, .1])
Q = np.diag([1., 1., .2, 1., 1., 100., 100., 1.])
R = np.diag([2., 1.])
LOWER = np.array([0., 0.])
UPPER = np.array([6e6, np.deg2rad(30.)])
RATE = np.array([5e5, np.deg2rad(8.)])


def regulation_rhs(state, command, wind, aero):
    """Evaluate the nonlinear plant after eliminating common shaft rotation.

    Parameters
    ----------
    state : array_like, shape (8,)
        Tower/blade deflections, shaft torsion, tower/blade velocities,
        rotor/generator speeds and pitch in the module's SI conventions.
    command : array_like, shape (2,)
        Generator torque in N m and requested pitch in rad.
    wind : float
        Free-stream wind speed in m/s.
    aero : callable
        ``aero(tip_speed_ratio, pitch_radians)`` returns thrust and torque
        coefficients ``(CT, CQ)``. `default_map` rejects extrapolation.

    Returns
    -------
    numpy.ndarray, shape (8,)
        State derivative per second, in the same state order.

    Notes
    -----
    This function does not apply actuator limits; use `controller` when
    simulating the bounded feedback experiment. The underlying plant rejects
    nonpositive effective wind and out-of-domain aerodynamic lookup.
    """
    x = np.asarray(state, dtype=float)
    u = np.asarray(command, dtype=float)
    if x.shape != (8,) or u.shape != (2,):
        raise ValueError('Expected eight regulation states and two commands')
    full = np.r_[x[:2], x[2], 0., x[3:7], x[7]]
    f = wind_rhs(0, full, [wind, u[0], u[1]], aero)
    return np.r_[x[3:5], x[5]-x[6], f[4:8], f[8]]


def equilibrium(wind, aero, speed=1.2, torque=5e6/1.2):
    """Solve a constant-wind equilibrium from torque and thrust balances.

    Parameters
    ----------
    wind : float
        Positive free-stream wind speed in m/s.
    aero : callable
        Aerodynamic coefficient interface described in `regulation_rhs`.
    speed : float, optional
        Positive rotor and low-speed-side generator angular speed in rad/s.
    torque : float, optional
        Positive generator torque in N m; default mechanical power is 5 MW.

    Returns
    -------
    state : numpy.ndarray, shape (8,)
        Absolute regulation coordinates, including nonzero deflections,
        torsion and pitch. Tower and blade velocities are zero.
    command : numpy.ndarray, shape (2,)
        Equilibrium generator torque and requested pitch.

    Notes
    -----
    Pitch is found on ``[0, 30 degrees]`` by a bracketed root solve. A missing
    bracket or an aerodynamic lookup outside its table raises an error; no
    extrapolated equilibrium is manufactured.
    """
    if wind <= 0 or speed <= 0 or torque <= 0:
        raise ValueError('Positive wind, speed and torque required')
    factor = .5*1.225*np.pi*63**3*wind**2
    pitch = brentq(lambda b: factor*aero(speed*63/wind, b)[1]-torque,
                   0., np.deg2rad(30.), xtol=1e-14)
    ct, _ = aero(speed*63/wind, pitch)
    thrust = .5*1.225*np.pi*63**2*ct*wind**2
    x = np.array([thrust/1981900., thrust/120000., torque/867637000.,
                  0., 0., speed, speed, pitch])
    return x, np.array([torque, pitch])


def linearize(state, command, wind, aero):
    """Compute local state/input Jacobians with centered finite differences.

    State, command, wind and aerodynamic-map conventions match
    `regulation_rhs`. Perturbations are ``1e-5 * STATE_SCALE`` and
    ``1e-5 * INPUT_SCALE``. Wind is held fixed; no wind-disturbance column
    or affine offset is returned. `design` calls this at solved equilibria.

    Returns
    -------
    a : numpy.ndarray, shape (8, 8)
        State Jacobian in unscaled physical coordinates.
    b : numpy.ndarray, shape (8, 2)
        Command Jacobian in unscaled physical coordinates.
    """
    a = np.empty((8, 8)); b = np.empty((8, 2))
    for j, scale in enumerate(STATE_SCALE):
        delta = np.eye(8)[j]*scale*1e-5
        a[:, j] = (regulation_rhs(state+delta, command, wind, aero)-
                   regulation_rhs(state-delta, command, wind, aero))/(2*scale*1e-5)
    for j, scale in enumerate(INPUT_SCALE):
        delta = np.eye(2)[j]*scale*1e-5
        b[:, j] = (regulation_rhs(state, command+delta, wind, aero)-
                   regulation_rhs(state, command-delta, wind, aero))/(2*scale*1e-5)
    return a, b


def design(aero, winds=(12., 14., 16.)):
    """Design and check one scaled continuous-time LQR law per operating wind.

    Parameters
    ----------
    aero : callable
        Aerodynamic coefficient map as in `regulation_rhs`.
    winds : sequence of float, optional
        Operating winds in m/s. Use a strictly increasing sequence with at
        least two points when passing the result to `memberships`.

    Returns
    -------
    list of dict
        Each record contains ``wind``, equilibrium ``state`` and ``command``,
        physical-coordinate ``a``/``b`` Jacobians, a ``(2, 8)`` feedback
        ``gain``, ``care_residual`` (infinity norm in scaled coordinates)
        and ``max_pole_real`` (1/s). The local law is
        ``command - gain @ (state - equilibrium_state)``.

    Raises
    ------
    RuntimeError
        If a local closed-loop pole is not strictly stable or the scaled
        Riccati residual exceeds ``1e-6``.

    Notes
    -----
    Cost matrices ``Q`` and ``R`` apply in the declared normalized coordinates.
    These checks concern the local linearizations, not a common Lyapunov
    certificate for the interpolated nonlinear closed loop.
    """
    points = []
    for wind in winds:
        x, u = equilibrium(wind, aero)
        a, b = linearize(x, u, wind, aero)
        an = a*STATE_SCALE[None, :]/STATE_SCALE[:, None]
        bn = b*INPUT_SCALE[None, :]/STATE_SCALE[:, None]
        p = solve_continuous_are(an, bn, Q, R)
        kn = np.linalg.solve(R, bn.T@p)
        gain = kn*INPUT_SCALE[:, None]/STATE_SCALE[None, :]
        residual = an.T@p+p@an-p@bn@np.linalg.solve(R, bn.T@p)+Q
        poles = np.linalg.eigvals(a-b@gain)
        if np.max(poles.real) >= 0 or np.linalg.norm(residual, np.inf) > 1e-6:
            raise RuntimeError('Local LQR failed stability or Riccati checks')
        points.append(dict(wind=float(wind), state=x, command=u, gain=gain,
                           a=a, b=b, care_residual=float(np.linalg.norm(residual, np.inf)),
                           max_pole_real=float(np.max(poles.real))))
    return points


def memberships(wind, points):
    """Return adjacent piecewise-linear scheduling weights without extrapolation.

    Parameters
    ----------
    wind : float
        Finite wind speed in m/s, inside the design interval.
    points : sequence of dict
        Records from `design`, with at least two strictly increasing
        ``wind`` values.

    Returns
    -------
    numpy.ndarray, shape (len(points),)
        Nonnegative weights summing to one. At most two adjacent entries
        are active; a grid point selects its own operating law.

    Raises
    ------
    ValueError
        If the wind or operating grid does not satisfy the stated domain.
    """
    grid = np.array([p['wind'] for p in points])
    if len(grid) < 2 or np.any(np.diff(grid) <= 0) or not np.isfinite(wind):
        raise ValueError('An increasing operating grid and finite wind are required')
    if wind < grid[0] or wind > grid[-1]:
        raise ValueError('Scheduling outside the design grid is not supported')
    j = min(np.searchsorted(grid, wind, side='right')-1, len(grid)-2)
    alpha = (wind-grid[j])/(grid[j+1]-grid[j])
    h = np.zeros(len(grid)); h[j:j+2] = [1-alpha, alpha]
    return h


def controller(state, wind, points, previous, dt, scheduled=True):
    """Evaluate state feedback and enforce command slew and magnitude limits.

    Parameters
    ----------
    state : numpy.ndarray, shape (8,)
        Measured full regulation state in the module's SI coordinates.
    wind : float
        Current measured wind in m/s, inside the design interval.
    points : sequence of dict
        Operating equilibria and local gains returned by `design`.
    previous : numpy.ndarray, shape (2,)
        Previously applied torque/pitch command. The intended control loop
        starts from a feasible equilibrium command.
    dt : float
        Positive control sample interval in seconds.
    scheduled : bool, optional
        If true, blend the local affine feedback laws using `memberships`.
        Otherwise use the middle operating point's fixed gain with the same
        interpolated equilibrium feedforward.

    Returns
    -------
    numpy.ndarray, shape (2,)
        Applied generator torque (N m) and demanded pitch (rad), limited to
        ``[0, 6e6]`` N m and ``[0, 30 degrees]``. Slew limits are
        ``5e5`` N m/s and 8 degrees/s.

    Notes
    -----
    The policy uses full-state and wind measurements and has no integral
    speed-error state. Interpolation may leave a small steady-state offset.
    """
    if dt <= 0:
        raise ValueError('Positive control sample time required')
    h = memberships(wind, points)
    if scheduled:
        raw = sum(w*(p['command']-p['gain']@(state-p['state'])) for w, p in zip(h, points))
    else:
        # Same wind scheduling and equilibrium feedforward; one fixed middle gain.
        xeq = sum(w*p['state'] for w, p in zip(h, points))
        ueq = sum(w*p['command'] for w, p in zip(h, points))
        raw = ueq-points[len(points)//2]['gain']@(state-xeq)
    return np.clip(previous+np.clip(raw-previous, -RATE*dt, RATE*dt), LOWER, UPPER)


def simulate(aero, points=None, scheduled=True, duration=60., dt=.02):
    """Run a held-command nonlinear wind-control experiment with fixed-step RK4.

    Parameters
    ----------
    aero : callable
        Aerodynamic coefficient map as in `regulation_rhs`.
    points : sequence of dict, optional
        Design records; omitted records are constructed by `design`.
    scheduled : bool, optional
        Select scheduled PDC or the matched fixed-middle-gain baseline.
    duration : float, optional
        Positive finite horizon in seconds, a whole number of sample periods.
    dt : float, optional
        Positive control and RK4 integration period in seconds.

    Returns
    -------
    dict
        ``time`` and ``wind`` are length-N arrays; ``state`` has shape
        ``(N, 8)`` and ``command`` has shape ``(N, 2)``. The final command
        repeats the last applied command. ``speed_rmse`` and
        ``speed_peak_error`` are measured against 1.2 rad/s;
        ``pitch_peak_deg`` reports the maximum actual pitch in degrees.

    Notes
    -----
    The initial state is the 12 m/s equilibrium. Wind becomes 13 m/s at
    20 s and 15 m/s at 40 s, exercising interior scheduling points. Inputs
    and wind are held through each integration step. This is a deterministic
    simulated experiment, not historical wind data or a robustness proof.
    """
    if not np.isfinite(dt) or not np.isfinite(duration) or dt <= 0 or duration <= 0:
        raise ValueError('Positive finite duration and sample period required')
    points = design(aero) if points is None else points
    n = int(round(duration/dt))+1
    if not np.isclose((n-1)*dt, duration):
        raise ValueError('Duration must be a positive whole number of sample periods')
    t = np.arange(n)*dt
    # Interior points exercise two active memberships, not only switched gains.
    wind = np.where(t < 20., 12., np.where(t < 40., 13., 15.))
    x = np.empty((n, 8)); u = np.empty((n, 2))
    x[0], previous = equilibrium(wind[0], aero)
    for k in range(n-1):
        u[k] = controller(x[k], wind[k], points, previous, dt, scheduled)
        rhs = lambda z: regulation_rhs(z, u[k], wind[k], aero)
        a = rhs(x[k]); b = rhs(x[k]+dt*a/2); c = rhs(x[k]+dt*b/2); d = rhs(x[k]+dt*c)
        x[k+1] = x[k]+dt*(a+2*b+2*c+d)/6
        previous = u[k]
    u[-1] = u[-2]
    if not np.isfinite(x).all():
        raise RuntimeError('Nonfinite wind trajectory')
    return dict(time=t, wind=wind, state=x, command=u,
                speed_rmse=float(np.sqrt(np.mean((x[:, 5]-1.2)**2))),
                speed_peak_error=float(np.max(np.abs(x[:, 5]-1.2))),
                pitch_peak_deg=float(np.rad2deg(x[:, 7].max())))


def default_map():
    """Load the bundled NREL 5 MW ROSCO table as a `RotorMap`.

    The file is ``benchmarks/data/Cp_Ct_Cq.NREL5MW.txt`` relative to the
    repository root. Keep that data file with the Python source when moving
    the project. This later-map variant does not recover the exact table
    behind the article's original controller comparison.
    """
    return RotorMap(Path(__file__).resolve().parents[2]/'benchmarks/data/Cp_Ct_Cq.NREL5MW.txt')


def variant_rhs(state, command, wind, aero, variant, frequency=10., damping=1.):
    """Explicit structural reduction or declared second-order pitch extension.

    rigid_structure: [torsion, rotor speed, generator speed, pitch].
    second_order_pitch: eight regulation states followed by pitch rate.
    The added actuator parameters are study choices, not recovered article data.
    """
    x = np.asarray(state, dtype=float)
    if variant == 'rigid_structure' and x.shape == (4,):
        full = np.array([0., 0., x[0], 0., 0., x[1], x[2], x[3]])
        f = regulation_rhs(full, command, wind, aero)
        return f[[2, 5, 6, 7]]
    if variant == 'second_order_pitch' and x.shape == (9,):
        if frequency <= 0 or damping <= 0:
            raise ValueError('Positive actuator frequency and damping required')
        f = regulation_rhs(x[:8], command, wind, aero)
        f[-1] = x[-1]
        return np.r_[f, frequency**2*(command[1]-x[7])-2*damping*frequency*x[-1]]
    raise ValueError('Unknown variant or incompatible state dimension')

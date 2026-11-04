"""Operating-point LQR/PDC study for the documented later-map wind variant.

Regulation state: tower, blade, shaft torsion, tower/blade velocities,
rotor/generator speeds and pitch. Absolute common rotation is eliminated.
This is a reproducible design exercise, not recovery of published gains.
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
    x = np.asarray(state, dtype=float)
    u = np.asarray(command, dtype=float)
    if x.shape != (8,) or u.shape != (2,):
        raise ValueError('Expected eight regulation states and two commands')
    full = np.r_[x[:2], x[2], 0., x[3:7], x[7]]
    f = wind_rhs(0, full, [wind, u[0], u[1]], aero)
    return np.r_[x[3:5], x[5]-x[6], f[4:8], f[8]]


def equilibrium(wind, aero, speed=1.2, torque=5e6/1.2):
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
    points = design(aero) if points is None else points
    n = int(round(duration/dt))+1
    if dt <= 0 or duration <= 0 or not np.isclose((n-1)*dt, duration):
        raise ValueError('Duration must be a positive whole number of sample periods')
    t = np.arange(n)*dt
    wind = np.where(t < 20., 12., np.where(t < 40., 14., 16.))
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

"""Independent mechanical and control checks for the wind design exercise."""
import numpy as np
import pytest
from intelligent_control import wind_control as w
from intelligent_control.benchmarks import wind_rhs


@pytest.fixture(scope='module')
def design():
    aero = w.default_map()
    return aero, w.design(aero)


def test_regulation_coordinates_preserve_full_model(design):
    aero, points = design
    x = points[1]['state'].copy(); x[0] += .01; x[5] += .003
    # Different common rotation offsets must leave torsion dynamics unchanged.
    for angle in [0., 2., -3.]:
        full = np.r_[x[:2], x[2]+angle, angle, x[3:7], x[7]]
        f = wind_rhs(0, full, [14., *points[1]['command']], aero)
        expected = np.r_[f[:2], f[2]-f[3], f[4:]]
        np.testing.assert_allclose(w.regulation_rhs(x, points[1]['command'], 14., aero), expected, atol=1e-12)


def test_equilibria_and_local_lqr_residuals(design):
    aero, points = design
    for p in points:
        assert np.max(np.abs(w.regulation_rhs(p['state'], p['command'], p['wind'], aero))) < 1e-9
        assert p['care_residual'] < 1e-6
        assert p['max_pole_real'] < -1e-4


def test_membership_partition_and_outside_grid(design):
    _, points = design
    for wind in np.linspace(12, 16, 33):
        h = w.memberships(wind, points)
        assert np.all(h >= 0) and np.sum(h) == pytest.approx(1.)
    np.testing.assert_array_equal(w.memberships(14., points), [0., 1., 0.])
    with pytest.raises(ValueError): w.memberships(17., points)


def test_actual_midpoint_linearizations_stable_under_interpolated_gains(design):
    aero, points = design
    for wind in [12.5, 13., 13.5, 14.5, 15., 15.5]:
        x, u = w.equilibrium(wind, aero)
        a, b = w.linearize(x, u, wind, aero)
        gain = sum(h*p['gain'] for h, p in zip(w.memberships(wind, points), points))
        assert np.max(np.linalg.eigvals(a-b@gain).real) < 0


def test_closed_loop_actuator_limits_rates_and_step_convergence(design):
    aero, points = design
    result = w.simulate(aero, points)
    assert np.count_nonzero(w.memberships(result['wind'][-1], points)) == 2
    u, x = result['command'], result['state']
    assert np.all(u >= w.LOWER-1e-9) and np.all(u <= w.UPPER+1e-9)
    assert np.all(np.abs(np.diff(u, axis=0)) <= w.RATE*.02+1e-8)
    assert abs(x[-1, 5]-1.2) < .01
    assert result['speed_peak_error'] < .2


def test_time_step_refinement(design):
    aero, points = design
    coarse = w.simulate(aero, points, duration=24., dt=.02)
    fine = w.simulate(aero, points, duration=24., dt=.01)
    # Refinement changes the sampled control period as well as RK4 integration.
    assert abs(coarse['speed_rmse']-fine['speed_rmse']) < .002
    assert abs(coarse['state'][-1, 5]-fine['state'][-1, 5]) < .002


def test_rigid_structure_and_second_order_actuator(design):
    from scipy.integrate import solve_ivp
    aero, points = design
    p = points[1];rigid = p['state'][[2, 5, 6, 7]]
    np.testing.assert_allclose(w.variant_rhs(rigid, p['command'], 14., aero, 'rigid_structure'), 0, atol=1e-10)
    initial = np.r_[p['state'], 0.];target = p['command'].copy();target[1] += .01
    trajectory = solve_ivp(lambda t,x:w.variant_rhs(x,target,14.,aero,'second_order_pitch'),
                           [0,1], initial, rtol=1e-9, atol=1e-11)
    expected = p['state'][7]+.01*(1-11*np.exp(-10))
    assert trajectory.y[7,-1] == pytest.approx(expected, abs=1e-9)
    with pytest.raises(ValueError): w.variant_rhs(initial,target,14.,aero,'second_order_pitch',damping=0)

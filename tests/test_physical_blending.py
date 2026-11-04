"""Independent physical and mathematical checks of the corrected tank.

Conservation, closed-form responses, finite differences and resolvent identities provide
different oracles for the fresh implementation.
"""
import numpy as np
import pytest
from intelligent_control.physical_blending import (
    DEFAULT_INPUT, DEFAULT_STATE, rhs, equilibrium, jacobians, linearize,
    affine_rhs, transfer_functions, constant_input_solution, simulate)


def test_balances_conserve_total_mass_and_solute_at_non_equilibrium_point():
    rho = 923.; state = np.array([.23, 1.7]); u = np.array([317., 149., .12, .82, 510.])
    derivative = rhs(state, u, rho)
    # Differentiate stored total mass and stored solute, independently of the
    # cancellation used by the implementation's concentration equation.
    mass_rate = rho*derivative[1]
    solute_rate = rho*(state[1]*derivative[0]+state[0]*derivative[1])
    assert mass_rate == pytest.approx(317+149-510)
    assert solute_rate == pytest.approx(317*.12+149*.82-510*.23)


def test_equilibrium_has_free_positive_volume_and_expected_composition():
    for volume in (.2, 2., 27.):
        state = equilibrium(volume=volume)
        np.testing.assert_allclose(state, [.5, volume], atol=0, rtol=0)
        np.testing.assert_allclose(rhs(state), [0, 0], atol=1e-15)
    with pytest.raises(ValueError, match='wout'):
        equilibrium([500, 200, .4, .75, 650])
    with pytest.raises(ValueError, match='unique'):
        equilibrium([0, 0, .4, .75, 0])


def test_analytic_jacobians_match_independent_centered_differences():
    x = np.array([.31, 2.7]); u = np.array([420., 175., .18, .89, 550.]); rho = 997.
    a, b = jacobians(x, u, rho)
    numerical_a = np.empty_like(a); numerical_b = np.empty_like(b)
    for j in range(2):
        delta = np.zeros(2); delta[j] = 1e-5
        numerical_a[:, j] = (rhs(x+delta, u, rho)-rhs(x-delta, u, rho))/(2e-5)
    for j in range(5):
        step = 1e-3 if j in (0, 1, 4) else 1e-5
        delta = np.zeros(5); delta[j] = step
        numerical_b[:, j] = (rhs(x, u+delta, rho)-rhs(x, u-delta, rho))/(2*step)
    np.testing.assert_allclose(a, numerical_a, rtol=2e-8, atol=1e-11)
    np.testing.assert_allclose(b, numerical_b, rtol=2e-8, atol=1e-11)
    assert a[0, 1] != 0  # A12 only vanishes when the concentration derivative does.


def test_equilibrium_matrix_and_input_order_match_physical_parameters():
    model = linearize()
    np.testing.assert_allclose(model['A'], [[-.35, 0], [0, 0]], atol=1e-15)
    np.testing.assert_allclose(model['B'],
        [[-.00005, .000125, .25, .1, 0], [.001, .001, 0, 0, -.001]], atol=1e-15)
    assert model['input_order'] == ('w1', 'w2', 'x1', 'x2', 'wout')
    np.testing.assert_array_equal(model['C'], np.eye(2))
    np.testing.assert_array_equal(model['D'], np.zeros((2, 5)))
    # Independent invariants: changing both feed compositions equally shifts
    # the equilibrium concentration by that same amount; common flow scaling
    # leaves the mixture composition unchanged.
    b = model['B']; a = model['A'][0, 0]
    assert (b[0, 2]+b[0, 3])/(-a) == pytest.approx(1)
    assert b[0, 0]*500+b[0, 1]*200 == pytest.approx(0, abs=1e-15)


def test_affine_non_equilibrium_model_preserves_its_reference_derivative():
    xbar = np.array([.2, 2.]); ubar = np.array([500., 200., .4, .75, 650.])
    np.testing.assert_allclose(affine_rhs(xbar, ubar, xbar, ubar), [.105, .05])
    a, _ = jacobians(xbar, ubar)
    assert a[0, 1] == pytest.approx(-.0525)
    # Omitting fbar would incorrectly predict both derivatives as zero here.
    dx = np.array([.001, .002]); du = np.array([.3, -.2, .0001, -.0002, .1])
    errors = []
    for scale in (1, .5):
        actual = rhs(xbar+scale*dx, ubar+scale*du)
        approximate = affine_rhs(xbar+scale*dx, ubar+scale*du, xbar, ubar)
        errors.append(np.linalg.norm(actual-approximate))
    assert 3.95 < errors[0]/errors[1] < 4.05


def test_transfer_functions_match_state_space_resolvent_and_expected_signs():
    model = linearize(); channels = transfer_functions()
    assert len(channels) == 10
    assert channels['X/w1']['numerator'] == pytest.approx([-.00005])
    assert channels['X/w2']['numerator'] == pytest.approx([.000125])
    assert channels['V/wout'] == {'numerator': [-.001], 'denominator': [1., 0.]}
    assert channels['X/wout'] == {'numerator': [0.], 'denominator': [1.]}
    for frequency in (.013, .7, 4.2):
        s = 1j*frequency
        response = model['C']@np.linalg.solve(s*np.eye(2)-model['A'], model['B'])+model['D']
        for i, output in enumerate(('X', 'V')):
            for j, source in enumerate(('w1', 'w2', 'x1', 'x2', 'wout')):
                channel = channels[f'{output}/{source}']
                gain = np.polyval(channel['numerator'], s)/np.polyval(channel['denominator'], s)
                assert gain == pytest.approx(response[i, j], rel=1e-12, abs=1e-14)


@pytest.mark.parametrize('outlet', [700., 650., 900.])
def test_numeric_integration_matches_independent_constant_flow_closed_forms(outlet):
    t = np.linspace(0, 8, 81); u = DEFAULT_INPUT.copy(); u[4] = outlet
    if outlet == 700:
        volume = np.full_like(t, 2.)
        concentration = .5*(1-np.exp(-.35*t))
    elif outlet == 650:
        volume = 2+.05*t
        concentration = .5*(1-(2/volume)**14)
    else:
        volume = 2-.2*t
        concentration = .5*(1-(volume/2)**3.5)
    reference = np.column_stack((concentration, volume))
    np.testing.assert_allclose(simulate([0, 2], t, u)['state'], reference, rtol=2e-9, atol=2e-10)
    np.testing.assert_allclose(constant_input_solution(t, [0, 2], u), reference, rtol=1e-13, atol=1e-14)


def test_closed_form_handles_zero_inlet_and_nearly_balanced_flow():
    t = np.array([0., .3, 2.])
    np.testing.assert_allclose(constant_input_solution(t, [.7, 2], [0, 0, 0, 1, 100]),
                               np.column_stack((np.full(3, .7), 2-.1*t)))
    u = DEFAULT_INPUT.copy(); u[4] += 1e-10
    np.testing.assert_allclose(constant_input_solution(t, [0, 2], u),
                               constant_input_solution(t, [0, 2]), atol=2e-13)
    assert constant_input_solution(0, [.7, 2]).shape == (2,)
    with pytest.raises(ValueError, match='empty'):
        constant_input_solution(20, [.7, 2], [0, 0, 0, 1, 100])


def test_piecewise_input_uses_declared_interval_order_and_absolute_time_origin():
    t = np.array([12., 13., 15., 16.]); u = np.tile(DEFAULT_INPUT, (3, 1))
    u[0, 4] = 650; u[1, 4] = 750; u[2, 2] = .7
    result = simulate([.25, 2], t, u)
    # Independent volume balance across unequal intervals.
    np.testing.assert_allclose(result['state'][:, 1], [2., 2.05, 1.95, 1.95], atol=1e-13)
    expected = np.array([.25, 2.])
    for k in range(3):
        expected = constant_input_solution(t[k+1]-t[k], expected, u[k])
        np.testing.assert_allclose(result['state'][k+1], expected, atol=2e-10)
    np.testing.assert_array_equal(result['inputs'], u)
    # Returned arrays must not provide aliases that mutate caller inputs.
    result['t'][0] = 100.; result['inputs'][0, 0] = 0
    assert t[0] == 12 and u[0, 0] == 500


def test_local_deviation_response_has_second_order_nonlinear_approximation_error():
    t = np.linspace(0, 8, 81)
    errors = []
    for change in (10., 5.):
        u = DEFAULT_INPUT.copy(); u[0] += change; u[4] += change
        actual = simulate(DEFAULT_STATE, t, u)['state'][:, 0]
        linear_absolute = .5+(-.00005*change/.35)*(1-np.exp(-.35*t))
        errors.append(np.max(np.abs(actual-linear_absolute)))
    assert errors[0] > 1e-6
    assert 3.9 < errors[0]/errors[1] < 4.1


@pytest.mark.parametrize('fraction,feeds', [(0., (0., 0.)), (1., (1., 1.)), (.5, (0., 1.))])
def test_physically_admissible_fraction_remains_in_unit_interval(fraction, feeds):
    u = np.array([300., 700., *feeds, 800.])
    states = simulate([fraction, .5], np.linspace(0, 4, 41), u)['state']
    assert np.all(states[:, 0] >= 0) and np.all(states[:, 0] <= 1)
    assert np.all(states[:, 1] > 0)


def test_emptying_is_rejected_before_any_solver_call(monkeypatch):
    import intelligent_control.physical_blending as module
    def forbidden_solver(*args, **kwargs):
        pytest.fail('An unsafe planned volume must be rejected before integration')
    monkeypatch.setattr(module, 'solve_ivp', forbidden_solver)
    with pytest.raises(ValueError, match='minimum_volume'):
        simulate([.5, 2], [0, 10], [500, 200, .4, .75, 900])
    # A later refilling segment does not excuse crossing the guard earlier.
    schedule = [[500, 200, .4, .75, 900], [500, 200, .4, .75, 0]]
    with pytest.raises(ValueError, match='minimum_volume'):
        simulate([.5, 2], [0, 10, 20], schedule)
    with pytest.raises(ValueError, match='Initial'):
        simulate([.5, .01], [0, 1], minimum_volume=.01)


@pytest.mark.parametrize('state,inputs,rho', [
    ([.5, 0], DEFAULT_INPUT, 1000), ([-.1, 2], DEFAULT_INPUT, 1000),
    ([1.1, 2], DEFAULT_INPUT, 1000), ([np.nan, 2], DEFAULT_INPUT, 1000),
    ([.5, 2], [500, -1, .4, .75, 700], 1000),
    ([.5, 2], [500, 200, -.1, .75, 700], 1000),
    ([.5, 2], [500, 200, .4, 1.1, 700], 1000),
    ([.5, 2], [500, 200, .4, .75, -1], 1000),
    ([.5, 2], DEFAULT_INPUT, 0), ([.5, 2], DEFAULT_INPUT, np.inf),
    ([.5, 2], DEFAULT_INPUT, 1j), ([.5, 2], DEFAULT_INPUT, True),
    ([.5+1j, 2], DEFAULT_INPUT, 1000), ([.5, 2], [500, 200, .4, .75], 1000)])
def test_public_rhs_rejects_nonphysical_or_ambiguous_values(state, inputs, rho):
    with pytest.raises(ValueError):
        rhs(state, inputs, rho)


def test_simulation_rejects_bad_schedule_and_time_axes():
    for time in ([0], [0, 0], [1, 0], [0, np.nan]):
        with pytest.raises(ValueError):
            simulate(DEFAULT_STATE, time)
    with pytest.raises(ValueError, match='schedule'):
        simulate(DEFAULT_STATE, [0, 1, 2], np.tile(DEFAULT_INPUT, (3, 1)))
    with pytest.raises(ValueError):
        simulate(DEFAULT_STATE, [0, 1], minimum_volume=-1)

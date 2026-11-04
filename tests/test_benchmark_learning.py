"""Independent contracts for the cross-benchmark teaching extension."""
from pathlib import Path
import numpy as np
from intelligent_control import benchmark_learning as learning


def test_arx_recovers_known_affine_system_and_preserves_units():
    rng=np.random.default_rng(5); u=rng.uniform(-2,2,150); y=np.empty(150); y[0]=4.
    for k in range(149):y[k+1]=.7*y[k]-.2*u[k]+1.2
    fit=learning.fit_record(dict(input=u,output=y))
    a,b,c=fit['theta']; expected_b=-.2*fit['input_scale']/fit['output_scale']
    np.testing.assert_allclose([a,b],[.7,expected_b],atol=1e-12)
    reconstructed=(a*(y[:-1]-fit['output_mean'])/fit['output_scale']+b*(u[:-1]-fit['input_mean'])/fit['input_scale']+c)*fit['output_scale']+fit['output_mean']
    np.testing.assert_allclose(reconstructed,y[1:],atol=1e-12)


def test_pi_target_poles_are_correct_for_both_input_signs():
    for beta in (-.2,.2):
        record=learning.closed_loop([.9,beta,0.])
        np.testing.assert_allclose(np.sort(record['nominal_poles']),[.8,.85],atol=1e-12)
        assert record['status']=='completed'
        assert record['max_input']<=2
        # Recover the actual recurrence from an unsaturated constant-reference
        # segment, independently of the implementation's reported pole array.
        error=record['trace'][12:40,1]-record['trace'][12:40,2]
        coeff=np.linalg.lstsq(np.c_[error[1:-1],error[:-2]],error[2:],rcond=None)[0]
        np.testing.assert_allclose(coeff,[1.65,-.68],atol=1e-9)


def test_predictor_mpc_respects_actuator_and_slew_bounds():
    record=learning.closed_loop([.85,.2,0.],policy='mpc',steps=65)
    assert record['solver_failures']==0
    assert record['status']=='completed'
    u=record['trace'][:,3]
    assert np.abs(u).max()<=2+1e-9
    assert np.max(np.abs(np.diff(np.r_[0,u])))<=.4+1e-7
    assert record['rmse']<.2


def test_sensor_reference_is_translation_and_unit_invariant():
    clean=np.linspace(30,40,200)
    a=learning.sensor_diagnosis(clean,.5)
    b=learning.sensor_diagnosis(clean*1000+273.15,500)
    np.testing.assert_allclose(a['traces'],b['traces'])
    np.testing.assert_allclose(a['traces'][:,2:].sum(1),1.,atol=1e-12)


def test_artificial_records_use_distinct_seeds_and_exact_recurrence():
    from intelligent_control.benchmarks import siso_step
    a,b=learning.generate_records('artificial_siso',Path(__file__).resolve().parents[1],samples=50)
    assert not np.array_equal(a['input'],b['input'])
    for record in (a,b):
        y=record['output']; u=record['input']
        expected=[siso_step(y[k],y[k-1] if k else 0.,u[k]) for k in range(49)]
        np.testing.assert_allclose(y[1:],expected,rtol=0,atol=0)

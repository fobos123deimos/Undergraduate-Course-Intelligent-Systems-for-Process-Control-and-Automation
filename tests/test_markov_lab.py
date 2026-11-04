"""Physical and information-flow checks for the sensor-diagnosis laboratory."""

import json
from math import erf, sqrt

import numpy as np
import pytest

from intelligent_control import markov_lab as lab


@pytest.fixture(scope="module")
def calibration():
    return lab.calibrate()


def test_residual_categories_and_gaussian_emission_integrals():
    assert np.array_equal(lab.symbols([-.1, .025, .094999, .095, 1]), [0, 1, 1, 2, 2])
    expected = []
    for bias in [0, .055, .14]:
        low = (1 + erf((.025 - bias) / (.035 * sqrt(2)))) / 2
        high = (1 + erf((.095 - bias) / (.035 * sqrt(2)))) / 2
        expected.append([low, high - low, 1 - high])
    actual = lab.theoretical_emission()
    assert np.allclose(actual, expected, rtol=0, atol=1e-15)
    assert np.allclose(actual.sum(axis=1), 1)
    assert np.array_equal(actual.argmax(axis=1), [0, 1, 2])


def test_calibration_is_reproducible_and_has_finite_bias_estimates(calibration):
    model, bias, observations = calibration
    repeated, repeated_bias, repeated_observations = lab.calibrate()
    assert np.array_equal(model.transition, repeated.transition)
    assert np.array_equal(model.emission, repeated.emission)
    assert np.array_equal(bias, repeated_bias)
    assert all(np.array_equal(left, right) for left, right in zip(observations, repeated_observations))
    assert len(observations) == 20
    assert all(len(sequence) == 150 for sequence in observations)
    assert np.all(np.isfinite(bias))
    assert np.allclose(bias, lab.BIAS, rtol=0, atol=.012)


@pytest.mark.parametrize("tau", [10., 14.])
@pytest.mark.parametrize("compensate", [False, True])
def test_predictor_uses_past_applied_inputs_and_traces_are_bounded(calibration, tau, compensate):
    model, bias, _ = calibration
    states = np.tile([0, 1, 2, 2, 1], 100)
    noise = np.random.default_rng(91).normal(0, lab.NOISE_STD, len(states))
    trace = lab.simulate_sensor_control(model, bias, states, noise, tau, compensate)
    for key in ("output", "prediction", "measurement", "control", "posterior"):
        assert np.all(np.isfinite(trace[key]))
    assert np.all((trace["control"] >= 0) & (trace["control"] <= 1))
    assert np.all((trace["output"] >= 0) & (trace["output"] <= 1))
    assert np.allclose(trace["posterior"].sum(axis=1), 1)
    # Independently derived exact zero-order-hold first-order tank recursion.
    nominal_decay, actual_decay = np.exp(-lab.DT / 10), np.exp(-lab.DT / tau)
    assert np.allclose(trace["prediction"][1:], nominal_decay * trace["prediction"][:-1]
                       + (1 - nominal_decay) * trace["control"][:-1], rtol=0, atol=1e-14)
    assert np.allclose(trace["output"][1:], actual_decay * trace["output"][:-1]
                       + (1 - actual_decay) * trace["control"][:-1], rtol=0, atol=1e-14)
    if tau == 10:
        assert np.array_equal(trace["prediction"], trace["output"])
        residual = lab.BIAS[states] + noise
        expected = model.filter(lab.symbols(residual))["filtered"]
        assert np.allclose(trace["posterior"], expected, rtol=0, atol=1e-14)


def test_controller_and_filter_are_causal_under_future_changes(calibration):
    model, bias, _ = calibration
    states = np.tile([0, 1, 2, 1], 50)
    noise = np.random.default_rng(22).normal(0, lab.NOISE_STD, len(states))
    original = lab.simulate_sensor_control(model, bias, states, noise, tau=14, compensate=True)
    modified_states, modified_noise = states.copy(), noise.copy()
    cut = 115
    modified_states[cut:] = 2
    modified_noise[cut:] = .4
    changed = lab.simulate_sensor_control(model, bias, modified_states, modified_noise,
                                          tau=14, compensate=True)
    for key in ("control", "output", "prediction", "posterior"):
        assert np.array_equal(original[key][:cut], changed[key][:cut])
    assert not np.allclose(original["control"][cut:], changed["control"][cut:])


def test_hidden_labels_affect_control_only_through_sensor_values(calibration):
    model, bias, _ = calibration
    states = np.tile([0, 1, 2, 1], 40)
    noise = np.random.default_rng(41).normal(0, lab.NOISE_STD, len(states))
    original = lab.simulate_sensor_control(model, bias, states, noise, tau=14, compensate=True)
    relabeled = (states + 1) % 3
    equivalent_noise = noise + lab.BIAS[states] - lab.BIAS[relabeled]
    equivalent = lab.simulate_sensor_control(model, bias, relabeled, equivalent_noise,
                                             tau=14, compensate=True)
    for key in ("control", "output", "prediction", "measurement", "posterior"):
        assert np.allclose(original[key], equivalent[key], rtol=0, atol=1e-13)


def test_full_experiment_keeps_calibration_and_test_records_separate(monkeypatch):
    supervised, unsupervised = lab.fit_supervised, lab.baum_welch
    seen = {}

    def inspect_supervised(states, observations, *args, **kwargs):
        seen["states"], seen["observations"] = states, observations
        return supervised(states, observations, *args, **kwargs)

    def inspect_unsupervised(observations, *args, **kwargs):
        seen["em_observations"] = observations
        return unsupervised(observations, *args, **kwargs)

    monkeypatch.setattr(lab, "fit_supervised", inspect_supervised)
    monkeypatch.setattr(lab, "baum_welch", inspect_unsupervised)
    result = lab.run_markov_experiment()
    test = result["diagnosis"]
    assert len(seen["states"]) == len(seen["observations"]) == 20
    assert seen["em_observations"] is seen["observations"]
    assert len(test["states"]) == len(test["observations"]) == 600
    for states, observations in zip(seen["states"], seen["observations"]):
        assert len(states) == len(observations) == 150
        assert not np.shares_memory(states, test["states"])
        assert not np.shares_memory(observations, test["observations"])
    # The durable result must be serializable without NaN or implementation objects.
    json.dumps(result["summary"], allow_nan=False)
    history = result["summary"]["baum_welch"]["training_log_likelihood"]
    assert np.all(np.diff(history) >= 0)
    assert result["summary"]["baum_welch"]["semantic_accuracy"] is None
    assert len(result["traces"]) == 4


def test_alarm_metrics_define_empty_denominators():
    no_fault = np.zeros(4, dtype=int)
    posterior = np.tile([1., 0., 0.], (4, 1))
    result = lab.alarm_metrics(no_fault, posterior)
    assert result["precision"] is None and result["recall"] is None
    assert result["false_alarm_rate"] == 0
    assert result["true_negative"] == 4

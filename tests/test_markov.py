"""Analytic chain cases and exhaustive, independent small-HMM oracles."""

from itertools import product

import numpy as np
import pytest

from intelligent_control.markov import (
    CategoricalHMM, baum_welch, fit_supervised, hitting_statistics,
    n_step_distribution, sample_markov, stationary_distribution,
    validate_transition,
)


def enumerate_paths(initial, transition, emission, observations):
    """Multiply full path probabilities; do not reuse dynamic recursions."""
    paths = np.array(list(product(range(len(initial)), repeat=len(observations))))
    weights = []
    for path in paths:
        weight = initial[path[0]] * emission[path[0], observations[0]]
        for t in range(1, len(observations)):
            weight *= transition[path[t - 1], path[t]] * emission[path[t], observations[t]]
        weights.append(weight)
    return paths, np.array(weights)


@pytest.fixture
def model():
    return CategoricalHMM([.6, .4], [[.7, .3], [.2, .8]], [[.6, .3, .1], [.1, .3, .6]])


def test_chain_propagation_stationarity_and_periodicity():
    transition = np.array([[.9, .1], [.2, .8]])
    assert np.allclose(n_step_distribution([1, 0], transition, 2), [.83, .17])
    assert np.allclose(n_step_distribution([1, 0], transition, 5), [.72269, .27731])
    assert np.array_equal(n_step_distribution([1, 0], transition, 0), [1, 0])
    stationary = stationary_distribution(transition)
    assert np.allclose(stationary, [2 / 3, 1 / 3])
    assert np.allclose(stationary @ transition, stationary)
    cycle = [[0, 1], [1, 0]]
    assert np.allclose(stationary_distribution(cycle), [.5, .5])
    assert np.array_equal(n_step_distribution([1, 0], cycle, 9), [0, 1])
    assert np.array_equal(stationary_distribution([[.5, .5], [0, 1]]), [0, 1])
    with pytest.raises(ValueError, match="not unique"):
        stationary_distribution(np.eye(2))


def test_hitting_times_analytic_and_multiple_failure_classes():
    geometric = hitting_statistics([[.75, .25], [0, 1]], [1])
    assert np.allclose(geometric["probability"], [1, 1])
    assert np.allclose(geometric["expected_steps"], [4, 0])
    process = [[.8, .15, .05], [.1, .7, .2], [0, 0, 1]]
    hit = hitting_statistics(process, [2])
    assert np.allclose(hit["probability"], 1)
    assert np.allclose(hit["expected_steps"], [10, 20 / 3, 0])
    assert n_step_distribution([1, 0, 0], process, 2)[2] == pytest.approx(.12)
    competing = hitting_statistics([[0, .5, .5], [0, 1, 0], [0, 0, 1]], [1])
    assert np.allclose(competing["probability"], [.5, 1, 0])
    assert np.array_equal(competing["expected_steps"], [np.inf, 0, np.inf])
    all_targets = hitting_statistics(np.eye(2), [0, 1])
    assert np.array_equal(all_targets["expected_steps"], [0, 0])
    # First passage stops at target, even if the original target can leave.
    assert np.array_equal(hitting_statistics([[0, 1], [1, 0]], [1])["expected_steps"], [1, 0])


def test_tiny_but_positive_failure_probability_still_gives_infinite_time():
    tiny = 1e-13
    hit = hitting_statistics([[0, 1 - tiny, tiny], [0, 1, 0], [0, 0, 1]], [1])
    assert np.isinf(hit["expected_steps"][0])


@pytest.mark.parametrize("transition", [[], [[1, 0, 0], [0, 1, 0]], [[.5, .6], [.2, .8]],
                                      [[1.1, -.1], [0, 1]], [[np.nan, 0], [0, 1]],
                                      [[np.inf, 0], [0, 1]], [[1j]]])
def test_reject_invalid_probability_matrices(transition):
    with pytest.raises(ValueError):
        validate_transition(transition)


@pytest.mark.parametrize("steps", [-1, .5, np.inf, True])
def test_reject_invalid_chain_step_counts(steps):
    with pytest.raises(ValueError):
        n_step_distribution([1], [[1]], steps)


def test_reject_invalid_chain_initial_and_targets():
    for initial in ([.5], [.2, .2], [np.nan, 0], [-.1, 1.1]):
        with pytest.raises(ValueError):
            n_step_distribution(initial, np.eye(2), 1)
    for targets in ([], [2], [-1], [0.5], [True]):
        with pytest.raises(ValueError):
            hitting_statistics(np.eye(2), targets)


def test_filter_smoother_pairwise_and_viterbi_against_exhaustive_oracle(model):
    observations = np.array([0, 1, 2, 1])
    paths, weights = enumerate_paths(model.initial, model.transition, model.emission, observations)
    total = weights.sum()
    posterior = model.smooth(observations)
    assert posterior["log_likelihood"] == pytest.approx(np.log(total), abs=1e-14)
    for t in range(len(observations)):
        prefix_paths, prefix_weights = enumerate_paths(model.initial, model.transition,
                                                       model.emission, observations[:t + 1])
        for state in range(2):
            assert posterior["smoothed"][t, state] == pytest.approx(
                weights[paths[:, t] == state].sum() / total, abs=1e-14)
            assert posterior["filtered"][t, state] == pytest.approx(
                prefix_weights[prefix_paths[:, -1] == state].sum() / prefix_weights.sum(), abs=1e-14)
        if t + 1 < len(observations):
            for left, right in product(range(2), repeat=2):
                joint = (paths[:, t] == left) & (paths[:, t + 1] == right)
                assert posterior["pairwise"][t, left, right] == pytest.approx(
                    weights[joint].sum() / total, abs=1e-14)
    best = model.viterbi(observations)
    assert np.array_equal(best["states"], paths[weights.argmax()])
    assert best["log_probability"] == pytest.approx(np.log(weights.max()), abs=1e-14)
    assert best["log_probability"] <= posterior["log_likelihood"]


def test_course_binary_hmm_worked_example():
    example = CategoricalHMM([.6, .4], [[.7, .3], [.4, .6]], [[.5, .5], [.1, .9]])
    posterior = example.smooth([0, 1, 0])
    assert np.exp(posterior["log_likelihood"]) == pytest.approx(.069616)
    assert np.allclose(posterior["filtered"][:, 0], [.882352941, .524118738, .862876350])
    assert np.allclose(posterior["smoothed"][:, 0], [.875660768, .616812227, .862876350])
    path = example.viterbi([0, 1, 0])
    assert np.array_equal(path["states"], [0, 0, 0])
    assert np.exp(path["log_probability"]) == pytest.approx(.03675)


def test_scaled_filter_long_record_and_causal_prefix(model):
    observations = np.tile([0, 1, 2], 4000)
    result = model.filter(observations)
    assert np.isfinite(result["log_likelihood"])
    assert result["log_likelihood"] < -1000
    assert np.allclose(result["filtered"].sum(axis=1), 1)
    assert np.allclose(result["filtered"][:17], model.filter(observations[:17])["filtered"])
    assert np.all(result["scales"] > 0)


def test_single_observation_and_structural_zero_cases():
    certain = CategoricalHMM([1, 0], [[1, 0], [0, 1]], [[1, 0], [0, 1]])
    posterior = certain.smooth([0])
    assert posterior["pairwise"].shape == (0, 2, 2)
    assert np.array_equal(posterior["smoothed"], [[1, 0]])
    assert certain.viterbi([0, 0])["log_probability"] == 0
    for method in (certain.filter, certain.smooth, certain.viterbi):
        with pytest.raises(ValueError, match="impossible"):
            method([0, 1])


@pytest.mark.parametrize("observations", [[], [-1], [3], [0.0], [[0]], [np.nan], [True]])
def test_reject_invalid_observations(model, observations):
    for method in (model.filter, model.smooth, model.viterbi):
        with pytest.raises(ValueError):
            method(observations)


def test_hmm_parameters_are_copied_and_checked():
    transition = np.eye(2)
    model = CategoricalHMM([1, 0], transition, [[1, 0], [0, 1]])
    transition[0] = [0, 1]
    assert model.transition[0, 0] == 1
    with pytest.raises(ValueError):
        model.emission[0, 0] = .5
    for emission in ([[1]], [[.5, .6], [0, 1]], [[np.nan, 0], [0, 1]]):
        with pytest.raises(ValueError):
            CategoricalHMM([1, 0], np.eye(2), emission)


def test_seeded_sampling_obeys_support_and_is_reproducible(model):
    first = model.sample(200, seed=13)
    second = model.sample(200, seed=13)
    assert all(np.array_equal(a, b) for a, b in zip(first, second))
    assert all(array.shape == (200,) for array in first)
    assert np.all(first[0] < 2) and np.all(first[1] < 3)
    states = sample_markov([[0, 1], [1, 0]], [1, 0], 10, rng=4)
    assert np.array_equal(states, np.arange(10) % 2)
    deterministic = CategoricalHMM([1, 0], [[0, 1], [1, 0]], np.eye(2))
    states, observations = deterministic.sample(20, seed=2)
    assert np.array_equal(states, observations)
    with pytest.raises(ValueError):
        model.sample(0)


def test_supervised_estimation_never_joins_records():
    model = fit_supervised([[0, 0], [1, 1]], [[0, 1], [1, 1]], 2, 2, pseudocount=.5)
    assert np.allclose(model.initial, [.5, .5])
    assert np.allclose(model.transition, [[.75, .25], [.25, .75]])
    assert np.allclose(model.emission, [[.5, .5], [1 / 6, 5 / 6]])
    course = fit_supervised([[0, 0, 1, 1], [1, 0, 0]], [[0, 0, 1, 1], [1, 0, 1]], 2, 2, 1)
    assert np.allclose(course.transition, [[.6, .4], [.5, .5]])
    assert np.allclose(course.emission, [[2 / 3, 1 / 3], [.2, .8]])


def test_supervised_validation_and_unobserved_rows():
    cases = [([], [], 2, 2, 1), ([[0]], [[0], [1]], 2, 2, 1),
             ([[0, 1]], [[0]], 2, 2, 1), ([[2]], [[0]], 2, 2, 1),
             ([[0]], [[2]], 2, 2, 1), ([[0.5]], [[0]], 2, 2, 1),
             ([0, 1], [0, 1], 2, 2, 1), ([[0]], [[0]], 2, 2, 0),
             ([[0]], [[0]], 2, 2, -1), ([[0]], [[0]], 2, 2, np.inf)]
    for args in cases:
        with pytest.raises(ValueError):
            fit_supervised(*args)


def test_baum_welch_likelihood_increases_and_preserves_probability_invariants(model):
    training = [model.sample(70, seed=seed)[1] for seed in range(4)]
    start = CategoricalHMM([.5, .5], [[.65, .35], [.35, .65]], [[.5, .3, .2], [.2, .3, .5]])
    fitted = baum_welch(training, start, max_iter=20, tol=1e-8)
    history = fitted["log_likelihood_history"]
    assert len(history) >= 2
    assert np.all(np.diff(history) >= 0)
    assert history[-1] > history[0] + .1
    assert fitted["iterations"] == len(history) - 1
    model = fitted["model"]
    assert np.allclose(model.transition.sum(axis=1), 1)
    assert np.allclose(model.emission.sum(axis=1), 1)
    assert model.initial.sum() == pytest.approx(1)
    assert history[-1] == pytest.approx(sum(model.filter(sequence)["log_likelihood"] for sequence in training))


def test_baum_welch_singleton_sequences_have_no_boundary_transition():
    start = CategoricalHMM([.5, .5], [[.8, .2], [.3, .7]], [[.8, .2], [.2, .8]])
    fitted = baum_welch([[0], [1], [0]], start, max_iter=3)
    assert np.array_equal(fitted["model"].transition, start.transition)
    for observations in ([], [0, 1], [[2]], [[0], []]):
        with pytest.raises(ValueError):
            baum_welch(observations, start)
    for tol in (-1, np.nan, np.inf):
        with pytest.raises(ValueError):
            baum_welch([[0]], start, tol=tol)


def test_baum_welch_preserves_unoccupied_state_rows_and_rejects_impossible_data():
    start = CategoricalHMM([1, 0], [[1, 0], [.3, .7]], [[1, 0], [.2, .8]])
    fitted = baum_welch([[0, 0]], start)
    assert np.array_equal(fitted["model"].transition[1], start.transition[1])
    assert np.array_equal(fitted["model"].emission[1], start.emission[1])
    with pytest.raises(ValueError, match="impossible"):
        baum_welch([[1]], start)

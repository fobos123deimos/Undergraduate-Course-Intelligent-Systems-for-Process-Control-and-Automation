"""Finite Markov chains and categorical hidden Markov models, using NumPy.

Conventions: transition[i, j] = P(z[t+1]=j | z[t]=i), distributions are
row vectors, and states and symbols use zero-based integer indices. The initial
state emits observation zero, before the first transition. Filtering uses only
observations available at that time; smoothing and Viterbi use the full record.

References
----------
L. R. Rabiner (1989), "A tutorial on hidden Markov models and selected
applications in speech recognition", Proceedings of the IEEE 77(2), 257-286.
https://doi.org/10.1109/5.18626
MIT 6.856, Markov Chains (row distributions, stationarity and hitting times):
https://courses.csail.mit.edu/6.856/21/Notes/n25-markov-chains.html
"""

import numpy as np


def _integer(value, name, minimum=0):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        raise ValueError(f"{name} must be an integer")
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return int(value)


def _probabilities(value, name, ndim):
    if np.iscomplexobj(value):
        raise ValueError(f"{name} must contain real probabilities")
    try:
        value = np.array(value, dtype=float, copy=True)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must contain real probabilities") from error
    if value.ndim != ndim or not value.size or any(size == 0 for size in value.shape):
        raise ValueError(f"{name} must be a nonempty {ndim}-dimensional array")
    if not np.all(np.isfinite(value)) or np.any(value < 0) or np.any(value > 1):
        raise ValueError(f"{name} must contain finite probabilities in [0, 1]")
    if not np.allclose(value.sum(axis=-1), 1, rtol=0, atol=1e-12):
        raise ValueError(f"{name} probabilities must sum to one along each row")
    return value


def validate_transition(transition):
    """Return a checked copy of a square row-stochastic matrix.

    Invalid rows are rejected rather than silently normalized.
    """
    transition = _probabilities(transition, "transition", 2)
    if transition.shape[0] != transition.shape[1]:
        raise ValueError("transition must be square")
    return transition


def _initial(initial, n_states):
    initial = _probabilities(initial, "initial", 1)
    if initial.size != n_states:
        raise ValueError("initial and transition state counts differ")
    return initial


def _indices(values, upper, name):
    values = np.asarray(values)
    if values.ndim != 1 or not values.size:
        raise ValueError(f"{name} must be a nonempty one-dimensional integer sequence")
    if values.dtype.kind not in "iu" or np.any(values < 0) or np.any(values >= upper):
        raise ValueError(f"{name} must contain integer indices in [0, {upper})")
    return values.astype(np.int64, copy=True)


def n_step_distribution(initial, transition, steps):
    """Compute initial @ transition**steps, with step zero returning initial."""
    transition = validate_transition(transition)
    initial = _initial(initial, len(transition))
    steps = _integer(steps, "steps")
    return initial @ np.linalg.matrix_power(transition, steps)


def _reachability(transition):
    reachable = transition > 0
    np.fill_diagonal(reachable, True)
    for k in range(len(transition)):
        reachable |= reachable[:, k, None] & reachable[None, k, :]
    return reachable


def stationary_distribution(transition):
    """Compute the unique stationary distribution or reject nonuniqueness.

    A finite chain has a unique stationary distribution when it has exactly one
    closed communicating class; irreducibility is sufficient but not necessary.
    Periodicity does not prevent stationarity, but can prevent convergence of
    the distribution from an arbitrary initial state.
    """
    transition = validate_transition(transition)
    reachable = _reachability(transition)
    remaining = set(range(len(transition)))
    closed = []
    while remaining:
        state = min(remaining)
        component = np.flatnonzero(reachable[state] & reachable[:, state])
        remaining.difference_update(component)
        outside = np.ones(len(transition), dtype=bool)
        outside[component] = False
        if not np.any(transition[np.ix_(component, np.flatnonzero(outside))] > 0):
            closed.append(component)
    if len(closed) != 1:
        raise ValueError("stationary distribution is not unique (multiple closed classes)")
    component = closed[0]
    restricted = transition[np.ix_(component, component)]
    system = restricted.T - np.eye(len(component))
    system[-1] = 1
    rhs = np.zeros(len(component))
    rhs[-1] = 1
    weights = np.linalg.solve(system, rhs)
    if np.any(weights < -1e-12):
        raise ArithmeticError("stationary solve produced negative probability")
    weights = np.maximum(weights, 0)
    weights /= weights.sum()
    stationary = np.zeros(len(transition))
    stationary[component] = weights
    if not np.allclose(stationary @ transition, stationary, rtol=0, atol=1e-10):
        raise ArithmeticError("stationary solve failed its invariance check")
    return stationary


def hitting_statistics(transition, targets):
    """Return eventual hit probabilities and unconditional mean hitting times.

    ``targets`` is a nonempty sequence of state indices. A target is reached at
    time zero when starting there, irrespective of its outgoing transitions.
    ``expected_steps`` is infinite if there is any positive probability of
    never hitting a target. Multiply finite step counts by the sample interval
    to obtain physical time. This handles reducible chains and competing
    absorbing classes without inverting a singular full transient block.
    """
    transition = validate_transition(transition)
    targets = np.unique(_indices(targets, len(transition), "targets"))
    stopped = transition.copy()
    stopped[targets] = 0
    stopped[targets, targets] = 1
    reachable = _reachability(stopped)
    can_hit = reachable[:, targets].any(axis=1)
    target_mask = np.zeros(len(transition), dtype=bool)
    target_mask[targets] = True
    candidates = np.flatnonzero(can_hit & ~target_mask)
    probability = target_mask.astype(float)
    if candidates.size:
        q = stopped[np.ix_(candidates, candidates)]
        direct = stopped[np.ix_(candidates, targets)].sum(axis=1)
        probability[candidates] = np.linalg.solve(np.eye(len(q)) - q, direct)
    if np.any(probability < -1e-10) or np.any(probability > 1 + 1e-10):
        raise ArithmeticError("hitting probability solve left [0, 1]")
    probability = np.clip(probability, 0, 1)
    # Any path into a class unable to reach the target makes the mean infinite.
    can_miss = reachable[:, ~can_hit].any(axis=1)
    certain = np.flatnonzero(~target_mask & ~can_miss)
    expected = np.full(len(transition), np.inf)
    expected[targets] = 0
    if certain.size:
        q = stopped[np.ix_(certain, certain)]
        expected[certain] = np.linalg.solve(np.eye(len(q)) - q, np.ones(len(q)))
    return {"probability": probability, "expected_steps": expected}


def sample_markov(transition, initial, length, rng=None):
    """Sample ``length`` states; ``rng`` accepts a seed or NumPy Generator."""
    transition = validate_transition(transition)
    initial = _initial(initial, len(transition))
    length = _integer(length, "length", minimum=1)
    rng = np.random.default_rng(rng)
    states = np.empty(length, dtype=int)
    states[0] = rng.choice(len(initial), p=initial)
    for t in range(1, length):
        states[t] = rng.choice(len(initial), p=transition[states[t - 1]])
    return states


def _log_probability(value):
    result = np.full(value.shape, -np.inf)
    np.log(value, out=result, where=value > 0)
    return result


class CategoricalHMM:
    """Discrete emissions with emission[state, symbol] = P(symbol | state).

    Arrays are checked, copied and made read-only. The scaled recursions avoid
    multiplying the many small probabilities of a full observation record.
    An impossible sequence raises ValueError instead of returning a fabricated
    posterior. Exact zeros represent structural impossibilities.
    """

    def __init__(self, initial, transition, emission):
        self.transition = validate_transition(transition)
        self.initial = _initial(initial, len(self.transition))
        self.emission = _probabilities(emission, "emission", 2)
        if len(self.emission) != len(self.transition):
            raise ValueError("emission and transition state counts differ")
        for array in (self.initial, self.transition, self.emission):
            array.setflags(write=False)

    def filter(self, observations):
        """Causal P(z[t] | observations[:t+1]) and log P(observations)."""
        observations = _indices(observations, self.emission.shape[1], "observations")
        filtered = np.empty((len(observations), len(self.initial)))
        scales = np.empty(len(observations))
        prior = self.initial
        for t, symbol in enumerate(observations):
            joint = prior * self.emission[:, symbol]
            scales[t] = joint.sum()
            if scales[t] <= 0:
                raise ValueError(f"impossible observation sequence at index {t}")
            filtered[t] = joint / scales[t]
            prior = filtered[t] @ self.transition
        return {"filtered": filtered, "scales": scales,
                "log_likelihood": float(np.log(scales).sum())}

    def smooth(self, observations):
        """Retrospective state and adjacent-state posteriors for a full record.

        ``pairwise[t,i,j]`` is P(z[t]=i,z[t+1]=j | all observations).
        It has shape (T-1, n_states, n_states), including when T is one.
        """
        observations = _indices(observations, self.emission.shape[1], "observations")
        result = self.filter(observations)
        filtered, scales = result["filtered"], result["scales"]
        backward = np.ones_like(filtered)
        pairwise = np.empty((len(observations) - 1, len(self.initial), len(self.initial)))
        for t in range(len(observations) - 2, -1, -1):
            likelihood = self.emission[:, observations[t + 1]] * backward[t + 1]
            backward[t] = (self.transition @ likelihood) / scales[t + 1]
            pairwise[t] = filtered[t, :, None] * self.transition * likelihood[None, :]
            pairwise[t] /= pairwise[t].sum()
        smoothed = filtered * backward
        smoothed /= smoothed.sum(axis=1, keepdims=True)
        return {**result, "smoothed": smoothed, "pairwise": pairwise}

    def viterbi(self, observations):
        """Most probable complete state path and its joint log probability.

        This is not the sequence of individual marginal posterior maxima.
        Ties follow NumPy's first-index rule in each dynamic-programming step.
        """
        observations = _indices(observations, self.emission.shape[1], "observations")
        log_transition = _log_probability(self.transition)
        log_emission = _log_probability(self.emission)
        scores = _log_probability(self.initial) + log_emission[:, observations[0]]
        previous = np.zeros((len(observations), len(self.initial)), dtype=int)
        for t in range(1, len(observations)):
            candidates = scores[:, None] + log_transition
            previous[t] = candidates.argmax(axis=0)
            scores = candidates.max(axis=0) + log_emission[:, observations[t]]
        if not np.any(np.isfinite(scores)):
            raise ValueError("impossible observation sequence")
        states = np.empty(len(observations), dtype=int)
        states[-1] = scores.argmax()
        log_probability = float(scores[states[-1]])
        for t in range(len(observations) - 1, 0, -1):
            states[t - 1] = previous[t, states[t]]
        return {"states": states, "log_probability": log_probability}

    def sample(self, length, seed=None):
        """Return (states, observations); seed also accepts a NumPy Generator."""
        rng = np.random.default_rng(seed)
        states = sample_markov(self.transition, self.initial, length, rng)
        observations = np.array([rng.choice(self.emission.shape[1], p=self.emission[state])
                                 for state in states], dtype=int)
        return states, observations


def _sequences(sequences, upper, name):
    if not isinstance(sequences, (list, tuple)) or not sequences:
        raise ValueError(f"{name} must be a nonempty list of separate sequences")
    return [_indices(sequence, upper, name) for sequence in sequences]


def _normalize_counts(counts, name, fallback=None):
    totals = counts.sum(axis=-1, keepdims=True)
    missing = totals[:, 0] == 0
    if np.any(missing) and fallback is None:
        raise ValueError(f"{name} has unobserved rows; use a positive pseudocount")
    result = np.divide(counts, totals, out=np.zeros_like(counts), where=totals > 0)
    if fallback is not None:
        result[missing] = fallback[missing]
    return result


def fit_supervised(state_sequences, observation_sequences, n_states, n_symbols, pseudocount=1.0):
    """Estimate a categorical HMM from separate, labeled training records.

    Count one initial state per record and transitions only within records.
    A nonnegative additive pseudocount is applied to initial, transition and
    emission counts. With zero smoothing, an entirely unobserved transition or
    emission row is rejected. The caller must keep test records separate.
    """
    n_states = _integer(n_states, "n_states", minimum=1)
    n_symbols = _integer(n_symbols, "n_symbols", minimum=1)
    if not np.isscalar(pseudocount) or not np.isfinite(pseudocount) or pseudocount < 0:
        raise ValueError("pseudocount must be finite and nonnegative")
    states = _sequences(state_sequences, n_states, "state_sequences")
    observations = _sequences(observation_sequences, n_symbols, "observation_sequences")
    if len(states) != len(observations):
        raise ValueError("state and observation record counts differ")
    initial = np.full(n_states, float(pseudocount))
    transition = np.full((n_states, n_states), float(pseudocount))
    emission = np.full((n_states, n_symbols), float(pseudocount))
    for state, observation in zip(states, observations):
        if len(state) != len(observation):
            raise ValueError("state and observation sequence lengths differ")
        initial[state[0]] += 1
        np.add.at(transition, (state[:-1], state[1:]), 1)
        np.add.at(emission, (state, observation), 1)
    return CategoricalHMM(initial / initial.sum(),
                          _normalize_counts(transition, "transition"),
                          _normalize_counts(emission, "emission"))


def baum_welch(observation_sequences, initial_model, max_iter=100, tol=1e-6):
    """Unsupervised maximum-likelihood EM on separate training records.

    Return a model, accepted log-likelihood history, iteration count and
    convergence flag. No pseudocount is used: each accepted M-step must not
    decrease observed-data likelihood beyond rounding. An unoccupied row keeps
    its previous value. Initial structural zeros remain structural zeros.
    EM finds a local optimum, state labels are interchangeable, and held-out
    records must not be passed to this training function.
    """
    if not isinstance(initial_model, CategoricalHMM):
        raise ValueError("initial_model must be a CategoricalHMM")
    max_iter = _integer(max_iter, "max_iter", minimum=1)
    if not np.isscalar(tol) or not np.isfinite(tol) or tol < 0:
        raise ValueError("tol must be finite and nonnegative")
    observations = _sequences(observation_sequences, initial_model.emission.shape[1],
                              "observation_sequences")
    model = initial_model
    history = [sum(model.filter(sequence)["log_likelihood"] for sequence in observations)]
    converged = False
    for _ in range(max_iter):
        initial = np.zeros_like(model.initial)
        transition = np.zeros_like(model.transition)
        emission = np.zeros_like(model.emission)
        for sequence in observations:
            posterior = model.smooth(sequence)
            gamma = posterior["smoothed"]
            initial += gamma[0]
            transition += posterior["pairwise"].sum(axis=0)
            for symbol in range(emission.shape[1]):
                emission[:, symbol] += gamma[sequence == symbol].sum(axis=0)
        candidate = CategoricalHMM(initial / initial.sum(),
                                   _normalize_counts(transition, "transition", model.transition),
                                   _normalize_counts(emission, "emission", model.emission))
        likelihood = sum(candidate.filter(sequence)["log_likelihood"] for sequence in observations)
        improvement = likelihood - history[-1]
        if improvement < -1e-10 * max(1, abs(history[-1])):
            raise ArithmeticError("Baum-Welch likelihood decreased beyond numerical tolerance")
        if improvement < 0:
            converged = True
            break
        model = candidate
        history.append(likelihood)
        if improvement <= tol * max(1, abs(history[-2])):
            converged = True
            break
    return {"model": model, "log_likelihood_history": np.array(history),
            "iterations": len(history) - 1, "converged": converged}

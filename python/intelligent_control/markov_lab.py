"""Synthetic sensor diagnosis with Markov chains, categorical HMMs and PI.

The three hidden modes are normal, drift and sensor fault, with fixed
positive concentration biases. Residuals are discretized using `symbols`.
Time is measured in minutes and the sample interval is `DT`.

Hidden labels are available only to synthetic calibration and retrospective
scoring. All settings are fixed before an independent test trajectory is
generated. Only causal filtering enters compensated control; smoothing and
Viterbi remain offline. The nominal predictor has a known initial state and
past applied inputs, an explicit information advantage over ordinary PI.

`run_markov_experiment` returns numerical records without writing files.
`save_markov_result` exports inspectable results and figures. This laboratory
is an enrichment beyond the supplied article models, not industrial fault
reliability evidence.
"""
from pathlib import Path
import json
import numpy as np
from scipy.special import ndtr
from .markov import (CategoricalHMM, sample_markov, stationary_distribution,
                     n_step_distribution, hitting_statistics, fit_supervised,
                     baum_welch)
from .methods import Tank, PID, control_metrics

TRANSITION = np.array([[.97, .025, .005], [.04, .93, .03], [.02, .08, .9]])
PRIOR = np.array([.8, .15, .05])
BIAS = np.array([0., .055, .14])
CUTPOINTS = np.array([.025, .095])
NOISE_STD = .035
DT = .2
STATE_NAMES = ['normal', 'drift', 'sensor fault']


def symbols(residual):
    """0: residual<.025; 1: .025<=residual<.095; 2: residual>=.095."""
    return np.digitize(residual, CUTPOINTS)


def theoretical_emission():
    """Integrate the declared Gaussian residual law over the three symbols.

    Return a ``(3, 3)`` emission matrix with sensor modes as rows and observed
    symbols as columns. The means are `BIAS`, noise scale is `NOISE_STD` and
    category boundaries are `CUTPOINTS`. These are known simulator parameters,
    not estimates from measured data.
    """
    cdf = ndtr((CUTPOINTS[None, :] - BIAS[:, None]) / NOISE_STD)
    return np.column_stack((cdf[:, 0], cdf[:, 1]-cdf[:, 0], 1-cdf[:, 1]))


def calibrate(seed=17, trajectories=20, length=150):
    """Fit a supervised HMM and sensor-bias means on separate records.

    Parameters
    ----------
    seed : int, optional
        Reproducible generator seed for calibration only.
    trajectories : int, optional
        Number of independent synthetic records.
    length : int, optional
        Number of observations in each record.

    Returns
    -------
    model : CategoricalHMM
        Estimated initial, transition and categorical emission probabilities,
        using pseudocount one and respecting record boundaries.
    bias : ndarray, shape (3,)
        Mean continuous residual for each labeled calibration state.
    observations : list of ndarray
        Separate integer-symbol records, reused by the unsupervised example.

    Raises
    ------
    ValueError
        If a state is never observed and its bias cannot be estimated.

    Notes
    -----
    No evaluation trajectory is consumed. State labels are known because this
    is a synthetic calibration experiment; practical use needs an identified
    calibration procedure rather than access to hidden test labels.
    """
    rng = np.random.default_rng(seed)
    states, observations, residuals = [], [], []
    for _ in range(trajectories):
        z = sample_markov(TRANSITION, PRIOR, length, rng)
        residual = BIAS[z] + rng.normal(0, NOISE_STD, length)
        states.append(z); observations.append(symbols(residual)); residuals.append(residual)
    model = fit_supervised(states, observations, 3, 3, pseudocount=1.)
    all_z, all_r = np.concatenate(states), np.concatenate(residuals)
    if any(not np.any(all_z == state) for state in range(3)):
        raise ValueError('Bias calibration requires observations of every sensor state')
    bias = np.array([all_r[all_z == state].mean() for state in range(3)])
    return model, bias, observations


def classification(truth, predicted):
    """Score three-class state predictions against retrospective labels.

    ``truth`` and ``predicted`` are matching integer arrays with labels in
    ``{0, 1, 2}``. Return accuracy and a 3 by 3 confusion matrix serialized as
    lists, with true states on rows and predicted states on columns. This
    helper does not relabel latent states or select a fit using test labels.
    """
    confusion = np.zeros((3, 3), dtype=int)
    np.add.at(confusion, (truth, predicted), 1)
    return {'accuracy': float(np.mean(truth == predicted)),
            'confusion_true_rows_predicted_columns': confusion.tolist()}


def alarm_metrics(truth, posterior, threshold=.7):
    """Score a fixed posterior threshold for sensor-fault state two.

    Parameters
    ----------
    truth : ndarray, shape (n,)
        Retrospective integer state labels; state two is the fault condition.
    posterior : ndarray, shape (n, 3)
        Filtered or other explicitly identified posterior state probabilities.
    threshold : float, optional
        Alarm when the fault posterior is greater than or equal to this value.

    Returns
    -------
    dict
        Threshold, true/false positive and negative counts, precision, recall
        and false-alarm rate. Any ratio with a zero denominator is ``None``.
        This function scores a supplied threshold rather than tuning it.
    """
    actual, alarm = truth == 2, posterior[:, 2] >= threshold
    tp, fp = int(np.sum(alarm & actual)), int(np.sum(alarm & ~actual))
    fn, tn = int(np.sum(~alarm & actual)), int(np.sum(~alarm & ~actual))
    return {'threshold': threshold, 'true_positive': tp, 'false_positive': fp,
            'false_negative': fn, 'true_negative': tn,
            'precision': tp/(tp+fp) if tp+fp else None,
            'recall': tp/(tp+fn) if tp+fn else None,
            'false_alarm_rate': fp/(fp+tn) if fp+tn else None}


def simulate_sensor_control(model, calibrated_bias, states, noise, tau=10., compensate=False):
    """Strictly causal update; no true labels, smoothing or true c in control law.

    Labels affect only the simulated sensor. A nominal predictor starts at the
    known initial concentration and uses past applied inputs, without correction
    by the faulty measurement. This information advantage is explicit.
    """
    n = len(states)
    t = DT*np.arange(n)
    reference = np.where(t < 10, .35, np.where(t < 75, .65, .45))
    plant, predictor = Tank(10*tau, 10), Tank()
    controller = PID(2., .2, dt=DT, bias=.35)
    output, prediction, measured, control = (np.empty(n) for _ in range(4))
    posterior = np.empty((n, 3))
    output[0] = prediction[0] = .35
    belief = model.initial.copy()
    for k in range(n):
        measured[k] = output[k] + BIAS[states[k]] + noise[k]
        prior = belief if k == 0 else belief @ model.transition
        belief = prior * model.emission[:, int(symbols(measured[k]-prediction[k]))]
        belief /= belief.sum()
        posterior[k] = belief
        feedback = measured[k] - float(belief @ calibrated_bias) if compensate else measured[k]
        control[k] = controller(reference[k], feedback)
        if k+1 < n:
            output[k+1] = plant.step(output[k], control[k], DT)
            prediction[k+1] = predictor.step(prediction[k], control[k], DT)
    return {'t': t, 'reference': reference, 'output': output, 'control': control,
            'measurement': measured, 'prediction': prediction, 'posterior': posterior,
            'metrics': control_metrics(t, reference, output, control)}


def run_markov_experiment():
    """Run the complete fixed-seed sensor-diagnosis teaching experiment.

    Return ``summary``, ``traces`` and ``diagnosis`` dictionaries. Supervised
    calibration uses twenty independent 150-sample records with seed 17;
    the separate evaluation record has 600 samples with seed 2026. Metrics
    compare instantaneous classification, causal filtering, offline smoothing
    and Viterbi, followed by nominal/mismatched ordinary and compensated PI.

    The Baum-Welch illustration starts from known simulator probabilities,
    which is favorable initialization rather than blind identification.
    Hidden evaluation labels neither tune hyperparameters nor relabel the
    unsupervised fit. No files are written and no industrial safety or
    population reliability estimate is claimed.
    """
    model, calibrated_bias, training_obs = calibrate()
    rng = np.random.default_rng(2026)
    states = sample_markov(TRANSITION, PRIOR, 600, rng)
    noise = rng.normal(0, NOISE_STD, len(states))
    residual = BIAS[states] + noise
    obs = symbols(residual)
    filtering, smoothing = model.filter(obs), model.smooth(obs)
    path = model.viterbi(obs)
    instantaneous = stationary_distribution(model.transition)[None, :] * model.emission[:, obs].T
    instantaneous /= instantaneous.sum(axis=1, keepdims=True)
    # Fixed physical ordering is an initialization, not proof of semantic labels.
    em_initial = CategoricalHMM(PRIOR, TRANSITION, theoretical_emission())
    em = baum_welch(training_obs, em_initial, max_iter=30, tol=1e-6)
    hit = hitting_statistics(TRANSITION, [2])
    absorbing = TRANSITION.copy(); absorbing[2] = [0., 0., 1.]
    traces, control_rows = {}, []
    for tau in (10., 14.):
        for compensate in (False, True):
            name = ('HMM compensated PI' if compensate else 'PI') + f', tau={tau:g}'
            trace = simulate_sensor_control(model, calibrated_bias, states, noise, tau, compensate)
            traces[name] = trace
            control_rows.append({'policy': name, 'actual_tau_min': tau,
                                 'predictor_tau_min': 10., **trace['metrics']})
    summary = {
        'scope': 'Synthetic enrichment beyond the supplied syllabus and article; sensor modes, not additional physical benchmark models.',
        'states': STATE_NAMES, 'sample_time_min': DT, 'noise_std': NOISE_STD,
        'bias_true': BIAS.tolist(), 'bias_calibrated': calibrated_bias.tolist(),
        'residual_cutpoints': CUTPOINTS.tolist(), 'true_transition': TRANSITION.tolist(),
        'true_initial': PRIOR.tolist(), 'theoretical_emission': theoretical_emission().tolist(),
        'estimated_transition': model.transition.tolist(), 'estimated_emission': model.emission.tolist(),
        'estimated_initial': model.initial.tolist(),
        'calibration': {'seed': 17, 'independent_trajectories': 20, 'samples_per_trajectory': 150,
                        'label_access': 'Synthetic calibration only; separate sequences preserve boundaries.', 'pseudocount': 1.},
        'test': {'seed': 2026, 'samples': 600, 'hyperparameters': 'Fixed before test; no label-based tuning.'},
        'chain': {'stationary': stationary_distribution(TRANSITION).tolist(),
                  'healthy_after_50_steps': n_step_distribution([1., 0., 0.], TRANSITION, 50).tolist(),
                  'expected_holding_steps': (1/(1-np.diag(TRANSITION))).tolist(),
                  'first_fault_probability': hit['probability'].tolist(),
                  'expected_first_fault_steps': hit['expected_steps'].tolist(),
                  'absorbing_fault_scenario_transition': absorbing.tolist(),
                  'absorbing_fault_note': 'Hypothetical irreversible fault; the original sensor chain permits recovery.'},
        'diagnosis': {'instantaneous_emission_MAP': classification(states, instantaneous.argmax(axis=1)),
                      'online_filter': classification(states, filtering['filtered'].argmax(axis=1)),
                      'offline_smoother': classification(states, smoothing['smoothed'].argmax(axis=1)),
                      'offline_viterbi': classification(states, path['states']),
                      'online_alarm': alarm_metrics(states, filtering['filtered']),
                      'test_log_likelihood_supervised': filtering['log_likelihood']},
        'baum_welch': {'training_log_likelihood': em['log_likelihood_history'].tolist(),
                       'iterations': em['iterations'], 'converged': em['converged'],
                       'test_log_likelihood': em['model'].filter(obs)['log_likelihood'],
                       'semantic_accuracy': None,
                       'note': 'Unsupervised latent labels are permutation invariant. Test labels are not used to relabel or select the fit.'},
        'control': control_rows,
        'limitations': 'One synthetic test seed; conditional independence is exact only for the calibrated residual generator. Predictor mismatch confounds process dynamics and sensor modes. Offline estimates are excluded from control. Results are not safety guarantees.'}
    return {'summary': summary, 'traces': traces,
            'diagnosis': {'states': states, 'observations': obs, 'residual': residual,
                          'filtered': filtering['filtered'], 'smoothed': smoothing['smoothed'],
                          'viterbi': path['states'], 'instantaneous': instantaneous}}


def save_markov_result(result, outdir):
    """Export diagnosis/control records and their figures.

    Parameters
    ----------
    result : dict
        Completed result from `run_markov_experiment`.
    outdir : str or pathlib.Path
        Destination, created with parents when necessary. Matching output
        filenames already present at this location are replaced.

    Returns
    -------
    pathlib.Path
        Directory containing ``metrics.json``, ``diagnosis.csv``, four control
        CSVs, and PNG/SVG diagnosis and comparison figures. The diagnosis
        export labels its retrospective truth/smoothing/Viterbi fields;
        those fields are not additional controller inputs.
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    (outdir/'metrics.json').write_text(json.dumps(result['summary'], indent=2, allow_nan=False)+'\n', encoding='utf-8')
    d = result['diagnosis']; t = DT*np.arange(len(d['states']))
    np.savetxt(outdir/'diagnosis.csv', np.column_stack((t, d['states'], d['observations'], d['residual'],
        d['filtered'], d['smoothed'], d['viterbi'])), delimiter=',', comments='',
        header='time_min,true_state,symbol,residual,filter_normal,filter_drift,filter_fault,smooth_normal,smooth_drift,smooth_fault,viterbi')
    fig, ax = plt.subplots(3, 1, figsize=(12, 9), sharex=True, layout='constrained')
    ax[0].plot(t, d['residual'], lw=.8, label='Noisy sensor residual')
    for threshold in CUTPOINTS: ax[0].axhline(threshold, color='gray', ls='--', lw=.8)
    ax[0].set(ylabel='Residual concentration', title='Independent sensor diagnosis | synthetic test, seed 2026'); ax[0].legend()
    ax[1].step(t, d['states'], where='post', label='True state', lw=2, color='black')
    ax[1].step(t, d['filtered'].argmax(axis=1), where='post', label='Online filter MAP', alpha=.75)
    ax[1].step(t, d['viterbi'], where='post', label='Offline Viterbi', alpha=.65)
    ax[1].set(yticks=[0, 1, 2], yticklabels=STATE_NAMES, ylabel='Mode'); ax[1].legend(ncol=3, fontsize=9)
    ax[2].plot(t, d['filtered'][:, 2], label='Online fault probability')
    ax[2].plot(t, d['smoothed'][:, 2], label='Offline smoothed probability', alpha=.75)
    ax[2].axhline(.7, color='gray', ls='--', label='Fixed alarm threshold')
    ax[2].set(ylabel='Probability', xlabel='Time [min]', ylim=(-.02, 1.02)); ax[2].legend(ncol=3, fontsize=9)
    for a in ax: a.grid(alpha=.2)
    fig.savefig(outdir/'diagnosis.png', dpi=160); fig.savefig(outdir/'diagnosis.svg'); plt.close(fig)
    fig, axes = plt.subplots(2, 2, figsize=(13, 7), sharex='col', layout='constrained')
    for col, tau in enumerate((10, 14)):
        for name, trace in result['traces'].items():
            if not name.endswith(f'tau={tau}'): continue
            axes[0, col].plot(trace['t'], trace['output'], label=name.split(',')[0])
            axes[1, col].plot(trace['t'], trace['control'], label=name.split(',')[0])
            np.savetxt(outdir/(name.replace(' ', '_').replace(',', '').replace('=', '-')+'.csv'),
                np.column_stack((trace['t'], trace['reference'], trace['output'], trace['control'],
                                 trace['measurement'], trace['prediction'], trace['posterior'])),
                delimiter=',', comments='', header='time,reference,output,control,measurement,nominal_prediction,p_normal,p_drift,p_fault')
        axes[0, col].plot(t, trace['reference'], '--', color='black', label='Reference')
        axes[0, col].set(title=f'Actual residence time {tau} min | predictor 10 min', ylabel='True concentration')
        axes[1, col].set(xlabel='Time [min]', ylabel='Applied inlet fraction')
        axes[0, col].legend(fontsize=9)
    for a in axes.ravel(): a.grid(alpha=.2)
    fig.suptitle('Unit 09 | Causal HMM sensor compensation with matched noise')
    fig.savefig(outdir/'comparison.png', dpi=160); fig.savefig(outdir/'comparison.svg'); plt.close(fig)
    return outdir

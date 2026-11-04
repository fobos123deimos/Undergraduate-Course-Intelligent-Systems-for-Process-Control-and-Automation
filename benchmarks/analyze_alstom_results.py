"""Independently check native ALSTOM CSVs and summarize the official PI baseline.

This command reads completed simulator results; it does not execute the MEX.
"""
from pathlib import Path
import argparse
import hashlib
import json

import numpy as np


OUTPUTS = ['CV_J_kg', 'bed_mass_kg', 'pressure_Pa', 'temperature_K']
SETPOINTS = ['CV_setpoint_J_kg', 'bed_mass_setpoint_kg', 'pressure_setpoint_Pa', 'temperature_setpoint_K']
INPUTS = ['char_kg_s', 'air_kg_s', 'coal_kg_s', 'steam_kg_s']
LIMITS = np.array([10000., 500., 10000., 1.])
UPPER = np.array([3.5, 20., 10., 6.])
SLEW = np.array([.2, 1., .2, 1.])


def columns(data, names):
    return np.column_stack([data[name] for name in names])


def analyze(folder):
    folder = Path(folder)
    native_path = folder / 'validation.json'
    native = json.loads(native_path.read_text(encoding='utf-8'))
    assert native['status'] == 'integration_and_input_checks_passed'
    assert native['case_count'] == len(native['cases']) == 11
    expected = {(load, scenario) for load in (0, 50, 100)
                for scenario in ('nominal', 'pressure_step', 'pressure_sine')}
    expected |= {(50, 'load_ramp'), (100, 'coal_quality')}
    assert {(c['initial_load_percent'], c['scenario']) for c in native['cases']} == expected
    records, traces = [], {}
    sensitivity = native.get('solver_sensitivity', [])
    if sensitivity:
        assert {c['solver_profile'] for c in sensitivity} == {'refined', 'author_default'}
        assert native['solver_refinement_check_passed'] is True
    for case in native['cases'] + sensitivity:
        scenario, load = case['scenario'], case['initial_load_percent']
        name = scenario if scenario in ('load_ramp', 'coal_quality') else f'load{load:03d}-{scenario}'
        profile = case.get('solver_profile', 'strict')
        if profile != 'strict':
            name += '-' + profile
        path = folder / (name + '.csv')
        data = np.genfromtxt(path, delimiter=',', names=True)
        t = data['time_s']
        y, sp = columns(data, OUTPUTS), columns(data, SETPOINTS)
        u = columns(data, INPUTS)
        command = columns(data, ['command_' + key for key in INPUTS])
        assert len(t) == case['sample_count'] and len(t) > 2
        assert all(np.isfinite(data[key]).all() for key in data.dtype.names)
        assert np.all(np.diff(t) >= 0) and t[0] == 0
        assert abs(t[-1] - case['duration_s']) < 1e-7
        pressure = np.zeros_like(t)
        if scenario == 'pressure_step':
            pressure = -20000 * (t >= 30)
        elif scenario == 'pressure_sine':
            pressure = 20000 * np.sin(2 * np.pi * .04 * t)
        coal = (8 if scenario == 'coal_quality' else 0) * np.clip((t - 10) / 10, 0, 1)
        demand = load + (50 if scenario == 'load_ramp' else 0) * np.clip((t - 100) / 600, 0, 1)
        np.testing.assert_allclose(data['psink_disturbance_Pa'], pressure, rtol=0, atol=1e-6)
        np.testing.assert_allclose(data['coal_quality_percent'], coal, rtol=0, atol=1e-8)
        np.testing.assert_allclose(data['load_demand_percent'], demand, rtol=0, atol=1e-8)
        np.testing.assert_allclose(data['command_limestone_kg_s'], .1 * command[:, 2], rtol=0, atol=1e-8)
        error = y - sp
        maximum = np.max(np.abs(error), axis=0)
        integral = np.trapezoid(np.abs(error), t, axis=0)
        dt = np.diff(t)
        moving = dt > 1e-10
        observed = {
            'maximum_absolute_error': maximum,
            'integrated_absolute_error': integral,
            'maximum_input_limit_violation': np.maximum(0, np.maximum(np.max(u - UPPER, axis=0), np.max(-u, axis=0))),
            'maximum_input_rate_violation': np.maximum(0, np.max(np.abs(np.diff(u, axis=0)[moving]) / dt[moving, None], axis=0) - SLEW),
            'maximum_command_limit_violation': np.maximum(0, np.maximum(np.max(command - UPPER, axis=0), np.max(-command, axis=0))),
            'maximum_command_rate_violation': np.maximum(0, np.max(np.abs(np.diff(command, axis=0)[moving]) / dt[moving, None], axis=0) - SLEW),
        }
        for key, actual in observed.items():
            np.testing.assert_allclose(actual, case[key], rtol=2e-8, atol=2e-6, err_msg=name + ': ' + key)
        records.append({'case': name, 'csv_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'samples': len(t), 'duration_s': float(t[-1]),
                        'pressure_test': scenario.startswith('pressure_'),
                        'maximum_error_relative_to_pressure_limits': (maximum / LIMITS).tolist(),
                        'applied_limestone_ratio_error_kg_s': float(np.max(np.abs(data['limestone_kg_s'] - .1 * u[:, 2]))),
                        **{key: value.tolist() for key, value in observed.items()}})
        traces[(load, scenario if profile == 'strict' else profile)] = (data, error)
    sensitivity_results = []
    for case in sensitivity:
        profile = case['solver_profile']
        baseline = traces[(50, 'nominal')][0]
        candidate = traces[(50, profile)][0]
        grid = np.arange(301.)
        # Match the native comparison's first value at duplicate event times.
        t0, i0 = np.unique(baseline['time_s'], return_index=True)
        t1, i1 = np.unique(candidate['time_s'], return_index=True)
        diff = np.column_stack([np.interp(grid, t1, candidate[key][i1]) - np.interp(grid, t0, baseline[key][i0]) for key in OUTPUTS])
        maximum = np.max(np.abs(diff) / LIMITS, axis=0)
        np.testing.assert_allclose(maximum, case['maximum_output_difference_scaled_to_pressure_limits'], rtol=2e-6, atol=1e-7)
        if profile == 'refined': assert np.max(maximum) < .05
        sensitivity_results.append({'profile': profile, 'maximum_scaled_difference': maximum.tolist(),
                                    'final_temperature_error_K': float(candidate['temperature_K'][-1] - candidate['temperature_setpoint_K'][-1])})
    report = {'status': 'independent_csv_checks_passed', 'case_count': 11,
              'csv_count': len(records), 'total_samples': sum(c['samples'] for c in records),
              'native_report_sha256': hashlib.sha256(native_path.read_bytes()).hexdigest(),
              'cases': records, 'solver_sensitivity_count': len(sensitivity),
              'solver_sensitivity': sensitivity_results,
              'scope': 'Recomputed native PI metrics, channel identities, disturbance shapes and source-result integrity; no claim that all control constraints are satisfied.'}
    (folder / 'analysis.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report, traces


def figures(folder, traces):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    labels = ['Calorific value', 'Bed mass', 'Pressure', 'Temperature']
    fig, axes = plt.subplots(3, 2, figsize=(12, 9), sharex=True, constrained_layout=True)
    for row, load in enumerate((0, 50, 100)):
        for col, scenario in enumerate(('pressure_step', 'pressure_sine')):
            data, error = traces[(load, scenario)]
            ax = axes[row, col]
            for j, label in enumerate(labels):
                ax.plot(data['time_s'], error[:, j] / LIMITS[j], label=label, linewidth=1.1)
            ax.axhline(1, color='black', linestyle='--', linewidth=.7)
            ax.axhline(-1, color='black', linestyle='--', linewidth=.7)
            ax.set_title(f'{load}% load: ' + scenario.replace('_', ' '))
            ax.set_ylabel('Output error / permitted magnitude')
            ax.grid(alpha=.2)
    axes[-1, 0].set_xlabel('Time [s]'); axes[-1, 1].set_xlabel('Time [s]')
    axes[0, 0].legend(ncol=2, fontsize=8)
    fig.suptitle('Official ALSTOM PI baseline — pressure disturbance tests\nDashed lines are challenge limits; excursions are retained')
    fig.savefig(Path(folder) / 'pressure-tests.png', dpi=140); plt.close(fig)
    fig, axes = plt.subplots(2, 2, figsize=(12, 7), constrained_layout=True)
    for col, (load, scenario) in enumerate(((50, 'load_ramp'), (100, 'coal_quality'))):
        data, error = traces[(load, scenario)]
        axes[0, col].plot(data['time_s'], data['load_actual_percent'], label='Actual load')
        axes[0, col].plot(data['time_s'], data['load_demand_percent'], '--', label='Demand')
        axes[0, col].set_title(scenario.replace('_', ' ').title())
        axes[0, col].set_ylabel('Load [%]'); axes[0, col].legend()
        for j, label in enumerate(labels):
            axes[1, col].plot(data['time_s'], error[:, j] / LIMITS[j], label=label)
        axes[1, col].set_ylabel('Error / pressure-test reference scale')
        axes[1, col].set_xlabel('Time [s]')
        for row in range(2): axes[row, col].grid(alpha=.2)
    axes[1, 0].legend(ncol=2, fontsize=8)
    fig.suptitle('Official ALSTOM PI baseline — load and +8% coal-quality changes\nPressure-test scales aid comparison; their limits do not apply to these two cases')
    fig.savefig(Path(folder) / 'operating-changes.png', dpi=140); plt.close(fig)
    if (50, 'refined') in traces:
        fig, ax = plt.subplots(figsize=(9, 4), constrained_layout=True)
        for profile, label in [('nominal', 'Strict'), ('refined', 'Refined'), ('author_default', 'Author solver settings')]:
            data, error = traces[(50, profile)]
            ax.plot(data['time_s'], error[:, 3], label=label)
        ax.set(xlabel='Time [s]', ylabel='Temperature error [K]', title='Official 50% nominal case — solver sensitivity')
        ax.grid(alpha=.2); ax.legend()
        fig.savefig(Path(folder) / 'solver-check.png', dpi=140); plt.close(fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', type=Path, default=Path(__file__).resolve().parent / 'results/alstom-native')
    args = parser.parse_args()
    report, traces = analyze(args.results)
    figures(args.results, traces)
    print(f"ALSTOM: {report['case_count']} challenge cases and {report['solver_sensitivity_count']} solver checks passed; metrics and figures saved.")

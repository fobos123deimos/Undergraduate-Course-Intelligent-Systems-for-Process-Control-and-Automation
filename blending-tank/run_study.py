"""Execute the physical tank study from its declared conservation equations."""
from pathlib import Path
import json
import sys
import numpy as np
from scipy.integrate import quad
from scipy.linalg import expm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'python'))
from intelligent_control.physical_blending import (
    DEFAULT_RHO, DEFAULT_INPUT, DEFAULT_STATE, simulate, linearize,
    constant_input_solution, transfer_functions)


def json_ready(value):
    if isinstance(value, np.ndarray): return value.tolist()
    if isinstance(value, np.generic): return value.item()
    if isinstance(value, dict): return {key: json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)): return [json_ready(item) for item in value]
    return value


def linear_response(t, initial_state, interval_inputs, model):
    """Exact zero-order-hold propagation of DEVIATIONS, then restore offsets."""
    augmented = np.zeros((7, 7))
    augmented[:2, :2], augmented[:2, 2:] = model['A'], model['B']
    deviation = np.asarray(initial_state, float)-model['x_eq']
    states = np.empty((len(t), 2)); states[0] = initial_state
    cache = {}
    for k, step in enumerate(np.diff(t)):
        key = round(float(step), 12)
        if key not in cache: cache[key] = expm(augmented*step)
        transition = cache[key]
        deviation = (transition[:2, :2] @ deviation
                     + transition[:2, 2:] @ (interval_inputs[k]-model['u_eq']))
        states[k+1] = model['x_eq']+deviation
    return states


def run_study(output_dir=None):
    t = np.linspace(0., 30., 601)
    model = linearize()
    cases, summaries = {}, {}
    for name, outlet in [('balanced_startup', 700.), ('filling_outlet_650', 650.)]:
        u = DEFAULT_INPUT.copy(); u[4] = outlet
        initial = np.array([0., 2.])
        trace = simulate(initial, t, u)
        analytical = constant_input_solution(t, initial, u)
        solute_input = u[0]*u[2]+u[1]*u[3]
        net_solute, _ = quad(lambda time: solute_input-u[4]*constant_input_solution(
            time, initial, u)[0], t[0], t[-1], epsabs=1e-9, epsrel=1e-10)
        final = trace['state'][-1]
        mass_residual = DEFAULT_RHO*(final[0]*final[1]-initial[0]*initial[1])-net_solute
        cases[name] = {'state': trace['state'], 'reference': analytical,
                       'inputs': np.tile(u, (len(t)-1, 1)), 'comparison': 'Analytical balance'}
        summaries[name] = {
            'initial_state': initial.tolist(), 'constant_input': u.tolist(),
            'final_state': final.tolist(),
            'max_concentration_error_vs_closed_form': float(np.max(abs(trace['state'][:, 0]-analytical[:, 0]))),
            'max_volume_error_vs_closed_form_m3': float(np.max(abs(trace['state'][:, 1]-analytical[:, 1]))),
            'solute_balance_final_residual_kg': float(mass_residual)}
    u = np.tile(DEFAULT_INPUT, (len(t)-1, 1))
    u[t[:-1] >= 5., 0] += 10.
    nonlinear = simulate(DEFAULT_STATE, t, u)['state']
    linear = linear_response(t, DEFAULT_STATE, u, model)
    cases['local_flow_step'] = {'state': nonlinear, 'reference': linear,
                               'inputs': u, 'comparison': 'Linear deviation model'}
    summaries['local_flow_step'] = {
        'initial_state': DEFAULT_STATE.tolist(), 'step_time_min': 5., 'w1_step_kg_per_min': 10.,
        'max_concentration_linearization_error': float(np.max(abs(nonlinear[:, 0]-linear[:, 0]))),
        'max_volume_linearization_error_m3': float(np.max(abs(nonlinear[:, 1]-linear[:, 1]))),
        'final_nonlinear_state': nonlinear[-1].tolist(), 'final_linear_state': linear[-1].tolist()}
    summary = {
        'scope': 'Physical implementation based on conservation laws and explicitly declared parameters.',
        'units': {'time': 'min', 'volume': 'm3', 'mass_flow': 'kg/min', 'density': 'kg/m3', 'mass_fraction': 'dimensionless'},
        'state_order': ['X', 'V'], 'input_order': ['w1', 'w2', 'x1', 'x2', 'wout'],
        'density_kg_per_m3': DEFAULT_RHO,
        'density_provenance': 'Explicit study assumption.',
        'model': json_ready(model), 'transfer_functions': json_ready(transfer_functions()),
        'scenarios': summaries,
        'limits': 'Ideal mixing and constant density. Equilibrium linear models are local and use deviations. The 650 kg/min outlet case fills the tank and has no constant-volume equilibrium. No vessel-capacity model or physical-plant validation is implied.'}
    result = {'t': t, 'cases': cases, 'summary': summary}
    if output_dir is not None: save_results(result, output_dir)
    return result


def save_results(result, output_dir):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir/'metrics.json').write_text(json.dumps(result['summary'], indent=2, allow_nan=False)+'\n', encoding='utf-8')
    fig, axes = plt.subplots(2, 3, figsize=(16, 7), sharex='col', layout='constrained')
    titles = ['Balanced startup | outlet 700 kg/min', 'Filling | outlet 650 kg/min', 'Local flow step | +10 kg/min at 5 min']
    for col, ((name, case), title) in enumerate(zip(result['cases'].items(), titles)):
        t, state, reference = result['t'], case['state'], case['reference']
        for row, ylabel in [(0, 'Solute mass fraction'), (1, 'Volume [m³]')]:
            axes[row, col].plot(t, state[:, row], lw=2, label='Nonlinear mass balance')
            axes[row, col].plot(t, reference[:, row], '--', lw=1.2, label=case['comparison'])
            axes[row, col].set(ylabel=ylabel)
            axes[row, col].grid(alpha=.2)
        axes[0, col].set_title(title, fontsize=11)
        axes[0, col].legend(fontsize=8)
        axes[1, col].set_xlabel('Time [min]')
        inputs = np.vstack((case['inputs'], case['inputs'][-1]))
        np.savetxt(output_dir/(name+'.csv'), np.column_stack((t, state, reference, inputs)),
                   delimiter=',', comments='',
                   header='time_min,X_nonlinear,V_nonlinear,X_reference,V_reference,w1,w2,x1,x2,wout')
    fig.suptitle('Corrected physical Blending Tank | density 1000 kg/m³', fontsize=14)
    fig.savefig(output_dir/'comparison.png', dpi=160)
    fig.savefig(output_dir/'comparison.svg')
    plt.close(fig)


if __name__ == '__main__':
    result = run_study(Path(__file__).resolve().parent/'results')
    print(json.dumps(result['summary']['scenarios'], indent=2))

# Corrected tank validation

The physical tank implementation is checked against conservation laws, analytical solutions and independently calculated linear models. The following record identifies the executed checks and their limits.

## Executed Python checks

All **115 repository tests passed locally**, including **31 dedicated corrected-tank tests**. The corrected notebook executed all six code cells with a fresh Jupyter kernel and saved its outputs without error cells. The three study scenarios ran with the current source; their CSV traces, metrics and comparison figure are stored in [results](results/metrics.json). The comparison figure was visually inspected.

The constant-volume startup matched its analytical concentration to a maximum absolute difference of approximately `3.32e-14`; the filling case differed by approximately `2.90e-14`. Final solute-balance residual magnitudes were below `1.4e-12 kg`. These are floating-point consistency checks against the declared ideal equations, not measurement precision or physical validation.

The 10 kg/min inlet perturbation produced a maximum nonlinear-versus-linear concentration difference of approximately `2.12e-5`. Independent tests halve perturbation amplitudes and check the expected second-order error trend. Volume follows the exact integrated flow imbalance in both representations. Finite-difference Jacobians, all transfer channels, nonequilibrium affine offsets and invalid/emptying configurations are checked separately.

## Native runtime status

The published [validation run 41866227718](https://github.com/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/actions/runs/41866227718) passed on source commit `7fcb51d9904748f998b459593f1730946ee39d24`. Python reran all **115 tests**, the corrected physical-tank study and all **eleven notebooks** successfully. **GNU Octave 11.1.0** executed and passed the **seven independent corrected-tank check groups**, alongside the nine course laboratories, Markov/HMM checks and ten mathematical benchmark checks. No source correction was needed after this run. See the [machine-readable record](validation.json).

## Scope

Python and MATLAB/Octave implement the same equations, state/input order and explicitly stated parameters. Numerical checks compare them with analytical balances and independent Jacobian/transfer calculations. The nonlinear, linear and transfer-function models are separate representations of the declared physical model.

MATLAB with Simulink is not available in the current local runtime. The fresh diagram builder and its simulation-comparison script can be inspected and run in that environment, but a generated or executed corrected `.slx` is not claimed here.

## Reproduction

```bash
python blending-tank/run_study.py
python -m pytest tests/test_physical_blending.py -q
```

```matlab
addpath('matlab');
validate_blending_tank;
addpath('simulink');
build_blending_tank;
validate_blending_simulink;
```

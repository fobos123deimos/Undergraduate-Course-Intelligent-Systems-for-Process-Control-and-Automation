# Corrected tank validation

The corrected implementation is independent of the archived project. The historical files are preserved and are not numerical dependencies. On 4 November 2026, all six archived members matched their original SHA-256 checksums byte for byte.

## Executed Python checks

All **115 repository tests passed locally**, including **31 dedicated corrected-tank tests**. The corrected notebook executed all six code cells with a fresh Jupyter kernel and saved its outputs without error cells. The three study scenarios ran with the current source; their CSV traces, metrics and comparison figure are stored in [results](results/metrics.json). The comparison figure was visually inspected.

The constant-volume startup matched its analytical concentration to a maximum absolute difference of approximately `3.32e-14`; the filling case differed by approximately `2.90e-14`. Final solute-balance residual magnitudes were below `1.4e-12 kg`. These are floating-point consistency checks against the declared ideal equations, not measurement precision or physical validation.

The 10 kg/min inlet perturbation produced a maximum nonlinear-versus-linear concentration difference of approximately `2.12e-5`. Independent tests halve perturbation amplitudes and check the expected second-order error trend. Volume follows the exact integrated flow imbalance in both representations. Finite-difference Jacobians, all transfer channels, nonequilibrium affine offsets and invalid/emptying configurations are checked separately.

## Native runtime status

The new MATLAB/Octave validation contains seven independent check groups and is included in `validate_all`. Its published execution will be recorded after the validation workflow finishes. Local Python success is not presented as a native MATLAB/Octave execution.

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

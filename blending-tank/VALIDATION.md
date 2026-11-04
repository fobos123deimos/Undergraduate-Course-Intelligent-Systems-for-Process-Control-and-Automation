# Corrected tank validation

The physical tank implementation is checked against conservation laws, analytical solutions and independently calculated linear models. The following record identifies the executed checks and their limits.

## Executed Python checks

All **131 repository tests passed locally**, including **31 dedicated corrected-tank tests**. The corrected notebook executed all six code cells with a fresh Jupyter kernel and saved its outputs without error cells. The three study scenarios ran with the current source; their CSV traces, metrics and comparison figure are stored in [results](results/metrics.json). The comparison figure was visually inspected.

The constant-volume startup matched its analytical concentration to a maximum absolute difference of approximately `3.32e-14`; the filling case differed by approximately `2.90e-14`. Final solute-balance residual magnitudes were below `1.4e-12 kg`. These are floating-point consistency checks against the declared ideal equations, not measurement precision or physical validation.

The 10 kg/min inlet perturbation produced a maximum nonlinear-versus-linear concentration difference of approximately `2.12e-5`. Independent tests halve perturbation amplitudes and check the expected second-order error trend. Volume follows the exact integrated flow imbalance in both representations. Finite-difference Jacobians, all transfer channels, nonequilibrium affine offsets and invalid/emptying configurations are checked separately.

## Native runtime status

The final [validation run 41886384567](https://github.com/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/actions/runs/41886384567) passed on source commit `831e66f9e56ef5fba7ea0bcfb98af376a0de054e`. Python reran all **131 tests** and **eleven notebooks**. GNU Octave and native MATLAB passed the seven physical-tank check groups. MATLAB R2025b with Simulink also executed the two physical-tank diagrams and passed startup, filling, perturbed nonlinear, state-space/transfer and zero-volume rejection checks. See the [machine-readable record](validation.json) and [generated model gallery](../simulink/models/README.md).

Simulink's maximum startup error was approximately 9.99e-16; filling error was 6.75e-14; state-space/transfer disagreement was 8.44e-15. The nonlinear/local-linear difference was approximately 2.12e-5. These values describe numerical consistency under the declared assumptions.

## Scope

Python and MATLAB/Octave implement the same equations, state/input order and explicitly stated parameters. Numerical checks compare them with analytical balances and independent Jacobian/transfer calculations. The nonlinear, linear and transfer-function models are separate representations of the declared physical model.

The generated `.slx` files and PNG views are preserved from the successful native MATLAB/Simulink run. They require the complete repository and the MATLAB/Simulink source folders on the path. No measured-plant validation or compatibility with every MATLAB release is claimed.

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

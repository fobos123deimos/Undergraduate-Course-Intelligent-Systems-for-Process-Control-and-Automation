# Nonlinear benchmark laboratory

This track works through every benchmark section in Andreas Kroll and Horst Schulte, *Benchmark problems for nonlinear system identification and control using Soft Computing methods: Need and overview*, Applied Soft Computing 25 (2014), 496–513, [doi:10.1016/j.asoc.2014.08.034](https://doi.org/10.1016/j.asoc.2014.08.034). It distinguishes equations available in the paper, added modeling assumptions, and external industrial simulators. Reading a case and running a component check are different from reproducing the published benchmark.

## Start here

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/blob/main/benchmarks/notebook.ipynb)

[Browse eleven original equipment diagrams](DIAGRAMS.md), with editable SVG sources and the state/input conventions used by the code.

From the repository root, after installing the requirements:

```bash
python benchmarks/run_benchmarks.py
python -m pytest tests/test_benchmarks.py -q
python benchmarks/fetch_external.py --list
```

The first command produces deterministic short simulations, balance checks and a provenance report in `benchmarks/results/`. Its external-model entries separately inspect preserved OpenFAST, Tennessee Eastman and ALSTOM evidence, with file paths and hashes; **this command does not rerun those external simulators**. OpenFAST and three native TE cases have executed successfully. The ALSTOM archive and initial conditions have been verified, while its native Windows MATLAB/Simulink execution remains pending. Original throttle measurements are still absent. The [notebook](notebook.ipynb) explains the same calculations. [Case studies and worked questions](CASE_STUDIES.md) cover model selection, identification and control for every section.

## Coverage and exact scope

| Paper section | Process or resource | Implementation | Reproduction boundary |
|---|---|---|---|
| 3.1, Eq. 30 | Artificial SISO, Narendra–Parthasarathy example 2 | `siso_step`, `artificial_data` | Exact recurrence; initial zero history and RNG seed explicitly chosen here |
| 3.1, Eq. 31 | Artificial 2-input/2-output example 4 | `mimo_step`, `artificial_data` | Exact recurrence; two examples are actually specified in the review, not all five examples of its reference [60] |
| 3.2 | DaISy, IFAC, NIST, MATLAB, UCI, DELVE, WEKA repositories | `load_io_csv`; [dataset register](DATASETS.md) | Metadata and import workflow; no claim that all historical third-party datasets are bundled |
| 3.3, Eq. 32 | Cart with inverted pendulum | `pendulum_rhs` | Table 3 parameters; force clipping; no rail impacts or static sticking model |
| 3.4 and 4.1 | Electromechanical throttle; PWA/TS predictors | `LocalARX`; [bound-data evaluation](run_throttle_reference.py) in Python and MATLAB | Exact historical archive URL recovered; measured records and original fitted partitions remain unavailable |
| 3.5, Eqs. 33–34 | Servo-pneumatic actuator | Literal balances plus [separate physical variant](PNEUMATIC_AUDIT.md) in Python/MATLAB/Simulink | Primary source resolves gravity offsets; complete mass/energy and choked-flow variant uses explicitly uncalibrated valve parameters |
| 3.6, Eq. 35 | Hydrostatic transmission | Literal transcription plus [separate SI variant](HYDROSTATIC_SOURCE_REVIEW.md) in Python/MATLAB/Simulink | Primary sources explain bar/mm³ conversions and motor torque; historical displacement/capacitance conventions and electrical gains remain unresolved |
| 3.7, Eq. 36 | Three-tank system | `three_tank_rhs` | Nominal drains closed; optional drain faults explicitly added |
| 3.8, Eqs. 37–38 | Biochemical reactor | `bioreactor_rhs`, `bioreactor_sample` | 50 Euler substeps per 0.5-unit sensor/control period |
| 3.9, Eqs. 39–46 | Klatt–Engell CSTR | `cstr_rhs`, `CSTR_SP1`, `CSTR_SP2` | Celsius convention and MJ→kJ conversion made explicit; full-state simulations do not solve the original observer task |
| 3.10, Eqs. 47–54 | 4×4 distillation Column A, 82 states | `column_a_rhs` | All stages, feed, condenser and reboiler implemented; NTNU precision for nominal reflux/boilup |
| 3.10 | 2×2 Column A with LV structure | `column_a_lv_rhs` | D/B level loops added with stated P gain; other named configurations are design extensions |
| 3.11 | ALSTOM nonlinear gasifier II and PI baseline | [Native 11-case runner](validate_alstom_reference.m); [source inspection](results/alstom-source-inspection.json) | Author archive recovered and checked; native execution needs compatible Windows MATLAB/Simulink and the supplied MEX; no trajectory or performance score claimed |
| 3.12, Eqs. 55–58 | Control-oriented wind turbine | `wind_rhs`, `wind_matrices`, `RotorMap` | Full 9-state reduced model; bundled 2022 ROSCO map is a documented later-map variant |
| 3.12 | High-order FAST/NREL 5 MW turbine | [Pinned OpenFAST runner](run_openfast_reference.py); [external guide](EXTERNAL_MODELS.md) | Official v5.0.0 60-second turbulent case executed and compared with its release baseline; successor configuration, not the 2014 experiment |
| 3.13 | Tennessee Eastman original and revised simulator | [Native runner](validate_te_reference.m); [executed evidence](results/te-native/validation.json) | Revised 52-state C source compiled in R2025b; mode1 nominal, IDV1 and IDV4 passed at 0.2 h each; other modes/full protocols remain open; original 50-state version kept distinct |
| 4.2 | Wind TS/PDC controller example | [Executable LQR/PDC study](WIND_CONTROL.md) in Python, MATLAB/Octave and Simulink | New scaled local LQR gains, interpolated nonlinear runs, constraints and two explicit plant variants; original Table 12 gains/results not claimed |

The survey kernels live in [benchmarks.py](../python/intelligent_control/benchmarks.py). The new physical variants have separate modules and source reviews, preserving the distinction between transcription and a dimensionally reconstructed model. Model equations are evaluated without clipping states to hide integration failure. Physical domain checks stop inappropriate experiments. Integrator and step size must suit the process; the stiff CSTR/column and discontinuous-friction systems need convergence checks.

## Source audit and corrections

1. **Three tanks:** Table 6 prints cubic metres for cross-sectional areas. Areas are implemented in square metres. Eq. (36) closes all nominal outlet valves. Consequently the total stored volume satisfies `dV/dt=q1+q2`; sustained positive pumping cannot have an equilibrium. A drain must be declared as an extension before doing steady-state tracking.
2. **CSTR:** Table 7 labels temperatures K, although Eq. (41) adds 273.15. Values 87, 106 and 104.9 are therefore treated as degrees Celsius. Cooling is supplied in MJ/h and converted to kJ/h in the coolant equation. The printed steady states are rounded; small derivative residuals are expected. Concentrations are mol/m³, not mol/L.
3. **Column:** Eq. (47) prints `V[i+1]`; its component balance and the original [NTNU model description](https://skoge.folk.ntnu.no/book/matlab_m/cola/cola.html) use the incoming vapor `V[i-1]`. The implementation follows this conservative balance. NTNU's model uses L0=2.70629 and V0=3.20629; Table 9 rounds these. In LV configuration D and B hold the end-vessel levels, leaving L and V for composition control, as shown in the paper's Fig. 9 and the primary implementation.
4. **Pneumatics:** Table 4 labels the molar constant 8.314 as mass specific. The [primary-source audit](PNEUMATIC_AUDIT.md) derives the specific constant from molar mass and identifies the gravity/Coulomb offsets removed during the original local identification. The literal core remains unchanged. A separate six-state variant includes absolute pressures, vertical gravity, variable chamber temperatures, mass/energy conservation and reversible choked flow. Valve geometry, discharge, thermal and friction-smoothing choices remain explicit assumptions; no apparatus calibration is claimed.
5. **Hydrostatic drive:** the [2006/2008/2011 primary sources](HYDROSTATIC_SOURCE_REVIEW.md) explain the bar/mm³ conversion factors and derive motor torque from motor displacement. The combined printed equations contain a conflicting pump-volume symbol; no official erratum was recovered. `hydrostatic_rhs` remains **transcription only**. The separate SI variant requires explicit displacement and capacitance conventions, uses requested normalized angles rather than unverified electrical gains, and exposes the motoring limitation of constant efficiencies. Balance and cross-language checks validate that declared interpretation, not historical calibration.
6. **Bioreactor:** for Γ=0.4, β=0.02 and u=0.769, Eqs. (37) yield the nonwashout equilibrium C₂≈0.9235897741, C₁≈0.0872975478. The prose instead reports C₁=0.1236837. Substituting that biomass with the equilibrium substrate leaves dC₂≈0.29603. The notebook verifies this discrepancy; it does not force the inconsistent prose number into the dynamics.
7. **Metric names:** in this article “MAE” in Eq. (1) is the **maximum** absolute error, not today's common mean absolute error. Report `max_abs_error` explicitly. VAF uses the variance of residuals and can ignore constant bias; it is not generally identical to R².

## Reporting a comparison

Report source version/hash, state/input units, initialization, solver tolerances, sample and hold periods, seeds, disturbances, actuator and state constraints. Split identification trajectories before normalization or feature fitting. Record one-step predictions with measured history separately from free-run predictions with predicted history. Report per-output RMSE, maximum absolute error, R²/VAF where defined, model size, and elapsed time. For control report tracking IAE/RMSE, settling specification, input energy and movement, and all constraint violations. A short synthetic experiment does not demonstrate global stability or industrial safety.

The [external source guide](EXTERNAL_MODELS.md) records what has actually been retrieved and what remains necessary for canonical comparisons.

The [coverage review](../docs/COVERAGE_REVIEW.md) separates the thirteen documented benchmark sections, ten implemented mathematical cores, optional variants and experiments that still require data, source clarification or an external runtime.

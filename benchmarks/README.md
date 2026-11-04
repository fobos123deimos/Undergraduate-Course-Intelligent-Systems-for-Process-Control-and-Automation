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

The first command produces deterministic short simulations, balance checks and a provenance report in `benchmarks/results/`. It does not manufacture throttle measurements or scores for an unavailable gasifier, FAST or Tennessee Eastman simulator. The [notebook](notebook.ipynb) explains the same calculations. [Case studies and worked questions](CASE_STUDIES.md) cover model selection, identification and control for every section.

## Coverage and exact scope

| Paper section | Process or resource | Implementation | Reproduction boundary |
|---|---|---|---|
| 3.1, Eq. 30 | Artificial SISO, Narendra–Parthasarathy example 2 | `siso_step`, `artificial_data` | Exact recurrence; initial zero history and RNG seed explicitly chosen here |
| 3.1, Eq. 31 | Artificial 2-input/2-output example 4 | `mimo_step`, `artificial_data` | Exact recurrence; two examples are actually specified in the review, not all five examples of its reference [60] |
| 3.2 | DaISy, IFAC, NIST, MATLAB, UCI, DELVE, WEKA repositories | `load_io_csv`; [dataset register](DATASETS.md) | Metadata and import workflow; no claim that all historical third-party datasets are bundled |
| 3.3, Eq. 32 | Cart with inverted pendulum | `pendulum_rhs` | Table 3 parameters; force clipping; no rail impacts or static sticking model |
| 3.4 and 4.1 | Electromechanical throttle; PWA/TS predictors | `LocalARX`, CSV import | Predictors runnable; official measured training/test records must be supplied |
| 3.5, Eqs. 33–34 | Servo-pneumatic actuator | `pneumatic_rhs`; `educational_valve_flows` | Balance equations exact; valve mass-flow closure is missing in paper; practice closure labeled separately |
| 3.6, Eq. 35 | Hydrostatic transmission | `hydrostatic_rhs` | Literal transcription only; published scalings need reconciliation before SI/vehicle claims |
| 3.7, Eq. 36 | Three-tank system | `three_tank_rhs` | Nominal drains closed; optional drain faults explicitly added |
| 3.8, Eqs. 37–38 | Biochemical reactor | `bioreactor_rhs`, `bioreactor_sample` | 50 Euler substeps per 0.5-unit sensor/control period |
| 3.9, Eqs. 39–46 | Klatt–Engell CSTR | `cstr_rhs`, `CSTR_SP1`, `CSTR_SP2` | Celsius convention and MJ→kJ conversion made explicit; full-state simulations do not solve the original observer task |
| 3.10, Eqs. 47–54 | 4×4 distillation Column A, 82 states | `column_a_rhs` | All stages, feed, condenser and reboiler implemented; NTNU precision for nominal reflux/boilup |
| 3.10 | 2×2 Column A with LV structure | `column_a_lv_rhs` | D/B level loops added with stated P gain; other named configurations are design extensions |
| 3.11 | ALSTOM nonlinear gasifier II and PI baseline | External simulator protocol | Four independent manipulated flows, constraints and official challenge cases must come from author's package |
| 3.12, Eqs. 55–58 | Control-oriented wind turbine | `wind_rhs`, `wind_matrices`, `RotorMap` | Full 9-state reduced model; bundled 2022 ROSCO map is a documented later-map variant |
| 3.12 | High-order FAST/NREL 5 MW turbine | `run_external`; [external guide](EXTERNAL_MODELS.md) | Requires simulator, turbine files, controller, inflow and case versions; no full aeroelastic results claimed |
| 3.13 | Tennessee Eastman original and revised simulator | Verified source download; `run_external` | Official original 50-state and revised 52-state versions kept distinct; no simplified replacement |
| 4.2 | Wind TS/PDC controller example | [Worked architecture exercise](CASE_STUDIES.md#12-reduced-and-aeroelastic-wind-turbines-312) | Local LQR/scheduling architecture discussed; gains, memberships and full closed-loop results not reproduced |

All Python functions live in [benchmarks.py](../python/intelligent_control/benchmarks.py). Model equations are evaluated without clipping states to hide integration failure. Physical domain checks stop inappropriate experiments. Integrator and step size must suit the process; the stiff CSTR/column and discontinuous-friction systems need convergence checks.

## Source audit and corrections

1. **Three tanks:** Table 6 prints cubic metres for cross-sectional areas. Areas are implemented in square metres. Eq. (36) closes all nominal outlet valves. Consequently the total stored volume satisfies `dV/dt=q1+q2`; sustained positive pumping cannot have an equilibrium. A drain must be declared as an extension before doing steady-state tracking.
2. **CSTR:** Table 7 labels temperatures K, although Eq. (41) adds 273.15. Values 87, 106 and 104.9 are therefore treated as degrees Celsius. Cooling is supplied in MJ/h and converted to kJ/h in the coolant equation. The printed steady states are rounded; small derivative residuals are expected. Concentrations are mol/m³, not mol/L.
3. **Column:** Eq. (47) prints `V[i+1]`; its component balance and the original [NTNU model description](https://skoge.folk.ntnu.no/book/matlab_m/cola/cola.html) use the incoming vapor `V[i-1]`. The implementation follows this conservative balance. NTNU's model uses L0=2.70629 and V0=3.20629; Table 9 rounds these. In LV configuration D and B hold the end-vessel levels, leaving L and V for composition control, as shown in the paper's Fig. 9 and the primary implementation.
4. **Pneumatics:** the review gives no valve/orifice mass-flow law and no numerical κ. Table 4 calls 8.314 a mass-specific air constant, although that number is the universal molar constant. The literal balance accepts this printed value; the practice experiment explicitly selects R=287.05 J/(kg K), κ=1.4 and a linear valve approximation. The vertical-load drawing also does not supply a gravity term in Eq. (33). These alternatives must not be compared with published benchmark scores as if identical.
5. **Hydrostatic drive:** Table 5 combines normalized angle limits with static gains 241.67 and 283.33, and pressure/volume units with numerical conversion factors. The final torque expression contains maximum pump displacement where a motor displacement might be expected. `hydrostatic_rhs` retains the printed expression and reports **transcription only**. An arbitrary rescaling is not a correction established by evidence.
6. **Bioreactor:** for Γ=0.4, β=0.02 and u=0.769, Eqs. (37) yield the nonwashout equilibrium C₂≈0.9235897741, C₁≈0.0872975478. The prose instead reports C₁=0.1236837. Substituting that biomass with the equilibrium substrate leaves dC₂≈0.29603. The notebook verifies this discrepancy; it does not force the inconsistent prose number into the dynamics.
7. **Metric names:** in this article “MAE” in Eq. (1) is the **maximum** absolute error, not today's common mean absolute error. Report `max_abs_error` explicitly. VAF uses the variance of residuals and can ignore constant bias; it is not generally identical to R².

## Reporting a comparison

Report source version/hash, state/input units, initialization, solver tolerances, sample and hold periods, seeds, disturbances, actuator and state constraints. Split identification trajectories before normalization or feature fitting. Record one-step predictions with measured history separately from free-run predictions with predicted history. Report per-output RMSE, maximum absolute error, R²/VAF where defined, model size, and elapsed time. For control report tracking IAE/RMSE, settling specification, input energy and movement, and all constraint violations. A short synthetic experiment does not demonstrate global stability or industrial safety.

The [external source guide](EXTERNAL_MODELS.md) records what has actually been retrieved and what remains necessary for canonical comparisons.

The [coverage review](../docs/COVERAGE_REVIEW.md) separates the thirteen documented benchmark sections, ten implemented mathematical cores, optional variants and experiments that still require data, source clarification or an external runtime.

# Validation record

Validation date: 4 November 2026. All course experiments use synthetic data.

## Numerical experiments

All nine Python laboratory programs executed locally. Their actual outputs are stored in the per-laboratory `results/metrics.json` and trace CSV files. The aggregate [execution record](execution.json) records numerical values and elapsed time from the final notebook executions. Runtime is environment-dependent and is not used to rank methods.

The current Python suite passed **175 numerical tests**: the previous 131 checks plus 23 pneumatic physical-model tests, eight hydrostatic SI tests, eight throttle pipeline tests and five ALSTOM transport tests. These include independent hidden-path enumeration, first-passage equations, long-sequence scaling, training boundaries, EM likelihood monotonicity, causal supervision, mass/solute conservation, analytical filling/draining trajectories, finite-difference Jacobians, transfer consistency, deviation coordinates, local Riccati/pole checks, wind interpolation and actuator limits. The nine course notebooks, benchmark notebook and physical-tank notebook executed with fresh Jupyter kernels, saved numerical outputs and no error cells. See the [notebook record](notebook-validation.json). Course comparison figures, sensor diagnosis, physical-tank results and the wind-control comparison were visually inspected.

The [physical Blending Tank](../blending-tank/README.md) has explicit units, an equilibrium model and a separate filling case. Dedicated evidence and runtime limitations are in the [tank validation record](../blending-tank/VALIDATION.md).

The Markov test uses 600 samples from an independent seed after calibration on 20 separate 150-sample records. Online filtering attained 0.876667 state accuracy, versus 0.756667 for instantaneous emission MAP. The fixed alarm threshold produced 42 true positives, 13 false negatives and no false positives in this particular realization. These are synthetic sample results, not population reliability estimates. Offline smoothing and Viterbi are scored separately and never enter control. The controller uses calibrated sensor biases; the Baum–Welch illustration has a favorable initialization at the simulator probabilities, as stated in the [limitations](LIMITATIONS.md).

The local runtime is Python 3.12 with NumPy 2.5.4, SciPy 1.18.1 and Matplotlib 3.11.2. Dependency ranges are recorded in `requirements.txt`; this run does not certify every allowed version combination.

Selected independent checks include exact tank response versus the analytical exponential, variable-volume solute conservation, ARX validation on a fresh excitation, PID saturation recovery, MPC bounds and move feasibility, fuzzy partition coverage, held-out and recursive neural prediction, genetic-search elitism and the evaluation budget. The benchmark suite checks reference equations, physical balances, nominal CSTR/column conditions, rotor-map bounds and external-case provenance.

The sample identification run estimated a 9.82375 min time constant for a nominal 10 min process and achieved a held-out free-run RMSE of approximately 0.00091121. The native benchmark runner produced 15 experiment/status entries; its Column A steady-state derivative residual was about 3.89e-13, and the three-tank total-volume balance residual was about 4.34e-19. No measured process data were used.

## Verified published execution

[Run 41896147563](https://github.com/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/actions/runs/41896147563) passed all three jobs on source commit `d4957d467b55b066462a2dea1b13d59c530380de`:

| Runtime | Executed evidence |
|---|---|
| Python 3.12 | 175 tests, nine course programs, physical-tank/wind/pneumatic studies and eleven notebooks |
| GNU Octave 11.1.0 | Nine units, ten article kernels, MPC/neural/Markov/tank checks, online adapters, wind, strict CSV import, pneumatic/hydrostatic variants and full-size synthetic throttle pipeline |
| MATLAB R2025b Update 7 with Simulink | The numerical checks above, **27 generated diagrams** and three revised Tennessee Eastman cases |

The [gallery](../simulink/models/README.md) preserves the original 25 SLX/PNG pairs unchanged from [run 41886384567](https://github.com/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/actions/runs/41886384567), with their original [provenance](../simulink/models/provenance.json). The latest run repeated those checks; its [base-suite report](native-simulink-latest.json) is preserved separately. The two additional physical variants have [new source/artifact/file hashes](../simulink/models/physical-variants/provenance.json). All 27 diagram views were visually inspected across these two preserved artifact sets; no operational absolute paths were found. Keep the repository source folders on the MATLAB path.

The base suite distinguishes nine continuous-plant ODE comparisons, three exact discrete recurrences, six Markov/HMM cases, two intelligent-control cases, wind PDC and two physical-tank diagrams. General PI/MPC diagrams have finite-state and final-tracking checks. The original preserved report records continuous-plant scaled error at most 2.33e-8, Markov/HMM error at most 1.12e-15, and physical startup/filling/linear error at most 6.76e-14. These are numerical consistency results, not measurement accuracy.

The new [pneumatic Simulink report](../simulink/models/physical-variants/pneumatic/validation.json) covers payloads 3, 6 and 9 kg, with maximum scaled state error 6.39e-9 and pressure error 1.37e-8 against independent Python trajectories. The [hydrostatic report](../simulink/models/physical-variants/hydrostatic/validation.json) covers 601 samples over 6 s: scaled state error 2.15e-7, power-balance residual 1.05e-12 W, and motoring validity throughout. Literal article fixtures and separate physical interpretations remain distinct. Source audits and calibration limits are linked in the [coverage review](COVERAGE_REVIEW.md).

The [native throttle report](../benchmarks/results/throttle-fixture-matlab.json) verifies the 10000/2500-row import, archive checks, train-only fitting and separate one-step/free-run evaluation on artificial records. Original measurements were not recovered.

## Native ALSTOM execution

[Windows run 41896750740](https://github.com/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/actions/runs/41896750740) passed on source `cb19bdb5bf36df5007cd8b4c249863d8bd2380db` in MATLAB R2025b Update 7. Eleven actual author PI cases plus two nominal solver checks produced thirteen CSVs and 62186 rows. Independent Python recomputation passed all trace/metric checks. All seventeen temporary private inputs were deleted and absence verified individually. Source and cleanup evidence are in the [provenance record](../benchmarks/results/alstom-native/provenance.json).

The [ALSTOM report](../benchmarks/ALSTOM_RESULTS.md) records negative performance results: all six pressure cases exceed the temperature tolerance, and the long demand ramp loses tracking. At 50% nominal load, temperature drift remains approximately -16.7123 K with strict, refined and author solver settings. The refined maximum difference is 1.145e-4 of the pressure-test tolerance scales. This sensitivity check covers only the nominal 50% case; it does not validate long-case convergence or reproduce historical controller rankings. Applied input limits pass within numerical tolerance, while command violations and output excursions remain reported.

The benchmark notebook was re-executed locally after the evidence refresh, with no error cells; its [refresh record](benchmark-notebook-refresh.json) pins the saved notebook hash. The final evidence publication updates reports, source-access status and notebook outputs; the numerical implementation is pinned by the distinct successful runs above. The [machine-readable CI record](ci-validation.json) identifies individual jobs and remaining boundaries.

## Additional native Windows verification

Official portable GNU Octave **11.3.0** on Windows x64 completed the full numerical suite in 1321.52 s. It passed all nine units, ten article kernels, seven MPC groups, seven Markov groups, seven physical-tank groups, streaming HMM and four causal control policies, fuzzy/neural adapters, wind LQR/PDC and the CSV importer. The [numerical record](native-octave-windows.json) pins the runtime archive and source-file hashes; the [execution log](native-octave-windows.txt) preserves completed checks. This run did not execute Simulink.

The streaming filter matched its native reference exactly, and the four causal PI traces differed by at most 7.8e-16. Wind speed RMSE was about 0.001570 rad/s. Neural evaluation also exposed limitations: the RBF one-step, recursive and out-of-domain RMSE values were approximately 0.00468, 0.11843 and 0.72880. Passing validation checks means these distinct behaviors and information boundaries were tested; it does not establish unrestricted generalization.

## Documents and diagrams

The three LaTeX editions compiled with Tectonic 0.17.0: 21 pages of course notes, 13 pages of exercises and 21 pages of worked solutions. All 55 final pages were rendered and visually inspected, including larger focused checks of diagrams, mathematical notation, accents, the bibliography and the complete Markov/HMM unit. Problem 09.5 begins on its own exercise-book page to keep its prompt together. Final compilation logs contain no overfull/underfull-box or missing-glyph warnings. Five original TikZ diagrams accompany the course text. The [document record](document-validation.json) contains page counts and SHA-256 checksums.

Eleven additional original equipment schematics are supplied as SVG and PNG in the [benchmark gallery](../benchmarks/DIAGRAMS.md). They were visually inspected, including full-size checks of repaired labels.

All local Markdown links and all eleven notebook document structures were checked. Colab links point to the corresponding real repository notebook paths; this does not claim an interactive Colab-browser session was tested.

## Reproduction commands

```bash
python tools/run_course.py --all
python benchmarks/run_benchmarks.py
python benchmarks/run_wind_control.py
python tools/validate.py --notebooks
```

```matlab
addpath('matlab');
validate_all;
validate_paper;
validate_online_hmm;
validate_intelligent_adapters;
validate_wind_control;
validate_io_csv;
validate_pneumatic_physical;
validate_hydrostatic_si;
validate_throttle_reference;
% MATLAB with Simulink:
addpath('simulink');
validate_simulink_suite('simulink/generated');
validate_pneumatic_simulink('simulink/generated-pneumatic');
validate_hydrostatic_simulink('simulink/generated-hydrostatic');
```

The [validation workflow](https://github.com/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/actions/workflows/validate.yml) runs Python, GNU Octave and native MATLAB/Simulink in separate jobs. Its status belongs to the particular commit shown by GitHub.

## Earlier published executions

The earlier [coverage review](COVERAGE_REVIEW.md) passed [run 41871009584](https://github.com/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/actions/runs/41871009584) on source commit `4662549b215be92714a874ef3caed9992cce1063`. Python reran **115 tests**, all nine course programs, the physical-tank study and **eleven notebooks**. GNU Octave 11.1.0 passed all nine units, the newly added dynamic multiloop comparison and fuzzy-PID derivative/ablation assertions, seven Markov/HMM groups, seven physical-tank groups and ten mathematical benchmark checks. This run validates the corrected MATLAB/Octave numerical source. It does not execute proprietary MATLAB or Simulink, recover missing industrial data or certify the full published benchmark protocols. The follow-up evidence record changes documentation only.

The physical tank passed [run 41866227718](https://github.com/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/actions/runs/41866227718) on source commit `7fcb51d9904748f998b459593f1730946ee39d24`. Python reran all **115 tests**, nine course programs, the physical-tank study and **eleven notebooks**. GNU Octave 11.1.0 on Ubuntu 26.04.1 passed the **seven physical-tank check groups**, nine course units, seven Markov/HMM groups and ten mathematical benchmark checks. This validates the numerical functions; the Simulink diagrams were not executed. No source correction was required after this run.

The Markov extension passed [run 41860754694](https://github.com/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/actions/runs/41860754694) on source commit `0418af4458abf7c264ea4f1cba320e4a940cf29c`. Python reran all **84 tests**, all **nine laboratory programs** and all **ten notebooks** successfully. GNU Octave 11.1.0 on Ubuntu 26.04.1 passed all **nine laboratory units**, the **seven Markov/HMM mathematical check groups**, and the existing ten mathematical benchmark checks. Its independently generated Markov test had filtered state accuracy 0.875; random streams differ between languages, while the small exact likelihood/posterior/Viterbi fixtures agree. No source corrections were required after this run.

The following initial validation remains part of the history:

[Run 41849137529](https://github.com/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/actions/runs/41849137529) passed both jobs on source commit `c8a9a6fc6b4e4631152e5d00c8b781982ca97f8a`. Python reran all eight laboratory programs, all 41 tests and all nine notebooks successfully. GNU Octave 11.1.0 on Ubuntu 26.04 passed all eight curriculum units and the checks for ten mathematical benchmarks, including cross-language derivative fixtures, conservation/equilibrium checks, rotor-map evaluation and the PWA/TS held-out validation. No code corrections were needed after this run. The follow-up commit recording this evidence changes documentation only.

The [machine-readable CI record](ci-validation.json) identifies the current validated source commit and individual jobs. The earlier runs above had different test counts and did not yet include native MATLAB/Simulink execution.

## Evidence boundary

Native MATLAB/Simulink execution takes place on the identified CI runner; local Python and portable Octave are separate execution environments. Opening a notebook through a Colab URL is also distinct from executing it locally with Jupyter.

The official OpenFAST v5.0.0 NREL 5 MW case ran for 60 s with 9601 samples; all 41 signals were compared with the matching official baseline. The maximum normalized RMSE was approximately 0.00361, below the declared 0.01 threshold. Revised Tennessee Eastman ran three 0.2 h mode-1 cases: nominal, IDV1 and IDV4, with noise disabled. The [external-source guide](../benchmarks/EXTERNAL_MODELS.md) links their traces, source hashes and exact scope. These are simulated reference cases, not measured-plant validation or complete historical article reproduction.

The actual ALSTOM Windows MEX completed eleven cases and two solver checks, with the limitations recorded above. Original throttle measurements, pneumatic apparatus calibration and historical hydrostatic conventions remain external requirements. Historical ALSTOM reference reconciliation, wind settings and full controller/observer experiments also remain outside the executed scope. See the [coverage review](COVERAGE_REVIEW.md) and [technical assessment](ASSESSMENT.md).

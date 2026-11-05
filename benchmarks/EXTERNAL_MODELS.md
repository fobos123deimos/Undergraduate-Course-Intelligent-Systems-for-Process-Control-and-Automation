# Official external models and reproducibility

An industrial plant is not reconstructed by assigning its name to an arbitrary low-order ODE. This directory provides source retrieval, checked interfaces, and experiment protocols for the portions whose complete equations/data are distributed outside the review.

## Completion review on 4 November 2026

The [dated access record](external_access_review.json) separates availability from execution. The [OpenFAST manifest](openfast_manifest.json) pins release binaries by SHA-256 and inputs by their Git blob hashes at the release's exact regression-test commit. Downloaded third-party files remain under ignored `external/`.

| Case | Current result | Remaining requirement |
|---|---|---|
| NREL 5 MW / OpenFAST | Official Windows v5.0.0 and matching turbulent onshore case executed for 60 s; 9601 samples, 41 non-time channels, all finite and compared with the official binary baseline | Historical 2014 reproduction still needs the exact wind/controller case |
| Tennessee Eastman | Official revised C source compiled and executed in MATLAB R2025b/Simulink: nominal mode1, IDV1 and IDV4 passed, 0.2 h each | Other modes and full-duration protocols remain separate |
| Throttle | Exact original ZIP URL recovered from two archived provider pages; public ZIP captures and measurements still unavailable; Python/MATLAB evaluation pipeline tested on labeled artificial records | Original train/test records and provenance; unrelated datasets are not substituted |
| ALSTOM Gasifier II | Author's R2017 plant and PI executed on Windows in eleven cases plus two nominal solver comparisons; thirteen CSVs independently checked | PI performance violations remain; other controllers, the full coal-quality envelope and historical-result reconciliation are incomplete; reruns require the author package and compatible Windows runtime |

The OpenFAST [evidence](results/openfast-validation.json) records all source/output hashes and a [compact trace](results/openfast-validation.csv). Maximum normalized channel RMSE against the official baseline is 0.003609 or less, below the declared 0.01 tolerance; the worst channel is the solver iteration counter. Rotor azimuth differences are modulo 360 degrees, and time alignment accounts for text's four-decimal rounding. This is a cross-build regression check, not certification of turbine fatigue or the survey's controller ranking.

```bash
python benchmarks/run_openfast_reference.py
# Existing runs are refused. Use --external-dir with a fresh path to repeat.
```

This command fetches 56 verified files, executes the official program/controller and validates all output channels. Its only input-file changes are text output encoding and the path to the same-release controller DLL. It preserves the official 60 s duration, 0.00625 s step, turbulent inflow and physical/control parameters. Linux/macOS need a separately pinned native build; the recorded execution used the supported Windows release binary.

## Downloaded and verified sources

The following files were retrieved on 2026-11-04 for inspection. Their SHA-256 values are pinned in `external_sources.json`. The downloader verifies the hash before extraction and refuses changed content. The official archives are stored locally outside the committed collection because their redistribution terms are not stated explicitly in the archive. Do not infer an open-source license merely from a public download.

| Source | Version / scope | State |
|---|---|---|
| [UW original Tennessee Eastman](https://depts.washington.edu/control/LARRY/TE/download.html) `tecode.zip` | Original 50-state Fortran, include and historical MATLAB wrappers | Retrieved; legacy ZIP compression needs 7-Zip or a compatible extractor |
| Same provider, `temexd_mod.zip` | Revised 2015 C/Simulink implementation; 50 plant continuous states from executable `NX`; example open/closed-loop models | Retrieved, compiled and executed; [three native cases passed](results/te-native/validation.json); [state-count audit](TE_STATE_COUNT_AUDIT.md) |
| [Roger Dixon's Gasifier archive](https://www.researchgate.net/publication/326066211_Gasifier_R2015_and_2017) | R2015 and R2017 Simulink diagrams, Windows MEX, initial states, PI baseline, 2002 challenge specification | Retrieved through normal browser flow; source files pinned in [manifest](alstom_manifest.json); [native Windows results](ALSTOM_RESULTS.md) preserved |
| [NTNU Column A](https://skoge.folk.ntnu.no/book/matlab_m/cola/cola.html) `colamod.m` | Original 82-state material-balance model | Retrieved and compared with Python balances |
| [ROSCO NREL 5 MW rotor table](https://github.com/NatLabRockies/ROSCO/blob/main/Examples/example_inputs/Cp_Ct_Cq.NREL5MW.txt) | Table header dated 2022-01-13 | Included unmodified with Apache-2.0 license; used for reduced-model demonstration |

```bash
python benchmarks/fetch_external.py --source te-revised
python benchmarks/fetch_external.py --source column-a
```

These commands write into ignored `benchmarks/external/`. They do not execute downloaded programs.

## Tennessee Eastman (3.13)

The original benchmark has 12 manipulated variables, 41 measured outputs, 50 states and six operating modes. The archived revised 2015 C plant also declares 50 continuous states through `NX` and `ssSetNumContStates(S,NX)`. Its parameter comment mentioning 52 conflicts with those executable declarations; the [state-count audit](TE_STATE_COUNT_AUDIT.md) documents the correction to earlier repository metadata. The revised package changes numerical handling, so report its version when using it. Its optional additional signals and disturbances do not silently become part of the 1993/2014 specification. The official archive warns that adaptive solver calls to the original random/disturbance logic can produce inconsistent results. Use the original fixed-step protocol or the revised code as appropriate and state which.

The retrieved revised archive contains `temexd_mod.c`, `teprob_mod.h`, `tesys.mdl`, `R12_ExampleScript.m`, and `MultiLoop_mode1.mdl`, `MultiLoop_mode3.mdl`, `MultiLoop_Skoge_mode1.mdl`, their initialization files and a historical Windows MEX binary. `run_te_reference.m` compiles the C source for the active MATLAB runtime in a private source copy and exports a 0.2 h closed-loop mode-1 case. Initialization is supplied through `SimulationInput` instead of changing the user's base workspace. The original equations, controller and supplied initial states are retained.

The distributed mode1 diagram has IDV8 active by default. The runner explicitly clears all 28 disturbance inputs for the nominal case. `validate_te_reference` then runs IDV1 (feed composition) and IDV4 (reactor cooling-water inlet temperature) from time zero. It checks complete aligned output grids, finite signals, actuator limits, pressure/level ranges and a measurable response relative to nominal. Measurement noise is disabled using documented bit4 with seed17. Solver: ode45, relative/absolute tolerances 1e-7/1e-9, maximum step 0.0005 h. These are three short integration checks, not a complete six-mode challenge study.

```matlab
addpath('benchmarks');
run_te_reference('benchmarks/external/te-revised/temexd_mod', 'benchmarks/results/te-mode1.csv');
validate_te_reference('benchmarks/external/te-revised/temexd_mod', 'benchmarks/results/te-native');
```

The [native validation record](results/te-native/validation.json) and adjacent CSV files contain the executed results: 21 saved rows per case, 41 measured outputs and 12 inputs. Nominal maximum scaled drift was 0.001447 or less; both specified disturbances changed the output trajectory. MATLAB R2025b Update 7 compiled the official C source and passed all three integration checks. These results came from [CI run 41878490951](https://github.com/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/actions/runs/41878490951); that run's separate wind-structure check failed and was repaired subsequently, so the TE evidence is the successful native command and exported results, not a claim that the whole run passed.

The same three cases also passed in the fully successful [workflow 41886384567](https://github.com/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/actions/runs/41886384567), alongside the original 25 course Simulink models, and again in [workflow 41896147563](https://github.com/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/actions/runs/41896147563), which additionally validated the two physical variants. The preserved TE traces retain their original execution provenance.

For a broader study, use the package's exact disturbance switches, add feed loss and valve sticking, and record shutdowns as failures rather than discarding them. Compare product rate/quality variability, input movement, transition time and constraint excursions. The review deliberately does not define one universal scalar score.

## ALSTOM Gasifier II (3.11)

Roger Dixon provides the nonlinear challenge package at [the author's Gasifier R2015 and 2017 record](https://www.researchgate.net/publication/326066211_Gasifier_R2015_and_2017). On 4 November 2026, the normal browser download succeeded and yielded `Gasifier_R2015and2017.zip` (452992 bytes), SHA-256 `dc84303d39c851350fdf5e62f6ac9aadaab804840519031245eeef23e4575cdf`. Direct ordinary HTTP requests to the same author's download links still returned 403. The downloader therefore accepts a normally downloaded local archive and verifies the same pinned hash before extraction:

```powershell
python benchmarks/fetch_external.py --source alstom-gasifier --local-file "$env:USERPROFILE/Downloads/Gasifier_R2015and2017.zip"
```

The retrieved package includes open-loop and PI closed-loop diagrams, initial conditions at 0%, 50% and 100% load, and the four-page `Specification.pdf`. Its plant is a 25-state `gasifier.mexw64`; three PI integrators make 28 initialized continuous states in the closed-loop model. No C/Fortran source or Linux binary is supplied. The MEX imports `libmx.dll`, `libmex.dll` and `MSVCR100.dll`; a compatible Windows MATLAB/Simulink and Microsoft runtime are needed. Native execution passed on Windows Server 2022 with MATLAB R2025b Update 7 and a pinned Microsoft runtime. The specification supplies no explicit redistribution license: the archive, binary and specification are not committed or included in public result artifacts. Temporary private inputs used for execution were deleted, with absence verified for all seventeen entries.

The [source inspection evidence](results/alstom-source-inspection.json) confirms all six required file hashes, AMD64 Windows binary format, finite initial states of dimensions [25, 1, 1, 1], consistent demand tables and the original disturbance expressions. Reproduce this inspection without MATLAB using `python benchmarks/inspect_alstom_source.py`. This checks the received package, not the simulator's numerical output.

Work with the original nonlinear open-loop model and its PI baseline. The five mass-flow inputs are char, air, coal, steam and limestone, but limestone follows coal in a fixed ratio, leaving four independent inputs. The controlled outputs are gas calorific value, bed mass, pressure and temperature. Preserve magnitude/rate constraints, sink-pressure disturbance shapes, coal-quality changes and the three load conditions from the challenge instructions. Compare each candidate with the same baseline initialization and disturbance realization. Report per-output maximum and integrated absolute deviations plus every constraint violation. A four-state proxy would not test this benchmark.

`run_alstom_reference.m` and `validate_alstom_reference.m` use the actual supplied model, parameter names, logging signals and initial-state files. They verify every necessary source file against [the manifest](alstom_manifest.json), run in a private copy, and leave the source package untouched. The test collection is:

- Three 300 s nominal runs at 0%, 50% and 100% load.
- Six canonical 300 s sink-pressure cases: a -0.2 bar step at 30 s or a 0.2 bar, 0.04 Hz sine, at each load.
- The supplied 50% to 100% load ramp over 100–700 s, followed until 5000 s as in `rampplot.m`.
- A +8% coal-quality ramp over 10–20 s at 100% load, followed until 5000 s. This is one documented challenging case, not the complete ±18% envelope.

The wrapper uses ode23tb with relative/absolute tolerances 1e-6/1e-8 and maximum step 0.25 s; the supplied plant, PI gains and load interpolation remain unchanged. It checks finite aligned traces, full duration and the actual logged disturbance/load shapes. It exports CV/bed mass/pressure/temperature and char/air/coal/steam flows, with maximum errors, integrated absolute errors, magnitude and rate violations. Pressure-test output tolerances are [10000 J/kg, 500 kg, 10000 Pa, 1 K]; input upper bounds are [3.5, 20, 10, 6] kg/s and slew bounds [0.2, 1, 0.2, 1] kg/s². Violations are reported rather than erased or treated as successful control: the author's specification explicitly describes limitations of the supplied PI under coal-quality changes.

```matlab
addpath('benchmarks');
validate_alstom_reference('benchmarks/external/alstom-gasifier/Gasifier_R2017', ...
    'benchmarks/results/alstom-native');
```

**Native execution completed:** [workflow 41896750740](https://github.com/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/actions/runs/41896750740), source `cb19bdb5bf36df5007cd8b4c249863d8bd2380db`, produced thirteen CSVs with 62186 rows: eleven cases above and two additional 50% nominal runs using refined and author-default solver settings. Independent Python checks recomputed the exported metrics and verified channel, disturbance and load definitions. The [results report](ALSTOM_RESULTS.md) preserves hashes, trajectories and performance limitations.

All six pressure-disturbance cases exceed the 1 K temperature-error limit. The applied flow magnitude and slew constraints hold within numerical tolerance; pre-constraint commands are logged separately. At 50% nominal load, the approximately -16.7123 K final temperature error persists with refined and author-default settings. The maximum strict-to-refined output difference is 1.14454e-4 when scaled by the pressure-test limits. This sensitivity check concerns only that nominal case; it does not establish convergence of the 5000 s ramp or coal-quality runs. The long load ramp leaves its intended operating-load range, and the observed PI behavior remains a documented reproduction limitation rather than evidence that the challenge requirements were met. Other controllers and the complete coal-quality sweep remain future work.

## Wind turbine: FAST / OpenFAST (3.12)

The paper's high-order verification model is FAST with the NREL 5 MW reference turbine. The current [OpenFAST project](https://github.com/OpenFAST/openfast) and [reference test models](https://github.com/OpenFAST/r-test) are successors, not a bitwise reconstruction of a 2014 FAST case. Pin the simulator release, reference-model commit, controller binary, inflow files and time step. Validate the unmodified reference case before changing a controller.

```python
from intelligent_control.benchmarks import run_external
# Use a new run directory containing the complete pinned OpenFAST case.
run_external(['openfast', 'case.fst'], 'my_new_case', 'case.out', metadata)
```

For partial load report tracking of the optimal rotor-speed/energy target. For full load report rotor-speed disturbance error, pitch peak and energy, and rotor/generator constraints. Structural comparison needs tower/blade/shaft loads, extreme values and damage-equivalent loads from a specified rainflow convention, S–N slope and duration. The reduced model's deflections are not certified fatigue life. The included ROSCO performance map makes the reduced model executable, but does not identify the exact map or turbulent realization behind Tables 11–12 of the paper.

## Throttle (3.4)

The original GMA/TU Dortmund source cited in the review is `http://www.rst.e-technik.tu-dortmund.de/cms/de/Veranstaltungen/GMA-Fachausschuss/Benchmark/index.html`. Its 2015 and 2019 archived pages identify the exact `Throttle.zip` download. The live download redirects to HTML, and the checked public archive indexes contain no ZIP capture. Current university datasets/software catalogs did not provide the measurements. The [recovery report](THROTTLE_RECOVERY.md) preserves fifteen dated checks and the exact address. The paper specifies 0.01 s sampling, 10000 training samples from a multisine experiment, and 2500 validation samples from quasi-amplitude-modulated pseudorandom excitation. Preserve duty cycle in percent and output angle in degrees.

`LocalARX` implements the eight-local-model structure discussed in section 4.1: each local predictor uses `[y(k-1),y(k-2),u(k-1),1]`; partitions use `[y(k-1)-y(k-2),u(k-1)]`. Its crisp nearest-centroid and soft inverse-distance partitions are explicit teaching alternatives, not the paper's recovered fitted PWA polyhedra or TS coefficients. Fit on measured training data only; test one-step and recursive modes separately. Do not cite the paper's 1.03°/1.06° test RMSE as a result of this code.

`run_throttle_reference.py` and `run_throttle_reference.m` now provide the complete input and evaluation workflow. A shared manifest binds archive/member provenance, source and CSV hashes, units, timestamps and exact record counts. Both reject redirected HTML, malformed ZIPs, missing archive members and altered records. Preprocessing and model fitting use only the training experiment. Separate one-step and free-run scores exclude the two seed samples. Full-size artificial fixtures validate the workflow in Python and MATLAB/Octave; they do not establish source authenticity or reproduce Table 11. See the [manifest and commands](THROTTLE_RECOVERY.md#ready-to-run-protocol).

## Pneumatic and hydrostatic source reconciliation

The [pneumatic audit](PNEUMATIC_AUDIT.md) uses the original Schulte-Hahn manuscript to resolve the gravity offset removed before local identification and to recover three local linear fits. A separate six-state model includes specific-air units, reversible choked flow and consistent chamber/mechanical energy. Actual valve geometry, leakage, thermal and stiction calibration remain external requirements.

The [hydrostatic review](HYDROSTATIC_SOURCE_REVIEW.md) uses open primary papers from 2006, 2008 and 2011 to explain bar/mm³ conversions and the motor displacement in torque. The separate SI model exposes displacement/capacitance conventions and normalized-angle inputs explicitly. The exact 2007 full text, electrical gains and historical calibration remain unresolved. Both new variants passed Python/MATLAB/Octave checks and native Simulink validation in [workflow 41896147563](https://github.com/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/actions/runs/41896147563), source `d4957d467b55b066462a2dea1b13d59c530380de`. Separate [pneumatic](../simulink/models/physical-variants/pneumatic/validation.json) and [hydrostatic](../simulink/models/physical-variants/hydrostatic/validation.json) reports preserve execution evidence. Their mathematical consistency does not authenticate the original experiments.

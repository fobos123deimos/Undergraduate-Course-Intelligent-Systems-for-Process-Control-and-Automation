# Official external models and reproducibility

An industrial plant is not reconstructed by assigning its name to an arbitrary low-order ODE. This directory provides source retrieval, checked interfaces, and experiment protocols for the portions whose complete equations/data are distributed outside the review.

## Downloaded and verified sources

The following files were retrieved on 2026-11-04 for inspection. Their SHA-256 values are pinned in `external_sources.json`. The downloader verifies the hash before extraction and refuses changed content. The official archives are stored locally outside the committed collection because their redistribution terms are not stated explicitly in the archive. Do not infer an open-source license merely from a public download.

| Source | Version / scope | State |
|---|---|---|
| [UW original Tennessee Eastman](https://depts.washington.edu/control/LARRY/TE/download.html) `tecode.zip` | Original 50-state Fortran, include and historical MATLAB wrappers | Retrieved; legacy ZIP compression needs 7-Zip or a compatible extractor |
| Same provider, `temexd_mod.zip` | Revised 2015 C/Simulink implementation; 52 continuous states; example open/closed-loop models | Retrieved and archive contents inspected; runtime simulation pending |
| [NTNU Column A](https://skoge.folk.ntnu.no/book/matlab_m/cola/cola.html) `colamod.m` | Original 82-state material-balance model | Retrieved and compared with Python balances |
| [ROSCO NREL 5 MW rotor table](https://github.com/NatLabRockies/ROSCO/blob/main/Examples/example_inputs/Cp_Ct_Cq.NREL5MW.txt) | Table header dated 2022-01-13 | Included unmodified with Apache-2.0 license; used for reduced-model demonstration |

```bash
python benchmarks/fetch_external.py --source te-revised
python benchmarks/fetch_external.py --source column-a
```

These commands write into ignored `benchmarks/external/`. They do not execute downloaded programs.

## Tennessee Eastman (3.13)

The original benchmark has 12 manipulated variables, 41 measured outputs, 50 states and six operating modes. The revised 2015 package changes numerical handling and uses 52 continuous states; report that version when using it. Its optional additional signals and disturbances do not silently become part of the 1993/2014 specification. The official archive warns that adaptive solver calls to the original random/disturbance logic can produce inconsistent results. Use the original fixed-step protocol or the revised code as appropriate and state which.

The retrieved revised archive contains `temexd_mod.c`, `teprob_mod.h`, `tesys.mdl`, `R12_ExampleScript.m`, and `MultiLoop_mode1.mdl`, `MultiLoop_mode3.mdl`, `MultiLoop_Skoge_mode1.mdl`, their initialization files and a historical Windows MEX binary. Build the C source with a supported MATLAB compiler for the active runtime instead of treating an old binary as portable. `run_te_reference.m` runs a short closed-loop mode-1 case and exports its output without editing the official model.

```matlab
addpath('benchmarks');
run_te_reference('benchmarks/external/te-revised/temexd_mod', 'benchmarks/results/te-mode1.csv');
```

First confirm stationarity at the chosen mode with no disturbance. Then use the package's exact disturbance switches, compare at least feed composition, feed loss, cooling-water change and valve sticking, and record shutdowns as failures rather than discarding them. Compare product rate/quality variability, input movement, transition time and constraint excursions. The review deliberately does not define one universal scalar score. The local repository has no measured or simulated TE score until this external runtime has actually completed.

## ALSTOM Gasifier II (3.11)

Roger Dixon provides the nonlinear challenge package at [the author's Gasifier R2015 and 2017 record](https://www.researchgate.net/publication/326066211_Gasifier_R2015_and_2017). Its named archive is `Gasifier_R2015 and 2017.zip`; the original article's older staff-page link is historical. An access-controlled download must be obtained through its normal provider flow. No replacement package or synthetic benchmark result is bundled.

Work with the original nonlinear open-loop model and its PI baseline. The five mass-flow inputs are char, air, coal, steam and limestone, but limestone follows coal in a fixed ratio, leaving four independent inputs. The controlled outputs are gas calorific value, bed mass, pressure and temperature. Preserve magnitude/rate constraints, sink-pressure disturbance shapes, coal-quality changes and the three load conditions from the challenge instructions. Compare each candidate with the same baseline initialization and disturbance realization. Report per-output maximum and integrated absolute deviations plus every constraint violation. A four-state proxy would not test this benchmark.

After installation, call `run_external` with the actual MATLAB launcher and output path. It requires source hash/version, solver, sample period and seed and refuses a preexisting output file. The launcher and signal-export names must be selected from the installed package, not guessed.

## Wind turbine: FAST / OpenFAST (3.12)

The paper's high-order verification model is FAST with the NREL 5 MW reference turbine. The current [OpenFAST project](https://github.com/OpenFAST/openfast) and [reference test models](https://github.com/OpenFAST/r-test) are successors, not a bitwise reconstruction of a 2014 FAST case. Pin the simulator release, reference-model commit, controller binary, inflow files and time step. Validate the unmodified reference case before changing a controller.

```python
from intelligent_control.benchmarks import run_external
# Use a new run directory containing the complete pinned OpenFAST case.
run_external(['openfast', 'case.fst'], 'my_new_case', 'case.out', metadata)
```

For partial load report tracking of the optimal rotor-speed/energy target. For full load report rotor-speed disturbance error, pitch peak and energy, and rotor/generator constraints. Structural comparison needs tower/blade/shaft loads, extreme values and damage-equivalent loads from a specified rainflow convention, S–N slope and duration. The reduced model's deflections are not certified fatigue life. The included ROSCO performance map makes the reduced model executable, but does not identify the exact map or turbulent realization behind Tables 11–12 of the paper.

## Throttle (3.4)

The original GMA/TU Dortmund source cited in the review is `http://www.rst.e-technik.tu-dortmund.de/cms/de/Veranstaltungen/GMA-Fachausschuss/Benchmark/index.html`. The original measured files were not recovered in this build. The paper specifies 0.01 s sampling, 10000 training samples from a multisine experiment, and 2500 validation samples from quasi-amplitude-modulated pseudorandom excitation. Preserve duty cycle in percent and output angle in degrees.

`LocalARX` implements the eight-local-model structure discussed in section 4.1: each local predictor uses `[y(k-1),y(k-2),u(k-1),1]`; partitions use `[y(k-1)-y(k-2),u(k-1)]`. Its crisp nearest-centroid and soft inverse-distance partitions are explicit teaching alternatives, not the paper's recovered fitted PWA polyhedra or TS coefficients. Fit on measured training data only; test one-step and recursive modes separately. Do not cite the paper's 1.03°/1.06° test RMSE as a result of this code.

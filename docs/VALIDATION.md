# Validation record

Validation date: 4 November 2026. All course experiments use synthetic data.

## Numerical experiments

All eight Python laboratory programs executed locally. Their actual outputs are stored in the per-laboratory `results/metrics.json` and trace CSV files. The aggregate [execution record](execution.json) records numerical values and elapsed time from the final notebook executions. Runtime is environment-dependent and is not used to rank methods.

All **41 numerical tests passed** locally: 12 method checks, 8 independent worked-answer checks and 21 benchmark checks. The eight course notebooks and the benchmark notebook executed with fresh Jupyter kernels, with saved numerical outputs and no error cells. See the [notebook record](notebook-validation.json). All eight course comparison figures were visually inspected; unrelated identification/control scenarios occupy separate panels.

The local runtime is Python 3.12 with NumPy 2.5.4, SciPy 1.18.1 and Matplotlib 3.11.2. Dependency ranges are recorded in `requirements.txt`; this run does not certify every allowed version combination.

Selected independent checks include exact tank response versus the analytical exponential, variable-volume solute conservation, ARX validation on a fresh excitation, PID saturation recovery, MPC bounds and move feasibility, fuzzy partition coverage, held-out and recursive neural prediction, genetic-search elitism and the evaluation budget. The benchmark suite checks reference equations, physical balances, nominal CSTR/column conditions, rotor-map bounds and external-case provenance.

The sample identification run estimated a 9.82375 min time constant for a nominal 10 min process and achieved a held-out free-run RMSE of approximately 0.00091121. The native benchmark runner produced 15 experiment/status entries; its Column A steady-state derivative residual was about 3.89e-13, and the three-tank total-volume balance residual was about 4.34e-19. No measured process data were used.

## Documents and diagrams

The three LaTeX editions compiled with Tectonic 0.17.0: 17 pages of course notes, 11 pages of exercises and 18 pages of worked solutions. All 46 final pages were rendered and visually inspected, including full-size checks of diagrams, mathematical notation, accents and the bibliography. Final compilation logs contain no overfull/underfull-box or missing-glyph warnings. Four original TikZ diagrams accompany the course text. The [document record](document-validation.json) contains page counts and SHA-256 checksums.

Eleven additional original equipment schematics are supplied as SVG and PNG in the [benchmark gallery](../benchmarks/DIAGRAMS.md). They were visually inspected, including full-size checks of repaired labels.

All local Markdown links and all nine notebook document structures were checked. Colab links point to the corresponding real repository notebook paths; this does not claim an interactive Colab-browser session was tested.

## Reproduction commands

```bash
python tools/run_course.py --all
python benchmarks/run_benchmarks.py
python tools/validate.py --notebooks
```

```matlab
addpath('matlab');
validate_all;
validate_paper;
```

The [validation workflow](https://github.com/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/actions/workflows/validate.yml) runs Python and GNU Octave in separate jobs. Its status belongs to the particular commit shown by GitHub.

## Verified published execution

[Run 41849137529](https://github.com/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/actions/runs/41849137529) passed both jobs on source commit `c8a9a6fc6b4e4631152e5d00c8b781982ca97f8a`. Python reran all eight laboratory programs, all 41 tests and all nine notebooks successfully. GNU Octave 11.1.0 on Ubuntu 26.04 passed all eight curriculum units and the checks for ten mathematical benchmarks, including cross-language derivative fixtures, conservation/equilibrium checks, rotor-map evaluation and the PWA/TS held-out validation. No code corrections were needed after this run. The follow-up commit recording this evidence changes documentation only.

The [machine-readable CI record](ci-validation.json) identifies the validated source commit and individual jobs. This is actual Octave execution; it does not imply execution in proprietary MATLAB or Simulink.

## Evidence boundary

MATLAB/Simulink is not installed as an executable runtime in the local environment. The Simulink builder and original binary archive are therefore supplied without a claim of local proprietary-runtime execution. Opening a notebook through a Colab URL is also distinct from executing it locally with Jupyter.

Canonical throttle data, ALSTOM gasifier, FAST and Tennessee Eastman experiments have external requirements documented in the [benchmark guide](../benchmarks/README.md). A retrieved official source archive is not evidence that its complete industrial benchmark was executed. No measured-data validation or full industrial reproduction is claimed where the required inputs/runtime are absent.

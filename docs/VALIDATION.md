# Validation record

Validation date: 4 November 2026. All course experiments use synthetic data.

## Numerical experiments

All nine Python laboratory programs executed locally. Their actual outputs are stored in the per-laboratory `results/metrics.json` and trace CSV files. The aggregate [execution record](execution.json) records numerical values and elapsed time from the final notebook executions. Runtime is environment-dependent and is not used to rank methods.

All **115 numerical tests passed locally**: the original 41 method/curriculum/benchmark checks, 43 Markov/HMM checks and 31 corrected physical-tank checks. These include independent hidden-path enumeration, first-passage equations, long-sequence scaling, training boundaries, EM likelihood monotonicity, causal supervision, mass/solute conservation, analytical filling/draining trajectories, finite-difference Jacobians, transfer consistency and deviation-coordinate tests. The nine course notebooks, benchmark notebook and corrected physical-tank notebook executed with fresh Jupyter kernels, saved numerical outputs and no error cells. See the [notebook record](notebook-validation.json). All nine course comparison figures, the sensor-diagnosis figure and the corrected physical-tank figure were visually inspected.

The [physical Blending Tank](../blending-tank/README.md) has explicit units, an equilibrium model and a separate filling case. Dedicated evidence and runtime limitations are in the [tank validation record](../blending-tank/VALIDATION.md).

The Markov test uses 600 samples from an independent seed after calibration on 20 separate 150-sample records. Online filtering attained 0.876667 state accuracy, versus 0.756667 for instantaneous emission MAP. The fixed alarm threshold produced 42 true positives, 13 false negatives and no false positives in this particular realization. These are synthetic sample results, not population reliability estimates. Offline smoothing and Viterbi are scored separately and never enter control. The controller uses calibrated sensor biases; the Baum–Welch illustration has a favorable initialization at the simulator probabilities, as stated in the [limitations](LIMITATIONS.md).

The local runtime is Python 3.12 with NumPy 2.5.4, SciPy 1.18.1 and Matplotlib 3.11.2. Dependency ranges are recorded in `requirements.txt`; this run does not certify every allowed version combination.

Selected independent checks include exact tank response versus the analytical exponential, variable-volume solute conservation, ARX validation on a fresh excitation, PID saturation recovery, MPC bounds and move feasibility, fuzzy partition coverage, held-out and recursive neural prediction, genetic-search elitism and the evaluation budget. The benchmark suite checks reference equations, physical balances, nominal CSTR/column conditions, rotor-map bounds and external-case provenance.

The sample identification run estimated a 9.82375 min time constant for a nominal 10 min process and achieved a held-out free-run RMSE of approximately 0.00091121. The native benchmark runner produced 15 experiment/status entries; its Column A steady-state derivative residual was about 3.89e-13, and the three-tank total-volume balance residual was about 4.34e-19. No measured process data were used.

## Documents and diagrams

The three LaTeX editions compiled with Tectonic 0.17.0: 21 pages of course notes, 13 pages of exercises and 21 pages of worked solutions. All 55 final pages were rendered and visually inspected, including larger focused checks of diagrams, mathematical notation, accents, the bibliography and the complete Markov/HMM unit. Problem 09.5 begins on its own exercise-book page to keep its prompt together. Final compilation logs contain no overfull/underfull-box or missing-glyph warnings. Five original TikZ diagrams accompany the course text. The [document record](document-validation.json) contains page counts and SHA-256 checksums.

Eleven additional original equipment schematics are supplied as SVG and PNG in the [benchmark gallery](../benchmarks/DIAGRAMS.md). They were visually inspected, including full-size checks of repaired labels.

All local Markdown links and all eleven notebook document structures were checked. Colab links point to the corresponding real repository notebook paths; this does not claim an interactive Colab-browser session was tested.

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

The [final coverage review](COVERAGE_REVIEW.md) passed [run 41871009584](https://github.com/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/actions/runs/41871009584) on source commit `4662549b215be92714a874ef3caed9992cce1063`. Python reran **115 tests**, all nine course programs, the physical-tank study and **eleven notebooks**. GNU Octave 11.1.0 passed all nine units, the newly added dynamic multiloop comparison and fuzzy-PID derivative/ablation assertions, seven Markov/HMM groups, seven physical-tank groups and ten mathematical benchmark checks. This run validates the corrected MATLAB/Octave numerical source. It does not execute proprietary MATLAB or Simulink, recover missing industrial data or certify the full published benchmark protocols. The follow-up evidence record changes documentation only.

The physical tank passed [run 41866227718](https://github.com/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/actions/runs/41866227718) on source commit `7fcb51d9904748f998b459593f1730946ee39d24`. Python reran all **115 tests**, nine course programs, the physical-tank study and **eleven notebooks**. GNU Octave 11.1.0 on Ubuntu 26.04.1 passed the **seven physical-tank check groups**, nine course units, seven Markov/HMM groups and ten mathematical benchmark checks. This validates the numerical functions; the Simulink diagrams were not executed. No source correction was required after this run.

The Markov extension passed [run 41860754694](https://github.com/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/actions/runs/41860754694) on source commit `0418af4458abf7c264ea4f1cba320e4a940cf29c`. Python reran all **84 tests**, all **nine laboratory programs** and all **ten notebooks** successfully. GNU Octave 11.1.0 on Ubuntu 26.04.1 passed all **nine laboratory units**, the **seven Markov/HMM mathematical check groups**, and the existing ten mathematical benchmark checks. Its independently generated Markov test had filtered state accuracy 0.875; random streams differ between languages, while the small exact likelihood/posterior/Viterbi fixtures agree. No source corrections were required after this run.

The following initial validation remains part of the history:

[Run 41849137529](https://github.com/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/actions/runs/41849137529) passed both jobs on source commit `c8a9a6fc6b4e4631152e5d00c8b781982ca97f8a`. Python reran all eight laboratory programs, all 41 tests and all nine notebooks successfully. GNU Octave 11.1.0 on Ubuntu 26.04 passed all eight curriculum units and the checks for ten mathematical benchmarks, including cross-language derivative fixtures, conservation/equilibrium checks, rotor-map evaluation and the PWA/TS held-out validation. No code corrections were needed after this run. The follow-up commit recording this evidence changes documentation only.

The [machine-readable CI record](ci-validation.json) identifies the validated source commit and individual jobs. This is actual Octave execution; it does not imply execution in proprietary MATLAB or Simulink.

## Evidence boundary

MATLAB/Simulink is not installed as an executable runtime in the local environment. The Simulink builder is therefore supplied without a claim of local proprietary-runtime execution. Opening a notebook through a Colab URL is also distinct from executing it locally with Jupyter.

Canonical throttle data, ALSTOM gasifier, FAST and Tennessee Eastman experiments have external requirements documented in the [benchmark guide](../benchmarks/README.md). A retrieved official source archive is not evidence that its complete industrial benchmark was executed. No measured-data validation or full industrial reproduction is claimed where the required inputs/runtime are absent.

# MATLAB/Octave learning-stage replay

`matlab/validate_benchmark_learning.m` applies the nine learning stages to the ten saved native-case training/test records. It requires the generated CSV/JSON records in `benchmarks/results/learning`, MATLAB or GNU Octave, and the repository's existing MATLAB functions. No Optimization Toolbox, Statistics Toolbox or Deep Learning Toolbox is required.

```matlab
addpath('matlab');
records = validate_benchmark_learning();
% Explicit subset, useful during development:
one_case = validate_benchmark_learning({'artificial_siso'});
```

| Unit | Native computation | Comparison boundary |
|---|---|---|
| 1 | Training-only population mean/std, affine ARX least squares, held-out one-step and recursive prediction | Coefficients, normalization and scores checked against saved Python records |
| 2 | PI gains, unsaturated pole polynomial and complete applied-input recurrence | Saved PI trajectory replayed with the same update ordering and affine offset |
| 3 | Measured-disturbance feedforward and first-order actuator cascade | Saved trajectories replayed; cascade retains its different actuator dynamics |
| 4 | Eight-step affine MPC, three free moves, input ±2 and move ±0.4 | Existing toolbox-free dual QP solver; checks feasibility, objective against feasible hold, and explicit fallback; not identical SLSQP iterations |
| 5 | Nine-rule product/Sugeno incremental PI | Saved fuzzy trajectory replayed; no nonlinear stability guarantee |
| 6 | Ten-hidden-unit tanh MLP with 500 Adam steps; 16-center affine-plus-Gaussian RBF with ridge 1e-4 | Training statistics and centers use training rows only; native RNG differs, so network weights and scores need not equal Python |
| 7 | Real-coded GA, 10 individuals, 8 generations plus initial evaluation, 90 objective calls | Native elite history and gain bounds checked; training fitness and held-out control kept separate; saved Python selected gains also replayed independently |
| 8 | Fixed nominal PI/MPC/fuzzy controllers under input-gain factors 0.8, 1 and 1.2 | Paired scalar-predictor sensitivity studies, not full-order plant robustness |
| 9 | Native supervised HMM calibration on 20 independent 150-sample records, filtering, smoothing, Viterbi and stationarity | Saved zero-based test symbols converted to one-based once; causal prefix and probability checks; native calibration RNG differs from Python |

Every case retains its physical CSV input/output units and uses the training mean and scale to form normalized coordinates. The later controller exercises use the fitted scalar predictor and **do not rerun the original nonlinear plant**. Initial records, physical interpretations, omitted inputs and short operating windows retain the qualifications in [the learning guide](README.md).

The HMM still requires a known-clean reference for its synthetic residual symbols. Evaluation labels are used for scoring only. Smoothing and Viterbi remain retrospective; missing test-state support must not be interpreted as validated fault recall.

The function returns inspectable records and prints completed cases without overwriting saved Python evidence. Missing case files raise an error. Divergence and MPC fallback counts are retained rather than turned into claims of successful control. A prepared implementation is not proof of runtime execution; consult the repository's validation record for actual MATLAB/Octave runs.

## Executed native check

On 4 November 2026, official portable **GNU Octave 11.3.0, Windows x64**, completed all **ten cases and 90 learning-stage entries**. No MPC solver fallback occurred. Deterministic controller replay errors were below 2e-16 on the recorded scale. The [execution record](../../docs/benchmark-learning-octave.json) includes runtime, elapsed time, source/data hashes, native network/GA/HMM scores and the stated scope. This is an Octave execution; a separate MATLAB run must be identified independently.

Passing the checks means the computations and cross-language comparisons were exercised. Large normalized free-run ARX errors remain visible for the pneumatic model (about 34.73), CSTR (26.58) and Column A (6.89). These are evidence against interpreting the reduced predictor as an accurate long-horizon apparatus model.

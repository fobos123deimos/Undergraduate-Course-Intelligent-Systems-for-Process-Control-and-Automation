# MATLAB and GNU Octave laboratories

The [physical Blending Tank](../blending-tank/README.md) is available separately through `run_blending_tank(true)` and `validate_blending_tank`. Its `bt_*` functions declare units, operating points, deviation models and transfer channels explicitly. `blending_rhs` adapts named parameter fields to the five-input interface. The physical tank validation also runs inside `validate_all`.

The nine laboratories run without add-on toolboxes. The implementation includes its own linearly constrained quadratic MPC solver, fuzzy inference, neural training, genetic search, Markov-chain analysis and categorical hidden Markov models. Run from the repository root:

```matlab
addpath('matlab');
results = validate_all();
checks = validate_paper();
run_lesson(9, true);
```

For GNU Octave, use `octave --no-gui --quiet --eval "addpath('matlab'); validate_all(); validate_paper();"`.

| Unit | Executable work |
|---|---|
| 01 | Exact sampled concentration balance, ARX least squares, independent input validation and physical Blending Tank equilibrium |
| 02 | IMC-tuned PI, filtered-derivative PID, anti-windup and sampled closed-loop eigenvalues |
| 03 | Relative gain array, static decoupler, dynamic decentralized/decoupled comparison, measured-disturbance feedforward and fast actuator cascade |
| 04 | Constrained SISO and 2x2 MIMO MPC with prediction/control horizons, move penalties, input/slew/output bounds and explicit failure hold |
| 05 | Diagnostic rules, Sugeno and Mamdani inference, incremental fuzzy control, fuzzy PID gain scheduling and a matched fuzzy PI comparison |
| 06 | Perceptron, trained tanh MLP, regularized RBF, SOM, neural forward-model inversion and separate one-step/free-run/out-of-domain validation |
| 07 | Real and binary genetic search with tournament selection, crossover, mutation and elitism; a counted 12-evaluation genetic MIMO move-penalty search and a deterministic sweep |
| 08 | Common-scenario PI/feedforward/fuzzy/MPC comparison with IAE, ISE, input variation and a plant-mismatch experiment |
| 09 | Markov regimes, stationary and finite-horizon probabilities, first hitting times, categorical HMM filtering/smoothing/Viterbi, separate calibration records, Baum-Welch estimation and sensor-bias supervision of PI |

The shared teaching plant is `10 dc/dt = u + d - c`: a 100 L well-mixed vessel with 10 L/min flow, normalized feed composition, `0 <= u <= 1`, sampling interval 0.2 min and 80 min horizon. The initial concentration is 0.35. References are 0.35, 0.65 at 10 min and 0.45 at 55 min. A concentration disturbance of +0.08 begins at 45 min. These are illustrative parameters, separate from the article's benchmarks. All inputs, outputs and training samples are simulated.

The MPC uses full-state feedback and constant future reference/disturbance estimates. The shared `mpc_control` solves the finite-horizon convex quadratic problem by dual coordinate minimization, with input bounds, slew bounds and optional predicted-output bounds. Outputs are the full state; the final optimized move is held after the control horizon. Unit 04 demonstrates SISO slew bounds and a separate 2x2 plant with both slew and output bounds. It is not a multivariable model of the one-state vessel. Unit 07 retains a counted small genetic MIMO move-weight search and a separate deterministic sweep; neither establishes a global optimum over controller designs.

Call `[u,info]=mpc_control(A,B,x,reference,H,Nc,rho,previous,options)`. Options include `lower`, `upper`, `max_move` (default 0.08), `output_lower`, `output_upper`, `affine`, `state_weight`, `tolerance` and `max_iterations`. Bounds and affine terms accept scalar or per-channel vectors. Positive state weight and a positive-definite condensed objective are required for this solver; a singular objective reports failure rather than silently regularizing the requested cost. The previous actuator command must satisfy the input bounds.

The result reports success/status, iterations, primal feasibility, stationarity and complementarity residuals, planned inputs, increments, predicted outputs and cost. Infeasibility detected by a constraint bound, iteration exhaustion or numerical failure returns the previous actuator command. The held sequence and its constraint violation are reported, including an output violation when holding cannot satisfy the requested output limits. This makes failure visible; it does not establish recursive feasibility, robustness or a terminal-set stability result. `validate_mpc` checks independent scalar optima, an equality-constrained coupled optimum, move/output bounds, prediction timing, infeasibility and deliberate iteration exhaustion. Both languages now support the same constraint classes, while their optimizers and experiment settings differ.

Neural training, independent one-step validation, recursive free run and out-of-domain evaluation are separate. Unit 06 returns fixed trained models in `neural_models` and their evaluation traces/metrics in `neural_validation`. `neural_predict` evaluates a model without fitting; `neural_rollout` uses only its initial measured output and then feeds back predicted values. A new complete input trajectory evaluates one-step and free-run predictions against the same independent truth. Out-of-domain points deliberately exceed the training square `[0,1]^2` and never influence fitting or tuning. A small one-step error is not a free-run stability or extrapolation guarantee. Random streams and learned weights can differ between Python and MATLAB/Octave. A SOM remains unsupervised and is not evaluated with classification labels.

## Markov chains and hidden Markov models

`run_markov_lab(true)` is also available directly; the [ninth laboratory](../laboratories/09-markov-hidden-state-diagnosis/README.md) provides the study guide. It uses the 100 L tank and 0.2 min sampling interval, with sensor modes **normal**, **drift** and **sensor fault**. The sensor biases are `[0, 0.055, 0.14]`, Gaussian noise has standard deviation `0.035`, and residual thresholds are `[0.025, 0.095]`. Twenty independent records of 150 samples (seed 17) supply calibration labels; a separate 600-sample record (seed 2026) supplies evaluation. Supervised transition/emission estimates use a pseudocount of one. A new record resets the initial state distribution; its first sample is not joined to the previous record's last sample.

The transition matrix is `[.97 .025 .005; .04 .93 .03; .02 .08 .9]` and the initial distribution is `[.8 .15 .05]`. The continuous residual is the measured concentration minus the prediction from the known nominal tank and applied input. Conditional independence given the sensor state is an assumption of this calibration experiment. The analytic Gaussian category probabilities are retained as simulation references; supervised inference uses estimates fitted to calibration records. Diagnosis is compared with an instantaneous emission-MAP classifier that uses the fitted stationary prior and the current category alone. The reported alarm metrics include precision, recall and the false-positive rate among non-fault samples.

The PI comparison uses `Kp=2`, `Ki=0.2`, input bounds `[0,1]`, bias `0.35`, conditional-integration anti-windup and reference changes from `0.35` to `0.65` at 10 min, then `0.45` at 75 min. There is no process disturbance. The supervisor subtracts the **filtered** expected sensor bias before the PI update. Smoothing and Viterbi use the whole record and are retrospective diagnostics only. Identical state/noise records drive both policies. The plant time constant is 10 min in the nominal comparison and 14 min in the mismatch comparison, while the predictor remains at 10 min. Mismatch contaminates the residual; bias compensation has no general stability or performance guarantee. Printed classification scores and control metrics describe the simulated records, not an industrial fault detector.

`markov_models(action,...)` uses **one-based** state and symbol indices, unlike Python's zero-based indices. All probability matrices are row-stochastic; an emission at the first sample is generated from the initial state before any transition.

| Action | Arguments after the action | Returned value |
|---|---|---|
| `propagate` | `P, initial, steps` | Row vector `initial * P^steps`; zero steps returns the initial distribution |
| `stationary` | `P` | Unique invariant row distribution; nonunique cases raise an error |
| `hitting` | `P, target_indices` | `[expected_steps, hit_probability]`, both columns; targets have time zero and are stopped at first visit |
| `simulate_chain` | `P, initial, length, optional_seed` | State column |
| `simulate` | `P, B, initial, length, optional_seed` | Structure with `states` and `observations` |
| `filter` / `forward` | `P, B, initial, observations` | `filtered`, per-sample `scales` and total `log_likelihood` |
| `smooth` | `P, B, initial, observations` | Filter results plus `smoothed` and summed posterior `transition_expectations` |
| `viterbi` | `P, B, initial, observations` | Most probable joint `path` and its `log_probability` |
| `supervised` | `state_cells, observation_cells, n_states, n_symbols, optional_pseudocount` | Estimated `transition`, `emission`, `initial` and counts including the pseudocount |
| `baum_welch` | `observation_cells, P0, B0, initial0, optional_iterations, optional_tolerance` | Estimated model and `log_likelihood_history` including the initialization |

Forward/backward calculations use per-sample scaling; Viterbi works in log probabilities. Invalid probabilities and impossible observation records raise errors. Supervised estimation defaults to a pseudocount of one; an explicit zero requests unsmoothed counts and requires every row to be observed. For first hitting times, a nonzero probability of never reaching a target means an infinite unconditional expectation; the separate hit probability reports that distinction. Multiplying steps by the sampling interval converts the result to minutes. The laboratory's absorbing fault model is an explicit modification of the reversible sensor-regime chain, not a claim that sensor faults can never recover.

Baum-Welch maximizes the sum of log likelihoods of the independent observation records. It uses no labels or pseudocount, retains a parameter row if its expected count is zero, and reports the full likelihood history. Convergence uses improvement relative to `max(1, abs(previous_log_likelihood))`; a tiny negative change from roundoff retains the preceding iterate, while a material decrease raises an error. Its likelihood can improve without recovering the physical state names: state permutations, local optima and model mismatch must be considered. Calibration labels give physical names to the supervised model only.

The laboratory's EM demonstration starts from the disclosed simulator transition, emission and initial probabilities, with 30 iterations and relative tolerance `1e-6`. This is a favorable initialization for studying the likelihood updates, not evidence of discovering an unknown physical model from scratch. Neither test labels nor test observations enter its fit. Markov-chain outputs also include mean holding durations and the 50-step (10 min) distribution starting from the normal state. IAE is integrated over time with the trapezoidal rule in both language implementations.

`validate_all()` runs the ninth laboratory and `validate_markov()`. The latter checks chain propagation and stationarity against analytic answers; first hitting times with certain, partial and impossible absorption; filtering, smoothing, transition expectations and Viterbi against exhaustive latent-path enumeration; long-record numerical scaling; independent-record count boundaries; EM likelihood and singleton records; and invalid inputs. The same two-state fixture is used in the Python tests. Random sequences are reproducible within each runtime, but exact MATLAB/Python random samples are not expected to coincide.

## Published benchmark equations

`paper_models(name,x,u,options)` supports the following names:

| Name | Return and units |
|---|---|
| `siso`, `mimo` | Next discrete output, Eqs. (30)-(31); SISO state is `[y(k); y(k-1)]` |
| `pendulum` | Derivative of `[angle; angular velocity; cart position; cart velocity]`, SI |
| `pneumatic` | Derivative of `[position; velocity; pI; pII]`; five explicitly supplied mass flows |
| `hydrostatic` | Literal Eq. (35) transcription; mixed units and angle-gain inconsistencies remain explicit |
| `three_tank` | Levels in m, flows in m3/s; nominal drains closed as in Eq. (36) |
| `bioreactor` | Two-state derivative; `bioreactor_sample` uses the article's 50 Euler steps of 0.01 |
| `cstr` | Concentrations mol/m3, temperatures degrees C, time hours, cooling input MJ/h |
| `column_a`, `column_a_lv` | 82-state balance: 41 compositions followed by 41 holdups, time minutes |
| `wind` | Nine-state tower/blade/drivetrain/pitch model with the separately documented later ROSCO map |

Example:

```matlab
rhs = @(t,x) paper_models('three_tank',x,[0;0]);
[t,h] = ode45(rhs,[0 20],[.4;.2;.3]);
dx = paper_models('cstr',[3517.5;740;87;79.8],[8.256;-6.239]);
```

For pneumatic pressure, the default printed gas constant `8.314` is dimensionally questionable with kg/s mass flows; `options.gas_constant=287.05` explicitly chooses a specific-air variant. Valve equations are not supplied by the article. Hydrostatic results are transcriptions, not validated SI predictions. CSTR cooling is converted from MJ/h to kJ/h. The column balances correct the vapor inflow index in Eq. (47) and use NTNU nominal flow precision. The wind map is read without extrapolation. These qualifications match the Python implementation and [benchmark documentation](../benchmarks/README.md).

The Tennessee Eastman simulator and industrial laboratory datasets remain external, provenance-controlled cases; they are not replaced by synthetic plants. No local MATLAB/Simulink execution is claimed. See the repository validation record for actual Octave execution status.

The previous eight-unit version passed `validate_all` and `validate_paper` with GNU Octave 11.1.0 on published source commit `c8a9a6f`: [verified CI job](https://github.com/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/actions/runs/41849137529/job/126640403549). That run includes the original eight units and ten mathematical benchmark checks; it predates the ninth laboratory. See the repository validation record for the current run.

`local_arx_fit` and `local_arx_predict` also implement the eight-local-model PWA/TS architecture discussed for the throttle in section 4.1. Their standardized partition features are output change and previous input, fitted on training records only. Crisp nearest-center and inverse-distance soft partitions are explicit teaching choices. The validation checks both on an unseen linear synthetic experiment; it does not claim the unavailable published throttle measurements or fitted partition parameters were reproduced.

`[t,u,y]=load_io_csv(path,{'input_name'},{'output_name'},sample_time)` imports externally supplied records with named channels and preserves the requested column order and row alignment. Time starts at zero and advances by the declared positive finite sample interval. The supported subset is an unquoted comma-separated header followed by at least two equal-width rows of finite real decimal/scientific-notation values. Duplicate or missing names, overlapping/duplicate channel selections, empty fields, blank/comment rows, quoted fields and nonnumeric values are rejected, including malformed unselected columns. No samples are dropped, imputed or resampled. A source manifest must separately identify provenance, units, sample time and training/test split; successful import is not source validation. `validate_io_csv` checks alignment and malformed records with explicitly labeled temporary test fixtures.

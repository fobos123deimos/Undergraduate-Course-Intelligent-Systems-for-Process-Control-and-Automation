# MATLAB and GNU Octave laboratories

The eight units run without add-on toolboxes. The implementation includes its own box-constrained quadratic MPC solver, fuzzy inference, neural training and genetic search. Run from the repository root:

```matlab
addpath('matlab');
results = validate_all();
checks = validate_paper();
run_lesson(8, true);
```

For GNU Octave, use `octave --no-gui --quiet --eval "addpath('matlab'); validate_all(); validate_paper();"`.

| Unit | Executable work |
|---|---|
| 01 | Exact sampled concentration balance, ARX least squares, independent input validation and physical Blending Tank equilibrium |
| 02 | IMC-tuned PI, filtered-derivative PID, anti-windup and sampled closed-loop eigenvalues |
| 03 | Relative gain array, static decoupler, measured-disturbance feedforward and fast actuator cascade |
| 04 | Constrained SISO and 2x2 MIMO MPC with prediction and control horizons and move penalties |
| 05 | Diagnostic rules, Sugeno and Mamdani inference, incremental fuzzy control and fuzzy PI gain scheduling |
| 06 | Perceptron, trained tanh MLP, regularized RBF, one-dimensional self-organizing map and neural forward-model inversion |
| 07 | Real and binary genetic search with tournament selection, crossover, mutation and elitism; a counted 12-evaluation genetic MIMO move-penalty search and a deterministic sweep |
| 08 | Common-scenario PI/feedforward/fuzzy/MPC comparison with IAE, ISE, input variation and a plant-mismatch experiment |

The shared teaching plant is `10 dc/dt = u + d - c`: a 100 L well-mixed vessel with 10 L/min flow, normalized feed composition, `0 <= u <= 1`, sampling interval 0.2 min and 80 min horizon. The initial concentration is 0.35. References are 0.35, 0.65 at 10 min and 0.45 at 55 min. A concentration disturbance of +0.08 begins at 45 min. These are illustrative parameters, separate from both the historical physical Blending Tank and the article's benchmarks. All inputs, outputs and training samples are simulated.

The MPC uses full-state feedback, constant future reference/disturbance estimates and input box constraints. It does not claim terminal-set stability, state constraint satisfaction or robust feasibility. Each move is a projected-gradient solution with a numerical tolerance and iteration limit. The MIMO exercise uses a separate 2x2 discrete model; it is not a multivariable model of the one-state vessel. Unit 07 includes a small evolutionary search over the MIMO move weight, plus an explicitly separate deterministic sweep; neither establishes a global optimum.

Neural validation samples are separate from training samples. Random streams and optimization details can differ between Python and MATLAB/Octave; numerical equality of trained weights is not expected. Unit 06's learned forward-model inversion is an illustrative nonlinear extension and its unconstrained generalization outside the training domain is not certified. A SOM is unsupervised and is not evaluated using classification labels.

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

GNU Octave 11.1.0 passed `validate_all` and `validate_paper` on the published source commit `c8a9a6f`: [verified CI job](https://github.com/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/actions/runs/41849137529/job/126640403549). This includes all eight units and ten mathematical benchmark checks.

`local_arx_fit` and `local_arx_predict` also implement the eight-local-model PWA/TS architecture discussed for the throttle in section 4.1. Their standardized partition features are output change and previous input, fitted on training records only. Crisp nearest-center and inverse-distance soft partitions are explicit teaching choices. The validation checks both on an unseen linear synthetic experiment; it does not claim the unavailable published throttle measurements or fitted partition parameters were reproduced.

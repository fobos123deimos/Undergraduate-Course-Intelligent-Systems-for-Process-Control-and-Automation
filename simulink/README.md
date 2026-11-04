# Simulink models and numerical validation

The builders create **25 models** from inspectable MATLAB source. They cover all ten implemented article equation cores, the physical tank, PI/MPC, fuzzy PID, neural RBF control, scheduled wind LQR/PDC, Markov occupancy, HMM diagnosis and four causal sensor-supervision experiments. Creating a diagram and executing it are separate operations; the [validation record](../docs/VALIDATION.md) identifies the source commit and runtime actually exercised.

From the repository root in MATLAB with Simulink:

```matlab
addpath('matlab'); addpath('simulink');
report = validate_simulink_suite('simulink/generated');
```

The command builds, simulates and checks the models, then writes `simulink/generated/validation.json`. Each model is saved as `.slx` with a viewable PNG. Output folders must be new: existing files and loaded models are refused rather than silently replaced. Individual builders accept `overwrite=true` when replacement is intentional. Generated models require the MATLAB and Simulink adapter source folders on the MATLAB path.

## Model inventory

| Builder | Models | Evidence collected by the suite |
|---|---|---|
| `build_models` | Nine continuous plants: physical blending tank, pendulum, three tanks, biochemical reactor, CSTR, Column A, pneumatic actuator, hydrostatic transmission and reduced wind turbine; PI and MIMO MPC loops | Plant traces compared with MATLAB ODE integration at the logged times; PI/MPC finite-state and final-tracking checks |
| `build_discrete_models` | Artificial SISO and MIMO recurrences; sampled biochemical reactor | Complete trace comparison with the direct recurrence, including the bioreactor's 50 Euler substeps per control sample |
| `build_markov_models` | Markov occupancy, categorical HMM diagnosis, nominal PI, nominal HMM-supervised PI, mismatched PI and mismatched HMM-supervised PI | Exact chain propagation, batch filtering and independent native control-loop references |
| `build_intelligent_models` | Fuzzy PID with applied-input anti-windup; trained RBF forward-model inversion on the nonlinear teaching plant | State and actuator traces matched to independent Unit 05/06 loops; active derivative action checked |
| `build_wind_pdc_model` | Scheduled LQR/PDC and held-command nonlinear wind model | Full state/command traces compared with native RK4 study; torque/pitch magnitude and rate limits checked |
| `build_blending_tank` | Physical nonlinear tank and matched nonlinear/state-space/transfer comparison | Analytical startup/filling and linear response, transfer consistency, input ordering and invalid-volume rejection |

The short plant experiments are specified in [paper_simulink_cases.m](paper_simulink_cases.m). These cases validate the adapters, state ordering and integration; they do not reproduce every industrial control protocol or published score. The original article equation checks remain in [validate_paper.m](../matlab/validate_paper.m).

The pneumatic fixture supplies five mass flows directly and explicitly chooses `R=287.05 J/(kg K)` and `kappa=1.4`; a voltage-driven valve model remains a separate closure. The hydrostatic fixture evaluates the documented mixed-unit transcription and does not establish corrected SI scaling. The wind fixture uses the declared later ROSCO rotor map. Short positive-velocity pendulum/pneumatic fixtures avoid interpreting a discontinuous Coulomb-friction approximation as a stiction model. Source boundaries remain in the [benchmark inventory](../benchmarks/README.md).

## Markov and HMM diagrams

The six models use the same separate calibration/test records as [Unit 09](../laboratories/09-markov-hidden-state-diagnosis/README.md), at a 0.2 min sample period:

1. `si_markov_occupancy`: discrete probability propagation `p(k+1)=p(k)P`, starting with the initial distribution before the first transition.
2. `si_hmm_diagnosis`: held categorical observations enter a streaming filter. Its discrete state is the **prior before the current observation**; the current posterior is output before the transition produces the next prior.
3. `si_hmm_nominal_baseline`: noisy/bias-corrupted sensor and ordinary PI on the nominal tank.
4. `si_hmm_nominal_supervisor`: the same sensor record, with the filtered expected bias subtracted before the PI update.
5. `si_hmm_mismatch_baseline`: ordinary PI with the plant time constant changed from 10 to 14 min.
6. `si_hmm_mismatch_supervisor`: the same mismatched plant and sensor record; the nominal predictor remains at 10 min.

The online controller has only two external inputs: reference and measured concentration. It never receives the hidden sensor label, true concentration, smoothing result or Viterbi path. Its internal predictor advances with the applied actuator command. Smoothing, Viterbi and parameter estimation remain offline MATLAB laboratory operations. This separates causal supervision from retrospective diagnosis.

`hmm_pi_sfun` calls [hmm_pi_step.m](../matlab/hmm_pi_step.m); `hmm_filter_sfun` calls [hmm_filter_step.m](../matlab/hmm_filter_step.m). [validate_online_hmm.m](../matlab/validate_online_hmm.m) tests these streaming interfaces without Simulink and compares all four control policies against the independent loop in `run_markov_lab`. [validate_markov_simulink.m](validate_markov_simulink.m) then checks the actual diagram outputs against the same reference records. A state/time alignment error therefore cannot be hidden by testing only final accuracy.

## Fuzzy and neural control diagrams

`si_fuzzy_pid_tank` exposes the reference, measurement, scheduled PID, actuator command, inlet disturbance and sampled plant as connected blocks. Its controller logs Kp, Ki, Kd and the derivative contribution. The reference changes at 10 and 55 min; an inlet disturbance begins at 45 min.

`si_neural_rbf_tank` uses the RBF model trained independently in Unit 06. The controller inverts its prediction by a bounded 24-step bisection. Its plant is the explicit synthetic extension `x_next=a*x+(1-a)*u+.015*sin(3*x)*u`, not an additional physical model attributed to the article. Training occurs before simulation; the diagram does not train on its evaluation trajectory. The initial state is zero, matching Unit 06. The monotonic-inversion assumption and out-of-domain limitations remain material.

[validate_intelligent_adapters.m](../matlab/validate_intelligent_adapters.m) checks both streaming policies without Simulink. [validate_intelligent_simulink.m](validate_intelligent_simulink.m) compares the actual diagrams with the independently written lesson loops. Control comparisons use the first N-1 applied commands because the numerical lessons store their last command differently.

## Scheduled wind control

The separate `si_wind_pdc` diagram uses measured full regulation state and current wind speed to interpolate local LQR laws. The actuator command is held over each 0.02 s RK4 interval, with magnitude and slew limits. It uses newly designed gains and the declared later rotor map, so agreement with the native study establishes adapter equivalence, not recovery of the article's fitted controller. [validate_wind_pdc_simulink.m](validate_wind_pdc_simulink.m) checks every state and applied command against `run_wind_control`.

## Physical tank

The [physical tank](../blending-tank/README.md) has state `[X,V]`, input `[w1,w2,x1,x2,wout]`, density 1000 kg/m3, mass flows in kg/min and time in min. Its comparison model uses input/state deviations and restores output offsets. All matrices and transfer coefficients come from `bt_linearize`; the Level-2 `bt_sfun` calls the conservation-law function `bt_rhs`.

```matlab
paths = build_blending_tank('simulink/generated/tank-only');
report = validate_blending_simulink('simulink/generated/tank-check');
```

## Runtime requirements

MATLAB with Simulink is required for model building and execution. No Control System Toolbox is required for these diagrams. GNU Octave can execute the numerical Markov/HMM and plant functions, but it cannot run `.slx` diagrams.

PNG export additionally requires a display. The Linux workflow starts an Xvfb virtual display before MATLAB, following the [official MATLAB Actions recipe](https://github.com/matlab-actions/.github#use-virtual-display-on-linux-runner). Model simulation alone can run without a display; Simulink printing cannot run in `-nodisplay` mode. The validation routine opens each model for export and closes it afterward.

For public GitHub projects, the official [Setup MATLAB action](https://github.com/matlab-actions/setup-matlab#licensing) documents automatic product licensing when used with its companion run actions. The repository workflow requests MATLAB and Simulink and preserves the generated diagrams and validation report as artifacts. Runtime success must still be checked for the specific workflow run; availability of the action is not execution evidence.

Interface references: [MATLAB S-functions](https://www.mathworks.com/help/simulink/sfg/writing-level-2-matlab-s-functions.html), [Discrete State-Space block](https://www.mathworks.com/help/simulink/slref/discretestatespace.html), [From Workspace block](https://www.mathworks.com/help/simulink/slref/fromworkspace.html) and [Transfer Fcn block](https://www.mathworks.com/help/simulink/slref/transferfcn.html).

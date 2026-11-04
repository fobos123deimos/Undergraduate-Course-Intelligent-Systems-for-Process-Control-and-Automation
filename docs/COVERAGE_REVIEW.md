# Syllabus, article and language coverage review

Review date: 4 November 2026. The review compares the supplied four-page integrated syllabus, the complete Kroll-Schulte article and the executable sources. It distinguishes a topic discussed in a lesson, an implemented model, a tested numerical property and a reproduced benchmark experiment.

**Finding:** all eight syllabus areas and the Markov/HMM extension have lessons, worked problems and Python plus MATLAB/Octave implementations. All thirteen article benchmark sections have an inventory and study protocol; ten mathematical model cores have implementations in both languages. Complete canonical reproduction of every article benchmark, identical experiments in both languages and coverage of every topic in Simulink are **not established**.

## Reference and scope

The language reference is [Control of Dynamical Systems at commit 6c41788](https://github.com/fobos123deimos/Undergraduate-Course-Control-of-Dynamical-Systems/tree/6c41788cf80625d1c947061977329e9f412dfeff). Its complete tree and Python, MATLAB and Simulink guides were inspected. The supplied syllabus is a non-official study synthesis; this review assesses that document rather than asserting an official teaching plan.

Source identities, without redistributing the PDFs:

| Source | SHA-256 |
|---|---|
| Integrated syllabus and complete bibliography, 4 pages | `a8c460046acf65c81fc3dec8d37efb6a7c81eaa2dfb124081843117a58d92361` |
| Kroll and Schulte, Applied Soft Computing 25 (2014), 496-513, DOI 10.1016/j.asoc.2014.08.034 | `bb2a94516c7a48a889c4f2caa5625e4c2d7c5cc31f798c4180bfc20539d4f05e` |

The code review began at source commit `00f3c04`. The corrections below are covered by the subsequent validation run identified in [execution evidence](VALIDATION.md). No result from a proprietary runtime is inferred from source inspection.

## Languages and deliverable formats

| Layer | Control reference | This collection | Boundary |
|---|---|---|---|
| Python | Scientific programs | Nine course labs, benchmark kernels, physical tank | Executed and numerically tested |
| Jupyter / Colab | Twelve notebooks | Nine course notebooks, one benchmark notebook, one physical-tank notebook | Jupyter execution is recorded; a Colab link is not proof of a Colab execution |
| MATLAB / GNU Octave | Portable numerical labs | Nine units, benchmark kernels, physical tank, Markov/HMM | GNU Octave execution is recorded; proprietary MATLAB execution is not |
| LaTeX / TikZ | Notes, problems, solutions, figures | Notes, 45 problems and solutions, diagrams | Authored and rendered documents, not simulation languages |
| Simulink | Generator for six nominal cases | Eight general model generators plus two dedicated physical-tank models | Source only; subset of topics; no generated model or completed simulation claimed |

No Julia, R or C++ teaching track was found in the reference tree. The two repositories use the same language stack. That does not imply that every model has a Simulink counterpart. In particular, there is no Markov/HMM Simulink diagram.

## Eight syllabus areas

Every row has a [lesson](../course/README.md), five [worked problems](../problem-sets/README.md), a [notebook](../README.md#nine-connected-laboratories), a Python experiment in [experiments.py](../python/intelligent_control/experiments.py) and a case in [run_lesson.m](../matlab/run_lesson.m). This is evidence of teaching coverage, not a claim of identical solver choices or numerical results.

| Area | Subtopics checked against the syllabus | Executable evidence and limits |
|---|---|---|
| 01. Modeling, identification and simulation | Physical and empirical models; states, inputs and disturbances; ODEs and transfer functions; parameter estimation; simulation and independent validation | Sampled mixing balance, ARX least squares and held-out excitation in both languages. The separate physical tank supplies conservation equations, Jacobians, state-space and transfer channels. |
| 02. Feedback, stability and tuning | Open/closed loop; transient and steady behavior; PI/PID; IMC; stability and tracking/disturbance/robustness compromises | PI/PID, anti-windup, sampled poles and IMC-based choices in both languages. Stability checks apply to the stated nominal model. |
| 03. Control structures | Multiloop and multivariable interaction; RGA and decoupling; feedforward; cascade; measurement requirements | Both languages execute feedforward/cascade and dynamic decentralized-versus-decoupled two-output comparisons. Static decoupling is not confused with removing all dynamic interaction. |
| 04. MPC | Prediction/control horizons; objective; constraints; receding horizon; SISO/MIMO | Both languages execute constrained SISO and MIMO MPC. Python also demonstrates move bounds and a MIMO output constraint; MATLAB/Octave uses input box constraints. Simulink has a MIMO MPC builder, awaiting runtime validation. |
| 05. Expert and fuzzy systems | IF-THEN diagnosis; memberships and linguistic sets; fuzzification, inference, defuzzification; fuzzy and fuzzy PID control | Diagnostic rules, Sugeno/Mamdani examples and control comparisons in both languages. MATLAB now schedules Kp, Ki and Kd, with a matched zero-derivative fuzzy PI comparison. |
| 06. Neural modeling and control | Perceptron, MLP, RBF, SOM; training; nonlinear identification; control; validation and generalization | Both languages train models, use independent one-step validation and implement neural-model control. Python additionally executes recursive free-run and out-of-domain comparisons; those numerical experiments are not duplicated in MATLAB. |
| 07. Evolutionary optimization | Representation, population, fitness, selection, crossover, mutation; binary/real coding; parameter/controller and MIMO MPC tuning; computational cost | Both languages implement binary/real genetic searches, controller tuning and a counted small MIMO MPC tuning search. Search budgets differ and neither demonstrates a global optimum. |
| 08. Integration and communication | Modeling, identification, controller comparison; model-based and intelligent methods; disturbances, uncertainty, metrics, reporting and presentation | Common-scenario comparisons, saved Python traces/metrics and worked evidence/reporting tasks. Model mismatch and information advantages are explicit. Presentation is a learning activity; a finished slide deck is not part of this collection. |

The three proposed integrated practices are covered by Units 01-02 (model and baseline), 03-04 (structures and MPC), and 05-08 (intelligent technique and comparison). The [course bibliography](../course/REFERENCES.md) preserves the supplied basic and complementary references. The 64-hour core and 8-hour extension are suggested study allocations.

## Markov and hidden Markov extension

The [ninth laboratory](../laboratories/09-markov-hidden-state-diagnosis/README.md) is an additional requested topic, separate from the eight-area syllabus and the article model inventory.

| Capability | Python | MATLAB/Octave |
|---|---|---|
| Finite-horizon propagation, stationary probabilities, holding durations, first-hitting probabilities and times | [markov.py](../python/intelligent_control/markov.py) | [markov_models.m](../matlab/markov_models.m) |
| Scaled forward filtering, backward smoothing, posterior transition counts and log-domain Viterbi | Same module | Same module |
| Supervised counts and Baum-Welch over separate trajectories | Same module | Same module |
| Independent calibration/test records; fault alarms; causal sensor-bias compensation; model mismatch | [markov_lab.py](../python/intelligent_control/markov_lab.py) | [run_markov_lab.m](../matlab/run_markov_lab.m) |
| Independent path enumeration, analytic first passage, long records, impossible observations, sequence boundaries, likelihood and causal-information checks | [43 numerical checks](../tests/test_markov.py) and [lab tests](../tests/test_markov_lab.py) | [Seven check groups](../matlab/validate_markov.m), including the same small exact HMM fixture |

Filtering alone enters the controller; smoothing and Viterbi remain retrospective. Both languages use the same model probabilities and experiment parameters. Their random streams and report fields differ. Python saves more diagnostic figures and confusion-matrix data; MATLAB reports some additional probability and scoring summaries. None of these synthetic experiments establishes industrial reliability.

## Article model inventory

The detailed source corrections and assumptions remain in the [benchmark guide](../benchmarks/README.md). Python kernels live in [benchmarks.py](../python/intelligent_control/benchmarks.py); MATLAB kernels live in [paper_models.m](../matlab/paper_models.m).

| Article section / model | Implemented in Python and MATLAB/Octave | What remains outside the validated result |
|---|---|---|
| 3.1, artificial SISO, Eq. (30) | Exact recurrence | Current run is a short demonstration, not the full 100000-sample identification study |
| 3.1, artificial MIMO, Eq. (31) | Exact recurrence | Same training-length/experiment boundary |
| 3.2, data repositories | [Dataset inventory](../benchmarks/DATASETS.md); Python CSV import workflow | Not a physical model; historical datasets and their fitted results are not all included; no equivalent MATLAB dataset importer |
| 3.3, inverted pendulum | Nonlinear state equations and limits | Local open-loop demonstration; no complete swing-up/rail-impact/stiction reproduction |
| 3.4 and 4.1, throttle | Eight-local-model crisp PWA and soft TS teaching predictors; MATLAB [fit](../matlab/local_arx_fit.m) and [predict](../matlab/local_arx_predict.m) | Measured records and the article's fitted partitions/coefficients absent; no published test score reproduced |
| 3.5, pneumatic actuator | Chamber and mechanical balances | Paper omits valve mass-flow closure; practice valve law and gas-constant choice are explicit variants |
| 3.6, hydrostatic drive | Literal differential-equation transcription | Published unit/scaling inconsistencies unresolved; physical vehicle simulation not validated |
| 3.7, three tanks | Nominal closed-drain balances and declared drain extension | General conservation verified; complete fault/control challenge not reproduced |
| 3.8, biochemical reactor | Continuous model and 50 Euler substeps per sensor period | Short synthetic experiment; all robustness/control comparisons are not executed |
| 3.9, CSTR | Four-state balances and operating-point parameters | Full observer-based SP1-to-SP2 experiment and its metrics are not reproduced |
| 3.10, Column A | 82-state balance and LV wrapper | Other named configurations and full published controller comparisons are design extensions |
| 3.11, ALSTOM gasifier | Protocol and external source route | Official challenge package and runtime results absent; no substitute plant |
| 3.12, reduced wind turbine | Nine-state mechanical/pitch model | Uses declared 2022 ROSCO map; original map/results and optional reduced-order/second-order pitch variants not reproduced |
| 3.12, FAST aeroelastic turbine | External run protocol/interface | Complete version-pinned simulator, turbine, controller and wind case not executed |
| 3.13, Tennessee Eastman | Verified official source retrieval and [MATLAB launcher](../benchmarks/run_te_reference.m) | Original 50-state and revised 52-state versions remain distinct; simulator execution unverified |
| 4.2, wind TS/PDC controller example | [Worked architecture discussion](../benchmarks/CASE_STUDIES.md#12-reduced-and-aeroelastic-wind-turbines-312) | No implemented LQR gain schedule or reproduced Tables 11-12; article does not supply a complete set of gains/memberships |

The **ten mathematical cores** are SISO, MIMO, pendulum, pneumatic, hydrostatic, three tanks, bioreactor, CSTR, Column A and reduced wind. LV and sampled bioreactor are variants of existing families, not extra cores. The thirteen-section count refers to Sections 3.1-3.13, not thirteen fully reproduced industrial simulations.

## Corrections made by this review

1. MATLAB Unit 05 previously used the name `fuzzy_pid` for a controller that changed proportional/integral gains only. It now schedules a nonzero filtered derivative term. A matched fuzzy PI comparison and validation assertions demonstrate that derivative action actually enters the applied control.
2. MATLAB Unit 03 previously stopped its multiloop comparison at a static RGA/decoupler. It now simulates both control structures on the same two-output plant, reference and actuator bounds, with anti-windup based on the applied input. Checks include equilibrium commands and final tracking.
3. Runtime-specific MPC limitations are stated separately. The bounded MATLAB/Octave iteration does not provide the Python solver-failure fallback or its additional move/output constraints.
4. The wind TS/PDC example and named variants are explicitly accounted for; a description of an architecture is not counted as an executed controller.

## Validation and open requirements

The local review reran all **115 Python tests**, the Markdown navigation check and structural validation of all **eleven notebooks**. The targeted Markov/HMM review independently reran its 43 checks. The updated MATLAB source requires the new Octave CI result recorded in [VALIDATION.md](VALIDATION.md); earlier successful runs do not validate changed code.

Completion of full canonical article reproduction still requires recovered throttle measurements, the ALSTOM challenge distribution, versioned FAST inputs and runtime, Tennessee Eastman runtime execution, resolution of pneumatic/hydrostatic source ambiguities, and the defined full controller/observer experiments. Full Simulink coverage and proprietary-runtime validation are separate remaining work. These are substantive limits, not missing titles in the topic index.

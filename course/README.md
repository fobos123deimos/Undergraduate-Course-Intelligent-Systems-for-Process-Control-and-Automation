# Course guide and prerequisite map

[Course notes (PDF)](notes.pdf) · [Editable LaTeX](notes.tex) · [Problem sets](../problem-sets/README.md) · [Bibliography](REFERENCES.md)

This original English study collection follows the eight content areas of the supplied integrated syllabus and adds a ninth unit on Markov chains and hidden-state diagnosis. Unit 09 is an extension, not a model attributed to the benchmark article or an additional topic claimed for the official syllabus. The supplied syllabus itself is a non-official synthesis. Academic context: the discipline associated with Prof. Michela Mulas; no authorship, review or endorsement by the professor is implied.

The worked tank is hypothetical: volume 100 L, flow 10 L/min, normalized high/low feed concentrations 1 and 0, and blend fraction between 0 and 1. These explicit teaching parameters illustrate the derivations; the article's named benchmarks are studied separately.

## Learning sequence

| Unit | Topic | Entry knowledge | Computation |
|---|---|---|---|
| 01 | [Modeling, identification and simulation](01-modeling-identification/lesson.md) | Differential equations, units, matrix least squares and elementary probability. | [Notebook](../laboratories/01-modeling-identification/notebook.ipynb) |
| 02 | [Feedback, stability and IMC tuning](02-feedback-imc/lesson.md) | Unit 01; Laplace transforms, characteristic polynomials and negative feedback. | [Notebook](../laboratories/02-feedback-imc/notebook.ipynb) |
| 03 | [Multiloop, multivariable, feedforward and cascade control](03-control-structures/lesson.md) | Units 01-02; matrix inversion and local transfer functions. | [Notebook](../laboratories/03-control-structures/notebook.ipynb) |
| 04 | [Constrained model predictive control](04-model-predictive-control/lesson.md) | Units 01-03; quadratic forms, least squares and constrained optimization. | [Notebook](../laboratories/04-model-predictive-control/notebook.ipynb) |
| 05 | [Knowledge-based supervision and fuzzy control](05-expert-fuzzy-control/lesson.md) | Units 01-03; sets, piecewise functions and numerical integration. | [Notebook](../laboratories/05-expert-fuzzy-control/notebook.ipynb) |
| 06 | [Neural modeling and control of dynamic systems](06-neural-identification-control/lesson.md) | Units 01, 02 and 04; differentiation, gradients, least squares and separation of training, validation and test data. | [Notebook](../laboratories/06-neural-identification-control/notebook.ipynb) |
| 07 | [Evolutionary optimization and controller tuning](07-evolutionary-tuning/lesson.md) | Units 02, 04 and 06; random sampling, objective functions and constrained experiment design. | [Notebook](../laboratories/07-evolutionary-tuning/notebook.ipynb) |
| 08 | [Integration, benchmark evidence and technical communication](08-integrated-validation/lesson.md) | Units 01-07; interpretation of numerical experiments and model limitations. | [Notebook](../laboratories/08-integrated-validation/notebook.ipynb) |
| 09 | [Markov chains and hidden-state diagnosis](09-markov-hidden-state-diagnosis/lesson.md) | Units 01, 02 and 08; conditional probability, matrix multiplication and elementary statistics. | [Notebook](../laboratories/09-markov-hidden-state-diagnosis/notebook.ipynb) |

## Suggested use of 64 core study hours and an 8-hour extension

Allocate eight hours to each unit: two for the lesson and derivations, two for computational exploration, three for the five integrated problems, and one for comparison and reflection. The eight core units total 64 hours; the Markov/HMM extension adds eight hours for a suggested total of 72. This is a study allocation, not an official timetable or assessment policy. Additional time may be required for prerequisite review and external industrial simulators.

Complete Units 01-04 in order. Unit 05 needs 01-03; Unit 06 needs 01, 02 and 04; Unit 07 builds on 02, 04 and 06. Unit 08 integrates the eight core units. Unit 09 builds on 01, 02 and 08, plus conditional probability and matrix multiplication. Each problem has linked subparts that move from a quantitative model to an implementation or evidence decision.

## Four connected practical blocks

1. **Model and establish a baseline (01-02):** derive balances, identify and validate a process model, then compare PI/PID and IMC-based tuning with actuator limits.
2. **Compare structures and predictions (03-04):** examine measured-disturbance feedforward, inner flow cascade, multivariable interaction and constrained MPC using a common experiment contract.
3. **Add and evaluate intelligence (05-08):** use expert rules, fuzzy control, neural identification/control and evolutionary tuning for a stated deficiency, then evaluate the improvement on held-out conditions.
4. **Diagnose uncertain operating regimes (09, extension):** calculate Markov occupancy and absorption, estimate categorical HMMs from separate trajectories, distinguish filtering from offline inference, and evaluate sensor-bias supervision under plant mismatch.

## Readiness checks

Before advancing, explain the input/output units, the state and operating point, and one physical limit. Derive one numerical prediction before running code. Distinguish a fitted trajectory from independent validation, a source equation from an educational closure, and a passing simulation from a stability proof.

Read the benchmark inventory alongside the article. The teaching tank is an integrative case, not a substitute for the pendulum, throttle, pneumatic, hydrostatic, reactor, distillation, gasifier, wind and Tennessee Eastman examples. External data/maps and reference simulators remain part of the identity of those benchmarks.

## Rebuild the text editions

Run `python course/build_documents.py` to regenerate the Markdown and LaTeX files from `course/content.py`. Compile `course/notes.tex`, `problem-sets/exercises.tex` and `problem-sets/solutions.tex` from their own directories. The physical and architecture figures are editable TikZ sources in `course/figures/`.

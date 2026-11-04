# Unit 08 - Integration, benchmark evidence and technical communication

[Lesson](../../course/08-integrated-validation/lesson.md) · [Worked solutions](solutions.md)

State units, assumptions and initial conditions before calculating. For computational extensions, report the actual experiment and its limitations.

## Problem 08.1 - Design an integrated Blending Tank study

Prepare a comparison of IMC-PI, feedforward PI, constrained MPC and one fuzzy or neural method on the hypothetical tank. (a) Define a common reference/disturbance protocol with a training period and a separate final test. (b) State the measurements each controller receives and how to disclose additional information. (c) Specify six reported outcomes and the minimum evidence required to reproduce them.

## Problem 08.2 - A biased model can have perfect VAF

Measured targets are $y=[0,1,2,3]$ and a model predicts $\hat y=y+0.5$. (a) Compute RMSE, VAF and $R^2$ using population variances and the standard definitions. (b) Explain why the metrics disagree. (c) Propose an additional validation check and explain what to report for a constant-output test record.

## Problem 08.3 - Distinguish reproduction from a teaching model

Consider three submissions: A implements the article's specified artificial recurrence with matching input/initial conditions; B simulates a wind rotor with an invented constant torque coefficient; C runs an official Tennessee Eastman implementation with a documented disturbance schedule. (a) Classify what each can support. (b) List metadata needed before comparing A or C with published scores. (c) Explain how B can still be useful without overstating its identity.

## Problem 08.4 - Cross-language agreement has several levels

Python and Octave simulations differ by $10^{-7}$ in concentration but by 0.02 in a threshold-based settling time. MATLAB/Simulink has not yet run. (a) Explain a plausible cause of the settling difference. (b) Propose numerical and behavioral cross-language checks. (c) Write an accurate validation statement.

## Problem 08.5 - Make a defensible recommendation from mixed results

In a fixed synthetic test family, a tuned controller reduces median IAE by 12% but increases input variation by 40%, misses two deadlines in 1,000 samples, and was tested at only one residence time. (a) State a supported conclusion. (b) Identify which additional experiments address generalization, timing and actuator wear. (c) Give a report outline that makes both the benefit and limitations inspectable.

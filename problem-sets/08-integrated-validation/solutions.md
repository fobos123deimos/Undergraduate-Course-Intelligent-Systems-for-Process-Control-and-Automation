# Unit 08 - Integration, benchmark evidence and technical communication

[Exercises](exercises.md) · [Lesson](../../course/08-integrated-validation/lesson.md)

These worked answers use the explicitly hypothetical problem data. Design questions may admit other defensible solutions if their assumptions and evidence are stated.

## Problem 08.1 - Design an integrated Blending Tank study

(a) One valid protocol starts all runs at $c=u=0.4$, uses one-minute sampling and a 120-minute horizon, with reference 0.4 until 20 min, 0.6 until 70 min, then 0.3. Tune on this schedule with a low-feed disturbance of 0.1 at 50 min; freeze designs, then test a new schedule with step times 15/65 min and disturbance 0.15 at 45 min, plus a declared changed residence time. Keep the exact schedule in configuration. (b) All controllers receive concentration and the previous applied input. Feedforward additionally receives measured inlet composition; this information advantage must be explicit. Use the same sensor noise and delay for shared channels. (c) Report IAE, peak error, settling rule/result, input variation, saturation duration and violations/fallbacks. Save parameters, seeds, initial states, numerical settings, applied input and output trajectories, plus the executable command producing the report. These are designed experiments, not claimed outcomes.

## Problem 08.2 - A biased model can have perfect VAF

(a) Every residual is -0.5, so RMSE is 0.5. Residual variance is zero and target variance is 1.25, giving VAF 100%. Residual SSE is 1 while the target centered sum of squares is 5, so $R^2=0.8$. (b) VAF removes the residual mean; it measures unexplained variation while ignoring a constant bias. $R^2$ retains that bias in SSE. (c) Report mean residual and maximum absolute error, and inspect residual versus operating point. For constant target data the variance denominator is zero: VAF and standard $R^2$ are undefined. Report that status and absolute metrics instead of silently setting either score to 0 or 100%.

## Problem 08.3 - Distinguish reproduction from a teaching model

(a) A is an equation-based reproduction candidate, subject to matching conventions and numerical checks. B is an educational wind-rotor approximation, not a reproduction of the full wind benchmark. C is a reference-simulator experiment, subject to version, controller and protocol matching. (b) Record model/source version, parameters, units, initial state, sampling, inputs/disturbances, noise, data split, controller information, metric formula and failure policy. Match these before comparing scores. (c) B can demonstrate inertia, aerodynamic/mechanical power balance and sensitivity to a chosen coefficient. Name and document the approximation, identify the missing map and restrict conclusions to its simplified dynamics. Do not use the benchmark name alone as evidence of comparability.

## Problem 08.4 - Cross-language agreement has several levels

(a) A trajectory near the settling-band boundary can cross it at adjacent samples after tiny floating-point differences; a threshold statistic is discontinuous even when trajectories agree closely. Different sample indexing or dwell conventions can also cause larger differences and should be checked. (b) Compare equilibria, one-step transitions, dimensions, units, applied bounds, maximum absolute trajectory error and identical sampling/metric logic. Include a case comfortably away from threshold boundaries and a case intentionally near them. (c) An accurate statement is: Python and Octave passed the specified trajectory and constraint checks; a boundary-sensitive settling statistic differed under the recorded convention; MATLAB/Simulink execution remains unverified. Do not turn source availability into a runtime claim.

## Problem 08.5 - Make a defensible recommendation from mixed results

(a) The controller improved median tracking error on the declared synthetic cases, with higher actuator movement and observed deadline misses. The evidence does not establish overall superiority or robustness to residence-time variation. (b) Test held-out reference/disturbance schedules and a justified range of plant parameters; measure solve time under realistic computational load and exercise the fallback; evaluate valve rate limits and a relevant wear/energy model rather than treating variation alone as a complete wear prediction. (c) Organize the report as requirements and physical model; baseline/alternative derivations; common experiment contract; tracking and effort trajectories; per-run metrics and failures; sensitivity/uncertainty results; execution record; limitations and the next decision. The recommendation should reflect the actual priorities and admissible deadline policy.

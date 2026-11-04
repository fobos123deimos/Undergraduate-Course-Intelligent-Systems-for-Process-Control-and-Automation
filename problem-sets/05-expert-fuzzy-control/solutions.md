# Unit 05 - Knowledge-based supervision and fuzzy control

[Exercises](exercises.md) · [Lesson](../../course/05-expert-fuzzy-control/lesson.md)

These worked answers use the explicitly hypothetical problem data. Design questions may admit other defensible solutions if their assumptions and evidence are stated.

## Problem 05.1 - Diagnose a symptom without overclaiming a fault

(a) For one-minute samples, define $r_u=u_{cmd}-u_{meas}$ and flag when $r_u>0.1$ for three consecutive valid samples; attach the evidence and sample times. With residual 0.2 this condition is met after the third sample. Name the state 'flow-tracking discrepancy', not 'valve definitely stuck'. (b) Reset only after $|r_u|<0.05$ for five valid samples; invalid sensor data should enter a distinct unknown state rather than count as successful tracking. (c) Valve limitation, supply-pressure loss, calibration error or a faulty flow sensor can all produce this record. Independent valve-position/supply-pressure measurement or a redundant flow check helps distinguish them. Concentration alone adds delayed, model-dependent evidence.

## Problem 05.2 - A reproducible Sugeno control action

(a) Memberships are $[0,0.7,0.3]$, so the weighted output is 0.3. (b) The requested increment is 0.06; the requested command is 1.02 and the applied blend is 1.0. Record the difference for any internal integrator or anti-windup mechanism. (c) If $e=e_{physical}/E$, reducing $E$ produces a larger normalized error for the same physical condition and activates more extreme rules. Thus normalization acts like a gain and must be part of the controller specification. The normalized domain and saturation policy also determine behavior outside the trained/design range.

## Problem 05.3 - Mamdani centroid is not singleton averaging

(a) For a symmetric triangle of base width 1, clipping at height $h$ leaves area $h-h^2/2$. The areas are 0.48 and 0.18. Each clipped set retains its center by symmetry. (b) The supports do not overlap except at a zero-membership endpoint, so the total first moment is $-0.5(0.48)+0.5(0.18)=-0.15$ and the area is 0.66. The centroid is $-0.2272727$. (c) The Sugeno result is $[-0.5(0.8)+0.5(0.2)]/(0.8+0.2)=-0.3$. The difference comes from the nonlinear dependence of clipped area on firing strength. A program that returns -0.3 for this Mamdani construction has implemented a different inference system.

## Problem 05.4 - A fuzzy gain schedule with an explicit implementation

(a) The proportional gains are 1, 2 and 3; the integral gains are 0.1, 0.2 and 0.3 per minute. (b) At sample $k$, evaluate $K_{p,k},K_{i,k}$ from the current error, calculate $v_k=K_{p,k}e_k+I_k$, apply $u_k=\operatorname{sat}_{[0,1]}v_k$, and update $I_{k+1}=I_k+T_s[K_{i,k}e_k+K_{aw}(u_k-v_k)]$. This integral state is already in actuator units. (c) Fixed-gain tests reveal local behavior and numerical errors, but the actual system is nonlinear and time-varying. Rapid scheduling, noise, delays and saturation may produce behaviors absent in frozen models. Test transitions and perturbations throughout the operating region; a formal global claim requires additional analysis.

## Problem 05.5 - Validate the rule surface before a closed-loop comparison

(a) Evaluate a dense grid including corners and every membership breakpoint; require a finite output within declared limits and nonzero aggregate firing. Along zero error change, check that positive error does not command a decrease in high-feed fraction under the chosen sign convention. Examine neighboring values for unintended jumps. (b) Asymmetric input/output membership widths, asymmetric normalization or non-symmetric saturation can break odd symmetry even if linguistic labels appear symmetric. (c) Keep reference, disturbance, noise, sample rate, initial state and actuator limits identical. Compare PI, an incremental fuzzy controller, and a PI with only fuzzy gain scheduling. Report tuning effort and all gains/rules. This separates the effect of inference from the effect of merely changing nominal gain or actuator smoothing.

# Unit 05 - Knowledge-based supervision and fuzzy control

[Course guide](../README.md) · [Notebook](../../laboratories/05-expert-fuzzy-control/notebook.ipynb) · [Exercises](../../problem-sets/05-expert-fuzzy-control/exercises.md) · [Worked solutions](../../problem-sets/05-expert-fuzzy-control/solutions.md)

**Prerequisites:** Units 01-03; sets, piecewise functions and numerical integration.

## Supervisory rules express decisions and evidence

A rule such as IF the concentration residual is large AND the flow sensor agrees with its command THEN suspect a concentration-path fault represents a diagnostic hypothesis. It does not prove a failed sensor. Store the measured evidence, persistence interval, action and reset condition separately. Use priorities for conflicting rules: an invalid measurement should inhibit a normal optimization request. Hysteresis and dwell time prevent repeated switching near a threshold. A low concentration alone cannot distinguish an inlet change, valve fault or concentration-sensor bias.

## Fuzzy membership is a degree of compatibility

On a normalized error domain $[-1,1]$, define negative, zero and positive memberships by $\mu_N(e)=\max(0,-e)$, $\mu_Z(e)=1-|e|$ and $\mu_P(e)=\max(0,e)$, after explicitly limiting $e$ to the domain. They sum to one. These numbers are not probabilities unless a separate probabilistic interpretation is established. Input scaling determines which physical errors activate each rule.

For a two-input controller using error and error change, a rule might be IF error is positive AND error change is positive THEN increase the blend strongly. Specify whether AND is minimum or product. Mamdani inference clips or scales an output membership function for every firing rule, aggregates the results, and often defuzzifies with the centroid:

$$u_f=\frac{\int z\,\mu_{out}(z)\,dz}{\int\mu_{out}(z)\,dz}.$$

For zero-order Sugeno inference, singleton consequents $z_i$ give $u_f=(\sum_i w_i z_i)/(\sum_i w_i)$. This generally differs from the centroid of overlapping Mamdani sets. If no rule fires, use a documented fallback; adding an arbitrary epsilon to the denominator does not define a meaningful inference result.

## Fuzzy control can act at several levels

A fuzzy controller may directly choose the command, produce its increment, or schedule PI/PID gains. If $u_k=u_{k-1}+K_u u_f$, then $K_u$ and the sampling interval determine how quickly the actuator moves. A fuzzy PID schedule changes $K_p,K_i,K_d$ with operating conditions; integrate with the current gain convention consistently and retain anti-windup. A stable PI at every fixed gain setting does not by itself prove stability during arbitrary gain switching.

For the tank, positive concentration error should generally increase the high-feed fraction. The rule surface must respect this known sign. Examine its monotonicity, continuity and saturated behavior before closing the loop. Compare against the same PI baseline with identical sensors and limits. Display both the membership functions and the resulting control surface; a list of linguistic rules alone is insufficient for reproduction.

## Computational practice

From the repository root, run `python tools/run_course.py --unit 5`. Use the notebook to inspect assumptions, rerun calculations and compare them with the worked reasoning. The lesson's hypothetical examples illustrate the method; inspect each program's configuration before comparing numerical outputs.

# Unit 02 - Feedback, stability and IMC tuning

[Exercises](exercises.md) · [Lesson](../../course/02-feedback-imc/lesson.md)

These worked answers use the explicitly hypothetical problem data. Design questions may admit other defensible solutions if their assumptions and evidence are stated.

## Problem 02.1 - An IMC reference design with a physical actuator

(a) $K_p=10/5=2$ and $K_i=1/5=0.2$ per minute. The ideal deviation response is $0.2(1-e^{-t/5})$. (b) At the original equilibrium, $I=0.4$; immediately after the step, $v=2(0.2)+0.4=0.8$, within the bounds. (c) The larger error is 0.8, giving $v=2.0$, but $u$ can only be 1. Concentration approaches at most 1. The linear closed-loop transfer function assumes $u=v$ and cannot predict saturation or the accumulating integral state. The target itself is infeasible, so anti-windup can improve recovery but cannot make it attainable.

## Problem 02.2 - A stable continuous design with an unstable software choice

(a) With zero reference, $e_k=-c_k$ and $c_{k+1}=(a-bK_p)c_k+bI_k$, while $I_{k+1}=I_k-T_sK_ic_k$. This gives the stated matrix. (b) For $a=0.9048374$, the trace is 1.7145123 and determinant 0.7335448; eigenvalues are approximately $0.89390714$ and $0.82060511$, inside the unit circle. (c) For $a=e^{-1}$, the matrix has trace about 0.1036383 and determinant $e^{-1}=0.3678794$. The poles are a complex pair of magnitude $\sqrt{e^{-1}}=0.606531$, so this particular sample remains stable, although response quality differs. This is a deliberate check against assuming coarse sampling always destabilizes. At $T_s=20$ min the determinant is $2-e^{-2}=1.864665>1$, so at least one pole is outside the unit circle. Derive and test the implemented update instead of guessing.

## Problem 02.3 - Recover from windup

(a) $v=0.9+0.4=1.3$ and $u=1$. (b) Without correction, $I^+=0.9+0.04=0.94$. With back-calculation, $I^+=0.9+0.04+0.5(1-1.3)=0.79$. The correction removes the portion of the integral state responsible for an unrealizable command. (c) A stuck valve, rate limit or failed low-level flow loop can make the actual blend differ from the clipped software request. Tracking actual actuator feedback aligns the internal controller state with what the plant receives. Sensor delay in that feedback must itself be considered. Excessively fast back-calculation can create undesirable sampled transients.

## Problem 02.4 - Delay uncertainty and a robustness budget

(a) $K_p=10/(5+2)=10/7$ and $T_i=10$ min, hence $K_i=1/7$ per minute. (b) The delay-free gains are 2 and 0.2, so both new gains are $5/7$ of those values. The lower gain accounts approximately for the missing phase information caused by delay. (c) Use the same bounded reference and disturbance trajectories at each delay, with a delay buffer that represents fractional samples explicitly. Record stability, peak error, constraint violations, IAE and actuator variation. Sustained oscillation, growing error, or violation of a declared operating limit in an allowed delay case disqualifies a candidate even if its nominal tracking integral is lower. A finite grid is evidence for those cases, not a proof for every delay.

## Problem 02.5 - Choose metrics before choosing the winner

(a) A has IAE 0.35 and variation $0.4+0.5+0.4+0.2=1.5$. B has IAE 0.40 and variation $0.2+0.02+0.03+0.03=0.28$. (b) $J_A=0.50$ and $J_B=0.428$, so B wins under this explicitly chosen cost although A tracks more tightly by IAE. (c) State the sample interval, quadrature convention, input normalization, initial input and weight units. Changing the weight can reverse the ranking; neither controller is universally superior. Treat hard safety/operating constraints separately rather than allowing a favorable average score to compensate for violations.

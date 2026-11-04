# Unit 02 - Feedback, stability and IMC tuning

[Lesson](../../course/02-feedback-imc/lesson.md) · [Worked solutions](solutions.md)

State units, assumptions and initial conditions before calculating. For computational extensions, report the actual experiment and its limitations.

## Problem 02.1 - An IMC reference design with a physical actuator

The tank operates initially at $c=u=0.4$ and the reference changes to 0.6. (a) Derive PI gains for $\lambda=5$ min and the nominal reference response. (b) Compute the immediate actuator command using the equilibrium integral state. (c) Repeat for a reference of 1.2 and explain which part of the nominal calculation ceases to predict the real response.

## Problem 02.2 - A stable continuous design with an unstable software choice

For $K_p=2$, $K_i=0.2$ per minute, use the exact held-input plant and the explicit integral update in the lesson. (a) Derive the closed-loop matrix. (b) Evaluate its eigenvalues for $T_s=1$ min. (c) Test $T_s=10$ min and explain why the continuous-time stability proof is insufficient.

## Problem 02.3 - Recover from windup

At one sample $I=0.9$, $e=0.2$, $K_p=2$, $K_i=0.2$, $T_s=1$ min. (a) Calculate requested and applied commands. (b) Calculate the next integral state without anti-windup and with $K_{aw}=0.5$ per minute. (c) Explain why back-calculation should use actual actuator feedback when the valve differs from the software saturation.

## Problem 02.4 - Delay uncertainty and a robustness budget

An identified model is $P(s)=e^{-2s}/(10s+1)$. (a) Apply the stated approximate IMC-PI rule for $\lambda=5$ min. (b) Compare gains to the delay-free design. (c) Propose a reproducible experiment with delay ranging from 1 to 4 min and explain which result would disqualify the fast tuning even if nominal IAE is smaller.

## Problem 02.5 - Choose metrics before choosing the winner

Controller A has absolute errors $[0.2,0.1,0.05,0]$ and applied inputs $[0.8,0.3,0.7,0.5]$. Controller B has errors $[0.2,0.12,0.06,0.02]$ and inputs $[0.6,0.58,0.55,0.52]$. Assume one-minute equal-duration intervals and an initial input of 0.4. (a) Compute rectangle-rule IAE and total input variation. (b) Compare $J=\mathrm{IAE}+0.1\,\mathrm{TV}(u)$. (c) Explain what a fair report must disclose about this scalar score.

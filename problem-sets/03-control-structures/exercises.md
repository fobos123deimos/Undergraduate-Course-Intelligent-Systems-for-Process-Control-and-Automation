# Unit 03 - Multiloop, multivariable, feedforward and cascade control

[Lesson](../../course/03-control-structures/lesson.md) · [Worked solutions](solutions.md)

State units, assumptions and initial conditions before calculating. For computational extensions, report the actual experiment and its limitations.

## Problem 03.1 - A feed composition disturbance

The concentration target is 0.5. The low feed changes from $d=0$ to 0.2 while total flow remains constant. (a) Calculate the new blend fraction required for zero steady error. (b) Compare exact nonlinear feedforward with the linearization around $u=0.5,d=0$. (c) Determine what occurs if $d$ rises to 0.7 and the target is unchanged.

## Problem 03.2 - When perfect feedforward cannot be built

Suppose $G_u=e^{-3s}/(10s+1)$ and $G_d=0.6e^{-s}/(10s+1)$. (a) Derive the ideal cancellation transfer function. (b) Explain the implementation obstacle. (c) Propose an implementable architecture and an experiment that separates feedforward benefit from ordinary feedback correction.

## Problem 03.3 - Design the inner flow loop before the outer loop

A blend actuator has $\tau_v=2$ min and the vessel has $\tau=10$ min. Use $v=u_{sp}+K_f(u_{sp}-u)$. (a) Choose $K_f$ for an inner time constant of 0.5 min. (b) Derive the transfer functions from $u_{sp}$ and $w$ to $u$. (c) Discuss what a valve limit and sensor noise can invalidate in the desired bandwidth separation.

## Problem 03.4 - Pairing and decoupling a coupled process

Use $K=\begin{bmatrix}1&0.6\\0.4&1\end{bmatrix}$. (a) Calculate its inverse and relative gain array. (b) Find the steady input change required for output change $[0.2,0]^T$. (c) If the available input deviations are each limited to $[-0.1,0.1]$, explain why independent output targets cannot be assumed achievable.

## Problem 03.5 - Select a structure with a fair information budget

A concentration loop is affected by slow inlet-composition drift and rapid supply-pressure disturbances at its valve. Available upgrades are an upstream composition sensor and an inner flow sensor. (a) Map each sensor to the disturbance it can address. (b) Design a three-case comparison that attributes improvement to architecture rather than extra actuator range. (c) State why a static RGA from one operating point cannot settle the full design choice.

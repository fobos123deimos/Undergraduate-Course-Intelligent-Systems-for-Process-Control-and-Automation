# Unit 03 - Multiloop, multivariable, feedforward and cascade control

[Exercises](exercises.md) · [Lesson](../../course/03-control-structures/lesson.md)

These worked answers use the explicitly hypothetical problem data. Design questions may admit other defensible solutions if their assumptions and evidence are stated.

## Problem 03.1 - A feed composition disturbance

(a) $u=(0.5-0.2)/(1-0.2)=0.375$. (b) The local relation is $\delta c=\delta u+0.5\delta d$, giving $u_{lin}=0.5-0.5(0.2)=0.4$. Its actual equilibrium is $0.4+0.6(0.2)=0.52$, so feedback must remove 0.02 concentration error. (c) Even $u=0$ gives concentration 0.7; any high-feed addition increases it. The target is infeasible. The supervisor should flag the condition or change the admissible target rather than continue integrating an error that the actuator cannot remove.

## Problem 03.2 - When perfect feedforward cannot be built

(a) $F=-G_d/G_u=-0.6e^{2s}$. (b) This needs the disturbance two minutes into the future; the actuator path is slower than the disturbance path. A causal controller cannot supply an unknown future value. (c) Use upstream sensing that provides at least two minutes of genuine transport preview if available; otherwise use a causal gain/filter and accept residual transient error, with feedback trimming. Compare feedback alone and feedback plus the feasible feedforward on the same recorded disturbance and initial state. Account for sensor location, latency and noise. Do not model an artificial negative delay and describe the resulting cancellation as implementable.

## Problem 03.3 - Design the inner flow loop before the outer loop

(a) $2/(1+K_f)=0.5$, so $K_f=3$. (b) From $2\dot u=(1+K_f)u_{sp}-(1+K_f)u+w$, $U/U_{sp}=4/(2s+4)$ and $U/W=1/(2s+4)$. The steady load sensitivity is reduced from 1 to 1/4. (c) Saturation prevents the requested initial response, and a noisy inner sensor is multiplied by the feedback gain. Rate limits add dynamics that the first-order design omits. Before tuning the outer loop around the 0.5-minute response, verify the inner loop over its actual working range, including setpoint bounds and disturbance amplitudes.

## Problem 03.4 - Pairing and decoupling a coupled process

(a) $K^{-1}=\frac1{0.76}\begin{bmatrix}1&-0.6\\-0.4&1\end{bmatrix}$ and the RGA has diagonal $1/0.76=1.315789$ and off-diagonal $-0.24/0.76=-0.315789$. (b) The required change is $[0.263158,-0.105263]^T$. (c) Both demands exceed their respective limits in magnitude, so the target is infeasible under these bounds. Saturating the inverse output destroys nominal cancellation and creates error in both outputs. A constrained optimization can select an attainable compromise, with output weights reflecting declared priorities.

## Problem 03.5 - Select a structure with a fair information budget

(a) The composition sensor enables feedforward for changes in the entering material. The flow sensor enables a cascade loop that rejects supply disturbances before concentration changes appreciably. (b) Compare feedback only, feedback plus measured composition feedforward, and that architecture plus inner flow regulation. Hold plant parameters, final actuator bounds, reference schedule, disturbance realizations and initial conditions fixed; disclose the added sensors and their noise/latency. Report concentration error and valve movement separately. (c) RGA describes local steady gains; it does not represent disturbance location, measurement timing, dynamic interaction, noise amplification or actuator constraints. Repeat local analyses across operating points and validate the chosen dynamic structure.

# Unit 01 - Modeling, identification and simulation

[Exercises](exercises.md) · [Lesson](../../course/01-modeling-identification/lesson.md)

These worked answers use the explicitly hypothetical problem data. Design questions may admit other defensible solutions if their assumptions and evidence are stated.

## Problem 01.1 - From vessel balances to an admissible simulation

(a) The total balance is $\dot V=q_H+q_L-q_o=0$. The solute balance is $V\dot c+c\dot V=q_H-q_oc$; substituting $q_H=10u$ and $q_o=10$ gives $10\dot c=u-c$. (b) $c(t)=0.7-0.5e^{-t/10}$, so $c(10)=0.5160603$. Solving $e^{-t/10}=0.05$ gives $t_{95}=29.9573$ min. The concentration remains between its initial and final values. (c) $V(t)=100+2t$ and $\dot c=10(0.7-c)/(100+2t)$. Separation gives $c(t)=0.7-0.5[100/(100+2t)]^5$. The response slows as the vessel fills; the constant residence-time, time-invariant transfer function no longer applies. A finite tank also needs an overflow limit.

## Problem 01.2 - A sampled model that respects concentration bounds

(a) Integration yields $c_{k+1}=e^{-T_s/10}c_k+(1-e^{-T_s/10})u_k$. Both coefficients are nonnegative and sum to one, proving invariance for admissible $c_k,u_k$. (b) Exact poles are approximately 0.90484, 0.22313 and 0.08208. Euler poles are 0.9, -0.5 and -1.5. At 15 min Euler is stable but can leave the physical interval; at 25 min it is unstable. (c) Re-run with successively smaller steps, check the analytical solution for a constant input and audit units and state initialization. Convergence to a physically impossible result points beyond time-step error. Do not conceal the failure by clipping the state, since clipping creates or destroys material.

## Problem 01.3 - Identify a process without leaking the answer

(a) Solving $0.2a+0.8b=0.26$ and $0.26a+0.1b=0.244$ gives $a=0.9$, $b=0.1$. The exact continuous time constant would be $-1/\ln(0.9)=9.49122$ min; interpreting this as the earlier Euler discretization instead gives 10 min. The discretization convention matters. (b) At equilibrium $u_k=c_k$ and $c_{k+1}=c_k$, so only $a+b=1$ is identified: the columns of $\Phi$ coincide. (c) Use different bounded multilevel sequences and different initial concentrations; reserve the last complete sequence for final reporting. Fit coefficients and scaling on training data, choose model order/regularization using validation data, then evaluate the frozen model once on test data. Report free-run and one-step errors separately.

## Problem 01.4 - Disturbance linearization and sensor dynamics

(a) The derivatives are $\partial f/\partial c=-0.1$, $\partial f/\partial u=0.1$, $\partial f/\partial d=0.06$. Therefore $Y/U=1/[(10s+1)(2s+1)]$ and $Y/D=0.6/[(10s+1)(2s+1)]$ in deviation variables. (b) The exact steady value is $0.4+0.6(0.1)=0.46$; the local prediction happens to be exact for this disturbance with fixed $u$. (c) A single lag may absorb the sensor's lag into an effective residence time or delay. An aggressively tuned controller then acts on a slower measurement than the plant-only design assumes. Identify sensor dynamics independently where possible, and report whether the model output is physical concentration or the measured signal.

## Problem 01.5 - Choose an identification claim that the evidence supports

(a) SSE is 0.10, MSE 0.025, RMSE $\sqrt{0.025}=0.158114$, and maximum absolute error 0.2. The target mean is 0.5 and the sum of squared deviations is 1, hence $R^2=0.90$. (b) A recursively simulated autoregressive model with a pole slightly above one can make small corrections when measured outputs are supplied, yet drift when fed its own outputs. (c) Match the paper's plant variant, parameters, sampling, input sequence, initial state and noise convention; keep a common independent test record and metric normalization. Four samples do not establish generalization, robustness or physical validity. The article uses MAE for maximum absolute error; write the metric out to avoid confusing it with mean absolute error.

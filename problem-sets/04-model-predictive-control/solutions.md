# Unit 04 - Constrained model predictive control

[Exercises](exercises.md) · [Lesson](../../course/04-model-predictive-control/lesson.md)

These worked answers use the explicitly hypothetical problem data. Design questions may admit other defensible solutions if their assumptions and evidence are stated.

## Problem 04.1 - Build the prediction matrices by hand

(a) $F=[0.9,0.81,0.729]^T$ and $G=\begin{bmatrix}0.1&0&0\\0.09&0.1&0\\0.081&0.09&0.1\end{bmatrix}$. (b) Multiplication, or recursive substitution, gives $[0.23,0.277,0.2893]^T$. (c) Only 0.5 is applied now. At the next sample, the state estimate and reference forecast may differ, so the optimization is repeated and the previous 0.7/0.4 plans are not commitments. All language implementations must use the same initial state and timing to obtain matching predictions.

## Problem 04.2 - Solve a constrained one-step controller

(a) Differentiating the objective gives $2b(ac+bu-r)+2\rho(u-u_{old})=0$. Thus $u^*=[0.1(0.8-0.18)+0.01(0.4)]/0.02=3.3$. (b) The intersection of amplitude and rate bounds is $[0.3,0.5]$, so the exact constrained optimum is 0.5. (c) $c^+=0.9(0.2)+0.1(0.5)=0.23$. The target remains a desired future output even though it cannot be reached in one step; clipping it to an immediately reachable value changes the performance objective and future plan. In this scalar convex problem projection is exact, but that property does not extend to arbitrary coupled QPs.

## Problem 04.3 - Input increments and operating-point offsets

(a) $D=\begin{bmatrix}1&0&0\\-1&1&0\\0&-1&1\end{bmatrix}$ and $d_0=[0.6,0,0]^T$. (b) The magnitude penalty is $3(0.6)^2=1.08$; the increment penalty is zero. The former encourages lower absolute actuation, while the latter only discourages movement. (c) A deviation model expects $\delta u=u-u^*$ and predicts $\delta y=y-y^*$. Feeding absolute $u$ introduces a systematic operating-point error and may lead the optimizer to inappropriate actions. Store and test the offsets explicitly, including state initialization, reference translation and actuator bounds in deviation coordinates.

## Problem 04.4 - A multivariable feasibility calculation

(a) Apply the inverse from Unit 03:

$$u=\frac{1}{0.76}\begin{bmatrix}1.4-0.12\\-0.56+0.2\end{bmatrix}=\begin{bmatrix}1.684211\\-0.473684\end{bmatrix}.$$

(b) Because $K$ is nonsingular this is the unique input producing the target; both components violate bounds. (c) Solve $\min_{0\leq u\leq1}(Ku-r)^T\operatorname{diag}(4,1)(Ku-r)$. Its optimum is a feasible compromise, not an exact realization of $r$. A steady target layer can supply consistent equilibrium inputs/outputs to the dynamic regulator, avoiding an impossible terminal goal. The 4:1 weights express priority; report the resulting errors in both outputs.

## Problem 04.5 - A solver failure is an operating event

(a) One conservative fallback is to hold the previous feasible input after applying declared rate and amplitude limits, while recording the event. Retain the actual applied input and the latest trustworthy state estimate. A separately validated backup controller is another option; transfer its integral state consistently. (b) A constant-disturbance estimator can correct bias in model predictions, improving offset behavior, but it does not provide computing time or a guaranteed feasible optimization result. (c) Log solve status, elapsed time, objective, maximum constraint residual, input actually applied and fallback flag at every sample. Report deadline misses and their effects separately, including worst-case intervals. Neither a successful solver status nor a short nominal trace proves recursive feasibility for untested conditions.

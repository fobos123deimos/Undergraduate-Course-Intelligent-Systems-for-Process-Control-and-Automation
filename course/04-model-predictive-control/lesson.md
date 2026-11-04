# Unit 04 - Constrained model predictive control

[Course guide](../README.md) · [Notebook](../../laboratories/04-model-predictive-control/notebook.ipynb) · [Exercises](../../problem-sets/04-model-predictive-control/exercises.md) · [Worked solutions](../../problem-sets/04-model-predictive-control/solutions.md)

**Prerequisites:** Units 01-03; quadratic forms, least squares and constrained optimization.

## Predict several steps, apply only the first action

For $x_{k+1}=Ax_k+Bu_k$, $y_k=Cx_k$, assemble predicted outputs as $Y=Fx_k+GU$, where $U=[u_k^T,\ldots,u_{k+N-1}^T]^T$. The first block rows are $CA$ in $F$ and $CB$ in $G$; the second are $CA^2$ and $[CAB,CB]$. Use a consistent convention: these predictions begin at $k+1$.

A useful objective is

$$J=(Y-R)^TQ(Y-R)+(DU-d_0)^TR_u(DU-d_0),$$

where $DU-d_0$ stacks input increments and its first element is $u_k-u_{k-1}$. Bounds on $U$, input increments and predicted outputs become linear inequalities. Penalizing input magnitude instead of increments solves a different problem, especially around nonzero operating points. The Hessian is positive definite when the regularization supplies strictly positive curvature in every free input direction.

At each sample, estimate the state, solve the optimization, apply the first action, and repeat. Use a shorter control horizon by holding the last planned move constant; write this mapping explicitly rather than silently changing the prediction length. Log solver status, time and fallback use. A failed solver must not be treated as a valid optimum.

## One step exposes the tradeoff

For $c^+=ac+bu$ and $J=(c^+-r)^2+\rho(u-u_{old})^2$, the unconstrained optimum is

$$u^*=\frac{b(r-ac)+\rho u_{old}}{b^2+\rho}.$$

With only scalar interval constraints, project this value onto their intersection. This is exact for the scalar one-step problem; independently clipping a general coupled multistep solution is not equivalent to solving its constrained quadratic program.

## Constraints and offset have different causes

If the target lies beyond the attainable set, no horizon removes that incompatibility. Soften selected output targets with nonnegative slack and an explicit penalty when the application permits it; keep actuator bounds hard. For persistent model mismatch, augment a constant disturbance state and estimate it, or add another justified offset-free mechanism. A large prediction horizon alone does not guarantee zero steady error.

## Stability is a design property to establish

Finite-horizon optimization and decreasing simulated error do not automatically imply closed-loop stability. Classical sufficient conditions involve suitable terminal cost, terminal invariant constraints and a feasible terminal controller. The teaching implementations demonstrate finite-horizon behavior under their declared experiments; do not infer a global nonlinear stability theorem. For multivariable processes, inspect individual output constraints and input allocation, not just the sum of squared errors.

## Computational practice

From the repository root, run `python tools/run_course.py --unit 4`. Use the notebook to inspect assumptions, rerun calculations and compare them with the worked reasoning. The lesson's hypothetical examples illustrate the method; inspect each program's configuration before comparing numerical outputs.

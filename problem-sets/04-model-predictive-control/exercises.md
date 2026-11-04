# Unit 04 - Constrained model predictive control

[Lesson](../../course/04-model-predictive-control/lesson.md) · [Worked solutions](solutions.md)

State units, assumptions and initial conditions before calculating. For computational extensions, report the actual experiment and its limitations.

## Problem 04.1 - Build the prediction matrices by hand

For $c^+=ac+bu$, use $a=0.9,b=0.1$ and a prediction horizon of three. (a) Write $F$ and $G$ for $Y=[c_{k+1},c_{k+2},c_{k+3}]^T$. (b) Predict the sequence for $c_k=0.2$ and planned inputs $[0.5,0.7,0.4]^T$. (c) Explain which action a receding-horizon controller actually sends to the plant and when the other actions may change.

## Problem 04.2 - Solve a constrained one-step controller

Use $a=0.9,b=0.1$, $c=0.2$, $r=0.8$, $u_{old}=0.4$ and $\rho=0.01$. (a) Derive and calculate the unconstrained optimum. (b) Enforce $0\leq u\leq1$ and $|u-u_{old}|\leq0.1$. (c) Compute the next concentration and explain why clipping the reference would solve a different problem.

## Problem 04.3 - Input increments and operating-point offsets

A controller operates at $u=0.6$. (a) Write the difference matrix and initial-value vector for three planned absolute inputs. (b) Compare the penalties on $U=[0.6,0.6,0.6]^T$ when penalizing $U^TU$ and $(DU-d_0)^T(DU-d_0)$. (c) Explain the effect of using absolute inputs in a model identified in deviations.

## Problem 04.4 - A multivariable feasibility calculation

At steady state $y=Ku$ with $K$ from Unit 03 and $0\leq u_i\leq1$. Target $y=[1.4,0.2]^T$. (a) Calculate the unconstrained input. (b) Prove that this target is infeasible. (c) Formulate a constrained steady target optimizer with output weights 4 and 1 and explain how it can support a dynamic MPC.

## Problem 04.5 - A solver failure is an operating event

A constrained MPC normally finishes in 0.02 s but occasionally exceeds a 0.1 s sampling deadline. (a) Design a causal fallback and identify what state it must retain. (b) Explain how disturbance-state augmentation can address steady mismatch but not a missed deadline. (c) Specify a validation record that prevents an apparently good output plot from hiding solver failures.

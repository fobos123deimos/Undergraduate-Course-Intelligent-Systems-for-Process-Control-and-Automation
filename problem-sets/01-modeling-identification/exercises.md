# Unit 01 - Modeling, identification and simulation

[Lesson](../../course/01-modeling-identification/lesson.md) · [Worked solutions](solutions.md)

State units, assumptions and initial conditions before calculating. For computational extensions, report the actual experiment and its limitations.

## Problem 01.1 - From vessel balances to an admissible simulation

A tank initially contains 100 L at $c(0)=0.2$. The total inlet and outlet flows are 10 L/min and the high-concentration fraction becomes $u=0.7$. (a) Derive the concentration equation from total and solute balances, retaining the volume derivative until the end. (b) Obtain $c(t)$, its value at 10 min, and the time to reach 95% of its total change. (c) Explain what changes if the outlet is fixed at 8 L/min; derive the new volume and concentration equations and identify which transfer-function assumption fails.

## Problem 01.2 - A sampled model that respects concentration bounds

Use the same tank with a held input. (a) Derive the exact sampled model for an arbitrary $T_s$ and prove interval invariance. (b) Compare its pole with Euler at $T_s=1$, 15 and 25 min. (c) A numerical model produces a negative concentration after a valid inlet change. Decide which evidence would distinguish an integration artifact from a wrong balance or inconsistent initial condition.

## Problem 01.3 - Identify a process without leaking the answer

Noiseless input-output samples are $(c_k,u_k,c_{k+1})=(0.2,0.8,0.26)$ and $(0.26,0.1,0.244)$. (a) Estimate $a,b$ and identify the time constant if these are exact one-minute samples. (b) Show why equilibrium-only observations do not uniquely determine both parameters. (c) Design independent training, validation and test trajectories for a noisy experiment and state which model choices may use each split.

## Problem 01.4 - Disturbance linearization and sensor dynamics

Let the low-concentration feed carry an unknown normalized concentration $d$. Its balance is $10\dot c=u+(1-u)d-c$. A concentration sensor obeys $2\dot y=c-y$. (a) Linearize around $(u,d,c)=(0.4,0,0.4)$ and obtain both measured-output transfer functions. (b) Find the steady concentration after $d$ rises to 0.1 with fixed $u=0.4$. (c) Explain why fitting a single first-order model to $u\mapsto y$ can distort controller tuning.

## Problem 01.5 - Choose an identification claim that the evidence supports

A model gives test errors $e=[0.1,-0.1,0.2,-0.2]$ on $y=[0,1,0,1]$. (a) Compute SSE, MSE, RMSE, maximum absolute error and $R^2$. (b) Give a case where a small one-step error would coexist with poor free simulation. (c) Propose two checks that would make a comparison against a model from Kroll and Schulte meaningful, and one conclusion these four samples cannot support.

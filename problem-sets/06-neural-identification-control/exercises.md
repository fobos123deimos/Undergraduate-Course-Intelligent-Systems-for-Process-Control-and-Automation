# Unit 06 - Neural modeling and control of dynamic systems

[Lesson](../../course/06-neural-identification-control/lesson.md) · [Worked solutions](solutions.md)

State units, assumptions and initial conditions before calculating. For computational extensions, report the actual experiment and its limitations.

## Problem 06.1 - A perceptron for a simple supervisory condition

Inputs are binary indicators $x_1$ (high residual) and $x_2$ (flow mismatch); the desired alarm is their logical OR. (a) Give weights and bias implementing the desired truth table with output 1 when $w^Tx+b\geq0$. (b) Starting from $w=[0,0]$, $b=0$ and learning rate 1, calculate the update after the sample $x=[0,0],t=0$, then after $x=[1,0],t=1$. (c) Explain why this classifier does not localize a specific physical fault.

## Problem 06.2 - Differentiate a minimal neural predictor

For one scalar regressor $x=0.5$, let $h=\tanh(w_1x)$, $\hat y=w_2h$, $w_1=1,w_2=0.8$, target $y=0.4$ and loss $L=(\hat y-y)^2/2$. (a) Compute the prediction. (b) Derive both weight gradients. (c) State how a finite-difference check and a separate validation trajectory catch different errors.

## Problem 06.3 - Fit and interpret a two-center RBF

Use centers 0 and 1, width $\sigma=1$, no bias term, and training pairs $(x,y)=(0,0),(1,1)$. (a) Write the design matrix. (b) Solve for the two exact interpolation weights. (c) Explain what predictions far outside $[0,1]$ reveal about this architecture and why regularization changes interpolation.

## Problem 06.4 - A SOM organizes operating modes

A two-unit SOM has prototypes $m_1=[0.2,0.3]^T$ and $m_2=[0.8,0.7]^T$. The normalized observation is $x=[0.3,0.4]^T$. Use learning rate 0.5, neighborhood weight 1 for the winner and 0.2 for the other unit. (a) Find the winner. (b) Calculate both updates. (c) Explain how training-data scaling and a subsequent fault label affect interpretation.

## Problem 06.5 - Put a neural prediction inside a bounded control decision

A local learned model predicts $\hat c^+=0.9c+0.1u+0.02u^2$. At $c=0.4$, current $u=0.4$ and desired next concentration 0.5, use a Newton inverse step with $\gamma=1$. (a) Calculate the prediction, derivative and candidate input. (b) Enforce $0\leq u\leq1$ and $|u-u_{old}|\leq0.1$. (c) Give two reasons to retain a fallback even if this training model fits well.

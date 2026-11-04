# Unit 01 - Modeling, identification and simulation

[Course guide](../README.md) · [Notebook](../../laboratories/01-modeling-identification/notebook.ipynb) · [Exercises](../../problem-sets/01-modeling-identification/exercises.md) · [Worked solutions](../../problem-sets/01-modeling-identification/solutions.md)

**Prerequisites:** Differential equations, units, matrix least squares and elementary probability.

## A model begins with a boundary

A controller changes a physical input; its software output is not automatically that input. Draw the vessel, inlet streams, outlet, sensor and valve before naming states. For a perfectly mixed tank with constant density and cross-sectional area $A$, conservation gives

$$A\dot h=q_H+q_L-q_o,\qquad \frac{d(Ahc)}{dt}=q_Hc_H+q_Lc_L-q_oc.$$

Expanding the derivative and substituting the volume balance cancels the outlet term in the concentration equation:

$$\dot c=\frac{q_H(c_H-c)+q_L(c_L-c)}{Ah}.$$

This cancellation does not mean the outlet is irrelevant: it changes $h$, which changes the residence time. Mixing is assumed instantaneous; density differences, reaction, evaporation and sensor dynamics are absent. A simulation approaching $h=0$ must stop or change its physical model rather than divide by a clipped volume silently.

## A common worked process

The exercises use hypothetical values $V=100$ L, total flow $q=10$ L/min and normalized feed concentrations $c_H=1$, $c_L=0$. A low-level flow system holds $q$ constant while $q_H=qu$ and $q_L=q(1-u)$, with $0\leq u\leq1$. Thus

$$\tau\dot c=u-c,\qquad \tau=V/q=10\ {\rm min}.$$

These are new teaching parameters, not a transcription of the archived Blending Tank files. At a constant input, $c^*=u^*$. In deviation variables, $G(s)=1/(10s+1)$. At a one-minute sampling period with a zero-order-held input,

$$c_{k+1}=ac_k+bu_k,\qquad a=e^{-0.1}=0.904837418,\quad b=1-a=0.095162582.$$

The analytical feed-composition problems use $d=d_{low}$ for the concentration of the low feed, giving an inlet mixture $u+(1-u)d_{low}$. The shared executable laboratory scenario instead uses an additive disturbance to the total inlet mixture, $u+d_{mix}$. Their conversion is $d_{mix}=(1-u)d_{low}$, so they are not interchangeable at fixed numerical values. Feedforward in the additive scenario compensates by $-d_{mix}$; the low-feed examples derive the nonlinear blend formula explicitly. Check the disturbance definition before comparing a worked answer with a laboratory run.

The exact discretization preserves the interval $[0,1]$ because the next concentration is a convex combination of the current concentration and the inlet blend. Forward Euler gives $a_E=1-T_s/\tau$; it is asymptotically stable for $0<T_s<2\tau$ but preserves this physical interval only for $0<T_s\leq\tau$.

## Identification is an experiment-design problem

Fit $y_{k+1}=ay_k+bu_k+e_{k+1}$ by least squares, $\hat\theta=(\Phi^T\Phi)^{-1}\Phi^TY$, only when the regressor matrix has full column rank. In software, use a QR/SVD least-squares solve rather than forming the inverse. A constant equilibrium record cannot identify both coefficients. Step tests help, but a bounded multilevel or persistently exciting signal gives a broader operating region.

Split complete trajectories chronologically into training, validation and final test sets. Fit scaling parameters on training data only. A one-step prediction uses the measured previous output; free simulation recursively uses its own prediction. Report both because a small one-step error can hide unstable recursive behavior. With noisy measured regressors, ordinary least squares can be biased; instrumental variables or a noise model may be needed.

## Evidence and interpretation

Check mass conservation, equilibria, convergence when the integration step is halved, and agreement with the analytical step response. Inspect residual autocorrelation and correlation with past inputs on an independent trajectory. Residual whiteness alone does not prove a correct physical model. Use the benchmark inventory to distinguish equation-based simulations from experimental datasets, and do not compare numerical scores obtained with different input protocols as if they were the same experiment.

## Computational practice

From the repository root, run `python tools/run_course.py --unit 1`. Use the notebook to inspect assumptions, rerun calculations and compare them with the worked reasoning. The lesson's hypothetical examples illustrate the method; inspect each program's configuration before comparing numerical outputs.

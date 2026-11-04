# Unit 02 - Feedback, stability and IMC tuning

[Course guide](../README.md) · [Notebook](../../laboratories/02-feedback-imc/notebook.ipynb) · [Exercises](../../problem-sets/02-feedback-imc/exercises.md) · [Worked solutions](../../problem-sets/02-feedback-imc/solutions.md)

**Prerequisites:** Unit 01; Laplace transforms, characteristic polynomials and negative feedback.

## Separate the plant, controller and actuator

For the hypothetical tank $P(s)=1/(\tau s+1)$, define the tracking error $e=r-y$ and a PI command $v=K_pe+I$, with $\dot I=K_ie$. The applied blend is $u=\operatorname{sat}_{[0,1]}(v)$. A control diagram that omits this saturation cannot explain windup. For a PID controller, differentiate a filtered measurement rather than an abrupt reference when derivative kick is undesirable; for example use $-K_ds/(1+T_fs)$ on $y$.

With ideal measurement, no saturation and PI feedback, the closed-loop characteristic polynomial is

$$\tau s^2+(1+K_p)s+K_i.$$

The second-order continuous model is asymptotically stable when $\tau>0$, $1+K_p>0$ and $K_i>0$. This result does not cover delays, sampled implementation or saturating nonlinear dynamics. The final-value theorem also requires a stable closed loop before it can justify zero constant-reference error.

## Derive an IMC design rather than memorize gains

For the stable minimum-phase model $\hat P=1/(\tau s+1)$, choose $Q=(\tau s+1)/(\lambda s+1)$. Converting the internal-model structure to ordinary feedback gives

$$C=\frac{Q}{1-\hat P Q}=\frac{\tau s+1}{\lambda s},\qquad K_p=\frac{\tau}{\lambda},\quad K_i=\frac1\lambda.$$

Nominal pole-zero cancellation makes $Y/R=1/(\lambda s+1)$, but the canceled pole still matters to internal dynamics and mismatch. With $\tau=10$ min and $\lambda=5$ min, $K_p=2$ and $K_i=0.2$ per minute. For a first-order-plus-dead-time approximation, the commonly used IMC-PI rule $K_p=\tau/[K(\lambda+\theta)]$, $T_i=\tau$ trades speed for delay tolerance; it is an approximation, not exact cancellation of a delay.

## Implement the controller that was analyzed

One explicit digital update is $v_k=K_pe_k+I_k$, $u_k=\operatorname{sat}(v_k)$, then $I_{k+1}=I_k+T_s[K_ie_k+K_{aw}(u_k-v_k)]$. Here $K_{aw}$ has units of inverse time because $I$ has actuator units. Conditional integration is another option: freeze integration when saturation and the error would push farther into the limit. Keep update order and derivative state explicit in MATLAB, Octave and Python.

The local discrete closed-loop matrix for the unsaturated explicit update and zero reference is

$$M=\begin{bmatrix}a-bK_p&b\\-T_sK_i&1\end{bmatrix}.$$

Its eigenvalues, not continuous poles alone, determine sampled stability. A reference beyond the attainable concentration range has no feasible equilibrium, however stable the local model is.

## Compare outcomes on the same experiment

Use identical initial state, reference steps, feed disturbances and actuator limits. Record tracking error, settling definition, total variation $\sum|u_k-u_{k-1}|$, saturation time and any violation. A smoother input may be valuable even if its integral absolute error is larger. Disturbance rejection and sensor-noise amplification are distinct design goals; one appealing tracking plot cannot demonstrate both.

## Computational practice

From the repository root, run `python tools/run_course.py --unit 2`. Use the notebook to inspect assumptions, rerun calculations and compare them with the worked reasoning. The lesson's hypothetical examples illustrate the method; inspect each program's configuration before comparing numerical outputs.

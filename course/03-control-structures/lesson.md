# Unit 03 - Multiloop, multivariable, feedforward and cascade control

[Course guide](../README.md) · [Notebook](../../laboratories/03-control-structures/notebook.ipynb) · [Exercises](../../problem-sets/03-control-structures/exercises.md) · [Worked solutions](../../problem-sets/03-control-structures/solutions.md)

**Prerequisites:** Units 01-02; matrix inversion and local transfer functions.

## Match architecture to the physical disturbance path

Feedback acts after an output error is visible. Feedforward uses a measured disturbance before that error develops. For $10\dot c=u+(1-u)d-c$, holding the equilibrium at $r$ requires

$$u_{ff}=\frac{r-d}{1-d},\qquad d\ne1.$$

For $0\leq d<1$, this is feasible only when $d\leq r\leq1$. Feedback can trim errors in $d$, mixing and actuator calibration; it cannot repair an impossible target. The linear cancellation formula is $F(s)=-G_d(s)/G_u(s)$. A nonminimum-phase zero or unfavorable delay in $G_u$ can make the ideal inverse unstable or noncausal, so practical feedforward often uses a filtered approximation.

## Cascade closes a faster measured loop

Suppose a valve command $v$ produces the actual blend $u$ through $\tau_v\dot u=v-u+w$, where $w$ is a valve/load disturbance. A fast inner controller regulates measured $u$ to an outer command $u_{sp}$; the outer concentration controller then sees the closed inner dynamics. With inner proportional gain $K_f$ and the feedforward equilibrium command $v=u_{sp}+K_f(u_{sp}-u)$, the inner pole is $-(1+K_f)/\tau_v$. A practical cascade needs an inner sensor, useful bandwidth separation and consistent actuator limits. A fast model is not evidence that an actual noisy valve can move arbitrarily quickly.

## Interactions require a joint view

For a local steady two-input/two-output gain matrix $K$, the relative gain array is $\Lambda=K\circ(K^{-1})^T$, where $\circ$ denotes elementwise multiplication. For

$$K=\begin{bmatrix}1&0.6\\0.4&1\end{bmatrix},\qquad \Lambda=\begin{bmatrix}1.315789&-0.315789\\-0.315789&1.315789\end{bmatrix}.$$

Diagonal pairing avoids negative relative gains here. RGA is a local steady-state diagnostic, not a stability proof: dynamics, delays and operating-point changes still matter. Static decoupling $u=K^{-1}v$ removes steady interaction for the nominal model, but can demand infeasible or rapidly changing physical inputs. If saturation occurs, the assumed decoupling is lost.

## Compare architectures under matched conditions

Start with independently tuned PI loops, then add measured-disturbance feedforward, cascade or decoupling for a stated reason. Keep the total available measurements explicit; a design with an additional disturbance sensor has an information advantage. Introduce one disturbance at a time, then simultaneous changes and model mismatch. Report output-by-output errors as well as a combined score. In Simulink, keep the physical plant, measurement path and controller subsystems separate so their responsibilities remain visible.

## Computational practice

From the repository root, run `python tools/run_course.py --unit 3`. Use the notebook to inspect assumptions, rerun calculations and compare them with the worked reasoning. The lesson's hypothetical examples illustrate the method; inspect each program's configuration before comparing numerical outputs.

# Benchmark case studies with worked reasoning

Each case links a modeling decision to an identification or control experiment. Numerical values are those of Kroll and Schulte (2014) unless a practice choice is explicitly labeled. Use the original paper for its historical comparisons; the calculations below are independent exercises, not copied problem statements.

## 1. Artificial SISO and MIMO systems (3.1)

**Task A.** Compute one SISO transition at y(k)=1, y(k−1)=2, u(k)=0.1, and one MIMO transition at y=[1,2], u=[0.1,0.2].

**Worked result.** Eq. (30) gives `1×2×3.5/(1+1×4)+0.1=1.5`. Eq. (31) gives `[1,2]/5+[0.1,0.2]=[0.3,0.6]`. These checks distinguish multiplication of both output squares from their sum and confirm the shared MIMO denominator.

**Task B.** Train a linear ARX baseline and nonlinear MLP/RBF or TS predictor with 100000 training samples, then use the specified periodic validation signals. State which errors use measured output history.

**Worked reasoning.** Estimate all scaling, features and parameters on the random-input training experiment. One-step output at k+1 uses measured y(k),y(k−1). Recursive validation replaces these by predictions; only initial history is measured. A low one-step RMSE can coexist with unstable free-run behavior. Save both traces and label their metrics separately. Fit an independent validation experiment rather than selecting a seed that looks favorable.

**Task C.** Explain why good performance on both recurrence examples does not prove industrial utility.

**Worked reasoning.** These recurrences have no sensor drift, actuator limits, safety states, model mismatch or physical units. They test nonlinear approximation and memory. They do not establish robustness to the operating regimes, disturbance structures and constraints of the later plant cases.

## 2. Data repositories (3.2)

**Task A.** Choose one dynamic DaISy record and one NIST nonlinear regression problem. Define their different validation goals before fitting.

**Worked reasoning.** The dynamic problem requires channel alignment, sample time, lag construction and chronology-preserving evaluation. NIST provides certified parameter values and a specified regression objective, so recovering those digits tests numerical accuracy. A random held-out score does not replace the certified-value comparison.

**Task B.** A dryer record has alternating missing outputs. May those outputs be interpolated using future observations before making a training/test split?

**Worked reasoning.** That would leak future information into lagged predictors. Preserve missingness, split complete experiments first, and fit any imputation using only information available at prediction time. Report the rows removed or imputed and compare against a complete-data subset where possible.

**Task C.** Design a minimal source record.

**Worked result.** Include provider URL, dataset title/version, file SHA-256, license, measured/synthetic status, column names/units, sample period, input/output alignment, preprocessing, split boundaries and checksum of the transformed file. [DATASETS.md](DATASETS.md) maps all named repository families and the review's tabulated examples.

## 3. Cart and inverted pendulum (3.3)

[Detailed TikZ schematic](figures/tikz/03-pendulum.png) · [Vector PDF](figures/tikz/03-pendulum.pdf) · [Editable TikZ](tikz/03-pendulum.tex) · [Diagram gallery](DIAGRAMS.md)

**Task A.** Linearize Eq. (32) at the upright equilibrium with zero friction and identify the unstable direction.

**Worked reasoning.** Let `a=1/(m+M)` and `d=2−ma`. To first order,

$$
\ddot\theta=\frac{g}{ld}\theta-\frac{a}{ld}u
-\frac{d_{Mf}}{ml^2d}\dot\theta,
\qquad
\ddot x=-\frac{amg}{d}\theta+\frac{2a}{d}u+
\frac{a d_{Mf}}{ld}\dot\theta.
$$
The positive gravitational coefficient accelerates a positive angular perturbation away from θ=0. State order is `[θ, θdot, x, xdot]`; assigning the cart angle to the wrong coordinate changes the feedback design.

**Task B.** Compare a local linear state-feedback law and a fuzzy/gain-scheduled controller.

**Worked protocol.** Use the same initial angular displacement, force limit ±120 N and 2 m rail. Report angular settling into ±0.1 rad, cart displacement and force effort. A stabilizer designed near upright is not a swing-up solution. Add a separate energy or nonlinear swing-up phase and a documented switch region if the initial condition is the hanging equilibrium.

**Task C.** Test mass/length and friction sensitivity.

**Worked reasoning.** Perturb positive m,M,l and vary Coulomb friction ±20%. The phrase ±100% cannot be implemented by making a mass or length zero, which makes the model singular. Use a strictly positive lower bound, report it and distinguish this practical choice from the printed range. Coulomb `sign(0)=0` omits stiction; high-frequency chattering is partly a model/integration issue.

## 4. Electromechanical throttle and local models (3.4, 4.1)

[Detailed TikZ schematic](figures/tikz/04-throttle.png) · [Vector PDF](figures/tikz/04-throttle.pdf) · [Editable TikZ](tikz/04-throttle.tex) · [Diagram gallery](DIAGRAMS.md)

**Task A.** Set up the eight-rule autoregressive predictor.

**Worked result.** Each local output is `a1_i y(k−1)+a2_i y(k−2)+b_i u(k−1)+a0_i`. Partition features are `[y(k−1)−y(k−2),u(k−1)]`. A PWA model selects one region; TS prediction averages local outputs using normalized memberships. `LocalARX` supplies a deterministic nearest-centroid/soft inverse-distance educational fit; it does not recover the article's trained coefficients.

**Task B.** Assess a measured validation record sampled at 10 ms.

**Worked protocol.** Keep the 10000-sample multisine training record separate from the 2500-sample quasi-modulated test record. Report angle in degrees, input duty in percent, maximum absolute error, RMSE, best-fit ratio and residual histogram. Preserve lag warmup when counting evaluated samples. Free-run prediction uses predicted output lags, while partition membership must use the same predicted histories.

**Task C.** Why is a simulated DC motor curve not a replacement dataset?

**Worked reasoning.** The benchmark intentionally captures unmodeled friction, nonlinear spring behavior and unknown physical parameters of a real throttle. A hand-tuned mechanistic model removes the very identification difficulty being studied. The original measured records were not recovered here; no measured-data score is asserted.

## 5. Servo-pneumatic actuator (3.5)

[Detailed TikZ schematic](figures/tikz/05-pneumatic.png) · [Vector PDF](figures/tikz/05-pneumatic.pdf) · [Editable TikZ](tikz/05-pneumatic.tex) · [Diagram gallery](DIAGRAMS.md)

**Task A.** Derive pressure dynamics from chamber volume changes.

**Worked result.** Volumes are `VI=V0+A x` and `VII=V0−A x`. Their time derivatives are `A xdot` and `−A xdot`. Compression/expansion therefore produces opposite signs in the pressure work terms. The pressure force `A(pI−pII)` is balanced against inertia and the stated viscous/Coulomb friction. The code retains the mass-flow directions of Eq. (33).

**Task B.** Identify what prevents a complete voltage-to-position reproduction from the review alone.

**Worked result.** The valve-voltage-to-orifice/mass-flow calibration, discharge factors, bypass law and κ are not fully specified. The [primary-source audit](PNEUMATIC_AUDIT.md) resolves the molar/specific gas-constant distinction and the gravity offset removed during local identification. The balance core accepts mass flows as arguments. A separate six-state physical variant implements reversible choked flow, gravity and mass/energy balances with declared valve and thermal choices; it is not a recovered apparatus calibration.

**Task C.** Design a controller comparison under payload change.

**Worked protocol.** Compare PI/cascade pressure control, fuzzy control and neural-model IMC using the same step, ramp and sinusoidal position references. Vary load mass from 3 to 9 kg while preserving the ±0.125 m stroke, voltage limits and positive chamber volumes. Score tracking RMSE, disturbance recovery, actuator effort and stroke violations. Do not report practice-closure scores as canonical pneumatic benchmark results.

## 6. Hydrostatic transmission (3.6)

[Detailed TikZ schematic](figures/tikz/06-hydrostatic.png) · [Vector PDF](figures/tikz/06-hydrostatic.pdf) · [Editable TikZ](tikz/06-hydrostatic.tex) · [Diagram gallery](DIAGRAMS.md)

**Task A.** Describe the four-state coupling and why two independent SISO designs can interact.

**Worked reasoning.** Pump and motor actuator positions feed the pressure-difference equation. Pressure and motor displacement generate torque, while speed feeds back into the hydraulic flow balance. Changing motor displacement alters both pressure demand and mechanical torque, so the speed and pressure loops share a nonlinear plant.

**Task B.** Audit the printed numerical parameterization before tuning.

**Worked result.** At a constant normalized unit input, the first-order pump position approaches 241.67, contradicting the listed ±1 angle limit. Numerical factors also mix cm³, mm⁵/N and pressure units. These issues cannot be fixed by interpreting every number as SI. The literal `hydrostatic_rhs` is useful for tracing the review but is explicitly unvalidated for physical vehicle simulation.

The [source review](HYDROSTATIC_SOURCE_REVIEW.md) now explains bar/mm³ conversion factors and the motor displacement in torque. The separate SI implementation requires explicit displacement/capacitance conventions and accepts requested normalized angles. Its energy balance, analytical limiting cases and cross-language trajectories are checked. The unresolved electrical gains and historical numeric conventions remain external requirements.

**Task C.** Plan a defensible multivariable control study once the original scaling is resolved.

**Worked protocol.** Reconcile Eq. (35) with the primary model reference, document each variable transformation, verify a steady operating point and reproduce a known trajectory. Then compare decoupling, TS/PDC or MPC on acceleration, constant-speed, reversal and load/road-slope cases. Record tracking IAE/RMSE, peak input and integrated squared control. Do not turn a missing road-to-wheel-load relation into an undisclosed arbitrary torque profile.

## 7. Three interacting tanks (3.7)

[Detailed TikZ schematic](figures/tikz/07-three-tanks.png) · [Vector PDF](figures/tikz/07-three-tanks.pdf) · [Editable TikZ](tikz/07-three-tanks.tex) · [Diagram gallery](DIAGRAMS.md)

**Task A.** Prove total-volume conservation.

**Worked result.** The signed square-root transfer q13 occurs with opposite signs in tanks 1 and 3; q32 does the same for tanks 3 and 2. Multiplying each level derivative by AT and summing gives `AT(h1dot+h2dot+h3dot)=q1+q2`. The test suite checks this identity at unequal levels and with drain faults.

**Task B.** Can constant positive pumps maintain constant levels in the nominal printed model?

**Worked result.** No. All nominal drains are closed, so positive net pumping increases total volume. A sustained tracking experiment must either use zero net inflow at equilibrium or introduce a documented drain configuration. `outlet_openings` implements a separate extension with `qout_i=alphaO AO sqrt(2g hi)`.

**Task C.** Separate sensor diagnosis from a physical leak.

**Worked reasoning.** A sensor bias changes the reported level without instantly changing the physical volume balance; a leak produces an unmodeled loss. A residual bank or SOM classifier should use both dynamical prediction and the volume-balance residual. Train on whole healthy/faulted runs and test on new fault times and magnitudes. Report false alarms, missed detections and detection delay, not just overall accuracy.

## 8. Biochemical reactor (3.8)

[Detailed TikZ schematic](figures/tikz/08-bioreactor.png) · [Vector PDF](figures/tikz/08-bioreactor.pdf) · [Editable TikZ](tikz/08-bioreactor.tex) · [Diagram gallery](DIAGRAMS.md)

**Task A.** Find nonwashout equilibria.

**Worked result.** Setting C1dot=0 with C1>0 gives `(1−C2)exp(C2/Γ)=u`. Substitution into C2dot=0 gives `C1=C2(1+β−C2)/(1+β)`. At u=0.769, Γ=0.4 and β=0.02, the relevant high-conversion root is `[0.0872975478,0.9235897741]`; this conflicts with the review's prose biomass. The discrepancy is reported in the notebook and results file.

**Task B.** Implement the sampled map correctly.

**Worked result.** Hold u fixed for 0.5 dimensionless time units and apply 50 forward-Euler steps of 0.01. The state passed to the second substep is the first substep's output. Applying only one Euler step per measurement changes the plant's effective time scale by a factor of 50.

**Task C.** Assess generalization and robustness.

**Worked protocol.** Train at multiple operating regimes and evaluate the stable u=0.75 and unstable u=1.25 regimes separately. Test parameter changes Γ=0.456, β=0.016 and Gaussian measurement noise σ=0.01 on both outputs. Keep true states and noisy observations distinct. Feed bounds, washout and physical-domain excursions must be recorded. Use an independently solved feasible reference rather than the inconsistent prose equilibrium.

## 9. Klatt–Engell chemical reactor (3.9)

[Detailed TikZ schematic](figures/tikz/09-cstr.png) · [Vector PDF](figures/tikz/09-cstr.pdf) · [Editable TikZ](tikz/09-cstr.tex) · [Diagram gallery](DIAGRAMS.md)

**Task A.** Reconcile the energy units.

**Worked result.** The Arrhenius denominator is T+273.15, so T values are Celsius. The cooling coefficient γ=0.1 has K/kJ units, whereas the cooling input is MJ/h. Thus the coolant derivative is `86.688(T−Tc)+0.1×1000×u2`. Omitting the factor 1000 prevents the printed operating points from approximately balancing.

**Task B.** Design a constrained transition experiment.

**Worked protocol.** Start from the equilibrated SP1 neighborhood and command SP2. Enforce `5≤u1≤35 h⁻¹`, `−8.5≤u2≤0 MJ/h`. Repeat with feed concentration falling from 5100 to 4500 mol/m³ after one minute and temperature noise uniform on ±0.1 K. Report the ±0.5% settling convention, overshoot, final bias, per-output squared scaled tracking deviation, and scaled input movement over the specified samples.

**Task C.** What changes if a controller is given all four true states?

**Worked reasoning.** The original problem measures only T and Tc and asks for concentration/disturbance and heat-transfer estimation. A full-state MPC simulation removes this observer problem. Such a simulation is a useful design stage, but a fair comparison must state the extra measurements and then implement/test an observer using only permitted signals.

## 10. Binary distillation Column A (3.10)

[Detailed TikZ schematic](figures/tikz/10-column-a.png) · [Vector PDF](figures/tikz/10-column-a.pdf) · [Editable TikZ](tikz/10-column-a.tex) · [Diagram gallery](DIAGRAMS.md)

**Task A.** Explain why there are 82 states.

**Worked result.** Each of 41 stages has a liquid light-component fraction xi and a liquid holdup Mi. The reboiler and total condenser each count as one stage. Vapor equilibrium is algebraic, so vapor composition does not add another state. The feed is stage 21 when counted from the bottom.

**Task B.** Verify a whole-column balance.

**Worked result.** All internal liquid/vapor flows cancel. The total balance is `sum(Midot)=F−D−B`. The light-component balance is `sum(Mi xidot+xi Midot)=F zF−D x41−B x1`. These identities catch an incorrect incoming-vapor index and wrong feed-stage handling even when a trajectory looks plausible.

**Task C.** Reduce the available manipulated inputs from four to two without deleting physical states.

**Worked reasoning.** In LV configuration use D and B to control condenser and reboiler inventory, respectively; retain L and V for composition control. The 82-state model remains. The practice wrapper uses P level gain 10/min and nonnegative product flows. Compare interaction/relative gains and constrained MPC using the same levels and feed disturbances. Report that level gain and saturation; they are controller choices rather than new plant physics.

## 11. ALSTOM Gasifier II (3.11)

[Detailed TikZ schematic](figures/tikz/11-gasifier.png) · [Vector PDF](figures/tikz/11-gasifier.pdf) · [Editable TikZ](tikz/11-gasifier.tex) · [Diagram gallery](DIAGRAMS.md)

**Task A.** Count independent manipulated variables.

**Worked result.** Five nominal mass-flow inputs reduce to four independent controls because limestone must follow coal in a fixed ratio. Optimizing all five independently violates the challenge configuration.

**Task B.** Choose an identification experiment and validation split.

**Worked protocol.** Use the official nonlinear simulator and bounded excitation of the four independent inputs. A Wiener model combines a dynamic linear block with a static nonlinear output map; compare it with a linear state-space baseline and a neural dynamic model. Separate complete operating/load experiments for fitting and validation, preserve original sample time and input constraints, and compare recursive as well as one-step predictions.

**Task C.** Define a fair control comparison.

**Worked reasoning.** Reuse the package's PI baseline and exactly specified step/harmonic sink-pressure, coal-quality and load scenarios. Score each controlled variable against its own tolerance and record input slew/magnitude violations. The [native ALSTOM study](ALSTOM_RESULTS.md) now records eleven cases and two additional nominal solver comparisons. All six pressure-disturbance cases exceed the temperature-error limit even though the applied input constraints hold within numerical tolerance. The nominal 50% temperature drift persists under the refined and author-default solver settings. Successful execution therefore establishes usable simulator evidence, not satisfactory PI control or complete historical benchmark reproduction. The separate long load-ramp and coal-quality results have not received this solver-refinement check.

## 12. Reduced and aeroelastic wind turbines (3.12)

[Detailed TikZ schematic](figures/tikz/12-wind-turbine.png) · [Vector PDF](figures/tikz/12-wind-turbine.pdf) · [Editable TikZ](tikz/12-wind-turbine.tex) · [Diagram gallery](DIAGRAMS.md)

**Task A.** Construct the state and mechanical energy.

**Worked result.** With four generalized coordinates q, four velocities qdot and one pitch actuator state, the reduced model has nine states. `E=0.5 qdotᵀM qdot+0.5 qᵀK q` has derivative `qdotᵀf−qdotᵀD qdot`. M must be positive definite; D and K are positive semidefinite. Common rotor/generator rotation is a rigid mode, so zero stiffness in that direction is expected, not a numerical singularity to erase.

**Task B.** Close the aerodynamic equations without hiding the source of CT/CQ.

**Worked result.** Effective wind is `v−(yTdot+yBdot)`, and λ=ωrR/veff. The map returns thrust/torque coefficients at λ and pitch. The included 2022 ROSCO table supplies a reproducible later-map variant; interpolation rejects extrapolation. It is not claimed to be the map underlying the article's exact numerical results.

**Task C.** Distinguish reduced control design from high-order verification.

**Worked reasoning.** Use the reduced model for controller synthesis and local sensitivity. Test with a pinned FAST/OpenFAST 5 MW case and documented wind files for loads and fault-tolerant verification. Partial-load energy capture and full-load speed limitation have different objectives. A small rotor-speed error alone does not establish low structural fatigue, acceptable pitch duty, or power quality.

**Task D.** Explain the TS/PDC controller example in Section 4.2 and the information needed to implement it.

**Worked reasoning.** Linearize a stated turbine model at a collection of operating points, express the regulation variables consistently, and check stabilizability before choosing local LQR weights and gains. In parallel distributed compensation (PDC), normalized nonnegative scheduling weights combine the local feedback laws. One explicit operating-point form is `u=sum_i h_i(rho) [u_i_star-K_i(x-x_i_star)]`, with `sum_i h_i=1`; the scheduling variable, state offsets, actuator limits and interpolation region must all be defined. Absolute rotation angles drift at nonzero nominal speed. Use rotor-speed/shaft-torsion or rotating-frame coordinates when defining the regulation equilibrium; absence of restoring stiffness alone does not imply uncontrollability.

A local LQR gain stabilizing each linearization does not by itself prove stability of the interpolated nonlinear closed loop. Rate limits, map validity, changing wind and scheduling transitions still need analysis and matched simulations. Reproducing the article's comparison requires its gains, weighting/membership definitions, operating points, rotor map, wind records and high-order validation configuration. The review does not supply that complete numerical package. The [executable wind study](WIND_CONTROL.md) now supplies new scaled LQR/PDC designs in Python and MATLAB/Octave, a corresponding Simulink diagram, nontrivial interpolated-wind trajectories and explicit rigid-structure/second-order-pitch variants. These are declared design choices; the outcomes in Table 12 are not claimed. A separate pinned OpenFAST successor case validates the external simulator against its own official baseline.

## 13. Tennessee Eastman (3.13)

[Detailed TikZ schematic](figures/tikz/13-tennessee-eastman.png) · [Vector PDF](figures/tikz/13-tennessee-eastman.pdf) · [Editable TikZ](tikz/13-tennessee-eastman.tex) · [Diagram gallery](DIAGRAMS.md) · [Signal reference](figures/tikz/13b-tennessee-eastman-signals.pdf)

**Task A.** Explain why a simple CSTR is not an equivalent benchmark.

**Worked result.** Tennessee Eastman couples a reactor, condenser, vapor–liquid separator, stripper and recycle compressor, with eight species, nonlinear equilibria and plantwide interactions. It has 12 manipulated inputs and 41 measured outputs. The original has 50 states. A one-vessel proxy omits most of this structure and its disturbance paths.

**Task B.** Select and document a simulator version.

**Worked reasoning.** The official original Fortran and the 2015 revised C/Simulink archives are available through the pinned downloader. Both the original model and the archived revised plant have 50 continuous states. The revised C source declares `NX=50`; an inconsistent parameter comment says 52. The [source audit](TE_STATE_COUNT_AUDIT.md) corrects earlier repository metadata without rerunning or changing the preserved trajectories. The revised version changes random/disturbance handling, and its additional optional outputs must be recorded. The original noise generator is sensitive to the solver-call sequence, so solver and step settings are part of the experimental definition.

**Task C.** Evaluate control and diagnosis without survivor bias.

**Worked protocol.** Verify nominal operation, then apply the official disturbance cases and operating-mode changes. Include every run, especially shutdowns and input saturation, when comparing controllers. Report product variability, recovery time, feed-valve movement and operational constraint violations. For diagnosis include false-alarm/missed-detection rates and delay per fault. The [revised simulator's native evidence](results/te-native/validation.json) covers nominal mode1, IDV1 and IDV4 for 0.2 h each; those checks do not establish the full operating-mode and fault-diagnosis comparison.

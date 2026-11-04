# Assumptions and limitations

## Course experiments

The common mixture is perfectly mixed, isothermal, constant-volume and single-phase. Its input changes immediately unless an actuator is explicitly added. Density, transport delay, nonlinear valve characteristics and sensor lag are not silently assumed to have been modeled. Course parameters are hypothetical.

PI/IMC pole calculations concern the stated continuous nominal model. Saturation, sampling, gain scheduling and neural model errors need separate analysis. Passing simulations does not establish global stability, safety or robustness on an industrial plant.

Identification uses independent training and evaluation trajectories. The ARX fit has noisy output regressors and therefore may be biased. MLP and RBF normalization is fit on training data only. One-step error, recursive free-run error and out-of-domain error are different questions. The neural controller is bounded model-based action selection, not a certified adaptive controller.

The MPC examples use a measured full state and a deterministic model. Python enforces input/move constraints and one MIMO example also constrains predicted states; its solver-failure handling records failures and holds the previous feasible command. MATLAB/Octave enforces input box constraints only and returns the last bounded projected-gradient iterate at its iteration limit, without the same failure-hold logic. Neither implementation includes state estimation, robust invariant sets or a terminal stability proof. Input feasibility does not guarantee future output feasibility.

Expert rules are illustrative thresholds. Fuzzy memberships, rule surfaces, learning hyperparameters and GA budgets are declared experimental choices. A single seeded search does not demonstrate optimizer superiority. The small nested GA/MPC example demonstrates the workflow and reports evaluations, not convergence to a global optimum.

The capstone uses matched uncertainty cases and a common sensor-noise seed. Feedforward has a disturbance measurement unavailable to the other controllers. Aggregate metrics include multiple setpoint segments; ITAE is measured from the beginning of the whole experiment. No universal ranking is implied.

## Markov chains and hidden-state diagnosis

Unit 09 is an enrichment beyond the supplied eight-unit syllabus and the article's benchmark inventory. Its hidden states describe sensor modes, not a new physical tank model. The transition matrix, positive sensor biases, independent Gaussian noise and residual cutpoints are declared teaching choices. Calibration labels are available only because the trajectories are synthetic; real deployments need labeled fault records or a separately justified identification strategy.

Twenty independent calibration trajectories are kept separate during parameter estimation. An independent seeded test is used only for scoring; thresholds and model settings are fixed beforehand. The continuous compensation biases are estimated only from calibration data. Baum–Welch fits symbols without labels, can reach a local optimum and cannot identify semantic state names without additional information. This demonstration starts EM at the known simulator transition, initial and theoretical emission probabilities: a favorable initialization, not blind identification from unknown operating conditions. Its states are not relabeled using held-out labels.

Filtering is causal; full-record smoothing and Viterbi are retrospective and never enter the controller. Conditional independence of residual emissions is exact for the nominal synthetic generator, but generally fails when the predictor is wrong or residuals are autocorrelated. The compensated PI has an additional nominal model, a known initial concentration and known past inputs. It therefore has an information advantage over ordinary PI. The changed residence-time case exposes confounding between model error and sensor faults. One seeded comparison does not establish a universal performance improvement or safe fault-tolerant operation.

The sensor chain permits recovery. Making the fault state absorbing is an explicitly hypothetical variant. First passage to fault and long-run occupancy are different quantities; expected first-passage time is infinite for starting states that do not reach the target almost surely.

## Article models and software environments

The separate [physical Blending Tank](../blending-tank/README.md) uses an explicitly chosen density of 1000 kg/m³, mass-flow units and a 2 m³ reference volume. Its 700 kg/min outlet case defines equilibrium; its 650 kg/min outlet case fills the vessel. Its matrices are derived from the stated conservation equations and operating point. The finite-volume guard prevents evaluation through an empty tank, but no upper vessel capacity or physical protection system is modeled. Numerical Python/Octave checks and actual Simulink execution are recorded separately.

Read the [benchmark inventory](../benchmarks/README.md) before interpreting a result as reproduction of a published benchmark. Missing measured data, unprovided valve laws, rotor maps, implementation variants and inaccessible plant distributions are material scientific limitations. A closure supplied for teaching is labeled separately from the paper equations.

MATLAB, GNU Octave, Simulink and Python are different execution environments. Shared model equations do not imply bitwise numerical agreement. The [validation record](VALIDATION.md) states which environments were actually exercised.

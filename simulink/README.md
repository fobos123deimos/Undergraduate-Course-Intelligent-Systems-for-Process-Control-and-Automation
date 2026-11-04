# Simulink model generation

`build_models` builds eight executable `.slx` diagrams using MATLAB with Simulink:

1. Variable-volume Blending Tank with five physical input quantities.
2. Inverted pendulum using the published nonlinear equations.
3. Three coupled tanks with nominal drains closed.
4. Bioreactor at the equilibrium calculated from its equations.
5. CSTR from the article's first rounded operating point.
6. The 82-state Column A balance.
7. Concentration PI control with actuator saturation and anti-windup.
8. Discrete 2x2 constrained model predictive control.

```matlab
addpath('matlab'); addpath('simulink');
paths = build_models();
load_system(paths{7});
result = sim('si_tank_pi');
plot(result.concentration.time, result.concentration.signals.values);
close_system('si_tank_pi',0);
```

The plant adapters call the same `paper_models` and `blending_rhs` functions used in the numerical laboratories. They expose physical states directly. The article's pneumatic plant lacks its valve-flow equations; hydrostatic units require reconciliation, and the wind example requires its coefficient-map variant. These are studied in MATLAB/Octave rather than silently packaged as fully reproduced industrial models.

Output files go to `simulink/generated/`. Existing files and loaded models are refused by default. Use `build_models(output_dir,true)` only when explicitly intending to replace files in that directory. The function creates models without opening windows and closes each saved model.

No generated `.slx` output or MATLAB/Simulink execution is claimed unless the validation record explicitly says so. The historical models under `legacy/` are supplied originals, not outputs of this generator. Their old S-function and numerical inconsistencies are documented separately.

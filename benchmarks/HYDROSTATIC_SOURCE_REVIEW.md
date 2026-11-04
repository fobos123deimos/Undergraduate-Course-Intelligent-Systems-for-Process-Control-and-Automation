# Hydrostatic transmission source review

The literal form of Kroll and Schulte's (2014) equation (35) remains in `benchmarks.py` and `paper_models.m`. The separate `hydrostatic_si` variant reconstructs a dimensionally consistent model. It resolves implementation inconsistencies, but **does not reproduce an authenticated calibration or Schulte's (2007) numerical results**.

## Primary sources and access

Checked on November 4, 2026. PDF page numbers below are one-based and include covers and contents pages.

| Source | Evidence used | Access |
|---|---|---|
| [Schulte, FUZZ-IEEE 2007, DOI 10.1109/FUZZY.2007.4295677](https://doi.org/10.1109/FUZZY.2007.4295677) | This is Table 5's reference [79], rather than Kugi (2000). | Metadata confirmed; full text not retrieved. IEEE presented an access verification page; the public OpenAlex record did not identify an open copy. |
| [Schulte, Workshop Computational Intelligence 2006, pp. 62–70](https://publikationen.bibliothek.kit.edu/1000005189/3236) | Printed p. 65, PDF p. 77, eqs. (6)–(8): hydraulic/mechanical power, reduced displacement `Ṽ=V/(2π)` and motor torque using motor displacement. Printed p. 64, PDF p. 76: current-driven actuation. | Open institutional full text retrieved from KIT. |
| [Schulte, Workshop Computational Intelligence 2008, pp. 90–104](https://publikationen.bibliothek.kit.edu/1000009271/645011) | Printed pp. 93–95, PDF pp. 105–107, eqs. (1)–(16): normalized angles, reduced displacement, hydraulic balance and torque. The note after (16) declares pressure in **bar** and displacement in **mm³**. The chapter cites the 2007 paper. | Open institutional full text retrieved from KIT; equations and units also inspected on the rendered page. |
| [Schulte and Gerland, EUSFLAT 2011, DOI 10.2991/eusflat.2011.18](https://www.atlantis-press.com/article/2203.pdf) | Printed p. 800, PDF p. 4, eqs. (12)–(16): normalized angles and torque using **motor** displacement. This is an extension to power-split transmissions. | Open publisher full text retrieved. |
| [Kroll and Schulte, 2014, DOI 10.1016/j.asoc.2014.08.034](https://doi.org/10.1016/j.asoc.2014.08.034) | Printed pp. 502–503, PDF pp. 7–8: eq. (35), Table 5 and reference [79]. | Supplied PDF inspected; an [institutional preprint](https://mrt-pc2.mrt.maschinenbau.uni-kassel.de/MRT/Veroeffentlichungen/Online/2014-Kroll_Schulte-ASC-Benchmark.pdf) was also located. |

The 2007 IFAC paper, DOI `10.3182/20071029-2-FR-4913.00018`, was located in the publisher catalog but was not used as an inspected full text. No restricted access or author contact was used. The full source PDFs are not redistributed in this repository; URLs and hashes are recorded in `hydrostatic_sources.json`.

## What the source comparison establishes

In the bar/mm³ convention stated in 2008, `10/C_H` converts `N/mm²/s` to `bar/s`, and `10^-4` converts `bar·mm³` to `N·m`. Those numerical factors cannot remain unchanged when pressure is expressed in Pa and volume in cm³. Table 5 of the 2014 survey uses these different labels. The SI variant converts all parameters before evaluating derivatives.

The 2006 torque derivation, equation (13) of 2008 and equation (15) of 2011 use motor displacement. The combined 2008 equation and equation (35) of 2014 print the pump-volume symbol in that term. This is an inconsistency between source equations. The separate variant uses motor displacement to satisfy the power balance; **it does not claim that an official erratum exists**.

Three numerical choices remain unresolved:

- **Displacement:** Table 5 associates 145/170 cm³ with the symbol `Ṽ`, whereas the derivation distinguishes swept volume per revolution from reduced displacement per radian. The numerical convention in the 2007 publication could not be confirmed. The constructor requires `per_revolution` or `per_radian`.
- **Capacitance:** the 2008 text introduces equal capacitances for two lines and a reduction with approximately constant charge pressure. For two closed, equally compressible lines, the full balance gives `C_Δ=C_line/2`; an already reduced capacitance is used directly as `C_Δ`. The constructor requires `per_line` or `effective`, keeping the assumptions distinct.
- **Actuators:** no verified electrical calibration was found for the gains 241.67 and 283.33. Directly applying them when both commands and states are normalized can drive angles outside their declared bounds. The new input is the **requested normalized angle** `r=k·u`, not voltage or current. Its unit gain follows from this input-coordinate definition; it is not an estimate of the physical actuator gain. Connecting hardware requires a separately identified mapping from the electrical signal to `r`.

## Implemented SI model

The state is `x=[a_P,a_M,p,ω_M]`, with normalized angles, differential pressure in Pa and motor speed in rad/s. Define `D_P,D_M` in m³/rad, `C_Δ` in m³/Pa, `L` in m³/(s·Pa), `g=i_g i_a`, `J=J_v/g²`, `b=d_vc/i_g²` and `η=η_g η_mh`:

```text
da_P/dt = (r_P-a_P)/τ_P
da_M/dt = (r_M-a_M)/τ_M
dp/dt   = (D_P a_P ω_P - D_M a_M ω_M - L p)/C_Δ
dω_M/dt = (η D_M a_M p - b ω_M - T_Lw/g)/J
```

Invalid angular states and commands are rejected without hidden saturation. Pressure and speed may be signed. `T_Lw>0` denotes a load opposing positive wheel speed.

The example explicitly chooses 145/170 cm³ **per revolution**, `D=V/(2π)`, `C_Δ=1840.8·10^-15 m³/Pa` and `L=0.14·10^-14 m³/(s·Pa)`. Other numbers follow Table 5 with their physical units preserved. The six-second trajectory starts at equilibrium, uses a pump speed of 180 rad/s and a 5000 N·m wheel load, and applies a small smooth pump-reference variation. These are simulation data, not measurements or a fit to external observations.

The balance uses stored energy `E=C_Δ p²/2+J ω_M²/2` and checks:

```text
dE/dt = p Q_P - T_Lw ω_M/g - L p² - b ω_M² - (1-η) p Q_M
```

`p Q_P` is power at the pump's hydraulic port, not combustion-engine shaft power. Actuator energy is excluded. Conversion loss is nonnegative during motoring, `p Q_M>=0`. In regeneration, the constant-efficiency approximation is not a passive four-quadrant law; `motoring_valid=false` makes this limitation detectable. No arbitrary efficiency map, relief-valve model or cavitation model has been added.

## Execution and evidence

```bash
PYTHONPATH=python python -m intelligent_control.hydrostatic_si
PYTHONPATH=python python -m pytest tests/test_hydrostatic_si.py -q
```

```matlab
addpath('matlab');
r = validate_hydrostatic_si();
study = run_hydrostatic_si();
plot(study.t, study.x(:,3)/1e6); ylabel('Differential pressure [MPa]');

% Requires MATLAB with Simulink; creates one separate additional model.
addpath('simulink');
validate_hydrostatic_simulink(fullfile('simulink','generated-hydrostatic'));
```

Python's `table5_interpretation(...)` and MATLAB's `hydrostatic_si_parameters(...)` require both conventions. The demonstration selects them explicitly; execution does not depend on private machine paths.

Eight Python tests and eight validation groups passed in GNU Octave 11.3.0 for Windows. They include independent evaluation in bar/mm³, motor torque, mechanical gear power, exponential pressure decay, analytical actuator response, a lossless matrix-exponential solution, energy conservation, integration-step refinement and invalid-input rejection. Numerical evidence is in `results/hydrostatic-si/`. Simulink execution produces its own validator report because GNU Octave does not execute Simulink.

Implementation agreement and conservation identities do not establish experimental calibration. Reproducing the historical benchmark still requires the complete 2007 text, numerical volume/capacitance conventions, actuator calibration and the original initial conditions and driving profiles.

# Benchmarks across the nine learning units

[Original article names and detailed TikZ atlas](../DIAGRAMS.md) · [Complete vector PDF](../figures/tikz/benchmark-atlas.pdf)

Each native case below has two freshly generated nonlinear records, a training-only scalar model fit and all nine computational stages. The later control curves are explicitly **local fitted-predictor exercises**, not nonlinear-apparatus validation. Full-order and measured-data gaps are retained.

| Unit | Computation and illustrated results |
|---|---|
| 01 | [Identification and simulation](unit-01.md) |
| 02 | [Feedback and nominal stability](unit-02.md) |
| 03 | [Feedforward and cascade structures](unit-03.md) |
| 04 | [Constrained predictive control](unit-04.md) |
| 05 | [Expert and fuzzy control](unit-05.md) |
| 06 | [Neural identification](unit-06.md) |
| 07 | [Evolutionary tuning](unit-07.md) |
| 08 | [Integration and uncertainty](unit-08.md) |
| 09 | [Markov chains and hidden sensor modes](unit-09.md) |

## Case index

| Case | Record | Scope |
|---|---|---|
| [Artificial SISO](cases/artificial_siso.md) | Section 3.1 / Eq. 30 | Nonlinear excitation + nine local learning stages |
| [Artificial MIMO](cases/artificial_mimo.md) | Section 3.1 / Eq. 31 | Nonlinear excitation + nine local learning stages |
| [Inverted pendulum](cases/pendulum.md) | Section 3.3 / Eq. 32 | Nonlinear excitation + nine local learning stages |
| [Pneumatic actuator](cases/pneumatic.md) | Section 3.5 | Nonlinear excitation + nine local learning stages |
| [Hydrostatic drive](cases/hydrostatic.md) | Section 3.6 | Nonlinear excitation + nine local learning stages |
| [Three tanks](cases/three_tank.md) | Section 3.7 / Eq. 36 | Nonlinear excitation + nine local learning stages |
| [Bioreactor](cases/bioreactor.md) | Section 3.8 / Eq. 37 | Nonlinear excitation + nine local learning stages |
| [CSTR](cases/cstr.md) | Section 3.9 / Eqs. 39-43 | Nonlinear excitation + nine local learning stages |
| [Column A](cases/column_a.md) | Section 3.10 | Nonlinear excitation + nine local learning stages |
| [Reduced wind turbine](cases/wind_reduced.md) | Section 3.12 and 4.2 | Nonlinear excitation + nine local learning stages |
| [ALSTOM gasifier](cases/gasifier.md) | Section 3.11 | Archived native trace + forecast/sensor audit; controller redesign pending |
| [High-order OpenFAST](cases/wind_fast.md) | Section 3.12 | Archived native trace + forecast/sensor audit; controller redesign pending |
| [Tennessee Eastman](cases/tennessee_eastman.md) | Section 3.13 | Archived native trace + forecast/sensor audit; controller redesign pending |
| [Throttle](../THROTTLE_RECOVERY.md) | Sections 3.4 and 4.1 | Original measured records unavailable; fixture tests are not replacement measurements |
| [Dataset repositories](../DATASETS.md) | Section 3.2 | Source register and strict importer; a resource collection is not a dynamical plant |

## Reproduce and interpret

Run `python benchmarks/run_learning_studies.py`. Machine-readable data are in [results/learning](../results/learning/summary.json); each case stores physical input/output records, fit statistics, traces and scores. Fixed seeds are 1401/2401 for training/test generation and 19 for learning. Report the channel, physical units and case qualification when using a figure.

The ten native cases yield 90 executed learning-stage entries. The three external families have additional offline analyses, while throttle measurements and a chosen historical dataset remain explicit dependencies. Thus this is not a claim of 135 full-order controller validations. See [coverage and source audit](../README.md).

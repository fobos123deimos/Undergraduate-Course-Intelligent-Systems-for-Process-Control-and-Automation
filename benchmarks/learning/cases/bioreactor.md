# Bioreactor: nine-stage worked study

Original article name: **Continuously operated bio-chemical reactor**, section **3.8**. [Detailed TikZ plate](../../figures/tikz/08-bioreactor.pdf) · [Editable source](../../tikz/08-bioreactor.tex) · [Original-name index](../../DIAGRAMS.md).

Article section **3.8 / Eq. 37**. Paper sampled model: 50 Euler substeps of 0.01 per 0.5 hold.

The selected channel is **dilution (dimensionless) → biomass (dimensionless)**, with time in **dimensionless**. All generated records are synthetic. A first-order predictor omits other states and possible channel interactions; its control exercise must not be mistaken for full-plant validation.

![Detailed benchmark equipment and physical channels](../../figures/tikz/08-bioreactor.png)

![Computed nine-stage results](../figures/bioreactor.png)

| Stage | Worked explanation |
|---|---|
| 1 | [Identification and simulation](../unit-01.md) |
| 2 | [Feedback and nominal stability](../unit-02.md) |
| 3 | [Feedforward and cascade structures](../unit-03.md) |
| 4 | [Constrained predictive control](../unit-04.md) |
| 5 | [Expert and fuzzy control](../unit-05.md) |
| 6 | [Neural identification](../unit-06.md) |
| 7 | [Evolutionary tuning](../unit-07.md) |
| 8 | [Integration and uncertainty](../unit-08.md) |
| 9 | [Markov chains and hidden sensor modes](../unit-09.md) |

[Physical training record](../../results/learning/bioreactor-train.csv) · [Independent test record](../../results/learning/bioreactor-test.csv) · [Numerical results and controller traces](../../results/learning/bioreactor.json)

Read the identification panel before trusting a control curve. A large free-run error, a weak input coefficient or extrapolation beyond the excitation region invalidates an apparatus-level interpretation even when the scalar predictor tracks its target. The external-source and conservation audits remain in [the benchmark guide](../../README.md).

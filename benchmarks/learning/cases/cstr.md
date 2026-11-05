# CSTR: nine-stage worked study

Original article name: **Continuously stirred chemical reactor**, section **3.9**. [Detailed TikZ plate](../../figures/tikz/09-cstr.pdf) · [Editable source](../../tikz/09-cstr.tex) · [Original-name index](../../DIAGRAMS.md).

Article section **3.9 / Eqs. 39-43**. Rounded SP1 initial state; dilution held at 8.256/h; short excitation around -6.239 MJ/h.

The selected channel is **cooling (MJ/h) → reactor temperature (deg C)**, with time in **h**. All generated records are synthetic. A first-order predictor omits other states and possible channel interactions; its control exercise must not be mistaken for full-plant validation.

![Detailed benchmark equipment and physical channels](../../figures/tikz/09-cstr.png)

![Computed nine-stage results](../figures/cstr.png)

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

[Physical training record](../../results/learning/cstr-train.csv) · [Independent test record](../../results/learning/cstr-test.csv) · [Numerical results and controller traces](../../results/learning/cstr.json)

Read the identification panel before trusting a control curve. A large free-run error, a weak input coefficient or extrapolation beyond the excitation region invalidates an apparatus-level interpretation even when the scalar predictor tracks its target. The external-source and conservation audits remain in [the benchmark guide](../../README.md).

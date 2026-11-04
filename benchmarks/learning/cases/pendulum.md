# Inverted pendulum: nine-stage worked study

Article section **3.3 / Eq. 32**. Short upright-window experiment; cart Coulomb friction explicitly set to zero, as in the existing local study.

The selected channel is **force (N) → angle (rad)**, with time in **s**. All generated records are synthetic. A first-order predictor omits other states and possible channel interactions; its control exercise must not be mistaken for full-plant validation.

![Equipment and physical channels](../../figures/03-pendulum.png)

![Computed nine-stage results](../figures/pendulum.png)

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

[Physical training record](../../results/learning/pendulum-train.csv) · [Independent test record](../../results/learning/pendulum-test.csv) · [Numerical results and controller traces](../../results/learning/pendulum.json)

Read the identification panel before trusting a control curve. A large free-run error, a weak input coefficient or extrapolation beyond the excitation region invalidates an apparatus-level interpretation even when the scalar predictor tracks its target. The external-source and conservation audits remain in [the benchmark guide](../../README.md).

**Negative control result.** The illustrated pendulum predictor does not follow the reference under the tested policies. Its fitted pole is 1.00799, input coefficient is -0.000255953, and affine drift is 0.0115705, in training-normalized coordinates. With commands limited to [-2, 2], the weak input effect cannot counteract the drift along this trajectory; the output continues to move away from the target. A status of `completed` records that the numerical loop finished, not that tracking or stabilization passed. These curves are retained as negative evidence. Establishing pendulum stabilization requires the full cart-pendulum state model, a justified operating point, adequate control authority and a separately validated controller.

# 03. Multiloop, feedforward and cascade structures

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/blob/main/laboratories/03-control-structures/notebook.ipynb)

A measured inlet disturbance can be canceled nominally by $u=v-d$.
A cascade loop measures the fast actuator variable and closes an inner loop
before the slower concentration controller. Multivariable interactions are
summarized by $\Lambda=K\circ(K^{-1})^T$; a static decoupler $K^{-1}$
cancels steady interaction, not all transient dynamics. Compare only cases
with the same disturbance location and measurement information.

```bash
python tools/run_course.py --unit 3
```

[Notebook](notebook.ipynb) · [Metrics](results/metrics.json) · [Course notes](../../course/README.md) · [Problems and solutions](../../problem-sets/README.md)

![Computed comparison](results/comparison.png)

## Read the method visually

![Unit 03 conceptual diagram](../../course/figures/learning/unit-03.png)

The short inner path uses the measured actuator/flow variable; the long outer path uses concentration. Cascade can correct an actuator disturbance before it strongly affects concentration. Compare it only with the single-loop case having that same actuator. The feedforward pair is a separate comparison, and its disturbance measurement is additional information.

The conceptual diagram is deliberately separate from the computed experiment below. [Editable SVG](../../course/figures/learning/unit-03.svg).

## Apply this unit to the article benchmarks

[Worked benchmark study for Unit 03](../../benchmarks/learning/unit-03.md)

![Unit 03 benchmark study](../../benchmarks/learning/figures/unit-03.png)

Read the per-model method, chosen signals, numerical results and interpretation in the linked study. The learning track declares its local-model approximations and separates equation-based experiments from external datasets and simulators. It does not turn an unavailable measured record into a synthetic benchmark result.

# 04. Constrained model predictive control

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/blob/main/laboratories/04-model-predictive-control/notebook.ipynb)

At each sample solve
$\min_U\sum_{j=1}^{N_p}\|\hat x_{k+j}-r\|_Q^2+
\sum_{j=0}^{N_c-1}\|\Delta u_{k+j}\|_R^2$,
subject to $\hat x^+=A\hat x+B u$, actuator bounds and move bounds.
Only the first optimized action is applied. Beyond the control horizon, hold
the final move. Inspect solver failures as well as tracking error.
The second experiment uses two coupled states and two constrained inputs.

```bash
python tools/run_course.py --unit 4
```

[Notebook](notebook.ipynb) · [Metrics](results/metrics.json) · [Course notes](../../course/README.md) · [Problems and solutions](../../problem-sets/README.md)

![Computed comparison](results/comparison.png)

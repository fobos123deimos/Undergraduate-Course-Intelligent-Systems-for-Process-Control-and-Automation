# 02. Feedback, stability and IMC tuning

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/blob/main/laboratories/02-feedback-imc/notebook.ipynb)

The IMC-inspired PI tuning for a FOPDT approximation is
$K_p=\tau/[K(\lambda+\theta)]$, $K_i=K_p/\tau$.
For the nominal tank, the characteristic polynomial is
$10s^2+(1+K_p)s+K_i$. Positive coefficients establish stability of this
second-order continuous nominal loop. Saturation and sampling still require
separate simulation. Conditional integration prevents an integral state
from growing while it would drive a saturated actuator further outward.

```bash
python tools/run_course.py --unit 2
```

[Notebook](notebook.ipynb) · [Metrics](results/metrics.json) · [Course notes](../../course/README.md) · [Problems and solutions](../../problem-sets/README.md)

![Computed comparison](results/comparison.png)

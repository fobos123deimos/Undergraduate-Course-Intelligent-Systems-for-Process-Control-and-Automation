# 01. Modeling, identification and simulation

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/blob/main/laboratories/01-modeling-identification/notebook.ipynb)

A well-mixed, constant-volume tank obeys $V\dot c=q(u-c)$.
With $V=100$ L and $q=10$ L/min, $G(s)=1/(10s+1)$ and
$c_{k+1}=a c_k+(1-a)u_k$, where $a=\exp(-T_s/10)$.
Estimate an ARX model from a persistently exciting experiment, then assess
one-step prediction and recursive free-run on a fresh input sequence.
Noise on the autoregressive regressor can bias least squares; a small residual
does not prove physical parameter accuracy.

```bash
python tools/run_course.py --unit 1
```

[Notebook](notebook.ipynb) · [Metrics](results/metrics.json) · [Course notes](../../course/README.md) · [Problems and solutions](../../problem-sets/README.md)

![Computed comparison](results/comparison.png)

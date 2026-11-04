# 06. Neural identification and control

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/blob/main/laboratories/06-neural-identification-control/notebook.ipynb)

The illustrative nonlinear transition is
$c^+=u+(c-u)\exp[-T_s(1+0.6c)/10]$. It freezes the flushing coefficient
over a sample and is explicitly different from the article benchmarks.
Fit a tanh MLP and a Gaussian RBF network with normalization learned on
training inputs only. Validate untouched transitions, a recursive trajectory
and out-of-domain points separately. The controller evaluates bounded actions
through the trained MLP. Perceptron classification and SOM clustering use the
same input domain to illustrate distinct learning objectives.

```bash
python tools/run_course.py --unit 6
```

[Notebook](notebook.ipynb) · [Metrics](results/metrics.json) · [Course notes](../../course/README.md) · [Problems and solutions](../../problem-sets/README.md)

![Computed comparison](results/comparison.png)

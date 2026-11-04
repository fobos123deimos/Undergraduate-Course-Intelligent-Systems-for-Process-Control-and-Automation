# 07. Evolutionary controller tuning

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/blob/main/laboratories/07-evolutionary-tuning/notebook.ipynb)

Encode $(K_p,K_i)$ as bounded real values or 12-bit binary chromosomes.
Use tournament selection, crossover, mutation and elitism to minimize
$J=\mathrm{IAE}+0.03\sum_k|u_k-u_{k-1}|$. Equal population and generation
counts give equal numbers of objective evaluations, not equal wall-clock cost.
Report the seeded search and test its gains on a changed residence time.
A small outer search also tunes a MIMO MPC move penalty; it is not a claim
of a global optimum.

```bash
python tools/run_course.py --unit 7
```

[Notebook](notebook.ipynb) · [Metrics](results/metrics.json) · [Course notes](../../course/README.md) · [Problems and solutions](../../problem-sets/README.md)

![Computed comparison](results/comparison.png)

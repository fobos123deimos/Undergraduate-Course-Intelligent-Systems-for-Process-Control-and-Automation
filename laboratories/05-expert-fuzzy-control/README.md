# 05. Expert supervision and fuzzy control

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/blob/main/laboratories/05-expert-fuzzy-control/notebook.ipynb)

Crisp supervisory rules produce traceable diagnoses. Fuzzy inference
instead represents graded membership. Mamdani uses min firing, max aggregation
and centroid defuzzification; Sugeno uses a normalized weighted average of
singleton consequents. The nine rules here form a PD-like surface used in an
incremental PI law. A separate example schedules PID gains. None of these
finite scenarios establishes global closed-loop stability.

```bash
python tools/run_course.py --unit 5
```

[Notebook](notebook.ipynb) · [Metrics](results/metrics.json) · [Course notes](../../course/README.md) · [Problems and solutions](../../problem-sets/README.md)

![Computed comparison](results/comparison.png)

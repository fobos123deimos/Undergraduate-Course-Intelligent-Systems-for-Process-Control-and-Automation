# 08. Integrated validation and robustness

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/blob/main/laboratories/08-integrated-validation/notebook.ipynb)

Compare PI, fuzzy gain PID and feedforward PI at residence times 7,
10 and 14 min, using the same sensor-noise seed and reference/disturbance
schedule. Report IAE, ISE, ITAE, actuator energy, movement and violations.
Feedforward receives a disturbance measurement, so its information advantage
must be stated. These are synthetic matched scenarios, not measured evidence
or statistical confidence bounds. A final recommendation must state which
constraint or uncertainty determines the preferred controller.

```bash
python tools/run_course.py --unit 8
```

[Notebook](notebook.ipynb) · [Metrics](results/metrics.json) · [Course notes](../../course/README.md) · [Problems and solutions](../../problem-sets/README.md)

![Computed comparison](results/comparison.png)

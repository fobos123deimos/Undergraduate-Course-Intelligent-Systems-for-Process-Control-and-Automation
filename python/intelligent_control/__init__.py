r"""Intelligent Systems for Process Control and Automation.

Python API for nine connected laboratories, the article benchmark track and
separate physical process models. The collection follows the same Python,
MATLAB/Octave, Simulink and LaTeX stack as the Control of Dynamical Systems
repository. This reference documents the Python source; the other language
implementations and their execution evidence remain in the course repository.

## Start here

- [Course and laboratory guide](https://github.com/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation#nine-connected-laboratories)
- [Worked problems and solutions](https://github.com/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/tree/main/problem-sets)
- [Article models and reproduction boundaries](https://github.com/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/blob/main/benchmarks/README.md)
- [Validation evidence](https://github.com/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/blob/main/docs/VALIDATION.md)
- [MATLAB/Octave](https://github.com/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/tree/main/matlab)
  and [27 Simulink models](https://github.com/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/tree/main/simulink/models)

## API map

| Module | Purpose |
|---|---|
| `intelligent_control.methods` | Mixing plant, identification, PI/PID, MPC, fuzzy rules, neural models and genetic search |
| `intelligent_control.experiments` | Nine laboratory scenarios, fair comparisons and saved experiment outputs |
| `intelligent_control.markov` | Finite chains, first passage, categorical HMM filtering, smoothing, Viterbi and estimation |
| `intelligent_control.markov_lab` | Independent calibration, hidden sensor modes, fault scoring and causal supervision |
| `intelligent_control.physical_blending` | Physical tank balances, equilibrium, Jacobians, transfer functions and variable volume |
| `intelligent_control.benchmarks` | Ten article equation cores, local ARX predictors, rotor maps and external interfaces |
| `intelligent_control.pneumatic_physical` | Separate six-state, conservative pneumatic mass/energy interpretation |
| `intelligent_control.hydrostatic_si` | Separate hydrostatic SI interpretation with explicit displacement and capacitance conventions |
| `intelligent_control.wind_control` | Local LQR/PDC design, scheduling, actuator limits and nonlinear wind studies |

## Run a first example

Clone the repository, install `requirements.txt`, and run from its root:

```python
import sys
sys.path.insert(0, "python")

import numpy as np
from intelligent_control import physical_blending, markov

x_eq = physical_blending.equilibrium()
np.testing.assert_allclose(physical_blending.rhs(x_eq), [0.0, 0.0], atol=1e-14)

P = np.array([[0.95, 0.05], [0.20, 0.80]])
distribution = markov.n_step_distribution([1.0, 0.0], P, steps=10)
np.testing.assert_allclose(distribution.sum(), 1.0)
```

The physical tank has state `[X, V]` (solute mass fraction and volume in m³),
mass-flow inputs in kg/min and time in minutes. Its conservative solute balance is

$$\frac{d(\rho V X)}{dt}=w_1x_1+w_2x_2-w_{out}X.$$

The simpler laboratory plant in `intelligent_control.methods` uses a separate
constant-volume teaching convention. Read each module's units before combining
models. Arrays are NumPy arrays; individual functions state their shape and
state/input order. No module runs a laboratory merely by being imported.

## Laboratories and notebooks

Use `python tools/run_course.py --unit 9` for the Markov/HMM laboratory or
`python tools/run_course.py --all` for all nine. The
[eleven notebooks](https://github.com/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/blob/main/README.md)
include nine course labs, benchmarks and the physical Blending Tank. They call
the same inspectable Python functions documented here.

## Interpretation and evidence

The teaching experiments are synthetic. Numerical agreement, conservation and
successful integration do not establish experimental calibration or industrial
controller suitability. HMM filtering is causal; full-record smoothing and
Viterbi decoding are retrospective and must not enter an online controller.

Original throttle measurements remain unavailable. Pneumatic and hydrostatic
physical interpretations remain separate from the literal survey equations.
OpenFAST, Tennessee Eastman and ALSTOM have their own source/runtime requirements;
their preserved native results are described in the
[external-model guide](https://github.com/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/blob/main/benchmarks/EXTERNAL_MODELS.md).
The ALSTOM PI's recorded output violations are not successful control results.

See the [coverage review](https://github.com/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/blob/main/docs/COVERAGE_REVIEW.md)
and [limitations](https://github.com/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/blob/main/docs/LIMITATIONS.md)
before interpreting these examples as historical benchmark reproductions.

## Documentation maintenance

This site is built from the Python docstrings with pdoc. Search any function,
class or module in the sidebar; signatures, source code and GitHub source links
are available on each API page. Rebuild with `python tools/build_api_docs.py`.
The [documentation guide](https://github.com/fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/blob/main/docs/API_DOCUMENTATION.md)
describes dependencies, local preview and publication.
"""

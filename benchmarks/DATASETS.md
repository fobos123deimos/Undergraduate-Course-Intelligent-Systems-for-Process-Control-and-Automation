# Data repositories in section 3.2

The paper's section 3.2 catalogs data repositories, rather than supplying one dynamical equation. Their dataset counts are a historical 2014 snapshot. This register preserves the scope without claiming that all collections are present locally.

| Collection | Role in the paper | Primary entry point | Required record before use |
|---|---|---|---|
| DaISy / KU Leuven | Dynamic system-identification records | https://homes.esat.kuleuven.be/~smc/daisy/ | Process, channels, sample time, experiment ID, original reference |
| IFAC TC 1.1 | Electronic circuit and artificial high-order SISO records | https://tc.ifac-control.org/1/1 | Exact dataset/version and signal-to-noise condition |
| NIST StRD | Certified nonlinear regression cases | https://www.itl.nist.gov/div898/strd/nls/nls_main.shtml | Dataset, model formula, starting point, certified estimates/precision |
| MATLAB Neural Network Toolbox | Engine, cholesterol, ball, house, magnetic levitation | https://www.mathworks.com/help/deeplearning/ | Product release, toolbox availability, dataset documentation |
| MATLAB Fuzzy Logic Toolbox | Auto MPG, Mackey–Glass, dryer | https://www.mathworks.com/help/fuzzy/ | Source license, lag selection and sampling for time series |
| MATLAB Statistics Toolbox | Thirty cases listed in Table 2 | https://www.mathworks.com/help/stats/ | Release-specific filename; distinguish measured and simulated data |
| UCI | Regression and classification collections | https://archive.ics.uci.edu/ | Dataset DOI/version, feature types, missingness and license |
| DELVE | Regression comparison protocols | https://www.cs.toronto.edu/~delve/ | Original training/test protocol and preprocessing |
| WEKA | Regression test collections | https://www.cs.waikato.ac.nz/ml/weka/ | ARFF schema, target field and original source |

These entry points identify the original providers; availability of every historical endpoint is not asserted. Source retrieval and execution of specific plant simulators are documented separately in the [external-source guide](EXTERNAL_MODELS.md) and [access record](external_access_review.json). The original measured throttle records remain unavailable. The repository does not imply that every dataset in these historical collections was downloaded or analyzed.

## DaISy systems listed in the review

Ethane–ethylene distillation; glass furnace; 120 MW power plant; industrial evaporator; pH-neutralization tank; fractional distillation; industrial dryer; liquid-saturated steam heat exchanger; winding process; CSTR; Abbott steam generator; ball-and-beam; laboratory hair dryer; CD-player arm; wing flutter; flexible robot arm; flexible steel subframe; cutaneous potential; tongue-displacement shapes; western Lake Erie; heat flow through a two-layer wall; heating system; in-vivo MRS simulator; Internet traffic.

## MATLAB Statistics cases listed in the review

Chemical reactions with correlated predictors; cardiac arrhythmia; car measurements (1970–1982); cereal ingredients; cities; discriminant-analysis cities; exam grades; Fisher iris; influenza surveillance; Massachusetts gasoline; cement heat; milk bacteria; simulated hospitals; automobile imports; ionosphere; clustered four-dimensional data; GPA and LSAT; mileage; biochemical oxygen demand; Morse-code recognition; 4000-predictor grouped data; dimensional run-out; polynomial fitting; popcorn; Hougen–Watson kinetics; SAT table; SAT CSV; gasoline spectra/octane; simulated stocks. `carbig` and its subset are separate entries in the original table. These are data-analysis cases, not thirty mechanistic plant simulators.

## Import protocol

Keep downloaded records under an ignored local data directory and retain their license. Convert a copy into CSV with explicit column names, without smoothing or replacing missing values silently:

```python
from intelligent_control.benchmarks import load_io_csv
t, u, y = load_io_csv('throttle_validation.csv', ['duty_percent'], ['angle_deg'], 0.01)
```

The same named-channel interface is available in MATLAB/Octave:

```matlab
addpath('matlab');
[t,u,y] = load_io_csv('throttle_validation.csv', {'duty_percent'}, {'angle_deg'}, 0.01);
```

Both importers reject malformed or nonfinite records instead of silently discarding samples. Their validation fixtures are labeled synthetic and are not substitutes for the unavailable measured throttle data. The [throttle recovery and evaluation guide](THROTTLE_RECOVERY.md) adds a shared source-hash manifest, actual ZIP/member checks, exact 10000/2500-row sampling contracts and separate one-step/free-run scoring in Python and MATLAB/Octave. The original download address is recovered; the measurements are still missing.

Record file SHA-256, original URL, dataset title, measured/synthetic status, units, sample period, row count, transformation history and split boundaries in a neighboring JSON manifest. Keep whole experiments apart when estimating generalization. A chronological split is preferable to random row splitting for a dependent time series; free-run testing must not read future output samples. NIST reference-parameter reproduction is a numerical-accuracy task and should be scored separately from held-out prediction.

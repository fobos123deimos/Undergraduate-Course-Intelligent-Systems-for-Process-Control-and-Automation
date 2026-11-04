"""Build navigable notebooks from course notes and executable experiment modules."""
from pathlib import Path
import sys
import argparse
import nbformat as nb
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'python'))
from intelligent_control.experiments import SLUGS,TITLES
REPO='fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation'
INTRO={
1:r'''A well-mixed, constant-volume tank obeys $V\dot c=q(u-c)$.
With $V=100$ L and $q=10$ L/min, $G(s)=1/(10s+1)$ and
$c_{k+1}=a c_k+(1-a)u_k$, where $a=\exp(-T_s/10)$.
Estimate an ARX model from a persistently exciting experiment, then assess
one-step prediction and recursive free-run on a fresh input sequence.
Noise on the autoregressive regressor can bias least squares; a small residual
does not prove physical parameter accuracy.''',
2:r'''The IMC-inspired PI tuning for a FOPDT approximation is
$K_p=\tau/[K(\lambda+\theta)]$, $K_i=K_p/\tau$.
For the nominal tank, the characteristic polynomial is
$10s^2+(1+K_p)s+K_i$. Positive coefficients establish stability of this
second-order continuous nominal loop. Saturation and sampling still require
separate simulation. Conditional integration prevents an integral state
from growing while it would drive a saturated actuator further outward.''',
3:r'''A measured inlet disturbance can be canceled nominally by $u=v-d$.
A cascade loop measures the fast actuator variable and closes an inner loop
before the slower concentration controller. Multivariable interactions are
summarized by $\Lambda=K\circ(K^{-1})^T$; a static decoupler $K^{-1}$
cancels steady interaction, not all transient dynamics. Compare only cases
with the same disturbance location and measurement information.''',
4:r'''At each sample solve
$\min_U\sum_{j=1}^{N_p}\|\hat x_{k+j}-r\|_Q^2+
\sum_{j=0}^{N_c-1}\|\Delta u_{k+j}\|_R^2$,
subject to $\hat x^+=A\hat x+B u$, actuator bounds and move bounds.
Only the first optimized action is applied. Beyond the control horizon, hold
the final move. Inspect solver failures as well as tracking error.
The second experiment uses two coupled states and two constrained inputs.''',
5:r'''Crisp supervisory rules produce traceable diagnoses. Fuzzy inference
instead represents graded membership. Mamdani uses min firing, max aggregation
and centroid defuzzification; Sugeno uses a normalized weighted average of
singleton consequents. The nine rules here form a PD-like surface used in an
incremental PI law. A separate example schedules PID gains. None of these
finite scenarios establishes global closed-loop stability.''',
6:r'''The illustrative nonlinear transition is
$c^+=u+(c-u)\exp[-T_s(1+0.6c)/10]$. It freezes the flushing coefficient
over a sample and is explicitly different from the article benchmarks.
Fit a tanh MLP and a Gaussian RBF network with normalization learned on
training inputs only. Validate untouched transitions, a recursive trajectory
and out-of-domain points separately. The controller evaluates bounded actions
through the trained MLP. Perceptron classification and SOM clustering use the
same input domain to illustrate distinct learning objectives.''',
7:r'''Encode $(K_p,K_i)$ as bounded real values or 12-bit binary chromosomes.
Use tournament selection, crossover, mutation and elitism to minimize
$J=\mathrm{IAE}+0.03\sum_k|u_k-u_{k-1}|$. Equal population and generation
counts give equal numbers of objective evaluations, not equal wall-clock cost.
Report the seeded search and test its gains on a changed residence time.
A small outer search also tunes a MIMO MPC move penalty; it is not a claim
of a global optimum.''',
8:r'''Compare PI, fuzzy gain PID and feedforward PI at residence times 7,
10 and 14 min, using the same sensor-noise seed and reference/disturbance
schedule. Report IAE, ISE, ITAE, actuator energy, movement and violations.
Feedforward receives a disturbance measurement, so its information advantage
must be stated. These are synthetic matched scenarios, not measured evidence
or statistical confidence bounds. A final recommendation must state which
constraint or uncertainty determines the preferred controller.''',
9:r'''A Markov chain describes transitions among normal, drifting and faulty sensor
modes. A categorical hidden Markov model infers these modes from noisy tank
residuals. Compute multi-step probabilities, stationary distributions and first
fault times; compare causal filtering with offline smoothing and Viterbi decoding.
Fit parameters using independent calibration sequences, then evaluate a held-out
trajectory. Baum-Welch illustrates unsupervised learning and label ambiguity.
Finally, use only the causal posterior to compensate a sensor in a PI loop,
and repeat with process-model mismatch. This unit is an enrichment beyond the
eight supplied syllabus units and the article benchmark inventory.'''}


def markov_cells(slug):
    """Keep the probabilistic calculations inspectable before the full experiment."""
    return [
        nb.v4.new_markdown_cell('## 1. Transition and first-fault calculations\n\nDistributions are row vectors. Python uses states 0, 1, 2; MATLAB/Octave uses 1, 2, 3. The initial state emits before the first transition. A stationary distribution need not be the limit of every chain: check irreducibility and periodicity.'),
        nb.v4.new_code_cell('import numpy as np\nfrom intelligent_control.markov import (n_step_distribution, stationary_distribution, hitting_statistics, CategoricalHMM)\nfrom intelligent_control.markov_lab import TRANSITION, PRIOR, STATE_NAMES\nprint("States:", STATE_NAMES)\nprint("Transition matrix:\\n", TRANSITION)\nprint("50-step distribution from normal:", n_step_distribution([1., 0., 0.], TRANSITION, 50))\nprint("Stationary distribution:", stationary_distribution(TRANSITION))\nprint("First fault:", hitting_statistics(TRANSITION, [2]))'),
        nb.v4.new_markdown_cell('## 2. A small HMM you can verify by hand\n\nThere are eight possible hidden paths for three observations and two states. Sum their joint probabilities to check the likelihood. Filtering at sample k uses observations through k; smoothing and Viterbi below use the entire record.'),
        nb.v4.new_code_cell('toy = CategoricalHMM([.6, .4], [[.7, .3], [.4, .6]], [[.5, .5], [.1, .9]])\nobservations = [0, 1, 0]\nprint("Likelihood:", np.exp(toy.filter(observations)["log_likelihood"]))\nprint("Filtered:\\n", toy.filter(observations)["filtered"])\nprint("Smoothed:\\n", toy.smooth(observations)["smoothed"])\nprint("Viterbi path:", toy.viterbi(observations)["states"])'),
        nb.v4.new_markdown_cell('## 3. Calibrate, freeze settings and test\n\nTwenty independent calibration sequences (seed 17, length 150) fit the HMM with pseudocount 1. Their labels are available because this is a synthetic calibration experiment. The independent 600-sample test uses seed 2026. The alarm threshold 0.7 and residual cutpoints are fixed before testing. Baum-Welch receives only calibration symbols; no held-out labels are used to name its latent states. This demonstration starts EM at the known simulator probabilities, a favorable initialization rather than uninformed identification.'),
        nb.v4.new_code_cell(f'from intelligent_control.experiments import run_unit\nimport json\nresult = run_unit(9, ROOT / "laboratories/{slug}/results")\nprint(json.dumps(result["summary"], indent=2))'),
        nb.v4.new_code_cell(f'from IPython.display import Image, display\ndisplay(Image(filename=str(ROOT / "laboratories/{slug}/results/diagnosis.png")))'),
        nb.v4.new_markdown_cell('## 4. Causal supervision with model mismatch\n\nBoth PI loops see the same latent sensor modes and noise. The compensated loop additionally propagates a nominal tank model from its known initial state and past applied inputs. It subtracts the posterior-weighted calibration bias from the current measurement. Only forward filtering enters this controller. The second case changes the true residence time from 10 to 14 min, while the predictor remains at 10 min; this confounds model error with sensor faults.'),
        nb.v4.new_code_cell(f'display(Image(filename=str(ROOT / "laboratories/{slug}/results/comparison.png")))\nfor row in result["summary"]["control"]:\n    print(row["policy"], "IAE =", round(row["iae"], 5), "movement =", round(row["total_variation"], 5))'),
        nb.v4.new_markdown_cell('## 5. Investigate\n\n1. Explain why the recoverable chain has a stationary fault probability below one but eventual first-fault probability one.\n2. Replace the fault row by an absorbing row; distinguish first passage from stationary behavior.\n3. Explain why offline estimates cannot be used as real-time controller inputs.\n4. Vary the alarm threshold using calibration data, then freeze it before generating a new test.\n5. Discuss emission dependence under model mismatch and the information advantage of the compensated controller.\n\n[Lesson](../../course/09-markov-hidden-state-diagnosis/lesson.md) · [Problems](../../problem-sets/09-markov-hidden-state-diagnosis/exercises.md) · [Worked solutions](../../problem-sets/09-markov-hidden-state-diagnosis/solutions.md) · [Native MATLAB/Octave](../../matlab/README.md)')]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--unit',type=int,choices=sorted(SLUGS),help='Rebuild only this notebook; retain outputs of the others.')
    args=parser.parse_args()
    selected=SLUGS if args.unit is None else {args.unit:SLUGS[args.unit]}
    for unit,slug in selected.items():
        folder=ROOT/'laboratories'/slug;folder.mkdir(parents=True,exist_ok=True)
        cells=[nb.v4.new_markdown_cell(f'# {unit:02d}. {TITLES[unit]}\n\nOriginal study laboratory. All generated data are synthetic.\n\n'+INTRO[unit]),
          nb.v4.new_markdown_cell('## Prepare the environment\n\nRun the next cell once in Colab. Locally, install `requirements.txt` and open this notebook within the repository. The cell only downloads the public repository when running in Colab and no checkout is present.'),
          nb.v4.new_code_cell('from pathlib import Path\nimport sys, subprocess\ntry:\n    import google.colab\n    IN_COLAB = True\nexcept ImportError:\n    IN_COLAB = False\nif IN_COLAB and not Path("python/intelligent_control").exists():\n    checkout = Path("/content/intelligent-process-control")\n    if not checkout.exists():\n        subprocess.run(["git", "clone", "https://github.com/'+REPO+'.git", str(checkout)], check=True)\n    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", str(checkout / "requirements.txt")], check=True)\n    import os\n    os.chdir(checkout)\nROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "python/intelligent_control").is_dir())\nsys.path.insert(0, str(ROOT / "python"))\nprint("Environment ready")'),
          nb.v4.new_markdown_cell('## Run the experiment\n\nRead the model and controller definitions alongside the results. Every rerun writes the metrics, trace CSV files and figure from the current parameters. Unit 7 includes nested optimization and costs more than the other units.'),
          nb.v4.new_code_cell(f'from intelligent_control.experiments import run_unit\nimport json\nresult = run_unit({unit}, ROOT / "laboratories/{slug}/results")\nprint(json.dumps(result["summary"], indent=2))'),
          nb.v4.new_code_cell(f'from IPython.display import Image, display\ndisplay(Image(filename=str(ROOT / "laboratories/{slug}/results/comparison.png")))'),
          nb.v4.new_markdown_cell('## Inspect the evidence\n\n1. Identify the physical assumptions, input limits and units.\n2. Explain a visible transient using the governing equation.\n3. Change one model or controller parameter, rerun and compare the saved metrics.\n4. State what the test does and does not establish.\n\nUse the [course guide](../../course/README.md), [worked problems](../../problem-sets/README.md) and [benchmark inventory](../../benchmarks/README.md) for the corresponding derivations and extensions.')]
        if unit==9:cells=cells[:3]+markov_cells(slug)
        note=nb.v4.new_notebook(cells=cells,metadata={'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'},'language_info':{'name':'python','version':'3.12'}})
        nb.write(note,folder/'notebook.ipynb')
        (folder/'README.md').write_text(f'# {unit:02d}. {TITLES[unit]}\n\n[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/{REPO}/blob/main/laboratories/{slug}/notebook.ipynb)\n\n'+INTRO[unit]+f'\n\n```bash\npython tools/run_course.py --unit {unit}\n```\n\n[Notebook](notebook.ipynb) · [Metrics](results/metrics.json) · [Course notes](../../course/README.md) · [Problems and solutions](../../problem-sets/README.md)\n\n![Computed comparison](results/comparison.png)\n',encoding='utf-8')
        if unit==9:
            with (folder/'README.md').open('a',encoding='utf-8') as handle:
                handle.write('\n![Computed diagnosis](results/diagnosis.png)\n\n[Detailed lesson](../../course/'+slug+'/lesson.md) · [Exercises](../../problem-sets/'+slug+'/exercises.md) · [Worked solutions](../../problem-sets/'+slug+'/solutions.md)\n\nThe notebook separates chains, a hand-checkable HMM, supervised calibration, Baum-Welch, held-out diagnosis and causal PI supervision. CSV traces include true states for retrospective scoring only. Offline estimates never enter the controller.\n')
    print(f'Built {len(selected)} notebooks and laboratory guides')

if __name__=='__main__':main()

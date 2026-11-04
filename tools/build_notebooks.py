"""Build navigable notebooks from course notes and executable experiment modules."""
from pathlib import Path
import sys
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
constraint or uncertainty determines the preferred controller.'''}

def main():
    for unit,slug in SLUGS.items():
        folder=ROOT/'laboratories'/slug;folder.mkdir(parents=True,exist_ok=True)
        cells=[nb.v4.new_markdown_cell(f'# {unit:02d}. {TITLES[unit]}\n\nOriginal study laboratory. All generated data are synthetic.\n\n'+INTRO[unit]),
          nb.v4.new_markdown_cell('## Prepare the environment\n\nRun the next cell once in Colab. Locally, install `requirements.txt` and open this notebook within the repository. The cell only downloads the public repository when running in Colab and no checkout is present.'),
          nb.v4.new_code_cell('from pathlib import Path\nimport sys, subprocess\ntry:\n    import google.colab\n    IN_COLAB = True\nexcept ImportError:\n    IN_COLAB = False\nif IN_COLAB and not Path("python/intelligent_control").exists():\n    checkout = Path("/content/intelligent-process-control")\n    if not checkout.exists():\n        subprocess.run(["git", "clone", "https://github.com/'+REPO+'.git", str(checkout)], check=True)\n    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", str(checkout / "requirements.txt")], check=True)\n    import os\n    os.chdir(checkout)\nROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "python/intelligent_control").is_dir())\nsys.path.insert(0, str(ROOT / "python"))\nprint("Environment ready")'),
          nb.v4.new_markdown_cell('## Run the experiment\n\nRead the model and controller definitions alongside the results. Every rerun writes the metrics, trace CSV files and figure from the current parameters. Unit 7 includes nested optimization and costs more than the other units.'),
          nb.v4.new_code_cell(f'from intelligent_control.experiments import run_unit\nimport json\nresult = run_unit({unit}, ROOT / "laboratories/{slug}/results")\nprint(json.dumps(result["summary"], indent=2))'),
          nb.v4.new_code_cell(f'from IPython.display import Image, display\ndisplay(Image(filename=str(ROOT / "laboratories/{slug}/results/comparison.png")))'),
          nb.v4.new_markdown_cell('## Inspect the evidence\n\n1. Identify the physical assumptions, input limits and units.\n2. Explain a visible transient using the governing equation.\n3. Change one model or controller parameter, rerun and compare the saved metrics.\n4. State what the test does and does not establish.\n\nUse the [course guide](../../course/README.md), [worked problems](../../problem-sets/README.md) and [benchmark inventory](../../benchmarks/README.md) for the corresponding derivations and extensions.')]
        note=nb.v4.new_notebook(cells=cells,metadata={'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'},'language_info':{'name':'python','version':'3.12'}})
        nb.write(note,folder/'notebook.ipynb')
        (folder/'README.md').write_text(f'# {unit:02d}. {TITLES[unit]}\n\n[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/{REPO}/blob/main/laboratories/{slug}/notebook.ipynb)\n\n'+INTRO[unit]+f'\n\n```bash\npython tools/run_course.py --unit {unit}\n```\n\n[Notebook](notebook.ipynb) · [Metrics](results/metrics.json) · [Course notes](../../course/README.md) · [Problems and solutions](../../problem-sets/README.md)\n\n![Computed comparison](results/comparison.png)\n',encoding='utf-8')
    print('Built eight notebooks and laboratory guides')

if __name__=='__main__':main()

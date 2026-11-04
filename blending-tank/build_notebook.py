"""Build only the corrected physical-tank notebook, preserving other notebooks."""
from pathlib import Path
import sys
import nbformat as nb

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from document_rendering import notebook_markdown, preserve_outputs
folder = Path(__file__).resolve().parent
environment = nb.read(ROOT/'laboratories/09-markov-hidden-state-diagnosis/notebook.ipynb', as_version=4).cells[2].source
cells = [
    nb.v4.new_markdown_cell('# Corrected physical Blending Tank\n\nA conservation-law implementation with explicitly declared parameters. State order: `[X,V]`; input order: `[w1,w2,x1,x2,wout]`. Time is in minutes, mass flows in kg/min, volume in m³, and fractions are dimensionless. Density 1000 kg/m³ is an explicit study assumption.\n\n[Derivation and usage](README.md) · [Validation evidence](VALIDATION.md)'),
    nb.v4.new_markdown_cell('## Prepare the environment\n\nIn Colab, the following cell downloads the public course repository and installs its declared numerical requirements. Locally it uses the existing checkout.'),
    nb.v4.new_code_cell(environment),
    nb.v4.new_markdown_cell('## 1. Establish a genuine equilibrium\n\nThe default inlets carry 500 and 200 kg/min, with solute fractions 0.4 and 0.75. Equilibrium requires outlet 700 kg/min and gives tank fraction 0.5. The chosen equilibrium volume is 2 m³. Inspect the analytical Jacobian and reduced transfer functions. They map deviations from these operating values.'),
    nb.v4.new_code_cell('import json\nimport numpy as np\nfrom intelligent_control.physical_blending import DEFAULT_INPUT, DEFAULT_STATE, linearize, transfer_functions, equilibrium, jacobians, rhs, simulate\nmodel = linearize()\nprint("Equilibrium state:", model["x_eq"])\nprint("Equilibrium input:", model["u_eq"])\nprint("A:\\n", model["A"])\nprint("B:\\n", model["B"])\nprint(json.dumps(transfer_functions(), indent=2))'),
    nb.v4.new_markdown_cell('## 2. Run startup, filling and a local perturbation\n\nStartup uses zero initial solute and balanced flow. Filling keeps outlet 650 kg/min and compares with its variable-volume closed form. The perturbation starts at equilibrium and adds 10 kg/min to inlet 1 at minute 5. Its linear branch propagates input/state deviations and restores the output offsets. The linear approximation is assessed only as a local model.'),
    nb.v4.new_code_cell('import runpy\nstudy = runpy.run_path(str(ROOT / "blending-tank/run_study.py"))\nresult = study["run_study"](ROOT / "blending-tank/results")\nprint(json.dumps(result["summary"]["scenarios"], indent=2))'),
    nb.v4.new_code_cell('from IPython.display import Image, display\ndisplay(Image(filename=str(ROOT / "blending-tank/results/comparison.png")))'),
    nb.v4.new_markdown_cell('## 3. Distinguish filling from equilibrium\n\nAn outlet of 650 kg/min is a valid filling experiment. It cannot define a full constant-volume equilibrium with the stated inlets. Away from equilibrium, retain the affine drift term and the volume derivative of the concentration balance.'),
    nb.v4.new_code_cell('filling_input = DEFAULT_INPUT.copy()\nfilling_input[4] = 650.\ntry:\n    equilibrium(filling_input)\nexcept ValueError as error:\n    print("Equilibrium rejected as expected:", error)\nreference_state = np.array([.3, 2.])\nA_local, B_local = jacobians(reference_state, filling_input)\nprint("Nonzero affine drift:", rhs(reference_state, filling_input))\nprint("General A(1,2):", A_local[0, 1])'),
    nb.v4.new_markdown_cell('## 4. Reject a requested run through an empty tank\n\nKnown piecewise-constant flows give an exact volume forecast. The numerical interface checks the full requested horizon before integrating. It does not silently continue through zero volume or clip the physical equations.'),
    nb.v4.new_code_cell('draining_input = DEFAULT_INPUT.copy()\ndraining_input[4] = 900.\ntry:\n    simulate(DEFAULT_STATE, np.linspace(0., 20., 41), draining_input)\nexcept ValueError as error:\n    print("Invalid simulation horizon rejected as expected:", error)'),
    nb.v4.new_markdown_cell('## Inspect and extend\n\n1. Explain the negative transfer gain from the dilute inlet to tank fraction.\n2. Halve the inlet-flow perturbation and compare local linearization errors.\n3. Change density explicitly and regenerate both the nonlinear and linear models.\n4. Explain why the volume pole is an integrator and why outlet flow has no direct first-order effect on concentration at equilibrium.\n5. Compare the MATLAB/Octave equations with these results. Generate the fresh Simulink diagrams only in MATLAB with Simulink.\n\nThe numerical tests establish consistency with the stated ideal model. No measured-tank validation or proprietary-runtime execution is implied.')]
cells.insert(3, nb.v4.new_markdown_cell(r'''## Physical balances and expected behavior

With constant density and perfect mixing, total mass and solute mass obey

$$
\rho\dot V=w_1+w_2-w_{out},\qquad
\rho V\dot X=w_1(x_1-X)+w_2(x_2-X).
$$

The second equation follows after substituting the volume balance into the solute balance. Outlet flow changes volume and residence time; it does not add a separate concentration-removal term after this cancellation.

![Computed physical tank scenarios](results/comparison.png)

Read the startup panel as approach to the balanced-flow equilibrium, the filling panel as changing inventory, and the local perturbation panel as a nonlinear-versus-linear comparison around a declared operating point. These are saved computed results; running the experiment below refreshes them. Concentration and volume use different units and must not be compared on a common unlabelled scale.'''))
for cell in cells:
    if cell.cell_type=='markdown':cell.source=notebook_markdown(cell.source,folder)
notebook = nb.v4.new_notebook(cells=cells, metadata={'kernelspec': {'name': 'python3', 'display_name': 'Python 3', 'language': 'python'}, 'language_info': {'name': 'python', 'version': '3.12'}})
if (folder/'notebook.ipynb').exists():notebook=preserve_outputs(nb.read(folder/'notebook.ipynb',as_version=4),notebook)
nb.write(notebook, folder/'notebook.ipynb')
print('Built corrected physical-tank notebook.')

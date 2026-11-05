# Equations, figures and notebook rendering

The Markdown lessons, GitHub pages and Colab notebooks use the same mathematical content but different frontends. Keep inline expressions on one line between single dollar signs. Put display equations between double-dollar delimiters on their own lines, separated from prose by blank lines. Use a display block for a multistep derivation or a long optimization objective. In Python generators, write LaTeX in raw strings so that commands such as `\frac` and `\tau` do not become control characters.

The revision replaces the MPC notebook's multiline inline objective with a display equation, changes the pendulum case-study display delimiters to portable Markdown form, and normalizes display blocks in the lessons. This is a rendering repair; the mathematical models and the eleven notebooks' executable cell sources are unchanged. Regenerating the existing LaTeX editions produced no content differences, so the previously validated PDF editions were preserved.

## Figures that remain visible before execution

Each unit now has a conceptual diagram in [PNG and editable SVG](../course/figures/learning), a caption explaining the information flow, and links to the [article application studies](../benchmarks/learning/README.md). Conceptual curves are labelled as illustrations; experiment plots and benchmark results remain separate numerical evidence. Notebook Markdown uses absolute public image and document URLs because Colab does not serve repository-relative Markdown paths. Saved output images remain embedded in the notebook as well.

```bash
python tools/build_lesson_figures.py
python course/build_documents.py
python tools/build_notebooks.py
python blending-tank/build_notebook.py
python tools/validate.py --skip-tests
```

The notebook generators preserve saved outputs only when their corresponding code cell is unchanged. Changed numerical code must be executed again; preserved outputs do not certify a new implementation.

## Check the actual frontend

```bash
python -m pip install -r requirements-rendering.txt
python tools/validate_rendering.py --html-dir build/notebook-preview --record docs/rendering-validation.json
python -m http.server 8000 --bind 127.0.0.1
```

Open the exported notebooks under `http://127.0.0.1:8000/build/notebook-preview/`. Inspect an equation, each new figure, its caption and a navigation link in the intended frontend. After publication, inspect the actual Colab notebook as well. The structural audit detects unbalanced delimiters/groups/environments, multiline inline math, control characters, notebook-relative links and saved error outputs; it exports all eleven notebooks but does not claim to be a MathJax or KaTeX renderer. The [check record](rendering-validation.json) states the verified scope. The ordinary course validation command runs the structural audit automatically.

Live Colab rendering was verified on 4 November 2026 for source `14c13f4c06f9352c7d90e630e1666a96510dcf7d`: the MPC objective and state equation rendered, and the conceptual and benchmark images in units 04 and 09 loaded without running cells. [The review record](illustrated-review.json) separates this browser inspection from local and CI notebook execution. All eleven notebooks also executed successfully in the corresponding course CI run.

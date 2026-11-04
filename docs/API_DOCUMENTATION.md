# Python API documentation with pdoc

The [online API reference](https://fobos123deimos.github.io/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation/) ([versioned HTML](api/index.html)) documents all ten Python package/module pages, including Markov/HMM, course methods and experiments, the physical Blending Tank, article kernels, wind control and the separate pneumatic/hydrostatic interpretations. It follows the pdoc navigation used by [Fast Wave](https://github.com/fobos123deimos/fast-wave/tree/main/docs): search, signatures, cross-references, mathematical notation and expandable source code.

The Python docstrings are the documentation source. The course notes, worked problems, notebooks and MATLAB/Simulink guides remain linked companion material. pdoc does not generate a MATLAB or Simulink API reference.

## Build and inspect

From the repository root, with Python 3.12:

```bash
python -m pip install -r requirements-docs.txt
python tools/build_api_docs.py
python tools/build_api_docs.py --check
python -m http.server 8000 --bind 127.0.0.1 --directory docs/api
```

Open `http://127.0.0.1:8000/` in a browser. Serving the site over HTTP also exercises the search worker normally; direct `file://` viewing can be limited by browser restrictions. To create an isolated build use `--output build/api`. Build destinations are restricted to `docs/api` and directories under `build/` so course notes and evidence cannot be overwritten accidentally.

The build imports the package but does not execute laboratories, download datasets or run external simulators. It checks the complete module inventory, public function/class/method anchors, docstring coverage, local links and fragments, search-index presence and absence of machine-specific paths. The [build record](api/build.json) contains source/template hashes normalized to LF, exact generated-file hashes, dependency versions and coverage counts. `--check` detects stale source or modified output without regenerating it.

pdoc 16.0.0 and its rendering dependencies are pinned in [requirements-docs.txt](../requirements-docs.txt). Scientific dependency ranges follow the main project. MathJax is loaded by pdoc for formula rendering and requires an internet connection; source text remains readable without it.

## Update documentation

1. Edit docstrings beside the relevant Python definitions. Describe units, array shapes, return fields and limitations before adding examples.
2. Rebuild and run `--check`; inspect the changed pages and search results in a browser.
3. Commit the Python source and `docs/api` together. Do not hand-edit generated HTML or search data.

[The small template](pdoc-template/module.html.jinja2) adds course, validation and Simulink navigation; [custom CSS](pdoc-template/custom.css) retains the standard pdoc layout. The favicon is embedded and does not depend on a local machine path.

## Automated publication

The [API workflow](../.github/workflows/api-docs.yml) rebuilds and checks the site for relevant pushes and pull requests. Only successful builds on `main` can deploy through GitHub Pages. The site artifact contains only the generated API directory; private external simulator packages and other local data are not publication inputs.

GitHub Pages is configured to use **GitHub Actions** as its source in the repository's Settings → Pages. This one-time repository setting is separate from the build. Normal deployments use GitHub's temporary workflow token, with no persistent personal token in the repository. The current source's publication outcome must be checked in Actions before treating a site URL as live.

References: [pdoc documentation](https://pdoc.dev/docs/pdoc.html), [render configuration](https://pdoc.dev/docs/pdoc/render.html), [GitHub Pages workflow requirements](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

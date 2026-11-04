"""Build the text editions from content.py; PDF compilation is a separate step.

Run from any directory with Python 3. No third-party dependencies are needed.
"""
from pathlib import Path
import re

from content import UNITS, REFERENCES

COURSE = Path(__file__).resolve().parent
ROOT = COURSE.parent
PROBLEMS = ROOT / "problem-sets"


def text_escape(value):
    mapping = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%",
               "$": r"\$", "#": r"\#", "_": r"\_", "{": r"\{",
               "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    return "".join(mapping.get(char, char) for char in value)


def inline(value):
    tokens = re.split(r"(\$[^$\n]+\$|`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*|\[[^\]]+\]\(https?://[^)]+\))", value)
    result = []
    for token in tokens:
        if token.startswith("$") and token.endswith("$"):
            result.append(token)
        elif re.fullmatch(r"\[[^\]]+\]\(https?://[^)]+\)", token):
            label, url = token[1:-1].split("](", 1)
            result.append(r"\href{" + url + "}{" + text_escape(label) + "}")
        elif token.startswith("`") and token.endswith("`"):
            result.append(r"\texttt{" + text_escape(token[1:-1]) + "}")
        elif token.startswith("**") and token.endswith("**"):
            result.append(r"\textbf{" + text_escape(token[2:-2]) + "}")
        elif token.startswith("*") and token.endswith("*"):
            result.append(r"\emph{" + text_escape(token[1:-1]) + "}")
        else:
            result.append(text_escape(token))
    return "".join(result)


def latex(markdown):
    result = []
    for paragraph in re.split(r"\n\s*\n", markdown.strip()):
        paragraph = paragraph.strip()
        if paragraph.startswith("$$") and paragraph.endswith("$$"):
            result.append(r"\[" + paragraph[2:-2].strip() + r"\]")
        elif paragraph.startswith("## "):
            result.append(r"\subsection{" + text_escape(paragraph[3:]) + "}")
        elif re.match(r"^\d+\. ", paragraph):
            for line in paragraph.splitlines():
                result.append(r"\noindent " + inline(line) + r"\par\smallskip")
        else:
            result.append(inline(paragraph.replace("\n", " ")) + "\n")
    return "\n\n".join(result)


PREAMBLE = r"""\documentclass[11pt,a4paper]{article}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage[margin=23mm]{geometry}
\usepackage{amsmath,amssymb}
\usepackage{xcolor}
\usepackage{tikz}
\usetikzlibrary{arrows.meta,positioning,calc}
\usepackage{hyperref}
\hypersetup{colorlinks=true,linkcolor=blue!45!black,urlcolor=blue!45!black}
\setlength{\parindent}{0pt}
\setlength{\parskip}{5pt plus 1pt}
\setlength{\emergencystretch}{2em}
\definecolor{water}{RGB}{205,231,241}
\definecolor{ink}{RGB}{30,62,79}
\tikzset{flow/.style={-{Latex},thick,ink}, equipment/.style={thick,ink},
         box/.style={draw=ink,rounded corners,align=center,inner sep=5pt}}
"""


def document(title, subtitle, body):
    return PREAMBLE + r"\title{" + text_escape(title) + r"\\[4pt]{\large " + text_escape(subtitle) + "}}\n" + r"\author{Independent study collection}" + "\n" + r"\date{}" + "\n" + r"\begin{document}" + "\n" + r"\maketitle" + "\n" + r"\noindent Academic context: Intelligent Systems for Process Control and Automation, Prof. Michela Mulas. These newly written learning materials are not an official course plan and do not imply the professor's authorship, review or endorsement." + "\n\n" + r"\tableofcontents\newpage" + "\n" + body + "\n" + r"\end{document}" + "\n"


DIAGRAMS = {
    "hidden-state-diagnosis": r"""\begin{center}
\begin{tikzpicture}[node distance=14mm and 25mm]
\node[box] (z0) {Hidden regime\\$z_{k-1}$};
\node[box,right=of z0] (z1) {Hidden regime\\$z_k$};
\node[box,right=of z1] (z2) {Hidden regime\\$z_{k+1}$};
\node[box,below=of z0,fill=water] (o0) {Residual symbol\\$o_{k-1}$};
\node[box,below=of z1,fill=water] (o1) {Residual symbol\\$o_k$};
\node[box,below=of z2,fill=water] (o2) {Residual symbol\\$o_{k+1}$};
\draw[flow] (z0)--node[above] {$P$}(z1);
\draw[flow] (z1)--node[above] {$P$}(z2);
\draw[flow] (z0)--node[right] {$B$}(o0);
\draw[flow] (z1)--node[right] {$B$}(o1);
\draw[flow] (z2)--node[right] {$B$}(o2);
\end{tikzpicture}
\end{center}
\noindent\textit{Transitions describe regime persistence; emissions connect a regime to uncertain evidence. At sample $k$, an online filter can use observations only through $o_k$.}
""",
    "blending-tank": r"""\begin{center}
\begin{tikzpicture}[scale=0.85]
\fill[water] (0,0) rectangle (4,2.4);
\draw[equipment] (0,3.4)--(0,0)--(4,0)--(4,3.4);
\draw[ink,dashed] (0,2.4)--(4,2.4);
\draw[flow] (-2,3.3)--(0.8,3.3)--(0.8,2.6);
\draw[flow] (6,3.3)--(3.2,3.3)--(3.2,2.6);
\draw[flow] (4,0.5)--(6,0.5);
\draw[equipment] (2,3.8)--(2,0.8);
\draw[equipment] (1.2,0.8)--(2.8,0.8);
\draw[equipment] (1.4,1.0)--(2.6,0.6);
\node[box,fill=white] at (2,3.9) {mixer};
\node at (-1,3.7) {$q_H=qu,\ c_H=1$};
\node at (5.6,3.7) {$q_L=q(1-u),\ c_L=d_{low}$};
\node at (5.3,0.1) {$q_o,\ c$};
\node at (2,1.7) {$V=Ah,\quad c(t)$};
\draw[<->,ink] (-0.4,0)--node[left] {$h$}(-0.4,2.4);
\node[box,fill=white] (sensor) at (4.7,1.7) {sensor};
\draw[ink] (4,1.7)--(sensor);
\draw[flow] (sensor.east)--(6.2,1.7) node[right] {$y$};
\end{tikzpicture}
\end{center}
\noindent\textit{Physical boundary for the analytical tank. A constant-volume model requires inlet and outlet balance. Here the disturbance is low-feed concentration; the shared laboratory instead uses an additive disturbance to the complete inlet mixture. The sensor reading may have dynamics distinct from concentration.}
""",
    "cascade-valve": r"""\begin{center}
\begin{tikzpicture}[node distance=1.0cm,scale=0.85,transform shape]
\node[box] (outer) {Concentration\\controller};
\node[box,right=of outer] (inner) {Flow\\controller};
\node[box,right=of inner] (valve) {Valve and\\flow actuator};
\node[box,right=of valve] (tank) {Mixed\\vessel};
\draw[flow] (-2,0)--node[above] {$r$}(outer);
\draw[flow] (outer)--node[above] {$u_{sp}$}(inner);
\draw[flow] (inner)--node[above] {$v$}(valve);
\draw[flow] (valve)--node[above] {$u$}(tank);
\draw[flow] (tank)--++(1.3,0) coordinate (out) node[right] {$c$};
\draw[flow] ($(valve.east)+(0.25,0)$)--++(0,-1.0)-|(inner.south);
\draw[flow] (out)--++(0,-2)-|(outer.south);
\node at (5,-1.3) {measured blend feedback};
\node at (4,-2.3) {measured concentration feedback};
\draw[flow] ($(valve.north)+(0,1)$)--node[right] {supply disturbance}(valve.north);
\end{tikzpicture}
\end{center}
\noindent\textit{Cascade uses a measured inner variable. Both feedback paths are negative under the error conventions stated in the text.}
""",
    "mpc-horizon": r"""\begin{center}
\begin{tikzpicture}[x=0.75cm,y=0.6cm]
\draw[flow] (0,0)--(12,0) node[right] {sample};
\draw[flow] (0,0)--(0,4.5) node[above] {output};
\draw[ink,thick] (0.2,0.8)--(1,1.2)--(2,1.1)--(3,1.8)--(4,2);
\draw[ink,dashed,thick] (4,2)--(5,2.5)--(6,3)--(7,3.3)--(8,3.5)--(9,3.6)--(10,3.7);
\draw[ink,densely dotted] (4,0)--(4,4);
\draw[ink,dotted] (0,3.8)--(11,3.8) node[right] {target};
\node at (2,-0.5) {measurements};
\node at (4,-0.5) {$k$};
\node at (8,-0.5) {predictions};
\draw[<->,ink] (4,4.3)--node[above] {prediction horizon}(10,4.3);
\end{tikzpicture}
\end{center}
\noindent\textit{The future curve is a model prediction, not an observed trajectory. Only the first planned input is applied before the next measurement.}
""",
    "neural-regressor": r"""\begin{center}
\begin{tikzpicture}[node distance=1.0cm]
\node[box] (data) {Past measured outputs\\and applied inputs};
\node[box,right=of data] (scaler) {Training-fitted\\normalization};
\node[box,right=of scaler] (net) {MLP or RBF\\predictor};
\draw[flow] (data)--node[above] {$\phi_k$}(scaler);
\draw[flow] (scaler)--(net);
\draw[flow] (net.east)--++(1.3,0) node[right] {$\hat y_{k+1}$};
\end{tikzpicture}
\end{center}
\noindent\textit{Causal regressors and fixed preprocessing are part of the model. Recursive simulation substitutes previous predictions for measured outputs; it is a different validation task.}
"""
}


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.strip() + "\n", encoding="utf-8")


def main():
    PROBLEMS.mkdir(exist_ok=True)
    for name, source in DIAGRAMS.items():
        write(COURSE / "figures" / (name + ".tex"), source)

    note_parts, exercise_parts, solution_parts = [], [], []
    guide_rows, problem_rows = [], []
    diagrams_at = {1: "blending-tank", 3: "cascade-valve", 4: "mpc-horizon", 6: "neural-regressor", 9: "hidden-state-diagnosis"}
    for number, unit in enumerate(UNITS, 1):
        slug, title = unit["slug"], unit["title"]
        lab = "../../laboratories/" + slug + "/notebook.ipynb"
        heading = f"# Unit {number:02d} - {title}\n\n"
        navigation = f"[Course guide](../README.md) · [Notebook]({lab}) · [Exercises](../../problem-sets/{slug}/exercises.md) · [Worked solutions](../../problem-sets/{slug}/solutions.md)\n\n"
        run = f"\n\n## Computational practice\n\nFrom the repository root, run `python tools/run_course.py --unit {number}`. Use the notebook to inspect assumptions, rerun calculations and compare them with the worked reasoning. The lesson's hypothetical examples illustrate the method; inspect each program's configuration before comparing numerical outputs.\n"
        write(COURSE / slug / "lesson.md", heading + navigation + "**Prerequisites:** " + unit["prerequisites"] + "\n\n" + unit["lesson"].strip() + run)
        ex_md = heading + "[Lesson](../../course/" + slug + "/lesson.md) · [Worked solutions](solutions.md)\n\nState units, assumptions and initial conditions before calculating. For computational extensions, report the actual experiment and its limitations.\n\n"
        sol_md = heading + "[Exercises](exercises.md) · [Lesson](../../course/" + slug + "/lesson.md)\n\nThese worked answers use the explicitly hypothetical problem data. Design questions may admit other defensible solutions if their assumptions and evidence are stated.\n\n"
        section = r"\clearpage\section{" + text_escape(f"Unit {number:02d}: {title}") + "}\n"
        note = section + r"\textbf{Prerequisites:} " + text_escape(unit["prerequisites"]) + "\n\n"
        ex_tex, sol_tex = section, section
        if number in diagrams_at:
            name = diagrams_at[number]
            note += r"\input{figures/" + name + ".tex}\n"
            if number in (1, 3):
                ex_tex += r"\input{../course/figures/" + name + ".tex}\n"
        note_parts.append(note + latex(unit["lesson"]))
        for problem_number, (problem_title, question, answer) in enumerate(unit["problems"], 1):
            problem_heading = f"Problem {number:02d}.{problem_number} - {problem_title}"
            ex_md += "## " + problem_heading + "\n\n" + question + "\n\n"
            sol_md += "## " + problem_heading + "\n\n" + answer + "\n\n"
            sub = r"\subsection{" + text_escape(problem_heading) + "}\n"
            ex_tex += sub + latex(question) + "\n"
            sol_tex += sub + r"\textbf{Problem.} " + latex(question) + "\n\n" + r"\textbf{Worked answer.} " + latex(answer) + "\n"
        write(PROBLEMS / slug / "exercises.md", ex_md)
        write(PROBLEMS / slug / "solutions.md", sol_md)
        exercise_parts.append(ex_tex)
        solution_parts.append(sol_tex)
        guide_rows.append(f"| {number:02d} | [{title}]({slug}/lesson.md) | {unit['prerequisites']} | [Notebook](../laboratories/{slug}/notebook.ipynb) |")
        problem_rows.append(f"| {number:02d} | {title} | [Five problems]({slug}/exercises.md) | [Worked answers]({slug}/solutions.md) |")

    notes = "\n".join(note_parts) + r"\clearpage\section{Bibliography and reading map}" + "\n" + latex(REFERENCES)
    problem_count = sum(len(unit["problems"]) for unit in UNITS)
    write(COURSE / "notes.tex", document("Intelligent Systems for Process Control and Automation", f"{len(UNITS)} connected study units", notes))
    write(PROBLEMS / "exercises.tex", document("Integrated process-control problems", f"{problem_count} problems with linked analytical and computational tasks", "\n".join(exercise_parts)))
    write(PROBLEMS / "solutions.tex", document("Worked solutions and design reasoning", f"{problem_count} integrated process-control problems", "\n".join(solution_parts)))
    write(COURSE / "REFERENCES.md", "# Bibliography and reading map\n\n" + REFERENCES)
    guide = """# Course guide and prerequisite map

[Course notes (PDF)](notes.pdf) · [Editable LaTeX](notes.tex) · [Problem sets](../problem-sets/README.md) · [Bibliography](REFERENCES.md)

This original English study collection follows the eight content areas of the supplied integrated syllabus and adds a ninth unit on Markov chains and hidden-state diagnosis. Unit 09 is an extension, not a model attributed to the benchmark article or an additional topic claimed for the official syllabus. The supplied syllabus itself is a non-official synthesis. Academic context: the discipline associated with Prof. Michela Mulas; no authorship, review or endorsement by the professor is implied.

The worked tank is hypothetical: volume 100 L, flow 10 L/min, normalized high/low feed concentrations 1 and 0, and blend fraction between 0 and 1. It illustrates derivations separately from the preserved historical Blending Tank implementation and from the article's named benchmarks.

## Learning sequence

| Unit | Topic | Entry knowledge | Computation |
|---|---|---|---|
""" + "\n".join(guide_rows) + """

## Suggested use of 64 core study hours and an 8-hour extension

Allocate eight hours to each unit: two for the lesson and derivations, two for computational exploration, three for the five integrated problems, and one for comparison and reflection. The eight core units total 64 hours; the Markov/HMM extension adds eight hours for a suggested total of 72. This is a study allocation, not an official timetable or assessment policy. Additional time may be required for prerequisite review and external industrial simulators.

Complete Units 01-04 in order. Unit 05 needs 01-03; Unit 06 needs 01, 02 and 04; Unit 07 builds on 02, 04 and 06. Unit 08 integrates the eight core units. Unit 09 builds on 01, 02 and 08, plus conditional probability and matrix multiplication. Each problem has linked subparts that move from a quantitative model to an implementation or evidence decision.

## Four connected practical blocks

1. **Model and establish a baseline (01-02):** derive balances, identify and validate a process model, then compare PI/PID and IMC-based tuning with actuator limits.
2. **Compare structures and predictions (03-04):** examine measured-disturbance feedforward, inner flow cascade, multivariable interaction and constrained MPC using a common experiment contract.
3. **Add and evaluate intelligence (05-08):** use expert rules, fuzzy control, neural identification/control and evolutionary tuning for a stated deficiency, then evaluate the improvement on held-out conditions.
4. **Diagnose uncertain operating regimes (09, extension):** calculate Markov occupancy and absorption, estimate categorical HMMs from separate trajectories, distinguish filtering from offline inference, and evaluate sensor-bias supervision under plant mismatch.

## Readiness checks

Before advancing, explain the input/output units, the state and operating point, and one physical limit. Derive one numerical prediction before running code. Distinguish a fitted trajectory from independent validation, a source equation from an educational closure, and a passing simulation from a stability proof.

Read the benchmark inventory alongside the article. The teaching tank is an integrative case, not a substitute for the pendulum, throttle, pneumatic, hydrostatic, reactor, distillation, gasifier, wind and Tennessee Eastman examples. External data/maps and reference simulators remain part of the identity of those benchmarks.

## Rebuild the text editions

Run `python course/build_documents.py` to regenerate the Markdown and LaTeX files from `course/content.py`. Compile `course/notes.tex`, `problem-sets/exercises.tex` and `problem-sets/solutions.tex` from their own directories. The physical and architecture figures are editable TikZ sources in `course/figures/`.
"""
    write(COURSE / "README.md", guide)
    write(PROBLEMS / "README.md", """# Integrated problem sets

[Exercise book (PDF)](exercises.pdf) · [Worked solutions (PDF)](solutions.pdf) · [Course notes](../course/notes.pdf)

Nine sets of five original integrated problems connect derivations, physical interpretation, implementation and evaluation: 40 problems cover the eight core units and five extend the collection with Markov chains and hidden-state diagnosis. Every problem has linked parts and a worked answer. Hypothetical numerical data are stated explicitly; design protocols are proposed experiments, not fabricated results.

| Unit | Topic | Exercises | Solutions |
|---|---|---|---|
""" + "\n".join(problem_rows) + "\n\nAttempt the quantitative derivation before opening the solution. For design questions, other answers are acceptable when they preserve the problem constraints and make evidence and limitations explicit.\n")
    print(f"Built {len(UNITS)} lessons, {sum(len(u['problems']) for u in UNITS)} worked problems, and three LaTeX editions.")


if __name__ == "__main__":
    main()

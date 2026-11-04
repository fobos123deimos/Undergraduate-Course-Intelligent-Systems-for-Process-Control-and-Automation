"""Portable math delimiters and repository links for Markdown notebook frontends."""
from pathlib import Path
import re
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
REPO = "fobos123deimos/Undergraduate-Course-Intelligent-Systems-for-Process-Control-and-Automation"


def normalize_math(text):
    """Keep display math in separate paragraphs; do not touch fenced code."""
    chunks = re.split(r"(```[\s\S]*?```)", text)
    for index in range(0, len(chunks), 2):
        value = chunks[index]
        value = re.sub(r"(?m)^\\\[\s*$", "$$", value)
        value = re.sub(r"(?m)^\\\]\s*$", "$$", value)
        value = re.sub(r"\$\$([\s\S]*?)\$\$", lambda m: "$$\n" + m[1].strip() + "\n$$", value)
        chunks[index] = value
    return "".join(chunks)


def notebook_markdown(text, folder):
    """Use public absolute links: Colab has no repository-relative file server."""
    text = normalize_math(text)
    def replace(match):
        image, label, target = match.groups()
        if target.startswith(("https:", "http:", "mailto:", "#", "attachment:", "data:")):
            return match[0]
        path, marker, fragment = target.partition("#")
        absolute = (Path(folder) / path).resolve()
        relative = absolute.relative_to(ROOT).as_posix()
        base = f"https://raw.githubusercontent.com/{REPO}/main/" if image else f"https://github.com/{REPO}/blob/main/"
        return f"{image}[{label}]({base}{quote(relative)}{marker}{fragment})"
    return re.sub(r"(!?)\[([^\]]*)\]\(([^)]+)\)", replace, text)


def preserve_outputs(previous, current):
    """Reuse only outputs whose executable source is byte-for-byte unchanged."""
    sources = {cell.source: cell for cell in previous.cells if cell.cell_type == "code"}
    for cell in current.cells:
        if cell.cell_type == "code" and cell.source in sources:
            old = sources[cell.source]
            cell.outputs = old.get("outputs", [])
            cell.execution_count = old.get("execution_count")
    return current

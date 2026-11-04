"""Audit math/link portability and optionally export notebook HTML for inspection."""
from pathlib import Path
import argparse
import json
import re
import nbformat

ROOT = Path(__file__).resolve().parents[1]


def check_math(source, label):
    """Reject known frontend failures; this is not a TeX rendering engine."""
    source = re.sub(r"```[\s\S]*?```", "", source)
    source = re.sub(r"`[^`\n]*`", "", source)
    if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", source):
        raise ValueError(f"{label}: control character, possibly a non-raw LaTeX string")
    if re.search(r"(?m)^\\[\[\]]\s*$", source):
        raise ValueError(f"{label}: use standalone $$ display delimiters")
    displays = re.findall(r"\$\$([\s\S]*?)\$\$", source)
    if source.count("$$") != 2*len(displays):raise ValueError(f"{label}: unmatched display delimiter")
    for match in re.finditer(r"\$\$([\s\S]*?)\$\$", source):
        if not match[0].startswith("$$\n") or not match[0].endswith("\n$$"):
            raise ValueError(f"{label}: display delimiters must be on their own lines")
    remaining = re.sub(r"\$\$[\s\S]*?\$\$", "", source)
    inline = re.findall(r"(?<!\\)\$([^$]*?)(?<!\\)\$", remaining)
    if len(re.findall(r"(?<!\\)\$", remaining)) != 2*len(inline):raise ValueError(f"{label}: unmatched inline delimiter")
    for equation in inline:
        if "\n" in equation:raise ValueError(f"{label}: inline math crosses a newline; use display math")
    for equation in displays+inline:
        # Escaped literal braces do not participate in TeX group nesting.
        groups = re.sub(r"\\[{}]", "", equation)
        level=0
        for char in groups:
            level += (char=="{")-(char=="}")
            if level<0:raise ValueError(f"{label}: unmatched closing math brace")
        if level:raise ValueError(f"{label}: unmatched opening math brace")
        begin=re.findall(r"\\begin\{([^}]+)\}",equation)
        end=re.findall(r"\\end\{([^}]+)\}",equation)
        if sorted(begin)!=sorted(end):raise ValueError(f"{label}: unmatched math environment")
    return {"display":len(displays),"inline":len(inline)}


def validate(html_dir=None, record=None):
    totals={"markdown_files":0,"notebooks":0,"markdown_cells":0,"display_math":0,"inline_math":0,"notebook_images":0}
    checked=[]
    paths=[p for p in ROOT.rglob('*.md') if not any(part in ('.git','build','external-data') for part in p.relative_to(ROOT).parts)]
    for path in sorted(paths):
        counts=check_math(path.read_text(encoding='utf-8'),str(path.relative_to(ROOT)))
        totals['markdown_files']+=1
        totals['display_math']+=counts['display'];totals['inline_math']+=counts['inline']
    if html_dir:
        from nbconvert import HTMLExporter
        exporter=HTMLExporter();html_dir.mkdir(parents=True,exist_ok=True)
    notebooks=sorted((ROOT/'laboratories').glob('*/notebook.ipynb'))+[ROOT/'benchmarks/notebook.ipynb',ROOT/'blending-tank/notebook.ipynb']
    for path in notebooks:
        notebook=nbformat.read(path,as_version=4);nbformat.validate(notebook)
        row={"path":path.relative_to(ROOT).as_posix(),"markdown_cells":0,"images":0,"code_cells":0,"code_cells_with_outputs":0,"error_outputs":0}
        for index,cell in enumerate(notebook.cells):
            if cell.cell_type=='markdown':
                row['markdown_cells']+=1
                counts=check_math(cell.source,f"{path.relative_to(ROOT)} cell {index}")
                totals['display_math']+=counts['display'];totals['inline_math']+=counts['inline']
                for target in re.findall(r"\]\(([^)]+)\)",cell.source):
                    if not target.startswith(('https:','http:','mailto:','#','attachment:','data:')):
                        raise ValueError(f"{path.relative_to(ROOT)} cell {index}: Colab-relative link {target}")
                row['images']+=len(re.findall(r"!\[",cell.source))
            elif cell.cell_type=='code':
                row['code_cells']+=1;row['code_cells_with_outputs']+=bool(cell.get('outputs'))
                row['error_outputs']+=sum(o.output_type=='error' for o in cell.get('outputs',[]))
        if row['error_outputs']:raise ValueError(f"{path}: saved error outputs")
        if html_dir:
            html,_=exporter.from_notebook_node(notebook)
            destination=html_dir/(path.parent.name+'.html');destination.write_text(html,encoding='utf-8')
            row['html_export']='passed'
            row['html_bytes']=destination.stat().st_size
        totals['notebooks']+=1;totals['markdown_cells']+=row['markdown_cells'];totals['notebook_images']+=row['images'];checked.append(row)
    result={"status":"passed","checks":totals,"notebooks":checked,"scope":"Delimiter, grouping, environment, absolute-link and notebook-HTML checks. Actual formula/layout rendering additionally requires browser visual inspection; this check is not a MathJax or KaTeX engine."}
    if record:record.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(totals,indent=2))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--html-dir',type=Path);parser.add_argument('--record',type=Path)
    args=parser.parse_args();validate(args.html_dir,args.record)

"""Run numerical tests, verify repository navigation and optionally execute notebooks."""
from pathlib import Path
import argparse
import json
import re
import subprocess
import sys
from urllib.parse import unquote
ROOT=Path(__file__).resolve().parents[1]

def navigation():
    missing=[]
    for path in ROOT.rglob('*.md'):
        if '.git' in path.parts:continue
        for target in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            if target.startswith(('https:','http:','mailto:','#')):continue
            target=unquote(target.split('#')[0]).strip('<>')
            if target and not (path.parent/target).exists():missing.append(f'{path.relative_to(ROOT)}: {target}')
    if missing:raise AssertionError('Broken local links:\n'+'\n'.join(missing))
    print('Local Markdown links passed')

def notebooks(execute=False):
    import nbformat
    from nbclient import NotebookClient
    records=[]
    paths=sorted((ROOT/'laboratories').glob('*/notebook.ipynb'))
    if (ROOT/'benchmarks/notebook.ipynb').exists():paths.append(ROOT/'benchmarks/notebook.ipynb')
    if (ROOT/'blending-tank/notebook.ipynb').exists():paths.append(ROOT/'blending-tank/notebook.ipynb')
    for path in paths:
        notebook=nbformat.read(path,as_version=4);nbformat.validate(notebook)
        if execute:
            NotebookClient(notebook,timeout=2400,kernel_name='python3',resources={'metadata':{'path':str(ROOT)}}).execute()
            nbformat.write(notebook,path)
        records.append({'path':str(path.relative_to(ROOT)).replace('\\','/'),'executed':execute})
        print(path.parent.name+(' executed' if execute else ' validated'))
    if execute:(ROOT/'docs'/'notebook-validation.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')

def main():
    p=argparse.ArgumentParser();p.add_argument('--notebooks',action='store_true');p.add_argument('--skip-tests',action='store_true');args=p.parse_args()
    if not args.skip_tests:subprocess.run([sys.executable,'-m','pytest','-q'],cwd=ROOT,check=True)
    navigation();notebooks(args.notebooks)
    from validate_rendering import validate as rendering
    rendering()
if __name__=='__main__':main()

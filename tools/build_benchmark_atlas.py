"""Compile, render and verify the original TikZ benchmark atlas.

Requires Tectonic 0.17.0, Poppler pdftoppm and pypdf for a fresh build.
The --check mode uses only the Python standard library and verifies committed
sources, all rendered artifacts, section coverage and PNG dimensions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / 'benchmarks/tikz'
OUTPUT = ROOT / 'benchmarks/figures/tikz'


def digest(path, text=False):
    data = path.read_bytes()
    return hashlib.sha256(data.replace(b'\r\n', b'\n') if text else data).hexdigest()


def catalog():
    data = json.loads((SOURCES / 'catalog.json').read_text(encoding='utf-8'))
    cases = data['cases']
    if [c['section'] for c in cases] != [f'3.{i}' for i in range(1, 14)]:
        raise ValueError('The catalog must cover all 13 original sections in order.')
    aliases = [a for c in cases for a in c['aliases']]
    if len(aliases) != len(set(aliases)):
        raise ValueError('Ambiguous benchmark aliases.')
    return data


def stems(data):
    return [s for c in data['cases'] for s in [c['stem'], c.get('companion')] if s]


def source_hashes(data):
    files = [SOURCES / 'common.tex', SOURCES / 'catalog.json', Path(__file__)]
    files += [SOURCES / (s + '.tex') for s in stems(data)]
    return {p.relative_to(ROOT).as_posix(): digest(p, text=True) for p in files}


def gallery(data):
    lines = ['# Benchmark atlas: original names and detailed TikZ drawings', '',
        'Fourteen original vector plates cover the thirteen benchmark sections of Kroll and Schulte (2014). Every plate carries the original section title; the table maps it to the names used in this repository. Section 3.2 is a collection of data resources, and section 3.1 contains two artificial examples.', '',
        '[Download the complete vector PDF](figures/tikz/benchmark-atlas.pdf) · [Editable TikZ sources](tikz/) · [Build and verification record](figures/tikz/build.json)', '',
        'These explanatory reconstructions connect physical equipment, signals and model variants. They are not construction P&IDs. The [source audit](README.md) and [case studies](CASE_STUDIES.md) retain data-access, calibration and simulator limitations; more visual detail does not establish new numerical validation.', '',
        '| Paper section | Original title in the article | Repository names |', '|---|---|---|']
    lines += [f'| {c["section"]} | {c["original_name"]} | '+', '.join(f'`{a}`' for a in c['aliases'])+' |' for c in data['cases']]
    for c in data['cases']:
        s = c['stem']
        lines += ['', f'## {c["section"]} — {c["original_name"]}', '', c['description'], '',
            f'![{c["original_name"]}: detailed model and signal drawing](figures/tikz/{s}.png)', '',
            f'[Vector PDF](figures/tikz/{s}.pdf) · [High-resolution PNG](figures/tikz/{s}.png) · [TikZ source](tikz/{s}.tex)']
        if c.get('companion'):
            s = c['companion']
            lines += ['', f'![Tennessee Eastman: all manipulated and measured signals](figures/tikz/{s}.png)', '',
                f'[Signal-reference PDF](figures/tikz/{s}.pdf) · [TikZ source](tikz/{s}.tex)']
    lines += ['', '## Sources and reproducibility', '',
        'Kroll, A. and Schulte, H. (2014), *'+data['article']['title']+'*, Applied Soft Computing 25, 496–513. [DOI](https://doi.org/'+data['article']['doi']+'). Original headings follow sections 3.1–3.13. The Tennessee Eastman topology was checked against Fig. 13, and its signal names and units against the documented interface in the [Ricker archive](https://depts.washington.edu/control/LARRY/TE/download.html).', '',
        'The pneumatic, hydrostatic, reactor, column and wind drawings also follow the explicit implementation audits linked from the benchmark inventory. The [Tennessee Eastman state-count audit](TE_STATE_COUNT_AUDIT.md) explains the correction from a misleading source comment to the executable `NX=50` declaration. The earlier compact diagrams remain available under `figures/`; current case sheets and the API use the detailed `figures/tikz/` plates.', '',
        'Install Tectonic 0.17.0 and Poppler, then `python -m pip install pypdf`. Run:', '',
        '```bash', 'python tools/build_benchmark_atlas.py', 'python tools/build_benchmark_atlas.py --check', 'python tools/build_api_docs.py', '```', '',
        'Use `--tectonic /path/to/tectonic --pdftoppm /path/to/pdftoppm` when the executables are not on PATH. `--only-cached` disables TeX bundle downloads after the first build. `--assemble-only` packages and checks already compiled/rendered plates; it does not compile changed sources. The committed build record hashes the sources and all artifacts. Inspect every rendered plate after changing a drawing.']
    (ROOT / 'benchmarks/DIAGRAMS.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tectonic', default='tectonic')
    parser.add_argument('--pdftoppm', default='pdftoppm')
    parser.add_argument('--only-cached', action='store_true')
    parser.add_argument('--assemble-only', action='store_true')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    data = catalog()
    names = stems(data)
    record_path = OUTPUT / 'build.json'
    if args.check:
        record = json.loads(record_path.read_text(encoding='utf-8'))
        if record['source_sha256_lf'] != source_hashes(data):
            raise ValueError('Atlas source changed: rebuild and inspect the rendered plates.')
        expected = {s+ext for s in names for ext in ('.pdf','.png')} | {'benchmark-atlas.pdf'}
        if set(record['artifact_sha256']) != expected:
            raise ValueError('Incomplete atlas artifacts.')
        for name, sha in record['artifact_sha256'].items():
            path = OUTPUT / name
            if digest(path) != sha:
                raise ValueError('Atlas artifact changed: '+name)
            if path.suffix == '.png':
                raw = path.read_bytes()
                if raw[:8] != b'\x89PNG\r\n\x1a\n' or max(struct.unpack('>II',raw[16:24])) < 2500:
                    raise ValueError('Invalid or undersized rendering: '+name)
        print(json.dumps({'status':'passed','paper_sections':13,'plates':len(names),'artifacts':len(expected)}))
        return
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if not args.assemble_only:
        for name in names:
            command = [args.tectonic, '--keep-logs', '--outdir', str(OUTPUT)]
            if args.only_cached:
                command += ['--only-cached']
            subprocess.run(command+[name+'.tex'], cwd=SOURCES, check=True)
            subprocess.run([args.pdftoppm,'-singlefile','-scale-to','2600','-png',str(OUTPUT/(name+'.pdf')),str(OUTPUT/name)], check=True)
    from pypdf import PdfReader, PdfWriter
    writer = PdfWriter()
    for c in data['cases']:
        for name in [c['stem']]+([c['companion']] if c.get('companion') else []):
            pdf = PdfReader(OUTPUT/(name+'.pdf'))
            if len(pdf.pages) != 1:
                raise ValueError('Each plate must be one page: '+name)
            if (OUTPUT/(name+'.pdf')).stat().st_mtime < max((SOURCES/(name+'.tex')).stat().st_mtime,(SOURCES/'common.tex').stat().st_mtime):
                raise ValueError('Recompile the changed source before packaging: '+name)
            if (OUTPUT/(name+'.png')).stat().st_mtime < (OUTPUT/(name+'.pdf')).stat().st_mtime:
                raise ValueError('Render the current PDF before packaging: '+name)
            log = (OUTPUT/(name+'.log')).read_text(encoding='utf-8',errors='replace')
            if any(term in log for term in ('Overfull \\','Missing character:','! LaTeX Error')):
                raise ValueError('Unresolved typesetting warning: '+name)
            writer.add_page(pdf.pages[0])
            writer.add_outline_item(c['section']+' '+c['original_name']+(' — signal reference' if name != c['stem'] else ''), len(writer.pages)-1)
    writer.add_metadata({'/Title':'Benchmark atlas — original names, equipment and signal interfaces','/Author':'Intelligent Systems for Process Control and Automation','/Subject':'Kroll and Schulte (2014), sections 3.1–3.13'})
    writer.write(OUTPUT/'benchmark-atlas.pdf')
    artifacts = {s+ext: digest(OUTPUT/(s+ext)) for s in names for ext in ('.pdf','.png')}
    artifacts['benchmark-atlas.pdf'] = digest(OUTPUT/'benchmark-atlas.pdf')
    record = {'generator':'Tectonic 0.17.0 / TikZ + Poppler pdftoppm + pypdf',
        'paper_sections':13,'plates':len(names),'png_long_edge':2600,
        'source_sha256_lf':source_hashes(data),'artifact_sha256':artifacts,
        'scope':'Original explanatory diagrams; numerical validation status is unchanged.'}
    record_path.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    gallery(data)
    print(json.dumps({'status':'built','plates':len(names),'atlas':'benchmarks/figures/tikz/benchmark-atlas.pdf'}))


if __name__ == '__main__':
    main()

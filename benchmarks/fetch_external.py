"""Fetch hash-pinned official source files without executing them."""
from pathlib import Path
import argparse
import hashlib
import json
import urllib.request
import zipfile

HERE=Path(__file__).resolve().parent


def fetch(name, local_file=None):
    item=json.loads((HERE/'external_sources.json').read_text(encoding='utf-8'))['sources'][name]
    target=HERE/'external'/name
    target.mkdir(parents=True,exist_ok=True)
    dest=target/item['filename']
    if local_file is not None:
        data=Path(local_file).read_bytes()
    else:
        data=dest.read_bytes() if dest.exists() else urllib.request.urlopen(item['url'],timeout=60).read()
    actual=hashlib.sha256(data).hexdigest()
    if actual!=item['sha256']:
        raise ValueError(f'Source hash changed for {name}; inspect provenance before accepting it')
    if dest.exists() and dest.read_bytes()!=data:
        raise FileExistsError(f'Preserving modified local archive: {dest}')
    if not dest.exists(): dest.write_bytes(data)
    if item['extract']:
        with zipfile.ZipFile(dest) as archive:
            for member in archive.infolist():
                relative=Path(member.filename.replace('\\','/'))
                output=(target/relative).resolve()
                if not output.is_relative_to(target.resolve()) or relative.is_absolute():
                    raise ValueError('Archive member escapes destination')
                mode=member.external_attr>>16
                if mode & 0o170000 == 0o120000:
                    raise ValueError('Archive symlinks are not accepted')
                if member.is_dir(): output.mkdir(parents=True,exist_ok=True)
                else:
                    output.parent.mkdir(parents=True,exist_ok=True)
                    payload=archive.read(member)
                    if output.exists() and output.read_bytes()!=payload:
                        raise FileExistsError(f'Preserving modified local source: {output}')
                    output.write_bytes(payload)
    (target/'provenance.json').write_text(json.dumps(item,indent=2),encoding='utf-8')
    print(f'Verified {name}: {actual}; stored at {target}')


if __name__=='__main__':
    sources=json.loads((HERE/'external_sources.json').read_text(encoding='utf-8'))['sources']
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--list',action='store_true')
    parser.add_argument('--source',choices=sources)
    parser.add_argument('--local-file',type=Path,help='Verify a provider archive obtained through its normal browser download flow')
    args=parser.parse_args()
    if args.list:
        for name,item in sources.items(): print(name,':',item['version'])
    elif args.source: fetch(args.source,args.local_file)
    else: parser.error('choose --list or --source')

"""Fetch and execute a pinned official OpenFAST 5 MW regression case on Windows.

The current OpenFAST case is a versioned successor demonstration, not a
reproduction of the 2014 survey's FAST/controller experiment. Downloaded
third-party files remain under ignored external/; only evidence is committed.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import urllib.request

import numpy as np

HERE = Path(__file__).resolve().parent


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def checked_download(url, path, expected, git_blob=False):
    path = Path(path)
    payload = path.read_bytes() if path.exists() else urllib.request.urlopen(url, timeout=90).read()
    digest = (hashlib.sha1(b'blob ' + str(len(payload)).encode() + b'\0' + payload).hexdigest()
              if git_blob else sha256(payload))
    if digest != expected:
        raise ValueError(f'Source checksum mismatch: {path.name}')
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(payload)
    return {'path': str(path), 'sha256': sha256(payload), 'bytes': len(payload)}


def fetch(root):
    manifest = json.loads((HERE / 'openfast_manifest.json').read_text(encoding='utf-8'))
    work = []
    for item in manifest['assets']:
        work.append((item['url'], root / 'bin' / item['name'], item['sha256'], False))
    for item in manifest['files']:
        relative = item['path'].removeprefix('glue-codes/openfast/')
        url = f"https://raw.githubusercontent.com/OpenFAST/r-test/{manifest['rtest_commit']}/{item['path']}"
        work.append((url, root / 'inputs' / relative, item['git_blob_sha1'], True))
    with ThreadPoolExecutor(max_workers=6) as pool:
        records = list(pool.map(lambda args: checked_download(*args), work))
    for record in records:
        record['path'] = str(Path(record['path']).relative_to(root)).replace('\\', '/')
    (root / 'download-evidence.json').write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
    return manifest, records


def replace_parameter(text, name, value):
    pattern = re.compile(r'^(\s*)(?:"[^"]*"|\S+)(\s+' + re.escape(name) + r'\s+.*)$', re.MULTILINE)
    result, count = pattern.subn(lambda m: m.group(1) + value + m.group(2), text)
    if count != 1:
        raise ValueError(f'Expected one parameter {name}; found {count}')
    return result


def read_ascii(path):
    lines = Path(path).read_text(encoding='utf-8', errors='strict').splitlines()
    index = next(i for i, line in enumerate(lines) if line.split()[:1] == ['Time'])
    names, units = lines[index].split(), lines[index + 1].split()
    values = np.loadtxt(lines[index + 2:])
    if values.ndim != 2 or values.shape[1] != len(names) or not np.isfinite(values).all():
        raise ValueError('Invalid OpenFAST output matrix')
    if len(units) != len(names) or np.any(np.diff(values[:, 0]) <= 0):
        raise ValueError('Invalid channel units or output time alignment')
    return names, units, values


def read_uncompressed_reference(path):
    """Read OpenFAST binary FileID3 (documented uncompressed regression format).

    Format reference: OpenFAST/openfast_toolbox, io/fast_output_file.py.
    Deliberately refuses other encodings instead of guessing their scaling.
    """
    with Path(path).open('rb') as stream:
        def take(dtype, count):
            value = np.fromfile(stream, dtype=dtype, count=count)
            if len(value) != count:
                raise ValueError('Truncated OpenFAST reference file')
            return value
        if take('<i2', 1)[0] != 3:
            raise ValueError('Expected uncompressed OpenFAST FileID3')
        channels, rows = take('<i4', 2)
        if not (1 <= channels <= 1000 and 1 <= rows <= 1000000):
            raise ValueError('Invalid reference dimensions')
        start, step = take('<f8', 2)
        description_length = int(take('<i4', 1)[0])
        if not 0 <= description_length <= 100000:
            raise ValueError('Invalid reference description')
        take('u1', description_length)
        names = [take('u1', 10).tobytes().decode('ascii').strip() for _ in range(channels + 1)]
        units = [take('u1', 10).tobytes().decode('ascii').strip() for _ in range(channels + 1)]
        data = take('<f8', int(rows * channels)).reshape(rows, channels)
        if stream.read(1):
            raise ValueError('Unexpected trailing reference bytes')
    return names, units, np.column_stack([start + step * np.arange(rows), data])


def compare_reference(names, values, reference_path):
    reference_names, _, reference = read_uncompressed_reference(reference_path)
    if names != reference_names or values.shape != reference.shape:
        raise AssertionError('Official reference channel/shape mismatch')
    # OpenFAST's text time column is rounded to four decimal places.
    np.testing.assert_allclose(values[:, 0], reference[:, 0], atol=5.1e-5, rtol=0)
    scale = np.maximum(1, np.max(np.abs(reference[:, 1:]), axis=0))
    difference = values[:, 1:] - reference[:, 1:]
    # Rotor azimuth is periodic: 359.999 and 0.001 degrees are 0.002 apart.
    if 'Azimuth' in names:
        angle = names.index('Azimuth') - 1
        difference[:, angle] = (difference[:, angle] + 180) % 360 - 180
    normalized_rmse = np.sqrt(np.mean(difference ** 2, axis=0)) / scale
    # Declared cross-compiler single-precision engineering tolerance, per channel.
    if not np.isfinite(normalized_rmse).all() or np.max(normalized_rmse) > .01:
        raise AssertionError(f'Official reference discrepancy: {np.max(normalized_rmse)} exceeds 0.01')
    return {'status': 'passed', 'channels_compared': len(names) - 1,
            'normalization': 'max(1, peak absolute reference channel value)',
            'azimuth_difference': 'shortest signed angular difference modulo 360 degrees',
            'normalized_rmse_tolerance': .01,
            'maximum_normalized_rmse': float(np.max(normalized_rmse)),
            'worst_channel': names[1 + int(np.argmax(normalized_rmse))],
            'reference_sha256': sha256(Path(reference_path).read_bytes())}


def run(root, output):
    if os.name != 'nt':
        raise RuntimeError('The pinned release assets are Windows executables; use a separately pinned native build elsewhere.')
    manifest, downloaded = fetch(root)
    case_name = manifest['case']
    work = root / 'runs' / case_name
    if work.exists():
        raise FileExistsError(f'Choose a new external directory; run already exists: {work}')
    work.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(root / 'inputs' / case_name, work)
    shutil.copytree(root / 'inputs' / '5MW_Baseline', work.parent / '5MW_Baseline')
    fst = work / f'{case_name}.fst'
    # Change output encoding only; preserve duration, time step and dynamics.
    fst.write_text(replace_parameter(fst.read_text(encoding='utf-8'), 'OutFileFmt', '1'), encoding='utf-8')
    servo = work / 'NRELOffshrBsline5MW_Onshore_ServoDyn.dat'
    servo.write_text(replace_parameter(servo.read_text(encoding='utf-8'), 'DLL_FileName',
                                     '"' + (root / 'bin' / 'DISCON.dll').as_posix() + '"'), encoding='utf-8')
    exe = root / 'bin' / 'OpenFAST.exe'
    version = subprocess.run([str(exe), '-v'], capture_output=True, text=True, check=True).stdout.strip()
    result = subprocess.run([str(exe), fst.name], cwd=work, capture_output=True, text=True, timeout=600)
    (work / 'execution.log').write_text(result.stdout + '\n' + result.stderr, encoding='utf-8')
    if result.returncode:
        raise RuntimeError(f'OpenFAST failed ({result.returncode}): {result.stdout[-4000:]} {result.stderr[-2000:]}')
    names, units, values = read_ascii(work / f'{case_name}.out')
    if abs(values[-1, 0] - 60.0) > 1e-5 or len(values) < 9000:
        raise AssertionError('Official 60-second run did not complete')
    channels = ['RotSpeed', 'GenSpeed', 'GenPwr', 'BldPitch1', 'TwrBsMyt']
    selected = [names.index(name) for name in channels]
    evidence = {
        'date': '2026-11-04', 'status': 'passed', 'release': manifest['release'],
        'rtest_commit': manifest['rtest_commit'], 'case': case_name,
        'runtime': version, 'sample_count': len(values), 'duration_s': float(values[-1, 0]),
        'dt_s': float(np.median(np.diff(values[:, 0]))), 'channel_count_including_time': len(names),
        'all_outputs_finite': True, 'source_files_verified': len(downloaded),
        'changes': ['Output format 4 (binary) to 1 (text)', 'Controller path points to official same-release DISCON.dll'],
        'interpretation': 'Official 60-second NREL 5 MW onshore turbulent-wind case; OpenFAST successor, not 2014 table reproduction.',
        'selected_channels': {names[i]: {'unit': units[i], 'minimum': float(values[:, i].min()),
                                        'maximum': float(values[:, i].max()), 'final': float(values[-1, i])}
                              for i in selected},
        'output_sha256': sha256((work / f'{case_name}.out').read_bytes()),
        'manifest_sha256': sha256((HERE / 'openfast_manifest.json').read_bytes()),
        'binary_sha256': sha256(exe.read_bytes()),
        'log_sha256': sha256((work / 'execution.log').read_bytes()),
        'official_reference_comparison': compare_reference(names, values, root / 'inputs' / case_name / f'{case_name}.outb'),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    # A compact inspection trace; complete official outputs remain external.
    np.savetxt(output.with_suffix('.csv'), values[::16, [0] + selected], delimiter=',',
               header=','.join(['time_s'] + channels), comments='')
    print(json.dumps(evidence, indent=2))
    return evidence


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--external-dir', type=Path, default=HERE / 'external' / 'openfast-v5')
    parser.add_argument('--output', type=Path, default=HERE / 'results' / 'openfast-validation.json')
    parser.add_argument('--fetch-only', action='store_true')
    args = parser.parse_args()
    destination = args.external_dir.resolve()
    if args.fetch_only:
        info, records = fetch(destination)
        print(f"Verified {len(records)} source files for {info['release']}")
    else:
        run(destination, args.output.resolve())

"""Check the author's local ALSTOM package without executing its Windows MEX."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import struct

import numpy as np
from scipy.io import loadmat

HERE = Path(__file__).resolve().parent


def inspect(source):
    source = Path(source)
    manifest = json.loads((HERE / 'alstom_manifest.json').read_text(encoding='utf-8'))
    for entry in manifest['source_files']:
        content = (source / entry['relative_path']).read_bytes()
        if hashlib.sha256(content).hexdigest() != entry['sha256']:
            raise ValueError(f"Modified official package file: {entry['relative_path']}")
    binary = (source / 'PI_closed_loop/gasifier.mexw64').read_bytes()
    pe_offset = struct.unpack_from('<I', binary, 0x3c)[0]
    assert binary[:2] == b'MZ' and binary[pe_offset:pe_offset + 4] == b'PE\0\0'
    assert struct.unpack_from('<H', binary, pe_offset + 4)[0] == 0x8664, 'Expected x64 Windows PE'
    dlls = sorted({s.decode() for s in re.findall(rb'[A-Za-z0-9_.-]+\.dll', binary)})
    assert {'libmx.dll', 'libmex.dll', 'MSVCR100.dll'}.issubset(dlls)
    loads = []
    previous_demands = None
    for load in (0, 50, 100):
        data = loadmat(source / f'PI_closed_loop/clss{load}_x.mat', simplify_cells=True)
        assert data['ld_sp'] == load
        assert data['dem'].shape == (7, 3) and np.isfinite(data['dem']).all()
        if previous_demands is not None:
            np.testing.assert_array_equal(data['dem'], previous_demands)
        previous_demands = data['dem']
        signals = data['x0c']['signals']
        dimensions = [int(s['dimensions']) for s in signals]
        assert dimensions == [25, 1, 1, 1], 'Expected plant plus three PI integrators'
        for signal in signals:
            assert np.asarray(signal['values']).size == signal['dimensions']
            assert np.isfinite(signal['values']).all()
        assert signals[0]['blockName'] == 'cgasifier_cl/Gasifier/S-Function'
        assert data['ld_final'] == data['distsine'] == data['diststep'] == 0
        loads.append({'load_percent': load, 'plant_states': 25, 'controller_states': 3,
                      'air_initial_temperature_K': float(data['tair0']),
                      'finite_initial_conditions': True})
    model = (source / 'PI_closed_loop/cgasifier_cl.mdl').read_text(encoding='cp1252')
    for expression in ('2e4 * distsine', '0.04*2*pi', '-0.2e5 * diststep',
                       'ld_sp + ld_final', 'gasifier', 'x0c'):
        assert f'"{expression}"' in model, f'Missing official model expression {expression}'
    return {'date': '2026-11-04', 'status': 'source_inspection_passed',
            'native_simulation_status': 'not_executed_requires_compatible_Windows_MATLAB',
            'archive_sha256': manifest['archive_sha256'],
            'verified_source_files': manifest['source_files'], 'initial_conditions': loads,
            'binary_architecture': 'Windows PE AMD64', 'binary_DLL_strings': dlls,
            'plant_source_code_supplied': False,
            'scope': 'Integrity, initial-state dimensions, finite values and official input expressions only; no plant trajectory or controller performance claim'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, default=HERE / 'external/alstom-gasifier/Gasifier_R2017')
    parser.add_argument('--report', type=Path, default=HERE / 'results/alstom-source-inspection.json')
    args = parser.parse_args()
    result = inspect(args.source_dir)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('ALSTOM source inspection passed; native simulation remains pending.')

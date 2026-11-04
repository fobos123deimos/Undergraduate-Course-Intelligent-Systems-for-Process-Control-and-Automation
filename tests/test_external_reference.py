"""Offline tests of external-source integrity and regression evidence parsing."""
from pathlib import Path
import importlib.util
import struct
import numpy as np
import pytest

SPEC = importlib.util.spec_from_file_location('openfast_reference', Path(__file__).resolve().parents[1] / 'benchmarks/run_openfast_reference.py')
reference = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reference)


def binary_fixture(path, values):
    names = ['Time', 'Azimuth', 'RotSpeed']
    with path.open('wb') as stream:
        stream.write(struct.pack('<hiidd', 3, 2, len(values), 0., .5))
        stream.write(struct.pack('<i', 0))
        for item in names + ['(s)', '(deg)', '(rpm)']:
            stream.write(item.encode().ljust(10))
        stream.write(np.asarray(values, dtype='<f8').tobytes())
    return names


def test_official_format_reader_and_circular_azimuth(tmp_path):
    path = tmp_path / 'reference.outb'
    names = binary_fixture(path, [[359.999, 12.], [.001, 12.1]])
    got_names, _, values = reference.read_uncompressed_reference(path)
    assert got_names == names
    np.testing.assert_allclose(values[:, 0], [0., .5])
    candidate = values.copy(); candidate[:, 1] += [360., -360.]
    result = reference.compare_reference(names, candidate, path)
    assert result['status'] == 'passed'
    assert result['maximum_normalized_rmse'] < 1e-14
    candidate[:, 2] += 2
    with pytest.raises(AssertionError, match='discrepancy'):
        reference.compare_reference(names, candidate, path)


def test_truncated_binary_and_nonmonotonic_ascii_are_rejected(tmp_path):
    path = tmp_path / 'bad.outb'; path.write_bytes(struct.pack('<h', 3))
    with pytest.raises(ValueError, match='Truncated'):
        reference.read_uncompressed_reference(path)
    text = tmp_path / 'bad.out'; text.write_text('Time RotSpeed\n(s) (rpm)\n0 12\n0 12\n')
    with pytest.raises(ValueError, match='alignment'):
        reference.read_ascii(text)


def test_cached_source_checksum_rejects_modified_content(tmp_path):
    path = tmp_path / 'data'; path.write_bytes(b'modified')
    with pytest.raises(ValueError, match='checksum'):
        reference.checked_download('https://example.invalid', path, reference.sha256(b'original'))
    assert path.read_bytes() == b'modified'


def test_parameter_replacement_is_exact_and_keeps_other_lines():
    text = '4   OutFileFmt - encoding\n60 TMax - seconds\n'
    assert reference.replace_parameter(text, 'OutFileFmt', '1') == '1   OutFileFmt - encoding\n60 TMax - seconds\n'
    with pytest.raises(ValueError, match='found 0'):
        reference.replace_parameter(text, 'DT', '.01')
    with pytest.raises(ValueError, match='found 2'):
        reference.replace_parameter(text + text, 'OutFileFmt', '1')

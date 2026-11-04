"""Offline tests of external-source integrity and regression evidence parsing."""
from pathlib import Path
import importlib.util
import struct
import hashlib
import io
import json
import zipfile
import numpy as np
import pytest

SPEC = importlib.util.spec_from_file_location('openfast_reference', Path(__file__).resolve().parents[1] / 'benchmarks/run_openfast_reference.py')
reference = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reference)
FETCH_SPEC = importlib.util.spec_from_file_location('external_fetch', Path(__file__).resolve().parents[1] / 'benchmarks/fetch_external.py')
fetcher = importlib.util.module_from_spec(FETCH_SPEC)
FETCH_SPEC.loader.exec_module(fetcher)
SUMMARY_SPEC = importlib.util.spec_from_file_location('benchmark_summary', Path(__file__).resolve().parents[1] / 'benchmarks/run_benchmarks.py')
summary = importlib.util.module_from_spec(SUMMARY_SPEC)
SUMMARY_SPEC.loader.exec_module(summary)


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


def local_archive(tmp_path, monkeypatch, members):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        for name, content in members:
            archive.writestr(name, content)
    payload = buffer.getvalue()
    path = tmp_path / 'provider-download.zip'; path.write_bytes(payload)
    manifest = {'sources': {'case': {'filename': 'source.zip', 'url': 'https://example.invalid',
                'sha256': hashlib.sha256(payload).hexdigest(), 'extract': True}}}
    (tmp_path / 'external_sources.json').write_text(json.dumps(manifest))
    monkeypatch.setattr(fetcher, 'HERE', tmp_path)
    def refuse_network(*args, **kwargs):
        raise AssertionError('A local provider archive must not trigger network access')
    monkeypatch.setattr(fetcher.urllib.request, 'urlopen', refuse_network)
    return path


def test_local_provider_archive_integrity_and_preservation(tmp_path, monkeypatch):
    path = local_archive(tmp_path, monkeypatch, [('package/model.mdl', 'official')])
    fetcher.fetch('case', path)
    extracted = tmp_path / 'external/case/package/model.mdl'
    assert extracted.read_text() == 'official'
    extracted.write_text('local changes')
    with pytest.raises(FileExistsError, match='modified local source'):
        fetcher.fetch('case', path)
    assert extracted.read_text() == 'local changes'
    path.write_bytes(b'wrong version')
    with pytest.raises(ValueError, match='hash changed'):
        fetcher.fetch('case', path)


@pytest.mark.parametrize('member', ['../../escaped.mdl', '/absolute.mdl'])
def test_local_archive_refuses_paths_outside_destination(tmp_path, monkeypatch, member):
    path = local_archive(tmp_path, monkeypatch, [(member, 'bad')])
    with pytest.raises(ValueError, match='escapes destination'):
        fetcher.fetch('case', path)
    assert not (tmp_path / 'escaped.mdl').exists()


def test_external_summary_does_not_promote_missing_or_failed_evidence(tmp_path, monkeypatch):
    monkeypatch.setattr(summary, 'ROOT', tmp_path)
    entries = summary.external_status()
    for entry in entries.values():
        assert entry['evidence_state'] == 'missing'
        assert entry['rerun_by_this_command'] is False
    path = tmp_path / 'benchmarks/results/openfast-validation.json'
    path.parent.mkdir(parents=True)
    path.write_text('{"status":"failed"}')
    entries = summary.external_status()
    assert entries['wind_fast']['evidence_state'] == 'incomplete_or_not_passed'
    assert 'no complete passed' in entries['wind_fast']['status']
    path.write_text('{"status":"passed"}')
    assert summary.external_status()['wind_fast']['evidence_state'] in {'invalid', 'incomplete_or_not_passed'}


def test_external_summary_links_preserved_results_without_claiming_a_rerun():
    entries = summary.external_status()
    for key in ('wind_fast', 'tennessee_eastman'):
        entry = entries[key]
        assert entry['evidence_state'] == 'preserved_passed_record'
        assert entry['rerun_by_this_command'] is False
        assert entry['evidence_sha256'] == hashlib.sha256((summary.ROOT / entry['evidence_path']).read_bytes()).hexdigest()
    assert entries['gasifier']['rerun_by_this_command'] is False
    assert entries['gasifier']['source_inspection']['evidence_state'] == 'preserved_passed_record'

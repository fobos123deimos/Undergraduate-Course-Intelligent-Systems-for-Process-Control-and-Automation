"""Private simulator transport must preserve the pinned provider bytes."""
import base64
import hashlib
import importlib.util
from pathlib import Path
import sys

import pytest

BENCHMARKS = Path(__file__).resolve().parents[1] / 'benchmarks'
sys.path.insert(0, str(BENCHMARKS))
spec = importlib.util.spec_from_file_location('alstom_transport', BENCHMARKS / 'prepare_alstom_ci.py')
transport = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transport)


def fixture_parts():
    payload = b'Synthetic transport fixture; not a plant model.'
    encoded = base64.b64encode(payload).decode('ascii')
    parts = [encoded[i*len(encoded)//17:(i+1)*len(encoded)//17] for i in range(17)]
    return payload, parts, hashlib.sha256(payload).hexdigest()


def test_private_transport_preserves_exact_bytes():
    payload, parts, digest = fixture_parts()
    assert transport.decode_archive(parts, digest, len(payload)) == payload


def test_absent_inputs_allow_only_the_explicit_provider_path():
    assert transport.decode_archive(['']*17, 'unused', 10) is None


def test_partial_private_inputs_are_not_silently_ignored():
    payload, parts, digest = fixture_parts()
    parts[5] = ''
    with pytest.raises(ValueError, match='Incomplete'):
        transport.decode_archive(parts, digest, len(payload))


def test_reordered_or_changed_archive_is_rejected():
    payload, parts, digest = fixture_parts()
    with pytest.raises(ValueError):
        transport.decode_archive(parts[::-1], digest, len(payload))
    with pytest.raises(ValueError, match='integrity'):
        transport.decode_archive(parts, '0'*64, len(payload))


def test_invalid_encoding_and_size_are_rejected():
    payload, parts, digest = fixture_parts()
    parts[0] = '!' + parts[0][1:]
    with pytest.raises(ValueError, match='encoding'):
        transport.decode_archive(parts, digest, len(payload))
    with pytest.raises(ValueError, match='length'):
        transport.decode_archive(parts, digest, len(payload)+10)

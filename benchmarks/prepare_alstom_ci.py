"""Prepare the verified author package without publishing its contents.

Default: ordinary download from the recorded provider. If all thirteen
ALSTOM_ARCHIVE_01..13 private repository inputs are present, decode their
ordered base64 chunks instead. Never print those values or upload the archive.
"""
from pathlib import Path
import base64
import hashlib
import json
import os
import tempfile

from fetch_external import fetch

HERE = Path(__file__).resolve().parent
PART_COUNT = 13
ARCHIVE_BYTES = 452992


def decode_archive(parts, expected_sha256, expected_size):
    if len(parts) != PART_COUNT:
        raise ValueError('Expected thirteen ordered private input slots')
    if not any(parts):
        return None
    if not all(parts):
        raise ValueError('Incomplete private archive inputs; no download fallback')
    encoded = ''.join(parts)
    if len(encoded) != 4 * ((expected_size + 2) // 3):
        raise ValueError('Private archive encoded length does not match the pinned source')
    try:
        payload = base64.b64decode(encoded, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise ValueError('Private archive encoding is invalid') from exc
    if len(payload) != expected_size or hashlib.sha256(payload).hexdigest() != expected_sha256:
        raise ValueError('Private archive integrity check failed')
    return payload


def main():
    manifest = json.loads((HERE / 'alstom_manifest.json').read_text(encoding='utf-8'))
    parts = [os.environ.get(f'ALSTOM_ARCHIVE_{i:02d}', '') for i in range(1, PART_COUNT + 1)]
    payload = decode_archive(parts, manifest['archive_sha256'], ARCHIVE_BYTES)
    if payload is None:
        print('ALSTOM source: ordinary provider download')
        fetch('alstom-gasifier')
    else:
        with tempfile.TemporaryDirectory(prefix='alstom-source-') as folder:
            path = Path(folder) / 'author-package.zip'
            path.write_bytes(payload)
            fetch('alstom-gasifier', path)
        print('ALSTOM source: verified private repository inputs')


if __name__ == '__main__':
    main()

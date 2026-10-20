"""Lossless monitor snapshot storage identity, separate from policy semantics.

The archive writer verifies the complete gzip round trip once. Consumers bind
its original bytes/identity to the exact compressed generation and its digest;
projection/census, cost and policy checks remain with their existing owners.
No uncompressed temporary file or persistent validator verdict is required.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
from pathlib import Path
import stat

SCHEMA = 'monitor_snapshot_archive_identity_v1'
MAX_RECEIPT_BYTES = 128 * 1024


def logical_path(path):
    path = Path(path)
    return path.with_suffix('') if path.name.endswith('.json.gz') else path


def file_identity(value):
    return dict(device=value.st_dev, inode=value.st_ino, size=value.st_size,
                mtime_ns=value.st_mtime_ns, ctime_ns=value.st_ctime_ns)


def _regular(path):
    if path.is_symlink() or any(p.is_symlink() for p in path.parents):
        raise ValueError('snapshot_archive_path_invalid')
    value = path.stat()
    if not stat.S_ISREG(value.st_mode) or value.st_uid != os.getuid():
        raise ValueError('snapshot_archive_path_invalid')
    return file_identity(value)


def _digest(path):
    from src.engine.infrastructure.validation_digest_session import reused_digest
    cached = reused_digest(path)
    if cached is not None:
        return cached
    before = _regular(path)
    with path.open('rb') as handle:
        value = hashlib.file_digest(handle, 'sha256').hexdigest()
    if _regular(path) != before:
        raise ValueError('snapshot_archive_changed_during_read')
    return value


def archived_receipt(path, *, bound_logical_generation=None):
    """Verify bytes, or native custody of a cold-verified logical generation.

    The latter requires the archiver's sealed exact physical epoch and the
    consumer's independently cold-bound logical bytes. It grants no semantics.
    """
    path = logical_path(path)
    archived = Path(str(path) + '.gz')
    if path.is_symlink():
        raise ValueError('snapshot_archive_path_invalid')
    receipt_path = Path(str(archived) + '.archive_receipt.json')
    before = _regular(archived)
    receipt_before = _regular(receipt_path)
    if receipt_before['size'] > MAX_RECEIPT_BYTES:
        raise ValueError('snapshot_archive_receipt_unbounded')
    with receipt_path.open('rb') as handle:
        raw = handle.read(MAX_RECEIPT_BYTES + 1)
    if len(raw) > MAX_RECEIPT_BYTES:
        raise ValueError('snapshot_archive_receipt_unbounded')
    receipt = json.loads(raw)
    seal=receipt.get('artifact_content_sha256')
    if seal is not None:
        expected=hashlib.sha256(json.dumps({k:v for k,v in receipt.items() if k!='artifact_content_sha256'},
            ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
        if seal!=expected:
            raise ValueError('snapshot_archive_receipt_seal_invalid')
        # A new native archiver has already verified SHA, size and CRC to EOF.
        # Reuse only that exact unchanged compressed byte epoch; semantic
        # census/cost/policy validation still runs in every native consumer.
        from src.engine.infrastructure.validation_digest_session import ACTIVE
        session=ACTIVE.get()
        bound=receipt.get('archive_generation') or {}
        if (session is not None and session.binding['role']=='postclose'
                and bound==before and receipt.get('schema')==SCHEMA):
            session.admit_native_generation(archived,
                dict(path=archived.name,size=before['size'],sha256=receipt.get('archive_sha256')),
                [before[key] for key in ('device','inode','size','mtime_ns','ctime_ns')],proof_sha256=seal)
    original = receipt.get('original_identity') or {}
    logical_size = receipt.get('logical_size_bytes')
    bound = bound_logical_generation
    if bound is not None and (seal is None or not isinstance(bound, dict)
            or bound != dict(path=path.name, size=logical_size,
                            sha256=receipt.get('logical_content_sha256'))):
        raise ValueError('snapshot_archive_logical_generation_changed')
    if (receipt.get('schema') != SCHEMA
            or receipt.get('logical_path') != str(path)
            or receipt.get('archive_generation') != before
            or receipt.get('runtime_effect') is not False
            or receipt.get('allowed_runtime_apply') is not False
            or type(logical_size) is not int or logical_size < 0
            or original.get('size') != logical_size
            or set(original) != {'device','inode','size','mtime_ns','ctime_ns'}
            or not isinstance(receipt.get('logical_content_sha256'), str)
            or len(receipt['logical_content_sha256']) != 64
            or not isinstance(receipt.get('archive_sha256'), str)
            or len(receipt['archive_sha256']) != 64
            or any(c not in '0123456789abcdef' for c in receipt['archive_sha256'])
            or (bound is None and _digest(archived) != receipt.get('archive_sha256'))):
        raise ValueError('snapshot_archive_receipt_invalid')
    if _regular(archived) != before or _regular(receipt_path) != receipt_before:
        raise ValueError('snapshot_archive_changed_during_read')
    return receipt


def snapshot_identity(path):
    """The producer's original inode identity survives verified gzip storage."""
    path = logical_path(path)
    if path.exists() or path.is_symlink():
        return _regular(path)
    return archived_receipt(path)['original_identity']


def snapshot_identity_matches(path, expected, *, expected_sha256=None):
    """Revalidate unchanged bytes when evidence preservation changed ctime.

    The expected identity comes from a sealed native projection. A sole ctime
    change additionally requires its sealed full source SHA, or the original
    native postclose manifest. This grants no semantic or policy approval.
    """
    path = logical_path(path)
    current = snapshot_identity(path)
    if current == expected:
        return True
    if (not isinstance(expected, dict) or set(expected) != set(current)
            or any(current[key] != expected[key] for key in current if key != 'ctime_ns')
            or path.is_symlink()):
        return False
    manifest_path = None
    if expected_sha256 is None:
        from datetime import date
        day = path.name.removeprefix('trade_review_').removesuffix('.json')
        if path.name != f'trade_review_{date.fromisoformat(day).isoformat()}.json':
            return False
        manifest_path = path.parent/'manifests'/f'monitor_snapshot_manifest_{day}_postclose_exit.json'
        manifest_before = _regular(manifest_path)
        if manifest_before['size'] > MAX_RECEIPT_BYTES:
            return False
        manifest = json.loads(manifest_path.read_bytes())
        if (manifest.get('target_date') != day or manifest.get('profile') != 'postclose_exit'
                or (manifest.get('snapshot_paths') or {}).get('trade_review') != str(path)):
            return False
        expected_sha256 = (manifest.get('snapshot_sha256') or {}).get('trade_review')
    if (not isinstance(expected_sha256, str) or len(expected_sha256) != 64
            or any(c not in '0123456789abcdef' for c in expected_sha256)):
        return False
    # Native compression verifies the full logical bytes once and binds them
    # to the exact compressed epoch. A preserved inode's ctime can also have
    # changed before compression; use the same original full-SHA authority.
    observed = generation(path)
    if (observed['size'] != current['size'] or observed['sha256'] != expected_sha256
            or snapshot_identity(path) != current):
        return False
    return manifest_path is None or _regular(manifest_path) == manifest_before


def generation(path):
    """Return the same logical generation before and after native compression."""
    path = logical_path(path)
    if path.exists() or path.is_symlink():
        before = _regular(path)
        value = dict(path=path.name, size=before['size'], sha256=_digest(path))
        if _regular(path) != before:
            raise ValueError('snapshot_archive_changed_during_read')
        if Path(str(path) + '.gz.archive_receipt.json').exists():
            receipt = archived_receipt(path)
            if (receipt['logical_size_bytes'] != value['size']
                    or receipt['logical_content_sha256'] != value['sha256']):
                raise ValueError('snapshot_archive_plain_gzip_conflict')
        return value
    receipt = archived_receipt(path)
    return dict(path=path.name, size=receipt['logical_size_bytes'],
                sha256=receipt['logical_content_sha256'])


def read_bytes(path, *, maximum):
    """Bound decoded bytes, validate gzip CRC, and retain the logical hash."""
    path = logical_path(path)
    if path.is_symlink():
        raise ValueError('snapshot_archive_path_invalid')
    archived = Path(str(path) + '.gz')
    if path.exists():
        before = _regular(path)
        if before['size'] > maximum:
            raise ValueError('snapshot_archive_decoded_size_limit')
        with path.open('rb') as handle:
            raw = handle.read(maximum + 1)
        if len(raw) != before['size'] or _regular(path) != before:
            raise ValueError('snapshot_archive_changed_during_read')
        if Path(str(archived)+'.archive_receipt.json').exists():
            receipt = archived_receipt(path)
            if (receipt['logical_size_bytes'] != len(raw)
                    or receipt['logical_content_sha256'] != hashlib.sha256(raw).hexdigest()):
                raise ValueError('snapshot_archive_plain_gzip_conflict')
        return raw
    if not path.exists() and archived.exists() and not Path(str(archived)+'.archive_receipt.json').exists():
        # Older archives have no transferable inode identity. Their small
        # report bytes can still be checked against the policy's original SHA.
        before = _regular(archived)
        with gzip.open(archived, 'rb') as handle:
            raw = handle.read(maximum + 1)
        if len(raw) > maximum or _regular(archived) != before:
            raise ValueError('snapshot_archive_decoded_size_limit')
        return raw
    before = generation(path)
    if before['size'] > maximum:
        raise ValueError('snapshot_archive_decoded_size_limit')
    physical = Path(str(path) + '.gz')
    opener = gzip.open if physical.suffix == '.gz' else open
    with opener(physical, 'rb') as handle:
        raw = handle.read(maximum + 1)
    if (len(raw) > maximum or len(raw) != before['size']
            or hashlib.sha256(raw).hexdigest() != before['sha256']
            or generation(path) != before):
        raise ValueError('snapshot_archive_changed_during_read')
    return raw


def present(path):
    path = logical_path(path)
    return path.exists() or path.is_symlink() or Path(str(path) + '.gz').exists()


def identity_available(path):
    """Legacy gzip alone cannot invent a formerly unrecorded raw inode."""
    path = logical_path(path)
    return path.exists() or path.is_symlink() or (
        Path(str(path)+'.gz').exists() and Path(str(path)+'.gz.archive_receipt.json').is_file())

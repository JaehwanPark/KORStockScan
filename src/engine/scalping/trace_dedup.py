"""Rebuildable, bounded-step indexes for the existing append-only AI files.

Owned by the trace writer, not the execution outbox. No copied payload ledger.
The caller holds the artifact generation lease while reading or appending.
"""
from collections import OrderedDict
from dataclasses import dataclass, field
import json
import hashlib
import os
import threading


class IndexNotReady(ValueError):
    pass


@dataclass
class Index:
    inode: tuple
    offset: int = 0
    mtime_ns: int = 0
    keys: set = field(default_factory=set)
    digests: dict = field(default_factory=dict)
    ready: bool = False
    tail: bytes = b''
    pending: bytes = b''
    observed_identity: tuple | None = None
    pending_reason: str = ''
    pending_verified_bytes: int = 0
    pending_verification_identity: tuple | None = None


_LOCK = threading.RLock()
_INDEXES = OrderedDict()
MAX_INDEXES = 32
MAX_ROW_BYTES = 32 * 1024 * 1024
MAX_PENDING_BYTES = 64 * 1024 * 1024


def _reserve_pending(value, raw):
    # Caller holds _LOCK. Partial assembly has a process-wide bound, in
    # addition to the writer/reader's common per-row limit.
    total = sum(len(index.pending) for index in _INDEXES.values() if index is not value)
    if total + len(raw) > MAX_PENDING_BYTES:
        raise IndexNotReady('ai_trace_dedup_pending_memory_budget')
    value.pending = raw


def semantic_digest(row, key_field):
    fields = {
        # Content-addressed blobs are shared across attempts. Request IDs,
        # capture clocks and first-writer attribution are not blob identity.
        'request_envelope_sha256': ('payload_sha256', 'prompt_sha256', 'sanitized_user_input',
                                   'sanitized_user_input_sha256', 'redacted', 'replay_exact'),
        'prompt_sha256': ('sanitized_prompt', 'redacted', 'replay_exact'),
        'candidate_sha256': ('endpoint', 'symbol', 'source_context', 'model_context', 'call_inputs'),
        'request_id': ('request_envelope_sha256', 'prompt_sha256', 'payload_sha256'),
        'decision_trace_id': ('decision_result_sha256', 'request_envelope_sha256', 'ai_input_payload_sha256'),
        'label_id': ('decision_trace_id', 'reference_price', 'source_date'),
    }.get(key_field)
    data = {key: row.get(key) for key in fields} if fields else row
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=True, default=str).encode()).hexdigest()


def _key(path, field):
    return str(path.absolute()), field


def _state(path, field, st):
    key = _key(path, field)
    inode = (st.st_dev, st.st_ino) if st else None
    with _LOCK:
        value = _INDEXES.get(key)
        if (value is None or value.inode != inode or (st and (
                st.st_size < value.offset + len(value.pending) or (st.st_size == value.offset
                and value.mtime_ns != st.st_mtime_ns)))):
            if value is not None:
                # External caches hold these set objects, not independent proof.
                value.keys.clear()
                value.digests.clear()
                value.ready = False
            value = Index(inode)
            _INDEXES[key] = value
        _INDEXES.move_to_end(key)
        while len(_INDEXES) > MAX_INDEXES:
            _INDEXES.popitem(last=False)
        return value


def prepare(path, field, generation, *, max_bytes=4 * 1024 * 1024, hot=False):
    st = generation.stat_name(generation.logical.name)
    value = _state(path, field, st)
    if st is None or st.st_size == 0:
        with _LOCK:
            value.ready = True
        return value
    with _LOCK:
        offset, tail, ready = value.offset, value.tail, value.ready
        pending = value.pending
        identity_now = (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns)
        if offset == st.st_size and ready:
            return value
        if hot and (not ready or st.st_size - offset > max_bytes):
            raise IndexNotReady('ai_trace_dedup_preparation_pending')
        if value.pending_reason and value.observed_identity == identity_now:
            raise IndexNotReady(value.pending_reason)
    fd = generation.open_name(generation.logical.name, os.O_RDONLY)
    try:
        generation.assert_open_descriptor_name_identity(fd, generation.logical.name)
        if tail and os.pread(fd, len(tail), max(0, offset-len(tail))) != tail:
            with _LOCK:
                value.keys.clear()
                value.digests.clear()
                value.ready = False
                _INDEXES.pop(_key(path, field), None)
            raise IndexNotReady('ai_trace_dedup_prefix_changed')
        if pending and value.observed_identity != identity_now:
            # An append/rewrite between maintenance leases must verify ALL
            # assembled bytes, in bounded steps, before reusing that prefix.
            with _LOCK:
                if value.pending_verification_identity != identity_now:
                    value.pending_verified_bytes = 0
                    value.pending_verification_identity = identity_now
                verified = value.pending_verified_bytes
            size = min(max_bytes, len(pending)-verified)
            if os.pread(fd, size, offset+verified) != pending[verified:verified+size]:
                with _LOCK:
                    value.keys.clear()
                    value.digests.clear()
                    value.ready = False
                    _INDEXES.pop(_key(path, field), None)
                raise IndexNotReady('ai_trace_dedup_prefix_changed')
            if generation.assert_open_descriptor_name_identity(fd, generation.logical.name) != identity_now:
                raise IndexNotReady('ai_trace_dedup_generation_changed')
            with _LOCK:
                if (_INDEXES.get(_key(path, field)) is not value or value.offset != offset
                        or value.pending != pending
                        or value.pending_verification_identity != identity_now):
                    raise IndexNotReady('ai_trace_dedup_checkpoint_changed')
                value.pending_verified_bytes = verified+size
            max_bytes -= size
            if verified+size < len(pending) or max_bytes == 0:
                raise IndexNotReady('ai_trace_dedup_preparation_pending')
        raw = pending + os.pread(fd, min(max_bytes, MAX_ROW_BYTES+1-len(pending)), offset + len(pending))
        end = raw.rfind(b'\n') + 1
        if not end:
            reason = ('ai_trace_dedup_row_size_exceeded' if len(raw) > MAX_ROW_BYTES
                      else 'ai_trace_dedup_partial_row' if offset+len(raw) == st.st_size
                      else 'ai_trace_dedup_preparation_pending')
            if generation.assert_open_descriptor_name_identity(fd, generation.logical.name) != identity_now:
                raise IndexNotReady('ai_trace_dedup_generation_changed')
            with _LOCK:
                if (_INDEXES.get(_key(path, field)) is not value or value.offset != offset
                        or value.pending != pending):
                    raise IndexNotReady('ai_trace_dedup_checkpoint_changed')
                _reserve_pending(value, raw if len(raw) <= MAX_ROW_BYTES else b'')
                value.pending_verified_bytes = 0
                value.pending_verification_identity = None
                value.observed_identity = identity_now
                value.pending_reason = reason if offset+len(raw) == st.st_size or len(raw)>MAX_ROW_BYTES else ''
                value.ready = False
            raise IndexNotReady(reason)
        keys = set()
        digests = {}
        for line in raw[:end].splitlines():
            if not line.strip():
                continue
            if len(line)+1 > MAX_ROW_BYTES:
                raise IndexNotReady('ai_trace_dedup_row_size_exceeded')
            try:
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise ValueError('not an object')
            except (ValueError, TypeError) as exc:
                raise IndexNotReady('ai_trace_dedup_invalid_row') from exc
            if row.get(field):
                key = str(row[field])
                digest = semantic_digest(row, field)
                previous = digests.get(key, value.digests.get(key))
                if previous is not None and previous != digest:
                    raise IndexNotReady('ai_trace_dedup_identity_conflict')
                keys.add(key)
                digests[key] = digest
        identity = generation.assert_open_descriptor_name_identity(fd, generation.logical.name)
        if identity[:2] != value.inode or identity[2:] != (st.st_size, st.st_mtime_ns):
            raise IndexNotReady('ai_trace_dedup_generation_changed')
        new_offset = offset + end
        new_tail = os.pread(fd, min(new_offset, 1024), max(0, new_offset-1024))
        with _LOCK:
            if (_INDEXES.get(_key(path, field)) is not value or value.offset != offset
                    or value.pending != pending):
                raise IndexNotReady('ai_trace_dedup_checkpoint_changed')
            _reserve_pending(value, raw[end:])
            value.keys.update(keys)
            value.digests.update(digests)
            value.offset = new_offset
            value.pending_verified_bytes = 0
            value.pending_verification_identity = None
            value.pending_reason = ''
            value.observed_identity = identity_now
            value.tail = new_tail
            value.mtime_ns = st.st_mtime_ns
            value.ready = new_offset == st.st_size
        if hot and not value.ready:
            raise IndexNotReady('ai_trace_dedup_partial_or_oversized_row')
        return value
    finally:
        os.close(fd)


def appended(path, field, row, descriptor, *, previous_identity, encoded):
    """Advance the verified prefix for every row in a mixed append-only stream.

    An empty predecessor or an index covering the exact predecessor is required.
    Keyless observations move the file cursor without inventing request keys.
    The already-written bytes supply the tail; this adds no file read or ledger.
    """
    st = os.fstat(descriptor)
    key = _key(path, field)
    with _LOCK:
        value = _INDEXES.get(key)
        if ((st.st_dev, st.st_ino) != previous_identity[:2]
                or st.st_size != previous_identity[2] + len(encoded)):
            _INDEXES.pop(key, None)
            raise OSError('ai_trace_dedup_append_generation_changed')
        if previous_identity[2] == 0:
            value = Index((st.st_dev, st.st_ino))
            _INDEXES[key] = value
        elif (value is None or not value.ready
              or value.inode != previous_identity[:2]
              or value.offset != previous_identity[2]
              or value.mtime_ns != previous_identity[3]):
            # Never skip an unseen suffix or mark a replacement file prepared.
            _INDEXES.pop(key, None)
            return
        _INDEXES.move_to_end(key)
        while len(_INDEXES) > MAX_INDEXES:
            _INDEXES.popitem(last=False)
        value.inode = (st.st_dev, st.st_ino)
        value.offset = st.st_size
        value.mtime_ns = st.st_mtime_ns
        if row.get(field):
            value.keys.add(str(row[field]))
            value.digests[str(row[field])] = semantic_digest(row, field)
        value.ready = True
        value.pending = b''
        value.pending_reason = ''
        value.pending_verified_bytes = 0
        value.pending_verification_identity = None
        value.tail = encoded[-1024:] if len(encoded) >= 1024 else (value.tail + encoded)[-1024:]

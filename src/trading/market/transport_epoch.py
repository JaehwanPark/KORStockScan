"""Durable local stream generations shared by Main releases on this data root.

Allocated once per connection, never per tick. The value is local provenance,
not a Kiwoom wire field or a clock used for freshness. Historical envelopes keep
their original epoch, so replay cannot acquire a new opportunity identity.
"""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time

from src.utils.constants import DATA_DIR

DEFAULT_PATH = DATA_DIR / 'runtime/kiwoom_ws_transport_epoch.json'
SCHEMA = 'kiwoom_ws_transport_epoch_v1'
MIN_EPOCH = 10**12  # Separate new allocations from legacy connection counters.
MAX_EPOCH = 2**53 - 1  # Exact in existing float/JSON consumers as well as int.


def _digest(body):
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def allocate_transport_epoch(*, previous=0, path=None):
    """Reserve and fsync before publishing; corruption/I/O failure stops bootstrap."""
    if type(previous) is not int or not 0 <= previous <= MAX_EPOCH:
        raise ValueError('transport_epoch_previous_invalid')
    path = Path(path) if path is not None else DEFAULT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_suffix('.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        lock.seek(0)
        marker = lock.read(128)
        if marker not in ('', SCHEMA + '\n'):
            raise ValueError('transport_epoch_marker_invalid')
        if not path.exists() and (marker or previous >= MIN_EPOCH):
            raise ValueError('transport_epoch_state_missing')
        last = 0
        if path.exists():
            if path.stat().st_size > 4096:
                raise ValueError('transport_epoch_state_invalid')
            row = json.loads(path.read_text())
            if (not isinstance(row, dict) or row.get('schema') != SCHEMA
                    or type(row.get('epoch')) is not int or not MIN_EPOCH <= row['epoch'] <= MAX_EPOCH
                    or row.get('sha256') != _digest({k: v for k, v in row.items() if k != 'sha256'})):
                raise ValueError('transport_epoch_state_invalid')
            last = row['epoch']
        epoch = max(MIN_EPOCH, time.time_ns() // 1000, previous + 1, last + 1)
        if epoch > MAX_EPOCH:
            raise ValueError('transport_epoch_exhausted')
        body = dict(schema=SCHEMA, epoch=epoch)
        value = dict(body, sha256=_digest(body))
        fd, temporary = tempfile.mkstemp(dir=path.parent, prefix='.transport-epoch-')
        try:
            with os.fdopen(fd, 'w') as handle:
                json.dump(value, handle, sort_keys=True, separators=(',', ':'))
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
            directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
            # A previously published store disappearing is not a first install.
            # Publish this marker before returning any allocated generation.
            if not marker:
                lock.write(SCHEMA + '\n')
                lock.flush()
                os.fsync(lock.fileno())
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return epoch

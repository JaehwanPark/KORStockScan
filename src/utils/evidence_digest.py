"""Canonical digest and bounded evidence reader shared by Main reports."""
import hashlib
import json
import os
import stat
from pathlib import Path

def digest(value):
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode()
    ).hexdigest()

def read_object(path, limit=4 * 1024 * 1024):
    """Read a stable bounded regular file without following its final symlink."""
    path = Path(path)
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
        raise ValueError("research_source_not_bounded_regular_file")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as handle:
        opened = os.fstat(handle.fileno())
        raw = handle.read(limit + 1)
        after = os.fstat(handle.fileno())

    def generation(s):
        return s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns

    if (
        len(raw) > limit
        or generation(before) != generation(opened)
        or generation(opened) != generation(after)
        or generation(after) != generation(path.lstat())
    ):
        raise ValueError("research_source_changed_during_read")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("research_source_not_object")
    return value

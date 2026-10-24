"""Strict bounded observer artifact IO shared by monitor and detector.

Callers own size limits, compression selection, seals and publication locks.
This owner only authenticates regular-file identity and JSON syntax.
"""
from contextlib import contextmanager
import json
import math
import os
from pathlib import Path
import stat


def file_signature(info):
    return tuple(getattr(info, "st_" + field) for field in (
        "dev", "ino", "mode", "nlink", "uid", "gid", "size", "mtime_ns", "ctime_ns"))


@contextmanager
def regular_fd(path, *, max_bytes=None):
    """Never block opening special files or follow a replacement symlink."""
    path = Path(path)
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode): raise ValueError("observer_regular_file_required")
    if max_bytes is not None and before.st_size > max_bytes:
        raise ValueError("observer_file_size_limit")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        opened = os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode): raise ValueError("observer_regular_file_required")
        if file_signature(opened) != file_signature(before):
            raise ValueError("observer_file_changed_before_read")
        yield fd
        if (file_signature(os.fstat(fd)) != file_signature(opened)
                or file_signature(path.lstat()) != file_signature(opened)):
            raise ValueError("observer_file_changed_during_read")
    finally:
        os.close(fd)


def regular_bytes(path, *, limit):
    with regular_fd(path, max_bytes=limit) as fd:
        chunks, total = [], 0
        while True:
            chunk = os.read(fd, min(128 * 1024, limit + 1 - total))
            if not chunk: break
            chunks.append(chunk); total += len(chunk)
            if total > limit: raise ValueError("observer_file_size_limit")
        return b"".join(chunks)


def json_object(encoded):
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result: raise ValueError("observer_json_duplicate_key")
            result[key] = value
        return result
    def number(value):
        result = float(value)
        if not math.isfinite(result): raise ValueError("observer_json_nonfinite")
        return result
    def invalid_constant(value):
        raise ValueError("observer_json_nonfinite")
    value = json.loads(encoded, object_pairs_hook=pairs, parse_float=number, parse_constant=invalid_constant)
    if not isinstance(value, dict): raise ValueError("observer_json_object_required")
    return value


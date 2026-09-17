"""Lossless block archives for sealed research facts, with indexed point reads.

Owned research facts only. Required evidence is migrated after durable byte
verification; optional cache eviction never owns these archives.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import struct
import stat
import tempfile
import zlib

MAGIC = b"KSSF1\n"
HEADER = struct.Struct(">II")
MAX_BLOCK = 8 * 1024 * 1024
MAX_RAW = 64 * 1024 * 1024


def fact_path(directory, symbol, day):
    raw = Path(directory) / "facts" / f"prospective_facts_{symbol}_{day:%Y%m%d}.jsonl"
    archived = raw.with_suffix(raw.suffix + ".zfb")
    return raw if raw.exists() else archived if archived.exists() else raw


class FactReader:
    def __init__(self, handle):
        self.handle = handle
        if handle.read(len(MAGIC)) != MAGIC:
            raise ValueError("research_archive_header_invalid")
        self.rows, self.position = [], 0
        self.block_offset = handle.tell()
        self.audit = hashlib.sha256()
        self.raw_bytes = self.row_count = 0
        self.sequential = True
        self.finished = False

    def __iter__(self):
        while row := self.readline(MAX_BLOCK + 1):
            yield row

    def fileno(self):
        return self.handle.fileno()

    def _block(self):
        self.block_offset = self.handle.tell()
        header = self.handle.read(HEADER.size)
        if len(header) != HEADER.size:
            raise ValueError("research_archive_interrupted_block")
        size, raw_size = HEADER.unpack(header)
        if size == raw_size == 0:
            footer = self.handle.read(80)
            if len(footer) != 80 or self.handle.read(1):
                raise ValueError("research_archive_footer_invalid")
            sha, count, raw_bytes = (
                footer[:64].decode(),
                *struct.unpack(">QQ", footer[64:]),
            )
            if self.sequential and (
                sha != self.audit.hexdigest()
                or count != self.row_count
                or raw_bytes != self.raw_bytes
            ):
                raise ValueError("research_archive_original_checksum_mismatch")
            self.finished = True
            return False
        if not 0 < size <= MAX_BLOCK or not 0 < raw_size <= MAX_BLOCK:
            raise ValueError("research_archive_block_budget_exceeded")
        raw = self.handle.read(size)
        if len(raw) != size:
            raise ValueError("research_archive_interrupted_block")
        decoder = zlib.decompressobj()
        decoded = decoder.decompress(raw, MAX_BLOCK + 1)
        if (
            not decoder.eof
            or decoder.unused_data
            or decoder.unconsumed_tail
            or len(decoded) != raw_size
        ):
            raise ValueError("research_archive_block_corrupt")
        self.rows = decoded.splitlines(keepends=True)
        if not 1 <= len(self.rows) <= 256 or any(
            not line.endswith(b"\n") for line in self.rows
        ):
            raise ValueError("research_archive_record_boundary_invalid")
        self.position = 0
        return True

    def tell(self):
        if self.position == len(self.rows):
            return self.handle.tell() << 8
        return (self.block_offset << 8) | self.position

    def seek(self, encoded):
        offset, ordinal = encoded >> 8, encoded & 255
        self.sequential = False
        self.finished = False
        if offset != self.block_offset or not self.rows:
            self.handle.seek(offset)
            if not self._block():
                raise ValueError("research_archive_index_points_to_footer")
        if ordinal >= len(self.rows):
            raise ValueError("research_archive_index_ordinal_invalid")
        self.position = ordinal

    def readline(self, limit=-1):
        if self.finished:
            return b""
        if self.position == len(self.rows) and not self._block():
            return b""
        row = self.rows[self.position]
        self.position += 1
        if limit >= 0 and len(row) > limit:
            raise ValueError("research_archive_row_budget_exceeded")
        if self.sequential:
            self.audit.update(row)
            self.raw_bytes += len(row)
            self.row_count += 1
            if self.raw_bytes > MAX_RAW:
                raise ValueError("research_archive_raw_budget_exceeded")
        return row


def seal_fact_file(path, *, offsets=None, expected_sha256=None):
    """CAS-migrate a bounded sealed native file after lossless verification."""
    from src.engine.monitoring.research_source_facts import generation

    path = Path(path)
    before = path.lstat()
    if (
        not stat.S_ISREG(before.st_mode)
        or path.is_symlink()
        or before.st_size > MAX_RAW
    ):
        raise ValueError("research_archive_source_not_bounded_regular")
    target = path.with_suffix(path.suffix + ".zfb")
    fd, temporary = tempfile.mkstemp(prefix=".research-fact-archive-", dir=path.parent)
    try:
        source_fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(source_fd, "rb") as source, os.fdopen(fd, "wb") as output:
            if generation(os.fstat(source.fileno())) != generation(before):
                raise ValueError("research_archive_source_changed")
            output.write(MAGIC)
            sha = hashlib.sha256()
            count = total = 0
            while True:
                rows = []
                block_position = output.tell()
                for _ in range(256):
                    line = source.readline(MAX_BLOCK + 1)
                    if not line:
                        break
                    if not line.endswith(b"\n") or len(line) > MAX_BLOCK:
                        raise ValueError("research_archive_original_record_incomplete")
                    if offsets is not None:
                        offsets.append((block_position << 8) | len(rows))
                    rows.append(line)
                    sha.update(line)
                    count += 1
                    total += len(line)
                    if total > MAX_RAW:
                        raise ValueError("research_archive_source_growing")
                if not rows:
                    break
                raw = b"".join(rows)
                compressed = zlib.compress(raw, 6)
                if max(len(raw), len(compressed)) > MAX_BLOCK:
                    raise ValueError("research_archive_block_budget_exceeded")
                output.write(HEADER.pack(len(compressed), len(raw)))
                output.write(compressed)
            if expected_sha256 is not None and sha.hexdigest() != expected_sha256:
                raise ValueError("research_archive_original_generation_mismatch")
            output.write(
                HEADER.pack(0, 0)
                + sha.hexdigest().encode()
                + struct.pack(">QQ", count, total)
            )
            output.flush()
            os.fsync(output.fileno())
        # A full sequential verification proves byte-for-byte reconstruction,
        # before changing the required source path or removing its raw form.
        with open(temporary, "rb") as check:
            reader = FactReader(check)
            while reader.readline(MAX_BLOCK + 1):
                pass
        if generation(path.lstat()) != generation(before):
            raise ValueError("research_archive_source_changed")
        if target.is_symlink():
            raise ValueError("research_archive_destination_symlink")
        os.replace(temporary, target)
        parent_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(parent_fd)
            if generation(path.lstat()) != generation(before):
                raise ValueError("research_archive_source_changed")
            path.unlink()
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)
        return target
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

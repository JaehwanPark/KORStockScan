from __future__ import annotations

import gzip
import hashlib
import json
import os
import secrets
import stat
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO

import fcntl

JSON_GENERATION_LOCK_SUFFIX = ".generation.lock"
JSONL_GENERATION_LOCK_SUFFIX = ".generation.lock"


def _directory_identity(metadata: os.stat_result) -> tuple[int, int]:
    return metadata.st_dev, metadata.st_ino


def _directory_open_flags() -> int:
    return (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )


def _open_directory_tree_nofollow(path: Path, *, create: bool) -> int:
    """Return a pinned directory fd without following any path component."""

    absolute = Path(os.path.abspath(os.fspath(path)))
    descriptor = os.open(os.sep, _directory_open_flags())
    try:
        for component in absolute.parts[1:]:
            try:
                child = os.open(
                    component,
                    _directory_open_flags(),
                    dir_fd=descriptor,
                )
            except FileNotFoundError:
                if not create:
                    raise
                try:
                    os.mkdir(component, 0o750, dir_fd=descriptor)
                    os.fsync(descriptor)
                except FileExistsError:
                    pass
                child = os.open(
                    component,
                    _directory_open_flags(),
                    dir_fd=descriptor,
                )
            os.close(descriptor)
            descriptor = child
        metadata = os.fstat(descriptor)
        if not stat.S_ISDIR(metadata.st_mode):
            raise OSError(f"json_generation_parent_invalid:{absolute}")
        try:
            path_metadata = absolute.lstat()
        except OSError as exc:
            raise OSError(f"json_generation_parent_changed:{absolute}") from exc
        if not stat.S_ISDIR(path_metadata.st_mode) or _directory_identity(
            path_metadata
        ) != _directory_identity(metadata):
            raise OSError(f"json_generation_parent_changed:{absolute}")
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


@contextmanager
def _pinned_read_generation(
    logical: Path,
    *,
    error_prefix: str,
) -> Iterator[ArtifactGenerationLease]:
    try:
        parent_descriptor = _open_directory_tree_nofollow(
            logical.parent,
            create=False,
        )
    except FileNotFoundError:
        raise FileNotFoundError(logical) from None
    parent_metadata = os.fstat(parent_descriptor)
    lease = ArtifactGenerationLease(
        logical=logical,
        parent_descriptor=parent_descriptor,
        parent_identity=_directory_identity(parent_metadata),
        error_prefix=error_prefix,
    )
    try:
        lease.assert_parent_current()
        try:
            yield lease
        except BaseException:
            raise
        else:
            lease.assert_parent_current()
    finally:
        os.close(parent_descriptor)


@dataclass(frozen=True)
class ArtifactGenerationLease:
    """Pinned parent and cooperative lock for one logical JSON generation."""

    logical: Path
    parent_descriptor: int
    parent_identity: tuple[int, int]
    error_prefix: str

    def __fspath__(self) -> str:
        return os.fspath(self.logical)

    def __str__(self) -> str:
        return str(self.logical)

    def __getattr__(self, name: str) -> Any:
        # Preserve the former context-manager value's Path surface for legacy
        # read-only callers. Mutation owners must use the pinned methods below.
        return getattr(self.logical, name)

    def _validated_name(self, name: str) -> str:
        if not name or name in {".", ".."} or Path(name).name != name:
            raise ValueError(f"{self.error_prefix}_entry_name_invalid:{name}")
        return name

    def assert_parent_current(self) -> None:
        pinned = os.fstat(self.parent_descriptor)
        if (
            not stat.S_ISDIR(pinned.st_mode)
            or _directory_identity(pinned) != self.parent_identity
        ):
            raise OSError(f"{self.error_prefix}_parent_descriptor_changed")
        try:
            current = self.logical.parent.lstat()
        except OSError as exc:
            raise OSError(
                f"{self.error_prefix}_parent_changed:{self.logical.parent}"
            ) from exc
        if (
            not stat.S_ISDIR(current.st_mode)
            or _directory_identity(current) != self.parent_identity
        ):
            raise OSError(f"{self.error_prefix}_parent_changed:{self.logical.parent}")

    def stat_name(self, name: str) -> os.stat_result | None:
        self.assert_parent_current()
        try:
            metadata = os.stat(
                self._validated_name(name),
                dir_fd=self.parent_descriptor,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            return None
        self.assert_parent_current()
        return metadata

    def assert_name_identity(
        self,
        name: str,
        expected: tuple[int, int, int, int],
    ) -> None:
        metadata = self.stat_name(name)
        if (
            metadata is None
            or not stat.S_ISREG(metadata.st_mode)
            or _file_identity(metadata) != expected
        ):
            raise OSError(f"{self.error_prefix}_entry_changed:{name}")

    def open_name(self, name: str, flags: int, mode: int = 0o640) -> int:
        self.assert_parent_current()
        descriptor = os.open(
            self._validated_name(name),
            flags | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
            mode,
            dir_fd=self.parent_descriptor,
        )
        try:
            self.assert_parent_current()
        except Exception:
            os.close(descriptor)
            raise
        return descriptor

    def assert_open_descriptor_name_identity(
        self,
        descriptor: int,
        name: str,
    ) -> tuple[int, int, int, int]:
        self.assert_parent_current()
        opened = os.fstat(descriptor)
        expected = _file_identity(opened)
        if not stat.S_ISREG(opened.st_mode):
            raise OSError(f"{self.error_prefix}_entry_not_regular:{name}")
        self.assert_name_identity(name, expected)
        if _file_identity(os.fstat(descriptor)) != expected:
            raise OSError(f"{self.error_prefix}_entry_changed:{name}")
        self.assert_parent_current()
        return expected

    def create_temporary(
        self,
        *,
        prefix: str,
        suffix: str,
        mode: int = 0o640,
    ) -> tuple[str, int]:
        self.assert_parent_current()
        for _ in range(128):
            name = f"{prefix}{secrets.token_hex(8)}{suffix}"
            try:
                descriptor = self.open_name(
                    name,
                    os.O_RDWR | os.O_CREAT | os.O_EXCL,
                    mode,
                )
            except FileExistsError:
                continue
            return name, descriptor
        raise FileExistsError(f"{self.error_prefix}_temporary_name_exhausted")

    def replace_name(self, source_name: str, target_name: str) -> None:
        source_metadata = self.stat_name(source_name)
        if source_metadata is None or not stat.S_ISREG(source_metadata.st_mode):
            raise OSError(f"{self.error_prefix}_replace_source_invalid:{source_name}")
        source_identity = _file_identity(source_metadata)
        os.replace(
            self._validated_name(source_name),
            self._validated_name(target_name),
            src_dir_fd=self.parent_descriptor,
            dst_dir_fd=self.parent_descriptor,
        )
        self.assert_name_identity(target_name, source_identity)
        self.fsync_parent()
        self.assert_name_identity(target_name, source_identity)

    def unlink_name(
        self,
        name: str,
        *,
        missing_ok: bool = False,
        require_current: bool = True,
    ) -> None:
        if require_current:
            self.assert_parent_current()
        try:
            os.unlink(self._validated_name(name), dir_fd=self.parent_descriptor)
        except FileNotFoundError:
            if not missing_ok:
                raise
        if require_current:
            self.fsync_parent()
        else:
            os.fsync(self.parent_descriptor)

    def fsync_parent(self) -> None:
        self.assert_parent_current()
        os.fsync(self.parent_descriptor)
        self.assert_parent_current()

    def chmod_parent(self, mode: int) -> None:
        self.assert_parent_current()
        os.fchmod(self.parent_descriptor, mode)
        self.assert_parent_current()

    def bound_path(self, name: str | None = None) -> Path:
        """Return a procfs path anchored to this still-open parent descriptor."""

        self.assert_parent_current()
        parent = Path("/proc/self/fd") / str(self.parent_descriptor)
        try:
            observed = parent.stat()
        except OSError as exc:
            raise OSError(f"{self.error_prefix}_bound_parent_unavailable") from exc
        if (
            not stat.S_ISDIR(observed.st_mode)
            or _directory_identity(observed) != self.parent_identity
        ):
            raise OSError(f"{self.error_prefix}_bound_parent_changed")
        return parent / self._validated_name(name) if name is not None else parent


@dataclass(frozen=True)
class JsonObjectReadReceipt:
    """One JSON object's payload and bytes from one pinned generation."""

    logical_path: Path
    physical_path: Path
    payload: dict[str, Any]
    raw_sha256: str
    decoded_sha256: str
    physical_identity: tuple[int, int, int, int]
    generation_census: tuple[tuple[str, tuple[int, int, int, int]], ...]
    parent_identity: tuple[int, int]


def _logical_json_path(path: Path) -> Path:
    candidate = Path(path).absolute()
    if candidate.suffix == ".gz":
        candidate = candidate.with_name(candidate.name[: -len(".gz")])
    if candidate.suffix != ".json":
        raise ValueError(f"json_generation_logical_path_invalid:{candidate}")
    return candidate


def json_generation_lock_path(path: Path) -> Path:
    """Return the cooperative lock shared by one JSON writer and compactor."""

    logical = _logical_json_path(path)
    return logical.with_name(f".{logical.name}{JSON_GENERATION_LOCK_SUFFIX}")


def _logical_jsonl_path(path: Path) -> Path:
    candidate = Path(path).absolute()
    if candidate.suffix == ".gz":
        candidate = candidate.with_name(candidate.name[: -len(".gz")])
    if candidate.suffix != ".jsonl":
        raise ValueError(f"jsonl_generation_logical_path_invalid:{candidate}")
    return candidate


def jsonl_generation_lock_path(path: Path) -> Path:
    """Return the cooperative lock shared by one JSONL writer and compactor."""

    logical = _logical_jsonl_path(path)
    return logical.with_name(f".{logical.name}{JSONL_GENERATION_LOCK_SUFFIX}")


@contextmanager
def _artifact_generation_lock(
    logical: Path,
    *,
    error_prefix: str,
    lock_suffix: str,
    exclusive: bool = True,
    blocking: bool = True,
) -> Iterator[ArtifactGenerationLease]:
    parent_descriptor = _open_directory_tree_nofollow(logical.parent, create=True)
    parent_metadata = os.fstat(parent_descriptor)
    parent_identity = _directory_identity(parent_metadata)
    lease = ArtifactGenerationLease(
        logical=logical,
        parent_descriptor=parent_descriptor,
        parent_identity=parent_identity,
        error_prefix=error_prefix,
    )
    lock_name = f".{logical.name}{lock_suffix}"
    descriptor = -1
    try:
        lease.assert_parent_current()
        descriptor = lease.open_name(lock_name, os.O_RDWR | os.O_CREAT, 0o640)
        lock_metadata = os.fstat(descriptor)
        if not stat.S_ISREG(lock_metadata.st_mode):
            raise OSError(
                f"{error_prefix}_lock_not_regular:{logical.parent / lock_name}"
            )
        lease.assert_name_identity(lock_name, _file_identity(lock_metadata))
        operation = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
        if not blocking:
            operation |= fcntl.LOCK_NB
        try:
            fcntl.flock(descriptor, operation)
        except BlockingIOError as exc:
            raise OSError(f"{error_prefix}_lock_busy:{logical}") from exc
        lease.assert_parent_current()
        lease.assert_name_identity(lock_name, _file_identity(lock_metadata))
        try:
            yield lease
        except BaseException:
            raise
        else:
            lease.assert_parent_current()
            lease.assert_name_identity(lock_name, _file_identity(lock_metadata))
    finally:
        if descriptor >= 0:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
            finally:
                os.close(descriptor)
        os.close(parent_descriptor)


@contextmanager
def jsonl_artifact_generation_lock(
    path: Path,
    *,
    exclusive: bool = True,
    blocking: bool = True,
) -> Iterator[ArtifactGenerationLease]:
    """Lock one logical JSONL generation under one pinned real parent fd."""

    logical = _logical_jsonl_path(path)
    with _artifact_generation_lock(
        logical,
        error_prefix="jsonl_generation",
        lock_suffix=JSONL_GENERATION_LOCK_SUFFIX,
        exclusive=exclusive,
        blocking=blocking,
    ) as lease:
        yield lease


@contextmanager
def json_artifact_generation_lock(
    path: Path,
    *,
    exclusive: bool = True,
    blocking: bool = True,
) -> Iterator[ArtifactGenerationLease]:
    """Lock one logical JSON generation under one pinned real parent fd."""

    logical = _logical_json_path(path)
    with _artifact_generation_lock(
        logical,
        error_prefix="json_generation",
        lock_suffix=JSON_GENERATION_LOCK_SUFFIX,
        exclusive=exclusive,
        blocking=blocking,
    ) as lease:
        yield lease


def _strict_json_object_pairs(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    for key, value in pairs:
        if key in parsed:
            raise ValueError(f"duplicate JSON key:{key}")
        parsed[key] = value
    return parsed


def _reject_non_finite_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number:{value}")


def _write_json_to_temporary(
    generation: ArtifactGenerationLease,
    value: Mapping[str, Any],
    *,
    ensure_ascii: bool,
    indent: int | None,
    sort_keys: bool,
    allow_nan: bool,
    trailing_newline: bool,
) -> str:
    temporary_name, descriptor = generation.create_temporary(
        prefix=f".{generation.logical.name}.",
        suffix=".tmp",
        mode=0o640,
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(
                dict(value),
                handle,
                ensure_ascii=ensure_ascii,
                indent=indent,
                sort_keys=sort_keys,
                allow_nan=allow_nan,
            )
            if trailing_newline:
                handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        generation.assert_parent_current()
        return temporary_name
    except Exception:
        generation.unlink_name(
            temporary_name,
            missing_ok=True,
            require_current=False,
        )
        raise


def _json_object_from_bytes(payload: bytes, *, source: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=_strict_json_object_pairs,
            parse_constant=_reject_non_finite_json_constant,
        )
    except (UnicodeDecodeError, ValueError) as exc:
        # Keep the stable wrapper while retaining the strict parser's causal
        # reason (for example duplicate keys or non-finite numbers).  Callers
        # use that reason to distinguish contract corruption without ever
        # treating malformed input as an absent generation.
        raise ValueError(f"json_generation_payload_invalid:{source}:{exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"json_generation_payload_not_object:{source}")
    return value


def _file_identity(metadata: os.stat_result) -> tuple[int, int, int, int]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_size,
        metadata.st_mtime_ns,
    )


def _read_generation_name_bytes(
    generation: ArtifactGenerationLease,
    name: str,
) -> tuple[bytes, tuple[int, int, int, int]]:
    descriptor = generation.open_name(name, os.O_RDONLY)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise OSError(f"json_generation_file_invalid:{name}")
        chunks: list[bytes] = []
        while chunk := os.read(descriptor, 1024 * 1024):
            chunks.append(chunk)
        after = os.fstat(descriptor)
        expected = _file_identity(before)
        if _file_identity(after) != expected:
            raise OSError(f"json_generation_entry_changed:{name}")
    finally:
        os.close(descriptor)
    generation.assert_name_identity(name, expected)
    return b"".join(chunks), expected


def _json_object_from_generation_name(
    generation: ArtifactGenerationLease,
    name: str,
) -> dict[str, Any]:
    payload, _ = _read_generation_name_bytes(generation, name)
    return _json_object_from_bytes(payload, source=generation.logical.parent / name)


def _open_or_create_child_directory_at(
    parent_descriptor: int,
    name: str,
    *,
    context: Path,
) -> int:
    if not name or name in {".", ".."} or Path(name).name != name:
        raise OSError(f"json_generation_archive_directory_invalid:{context}")
    created = False
    try:
        try:
            os.mkdir(name, 0o750, dir_fd=parent_descriptor)
            created = True
        except FileExistsError:
            pass
        descriptor = os.open(name, _directory_open_flags(), dir_fd=parent_descriptor)
    except OSError as exc:
        raise OSError(f"json_generation_archive_directory_invalid:{context}") from exc
    try:
        pinned = os.fstat(descriptor)
        entry = os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
        if (
            not stat.S_ISDIR(pinned.st_mode)
            or not stat.S_ISDIR(entry.st_mode)
            or _directory_identity(pinned) != _directory_identity(entry)
        ):
            raise OSError(f"json_generation_archive_directory_invalid:{context}")
        if created:
            os.fsync(parent_descriptor)
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


def _stable_file_sha256_at(
    directory_descriptor: int,
    name: str,
    *,
    context: Path,
) -> tuple[tuple[int, int, int, int], str]:
    descriptor = os.open(
        name,
        os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
        dir_fd=directory_descriptor,
    )
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise OSError(f"json_generation_archive_conflict:{context}")
        digest = hashlib.sha256()
        while chunk := os.read(descriptor, 1024 * 1024):
            digest.update(chunk)
        after = os.fstat(descriptor)
        expected = _file_identity(before)
        if _file_identity(after) != expected:
            raise OSError(f"json_generation_archive_conflict:{context}")
    finally:
        os.close(descriptor)
    entry = os.stat(name, dir_fd=directory_descriptor, follow_symlinks=False)
    if not stat.S_ISREG(entry.st_mode) or _file_identity(entry) != expected:
        raise OSError(f"json_generation_archive_conflict:{context}")
    return expected, digest.hexdigest()


def _restore_gzip_to_temporary(
    generation: ArtifactGenerationLease,
    compressed_name: str,
) -> tuple[str, tuple[int, int, int, int], str]:
    """Stream one pinned gzip generation into a durable pinned temporary."""

    source_descriptor = generation.open_name(compressed_name, os.O_RDONLY)
    temporary_name = ""
    temporary_descriptor = -1
    try:
        temporary_name, temporary_descriptor = generation.create_temporary(
            prefix=f".{generation.logical.name}.",
            suffix=".restore.tmp",
            mode=0o640,
        )
        before = os.fstat(source_descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise OSError(f"json_generation_gzip_invalid:{compressed_name}")
        digest = hashlib.sha256()
        with (
            os.fdopen(os.dup(source_descriptor), "rb") as source_handle,
            os.fdopen(os.dup(temporary_descriptor), "wb") as temporary_handle,
        ):
            while chunk := source_handle.read(1024 * 1024):
                digest.update(chunk)
            source_handle.seek(0)
            with gzip.GzipFile(fileobj=source_handle, mode="rb") as decoded_handle:
                while chunk := decoded_handle.read(1024 * 1024):
                    temporary_handle.write(chunk)
            temporary_handle.flush()
            os.fsync(temporary_handle.fileno())
        after = os.fstat(source_descriptor)
        expected = _file_identity(before)
        if _file_identity(after) != expected:
            raise OSError(f"json_generation_gzip_changed:{compressed_name}")
        os.fchmod(temporary_descriptor, 0o640)
        generation.assert_name_identity(compressed_name, expected)
        generation.assert_parent_current()
        return temporary_name, expected, digest.hexdigest()
    except Exception:
        if temporary_name:
            generation.unlink_name(
                temporary_name,
                missing_ok=True,
                require_current=False,
            )
        raise
    finally:
        if temporary_descriptor >= 0:
            os.close(temporary_descriptor)
        os.close(source_descriptor)


def _restore_archived_json_generation(
    generation: ArtifactGenerationLease,
    compressed_name: str,
) -> None:
    """Restore/archive gzip using only the lease's pinned parent hierarchy."""

    compressed_path = generation.logical.parent / compressed_name
    compressed_metadata = generation.stat_name(compressed_name)
    if compressed_metadata is None or not stat.S_ISREG(compressed_metadata.st_mode):
        raise OSError(f"json_generation_gzip_invalid:{compressed_path}")
    try:
        restored_name, compressed_identity, stored_hash = _restore_gzip_to_temporary(
            generation, compressed_name
        )
    except (gzip.BadGzipFile, EOFError, OSError) as exc:
        raise ValueError(f"json_generation_gzip_invalid:{compressed_path}") from exc
    try:
        decoded_value = _json_object_from_generation_name(generation, restored_name)
        logical_metadata = generation.stat_name(generation.logical.name)
        if logical_metadata is not None:
            if not stat.S_ISREG(logical_metadata.st_mode):
                raise OSError(f"json_generation_plain_invalid:{generation.logical}")
            if (
                _json_object_from_generation_name(
                    generation,
                    generation.logical.name,
                )
                != decoded_value
            ):
                raise ValueError(
                    f"json_generation_plain_gzip_conflict:{generation.logical}"
                )
        else:
            generation.assert_parent_current()
            try:
                os.link(
                    restored_name,
                    generation.logical.name,
                    src_dir_fd=generation.parent_descriptor,
                    dst_dir_fd=generation.parent_descriptor,
                    follow_symlinks=False,
                )
            except FileExistsError as exc:
                raise OSError(
                    "json_generation_plain_appeared_before_restore:"
                    f"{generation.logical}"
                ) from exc
            generation.fsync_parent()
    finally:
        generation.unlink_name(
            restored_name,
            missing_ok=True,
            require_current=False,
        )

    archive_root_path = generation.logical.parent / "superseded"
    generation.assert_parent_current()
    archive_root_descriptor = _open_or_create_child_directory_at(
        generation.parent_descriptor,
        "superseded",
        context=archive_root_path,
    )
    archive_directory_name = f"{generation.logical.stem}-{stored_hash[:16]}"
    archive_directory_path = archive_root_path / archive_directory_name
    archive_directory_descriptor = -1
    try:
        generation.assert_parent_current()
        archive_directory_descriptor = _open_or_create_child_directory_at(
            archive_root_descriptor,
            archive_directory_name,
            context=archive_directory_path,
        )
        archived_path = archive_directory_path / compressed_name
        try:
            archived_metadata = os.stat(
                compressed_name,
                dir_fd=archive_directory_descriptor,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            archived_metadata = None
        if archived_metadata is not None:
            if (
                not stat.S_ISREG(archived_metadata.st_mode)
                or _stable_file_sha256_at(
                    archive_directory_descriptor,
                    compressed_name,
                    context=archived_path,
                )[1]
                != stored_hash
            ):
                raise OSError(f"json_generation_archive_conflict:{archived_path}")
        else:
            generation.assert_name_identity(compressed_name, compressed_identity)
            try:
                os.link(
                    compressed_name,
                    compressed_name,
                    src_dir_fd=generation.parent_descriptor,
                    dst_dir_fd=archive_directory_descriptor,
                    follow_symlinks=False,
                )
            except FileExistsError as exc:
                raise OSError(
                    f"json_generation_archive_conflict:{archived_path}"
                ) from exc
            archived_identity, archived_hash = _stable_file_sha256_at(
                archive_directory_descriptor,
                compressed_name,
                context=archived_path,
            )
            if archived_identity != compressed_identity or archived_hash != stored_hash:
                raise OSError(f"json_generation_archive_conflict:{archived_path}")
            os.fsync(archive_directory_descriptor)
        generation.assert_name_identity(compressed_name, compressed_identity)
        generation.unlink_name(compressed_name)
    finally:
        if archive_directory_descriptor >= 0:
            os.close(archive_directory_descriptor)
        os.close(archive_root_descriptor)


def _write_json_object_generation_safe_pinned(
    generation: ArtifactGenerationLease,
    value: Mapping[str, Any],
    *,
    ensure_ascii: bool,
    indent: int | None,
    sort_keys: bool,
    allow_nan: bool,
    trailing_newline: bool,
) -> None:
    temporary = _write_json_to_temporary(
        generation,
        value,
        ensure_ascii=ensure_ascii,
        indent=indent,
        sort_keys=sort_keys,
        allow_nan=allow_nan,
        trailing_newline=trailing_newline,
    )
    try:
        compressed_name = f"{generation.logical.name}.gz"
        if generation.stat_name(compressed_name) is not None:
            _restore_archived_json_generation(generation, compressed_name)
        logical_metadata = generation.stat_name(generation.logical.name)
        if logical_metadata is not None and not stat.S_ISREG(logical_metadata.st_mode):
            raise OSError(f"json_generation_plain_invalid:{generation.logical}")
        generation.replace_name(temporary, generation.logical.name)
    finally:
        generation.unlink_name(
            temporary,
            missing_ok=True,
            require_current=False,
        )


def write_json_object_generation_safe(
    path: Path,
    value: Mapping[str, Any],
    *,
    ensure_ascii: bool = False,
    indent: int | None = 2,
    sort_keys: bool = False,
    allow_nan: bool = False,
    trailing_newline: bool = False,
    generation: ArtifactGenerationLease | None = None,
) -> None:
    """Atomically write JSON while preserving a prior gzip-only generation.

    The cooperative generation lock is also used by closed-date storage
    compaction. If a prior active gzip exists, its decoded bytes are first
    published as an equal plain copy, then the exact gzip bytes are retained
    below ``superseded/`` before the new plain generation is installed.
    """

    if not isinstance(value, Mapping):
        raise TypeError("json generation value must be a mapping")
    logical = _logical_json_path(path)
    if generation is not None:
        if generation.logical != logical:
            raise ValueError(f"json_generation_lease_path_mismatch:{logical}")
        _write_json_object_generation_safe_pinned(
            generation,
            value,
            ensure_ascii=ensure_ascii,
            indent=indent,
            sort_keys=sort_keys,
            allow_nan=allow_nan,
            trailing_newline=trailing_newline,
        )
        return
    with json_artifact_generation_lock(
        logical,
        exclusive=True,
        blocking=True,
    ) as write_generation:
        _write_json_object_generation_safe_pinned(
            write_generation,
            value,
            ensure_ascii=ensure_ascii,
            indent=indent,
            sort_keys=sort_keys,
            allow_nan=allow_nan,
            trailing_newline=trailing_newline,
        )


def existing_or_gzip_path(path: Path) -> Path:
    """Return path if present, otherwise the sibling .gz path when present."""
    # ``Path.exists`` follows symlinks, so a broken link would otherwise look
    # indistinguishable from an absent generation.  Return any directory entry
    # here and let the strict reader reject non-regular files via ``lstat``.
    if path.exists() or path.is_symlink():
        return path
    gz_path = path.with_name(path.name + ".gz")
    return gz_path if gz_path.exists() or gz_path.is_symlink() else path


def _read_json_object_strict_pinned(
    logical: Path,
    generation: ArtifactGenerationLease,
) -> dict[str, Any]:
    candidate_names = (logical.name, f"{logical.name}.gz")

    def census() -> dict[str, tuple[int, int, int, int]]:
        observed: dict[str, tuple[int, int, int, int]] = {}
        for name in candidate_names:
            metadata = generation.stat_name(name)
            if metadata is None:
                continue
            candidate = logical.parent / name
            if not stat.S_ISREG(metadata.st_mode):
                raise ValueError(f"json_artifact_path_type_invalid:{candidate}")
            observed[name] = _file_identity(metadata)
        return observed

    initial_census = census()
    if not initial_census:
        raise FileNotFoundError(logical)
    decoded: list[tuple[str, dict[str, Any], bytes]] = []
    for name, expected_identity in initial_census.items():
        candidate = logical.parent / name
        try:
            descriptor = generation.open_name(name, os.O_RDONLY)
        except OSError as exc:
            raise ValueError(f"json_artifact_changed_during_read:{candidate}") from exc
        try:
            before_identity = generation.assert_open_descriptor_name_identity(
                descriptor,
                name,
            )
            if before_identity != expected_identity:
                raise ValueError(f"json_artifact_changed_during_read:{candidate}")
            with os.fdopen(os.dup(descriptor), "rb") as raw_handle:
                try:
                    if name.endswith(".gz"):
                        with gzip.GzipFile(
                            fileobj=raw_handle,
                            mode="rb",
                        ) as decoded_handle:
                            decoded_bytes = decoded_handle.read()
                    else:
                        decoded_bytes = raw_handle.read()
                except (EOFError, UnicodeDecodeError, gzip.BadGzipFile, ValueError):
                    raise
            value = _json_object_from_bytes(decoded_bytes, source=candidate)
            if (
                generation.assert_open_descriptor_name_identity(descriptor, name)
                != before_identity
            ):
                raise ValueError(f"json_artifact_changed_during_read:{candidate}")
        finally:
            os.close(descriptor)
        if not isinstance(value, dict):
            raise ValueError(f"json_artifact_not_object:{candidate}")
        decoded.append((name, value, decoded_bytes))
    if census() != initial_census:
        raise ValueError(f"json_artifact_changed_during_read:{logical}")
    if len(decoded) == 2 and decoded[0][2] != decoded[1][2]:
        raise ValueError(f"json_artifact_plain_gzip_conflict:{logical}")
    return decoded[0][1]


def read_json_object_strict(
    path: Path,
    *,
    generation: ArtifactGenerationLease | None = None,
) -> dict[str, Any]:
    """Read stable plain/gzip JSON from one no-follow pinned parent."""

    candidate = Path(path).absolute()
    logical = (
        candidate.with_name(candidate.name[: -len(".gz")])
        if candidate.suffix == ".gz"
        else candidate
    )
    if logical.suffix != ".json":
        raise ValueError(f"json_generation_logical_path_invalid:{logical}")
    if generation is not None:
        if generation.logical != logical:
            raise ValueError(f"json_generation_lease_path_mismatch:{logical}")
        return _read_json_object_strict_pinned(logical, generation)
    try:
        with _pinned_read_generation(
            logical,
            error_prefix="json_artifact",
        ) as read_generation:
            return _read_json_object_strict_pinned(logical, read_generation)
    except FileNotFoundError:
        raise
    except OSError as exc:
        raise ValueError(f"json_artifact_parent_invalid:{logical.parent}") from exc


def _read_json_object_strict_receipt_pinned(
    logical: Path,
    generation: ArtifactGenerationLease,
) -> JsonObjectReadReceipt:
    payload = _read_json_object_strict_pinned(logical, generation)
    names = (logical.name, f"{logical.name}.gz")
    initial_census: dict[str, tuple[int, int, int, int]] = {}
    for name in names:
        metadata = generation.stat_name(name)
        if metadata is None:
            continue
        if not stat.S_ISREG(metadata.st_mode):
            raise ValueError(f"json_artifact_path_type_invalid:{logical.parent / name}")
        initial_census[name] = _file_identity(metadata)
    if not initial_census:
        raise FileNotFoundError(logical)
    selected_name = logical.name if logical.name in initial_census else names[1]
    raw, identity = _read_generation_name_bytes(generation, selected_name)
    try:
        decoded = gzip.decompress(raw) if selected_name.endswith(".gz") else raw
    except (EOFError, gzip.BadGzipFile, OSError) as exc:
        raise ValueError(
            f"json_generation_gzip_invalid:{logical.parent / selected_name}"
        ) from exc
    if (
        _json_object_from_bytes(decoded, source=logical.parent / selected_name)
        != payload
    ):
        raise ValueError(f"json_artifact_changed_during_read:{logical}")
    final_census: dict[str, tuple[int, int, int, int]] = {}
    for name in names:
        metadata = generation.stat_name(name)
        if metadata is None:
            continue
        if not stat.S_ISREG(metadata.st_mode):
            raise ValueError(f"json_artifact_path_type_invalid:{logical.parent / name}")
        final_census[name] = _file_identity(metadata)
    if final_census != initial_census:
        raise ValueError(f"json_artifact_changed_during_read:{logical}")
    generation.assert_parent_current()
    return JsonObjectReadReceipt(
        logical_path=logical,
        physical_path=logical.parent / selected_name,
        payload=payload,
        raw_sha256=hashlib.sha256(raw).hexdigest(),
        decoded_sha256=hashlib.sha256(decoded).hexdigest(),
        physical_identity=identity,
        generation_census=tuple(sorted(initial_census.items())),
        parent_identity=generation.parent_identity,
    )


def read_json_object_strict_receipt(
    path: Path,
    *,
    generation: ArtifactGenerationLease | None = None,
) -> JsonObjectReadReceipt:
    """Read payload, raw hash, and file identity from one pinned generation."""

    logical = _logical_json_path(path)
    if generation is not None:
        if generation.logical != logical:
            raise ValueError(f"json_generation_lease_path_mismatch:{logical}")
        return _read_json_object_strict_receipt_pinned(logical, generation)
    try:
        with _pinned_read_generation(
            logical,
            error_prefix="json_artifact",
        ) as read_generation:
            return _read_json_object_strict_receipt_pinned(
                logical,
                read_generation,
            )
    except FileNotFoundError:
        raise
    except OSError as exc:
        raise ValueError(f"json_artifact_parent_invalid:{logical.parent}") from exc


def json_object_generation_census(
    path: Path,
) -> tuple[tuple[int, int], tuple[tuple[str, tuple[int, int, int, int, int]], ...]]:
    """Return an O(1)-memory no-follow identity census for cache validation."""

    logical = _logical_json_path(path)
    try:
        with _pinned_read_generation(
            logical,
            error_prefix="json_artifact",
        ) as generation:
            names = (logical.name, f"{logical.name}.gz")

            def census() -> tuple[tuple[str, tuple[int, int, int, int, int]], ...]:
                rows: list[tuple[str, tuple[int, int, int, int, int]]] = []
                for name in names:
                    metadata = generation.stat_name(name)
                    if metadata is None:
                        continue
                    if not stat.S_ISREG(metadata.st_mode):
                        raise ValueError(
                            "json_artifact_path_type_invalid:"
                            f"{logical.parent / name}"
                        )
                    rows.append(
                        (
                            name,
                            (
                                metadata.st_dev,
                                metadata.st_ino,
                                metadata.st_size,
                                metadata.st_mtime_ns,
                                metadata.st_ctime_ns,
                            ),
                        )
                    )
                if not rows:
                    raise FileNotFoundError(logical)
                return tuple(rows)

            before = census()
            after = census()
            if before != after:
                raise ValueError(f"json_artifact_changed_during_read:{logical}")
            generation.assert_parent_current()
            return generation.parent_identity, before
    except FileNotFoundError:
        raise
    except OSError as exc:
        raise ValueError(f"json_artifact_parent_invalid:{logical.parent}") from exc


def open_text_auto(path: Path, *, errors: str = "replace") -> TextIO:
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors=errors)
    return path.open("r", encoding="utf-8", errors=errors)


def iter_jsonl(path: Path, *, errors: str = "replace") -> Iterator[dict[str, Any]]:
    actual_path = existing_or_gzip_path(path)
    if not actual_path.exists():
        return
    with open_text_auto(actual_path, errors=errors) as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                yield payload


def read_jsonl(path: Path, *, errors: str = "replace") -> list[dict[str, Any]]:
    return list(iter_jsonl(path, errors=errors))


def _iter_jsonl_objects_strict_pinned(
    logical: Path,
    generation: ArtifactGenerationLease,
    *,
    provenance: dict[str, Any] | None,
) -> Iterator[dict[str, Any]]:
    candidate_names = (logical.name, f"{logical.name}.gz")

    def census() -> dict[str, tuple[int, int, int, int]]:
        observed: dict[str, tuple[int, int, int, int]] = {}
        for name in candidate_names:
            metadata = generation.stat_name(name)
            if metadata is None:
                continue
            item = logical.parent / name
            if not stat.S_ISREG(metadata.st_mode):
                raise ValueError(f"jsonl_artifact_path_type_invalid:{item}")
            observed[name] = _file_identity(metadata)
        return observed

    initial_census = census()
    if not initial_census:
        raise FileNotFoundError(logical)
    descriptors: dict[str, int] = {}
    try:
        for name, expected_identity in initial_census.items():
            item = logical.parent / name
            descriptor = generation.open_name(name, os.O_RDONLY)
            descriptors[name] = descriptor
            if (
                generation.assert_open_descriptor_name_identity(descriptor, name)
                != expected_identity
            ):
                raise ValueError(f"jsonl_artifact_changed_during_read:{item}")

        class _DigestingReader:
            """Minimal file wrapper that hashes compressed bytes as gzip reads."""

            def __init__(self, handle: Any, digest: Any) -> None:
                self._handle = handle
                self._digest = digest

            def read(self, size: int = -1) -> bytes:
                chunk = self._handle.read(size)
                if chunk:
                    self._digest.update(chunk)
                return chunk

            def readable(self) -> bool:
                return True

            def seekable(self) -> bool:
                return False

        def stream(
            name: str,
            descriptor: int,
            *,
            emit_rows: bool,
            metrics: dict[str, Any],
        ) -> Iterator[dict[str, Any]]:
            item = logical.parent / name
            os.lseek(descriptor, 0, os.SEEK_SET)
            stored_digest = hashlib.sha256()
            decoded_digest = hashlib.sha256()
            decoded_bytes = 0
            line_count = 0
            nonempty_line_count = 0
            object_count = 0
            duplicate = os.dup(descriptor)
            try:
                with os.fdopen(duplicate, "rb") as raw_handle:
                    if name.endswith(".gz"):
                        stream_context = gzip.GzipFile(
                            fileobj=_DigestingReader(raw_handle, stored_digest),
                            mode="rb",
                        )
                    else:
                        stream_context = raw_handle
                    try:
                        for raw_line in stream_context:
                            if not name.endswith(".gz"):
                                stored_digest.update(raw_line)
                            decoded_digest.update(raw_line)
                            decoded_bytes += len(raw_line)
                            line_count += 1
                            if not raw_line.strip():
                                continue
                            nonempty_line_count += 1
                            parsed = _json_object_from_bytes(raw_line, source=item)
                            object_count += 1
                            if emit_rows:
                                yield parsed
                    finally:
                        if name.endswith(".gz"):
                            stream_context.close()
            except (EOFError, gzip.BadGzipFile, OSError) as exc:
                raise ValueError(f"jsonl_artifact_payload_invalid:{item}") from exc
            metrics.update(
                {
                    "stored_sha256": stored_digest.hexdigest(),
                    "stored_size_bytes": os.fstat(descriptor).st_size,
                    "decoded_content_sha256": decoded_digest.hexdigest(),
                    "decoded_content_bytes": decoded_bytes,
                    "line_count": line_count,
                    "nonempty_line_count": nonempty_line_count,
                    "object_row_count": object_count,
                }
            )
            if (
                generation.assert_open_descriptor_name_identity(descriptor, name)
                != initial_census[name]
            ):
                raise ValueError(f"jsonl_artifact_changed_during_read:{item}")

        selected = logical.name if logical.name in descriptors else f"{logical.name}.gz"
        selected_scan: dict[str, Any] = {}
        scans: dict[str, dict[str, Any]] = {selected: selected_scan}
        comparison_names = [name for name in descriptors if name != selected]
        if comparison_names:
            comparison_name = comparison_names[0]
            comparison_scan: dict[str, Any] = {}
            scans[comparison_name] = comparison_scan
            for _row in stream(
                comparison_name,
                descriptors[comparison_name],
                emit_rows=False,
                metrics=comparison_scan,
            ):
                raise AssertionError("non-emitting JSONL scan yielded a row")
            if census() != initial_census:
                raise ValueError(f"jsonl_artifact_changed_during_read:{logical}")

        yield from stream(
            selected,
            descriptors[selected],
            emit_rows=True,
            metrics=selected_scan,
        )
        if len(scans) == 2:
            comparison_scan = scans[comparison_names[0]]
            identity_fields = (
                "decoded_content_sha256",
                "decoded_content_bytes",
                "line_count",
                "nonempty_line_count",
                "object_row_count",
            )
            if any(
                selected_scan.get(field) != comparison_scan.get(field)
                for field in identity_fields
            ):
                raise ValueError(f"jsonl_artifact_plain_gzip_conflict:{logical}")
        if census() != initial_census:
            raise ValueError(f"jsonl_artifact_changed_during_read:{logical}")
        if provenance is not None:
            selected_path = logical.parent / selected
            provenance.update(
                {
                    "logical_source_path": str(logical),
                    "source_path": str(selected_path),
                    "source_compression": (
                        "gzip" if selected.endswith(".gz") else "plain"
                    ),
                    "source_sha256": selected_scan["stored_sha256"],
                    "source_bytes": selected_scan["stored_size_bytes"],
                    "source_content_sha256": selected_scan["decoded_content_sha256"],
                    "source_content_bytes": selected_scan["decoded_content_bytes"],
                    "source_line_count": selected_scan["line_count"],
                    "source_nonempty_line_count": selected_scan["nonempty_line_count"],
                    "source_json_object_row_count": selected_scan["object_row_count"],
                    "physical_representations": [
                        {
                            "compression": (
                                "gzip" if name.endswith(".gz") else "plain"
                            ),
                            "stored_bytes": scans[name]["stored_size_bytes"],
                            "stored_sha256": scans[name]["stored_sha256"],
                        }
                        for name in candidate_names
                        if name in scans
                    ],
                    "source_snapshot_stable": True,
                }
            )
    finally:
        for descriptor in descriptors.values():
            os.close(descriptor)


def iter_jsonl_objects_strict(
    path: Path,
    *,
    provenance: dict[str, Any] | None = None,
    generation: ArtifactGenerationLease | None = None,
) -> Iterator[dict[str, Any]]:
    """Yield stable strict JSONL from one no-follow pinned parent."""

    candidate = Path(path).absolute()
    logical = (
        candidate.with_name(candidate.name[: -len(".gz")])
        if candidate.suffix == ".gz"
        else candidate
    )
    if logical.suffix != ".jsonl":
        raise ValueError(f"jsonl_generation_logical_path_invalid:{logical}")
    if generation is not None:
        if generation.logical != logical:
            raise ValueError(f"jsonl_generation_lease_path_mismatch:{logical}")
        yield from _iter_jsonl_objects_strict_pinned(
            logical,
            generation,
            provenance=provenance,
        )
        return
    try:
        with _pinned_read_generation(
            logical,
            error_prefix="jsonl_artifact",
        ) as read_generation:
            yield from _iter_jsonl_objects_strict_pinned(
                logical,
                read_generation,
                provenance=provenance,
            )
    except FileNotFoundError:
        raise
    except OSError as exc:
        raise ValueError(f"jsonl_artifact_parent_invalid:{logical.parent}") from exc

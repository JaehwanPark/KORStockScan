"""Post-session compression and opt-in retention for forward observations.

The default CLI is dry-run.  ``--apply`` is required before any file changes.
Only validated ``trade_date=YYYY-MM-DD`` descendants of the configured root
are eligible, and the current trade date is never compressed or removed.
Compression and deletion are separate authorities: expired trade-date
partitions are removed only when ``--purge-expired`` is supplied explicitly.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import shutil
import stat
import tempfile
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .path_journal import PathStoragePolicy, partition_maintenance_lock

MAINTENANCE_SCHEMA = "scalp_micro_reversion_storage_maintenance_v1"
MAINTENANCE_AUTHORITY = "post_session_storage_only_no_trading_authority"
KST = ZoneInfo("Asia/Seoul")
MAINTENANCE_METRIC_CONTRACT = {
    "metric_role": "source_quality_and_storage_retention",
    "decision_authority": MAINTENANCE_AUTHORITY,
    "window_policy": "closed_trade_dates_only",
    "sample_floor": "not_applicable_storage_operation",
    "primary_decision_metric": "retained_uncompressed_bytes",
    "source_quality_gate": "verified_trade_date_path_and_gzip_roundtrip_sha256",
    "forbidden_uses": [
        "current_trade_date_mutation",
        "retention_purge_without_explicit_opt_in",
        "broker_order_submission",
        "strategy_or_threshold_change",
        "provider_or_bot_mutation",
        "economic_edge_claim",
    ],
}


@dataclass(frozen=True, slots=True)
class StorageMaintenanceAction:
    action: str
    path: str
    trade_date: str
    source_bytes: int
    applied: bool


def maintain_forward_storage(
    root: Path,
    *,
    as_of_date: date,
    storage_policy: PathStoragePolicy | None = None,
    apply: bool = False,
    purge_expired: bool = False,
) -> dict[str, object]:
    if not isinstance(apply, bool) or not isinstance(purge_expired, bool):
        raise TypeError("storage maintenance authorities must be native booleans")
    policy = storage_policy or PathStoragePolicy()
    root_path = Path(root).resolve()
    runtime_trade_date = datetime.now(KST).date()
    if apply and as_of_date > runtime_trade_date:
        raise ValueError("storage maintenance as-of date must not be in the future")
    protected_trade_dates = {as_of_date, runtime_trade_date}
    actions: list[StorageMaintenanceAction] = []
    partition_failures: list[dict[str, str]] = []
    purge_candidate_count = 0
    purge_candidate_bytes = 0
    if not root_path.exists():
        return _result(
            root_path,
            as_of_date,
            runtime_trade_date,
            apply,
            purge_expired,
            actions,
            partition_failures=partition_failures,
            purge_candidate_count=purge_candidate_count,
            purge_candidate_bytes=purge_candidate_bytes,
        )
    for candidate in sorted(root_path.glob("trade_date=????-??-??")):
        candidate_trade_date = candidate.name.removeprefix("trade_date=")
        try:
            trade_dir = _validated_descendant(root_path, candidate)
            if not trade_dir.is_dir() or trade_dir.is_symlink():
                raise ValueError("trade-date maintenance target must be a directory")
            trade_date = date.fromisoformat(candidate_trade_date)
        except Exception as exc:
            partition_failures.append(
                {
                    "trade_date": candidate_trade_date,
                    "path": str(candidate),
                    "error_type": type(exc).__name__,
                    "reason": str(exc),
                    "candidate_count": "1",
                    "candidate_bytes": "0",
                    "published_target_count": "0",
                    "unlinked_source_count": "0",
                    "manifest_update_count": "0",
                    "recovery_required": "false",
                }
            )
            continue
        if trade_date in protected_trade_dates:
            continue
        age_days = (as_of_date - trade_date).days
        if age_days <= 0:
            continue
        try:
            if apply:
                with partition_maintenance_lock(
                    trade_dir,
                    blocking=False,
                    exclusive=True,
                ):
                    partition_actions, purge_count, purge_bytes, group_failures = (
                        _maintain_trade_directory(
                            root_path,
                            trade_dir,
                            trade_date=trade_date,
                            age_days=age_days,
                            as_of_date=as_of_date,
                            policy=policy,
                            apply=True,
                            purge_expired=purge_expired,
                        )
                    )
            else:
                partition_actions, purge_count, purge_bytes, group_failures = (
                    _maintain_trade_directory(
                        root_path,
                        trade_dir,
                        trade_date=trade_date,
                        age_days=age_days,
                        as_of_date=as_of_date,
                        policy=policy,
                        apply=False,
                        purge_expired=purge_expired,
                    )
                )
        except Exception as exc:
            try:
                failed_bytes = _tree_bytes(trade_dir)
            except OSError:
                failed_bytes = 0
            partition_failures.append(
                {
                    "trade_date": trade_date.isoformat(),
                    "path": str(trade_dir),
                    "error_type": type(exc).__name__,
                    "reason": str(exc),
                    "candidate_count": "1",
                    "candidate_bytes": str(failed_bytes),
                    "recovery_required": "false",
                }
            )
            continue
        actions.extend(partition_actions)
        partition_failures.extend(group_failures)
        purge_candidate_count += purge_count
        purge_candidate_bytes += purge_bytes
    return _result(
        root_path,
        as_of_date,
        runtime_trade_date,
        apply,
        purge_expired,
        actions,
        partition_failures=partition_failures,
        purge_candidate_count=purge_candidate_count,
        purge_candidate_bytes=purge_candidate_bytes,
    )


def _maintain_trade_directory(
    root_path: Path,
    trade_dir: Path,
    *,
    trade_date: date,
    age_days: int,
    as_of_date: date,
    policy: PathStoragePolicy,
    apply: bool,
    purge_expired: bool,
) -> tuple[
    list[StorageMaintenanceAction],
    int,
    int,
    list[dict[str, str]],
]:
    partition_actions: list[StorageMaintenanceAction] = []
    partition_failures = _descendant_symlink_failures(
        trade_dir,
        trade_date=trade_date,
    )

    purge_candidate_count = 0
    purge_candidate_bytes = 0
    if age_days > policy.retention_days:
        source_bytes = _tree_bytes(trade_dir)
        purge_candidate_count = 1
        purge_candidate_bytes = source_bytes
        if purge_expired:
            if partition_failures:
                return (
                    partition_actions,
                    purge_candidate_count,
                    purge_candidate_bytes,
                    partition_failures,
                )
            if apply:
                try:
                    _assert_tree_stable_and_closed(trade_dir, phase="before_purge")
                    shutil.rmtree(trade_dir)
                except Exception as exc:
                    remaining_bytes = (
                        _tree_bytes(trade_dir) if trade_dir.exists() else 0
                    )
                    deleted_bytes = max(0, source_bytes - remaining_bytes)
                    if deleted_bytes > 0 or not trade_dir.exists():
                        partition_actions.append(
                            StorageMaintenanceAction(
                                action=(
                                    "purge_trade_date_partial"
                                    if trade_dir.exists()
                                    else "purge_trade_date"
                                ),
                                path=str(trade_dir),
                                trade_date=trade_date.isoformat(),
                                source_bytes=deleted_bytes,
                                applied=True,
                            )
                        )
                    partition_failures.append(
                        _failure_row(
                            trade_date=trade_date,
                            path=trade_dir,
                            exc=exc,
                            candidate_count=int(trade_dir.exists()),
                            candidate_bytes=remaining_bytes,
                            recovery_required=(
                                trade_dir.exists() and deleted_bytes > 0
                            ),
                        )
                    )
                    return (
                        partition_actions,
                        purge_candidate_count,
                        purge_candidate_bytes,
                        partition_failures,
                    )
                else:
                    partition_actions.append(
                        StorageMaintenanceAction(
                            action="purge_trade_date",
                            path=str(trade_dir),
                            trade_date=trade_date.isoformat(),
                            source_bytes=source_bytes,
                            applied=True,
                        )
                    )
                    return (
                        partition_actions,
                        purge_candidate_count,
                        purge_candidate_bytes,
                        partition_failures,
                    )
            else:
                partition_actions.append(
                    StorageMaintenanceAction(
                        action="purge_trade_date",
                        path=str(trade_dir),
                        trade_date=trade_date.isoformat(),
                        source_bytes=source_bytes,
                        applied=False,
                    )
                )
                return (
                    partition_actions,
                    purge_candidate_count,
                    purge_candidate_bytes,
                    partition_failures,
                )
    if age_days < policy.compression_after_days:
        return (
            partition_actions,
            purge_candidate_count,
            purge_candidate_bytes,
            partition_failures,
        )

    compression_actions, compression_failures = _maintain_compression_groups(
        root_path,
        trade_dir,
        trade_date=trade_date,
        as_of_date=as_of_date,
        apply=apply,
    )
    partition_actions.extend(compression_actions)
    partition_failures.extend(compression_failures)
    return (
        partition_actions,
        purge_candidate_count,
        purge_candidate_bytes,
        partition_failures,
    )


def _descendant_symlink_failures(
    trade_dir: Path,
    *,
    trade_date: date,
) -> list[dict[str, str]]:
    return [
        _failure_row(
            trade_date=trade_date,
            path=candidate,
            exc=OSError(f"symlink descendant is forbidden:{candidate}"),
            candidate_count=1,
            candidate_bytes=0,
            recovery_required=False,
        )
        for candidate in sorted(trade_dir.rglob("*"))
        if candidate.is_symlink()
    ]


def _failure_row(
    *,
    trade_date: date,
    path: Path,
    exc: Exception,
    candidate_count: int,
    candidate_bytes: int,
    recovery_required: bool,
    published_target_count: int = 0,
    unlinked_source_count: int = 0,
    manifest_update_count: int = 0,
) -> dict[str, str]:
    return {
        "trade_date": trade_date.isoformat(),
        "path": str(path),
        "error_type": type(exc).__name__,
        "reason": str(exc),
        "candidate_count": str(candidate_count),
        "candidate_bytes": str(candidate_bytes),
        "published_target_count": str(published_target_count),
        "unlinked_source_count": str(unlinked_source_count),
        "manifest_update_count": str(manifest_update_count),
        "recovery_required": str(recovery_required).lower(),
    }


def _validated_descendant(root: Path, candidate: Path) -> Path:
    lexical = candidate.absolute()
    try:
        relative = lexical.relative_to(root)
    except ValueError as exc:
        raise ValueError("storage maintenance target escapes configured root") from exc
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("storage maintenance does not follow symlinks")
    resolved = candidate.resolve()
    if not resolved.is_relative_to(root) or resolved == root:
        raise ValueError("storage maintenance target escapes configured root")
    return resolved


def _path_has_open_fd(path: Path) -> bool:
    try:
        expected = path.stat()
    except FileNotFoundError:
        return False
    proc_root = Path("/proc")
    if not proc_root.is_dir():
        raise OSError("open FD verification requires /proc")
    for process_dir in proc_root.iterdir():
        if not process_dir.name.isdigit():
            continue
        fd_dir = process_dir / "fd"
        try:
            descriptors = tuple(fd_dir.iterdir())
        except OSError:
            continue
        for descriptor in descriptors:
            try:
                opened = descriptor.stat()
            except OSError:
                continue
            if opened.st_dev == expected.st_dev and opened.st_ino == expected.st_ino:
                return True
    return False


def _capture_stable_file(path: Path) -> tuple[int, int, int, int, str]:
    if path.is_symlink():
        raise OSError(f"unsafe_symlink_file:{path}")
    initial = path.lstat()
    if not stat.S_ISREG(initial.st_mode):
        raise OSError(f"unsafe_non_regular_file:{path}")
    if _path_has_open_fd(path):
        raise OSError(f"source_open_fd:{path}")
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise OSError(f"unsafe_non_regular_file:{path}")
        digest = hashlib.sha256()
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    path_after = path.lstat()
    if not stat.S_ISREG(path_after.st_mode):
        raise OSError(f"unsafe_non_regular_file_after_stability_check:{path}")
    before_metadata = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
    )
    after_metadata = (
        path_after.st_dev,
        path_after.st_ino,
        path_after.st_size,
        path_after.st_mtime_ns,
    )
    descriptor_after_metadata = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    )
    if (
        before_metadata != descriptor_after_metadata
        or before_metadata != after_metadata
    ):
        raise OSError(f"source_changed_during_stability_check:{path}")
    if _path_has_open_fd(path):
        raise OSError(f"source_open_fd_after_stability_check:{path}")
    return (*after_metadata, digest.hexdigest())


def _assert_source_unchanged_and_closed(
    source: Path,
    expected: tuple[int, int, int, int, str],
    *,
    phase: str,
) -> None:
    observed = _capture_stable_file(source)
    if observed != expected:
        raise OSError(f"source_changed_{phase}:{source}")


def _assert_tree_stable_and_closed(
    path: Path,
    *,
    phase: str = "partition_preflight",
) -> None:
    candidates = {
        candidate: _capture_stable_file(candidate)
        for candidate in sorted(path.rglob("*"))
        if candidate.is_file() and not candidate.is_symlink()
    }
    observed_paths = {
        candidate
        for candidate in path.rglob("*")
        if candidate.is_file() and not candidate.is_symlink()
    }
    if observed_paths != set(candidates):
        raise OSError(f"source_tree_changed_before_purge:{path}")
    for candidate, expected in candidates.items():
        _assert_source_unchanged_and_closed(
            candidate,
            expected,
            phase=phase,
        )


def _restored_gzip_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with gzip.open(path, "rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _validated_manifest_payload(manifest_path: Path) -> dict[str, object]:
    manifest_snapshot = _capture_stable_file(manifest_path)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    _assert_source_unchanged_and_closed(
        manifest_path,
        manifest_snapshot,
        phase="during_manifest_read",
    )
    if not isinstance(payload, dict) or not isinstance(payload.get("shards"), list):
        raise ValueError(f"invalid market stream manifest: {manifest_path}")
    for shard in payload["shards"]:
        if not isinstance(shard, dict):
            raise ValueError(f"invalid market stream shard manifest: {manifest_path}")
        file_name = str(shard.get("file") or "").strip()
        if not file_name:
            raise ValueError(f"missing shard filename: {manifest_path}")
        if Path(file_name).name != file_name:
            raise ValueError(
                f"manifest shard must be a local filename: {manifest_path}"
            )
        logical_name = file_name.removesuffix(".gz")
        if not logical_name.endswith(".jsonl"):
            raise ValueError(f"manifest shard must be JSONL: {manifest_path}")
        plain = manifest_path.parent / file_name
        compressed = plain.with_suffix(f"{plain.suffix}.gz")
        if plain.is_symlink() or compressed.is_symlink():
            raise OSError(f"manifest shard cannot be a symlink: {plain}")
        if not plain.exists() and not compressed.exists():
            raise FileNotFoundError(f"manifest shard is unavailable: {plain}")
        available = plain if plain.exists() else compressed
        if not available.is_file():
            raise OSError(f"manifest shard must be a regular file: {available}")
    return payload


def _manifest_logical_sources(manifest_path: Path) -> tuple[Path, ...]:
    payload = _validated_manifest_payload(manifest_path)
    sources: list[Path] = []
    for shard in payload["shards"]:
        file_path = manifest_path.parent / str(shard["file"])
        logical = file_path.with_suffix("") if file_path.suffix == ".gz" else file_path
        if logical.suffix == ".jsonl":
            sources.append(logical)
    return tuple(sources)


def _preflight_compression_group(
    sources: list[Path],
    manifest_path: Path | None,
) -> None:
    if manifest_path is not None:
        _validated_manifest_payload(manifest_path)
    for source in sources:
        source_snapshot = _capture_stable_file(source)
        target = source.with_suffix(f"{source.suffix}.gz")
        if target.is_symlink():
            raise OSError(f"compressed_target_symlink_forbidden:{target}")
        if target.exists():
            target_snapshot = _capture_stable_file(target)
            if _restored_gzip_sha256(target) != source_snapshot[-1]:
                raise OSError(f"existing_compressed_source_mismatch:{source}")
            _assert_source_unchanged_and_closed(
                target,
                target_snapshot,
                phase="group_preflight",
            )


def _maintain_compression_groups(
    root_path: Path,
    trade_dir: Path,
    *,
    trade_date: date,
    as_of_date: date,
    apply: bool,
) -> tuple[list[StorageMaintenanceAction], list[dict[str, str]]]:
    actions: list[StorageMaintenanceAction] = []
    failures: list[dict[str, str]] = []
    directories = sorted(
        {
            path.parent
            for path in (
                *trade_dir.rglob("*.jsonl"),
                *trade_dir.rglob("*.manifest.json"),
            )
            if not path.is_symlink()
        }
    )
    for directory in directories:
        sources_in_directory = sorted(
            path for path in directory.glob("*.jsonl") if not path.is_symlink()
        )
        manifests = sorted(
            path for path in directory.glob("*.manifest.json") if not path.is_symlink()
        )
        manifest_groups: list[tuple[Path, list[Path]]] = []
        source_owners: dict[Path, Path] = {}
        preflight_errors: list[tuple[Path, Exception]] = []
        for manifest_path in manifests:
            try:
                logical_sources = list(_manifest_logical_sources(manifest_path))
                duplicate_sources = {
                    source
                    for source in logical_sources
                    if logical_sources.count(source) > 1
                }
                overlap = {
                    source for source in logical_sources if source in source_owners
                }
                if duplicate_sources or overlap:
                    conflicts = duplicate_sources | overlap
                    raise ValueError(
                        "multiple manifests claim one shard:"
                        + ",".join(str(path) for path in sorted(conflicts))
                    )
                manifest_groups.append(
                    (
                        manifest_path,
                        [source for source in logical_sources if source.exists()],
                    )
                )
                source_owners.update(
                    {source: manifest_path for source in logical_sources}
                )
            except Exception as exc:
                preflight_errors.append((manifest_path, exc))

        # Ownership is a directory-wide precondition. Processing an earlier
        # valid manifest before discovering a later overlap can strand the
        # latter on a missing plain shard. Reject the whole physical session
        # before publishing any gzip or rewriting any manifest.
        if preflight_errors:
            for manifest_path, exc in preflight_errors:
                failures.append(
                    _failure_row(
                        trade_date=trade_date,
                        path=manifest_path,
                        exc=exc,
                        candidate_count=0,
                        candidate_bytes=(
                            manifest_path.stat().st_size
                            if manifest_path.exists()
                            else 0
                        ),
                        recovery_required=False,
                    )
                )
            failures.append(
                _failure_row(
                    trade_date=trade_date,
                    path=directory,
                    exc=ValueError("directory_manifest_ownership_preflight_failed"),
                    candidate_count=len(sources_in_directory),
                    candidate_bytes=sum(
                        source.stat().st_size for source in sources_in_directory
                    ),
                    recovery_required=False,
                )
            )
            continue

        groups: list[tuple[Path | None, list[Path]]] = list(manifest_groups)
        groups.extend(
            (None, [source])
            for source in sources_in_directory
            if source not in source_owners
        )
        for manifest_path, sources in groups:
            group_path = manifest_path or sources[0]
            candidate_bytes = sum(
                source.stat().st_size for source in sources if source.exists()
            )
            if not apply:
                if manifest_path is not None and not sources:
                    if _manifest_requires_reference_repair(manifest_path):
                        actions.append(
                            StorageMaintenanceAction(
                                action="repair_manifest_reference",
                                path=str(manifest_path),
                                trade_date=trade_date.isoformat(),
                                source_bytes=manifest_path.stat().st_size,
                                applied=False,
                            )
                        )
                    continue
                actions.extend(
                    StorageMaintenanceAction(
                        action=(
                            "finalize_verified_compression"
                            if source.with_suffix(f"{source.suffix}.gz").exists()
                            else "compress_jsonl"
                        ),
                        path=str(source),
                        trade_date=trade_date.isoformat(),
                        source_bytes=source.stat().st_size,
                        applied=False,
                    )
                    for source in sources
                )
                continue
            try:
                if manifest_path is not None and not sources:
                    if _refresh_one_manifest(
                        manifest_path,
                        as_of_date=as_of_date,
                    ):
                        actions.append(
                            StorageMaintenanceAction(
                                action="repair_manifest_reference",
                                path=str(manifest_path),
                                trade_date=trade_date.isoformat(),
                                source_bytes=manifest_path.stat().st_size,
                                applied=True,
                            )
                        )
                    continue
                sources = [
                    _validated_descendant(root_path, source) for source in sources
                ]
                _preflight_compression_group(sources, manifest_path)
                group_actions, group_failure = _compress_group_verified(
                    sources,
                    manifest_path=manifest_path,
                    trade_date=trade_date,
                    as_of_date=as_of_date,
                )
                actions.extend(group_actions)
                if group_failure is not None:
                    failures.append(group_failure)
            except Exception as exc:
                failures.append(
                    _failure_row(
                        trade_date=trade_date,
                        path=group_path,
                        exc=exc,
                        candidate_count=len(sources),
                        candidate_bytes=candidate_bytes,
                        recovery_required=False,
                    )
                )
    return actions, failures


def _manifest_requires_reference_repair(manifest_path: Path) -> bool:
    payload = _validated_manifest_payload(manifest_path)
    for shard in payload["shards"]:
        plain = manifest_path.parent / str(shard["file"])
        if plain.suffix == ".gz" or plain.exists():
            continue
        if plain.with_suffix(f"{plain.suffix}.gz").exists():
            return True
    return False


def _prepare_verified_gzip(
    source: Path,
    target: Path,
    source_snapshot: tuple[int, int, int, int, str],
) -> Path:
    """Build and verify a private gzip without publishing or unlinking source."""

    source_hash = hashlib.sha256()
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with (
            source.open("rb") as input_handle,
            gzip.open(temporary, "wb", compresslevel=6) as output_handle,
        ):
            while chunk := input_handle.read(1024 * 1024):
                source_hash.update(chunk)
                output_handle.write(chunk)
        if source_hash.hexdigest() != source_snapshot[-1]:
            raise OSError(f"source_changed_during_compression:{source}")
        with temporary.open("rb") as handle:
            os.fsync(handle.fileno())
        verified_hash = hashlib.sha256()
        with gzip.open(temporary, "rb") as handle:
            while chunk := handle.read(1024 * 1024):
                verified_hash.update(chunk)
        if verified_hash.digest() != source_hash.digest():
            raise OSError("compressed JSONL verification failed")
        os.chmod(temporary, 0o640)
        return temporary
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _fsync_directory(path: Path) -> None:
    directory_descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(directory_descriptor)
    finally:
        os.close(directory_descriptor)


def _publish_gzip_no_clobber(temporary: Path, target: Path) -> None:
    """Atomically publish a prepared gzip without replacing any target inode."""

    try:
        os.link(temporary, target)
    except FileExistsError as exc:
        raise OSError(f"compressed_target_appeared_before_publish:{target}") from exc
    _fsync_directory(target.parent)


def _compress_group_verified(
    sources: list[Path],
    *,
    manifest_path: Path | None,
    trade_date: date,
    as_of_date: date,
) -> tuple[list[StorageMaintenanceAction], dict[str, str] | None]:

    plans: list[
        tuple[
            str,
            Path,
            Path,
            int,
            tuple[int, int, int, int, str],
            tuple[int, int, int, int, str] | None,
            Path | None,
        ]
    ] = []
    temporary_paths: list[Path] = []
    published_targets: set[Path] = set()
    manifest_before = manifest_path.read_bytes() if manifest_path is not None else None
    try:
        for source in sources:
            target = source.with_suffix(f"{source.suffix}.gz")
            if target.is_symlink():
                raise OSError(f"compressed_target_symlink_forbidden:{target}")
            source_snapshot = _capture_stable_file(source)
            source_bytes = source_snapshot[2]
            if target.exists():
                target_snapshot = _capture_stable_file(target)
                if _restored_gzip_sha256(target) != source_snapshot[-1]:
                    raise OSError(f"existing_compressed_source_mismatch:{source}")
                plans.append(
                    (
                        "finalize_verified_compression",
                        source,
                        target,
                        source_bytes,
                        source_snapshot,
                        target_snapshot,
                        None,
                    )
                )
                continue
            temporary = _prepare_verified_gzip(source, target, source_snapshot)
            temporary_paths.append(temporary)
            plans.append(
                (
                    "compress_jsonl",
                    source,
                    target,
                    source_bytes,
                    source_snapshot,
                    None,
                    temporary,
                )
            )

        # A later shard may have opened or changed while an earlier gzip was
        # being prepared. Close that window before publishing any target.
        for _, source, target, _, source_snapshot, target_snapshot, _ in plans:
            _assert_source_unchanged_and_closed(
                source,
                source_snapshot,
                phase="before_partition_publish",
            )
            if target_snapshot is None:
                if target.exists() or target.is_symlink():
                    raise OSError(f"compressed_target_appeared_before_publish:{target}")
            else:
                _assert_source_unchanged_and_closed(
                    target,
                    target_snapshot,
                    phase="before_partition_publish",
                )

        for _, _, target, _, _, _, temporary in plans:
            if temporary is not None:
                try:
                    _publish_gzip_no_clobber(temporary, target)
                finally:
                    if (
                        target.exists()
                        and not target.is_symlink()
                        and temporary.exists()
                    ):
                        target_state = target.lstat()
                        temporary_state = temporary.lstat()
                        if (
                            stat.S_ISREG(target_state.st_mode)
                            and target_state.st_dev == temporary_state.st_dev
                            and target_state.st_ino == temporary_state.st_ino
                        ):
                            published_targets.add(target)

        # Do not remove a source, or rewrite its manifest, if any shard became
        # open/unstable across publication. Valid gzip copies may remain as
        # recoverable evidence; they never replace another inode.
        for _, source, _, _, source_snapshot, _, _ in plans:
            _assert_source_unchanged_and_closed(
                source,
                source_snapshot,
                phase="after_partition_publish",
            )

        if manifest_path is not None:
            _refresh_one_manifest(
                manifest_path,
                as_of_date=as_of_date,
                planned_sources={plan[1] for plan in plans},
            )

        for _, source, target, _, source_snapshot, _, _ in plans:
            _assert_source_unchanged_and_closed(
                source,
                source_snapshot,
                phase="before_finalize_unlink",
            )
            target_snapshot = _capture_stable_file(target)
            if _restored_gzip_sha256(target) != source_snapshot[-1]:
                raise OSError(f"compressed_target_changed_before_unlink:{target}")
            _assert_source_unchanged_and_closed(
                target,
                target_snapshot,
                phase="before_finalize_unlink",
            )
            try:
                source.unlink()
            except OSError:
                if source.exists() or source.is_symlink():
                    raise
            _fsync_directory(source.parent)

        return (
            [
                StorageMaintenanceAction(
                    action=action,
                    path=str(source),
                    trade_date=trade_date.isoformat(),
                    source_bytes=source_bytes,
                    applied=True,
                )
                for action, source, _, source_bytes, _, _, _ in plans
            ],
            None,
        )
    except Exception as exc:
        partial_actions: list[StorageMaintenanceAction] = []
        unlinked_count = 0
        unresolved_plans: list[
            tuple[
                str,
                Path,
                Path,
                int,
                tuple[int, int, int, int, str],
                tuple[int, int, int, int, str] | None,
                Path | None,
            ]
        ] = []
        for plan in plans:
            action, source, target, source_bytes, _, _, _ = plan
            source_exists = source.exists()
            target_exists = target.exists()
            if target_exists and not source_exists:
                unlinked_count += 1
                partial_actions.append(
                    StorageMaintenanceAction(
                        action=action,
                        path=str(source),
                        trade_date=trade_date.isoformat(),
                        source_bytes=source_bytes,
                        applied=True,
                    )
                )
            else:
                unresolved_plans.append(plan)
                if target_exists and source_exists and target in published_targets:
                    partial_actions.append(
                        StorageMaintenanceAction(
                            action="publish_verified_gzip_source_preserved",
                            path=str(source),
                            trade_date=trade_date.isoformat(),
                            source_bytes=source_bytes,
                            applied=True,
                        )
                    )
        manifest_changed = (
            manifest_path is not None
            and manifest_path.exists()
            and manifest_before != manifest_path.read_bytes()
        )
        if manifest_changed:
            partial_actions.append(
                StorageMaintenanceAction(
                    action="repair_manifest_reference",
                    path=str(manifest_path),
                    trade_date=trade_date.isoformat(),
                    source_bytes=manifest_path.stat().st_size,
                    applied=True,
                )
            )
        failure = _failure_row(
            trade_date=trade_date,
            path=manifest_path or sources[0],
            exc=exc,
            candidate_count=len(unresolved_plans),
            candidate_bytes=sum(plan[3] for plan in unresolved_plans),
            recovery_required=any(
                source.exists() and target.exists() for _, source, target, *_ in plans
            ),
            published_target_count=sum(target.exists() for target in published_targets),
            unlinked_source_count=unlinked_count,
            manifest_update_count=int(manifest_changed),
        )
        return partial_actions, failure
    finally:
        for temporary in temporary_paths:
            temporary.unlink(missing_ok=True)


def _refresh_one_manifest(
    manifest_path: Path,
    *,
    as_of_date: date,
    planned_sources: set[Path] | None = None,
) -> bool:
    """Keep one writer manifest discoverable after group-local compression."""

    planned = planned_sources or set()
    payload = _validated_manifest_payload(manifest_path)
    changed = False
    for shard in payload["shards"]:
        file_name = str(shard.get("file") or "").strip()
        plain = manifest_path.parent / file_name
        if plain.suffix == ".gz":
            continue
        compressed = plain.with_suffix(f"{plain.suffix}.gz")
        if plain.exists() and plain not in planned:
            continue
        if not compressed.exists():
            raise FileNotFoundError(f"manifest shard is unavailable: {plain}")
        shard["file"] = compressed.name
        shard["bytes"] = compressed.stat().st_size
        shard["compressed"] = True
        changed = True
    if changed:
        payload["storage_maintenance_schema"] = MAINTENANCE_SCHEMA
        payload["storage_maintenance_as_of_date"] = as_of_date.isoformat()
        _write_json_atomic(manifest_path, payload)
    return changed


def _write_json_atomic(path: Path, payload: dict[str, object]) -> None:
    expected = _capture_stable_file(path)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        encoded = (
            json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n"
        ).encode("utf-8")
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o640)
        _assert_source_unchanged_and_closed(
            path,
            expected,
            phase="before_manifest_publish",
        )
        os.replace(temporary, path)
        directory_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        temporary.unlink(missing_ok=True)


def _tree_bytes(path: Path) -> int:
    total = 0
    for item in path.rglob("*"):
        state = item.lstat()
        if stat.S_ISREG(state.st_mode):
            total += state.st_size
    return total


def _result(
    root: Path,
    as_of_date: date,
    runtime_trade_date: date,
    apply: bool,
    purge_expired: bool,
    actions: list[StorageMaintenanceAction],
    *,
    partition_failures: list[dict[str, str]],
    purge_candidate_count: int,
    purge_candidate_bytes: int,
) -> dict[str, object]:
    purge_applied_count = sum(
        row.action == "purge_trade_date" and row.applied for row in actions
    )
    purge_partial_applied_count = sum(
        row.action == "purge_trade_date_partial" and row.applied for row in actions
    )
    return {
        "schema": MAINTENANCE_SCHEMA,
        "root": str(root),
        "as_of_date": as_of_date.isoformat(),
        "runtime_trade_date": runtime_trade_date.isoformat(),
        "protected_trade_dates": sorted(
            {as_of_date.isoformat(), runtime_trade_date.isoformat()}
        ),
        "mode": "apply" if apply else "dry_run",
        "purge_enabled": purge_expired,
        "purge_status": (
            "explicit_opt_in_apply"
            if purge_expired and apply
            else (
                "explicit_opt_in_dry_run"
                if purge_expired
                else "disabled_no_deletion_authority"
            )
        ),
        "purge_candidate_count": purge_candidate_count,
        "purge_candidate_bytes": purge_candidate_bytes,
        "purge_applied_count": purge_applied_count,
        "purge_partial_applied_count": purge_partial_applied_count,
        "deletion_performed": (
            purge_applied_count > 0 or purge_partial_applied_count > 0
        ),
        "status": "partial_failure" if partition_failures else "pass",
        "partition_failure_count": len(partition_failures),
        "partition_failures": partition_failures,
        "failed_candidate_count": sum(
            int(row.get("candidate_count") or 0) for row in partition_failures
        ),
        "failed_candidate_bytes": sum(
            int(row.get("candidate_bytes") or 0) for row in partition_failures
        ),
        "recovery_required_count": sum(
            row.get("recovery_required") == "true" for row in partition_failures
        ),
        "action_count": len(actions),
        "source_bytes": sum(row.source_bytes for row in actions),
        "actions": [asdict(row) for row in actions],
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "trading_runtime_effect": False,
        **MAINTENANCE_METRIC_CONTRACT,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--as-of-date",
        type=date.fromisoformat,
        default=datetime.now(KST).date(),
    )
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--purge-expired",
        action="store_true",
        help=(
            "Explicitly authorize removal of validated trade-date partitions "
            "older than the configured retention window. Disabled by default."
        ),
    )
    args = parser.parse_args()
    result = maintain_forward_storage(
        args.root,
        as_of_date=args.as_of_date,
        apply=args.apply,
        purge_expired=args.purge_expired,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

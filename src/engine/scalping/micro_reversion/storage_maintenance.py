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
import tempfile
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo

from .path_journal import PathStoragePolicy

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
            purge_candidate_count=purge_candidate_count,
            purge_candidate_bytes=purge_candidate_bytes,
        )
    for trade_dir in _trade_date_directories(root_path):
        trade_date = date.fromisoformat(trade_dir.name.removeprefix("trade_date="))
        if trade_date in protected_trade_dates:
            continue
        age_days = (as_of_date - trade_date).days
        if age_days <= 0:
            continue
        if age_days > policy.retention_days:
            source_bytes = _tree_bytes(trade_dir)
            purge_candidate_count += 1
            purge_candidate_bytes += source_bytes
            if purge_expired:
                if apply:
                    shutil.rmtree(trade_dir)
                actions.append(
                    StorageMaintenanceAction(
                        action="purge_trade_date",
                        path=str(trade_dir),
                        trade_date=trade_date.isoformat(),
                        source_bytes=source_bytes,
                        applied=apply,
                    )
                )
                continue
        if age_days < policy.compression_after_days:
            continue
        for source in sorted(trade_dir.rglob("*.jsonl")):
            source = _validated_descendant(root_path, source)
            target = source.with_suffix(f"{source.suffix}.gz")
            if target.exists():
                source_bytes = source.stat().st_size
                if apply:
                    _finalize_verified_compression(source, target)
                actions.append(
                    StorageMaintenanceAction(
                        action="finalize_verified_compression",
                        path=str(source),
                        trade_date=trade_date.isoformat(),
                        source_bytes=source_bytes,
                        applied=apply,
                    )
                )
                continue
            source_bytes = source.stat().st_size
            if apply:
                _compress_verified(source, target)
            actions.append(
                StorageMaintenanceAction(
                    action="compress_jsonl",
                    path=str(source),
                    trade_date=trade_date.isoformat(),
                    source_bytes=source_bytes,
                    applied=apply,
                )
            )
        if apply:
            _refresh_compressed_manifests(trade_dir, as_of_date=as_of_date)
    return _result(
        root_path,
        as_of_date,
        runtime_trade_date,
        apply,
        purge_expired,
        actions,
        purge_candidate_count=purge_candidate_count,
        purge_candidate_bytes=purge_candidate_bytes,
    )


def _trade_date_directories(root: Path) -> Iterable[Path]:
    for candidate in sorted(root.glob("trade_date=????-??-??")):
        resolved = _validated_descendant(root, candidate)
        if resolved.is_dir() and not resolved.is_symlink():
            date.fromisoformat(resolved.name.removeprefix("trade_date="))
            yield resolved


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


def _compress_verified(source: Path, target: Path) -> None:
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
        with temporary.open("rb") as handle:
            os.fsync(handle.fileno())
        verified_hash = hashlib.sha256()
        with gzip.open(temporary, "rb") as handle:
            while chunk := handle.read(1024 * 1024):
                verified_hash.update(chunk)
        if verified_hash.digest() != source_hash.digest():
            raise OSError("compressed JSONL verification failed")
        os.chmod(temporary, 0o640)
        os.replace(temporary, target)
        directory_descriptor = os.open(target.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
        source.unlink()
        directory_descriptor = os.open(target.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        temporary.unlink(missing_ok=True)


def _finalize_verified_compression(source: Path, target: Path) -> None:
    """Recover an interrupted target-replace/source-unlink transition."""

    source_hash = hashlib.sha256()
    with source.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            source_hash.update(chunk)
    restored_hash = hashlib.sha256()
    with gzip.open(target, "rb") as handle:
        while chunk := handle.read(1024 * 1024):
            restored_hash.update(chunk)
    if restored_hash.digest() != source_hash.digest():
        raise OSError("existing compressed JSONL does not match source")
    source.unlink()
    directory_descriptor = os.open(source.parent, os.O_RDONLY)
    try:
        os.fsync(directory_descriptor)
    finally:
        os.close(directory_descriptor)


def _refresh_compressed_manifests(trade_dir: Path, *, as_of_date: date) -> None:
    """Keep writer manifests discoverable after closed-date compression."""

    for manifest_path in sorted(trade_dir.rglob("*.manifest.json")):
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or not isinstance(payload.get("shards"), list):
            raise ValueError(f"invalid market stream manifest: {manifest_path}")
        changed = False
        for shard in payload["shards"]:
            if not isinstance(shard, dict):
                raise ValueError(
                    f"invalid market stream shard manifest: {manifest_path}"
                )
            file_name = str(shard.get("file") or "").strip()
            if not file_name:
                raise ValueError(f"missing shard filename: {manifest_path}")
            plain = manifest_path.parent / file_name
            compressed = plain.with_suffix(f"{plain.suffix}.gz")
            if plain.exists():
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


def _write_json_atomic(path: Path, payload: dict[str, object]) -> None:
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
        os.replace(temporary, path)
        directory_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        temporary.unlink(missing_ok=True)


def _tree_bytes(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def _result(
    root: Path,
    as_of_date: date,
    runtime_trade_date: date,
    apply: bool,
    purge_expired: bool,
    actions: list[StorageMaintenanceAction],
    *,
    purge_candidate_count: int,
    purge_candidate_bytes: int,
) -> dict[str, object]:
    purge_applied_count = sum(
        row.action == "purge_trade_date" and row.applied for row in actions
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
        "deletion_performed": purge_applied_count > 0,
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

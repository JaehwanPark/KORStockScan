"""Post-session compression and bounded retention for forward observations.

The default CLI is dry-run.  ``--apply`` is required before any file changes.
Only validated ``trade_date=YYYY-MM-DD`` descendants of the configured root
are eligible, and the current trade date is never compressed or removed.
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
) -> dict[str, object]:
    policy = storage_policy or PathStoragePolicy()
    root_path = Path(root).resolve()
    actions: list[StorageMaintenanceAction] = []
    if not root_path.exists():
        return _result(root_path, as_of_date, apply, actions)
    for trade_dir in _trade_date_directories(root_path):
        trade_date = date.fromisoformat(trade_dir.name.removeprefix("trade_date="))
        age_days = (as_of_date - trade_date).days
        if age_days <= 0:
            continue
        if age_days > policy.retention_days:
            source_bytes = _tree_bytes(trade_dir)
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
        compressed_any = False
        for source in sorted(trade_dir.rglob("*.jsonl")):
            source = _validated_descendant(root_path, source)
            target = source.with_suffix(f"{source.suffix}.gz")
            if target.exists():
                raise FileExistsError(f"compressed target already exists: {target}")
            source_bytes = source.stat().st_size
            if apply:
                _compress_verified(source, target)
                compressed_any = True
            actions.append(
                StorageMaintenanceAction(
                    action="compress_jsonl",
                    path=str(source),
                    trade_date=trade_date.isoformat(),
                    source_bytes=source_bytes,
                    applied=apply,
                )
            )
        if apply and compressed_any:
            _refresh_compressed_manifests(trade_dir, as_of_date=as_of_date)
    return _result(root_path, as_of_date, apply, actions)


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
    apply: bool,
    actions: list[StorageMaintenanceAction],
) -> dict[str, object]:
    return {
        "schema": MAINTENANCE_SCHEMA,
        "root": str(root),
        "as_of_date": as_of_date.isoformat(),
        "mode": "apply" if apply else "dry_run",
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
    args = parser.parse_args()
    result = maintain_forward_storage(
        args.root,
        as_of_date=args.as_of_date,
        apply=args.apply,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

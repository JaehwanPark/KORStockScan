"""Compress raw dashboard files only after analytics ingestion is verified."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import stat as stat_module
import uuid
from datetime import date, timedelta
from pathlib import Path

from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import (
    jsonl_artifact_generation_lock,
    write_json_object_generation_safe,
)

PIPELINE_EVENTS_DIR = DATA_DIR / "pipeline_events"
CANONICAL_CONTEXT_DIR = DATA_DIR / "ai_canonical_context_candidates"
PIPELINE_SUMMARY_DIR = DATA_DIR / "pipeline_event_summaries"
MONITOR_SNAPSHOT_DIR = DATA_DIR / "report" / "monitor_snapshots"
MONITOR_SNAPSHOT_MANIFEST_DIR = MONITOR_SNAPSHOT_DIR / "manifests"
ANALYTICS_PARQUET_DIR = DATA_DIR / "analytics" / "parquet"
THRESHOLD_CYCLE_DIR = DATA_DIR / "threshold_cycle"
THRESHOLD_SNAPSHOT_DIR = THRESHOLD_CYCLE_DIR / "snapshots"
POSTCLOSE_STATUS_DIR = DATA_DIR / 'report' / 'threshold_cycle_postclose_status'
POSTCLOSE_CONTROLLER_DIR = DATA_DIR / 'report' / 'postclose_done_controller'
CANONICAL_CONTEXT_MIN_AGE_DAYS = 1
PIPELINE_SUMMARY_MIN_AGE_DAYS = 1
THRESHOLD_PARTITION_MIN_AGE_DAYS = 30
# Keep aligned with backfill_threshold_cycle_events.DEFAULT_MAX_OUTPUT_LINES_PER_PARTITION.
# This module must remain import-side-effect free because it runs under disk-pressure cleanup.
THRESHOLD_PARTITION_MAX_ROWS = 25_000


def _parse_iso_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except Exception:
        return None


def _date_from_pipeline_file(path: Path) -> date | None:
    stem = path.stem  # pipeline_events_YYYY-MM-DD
    if not stem.startswith("pipeline_events_"):
        return None
    return _parse_iso_date(stem.replace("pipeline_events_", "", 1))


def _date_from_threshold_snapshot_file(path: Path) -> date | None:
    stem = path.stem  # pipeline_events_YYYY-MM-DD_YYYYMMDD_HHMMSS
    prefix = "pipeline_events_"
    if not stem.startswith(prefix):
        return None
    parts = stem[len(prefix) :].split("_", 1)
    if not parts:
        return None
    return _parse_iso_date(parts[0])


def _date_from_named_file(path: Path, prefix: str) -> date | None:
    name = path.name
    suffix = ".jsonl"
    if not name.startswith(prefix) or not name.endswith(suffix):
        return None
    return _parse_iso_date(name[len(prefix) : -len(suffix)])


def _kind_and_date_from_snapshot_file(path: Path) -> tuple[str, date] | None:
    stem = path.stem  # {kind}_YYYY-MM-DD
    if "_" not in stem:
        return None
    maybe_date = _parse_iso_date(stem.split("_")[-1])
    if maybe_date is None:
        return None
    kind = stem[: -(len(maybe_date.isoformat()) + 1)]
    if not kind:
        return None
    return kind, maybe_date


def _parquet_partition_exists(dataset: str, target_date: date) -> bool:
    partition_dir = ANALYTICS_PARQUET_DIR / dataset / f"date={target_date.isoformat()}"
    return partition_dir.exists() and any(partition_dir.glob("*.parquet"))


def _snapshot_manifest_verifies(kind: str, target_date: date) -> bool:
    for manifest_path in sorted(
        MONITOR_SNAPSHOT_MANIFEST_DIR.glob(
            f"monitor_snapshot_manifest_{target_date.isoformat()}_*.json"
        )
    ):
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        snapshot_paths = payload.get("snapshot_paths") or {}
        tracked_path = snapshot_paths.get(kind)
        if not isinstance(tracked_path, str) or not tracked_path:
            continue
        if Path(tracked_path).name == f"{kind}_{target_date.isoformat()}.json":
            return True
    return False


def _threshold_backfill_exists(target_date: date) -> bool:
    partition_dir = THRESHOLD_CYCLE_DIR / f"date={target_date.isoformat()}"
    return partition_dir.exists() and (
        any(partition_dir.glob("family=*/part-*.jsonl"))
        or any(partition_dir.glob("family=*/part-*.jsonl.gz"))
    )


def _threshold_checkpoint(target_date: date) -> dict:
    checkpoint = THRESHOLD_CYCLE_DIR / "checkpoints" / f"{target_date.isoformat()}.json"
    try:
        payload = json.loads(checkpoint.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _threshold_backfill_complete(target_date: date) -> bool:
    return bool(_threshold_checkpoint(target_date).get("completed"))


def _threshold_partition_expected_rows(checkpoint: dict, path: Path) -> int | None:
    family = path.parent.name.replace("family=", "", 1)
    partitions = checkpoint.get("partitions")
    item = partitions.get(family) if isinstance(partitions, dict) else None
    try:
        current_part = int((item or {}).get("part") or 1)
        current_count = int((item or {}).get("line_count") or 0)
        part_number = int(path.stem.replace("part-", "", 1))
    except (TypeError, ValueError):
        return None
    if part_number < current_part:
        return THRESHOLD_PARTITION_MAX_ROWS
    if part_number == current_part and current_count > 0:
        return current_count
    return None


def _summary_manifest_expected_rows(
    path: Path, target_date: date, *, manifest_prefix: str
) -> int | None:
    manifest = PIPELINE_SUMMARY_DIR / f"{manifest_prefix}{target_date.isoformat()}.json"
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except Exception:
        return None
    tracked = str(payload.get("summary_path") or "")
    try:
        expected = int(payload.get("summary_row_count") or 0)
    except (TypeError, ValueError):
        return None
    if (
        expected <= 0
        or Path(tracked).name != path.name
        or payload.get("runtime_effect") is not False
    ):
        return None
    return expected


def _snapshot_json_boundary_valid(path: Path) -> bool:
    """Reject visibly truncated object snapshots without materializing them."""

    try:
        with path.open("rb") as handle:
            first_non_whitespace = b""
            while chunk := handle.read(64 * 1024):
                stripped = chunk.lstrip()
                if stripped:
                    first_non_whitespace = stripped[:1]
                    break
            if first_non_whitespace != b"{":
                return False
            file_size = handle.seek(0, os.SEEK_END)
            cursor = file_size
            last_non_whitespace = b""
            while cursor > 0:
                chunk_size = min(64 * 1024, cursor)
                cursor -= chunk_size
                handle.seek(cursor)
                stripped = handle.read(chunk_size).rstrip()
                if stripped:
                    last_non_whitespace = stripped[-1:]
                    break
            return last_non_whitespace == b"}"
    except OSError:
        return False


def _gzip_file(path: Path, *, dry_run: bool, custody=None) -> tuple[bool, int]:
    """Retain failed owned archive bytes outside the canonical alias namespace."""
    attempt = {}
    try:
        return _gzip_file_unchecked(path,dry_run=dry_run,custody=custody,_attempt=attempt)
    except Exception:
        if not path.is_file() or path.is_symlink():
            # Once the plain source is gone, never move its sole archive out
            # of the canonical namespace on an unexpected later exception.
            raise
        # The existing JSONL generation owner excludes cooperative writers.
        # A foreign replacement inode is never moved or removed here.
        from src.engine.lifecycle.snapshot_archive import file_identity
        archived = Path(str(path)+'.gz')
        expected = attempt.get('archive_identity')
        if expected is not None and archived.is_file() and not archived.is_symlink():
            current = file_identity(archived.stat())
            if (current['device'],current['inode']) == (expected['device'],expected['inode']):
                failed = Path(str(archived)+'.failed.'+uuid.uuid4().hex)
                os.replace(archived,failed)
        receipt = Path(str(archived)+'.archive_receipt.json')
        expected_receipt = attempt.get('receipt_content_sha256')
        if expected_receipt and receipt.is_file() and not receipt.is_symlink():
            before = file_identity(receipt.stat())
            if before != attempt.get('previous_receipt_identity') and before['size'] <= 1024*1024:
                descriptor=os.open(receipt,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
                with os.fdopen(descriptor,'rb') as stream:
                    opened=os.fstat(stream.fileno())
                    if not stat_module.S_ISREG(opened.st_mode) or file_identity(opened)!=before:
                        raise ValueError('archive_failure_receipt_changed_before_read')
                    raw=stream.read(1024*1024+1)
                    if file_identity(os.fstat(stream.fileno()))!=before:
                        raise ValueError('archive_failure_receipt_changed_during_read')
                try:
                    from src.engine.scalping.micro_reversion.economic_reference import content_sha256
                    body=json.loads(raw)
                    owned=(isinstance(body,dict) and content_sha256(body)==expected_receipt
                           and file_identity(receipt.stat())==before)
                except (ValueError,TypeError):owned=False
                if owned:
                    os.replace(receipt,Path(str(receipt)+'.failed.'+uuid.uuid4().hex))
        raise


def _gzip_file_unchecked(path: Path, *, dry_run: bool, custody=None, _attempt=None) -> tuple[bool, int]:
    """Return (compressed, saved_bytes_estimate)."""
    if not path.exists() or not path.is_file():
        return False, 0
    gz_path = Path(f"{path}.gz")
    snapshot = path.parent == MONITOR_SNAPSHOT_DIR and path.suffix == '.json'
    existing_archive = gz_path.exists()
    if existing_archive and not snapshot:
        return False, 0
    from src.engine.lifecycle.snapshot_archive import file_identity
    if path.is_symlink() or gz_path.is_symlink() or any(p.is_symlink() for p in path.parents):
        raise ValueError('archive_source_path_invalid')
    original_identity = file_identity(path.stat())
    archive_identity = file_identity(gz_path.stat()) if existing_archive else None
    receipt_path = Path(str(gz_path)+'.archive_receipt.json')
    if not existing_archive and (receipt_path.exists() or receipt_path.is_symlink()):
        raise ValueError('archive_orphan_receipt_preserved')
    if _attempt is not None:
        _attempt['previous_receipt_identity'] = file_identity(receipt_path.stat()) if receipt_path.is_file() else None
    original_size = original_identity['size']
    if dry_run:
        return True, original_size
    tmp_path = Path(f"{gz_path}.tmp")
    logical_digest = hashlib.sha256()
    if existing_archive:
        with path.open('rb') as src:
            logical_digest = hashlib.file_digest(src, 'sha256')
    else:
        with open(path, "rb") as src, gzip.open(tmp_path, "wb", compresslevel=9) as dst:
            while chunk := src.read(1024 * 1024):
                dst.write(chunk)
                logical_digest.update(chunk)
        with tmp_path.open('rb') as handle:
            os.fsync(handle.fileno())
    custody_identities = {}
    for reference in custody or []:
        custody_path = Path(reference['path'])
        before = file_identity(custody_path.stat())
        if (hashlib.sha256(custody_path.read_bytes()).hexdigest() != reference['sha256']
                or file_identity(custody_path.stat()) != before):
            tmp_path.unlink(missing_ok=True)
            raise ValueError('storage_custody_changed_during_compression')
        custody_identities[custody_path] = before
    if not existing_archive:
        owned_identity=file_identity(tmp_path.stat())
        if _attempt is not None:
            _attempt['archive_identity']=owned_identity
        os.replace(tmp_path, gz_path)
    restored_size = 0
    restored_digest = hashlib.sha256()
    # Verify the final inode after rename. Rename changes ctime, so validating
    # a temporary then sealing a later ctime could bind an intervening rewrite.
    checked_archive = gz_path
    checked_identity = file_identity(checked_archive.stat())
    if not existing_archive and any(checked_identity[key]!=owned_identity[key] for key in ('device','inode')):
        raise ValueError('archive_foreign_generation_after_rename')
    descriptor=os.open(checked_archive,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
    with os.fdopen(descriptor,'rb') as raw_archive,gzip.GzipFile(fileobj=raw_archive,mode='rb') as archived:
        if (not stat_module.S_ISREG(os.fstat(raw_archive.fileno()).st_mode)
                or file_identity(os.fstat(raw_archive.fileno())) != checked_identity):
            raise ValueError('archive_generation_changed_before_crc')
        while chunk := archived.read(1024 * 1024):
            restored_size += len(chunk)
            if restored_size > original_size:
                raise ValueError('archive_decoded_size_mismatch')
            restored_digest.update(chunk)
        if file_identity(os.fstat(archived.fileno())) != checked_identity:
            raise ValueError('archive_generation_changed_during_crc')
    if (
        restored_size != original_size
        or restored_digest.digest() != logical_digest.digest()
        or file_identity(path.stat()) != original_identity
        or file_identity(checked_archive.stat()) != checked_identity
        or (existing_archive and file_identity(gz_path.stat()) != archive_identity)
    ):
        tmp_path.unlink(missing_ok=True)
        raise OSError(f"gzip_size_mismatch:{path.name}:{restored_size}/{original_size}")
    for custody_path,before in custody_identities.items():
        if file_identity(custody_path.stat()) != before:
            raise ValueError('storage_custody_changed_during_compression')
    published_identity = file_identity(gz_path.stat())
    if published_identity != checked_identity:
        raise ValueError('archive_generation_changed_before_receipt')
    if snapshot:
        from src.engine.lifecycle.snapshot_archive import SCHEMA
        from src.engine.scalping.micro_reversion.economic_reference import content_sha256
        with gz_path.open('rb') as handle:
            archive_sha = hashlib.file_digest(handle, 'sha256').hexdigest()
        archive_receipt=dict(
            schema=SCHEMA, logical_path=str(path),
            logical_content_sha256=logical_digest.hexdigest(),
            logical_size_bytes=original_size, original_identity=original_identity,
            archive_generation=file_identity(gz_path.stat()), archive_sha256=archive_sha,
            runtime_effect=False, allowed_runtime_apply=False)
        if _attempt is not None:
            _attempt['receipt_content_sha256']=content_sha256(archive_receipt)
        write_json_object_generation_safe(
            Path(f'{gz_path}.archive_receipt.json'),archive_receipt)
    if path.name.startswith("pipeline_events_") and path.suffix == ".jsonl":
        from src.engine.scalping.micro_reversion.economic_reference import content_sha256
        stat = gz_path.stat()
        if file_identity(stat) != published_identity:
            raise ValueError('archive_generation_changed_before_receipt')
        archive_receipt = {
            "schema": "pipeline_raw_archive_identity_v1",
            "logical_path": str(path),
            "logical_content_sha256": logical_digest.hexdigest(),
            "logical_size_bytes": original_size,
            "storage_custody": custody or [],
            "storage_disposition": "verified_gzip_representation_original_receipts_preserved",
            "archive_generation": {
                "device": stat.st_dev, "inode": stat.st_ino,
                "size_bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns,
                "ctime_ns": stat.st_ctime_ns,
            },
            "verification_contract": "logical_sha256_size_crc_to_eof_v1",
            "runtime_effect": False, "allowed_runtime_apply": False,
        }
        archive_receipt['artifact_content_sha256'] = content_sha256(archive_receipt)
        if _attempt is not None:
            _attempt['receipt_content_sha256'] = content_sha256(archive_receipt)
        write_json_object_generation_safe(
            Path(f"{gz_path}.archive_receipt.json"),
            archive_receipt,
        )
    if file_identity(gz_path.stat()) != published_identity:
        raise ValueError('archive_generation_changed_before_removal')
    if file_identity(path.stat()) != original_identity:
        raise ValueError('archive_source_changed_before_removal')
    path.unlink()
    return True, original_size - published_identity['size']


def _gzip_file_with_jsonl_generation_lock(
    path: Path, *, dry_run: bool, custody=None
) -> tuple[bool, int]:
    """Compact one JSONL generation without racing strict replay readers."""

    with jsonl_artifact_generation_lock(path, exclusive=True):
        return _gzip_file(path, dry_run=dry_run, custody=custody)


def _gzip_jsonl_file_unlocked(
    path: Path,
    *,
    dry_run: bool,
    expected_schema: str | None = None,
    expected_row_count: int | None = None,
) -> tuple[bool, int, int]:
    """Validate JSONL while streaming it into an atomic gzip archive."""
    if not path.exists() or not path.is_file():
        return False, 0, 0
    gz_path = Path(f"{path}.gz")
    if gz_path.exists():
        return False, 0, 0
    original_size = path.stat().st_size
    row_count = 0
    tmp_path = Path(f"{gz_path}.tmp")
    destination = None
    try:
        if not dry_run:
            destination = gzip.open(tmp_path, "wb", compresslevel=9)
        with path.open("rb") as source:
            for raw_line in source:
                stripped = raw_line.strip()
                if not stripped:
                    if destination is not None:
                        destination.write(raw_line)
                    continue
                payload = json.loads(stripped)
                if not isinstance(payload, dict):
                    raise ValueError("non_object_jsonl_row")
                if expected_schema and payload.get("schema") != expected_schema:
                    raise ValueError("unexpected_jsonl_schema")
                row_count += 1
                if destination is not None:
                    destination.write(raw_line)
        if row_count <= 0:
            raise ValueError("empty_jsonl")
        if expected_row_count is not None and row_count != expected_row_count:
            raise ValueError(
                f"jsonl_row_count_mismatch:{row_count}/{expected_row_count}"
            )
        if destination is not None:
            destination.close()
            destination = None
            with gzip.open(tmp_path, "rb") as archived:
                while archived.read(1024 * 1024):
                    pass
            os.replace(tmp_path, gz_path)
            path.unlink()
        return True, original_size, row_count
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise
    finally:
        if destination is not None:
            destination.close()


def _gzip_jsonl_file(
    path: Path,
    *,
    dry_run: bool,
    expected_schema: str | None = None,
    expected_row_count: int | None = None,
) -> tuple[bool, int, int]:
    """Validate and compact JSONL under its exclusive generation lease."""

    with jsonl_artifact_generation_lock(path, exclusive=True):
        return _gzip_jsonl_file_unlocked(
            path,
            dry_run=dry_run,
            expected_schema=expected_schema,
            expected_row_count=expected_row_count,
        )



def _postclose_source_protection(target_date: date, today: date) -> str | None:
    """Keep native source representations until handoff and policy-day expiry."""
    if target_date >= today:
        return 'current_or_future_source_date'
    day = target_date.isoformat()
    status_path = POSTCLOSE_STATUS_DIR / f"threshold_cycle_postclose_{day}.status.json"
    if not status_path.exists() and not status_path.is_symlink():
        return None  # Legacy files without a native postclose owner retain their contract.
    try:
        if status_path.is_symlink() or status_path.stat().st_size > 1024 * 1024:
            return 'postclose_status_untrusted'
        status = json.loads(status_path.read_text(encoding='utf-8'))
        if not isinstance(status, dict) or status.get('target_date') != day:
            return 'postclose_status_invalid'
        if (status.get('status') != 'succeeded'
                or type(status.get('exit_code')) is not int
                or status.get('exit_code') != 0):
            return 'postclose_native_not_closed'
        from src.utils.market_day import is_krx_trading_day
        candidate = target_date
        for _ in range(14):
            candidate += timedelta(days=1)
            if is_krx_trading_day(candidate):
                break
        else:
            return 'postclose_next_policy_day_unresolved'
        if today <= candidate:
            return f'postclose_policy_day_not_elapsed:{candidate.isoformat()}'
        controller_path = POSTCLOSE_CONTROLLER_DIR / f'postclose_done_controller_{day}.json'
        if controller_path.is_symlink() or controller_path.stat().st_size > 1024 * 1024:
            return 'postclose_controller_untrusted'
        controller = json.loads(controller_path.read_text(encoding='utf-8'))
        if (not isinstance(controller, dict) or controller.get('date') != day
                or controller.get('status') != 'done'
                or controller.get('whole_native_chain_done_claimed') is not True):
            return 'postclose_controller_not_closed'
        from src.engine.automation.postclose_done_controller import done_terminal_receipt_issues
        issues = done_terminal_receipt_issues(controller_path, day, started_after_ns=0,
                                             generation_only=True)
        if ('strict_checklist_generation_stale' in issues and set(issues) <= {
                'strict_checklist_generation_stale', 'strict_generation_changed_during_recheck'}):
            # Archival custody may bind the original bytes after the policy
            # day. Never reseal a historical PASS against today's checklist.
            strict_path = Path(str(controller.get('verification_attempt_path') or ''))
            if strict_path.is_symlink() or strict_path.stat().st_size > 8*1024*1024:
                return 'postclose_historical_strict_untrusted'
            raw = strict_path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != controller.get('verification_attempt_sha256'):
                return 'postclose_historical_strict_changed'
            sha = (json.loads(raw).get('generation_binding') or {}).get('checklist_sha256')
            if not isinstance(sha, str) or not re.fullmatch('[0-9a-f]{64}', sha):
                return 'postclose_historical_checklist_identity_missing'
            snapshot = DATA_DIR / 'runtime/policy_bootstrap/historical_checklists' / (sha + '.md')
            if (snapshot.is_symlink() or snapshot.stat().st_size > 8*1024*1024
                    or hashlib.sha256(snapshot.read_bytes()).hexdigest() != sha):
                return 'postclose_historical_checklist_unverified'
            issues = done_terminal_receipt_issues(controller_path, day, started_after_ns=0,
                                                  generation_only=True, checklist_snapshot=snapshot)
        if issues:
            return 'postclose_controller_receipt_invalid'
    except (OSError, ValueError, TypeError):
        return 'postclose_custody_receipt_missing_or_invalid'
    return None

def _storage_custody(target_date):
    """References only; the preceding native gate owns their validity."""
    path = POSTCLOSE_CONTROLLER_DIR / f'postclose_done_controller_{target_date}.json'
    if not path.exists(): return []
    raw = path.read_bytes(); controller = json.loads(raw)
    strict = Path(controller['verification_attempt_path']); strict_raw = strict.read_bytes()
    sha = json.loads(strict_raw)['generation_binding']['checklist_sha256']
    snapshot = DATA_DIR / 'runtime/policy_bootstrap/historical_checklists' / (sha + '.md')
    refs = [dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest()),
            dict(path=str(strict), sha256=hashlib.sha256(strict_raw).hexdigest())]
    if snapshot.exists(): refs.append(dict(path=str(snapshot),sha256=sha))
    return refs


def run(*, retention_days: int, today: date, dry_run: bool, pipeline_dates=None) -> dict:
    cutoff = today - timedelta(days=retention_days)
    stats = {
        "cutoff": cutoff.isoformat(),
        "pipeline": {"scanned": 0, "verified": 0, "compressed": 0, "saved_bytes": 0},
        "snapshots": {"scanned": 0, "verified": 0, "compressed": 0, "saved_bytes": 0},
        "threshold_snapshots": {
            "scanned": 0,
            "verified": 0,
            "compressed": 0,
            "saved_bytes": 0,
        },
        "canonical_context": {
            "scanned": 0,
            "verified": 0,
            "compressed": 0,
            "saved_bytes": 0,
            "rows": 0,
        },
        "pipeline_summaries": {
            "scanned": 0,
            "verified": 0,
            "compressed": 0,
            "saved_bytes": 0,
            "rows": 0,
        },
        "threshold_partitions": {
            "scanned": 0,
            "verified": 0,
            "compressed": 0,
            "saved_bytes": 0,
            "rows": 0,
        },
        "skipped_unverified": 0,
        "retained_holding_policy_source_count": 0,
        "retained_trade_window_source_count": 0,
        "skipped_postclose_protected": 0,
        "postclose_protection_reasons": {},
        "errors": [],
    }

    protection_cache = {}
    def protected(target_date):
        if target_date not in protection_cache:
            protection_cache[target_date] = _postclose_source_protection(target_date, today)
        reason = protection_cache[target_date]
        if reason:
            stats['skipped_postclose_protected'] += 1
            stats['postclose_protection_reasons'][target_date.isoformat()] = reason
        return bool(reason)

    # pipeline_events_*.jsonl only (already compressed .gz excluded)
    for path in sorted(PIPELINE_EVENTS_DIR.glob("pipeline_events_*.jsonl")):
        target_date = _date_from_pipeline_file(path)
        if target_date is None or target_date > cutoff:
            continue
        if pipeline_dates is not None and target_date not in pipeline_dates:
            continue
        if protected(target_date):
            continue
        stats["pipeline"]["scanned"] += 1
        try:
            verified = _parquet_partition_exists("pipeline_events", target_date)
            if not verified:
                stats["skipped_unverified"] += 1
                continue
            stats["pipeline"]["verified"] += 1
            compressed, saved = _gzip_file_with_jsonl_generation_lock(
                path, dry_run=dry_run, custody=_storage_custody(target_date)
            )
            if compressed:
                stats["pipeline"]["compressed"] += 1
                stats["pipeline"]["saved_bytes"] += saved
        except Exception as exc:
            stats["errors"].append(f"pipeline:{path.name}:{exc}")

    if pipeline_dates is not None:
        return stats

    # monitor snapshot *.json only (already compressed .gz excluded)
    for path in sorted(MONITOR_SNAPSHOT_DIR.glob("*_*.json")):
        parsed = _kind_and_date_from_snapshot_file(path)
        if parsed is None:
            continue
        kind, target_date = parsed
        if target_date > cutoff:
            continue
        if protected(target_date):
            continue
        stats["snapshots"]["scanned"] += 1
        try:
            manifest_verified = _snapshot_manifest_verifies(kind, target_date)
            content_valid = _snapshot_json_boundary_valid(path)
            verified = manifest_verified and content_valid
            if not verified:
                stats["skipped_unverified"] += 1
                if manifest_verified and not content_valid:
                    stats["errors"].append(
                        f"snapshot:{path.name}:invalid_json_boundary_not_compressed"
                    )
                continue
            stats["snapshots"]["verified"] += 1
            compressed, saved = _gzip_file(path, dry_run=dry_run)
            if compressed:
                stats["snapshots"]["compressed"] += 1
                stats["snapshots"]["saved_bytes"] += saved
            if kind == 'trade_review':
                sidecar = path.with_suffix('.completed_projection.json')
                if sidecar.is_file():
                    # Keep the small producer dependency receipt plain; its
                    # projection bytes retain the same logical generation.
                    compressed, saved = _gzip_file(sidecar, dry_run=dry_run)
                    if compressed:
                        stats['snapshots']['compressed'] += 1
                        stats['snapshots']['saved_bytes'] += saved
        except Exception as exc:
            stats["errors"].append(f"snapshot:{path.name}:{exc}")

    # threshold-cycle immutable source snapshots (already compressed .gz excluded)
    for path in sorted(THRESHOLD_SNAPSHOT_DIR.glob("pipeline_events_*.jsonl")):
        target_date = _date_from_threshold_snapshot_file(path)
        if target_date is None or target_date > cutoff:
            continue
        if protected(target_date):
            continue
        stats["threshold_snapshots"]["scanned"] += 1
        try:
            if not _threshold_backfill_exists(target_date):
                stats["skipped_unverified"] += 1
                continue
            stats["threshold_snapshots"]["verified"] += 1
            compressed, saved = _gzip_file_with_jsonl_generation_lock(
                path, dry_run=dry_run
            )
            if compressed:
                stats["threshold_snapshots"]["compressed"] += 1
                stats["threshold_snapshots"]["saved_bytes"] += saved
        except Exception as exc:
            stats["errors"].append(f"threshold_snapshot:{path.name}:{exc}")

    canonical_cutoff = today - timedelta(
        days=max(retention_days, CANONICAL_CONTEXT_MIN_AGE_DAYS)
    )
    for path in sorted(
        CANONICAL_CONTEXT_DIR.glob("ai_canonical_context_candidates_*.jsonl")
    ):
        target_date = _date_from_named_file(path, "ai_canonical_context_candidates_")
        if target_date is None or target_date > canonical_cutoff:
            continue
        if protected(target_date):
            continue
        stats["canonical_context"]["scanned"] += 1
        try:
            compressed, saved, rows = _gzip_jsonl_file(
                path,
                dry_run=dry_run,
                expected_schema="ai_canonical_context_candidate_v1",
            )
            stats["canonical_context"]["verified"] += 1
            stats["canonical_context"]["rows"] += rows
            if compressed:
                stats["canonical_context"]["compressed"] += 1
                stats["canonical_context"]["saved_bytes"] += saved
        except Exception as exc:
            stats["errors"].append(f"canonical_context:{path.name}:{exc}")

    summary_cutoff = today - timedelta(
        days=max(retention_days, PIPELINE_SUMMARY_MIN_AGE_DAYS)
    )
    summary_contracts = (
        ("pipeline_event_summary_", "pipeline_event_summary_manifest_"),
        (
            "pipeline_event_summary_producer_parity_",
            "pipeline_event_summary_producer_parity_manifest_",
        ),
        (
            "pipeline_event_producer_summary_",
            "pipeline_event_producer_summary_manifest_",
        ),
    )
    for filename_prefix, manifest_prefix in summary_contracts:
        for path in sorted(PIPELINE_SUMMARY_DIR.glob(f"{filename_prefix}*.jsonl")):
            target_date = _date_from_named_file(path, filename_prefix)
            if target_date is None or target_date > summary_cutoff:
                continue
            if protected(target_date):
                continue
            stats["pipeline_summaries"]["scanned"] += 1
            try:
                expected_rows = _summary_manifest_expected_rows(
                    path, target_date, manifest_prefix=manifest_prefix
                )
                if expected_rows is None:
                    stats["skipped_unverified"] += 1
                    continue
                compressed, saved, rows = _gzip_jsonl_file(
                    path,
                    dry_run=dry_run,
                    expected_row_count=expected_rows,
                )
                stats["pipeline_summaries"]["verified"] += 1
                stats["pipeline_summaries"]["rows"] += rows
                if compressed:
                    stats["pipeline_summaries"]["compressed"] += 1
                    stats["pipeline_summaries"]["saved_bytes"] += saved
            except Exception as exc:
                stats["errors"].append(f"pipeline_summary:{path.name}:{exc}")

    partition_cutoff = today - timedelta(
        days=max(retention_days, THRESHOLD_PARTITION_MIN_AGE_DAYS)
    )
    for date_dir in sorted(THRESHOLD_CYCLE_DIR.glob("date=????-??-??")):
        target_date = _parse_iso_date(date_dir.name.replace("date=", "", 1))
        if target_date is None or target_date > partition_cutoff:
            continue
        if protected(target_date):
            continue
        paths = sorted(date_dir.glob("family=*/part-*.jsonl"))
        stats["threshold_partitions"]["scanned"] += len(paths)
        if not paths:
            continue
        checkpoint = _threshold_checkpoint(target_date)
        if not checkpoint.get("completed"):
            stats["skipped_unverified"] += len(paths)
            continue
        for path in paths:
            try:
                expected_rows = _threshold_partition_expected_rows(checkpoint, path)
                if expected_rows is None:
                    stats["skipped_unverified"] += 1
                    continue
                compressed, saved, rows = _gzip_jsonl_file(
                    path,
                    dry_run=dry_run,
                    expected_row_count=expected_rows,
                )
                stats["threshold_partitions"]["verified"] += 1
                stats["threshold_partitions"]["rows"] += rows
                if compressed:
                    stats["threshold_partitions"]["compressed"] += 1
                    stats["threshold_partitions"]["saved_bytes"] += saved
            except Exception as exc:
                stats["errors"].append(f"threshold_partition:{path}:{exc}")
    return stats


def _format_bytes(num: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(num)
    idx = 0
    while value >= 1024.0 and idx < len(units) - 1:
        value /= 1024.0
        idx += 1
    return f"{value:.1f}{units[idx]}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compress dashboard raw files only after canonical file/parquet verification and D+N age.",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=1,
        help="Compress files with date <= today - days (default: 1)",
    )
    parser.add_argument(
        "--date", dest="today", default=None, help="Override today date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Scan and verify only; do not compress"
    )
    parser.add_argument('--pipeline-date', action='append', type=date.fromisoformat,
                        help='Limit storage repair to these pipeline dates; preserve other families')
    args = parser.parse_args()

    if args.days < 0:
        print("[DASHBOARD_ARCHIVE_ERROR] --days must be >= 0")
        return 2

    today = _parse_iso_date(args.today) if args.today else date.today()
    if today is None:
        print(f"[DASHBOARD_ARCHIVE_ERROR] invalid --date: {args.today}")
        return 2

    stats = run(retention_days=args.days, today=today, dry_run=args.dry_run,
                pipeline_dates=set(args.pipeline_date) if args.pipeline_date else None)
    mode = "DRY_RUN" if args.dry_run else "RUN"
    print(f"[DASHBOARD_ARCHIVE_{mode}] cutoff={stats['cutoff']}")
    if stats.get('skipped_postclose_protected'):
        print('[DASHBOARD_ARCHIVE_POSTCLOSE_PROTECTED] ' + json.dumps({
            'count': stats['skipped_postclose_protected'],
            'reasons': stats['postclose_protection_reasons'],
        }, sort_keys=True))
    print(
        "[DASHBOARD_ARCHIVE_PIPELINE] "
        f"scanned={stats['pipeline']['scanned']} "
        f"verified={stats['pipeline']['verified']} "
        f"compressed={stats['pipeline']['compressed']} "
        f"saved_bytes={stats['pipeline']['saved_bytes']}({_format_bytes(stats['pipeline']['saved_bytes'])})"
    )
    print(
        "[DASHBOARD_ARCHIVE_SNAPSHOTS] "
        f"scanned={stats['snapshots']['scanned']} "
        f"verified={stats['snapshots']['verified']} "
        f"compressed={stats['snapshots']['compressed']} "
        f"saved_bytes={stats['snapshots']['saved_bytes']}({_format_bytes(stats['snapshots']['saved_bytes'])})"
    )
    print(
        "[DASHBOARD_ARCHIVE_THRESHOLD_SNAPSHOTS] "
        f"scanned={stats['threshold_snapshots']['scanned']} "
        f"verified={stats['threshold_snapshots']['verified']} "
        f"compressed={stats['threshold_snapshots']['compressed']} "
        f"saved_bytes={stats['threshold_snapshots']['saved_bytes']}({_format_bytes(stats['threshold_snapshots']['saved_bytes'])})"
    )
    for key, label in (
        ("canonical_context", "CANONICAL_CONTEXT"),
        ("pipeline_summaries", "PIPELINE_SUMMARIES"),
        ("threshold_partitions", "THRESHOLD_PARTITIONS"),
    ):
        item = stats[key]
        print(
            f"[DASHBOARD_ARCHIVE_{label}] "
            f"scanned={item['scanned']} verified={item['verified']} "
            f"compressed={item['compressed']} rows={item['rows']} "
            f"saved_bytes={item['saved_bytes']}({_format_bytes(item['saved_bytes'])})"
        )
    print(f"[DASHBOARD_ARCHIVE_SKIPPED_UNVERIFIED] {stats['skipped_unverified']}")
    if stats["errors"]:
        print(f"[DASHBOARD_ARCHIVE_ERRORS] {len(stats['errors'])}")
        for item in stats["errors"][:20]:
            print(f" - {item}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

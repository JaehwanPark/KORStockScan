"""Compress raw dashboard files only after analytics ingestion is verified."""

from __future__ import annotations

import argparse
import gzip
import json
import os
from datetime import date, timedelta
from pathlib import Path

from src.utils.constants import DATA_DIR

PIPELINE_EVENTS_DIR = DATA_DIR / "pipeline_events"
CANONICAL_CONTEXT_DIR = DATA_DIR / "ai_canonical_context_candidates"
PIPELINE_SUMMARY_DIR = DATA_DIR / "pipeline_event_summaries"
MONITOR_SNAPSHOT_DIR = DATA_DIR / "report" / "monitor_snapshots"
MONITOR_SNAPSHOT_MANIFEST_DIR = MONITOR_SNAPSHOT_DIR / "manifests"
ANALYTICS_PARQUET_DIR = DATA_DIR / "analytics" / "parquet"
THRESHOLD_CYCLE_DIR = DATA_DIR / "threshold_cycle"
THRESHOLD_SNAPSHOT_DIR = THRESHOLD_CYCLE_DIR / "snapshots"
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


def _gzip_file(path: Path, *, dry_run: bool) -> tuple[bool, int]:
    """Return (compressed, saved_bytes_estimate)."""
    if not path.exists() or not path.is_file():
        return False, 0
    gz_path = Path(f"{path}.gz")
    if gz_path.exists():
        return False, 0
    original_size = path.stat().st_size
    if dry_run:
        return True, original_size
    tmp_path = Path(f"{gz_path}.tmp")
    with open(path, "rb") as src, gzip.open(tmp_path, "wb", compresslevel=9) as dst:
        while True:
            chunk = src.read(1024 * 1024)
            if not chunk:
                break
            dst.write(chunk)
    restored_size = 0
    with gzip.open(tmp_path, "rb") as archived:
        while chunk := archived.read(1024 * 1024):
            restored_size += len(chunk)
    if restored_size != original_size:
        tmp_path.unlink(missing_ok=True)
        raise OSError(f"gzip_size_mismatch:{path.name}:{restored_size}/{original_size}")
    os.replace(tmp_path, gz_path)
    path.unlink()
    return True, original_size


def _gzip_jsonl_file(
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


def run(*, retention_days: int, today: date, dry_run: bool) -> dict:
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
        "errors": [],
    }

    # pipeline_events_*.jsonl only (already compressed .gz excluded)
    for path in sorted(PIPELINE_EVENTS_DIR.glob("pipeline_events_*.jsonl")):
        target_date = _date_from_pipeline_file(path)
        if target_date is None or target_date > cutoff:
            continue
        stats["pipeline"]["scanned"] += 1
        try:
            verified = _parquet_partition_exists("pipeline_events", target_date)
            if not verified:
                stats["skipped_unverified"] += 1
                continue
            stats["pipeline"]["verified"] += 1
            compressed, saved = _gzip_file(path, dry_run=dry_run)
            if compressed:
                stats["pipeline"]["compressed"] += 1
                stats["pipeline"]["saved_bytes"] += saved
        except Exception as exc:
            stats["errors"].append(f"pipeline:{path.name}:{exc}")

    # monitor snapshot *.json only (already compressed .gz excluded)
    for path in sorted(MONITOR_SNAPSHOT_DIR.glob("*_*.json")):
        parsed = _kind_and_date_from_snapshot_file(path)
        if parsed is None:
            continue
        kind, target_date = parsed
        if target_date > cutoff:
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
        except Exception as exc:
            stats["errors"].append(f"snapshot:{path.name}:{exc}")

    # threshold-cycle immutable source snapshots (already compressed .gz excluded)
    for path in sorted(THRESHOLD_SNAPSHOT_DIR.glob("pipeline_events_*.jsonl")):
        target_date = _date_from_threshold_snapshot_file(path)
        if target_date is None or target_date > cutoff:
            continue
        stats["threshold_snapshots"]["scanned"] += 1
        try:
            if not _threshold_backfill_exists(target_date):
                stats["skipped_unverified"] += 1
                continue
            stats["threshold_snapshots"]["verified"] += 1
            compressed, saved = _gzip_file(path, dry_run=dry_run)
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
    args = parser.parse_args()

    if args.days < 0:
        print("[DASHBOARD_ARCHIVE_ERROR] --days must be >= 0")
        return 2

    today = _parse_iso_date(args.today) if args.today else date.today()
    if today is None:
        print(f"[DASHBOARD_ARCHIVE_ERROR] invalid --date: {args.today}")
        return 2

    stats = run(retention_days=args.days, today=today, dry_run=args.dry_run)
    mode = "DRY_RUN" if args.dry_run else "RUN"
    print(f"[DASHBOARD_ARCHIVE_{mode}] cutoff={stats['cutoff']}")
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

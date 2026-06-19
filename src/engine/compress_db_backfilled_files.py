"""Compress raw dashboard files only after analytics ingestion is verified."""

from __future__ import annotations

import argparse
import gzip
import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path

from src.utils.constants import DATA_DIR


PIPELINE_EVENTS_DIR = DATA_DIR / "pipeline_events"
MONITOR_SNAPSHOT_DIR = DATA_DIR / "report" / "monitor_snapshots"
MONITOR_SNAPSHOT_MANIFEST_DIR = MONITOR_SNAPSHOT_DIR / "manifests"
ANALYTICS_PARQUET_DIR = DATA_DIR / "analytics" / "parquet"
THRESHOLD_CYCLE_DIR = DATA_DIR / "threshold_cycle"
THRESHOLD_SNAPSHOT_DIR = THRESHOLD_CYCLE_DIR / "snapshots"


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
        MONITOR_SNAPSHOT_MANIFEST_DIR.glob(f"monitor_snapshot_manifest_{target_date.isoformat()}_*.json")
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
    return partition_dir.exists() and any(partition_dir.glob("family=*/part-*.jsonl"))


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
    os.replace(tmp_path, gz_path)
    path.unlink()
    return True, original_size


def run(*, retention_days: int, today: date, dry_run: bool) -> dict:
    cutoff = today - timedelta(days=retention_days)
    stats = {
        "cutoff": cutoff.isoformat(),
        "pipeline": {"scanned": 0, "verified": 0, "compressed": 0, "saved_bytes": 0},
        "snapshots": {"scanned": 0, "verified": 0, "compressed": 0, "saved_bytes": 0},
        "threshold_snapshots": {"scanned": 0, "verified": 0, "compressed": 0, "saved_bytes": 0},
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
            verified = _snapshot_manifest_verifies(kind, target_date)
            if not verified:
                stats["skipped_unverified"] += 1
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
    parser.add_argument("--days", type=int, default=1, help="Compress files with date <= today - days (default: 1)")
    parser.add_argument("--date", dest="today", default=None, help="Override today date (YYYY-MM-DD)")
    parser.add_argument("--dry-run", action="store_true", help="Scan and verify only; do not compress")
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
    print(f"[DASHBOARD_ARCHIVE_SKIPPED_UNVERIFIED] {stats['skipped_unverified']}")
    if stats["errors"]:
        print(f"[DASHBOARD_ARCHIVE_ERRORS] {len(stats['errors'])}")
        for item in stats["errors"][:20]:
            print(f" - {item}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

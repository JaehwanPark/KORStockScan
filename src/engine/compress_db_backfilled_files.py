"""Compress raw dashboard files only after DB ingestion is verified."""

from __future__ import annotations

import argparse
import gzip
import os
from datetime import date, datetime, timedelta
from pathlib import Path

from src.engine.dashboard_data_repository import get_db_connection
from src.utils.constants import DATA_DIR


PIPELINE_EVENTS_DIR = DATA_DIR / "pipeline_events"
MONITOR_SNAPSHOT_DIR = DATA_DIR / "report" / "monitor_snapshots"


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


def _db_has_pipeline_events(conn, target_date: date) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1
            FROM dashboard_pipeline_events
            WHERE event_date = %s
            LIMIT 1
            """,
            (target_date.isoformat(),),
        )
        return cur.fetchone() is not None


def _db_has_snapshot(conn, kind: str, target_date: date) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1
            FROM dashboard_monitor_snapshots
            WHERE snapshot_kind = %s
              AND target_date = %s
            LIMIT 1
            """,
            (kind, target_date.isoformat()),
        )
        return cur.fetchone() is not None


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
        "skipped_unverified": 0,
        "errors": [],
    }

    conn = get_db_connection()
    try:
        # pipeline_events_*.jsonl only (already compressed .gz excluded)
        for path in sorted(PIPELINE_EVENTS_DIR.glob("pipeline_events_*.jsonl")):
            target_date = _date_from_pipeline_file(path)
            if target_date is None or target_date > cutoff:
                continue
            stats["pipeline"]["scanned"] += 1
            try:
                verified = _db_has_pipeline_events(conn, target_date)
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
                verified = _db_has_snapshot(conn, kind, target_date)
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
    finally:
        conn.close()
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
        description="Compress dashboard raw files only when matching DB records exist and file is D+N old.",
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
    print(f"[DASHBOARD_ARCHIVE_SKIPPED_UNVERIFIED] {stats['skipped_unverified']}")
    if stats["errors"]:
        print(f"[DASHBOARD_ARCHIVE_ERRORS] {len(stats['errors'])}")
        for item in stats["errors"][:20]:
            print(f" - {item}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

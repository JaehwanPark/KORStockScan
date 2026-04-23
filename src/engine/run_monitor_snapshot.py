"""CLI wrapper for saving monitor snapshots without cron-unfriendly inline code."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import time
from datetime import datetime
from pathlib import Path

from src.engine.log_archive_service import save_monitor_snapshots_for_date_with_profile


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Save monitor snapshots for a target date.")
    parser.add_argument(
        "--date",
        dest="target_date",
        help="Target date in YYYY-MM-DD format. Defaults to local today.",
    )
    parser.add_argument(
        "--profile",
        choices=("full", "intraday_light"),
        default=os.getenv("MONITOR_SNAPSHOT_PROFILE", "full"),
        help="Snapshot build profile. default=full",
    )
    parser.add_argument(
        "--io-delay-sec",
        dest="io_delay_sec",
        type=float,
        default=float(os.getenv("MONITOR_SNAPSHOT_IO_DELAY_SEC", "0")),
        help="Delay seconds between snapshot stages to reduce read/write burst.",
    )
    parser.add_argument(
        "--skip-server-comparison",
        action="store_true",
        default=os.getenv("MONITOR_SNAPSHOT_SKIP_SERVER_COMPARISON", "0") == "1",
        help="Skip remote server comparison artifact generation.",
    )
    parser.add_argument(
        "--lock-file",
        dest="lock_file",
        default=os.getenv("MONITOR_SNAPSHOT_LOCK_FILE", "tmp/run_monitor_snapshot.lock"),
        help="Process lock file path to prevent concurrent snapshot jobs.",
    )
    parser.add_argument(
        "--skip-lock",
        action="store_true",
        help="Skip inner process lock. Use only when an outer wrapper already holds the lock.",
    )
    return parser


def _validate_wrapper_invocation(target_date: str | None) -> int | None:
    if os.getenv("MONITOR_SNAPSHOT_FROM_WRAPPER") == "1":
        return None

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(
        json.dumps(
            {
                "target_date": target_date or "unknown",
                "status": "failed",
                "error_kind": "ForbiddenInvocation",
                "error": (
                    "run_monitor_snapshot must be executed through "
                    "deploy/run_monitor_snapshot_safe.sh"
                ),
                "profile": os.getenv("MONITOR_SNAPSHOT_PROFILE", "full"),
                "skip_server_comparison": os.getenv("MONITOR_SNAPSHOT_SKIP_SERVER_COMPARISON", "0")
                == "1",
                "skip_lock": True,
                "started_at": now,
                "finished_at": now,
                "duration_sec": 0.0,
            },
            ensure_ascii=False,
        )
    )
    return 2


def main() -> int:
    args = build_parser().parse_args()
    resolved_target_date = args.target_date
    invocation_result = _validate_wrapper_invocation(resolved_target_date)
    if invocation_result is not None:
        return invocation_result

    started_at = datetime.now()
    started_at_display = started_at.strftime("%Y-%m-%d %H:%M:%S")
    target_date = resolved_target_date or started_at.strftime("%Y-%m-%d")
    lock_path = Path(args.lock_file)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_handle = None
    status = "success"
    error_kind = ""
    error_message = ""
    result: dict[str, str] = {}
    if not args.skip_lock:
        lock_handle = open(lock_path, "a+", encoding="utf-8")
        try:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            print(
                json.dumps(
                    {
                        "target_date": target_date,
                        "status": "skipped",
                        "reason": "lock_busy",
                        "lock_file": str(lock_path),
                        "started_at": started_at_display,
                        "finished_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "duration_sec": round(time.time() - started_at.timestamp(), 3),
                    },
                    ensure_ascii=False,
                )
            )
            lock_handle.close()
            return 0
    try:
        result = save_monitor_snapshots_for_date_with_profile(
            target_date,
            profile=args.profile,
            io_delay_sec=max(0.0, float(args.io_delay_sec)),
            include_server_comparison=not args.skip_server_comparison,
        )
    except Exception as exc:
        status = "failed"
        error_kind = type(exc).__name__
        error_message = str(exc)
    finally:
        if lock_handle is not None:
            lock_handle.close()

    finished_at = datetime.now()
    print(
        json.dumps(
            {
                "target_date": target_date,
                "status": status,
                "profile": args.profile,
                "io_delay_sec": max(0.0, float(args.io_delay_sec)),
                "skip_server_comparison": bool(args.skip_server_comparison),
                "skip_lock": bool(args.skip_lock),
                "started_at": started_at_display,
                "finished_at": finished_at.strftime("%Y-%m-%d %H:%M:%S"),
                "duration_sec": round((finished_at - started_at).total_seconds(), 3),
                "error_kind": error_kind or None,
                "error": error_message or None,
                "snapshots": result if status == "success" else {},
            },
            ensure_ascii=False,
        )
    )
    return 0 if status == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""CLI wrapper for saving monitor snapshots without cron-unfriendly inline code."""

from __future__ import annotations

import argparse
import json
from datetime import datetime

from src.engine.log_archive_service import save_monitor_snapshots_for_date


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Save monitor snapshots for a target date.")
    parser.add_argument(
        "--date",
        dest="target_date",
        help="Target date in YYYY-MM-DD format. Defaults to local today.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    target_date = args.target_date or datetime.now().strftime("%Y-%m-%d")
    result = save_monitor_snapshots_for_date(target_date)
    print(json.dumps({"target_date": target_date, "snapshots": result}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Manual CLI summary for the structured daily report."""

from __future__ import annotations

import argparse
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from src.engine.daily_report_service import (
    format_daily_report_summary,
    load_or_build_daily_report,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Show the structured daily report summary."
    )
    parser.add_argument("--date", help="기준일 (YYYY-MM-DD)")
    parser.add_argument(
        "--refresh", action="store_true", help="저장된 JSON 대신 즉시 재생성"
    )
    args = parser.parse_args()

    report = load_or_build_daily_report(args.date, refresh=args.refresh)
    print(format_daily_report_summary(report))


if __name__ == "__main__":
    main()

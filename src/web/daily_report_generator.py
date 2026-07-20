"""Generate and persist the daily report JSON used by web/API surfaces."""

from __future__ import annotations

import argparse

from src.engine.daily_report_service import (
    build_daily_report,
    format_daily_report_summary,
    save_daily_report,
)


def generate_daily_report(target_date: str | None = None) -> dict:
    report = build_daily_report(target_date)
    path = save_daily_report(report)
    print(format_daily_report_summary(report))
    print(f"🎉 리포트 저장 완료: {path}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate daily KORStockScan report JSON."
    )
    parser.add_argument("--date", help="기준일 (YYYY-MM-DD). 기본값은 오늘.")
    args = parser.parse_args()
    generate_daily_report(args.date)


if __name__ == "__main__":
    main()

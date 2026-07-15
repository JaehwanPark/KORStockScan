"""Manual CLI summary for HOLDING_PIPELINE based trade review."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from src.engine.sniper_trade_review_report import (
    build_trade_review_report,
    format_trade_review_summary,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Show HOLDING/매매 복기 집계.")
    parser.add_argument("--date", help="기준일 (YYYY-MM-DD)")
    parser.add_argument("--code", help="종목코드 6자리")
    parser.add_argument(
        "--since", help="이 시각 이후 로그만 집계 (HH:MM 또는 HH:MM:SS)"
    )
    parser.add_argument("--top", type=int, default=10, help="표시할 거래 수")
    args = parser.parse_args()

    target_date = args.date or datetime.now().strftime("%Y-%m-%d")
    report = build_trade_review_report(
        target_date=target_date,
        code=args.code,
        since_time=args.since,
        top_n=max(1, int(args.top or 10)),
    )
    print(format_trade_review_summary(report))


if __name__ == "__main__":
    main()

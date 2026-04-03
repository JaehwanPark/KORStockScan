"""Entry pipeline flow summary script.

Usage:
    python3 src/tests/test_entry_pipeline_flow.py
    python3 src/tests/test_entry_pipeline_flow.py --date 2026-04-03 --since 12:25:00 --top 10
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.engine.sniper_entry_pipeline_report import build_entry_pipeline_flow_report


def main():
    parser = argparse.ArgumentParser(description="종목별 ENTRY_PIPELINE 흐름 집계")
    parser.add_argument("--date", help="집계 대상 날짜 (YYYY-MM-DD). 기본값은 오늘")
    parser.add_argument("--since", help="이 시각 이후 로그만 집계 (HH:MM 또는 HH:MM:SS)")
    parser.add_argument("--top", type=int, default=10, help="상위 사례 표시 개수")
    args = parser.parse_args()

    target_date = args.date or datetime.now().strftime("%Y-%m-%d")
    report = build_entry_pipeline_flow_report(
        target_date=target_date,
        since_time=args.since,
        top_n=max(1, args.top),
    )

    print(f"🧭 ENTRY_PIPELINE 흐름 집계 ({report['date']})")
    if report.get("since"):
        print(f"- since 필터: {report['since']}")
    print(f"- 총 이벤트: {report['metrics']['total_events']}건")
    print(f"- 추적 종목: {report['metrics']['tracked_stocks']}개")
    print(f"- 주문 제출 종목: {report['metrics']['submitted_stocks']}개")
    print(f"- 차단 종목: {report['metrics']['blocked_stocks']}개")
    print(f"- 대기 종목: {report['metrics']['waiting_stocks']}개")

    if report.get("blocker_breakdown"):
        print("- 주요 blocker:")
        for item in report["blocker_breakdown"][:5]:
            print(f"  {item['gate']}: {item['count']}개")

    if report["sections"]["recent_stocks"]:
        print("1. 최근 종목 흐름")
        for idx, row in enumerate(report["sections"]["recent_stocks"], start=1):
            passed_flow = " -> ".join(item["label"] for item in row.get("pass_flow", []))
            latest = row.get("latest_status") or {}
            print(
                f"{idx}. {row['name']}({row['code']}) "
                f"passed={passed_flow or '-'} "
                f"latest={latest.get('label', row['latest_stage'])} "
                f"reason={latest.get('reason') or '-'} "
                f"time={latest.get('timestamp', row['latest_timestamp'])}"
            )


if __name__ == "__main__":
    main()

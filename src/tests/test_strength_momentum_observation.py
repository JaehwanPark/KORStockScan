"""Strength momentum observation log summary script.

Usage:
    python3 src/tests/test_strength_momentum_observation.py
    python3 src/tests/test_strength_momentum_observation.py --date 2026-04-03 --top 20
    python3 src/tests/test_strength_momentum_observation.py --date 2026-04-03 --since 12:15:00
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.engine.sniper_strength_observation_report import (
    build_strength_momentum_report,
    format_strength_momentum_report,
)


def main():
    parser = argparse.ArgumentParser(description="동적 체결강도 관측 로그 집계")
    parser.add_argument("--date", help="집계 대상 날짜 (YYYY-MM-DD). 기본값은 오늘")
    parser.add_argument("--top", type=int, default=10, help="상위 사례 표시 개수")
    parser.add_argument(
        "--since", help="이 시각 이후 로그만 집계 (HH:MM 또는 HH:MM:SS)"
    )
    args = parser.parse_args()

    target_date = args.date or datetime.now().strftime("%Y-%m-%d")
    report = build_strength_momentum_report(
        target_date=target_date,
        top_n=max(1, args.top),
        since_time=args.since,
    )
    print(format_strength_momentum_report(report))


if __name__ == "__main__":
    main()

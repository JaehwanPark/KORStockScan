"""Gatekeeper snapshot inspection / replay helper.

Usage:
    python3 src/tests/test_gatekeeper_replay.py --date 2026-04-03 --code 095570
    python3 src/tests/test_gatekeeper_replay.py --date 2026-04-03 --code 095570 --time 19:42:11 --show-report
    python3 src/tests/test_gatekeeper_replay.py --date 2026-04-03 --code 095570 --time 19:42:11 --rerun
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.engine.sniper_gatekeeper_replay import (
    find_gatekeeper_snapshot,
    load_gatekeeper_snapshots,
    rerun_gatekeeper_snapshot,
)
from src.engine.sniper_config import CONF


def _format_snapshot(item: dict, show_report: bool = False) -> str:
    summary = item.get("ctx_summary") or {}
    lines = [
        f"🧪 Gatekeeper 스냅샷 ({item.get('signal_date')} {item.get('signal_time')})",
        f"- 종목: {item.get('stock_name')}({item.get('stock_code')}) / 전략: {item.get('strategy')}",
        f"- 판정: {item.get('action_label')} / allow={item.get('allow_entry')}",
        f"- 현재가: {summary.get('curr_price')} / 등락률: {summary.get('fluctuation')}",
        f"- VWAP 상태: {summary.get('vwap_status')}",
        f"- 미세수급: {summary.get('micro_flow_desc')}",
        f"- 잔량흐름: {summary.get('depth_flow_desc')}",
        f"- 프로그램: {summary.get('program_flow_desc')}",
        f"- WS 매수비율: {summary.get('buy_ratio_ws')} / 실행 매수비율: {summary.get('exec_buy_ratio')}",
        f"- 순간체결대금: {summary.get('tick_trade_value')} / 순매수체결량: {summary.get('net_buy_exec_volume')}",
        f"- 시가총액: {summary.get('market_cap')} / radar: {summary.get('radar_score')} ({summary.get('radar_conclusion')})",
    ]
    if show_report:
        lines.append("")
        lines.append("📄 원본 게이트키퍼 리포트")
        lines.append(item.get("report") or "(리포트 없음)")
    return "\n".join(lines)


def _rerun_snapshot(item: dict) -> str:
    result = rerun_gatekeeper_snapshot(item, conf=CONF)
    if not result.get("ok"):
        return f"⚠️ {result.get('error')}"
    return "\n".join(
        [
            "🔁 현재 프롬프트 기준 재실행",
            f"- action: {result.get('action_label')}",
            f"- allow: {result.get('allow_entry')}",
            "",
            str(result.get("report") or ""),
        ]
    )


def main():
    parser = argparse.ArgumentParser(description="저장된 Gatekeeper 스냅샷 점검")
    parser.add_argument("--date", help="대상 날짜 (YYYY-MM-DD). 기본값은 오늘")
    parser.add_argument("--code", help="종목코드 6자리")
    parser.add_argument("--time", help="목표 시각 (HH:MM 또는 HH:MM:SS)")
    parser.add_argument("--show-report", action="store_true", help="원본 리포트 전문 표시")
    parser.add_argument("--rerun", action="store_true", help="저장된 realtime_ctx로 현재 프롬프트 재실행")
    parser.add_argument("--top", type=int, default=10, help="목록 출력 개수")
    args = parser.parse_args()

    target_date = args.date or datetime.now().strftime("%Y-%m-%d")

    if args.code:
        snapshot = find_gatekeeper_snapshot(target_date, args.code, args.time)
        if not snapshot:
            print(
                f"⚠️ {target_date} / {args.code} 에 대한 Gatekeeper 스냅샷이 없습니다.\n"
                "오늘 이전 차단 건은 스냅샷 저장이 없었을 수 있습니다."
            )
            return
        print(_format_snapshot(snapshot, show_report=args.show_report))
        if args.rerun:
            print("")
            print(_rerun_snapshot(snapshot))
        return

    rows = load_gatekeeper_snapshots(target_date)
    print(f"🗂️ Gatekeeper 스냅샷 목록 ({target_date})")
    print(f"- 총 {len(rows)}건")
    if not rows:
        print("- 저장된 스냅샷이 없습니다.")
        return
    for idx, item in enumerate(rows[-max(1, args.top):], start=1):
        print(
            f"{idx}. {item.get('signal_time')} "
            f"{item.get('stock_name')}({item.get('stock_code')}) "
            f"{item.get('strategy')} -> {item.get('action_label')} "
            f"allow={item.get('allow_entry')}"
        )


if __name__ == "__main__":
    main()

"""Summaries for latency-aware entry behavior from existing log files."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from src.engine.log_archive_service import iter_target_log_lines
from src.utils.constants import LOGS_DIR


_DECISION_RE = re.compile(
    r"\[LATENCY_ENTRY_DECISION\].*?mode=(?P<mode>\w+).*?decision=(?P<decision>\w+).*?"
    r"latency=(?P<latency>\w+)"
)
_SUBMISSION_RE = re.compile(
    r"\[ENTRY_SUBMISSION_BUNDLE\].*?mode=(?P<mode>\w+).*?requested_qty=(?P<qty>\d+).*?legs=(?P<legs>\d+)"
)
_ORDER_SENT_RE = re.compile(
    r"\[LATENCY_ENTRY_ORDER_SENT\].*?tag=(?P<tag>[\w_]+).*?type=(?P<order_type>\w+).*?tif=(?P<tif>\w+)"
)
_FILL_RE = re.compile(
    r"\[ENTRY_FILL\].*?tag=(?P<tag>[\w_]+).*?fill_qty=(?P<fill_qty>\d+).*?filled=(?P<filled>\d+)/(?P<requested>\d+)"
)
_BUNDLE_FILLED_RE = re.compile(
    r"\[ENTRY_BUNDLE_FILLED\].*?mode=(?P<mode>\w+).*?filled_qty=(?P<filled>\d+)/(?P<requested>\d+)"
)
_TIF_PROMOTION_RE = re.compile(r"\[ENTRY_TIF_MAP\]")


@dataclass
class EntryMetricsSummary:
    """Compact operating summary for the current trading day."""

    date: str
    latency_counts: Counter = field(default_factory=Counter)
    decision_counts: Counter = field(default_factory=Counter)
    mode_counts: Counter = field(default_factory=Counter)
    submission_mode_counts: Counter = field(default_factory=Counter)
    order_tag_counts: Counter = field(default_factory=Counter)
    order_tif_counts: Counter = field(default_factory=Counter)
    order_type_counts: Counter = field(default_factory=Counter)
    fill_tag_counts: Counter = field(default_factory=Counter)
    bundle_filled_mode_counts: Counter = field(default_factory=Counter)
    tif_promotions: int = 0

    @property
    def fallback_activation_count(self) -> int:
        return int(self.submission_mode_counts.get("fallback", 0))

    @property
    def normal_activation_count(self) -> int:
        return int(self.submission_mode_counts.get("normal", 0))


def _iter_today_lines(log_path: Path, *, target_date: str) -> list[str]:
    return iter_target_log_lines([log_path], target_date=target_date)


def summarize_today_entry_metrics(now: datetime | None = None) -> EntryMetricsSummary:
    current = now or datetime.now()
    target_date = current.strftime("%Y-%m-%d")
    summary = EntryMetricsSummary(date=target_date)

    decision_lines = _iter_today_lines(LOGS_DIR / "sniper_state_handlers_info.log", target_date=target_date)
    fill_lines = _iter_today_lines(LOGS_DIR / "sniper_execution_receipts_info.log", target_date=target_date)
    tif_lines = _iter_today_lines(LOGS_DIR / "kiwoom_orders_info.log", target_date=target_date)

    for line in decision_lines:
        if match := _DECISION_RE.search(line):
            summary.mode_counts.update([match.group("mode").lower()])
            summary.decision_counts.update([match.group("decision").upper()])
            summary.latency_counts.update([match.group("latency").upper()])
        if match := _SUBMISSION_RE.search(line):
            summary.submission_mode_counts.update([match.group("mode").lower()])
        if match := _ORDER_SENT_RE.search(line):
            summary.order_tag_counts.update([match.group("tag").lower()])
            summary.order_tif_counts.update([match.group("tif").upper()])
            summary.order_type_counts.update([match.group("order_type").upper()])

    for line in fill_lines:
        if match := _FILL_RE.search(line):
            summary.fill_tag_counts.update([match.group("tag").lower()])
        if match := _BUNDLE_FILLED_RE.search(line):
            summary.bundle_filled_mode_counts.update([match.group("mode").lower()])

    for line in tif_lines:
        if _TIF_PROMOTION_RE.search(line):
            summary.tif_promotions += 1

    return summary


def _extract_display_values(summary: EntryMetricsSummary) -> dict[str, int | str]:
    safe = summary.latency_counts.get("SAFE", 0)
    caution = summary.latency_counts.get("CAUTION", 0)
    danger = summary.latency_counts.get("DANGER", 0)
    normal = summary.normal_activation_count
    fallback = summary.fallback_activation_count
    scout_sent = summary.order_tag_counts.get("fallback_scout", 0)
    main_sent = summary.order_tag_counts.get("fallback_main", 0)
    scout_fill = summary.fill_tag_counts.get("fallback_scout", 0)
    main_fill = summary.fill_tag_counts.get("fallback_main", 0)
    fallback_filled = summary.bundle_filled_mode_counts.get("fallback", 0)
    order_types = ", ".join(
        f"{order_type} {count}건"
        for order_type, count in sorted(summary.order_type_counts.items())
    ) or "없음"
    tif_usage = ", ".join(
        f"{tif} {count}건"
        for tif, count in sorted(summary.order_tif_counts.items())
    ) or "없음"

    return {
        "safe": safe,
        "caution": caution,
        "danger": danger,
        "normal": normal,
        "fallback": fallback,
        "scout_sent": scout_sent,
        "main_sent": main_sent,
        "scout_fill": scout_fill,
        "main_fill": main_fill,
        "fallback_filled": fallback_filled,
        "order_types": order_types,
        "tif_usage": tif_usage,
        "tif_promotions": summary.tif_promotions,
    }


def format_entry_metrics_summary_compact(summary: EntryMetricsSummary) -> str:
    """Render a compact intraday summary for manual admin lookups."""

    values = _extract_display_values(summary)
    return (
        f"📊 장중 진입 지표 ({summary.date})\n"
        f"- 지연 판정: SAFE {values['safe']}건 / CAUTION {values['caution']}건 / DANGER {values['danger']}건\n"
        f"- 진입 방식: 일반 {values['normal']}건 / fallback {values['fallback']}건\n"
        f"- fallback 진행: 정찰병 전송 {values['scout_sent']}건, 본대 전송 {values['main_sent']}건\n"
        f"- fallback 체결: 정찰병 {values['scout_fill']}건, 본대 {values['main_fill']}건, 완전체결 {values['fallback_filled']}건\n"
        f"- 주문 참고: 타입 {values['order_types']} / TIF {values['tif_usage']} / IOC→16 {values['tif_promotions']}건\n"
        "  SAFE=일반 진입 가능, CAUTION=fallback 검토, DANGER=신규 진입 차단"
    )


def format_entry_metrics_summary(summary: EntryMetricsSummary) -> str:
    """Render a detailed end-of-day report for admins."""

    values = _extract_display_values(summary)

    return (
        f"📊 진입 지표 요약 ({summary.date})\n"
        "\n"
        "1. 지연 상태 판정\n"
        f"- 안정 구간 `SAFE`: {values['safe']}건\n"
        "  지금 진입해도 괜찮다고 본 케이스입니다.\n"
        f"- 주의 구간 `CAUTION`: {values['caution']}건\n"
        "  약간 애매해서 정찰병+본대 fallback 대상으로 본 케이스입니다.\n"
        f"- 위험 구간 `DANGER`: {values['danger']}건\n"
        "  지연/호가 상태가 불안해서 신규 진입을 막은 케이스입니다.\n"
        "\n"
        "2. 실제 진입 방식\n"
        f"- 일반 진입 `normal`: {values['normal']}건\n"
        "  지연 상태가 안정적이라 단일 진입으로 처리한 횟수입니다.\n"
        f"- 분할 진입 `fallback`: {values['fallback']}건\n"
        "  정찰병(scout)+본대(main)로 나눠 보수적으로 진입한 횟수입니다.\n"
        "\n"
        "3. fallback 주문/체결 진행\n"
        f"- 정찰병 주문 전송: {values['scout_sent']}건\n"
        f"- 본대 주문 전송: {values['main_sent']}건\n"
        f"- 정찰병 체결: {values['scout_fill']}건\n"
        f"- 본대 체결: {values['main_fill']}건\n"
        f"- fallback 묶음 완전체결: {values['fallback_filled']}건\n"
        "  scout/main이 모두 채워져 fallback 진입이 끝난 횟수입니다.\n"
        "\n"
        "4. 주문 방식 참고\n"
        f"- 주문 타입 사용량: {values['order_types']}\n"
        f"- TIF 사용량: {values['tif_usage']}\n"
        f"- `IOC -> 16` 승격: {values['tif_promotions']}건\n"
        "  Kiwoom 제약으로 IOC 매수 요청이 최유리 IOC(16)로 변환된 횟수입니다."
    )

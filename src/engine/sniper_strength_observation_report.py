"""Structured reporting helpers for dynamic strength momentum observation logs."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.engine.log_archive_service import iter_target_log_lines
from src.utils.constants import LOGS_DIR


_ENTRY_RE = re.compile(
    r"^\[(?P<timestamp>[^\]]+)\].*?\[ENTRY_PIPELINE\] "
    r"(?P<name>.+?)\((?P<code>[^)]+)\) "
    r"stage=(?P<stage>[^\s]+)(?P<rest>.*)$"
)
_FIELD_RE = re.compile(r"(?P<key>[A-Za-z_]+)=(?P<value>[^\s]+)")


@dataclass
class MomentumEvent:
    timestamp: str
    name: str
    code: str
    stage: str
    fields: dict[str, str]
    raw_line: str


def _parse_since_datetime(target_date: str, since_time: str | None) -> datetime | None:
    if not since_time:
        return None
    candidate = str(since_time).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%H:%M:%S", "%H:%M"):
        try:
            if fmt.startswith("%Y"):
                return datetime.strptime(candidate, fmt)
            return datetime.strptime(f"{target_date} {candidate}", f"%Y-%m-%d {fmt}")
        except Exception:
            continue
    return None


def _iter_target_lines(log_path: Path, *, target_date: str) -> list[str]:
    return iter_target_log_lines([log_path], target_date=target_date, marker="[ENTRY_PIPELINE]")


def _parse_entry_event(line: str) -> MomentumEvent | None:
    match = _ENTRY_RE.match(line.strip())
    if not match:
        return None
    fields = {m.group("key"): m.group("value") for m in _FIELD_RE.finditer(match.group("rest") or "")}
    return MomentumEvent(
        timestamp=match.group("timestamp"),
        name=match.group("name"),
        code=match.group("code"),
        stage=match.group("stage"),
        fields=fields,
        raw_line=line.strip(),
    )


def _to_float(value: str | None, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(str(value).replace(",", "").strip())
    except Exception:
        return default


def _to_int(value: str | None, default: int = 0) -> int:
    if value is None:
        return default
    try:
        return int(float(str(value).replace(",", "").strip()))
    except Exception:
        return default


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"true", "1", "y", "yes"}:
        return True
    if text in {"false", "0", "n", "no"}:
        return False
    return default


def _event_to_row(event: MomentumEvent) -> dict:
    return {
        "timestamp": event.timestamp,
        "name": event.name,
        "code": event.code,
        "stage": event.stage,
        "fields": dict(event.fields),
    }


def build_strength_momentum_report(target_date: str, top_n: int = 10, since_time: str | None = None) -> dict:
    log_path = LOGS_DIR / "sniper_state_handlers_info.log"
    lines = _iter_target_lines(log_path, target_date=target_date)
    events = [event for line in lines if (event := _parse_entry_event(line))]
    since_dt = _parse_since_datetime(target_date, since_time)
    if since_dt is not None:
        filtered_events: list[MomentumEvent] = []
        for event in events:
            try:
                event_dt = datetime.strptime(event.timestamp, "%Y-%m-%d %H:%M:%S")
            except Exception:
                continue
            if event_dt >= since_dt:
                filtered_events.append(event)
        events = filtered_events

    relevant_stages = {
        "strength_momentum_observed",
        "strength_momentum_pass",
        "blocked_vpw",
        "blocked_strength_momentum",
        "dynamic_vpw_override_pass",
    }
    events = [event for event in events if event.stage in relevant_stages]

    report = {
        "date": target_date,
        "since": since_dt.strftime("%Y-%m-%d %H:%M:%S") if since_dt else None,
        "log_path": str(log_path),
        "has_data": bool(events),
        "metrics": {
            "total_events": 0,
            "observed_failures": 0,
            "observed_unique_stocks": 0,
            "passes": 0,
            "pass_unique_stocks": 0,
            "blocked_vpw": 0,
            "blocked_strength_momentum": 0,
            "dynamic_override_pass": 0,
            "dynamic_override_unique_stocks": 0,
        },
        "reason_breakdown": {
            "observed": [],
            "blocked_vpw_dynamic": [],
        },
        "sections": {
            "dynamic_override_candidates": [],
            "top_passes": [],
            "near_misses": [],
        },
    }

    if not events:
        return report

    stage_counts = Counter(event.stage for event in events)
    observed_reasons = Counter(
        event.fields.get("reason", "unknown")
        for event in events
        if event.stage == "strength_momentum_observed"
    )
    blocked_dynamic_reasons = Counter(
        event.fields.get("dynamic_reason", "unknown")
        for event in events
        if event.stage == "blocked_vpw"
    )
    pass_stocks = {(event.name, event.code) for event in events if event.stage == "strength_momentum_pass"}
    observed_stocks = {(event.name, event.code) for event in events if event.stage == "strength_momentum_observed"}

    latest_static_block_candidates: dict[tuple[str, str], MomentumEvent] = {}
    latest_pass_events: dict[tuple[str, str], MomentumEvent] = {}
    latest_observed_events: dict[tuple[str, str], MomentumEvent] = {}

    for event in events:
        key = (event.name, event.code)
        if event.stage == "dynamic_vpw_override_pass":
            latest_static_block_candidates[key] = event
        if event.stage == "blocked_vpw" and _to_bool(event.fields.get("dynamic_allowed"), False):
            latest_static_block_candidates[key] = event
        if event.stage == "strength_momentum_pass":
            latest_pass_events[key] = event
        if event.stage == "strength_momentum_observed":
            latest_observed_events[key] = event

    top_candidates = sorted(
        latest_static_block_candidates.values(),
        key=lambda event: (
            _to_float(event.fields.get("dynamic_delta"), 0.0),
            _to_int(event.fields.get("dynamic_buy_value"), 0),
        ),
        reverse=True,
    )[:top_n]

    top_passes = sorted(
        latest_pass_events.values(),
        key=lambda event: (
            _to_int(event.fields.get("buy_value"), 0),
            _to_float(event.fields.get("delta"), 0.0),
        ),
        reverse=True,
    )[:top_n]

    top_near_misses = sorted(
        (
            event for event in latest_observed_events.values()
            if event.fields.get("reason") in {
                "below_window_buy_value",
                "below_buy_ratio",
                "below_exec_buy_ratio",
                "below_strength_base",
                "insufficient_history",
                "below_target_delta",
            }
        ),
        key=lambda event: (
            _to_float(event.fields.get("delta"), 0.0),
            _to_int(event.fields.get("buy_value"), 0),
        ),
        reverse=True,
    )[:top_n]

    report["metrics"] = {
        "total_events": len(events),
        "observed_failures": stage_counts.get("strength_momentum_observed", 0),
        "observed_unique_stocks": len(observed_stocks),
        "passes": stage_counts.get("strength_momentum_pass", 0),
        "pass_unique_stocks": len(pass_stocks),
        "blocked_vpw": stage_counts.get("blocked_vpw", 0),
        "blocked_strength_momentum": stage_counts.get("blocked_strength_momentum", 0),
        "dynamic_override_pass": stage_counts.get("dynamic_vpw_override_pass", 0),
        "dynamic_override_unique_stocks": len(latest_static_block_candidates),
    }
    report["reason_breakdown"] = {
        "observed": [{"reason": reason, "count": count} for reason, count in observed_reasons.most_common(10)],
        "blocked_vpw_dynamic": [{"reason": reason, "count": count} for reason, count in blocked_dynamic_reasons.most_common(10)],
    }
    report["sections"] = {
        "dynamic_override_candidates": [_event_to_row(event) for event in top_candidates],
        "top_passes": [_event_to_row(event) for event in top_passes],
        "near_misses": [_event_to_row(event) for event in top_near_misses],
    }
    return report


def format_strength_momentum_report(report: dict) -> str:
    target_date = str(report.get("date", "") or "")
    metrics = report.get("metrics", {}) or {}
    if not report.get("has_data"):
        lines = [
            f"📈 동적 체결강도 관측 집계 ({target_date})",
            "- 관련 ENTRY_PIPELINE 로그가 없습니다.",
        ]
        if report.get("since"):
            lines.append(f"- since 필터: {report['since']}")
        lines.append(f"- 확인 파일: {report.get('log_path', '')}")
        return "\n".join(lines)

    lines_out = [
        f"📈 동적 체결강도 관측 집계 ({target_date})",
        f"- 총 관련 이벤트: {metrics.get('total_events', 0)}건",
        f"- 관측 실패 로그: {metrics.get('observed_failures', 0)}건 / 고유종목 {metrics.get('observed_unique_stocks', 0)}개",
        f"- 동적 통과 로그: {metrics.get('passes', 0)}건 / 고유종목 {metrics.get('pass_unique_stocks', 0)}개",
        f"- 정적 120 차단 로그: {metrics.get('blocked_vpw', 0)}건",
        f"- 동적 게이트 직접 차단 로그: {metrics.get('blocked_strength_momentum', 0)}건",
        f"- 정적 120 오버라이드 통과 로그: {metrics.get('dynamic_override_pass', 0)}건",
    ]
    if report.get("since"):
        lines_out.append(f"- since 필터: {report['since']}")
    lines_out.append(f"- 정적 120 구간에서 동적 통과한 후보 종목: {metrics.get('dynamic_override_unique_stocks', 0)}개")

    observed = report.get("reason_breakdown", {}).get("observed", []) or []
    if observed:
        lines_out.append(
            "- 주요 관측 실패 사유: "
            + ", ".join(f"{item['reason']} {item['count']}건" for item in observed[:5])
        )

    blocked = report.get("reason_breakdown", {}).get("blocked_vpw_dynamic", []) or []
    if blocked:
        lines_out.append(
            "- 정적 차단 시 동적 사유 분포: "
            + ", ".join(f"{item['reason']} {item['count']}건" for item in blocked[:5])
        )

    top_candidates = report.get("sections", {}).get("dynamic_override_candidates", []) or []
    if top_candidates:
        lines_out.append("")
        lines_out.append("1. 정적 120 구간에서 동적 통과한 후보")
        for idx, event in enumerate(top_candidates, start=1):
            fields = event.get("fields", {}) or {}
            delta = fields.get("dynamic_delta", fields.get("delta", "?"))
            buy_value = fields.get("dynamic_buy_value", fields.get("buy_value", "?"))
            reason = fields.get("dynamic_reason", fields.get("reason", "?"))
            lines_out.append(
                f"{idx}. {event.get('name')}({event.get('code')}) "
                f"vpw={fields.get('current_vpw', '?')} "
                f"delta={delta} "
                f"buy_value={buy_value} "
                f"reason={reason} "
                f"time={event.get('timestamp')}"
            )

    top_passes = report.get("sections", {}).get("top_passes", []) or []
    if top_passes:
        lines_out.append("")
        lines_out.append("2. 동적 게이트 통과 상위 사례")
        for idx, event in enumerate(top_passes, start=1):
            fields = event.get("fields", {}) or {}
            lines_out.append(
                f"{idx}. {event.get('name')}({event.get('code')}) "
                f"base={fields.get('base_vpw', '?')} "
                f"curr={fields.get('current_vpw', '?')} "
                f"delta={fields.get('delta', '?')} "
                f"buy_value={fields.get('buy_value', '?')} "
                f"buy_ratio={fields.get('buy_ratio', '?')} "
                f"time={event.get('timestamp')}"
            )

    near_misses = report.get("sections", {}).get("near_misses", []) or []
    if near_misses:
        lines_out.append("")
        lines_out.append("3. 튜닝 우선 검토 near-miss")
        for idx, event in enumerate(near_misses, start=1):
            fields = event.get("fields", {}) or {}
            lines_out.append(
                f"{idx}. {event.get('name')}({event.get('code')}) "
                f"reason={fields.get('reason', '?')} "
                f"delta={fields.get('delta', '?')} "
                f"buy_value={fields.get('buy_value', '?')} "
                f"buy_ratio={fields.get('buy_ratio', '?')} "
                f"time={event.get('timestamp')}"
            )

    return "\n".join(lines_out)

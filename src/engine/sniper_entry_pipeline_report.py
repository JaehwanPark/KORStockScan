"""Structured reporting helpers for entry pipeline flow logs."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.utils.constants import LOGS_DIR


_ENTRY_RE = re.compile(
    r"^\[(?P<timestamp>[^\]]+)\].*?\[ENTRY_PIPELINE\] "
    r"(?P<name>.+?)\((?P<code>[^)]+)\) "
    r"stage=(?P<stage>[^\s]+)(?P<rest>.*)$"
)
_FIELD_RE = re.compile(r"(?P<key>[A-Za-z_]+)=(?P<value>[^\s]+)")

_DISPLAY_STAGE_LABELS = {
    "watching": "감시중",
    "ai_confirmed": "AI 확답",
    "strength_momentum_pass": "동적 체결강도 통과",
    "dynamic_vpw_override_pass": "정적 120 우회",
    "entry_armed": "진입 자격 확보",
    "entry_armed_resume": "진입 자격 유지",
    "budget_pass": "수량 계산 통과",
    "latency_pass": "Latency 통과",
    "order_leg_sent": "주문 전송",
    "order_bundle_submitted": "주문 제출 완료",
    "first_ai_wait": "첫 AI 대기",
    "blocked_strength_momentum": "동적 체결강도 차단",
    "blocked_liquidity": "유동성 차단",
    "blocked_ai_score": "AI 점수 차단",
    "latency_block": "Latency 차단",
    "blocked_zero_qty": "수량 0주 차단",
    "blocked_gap_from_scan": "포착가 갭 차단",
    "blocked_overbought": "과열 차단",
    "blocked_big_bite_hard_gate": "Big-Bite 차단",
    "blocked_vpw": "정적 체결강도 차단",
}

_SUMMARY_PASS_STAGES = {
    "ai_confirmed",
    "strength_momentum_pass",
    "dynamic_vpw_override_pass",
    "entry_armed",
    "budget_pass",
    "latency_pass",
    "order_leg_sent",
    "order_bundle_submitted",
}


@dataclass
class PipelineEvent:
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
    lines: list[str] = []
    candidate_paths = [log_path]
    candidate_paths.extend(sorted(log_path.parent.glob(f"{log_path.name}.*"), key=lambda path: path.name))

    for candidate in candidate_paths:
        if not candidate.exists() or not candidate.is_file():
            continue
        with open(candidate, "r", encoding="utf-8") as handle:
            for raw_line in handle:
                if f"[{target_date}" not in raw_line:
                    continue
                if "[ENTRY_PIPELINE]" not in raw_line:
                    continue
                lines.append(raw_line.strip())
    return lines


def _parse_event(line: str) -> PipelineEvent | None:
    match = _ENTRY_RE.match(line.strip())
    if not match:
        return None
    fields = {m.group("key"): m.group("value") for m in _FIELD_RE.finditer(match.group("rest") or "")}
    return PipelineEvent(
        timestamp=match.group("timestamp"),
        name=match.group("name"),
        code=match.group("code"),
        stage=match.group("stage"),
        fields=fields,
        raw_line=line.strip(),
    )


def _event_to_row(event: PipelineEvent) -> dict:
    return {
        "timestamp": event.timestamp,
        "name": event.name,
        "code": event.code,
        "stage": event.stage,
        "fields": dict(event.fields),
    }


def _classify_stage(stage: str) -> str:
    if stage in {"order_leg_sent", "order_bundle_submitted"}:
        return "submitted"
    if stage.startswith("blocked_") or stage.endswith("_block") or stage.endswith("_failed"):
        return "blocked"
    if stage in {"first_ai_wait"}:
        return "waiting"
    return "progress"


def _friendly_gate_name(stage: str) -> str:
    mapping = {
        "blocked_strength_momentum": "동적 체결강도",
        "blocked_liquidity": "유동성",
        "blocked_ai_score": "AI 점수",
        "latency_block": "Latency",
        "blocked_zero_qty": "주문 가능 수량",
        "blocked_gap_from_scan": "포착가 대비 갭",
        "blocked_overbought": "과열",
        "blocked_big_bite_hard_gate": "Big-Bite 하드게이트",
        "blocked_vpw": "정적 체결강도",
        "first_ai_wait": "첫 AI 대기",
    }
    return mapping.get(stage, stage)


def _display_stage_label(stage: str) -> str:
    return _DISPLAY_STAGE_LABELS.get(stage, _friendly_gate_name(stage))


def _build_summary_flow(item_events: list[PipelineEvent], latest: PipelineEvent) -> list[dict]:
    summary = [{"stage": "watching", "label": _display_stage_label("watching"), "kind": "start"}]
    seen_passes: set[str] = set()

    for event in item_events:
        if event.stage in _SUMMARY_PASS_STAGES and event.stage not in seen_passes:
            summary.append({
                "stage": event.stage,
                "label": _display_stage_label(event.stage),
                "kind": "pass" if event.stage != "order_bundle_submitted" else "submitted",
            })
            seen_passes.add(event.stage)

    latest_class = _classify_stage(latest.stage)
    if latest_class == "blocked":
        summary.append({
            "stage": latest.stage,
            "label": _display_stage_label(latest.stage),
            "kind": "blocked",
        })
    elif latest_class == "waiting":
        summary.append({
            "stage": latest.stage,
            "label": _display_stage_label(latest.stage),
            "kind": "waiting",
        })
    elif latest.stage not in _SUMMARY_PASS_STAGES:
        summary.append({
            "stage": latest.stage,
            "label": _display_stage_label(latest.stage),
            "kind": "progress",
        })

    compact: list[dict] = []
    for item in summary:
        if compact and compact[-1]["stage"] == item["stage"] and compact[-1]["kind"] == item["kind"]:
            continue
        compact.append(item)
    return compact


def _build_pass_flow(item_events: list[PipelineEvent]) -> list[dict]:
    flow = [{"stage": "watching", "label": _display_stage_label("watching"), "kind": "start"}]
    seen_passes: set[str] = set()
    for event in item_events:
        if event.stage not in _SUMMARY_PASS_STAGES or event.stage in seen_passes:
            continue
        flow.append({
            "stage": event.stage,
            "label": _display_stage_label(event.stage),
            "kind": "pass" if event.stage != "order_bundle_submitted" else "submitted",
        })
        seen_passes.add(event.stage)
    return flow


def _build_latest_status(latest: PipelineEvent) -> dict:
    status_kind = _classify_stage(latest.stage)
    return {
        "stage": latest.stage,
        "label": _display_stage_label(latest.stage),
        "kind": status_kind,
        "reason": latest.fields.get("reason") or latest.fields.get("dynamic_reason") or "",
        "timestamp": latest.timestamp,
    }


def build_entry_pipeline_flow_report(target_date: str, since_time: str | None = None, top_n: int = 20) -> dict:
    log_path = LOGS_DIR / "sniper_state_handlers_info.log"
    lines = _iter_target_lines(log_path, target_date=target_date)
    events = [event for line in lines if (event := _parse_event(line))]
    since_dt = _parse_since_datetime(target_date, since_time)
    if since_dt is not None:
        filtered_events: list[PipelineEvent] = []
        for event in events:
            try:
                event_dt = datetime.strptime(event.timestamp, "%Y-%m-%d %H:%M:%S")
            except Exception:
                continue
            if event_dt >= since_dt:
                filtered_events.append(event)
        events = filtered_events

    stock_events: dict[tuple[str, str], list[PipelineEvent]] = defaultdict(list)
    for event in events:
        stock_events[(event.name, event.code)].append(event)

    per_stock_rows = []
    blocker_counts: Counter[str] = Counter()
    latest_stage_counts: Counter[str] = Counter()

    for key, item_events in stock_events.items():
        if not item_events:
            continue
        latest = item_events[-1]
        latest_stage_counts[latest.stage] += 1
        stage_class = _classify_stage(latest.stage)
        if stage_class in {"blocked", "waiting"}:
            blocker_counts[_friendly_gate_name(latest.stage)] += 1

        compact_flow = []
        for event in item_events:
            if not compact_flow or event.stage != compact_flow[-1]:
                compact_flow.append(event.stage)

        pass_flow = _build_pass_flow(item_events)
        latest_status = _build_latest_status(latest)

        per_stock_rows.append({
            "name": latest.name,
            "code": latest.code,
            "latest_timestamp": latest.timestamp,
            "latest_stage": latest.stage,
            "latest_stage_label": _display_stage_label(latest.stage),
            "stage_class": stage_class,
            "latest_reason": latest_status["reason"],
            "flow": compact_flow,
            "pass_flow": pass_flow,
            "latest_status": latest_status,
            "summary_flow": _build_summary_flow(item_events, latest),
            "events": [_event_to_row(event) for event in item_events[-min(len(item_events), 20):]],
        })

    per_stock_rows.sort(key=lambda row: row["latest_timestamp"], reverse=True)

    report = {
        "date": target_date,
        "since": since_dt.strftime("%Y-%m-%d %H:%M:%S") if since_dt else None,
        "log_path": str(log_path),
        "has_data": bool(events),
        "metrics": {
            "total_events": len(events),
            "tracked_stocks": len(stock_events),
            "submitted_stocks": sum(1 for row in per_stock_rows if row["stage_class"] == "submitted"),
            "blocked_stocks": sum(1 for row in per_stock_rows if row["stage_class"] == "blocked"),
            "waiting_stocks": sum(1 for row in per_stock_rows if row["stage_class"] == "waiting"),
        },
        "latest_stage_breakdown": [
            {"stage": stage, "count": count}
            for stage, count in latest_stage_counts.most_common(12)
        ],
        "blocker_breakdown": [
            {"gate": gate, "count": count}
            for gate, count in blocker_counts.most_common(12)
        ],
        "sections": {
            "recent_stocks": per_stock_rows[:top_n],
            "blocked_stocks": [row for row in per_stock_rows if row["stage_class"] == "blocked"][:top_n],
            "submitted_stocks": [row for row in per_stock_rows if row["stage_class"] == "submitted"][:top_n],
            "waiting_stocks": [row for row in per_stock_rows if row["stage_class"] == "waiting"][:top_n],
        },
    }
    return report

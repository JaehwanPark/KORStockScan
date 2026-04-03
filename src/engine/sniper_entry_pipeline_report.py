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
_GATEKEEPER_ACTION_RE = re.compile(
    r"\saction=(?P<action>.+?)(?:\s+cooldown_sec=|\s+cooldown_policy=|\s+gatekeeper_eval_ms=|$)"
)
_IGNORED_STOCK_KEYS = {
    ("TEST", "123456"),
}
_EXECUTION_BLOCK_STAGES = {
    "blocked_no_admin",
    "blocked_zero_qty",
    "blocked_liquidity",
    "latency_block",
    "blocked_pause",
    "order_leg_fail",
    "order_leg_no_response",
    "order_bundle_failed",
}

_DISPLAY_STAGE_LABELS = {
    "watching": "감시중",
    "ai_confirmed": "AI 확답",
    "strength_momentum_observed": "동적 체결강도 관측",
    "strength_momentum_pass": "동적 체결강도 통과",
    "dynamic_vpw_override_pass": "정적 120 우회",
    "entry_armed": "진입 자격 확보",
    "entry_armed_resume": "진입 자격 유지",
    "budget_pass": "수량 계산 통과",
    "latency_pass": "지연 리스크 통과",
    "order_leg_sent": "주문 전송",
    "order_bundle_submitted": "주문 제출 완료",
    "first_ai_wait": "첫 AI 대기",
    "blocked_strength_momentum": "동적 체결강도 차단",
    "blocked_liquidity": "유동성 차단",
    "blocked_ai_score": "AI 점수 차단",
    "latency_block": "지연 리스크 차단",
    "blocked_zero_qty": "수량 0주 차단",
    "blocked_gap_from_scan": "포착가 갭 차단",
    "blocked_overbought": "과열 차단",
    "blocked_big_bite_hard_gate": "Big-Bite 차단",
    "blocked_vpw": "정적 체결강도 차단",
    "blocked_gatekeeper_reject": "게이트키퍼 보류",
    "blocked_swing_gap": "스윙 갭상승 차단",
}

_DISPLAY_REASON_LABELS = {
    "below_window_buy_value": "단기 매수 유입 약함",
    "below_strength_base": "체결강도 베이스 부족",
    "below_buy_ratio": "매수비율 부족",
    "below_exec_buy_ratio": "체결 매수비율 부족",
    "insufficient_history": "관측 히스토리 부족",
    "below_target_delta": "체결강도 변화량 부족",
    "latency_state_danger": "지연 리스크 위험구간",
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

_CONFIRMED_FLOW_ANCHOR_STAGES = {
    "ai_confirmed",
    "entry_armed",
    "entry_armed_resume",
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
    fields = {
        m.group("key"): str(m.group("value")).replace("|", " ")
        for m in _FIELD_RE.finditer(match.group("rest") or "")
    }
    return PipelineEvent(
        timestamp=match.group("timestamp"),
        name=match.group("name"),
        code=match.group("code"),
        stage=match.group("stage"),
        fields=fields,
        raw_line=line.strip(),
    )


def _event_sort_key(event: PipelineEvent) -> tuple[datetime, str, str]:
    try:
        parsed = datetime.strptime(event.timestamp, "%Y-%m-%d %H:%M:%S")
    except Exception:
        parsed = datetime.min
    return parsed, event.name, event.stage


def _event_to_row(event: PipelineEvent) -> dict:
    return {
        "timestamp": event.timestamp,
        "name": event.name,
        "code": event.code,
        "stage": event.stage,
        "fields": dict(event.fields),
    }


def _should_ignore_event(event: PipelineEvent) -> bool:
    key = (str(event.name or "").strip().upper(), str(event.code or "").strip())
    if key in _IGNORED_STOCK_KEYS:
        return True
    if key[0] in {"TEST", "DUMMY", "MOCK"}:
        return True
    return False


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
        "latency_block": "지연 리스크",
        "blocked_zero_qty": "주문 가능 수량",
        "blocked_gap_from_scan": "포착가 대비 갭",
        "blocked_overbought": "과열",
        "blocked_big_bite_hard_gate": "Big-Bite 하드게이트",
        "blocked_vpw": "정적 체결강도",
        "blocked_gatekeeper_reject": "게이트키퍼 보류",
        "blocked_swing_gap": "스윙 갭상승",
        "first_ai_wait": "첫 AI 대기",
    }
    return mapping.get(stage, stage)


_BLOCKER_GUIDE = {
    "동적 체결강도": {
        "description": "실시간 체결대금·매수비율·체결강도 기준을 못 채운 경우",
        "check": "window_buy_value, buy_ratio, vpw base",
    },
    "유동성": {
        "description": "호가 잔량이나 거래대금이 부족해 즉시 진입 품질이 낮은 경우",
        "check": "ask/bid depth, liquidity_value",
    },
    "AI 점수": {
        "description": "실시간 AI 확답 점수가 전략 기준에 못 미친 경우",
        "check": "current_ai_score, threshold",
    },
    "지연 리스크": {
        "description": "신호 시점 대비 현재 체결 위치가 늦거나 슬리피지 위험이 큰 경우",
        "check": "latency_state, slippage, ws_age",
    },
    "주문 가능 수량": {
        "description": "예수금·비중·안전계수 적용 후 실제 주문 수량이 0주인 경우",
        "check": "deposit, ratio, safe_budget",
    },
    "포착가 대비 갭": {
        "description": "포착 시점보다 현재가가 너무 멀어져 추격 진입을 막은 경우",
        "check": "scan_price gap",
    },
    "과열": {
        "description": "급등/과열 상태로 판단되어 진입을 보류한 경우",
        "check": "fluctuation, overbought gate",
    },
    "Big-Bite 하드게이트": {
        "description": "초기 강한 매수 신호 없이 Big-Bite 진입 조건이 미충족인 경우",
        "check": "big_bite trigger/confirm",
    },
    "정적 체결강도": {
        "description": "기존 체결강도 120 하드게이트를 넘지 못한 경우",
        "check": "current_vpw vs limit",
    },
    "게이트키퍼 거부": {
        "description": "스윙 AI Gatekeeper가 수급·호가·갭·위치 정보를 종합해 즉시 진입보다 보류가 낫다고 본 경우",
        "check": "gatekeeper action, report, gap, orderbook, program flow",
    },
    "스윙 갭상승": {
        "description": "스윙 진입 기준 대비 갭상승 폭이 너무 커서 추격을 막은 경우",
        "check": "fluctuation vs max_gap",
    },
    "첫 AI 대기": {
        "description": "첫 AI 분석 턴으로 즉시 진입하지 않고 다음 확인을 기다리는 상태",
        "check": "first_ai_wait path",
    },
}

_GATEKEEPER_ACTION_GUIDE = {
    "눌림 대기": {
        "description": (
            "추세 자체를 부정한 것은 아니지만, 현재 가격 위치가 애매하거나 단기 추격 리스크가 크다고 본 경우입니다. "
            "즉시 진입 대신 눌림 재진입, VWAP/전일고점 재지지, 매도잔량 소화 확인이 필요하다는 의미에 가깝습니다."
        ),
        "check": "VWAP 재안착, 전일고점 재돌파, 매도잔량 소화, 프로그램/순매수 유지",
    },
    "전량 회피": {
        "description": (
            "현재 시점의 수급·호가·갭 구조가 불리해 스윙 진입 기대값이 낮다고 본 경우입니다. "
            "단순 타이밍 문제라기보다 공급 우위, 추격 과열, 돌파 품질 저하처럼 구조적 리스크가 커서 아예 건너뛰자는 판단입니다."
        ),
        "check": "갭 과열, 매도 우위 잔량, 프로그램 순매도, 돌파 실패/상단 매물 여부",
    },
    "둘 다 아님": {
        "description": (
            "스캘핑도 스윙도 현재 문맥상 적합하지 않다고 본 경우입니다. "
            "진입 시나리오 자체가 불명확하거나 수급 방향성이 약해 전략 우위를 만들지 못한 상태에 가깝습니다."
        ),
        "check": "전략 부합도, 수급 방향성, 위치 애매함, 추세 지속성",
    },
    "스윙 우선": {
        "description": (
            "초단기 추격보다는 스윙 관점의 눌림/재돌파 시나리오가 더 유효하다고 본 경우입니다. "
            "같은 종목이라도 진입 타임프레임을 더 길게 보라는 의미입니다."
        ),
        "check": "타임프레임 전환, 눌림 구간, 일봉 위치, 거래대금 유지",
    },
}


def _display_stage_label(stage: str) -> str:
    return _DISPLAY_STAGE_LABELS.get(stage, _friendly_gate_name(stage))


def _display_reason_label(reason: str) -> str:
    if not reason:
        return ""
    return _DISPLAY_REASON_LABELS.get(reason, reason)


def _extract_gatekeeper_action(event: PipelineEvent) -> str:
    action = str(event.fields.get("action") or "").replace("|", " ").strip()
    if action and action not in {"눌림", "전량", "둘", "스윙"}:
        return action
    match = _GATEKEEPER_ACTION_RE.search(event.raw_line or "")
    if match:
        return str(match.group("action") or "").replace("|", " ").strip()
    return action


def _extract_event_reason(event: PipelineEvent) -> str:
    if event.stage == "blocked_gatekeeper_reject":
        return _extract_gatekeeper_action(event) or event.fields.get("reason") or ""
    return event.fields.get("reason") or event.fields.get("dynamic_reason") or ""


def _friendly_blocker_name(event: PipelineEvent) -> str:
    if event.stage == "blocked_gatekeeper_reject":
        action = _extract_gatekeeper_action(event)
        if action:
            return f"게이트키퍼: {action}"
    return _friendly_gate_name(event.stage)


def _resolve_blocker_guide(gate: str) -> dict[str, str]:
    gate_text = str(gate or "").strip()
    if gate_text.startswith("게이트키퍼:"):
        action = gate_text.split(":", 1)[1].strip()
        action_guide = _GATEKEEPER_ACTION_GUIDE.get(action)
        if action_guide:
            return {
                "gate": gate_text,
                "description": action_guide["description"],
                "check": action_guide["check"],
            }
        fallback = _BLOCKER_GUIDE.get("게이트키퍼 거부", {})
        return {
            "gate": gate_text,
            "description": fallback.get("description", "운영 로그에서 상세 사유 확인 필요"),
            "check": fallback.get("check", "-"),
        }

    base = _BLOCKER_GUIDE.get(gate_text, {})
    return {
        "gate": gate_text,
        "description": base.get("description", "운영 로그에서 상세 사유 확인 필요"),
        "check": base.get("check", "-"),
    }


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
    anchor_idx = next(
        (idx for idx, event in enumerate(item_events) if event.stage in _CONFIRMED_FLOW_ANCHOR_STAGES),
        None,
    )
    if anchor_idx is None:
        return flow

    seen_passes: set[str] = set()
    for idx, event in enumerate(item_events):
        if event.stage not in _SUMMARY_PASS_STAGES or event.stage in seen_passes:
            continue
        if idx < anchor_idx and event.stage in {"strength_momentum_pass", "dynamic_vpw_override_pass"}:
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
    raw_reason = _extract_event_reason(latest)
    return {
        "stage": latest.stage,
        "label": _display_stage_label(latest.stage),
        "kind": status_kind,
        "reason": raw_reason,
        "reason_label": _display_reason_label(raw_reason),
        "timestamp": latest.timestamp,
    }


def _build_confirmed_failure(item_events: list[PipelineEvent]) -> dict | None:
    anchor_idx = next(
        (idx for idx, event in enumerate(item_events) if event.stage in _CONFIRMED_FLOW_ANCHOR_STAGES),
        None,
    )
    if anchor_idx is None:
        return None

    for event in reversed(item_events[anchor_idx:]):
        if event.stage not in _EXECUTION_BLOCK_STAGES:
            continue
        return {
            "stage": event.stage,
            "label": _display_stage_label(event.stage),
            "reason": _extract_event_reason(event),
            "reason_label": _display_reason_label(_extract_event_reason(event)),
            "timestamp": event.timestamp,
            "fields": dict(event.fields),
            "details": _build_failure_details(event),
        }
    return None


def _build_failure_details(event: PipelineEvent) -> list[dict[str, str]]:
    details: list[dict[str, str]] = []
    field_map = [
        ("decision", "판정"),
        ("latency", "지연상태"),
        ("ws_age_ms", "WS 나이"),
        ("ws_jitter_ms", "WS 지터"),
        ("spread_ratio", "호가스프레드"),
        ("quote_stale", "시세정체"),
        ("deposit", "주문가능금액"),
        ("qty", "수량"),
    ]
    for key, label in field_map:
        value = event.fields.get(key)
        if value in (None, "", "None"):
            continue
        if key in {"ws_age_ms", "ws_jitter_ms"}:
            display_value = f"{value}ms"
        else:
            display_value = str(value)
        details.append({"label": label, "value": display_value})
    return details


def _build_precheck_passes(item_events: list[PipelineEvent]) -> list[dict]:
    anchor_idx = next(
        (idx for idx, event in enumerate(item_events) if event.stage in _CONFIRMED_FLOW_ANCHOR_STAGES),
        None,
    )
    if anchor_idx is not None:
        return []

    precheck_stages = []
    seen = set()
    for event in item_events:
        if event.stage not in {"strength_momentum_pass", "dynamic_vpw_override_pass"}:
            continue
        if event.stage in seen:
            continue
        seen.add(event.stage)
        precheck_stages.append({
            "stage": event.stage,
            "label": _display_stage_label(event.stage),
            "kind": "pass",
        })
    return precheck_stages


def _find_latest_gatekeeper_event(item_events: list[PipelineEvent]) -> PipelineEvent | None:
    for event in reversed(item_events):
        if event.stage == "blocked_gatekeeper_reject":
            return event
    return None


def build_entry_pipeline_flow_report(target_date: str, since_time: str | None = None, top_n: int = 20) -> dict:
    log_path = LOGS_DIR / "sniper_state_handlers_info.log"
    lines = _iter_target_lines(log_path, target_date=target_date)
    events = [
        event
        for line in lines
        if (event := _parse_event(line)) and not _should_ignore_event(event)
    ]
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

    events.sort(key=_event_sort_key)

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
            blocker_counts[_friendly_blocker_name(latest)] += 1

        compact_flow = []
        for event in item_events:
            if not compact_flow or event.stage != compact_flow[-1]:
                compact_flow.append(event.stage)

        pass_flow = _build_pass_flow(item_events)
        latest_status = _build_latest_status(latest)
        latest_gatekeeper_event = _find_latest_gatekeeper_event(item_events)
        gatekeeper_replay = None
        if latest_gatekeeper_event is not None:
            replay_time = ""
            try:
                replay_time = datetime.strptime(
                    latest_gatekeeper_event.timestamp,
                    "%Y-%m-%d %H:%M:%S",
                ).strftime("%H:%M:%S")
            except Exception:
                replay_time = ""
            gatekeeper_replay = {
                "timestamp": latest_gatekeeper_event.timestamp,
                "time": replay_time,
                "action": latest_gatekeeper_event.fields.get("action") or "",
                "url": (
                    f"/gatekeeper-replay?date={target_date}&code={latest.code}"
                    + (f"&time={replay_time}" if replay_time else "")
                ),
                "api_url": (
                    f"/api/gatekeeper-replay?date={target_date}&code={latest.code}"
                    + (f"&time={replay_time}" if replay_time else "")
                ),
            }

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
            "precheck_passes": _build_precheck_passes(item_events),
            "latest_status": latest_status,
            "confirmed_failure": _build_confirmed_failure(item_events),
            "gatekeeper_replay": gatekeeper_replay,
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
        "blocker_guide": [
            _resolve_blocker_guide(gate)
            for gate, _count in blocker_counts.most_common(12)
        ],
        "sections": {
            "recent_stocks": per_stock_rows[:top_n],
            "blocked_stocks": [row for row in per_stock_rows if row["stage_class"] == "blocked"][:top_n],
            "submitted_stocks": [row for row in per_stock_rows if row["stage_class"] == "submitted"][:top_n],
            "waiting_stocks": [row for row in per_stock_rows if row["stage_class"] == "waiting"][:top_n],
        },
    }
    return report

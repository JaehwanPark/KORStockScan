"""Performance tuning report for AI-heavy holding and gatekeeper paths."""

from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from src.engine.log_archive_service import iter_target_log_lines
from src.engine.sniper_trade_review_report import build_trade_review_report
from src.market_regime import summarize_market_regime
from src.utils.constants import DATA_DIR, LOGS_DIR, POSTGRES_URL, TRADING_RULES


_ENTRY_RE = re.compile(
    r"^\[(?P<timestamp>[^\]]+)\].*?\[ENTRY_PIPELINE\] "
    r"(?P<name>.+?)\((?P<code>[^)]+)\) "
    r"stage=(?P<stage>[^\s]+)(?P<rest>.*)$"
)
_HOLDING_RE = re.compile(
    r"^\[(?P<timestamp>[^\]]+)\].*?\[HOLDING_PIPELINE\] "
    r"(?P<name>.+?)\((?P<code>[^)]+)\) "
    r"stage=(?P<stage>[^\s]+)(?P<rest>.*)$"
)
_FIELD_RE = re.compile(r"(?P<key>[A-Za-z_]+)=(?P<value>[^\s]+)")

_GATEKEEPER_DECISION_STAGES = {
    "blocked_gatekeeper_reject",
    "market_regime_pass",
    "blocked_gatekeeper_error",
}
_CONFIRMED_ENTRY_STAGES = {"order_bundle_submitted"}
_ENTRY_ARMED_STAGES = {"entry_armed", "entry_armed_resume"}
_ENTRY_ARMED_EXPIRED_STAGES = {"entry_armed_expired", "entry_armed_expired_after_wait", "entry_arm_expired"}
_GATEKEEPER_ACTION_RE = re.compile(
    r"\saction=(?P<action>.+?)(?:\s+cooldown_sec=|\s+cooldown_policy=|\s+gatekeeper_eval_ms=|$)"
)
_STRATEGY_LABELS = {
    "scalping": "스캘핑",
    "swing": "스윙",
    "other": "기타",
}
_STRATEGY_ORDER = ("scalping", "swing")
PERFORMANCE_TUNING_SCHEMA_VERSION = 3
_BLOCKER_LABELS = {
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
_REUSE_REASON_LABELS = {
    "sig_changed": "시그니처 변경",
    "age_expired": "재사용 창 만료",
    "ws_stale": "WS stale",
    "price_move": "가격 변화 확대",
    "near_ai_exit": "AI 손절 경계",
    "near_safe_profit": "안전수익 경계",
    "near_low_score": "저점수 경계",
    "score_boundary": "점수 경계",
    "missing_action": "이전 액션 없음",
    "missing_allow_flag": "이전 허용값 없음",
}
_SWING_DAILY_BLOCKER_LABELS = {
    "market_regime_block": "시장 국면 제한",
    "blocked_gatekeeper_reject": "Gatekeeper 거부",
    "blocked_swing_gap": "스윙 갭상승",
    "blocked_zero_qty": "주문 가능 수량",
    "latency_block": "지연 리스크",
}


@dataclass
class PerfEvent:
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


def _iter_target_lines(log_path: Path, *, target_date: str, marker: str) -> list[str]:
    return iter_target_log_lines([log_path], target_date=target_date, marker=marker)


def _jsonl_path(target_date: str) -> Path:
    return DATA_DIR / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"


def _stringify_field_value(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ",".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def _load_pipeline_events_from_jsonl(*, target_date: str) -> tuple[list[PerfEvent], list[PerfEvent]]:
    path = _jsonl_path(target_date)
    if not path.exists():
        return [], []

    entry_events: list[PerfEvent] = []
    holding_events: list[PerfEvent] = []

    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except Exception:
                continue

            pipeline = str(payload.get("pipeline") or "").strip()
            if pipeline not in {"ENTRY_PIPELINE", "HOLDING_PIPELINE"}:
                continue
            if payload.get("event_type") not in (None, "", "pipeline_event"):
                continue

            stock_name = str(payload.get("stock_name") or "").strip()
            stock_code = str(payload.get("stock_code") or "").strip()
            stage = str(payload.get("stage") or "").strip()
            emitted_at = str(payload.get("emitted_at") or "").strip()
            if not stock_name or not stock_code or not stage or not emitted_at:
                continue

            try:
                emitted_dt = datetime.fromisoformat(emitted_at)
            except Exception:
                continue
            if emitted_dt.strftime("%Y-%m-%d") != target_date:
                continue

            fields_payload = payload.get("fields") or {}
            if not isinstance(fields_payload, dict):
                fields_payload = {}
            fields = {
                str(key): _stringify_field_value(value).replace("|", " ")
                for key, value in fields_payload.items()
            }
            record_id = payload.get("record_id")
            if record_id not in (None, "", 0):
                fields.setdefault("id", str(record_id))

            event = PerfEvent(
                timestamp=emitted_dt.strftime("%Y-%m-%d %H:%M:%S"),
                name=stock_name,
                code=stock_code,
                stage=stage,
                fields=fields,
                raw_line=str(payload.get("text_payload") or ""),
            )
            if pipeline == "ENTRY_PIPELINE":
                entry_events.append(event)
            else:
                holding_events.append(event)

    def _sort_key(event: PerfEvent) -> tuple[datetime, str, str]:
        try:
            parsed = datetime.strptime(event.timestamp, "%Y-%m-%d %H:%M:%S")
        except Exception:
            parsed = datetime.min
        return parsed, event.code, event.stage

    entry_events.sort(key=_sort_key)
    holding_events.sort(key=_sort_key)
    return entry_events, holding_events


def _parse_event(line: str, pattern: re.Pattern[str]) -> PerfEvent | None:
    match = pattern.match(line.strip())
    if not match:
        return None
    fields = {
        m.group("key"): str(m.group("value") or "").replace("|", " ")
        for m in _FIELD_RE.finditer(match.group("rest") or "")
    }
    return PerfEvent(
        timestamp=match.group("timestamp"),
        name=match.group("name"),
        code=match.group("code"),
        stage=match.group("stage"),
        fields=fields,
        raw_line=line.strip(),
    )


def _safe_float(value, default: float | None = None) -> float | None:
    if value in (None, "", "-", "None"):
        return default
    try:
        return float(value)
    except Exception:
        return default


def _safe_int(value, default: int | None = None) -> int | None:
    if value in (None, "", "-", "None"):
        return default
    try:
        return int(float(value))
    except Exception:
        return default


def _safe_bool(value, default: bool = False) -> bool:
    if value in (None, "", "-", "None"):
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _safe_date_string(value) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    rank = max(0, min(len(ordered) - 1, math.ceil((pct / 100.0) * len(ordered)) - 1))
    return float(ordered[rank])


def _avg(values: list[float]) -> float:
    return round(sum(values) / len(values), 2) if values else 0.0


def _ratio(numerator: int, denominator: int) -> float:
    return round((numerator / denominator) * 100.0, 1) if denominator > 0 else 0.0


def _metric_card(label: str, value: str, hint: str = "") -> dict:
    return {"label": label, "value": value, "hint": hint}


def _strategy_group(strategy: str | None) -> str:
    raw = str(strategy or "").strip().upper()
    if raw == "SCALPING":
        return "scalping"
    if raw in {"KOSPI_ML", "KOSDAQ_ML", "SWING", "SWING_ML"}:
        return "swing"
    return "other"


def _strategy_label(group: str) -> str:
    return _STRATEGY_LABELS.get(group, group)


def _classify_entry_stage(stage: str) -> str:
    if stage in _CONFIRMED_ENTRY_STAGES:
        return "submitted"
    if stage.startswith("blocked_") or stage.endswith("_block") or stage.endswith("_failed"):
        return "blocked"
    if stage == "first_ai_wait":
        return "waiting"
    return "progress"


def _parse_trade_dt(value) -> datetime | None:
    if value in (None, "", "None"):
        return None
    candidate = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(candidate, fmt)
        except Exception:
            continue
    try:
        return datetime.fromisoformat(candidate)
    except Exception:
        return None


def _is_entered_trade(row: dict) -> bool:
    status = str(row.get("status") or "").upper()
    if row.get("buy_time"):
        return True
    if (_safe_int(row.get("buy_qty"), 0) or 0) > 0:
        return True
    return status in {"BUY_ORDERED", "HOLDING", "SELL_ORDERED", "COMPLETED"}


def _is_completed_trade(row: dict) -> bool:
    return str(row.get("status") or "").upper() == "COMPLETED"


def _valid_completed_profit_values(rows: list[dict]) -> list[float]:
    values: list[float] = []
    for row in rows:
        if not _is_completed_trade(row):
            continue
        profit_rate = _safe_float(row.get("profit_rate"), None)
        if profit_rate is None:
            continue
        values.append(float(profit_rate))
    return values


def _extract_gatekeeper_action(event: PerfEvent) -> str:
    action = str(event.fields.get("action") or "").replace("|", " ").strip()
    if action and action not in {"눌림", "전량", "둘", "스윙"}:
        return action
    match = _GATEKEEPER_ACTION_RE.search(event.raw_line or "")
    if match:
        return str(match.group("action") or "").replace("|", " ").strip()
    return action


def _friendly_blocker_name(event: PerfEvent) -> str:
    if event.stage == "blocked_gatekeeper_reject":
        action = _extract_gatekeeper_action(event)
        if action:
            return f"게이트키퍼: {action}"
    return _BLOCKER_LABELS.get(event.stage, event.stage)


def _split_reason_codes(value) -> list[str]:
    raw = str(value or "").strip()
    if not raw:
        return []
    return [token for token in re.split(r"[,\s]+", raw) if token]


def _friendly_reason_name(code: str) -> str:
    normalized = str(code or "").strip()
    return _REUSE_REASON_LABELS.get(normalized, normalized)


def _count_sig_delta_fields(counter: Counter, value) -> None:
    raw = str(value or "").strip()
    if not raw or raw == "-":
        return
    for delta_field in raw.split(","):
        if ":" not in delta_field:
            continue
        field_name = delta_field.split(":", 1)[0].strip()
        if field_name:
            counter[field_name] += 1


def _build_current_trade_rows(target_date: str) -> tuple[list[dict], list[str]]:
    report = build_trade_review_report(
        target_date=target_date,
        since_time=None,
        top_n=10_000,
        scope="all",
    )
    rows = list((report.get("sections", {}) or {}).get("recent_trades", []) or [])
    warnings = list((report.get("meta", {}) or {}).get("warnings", []) or [])
    return rows, warnings


def _infer_strategy_from_event(event: PerfEvent, strategy_by_code: dict[str, str]) -> str:
    raw = str(event.fields.get("strategy") or "").strip()
    if raw:
        return raw
    raw = str(strategy_by_code.get(str(event.code or "").strip()[:6]) or "").strip()
    if raw:
        return raw
    if event.stage in {
        "blocked_gatekeeper_reject",
        "blocked_swing_gap",
        "market_regime_pass",
        "blocked_gatekeeper_error",
    }:
        return "KOSPI_ML"
    return "SCALPING"


def _summarize_top_counts(counter: Counter[str], limit: int = 3) -> list[dict]:
    total = sum(counter.values())
    rows = []
    for label, count in counter.most_common(limit):
        rows.append({
            "label": label,
            "count": count,
            "ratio": _ratio(count, total),
        })
    return rows


def _load_cached_market_regime_summary(target_date: str) -> dict | None:
    cache_path = DATA_DIR / "cache" / "market_regime_snapshot.json"
    if not cache_path.exists():
        return None
    try:
        with open(cache_path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except Exception:
        return None

    cached_session_date = str(payload.get("cached_session_date") or payload.get("debug", {}).get("cached_session_date") or "")
    if cached_session_date != str(target_date or ""):
        return None

    summary = summarize_market_regime(payload.get("risk_state"))
    summary["allow_swing_entry"] = bool(payload.get("allow_swing_entry", False))
    summary["swing_score"] = _safe_int(payload.get("swing_score"), 0) or 0
    summary["cached_session_date"] = cached_session_date
    return summary


def _summarize_counter_with_stock_counts(counter: Counter[str], stock_sets: dict[str, set[str]]) -> list[dict]:
    total = sum(counter.values())
    rows = []
    for label, count in counter.most_common():
        rows.append({
            "label": label,
            "count": count,
            "stock_count": len(stock_sets.get(label) or set()),
            "ratio": _ratio(count, total),
        })
    return rows


def _build_swing_daily_summary(
    *,
    entry_events: list[PerfEvent],
    trade_rows: list[dict],
    strategy_rows: list[dict],
    target_date: str,
) -> dict:
    strategy_by_code = {}
    for row in trade_rows:
        code = str(row.get("code") or "").strip()[:6]
        if code and code not in strategy_by_code:
            strategy_by_code[code] = str(row.get("strategy") or "")

    swing_events = [
        event
        for event in entry_events
        if _strategy_group(_infer_strategy_from_event(event, strategy_by_code)) == "swing"
    ]
    swing_row = next((row for row in strategy_rows if row.get("key") == "swing"), None)
    swing_pipeline = dict((swing_row or {}).get("pipeline") or {})
    swing_outcomes = dict((swing_row or {}).get("outcomes") or {})

    blocker_counts: Counter[str] = Counter()
    blocker_stock_sets: dict[str, set[str]] = defaultdict(set)
    gatekeeper_actions: Counter[str] = Counter()

    for event in swing_events:
        label = _SWING_DAILY_BLOCKER_LABELS.get(event.stage)
        if not label:
            continue
        blocker_counts[label] += 1
        blocker_stock_sets[label].add(str(event.code or "").strip()[:6] or str(event.name or "").strip())
        if event.stage == "blocked_gatekeeper_reject":
            action = _extract_gatekeeper_action(event) or "UNKNOWN"
            gatekeeper_actions[action] += 1

    market_regime = _load_cached_market_regime_summary(target_date) or summarize_market_regime(None)
    market_regime["allow_swing_entry"] = bool(market_regime.get("allow_swing_entry", False))
    market_regime["swing_score"] = _safe_int(market_regime.get("swing_score"), 0) or 0

    dominant_label = blocker_counts.most_common(1)[0][0] if blocker_counts else ""
    candidates = int(swing_pipeline.get("candidates", 0) or 0)
    entered_rows = int(swing_outcomes.get("entered_rows", 0) or 0)
    total_blocker_events = sum(blocker_counts.values())
    total_blocker_stocks = len({code for codes in blocker_stock_sets.values() for code in codes})
    market_regime_block_count = blocker_counts.get("시장 국면 제한", 0)
    gatekeeper_reject_count = blocker_counts.get("Gatekeeper 거부", 0)

    if entered_rows > 0:
        day_type = {
            "label": "진입 발생일",
            "tone": "good",
            "comment": (
                f"스윙 실제 진입이 {entered_rows}건 발생했습니다. "
                "차단 사유보다 진입 후 성과와 missed case 비교가 더 중요해진 구간입니다."
            ),
        }
    elif not market_regime.get("allow_swing_entry", False) and market_regime_block_count > 0 and gatekeeper_reject_count > 0:
        day_type = {
            "label": "Gatekeeper 거부 중심 (시장 제한 동반)",
            "tone": "warn",
            "comment": (
                f"시장 국면은 {market_regime.get('status_text', '데이터 부족')}이어서 스윙 비허용 상태였고, "
                f"실제 blocker 이벤트는 Gatekeeper 거부가 {gatekeeper_reject_count}건으로 가장 많았습니다."
            ),
        }
    elif not market_regime.get("allow_swing_entry", False) and market_regime_block_count > 0:
        day_type = {
            "label": "시장 국면 제한 중심",
            "tone": "warn",
            "comment": (
                f"시장 국면이 {market_regime.get('status_text', '데이터 부족')}으로 스윙 비허용 상태였습니다. "
                "이런 날은 threshold 완화보다 시장 국면 차단이 맞았는지부터 보는 편이 안전합니다."
            ),
        }
    elif dominant_label == "Gatekeeper 거부":
        day_type = {
            "label": "Gatekeeper 거부 중심",
            "tone": "warn",
            "comment": (
                f"스윙 blocker 이벤트 중 Gatekeeper 거부가 {gatekeeper_reject_count}건으로 가장 많았습니다. "
                "먼저 action_label과 cooldown_policy 분포를 보는 편이 좋습니다."
            ),
        }
    elif dominant_label == "스윙 갭상승":
        day_type = {
            "label": "갭 차단 중심",
            "tone": "warn",
            "comment": "스윙 갭상승 차단이 우세한 날입니다. 실제 blocked_swing_gap 샘플을 본 뒤에만 완화 여부를 검토합니다.",
        }
    elif dominant_label == "지연 리스크":
        day_type = {
            "label": "지연 리스크 중심",
            "tone": "warn",
            "comment": "전략 자체보다 실행 지연이 차단에 큰 비중을 차지한 날입니다.",
        }
    elif dominant_label == "주문 가능 수량":
        day_type = {
            "label": "주문 가능 수량 제약",
            "tone": "warn",
            "comment": "신호보다 예산/수량 제약이 먼저 걸린 날입니다.",
        }
    elif candidates <= 0:
        day_type = {
            "label": "후보 부족",
            "tone": "warn",
            "comment": "스윙 후보 자체가 적어 차단 해석보다 스캐너 입력층을 먼저 봐야 하는 날입니다.",
        }
    else:
        day_type = {
            "label": "혼합 차단",
            "tone": "warn",
            "comment": "한 가지 blocker로 설명되지 않는 혼합형 차단일입니다. 시장 국면과 Gatekeeper를 함께 비교해야 합니다.",
        }

    return {
        "market_regime": market_regime,
        "day_type": day_type,
        "metrics": {
            "candidates": candidates,
            "entered_rows": entered_rows,
            "submitted": int(swing_pipeline.get("submitted", 0) or 0),
            "blocked_latest": int(swing_pipeline.get("blocked_latest", 0) or 0),
            "blocker_event_count": total_blocker_events,
            "blocked_stock_count": total_blocker_stocks,
        },
        "blocker_families": _summarize_counter_with_stock_counts(blocker_counts, blocker_stock_sets),
        "latest_blockers": list(swing_pipeline.get("latest_blockers") or []),
        "gatekeeper_actions": _summarize_top_counts(gatekeeper_actions, limit=5),
    }


def _build_strategy_outcomes(
    *,
    entry_events: list[PerfEvent],
    holding_events: list[PerfEvent],
    trade_rows: list[dict],
    trend_by_group: dict[str, dict] | None = None,
) -> list[dict]:
    strategy_by_code = {}
    for row in trade_rows:
        code = str(row.get("code") or "").strip()[:6]
        if not code:
            continue
        if code not in strategy_by_code:
            strategy_by_code[code] = str(row.get("strategy") or "")

    stock_events: dict[tuple[str, str], list[PerfEvent]] = {}
    for event in entry_events:
        stock_events.setdefault((event.name, event.code), []).append(event)

    pipeline_by_group: dict[str, dict] = {}
    for group in _STRATEGY_ORDER:
        pipeline_by_group[group] = {
            "candidates": 0,
            "ai_confirmed": 0,
            "entry_armed": 0,
            "submitted": 0,
            "blocked_latest": 0,
            "waiting_latest": 0,
            "progress_latest": 0,
            "latest_blockers": Counter(),
        }

    for _, item_events in stock_events.items():
        latest = item_events[-1]
        raw_strategy = _infer_strategy_from_event(latest, strategy_by_code)
        group = _strategy_group(raw_strategy)
        if group not in pipeline_by_group:
            continue
        bucket = pipeline_by_group[group]
        bucket["candidates"] += 1
        seen_stages = {event.stage for event in item_events}
        if "ai_confirmed" in seen_stages:
            bucket["ai_confirmed"] += 1
        if seen_stages & _ENTRY_ARMED_STAGES:
            bucket["entry_armed"] += 1
        if seen_stages & _CONFIRMED_ENTRY_STAGES:
            bucket["submitted"] += 1
        stage_class = _classify_entry_stage(latest.stage)
        if stage_class == "blocked":
            bucket["blocked_latest"] += 1
            bucket["latest_blockers"][_friendly_blocker_name(latest)] += 1
        elif stage_class == "waiting":
            bucket["waiting_latest"] += 1
        else:
            bucket["progress_latest"] += 1

    outcome_by_group: dict[str, dict] = {}
    for group in _STRATEGY_ORDER:
        group_rows = [row for row in trade_rows if _strategy_group(row.get("strategy")) == group]
        entered_rows = [row for row in group_rows if _is_entered_trade(row)]
        completed_rows = [row for row in entered_rows if _is_completed_trade(row)]
        open_rows = [row for row in entered_rows if not _is_completed_trade(row)]
        completed_profit_values = _valid_completed_profit_values(completed_rows)
        win_count = sum(1 for value in completed_profit_values if value > 0)
        loss_count = sum(1 for value in completed_profit_values if value < 0)
        outcome_by_group[group] = {
            "rows": group_rows,
            "entered_rows": entered_rows,
            "completed_rows": completed_rows,
            "open_rows": open_rows,
            "watching_rows": [
                row for row in group_rows
                if str(row.get("status") or "").upper() == "WATCHING"
            ],
            "expired_rows": [
                row for row in group_rows
                if str(row.get("status") or "").upper() == "EXPIRED"
            ],
            "win_count": win_count,
            "loss_count": loss_count,
            "win_rate": _ratio(win_count, len(completed_rows)),
            "avg_profit_rate": round(sum(completed_profit_values) / len(completed_profit_values), 2) if completed_profit_values else 0.0,
            "realized_pnl_krw": int(sum((_safe_int(row.get("realized_pnl_krw"), 0) or 0) for row in completed_rows)),
        }

    trade_group_by_code = {}
    for group, payload in outcome_by_group.items():
        for row in payload["entered_rows"]:
            code = str(row.get("code") or "").strip()[:6]
            if code and code not in trade_group_by_code:
                trade_group_by_code[code] = group

    exit_rules_by_group = {group: Counter() for group in _STRATEGY_ORDER}
    early_exit_by_group = Counter()
    for event in holding_events:
        if event.stage != "exit_signal":
            continue
        group = trade_group_by_code.get(str(event.code or "").strip()[:6])
        if group not in exit_rules_by_group:
            continue
        exit_rule = str(event.fields.get("exit_rule") or "-")
        exit_rules_by_group[group][exit_rule] += 1
        if "ai_early" in exit_rule:
            early_exit_by_group[group] += 1

    strategy_rows = []
    for group in _STRATEGY_ORDER:
        pipe = pipeline_by_group[group]
        out = outcome_by_group[group]
        blocker_total = sum(pipe["latest_blockers"].values())
        strategy_rows.append({
            "key": group,
            "label": _strategy_label(group),
            "pipeline": {
                "candidates": pipe["candidates"],
                "ai_confirmed": pipe["ai_confirmed"],
                "entry_armed": pipe["entry_armed"],
                "submitted": pipe["submitted"],
                "blocked_latest": pipe["blocked_latest"],
                "waiting_latest": pipe["waiting_latest"],
                "progress_latest": pipe["progress_latest"],
                "ai_confirm_rate": _ratio(pipe["ai_confirmed"], pipe["candidates"]),
                "entry_arm_rate": _ratio(pipe["entry_armed"], pipe["ai_confirmed"]),
                "submitted_rate": _ratio(pipe["submitted"], pipe["entry_armed"]),
                "latest_blockers": _summarize_top_counts(pipe["latest_blockers"]),
                "top_blocker": pipe["latest_blockers"].most_common(1)[0][0] if pipe["latest_blockers"] else "",
                "top_blocker_ratio": _ratio(pipe["latest_blockers"].most_common(1)[0][1], blocker_total) if pipe["latest_blockers"] else 0.0,
            },
            "outcomes": {
                "total_rows": len(out["rows"]),
                "entered_rows": len(out["entered_rows"]),
                "completed_rows": len(out["completed_rows"]),
                "open_rows": len(out["open_rows"]),
                "watching_rows": len(out["watching_rows"]),
                "expired_rows": len(out["expired_rows"]),
                "entry_rate": _ratio(len(out["entered_rows"]), pipe["candidates"]),
                "completion_rate": _ratio(len(out["completed_rows"]), len(out["entered_rows"])),
                "win_count": out["win_count"],
                "loss_count": out["loss_count"],
                "win_rate": out["win_rate"],
                "avg_profit_rate": out["avg_profit_rate"],
                "realized_pnl_krw": out["realized_pnl_krw"],
                "early_exit_count": early_exit_by_group[group],
                "early_exit_ratio": _ratio(early_exit_by_group[group], len(out["completed_rows"])),
                "top_exit_rules": _summarize_top_counts(exit_rules_by_group[group]),
            },
            "trends": (trend_by_group or {}).get(group, {}),
        })
    return strategy_rows


def _fetch_trade_history_rows(target_date: str, max_dates: int = 20) -> tuple[list[dict], list[str], list[str]]:
    warnings: list[str] = []
    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(POSTGRES_URL, pool_pre_ping=True)
    except Exception as exc:
        return [], [f"성과 추세용 DB 연결 준비 실패: {exc}"], []

    try:
        target_date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
    except Exception:
        return [], [f"성과 추세 기준일 형식이 잘못되었습니다: {target_date}"], []

    recent_dates: list[str] = []
    try:
        with engine.connect() as conn:
            date_rows = conn.execute(
                text(
                    """
                    SELECT rec_date
                    FROM recommendation_history
                    WHERE rec_date <= :target_date
                    GROUP BY rec_date
                    ORDER BY rec_date DESC
                    LIMIT :limit
                    """
                ),
                {"target_date": target_date_obj, "limit": max_dates},
            ).fetchall()
            recent_dates = [_safe_date_string(row[0]) for row in date_rows if _safe_date_string(row[0])]
            if not recent_dates:
                return [], warnings, []

            oldest = min(recent_dates)
            result = conn.execute(
                text(
                    """
                    SELECT
                        rec_date, stock_code, stock_name, status, strategy,
                        buy_price, buy_qty, buy_time, sell_price, sell_time, profit_rate
                    FROM recommendation_history
                    WHERE rec_date >= :oldest_date AND rec_date <= :target_date
                    ORDER BY rec_date DESC, COALESCE(sell_time, buy_time) DESC NULLS LAST, stock_code
                    """
                ),
                {"oldest_date": oldest, "target_date": target_date_obj},
            ).mappings().all()
    except Exception as exc:
        warnings.append(f"성과 추세 이력 조회 실패: {exc}")
        return [], warnings, []

    rows: list[dict] = []
    for row in result:
        status = str(row.get("status") or "")
        buy_price = _safe_float(row.get("buy_price"))
        sell_price = _safe_float(row.get("sell_price"))
        buy_qty = _safe_int(row.get("buy_qty"), 0) or 0
        raw_profit_rate = _safe_float(row.get("profit_rate"), None)
        profit_rate = round(raw_profit_rate, 2) if raw_profit_rate is not None and status.upper() == "COMPLETED" else None
        pnl_krw = (
            int(round((sell_price - buy_price) * buy_qty))
            if status.upper() == "COMPLETED" and sell_price is not None and buy_price is not None and buy_qty
            else 0
        )
        rows.append({
            "rec_date": _safe_date_string(row.get("rec_date")),
            "code": str(row.get("stock_code") or "").strip()[:6],
            "name": str(row.get("stock_name") or ""),
            "status": status,
            "strategy": str(row.get("strategy") or ""),
            "buy_price": buy_price,
            "buy_qty": buy_qty,
            "buy_time": str(row.get("buy_time") or ""),
            "sell_price": _safe_int(sell_price, 0) or 0,
            "sell_time": str(row.get("sell_time") or ""),
            "profit_rate": profit_rate,
            "realized_pnl_krw": pnl_krw,
        })
    return rows, warnings, recent_dates


def _summarize_trade_rows(rows: list[dict], date_count: int) -> dict:
    entered_rows = [row for row in rows if _is_entered_trade(row)]
    completed_rows = [row for row in entered_rows if _is_completed_trade(row)]
    completed_profit_values = _valid_completed_profit_values(completed_rows)
    win_count = sum(1 for value in completed_profit_values if value > 0)
    loss_count = sum(1 for value in completed_profit_values if value < 0)
    return {
        "date_count": date_count,
        "entered_rows": len(entered_rows),
        "completed_rows": len(completed_rows),
        "win_count": win_count,
        "loss_count": loss_count,
        "win_rate": _ratio(win_count, len(completed_rows)),
        "avg_profit_rate": round(sum(completed_profit_values) / len(completed_profit_values), 2) if completed_profit_values else 0.0,
        "realized_pnl_krw": int(sum(_safe_int(row.get("realized_pnl_krw"), 0) or 0 for row in completed_rows)),
    }


def _trend_signal(last_5: dict, last_20: dict) -> dict:
    diff = round(float(last_5.get("avg_profit_rate", 0.0)) - float(last_20.get("avg_profit_rate", 0.0)), 2)
    win_diff = round(float(last_5.get("win_rate", 0.0)) - float(last_20.get("win_rate", 0.0)), 1)
    if last_5.get("completed_rows", 0) < 2 and last_20.get("completed_rows", 0) < 4:
        return {
            "label": "표본 부족",
            "tone": "warn",
            "comment": "종료 거래가 적어 최근 추세 해석은 가볍게 보는 편이 좋습니다.",
            "avg_profit_diff": diff,
            "win_rate_diff": win_diff,
        }
    if diff >= 0.25 and win_diff >= 0.0:
        return {
            "label": "개선 추세",
            "tone": "good",
            "comment": "최근 5거래일 평균 손익이 20거래일 평균보다 개선된 상태입니다.",
            "avg_profit_diff": diff,
            "win_rate_diff": win_diff,
        }
    if diff <= -0.25 and win_diff <= 0.0:
        return {
            "label": "약화 추세",
            "tone": "bad",
            "comment": "최근 5거래일 평균 손익이 20거래일 평균보다 약해져 보수적 점검이 필요합니다.",
            "avg_profit_diff": diff,
            "win_rate_diff": win_diff,
        }
    return {
        "label": "혼합 추세",
        "tone": "warn",
        "comment": "최근 성과와 장기 성과가 엇갈려, 한 항목만 보고 튜닝하기엔 애매한 상태입니다.",
        "avg_profit_diff": diff,
        "win_rate_diff": win_diff,
    }


def _build_strategy_trends(history_rows: list[dict], recent_dates: list[str]) -> dict[str, dict]:
    rows_by_group_date: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for row in history_rows:
        group = _strategy_group(row.get("strategy"))
        if group not in _STRATEGY_ORDER:
            continue
        rows_by_group_date[group][str(row.get("rec_date") or "")].append(row)

    trend_by_group: dict[str, dict] = {}
    ordered_dates = list(reversed(recent_dates))
    for group in _STRATEGY_ORDER:
        date_map = rows_by_group_date.get(group, {})
        daily_points = []
        for rec_date in ordered_dates:
            rows = date_map.get(rec_date, [])
            summary = _summarize_trade_rows(rows, 1)
            daily_points.append({
                "date": rec_date,
                "entered_rows": summary["entered_rows"],
                "completed_rows": summary["completed_rows"],
                "win_rate": summary["win_rate"],
                "avg_profit_rate": summary["avg_profit_rate"],
                "realized_pnl_krw": summary["realized_pnl_krw"],
            })

        last_5_dates = ordered_dates[-5:]
        last_20_dates = ordered_dates[-20:]
        last_5_rows = [row for rec_date in last_5_dates for row in date_map.get(rec_date, [])]
        last_20_rows = [row for rec_date in last_20_dates for row in date_map.get(rec_date, [])]
        summary_5 = _summarize_trade_rows(last_5_rows, len(last_5_dates))
        summary_20 = _summarize_trade_rows(last_20_rows, len(last_20_dates))
        trend_by_group[group] = {
            "summary_5d": summary_5,
            "summary_20d": summary_20,
            "signal": _trend_signal(summary_5, summary_20),
            "recent_points": daily_points[-5:],
        }
    return trend_by_group


def _build_auto_comments(metrics: dict, strategy_rows: list[dict]) -> list[dict]:
    comments: list[dict] = []
    by_key = {row["key"]: row for row in strategy_rows}
    scalping = by_key.get("scalping")
    swing = by_key.get("swing")

    total_completed = sum(int((row.get("outcomes") or {}).get("completed_rows", 0)) for row in strategy_rows)
    if total_completed < 3:
        comments.append({
            "tone": "warn",
            "strategy": "전체",
            "title": "성과 표본이 아직 작습니다",
            "comment": (
                f"종료 거래가 {total_completed}건이라 성과 해석이 쉽게 흔들릴 수 있습니다. "
                "오늘 값은 방향성 점검용으로 보고, 3~5거래 이상 누적되면 튜닝 결정을 더 강하게 걸어보는 편이 안전합니다."
            ),
        })

    if scalping:
        pipe = scalping["pipeline"]
        out = scalping["outcomes"]
        trends = scalping.get("trends") or {}
        trend_signal = (trends.get("signal") or {})
        top_blocker = str(pipe.get("top_blocker") or "")
        top_blocker_ratio = float(pipe.get("top_blocker_ratio") or 0.0)
        if top_blocker == "동적 체결강도" and top_blocker_ratio >= 50.0 and out.get("entered_rows", 0) <= 2:
            comments.append({
                "tone": "warn",
                "strategy": scalping["label"],
                "title": "스캘핑 진입 병목이 동적 체결강도에 쏠려 있습니다",
                "comment": (
                    f"최신 차단의 {top_blocker_ratio:.1f}%가 동적 체결강도이며 실제 진입은 {out.get('entered_rows', 0)}건입니다. "
                    "특히 `window_buy_value`, `buy_ratio` 문턱이 과도한지 shadow 후보와 함께 점검할 시점입니다."
                ),
            })
        if float(out.get("early_exit_ratio", 0.0) or 0.0) >= 40.0 and float(out.get("avg_profit_rate", 0.0) or 0.0) <= 0.2:
            comments.append({
                "tone": "warn",
                "strategy": scalping["label"],
                "title": "조기청산 비중이 높습니다",
                "comment": (
                    f"종료 거래 중 AI 조기청산 비중이 {out.get('early_exit_ratio', 0.0):.1f}%입니다. "
                    "최소 보유시간, 하방카운트 조건, AI 저점수 컷아웃 민감도를 함께 점검해볼 만합니다."
                ),
            })
        if float(metrics.get("holding_skip_ratio", 0.0) or 0.0) > 65.0 and float(out.get("avg_profit_rate", 0.0) or 0.0) <= 0.0 and out.get("completed_rows", 0) >= 2:
            comments.append({
                "tone": "bad",
                "strategy": scalping["label"],
                "title": "보유 AI skip이 높고 성과가 약합니다",
                "comment": (
                    f"보유 AI skip 비율이 {metrics.get('holding_skip_ratio', 0.0):.1f}%인데 평균 손익률이 {out.get('avg_profit_rate', 0.0):+.2f}%입니다. "
                    "skip 재사용 창이나 WS age 기준이 공격적인지 확인할 필요가 있습니다."
                ),
            })
        elif out.get("completed_rows", 0) >= 2 and float(out.get("avg_profit_rate", 0.0) or 0.0) > 0.0:
            comments.append({
                "tone": "good",
                "strategy": scalping["label"],
                "title": "현재 스캘핑 밸런스는 크게 무너지지 않았습니다",
                "comment": (
                    f"종료 {out.get('completed_rows', 0)}건 기준 평균 손익률 {out.get('avg_profit_rate', 0.0):+.2f}%입니다. "
                    "성능 최적화 수치를 더 공격적으로 움직이기보다 현재 병목이 실제 기회손실로 이어지는지 우선 관찰하는 편이 좋습니다."
                ),
            })
        if trend_signal.get("label") == "약화 추세":
            comments.append({
                "tone": "warn",
                "strategy": scalping["label"],
                "title": "스캘핑 최근 추세가 장기 평균보다 약합니다",
                "comment": (
                    f"최근 5거래일 평균 손익은 {(trends.get('summary_5d') or {}).get('avg_profit_rate', 0.0):+.2f}%로, "
                    f"20거래일 평균 {(trends.get('summary_20d') or {}).get('avg_profit_rate', 0.0):+.2f}%보다 낮습니다. "
                    "지금 완화하려는 게이트가 최근 손익 약세를 더 키우는 방향은 아닌지 같이 봐야 합니다."
                ),
            })

    if swing:
        pipe = swing["pipeline"]
        out = swing["outcomes"]
        trends = swing.get("trends") or {}
        trend_signal = (trends.get("signal") or {})
        latest_blockers = {item["label"]: item["ratio"] for item in pipe.get("latest_blockers", [])}
        gatekeeper_ratio = sum(
            item["ratio"] for item in pipe.get("latest_blockers", [])
            if str(item.get("label") or "").startswith("게이트키퍼:")
        )
        gap_ratio = float(latest_blockers.get("스윙 갭상승", 0.0) or 0.0)
        if pipe.get("candidates", 0) >= 3 and out.get("entered_rows", 0) == 0 and (gatekeeper_ratio + gap_ratio) >= 60.0:
            comments.append({
                "tone": "warn",
                "strategy": swing["label"],
                "title": "스윙은 정책 게이트에서 대부분 멈추고 있습니다",
                "comment": (
                    f"스윙 감시 {pipe.get('candidates', 0)}종목 중 실제 진입은 0건이며, 최신 차단의 "
                    f"{gatekeeper_ratio:.1f}%는 Gatekeeper, {gap_ratio:.1f}%는 갭상승 차단입니다. "
                    "눌림 대기 cooldown, KOSPI gap 기준, Gatekeeper 프롬프트의 보수성을 함께 재확인하는 편이 좋습니다."
                ),
            })
        if float(metrics.get("gatekeeper_fast_reuse_ratio", 0.0) or 0.0) > 60.0 and pipe.get("ai_confirmed", 0) <= 1:
            comments.append({
                "tone": "warn",
                "strategy": swing["label"],
                "title": "Gatekeeper fast reuse가 높은 편입니다",
                "comment": (
                    f"Gatekeeper fast reuse 비율이 {metrics.get('gatekeeper_fast_reuse_ratio', 0.0):.1f}%인데 "
                    f"스윙 AI 확답은 {pipe.get('ai_confirmed', 0)}건입니다. TTL을 낮추거나 경계 구간 재평가를 더 자주 허용할 여지가 있습니다."
                ),
            })
        if gatekeeper_ratio > 0:
            comments.append({
                "tone": "good" if gatekeeper_ratio < 50.0 else "warn",
                "strategy": swing["label"],
                "title": "Gatekeeper 액션 분포를 함께 봐야 합니다",
                "comment": (
                    "스윙은 실제 체결보다 Gatekeeper 판단 품질이 선행합니다. "
                    "특히 `눌림 대기`가 많다면 재평가 간격과 재진입 조건을, `전량 회피`가 많다면 프롬프트의 공급 우위 해석이 과한지 확인하세요."
                ),
            })
        if trend_signal.get("label") == "개선 추세" and out.get("entered_rows", 0) == 0:
            comments.append({
                "tone": "warn",
                "strategy": swing["label"],
                "title": "스윙 장기 성과는 나쁘지 않은데 오늘 진입이 막혔습니다",
                "comment": (
                    f"최근 5거래일 평균 손익이 {(trends.get('summary_5d') or {}).get('avg_profit_rate', 0.0):+.2f}%로 개선 추세인데, "
                    f"오늘 실제 스윙 진입은 {out.get('entered_rows', 0)}건입니다. "
                    "Gatekeeper 보수성이나 gap 기준이 최근 장세 대비 과한지 다시 점검해볼 만합니다."
                ),
            })

    if float(metrics.get("gatekeeper_eval_ms_p95", 0.0) or 0.0) > 1200.0:
        comments.append({
            "tone": "warn",
            "strategy": "전체",
            "title": "Gatekeeper 평가 시간이 길어지고 있습니다",
            "comment": (
                f"Gatekeeper 평가 p95가 {metrics.get('gatekeeper_eval_ms_p95', 0.0):.0f}ms입니다. "
                "프롬프트 입력값이 너무 많아졌는지, fast reuse가 충분히 작동하는지 함께 점검해볼 만합니다."
            ),
        })

    return comments


def _build_watch_items(metrics: dict) -> list[dict]:
    hold_skip_ratio = float(metrics.get("holding_skip_ratio", 0.0) or 0.0)
    hold_ws_p95 = float(metrics.get("holding_skip_ws_age_p95", 0.0) or 0.0)
    gate_eval_p95 = float(metrics.get("gatekeeper_eval_ms_p95", 0.0) or 0.0)
    gate_fast_ratio = float(metrics.get("gatekeeper_fast_reuse_ratio", 0.0) or 0.0)
    gate_ws_p95 = float(metrics.get("gatekeeper_fast_reuse_ws_age_p95", 0.0) or 0.0)
    ai_hit_ratio = float(metrics.get("holding_ai_cache_hit_ratio", 0.0) or 0.0)
    dual_shadow_samples = int(metrics.get("dual_persona_shadow_samples", 0) or 0)
    dual_conflict_ratio = float(metrics.get("dual_persona_conflict_ratio", 0.0) or 0.0)
    dual_veto_ratio = float(metrics.get("dual_persona_conservative_veto_ratio", 0.0) or 0.0)
    dual_override_ratio = float(metrics.get("dual_persona_fused_override_ratio", 0.0) or 0.0)
    dual_extra_ms_p95 = float(metrics.get("dual_persona_extra_ms_p95", 0.0) or 0.0)

    hold_ws_warn = float(getattr(TRADING_RULES, "AI_HOLDING_FAST_REUSE_MAX_WS_AGE_SEC", 1.5) or 1.5)
    gate_ws_warn = float(getattr(TRADING_RULES, "AI_GATEKEEPER_FAST_REUSE_MAX_WS_AGE_SEC", 2.0) or 2.0)
    dual_min_samples = int(getattr(TRADING_RULES, "OPENAI_DUAL_PERSONA_GATEKEEPER_MIN_SAMPLES", 30) or 30)
    dual_min_override_ratio = float(
        getattr(TRADING_RULES, "OPENAI_DUAL_PERSONA_GATEKEEPER_MIN_OVERRIDE_RATIO", 3.0) or 3.0
    )
    dual_max_extra_ms = float(getattr(TRADING_RULES, "OPENAI_DUAL_PERSONA_MAX_EXTRA_MS", 2500) or 2500)
    dual_max_gate_eval_p95 = float(
        getattr(TRADING_RULES, "OPENAI_DUAL_PERSONA_GATEKEEPER_MAX_EVAL_MS_P95", 5000) or 5000
    )

    items: list[dict] = []

    items.append({
        "label": "보유 AI skip 비율",
        "value": f"{hold_skip_ratio:.1f}%",
        "target": "20% ~ 60%",
        "tone": "warn" if hold_skip_ratio < 15.0 or hold_skip_ratio > 70.0 else "good",
        "comment": "너무 낮으면 비용 절감이 약하고, 너무 높으면 stale 리스크를 점검해야 합니다.",
    })
    items.append({
        "label": "보유 AI skip WS age p95",
        "value": f"{hold_ws_p95:.2f}s",
        "target": f"<= {hold_ws_warn:.2f}s",
        "tone": "bad" if hold_ws_p95 > hold_ws_warn else "good",
        "comment": "skip 시점의 웹소켓 나이가 길면 최신성이 부족할 수 있습니다.",
    })
    items.append({
        "label": "Gatekeeper 평가 p95",
        "value": f"{gate_eval_p95:.0f}ms",
        "target": f"re-enable <= {int(dual_max_gate_eval_p95)}ms / preferred < 1200ms",
        "tone": "bad" if gate_eval_p95 > dual_max_gate_eval_p95 else ("warn" if gate_eval_p95 > 1200 else "good"),
        "comment": "오늘 재활성화 최소 조건과 이상적 성능 목표를 함께 표시합니다.",
    })
    items.append({
        "label": "Gatekeeper fast reuse 비율",
        "value": f"{gate_fast_ratio:.1f}%",
        "target": "15% ~ 55%",
        "tone": "warn" if gate_fast_ratio < 10.0 or gate_fast_ratio > 65.0 else "good",
        "comment": "너무 낮으면 최적화 효과가 적고, 너무 높으면 같은 판단을 오래 재사용할 수 있습니다.",
    })
    items.append({
        "label": "Gatekeeper fast reuse WS age p95",
        "value": f"{gate_ws_p95:.2f}s",
        "target": f"<= {gate_ws_warn:.2f}s",
        "tone": "bad" if gate_ws_p95 > gate_ws_warn else "good",
        "comment": "fast reuse가 stale WS 위에서 일어나지 않는지 확인합니다.",
    })
    items.append({
        "label": "보유 AI 결과 cache hit",
        "value": f"{ai_hit_ratio:.1f}%",
        "target": "10% ~ 50%",
        "tone": "warn" if ai_hit_ratio < 5.0 or ai_hit_ratio > 70.0 else "good",
        "comment": "높다고 무조건 좋은 건 아닙니다. 너무 높으면 같은 판단 반복일 수 있습니다.",
    })
    items.append({
        "label": "듀얼 페르소나 shadow 표본",
        "value": f"{dual_shadow_samples}건",
        "target": f"re-enable >= {dual_min_samples}건",
        "tone": "warn" if dual_shadow_samples < dual_min_samples else "good",
        "comment": "표본이 너무 적으면 재활성화 판단과 충돌률 해석이 쉽게 흔들립니다.",
    })
    items.append({
        "label": "듀얼 페르소나 충돌률",
        "value": f"{dual_conflict_ratio:.1f}%",
        "target": "15% ~ 35%",
        "tone": "warn" if dual_shadow_samples >= 10 and (dual_conflict_ratio < 15.0 or dual_conflict_ratio > 35.0) else "good",
        "comment": "너무 낮으면 중복 판단, 너무 높으면 프롬프트 방향 불일치를 의심할 수 있습니다.",
    })
    items.append({
        "label": "보수 veto 비율",
        "value": f"{dual_veto_ratio:.1f}%",
        "target": "8% ~ 25%",
        "tone": "warn" if dual_shadow_samples >= 10 and (dual_veto_ratio < 8.0 or dual_veto_ratio > 25.0) else "good",
        "comment": "과도한 veto는 과보수, 지나치게 낮은 veto는 실익 부족일 수 있습니다.",
    })
    items.append({
        "label": "가상 fused override 비율",
        "value": f"{dual_override_ratio:.1f}%",
        "target": f"re-enable >= {dual_min_override_ratio:.1f}% / preferred 5% ~ 15%",
        "tone": (
            "bad"
            if dual_shadow_samples >= dual_min_samples and dual_override_ratio < dual_min_override_ratio
            else ("warn" if dual_shadow_samples >= 10 and (dual_override_ratio < 5.0 or dual_override_ratio > 15.0) else "good")
        ),
        "comment": "재활성화 최소 기준과 이상적 override 분포를 함께 봅니다.",
    })
    items.append({
        "label": "듀얼 페르소나 extra latency p95",
        "value": f"{dual_extra_ms_p95:.0f}ms",
        "target": f"<= {int(dual_max_extra_ms)}ms",
        "tone": "warn" if dual_shadow_samples >= 1 and dual_extra_ms_p95 > dual_max_extra_ms else "good",
        "comment": "shadow는 비동기지만, 실제 live 전환 전에 응답시간 분포는 미리 관찰해두는 편이 좋습니다.",
    })
    dual_gatekeeper_ready = bool(
        dual_shadow_samples >= dual_min_samples
        and dual_override_ratio >= dual_min_override_ratio
        and dual_extra_ms_p95 <= dual_max_extra_ms
        and gate_eval_p95 <= dual_max_gate_eval_p95
    )
    items.append({
        "label": "Gatekeeper 듀얼 재활성화 조건",
        "value": "충족" if dual_gatekeeper_ready else "미충족",
        "target": (
            f"samples>={dual_min_samples}, override>={dual_min_override_ratio:.1f}%, "
            f"extra_p95<={int(dual_max_extra_ms)}ms, gate_p95<={int(dual_max_gate_eval_p95)}ms"
        ),
        "tone": "good" if dual_gatekeeper_ready else "warn",
        "comment": (
            f"현재 samples={dual_shadow_samples}, override={dual_override_ratio:.1f}%, "
            f"extra_p95={dual_extra_ms_p95:.0f}ms, gate_p95={gate_eval_p95:.0f}ms"
        ),
    })
    return items


def build_performance_tuning_report(*, target_date: str, since_time: str | None = None) -> dict:
    entry_events, holding_events = _load_pipeline_events_from_jsonl(target_date=target_date)
    if not entry_events and not holding_events:
        log_path = LOGS_DIR / "sniper_state_handlers_info.log"
        entry_lines = _iter_target_lines(log_path, target_date=target_date, marker="[ENTRY_PIPELINE]")
        holding_lines = _iter_target_lines(log_path, target_date=target_date, marker="[HOLDING_PIPELINE]")
        entry_events = [event for line in entry_lines if (event := _parse_event(line, _ENTRY_RE))]
        holding_events = [event for line in holding_lines if (event := _parse_event(line, _HOLDING_RE))]

    since_dt = _parse_since_datetime(target_date, since_time)
    if since_dt is not None:
        entry_events = [e for e in entry_events if datetime.strptime(e.timestamp, "%Y-%m-%d %H:%M:%S") >= since_dt]
        holding_events = [e for e in holding_events if datetime.strptime(e.timestamp, "%Y-%m-%d %H:%M:%S") >= since_dt]

    holding_reviews = [e for e in holding_events if e.stage == "ai_holding_review"]
    holding_skips = [e for e in holding_events if e.stage == "ai_holding_skip_unchanged"]
    exit_signals = [e for e in holding_events if e.stage == "exit_signal"]
    gatekeeper_decisions = [e for e in entry_events if e.stage in _GATEKEEPER_DECISION_STAGES]
    gatekeeper_fast_reuse = [e for e in entry_events if e.stage == "gatekeeper_fast_reuse"]
    dual_persona_events = [e for e in (entry_events + holding_events) if e.stage == "dual_persona_shadow"]
    dual_gatekeeper_events = [e for e in dual_persona_events if str(e.fields.get("decision_type") or "") == "gatekeeper"]
    dual_overnight_events = [e for e in dual_persona_events if str(e.fields.get("decision_type") or "") == "overnight"]
    budget_pass_events = [e for e in entry_events if e.stage == "budget_pass"]
    submitted_events = [e for e in entry_events if e.stage == "order_bundle_submitted"]
    latency_block_events = [e for e in entry_events if e.stage == "latency_block"]
    latency_pass_events = [e for e in entry_events if e.stage == "latency_pass"]
    expired_armed_events = [e for e in entry_events if e.stage in _ENTRY_ARMED_EXPIRED_STAGES]
    fill_rebased_events = [e for e in holding_events if e.stage == "position_rebased_after_fill"]
    preset_sync_ok_events = [e for e in holding_events if e.stage == "preset_exit_sync_ok"]
    preset_sync_mismatch_events = [e for e in holding_events if e.stage == "preset_exit_sync_mismatch"]
    ai_overlap_events = [
        e
        for e in entry_events
        if e.stage in {
            "ai_confirmed",
            "blocked_ai_score",
            "blocked_overbought",
            "blocked_strength_momentum",
            "blocked_vpw",
            "latency_block",
            "latency_pass",
        }
    ]

    holding_review_ms = [float(v) for e in holding_reviews if (v := _safe_float(e.fields.get("review_ms"))) is not None]
    holding_skip_ws_ages = [float(v) for e in holding_skips if (v := _safe_float(e.fields.get("ws_age_sec"))) is not None]
    gatekeeper_eval_ms = [float(v) for e in gatekeeper_decisions if (v := _safe_float(e.fields.get("gatekeeper_eval_ms"))) is not None]
    gatekeeper_fast_ws_ages = [float(v) for e in gatekeeper_fast_reuse if (v := _safe_float(e.fields.get("ws_age_sec"))) is not None]
    dual_shadow_extra_ms = [float(v) for e in dual_persona_events if (v := _safe_float(e.fields.get("shadow_extra_ms"))) is not None]

    holding_ai_cache_modes = Counter(str(e.fields.get("ai_cache", "miss") or "miss") for e in holding_reviews)
    gatekeeper_cache_modes = Counter(str(e.fields.get("gatekeeper_cache", "miss") or "miss") for e in gatekeeper_decisions)
    gatekeeper_actions = Counter(str(e.fields.get("action", "UNKNOWN") or "UNKNOWN") for e in gatekeeper_decisions if e.stage == "blocked_gatekeeper_reject")
    exit_rule_counts = Counter(str(e.fields.get("exit_rule", "-") or "-") for e in exit_signals)
    dual_persona_agreement = Counter(str(e.fields.get("agreement_bucket", "-") or "-") for e in dual_persona_events)
    dual_persona_winners = Counter(str(e.fields.get("winner", "-") or "-") for e in dual_persona_events)
    dual_persona_decision_types = Counter(str(e.fields.get("decision_type", "-") or "-") for e in dual_persona_events)
    trade_rows, trade_warnings = _build_current_trade_rows(target_date)
    history_rows, history_warnings, recent_history_dates = _fetch_trade_history_rows(target_date)
    trend_by_group = _build_strategy_trends(history_rows, recent_history_dates)
    fill_quality_by_trade_id: dict[str, str] = {}
    for event in fill_rebased_events:
        trade_id = str(event.fields.get("id") or "").strip()
        if not trade_id:
            continue
        quality = str(event.fields.get("fill_quality") or "UNKNOWN").strip().upper() or "UNKNOWN"
        prev = fill_quality_by_trade_id.get(trade_id)
        if prev == "PARTIAL_FILL":
            continue
        if quality == "PARTIAL_FILL":
            fill_quality_by_trade_id[trade_id] = quality
        elif prev is None:
            fill_quality_by_trade_id[trade_id] = quality

    fill_quality_profit_map: dict[str, list[float]] = defaultdict(list)
    for row in trade_rows:
        if not _is_completed_trade(row):
            continue
        profit_rate = _safe_float(row.get("profit_rate"), None)
        if profit_rate is None:
            continue
        trade_id = str(row.get("id") or "").strip()
        quality = fill_quality_by_trade_id.get(trade_id, "UNKNOWN")
        fill_quality_profit_map[quality].append(float(profit_rate))
    dual_persona_hard_flags = Counter()
    for event in dual_persona_events:
        raw_flags = str(event.fields.get("hard_flags", "") or "")
        if not raw_flags or raw_flags == "-":
            continue
        for flag in raw_flags.split(","):
            clean_flag = str(flag or "").strip()
            if clean_flag:
                dual_persona_hard_flags[clean_flag] += 1

    latency_reason_counts = Counter(str(e.fields.get("reason") or "-") for e in latency_block_events)
    latency_danger_reason_counts = Counter()
    for event in latency_block_events:
        raw_danger_reasons = str(event.fields.get("latency_danger_reasons") or "").strip()
        if not raw_danger_reasons:
            continue
        for reason in raw_danger_reasons.split(","):
            clean = str(reason or "").strip()
            if clean:
                latency_danger_reason_counts[clean] += 1
    quote_fresh_latency_blocks = sum(
        1
        for e in latency_block_events
        if str(e.fields.get("quote_stale") or "").strip().lower() in {"false", "0", "no"}
    )
    quote_fresh_latency_passes = sum(
        1
        for e in latency_pass_events
        if str(e.fields.get("quote_stale") or "").strip().lower() in {"false", "0", "no"}
    )
    fill_quality_counts = Counter(str(e.fields.get("fill_quality") or "UNKNOWN") for e in fill_rebased_events)
    preset_sync_status_counts = Counter(str(e.fields.get("sync_status") or "-") for e in preset_sync_mismatch_events + preset_sync_ok_events)
    ai_overlap_blocked_stage_counts = Counter()
    ai_overlap_overbought_blocks = 0
    for event in ai_overlap_events:
        blocked_stage = str(event.fields.get("blocked_stage") or "").strip()
        if blocked_stage and blocked_stage != "-":
            ai_overlap_blocked_stage_counts[blocked_stage] += 1
        if _safe_bool(event.fields.get("overbought_blocked"), False):
            ai_overlap_overbought_blocks += 1

    holding_reuse_blockers = Counter()
    holding_sig_deltas = Counter()
    for event in holding_events:
        if event.stage != "ai_holding_reuse_bypass":
            continue
        for reason_code in _split_reason_codes(event.fields.get("reason_codes")):
            holding_reuse_blockers[_friendly_reason_name(reason_code)] += 1
        _count_sig_delta_fields(holding_sig_deltas, event.fields.get("sig_delta"))

    gatekeeper_reuse_blockers = Counter()
    gatekeeper_action_ages = []
    gatekeeper_allow_ages = []
    gatekeeper_sig_deltas = Counter()
    gatekeeper_bypass_evaluation_samples = 0
    
    for event in entry_events:
        if event.stage != "gatekeeper_fast_reuse_bypass":
            continue
        gatekeeper_bypass_evaluation_samples += 1
        for reason_code in _split_reason_codes(event.fields.get("reason_codes")):
            gatekeeper_reuse_blockers[_friendly_reason_name(reason_code)] += 1
        
        # 신규: lifecycle age 수집
        action_age_str = event.fields.get("action_age_sec")
        if action_age_str and action_age_str != "-":
            try:
                gatekeeper_action_ages.append(float(action_age_str))
            except (ValueError, TypeError):
                pass
        
        allow_age_str = event.fields.get("allow_entry_age_sec")
        if allow_age_str and allow_age_str != "-":
            try:
                gatekeeper_allow_ages.append(float(allow_age_str))
            except (ValueError, TypeError):
                pass
        
        # 신규: sig_delta 상위 필드 추출
        _count_sig_delta_fields(gatekeeper_sig_deltas, event.fields.get("sig_delta"))

    total_holding_samples = len(holding_reviews) + len(holding_skips)
    total_gatekeeper_samples = len(gatekeeper_decisions)
    holding_ai_cache_hit_count = holding_ai_cache_modes.get("hit", 0)
    gatekeeper_fast_reuse_count = gatekeeper_cache_modes.get("fast_reuse", 0)
    gatekeeper_ai_cache_hit_count = gatekeeper_cache_modes.get("hit", 0)
    dual_persona_conflicts = sum(
        1 for e in dual_persona_events
        if str(e.fields.get("agreement_bucket", "all_agree") or "all_agree") != "all_agree"
    )
    dual_persona_conservative_veto = sum(
        1 for e in dual_persona_events if _safe_bool(e.fields.get("cons_veto"), False)
    )
    dual_persona_fused_override = sum(
        1
        for e in dual_persona_events
        if str(e.fields.get("fused_action", "") or "") != str(e.fields.get("gemini_action", "") or "")
    )

    metrics = {
        "holding_reviews": len(holding_reviews),
        "holding_skips": len(holding_skips),
        "holding_skip_ratio": _ratio(len(holding_skips), total_holding_samples),
        "holding_ai_cache_hit_ratio": _ratio(holding_ai_cache_hit_count, len(holding_reviews)),
        "holding_review_ms_avg": _avg(holding_review_ms),
        "holding_review_ms_p95": round(_percentile(holding_review_ms, 95), 2),
        "holding_skip_ws_age_p95": round(_percentile(holding_skip_ws_ages, 95), 2),
        "gatekeeper_decisions": total_gatekeeper_samples,
        "gatekeeper_fast_reuse_ratio": _ratio(gatekeeper_fast_reuse_count, total_gatekeeper_samples),
        "gatekeeper_ai_cache_hit_ratio": _ratio(gatekeeper_ai_cache_hit_count, total_gatekeeper_samples),
        "gatekeeper_eval_ms_avg": _avg(gatekeeper_eval_ms),
        "gatekeeper_eval_ms_p95": round(_percentile(gatekeeper_eval_ms, 95), 2),
        "gatekeeper_fast_reuse_ws_age_p95": round(_percentile(gatekeeper_fast_ws_ages, 95), 2),
        "gatekeeper_action_age_p95": round(_percentile(gatekeeper_action_ages, 95), 2) if gatekeeper_action_ages else 0,
        "gatekeeper_allow_entry_age_p95": round(_percentile(gatekeeper_allow_ages, 95), 2) if gatekeeper_allow_ages else 0,
        "gatekeeper_bypass_evaluation_samples": gatekeeper_bypass_evaluation_samples,
        "budget_pass_events": int(len(budget_pass_events)),
        "order_bundle_submitted_events": int(len(submitted_events)),
        "budget_pass_to_submitted_rate": _ratio(len(submitted_events), len(budget_pass_events)),
        "latency_block_events": int(len(latency_block_events)),
        "latency_pass_events": int(len(latency_pass_events)),
        "quote_fresh_latency_blocks": int(quote_fresh_latency_blocks),
        "quote_fresh_latency_passes": int(quote_fresh_latency_passes),
        "quote_fresh_latency_pass_rate": _ratio(
            quote_fresh_latency_passes,
            quote_fresh_latency_passes + quote_fresh_latency_blocks,
        ),
        "expired_armed_events": int(len(expired_armed_events)),
        "position_rebased_after_fill_events": int(len(fill_rebased_events)),
        "full_fill_events": int(fill_quality_counts.get("FULL_FILL", 0)),
        "partial_fill_events": int(fill_quality_counts.get("PARTIAL_FILL", 0)),
        "preset_exit_sync_ok_events": int(len(preset_sync_ok_events)),
        "preset_exit_sync_mismatch_events": int(len(preset_sync_mismatch_events)),
        "preset_exit_sync_mismatch_rate": _ratio(
            len(preset_sync_mismatch_events),
            len(preset_sync_mismatch_events) + len(preset_sync_ok_events),
        ),
        "ai_overlap_events": int(len(ai_overlap_events)),
        "ai_overlap_blocked_events": int(sum(ai_overlap_blocked_stage_counts.values())),
        "ai_overlap_overbought_blocked_events": int(ai_overlap_overbought_blocks),
        "exit_signals": len(exit_signals),
        "dual_persona_shadow_samples": len(dual_persona_events),
        "dual_persona_gatekeeper_samples": len(dual_gatekeeper_events),
        "dual_persona_overnight_samples": len(dual_overnight_events),
        "dual_persona_conflict_ratio": _ratio(dual_persona_conflicts, len(dual_persona_events)),
        "dual_persona_conservative_veto_ratio": _ratio(dual_persona_conservative_veto, len(dual_persona_events)),
        "dual_persona_fused_override_ratio": _ratio(dual_persona_fused_override, len(dual_persona_events)),
        "dual_persona_extra_ms_p95": round(_percentile(dual_shadow_extra_ms, 95), 2),
        "full_fill_completed_avg_profit_rate": round(
            sum(fill_quality_profit_map.get("FULL_FILL", [])) / len(fill_quality_profit_map.get("FULL_FILL", [])),
            3,
        ) if fill_quality_profit_map.get("FULL_FILL") else 0.0,
        "partial_fill_completed_avg_profit_rate": round(
            sum(fill_quality_profit_map.get("PARTIAL_FILL", [])) / len(fill_quality_profit_map.get("PARTIAL_FILL", [])),
            3,
        ) if fill_quality_profit_map.get("PARTIAL_FILL") else 0.0,
    }

    cards = [
        _metric_card("보유 AI 리뷰", f"{metrics['holding_reviews']}건", "실제 AI 재평가"),
        _metric_card("보유 AI skip", f"{metrics['holding_skips']}건", "시장상태 동일로 생략"),
        _metric_card("보유 AI p95", f"{metrics['holding_review_ms_p95']:.0f}ms", "리뷰 지연 상위 5%"),
        _metric_card("Gatekeeper 결정", f"{metrics['gatekeeper_decisions']}건", "실제 허용/보류 판단"),
        _metric_card("Gatekeeper fast reuse", f"{metrics['gatekeeper_fast_reuse_ratio']:.1f}%", "같은 장면 재사용 비율"),
        _metric_card("Gatekeeper p95", f"{metrics['gatekeeper_eval_ms_p95']:.0f}ms", "평가 지연 상위 5%"),
        _metric_card("Dual Persona shadow", f"{metrics['dual_persona_shadow_samples']}건", "Gatekeeper + Overnight shadow 표본"),
        _metric_card("Dual Persona 충돌률", f"{metrics['dual_persona_conflict_ratio']:.1f}%", "Gemini와 다른 결론 비중"),
        _metric_card("보수 veto", f"{metrics['dual_persona_conservative_veto_ratio']:.1f}%", "보수 페르소나 veto 비중"),
        _metric_card("Dual Persona p95", f"{metrics['dual_persona_extra_ms_p95']:.0f}ms", "shadow 추가 응답시간 상위 5%"),
    ]

    strategy_rows = _build_strategy_outcomes(
        entry_events=entry_events,
        holding_events=holding_events,
        trade_rows=trade_rows,
        trend_by_group=trend_by_group,
    )
    swing_daily_summary = _build_swing_daily_summary(
        entry_events=entry_events,
        trade_rows=trade_rows,
        strategy_rows=strategy_rows,
        target_date=target_date,
    )
    auto_comments = _build_auto_comments(metrics, strategy_rows)

    top_holding_slow = sorted(
        [
            {
                "timestamp": e.timestamp,
                "name": e.name,
                "code": e.code,
                "review_ms": _safe_int(e.fields.get("review_ms"), 0) or 0,
                "profit_rate": e.fields.get("profit_rate", ""),
                "ai_cache": e.fields.get("ai_cache", "miss"),
            }
            for e in holding_reviews
        ],
        key=lambda item: item["review_ms"],
        reverse=True,
    )[:8]

    top_gatekeeper_slow = sorted(
        [
            {
                "timestamp": e.timestamp,
                "name": e.name,
                "code": e.code,
                "gatekeeper_eval_ms": _safe_int(e.fields.get("gatekeeper_eval_ms"), 0) or 0,
                "cache": e.fields.get("gatekeeper_cache", "miss"),
                "action": e.fields.get("action", e.fields.get("gatekeeper", "")),
            }
            for e in gatekeeper_decisions
        ],
        key=lambda item: item["gatekeeper_eval_ms"],
        reverse=True,
    )[:8]
    top_dual_persona_slow = sorted(
        [
            {
                "timestamp": e.timestamp,
                "name": e.name,
                "code": e.code,
                "decision_type": e.fields.get("decision_type", "-"),
                "shadow_extra_ms": _safe_int(e.fields.get("shadow_extra_ms"), 0) or 0,
                "winner": e.fields.get("winner", "-"),
                "agreement_bucket": e.fields.get("agreement_bucket", "-"),
            }
            for e in dual_persona_events
        ],
        key=lambda item: item["shadow_extra_ms"],
        reverse=True,
    )[:8]

    return {
        "date": target_date,
        "since": since_time,
        "metrics": metrics,
        "cards": cards,
        "watch_items": _build_watch_items(metrics),
        "strategy_rows": strategy_rows,
        "auto_comments": auto_comments,
        "meta": {
            "schema_version": PERFORMANCE_TUNING_SCHEMA_VERSION,
            "warnings": trade_warnings + history_warnings,
            "outcome_basis": "기준일 누적 성과 (trade review 정규화)",
            "engine_basis": "조회 구간 엔진 지표",
            "trend_basis": f"최근 {len(recent_history_dates)}개 거래일 rolling 성과" if recent_history_dates else "최근 거래일 rolling 성과",
        },
        "breakdowns": {
            "latency_reason_breakdown": [{"label": key, "count": value} for key, value in latency_reason_counts.most_common()],
            "latency_danger_reason_breakdown": [{"label": key, "count": value} for key, value in latency_danger_reason_counts.most_common()],
            "holding_ai_cache_modes": [{"label": key, "count": value} for key, value in holding_ai_cache_modes.most_common()],
            "holding_reuse_blockers": [{"label": key, "count": value} for key, value in holding_reuse_blockers.most_common()],
            "holding_sig_deltas": [{"label": key, "count": value} for key, value in holding_sig_deltas.most_common()],
            "gatekeeper_cache_modes": [{"label": key, "count": value} for key, value in gatekeeper_cache_modes.most_common()],
            "gatekeeper_reuse_blockers": [{"label": key, "count": value} for key, value in gatekeeper_reuse_blockers.most_common()],
            "gatekeeper_sig_deltas": [{"label": key, "count": value} for key, value in gatekeeper_sig_deltas.most_common()],
            "gatekeeper_actions": [{"label": key, "count": value} for key, value in gatekeeper_actions.most_common()],
            "exit_rules": [{"label": key, "count": value} for key, value in exit_rule_counts.most_common()],
            "fill_quality_cohorts": [
                {
                    "label": quality,
                    "count": len(profits),
                    "avg_profit_rate": round(sum(profits) / len(profits), 3) if profits else 0.0,
                }
                for quality, profits in sorted(fill_quality_profit_map.items(), key=lambda pair: len(pair[1]), reverse=True)
            ],
            "preset_exit_sync_status": [{"label": key, "count": value} for key, value in preset_sync_status_counts.most_common()],
            "ai_overlap_blocked_stages": [{"label": key, "count": value} for key, value in ai_overlap_blocked_stage_counts.most_common()],
            "dual_persona_agreement": [{"label": key, "count": value} for key, value in dual_persona_agreement.most_common()],
            "dual_persona_winners": [{"label": key, "count": value} for key, value in dual_persona_winners.most_common()],
            "dual_persona_decision_types": [{"label": key, "count": value} for key, value in dual_persona_decision_types.most_common()],
            "dual_persona_hard_flags": [{"label": key, "count": value} for key, value in dual_persona_hard_flags.most_common()],
        },
        "sections": {
            "swing_daily_summary": swing_daily_summary,
            "top_holding_slow": top_holding_slow,
            "top_gatekeeper_slow": top_gatekeeper_slow,
            "top_dual_persona_slow": top_dual_persona_slow,
        },
    }

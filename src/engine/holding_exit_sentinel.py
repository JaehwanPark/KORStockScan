"""Intraday HOLD/EXIT bottleneck sentinel.

This module is report-only. It reads structured holding pipeline events and
saved observation reports, classifies HOLD/EXIT anomalies, and writes
artifacts.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any

from src.engine.sentinel_event_cache import update_and_load_cached_event_rows
from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import existing_or_gzip_path, iter_jsonl
from src.utils.market_day import is_krx_trading_day

IGNORED_STOCK_NAMES = {"TEST", "DUMMY", "MOCK"}
DEFAULT_WINDOWS = (5, 10, 30)
SESSION_START = time(9, 0)
SENTINEL_END = time(15, 30)
REPORT_DIRNAME = "holding_exit_sentinel"
HOLDING_PIPELINE = "HOLDING_PIPELINE"
EVENT_CACHE_SCHEMA_VERSION = 3
EVENT_CACHE_NAME = "holding_exit_sentinel_events"
FORBIDDEN_AUTOMATIONS = [
    "auto_sell",
    "holding_threshold_relaxation",
    "holding_flow_override_mutation",
    "ai_cache_ttl_mutation",
    "bot_restart",
]


@dataclass(frozen=True)
class PipelineEvent:
    emitted_at: datetime
    pipeline: str
    stage: str
    stock_name: str
    stock_code: str
    record_id: str
    fields: dict[str, str]


def _pipeline_events_path(target_date: str) -> Path:
    return DATA_DIR / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"


def _event_cache_dir() -> Path:
    return DATA_DIR / "runtime" / "sentinel_event_cache"


def _observation_path(target_date: str) -> Path:
    return (
        DATA_DIR
        / "report"
        / "monitor_snapshots"
        / f"holding_exit_observation_{target_date}.json"
    )


def _report_dir() -> Path:
    return DATA_DIR / "report" / REPORT_DIRNAME


def _safe_str(value: Any) -> str:
    return str(value if value is not None else "").strip()


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_iso_datetime(value: str) -> datetime | None:
    text = _safe_str(value)
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _parse_target_date(target_date: str) -> date:
    return datetime.strptime(target_date, "%Y-%m-%d").date()


def _parse_as_of(target_date: str, as_of: str | None) -> datetime | None:
    text = _safe_str(as_of)
    if not text:
        return None
    parsed = _parse_iso_datetime(text)
    if parsed is not None:
        return parsed
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(f"{target_date} {text}", f"%Y-%m-%d {fmt}")
        except ValueError:
            continue
    raise ValueError(f"invalid --as-of value: {as_of}")


def _is_ignored_event(payload: dict[str, Any]) -> bool:
    return _safe_str(payload.get("stock_name")).upper() in IGNORED_STOCK_NAMES


def _payload_to_cache_row(payload: dict[str, Any]) -> dict[str, Any] | None:
    if _safe_str(payload.get("event_type")) != "pipeline_event":
        return None
    if _safe_str(payload.get("pipeline")) != HOLDING_PIPELINE:
        return None
    if _is_ignored_event(payload):
        return None
    emitted_at = _parse_iso_datetime(_safe_str(payload.get("emitted_at")))
    if emitted_at is None:
        return None
    raw_fields = payload.get("fields") or {}
    fields = {str(k): _safe_str(v) for k, v in raw_fields.items()}
    record_id = payload.get("record_id")
    if record_id in (None, "", 0):
        record_id = fields.get("id") or ""
    return {
        "emitted_at": emitted_at.isoformat(),
        "pipeline": _safe_str(payload.get("pipeline")),
        "stage": _safe_str(payload.get("stage")),
        "stock_name": _safe_str(payload.get("stock_name")),
        "stock_code": _safe_str(payload.get("stock_code"))[:6],
        "record_id": _safe_str(record_id),
        "fields": fields,
    }


def _event_from_cache_row(row: dict[str, Any]) -> PipelineEvent | None:
    emitted_at = _parse_iso_datetime(_safe_str(row.get("emitted_at")))
    if emitted_at is None:
        return None
    raw_fields = row.get("fields") or {}
    fields = (
        {str(k): _safe_str(v) for k, v in raw_fields.items()}
        if isinstance(raw_fields, dict)
        else {}
    )
    return PipelineEvent(
        emitted_at=emitted_at,
        pipeline=_safe_str(row.get("pipeline")),
        stage=_safe_str(row.get("stage")),
        stock_name=_safe_str(row.get("stock_name")),
        stock_code=_safe_str(row.get("stock_code"))[:6],
        record_id=_safe_str(row.get("record_id")),
        fields=fields,
    )


def load_pipeline_events(
    target_date: str, *, use_cache: bool = False
) -> list[PipelineEvent]:
    path = existing_or_gzip_path(_pipeline_events_path(target_date))
    if not path.exists():
        return []
    if use_cache:
        rows, _ = update_and_load_cached_event_rows(
            raw_path=path,
            cache_dir=_event_cache_dir(),
            cache_name=EVENT_CACHE_NAME,
            target_date=target_date,
            schema_version=EVENT_CACHE_SCHEMA_VERSION,
            parse_payload=_payload_to_cache_row,
        )
        events = [
            event for row in rows if (event := _event_from_cache_row(row)) is not None
        ]
        events.sort(key=lambda event: event.emitted_at)
        return events

    events: list[PipelineEvent] = []
    for payload in iter_jsonl(path):
        if _safe_str(payload.get("event_type")) != "pipeline_event":
            continue
        if _safe_str(payload.get("pipeline")) != HOLDING_PIPELINE:
            continue
        if _is_ignored_event(payload):
            continue
        emitted_at = _parse_iso_datetime(_safe_str(payload.get("emitted_at")))
        if emitted_at is None:
            continue
        raw_fields = payload.get("fields") or {}
        fields = {str(k): _safe_str(v) for k, v in raw_fields.items()}
        record_id = payload.get("record_id")
        if record_id in (None, "", 0):
            record_id = fields.get("id") or ""
        events.append(
            PipelineEvent(
                emitted_at=emitted_at,
                pipeline=_safe_str(payload.get("pipeline")),
                stage=_safe_str(payload.get("stage")),
                stock_name=_safe_str(payload.get("stock_name")),
                stock_code=_safe_str(payload.get("stock_code"))[:6],
                record_id=_safe_str(record_id),
                fields=fields,
            )
        )
    events.sort(key=lambda event: event.emitted_at)
    return events


def load_observation_report(target_date: str) -> dict[str, Any] | None:
    path = _observation_path(target_date)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def previous_trading_day_with_events(
    target_date: str, *, max_lookback_days: int = 10
) -> str | None:
    current = _parse_target_date(target_date)
    for offset in range(1, max_lookback_days + 1):
        candidate = current - timedelta(days=offset)
        if not is_krx_trading_day(candidate):
            continue
        candidate_text = candidate.isoformat()
        if existing_or_gzip_path(_pipeline_events_path(candidate_text)).exists():
            return candidate_text
    return None


def _attempt_key(event: PipelineEvent) -> str:
    if event.record_id:
        return f"id:{event.record_id}"
    if event.stock_code:
        return f"code:{event.stock_code}"
    return f"name:{event.stock_name}"


def _ratio(numerator: int, denominator: int) -> float:
    return round((numerator / denominator) * 100.0, 1) if denominator else 0.0


def _count_unique(events: list[PipelineEvent], stage: str) -> int:
    return len({_attempt_key(event) for event in events if event.stage == stage})


def _is_false_like(value: str) -> bool:
    return _safe_str(value).lower() in {"0", "false", "no", "n"}


def _is_true_like(value: str) -> bool:
    return _safe_str(value).lower() in {"1", "true", "yes", "y"}


def _is_non_real_observation(event: PipelineEvent) -> bool:
    fields = event.fields
    if _is_false_like(fields.get("actual_order_submitted", "")):
        return True
    if _is_true_like(fields.get("broker_order_forbidden", "")):
        return True
    if _is_true_like(fields.get("simulated_order", "")):
        return True
    if fields.get("simulation_book") or fields.get("simulation_owner"):
        return True
    if _is_true_like(fields.get("swing_intraday_probe", "")):
        return True
    if fields.get("probe_id") or fields.get("probe_origin_stage"):
        return True
    if (
        "sim_" in event.stage
        or "_probe_" in event.stage
        or event.stage.startswith("swing_probe_")
    ):
        return True
    return False


def _non_real_attempt_keys(events: list[PipelineEvent]) -> set[str]:
    """Propagate probe/sim provenance to sparse sibling events with the same record id."""
    return {
        _attempt_key(event)
        for event in events
        if _attempt_key(event) and _is_non_real_observation(event)
    }


def _is_explicit_real_sell_execution(event: PipelineEvent) -> bool:
    """Return whether a sell event proves a real broker submission or fill."""
    if event.stage not in {"sell_order_sent", "sell_completed"}:
        return False
    if _is_non_real_observation(event):
        return False
    fields = event.fields
    if _is_true_like(fields.get("actual_order_submitted", "")):
        return True
    if event.stage == "sell_order_sent":
        order_no = _safe_str(
            fields.get("ord_no")
            or fields.get("order_no")
            or fields.get("broker_order_no")
        ).strip().lower()
        return bool(order_no and order_no not in {"-", "0", "none", "null"})
    return False


def _real_sell_execution_attempt_keys(events: list[PipelineEvent]) -> set[str]:
    """Prefer explicit broker evidence over counterfactual siblings on the same record."""
    return {
        _attempt_key(event)
        for event in events
        if _attempt_key(event) and _is_explicit_real_sell_execution(event)
    }


def _count_cache_miss(events: list[PipelineEvent]) -> int:
    return sum(
        1
        for event in events
        if event.stage == "ai_holding_review" and event.fields.get("ai_cache") == "miss"
    )


def _count_parse_fail(events: list[PipelineEvent]) -> int:
    return sum(
        1
        for event in events
        if event.stage in {"ai_holding_review", "holding_flow_override_review"}
        and event.fields.get("ai_parse_fail") in {"1", "True", "true", "YES", "yes"}
    )


def _score50_origin_counts(events: list[PipelineEvent]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for event in events:
        if event.stage not in {
            "ai_holding_review",
            "ai_holding_fast_reuse_band",
            "ai_holding_reuse_bypass",
            "ai_holding_skip_unchanged",
            "bad_entry_refined_candidate",
        }:
            continue
        fields = event.fields
        origin = _safe_str(fields.get("holding_score_score50_origin")).strip()
        if origin and origin not in {"-", "none", "null"}:
            counter[origin] += 1
            continue
        score_values = (
            fields.get("holding_score_effective"),
            fields.get("ai_score"),
            fields.get("current_ai_score"),
        )
        if any(_safe_float(value, -1.0) == 50.0 for value in score_values):
            counter["legacy_or_unclassified_score50"] += 1
    return dict(sorted(counter.items()))


def _max_field(events: list[PipelineEvent], stage: str, field: str) -> float:
    values = [
        _safe_float(event.fields.get(field), 0.0)
        for event in events
        if event.stage == stage
    ]
    return max(values) if values else 0.0


TERMINAL_HOLDING_STAGES = {"sell_completed"}
ACTIVE_HOLDING_STAGES = {
    "holding_started",
    "position_rebased_after_fill",
    "ai_holding_fast_reuse_band",
    "ai_holding_reuse_bypass",
    "ai_holding_review",
    "ai_holding_skip_unchanged",
    "bad_entry_refined_candidate",
    "exit_signal",
    "holding_flow_override_candidate_cleared",
    "holding_flow_override_defer_exit",
    "holding_flow_override_exit_confirmed",
    "holding_flow_override_force_exit",
    "holding_flow_override_review",
    "reversal_add_blocked_reason",
    "reversal_add_gate_blocked",
    "scale_in_price_guard_block",
    "scale_in_qty_block",
    "sell_order_sent",
    "soft_stop_expert_shadow",
    "soft_stop_micro_grace",
    "stat_action_decision_snapshot",
}


def _active_holding_keys(events: list[PipelineEvent]) -> set[str]:
    last_by_key: dict[str, PipelineEvent] = {}
    for event in events:
        key = _attempt_key(event)
        if not key:
            continue
        last_by_key[key] = event
    return {
        key
        for key, event in last_by_key.items()
        if event.stage in ACTIVE_HOLDING_STAGES
        and event.stage not in TERMINAL_HOLDING_STAGES
    }


def _stage_reason_top(events: list[PipelineEvent]) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for event in events:
        if event.stage == "holding_flow_override_defer_exit":
            key = f"flow유예:{event.fields.get('exit_rule') or '-'}"
        elif event.stage == "exit_signal":
            key = f"청산신호:{event.fields.get('exit_rule') or event.fields.get('reason') or '-'}"
        elif event.stage == "ai_holding_review":
            key = f"AI보유감시:cache_{event.fields.get('ai_cache') or '-'}"
        elif event.stage == "soft_stop_micro_grace":
            key = "soft_stop_grace"
        elif event.stage in {"sell_order_sent", "sell_completed"}:
            key = event.stage
        else:
            continue
        counter[key] += 1
    return [
        {"label": label, "count": count} for label, count in counter.most_common(10)
    ]


def _summarize_events(
    events: list[PipelineEvent], *, start_at: datetime, end_at: datetime
) -> dict[str, Any]:
    scoped = [event for event in events if start_at <= event.emitted_at <= end_at]
    non_real_keys = _non_real_attempt_keys(scoped)
    real_sell_keys = _real_sell_execution_attempt_keys(scoped)
    real_scoped = [
        event
        for event in scoped
        if not _is_non_real_observation(event)
        and (
            _attempt_key(event) in real_sell_keys
            or _attempt_key(event) not in non_real_keys
        )
    ]
    non_real_scoped = [
        event
        for event in scoped
        if _is_non_real_observation(event)
        or (
            _attempt_key(event) in non_real_keys
            and _attempt_key(event) not in real_sell_keys
        )
    ]
    stage_events = Counter(event.stage for event in scoped)
    stage_unique = {
        stage: len({_attempt_key(event) for event in scoped if event.stage == stage})
        for stage in sorted(set(stage_events))
    }
    exit_signal = int(stage_unique.get("exit_signal", 0) or 0)
    sell_sent = int(stage_unique.get("sell_order_sent", 0) or 0)
    sell_completed = int(stage_unique.get("sell_completed", 0) or 0)
    real_exit_signal = _count_unique(real_scoped, "exit_signal")
    real_sell_sent = _count_unique(real_scoped, "sell_order_sent")
    real_sell_completed = _count_unique(real_scoped, "sell_completed")
    non_real_exit_signal = _count_unique(non_real_scoped, "exit_signal")
    non_real_sell_sent = _count_unique(non_real_scoped, "sell_order_sent")
    non_real_sell_completed = _count_unique(non_real_scoped, "sell_completed")
    stage_unique.update(
        {
            "real_exit_signal": real_exit_signal,
            "real_sell_order_sent": real_sell_sent,
            "real_sell_completed": real_sell_completed,
            "non_real_exit_signal": non_real_exit_signal,
            "non_real_sell_order_sent": non_real_sell_sent,
            "non_real_sell_completed": non_real_sell_completed,
        }
    )
    flow_defer = int(stage_events.get("holding_flow_override_defer_exit", 0) or 0)
    flow_review = int(stage_events.get("holding_flow_override_review", 0) or 0)
    ai_review = int(stage_events.get("ai_holding_review", 0) or 0)
    cache_miss = _count_cache_miss(scoped)
    score50_origin_counts = _score50_origin_counts(scoped)
    active_keys = _active_holding_keys(scoped)
    latest_event_at = (
        scoped[-1].emitted_at.isoformat(timespec="seconds") if scoped else None
    )
    return {
        "start_at": start_at.isoformat(timespec="seconds"),
        "end_at": end_at.isoformat(timespec="seconds"),
        "event_count": len(scoped),
        "latest_event_at": latest_event_at,
        "stage_events": dict(sorted(stage_events.items())),
        "stage_unique": stage_unique,
        "reason_top": _stage_reason_top(scoped),
        "score50_origin_counts": score50_origin_counts,
        "holding_score_preflight_blocked_events": int(
            score50_origin_counts.get("preflight_source_quality_blocked", 0)
        ),
        "holding_score_raw_non50_neutralized_events": int(
            score50_origin_counts.get("post_call_source_quality_neutralized", 0)
        ),
        "max_defer_worsen_pct": round(
            _max_field(scoped, "holding_flow_override_defer_exit", "worsen_pct"), 3
        ),
        "max_force_worsen_pct": round(
            _max_field(scoped, "holding_flow_override_force_exit", "profit_rate"), 3
        ),
        "ai_parse_fail_events": _count_parse_fail(scoped),
        "ratios": {
            "sell_sent_to_exit_signal_unique_pct": _ratio(sell_sent, exit_signal),
            "sell_completed_to_exit_signal_unique_pct": _ratio(
                sell_completed, exit_signal
            ),
            "real_sell_sent_to_exit_signal_unique_pct": _ratio(
                real_sell_sent, real_exit_signal
            ),
            "non_real_sell_sent_to_exit_signal_unique_pct": _ratio(
                non_real_sell_sent, non_real_exit_signal
            ),
            "flow_defer_to_review_event_pct": _ratio(flow_defer, flow_review),
            "ai_cache_miss_pct": _ratio(cache_miss, ai_review),
        },
        "unique_symbols": {
            "holding_started": len(
                {
                    _attempt_key(event)
                    for event in scoped
                    if event.stage == "holding_started"
                }
            ),
            "exit_signal": exit_signal,
            "sell_order_sent": sell_sent,
            "sell_completed": sell_completed,
            "real_exit_signal": real_exit_signal,
            "real_sell_order_sent": real_sell_sent,
            "real_sell_completed": real_sell_completed,
            "non_real_exit_signal": non_real_exit_signal,
            "non_real_sell_order_sent": non_real_sell_sent,
            "non_real_sell_completed": non_real_sell_completed,
            "active_holding": len(active_keys),
        },
    }


def _same_time_on_date(target_date: str, source: datetime) -> datetime:
    return datetime.combine(_parse_target_date(target_date), source.time())


def _observation_metrics(observation: dict[str, Any] | None) -> dict[str, Any]:
    if not observation:
        return {}
    soft_stop = observation.get("soft_stop_rebound") or {}
    trailing = {}
    for item in observation.get("exit_rule_quality") or []:
        if item.get("exit_rule") == "scalp_trailing_take_profit":
            trailing = item
            break
    return {
        "soft_stop_total": int(soft_stop.get("total_soft_stop") or 0),
        "soft_stop_rebound_above_sell_10m_rate": _safe_float(
            soft_stop.get("rebound_above_sell_10m_rate"),
            0.0,
        ),
        "trailing_evaluated": int(trailing.get("evaluated_post_sell") or 0),
        "trailing_missed_upside_rate": _safe_float(
            trailing.get("missed_upside_rate"), 0.0
        ),
    }


def _classify(
    summary: dict[str, Any],
    baseline: dict[str, Any] | None,
    observation_metrics: dict[str, Any],
    *,
    as_of: datetime,
) -> dict[str, Any]:
    stage_events = summary["stage_events"]
    unique = summary["stage_unique"]
    ratios = summary["ratios"]
    latest = _parse_iso_datetime(_safe_str(summary.get("latest_event_at")))
    stale_sec = int((as_of - latest).total_seconds()) if latest else None
    during_sentinel_hours = SESSION_START <= as_of.time() <= SENTINEL_END

    exit_signal = int(unique.get("exit_signal", 0) or 0)
    sell_sent = int(unique.get("sell_order_sent", 0) or 0)
    real_exit_signal = int(unique.get("real_exit_signal", 0) or 0)
    real_sell_sent = int(unique.get("real_sell_order_sent", 0) or 0)
    non_real_exit_signal = int(unique.get("non_real_exit_signal", 0) or 0)
    non_real_sell_sent = int(unique.get("non_real_sell_order_sent", 0) or 0)
    flow_defer = int(stage_events.get("holding_flow_override_defer_exit", 0) or 0)
    force_exit = int(stage_events.get("holding_flow_override_force_exit", 0) or 0)
    exit_confirmed = int(
        stage_events.get("holding_flow_override_exit_confirmed", 0) or 0
    )
    ai_review = int(stage_events.get("ai_holding_review", 0) or 0)
    active_holding = int(
        summary.get("unique_symbols", {}).get("active_holding", 0) or 0
    )

    matches: list[str] = []
    reasons: list[str] = []

    if during_sentinel_hours and summary["event_count"] == 0:
        matches.append("RUNTIME_OPS")
        reasons.append("holding pipeline event stream is empty during sentinel hours")
    elif (
        during_sentinel_hours
        and stale_sec is not None
        and stale_sec > 900
        and ai_review > 0
        and active_holding > 0
    ):
        matches.append("RUNTIME_OPS")
        reasons.append(
            "holding pipeline event stream is stale while active holdings remain"
        )

    if real_exit_signal >= 1 and real_sell_sent < real_exit_signal:
        matches.append("SELL_EXECUTION_DROUGHT")
        reasons.append("real exit_signal is not fully followed by real sell_order_sent")
    elif non_real_exit_signal >= 1 and non_real_sell_sent < non_real_exit_signal:
        reasons.append(
            "non-real exit_signal has no broker sell_order_sent; report-only provenance split"
        )

    if flow_defer >= 3 or force_exit >= 1 or exit_confirmed >= 2:
        matches.append("HOLD_DEFER_DANGER")
        reasons.append("holding_flow_override defer/force/confirm events are elevated")

    if ai_review >= 5 and (
        ratios.get("ai_cache_miss_pct", 0.0) >= 90.0
        or summary.get("ai_parse_fail_events", 0) > 0
    ):
        matches.append("AI_HOLDING_OPS")
        reasons.append("AI holding review cache miss or parse failure is elevated")

    if (
        observation_metrics.get("soft_stop_total", 0) >= 5
        and observation_metrics.get("soft_stop_rebound_above_sell_10m_rate", 0.0)
        >= 70.0
    ):
        matches.append("SOFT_STOP_WHIPSAW")
        reasons.append("soft stop rebound rate is high in saved observation")

    if (
        observation_metrics.get("trailing_evaluated", 0) >= 5
        and observation_metrics.get("trailing_missed_upside_rate", 0.0) >= 30.0
    ):
        matches.append("TRAILING_EARLY_EXIT")
        reasons.append("trailing missed-upside rate is high in saved observation")

    priority = [
        "RUNTIME_OPS",
        "SELL_EXECUTION_DROUGHT",
        "HOLD_DEFER_DANGER",
        "AI_HOLDING_OPS",
        "SOFT_STOP_WHIPSAW",
        "TRAILING_EARLY_EXIT",
    ]
    primary = next((item for item in priority if item in matches), "NORMAL")
    secondary = [item for item in matches if item != primary]
    if primary == "NORMAL":
        reasons.append("no HOLD/EXIT sentinel threshold breached")

    return {
        "primary": primary,
        "secondary": secondary,
        "matches": matches,
        "reasons": reasons,
        "stale_sec": stale_sec,
        "baseline_sell_sent_to_exit_signal_unique_pct": (
            (baseline or {})
            .get("ratios", {})
            .get("sell_sent_to_exit_signal_unique_pct")
        ),
        "sell_execution_scope": {
            "real_exit_signal": real_exit_signal,
            "real_sell_order_sent": real_sell_sent,
            "non_real_exit_signal": non_real_exit_signal,
            "non_real_sell_order_sent": non_real_sell_sent,
        },
        "live_runtime_effect": False,
        "forbidden_automations": FORBIDDEN_AUTOMATIONS,
    }


def _recommend_actions(classification: dict[str, Any]) -> list[str]:
    primary = classification.get("primary")
    if primary == "SELL_EXECUTION_DROUGHT":
        return ["Check sell order receipt/order path before changing exit thresholds."]
    if primary == "HOLD_DEFER_DANGER":
        return [
            "Review holding_flow_override defer examples and worsen floor evidence."
        ]
    if primary == "AI_HOLDING_OPS":
        return [
            "Review AI cache/provenance/parse telemetry; do not mutate cache TTL automatically."
        ]
    if primary == "SOFT_STOP_WHIPSAW":
        return ["Append soft-stop rebound examples to postclose threshold review."]
    if primary == "TRAILING_EARLY_EXIT":
        return ["Append trailing missed-upside examples to postclose threshold review."]
    if primary == "RUNTIME_OPS":
        return [
            "Check holding pipeline event freshness; restart only after explicit approval."
        ]
    return ["Continue monitoring; no dynamic action required."]


def _followup_route(classification: dict[str, Any]) -> dict[str, Any]:
    primary = classification.get("primary")
    scope = classification.get("sell_execution_scope") or {}
    if primary == "RUNTIME_OPS":
        return {
            "route": "holding_runtime_ops_playbook",
            "owner": "operator_review",
            "operator_action_required": True,
            "runtime_effect": "report_only_no_mutation",
            "next_artifact": "incident_playbook_review",
        }
    if primary == "SELL_EXECUTION_DROUGHT":
        return {
            "route": "sell_receipt_order_path_check",
            "owner": "postclose_holding_exit_attribution",
            "operator_action_required": bool(scope.get("real_exit_signal", 0)),
            "runtime_effect": "report_only_no_mutation",
            "next_artifact": "trade_lifecycle_attribution",
        }
    if primary == "HOLD_DEFER_DANGER":
        return {
            "route": "holding_flow_defer_cost_review",
            "owner": "postclose_threshold_cycle",
            "operator_action_required": False,
            "runtime_effect": "report_only_no_mutation",
            "next_artifact": "holding_exit_observation",
        }
    if primary == "AI_HOLDING_OPS":
        return {
            "route": "ai_holding_provenance_review",
            "owner": "runtime_stability_review",
            "operator_action_required": False,
            "runtime_effect": "report_only_no_mutation",
            "next_artifact": "holding_exit_sentinel",
        }
    if primary == "SOFT_STOP_WHIPSAW":
        return {
            "route": "soft_stop_whipsaw_calibration_review",
            "owner": "postclose_threshold_cycle",
            "operator_action_required": False,
            "runtime_effect": "report_only_no_mutation",
            "next_artifact": "threshold_cycle_calibration_source_bundle",
        }
    if primary == "TRAILING_EARLY_EXIT":
        return {
            "route": "trailing_continuation_report_only_review",
            "owner": "postclose_threshold_cycle",
            "operator_action_required": False,
            "runtime_effect": "report_only_no_mutation",
            "next_artifact": "threshold_cycle_calibration_source_bundle",
        }
    return {
        "route": "normal_no_action",
        "owner": "none",
        "operator_action_required": False,
        "runtime_effect": "report_only_no_mutation",
        "next_artifact": "none",
    }


def build_holding_exit_sentinel_report(
    target_date: str,
    *,
    as_of: datetime | None = None,
    windows_min: tuple[int, ...] = DEFAULT_WINDOWS,
    dry_run: bool = False,
    use_cache: bool = False,
) -> dict[str, Any]:
    events = load_pipeline_events(target_date, use_cache=use_cache)
    if as_of is None:
        if dry_run and events:
            as_of = events[-1].emitted_at
        else:
            as_of = datetime.now()

    session_start = datetime.combine(_parse_target_date(target_date), SESSION_START)
    session_summary = _summarize_events(events, start_at=session_start, end_at=as_of)
    windows = {}
    for minutes in sorted(set(windows_min)):
        start_at = max(session_start, as_of - timedelta(minutes=minutes))
        windows[f"{minutes}m"] = _summarize_events(
            events, start_at=start_at, end_at=as_of
        )

    baseline_date = previous_trading_day_with_events(target_date)
    baseline_summary = None
    if baseline_date:
        baseline_events = load_pipeline_events(baseline_date, use_cache=use_cache)
        baseline_start = datetime.combine(
            _parse_target_date(baseline_date), SESSION_START
        )
        baseline_end = _same_time_on_date(baseline_date, as_of)
        baseline_summary = _summarize_events(
            baseline_events, start_at=baseline_start, end_at=baseline_end
        )

    observation = load_observation_report(target_date)
    obs_metrics = _observation_metrics(observation)
    classification = _classify(
        session_summary, baseline_summary, obs_metrics, as_of=as_of
    )
    followup = _followup_route(classification)

    return {
        "schema_version": 2,
        "report_type": "holding_exit_sentinel",
        "target_date": target_date,
        "as_of": as_of.isoformat(timespec="seconds"),
        "dry_run": bool(dry_run),
        "event_load": {
            "cache_enabled": bool(use_cache),
            "cache_name": EVENT_CACHE_NAME if use_cache else None,
            "cache_schema_version": EVENT_CACHE_SCHEMA_VERSION if use_cache else None,
        },
        "policy": {
            "report_only": True,
            "live_runtime_effect": False,
            "allowed_automations": [
                "json_report",
                "markdown_report",
                "action_recommendation",
            ],
            "forbidden_automations": FORBIDDEN_AUTOMATIONS,
        },
        "baseline": {"date": baseline_date, "same_time_summary": baseline_summary},
        "current": {"session": session_summary, "windows": windows},
        "observation": {
            "path": str(_observation_path(target_date)),
            "metrics": obs_metrics,
        },
        "classification": classification,
        "followup": followup,
        "recommended_actions": _recommend_actions(classification),
    }


def _format_top(items: list[dict[str, Any]], *, limit: int = 5) -> str:
    if not items:
        return "-"
    return ", ".join(f"{item['label']}={item['count']}" for item in items[:limit])


def build_markdown(report: dict[str, Any]) -> str:
    session = report["current"]["session"]
    unique = session["stage_unique"]
    ratios = session["ratios"]
    classification = report["classification"]
    obs = report["observation"]["metrics"]
    lines = [
        f"# HOLD/EXIT Sentinel {report['target_date']}",
        "",
        "## 판정",
        "",
        f"- primary: `{classification['primary']}`",
        f"- secondary: `{', '.join(classification['secondary']) if classification['secondary'] else '-'}`",
        f"- report_only: `{str(report['policy']['report_only']).lower()}`",
        f"- live_runtime_effect: `{str(report['policy']['live_runtime_effect']).lower()}`",
        f"- operator_action_required: `{str(report['followup']['operator_action_required']).lower()}`",
        f"- followup_route: `{report['followup']['route']}`",
        f"- followup_owner: `{report['followup']['owner']}`",
        f"- runtime_effect: `{report['followup']['runtime_effect']}`",
        "",
        "## 근거",
        "",
        f"- as_of: `{report['as_of']}`",
        f"- exit_signal unique: `{unique.get('exit_signal', 0)}`",
        f"- sell_order_sent unique: `{unique.get('sell_order_sent', 0)}`",
        f"- sell_completed unique: `{unique.get('sell_completed', 0)}`",
        f"- real exit/sell_sent/sell_completed: `{unique.get('real_exit_signal', 0)}` / "
        f"`{unique.get('real_sell_order_sent', 0)}` / `{unique.get('real_sell_completed', 0)}`",
        f"- non-real exit/sell_sent/sell_completed: `{unique.get('non_real_exit_signal', 0)}` / "
        f"`{unique.get('non_real_sell_order_sent', 0)}` / `{unique.get('non_real_sell_completed', 0)}`",
        f"- sell_sent/exit_signal: `{ratios.get('sell_sent_to_exit_signal_unique_pct', 0.0)}%`",
        f"- real sell_sent/exit_signal: `{ratios.get('real_sell_sent_to_exit_signal_unique_pct', 0.0)}%`",
        f"- non-real sell_sent/exit_signal: `{ratios.get('non_real_sell_sent_to_exit_signal_unique_pct', 0.0)}%`",
        f"- flow defer events: `{session['stage_events'].get('holding_flow_override_defer_exit', 0)}`",
        f"- AI holding cache MISS: `{ratios.get('ai_cache_miss_pct', 0.0)}%`",
        f"- score50 origins: `{session.get('score50_origin_counts') or {}}`",
        f"- score50 preflight/source-quality blocked: `{session.get('holding_score_preflight_blocked_events', 0)}`",
        f"- score50 raw-non50 neutralized: `{session.get('holding_score_raw_non50_neutralized_events', 0)}`",
        f"- soft_stop rebound above sell 10m: `{obs.get('soft_stop_rebound_above_sell_10m_rate', 0.0)}%`",
        f"- trailing missed-upside: `{obs.get('trailing_missed_upside_rate', 0.0)}%`",
        f"- top reasons: `{_format_top(session['reason_top'])}`",
        "",
        "## 금지된 자동변경",
        "",
    ]
    lines.extend(f"- `{item}`" for item in report["policy"]["forbidden_automations"])
    lines.extend(["", "## 권고 액션", ""])
    lines.extend(f"- {item}" for item in report["recommended_actions"])
    return "\n".join(lines) + "\n"


def save_report_artifacts(report: dict[str, Any]) -> dict[str, str]:
    target_date = report["target_date"]
    report_dir = _report_dir()
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / f"holding_exit_sentinel_{target_date}.json"
    md_path = report_dir / f"holding_exit_sentinel_{target_date}.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    md_path.write_text(build_markdown(report), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build intraday HOLD/EXIT sentinel report."
    )
    parser.add_argument(
        "--date", dest="target_date", default=datetime.now().strftime("%Y-%m-%d")
    )
    parser.add_argument("--as-of", dest="as_of", default="")
    parser.add_argument(
        "--window-min", dest="window_min", action="append", type=int, default=[]
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--use-cache",
        action="store_true",
        help="Use slim incremental sentinel event cache.",
    )
    parser.add_argument("--print-json", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    as_of = _parse_as_of(args.target_date, args.as_of) if args.as_of else None
    windows = tuple(args.window_min) if args.window_min else DEFAULT_WINDOWS
    report = build_holding_exit_sentinel_report(
        args.target_date,
        as_of=as_of,
        windows_min=windows,
        dry_run=bool(args.dry_run),
        use_cache=bool(args.use_cache),
    )
    artifacts = save_report_artifacts(report)
    result = {
        "status": "success",
        "target_date": args.target_date,
        "classification": report["classification"]["primary"],
        "secondary": report["classification"]["secondary"],
        "artifacts": artifacts,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.print_json else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

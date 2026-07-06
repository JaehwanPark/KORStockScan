from __future__ import annotations

import argparse
import gzip
import json
import time
from collections import Counter, defaultdict
from datetime import datetime, time as dt_time
from pathlib import Path
from typing import Any

from src.engine.scalping.rising_missed_one_share_entry import (
    BLOCK_ENTRY_AI_NOT_EVALUATED,
    RISING_MISSED_CLASS_ACTIONABLE_MAJOR,
    RISING_MISSED_CLASS_INTENDED_GUARD_PRESERVED,
    RISING_MISSED_CLASS_NOT_RISING,
    RISING_MISSED_CLASS_RUNTIME_BACKPRESSURE,
    RISING_MISSED_CLASS_SOURCE_QUALITY_EXCLUDED,
    RISING_MISSED_CLASS_STRATEGY_REJECT,
    RISING_MISSED_CLASS_SUBMITTED_RESOLVED,
    classify_rising_missed_candidate,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENTRY_PIPELINE = "ENTRY_PIPELINE"
PROMOTED_STAGE = "scalping_scanner_candidate_promoted"
REAL_SUBMIT_TRUE = "true"
RISING_MISSED_FORCED_ENTRY_REASON = "rising_missed_one_share_entry"
RISING_MISSED_FORCED_LINEAGE_WINDOW_SEC = 180
RISING_MISSED_FORCED_LINEAGE_STAGES = {
    "latency_pass",
    "order_bundle_submitted",
    "holding_started",
}

BLOCKER_STAGES = {
    "ai_confirmed_terminal_no_budget",
    "blocked_ai_score",
    "blocked_gap_from_scan",
    "blocked_liquidity",
    "blocked_overbought",
    "blocked_strength_momentum",
    "blocked_vpw",
    "first_ai_wait",
    "latency_block",
    "score65_74_recovery_probe_blocked",
    "scalping_scanner_watch_eviction",
    "scalping_scanner_watching_runtime_skip",
    "same_symbol_loss_reentry_cooldown",
    "scalping_scanner_runtime_target_attach",
}

RECOVERY_OBSERVATION_REASONS = {
    "scanner_fast_precheck_subscription_recheck_snapshot_applied",
    "scanner_fast_precheck_stale_ws_recovered",
    "scanner_heavy_eval_stale_snapshot_recheck",
    "ws_snapshot_missing_or_zero_recovered",
}

BUY_WINDOW_PAUSE_REASONS = {
    "before_strategy_start",
    "outside_scalping_buy_window",
    "scalping_new_buy_cutoff",
}

QUEUE_STAGES = {
    "scalping_scanner_fast_precheck",
    "scalping_scanner_heavy_eval_lag",
    "scalping_scanner_runtime_queue_lag",
}

ENTRY_PRICE_STAGES = {
    "entry_ai_price_canary_applied",
    "entry_ai_price_canary_fallback",
    "entry_ai_price_canary_skip_order",
    "entry_submit_revalidation_warning",
    "entry_submit_revalidation_block",
    "pre_submit_price_guard_block",
    "entry_order_cancel_requested",
    "entry_order_cancel_confirmed",
    "entry_order_cancel_failed",
}

SCALE_IN_STAGES = {
    "scale_in_price_resolved",
    "scale_in_price_guard_block",
    "scale_in_p2_observe",
    "scale_in_executed",
    "stat_action_decision_snapshot",
}

ACTIONABLE_BLOCKER_STAGE_PRIORITY = {
    "latency_block": 100,
    "entry_submit_revalidation_block": 95,
    "pre_submit_price_guard_block": 90,
}

SCALE_IN_REASON_TOKENS = {
    "scale_in",
    "avg_down",
    "pyramid",
    "profit_not_enough",
    "pnl_out_of_range",
    "add_judgment",
    "hold_sec_out_of_range",
    "low_broken",
    "ai_not_recovering",
    "spread_bps",
    "flow_hold",
}

RELIEF_BLOCKER_REASONS = {
    "scanner_full_eval_loop_budget_deferred",
    "entry_cooldown_active",
    "same_symbol_loss_reentry_cooldown",
    "scalping_new_buy_cutoff",
    "outside_scalping_buy_window",
    "ws_snapshot_missing_or_zero",
    "ws_snapshot_missing_or_zero_recovered",
}

SELECTION_PRIOR_RISK_RECOMMENDATIONS = {
    "source_quality_blocked",
    "loss_filter",
    "quality_risk",
}

SELECTION_PRIOR_SORT_ORDER = {
    "positive_prior": 0,
    "recheck_prior": 1,
    "hold_sample": 2,
    "unavailable": 3,
    "quality_risk": 4,
    "loss_filter": 5,
    "source_quality_blocked": 6,
}

LOW_AI_SCORE_CUTOFF = 65.0
NEGATIVE_BUY_PRESSURE_CUTOFF = 0.0
ENTRY_FRESH_MAX_AGE_MS = 3000.0
ZERO_HISTORY_WORKORDER_MIN_EVENTS = 2
DEFAULT_BUY_WINDOW_START = dt_time(9, 0)
DEFAULT_BUY_WINDOW_END = dt_time(15, 20)
ACTIONABLE_FULL_EVAL_DEFERRED_MIN_COUNT = 2
ACTIONABLE_FULL_EVAL_DEFERRED_MIN_DELTA_PCT = 1.0
LATENCY_DANGER_SPREAD_RATIO_CAP = 0.0100
LATENCY_DANGER_WS_AGE_MS_CAP = 450.0

LATENCY_PROVENANCE_FIELD_KEYS = (
    "latency_state",
    "latency_danger_reasons",
    "spread_ratio",
    "pre_submit_quote_refresh_spread_ratio",
    "ws_age_ms",
    "pre_submit_effective_quote_age_ms",
    "pre_submit_ws_snapshot_refresh_age_ms",
    "pre_submit_effective_quote_stale",
    "quote_stale_at_submit",
    "quote_stale",
    "orderbook_micro_spread_ticks",
    "orderbook_micro_state",
    "orderbook_micro_ofi_bucket_key",
    "orderbook_micro_calibration_bucket",
)
ACTIONABLE_COOLDOWN_MIN_COUNT = 2
ACTIONABLE_COOLDOWN_MIN_DELTA_PCT = 1.0

STRENGTH_HISTORY_COUNT_KEYS = (
    "fast_precheck_observed_ws_strength_history_count",
    "ws_strength_history_count",
    "strength_momentum_history_count",
    "pre_ai_ws_snapshot_refresh_history_count",
    "refresh_history_count",
)

ENTRY_AI_ACTION_FIELD_KEYS = (
    "rising_missed_entry_ai_action",
    "entry_ai_action",
    "ai_action",
    "action",
    "last_ai_action",
    "current_ai_action",
    "last_watching_ai_action",
)

ENTRY_AI_ACTION_PRIORITY_STAGES = (
    "order_bundle_submitted",
    "scalp_entry_action_decision_snapshot",
    "ai_confirmed",
    "blocked_ai_score",
    "ai_confirmed_terminal_no_budget",
    "first_ai_wait",
)


def _safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None:
            return default
        text = str(value).strip()
        if text.lower() in {"", "none", "nan", "nat", "inf", "+inf", "-inf"}:
            return default
        if text.startswith("not_applicable"):
            return default
        return float(text.replace("%", "").replace("+", ""))
    except Exception:
        return default


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    opener = gzip.open if path.suffix == ".gz" else Path.open
    with opener(path, mode="rt", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def _exclude_from_real_entry_analysis(row: dict[str, Any]) -> bool:
    stage = str(row.get("stage") or "")
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    if stage.startswith("scalp_sim_") or stage.startswith("swing_"):
        return True
    if str(fields.get("simulated_order") or "").strip().lower() == "true":
        return True
    if any(fields.get(key) not in (None, "") for key in ("simulation_book", "simulation_owner", "sim_record_id")):
        return True
    if str(fields.get("reason") or "").strip() == "scalp_live_simulator":
        return True
    if _is_rising_missed_forced_one_share_entry(fields):
        return True
    authority = str(fields.get("decision_authority") or "").lower()
    return "sim_" in authority or "swing_" in authority


def _is_rising_missed_forced_one_share_entry(fields: dict[str, Any]) -> bool:
    reason = str(fields.get("forced_entry_reason") or "").strip()
    forced = str(fields.get("rising_missed_one_share_entry_forced") or "").strip().lower() == "true"
    qty = _safe_float(fields.get("forced_entry_qty"))
    one_share_or_missing = qty is None or qty == 1.0
    return one_share_or_missing and (reason == RISING_MISSED_FORCED_ENTRY_REASON or forced)


def _parse_event_dt(row: dict[str, Any]) -> datetime | None:
    value = _event_time(row)
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed.replace(tzinfo=None)


def _forced_lineage_qty_is_one(fields: dict[str, Any]) -> bool:
    for key in ("forced_entry_qty", "order_requested_qty", "order_quantity", "quantity", "qty", "fill_qty", "order_filled_qty"):
        value = _safe_float(fields.get(key))
        if value == 1.0:
            return True
    return False


def _is_rising_missed_forced_lineage_row(
    row: dict[str, Any],
    latest_forced_scout_at_by_code: dict[str, datetime],
) -> bool:
    code = str(row.get("stock_code") or "").strip()
    forced_at = latest_forced_scout_at_by_code.get(code)
    event_at = _parse_event_dt(row)
    if forced_at is None or event_at is None:
        return False
    elapsed_sec = (event_at - forced_at).total_seconds()
    if elapsed_sec < 0 or elapsed_sec > RISING_MISSED_FORCED_LINEAGE_WINDOW_SEC:
        return False
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    stage = str(row.get("stage") or "")
    actual_submitted = str(fields.get("actual_order_submitted") or "").strip().lower() == REAL_SUBMIT_TRUE
    return stage in RISING_MISSED_FORCED_LINEAGE_STAGES or actual_submitted or _forced_lineage_qty_is_one(fields)


def _entry_events(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    latest_forced_scout_at_by_code: dict[str, datetime] = {}
    for row in rows:
        if row.get("pipeline") != ENTRY_PIPELINE:
            continue
        code = str(row.get("stock_code") or "").strip()
        fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
        if _is_rising_missed_forced_one_share_entry(fields):
            event_at = _parse_event_dt(row)
            if code and event_at is not None:
                latest_forced_scout_at_by_code[code] = event_at
            continue
        if _is_rising_missed_forced_lineage_row(row, latest_forced_scout_at_by_code):
            continue
        if _exclude_from_real_entry_analysis(row):
            continue
        if not code or code == "-":
            continue
        grouped[code].append(row)
    return dict(grouped)


def _field(row: dict[str, Any], key: str, default: Any = "") -> Any:
    fields = row.get("fields")
    if not isinstance(fields, dict):
        return default
    return fields.get(key, default)


def _selection_prior_recommendation(item: dict[str, Any]) -> str:
    for blocker in reversed(item.get("recent_blockers") or []):
        recommendation = str(blocker.get("rising_missed_selection_recommendation") or "").strip()
        if recommendation:
            return recommendation
    deferred = item.get("scanner_full_eval_budget_deferred")
    if isinstance(deferred, dict):
        recommendation = str(deferred.get("rising_missed_selection_recommendation") or "").strip()
        if recommendation:
            return recommendation
    return "unavailable"


def _selection_prior_counts(items: list[dict[str, Any]]) -> Counter[str]:
    return Counter(_selection_prior_recommendation(item) for item in items)


def _selection_prior_sort_key(item: dict[str, Any]) -> tuple[int, float]:
    recommendation = _selection_prior_recommendation(item)
    return (
        SELECTION_PRIOR_SORT_ORDER.get(recommendation, SELECTION_PRIOR_SORT_ORDER["unavailable"]),
        -(item.get("max_price_delta_since_first_seen_pct") or -999.0),
    )


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _entry_ai_action_from_fields(fields: dict[str, Any]) -> tuple[str, str]:
    for key in ENTRY_AI_ACTION_FIELD_KEYS:
        value = fields.get(key)
        text = str(value or "").strip()
        if text:
            return text, key
    return "", ""


def _latest_entry_ai_action_snapshot(rows: list[dict[str, Any]]) -> dict[str, Any]:
    for preferred_stage in ENTRY_AI_ACTION_PRIORITY_STAGES:
        for row in reversed(rows):
            if str(row.get("stage") or "") != preferred_stage:
                continue
            fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
            action, field = _entry_ai_action_from_fields(fields)
            if action:
                return {
                    "action": action,
                    "field": field,
                    "stage": preferred_stage,
                    "emitted_at": _event_time(row),
                }
    for row in reversed(rows):
        fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
        action, field = _entry_ai_action_from_fields(fields)
        if action:
            return {
                "action": action,
                "field": field,
                "stage": str(row.get("stage") or ""),
                "emitted_at": _event_time(row),
            }
    return {"action": "-", "field": "missing", "stage": "missing", "emitted_at": ""}


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def _metric_summary(values: list[float]) -> dict[str, float | None]:
    return {
        "min": round(min(values), 6) if values else None,
        "median": round(_median(values), 6) if values else None,
        "max": round(max(values), 6) if values else None,
    }


def _latency_danger_cause(fields: dict[str, Any]) -> str:
    reason_text = str(fields.get("latency_danger_reasons") or fields.get("latency_reason") or "").lower()
    stale_values = (
        fields.get("pre_submit_effective_quote_stale"),
        fields.get("quote_stale_at_submit"),
        fields.get("quote_stale"),
    )
    if any(_boolish(value) for value in stale_values) or "quote_stale" in reason_text:
        return "quote_stale"
    if "spread_too_wide" in reason_text:
        return "spread_too_wide"
    spread_ratio = _safe_float(fields.get("spread_ratio") or fields.get("pre_submit_quote_refresh_spread_ratio"))
    if spread_ratio is not None and spread_ratio > LATENCY_DANGER_SPREAD_RATIO_CAP:
        return "spread_too_wide"
    spread_ticks = _safe_float(fields.get("orderbook_micro_spread_ticks"))
    bucket = str(fields.get("orderbook_micro_ofi_bucket_key") or fields.get("orderbook_micro_calibration_bucket") or "")
    if (spread_ticks is not None and spread_ticks >= 5.0) or "spread=wide" in bucket:
        return "spread_microstructure_wide"
    ws_age_ms = _safe_float(
        fields.get("ws_age_ms")
        or fields.get("pre_submit_effective_quote_age_ms")
        or fields.get("pre_submit_ws_snapshot_refresh_age_ms")
    )
    if (ws_age_ms is not None and ws_age_ms > LATENCY_DANGER_WS_AGE_MS_CAP) or "ws_age_too_high" in reason_text:
        return "ws_age_too_high"
    return "other_danger"


def _latency_danger_event_fields(row: dict[str, Any]) -> dict[str, Any]:
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    return {
        "latency_state": str(fields.get("latency_state") or ""),
        "latency_danger_reasons": str(fields.get("latency_danger_reasons") or ""),
        "latency_root_cause": _latency_danger_cause(fields),
        "spread_ratio": _safe_float(fields.get("spread_ratio") or fields.get("pre_submit_quote_refresh_spread_ratio")),
        "ws_age_ms": _safe_float(
            fields.get("ws_age_ms")
            or fields.get("pre_submit_effective_quote_age_ms")
            or fields.get("pre_submit_ws_snapshot_refresh_age_ms")
        ),
        "spread_ticks": _safe_float(fields.get("orderbook_micro_spread_ticks")),
        "micro_state": str(fields.get("orderbook_micro_state") or ""),
        "ofi_bucket": str(
            fields.get("orderbook_micro_ofi_bucket_key")
            or fields.get("orderbook_micro_calibration_bucket")
            or ""
        ),
        "pre_submit_effective_quote_stale": str(fields.get("pre_submit_effective_quote_stale") or ""),
        "quote_stale_at_submit": str(fields.get("quote_stale_at_submit") or ""),
        "quote_stale": str(fields.get("quote_stale") or ""),
    }


def _latency_danger_root_cause_summary(blocker_rows: list[dict[str, Any]]) -> dict[str, Any]:
    events = []
    for row in blocker_rows:
        if row.get("stage") != "latency_block" or _blocker_reason(row) != "latency_state_danger":
            continue
        fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
        if not any(fields.get(key) not in (None, "") for key in LATENCY_PROVENANCE_FIELD_KEYS):
            continue
        events.append(_latency_danger_event_fields(row))
    if not events:
        return {
            "event_count": 0,
            "top_cause": "",
            "cause_counts": [],
            "spread_ratio": _metric_summary([]),
            "ws_age_ms": _metric_summary([]),
            "spread_ticks": _metric_summary([]),
            "top_micro_state": "-",
            "top_ofi_bucket": "no_latency_provenance_fields",
        }
    cause_counts = Counter(str(item.get("latency_root_cause") or "other_danger") for item in events)
    micro_state_counts = Counter(str(item.get("micro_state") or "-") for item in events)
    bucket_counts = Counter(str(item.get("ofi_bucket") or "-") for item in events)
    return {
        "event_count": len(events),
        "top_cause": cause_counts.most_common(1)[0][0],
        "cause_counts": [
            {"cause": cause, "count": count}
            for cause, count in cause_counts.most_common()
        ],
        "spread_ratio": _metric_summary(
            [value for item in events if (value := item.get("spread_ratio")) is not None]
        ),
        "ws_age_ms": _metric_summary(
            [value for item in events if (value := item.get("ws_age_ms")) is not None]
        ),
        "spread_ticks": _metric_summary(
            [value for item in events if (value := item.get("spread_ticks")) is not None]
        ),
        "top_micro_state": micro_state_counts.most_common(1)[0][0],
        "top_ofi_bucket": bucket_counts.most_common(1)[0][0],
    }


def _blocker_reason(row: dict[str, Any]) -> str:
    for key in (
        "reason",
        "block_reason",
        "skip_reason",
        "scanner_watch_skip_reason",
        "scanner_block_reason",
        "eviction_reason",
        "budget_block_reason",
        "terminal_reason",
        "entry_submit_revalidation_warning",
        "scalp_sim_candidate_window_blocked_reason",
        "runtime_target_attach_reason",
    ):
        value = _field(row, key)
        if value not in (None, ""):
            return str(value)
    return ""


def _first_float_field(row: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        value = _safe_float(_field(row, key))
        if value is not None:
            return value
    return None


def _event_max_age_ms(row: dict[str, Any]) -> float | None:
    age_values: list[float] = []
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    for key, value in fields.items():
        key_text = str(key).lower()
        if not (
            "age_ms" in key_text
            or "delay_ms" in key_text
            or "lag_ms" in key_text
            or key_text in {"quote_age_ms", "tick_latest_age_ms"}
        ):
            continue
        parsed = _safe_float(value)
        if parsed is not None:
            age_values.append(parsed)
    return max(age_values) if age_values else None


def _event_has_stale_or_delayed_context(row: dict[str, Any]) -> bool:
    return _stale_or_delayed_eval_category(row) != ""


def _stale_or_delayed_eval_category(row: dict[str, Any]) -> str:
    if _event_is_recovery_observation(row):
        return ""
    reason = _blocker_reason(row).lower()
    stage = str(row.get("stage") or "").lower()
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    context_text = " ".join(
        str(value).lower()
        for key, value in fields.items()
        if any(token in str(key).lower() for token in ("stale", "fresh", "snapshot", "subscription"))
    )
    combined = f"{stage} {reason} {context_text}"
    if "scanner_full_eval_loop_budget_deferred" in combined or ("full_eval" in stage and "lag" in stage):
        return "full_eval_delay"
    if "ws_snapshot_missing_or_zero" in combined or "missing_or_zero_curr" in combined:
        return "ws_quote_missing"
    if "stale_context_or_quote" in combined or ("entry_submit_revalidation" in stage and "stale" in combined):
        return "pre_submit_hard_stale"
    if (
        ("pre_ai" in combined and "stale" in combined)
        or "stale_ws_snapshot" in combined
        or "subscription_alive_but_entry_stale" in combined
        or "insufficient_history" in combined
    ):
        return "pre_ai_stale_or_history_gap"
    if "stale" in combined:
        return "diagnostic_quote_age_stale"
    max_age_ms = _event_max_age_ms(row)
    if max_age_ms is not None and max_age_ms > ENTRY_FRESH_MAX_AGE_MS:
        return "diagnostic_quote_age_stale"
    return ""


def _event_is_fresh_context(row: dict[str, Any]) -> bool:
    max_age_ms = _event_max_age_ms(row)
    return max_age_ms is not None and max_age_ms <= ENTRY_FRESH_MAX_AGE_MS and not _event_has_stale_or_delayed_context(row)


def _event_is_recovery_observation(row: dict[str, Any]) -> bool:
    return _blocker_reason(row) in RECOVERY_OBSERVATION_REASONS


def _low_ai_or_negative_pressure(row: dict[str, Any]) -> bool:
    ai_score = _first_float_field(row, "ai_score", "buy_ai_score", "entry_ai_score")
    buy_pressure = _first_float_field(
        row,
        "buy_pressure",
        "buy_pressure_10t",
        "orderbook_buy_pressure",
        "pressure_buy",
    )
    return (
        (ai_score is not None and ai_score < LOW_AI_SCORE_CUTOFF)
        or (buy_pressure is not None and buy_pressure < NEGATIVE_BUY_PRESSURE_CUTOFF)
    )


def _low_ai_pressure_quality_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "fresh_eval": 0,
        "stale_or_delayed_eval": 0,
        "unknown_eval_quality": 0,
    }
    for row in rows:
        if not _low_ai_or_negative_pressure(row):
            continue
        if _event_has_stale_or_delayed_context(row):
            counts["stale_or_delayed_eval"] += 1
        elif _event_is_fresh_context(row):
            counts["fresh_eval"] += 1
        else:
            counts["unknown_eval_quality"] += 1
    return counts


def _stale_or_delayed_eval_category_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        if not _low_ai_or_negative_pressure(row):
            continue
        category = _stale_or_delayed_eval_category(row)
        if category:
            counter[category] += 1
    return {
        "diagnostic_quote_age_stale": int(counter.get("diagnostic_quote_age_stale", 0)),
        "full_eval_delay": int(counter.get("full_eval_delay", 0)),
        "ws_quote_missing": int(counter.get("ws_quote_missing", 0)),
        "pre_ai_stale_or_history_gap": int(counter.get("pre_ai_stale_or_history_gap", 0)),
        "pre_submit_hard_stale": int(counter.get("pre_submit_hard_stale", 0)),
    }


def _unresolved_stale_low_ai_pressure_count(rows: list[dict[str, Any]]) -> int:
    stale_indexes = [
        idx
        for idx, row in enumerate(rows)
        if _low_ai_or_negative_pressure(row) and _event_has_stale_or_delayed_context(row)
    ]
    if not stale_indexes:
        return 0
    latest_stale_idx = stale_indexes[-1]
    if any(
        _is_downstream_progress_after_stale_source(row) or _event_is_recovery_observation(row)
        for row in rows[latest_stale_idx + 1 :]
    ):
        return 0
    return len(stale_indexes)


def _strength_history_count(row: dict[str, Any]) -> int | None:
    for key in STRENGTH_HISTORY_COUNT_KEYS:
        value = _safe_float(_field(row, key))
        if value is not None:
            return int(value)
    return None


def _is_zero_strength_history_source_quality_event(row: dict[str, Any]) -> bool:
    if _event_is_recovery_observation(row):
        return False
    stage = str(row.get("stage") or "").lower()
    fast_precheck_result = str(_field(row, "fast_precheck_result", "") or "").strip().lower()
    if stage == "scalping_scanner_fast_precheck" and fast_precheck_result == "eligible_for_heavy_entry_eval":
        return False
    history_count = _strength_history_count(row)
    if history_count is None or history_count > 0:
        return False
    reason = _blocker_reason(row).lower()
    context = f"{stage} {reason}"
    return any(
        token in context
        for token in (
            "insufficient_history",
            "stability_pending",
            "strength_momentum",
            "fast_precheck",
            "stale_ws_recovered",
        )
    )


def _is_downstream_progress_after_stale_source(row: dict[str, Any]) -> bool:
    stage = str(row.get("stage") or "")
    reason = _blocker_reason(row)
    if _field(row, "fast_precheck_result") == "eligible_for_heavy_entry_eval":
        return True
    if _field(row, "fast_precheck_reason") in {
        "fast_precheck_pass",
        "rising_realtime_type_fresh_quote_timestamp_stale",
        "rising_subscription_recheck_fresh_realtime_evidence",
    }:
        return True
    return stage in {
        "ai_confirmed",
        "ai_confirmed_terminal_no_budget",
        "blocked_ai_score",
        "blocked_strength_momentum",
        "entry_ai_price_canary_applied",
        "scalp_entry_action_decision_snapshot",
        "strength_momentum_observed",
        "strength_momentum_pass",
    } and reason not in RECOVERY_OBSERVATION_REASONS


def _zero_strength_history_source_quality(rows: list[dict[str, Any]]) -> dict[str, Any]:
    zero_indexed_rows = [
        (idx, row) for idx, row in enumerate(rows) if _is_zero_strength_history_source_quality_event(row)
    ]
    zero_rows = [row for _idx, row in zero_indexed_rows]
    latest_zero_idx = zero_indexed_rows[-1][0] if zero_indexed_rows else -1
    downstream_progress = next(
        (row for row in rows[latest_zero_idx + 1 :] if _is_downstream_progress_after_stale_source(row)),
        None,
    )
    unresolved_zero_rows = [] if downstream_progress else zero_rows
    reason_counts = Counter(
        _blocker_reason(row) or str(row.get("stage") or "") for row in unresolved_zero_rows
    )
    latest = unresolved_zero_rows[-1] if unresolved_zero_rows else {}
    raw_reason_counts = Counter(_blocker_reason(row) or str(row.get("stage") or "") for row in zero_rows)
    route = "transient_stale_recovered_to_downstream_blocker" if zero_rows and downstream_progress else (
        "source_quality_workorder_required"
        if len(unresolved_zero_rows) >= ZERO_HISTORY_WORKORDER_MIN_EVENTS
        else "observe_until_repeated"
    )
    return {
        "event_count": len(unresolved_zero_rows),
        "raw_event_count": len(zero_rows),
        "recovered_by_downstream_progress": bool(downstream_progress),
        "downstream_progress_at": _event_time(downstream_progress) if downstream_progress else "",
        "downstream_progress_stage": (downstream_progress.get("stage") or "") if downstream_progress else "",
        "downstream_progress_reason": _blocker_reason(downstream_progress) if downstream_progress else "",
        "repeated": len(unresolved_zero_rows) >= ZERO_HISTORY_WORKORDER_MIN_EVENTS,
        "latest_at": _event_time(latest) if latest else "",
        "latest_stage": (latest.get("stage") or "") if latest else "",
        "latest_reason": _blocker_reason(latest) if latest else "",
        "top_reasons": [
            {"reason": reason, "count": count}
            for reason, count in reason_counts.most_common(5)
        ],
        "raw_top_reasons": [
            {"reason": reason, "count": count}
            for reason, count in raw_reason_counts.most_common(5)
        ],
        "source_quality_route": route,
    }


def _is_blocker_row(row: dict[str, Any]) -> bool:
    if row.get("stage") not in BLOCKER_STAGES:
        return False
    return _blocker_reason(row) not in RECOVERY_OBSERVATION_REASONS | BUY_WINDOW_PAUSE_REASONS


def _dominant_blocker(rows: list[dict[str, Any]]) -> dict[str, Any]:
    blocker_rows = [row for row in rows if _is_blocker_row(row)]
    if not blocker_rows:
        return {"stage": "", "reason": "", "count": 0}
    counts = Counter((row.get("stage") or "", _blocker_reason(row)) for row in blocker_rows)
    (stage, reason), count = counts.most_common(1)[0]
    return {"stage": stage, "reason": reason, "count": count}


def _latest_blocker(rows: list[dict[str, Any]]) -> dict[str, Any]:
    for row in reversed(rows):
        if _is_blocker_row(row):
            return {
                "emitted_at": _event_time(row),
                "stage": row.get("stage") or "",
                "reason": _blocker_reason(row),
                "ai_score": _safe_float(_field(row, "ai_score")),
                "price_delta_since_first_seen_pct": _safe_float(
                    _field(row, "price_delta_since_first_seen_pct")
                ),
            }
    return {"emitted_at": "", "stage": "", "reason": "", "ai_score": None, "price_delta_since_first_seen_pct": None}


def _blocker_taxonomy(
    *,
    stage: str,
    reason: str,
    count: int = 1,
    max_delta_pct: float | None = None,
    latency_root_cause: str = "",
) -> dict[str, Any]:
    reason_lower = reason.lower()
    stage_lower = stage.lower()
    latency_cause = latency_root_cause.strip().lower()
    delta = max_delta_pct if max_delta_pct is not None else 0.0
    if stage == "scalping_scanner_watch_eviction":
        return {
            "class": "watch_budget_reallocated",
            "actionable": False,
            "major_blocker": False,
            "route": "watch_budget_reallocated_after_stale_or_terminal_expiry",
        }
    if reason == "ws_snapshot_missing_or_zero":
        evictable = count >= 3
        return {
            "class": "source_freshness_evictable" if evictable else "source_freshness_recovering",
            "actionable": evictable,
            "major_blocker": False,
            "route": "evict_or_quarantine_and_reallocate_watch_budget"
            if evictable
            else "short_recovery_window_before_watch_budget_reallocation",
        }
    if reason == "scanner_full_eval_loop_budget_deferred":
        return {
            "class": "runtime_backpressure",
            "actionable": False,
            "major_blocker": False,
            "route": "auto_governor_backpressure_observation",
        }
    if (
        reason == "entry_cooldown_active"
        or stage == "same_symbol_loss_reentry_cooldown"
        or reason == "operator_manual_control_excluded_symbol"
    ):
        if reason == "operator_manual_control_excluded_symbol":
            route = "operator_manual_control_guard_preserved_no_bypass"
        elif count >= ACTIONABLE_COOLDOWN_MIN_COUNT and delta >= ACTIONABLE_COOLDOWN_MIN_DELTA_PCT:
            route = "review_cooldown_opportunity_loss_or_wrong_scope"
        else:
            route = "normal_cooldown_guard"
        return {
            "class": "intended_guard",
            "actionable": False,
            "major_blocker": False,
            "route": route,
        }
    if "stale_context_or_quote" in reason_lower or "submit_revalidation" in stage_lower:
        return {
            "class": "submit_hard_guard",
            "actionable": True,
            "major_blocker": True,
            "route": "preserve_stale_submit_block_and_fix_price_or_quote_context",
        }
    if stage == "latency_block":
        if latency_cause in {"quote_stale", "spread_too_wide", "spread_microstructure_wide"}:
            return {
                "class": "pre_submit_quality_guard",
                "actionable": False,
                "major_blocker": False,
                "route": f"known_{latency_cause}_guard_preserved_no_bypass",
            }
        return {
            "class": "pre_submit_quality_guard",
            "actionable": True,
            "major_blocker": True,
            "route": "inspect_latency_danger_or_slippage_without_guard_bypass",
        }
    if "stale" in reason_lower or "insufficient_history" in reason_lower:
        return {
            "class": "source_freshness_blocker",
            "actionable": True,
            "major_blocker": True,
            "route": "fix_observation_source_quality_before_threshold_tuning",
        }
    return {
        "class": "strategy_reject",
        "actionable": False,
        "major_blocker": False,
        "route": "strategy_or_ai_reject_attribution",
    }


def _dominant_actionable_blocker(rows: list[dict[str, Any]]) -> dict[str, Any]:
    blocker_rows = [row for row in rows if _is_blocker_row(row)]
    if not blocker_rows:
        return {"stage": "", "reason": "", "count": 0, "class": "", "route": ""}
    max_delta = _max_delta(rows)
    counts = Counter(
        (
            row.get("stage") or "",
            _blocker_reason(row),
            _latency_danger_cause(row.get("fields") if isinstance(row.get("fields"), dict) else {})
            if row.get("stage") == "latency_block" and _blocker_reason(row) == "latency_state_danger"
            else "",
        )
        for row in blocker_rows
    )
    ordered = sorted(
        counts.items(),
        key=lambda item: (
            ACTIONABLE_BLOCKER_STAGE_PRIORITY.get(str(item[0][0]), 0),
            item[1],
        ),
        reverse=True,
    )
    for (stage, reason, latency_root_cause), count in ordered:
        taxonomy = _blocker_taxonomy(
            stage=str(stage),
            reason=str(reason),
            count=int(count),
            max_delta_pct=max_delta,
            latency_root_cause=str(latency_root_cause),
        )
        if taxonomy["major_blocker"]:
            return {
                "stage": stage,
                "reason": reason,
                "count": count,
                "class": taxonomy["class"],
                "route": taxonomy["route"],
            }
    return {"stage": "", "reason": "", "count": 0, "class": "non_actionable_guard_or_backpressure", "route": "observe_only"}


def _runtime_attach_identity_mismatch(rows: list[dict[str, Any]]) -> dict[str, Any]:
    mismatch_rows = []
    for row in rows:
        if row.get("stage") != "scalping_scanner_runtime_target_attach":
            continue
        fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
        if (
            str(fields.get("runtime_target_attach_outcome") or "").strip() == "skipped"
            and str(fields.get("runtime_target_attach_reason") or "").strip() == "scanner_identity_name_mismatch"
        ):
            mismatch_rows.append(row)
    latest = mismatch_rows[-1] if mismatch_rows else {}
    latest_fields = latest.get("fields") if isinstance(latest.get("fields"), dict) else {}
    return {
        "count": len(mismatch_rows),
        "latest_at": _event_time(latest) if latest else "",
        "latest_reason": str(latest_fields.get("runtime_target_attach_reason") or ""),
        "payload_name": str(latest_fields.get("scanner_identity_payload_name") or ""),
        "db_name": str(latest_fields.get("scanner_identity_db_name") or ""),
        "mismatch_expired": str(latest_fields.get("scanner_identity_mismatch_expired") or ""),
    }


def _full_eval_deferred_status(rows: list[dict[str, Any]], deferred_rows: list[dict[str, Any]]) -> str:
    if not deferred_rows:
        return "not_deferred"
    latest_deferred = deferred_rows[-1]
    try:
        latest_idx = max(idx for idx, row in enumerate(rows) if row is latest_deferred)
    except ValueError:
        latest_idx = -1
    later_rows = rows[latest_idx + 1 :] if latest_idx >= 0 else []
    if any(_is_downstream_progress_after_stale_source(row) for row in later_rows):
        return "deferred_then_evaluated"
    return "deferred_never_evaluated"


def _latest_delta(rows: list[dict[str, Any]]) -> float | None:
    for row in reversed(rows):
        value = _safe_float(_field(row, "price_delta_since_first_seen_pct"))
        if value is not None:
            return value
    return None


def _max_delta(rows: list[dict[str, Any]]) -> float | None:
    values = [
        value
        for row in rows
        if (value := _safe_float(_field(row, "price_delta_since_first_seen_pct"))) is not None
    ]
    return max(values) if values else None


def _event_time(row: dict[str, Any]) -> str:
    return str(row.get("emitted_at") or "")


def _normalize_event_bound(value: str | None, *, target_date: str) -> str | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    if "T" in text:
        return text
    try:
        parsed_time = dt_time.fromisoformat(text)
    except ValueError:
        return text
    return f"{target_date}T{parsed_time.isoformat()}"


def _top_counter(counter: Counter[Any], *, limit: int = 10, key_name: str = "key") -> list[dict[str, Any]]:
    return [{key_name: key, "count": count} for key, count in counter.most_common(limit)]


def _real_rows(
    rows: list[dict[str, Any]],
    *,
    since: str | None = None,
    event_until: str | None = None,
    target_date: str,
) -> list[dict[str, Any]]:
    selected = []
    normalized_since = _normalize_event_bound(since, target_date=target_date)
    normalized_until = _normalize_event_bound(event_until, target_date=target_date)
    latest_forced_scout_at_by_code: dict[str, datetime] = {}
    for row in rows:
        event_time = _event_time(row)
        if normalized_since and event_time < normalized_since:
            continue
        if normalized_until and event_time > normalized_until:
            continue
        code = str(row.get("stock_code") or "").strip()
        fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
        if row.get("pipeline") == ENTRY_PIPELINE and _is_rising_missed_forced_one_share_entry(fields):
            event_at = _parse_event_dt(row)
            if code and event_at is not None:
                latest_forced_scout_at_by_code[code] = event_at
            continue
        if row.get("pipeline") == ENTRY_PIPELINE and _is_rising_missed_forced_lineage_row(
            row,
            latest_forced_scout_at_by_code,
        ):
            continue
        if _exclude_from_real_entry_analysis(row):
            continue
        selected.append(row)
    return selected


def _entry_price_diagnostics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    entry_rows = [row for row in rows if row.get("pipeline") == ENTRY_PIPELINE]
    relevant = []
    for row in entry_rows:
        stage = str(row.get("stage") or "")
        fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
        if stage in ENTRY_PRICE_STAGES or any(
            key in fields
            for key in (
                "entry_price_guard",
                "entry_submit_revalidation",
                "price_below_bid_bps",
                "submitted_order_price",
                "entry_order_lifecycle",
            )
        ):
            relevant.append(row)

    stage_counts = Counter(str(row.get("stage") or "") for row in relevant)
    guard_counts = Counter(str(_field(row, "entry_price_guard") or "-") for row in relevant)
    resolution_counts = Counter(str(_field(row, "resolution_reason") or "-") for row in relevant)
    block_rows = [
        row
        for row in relevant
        if str(row.get("stage") or "") in {"entry_ai_price_canary_skip_order", "entry_submit_revalidation_block", "pre_submit_price_guard_block"}
        or str(row.get("stage") or "").startswith("entry_order_cancel_")
        or str(_field(row, "entry_submit_revalidation_block") or "").lower() == "true"
        or str(_field(row, "price_context_stale_at_submit") or "").lower() == "true"
        or str(_field(row, "quote_stale_at_submit") or "").lower() == "true"
    ]
    candidate_failure_rows = [
        row
        for row in relevant
        if str(row.get("stage") or "") == "entry_ai_price_canary_fallback"
    ]
    candidate_failure_reason_counts = Counter(_blocker_reason(row) or "-" for row in candidate_failure_rows)

    def _submitted_order_price(row: dict[str, Any]) -> float | None:
        return _safe_float(
            _field(row, "submitted_order_price")
            or _field(row, "submitted_price")
            or _field(row, "order_price")
            or _field(row, "resolved_order_price")
        )

    return {
        "event_count": len(relevant),
        "block_or_unfilled_count": len(block_rows),
        "candidate_failure_count": len(candidate_failure_rows),
        "candidate_failure_reason_counts": _top_counter(
            candidate_failure_reason_counts,
            key_name="reason",
        ),
        "stage_counts": _top_counter(stage_counts, key_name="stage"),
        "guard_counts": _top_counter(guard_counts, key_name="entry_price_guard"),
        "resolution_counts": _top_counter(resolution_counts, key_name="resolution_reason"),
        "recent_issues": [
            {
                "emitted_at": _event_time(row),
                "stock_code": row.get("stock_code") or "",
                "stock_name": row.get("stock_name") or "",
                "stage": row.get("stage") or "",
                "reason": _blocker_reason(row),
                "entry_price_guard": _field(row, "entry_price_guard", ""),
                "resolution_reason": _field(row, "resolution_reason", ""),
                "price_below_bid_bps": _safe_float(_field(row, "price_below_bid_bps")),
                "submitted_order_price": _submitted_order_price(row),
                "best_bid_at_submit": _safe_float(_field(row, "best_bid_at_submit")),
                "quote_age_at_submit_ms": _safe_float(_field(row, "quote_age_at_submit_ms")),
                "entry_submit_revalidation": _field(row, "entry_submit_revalidation", ""),
                "entry_submit_revalidation_warning": _field(row, "entry_submit_revalidation_warning", ""),
                "ai_entry_price_canary_action": _field(row, "ai_entry_price_canary_action", ""),
                "pre_submit_liquidity_guard_action": _field(row, "pre_submit_liquidity_guard_action", ""),
                "pre_submit_liquidity_reason": _field(row, "pre_submit_liquidity_reason", ""),
            }
            for row in block_rows[-12:]
        ],
        "decision_authority": "diagnostic_only_no_order_guard_bypass",
        "runtime_effect": False,
    }


def _scale_in_diagnostics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    holding_rows = [row for row in rows if row.get("pipeline") == "HOLDING_PIPELINE"]
    relevant = []
    for row in holding_rows:
        stage = str(row.get("stage") or "")
        fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
        value_text = " ".join([stage, *(str(value) for value in fields.values())]).lower()
        if stage == "stat_action_decision_snapshot":
            action = str(
                _field(row, "scale_in_action_type")
                or _field(row, "scale_in_arm")
                or _field(row, "chosen_action")
                or ""
            ).strip()
            reason_text = " ".join(
                str(_field(row, key) or "")
                for key in ("scale_in_blocker_reason", "scale_in_gate_reason", "reason")
            ).lower()
            if (action and action != "-") or any(token in reason_text for token in SCALE_IN_REASON_TOKENS):
                relevant.append(row)
            continue
        if stage in SCALE_IN_STAGES or any(token in value_text for token in SCALE_IN_REASON_TOKENS):
            relevant.append(row)

    blocker_counter: Counter[str] = Counter()
    action_counter: Counter[str] = Counter()
    blocked_rows: list[dict[str, Any]] = []
    executed_rows: list[dict[str, Any]] = []
    for row in relevant:
        stage = str(row.get("stage") or "")
        stage_lower = stage.lower()
        executed = stage == "scale_in_executed" or str(_field(row, "scale_in_executed") or "").lower() == "true"
        allowed = str(_field(row, "scale_in_gate_allowed") or "").strip().lower()
        reason = str(_field(row, "scale_in_blocker_reason") or _field(row, "scale_in_gate_reason") or _field(row, "reason") or "")
        action = str(_field(row, "scale_in_action_type") or _field(row, "scale_in_arm") or _field(row, "chosen_action") or "-")
        action_counter[action] += 1
        blocked_stage = "blocked" in stage_lower or stage in {
            "scale_in_price_guard_block",
            "scale_in_qty_block",
            "scale_in_order_unfilled",
        }
        if not executed and (allowed == "false" or blocked_stage):
            blocker_counter[reason or str(row.get("stage") or "-")] += 1
            blocked_rows.append(row)
        if executed:
            executed_rows.append(row)

    return {
        "event_count": len(relevant),
        "blocked_count": len(blocked_rows),
        "executed_count": len(executed_rows),
        "blocker_reason_counts": _top_counter(blocker_counter, key_name="reason"),
        "action_counts": _top_counter(action_counter, key_name="action"),
        "recent_blockers": [
            {
                "emitted_at": _event_time(row),
                "stock_code": row.get("stock_code") or "",
                "stock_name": row.get("stock_name") or "",
                "stage": row.get("stage") or "",
                "profit_rate": _safe_float(_field(row, "profit_rate")),
                "peak_profit": _safe_float(_field(row, "peak_profit")),
                "current_ai_score": _safe_float(_field(row, "current_ai_score") or _field(row, "ai_score")),
                "scale_in_gate_allowed": _field(row, "scale_in_gate_allowed", ""),
                "scale_in_gate_reason": _field(row, "scale_in_gate_reason", ""),
                "scale_in_blocker_reason": _field(row, "scale_in_blocker_reason", ""),
                "scale_in_action_type": _field(row, "scale_in_action_type", ""),
                "distance_to_buy_bps": _safe_float(_field(row, "distance_to_buy_bps")),
            }
            for row in blocked_rows[-12:]
        ],
        "decision_authority": "diagnostic_only_no_scale_in_authority_change",
        "runtime_effect": False,
    }


def _post_sell_path(post_sell_dir: Path, kind: str, target_date: str) -> Path:
    plain = post_sell_dir / f"{kind}_{target_date}.jsonl"
    if plain.exists():
        return plain
    gz_path = plain.with_suffix(plain.suffix + ".gz")
    return gz_path if gz_path.exists() else plain


def _sell_flow(row: dict[str, Any]) -> str:
    profit = _safe_float(row.get("profit_rate"))
    exit_rule = str(row.get("exit_rule") or "").lower()
    reason = str(row.get("sell_reason_type") or "").lower()
    if (profit is not None and profit < 0) or "loss" in reason or "stop" in exit_rule:
        return "stop_loss_flow"
    if (profit is not None and profit > 0) or any(token in exit_rule for token in ("profit", "trailing", "target")):
        return "take_profit_flow"
    return "other_sell_flow"


def _post_sell_flow_diagnostics(*, target_date: str, post_sell_dir: Path) -> dict[str, Any]:
    candidates = _read_jsonl(_post_sell_path(post_sell_dir, "post_sell_candidates", target_date))
    evaluations = _read_jsonl(_post_sell_path(post_sell_dir, "post_sell_evaluations", target_date))
    outcome_counter = Counter(str(row.get("outcome") or "-") for row in evaluations)
    flow_counter = Counter(_sell_flow(row) for row in evaluations)
    missed_rows = [row for row in evaluations if str(row.get("outcome") or "") == "MISSED_UPSIDE"]
    bad_entry_rows = [
        row
        for row in evaluations
        if (_safe_float(row.get("profit_rate"), 0.0) or 0.0) < 0
        and (_safe_float((row.get("metrics_10m") or {}).get("mfe_vs_buy_pct"), -999.0) or -999.0) <= 0
    ]
    return {
        "candidate_count": len(candidates),
        "evaluated_count": len(evaluations),
        "outcome_counts": _top_counter(outcome_counter, key_name="outcome"),
        "sell_flow_counts": _top_counter(flow_counter, key_name="flow"),
        "missed_upside_count": len(missed_rows),
        "bad_entry_after_sell_count": len(bad_entry_rows),
        "top_missed_upside": [
            {
                "stock_code": row.get("stock_code") or "",
                "stock_name": row.get("stock_name") or "",
                "sell_time": row.get("sell_time") or "",
                "flow": _sell_flow(row),
                "profit_rate": _safe_float(row.get("profit_rate")),
                "exit_rule": row.get("exit_rule") or "",
                "mfe_10m_pct": _safe_float((row.get("metrics_10m") or {}).get("mfe_pct")),
                "mfe_vs_buy_10m_pct": _safe_float((row.get("metrics_10m") or {}).get("mfe_vs_buy_pct")),
                "ai_score_at_exit": _safe_float(row.get("ai_score_at_exit") or row.get("current_ai_score")),
            }
            for row in sorted(
                missed_rows,
                key=lambda item: _safe_float((item.get("metrics_10m") or {}).get("mfe_pct"), -999.0) or -999.0,
                reverse=True,
            )[:12]
        ],
        "bad_entry_examples": [
            {
                "stock_code": row.get("stock_code") or "",
                "stock_name": row.get("stock_name") or "",
                "sell_time": row.get("sell_time") or "",
                "profit_rate": _safe_float(row.get("profit_rate")),
                "exit_rule": row.get("exit_rule") or "",
                "mfe_vs_buy_10m_pct": _safe_float((row.get("metrics_10m") or {}).get("mfe_vs_buy_pct")),
                "ai_score_at_exit": _safe_float(row.get("ai_score_at_exit") or row.get("current_ai_score")),
            }
            for row in bad_entry_rows[:12]
        ],
        "decision_authority": "post_sell_diagnostic_only_no_exit_or_threshold_mutation",
        "runtime_effect": False,
    }


def _summarize_code(
    code: str,
    rows: list[dict[str, Any]],
    *,
    promotion_source_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    stage_counts = Counter(str(row.get("stage") or "") for row in rows)
    name = next((str(row.get("stock_name") or "") for row in rows if row.get("stock_name")), "")
    promotion_rows = promotion_source_rows if promotion_source_rows is not None else rows
    promoted_rows = [row for row in promotion_rows if row.get("stage") == PROMOTED_STAGE]
    ai_rows = [row for row in rows if row.get("stage") == "ai_confirmed"]
    real_submit_rows = [
        row for row in rows if str(_field(row, "actual_order_submitted")).lower() == REAL_SUBMIT_TRUE
    ]
    blocker_rows = [row for row in rows if _is_blocker_row(row)]
    budget_deferred_rows = [
        row
        for row in blocker_rows
        if _blocker_reason(row) == "scanner_full_eval_loop_budget_deferred"
    ]
    latest_budget_deferred = budget_deferred_rows[-1] if budget_deferred_rows else {}
    queue_counts = {stage: stage_counts.get(stage, 0) for stage in QUEUE_STAGES if stage_counts.get(stage, 0)}
    latest_ai = ai_rows[-1] if ai_rows else {}
    entry_ai_snapshot = _latest_entry_ai_action_snapshot(rows)
    max_delta = _max_delta(rows)
    return {
        "stock_code": code,
        "stock_name": name,
        "promoted_count": len(promoted_rows),
        "first_promoted_at": _event_time(promoted_rows[0]) if promoted_rows else "",
        "promoted_in_event_window": any(row.get("stage") == PROMOTED_STAGE for row in rows),
        "last_event_at": _event_time(rows[-1]) if rows else "",
        "max_price_delta_since_first_seen_pct": max_delta,
        "latest_price_delta_since_first_seen_pct": _latest_delta(rows),
        "ai_confirmed_count": len(ai_rows),
        "latest_ai_action": _field(latest_ai, "action") if latest_ai else "",
        "latest_ai_score": _safe_float(_field(latest_ai, "ai_score")) if latest_ai else None,
        "rising_missed_entry_ai_action": entry_ai_snapshot["action"],
        "rising_missed_entry_ai_action_source": entry_ai_snapshot["field"],
        "rising_missed_entry_ai_action_stage": entry_ai_snapshot["stage"],
        "rising_missed_entry_ai_action_emitted_at": entry_ai_snapshot["emitted_at"],
        "rising_missed_entry_ai_not_evaluated_excluded": str(entry_ai_snapshot["action"]).strip().lower()
        == "not_evaluated",
        "latest_entry_score_threshold": _safe_float(_field(latest_ai, "entry_score_threshold"))
        if latest_ai
        else None,
        "real_submit_count": len(real_submit_rows),
        "blocker_count": len(blocker_rows),
        "dominant_blocker": _dominant_blocker(rows),
        "dominant_actionable_blocker": _dominant_actionable_blocker(rows),
        "runtime_attach_identity_mismatch": _runtime_attach_identity_mismatch(rows),
        "latest_blocker": _latest_blocker(rows),
        "latency_danger_root_cause": _latency_danger_root_cause_summary(blocker_rows),
        "queue_observation_counts": queue_counts,
        "low_ai_or_negative_pressure_eval_quality": _low_ai_pressure_quality_counts(rows),
        "stale_or_delayed_eval_category_counts": _stale_or_delayed_eval_category_counts(rows),
        "unresolved_stale_low_ai_or_pressure_eval_count": _unresolved_stale_low_ai_pressure_count(rows),
        "zero_strength_history_source_quality": _zero_strength_history_source_quality(rows),
        "scanner_full_eval_budget_deferred": {
            "count": len(budget_deferred_rows),
            "status": _full_eval_deferred_status(rows, budget_deferred_rows),
            "latest_at": _event_time(latest_budget_deferred) if latest_budget_deferred else "",
            "scanner_full_eval_limit": _safe_float(_field(latest_budget_deferred, "scanner_full_eval_limit")),
            "scanner_full_eval_count": _safe_float(_field(latest_budget_deferred, "scanner_full_eval_count")),
            "scanner_rising_full_eval_extra_limit": _safe_float(
                _field(latest_budget_deferred, "scanner_rising_full_eval_extra_limit")
            ),
            "scanner_rising_full_eval_relief_count": _safe_float(
                _field(latest_budget_deferred, "scanner_rising_full_eval_relief_count")
            ),
            "scanner_full_eval_budget_source": _field(
                latest_budget_deferred,
                "scanner_full_eval_budget_source",
                "",
            ),
            "rising_missed_selection_prior_key": _field(
                latest_budget_deferred,
                "rising_missed_selection_prior_key",
                "",
            ),
            "rising_missed_selection_recommendation": _field(
                latest_budget_deferred,
                "rising_missed_selection_recommendation",
                "",
            ),
            "rising_missed_selection_rank_reason": _field(
                latest_budget_deferred,
                "rising_missed_selection_rank_reason",
                "",
            ),
        },
        "recent_blockers": [
            {
                "emitted_at": _event_time(row),
                "stage": row.get("stage") or "",
                "reason": _blocker_reason(row),
                "ai_score": _safe_float(_field(row, "ai_score")),
                "price_delta_since_first_seen_pct": _safe_float(
                    _field(row, "price_delta_since_first_seen_pct")
                ),
                "rising_entry_relief_eligible": _field(row, "rising_entry_relief_eligible", ""),
                "rising_entry_relief_reason": _field(row, "rising_entry_relief_reason", ""),
                "scanner_positive_delta_pct": _safe_float(_field(row, "scanner_positive_delta_pct")),
                "scanner_full_eval_budget_source": _field(row, "scanner_full_eval_budget_source", ""),
                "rising_missed_selection_prior_key": _field(row, "rising_missed_selection_prior_key", ""),
                "rising_missed_selection_recommendation": _field(row, "rising_missed_selection_recommendation", ""),
                "rising_missed_selection_confidence": _field(row, "rising_missed_selection_confidence", ""),
                "rising_missed_selection_score_delta": _safe_float(
                    _field(row, "rising_missed_selection_score_delta")
                ),
                "rising_missed_selection_rank_reason": _field(row, "rising_missed_selection_rank_reason", ""),
                "rising_missed_selection_match_type": _field(row, "rising_missed_selection_match_type", ""),
                "scanner_full_eval_limit": _safe_float(_field(row, "scanner_full_eval_limit")),
                "scanner_full_eval_count": _safe_float(_field(row, "scanner_full_eval_count")),
                "scanner_rising_full_eval_extra_limit": _safe_float(
                    _field(row, "scanner_rising_full_eval_extra_limit")
                ),
                "scanner_rising_full_eval_relief_count": _safe_float(
                    _field(row, "scanner_rising_full_eval_relief_count")
                ),
                "eviction_reason": _field(row, "eviction_reason", ""),
                "terminal_reason": _field(row, "terminal_reason", ""),
                "eviction_attempt_count": _safe_float(_field(row, "eviction_attempt_count")),
                "stale_age_sec": _safe_float(_field(row, "stale_age_sec")),
                **(
                    _latency_danger_event_fields(row)
                    if row.get("stage") == "latency_block" and _blocker_reason(row) == "latency_state_danger"
                    else {}
                ),
                "taxonomy": _blocker_taxonomy(
                    stage=str(row.get("stage") or ""),
                    reason=_blocker_reason(row),
                    count=1,
                    max_delta_pct=max_delta,
                    latency_root_cause=_latency_danger_cause(row.get("fields") if isinstance(row.get("fields"), dict) else {})
                    if row.get("stage") == "latency_block" and _blocker_reason(row) == "latency_state_danger"
                    else "",
                ),
            }
            for row in blocker_rows[-8:]
        ],
    }


def _rollup_blocker_taxonomy(items: list[dict[str, Any]]) -> dict[str, Any]:
    class_counter: Counter[str] = Counter()
    route_counter: Counter[tuple[str, str]] = Counter()
    actionable_counter: Counter[tuple[str, str, str]] = Counter()
    suppressed_non_major_counter: Counter[tuple[str, str, str]] = Counter()
    for item in items:
        max_delta = item.get("max_price_delta_since_first_seen_pct")
        per_symbol_counter = Counter(
            (
                blocker.get("stage") or "",
                blocker.get("reason") or "",
                str(blocker.get("latency_root_cause") or "")
                if blocker.get("stage") == "latency_block" and blocker.get("reason") == "latency_state_danger"
                else "",
            )
            for blocker in item.get("recent_blockers") or []
            if blocker.get("stage")
        )
        for (stage, reason, latency_root_cause), count in per_symbol_counter.items():
            effective_count = int(count)
            if reason == "scanner_full_eval_loop_budget_deferred":
                budget = item.get("scanner_full_eval_budget_deferred") or {}
                effective_count = max(effective_count, int(budget.get("count") or 0))
            taxonomy = _blocker_taxonomy(
                stage=stage,
                reason=reason,
                count=effective_count,
                max_delta_pct=max_delta,
                latency_root_cause=latency_root_cause,
            )
            if (
                item.get("rising_missed_class")
                in {
                    RISING_MISSED_CLASS_SOURCE_QUALITY_EXCLUDED,
                    RISING_MISSED_CLASS_NOT_RISING,
                }
                and taxonomy["class"] in {
                    "source_freshness_blocker",
                }
            ):
                taxonomy = {
                    **taxonomy,
                    "class": "source_quality_exclusion_candidate",
                    "actionable": False,
                    "major_blocker": False,
                    "route": "watch_budget_reallocated_after_source_quality_exclusion",
                }
            block_class = taxonomy["class"]
            route = taxonomy["route"]
            class_counter[block_class] += effective_count
            route_counter[(block_class, route)] += effective_count
            target = actionable_counter if taxonomy["major_blocker"] else suppressed_non_major_counter
            target[(block_class, stage, reason)] += effective_count
    suppressed_non_major_counts = [
        {"class": block_class, "stage": stage, "reason": reason, "count": count}
        for (block_class, stage, reason), count in suppressed_non_major_counter.most_common()
    ]
    return {
        "class_counts": _top_counter(class_counter, key_name="class"),
        "route_counts": [
            {"class": block_class, "route": route, "count": count}
            for (block_class, route), count in route_counter.most_common()
        ],
        "actionable_major_blocker_counts": [
            {"class": block_class, "stage": stage, "reason": reason, "count": count}
            for (block_class, stage, reason), count in actionable_counter.most_common()
        ],
        "suppressed_non_major_counts": suppressed_non_major_counts,
        "suppressed_non_actionable_counts": suppressed_non_major_counts,
        "decision_authority": "diagnostic_taxonomy_only_no_runtime_or_guard_change",
        "runtime_effect": False,
        "forbidden_uses": [
            "guard_bypass",
            "stale_submit_bypass",
            "intraday_threshold_mutation",
            "real_order_approval",
        ],
    }


def _rollup_blockers(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counter: Counter[tuple[str, str]] = Counter()
    for item in items:
        for blocker in item["recent_blockers"]:
            stage = blocker.get("stage") or ""
            reason = blocker.get("reason") or ""
            if stage and (reason in RELIEF_BLOCKER_REASONS or stage == "scalping_scanner_watch_eviction"):
                counter[(stage, reason)] += 1
    return [
        {"stage": stage, "reason": reason, "count": count}
        for (stage, reason), count in counter.most_common()
    ]


def _rollup_low_ai_pressure_quality(items: list[dict[str, Any]]) -> dict[str, int]:
    counter = Counter()
    for item in items:
        counter.update(item.get("low_ai_or_negative_pressure_eval_quality") or {})
    return {
        "fresh_eval": int(counter.get("fresh_eval", 0)),
        "stale_or_delayed_eval": int(counter.get("stale_or_delayed_eval", 0)),
        "unknown_eval_quality": int(counter.get("unknown_eval_quality", 0)),
    }


def _rollup_stale_or_delayed_eval_categories(items: list[dict[str, Any]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for item in items:
        counter.update(item.get("stale_or_delayed_eval_category_counts") or {})
    return {
        "diagnostic_quote_age_stale": int(counter.get("diagnostic_quote_age_stale", 0)),
        "full_eval_delay": int(counter.get("full_eval_delay", 0)),
        "ws_quote_missing": int(counter.get("ws_quote_missing", 0)),
        "pre_ai_stale_or_history_gap": int(counter.get("pre_ai_stale_or_history_gap", 0)),
        "pre_submit_hard_stale": int(counter.get("pre_submit_hard_stale", 0)),
    }


def _rollup_unresolved_stale_low_ai_pressure_count(items: list[dict[str, Any]]) -> int:
    return sum(int(item.get("unresolved_stale_low_ai_or_pressure_eval_count") or 0) for item in items)


def _unresolved_stale_low_ai_pressure_symbols(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    symbols = []
    for item in items:
        count = int(item.get("unresolved_stale_low_ai_or_pressure_eval_count") or 0)
        if count <= 0:
            continue
        latest = item.get("latest_blocker") if isinstance(item.get("latest_blocker"), dict) else {}
        symbols.append(
            {
                "stock_code": item.get("stock_code") or "",
                "stock_name": item.get("stock_name") or "",
                "event_count": count,
                "latest_stage": latest.get("stage") or "",
                "latest_reason": latest.get("reason") or "",
            }
        )
    return sorted(symbols, key=lambda item: int(item.get("event_count") or 0), reverse=True)


def _scanner_full_eval_budget_diagnostics(items: list[dict[str, Any]]) -> dict[str, Any]:
    symbol_rows: list[dict[str, Any]] = []
    total_count = 0
    for item in items:
        budget = item.get("scanner_full_eval_budget_deferred") or {}
        count = int(budget.get("count") or 0)
        if count <= 0:
            continue
        total_count += count
        symbol_rows.append(
            {
                "stock_code": item.get("stock_code") or "",
                "stock_name": item.get("stock_name") or "",
                "count": count,
                "latest_at": budget.get("latest_at") or "",
                "latest_price_delta_since_first_seen_pct": item.get("latest_price_delta_since_first_seen_pct"),
                "max_price_delta_since_first_seen_pct": item.get("max_price_delta_since_first_seen_pct"),
                "scanner_full_eval_limit": budget.get("scanner_full_eval_limit"),
                "scanner_rising_full_eval_extra_limit": budget.get("scanner_rising_full_eval_extra_limit"),
                "scanner_rising_full_eval_relief_count": budget.get("scanner_rising_full_eval_relief_count"),
                "scanner_full_eval_count": budget.get("scanner_full_eval_count"),
                "scanner_full_eval_budget_source": budget.get("scanner_full_eval_budget_source") or "",
                "deferred_status": budget.get("status") or "deferred_never_evaluated",
            }
        )
    symbol_rows.sort(
        key=lambda row: (
            int(row.get("count") or 0),
            row.get("max_price_delta_since_first_seen_pct") or -999.0,
        ),
        reverse=True,
    )
    return {
        "deferred_count": total_count,
        "symbol_count": len(symbol_rows),
        "top_symbols": symbol_rows[:12],
        "status_counts": _top_counter(
            Counter(str(row.get("deferred_status") or "deferred_never_evaluated") for row in symbol_rows),
            key_name="status",
        ),
        "decision_authority": "diagnostic_only_no_runtime_budget_change",
        "runtime_effect": False,
        "forbidden_uses": [
            "buy_score_relaxation",
            "threshold_relaxation",
            "stale_submit_bypass",
            "broker_guard_bypass",
            "unbounded_cpu_or_ai_budget_increase",
        ],
    }


def _actionable_scanner_full_eval_backpressure(scanner_budget: dict[str, Any]) -> list[dict[str, Any]]:
    actionable_rows: list[dict[str, Any]] = []
    for row in scanner_budget.get("top_symbols") or []:
        count = int(row.get("count") or 0)
        max_delta = _safe_float(row.get("max_price_delta_since_first_seen_pct"), 0.0) or 0.0
        if row.get("deferred_status") == "deferred_then_evaluated":
            continue
        if count < ACTIONABLE_FULL_EVAL_DEFERRED_MIN_COUNT and max_delta < ACTIONABLE_FULL_EVAL_DEFERRED_MIN_DELTA_PCT:
            continue
        actionable_rows.append(row)
    total_count = sum(int(row.get("count") or 0) for row in actionable_rows)
    if not actionable_rows:
        return []
    return [
        {
            "class": "runtime_backpressure",
            "stage": "scalping_scanner_watching_runtime_skip",
            "reason": "scanner_full_eval_loop_budget_deferred",
            "count": total_count,
            "symbol_count": len(actionable_rows),
        }
    ]


def _zero_strength_history_workorders(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    workorders: list[dict[str, Any]] = []
    for item in items:
        quality = item.get("zero_strength_history_source_quality") or {}
        event_count = int(quality.get("event_count") or 0)
        if event_count < ZERO_HISTORY_WORKORDER_MIN_EVENTS:
            continue
        workorders.append(
            {
                "workorder_type": "scanner_strength_momentum_history_missing",
                "stock_code": item.get("stock_code") or "",
                "stock_name": item.get("stock_name") or "",
                "event_count": event_count,
                "latest_at": quality.get("latest_at") or "",
                "latest_stage": quality.get("latest_stage") or "",
                "latest_reason": quality.get("latest_reason") or "",
                "top_reasons": quality.get("top_reasons") or [],
                "decision_authority": "source_quality_only",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "implementation_status": "implemented_source_quality_contract_available",
                "implementation_provenance": {
                    "implementation_type": "scanner_strength_history_source_quality_provenance",
                    "metric_role": "source_quality_gate",
                    "decision_authority": "source_quality_only",
                    "source_quality_route": quality.get("source_quality_route") or "",
                    "raw_event_count": quality.get("raw_event_count") or 0,
                    "recovered_by_downstream_progress": bool(
                        quality.get("recovered_by_downstream_progress")
                    ),
                    "history_count_keys": list(STRENGTH_HISTORY_COUNT_KEYS),
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "root_cause_closure_status_hint": "implementation_done",
                },
                "forbidden_uses": [
                    "buy_score_relaxation",
                    "ai_threshold_relaxation",
                    "strength_threshold_relaxation",
                    "broker_guard_bypass",
                    "stale_submit_bypass",
                    "real_order_approval",
                ],
                "next_action": (
                    "check_ws_strength_momentum_history_producer_and_subscription_tick_flow_before_strategy_tuning"
                ),
            }
        )
    return sorted(workorders, key=lambda item: item["event_count"], reverse=True)


def _runtime_attach_identity_workorders(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    workorders: list[dict[str, Any]] = []
    for item in items:
        mismatch = item.get("runtime_attach_identity_mismatch") or {}
        count = int(mismatch.get("count") or 0)
        if count <= 0:
            continue
        workorders.append(
            {
                "workorder_type": "scanner_runtime_attach_identity_mismatch",
                "stock_code": item.get("stock_code") or "",
                "stock_name": item.get("stock_name") or "",
                "event_count": count,
                "latest_at": mismatch.get("latest_at") or "",
                "latest_reason": mismatch.get("latest_reason") or "",
                "payload_name": mismatch.get("payload_name") or "",
                "db_name": mismatch.get("db_name") or "",
                "mismatch_expired": mismatch.get("mismatch_expired") or "",
                "decision_authority": "source_quality_only",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "implementation_status": "implemented_source_quality_contract_available",
                "implementation_provenance": {
                    "implementation_type": "scanner_runtime_attach_identity_source_quality_provenance",
                    "metric_role": "source_quality_gate",
                    "decision_authority": "source_quality_only",
                    "latest_reason": mismatch.get("latest_reason") or "",
                    "payload_name": mismatch.get("payload_name") or "",
                    "db_name": mismatch.get("db_name") or "",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "root_cause_closure_status_hint": "implementation_done",
                },
                "forbidden_uses": [
                    "buy_score_relaxation",
                    "ai_threshold_relaxation",
                    "broker_guard_bypass",
                    "stale_submit_bypass",
                    "real_order_approval",
                    "forced_one_share_success_counting",
                ],
                "next_action": (
                    "check_scanner_promotion_payload_and_db_runtime_target_attach_identity_normalization"
                ),
            }
        )
    return sorted(workorders, key=lambda item: item["event_count"], reverse=True)


def _freshness_recovery_workorders(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    workorders: list[dict[str, Any]] = []
    for item in items:
        categories = item.get("stale_or_delayed_eval_category_counts") or {}
        diagnostic_stale = int(categories.get("diagnostic_quote_age_stale") or 0)
        history_gap = int(categories.get("pre_ai_stale_or_history_gap") or 0)
        if diagnostic_stale <= 0 and history_gap <= 0:
            continue
        latest = item.get("latest_blocker") if isinstance(item.get("latest_blocker"), dict) else {}
        workorders.append(
            {
                "workorder_type": "bounded_rising_candidate_freshness_recheck",
                "stock_code": item.get("stock_code") or "",
                "stock_name": item.get("stock_name") or "",
                "diagnostic_quote_age_stale": diagnostic_stale,
                "pre_ai_stale_or_history_gap": history_gap,
                "event_count": diagnostic_stale + history_gap,
                "max_price_delta_since_first_seen_pct": item.get("max_price_delta_since_first_seen_pct"),
                "latest_stage": latest.get("stage") or "",
                "latest_reason": latest.get("reason") or "",
                "decision_authority": "source_quality_only",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "implementation_status": "implemented_source_quality_contract_available",
                "implementation_provenance": {
                    "implementation_type": "bounded_rising_freshness_recheck_source_provenance",
                    "metric_role": "source_quality_gate",
                    "decision_authority": "source_quality_only",
                    "diagnostic_quote_age_stale": diagnostic_stale,
                    "pre_ai_stale_or_history_gap": history_gap,
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "root_cause_closure_status_hint": "implementation_done",
                },
                "forbidden_uses": [
                    "buy_score_relaxation",
                    "ai_threshold_relaxation",
                    "strength_threshold_relaxation",
                    "broker_guard_bypass",
                    "stale_submit_bypass",
                    "real_order_approval",
                    "unbounded_cpu_or_ai_budget_increase",
                ],
                "next_action": (
                    "add_or_tune_bounded_fresh_recheck_enqueue_after_stale_or_history_gap"
                ),
            }
        )
    return sorted(
        workorders,
        key=lambda item: (
            int(item.get("event_count") or 0),
            _safe_float(item.get("max_price_delta_since_first_seen_pct"), -999.0) or -999.0,
        ),
        reverse=True,
    )


def _rising_missed_classification_for_item(item: dict[str, Any], *, rising_threshold_pct: float) -> dict[str, Any]:
    dominant = item.get("dominant_actionable_blocker") if isinstance(item.get("dominant_actionable_blocker"), dict) else {}
    blocker_class = str(dominant.get("class") or "")
    blocker_route = str(dominant.get("route") or "")
    budget = item.get("scanner_full_eval_budget_deferred") if isinstance(item.get("scanner_full_eval_budget_deferred"), dict) else {}
    quality = item.get("zero_strength_history_source_quality") if isinstance(item.get("zero_strength_history_source_quality"), dict) else {}
    recent_blockers = item.get("recent_blockers") if isinstance(item.get("recent_blockers"), list) else []
    recent_taxonomies = [
        row.get("taxonomy")
        for row in recent_blockers
        if isinstance(row, dict) and isinstance(row.get("taxonomy"), dict)
    ]
    recent_preserved_guard = any(
        str(taxonomy.get("class") or "") in {"submit_hard_guard", "intended_guard"}
        or (
            str(taxonomy.get("class") or "") == "pre_submit_quality_guard"
            and str(taxonomy.get("route") or "").startswith("known_")
        )
        for taxonomy in recent_taxonomies
    )
    source_quality_excluded = (
        int(item.get("unresolved_stale_low_ai_or_pressure_eval_count") or 0) > 0
        or int((item.get("runtime_attach_identity_mismatch") or {}).get("count") or 0) > 0
        or int(quality.get("event_count") or 0) >= ZERO_HISTORY_WORKORDER_MIN_EVENTS
        or blocker_class in {"source_freshness_blocker", "source_freshness_evictable"}
        or bool(item.get("rising_missed_entry_ai_not_evaluated_excluded"))
    )
    intended_guard_preserved = (
        blocker_class in {"submit_hard_guard", "intended_guard"}
        or (blocker_class == "pre_submit_quality_guard" and blocker_route.startswith("known_"))
        or recent_preserved_guard
    )
    runtime_backpressure_observation = int(budget.get("count") or 0) > 0
    strategy_reject_missed = blocker_class == "strategy_reject"
    actionable_major_missed = bool(dominant.get("stage")) and blocker_class not in {
        "",
        "non_actionable_guard_or_backpressure",
        "strategy_reject",
        "submit_hard_guard",
        "source_freshness_blocker",
        "source_freshness_evictable",
    }
    classification = classify_rising_missed_candidate(
        max_delta_pct=item.get("max_price_delta_since_first_seen_pct"),
        real_submit_count=item.get("real_submit_count"),
        min_delta_pct=rising_threshold_pct,
        source_quality_excluded=source_quality_excluded,
        intended_guard_preserved=intended_guard_preserved,
        runtime_backpressure_observation=runtime_backpressure_observation,
        strategy_reject_missed=strategy_reject_missed,
        actionable_major_missed=actionable_major_missed,
    )
    return {
        "rising_missed_class": classification.rising_missed_class,
        "rising_missed_class_reason": BLOCK_ENTRY_AI_NOT_EVALUATED
        if classification.rising_missed and item.get("rising_missed_entry_ai_not_evaluated_excluded")
        else classification.reason,
        "rising_missed_one_share_eligible": classification.one_share_eligible,
        "rising_missed_class_flags": {
            RISING_MISSED_CLASS_SOURCE_QUALITY_EXCLUDED: source_quality_excluded,
            RISING_MISSED_CLASS_INTENDED_GUARD_PRESERVED: intended_guard_preserved,
            RISING_MISSED_CLASS_RUNTIME_BACKPRESSURE: runtime_backpressure_observation,
            RISING_MISSED_CLASS_STRATEGY_REJECT: strategy_reject_missed,
            RISING_MISSED_CLASS_ACTIONABLE_MAJOR: actionable_major_missed,
        },
    }


def _root_cause_priorities(
    *,
    rising_missed: list[dict[str, Any]],
    falling_submitted: list[dict[str, Any]],
    summaries: list[dict[str, Any]],
    scanner_budget: dict[str, Any],
    entry_price: dict[str, Any],
    scale_in: dict[str, Any],
    post_sell: dict[str, Any],
) -> list[dict[str, Any]]:
    priorities: list[dict[str, Any]] = []

    zero_history = _zero_strength_history_workorders(rising_missed)
    stale_eval_count = _rollup_low_ai_pressure_quality(rising_missed).get("stale_or_delayed_eval", 0)
    unresolved_stale_eval_count = _rollup_unresolved_stale_low_ai_pressure_count(rising_missed)
    unresolved_stale_eval_symbols = _unresolved_stale_low_ai_pressure_symbols(rising_missed)
    if zero_history or unresolved_stale_eval_count:
        priorities.append(
            {
                "priority": 1,
                "issue": "scanner_strength_history_or_stale_eval",
                "decision": "fix_observation_freshness_before_threshold_tuning",
                "evidence": {
                    "rising_missed_symbols": len(rising_missed),
                    "repeated_zero_strength_history_symbols": len(zero_history),
                    "stale_or_delayed_low_ai_or_pressure_events": stale_eval_count,
                    "stale_or_delayed_eval_category_counts": _rollup_stale_or_delayed_eval_categories(
                        rising_missed
                    ),
                    "unresolved_stale_or_delayed_low_ai_or_pressure_events": unresolved_stale_eval_count,
                    "top_symbols": [
                        {
                            "stock_code": item.get("stock_code") or "",
                            "stock_name": item.get("stock_name") or "",
                            "event_count": item.get("event_count") or 0,
                            "latest_reason": item.get("latest_reason") or "",
                        }
                        for item in zero_history[:8]
                    ],
                    "top_unresolved_stale_eval_symbols": unresolved_stale_eval_symbols[:8],
                },
                "next_action": "inspect_ws_strength_momentum_history_and_subscription_recheck_flow",
                "runtime_effect": False,
                "forbidden_uses": [
                    "buy_score_relaxation",
                    "strength_threshold_relaxation",
                    "stale_submit_bypass",
                    "broker_guard_bypass",
                ],
            }
        )

    budget_deferred_count = int(scanner_budget.get("deferred_count") or 0)
    actionable_backpressure = _actionable_scanner_full_eval_backpressure(scanner_budget)
    if budget_deferred_count and actionable_backpressure:
        priorities.append(
            {
                "priority": 2,
                "issue": "scanner_full_eval_budget_deferred",
                "decision": "treat_only_sla_breach_as_evaluation_throughput_bottleneck",
                "evidence": {
                    "deferred_count": budget_deferred_count,
                    "symbol_count": int(scanner_budget.get("symbol_count") or 0),
                    "top_symbols": scanner_budget.get("top_symbols") or [],
                    "actionable_backpressure_counts": actionable_backpressure,
                },
                "next_action": "raise_only_bounded_scanner_eval_capacity_if_high_delta_candidates_keep_deferred",
                "runtime_effect": False,
                "forbidden_uses": scanner_budget.get("forbidden_uses") or [
                    "buy_score_relaxation",
                    "threshold_relaxation",
                    "stale_submit_bypass",
                    "broker_guard_bypass",
                ],
            }
        )

    ai_wait = 0
    for item in rising_missed:
        for blocker in item.get("recent_blockers") or []:
            if blocker.get("stage") in {"blocked_ai_score", "ai_confirmed_terminal_no_budget", "first_ai_wait"}:
                ai_wait += 1
    if ai_wait:
        priorities.append(
            {
                "priority": 3,
                "issue": "ai_wait_or_baseline_prior_score_block",
                "decision": "do_not_relax_score_without_fresh_positive_context_and_rolling_confirmation",
                "evidence": {
                    "recent_ai_wait_blockers": ai_wait,
                    "rising_missed_symbols": len(rising_missed),
                    "top_symbols": [
                        {
                            "stock_code": item.get("stock_code") or "",
                            "stock_name": item.get("stock_name") or "",
                            "latest_ai_score": item.get("latest_ai_score"),
                            "latest_entry_score_threshold": item.get("latest_entry_score_threshold"),
                            "latest_blocker": item.get("latest_blocker") or {},
                        }
                        for item in rising_missed[:8]
                    ],
                },
                "next_action": "separate_fresh_low_score_wait_from_stale_or_negative_pressure_wait",
                "runtime_effect": False,
                "forbidden_uses": [
                    "intraday_threshold_mutation",
                    "broad_buy_score_relaxation",
                    "real_order_approval",
                ],
            }
        )

    price_block_count = int(entry_price.get("block_or_unfilled_count") or 0)
    price_candidate_failure_count = int(entry_price.get("candidate_failure_count") or 0)
    if price_block_count or price_candidate_failure_count:
        priorities.append(
            {
                "priority": 4,
                "issue": "entry_price_or_submit_price_guard_block",
                "decision": "review_price_resolution_quality_without_stale_submit_bypass",
                "evidence": {
                    "block_or_unfilled_count": price_block_count,
                    "candidate_failure_count": price_candidate_failure_count,
                    "candidate_failure_reason_counts": entry_price.get("candidate_failure_reason_counts") or [],
                    "stage_counts": entry_price.get("stage_counts") or [],
                    "recent_issues": entry_price.get("recent_issues") or [],
                },
                "next_action": "inspect_invalid_price_and_pre_submit_guard_rows_before_order_price_changes",
                "runtime_effect": False,
                "forbidden_uses": [
                    "stale_submit_bypass",
                    "broker_guard_bypass",
                    "intraday_order_price_relaxation_without_operator_override",
                ],
            }
        )

    scale_block_count = int(scale_in.get("blocked_count") or 0)
    if scale_block_count:
        priorities.append(
            {
                "priority": 5,
                "issue": "scale_in_blocked",
                "decision": "preserve_scale_in_safety_and_find_blocker_class",
                "evidence": {
                    "blocked_count": scale_block_count,
                    "executed_count": int(scale_in.get("executed_count") or 0),
                    "blocker_reason_counts": scale_in.get("blocker_reason_counts") or [],
                    "recent_blockers": scale_in.get("recent_blockers") or [],
                },
                "next_action": "separate_price_guard_qty_guard_and_window_guard_before_scale_in_change",
                "runtime_effect": False,
                "forbidden_uses": [
                    "scale_in_guard_bypass",
                    "quantity_cap_release",
                    "hard_safety_relaxation",
                    "broker_guard_bypass",
                ],
            }
        )

    if falling_submitted:
        priorities.append(
            {
                "priority": 6,
                "issue": "falling_promoted_real_submit",
                "decision": "minimize_bad_entry_before_any_entry_relief",
                "evidence": {
                    "falling_real_submitted_count": len(falling_submitted),
                    "examples": falling_submitted[:8],
                },
                "next_action": "trace_submit_stage_and_entry_context_for_each_falling_submit",
                "runtime_effect": False,
                "forbidden_uses": [
                    "entry_relief_that_increases_falling_submit_risk",
                    "broker_guard_bypass",
                ],
            }
        )

    if int(post_sell.get("missed_upside_count") or 0) or int(post_sell.get("bad_entry_after_sell_count") or 0):
        priorities.append(
            {
                "priority": 7,
                "issue": "post_sell_missed_upside_or_bad_entry",
                "decision": "use_as_exit_entry_diagnostic_not_intraday_exit_mutation",
                "evidence": {
                    "missed_upside_count": int(post_sell.get("missed_upside_count") or 0),
                    "bad_entry_after_sell_count": int(post_sell.get("bad_entry_after_sell_count") or 0),
                    "top_missed_upside": post_sell.get("top_missed_upside") or [],
                    "bad_entry_examples": post_sell.get("bad_entry_examples") or [],
                },
                "next_action": "split_stop_loss_and_take_profit_flows_after_post_sell_window_matures",
                "runtime_effect": False,
                "forbidden_uses": [
                    "intraday_exit_threshold_mutation",
                    "hard_stop_relaxation",
                    "automatic_exit_deferral",
                ],
            }
        )

    if not priorities and summaries:
        priorities.append(
            {
                "priority": 1,
                "issue": "no_major_actionable_root_cause_in_current_window",
                "decision": "continue_observation",
                "evidence": {
                    "promoted_symbol_count": len(summaries),
                    "rising_missed_symbols": len(rising_missed),
                    "falling_real_submitted_count": len(falling_submitted),
                },
                "next_action": "rerun_next_interval",
                "runtime_effect": False,
                "forbidden_uses": ["runtime_mutation_without_new_evidence"],
            }
        )
    return priorities


def build_report(
    *,
    target_date: str,
    pipeline_path: Path,
    post_sell_dir: Path | None = None,
    generated_at: str | None = None,
    since: str | None = None,
    event_until: str | None = None,
    rising_threshold_pct: float = 1.0,
    falling_threshold_pct: float = -0.1,
) -> dict[str, Any]:
    all_rows = _read_jsonl(pipeline_path)
    normalized_since = _normalize_event_bound(since, target_date=target_date)
    normalized_until = _normalize_event_bound(event_until, target_date=target_date)
    source_rows = [row for row in all_rows if not normalized_until or _event_time(row) <= normalized_until]
    full_grouped = _entry_events(source_rows)
    rows = source_rows
    if normalized_since:
        rows = [row for row in rows if _event_time(row) >= normalized_since]
    real_rows = _real_rows(all_rows, since=since, event_until=event_until, target_date=target_date)
    grouped = _entry_events(rows)
    real_entry_event_count = sum(len(events) for events in grouped.values())
    summaries = [
        _summarize_code(code, events, promotion_source_rows=full_grouped.get(code, events))
        for code, events in grouped.items()
        if any(row.get("stage") == PROMOTED_STAGE for row in full_grouped.get(code, events))
    ]
    for item in summaries:
        item.update(_rising_missed_classification_for_item(item, rising_threshold_pct=rising_threshold_pct))
    rising_missed = [
        item
        for item in summaries
        if item.get("rising_missed_class") not in {
            RISING_MISSED_CLASS_NOT_RISING,
            RISING_MISSED_CLASS_SUBMITTED_RESOLVED,
        }
        and not item.get("rising_missed_entry_ai_not_evaluated_excluded")
    ]
    rising_missed_ai_not_evaluated_excluded = [
        item
        for item in summaries
        if item.get("rising_missed_class") not in {
            RISING_MISSED_CLASS_NOT_RISING,
            RISING_MISSED_CLASS_SUBMITTED_RESOLVED,
        }
        and item.get("rising_missed_entry_ai_not_evaluated_excluded")
    ]
    falling_submitted = [
        item
        for item in summaries
        if (item["latest_price_delta_since_first_seen_pct"] or 0.0) <= falling_threshold_pct
        and item["real_submit_count"] > 0
    ]
    non_rising_promoted = [
        item
        for item in summaries
        if (item["max_price_delta_since_first_seen_pct"] or 0.0) < rising_threshold_pct
    ]
    falling_promoted = [
        item
        for item in summaries
        if (item["latest_price_delta_since_first_seen_pct"] or 0.0) <= falling_threshold_pct
    ]
    blocker_counter: Counter[tuple[str, str]] = Counter()
    for item in summaries:
        for blocker in item["recent_blockers"]:
            if blocker["stage"]:
                blocker_counter[(blocker["stage"], blocker["reason"])] += 1
    entry_price = _entry_price_diagnostics(real_rows)
    scale_in = _scale_in_diagnostics(real_rows)
    post_sell = _post_sell_flow_diagnostics(
        target_date=target_date,
        post_sell_dir=post_sell_dir or PROJECT_ROOT / "data" / "post_sell",
    )
    scanner_budget = _scanner_full_eval_budget_diagnostics(rising_missed)
    blocker_taxonomy = _rollup_blocker_taxonomy(summaries)
    selection_prior_counts = _selection_prior_counts(rising_missed)
    selection_positive_or_recheck_count = sum(
        selection_prior_counts.get(key, 0) for key in ("positive_prior", "recheck_prior")
    )
    selection_risk_count = sum(
        selection_prior_counts.get(key, 0) for key in SELECTION_PRIOR_RISK_RECOMMENDATIONS
    )
    return {
        "schema_version": 1,
        "report_type": "intraday_entry_blocker_diagnostics",
        "target_date": target_date,
        "generated_at": generated_at or datetime.now().isoformat(timespec="seconds"),
        "source_pipeline_events": str(pipeline_path),
        "event_window": {
            "since": since or "",
            "until": event_until or "",
        },
        "thresholds": {
            "rising_missed_pct": rising_threshold_pct,
            "falling_submitted_pct": falling_threshold_pct,
        },
        "metric_contracts": {
            "rising_missed_low_ai_or_negative_pressure_eval_quality": {
                "metric_role": "source_quality_gate",
                "decision_authority": "diagnostic_only",
                "window_policy": "intraday_event_window",
                "sample_floor": "none_diagnostic",
                "primary_decision_metric": False,
                "source_quality_gate": "entry_eval_freshness_context",
                "forbidden_uses": [
                    "buy_score_relaxation",
                    "ai_threshold_relaxation",
                    "broker_guard_bypass",
                    "stale_submit_bypass",
                    "real_order_approval",
                ],
            },
            "rising_missed_stale_or_delayed_eval_category_counts": {
                "metric_role": "source_quality_gate",
                "decision_authority": "diagnostic_only",
                "window_policy": "intraday_event_window",
                "sample_floor": "none_diagnostic",
                "primary_decision_metric": False,
                "source_quality_gate": "entry_eval_freshness_cause_classification",
                "forbidden_uses": [
                    "buy_score_relaxation",
                    "ai_threshold_relaxation",
                    "broker_guard_bypass",
                    "stale_submit_bypass",
                    "real_order_approval",
                ],
            },
            "repeated_zero_strength_history_source_quality_workorders": {
                "metric_role": "source_quality_gate",
                "decision_authority": "source_quality_only",
                "window_policy": "intraday_event_window",
                "sample_floor": f"{ZERO_HISTORY_WORKORDER_MIN_EVENTS}_events_per_symbol",
                "primary_decision_metric": False,
                "source_quality_gate": "strength_momentum_history_available_before_entry_quality_judgment",
                "forbidden_uses": [
                    "buy_score_relaxation",
                    "ai_threshold_relaxation",
                    "strength_threshold_relaxation",
                    "broker_guard_bypass",
                    "stale_submit_bypass",
                    "real_order_approval",
                ],
            },
            "runtime_attach_identity_mismatch_workorders": {
                "metric_role": "source_quality_gate",
                "decision_authority": "source_quality_only",
                "window_policy": "intraday_event_window",
                "sample_floor": "1_mismatch_event_per_symbol",
                "primary_decision_metric": False,
                "source_quality_gate": "scanner_promotion_payload_matches_runtime_target_identity",
                "forbidden_uses": [
                    "buy_score_relaxation",
                    "ai_threshold_relaxation",
                    "broker_guard_bypass",
                    "stale_submit_bypass",
                    "real_order_approval",
                    "forced_one_share_success_counting",
                ],
            },
            "bounded_freshness_recovery_workorders": {
                "metric_role": "source_quality_gate",
                "decision_authority": "source_quality_only",
                "window_policy": "intraday_event_window",
                "sample_floor": "1_stale_or_history_gap_event_per_symbol",
                "primary_decision_metric": False,
                "source_quality_gate": "fresh_entry_eval_before_strategy_threshold_judgment",
                "forbidden_uses": [
                    "buy_score_relaxation",
                    "ai_threshold_relaxation",
                    "strength_threshold_relaxation",
                    "broker_guard_bypass",
                    "stale_submit_bypass",
                    "real_order_approval",
                    "unbounded_cpu_or_ai_budget_increase",
                ],
            },
            "scanner_full_eval_budget_diagnostics": {
                "metric_role": "runtime_evaluation_throughput_diagnostic",
                "decision_authority": "diagnostic_only",
                "window_policy": "same_day_intraday_light",
                "sample_floor": "none_intraday_diagnostic",
                "primary_decision_metric": False,
                "source_quality_gate": "scanner_runtime_skip_fields_present",
                "forbidden_uses": [
                    "buy_score_relaxation",
                    "threshold_relaxation",
                    "stale_submit_bypass",
                    "broker_guard_bypass",
                    "unbounded_cpu_or_ai_budget_increase",
                ],
            },
            "rising_missed_selection_prior": {
                "metric_role": "selection_priority_diagnostic",
                "decision_authority": "source_only_scanner_ranking_hint",
                "window_policy": "preopen_verified_policy_catalog_only",
                "sample_floor": "none_ranking_hint",
                "primary_decision_metric": False,
                "source_quality_gate": "KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_FILE_catalog_contract",
                "forbidden_uses": [
                    "forced_one_share_allow_block_change",
                    "real_order_approval",
                    "threshold_relaxation",
                    "broker_guard_bypass",
                    "provider_route_change",
                    "bot_restart_trigger",
                ],
            },
            "rising_missed_ai_not_evaluated_exclusion": {
                "metric_role": "source_quality_gate",
                "decision_authority": "exclude_not_evaluated_entry_ai_from_rising_missed_selection",
                "window_policy": "same_day_intraday_entry_snapshot",
                "sample_floor": "1_not_evaluated_entry_ai_snapshot",
                "primary_decision_metric": False,
                "source_quality_gate": "submit_or_latest_entry_snapshot_ai_action_available",
                "forbidden_uses": [
                    "threshold_relaxation",
                    "broker_guard_bypass",
                    "stale_submit_bypass",
                    "provider_route_change",
                    "bot_restart_trigger",
                    "real_order_approval",
                ],
            },
            "blocker_taxonomy": {
                "metric_role": "funnel_count",
                "decision_authority": "diagnostic_taxonomy_only",
                "window_policy": "intraday_event_window",
                "sample_floor": "none_diagnostic",
                "primary_decision_metric": False,
                "source_quality_gate": "blocker_stage_reason_fields_present",
                "forbidden_uses": [
                    "guard_bypass",
                    "stale_submit_bypass",
                    "intraday_threshold_mutation",
                    "real_order_approval",
                ],
            },
            "entry_price_execution": {
                "metric_role": "execution_quality_real_only",
                "decision_authority": "diagnostic_only",
                "window_policy": "same_day_intraday_light",
                "sample_floor": "none_intraday_diagnostic",
                "primary_decision_metric": False,
                "source_quality_gate": "fresh_entry_pipeline_event_and_price_context_fields",
                "forbidden_uses": [
                    "entry_price_relaxation_without_operator_override",
                    "stale_submit_bypass",
                    "broker_guard_bypass",
                    "real_order_approval",
                ],
            },
            "scale_in_diagnostics": {
                "metric_role": "funnel_count",
                "decision_authority": "diagnostic_only",
                "window_policy": "same_day_intraday_light",
                "sample_floor": "none_intraday_diagnostic",
                "primary_decision_metric": False,
                "source_quality_gate": "holding_pipeline_scale_in_fields_present",
                "forbidden_uses": [
                    "scale_in_guard_bypass",
                    "quantity_cap_release",
                    "hard_safety_relaxation",
                    "broker_guard_bypass",
                ],
            },
            "post_sell_flow_diagnostics": {
                "metric_role": "exit_post_sell_dimension",
                "decision_authority": "diagnostic_only",
                "window_policy": "same_day_post_sell_forward_window",
                "sample_floor": "rolling_window_required_before_any_runtime_change",
                "primary_decision_metric": "sim_post_decision_mfe_10m_pct",
                "source_quality_gate": "post_sell_candidate_plus_evaluation_join",
                "forbidden_uses": [
                    "intraday_exit_threshold_mutation",
                    "automatic_exit_deferral",
                    "hard_stop_relaxation",
                    "broker_guard_bypass",
                    "provider_route_change",
                    "bot_restart_trigger",
                ],
            },
        },
        "scanner_full_eval_budget_diagnostics": scanner_budget,
        "blocker_taxonomy": blocker_taxonomy,
        "entry_price_execution": entry_price,
        "scale_in_diagnostics": scale_in,
        "post_sell_flow_diagnostics": post_sell,
        "summary": {
            "entry_event_count": real_entry_event_count,
            "promoted_symbol_count": len(summaries),
            "promoted_before_window_symbol_count": sum(
                1 for item in summaries if not item.get("promoted_in_event_window")
            ),
            "rising_missed_buy_count": len(rising_missed),
            "rising_missed_ai_not_evaluated_excluded_count": len(
                rising_missed_ai_not_evaluated_excluded
            ),
            "rising_missed_ai_not_evaluated_excluded_symbols": [
                item.get("stock_code") or "" for item in rising_missed_ai_not_evaluated_excluded
            ],
            "falling_real_submitted_count": len(falling_submitted),
            "real_submit_symbol_count": sum(1 for item in summaries if item["real_submit_count"] > 0),
            "excluded_analysis_scope": "sim_swing_and_rising_missed_forced_one_share_events",
            "rising_missed_low_ai_or_negative_pressure_eval_quality": _rollup_low_ai_pressure_quality(
                rising_missed
            ),
            "rising_missed_stale_or_delayed_eval_category_counts": _rollup_stale_or_delayed_eval_categories(
                rising_missed
            ),
            "repeated_zero_strength_history_workorder_count": len(
                _zero_strength_history_workorders(summaries)
            ),
            "rising_missed_repeated_zero_strength_history_workorder_count": len(
                _zero_strength_history_workorders(rising_missed)
            ),
            "runtime_attach_identity_mismatch_workorder_count": len(
                _runtime_attach_identity_workorders(summaries)
            ),
            "rising_missed_runtime_attach_identity_mismatch_workorder_count": len(
                _runtime_attach_identity_workorders(rising_missed)
            ),
            "rising_missed_freshness_recovery_workorder_count": len(
                _freshness_recovery_workorders(rising_missed)
            ),
            "rising_missed_full_eval_budget_deferred_count": int(
                scanner_budget.get("deferred_count") or 0
            ),
            "rising_missed_full_eval_budget_deferred_symbol_count": int(
                scanner_budget.get("symbol_count") or 0
            ),
            "rising_missed_class_counts": _top_counter(
                Counter(str(item.get("rising_missed_class") or "") for item in rising_missed),
                key_name="class",
            ),
            "rising_missed_selection_prior_recommendation_counts": _top_counter(
                selection_prior_counts,
                key_name="recommendation",
            ),
            "rising_missed_selection_positive_or_recheck_count": selection_positive_or_recheck_count,
            "rising_missed_selection_risk_count": selection_risk_count,
            "rising_missed_one_share_eligible_symbol_count": sum(
                1 for item in rising_missed if bool(item.get("rising_missed_one_share_eligible"))
            ),
            "actionable_major_blocker_count": sum(
                int(item.get("count") or 0)
                for item in blocker_taxonomy.get("actionable_major_blocker_counts", [])
            ),
            "suppressed_non_actionable_blocker_count": sum(
                int(item.get("count") or 0)
                for item in blocker_taxonomy.get("suppressed_non_actionable_counts", [])
            ),
        },
        "source_quality_workorders": {
            "repeated_zero_strength_history": _zero_strength_history_workorders(summaries),
            "rising_missed_repeated_zero_strength_history": _zero_strength_history_workorders(
                rising_missed
            ),
            "runtime_attach_identity_mismatch": _runtime_attach_identity_workorders(summaries),
            "rising_missed_runtime_attach_identity_mismatch": _runtime_attach_identity_workorders(
                rising_missed
            ),
            "rising_missed_freshness_recovery": _freshness_recovery_workorders(rising_missed),
        },
        "root_cause_priorities": _root_cause_priorities(
            rising_missed=rising_missed,
            falling_submitted=falling_submitted,
            summaries=summaries,
            scanner_budget=scanner_budget,
            entry_price=entry_price,
            scale_in=scale_in,
            post_sell=post_sell,
        ),
        "blocker_rollup": [
            {"stage": stage, "reason": reason, "count": count}
            for (stage, reason), count in blocker_counter.most_common()
        ],
        "relief_blocker_split_rollup": {
            "rising_missed_buy": _rollup_blockers(rising_missed),
            "non_rising_promoted": _rollup_blockers(non_rising_promoted),
            "falling_promoted": _rollup_blockers(falling_promoted),
        },
        "rising_missed_buy": sorted(
            rising_missed,
            key=_selection_prior_sort_key,
        ),
        "rising_missed_ai_not_evaluated_excluded": sorted(
            rising_missed_ai_not_evaluated_excluded,
            key=lambda item: item["max_price_delta_since_first_seen_pct"] or -999.0,
            reverse=True,
        ),
        "falling_real_submitted": sorted(
            falling_submitted,
            key=lambda item: item["latest_price_delta_since_first_seen_pct"] or 999.0,
        ),
        "promoted_symbols": sorted(
            summaries,
            key=lambda item: item["max_price_delta_since_first_seen_pct"] or -999.0,
            reverse=True,
        ),
    }


def _default_pipeline_path(target_date: str) -> Path:
    plain_path = PROJECT_ROOT / "data" / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"
    if plain_path.exists():
        return plain_path
    gz_path = plain_path.with_suffix(plain_path.suffix + ".gz")
    return gz_path if gz_path.exists() else plain_path


def _default_output_path(target_date: str) -> Path:
    return (
        PROJECT_ROOT
        / "data"
        / "report"
        / "intraday_entry_blocker_diagnostics"
        / f"intraday_entry_blocker_diagnostics_{target_date}.json"
    )


def _parse_hhmm(value: str) -> dt_time:
    hour_text, minute_text = str(value).strip().split(":", 1)
    return dt_time(int(hour_text), int(minute_text))


def _within_time_window(now_value: datetime, *, start: dt_time, end: dt_time) -> bool:
    current = now_value.time()
    return start <= current <= end


def _loop_should_stop(now_value: datetime, *, until: dt_time | None) -> bool:
    return until is not None and now_value.time() > until


def _build_write_report(args: argparse.Namespace) -> dict[str, Any]:
    pipeline_path = args.pipeline_path or _default_pipeline_path(args.target_date)
    output_path = args.output or _default_output_path(args.target_date)
    report = build_report(
        target_date=args.target_date,
        pipeline_path=pipeline_path,
        post_sell_dir=args.post_sell_dir,
        since=args.since,
        event_until=args.event_until,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "output": str(output_path),
        **report["summary"],
        "root_cause_priorities": report.get("root_cause_priorities", []),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build intraday entry blocker diagnostics from pipeline events.")
    parser.add_argument("--target-date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--pipeline-path", type=Path)
    parser.add_argument("--post-sell-dir", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--since", help="Only include events with emitted_at at or after this ISO timestamp.")
    parser.add_argument("--event-until", help="Only include events with emitted_at at or before this ISO timestamp.")
    parser.add_argument("--print-summary", action="store_true")
    parser.add_argument("--loop", action="store_true", help="Repeat report generation until --until.")
    parser.add_argument("--interval-sec", type=int, default=180)
    parser.add_argument("--until", help="Stop after local HH:MM, for example 19:00.")
    parser.add_argument("--buy-window-only", action="store_true")
    parser.add_argument("--buy-window-start", default="09:00")
    parser.add_argument("--buy-window-end", default="15:20")
    args = parser.parse_args(argv)

    until = _parse_hhmm(args.until) if args.until else None
    buy_start = _parse_hhmm(args.buy_window_start) if args.buy_window_start else DEFAULT_BUY_WINDOW_START
    buy_end = _parse_hhmm(args.buy_window_end) if args.buy_window_end else DEFAULT_BUY_WINDOW_END
    interval_sec = max(1, int(args.interval_sec or 180))

    while True:
        now_value = datetime.now()
        if _loop_should_stop(now_value, until=until):
            if args.print_summary:
                print(
                    json.dumps(
                        {"status": "stopped_after_until", "now": now_value.isoformat(timespec="seconds")},
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                    flush=True,
                )
            break
        if args.buy_window_only and not _within_time_window(now_value, start=buy_start, end=buy_end):
            if args.print_summary:
                print(
                    json.dumps(
                        {"status": "paused_outside_buy_window", "now": now_value.isoformat(timespec="seconds")},
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                    flush=True,
                )
        else:
            summary = _build_write_report(args)
            if args.print_summary:
                print(json.dumps(summary, ensure_ascii=False, sort_keys=True), flush=True)
        if not args.loop:
            break
        time.sleep(interval_sec)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import gzip
import json
import time
from collections import Counter, defaultdict
from datetime import datetime, time as dt_time
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENTRY_PIPELINE = "ENTRY_PIPELINE"
PROMOTED_STAGE = "scalping_scanner_candidate_promoted"
REAL_SUBMIT_TRUE = "true"

BLOCKER_STAGES = {
    "ai_confirmed_terminal_no_budget",
    "blocked_ai_score",
    "blocked_gap_from_scan",
    "blocked_liquidity",
    "blocked_overbought",
    "blocked_strength_momentum",
    "blocked_vpw",
    "first_ai_wait",
    "score65_74_recovery_probe_blocked",
    "scalping_scanner_watch_eviction",
    "scalping_scanner_watching_runtime_skip",
}

RECOVERY_OBSERVATION_REASONS = {
    "scanner_fast_precheck_subscription_recheck_snapshot_applied",
    "scanner_fast_precheck_stale_ws_recovered",
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

RELIEF_BLOCKER_REASONS = {
    "scanner_full_eval_loop_budget_deferred",
    "entry_cooldown_active",
    "scalping_new_buy_cutoff",
    "outside_scalping_buy_window",
    "ws_snapshot_missing_or_zero",
    "ws_snapshot_missing_or_zero_recovered",
}

LOW_AI_SCORE_CUTOFF = 65.0
NEGATIVE_BUY_PRESSURE_CUTOFF = 0.0
ENTRY_FRESH_MAX_AGE_MS = 3000.0
ZERO_HISTORY_WORKORDER_MIN_EVENTS = 2
DEFAULT_BUY_WINDOW_START = dt_time(9, 0)
DEFAULT_BUY_WINDOW_END = dt_time(15, 20)

STRENGTH_HISTORY_COUNT_KEYS = (
    "ws_strength_history_count",
    "strength_momentum_history_count",
    "pre_ai_ws_snapshot_refresh_history_count",
    "refresh_history_count",
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
    authority = str(fields.get("decision_authority") or "").lower()
    return "sim_" in authority or "swing_" in authority


def _entry_events(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("pipeline") != ENTRY_PIPELINE:
            continue
        if _exclude_from_real_entry_analysis(row):
            continue
        code = str(row.get("stock_code") or "").strip()
        if not code or code == "-":
            continue
        grouped[code].append(row)
    return dict(grouped)


def _field(row: dict[str, Any], key: str, default: Any = "") -> Any:
    fields = row.get("fields")
    if not isinstance(fields, dict):
        return default
    return fields.get(key, default)


def _blocker_reason(row: dict[str, Any]) -> str:
    for key in (
        "reason",
        "block_reason",
        "skip_reason",
        "scanner_watch_skip_reason",
        "scanner_block_reason",
        "budget_block_reason",
        "terminal_reason",
        "scalp_sim_candidate_window_blocked_reason",
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
    reason = _blocker_reason(row).lower()
    stage = str(row.get("stage") or "").lower()
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    context_text = " ".join(
        str(value).lower()
        for key, value in fields.items()
        if any(token in str(key).lower() for token in ("stale", "fresh", "snapshot", "subscription"))
    )
    if any(
        token in f"{stage} {reason} {context_text}"
        for token in (
            "stale",
            "ws_snapshot_missing_or_zero",
            "subscription_alive_but_entry_stale",
            "insufficient_history",
        )
    ):
        return True
    max_age_ms = _event_max_age_ms(row)
    return max_age_ms is not None and max_age_ms > ENTRY_FRESH_MAX_AGE_MS


def _event_is_fresh_context(row: dict[str, Any]) -> bool:
    max_age_ms = _event_max_age_ms(row)
    return max_age_ms is not None and max_age_ms <= ENTRY_FRESH_MAX_AGE_MS and not _event_has_stale_or_delayed_context(row)


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


def _strength_history_count(row: dict[str, Any]) -> int | None:
    for key in STRENGTH_HISTORY_COUNT_KEYS:
        value = _safe_float(_field(row, key))
        if value is not None:
            return int(value)
    return None


def _is_zero_strength_history_source_quality_event(row: dict[str, Any]) -> bool:
    history_count = _strength_history_count(row)
    if history_count is None or history_count > 0:
        return False
    stage = str(row.get("stage") or "").lower()
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


def _zero_strength_history_source_quality(rows: list[dict[str, Any]]) -> dict[str, Any]:
    zero_rows = [row for row in rows if _is_zero_strength_history_source_quality_event(row)]
    reason_counts = Counter(_blocker_reason(row) or str(row.get("stage") or "") for row in zero_rows)
    latest = zero_rows[-1] if zero_rows else {}
    return {
        "event_count": len(zero_rows),
        "repeated": len(zero_rows) >= ZERO_HISTORY_WORKORDER_MIN_EVENTS,
        "latest_at": _event_time(latest) if latest else "",
        "latest_stage": (latest.get("stage") or "") if latest else "",
        "latest_reason": _blocker_reason(latest) if latest else "",
        "top_reasons": [
            {"reason": reason, "count": count}
            for reason, count in reason_counts.most_common(5)
        ],
        "source_quality_route": (
            "source_quality_workorder_required"
            if len(zero_rows) >= ZERO_HISTORY_WORKORDER_MIN_EVENTS
            else "observe_until_repeated"
        ),
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


def _top_counter(counter: Counter[Any], *, limit: int = 10, key_name: str = "key") -> list[dict[str, Any]]:
    return [{key_name: key, "count": count} for key, count in counter.most_common(limit)]


def _real_rows(rows: list[dict[str, Any]], *, since: str | None = None) -> list[dict[str, Any]]:
    selected = []
    for row in rows:
        if since and _event_time(row) < since:
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
                "submitted_order_price": _safe_float(_field(row, "submitted_order_price")),
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
        text = " ".join([stage, *(str(key) for key in fields), *(str(value) for value in fields.values())]).lower()
        if stage in SCALE_IN_STAGES or "scale_in" in text or "avg_down" in text or "pyramid" in text:
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
    return {
        "stock_code": code,
        "stock_name": name,
        "promoted_count": len(promoted_rows),
        "first_promoted_at": _event_time(promoted_rows[0]) if promoted_rows else "",
        "promoted_in_event_window": any(row.get("stage") == PROMOTED_STAGE for row in rows),
        "last_event_at": _event_time(rows[-1]) if rows else "",
        "max_price_delta_since_first_seen_pct": _max_delta(rows),
        "latest_price_delta_since_first_seen_pct": _latest_delta(rows),
        "ai_confirmed_count": len(ai_rows),
        "latest_ai_action": _field(latest_ai, "action") if latest_ai else "",
        "latest_ai_score": _safe_float(_field(latest_ai, "ai_score")) if latest_ai else None,
        "latest_entry_score_threshold": _safe_float(_field(latest_ai, "entry_score_threshold"))
        if latest_ai
        else None,
        "real_submit_count": len(real_submit_rows),
        "blocker_count": len(blocker_rows),
        "dominant_blocker": _dominant_blocker(rows),
        "latest_blocker": _latest_blocker(rows),
        "queue_observation_counts": queue_counts,
        "low_ai_or_negative_pressure_eval_quality": _low_ai_pressure_quality_counts(rows),
        "zero_strength_history_source_quality": _zero_strength_history_source_quality(rows),
        "scanner_full_eval_budget_deferred": {
            "count": len(budget_deferred_rows),
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
                "scanner_full_eval_limit": _safe_float(_field(row, "scanner_full_eval_limit")),
                "scanner_full_eval_count": _safe_float(_field(row, "scanner_full_eval_count")),
                "scanner_rising_full_eval_extra_limit": _safe_float(
                    _field(row, "scanner_rising_full_eval_extra_limit")
                ),
                "scanner_rising_full_eval_relief_count": _safe_float(
                    _field(row, "scanner_rising_full_eval_relief_count")
                ),
            }
            for row in blocker_rows[-8:]
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
    if zero_history or stale_eval_count:
        priorities.append(
            {
                "priority": 1,
                "issue": "scanner_strength_history_or_stale_eval",
                "decision": "fix_observation_freshness_before_threshold_tuning",
                "evidence": {
                    "rising_missed_symbols": len(rising_missed),
                    "repeated_zero_strength_history_symbols": len(zero_history),
                    "stale_or_delayed_low_ai_or_pressure_events": stale_eval_count,
                    "top_symbols": [
                        {
                            "stock_code": item.get("stock_code") or "",
                            "stock_name": item.get("stock_name") or "",
                            "event_count": item.get("event_count") or 0,
                            "latest_reason": item.get("latest_reason") or "",
                        }
                        for item in zero_history[:8]
                    ],
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
    if budget_deferred_count:
        priorities.append(
            {
                "priority": 2,
                "issue": "scanner_full_eval_budget_deferred",
                "decision": "treat_as_evaluation_throughput_bottleneck_not_buy_threshold_signal",
                "evidence": {
                    "deferred_count": budget_deferred_count,
                    "symbol_count": int(scanner_budget.get("symbol_count") or 0),
                    "top_symbols": scanner_budget.get("top_symbols") or [],
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
    rising_threshold_pct: float = 0.5,
    falling_threshold_pct: float = -0.1,
) -> dict[str, Any]:
    all_rows = _read_jsonl(pipeline_path)
    full_grouped = _entry_events(all_rows)
    rows = all_rows
    if since:
        rows = [row for row in rows if _event_time(row) >= since]
    real_rows = _real_rows(all_rows, since=since)
    grouped = _entry_events(rows)
    real_entry_event_count = sum(len(events) for events in grouped.values())
    summaries = [
        _summarize_code(code, events, promotion_source_rows=full_grouped.get(code, events))
        for code, events in grouped.items()
        if any(row.get("stage") == PROMOTED_STAGE for row in full_grouped.get(code, events))
    ]
    rising_missed = [
        item
        for item in summaries
        if (item["max_price_delta_since_first_seen_pct"] or 0.0) >= rising_threshold_pct
        and item["real_submit_count"] == 0
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
    return {
        "schema_version": 1,
        "report_type": "intraday_entry_blocker_diagnostics",
        "target_date": target_date,
        "generated_at": generated_at or datetime.now().isoformat(timespec="seconds"),
        "source_pipeline_events": str(pipeline_path),
        "event_window": {
            "since": since or "",
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
            "falling_real_submitted_count": len(falling_submitted),
            "real_submit_symbol_count": sum(1 for item in summaries if item["real_submit_count"] > 0),
            "excluded_analysis_scope": "sim_and_swing_events",
            "rising_missed_low_ai_or_negative_pressure_eval_quality": _rollup_low_ai_pressure_quality(
                rising_missed
            ),
            "repeated_zero_strength_history_workorder_count": len(
                _zero_strength_history_workorders(summaries)
            ),
            "rising_missed_repeated_zero_strength_history_workorder_count": len(
                _zero_strength_history_workorders(rising_missed)
            ),
            "rising_missed_full_eval_budget_deferred_count": int(
                scanner_budget.get("deferred_count") or 0
            ),
            "rising_missed_full_eval_budget_deferred_symbol_count": int(
                scanner_budget.get("symbol_count") or 0
            ),
        },
        "source_quality_workorders": {
            "repeated_zero_strength_history": _zero_strength_history_workorders(summaries),
            "rising_missed_repeated_zero_strength_history": _zero_strength_history_workorders(
                rising_missed
            ),
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

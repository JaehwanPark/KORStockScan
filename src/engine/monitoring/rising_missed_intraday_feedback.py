from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.engine.scalping.risky_micro_episode import (
    POLICY_VERSION as RISKY_MICRO_POLICY_VERSION,
    PRIMARY_ENTRY_PROFILE as RISKY_MICRO_PRIMARY_ENTRY_PROFILE,
    TICK_CONTEXT_GAP_REASONS as RISKY_MICRO_TICK_CONTEXT_GAP_REASONS,
    evaluate_risky_micro_episode,
)
from src.utils.jsonl_io import existing_or_gzip_path, iter_jsonl

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PIPELINE_EVENTS_DIR = PROJECT_ROOT / "data" / "pipeline_events"
REPORT_DIR = PROJECT_ROOT / "data" / "report" / "rising_missed_intraday_feedback"
KST = timezone(timedelta(hours=9))
CLEAN_BASELINE_DATE = "2026-06-05"
NXT_POST_BLOCK_ROLLING_REPORT_DAYS = 20
LATENCY_FALSE_NEGATIVE_ROLLING_REPORT_DAYS = 20
FORCED_REASON = "rising_missed_one_share_entry"
AVG_DOWN_FAIL_FLOOR = 2
FORCED_SUBMIT_LINEAGE_JOIN_WINDOW_MINUTES = 15
LATENCY_FALSE_NEGATIVE_MIN_MFE_PCT = 3.0
LATENCY_FALSE_NEGATIVE_MAX_MAE_ABS_PCT = 1.5
LATENCY_FALSE_NEGATIVE_BUCKETS = {
    "latency_true_ofi_below_floor",
    "latency_true_ofi_samples_below_floor",
    "latency_spread_above_caution",
    "latency_spread_above_caution_below_guard_cap",
}
LATENCY_CANARY_MIN_REVIEW_SCORE_PCT = 2.0
LATENCY_CANARY_TRUE_OFI_MIN_SAMPLE_COUNT = 100
LATENCY_CANARY_FRESH_WS_MAX_AGE_MS = 150.0
LATENCY_CANARY_TRUE_OFI_NEAR_ZERO_FLOOR = -0.10
LATENCY_CANARY_SPREAD_ONLY_MAX_SPREAD_BPS = 90.0
LATENCY_ROLLING_MIN_LOW_ADVERSE_RATE_PCT = 30.0
LATENCY_ROLLING_MIN_READY_RATE_PCT = 30.0
EXECUTABLE_BBO_COUNTERFACTUAL_STAGES = frozenset(
    {"blocked_zero_qty", "latency_block", "rising_missed_tick_speed_entry_block"}
)
EXECUTABLE_BBO_PREDECESSOR_MAX_AGE_SEC = 1.0
EXECUTABLE_BBO_PREDECESSOR_STAGES = frozenset({"rising_missed_one_share_entry"})
RISKY_MICRO_HORIZONS_SEC = (3, 10, 20, 30)
RISKY_MICRO_MAX_ENDPOINT_LAG_SEC = 5.0
RISKY_MICRO_MAX_INTERNAL_GAP_SEC = 10.0
RISKY_MICRO_MAX_QUOTE_AGE_MS = 1_000.0
RISKY_MICRO_ROLLING_REPORT_DAYS = 20
RISKY_MICRO_ROLLING_MIN_RESOLVED_EPISODES = 30
RISKY_MICRO_ROLLING_MIN_UNIQUE_SYMBOLS = 10
RISKY_MICRO_ROLLING_MIN_TRADE_DATES = 3
RISKY_MICRO_ROLLING_MIN_FILLED_TERMINAL_EPISODES = 10
RISKY_MICRO_ENTRY_PROFILE_TTLS_SEC = (3, 5, 10)
RISKY_MICRO_LIMITED_ASK_MAX_SPREAD_BPS = 15.0
RISKY_MICRO_EXPECTED_SOURCE_CATEGORIES = (
    "scanner_candidate",
    "tp1",
    "entry_ai",
    "latency",
    "liquidity_micro",
    "tick_speed",
    "entry_price",
)
RISKY_MICRO_DERIVED_SOURCE_STAGES = {
    "rising_missed_one_share_entry_blocked": "scanner_candidate",
    "rising_missed_scout_quality_guard_blocked": "scanner_candidate",
    "rising_missed_tp1_candidate_blocked": "tp1",
    "rising_missed_tp1_candidate_deferred": "tp1",
    "pre_submit_entry_ai_authority_guard_block": "entry_ai",
    "real_weak_ai_micro_entry_block": "entry_ai",
    "blocked_liquidity": "liquidity_micro",
    "entry_price_canary_submit_block": "entry_price",
    "entry_ai_price_input_preflight_block": "entry_price",
}
TP1_GROSS_TARGET_PCT = 1.30
TP1_ADVERSE_STOP_PCT = -0.70
TP1_COST_RESERVE_PCT = 0.30
TP1_NET_TARGET_PCT = 1.00
TP1_LABEL_HORIZON_SEC = 20 * 60
TP1_DETAIL_ROW_EXPORT_LIMIT = 200
TP1_POST_BLOCK_HORIZONS_MIN = (1, 3, 5, 10, 20, 30, 60)
BACKOFF_EXECUTABLE_HORIZONS_MIN = (1, 3, 5, 10)
TP1_POST_BLOCK_MIN_FRESH_PRICE_SAMPLES = 2
FORBIDDEN_USES = [
    "runtime_threshold_mutation",
    "intraday_runtime_apply",
    "stale_submit_bypass",
    "broker_guard_bypass",
    "order_guard_relaxation",
    "scale_in_guard_bypass",
    "quantity_guard_relaxation",
    "position_cap_release",
    "provider_route_change",
    "bot_restart",
    "forced_one_share_success_counting",
    "real_execution_quality_approval",
]
TP1_LABEL_PROJECTION_FIELD_KEYS = frozenset(
    {
        "actual_fee_krw",
        "actual_tax_krw",
        "canonical_mark_price",
        "current_price",
        "current_price_observed",
        "effective_venue",
        "fee_krw",
        "first_seen_price",
        "forced_entry_qty",
        "holding_rest_quote_route_consistent",
        "holding_ws_recovered_curr",
        "latest_price",
        "market_session_bucket",
        "mark_price_at_submit",
        "market_data_effective_price_source",
        "market_data_effective_best_ask",
        "market_data_effective_best_bid",
        "market_data_freshness_state",
        "market_data_rest_age_basis",
        "market_data_rest_quote_age_ms",
        "market_data_ws_age_basis",
        "market_data_ws_quote_age_ms",
        "market_data_ws_rest_gap_bps",
        "pre_submit_ws_snapshot_refresh_latest_price",
        "pre_submit_ws_snapshot_refresh_best_ask",
        "pre_submit_ws_snapshot_refresh_best_bid",
        "best_ask_at_submit",
        "best_bid_at_submit",
        "entry_ai_price_ws_snapshot_refresh_best_ask",
        "entry_ai_price_ws_snapshot_refresh_best_bid",
        "pre_submit_rest_orderbook_refresh_best_ask",
        "pre_submit_rest_orderbook_refresh_best_bid",
        "pre_submit_quote_refresh_best_ask",
        "pre_submit_quote_refresh_best_bid",
        "executable_buy_price",
        "executable_sell_price",
        "quantity",
        "rising_missed_effective_venue",
        "rising_missed_market_session_bucket",
        "rising_missed_nxt_post_block_first_hit_move_pct",
        "rising_missed_nxt_post_block_first_hit_ts",
        "rising_missed_nxt_post_block_horizon_sec",
        "rising_missed_nxt_post_block_max_move_pct",
        "rising_missed_nxt_post_block_min_move_pct",
        "rising_missed_nxt_post_block_ws_0d_best_ask",
        "rising_missed_nxt_post_block_ws_0d_best_bid",
        "rising_missed_nxt_post_block_sampler_outcome_label",
        "rising_missed_tp1_actual_watch_delta_pct",
        "rising_missed_tp1_ai_action",
        "rising_missed_tp1_bid_imbalance_surge",
        "rising_missed_tp1_candidate_allowed",
        "rising_missed_tp1_candidate_lane",
        "rising_missed_tp1_candidate_reason",
        "rising_missed_tp1_counterfactual_submit_safety_action",
        "rising_missed_tp1_counterfactual_submit_safety_risks",
        "rising_missed_tp1_depth_imbalance_ewma",
        "rising_missed_tp1_effective_price",
        "rising_missed_tp1_effective_quote_age_ms",
        "rising_missed_tp1_evaluation_id",
        "rising_missed_tp1_micro_age_sec",
        "rising_missed_tp1_micro_confidence",
        "rising_missed_tp1_micro_source_state",
        "rising_missed_tp1_micro_vwap_fresh",
        "rising_missed_tp1_micro_vwap_gap_bps",
        "rising_missed_tp1_pressure_ewma",
        "rising_missed_tp1_selector_active",
        "rising_missed_tp1_source_family_count",
        "rising_missed_tp1_spread_ratio",
        "rising_missed_tp1_tick_acceleration",
        "rising_missed_tp1_tick_acceleration_fresh",
        "rising_missed_tp1_top_depth_ratio",
        "rising_missed_tp1_true_ofi_ewma",
        "rising_missed_tp1_true_ofi_sample_count",
        "rising_missed_tp1_ws_0b_signed_fid15_present",
        "rising_missed_tp1_ws_micro_provenance_ready",
        "selector_deferred",
        "selector_reason",
        "stock_code",
        "stock_name",
        "submitted_order_price",
        "tax_krw",
        "venue",
        "venue_resolution",
        "ws_last_0b_age_ms",
    }
)


def _safe_float(value: Any) -> float | None:
    if value in (None, "", "-"):
        return None
    try:
        return float(str(value).replace(",", "").replace("+", "").replace("%", ""))
    except ValueError:
        return None


def _safe_int(value: Any) -> int:
    numeric = _safe_float(value)
    return int(numeric) if numeric is not None else 0


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _optional_boolish(value: Any) -> bool | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in {"", "-", "none", "null", "unknown"}:
        return None
    if isinstance(value, bool):
        return value
    return text in {"1", "true", "yes", "y", "on"}


def _fields(row: dict[str, Any]) -> dict[str, Any]:
    fields = row.get("fields")
    return fields if isinstance(fields, dict) else {}


def _event_ts(row: dict[str, Any]) -> str:
    return str(row.get("emitted_at") or row.get("timestamp") or row.get("ts") or "")


def _parse_ts(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=KST)
    return parsed


def _compatible_elapsed_seconds(
    later: datetime | None,
    earlier: datetime | None,
) -> float | None:
    if later is None or earlier is None:
        return None
    if (later.tzinfo is None) != (earlier.tzinfo is None):
        return None
    return (later - earlier).total_seconds()


def _event_code(row: dict[str, Any]) -> str:
    fields = _fields(row)
    return str(
        row.get("stock_code") or fields.get("stock_code") or row.get("code") or ""
    ).strip()


def _event_name(row: dict[str, Any]) -> str:
    fields = _fields(row)
    return str(
        row.get("stock_name") or fields.get("stock_name") or _event_code(row) or ""
    ).strip()


def _scanner_current_price_usable(row: dict[str, Any], fields: dict[str, Any]) -> bool:
    stage = str(row.get("stage") or "")
    if not stage.startswith("scalping_scanner_"):
        return True
    ws_trade_age_ms = _safe_float(fields.get("ws_last_0b_age_ms"))
    return bool(ws_trade_age_ms is not None and ws_trade_age_ms <= 3000.0)


def _event_price_with_source(row: dict[str, Any]) -> tuple[float | None, str]:
    fields = _fields(row)
    for key in (
        "pre_submit_ws_snapshot_refresh_latest_price",
        "mark_price_at_submit",
        "canonical_mark_price",
        "latest_price",
        "current_price",
        "current_price_observed",
        "holding_ws_recovered_curr",
        "rising_missed_one_share_entry_price",
        "submitted_order_price",
        "rising_missed_tp1_effective_price",
        "first_seen_price",
    ):
        price = _safe_float(fields.get(key))
        if price is not None and price > 0:
            return price, key
    return None, "missing"


def _event_price(row: dict[str, Any]) -> float | None:
    return _event_price_with_source(row)[0]


def _event_executable_bbo(
    row: dict[str, Any],
) -> tuple[float | None, float | None, str]:
    """Return a validated executable top of book without mark-price fallback."""

    fields = _fields(row)
    candidates = (
        (
            "market_data_effective_bbo",
            "market_data_effective_best_bid",
            "market_data_effective_best_ask",
        ),
        ("submit_bbo", "best_bid_at_submit", "best_ask_at_submit"),
        (
            "pre_submit_ws_snapshot_refresh_bbo",
            "pre_submit_ws_snapshot_refresh_best_bid",
            "pre_submit_ws_snapshot_refresh_best_ask",
        ),
        (
            "entry_ai_price_ws_snapshot_refresh_bbo",
            "entry_ai_price_ws_snapshot_refresh_best_bid",
            "entry_ai_price_ws_snapshot_refresh_best_ask",
        ),
        (
            "pre_submit_rest_orderbook_refresh_bbo",
            "pre_submit_rest_orderbook_refresh_best_bid",
            "pre_submit_rest_orderbook_refresh_best_ask",
        ),
        (
            "pre_submit_quote_refresh_bbo",
            "pre_submit_quote_refresh_best_bid",
            "pre_submit_quote_refresh_best_ask",
        ),
        (
            "explicit_executable_prices",
            "executable_sell_price",
            "executable_buy_price",
        ),
        (
            "nxt_post_block_ws_0d_bbo",
            "rising_missed_nxt_post_block_ws_0d_best_bid",
            "rising_missed_nxt_post_block_ws_0d_best_ask",
        ),
    )
    for source, bid_key, ask_key in candidates:
        bid = _safe_float(fields.get(bid_key))
        ask = _safe_float(fields.get(ask_key))
        if bid is not None and ask is not None and bid > 0 and ask >= bid:
            return bid, ask, source
    return None, None, "missing_or_invalid_executable_bbo"


def _decision_stage_current_price_unusable(row: dict[str, Any], source: str) -> bool:
    return bool(
        source in {"current_price", "current_price_observed"}
        and str(row.get("stage") or "")
        in {"budget_pass", "orderbook_stability_observed"}
    )


def _tp1_observation_price(row: dict[str, Any]) -> tuple[float | None, str]:
    fields = _fields(row)
    stage = str(row.get("stage") or "")
    if stage == "holding_rest_quote_divergence_blocked":
        # The holding runtime explicitly rejected this REST value because it
        # conflicted with a recent WS quote. It is diagnostic provenance, not
        # an executable/observable market price for TP1 MFE/MAE labels.
        return None, "rejected_rest_quote_divergence"
    if stage == "holding_rest_quote_venue_blocked":
        return None, "rejected_rest_quote_venue"
    if stage == "holding_ws_freshness_recovered" and not _boolish(
        fields.get("holding_rest_quote_route_consistent")
    ):
        # Historical recovery rows without an exact venue-qualified REST
        # request cannot support tuning labels.
        return None, "rest_quote_recovery_venue_unproven"
    is_tp1_evaluation = stage in {
        "rising_missed_one_share_entry",
        "rising_missed_normal_buy_bridge_unlocked",
        "rising_missed_tp1_candidate_blocked",
        "rising_missed_tp1_candidate_deferred",
        "rising_missed_tp1_counterfactual_submit_safety",
    }
    if is_tp1_evaluation:
        effective_price = _safe_float(fields.get("rising_missed_tp1_effective_price"))
        if effective_price is not None and effective_price > 0:
            return effective_price, "rising_missed_tp1_effective_price"
    price, source = _event_price_with_source(row)
    if _decision_stage_current_price_unusable(row, source):
        return None, "decision_stage_current_price_without_fresh_mark"
    if source in {
        "current_price",
        "current_price_observed",
    } and not _scanner_current_price_usable(row, fields):
        return None, "scanner_current_price_time_basis_unknown"
    return price, source


def _event_delta_pct(row: dict[str, Any]) -> float | None:
    fields = _fields(row)
    return _safe_float(
        fields.get("price_delta_since_first_seen_pct")
        or fields.get("scanner_rising_missed_price_delta_since_first_seen_pct")
        or fields.get("rising_missed_one_share_entry_positive_delta_pct")
    )


def _pipeline_path(target_date: str) -> Path:
    return PIPELINE_EVENTS_DIR / f"pipeline_events_{target_date}.jsonl"


def _default_output_paths(target_date: str) -> tuple[Path, Path]:
    return (
        REPORT_DIR / f"rising_missed_intraday_feedback_{target_date}.json",
        REPORT_DIR / f"rising_missed_intraday_feedback_{target_date}.md",
    )


def _is_forced_rising_missed(row: dict[str, Any]) -> bool:
    fields = _fields(row)
    return (
        row.get("stage") == "rising_missed_one_share_entry"
        or str(fields.get("forced_entry_reason") or "") == FORCED_REASON
        or _boolish(fields.get("rising_missed_one_share_entry_forced"))
    )


def _forced_entry_record(row: dict[str, Any]) -> dict[str, Any]:
    fields = _fields(row)
    return {
        "record_id": str(row.get("record_id") or "").strip(),
        "stock_code": row.get("stock_code"),
        "stock_name": row.get("stock_name"),
        "first_rising_ts": row.get("emitted_at"),
        "source_signature": fields.get("source_signature"),
        "scanner_promotion_reason": fields.get("scanner_promotion_reason"),
        "rising_missed_class": fields.get("rising_missed_class"),
        "rising_missed_class_reason": fields.get("rising_missed_class_reason"),
        "price_delta_since_first_seen_pct": _safe_float(
            fields.get("price_delta_since_first_seen_pct")
            or fields.get("rising_missed_one_share_entry_positive_delta_pct")
        ),
    }


def _quality_label(item: dict[str, Any]) -> str:
    latest_profit = item.get("latest_profit_rate")
    max_profit = item.get("max_profit_seen")
    min_profit = item.get("min_profit_seen")
    exit_rule = str(item.get("exit_rule_candidate") or "")
    sell_reason = str(item.get("sell_reason_type") or "").upper()
    if sell_reason == "LOSS" or "stop" in exit_rule:
        return "rising_missed_initial_quality_fail"
    if latest_profit is not None and latest_profit < 0:
        return "rising_missed_initial_quality_fail_open"
    if (
        min_profit is not None
        and min_profit <= -2.0
        and (max_profit is None or max_profit < 0.5)
    ):
        return "rising_missed_initial_quality_fail_open"
    if (
        max_profit is not None
        and max_profit >= 1.0
        and (latest_profit is not None and latest_profit >= 0)
    ):
        return "rising_missed_scale_in_rescue_warning"
    return "rising_missed_initial_quality_review"


def _update_holding_record(item: dict[str, Any], row: dict[str, Any]) -> None:
    fields = _fields(row)
    profit_rate = _safe_float(fields.get("profit_rate"))
    peak_profit = _safe_float(fields.get("peak_profit"))
    avg_down_count = _safe_int(fields.get("avg_down_count"))
    item["latest_stage"] = row.get("stage")
    item["latest_snapshot_ts"] = row.get("emitted_at")
    item["latest_profit_rate"] = profit_rate
    item["latest_peak_profit"] = peak_profit
    item["latest_buy_qty"] = _safe_int(fields.get("buy_qty"))
    item["latest_reason"] = fields.get("reason") or fields.get("scale_in_action_reason")
    item["latest_gate_reason"] = (
        fields.get("scale_in_gate_reason")
        or fields.get("scale_in_blocker_reason")
        or fields.get("gate_reason")
    )
    item["exit_rule_candidate"] = fields.get("exit_rule_candidate") or fields.get(
        "exit_rule"
    )
    item["sell_reason_type"] = fields.get("sell_reason_type")
    item["max_avg_down_count"] = max(
        _safe_int(item.get("max_avg_down_count")), avg_down_count
    )
    if avg_down_count >= AVG_DOWN_FAIL_FLOOR:
        item["avg_down_ge2_seen"] = True
        item["first_avg_down_ge2_ts"] = item.get("first_avg_down_ge2_ts") or row.get(
            "emitted_at"
        )
    if profit_rate is not None:
        item["min_profit_seen"] = (
            profit_rate
            if item.get("min_profit_seen") is None
            else min(float(item["min_profit_seen"]), profit_rate)
        )
        item["max_profit_seen"] = (
            profit_rate
            if item.get("max_profit_seen") is None
            else max(float(item["max_profit_seen"]), profit_rate)
        )


def _regression_label(item: dict[str, Any]) -> str:
    final_profit = item.get("final_profit_rate")
    if final_profit is None:
        return "first_touch_open_unresolved"
    if final_profit > 0:
        return "first_touch_recovered_profit"
    return "first_touch_loss_or_flat"


def _first_touch_shadow_decision(item: dict[str, Any]) -> dict[str, Any]:
    submitted_count = _safe_int(item.get("avg_down_submitted_event_count"))
    touch_ai = _safe_float(item.get("first_touch_ai_score"))
    touch_peak = _safe_float(item.get("first_touch_peak_profit"))
    blocker_counts = item.get("blocker_counts_before_first_touch")
    blocker_counts = blocker_counts if isinstance(blocker_counts, dict) else {}
    repeated_blocker_count = sum(_safe_int(value) for value in blocker_counts.values())
    support_signals: list[str] = []
    risk_signals: list[str] = []
    if touch_peak is not None and touch_peak >= 0.30:
        support_signals.append("prior_peak_recovery_ge_0_30")
    if touch_ai is not None and touch_ai >= 70.0:
        support_signals.append("ai_score_ge_70")
    if repeated_blocker_count >= 8:
        risk_signals.append("repeated_pre_touch_blockers_ge_8")
    if touch_ai is not None and touch_ai < 60.0:
        risk_signals.append("ai_score_lt_60")
    if submitted_count > 1:
        risk_signals.append("cap1_extra_avg_down_would_block")
    cap1_decision = "cap1_not_applicable_no_submit"
    if submitted_count == 1:
        cap1_decision = "cap1_first_avg_down_allowed"
    elif submitted_count > 1:
        cap1_decision = "cap1_extra_avg_down_would_block"
    return {
        "first_touch_shadow_decision_authority": "source_only_no_runtime_effect",
        "first_touch_shadow_cap1_decision": cap1_decision,
        "first_touch_shadow_support_signals": support_signals,
        "first_touch_shadow_risk_signals": risk_signals,
        "first_touch_shadow_repeated_blocker_count": repeated_blocker_count,
    }


def _touch_reason(fields: dict[str, Any]) -> str | None:
    return (
        fields.get("gate_reason")
        or fields.get("block_reason")
        or fields.get("reason")
        or fields.get("scale_in_gate_reason")
        or fields.get("scale_in_blocker_reason")
    )


def _touch_feature(row: dict[str, Any]) -> dict[str, Any]:
    fields = _fields(row)
    return {
        "first_touch_ts": row.get("emitted_at"),
        "first_touch_stage": row.get("stage"),
        "first_touch_profit_rate": _safe_float(fields.get("profit_rate")),
        "first_touch_peak_profit": _safe_float(fields.get("peak_profit")),
        "first_touch_ai_score": _safe_float(
            fields.get("current_ai_score") or fields.get("ai_score")
        ),
        "first_touch_gate_reason": _touch_reason(fields),
        "first_touch_avgdown_decision_allowed": fields.get(
            "first_touch_avgdown_decision_allowed"
        ),
        "first_touch_avgdown_decision_reason": fields.get(
            "first_touch_avgdown_decision_reason"
        ),
        "first_touch_avgdown_support_signals": fields.get(
            "first_touch_avgdown_support_signals"
        ),
        "first_touch_avgdown_risk_signals": fields.get(
            "first_touch_avgdown_risk_signals"
        ),
        "first_touch_avgdown_repeated_blocker_count": _safe_int(
            fields.get("first_touch_avgdown_repeated_blocker_count")
        ),
        "first_touch_avgdown_decision_authority": fields.get(
            "first_touch_avgdown_decision_authority"
        ),
        "first_touch_avgdown_ai_score_usable": _optional_boolish(
            fields.get("first_touch_avgdown_ai_score_usable")
        ),
        "first_touch_avgdown_ai_score_source": fields.get(
            "first_touch_avgdown_ai_score_source"
        ),
        "first_touch_avgdown_ai_score_data_quality": fields.get(
            "first_touch_avgdown_ai_score_data_quality"
        ),
        "first_touch_avgdown_ai_score_excluded_reason": fields.get(
            "first_touch_avgdown_ai_score_excluded_reason"
        ),
        "first_touch_reversal_feature_source_quality": fields.get(
            "first_touch_reversal_feature_source_quality"
        ),
        "first_touch_reversal_feature_stale": _optional_boolish(
            fields.get("first_touch_reversal_feature_stale")
        ),
        "first_touch_reversal_feature_stale_reason": fields.get(
            "first_touch_reversal_feature_stale_reason"
        ),
        "first_touch_tick_context_quality": fields.get(
            "first_touch_tick_context_quality"
        ),
        "first_touch_tick_latest_age_ms": fields.get("first_touch_tick_latest_age_ms"),
        "first_touch_quote_stale": fields.get("first_touch_quote_stale"),
        "first_touch_quote_age_ms": fields.get("first_touch_quote_age_ms"),
        "buy_pressure_10t": _safe_float(fields.get("buy_pressure_10t")),
        "tick_aggressor_trusted_count": _safe_float(
            fields.get("tick_aggressor_trusted_count")
        ),
        "tick_aggressor_pressure_usable": _optional_boolish(
            fields.get("tick_aggressor_pressure_usable")
        ),
        "tick_acceleration_ratio": _safe_float(fields.get("tick_acceleration_ratio")),
        "curr_vs_micro_vwap_bp": _safe_float(fields.get("curr_vs_micro_vwap_bp")),
        "micro_vwap_available": _optional_boolish(fields.get("micro_vwap_available")),
        "minute_candle_context_quality": fields.get("minute_candle_context_quality"),
        "minute_candle_window_fresh": _optional_boolish(
            fields.get("minute_candle_window_fresh")
        ),
        "minute_candle_latest_age_ms": fields.get("minute_candle_latest_age_ms"),
    }


def _update_first_touch_regression(
    item: dict[str, Any],
    row: dict[str, Any],
    blocker_counts: Counter[str],
    blocker_reason_counts: Counter[str],
) -> None:
    fields = _fields(row)
    stage = str(row.get("stage") or "")
    is_first_touch_stage = (
        "stop_line_touch_mandatory_avg_down" in stage
        or stage == "stop_line_touch_first_touch_avgdown_decision_blocked"
    )
    if is_first_touch_stage and not item.get("first_touch_seen"):
        item["first_touch_seen"] = True
        item.update(_touch_feature(row))
        item["blocker_counts_before_first_touch"] = dict(blocker_counts)
        item["blocker_reason_counts_before_first_touch"] = dict(blocker_reason_counts)
    if stage == "stop_line_touch_first_touch_avgdown_decision_blocked":
        item["first_touch_avgdown_decision_blocked"] = True
    if "stop_line_touch_mandatory_avg_down_submitted" in stage:
        item["first_touch_avg_down_submitted"] = True
        item["first_touch_submitted_ts"] = item.get(
            "first_touch_submitted_ts"
        ) or row.get("emitted_at")
        item["avg_down_submitted_event_count"] = (
            _safe_int(item.get("avg_down_submitted_event_count")) + 1
        )
    if "stop_line_touch_mandatory_avg_down_not_eligible" in stage:
        item["first_touch_not_eligible_seen"] = True
        item["first_touch_not_eligible_reason"] = item.get(
            "first_touch_not_eligible_reason"
        ) or _touch_reason(fields)
    if stage.startswith("blocked_") and not item.get("first_touch_seen"):
        blocker_counts[stage] += 1
        reason = _touch_reason(fields)
        if reason:
            blocker_reason_counts[str(reason)] += 1
    if stage == "sell_completed":
        profit_rate = _safe_float(fields.get("profit_rate"))
        if profit_rate is not None:
            item["final_profit_rate"] = profit_rate
            item["final_stage"] = stage
            item["final_ts"] = row.get("emitted_at")
    avg_down_count = _safe_int(fields.get("avg_down_count"))
    if avg_down_count:
        item["max_avg_down_count"] = max(
            _safe_int(item.get("max_avg_down_count")), avg_down_count
        )


def _build_first_touch_regression_rows(
    forced: dict[str, dict[str, Any]],
    pipeline_path: Path,
) -> list[dict[str, Any]]:
    candidates: dict[str, dict[str, Any]] = {
        record_id: {
            **entry,
            "record_id": record_id,
            "first_touch_seen": False,
            "first_touch_avg_down_submitted": False,
            "first_touch_not_eligible_seen": False,
            "max_avg_down_count": 0,
            "avg_down_submitted_event_count": 0,
        }
        for record_id, entry in forced.items()
    }
    blocker_counts: dict[str, Counter[str]] = {
        record_id: Counter() for record_id in candidates
    }
    blocker_reason_counts: dict[str, Counter[str]] = {
        record_id: Counter() for record_id in candidates
    }
    for row in iter_jsonl(pipeline_path):
        record_id = str(row.get("record_id") or "").strip()
        if record_id not in candidates:
            continue
        fields = _fields(row)
        stage = str(row.get("stage") or "")
        if stage == "order_bundle_submitted" and _boolish(
            fields.get("actual_order_submitted")
        ):
            candidates[record_id]["entry_order_submitted"] = True
            candidates[record_id]["entry_order_submitted_count"] = (
                _safe_int(candidates[record_id].get("entry_order_submitted_count")) + 1
            )
            candidates[record_id]["entry_order_last_submitted_ts"] = row.get(
                "emitted_at"
            )
        if stage == "holding_started" and _boolish(
            fields.get("actual_order_submitted")
        ):
            candidates[record_id]["entry_fill_seen"] = True
            candidates[record_id]["entry_fill_seen_count"] = (
                _safe_int(candidates[record_id].get("entry_fill_seen_count")) + 1
            )
            candidates[record_id]["entry_fill_last_seen_ts"] = row.get("emitted_at")
        _update_first_touch_regression(
            candidates[record_id],
            row,
            blocker_counts[record_id],
            blocker_reason_counts[record_id],
        )
    rows: list[dict[str, Any]] = []
    for item in candidates.values():
        if not item.get("first_touch_seen"):
            continue
        item["first_touch_regression_label"] = _regression_label(item)
        item.update(_first_touch_shadow_decision(item))
        item["decision_authority"] = "source_only_first_touch_regression_table"
        item["entry_order_submitted"] = bool(item.get("entry_order_submitted"))
        item["entry_order_submitted_count"] = _safe_int(
            item.get("entry_order_submitted_count")
        )
        item["entry_fill_seen"] = bool(item.get("entry_fill_seen"))
        item["entry_fill_seen_count"] = _safe_int(item.get("entry_fill_seen_count"))
        item["actual_order_submitted"] = False
        item["broker_order_forbidden"] = True
        item["runtime_effect"] = False
        item["allowed_runtime_apply"] = False
        item["forbidden_uses"] = FORBIDDEN_USES
        rows.append(item)
    rows.sort(
        key=lambda item: (
            str(item.get("first_touch_ts") or ""),
            str(item.get("record_id") or ""),
        )
    )
    return rows


def _forced_submit_join_key(
    row: dict[str, Any],
    candidates: dict[str, dict[str, Any]],
    by_code: dict[str, list[dict[str, Any]]],
) -> str | None:
    record_id = str(row.get("record_id") or "").strip()
    if record_id in candidates:
        return record_id
    code = _event_code(row)
    event_dt = _parse_ts(_event_ts(row))
    if not code or event_dt is None:
        return None
    best: tuple[datetime, str] | None = None
    for candidate in by_code.get(code, []):
        candidate_dt = _parse_ts(candidate.get("first_rising_ts"))
        if candidate_dt is None or candidate_dt > event_dt:
            continue
        if event_dt - candidate_dt > timedelta(
            minutes=FORCED_SUBMIT_LINEAGE_JOIN_WINDOW_MINUTES
        ):
            continue
        candidate_record_id = str(candidate.get("record_id") or "").strip()
        if not candidate_record_id:
            continue
        if best is None or candidate_dt > best[0]:
            best = (candidate_dt, candidate_record_id)
    return best[1] if best else None


def _build_forced_submit_lineage_rows(
    forced: dict[str, dict[str, Any]],
    pipeline_path: Path,
) -> list[dict[str, Any]]:
    candidates: dict[str, dict[str, Any]] = {
        record_id: {
            **entry,
            "record_id": record_id,
            "order_plan_forced_seen": False,
            "order_plan_forced_count": 0,
            "order_leg_request_count": 0,
            "order_leg_sent_count": 0,
            "order_bundle_submitted_count": 0,
            "buy_signal_telegram_enqueued_count": 0,
            "entry_reprice_after_submit_evaluated_count": 0,
            "entry_reprice_after_submit_blocked_count": 0,
            "entry_order_cancel_requested_count": 0,
            "entry_order_cancel_confirmed_count": 0,
            "order_no_list": [],
            "submitted_price_list": [],
            "submit_lineage_join_method": "record_id",
        }
        for record_id, entry in forced.items()
    }
    by_code: dict[str, list[dict[str, Any]]] = {}
    for item in candidates.values():
        code = str(item.get("stock_code") or "").strip()
        if code:
            by_code.setdefault(code, []).append(item)
    for rows in by_code.values():
        rows.sort(key=lambda item: str(item.get("first_rising_ts") or ""))

    lineage_stages = {
        "rising_missed_one_share_entry_order_plan_forced",
        "order_leg_request",
        "order_leg_sent",
        "buy_signal_telegram_enqueued",
        "order_bundle_submitted",
        "entry_reprice_after_submit_evaluated",
        "entry_reprice_after_submit_blocked",
        "entry_order_cancel_requested",
        "entry_order_cancel_confirmed",
    }
    for row in iter_jsonl(pipeline_path):
        stage = str(row.get("stage") or "")
        if stage not in lineage_stages:
            continue
        join_key = _forced_submit_join_key(row, candidates, by_code)
        if not join_key or join_key not in candidates:
            continue
        item = candidates[join_key]
        if str(row.get("record_id") or "").strip() != join_key:
            item["submit_lineage_join_method"] = "code_time_window"
        fields = _fields(row)
        ts = _event_ts(row)
        if stage == "rising_missed_one_share_entry_order_plan_forced":
            item["order_plan_forced_seen"] = True
            item["order_plan_forced_count"] += 1
            item["order_plan_first_ts"] = item.get("order_plan_first_ts") or ts
            item["order_plan_last_ts"] = ts
            planned_price = fields.get("planned_order_price")
            if planned_price not in (None, ""):
                item["planned_order_price"] = planned_price
            forced_qty = fields.get("forced_entry_qty")
            if forced_qty not in (None, ""):
                item["forced_entry_qty"] = forced_qty
        elif stage == "order_leg_request":
            item["order_leg_request_count"] += 1
            item["order_leg_request_last_ts"] = ts
            price = (
                fields.get("submitted_order_price")
                or fields.get("order_price")
                or fields.get("price")
            )
            if price not in (None, ""):
                item["submitted_price_list"].append(str(price))
        elif stage == "order_leg_sent":
            item["order_leg_sent_count"] += 1
            item["order_leg_sent_last_ts"] = ts
            order_no = (
                fields.get("order_no")
                or fields.get("ord_no")
                or fields.get("broker_order_no")
            )
            if order_no not in (None, ""):
                item["order_no_list"].append(str(order_no))
        elif stage == "buy_signal_telegram_enqueued":
            item["buy_signal_telegram_enqueued_count"] += 1
            item["buy_signal_telegram_enqueued_last_ts"] = ts
        elif stage == "order_bundle_submitted" and _boolish(
            fields.get("actual_order_submitted")
        ):
            item["entry_order_submitted"] = True
            item["order_bundle_submitted_count"] += 1
            item["order_bundle_submitted_last_ts"] = ts
            item["entry_order_last_submitted_ts"] = ts
            order_no = (
                fields.get("order_no")
                or fields.get("ord_no")
                or fields.get("broker_order_no")
            )
            if order_no not in (None, ""):
                item["primary_order_no"] = str(order_no)
            order_price = fields.get("order_price") or fields.get(
                "submitted_order_price"
            )
            if order_price not in (None, ""):
                item["submitted_order_price"] = order_price
        elif stage == "entry_reprice_after_submit_evaluated":
            item["entry_reprice_after_submit_evaluated_count"] += 1
            item["entry_reprice_after_submit_last_reason"] = fields.get(
                "block_reason"
            ) or fields.get("reason")
            item["entry_reprice_after_submit_last_ts"] = ts
        elif stage == "entry_reprice_after_submit_blocked":
            item["entry_reprice_after_submit_blocked_count"] += 1
            item["entry_reprice_after_submit_last_reason"] = fields.get(
                "block_reason"
            ) or fields.get("reason")
            item["entry_reprice_after_submit_blocked_last_ts"] = ts
        elif stage == "entry_order_cancel_requested":
            item["entry_order_cancel_requested_count"] += 1
            item["entry_order_cancel_requested_last_ts"] = ts
        elif stage == "entry_order_cancel_confirmed":
            item["entry_order_cancel_confirmed_count"] += 1
            item["entry_order_cancel_confirmed_last_ts"] = ts

    rows: list[dict[str, Any]] = []
    for item in candidates.values():
        if not (
            item.get("order_plan_forced_seen")
            or item.get("order_leg_request_count")
            or item.get("order_leg_sent_count")
            or item.get("order_bundle_submitted_count")
        ):
            continue
        item["entry_order_submitted"] = bool(item.get("entry_order_submitted"))
        item["order_no_list"] = ",".join(dict.fromkeys(item.get("order_no_list") or []))
        item["submitted_price_list"] = ",".join(
            dict.fromkeys(item.get("submitted_price_list") or [])
        )
        item["actual_order_submitted"] = False
        item["broker_order_forbidden"] = True
        item["runtime_effect"] = False
        item["allowed_runtime_apply"] = False
        item["decision_authority"] = "source_only_rising_missed_submit_lineage"
        item["forbidden_uses"] = FORBIDDEN_USES
        rows.append(item)
    rows.sort(
        key=lambda item: (
            str(
                item.get("order_plan_first_ts")
                or item.get("order_bundle_submitted_last_ts")
                or ""
            ),
            str(item.get("record_id") or ""),
        )
    )
    return rows


def _first_touch_ai_provenance_missing(item: dict[str, Any]) -> bool:
    # A mandatory-avg-down attempt can be rejected by the deterministic
    # eligibility gate before the avg-down AI decision is evaluated.  The
    # generic current_ai_score logged on that row is position context, not
    # evidence that avg-down AI provenance was expected.
    if item.get("first_touch_not_eligible_seen"):
        return False
    if (
        item.get("first_touch_avgdown_ai_score") is None
        and item.get("first_touch_ai_score") is None
    ):
        return False
    return (
        item.get("first_touch_avgdown_ai_score_usable") is None
        or item.get("first_touch_avgdown_ai_score_source") in (None, "", "-")
        or item.get("first_touch_avgdown_ai_score_data_quality") in (None, "", "-")
    )


def _first_touch_ai_provenance_unusable(item: dict[str, Any]) -> bool:
    usable = item.get("first_touch_avgdown_ai_score_usable")
    data_quality = (
        str(item.get("first_touch_avgdown_ai_score_data_quality") or "").strip().lower()
    )
    source = str(item.get("first_touch_avgdown_ai_score_source") or "").strip().lower()
    if usable is False:
        return True
    if data_quality and data_quality not in {"fresh", "partial"}:
        return True
    return source in {
        "fallback_score_50",
        "engine_disabled",
        "lock_contention",
        "timeout",
        "unknown",
    }


def _first_touch_micro_signals(item: dict[str, Any]) -> set[str]:
    text = "|".join(
        str(item.get(key) or "")
        for key in (
            "first_touch_avgdown_support_signals",
            "first_touch_avgdown_risk_signals",
        )
    )
    return {token for token in text.split("|") if token}


def _first_touch_pressure_signal_used(item: dict[str, Any]) -> bool:
    return bool(
        _first_touch_micro_signals(item)
        & {"buy_pressure_support", "tick_accel_support"}
    )


def _first_touch_micro_vwap_signal_used(item: dict[str, Any]) -> bool:
    return bool(
        _first_touch_micro_signals(item)
        & {"micro_vwap_non_negative", "micro_vwap_negative"}
    )


def _first_touch_pressure_provenance_missing(item: dict[str, Any]) -> bool:
    if not _first_touch_pressure_signal_used(item):
        return False
    return (
        item.get("tick_aggressor_trusted_count") is None
        and item.get("tick_aggressor_pressure_usable") is None
    )


def _first_touch_pressure_provenance_unusable(item: dict[str, Any]) -> bool:
    if not _first_touch_pressure_signal_used(item):
        return False
    trusted_count = _safe_float(item.get("tick_aggressor_trusted_count")) or 0.0
    return item.get("tick_aggressor_pressure_usable") is False and trusted_count <= 0.0


def _first_touch_micro_provenance_missing(item: dict[str, Any]) -> bool:
    signals = _first_touch_micro_signals(item)
    micro_signal_used = bool(
        signals
        & {
            "buy_pressure_support",
            "tick_accel_support",
            "micro_vwap_non_negative",
            "micro_vwap_negative",
            "micro_context_stale_ignored",
        }
    )
    if not micro_signal_used:
        return False
    quality = (
        str(item.get("first_touch_reversal_feature_source_quality") or "")
        .strip()
        .lower()
    )
    if quality in {"", "-", "missing", "unknown"}:
        return True
    if _first_touch_micro_vwap_signal_used(item):
        return (
            item.get("micro_vwap_available") is None
            or item.get("minute_candle_window_fresh") is None
            or item.get("minute_candle_context_quality") in (None, "", "-")
            or item.get("minute_candle_latest_age_ms") in (None, "", "-")
        )
    return False


def _first_touch_micro_provenance_unusable(item: dict[str, Any]) -> bool:
    signals = _first_touch_micro_signals(item)
    micro_signal_used = bool(
        signals
        & {
            "buy_pressure_support",
            "tick_accel_support",
            "micro_vwap_non_negative",
            "micro_vwap_negative",
            "micro_context_stale_ignored",
        }
    )
    if not micro_signal_used:
        return False
    quality = (
        str(item.get("first_touch_reversal_feature_source_quality") or "")
        .strip()
        .lower()
    )
    stale = item.get("first_touch_reversal_feature_stale")
    reason = (
        str(item.get("first_touch_reversal_feature_stale_reason") or "").strip().lower()
    )
    if (
        quality not in {"", "-", "usable"}
        or stale is True
        or bool(reason and reason != "-")
    ):
        return True
    if _first_touch_micro_vwap_signal_used(item):
        return (
            item.get("micro_vwap_available") is False
            or item.get("minute_candle_window_fresh") is False
        )
    return False


def _count_first_touch_source_quality(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "first_touch_ai_provenance_missing_count": sum(
            1 for item in rows if _first_touch_ai_provenance_missing(item)
        ),
        "first_touch_ai_provenance_unusable_count": sum(
            1 for item in rows if _first_touch_ai_provenance_unusable(item)
        ),
        "first_touch_pressure_provenance_missing_count": sum(
            1 for item in rows if _first_touch_pressure_provenance_missing(item)
        ),
        "first_touch_pressure_provenance_unusable_count": sum(
            1 for item in rows if _first_touch_pressure_provenance_unusable(item)
        ),
        "first_touch_micro_provenance_missing_count": sum(
            1 for item in rows if _first_touch_micro_provenance_missing(item)
        ),
        "first_touch_micro_provenance_unusable_count": sum(
            1 for item in rows if _first_touch_micro_provenance_unusable(item)
        ),
    }


def _field_reason(fields: dict[str, Any]) -> str:
    return str(
        fields.get("block_reason")
        or fields.get("reason")
        or fields.get("latency_spread_relief_micro_estimator_reason")
        or fields.get("rising_missed_submit_safety_backoff_reason")
        or fields.get("scanner_ws_stale_backoff_reason")
        or ""
    ).strip()


def _quote_age_ms(fields: dict[str, Any]) -> float | None:
    for key in (
        "rising_missed_scout_quality_guard_quote_age_ms",
        "quote_consistency_ws_age_ms",
        "quote_age_ms",
        "entry_ai_price_ws_snapshot_refresh_age_ms",
        "orderbook_micro_observer_last_quote_age_ms",
        "pre_submit_quote_refresh_age_ms",
    ):
        value = _safe_float(fields.get(key))
        if value is not None:
            return value
    return None


def _classify_stale_quote_block(fields: dict[str, Any]) -> tuple[str, list[str]]:
    components: list[str] = []
    quote_age = _quote_age_ms(fields)
    max_quote_age = (
        _safe_float(fields.get("rising_missed_scout_quality_guard_max_quote_age_ms"))
        or 3000.0
    )
    quote_stale = _boolish(
        fields.get("rising_missed_scout_quality_guard_quote_stale")
    ) or (quote_age is not None and quote_age > max_quote_age)
    if quote_stale:
        components.append("quote_age_stale")

    rest_applied = _boolish(fields.get("pre_submit_rest_orderbook_refresh_applied"))
    rest_success = _boolish(fields.get("rising_missed_rest_quote_ai_recheck_success"))
    if rest_applied:
        components.append("rest_orderbook_fresh")
    elif str(fields.get("pre_submit_rest_orderbook_refresh_enabled") or "").strip():
        components.append("rest_orderbook_unavailable")
    if _boolish(fields.get("rising_missed_rest_quote_ai_recheck_attempted")):
        components.append("ai_recheck_attempted")
    if rest_success:
        components.append("ai_recheck_success")

    ai_action = (
        str(
            fields.get("rising_missed_scout_quality_guard_ai_action")
            or fields.get("rising_missed_rest_quote_ai_recheck_ai_action")
            or fields.get("rising_missed_entry_ai_action")
            or ""
        )
        .strip()
        .upper()
    )
    if ai_action in {"WAIT", "DROP"}:
        components.append(f"ai_{ai_action.lower()}")
    elif _boolish(fields.get("rising_missed_scout_quality_guard_weak_ai")):
        components.append("weak_ai_score")

    if _boolish(fields.get("rising_missed_scout_quality_guard_weak_strength")):
        components.append("weak_strength")
    if _boolish(
        fields.get("rising_missed_scout_quality_guard_recent_weak_ai_micro_block")
    ):
        components.append("recent_weak_ai_micro")
    if _boolish(fields.get("rising_missed_scout_quality_guard_weak_evidence")):
        components.append("weak_evidence")
    if _boolish(fields.get("rising_missed_scout_quality_guard_ai_provenance_missing")):
        components.append("ai_provenance_missing")
    if _boolish(
        fields.get(
            "rising_missed_scout_quality_guard_ai_score_defaulted_without_action"
        )
    ):
        components.append("ai_score_defaulted_without_action")

    micro_reason = str(
        fields.get("latency_spread_relief_micro_estimator_reason") or ""
    ).strip()
    if micro_reason:
        components.append(f"true_ofi_{micro_reason}")

    if "rest_orderbook_unavailable" in components:
        return "rest_or_quote_unavailable", components
    if "ai_drop" in components:
        return "ai_drop_after_refresh", components
    if "ai_wait" in components:
        return "ai_wait_after_refresh", components
    if any(item.startswith("true_ofi_true_ofi_below_floor") for item in components):
        return "true_ofi_below_floor", components
    if "ai_provenance_missing" in components:
        return "missing_ai_or_fresh_input", components
    if "weak_ai_score" in components:
        return "weak_ai_score", components
    if quote_stale and not any(
        item.startswith("ai_") or item.startswith("weak_") for item in components
    ):
        return "quote_age_only", components
    return "stale_quote_with_weak_evidence", components


def _classify_submit_safety_block(row: dict[str, Any]) -> tuple[str, str, list[str]]:
    fields = _fields(row)
    stage = str(row.get("stage") or "")
    reason = _field_reason(fields)
    if stage == "blocked_zero_qty":
        binding_caps = _split_csv_values(fields.get("binding_caps"))
        components = binding_caps or ["quantity_zero_without_binding_cap"]
        primary_cap = binding_caps[0] if binding_caps else "unspecified"
        return (
            primary_cap,
            f"quantity_{primary_cap}",
            components,
        )
    if stage == "rising_missed_scout_quality_guard_blocked" and reason in {
        "stale_quote_with_weak_ai_or_strength",
        "stale_quote_with_missing_ai_provenance",
    }:
        bucket, components = _classify_stale_quote_block(fields)
        return reason, bucket, components
    if stage == "latency_block":
        micro_reason = str(
            fields.get("latency_spread_relief_micro_estimator_reason") or ""
        ).strip()
        detail = str(
            fields.get("latency_danger_detail_reason")
            or fields.get("latency_danger_reasons")
            or ""
        ).strip()
        components = [item for item in (detail, micro_reason) if item]
        if micro_reason == "true_ofi_below_floor":
            return (
                reason or "latency_state_danger",
                "latency_true_ofi_below_floor",
                components,
            )
        return (
            reason or "latency_state_danger",
            f"latency_{micro_reason or detail or 'unspecified'}",
            components,
        )
    if stage == "real_weak_ai_micro_entry_block":
        micro_state = str(fields.get("orderbook_micro_state") or "").strip()
        components = [item for item in (micro_state, reason) if item]
        return (
            reason or "weak_ai_micro",
            f"weak_ai_micro_{micro_state or 'unspecified'}",
            components,
        )
    return reason or "unspecified", reason or stage or "unspecified", []


def _split_csv_values(value: Any) -> list[str]:
    return [
        item.strip()
        for item in str(value or "").split(",")
        if item.strip() and item.strip() != "-"
    ]


def _tp1_counterfactual_decision_context(fields: dict[str, Any]) -> dict[str, Any]:
    """Preserve decision-time inputs alongside a post-horizon TP1 label."""
    return {
        "effective_price_source": fields.get("market_data_effective_price_source"),
        "effective_quote_age_ms": _safe_float(
            fields.get("rising_missed_tp1_effective_quote_age_ms")
        ),
        "ws_quote_age_ms": _safe_float(fields.get("market_data_ws_quote_age_ms")),
        "ws_age_basis": fields.get("market_data_ws_age_basis"),
        "rest_quote_age_ms": _safe_float(fields.get("market_data_rest_quote_age_ms")),
        "rest_age_basis": fields.get("market_data_rest_age_basis"),
        "ws_rest_gap_bps": _safe_float(fields.get("market_data_ws_rest_gap_bps")),
        "freshness_state": fields.get("market_data_freshness_state"),
        "spread_ratio": _safe_float(fields.get("rising_missed_tp1_spread_ratio")),
        "watch_delta_pct": _safe_float(
            fields.get("rising_missed_tp1_actual_watch_delta_pct")
        ),
        "ai_action": fields.get("rising_missed_tp1_ai_action"),
        "bid_imbalance_surge": _optional_boolish(
            fields.get("rising_missed_tp1_bid_imbalance_surge")
        ),
        "source_family_count": _safe_int(
            fields.get("rising_missed_tp1_source_family_count")
        ),
        "ws_micro_ready": _optional_boolish(
            fields.get("rising_missed_tp1_ws_micro_provenance_ready")
        ),
        "ws_signed_fid15_present": _optional_boolish(
            fields.get("rising_missed_tp1_ws_0b_signed_fid15_present")
        ),
        "micro_source_state": fields.get("rising_missed_tp1_micro_source_state"),
        "micro_age_sec": _safe_float(fields.get("rising_missed_tp1_micro_age_sec")),
        "micro_confidence": _safe_float(
            fields.get("rising_missed_tp1_micro_confidence")
        ),
        "true_ofi_ewma": _safe_float(fields.get("rising_missed_tp1_true_ofi_ewma")),
        "true_ofi_sample_count": _safe_int(
            fields.get("rising_missed_tp1_true_ofi_sample_count")
        ),
        "pressure_ewma": _safe_float(fields.get("rising_missed_tp1_pressure_ewma")),
        "depth_imbalance_ewma": _safe_float(
            fields.get("rising_missed_tp1_depth_imbalance_ewma")
        ),
        "top_depth_ratio": _safe_float(fields.get("rising_missed_tp1_top_depth_ratio")),
        "tick_acceleration": _safe_float(
            fields.get("rising_missed_tp1_tick_acceleration")
        ),
        "tick_acceleration_fresh": _optional_boolish(
            fields.get("rising_missed_tp1_tick_acceleration_fresh")
        ),
        "micro_vwap_gap_bps": _safe_float(
            fields.get("rising_missed_tp1_micro_vwap_gap_bps")
        ),
        "micro_vwap_fresh": _optional_boolish(
            fields.get("rising_missed_tp1_micro_vwap_fresh")
        ),
    }


def _submit_safety_block_row(
    row: dict[str, Any],
    *,
    predecessor_bbo: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fields = _fields(row)
    reason, bucket, components = _classify_submit_safety_block(row)
    stage = str(row.get("stage") or "")
    executable_bid, executable_ask, executable_bbo_source = _event_executable_bbo(row)
    predecessor_age_ms = None
    predecessor_stage = None
    if executable_bid is None and predecessor_bbo is not None:
        executable_bid = _safe_float(predecessor_bbo.get("bid"))
        executable_ask = _safe_float(predecessor_bbo.get("ask"))
        executable_bbo_source = str(
            predecessor_bbo.get("source") or "missing_or_invalid_executable_bbo"
        )
        predecessor_age_ms = _safe_float(predecessor_bbo.get("age_ms"))
        predecessor_stage = predecessor_bbo.get("stage")
    requires_executable_bbo = stage in EXECUTABLE_BBO_COUNTERFACTUAL_STAGES
    price = executable_ask if requires_executable_bbo else _event_price(row)
    block_price_source = (
        f"{executable_bbo_source}:executable_ask"
        if requires_executable_bbo and executable_ask is not None
        else (
            "missing_executable_ask"
            if requires_executable_bbo
            else _event_price_with_source(row)[1]
        )
    )
    quote_age = _quote_age_ms(fields)
    tick_speed_window_span_sec = _safe_float(
        fields.get("rising_missed_tick_window_span_sec")
    )
    tick_speed_acceleration_ratio = _safe_float(
        fields.get("rising_missed_tick_acceleration_ratio")
    )
    tick_speed_window_slow = _optional_boolish(
        fields.get("rising_missed_tick_window_slow")
    )
    tick_speed_acceleration_slow = _optional_boolish(
        fields.get("rising_missed_tick_accel_slow")
    )
    if stage != "rising_missed_tick_speed_entry_block":
        tick_speed_block_profile = "not_applicable"
    elif tick_speed_window_span_sec is None or tick_speed_acceleration_ratio is None:
        tick_speed_block_profile = "missing_decision_input"
    elif tick_speed_window_slow and tick_speed_acceleration_slow:
        tick_speed_block_profile = "slow_window_and_relative_acceleration"
    elif tick_speed_window_slow:
        tick_speed_block_profile = "slow_window_only"
    elif tick_speed_acceleration_slow:
        tick_speed_block_profile = "relative_acceleration_only"
    else:
        tick_speed_block_profile = "guard_inputs_not_slow"
    return {
        "ts": _event_ts(row),
        "stage": row.get("stage"),
        "record_id": str(row.get("record_id") or "").strip(),
        "stock_code": _event_code(row),
        "stock_name": _event_name(row),
        "effective_venue": _tp1_effective_venue(fields),
        "market_session_bucket": fields.get("rising_missed_market_session_bucket")
        or fields.get("market_session_bucket")
        or "unknown",
        "reason": reason,
        "blocker_bucket": bucket,
        "components": components,
        "price_delta_since_first_seen_pct": _event_delta_pct(row),
        "block_price": price,
        "block_price_source": block_price_source,
        "counterfactual_requires_executable_bbo": requires_executable_bbo,
        "executable_bbo_state": (
            "pass"
            if executable_bid is not None and executable_ask is not None
            else "source_gap_missing_or_invalid"
        ),
        "executable_bbo_source": executable_bbo_source,
        "executable_bbo_predecessor_stage": predecessor_stage,
        "executable_bbo_predecessor_age_ms": predecessor_age_ms,
        "block_executable_best_bid": executable_bid,
        "block_executable_best_ask": executable_ask,
        "quantity_pre_cap_qty": _safe_int(fields.get("pre_cap_qty")),
        "quantity_effective_qty": _safe_int(fields.get("effective_qty")),
        "quantity_binding_caps": _split_csv_values(fields.get("binding_caps")),
        "quantity_budget_base_krw": _safe_int(fields.get("budget_base")),
        "quantity_target_budget_krw": _safe_int(fields.get("target_budget")),
        "quantity_safe_budget_krw": _safe_int(fields.get("safe_budget")),
        "one_share_floor_position_cap_conflict": bool(
            stage == "blocked_zero_qty"
            and _safe_int(fields.get("pre_cap_qty")) >= 1
            and _safe_int(fields.get("effective_qty")) == 0
            and "max_position_qty_cap" in _split_csv_values(fields.get("binding_caps"))
        ),
        "mfe_after_block_pct": None,
        "mae_after_block_pct": None,
        "post_block_price_event_count": 0,
        "post_block_executable_bbo_event_count": 0,
        "post_block_executable_bbo_source_gap_count": 0,
        "post_block_executable_bbo_venue_mismatch_count": 0,
        "post_block_executable_bbo_out_of_window_count": 0,
        "post_block_first_hit": "not_observed",
        "post_block_first_hit_ts": None,
        "post_block_first_hit_elapsed_sec": None,
        "quote_age_ms": quote_age,
        "quote_age_sec": (
            round(quote_age / 1000.0, 3) if quote_age is not None else None
        ),
        "max_quote_age_ms": _safe_float(
            fields.get("rising_missed_scout_quality_guard_max_quote_age_ms")
        ),
        "ai_action": fields.get("rising_missed_scout_quality_guard_ai_action")
        or fields.get("rising_missed_rest_quote_ai_recheck_ai_action")
        or fields.get("rising_missed_entry_ai_action")
        or fields.get("weak_ai_micro_entry_block_ai_action"),
        "ai_score": _safe_float(
            fields.get("rising_missed_scout_quality_guard_ai_score")
            or fields.get("rising_missed_rest_quote_ai_recheck_ai_score")
            or fields.get("ai_score")
            or fields.get("weak_ai_micro_entry_block_ai_score")
        ),
        "rest_refresh_applied": _optional_boolish(
            fields.get("pre_submit_rest_orderbook_refresh_applied")
        ),
        "rest_refresh_reason": fields.get("pre_submit_rest_orderbook_refresh_reason"),
        "ws_age_ms": _safe_float(
            fields.get("ws_age_ms") or fields.get("quote_consistency_ws_age_ms")
        ),
        "spread_bps": _safe_float(fields.get("latency_spread_block_spread_bps")),
        "spread_ratio": _safe_float(fields.get("spread_ratio")),
        "true_ofi_ewma": _safe_float(
            fields.get("latency_spread_relief_micro_estimator_true_ofi_ewma")
        ),
        "true_ofi_sample_count": _safe_int(
            fields.get("latency_spread_relief_micro_estimator_true_ofi_sample_count")
        ),
        "true_ofi_reason": fields.get("latency_spread_relief_micro_estimator_reason"),
        "runtime_direct_canary_enabled": _optional_boolish(
            fields.get("latency_true_ofi_direct_canary_enabled")
        ),
        "runtime_direct_canary_applied": _optional_boolish(
            fields.get("latency_true_ofi_direct_canary_applied")
        ),
        "runtime_direct_canary_reason": fields.get(
            "latency_true_ofi_direct_canary_reason"
        ),
        "runtime_direct_canary_ws_age_ms": _safe_float(
            fields.get("latency_true_ofi_direct_canary_ws_age_ms")
        ),
        "runtime_direct_canary_effective_max_ws_age_ms": _safe_float(
            fields.get("latency_true_ofi_direct_canary_effective_max_ws_age_ms")
        ),
        "runtime_dynamic_age_band_enabled": _optional_boolish(
            fields.get("latency_true_ofi_direct_canary_dynamic_age_band_enabled")
        ),
        "runtime_dynamic_age_band_active": _optional_boolish(
            fields.get("latency_true_ofi_direct_canary_dynamic_age_band_active")
        ),
        "runtime_dynamic_age_band_eligible": _optional_boolish(
            fields.get("latency_true_ofi_direct_canary_dynamic_age_band_eligible")
        ),
        "runtime_dynamic_age_band_applied": _optional_boolish(
            fields.get("latency_true_ofi_direct_canary_dynamic_age_band_applied")
        ),
        "runtime_dynamic_age_band_max_ws_age_ms": _safe_float(
            fields.get("latency_true_ofi_direct_canary_dynamic_age_band_max_ws_age_ms")
        ),
        "runtime_dynamic_age_band_min_samples": _safe_int(
            fields.get("latency_true_ofi_direct_canary_dynamic_age_band_min_samples")
        ),
        "runtime_dynamic_age_band_max_spread_bps": _safe_float(
            fields.get("latency_true_ofi_direct_canary_dynamic_age_band_max_spread_bps")
        ),
        "runtime_dynamic_age_band_min_true_ofi": _safe_float(
            fields.get("latency_true_ofi_direct_canary_dynamic_age_band_min_true_ofi")
        ),
        "runtime_dynamic_age_band_min_signed_tape_buy_ratio": _safe_float(
            fields.get(
                "latency_true_ofi_direct_canary_dynamic_age_band_min_signed_tape_buy_ratio"
            )
        ),
        "runtime_dynamic_age_band_min_signed_tape_samples": _safe_int(
            fields.get(
                "latency_true_ofi_direct_canary_dynamic_age_band_min_signed_tape_samples"
            )
        ),
        "runtime_signed_tape_sample_count": _safe_int(
            fields.get("latency_true_ofi_direct_canary_signed_tape_sample_count")
        ),
        "runtime_signed_tape_trusted_ws_count": _safe_int(
            fields.get("latency_true_ofi_direct_canary_signed_tape_trusted_ws_count")
        ),
        "runtime_signed_tape_unknown_source_count": _safe_int(
            fields.get(
                "latency_true_ofi_direct_canary_signed_tape_unknown_source_count"
            )
        ),
        "runtime_signed_tape_buy_ratio": _safe_float(
            fields.get("latency_true_ofi_direct_canary_signed_tape_buy_ratio")
        ),
        "runtime_signed_tape_latest_side": fields.get(
            "latency_true_ofi_direct_canary_signed_tape_event_time_latest_side"
        ),
        "runtime_signed_tape_sell_dominated": _optional_boolish(
            fields.get("latency_true_ofi_direct_canary_signed_tape_sell_dominated")
        ),
        "runtime_large_sell_print_detected": _optional_boolish(
            fields.get("latency_true_ofi_direct_canary_large_sell_print_detected")
        ),
        "source_quality_gate": fields.get("source_quality_gate"),
        "source_quality_state": fields.get(
            "weak_ai_micro_entry_block_source_quality_state"
        ),
        "source_quality_missing_fields": _split_csv_values(
            fields.get("weak_ai_micro_entry_block_missing_fields")
        ),
        "orderbook_micro_state": fields.get("orderbook_micro_state"),
        "orderbook_micro_reason": fields.get("orderbook_micro_reason"),
        # Preserve the exact tick-speed veto inputs. The runtime guard stays the
        # authority; these fields only let postclose consumers distinguish a
        # slow absolute tape from a relative-acceleration-only false negative.
        "tick_speed_block_profile": tick_speed_block_profile,
        "tick_speed_decision_input_complete": bool(
            tick_speed_window_span_sec is not None
            and tick_speed_acceleration_ratio is not None
        ),
        "tick_speed_window_span_sec": tick_speed_window_span_sec,
        "tick_speed_window_span_sec_raw": _safe_float(
            fields.get("rising_missed_tick_window_span_sec_raw")
        ),
        "tick_speed_window_max_span_sec": _safe_float(
            fields.get("rising_missed_tick_window_max_span_sec")
        ),
        "tick_speed_window_slow": tick_speed_window_slow,
        "tick_speed_acceleration_ratio": tick_speed_acceleration_ratio,
        "tick_speed_acceleration_ratio_raw": _safe_float(
            fields.get("rising_missed_tick_acceleration_ratio_raw")
        ),
        "tick_speed_min_acceleration_ratio": _safe_float(
            fields.get("rising_missed_min_tick_acceleration_ratio")
        ),
        "tick_speed_acceleration_slow": tick_speed_acceleration_slow,
        "tick_speed_absolute_recent_5tick_seconds": _safe_float(
            fields.get("rising_missed_tick_absolute_recent_5tick_seconds")
        ),
        "tick_speed_absolute_sample_count": _safe_int(
            fields.get("rising_missed_tick_absolute_sample_count")
        ),
        "tick_speed_absolute_quote_age_ms": _safe_float(
            fields.get("rising_missed_tick_absolute_quote_age_ms")
        ),
        "tick_speed_absolute_orderbook_state": fields.get(
            "rising_missed_tick_absolute_orderbook_state"
        ),
        "tick_speed_absolute_tp1_support_count": _safe_int(
            fields.get("rising_missed_tick_absolute_tp1_support_count")
        ),
        "tick_speed_absolute_large_sell_detected": _optional_boolish(
            fields.get("rising_missed_tick_absolute_large_sell_detected")
        ),
        "tick_speed_absolute_relief_enabled": _optional_boolish(
            fields.get("rising_missed_tick_absolute_throughput_relief_enabled")
        ),
        "tick_speed_absolute_relief_active_date": fields.get(
            "rising_missed_tick_absolute_throughput_relief_active_date"
        ),
        "tick_speed_absolute_relief_applied": _optional_boolish(
            fields.get("rising_missed_tick_absolute_throughput_relief_applied")
        ),
        "tick_speed_absolute_relief_path": fields.get(
            "rising_missed_tick_absolute_throughput_relief_path"
        ),
        "tick_speed_absolute_relief_checks": fields.get(
            "rising_missed_tick_absolute_throughput_relief_checks"
        ),
        "buy_pressure_usable": _optional_boolish(
            fields.get("weak_ai_micro_entry_block_buy_pressure_usable")
        ),
        "tick_aggressor_pressure_usable": _optional_boolish(
            fields.get("weak_ai_micro_entry_block_tick_aggressor_pressure_usable")
        ),
        "source_signature": fields.get("source_signature"),
        "scanner_promotion_reason": fields.get("scanner_promotion_reason"),
        "decision_authority": "source_only_submit_safety_blocker_attribution",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "forbidden_uses": FORBIDDEN_USES,
    }


def _update_block_mfe_mae(
    block: dict[str, Any],
    price: float | None,
    *,
    observation_ts: datetime | None = None,
) -> None:
    base = _safe_float(block.get("block_price"))
    if base is None or base <= 0 or price is None or price <= 0:
        return
    move_pct = ((price - base) / base) * 100.0
    block["post_block_price_event_count"] = (
        _safe_int(block.get("post_block_price_event_count")) + 1
    )
    block["mfe_after_block_pct"] = (
        round(move_pct, 4)
        if block.get("mfe_after_block_pct") is None
        else round(max(float(block["mfe_after_block_pct"]), move_pct), 4)
    )
    block["mae_after_block_pct"] = (
        round(move_pct, 4)
        if block.get("mae_after_block_pct") is None
        else round(min(float(block["mae_after_block_pct"]), move_pct), 4)
    )
    if block.get("post_block_first_hit") != "not_observed":
        return
    if move_pct >= TP1_NET_TARGET_PCT:
        first_hit = "net_target_first"
    elif move_pct <= TP1_ADVERSE_STOP_PCT:
        first_hit = "adverse_stop_first"
    else:
        return
    source_ts = _parse_ts(block.get("ts"))
    elapsed_sec = _compatible_elapsed_seconds(observation_ts, source_ts)
    if elapsed_sec is None or elapsed_sec < 0:
        return
    block["post_block_first_hit"] = first_hit
    block["post_block_first_hit_ts"] = observation_ts.isoformat()
    block["post_block_first_hit_elapsed_sec"] = round(elapsed_sec, 3)


def _is_submit_safety_block(row: dict[str, Any]) -> bool:
    fields = _fields(row)
    stage = str(row.get("stage") or "")
    lineage = (
        str(fields.get("forced_entry_reason") or "") == FORCED_REASON
        or _boolish(fields.get("rising_missed_submit_safety_backoff_lineage"))
        or any(str(key).startswith("rising_missed_") for key in fields)
    )
    if not lineage:
        return False
    if stage in {
        "blocked_zero_qty",
        "rising_missed_scout_quality_guard_blocked",
        "latency_block",
        "real_weak_ai_micro_entry_block",
        "rising_missed_tick_speed_entry_block",
    }:
        return True
    return str(fields.get("rising_missed_filter_layer") or "") == "submit_safety" and (
        stage.endswith("_block") or stage.endswith("_blocked")
    )


def _is_backoff_event(row: dict[str, Any]) -> bool:
    fields = _fields(row)
    if str(row.get("stage") or "") != "scalping_scanner_fast_precheck":
        return False
    return str(fields.get("fast_precheck_result") or "") == "budget_reallocated"


def _update_backoff_executable_outcome(
    item: dict[str, Any],
    row: dict[str, Any],
    *,
    observation_ts: datetime | None,
    executable_bid: float | None,
    executable_ask: float | None,
    executable_source: str,
) -> None:
    fields = _fields(row)
    if str(row.get("stage") or "") != "risky_micro_episode_executable_bbo_observed":
        return
    if (
        str(fields.get("risky_micro_episode_horizon_observer_purpose") or "")
        != "rising_missed_backoff_executable_outcome"
    ):
        return
    item["backoff_executable_observer_event_count"] = (
        _safe_int(item.get("backoff_executable_observer_event_count")) + 1
    )
    if not _boolish(fields.get("risky_micro_episode_horizon_observer_quote_fresh")):
        item["backoff_executable_source_gap_count"] = (
            _safe_int(item.get("backoff_executable_source_gap_count")) + 1
        )
        return
    observed_venue = str(_tp1_effective_venue(fields) or "").upper()
    expected_venue = str(item.get("effective_venue") or "").upper()
    if expected_venue and observed_venue != expected_venue:
        item["backoff_executable_venue_mismatch_count"] = (
            _safe_int(item.get("backoff_executable_venue_mismatch_count")) + 1
        )
        return
    source_ts = _parse_ts(item.get("last_backoff_ts"))
    elapsed_sec = _compatible_elapsed_seconds(observation_ts, source_ts)
    if (
        elapsed_sec is None
        or elapsed_sec < 0
        or elapsed_sec > max(BACKOFF_EXECUTABLE_HORIZONS_MIN) * 60.0
    ):
        item["backoff_executable_out_of_window_count"] = (
            _safe_int(item.get("backoff_executable_out_of_window_count")) + 1
        )
        return
    if (
        executable_bid is None
        or executable_bid <= 0
        or executable_ask is None
        or executable_ask < executable_bid
    ):
        item["backoff_executable_source_gap_count"] = (
            _safe_int(item.get("backoff_executable_source_gap_count")) + 1
        )
        return
    entry_ask = _safe_float(item.get("entry_executable_best_ask"))
    if entry_ask is None or entry_ask <= 0:
        entry_ask = executable_ask
        item["entry_executable_best_bid"] = executable_bid
        item["entry_executable_best_ask"] = executable_ask
        item["entry_executable_bbo_source"] = executable_source
        item["entry_executable_bbo_ts"] = _event_ts(row)
    move_pct = ((executable_bid - entry_ask) / entry_ask) * 100.0
    item["backoff_executable_fresh_event_count"] = (
        _safe_int(item.get("backoff_executable_fresh_event_count")) + 1
    )
    current_max = _safe_float(item.get("max_executable_bid_move_pct"))
    current_min = _safe_float(item.get("min_executable_bid_move_pct"))
    item["max_executable_bid_move_pct"] = round(
        move_pct if current_max is None else max(current_max, move_pct), 6
    )
    item["min_executable_bid_move_pct"] = round(
        move_pct if current_min is None else min(current_min, move_pct), 6
    )
    for minutes in BACKOFF_EXECUTABLE_HORIZONS_MIN:
        if elapsed_sec > minutes * 60.0:
            continue
        horizon = item["executable_horizons"][f"{minutes}m"]
        horizon["event_count"] += 1
        horizon_max = _safe_float(horizon.get("mfe_pct"))
        horizon_min = _safe_float(horizon.get("mae_pct"))
        horizon["mfe_pct"] = round(
            move_pct if horizon_max is None else max(horizon_max, move_pct), 6
        )
        horizon["mae_pct"] = round(
            move_pct if horizon_min is None else min(horizon_min, move_pct), 6
        )
    if not item.get("executable_sampled_first_hit"):
        if move_pct >= TP1_GROSS_TARGET_PCT:
            item["executable_sampled_first_hit"] = "sampled_gross_target_first"
        elif move_pct <= TP1_ADVERSE_STOP_PCT:
            item["executable_sampled_first_hit"] = "sampled_adverse_stop_first"
        if item.get("executable_sampled_first_hit"):
            item["executable_sampled_first_hit_ts"] = _event_ts(row)
            item["executable_sampled_first_hit_elapsed_sec"] = round(elapsed_sec, 3)


def _dynamic_age_post_apply_source_row(row: dict[str, Any]) -> dict[str, Any] | None:
    fields = _fields(row)
    if str(row.get("stage") or "") != "scalp_entry_action_decision_snapshot":
        return None
    if not _boolish(
        fields.get("latency_true_ofi_direct_canary_dynamic_age_band_applied")
    ):
        return None
    trace_id = str(fields.get("ai_decision_trace_id") or "").strip()
    if trace_id in {"", "-", "unknown", "not_available"}:
        return None
    executable_bid, executable_ask, executable_source = _event_executable_bbo(row)
    venue = str(fields.get("effective_venue") or fields.get("venue") or "").upper()
    spread_bps = _safe_float(fields.get("latency_spread_block_spread_bps"))
    if (
        spread_bps is None
        and executable_bid is not None
        and executable_ask is not None
        and executable_ask + executable_bid > 0
    ):
        spread_bps = (
            (executable_ask - executable_bid)
            / ((executable_ask + executable_bid) / 2.0)
            * 10000.0
        )
    return {
        "ts": _event_ts(row),
        "record_id": str(row.get("record_id") or "").strip(),
        "stock_code": _event_code(row),
        "stock_name": _event_name(row),
        "effective_venue": venue or "UNKNOWN",
        "ai_decision_trace_id": trace_id,
        "dynamic_age_source_stage": fields.get("source_stage") or "unknown",
        "downstream_terminal_stage": fields.get("source_stage") or "unknown",
        "entry_executable_best_bid": executable_bid,
        "entry_executable_best_ask": executable_ask,
        "entry_executable_bbo_source": executable_source,
        "entry_ws_age_ms": _safe_float(
            fields.get("latency_true_ofi_direct_canary_ws_age_ms")
            or fields.get("pre_submit_ws_snapshot_refresh_age_ms")
        ),
        "entry_spread_bps": round(spread_bps, 4) if spread_bps is not None else None,
        "entry_true_ofi_ewma": _safe_float(
            fields.get("latency_spread_relief_micro_estimator_true_ofi_ewma")
        ),
        "entry_orderbook_micro_ofi_z": _safe_float(fields.get("orderbook_micro_ofi_z")),
        "entry_signed_tape_buy_ratio": _safe_float(
            fields.get("latency_true_ofi_direct_canary_signed_tape_buy_ratio")
        ),
        "actual_order_submitted": _boolish(fields.get("actual_order_submitted")),
        "first_hit": "not_observed",
        "first_hit_ts": None,
        "first_hit_elapsed_sec": None,
        "post_apply_executable_bid_event_count": 0,
        "horizons": {
            f"{minutes}m": {
                "event_count": 0,
                "mfe_pct": None,
                "mae_pct": None,
            }
            for minutes in TP1_POST_BLOCK_HORIZONS_MIN
        },
        "decision_authority": "source_only_dynamic_age_post_apply_attribution",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "forbidden_uses": FORBIDDEN_USES,
    }


def _update_dynamic_age_post_apply_row(
    item: dict[str, Any],
    *,
    observation_ts: datetime | None,
    executable_bid: float | None,
) -> None:
    source_ts = _parse_ts(item.get("ts"))
    entry_ask = _safe_float(item.get("entry_executable_best_ask"))
    if (
        source_ts is None
        or observation_ts is None
        or entry_ask is None
        or entry_ask <= 0
        or executable_bid is None
        or executable_bid <= 0
    ):
        return
    elapsed_sec = (observation_ts - source_ts).total_seconds()
    if elapsed_sec <= 0 or elapsed_sec > max(TP1_POST_BLOCK_HORIZONS_MIN) * 60:
        return
    move_pct = ((executable_bid - entry_ask) / entry_ask) * 100.0
    item["post_apply_executable_bid_event_count"] = (
        _safe_int(item.get("post_apply_executable_bid_event_count")) + 1
    )
    for minutes in TP1_POST_BLOCK_HORIZONS_MIN:
        if elapsed_sec > minutes * 60:
            continue
        horizon = item["horizons"][f"{minutes}m"]
        horizon["event_count"] = _safe_int(horizon.get("event_count")) + 1
        horizon["mfe_pct"] = (
            round(move_pct, 4)
            if horizon.get("mfe_pct") is None
            else round(max(float(horizon["mfe_pct"]), move_pct), 4)
        )
        horizon["mae_pct"] = (
            round(move_pct, 4)
            if horizon.get("mae_pct") is None
            else round(min(float(horizon["mae_pct"]), move_pct), 4)
        )
    if item.get("first_hit") == "not_observed":
        if move_pct >= TP1_NET_TARGET_PCT:
            first_hit = "net_target_first"
        elif move_pct <= TP1_ADVERSE_STOP_PCT:
            first_hit = "adverse_stop_first"
        else:
            return
        item["first_hit"] = first_hit
        item["first_hit_ts"] = observation_ts.isoformat()
        item["first_hit_elapsed_sec"] = round(elapsed_sec, 3)


def _build_submit_safety_and_backoff_audit(
    pipeline_path: Path,
) -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    submit_blocks: list[dict[str, Any]] = []
    open_submit_blocks_by_code: dict[str, list[dict[str, Any]]] = {}
    backoff_by_code: dict[str, dict[str, Any]] = {}
    reason_counts: Counter[str] = Counter()
    bucket_counts: Counter[str] = Counter()
    component_counts: Counter[str] = Counter()
    source_quality_gate_counts: Counter[str] = Counter()
    source_quality_state_counts: Counter[str] = Counter()
    source_quality_missing_field_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    latest_seen_ts: datetime | None = None
    dynamic_age_rows_by_trace: dict[str, dict[str, Any]] = {}
    open_dynamic_age_rows_by_code: dict[str, list[dict[str, Any]]] = {}
    recent_executable_bbo_by_record: dict[str, dict[str, Any]] = {}

    for row in iter_jsonl(pipeline_path):
        code = _event_code(row)
        if not code:
            continue
        fields = _fields(row)
        stage = str(row.get("stage") or "")
        ts = _event_ts(row)
        parsed_ts = _parse_ts(ts)
        if parsed_ts is not None and (
            latest_seen_ts is None or parsed_ts > latest_seen_ts
        ):
            latest_seen_ts = parsed_ts
        observation_price = _tp1_observation_price(row)[0]
        executable_bid, _executable_ask, _executable_bbo_source = _event_executable_bbo(
            row
        )
        delta = _event_delta_pct(row)

        for item in open_dynamic_age_rows_by_code.get(code, []):
            _update_dynamic_age_post_apply_row(
                item,
                observation_ts=parsed_ts,
                executable_bid=executable_bid,
            )

        dynamic_age_source = _dynamic_age_post_apply_source_row(row)
        if dynamic_age_source is not None:
            trace_id = str(dynamic_age_source["ai_decision_trace_id"])
            existing_dynamic_age = dynamic_age_rows_by_trace.get(trace_id)
            if existing_dynamic_age is None:
                dynamic_age_rows_by_trace[trace_id] = dynamic_age_source
                open_dynamic_age_rows_by_code.setdefault(code, []).append(
                    dynamic_age_source
                )
            else:
                existing_dynamic_age["downstream_terminal_stage"] = (
                    dynamic_age_source.get("downstream_terminal_stage")
                    or existing_dynamic_age.get("downstream_terminal_stage")
                )

        for block in open_submit_blocks_by_code.get(code, []):
            if block.get("counterfactual_requires_executable_bbo"):
                block_ts = _parse_ts(block.get("ts"))
                elapsed_sec = _compatible_elapsed_seconds(parsed_ts, block_ts)
                if elapsed_sec is None or elapsed_sec < 0 or elapsed_sec > 3600.0:
                    block["post_block_executable_bbo_out_of_window_count"] = (
                        _safe_int(
                            block.get("post_block_executable_bbo_out_of_window_count")
                        )
                        + 1
                    )
                    continue
                observation_venue = str(_tp1_effective_venue(fields) or "").upper()
                block_venue = str(block.get("effective_venue") or "").upper()
                if observation_venue != block_venue:
                    block["post_block_executable_bbo_venue_mismatch_count"] = (
                        _safe_int(
                            block.get("post_block_executable_bbo_venue_mismatch_count")
                        )
                        + 1
                    )
                    continue
                if executable_bid is None:
                    block["post_block_executable_bbo_source_gap_count"] = (
                        _safe_int(
                            block.get("post_block_executable_bbo_source_gap_count")
                        )
                        + 1
                    )
                    continue
                block["post_block_executable_bbo_event_count"] = (
                    _safe_int(block.get("post_block_executable_bbo_event_count")) + 1
                )
                _update_block_mfe_mae(
                    block,
                    executable_bid,
                    observation_ts=parsed_ts,
                )
            else:
                _update_block_mfe_mae(
                    block,
                    observation_price,
                    observation_ts=parsed_ts,
                )

        if code in backoff_by_code:
            backoff = backoff_by_code[code]
            _update_backoff_executable_outcome(
                backoff,
                row,
                observation_ts=parsed_ts,
                executable_bid=executable_bid,
                executable_ask=_executable_ask,
                executable_source=_executable_bbo_source,
            )
            if delta is not None:
                current = backoff.get("max_delta_after_last_backoff_pct")
                backoff["max_delta_after_last_backoff_pct"] = (
                    delta if current is None else max(float(current), delta)
                )
                backoff["max_delta_after_last_backoff_ts"] = ts
            if (
                stage == "scalping_scanner_fast_precheck"
                and fields.get("fast_precheck_result")
                == "eligible_for_heavy_entry_eval"
            ):
                backoff["fast_pass_after_last_backoff_count"] += 1
                backoff["first_fast_pass_after_last_backoff_ts"] = (
                    backoff.get("first_fast_pass_after_last_backoff_ts") or ts
                )
            if stage == "scalping_scanner_candidate_promoted":
                backoff["promoted_after_last_backoff_count"] += 1
                backoff["first_promoted_after_last_backoff_ts"] = (
                    backoff.get("first_promoted_after_last_backoff_ts") or ts
                )
            if stage == "scalping_scanner_heavy_eval_lag":
                backoff["heavy_eval_after_last_backoff_count"] += 1
                backoff["first_heavy_eval_after_last_backoff_ts"] = (
                    backoff.get("first_heavy_eval_after_last_backoff_ts") or ts
                )

        if _is_submit_safety_block(row):
            predecessor_bbo = None
            record_id = str(row.get("record_id") or "").strip()
            recent_bbo = recent_executable_bbo_by_record.get(record_id)
            if recent_bbo is not None and parsed_ts is not None:
                recent_ts = recent_bbo.get("ts")
                age_sec = _compatible_elapsed_seconds(
                    parsed_ts,
                    recent_ts if isinstance(recent_ts, datetime) else None,
                )
                same_venue = (
                    str(recent_bbo.get("venue") or "").upper()
                    == str(_tp1_effective_venue(fields) or "").upper()
                )
                if (
                    age_sec is not None
                    and 0.0 <= age_sec <= EXECUTABLE_BBO_PREDECESSOR_MAX_AGE_SEC
                    and str(recent_bbo.get("stage") or "")
                    in EXECUTABLE_BBO_PREDECESSOR_STAGES
                    and same_venue
                ):
                    predecessor_bbo = {
                        **recent_bbo,
                        "age_ms": round(age_sec * 1000.0, 3),
                    }
            block = _submit_safety_block_row(
                row,
                predecessor_bbo=predecessor_bbo,
            )
            submit_blocks.append(block)
            open_submit_blocks_by_code.setdefault(code, []).append(block)
            reason_counts[block["reason"]] += 1
            bucket_counts[block["blocker_bucket"]] += 1
            for component in block.get("components") or []:
                component_counts[str(component)] += 1
            if block["reason"] == "source_quality_unknown":
                source_quality_gate_counts[
                    str(block.get("source_quality_gate") or "missing")
                ] += 1
                source_quality_state_counts[
                    str(block.get("source_quality_state") or "missing")
                ] += 1
                source_quality_missing_field_counts.update(
                    str(item)
                    for item in block.get("source_quality_missing_fields") or []
                )
            source = fields.get("scanner_budget_reallocation_source") or fields.get(
                "rising_missed_budget_reallocation_source"
            )
            if source:
                source_counts[str(source)] += 1

        if (
            parsed_ts is not None
            and executable_bid is not None
            and _executable_ask is not None
        ):
            record_id = str(row.get("record_id") or "").strip()
            if record_id:
                recent_executable_bbo_by_record[record_id] = {
                    "bid": executable_bid,
                    "ask": _executable_ask,
                    "source": (f"predecessor:{stage}:{_executable_bbo_source}"),
                    "stage": stage,
                    "ts": parsed_ts,
                    "venue": _tp1_effective_venue(fields),
                }

        if _is_backoff_event(row):
            source = fields.get("scanner_budget_reallocation_source") or fields.get(
                "rising_missed_budget_reallocation_source"
            )
            reason = (
                fields.get("fast_precheck_reason")
                or fields.get("scanner_ws_stale_backoff_reason")
                or fields.get("rising_missed_submit_safety_backoff_reason")
            )
            source_counts[str(source or "unknown")] += 1
            effective_venue = str(_tp1_effective_venue(fields) or "").upper()
            observer_registered = _boolish(
                fields.get("risky_micro_episode_horizon_observer_registered")
            )
            backoff_by_code[code] = {
                "stock_code": code,
                "stock_name": _event_name(row),
                "last_backoff_ts": ts,
                "last_backoff_reason": reason,
                "last_backoff_source": source,
                "last_backoff_delta_pct": delta,
                "max_delta_after_last_backoff_pct": delta,
                "max_delta_after_last_backoff_ts": ts if delta is not None else None,
                "effective_venue": effective_venue or "UNKNOWN",
                "decision_event_executable_best_bid": executable_bid,
                "decision_event_executable_best_ask": _executable_ask,
                "decision_event_executable_bbo_source": _executable_bbo_source,
                "entry_executable_best_bid": None,
                "entry_executable_best_ask": None,
                "entry_executable_bbo_source": "first_fresh_post_backoff_observer",
                "entry_executable_bbo_ts": None,
                "backoff_executable_observer_registered": observer_registered,
                "backoff_executable_observer_status": fields.get(
                    "risky_micro_episode_horizon_observer_status"
                )
                or "not_registered",
                "backoff_executable_observer_event_count": 0,
                "backoff_executable_fresh_event_count": 0,
                "backoff_executable_source_gap_count": 0,
                "backoff_executable_venue_mismatch_count": 0,
                "backoff_executable_out_of_window_count": 0,
                "max_executable_bid_move_pct": None,
                "min_executable_bid_move_pct": None,
                "executable_sampled_first_hit": None,
                "executable_sampled_first_hit_ts": None,
                "executable_sampled_first_hit_elapsed_sec": None,
                "executable_horizons": {
                    f"{minutes}m": {
                        "event_count": 0,
                        "mfe_pct": None,
                        "mae_pct": None,
                    }
                    for minutes in BACKOFF_EXECUTABLE_HORIZONS_MIN
                },
                "fast_pass_after_last_backoff_count": 0,
                "promoted_after_last_backoff_count": 0,
                "heavy_eval_after_last_backoff_count": 0,
                "decision_authority": "source_only_backoff_opportunity_audit",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "forbidden_uses": FORBIDDEN_USES,
            }

    for block in submit_blocks:
        components = block.get("components")
        if isinstance(components, list):
            block["components"] = ",".join(str(item) for item in components)
    audit_rows = sorted(
        backoff_by_code.values(),
        key=lambda item: (
            -1.0
            * (_safe_float(item.get("max_delta_after_last_backoff_pct")) or -999999.0),
            str(item.get("last_backoff_ts") or ""),
        ),
    )
    for item in audit_rows:
        recovered = bool(
            item.get("fast_pass_after_last_backoff_count")
            or item.get("promoted_after_last_backoff_count")
            or item.get("heavy_eval_after_last_backoff_count")
        )
        max_delta = _safe_float(item.get("max_delta_after_last_backoff_pct"))
        last_backoff_ts = _parse_ts(item.get("last_backoff_ts"))
        age_sec = None
        if latest_seen_ts is not None and last_backoff_ts is not None:
            age_sec = max(0.0, (latest_seen_ts - last_backoff_ts).total_seconds())
        item["last_backoff_observation_age_sec"] = (
            round(age_sec, 3) if age_sec is not None else None
        )
        item["backoff_observation_state"] = (
            "mature_unrecovered"
            if age_sec is not None and age_sec >= 180.0 and not recovered
            else "active_or_recovered"
        )
        item["recovered_eval_after_last_backoff"] = recovered
        mark_price_candidate = bool(
            max_delta is not None
            and max_delta >= 1.0
            and not recovered
            and age_sec is not None
            and age_sec >= 180.0
        )
        executable_source_quality_pass = bool(
            item.get("effective_venue") in {"KRX", "NXT", "PREMARKET_KRX_LIKE"}
            and _safe_float(item.get("entry_executable_best_ask")) is not None
            and _safe_int(item.get("backoff_executable_fresh_event_count"))
            >= TP1_POST_BLOCK_MIN_FRESH_PRICE_SAMPLES
        )
        item["mark_price_opportunity_candidate"] = mark_price_candidate
        item["backoff_executable_source_quality_pass"] = executable_source_quality_pass
        item["potential_backoff_opportunity_loss"] = bool(
            executable_source_quality_pass
            and (_safe_float(item.get("max_executable_bid_move_pct")) or -999.0)
            >= TP1_GROSS_TARGET_PCT
            and item.get("executable_sampled_first_hit") == "sampled_gross_target_first"
            and not recovered
            and age_sec is not None
            and age_sec >= 180.0
        )
        item["backoff_opportunity_classification"] = (
            "executable_confirmed_opportunity_loss"
            if item["potential_backoff_opportunity_loss"]
            else (
                "executable_observed_no_target"
                if executable_source_quality_pass
                else (
                    "mark_price_only_unconfirmed"
                    if mark_price_candidate
                    else "no_opportunity_signal"
                )
            )
        )

    dynamic_age_rows = sorted(
        dynamic_age_rows_by_trace.values(),
        key=lambda item: (str(item.get("ts") or ""), str(item.get("stock_code") or "")),
    )
    dynamic_age_first_hit_counts = Counter(
        str(item.get("first_hit") or "not_observed") for item in dynamic_age_rows
    )
    dynamic_age_venue_counts = Counter(
        str(item.get("effective_venue") or "UNKNOWN") for item in dynamic_age_rows
    )
    summary = {
        "submit_safety_block_count": len(submit_blocks),
        "submit_safety_executable_bbo_required_count": sum(
            bool(item.get("counterfactual_requires_executable_bbo"))
            for item in submit_blocks
        ),
        "submit_safety_executable_bbo_entry_source_gap_count": sum(
            bool(item.get("counterfactual_requires_executable_bbo"))
            and item.get("executable_bbo_state") != "pass"
            for item in submit_blocks
        ),
        "submit_safety_executable_bbo_labeled_count": sum(
            bool(item.get("counterfactual_requires_executable_bbo"))
            and item.get("executable_bbo_state") == "pass"
            and _safe_int(item.get("post_block_executable_bbo_event_count")) > 0
            for item in submit_blocks
        ),
        "tick_speed_block_count": sum(
            item.get("stage") == "rising_missed_tick_speed_entry_block"
            for item in submit_blocks
        ),
        "tick_speed_decision_input_complete_count": sum(
            item.get("stage") == "rising_missed_tick_speed_entry_block"
            and bool(item.get("tick_speed_decision_input_complete"))
            for item in submit_blocks
        ),
        "tick_speed_relative_acceleration_only_block_count": sum(
            item.get("tick_speed_block_profile") == "relative_acceleration_only"
            for item in submit_blocks
        ),
        "tick_speed_absolute_relief_applied_count": sum(
            item.get("stage") == "rising_missed_tick_speed_entry_block"
            and bool(item.get("tick_speed_absolute_relief_applied"))
            for item in submit_blocks
        ),
        "blocked_zero_qty_count": sum(
            item.get("stage") == "blocked_zero_qty" for item in submit_blocks
        ),
        "blocked_zero_qty_one_share_floor_position_cap_conflict_count": sum(
            bool(item.get("one_share_floor_position_cap_conflict"))
            for item in submit_blocks
        ),
        "blocked_zero_qty_executable_bbo_labeled_count": sum(
            item.get("stage") == "blocked_zero_qty"
            and item.get("executable_bbo_state") == "pass"
            and _safe_int(item.get("post_block_executable_bbo_event_count")) > 0
            for item in submit_blocks
        ),
        "submit_safety_reason_counts": [
            {"reason": key, "count": value}
            for key, value in reason_counts.most_common()
        ],
        "submit_safety_bucket_counts": [
            {"blocker_bucket": key, "count": value}
            for key, value in bucket_counts.most_common()
        ],
        "submit_safety_component_counts": [
            {"component": key, "count": value}
            for key, value in component_counts.most_common()
        ],
        "submit_safety_source_quality_unknown_gate_counts": [
            {"source_quality_gate": key, "count": value}
            for key, value in source_quality_gate_counts.most_common()
        ],
        "submit_safety_source_quality_unknown_state_counts": [
            {"source_quality_state": key, "count": value}
            for key, value in source_quality_state_counts.most_common()
        ],
        "submit_safety_source_quality_unknown_missing_field_counts": [
            {"missing_field": key, "count": value}
            for key, value in source_quality_missing_field_counts.most_common()
        ],
        "budget_reallocation_source_counts": [
            {"source": key, "count": value}
            for key, value in source_counts.most_common()
        ],
        "backoff_audit_symbol_count": len(audit_rows),
        "backoff_recovered_eval_symbol_count": sum(
            1 for item in audit_rows if item["recovered_eval_after_last_backoff"]
        ),
        "backoff_active_positive_delta_symbol_count": sum(
            1
            for item in audit_rows
            if (_safe_float(item.get("max_delta_after_last_backoff_pct")) or 0.0) >= 1.0
            and not item["recovered_eval_after_last_backoff"]
            and item.get("backoff_observation_state") == "active_or_recovered"
        ),
        "potential_backoff_opportunity_loss_count": sum(
            1 for item in audit_rows if item["potential_backoff_opportunity_loss"]
        ),
        "backoff_mark_price_opportunity_candidate_count": sum(
            1 for item in audit_rows if item["mark_price_opportunity_candidate"]
        ),
        "backoff_executable_source_quality_pass_count": sum(
            1 for item in audit_rows if item["backoff_executable_source_quality_pass"]
        ),
        "backoff_executable_source_quality_gap_count": sum(
            1
            for item in audit_rows
            if item["mark_price_opportunity_candidate"]
            and not item["backoff_executable_source_quality_pass"]
        ),
        "dynamic_age_post_apply_episode_count": len(dynamic_age_rows),
        "dynamic_age_post_apply_latency_pass_count": sum(
            item.get("dynamic_age_source_stage") == "latency_pass"
            for item in dynamic_age_rows
        ),
        "dynamic_age_post_apply_actual_order_submitted_count": sum(
            bool(item.get("actual_order_submitted")) for item in dynamic_age_rows
        ),
        "dynamic_age_post_apply_executable_bbo_source_gap_count": sum(
            _safe_float(item.get("entry_executable_best_ask")) is None
            for item in dynamic_age_rows
        ),
        "dynamic_age_post_apply_venue_source_gap_count": sum(
            item.get("effective_venue") not in {"KRX", "NXT", "PREMARKET_KRX_LIKE"}
            for item in dynamic_age_rows
        ),
        "dynamic_age_post_apply_outcome_source_gap_count": sum(
            _safe_int(item.get("post_apply_executable_bid_event_count")) < 2
            for item in dynamic_age_rows
        ),
        "dynamic_age_post_apply_source_quality_pass_count": sum(
            _safe_float(item.get("entry_executable_best_ask")) is not None
            and item.get("effective_venue") in {"KRX", "NXT", "PREMARKET_KRX_LIKE"}
            and _safe_int(item.get("post_apply_executable_bid_event_count")) >= 2
            for item in dynamic_age_rows
        ),
        "dynamic_age_post_apply_first_hit_counts": [
            {"first_hit": key, "count": value}
            for key, value in dynamic_age_first_hit_counts.most_common()
        ],
        "dynamic_age_post_apply_venue_counts": [
            {"effective_venue": key, "count": value}
            for key, value in dynamic_age_venue_counts.most_common()
        ],
    }
    return summary, submit_blocks, audit_rows, dynamic_age_rows


def _latency_false_negative_review_bucket(block: dict[str, Any]) -> str | None:
    if str(block.get("stage") or "") != "latency_block":
        return None
    blocker_bucket = str(block.get("blocker_bucket") or "")
    true_ofi_reason = str(block.get("true_ofi_reason") or "")
    components = str(block.get("components") or "")
    if blocker_bucket in {
        "latency_true_ofi_below_floor",
        "latency_true_ofi_samples_below_floor",
    }:
        return "true_ofi_false_negative_candidate"
    if true_ofi_reason in {"true_ofi_below_floor", "true_ofi_samples_below_floor"}:
        return "true_ofi_false_negative_candidate"
    if blocker_bucket in {
        "latency_spread_above_caution",
        "latency_spread_above_caution_below_guard_cap",
    }:
        return "spread_caution_false_negative_candidate"
    if "spread_above_caution" in components:
        return "spread_caution_false_negative_candidate"
    return None


def _build_latency_false_negative_review(
    submit_blocks: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    bucket_counts: Counter[str] = Counter()
    for block in submit_blocks:
        review_bucket = _latency_false_negative_review_bucket(block)
        if review_bucket is None:
            continue
        blocker_bucket = str(block.get("blocker_bucket") or "")
        if blocker_bucket not in LATENCY_FALSE_NEGATIVE_BUCKETS:
            components = str(block.get("components") or "")
            if (
                "spread_above_caution" not in components
                and "true_ofi_below_floor" not in components
            ):
                continue
        mfe = _safe_float(block.get("mfe_after_block_pct"))
        mae = _safe_float(block.get("mae_after_block_pct"))
        if mfe is None or mae is None:
            continue
        if (
            mfe < LATENCY_FALSE_NEGATIVE_MIN_MFE_PCT
            or mae < -LATENCY_FALSE_NEGATIVE_MAX_MAE_ABS_PCT
        ):
            continue
        bucket_counts[review_bucket] += 1
        rows.append(
            {
                "ts": block.get("ts"),
                "stage": block.get("stage"),
                "record_id": block.get("record_id"),
                "stock_code": block.get("stock_code"),
                "stock_name": block.get("stock_name"),
                "effective_venue": block.get("effective_venue"),
                "market_session_bucket": block.get("market_session_bucket"),
                "review_bucket": review_bucket,
                "review_reason": "latency_submit_safety_block_high_mfe_low_mae",
                "blocker_bucket": blocker_bucket,
                "reason": block.get("reason"),
                "components": block.get("components"),
                "block_price": block.get("block_price"),
                "block_price_source": block.get("block_price_source"),
                "executable_bbo_state": block.get("executable_bbo_state"),
                "executable_bbo_source": block.get("executable_bbo_source"),
                "block_executable_best_bid": block.get("block_executable_best_bid"),
                "block_executable_best_ask": block.get("block_executable_best_ask"),
                "mfe_after_block_pct": mfe,
                "mae_after_block_pct": mae,
                "post_block_price_event_count": block.get(
                    "post_block_price_event_count"
                ),
                "post_block_executable_bbo_event_count": block.get(
                    "post_block_executable_bbo_event_count"
                ),
                "post_block_executable_bbo_source_gap_count": block.get(
                    "post_block_executable_bbo_source_gap_count"
                ),
                "price_delta_since_first_seen_pct": block.get(
                    "price_delta_since_first_seen_pct"
                ),
                "quote_age_sec": block.get("quote_age_sec"),
                "ws_age_ms": block.get("ws_age_ms"),
                "spread_bps": block.get("spread_bps"),
                "spread_ratio": block.get("spread_ratio"),
                "true_ofi_ewma": block.get("true_ofi_ewma"),
                "true_ofi_sample_count": block.get("true_ofi_sample_count"),
                "true_ofi_reason": block.get("true_ofi_reason"),
                "runtime_direct_canary_enabled": block.get(
                    "runtime_direct_canary_enabled"
                ),
                "runtime_direct_canary_applied": block.get(
                    "runtime_direct_canary_applied"
                ),
                "runtime_direct_canary_reason": block.get(
                    "runtime_direct_canary_reason"
                ),
                "runtime_direct_canary_ws_age_ms": block.get(
                    "runtime_direct_canary_ws_age_ms"
                ),
                "runtime_direct_canary_effective_max_ws_age_ms": block.get(
                    "runtime_direct_canary_effective_max_ws_age_ms"
                ),
                "runtime_dynamic_age_band_enabled": block.get(
                    "runtime_dynamic_age_band_enabled"
                ),
                "runtime_dynamic_age_band_active": block.get(
                    "runtime_dynamic_age_band_active"
                ),
                "runtime_dynamic_age_band_eligible": block.get(
                    "runtime_dynamic_age_band_eligible"
                ),
                "runtime_dynamic_age_band_applied": block.get(
                    "runtime_dynamic_age_band_applied"
                ),
                "runtime_dynamic_age_band_max_ws_age_ms": block.get(
                    "runtime_dynamic_age_band_max_ws_age_ms"
                ),
                "runtime_dynamic_age_band_min_samples": block.get(
                    "runtime_dynamic_age_band_min_samples"
                ),
                "runtime_dynamic_age_band_max_spread_bps": block.get(
                    "runtime_dynamic_age_band_max_spread_bps"
                ),
                "runtime_dynamic_age_band_min_true_ofi": block.get(
                    "runtime_dynamic_age_band_min_true_ofi"
                ),
                "runtime_dynamic_age_band_min_signed_tape_buy_ratio": block.get(
                    "runtime_dynamic_age_band_min_signed_tape_buy_ratio"
                ),
                "runtime_dynamic_age_band_min_signed_tape_samples": block.get(
                    "runtime_dynamic_age_band_min_signed_tape_samples"
                ),
                "runtime_signed_tape_sample_count": block.get(
                    "runtime_signed_tape_sample_count"
                ),
                "runtime_signed_tape_trusted_ws_count": block.get(
                    "runtime_signed_tape_trusted_ws_count"
                ),
                "runtime_signed_tape_unknown_source_count": block.get(
                    "runtime_signed_tape_unknown_source_count"
                ),
                "runtime_signed_tape_buy_ratio": block.get(
                    "runtime_signed_tape_buy_ratio"
                ),
                "runtime_signed_tape_latest_side": block.get(
                    "runtime_signed_tape_latest_side"
                ),
                "runtime_signed_tape_sell_dominated": block.get(
                    "runtime_signed_tape_sell_dominated"
                ),
                "runtime_large_sell_print_detected": block.get(
                    "runtime_large_sell_print_detected"
                ),
                "ai_action": block.get("ai_action"),
                "ai_score": block.get("ai_score"),
                "source_signature": block.get("source_signature"),
                "scanner_promotion_reason": block.get("scanner_promotion_reason"),
                "decision_authority": "source_only_latency_false_negative_review",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "forbidden_uses": FORBIDDEN_USES,
            }
        )
    rows.sort(
        key=lambda item: (
            -1.0 * (_safe_float(item.get("mfe_after_block_pct")) or -999999.0),
            _safe_float(item.get("mae_after_block_pct")) or -999999.0,
            str(item.get("ts") or ""),
        )
    )
    summary = {
        "latency_false_negative_review_count": len(rows),
        "latency_false_negative_true_ofi_count": bucket_counts.get(
            "true_ofi_false_negative_candidate", 0
        ),
        "latency_false_negative_spread_only_count": bucket_counts.get(
            "spread_caution_false_negative_candidate", 0
        ),
        "latency_false_negative_review_bucket_counts": [
            {"review_bucket": key, "count": value}
            for key, value in bucket_counts.most_common()
        ],
        "latency_false_negative_min_mfe_pct": LATENCY_FALSE_NEGATIVE_MIN_MFE_PCT,
        "latency_false_negative_max_mae_abs_pct": LATENCY_FALSE_NEGATIVE_MAX_MAE_ABS_PCT,
    }
    return summary, rows


def _latency_canary_cohort(row: dict[str, Any]) -> str:
    review_bucket = str(row.get("review_bucket") or "")
    if review_bucket == "true_ofi_false_negative_candidate":
        return "true_ofi_near_zero_false_negative"
    if review_bucket == "spread_caution_false_negative_candidate":
        return "spread_only_false_negative"
    return "unclassified_latency_false_negative"


def _latency_canary_grade(row: dict[str, Any], review_score: float) -> tuple[str, str]:
    cohort = _latency_canary_cohort(row)
    ws_age = _safe_float(row.get("ws_age_ms"))
    spread_bps = _safe_float(row.get("spread_bps"))
    true_ofi = _safe_float(row.get("true_ofi_ewma"))
    sample_count = _safe_int(row.get("true_ofi_sample_count"))
    if ws_age is None or ws_age > LATENCY_CANARY_FRESH_WS_MAX_AGE_MS:
        return "hold_sample", "ws_age_not_fresh_enough_for_canary_recheck"
    if review_score < LATENCY_CANARY_MIN_REVIEW_SCORE_PCT:
        return "hold_sample", "post_block_mfe_mae_score_below_canary_floor"
    if cohort == "true_ofi_near_zero_false_negative":
        if sample_count < LATENCY_CANARY_TRUE_OFI_MIN_SAMPLE_COUNT:
            return "hold_sample", "true_ofi_sample_count_below_canary_floor"
        if true_ofi is None:
            return "hold_sample", "true_ofi_missing"
        if true_ofi < LATENCY_CANARY_TRUE_OFI_NEAR_ZERO_FLOOR:
            return "observe_only", "true_ofi_still_materially_negative"
        return "ready_for_recheck", "true_ofi_near_zero_or_positive_with_fresh_ws"
    if cohort == "spread_only_false_negative":
        if spread_bps is None:
            return "hold_sample", "spread_bps_missing"
        if spread_bps > LATENCY_CANARY_SPREAD_ONLY_MAX_SPREAD_BPS:
            return "observe_wide_spread", "spread_bps_above_spread_only_canary_cap"
        return (
            "ready_for_recheck",
            "spread_only_false_negative_with_fresh_ws_and_bounded_spread",
        )
    return "hold_sample", "unclassified_latency_false_negative"


def _build_latency_false_negative_canary_candidates(
    review_rows: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    cohort_counts: Counter[str] = Counter()
    grade_counts: Counter[str] = Counter()
    runtime_dynamic_age_state_counts: Counter[str] = Counter()
    for item in review_rows:
        mfe = _safe_float(item.get("mfe_after_block_pct"))
        mae = _safe_float(item.get("mae_after_block_pct"))
        if mfe is None or mae is None:
            continue
        review_score = round(mfe - abs(mae), 4)
        cohort = _latency_canary_cohort(item)
        grade, reason = _latency_canary_grade(item, review_score)
        dynamic_active = item.get("runtime_dynamic_age_band_active")
        dynamic_eligible = item.get("runtime_dynamic_age_band_eligible")
        dynamic_applied = item.get("runtime_dynamic_age_band_applied")
        if (
            dynamic_active is None
            or dynamic_eligible is None
            or dynamic_applied is None
        ):
            dynamic_state = "source_gap_not_observed"
        elif not dynamic_active:
            dynamic_state = "observed_inactive"
        elif dynamic_applied:
            dynamic_state = "observed_active_applied"
        elif dynamic_eligible:
            dynamic_state = "observed_active_eligible_not_applied"
        else:
            dynamic_state = "observed_active_not_eligible"
        cohort_counts[cohort] += 1
        grade_counts[grade] += 1
        runtime_dynamic_age_state_counts[dynamic_state] += 1
        rows.append(
            {
                **item,
                "canary_candidate_family": "latency_false_negative_canary_candidate",
                "canary_cohort": cohort,
                "canary_grade": grade,
                "canary_reason": reason,
                "canary_primary_review_score_pct": review_score,
                "canary_min_review_score_pct": LATENCY_CANARY_MIN_REVIEW_SCORE_PCT,
                "canary_true_ofi_min_sample_count": LATENCY_CANARY_TRUE_OFI_MIN_SAMPLE_COUNT,
                "canary_fresh_ws_max_age_ms": LATENCY_CANARY_FRESH_WS_MAX_AGE_MS,
                "canary_spread_only_max_spread_bps": LATENCY_CANARY_SPREAD_ONLY_MAX_SPREAD_BPS,
                "canary_next_action": (
                    "next_scanner_loop_feature_envelope_review"
                    if grade == "ready_for_recheck"
                    else "source_only_accumulate_more_false_negative_samples"
                ),
                "runtime_dynamic_age_band_provenance_state": dynamic_state,
                "runtime_dynamic_age_band_contract_relation": (
                    "diagnostic_parallel_to_strict_recheck_no_grade_override"
                ),
                "decision_authority": "source_only_latency_false_negative_canary_candidate",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "forbidden_uses": FORBIDDEN_USES,
            }
        )
    rows.sort(
        key=lambda row: (
            0 if row.get("canary_grade") == "ready_for_recheck" else 1,
            -1.0
            * (_safe_float(row.get("canary_primary_review_score_pct")) or -999999.0),
            str(row.get("ts") or ""),
        )
    )
    summary = {
        "latency_false_negative_canary_candidate_count": len(rows),
        "latency_false_negative_canary_ready_count": grade_counts.get(
            "ready_for_recheck", 0
        ),
        "latency_false_negative_canary_observe_wide_spread_count": grade_counts.get(
            "observe_wide_spread", 0
        ),
        "latency_false_negative_canary_hold_sample_count": grade_counts.get(
            "hold_sample", 0
        ),
        "latency_false_negative_canary_cohort_counts": [
            {"canary_cohort": key, "count": value}
            for key, value in cohort_counts.most_common()
        ],
        "latency_false_negative_canary_grade_counts": [
            {"canary_grade": key, "count": value}
            for key, value in grade_counts.most_common()
        ],
        "latency_false_negative_runtime_dynamic_age_state_counts": [
            {"runtime_dynamic_age_state": key, "count": value}
            for key, value in runtime_dynamic_age_state_counts.most_common()
        ],
        "latency_false_negative_runtime_dynamic_age_source_gap_count": (
            runtime_dynamic_age_state_counts.get("source_gap_not_observed", 0)
        ),
        "latency_false_negative_runtime_dynamic_age_eligible_count": (
            runtime_dynamic_age_state_counts.get(
                "observed_active_eligible_not_applied", 0
            )
            + runtime_dynamic_age_state_counts.get("observed_active_applied", 0)
        ),
        "latency_false_negative_runtime_dynamic_age_applied_count": (
            runtime_dynamic_age_state_counts.get("observed_active_applied", 0)
        ),
        "latency_false_negative_canary_min_review_score_pct": LATENCY_CANARY_MIN_REVIEW_SCORE_PCT,
        "latency_false_negative_canary_true_ofi_min_sample_count": LATENCY_CANARY_TRUE_OFI_MIN_SAMPLE_COUNT,
        "latency_false_negative_canary_fresh_ws_max_age_ms": LATENCY_CANARY_FRESH_WS_MAX_AGE_MS,
        "latency_false_negative_canary_spread_only_max_spread_bps": LATENCY_CANARY_SPREAD_ONLY_MAX_SPREAD_BPS,
    }
    return summary, rows


def _clean_baseline_rolling_latency_false_negative_candidates(
    target_date: str,
    current_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Roll source-only latency false negatives without restoring retry authority."""

    source_rows: list[tuple[str, dict[str, Any]]] = [
        (target_date, dict(row)) for row in current_rows
    ]
    inspected_source_dates = {target_date}
    excluded_reports: list[dict[str, str]] = []
    prefix = "rising_missed_intraday_feedback_"
    eligible_paths: list[Path] = []
    for path in sorted(REPORT_DIR.glob(f"{prefix}*.json")):
        report_date = path.stem.removeprefix(prefix)
        if CLEAN_BASELINE_DATE <= report_date < target_date:
            eligible_paths.append(path)
    prior_limit = max(0, LATENCY_FALSE_NEGATIVE_ROLLING_REPORT_DAYS - 1)
    for path in eligible_paths[-prior_limit:] if prior_limit else []:
        report_date = path.stem.removeprefix(prefix)
        try:
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError):
            excluded_reports.append(
                {"target_date": report_date, "reason": "report_unreadable"}
            )
            continue
        if not isinstance(payload, dict) or (
            payload.get("report_type") != "rising_missed_intraday_feedback"
            or payload.get("target_date") != report_date
            or bool(payload.get("runtime_effect"))
            or bool(payload.get("allowed_runtime_apply"))
        ):
            excluded_reports.append(
                {"target_date": report_date, "reason": "report_contract_invalid"}
            )
            continue
        daily_rows = payload.get("latency_false_negative_canary_candidate_rows")
        if not isinstance(daily_rows, list):
            excluded_reports.append(
                {"target_date": report_date, "reason": "daily_candidates_missing"}
            )
            continue
        inspected_source_dates.add(report_date)
        source_rows.extend(
            (report_date, dict(row)) for row in daily_rows if isinstance(row, dict)
        )

    valid_venues = {"KRX", "NXT", "PREMARKET_KRX_LIKE"}
    source_gap_rows = 0
    grouped: dict[tuple[str, str, str], list[tuple[str, dict[str, Any]]]] = {}
    for report_date, row in source_rows:
        venue = str(row.get("effective_venue") or "").strip().upper()
        session = str(row.get("market_session_bucket") or "").strip()
        cohort = str(row.get("canary_cohort") or "").strip()
        mfe = _safe_float(row.get("mfe_after_block_pct"))
        mae = _safe_float(row.get("mae_after_block_pct"))
        if (
            venue not in valid_venues
            or not session
            or session == "unknown"
            or not cohort
            or mfe is None
            or mae is None
        ):
            source_gap_rows += 1
            continue
        grouped.setdefault((venue, session, cohort), []).append((report_date, row))

    rolling_rows: list[dict[str, Any]] = []
    for (venue, session, cohort), dated_rows in grouped.items():
        sample_count = len(dated_rows)
        mfe_values = [float(row["mfe_after_block_pct"]) for _, row in dated_rows]
        mae_values = [float(row["mae_after_block_pct"]) for _, row in dated_rows]
        ready_count = sum(
            str(row.get("canary_grade") or "") == "ready_for_recheck"
            for _, row in dated_rows
        )
        low_adverse_count = sum(
            float(row.get("mae_after_block_pct")) >= TP1_ADVERSE_STOP_PCT
            and float(row.get("mfe_after_block_pct"))
            >= LATENCY_FALSE_NEGATIVE_MIN_MFE_PCT
            for _, row in dated_rows
        )
        ready_rate_pct = ready_count * 100.0 / sample_count
        low_adverse_rate_pct = low_adverse_count * 100.0 / sample_count
        sample_floor_met = sample_count >= 10
        consistent_low_adverse_edge = bool(
            sample_floor_met
            and low_adverse_count >= 3
            and ready_count >= 3
            and low_adverse_rate_pct >= LATENCY_ROLLING_MIN_LOW_ADVERSE_RATE_PCT
            and ready_rate_pct >= LATENCY_ROLLING_MIN_READY_RATE_PCT
        )
        rolling_rows.append(
            {
                "effective_venue": venue,
                "market_session_bucket": session,
                "canary_cohort": cohort,
                "completed_sample_count": sample_count,
                "ready_for_recheck_count": ready_count,
                "ready_for_recheck_rate_pct": round(ready_rate_pct, 6),
                "low_adverse_opportunity_count": low_adverse_count,
                "low_adverse_opportunity_rate_pct": round(low_adverse_rate_pct, 6),
                "equal_weight_avg_mfe_after_block_pct": round(
                    sum(mfe_values) / sample_count, 6
                ),
                "equal_weight_avg_mae_after_block_pct": round(
                    sum(mae_values) / sample_count, 6
                ),
                "rolling_assessment": (
                    "source_only_next_scanner_loop_feature_review_priority"
                    if consistent_low_adverse_edge
                    else (
                        "hold_sample"
                        if not sample_floor_met
                        else "hold_no_consistent_low_adverse_edge"
                    )
                ),
                "next_action": (
                    "review_normal_entry_feature_envelope_on_next_scanner_loop"
                    if consistent_low_adverse_edge
                    else "source_only_accumulate"
                ),
                "metric_role": "source_only_latency_false_negative_rolling_attribution",
                "decision_authority": "source_only_no_retry_or_runtime_mutation",
                "window_policy": "clean_baseline_rolling_latest_20_report_artifacts",
                "clean_tuning_baseline_date": CLEAN_BASELINE_DATE,
                "source_dates": sorted({report_date for report_date, _ in dated_rows}),
                "sample_floor": "10_executable_bbo_latency_false_negative_rows_per_venue_session_cohort",
                "sample_floor_met": sample_floor_met,
                "minimum_low_adverse_rate_pct": (
                    LATENCY_ROLLING_MIN_LOW_ADVERSE_RATE_PCT
                ),
                "minimum_ready_for_recheck_rate_pct": (
                    LATENCY_ROLLING_MIN_READY_RATE_PCT
                ),
                "primary_decision_metric": (
                    "low_adverse_opportunity_rate_pct_and_ready_for_recheck_rate_pct_"
                    "with_equal_weight_mfe_mae"
                ),
                "source_quality_gate": (
                    "explicit_venue_session_executable_ask_and_post_block_executable_bid"
                ),
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "forbidden_uses": FORBIDDEN_USES,
            }
        )
    rolling_rows.sort(
        key=lambda row: (
            (
                0
                if row.get("rolling_assessment")
                == "source_only_next_scanner_loop_feature_review_priority"
                else 1
            ),
            -_safe_int(row.get("completed_sample_count")),
            str(row.get("effective_venue")),
            str(row.get("market_session_bucket")),
            str(row.get("canary_cohort")),
        )
    )
    usable_source_dates = sorted(
        {
            report_date
            for dated_rows in grouped.values()
            for report_date, _ in dated_rows
        }
    )
    usable_row_count = sum(len(dated_rows) for dated_rows in grouped.values())
    total_input_row_count = usable_row_count + source_gap_rows
    return rolling_rows, {
        "window_policy": "clean_baseline_rolling_latest_20_report_artifacts",
        "clean_tuning_baseline_date": CLEAN_BASELINE_DATE,
        "rolling_report_day_limit": LATENCY_FALSE_NEGATIVE_ROLLING_REPORT_DAYS,
        "start_date": usable_source_dates[0] if usable_source_dates else target_date,
        "end_date": target_date,
        "source_dates": usable_source_dates,
        "source_date_count": len(usable_source_dates),
        "inspected_source_dates": sorted(inspected_source_dates),
        "inspected_source_date_count": len(inspected_source_dates),
        "usable_row_count": usable_row_count,
        "total_input_row_count": total_input_row_count,
        "usable_row_rate_pct": (
            round(usable_row_count * 100.0 / total_input_row_count, 6)
            if total_input_row_count
            else 0.0
        ),
        "source_gap_row_count": source_gap_rows,
        "source_quality_state": (
            (
                "pass_with_row_exclusions"
                if usable_row_count
                else "source_quality_blocked_no_usable_rows"
            )
            if source_gap_rows
            else "pass"
        ),
        "excluded_report_count": len(excluded_reports),
        "excluded_reports": excluded_reports,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }


def _tp1_label_timestamp(value: Any) -> datetime | None:
    parsed = _parse_ts(value)
    if parsed is None:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=KST)


def _tp1_actual_costs(fields: dict[str, Any]) -> tuple[float | None, float | None]:
    fee = _safe_float(
        fields.get("actual_fee_krw")
        if fields.get("actual_fee_krw") not in (None, "", "-")
        else fields.get("fee_krw")
    )
    tax = _safe_float(
        fields.get("actual_tax_krw")
        if fields.get("actual_tax_krw") not in (None, "", "-")
        else fields.get("tax_krw")
    )
    return fee, tax


def _tp1_effective_venue(fields: dict[str, Any]) -> str:
    """Retain only explicit venue provenance; never infer a venue from session."""

    value = (
        str(
            fields.get("rising_missed_effective_venue")
            or fields.get("effective_venue")
            or fields.get("venue")
            or ""
        )
        .strip()
        .upper()
    )
    return value if value in {"KRX", "NXT", "PREMARKET_KRX_LIKE"} else "unknown"


def _tp1_venue_resolution(fields: dict[str, Any]) -> str:
    """Preserve the explicit producer resolution without session inference."""

    return str(fields.get("venue_resolution") or "missing").strip() or "missing"


def _tp1_post_block_measurement_state(
    *,
    observation_watermark: datetime | None,
    horizon_end: datetime,
    observed_price_event_count: int,
    non_executable_price_event_count: int = 0,
) -> str:
    """Classify whether a bounded post-block window is actually measurable."""

    if observation_watermark is None or observation_watermark < horizon_end:
        return "pending_horizon"
    if observed_price_event_count <= 0:
        if non_executable_price_event_count > 0:
            return "source_gap_non_executable_price_only"
        return "source_gap_no_post_block_price"
    if observed_price_event_count < TP1_POST_BLOCK_MIN_FRESH_PRICE_SAMPLES:
        return "source_gap_insufficient_post_block_price"
    return "pass"


def _tp1_post_block_horizon_measurements(
    events: list[dict[str, Any]],
    *,
    start_index: int,
    candidate_ts: datetime | None,
    code: str,
    entry_price: float | None,
    observation_watermark: datetime | None,
    evaluation_id: str = "",
) -> dict[str, Any]:
    """Build source-only bounded outcomes without treating the candidate anchor as a sample.

    A later global pipeline event proves only that the clock advanced.  It does not
    prove that the blocked symbol was observed.  Each horizon therefore keeps its
    own same-symbol price coverage state before it can be labelled as ``no_hit``.
    """

    if candidate_ts is None or entry_price is None or entry_price <= 0 or not code:
        return {
            "evaluation_horizons_min": list(TP1_POST_BLOCK_HORIZONS_MIN),
            "horizon_measurements": [],
            "late_recovery_after_adverse": {
                "detected": False,
                "reason": "input_unavailable",
            },
        }

    measurements = {
        horizon_min: {
            "horizon_min": horizon_min,
            "horizon_sec": horizon_min * 60,
            "horizon_end": candidate_ts + timedelta(minutes=horizon_min),
            "observed_price_event_count": 0,
            "non_executable_price_event_count": 0,
            "first_hit_label": None,
            "first_hit_ts": None,
            "first_hit_move_pct": None,
            "first_hit_price_source": None,
            "max_move_pct": None,
            "min_move_pct": None,
            "sampler_completion_mfe_pct": None,
            "sampler_completion_mae_pct": None,
            "sampler_completion_label": None,
            "sampler_completion_first_hit_ts": None,
            "sampler_completion_first_hit_move_pct": None,
        }
        for horizon_min in TP1_POST_BLOCK_HORIZONS_MIN
    }
    max_horizon_end = measurements[max(TP1_POST_BLOCK_HORIZONS_MIN)]["horizon_end"]
    first_adverse_ts: str | None = None
    first_adverse_move_pct: float | None = None
    first_target_after_adverse_ts: str | None = None
    first_target_after_adverse_move_pct: float | None = None
    first_boundary_label: str | None = None

    observation_rows: list[tuple[datetime, int, dict[str, Any]]] = []
    for position, subsequent in enumerate(events[start_index + 1 :], start_index + 1):
        if _event_code(subsequent) != code:
            continue
        event_ts = _tp1_label_timestamp(_event_ts(subsequent))
        if event_ts is None or event_ts <= candidate_ts or event_ts > max_horizon_end:
            continue
        observation_rows.append((event_ts, position, subsequent))

    for event_ts, _position, subsequent in sorted(observation_rows):
        fields = _fields(subsequent)
        stage = str(subsequent.get("stage") or "")
        event_evaluation_id = str(
            fields.get("rising_missed_tp1_evaluation_id") or ""
        ).strip()
        is_nxt_sampler_event = stage.startswith("rising_missed_nxt_post_block_")
        if is_nxt_sampler_event and (
            not evaluation_id or event_evaluation_id != evaluation_id
        ):
            # NXT sampler prices are evaluation-scoped.  A legacy candidate
            # without an evaluation id cannot safely consume them, and neither
            # can a different evaluation for the same symbol.
            continue
        if stage in {
            "rising_missed_nxt_post_block_sampler_registered",
            "rising_missed_nxt_post_block_sampler_restored",
            "rising_missed_nxt_post_block_sampler_registration_skipped",
        }:
            # Registration repeats the entry anchor; it is not a post-block price.
            continue
        if stage == "rising_missed_nxt_post_block_price_sampler_completed":
            completion_horizon_sec = _safe_float(
                fields.get("rising_missed_nxt_post_block_horizon_sec")
            )
            completion_horizon_sec = (
                completion_horizon_sec
                if completion_horizon_sec is not None and completion_horizon_sec > 0
                else TP1_LABEL_HORIZON_SEC
            )
            completion_mfe = _safe_float(
                fields.get("rising_missed_nxt_post_block_max_move_pct")
            )
            completion_mae = _safe_float(
                fields.get("rising_missed_nxt_post_block_min_move_pct")
            )
            completion_label = str(
                fields.get("rising_missed_nxt_post_block_sampler_outcome_label") or ""
            )
            completion_first_hit_move = _safe_float(
                fields.get("rising_missed_nxt_post_block_first_hit_move_pct")
            )
            completion_first_hit_ts = fields.get(
                "rising_missed_nxt_post_block_first_hit_ts"
            )
            for measurement in measurements.values():
                if measurement["horizon_sec"] < completion_horizon_sec:
                    continue
                measurement["sampler_completion_mfe_pct"] = completion_mfe
                measurement["sampler_completion_mae_pct"] = completion_mae
                measurement["sampler_completion_label"] = completion_label
                measurement["sampler_completion_first_hit_ts"] = completion_first_hit_ts
                measurement["sampler_completion_first_hit_move_pct"] = (
                    completion_first_hit_move
                )
            continue

        executable_bid, _executable_ask, bbo_source = _event_executable_bbo(subsequent)
        if executable_bid is None or executable_bid <= 0:
            mark_price, _mark_source = _tp1_observation_price(subsequent)
            if mark_price is not None and mark_price > 0:
                for measurement in measurements.values():
                    if event_ts <= measurement["horizon_end"]:
                        measurement["non_executable_price_event_count"] += 1
            continue
        price = executable_bid
        price_source = f"{bbo_source}:best_bid"
        move_pct = ((price - entry_price) / entry_price) * 100.0
        for measurement in measurements.values():
            if event_ts > measurement["horizon_end"]:
                continue
            measurement["observed_price_event_count"] += 1
            measurement["max_move_pct"] = (
                move_pct
                if measurement["max_move_pct"] is None
                else max(float(measurement["max_move_pct"]), move_pct)
            )
            measurement["min_move_pct"] = (
                move_pct
                if measurement["min_move_pct"] is None
                else min(float(measurement["min_move_pct"]), move_pct)
            )
            if measurement["first_hit_label"] is None:
                if move_pct >= TP1_GROSS_TARGET_PCT:
                    measurement["first_hit_label"] = "gross_target_first"
                elif move_pct <= TP1_ADVERSE_STOP_PCT:
                    measurement["first_hit_label"] = "adverse_stop_first"
                if measurement["first_hit_label"] is not None:
                    measurement["first_hit_ts"] = _event_ts(subsequent)
                    measurement["first_hit_move_pct"] = move_pct
                    measurement["first_hit_price_source"] = price_source
        if first_boundary_label is None:
            if move_pct >= TP1_GROSS_TARGET_PCT:
                first_boundary_label = "gross_target_first"
            elif move_pct <= TP1_ADVERSE_STOP_PCT:
                first_boundary_label = "adverse_stop_first"
                first_adverse_ts = _event_ts(subsequent)
                first_adverse_move_pct = move_pct
        elif (
            first_boundary_label == "adverse_stop_first"
            and first_target_after_adverse_ts is None
            and move_pct >= TP1_GROSS_TARGET_PCT
        ):
            first_target_after_adverse_ts = _event_ts(subsequent)
            first_target_after_adverse_move_pct = move_pct

    rendered: list[dict[str, Any]] = []
    for horizon_min in TP1_POST_BLOCK_HORIZONS_MIN:
        measurement = measurements[horizon_min]
        completion_mfe = measurement["sampler_completion_mfe_pct"]
        completion_mae = measurement["sampler_completion_mae_pct"]
        if completion_mfe is not None:
            measurement["max_move_pct"] = (
                completion_mfe
                if measurement["max_move_pct"] is None
                else max(float(measurement["max_move_pct"]), completion_mfe)
            )
        if completion_mae is not None:
            measurement["min_move_pct"] = (
                completion_mae
                if measurement["min_move_pct"] is None
                else min(float(measurement["min_move_pct"]), completion_mae)
            )
        if measurement["first_hit_label"] is None and measurement[
            "sampler_completion_label"
        ] in {"gross_target_first", "adverse_stop_first"}:
            measurement["first_hit_label"] = measurement["sampler_completion_label"]
            measurement["first_hit_ts"] = measurement["sampler_completion_first_hit_ts"]
            measurement["first_hit_move_pct"] = measurement[
                "sampler_completion_first_hit_move_pct"
            ]
            measurement["first_hit_price_source"] = "nxt_post_block_sampler_completion"

        measurement_state = _tp1_post_block_measurement_state(
            observation_watermark=observation_watermark,
            horizon_end=measurement["horizon_end"],
            observed_price_event_count=measurement["observed_price_event_count"],
            non_executable_price_event_count=measurement[
                "non_executable_price_event_count"
            ],
        )
        if measurement["first_hit_label"] is not None:
            outcome_label = measurement["first_hit_label"]
        elif measurement_state == "pending_horizon":
            outcome_label = "pending_horizon"
        elif measurement_state == "pass":
            outcome_label = f"no_hit_within_{horizon_min}m"
        else:
            outcome_label = measurement_state
        rendered.append(
            {
                "horizon_min": horizon_min,
                "horizon_sec": measurement["horizon_sec"],
                "outcome_label": outcome_label,
                "source_quality_state": measurement_state,
                "observed_price_event_count": measurement["observed_price_event_count"],
                "non_executable_price_event_count": measurement[
                    "non_executable_price_event_count"
                ],
                "first_hit_ts": measurement["first_hit_ts"],
                "first_hit_move_pct": (
                    round(float(measurement["first_hit_move_pct"]), 4)
                    if measurement["first_hit_move_pct"] is not None
                    else None
                ),
                "first_hit_price_source": measurement["first_hit_price_source"],
                "max_move_pct": (
                    round(float(measurement["max_move_pct"]), 4)
                    if measurement["max_move_pct"] is not None
                    else None
                ),
                "min_move_pct": (
                    round(float(measurement["min_move_pct"]), 4)
                    if measurement["min_move_pct"] is not None
                    else None
                ),
            }
        )

    late_recovery_horizon_min = None
    if first_target_after_adverse_ts:
        target_ts = _tp1_label_timestamp(first_target_after_adverse_ts)
        if target_ts is not None:
            late_recovery_horizon_min = next(
                (
                    horizon_min
                    for horizon_min in TP1_POST_BLOCK_HORIZONS_MIN
                    if target_ts <= measurements[horizon_min]["horizon_end"]
                ),
                None,
            )
    return {
        "evaluation_horizons_min": list(TP1_POST_BLOCK_HORIZONS_MIN),
        "horizon_measurements": rendered,
        "late_recovery_after_adverse": {
            "detected": bool(first_adverse_ts and first_target_after_adverse_ts),
            "first_adverse_ts": first_adverse_ts,
            "first_adverse_move_pct": (
                round(first_adverse_move_pct, 4)
                if first_adverse_move_pct is not None
                else None
            ),
            "first_target_after_adverse_ts": first_target_after_adverse_ts,
            "first_target_after_adverse_move_pct": (
                round(first_target_after_adverse_move_pct, 4)
                if first_target_after_adverse_move_pct is not None
                else None
            ),
            "first_recovery_horizon_min": late_recovery_horizon_min,
            "reason": (
                "adverse_first_then_late_target_observed"
                if first_adverse_ts and first_target_after_adverse_ts
                else "not_observed"
            ),
        },
    }


def _tp1_primary_horizon_measurement(
    multi_horizon: dict[str, Any], *, horizon_min: int = 20
) -> dict[str, Any]:
    for measurement in multi_horizon.get("horizon_measurements") or []:
        if _safe_int(measurement.get("horizon_min")) == horizon_min:
            return measurement
    return {}


def _tp1_counterfactual_multi_horizon_summary(
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    coverage_counts: Counter[tuple[int, str]] = Counter()
    outcome_counts: Counter[tuple[int, str]] = Counter()
    late_recovery_count = 0
    late_recovery_horizon_counts: Counter[str] = Counter()
    for row in rows:
        recovery = row.get("post_block_late_recovery_after_adverse") or {}
        if recovery.get("detected"):
            late_recovery_count += 1
            late_recovery_horizon_counts[
                str(recovery.get("first_recovery_horizon_min") or "unresolved")
            ] += 1
        for measurement in row.get("post_block_horizon_measurements") or []:
            horizon_min = _safe_int(measurement.get("horizon_min"))
            if horizon_min not in TP1_POST_BLOCK_HORIZONS_MIN:
                continue
            coverage_counts[
                (horizon_min, str(measurement.get("source_quality_state") or "unknown"))
            ] += 1
            outcome_counts[
                (horizon_min, str(measurement.get("outcome_label") or "unknown"))
            ] += 1
    return {
        "rising_missed_tp1_counterfactual_multi_horizon_labeled_count": len(rows),
        "rising_missed_tp1_counterfactual_multi_horizon_coverage_counts": [
            {
                "horizon_min": horizon_min,
                "source_quality_state": source_quality_state,
                "count": count,
            }
            for (horizon_min, source_quality_state), count in sorted(
                coverage_counts.items()
            )
        ],
        "rising_missed_tp1_counterfactual_multi_horizon_outcome_counts": [
            {
                "horizon_min": horizon_min,
                "outcome_label": outcome_label,
                "count": count,
            }
            for (horizon_min, outcome_label), count in sorted(outcome_counts.items())
        ],
        "rising_missed_tp1_counterfactual_late_recovery_after_adverse_count": (
            late_recovery_count
        ),
        "rising_missed_tp1_counterfactual_late_recovery_horizon_counts": [
            {"first_recovery_horizon_min": horizon, "count": count}
            for horizon, count in sorted(late_recovery_horizon_counts.items())
        ],
    }


def _tp1_counterfactual_multi_horizon_by_effective_venue(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Keep explicit KRX/NXT cohorts separate from unavailable venue provenance."""

    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        venue = str(row.get("effective_venue") or "unknown")
        grouped.setdefault(venue, []).append(row)
    return [
        {
            "effective_venue": venue,
            **_tp1_counterfactual_multi_horizon_summary(venue_rows),
        }
        for venue, venue_rows in sorted(grouped.items())
    ]


def _tp1_label_candidate_kind(row: dict[str, Any]) -> str:
    fields = _fields(row)
    if str(row.get("stage") or "") == "rising_missed_tp1_counterfactual_submit_safety":
        return "counterfactual"
    if (
        _boolish(fields.get("rising_missed_tp1_selector_active"))
        and _boolish(fields.get("rising_missed_tp1_candidate_allowed"))
        and str(fields.get("rising_missed_tp1_candidate_reason") or "")
        == "rising_missed_tp1_candidate_pass"
    ):
        return "candidate"
    return ""


def _tp1_label_event_projection(row: dict[str, Any]) -> dict[str, Any]:
    """Drop unrelated high-volume diagnostics from retained TP1 label rows."""

    fields = _fields(row)
    projected_fields = {
        key: value
        for key, value in fields.items()
        if key in TP1_LABEL_PROJECTION_FIELD_KEYS
    }
    return {
        key: row[key]
        for key in (
            "pipeline",
            "record_id",
            "stock_code",
            "stock_name",
            "stage",
            "emitted_at",
            "timestamp",
            "ts",
        )
        if key in row
    } | {"fields": projected_fields}


def _load_tp1_label_event_projection(
    pipeline_path: Path,
) -> tuple[list[dict[str, Any]], datetime | None]:
    """Load only TP1 candidate/price rows instead of the complete pipeline.

    The intraday pipeline can grow to several gigabytes.  Materializing every
    decoded event made this report consume multiple gigabytes of RSS and could
    starve the live bot.  The first streaming pass identifies candidate symbols
    and the global observation watermark.  The second retains only rows that
    can change a TP1 label: candidates, usable prices, sampler lifecycle rows,
    or explicit fee/tax evidence.
    """

    candidate_codes: set[str] = set()
    observation_watermark: datetime | None = None
    for row in iter_jsonl(pipeline_path):
        timestamp = _tp1_label_timestamp(_event_ts(row))
        if timestamp is not None and (
            observation_watermark is None or timestamp > observation_watermark
        ):
            observation_watermark = timestamp
        if _tp1_label_candidate_kind(row):
            code = _event_code(row)
            if code:
                candidate_codes.add(code)

    if not candidate_codes:
        return [], observation_watermark

    projected: list[dict[str, Any]] = []
    for row in iter_jsonl(pipeline_path):
        if _event_code(row) not in candidate_codes:
            continue
        fields = _fields(row)
        stage = str(row.get("stage") or "")
        price, _price_source = _tp1_observation_price(row)
        executable_bid, executable_ask, _bbo_source = _event_executable_bbo(row)
        fee, tax = _tp1_actual_costs(fields)
        if (
            _tp1_label_candidate_kind(row)
            or (price is not None and price > 0)
            or (executable_bid is not None and executable_ask is not None)
            or stage.startswith("rising_missed_nxt_post_block_")
            or fee is not None
            or tax is not None
        ):
            projected.append(_tp1_label_event_projection(row))
    return projected, observation_watermark


def _build_tp1_first_hit_labels(
    pipeline_path: Path,
    *,
    label_events: list[dict[str, Any]] | None = None,
    observation_watermark: datetime | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if label_events is None:
        events, loaded_watermark = _load_tp1_label_event_projection(pipeline_path)
        observation_watermark = observation_watermark or loaded_watermark
    else:
        events = label_events
    candidates: list[tuple[int, dict[str, Any]]] = []
    for index, row in enumerate(events):
        fields = _fields(row)
        if not _boolish(fields.get("rising_missed_tp1_selector_active")):
            continue
        if not _boolish(fields.get("rising_missed_tp1_candidate_allowed")):
            continue
        if (
            str(fields.get("rising_missed_tp1_candidate_reason") or "")
            != "rising_missed_tp1_candidate_pass"
        ):
            continue
        candidates.append((index, row))

    labels: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, ...]] = set()
    for index, candidate in candidates:
        fields = _fields(candidate)
        code = _event_code(candidate)
        record_id = str(candidate.get("record_id") or "").strip()
        candidate_ts_text = _event_ts(candidate)
        evaluation_id = str(fields.get("rising_missed_tp1_evaluation_id") or "").strip()
        dedupe_key = (
            ("evaluation_id", evaluation_id)
            if evaluation_id
            else ("legacy_event", record_id, code, candidate_ts_text)
        )
        if not code or dedupe_key in seen_keys:
            continue
        seen_keys.add(dedupe_key)
        candidate_ts = _tp1_label_timestamp(candidate_ts_text)
        entry_executable_bid, entry_executable_ask, entry_bbo_source = (
            _event_executable_bbo(candidate)
        )
        entry_price = entry_executable_ask
        entry_price_source = (
            f"{entry_bbo_source}:best_ask"
            if entry_price is not None and entry_price > 0
            else "missing_or_invalid_executable_ask"
        )
        label = (
            "source_gap_missing_executable_entry_bbo"
            if candidate_ts is not None
            else "input_unavailable"
        )
        first_hit_ts = None
        first_hit_move_pct = None
        first_hit_price_source = None
        max_move_pct = None
        min_move_pct = None
        observed_event_count = 0
        latest_ts = candidate_ts
        actual_fee_krw, actual_tax_krw = _tp1_actual_costs(fields)
        if candidate_ts is not None and entry_price is not None and entry_price > 0:
            label = "pending_horizon"
            horizon_end = candidate_ts + timedelta(seconds=TP1_LABEL_HORIZON_SEC)
            for subsequent in events[index:]:
                if _event_code(subsequent) != code:
                    continue
                event_ts = _tp1_label_timestamp(_event_ts(subsequent))
                if (
                    event_ts is None
                    or event_ts < candidate_ts
                    or event_ts > horizon_end
                ):
                    continue
                later_fee, later_tax = _tp1_actual_costs(_fields(subsequent))
                if later_fee is not None:
                    actual_fee_krw = later_fee
                if later_tax is not None:
                    actual_tax_krw = later_tax
                price, _price_source = _tp1_observation_price(subsequent)
                if price is None or price <= 0:
                    continue
                observed_event_count += 1
                latest_ts = max(latest_ts or event_ts, event_ts)
                move_pct = ((price - entry_price) / entry_price) * 100.0
                max_move_pct = (
                    move_pct if max_move_pct is None else max(max_move_pct, move_pct)
                )
                min_move_pct = (
                    move_pct if min_move_pct is None else min(min_move_pct, move_pct)
                )
                if first_hit_ts is None:
                    if move_pct >= TP1_GROSS_TARGET_PCT:
                        label = "gross_target_first"
                        first_hit_ts = _event_ts(subsequent)
                        first_hit_move_pct = move_pct
                    elif move_pct <= TP1_ADVERSE_STOP_PCT:
                        label = "adverse_stop_first"
                        first_hit_ts = _event_ts(subsequent)
                        first_hit_move_pct = move_pct
            if (
                label == "pending_horizon"
                and observation_watermark is not None
                and observation_watermark >= horizon_end
            ):
                label = "no_hit_within_20m"

        multi_horizon = _tp1_post_block_horizon_measurements(
            events,
            start_index=index,
            candidate_ts=candidate_ts,
            code=code,
            entry_price=entry_price,
            observation_watermark=observation_watermark,
            evaluation_id=evaluation_id,
        )
        primary_horizon = _tp1_primary_horizon_measurement(multi_horizon)
        if primary_horizon:
            label = str(primary_horizon.get("outcome_label") or label)
            first_hit_ts = primary_horizon.get("first_hit_ts")
            first_hit_move_pct = primary_horizon.get("first_hit_move_pct")
            first_hit_price_source = primary_horizon.get("first_hit_price_source")
            max_move_pct = primary_horizon.get("max_move_pct")
            min_move_pct = primary_horizon.get("min_move_pct")
            observed_event_count = _safe_int(
                primary_horizon.get("observed_price_event_count")
            )

        actual_costs_available = (
            actual_fee_krw is not None and actual_tax_krw is not None
        )
        actual_cost_pct = None
        net_label = "unavailable_fee_tax_missing"
        if actual_costs_available and entry_price is not None and entry_price > 0:
            quantity = max(
                1,
                _safe_int(
                    fields.get("forced_entry_qty") or fields.get("quantity") or 1
                ),
            )
            notional = entry_price * quantity
            actual_cost_pct = ((actual_fee_krw + actual_tax_krw) / notional) * 100.0
            if label == "gross_target_first" and first_hit_move_pct is not None:
                net_label = (
                    "net_target_confirmed"
                    if first_hit_move_pct - actual_cost_pct >= TP1_NET_TARGET_PCT
                    else "net_target_not_met"
                )
            elif label == "pending_horizon":
                net_label = "pending_horizon"
            elif label == "input_unavailable":
                net_label = "input_unavailable"
            else:
                net_label = "net_target_not_met"
        labels.append(
            {
                "record_id": record_id,
                "stock_code": code,
                "stock_name": _event_name(candidate),
                "candidate_ts": candidate_ts_text,
                "candidate_stage": candidate.get("stage"),
                "candidate_lane": fields.get("rising_missed_tp1_candidate_lane"),
                "effective_venue": _tp1_effective_venue(fields),
                "venue_resolution": _tp1_venue_resolution(fields),
                "market_session_bucket": fields.get(
                    "rising_missed_market_session_bucket"
                )
                or fields.get("market_session_bucket")
                or "unknown",
                "evaluation_id": evaluation_id or None,
                "entry_price": entry_price,
                "entry_price_source": entry_price_source,
                "entry_executable_best_bid": entry_executable_bid,
                "entry_executable_best_ask": entry_executable_ask,
                "entry_executable_bbo_state": (
                    "pass"
                    if entry_executable_bid is not None
                    and entry_executable_ask is not None
                    else "source_gap_missing_or_invalid"
                ),
                "gross_first_hit_label": label,
                "first_hit_ts": first_hit_ts,
                "first_hit_move_pct": (
                    round(first_hit_move_pct, 4)
                    if first_hit_move_pct is not None
                    else None
                ),
                "first_hit_price_source": first_hit_price_source,
                "max_move_pct_within_20m": (
                    round(max_move_pct, 4) if max_move_pct is not None else None
                ),
                "min_move_pct_within_20m": (
                    round(min_move_pct, 4) if min_move_pct is not None else None
                ),
                "observed_price_event_count": observed_event_count,
                "post_block_horizon_measurements": multi_horizon.get(
                    "horizon_measurements"
                )
                or [],
                "post_block_late_recovery_after_adverse": multi_horizon.get(
                    "late_recovery_after_adverse"
                )
                or {},
                "gross_target_pct": TP1_GROSS_TARGET_PCT,
                "adverse_stop_pct": TP1_ADVERSE_STOP_PCT,
                "horizon_sec": TP1_LABEL_HORIZON_SEC,
                "cost_reserve_pct": TP1_COST_RESERVE_PCT,
                "net_target_pct": TP1_NET_TARGET_PCT,
                "actual_fee_krw": actual_fee_krw,
                "actual_tax_krw": actual_tax_krw,
                "actual_cost_pct": (
                    round(actual_cost_pct, 6) if actual_cost_pct is not None else None
                ),
                "net_label": net_label,
                "decision_authority": "source_only_tp1_outcome_label",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "forbidden_uses": FORBIDDEN_USES,
            }
        )
    counts = Counter(
        str(item.get("gross_first_hit_label") or "unknown") for item in labels
    )
    net_counts = Counter(str(item.get("net_label") or "unknown") for item in labels)
    return {
        "rising_missed_tp1_labeled_candidate_count": len(labels),
        "rising_missed_tp1_gross_label_counts": [
            {"gross_first_hit_label": key, "count": value}
            for key, value in counts.most_common()
        ],
        "rising_missed_tp1_net_label_counts": [
            {"net_label": key, "count": value}
            for key, value in net_counts.most_common()
        ],
        "rising_missed_tp1_net_confirmed_count": net_counts.get(
            "net_target_confirmed", 0
        ),
    }, labels


def _build_tp1_counterfactual_submit_safety(
    pipeline_path: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    action_counts: Counter[str] = Counter()
    selector_reason_counts: Counter[str] = Counter()
    risk_counts: Counter[str] = Counter()
    unique_symbols: set[str] = set()
    rows: list[dict[str, Any]] = []
    for row in iter_jsonl(pipeline_path):
        if (
            str(row.get("stage") or "")
            != "rising_missed_tp1_counterfactual_submit_safety"
        ):
            continue
        fields = _fields(row)
        action = str(
            fields.get("rising_missed_tp1_counterfactual_submit_safety_action")
            or "not_evaluated"
        )
        selector_reason = str(fields.get("selector_reason") or "not_evaluated")
        risks = [
            token.strip()
            for token in str(
                fields.get("rising_missed_tp1_counterfactual_submit_safety_risks") or ""
            ).split(",")
            if token.strip() and token.strip() != "-"
        ]
        code = _event_code(row)
        if code:
            unique_symbols.add(code)
        action_counts[action] += 1
        selector_reason_counts[selector_reason] += 1
        risk_counts.update(risks)
        rows.append(
            {
                "ts": _event_ts(row),
                "stock_code": code,
                "stock_name": _event_name(row),
                "record_id": row.get("record_id"),
                "evaluation_id": fields.get("rising_missed_tp1_evaluation_id"),
                "source_stage": fields.get("source_stage"),
                "selector_reason": selector_reason,
                "selector_deferred": _boolish(fields.get("selector_deferred")),
                "candidate_lane": fields.get("rising_missed_tp1_candidate_lane"),
                "positive_support_count": _safe_int(
                    fields.get("rising_missed_tp1_positive_support_count")
                ),
                "positive_support_families": fields.get(
                    "rising_missed_tp1_positive_support_families"
                ),
                "counterfactual_action": action,
                "counterfactual_risks": risks,
                "effective_venue": _tp1_effective_venue(fields),
                "venue_resolution": _tp1_venue_resolution(fields),
                **_tp1_counterfactual_decision_context(fields),
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "decision_authority": "source_only_candidate_to_submit_safety_projection",
                "forbidden_uses": FORBIDDEN_USES,
            }
        )
    return {
        "rising_missed_tp1_counterfactual_submit_safety_count": len(rows),
        "rising_missed_tp1_counterfactual_unique_symbol_count": len(unique_symbols),
        "rising_missed_tp1_counterfactual_action_counts": [
            {"action": key, "count": value}
            for key, value in action_counts.most_common()
        ],
        "rising_missed_tp1_counterfactual_selector_reason_counts": [
            {"selector_reason": key, "count": value}
            for key, value in selector_reason_counts.most_common()
        ],
        "rising_missed_tp1_counterfactual_risk_counts": [
            {"risk": key, "count": value} for key, value in risk_counts.most_common()
        ],
    }, rows


def _build_tp1_counterfactual_first_hit_labels(
    pipeline_path: Path,
    *,
    label_events: list[dict[str, Any]] | None = None,
    observation_watermark: datetime | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if label_events is None:
        events, loaded_watermark = _load_tp1_label_event_projection(pipeline_path)
        observation_watermark = observation_watermark or loaded_watermark
    else:
        events = label_events
    labels: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, ...]] = set()
    for index, candidate in enumerate(events):
        if (
            str(candidate.get("stage") or "")
            != "rising_missed_tp1_counterfactual_submit_safety"
        ):
            continue
        fields = _fields(candidate)
        code = _event_code(candidate)
        candidate_ts_text = _event_ts(candidate)
        evaluation_id = str(fields.get("rising_missed_tp1_evaluation_id") or "").strip()
        record_id = str(candidate.get("record_id") or "").strip()
        dedupe_key = (
            ("evaluation_id", evaluation_id)
            if evaluation_id
            else ("legacy_event", record_id, code, candidate_ts_text)
        )
        if not code or dedupe_key in seen_keys:
            continue
        seen_keys.add(dedupe_key)

        candidate_ts = _tp1_label_timestamp(candidate_ts_text)
        entry_executable_bid, entry_executable_ask, entry_bbo_source = (
            _event_executable_bbo(candidate)
        )
        entry_price = entry_executable_ask
        entry_price_source = (
            f"{entry_bbo_source}:best_ask"
            if entry_price is not None and entry_price > 0
            else "missing_or_invalid_executable_ask"
        )
        label = (
            "source_gap_missing_executable_entry_bbo"
            if candidate_ts is not None
            else "input_unavailable"
        )
        first_hit_ts = None
        first_hit_move_pct = None
        first_hit_price_source = None
        max_move_pct = None
        min_move_pct = None
        observed_event_count = 0
        if candidate_ts is not None and entry_price is not None and entry_price > 0:
            label = "pending_horizon"
            horizon_end = candidate_ts + timedelta(seconds=TP1_LABEL_HORIZON_SEC)
            for subsequent in events[index:]:
                if _event_code(subsequent) != code:
                    continue
                subsequent_fields = _fields(subsequent)
                subsequent_stage = str(subsequent.get("stage") or "")
                subsequent_evaluation_id = str(
                    subsequent_fields.get("rising_missed_tp1_evaluation_id") or ""
                ).strip()
                is_sampler_event = subsequent_stage.startswith(
                    "rising_missed_nxt_post_block_"
                )
                if (
                    is_sampler_event
                    and evaluation_id
                    and subsequent_evaluation_id != evaluation_id
                ):
                    continue
                event_ts = _tp1_label_timestamp(_event_ts(subsequent))
                if event_ts is None or event_ts < candidate_ts:
                    continue
                if (
                    subsequent_stage
                    == "rising_missed_nxt_post_block_price_sampler_completed"
                    and subsequent_evaluation_id == evaluation_id
                ):
                    completion_max = _safe_float(
                        subsequent_fields.get(
                            "rising_missed_nxt_post_block_max_move_pct"
                        )
                    )
                    completion_min = _safe_float(
                        subsequent_fields.get(
                            "rising_missed_nxt_post_block_min_move_pct"
                        )
                    )
                    if completion_max is not None:
                        max_move_pct = completion_max
                    if completion_min is not None:
                        min_move_pct = completion_min
                    completion_label = str(
                        subsequent_fields.get(
                            "rising_missed_nxt_post_block_sampler_outcome_label"
                        )
                        or ""
                    )
                    if completion_label in {
                        "gross_target_first",
                        "adverse_stop_first",
                        "no_hit_within_20m",
                    }:
                        label = completion_label
                    completion_first_hit = _safe_float(
                        subsequent_fields.get(
                            "rising_missed_nxt_post_block_first_hit_move_pct"
                        )
                    )
                    if completion_first_hit is not None:
                        first_hit_move_pct = completion_first_hit
                        completion_first_hit_ts = subsequent_fields.get(
                            "rising_missed_nxt_post_block_first_hit_ts"
                        )
                        if completion_first_hit_ts not in (None, "", "-"):
                            first_hit_ts = completion_first_hit_ts
                    continue
                if event_ts > horizon_end:
                    continue
                price, _price_source = _tp1_observation_price(subsequent)
                if price is None or price <= 0:
                    continue
                observed_event_count += 1
                move_pct = ((price - entry_price) / entry_price) * 100.0
                max_move_pct = (
                    move_pct if max_move_pct is None else max(max_move_pct, move_pct)
                )
                min_move_pct = (
                    move_pct if min_move_pct is None else min(min_move_pct, move_pct)
                )
                if first_hit_ts is None:
                    if move_pct >= TP1_GROSS_TARGET_PCT:
                        label = "gross_target_first"
                        first_hit_ts = _event_ts(subsequent)
                        first_hit_move_pct = move_pct
                    elif move_pct <= TP1_ADVERSE_STOP_PCT:
                        label = "adverse_stop_first"
                        first_hit_ts = _event_ts(subsequent)
                        first_hit_move_pct = move_pct
            if (
                label == "pending_horizon"
                and observation_watermark is not None
                and observation_watermark >= horizon_end
            ):
                label = "no_hit_within_20m"

        multi_horizon = _tp1_post_block_horizon_measurements(
            events,
            start_index=index,
            candidate_ts=candidate_ts,
            code=code,
            entry_price=entry_price,
            observation_watermark=observation_watermark,
            evaluation_id=evaluation_id,
        )
        primary_horizon = _tp1_primary_horizon_measurement(multi_horizon)
        if primary_horizon:
            label = str(primary_horizon.get("outcome_label") or label)
            first_hit_ts = primary_horizon.get("first_hit_ts")
            first_hit_move_pct = primary_horizon.get("first_hit_move_pct")
            first_hit_price_source = primary_horizon.get("first_hit_price_source")
            max_move_pct = primary_horizon.get("max_move_pct")
            min_move_pct = primary_horizon.get("min_move_pct")
            observed_event_count = _safe_int(
                primary_horizon.get("observed_price_event_count")
            )

        labels.append(
            {
                "record_id": record_id,
                "stock_code": code,
                "stock_name": _event_name(candidate),
                "candidate_ts": candidate_ts_text,
                "evaluation_id": evaluation_id or None,
                "selector_reason": fields.get("selector_reason"),
                "selector_deferred": _boolish(fields.get("selector_deferred")),
                "effective_venue": _tp1_effective_venue(fields),
                "venue_resolution": _tp1_venue_resolution(fields),
                "market_session_bucket": fields.get(
                    "rising_missed_market_session_bucket"
                )
                or fields.get("market_session_bucket")
                or "unknown",
                "counterfactual_action": fields.get(
                    "rising_missed_tp1_counterfactual_submit_safety_action"
                ),
                "counterfactual_risks": _split_csv_values(
                    fields.get("rising_missed_tp1_counterfactual_submit_safety_risks")
                ),
                **_tp1_counterfactual_decision_context(fields),
                "entry_price": entry_price,
                "entry_price_source": entry_price_source,
                "entry_executable_best_bid": entry_executable_bid,
                "entry_executable_best_ask": entry_executable_ask,
                "entry_executable_bbo_state": (
                    "pass"
                    if entry_executable_bid is not None
                    and entry_executable_ask is not None
                    else "source_gap_missing_or_invalid"
                ),
                "gross_first_hit_label": label,
                "first_hit_ts": first_hit_ts,
                "first_hit_move_pct": (
                    round(first_hit_move_pct, 4)
                    if first_hit_move_pct is not None
                    else None
                ),
                "first_hit_price_source": first_hit_price_source,
                "max_move_pct_within_20m": (
                    round(max_move_pct, 4) if max_move_pct is not None else None
                ),
                "min_move_pct_within_20m": (
                    round(min_move_pct, 4) if min_move_pct is not None else None
                ),
                "observed_price_event_count": observed_event_count,
                "post_block_horizon_measurements": multi_horizon.get(
                    "horizon_measurements"
                )
                or [],
                "post_block_late_recovery_after_adverse": multi_horizon.get(
                    "late_recovery_after_adverse"
                )
                or {},
                "gross_target_pct": TP1_GROSS_TARGET_PCT,
                "adverse_stop_pct": TP1_ADVERSE_STOP_PCT,
                "horizon_sec": TP1_LABEL_HORIZON_SEC,
                "decision_authority": "source_only_tp1_counterfactual_outcome_label",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "forbidden_uses": FORBIDDEN_USES,
            }
        )
    counts = Counter(
        str(item.get("gross_first_hit_label") or "unknown") for item in labels
    )
    return {
        "rising_missed_tp1_counterfactual_labeled_count": len(labels),
        "rising_missed_tp1_counterfactual_gross_label_counts": [
            {"gross_first_hit_label": key, "count": value}
            for key, value in counts.most_common()
        ],
        "rising_missed_tp1_counterfactual_gross_target_first_count": counts.get(
            "gross_target_first", 0
        ),
        "rising_missed_tp1_counterfactual_adverse_stop_first_count": counts.get(
            "adverse_stop_first", 0
        ),
    }, labels


def _tp1_counterfactual_direct_target_first_attribution(
    labels: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Keep the directly executable upside cohort attributable and source-only.

    The general TP1 detail table is payload bounded.  A small direct-target
    attribution table prevents later consumers from mistaking that export cap
    for the complete missed-opportunity population.  Complete counts remain in
    the summary while the compact detail table is independently payload bounded.
    """

    target_label_candidates = [
        row
        for row in labels
        if row.get("gross_first_hit_label") == "gross_target_first"
        and row.get("entry_executable_bbo_state") == "pass"
        and str(row.get("entry_price_source") or "").endswith(":best_ask")
        and row.get("first_hit_ts") not in (None, "", "-")
    ]
    eligible = [
        row
        for row in target_label_candidates
        if str(row.get("first_hit_price_source") or "").endswith(":best_bid")
        and row.get("effective_venue") in {"KRX", "NXT", "PREMARKET_KRX_LIKE"}
        and str(row.get("market_session_bucket") or "").strip() not in {"", "unknown"}
    ]
    selector_counts = Counter(
        str(row.get("selector_reason") or "unknown") for row in eligible
    )
    ai_action_counts = Counter(
        str(row.get("ai_action") or "unknown") for row in eligible
    )
    venue_session_counts = Counter(
        (
            str(row.get("effective_venue") or "unknown"),
            str(row.get("market_session_bucket") or "unknown"),
        )
        for row in eligible
    )
    compact_rows = [
        {
            "record_id": row.get("record_id"),
            "evaluation_id": row.get("evaluation_id"),
            "candidate_ts": row.get("candidate_ts"),
            "stock_code": row.get("stock_code"),
            "stock_name": row.get("stock_name"),
            "effective_venue": row.get("effective_venue"),
            "market_session_bucket": row.get("market_session_bucket"),
            "selector_reason": row.get("selector_reason"),
            "ai_action": row.get("ai_action"),
            "counterfactual_action": row.get("counterfactual_action"),
            "entry_price": row.get("entry_price"),
            "entry_price_source": row.get("entry_price_source"),
            "first_hit_ts": row.get("first_hit_ts"),
            "first_hit_move_pct": row.get("first_hit_move_pct"),
            "first_hit_price_source": row.get("first_hit_price_source"),
            "decision_authority": ("source_only_tp1_direct_target_first_attribution"),
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "forbidden_uses": FORBIDDEN_USES,
        }
        for row in eligible
    ]
    return {
        "rising_missed_tp1_counterfactual_direct_target_first_count": len(eligible),
        "rising_missed_tp1_counterfactual_direct_target_first_source_quality_gap_count": (
            len(target_label_candidates) - len(eligible)
        ),
        "rising_missed_tp1_counterfactual_direct_target_first_unique_symbol_count": len(
            {
                str(row.get("stock_code") or "")
                for row in eligible
                if row.get("stock_code")
            }
        ),
        "rising_missed_tp1_counterfactual_direct_target_first_selector_counts": [
            {"selector_reason": key, "count": value}
            for key, value in selector_counts.most_common()
        ],
        "rising_missed_tp1_counterfactual_direct_target_first_ai_action_counts": [
            {"ai_action": key, "count": value}
            for key, value in ai_action_counts.most_common()
        ],
        "rising_missed_tp1_counterfactual_direct_target_first_venue_session_counts": [
            {
                "effective_venue": venue,
                "market_session_bucket": session,
                "count": count,
            }
            for (venue, session), count in sorted(venue_session_counts.items())
        ],
        "rising_missed_tp1_counterfactual_direct_target_first_row_export_count": min(
            len(compact_rows), TP1_DETAIL_ROW_EXPORT_LIMIT
        ),
        "rising_missed_tp1_counterfactual_direct_target_first_row_omitted_count": max(
            0, len(compact_rows) - TP1_DETAIL_ROW_EXPORT_LIMIT
        ),
        "rising_missed_tp1_counterfactual_direct_target_first_row_export_truncated": (
            len(compact_rows) > TP1_DETAIL_ROW_EXPORT_LIMIT
        ),
    }, compact_rows


def _aggregate_nxt_post_block_outcomes(
    sampler_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for item in sampler_rows:
        if item.get("stage") != "rising_missed_nxt_post_block_price_sampler_completed":
            continue
        if item.get("source_quality_state") != "pass":
            continue
        stage = str(item.get("source_block_stage") or "missing").strip()
        reason = str(item.get("source_block_reason") or "missing").strip()
        grouped.setdefault((stage, reason), []).append(item)

    rows: list[dict[str, Any]] = []
    for (stage, reason), items in grouped.items():
        outcomes = Counter(
            str(item.get("outcome_label") or "unknown") for item in items
        )
        mfe_values = [
            float(value)
            for item in items
            for value in [item.get("mfe_after_block_pct")]
            if value is not None
        ]
        mae_values = [
            float(value)
            for item in items
            for value in [item.get("mae_after_block_pct")]
            if value is not None
        ]
        sample_count = len(items)
        target_count = outcomes.get("gross_target_first", 0)
        adverse_count = outcomes.get("adverse_stop_first", 0)
        rows.append(
            {
                "source_block_stage": stage,
                "source_block_reason": reason,
                "completed_sample_count": sample_count,
                "unique_symbol_count": len(
                    {
                        str(item.get("stock_code") or "")
                        for item in items
                        if str(item.get("stock_code") or "")
                    }
                ),
                "gross_target_first_count": target_count,
                "adverse_stop_first_count": adverse_count,
                "no_hit_within_20m_count": outcomes.get("no_hit_within_20m", 0),
                "gross_target_first_rate_pct": round(
                    target_count * 100.0 / sample_count, 6
                ),
                "adverse_stop_first_rate_pct": round(
                    adverse_count * 100.0 / sample_count, 6
                ),
                "equal_weight_avg_mfe_after_block_pct": (
                    round(sum(mfe_values) / len(mfe_values), 6) if mfe_values else None
                ),
                "equal_weight_avg_mae_after_block_pct": (
                    round(sum(mae_values) / len(mae_values), 6) if mae_values else None
                ),
                "max_mfe_after_block_pct": max(mfe_values) if mfe_values else None,
                "min_mae_after_block_pct": min(mae_values) if mae_values else None,
                "metric_role": "source_quality_gated_blocker_outcome_attribution",
                "decision_authority": "source_only_no_runtime_mutation",
                "window_policy": "same_day_nxt_completed_20m_post_block_sampler",
                "sample_floor": (
                    "10_source_quality_pass_completed_samplers_per_blocker"
                ),
                "sample_floor_met": sample_count >= 10,
                "primary_decision_metric": (
                    "gross_target_first_rate_pct_and_adverse_stop_first_rate_pct"
                ),
                "source_quality_gate": (
                    "completed_sampler_source_quality_pass_and_explicit_nxt_venue"
                ),
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "forbidden_uses": FORBIDDEN_USES,
            }
        )
    return sorted(
        rows,
        key=lambda item: (
            -int(item["gross_target_first_count"]),
            -float(item["max_mfe_after_block_pct"] or 0.0),
            str(item["source_block_stage"]),
            str(item["source_block_reason"]),
        ),
    )


def _clean_baseline_rolling_nxt_post_block_outcomes(
    target_date: str,
    current_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Aggregate recent source-quality-gated blocker outcomes since baseline.

    The daily report remains the owner of same-day samples.  This view only
    combines already-gated daily summaries and never grants runtime authority.
    The target-date artifact is deliberately excluded from disk so a stale
    partial report cannot be counted alongside the current in-memory result.
    """

    source_rows: list[tuple[str, dict[str, Any]]] = [
        (target_date, dict(row)) for row in current_rows
    ]
    source_dates = {target_date}
    excluded_reports: list[dict[str, str]] = []
    prefix = "rising_missed_intraday_feedback_"
    eligible_paths = []
    for path in sorted(REPORT_DIR.glob(f"{prefix}*.json")):
        report_date = path.stem.removeprefix(prefix)
        if not (CLEAN_BASELINE_DATE <= report_date < target_date):
            continue
        eligible_paths.append(path)
    prior_limit = max(0, NXT_POST_BLOCK_ROLLING_REPORT_DAYS - 1)
    for path in eligible_paths[-prior_limit:] if prior_limit else []:
        report_date = path.stem.removeprefix(prefix)
        try:
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError):
            excluded_reports.append(
                {"target_date": report_date, "reason": "report_unreadable"}
            )
            continue
        if not isinstance(payload, dict) or (
            payload.get("report_type") != "rising_missed_intraday_feedback"
            or payload.get("target_date") != report_date
            or bool(payload.get("runtime_effect"))
            or bool(payload.get("allowed_runtime_apply"))
        ):
            excluded_reports.append(
                {"target_date": report_date, "reason": "report_contract_invalid"}
            )
            continue
        daily_rows = (payload.get("summary") or {}).get(
            "rising_missed_nxt_post_block_blocker_outcome_attribution"
        )
        if not isinstance(daily_rows, list):
            excluded_reports.append(
                {"target_date": report_date, "reason": "daily_attribution_missing"}
            )
            continue
        source_dates.add(report_date)
        source_rows.extend(
            (report_date, dict(row)) for row in daily_rows if isinstance(row, dict)
        )

    grouped: dict[tuple[str, str], list[tuple[str, dict[str, Any]]]] = {}
    for report_date, row in source_rows:
        stage = str(row.get("source_block_stage") or "missing").strip()
        reason = str(row.get("source_block_reason") or "missing").strip()
        grouped.setdefault((stage, reason), []).append((report_date, row))

    rolling_rows: list[dict[str, Any]] = []
    for (stage, reason), dated_rows in grouped.items():
        sample_count = sum(
            _safe_int(row.get("completed_sample_count")) for _, row in dated_rows
        )
        if sample_count <= 0:
            continue
        target_count = sum(
            _safe_int(row.get("gross_target_first_count")) for _, row in dated_rows
        )
        adverse_count = sum(
            _safe_int(row.get("adverse_stop_first_count")) for _, row in dated_rows
        )
        no_hit_count = sum(
            _safe_int(row.get("no_hit_within_20m_count")) for _, row in dated_rows
        )

        def _weighted_average(
            rows: list[tuple[str, dict[str, Any]]], field: str
        ) -> float | None:
            weighted_sum = 0.0
            weight = 0
            for _, row in rows:
                value = _safe_float(row.get(field))
                row_count = _safe_int(row.get("completed_sample_count"))
                if value is None or row_count <= 0:
                    continue
                weighted_sum += value * row_count
                weight += row_count
            return round(weighted_sum / weight, 6) if weight else None

        avg_mfe = _weighted_average(
            dated_rows, "equal_weight_avg_mfe_after_block_pct"
        )
        avg_mae = _weighted_average(
            dated_rows, "equal_weight_avg_mae_after_block_pct"
        )
        gross_first_hit_payoff_proxy_pct = round(
            (target_count * TP1_GROSS_TARGET_PCT + adverse_count * TP1_ADVERSE_STOP_PCT)
            / sample_count,
            6,
        )
        sample_floor_met = sample_count >= 10
        rolling_assessment = "hold_sample"
        if sample_floor_met:
            rolling_assessment = (
                "source_only_positive_payoff_proxy_needs_cost_adjusted_ev"
                if gross_first_hit_payoff_proxy_pct > 0.0
                and avg_mfe is not None
                and avg_mae is not None
                and avg_mfe > abs(avg_mae)
                else "hold_no_edge"
            )
        max_mfe_values = [
            value
            for _, row in dated_rows
            for value in [_safe_float(row.get("max_mfe_after_block_pct"))]
            if value is not None
        ]
        min_mae_values = [
            value
            for _, row in dated_rows
            for value in [_safe_float(row.get("min_mae_after_block_pct"))]
            if value is not None
        ]
        row_source_dates = sorted({report_date for report_date, _ in dated_rows})
        rolling_rows.append(
            {
                "source_block_stage": stage,
                "source_block_reason": reason,
                "completed_sample_count": sample_count,
                "daily_unique_symbol_count_sum": sum(
                    _safe_int(row.get("unique_symbol_count")) for _, row in dated_rows
                ),
                "gross_target_first_count": target_count,
                "adverse_stop_first_count": adverse_count,
                "no_hit_within_20m_count": no_hit_count,
                "gross_target_first_rate_pct": round(
                    target_count * 100.0 / sample_count, 6
                ),
                "adverse_stop_first_rate_pct": round(
                    adverse_count * 100.0 / sample_count, 6
                ),
                "equal_weight_avg_mfe_after_block_pct": avg_mfe,
                "equal_weight_avg_mae_after_block_pct": avg_mae,
                "gross_first_hit_payoff_proxy_pct": (gross_first_hit_payoff_proxy_pct),
                "net_ev_state": "unavailable_fee_tax_and_no_hit_exit_outcome_missing",
                "max_mfe_after_block_pct": (
                    max(max_mfe_values) if max_mfe_values else None
                ),
                "min_mae_after_block_pct": (
                    min(min_mae_values) if min_mae_values else None
                ),
                "rolling_assessment": rolling_assessment,
                "metric_role": "source_quality_gated_blocker_outcome_attribution",
                "decision_authority": "source_only_no_runtime_mutation",
                "window_policy": "clean_baseline_rolling_latest_20_report_artifacts",
                "clean_tuning_baseline_date": CLEAN_BASELINE_DATE,
                "source_dates": row_source_dates,
                "source_date_count": len(row_source_dates),
                "sample_floor": (
                    "10_source_quality_pass_completed_samplers_per_blocker"
                ),
                "sample_floor_met": sample_floor_met,
                "primary_decision_metric": (
                    "gross_target_first_rate_pct_and_adverse_stop_first_rate_pct_"
                    "with_gross_first_hit_payoff_proxy_and_equal_weight_mfe_mae"
                ),
                "source_quality_gate": (
                    "daily_completed_sampler_source_quality_pass_and_explicit_nxt_venue"
                ),
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "forbidden_uses": FORBIDDEN_USES,
            }
        )
    rolling_rows.sort(
        key=lambda row: (
            str(row.get("rolling_assessment")),
            -_safe_int(row.get("completed_sample_count")),
            str(row.get("source_block_stage")),
            str(row.get("source_block_reason")),
        )
    )
    return rolling_rows, {
        "window_policy": "clean_baseline_rolling_latest_20_report_artifacts",
        "clean_tuning_baseline_date": CLEAN_BASELINE_DATE,
        "rolling_report_day_limit": NXT_POST_BLOCK_ROLLING_REPORT_DAYS,
        "start_date": min(source_dates) if source_dates else target_date,
        "end_date": target_date,
        "source_dates": sorted(source_dates),
        "source_date_count": len(source_dates),
        "excluded_report_count": len(excluded_reports),
        "excluded_reports": excluded_reports,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }


def _build_nxt_session_observation(
    pipeline_path: Path,
) -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    evaluation_rows: list[dict[str, Any]] = []
    order_rows: list[dict[str, Any]] = []
    sampler_rows: list[dict[str, Any]] = []
    seen_evaluations: set[tuple[str, ...]] = set()
    session_counts: Counter[str] = Counter()
    micro_state_counts: Counter[str] = Counter()
    route_counts: Counter[str] = Counter()
    effective_venue_counts: Counter[str] = Counter()
    sampler_stage_counts: Counter[str] = Counter()
    sampler_source_block_stage_counts: Counter[str] = Counter()
    sampler_outcome_counts: Counter[str] = Counter()
    sampler_evaluations: set[str] = set()
    unique_symbols: set[str] = set()
    for row in iter_jsonl(pipeline_path):
        fields = _fields(row)
        stage = str(row.get("stage") or "")
        evaluation_id = str(fields.get("rising_missed_tp1_evaluation_id") or "").strip()
        session_bucket = str(
            fields.get("rising_missed_market_session_bucket") or "missing"
        ).strip()
        effective_venue = _tp1_effective_venue(fields)
        is_exact_nxt_cohort = bool(
            session_bucket == "nxt_entry_window" and effective_venue == "NXT"
        )
        if evaluation_id and is_exact_nxt_cohort:
            key = ("evaluation_id", evaluation_id)
            if key not in seen_evaluations:
                seen_evaluations.add(key)
                code = _event_code(row)
                if code:
                    unique_symbols.add(code)
                micro_state = str(
                    fields.get("rising_missed_nxt_micro_state") or "missing"
                ).strip()
                route_0b = str(
                    fields.get("rising_missed_ws_0b_route") or "unknown"
                ).strip()
                route_0d = str(
                    fields.get("rising_missed_ws_0d_route") or "unknown"
                ).strip()
                session_counts[session_bucket] += 1
                micro_state_counts[micro_state] += 1
                route_counts[f"0B:{route_0b}"] += 1
                route_counts[f"0D:{route_0d}"] += 1
                effective_venue_counts[effective_venue] += 1
                evaluation_rows.append(
                    {
                        "ts": _event_ts(row),
                        "stock_code": code,
                        "stock_name": _event_name(row),
                        "record_id": row.get("record_id"),
                        "evaluation_id": evaluation_id,
                        "stage": stage,
                        "market_session_bucket": session_bucket,
                        "market_session_state": fields.get(
                            "rising_missed_market_session_state"
                        ),
                        "effective_venue": effective_venue,
                        "nxt_eligible": fields.get("rising_missed_nxt_eligible"),
                        "nxt_flag_source": fields.get("rising_missed_nxt_flag_source"),
                        "ws_0b_route": route_0b,
                        "ws_0d_route": route_0d,
                        "ws_0b_age_ms": _safe_float(
                            fields.get("rising_missed_ws_0b_age_ms")
                        ),
                        "ws_0d_age_ms": _safe_float(
                            fields.get("rising_missed_ws_0d_age_ms")
                        ),
                        "nxt_micro_state": micro_state,
                        "input_ready": _boolish(
                            fields.get("rising_missed_tp1_input_ready")
                        ),
                        "effective_price_source": fields.get(
                            "market_data_effective_price_source"
                        ),
                        "candidate_allowed": _optional_boolish(
                            fields.get("rising_missed_tp1_candidate_allowed")
                        ),
                        "candidate_reason": fields.get(
                            "rising_missed_tp1_candidate_reason"
                        ),
                        "nxt_price_jump_recovery_configured": _boolish(
                            fields.get(
                                "rising_missed_tp1_nxt_price_jump_recovery_configured"
                            )
                        ),
                        "nxt_price_jump_recovery_active": _boolish(
                            fields.get(
                                "rising_missed_tp1_nxt_price_jump_recovery_enabled"
                            )
                        ),
                        "nxt_price_jump_recovery_active_date": fields.get(
                            "rising_missed_tp1_nxt_price_jump_recovery_active_date"
                        ),
                        "nxt_price_jump_recovery_current_date": fields.get(
                            "rising_missed_tp1_nxt_price_jump_recovery_current_date"
                        ),
                        "nxt_price_jump_recovery_runtime_called": _boolish(
                            fields.get(
                                "rising_missed_tp1_nxt_price_jump_recovery_runtime_called"
                            )
                        ),
                        "nxt_price_jump_recovery_runtime_applied": _boolish(
                            fields.get(
                                "rising_missed_tp1_nxt_price_jump_recovery_runtime_applied"
                            )
                        ),
                        "nxt_price_jump_recovery_runtime_call_reason": fields.get(
                            "rising_missed_tp1_nxt_price_jump_recovery_runtime_call_reason"
                        ),
                        "decision_authority": "observe_only_no_runtime_mutation",
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                        "forbidden_uses": FORBIDDEN_USES,
                    }
                )
        if stage == "order_leg_request" and evaluation_id and is_exact_nxt_cohort:
            order_rows.append(
                {
                    "ts": _event_ts(row),
                    "stock_code": _event_code(row),
                    "stock_name": _event_name(row),
                    "record_id": row.get("record_id"),
                    "evaluation_id": evaluation_id,
                    "market_session_bucket": session_bucket,
                    "effective_venue": fields.get("rising_missed_effective_venue"),
                    "requested_order_type": fields.get("requested_order_type"),
                    "effective_order_type": fields.get("effective_order_type"),
                    "effective_dmst_stex_tp": fields.get("effective_dmst_stex_tp"),
                    "order_type_remapped": _boolish(fields.get("order_type_remapped")),
                    "order_type_remap_reason": fields.get("order_type_remap_reason"),
                    "decision_authority": "execution_quality_observation_only",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "forbidden_uses": FORBIDDEN_USES,
                }
            )
        if stage.startswith("rising_missed_nxt_post_block_") and is_exact_nxt_cohort:
            if evaluation_id:
                sampler_evaluations.add(evaluation_id)
            sampler_stage_counts[stage] += 1
            source_block_stage = str(
                fields.get("rising_missed_nxt_post_block_source_block_stage")
                or "tp1_selector"
            ).strip()
            if stage == "rising_missed_nxt_post_block_sampler_registered":
                sampler_source_block_stage_counts[source_block_stage] += 1
            outcome_label = str(
                fields.get("rising_missed_nxt_post_block_sampler_outcome_label") or ""
            ).strip()
            if outcome_label:
                sampler_outcome_counts[outcome_label] += 1
            sampler_rows.append(
                {
                    "ts": _event_ts(row),
                    "stock_code": _event_code(row),
                    "stock_name": _event_name(row),
                    "record_id": row.get("record_id"),
                    "evaluation_id": evaluation_id,
                    "stage": stage,
                    "market_session_bucket": session_bucket,
                    "effective_venue": fields.get("rising_missed_effective_venue"),
                    "selector_reason": fields.get(
                        "rising_missed_nxt_post_block_selector_reason"
                    ),
                    "selector_deferred": _boolish(
                        fields.get("rising_missed_nxt_post_block_selector_deferred")
                    ),
                    "source_block_stage": source_block_stage,
                    "source_block_reason": fields.get(
                        "rising_missed_nxt_post_block_source_block_reason"
                    ),
                    "entry_price_source": fields.get(
                        "rising_missed_nxt_post_block_entry_price_source"
                    ),
                    "counterfactual_requires_executable_bbo": _boolish(
                        fields.get(
                            "rising_missed_nxt_post_block_counterfactual_requires_executable_bbo"
                        )
                    ),
                    "entry_executable_best_bid": _safe_float(
                        fields.get(
                            "rising_missed_nxt_post_block_entry_executable_best_bid"
                        )
                    ),
                    "entry_executable_best_ask": _safe_float(
                        fields.get(
                            "rising_missed_nxt_post_block_entry_executable_best_ask"
                        )
                    ),
                    "entry_executable_bbo_source": fields.get(
                        "rising_missed_nxt_post_block_entry_executable_bbo_source"
                    ),
                    "sampler_runtime_configured": _boolish(
                        fields.get(
                            "rising_missed_nxt_post_block_sampler_runtime_configured"
                        )
                    ),
                    "sampler_runtime_active_date": fields.get(
                        "rising_missed_nxt_post_block_sampler_runtime_active_date"
                    ),
                    "sampler_runtime_current_date": fields.get(
                        "rising_missed_nxt_post_block_sampler_runtime_current_date"
                    ),
                    "sampler_runtime_active": _boolish(
                        fields.get(
                            "rising_missed_nxt_post_block_sampler_runtime_active"
                        )
                    ),
                    "sampler_runtime_called": _boolish(
                        fields.get(
                            "rising_missed_nxt_post_block_sampler_runtime_called"
                        )
                    ),
                    "sampler_runtime_applied": _boolish(
                        fields.get(
                            "rising_missed_nxt_post_block_sampler_runtime_applied"
                        )
                    ),
                    "rest_fallback_runtime_configured": _boolish(
                        fields.get(
                            "rising_missed_nxt_post_block_rest_fallback_runtime_configured"
                        )
                    ),
                    "rest_fallback_runtime_active_date": fields.get(
                        "rising_missed_nxt_post_block_rest_fallback_runtime_active_date"
                    ),
                    "rest_fallback_runtime_current_date": fields.get(
                        "rising_missed_nxt_post_block_rest_fallback_runtime_current_date"
                    ),
                    "rest_fallback_runtime_active": _boolish(
                        fields.get(
                            "rising_missed_nxt_post_block_rest_fallback_runtime_active"
                        )
                    ),
                    "rest_fallback_runtime_called": _boolish(
                        fields.get(
                            "rising_missed_nxt_post_block_rest_fallback_runtime_called"
                        )
                    ),
                    "rest_fallback_runtime_call_reason": fields.get(
                        "rising_missed_nxt_post_block_rest_fallback_runtime_call_reason"
                    ),
                    "source_block_actual_order_submitted": _boolish(
                        fields.get(
                            "rising_missed_nxt_post_block_source_block_actual_order_submitted"
                        )
                    ),
                    "source_block_broker_order_forbidden": _boolish(
                        fields.get(
                            "rising_missed_nxt_post_block_source_block_broker_order_forbidden"
                        )
                    ),
                    "source_block_requested_qty": _safe_int(
                        fields.get(
                            "rising_missed_nxt_post_block_source_block_requested_qty"
                        )
                    ),
                    "source_block_filled_qty": _safe_int(
                        fields.get(
                            "rising_missed_nxt_post_block_source_block_filled_qty"
                        )
                    ),
                    "source_block_residual_submitted_qty": _safe_int(
                        fields.get(
                            "rising_missed_nxt_post_block_source_block_residual_submitted_qty"
                        )
                    ),
                    "source_block_residual_submitted_leg_count": _safe_int(
                        fields.get(
                            "rising_missed_nxt_post_block_source_block_residual_submitted_leg_count"
                        )
                    ),
                    "rest_fallback_enabled": _boolish(
                        fields.get("rising_missed_nxt_post_block_rest_fallback_enabled")
                    ),
                    "rest_fallback_attempted": _boolish(
                        fields.get(
                            "rising_missed_nxt_post_block_rest_fallback_attempted"
                        )
                    ),
                    "rest_fallback_applied": _boolish(
                        fields.get("rising_missed_nxt_post_block_rest_fallback_applied")
                    ),
                    "rest_fallback_reason": fields.get(
                        "rising_missed_nxt_post_block_rest_fallback_reason"
                    ),
                    "rest_fetch_state": fields.get(
                        "rising_missed_nxt_post_block_rest_fetch_state"
                    ),
                    "observation_state": fields.get(
                        "rising_missed_nxt_post_block_price_observation_state"
                    ),
                    "price_source": fields.get(
                        "rising_missed_nxt_post_block_price_source"
                    ),
                    "price_source_reason": fields.get(
                        "rising_missed_nxt_post_block_price_source_reason"
                    ),
                    "price_fallback_from_reason": fields.get(
                        "rising_missed_nxt_post_block_price_fallback_from_reason"
                    ),
                    "price_basis": fields.get(
                        "rising_missed_nxt_post_block_price_basis"
                    ),
                    "current_price_observed": _safe_float(
                        fields.get("current_price_observed")
                    ),
                    "ws_0b_age_ms": _safe_float(
                        fields.get("rising_missed_nxt_post_block_ws_0b_age_ms")
                    ),
                    "ws_0b_item": fields.get("rising_missed_nxt_post_block_ws_0b_item"),
                    "ws_0b_route": fields.get(
                        "rising_missed_nxt_post_block_ws_0b_route"
                    ),
                    "ws_0d_age_ms": _safe_float(
                        fields.get("rising_missed_nxt_post_block_ws_0d_age_ms")
                    ),
                    "ws_0d_item": fields.get("rising_missed_nxt_post_block_ws_0d_item"),
                    "ws_0d_route": fields.get(
                        "rising_missed_nxt_post_block_ws_0d_route"
                    ),
                    "ws_0d_best_bid": _safe_int(
                        fields.get("rising_missed_nxt_post_block_ws_0d_best_bid")
                    ),
                    "ws_0d_best_ask": _safe_int(
                        fields.get("rising_missed_nxt_post_block_ws_0d_best_ask")
                    ),
                    "ws_0d_quote_proxy_applied": _boolish(
                        fields.get(
                            "rising_missed_nxt_post_block_ws_0d_quote_proxy_applied"
                        )
                    ),
                    "fresh_sample": _boolish(
                        fields.get("rising_missed_nxt_post_block_fresh_sample")
                    ),
                    "sample_attempt_count": _safe_int(
                        fields.get("rising_missed_nxt_post_block_sample_attempt_count")
                    ),
                    "fresh_sample_count": _safe_int(
                        fields.get("rising_missed_nxt_post_block_fresh_sample_count")
                    ),
                    "trade_price_sample_count": _safe_int(
                        fields.get(
                            "rising_missed_nxt_post_block_trade_price_sample_count"
                        )
                    ),
                    "quote_proxy_sample_count": _safe_int(
                        fields.get(
                            "rising_missed_nxt_post_block_quote_proxy_sample_count"
                        )
                    ),
                    "source_gap_sample_count": _safe_int(
                        fields.get(
                            "rising_missed_nxt_post_block_source_gap_sample_count"
                        )
                    ),
                    "move_pct": _safe_float(
                        fields.get("rising_missed_nxt_post_block_move_pct")
                    ),
                    "first_hit_move_pct": _safe_float(
                        fields.get("rising_missed_nxt_post_block_first_hit_move_pct")
                    ),
                    "first_hit_price_source": fields.get(
                        "rising_missed_nxt_post_block_first_hit_price_source"
                    ),
                    "first_hit_price_basis": fields.get(
                        "rising_missed_nxt_post_block_first_hit_price_basis"
                    ),
                    "mfe_after_block_pct": _safe_float(
                        fields.get("rising_missed_nxt_post_block_max_move_pct")
                    ),
                    "mae_after_block_pct": _safe_float(
                        fields.get("rising_missed_nxt_post_block_min_move_pct")
                    ),
                    "outcome_label": outcome_label or None,
                    "source_quality_state": fields.get(
                        "rising_missed_nxt_post_block_sampler_source_quality_state"
                    ),
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "decision_authority": "source_only_nxt_post_block_price_observation",
                    "forbidden_uses": FORBIDDEN_USES,
                }
            )
    blocker_outcome_rows = _aggregate_nxt_post_block_outcomes(sampler_rows)
    return (
        {
            "rising_missed_nxt_evaluation_count": len(evaluation_rows),
            "rising_missed_nxt_unique_symbol_count": len(unique_symbols),
            "rising_missed_nxt_session_bucket_counts": [
                {"market_session_bucket": key, "count": value}
                for key, value in session_counts.most_common()
            ],
            "rising_missed_nxt_micro_state_counts": [
                {"nxt_micro_state": key, "count": value}
                for key, value in micro_state_counts.most_common()
            ],
            "rising_missed_nxt_ws_route_counts": [
                {"ws_type_route": key, "count": value}
                for key, value in route_counts.most_common()
            ],
            "rising_missed_nxt_effective_venue_counts": [
                {"effective_venue": key, "count": value}
                for key, value in effective_venue_counts.most_common()
            ],
            "rising_missed_nxt_input_ready_count": sum(
                1 for item in evaluation_rows if item.get("input_ready")
            ),
            "rising_missed_nxt_rest_quote_selected_count": sum(
                1
                for item in evaluation_rows
                if item.get("effective_price_source") == "ka10004_rest_orderbook"
            ),
            "rising_missed_nxt_order_request_count": len(order_rows),
            "rising_missed_nxt_order_type_remap_count": sum(
                1 for item in order_rows if item.get("order_type_remapped")
            ),
            "rising_missed_nxt_post_block_sampler_evaluation_count": len(
                sampler_evaluations
            ),
            "rising_missed_nxt_post_block_sampler_stage_counts": [
                {"stage": key, "count": value}
                for key, value in sampler_stage_counts.most_common()
            ],
            "rising_missed_nxt_post_block_source_block_stage_counts": [
                {"source_block_stage": key, "count": value}
                for key, value in sampler_source_block_stage_counts.most_common()
            ],
            "rising_missed_nxt_post_block_source_block_order_submitted_count": sum(
                1
                for item in sampler_rows
                if item.get("stage")
                == "rising_missed_nxt_post_block_sampler_registered"
                and item.get("source_block_actual_order_submitted")
            ),
            "rising_missed_nxt_post_block_source_block_residual_submitted_qty": sum(
                _safe_int(item.get("source_block_residual_submitted_qty"))
                for item in sampler_rows
                if item.get("stage")
                == "rising_missed_nxt_post_block_sampler_registered"
            ),
            "rising_missed_nxt_post_block_sampler_registered_count": sampler_stage_counts.get(
                "rising_missed_nxt_post_block_sampler_registered", 0
            ),
            "rising_missed_nxt_post_block_sampler_runtime_called_count": sum(
                1
                for evaluation_id in {
                    str(item.get("evaluation_id") or "")
                    for item in sampler_rows
                    if item.get("sampler_runtime_called")
                    and str(item.get("evaluation_id") or "")
                }
            ),
            "rising_missed_nxt_post_block_sampler_runtime_applied_count": sum(
                1
                for evaluation_id in {
                    str(item.get("evaluation_id") or "")
                    for item in sampler_rows
                    if item.get("sampler_runtime_applied")
                    and str(item.get("evaluation_id") or "")
                }
            ),
            "rising_missed_nxt_post_block_rest_fallback_runtime_called_count": sum(
                1 for item in sampler_rows if item.get("rest_fallback_runtime_called")
            ),
            "rising_missed_nxt_price_jump_recovery_runtime_called_count": sum(
                1
                for item in evaluation_rows
                if item.get("nxt_price_jump_recovery_runtime_called")
            ),
            "rising_missed_nxt_price_jump_recovery_runtime_applied_count": sum(
                1
                for item in evaluation_rows
                if item.get("nxt_price_jump_recovery_runtime_applied")
            ),
            "rising_missed_nxt_post_block_sampler_registration_skipped_count": (
                sampler_stage_counts.get(
                    "rising_missed_nxt_post_block_sampler_registration_skipped", 0
                )
            ),
            "rising_missed_nxt_post_block_price_sample_count": sampler_stage_counts.get(
                "rising_missed_nxt_post_block_price_sample", 0
            ),
            "rising_missed_nxt_post_block_fresh_price_sample_count": sum(
                1
                for item in sampler_rows
                if item.get("stage") == "rising_missed_nxt_post_block_price_sample"
                and item.get("fresh_sample")
            ),
            "rising_missed_nxt_post_block_source_gap_sample_count": sum(
                1
                for item in sampler_rows
                if item.get("stage") == "rising_missed_nxt_post_block_price_sample"
                and not item.get("fresh_sample")
            ),
            "rising_missed_nxt_post_block_trade_price_sample_count": sum(
                1
                for item in sampler_rows
                if item.get("stage") == "rising_missed_nxt_post_block_price_sample"
                and item.get("price_source") == "trusted_ws_0b_nxt"
            ),
            "rising_missed_nxt_post_block_quote_proxy_sample_count": sum(
                1
                for item in sampler_rows
                if item.get("stage") == "rising_missed_nxt_post_block_price_sample"
                and item.get("price_source") == "trusted_ws_0d_nxt_executable_bid_proxy"
            ),
            "rising_missed_nxt_post_block_rest_fallback_attempted_count": sum(
                1
                for item in sampler_rows
                if item.get("stage") == "rising_missed_nxt_post_block_price_sample"
                and item.get("rest_fallback_attempted")
            ),
            "rising_missed_nxt_post_block_rest_fallback_applied_count": sum(
                1
                for item in sampler_rows
                if item.get("stage") == "rising_missed_nxt_post_block_price_sample"
                and item.get("rest_fallback_applied")
            ),
            "rising_missed_nxt_post_block_rest_budget_deferred_count": sum(
                1
                for item in sampler_rows
                if item.get("stage") == "rising_missed_nxt_post_block_price_sample"
                and item.get("rest_fallback_reason")
                == "observation_rest_budget_deferred"
            ),
            "rising_missed_nxt_post_block_sampler_completed_count": sampler_stage_counts.get(
                "rising_missed_nxt_post_block_price_sampler_completed", 0
            ),
            "rising_missed_nxt_post_block_sampler_outcome_counts": [
                {"outcome_label": key, "count": value}
                for key, value in sampler_outcome_counts.most_common()
            ],
            "rising_missed_nxt_post_block_blocker_outcome_attribution": (
                blocker_outcome_rows
            ),
        },
        evaluation_rows,
        order_rows,
        sampler_rows,
    )


def _build_adverse_micro_recovery_observation(
    pipeline_path: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Keep KRX adverse-micro recovery checkpoints separate from NXT sampling."""

    stage_counts: Counter[str] = Counter()
    checkpoint_counts: Counter[str] = Counter()
    source_quality_counts: Counter[str] = Counter()
    outcome_counts: Counter[str] = Counter()
    rows: list[dict[str, Any]] = []
    registered_observation_ids: set[str] = set()
    for event in iter_jsonl(pipeline_path):
        stage = str(event.get("stage") or "")
        if not stage.startswith("rising_missed_adverse_micro_recovery_"):
            continue
        fields = _fields(event)
        if str(fields.get("effective_venue") or "").upper() != "KRX":
            continue
        observation_id = str(
            fields.get("rising_missed_adverse_micro_recovery_observation_id") or ""
        )
        stage_counts[stage] += 1
        source_reason = str(
            fields.get("rising_missed_adverse_micro_recovery_source_reason") or "-"
        )
        if stage.endswith("checkpoint"):
            source_quality_counts[source_reason] += 1
            checkpoint = str(
                fields.get("rising_missed_adverse_micro_recovery_checkpoint_sec")
                or "unknown"
            )
            checkpoint_counts[checkpoint] += 1
        if stage.endswith("registered") and observation_id:
            registered_observation_ids.add(observation_id)
        if stage.endswith("completed"):
            outcome = str(
                fields.get("rising_missed_adverse_micro_recovery_outcome") or "unknown"
            )
            outcome_counts[outcome] += 1
        rows.append(
            {
                "ts": _event_ts(event),
                "stock_code": _event_code(event),
                "stock_name": _event_name(event),
                "observation_id": observation_id or "-",
                "source_tp1_evaluation_id": fields.get(
                    "rising_missed_adverse_micro_recovery_source_tp1_evaluation_id",
                    "-",
                ),
                "stage": stage,
                "checkpoint_sec": fields.get(
                    "rising_missed_adverse_micro_recovery_checkpoint_sec", "-"
                ),
                "price_fresh": _boolish(
                    fields.get("rising_missed_adverse_micro_recovery_price_fresh")
                ),
                "move_pct": _safe_float(
                    fields.get("rising_missed_adverse_micro_recovery_move_pct")
                ),
                "max_move_pct": _safe_float(
                    fields.get("rising_missed_adverse_micro_recovery_max_move_pct")
                ),
                "min_move_pct": _safe_float(
                    fields.get("rising_missed_adverse_micro_recovery_min_move_pct")
                ),
                "next_scanner_loop_rechecked": _boolish(
                    fields.get(
                        "rising_missed_adverse_micro_recovery_next_scanner_loop_rechecked"
                    )
                ),
                "reentry_candidate_allowed": _boolish(
                    fields.get(
                        "rising_missed_adverse_micro_recovery_reentry_candidate_allowed"
                    )
                ),
                "recovery_observed": _boolish(
                    fields.get("rising_missed_adverse_micro_recovery_detected")
                ),
                "source_reason": source_reason,
                "raw_0b_route": fields.get(
                    "rising_missed_adverse_micro_recovery_ws_0b_raw_route", "-"
                ),
                "outcome": fields.get(
                    "rising_missed_adverse_micro_recovery_outcome", "-"
                ),
            }
        )
    return {
        "rising_missed_adverse_micro_recovery_observation_count": len(
            registered_observation_ids
        ),
        "rising_missed_adverse_micro_recovery_stage_counts": [
            {"stage": stage, "count": count}
            for stage, count in stage_counts.most_common()
        ],
        "rising_missed_adverse_micro_recovery_checkpoint_counts": [
            {"checkpoint_sec": checkpoint, "count": count}
            for checkpoint, count in sorted(checkpoint_counts.items())
        ],
        "rising_missed_adverse_micro_recovery_source_quality_counts": [
            {"source_reason": reason, "count": count}
            for reason, count in source_quality_counts.most_common()
        ],
        "rising_missed_adverse_micro_recovery_outcome_counts": [
            {"outcome": outcome, "count": count}
            for outcome, count in outcome_counts.most_common()
        ],
    }, rows


def _risky_micro_source_category(source_stage: str) -> str:
    stage = str(source_stage or "").lower()
    if "scanner" in stage or ("candidate" in stage and "tp1" not in stage):
        return "scanner_candidate"
    if "tp1" in stage:
        return "tp1"
    if "entry_ai" in stage or "ai_authority" in stage:
        return "entry_ai"
    if "latency" in stage:
        return "latency"
    if "liquidity" in stage or "micro" in stage:
        return "liquidity_micro"
    if "tick_speed" in stage:
        return "tick_speed"
    if "entry_price" in stage or "price_canary" in stage:
        return "entry_price"
    return "other"


def _first_risky_micro_float(fields: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        value = _safe_float(fields.get(key))
        if value is not None:
            return value
    return None


def _first_risky_micro_text(fields: dict[str, Any], *keys: str) -> str:
    """Return the first meaningful producer token without masking fallbacks.

    Older TP1 rows often carry ``"missing"`` in the direct source field while
    preserving the real diagnosis in the WS or submit-context source field.
    Treating that placeholder as authoritative erased the actual gap owner in
    the postclose adapter.
    """

    placeholders = {"", "-", "missing", "none", "null", "not_evaluated"}
    for key in keys:
        value = str(fields.get(key) or "").strip()
        if value.lower() not in placeholders:
            return value
    return ""


def _risky_micro_tp1_tick_diagnostics(fields: dict[str, Any]) -> dict[str, Any]:
    """Preserve same-event TP1 tick source quality without synthetic backfill."""

    sample_count = _first_risky_micro_float(
        fields,
        "rising_missed_tp1_submit_context_tick_window_sample_count",
        "rising_missed_tp1_tick_window_sample_count",
        "rising_missed_tp1_ws_tick_window_sample_count",
    )
    age_sec = _first_risky_micro_float(
        fields,
        "rising_missed_tp1_submit_context_tick_acceleration_age_sec",
        "rising_missed_tp1_tick_acceleration_age_sec",
        "rising_missed_tp1_ws_tick_acceleration_age_sec",
    )
    source = _first_risky_micro_text(
        fields,
        "rising_missed_tp1_submit_context_tick_acceleration_source",
        "rising_missed_tp1_tick_acceleration_source",
        "rising_missed_tp1_ws_tick_acceleration_source",
        "tick_context_source",
    )
    fresh = any(
        _boolish(fields.get(key))
        for key in (
            "rising_missed_tp1_tick_acceleration_fresh",
            "rising_missed_tp1_submit_context_tick_acceleration_fresh",
            "rising_missed_tp1_ws_tick_acceleration_fresh",
        )
    )
    gap_reason = "none"
    if not fresh:
        if (
            sample_count is not None and sample_count < 10
        ) or "insufficient_10tick_window" in source.lower():
            gap_reason = "tp1_signed_tick_sample_floor_not_met"
        elif source != "trusted_ws_signed_0b_10tick_received_ts":
            gap_reason = "tp1_tick_source_untrusted_or_missing"
        elif age_sec is None:
            gap_reason = "tp1_tick_context_age_missing"
        elif age_sec > 3.0:
            gap_reason = "tp1_tick_context_stale"
        else:
            gap_reason = "tp1_submit_context_freshness_unconfirmed"
    return {
        "fresh": fresh,
        "gap_reason": gap_reason,
        "sample_count": (int(sample_count) if sample_count is not None else "-"),
        "age_sec": round(age_sec, 6) if age_sec is not None else "-",
        "source": source or "-",
    }


def _risky_micro_quote_age_ms(fields: dict[str, Any]) -> float | None:
    return _first_risky_micro_float(
        fields,
        "market_data_effective_quote_age_ms",
        "quote_age_at_submit_ms",
        "quote_age_ms",
        "ws_age_ms",
        "pre_submit_effective_quote_age_ms",
        "entry_ai_price_ws_snapshot_refresh_age_ms",
        "orderbook_micro_observer_last_quote_age_ms",
        "observed_mark_gap_fresh_quote_age_ms",
        "risky_micro_episode_quote_age_ms",
    )


def _risky_micro_has_rising_missed_lineage(row: dict[str, Any]) -> bool:
    fields = _fields(row)
    stage = str(row.get("stage") or "")
    return bool(
        _is_forced_rising_missed(row)
        or _boolish(fields.get("rising_missed_entry_lineage"))
        or (
            stage.startswith("rising_missed_")
            and bool(fields.get("rising_missed_tp1_evaluation_id"))
        )
    )


def _risky_micro_projection_from_block_event(
    row: dict[str, Any],
) -> dict[str, Any] | None:
    """Project an existing rising-missed blocker into source-only research.

    This adapter intentionally runs only in the report consumer.  It does not
    add an entry owner, retry a blocked order, or mutate the live pipeline.
    """

    stage = str(row.get("stage") or "")
    source_category = RISKY_MICRO_DERIVED_SOURCE_STAGES.get(stage)
    if source_category is None or not _risky_micro_has_rising_missed_lineage(row):
        return None
    fields = _fields(row)
    bid, ask, bbo_source = _event_executable_bbo(row)
    quote_age_ms = _risky_micro_quote_age_ms(fields)
    tick_acceleration_ratio = _first_risky_micro_float(
        fields,
        "rising_missed_tp1_tick_acceleration",
        "rising_missed_tp1_submit_context_tick_acceleration",
        "rising_missed_tp1_ws_tick_acceleration",
        "rising_missed_tick_acceleration_ratio",
        "tick_acceleration_ratio",
    )
    tick_window_span_sec = _first_risky_micro_float(
        fields,
        "rising_missed_tp1_ws_momentum_window_span_sec",
        "rising_missed_tp1_submit_context_tick_window_span_sec",
        "rising_missed_tick_window_span_sec",
        "tick_window_span_sec",
    )
    tp1_tick_diagnostics = _risky_micro_tp1_tick_diagnostics(fields)
    if source_category == "tp1" and not tp1_tick_diagnostics["fresh"]:
        tick_acceleration_ratio = None
        tick_window_span_sec = None
    elif source_category == "tp1" and (
        tick_acceleration_ratio is None or tick_window_span_sec is None
    ):
        if tick_acceleration_ratio is None and tick_window_span_sec is None:
            tp1_tick_diagnostics["gap_reason"] = (
                "tick_acceleration_and_window_span_missing"
            )
        elif tick_acceleration_ratio is None:
            tp1_tick_diagnostics["gap_reason"] = "tick_acceleration_missing"
        else:
            tp1_tick_diagnostics["gap_reason"] = "tick_window_span_missing"
    tick_context_source = (
        str(tp1_tick_diagnostics["source"])
        if source_category == "tp1"
        else _first_risky_micro_text(fields, "tick_context_source") or "missing"
    )
    true_ofi = _first_risky_micro_float(
        fields,
        "rising_missed_tp1_true_ofi_ewma",
        "rising_missed_tp1_submit_context_true_ofi_ewma",
        "rising_missed_micro_estimator_true_ofi_ewma",
        "orderbook_micro_ofi_norm",
    )
    depth_ratio = _first_risky_micro_float(
        fields,
        "rising_missed_tp1_top_depth_ratio",
        "rising_missed_tp1_submit_context_top_depth_ratio",
    )
    quote_imbalance = _first_risky_micro_float(fields, "orderbook_micro_qi")
    support_count = _first_risky_micro_float(
        fields,
        "rising_missed_tp1_positive_support_count",
        "rising_missed_tp1_submit_context_support_count",
    )
    orderbook_state = str(fields.get("orderbook_micro_state") or "").lower()
    hard_negative_reasons = (
        str(fields.get("rising_missed_tp1_hard_negative_reasons") or "").strip().lower()
    )
    large_sell_detected = any(
        _boolish(fields.get(key))
        for key in (
            "large_sell_print_detected",
            "signed_tape_sell_dominated",
            "market_data_signed_tape_sell_dominated",
        )
    )
    adverse_micro_detected = bool(
        large_sell_detected
        or hard_negative_reasons not in {"", "-", "none", "not_applicable"}
        or orderbook_state in {"bearish", "strong_bearish"}
        or (
            true_ofi is not None
            and true_ofi < 0.0
            and (
                (depth_ratio is not None and depth_ratio < 0.5)
                or (quote_imbalance is not None and quote_imbalance < 0.25)
            )
        )
    )
    positive_micro_support = bool(
        not adverse_micro_detected
        and (
            (support_count is not None and support_count >= 2.0)
            or orderbook_state in {"bullish", "strong_bullish"}
            or (
                true_ofi is not None
                and true_ofi > 0.0
                and depth_ratio is not None
                and depth_ratio >= 1.0
            )
            or (
                true_ofi is not None
                and true_ofi > 0.0
                and quote_imbalance is not None
                and quote_imbalance >= 0.5
            )
        )
    )
    source_block_reason = str(
        fields.get("block_reason")
        or fields.get("reason")
        or fields.get("rising_missed_tp1_candidate_reason")
        or fields.get("entry_ai_submit_authority_reason")
        or stage
    )
    projected = evaluate_risky_micro_episode(
        rising_missed_lineage=True,
        source_stage=f"{source_category}:{stage}",
        source_block_reason=source_block_reason,
        best_bid=int(bid or 0),
        best_ask=int(ask or 0),
        quote_age_ms=quote_age_ms,
        tick_acceleration_ratio=tick_acceleration_ratio,
        tick_window_span_sec=tick_window_span_sec,
        tick_context_gap_reason=(
            str(tp1_tick_diagnostics["gap_reason"])
            if source_category == "tp1"
            else None
        ),
        positive_micro_support=positive_micro_support,
        adverse_micro_detected=adverse_micro_detected,
        large_sell_detected=large_sell_detected,
    )
    projected.update(
        {
            "effective_venue": (
                fields.get("rising_missed_effective_venue")
                or fields.get("effective_venue")
                or fields.get("venue")
                or "unknown"
            ),
            "market_session_bucket": (
                fields.get("rising_missed_market_session_bucket")
                or fields.get("market_session_bucket")
                or "unknown"
            ),
            "risky_micro_episode_source_event_stage": stage,
            "risky_micro_episode_source_category": source_category,
            "risky_micro_episode_source_projection_origin": (
                "postclose_existing_block_event_adapter"
            ),
            "risky_micro_episode_source_bbo_provenance": bbo_source,
            "risky_micro_episode_tick_context_source": tick_context_source,
            "risky_micro_episode_tick_context_tp1_sample_count": (
                tp1_tick_diagnostics["sample_count"]
                if source_category == "tp1"
                else "-"
            ),
            "risky_micro_episode_tick_context_tp1_age_sec": (
                tp1_tick_diagnostics["age_sec"] if source_category == "tp1" else "-"
            ),
            "risky_micro_episode_tick_context_tp1_source": (
                tp1_tick_diagnostics["source"] if source_category == "tp1" else "-"
            ),
            "risky_micro_episode_source_observation_id": str(
                fields.get("rising_missed_tp1_evaluation_id")
                or fields.get("entry_price_ai_decision_trace_id")
                or f"{stage}:{_event_ts(row)}"
            ),
        }
    )
    return projected


def _risky_micro_ts(value: Any) -> datetime | None:
    """Normalize source timestamps before executable-path comparisons."""

    parsed = _parse_ts(value)
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=KST)
    return parsed.astimezone(KST)


def _risky_micro_venue_session(fields: dict[str, Any]) -> tuple[str, str]:
    venue = (
        str(
            fields.get("rising_missed_effective_venue")
            or fields.get("effective_venue")
            or fields.get("venue")
            or "unknown"
        )
        .strip()
        .upper()
    )
    session = (
        str(
            fields.get("rising_missed_market_session_bucket")
            or fields.get("market_session_bucket")
            or "unknown"
        )
        .strip()
        .upper()
    )
    return venue, session


def _risky_micro_fresh_executable_bbo(
    row: dict[str, Any],
) -> tuple[float | None, float | None, str]:
    fields = _fields(row)
    bid, ask, source = _event_executable_bbo(row)
    quote_age_ms = _risky_micro_quote_age_ms(fields)
    if bid is None or ask is None:
        bid = _safe_float(fields.get("risky_micro_episode_best_bid"))
        ask = _safe_float(fields.get("risky_micro_episode_best_ask"))
        quote_age_ms = _safe_float(fields.get("risky_micro_episode_quote_age_ms"))
        source = "risky_micro_candidate_bbo"
    if (
        bid is None
        or ask is None
        or bid <= 0
        or ask < bid
        or quote_age_ms is None
        or quote_age_ms < 0
        or quote_age_ms > RISKY_MICRO_MAX_QUOTE_AGE_MS
    ):
        return None, None, "missing_stale_or_invalid_executable_bbo"
    return bid, ask, source


def _risky_micro_horizon_measurement(
    observations: list[dict[str, Any]],
    *,
    fill_ts: datetime,
    fill_price: float,
    horizon_sec: int,
    total_cost_bps: float,
) -> dict[str, Any]:
    target_ts = fill_ts + timedelta(seconds=horizon_sec)
    endpoint = next(
        (item for item in observations if item["ts"] >= target_ts),
        None,
    )
    if endpoint is None:
        return {
            "horizon_sec": horizon_sec,
            "complete": False,
            "reason": "endpoint_missing",
        }
    endpoint_lag_sec = (endpoint["ts"] - target_ts).total_seconds()
    if endpoint_lag_sec > RISKY_MICRO_MAX_ENDPOINT_LAG_SEC:
        return {
            "horizon_sec": horizon_sec,
            "complete": False,
            "reason": "endpoint_lag_exceeded",
            "endpoint_lag_sec": round(endpoint_lag_sec, 6),
        }
    path = [item for item in observations if fill_ts <= item["ts"] <= endpoint["ts"]]
    path_times = [fill_ts, *(item["ts"] for item in path)]
    max_gap_sec = max(
        (
            (right - left).total_seconds()
            for left, right in zip(path_times, path_times[1:], strict=False)
        ),
        default=0.0,
    )
    if max_gap_sec > RISKY_MICRO_MAX_INTERNAL_GAP_SEC:
        return {
            "horizon_sec": horizon_sec,
            "complete": False,
            "reason": "internal_gap_exceeded",
            "max_internal_gap_sec": round(max_gap_sec, 6),
        }
    bids = [float(item["bid"]) for item in path]
    terminal_bps = ((float(endpoint["bid"]) / fill_price) - 1.0) * 10_000.0
    return {
        "horizon_sec": horizon_sec,
        "complete": True,
        "endpoint_ts": endpoint["ts"].isoformat(),
        "endpoint_lag_sec": round(endpoint_lag_sec, 6),
        "max_internal_gap_sec": round(max_gap_sec, 6),
        "observation_count": len(path),
        "terminal_return_bps": round(terminal_bps, 6),
        "cost_adjusted_terminal_return_bps": round(
            terminal_bps - total_cost_bps,
            6,
        ),
        "mfe_bps": round(((max(bids) / fill_price) - 1.0) * 10_000.0, 6),
        "mae_bps": round(((min(bids) / fill_price) - 1.0) * 10_000.0, 6),
        "price_basis": "fresh_executable_bid",
    }


def _join_risky_micro_entry_profile_outcome(
    candidate: dict[str, Any],
    observations: list[dict[str, Any]],
    *,
    entry_profile: str,
    entry_price_override: float | None,
    ttl_sec: int,
    profile_eligible: bool,
    profile_eligibility_reason: str,
    promotion_ev_included: bool,
) -> dict[str, Any]:
    candidate_ts = _risky_micro_ts(candidate.get("ts"))
    entry_price = entry_price_override
    gross_target_bps = _safe_float(candidate.get("gross_target_bps")) or 0.0
    adverse_limit_bps = (
        _safe_float(candidate.get("adverse_limit_bps")) or gross_target_bps
    )
    total_cost_bps = _safe_float(candidate.get("conservative_total_cost_bps")) or 0.0
    ttl_sec = max(1, ttl_sec)
    max_hold_sec = max(1, _safe_int(candidate.get("max_hold_sec")))
    is_bid_plus_one_profile = entry_profile.startswith("bid_plus_one_ttl_")
    target_price = (
        _safe_float(candidate.get("hypothetical_target_price"))
        if is_bid_plus_one_profile
        else None
    )
    adverse_price = (
        _safe_float(candidate.get("hypothetical_adverse_price"))
        if is_bid_plus_one_profile
        else None
    )
    if target_price is None and entry_price is not None and gross_target_bps > 0:
        target_price = entry_price * (1.0 + gross_target_bps / 10_000.0)
    if adverse_price is None and entry_price is not None and adverse_limit_bps > 0:
        adverse_price = entry_price * (1.0 - adverse_limit_bps / 10_000.0)
    candidate_status = str(candidate.get("status") or "unknown")
    if candidate_status == "source_only_candidate":
        evaluation_role = "promotion_ev_source_candidate"
    elif candidate_status == "recheck_required":
        evaluation_role = "diagnostic_recheck_cohort"
    else:
        evaluation_role = "excluded_or_source_quality_control"
    base = {
        "metric_role": "source_only_counterfactual_outcome",
        "decision_authority": "source_only_no_runtime_apply",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "fill_feasible": None,
        "fill_price": None,
        "exit_price": None,
        "net_return_bps": None,
        "outcome_join_consumer": "fresh_executable_bbo_entry_profile_v2",
        "candidate_status": candidate_status,
        "policy_version": str(candidate.get("policy_version") or "unknown"),
        "entry_profile": entry_profile,
        "entry_profile_ttl_sec": ttl_sec,
        "entry_profile_eligible": profile_eligible,
        "entry_profile_eligibility_reason": profile_eligibility_reason,
        "entry_profile_promotion_ev_included": bool(promotion_ev_included),
        "entry_profile_entry_price": entry_price,
        "entry_profile_target_price": target_price,
        "entry_profile_adverse_price": adverse_price,
        "outcome_evaluation_role": evaluation_role,
        "fill_price_basis": (
            "passive_limit_conservative_ask_touch"
            if is_bid_plus_one_profile
            else "bounded_candidate_executable_ask_touch"
        ),
        "exit_price_basis": "fresh_executable_bid",
        "adverse_price_basis": (
            "event_hypothetical_adverse_price"
            if is_bid_plus_one_profile
            and _safe_float(candidate.get("hypothetical_adverse_price")) is not None
            else "entry_profile_adverse_limit_bps"
        ),
    }
    if not profile_eligible:
        return {
            **base,
            "outcome_join_status": "diagnostic_profile_not_applicable",
        }
    if candidate.get("status") == "source_quality_blocked":
        return {**base, "outcome_join_status": "source_quality_blocked"}
    if (
        candidate_ts is None
        or entry_price is None
        or entry_price <= 0
        or target_price is None
        or target_price <= entry_price
        or adverse_price is None
        or adverse_price >= entry_price
        or total_cost_bps <= 0
    ):
        return {**base, "outcome_join_status": "source_quality_blocked_input_missing"}
    candidate_venue = str(candidate.get("effective_venue") or "UNKNOWN").upper()
    candidate_session = str(candidate.get("market_session_bucket") or "UNKNOWN").upper()
    if candidate_venue == "UNKNOWN" or candidate_session == "UNKNOWN":
        return {
            **base,
            "outcome_join_status": "source_quality_blocked_venue_or_session_missing",
        }
    matching = [
        item
        for item in observations
        if item["ts"] >= candidate_ts
        and item["venue"] == candidate_venue
        and item["session"] == candidate_session
    ]
    ttl_end = candidate_ts + timedelta(seconds=ttl_sec)
    fill = next(
        (
            item
            for item in matching
            if item["ts"] <= ttl_end and float(item["ask"]) <= entry_price
        ),
        None,
    )
    if fill is None:
        matching_watermark = max(
            (item["ts"] for item in matching),
            default=None,
        )
        matured = bool(matching_watermark and matching_watermark >= ttl_end)
        return {
            **base,
            "outcome_join_status": (
                "resolved_not_filled" if matured else "pending_fill_horizon"
            ),
            "fill_feasible": False if matured else None,
            "passive_ttl_end": ttl_end.isoformat(),
            "matching_fresh_bbo_observation_count": len(matching),
            "matching_fresh_bbo_watermark": (
                matching_watermark.isoformat() if matching_watermark else None
            ),
            "net_return_bps": 0.0 if matured else None,
        }
    fill_ts = fill["ts"]
    path = [item for item in matching if item["ts"] >= fill_ts]
    hold_end = fill_ts + timedelta(seconds=max_hold_sec)
    target_hit = next(
        (
            item
            for item in path
            if item["ts"] <= hold_end and float(item["bid"]) >= float(target_price or 0)
        ),
        None,
    )
    adverse_hit = next(
        (
            item
            for item in path
            if item["ts"] <= hold_end
            and adverse_price is not None
            and float(item["bid"]) <= adverse_price
        ),
        None,
    )
    first_hit = None
    outcome = "pending_timeout_horizon"
    if target_hit is not None and (
        adverse_hit is None or target_hit["ts"] <= adverse_hit["ts"]
    ):
        first_hit = target_hit
        outcome = "resolved_target_first"
    elif adverse_hit is not None:
        first_hit = adverse_hit
        outcome = "resolved_adverse_first"
    timeout_endpoint = next((item for item in path if item["ts"] >= hold_end), None)
    if first_hit is None and timeout_endpoint is not None:
        if (
            timeout_endpoint["ts"] - hold_end
        ).total_seconds() <= RISKY_MICRO_MAX_ENDPOINT_LAG_SEC:
            first_hit = timeout_endpoint
            outcome = "resolved_timeout"
    exit_price = None
    if first_hit is not None:
        exit_price = (
            float(target_price)
            if outcome == "resolved_target_first" and target_price is not None
            else float(first_hit["bid"])
        )
    net_return_bps = (
        ((exit_price / entry_price) - 1.0) * 10_000.0 - total_cost_bps
        if exit_price is not None
        else None
    )
    return {
        **base,
        "outcome_join_status": outcome,
        "fill_feasible": True,
        "fill_ts": fill_ts.isoformat(),
        "fill_price": entry_price,
        "fill_touch_ask": fill["ask"],
        "fill_bbo_source": fill["source"],
        "first_hit_ts": first_hit["ts"].isoformat() if first_hit else None,
        "exit_price": exit_price,
        "net_return_bps": (
            round(net_return_bps, 6) if net_return_bps is not None else None
        ),
        "horizons": [
            _risky_micro_horizon_measurement(
                path,
                fill_ts=fill_ts,
                fill_price=entry_price,
                horizon_sec=horizon,
                total_cost_bps=total_cost_bps,
            )
            for horizon in RISKY_MICRO_HORIZONS_SEC
        ],
    }


def _join_risky_micro_executable_outcome(
    candidate: dict[str, Any],
    observations: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compare bounded source-only entry profiles for one candidate.

    Only the canonical bid+1/3-second profile can enter promotion EV.  Longer
    TTLs and the narrow-spread ask profile are paired diagnostics, so a single
    episode cannot gain promotion weight by being represented four times.
    """

    passive_entry = _safe_float(candidate.get("hypothetical_entry_price"))
    best_ask = _safe_float(candidate.get("best_ask"))
    spread_bps = _safe_float(candidate.get("spread_bps"))
    profiles: list[dict[str, Any]] = []
    for ttl_sec in RISKY_MICRO_ENTRY_PROFILE_TTLS_SEC:
        profile_name = f"bid_plus_one_ttl_{ttl_sec}s"
        profiles.append(
            _join_risky_micro_entry_profile_outcome(
                candidate,
                observations,
                entry_profile=profile_name,
                entry_price_override=passive_entry,
                ttl_sec=ttl_sec,
                profile_eligible=True,
                profile_eligibility_reason="passive_bid_plus_one_profile",
                promotion_ev_included=(
                    profile_name == RISKY_MICRO_PRIMARY_ENTRY_PROFILE
                    and candidate.get("status") == "source_only_candidate"
                ),
            )
        )
    ask_eligible = bool(
        best_ask is not None
        and best_ask > 0
        and spread_bps is not None
        and spread_bps <= RISKY_MICRO_LIMITED_ASK_MAX_SPREAD_BPS
    )
    profiles.append(
        _join_risky_micro_entry_profile_outcome(
            candidate,
            observations,
            entry_profile="limited_ask_ttl_3s_spread_le_15bps",
            entry_price_override=best_ask,
            ttl_sec=3,
            profile_eligible=ask_eligible,
            profile_eligibility_reason=(
                "candidate_spread_le_15bps"
                if ask_eligible
                else "candidate_spread_missing_or_above_15bps"
            ),
            promotion_ev_included=False,
        )
    )
    primary = next(
        item
        for item in profiles
        if item.get("entry_profile") == RISKY_MICRO_PRIMARY_ENTRY_PROFILE
    )
    return {
        **primary,
        "entry_profile_outcomes": profiles,
        "entry_profile_comparison_authority": (
            "source_only_paired_counterfactual_no_runtime_apply"
        ),
    }


def _build_risky_micro_episode_source_candidates(
    pipeline_path: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Summarize and join source-only passive episodes without live authority."""

    status_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    source_stage_counts: Counter[str] = Counter()
    source_category_counts: Counter[str] = Counter()
    instrumentation_gap_counts: Counter[str] = Counter()
    tick_context_gap_reason_counts: Counter[str] = Counter()
    unique_symbols: set[str] = set()
    seen: set[tuple[str, str, str, str, str]] = set()
    rows: list[dict[str, Any]] = []
    for row in iter_jsonl(pipeline_path):
        event_stage = str(row.get("stage") or "")
        explicit_candidate = (
            event_stage == "risky_micro_episode_source_candidate_observed"
        )
        projected_fields = (
            None
            if explicit_candidate
            else _risky_micro_projection_from_block_event(row)
        )
        if not explicit_candidate and projected_fields is None:
            continue
        fields = _fields(row) if explicit_candidate else projected_fields
        assert isinstance(fields, dict)
        code = _event_code(row)
        status = str(fields.get("risky_micro_episode_status") or "unknown")
        reason = str(fields.get("risky_micro_episode_reason") or "unknown")
        source_stage = str(fields.get("risky_micro_episode_source_stage") or "unknown")
        source_observation_id = str(
            fields.get("risky_micro_episode_source_observation_id")
            or ("explicit_daily_stage_status" if explicit_candidate else _event_ts(row))
        )
        dedupe_key = (
            str(row.get("record_id") or ""),
            code,
            source_stage,
            status,
            source_observation_id,
        )
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        venue, session = _risky_micro_venue_session(fields)
        if code:
            unique_symbols.add(code)
        status_counts[status] += 1
        reason_counts[reason] += 1
        source_stage_counts[source_stage] += 1
        source_category_counts[_risky_micro_source_category(source_stage)] += 1
        instrumentation_gap = fields.get("risky_micro_episode_instrumentation_gap")
        if not instrumentation_gap:
            if reason == "executable_bbo_missing_or_invalid":
                instrumentation_gap = "executable_bbo_missing"
            elif reason == "executable_quote_stale_or_age_missing":
                instrumentation_gap = (
                    "quote_age_missing"
                    if _risky_micro_quote_age_ms(fields) is None
                    else "stale_quote"
                )
            elif reason == "tick_context_missing":
                instrumentation_gap = "tick_context_missing"
            else:
                instrumentation_gap = "none"
        instrumentation_gap = str(instrumentation_gap)
        tick_context_gap_reason = str(
            fields.get("risky_micro_episode_tick_context_gap_reason")
            or (
                "tick_acceleration_and_window_span_missing"
                if instrumentation_gap == "tick_context_missing"
                else "none"
            )
        )
        if tick_context_gap_reason not in RISKY_MICRO_TICK_CONTEXT_GAP_REASONS:
            tick_context_gap_reason = "unclassified_tick_context_gap"
        candidate_quote_age_ms = _risky_micro_quote_age_ms(fields)
        instrumentation_gap_counts[instrumentation_gap] += 1
        if instrumentation_gap == "tick_context_missing":
            tick_context_gap_reason_counts[tick_context_gap_reason] += 1
        rows.append(
            {
                "ts": _event_ts(row),
                "record_id": row.get("record_id"),
                "stock_code": code,
                "stock_name": _event_name(row),
                "effective_venue": venue,
                "market_session_bucket": session,
                "status": status,
                "reason": reason,
                "policy_version": str(
                    fields.get("risky_micro_episode_policy_version") or "unknown"
                ),
                "entry_profile": str(
                    fields.get("risky_micro_episode_entry_profile")
                    or "legacy_unspecified"
                ),
                "instrumentation_gap": instrumentation_gap,
                "bbo_state": fields.get(
                    "risky_micro_episode_bbo_state",
                    (
                        "valid"
                        if _safe_int(fields.get("risky_micro_episode_best_bid")) > 0
                        and _safe_int(fields.get("risky_micro_episode_best_ask"))
                        >= _safe_int(fields.get("risky_micro_episode_best_bid"))
                        else "missing_or_invalid"
                    ),
                ),
                "quote_age_ms": (
                    candidate_quote_age_ms
                    if candidate_quote_age_ms is not None
                    else "-"
                ),
                "quote_freshness_state": fields.get(
                    "risky_micro_episode_quote_freshness_state",
                    (
                        "missing"
                        if candidate_quote_age_ms is None
                        else (
                            "fresh"
                            if 0
                            <= float(candidate_quote_age_ms)
                            <= RISKY_MICRO_MAX_QUOTE_AGE_MS
                            else "stale"
                        )
                    ),
                ),
                "tick_context_state": fields.get(
                    "risky_micro_episode_tick_context_state",
                    (
                        "present"
                        if _safe_float(
                            fields.get("risky_micro_episode_tick_acceleration_ratio")
                        )
                        is not None
                        and _safe_float(
                            fields.get("risky_micro_episode_tick_window_span_sec")
                        )
                        is not None
                        else "missing"
                    ),
                ),
                "tick_context_gap_reason": tick_context_gap_reason,
                "tick_context_tp1_sample_count": fields.get(
                    "risky_micro_episode_tick_context_tp1_sample_count", "-"
                ),
                "tick_context_tp1_age_sec": fields.get(
                    "risky_micro_episode_tick_context_tp1_age_sec", "-"
                ),
                "tick_context_tp1_source": fields.get(
                    "risky_micro_episode_tick_context_tp1_source", "-"
                ),
                "source_stage": source_stage,
                "source_category": fields.get(
                    "risky_micro_episode_source_category",
                    _risky_micro_source_category(source_stage),
                ),
                "source_event_stage": fields.get(
                    "risky_micro_episode_source_event_stage", event_stage
                ),
                "source_projection_origin": fields.get(
                    "risky_micro_episode_source_projection_origin",
                    "runtime_explicit_candidate_event",
                ),
                "source_observation_id": source_observation_id,
                "source_bbo_provenance": fields.get(
                    "risky_micro_episode_source_bbo_provenance", "runtime_event_payload"
                ),
                "source_block_reason": fields.get(
                    "risky_micro_episode_source_block_reason", "-"
                ),
                "best_bid": _safe_int(fields.get("risky_micro_episode_best_bid")),
                "best_ask": _safe_int(fields.get("risky_micro_episode_best_ask")),
                "spread_bps": fields.get("risky_micro_episode_spread_bps", "-"),
                "tick_acceleration_ratio": fields.get(
                    "risky_micro_episode_tick_acceleration_ratio", "-"
                ),
                "tick_window_span_sec": fields.get(
                    "risky_micro_episode_tick_window_span_sec", "-"
                ),
                "tick_context_source": fields.get(
                    "risky_micro_episode_tick_context_source", "unknown"
                ),
                "positive_micro_support": _boolish(
                    fields.get("risky_micro_episode_positive_micro_support")
                ),
                "adverse_micro_detected": _boolish(
                    fields.get("risky_micro_episode_adverse_micro_detected")
                ),
                "large_sell_detected": _boolish(
                    fields.get("risky_micro_episode_large_sell_detected")
                ),
                "hypothetical_entry_price": _safe_int(
                    fields.get("risky_micro_episode_hypothetical_entry_price")
                ),
                "hypothetical_target_price": _safe_int(
                    fields.get("risky_micro_episode_hypothetical_target_price")
                ),
                "hypothetical_adverse_price": _safe_int(
                    fields.get("risky_micro_episode_hypothetical_adverse_price")
                ),
                "gross_target_bps": _safe_int(
                    fields.get("risky_micro_episode_gross_target_bps")
                ),
                "adverse_limit_bps": _safe_int(
                    fields.get("risky_micro_episode_adverse_limit_bps")
                ),
                "conservative_total_cost_bps": _safe_int(
                    fields.get("risky_micro_episode_conservative_total_cost_bps")
                ),
                "passive_ttl_sec": _safe_int(
                    fields.get("risky_micro_episode_passive_ttl_sec")
                ),
                "max_hold_sec": _safe_int(
                    fields.get("risky_micro_episode_max_hold_sec")
                ),
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "quantity_owner": fields.get(
                    "risky_micro_episode_quantity_owner",
                    "position_sizing_dynamic_formula_then_existing_probe_first",
                ),
                "quantity_is_tuning_axis": _boolish(
                    fields.get("risky_micro_episode_quantity_is_tuning_axis")
                ),
                "independent_episode_or_widget_owner": _boolish(
                    fields.get(
                        "risky_micro_episode_independent_episode_or_widget_owner"
                    )
                ),
                "outcome_join_required": _boolish(
                    fields.get("risky_micro_episode_outcome_join_required")
                ),
                "horizon_observer_registered": _boolish(
                    fields.get("risky_micro_episode_horizon_observer_registered")
                ),
                "horizon_observer_registration_status": str(
                    fields.get("risky_micro_episode_horizon_observer_status")
                    or "not_instrumented"
                ),
                "horizon_observer_registration_key": str(
                    fields.get("risky_micro_episode_horizon_observer_registration_key")
                    or "-"
                ),
            }
        )

    observations_by_code: dict[str, list[dict[str, Any]]] = {
        code: [] for code in unique_symbols
    }
    pipeline_watermark: datetime | None = None
    horizon_observer_event_count = 0
    horizon_observer_fresh_bbo_event_count = 0
    if observations_by_code:
        for row in iter_jsonl(pipeline_path):
            row_ts = _risky_micro_ts(_event_ts(row))
            if row_ts is not None and (
                pipeline_watermark is None or row_ts > pipeline_watermark
            ):
                pipeline_watermark = row_ts
            code = _event_code(row)
            if code not in observations_by_code:
                continue
            if str(row.get("stage") or "") == (
                "risky_micro_episode_executable_bbo_observed"
            ):
                horizon_observer_event_count += 1
                if _boolish(
                    _fields(row).get("risky_micro_episode_horizon_observer_quote_fresh")
                ):
                    horizon_observer_fresh_bbo_event_count += 1
            ts = row_ts
            if ts is None:
                continue
            bid, ask, source = _risky_micro_fresh_executable_bbo(row)
            if bid is None or ask is None:
                continue
            venue, session = _risky_micro_venue_session(_fields(row))
            observations_by_code[code].append(
                {
                    "ts": ts,
                    "bid": bid,
                    "ask": ask,
                    "source": source,
                    "venue": venue,
                    "session": session,
                }
            )
    outcome_counts: Counter[str] = Counter()
    resolved_eligible_net_bps: list[float] = []
    resolved_eligible_count = 0
    recheck_diagnostic_net_bps: list[float] = []
    recheck_diagnostic_resolved_count = 0
    matured_pending_gap_counts: Counter[str] = Counter()
    for candidate in rows:
        observations = sorted(
            observations_by_code.get(str(candidate.get("stock_code") or ""), []),
            key=lambda item: item["ts"],
        )
        outcome = _join_risky_micro_executable_outcome(
            candidate,
            observations,
        )
        candidate.update(outcome)
        outcome_status = str(outcome.get("outcome_join_status") or "unknown")
        maturity_deadline: datetime | None = None
        if outcome_status == "pending_fill_horizon":
            candidate_ts = _risky_micro_ts(str(candidate.get("ts") or ""))
            if candidate_ts is not None:
                maturity_deadline = candidate_ts + timedelta(
                    seconds=max(_safe_int(candidate.get("passive_ttl_sec")), 0)
                )
        elif outcome_status == "pending_timeout_horizon":
            fill_ts = _risky_micro_ts(str(outcome.get("fill_ts") or ""))
            if fill_ts is not None:
                maturity_deadline = fill_ts + timedelta(
                    seconds=max(_safe_int(candidate.get("max_hold_sec")), 0)
                )
        if (
            maturity_deadline is not None
            and pipeline_watermark is not None
            and pipeline_watermark >= maturity_deadline
        ):
            gap = (
                "fresh_bbo_fill_horizon_missing"
                if outcome_status == "pending_fill_horizon"
                else "fresh_bbo_exit_horizon_missing"
            )
            candidate.update(
                {
                    "outcome_instrumentation_gap": gap,
                    "outcome_instrumentation_gap_matured": True,
                    "outcome_maturity_deadline": maturity_deadline.isoformat(),
                    "outcome_pipeline_watermark": pipeline_watermark.isoformat(),
                }
            )
            matured_pending_gap_counts[gap] += 1
        outcome_counts[outcome_status] += 1
        if outcome.get(
            "outcome_evaluation_role"
        ) == "promotion_ev_source_candidate" and outcome_status.startswith("resolved_"):
            resolved_eligible_count += 1
            net_bps = _safe_float(outcome.get("net_return_bps"))
            if net_bps is not None:
                resolved_eligible_net_bps.append(net_bps)
        elif outcome.get(
            "outcome_evaluation_role"
        ) == "diagnostic_recheck_cohort" and outcome_status.startswith("resolved_"):
            recheck_diagnostic_resolved_count += 1
            net_bps = _safe_float(outcome.get("net_return_bps"))
            if net_bps is not None:
                recheck_diagnostic_net_bps.append(net_bps)

    observed_categories = {
        category for category in source_category_counts if category != "other"
    }
    unobserved_categories = [
        category
        for category in RISKY_MICRO_EXPECTED_SOURCE_CATEGORIES
        if category not in observed_categories
    ]
    daily_source_quality_adjusted_ev_pct = (
        round(sum(resolved_eligible_net_bps) / resolved_eligible_count / 100.0, 6)
        if resolved_eligible_count
        else None
    )
    instrumented_categories = {
        *RISKY_MICRO_DERIVED_SOURCE_STAGES.values(),
        "latency",
        "tick_speed",
    }
    projection_origin_counts = Counter(
        str(row.get("source_projection_origin") or "unknown") for row in rows
    )
    horizon_registration_status_counts = Counter(
        str(row.get("horizon_observer_registration_status") or "not_instrumented")
        for row in rows
        if str(row.get("source_projection_origin") or "")
        == "runtime_explicit_candidate_event"
    )
    return {
        "risky_micro_episode_observation_count": len(rows),
        "risky_micro_episode_unique_symbol_count": len(unique_symbols),
        "risky_micro_episode_status_counts": [
            {"status": key, "count": value}
            for key, value in status_counts.most_common()
        ],
        "risky_micro_episode_reason_counts": [
            {"reason": key, "count": value}
            for key, value in reason_counts.most_common()
        ],
        "risky_micro_episode_source_stage_counts": [
            {"source_stage": key, "count": value}
            for key, value in source_stage_counts.most_common()
        ],
        "risky_micro_episode_source_category_counts": [
            {"source_category": key, "count": value}
            for key, value in source_category_counts.most_common()
        ],
        "risky_micro_episode_expected_source_categories": list(
            RISKY_MICRO_EXPECTED_SOURCE_CATEGORIES
        ),
        "risky_micro_episode_unobserved_source_categories": unobserved_categories,
        "risky_micro_episode_source_coverage_complete": not unobserved_categories,
        "risky_micro_episode_natural_sample_absent_categories": (unobserved_categories),
        "risky_micro_episode_instrumented_source_categories": sorted(
            instrumented_categories
        ),
        "risky_micro_episode_source_instrumentation_complete": all(
            category in instrumented_categories
            for category in RISKY_MICRO_EXPECTED_SOURCE_CATEGORIES
        ),
        "risky_micro_episode_projection_origin_counts": [
            {"origin": key, "count": value}
            for key, value in projection_origin_counts.most_common()
        ],
        "risky_micro_episode_instrumentation_gap_counts": [
            {"gap": key, "count": value}
            for key, value in instrumentation_gap_counts.most_common()
        ],
        "risky_micro_episode_tick_context_missing_count": (
            instrumentation_gap_counts.get("tick_context_missing", 0)
        ),
        "risky_micro_episode_tick_context_gap_reason_counts": [
            {"reason": key, "count": value}
            for key, value in tick_context_gap_reason_counts.most_common()
        ],
        "risky_micro_episode_stale_quote_count": (
            instrumentation_gap_counts.get("stale_quote", 0)
        ),
        "risky_micro_episode_quote_age_missing_count": (
            instrumentation_gap_counts.get("quote_age_missing", 0)
        ),
        "risky_micro_episode_executable_bbo_missing_count": (
            instrumentation_gap_counts.get("executable_bbo_missing", 0)
        ),
        "risky_micro_episode_source_only_candidate_count": status_counts.get(
            "source_only_candidate", 0
        ),
        "risky_micro_episode_recheck_required_count": status_counts.get(
            "recheck_required", 0
        ),
        "risky_micro_episode_excessive_risk_excluded_count": status_counts.get(
            "excluded_excessive_risk", 0
        ),
        "risky_micro_episode_candidate_projection_ready": bool(rows),
        "risky_micro_episode_outcome_join_consumer_implemented": True,
        "risky_micro_episode_outcome_join_status_counts": [
            {"status": key, "count": value}
            for key, value in outcome_counts.most_common()
        ],
        "risky_micro_episode_matured_pending_outcome_gap_counts": [
            {"gap": key, "count": value}
            for key, value in matured_pending_gap_counts.most_common()
        ],
        "risky_micro_episode_matured_pending_outcome_gap_count": sum(
            matured_pending_gap_counts.values()
        ),
        "risky_micro_episode_horizon_observer_registration_status_counts": [
            {"status": key, "count": value}
            for key, value in horizon_registration_status_counts.most_common()
        ],
        "risky_micro_episode_horizon_observer_registered_candidate_count": sum(
            1 for row in rows if row.get("horizon_observer_registered")
        ),
        "risky_micro_episode_horizon_observer_event_count": (
            horizon_observer_event_count
        ),
        "risky_micro_episode_horizon_observer_fresh_bbo_event_count": (
            horizon_observer_fresh_bbo_event_count
        ),
        "risky_micro_episode_resolved_eligible_episode_count": resolved_eligible_count,
        "risky_micro_episode_daily_source_quality_adjusted_ev_pct": daily_source_quality_adjusted_ev_pct,
        "risky_micro_episode_recheck_diagnostic_resolved_count": (
            recheck_diagnostic_resolved_count
        ),
        "risky_micro_episode_recheck_diagnostic_ev_pct": (
            round(
                sum(recheck_diagnostic_net_bps)
                / recheck_diagnostic_resolved_count
                / 100.0,
                6,
            )
            if recheck_diagnostic_resolved_count
            else None
        ),
        "risky_micro_episode_source_quality_adjusted_ev_pct": None,
        "risky_micro_episode_ev_decision_authority": "daily_source_only_diagnostic_not_promotion_authority",
        "risky_micro_episode_executable_outcome_join_ready": resolved_eligible_count
        > 0,
        "risky_micro_episode_promotion_review_sample_floor_met": False,
        "risky_micro_episode_promotion_review_sample_floor_reason": "rolling_30_resolved_10_symbols_3_dates_and_10_filled_terminal_3_dates_not_owned_by_intraday_daily_report",
    }, rows


def _risky_micro_daily_rolling_eligible_rows(
    trade_date: str,
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Keep paired profile outcomes for source-only candidates only.

    Recheck rows stay in the daily diagnostic table and never enter the rolling
    promotion-EV population.  The daily cap is applied per symbol/profile so
    paired TTL/ask diagnostics remain comparable without duplicating promotion
    weight.
    """

    eligible: list[dict[str, Any]] = []
    seen_symbol_profiles: set[tuple[str, str]] = set()
    for row in sorted(rows, key=lambda item: str(item.get("ts") or "")):
        code = str(row.get("stock_code") or "").strip()
        candidate_status = str(row.get("candidate_status") or row.get("status") or "")
        venue = str(row.get("effective_venue") or "").strip().upper()
        session = str(row.get("market_session_bucket") or "").strip().upper()
        if (
            not code
            or candidate_status != "source_only_candidate"
            or venue not in {"KRX", "NXT", "PREMARKET_KRX_LIKE"}
            or session in {"", "UNKNOWN"}
        ):
            continue
        profile_outcomes = row.get("entry_profile_outcomes")
        if not isinstance(profile_outcomes, list):
            profile_outcomes = [row]
        for profile in profile_outcomes:
            if not isinstance(profile, dict):
                continue
            outcome_status = str(profile.get("outcome_join_status") or "")
            net_return_bps = _safe_float(profile.get("net_return_bps"))
            entry_profile = str(
                profile.get("entry_profile") or row.get("entry_profile") or "unknown"
            )
            symbol_profile = (code, entry_profile)
            if (
                symbol_profile in seen_symbol_profiles
                or not _boolish(profile.get("entry_profile_eligible", True))
                or not outcome_status.startswith("resolved_")
                or net_return_bps is None
            ):
                continue
            seen_symbol_profiles.add(symbol_profile)
            eligible.append(
                {
                    "trade_date": trade_date,
                    "ts": row.get("ts"),
                    "stock_code": code,
                    "stock_name": row.get("stock_name"),
                    "effective_venue": venue,
                    "market_session_bucket": session,
                    "source_category": row.get("source_category")
                    or _risky_micro_source_category(str(row.get("source_stage") or "")),
                    "source_stage": row.get("source_stage"),
                    "candidate_status": candidate_status,
                    "policy_version": str(
                        profile.get("policy_version")
                        or row.get("policy_version")
                        or "unknown"
                    ),
                    "entry_profile": entry_profile,
                    "entry_profile_ttl_sec": profile.get("entry_profile_ttl_sec"),
                    "entry_profile_promotion_ev_included": _boolish(
                        profile.get("entry_profile_promotion_ev_included")
                    ),
                    "outcome_join_status": outcome_status,
                    "fill_feasible": profile.get("fill_feasible"),
                    "net_return_bps": round(net_return_bps, 6),
                    "metric_role": "source_only_counterfactual_outcome",
                    "decision_authority": "source_only_no_runtime_apply",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "rolling_eligible_daily_cap_applied": True,
                }
            )
    return eligible


def _clean_baseline_rolling_risky_micro_outcomes(
    target_date: str,
    current_daily_rows: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Aggregate clean-baseline source-only outcomes without live authority."""

    source_rows = [dict(row) for row in current_daily_rows]
    inspected_dates = {target_date}
    excluded_reports: list[dict[str, str]] = []
    prefix = "rising_missed_intraday_feedback_"
    eligible_paths: list[Path] = []
    for path in sorted(REPORT_DIR.glob(f"{prefix}*.json")):
        report_date = path.stem.removeprefix(prefix)
        if CLEAN_BASELINE_DATE <= report_date < target_date:
            eligible_paths.append(path)
    prior_limit = max(0, RISKY_MICRO_ROLLING_REPORT_DAYS - 1)
    for path in eligible_paths[-prior_limit:] if prior_limit else []:
        report_date = path.stem.removeprefix(prefix)
        try:
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError):
            excluded_reports.append(
                {"target_date": report_date, "reason": "report_unreadable"}
            )
            continue
        if not isinstance(payload, dict) or (
            payload.get("report_type") != "rising_missed_intraday_feedback"
            or payload.get("target_date") != report_date
            or bool(payload.get("runtime_effect"))
            or bool(payload.get("allowed_runtime_apply"))
        ):
            excluded_reports.append(
                {"target_date": report_date, "reason": "report_contract_invalid"}
            )
            continue
        daily_rows = payload.get("risky_micro_episode_rolling_eligible_rows")
        if not isinstance(daily_rows, list):
            candidate_rows = payload.get("risky_micro_episode_source_candidate_rows")
            if not isinstance(candidate_rows, list):
                excluded_reports.append(
                    {"target_date": report_date, "reason": "daily_outcomes_missing"}
                )
                continue
            payload_summary = payload.get("summary")
            payload_summary = (
                payload_summary if isinstance(payload_summary, dict) else {}
            )
            reported_observation_count = _safe_int(
                payload_summary.get("risky_micro_episode_observation_count")
            )
            if reported_observation_count > len(candidate_rows):
                excluded_reports.append(
                    {
                        "target_date": report_date,
                        "reason": "truncated_daily_outcomes",
                    }
                )
                continue
            daily_rows = _risky_micro_daily_rolling_eligible_rows(
                report_date,
                [row for row in candidate_rows if isinstance(row, dict)],
            )
        else:
            daily_rows = _risky_micro_daily_rolling_eligible_rows(
                report_date,
                [row for row in daily_rows if isinstance(row, dict)],
            )
        inspected_dates.add(report_date)
        source_rows.extend(daily_rows)

    source_rows = sorted(
        source_rows,
        key=lambda item: (
            str(item.get("trade_date") or ""),
            str(item.get("ts") or ""),
            str(item.get("stock_code") or ""),
            str(item.get("entry_profile") or ""),
        ),
    )
    promotion_rows = [
        row
        for row in source_rows
        if str(row.get("candidate_status") or "") == "source_only_candidate"
        and str(row.get("policy_version") or "") == RISKY_MICRO_POLICY_VERSION
        and str(row.get("entry_profile") or "") == RISKY_MICRO_PRIMARY_ENTRY_PROFILE
        and _boolish(row.get("entry_profile_promotion_ev_included"))
    ]
    resolved_count = len(promotion_rows)
    unique_symbols = {
        str(row.get("stock_code") or "")
        for row in promotion_rows
        if row.get("stock_code")
    }
    trade_dates = {
        str(row.get("trade_date") or "")
        for row in promotion_rows
        if row.get("trade_date")
    }
    net_values = [
        value
        for value in (_safe_float(row.get("net_return_bps")) for row in promotion_rows)
        if value is not None
    ]
    diagnostic_ev_pct = (
        round(sum(net_values) / len(net_values) / 100.0, 6) if net_values else None
    )
    resolved_opportunity_sample_floor_met = bool(
        resolved_count >= RISKY_MICRO_ROLLING_MIN_RESOLVED_EPISODES
        and len(unique_symbols) >= RISKY_MICRO_ROLLING_MIN_UNIQUE_SYMBOLS
        and len(trade_dates) >= RISKY_MICRO_ROLLING_MIN_TRADE_DATES
    )
    filled_terminal_rows = [
        row
        for row in promotion_rows
        if _boolish(row.get("fill_feasible"))
        and str(row.get("outcome_join_status") or "")
        in {
            "resolved_target_first",
            "resolved_adverse_first",
            "resolved_timeout",
        }
    ]
    filled_terminal_trade_dates = {
        str(row.get("trade_date") or "")
        for row in filled_terminal_rows
        if row.get("trade_date")
    }
    filled_terminal_sample_floor_met = bool(
        len(filled_terminal_rows) >= RISKY_MICRO_ROLLING_MIN_FILLED_TERMINAL_EPISODES
        and len(filled_terminal_trade_dates) >= RISKY_MICRO_ROLLING_MIN_TRADE_DATES
    )
    sample_floor_met = bool(
        resolved_opportunity_sample_floor_met and filled_terminal_sample_floor_met
    )
    if not sample_floor_met:
        decision = "sample_floor_pending"
    elif diagnostic_ev_pct is not None and diagnostic_ev_pct > 0.0:
        decision = "outcome_join_ready_positive_ev"
    else:
        decision = "outcome_join_ready_non_positive_ev"
    outcome_counts = Counter(
        str(row.get("outcome_join_status") or "unknown") for row in promotion_rows
    )
    entry_profile_summaries: list[dict[str, Any]] = []
    for entry_profile in sorted(
        {
            str(row.get("entry_profile") or "unknown")
            for row in source_rows
            if row.get("entry_profile")
        }
    ):
        profile_rows = [
            row
            for row in source_rows
            if row.get("candidate_status") == "source_only_candidate"
            and row.get("policy_version") == RISKY_MICRO_POLICY_VERSION
            and row.get("entry_profile") == entry_profile
        ]
        profile_values = [
            value
            for value in (
                _safe_float(row.get("net_return_bps")) for row in profile_rows
            )
            if value is not None
        ]
        entry_profile_summaries.append(
            {
                "entry_profile": entry_profile,
                "resolved_opportunity_count": len(profile_rows),
                "filled_terminal_episode_count": sum(
                    1
                    for row in profile_rows
                    if _boolish(row.get("fill_feasible"))
                    and str(row.get("outcome_join_status") or "")
                    in {
                        "resolved_target_first",
                        "resolved_adverse_first",
                        "resolved_timeout",
                    }
                ),
                "diagnostic_ev_pct": (
                    round(sum(profile_values) / len(profile_values) / 100.0, 6)
                    if profile_values
                    else None
                ),
                "promotion_ev_included": (
                    entry_profile == RISKY_MICRO_PRIMARY_ENTRY_PROFILE
                ),
                "decision_authority": "source_only_profile_comparison_no_runtime_apply",
            }
        )
    promotion_blockers: list[str] = []
    if len(trade_dates) < RISKY_MICRO_ROLLING_MIN_TRADE_DATES:
        promotion_blockers.append("minimum_3_trade_dates_not_met")
    if not resolved_opportunity_sample_floor_met:
        promotion_blockers.append("resolved_opportunity_sample_floor_not_met")
    if not filled_terminal_sample_floor_met:
        promotion_blockers.append("filled_terminal_episode_sample_floor_not_met")
    if diagnostic_ev_pct is not None and diagnostic_ev_pct <= 0.0:
        promotion_blockers.append("non_positive_source_quality_adjusted_ev")
    if sample_floor_met:
        promotion_blockers.append(
            "explicit_preopen_policy_and_operator_approval_required"
        )
    return {
        "risky_micro_episode_rolling_decision": decision,
        "risky_micro_episode_rolling_resolved_episode_count": resolved_count,
        "risky_micro_episode_rolling_unique_symbol_count": len(unique_symbols),
        "risky_micro_episode_rolling_trade_date_count": len(trade_dates),
        "risky_micro_episode_rolling_trade_dates": sorted(trade_dates),
        "risky_micro_episode_rolling_diagnostic_ev_pct": diagnostic_ev_pct,
        "risky_micro_episode_source_quality_adjusted_ev_pct": (
            diagnostic_ev_pct if sample_floor_met else None
        ),
        "risky_micro_episode_promotion_review_sample_floor_met": sample_floor_met,
        "risky_micro_episode_resolved_opportunity_sample_floor_met": (
            resolved_opportunity_sample_floor_met
        ),
        "risky_micro_episode_resolved_opportunity_sample_floor": {
            "minimum_resolved_opportunities": RISKY_MICRO_ROLLING_MIN_RESOLVED_EPISODES,
            "minimum_unique_symbols": RISKY_MICRO_ROLLING_MIN_UNIQUE_SYMBOLS,
            "minimum_trade_dates": RISKY_MICRO_ROLLING_MIN_TRADE_DATES,
        },
        "risky_micro_episode_filled_terminal_episode_count": len(filled_terminal_rows),
        "risky_micro_episode_filled_terminal_trade_date_count": len(
            filled_terminal_trade_dates
        ),
        "risky_micro_episode_filled_terminal_sample_floor_met": (
            filled_terminal_sample_floor_met
        ),
        "risky_micro_episode_filled_terminal_sample_floor": {
            "minimum_filled_terminal_episodes": (
                RISKY_MICRO_ROLLING_MIN_FILLED_TERMINAL_EPISODES
            ),
            "minimum_trade_dates": RISKY_MICRO_ROLLING_MIN_TRADE_DATES,
            "terminal_outcomes": [
                "resolved_target_first",
                "resolved_adverse_first",
                "resolved_timeout",
            ],
            "fill_basis": "counterfactual_fresh_executable_ask_touch",
        },
        "risky_micro_episode_entry_profile_summaries": entry_profile_summaries,
        "risky_micro_episode_real_order_promotion_allowed": False,
        "risky_micro_episode_real_order_promotion_blockers": promotion_blockers,
        "risky_micro_episode_real_order_promotion_state": (
            "blocked_pending_preopen_policy_and_explicit_approval"
            if sample_floor_met
            else "blocked_sample_floor"
        ),
        "risky_micro_episode_promotion_review_sample_floor_reason": (
            "rolling_30_resolved_10_symbols_3_dates_and_10_filled_terminal_3_dates_met"
            if sample_floor_met
            else "rolling_resolved_opportunity_or_filled_terminal_floor_pending"
        ),
        "risky_micro_episode_rolling_outcome_status_counts": [
            {"status": key, "count": value}
            for key, value in outcome_counts.most_common()
        ],
        "risky_micro_episode_rolling_window": {
            "clean_baseline_date": CLEAN_BASELINE_DATE,
            "report_days": RISKY_MICRO_ROLLING_REPORT_DAYS,
            "inspected_source_dates": sorted(inspected_dates),
            "excluded_reports": excluded_reports,
            "per_symbol_daily_episode_cap": 1,
            "candidate_status_filter": "source_only_candidate",
            "policy_version_filter": RISKY_MICRO_POLICY_VERSION,
            "promotion_entry_profile": RISKY_MICRO_PRIMARY_ENTRY_PROFILE,
        },
        "risky_micro_episode_ev_decision_authority": (
            "rolling_source_only_review_candidate_no_runtime_apply"
            if sample_floor_met
            else "rolling_source_only_sample_floor_pending_no_runtime_apply"
        ),
    }, source_rows


def build_report(
    target_date: str,
    *,
    pipeline_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    pipeline_path = pipeline_path or _pipeline_path(target_date)
    resolved_pipeline_path = existing_or_gzip_path(pipeline_path)
    generated_at = generated_at or datetime.now(KST).isoformat(timespec="seconds")
    forced: dict[str, dict[str, Any]] = {}
    holding_by_record: dict[str, dict[str, Any]] = {}
    source_quality_status = (
        "pass" if resolved_pipeline_path.exists() else "missing_pipeline_events"
    )

    for row in iter_jsonl(pipeline_path):
        record_id = str(row.get("record_id") or "").strip()
        if not record_id:
            continue
        if _is_forced_rising_missed(row):
            item = forced.setdefault(record_id, _forced_entry_record(row))
            item["rising_missed_stage_count"] = (
                _safe_int(item.get("rising_missed_stage_count")) + 1
            )
            if row.get("stage") == "rising_missed_one_share_entry":
                first_count = item.get("rising_missed_stage_count", 1)
                item.update(_forced_entry_record(row))
                item["rising_missed_stage_count"] = first_count
        if row.get("pipeline") == "HOLDING_PIPELINE":
            fields = _fields(row)
            if "avg_down_count" not in fields and "profit_rate" not in fields:
                continue
            item = holding_by_record.setdefault(
                record_id,
                {
                    "record_id": record_id,
                    "stock_code": row.get("stock_code"),
                    "stock_name": row.get("stock_name"),
                    "max_avg_down_count": 0,
                    "min_profit_seen": None,
                    "max_profit_seen": None,
                    "avg_down_ge2_seen": False,
                },
            )
            _update_holding_record(item, row)

    rows: list[dict[str, Any]] = []
    for record_id, entry in forced.items():
        holding = holding_by_record.get(record_id)
        if not holding or not holding.get("avg_down_ge2_seen"):
            continue
        item = {**entry, **holding}
        item["feedback_label"] = _quality_label(item)
        item["decision_authority"] = "source_only_intraday_feedback_no_runtime_mutation"
        item["runtime_effect"] = False
        item["allowed_runtime_apply"] = False
        item["forbidden_uses"] = FORBIDDEN_USES
        rows.append(item)

    rows.sort(
        key=lambda item: (
            str(item.get("first_avg_down_ge2_ts") or ""),
            str(item.get("record_id") or ""),
        )
    )
    first_touch_rows = _build_first_touch_regression_rows(forced, pipeline_path)
    submit_lineage_rows = _build_forced_submit_lineage_rows(forced, pipeline_path)
    label_counts = Counter(
        str(item.get("feedback_label") or "unknown") for item in rows
    )
    first_touch_label_counts = Counter(
        str(item.get("first_touch_regression_label") or "unknown")
        for item in first_touch_rows
    )
    first_touch_source_quality_counts = _count_first_touch_source_quality(
        first_touch_rows
    )
    (
        submit_backoff_summary,
        submit_safety_rows,
        backoff_audit_rows,
        dynamic_age_post_apply_rows,
    ) = _build_submit_safety_and_backoff_audit(pipeline_path)
    latency_false_negative_summary, latency_false_negative_rows = (
        _build_latency_false_negative_review(submit_safety_rows)
    )
    latency_canary_summary, latency_canary_rows = (
        _build_latency_false_negative_canary_candidates(latency_false_negative_rows)
    )
    (
        rolling_latency_false_negative_rows,
        rolling_latency_false_negative_window,
    ) = _clean_baseline_rolling_latency_false_negative_candidates(
        target_date,
        latency_canary_rows,
    )
    tp1_label_events, tp1_observation_watermark = _load_tp1_label_event_projection(
        pipeline_path
    )
    tp1_label_summary, tp1_label_rows = _build_tp1_first_hit_labels(
        pipeline_path,
        label_events=tp1_label_events,
        observation_watermark=tp1_observation_watermark,
    )
    tp1_counterfactual_summary, tp1_counterfactual_rows = (
        _build_tp1_counterfactual_submit_safety(pipeline_path)
    )
    tp1_counterfactual_label_summary, tp1_counterfactual_label_rows = (
        _build_tp1_counterfactual_first_hit_labels(
            pipeline_path,
            label_events=tp1_label_events,
            observation_watermark=tp1_observation_watermark,
        )
    )
    (
        tp1_counterfactual_direct_target_summary,
        tp1_counterfactual_direct_target_rows,
    ) = _tp1_counterfactual_direct_target_first_attribution(
        tp1_counterfactual_label_rows
    )
    tp1_counterfactual_multi_horizon_summary = (
        _tp1_counterfactual_multi_horizon_summary(tp1_counterfactual_label_rows)
    )
    tp1_counterfactual_multi_horizon_by_effective_venue = (
        _tp1_counterfactual_multi_horizon_by_effective_venue(
            tp1_counterfactual_label_rows
        )
    )
    (
        nxt_session_summary,
        nxt_session_rows,
        nxt_order_rows,
        nxt_post_block_sampler_rows,
    ) = _build_nxt_session_observation(pipeline_path)
    adverse_micro_recovery_summary, adverse_micro_recovery_rows = (
        _build_adverse_micro_recovery_observation(pipeline_path)
    )
    risky_micro_episode_summary, risky_micro_episode_rows = (
        _build_risky_micro_episode_source_candidates(pipeline_path)
    )
    risky_micro_episode_daily_rolling_rows = _risky_micro_daily_rolling_eligible_rows(
        target_date,
        risky_micro_episode_rows,
    )
    risky_micro_episode_rolling_summary, risky_micro_episode_rolling_rows = (
        _clean_baseline_rolling_risky_micro_outcomes(
            target_date,
            risky_micro_episode_daily_rolling_rows,
        )
    )
    if first_touch_source_quality_counts["first_touch_ai_provenance_missing_count"]:
        source_quality_status = "first_touch_ai_provenance_missing"
    if first_touch_source_quality_counts["first_touch_ai_provenance_unusable_count"]:
        source_quality_status = "first_touch_ai_provenance_unusable"
    if first_touch_source_quality_counts[
        "first_touch_pressure_provenance_missing_count"
    ]:
        source_quality_status = "first_touch_pressure_provenance_missing"
    if first_touch_source_quality_counts[
        "first_touch_pressure_provenance_unusable_count"
    ]:
        source_quality_status = "first_touch_pressure_provenance_unusable"
    if first_touch_source_quality_counts["first_touch_micro_provenance_missing_count"]:
        source_quality_status = "first_touch_micro_provenance_missing"
    if first_touch_source_quality_counts["first_touch_micro_provenance_unusable_count"]:
        source_quality_status = "first_touch_micro_provenance_unusable"
    (
        rolling_nxt_post_block_rows,
        rolling_nxt_post_block_window,
    ) = _clean_baseline_rolling_nxt_post_block_outcomes(
        target_date,
        list(
            nxt_session_summary.get(
                "rising_missed_nxt_post_block_blocker_outcome_attribution", []
            )
        ),
    )
    initial_fail_count = sum(
        count
        for label, count in label_counts.items()
        if label
        in {
            "rising_missed_initial_quality_fail",
            "rising_missed_initial_quality_fail_open",
        }
    )
    code_improvement_orders = []
    if rows:
        code_improvement_orders.append(
            {
                "order_id": "order_rising_missed_initial_quality_feedback_loop",
                "title": "rising missed initial quality feedback loop",
                "source_report_type": "rising_missed_intraday_feedback",
                "lifecycle_stage": "entry",
                "target_subsystem": "rising_missed_entry_classifier",
                "route": "instrumentation_order",
                "mapped_family": "rising_missed_initial_quality_feedback_loop",
                "threshold_family": "rising_missed_initial_quality_feedback_loop",
                "improvement_type": "source_only_intraday_feedback_workorder",
                "confidence": "same_day_source_only",
                "priority": 1 if initial_fail_count else 2,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "decision_authority": "source_only_intraday_feedback_no_runtime_mutation",
                "implementation_status": "implemented",
                "implementation_provenance": {
                    "implementation_type": "rising_missed_avg_down_ge2_intraday_detector",
                    "rising_missed_avg_down_ge2_count": len(rows),
                    "initial_quality_fail_count": initial_fail_count,
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "root_cause_closure_status_hint": "implementation_done",
                },
                "expected_ev_effect": (
                    "Continuously separate rising-missed entries that need two or more average-down attempts "
                    "from profitable scout examples before proposing any classifier expansion."
                ),
                "evidence": [
                    f"rising_missed_avg_down_ge2_count={len(rows)}",
                    f"initial_quality_fail_count={initial_fail_count}",
                    "feedback_label_counts="
                    + ",".join(
                        f"{key}={value}" for key, value in label_counts.most_common()
                    ),
                    f"source_quality_status={source_quality_status}",
                ],
                "source_paths": [str(resolved_pipeline_path)],
                "files_likely_touched": [
                    "src/engine/scalping/rising_missed_one_share_entry.py",
                    "src/engine/monitoring/intraday_entry_blocker_diagnostics.py",
                    "src/engine/monitoring/rising_missed_scout_workorder.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/pytest src/tests/test_rising_missed_intraday_feedback.py src/tests/test_rising_missed_scout_workorder.py src/tests/test_build_code_improvement_workorder.py",
                    "feedback loop remains source-only and does not mutate intraday runtime thresholds, broker/order guards, provider route, bot state, or scale-in quantity/caps",
                ],
                "forbidden_uses": FORBIDDEN_USES,
            }
        )

    return {
        "schema_version": 1,
        "report_type": "rising_missed_intraday_feedback",
        "target_date": target_date,
        "generated_at": generated_at,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "decision_authority": "source_only_intraday_feedback_no_runtime_mutation",
        "forbidden_uses": FORBIDDEN_USES,
        "metric_contracts": {
            "rising_missed_avg_down_ge2_feedback": {
                "metric_role": "entry_quality_intraday_feedback",
                "decision_authority": "source_only_intraday_feedback_no_runtime_mutation",
                "window_policy": "same_day_intraday_pipeline_events",
                "sample_floor": "1_rising_missed_forced_entry_with_avg_down_count_ge2",
                "primary_decision_metric": "rising_missed_avg_down_ge2_count",
                "source_quality_gate": "record_id_joined_forced_rising_missed_entry_and_holding_avg_down_snapshot",
                "forbidden_uses": FORBIDDEN_USES,
            },
            "rising_missed_first_touch_regression": {
                "metric_role": "source_only_first_touch_regression",
                "decision_authority": "source_only_first_touch_regression_table",
                "window_policy": "same_day_intraday_pipeline_events_continuously_updated",
                "sample_floor": "1_rising_missed_forced_entry_with_first_stop_line_touch",
                "primary_decision_metric": "first_touch_regression_label_counts",
                "source_quality_gate": (
                    "record_id_joined_forced_rising_missed_entry_and_first_stop_line_touch_event_with_"
                    "holding_ai_role_gate_provenance_trusted_pressure_provenance_and_"
                    "fresh_minute_candle_micro_vwap_provenance_when_used"
                ),
                "forbidden_uses": FORBIDDEN_USES,
            },
            "rising_missed_submit_lineage": {
                "metric_role": "source_only_rising_missed_submit_lineage",
                "decision_authority": "source_only_rising_missed_submit_lineage",
                "window_policy": "same_day_intraday_pipeline_events_continuously_updated",
                "sample_floor": "1_forced_rising_missed_entry_with_order_plan_or_submit_event",
                "primary_decision_metric": "rising_missed_entry_submitted_count",
                "source_quality_gate": (
                    "record_id_or_code_time_window_joined_forced_rising_missed_entry_and_submit_events"
                ),
                "forbidden_uses": FORBIDDEN_USES,
            },
            "rising_missed_submit_safety_blocker_breakdown": {
                "metric_role": "source_only_submit_safety_blocker_attribution",
                "decision_authority": "source_only_submit_safety_blocker_attribution",
                "window_policy": "same_day_intraday_pipeline_events_continuously_updated",
                "sample_floor": "1_submit_safety_block_event",
                "primary_decision_metric": "submit_safety_bucket_counts",
                "source_quality_gate": (
                    "pipeline_event_submit_safety_fields_with_quote_ai_micro_provenance_"
                    "and_executable_ask_then_post_block_executable_bid_for_latency_tick"
                ),
                "forbidden_uses": FORBIDDEN_USES,
            },
            "rising_missed_backoff_opportunity_audit": {
                "metric_role": "source_only_backoff_opportunity_audit",
                "decision_authority": "source_only_backoff_opportunity_audit",
                "window_policy": (
                    "same_day_fast_precheck_backoff_plus_exact_route_executable_"
                    "bbo_1_3_5_10m"
                ),
                "sample_floor": (
                    "1_fast_precheck_budget_reallocated_event_plus_entry_ask_and_"
                    "2_fresh_post_backoff_executable_bid_samples"
                ),
                "primary_decision_metric": "potential_backoff_opportunity_loss_count",
                "source_quality_gate": (
                    "same_code_venue_session_exact_route_entry_ask_and_post_backoff_"
                    "fresh_executable_bid_with_15s_sampled_gross_target_1_3pct_"
                    "before_sampled_adverse_stop_and_mark_price_candidates_kept_"
                    "diagnostic_only"
                ),
                "forbidden_uses": FORBIDDEN_USES,
            },
            "rising_missed_latency_false_negative_review": {
                "metric_role": "source_only_latency_false_negative_review",
                "decision_authority": "source_only_latency_false_negative_review",
                "window_policy": "same_day_intraday_pipeline_events_continuously_updated",
                "sample_floor": "1_latency_submit_safety_block_with_high_mfe_low_mae",
                "primary_decision_metric": "latency_false_negative_review_count",
                "source_quality_gate": (
                    "submit_safety_blocker_rows_with_executable_ask_entry_post_block_"
                    "executable_bid_mfe_mae_and_latency_micro_provenance"
                ),
                "forbidden_uses": FORBIDDEN_USES,
            },
            "rising_missed_latency_false_negative_canary_candidate": {
                "metric_role": "source_only_latency_false_negative_canary_candidate",
                "decision_authority": "source_only_latency_false_negative_canary_candidate",
                "window_policy": "same_day_intraday_pipeline_events_continuously_updated",
                "sample_floor": "1_latency_false_negative_review_row",
                "primary_decision_metric": "latency_false_negative_canary_ready_count",
                "source_quality_gate": (
                    "latency_false_negative_review_rows_with_spread_true_ofi_ws_age_"
                    "and_executable_bbo_post_block_mfe_mae_and_runtime_dynamic_age_"
                    "signed_tape_provenance_when_emitted"
                ),
                "forbidden_uses": FORBIDDEN_USES,
            },
            "rising_missed_latency_false_negative_rolling_attribution": {
                "metric_role": "source_only_latency_false_negative_rolling_attribution",
                "decision_authority": "source_only_no_retry_or_runtime_mutation",
                "window_policy": "clean_baseline_rolling_latest_20_report_artifacts",
                "sample_floor": "10_executable_bbo_rows_per_venue_session_cohort",
                "primary_decision_metric": (
                    "low_adverse_opportunity_rate_pct_and_ready_for_recheck_rate_pct_"
                    "with_equal_weight_mfe_mae"
                ),
                "source_quality_gate": (
                    "explicit_venue_session_executable_ask_and_post_block_executable_bid"
                ),
                "forbidden_uses": FORBIDDEN_USES,
            },
            "rising_missed_dynamic_age_post_apply_attribution": {
                "metric_role": "source_only_post_apply_attribution",
                "decision_authority": "source_only_dynamic_age_post_apply_attribution",
                "window_policy": "same_day_1_3_5_10_20_30_60m_executable_bid_after_dynamic_age_apply",
                "sample_floor": "1_unique_exact_trace_dynamic_age_apply_with_executable_ask",
                "primary_decision_metric": "net_target_first_vs_adverse_stop_first_count",
                "source_quality_gate": (
                    "exact_ai_decision_trace_explicit_venue_entry_executable_ask_"
                    "and_same_symbol_post_apply_executable_bid"
                ),
                "forbidden_uses": FORBIDDEN_USES,
            },
            "rising_missed_tp1_counterfactual_submit_safety": {
                "metric_role": "source_only_candidate_to_submit_safety_projection",
                "decision_authority": "source_only_candidate_to_submit_safety_projection",
                "window_policy": "same_day_selector_block_evaluation_snapshots",
                "sample_floor": "1_tp1_selector_block_or_defer",
                "primary_decision_metric": "counterfactual_action_counts",
                "source_quality_gate": "tp1_freshness_envelope_and_selector_provenance",
                "forbidden_uses": FORBIDDEN_USES,
            },
            "rising_missed_tp1_counterfactual_outcome_label": {
                "metric_role": "source_only_tp1_counterfactual_outcome_label",
                "decision_authority": "source_only_tp1_counterfactual_outcome_label",
                "window_policy": "selector_block_plus_20m_same_symbol_fresh_price_observations",
                "sample_floor": "1_tp1_selector_block_with_effective_price",
                "primary_decision_metric": "rising_missed_tp1_counterfactual_gross_label_counts",
                "source_quality_gate": (
                    "freshness_envelope_effective_price_then_fresh_submit_mark_or_signed_ws_0b"
                ),
                "forbidden_uses": FORBIDDEN_USES,
            },
            "rising_missed_tp1_counterfactual_multi_horizon_outcome": {
                "metric_role": "source_only_missed_entry_horizon_observation",
                "decision_authority": "source_only_tp1_counterfactual_multi_horizon",
                "window_policy": (
                    "selector_block_plus_1_3_5_10_20_30_60m_same_symbol_fresh_price_observations"
                ),
                "sample_floor": "2_post_block_price_observations_per_horizon",
                "primary_decision_metric": (
                    "rising_missed_tp1_counterfactual_late_recovery_after_adverse_count"
                ),
                "source_quality_gate": (
                    "candidate_effective_price_same_symbol_post_block_price_and_"
                    "explicit_effective_venue_provenance_for_venue_split"
                ),
                "forbidden_uses": FORBIDDEN_USES,
            },
            "rising_missed_tp1_counterfactual_direct_target_first_attribution": {
                "metric_role": "source_only_missed_opportunity_attribution",
                "decision_authority": (
                    "source_only_tp1_direct_target_first_attribution"
                ),
                "window_policy": "same_day_intraday_pipeline_events",
                "sample_floor": "1_direct_target_first_executable_bbo_label",
                "primary_decision_metric": (
                    "rising_missed_tp1_counterfactual_direct_target_first_count"
                ),
                "source_quality_gate": (
                    "executable_best_ask_entry_and_executable_best_bid_"
                    "target_before_adverse_with_explicit_venue_session"
                ),
                "forbidden_uses": FORBIDDEN_USES,
            },
            "rising_missed_nxt_session_observation": {
                "metric_role": "source_quality_gate",
                "decision_authority": "observe_only_no_runtime_mutation",
                "window_policy": "same_day_nxt_session_tp1_and_order_events",
                "sample_floor": "1_nxt_session_rising_missed_tp1_evaluation",
                "primary_decision_metric": "nxt_session_micro_and_fillability_distribution",
                "source_quality_gate": (
                    "absolute_0b_0d_receive_ts_actual_ws_item_route_effective_order_"
                    "resolution_and_price_jump_runtime_call_provenance"
                ),
                "forbidden_uses": FORBIDDEN_USES,
            },
            "rising_missed_nxt_post_block_price_sampler": {
                "metric_role": "source_quality_gate",
                "decision_authority": "source_only_nxt_post_block_price_observation",
                "window_policy": "nxt_tp1_or_downstream_block_bounded_20m",
                "sample_floor": (
                    "2_fresh_nxt_ws_or_bounded_observation_only_rest_price_samples"
                ),
                "primary_decision_metric": "gross_1.30_first_before_adverse_0.70",
                "source_quality_gate": (
                    "fresh_absolute_nxt_ws_route_or_bounded_ka10004_receive_observation_"
                    "with_sampler_and_rest_runtime_call_provenance"
                ),
                "forbidden_uses": FORBIDDEN_USES,
            },
            "rising_missed_nxt_post_block_blocker_outcome_attribution": {
                "metric_role": "source_quality_gated_blocker_outcome_attribution",
                "decision_authority": "source_only_no_runtime_mutation",
                "window_policy": "same_day_nxt_completed_20m_post_block_sampler",
                "sample_floor": "10_source_quality_pass_completed_samplers_per_blocker",
                "primary_decision_metric": (
                    "gross_target_first_rate_pct_and_adverse_stop_first_rate_pct"
                ),
                "source_quality_gate": (
                    "completed_sampler_source_quality_pass_and_explicit_nxt_venue"
                ),
                "forbidden_uses": FORBIDDEN_USES,
            },
            "rising_missed_nxt_post_block_rolling_blocker_outcome_attribution": {
                "metric_role": "source_quality_gated_blocker_outcome_attribution",
                "decision_authority": "source_only_no_runtime_mutation",
                "window_policy": "clean_baseline_rolling_latest_20_report_artifacts",
                "sample_floor": (
                    "10_source_quality_pass_completed_samplers_per_blocker"
                ),
                "primary_decision_metric": (
                    "gross_target_first_rate_pct_and_adverse_stop_first_rate_pct_"
                    "with_gross_first_hit_payoff_proxy_and_equal_weight_mfe_mae"
                ),
                "source_quality_gate": (
                    "daily_completed_sampler_source_quality_pass_and_explicit_nxt_venue"
                ),
                "forbidden_uses": FORBIDDEN_USES,
            },
            "rising_missed_adverse_micro_recovery": {
                "metric_role": "source_quality_gate",
                "decision_authority": "observe_only_adverse_micro_recovery",
                "window_policy": "krx_tp1_hard_negative_15s_30s_60s",
                "sample_floor": "1_fresh_ws_0b_checkpoint",
                "primary_decision_metric": "post_block_recovery_move_pct",
                "source_quality_gate": (
                    "canonical_krx_registration_and_absolute_ws_0b_timestamp"
                ),
                "forbidden_uses": FORBIDDEN_USES,
            },
            "risky_micro_episode_source_candidate": {
                "metric_role": "source_candidate_classification",
                "decision_authority": (
                    "source_only_passive_episode_research_no_order_authority"
                ),
                "window_policy": "same_candidate_fresh_bbo_source_projection",
                "sample_floor": "not_applicable_source_candidate_projection",
                "primary_decision_metric": "candidate_status_counts",
                "source_quality_gate": (
                    "rising_missed_lineage_fresh_executable_bbo_tick_context_and_non_adverse_micro"
                ),
                "forbidden_uses": [
                    *FORBIDDEN_USES,
                    "broker_order_submission",
                    "broker_order_cancel",
                    "automated_sell",
                    "live_promotion_from_candidate_counts",
                ],
            },
            "risky_micro_episode_executable_outcome": {
                "metric_role": "source_only_counterfactual_outcome",
                "decision_authority": "source_only_no_runtime_apply",
                "window_policy": (
                    "same_episode_bid_plus_one_ttl_3_5_10_and_ask_ttl3_spread_le_15bps_"
                    "with_fresh_executable_bbo_3_10_20_30_second_path"
                ),
                "sample_floor": (
                    "rolling_30_resolved_opportunities_10_symbols_3_dates_and_"
                    "10_filled_terminal_episodes_3_dates_for_promotion_review"
                ),
                "primary_decision_metric": "source_quality_adjusted_ev_pct",
                "source_quality_gate": (
                    "passive_ask_touch_and_fresh_executable_bid_with_exact_"
                    "symbol_session_and_item_venue_or_official_route_depth_proof"
                ),
                "forbidden_uses": [
                    *FORBIDDEN_USES,
                    "daily_only_ev_runtime_promotion",
                    "recheck_required_in_promotion_ev",
                    "multi_profile_duplicate_weight_in_promotion_ev",
                    "cross_venue_outcome_join",
                    "mark_price_fill_or_exit_substitution",
                ],
            },
            "risky_micro_episode_instrumentation_gap": {
                "metric_role": "instrumentation_gap",
                "decision_authority": "source_quality_repair_priority_only",
                "window_policy": "same_candidate_projection_input_contract",
                "sample_floor": "one_missing_required_input",
                "primary_decision_metric": "gap_count_by_canonical_reason",
                "source_quality_gate": (
                    "explicit_bbo_quote_age_and_tick_context_presence_state"
                ),
                "forbidden_uses": [
                    *FORBIDDEN_USES,
                    "missing_context_imputation_for_promotion_ev",
                    "source_quality_gap_as_real_order_authority",
                ],
            },
            "risky_micro_episode_bounded_bbo_observer": {
                "metric_role": "source_quality_instrumentation",
                "decision_authority": (
                    "report_only_bounded_executable_bbo_observer_no_order_authority"
                ),
                "window_policy": (
                    "same_symbol_session_exact_route_or_depth_proven_venue_"
                    "1s_until_45s_after_runtime_candidate"
                ),
                "sample_floor": "not_applicable_instrumentation",
                "primary_decision_metric": ("fresh_executable_bbo_horizon_coverage"),
                "source_quality_gate": (
                    "exact_symbol_session_0d_and_exact_item_venue_or_official_"
                    "route_depth_proof_and_fresh_bbo_age_le_1000ms"
                ),
                "forbidden_uses": [
                    *FORBIDDEN_USES,
                    "broker_order_submission",
                    "broker_order_cancel",
                    "scanner_slot_authority",
                    "entry_or_exit_authority",
                    "stale_quote_or_hard_safety_bypass",
                ],
            },
        },
        "source_paths": {"pipeline_events": str(resolved_pipeline_path)},
        "source_quality": {
            "status": source_quality_status,
            "pipeline_events_exists": resolved_pipeline_path.exists(),
            "tp1_label_projection_mode": "streaming_two_pass_exact_field_allowlist_v3",
            "tp1_label_projected_event_count": len(tp1_label_events),
            "tp1_label_full_fields_materialized": False,
            **first_touch_source_quality_counts,
        },
        "summary": {
            "forced_rising_missed_record_count": len(forced),
            "holding_record_count": len(holding_by_record),
            "rising_missed_avg_down_ge2_count": len(rows),
            "rising_missed_submit_lineage_record_count": len(submit_lineage_rows),
            "rising_missed_order_plan_forced_count": sum(
                _safe_int(item.get("order_plan_forced_count"))
                for item in submit_lineage_rows
            ),
            "rising_missed_entry_submitted_count": sum(
                1 for item in submit_lineage_rows if item.get("entry_order_submitted")
            ),
            "rising_missed_order_bundle_submitted_count": sum(
                _safe_int(item.get("order_bundle_submitted_count"))
                for item in submit_lineage_rows
            ),
            "rising_missed_order_leg_sent_count": sum(
                _safe_int(item.get("order_leg_sent_count"))
                for item in submit_lineage_rows
            ),
            "first_touch_regression_record_count": len(first_touch_rows),
            "first_touch_entry_submitted_count": sum(
                1 for item in first_touch_rows if item.get("entry_order_submitted")
            ),
            "first_touch_avg_down_submitted_count": sum(
                1
                for item in first_touch_rows
                if item.get("first_touch_avg_down_submitted")
            ),
            "first_touch_not_eligible_count": sum(
                1
                for item in first_touch_rows
                if item.get("first_touch_not_eligible_seen")
            ),
            "first_touch_avgdown_decision_blocked_count": sum(
                1
                for item in first_touch_rows
                if item.get("first_touch_avgdown_decision_blocked")
            ),
            "first_touch_closed_count": sum(
                1
                for item in first_touch_rows
                if item.get("final_profit_rate") is not None
            ),
            "first_touch_profitable_count": first_touch_label_counts.get(
                "first_touch_recovered_profit", 0
            ),
            "first_touch_loss_or_flat_count": first_touch_label_counts.get(
                "first_touch_loss_or_flat", 0
            ),
            "first_touch_regression_label_counts": [
                {"first_touch_regression_label": key, "count": value}
                for key, value in first_touch_label_counts.most_common()
            ],
            **first_touch_source_quality_counts,
            "initial_quality_fail_count": initial_fail_count,
            "scale_in_rescue_warning_count": label_counts.get(
                "rising_missed_scale_in_rescue_warning", 0
            ),
            "feedback_label_counts": [
                {"feedback_label": key, "count": value}
                for key, value in label_counts.most_common()
            ],
            **submit_backoff_summary,
            **latency_false_negative_summary,
            **latency_canary_summary,
            "latency_false_negative_rolling_attribution": (
                rolling_latency_false_negative_rows
            ),
            "latency_false_negative_rolling_window": (
                rolling_latency_false_negative_window
            ),
            **tp1_label_summary,
            **tp1_counterfactual_summary,
            **tp1_counterfactual_label_summary,
            **tp1_counterfactual_direct_target_summary,
            **tp1_counterfactual_multi_horizon_summary,
            "rising_missed_tp1_counterfactual_detail_row_export_count": min(
                len(tp1_counterfactual_label_rows), TP1_DETAIL_ROW_EXPORT_LIMIT
            ),
            "rising_missed_tp1_counterfactual_detail_row_omitted_count": max(
                0,
                len(tp1_counterfactual_label_rows) - TP1_DETAIL_ROW_EXPORT_LIMIT,
            ),
            "rising_missed_tp1_counterfactual_detail_row_export_truncated": (
                len(tp1_counterfactual_label_rows) > TP1_DETAIL_ROW_EXPORT_LIMIT
            ),
            "rising_missed_tp1_counterfactual_multi_horizon_by_effective_venue": (
                tp1_counterfactual_multi_horizon_by_effective_venue
            ),
            **nxt_session_summary,
            "rising_missed_nxt_post_block_rolling_blocker_outcome_attribution": (
                rolling_nxt_post_block_rows
            ),
            "rising_missed_nxt_post_block_rolling_window": (
                rolling_nxt_post_block_window
            ),
            **adverse_micro_recovery_summary,
            **risky_micro_episode_summary,
            **risky_micro_episode_rolling_summary,
            "code_improvement_order_count": len(code_improvement_orders),
            "consumer_readiness": {
                "scout_workorder_input_ready": bool(forced),
                "closed_first_touch_outcome_available": any(
                    item.get("final_profit_rate") is not None
                    for item in first_touch_rows
                ),
                "code_improvement_order_available": bool(code_improvement_orders),
                "state": (
                    "actionable_source_rows"
                    if forced or rows or code_improvement_orders
                    else "no_actionable_source_rows"
                ),
            },
        },
        "records": rows[:100],
        "rising_missed_submit_lineage_rows": submit_lineage_rows[:200],
        "first_touch_regression_rows": first_touch_rows[:200],
        # Keep the current intraday window inspectable after the bounded table
        # reaches its payload limit.
        "submit_safety_blocker_rows": submit_safety_rows[-200:],
        "blocked_zero_qty_counterfactual_rows": [
            item
            for item in submit_safety_rows
            if item.get("stage") == "blocked_zero_qty"
        ][-200:],
        "backoff_opportunity_audit_rows": backoff_audit_rows[:200],
        "latency_false_negative_review_rows": latency_false_negative_rows[:200],
        "latency_false_negative_canary_candidate_rows": latency_canary_rows[:200],
        "latency_false_negative_rolling_attribution_rows": (
            rolling_latency_false_negative_rows
        ),
        "dynamic_age_post_apply_attribution_rows": dynamic_age_post_apply_rows[:200],
        "rising_missed_tp1_first_hit_label_rows": tp1_label_rows[:200],
        "rising_missed_tp1_counterfactual_submit_safety_rows": tp1_counterfactual_rows[
            :200
        ],
        "rising_missed_tp1_counterfactual_first_hit_label_rows": tp1_counterfactual_label_rows[
            :TP1_DETAIL_ROW_EXPORT_LIMIT
        ],
        "rising_missed_tp1_counterfactual_direct_target_first_rows": (
            tp1_counterfactual_direct_target_rows[:TP1_DETAIL_ROW_EXPORT_LIMIT]
        ),
        "rising_missed_nxt_session_observation_rows": nxt_session_rows[:200],
        "rising_missed_nxt_order_resolution_rows": nxt_order_rows[:200],
        "rising_missed_nxt_post_block_price_sampler_rows": nxt_post_block_sampler_rows[
            -200:
        ],
        "rising_missed_adverse_micro_recovery_rows": adverse_micro_recovery_rows[-200:],
        "risky_micro_episode_source_candidate_rows": risky_micro_episode_rows[-200:],
        "risky_micro_episode_recheck_diagnostic_rows": [
            row
            for row in risky_micro_episode_rows[-200:]
            if row.get("status") == "recheck_required"
        ],
        "risky_micro_episode_rolling_eligible_rows": (
            risky_micro_episode_daily_rolling_rows
        ),
        "risky_micro_episode_rolling_outcome_rows": risky_micro_episode_rolling_rows,
        "code_improvement_orders": code_improvement_orders,
    }


def write_outputs(
    report: dict[str, Any], *, output_json: Path, output_md: Path
) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    lines = [
        f"# {report.get('target_date')} Rising Missed Intraday Feedback",
        "",
        f"- generated_at: {report.get('generated_at')}",
        "- decision_authority: source_only_intraday_feedback_no_runtime_mutation",
        "- runtime_effect: false",
        "- allowed_runtime_apply: false",
        "- forbidden_uses: " + ", ".join(FORBIDDEN_USES),
        "",
        "## Summary",
        "",
        f"- forced_rising_missed_record_count: {summary.get('forced_rising_missed_record_count')}",
        f"- holding_record_count: {summary.get('holding_record_count')}",
        f"- rising_missed_avg_down_ge2_count: {summary.get('rising_missed_avg_down_ge2_count')}",
        f"- rising_missed_submit_lineage_record_count: "
        f"{summary.get('rising_missed_submit_lineage_record_count')}",
        f"- rising_missed_order_plan_forced_count: {summary.get('rising_missed_order_plan_forced_count')}",
        f"- rising_missed_entry_submitted_count: {summary.get('rising_missed_entry_submitted_count')}",
        f"- rising_missed_order_bundle_submitted_count: "
        f"{summary.get('rising_missed_order_bundle_submitted_count')}",
        f"- rising_missed_order_leg_sent_count: {summary.get('rising_missed_order_leg_sent_count')}",
        f"- first_touch_regression_record_count: {summary.get('first_touch_regression_record_count')}",
        f"- first_touch_entry_submitted_count: {summary.get('first_touch_entry_submitted_count')}",
        f"- first_touch_avg_down_submitted_count: {summary.get('first_touch_avg_down_submitted_count')}",
        f"- first_touch_avgdown_decision_blocked_count: {summary.get('first_touch_avgdown_decision_blocked_count')}",
        f"- first_touch_closed_count: {summary.get('first_touch_closed_count')}",
        f"- first_touch_profitable_count: {summary.get('first_touch_profitable_count')}",
        f"- first_touch_loss_or_flat_count: {summary.get('first_touch_loss_or_flat_count')}",
        f"- first_touch_ai_provenance_missing_count: {summary.get('first_touch_ai_provenance_missing_count')}",
        f"- first_touch_ai_provenance_unusable_count: {summary.get('first_touch_ai_provenance_unusable_count')}",
        f"- first_touch_pressure_provenance_missing_count: "
        f"{summary.get('first_touch_pressure_provenance_missing_count')}",
        f"- first_touch_pressure_provenance_unusable_count: "
        f"{summary.get('first_touch_pressure_provenance_unusable_count')}",
        f"- first_touch_micro_provenance_missing_count: {summary.get('first_touch_micro_provenance_missing_count')}",
        f"- first_touch_micro_provenance_unusable_count: {summary.get('first_touch_micro_provenance_unusable_count')}",
        f"- initial_quality_fail_count: {summary.get('initial_quality_fail_count')}",
        f"- scale_in_rescue_warning_count: {summary.get('scale_in_rescue_warning_count')}",
        f"- submit_safety_block_count: {summary.get('submit_safety_block_count')}",
        f"- submit_safety_executable_bbo_required_count: "
        f"{summary.get('submit_safety_executable_bbo_required_count')}",
        f"- submit_safety_executable_bbo_entry_source_gap_count: "
        f"{summary.get('submit_safety_executable_bbo_entry_source_gap_count')}",
        f"- submit_safety_executable_bbo_labeled_count: "
        f"{summary.get('submit_safety_executable_bbo_labeled_count')}",
        f"- submit_safety_source_quality_unknown_gate_counts: "
        f"{summary.get('submit_safety_source_quality_unknown_gate_counts')}",
        f"- submit_safety_source_quality_unknown_state_counts: "
        f"{summary.get('submit_safety_source_quality_unknown_state_counts')}",
        f"- submit_safety_source_quality_unknown_missing_field_counts: "
        f"{summary.get('submit_safety_source_quality_unknown_missing_field_counts')}",
        f"- backoff_audit_symbol_count: {summary.get('backoff_audit_symbol_count')}",
        f"- backoff_recovered_eval_symbol_count: {summary.get('backoff_recovered_eval_symbol_count')}",
        f"- backoff_active_positive_delta_symbol_count: "
        f"{summary.get('backoff_active_positive_delta_symbol_count')}",
        f"- potential_backoff_opportunity_loss_count: {summary.get('potential_backoff_opportunity_loss_count')}",
        f"- latency_false_negative_review_count: {summary.get('latency_false_negative_review_count')}",
        f"- latency_false_negative_true_ofi_count: {summary.get('latency_false_negative_true_ofi_count')}",
        f"- latency_false_negative_spread_only_count: "
        f"{summary.get('latency_false_negative_spread_only_count')}",
        f"- latency_false_negative_canary_candidate_count: "
        f"{summary.get('latency_false_negative_canary_candidate_count')}",
        f"- latency_false_negative_canary_ready_count: "
        f"{summary.get('latency_false_negative_canary_ready_count')}",
        f"- latency_false_negative_canary_observe_wide_spread_count: "
        f"{summary.get('latency_false_negative_canary_observe_wide_spread_count')}",
        f"- latency_false_negative_canary_hold_sample_count: "
        f"{summary.get('latency_false_negative_canary_hold_sample_count')}",
        f"- latency_false_negative_runtime_dynamic_age_source_gap_count: "
        f"{summary.get('latency_false_negative_runtime_dynamic_age_source_gap_count')}",
        f"- latency_false_negative_runtime_dynamic_age_eligible_count: "
        f"{summary.get('latency_false_negative_runtime_dynamic_age_eligible_count')}",
        f"- latency_false_negative_runtime_dynamic_age_applied_count: "
        f"{summary.get('latency_false_negative_runtime_dynamic_age_applied_count')}",
        f"- latency_false_negative_rolling_attribution: "
        f"{summary.get('latency_false_negative_rolling_attribution')}",
        f"- latency_false_negative_rolling_window: "
        f"{summary.get('latency_false_negative_rolling_window')}",
        f"- dynamic_age_post_apply_episode_count: "
        f"{summary.get('dynamic_age_post_apply_episode_count')}",
        f"- dynamic_age_post_apply_latency_pass_count: "
        f"{summary.get('dynamic_age_post_apply_latency_pass_count')}",
        f"- dynamic_age_post_apply_actual_order_submitted_count: "
        f"{summary.get('dynamic_age_post_apply_actual_order_submitted_count')}",
        f"- dynamic_age_post_apply_executable_bbo_source_gap_count: "
        f"{summary.get('dynamic_age_post_apply_executable_bbo_source_gap_count')}",
        f"- dynamic_age_post_apply_venue_source_gap_count: "
        f"{summary.get('dynamic_age_post_apply_venue_source_gap_count')}",
        f"- dynamic_age_post_apply_outcome_source_gap_count: "
        f"{summary.get('dynamic_age_post_apply_outcome_source_gap_count')}",
        f"- dynamic_age_post_apply_source_quality_pass_count: "
        f"{summary.get('dynamic_age_post_apply_source_quality_pass_count')}",
        f"- dynamic_age_post_apply_first_hit_counts: "
        f"{summary.get('dynamic_age_post_apply_first_hit_counts')}",
        f"- dynamic_age_post_apply_venue_counts: "
        f"{summary.get('dynamic_age_post_apply_venue_counts')}",
        f"- rising_missed_tp1_counterfactual_submit_safety_count: "
        f"{summary.get('rising_missed_tp1_counterfactual_submit_safety_count')}",
        f"- rising_missed_tp1_counterfactual_unique_symbol_count: "
        f"{summary.get('rising_missed_tp1_counterfactual_unique_symbol_count')}",
        f"- rising_missed_tp1_counterfactual_action_counts: "
        f"{summary.get('rising_missed_tp1_counterfactual_action_counts')}",
        f"- rising_missed_tp1_counterfactual_selector_reason_counts: "
        f"{summary.get('rising_missed_tp1_counterfactual_selector_reason_counts')}",
        f"- rising_missed_tp1_counterfactual_risk_counts: "
        f"{summary.get('rising_missed_tp1_counterfactual_risk_counts')}",
        f"- rising_missed_tp1_counterfactual_gross_label_counts: "
        f"{summary.get('rising_missed_tp1_counterfactual_gross_label_counts')}",
        f"- rising_missed_tp1_counterfactual_direct_target_first_count: "
        f"{summary.get('rising_missed_tp1_counterfactual_direct_target_first_count')}",
        f"- rising_missed_tp1_counterfactual_direct_target_first_unique_symbol_count: "
        f"{summary.get('rising_missed_tp1_counterfactual_direct_target_first_unique_symbol_count')}",
        f"- rising_missed_tp1_counterfactual_direct_target_first_source_quality_gap_count: "
        f"{summary.get('rising_missed_tp1_counterfactual_direct_target_first_source_quality_gap_count')}",
        f"- rising_missed_tp1_counterfactual_direct_target_first_selector_counts: "
        f"{summary.get('rising_missed_tp1_counterfactual_direct_target_first_selector_counts')}",
        f"- rising_missed_tp1_counterfactual_direct_target_first_ai_action_counts: "
        f"{summary.get('rising_missed_tp1_counterfactual_direct_target_first_ai_action_counts')}",
        f"- rising_missed_tp1_counterfactual_direct_target_first_row_export_count: "
        f"{summary.get('rising_missed_tp1_counterfactual_direct_target_first_row_export_count')}",
        f"- rising_missed_tp1_counterfactual_direct_target_first_row_omitted_count: "
        f"{summary.get('rising_missed_tp1_counterfactual_direct_target_first_row_omitted_count')}",
        f"- rising_missed_tp1_counterfactual_direct_target_first_row_export_truncated: "
        f"{summary.get('rising_missed_tp1_counterfactual_direct_target_first_row_export_truncated')}",
        f"- rising_missed_tp1_counterfactual_detail_row_export_count: "
        f"{summary.get('rising_missed_tp1_counterfactual_detail_row_export_count')}",
        f"- rising_missed_tp1_counterfactual_detail_row_omitted_count: "
        f"{summary.get('rising_missed_tp1_counterfactual_detail_row_omitted_count')}",
        f"- rising_missed_tp1_counterfactual_detail_row_export_truncated: "
        f"{summary.get('rising_missed_tp1_counterfactual_detail_row_export_truncated')}",
        f"- rising_missed_tp1_counterfactual_multi_horizon_coverage_counts: "
        f"{summary.get('rising_missed_tp1_counterfactual_multi_horizon_coverage_counts')}",
        f"- rising_missed_tp1_counterfactual_multi_horizon_outcome_counts: "
        f"{summary.get('rising_missed_tp1_counterfactual_multi_horizon_outcome_counts')}",
        f"- rising_missed_tp1_counterfactual_late_recovery_after_adverse_count: "
        f"{summary.get('rising_missed_tp1_counterfactual_late_recovery_after_adverse_count')}",
        f"- rising_missed_tp1_counterfactual_multi_horizon_by_effective_venue: "
        f"{summary.get('rising_missed_tp1_counterfactual_multi_horizon_by_effective_venue')}",
        f"- rising_missed_nxt_evaluation_count: "
        f"{summary.get('rising_missed_nxt_evaluation_count')}",
        f"- rising_missed_nxt_unique_symbol_count: "
        f"{summary.get('rising_missed_nxt_unique_symbol_count')}",
        f"- rising_missed_nxt_session_bucket_counts: "
        f"{summary.get('rising_missed_nxt_session_bucket_counts')}",
        f"- rising_missed_nxt_micro_state_counts: "
        f"{summary.get('rising_missed_nxt_micro_state_counts')}",
        f"- rising_missed_nxt_input_ready_count: "
        f"{summary.get('rising_missed_nxt_input_ready_count')}",
        f"- rising_missed_nxt_rest_quote_selected_count: "
        f"{summary.get('rising_missed_nxt_rest_quote_selected_count')}",
        f"- rising_missed_nxt_order_request_count: "
        f"{summary.get('rising_missed_nxt_order_request_count')}",
        f"- rising_missed_nxt_order_type_remap_count: "
        f"{summary.get('rising_missed_nxt_order_type_remap_count')}",
        f"- rising_missed_nxt_post_block_sampler_registered_count: "
        f"{summary.get('rising_missed_nxt_post_block_sampler_registered_count')}",
        f"- rising_missed_nxt_post_block_sampler_runtime_called_count: "
        f"{summary.get('rising_missed_nxt_post_block_sampler_runtime_called_count')}",
        f"- rising_missed_nxt_post_block_sampler_runtime_applied_count: "
        f"{summary.get('rising_missed_nxt_post_block_sampler_runtime_applied_count')}",
        f"- rising_missed_nxt_post_block_rest_fallback_runtime_called_count: "
        f"{summary.get('rising_missed_nxt_post_block_rest_fallback_runtime_called_count')}",
        f"- rising_missed_nxt_price_jump_recovery_runtime_called_count: "
        f"{summary.get('rising_missed_nxt_price_jump_recovery_runtime_called_count')}",
        f"- rising_missed_nxt_price_jump_recovery_runtime_applied_count: "
        f"{summary.get('rising_missed_nxt_price_jump_recovery_runtime_applied_count')}",
        f"- rising_missed_nxt_post_block_source_block_stage_counts: "
        f"{summary.get('rising_missed_nxt_post_block_source_block_stage_counts')}",
        f"- rising_missed_nxt_post_block_source_block_order_submitted_count: "
        f"{summary.get('rising_missed_nxt_post_block_source_block_order_submitted_count')}",
        f"- rising_missed_nxt_post_block_source_block_residual_submitted_qty: "
        f"{summary.get('rising_missed_nxt_post_block_source_block_residual_submitted_qty')}",
        f"- rising_missed_nxt_post_block_price_sample_count: "
        f"{summary.get('rising_missed_nxt_post_block_price_sample_count')}",
        f"- rising_missed_nxt_post_block_fresh_price_sample_count: "
        f"{summary.get('rising_missed_nxt_post_block_fresh_price_sample_count')}",
        f"- rising_missed_nxt_post_block_source_gap_sample_count: "
        f"{summary.get('rising_missed_nxt_post_block_source_gap_sample_count')}",
        f"- rising_missed_nxt_post_block_rest_fallback_attempted_count: "
        f"{summary.get('rising_missed_nxt_post_block_rest_fallback_attempted_count')}",
        f"- rising_missed_nxt_post_block_rest_fallback_applied_count: "
        f"{summary.get('rising_missed_nxt_post_block_rest_fallback_applied_count')}",
        f"- rising_missed_nxt_post_block_rest_budget_deferred_count: "
        f"{summary.get('rising_missed_nxt_post_block_rest_budget_deferred_count')}",
        f"- rising_missed_nxt_post_block_sampler_completed_count: "
        f"{summary.get('rising_missed_nxt_post_block_sampler_completed_count')}",
        f"- rising_missed_nxt_post_block_sampler_outcome_counts: "
        f"{summary.get('rising_missed_nxt_post_block_sampler_outcome_counts')}",
        f"- rising_missed_nxt_post_block_blocker_outcome_attribution: "
        f"{summary.get('rising_missed_nxt_post_block_blocker_outcome_attribution')}",
        f"- rising_missed_nxt_post_block_rolling_blocker_outcome_attribution: "
        f"{summary.get('rising_missed_nxt_post_block_rolling_blocker_outcome_attribution')}",
        f"- rising_missed_nxt_post_block_rolling_window: "
        f"{summary.get('rising_missed_nxt_post_block_rolling_window')}",
        f"- rising_missed_adverse_micro_recovery_observation_count: "
        f"{summary.get('rising_missed_adverse_micro_recovery_observation_count')}",
        f"- rising_missed_adverse_micro_recovery_checkpoint_counts: "
        f"{summary.get('rising_missed_adverse_micro_recovery_checkpoint_counts')}",
        f"- rising_missed_adverse_micro_recovery_outcome_counts: "
        f"{summary.get('rising_missed_adverse_micro_recovery_outcome_counts')}",
        f"- risky_micro_episode_observation_count: "
        f"{summary.get('risky_micro_episode_observation_count')}",
        f"- risky_micro_episode_status_counts: "
        f"{summary.get('risky_micro_episode_status_counts')}",
        f"- risky_micro_episode_reason_counts: "
        f"{summary.get('risky_micro_episode_reason_counts')}",
        f"- risky_micro_episode_source_category_counts: "
        f"{summary.get('risky_micro_episode_source_category_counts')}",
        f"- risky_micro_episode_unobserved_source_categories: "
        f"{summary.get('risky_micro_episode_unobserved_source_categories')}",
        f"- risky_micro_episode_source_coverage_complete: "
        f"{summary.get('risky_micro_episode_source_coverage_complete')}",
        f"- risky_micro_episode_source_instrumentation_complete: "
        f"{summary.get('risky_micro_episode_source_instrumentation_complete')}",
        f"- risky_micro_episode_natural_sample_absent_categories: "
        f"{summary.get('risky_micro_episode_natural_sample_absent_categories')}",
        f"- risky_micro_episode_outcome_join_status_counts: "
        f"{summary.get('risky_micro_episode_outcome_join_status_counts')}",
        f"- risky_micro_episode_matured_pending_outcome_gap_counts: "
        f"{summary.get('risky_micro_episode_matured_pending_outcome_gap_counts')}",
        f"- risky_micro_episode_horizon_observer_registration_status_counts: "
        f"{summary.get('risky_micro_episode_horizon_observer_registration_status_counts')}",
        f"- risky_micro_episode_horizon_observer_registered_candidate_count: "
        f"{summary.get('risky_micro_episode_horizon_observer_registered_candidate_count')}",
        f"- risky_micro_episode_horizon_observer_event_count: "
        f"{summary.get('risky_micro_episode_horizon_observer_event_count')}",
        f"- risky_micro_episode_horizon_observer_fresh_bbo_event_count: "
        f"{summary.get('risky_micro_episode_horizon_observer_fresh_bbo_event_count')}",
        f"- risky_micro_episode_instrumentation_gap_counts: "
        f"{summary.get('risky_micro_episode_instrumentation_gap_counts')}",
        f"- risky_micro_episode_tick_context_gap_reason_counts: "
        f"{summary.get('risky_micro_episode_tick_context_gap_reason_counts')}",
        f"- risky_micro_episode_resolved_eligible_episode_count: "
        f"{summary.get('risky_micro_episode_resolved_eligible_episode_count')}",
        f"- risky_micro_episode_recheck_diagnostic_resolved_count: "
        f"{summary.get('risky_micro_episode_recheck_diagnostic_resolved_count')}",
        f"- risky_micro_episode_recheck_diagnostic_ev_pct: "
        f"{summary.get('risky_micro_episode_recheck_diagnostic_ev_pct')}",
        f"- risky_micro_episode_daily_source_quality_adjusted_ev_pct: "
        f"{summary.get('risky_micro_episode_daily_source_quality_adjusted_ev_pct')}",
        f"- risky_micro_episode_ev_decision_authority: "
        f"{summary.get('risky_micro_episode_ev_decision_authority')}",
        f"- risky_micro_episode_rolling_decision: "
        f"{summary.get('risky_micro_episode_rolling_decision')}",
        f"- risky_micro_episode_rolling_resolved_episode_count: "
        f"{summary.get('risky_micro_episode_rolling_resolved_episode_count')}",
        f"- risky_micro_episode_rolling_unique_symbol_count: "
        f"{summary.get('risky_micro_episode_rolling_unique_symbol_count')}",
        f"- risky_micro_episode_rolling_trade_date_count: "
        f"{summary.get('risky_micro_episode_rolling_trade_date_count')}",
        f"- risky_micro_episode_rolling_diagnostic_ev_pct: "
        f"{summary.get('risky_micro_episode_rolling_diagnostic_ev_pct')}",
        f"- risky_micro_episode_source_quality_adjusted_ev_pct: "
        f"{summary.get('risky_micro_episode_source_quality_adjusted_ev_pct')}",
        f"- risky_micro_episode_promotion_review_sample_floor_met: "
        f"{summary.get('risky_micro_episode_promotion_review_sample_floor_met')}",
        f"- risky_micro_episode_resolved_opportunity_sample_floor_met: "
        f"{summary.get('risky_micro_episode_resolved_opportunity_sample_floor_met')}",
        f"- risky_micro_episode_filled_terminal_episode_count: "
        f"{summary.get('risky_micro_episode_filled_terminal_episode_count')}",
        f"- risky_micro_episode_filled_terminal_sample_floor_met: "
        f"{summary.get('risky_micro_episode_filled_terminal_sample_floor_met')}",
        f"- risky_micro_episode_entry_profile_summaries: "
        f"{summary.get('risky_micro_episode_entry_profile_summaries')}",
        f"- risky_micro_episode_real_order_promotion_allowed: "
        f"{summary.get('risky_micro_episode_real_order_promotion_allowed')}",
        f"- risky_micro_episode_real_order_promotion_blockers: "
        f"{summary.get('risky_micro_episode_real_order_promotion_blockers')}",
        f"- code_improvement_order_count: {summary.get('code_improvement_order_count')}",
        f"- consumer_readiness: {summary.get('consumer_readiness')}",
        "",
    ]
    if report.get("rising_missed_nxt_session_observation_rows"):
        lines.extend(["## NXT Session Observation", ""])
        for item in report.get("rising_missed_nxt_session_observation_rows") or []:
            lines.append(
                "- ts={ts} code={stock_code} name={stock_name} bucket={market_session_bucket} "
                "venue={effective_venue} eligible={nxt_eligible} micro={nxt_micro_state} "
                "0B_route={ws_0b_route} 0B_age_ms={ws_0b_age_ms} "
                "0D_route={ws_0d_route} 0D_age_ms={ws_0d_age_ms} "
                "input_ready={input_ready} quote_source={effective_price_source} "
                "candidate_allowed={candidate_allowed} reason={candidate_reason}".format(
                    **item
                )
            )
        lines.append("")
    if report.get("rising_missed_nxt_order_resolution_rows"):
        lines.extend(["## NXT Order Resolution", ""])
        for item in report.get("rising_missed_nxt_order_resolution_rows") or []:
            lines.append(
                "- ts={ts} code={stock_code} name={stock_name} evaluation_id={evaluation_id} "
                "requested_type={requested_order_type} effective_type={effective_order_type} "
                "exchange={effective_dmst_stex_tp} remapped={order_type_remapped} "
                "reason={order_type_remap_reason}".format(**item)
            )
        lines.append("")
    if report.get("rising_missed_nxt_post_block_price_sampler_rows"):
        lines.extend(["## NXT Post-block Price Sampler", ""])
        for item in report.get("rising_missed_nxt_post_block_price_sampler_rows") or []:
            lines.append(
                "- ts={ts} code={stock_code} name={stock_name} evaluation_id={evaluation_id} "
                "stage={stage} block_stage={source_block_stage} "
                "block_reason={source_block_reason} entry_price_source={entry_price_source} "
                "state={observation_state} source={price_source} "
                "reason={price_source_reason} price={current_price_observed} "
                "0B_age_ms={ws_0b_age_ms} 0B_item={ws_0b_item} 0B_route={ws_0b_route} "
                "rest_attempted={rest_fallback_attempted} "
                "rest_applied={rest_fallback_applied} "
                "rest_reason={rest_fallback_reason} "
                "move_pct={move_pct} first_hit_move_pct={first_hit_move_pct} "
                "mfe_after_block_pct={mfe_after_block_pct} "
                "mae_after_block_pct={mae_after_block_pct} outcome={outcome_label} "
                "quality={source_quality_state}".format(**item)
            )
        lines.append("")
    if report.get("rising_missed_adverse_micro_recovery_rows"):
        lines.extend(["## KRX Adverse-micro Recovery Observation", ""])
        for item in report.get("rising_missed_adverse_micro_recovery_rows") or []:
            lines.append(
                "- ts={ts} code={stock_code} tp1_evaluation={source_tp1_evaluation_id} "
                "stage={stage} checkpoint={checkpoint_sec} "
                "fresh={price_fresh} move_pct={move_pct} max={max_move_pct} "
                "min={min_move_pct} next_loop={next_scanner_loop_rechecked} "
                "reentry_allowed={reentry_candidate_allowed} recovered={recovery_observed} "
                "source={source_reason} raw_0B_route={raw_0b_route} outcome={outcome}".format(
                    **item
                )
            )
        lines.append("")
    if report.get("risky_micro_episode_source_candidate_rows"):
        lines.extend(["## Risky Micro Episode Source Candidates", ""])
        for item in report.get("risky_micro_episode_source_candidate_rows") or []:
            lines.append(
                "- ts={ts} code={stock_code} name={stock_name} status={status} "
                "reason={reason} policy={policy_version} profile={entry_profile} "
                "instrumentation_gap={instrumentation_gap} "
                "source_stage={source_stage} block={source_block_reason} "
                "origin={source_projection_origin} source_event={source_event_stage} "
                "venue={effective_venue} session={market_session_bucket} "
                "bbo={best_bid}/{best_ask} spread_bps={spread_bps} "
                "tick_accel={tick_acceleration_ratio} tick_span={tick_window_span_sec} "
                "tick_source={tick_context_source} "
                "positive_micro={positive_micro_support} adverse={adverse_micro_detected} "
                "large_sell={large_sell_detected} passive_entry={hypothetical_entry_price} "
                "target={hypothetical_target_price} adverse_price={hypothetical_adverse_price} "
                "target_bps={gross_target_bps} adverse_bps={adverse_limit_bps} "
                "ttl={passive_ttl_sec}s max_hold={max_hold_sec}s "
                "quantity_owner={quantity_owner} outcome_join={outcome_join_status} "
                "fill={fill_feasible}@{fill_price} exit={exit_price} net_bps={net_return_bps}".format(
                    **item
                )
            )
        lines.append("")
    if report.get("rising_missed_submit_lineage_rows"):
        lines.extend(
            [
                "## Rising Missed Submit Lineage",
                "",
            ]
        )
        for item in report.get("rising_missed_submit_lineage_rows") or []:
            lines.append(
                "- record_id={record_id} code={stock_code} name={stock_name} "
                "entry_submitted={entry_order_submitted} plan_count={order_plan_forced_count} "
                "leg_request_count={order_leg_request_count} leg_sent_count={order_leg_sent_count} "
                "bundle_count={order_bundle_submitted_count} primary_order_no={primary_order_no} "
                "planned_price={planned_order_price} submitted_price={submitted_order_price} "
                "reprice_block_count={entry_reprice_after_submit_blocked_count} "
                "reprice_reason={entry_reprice_after_submit_last_reason} "
                "cancel_confirmed_count={entry_order_cancel_confirmed_count} "
                "join={submit_lineage_join_method}".format(
                    **{
                        **item,
                        "primary_order_no": item.get("primary_order_no")
                        or item.get("order_no_list")
                        or "-",
                        "planned_order_price": item.get("planned_order_price") or "-",
                        "submitted_order_price": item.get("submitted_order_price")
                        or item.get("submitted_price_list")
                        or "-",
                        "entry_reprice_after_submit_last_reason": (
                            item.get("entry_reprice_after_submit_last_reason") or "-"
                        ),
                    }
                )
            )
        lines.append("")
    lines.extend(["## Submit Safety Blockers", ""])
    for item in report.get("submit_safety_blocker_rows") or []:
        lines.append(
            "- ts={ts} code={stock_code} name={stock_name} stage={stage} reason={reason} "
            "bucket={blocker_bucket} components={components} delta={price_delta_since_first_seen_pct} "
            "mfe_after={mfe_after_block_pct} mae_after={mae_after_block_pct} "
            "quote_age_sec={quote_age_sec} ai_action={ai_action} ai_score={ai_score} "
            "true_ofi={true_ofi_ewma} true_ofi_reason={true_ofi_reason} "
            "spread_bps={spread_bps} source_quality_gate={source_quality_gate} "
            "source_quality_state={source_quality_state} missing_fields={source_quality_missing_fields} "
            "micro_state={orderbook_micro_state} tick_profile={tick_speed_block_profile} "
            "tick_span_sec={tick_speed_window_span_sec} "
            "tick_accel={tick_speed_acceleration_ratio} "
            "absolute_5tick_sec={tick_speed_absolute_recent_5tick_seconds} "
            "absolute_samples={tick_speed_absolute_sample_count} "
            "absolute_relief_applied={tick_speed_absolute_relief_applied} "
            "absolute_relief_path={tick_speed_absolute_relief_path}".format(**item)
        )
    lines.extend(["", "## Blocked Zero Quantity Counterfactual", ""])
    for item in report.get("blocked_zero_qty_counterfactual_rows") or []:
        lines.append(
            "- ts={ts} code={stock_code} name={stock_name} reason={reason} "
            "entry_ask={block_executable_best_ask} entry_bbo_source={executable_bbo_source} "
            "predecessor_age_ms={executable_bbo_predecessor_age_ms} "
            "pre_cap_qty={quantity_pre_cap_qty} effective_qty={quantity_effective_qty} "
            "binding_caps={quantity_binding_caps} floor_cap_conflict={one_share_floor_position_cap_conflict} "
            "mfe_after={mfe_after_block_pct} mae_after={mae_after_block_pct} "
            "first_hit={post_block_first_hit} first_hit_elapsed_sec={post_block_first_hit_elapsed_sec} "
            "decision_authority={decision_authority}".format(**item)
        )
    lines.extend(
        [
            "",
            "## Backoff Opportunity Audit",
            "",
        ]
    )
    for item in report.get("backoff_opportunity_audit_rows") or []:
        lines.append(
            "- code={stock_code} name={stock_name} last_backoff={last_backoff_ts} "
            "reason={last_backoff_reason} source={last_backoff_source} "
            "max_delta_after={max_delta_after_last_backoff_pct} "
            "mark_candidate={mark_price_opportunity_candidate} "
            "entry_ask={entry_executable_best_ask} "
            "executable_mfe={max_executable_bid_move_pct} "
            "executable_mae={min_executable_bid_move_pct} "
            "executable_sampled_first_hit={executable_sampled_first_hit} "
            "executable_source_quality={backoff_executable_source_quality_pass} "
            "recovered_eval={recovered_eval_after_last_backoff} "
            "potential_loss={potential_backoff_opportunity_loss} "
            "classification={backoff_opportunity_classification} "
            "state={backoff_observation_state} age_sec={last_backoff_observation_age_sec} "
            "pass_after={fast_pass_after_last_backoff_count} "
            "promoted_after={promoted_after_last_backoff_count} "
            "heavy_after={heavy_eval_after_last_backoff_count}".format(**item)
        )
    lines.extend(
        [
            "",
            "## Latency False Negative Review",
            "",
        ]
    )
    for item in report.get("latency_false_negative_review_rows") or []:
        lines.append(
            "- ts={ts} code={stock_code} name={stock_name} review_bucket={review_bucket} "
            "blocker_bucket={blocker_bucket} mfe_after={mfe_after_block_pct} "
            "mae_after={mae_after_block_pct} spread_bps={spread_bps} "
            "true_ofi={true_ofi_ewma} true_ofi_reason={true_ofi_reason} "
            "samples={true_ofi_sample_count} ws_age_ms={ws_age_ms} "
            "decision_authority={decision_authority}".format(**item)
        )
    lines.extend(
        [
            "",
            "## Latency False Negative Canary Candidates",
            "",
        ]
    )
    for item in report.get("latency_false_negative_canary_candidate_rows") or []:
        lines.append(
            "- ts={ts} code={stock_code} name={stock_name} cohort={canary_cohort} "
            "grade={canary_grade} score={canary_primary_review_score_pct} "
            "mfe_after={mfe_after_block_pct} mae_after={mae_after_block_pct} "
            "spread_bps={spread_bps} true_ofi={true_ofi_ewma} samples={true_ofi_sample_count} "
            "ws_age_ms={ws_age_ms} reason={canary_reason} next_action={canary_next_action} "
            "runtime_dynamic_age_state={runtime_dynamic_age_band_provenance_state} "
            "decision_authority={decision_authority}".format(**item)
        )
    lines.extend(
        [
            "",
            "## Latency False Negative Rolling Attribution",
            "",
        ]
    )
    for item in report.get("latency_false_negative_rolling_attribution_rows") or []:
        lines.append(
            "- venue={effective_venue} session={market_session_bucket} "
            "cohort={canary_cohort} samples={completed_sample_count} "
            "ready_rate={ready_for_recheck_rate_pct} "
            "low_adverse_rate={low_adverse_opportunity_rate_pct} "
            "avg_mfe={equal_weight_avg_mfe_after_block_pct} "
            "avg_mae={equal_weight_avg_mae_after_block_pct} "
            "assessment={rolling_assessment} next_action={next_action} "
            "decision_authority={decision_authority}".format(**item)
        )
    lines.extend(["", "## Dynamic-age Post-apply Attribution", ""])
    for item in report.get("dynamic_age_post_apply_attribution_rows") or []:
        horizons = ";".join(
            f"{key}:n={value.get('event_count')}/mfe={value.get('mfe_pct')}/mae={value.get('mae_pct')}"
            for key, value in (item.get("horizons") or {}).items()
        )
        lines.append(
            "- ts={ts} code={stock_code} name={stock_name} venue={effective_venue} "
            "source_stage={dynamic_age_source_stage} terminal={downstream_terminal_stage} "
            "entry_ask={entry_executable_best_ask} first_hit={first_hit} "
            "first_hit_elapsed_sec={first_hit_elapsed_sec} order_submitted={actual_order_submitted} "
            "horizons={horizons} decision_authority={decision_authority}".format_map(
                {**item, "horizons": horizons or "-"}
            )
        )
    lines.extend(["", "## TP1 Counterfactual First-hit Labels", ""])
    for item in (
        report.get("rising_missed_tp1_counterfactual_first_hit_label_rows") or []
    ):
        lines.append(
            "- ts={candidate_ts} code={stock_code} name={stock_name} "
            "selector={selector_reason} action={counterfactual_action} risks={counterfactual_risks} "
            "label={gross_first_hit_label} entry={entry_price} source={effective_price_source} "
            "ws_age_ms={ws_quote_age_ms} rest_age_ms={rest_quote_age_ms} gap_bps={ws_rest_gap_bps} "
            "spread={spread_ratio} true_ofi={true_ofi_ewma} pressure={pressure_ewma} "
            "depth={depth_imbalance_ewma} tick_accel={tick_acceleration} "
            "micro_state={micro_source_state}".format(**item)
        )
    lines.extend(["", "## TP1 Direct Target-first Attribution", ""])
    for item in (
        report.get("rising_missed_tp1_counterfactual_direct_target_first_rows") or []
    ):
        lines.append(
            "- ts={candidate_ts} code={stock_code} name={stock_name} "
            "venue={effective_venue} session={market_session_bucket} "
            "selector={selector_reason} ai_action={ai_action} "
            "entry={entry_price} entry_source={entry_price_source} "
            "first_hit_ts={first_hit_ts} first_hit_move_pct={first_hit_move_pct} "
            "first_hit_source={first_hit_price_source} "
            "decision_authority={decision_authority}".format(**item)
        )
    lines.extend(["", "## TP1 Counterfactual Multi-horizon Coverage", ""])
    for item in (
        report.get("rising_missed_tp1_counterfactual_first_hit_label_rows") or []
    ):
        horizons = ";".join(
            "{horizon_min}m:{outcome_label}/{source_quality_state}/n={observed_price_event_count}".format(
                **measurement
            )
            for measurement in item.get("post_block_horizon_measurements") or []
        )
        recovery = item.get("post_block_late_recovery_after_adverse") or {}
        lines.append(
            "- ts={ts} code={code} name={name} horizons={horizons} "
            "late_recovery_after_adverse={late_recovery} "
            "recovery_horizon_min={recovery_horizon} reason={recovery_reason}".format(
                ts=item.get("candidate_ts"),
                code=item.get("stock_code"),
                name=item.get("stock_name"),
                horizons=horizons or "-",
                late_recovery=recovery.get("detected", False),
                recovery_horizon=recovery.get("first_recovery_horizon_min") or "-",
                recovery_reason=recovery.get("reason") or "-",
            )
        )
    lines.extend(
        [
            "",
            "## First Touch Regression",
            "",
        ]
    )
    for item in report.get("first_touch_regression_rows") or []:
        blocker_counts = item.get("blocker_counts_before_first_touch") or {}
        top_blockers = ",".join(
            f"{key}={value}" for key, value in list(blocker_counts.items())[:4]
        )
        display_item = {
            **item,
            "final_profit_rate": item.get("final_profit_rate"),
            "first_touch_shadow_cap1_decision": item.get(
                "first_touch_shadow_cap1_decision", "-"
            ),
            "first_touch_avgdown_decision_reason": item.get(
                "first_touch_avgdown_decision_reason"
            )
            or "-",
            "top_blockers": top_blockers,
        }
        lines.append(
            "- record_id={record_id} code={stock_code} name={stock_name} label={first_touch_regression_label} "
            "entry_submitted={entry_order_submitted} avgdown_submitted={first_touch_avg_down_submitted} "
            "touch_profit={first_touch_profit_rate} "
            "touch_peak={first_touch_peak_profit} touch_ai={first_touch_ai_score} "
            "final_profit={final_profit_rate} entry_submit_count={entry_order_submitted_count} "
            "avgdown_submitted_count={avg_down_submitted_event_count} "
            "runtime_decision={first_touch_avgdown_decision_reason} shadow_cap1={first_touch_shadow_cap1_decision} "
            "max_avg_down={max_avg_down_count} blockers={top_blockers}".format(
                **display_item
            )
        )
    lines.extend(["", "## Records", ""])
    for item in report.get("records") or []:
        lines.append(
            "- record_id={record_id} code={stock_code} name={stock_name} label={feedback_label} "
            "avg_down={max_avg_down_count} latest_profit={latest_profit_rate} min_profit={min_profit_seen} "
            "max_profit={max_profit_seen} latest_gate={latest_gate_reason}".format(
                **item
            )
        )
    output_md.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build rising missed intraday feedback report."
    )
    parser.add_argument("--target-date", default=datetime.now(KST).strftime("%Y-%m-%d"))
    parser.add_argument("--pipeline-path", type=Path)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--generated-at")
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args(argv)
    report = build_report(
        args.target_date,
        pipeline_path=args.pipeline_path,
        generated_at=args.generated_at,
    )
    default_json, default_md = _default_output_paths(args.target_date)
    output_json = args.output_json or default_json
    output_md = args.output_md or default_md
    write_outputs(report, output_json=output_json, output_md=output_md)
    if args.print_summary:
        print(
            json.dumps(
                {
                    "output_json": str(output_json),
                    "output_md": str(output_md),
                    **report["summary"],
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

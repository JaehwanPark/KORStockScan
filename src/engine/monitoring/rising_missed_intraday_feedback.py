from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.utils.jsonl_io import existing_or_gzip_path, iter_jsonl

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PIPELINE_EVENTS_DIR = PROJECT_ROOT / "data" / "pipeline_events"
REPORT_DIR = PROJECT_ROOT / "data" / "report" / "rising_missed_intraday_feedback"
KST = timezone(timedelta(hours=9))
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
TP1_GROSS_TARGET_PCT = 1.30
TP1_ADVERSE_STOP_PCT = -0.70
TP1_COST_RESERVE_PCT = 0.30
TP1_NET_TARGET_PCT = 1.00
TP1_LABEL_HORIZON_SEC = 20 * 60
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
        return datetime.fromisoformat(text)
    except ValueError:
        return None


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


def _decision_stage_current_price_unusable(row: dict[str, Any], source: str) -> bool:
    return bool(
        source in {"current_price", "current_price_observed"}
        and str(row.get("stage") or "")
        in {"budget_pass", "orderbook_stability_observed"}
    )


def _tp1_observation_price(row: dict[str, Any]) -> tuple[float | None, str]:
    fields = _fields(row)
    is_tp1_evaluation = bool(
        fields.get("rising_missed_tp1_evaluation_id")
        or fields.get("rising_missed_tp1_candidate_reason")
        or str(row.get("stage") or "")
        == "rising_missed_tp1_counterfactual_submit_safety"
    )
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


def _submit_safety_block_row(row: dict[str, Any]) -> dict[str, Any]:
    fields = _fields(row)
    reason, bucket, components = _classify_submit_safety_block(row)
    price = _event_price(row)
    quote_age = _quote_age_ms(fields)
    return {
        "ts": _event_ts(row),
        "stage": row.get("stage"),
        "record_id": str(row.get("record_id") or "").strip(),
        "stock_code": _event_code(row),
        "stock_name": _event_name(row),
        "reason": reason,
        "blocker_bucket": bucket,
        "components": components,
        "price_delta_since_first_seen_pct": _event_delta_pct(row),
        "block_price": price,
        "mfe_after_block_pct": None,
        "mae_after_block_pct": None,
        "post_block_price_event_count": 0,
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
        "source_quality_gate": fields.get("source_quality_gate"),
        "source_quality_state": fields.get(
            "weak_ai_micro_entry_block_source_quality_state"
        ),
        "source_quality_missing_fields": _split_csv_values(
            fields.get("weak_ai_micro_entry_block_missing_fields")
        ),
        "orderbook_micro_state": fields.get("orderbook_micro_state"),
        "orderbook_micro_reason": fields.get("orderbook_micro_reason"),
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


def _update_block_mfe_mae(block: dict[str, Any], price: float | None) -> None:
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


def _build_submit_safety_and_backoff_audit(
    pipeline_path: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
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
        price = _tp1_observation_price(row)[0]
        delta = _event_delta_pct(row)

        for block in open_submit_blocks_by_code.get(code, []):
            _update_block_mfe_mae(block, price)

        if code in backoff_by_code:
            backoff = backoff_by_code[code]
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
            block = _submit_safety_block_row(row)
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
            backoff_by_code[code] = {
                "stock_code": code,
                "stock_name": _event_name(row),
                "last_backoff_ts": ts,
                "last_backoff_reason": reason,
                "last_backoff_source": source,
                "last_backoff_delta_pct": delta,
                "max_delta_after_last_backoff_pct": delta,
                "max_delta_after_last_backoff_ts": ts if delta is not None else None,
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
        item["potential_backoff_opportunity_loss"] = bool(
            max_delta is not None
            and max_delta >= 1.0
            and not recovered
            and age_sec is not None
            and age_sec >= 180.0
        )

    summary = {
        "submit_safety_block_count": len(submit_blocks),
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
    }
    return summary, submit_blocks, audit_rows


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
                "review_bucket": review_bucket,
                "review_reason": "latency_submit_safety_block_high_mfe_low_mae",
                "blocker_bucket": blocker_bucket,
                "reason": block.get("reason"),
                "components": block.get("components"),
                "block_price": block.get("block_price"),
                "mfe_after_block_pct": mfe,
                "mae_after_block_pct": mae,
                "post_block_price_event_count": block.get(
                    "post_block_price_event_count"
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
    for item in review_rows:
        mfe = _safe_float(item.get("mfe_after_block_pct"))
        mae = _safe_float(item.get("mae_after_block_pct"))
        if mfe is None or mae is None:
            continue
        review_score = round(mfe - abs(mae), 4)
        cohort = _latency_canary_cohort(item)
        grade, reason = _latency_canary_grade(item, review_score)
        cohort_counts[cohort] += 1
        grade_counts[grade] += 1
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
                    "bounded_latency_remeasure_enqueue"
                    if grade == "ready_for_recheck"
                    else "source_only_accumulate_more_false_negative_samples"
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
        "latency_false_negative_canary_min_review_score_pct": LATENCY_CANARY_MIN_REVIEW_SCORE_PCT,
        "latency_false_negative_canary_true_ofi_min_sample_count": LATENCY_CANARY_TRUE_OFI_MIN_SAMPLE_COUNT,
        "latency_false_negative_canary_fresh_ws_max_age_ms": LATENCY_CANARY_FRESH_WS_MAX_AGE_MS,
        "latency_false_negative_canary_spread_only_max_spread_bps": LATENCY_CANARY_SPREAD_ONLY_MAX_SPREAD_BPS,
    }
    return summary, rows


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


def _build_tp1_first_hit_labels(
    pipeline_path: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    events = list(iter_jsonl(pipeline_path))
    observation_watermark = max(
        (
            timestamp
            for row in events
            if (timestamp := _tp1_label_timestamp(_event_ts(row))) is not None
        ),
        default=None,
    )
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
        entry_price, entry_price_source = _tp1_observation_price(candidate)
        label = "input_unavailable"
        first_hit_ts = None
        first_hit_move_pct = None
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
                "evaluation_id": evaluation_id or None,
                "entry_price": entry_price,
                "entry_price_source": entry_price_source,
                "gross_first_hit_label": label,
                "first_hit_ts": first_hit_ts,
                "first_hit_move_pct": (
                    round(first_hit_move_pct, 4)
                    if first_hit_move_pct is not None
                    else None
                ),
                "max_move_pct_within_20m": (
                    round(max_move_pct, 4) if max_move_pct is not None else None
                ),
                "min_move_pct_within_20m": (
                    round(min_move_pct, 4) if min_move_pct is not None else None
                ),
                "observed_price_event_count": observed_event_count,
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
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    events = list(iter_jsonl(pipeline_path))
    observation_watermark = max(
        (
            timestamp
            for row in events
            if (timestamp := _tp1_label_timestamp(_event_ts(row))) is not None
        ),
        default=None,
    )
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
        entry_price, entry_price_source = _tp1_observation_price(candidate)
        label = "input_unavailable"
        first_hit_ts = None
        first_hit_move_pct = None
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

        labels.append(
            {
                "record_id": record_id,
                "stock_code": code,
                "stock_name": _event_name(candidate),
                "candidate_ts": candidate_ts_text,
                "evaluation_id": evaluation_id or None,
                "selector_reason": fields.get("selector_reason"),
                "selector_deferred": _boolish(fields.get("selector_deferred")),
                "counterfactual_action": fields.get(
                    "rising_missed_tp1_counterfactual_submit_safety_action"
                ),
                "counterfactual_risks": _split_csv_values(
                    fields.get("rising_missed_tp1_counterfactual_submit_safety_risks")
                ),
                **_tp1_counterfactual_decision_context(fields),
                "entry_price": entry_price,
                "entry_price_source": entry_price_source,
                "gross_first_hit_label": label,
                "first_hit_ts": first_hit_ts,
                "first_hit_move_pct": (
                    round(first_hit_move_pct, 4)
                    if first_hit_move_pct is not None
                    else None
                ),
                "max_move_pct_within_20m": (
                    round(max_move_pct, 4) if max_move_pct is not None else None
                ),
                "min_move_pct_within_20m": (
                    round(min_move_pct, 4) if min_move_pct is not None else None
                ),
                "observed_price_event_count": observed_event_count,
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
        if evaluation_id and session_bucket.startswith("nxt_"):
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
                effective_venue = str(
                    fields.get("rising_missed_effective_venue") or "unknown"
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
                        "decision_authority": "observe_only_no_runtime_mutation",
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                        "forbidden_uses": FORBIDDEN_USES,
                    }
                )
        if (
            stage == "order_leg_request"
            and evaluation_id
            and session_bucket.startswith("nxt_")
        ):
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
        if stage.startswith("rising_missed_nxt_post_block_"):
            if evaluation_id:
                sampler_evaluations.add(evaluation_id)
            sampler_stage_counts[stage] += 1
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
                    "observation_state": fields.get(
                        "rising_missed_nxt_post_block_price_observation_state"
                    ),
                    "price_source": fields.get(
                        "rising_missed_nxt_post_block_price_source"
                    ),
                    "price_source_reason": fields.get(
                        "rising_missed_nxt_post_block_price_source_reason"
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
                    "fresh_sample": _boolish(
                        fields.get("rising_missed_nxt_post_block_fresh_sample")
                    ),
                    "sample_attempt_count": _safe_int(
                        fields.get("rising_missed_nxt_post_block_sample_attempt_count")
                    ),
                    "fresh_sample_count": _safe_int(
                        fields.get("rising_missed_nxt_post_block_fresh_sample_count")
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
            "rising_missed_nxt_post_block_sampler_registered_count": sampler_stage_counts.get(
                "rising_missed_nxt_post_block_sampler_registered", 0
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
            "rising_missed_nxt_post_block_sampler_completed_count": sampler_stage_counts.get(
                "rising_missed_nxt_post_block_price_sampler_completed", 0
            ),
            "rising_missed_nxt_post_block_sampler_outcome_counts": [
                {"outcome_label": key, "count": value}
                for key, value in sampler_outcome_counts.most_common()
            ],
        },
        evaluation_rows,
        order_rows,
        sampler_rows,
    )


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
    submit_backoff_summary, submit_safety_rows, backoff_audit_rows = (
        _build_submit_safety_and_backoff_audit(pipeline_path)
    )
    latency_false_negative_summary, latency_false_negative_rows = (
        _build_latency_false_negative_review(submit_safety_rows)
    )
    latency_canary_summary, latency_canary_rows = (
        _build_latency_false_negative_canary_candidates(latency_false_negative_rows)
    )
    tp1_label_summary, tp1_label_rows = _build_tp1_first_hit_labels(pipeline_path)
    tp1_counterfactual_summary, tp1_counterfactual_rows = (
        _build_tp1_counterfactual_submit_safety(pipeline_path)
    )
    tp1_counterfactual_label_summary, tp1_counterfactual_label_rows = (
        _build_tp1_counterfactual_first_hit_labels(pipeline_path)
    )
    (
        nxt_session_summary,
        nxt_session_rows,
        nxt_order_rows,
        nxt_post_block_sampler_rows,
    ) = _build_nxt_session_observation(pipeline_path)
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
                "source_quality_gate": "pipeline_event_submit_safety_fields_with_quote_ai_micro_provenance",
                "forbidden_uses": FORBIDDEN_USES,
            },
            "rising_missed_backoff_opportunity_audit": {
                "metric_role": "source_only_backoff_opportunity_audit",
                "decision_authority": "source_only_backoff_opportunity_audit",
                "window_policy": "same_day_intraday_pipeline_events_continuously_updated",
                "sample_floor": "1_fast_precheck_budget_reallocated_event",
                "primary_decision_metric": "potential_backoff_opportunity_loss_count",
                "source_quality_gate": "code_joined_fast_precheck_backoff_and_later_runtime_observation_events",
                "forbidden_uses": FORBIDDEN_USES,
            },
            "rising_missed_latency_false_negative_review": {
                "metric_role": "source_only_latency_false_negative_review",
                "decision_authority": "source_only_latency_false_negative_review",
                "window_policy": "same_day_intraday_pipeline_events_continuously_updated",
                "sample_floor": "1_latency_submit_safety_block_with_high_mfe_low_mae",
                "primary_decision_metric": "latency_false_negative_review_count",
                "source_quality_gate": (
                    "submit_safety_blocker_rows_with_post_block_mfe_mae_and_latency_micro_provenance"
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
                    "latency_false_negative_review_rows_with_spread_true_ofi_ws_age_and_post_block_mfe_mae"
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
            "rising_missed_nxt_session_observation": {
                "metric_role": "source_quality_gate",
                "decision_authority": "observe_only_no_runtime_mutation",
                "window_policy": "same_day_nxt_session_tp1_and_order_events",
                "sample_floor": "1_nxt_session_rising_missed_tp1_evaluation",
                "primary_decision_metric": "nxt_session_micro_and_fillability_distribution",
                "source_quality_gate": (
                    "absolute_0b_0d_receive_ts_actual_ws_item_route_and_effective_order_resolution"
                ),
                "forbidden_uses": FORBIDDEN_USES,
            },
            "rising_missed_nxt_post_block_price_sampler": {
                "metric_role": "source_quality_gate",
                "decision_authority": "source_only_nxt_post_block_price_observation",
                "window_policy": "nxt_selector_block_or_defer_bounded_20m",
                "sample_floor": "2_fresh_absolute_ws_0b_nxt_price_samples",
                "primary_decision_metric": "gross_1.30_first_before_adverse_0.70",
                "source_quality_gate": (
                    "fresh_absolute_0b_receive_ts_and_actual_nxt_item_route"
                ),
                "forbidden_uses": FORBIDDEN_USES,
            },
        },
        "source_paths": {"pipeline_events": str(resolved_pipeline_path)},
        "source_quality": {
            "status": source_quality_status,
            "pipeline_events_exists": resolved_pipeline_path.exists(),
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
            **tp1_label_summary,
            **tp1_counterfactual_summary,
            **tp1_counterfactual_label_summary,
            **nxt_session_summary,
            "code_improvement_order_count": len(code_improvement_orders),
        },
        "records": rows[:100],
        "rising_missed_submit_lineage_rows": submit_lineage_rows[:200],
        "first_touch_regression_rows": first_touch_rows[:200],
        "submit_safety_blocker_rows": submit_safety_rows[:200],
        "backoff_opportunity_audit_rows": backoff_audit_rows[:200],
        "latency_false_negative_review_rows": latency_false_negative_rows[:200],
        "latency_false_negative_canary_candidate_rows": latency_canary_rows[:200],
        "rising_missed_tp1_first_hit_label_rows": tp1_label_rows[:200],
        "rising_missed_tp1_counterfactual_submit_safety_rows": tp1_counterfactual_rows[
            :200
        ],
        "rising_missed_tp1_counterfactual_first_hit_label_rows": tp1_counterfactual_label_rows[
            :200
        ],
        "rising_missed_nxt_session_observation_rows": nxt_session_rows[:200],
        "rising_missed_nxt_order_resolution_rows": nxt_order_rows[:200],
        "rising_missed_nxt_post_block_price_sampler_rows": nxt_post_block_sampler_rows[
            -200:
        ],
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
        f"- rising_missed_nxt_post_block_price_sample_count: "
        f"{summary.get('rising_missed_nxt_post_block_price_sample_count')}",
        f"- rising_missed_nxt_post_block_fresh_price_sample_count: "
        f"{summary.get('rising_missed_nxt_post_block_fresh_price_sample_count')}",
        f"- rising_missed_nxt_post_block_source_gap_sample_count: "
        f"{summary.get('rising_missed_nxt_post_block_source_gap_sample_count')}",
        f"- rising_missed_nxt_post_block_sampler_completed_count: "
        f"{summary.get('rising_missed_nxt_post_block_sampler_completed_count')}",
        f"- rising_missed_nxt_post_block_sampler_outcome_counts: "
        f"{summary.get('rising_missed_nxt_post_block_sampler_outcome_counts')}",
        f"- code_improvement_order_count: {summary.get('code_improvement_order_count')}",
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
                "stage={stage} state={observation_state} source={price_source} "
                "reason={price_source_reason} price={current_price_observed} "
                "0B_age_ms={ws_0b_age_ms} 0B_item={ws_0b_item} 0B_route={ws_0b_route} "
                "move_pct={move_pct} first_hit_move_pct={first_hit_move_pct} "
                "mfe_after_block_pct={mfe_after_block_pct} "
                "mae_after_block_pct={mae_after_block_pct} outcome={outcome_label} "
                "quality={source_quality_state}".format(**item)
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
            "micro_state={orderbook_micro_state}".format(**item)
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
            "recovered_eval={recovered_eval_after_last_backoff} "
            "potential_loss={potential_backoff_opportunity_loss} "
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
            "decision_authority={decision_authority}".format(**item)
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

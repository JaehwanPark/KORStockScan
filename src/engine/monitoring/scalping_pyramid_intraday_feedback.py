from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.utils.constants import DATA_DIR, TRADING_RULES
from src.utils.jsonl_io import existing_or_gzip_path, iter_jsonl

KST = timezone(timedelta(hours=9))
REPORT_TYPE = "scalping_pyramid_intraday_feedback"
PIPELINE_EVENTS_DIR = DATA_DIR / "pipeline_events"
REPORT_DIR = DATA_DIR / "report" / REPORT_TYPE
FORBIDDEN_USES = [
    "intraday_threshold_mutation",
    "intraday_runtime_apply",
    "hard_safety_relaxation",
    "broker_guard_bypass",
    "order_guard_relaxation",
    "stale_quote_bypass",
    "cooldown_bypass",
    "quantity_guard_relaxation",
    "position_cap_release",
    "provider_route_change",
    "bot_restart",
    "real_execution_quality_approval",
]


def _safe_float(value: Any, default: float | None = None) -> float | None:
    if value in (None, "", "-"):
        return default
    try:
        return float(str(value).replace(",", "").replace("+", "").replace("%", ""))
    except (TypeError, ValueError):
        return default


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _optional_boolish(value: Any) -> bool | None:
    if value in (None, "", "-"):
        return None
    return _boolish(value)


def _pyramid_min_profit_pct() -> float:
    return float(getattr(TRADING_RULES, "SCALPING_PYRAMID_MIN_PROFIT_PCT", 1.5) or 1.5)


def _fields(row: dict[str, Any]) -> dict[str, Any]:
    fields = row.get("fields")
    return fields if isinstance(fields, dict) else {}


def _pipeline_path(target_date: str) -> Path:
    return PIPELINE_EVENTS_DIR / f"pipeline_events_{target_date}.jsonl"


def _default_output_paths(target_date: str) -> tuple[Path, Path]:
    return (
        REPORT_DIR / f"{REPORT_TYPE}_{target_date}.json",
        REPORT_DIR / f"{REPORT_TYPE}_{target_date}.md",
    )


def _record_key(row: dict[str, Any], fields: dict[str, Any]) -> str:
    record_id = str(row.get("record_id") or fields.get("record_id") or "").strip()
    if record_id:
        return f"record:{record_id}"
    code = str(row.get("stock_code") or fields.get("stock_code") or "").strip()
    return f"code:{code}" if code else ""


def _is_one_share_event(row: dict[str, Any]) -> bool:
    fields = _fields(row)
    return (
        str(row.get("stage") or "") == "rising_missed_one_share_entry"
        or str(fields.get("forced_entry_reason") or "")
        == "rising_missed_one_share_entry"
        or _boolish(fields.get("rising_missed_one_share_entry_forced"))
    )


def _one_share_record(row: dict[str, Any]) -> dict[str, Any]:
    fields = _fields(row)
    return {
        "record_id": str(row.get("record_id") or "").strip(),
        "stock_code": row.get("stock_code"),
        "stock_name": row.get("stock_name"),
        "first_one_share_ts": row.get("emitted_at"),
        "first_observed_ts": row.get("emitted_at"),
        "source_stage": row.get("stage"),
        "source_signature": fields.get("source_signature"),
        "position_tag": fields.get("position_tag") or fields.get("entry_position_tag"),
        "rising_missed_class": fields.get("rising_missed_class"),
        "scanner_promotion_reason": fields.get("scanner_promotion_reason"),
        "one_share_event": True,
        "forced_entry_qty": max(
            1, int(_safe_float(fields.get("forced_entry_qty"), 1.0) or 1.0)
        ),
        "scale_in_arm": "PYRAMID",
        "scale_in_blocker_reason": "one_share_pyramid_no_opportunity_seen",
        "scale_in_blocker_namespace": "ONE_SHARE_PYRAMID_BACKTEST",
    }


def _pyramid_blocked_record(row: dict[str, Any]) -> dict[str, Any] | None:
    fields = _fields(row)
    stage = str(row.get("stage") or "")
    if stage != "pyramid_blocked_reason":
        return None
    arm = str(fields.get("scale_in_arm") or "").upper()
    if arm and arm != "PYRAMID":
        return None
    return {
        "record_id": str(row.get("record_id") or "").strip(),
        "stock_code": row.get("stock_code"),
        "stock_name": row.get("stock_name"),
        "first_observed_ts": row.get("emitted_at"),
        "source_stage": stage,
        "source_signature": fields.get("source_signature"),
        "position_tag": fields.get("position_tag") or fields.get("entry_position_tag"),
        "scale_in_arm": "PYRAMID",
        "scale_in_blocker_reason": fields.get("scale_in_blocker_reason")
        or fields.get("blocked_reason"),
        "scale_in_blocker_namespace": fields.get("scale_in_blocker_namespace"),
        "profit_rate": _safe_float(fields.get("profit_rate")),
        "peak_profit": _safe_float(fields.get("peak_profit")),
        "current_ai_score": _safe_float(
            fields.get("current_ai_score") or fields.get("ai_score")
        ),
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
        "minute_candle_window_fresh": _optional_boolish(
            fields.get("minute_candle_window_fresh")
        ),
        "min_profit_pct": _safe_float(fields.get("min_profit_pct")),
        "min_ai_score": _safe_float(fields.get("min_ai_score")),
        "min_buy_pressure": _safe_float(fields.get("min_buy_pressure")),
        "min_tick_accel": _safe_float(fields.get("min_tick_accel")),
        "max_micro_vwap_bps": _safe_float(fields.get("max_micro_vwap_bps")),
        "pyramid_runtime_prior_status": fields.get("pyramid_runtime_prior_status"),
        "pyramid_runtime_prior_signal": fields.get("pyramid_runtime_prior_signal"),
    }


def _is_pyramid_submit_event(row: dict[str, Any]) -> bool:
    stage = str(row.get("stage") or "").lower()
    if not any(token in stage for token in ("submit", "submitted", "receipt")):
        return False
    fields = _fields(row)
    text = json.dumps({"stage": stage, "fields": fields}, ensure_ascii=False).lower()
    return "pyramid" in text


def _pyramid_submit_record(row: dict[str, Any]) -> dict[str, Any]:
    fields = _fields(row)
    return {
        "record_id": str(row.get("record_id") or "").strip(),
        "stock_code": row.get("stock_code"),
        "stock_name": row.get("stock_name"),
        "first_observed_ts": row.get("emitted_at"),
        "source_stage": row.get("stage"),
        "source_signature": fields.get("source_signature"),
        "position_tag": fields.get("position_tag") or fields.get("entry_position_tag"),
        "scale_in_arm": "PYRAMID",
        "scale_in_blocker_reason": "pyramid_submitted",
        "scale_in_blocker_namespace": "PYRAMID_SUBMITTED",
        "profit_rate": _safe_float(fields.get("profit_rate")),
        "peak_profit": _safe_float(fields.get("peak_profit")),
        "current_ai_score": _safe_float(
            fields.get("current_ai_score") or fields.get("ai_score")
        ),
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
        "minute_candle_window_fresh": _optional_boolish(
            fields.get("minute_candle_window_fresh")
        ),
        "pyramid_submit_seen": True,
        "pyramid_submit_ts": row.get("emitted_at"),
    }


def _update_snapshot(item: dict[str, Any], row: dict[str, Any]) -> None:
    fields = _fields(row)
    profit_rate = _safe_float(fields.get("profit_rate"))
    item["latest_snapshot_ts"] = row.get("emitted_at")
    item["latest_stage"] = row.get("stage")
    item["latest_profit_rate"] = profit_rate
    item["latest_peak_profit"] = _safe_float(fields.get("peak_profit"))
    if profit_rate is not None:
        item["min_profit_seen"] = (
            profit_rate
            if item.get("min_profit_seen") is None
            else min(item["min_profit_seen"], profit_rate)
        )
        item["max_profit_seen"] = (
            profit_rate
            if item.get("max_profit_seen") is None
            else max(item["max_profit_seen"], profit_rate)
        )
    for key in (
        "current_ai_score",
        "buy_pressure_10t",
        "tick_aggressor_trusted_count",
        "tick_aggressor_pressure_usable",
        "tick_acceleration_ratio",
        "curr_vs_micro_vwap_bp",
        "micro_vwap_available",
        "minute_candle_window_fresh",
    ):
        if key == "tick_aggressor_pressure_usable":
            if fields.get(key) is not None:
                item[key] = _optional_boolish(fields.get(key))
            continue
        if key in {"micro_vwap_available", "minute_candle_window_fresh"}:
            if fields.get(key) is not None:
                item[key] = _optional_boolish(fields.get(key))
            continue
        value = _safe_float(
            fields.get(key)
            or fields.get("ai_score" if key == "current_ai_score" else key)
        )
        if value is not None:
            item[key] = value
    if item.get("one_share_event"):
        opportunity_profit = _safe_float(
            item.get("pyramid_opportunity_profit_rate"), None
        )
        min_profit_pct = _pyramid_min_profit_pct()
        item["pyramid_opportunity_min_profit_pct"] = min_profit_pct
        if (
            profit_rate is not None
            and profit_rate >= min_profit_pct
            and opportunity_profit is None
        ):
            item["pyramid_opportunity_seen"] = True
            item["pyramid_opportunity_ts"] = row.get("emitted_at")
            item["pyramid_opportunity_profit_rate"] = profit_rate
            item["pyramid_opportunity_peak_profit"] = _safe_float(
                fields.get("peak_profit")
            )
            if (
                item.get("scale_in_blocker_reason")
                == "one_share_pyramid_no_opportunity_seen"
            ):
                item["scale_in_blocker_reason"] = (
                    "one_share_pyramid_not_submitted_opportunity"
                )
            item["scale_in_blocker_namespace"] = "ONE_SHARE_PYRAMID_BACKTEST"


def _pressure_provenance_missing(item: dict[str, Any]) -> bool:
    if item.get("buy_pressure_10t") is None:
        return False
    return (
        item.get("tick_aggressor_trusted_count") is None
        and item.get("tick_aggressor_pressure_usable") is None
    )


def _pressure_provenance_unusable(item: dict[str, Any]) -> bool:
    if item.get("buy_pressure_10t") is None:
        return False
    trusted_count = _safe_float(item.get("tick_aggressor_trusted_count"), 0.0) or 0.0
    pressure_usable = item.get("tick_aggressor_pressure_usable")
    return pressure_usable is False and trusted_count <= 0.0


def _pressure_provenance_missing_count(items: list[dict[str, Any]]) -> int:
    return sum(1 for item in items if _pressure_provenance_missing(item))


def _pressure_provenance_unusable_count(items: list[dict[str, Any]]) -> int:
    return sum(1 for item in items if _pressure_provenance_unusable(item))


def _micro_vwap_provenance_missing(item: dict[str, Any]) -> bool:
    micro_value = _safe_float(item.get("curr_vs_micro_vwap_bp"), None)
    if micro_value is None or abs(float(micro_value)) <= 1e-9:
        return False
    return (
        item.get("micro_vwap_available") is None
        or item.get("minute_candle_window_fresh") is None
    )


def _micro_vwap_provenance_unusable(item: dict[str, Any]) -> bool:
    micro_value = _safe_float(item.get("curr_vs_micro_vwap_bp"), None)
    if micro_value is None or abs(float(micro_value)) <= 1e-9:
        return False
    return (
        item.get("micro_vwap_available") is False
        or item.get("minute_candle_window_fresh") is False
    )


def _micro_vwap_provenance_missing_count(items: list[dict[str, Any]]) -> int:
    return sum(1 for item in items if _micro_vwap_provenance_missing(item))


def _micro_vwap_provenance_unusable_count(items: list[dict[str, Any]]) -> int:
    return sum(1 for item in items if _micro_vwap_provenance_unusable(item))


def _update_sell(item: dict[str, Any], row: dict[str, Any]) -> None:
    fields = _fields(row)
    final_profit = _safe_float(fields.get("profit_rate"))
    if final_profit is None:
        return
    item["final_ts"] = row.get("emitted_at")
    item["final_stage"] = row.get("stage")
    item["final_profit_rate"] = final_profit
    item["sell_reason_type"] = fields.get("sell_reason_type")
    item["exit_rule_candidate"] = fields.get("exit_rule_candidate") or fields.get(
        "exit_rule"
    )


def _update_submit(item: dict[str, Any], row: dict[str, Any]) -> None:
    fields = _fields(row)
    text = json.dumps(
        {"stage": row.get("stage"), "fields": fields}, ensure_ascii=False
    ).lower()
    if "pyramid" not in text:
        return
    item["pyramid_submit_seen"] = True
    item["pyramid_submit_ts"] = item.get("pyramid_submit_ts") or row.get("emitted_at")


def _feedback_label(item: dict[str, Any]) -> str:
    final_profit = item.get("final_profit_rate")
    blocker = str(item.get("scale_in_blocker_reason") or "")
    profit = item.get("profit_rate")
    max_seen = item.get("max_profit_seen")
    if final_profit is None:
        return "pyramid_open_unresolved"
    if (
        item.get("one_share_event")
        and not item.get("pyramid_opportunity_seen")
        and not item.get("pyramid_submit_seen")
    ):
        return "pyramid_correctly_blocked"
    if "micro_vwap_overheated" in blocker and final_profit <= max(
        float(profit or 0.0), 0.5
    ):
        return "pyramid_overheat_or_reversal_risk"
    if final_profit <= 0 or (profit is not None and final_profit <= float(profit)):
        return "pyramid_overheat_or_reversal_risk"
    if (
        max_seen is not None
        and profit is not None
        and float(max_seen) >= float(profit) + 0.8
    ):
        return "pyramid_would_have_helped"
    if final_profit >= 1.0:
        return "pyramid_would_have_helped"
    return "pyramid_correctly_blocked"


def _one_share_opportunity_cost(item: dict[str, Any]) -> float:
    opportunity_profit = _safe_float(item.get("pyramid_opportunity_profit_rate"), 0.0)
    max_profit = _safe_float(item.get("max_profit_seen"), opportunity_profit)
    return max(0.0, float(max_profit or 0.0) - float(opportunity_profit or 0.0))


def _aggregate_by_blocker(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("scale_in_blocker_reason") or "unknown")].append(row)
    metrics = []
    for blocker, items in sorted(grouped.items()):
        sample_count = len(items)
        recovered = sum(
            1
            for item in items
            if item.get("pyramid_feedback_label") == "pyramid_would_have_helped"
        )
        reversal = sum(
            1
            for item in items
            if item.get("pyramid_feedback_label") == "pyramid_overheat_or_reversal_risk"
        )
        submitted_profit = sum(
            1
            for item in items
            if _boolish(item.get("actual_order_submitted"))
            and _safe_float(item.get("final_profit_rate"), 0.0) > 0
        )
        metrics.append(
            {
                "scale_in_blocker_reason": blocker,
                "sample_count": sample_count,
                "recovered_or_extended_count": recovered,
                "recovered_or_extended_rate": (
                    recovered / sample_count if sample_count else 0.0
                ),
                "reversal_or_flat_count": reversal,
                "reversal_or_flat_rate": (
                    reversal / sample_count if sample_count else 0.0
                ),
                "blocked_then_recovered_count": recovered,
                "blocked_then_recovered_rate": (
                    recovered / sample_count if sample_count else 0.0
                ),
                "submitted_then_profit_count": submitted_profit,
                "submitted_then_profit_rate": (
                    submitted_profit / sample_count if sample_count else 0.0
                ),
            }
        )
    return metrics


def _one_share_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    label_counts = Counter(
        str(item.get("pyramid_feedback_label") or "unknown") for item in rows
    )
    closed = [
        item
        for item in rows
        if item.get("pyramid_feedback_label") != "pyramid_open_unresolved"
    ]
    opportunity_rows = [
        item for item in rows if bool(item.get("pyramid_opportunity_seen"))
    ]
    costs = [
        _safe_float(item.get("pyramid_opportunity_cost_pct"), 0.0)
        for item in opportunity_rows
    ]
    missed = [
        item
        for item in rows
        if item.get("pyramid_feedback_label") == "pyramid_would_have_helped"
    ]
    return {
        "one_share_event_count": len(rows),
        "one_share_closed_count": len(closed),
        "one_share_pyramid_opportunity_count": len(opportunity_rows),
        "one_share_pyramid_missed_upside_count": len(missed),
        "one_share_pyramid_missed_upside_rate": (
            len(missed) / len(closed) if closed else 0.0
        ),
        "one_share_pyramid_avg_opportunity_cost_pct": (
            sum(costs) / len(costs) if costs else 0.0
        ),
        "one_share_pyramid_label_counts": [
            {"pyramid_feedback_label": key, "count": value}
            for key, value in label_counts.most_common()
        ],
    }


def build_report(
    target_date: str,
    *,
    pipeline_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    pipeline_path = pipeline_path or _pipeline_path(target_date)
    resolved_pipeline_path = existing_or_gzip_path(pipeline_path)
    generated_at = generated_at or datetime.now(KST).isoformat(timespec="seconds")
    source_quality_status = (
        "pass" if resolved_pipeline_path.exists() else "missing_pipeline_events"
    )
    candidates: dict[str, dict[str, Any]] = {}
    one_share_records: dict[str, dict[str, Any]] = {}

    for row in iter_jsonl(pipeline_path):
        fields = _fields(row)
        key = _record_key(row, fields)
        if not key:
            continue
        if _is_one_share_event(row):
            one_share = _one_share_record(row)
            item = one_share_records.setdefault(key, one_share)
            item.update({k: v for k, v in one_share.items() if v not in (None, "")})
        blocked = _pyramid_blocked_record(row)
        if blocked:
            item = candidates.setdefault(key, blocked)
            item.update({k: v for k, v in blocked.items() if v not in (None, "")})
            if key in one_share_records:
                one_share_records[key].update(
                    {k: v for k, v in blocked.items() if v not in (None, "")}
                )
                one_share_records[key]["pyramid_opportunity_seen"] = True
                one_share_records[key]["pyramid_opportunity_ts"] = row.get("emitted_at")
                one_share_records[key]["pyramid_opportunity_profit_rate"] = blocked.get(
                    "profit_rate"
                )
        if _is_pyramid_submit_event(row):
            submitted = _pyramid_submit_record(row)
            item = candidates.setdefault(key, submitted)
            item.update({k: v for k, v in submitted.items() if v not in (None, "")})
            _update_submit(item, row)
            if key in one_share_records:
                one_share_records[key].update(
                    {k: v for k, v in submitted.items() if v not in (None, "")}
                )
                _update_submit(one_share_records[key], row)
        if key in candidates and row.get("pipeline") == "HOLDING_PIPELINE":
            stage = str(row.get("stage") or "")
            if stage == "sell_completed":
                _update_sell(candidates[key], row)
            elif (
                stage
                in {"stat_action_decision_snapshot", "bad_entry_refined_candidate"}
                or "profit_rate" in fields
            ):
                _update_snapshot(candidates[key], row)
            if "submit" in stage or "receipt" in stage or "submitted" in stage:
                _update_submit(candidates[key], row)
        if key in one_share_records and row.get("pipeline") == "HOLDING_PIPELINE":
            stage = str(row.get("stage") or "")
            if stage == "sell_completed":
                _update_sell(one_share_records[key], row)
            elif (
                stage
                in {"stat_action_decision_snapshot", "bad_entry_refined_candidate"}
                or "profit_rate" in fields
            ):
                _update_snapshot(one_share_records[key], row)
            if "submit" in stage or "receipt" in stage or "submitted" in stage:
                _update_submit(one_share_records[key], row)

    rows = []
    for item in candidates.values():
        item["pyramid_feedback_label"] = _feedback_label(item)
        item["actual_order_submitted"] = bool(item.get("pyramid_submit_seen"))
        item["broker_order_forbidden"] = not bool(item.get("pyramid_submit_seen"))
        item["runtime_effect"] = False
        item["allowed_runtime_apply"] = False
        item["decision_authority"] = (
            "source_only_pyramid_intraday_feedback_no_runtime_mutation"
        )
        item["forbidden_uses"] = FORBIDDEN_USES
        rows.append(item)
    rows.sort(
        key=lambda item: (
            str(item.get("first_observed_ts") or ""),
            str(item.get("record_id") or ""),
        )
    )

    one_share_rows = []
    for item in one_share_records.values():
        item["pyramid_feedback_label"] = _feedback_label(item)
        item["actual_order_submitted"] = bool(item.get("pyramid_submit_seen"))
        item["broker_order_forbidden"] = not bool(item.get("pyramid_submit_seen"))
        item["runtime_effect"] = False
        item["allowed_runtime_apply"] = False
        item["decision_authority"] = (
            "source_only_one_share_pyramid_opportunity_backtest_no_runtime_mutation"
        )
        item["forbidden_uses"] = FORBIDDEN_USES
        item["pyramid_opportunity_cost_pct"] = round(
            _one_share_opportunity_cost(item), 4
        )
        one_share_rows.append(item)
    one_share_rows.sort(
        key=lambda item: (
            str(item.get("first_one_share_ts") or ""),
            str(item.get("record_id") or ""),
        )
    )

    label_counts = Counter(
        str(item.get("pyramid_feedback_label") or "unknown") for item in rows
    )
    blocker_metrics = _aggregate_by_blocker(rows)
    one_share_opportunity_summary = _one_share_summary(one_share_rows)
    pressure_provenance_missing_count = _pressure_provenance_missing_count(
        rows + one_share_rows
    )
    pressure_provenance_unusable_count = _pressure_provenance_unusable_count(
        rows + one_share_rows
    )
    micro_vwap_provenance_missing_count = _micro_vwap_provenance_missing_count(
        rows + one_share_rows
    )
    micro_vwap_provenance_unusable_count = _micro_vwap_provenance_unusable_count(
        rows + one_share_rows
    )
    if pressure_provenance_missing_count:
        source_quality_status = "pressure_provenance_missing"
    if pressure_provenance_unusable_count:
        source_quality_status = "pressure_provenance_unusable"
    if micro_vwap_provenance_missing_count:
        source_quality_status = "micro_vwap_provenance_missing"
    if micro_vwap_provenance_unusable_count:
        source_quality_status = "micro_vwap_provenance_unusable"
    return {
        "schema_version": 1,
        "report_type": REPORT_TYPE,
        "target_date": target_date,
        "generated_at": generated_at,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "decision_authority": "source_only_pyramid_intraday_feedback_no_runtime_mutation",
        "forbidden_uses": FORBIDDEN_USES,
        "metric_contract": {
            "metric_role": "scale_in_pyramid_intraday_feedback",
            "decision_authority": "source_only_pyramid_intraday_feedback_no_runtime_mutation",
            "window_policy": "same_day_intraday_pipeline_events_continuously_updated",
            "sample_floor": "1_pyramid_blocked_reason_or_pyramid_submit_event",
            "primary_decision_metric": "pyramid_feedback_label_counts_and_blocker_cluster_rates",
            "source_quality_gate": (
                "pipeline_event_record_id_or_stock_code_join_with_required_provenance_and_"
                "tick_aggressor_pressure_provenance_for_buy_pressure_and_fresh_minute_candle_for_micro_vwap"
            ),
            "forbidden_uses": FORBIDDEN_USES,
        },
        "one_share_metric_contract": {
            "metric_role": "one_share_pyramid_opportunity_cost_backtest",
            "decision_authority": "source_only_one_share_pyramid_opportunity_backtest_no_runtime_mutation",
            "window_policy": "same_day_one_share_events_continuously_updated_then_postclose_rolling_clean_baseline",
            "sample_floor": "rolling_closed_one_share_pyramid_rows_ge_20",
            "primary_decision_metric": "one_share_pyramid_missed_upside_rate_and_avg_opportunity_cost_pct",
            "source_quality_gate": (
                "one_share_event_record_id_joined_to_holding_snapshots_and_sell_completed_with_"
                "fresh_minute_candle_provenance_for_micro_vwap_when_present"
            ),
            "forbidden_uses": FORBIDDEN_USES,
        },
        "source_paths": {"pipeline_events": str(resolved_pipeline_path)},
        "source_quality": {
            "status": source_quality_status,
            "pipeline_events_exists": resolved_pipeline_path.exists(),
            "pressure_provenance_missing_count": pressure_provenance_missing_count,
            "pressure_provenance_unusable_count": pressure_provenance_unusable_count,
            "micro_vwap_provenance_missing_count": micro_vwap_provenance_missing_count,
            "micro_vwap_provenance_unusable_count": micro_vwap_provenance_unusable_count,
        },
        "summary": {
            "pyramid_feedback_row_count": len(rows),
            "pressure_provenance_missing_count": pressure_provenance_missing_count,
            "pressure_provenance_unusable_count": pressure_provenance_unusable_count,
            "micro_vwap_provenance_missing_count": micro_vwap_provenance_missing_count,
            "micro_vwap_provenance_unusable_count": micro_vwap_provenance_unusable_count,
            "closed_pyramid_row_count": sum(
                1
                for item in rows
                if item.get("pyramid_feedback_label") != "pyramid_open_unresolved"
            ),
            "pyramid_would_have_helped_count": label_counts.get(
                "pyramid_would_have_helped", 0
            ),
            "pyramid_correctly_blocked_count": label_counts.get(
                "pyramid_correctly_blocked", 0
            ),
            "pyramid_overheat_or_reversal_risk_count": label_counts.get(
                "pyramid_overheat_or_reversal_risk", 0
            ),
            "pyramid_open_unresolved_count": label_counts.get(
                "pyramid_open_unresolved", 0
            ),
            "pyramid_feedback_label_counts": [
                {"pyramid_feedback_label": key, "count": value}
                for key, value in label_counts.most_common()
            ],
            **one_share_opportunity_summary,
        },
        "blocker_metrics": blocker_metrics,
        "pyramid_feedback_rows": rows[:300],
        "one_share_pyramid_opportunity_rows": one_share_rows,
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
        f"# {report.get('target_date')} Scalping Pyramid Intraday Feedback",
        "",
        f"- generated_at: {report.get('generated_at')}",
        "- decision_authority: source_only_pyramid_intraday_feedback_no_runtime_mutation",
        "- runtime_effect: false",
        "- allowed_runtime_apply: false",
        "- forbidden_uses: " + ", ".join(FORBIDDEN_USES),
        "",
        "## Summary",
        "",
        f"- pyramid_feedback_row_count: {summary.get('pyramid_feedback_row_count')}",
        f"- closed_pyramid_row_count: {summary.get('closed_pyramid_row_count')}",
        f"- pyramid_would_have_helped_count: {summary.get('pyramid_would_have_helped_count')}",
        f"- pyramid_correctly_blocked_count: {summary.get('pyramid_correctly_blocked_count')}",
        f"- pyramid_overheat_or_reversal_risk_count: {summary.get('pyramid_overheat_or_reversal_risk_count')}",
        f"- pyramid_open_unresolved_count: {summary.get('pyramid_open_unresolved_count')}",
        f"- one_share_event_count: {summary.get('one_share_event_count')}",
        f"- one_share_closed_count: {summary.get('one_share_closed_count')}",
        f"- one_share_pyramid_opportunity_count: {summary.get('one_share_pyramid_opportunity_count')}",
        f"- one_share_pyramid_missed_upside_count: {summary.get('one_share_pyramid_missed_upside_count')}",
        f"- one_share_pyramid_missed_upside_rate: {_safe_float(summary.get('one_share_pyramid_missed_upside_rate'), 0.0):.2f}",
        f"- one_share_pyramid_avg_opportunity_cost_pct: {_safe_float(summary.get('one_share_pyramid_avg_opportunity_cost_pct'), 0.0):.2f}",
        "",
        "## Blocker Metrics",
        "",
    ]
    for item in report.get("blocker_metrics") or []:
        lines.append(
            "- blocker={scale_in_blocker_reason} sample={sample_count} "
            "recovered_rate={recovered_or_extended_rate:.2f} reversal_rate={reversal_or_flat_rate:.2f} "
            "blocked_then_recovered_rate={blocked_then_recovered_rate:.2f}".format(
                **item
            )
        )
    lines.extend(["", "## Rows", ""])
    for item in report.get("pyramid_feedback_rows") or []:
        lines.append(
            "- record_id={record_id} code={stock_code} name={stock_name} label={pyramid_feedback_label} "
            "blocker={scale_in_blocker_reason} profit={profit_rate} final={final_profit_rate} "
            "ai={current_ai_score} tick={tick_acceleration_ratio} micro_vwap={curr_vs_micro_vwap_bp}".format(
                **{**item, "final_profit_rate": item.get("final_profit_rate")}
            )
        )
    lines.extend(["", "## One Share Opportunity Rows", ""])
    for item in report.get("one_share_pyramid_opportunity_rows") or []:
        lines.append(
            "- record_id={record_id} code={stock_code} name={stock_name} label={pyramid_feedback_label} "
            "opportunity_seen={pyramid_opportunity_seen} opportunity_profit={pyramid_opportunity_profit_rate} "
            "max_profit={max_profit_seen} opportunity_cost={pyramid_opportunity_cost_pct} "
            "final={final_profit_rate}".format(
                **{
                    **item,
                    "pyramid_opportunity_seen": bool(
                        item.get("pyramid_opportunity_seen")
                    ),
                    "pyramid_opportunity_profit_rate": item.get(
                        "pyramid_opportunity_profit_rate"
                    ),
                    "max_profit_seen": item.get("max_profit_seen"),
                    "final_profit_rate": item.get("final_profit_rate"),
                }
            )
        )
    output_md.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build scalping PYRAMID intraday feedback report."
    )
    parser.add_argument("--target-date", default=datetime.now(KST).strftime("%Y-%m-%d"))
    parser.add_argument("--pipeline-path", type=Path)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args(argv)
    output_json, output_md = (
        (args.output_json, args.output_md)
        if args.output_json and args.output_md
        else _default_output_paths(args.target_date)
    )
    report = build_report(args.target_date, pipeline_path=args.pipeline_path)
    write_outputs(report, output_json=output_json, output_md=output_md)
    if args.print_summary:
        print(json.dumps(report.get("summary", {}), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

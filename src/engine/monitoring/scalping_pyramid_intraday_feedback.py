from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.engine.scalping.rising_missed_one_share_entry import (
    SCOUT_AI_ATTRIBUTION_SCHEMA,
)
from src.engine.trade_profit import (
    calculate_net_profit_rate,
    calculate_net_realized_pnl,
    get_trade_cost_rate,
)

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


def _event_epoch(value: Any) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=KST)
    return parsed.timestamp()


def _event_after_final(item: dict[str, Any], row: dict[str, Any]) -> bool:
    final_epoch = _event_epoch(item.get("final_ts"))
    event_epoch = _event_epoch(row.get("emitted_at"))
    return bool(
        final_epoch is not None
        and event_epoch is not None
        and event_epoch > final_epoch
    )


def _pyramid_min_profit_pct() -> float:
    return float(getattr(TRADING_RULES, "SCALPING_PYRAMID_MIN_PROFIT_PCT", 1.5) or 1.5)


def _fields(row: dict[str, Any]) -> dict[str, Any]:
    fields = row.get("fields")
    return fields if isinstance(fields, dict) else {}


def _venue_token(value: Any) -> str:
    token = str(value or "").strip().upper()
    return token if token in {"KRX", "NXT", "PREMARKET_KRX_LIKE"} else ""


def _update_venue_provenance(item: dict[str, Any], row: dict[str, Any]) -> None:
    fields = _fields(row)
    authoritative = {
        token
        for token in (
            _venue_token(fields.get("rising_missed_effective_venue")),
            _venue_token(fields.get("effective_venue")),
        )
        if token
    }
    fallback = _venue_token(fields.get("venue"))
    authoritative_seen = set(item.get("_effective_venue_authoritative_seen") or [])
    fallback_seen = set(item.get("_effective_venue_fallback_seen") or [])
    authoritative_seen.update(authoritative)
    if fallback:
        fallback_seen.add(fallback)
    item["_effective_venue_authoritative_seen"] = sorted(authoritative_seen)
    item["_effective_venue_fallback_seen"] = sorted(fallback_seen)
    if len(authoritative_seen) == 1:
        item["effective_venue"] = next(iter(authoritative_seen))
        item["effective_venue_resolution"] = "explicit_effective_venue_field"
        item["venue_source_quality_valid"] = True
    elif len(authoritative_seen) > 1:
        item["effective_venue"] = "UNKNOWN"
        item["effective_venue_resolution"] = "conflicting_explicit_effective_venue"
        item["venue_source_quality_valid"] = False
    elif len(fallback_seen) == 1:
        item["effective_venue"] = next(iter(fallback_seen))
        item["effective_venue_resolution"] = "single_venue_fallback"
        item["venue_source_quality_valid"] = True
    elif len(fallback_seen) > 1:
        item["effective_venue"] = "UNKNOWN"
        item["effective_venue_resolution"] = "conflicting_venue_fallback"
        item["venue_source_quality_valid"] = False
    else:
        item["effective_venue"] = "UNKNOWN"
        item["effective_venue_resolution"] = "missing_explicit_venue"
        item["venue_source_quality_valid"] = False
    session_bucket = str(
        fields.get("rising_missed_market_session_bucket")
        or fields.get("market_session_bucket")
        or ""
    ).strip()
    if session_bucket and not item.get("market_session_bucket"):
        item["market_session_bucket"] = session_bucket


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
    stage = str(row.get("stage") or "")
    return bool(
        (
            stage == "probe_filled"
            and int(_safe_float(fields.get("fill_qty"), 0) or 0) == 1
        )
        or (
            stage == "rising_missed_one_share_entry"
            and _boolish(fields.get("actual_order_submitted"))
        )
    )


def _is_one_share_plan_event(row: dict[str, Any]) -> bool:
    stage = str(row.get("stage") or "")
    if stage == "rising_missed_one_share_entry":
        return True
    if stage != "entry_split_order_plan_applied":
        return False
    fields = _fields(row)
    return bool(
        _boolish(fields.get("rising_missed_one_share_scout"))
        and _boolish(fields.get("entry_split_order_probe_first_applied"))
        and int(_safe_float(fields.get("effective_qty"), 0.0) or 0) > 1
    )


def _update_scout_ai_execution_attribution(
    item: dict[str, Any], row: dict[str, Any]
) -> None:
    fields = _fields(row)
    if (
        str(fields.get("scout_ai_attribution_schema") or "").strip()
        != SCOUT_AI_ATTRIBUTION_SCHEMA
    ):
        return
    incoming_trace_id = str(
        fields.get("scout_ai_parent_decision_trace_id") or ""
    ).strip()
    current_trace_id = str(item.get("scout_ai_parent_decision_trace_id") or "").strip()
    if (
        current_trace_id not in {"", "-"}
        and incoming_trace_id not in {"", "-"}
        and current_trace_id != incoming_trace_id
    ):
        item["scout_ai_attribution_conflict"] = True
        item.setdefault("scout_ai_attribution_conflicting_trace_ids", []).append(
            incoming_trace_id
        )
        return
    for key in (
        "scout_ai_attribution_schema",
        "scout_ai_attribution_status",
        "scout_ai_parent_decision_trace_id",
        "scout_ai_parent_snapshot_id",
        "scout_ai_parent_action",
        "scout_ai_parent_score",
        "scout_ai_parent_result_source",
        "scout_ai_parent_contract_status",
        "scout_ai_parent_prompt_version",
        "scout_ai_parent_probe_intent",
        "scout_ai_parent_probe_intent_status",
        "scout_ai_action_used_as_submit_authority",
        "scout_ai_parent_actual_order_submitted",
        "scout_submission_authority",
        "scout_ai_runtime_relationship",
        "scout_probe_bundle_id",
        "scout_attribution_source_quality_gate",
    ):
        if fields.get(key) not in (None, ""):
            item[key] = fields.get(key)
    stage = str(row.get("stage") or fields.get("scout_execution_stage") or "").strip()
    stages = item.setdefault("scout_ai_attribution_lifecycle_stages", [])
    if stage and stage not in stages:
        stages.append(stage)
    if _boolish(fields.get("scout_attribution_actual_order_submitted")):
        item["scout_ai_attribution_real_submission_seen"] = True
    item.setdefault("scout_ai_attribution_conflict", False)


def _one_share_record(row: dict[str, Any]) -> dict[str, Any]:
    fields = _fields(row)
    item = {
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
        "entry_split_order_probe_qty": int(
            _safe_float(fields.get("entry_split_order_probe_qty"), 0.0) or 0
        ),
        "entry_split_order_leg_count": int(
            _safe_float(fields.get("entry_split_order_leg_count"), 0.0) or 0
        ),
        "entry_split_order_qty_weight_min": _safe_float(
            fields.get("entry_split_order_qty_weight_min")
        ),
        "entry_split_order_policy_version": fields.get(
            "entry_split_order_policy_version"
        ),
        "entry_split_order_variant_id": fields.get("entry_split_order_variant_id"),
        "scale_in_arm": "PYRAMID",
        "scale_in_blocker_reason": "one_share_pyramid_no_opportunity_seen",
        "scale_in_blocker_namespace": "ONE_SHARE_PYRAMID_BACKTEST",
    }
    _update_venue_provenance(item, row)
    _update_scout_ai_execution_attribution(item, row)
    return item


_REAL_ENTRY_LIFECYCLE_STAGES = {
    "order_bundle_submitted",
    "probe_submitted",
    "holding_started",
    "entry_order_cancel_confirmed",
    "sell_completed",
}
_SCOUT_AI_ATTRIBUTION_REQUIRED_CLOSED_STAGES = {
    "probe_submitted",
    "probe_filled",
    "order_bundle_submitted",
    "holding_started",
    "sell_completed",
}


def _real_entry_lifecycle_record(
    row: dict[str, Any],
) -> dict[str, Any]:
    fields = _fields(row)
    record_key = _record_key(row, fields)
    attempt_id = str(
        fields.get("main_lifecycle_attempt_id")
        or fields.get("attempt_id")
        or fields.get("scanner_promotion_id")
        or ""
    ).strip()
    item = {
        "record_id": str(row.get("record_id") or fields.get("record_id") or "").strip(),
        "record_key": record_key,
        "attempt_id": attempt_id or None,
        "main_lifecycle_id": str(fields.get("main_lifecycle_id") or "").strip()
        or None,
        "stock_code": row.get("stock_code") or fields.get("stock_code"),
        "stock_name": row.get("stock_name") or fields.get("stock_name"),
        "strategy": fields.get("strategy") or "SCALPING",
        "first_observed_ts": row.get("emitted_at"),
        "actual_entry_order_submitted": False,
        "entry_submit_order_nos": [],
        "planned_qty": 0,
        "broker_submitted_qty": 0,
        "filled_qty": 0,
        "canceled_unfilled_qty": 0,
        "probe_first_entry": False,
    }
    _update_venue_provenance(item, row)
    return item


def _real_entry_lifecycle_key(
    row: dict[str, Any], fields: dict[str, Any]
) -> str:
    """Return the narrowest stable identity for one real entry attempt.

    Scanner records can be recycled for a later promotion of the same symbol.  A
    record-id-only key therefore merges a canceled order with a later fill and
    corrupts submitted/fill/cancel attribution.  New journal rows carry an exact
    attempt identity; legacy rows retain the previous record key fallback.
    """

    for field_name in (
        "main_lifecycle_attempt_id",
        "attempt_id",
        "scanner_promotion_id",
    ):
        value = str(fields.get(field_name) or "").strip()
        if value:
            return f"attempt:{value}"
    main_lifecycle_id = str(fields.get("main_lifecycle_id") or "").strip()
    if main_lifecycle_id:
        return f"main_lifecycle:{main_lifecycle_id}"
    record_key = _record_key(row, fields)
    return f"record:{record_key}" if record_key else ""


def _earlier_event_time(current: Any, candidate: Any) -> Any:
    current_epoch = _event_epoch(current)
    candidate_epoch = _event_epoch(candidate)
    if candidate_epoch is None:
        return current
    if current_epoch is None or candidate_epoch < current_epoch:
        return candidate
    return current


def _later_event_time(current: Any, candidate: Any) -> Any:
    current_epoch = _event_epoch(current)
    candidate_epoch = _event_epoch(candidate)
    if candidate_epoch is None:
        return current
    if current_epoch is None or candidate_epoch > current_epoch:
        return candidate
    return current


def _update_real_entry_lifecycle(item: dict[str, Any], row: dict[str, Any]) -> None:
    stage = str(row.get("stage") or "")
    if stage not in _REAL_ENTRY_LIFECYCLE_STAGES:
        return
    fields = _fields(row)
    attempt_id = str(
        fields.get("main_lifecycle_attempt_id")
        or fields.get("attempt_id")
        or fields.get("scanner_promotion_id")
        or ""
    ).strip()
    if attempt_id and not item.get("attempt_id"):
        item["attempt_id"] = attempt_id
    main_lifecycle_id = str(fields.get("main_lifecycle_id") or "").strip()
    if main_lifecycle_id and not item.get("main_lifecycle_id"):
        item["main_lifecycle_id"] = main_lifecycle_id
    _update_scout_ai_execution_attribution(item, row)
    _update_venue_provenance(item, row)
    item["first_observed_ts"] = _earlier_event_time(
        item.get("first_observed_ts"), row.get("emitted_at")
    )
    item["latest_observed_ts"] = _later_event_time(
        item.get("latest_observed_ts"), row.get("emitted_at")
    )

    if stage in {"order_bundle_submitted", "probe_submitted"}:
        if not _boolish(fields.get("actual_order_submitted")):
            return
        item["actual_entry_order_submitted"] = True
        item["entry_submitted_at"] = _earlier_event_time(
            item.get("entry_submitted_at"), row.get("emitted_at")
        )
        order_no = str(
            fields.get("broker_order_no")
            or fields.get("order_no")
            or fields.get("ord_no")
            or ""
        ).strip()
        order_nos = item.setdefault("entry_submit_order_nos", [])
        if order_no and order_no not in order_nos:
            order_nos.append(order_no)
        planned_qty = int(
            _safe_float(
                fields.get("requested_qty")
                or fields.get("forced_entry_qty")
                or fields.get("effective_qty"),
                0.0,
            )
            or 0
        )
        item["planned_qty"] = max(int(item.get("planned_qty") or 0), planned_qty)
        if stage == "probe_submitted":
            item["probe_first_entry"] = True
            submitted_qty = int(_safe_float(fields.get("qty"), 0.0) or 0)
        else:
            submitted_qty = int(
                _safe_float(
                    fields.get("requested_qty") or fields.get("effective_qty"), 0.0
                )
                or 0
            )
        if stage == "probe_submitted" or not item.get("probe_first_entry"):
            if stage == "probe_submitted" and submitted_qty > 0:
                item["broker_submitted_qty"] = submitted_qty
            else:
                item["broker_submitted_qty"] = max(
                    int(item.get("broker_submitted_qty") or 0),
                    submitted_qty,
                )
        submitted_price = _safe_float(
            fields.get("order_price") or fields.get("submitted_order_price"), None
        )
        if submitted_price is not None:
            item["submitted_price"] = submitted_price
        item["broker_route"] = fields.get("broker_route") or item.get("broker_route")
        return

    if stage == "holding_started":
        fill_qty = int(
            _safe_float(
                fields.get("buy_qty")
                or fields.get("fill_qty")
                or fields.get("executed_qty"),
                0.0,
            )
            or 0
        )
        if fill_qty <= 0:
            return
        item["filled_qty"] = max(int(item.get("filled_qty") or 0), fill_qty)
        item["first_fill_at"] = _earlier_event_time(
            item.get("first_fill_at"), row.get("emitted_at")
        )
        fill_price = _safe_float(
            fields.get("buy_price")
            or fields.get("avg_fill_price")
            or fields.get("fill_price"),
            None,
        )
        if fill_price is not None:
            item["average_fill_price"] = fill_price
        return

    if stage == "entry_order_cancel_confirmed":
        item["entry_cancel_confirmed_at"] = _later_event_time(
            item.get("entry_cancel_confirmed_at"), row.get("emitted_at")
        )
        item["canceled_unfilled_qty"] = max(
            int(item.get("canceled_unfilled_qty") or 0),
            int(
                _safe_float(
                    fields.get("unfilled_qty")
                    or fields.get("remaining_qty")
                    or fields.get("qty"),
                    0.0,
                )
                or 0
            ),
        )
        confirmed_filled_qty = int(
            _safe_float(fields.get("filled_qty") or fields.get("executed_qty"), 0.0)
            or 0
        )
        if confirmed_filled_qty > 0:
            item["filled_qty"] = max(
                int(item.get("filled_qty") or 0), confirmed_filled_qty
            )
        return

    if stage == "sell_completed":
        raw_final_profit = _safe_float(fields.get("profit_rate"), None)
        raw_buy_price = _safe_float(fields.get("buy_price"), None)
        average_fill_price = _safe_float(item.get("average_fill_price"), None)
        sell_price = _safe_float(fields.get("sell_price"), None)
        filled_qty = max(0, int(item.get("filled_qty") or 0))
        sell_qty = int(_safe_float(fields.get("sell_qty"), 0.0) or 0)
        same_cycle_fill_reconciled = bool(
            str(item.get("record_id") or "").strip()
            and raw_buy_price is not None
            and average_fill_price is not None
            and raw_buy_price > 0
            and average_fill_price > 0
            and abs(raw_buy_price - average_fill_price) > 1e-9
            and sell_price is not None
            and sell_price > 0
            # Keep this repair to an unambiguous one-share lifecycle. A
            # multi-share or scale-in position may legitimately have a later
            # average price that differs from the initial holding receipt.
            and filled_qty == 1
            and sell_qty == filled_qty
            and int(item.get("broker_submitted_qty") or 0) == 1
        )
        final_profit = (
            calculate_net_profit_rate(average_fill_price, sell_price)
            if same_cycle_fill_reconciled
            else raw_final_profit
        )
        if final_profit is None:
            return
        item["sell_completed_at"] = _later_event_time(
            item.get("sell_completed_at"), row.get("emitted_at")
        )
        item["final_profit_rate"] = final_profit
        realized_pnl = _safe_float(fields.get("realized_pnl_krw"), None)
        if same_cycle_fill_reconciled:
            item["raw_sell_completed_buy_price"] = raw_buy_price
            item["raw_sell_completed_profit_rate"] = raw_final_profit
            item["raw_sell_completed_realized_pnl_krw"] = realized_pnl
            item["realized_pnl_krw"] = calculate_net_realized_pnl(
                average_fill_price,
                sell_price,
                filled_qty,
            )
            item["realized_pnl_krw_source"] = (
                "reconciled_same_cycle_broker_fill_prices_fee_aware"
            )
            item["lifecycle_economics_reconciled"] = True
            item["lifecycle_economics_reconcile_reason"] = (
                "sell_event_buy_price_differs_from_holding_broker_fill"
            )
        elif realized_pnl is not None:
            item["realized_pnl_krw"] = int(round(realized_pnl))
            item["realized_pnl_krw_source"] = str(
                fields.get("realized_pnl_krw_source") or "sell_completed_event"
            )
        if sell_price is not None:
            item["sell_price"] = sell_price
        # Older scalp-revive receipts carried the exact broker sell fill and
        # net profit rate but omitted KRW PnL. Reconstruct only when the same
        # position cycle proves a full-quantity close; never infer from a
        # partial fill, mark price, or unmatched quantity.
        if realized_pnl is None and not same_cycle_fill_reconciled:
            buy_price = _safe_float(
                fields.get("buy_price") or item.get("average_fill_price"), None
            )
            if (
                buy_price is not None
                and buy_price > 0
                and sell_price is not None
                and sell_price > 0
                and filled_qty > 0
                and sell_qty == filled_qty
            ):
                item["realized_pnl_krw"] = calculate_net_realized_pnl(
                    buy_price,
                    sell_price,
                    filled_qty,
                )
                item["realized_pnl_krw_source"] = (
                    "reconstructed_same_cycle_full_close_fee_aware"
                )
                item["realized_pnl_cost_rate"] = get_trade_cost_rate()


def _canonical_expansion_outcome_label(item: dict[str, Any]) -> str:
    post_probe_label = str(item.get("post_probe_real_outcome_label") or "")
    confirmation_alignment = str(
        item.get("post_probe_confirmation_contract_alignment") or ""
    )
    if confirmation_alignment == "runtime_confirmed_source_quality_disputed":
        if post_probe_label == "profitable_zero_fill_no_confirmation":
            return "expansion_missed_upside_runtime_confirmed_source_quality_disputed"
        if post_probe_label == "loss_or_flat_zero_fill_no_confirmation":
            return (
                "expansion_confirmation_false_positive_"
                "runtime_confirmed_source_quality_disputed"
            )
    post_probe_mapping = {
        "profitable_zero_fill_confirmation_ready": (
            "expansion_missed_upside_confirmation_ready"
        ),
        "profitable_zero_fill_no_confirmation": (
            "expansion_correctly_not_expanded_no_confirmation"
        ),
        "profitable_zero_fill_recovery_confirmation_ready": (
            "expansion_recovery_missed_upside_confirmation_ready"
        ),
        "profitable_zero_fill_recovery_not_confirmed": (
            "expansion_correctly_not_expanded_recovery_not_confirmed"
        ),
        "profitable_zero_fill_recovery_evaluation_not_run": (
            "expansion_recovery_evaluation_not_run"
        ),
        "loss_or_flat_zero_fill_confirmation_ready": (
            "expansion_confirmation_false_positive_loss_or_flat"
        ),
        "loss_or_flat_zero_fill_no_confirmation": ("expansion_correctly_not_expanded"),
        "source_quality_blocked": "expansion_source_quality_blocked",
        "open_unresolved": "expansion_open_unresolved",
        "not_zero_fill": "expansion_not_applicable_residual_filled",
    }
    if post_probe_label in post_probe_mapping:
        return post_probe_mapping[post_probe_label]
    legacy_label = str(item.get("legacy_pyramid_feedback_label") or "")
    return {
        "pyramid_would_have_helped": "expansion_missed_upside_threshold_crossed",
        "pyramid_correctly_blocked": "expansion_correctly_not_expanded",
        "pyramid_overheat_or_reversal_risk": (
            "expansion_correctly_not_expanded_reversal_risk"
        ),
        "pyramid_open_unresolved": "expansion_open_unresolved",
    }.get(legacy_label, "expansion_not_observed")


def _finalize_real_entry_lifecycle(
    item: dict[str, Any], one_share_item: dict[str, Any] | None
) -> None:
    filled_qty = max(0, int(item.get("filled_qty") or 0))
    final_profit = _safe_float(item.get("final_profit_rate"), None)
    if final_profit is not None and item.get("sell_completed_at"):
        state = "closed"
    elif filled_qty > 0:
        state = "holding"
    elif item.get("entry_cancel_confirmed_at"):
        state = "canceled_unfilled"
    else:
        state = "pending_entry"
    item["lifecycle_state"] = state
    item["closed_outcome_label"] = (
        "winner"
        if state == "closed" and final_profit is not None and final_profit > 0
        else (
            "loss"
            if state == "closed" and final_profit is not None and final_profit < 0
            else (
                "flat"
                if state == "closed" and final_profit is not None
                else "not_closed"
            )
        )
    )
    item["venue_source_quality_valid"] = bool(
        item.get("venue_source_quality_valid")
        and str(item.get("effective_venue") or "")
        in {"KRX", "NXT", "PREMARKET_KRX_LIKE"}
    )
    planned_qty = max(0, int(item.get("planned_qty") or 0))
    item["single_share_plan"] = bool(
        planned_qty == 1 and not item.get("probe_first_entry")
    )
    item["single_share_plan_closed_winner"] = bool(
        item["single_share_plan"]
        and state == "closed"
        and final_profit is not None
        and final_profit > 0
    )
    if isinstance(one_share_item, dict):
        for key in (
            "probe_bundle_id",
            "probe_fill_qty",
            "residual_expected_qty",
            "residual_submitted_qty",
            "residual_filled_qty",
            "residual_unfilled_qty",
            "residual_zero_fill",
            "post_probe_real_outcome_label",
            "post_probe_real_confirmation_ready",
            "canonical_expansion_outcome_label",
        ):
            if key in one_share_item:
                item[key] = one_share_item.get(key)
        probe_fill_qty = max(0, int(one_share_item.get("probe_fill_qty") or 0))
        residual_submitted_qty = max(
            0, int(one_share_item.get("residual_submitted_qty") or 0)
        )
        if item.get("probe_first_entry") and probe_fill_qty > 0:
            item["broker_submitted_qty"] = max(
                int(item.get("broker_submitted_qty") or 0),
                probe_fill_qty + residual_submitted_qty,
            )
        residual_filled_qty = one_share_item.get("residual_filled_qty")
        if residual_filled_qty is not None and probe_fill_qty > 0:
            item["filled_qty"] = max(
                filled_qty,
                probe_fill_qty + max(0, int(residual_filled_qty)),
            )
    item["runtime_effect"] = False
    item["allowed_runtime_apply"] = False
    item["actual_order_submitted"] = bool(item.get("actual_entry_order_submitted"))
    item["broker_order_forbidden"] = False
    item["decision_authority"] = (
        "source_only_same_day_real_entry_lifecycle_reconciliation"
    )
    item["forbidden_uses"] = FORBIDDEN_USES


def _real_entry_lifecycle_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    closed = [
        item
        for item in rows
        if item.get("lifecycle_state") == "closed"
        and _safe_float(item.get("final_profit_rate"), None) is not None
    ]

    def _dimension_metrics(
        dimension: str, dimension_rows: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in dimension_rows:
            value = str(item.get(dimension) or "UNKNOWN").strip() or "UNKNOWN"
            grouped[value].append(item)
        metrics = []
        for value, bucket_rows in sorted(grouped.items()):
            bucket_closed = [
                item
                for item in bucket_rows
                if item.get("lifecycle_state") == "closed"
                and _safe_float(item.get("final_profit_rate"), None) is not None
            ]
            profit_values = [
                float(_safe_float(item.get("final_profit_rate"), 0.0) or 0.0)
                for item in bucket_closed
            ]
            pnl_values = [
                int(item["realized_pnl_krw"])
                for item in bucket_closed
                if item.get("realized_pnl_krw") is not None
            ]
            metrics.append(
                {
                    dimension: value,
                    "submitted_cycle_count": len(bucket_rows),
                    "filled_cycle_count": sum(
                        1
                        for item in bucket_rows
                        if int(item.get("filled_qty") or 0) > 0
                    ),
                    "canceled_unfilled_cycle_count": sum(
                        1
                        for item in bucket_rows
                        if item.get("lifecycle_state") == "canceled_unfilled"
                    ),
                    "closed_cycle_count": len(bucket_closed),
                    "holding_cycle_count": sum(
                        1
                        for item in bucket_rows
                        if item.get("lifecycle_state") == "holding"
                    ),
                    "winner_count": sum(
                        1 for item in bucket_closed if item["final_profit_rate"] > 0
                    ),
                    "loss_count": sum(
                        1 for item in bucket_closed if item["final_profit_rate"] < 0
                    ),
                    "flat_count": sum(
                        1 for item in bucket_closed if item["final_profit_rate"] == 0
                    ),
                    "diagnostic_win_rate": (
                        round(
                            sum(
                                1
                                for item in bucket_closed
                                if item["final_profit_rate"] > 0
                            )
                            / len(bucket_closed),
                            4,
                        )
                        if bucket_closed
                        else 0.0
                    ),
                    "equal_weight_avg_profit_pct": (
                        round(sum(profit_values) / len(profit_values), 4)
                        if profit_values
                        else 0.0
                    ),
                    "realized_pnl_krw_known_sum": sum(pnl_values),
                    "realized_pnl_krw_known_count": len(pnl_values),
                    "single_share_plan_closed_winner_count": sum(
                        1
                        for item in bucket_rows
                        if item.get("single_share_plan_closed_winner")
                    ),
                    "multi_leg_probe_cycle_count": sum(
                        1 for item in bucket_rows if item.get("probe_first_entry")
                    ),
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                }
            )
        return metrics

    venue_valid_rows = [
        item for item in rows if item.get("venue_source_quality_valid") is True
    ]
    profit_values = [
        float(_safe_float(item.get("final_profit_rate"), 0.0) or 0.0) for item in closed
    ]
    pnl_values = [
        int(item["realized_pnl_krw"])
        for item in closed
        if item.get("realized_pnl_krw") is not None
    ]
    pnl_source_counts = Counter(
        str(item.get("realized_pnl_krw_source") or "missing_source")
        for item in closed
        if item.get("realized_pnl_krw") is not None
    )
    realized_pnl_missing_count = len(closed) - len(pnl_values)
    return {
        "submitted_cycle_count": len(rows),
        "filled_cycle_count": sum(
            1 for item in rows if int(item.get("filled_qty") or 0) > 0
        ),
        "canceled_unfilled_cycle_count": sum(
            1 for item in rows if item.get("lifecycle_state") == "canceled_unfilled"
        ),
        "closed_cycle_count": len(closed),
        "holding_cycle_count": sum(
            1 for item in rows if item.get("lifecycle_state") == "holding"
        ),
        "pending_entry_cycle_count": sum(
            1 for item in rows if item.get("lifecycle_state") == "pending_entry"
        ),
        "winner_count": sum(1 for item in closed if item["final_profit_rate"] > 0),
        "loss_count": sum(1 for item in closed if item["final_profit_rate"] < 0),
        "flat_count": sum(1 for item in closed if item["final_profit_rate"] == 0),
        "diagnostic_win_rate": (
            round(
                sum(1 for item in closed if item["final_profit_rate"] > 0)
                / len(closed),
                4,
            )
            if closed
            else 0.0
        ),
        "equal_weight_avg_profit_pct": (
            round(sum(profit_values) / len(profit_values), 4) if profit_values else 0.0
        ),
        "realized_pnl_krw_known_sum": sum(pnl_values),
        "realized_pnl_krw_known_count": len(pnl_values),
        "realized_pnl_krw_missing_count": realized_pnl_missing_count,
        "realized_pnl_krw_source_counts": [
            {"source": source, "count": count}
            for source, count in sorted(pnl_source_counts.items())
        ],
        "realized_pnl_source_quality_state": (
            "complete"
            if closed and realized_pnl_missing_count == 0
            else (
                "partial_missing_realized_pnl"
                if closed
                else "not_applicable_no_closed_cycle"
            )
        ),
        "single_share_plan_closed_winner_count": sum(
            1 for item in rows if item.get("single_share_plan_closed_winner")
        ),
        "multi_leg_probe_cycle_count": sum(
            1 for item in rows if item.get("probe_first_entry")
        ),
        "multi_leg_zero_residual_fill_count": sum(
            1
            for item in rows
            if item.get("probe_first_entry") and item.get("residual_zero_fill") is True
        ),
        "venue_source_quality_valid_count": len(venue_valid_rows),
        "venue_source_quality_invalid_count": len(rows) - len(venue_valid_rows),
        "by_effective_venue": _dimension_metrics("effective_venue", venue_valid_rows),
        "by_market_session_bucket": _dimension_metrics(
            "market_session_bucket", venue_valid_rows
        ),
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


def _post_probe_hard_abort_recovery_candidate_record(
    row: dict[str, Any],
) -> dict[str, Any] | None:
    stage = str(row.get("stage") or "")
    if stage not in _POST_PROBE_RECOVERY_STAGES:
        return None
    fields = _fields(row)
    if not (
        _boolish(fields.get("recovery_eligible"))
        and _boolish(fields.get("recovery_confirmation_ready"))
        and not _boolish(fields.get("runtime_effect"))
        and not _boolish(fields.get("actual_order_submitted"))
        and _boolish(fields.get("broker_order_forbidden"))
        and str(fields.get("decision_authority") or "").strip()
        in _POST_PROBE_RECOVERY_AUTHORITIES
    ):
        return None
    terminal_abort_event = stage == "post_probe_terminal_abort_recovery_observed"
    return {
        "record_id": str(row.get("record_id") or "").strip(),
        "stock_code": row.get("stock_code"),
        "stock_name": row.get("stock_name"),
        "first_observed_ts": row.get("emitted_at"),
        "source_stage": row.get("stage"),
        "scale_in_arm": "PYRAMID",
        "scale_in_blocker_reason": (
            "post_terminal_abort_recovery_source_only"
            if terminal_abort_event
            else "post_hard_abort_recovery_source_only"
        ),
        "scale_in_blocker_namespace": (
            "POST_PROBE_TERMINAL_ABORT_RECOVERY"
            if terminal_abort_event
            else "POST_PROBE_HARD_ABORT_RECOVERY"
        ),
        "recovery_abort_class": str(fields.get("recovery_abort_class") or "unknown"),
        "profit_rate": _safe_float(fields.get("profit_rate")),
        "peak_profit": _safe_float(fields.get("peak_profit")),
        "current_ai_score": _safe_float(fields.get("current_ai_score")),
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
        "recovery_ai_thesis_state": str(
            fields.get("recovery_ai_thesis_state") or "unreported"
        )
        .strip()
        .lower(),
        "recovery_ai_tape_substitution_applied": _boolish(
            fields.get("recovery_ai_tape_substitution_applied")
        ),
        "recovery_ai_parent_prompt_version": str(
            fields.get("recovery_ai_parent_prompt_version") or "unreported"
        ).strip(),
        "recovery_holding_ai_action": str(
            fields.get("recovery_holding_ai_action") or "unreported"
        ).strip(),
        "recovery_holding_ai_data_quality": str(
            fields.get("recovery_holding_ai_data_quality") or "unreported"
        ).strip(),
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
    _update_scout_ai_execution_attribution(item, row)
    profit_rate = _safe_float(fields.get("profit_rate"))
    peak_profit = _safe_float(fields.get("peak_profit"))
    observed_peak = (
        max(value for value in (profit_rate, peak_profit) if value is not None)
        if profit_rate is not None or peak_profit is not None
        else None
    )
    item["latest_snapshot_ts"] = row.get("emitted_at")
    item["latest_stage"] = row.get("stage")
    item["latest_profit_rate"] = profit_rate
    item["latest_peak_profit"] = peak_profit
    observed_min_profit = _safe_float(fields.get("min_profit_pct"), None)
    if observed_min_profit is not None and observed_min_profit > 0:
        item["pyramid_opportunity_min_profit_pct"] = observed_min_profit
        item["pyramid_opportunity_threshold_source"] = "exact_pyramid_evaluation_event"
    if profit_rate is not None:
        item["min_profit_seen"] = (
            profit_rate
            if item.get("min_profit_seen") is None
            else min(item["min_profit_seen"], profit_rate)
        )
        item["max_profit_seen"] = (
            observed_peak
            if item.get("max_profit_seen") is None
            else max(item["max_profit_seen"], observed_peak)
        )
    elif observed_peak is not None:
        item["max_profit_seen"] = (
            observed_peak
            if item.get("max_profit_seen") is None
            else max(item["max_profit_seen"], observed_peak)
        )
    if item.get("normal_winner_expansion_candidate_seen"):
        post_values = [
            value for value in (profit_rate, observed_peak) if value is not None
        ]
        if post_values:
            item["normal_winner_expansion_post_candidate_max_profit_pct"] = max(
                _safe_float(
                    item.get("normal_winner_expansion_post_candidate_max_profit_pct"),
                    post_values[0],
                ),
                *post_values,
            )
            item["normal_winner_expansion_post_candidate_min_profit_pct"] = min(
                _safe_float(
                    item.get("normal_winner_expansion_post_candidate_min_profit_pct"),
                    post_values[0],
                ),
                *post_values,
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
        min_profit_pct = float(
            _safe_float(
                item.get("pyramid_opportunity_min_profit_pct"),
                _pyramid_min_profit_pct(),
            )
            or _pyramid_min_profit_pct()
        )
        item["pyramid_opportunity_min_profit_pct"] = min_profit_pct
        item.setdefault(
            "pyramid_opportunity_threshold_source",
            "static_fallback_pending_runtime_threshold_provenance",
        )
        exact_cross = profit_rate is not None and profit_rate >= min_profit_pct
        peak_cross = observed_peak is not None and observed_peak >= min_profit_pct
        if (exact_cross or peak_cross) and opportunity_profit is None:
            item["pyramid_opportunity_seen"] = True
            item["pyramid_opportunity_ts"] = row.get("emitted_at")
            item["pyramid_opportunity_profit_rate"] = (
                profit_rate if exact_cross else min_profit_pct
            )
            item["pyramid_opportunity_peak_profit"] = observed_peak
            item["pyramid_opportunity_source"] = (
                "exact_profit_snapshot"
                if exact_cross
                else "holding_peak_threshold_crossed"
            )
            if (
                item.get("scale_in_blocker_reason")
                == "one_share_pyramid_no_opportunity_seen"
            ):
                item["scale_in_blocker_reason"] = (
                    "one_share_pyramid_not_submitted_opportunity"
                )
            item["scale_in_blocker_namespace"] = "ONE_SHARE_PYRAMID_BACKTEST"


_PROBE_RESIDUAL_STAGES = {
    "probe_filled",
    "residual_submitted",
    "residual_blocked",
    "residual_partial_complete",
    "bundle_completed",
}
_PROBE_DIRECTION_STAGES = {
    "probe_continuation_deferred",
    "residual_planned",
}
_POST_PROBE_RECOVERY_STAGES = {
    "post_probe_hard_abort_recovery_observed",
    "post_probe_terminal_abort_recovery_observed",
}
_POST_PROBE_RECOVERY_AUTHORITIES = {
    "source_only_post_hard_abort_recovery_observation_no_runtime_mutation",
    "source_only_post_terminal_abort_recovery_observation_no_runtime_mutation",
}
_SOFT_RESIDUAL_ABORT_REASONS = {
    "residual_leg_direction_deferred",
    "residual_revalidation_timeout",
}


def _update_probe_residual_observation(
    item: dict[str, Any], row: dict[str, Any]
) -> None:
    stage = str(row.get("stage") or "")
    fields = _fields(row)
    row_bundle_id = str(fields.get("probe_bundle_id") or "").strip()
    if row_bundle_id == "-":
        row_bundle_id = ""
    item_bundle_id = str(item.get("probe_bundle_id") or "").strip()
    if row_bundle_id and item_bundle_id and row_bundle_id != item_bundle_id:
        item["residual_fill_attribution_valid"] = False
        item["residual_fill_attribution_state"] = "bundle_mismatch"
        reasons = item.setdefault("residual_fill_attribution_reasons", [])
        reason = f"probe_bundle_mismatch:{item_bundle_id}:{row_bundle_id}"
        if reason not in reasons:
            reasons.append(reason)
        return
    if row_bundle_id and not item_bundle_id:
        item["probe_bundle_id"] = row_bundle_id
    item["probe_confirmation_max_count"] = max(
        int(item.get("probe_confirmation_max_count") or 0),
        int(_safe_float(fields.get("probe_confirmation_count"), 0) or 0),
    )
    if stage in _PROBE_DIRECTION_STAGES:
        state = str(fields.get("post_probe_direction_state") or "").strip().upper()
        action = str(fields.get("post_probe_continuation_action") or "").strip().upper()
        reason = str(fields.get("post_probe_direction_reason") or "").strip()
        positive_groups = {
            token.strip()
            for token in str(
                fields.get("post_probe_direction_positive_groups") or ""
            ).split(",")
            if token.strip() and token.strip() != "-"
        }
        negative_groups = {
            token.strip()
            for token in str(
                fields.get("post_probe_direction_negative_groups") or ""
            ).split(",")
            if token.strip() and token.strip() != "-"
        }
        strong = bool(
            state == "STRONG"
            and action
            in {
                "DEFER",
                "ALLOW_NARROW",
                "ALLOW_NORMAL",
                "ALLOW_RECOVERED_WIDE",
            }
            and len(positive_groups) >= 2
            and not negative_groups
        )
        previous_consecutive = int(
            item.get("probe_direction_current_consecutive_strong_count") or 0
        )
        current_consecutive = previous_consecutive + 1 if strong else 0
        item["probe_direction_current_consecutive_strong_count"] = current_consecutive
        item["probe_direction_max_consecutive_strong_count"] = max(
            int(item.get("probe_direction_max_consecutive_strong_count") or 0),
            current_consecutive,
        )
        item["probe_direction_evaluation_count"] = (
            int(item.get("probe_direction_evaluation_count") or 0) + 1
        )
        item["probe_direction_strong_evaluation_count"] = int(
            item.get("probe_direction_strong_evaluation_count") or 0
        ) + int(strong)
        item["probe_direction_max_positive_group_count"] = max(
            int(item.get("probe_direction_max_positive_group_count") or 0),
            len(positive_groups),
        )
        item["probe_direction_negative_seen"] = bool(
            item.get("probe_direction_negative_seen") or negative_groups
        )
        item["probe_direction_latest_state"] = state or "-"
        item["probe_direction_latest_action"] = action or "-"
        item["probe_direction_latest_reason"] = reason or "-"
        item["probe_direction_latest_positive_groups"] = (
            ",".join(sorted(positive_groups)) or "-"
        )
        item["probe_direction_latest_negative_groups"] = (
            ",".join(sorted(negative_groups)) or "-"
        )
        item["probe_direction_latest_mixed_groups"] = str(
            fields.get("post_probe_direction_mixed_groups") or "-"
        )
        item["probe_direction_latest_orderbook_state"] = str(
            fields.get("post_probe_direction_orderbook_state") or "unknown"
        )
        item["probe_direction_latest_signed_pressure_source"] = str(
            fields.get("post_probe_direction_signed_pressure_source") or "unavailable"
        )
        item["probe_direction_latest_route_source_allowed"] = _optional_boolish(
            fields.get("post_probe_route_source_allowed")
        )
        item["probe_direction_latest_route_source_blockers"] = str(
            fields.get("post_probe_route_source_blockers") or "-"
        )
        mark_price = _safe_float(fields.get("post_probe_direction_mark_price"), None)
        probe_fill_price = _safe_float(
            fields.get("post_probe_direction_probe_fill_price"), None
        )
        ai_action = (
            str(fields.get("post_probe_direction_ai_action") or "").strip().upper()
        )
        evidence_signature = str(
            fields.get("post_probe_confirmation_source_version_signature")
            or fields.get("post_probe_confirmation_evidence_signature")
            or ""
        ).strip()
        confirmation_source_quality_blockers = []
        if not _boolish(fields.get("post_probe_direction_tick_context_fresh")):
            confirmation_source_quality_blockers.append("tick_context_not_fresh")
        if not _boolish(fields.get("post_probe_confirmation_evidence_version_proven")):
            confirmation_source_quality_blockers.append("evidence_version_not_proven")
        if not evidence_signature:
            confirmation_source_quality_blockers.append("evidence_signature_missing")
        if ai_action not in {"BUY", "WAIT"}:
            confirmation_source_quality_blockers.append(
                "ai_action_not_confirmation_eligible"
            )
        counterfactual_confirmation = bool(
            mark_price is not None
            and probe_fill_price is not None
            and mark_price >= probe_fill_price > 0
            and len(positive_groups) >= 2
            and not negative_groups
            and ai_action in {"BUY", "WAIT"}
            and not _boolish(fields.get("post_probe_hard_veto"))
            and _boolish(fields.get("post_probe_confirmation_evidence_version_proven"))
            and evidence_signature
            and _boolish(fields.get("post_probe_direction_tick_context_fresh"))
        )
        observed_epoch = _event_epoch(row.get("emitted_at"))
        item.setdefault("post_probe_real_confirmation_observations", []).append(
            {
                "observed_at": row.get("emitted_at"),
                "observed_epoch": observed_epoch,
                "eligible": counterfactual_confirmation,
                "evidence_signature": evidence_signature,
                "source_quality_blockers": confirmation_source_quality_blockers,
            }
        )
        reason_counts = item.setdefault("probe_direction_reason_counts", {})
        if reason:
            reason_counts[reason] = int(reason_counts.get(reason) or 0) + 1
    requested_qty = int(
        _safe_float(
            fields.get("forced_entry_qty")
            or fields.get("entry_split_probe_requested_qty"),
            0.0,
        )
        or 0.0
    )
    if requested_qty > 0:
        item["forced_entry_qty"] = max(
            int(item.get("forced_entry_qty") or 0), requested_qty
        )
    if stage == "pyramid_blocked_reason":
        item["pyramid_evaluation_seen"] = True
        item["pyramid_evaluation_count"] = (
            int(item.get("pyramid_evaluation_count") or 0) + 1
        )
    if stage in _POST_PROBE_RECOVERY_STAGES:
        item["post_probe_hard_abort_recovery_evaluation_seen"] = True
        item["post_probe_hard_abort_recovery_evaluation_count"] = (
            int(item.get("post_probe_hard_abort_recovery_evaluation_count") or 0) + 1
        )
        source_blockers = {
            token.strip()
            for token in str(
                fields.get("recovery_source_quality_blockers") or ""
            ).split(",")
            if token.strip() and token.strip() != "-"
        }
        decision_authority = str(fields.get("decision_authority") or "").strip()
        contract_integrity_blockers: set[str] = set()
        if decision_authority not in _POST_PROBE_RECOVERY_AUTHORITIES:
            contract_integrity_blockers.add("decision_authority_invalid")
        if _boolish(fields.get("runtime_effect")):
            contract_integrity_blockers.add("runtime_effect_not_false")
        if _boolish(fields.get("actual_order_submitted")):
            contract_integrity_blockers.add("actual_order_submitted_not_false")
        if not _boolish(fields.get("broker_order_forbidden")):
            contract_integrity_blockers.add("broker_order_forbidden_not_true")
        evidence_signature = str(
            fields.get("recovery_evidence_signature") or ""
        ).strip()
        if not evidence_signature:
            contract_integrity_blockers.add("evidence_signature_missing")
        contract_blockers = source_blockers | contract_integrity_blockers
        observed_epoch = _event_epoch(row.get("emitted_at"))
        item.setdefault("post_probe_hard_abort_recovery_observations", []).append(
            {
                "observed_at": row.get("emitted_at"),
                "observed_epoch": observed_epoch,
                "eligible": bool(
                    _boolish(fields.get("recovery_eligible")) and not contract_blockers
                ),
                "evidence_signature": evidence_signature,
                "source_quality_blockers": sorted(contract_blockers),
                "confirmation_preserved": bool(
                    _boolish(fields.get("recovery_confirmation_preserved"))
                    and not contract_integrity_blockers
                ),
                "ai_thesis_state": str(
                    fields.get("recovery_ai_thesis_state") or "unreported"
                )
                .strip()
                .lower(),
                "ai_tape_substitution_applied": _boolish(
                    fields.get("recovery_ai_tape_substitution_applied")
                ),
            }
        )
        item["post_probe_hard_abort_recovery_latest_state"] = str(
            fields.get("recovery_state") or "-"
        )
        item["post_probe_hard_abort_recovery_latest_reason"] = str(
            fields.get("recovery_reason") or "-"
        )
        item["post_probe_terminal_abort_recovery_latest_class"] = str(
            fields.get("recovery_abort_class") or "unknown"
        )
        item["post_probe_hard_abort_recovery_event_confirmation_max_count"] = max(
            int(
                item.get("post_probe_hard_abort_recovery_event_confirmation_max_count")
                or 0
            ),
            int(_safe_float(fields.get("recovery_confirmation_count"), 0) or 0),
        )
    if stage not in _PROBE_RESIDUAL_STAGES:
        return

    item["probe_residual_observation_seen"] = True
    item["probe_bundle_id"] = row_bundle_id or item.get("probe_bundle_id")
    if stage == "probe_filled":
        probe_fill_qty = max(1, int(_safe_float(fields.get("fill_qty"), 1.0) or 1.0))
        item["probe_fill_qty"] = probe_fill_qty
        item["probe_fill_price"] = _safe_float(fields.get("fill_price"))
        item["probe_filled_at"] = row.get("emitted_at")
    elif stage == "residual_submitted":
        order_no = str(fields.get("order_no") or "").strip()
        submitted_orders = item.setdefault("residual_submitted_order_nos", [])
        qty = max(0, int(_safe_float(fields.get("qty"), 0.0) or 0.0))
        if qty > 0 and not order_no:
            item["residual_fill_attribution_valid"] = False
            item["residual_fill_attribution_state"] = "submission_order_no_missing"
            reasons = item.setdefault("residual_fill_attribution_reasons", [])
            if "residual_submission_order_no_missing" not in reasons:
                reasons.append("residual_submission_order_no_missing")
        if not order_no or order_no not in submitted_orders:
            if order_no:
                submitted_orders.append(order_no)
            item["residual_submitted_qty"] = (
                int(item.get("residual_submitted_qty") or 0) + qty
            )
            price = int(_safe_float(fields.get("price"), 0.0) or 0.0)
            if price > 0:
                item.setdefault("residual_submitted_prices", []).append(price)
                item.setdefault("post_probe_reprice_observations", []).append(
                    {
                        "order_no": order_no,
                        "profile": str(
                            fields.get("entry_price_resolver_offset_profile")
                            or "unknown"
                        ),
                        "action": str(
                            fields.get("entry_price_resolver_action") or "unknown"
                        ),
                        "previous_price": int(
                            _safe_float(
                                fields.get("entry_price_resolver_previous_price"),
                                0.0,
                            )
                            or 0
                        ),
                        "resolved_price": int(
                            _safe_float(
                                fields.get("entry_price_resolver_resolved_price"),
                                price,
                            )
                            or price
                        ),
                    }
                )
        item["residual_submitted_leg_count"] = len(submitted_orders)
        item["residual_fill_attribution_state"] = "open_unresolved"
    elif stage == "residual_blocked":
        reason = str(fields.get("reason") or "unknown")
        explicit_recheck_allowed = _optional_boolish(
            fields.get("entry_split_probe_scale_in_recheck_allowed")
        )
        partial_submitted = bool(
            _boolish(fields.get("actual_order_submitted"))
            or int(_safe_float(fields.get("residual_submitted_qty"), 0.0) or 0.0) > 0
            or int(_safe_float(fields.get("residual_submitted_leg_count"), 0.0) or 0.0)
            > 0
        )
        soft_abort = bool(
            explicit_recheck_allowed is True
            or (
                explicit_recheck_allowed is None
                and reason in _SOFT_RESIDUAL_ABORT_REASONS
                and not partial_submitted
            )
        )
        item["residual_block_reason"] = reason
        item["residual_abort_detail_reason"] = str(
            fields.get("entry_split_probe_terminal_abort_detail_reason")
            or fields.get("residual_revalidation_timeout_cause")
            or "-"
        )
        item["residual_terminal_mixed_groups"] = str(
            fields.get("post_probe_direction_mixed_groups") or "-"
        )
        item["residual_terminal_orderbook_state"] = str(
            fields.get("post_probe_direction_orderbook_state") or "unknown"
        )
        item["residual_terminal_signed_pressure_source"] = str(
            fields.get("post_probe_direction_signed_pressure_source") or "unavailable"
        )
        item["residual_terminal_route_source_allowed"] = _optional_boolish(
            fields.get("post_probe_route_source_allowed")
        )
        item["residual_terminal_route_source_blockers"] = str(
            fields.get("post_probe_route_source_blockers") or "-"
        )
        item["residual_soft_abort"] = soft_abort
        item["residual_hard_or_capacity_abort"] = not soft_abort
        item["residual_partial_submitted_before_block"] = partial_submitted
        item["residual_scale_in_recheck_allowed"] = soft_abort
        if not partial_submitted:
            item["probe_bundle_terminal_seen"] = True
            item["probe_bundle_terminal_filled_qty"] = int(
                item.get("probe_fill_qty") or 1
            )
            item["probe_bundle_terminal_at"] = row.get("emitted_at")
    elif stage in {"residual_partial_complete", "bundle_completed"}:
        filled_qty = int(_safe_float(fields.get("filled_qty"), 0.0) or 0.0)
        if filled_qty > 0:
            item["probe_bundle_terminal_seen"] = True
            item["probe_bundle_terminal_filled_qty"] = filled_qty
            item["probe_bundle_terminal_at"] = row.get("emitted_at")


def _finalize_probe_residual_observation(item: dict[str, Any]) -> None:
    if not item.get("probe_residual_observation_seen"):
        return
    probe_fill_qty = max(1, int(item.get("probe_fill_qty") or 1))
    requested_qty = max(
        probe_fill_qty,
        int(item.get("forced_entry_qty") or probe_fill_qty),
    )
    residual_expected_qty = max(0, requested_qty - probe_fill_qty)
    item["residual_expected_qty"] = residual_expected_qty
    submitted_qty = max(0, int(item.get("residual_submitted_qty") or 0))
    item.setdefault("residual_fill_attribution_reasons", [])
    if item.get("residual_fill_attribution_valid") is False:
        item["residual_filled_qty"] = None
        item["residual_unfilled_qty"] = None
        item["residual_zero_fill"] = None
    elif not item.get("probe_bundle_terminal_seen"):
        item["residual_fill_attribution_valid"] = None
        item["residual_fill_attribution_state"] = "open_unresolved"
        item["residual_filled_qty"] = None
        item["residual_unfilled_qty"] = None
        item["residual_zero_fill"] = None
    else:
        terminal_filled_qty = max(
            probe_fill_qty,
            int(item.get("probe_bundle_terminal_filled_qty") or probe_fill_qty),
        )
        residual_filled_qty = max(0, terminal_filled_qty - probe_fill_qty)
        if (
            residual_filled_qty > residual_expected_qty
            or residual_filled_qty > submitted_qty
        ):
            item["residual_fill_attribution_valid"] = False
            item["residual_fill_attribution_state"] = (
                "filled_qty_exceeds_submitted_or_expected"
            )
            item["residual_fill_attribution_reasons"].append(
                "residual_filled_qty_exceeds_submitted_or_expected"
            )
            item["residual_filled_qty"] = None
            item["residual_unfilled_qty"] = None
            item["residual_zero_fill"] = None
        else:
            item["residual_fill_attribution_valid"] = True
            item["residual_filled_qty"] = residual_filled_qty
            item["residual_unfilled_qty"] = max(
                0, residual_expected_qty - residual_filled_qty
            )
            item["residual_zero_fill"] = bool(
                residual_expected_qty > 0 and residual_filled_qty == 0
            )
            item["residual_fill_attribution_state"] = (
                "zero_fill"
                if item["residual_zero_fill"]
                else (
                    "full_fill"
                    if residual_filled_qty == residual_expected_qty
                    else "partial_fill"
                )
            )
    max_profit_seen = _safe_float(item.get("max_profit_seen"), None)
    min_profit_pct = float(
        _safe_float(
            item.get("pyramid_opportunity_min_profit_pct"),
            _pyramid_min_profit_pct(),
        )
        or _pyramid_min_profit_pct()
    )
    item["residual_pyramid_threshold_missed_upside_candidate"] = bool(
        item.get("residual_zero_fill") is True
        and max_profit_seen is not None
        and max_profit_seen >= min_profit_pct
    )


def _probe_first_residual_leg_qty(item: dict[str, Any]) -> int | None:
    residual_qty = max(0, int(item.get("residual_unfilled_qty") or 0))
    total_leg_count = max(0, int(item.get("entry_split_order_leg_count") or 0))
    first_weight = _safe_float(item.get("entry_split_order_qty_weight_min"), None)
    if residual_qty <= 0 or total_leg_count <= 1 or first_weight is None:
        return None
    residual_leg_count = min(total_leg_count - 1, residual_qty)
    if residual_leg_count <= 1:
        return residual_qty
    return max(
        1,
        min(
            residual_qty - (residual_leg_count - 1),
            int(round(residual_qty * first_weight)),
        ),
    )


def _finalize_post_probe_real_confirmation(item: dict[str, Any]) -> None:
    observations = [
        observation
        for observation in item.get("post_probe_real_confirmation_observations") or []
        if isinstance(observation, dict)
        and _safe_float(observation.get("observed_epoch"), None) is not None
    ]
    observations.sort(
        key=lambda observation: float(observation.get("observed_epoch") or 0.0)
    )
    probe_filled_epoch = _event_epoch(item.get("probe_filled_at"))
    terminal_epoch = _event_epoch(item.get("probe_bundle_terminal_at"))
    confirmation_count = 0
    max_count = 0
    last_accepted_epoch: float | None = None
    last_signature = ""
    ready_at = None
    ready_signature = None
    excluded_count = 0
    source_quality_blockers: set[str] = set()
    for observation in observations:
        observed_epoch = float(observation["observed_epoch"])
        if (probe_filled_epoch is not None and observed_epoch < probe_filled_epoch) or (
            terminal_epoch is not None and observed_epoch > terminal_epoch
        ):
            excluded_count += 1
            continue
        source_quality_blockers.update(
            str(blocker)
            for blocker in observation.get("source_quality_blockers") or []
            if str(blocker)
        )
        if not bool(observation.get("eligible")):
            confirmation_count = 0
            last_accepted_epoch = None
            last_signature = ""
            continue
        evidence_signature = str(observation.get("evidence_signature") or "").strip()
        if confirmation_count <= 0:
            confirmation_count = 1
            last_accepted_epoch = observed_epoch
            last_signature = evidence_signature
        elif (
            last_accepted_epoch is not None
            and observed_epoch - last_accepted_epoch >= 0.25
            and evidence_signature
            and evidence_signature != last_signature
        ):
            confirmation_count += 1
            last_accepted_epoch = observed_epoch
            last_signature = evidence_signature
        max_count = max(max_count, confirmation_count)
        if confirmation_count >= 2 and ready_at is None:
            ready_at = observation.get("observed_at")
            ready_signature = evidence_signature
    item["post_probe_real_confirmation_max_count"] = max_count
    item["post_probe_real_confirmation_ready_at"] = ready_at
    item["post_probe_real_confirmation_ready_signature"] = ready_signature
    item["post_probe_real_confirmation_excluded_observation_count"] = excluded_count
    item["post_probe_real_confirmation_source_quality_blockers"] = sorted(
        source_quality_blockers
    )
    item.pop("post_probe_real_confirmation_observations", None)


def _finalize_post_probe_hard_abort_recovery(item: dict[str, Any]) -> None:
    observations = [
        observation
        for observation in item.get("post_probe_hard_abort_recovery_observations") or []
        if isinstance(observation, dict)
        and _safe_float(observation.get("observed_epoch"), None) is not None
    ]
    observations.sort(
        key=lambda observation: float(observation.get("observed_epoch") or 0.0)
    )
    terminal_epoch = _event_epoch(item.get("probe_bundle_terminal_at"))
    final_epoch = _event_epoch(item.get("final_ts"))
    confirmation_count = 0
    max_count = 0
    last_accepted_epoch: float | None = None
    last_signature = ""
    ready_at = None
    excluded_count = 0
    valid_window_evaluation_count = 0
    source_quality_blockers: set[str] = set()
    preserved_gap_count = 0
    ai_thesis_state_counts: Counter[str] = Counter()
    ai_tape_substitution_count = 0
    for observation in observations:
        observed_epoch = float(observation["observed_epoch"])
        if (terminal_epoch is not None and observed_epoch < terminal_epoch) or (
            final_epoch is not None and observed_epoch > final_epoch
        ):
            excluded_count += 1
            continue
        valid_window_evaluation_count += 1
        ai_thesis_state = str(
            observation.get("ai_thesis_state") or "unreported"
        ).strip()
        ai_thesis_state_counts[ai_thesis_state or "unreported"] += 1
        if bool(
            observation.get("ai_tape_substitution_applied")
            and ai_thesis_state == "supportive"
        ):
            ai_tape_substitution_count += 1
        source_quality_blockers.update(
            str(blocker)
            for blocker in observation.get("source_quality_blockers") or []
            if str(blocker)
        )
        if not bool(observation.get("eligible")):
            if bool(observation.get("confirmation_preserved")) and confirmation_count:
                preserved_gap_count += 1
                continue
            confirmation_count = 0
            last_accepted_epoch = None
            last_signature = ""
            continue
        signature = str(observation.get("evidence_signature") or "").strip()
        if confirmation_count <= 0:
            confirmation_count = 1
            last_accepted_epoch = observed_epoch
            last_signature = signature
        elif (
            last_accepted_epoch is not None
            and observed_epoch - last_accepted_epoch >= 0.25
            and signature
            and signature != last_signature
        ):
            confirmation_count += 1
            last_accepted_epoch = observed_epoch
            last_signature = signature
        max_count = max(max_count, confirmation_count)
        if confirmation_count >= 2 and ready_at is None:
            ready_at = observation.get("observed_at")
    item["post_probe_hard_abort_recovery_confirmation_max_count"] = max_count
    item["post_probe_hard_abort_recovery_confirmation_required_count"] = 2
    item["post_probe_hard_abort_recovery_confirmation_min_spacing_ms"] = 250
    item["post_probe_hard_abort_recovery_confirmation_ready"] = max_count >= 2
    item["post_probe_hard_abort_recovery_confirmation_ready_at"] = ready_at
    item["post_probe_hard_abort_recovery_excluded_observation_count"] = excluded_count
    item["post_probe_hard_abort_recovery_valid_window_evaluation_count"] = (
        valid_window_evaluation_count
    )
    item["post_probe_hard_abort_recovery_source_quality_blockers"] = sorted(
        source_quality_blockers
    )
    item["post_probe_hard_abort_recovery_confirmation_preserved_gap_count"] = (
        preserved_gap_count
    )
    item["post_probe_hard_abort_recovery_ai_thesis_state_counts"] = dict(
        sorted(ai_thesis_state_counts.items())
    )
    item["post_probe_hard_abort_recovery_ai_tape_substitution_count"] = (
        ai_tape_substitution_count
    )
    item.pop("post_probe_hard_abort_recovery_observations", None)


def _finalize_probe_residual_real_outcome(item: dict[str, Any]) -> None:
    if not item.get("probe_residual_observation_seen"):
        return
    _finalize_post_probe_real_confirmation(item)
    _finalize_post_probe_hard_abort_recovery(item)
    final_profit = _safe_float(item.get("final_profit_rate"), None)
    confirmation_ready = bool(
        int(item.get("post_probe_real_confirmation_max_count") or 0) >= 2
    )
    runtime_confirmation_count = int(item.get("probe_confirmation_max_count") or 0)
    runtime_confirmation_ready = bool(runtime_confirmation_count >= 2)
    item["post_probe_real_confirmation_ready"] = confirmation_ready
    item["post_probe_real_confirmation_required_count"] = 2
    item["post_probe_real_confirmation_min_spacing_ms"] = 250
    item["post_probe_runtime_confirmation_max_count"] = runtime_confirmation_count
    item["post_probe_runtime_confirmation_ready"] = runtime_confirmation_ready
    item["post_probe_confirmation_contract_alignment"] = (
        "runtime_and_source_quality_confirmed"
        if runtime_confirmation_ready and confirmation_ready
        else (
            "runtime_confirmed_source_quality_disputed"
            if runtime_confirmation_ready
            else "not_runtime_confirmed"
        )
    )
    item["post_probe_real_outcome_profit_pct"] = final_profit
    item["post_probe_probe_actual_order_submitted"] = bool(
        int(item.get("probe_fill_qty") or 0) > 0
    )
    item["post_probe_residual_actual_order_submitted"] = bool(
        int(item.get("residual_submitted_qty") or 0) > 0
    )
    reprice_candidates = [
        row
        for row in item.get("post_probe_reprice_observations") or []
        if isinstance(row, dict)
    ]
    reprice_observations = [
        row
        for row in reprice_candidates
        if str(row.get("profile") or "").strip().lower()
        not in {"", "unknown", "none", "not_available"}
        and str(row.get("action") or "").strip().lower()
        not in {"", "unknown", "none", "not_available"}
        and int(row.get("previous_price") or 0) > 0
        and int(row.get("resolved_price") or 0) > 0
    ]
    reprice_rejected_count = len(reprice_candidates) - len(reprice_observations)
    reprice_profiles = sorted(
        {str(row.get("profile") or "unknown") for row in reprice_observations}
    )
    reprice_improvement_bps = [
        round(
            (
                (int(row.get("previous_price") or 0) - int(row["resolved_price"]))
                / int(row.get("previous_price") or 1)
            )
            * 10000.0,
            4,
        )
        for row in reprice_observations
        if int(row.get("previous_price") or 0) > 0
    ]
    item["post_probe_reprice_observed"] = bool(reprice_observations)
    item["post_probe_reprice_candidate_leg_count"] = len(reprice_candidates)
    item["post_probe_reprice_profiles"] = reprice_profiles
    item["post_probe_reprice_leg_count"] = len(reprice_observations)
    item["post_probe_reprice_provenance_rejected_leg_count"] = reprice_rejected_count
    item["post_probe_reprice_provenance_complete"] = bool(
        reprice_candidates and reprice_rejected_count == 0
    )
    item["post_probe_reprice_avg_passive_improvement_bps"] = (
        round(sum(reprice_improvement_bps) / len(reprice_improvement_bps), 4)
        if reprice_improvement_bps
        else None
    )

    source_quality_reasons: list[str] = []
    if item.get("residual_fill_attribution_valid") is not True:
        source_quality_reasons.append(
            "residual_fill_attribution:"
            + str(item.get("residual_fill_attribution_state") or "unknown")
        )
    if item.get("venue_source_quality_valid") is not True:
        source_quality_reasons.append(
            "effective_venue:"
            + str(item.get("effective_venue_resolution") or "missing")
        )
    if final_profit is None:
        source_quality_reasons.append("real_sell_completed_profit_missing")
    if item.get("pyramid_submit_seen"):
        source_quality_reasons.append("later_pyramid_submit_contaminates_probe_outcome")
    item["post_probe_real_outcome_source_quality_reasons"] = source_quality_reasons
    item["post_probe_real_outcome_source_quality_valid"] = not source_quality_reasons
    reprice_source_quality_reasons = list(source_quality_reasons)
    if reprice_candidates and reprice_rejected_count:
        reprice_source_quality_reasons.append(
            "post_probe_reprice_provenance_incomplete"
        )
    if not reprice_candidates:
        reprice_source_quality_reasons.append("post_probe_reprice_observation_missing")
    item["post_probe_reprice_outcome_source_quality_reasons"] = (
        reprice_source_quality_reasons
    )
    item["post_probe_reprice_outcome_source_quality_valid"] = bool(
        item.get("post_probe_reprice_observed")
        and item.get("post_probe_reprice_provenance_complete")
        and not reprice_source_quality_reasons
    )

    if item.get("residual_fill_attribution_state") == "open_unresolved":
        label = "open_unresolved"
    elif source_quality_reasons:
        label = "source_quality_blocked"
    elif item.get("residual_zero_fill") is not True:
        label = "not_zero_fill"
    elif final_profit is not None and final_profit > 0:
        if confirmation_ready:
            label = "profitable_zero_fill_confirmation_ready"
        elif (
            item.get("residual_hard_or_capacity_abort")
            and not runtime_confirmation_ready
        ):
            if item.get("post_probe_hard_abort_recovery_confirmation_ready"):
                label = "profitable_zero_fill_recovery_confirmation_ready"
            elif (
                int(
                    item.get(
                        "post_probe_hard_abort_recovery_valid_window_evaluation_count"
                    )
                    or 0
                )
                > 0
            ):
                label = "profitable_zero_fill_recovery_not_confirmed"
            else:
                label = "profitable_zero_fill_recovery_evaluation_not_run"
        else:
            label = "profitable_zero_fill_no_confirmation"
    else:
        label = (
            "loss_or_flat_zero_fill_confirmation_ready"
            if confirmation_ready
            else "loss_or_flat_zero_fill_no_confirmation"
        )
    item["post_probe_real_outcome_label"] = label
    if label in {"source_quality_blocked", "open_unresolved", "not_zero_fill"}:
        runtime_label = label
    elif final_profit is not None and final_profit > 0:
        runtime_label = (
            "profitable_zero_fill_runtime_confirmation_ready"
            if runtime_confirmation_ready
            else "profitable_zero_fill_runtime_confirmation_absent"
        )
    else:
        runtime_label = (
            "loss_or_flat_zero_fill_runtime_confirmation_ready"
            if runtime_confirmation_ready
            else "loss_or_flat_zero_fill_runtime_confirmation_absent"
        )
    item["post_probe_runtime_outcome_label"] = runtime_label
    item["residual_missed_upside_candidate"] = bool(
        label
        in {
            "profitable_zero_fill_confirmation_ready",
            "profitable_zero_fill_recovery_confirmation_ready",
        }
    )
    item["runtime_confirmation_missed_upside_candidate"] = bool(
        label == "profitable_zero_fill_no_confirmation" and runtime_confirmation_ready
    )

    first_leg_qty = _probe_first_residual_leg_qty(item)
    probe_fill_price = _safe_float(item.get("probe_fill_price"), None)
    item["post_probe_counterfactual_first_leg_qty"] = first_leg_qty
    item["post_probe_counterfactual_price_source"] = (
        "probe_fill_price_proxy" if probe_fill_price is not None else "unavailable"
    )
    first_leg_notional = (
        int(round(first_leg_qty * probe_fill_price))
        if first_leg_qty is not None and probe_fill_price is not None
        else 0
    )
    item["post_probe_counterfactual_first_leg_notional_krw"] = first_leg_notional
    counterfactual_source_quality_reasons = []
    if not item["post_probe_real_outcome_source_quality_valid"]:
        counterfactual_source_quality_reasons.extend(source_quality_reasons)
    if first_leg_qty is None:
        counterfactual_source_quality_reasons.append("first_residual_leg_plan_missing")
    if probe_fill_price is None:
        counterfactual_source_quality_reasons.append("probe_fill_price_missing")
    item["post_probe_counterfactual_source_quality_reasons"] = (
        counterfactual_source_quality_reasons
    )
    item["post_probe_counterfactual_source_quality_valid"] = (
        not counterfactual_source_quality_reasons
    )
    item["post_probe_counterfactual_first_leg_profit_proxy_krw"] = (
        round(first_leg_notional * final_profit / 100.0, 2)
        if first_leg_notional > 0 and final_profit is not None
        else None
    )


def _apply_daily_pyramid_threshold_provenance(
    one_share_records: dict[str, dict[str, Any]],
    candidates: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    observed_thresholds = sorted(
        {
            round(float(value), 6)
            for item in candidates.values()
            for value in [_safe_float(item.get("min_profit_pct"), None)]
            if value is not None and value > 0
        }
    )
    unique_runtime_threshold = (
        observed_thresholds[0] if len(observed_thresholds) == 1 else None
    )
    for item in one_share_records.values():
        threshold_source = str(item.get("pyramid_opportunity_threshold_source") or "")
        if threshold_source != "exact_pyramid_evaluation_event":
            if unique_runtime_threshold is not None:
                item["pyramid_opportunity_min_profit_pct"] = unique_runtime_threshold
                item["pyramid_opportunity_threshold_source"] = (
                    "same_day_unique_runtime_pyramid_evaluation"
                )
            else:
                item["pyramid_opportunity_min_profit_pct"] = _pyramid_min_profit_pct()
                item["pyramid_opportunity_threshold_source"] = (
                    "static_fallback_no_unique_runtime_threshold"
                )
        threshold = float(item["pyramid_opportunity_min_profit_pct"])
        max_profit_seen = _safe_float(item.get("max_profit_seen"), None)
        if (
            not item.get("pyramid_opportunity_seen")
            and max_profit_seen is not None
            and max_profit_seen >= threshold
        ):
            item["pyramid_opportunity_seen"] = True
            item["pyramid_opportunity_ts"] = item.get("latest_snapshot_ts")
            item["pyramid_opportunity_profit_rate"] = threshold
            item["pyramid_opportunity_peak_profit"] = max_profit_seen
            item["pyramid_opportunity_source"] = (
                "holding_peak_runtime_threshold_crossed_postscan"
            )
            if (
                item.get("scale_in_blocker_reason")
                == "one_share_pyramid_no_opportunity_seen"
            ):
                item["scale_in_blocker_reason"] = (
                    "one_share_pyramid_not_submitted_opportunity"
                )
    return {
        "observed_min_profit_pct_values": observed_thresholds,
        "selected_min_profit_pct": (
            unique_runtime_threshold
            if unique_runtime_threshold is not None
            else _pyramid_min_profit_pct()
        ),
        "selection_source": (
            "same_day_unique_runtime_pyramid_evaluation"
            if unique_runtime_threshold is not None
            else "static_fallback_no_unique_runtime_threshold"
        ),
        "ambiguous": len(observed_thresholds) > 1,
    }


def _incremental_return_pct(
    outcome_profit_pct: float | None, entry_profit_pct: float | None
) -> float | None:
    if outcome_profit_pct is None or entry_profit_pct is None:
        return None
    denominator = 1.0 + (float(entry_profit_pct) / 100.0)
    if denominator <= 0:
        return None
    return round(
        (((1.0 + (float(outcome_profit_pct) / 100.0)) / denominator) - 1.0) * 100.0,
        4,
    )


def _update_normal_winner_expansion_candidate(
    item: dict[str, Any], blocked: dict[str, Any], row: dict[str, Any]
) -> bool:
    profit_rate = _safe_float(blocked.get("profit_rate"), None)
    if profit_rate is None or profit_rate <= 0:
        return True
    if _event_after_final(item, row):
        reason = "temporal_inversion:candidate_after_final_ts"
        candidate = {
            "observed_at": row.get("emitted_at"),
            "profit_rate": profit_rate,
            "scale_in_blocker_reason": blocked.get("scale_in_blocker_reason"),
            "source_quality_valid": False,
            "source_quality_reason": reason,
            "final_ts": item.get("final_ts"),
        }
        item.setdefault("normal_winner_expansion_candidates", []).append(candidate)
        item["normal_winner_expansion_candidate_count"] = len(
            item["normal_winner_expansion_candidates"]
        )
        item["normal_winner_expansion_candidate_seen"] = True
        item["normal_winner_expansion_temporal_inversion"] = True
        item["normal_winner_expansion_temporal_inversion_candidate_at"] = row.get(
            "emitted_at"
        )
        item["normal_winner_expansion_source_quality_valid"] = False
        reasons = list(item.get("normal_winner_expansion_source_quality_reasons") or [])
        if reason not in reasons:
            reasons.append(reason)
        item["normal_winner_expansion_source_quality_reasons"] = reasons
        return False
    ai_tape_substitution_applied = bool(
        blocked.get("recovery_ai_tape_substitution_applied")
        and str(blocked.get("recovery_ai_thesis_state") or "").strip().lower()
        == "supportive"
    )
    source_quality_valid = bool(
        not _pressure_provenance_missing(blocked)
        and (
            not _pressure_provenance_unusable(blocked)
            or ai_tape_substitution_applied
        )
        and not _micro_vwap_provenance_missing(blocked)
        and not _micro_vwap_provenance_unusable(blocked)
    )
    candidate = {
        "observed_at": row.get("emitted_at"),
        "profit_rate": profit_rate,
        "scale_in_blocker_reason": blocked.get("scale_in_blocker_reason"),
        "scale_in_blocker_namespace": blocked.get("scale_in_blocker_namespace"),
        "recovery_abort_class": blocked.get("recovery_abort_class"),
        "current_ai_score": blocked.get("current_ai_score"),
        "buy_pressure_10t": blocked.get("buy_pressure_10t"),
        "tick_acceleration_ratio": blocked.get("tick_acceleration_ratio"),
        "curr_vs_micro_vwap_bp": blocked.get("curr_vs_micro_vwap_bp"),
        "recovery_ai_thesis_state": blocked.get("recovery_ai_thesis_state"),
        "recovery_ai_tape_substitution_applied": blocked.get(
            "recovery_ai_tape_substitution_applied"
        ),
        "recovery_ai_parent_prompt_version": blocked.get(
            "recovery_ai_parent_prompt_version"
        ),
        "recovery_holding_ai_action": blocked.get("recovery_holding_ai_action"),
        "recovery_holding_ai_data_quality": blocked.get(
            "recovery_holding_ai_data_quality"
        ),
        "source_quality_valid": source_quality_valid,
    }
    item.setdefault("normal_winner_expansion_candidates", []).append(candidate)
    item["normal_winner_expansion_candidate_count"] = len(
        item["normal_winner_expansion_candidates"]
    )
    if item.get("normal_winner_expansion_candidate_seen"):
        return
    item["normal_winner_expansion_candidate_seen"] = True
    item["normal_winner_expansion_candidate_at"] = row.get("emitted_at")
    item["normal_winner_expansion_entry_profit_pct"] = profit_rate
    item["normal_winner_expansion_blocker_reason"] = blocked.get(
        "scale_in_blocker_reason"
    )
    item["normal_winner_expansion_blocker_namespace"] = blocked.get(
        "scale_in_blocker_namespace"
    )
    item["normal_winner_expansion_recovery_abort_class"] = blocked.get(
        "recovery_abort_class"
    )
    item["normal_winner_expansion_current_ai_score"] = blocked.get("current_ai_score")
    item["normal_winner_expansion_buy_pressure_10t"] = blocked.get("buy_pressure_10t")
    item["normal_winner_expansion_tick_acceleration_ratio"] = blocked.get(
        "tick_acceleration_ratio"
    )
    item["normal_winner_expansion_curr_vs_micro_vwap_bp"] = blocked.get(
        "curr_vs_micro_vwap_bp"
    )
    item["normal_winner_expansion_recovery_ai_thesis_state"] = blocked.get(
        "recovery_ai_thesis_state"
    )
    item["normal_winner_expansion_recovery_ai_tape_substitution_applied"] = bool(
        blocked.get("recovery_ai_tape_substitution_applied")
    )
    item["normal_winner_expansion_recovery_ai_parent_prompt_version"] = blocked.get(
        "recovery_ai_parent_prompt_version"
    )
    item["normal_winner_expansion_recovery_holding_ai_action"] = blocked.get(
        "recovery_holding_ai_action"
    )
    item["normal_winner_expansion_recovery_holding_ai_data_quality"] = blocked.get(
        "recovery_holding_ai_data_quality"
    )
    item["normal_winner_expansion_source_quality_valid"] = source_quality_valid
    item["normal_winner_expansion_post_candidate_max_profit_pct"] = profit_rate
    item["normal_winner_expansion_post_candidate_min_profit_pct"] = profit_rate
    return True


def _finalize_normal_winner_expansion(item: dict[str, Any]) -> None:
    if not item.get("normal_winner_expansion_candidate_seen"):
        item["normal_winner_expansion_label"] = "not_observed"
        return
    candidate_at = item.get("normal_winner_expansion_candidate_at")
    if (
        candidate_at
        and _event_epoch(candidate_at) is not None
        and _event_epoch(item.get("final_ts")) is not None
        and _event_epoch(candidate_at) > _event_epoch(item.get("final_ts"))
    ):
        reason = "temporal_inversion:candidate_after_final_ts"
        item["normal_winner_expansion_temporal_inversion"] = True
        item["normal_winner_expansion_temporal_inversion_candidate_at"] = candidate_at
        item["normal_winner_expansion_source_quality_valid"] = False
        for key in (
            "normal_winner_expansion_candidate_at",
            "normal_winner_expansion_entry_profit_pct",
            "normal_winner_expansion_post_candidate_max_profit_pct",
            "normal_winner_expansion_post_candidate_min_profit_pct",
        ):
            item.pop(key, None)
        reasons = list(item.get("normal_winner_expansion_source_quality_reasons") or [])
        if reason not in reasons:
            reasons.append(reason)
        item["normal_winner_expansion_source_quality_reasons"] = reasons
    base_source_quality_valid = bool(
        item.get("normal_winner_expansion_source_quality_valid")
    )
    source_quality_reasons = list(
        item.get("normal_winner_expansion_source_quality_reasons") or []
    )
    if item.get("residual_fill_attribution_valid") is not True:
        source_quality_reasons.append(
            f"residual_fill_attribution:{item.get('residual_fill_attribution_state') or 'unknown'}"
        )
    if not bool(item.get("venue_source_quality_valid")):
        source_quality_reasons.append(
            f"effective_venue:{item.get('effective_venue_resolution') or 'missing'}"
        )
    item["normal_winner_expansion_source_quality_valid"] = bool(
        base_source_quality_valid and not source_quality_reasons
    )
    item["normal_winner_expansion_source_quality_reasons"] = list(
        dict.fromkeys(source_quality_reasons)
    )
    entry_profit = _safe_float(
        item.get("normal_winner_expansion_entry_profit_pct"), None
    )
    post_max = _safe_float(
        item.get("normal_winner_expansion_post_candidate_max_profit_pct"), None
    )
    post_min = _safe_float(
        item.get("normal_winner_expansion_post_candidate_min_profit_pct"), None
    )
    final_profit = _safe_float(item.get("final_profit_rate"), None)
    gross_incremental_mfe = _incremental_return_pct(post_max, entry_profit)
    gross_incremental_mae = _incremental_return_pct(post_min, entry_profit)
    gross_incremental_final = _incremental_return_pct(final_profit, entry_profit)
    assumed_trade_cost_pct = round(
        max(0.0, float(getattr(TRADING_RULES, "TRADE_COST_RATE", 0.0) or 0.0)) * 100.0,
        4,
    )
    incremental_mfe = (
        round(gross_incremental_mfe - assumed_trade_cost_pct, 4)
        if gross_incremental_mfe is not None
        else None
    )
    incremental_mae = (
        round(gross_incremental_mae - assumed_trade_cost_pct, 4)
        if gross_incremental_mae is not None
        else None
    )
    incremental_final = (
        round(gross_incremental_final - assumed_trade_cost_pct, 4)
        if gross_incremental_final is not None
        else None
    )
    item["normal_winner_expansion_assumed_trade_cost_pct"] = assumed_trade_cost_pct
    item["normal_winner_expansion_gross_incremental_mfe_pct"] = gross_incremental_mfe
    item["normal_winner_expansion_gross_incremental_mae_pct"] = gross_incremental_mae
    item["normal_winner_expansion_gross_incremental_final_profit_pct"] = (
        gross_incremental_final
    )
    item["normal_winner_expansion_incremental_mfe_pct"] = incremental_mfe
    item["normal_winner_expansion_incremental_mae_pct"] = incremental_mae
    item["normal_winner_expansion_incremental_final_profit_pct"] = incremental_final
    residual_unfilled_qty = max(0, int(item.get("residual_unfilled_qty") or 0))
    probe_fill_price = _safe_float(item.get("probe_fill_price"), None)
    candidate_price = (
        float(probe_fill_price) * (1.0 + (float(entry_profit) / 100.0))
        if probe_fill_price is not None and entry_profit is not None
        else None
    )
    item["normal_winner_expansion_candidate_notional_krw"] = (
        int(round(candidate_price * residual_unfilled_qty))
        if candidate_price is not None and candidate_price > 0
        else 0
    )
    residual_fill_state = str(item.get("residual_fill_attribution_state") or "").strip()
    if residual_fill_state == "open_unresolved":
        label = "open_unresolved"
    elif not item.get("normal_winner_expansion_source_quality_valid"):
        label = "source_quality_blocked"
    elif residual_unfilled_qty <= 0:
        label = "not_underexpanded"
    elif final_profit is None:
        label = "open_unresolved"
    elif incremental_final is not None and incremental_final > 0:
        label = "realized_incremental_winner"
    elif incremental_mfe is not None and incremental_mfe >= 0.5:
        label = "transient_extension_exit_timing_needed"
    else:
        label = "correctly_not_expanded_or_reversal"
    item["normal_winner_expansion_label"] = label


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
    _update_scout_ai_execution_attribution(item, row)
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
    post_probe_closed = [
        item
        for item in rows
        if str(item.get("post_probe_real_outcome_label") or "")
        in {
            "profitable_zero_fill_confirmation_ready",
            "profitable_zero_fill_no_confirmation",
            "profitable_zero_fill_recovery_confirmation_ready",
            "profitable_zero_fill_recovery_not_confirmed",
            "profitable_zero_fill_recovery_evaluation_not_run",
            "loss_or_flat_zero_fill_confirmation_ready",
            "loss_or_flat_zero_fill_no_confirmation",
        }
    ]
    post_probe_confirmation_ready = [
        item
        for item in post_probe_closed
        if bool(item.get("post_probe_real_confirmation_ready"))
    ]
    post_probe_counterfactual_ev_eligible = [
        item
        for item in post_probe_confirmation_ready
        if bool(item.get("post_probe_counterfactual_source_quality_valid"))
    ]
    post_probe_profit_values = [
        float(item["post_probe_real_outcome_profit_pct"])
        for item in post_probe_counterfactual_ev_eligible
        if item.get("post_probe_real_outcome_profit_pct") is not None
    ]
    post_probe_weighted_values = [
        (
            float(item["post_probe_real_outcome_profit_pct"]),
            int(item.get("post_probe_counterfactual_first_leg_notional_krw") or 0),
        )
        for item in post_probe_counterfactual_ev_eligible
        if item.get("post_probe_real_outcome_profit_pct") is not None
        and int(item.get("post_probe_counterfactual_first_leg_notional_krw") or 0) > 0
    ]
    post_probe_profit_proxies = [
        float(item["post_probe_counterfactual_first_leg_profit_proxy_krw"])
        for item in post_probe_counterfactual_ev_eligible
        if item.get("post_probe_counterfactual_first_leg_profit_proxy_krw") is not None
    ]
    post_probe_winner_count = sum(
        1
        for item in post_probe_closed
        if str(item.get("post_probe_real_outcome_label") or "").startswith(
            "profitable_zero_fill"
        )
    )
    canonical_label_counts = Counter(
        str(item.get("canonical_expansion_outcome_label") or "expansion_not_observed")
        for item in rows
    )
    closed_attribution_rows = [
        item for item in rows if str(item.get("final_stage") or "") == "sell_completed"
    ]
    closed_attribution_complete = [
        item
        for item in closed_attribution_rows
        if item.get("scout_ai_attribution_status") == "linked_frozen_parent"
        and not item.get("scout_ai_attribution_conflict")
        and _SCOUT_AI_ATTRIBUTION_REQUIRED_CLOSED_STAGES.issubset(
            set(item.get("scout_ai_attribution_lifecycle_stages") or [])
        )
    ]
    return {
        "one_share_event_count": len(rows),
        "scout_ai_attribution_linked_count": sum(
            1
            for item in rows
            if item.get("scout_ai_attribution_status") == "linked_frozen_parent"
            and not item.get("scout_ai_attribution_conflict")
        ),
        "scout_ai_attribution_incomplete_count": sum(
            1
            for item in rows
            if item.get("scout_ai_attribution_status")
            == "parent_provenance_incomplete"
        ),
        "scout_ai_attribution_pre_ai_pending_count": sum(
            1
            for item in rows
            if item.get("scout_ai_attribution_status")
            == "parent_ai_not_evaluated_yet"
        ),
        "scout_ai_attribution_probe_bundle_pending_count": sum(
            1
            for item in rows
            if item.get("scout_ai_attribution_status")
            == "linked_parent_pending_probe_bundle"
        ),
        "scout_ai_attribution_conflict_count": sum(
            1 for item in rows if item.get("scout_ai_attribution_conflict")
        ),
        "scout_ai_attribution_closed_full_lifecycle_count": len(
            closed_attribution_complete
        ),
        "scout_ai_attribution_closed_incomplete_lifecycle_count": (
            len(closed_attribution_rows) - len(closed_attribution_complete)
        ),
        "scout_ai_attribution_open_pending_lifecycle_count": (
            len(rows) - len(closed_attribution_rows)
        ),
        "one_share_closed_count": len(closed),
        "one_share_pyramid_opportunity_count": len(opportunity_rows),
        "one_share_pyramid_missed_upside_count": len(missed),
        "one_share_pyramid_missed_upside_rate": (
            len(missed) / len(closed) if closed else 0.0
        ),
        "one_share_pyramid_avg_opportunity_cost_pct": (
            sum(costs) / len(costs) if costs else 0.0
        ),
        "probe_residual_zero_fill_count": sum(
            1 for item in rows if item.get("residual_zero_fill")
        ),
        "probe_residual_soft_abort_count": sum(
            1 for item in rows if item.get("residual_soft_abort")
        ),
        "probe_residual_missed_upside_candidate_count": sum(
            1 for item in rows if item.get("residual_missed_upside_candidate")
        ),
        "probe_residual_pyramid_threshold_missed_upside_candidate_count": sum(
            1
            for item in rows
            if item.get("residual_pyramid_threshold_missed_upside_candidate")
        ),
        "probe_residual_real_outcome_closed_count": len(post_probe_closed),
        "probe_residual_realized_winner_zero_fill_count": post_probe_winner_count,
        "probe_residual_realized_loss_or_flat_zero_fill_count": (
            len(post_probe_closed) - post_probe_winner_count
        ),
        "probe_residual_realized_winner_confirmation_ready_count": sum(
            1
            for item in post_probe_closed
            if item.get("post_probe_real_outcome_label")
            in {
                "profitable_zero_fill_confirmation_ready",
                "profitable_zero_fill_recovery_confirmation_ready",
            }
        ),
        "post_hard_abort_recovery_evaluation_seen_count": sum(
            1
            for item in post_probe_closed
            if item.get("post_probe_hard_abort_recovery_evaluation_seen")
        ),
        "post_hard_abort_recovery_confirmation_ready_count": sum(
            1
            for item in post_probe_closed
            if item.get("post_probe_hard_abort_recovery_confirmation_ready")
        ),
        "post_terminal_abort_recovery_evaluation_seen_count": sum(
            1
            for item in post_probe_closed
            if item.get("post_probe_hard_abort_recovery_evaluation_seen")
        ),
        "post_terminal_abort_recovery_confirmation_ready_count": sum(
            1
            for item in post_probe_closed
            if item.get("post_probe_hard_abort_recovery_confirmation_ready")
        ),
        "post_terminal_abort_recovery_confirmation_preserved_gap_count": sum(
            int(
                item.get(
                    "post_probe_hard_abort_recovery_confirmation_preserved_gap_count"
                )
                or 0
            )
            for item in post_probe_closed
        ),
        "post_terminal_abort_recovery_ai_supportive_evaluation_count": sum(
            int(
                (
                    item.get("post_probe_hard_abort_recovery_ai_thesis_state_counts")
                    or {}
                ).get("supportive")
                or 0
            )
            for item in post_probe_closed
        ),
        "post_terminal_abort_recovery_ai_tape_substitution_count": sum(
            int(
                item.get(
                    "post_probe_hard_abort_recovery_ai_tape_substitution_count"
                )
                or 0
            )
            for item in post_probe_closed
        ),
        "post_terminal_abort_recovery_hard_count": sum(
            1
            for item in post_probe_closed
            if item.get("post_probe_terminal_abort_recovery_latest_class") == "hard"
        ),
        "post_terminal_abort_recovery_soft_count": sum(
            1
            for item in post_probe_closed
            if item.get("post_probe_terminal_abort_recovery_latest_class") == "soft"
        ),
        "post_hard_abort_recovery_evaluation_not_run_profitable_count": sum(
            1
            for item in post_probe_closed
            if item.get("post_probe_real_outcome_label")
            == "profitable_zero_fill_recovery_evaluation_not_run"
        ),
        "probe_residual_realized_loss_or_flat_confirmation_ready_count": sum(
            1
            for item in post_probe_closed
            if item.get("post_probe_real_outcome_label")
            == "loss_or_flat_zero_fill_confirmation_ready"
        ),
        "canonical_expansion_missed_upside_count": canonical_label_counts.get(
            "expansion_missed_upside_confirmation_ready", 0
        )
        + canonical_label_counts.get("expansion_missed_upside_threshold_crossed", 0)
        + canonical_label_counts.get(
            "expansion_missed_upside_runtime_confirmed_source_quality_disputed", 0
        )
        + canonical_label_counts.get(
            "expansion_recovery_missed_upside_confirmation_ready", 0
        ),
        "canonical_expansion_source_quality_valid_missed_upside_count": (
            canonical_label_counts.get("expansion_missed_upside_confirmation_ready", 0)
            + canonical_label_counts.get("expansion_missed_upside_threshold_crossed", 0)
            + canonical_label_counts.get(
                "expansion_recovery_missed_upside_confirmation_ready", 0
            )
        ),
        "post_probe_runtime_confirmation_source_quality_disputed_count": sum(
            1
            for item in rows
            if item.get("post_probe_confirmation_contract_alignment")
            == "runtime_confirmed_source_quality_disputed"
        ),
        "post_probe_legacy_label_conflict_count": sum(
            1 for item in rows if item.get("post_probe_legacy_label_conflict")
        ),
        "post_probe_confirmation_false_positive_loss_or_flat_count": (
            canonical_label_counts.get(
                "expansion_confirmation_false_positive_loss_or_flat", 0
            )
        ),
        "probe_residual_confirmation_ready_counterfactual_ev_eligible_count": len(
            post_probe_counterfactual_ev_eligible
        ),
        "probe_residual_confirmation_ready_counterfactual_source_blocked_count": (
            len(post_probe_confirmation_ready)
            - len(post_probe_counterfactual_ev_eligible)
        ),
        "probe_residual_real_outcome_source_quality_blocked_count": sum(
            1
            for item in rows
            if item.get("post_probe_real_outcome_label") == "source_quality_blocked"
        ),
        "probe_residual_real_outcome_diagnostic_win_rate": (
            post_probe_winner_count / len(post_probe_closed)
            if post_probe_closed
            else 0.0
        ),
        "probe_residual_confirmation_ready_equal_weight_avg_profit_pct": (
            sum(post_probe_profit_values) / len(post_probe_profit_values)
            if post_probe_profit_values
            else 0.0
        ),
        "probe_residual_confirmation_ready_notional_weighted_ev_pct": (
            sum(value * notional for value, notional in post_probe_weighted_values)
            / sum(notional for _, notional in post_probe_weighted_values)
            if post_probe_weighted_values
            else 0.0
        ),
        "probe_residual_confirmation_ready_simple_sum_profit_proxy_krw": round(
            sum(post_probe_profit_proxies), 2
        ),
        "probe_residual_pyramid_evaluation_seen_count": sum(
            1 for item in rows if item.get("pyramid_evaluation_seen")
        ),
        "probe_residual_fill_attribution_invalid_count": sum(
            1 for item in rows if item.get("residual_fill_attribution_valid") is False
        ),
        "probe_residual_fill_open_unresolved_count": sum(
            1
            for item in rows
            if item.get("residual_fill_attribution_state") == "open_unresolved"
        ),
        "probe_residual_venue_source_quality_invalid_count": sum(
            1
            for item in rows
            if item.get("probe_residual_observation_seen")
            and item.get("venue_source_quality_valid") is not True
        ),
        "one_share_pyramid_label_counts": [
            {"pyramid_feedback_label": key, "count": value}
            for key, value in label_counts.most_common()
        ],
        "one_share_pyramid_label_semantics": "legacy_profit_threshold_crossing_only",
        "canonical_expansion_label_counts": [
            {"canonical_expansion_outcome_label": key, "count": value}
            for key, value in canonical_label_counts.most_common()
        ],
        "canonical_expansion_label_semantics": (
            "post_probe_real_confirmation_precedence_then_legacy_threshold"
        ),
    }


def _normal_winner_expansion_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = [
        item
        for item in rows
        if bool(item.get("normal_winner_expansion_candidate_seen"))
        and (
            int(item.get("residual_unfilled_qty") or 0) > 0
            or str(item.get("residual_fill_attribution_state") or "")
            in {
                "open_unresolved",
                "bundle_mismatch",
                "submission_order_no_missing",
                "filled_qty_exceeds_submitted_or_expected",
            }
        )
    ]
    valid = [
        item
        for item in candidates
        if bool(item.get("normal_winner_expansion_source_quality_valid"))
    ]
    closed = [
        item
        for item in valid
        if item.get("normal_winner_expansion_label") != "open_unresolved"
    ]
    final_values = [
        value
        for item in closed
        for value in [
            _safe_float(
                item.get("normal_winner_expansion_incremental_final_profit_pct"),
                None,
            )
        ]
        if value is not None
    ]
    weighted_values = [
        (value, int(item.get("normal_winner_expansion_candidate_notional_krw") or 0))
        for item in closed
        for value in [
            _safe_float(
                item.get("normal_winner_expansion_incremental_final_profit_pct"),
                None,
            )
        ]
        if value is not None
        and int(item.get("normal_winner_expansion_candidate_notional_krw") or 0) > 0
    ]
    label_counts = Counter(
        str(item.get("normal_winner_expansion_label") or "not_observed")
        for item in candidates
    )
    signature_counts: Counter[str] = Counter()
    signature_winners: Counter[str] = Counter()
    for item in valid:
        signature = (
            "two_consecutive_strong_no_negative"
            if (
                int(item.get("probe_confirmation_max_count") or 0) >= 2
                or int(item.get("probe_direction_max_consecutive_strong_count") or 0)
                >= 2
            )
            and not bool(item.get("probe_direction_negative_seen"))
            else (
                "strong_seen_but_not_confirmed"
                if int(item.get("probe_direction_strong_evaluation_count") or 0) > 0
                else (
                    "negative_group_seen"
                    if bool(item.get("probe_direction_negative_seen"))
                    else "no_directional_confirmation"
                )
            )
        )
        item["normal_winner_expansion_probe_confirmation_signature"] = signature
        signature_counts[signature] += 1
        if item.get("normal_winner_expansion_label") == "realized_incremental_winner":
            signature_winners[signature] += 1

    def _bucket(value: float | None, cuts: tuple[float, float]) -> str:
        if value is None:
            return "unknown"
        if value < cuts[0]:
            return f"lt_{cuts[0]:g}"
        if value < cuts[1]:
            return f"{cuts[0]:g}_to_{cuts[1]:g}"
        return f"ge_{cuts[1]:g}"

    axis_getters = {
        "entry_profit_pct": lambda item: _bucket(
            _safe_float(item.get("normal_winner_expansion_entry_profit_pct"), None),
            (0.4, 0.8),
        ),
        "ai_score": lambda item: _bucket(
            _safe_float(item.get("normal_winner_expansion_current_ai_score"), None),
            (60.0, 70.0),
        ),
        "buy_pressure_10t": lambda item: _bucket(
            _safe_float(item.get("normal_winner_expansion_buy_pressure_10t"), None),
            (50.0, 70.0),
        ),
        "tick_acceleration_ratio": lambda item: _bucket(
            _safe_float(
                item.get("normal_winner_expansion_tick_acceleration_ratio"), None
            ),
            (0.5, 1.0),
        ),
        "micro_vwap_side": lambda item: (
            "unknown"
            if _safe_float(
                item.get("normal_winner_expansion_curr_vs_micro_vwap_bp"), None
            )
            is None
            else (
                "negative"
                if _safe_float(
                    item.get("normal_winner_expansion_curr_vs_micro_vwap_bp"),
                    0.0,
                )
                < 0
                else "non_negative"
            )
        ),
        "recovery_ai_thesis_state": lambda item: str(
            item.get("normal_winner_expansion_recovery_ai_thesis_state")
            or "unreported"
        ),
        "recovery_ai_tape_substitution": lambda item: (
            "applied"
            if item.get(
                "normal_winner_expansion_recovery_ai_tape_substitution_applied"
            )
            else "not_applied"
        ),
        "recovery_ai_parent_prompt_version": lambda item: str(
            item.get("normal_winner_expansion_recovery_ai_parent_prompt_version")
            or "unreported"
        ),
        "recovery_holding_ai_action": lambda item: str(
            item.get("normal_winner_expansion_recovery_holding_ai_action")
            or "unreported"
        ),
        "recovery_holding_ai_data_quality": lambda item: str(
            item.get("normal_winner_expansion_recovery_holding_ai_data_quality")
            or "unreported"
        ),
        "blocker_reason": lambda item: str(
            item.get("normal_winner_expansion_blocker_reason") or "unknown"
        ),
    }
    feature_axis_metrics: dict[str, list[dict[str, Any]]] = {}
    for axis, getter in axis_getters.items():
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in closed:
            grouped[getter(item)].append(item)
        axis_rows = []
        for bucket, bucket_items in sorted(grouped.items()):
            weighted = [
                (
                    _safe_float(
                        item.get(
                            "normal_winner_expansion_incremental_final_profit_pct"
                        ),
                        0.0,
                    ),
                    int(
                        item.get("normal_winner_expansion_candidate_notional_krw") or 0
                    ),
                )
                for item in bucket_items
                if int(item.get("normal_winner_expansion_candidate_notional_krw") or 0)
                > 0
            ]
            axis_rows.append(
                {
                    "bucket": bucket,
                    "sample_count": len(bucket_items),
                    "realized_incremental_winner_count": sum(
                        1
                        for item in bucket_items
                        if item.get("normal_winner_expansion_label")
                        == "realized_incremental_winner"
                    ),
                    "notional_weighted_ev_pct": (
                        round(
                            sum(value * notional for value, notional in weighted)
                            / sum(notional for _, notional in weighted),
                            4,
                        )
                        if weighted
                        else 0.0
                    ),
                    "daily_only_live_authority": False,
                }
            )
        feature_axis_metrics[axis] = axis_rows

    def _dimension_metrics(
        dimension: str, dimension_rows: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in dimension_rows:
            value = str(item.get(dimension) or "UNKNOWN").strip() or "UNKNOWN"
            grouped[value].append(item)
        metrics = []
        for value, bucket_items in sorted(grouped.items()):
            bucket_weighted = [
                (
                    _safe_float(
                        item.get(
                            "normal_winner_expansion_incremental_final_profit_pct"
                        ),
                        0.0,
                    ),
                    int(
                        item.get("normal_winner_expansion_candidate_notional_krw") or 0
                    ),
                )
                for item in bucket_items
                if int(item.get("normal_winner_expansion_candidate_notional_krw") or 0)
                > 0
            ]
            metrics.append(
                {
                    dimension: value,
                    "sample_count": len(bucket_items),
                    "realized_incremental_winner_count": sum(
                        1
                        for item in bucket_items
                        if item.get("normal_winner_expansion_label")
                        == "realized_incremental_winner"
                    ),
                    "notional_weighted_ev_pct": (
                        round(
                            sum(
                                outcome * notional
                                for outcome, notional in bucket_weighted
                            )
                            / sum(notional for _, notional in bucket_weighted),
                            4,
                        )
                        if bucket_weighted
                        else 0.0
                    ),
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                }
            )
        return metrics

    venue_valid_closed = [
        item
        for item in closed
        if bool(item.get("venue_source_quality_valid"))
        and str(item.get("effective_venue") or "")
        in {"KRX", "NXT", "PREMARKET_KRX_LIKE"}
    ]
    return {
        "candidate_count": len(candidates),
        "temporal_inversion_candidate_count": sum(
            1
            for item in candidates
            if bool(item.get("normal_winner_expansion_temporal_inversion"))
        ),
        "source_quality_valid_candidate_count": len(valid),
        "source_quality_blocked_candidate_count": len(candidates) - len(valid),
        "closed_candidate_count": len(closed),
        "realized_incremental_winner_count": label_counts.get(
            "realized_incremental_winner", 0
        ),
        "transient_extension_exit_timing_needed_count": label_counts.get(
            "transient_extension_exit_timing_needed", 0
        ),
        "correctly_not_expanded_or_reversal_count": label_counts.get(
            "correctly_not_expanded_or_reversal", 0
        ),
        "equal_weight_avg_profit_pct": (
            round(sum(final_values) / len(final_values), 4) if final_values else 0.0
        ),
        "notional_weighted_ev_pct": (
            round(
                sum(value * notional for value, notional in weighted_values)
                / sum(notional for _, notional in weighted_values),
                4,
            )
            if weighted_values
            else 0.0
        ),
        "diagnostic_win_rate": (
            round(
                label_counts.get("realized_incremental_winner", 0) / len(closed),
                4,
            )
            if closed
            else 0.0
        ),
        "label_counts": [
            {"label": key, "count": value} for key, value in label_counts.most_common()
        ],
        "probe_confirmation_signature_metrics": [
            {
                "signature": signature,
                "sample_count": count,
                "realized_incremental_winner_count": signature_winners.get(
                    signature, 0
                ),
                "diagnostic_win_rate": round(
                    signature_winners.get(signature, 0) / count, 4
                ),
            }
            for signature, count in sorted(signature_counts.items())
        ],
        "feature_axis_metrics": feature_axis_metrics,
        "venue_source_quality_valid_closed_count": len(venue_valid_closed),
        "venue_source_quality_blocked_closed_count": len(closed)
        - len(venue_valid_closed),
        "by_effective_venue": _dimension_metrics("effective_venue", venue_valid_closed),
        "by_market_session_bucket": _dimension_metrics(
            "market_session_bucket", venue_valid_closed
        ),
    }


def _real_scale_in_execution_record(
    row: dict[str, Any], fields: dict[str, Any]
) -> dict[str, Any] | None:
    if str(row.get("stage") or "") != "scale_in_executed":
        return None
    if not _boolish(fields.get("actual_order_submitted")) or _boolish(
        fields.get("broker_order_forbidden")
    ):
        return None
    order_no = str(fields.get("order_no") or fields.get("ord_no") or "").strip()
    fill_price = _safe_float(fields.get("fill_price"), 0.0) or 0.0
    fill_qty = int(_safe_float(fields.get("fill_qty"), 0) or 0)
    if not order_no or fill_price <= 0 or fill_qty <= 0:
        return None
    add_type = str(fields.get("add_type") or "").strip().upper()
    add_reason = str(fields.get("add_reason") or "").strip()
    return {
        "position_key": _record_key(row, fields),
        "record_id": row.get("record_id"),
        "stock_code": str(row.get("stock_code") or ""),
        "stock_name": str(row.get("stock_name") or ""),
        "order_no": order_no,
        "executed_at": row.get("emitted_at"),
        "add_type": add_type or "UNKNOWN",
        "add_reason": add_reason or "-",
        "scale_in_outcome_cohort": (
            "winner_recovery"
            if add_reason == "post_probe_winner_recovery_first_leg"
            else (
                "avg_down"
                if add_type == "AVG_DOWN"
                else "normal_pyramid" if add_type == "PYRAMID" else "unknown"
            )
        ),
        "fill_price": round(fill_price, 4),
        "fill_qty": fill_qty,
        "fill_notional_krw": round(fill_price * fill_qty, 4),
        "entry_effective_venue": str(
            fields.get("effective_venue")
            or fields.get("rising_missed_effective_venue")
            or "UNKNOWN"
        )
        .strip()
        .upper(),
        "market_session_bucket": str(
            fields.get("market_session_bucket")
            or fields.get("rising_missed_market_session_bucket")
            or "UNKNOWN"
        ).strip(),
        "scale_in_broker_actual_execution_venue": str(
            fields.get("broker_actual_execution_venue") or "UNKNOWN"
        )
        .strip()
        .upper(),
        "scale_in_broker_actual_execution_venue_source": str(
            fields.get("broker_actual_execution_venue_source") or "unknown"
        ).strip(),
        "scale_in_receipt_economics_complete": _boolish(
            fields.get("receipt_economics_complete")
        ),
        "scale_in_receipt_quantity_contract_complete": _boolish(
            fields.get("receipt_quantity_contract_complete")
        ),
        "scale_in_receipt_unit_fill_consistent": _boolish(
            fields.get("receipt_unit_fill_consistent")
        ),
        "scale_in_broker_execution_provenance_complete": _boolish(
            fields.get("broker_execution_provenance_complete")
        ),
        "post_add_avg_price": _safe_float(fields.get("new_avg_price"), None),
        "post_add_position_qty": int(_safe_float(fields.get("new_buy_qty"), 0) or 0),
        "recovery_ai_thesis_state": str(
            fields.get("post_probe_winner_recovery_ai_thesis_state") or "unreported"
        ),
        "recovery_ai_parent_action": str(
            fields.get("post_probe_winner_recovery_ai_parent_action")
            or "NOT_EVALUATED"
        ),
        "recovery_ai_parent_prompt_version": str(
            fields.get("post_probe_winner_recovery_ai_parent_prompt_version") or "-"
        ),
        "recovery_ai_parent_trace_id": str(
            fields.get("post_probe_winner_recovery_ai_parent_trace_id") or "-"
        ),
        "recovery_ai_parent_snapshot_id": str(
            fields.get("post_probe_winner_recovery_ai_parent_snapshot_id") or "-"
        ),
        "recovery_holding_ai_action": str(
            fields.get("post_probe_winner_recovery_holding_ai_action")
            or "NOT_EVALUATED"
        ),
        "recovery_holding_ai_data_quality": str(
            fields.get("post_probe_winner_recovery_holding_ai_data_quality")
            or "insufficient"
        ),
        "recovery_holding_ai_input_schema": str(
            fields.get("post_probe_winner_recovery_holding_ai_input_schema") or "-"
        ),
        "recovery_ai_tape_substitution_applied": _boolish(
            fields.get("post_probe_winner_recovery_ai_tape_substitution_applied")
        ),
        "closed": False,
        "actual_order_submitted": True,
        "broker_order_forbidden": False,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "decision_authority": "real_scale_in_execution_outcome_observation_only",
        "forbidden_uses": FORBIDDEN_USES,
    }


def _update_real_scale_in_outcome(item: dict[str, Any], row: dict[str, Any]) -> None:
    emitted_epoch = _event_epoch(row.get("emitted_at"))
    executed_epoch = _event_epoch(item.get("executed_at"))
    if (
        emitted_epoch is None
        or executed_epoch is None
        or emitted_epoch < executed_epoch
        or row.get("pipeline") != "HOLDING_PIPELINE"
    ):
        return
    fields = _fields(row)
    profit_rate = _safe_float(fields.get("profit_rate"), None)
    if profit_rate is not None:
        item["latest_position_profit_pct"] = round(profit_rate, 4)
        item["latest_position_profit_at"] = row.get("emitted_at")
    if str(row.get("stage") or "") != "sell_completed":
        return
    sell_price = _safe_float(fields.get("sell_price"), None)
    item["closed"] = profit_rate is not None
    item["sell_completed_at"] = row.get("emitted_at")
    item["final_position_profit_pct"] = profit_rate
    item["sell_price"] = sell_price
    item["realized_pnl_krw"] = _safe_float(fields.get("realized_pnl_krw"), None)
    item["no_scale_in_counterfactual_profit_pct"] = _safe_float(
        fields.get("no_scale_in_counterfactual_profit_pct"), None
    )
    item["scale_in_incremental_realized_delta_pct"] = _safe_float(
        fields.get("scale_in_incremental_realized_delta_pct"), None
    )
    item["sell_receipt_economics_complete"] = _boolish(
        fields.get("sell_execution_receipt_economics_complete")
    )
    item["sell_receipt_quantity_contract_complete"] = _boolish(
        fields.get("sell_execution_receipt_quantity_contract_complete")
    )
    item["sell_receipt_unit_fill_consistent"] = _boolish(
        fields.get("sell_execution_receipt_unit_fill_consistent")
    )
    item["sell_broker_execution_provenance_complete"] = _boolish(
        fields.get("broker_execution_provenance_complete")
    )
    item["sell_broker_actual_execution_venue"] = (
        str(fields.get("broker_actual_execution_venue") or "UNKNOWN")
        .strip()
        .upper()
    )
    item["sell_broker_actual_execution_venue_source"] = str(
        fields.get("broker_actual_execution_venue_source") or "unknown"
    ).strip()
    fill_price = _safe_float(item.get("fill_price"), 0.0) or 0.0
    if sell_price is not None and fill_price > 0:
        item["scale_in_leg_gross_return_proxy_pct"] = round(
            ((sell_price - fill_price) / fill_price) * 100.0,
            4,
        )


def _finalize_real_scale_in_source_quality(item: dict[str, Any]) -> None:
    """Calculate fee-aware leg EV only from complete broker receipt contracts."""

    blockers: list[str] = []
    if not item.get("closed"):
        blockers.append("position_not_closed")
    if not item.get("scale_in_receipt_economics_complete"):
        blockers.append("scale_in_receipt_economics_incomplete")
    if not item.get("scale_in_receipt_quantity_contract_complete"):
        blockers.append("scale_in_receipt_quantity_incomplete")
    if not item.get("scale_in_receipt_unit_fill_consistent"):
        blockers.append("scale_in_receipt_unit_fill_inconsistent")
    if not item.get("scale_in_broker_execution_provenance_complete"):
        blockers.append("scale_in_broker_provenance_incomplete")
    if not item.get("sell_receipt_economics_complete"):
        blockers.append("sell_receipt_economics_incomplete")
    if not item.get("sell_receipt_quantity_contract_complete"):
        blockers.append("sell_receipt_quantity_incomplete")
    if not item.get("sell_receipt_unit_fill_consistent"):
        blockers.append("sell_receipt_unit_fill_inconsistent")
    if not item.get("sell_broker_execution_provenance_complete"):
        blockers.append("sell_broker_provenance_incomplete")
    if not item.get("winner_recovery_qty_cap_valid", True):
        blockers.append("winner_recovery_qty_cap_invalid")
    if item.get("scale_in_outcome_cohort") == "winner_recovery":
        if str(item.get("entry_effective_venue") or "").upper() not in {
            "KRX",
            "NXT",
            "PREMARKET_KRX_LIKE",
        }:
            blockers.append("winner_recovery_entry_venue_unproven")
        if str(item.get("market_session_bucket") or "").upper() in {
            "",
            "-",
            "UNKNOWN",
        }:
            blockers.append("winner_recovery_session_unproven")

    fill_price = _safe_float(item.get("fill_price"), 0.0) or 0.0
    fill_qty = int(_safe_float(item.get("fill_qty"), 0) or 0)
    sell_price = _safe_float(item.get("sell_price"), 0.0) or 0.0
    fill_notional = _safe_float(item.get("fill_notional_krw"), 0.0) or 0.0
    if fill_price <= 0 or fill_qty <= 0 or fill_notional <= 0:
        blockers.append("scale_in_fill_economics_invalid")
    if sell_price <= 0:
        blockers.append("terminal_sell_price_invalid")

    item["source_quality_valid"] = not blockers
    item["source_quality_blockers"] = blockers
    if blockers:
        item["scale_in_leg_net_pnl_proxy_krw"] = None
        item["scale_in_leg_net_return_proxy_pct"] = None
        return

    leg_net_pnl = calculate_net_realized_pnl(fill_price, sell_price, fill_qty)
    item["scale_in_leg_net_pnl_proxy_krw"] = leg_net_pnl
    item["scale_in_leg_net_return_proxy_pct"] = round(
        (leg_net_pnl / fill_notional) * 100.0,
        4,
    )


def _real_scale_in_performance_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    closed = [item for item in rows if item.get("closed")]
    active = [item for item in rows if not item.get("closed")]

    def dimension_items(cohort: str) -> dict[str, Any]:
        cohort_rows = [
            item for item in rows if item.get("scale_in_outcome_cohort") == cohort
        ]
        cohort_closed = [item for item in cohort_rows if item.get("closed")]
        values = [
            _safe_float(item.get("final_position_profit_pct"), 0.0) or 0.0
            for item in cohort_closed
        ]
        source_quality_valid = [
            item for item in cohort_closed if item.get("source_quality_valid")
        ]
        valid_notional = sum(
            _safe_float(item.get("fill_notional_krw"), 0.0) or 0.0
            for item in source_quality_valid
        )
        valid_net_pnl = sum(
            _safe_float(item.get("scale_in_leg_net_pnl_proxy_krw"), 0.0) or 0.0
            for item in source_quality_valid
        )
        valid_net_returns = [
            _safe_float(item.get("scale_in_leg_net_return_proxy_pct"), 0.0) or 0.0
            for item in source_quality_valid
        ]
        return {
            "execution_count": len(cohort_rows),
            "closed_count": len(cohort_closed),
            "active_unrealized_count": len(cohort_rows) - len(cohort_closed),
            "closed_winner_count": sum(1 for value in values if value > 0),
            "closed_loss_or_flat_count": sum(1 for value in values if value <= 0),
            "equal_weight_avg_final_position_profit_pct": (
                round(sum(values) / len(values), 4) if values else None
            ),
            "source_quality_valid_closed_count": len(source_quality_valid),
            "source_quality_blocked_closed_count": len(cohort_closed)
            - len(source_quality_valid),
            "scale_in_leg_net_pnl_proxy_krw_sum": (
                round(valid_net_pnl, 4) if source_quality_valid else None
            ),
            "equal_weight_avg_scale_in_leg_net_return_pct": (
                round(sum(valid_net_returns) / len(valid_net_returns), 4)
                if valid_net_returns
                else None
            ),
            "source_quality_adjusted_ev_pct": (
                round((valid_net_pnl / valid_notional) * 100.0, 4)
                if valid_notional > 0
                else None
            ),
            "scale_in_leg_diagnostic_win_rate": (
                round(
                    sum(1 for value in valid_net_returns if value > 0)
                    / len(valid_net_returns),
                    4,
                )
                if valid_net_returns
                else None
            ),
            "runtime_apply_authority": False,
        }

    by_cohort = {
        cohort: dimension_items(cohort)
        for cohort in ("winner_recovery", "normal_pyramid", "avg_down", "unknown")
    }
    winner_recovery_rows = [
        item
        for item in rows
        if item.get("scale_in_outcome_cohort") == "winner_recovery"
    ]
    source_quality_valid_closed = [
        item for item in closed if item.get("source_quality_valid")
    ]
    valid_notional = sum(
        _safe_float(item.get("fill_notional_krw"), 0.0) or 0.0
        for item in source_quality_valid_closed
    )
    valid_net_pnl = sum(
        _safe_float(item.get("scale_in_leg_net_pnl_proxy_krw"), 0.0) or 0.0
        for item in source_quality_valid_closed
    )
    valid_net_returns = [
        _safe_float(item.get("scale_in_leg_net_return_proxy_pct"), 0.0) or 0.0
        for item in source_quality_valid_closed
    ]

    def ai_dimension_items(dimension: str) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in winner_recovery_rows:
            value = str(item.get(dimension) or "UNKNOWN").strip() or "UNKNOWN"
            grouped[value].append(item)
        result = []
        for value, bucket_rows in sorted(grouped.items()):
            bucket_closed = [item for item in bucket_rows if item.get("closed")]
            profit_values = [
                float(_safe_float(item.get("final_position_profit_pct"), 0.0) or 0.0)
                for item in bucket_closed
            ]
            source_quality_valid = [
                item
                for item in bucket_closed
                if item.get("source_quality_valid")
            ]
            valid_notional = sum(
                _safe_float(item.get("fill_notional_krw"), 0.0) or 0.0
                for item in source_quality_valid
            )
            valid_net_pnl = sum(
                _safe_float(item.get("scale_in_leg_net_pnl_proxy_krw"), 0.0)
                or 0.0
                for item in source_quality_valid
            )
            result.append(
                {
                    dimension: value,
                    "execution_count": len(bucket_rows),
                    "closed_count": len(bucket_closed),
                    "closed_winner_count": sum(
                        1 for value in profit_values if value > 0
                    ),
                    "equal_weight_avg_final_position_profit_pct": (
                        round(sum(profit_values) / len(profit_values), 4)
                        if profit_values
                        else None
                    ),
                    "source_quality_valid_closed_count": len(source_quality_valid),
                    "source_quality_adjusted_ev_pct": (
                        round((valid_net_pnl / valid_notional) * 100.0, 4)
                        if valid_notional > 0
                        else None
                    ),
                    "runtime_apply_authority": False,
                }
            )
        return result

    return {
        "execution_count": len(rows),
        "closed_count": len(closed),
        "active_unrealized_count": len(active),
        "winner_recovery_execution_count": by_cohort["winner_recovery"][
            "execution_count"
        ],
        "normal_pyramid_execution_count": by_cohort["normal_pyramid"][
            "execution_count"
        ],
        "avg_down_execution_count": by_cohort["avg_down"]["execution_count"],
        "winner_recovery_qty_cap_invalid_count": sum(
            1
            for item in rows
            if item.get("scale_in_outcome_cohort") == "winner_recovery"
            and not item.get("winner_recovery_qty_cap_valid")
        ),
        "winner_expansion_vs_avg_down_asymmetry_observed": bool(
            by_cohort["winner_recovery"]["execution_count"] == 0
            and by_cohort["normal_pyramid"]["execution_count"] == 0
            and by_cohort["avg_down"]["execution_count"] > 0
        ),
        "by_outcome_cohort": by_cohort,
        "winner_recovery_by_ai_thesis_state": ai_dimension_items(
            "recovery_ai_thesis_state"
        ),
        "winner_recovery_by_ai_parent_prompt_version": ai_dimension_items(
            "recovery_ai_parent_prompt_version"
        ),
        "winner_recovery_by_holding_ai_action": ai_dimension_items(
            "recovery_holding_ai_action"
        ),
        "winner_recovery_by_holding_ai_data_quality": ai_dimension_items(
            "recovery_holding_ai_data_quality"
        ),
        "completed_outcome_available": bool(closed),
        "source_quality_valid_closed_count": len(source_quality_valid_closed),
        "source_quality_blocked_closed_count": len(closed)
        - len(source_quality_valid_closed),
        "scale_in_leg_net_pnl_proxy_krw_sum": (
            round(valid_net_pnl, 4) if source_quality_valid_closed else None
        ),
        "equal_weight_avg_scale_in_leg_net_return_pct": (
            round(sum(valid_net_returns) / len(valid_net_returns), 4)
            if valid_net_returns
            else None
        ),
        "source_quality_adjusted_ev_pct": (
            round((valid_net_pnl / valid_notional) * 100.0, 4)
            if valid_notional > 0
            else None
        ),
        "scale_in_leg_diagnostic_win_rate": (
            round(
                sum(1 for value in valid_net_returns if value > 0)
                / len(valid_net_returns),
                4,
            )
            if valid_net_returns
            else None
        ),
        "source_quality_adjusted_ev_available": bool(source_quality_valid_closed),
        "source_quality_adjusted_ev_unavailable_reason": (
            "-"
            if source_quality_valid_closed
            else (
                "all_closed_scale_in_rows_failed_receipt_source_quality"
                if closed
                else "no_closed_scale_in_position"
            )
        ),
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
    one_share_plans: dict[str, dict[str, Any]] = {}
    real_entry_lifecycle_records: dict[str, dict[str, Any]] = {}
    real_scale_in_records: dict[str, dict[str, Any]] = {}

    for row in iter_jsonl(pipeline_path):
        fields = _fields(row)
        key = _record_key(row, fields)
        if not key:
            continue
        real_scale_in = _real_scale_in_execution_record(row, fields)
        if real_scale_in:
            execution_key = f"{key}:{real_scale_in['order_no']}"
            existing_execution = real_scale_in_records.get(execution_key)
            if existing_execution is None:
                real_scale_in_records[execution_key] = real_scale_in
            else:
                prior_notional = (
                    _safe_float(existing_execution.get("fill_notional_krw"), 0.0) or 0.0
                )
                prior_qty = int(_safe_float(existing_execution.get("fill_qty"), 0) or 0)
                added_notional = (
                    _safe_float(real_scale_in.get("fill_notional_krw"), 0.0) or 0.0
                )
                added_qty = int(_safe_float(real_scale_in.get("fill_qty"), 0) or 0)
                combined_qty = prior_qty + added_qty
                combined_notional = prior_notional + added_notional
                existing_execution.update(
                    {
                        "fill_qty": combined_qty,
                        "fill_notional_krw": round(combined_notional, 4),
                        "fill_price": (
                            round(combined_notional / combined_qty, 4)
                            if combined_qty > 0
                            else 0.0
                        ),
                        "post_add_avg_price": real_scale_in.get("post_add_avg_price"),
                        "post_add_position_qty": real_scale_in.get(
                            "post_add_position_qty"
                        ),
                        "scale_in_receipt_economics_complete": bool(
                            existing_execution.get(
                                "scale_in_receipt_economics_complete"
                            )
                            and real_scale_in.get(
                                "scale_in_receipt_economics_complete"
                            )
                        ),
                        "scale_in_receipt_quantity_contract_complete": bool(
                            existing_execution.get(
                                "scale_in_receipt_quantity_contract_complete"
                            )
                            and real_scale_in.get(
                                "scale_in_receipt_quantity_contract_complete"
                            )
                        ),
                        "scale_in_receipt_unit_fill_consistent": bool(
                            existing_execution.get(
                                "scale_in_receipt_unit_fill_consistent"
                            )
                            and real_scale_in.get(
                                "scale_in_receipt_unit_fill_consistent"
                            )
                        ),
                        "scale_in_broker_execution_provenance_complete": bool(
                            existing_execution.get(
                                "scale_in_broker_execution_provenance_complete"
                            )
                            and real_scale_in.get(
                                "scale_in_broker_execution_provenance_complete"
                            )
                        ),
                    }
                )
        if str(row.get("stage") or "") in _REAL_ENTRY_LIFECYCLE_STAGES:
            lifecycle_key = _real_entry_lifecycle_key(row, fields)
            lifecycle_item = real_entry_lifecycle_records.setdefault(
                lifecycle_key, _real_entry_lifecycle_record(row)
            )
            _update_real_entry_lifecycle(lifecycle_item, row)
        if _is_one_share_plan_event(row):
            one_share_plans[key] = _one_share_record(row)
        if key in one_share_plans:
            _update_scout_ai_execution_attribution(one_share_plans[key], row)
        if _is_one_share_event(row):
            one_share = _one_share_record(row)
            planned = one_share_plans.get(key) or {}
            planned_qty = int(planned.get("forced_entry_qty") or 0)
            if planned_qty > 0:
                one_share["forced_entry_qty"] = planned_qty
            for plan_key in (
                "source_signature",
                "position_tag",
                "rising_missed_class",
                "scanner_promotion_reason",
                "_effective_venue_authoritative_seen",
                "_effective_venue_fallback_seen",
                "effective_venue",
                "effective_venue_resolution",
                "venue_source_quality_valid",
                "market_session_bucket",
                "entry_split_order_probe_qty",
                "entry_split_order_leg_count",
                "entry_split_order_qty_weight_min",
                "entry_split_order_policy_version",
                "entry_split_order_variant_id",
            ):
                if planned.get(plan_key) not in (None, ""):
                    one_share[plan_key] = planned[plan_key]
            for plan_key, plan_value in planned.items():
                if plan_key.startswith("scout_") and plan_value not in (None, ""):
                    one_share[plan_key] = plan_value
            one_share["one_share_plan_ts"] = planned.get("first_one_share_ts")
            one_share["one_share_actual_stage"] = row.get("stage")
            item = one_share_records.setdefault(key, one_share)
            item.update({k: v for k, v in one_share.items() if v not in (None, "")})
        if key in one_share_records:
            _update_scout_ai_execution_attribution(one_share_records[key], row)
            _update_venue_provenance(one_share_records[key], row)
            _update_probe_residual_observation(one_share_records[key], row)
            recovery_candidate = _post_probe_hard_abort_recovery_candidate_record(row)
            if recovery_candidate:
                _update_normal_winner_expansion_candidate(
                    one_share_records[key], recovery_candidate, row
                )
        blocked = _pyramid_blocked_record(row)
        if blocked:
            accepted_for_lifecycle = True
            if key in one_share_records:
                accepted_for_lifecycle = _update_normal_winner_expansion_candidate(
                    one_share_records[key], blocked, row
                )
            if accepted_for_lifecycle:
                item = candidates.setdefault(key, blocked)
                item.update({k: v for k, v in blocked.items() if v not in (None, "")})
            if key in one_share_records and accepted_for_lifecycle:
                one_share_records[key].update(
                    {k: v for k, v in blocked.items() if v not in (None, "")}
                )
                _update_snapshot(one_share_records[key], row)
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
                _update_snapshot(candidates[key], row)
                _update_sell(candidates[key], row)
            elif not _event_after_final(candidates[key], row) and (
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
                _update_snapshot(one_share_records[key], row)
                _update_sell(one_share_records[key], row)
            elif not _event_after_final(one_share_records[key], row) and (
                stage
                in {"stat_action_decision_snapshot", "bad_entry_refined_candidate"}
                or "profit_rate" in fields
            ):
                _update_snapshot(one_share_records[key], row)
            if "submit" in stage or "receipt" in stage or "submitted" in stage:
                _update_submit(one_share_records[key], row)

    real_scale_in_by_position: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in real_scale_in_records.values():
        real_scale_in_by_position[str(item.get("position_key") or "")].append(item)
    if real_scale_in_by_position:
        for row in iter_jsonl(pipeline_path):
            fields = _fields(row)
            key = _record_key(row, fields)
            for item in real_scale_in_by_position.get(key, []):
                _update_real_scale_in_outcome(item, row)

    # JSONL writes from independent workers can be physically out of timestamp
    # order. A pyramid event whose own event time is after the terminal sell is
    # not a lifecycle candidate even when it appeared earlier in the file.
    for key, item in list(candidates.items()):
        lifecycle = one_share_records.get(key) or item
        if _event_epoch(item.get("first_observed_ts")) is not None and (
            _event_epoch(lifecycle.get("final_ts")) is not None
            and _event_epoch(item.get("first_observed_ts"))
            > _event_epoch(lifecycle.get("final_ts"))
        ):
            candidates.pop(key, None)

    pyramid_threshold_provenance = _apply_daily_pyramid_threshold_provenance(
        one_share_records,
        candidates,
    )

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
    for key, item in one_share_records.items():
        _finalize_probe_residual_observation(item)
        _finalize_probe_residual_real_outcome(item)
        if item.get("normal_winner_expansion_blocker_reason") in {
            "post_hard_abort_recovery_source_only",
            "post_terminal_abort_recovery_source_only",
        } and not item.get("post_probe_hard_abort_recovery_confirmation_ready"):
            for field_name in tuple(item):
                if field_name.startswith("normal_winner_expansion_"):
                    item.pop(field_name, None)
        _finalize_normal_winner_expansion(item)
        legacy_feedback_label = _feedback_label(item)
        item["pyramid_feedback_label"] = legacy_feedback_label
        item["legacy_pyramid_feedback_label"] = legacy_feedback_label
        item["canonical_expansion_outcome_label"] = _canonical_expansion_outcome_label(
            item
        )
        item["post_probe_legacy_label_conflict"] = bool(
            item["canonical_expansion_outcome_label"]
            == "expansion_missed_upside_confirmation_ready"
            and legacy_feedback_label != "pyramid_would_have_helped"
        )
        item["canonical_expansion_missed_upside_candidate"] = bool(
            item["canonical_expansion_outcome_label"]
            in {
                "expansion_missed_upside_confirmation_ready",
                "expansion_missed_upside_threshold_crossed",
                "expansion_missed_upside_runtime_confirmed_source_quality_disputed",
                "expansion_recovery_missed_upside_confirmation_ready",
            }
        )
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
    real_entry_lifecycle_rows = []
    for item in real_entry_lifecycle_records.values():
        if not item.get("actual_entry_order_submitted"):
            continue
        _finalize_real_entry_lifecycle(
            item, one_share_records.get(str(item.get("record_key") or ""))
        )
        real_entry_lifecycle_rows.append(item)
    real_entry_lifecycle_rows.sort(
        key=lambda item: (
            str(item.get("entry_submitted_at") or item.get("first_observed_ts") or ""),
            str(item.get("record_id") or ""),
        )
    )
    real_scale_in_rows = sorted(
        real_scale_in_records.values(),
        key=lambda item: (
            str(item.get("executed_at") or ""),
            str(item.get("record_id") or ""),
            str(item.get("order_no") or ""),
        ),
    )
    for item in real_scale_in_rows:
        winner_recovery = item.get("scale_in_outcome_cohort") == "winner_recovery"
        item["winner_recovery_qty_cap"] = 1 if winner_recovery else None
        item["winner_recovery_qty_cap_valid"] = bool(
            not winner_recovery or int(_safe_float(item.get("fill_qty"), 0) or 0) <= 1
        )
        _finalize_real_scale_in_source_quality(item)

    label_counts = Counter(
        str(item.get("pyramid_feedback_label") or "unknown") for item in rows
    )
    blocker_metrics = _aggregate_by_blocker(rows)
    one_share_opportunity_summary = _one_share_summary(one_share_rows)
    normal_winner_expansion_summary = _normal_winner_expansion_summary(one_share_rows)
    real_entry_lifecycle_summary = _real_entry_lifecycle_summary(
        real_entry_lifecycle_rows
    )
    real_scale_in_performance_summary = _real_scale_in_performance_summary(
        real_scale_in_rows
    )
    real_scale_in_source_quality_blocked_closed_count = int(
        real_scale_in_performance_summary.get(
            "source_quality_blocked_closed_count", 0
        )
        or 0
    )
    winner_recovery_qty_cap_invalid_count = int(
        real_scale_in_performance_summary.get(
            "winner_recovery_qty_cap_invalid_count", 0
        )
        or 0
    )
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
    residual_fill_attribution_invalid_count = sum(
        1
        for item in one_share_rows
        if item.get("residual_fill_attribution_valid") is False
    )
    temporal_inversion_candidate_count = sum(
        1
        for item in one_share_rows
        if bool(item.get("normal_winner_expansion_temporal_inversion"))
    )
    if pressure_provenance_missing_count:
        source_quality_status = "pressure_provenance_missing"
    if pressure_provenance_unusable_count:
        source_quality_status = "pressure_provenance_unusable"
    if micro_vwap_provenance_missing_count:
        source_quality_status = "micro_vwap_provenance_missing"
    if micro_vwap_provenance_unusable_count:
        source_quality_status = "micro_vwap_provenance_unusable"
    if real_scale_in_source_quality_blocked_closed_count:
        # A closed scale-in row already carries its own source_quality_valid
        # flag and blockers.  Keep that row out of leg EV without poisoning
        # unrelated one-share and normal-winner calibration rows from the same
        # day.
        source_quality_status = "pass_with_row_exclusions"
    if winner_recovery_qty_cap_invalid_count:
        source_quality_status = "winner_recovery_qty_cap_invalid"
    return {
        "schema_version": 4,
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
                "exact_probe_bundle_receipt_and_terminal_fill_join_with_explicit_"
                "effective_venue_and_fresh_minute_candle_provenance_when_present"
            ),
            "forbidden_uses": FORBIDDEN_USES,
        },
        "post_probe_real_outcome_metric_contract": {
            "metric_role": "multi_leg_post_probe_real_outcome_attribution",
            "decision_authority": (
                "source_only_post_probe_real_outcome_no_runtime_mutation"
            ),
            "window_policy": (
                "same_day_probe_fill_to_terminal_sell_with_250ms_two_evaluation_"
                "confirmation_reconstruction"
            ),
            "sample_floor": "rolling_closed_source_quality_valid_zero_fill_rows_ge_20",
            "primary_decision_metric": (
                "probe_residual_confirmation_ready_notional_weighted_ev_pct"
            ),
            "source_quality_gate": (
                "exact_probe_bundle_terminal_fill_real_sell_profit_explicit_venue_"
                "and_version_proven_post_probe_evidence"
            ),
            "forbidden_uses": FORBIDDEN_USES,
        },
        "post_hard_abort_recovery_metric_contract": {
            "metric_role": "bounded_tunable_scale_in_counterfactual",
            "decision_authority": (
                "source_only_post_terminal_abort_recovery_observation_no_runtime_mutation"
            ),
            "window_policy": "same_position_cycle_terminal_abort_to_sell",
            "sample_floor": (
                "rolling_closed_source_quality_valid_recovery_candidates_ge_20"
            ),
            "primary_decision_metric": "notional_weighted_ev_pct",
            "source_quality_gate": (
                "fresh_quote_tick_micro_and_two_independent_market_tape_or_"
                "trusted_ai_groups_same_probe_terminal_cycle"
            ),
            "forbidden_uses": FORBIDDEN_USES,
        },
        "normal_winner_expansion_metric_contract": {
            "metric_role": "bounded_tunable_scale_in_counterfactual",
            "decision_authority": (
                "source_only_normal_winner_expansion_attribution_no_runtime_mutation"
            ),
            "window_policy": (
                "same_day_probe_fill_or_terminal_hard_abort_to_first_source_quality_"
                "valid_positive_scale_in_evaluation_to_sell"
            ),
            "sample_floor": "rolling_closed_source_quality_valid_candidates_ge_20",
            "primary_decision_metric": "notional_weighted_ev_pct",
            "source_quality_gate": (
                "one_share_record_join_positive_pyramid_evaluation_with_optional_"
                "pressure_and_micro_vwap_feature_provenance_then_post_candidate_"
                "holding_and_sell; candidate_at_must_not_be_after_final_ts; "
                "trusted_ai_tape_substitution_requires_supportive_thesis; "
                "explicit_conflict_free_venue_required_for_venue_split"
            ),
            "forbidden_uses": FORBIDDEN_USES,
        },
        "whole_day_real_entry_lifecycle_metric_contract": {
            "metric_role": "same_day_real_entry_lifecycle_reconciliation",
            "decision_authority": (
                "source_only_same_day_real_entry_lifecycle_reconciliation"
            ),
            "window_policy": (
                "target_date_premarket_krx_nxt_submit_fill_cancel_sell_events"
            ),
            "sample_floor": "1_actual_order_submitted_entry_cycle",
            "primary_decision_metric": (
                "realized_pnl_krw_known_sum_with_equal_weight_avg_profit_pct"
            ),
            "source_quality_gate": (
                "record_joined_actual_order_submit_fill_cancel_sell_with_explicit_"
                "effective_venue_and_non_null_sell_profit_for_closed_cycles; "
                "realized_pnl_requires_event_value_or_same_cycle_full_quantity_"
                "broker_fill_price_reconstruction_with_fee_aware_provenance"
            ),
            "forbidden_uses": FORBIDDEN_USES,
        },
        "real_scale_in_performance_metric_contract": {
            "metric_role": "real_scale_in_execution_outcome_attribution",
            "decision_authority": "real_scale_in_execution_outcome_observation_only",
            "window_policy": "scale_in_execution_to_same_position_terminal_sell",
            "sample_floor": "rolling_closed_real_scale_in_positions_ge_20",
            "primary_decision_metric": "source_quality_adjusted_ev_pct",
            "source_quality_gate": (
                "record_and_order_joined_real_scale_in_fill_then_terminal_sell; "
                "complete quantity/economics/broker provenance on both receipts; "
                "winner recovery additionally requires explicit entry venue and "
                "session cohort provenance; "
                "active positions remain unrealized and leg net return is a fee-aware "
                "pro-rata attribution proxy"
            ),
            "forbidden_uses": FORBIDDEN_USES,
        },
        "source_paths": {"pipeline_events": str(resolved_pipeline_path)},
        "pyramid_threshold_provenance": pyramid_threshold_provenance,
        "source_quality": {
            "status": source_quality_status,
            "pipeline_events_exists": resolved_pipeline_path.exists(),
            "pyramid_threshold_provenance_status": (
                "ambiguous"
                if pyramid_threshold_provenance.get("ambiguous")
                else (
                    "pass"
                    if pyramid_threshold_provenance.get(
                        "observed_min_profit_pct_values"
                    )
                    else "static_fallback_no_runtime_observation"
                )
            ),
            "pressure_provenance_missing_count": pressure_provenance_missing_count,
            "pressure_provenance_unusable_count": pressure_provenance_unusable_count,
            "micro_vwap_provenance_missing_count": micro_vwap_provenance_missing_count,
            "micro_vwap_provenance_unusable_count": micro_vwap_provenance_unusable_count,
            "residual_fill_attribution_invalid_count": (
                residual_fill_attribution_invalid_count
            ),
            "temporal_inversion_candidate_count": temporal_inversion_candidate_count,
            "winner_recovery_qty_cap_invalid_count": (
                winner_recovery_qty_cap_invalid_count
            ),
            "real_scale_in_source_quality_blocked_closed_count": (
                real_scale_in_source_quality_blocked_closed_count
            ),
            "source_quality_excluded_row_count": (
                real_scale_in_source_quality_blocked_closed_count
            ),
            "source_quality_exclusion_reasons": (
                {
                    "real_scale_in_receipt_source_quality_incomplete": (
                        real_scale_in_source_quality_blocked_closed_count
                    )
                }
                if real_scale_in_source_quality_blocked_closed_count
                else {}
            ),
        },
        "summary": {
            "pyramid_feedback_row_count": len(rows),
            "pressure_provenance_missing_count": pressure_provenance_missing_count,
            "pressure_provenance_unusable_count": pressure_provenance_unusable_count,
            "micro_vwap_provenance_missing_count": micro_vwap_provenance_missing_count,
            "micro_vwap_provenance_unusable_count": micro_vwap_provenance_unusable_count,
            "residual_fill_attribution_invalid_count": (
                residual_fill_attribution_invalid_count
            ),
            "temporal_inversion_candidate_count": temporal_inversion_candidate_count,
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
            "normal_winner_expansion": normal_winner_expansion_summary,
            "whole_day_real_entry_lifecycle": real_entry_lifecycle_summary,
            "real_scale_in_performance": real_scale_in_performance_summary,
        },
        "blocker_metrics": blocker_metrics,
        "pyramid_feedback_rows": rows[:300],
        "one_share_pyramid_opportunity_rows": one_share_rows,
        "whole_day_real_entry_lifecycle_rows": real_entry_lifecycle_rows,
        "real_scale_in_performance_rows": real_scale_in_rows,
        "normal_winner_expansion_rows": [
            {
                key: item.get(key)
                for key in (
                    "record_id",
                    "stock_code",
                    "stock_name",
                    "effective_venue",
                    "effective_venue_resolution",
                    "venue_source_quality_valid",
                    "market_session_bucket",
                    "normal_winner_expansion_candidate_at",
                    "normal_winner_expansion_entry_profit_pct",
                    "normal_winner_expansion_blocker_reason",
                    "normal_winner_expansion_current_ai_score",
                    "normal_winner_expansion_buy_pressure_10t",
                    "normal_winner_expansion_tick_acceleration_ratio",
                    "normal_winner_expansion_curr_vs_micro_vwap_bp",
                    "normal_winner_expansion_source_quality_valid",
                    "normal_winner_expansion_source_quality_reasons",
                    "normal_winner_expansion_temporal_inversion",
                    "normal_winner_expansion_temporal_inversion_candidate_at",
                    "normal_winner_expansion_assumed_trade_cost_pct",
                    "normal_winner_expansion_candidate_notional_krw",
                    "normal_winner_expansion_gross_incremental_mfe_pct",
                    "normal_winner_expansion_gross_incremental_final_profit_pct",
                    "normal_winner_expansion_incremental_mfe_pct",
                    "normal_winner_expansion_incremental_mae_pct",
                    "normal_winner_expansion_incremental_final_profit_pct",
                    "normal_winner_expansion_label",
                    "normal_winner_expansion_probe_confirmation_signature",
                    "post_probe_hard_abort_recovery_evaluation_seen",
                    "post_probe_hard_abort_recovery_confirmation_max_count",
                    "post_probe_hard_abort_recovery_confirmation_ready",
                    "post_probe_hard_abort_recovery_confirmation_ready_at",
                    "post_probe_hard_abort_recovery_confirmation_preserved_gap_count",
                    "post_probe_hard_abort_recovery_ai_thesis_state_counts",
                    "post_probe_hard_abort_recovery_ai_tape_substitution_count",
                    "normal_winner_expansion_recovery_ai_thesis_state",
                    "normal_winner_expansion_recovery_ai_tape_substitution_applied",
                    "normal_winner_expansion_recovery_ai_parent_prompt_version",
                    "normal_winner_expansion_recovery_holding_ai_action",
                    "normal_winner_expansion_recovery_holding_ai_data_quality",
                    "probe_direction_evaluation_count",
                    "probe_direction_strong_evaluation_count",
                    "probe_direction_max_consecutive_strong_count",
                    "probe_confirmation_max_count",
                    "probe_direction_negative_seen",
                    "final_profit_rate",
                    "actual_order_submitted",
                    "broker_order_forbidden",
                    "runtime_effect",
                    "allowed_runtime_apply",
                    "decision_authority",
                    "forbidden_uses",
                )
            }
            for item in one_share_rows
            if item.get("normal_winner_expansion_candidate_seen")
        ],
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
        f"- probe_residual_zero_fill_count: {summary.get('probe_residual_zero_fill_count')}",
        f"- probe_residual_soft_abort_count: {summary.get('probe_residual_soft_abort_count')}",
        f"- probe_residual_missed_upside_candidate_count: {summary.get('probe_residual_missed_upside_candidate_count')}",
        f"- probe_residual_pyramid_threshold_missed_upside_candidate_count: {summary.get('probe_residual_pyramid_threshold_missed_upside_candidate_count')}",
        f"- probe_residual_real_outcome_closed_count: {summary.get('probe_residual_real_outcome_closed_count')}",
        f"- probe_residual_realized_winner_zero_fill_count: {summary.get('probe_residual_realized_winner_zero_fill_count')}",
        f"- probe_residual_realized_loss_or_flat_zero_fill_count: {summary.get('probe_residual_realized_loss_or_flat_zero_fill_count')}",
        f"- probe_residual_realized_winner_confirmation_ready_count: {summary.get('probe_residual_realized_winner_confirmation_ready_count')}",
        f"- probe_residual_realized_loss_or_flat_confirmation_ready_count: {summary.get('probe_residual_realized_loss_or_flat_confirmation_ready_count')}",
        f"- post_hard_abort_recovery_evaluation_seen_count: {summary.get('post_hard_abort_recovery_evaluation_seen_count')}",
        f"- post_hard_abort_recovery_confirmation_ready_count: {summary.get('post_hard_abort_recovery_confirmation_ready_count')}",
        f"- post_terminal_abort_recovery_confirmation_preserved_gap_count: {summary.get('post_terminal_abort_recovery_confirmation_preserved_gap_count')}",
        f"- post_terminal_abort_recovery_ai_supportive_evaluation_count: {summary.get('post_terminal_abort_recovery_ai_supportive_evaluation_count')}",
        f"- post_terminal_abort_recovery_ai_tape_substitution_count: {summary.get('post_terminal_abort_recovery_ai_tape_substitution_count')}",
        f"- post_hard_abort_recovery_evaluation_not_run_profitable_count: {summary.get('post_hard_abort_recovery_evaluation_not_run_profitable_count')}",
        f"- canonical_expansion_missed_upside_count: {summary.get('canonical_expansion_missed_upside_count')}",
        f"- canonical_expansion_source_quality_valid_missed_upside_count: {summary.get('canonical_expansion_source_quality_valid_missed_upside_count')}",
        f"- post_probe_runtime_confirmation_source_quality_disputed_count: {summary.get('post_probe_runtime_confirmation_source_quality_disputed_count')}",
        f"- post_probe_legacy_label_conflict_count: {summary.get('post_probe_legacy_label_conflict_count')}",
        f"- post_probe_confirmation_false_positive_loss_or_flat_count: {summary.get('post_probe_confirmation_false_positive_loss_or_flat_count')}",
        f"- probe_residual_confirmation_ready_equal_weight_avg_profit_pct: {_safe_float(summary.get('probe_residual_confirmation_ready_equal_weight_avg_profit_pct'), 0.0):.4f}",
        f"- probe_residual_confirmation_ready_notional_weighted_ev_pct: {_safe_float(summary.get('probe_residual_confirmation_ready_notional_weighted_ev_pct'), 0.0):.4f}",
        f"- probe_residual_confirmation_ready_simple_sum_profit_proxy_krw: {_safe_float(summary.get('probe_residual_confirmation_ready_simple_sum_profit_proxy_krw'), 0.0):.2f}",
        f"- probe_residual_pyramid_evaluation_seen_count: {summary.get('probe_residual_pyramid_evaluation_seen_count')}",
        f"- normal_winner_expansion: {json.dumps(summary.get('normal_winner_expansion') or {}, ensure_ascii=False, sort_keys=True)}",
        f"- whole_day_real_entry_lifecycle: {json.dumps(summary.get('whole_day_real_entry_lifecycle') or {}, ensure_ascii=False, sort_keys=True)}",
        f"- real_scale_in_performance: {json.dumps(summary.get('real_scale_in_performance') or {}, ensure_ascii=False, sort_keys=True)}",
        f"- pyramid_min_profit_pct: {(report.get('pyramid_threshold_provenance') or {}).get('selected_min_profit_pct')}",
        f"- pyramid_threshold_source: {(report.get('pyramid_threshold_provenance') or {}).get('selection_source')}",
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
    lines.extend(["", "## Real Scale-In Performance Rows", ""])
    for item in report.get("real_scale_in_performance_rows") or []:
        lines.append(
            "- record_id={record_id} code={stock_code} name={stock_name} "
            "cohort={scale_in_outcome_cohort} type={add_type} reason={add_reason} "
            "fill={fill_price}x{fill_qty} closed={closed} latest={latest_position_profit_pct} "
            "final={final_position_profit_pct} leg_gross_proxy={scale_in_leg_gross_return_proxy_pct} "
            "leg_net_proxy={scale_in_leg_net_return_proxy_pct} source_quality={source_quality_valid}".format(
                **{
                    **item,
                    "closed": bool(item.get("closed")),
                    "latest_position_profit_pct": item.get(
                        "latest_position_profit_pct"
                    ),
                    "final_position_profit_pct": item.get("final_position_profit_pct"),
                    "scale_in_leg_gross_return_proxy_pct": item.get(
                        "scale_in_leg_gross_return_proxy_pct"
                    ),
                    "scale_in_leg_net_return_proxy_pct": item.get(
                        "scale_in_leg_net_return_proxy_pct"
                    ),
                    "source_quality_valid": bool(
                        item.get("source_quality_valid")
                    ),
                }
            )
        )
    lines.extend(["", "## One Share Opportunity Rows", ""])
    for item in report.get("one_share_pyramid_opportunity_rows") or []:
        lines.append(
            "- record_id={record_id} code={stock_code} name={stock_name} label={pyramid_feedback_label} "
            "canonical={canonical_expansion_outcome_label} "
            "opportunity_seen={pyramid_opportunity_seen} opportunity_profit={pyramid_opportunity_profit_rate} "
            "max_profit={max_profit_seen} opportunity_cost={pyramid_opportunity_cost_pct} "
            "final={final_profit_rate} residual_zero_fill={residual_zero_fill} "
            "residual_soft_abort={residual_soft_abort} residual_missed_candidate={residual_missed_upside_candidate} "
            "post_probe_real_outcome={post_probe_real_outcome_label} "
            "confirmation_ready={post_probe_real_confirmation_ready} "
            "runtime_confirmation_ready={post_probe_runtime_confirmation_ready} "
            "confirmation_alignment={post_probe_confirmation_contract_alignment} "
            "recovery_evaluation_seen={post_probe_hard_abort_recovery_evaluation_seen} "
            "recovery_confirmation_ready={post_probe_hard_abort_recovery_confirmation_ready} "
            "confirmation_source_quality_blockers={post_probe_real_confirmation_source_quality_blockers} "
            "first_leg_qty={post_probe_counterfactual_first_leg_qty} "
            "first_leg_profit_proxy_krw={post_probe_counterfactual_first_leg_profit_proxy_krw}".format(
                **{
                    **item,
                    "canonical_expansion_outcome_label": item.get(
                        "canonical_expansion_outcome_label"
                    ),
                    "pyramid_opportunity_seen": bool(
                        item.get("pyramid_opportunity_seen")
                    ),
                    "pyramid_opportunity_profit_rate": item.get(
                        "pyramid_opportunity_profit_rate"
                    ),
                    "max_profit_seen": item.get("max_profit_seen"),
                    "final_profit_rate": item.get("final_profit_rate"),
                    "residual_zero_fill": bool(item.get("residual_zero_fill")),
                    "residual_soft_abort": bool(item.get("residual_soft_abort")),
                    "residual_missed_upside_candidate": bool(
                        item.get("residual_missed_upside_candidate")
                    ),
                    "post_probe_real_outcome_label": item.get(
                        "post_probe_real_outcome_label"
                    ),
                    "post_probe_real_confirmation_ready": bool(
                        item.get("post_probe_real_confirmation_ready")
                    ),
                    "post_probe_runtime_confirmation_ready": bool(
                        item.get("post_probe_runtime_confirmation_ready")
                    ),
                    "post_probe_confirmation_contract_alignment": item.get(
                        "post_probe_confirmation_contract_alignment"
                    ),
                    "post_probe_hard_abort_recovery_evaluation_seen": bool(
                        item.get("post_probe_hard_abort_recovery_evaluation_seen")
                    ),
                    "post_probe_hard_abort_recovery_confirmation_ready": bool(
                        item.get("post_probe_hard_abort_recovery_confirmation_ready")
                    ),
                    "post_probe_real_confirmation_source_quality_blockers": (
                        ",".join(
                            item.get(
                                "post_probe_real_confirmation_source_quality_blockers"
                            )
                            or []
                        )
                        or "-"
                    ),
                    "post_probe_counterfactual_first_leg_qty": item.get(
                        "post_probe_counterfactual_first_leg_qty"
                    ),
                    "post_probe_counterfactual_first_leg_profit_proxy_krw": item.get(
                        "post_probe_counterfactual_first_leg_profit_proxy_krw"
                    ),
                }
            )
        )
    lines.extend(["", "## Whole-Day Real Entry Lifecycle Rows", ""])
    for item in report.get("whole_day_real_entry_lifecycle_rows") or []:
        lines.append(
            "- record_id={record_id} code={stock_code} name={stock_name} "
            "venue={effective_venue} session={market_session_bucket} "
            "state={lifecycle_state} planned_qty={planned_qty} "
            "submitted_qty={broker_submitted_qty} filled_qty={filled_qty} "
            "final={final_profit_rate} realized_pnl_krw={realized_pnl_krw} "
            "realized_pnl_source={realized_pnl_krw_source} "
            "canonical={canonical_expansion_outcome_label}".format(
                **{
                    **item,
                    "market_session_bucket": item.get("market_session_bucket"),
                    "final_profit_rate": item.get("final_profit_rate"),
                    "realized_pnl_krw": item.get("realized_pnl_krw"),
                    "realized_pnl_krw_source": item.get("realized_pnl_krw_source"),
                    "canonical_expansion_outcome_label": item.get(
                        "canonical_expansion_outcome_label"
                    ),
                }
            )
        )
    lines.extend(["", "## Normal Winner Expansion Rows", ""])
    for item in report.get("normal_winner_expansion_rows") or []:
        lines.append(
            "- record_id={record_id} code={stock_code} name={stock_name} "
            "label={normal_winner_expansion_label} entry_profit={normal_winner_expansion_entry_profit_pct} "
            "incremental_mfe={normal_winner_expansion_incremental_mfe_pct} "
            "incremental_final={normal_winner_expansion_incremental_final_profit_pct} "
            "confirmation={normal_winner_expansion_probe_confirmation_signature}".format(
                **item
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

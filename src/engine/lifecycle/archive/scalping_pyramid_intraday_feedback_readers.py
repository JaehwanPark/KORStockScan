"""Historical read-only helpers; no active policy publisher or CLI.

Only existing forensic consumers retain these calculations. Live callers use
their native role owners and permanent retirement fences.
"""

from __future__ import annotations


from collections import Counter, defaultdict


from datetime import datetime, timedelta, timezone


from typing import Any


from src.engine.scalping.rising_missed_candidate import (
    SCOUT_AI_ATTRIBUTION_SCHEMA,
)


from src.engine.trade_profit import (
    calculate_net_profit_rate,
    calculate_net_realized_pnl,
    get_trade_cost_rate,
)

KST = timezone(timedelta(hours=9))


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


def _fields(row: dict[str, Any]) -> dict[str, Any]:
    fields = row.get("fields")
    return fields if isinstance(fields, dict) else {}


def _venue_token(value: Any) -> str:
    token = str(value or "").strip().upper()
    return (
        token
        if token in {"KRX", "NXT", "KRX_NXT_INTEGRATED", "PREMARKET_KRX_LIKE"}
        else ""
    )


def _update_venue_provenance(item: dict[str, Any], row: dict[str, Any]) -> None:
    fields = _fields(row)
    decision_scope = _venue_token(fields.get("decision_market_scope"))
    authoritative = (
        {decision_scope}
        if decision_scope
        else {
            token
            for token in (
                _venue_token(fields.get("rising_missed_effective_venue")),
                _venue_token(fields.get("effective_venue")),
            )
            if token
        }
    )
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
        or fields.get("market_session_regime")
        or ""
    ).strip()
    if session_bucket and not item.get("market_session_bucket"):
        item["market_session_bucket"] = session_bucket
    session_regime = str(fields.get("market_session_regime") or session_bucket).strip()
    if session_regime and not item.get("market_session_regime"):
        item["market_session_regime"] = session_regime
    item["decision_market_scope"] = item.get("effective_venue", "UNKNOWN")
    route = str(fields.get("market_data_route") or "").strip().lower()
    if route not in {"krx_only", "nxt_only", "krx_nxt_integrated"}:
        route = {
            "KRX": "krx_only",
            "NXT": "nxt_only",
            "KRX_NXT_INTEGRATED": "krx_nxt_integrated",
            "PREMARKET_KRX_LIKE": "krx_only",
        }.get(str(item.get("decision_market_scope") or ""), "unknown")
    if not item.get("market_data_route") or item.get("market_data_route") == "unknown":
        item["market_data_route"] = route
    actual = str(fields.get("actual_execution_venue") or "UNKNOWN").strip().upper()
    if actual not in {"KRX", "NXT"}:
        actual = "UNKNOWN"
    actual_seen = set(item.get("_actual_execution_venues_seen") or [])
    if actual != "UNKNOWN":
        actual_seen.add(actual)
    item["_actual_execution_venues_seen"] = sorted(actual_seen)
    item["actual_execution_venue"] = (
        next(iter(actual_seen)) if len(actual_seen) == 1 else "UNKNOWN"
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


def _update_sell(item: dict[str, Any], row: dict[str, Any]) -> None:
    fields = _fields(row)
    _update_scout_ai_execution_attribution(item, row)
    final_profit = _safe_float(fields.get("profit_rate"))
    if final_profit is None:
        return
    incoming_epoch = _event_epoch(row.get("emitted_at"))
    current_epoch = _event_epoch(item.get("final_ts"))
    if current_epoch is not None and (
        incoming_epoch is None or incoming_epoch < current_epoch
    ):
        return
    item["final_ts"] = row.get("emitted_at")
    item["final_stage"] = row.get("stage")
    item["final_profit_rate"] = final_profit
    item["sell_price"] = _safe_float(
        fields.get("sell_price") or fields.get("last_sell_fill_price"), None
    )
    item["sell_reason_type"] = fields.get("sell_reason_type")
    item["exit_rule_candidate"] = fields.get("exit_rule_candidate") or fields.get(
        "exit_rule"
    )


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
            if item.get("scout_ai_attribution_status") == "parent_provenance_incomplete"
        ),
        "scout_ai_attribution_pre_ai_pending_count": sum(
            1
            for item in rows
            if item.get("scout_ai_attribution_status") == "parent_ai_not_evaluated_yet"
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
                item.get("post_probe_hard_abort_recovery_ai_tape_substitution_count")
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

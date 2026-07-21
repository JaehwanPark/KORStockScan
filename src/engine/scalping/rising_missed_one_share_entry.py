"""Pure decision helper for rising-missed one-share SCALPING entries."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

FORCED_ENTRY_REASON = "rising_missed_one_share_entry"
BLOCK_FEATURE_DISABLED = "feature_disabled"
BLOCK_NOT_CANDIDATE = "not_rising_missed_candidate"
BLOCK_CLASS_NOT_ELIGIBLE = "rising_missed_class_not_one_share_eligible"
BLOCK_OPEN_PENDING = "open_pending_entry_order"
BLOCK_ALREADY_HOLDING = "already_holding"
BLOCK_PRICE_ABOVE_CAP = "price_above_one_share_entry_cap"
BLOCK_UPPER_LIMIT_PROXIMITY = "upper_limit_proximity_entry_block"
BLOCK_ENTRY_AI_NOT_EVALUATED = "entry_ai_action_not_evaluated"
BLOCK_ENTRY_AI_ACTION_NOT_BUY = "entry_ai_action_not_buy"
NORMAL_BUY_BRIDGE_REASON = "rising_missed_normal_buy_bridge_ok"
MAX_ONE_SHARE_ENTRY_PRICE_KRW = 1_000_000
# Legacy compatibility only.  Rising-missed no longer owns a budget cap;
# position_sizing_allocator resolves the real quantity at submit time.
DEFAULT_RISING_MISSED_SCOUT_ENTRY_BUDGET_CAP_KRW = 0
DEFAULT_RISING_MISSED_UPPER_LIMIT_EXCLUDE_PCT = 22.0
DEFAULT_UPPER_LIMIT_PROXIMITY_BLOCK_PCT = 27.0
RISING_MISSED_OPPORTUNITY_COST_POLICY = "balanced"
RISING_MISSED_FILTER_LAYER_CANDIDATE_GATE = "candidate_gate"
RISING_MISSED_FILTER_OWNER_CANDIDATE_GATE = "rising_missed_candidate_gate"
RISING_MISSED_FILTER_ACTION_CANDIDATE_ALLOW = "candidate_allow"
RISING_MISSED_FILTER_ACTION_CANDIDATE_BLOCK = "candidate_block"
RISING_MISSED_CLASS_NOT_RISING = "not_rising_missed"
RISING_MISSED_CLASS_SUBMITTED_RESOLVED = "submitted_resolved"
RISING_MISSED_CLASS_RAW = "rising_missed_raw"
RISING_MISSED_CLASS_SOURCE_QUALITY_EXCLUDED = "source_quality_excluded"
RISING_MISSED_CLASS_INTENDED_GUARD_PRESERVED = "intended_guard_preserved"
RISING_MISSED_CLASS_RUNTIME_BACKPRESSURE = "runtime_backpressure_observation"
RISING_MISSED_CLASS_STRATEGY_REJECT = "strategy_reject_missed"
RISING_MISSED_CLASS_ACTIONABLE_MAJOR = "actionable_major_missed"
RISING_MISSED_ONE_SHARE_ELIGIBLE_CLASSES = {
    RISING_MISSED_CLASS_RAW,
    RISING_MISSED_CLASS_ACTIONABLE_MAJOR,
}
TP1_SELECTOR_PASS = "rising_missed_tp1_candidate_pass"
TP1_SELECTOR_BYPASS = "rising_missed_tp1_selector_inactive"
TP1_SELECTOR_DEFER_INPUT = "rising_missed_tp1_decision_input_defer"
TP1_SELECTOR_BLOCK_LANE = "rising_missed_tp1_lane_not_eligible"
TP1_SELECTOR_BLOCK_AI = "rising_missed_tp1_ai_state_blocked"
TP1_SELECTOR_BLOCK_HARD_NEGATIVE = "rising_missed_tp1_hard_negative_evidence"
TP1_SELECTOR_BLOCK_SUPPORT = "rising_missed_tp1_insufficient_positive_support"
TP1_SELECTOR_GROSS_TARGET_PCT = 1.30
TP1_SELECTOR_ADVERSE_STOP_PCT = -0.70
TP1_SELECTOR_COST_RESERVE_PCT = 0.30
TP1_SELECTOR_NET_TARGET_PCT = 1.00
TP1_SELECTOR_HORIZON_SEC = 20 * 60
TP1_SELECTOR_MIN_POSITIVE_SUPPORT_FAMILIES = 2
TP1_SELECTOR_SPREAD_CAUTION_RATIO = 0.002
TP1_SELECTOR_CHASE_DELTA_PCT = 3.0


@dataclass(frozen=True)
class RisingMissedOneShareDecision:
    allowed: bool
    reason: str
    forced_qty: int = 0
    positive_delta_pct: float = 0.0
    log_fields: dict[str, Any] | None = None


@dataclass(frozen=True)
class RisingMissedNormalBuyBridgeDecision:
    allowed: bool
    reason: str
    log_fields: dict[str, Any] | None = None


@dataclass(frozen=True)
class RisingMissedClassification:
    rising_missed: bool
    rising_missed_class: str
    one_share_eligible: bool
    reason: str


@dataclass(frozen=True)
class RisingMissedTP1CandidateDecision:
    allowed: bool
    deferred: bool
    reason: str
    lane: str = "none"
    log_fields: dict[str, Any] | None = None


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except Exception:
        return int(default)


def _normalized_text(value: Any) -> str:
    return str(value or "").strip().upper()


def _field_present(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    return bool(text) and text not in {
        "0",
        "false",
        "no",
        "n",
        "off",
        "none",
        "null",
        "-",
    }


def _signature_tokens(
    stock: dict[str, Any],
    *,
    include_promotion_reason: bool = True,
) -> set[str]:
    tokens: set[str] = set()
    keys = [
        "source_signature",
        "scanner_source_signature",
        "scanner_sources",
    ]
    if include_promotion_reason:
        keys.extend(("scanner_promotion_reason", "promotion_reason"))
    for key in keys:
        raw = str(stock.get(key) or "").upper()
        tokens.update(token for token in re.split(r"[^A-Z0-9_]+", raw) if token)
    return tokens


def _source_family_count(stock: dict[str, Any]) -> int:
    explicit = _safe_int(
        stock.get("source_family_count")
        or stock.get("scanner_source_family_count")
        or stock.get("source_count"),
        0,
    )
    if explicit > 0:
        return explicit
    return len(_signature_tokens(stock, include_promotion_reason=False))


def _has_signature(stock: dict[str, Any], marker: str) -> bool:
    return marker.upper() in _signature_tokens(stock)


def evaluate_rising_missed_tp1_candidate(
    stock: dict[str, Any] | None,
    decision_input: dict[str, Any] | None,
    *,
    selector_enabled: bool,
    active_date: str,
    current_date: str,
    current_ai_action: Any = None,
    nxt_price_jump_recovery_enabled: bool = False,
    nxt_price_jump_recovery_active_date: str = "",
) -> RisingMissedTP1CandidateDecision:
    """Return candidate eligibility only; broker submit safety remains downstream."""
    stock = stock if isinstance(stock, dict) else {}
    decision_input = decision_input if isinstance(decision_input, dict) else {}
    active = bool(selector_enabled and active_date and active_date == current_date)
    source_count = _source_family_count(stock)
    low_rebound_pct = _safe_float(
        stock.get("low_rebound_pct") or stock.get("LowReboundPct"), 0.0
    )
    watch_delta_raw = decision_input.get("rising_missed_tp1_actual_watch_delta_pct")
    watch_delta_available = watch_delta_raw not in (None, "", "-")
    watch_delta_pct = _safe_float(watch_delta_raw, 0.0)
    low_rebound_lane = bool(
        (
            _has_signature(stock, "LOW_REBOUND_RISING_MISSED")
            or _has_signature(stock, "LOW_REBOUND")
        )
        and low_rebound_pct >= 1.0
        and source_count >= 3
    )
    acceleration_lane = bool(
        watch_delta_available and watch_delta_pct >= 1.0 and source_count >= 2
    )
    lane = (
        "low_rebound"
        if low_rebound_lane
        else "acceleration" if acceleration_lane else "none"
    )
    ai_action = (
        str(
            current_ai_action
            if current_ai_action not in (None, "")
            else _entry_ai_action_for_rising_missed(stock)[0]
        )
        .strip()
        .upper()
    )
    bid_imbalance_surge = _has_signature(stock, "BID_IMBALANCE_SURGE")
    input_ready = bool(decision_input.get("rising_missed_tp1_input_ready"))
    effective_quote_age_ms = _safe_float(
        decision_input.get("rising_missed_tp1_effective_quote_age_ms"),
        999999.0,
    )
    spread_ratio = _safe_float(
        decision_input.get("rising_missed_tp1_spread_ratio"), 1.0
    )
    micro_confidence = _safe_float(
        decision_input.get("rising_missed_tp1_micro_confidence"),
        0.0,
    )
    true_ofi_ewma = _safe_float(
        decision_input.get("rising_missed_tp1_true_ofi_ewma"),
        0.0,
    )
    pressure_ewma = _safe_float(
        decision_input.get("rising_missed_tp1_pressure_ewma"),
        0.0,
    )
    depth_imbalance_ewma = _safe_float(
        decision_input.get("rising_missed_tp1_depth_imbalance_ewma"),
        -1.0,
    )
    top_depth_ratio = _safe_float(
        decision_input.get("rising_missed_tp1_top_depth_ratio"),
        0.0,
    )
    signed_tape_state = (
        str(decision_input.get("market_data_signed_tape_state") or "").strip().lower()
    )
    tick_acceleration_support = bool(
        _field_present(decision_input.get("rising_missed_tp1_tick_acceleration_fresh"))
        and _safe_float(
            decision_input.get("rising_missed_tp1_tick_acceleration"),
            0.0,
        )
        >= 1.0
    )
    micro_vwap_support = bool(
        _field_present(decision_input.get("rising_missed_tp1_micro_vwap_fresh"))
        and _safe_float(
            decision_input.get("rising_missed_tp1_micro_vwap_gap_bps"),
            -999999.0,
        )
        >= 0.0
    )
    micro_trusted = micro_confidence >= 0.25
    support_families = {
        "bid_imbalance": bid_imbalance_surge,
        "order_flow": bool(
            micro_trusted and (true_ofi_ewma > 0.0 or pressure_ewma >= 49.0)
        ),
        "depth": bool(
            micro_trusted and depth_imbalance_ewma >= -0.05 and top_depth_ratio >= 0.95
        ),
        "momentum": bool(tick_acceleration_support or micro_vwap_support),
    }
    positive_supports = sorted(
        name for name, supported in support_families.items() if supported
    )
    nxt_price_jump_recovery_lane = bool(
        nxt_price_jump_recovery_enabled
        and lane == "none"
        and str(decision_input.get("rising_missed_effective_venue") or "").upper()
        == "NXT"
        and str(decision_input.get("rising_missed_market_session_bucket") or "").lower()
        == "nxt_entry_window"
        and _field_present(decision_input.get("rising_missed_nxt_eligible"))
        and _has_signature(stock, "LOW_REBOUND_RISING_MISSED")
        and _has_signature(stock, "PRICE_JUMP_START")
        and low_rebound_pct >= 3.0
        and source_count >= 2
        and input_ready
        and effective_quote_age_ms <= 1000.0
        and spread_ratio <= TP1_SELECTOR_SPREAD_CAUTION_RATIO
        and micro_confidence >= 0.80
        and true_ofi_ewma > 0.0
        and pressure_ewma >= 70.0
        and support_families["order_flow"]
    )
    if nxt_price_jump_recovery_lane:
        lane = "nxt_price_jump_recovery"
    support_reversal_lane = bool(
        lane == "none"
        and len(positive_supports) >= TP1_SELECTOR_MIN_POSITIVE_SUPPORT_FAMILIES
    )
    if support_reversal_lane:
        lane = "support_reversal"
    hard_negative_reasons = []
    if ai_action in {"DROP", "NOT_EVALUATED", "FAIL_CLOSED", "UNAVAILABLE"}:
        hard_negative_reasons.append("ai_explicit_veto")
    if signed_tape_state == "sell_dominated":
        hard_negative_reasons.append("fresh_sell_dominated_tape")
    counterfactual_risks = []
    if spread_ratio > TP1_SELECTOR_SPREAD_CAUTION_RATIO:
        counterfactual_risks.append("spread_above_candidate_caution")
    if not micro_trusted:
        counterfactual_risks.append("micro_confidence_below_prior")
    if true_ofi_ewma <= 0.0:
        counterfactual_risks.append("true_ofi_nonpositive")
    if pressure_ewma < 49.0:
        counterfactual_risks.append("pressure_below_prior")
    if depth_imbalance_ewma < -0.05 or top_depth_ratio < 0.95:
        counterfactual_risks.append("depth_support_weak")
    if not support_families["momentum"]:
        counterfactual_risks.append("momentum_support_weak")
    if (
        ai_action in {"", "-", "WAIT", "MISSING", "NONE", "NULL"}
        and not bid_imbalance_surge
    ):
        counterfactual_risks.append("wait_without_bid_imbalance")
    if watch_delta_available and watch_delta_pct > TP1_SELECTOR_CHASE_DELTA_PCT:
        counterfactual_risks.append("acceleration_above_chase_prior")
    counterfactual_action = (
        "INPUT_DEFER_EXPECTED"
        if not input_ready or effective_quote_age_ms > 3000.0
        else (
            "HARD_VETO_EXPECTED"
            if hard_negative_reasons
            else (
                "RECHECK_REQUIRED"
                if counterfactual_risks
                else "NO_CURRENT_VETO_EVIDENCE"
            )
        )
    )
    base_fields = {
        "rising_missed_tp1_selector_enabled": bool(selector_enabled),
        "rising_missed_tp1_selector_active": active,
        "rising_missed_tp1_selector_active_date": active_date or "-",
        "rising_missed_tp1_selector_current_date": current_date or "-",
        "rising_missed_tp1_candidate_lane": lane,
        "rising_missed_tp1_source_family_count": source_count,
        "rising_missed_tp1_low_rebound_pct": f"{low_rebound_pct:.4f}",
        "rising_missed_tp1_watch_delta_pct": (
            f"{watch_delta_pct:.4f}" if watch_delta_available else "-"
        ),
        "rising_missed_tp1_ai_action": ai_action or "-",
        "rising_missed_tp1_bid_imbalance_surge": bid_imbalance_surge,
        "rising_missed_tp1_selector_policy": "probability_support_v3",
        "rising_missed_tp1_support_reversal_lane": support_reversal_lane,
        "rising_missed_tp1_nxt_price_jump_recovery_enabled": bool(
            nxt_price_jump_recovery_enabled
        ),
        "rising_missed_tp1_nxt_price_jump_recovery_active_date": (
            nxt_price_jump_recovery_active_date or "-"
        ),
        "rising_missed_tp1_nxt_price_jump_recovery_lane": (
            nxt_price_jump_recovery_lane
        ),
        "rising_missed_tp1_positive_support_count": len(positive_supports),
        "rising_missed_tp1_positive_support_min": (
            1
            if nxt_price_jump_recovery_lane
            else TP1_SELECTOR_MIN_POSITIVE_SUPPORT_FAMILIES
        ),
        "rising_missed_tp1_positive_support_families": ",".join(positive_supports)
        or "-",
        "rising_missed_tp1_support_bid_imbalance": support_families["bid_imbalance"],
        "rising_missed_tp1_support_order_flow": support_families["order_flow"],
        "rising_missed_tp1_support_depth": support_families["depth"],
        "rising_missed_tp1_support_momentum": support_families["momentum"],
        "rising_missed_tp1_spread_caution_ratio": TP1_SELECTOR_SPREAD_CAUTION_RATIO,
        "rising_missed_tp1_spread_penalty_applied": bool(
            spread_ratio > TP1_SELECTOR_SPREAD_CAUTION_RATIO
        ),
        "rising_missed_tp1_spread_hard_blocked": False,
        "rising_missed_tp1_chase_prior_pct": TP1_SELECTOR_CHASE_DELTA_PCT,
        "rising_missed_tp1_chase_recheck_required": bool(
            watch_delta_available and watch_delta_pct > TP1_SELECTOR_CHASE_DELTA_PCT
        ),
        "rising_missed_tp1_hard_negative_reasons": (
            ",".join(hard_negative_reasons) if hard_negative_reasons else "-"
        ),
        "rising_missed_tp1_downstream_submit_safety_required": True,
        "rising_missed_tp1_counterfactual_submit_safety_action": counterfactual_action,
        "rising_missed_tp1_counterfactual_submit_safety_risks": (
            ",".join(counterfactual_risks) if counterfactual_risks else "-"
        ),
        "rising_missed_tp1_counterfactual_submit_safety_metric_role": "source_only",
        "rising_missed_tp1_counterfactual_submit_safety_decision_authority": (
            "source_only_candidate_to_submit_safety_projection"
        ),
        "rising_missed_tp1_counterfactual_submit_safety_runtime_effect": False,
        "rising_missed_tp1_counterfactual_submit_safety_allowed_runtime_apply": False,
        "rising_missed_tp1_counterfactual_submit_safety_actual_order_submitted": False,
        "rising_missed_tp1_counterfactual_submit_safety_broker_order_forbidden": True,
        "rising_missed_tp1_gross_target_pct": TP1_SELECTOR_GROSS_TARGET_PCT,
        "rising_missed_tp1_adverse_stop_pct": TP1_SELECTOR_ADVERSE_STOP_PCT,
        "rising_missed_tp1_cost_reserve_pct": TP1_SELECTOR_COST_RESERVE_PCT,
        "rising_missed_tp1_net_target_pct": TP1_SELECTOR_NET_TARGET_PCT,
        "rising_missed_tp1_horizon_sec": TP1_SELECTOR_HORIZON_SEC,
        "rising_missed_tp1_actual_fee_tax_required_for_net_label": True,
        "metric_role": "bounded_tunable_candidate_gate",
        "decision_authority": (
            "operator_runtime_override_rising_missed_nxt_price_jump_recovery"
            if nxt_price_jump_recovery_lane
            else "operator_runtime_override_rising_missed_tp1_candidate_selector"
        ),
        "window_policy": "same_day_intraday_candidate_then_postclose_20m_label",
        "sample_floor": (
            "nxt_low_rebound_price_jump_one_positive_order_flow_support"
            if nxt_price_jump_recovery_lane
            else "identity_lane_or_two_independent_positive_support_families"
        ),
        "primary_decision_metric": "gross_1_30_before_adverse_0_70_within_20m",
        "source_quality_gate": "freshness_envelope_and_trusted_ws_micro_required",
        "threshold_family": (
            "rising_missed_nxt_price_jump_recovery"
            if nxt_price_jump_recovery_lane
            else "rising_missed_tp1_selector"
        ),
        "rising_missed_tp1_nxt_price_jump_recovery_runtime_effect": (
            nxt_price_jump_recovery_lane
        ),
        "rising_missed_tp1_nxt_price_jump_recovery_allowed_runtime_apply": (
            nxt_price_jump_recovery_lane
        ),
        "forbidden_uses": (
            "broker_guard_bypass,submit_safety_bypass,quantity_or_cap_change,provider_route_change,"
            "tp_or_exit_change,hard_or_protect_or_emergency_guard_relaxation,profit_guarantee"
        ),
    }

    def _decision_fields(
        *, allowed: bool, deferred: bool, reason: str
    ) -> dict[str, Any]:
        return {
            **base_fields,
            **decision_input,
            "rising_missed_tp1_candidate_allowed": allowed,
            "rising_missed_tp1_candidate_deferred": deferred,
            "rising_missed_tp1_candidate_reason": reason,
        }

    if not active:
        return RisingMissedTP1CandidateDecision(
            allowed=True,
            deferred=False,
            reason=TP1_SELECTOR_BYPASS,
            lane=lane,
            log_fields=_decision_fields(
                allowed=True,
                deferred=False,
                reason=TP1_SELECTOR_BYPASS,
            ),
        )
    if not input_ready:
        return RisingMissedTP1CandidateDecision(
            allowed=False,
            deferred=True,
            reason=str(
                decision_input.get("rising_missed_tp1_input_reason")
                or TP1_SELECTOR_DEFER_INPUT
            ),
            lane=lane,
            log_fields=_decision_fields(
                allowed=False,
                deferred=True,
                reason=str(
                    decision_input.get("rising_missed_tp1_input_reason")
                    or TP1_SELECTOR_DEFER_INPUT
                ),
            ),
        )
    if effective_quote_age_ms > 3000.0:
        return RisingMissedTP1CandidateDecision(
            allowed=False,
            deferred=True,
            reason="tp1_effective_quote_stale",
            lane=lane,
            log_fields=_decision_fields(
                allowed=False,
                deferred=True,
                reason="tp1_effective_quote_stale",
            ),
        )
    if lane == "none":
        return RisingMissedTP1CandidateDecision(
            allowed=False,
            deferred=False,
            reason=TP1_SELECTOR_BLOCK_LANE,
            lane=lane,
            log_fields=_decision_fields(
                allowed=False,
                deferred=False,
                reason=TP1_SELECTOR_BLOCK_LANE,
            ),
        )
    if ai_action in {"DROP", "NOT_EVALUATED", "FAIL_CLOSED", "UNAVAILABLE"}:
        return RisingMissedTP1CandidateDecision(
            allowed=False,
            deferred=False,
            reason=TP1_SELECTOR_BLOCK_AI,
            lane=lane,
            log_fields=_decision_fields(
                allowed=False,
                deferred=False,
                reason=TP1_SELECTOR_BLOCK_AI,
            ),
        )
    if hard_negative_reasons:
        return RisingMissedTP1CandidateDecision(
            allowed=False,
            deferred=False,
            reason=TP1_SELECTOR_BLOCK_HARD_NEGATIVE,
            lane=lane,
            log_fields=_decision_fields(
                allowed=False,
                deferred=False,
                reason=TP1_SELECTOR_BLOCK_HARD_NEGATIVE,
            ),
        )
    required_positive_supports = (
        1
        if nxt_price_jump_recovery_lane
        else (TP1_SELECTOR_MIN_POSITIVE_SUPPORT_FAMILIES)
    )
    if len(positive_supports) < required_positive_supports:
        return RisingMissedTP1CandidateDecision(
            allowed=False,
            deferred=False,
            reason=TP1_SELECTOR_BLOCK_SUPPORT,
            lane=lane,
            log_fields=_decision_fields(
                allowed=False,
                deferred=False,
                reason=TP1_SELECTOR_BLOCK_SUPPORT,
            ),
        )
    return RisingMissedTP1CandidateDecision(
        allowed=True,
        deferred=False,
        reason=TP1_SELECTOR_PASS,
        lane=lane,
        log_fields=_decision_fields(
            allowed=True,
            deferred=False,
            reason=TP1_SELECTOR_PASS,
        ),
    )


def _prior_log_fields(stock: dict[str, Any]) -> dict[str, Any]:
    prior = stock.get("rising_missed_prior")
    prior = prior if isinstance(prior, dict) else {}
    return {
        "rising_missed_prior_key": stock.get("rising_missed_prior_key")
        or prior.get("prior_key")
        or "-",
        "rising_missed_prior_recommendation": stock.get(
            "rising_missed_prior_recommendation"
        )
        or prior.get("recommendation")
        or "unavailable",
        "rising_missed_prior_confidence": stock.get("rising_missed_prior_confidence")
        or prior.get("confidence")
        or "none",
        "rising_missed_prior_window": stock.get("rising_missed_prior_window")
        or prior.get("selected_window")
        or "-",
        "rising_missed_prior_reason": stock.get("rising_missed_prior_reason")
        or prior.get("reason")
        or "prior_not_attached",
    }


def _candidate_gate_filter_fields(*, allowed: bool = False) -> dict[str, Any]:
    return {
        "rising_missed_filter_layer": RISING_MISSED_FILTER_LAYER_CANDIDATE_GATE,
        "rising_missed_filter_owner": RISING_MISSED_FILTER_OWNER_CANDIDATE_GATE,
        "rising_missed_filter_action": (
            RISING_MISSED_FILTER_ACTION_CANDIDATE_ALLOW
            if allowed
            else RISING_MISSED_FILTER_ACTION_CANDIDATE_BLOCK
        ),
        "rising_missed_opportunity_cost_policy": RISING_MISSED_OPPORTUNITY_COST_POLICY,
    }


def _entry_ai_action_for_rising_missed(stock: dict[str, Any]) -> tuple[str, str]:
    for key in (
        "rising_missed_entry_ai_action",
        "entry_ai_action",
        "ai_action",
        "last_ai_action",
        "current_ai_action",
        "last_watching_ai_action",
    ):
        value = stock.get(key)
        text = str(value or "").strip()
        if text:
            return text, key
    return "-", "missing"


def _entry_ai_action_not_evaluated(stock: dict[str, Any]) -> bool:
    action, _source = _entry_ai_action_for_rising_missed(stock)
    return action.strip().lower() == "not_evaluated"


def _positive_delta_pct(stock: dict[str, Any], explicit_delta_pct: Any = None) -> float:
    values = [
        explicit_delta_pct,
        stock.get("price_delta_since_first_seen_pct"),
        stock.get("scanner_positive_delta_pct"),
        stock.get("comparable_flu_delta_since_first_seen"),
        stock.get("max_price_delta_since_first_seen_pct"),
        stock.get("low_rebound_pct"),
        stock.get("LowReboundPct"),
    ]
    return max(0.0, *(_safe_float(value, 0.0) for value in values))


def resolve_rising_missed_scout_forced_qty(
    *,
    current_price: Any = None,
    budget_cap_krw: Any = DEFAULT_RISING_MISSED_SCOUT_ENTRY_BUDGET_CAP_KRW,
) -> tuple[int, dict[str, Any]]:
    entry_price = _safe_int(current_price, 0)
    return 1, {
        "rising_missed_scout_sizing_mode": "central_allocator_at_submit",
        "rising_missed_scout_budget_owner": "position_sizing_dynamic_formula",
        "rising_missed_scout_legacy_budget_cap_ignored": bool(
            _safe_int(budget_cap_krw, 0) > 0
        ),
        "rising_missed_scout_selection_qty_placeholder": 1,
        "rising_missed_scout_selection_price": entry_price,
    }


def classify_rising_missed_candidate(
    *,
    max_delta_pct: Any,
    real_submit_count: Any = 0,
    min_delta_pct: float = 1.0,
    source_quality_excluded: bool = False,
    intended_guard_preserved: bool = False,
    runtime_backpressure_observation: bool = False,
    strategy_reject_missed: bool = False,
    actionable_major_missed: bool = False,
) -> RisingMissedClassification:
    delta = _safe_float(max_delta_pct, 0.0)
    submit_count = _safe_int(real_submit_count, 0)
    threshold = max(0.0, float(min_delta_pct))
    if delta < threshold:
        return RisingMissedClassification(
            rising_missed=False,
            rising_missed_class=RISING_MISSED_CLASS_NOT_RISING,
            one_share_eligible=False,
            reason="below_rising_missed_threshold",
        )
    if submit_count > 0:
        return RisingMissedClassification(
            rising_missed=False,
            rising_missed_class=RISING_MISSED_CLASS_SUBMITTED_RESOLVED,
            one_share_eligible=False,
            reason="real_submit_observed",
        )
    if source_quality_excluded:
        klass = RISING_MISSED_CLASS_SOURCE_QUALITY_EXCLUDED
        reason = "source_quality_excluded"
    elif intended_guard_preserved:
        klass = RISING_MISSED_CLASS_INTENDED_GUARD_PRESERVED
        reason = "intended_guard_preserved"
    elif runtime_backpressure_observation:
        klass = RISING_MISSED_CLASS_RUNTIME_BACKPRESSURE
        reason = "runtime_backpressure_observation"
    elif strategy_reject_missed:
        klass = RISING_MISSED_CLASS_STRATEGY_REJECT
        reason = "strategy_reject_missed"
    elif actionable_major_missed:
        klass = RISING_MISSED_CLASS_ACTIONABLE_MAJOR
        reason = "actionable_major_missed"
    else:
        klass = RISING_MISSED_CLASS_RAW
        reason = "rising_missed_raw"
    return RisingMissedClassification(
        rising_missed=True,
        rising_missed_class=klass,
        one_share_eligible=klass in RISING_MISSED_ONE_SHARE_ELIGIBLE_CLASSES,
        reason=reason,
    )


def _looks_like_scalping_rising_missed_candidate(
    stock: dict[str, Any],
    *,
    strategy: str,
    position_tag: str,
    positive_delta_pct: float,
    min_delta_pct: float,
) -> bool:
    if _normalized_text(strategy) != "SCALPING":
        return False
    if positive_delta_pct < max(0.0, float(min_delta_pct)):
        return False
    return bool(
        _field_present(stock.get("scanner_promotion_id"))
        or _field_present(stock.get("scanner_promotion_reason"))
        or _field_present(stock.get("entry_armed_at_epoch"))
        or _field_present(stock.get("_scanner_rising_entry_relief_reason"))
        or _field_present(stock.get("rising_missed_buy"))
        or _field_present(stock.get("rising_entry_relief_eligible"))
        or _field_present(stock.get("rising_missed_lineage"))
        or _field_present(stock.get("low_rebound_pct"))
        or _field_present(stock.get("LowReboundPct"))
        or "LOW_REBOUND_RISING_MISSED"
        in str(stock.get("source_signature") or "").upper()
    )


def evaluate_rising_missed_one_share_entry(
    stock: dict[str, Any] | None,
    *,
    strategy: str,
    position_tag: str,
    feature_enabled: bool,
    has_open_pending: bool,
    already_holding: bool,
    positive_delta_pct: Any = None,
    min_delta_pct: float = 1.0,
    current_price: Any = None,
    max_entry_price_krw: int = MAX_ONE_SHARE_ENTRY_PRICE_KRW,
    scout_budget_cap_krw: int = DEFAULT_RISING_MISSED_SCOUT_ENTRY_BUDGET_CAP_KRW,
    current_fluctuation_pct: Any = None,
    upper_limit_exclude_enabled: bool = True,
    upper_limit_exclude_pct: float = DEFAULT_RISING_MISSED_UPPER_LIMIT_EXCLUDE_PCT,
) -> RisingMissedOneShareDecision:
    stock = stock if isinstance(stock, dict) else {}
    delta_pct = _positive_delta_pct(stock, explicit_delta_pct=positive_delta_pct)
    fluctuation_pct = _safe_float(
        (
            current_fluctuation_pct
            if current_fluctuation_pct is not None
            else stock.get(
                "fluctuation", stock.get("fluctuation_rate", stock.get("flu_rate"))
            )
        ),
        0.0,
    )
    entry_price = (
        _safe_int(current_price, 0)
        or _safe_int(stock.get("target_buy_price"), 0)
        or _safe_int(stock.get("curr_price"), 0)
    )
    price_cap = max(0, _safe_int(max_entry_price_krw, MAX_ONE_SHARE_ENTRY_PRICE_KRW))
    forced_qty, sizing_fields = resolve_rising_missed_scout_forced_qty(
        current_price=entry_price,
        budget_cap_krw=scout_budget_cap_krw,
    )
    upper_limit_threshold = max(
        0.0,
        _safe_float(
            upper_limit_exclude_pct, DEFAULT_RISING_MISSED_UPPER_LIMIT_EXCLUDE_PCT
        ),
    )
    base_fields = {
        **_candidate_gate_filter_fields(allowed=False),
        "rising_missed_one_share_entry_enabled": bool(feature_enabled),
        "rising_missed_one_share_entry_positive_delta_pct": f"{delta_pct:.4f}",
        "rising_missed_one_share_entry_min_delta_pct": f"{float(min_delta_pct):.4f}",
        "rising_missed_one_share_entry_strategy": _normalized_text(strategy) or "-",
        "rising_missed_one_share_entry_position_tag": _normalized_text(position_tag)
        or "-",
        "rising_missed_one_share_entry_forced_qty": forced_qty,
        "rising_missed_one_share_entry_price": entry_price,
        "rising_missed_one_share_entry_price_cap_krw": price_cap,
        "rising_missed_one_share_entry_fluctuation_pct": f"{fluctuation_pct:.2f}",
        "rising_missed_one_share_entry_upper_limit_exclude_pct": f"{upper_limit_threshold:.2f}",
        "rising_missed_one_share_entry_upper_limit_gap_to_limit_pct": f"{max(0.0, 30.0 - fluctuation_pct):.2f}",
        "rising_missed_one_share_entry_upper_limit_exclude_enabled": bool(
            upper_limit_exclude_enabled
        ),
    }
    base_fields.update(sizing_fields)
    base_fields.update(_prior_log_fields(stock))
    entry_ai_action, entry_ai_action_source = _entry_ai_action_for_rising_missed(stock)
    base_fields.update(
        {
            "rising_missed_entry_ai_action": entry_ai_action,
            "rising_missed_entry_ai_action_source": entry_ai_action_source,
            "rising_missed_entry_ai_not_evaluated_excluded": _entry_ai_action_not_evaluated(
                stock
            ),
        }
    )
    classification = classify_rising_missed_candidate(
        max_delta_pct=delta_pct,
        real_submit_count=stock.get("real_submit_count")
        or stock.get("actual_order_submit_count")
        or 0,
        min_delta_pct=min_delta_pct,
        source_quality_excluded=stock.get("rising_missed_class")
        == RISING_MISSED_CLASS_SOURCE_QUALITY_EXCLUDED,
        intended_guard_preserved=stock.get("rising_missed_class")
        == RISING_MISSED_CLASS_INTENDED_GUARD_PRESERVED,
        runtime_backpressure_observation=stock.get("rising_missed_class")
        == RISING_MISSED_CLASS_RUNTIME_BACKPRESSURE,
        strategy_reject_missed=stock.get("rising_missed_class")
        == RISING_MISSED_CLASS_STRATEGY_REJECT,
        actionable_major_missed=stock.get("rising_missed_class")
        == RISING_MISSED_CLASS_ACTIONABLE_MAJOR,
    )
    base_fields.update(
        {
            "rising_missed_class": classification.rising_missed_class,
            "rising_missed_class_reason": classification.reason,
            "rising_missed_one_share_eligible": classification.one_share_eligible,
        }
    )
    if not feature_enabled:
        return RisingMissedOneShareDecision(
            allowed=False,
            reason=BLOCK_FEATURE_DISABLED,
            positive_delta_pct=delta_pct,
            log_fields=base_fields,
        )
    if (
        classification.rising_missed_class == RISING_MISSED_CLASS_SUBMITTED_RESOLVED
        or (classification.rising_missed and not classification.one_share_eligible)
    ):
        return RisingMissedOneShareDecision(
            allowed=False,
            reason=BLOCK_CLASS_NOT_ELIGIBLE,
            positive_delta_pct=delta_pct,
            log_fields=base_fields,
        )
    if not _looks_like_scalping_rising_missed_candidate(
        stock,
        strategy=strategy,
        position_tag=position_tag,
        positive_delta_pct=delta_pct,
        min_delta_pct=min_delta_pct,
    ):
        return RisingMissedOneShareDecision(
            allowed=False,
            reason=BLOCK_NOT_CANDIDATE,
            positive_delta_pct=delta_pct,
            log_fields=base_fields,
        )
    if _entry_ai_action_not_evaluated(stock):
        base_fields.update(
            {
                "rising_missed_class": RISING_MISSED_CLASS_SOURCE_QUALITY_EXCLUDED,
                "rising_missed_class_reason": BLOCK_ENTRY_AI_NOT_EVALUATED,
                "rising_missed_one_share_eligible": False,
            }
        )
        return RisingMissedOneShareDecision(
            allowed=False,
            reason=BLOCK_ENTRY_AI_NOT_EVALUATED,
            positive_delta_pct=delta_pct,
            log_fields=base_fields,
        )
    if (
        upper_limit_exclude_enabled
        and upper_limit_threshold > 0
        and fluctuation_pct >= upper_limit_threshold
    ):
        base_fields.update(
            {
                "rising_missed_class": RISING_MISSED_CLASS_SOURCE_QUALITY_EXCLUDED,
                "rising_missed_class_reason": BLOCK_UPPER_LIMIT_PROXIMITY,
                "rising_missed_one_share_eligible": False,
            }
        )
        return RisingMissedOneShareDecision(
            allowed=False,
            reason=BLOCK_UPPER_LIMIT_PROXIMITY,
            positive_delta_pct=delta_pct,
            log_fields=base_fields,
        )
    if has_open_pending:
        return RisingMissedOneShareDecision(
            allowed=False,
            reason=BLOCK_OPEN_PENDING,
            positive_delta_pct=delta_pct,
            log_fields=base_fields,
        )
    if already_holding:
        return RisingMissedOneShareDecision(
            allowed=False,
            reason=BLOCK_ALREADY_HOLDING,
            positive_delta_pct=delta_pct,
            log_fields=base_fields,
        )
    if price_cap > 0 and entry_price > price_cap:
        return RisingMissedOneShareDecision(
            allowed=False,
            reason=BLOCK_PRICE_ABOVE_CAP,
            positive_delta_pct=delta_pct,
            log_fields=base_fields,
        )
    return RisingMissedOneShareDecision(
        allowed=True,
        reason=FORCED_ENTRY_REASON,
        forced_qty=forced_qty,
        positive_delta_pct=delta_pct,
        log_fields={**base_fields, **_candidate_gate_filter_fields(allowed=True)},
    )


def evaluate_rising_missed_normal_buy_bridge(
    stock: dict[str, Any] | None,
    *,
    strategy: str,
    position_tag: str,
    feature_enabled: bool,
    has_open_pending: bool,
    already_holding: bool,
    current_ai_action: Any = None,
    positive_delta_pct: Any = None,
    min_delta_pct: float = 1.0,
    current_price: Any = None,
    max_entry_price_krw: int = MAX_ONE_SHARE_ENTRY_PRICE_KRW,
    scout_budget_cap_krw: int = DEFAULT_RISING_MISSED_SCOUT_ENTRY_BUDGET_CAP_KRW,
    current_fluctuation_pct: Any = None,
    upper_limit_exclude_enabled: bool = True,
    upper_limit_exclude_pct: float = DEFAULT_RISING_MISSED_UPPER_LIMIT_EXCLUDE_PCT,
) -> RisingMissedNormalBuyBridgeDecision:
    stock = stock if isinstance(stock, dict) else {}
    decision = evaluate_rising_missed_one_share_entry(
        stock,
        strategy=strategy,
        position_tag=position_tag,
        feature_enabled=feature_enabled,
        has_open_pending=has_open_pending,
        already_holding=already_holding,
        positive_delta_pct=positive_delta_pct,
        min_delta_pct=min_delta_pct,
        current_price=current_price,
        max_entry_price_krw=max_entry_price_krw,
        scout_budget_cap_krw=scout_budget_cap_krw,
        current_fluctuation_pct=current_fluctuation_pct,
        upper_limit_exclude_enabled=upper_limit_exclude_enabled,
        upper_limit_exclude_pct=upper_limit_exclude_pct,
    )
    log_fields = {
        key: value
        for key, value in dict(decision.log_fields or {}).items()
        if key != "rising_missed_one_share_entry_forced_qty"
        and not str(key).startswith("rising_missed_scout_")
    }
    action = (
        str(
            current_ai_action
            if current_ai_action not in (None, "")
            else _entry_ai_action_for_rising_missed(stock)[0]
        )
        .strip()
        .upper()
    )
    allowed = bool(decision.allowed and action == "BUY")
    reason = NORMAL_BUY_BRIDGE_REASON if allowed else decision.reason
    if decision.allowed and action != "BUY":
        reason = BLOCK_ENTRY_AI_ACTION_NOT_BUY
    log_fields.update(
        {
            **_candidate_gate_filter_fields(allowed=allowed),
            "rising_missed_normal_buy_bridge_enabled": bool(feature_enabled),
            "rising_missed_normal_buy_bridge_allowed": allowed,
            "rising_missed_normal_buy_bridge_reason": reason,
            "rising_missed_normal_buy_bridge_underlying_reason": decision.reason,
            "rising_missed_normal_buy_bridge_ai_action": action or "-",
            "rising_missed_normal_buy_bridge_uses_normal_sizing": True,
            "rising_missed_normal_buy_bridge_forced_scout_fields_used": False,
        }
    )
    return RisingMissedNormalBuyBridgeDecision(
        allowed=allowed,
        reason=reason,
        log_fields=log_fields,
    )


def is_forced_rising_missed_one_share_entry(
    stock: dict[str, Any] | None, runtime: dict[str, Any] | None
) -> bool:
    stock = stock if isinstance(stock, dict) else {}
    runtime = runtime if isinstance(runtime, dict) else {}
    return (
        bool(stock.get("rising_missed_one_share_entry_forced"))
        and _safe_int(stock.get("forced_entry_qty"), 0) > 0
        and str(
            stock.get("forced_entry_reason") or runtime.get("forced_entry_reason") or ""
        ).strip()
        == FORCED_ENTRY_REASON
    )


def collapse_to_one_share_order(
    planned_orders: list[dict[str, Any]] | None,
    *,
    fallback_price: int,
    forced_qty: int = 1,
) -> list[dict[str, Any]]:
    base = dict((planned_orders or [{}])[0] or {})
    price = _safe_int(base.get("price"), 0) or _safe_int(fallback_price, 0)
    base.update(
        {
            "tag": FORCED_ENTRY_REASON,
            "qty": max(1, _safe_int(forced_qty, 1)),
            "price": price,
            "tif": base.get("tif") or "DAY",
        }
    )
    base["rising_missed_one_share_entry_forced"] = True
    return [base]

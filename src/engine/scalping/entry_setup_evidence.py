"""Deterministic entry setup evidence and offline AI risk composition.

This module is deliberately independent from the Windows widget advisory stack.
It consumes the existing exact-payload analysis ledgers and never calls a
provider, broker, account, order, or token endpoint.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any

from src.trading.order.tick_utils import get_tick_size

ENTRY_SETUP_EVIDENCE_SCHEMA = "entry_setup_evidence_v1"
ENTRY_RISK_ADJUDICATION_SCHEMA = "entry_setup_risk_adjudication_v1"
ENTRY_ACTION_COMPARISON_SCHEMA = "entry_action_comparative_adjudication_v1"
ENTRY_ACTION_COUNTERWEIGHT_COMPARISON_SCHEMA = (
    "entry_action_counterweight_comparative_adjudication_v2"
)
ENTRY_ACTION_COUNTERWEIGHT_BINDINGS_SCHEMA = "entry_action_counterweight_bindings_v1"
ENTRY_DECISION_COMPOSER_SCHEMA = "entry_decision_composer_v1"
ENTRY_SETUP_EVIDENCE_VERSION = "entry_setup_evidence_policy_v10"
ENTRY_SETUP_TIMING_EVIDENCE_VERSION = "entry_setup_evidence_policy_v11_timing_aware"
ENTRY_SETUP_BALANCED_EVIDENCE_VERSION = "entry_setup_evidence_policy_v12_balanced"
ENTRY_DECISION_COMPOSER_V2_14_2_VERSION = "entry_decision_composer_v2_14_2_balanced"
ENTRY_DECISION_COMPOSER_V2_15_2_VERSION = "entry_decision_composer_v2_15_2_balanced"
ENTRY_DECISION_COMPOSER_V2_14_3_VERSION = "entry_decision_composer_v2_14_3_comparative"
ENTRY_DECISION_COMPOSER_V2_15_3_VERSION = "entry_decision_composer_v2_15_3_comparative"
ENTRY_DECISION_COMPOSER_V2_14_4_VERSION = (
    "entry_decision_composer_v2_14_4_counterweight_bound"
)
ENTRY_DECISION_COMPOSER_V2_15_4_VERSION = (
    "entry_decision_composer_v2_15_4_counterweight_bound"
)
ENTRY_DECISION_COMPOSER_VERSION = "entry_decision_composer_policy_v11"
ENTRY_DECISION_COMPOSER_V2_15_VERSION = "entry_decision_composer_policy_v9"
ENTRY_DECISION_COMPOSER_V2_14_1_VERSION = (
    "entry_decision_composer_policy_v12_timing_aware"
)
ENTRY_DECISION_COMPOSER_V2_15_1_VERSION = (
    "entry_decision_composer_policy_v11_timing_aware"
)
ENTRY_DECISION_COMPOSER_V2_16_VERSION = "entry_decision_composer_policy_v10"
ENTRY_BOUNDED_RECOVERY_POLICY_VERSION = "entry_bounded_recovery_policy_v1"
ENTRY_SEQUENTIAL_RECOVERY_POLICY_VERSION = "entry_sequential_recovery_policy_v1"
STRUCTURE_PHASE_POLICY_VERSION = "entry_completed_bar_structure_phase_v2"
ENTRY_RISK_ADJUDICATION_REPAIR_VERSION = (
    "entry_setup_risk_fail_closed_invalidation_citation_v1"
)

TAIL_RISK_CALIBRATION_VERSION = "entry_tail_risk_calibration_v2"
TAIL_RISK_SPREAD_FLOOR_BP = 100.0
TAIL_RISK_FILLABILITY_CEILING = 15.0
TAIL_RISK_TOP3_ASK_TO_BID_FLOOR = 5.0
RELATIVE_WEAKNESS_FLOOR_PCT_POINT = -0.50
ENTRY_TIMING_CONTEXT_SCHEMA = "entry_timing_context_v1"
ENTRY_TIMING_OBSERVATION_SCHEMA = "entry_timing_observation_v1"
ENTRY_TIMING_POLICY_VERSION = "entry_timing_late_unreset_policy_v1"
ENTRY_TIMING_LATE_WATCH_SEC = 600.0
ENTRY_TIMING_MATERIAL_EXTENSION_PCT = 1.0
ENTRY_TIMING_REPROMOTION_FLOOR = 3
ENTRY_TIMING_RESET_DRAWDOWN_PCT = -0.50
ENTRY_GROUP_OBSERVATION_SCHEMA = "entry_predecision_group_observation_v1"

RECHECK_REASONS = {
    "TRIGGER_CONFIRMATION_RECHECK",
    "LARGE_SELL_EXHAUSTION_RECHECK",
    "TAIL_LIQUIDITY_RECHECK",
    "MICRO_PRICE_RESPONSE_RECHECK",
    "SETUP_DISCOVERY_RECHECK",
    "TIMING_RESET_RECHECK",
}

SETUP_FAMILIES = {
    "CLEAN_CONTINUATION",
    "PULLBACK_RECOVERY",
    "RECOVERY_CONFIRMATION",
    "MICRO_RECOVERY",
    "NO_VALID_SETUP",
}
SETUP_STATES = {"READY", "WAIT_CONFIRMATION", "UNCONFIRMED", "INVALID", "INSUFFICIENT"}
STRUCTURE_PHASES = {
    "distribution",
    "failed_breakout",
    "continuation",
    "pullback",
    "early_continuation_probe",
    "recovery_continuation",
    "rebound_attempt",
    "range_or_no_setup",
}
STRUCTURE_PHASE_FAMILIES = {
    "continuation": "CLEAN_CONTINUATION",
    "early_continuation_probe": "CLEAN_CONTINUATION",
    "pullback": "PULLBACK_RECOVERY",
    "recovery_continuation": "RECOVERY_CONFIRMATION",
    "rebound_attempt": "RECOVERY_CONFIRMATION",
}
RISK_VERDICTS = {"PASS", "CAUTION", "VETO", "INSUFFICIENT"}
COMPARATIVE_ENTRY_ACTIONS = {"ENTER_NOW", "RECHECK", "BLOCK"}
COMPARATIVE_RISK_DISPOSITIONS = {"COMPENSATED", "RECHECKABLE", "BLOCKING"}
COMPARATIVE_RECHECK_TRADEOFFS = {
    "ENTER_NOW_DOMINANT",
    "RECHECK_DOMINANT",
    "NOT_APPLICABLE_BLOCKED",
}
MECHANISTIC_ENTRY_THRESHOLD_POLICY_SCHEMA = "mechanistic_entry_threshold_policy_v1"
MECHANISTIC_PRIMARY_DECISION_SCHEMA = "mechanistic_entry_primary_decision_v2"
MECHANISTIC_POLICY_DECISION_SCHEMA = "mechanistic_entry_policy_decision_v1"
MECHANISTIC_ENTRY_FLOW_OBSERVATION_SCHEMA = "mechanistic_entry_flow_observation_v1"
MECHANISTIC_PRIMARY_DECISION_OWNER = "mechanistic_entry_adjudicator"
MECHANISTIC_AI_ADVISORY_ROLE = "auxiliary_risk_screen_pass_veto_no_promotion"
MECHANISTIC_PRIMARY_ROLE_CONTRACT = {
    "primary_decision_owner": MECHANISTIC_PRIMARY_DECISION_OWNER,
    "ai_role": MECHANISTIC_AI_ADVISORY_ROLE,
    "hard_safety_owner": "existing_runtime_submit_and_order_guards",
    "decision_precedence": [
        "hard_safety_and_source_quality",
        "mechanistic_entry_adjudicator",
        "ai_evidence_bound_risk_screen",
    ],
    "ai_can_promote_entry": False,
    "ai_can_veto_entry": True,
    "ai_can_override_hard_safety": False,
}
MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1 = {
    "schema": MECHANISTIC_ENTRY_THRESHOLD_POLICY_SCHEMA,
    "version": "mechanistic_entry_thresholds_initial_v1",
    "thresholds": {
        "minimum_micro_net_aggressive_delta_10t": 1.0,
        "minimum_micro_price_change_10t_pct": 0.0,
        "maximum_spread_bp": TAIL_RISK_SPREAD_FLOOR_BP,
        "minimum_fillability_score": TAIL_RISK_FILLABILITY_CEILING,
        "maximum_top3_ask_to_bid_ratio": TAIL_RISK_TOP3_ASK_TO_BID_FLOOR,
    },
    "postclose_selection": {
        "minimum_cost_adjusted_ev_pct": 0.10,
        "require_positive_paired_ev_delta": True,
        "minimum_exposure_count": 10,
        "minimum_unique_symbol_count": 3,
        "minimum_independent_source_date_count": 2,
        "require_bounded_probe_risk_budget_pass": True,
        "chronological_holdout_required": True,
    },
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
}
RISK_CODES = {
    "NO_BLOCKING_RISK",
    "SOURCE_QUALITY_GAP",
    "STRUCTURE_INVALIDATED",
    "DISTRIBUTION_RISK",
    "OVEREXTENSION_CHASE",
    "LIQUIDITY_UNUSABLE",
    "LIQUIDITY_FRAGILE",
    "ADVERSE_TAPE",
    "REWARD_RISK_WEAK",
    "CONFIRMATION_MISSING",
}

# Only structural/source/unusable-liquidity failures can turn an AI VETO into an
# offline DROP. Fragile-but-observable liquidity, tape, reward/risk, and
# confirmation concerns remain eligible for a one-share probe observation
# because the real submit and post-probe guards still own executable safety.
BLOCKING_VETO_RISK_CODES = {
    "SOURCE_QUALITY_GAP",
    "STRUCTURE_INVALIDATED",
    "DISTRIBUTION_RISK",
    "OVEREXTENSION_CHASE",
    "LIQUIDITY_UNUSABLE",
}

OBSERVATION_CONTRACT = {
    "metric_role": "ai_entry_setup_evidence_observation",
    "decision_authority": "offline_replay_and_attribution_only",
    "window_policy": "same_exact_payload_completed_bar_snapshot",
    "sample_floor": "one_exact_payload_starts_observation_only",
    "primary_decision_metric": "candidate_probe_cost_adjusted_ev_pct",
    "source_quality_gate": "exact_payload_fresh_same_route",
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "forbidden_uses": [
        "standalone_live_entry",
        "score_only_buy",
        "provider_or_model_change",
        "threshold_price_quantity_or_cap_change",
        "broker_or_safety_guard_bypass",
        "bot_restart",
        "widget_runtime_or_policy_change",
    ],
}

CONTEXT_OBSERVATION_CONTRACT = {
    "schema": "entry_setup_context_observations_v1",
    "version": "entry_setup_context_observations_policy_v1",
    "metric_role": "entry_risk_context_observation",
    "decision_authority": "bounded_nonblocking_risk_corroboration_only",
    "window_policy": "same_exact_payload_snapshot_no_cross_venue_fill",
    "sample_floor": "one_fresh_observation_starts_attribution_only",
    "primary_decision_metric": "candidate_probe_cost_adjusted_ev_pct",
    "source_quality_gate": "fresh_explicit_source_and_exact_observation_time",
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "forbidden_uses": [
        "create_or_promote_setup",
        "standalone_live_entry_or_block",
        "missing_as_adverse_evidence",
        "cross_venue_or_cross_session_imputation",
        "provider_model_price_quantity_or_threshold_change",
        "broker_or_safety_guard_bypass",
    ],
}


def build_entry_timing_context(
    *,
    decision_epoch: Any,
    promotion_events: Any,
    current_price: Any,
    effective_venue: Any = None,
    session_bucket: Any = None,
    source_kind: str = "scanner_promotion_events",
) -> dict[str, Any]:
    """Build an outcome-blind, no-lookahead scanner timing envelope."""

    decision = _number(decision_epoch)
    expected_venue = str(effective_venue or "").strip().upper()
    expected_session = str(session_bucket or "").strip().upper()
    events: list[dict[str, Any]] = []
    for raw in promotion_events if isinstance(promotion_events, list) else []:
        event = _as_dict(raw)
        fields = _as_dict(event.get("fields"))
        event_venue = str(fields.get("effective_venue") or "").strip().upper()
        event_session = (
            str(
                fields.get("market_session_bucket")
                or fields.get("session_bucket")
                or ""
            )
            .strip()
            .upper()
        )
        if expected_venue and event_venue != expected_venue:
            continue
        if expected_session and event_session != expected_session:
            continue
        epoch = _number(
            event.get("promotion_epoch")
            if event.get("promotion_epoch") is not None
            else event.get("emitted_epoch")
        )
        if decision is None or epoch is None or epoch <= 0 or epoch > decision:
            continue
        events.append({"promotion_epoch": epoch, "fields": fields})
    events.sort(key=lambda row: row["promotion_epoch"])
    deduplicated: list[dict[str, Any]] = []
    seen_promotion_ids: set[str] = set()
    for event in events:
        promotion_id = str(
            _as_dict(event.get("fields")).get("scanner_promotion_id") or ""
        )
        if promotion_id and promotion_id in seen_promotion_ids:
            continue
        if promotion_id:
            seen_promotion_ids.add(promotion_id)
        deduplicated.append(event)
    events = deduplicated
    first = events[0] if events else {}
    current = events[-1] if events else {}
    first_fields = _as_dict(first.get("fields"))
    current_fields = _as_dict(current.get("fields"))
    first_epoch = _number(first.get("promotion_epoch"))
    current_epoch = _number(current.get("promotion_epoch"))
    first_price = _number(first_fields.get("first_seen_price"))
    if first_price is None:
        first_price = _number(first_fields.get("current_price_observed"))
    observed_price = _number(current_price)
    if observed_price is None:
        observed_price = _number(current_fields.get("current_price_observed"))
    price_delta = (
        (observed_price / first_price - 1.0) * 100.0
        if first_price is not None
        and first_price > 0
        and observed_price is not None
        and observed_price > 0
        else None
    )
    promotion_ids = [
        str(_as_dict(row.get("fields")).get("scanner_promotion_id") or "")
        for row in events
    ]
    promotion_ids = [value for value in promotion_ids if value]
    timeline_exact = bool(
        decision is not None
        and first_epoch is not None
        and current_epoch is not None
        and promotion_ids
        and len(promotion_ids) == len(events)
    )
    context = {
        "schema": ENTRY_TIMING_CONTEXT_SCHEMA,
        "version": ENTRY_TIMING_POLICY_VERSION,
        "source_status": (
            "exact_scanner_promotion_asof" if timeline_exact else "insufficient"
        ),
        "source_kind": str(source_kind or "scanner_promotion_events"),
        "decision_epoch": decision,
        "first_watch_epoch": first_epoch,
        "current_promotion_epoch": current_epoch,
        "watch_age_sec": (
            max(0.0, decision - first_epoch)
            if decision is not None and first_epoch is not None
            else None
        ),
        "current_promotion_age_sec": (
            max(0.0, decision - current_epoch)
            if decision is not None and current_epoch is not None
            else None
        ),
        "promotion_count_as_of_decision": len(events),
        "first_watch_price": first_price,
        "decision_price": observed_price,
        "price_delta_since_first_watch_pct": (
            round(price_delta, 6) if price_delta is not None else None
        ),
        "promotion_ids_sha256": (
            _canonical_sha256(promotion_ids) if promotion_ids else None
        ),
        "effective_venue": expected_venue or None,
        "session_bucket": expected_session or None,
        "cohort_filter_applied": bool(expected_venue or expected_session),
        "no_lookahead_filter_applied": True,
        "latest_event_not_after_decision": bool(
            current_epoch is not None
            and decision is not None
            and current_epoch <= decision
        ),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    context["context_sha256"] = _canonical_sha256(context)
    return context


def _entry_timing_observation(
    timing_context: Any,
    *,
    completed_structure: dict[str, Any],
    balanced_policy: bool = False,
) -> dict[str, Any]:
    context = _as_dict(timing_context)
    exact = bool(
        context.get("schema") == ENTRY_TIMING_CONTEXT_SCHEMA
        and context.get("version") == ENTRY_TIMING_POLICY_VERSION
        and context.get("source_status") == "exact_scanner_promotion_asof"
        and context.get("no_lookahead_filter_applied") is True
        and context.get("latest_event_not_after_decision") is True
    )
    if balanced_policy:
        exact = exact and context.get("context_sha256") == _canonical_sha256(
            {k: v for k, v in context.items() if k != "context_sha256"}
        )
    watch_age = _number(context.get("watch_age_sec"))
    price_delta = _number(context.get("price_delta_since_first_watch_pct"))
    promotion_count = int(_number(context.get("promotion_count_as_of_decision")) or 0)
    returns = _as_dict(completed_structure.get("returns_pct"))
    positive_horizons: list[tuple[int, float]] = []
    for key, raw_value in returns.items():
        text = str(key or "").strip().lower()
        value = _number(raw_value)
        if not text.endswith("m") or value is None or value < 0.0:
            continue
        try:
            positive_horizons.append((int(text[:-1]), value))
        except ValueError:
            continue
    completed_uptrend_min = max((row[0] for row in positive_horizons), default=0)
    completed_uptrend_return = max((row[1] for row in positive_horizons), default=0.0)
    if balanced_policy:
        # A return belongs to its own horizon. Two independent maxima can
        # manufacture a long, strong uptrend that no observed window supports.
        completed_uptrend_min, completed_uptrend_return = max(
            (row for row in positive_horizons if row[0] >= 5),
            key=lambda row: row[1],
            default=(0, 0.0),
        )
        # Legacy context calls the earliest observed promotion "first_watch".
        # Its price was not timestamp-bound, so do not use it for extension.
        price_delta = None
    phase = str(completed_structure.get("phase") or "").strip().lower()
    peak_drawdown = _number(completed_structure.get("peak_drawdown_pct"))
    reset_observed = bool(
        phase in {"pullback", "recovery_continuation", "rebound_attempt"}
        and peak_drawdown is not None
        and peak_drawdown <= ENTRY_TIMING_RESET_DRAWDOWN_PCT
    )
    late = bool(watch_age is not None and watch_age >= ENTRY_TIMING_LATE_WATCH_SEC)
    repeated = promotion_count >= ENTRY_TIMING_REPROMOTION_FLOOR
    material_extension = bool(
        (price_delta is not None and price_delta >= ENTRY_TIMING_MATERIAL_EXTENSION_PCT)
        or (
            completed_uptrend_min >= 5
            and completed_uptrend_return >= ENTRY_TIMING_MATERIAL_EXTENSION_PCT
        )
    )
    if not exact:
        state = "insufficient"
        fact_id = None
    elif (late or repeated) and reset_observed:
        state = "late_but_reset_pullback"
        fact_id = "late_entry_reset_confirmed"
    elif repeated and material_extension:
        state = "repeated_repromotion_without_reset"
        fact_id = "repeated_repromotion_without_reset"
    elif late and material_extension:
        state = "late_unreset_extension"
        fact_id = "late_unreset_entry_timing"
    else:
        state = "early_or_unextended"
        fact_id = None
    observation = {
        "schema": ENTRY_TIMING_OBSERVATION_SCHEMA,
        "version": ENTRY_TIMING_POLICY_VERSION,
        "state": state,
        "fact_id": fact_id,
        "source_status": context.get("source_status") or "insufficient",
        "watch_age_sec": watch_age,
        "current_promotion_age_sec": _number(context.get("current_promotion_age_sec")),
        "promotion_count_as_of_decision": promotion_count,
        "price_delta_since_first_watch_pct": price_delta,
        "completed_uptrend_horizon_min": completed_uptrend_min,
        "completed_uptrend_return_pct": round(completed_uptrend_return, 6),
        "completed_structure_phase": phase or None,
        "completed_peak_drawdown_pct": peak_drawdown,
        "reset_observed": reset_observed,
        "late_watch_threshold_sec": ENTRY_TIMING_LATE_WATCH_SEC,
        "material_extension_threshold_pct": ENTRY_TIMING_MATERIAL_EXTENSION_PCT,
        "repromotion_floor": ENTRY_TIMING_REPROMOTION_FLOOR,
        "age_only_never_adverse": True,
        "missing_timing_never_adverse": True,
        "context_sha256": context.get("context_sha256"),
        "decision_authority": "bounded_entry_risk_corroboration_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    if balanced_policy:
        observation.update(
            first_observed_promotion_epoch=context.get("first_watch_epoch"),
            first_observed_promotion_age_sec=watch_age,
            first_watch_epoch=None,
            watch_age_sec=None,
            first_watch_missing_reason="promotion_is_not_first_watch_evidence",
            price_delta_since_first_watch_pct=None,
            price_delta_missing_reason="first_watch_price_time_not_bound",
            completed_uptrend_role="window_return_not_continuous_trend_duration",
            timing_proxy_never_hard_veto=True,
            late_promotion_threshold_sec=ENTRY_TIMING_LATE_WATCH_SEC,
        )
        observation.pop("late_watch_threshold_sec", None)
    return observation


def _entry_group_observation(
    *,
    payload: dict[str, Any],
    completed_structure: dict[str, Any],
    structure_phase: str,
    spread_bp: float | None,
    fillability_score: float | None,
    top3_ask_to_bid_ratio: float | None,
    timing_observation: dict[str, Any],
) -> dict[str, Any]:
    """Freeze a pre-decision group key; missing dimensions remain UNKNOWN."""

    current = _as_dict(payload.get("current"))
    price = _number(current.get("price"))
    tick_size = (
        _number(get_tick_size(price)) if price is not None and price > 0 else None
    )
    tick_pct = (
        tick_size / price * 100.0
        if tick_size is not None and tick_size > 0 and price is not None
        else None
    )
    price_tick_band = (
        "LT_5BP"
        if tick_pct is not None and tick_pct < 0.05
        else (
            "5_TO_10BP"
            if tick_pct is not None and tick_pct < 0.10
            else "GE_10BP" if tick_pct is not None else "UNKNOWN"
        )
    )
    if any(
        value is None for value in (spread_bp, fillability_score, top3_ask_to_bid_ratio)
    ):
        liquidity_band = "UNKNOWN"
    elif (
        spread_bp <= 40.0 and fillability_score >= 45.0 and top3_ask_to_bid_ratio <= 2.0
    ):
        liquidity_band = "SUPPORTIVE"
    elif (
        spread_bp <= 100.0
        and fillability_score >= 15.0
        and top3_ask_to_bid_ratio <= 5.0
    ):
        liquidity_band = "BOUNDED"
    else:
        liquidity_band = "FRAGILE"

    realized_volatility_pct = _number(
        completed_structure.get("realized_volatility_pct")
    )
    if realized_volatility_pct is None:
        candle_context = _as_dict(payload.get("entry_candle_context"))
        completed_closes = []
        for row in candle_context.get("bars") or []:
            bar = _as_dict(row)
            if bar.get("forming") is True or bar.get("is_forming") is True:
                continue
            close = _number(bar.get("close"))
            if close is None:
                close = _number(bar.get("c"))
            if close is not None and close > 0:
                completed_closes.append(close)
        close_returns_pct = [
            ((current_close / previous_close) - 1.0) * 100.0
            for previous_close, current_close in zip(
                completed_closes, completed_closes[1:]
            )
            if previous_close > 0
        ]
        if len(close_returns_pct) >= 2:
            mean_return = sum(close_returns_pct) / len(close_returns_pct)
            realized_volatility_pct = math.sqrt(
                sum(
                    (observed_return - mean_return) ** 2
                    for observed_return in close_returns_pct
                )
                / len(close_returns_pct)
            )
    volatility_band = (
        "LOW"
        if realized_volatility_pct is not None and realized_volatility_pct < 0.50
        else (
            "MEDIUM"
            if realized_volatility_pct is not None and realized_volatility_pct < 1.50
            else "HIGH" if realized_volatility_pct is not None else "UNKNOWN"
        )
    )
    watch_age = _number(timing_observation.get("watch_age_sec"))
    watch_age_band = (
        "LT_180S"
        if watch_age is not None and watch_age < 180.0
        else (
            "180_TO_600S"
            if watch_age is not None and watch_age < 600.0
            else "GE_600S" if watch_age is not None else "UNKNOWN"
        )
    )
    extension = _number(timing_observation.get("price_delta_since_first_watch_pct"))
    extension_band = (
        "RESET_OR_NEGATIVE"
        if extension is not None and extension < 0.0
        else (
            "LT_1PCT"
            if extension is not None and extension < 1.0
            else "GE_1PCT" if extension is not None else "UNKNOWN"
        )
    )
    routing = _as_dict(payload.get("routing"))
    venue = str(
        payload.get("effective_venue") or routing.get("effective_venue") or "UNKNOWN"
    ).upper()
    session = str(
        payload.get("session_bucket") or routing.get("session_bucket") or "UNKNOWN"
    ).upper()
    key_parts = {
        "price_tick_band": price_tick_band,
        "liquidity_band": liquidity_band,
        "volatility_band": volatility_band,
        "structure_phase": structure_phase,
        "watch_age_band": watch_age_band,
        "extension_band": extension_band,
        "venue": venue,
        "session_bucket": session,
    }
    body = {
        "schema": ENTRY_GROUP_OBSERVATION_SCHEMA,
        "key_parts": key_parts,
        "group_key": "|".join(key_parts.values()),
        "price": price,
        "tick_size": tick_size,
        "tick_pct": tick_pct,
        "realized_volatility_pct": realized_volatility_pct,
        "missing_dimensions": sorted(
            key for key, value in key_parts.items() if value == "UNKNOWN"
        ),
        "feature_time_boundary": "decision_time_or_completed_bar_only",
        "future_outcome_fields_forbidden": True,
        "symbol_specific_threshold_active": False,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    return {**body, "group_observation_sha256": _canonical_sha256(body)}


def build_entry_predecision_group_observation(
    *,
    exact_payload: Any,
    exact_analysis: Any,
    entry_timing_context: Any = None,
    balanced_policy: bool = False,
) -> dict[str, Any]:
    """Build offline-only grouping metadata without changing provider input."""

    payload = _as_dict(exact_payload)
    exact = _as_dict(exact_analysis)
    completed_structure = _as_dict(exact.get("completed_structure"))
    liquidity = _as_dict(exact.get("executable_liquidity"))
    structure_phase = str(completed_structure.get("phase") or "UNKNOWN")
    timing_observation = _entry_timing_observation(
        entry_timing_context,
        completed_structure=completed_structure,
        balanced_policy=balanced_policy,
    )
    return _entry_group_observation(
        payload=payload,
        completed_structure=completed_structure,
        structure_phase=structure_phase,
        spread_bp=_number(liquidity.get("spread_bp")),
        fillability_score=_number(liquidity.get("fillability_score")),
        top3_ask_to_bid_ratio=_number(liquidity.get("top3_ask_to_bid_ratio")),
        timing_observation=timing_observation,
    )


TAIL_RISK_OBSERVATION_CONTRACT = {
    "schema": "entry_tail_risk_assessment_v1",
    "version": TAIL_RISK_CALIBRATION_VERSION,
    "metric_role": "bounded_probe_risk_recheck_observation",
    "decision_authority": "offline_replay_and_attribution_only",
    "window_policy": "same_exact_payload_completed_bar_snapshot",
    "sample_floor": "one_exact_payload_starts_observation_only",
    "primary_decision_metric": "candidate_probe_worst_loss_pct",
    "source_quality_gate": "exact_payload_fresh_same_route",
    "calibration_scope": "clean_baseline_in_sample_exploratory",
    "validation_requirement": "new_post_policy_out_of_sample_trading_date",
    "promotion_authority": False,
    "thresholds": {
        "spread_floor_bp": TAIL_RISK_SPREAD_FLOOR_BP,
        "fillability_ceiling": TAIL_RISK_FILLABILITY_CEILING,
        "top3_ask_to_bid_floor": TAIL_RISK_TOP3_ASK_TO_BID_FLOOR,
        "combination": "all",
    },
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "forbidden_uses": [
        "standalone_live_entry_or_block",
        "broker_or_safety_guard_bypass",
        "threshold_price_quantity_or_cap_change",
        "provider_or_bot_change",
        "same_sample_live_promotion",
    ],
}


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _number(value: Any) -> float | None:
    try:
        parsed = float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def build_mechanistic_entry_flow_observation(exact_analysis: Any) -> dict[str, Any]:
    """Project pre-decision multi-horizon shape for grouped entry research.

    The projection deliberately carries no outcome, action, or label.  Its
    family memberships are a small, fixed and interpretable set so postclose
    calibration can test recurring shapes without a symbol-specific threshold
    grid.  A family match nominates a later RECHECK only; it is never sufficient
    to authorize ENTER without the separate micro-confirmation and EV gates.
    """

    exact = _as_dict(exact_analysis)
    structure = _as_dict(exact.get("completed_structure"))
    returns = _as_dict(structure.get("returns_pct"))
    slopes = _as_dict(structure.get("slopes_pct_per_bar"))
    liquidity = _as_dict(exact.get("executable_liquidity"))
    volume = _as_dict(exact.get("volume_confirmation"))
    tape = _as_dict(exact.get("tape_sample"))
    program = _as_dict(exact.get("program_flow"))
    source_quality = _as_dict(exact.get("source_quality"))

    horizon_values = {
        "returns_pct": {
            horizon: _number(returns.get(horizon))
            for horizon in ("1m", "3m", "5m", "10m", "20m", "60m")
        },
        "slopes_pct_per_bar": {
            horizon: _number(slopes.get(horizon))
            for horizon in ("1m", "3m", "5m", "10m", "20m", "60m")
        },
    }
    r5 = horizon_values["returns_pct"]["5m"]
    r10 = horizon_values["returns_pct"]["10m"]
    s5 = horizon_values["slopes_pct_per_bar"]["5m"]
    s10 = horizon_values["slopes_pct_per_bar"]["10m"]
    s20 = horizon_values["slopes_pct_per_bar"]["20m"]
    top3_ratio = _number(liquidity.get("top3_ask_to_bid_ratio"))
    volume_ratio = _number(volume.get("volume_ratio"))
    bars_since_session_high = _number(structure.get("bars_since_session_high"))

    family_memberships = {
        # Fixed research boundaries.  They are not live BUY thresholds.
        "DEPTH_SUPPORTED": top3_ratio is not None and top3_ratio <= 0.5,
        "HIGH_VELOCITY_CONTINUATION": (
            r5 is not None and r5 >= 5.0 and s5 is not None and s5 > 0.0
        ),
        "MID_HORIZON_STAIRCASE": (
            r10 is not None and 1.0 <= r10 < 2.0 and s10 is not None and s10 > 0.0
        ),
        "REBOUND_DECELERATION": (s20 is not None and -0.5 <= s20 < -0.1),
        "VOLUME_EXPANSION": (volume_ratio is not None and 1.5 <= volume_ratio < 2.0),
        "RECENT_SESSION_HIGH": bars_since_session_high == 0.0,
    }
    # Two bounded interaction families preserve recurring flow shape without
    # opening an arbitrary combinatorial grid.  They remain RECHECK-only.
    family_memberships.update(
        {
            "DEPTH_SUPPORTED_STAIRCASE": (
                family_memberships["DEPTH_SUPPORTED"]
                and family_memberships["MID_HORIZON_STAIRCASE"]
            ),
            "STAIRCASE_RECENT_HIGH": (
                family_memberships["MID_HORIZON_STAIRCASE"]
                and family_memberships["RECENT_SESSION_HIGH"]
            ),
        }
    )
    missing_fields = sorted(
        [
            f"returns_pct.{horizon}"
            for horizon, value in horizon_values["returns_pct"].items()
            if value is None
        ]
        + [
            f"slopes_pct_per_bar.{horizon}"
            for horizon, value in horizon_values["slopes_pct_per_bar"].items()
            if value is None
        ]
    )
    body = {
        "schema": MECHANISTIC_ENTRY_FLOW_OBSERVATION_SCHEMA,
        "source_analysis_sha256": exact.get("analysis_sha256"),
        "source_quality": {
            "status": source_quality.get("status"),
            "completed_bar_count": source_quality.get("completed_bar_count"),
            "forming_bar_excluded": source_quality.get("forming_bar_excluded"),
        },
        "completed_structure": {
            **horizon_values,
            "phase": structure.get("phase"),
            "regime": structure.get("regime"),
            "alignment": structure.get("alignment"),
            "peak_drawdown_pct": _number(structure.get("peak_drawdown_pct")),
            "rolling_20m_peak_drawdown_pct": _number(
                structure.get("rolling_20m_peak_drawdown_pct")
            ),
            "rolling_20m_low_rebound_pct": _number(
                structure.get("rolling_20m_low_rebound_pct")
            ),
            "bars_since_session_high": bars_since_session_high,
            "bars_since_session_low": _number(structure.get("bars_since_session_low")),
            "bars_since_20m_high": _number(structure.get("bars_since_20m_high")),
            "bars_since_20m_low": _number(structure.get("bars_since_20m_low")),
        },
        "execution_context": {
            "spread_bp": _number(liquidity.get("spread_bp")),
            "fillability_score": _number(liquidity.get("fillability_score")),
            "top1_ask_to_bid_ratio": _number(liquidity.get("top1_ask_to_bid_ratio")),
            "top3_ask_to_bid_ratio": top3_ratio,
            "volume_ratio": volume_ratio,
            "buy_pressure_pct": _number(tape.get("buy_pressure_pct")),
            "net_aggressive_delta_shares": _number(
                tape.get("net_aggressive_delta_shares")
            ),
            "program_net_qty": _number(program.get("net_qty")),
        },
        "family_memberships": family_memberships,
        "matched_families": sorted(
            family for family, matched in family_memberships.items() if matched
        ),
        "missing_fields": missing_fields,
        "family_boundaries_are_offline_research_only": True,
        "flow_match_authorizes_recheck_only": True,
        "micro_confirmation_required_for_enter": True,
        "future_outcome_fields_forbidden": True,
        "future_outcome_fields_used": False,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    return {
        **body,
        "flow_observation_sha256": _canonical_sha256(body),
    }


def micro_recovery_observation(features: Any) -> dict[str, Any]:
    """Observe tape plus price response; never infer fills or net profitability.

    Completed-bar trend and distance below VWAP are not a second trigger. The
    existing freshness flags remain authoritative; unknown flags fail closed.
    """
    values = _as_dict(features)
    delta = _number(values.get("net_aggressive_delta_10t"))
    response = _number(values.get("price_change_10t_pct"))
    source_ok = bool(
        values.get("tick_aggressor_pressure_usable") is True
        and values.get("tick_context_stale") is False
        and values.get("quote_stale") is False
        and values.get("large_sell_print_detected") is False
        and (_number(values.get("tick_aggressor_trusted_count")) or 0) >= 10
    )
    tape_support = bool(source_ok and delta is not None and delta > 0)
    return {
        "source_usable": source_ok,
        "tape_support": tape_support,
        "price_response": bool(source_ok and response is not None and response > 0),
        "net_aggressive_delta_10t": delta,
        "price_change_10t_pct": response,
    }


def _source_quality_status(value: Any) -> str:
    source = _as_dict(value)
    quality = source.get("quality")
    if isinstance(quality, dict):
        quality = quality.get("status")
    if quality in (None, ""):
        quality = source.get("source_quality")
        if isinstance(quality, dict):
            quality = quality.get("status")
    return str(quality or "unknown").strip().lower()


def _source_is_fresh(value: Any) -> bool:
    return _source_quality_status(value) in {
        "fresh",
        "fresh_consistent",
        "pass",
    }


def _has_observation_time(value: Any) -> bool:
    source = _as_dict(value)
    return source.get("observed_at") not in (None, "") or source.get(
        "captured_at"
    ) not in (None, "")


def _build_context_observations(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract null-aware relative-strength, flow, and external-risk inputs.

    Missing data remains explicit and never becomes a negative fact. Only
    fresh, same-payload observations can corroborate a bounded risk.
    """

    candle_context = _as_dict(payload.get("entry_candle_context"))
    multi = _as_dict(candle_context.get("multi_timeframe_context"))
    market = _as_dict(multi.get("market_context"))
    sector = _as_dict(multi.get("sector_context"))
    snapshot = _as_dict(payload.get("ai_market_snapshot_v1"))
    if not snapshot:
        snapshot = _as_dict(candle_context.get("ai_market_snapshot_v1"))
    sources = _as_dict(snapshot.get("sources"))

    stock_5m = _number(sector.get("stock_return_5m_pct"))
    stock_15m = _number(sector.get("stock_return_15m_pct"))
    market_5m = _number(market.get("return_5m_pct"))
    market_15m = _number(market.get("return_15m_pct"))
    market_relative_5m = (
        round(stock_5m - market_5m, 6)
        if stock_5m is not None and market_5m is not None
        else None
    )
    market_relative_15m = (
        round(stock_15m - market_15m, 6)
        if stock_15m is not None and market_15m is not None
        else None
    )
    market_relative_usable = bool(
        _source_is_fresh(market)
        and market_relative_5m is not None
        and market_relative_15m is not None
    )
    sector_relative_5m = _number(sector.get("sector_relative_return_5m_pct"))
    sector_relative_15m = _number(sector.get("sector_relative_return_15m_pct"))
    sector_relative_usable = bool(
        _source_is_fresh(sector)
        and sector_relative_5m is not None
        and sector_relative_15m is not None
    )

    program = _as_dict(sources.get("program"))
    program_value = _as_dict(program.get("value"))
    program_net_qty = _number(program_value.get("net_qty"))
    program_delta_qty = _number(program_value.get("delta_qty"))
    program_usable = bool(
        _source_is_fresh(program)
        and _has_observation_time(program)
        and program_net_qty is not None
    )

    investor = _as_dict(sources.get("investor"))
    investor_value = _as_dict(investor.get("value"))
    foreign_net = _number(investor_value.get("foreign_net"))
    institutional_net = _number(investor_value.get("inst_net"))
    investor_numbers = [foreign_net, institutional_net]
    investor_all_zero = bool(
        all(value is not None for value in investor_numbers)
        and all(value == 0.0 for value in investor_numbers)
    )
    investor_usable = bool(
        _source_is_fresh(investor)
        and _has_observation_time(investor)
        and all(value is not None for value in investor_numbers)
        and not investor_all_zero
    )

    runtime_context = _as_dict(payload.get("runtime_context"))
    external = _as_dict(payload.get("external_market_context"))
    if not external:
        external = _as_dict(runtime_context.get("external_market_context"))
    if not external:
        external_source = _as_dict(sources.get("external_market"))
        external = _as_dict(external_source.get("value"))
        if external:
            external = {
                **external,
                "source": external_source.get("source"),
                "quality": external_source.get("quality"),
                "observed_at": external_source.get("observed_at"),
            }
    external_risk_state = (
        str(external.get("risk_state") or external.get("state") or "unknown")
        .strip()
        .upper()
    )
    external_usable = bool(
        _source_is_fresh(external)
        and _has_observation_time(external)
        and external_risk_state != "UNKNOWN"
    )

    return {
        **CONTEXT_OBSERVATION_CONTRACT,
        "market_relative": {
            "status": "observed" if market_relative_usable else "unavailable",
            "usable_for_risk": market_relative_usable,
            "return_5m_pct_point": market_relative_5m,
            "return_15m_pct_point": market_relative_15m,
            "source": market.get("source"),
            "source_quality": _source_quality_status(market),
            "reason": market.get("reason"),
        },
        "sector_relative": {
            "status": "observed" if sector_relative_usable else "unavailable",
            "usable_for_risk": sector_relative_usable,
            "return_5m_pct_point": sector_relative_5m,
            "return_15m_pct_point": sector_relative_15m,
            "source": sector.get("source"),
            "source_quality": _source_quality_status(sector),
            "reason": sector.get("reason"),
        },
        "program_flow": {
            "status": "observed" if program_usable else "unavailable",
            "usable_for_risk": program_usable,
            "net_qty": program_net_qty,
            "delta_qty": program_delta_qty,
            "source": program.get("source"),
            "source_quality": _source_quality_status(program),
            "observed_at": program.get("observed_at"),
        },
        "investor_flow": {
            "status": (
                "observed"
                if investor_usable
                else (
                    "observed_zero_or_not_yet_reported"
                    if investor_all_zero
                    and _source_is_fresh(investor)
                    and _has_observation_time(investor)
                    else "unavailable"
                )
            ),
            "usable_for_risk": investor_usable,
            "foreign_net": foreign_net,
            "institutional_net": institutional_net,
            "source": investor.get("source"),
            "source_quality": _source_quality_status(investor),
            "observed_at": investor.get("observed_at"),
        },
        "external_market": {
            "status": "observed" if external_usable else "unavailable",
            "usable_for_risk": external_usable,
            "risk_state": external_risk_state,
            "source": external.get("source"),
            "source_quality": _source_quality_status(external),
            "observed_at": external.get("observed_at"),
        },
    }


def build_entry_setup_evidence(
    *,
    exact_payload: Any,
    exact_analysis: Any,
    recovery_analysis: Any,
    entry_timing_context: Any = None,
    timing_aware_policy: bool = False,
    balanced_policy: bool = False,
) -> dict[str, Any]:
    """Classify a symbol-agnostic setup from existing exact analysis ledgers."""

    timing_aware_policy = timing_aware_policy or balanced_policy
    payload = _as_dict(exact_payload)
    exact = _as_dict(exact_analysis)
    recovery = _as_dict(recovery_analysis)
    facts = _as_dict(exact.get("deterministic_contract_facts"))
    source_quality = _as_dict(exact.get("source_quality"))
    liquidity = _as_dict(exact.get("executable_liquidity"))
    tape = _as_dict(exact.get("tape_sample"))
    volume = _as_dict(exact.get("volume_confirmation"))
    clean = _as_dict(recovery.get("clean_continuation_probe"))
    recovery_confirmation = _as_dict(recovery.get("recovery_confirmation_probe"))
    hard_blockers = [str(value) for value in recovery.get("hard_blockers") or []]
    source_mode = str(recovery.get("source_mode") or "").strip().lower()
    source_status = str(source_quality.get("status") or "").strip().lower()
    completed_bar_count = int(source_quality.get("completed_bar_count") or 0)
    completed_structure = _as_dict(exact.get("completed_structure"))
    structure_phase = str(completed_structure.get("phase") or "").strip().lower()
    if structure_phase not in STRUCTURE_PHASES:
        if facts.get("orderly_pullback_recovery") is True:
            structure_phase = "pullback"
        elif (
            _as_dict(recovery.get("recovery_confirmation_probe")).get("eligible")
            is True
        ):
            structure_phase = "recovery_continuation"
        elif facts.get("structural_edge_floor") is True:
            structure_phase = "continuation"
        elif facts.get("early_session_probe_candidate") is True:
            structure_phase = "early_continuation_probe"
        else:
            structure_phase = "range_or_no_setup"
    phase_family = STRUCTURE_PHASE_FAMILIES.get(structure_phase, "NO_VALID_SETUP")
    stable_phase_fields = {
        key: completed_structure.get(key)
        for key in (
            "phase",
            "phase_policy_version",
            "phase_input_policy",
            "structural_edge",
            "returns_pct",
            "slopes_pct_per_bar",
            "peak_drawdown_pct",
            "rolling_20m_peak_drawdown_pct",
            "rolling_20m_low_rebound_pct",
            "bars_since_session_high",
            "bars_since_session_low",
            "bars_since_20m_high",
            "bars_since_20m_low",
            "high_direction",
            "low_direction",
            "regime",
            "alignment",
            "structural_edge_policy_version",
            "structural_edge_floor",
            "long_horizon_structural_edge_floor",
            "early_session_structural_edge_floor",
            "early_short_structure_floor",
            "adverse_distribution_no_edge",
        )
    }
    phase_source = {
        "completed_bar_count": completed_bar_count,
        "completed_structure": stable_phase_fields,
        "decision_window_end": _as_dict(
            _as_dict(
                _as_dict(payload.get("entry_candle_context")).get("source_quality")
            ).get("decision_window")
        ).get("end_timestamp"),
    }
    structure_phase_sha256 = _canonical_sha256(phase_source)

    positive_facts: list[str] = []
    contradicting_facts = [
        str(value) for value in exact.get("contradictions") or [] if value
    ]
    invalidation_facts: list[str] = []
    corroborated_risk_codes: list[str] = []
    recheck_reasons: list[str] = []
    context_observations = _build_context_observations(payload)
    micro = micro_recovery_observation(payload.get("features"))
    timing_observation = _entry_timing_observation(
        (
            entry_timing_context
            if entry_timing_context is not None
            else payload.get("entry_timing_context")
        ),
        completed_structure=completed_structure,
        balanced_policy=balanced_policy,
    )

    spread_bp = _number(liquidity.get("spread_bp"))
    fillability_score = _number(liquidity.get("fillability_score"))
    top3_ask_to_bid_ratio = _number(liquidity.get("top3_ask_to_bid_ratio"))
    tail_liquidity_fragility = bool(
        spread_bp is not None
        and spread_bp >= TAIL_RISK_SPREAD_FLOOR_BP
        and fillability_score is not None
        and fillability_score <= TAIL_RISK_FILLABILITY_CEILING
        and top3_ask_to_bid_ratio is not None
        and top3_ask_to_bid_ratio >= TAIL_RISK_TOP3_ASK_TO_BID_FLOOR
    )

    if facts.get("structural_edge_floor") is True:
        positive_facts.append("structural_edge_floor")
    if facts.get("early_session_structural_edge_floor") is True:
        positive_facts.append("early_session_structural_edge_floor")
    if facts.get("early_session_probe_candidate") is True:
        positive_facts.append("early_session_probe_candidate")
    if facts.get("orderly_pullback_recovery") is True:
        positive_facts.append("orderly_pullback_recovery")
    if facts.get("trusted_supportive_trigger") is True:
        positive_facts.append("trusted_supportive_trigger")
    if clean.get("eligible") is True:
        positive_facts.append("clean_continuation_probe_eligible")
    if recovery_confirmation.get("eligible") is True:
        positive_facts.append("recovery_confirmation_probe_eligible")
    if (
        str(tape.get("state") or "").lower() == "sufficient"
        and str(tape.get("raw_status") or "").lower() == "supportive"
    ):
        positive_facts.append("tape_supportive")
    elif str(tape.get("raw_status") or "").lower() == "adverse":
        contradicting_facts.append("tape_adverse")
        corroborated_risk_codes.append("ADVERSE_TAPE")
    if str(tape.get("state") or "").lower() == "too_thin":
        contradicting_facts.append("tape_sample_too_thin")
    liquidity_state = str(liquidity.get("state") or "").lower()
    if liquidity_state == "supportive":
        positive_facts.append("liquidity_supportive")
    elif liquidity_state in {"adverse", "blocking"}:
        contradicting_facts.append("liquidity_adverse")
    if str(volume.get("state") or "").lower() == "confirmed":
        positive_facts.append("volume_confirmed")
    elif str(volume.get("state") or "").lower() in {
        "confirmation_absent",
        "insufficient",
    }:
        contradicting_facts.append("volume_confirmation_missing")
        corroborated_risk_codes.append("CONFIRMATION_MISSING")
    trigger_state = str(exact.get("trigger_state") or "").lower()
    if trigger_state == "confirmed":
        positive_facts.append("trigger_confirmed")
    elif trigger_state in {
        "recovery_required",
        "unconfirmed",
        "insufficient_tape_confirmation",
    }:
        contradicting_facts.append("trigger_confirmation_missing")
        corroborated_risk_codes.append("CONFIRMATION_MISSING")

    # These auxiliary inputs can corroborate only a bounded CAUTION. They do
    # not create a setup, never turn missing data into a negative signal, and
    # cannot bypass the existing submit/post-probe safety owners.
    market_relative = _as_dict(context_observations.get("market_relative"))
    if (
        market_relative.get("usable_for_risk") is True
        and _number(market_relative.get("return_5m_pct_point"))
        <= RELATIVE_WEAKNESS_FLOOR_PCT_POINT
        and _number(market_relative.get("return_15m_pct_point"))
        <= RELATIVE_WEAKNESS_FLOOR_PCT_POINT
    ):
        contradicting_facts.append("market_relative_weak_5m_15m")
        corroborated_risk_codes.append("ADVERSE_TAPE")
    sector_relative = _as_dict(context_observations.get("sector_relative"))
    if (
        sector_relative.get("usable_for_risk") is True
        and _number(sector_relative.get("return_5m_pct_point"))
        <= RELATIVE_WEAKNESS_FLOOR_PCT_POINT
        and _number(sector_relative.get("return_15m_pct_point"))
        <= RELATIVE_WEAKNESS_FLOOR_PCT_POINT
    ):
        contradicting_facts.append("sector_relative_weak_5m_15m")
        corroborated_risk_codes.append("ADVERSE_TAPE")
    program_flow = _as_dict(context_observations.get("program_flow"))
    if (
        program_flow.get("usable_for_risk") is True
        and (_number(program_flow.get("net_qty")) or 0.0) < 0.0
        and (_number(program_flow.get("delta_qty")) or 0.0) < 0.0
    ):
        contradicting_facts.append("program_flow_net_and_delta_sell")
        corroborated_risk_codes.append("ADVERSE_TAPE")
    if "supportive_micro_tape_vs_program_net_sell" in contradicting_facts:
        corroborated_risk_codes.append("ADVERSE_TAPE")
    investor_flow = _as_dict(context_observations.get("investor_flow"))
    if (
        investor_flow.get("usable_for_risk") is True
        and (_number(investor_flow.get("foreign_net")) or 0.0) < 0.0
        and (_number(investor_flow.get("institutional_net")) or 0.0) < 0.0
    ):
        contradicting_facts.append("foreign_institutional_joint_sell")
        corroborated_risk_codes.append("ADVERSE_TAPE")
    external_market = _as_dict(context_observations.get("external_market"))
    if external_market.get("usable_for_risk") is True and str(
        external_market.get("risk_state") or ""
    ).upper() in {"RISK_OFF", "SEVERE", "HIGH_RISK"}:
        contradicting_facts.append("external_market_risk_off")
        corroborated_risk_codes.append("ADVERSE_TAPE")

    if balanced_policy:
        # Same freshness, units and paired observations as the adverse branch.
        # Correlated context corroborates a setup; it never creates one.
        for name, source in (("market", market_relative), ("sector", sector_relative)):
            if source.get("usable_for_risk") is True and all(
                (value := _number(source.get(key))) is not None
                and value >= -RELATIVE_WEAKNESS_FLOOR_PCT_POINT
                for key in ("return_5m_pct_point", "return_15m_pct_point")
            ):
                positive_facts.append(f"{name}_relative_strong_5m_15m")
        for source, keys, fact in (
            (program_flow, ("net_qty", "delta_qty"), "program_flow_net_and_delta_buy"),
            (
                investor_flow,
                ("foreign_net", "institutional_net"),
                "foreign_institutional_joint_buy",
            ),
        ):
            if source.get("usable_for_risk") is True and all(
                (value := _number(source.get(key))) is not None and value > 0
                for key in keys
            ):
                positive_facts.append(fact)
        if (
            external_market.get("usable_for_risk") is True
            and str(external_market.get("risk_state") or "").upper() == "RISK_ON"
        ):
            positive_facts.append("external_market_risk_on")

    analysis_schema_valid = bool(
        exact.get("schema") == "exact_payload_analysis_v1"
        and recovery.get("schema") == "anticipatory_reversal_analysis_v1"
    )
    if not analysis_schema_valid:
        invalidation_facts.append("analysis_schema_invalid")
        corroborated_risk_codes.append("SOURCE_QUALITY_GAP")
    if source_mode == "unusable" or source_status not in {
        "fresh_consistent",
        "pass",
    }:
        invalidation_facts.append("source_quality_unusable")
        corroborated_risk_codes.append("SOURCE_QUALITY_GAP")
    if completed_bar_count <= 0:
        invalidation_facts.append("completed_bars_missing")
        corroborated_risk_codes.append("SOURCE_QUALITY_GAP")
    if facts.get("adverse_distribution_no_edge") is True:
        invalidation_facts.append("adverse_distribution_no_edge")
        corroborated_risk_codes.append("DISTRIBUTION_RISK")
    if facts.get("blocking_overextension") is True:
        invalidation_facts.append("blocking_overextension")
        corroborated_risk_codes.append("OVEREXTENSION_CHASE")
    if facts.get("ask_wall_wide_spread") is True:
        contradicting_facts.append("ask_wall_wide_spread")
        corroborated_risk_codes.append("LIQUIDITY_FRAGILE")
    if (
        str(liquidity.get("execution_cost_state") or "").lower()
        == "extreme_or_unusable"
    ):
        invalidation_facts.append("liquidity_extreme_or_unusable")
        corroborated_risk_codes.append("LIQUIDITY_UNUSABLE")
    if hard_blockers:
        invalidation_facts.extend(f"hard_blocker:{value}" for value in hard_blockers)
        if "SOURCE_QUALITY_GAP" not in corroborated_risk_codes:
            corroborated_risk_codes.append("STRUCTURE_INVALIDATED")
    if tail_liquidity_fragility:
        contradicting_facts.append("tail_liquidity_fragility")
        corroborated_risk_codes.append("LIQUIDITY_FRAGILE")
    if timing_aware_policy:
        timing_state = str(timing_observation.get("state") or "")
        timing_fact_id = str(timing_observation.get("fact_id") or "")
        if (
            timing_state
            in {
                "late_unreset_extension",
                "repeated_repromotion_without_reset",
            }
            and timing_fact_id
        ):
            contradicting_facts.append(timing_fact_id)
            corroborated_risk_codes.append(
                "REWARD_RISK_WEAK" if balanced_policy else "OVEREXTENSION_CHASE"
            )
        elif timing_state == "late_but_reset_pullback" and timing_fact_id:
            positive_facts.append(timing_fact_id)

    source_usable = bool(
        payload
        and analysis_schema_valid
        and source_status in {"fresh_consistent", "pass"}
        and source_mode in {"fresh_dual", "degraded_but_bounded"}
        and completed_bar_count > 0
        and "source_quality_unusable" not in invalidation_facts
    )
    large_sell_recheck_eligible = bool(
        source_usable
        and phase_family != "NO_VALID_SETUP"
        and set(invalidation_facts) == {"hard_blocker:large_sell_print_present"}
        and facts.get("structural_edge_floor") is True
        and str(volume.get("state") or "").lower() == "confirmed"
        and not tail_liquidity_fragility
    )
    if not source_usable:
        setup_family = "NO_VALID_SETUP"
        setup_state = "INSUFFICIENT"
    elif large_sell_recheck_eligible:
        setup_family = phase_family
        setup_state = "WAIT_CONFIRMATION"
        recheck_reasons.append("LARGE_SELL_EXHAUSTION_RECHECK")
    elif invalidation_facts:
        setup_family = "NO_VALID_SETUP"
        setup_state = "INVALID"
    elif phase_family == "RECOVERY_CONFIRMATION" and (
        recovery_confirmation.get("eligible") is True
        or facts.get("trusted_supportive_trigger") is True
    ):
        setup_family = phase_family
        setup_state = "READY"
    elif phase_family == "RECOVERY_CONFIRMATION":
        setup_family = phase_family
        setup_state = "WAIT_CONFIRMATION"
    elif phase_family == "CLEAN_CONTINUATION" and (
        clean.get("eligible") is True or facts.get("trusted_supportive_trigger") is True
    ):
        setup_family = phase_family
        setup_state = "READY"
    elif (
        phase_family == "PULLBACK_RECOVERY"
        and facts.get("orderly_pullback_recovery") is True
    ):
        setup_family = "PULLBACK_RECOVERY"
        setup_state = (
            "READY"
            if facts.get("trusted_supportive_trigger") is True
            else "WAIT_CONFIRMATION"
        )
    elif phase_family == "CLEAN_CONTINUATION" and (
        facts.get("structural_edge_floor") is True
        or facts.get("early_session_probe_candidate") is True
    ):
        setup_family = phase_family
        setup_state = "WAIT_CONFIRMATION"
    elif phase_family in {"CLEAN_CONTINUATION", "PULLBACK_RECOVERY"}:
        setup_family = phase_family
        setup_state = "WAIT_CONFIRMATION"
    elif (
        structure_phase == "range_or_no_setup"
        and micro["tape_support"]
        and micro["price_response"]
        and liquidity_state == "supportive"
        and not tail_liquidity_fragility
    ):
        setup_family = "MICRO_RECOVERY"
        setup_state = "WAIT_CONFIRMATION"
        positive_facts.extend(
            ["micro_trusted_buy_flow", "micro_positive_price_response"]
        )
        contradicting_facts.append("micro_continuation_unconfirmed")
        corroborated_risk_codes.append("CONFIRMATION_MISSING")
        recheck_reasons.append("MICRO_PRICE_RESPONSE_RECHECK")
    else:
        setup_family = "NO_VALID_SETUP"
        setup_state = "UNCONFIRMED"
        contradicting_facts.append("no_supported_setup")
        corroborated_risk_codes.append("CONFIRMATION_MISSING")
        # Observation only: no inferred EDGE and no automatic probe. A changed
        # fresh snapshot must establish a setup before the submit owner runs.
        if micro["tape_support"] and liquidity_state == "supportive":
            recheck_reasons.append("SETUP_DISCOVERY_RECHECK")

    if setup_state == "WAIT_CONFIRMATION" and tail_liquidity_fragility:
        recheck_reasons.append("TAIL_LIQUIDITY_RECHECK")

    if (
        setup_state == "WAIT_CONFIRMATION"
        and not contradicting_facts
        and not invalidation_facts
    ):
        # WAIT_CONFIRMATION must carry the deterministic reason that the
        # risk-only adjudicator is allowed to cite. Blocker-driven WAIT rows
        # already cite their invalidation fact and must not fabricate a
        # missing trigger when the trigger was actually confirmed.
        contradicting_facts.append("trigger_confirmation_missing")
        corroborated_risk_codes.append("CONFIRMATION_MISSING")
    if setup_state == "WAIT_CONFIRMATION" and not recheck_reasons:
        recheck_reasons.append("TRIGGER_CONFIRMATION_RECHECK")

    evidence = {
        "schema": ENTRY_SETUP_EVIDENCE_SCHEMA,
        "version": (
            ENTRY_SETUP_BALANCED_EVIDENCE_VERSION
            if balanced_policy
            else (
                ENTRY_SETUP_TIMING_EVIDENCE_VERSION
                if timing_aware_policy
                else ENTRY_SETUP_EVIDENCE_VERSION
            )
        ),
        "setup_family": setup_family,
        "setup_state": setup_state,
        "structure_phase": structure_phase,
        "structure_phase_policy_version": STRUCTURE_PHASE_POLICY_VERSION,
        "structure_phase_sha256": structure_phase_sha256,
        "structure_phase_bar_end": phase_source["decision_window_end"],
        "structure_phase_stable_on_completed_bar": True,
        "structure_phase_role": "completed_bar_chart_flow_only",
        "execution_readiness_state": setup_state,
        "execution_readiness_role": "intrabar_tape_quote_risk_recheck",
        "positive_facts": _unique(positive_facts),
        "contradicting_facts": _unique(contradicting_facts),
        "invalidation_facts": _unique(invalidation_facts),
        "corroborated_risk_codes": _unique(corroborated_risk_codes),
        "recheck_reasons": _unique(recheck_reasons),
        "tail_risk_assessment": {
            **TAIL_RISK_OBSERVATION_CONTRACT,
            "state": (
                "elevated_depth_spread_fragility"
                if tail_liquidity_fragility
                else "not_observed"
            ),
            "inputs": {
                "spread_bp": spread_bp,
                "fillability_score": fillability_score,
                "top3_ask_to_bid_ratio": top3_ask_to_bid_ratio,
            },
        },
        "context_observations": context_observations,
        "micro_recovery_observation": micro,
        "source_quality": {
            "status": source_status or "unknown",
            "source_mode": source_mode or "unknown",
            "completed_bar_count": completed_bar_count,
        },
        "symbol_specific_branching": False,
        "widget_dependency": False,
        "observation_contract": dict(OBSERVATION_CONTRACT),
        "metric_role": OBSERVATION_CONTRACT["metric_role"],
        "decision_authority": OBSERVATION_CONTRACT["decision_authority"],
        "window_policy": OBSERVATION_CONTRACT["window_policy"],
        "sample_floor": OBSERVATION_CONTRACT["sample_floor"],
        "primary_decision_metric": OBSERVATION_CONTRACT["primary_decision_metric"],
        "source_quality_gate": OBSERVATION_CONTRACT["source_quality_gate"],
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "forbidden_uses": list(OBSERVATION_CONTRACT["forbidden_uses"]),
    }
    if timing_aware_policy:
        evidence[ENTRY_TIMING_OBSERVATION_SCHEMA] = timing_observation
    if balanced_policy:
        evidence["risk_fact_bindings"] = _risk_fact_bindings(evidence)
    evidence["evidence_sha256"] = _canonical_sha256(evidence)
    return evidence


def _risk_fact_bindings(setup: dict[str, Any]) -> dict[str, list[str]]:
    """Bind each emitted code to its exact adverse ledger facts, not prose."""

    def string_list(key):
        value = setup.get(key)
        return (
            [item for item in value if isinstance(item, str)]
            if isinstance(value, list)
            else []
        )

    adverse = set(string_list("contradicting_facts")) | set(
        string_list("invalidation_facts")
    )
    candidates = {
        "SOURCE_QUALITY_GAP": {
            "analysis_schema_invalid",
            "source_quality_unusable",
            "completed_bars_missing",
        },
        "STRUCTURE_INVALIDATED": {
            *{fact for fact in adverse if fact.startswith("hard_blocker:")},
            "no_supported_setup",
        },
        "DISTRIBUTION_RISK": {"adverse_distribution_no_edge"},
        "OVEREXTENSION_CHASE": {
            "blocking_overextension",
            "repeated_repromotion_without_reset",
            "late_unreset_entry_timing",
        },
        "LIQUIDITY_UNUSABLE": {
            "liquidity_extreme_or_unusable",
            "liquidity_adverse",
            "tail_liquidity_fragility",
        },
        "LIQUIDITY_FRAGILE": {
            "liquidity_adverse",
            "ask_wall_wide_spread",
            "tail_liquidity_fragility",
        },
        "ADVERSE_TAPE": {
            "tape_adverse",
            "market_relative_weak_5m_15m",
            "sector_relative_weak_5m_15m",
            "program_flow_net_and_delta_sell",
            "supportive_micro_tape_vs_program_net_sell",
            "foreign_institutional_joint_sell",
            "external_market_risk_off",
        },
        "REWARD_RISK_WEAK": {
            "late_unreset_entry_timing",
            "repeated_repromotion_without_reset",
            "reward_risk_weak",
        },
        "CONFIRMATION_MISSING": {
            "volume_confirmation_missing",
            "trigger_confirmation_missing",
            "micro_continuation_unconfirmed",
            "no_supported_setup",
            "tape_sample_too_thin",
        },
    }
    return {
        code: sorted(candidates.get(code, set()) & adverse)
        for code in string_list("corroborated_risk_codes")
    }


def entry_risk_adjudication_openai_schema(
    setup_evidence: Any = None,
) -> dict[str, Any]:
    """Return the V2.14 schema, optionally constrained to one setup ledger."""

    schema = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema",
            "risk_verdict",
            "risk_codes",
            "supporting_fact_ids",
            "contradicting_fact_ids",
            "confidence",
        ],
        "properties": {
            "schema": {
                "type": "string",
                "enum": [ENTRY_RISK_ADJUDICATION_SCHEMA],
            },
            "risk_verdict": {
                "type": "string",
                "enum": sorted(RISK_VERDICTS),
            },
            "risk_codes": {
                "type": "array",
                "minItems": 1,
                "maxItems": 6,
                "items": {"type": "string", "enum": sorted(RISK_CODES)},
            },
            "supporting_fact_ids": {
                "type": "array",
                "maxItems": 8,
                "items": {"type": "string"},
            },
            "contradicting_fact_ids": {
                "type": "array",
                "maxItems": 8,
                "items": {"type": "string"},
            },
            "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
        },
    }
    if setup_evidence is None:
        return schema

    setup = _as_dict(setup_evidence)
    invalidation_facts = list(setup.get("invalidation_facts") or [])
    contradicting_facts = list(setup.get("contradicting_facts") or [])
    setup_state = str(setup.get("setup_state") or "").strip().upper()
    fact_fields = {
        "supporting_fact_ids": list(setup.get("positive_facts") or []),
        "contradicting_fact_ids": (
            invalidation_facts
            if setup_state == "INVALID" and invalidation_facts
            else [*contradicting_facts, *invalidation_facts]
        ),
    }
    for response_field, raw_values in fact_fields.items():
        allowed_values = list(
            dict.fromkeys(
                str(value) for value in raw_values if isinstance(value, str) and value
            )
        )
        field_schema = schema["properties"][response_field]
        if allowed_values:
            field_schema["items"]["enum"] = allowed_values
            if response_field == "contradicting_fact_ids" and setup_state in {
                "INVALID",
                "WAIT_CONFIRMATION",
                "UNCONFIRMED",
            }:
                field_schema["minItems"] = 1
        else:
            field_schema["maxItems"] = 0
    return schema


def _comparative_recheck_reasons(setup: dict[str, Any]) -> set[str]:
    reasons = set(map(str, setup.get("recheck_reasons") or []))
    bindings = _risk_fact_bindings(setup)
    bounded_codes = set(bindings) - BLOCKING_VETO_RISK_CODES
    if "LIQUIDITY_FRAGILE" in bounded_codes:
        reasons.add(
            "TAIL_LIQUIDITY_RECHECK"
            if "tail_liquidity_fragility" in bindings["LIQUIDITY_FRAGILE"]
            else "MICRO_PRICE_RESPONSE_RECHECK"
        )
    if "ADVERSE_TAPE" in bounded_codes:
        reasons.add("MICRO_PRICE_RESPONSE_RECHECK")
    if "REWARD_RISK_WEAK" in bounded_codes:
        reasons.add("TIMING_RESET_RECHECK")
    if "CONFIRMATION_MISSING" in bounded_codes:
        reasons.add(
            "SETUP_DISCOVERY_RECHECK"
            if str(setup.get("setup_state") or "").upper() == "UNCONFIRMED"
            else "TRIGGER_CONFIRMATION_RECHECK"
        )
    return reasons & RECHECK_REASONS


def _required_counterweight_fact_ids(
    setup: dict[str, Any],
    *,
    risk_code: str,
    fact_id: str,
) -> list[str]:
    """Return present, risk-specific facts that may compensate one bounded risk."""

    positive_facts = set(map(str, setup.get("positive_facts") or []))
    micro = _as_dict(setup.get("micro_recovery_observation"))
    micro_counterweight = (
        ["micro_trusted_buy_flow", "micro_positive_price_response"]
        if micro.get("source_usable") is True
        and micro.get("tape_support") is True
        and micro.get("price_response") is True
        else []
    )
    if risk_code == "LIQUIDITY_FRAGILE":
        return (
            ["liquidity_supportive"] if "liquidity_supportive" in positive_facts else []
        )
    if risk_code == "ADVERSE_TAPE":
        return micro_counterweight
    if risk_code == "REWARD_RISK_WEAK":
        return (
            ["late_entry_reset_confirmed"]
            if "late_entry_reset_confirmed" in positive_facts
            else []
        )
    if risk_code == "CONFIRMATION_MISSING" and fact_id == "volume_confirmation_missing":
        return (
            [*micro_counterweight, "trigger_confirmed"]
            if micro_counterweight and "trigger_confirmed" in positive_facts
            else []
        )
    return []


def _required_counterweight_fact_ids_for_risk(
    setup: dict[str, Any],
    *,
    risk_code: str,
) -> list[str]:
    """Require every fact carried by one risk code to have a counterweight."""

    fact_ids = _risk_fact_bindings(setup).get(risk_code, [])
    if not fact_ids:
        return []
    per_fact = [
        _required_counterweight_fact_ids(
            setup,
            risk_code=risk_code,
            fact_id=fact_id,
        )
        for fact_id in fact_ids
    ]
    if any(not values for values in per_fact):
        return []
    return list(dict.fromkeys(fact for values in per_fact for fact in values))


def entry_action_counterweight_bindings(setup_evidence: Any) -> dict[str, Any]:
    """Bind each current risk fact to present facts allowed to compensate it."""

    setup = _as_dict(setup_evidence)
    rows = []
    for risk_code, fact_ids in sorted(_risk_fact_bindings(setup).items()):
        rows.append(
            {
                "risk_code": risk_code,
                "risk_fact_ids": fact_ids,
                "required_counterweight_fact_ids": (
                    _required_counterweight_fact_ids_for_risk(
                        setup,
                        risk_code=risk_code,
                    )
                ),
            }
        )
    result = {
        "schema": ENTRY_ACTION_COUNTERWEIGHT_BINDINGS_SCHEMA,
        "bindings": rows,
        "decision_authority": "offline_evidence_accountability_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    result["bindings_sha256"] = _canonical_sha256(result)
    return result


def validate_entry_action_counterweight_bindings(
    bindings: Any,
    *,
    setup_evidence: Any,
) -> list[str]:
    """Require the supplied counterweight ledger to match deterministic evidence."""

    supplied = _as_dict(bindings)
    expected = entry_action_counterweight_bindings(setup_evidence)
    if supplied != expected:
        return ["entry_action_counterweight_bindings_mismatch"]
    return []


def validate_mechanistic_entry_threshold_policy(policy: Any) -> list[str]:
    """Validate one offline-only threshold policy and its promotion floor."""

    value = _as_dict(policy)
    errors: list[str] = []
    expected_fields = {
        "schema",
        "version",
        "thresholds",
        "postclose_selection",
        "runtime_effect",
        "allowed_runtime_apply",
        "actual_order_submitted",
        "broker_order_forbidden",
    }
    if set(value) != expected_fields:
        errors.append("mechanistic_entry_threshold_policy_fields_invalid")
    if value.get("schema") != MECHANISTIC_ENTRY_THRESHOLD_POLICY_SCHEMA:
        errors.append("mechanistic_entry_threshold_policy_schema_invalid")
    if not str(value.get("version") or "").strip():
        errors.append("mechanistic_entry_threshold_policy_version_missing")

    thresholds = _as_dict(value.get("thresholds"))
    required_thresholds = {
        "minimum_micro_net_aggressive_delta_10t",
        "minimum_micro_price_change_10t_pct",
        "maximum_spread_bp",
        "minimum_fillability_score",
        "maximum_top3_ask_to_bid_ratio",
    }
    parsed_thresholds = {
        key: _number(thresholds.get(key)) for key in required_thresholds
    }
    if set(thresholds) != required_thresholds or any(
        number is None for number in parsed_thresholds.values()
    ):
        errors.append("mechanistic_entry_thresholds_invalid")
    elif (
        parsed_thresholds["minimum_micro_net_aggressive_delta_10t"] < 0
        or parsed_thresholds["minimum_micro_price_change_10t_pct"] < 0
        or parsed_thresholds["maximum_spread_bp"] <= 0
        or not 0 <= parsed_thresholds["minimum_fillability_score"] <= 100
        or parsed_thresholds["maximum_top3_ask_to_bid_ratio"] <= 0
    ):
        errors.append("mechanistic_entry_threshold_bounds_invalid")

    selection = _as_dict(value.get("postclose_selection"))
    expected_selection_fields = {
        "minimum_cost_adjusted_ev_pct",
        "require_positive_paired_ev_delta",
        "minimum_exposure_count",
        "minimum_unique_symbol_count",
        "minimum_independent_source_date_count",
        "require_bounded_probe_risk_budget_pass",
        "chronological_holdout_required",
    }
    minimum_ev = _number(selection.get("minimum_cost_adjusted_ev_pct"))
    if set(selection) != expected_selection_fields:
        errors.append("mechanistic_entry_postclose_selection_fields_invalid")
    if minimum_ev is None or minimum_ev < 0.10:
        errors.append("mechanistic_entry_net_ev_floor_invalid")
    for field, floor in (
        ("minimum_exposure_count", 10),
        ("minimum_unique_symbol_count", 3),
        ("minimum_independent_source_date_count", 2),
    ):
        count = selection.get(field)
        if isinstance(count, bool) or not isinstance(count, int) or count < floor:
            errors.append(f"mechanistic_entry_{field}_invalid")
    for field in (
        "require_positive_paired_ev_delta",
        "require_bounded_probe_risk_budget_pass",
        "chronological_holdout_required",
    ):
        if selection.get(field) is not True:
            errors.append(f"mechanistic_entry_{field}_invalid")

    if (
        value.get("runtime_effect") is not False
        or value.get("allowed_runtime_apply") is not False
        or value.get("actual_order_submitted") is not False
        or value.get("broker_order_forbidden") is not True
    ):
        errors.append("mechanistic_entry_offline_authority_invalid")
    return list(dict.fromkeys(errors))


def mechanistic_entry_action_core(
    setup_evidence: Any,
    *,
    policy: Any = None,
) -> dict[str, Any]:
    """Apply the deterministic action core without generation-schema coupling."""

    setup = _as_dict(setup_evidence)
    selected_policy = (
        MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1 if policy is None else _as_dict(policy)
    )
    policy_errors = validate_mechanistic_entry_threshold_policy(selected_policy)
    if policy_errors:
        raise ValueError(
            f"mechanistic_entry_threshold_policy_invalid:{','.join(policy_errors)}"
        )
    thresholds = _as_dict(selected_policy.get("thresholds"))

    bindings = _risk_fact_bindings(setup)
    micro = _as_dict(setup.get("micro_recovery_observation"))
    tail_inputs = _as_dict(_as_dict(setup.get("tail_risk_assessment")).get("inputs"))
    micro_delta = _number(micro.get("net_aggressive_delta_10t"))
    micro_price_change = _number(micro.get("price_change_10t_pct"))
    spread_bp = _number(tail_inputs.get("spread_bp"))
    fillability_score = _number(tail_inputs.get("fillability_score"))
    top3_ask_to_bid_ratio = _number(tail_inputs.get("top3_ask_to_bid_ratio"))
    micro_threshold_pass = bool(
        micro.get("source_usable") is True
        and micro_delta is not None
        and micro_delta >= float(thresholds["minimum_micro_net_aggressive_delta_10t"])
        and micro_price_change is not None
        and micro_price_change > float(thresholds["minimum_micro_price_change_10t_pct"])
    )
    liquidity_threshold_pass = bool(
        spread_bp is not None
        and spread_bp < float(thresholds["maximum_spread_bp"])
        and fillability_score is not None
        and fillability_score > float(thresholds["minimum_fillability_score"])
        and top3_ask_to_bid_ratio is not None
        and top3_ask_to_bid_ratio < float(thresholds["maximum_top3_ask_to_bid_ratio"])
    )
    assessments = []
    for risk_code, fact_ids in sorted(bindings.items()):
        if not fact_ids:
            raise ValueError(f"mechanistic_risk_fact_binding_missing:{risk_code}")
        counterweights = _required_counterweight_fact_ids_for_risk(
            setup,
            risk_code=risk_code,
        )
        if risk_code in {"ADVERSE_TAPE", "CONFIRMATION_MISSING"} and not (
            micro_threshold_pass
        ):
            counterweights = []
        if risk_code == "LIQUIDITY_FRAGILE" and not liquidity_threshold_pass:
            counterweights = []
        blocking = risk_code in BLOCKING_VETO_RISK_CODES
        disposition = (
            "BLOCKING"
            if blocking
            else "COMPENSATED" if counterweights else "RECHECKABLE"
        )
        assessments.append(
            {
                "risk_code": risk_code,
                "fact_id": fact_ids[0],
                "disposition": disposition,
                "counterweight_fact_ids": (
                    counterweights if disposition == "COMPENSATED" else []
                ),
            }
        )

    state = str(setup.get("setup_state") or "INSUFFICIENT").upper()
    dispositions = {row["disposition"] for row in assessments}
    if state in {"INVALID", "INSUFFICIENT"} or "BLOCKING" in dispositions:
        action = "BLOCK"
    elif state == "READY" and dispositions <= {"COMPENSATED"}:
        action = "ENTER_NOW"
    else:
        action = "RECHECK"
    reasons = _comparative_recheck_reasons(setup)
    reason_priority = (
        "TAIL_LIQUIDITY_RECHECK",
        "TIMING_RESET_RECHECK",
        "MICRO_PRICE_RESPONSE_RECHECK",
        "TRIGGER_CONFIRMATION_RECHECK",
        "SETUP_DISCOVERY_RECHECK",
        "LARGE_SELL_EXHAUSTION_RECHECK",
    )
    reason = next((value for value in reason_priority if value in reasons), "NONE")
    opportunity_priority = (
        "structural_edge_floor",
        "early_session_structural_edge_floor",
        "orderly_pullback_recovery",
        "clean_continuation_probe_eligible",
        "recovery_confirmation_probe_eligible",
        "trusted_supportive_trigger",
        "trigger_confirmed",
        "micro_trusted_buy_flow",
        "micro_positive_price_response",
        "tape_supportive",
        "liquidity_supportive",
        "volume_confirmed",
    )
    positive = set(map(str, setup.get("positive_facts") or []))
    opportunity = [fact for fact in opportunity_priority if fact in positive][:8]
    response = {
        "schema": ENTRY_ACTION_COUNTERWEIGHT_COMPARISON_SCHEMA,
        "preferred_action": action,
        "opportunity_fact_ids": opportunity,
        "risk_assessments": assessments,
        "recheck_reason": reason if action == "RECHECK" else "NONE",
        "recheck_value_vs_opportunity_decay": {
            "ENTER_NOW": "ENTER_NOW_DOMINANT",
            "RECHECK": "RECHECK_DOMINANT",
            "BLOCK": "NOT_APPLICABLE_BLOCKED",
        }[action],
        "confidence": 100,
    }
    return response


def mechanistic_entry_action_comparison(
    setup_evidence: Any,
    *,
    policy: Any = None,
) -> dict[str, Any]:
    """Apply and fully validate a deterministic offline comparison."""

    setup = _as_dict(setup_evidence)
    response = mechanistic_entry_action_core(setup, policy=policy)
    errors = validate_entry_action_comparison(response, setup_evidence=setup)
    if errors:
        raise ValueError(f"mechanistic_entry_comparison_invalid:{','.join(errors)}")
    return response


def mechanistic_entry_policy_decision(
    setup_evidence: Any,
    *,
    policy: Any = None,
) -> dict[str, Any]:
    """Return the threshold-bound deterministic action shared by R1 and live."""

    setup = _as_dict(setup_evidence)
    selected_policy = (
        MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1 if policy is None else _as_dict(policy)
    )
    policy_errors = validate_mechanistic_entry_threshold_policy(selected_policy)
    if policy_errors:
        raise ValueError(
            f"mechanistic_entry_threshold_policy_invalid:{','.join(policy_errors)}"
        )
    comparison = mechanistic_entry_action_core(setup, policy=selected_policy)
    thresholds = _as_dict(selected_policy.get("thresholds"))
    tail_inputs = _as_dict(_as_dict(setup.get("tail_risk_assessment")).get("inputs"))
    observed = {
        "spread_bp": _number(tail_inputs.get("spread_bp")),
        "fillability_score": _number(tail_inputs.get("fillability_score")),
        "top3_ask_to_bid_ratio": _number(tail_inputs.get("top3_ask_to_bid_ratio")),
    }
    liquidity_complete = all(value is not None for value in observed.values())
    liquidity_pass = bool(
        liquidity_complete
        and observed["spread_bp"] < float(thresholds["maximum_spread_bp"])
        and observed["fillability_score"]
        > float(thresholds["minimum_fillability_score"])
        and observed["top3_ask_to_bid_ratio"]
        < float(thresholds["maximum_top3_ask_to_bid_ratio"])
    )
    core_action = str(comparison.get("preferred_action") or "BLOCK").upper()
    if core_action == "BLOCK":
        action = "BLOCK"
        reason = "mechanistic_hard_or_source_block"
    elif core_action == "RECHECK":
        action = "RECHECK"
        reason = str(comparison.get("recheck_reason") or "MECHANISTIC_RECHECK")
    elif not liquidity_complete:
        action = "RECHECK"
        reason = "MECHANISTIC_LIQUIDITY_INPUT_RECHECK"
    elif not liquidity_pass:
        action = "RECHECK"
        reason = "MECHANISTIC_LIQUIDITY_THRESHOLD_RECHECK"
    else:
        action = "ENTER_NOW"
        reason = "MECHANISTIC_SETUP_AND_THRESHOLD_PASS"
    return {
        "schema": MECHANISTIC_POLICY_DECISION_SCHEMA,
        "action": action,
        "reason": reason,
        "core_comparison": comparison,
        "liquidity_inputs": observed,
        "liquidity_inputs_complete": liquidity_complete,
        "liquidity_threshold_pass": liquidity_pass,
        "policy_version": selected_policy.get("version"),
        "primary_decision_owner": MECHANISTIC_PRIMARY_DECISION_OWNER,
        "ai_role": MECHANISTIC_AI_ADVISORY_ROLE,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def validate_mechanistic_risk_screen(
    response: Any, *, setup_evidence: Any
) -> list[str]:
    """Validate a binding second opinion, without changing legacy AI owners.

    Bounded execution/tape/reward risks can justify rejecting a machine point,
    but missing confirmation alone cannot. Existing fact bindings and source
    validity still apply. The screen must also acknowledge positive evidence.
    """
    errors = validate_entry_risk_adjudication(response, setup_evidence=setup_evidence)
    risk = _as_dict(response)
    codes = (
        set(map(str, risk["risk_codes"]))
        if isinstance(risk.get("risk_codes"), list)
        else set()
    )
    if (
        risk.get("risk_verdict") == "VETO"
        and codes & {"LIQUIDITY_FRAGILE", "ADVERSE_TAPE", "REWARD_RISK_WEAK"}
        and risk.get("supporting_fact_ids")
    ):
        errors = [e for e in errors if e != "entry_risk_veto_requires_blocking_risk"]
    return errors


def compose_mechanistic_primary_decision(
    *,
    setup_evidence: Any,
    ai_risk_adjudication: Any = None,
    policy: Any = None,
) -> dict[str, Any]:
    """Machine selects points; validated AI PASS/VETO screens exposure.

    Only PASS can preserve ENTER_NOW. Missing/malformed/CAUTION responses are
    non-exposure rechecks, never implicit PASS or probe permission. AI cannot
    promote a machine RECHECK/BLOCK or override final execution guards.
    """

    setup = _as_dict(setup_evidence)
    policy_decision = mechanistic_entry_policy_decision(setup, policy=policy)
    comparison = policy_decision["core_comparison"]
    result = compose_entry_action_comparison(
        setup_evidence=setup,
        action_comparison=comparison,
    )
    advisory = _as_dict(ai_risk_adjudication)
    advisory_errors = (
        validate_mechanistic_risk_screen(advisory, setup_evidence=setup)
        if advisory
        else ["ai_advisory_not_available"]
    )
    advisory_verdict = str(advisory.get("risk_verdict") or "UNAVAILABLE").upper()
    mechanistic_action = str(policy_decision.get("action") or "BLOCK").upper()
    if mechanistic_action != "ENTER_NOW":
        result.update(
            action="WAIT" if mechanistic_action == "RECHECK" else "DROP",
            score=70 if mechanistic_action == "RECHECK" else 0,
            reason=str(policy_decision.get("reason") or "")[:120],
            edge_state="EDGE" if mechanistic_action == "RECHECK" else "NO_EDGE",
            entry_composed_action=(
                "WAIT" if mechanistic_action == "RECHECK" else "DROP"
            ),
            entry_composed_reason=str(policy_decision.get("reason") or "")[:120],
            entry_probe_intent=False,
            entry_probe_intent_status="not_eligible",
            entry_recheck_intent=mechanistic_action == "RECHECK",
            entry_recheck_reasons=(
                [str(policy_decision.get("reason"))]
                if mechanistic_action == "RECHECK"
                else []
            ),
            entry_recheck_intent_status=(
                "eligible_next_scanner_loop_recheck"
                if mechanistic_action == "RECHECK"
                else "not_eligible"
            ),
        )
    advisory_direction = {
        "PASS": "ENTER_NOW",
        "CAUTION": "RECHECK",
        "VETO": "BLOCK",
        "INSUFFICIENT": "RECHECK",
    }.get(advisory_verdict, "UNAVAILABLE")
    screen_required = mechanistic_action == "ENTER_NOW"
    screen_status = "not_requested_machine_nonentry"
    if screen_required:
        screen_status = (
            "response_invalid" if advisory_errors else advisory_verdict.lower()
        )
        if advisory_errors or advisory_verdict != "PASS":
            veto = not advisory_errors and advisory_verdict == "VETO"
            screened_action = "DROP" if veto else "WAIT"
            reason = "entry_ai_screen_" + screen_status
            result.update(
                action=screened_action,
                score=0 if veto else 50,
                reason=reason,
                edge_state="EDGE",
                entry_composed_action=screened_action,
                entry_composed_reason=reason,
                entry_probe_intent=False,
                entry_probe_intent_status="ai_screen_no_exposure",
                entry_recheck_intent=not veto,
                entry_recheck_reasons=[] if veto else ["MICRO_PRICE_RESPONSE_RECHECK"],
                entry_recheck_intent_status=(
                    "not_eligible" if veto else "eligible_next_scanner_loop_recheck"
                ),
            )
    role_contract = dict(MECHANISTIC_PRIMARY_ROLE_CONTRACT)
    result.update(
        {
            "primary_schema": MECHANISTIC_PRIMARY_DECISION_SCHEMA,
            "entry_primary_decision_owner": MECHANISTIC_PRIMARY_DECISION_OWNER,
            "entry_ai_role": MECHANISTIC_AI_ADVISORY_ROLE,
            "entry_decision_role_contract": role_contract,
            "entry_mechanistic_action": mechanistic_action,
            "entry_mechanistic_policy_decision": policy_decision,
            "entry_mechanistic_policy_version": (
                _as_dict(
                    MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1 if policy is None else policy
                ).get("version")
            ),
            "entry_ai_advisory_verdict": advisory_verdict,
            "entry_ai_advisory_contract_valid": not advisory_errors,
            "entry_ai_advisory_contract_errors": advisory_errors,
            "entry_ai_advisory_direction": advisory_direction,
            "entry_ai_advisory_agrees_with_mechanistic": (
                advisory_direction == mechanistic_action if advisory else None
            ),
            "entry_ai_advisory_changed_action": (
                screen_required and screen_status != "pass"
            ),
            "entry_ai_screen_status": screen_status,
            "entry_ai_screen_required": screen_required,
            "entry_ai_screen_pass": screen_required and screen_status == "pass",
            "entry_ai_risk_verdict": advisory_verdict,
            "entry_ai_risk_codes": (
                list(advisory.get("risk_codes") or [])
                if isinstance(advisory.get("risk_codes"), list)
                else []
            ),
            "entry_ai_veto_corroborated": screen_required and screen_status == "veto",
            "entry_ai_contract_valid": not advisory_errors if screen_required else True,
            "entry_ai_contract_errors": advisory_errors if screen_required else [],
            "entry_final_execution_authority": (
                "existing_runtime_submit_and_order_guards"
            ),
        }
    )
    result.pop("composer_sha256", None)
    result["composer_sha256"] = _canonical_sha256(result)
    return result


def entry_action_comparison_openai_schema(
    setup_evidence: Any = None,
    *,
    counterweight_bound: bool = False,
) -> dict[str, Any]:
    """Return the comparative action schema constrained to one evidence ledger."""

    comparison_schema = (
        ENTRY_ACTION_COUNTERWEIGHT_COMPARISON_SCHEMA
        if counterweight_bound
        else ENTRY_ACTION_COMPARISON_SCHEMA
    )
    assessment_required = ["risk_code", "fact_id", "disposition"]
    assessment_properties = {
        "risk_code": {
            "type": "string",
            "enum": sorted(RISK_CODES - {"NO_BLOCKING_RISK"}),
        },
        "fact_id": {"type": "string"},
        "disposition": {
            "type": "string",
            "enum": sorted(COMPARATIVE_RISK_DISPOSITIONS),
        },
    }
    if counterweight_bound:
        assessment_required.append("counterweight_fact_ids")
        assessment_properties["counterweight_fact_ids"] = {
            "type": "array",
            "maxItems": 4,
            "items": {"type": "string"},
        }
    schema = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema",
            "preferred_action",
            "opportunity_fact_ids",
            "risk_assessments",
            "recheck_reason",
            "recheck_value_vs_opportunity_decay",
            "confidence",
        ],
        "properties": {
            "schema": {
                "type": "string",
                "enum": [comparison_schema],
            },
            "preferred_action": {
                "type": "string",
                "enum": sorted(COMPARATIVE_ENTRY_ACTIONS),
            },
            "opportunity_fact_ids": {
                "type": "array",
                "maxItems": 8,
                "items": {"type": "string"},
            },
            "risk_assessments": {
                "type": "array",
                "maxItems": 10,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": assessment_required,
                    "properties": assessment_properties,
                },
            },
            "recheck_reason": {
                "type": "string",
                "enum": ["NONE", *sorted(RECHECK_REASONS)],
            },
            "recheck_value_vs_opportunity_decay": {
                "type": "string",
                "enum": sorted(COMPARATIVE_RECHECK_TRADEOFFS),
            },
            "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
        },
    }
    if setup_evidence is None:
        return schema

    setup = _as_dict(setup_evidence)
    state = str(setup.get("setup_state") or "").upper()
    bindings = _risk_fact_bindings(setup)
    allowed_actions = (
        ["ENTER_NOW"]
        if state == "READY" and not bindings
        else (
            ["ENTER_NOW", "RECHECK"]
            if state == "READY"
            else (
                ["RECHECK"]
                if state in {"WAIT_CONFIRMATION", "UNCONFIRMED"}
                else ["BLOCK"]
            )
        )
    )
    schema["properties"]["preferred_action"]["enum"] = allowed_actions
    positive_facts = list(
        dict.fromkeys(
            str(value)
            for value in setup.get("positive_facts") or []
            if isinstance(value, str) and value
        )
    )
    opportunity_schema = schema["properties"]["opportunity_fact_ids"]
    if positive_facts:
        opportunity_schema["items"]["enum"] = positive_facts
    else:
        opportunity_schema["maxItems"] = 0
    assessment_schema = schema["properties"]["risk_assessments"]
    if bindings:
        assessment_schema["minItems"] = len(bindings)
        assessment_schema["maxItems"] = len(bindings)
        assessment_schema["items"]["properties"]["risk_code"]["enum"] = sorted(bindings)
        assessment_schema["items"]["properties"]["fact_id"]["enum"] = sorted(
            {fact for facts in bindings.values() for fact in facts}
        )
        if counterweight_bound:
            bound = entry_action_counterweight_bindings(setup)
            counterweight_ids = sorted(
                {
                    fact
                    for row in bound["bindings"]
                    for fact in row["required_counterweight_fact_ids"]
                }
            )
            if counterweight_ids:
                assessment_schema["items"]["properties"]["counterweight_fact_ids"][
                    "items"
                ]["enum"] = counterweight_ids
            else:
                assessment_schema["items"]["properties"]["counterweight_fact_ids"][
                    "maxItems"
                ] = 0
    else:
        assessment_schema["maxItems"] = 0
    reasons = sorted(_comparative_recheck_reasons(setup))
    schema["properties"]["recheck_reason"]["enum"] = ["NONE", *reasons]
    return schema


def validate_entry_setup_evidence(evidence: Any) -> list[str]:
    """Validate the deterministic ledger before AI output can be composed."""

    setup = _as_dict(evidence)
    errors: list[str] = []
    if setup.get("schema") != ENTRY_SETUP_EVIDENCE_SCHEMA:
        errors.append("entry_setup_evidence_schema_invalid")
    evidence_version = setup.get("version")
    if evidence_version not in {
        ENTRY_SETUP_EVIDENCE_VERSION,
        ENTRY_SETUP_TIMING_EVIDENCE_VERSION,
        ENTRY_SETUP_BALANCED_EVIDENCE_VERSION,
    }:
        errors.append("entry_setup_evidence_version_invalid")
    balanced_policy = evidence_version == ENTRY_SETUP_BALANCED_EVIDENCE_VERSION
    if balanced_policy:
        bindings = _risk_fact_bindings(setup)
        if setup.get("risk_fact_bindings") != bindings or any(
            not facts for facts in bindings.values()
        ):
            errors.append("entry_setup_risk_fact_bindings_invalid")
    if evidence_version in {
        ENTRY_SETUP_TIMING_EVIDENCE_VERSION,
        ENTRY_SETUP_BALANCED_EVIDENCE_VERSION,
    }:
        timing = _as_dict(setup.get(ENTRY_TIMING_OBSERVATION_SCHEMA))
        if (
            timing.get("schema") != ENTRY_TIMING_OBSERVATION_SCHEMA
            or timing.get("version") != ENTRY_TIMING_POLICY_VERSION
            or timing.get("state")
            not in {
                "insufficient",
                "early_or_unextended",
                "late_but_reset_pullback",
                "late_unreset_extension",
                "repeated_repromotion_without_reset",
            }
            or timing.get("age_only_never_adverse") is not True
            or timing.get("missing_timing_never_adverse") is not True
            or timing.get("runtime_effect") is not False
            or timing.get("allowed_runtime_apply") is not False
            or timing.get("actual_order_submitted") is not False
            or timing.get("broker_order_forbidden") is not True
        ):
            errors.append("entry_setup_timing_observation_contract_invalid")
        timing_state = str(timing.get("state") or "")
        expected_fact = {
            "late_but_reset_pullback": "late_entry_reset_confirmed",
            "late_unreset_extension": "late_unreset_entry_timing",
            "repeated_repromotion_without_reset": (
                "repeated_repromotion_without_reset"
            ),
        }.get(timing_state)
        if timing.get("fact_id") != expected_fact:
            errors.append("entry_setup_timing_fact_invalid")
        if timing_state in {
            "late_unreset_extension",
            "repeated_repromotion_without_reset",
        } and (
            expected_fact not in (setup.get("contradicting_facts") or [])
            or ("REWARD_RISK_WEAK" if balanced_policy else "OVEREXTENSION_CHASE")
            not in (setup.get("corroborated_risk_codes") or [])
        ):
            errors.append("entry_setup_timing_risk_projection_invalid")
        if timing_state == "late_but_reset_pullback" and expected_fact not in (
            setup.get("positive_facts") or []
        ):
            errors.append("entry_setup_timing_reset_projection_invalid")
    if setup.get("setup_family") not in SETUP_FAMILIES:
        errors.append("entry_setup_family_invalid")
    if setup.get("setup_state") not in SETUP_STATES:
        errors.append("entry_setup_state_invalid")
    if setup.get("structure_phase") not in STRUCTURE_PHASES:
        errors.append("entry_setup_structure_phase_invalid")
    if setup.get("structure_phase_policy_version") != STRUCTURE_PHASE_POLICY_VERSION:
        errors.append("entry_setup_structure_phase_policy_invalid")
    if setup.get("structure_phase_stable_on_completed_bar") is not True:
        errors.append("entry_setup_structure_phase_stability_contract_invalid")
    if setup.get("structure_phase_role") != "completed_bar_chart_flow_only":
        errors.append("entry_setup_structure_phase_role_invalid")
    if setup.get("execution_readiness_state") != setup.get("setup_state"):
        errors.append("entry_setup_execution_readiness_state_invalid")
    if setup.get("execution_readiness_role") != "intrabar_tape_quote_risk_recheck":
        errors.append("entry_setup_execution_readiness_role_invalid")
    if (
        not isinstance(setup.get("structure_phase_sha256"), str)
        or len(setup.get("structure_phase_sha256")) != 64
    ):
        errors.append("entry_setup_structure_phase_sha256_invalid")
    if (
        setup.get("setup_family") == "NO_VALID_SETUP"
        and setup.get("setup_state") not in {"INVALID", "INSUFFICIENT", "UNCONFIRMED"}
    ) or (
        setup.get("setup_family") in SETUP_FAMILIES - {"NO_VALID_SETUP"}
        and setup.get("setup_state") in {"INVALID", "INSUFFICIENT", "UNCONFIRMED"}
    ):
        errors.append("entry_setup_family_state_inconsistent")
    expected_phase_family = STRUCTURE_PHASE_FAMILIES.get(
        setup.get("structure_phase"), "NO_VALID_SETUP"
    )
    if setup.get("setup_family") not in {"NO_VALID_SETUP", "MICRO_RECOVERY"} and (
        setup.get("setup_family") != expected_phase_family
    ):
        errors.append("entry_setup_structure_phase_family_inconsistent")
    if setup.get("setup_family") == "MICRO_RECOVERY":
        micro = _as_dict(setup.get("micro_recovery_observation"))
        if (
            setup.get("setup_state") != "WAIT_CONFIRMATION"
            or setup.get("structure_phase") != "range_or_no_setup"
            or not all(
                micro.get(key) is True
                for key in ("source_usable", "tape_support", "price_response")
            )
            or not all(
                (value := _number(micro.get(key))) is not None and value > 0
                for key in ("net_aggressive_delta_10t", "price_change_10t_pct")
            )
            or setup.get("invalidation_facts")
            or not {
                "micro_trusted_buy_flow",
                "micro_positive_price_response",
                "liquidity_supportive",
            }.issubset(setup.get("positive_facts") or [])
            or setup.get("recheck_reasons") != ["MICRO_PRICE_RESPONSE_RECHECK"]
        ):
            errors.append("entry_setup_micro_recovery_contract_invalid")
    for field in (
        "positive_facts",
        "contradicting_facts",
        "invalidation_facts",
        "corroborated_risk_codes",
        "recheck_reasons",
    ):
        values = setup.get(field)
        if (
            not isinstance(values, list)
            or any(not isinstance(value, str) or not value for value in values)
            or len(values) != len(set(values))
        ):
            errors.append(f"entry_setup_{field}_invalid")
    if any(
        str(code) not in RISK_CODES
        for code in setup.get("corroborated_risk_codes") or []
    ):
        errors.append("entry_setup_corroborated_risk_code_unknown")
    recheck_reasons = set(map(str, setup.get("recheck_reasons") or []))
    if not recheck_reasons.issubset(RECHECK_REASONS):
        errors.append("entry_setup_recheck_reason_unknown")
    if setup.get("setup_state") == "WAIT_CONFIRMATION" and not recheck_reasons:
        errors.append("entry_setup_wait_recheck_reason_missing")
    if (
        setup.get("setup_state") not in {"WAIT_CONFIRMATION", "UNCONFIRMED"}
        and recheck_reasons
    ):
        errors.append("entry_setup_recheck_reason_state_inconsistent")
    if setup.get("setup_state") == "UNCONFIRMED" and (
        setup.get("invalidation_facts")
        or "no_supported_setup" not in (setup.get("contradicting_facts") or [])
        or not recheck_reasons.issubset({"SETUP_DISCOVERY_RECHECK"})
    ):
        errors.append("entry_setup_unconfirmed_contract_invalid")
    tail_assessment = _as_dict(setup.get("tail_risk_assessment"))
    for field, expected in TAIL_RISK_OBSERVATION_CONTRACT.items():
        if tail_assessment.get(field) != expected:
            errors.append(f"entry_setup_tail_risk_{field}_contract_invalid")
    tail_state = str(tail_assessment.get("state") or "")
    if tail_state not in {"not_observed", "elevated_depth_spread_fragility"}:
        errors.append("entry_setup_tail_risk_state_invalid")
    if "TAIL_LIQUIDITY_RECHECK" in recheck_reasons and tail_state != (
        "elevated_depth_spread_fragility"
    ):
        errors.append("entry_setup_tail_recheck_without_fragility")
    if (
        "LARGE_SELL_EXHAUSTION_RECHECK" in recheck_reasons
        and "hard_blocker:large_sell_print_present"
        not in set(map(str, setup.get("invalidation_facts") or []))
    ):
        errors.append("entry_setup_large_sell_recheck_without_blocker")
    if (
        "TRIGGER_CONFIRMATION_RECHECK" in recheck_reasons
        and "trigger_confirmation_missing"
        not in set(map(str, setup.get("contradicting_facts") or []))
    ):
        errors.append("entry_setup_trigger_recheck_without_missing_confirmation")
    context_observations = _as_dict(setup.get("context_observations"))
    for field, expected in CONTEXT_OBSERVATION_CONTRACT.items():
        if context_observations.get(field) != expected:
            errors.append(f"entry_setup_context_{field}_contract_invalid")
    for source_name in (
        "market_relative",
        "sector_relative",
        "program_flow",
        "investor_flow",
        "external_market",
    ):
        source = _as_dict(context_observations.get(source_name))
        if source.get("status") not in {
            "observed",
            "observed_zero_or_not_yet_reported",
            "unavailable",
        } or not isinstance(source.get("usable_for_risk"), bool):
            errors.append(f"entry_setup_context_{source_name}_invalid")
    group_observation = setup.get(ENTRY_GROUP_OBSERVATION_SCHEMA)
    if group_observation is not None:
        group = _as_dict(group_observation)
        group_body = {
            key: value
            for key, value in group.items()
            if key != "group_observation_sha256"
        }
        key_parts = _as_dict(group.get("key_parts"))
        required_group_parts = {
            "price_tick_band",
            "liquidity_band",
            "volatility_band",
            "structure_phase",
            "watch_age_band",
            "extension_band",
            "venue",
            "session_bucket",
        }
        if (
            group.get("schema") != ENTRY_GROUP_OBSERVATION_SCHEMA
            or set(key_parts) != required_group_parts
            or group.get("group_key") != "|".join(key_parts.values())
            or group.get("group_observation_sha256") != _canonical_sha256(group_body)
            or group.get("feature_time_boundary")
            != "decision_time_or_completed_bar_only"
            or group.get("future_outcome_fields_forbidden") is not True
            or group.get("symbol_specific_threshold_active") is not False
            or group.get("runtime_effect") is not False
            or group.get("allowed_runtime_apply") is not False
            or group.get("actual_order_submitted") is not False
            or group.get("broker_order_forbidden") is not True
        ):
            errors.append("entry_setup_group_observation_contract_invalid")
    if (
        setup.get("runtime_effect") is not False
        or setup.get("allowed_runtime_apply") is not False
        or setup.get("actual_order_submitted") is not False
        or setup.get("broker_order_forbidden") is not True
        or setup.get("symbol_specific_branching") is not False
        or setup.get("widget_dependency") is not False
    ):
        errors.append("entry_setup_authority_contract_invalid")
    if setup.get("observation_contract") != OBSERVATION_CONTRACT:
        errors.append("entry_setup_observation_contract_invalid")
    for field in (
        "metric_role",
        "decision_authority",
        "window_policy",
        "sample_floor",
        "primary_decision_metric",
        "source_quality_gate",
        "forbidden_uses",
    ):
        if setup.get(field) != OBSERVATION_CONTRACT[field]:
            errors.append(f"entry_setup_{field}_contract_invalid")
    evidence_sha256 = str(setup.get("evidence_sha256") or "")
    if not evidence_sha256 or evidence_sha256 != _canonical_sha256(
        {key: value for key, value in setup.items() if key != "evidence_sha256"}
    ):
        errors.append("entry_setup_evidence_sha256_invalid")
    return list(dict.fromkeys(errors))


def validate_entry_risk_adjudication(
    response: Any,
    *,
    setup_evidence: Any,
) -> list[str]:
    """Reject invented facts and semantic drift without semantic repair."""

    result = _as_dict(response)
    setup = _as_dict(setup_evidence)
    errors = validate_entry_setup_evidence(setup)
    expected_fields = {
        "schema",
        "risk_verdict",
        "risk_codes",
        "supporting_fact_ids",
        "contradicting_fact_ids",
        "confidence",
    }
    if set(result) - expected_fields:
        errors.append("entry_risk_unexpected_fields")
    if result.get("schema") != ENTRY_RISK_ADJUDICATION_SCHEMA:
        errors.append("entry_risk_schema_invalid")
    verdict = str(result.get("risk_verdict") or "").strip().upper()
    if verdict not in RISK_VERDICTS:
        errors.append("entry_risk_verdict_invalid")
    codes = result.get("risk_codes")
    if (
        not isinstance(codes, list)
        or not codes
        or any(not isinstance(code, str) for code in codes)
        or len(codes) != len(set(map(str, codes)))
        or any(str(code) not in RISK_CODES for code in codes)
    ):
        errors.append("entry_risk_codes_invalid")
        codes = []
    confidence = result.get("confidence")
    if (
        isinstance(confidence, bool)
        or not isinstance(confidence, int)
        or not 0 <= confidence <= 100
    ):
        errors.append("entry_risk_confidence_invalid")
    positive_facts = set(map(str, setup.get("positive_facts") or []))
    adverse_facts = {
        *map(str, setup.get("contradicting_facts") or []),
        *map(str, setup.get("invalidation_facts") or []),
    }
    fact_sets = {
        "supporting_fact_ids": positive_facts,
        "contradicting_fact_ids": adverse_facts,
    }
    for field, known_facts in fact_sets.items():
        values = result.get(field)
        if not isinstance(values, list) or len(values) != len(set(map(str, values))):
            errors.append(f"entry_risk_{field}_invalid")
            continue
        if any(str(value) not in known_facts for value in values):
            errors.append(f"entry_risk_{field}_invented")
    supporting_fact_ids = result.get("supporting_fact_ids")
    contradicting_fact_ids = result.get("contradicting_fact_ids")
    referenced_facts = [
        *(list(supporting_fact_ids) if isinstance(supporting_fact_ids, list) else []),
        *(
            list(contradicting_fact_ids)
            if isinstance(contradicting_fact_ids, list)
            else []
        ),
    ]
    if verdict != "INSUFFICIENT" and not referenced_facts:
        errors.append("entry_risk_fact_reference_required")
    if verdict == "PASS" and not result.get("supporting_fact_ids"):
        errors.append("entry_risk_pass_supporting_fact_required")
    if verdict in {"CAUTION", "VETO"} and not result.get("contradicting_fact_ids"):
        errors.append("entry_risk_adverse_fact_required")
    if "NO_BLOCKING_RISK" in set(map(str, codes)) and len(codes) != 1:
        errors.append("entry_risk_no_blocking_code_conflict")
    if verdict != "PASS" and "NO_BLOCKING_RISK" in set(map(str, codes)):
        errors.append("entry_risk_no_blocking_verdict_invalid")
    if verdict == "PASS" and set(map(str, codes)) != {"NO_BLOCKING_RISK"}:
        errors.append("entry_risk_pass_codes_invalid")
    if setup.get("version") == ENTRY_SETUP_BALANCED_EVIDENCE_VERSION:
        if len(codes) > 6 or any(
            isinstance(result.get(field), list) and len(result[field]) > 8
            for field in ("supporting_fact_ids", "contradicting_fact_ids")
        ):
            errors.append("entry_risk_citation_bounds_exceeded")
        bindings = _risk_fact_bindings(setup)
        cited = (
            set(map(str, contradicting_fact_ids))
            if isinstance(contradicting_fact_ids, list)
            else set()
        )
        support = (
            set(map(str, supporting_fact_ids))
            if isinstance(supporting_fact_ids, list)
            else set()
        )
        if verdict == "PASS":
            if set(bindings) & BLOCKING_VETO_RISK_CODES or setup.get(
                "invalidation_facts"
            ):
                errors.append("entry_risk_pass_ignores_blocking_risk")
            if any(not cited.intersection(facts) for facts in bindings.values()):
                errors.append("entry_risk_pass_residual_risk_not_considered")
            if not support.intersection(
                {
                    "structural_edge_floor",
                    "early_session_structural_edge_floor",
                    "orderly_pullback_recovery",
                    "clean_continuation_probe_eligible",
                    "recovery_confirmation_probe_eligible",
                }
            ) or not support.intersection(
                {
                    "trusted_supportive_trigger",
                    "trigger_confirmed",
                    "clean_continuation_probe_eligible",
                    "recovery_confirmation_probe_eligible",
                }
            ):
                errors.append("entry_risk_pass_setup_and_trigger_support_required")
        else:
            for code in codes:
                if code not in bindings or not cited.intersection(
                    bindings.get(code, [])
                ):
                    errors.append("entry_risk_code_fact_binding_invalid")
            if verdict == "VETO" and not set(codes).intersection(
                BLOCKING_VETO_RISK_CODES
            ):
                errors.append("entry_risk_veto_requires_blocking_risk")
    elif verdict == "PASS" and setup.get("corroborated_risk_codes"):
        errors.append("entry_risk_pass_ignores_corroborated_risk")
    if verdict == "VETO" and set(map(str, codes)) == {"NO_BLOCKING_RISK"}:
        errors.append("entry_risk_veto_without_risk")
    if verdict == "INSUFFICIENT" and "SOURCE_QUALITY_GAP" not in set(map(str, codes)):
        errors.append("entry_risk_insufficient_without_source_gap")
    if (
        verdict == "INSUFFICIENT"
        and setup.get("setup_state") != "INSUFFICIENT"
        and "SOURCE_QUALITY_GAP"
        not in set(map(str, setup.get("corroborated_risk_codes") or []))
    ):
        errors.append("entry_risk_unfounded_insufficient")
    if setup.get("setup_state") == "INSUFFICIENT" and verdict != "INSUFFICIENT":
        errors.append("entry_risk_source_insufficient_misclassified")
    if setup.get("setup_state") == "INVALID" and verdict == "PASS":
        errors.append("entry_risk_invalid_setup_pass")
    if setup.get("setup_state") == "INVALID" and verdict == "CAUTION":
        errors.append("entry_risk_invalid_setup_requires_veto")
    if setup.get("setup_state") == "INVALID" and verdict == "VETO":
        cited = set(map(str, result.get("contradicting_fact_ids") or []))
        invalidations = set(map(str, setup.get("invalidation_facts") or []))
        if not cited.intersection(invalidations):
            errors.append("entry_risk_invalid_setup_invalidation_fact_required")
    if setup.get("setup_state") == "WAIT_CONFIRMATION" and verdict == "PASS":
        errors.append("entry_risk_wait_confirmation_pass")
    if setup.get("setup_state") == "UNCONFIRMED" and verdict == "PASS":
        errors.append("entry_risk_unconfirmed_pass")
    return list(dict.fromkeys(errors))


def validate_entry_action_comparison(
    response: Any,
    *,
    setup_evidence: Any,
) -> list[str]:
    """Validate an outcome-blind ENTER_NOW versus RECHECK comparison."""

    result = _as_dict(response)
    setup = _as_dict(setup_evidence)
    errors = validate_entry_setup_evidence(setup)
    expected_fields = {
        "schema",
        "preferred_action",
        "opportunity_fact_ids",
        "risk_assessments",
        "recheck_reason",
        "recheck_value_vs_opportunity_decay",
        "confidence",
    }
    if set(result) != expected_fields:
        errors.append("entry_comparison_fields_invalid")
    response_schema = result.get("schema")
    if response_schema not in {
        ENTRY_ACTION_COMPARISON_SCHEMA,
        ENTRY_ACTION_COUNTERWEIGHT_COMPARISON_SCHEMA,
    }:
        errors.append("entry_comparison_schema_invalid")
    counterweight_bound = (
        response_schema == ENTRY_ACTION_COUNTERWEIGHT_COMPARISON_SCHEMA
    )
    action = str(result.get("preferred_action") or "").strip().upper()
    state = str(setup.get("setup_state") or "").strip().upper()
    bindings = _risk_fact_bindings(setup)
    allowed_actions = (
        {"ENTER_NOW"}
        if state == "READY" and not bindings
        else (
            {"ENTER_NOW", "RECHECK"}
            if state == "READY"
            else (
                {"RECHECK"}
                if state in {"WAIT_CONFIRMATION", "UNCONFIRMED"}
                else {"BLOCK"}
            )
        )
    )
    if action not in COMPARATIVE_ENTRY_ACTIONS or action not in allowed_actions:
        errors.append("entry_comparison_action_state_invalid")
    confidence = result.get("confidence")
    if (
        isinstance(confidence, bool)
        or not isinstance(confidence, int)
        or not 0 <= confidence <= 100
    ):
        errors.append("entry_comparison_confidence_invalid")

    opportunity_ids = result.get("opportunity_fact_ids")
    positive_facts = set(map(str, setup.get("positive_facts") or []))
    if (
        not isinstance(opportunity_ids, list)
        or len(opportunity_ids) > 8
        or len(opportunity_ids) != len(set(map(str, opportunity_ids)))
        or any(str(value) not in positive_facts for value in opportunity_ids)
    ):
        errors.append("entry_comparison_opportunity_facts_invalid")
        opportunity_ids = []

    assessments = result.get("risk_assessments")
    assessment_by_code: dict[str, dict[str, Any]] = {}
    if not isinstance(assessments, list) or len(assessments) != len(bindings):
        errors.append("entry_comparison_risk_assessment_count_invalid")
        assessments = []
    for assessment in assessments:
        expected_assessment_fields = {
            "risk_code",
            "fact_id",
            "disposition",
        }
        if counterweight_bound:
            expected_assessment_fields.add("counterweight_fact_ids")
        if (
            not isinstance(assessment, dict)
            or set(assessment) != expected_assessment_fields
        ):
            errors.append("entry_comparison_risk_assessment_fields_invalid")
            continue
        code = str(assessment.get("risk_code") or "")
        fact_id = str(assessment.get("fact_id") or "")
        disposition = str(assessment.get("disposition") or "")
        if code in assessment_by_code:
            errors.append("entry_comparison_risk_code_duplicate")
        assessment_by_code[code] = assessment
        if code not in bindings or fact_id not in bindings.get(code, []):
            errors.append("entry_comparison_risk_fact_binding_invalid")
        if disposition not in COMPARATIVE_RISK_DISPOSITIONS:
            errors.append("entry_comparison_risk_disposition_invalid")
        if code in BLOCKING_VETO_RISK_CODES and disposition != "BLOCKING":
            errors.append("entry_comparison_blocking_risk_downgraded")
        if code not in BLOCKING_VETO_RISK_CODES and disposition == "BLOCKING":
            errors.append("entry_comparison_bounded_risk_escalated")
        if counterweight_bound:
            counterweight_ids = assessment.get("counterweight_fact_ids")
            if (
                not isinstance(counterweight_ids, list)
                or len(counterweight_ids) != len(set(map(str, counterweight_ids)))
                or any(not isinstance(value, str) for value in counterweight_ids)
            ):
                errors.append("entry_comparison_counterweight_facts_invalid")
                counterweight_ids = []
            required_counterweights = _required_counterweight_fact_ids_for_risk(
                setup,
                risk_code=code,
            )
            if disposition == "COMPENSATED":
                if not required_counterweights or set(counterweight_ids) != set(
                    required_counterweights
                ):
                    errors.append("entry_comparison_compensation_unbound")
            elif counterweight_ids:
                errors.append("entry_comparison_unused_counterweight_facts")
    if set(assessment_by_code) != set(bindings):
        errors.append("entry_comparison_risk_coverage_invalid")

    dispositions = {
        str(assessment.get("disposition") or "")
        for assessment in assessments
        if isinstance(assessment, dict)
    }
    reason = str(result.get("recheck_reason") or "")
    allowed_reasons = _comparative_recheck_reasons(setup)
    tradeoff = str(result.get("recheck_value_vs_opportunity_decay") or "")
    expected_tradeoff = {
        "ENTER_NOW": "ENTER_NOW_DOMINANT",
        "RECHECK": "RECHECK_DOMINANT",
        "BLOCK": "NOT_APPLICABLE_BLOCKED",
    }.get(action)
    if tradeoff not in COMPARATIVE_RECHECK_TRADEOFFS or tradeoff != expected_tradeoff:
        errors.append("entry_comparison_tradeoff_action_invalid")
    if action == "ENTER_NOW":
        if reason != "NONE":
            errors.append("entry_comparison_enter_recheck_reason_invalid")
        if any(disposition != "COMPENSATED" for disposition in dispositions):
            errors.append("entry_comparison_enter_unresolved_risk")
        support = set(map(str, opportunity_ids))
        if not support.intersection(
            {
                "structural_edge_floor",
                "early_session_structural_edge_floor",
                "orderly_pullback_recovery",
                "clean_continuation_probe_eligible",
                "recovery_confirmation_probe_eligible",
            }
        ) or not support.intersection(
            {
                "trusted_supportive_trigger",
                "trigger_confirmed",
                "clean_continuation_probe_eligible",
                "recovery_confirmation_probe_eligible",
            }
        ):
            errors.append("entry_comparison_enter_setup_trigger_support_required")
    elif action == "RECHECK":
        if "RECHECKABLE" not in dispositions:
            errors.append("entry_comparison_recheckable_risk_required")
        if reason == "NONE" or reason not in allowed_reasons:
            errors.append("entry_comparison_recheck_reason_invalid")
    elif action == "BLOCK":
        if reason != "NONE" and reason not in allowed_reasons:
            errors.append("entry_comparison_block_recheck_reason_invalid")
        if state not in {"INVALID", "INSUFFICIENT"} and "BLOCKING" not in dispositions:
            errors.append("entry_comparison_block_without_blocker")
    return list(dict.fromkeys(errors))


def compose_entry_action_comparison(
    *,
    setup_evidence: Any,
    action_comparison: Any,
    bounded_recovery_policy: bool = False,
) -> dict[str, Any]:
    """Compose the comparative response through the existing guarded action shape."""

    setup = _as_dict(setup_evidence)
    comparison = _as_dict(action_comparison)
    comparison_errors = validate_entry_action_comparison(
        comparison,
        setup_evidence=setup,
    )
    action = str(comparison.get("preferred_action") or "").strip().upper()
    assessments = [
        assessment
        for assessment in comparison.get("risk_assessments") or []
        if isinstance(assessment, dict)
    ]
    support = [str(value) for value in comparison.get("opportunity_fact_ids") or []]
    if comparison_errors:
        risk = {
            "schema": ENTRY_RISK_ADJUDICATION_SCHEMA,
            "risk_verdict": "CAUTION",
            "risk_codes": [],
            "supporting_fact_ids": [],
            "contradicting_fact_ids": [],
            "confidence": 0,
        }
    elif action == "ENTER_NOW":
        risk = {
            "schema": ENTRY_RISK_ADJUDICATION_SCHEMA,
            "risk_verdict": "PASS",
            "risk_codes": ["NO_BLOCKING_RISK"],
            "supporting_fact_ids": support,
            "contradicting_fact_ids": [
                str(assessment.get("fact_id")) for assessment in assessments
            ],
            "confidence": comparison.get("confidence"),
        }
    elif action == "RECHECK":
        recheckable = [
            assessment
            for assessment in assessments
            if assessment.get("disposition") == "RECHECKABLE"
        ]
        risk = {
            "schema": ENTRY_RISK_ADJUDICATION_SCHEMA,
            "risk_verdict": "CAUTION",
            "risk_codes": [
                str(assessment.get("risk_code")) for assessment in recheckable
            ],
            "supporting_fact_ids": support,
            "contradicting_fact_ids": [
                str(assessment.get("fact_id")) for assessment in recheckable
            ],
            "confidence": comparison.get("confidence"),
        }
    else:
        blocking = [
            assessment
            for assessment in assessments
            if assessment.get("disposition") == "BLOCKING"
        ]
        insufficient = str(setup.get("setup_state") or "").upper() == "INSUFFICIENT"
        risk = {
            "schema": ENTRY_RISK_ADJUDICATION_SCHEMA,
            "risk_verdict": "INSUFFICIENT" if insufficient else "VETO",
            "risk_codes": (
                ["SOURCE_QUALITY_GAP"]
                if insufficient and not blocking
                else [str(assessment.get("risk_code")) for assessment in blocking]
            ),
            "supporting_fact_ids": support,
            "contradicting_fact_ids": [
                str(assessment.get("fact_id")) for assessment in blocking
            ],
            "confidence": comparison.get("confidence"),
        }
    result = compose_entry_decision(
        setup_evidence=setup,
        risk_adjudication=risk,
        bounded_recovery_policy=bounded_recovery_policy,
        timing_aware_policy=True,
    )
    result["composer_version"] = (
        (
            ENTRY_DECISION_COMPOSER_V2_15_4_VERSION
            if bounded_recovery_policy
            else ENTRY_DECISION_COMPOSER_V2_14_4_VERSION
        )
        if comparison.get("schema") == ENTRY_ACTION_COUNTERWEIGHT_COMPARISON_SCHEMA
        else (
            ENTRY_DECISION_COMPOSER_V2_15_3_VERSION
            if bounded_recovery_policy
            else ENTRY_DECISION_COMPOSER_V2_14_3_VERSION
        )
    )
    result["entry_action_comparison"] = comparison
    result["entry_action_comparison_schema"] = ENTRY_ACTION_COMPARISON_SCHEMA
    result["entry_action_comparison_preferred_action"] = action
    result["entry_action_comparison_tradeoff"] = comparison.get(
        "recheck_value_vs_opportunity_decay"
    )
    if comparison_errors:
        result.update(
            action="WAIT",
            edge_state="INSUFFICIENT_DATA",
            reason="entry_action_comparison_contract_invalid",
            entry_composed_action="WAIT",
            entry_composed_reason="entry_action_comparison_contract_invalid",
            entry_probe_intent=False,
            entry_probe_intent_status="not_eligible",
            entry_ai_contract_valid=False,
            entry_ai_contract_errors=comparison_errors,
            decision_quality_contract_status="fail_closed",
        )
    elif action == "RECHECK":
        result["entry_recheck_reasons"] = [comparison["recheck_reason"]]
        result["entry_recheck_intent"] = True
        result["entry_recheck_intent_status"] = "eligible_next_scanner_loop_recheck"
    result.pop("composer_sha256", None)
    result["composer_sha256"] = _canonical_sha256(result)
    return result


def repair_invalid_entry_risk_adjudication(
    response: Any,
    *,
    setup_evidence: Any,
) -> tuple[dict[str, Any], list[str]]:
    """Attach a ledger-backed invalidation citation to a fail-closed VETO.

    This bounded offline repair runs only when the deterministic setup is
    already INVALID and the provider already returned VETO. It cannot promote
    an exposure, change risk codes, or invent evidence; it copies one exact
    invalidation ID from the validated setup ledger and leaves any other
    contract error for the caller to reject.
    """

    result = json.loads(json.dumps(_as_dict(response)))
    setup = _as_dict(setup_evidence)
    if validate_entry_setup_evidence(setup):
        return result, []
    if (
        setup.get("setup_state") != "INVALID"
        or str(result.get("risk_verdict") or "").strip().upper() != "VETO"
    ):
        return result, []
    cited = result.get("contradicting_fact_ids")
    invalidations = [str(value) for value in setup.get("invalidation_facts") or []]
    if not isinstance(cited, list) or not invalidations:
        return result, []
    cited_ids = [str(value) for value in cited]
    if set(cited_ids).intersection(invalidations):
        return result, []
    result["contradicting_fact_ids"] = list(
        dict.fromkeys([invalidations[0], *cited_ids])
    )[:8]
    return result, ["invalid_setup_invalidation_fact_copied_from_ledger"]


def compose_entry_decision(
    *,
    setup_evidence: Any,
    risk_adjudication: Any,
    bounded_recovery_policy: bool = False,
    sequential_recovery_policy: bool = False,
    timing_aware_policy: bool = False,
) -> dict[str, Any]:
    """Compose an offline legacy-compatible action without order authority."""

    if bounded_recovery_policy and sequential_recovery_policy:
        raise ValueError("entry_recovery_policy_modes_are_mutually_exclusive")

    setup = _as_dict(setup_evidence)
    risk = _as_dict(risk_adjudication)
    balanced_policy = setup.get("version") == ENTRY_SETUP_BALANCED_EVIDENCE_VERSION
    timing_aware_policy = timing_aware_policy or balanced_policy
    context_observations = _as_dict(setup.get("context_observations"))
    state = str(setup.get("setup_state") or "INSUFFICIENT").strip().upper()
    family = str(setup.get("setup_family") or "NO_VALID_SETUP").strip().upper()
    verdict = str(risk.get("risk_verdict") or "INSUFFICIENT").strip().upper()
    raw_risk_codes = risk.get("risk_codes")
    risk_codes = (
        [str(value) for value in raw_risk_codes]
        if isinstance(raw_risk_codes, list)
        else []
    )
    corroborated_codes = set(map(str, setup.get("corroborated_risk_codes") or []))
    supported_veto_codes = sorted(set(risk_codes) & corroborated_codes)
    corroborated_veto_codes = sorted(
        set(supported_veto_codes) & BLOCKING_VETO_RISK_CODES
    )
    bounded_risk_codes = sorted(set(supported_veto_codes) - BLOCKING_VETO_RISK_CODES)
    veto_corroborated = bool(verdict == "VETO" and corroborated_veto_codes)
    contract_errors = validate_entry_risk_adjudication(
        risk,
        setup_evidence=setup,
    )
    recheck_reasons = [str(value) for value in setup.get("recheck_reasons") or []]
    positive_facts = set(map(str, setup.get("positive_facts") or []))
    contradicting_facts = set(map(str, setup.get("contradicting_facts") or []))
    invalidation_facts = set(map(str, setup.get("invalidation_facts") or []))
    source_quality = _as_dict(setup.get("source_quality"))
    source_fresh = str(source_quality.get("status") or "").lower() in {
        "fresh",
        "fresh_consistent",
        "pass",
    }
    bounded_recovery_path = None
    # V2.15 is an exploration-only recovery seed and therefore cannot turn an
    # otherwise READY/PASS setup into immediate exposure.  V2.15.1 is the
    # reviewed timing-aware performance descendant: it keeps the same bounded
    # recovery paths for non-ready setups while preserving the ordinary
    # READY/PASS exposure and READY/CAUTION one-share observation semantics.
    # V2.16 remains a sequential observation seed.
    seed_only_recovery_policy = bool(
        sequential_recovery_policy
        or (bounded_recovery_policy and not timing_aware_policy)
    )
    if (
        (bounded_recovery_policy or sequential_recovery_policy)
        and source_fresh
        and not contract_errors
    ):
        if (
            state == "WAIT_CONFIRMATION"
            and family == "MICRO_RECOVERY"
            and not invalidation_facts
        ):
            bounded_recovery_path = "intrabar_micro_price_flow_recovery"
        elif (
            state == "UNCONFIRMED"
            and not invalidation_facts
            and "no_supported_setup" in contradicting_facts
            and str(setup.get("structure_phase") or "") == "distribution"
            and "liquidity_supportive" in positive_facts
            and "supportive_micro_tape_vs_program_net_sell" in contradicting_facts
        ):
            bounded_recovery_path = "soft_distribution_micro_program_divergence"
        elif (
            state == "WAIT_CONFIRMATION"
            and family == "RECOVERY_CONFIRMATION"
            and not invalidation_facts
            and recheck_reasons == ["TRIGGER_CONFIRMATION_RECHECK"]
            and {"liquidity_supportive", "tape_supportive"}.issubset(positive_facts)
        ):
            bounded_recovery_path = "recovery_liquidity_tape_confirmation"
    recheck_intent = bool(
        not contract_errors
        and (
            state == "WAIT_CONFIRMATION"
            or bool(recheck_reasons)
            or bounded_recovery_path is not None
        )
    )
    bounded_wait_probe_intent = bool(
        recheck_intent
        and state != "UNCONFIRMED"
        and not sequential_recovery_policy
        and "LARGE_SELL_EXHAUSTION_RECHECK" not in recheck_reasons
        and (
            bounded_recovery_path is not None
            if bounded_recovery_policy
            else not invalidation_facts
        )
    )

    if contract_errors:
        action = "WAIT"
        edge_state = "INSUFFICIENT_DATA"
        probe_intent = False
        reason = "entry_setup_or_ai_contract_invalid"
    elif state == "INSUFFICIENT" or verdict == "INSUFFICIENT":
        action = "WAIT"
        edge_state = "INSUFFICIENT_DATA"
        probe_intent = False
        reason = "entry_setup_or_ai_insufficient"
    elif state in {"INVALID", "UNCONFIRMED"}:
        if bounded_recovery_path is not None:
            action = "WAIT"
            edge_state = "EDGE"
            probe_intent = not sequential_recovery_policy
            reason = (
                "entry_setup_sequential_recovery_observation"
                if sequential_recovery_policy
                else "entry_setup_bounded_recovery_recheck_probe"
            )
        else:
            action = "WAIT" if state == "UNCONFIRMED" else "DROP"
            edge_state = "NO_EDGE"
            probe_intent = False
            reason = (
                "entry_setup_discovery_required"
                if state == "UNCONFIRMED"
                else "entry_setup_invalid"
            )
    elif state == "WAIT_CONFIRMATION":
        action = "WAIT"
        edge_state = "EDGE"
        probe_intent = bounded_wait_probe_intent
        reason = (
            "entry_setup_bounded_wait_probe"
            if bounded_wait_probe_intent
            else "entry_setup_confirmation_required"
        )
    elif veto_corroborated:
        action = "DROP"
        edge_state = "EDGE"
        probe_intent = False
        reason = "entry_ai_veto_corroborated"
    elif verdict == "PASS":
        action = "WAIT" if seed_only_recovery_policy else "BUY"
        edge_state = "EDGE"
        probe_intent = not seed_only_recovery_policy
        reason = (
            "entry_setup_ready_outside_bounded_recovery_cohort"
            if seed_only_recovery_policy
            else "entry_setup_ready_ai_pass"
        )
    else:
        action = "WAIT"
        edge_state = "EDGE"
        probe_intent = False if seed_only_recovery_policy else True
        reason = (
            "entry_ai_veto_uncorroborated_recheck"
            if verdict == "VETO"
            else "entry_ai_caution_recheck"
        )

    if (
        balanced_policy
        and not contract_errors
        and action == "WAIT"
        and probe_intent
        and not recheck_reasons
    ):
        # Use the existing quote/tape recheck owner, TTL and attempt caps.
        # READY/CAUTION is not immediate non-participation or a new scheduler.
        recheck_reasons = ["MICRO_PRICE_RESPONSE_RECHECK"]
        recheck_intent = True

    confidence = risk.get("confidence")
    confidence = (
        confidence
        if isinstance(confidence, int) and not isinstance(confidence, bool)
        else 0
    )
    score = (
        max(75, confidence)
        if action == "BUY"
        else (
            min(74, max(50, 50 + round(confidence * 0.24)))
            if action == "WAIT"
            else min(49, max(0, round(49 * (1.0 - confidence / 100.0))))
        )
    )
    setup_name = {
        "CLEAN_CONTINUATION": "continuation",
        "PULLBACK_RECOVERY": "pullback_recovery",
        "RECOVERY_CONFIRMATION": "reversal",
        "MICRO_RECOVERY": "reversal",
    }.get(family, "no_setup")
    result = {
        "schema": ENTRY_DECISION_COMPOSER_SCHEMA,
        "composer_version": (
            (
                ENTRY_DECISION_COMPOSER_V2_15_2_VERSION
                if bounded_recovery_policy
                else ENTRY_DECISION_COMPOSER_V2_14_2_VERSION
            )
            if balanced_policy
            else (
                ENTRY_DECISION_COMPOSER_V2_16_VERSION
                if sequential_recovery_policy
                else (
                    (
                        ENTRY_DECISION_COMPOSER_V2_15_1_VERSION
                        if timing_aware_policy
                        else ENTRY_DECISION_COMPOSER_V2_15_VERSION
                    )
                    if bounded_recovery_policy
                    else (
                        ENTRY_DECISION_COMPOSER_V2_14_1_VERSION
                        if timing_aware_policy
                        else ENTRY_DECISION_COMPOSER_VERSION
                    )
                )
            )
        ),
        "action": action,
        "score": score,
        "score_authority": "legacy_response_shape_only_not_a_decision_gate",
        "reason": reason,
        "edge_state": edge_state,
        "evidence": {
            "setup": setup_name,
            "trigger": (
                "confirmed"
                if action == "BUY"
                else (
                    "recovery_required"
                    if edge_state == "EDGE" and action == "WAIT"
                    else (
                        "failed"
                        if edge_state != "INSUFFICIENT_DATA"
                        else "insufficient"
                    )
                )
            ),
        },
        "entry_setup_evidence_version": setup.get("version"),
        "entry_setup_evidence_sha256": setup.get("evidence_sha256"),
        "entry_setup_family": family,
        "entry_setup_state": state,
        "entry_structure_phase": setup.get("structure_phase"),
        "entry_structure_phase_policy_version": setup.get(
            "structure_phase_policy_version"
        ),
        "entry_structure_phase_sha256": setup.get("structure_phase_sha256"),
        "entry_structure_phase_bar_end": setup.get("structure_phase_bar_end"),
        "entry_execution_readiness_state": setup.get("execution_readiness_state"),
        "entry_timing_state": _as_dict(setup.get(ENTRY_TIMING_OBSERVATION_SCHEMA)).get(
            "state"
        ),
        "entry_ai_risk_verdict": verdict,
        "entry_ai_risk_codes": risk_codes,
        "entry_ai_veto_supported_codes": supported_veto_codes,
        "entry_ai_bounded_risk_codes": bounded_risk_codes,
        "entry_ai_veto_corroborated": veto_corroborated,
        "entry_ai_veto_corroborated_codes": corroborated_veto_codes,
        "entry_ai_contract_valid": not contract_errors,
        "entry_ai_contract_errors": contract_errors,
        "entry_probe_intent": probe_intent,
        "entry_probe_intent_status": (
            "eligible_offline_probe"
            if action == "BUY"
            else "eligible_wait_probe" if probe_intent else "not_eligible"
        ),
        "entry_probe_intent_authority": (
            "offline_candidate_only_existing_submit_guard_required"
        ),
        "entry_probe_intent_submit_guard_required": True,
        "entry_probe_intent_actual_order_submitted": False,
        "downstream_guard_contract": {
            "one_share_probe_first_required": True,
            "fresh_submit_revalidation_required": True,
            "account_order_quantity_cooldown_guards_required": True,
            "post_probe_direction_recheck_required": True,
            "hard_protect_emergency_exit_guards_required": True,
            "guard_bypass_allowed": False,
        },
        "entry_recheck_intent": recheck_intent,
        "entry_recheck_reasons": recheck_reasons,
        "entry_recheck_intent_status": (
            "eligible_next_scanner_loop_recheck" if recheck_intent else "not_eligible"
        ),
        "entry_recheck_intent_authority": "offline_observation_only",
        "entry_recheck_intent_actual_order_submitted": False,
        "entry_bounded_recovery_policy_version": (
            ENTRY_BOUNDED_RECOVERY_POLICY_VERSION if bounded_recovery_policy else None
        ),
        "entry_bounded_recovery_eligible": bounded_recovery_path is not None,
        "entry_bounded_recovery_path": bounded_recovery_path,
        "entry_sequential_recovery_policy_version": (
            ENTRY_SEQUENTIAL_RECOVERY_POLICY_VERSION
            if sequential_recovery_policy
            else None
        ),
        "entry_sequential_recovery_seed_eligible": bool(
            sequential_recovery_policy and bounded_recovery_path is not None
        ),
        "entry_tail_risk_state": str(
            _as_dict(setup.get("tail_risk_assessment")).get("state") or "not_observed"
        ),
        "entry_tail_risk_calibration_version": str(
            _as_dict(setup.get("tail_risk_assessment")).get("version") or ""
        ),
        "entry_setup_source_quality": dict(setup.get("source_quality") or {}),
        "entry_setup_context_observation_version": context_observations.get("version"),
        **{
            f"entry_setup_{source_name}_status": _as_dict(
                context_observations.get(source_name)
            ).get("status", "unavailable")
            for source_name in (
                "market_relative",
                "sector_relative",
                "program_flow",
                "investor_flow",
                "external_market",
            )
        },
        **{
            f"entry_setup_{source_name}_usable_for_risk": bool(
                _as_dict(context_observations.get(source_name)).get(
                    "usable_for_risk", False
                )
            )
            for source_name in (
                "market_relative",
                "sector_relative",
                "program_flow",
                "investor_flow",
                "external_market",
            )
        },
        "entry_composed_action": action,
        "entry_composed_reason": reason,
        "decision_quality_contract_status": (
            "pass" if not contract_errors else "fail_closed"
        ),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    result["composer_sha256"] = _canonical_sha256(result)
    return result

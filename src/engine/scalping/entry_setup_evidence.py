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

ENTRY_SETUP_EVIDENCE_SCHEMA = "entry_setup_evidence_v1"
ENTRY_RISK_ADJUDICATION_SCHEMA = "entry_setup_risk_adjudication_v1"
ENTRY_DECISION_COMPOSER_SCHEMA = "entry_decision_composer_v1"
ENTRY_SETUP_EVIDENCE_VERSION = "entry_setup_evidence_policy_v9"
ENTRY_DECISION_COMPOSER_VERSION = "entry_decision_composer_policy_v8"
ENTRY_DECISION_COMPOSER_V2_15_VERSION = "entry_decision_composer_policy_v9"
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

RECHECK_REASONS = {
    "TRIGGER_CONFIRMATION_RECHECK",
    "LARGE_SELL_EXHAUSTION_RECHECK",
    "TAIL_LIQUIDITY_RECHECK",
}

SETUP_FAMILIES = {
    "CLEAN_CONTINUATION",
    "PULLBACK_RECOVERY",
    "RECOVERY_CONFIRMATION",
    "NO_VALID_SETUP",
}
SETUP_STATES = {"READY", "WAIT_CONFIRMATION", "INVALID", "INSUFFICIENT"}
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
) -> dict[str, Any]:
    """Classify a symbol-agnostic setup from existing exact analysis ledgers."""

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
    else:
        setup_family = "NO_VALID_SETUP"
        setup_state = "INVALID"
        invalidation_facts.append("no_supported_setup")
        corroborated_risk_codes.append("STRUCTURE_INVALIDATED")

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
        "version": ENTRY_SETUP_EVIDENCE_VERSION,
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
    evidence["evidence_sha256"] = _canonical_sha256(evidence)
    return evidence


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
            }:
                field_schema["minItems"] = 1
        else:
            field_schema["maxItems"] = 0
    return schema


def validate_entry_setup_evidence(evidence: Any) -> list[str]:
    """Validate the deterministic ledger before AI output can be composed."""

    setup = _as_dict(evidence)
    errors: list[str] = []
    if setup.get("schema") != ENTRY_SETUP_EVIDENCE_SCHEMA:
        errors.append("entry_setup_evidence_schema_invalid")
    if setup.get("version") != ENTRY_SETUP_EVIDENCE_VERSION:
        errors.append("entry_setup_evidence_version_invalid")
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
        and setup.get("setup_state") not in {"INVALID", "INSUFFICIENT"}
    ) or (
        setup.get("setup_family") in SETUP_FAMILIES - {"NO_VALID_SETUP"}
        and setup.get("setup_state") in {"INVALID", "INSUFFICIENT"}
    ):
        errors.append("entry_setup_family_state_inconsistent")
    expected_phase_family = STRUCTURE_PHASE_FAMILIES.get(
        setup.get("structure_phase"), "NO_VALID_SETUP"
    )
    if setup.get("setup_family") != "NO_VALID_SETUP" and (
        setup.get("setup_family") != expected_phase_family
    ):
        errors.append("entry_setup_structure_phase_family_inconsistent")
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
    if setup.get("setup_state") != "WAIT_CONFIRMATION" and recheck_reasons:
        errors.append("entry_setup_recheck_reason_state_inconsistent")
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
    if verdict == "PASS" and setup.get("corroborated_risk_codes"):
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
    return list(dict.fromkeys(errors))


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
) -> dict[str, Any]:
    """Compose an offline legacy-compatible action without order authority."""

    if bounded_recovery_policy and sequential_recovery_policy:
        raise ValueError("entry_recovery_policy_modes_are_mutually_exclusive")

    setup = _as_dict(setup_evidence)
    risk = _as_dict(risk_adjudication)
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
    recovery_seed_policy = bounded_recovery_policy or sequential_recovery_policy
    if recovery_seed_policy and source_fresh and not contract_errors:
        if (
            state == "INVALID"
            and invalidation_facts == {"no_supported_setup"}
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
        and (state == "WAIT_CONFIRMATION" or bounded_recovery_path is not None)
    )
    bounded_wait_probe_intent = bool(
        recheck_intent
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
    elif state == "INVALID":
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
            action = "DROP"
            edge_state = "NO_EDGE"
            probe_intent = False
            reason = "entry_setup_invalid"
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
        action = "WAIT" if recovery_seed_policy else "BUY"
        edge_state = "EDGE"
        probe_intent = not recovery_seed_policy
        reason = (
            "entry_setup_ready_outside_bounded_recovery_cohort"
            if recovery_seed_policy
            else "entry_setup_ready_ai_pass"
        )
    else:
        action = "WAIT"
        edge_state = "EDGE"
        probe_intent = False if recovery_seed_policy else True
        reason = (
            "entry_ai_veto_uncorroborated_recheck"
            if verdict == "VETO"
            else "entry_ai_caution_recheck"
        )

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
    }.get(family, "no_setup")
    result = {
        "schema": ENTRY_DECISION_COMPOSER_SCHEMA,
        "composer_version": (
            ENTRY_DECISION_COMPOSER_V2_16_VERSION
            if sequential_recovery_policy
            else (
                ENTRY_DECISION_COMPOSER_V2_15_VERSION
                if bounded_recovery_policy
                else ENTRY_DECISION_COMPOSER_VERSION
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

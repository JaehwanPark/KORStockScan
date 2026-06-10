"""Shared pre-final auto-promotion contracts for scalping and swing."""

from __future__ import annotations

from typing import Any


PRIMARY_EV_UPLIFT_THRESHOLD_PCT = 1.0

AUTO_PROMOTION_STATES = (
    "source_only",
    "sim_auto_approved",
    "ai_tier2_auto_approved",
    "dry_run_auto_apply_ready",
    "bounded_live_auto_apply_ready",
    "bounded_real_canary_auto_approved",
    "final_user_approval_required",
    "full_live_enabled",
)

FINAL_USER_APPROVAL_FAMILIES = {
    "full_swing_live_conversion",
    "full_scalping_live_conversion",
    "provider_route_change",
    "bot_restart",
    "hard_safety_relaxation",
    "protect_safety_relaxation",
    "emergency_safety_relaxation",
}

EXPLICIT_TIER2_BLOCK_TERMS = {
    "attribution",
    "broker",
    "cap",
    "contract",
    "cooldown",
    "env",
    "forbidden",
    "hook",
    "leak",
    "mapping",
    "missing",
    "provider",
    "qty",
    "safety",
    "schema",
    "source quality",
    "source_quality",
    "stale",
}


def tier2_validation_passed(status: Any) -> bool:
    return str(status or "").strip().lower() == "parsed"


def tier2_fail_closed_reason(status: Any) -> str | None:
    if tier2_validation_passed(status):
        return None
    normalized = str(status or "missing").strip().lower() or "missing"
    return f"ai_tier2_validation_not_parsed:{normalized}"


def explicit_tier2_block_allowed(reason: Any, final_state: str) -> bool:
    if final_state not in {
        "runtime_blocked_contract_gap",
        "code_patch_required",
        "code_review_failed",
        "automation_handoff_gap",
    }:
        return False
    text = str(reason or "").lower()
    return any(term in text for term in EXPLICIT_TIER2_BLOCK_TERMS)


def primary_ev_uplift_passes(
    value: Any,
    *,
    positive_edge: bool = True,
    threshold_pct: float = PRIMARY_EV_UPLIFT_THRESHOLD_PCT,
) -> bool:
    try:
        number = float(value)
    except Exception:
        return False
    if number != number:
        return False
    return number >= threshold_pct if positive_edge else number <= -threshold_pct


def pre_final_promotion_contract() -> dict[str, Any]:
    return {
        "schema_version": "pre_final_auto_promotion_contract_v1",
        "final_user_approval_boundary": "full_live_only",
        "states": list(AUTO_PROMOTION_STATES),
        "tier2_policy": "fail_closed",
        "primary_ev_uplift_threshold_pct": PRIMARY_EV_UPLIFT_THRESHOLD_PCT,
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "diagnostic_metric": "diagnostic_win_rate",
        "manual_only_final_families": sorted(FINAL_USER_APPROVAL_FAMILIES),
        "forbidden_pre_final_uses": [
            "full_live_conversion",
            "sizing_formula_runtime_apply_without_guard",
            "provider_route_change",
            "bot_restart",
            "hard_safety_relaxation",
            "protect_safety_relaxation",
            "emergency_safety_relaxation",
        ],
    }

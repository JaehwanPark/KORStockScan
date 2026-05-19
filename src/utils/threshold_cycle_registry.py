"""Shared threshold-cycle stage registry.

New threshold collectors should either add their stage here or emit a
``threshold_family`` field with the pipeline event. This keeps live compact
logging, raw backfill, and report loading on the same inclusion rule.
"""

from __future__ import annotations

from typing import Any


THRESHOLD_STAGE_FAMILY_MAP = {
    "budget_pass": "entry_mechanical_momentum",
    "order_bundle_submitted": "pre_submit_price_guard",
    "latency_pass": "pre_submit_price_guard",
    "pre_submit_price_guard_block": "pre_submit_price_guard",
    "pre_submit_liquidity_guard_block": "liquidity_pre_submit_guard_p1",
    "pre_submit_overbought_pullback_guard_block": "overbought_pullback_guard_p1",
    "entry_ai_price_canary_applied": "pre_submit_price_guard",
    "entry_ai_price_canary_fallback": "pre_submit_price_guard",
    "entry_ai_price_canary_skip_order": "pre_submit_price_guard",
    "entry_ai_price_canary_skip_followup": "pre_submit_price_guard",
    "entry_submit_revalidation_warning": "pre_submit_price_guard",
    "entry_submit_revalidation_block": "pre_submit_price_guard",
    "scalp_entry_action_decision_snapshot": "scalp_entry_action_decision_matrix",
    "lifecycle_decision_matrix_runtime_policy": "lifecycle_decision_matrix_runtime",
    "lifecycle_decision_matrix_runtime_effect": "lifecycle_decision_matrix_runtime",
    "entry_order_cancel_requested": "pre_submit_price_guard",
    "entry_order_cancel_confirmed": "pre_submit_price_guard",
    "entry_order_cancel_failed": "pre_submit_price_guard",
    "entry_ai_price_ofi_skip_demoted": "entry_ofi_ai_smoothing",
    "holding_flow_ofi_smoothing_applied": "holding_flow_ofi_smoothing",
    "holding_flow_override_force_exit": "holding_flow_ofi_smoothing",
    "bad_entry_block_observed": "bad_entry_block",
    "bad_entry_refined_candidate": "bad_entry_block",
    "bad_entry_refined_exit": "bad_entry_block",
    "reversal_add_candidate": "reversal_add",
    "reversal_add_blocked_reason": "reversal_add",
    "reversal_add_gate_blocked": "reversal_add",
    "soft_stop_micro_grace": "soft_stop_micro_grace",
    "soft_stop_expert_shadow": "soft_stop_expert_defense",
    "soft_stop_absorption_probe": "soft_stop_expert_defense",
    "soft_stop_absorption_extend": "soft_stop_expert_defense",
    "soft_stop_absorption_exit": "soft_stop_expert_defense",
    "soft_stop_absorption_recovered": "soft_stop_expert_defense",
    "protect_trailing_smooth_hold": "protect_trailing_smoothing",
    "protect_trailing_smooth_confirmed": "protect_trailing_smoothing",
    "adverse_fill_observed": "adverse_fill_detector",
    "scale_in_price_resolved": "scale_in_price_guard",
    "scale_in_price_guard_block": "scale_in_price_guard",
    "scale_in_price_p2_observe": "scale_in_price_guard",
    "exit_signal": "statistical_action_weight",
    "sell_completed": "statistical_action_weight",
    "scale_in_executed": "statistical_action_weight",
    "stat_action_decision_snapshot": "statistical_action_weight",
    "scalp_sim_entry_armed": "entry_mechanical_momentum",
    "scalp_sim_entry_ai_price_applied": "pre_submit_price_guard",
    "scalp_sim_entry_ai_price_skip_order": "pre_submit_price_guard",
    "scalp_sim_entry_submit_revalidation_warning": "pre_submit_price_guard",
    "scalp_sim_entry_submit_revalidation_block": "pre_submit_price_guard",
    "scalp_sim_buy_order_virtual_pending": "pre_submit_price_guard",
    "scalp_sim_buy_order_assumed_filled": "pre_submit_price_guard",
    "scalp_sim_holding_started": "statistical_action_weight",
    "scalp_sim_scale_in_order_assumed_filled": "scale_in_price_guard",
    "scalp_sim_scale_in_order_unfilled": "scale_in_price_guard",
    "scalp_sim_sell_order_assumed_filled": "statistical_action_weight",
    "scalp_sim_sell_blocked_zero_qty": "statistical_action_weight",
    "scalp_sim_entry_unpriced": "pre_submit_price_guard",
    "scalp_sim_entry_expired": "pre_submit_price_guard",
    "scalp_sim_duplicate_buy_signal": "entry_mechanical_momentum",
}

TARGET_STAGES = frozenset(THRESHOLD_STAGE_FAMILY_MAP)


def _clean_family(value: Any) -> str:
    family = str(value or "").strip()
    return family if family and family != "-" else ""


def threshold_family_for_stage(stage: str, fields: dict | None = None) -> str:
    family = THRESHOLD_STAGE_FAMILY_MAP.get(str(stage or "").strip(), "")
    if family:
        return family
    if isinstance(fields, dict):
        return _clean_family(fields.get("threshold_family"))
    return ""


def is_threshold_cycle_stage(stage: str, fields: dict | None = None) -> bool:
    return bool(threshold_family_for_stage(stage, fields))

"""Shared threshold-cycle stage registry.

New threshold collectors should either add their stage here or emit a
``threshold_family`` field with the pipeline event. This keeps live compact
logging, raw backfill, and report loading on the same inclusion rule.
"""

from __future__ import annotations

from typing import Any


THRESHOLD_STAGE_FAMILY_MAP = {
    "budget_pass": "entry_mechanical_momentum",
    "order_bundle_submitted": "dynamic_entry_price_resolver",
    "order_leg_request": "dynamic_entry_price_resolver",
    "latency_pass": "dynamic_entry_price_resolver",
    "pre_submit_price_guard_block": "pre_submit_price_guard",
    "pre_submit_liquidity_guard_block": "liquidity_pre_submit_guard_p1",
    "caution_weak_liquidity_entry_block": "caution_weak_liquidity_entry_block",
    "pre_submit_entry_ai_authority_guard_block": "pre_submit_entry_ai_authority_guard",
    "pre_submit_overbought_pullback_guard_block": "overbought_pullback_guard_p1",
    "entry_ai_price_canary_applied": "dynamic_entry_price_resolver",
    "entry_ai_price_canary_fallback": "dynamic_entry_price_resolver",
    "entry_ai_price_canary_skip_order": "dynamic_entry_price_resolver",
    "entry_ai_price_canary_skip_followup": "dynamic_entry_price_resolver",
    "entry_submit_revalidation_warning": "dynamic_entry_price_resolver",
    "entry_submit_revalidation_block": "pre_submit_price_guard",
    "scalp_entry_action_decision_snapshot": "scalp_entry_action_decision_matrix",
    "lifecycle_decision_matrix_runtime_policy": "lifecycle_decision_matrix_runtime",
    "lifecycle_decision_matrix_runtime_effect": "lifecycle_decision_matrix_runtime",
    "entry_order_cancel_requested": "entry_price_execution_quality",
    "entry_order_cancel_confirmed": "entry_price_execution_quality",
    "entry_order_cancel_failed": "entry_price_execution_quality",
    "entry_cancel_wait_attribution": "entry_cancel_wait_attribution",
    "entry_opportunity_recheck_enqueued": "entry_opportunity_recheck_runtime",
    "entry_opportunity_recheck_refresh_attempted": "entry_opportunity_recheck_runtime",
    "entry_opportunity_recheck_fresh_pass": "entry_opportunity_recheck_runtime",
    "entry_opportunity_recheck_normal_buy_reentered": "entry_opportunity_recheck_runtime",
    "entry_opportunity_recheck_blocked": "entry_opportunity_recheck_runtime",
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
    "quote_consistency_observed": "quote_consistency_normalization",
    "quote_consistency_diverged": "quote_consistency_normalization",
    "quote_consistency_safety_exit_applied": "quote_consistency_normalization",
    "scalp_sim_entry_armed": "entry_mechanical_momentum",
    "scalp_sim_entry_ai_price_applied": "dynamic_entry_price_resolver",
    "scalp_sim_entry_ai_price_skip_order": "dynamic_entry_price_resolver",
    "scalp_sim_entry_submit_revalidation_warning": "dynamic_entry_price_resolver",
    "scalp_sim_entry_submit_revalidation_block": "dynamic_entry_price_resolver",
    "scalp_sim_pre_submit_liquidity_guard_would_block": "liquidity_pre_submit_guard_p1",
    "scalp_sim_pre_submit_liquidity_guard_would_pass": "liquidity_pre_submit_guard_p1",
    "scalp_sim_pre_submit_liquidity_guard_unknown": "liquidity_pre_submit_guard_p1",
    "scalp_sim_pre_submit_overbought_guard_would_block": "overbought_pullback_guard_p1",
    "scalp_sim_pre_submit_overbought_guard_would_pass": "overbought_pullback_guard_p1",
    "scalp_sim_buy_order_virtual_pending": "dynamic_entry_price_resolver",
    "scalp_sim_buy_order_assumed_filled": "dynamic_entry_price_resolver",
    "scalp_sim_holding_started": "statistical_action_weight",
    "scalp_sim_scale_in_order_assumed_filled": "scale_in_price_guard",
    "scalp_sim_scale_in_order_unfilled": "scale_in_price_guard",
    "scalp_sim_scale_in_window_expansion": "scalp_sim_scale_in_window_expansion",
    "scalp_sim_sell_order_assumed_filled": "statistical_action_weight",
    "scalp_sim_sell_blocked_zero_qty": "statistical_action_weight",
    "scalp_sim_entry_unpriced": "dynamic_entry_price_resolver",
    "scalp_sim_entry_expired": "dynamic_entry_price_resolver",
    "scalp_sim_duplicate_buy_signal": "entry_mechanical_momentum",
    "scalp_sim_candidate_window_discarded": "entry_mechanical_momentum",
    "scalp_sim_ai_holding_live_call": "scalp_sim_ai_budget_manager",
    "scalp_sim_ai_holding_reuse": "scalp_sim_ai_budget_manager",
    "scalp_sim_ai_holding_deferred": "scalp_sim_ai_budget_manager",
    "sim_ai_budget_exhausted": "scalp_sim_ai_budget_manager",
    "sim_ai_critical_bypass": "scalp_sim_ai_budget_manager",
    "scalp_sim_panic_bottoming_entry_allowed": "panic_lifecycle_actuator",
    "scalp_sim_panic_level1_entry_observed": "panic_lifecycle_actuator",
    "scalp_sim_panic_entry_blocked": "panic_lifecycle_actuator",
    "scalp_sim_panic_scale_in_blocked": "panic_lifecycle_actuator",
    "scalp_sim_panic_action_deduped": "panic_lifecycle_actuator",
    "scalp_sim_partial_sell_order_assumed_filled": "panic_lifecycle_actuator",
    "scalp_sim_panic_context_warning": "panic_lifecycle_actuator",
    "scalp_sim_euphoria_context_noop": "panic_lifecycle_actuator",
    "scalp_sim_euphoria_entry_blocked": "panic_lifecycle_actuator",
    "scalp_sim_euphoria_chase_entry_blocked": "panic_lifecycle_actuator",
    "scalp_sim_euphoria_retest_starter_allowed": "panic_lifecycle_actuator",
    "scalp_sim_euphoria_level1_starter_observed": "panic_lifecycle_actuator",
    "scalp_sim_euphoria_scale_in_blocked": "panic_lifecycle_actuator",
    "scalp_sim_euphoria_partial_profit_assumed_filled": "panic_lifecycle_actuator",
    "scalp_sim_euphoria_partial_profit_unpriced": "panic_lifecycle_actuator",
    "scalp_sim_euphoria_action_deduped": "panic_lifecycle_actuator",
    "swing_probe_entry_candidate": "swing_strategy_discovery_sim",
    "swing_probe_holding_started": "swing_strategy_discovery_sim",
    "swing_probe_exit_signal": "swing_strategy_discovery_sim",
    "swing_probe_sell_order_assumed_filled": "swing_strategy_discovery_sim",
    "swing_probe_scale_in_order_assumed_filled": "swing_strategy_discovery_sim",
    "swing_sim_scale_in_order_assumed_filled": "swing_strategy_discovery_sim",
    "swing_probe_discarded": "swing_strategy_discovery_sim",
    "swing_probe_state_persisted": "swing_strategy_discovery_sim",
    "swing_probe_state_restored": "swing_strategy_discovery_sim",
    "swing_probe_state_empty_overwrite_blocked": "swing_strategy_discovery_sim",
    "swing_reentry_counterfactual_after_loss": "swing_strategy_discovery_sim",
    "swing_same_symbol_loss_reentry_cooldown": "swing_strategy_discovery_sim",
    "swing_same_symbol_loss_reentry_cooldowns_restored": "swing_strategy_discovery_sim",
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

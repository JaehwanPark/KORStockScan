# Observation Source Quality Audit - 2026-06-01

- status: `warning`
- event_count: `406091`
- decision_authority: `source_quality_only`
- runtime_effect: `False`
- forbidden_uses: `runtime_threshold_apply, order_submit, provider_route_change, bot_restart, real_execution_quality_approval`

## Warning Stages
- `scalp_sim_pre_submit_overbought_guard_would_pass` sample=`348` missing=`{'sim_overbought_risk_state': 0.9023}` zero=`{}`
- `scalp_sim_sell_order_assumed_filled` sample=`349` missing=`{'simulated_order': 0.0401}` zero=`{}`

## Invalid Label Findings
- none

## High Volume Stages Without Source-Like Fields
- `soft_stop_whipsaw_confirmation_expired` count=`58` routing=`instrumentation_gap_or_diagnostic_contract_needed`

## Top Stages
- `budget_pass`: `25399`
- `orderbook_stability_observed`: `25395`
- `latency_block`: `25222`
- `strength_momentum_observed`: `23715`
- `blocked_strength_momentum`: `23715`
- `market_regime_prior_observed`: `22832`
- `swing_entry_policy_evaluated`: `22832`
- `swing_entry_micro_context_observed`: `22783`
- `blocked_swing_score_vpw`: `18696`
- `bad_entry_refined_candidate`: `18611`
- `scalp_sim_panic_scale_in_blocked`: `17741`
- `stat_action_decision_snapshot`: `15758`
- `blocked_overbought`: `12671`
- `scalp_sim_panic_level1_partial_skipped_min_remaining`: `12244`
- `scalp_entry_action_decision_snapshot`: `7288`
- `scalp_sim_panic_action_deduped`: `6824`
- `ai_holding_fast_reuse_band`: `6530`
- `holding_flow_override_defer_exit`: `6514`
- `ai_holding_reuse_bypass`: `6504`
- `reversal_add_blocked_reason`: `6454`

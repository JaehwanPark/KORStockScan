# Observation Source Quality Audit - 2026-06-19

- status: `pass`
- event_count: `78448`
- tuning_input_policy: `exclude_defective_rows_not_full_day_raw`
- hard_blocking_excluded_row_count: `0`
- tuning_input_allowed: `True`
- decision_authority: `source_quality_only`
- runtime_effect: `False`
- forbidden_uses: `runtime_threshold_apply, order_submit, provider_route_change, bot_restart, real_execution_quality_approval`

## Warning Stages
- none

## Hard Blocking Row Exclusions
- none

## Invalid Label Findings
- none

## High Volume Stages Without Source-Like Fields
- none

## Unknown Token Findings
- none

## Reviewed Unknown Token Findings
- `latency_block` count=`861` routing=`reviewed_unknown_token_provenance` fields=`latency_strategy_id=514(reviewed_pre_contract_placeholder), latency_position_tag=514(reviewed_pre_contract_placeholder), latency_spread_relief_tag=514(reviewed_pre_contract_placeholder), latency_spread_relief_signal_score=514(reviewed_pre_contract_placeholder), latency_spread_relief_configured_min_signal_score=514(reviewed_pre_contract_placeholder), latency_spread_relief_effective_min_signal_score=514(reviewed_pre_contract_placeholder)`
- `latency_pass` count=`137` routing=`reviewed_unknown_token_provenance` fields=`latency_strategy_id=69(reviewed_pre_contract_placeholder), latency_position_tag=69(reviewed_pre_contract_placeholder), latency_spread_relief_tag=69(reviewed_pre_contract_placeholder), latency_spread_relief_signal_score=69(reviewed_pre_contract_placeholder), latency_spread_relief_configured_min_signal_score=69(reviewed_pre_contract_placeholder), latency_spread_relief_effective_min_signal_score=69(reviewed_pre_contract_placeholder)`
- `lifecycle_decision_matrix_runtime_policy` count=`136` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=5(reviewed_missing_risk_regime_context)`
- `order_leg_request` count=`133` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=5(reviewed_missing_risk_regime_context)`
- `swing_sim_buy_order_assumed_filled` count=`133` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=5(reviewed_missing_risk_regime_context)`
- `swing_sim_order_bundle_assumed_filled` count=`133` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=5(reviewed_missing_risk_regime_context)`
- `scalp_sim_panic_context_warning` count=`106` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=106(reviewed_missing_risk_regime_context), market_risk_state=106(reviewed_missing_risk_regime_context), liquidity_state=106(reviewed_missing_risk_regime_context), risk_regime_epoch_id=106(reviewed_missing_risk_regime_context)`

## Top Stages
- `scalping_scanner_candidate_observed`: `22612`
- `scalping_scanner_real_source_guard_block`: `22612`
- `strength_momentum_observed`: `2125`
- `blocked_strength_momentum`: `2085`
- `scalping_scanner_candidate_promoted`: `1869`
- `bad_entry_refined_candidate`: `1203`
- `swing_probe_discarded`: `1194`
- `stat_action_decision_snapshot`: `1068`
- `budget_pass`: `1025`
- `swing_entry_policy_evaluated`: `1014`
- `orderbook_stability_observed`: `998`
- `swing_entry_micro_context_observed`: `987`
- `scalp_entry_action_decision_snapshot`: `947`
- `market_regime_prior_observed`: `910`
- `scalp_sim_panic_scale_in_blocked`: `910`
- `ai_holding_fast_reuse_band`: `861`
- `latency_block`: `861`
- `ai_holding_reuse_bypass`: `859`
- `ai_holding_review`: `755`
- `scalp_sim_ai_holding_live_call`: `739`

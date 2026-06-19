# Observation Source Quality Audit - 2026-06-19

- status: `pass`
- event_count: `59509`
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
- `latency_block` count=`737` routing=`reviewed_unknown_token_provenance` fields=`latency_strategy_id=514(reviewed_pre_contract_placeholder), latency_position_tag=514(reviewed_pre_contract_placeholder), latency_spread_relief_tag=514(reviewed_pre_contract_placeholder), latency_spread_relief_signal_score=514(reviewed_pre_contract_placeholder), latency_spread_relief_configured_min_signal_score=514(reviewed_pre_contract_placeholder), latency_spread_relief_effective_min_signal_score=514(reviewed_pre_contract_placeholder)`
- `latency_pass` count=`100` routing=`reviewed_unknown_token_provenance` fields=`latency_strategy_id=69(reviewed_pre_contract_placeholder), latency_position_tag=69(reviewed_pre_contract_placeholder), latency_spread_relief_tag=69(reviewed_pre_contract_placeholder), latency_spread_relief_signal_score=69(reviewed_pre_contract_placeholder), latency_spread_relief_configured_min_signal_score=69(reviewed_pre_contract_placeholder), latency_spread_relief_effective_min_signal_score=69(reviewed_pre_contract_placeholder)`
- `lifecycle_decision_matrix_runtime_policy` count=`99` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=5(reviewed_missing_risk_regime_context)`
- `order_leg_request` count=`96` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=5(reviewed_missing_risk_regime_context)`
- `swing_sim_buy_order_assumed_filled` count=`96` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=5(reviewed_missing_risk_regime_context)`
- `swing_sim_order_bundle_assumed_filled` count=`96` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=5(reviewed_missing_risk_regime_context)`
- `scalp_sim_panic_context_warning` count=`93` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=93(reviewed_missing_risk_regime_context), market_risk_state=93(reviewed_missing_risk_regime_context), liquidity_state=93(reviewed_missing_risk_regime_context), risk_regime_epoch_id=93(reviewed_missing_risk_regime_context)`

## Top Stages
- `scalping_scanner_candidate_observed`: `15244`
- `scalping_scanner_real_source_guard_block`: `15244`
- `strength_momentum_observed`: `1875`
- `blocked_strength_momentum`: `1854`
- `scalping_scanner_candidate_promoted`: `1581`
- `bad_entry_refined_candidate`: `1106`
- `stat_action_decision_snapshot`: `1010`
- `swing_probe_discarded`: `987`
- `budget_pass`: `857`
- `scalp_sim_panic_scale_in_blocked`: `857`
- `swing_entry_policy_evaluated`: `846`
- `orderbook_stability_observed`: `837`
- `scalp_entry_action_decision_snapshot`: `830`
- `swing_entry_micro_context_observed`: `826`
- `market_regime_prior_observed`: `811`
- `ai_holding_fast_reuse_band`: `778`
- `ai_holding_reuse_bypass`: `776`
- `latency_block`: `737`
- `ai_holding_review`: `689`
- `scalp_sim_ai_holding_live_call`: `673`

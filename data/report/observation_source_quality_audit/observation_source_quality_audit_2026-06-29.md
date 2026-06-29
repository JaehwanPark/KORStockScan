# Observation Source Quality Audit - 2026-06-29

- status: `pass`
- event_count: `160299`
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
- `scalp_sim_panic_context_warning` count=`2897` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=2897(reviewed_missing_risk_regime_context), market_risk_state=2897(reviewed_missing_risk_regime_context), liquidity_state=2897(reviewed_missing_risk_regime_context), risk_regime_epoch_id=2897(reviewed_missing_risk_regime_context)`
- `scalp_entry_action_decision_snapshot` count=`1168` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=324(reviewed_missing_risk_regime_context)`
- `lifecycle_decision_matrix_runtime_policy` count=`2` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=1(reviewed_missing_risk_regime_context)`
- `order_bundle_submitted` count=`2` routing=`reviewed_unknown_token_provenance` fields=`latency_strategy_id=2(reviewed_pre_contract_placeholder), latency_position_tag=2(reviewed_pre_contract_placeholder), latency_spread_relief_tag=2(reviewed_pre_contract_placeholder), latency_spread_relief_signal_score=2(reviewed_pre_contract_placeholder), latency_spread_relief_configured_min_signal_score=2(reviewed_pre_contract_placeholder), latency_spread_relief_effective_min_signal_score=2(reviewed_pre_contract_placeholder), filled_qty=2(reviewed_pre_contract_placeholder), remaining_qty=2(reviewed_pre_contract_placeholder)`
- `order_leg_request` count=`2` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=1(reviewed_missing_risk_regime_context)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `34475`
- `scalping_scanner_fast_precheck`: `30024`
- `scalping_scanner_runtime_queue_lag`: `21985`
- `scalping_scanner_watching_runtime_skip`: `16225`
- `scalping_scanner_candidate_observed`: `5707`
- `scalping_scanner_real_source_guard_block`: `5707`
- `bad_entry_refined_candidate`: `4463`
- `scalping_scanner_heavy_eval_lag`: `4451`
- `scalping_scanner_runtime_target_attach`: `3204`
- `scalp_sim_panic_context_warning`: `2897`
- `strength_momentum_observed`: `2440`
- `scalping_scanner_candidate_promoted`: `2429`
- `scalp_sim_panic_scale_in_blocked`: `2018`
- `reversal_add_blocked_reason`: `2009`
- `stat_action_decision_snapshot`: `1980`
- `blocked_strength_momentum`: `1495`
- `scalp_sim_scale_in_candidate_funnel`: `1436`
- `scalp_entry_action_decision_snapshot`: `1168`
- `ai_holding_fast_reuse_band`: `1068`
- `ai_holding_reuse_bypass`: `1068`

# Observation Source Quality Audit - 2026-07-03

- status: `pass`
- event_count: `122764`
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
- `stat_action_decision_snapshot` count=`2825` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=7(reviewed_stale_flag_not_available), quote_stale=7(reviewed_stale_flag_not_available)`
- `scalp_sim_panic_context_warning` count=`1584` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=1584(reviewed_missing_risk_regime_context), market_risk_state=1584(reviewed_missing_risk_regime_context), liquidity_state=1584(reviewed_missing_risk_regime_context), risk_regime_epoch_id=1584(reviewed_missing_risk_regime_context)`
- `scalp_entry_action_decision_snapshot` count=`361` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=76(reviewed_missing_risk_regime_context), liquidity_guard_action=1(reviewed_pre_submit_liquidity_not_available)`
- `latency_pass` count=`62` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=62(reviewed_pre_submit_liquidity_not_available)`
- `order_bundle_submitted` count=`60` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=60(reviewed_pre_submit_liquidity_not_available), latency_strategy_id=60(reviewed_pre_contract_placeholder), latency_position_tag=60(reviewed_pre_contract_placeholder), latency_spread_relief_tag=60(reviewed_pre_contract_placeholder), latency_spread_relief_signal_score=60(reviewed_pre_contract_placeholder), latency_spread_relief_configured_min_signal_score=60(reviewed_pre_contract_placeholder), latency_spread_relief_effective_min_signal_score=60(reviewed_pre_contract_placeholder), filled_qty=60(reviewed_pre_contract_placeholder)`
- `order_leg_request` count=`60` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=60(reviewed_pre_submit_liquidity_not_available), risk_regime_context=41(reviewed_missing_risk_regime_context)`
- `order_leg_sent` count=`60` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=60(reviewed_pre_submit_liquidity_not_available)`
- `scale_in_qty_block` count=`23` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=7(reviewed_stale_flag_not_available), quote_stale=7(reviewed_stale_flag_not_available)`
- `sell_order_sent` count=`20` routing=`reviewed_unknown_token_provenance` fields=`sell_order_exchange_resolution_reason=9(reviewed_sell_order_exchange_resolution_not_available)`
- `real_weak_pullback_entry_block` count=`2` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=2(reviewed_pre_submit_liquidity_not_available), risk_regime_context=2(reviewed_missing_risk_regime_context)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `21089`
- `scalping_scanner_fast_precheck`: `17754`
- `scalping_scanner_runtime_queue_lag`: `12742`
- `scalping_scanner_watching_runtime_skip`: `11496`
- `scalping_scanner_runtime_target_attach`: `7584`
- `bad_entry_refined_candidate`: `4764`
- `holding_ws_freshness_blocked`: `3695`
- `scalping_scanner_heavy_eval_lag`: `3335`
- `stat_action_decision_snapshot`: `2825`
- `manual_control_excluded_symbol_blocked`: `2389`
- `ai_holding_fast_reuse_band`: `2364`
- `ai_holding_reuse_bypass`: `2363`
- `ai_holding_review`: `2352`
- `reversal_add_blocked_reason`: `2282`
- `holding_ws_freshness_recovered`: `2102`
- `strength_momentum_observed`: `2029`
- `blocked_strength_momentum`: `1810`
- `scalp_sim_panic_context_warning`: `1584`
- `scalping_scanner_candidate_observed`: `1411`
- `scalping_scanner_real_source_guard_block`: `1411`

# Observation Source Quality Audit - 2026-07-03

- status: `pass`
- event_count: `75534`
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
- `scalp_sim_panic_context_warning` count=`698` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=698(reviewed_missing_risk_regime_context), market_risk_state=698(reviewed_missing_risk_regime_context), liquidity_state=698(reviewed_missing_risk_regime_context), risk_regime_epoch_id=698(reviewed_missing_risk_regime_context)`
- `scalp_entry_action_decision_snapshot` count=`240` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=26(reviewed_missing_risk_regime_context)`
- `latency_pass` count=`39` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=39(reviewed_pre_submit_liquidity_not_available)`
- `order_bundle_submitted` count=`37` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=37(reviewed_pre_submit_liquidity_not_available), latency_strategy_id=37(reviewed_pre_contract_placeholder), latency_position_tag=37(reviewed_pre_contract_placeholder), latency_spread_relief_tag=37(reviewed_pre_contract_placeholder), latency_spread_relief_signal_score=37(reviewed_pre_contract_placeholder), latency_spread_relief_configured_min_signal_score=37(reviewed_pre_contract_placeholder), latency_spread_relief_effective_min_signal_score=37(reviewed_pre_contract_placeholder), filled_qty=37(reviewed_pre_contract_placeholder)`
- `order_leg_request` count=`37` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=37(reviewed_pre_submit_liquidity_not_available), risk_regime_context=23(reviewed_missing_risk_regime_context)`
- `order_leg_sent` count=`37` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=37(reviewed_pre_submit_liquidity_not_available)`
- `sell_order_sent` count=`14` routing=`reviewed_unknown_token_provenance` fields=`sell_order_exchange_resolution_reason=7(reviewed_sell_order_exchange_resolution_not_available)`
- `real_weak_pullback_entry_block` count=`2` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=2(reviewed_pre_submit_liquidity_not_available), risk_regime_context=2(reviewed_missing_risk_regime_context)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `13446`
- `scalping_scanner_fast_precheck`: `11124`
- `scalping_scanner_runtime_queue_lag`: `7790`
- `scalping_scanner_watching_runtime_skip`: `6314`
- `scalping_scanner_runtime_target_attach`: `3965`
- `holding_ws_freshness_blocked`: `3550`
- `bad_entry_refined_candidate`: `2809`
- `scalping_scanner_heavy_eval_lag`: `2322`
- `strength_momentum_observed`: `1583`
- `stat_action_decision_snapshot`: `1573`
- `blocked_strength_momentum`: `1447`
- `ai_holding_fast_reuse_band`: `1414`
- `ai_holding_reuse_bypass`: `1414`
- `ai_holding_review`: `1405`
- `holding_ws_freshness_recovered`: `1389`
- `reversal_add_blocked_reason`: `1206`
- `manual_control_excluded_symbol_blocked`: `1149`
- `rising_missed_scout_upgrade_eval`: `1067`
- `scalp_sim_panic_scale_in_blocked`: `934`
- `scalp_sim_panic_context_warning`: `698`

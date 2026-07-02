# Observation Source Quality Audit - 2026-07-02

- status: `pass`
- event_count: `144149`
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
- `scalp_sim_panic_context_warning` count=`2715` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=2715(reviewed_missing_risk_regime_context), market_risk_state=2715(reviewed_missing_risk_regime_context), liquidity_state=2715(reviewed_missing_risk_regime_context), risk_regime_epoch_id=2715(reviewed_missing_risk_regime_context)`
- `scalp_entry_action_decision_snapshot` count=`665` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=152(reviewed_missing_risk_regime_context)`
- `latency_pass` count=`60` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=52(reviewed_pre_submit_liquidity_not_available)`
- `lifecycle_decision_matrix_runtime_policy` count=`58` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=32(reviewed_missing_risk_regime_context)`
- `order_bundle_submitted` count=`50` routing=`reviewed_unknown_token_provenance` fields=`latency_strategy_id=50(reviewed_pre_contract_placeholder), latency_position_tag=50(reviewed_pre_contract_placeholder), latency_spread_relief_tag=50(reviewed_pre_contract_placeholder), latency_spread_relief_signal_score=50(reviewed_pre_contract_placeholder), latency_spread_relief_configured_min_signal_score=50(reviewed_pre_contract_placeholder), latency_spread_relief_effective_min_signal_score=50(reviewed_pre_contract_placeholder), filled_qty=50(reviewed_pre_contract_placeholder), remaining_qty=50(reviewed_pre_contract_placeholder)`
- `order_leg_request` count=`50` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=47(reviewed_pre_submit_liquidity_not_available), risk_regime_context=28(reviewed_missing_risk_regime_context)`
- `order_leg_sent` count=`50` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=47(reviewed_pre_submit_liquidity_not_available)`
- `sell_order_sent` count=`19` routing=`reviewed_unknown_token_provenance` fields=`sell_order_exchange_resolution_reason=11(reviewed_sell_order_exchange_resolution_not_available)`
- `real_weak_pullback_entry_block` count=`7` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=3(reviewed_missing_risk_regime_context), liquidity_guard_action=3(reviewed_pre_submit_liquidity_not_available)`
- `entry_submit_revalidation_block` count=`1` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=1(reviewed_pre_submit_liquidity_not_available)`
- `entry_submit_revalidation_warning` count=`1` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=1(reviewed_pre_submit_liquidity_not_available)`
- `order_bundle_failed` count=`1` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=1(reviewed_pre_submit_liquidity_not_available)`
- `pre_submit_weak_context_late_entry_guard_block` count=`1` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=1(reviewed_pre_submit_liquidity_not_available)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `27983`
- `scalping_scanner_fast_precheck`: `24991`
- `scalping_scanner_watching_runtime_skip`: `17641`
- `scalping_scanner_runtime_queue_lag`: `16012`
- `bad_entry_refined_candidate`: `4851`
- `scalping_scanner_candidate_observed`: `3335`
- `scalping_scanner_real_source_guard_block`: `3335`
- `stat_action_decision_snapshot`: `3083`
- `scalping_scanner_heavy_eval_lag`: `2992`
- `scalp_sim_panic_context_warning`: `2715`
- `scalping_scanner_runtime_target_attach`: `2556`
- `holding_ws_freshness_blocked`: `2458`
- `reversal_add_blocked_reason`: `2165`
- `ai_holding_fast_reuse_band`: `1857`
- `ai_holding_reuse_bypass`: `1857`
- `ai_holding_review`: `1853`
- `strength_momentum_observed`: `1748`
- `blocked_strength_momentum`: `1489`
- `scalp_sim_scale_in_candidate_funnel`: `1341`
- `holding_ws_freshness_recovered`: `1326`

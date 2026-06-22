# Observation Source Quality Audit - 2026-06-22

- status: `pass`
- event_count: `82700`
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
- `scalp_entry_action_decision_snapshot` count=`984` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=11(reviewed_missing_risk_regime_context), sim_pre_submit_liquidity_guard_action=2(reviewed_sim_liquidity_not_available)`
- `scalp_sim_panic_context_warning` count=`203` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=203(reviewed_missing_risk_regime_context), market_risk_state=203(reviewed_missing_risk_regime_context), liquidity_state=203(reviewed_missing_risk_regime_context), risk_regime_epoch_id=203(reviewed_missing_risk_regime_context)`
- `scalp_sim_buy_order_assumed_filled` count=`193` routing=`reviewed_unknown_token_provenance` fields=`sim_pre_submit_liquidity_guard_action=2(reviewed_sim_liquidity_not_available)`
- `scalp_sim_buy_order_virtual_pending` count=`193` routing=`reviewed_unknown_token_provenance` fields=`sim_pre_submit_liquidity_guard_action=2(reviewed_sim_liquidity_not_available)`
- `scalp_sim_entry_armed` count=`193` routing=`reviewed_unknown_token_provenance` fields=`sim_pre_submit_liquidity_guard_action=2(reviewed_sim_liquidity_not_available)`
- `scalp_sim_holding_started` count=`193` routing=`reviewed_unknown_token_provenance` fields=`sim_pre_submit_liquidity_guard_action=2(reviewed_sim_liquidity_not_available)`
- `scalp_sim_pre_submit_overbought_guard_would_pass` count=`192` routing=`reviewed_unknown_token_provenance` fields=`sim_pre_submit_liquidity_guard_action=2(reviewed_sim_liquidity_not_available)`
- `scalp_sim_sell_order_assumed_filled` count=`116` routing=`reviewed_unknown_token_provenance` fields=`sim_pre_submit_liquidity_guard_action=1(reviewed_sim_liquidity_not_available)`
- `scalp_sim_pre_submit_liquidity_guard_unknown` count=`2` routing=`reviewed_unknown_token_provenance` fields=`sim_pre_submit_liquidity_guard_action=2(reviewed_sim_liquidity_not_available), __stage=2(reviewed_explicit_sim_liquidity_unknown_stage)`
- `order_bundle_submitted` count=`1` routing=`reviewed_unknown_token_provenance` fields=`latency_strategy_id=1(reviewed_pre_contract_placeholder), latency_position_tag=1(reviewed_pre_contract_placeholder), latency_spread_relief_tag=1(reviewed_pre_contract_placeholder), latency_spread_relief_signal_score=1(reviewed_pre_contract_placeholder), latency_spread_relief_configured_min_signal_score=1(reviewed_pre_contract_placeholder), latency_spread_relief_effective_min_signal_score=1(reviewed_pre_contract_placeholder), filled_qty=1(reviewed_pre_contract_placeholder), remaining_qty=1(reviewed_pre_contract_placeholder)`

## Top Stages
- `scalping_scanner_candidate_observed`: `14535`
- `scalping_scanner_real_source_guard_block`: `14533`
- `scalping_scanner_fast_precheck`: `5119`
- `scalping_scanner_runtime_queue_lag`: `4997`
- `scalping_scanner_watching_runtime_skip`: `3957`
- `scalping_scanner_candidate_promoted`: `2273`
- `bad_entry_refined_candidate`: `2037`
- `scalping_scanner_runtime_target_attach`: `1971`
- `stat_action_decision_snapshot`: `1696`
- `scalping_scanner_heavy_eval_lag`: `1656`
- `strength_momentum_observed`: `1586`
- `swing_probe_discarded`: `1413`
- `ai_holding_fast_reuse_band`: `1261`
- `ai_holding_reuse_bypass`: `1261`
- `scalp_sim_ai_holding_live_call`: `1097`
- `ai_holding_review`: `1097`
- `reversal_add_blocked_reason`: `1039`
- `scalp_entry_action_decision_snapshot`: `984`
- `scalp_sim_panic_scale_in_blocked`: `871`
- `budget_pass`: `851`

# Observation Source Quality Audit - 2026-06-23

- status: `pass`
- event_count: `130860`
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
- `scalp_sim_panic_context_warning` count=`2086` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=2086(reviewed_missing_risk_regime_context), market_risk_state=2086(reviewed_missing_risk_regime_context), liquidity_state=2086(reviewed_missing_risk_regime_context), risk_regime_epoch_id=2086(reviewed_missing_risk_regime_context)`
- `scalp_entry_action_decision_snapshot` count=`1333` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=158(reviewed_missing_risk_regime_context), sim_pre_submit_liquidity_guard_action=1(reviewed_sim_liquidity_not_available), entry_adm_cache_token=1(reviewed_entry_adm_bucket_provenance_recorded), entry_adm_bucket_token=1(reviewed_entry_adm_bucket_provenance_recorded), entry_adm_price_resolution_bucket=1(reviewed_entry_adm_bucket_provenance_recorded)`
- `ai_confirmed` count=`618` routing=`reviewed_unknown_token_provenance` fields=`entry_adm_cache_token=1(reviewed_entry_adm_bucket_provenance_recorded), entry_adm_bucket_token=1(reviewed_entry_adm_bucket_provenance_recorded), entry_adm_price_resolution_bucket=1(reviewed_entry_adm_bucket_provenance_recorded)`
- `scalp_sim_buy_order_assumed_filled` count=`212` routing=`reviewed_unknown_token_provenance` fields=`sim_pre_submit_liquidity_guard_action=1(reviewed_sim_liquidity_not_available)`
- `scalp_sim_buy_order_virtual_pending` count=`212` routing=`reviewed_unknown_token_provenance` fields=`sim_pre_submit_liquidity_guard_action=1(reviewed_sim_liquidity_not_available)`
- `scalp_sim_entry_armed` count=`212` routing=`reviewed_unknown_token_provenance` fields=`sim_pre_submit_liquidity_guard_action=1(reviewed_sim_liquidity_not_available)`
- `scalp_sim_holding_started` count=`212` routing=`reviewed_unknown_token_provenance` fields=`sim_pre_submit_liquidity_guard_action=1(reviewed_sim_liquidity_not_available)`
- `scalp_sim_pre_submit_overbought_guard_would_pass` count=`211` routing=`reviewed_unknown_token_provenance` fields=`sim_pre_submit_liquidity_guard_action=1(reviewed_sim_liquidity_not_available)`
- `scalp_sim_sell_order_assumed_filled` count=`157` routing=`reviewed_unknown_token_provenance` fields=`sim_pre_submit_liquidity_guard_action=1(reviewed_sim_liquidity_not_available)`
- `lifecycle_decision_matrix_runtime_policy` count=`49` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=3(reviewed_missing_risk_regime_context)`
- `order_leg_request` count=`46` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=1(reviewed_missing_risk_regime_context)`
- `swing_sim_buy_order_assumed_filled` count=`43` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=1(reviewed_missing_risk_regime_context)`
- `swing_sim_order_bundle_assumed_filled` count=`43` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=1(reviewed_missing_risk_regime_context)`
- `order_bundle_submitted` count=`3` routing=`reviewed_unknown_token_provenance` fields=`latency_strategy_id=3(reviewed_pre_contract_placeholder), latency_position_tag=3(reviewed_pre_contract_placeholder), latency_spread_relief_tag=3(reviewed_pre_contract_placeholder), latency_spread_relief_signal_score=3(reviewed_pre_contract_placeholder), latency_spread_relief_configured_min_signal_score=3(reviewed_pre_contract_placeholder), latency_spread_relief_effective_min_signal_score=3(reviewed_pre_contract_placeholder), filled_qty=3(reviewed_pre_contract_placeholder), remaining_qty=3(reviewed_pre_contract_placeholder)`
- `real_weak_pullback_entry_block` count=`3` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=2(reviewed_missing_risk_regime_context)`
- `scalp_sim_pre_submit_liquidity_guard_unknown` count=`1` routing=`reviewed_unknown_token_provenance` fields=`sim_pre_submit_liquidity_guard_action=1(reviewed_sim_liquidity_not_available), __stage=1(reviewed_explicit_sim_liquidity_unknown_stage)`

## Top Stages
- `scalping_scanner_fast_precheck`: `15467`
- `scalping_scanner_runtime_queue_lag`: `11368`
- `scalping_scanner_watching_runtime_skip`: `11117`
- `scalping_scanner_candidate_observed`: `10264`
- `scalping_scanner_real_source_guard_block`: `10264`
- `scalping_scanner_heavy_eval_lag`: `7689`
- `bad_entry_refined_candidate`: `4085`
- `strength_momentum_observed`: `3485`
- `stat_action_decision_snapshot`: `2666`
- `swing_probe_discarded`: `2549`
- `scalping_scanner_runtime_target_attach`: `2361`
- `budget_pass`: `2154`
- `orderbook_stability_observed`: `2123`
- `scalp_sim_panic_context_warning`: `2086`
- `swing_entry_policy_evaluated`: `2083`
- `latency_block`: `2068`
- `swing_entry_micro_context_observed`: `2052`
- `blocked_swing_score_vpw`: `1996`
- `blocked_strength_momentum`: `1973`
- `market_regime_block`: `1921`

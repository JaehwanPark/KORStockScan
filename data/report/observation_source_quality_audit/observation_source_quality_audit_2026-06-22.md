# Observation Source Quality Audit - 2026-06-22

- status: `pass`
- event_count: `96759`
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
- `scalp_entry_action_decision_snapshot` count=`1166` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=161(reviewed_missing_risk_regime_context), sim_pre_submit_liquidity_guard_action=2(reviewed_sim_liquidity_not_available)`
- `scalp_sim_panic_context_warning` count=`230` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=230(reviewed_missing_risk_regime_context), market_risk_state=230(reviewed_missing_risk_regime_context), liquidity_state=230(reviewed_missing_risk_regime_context), risk_regime_epoch_id=230(reviewed_missing_risk_regime_context)`
- `scalp_sim_buy_order_assumed_filled` count=`206` routing=`reviewed_unknown_token_provenance` fields=`sim_pre_submit_liquidity_guard_action=2(reviewed_sim_liquidity_not_available)`
- `scalp_sim_buy_order_virtual_pending` count=`206` routing=`reviewed_unknown_token_provenance` fields=`sim_pre_submit_liquidity_guard_action=2(reviewed_sim_liquidity_not_available)`
- `scalp_sim_entry_armed` count=`206` routing=`reviewed_unknown_token_provenance` fields=`sim_pre_submit_liquidity_guard_action=2(reviewed_sim_liquidity_not_available)`
- `scalp_sim_holding_started` count=`206` routing=`reviewed_unknown_token_provenance` fields=`sim_pre_submit_liquidity_guard_action=2(reviewed_sim_liquidity_not_available)`
- `scalp_sim_pre_submit_overbought_guard_would_pass` count=`205` routing=`reviewed_unknown_token_provenance` fields=`sim_pre_submit_liquidity_guard_action=2(reviewed_sim_liquidity_not_available)`
- `scalp_sim_sell_order_assumed_filled` count=`116` routing=`reviewed_unknown_token_provenance` fields=`sim_pre_submit_liquidity_guard_action=1(reviewed_sim_liquidity_not_available)`
- `lifecycle_decision_matrix_runtime_policy` count=`72` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=1(reviewed_missing_risk_regime_context)`
- `real_weak_pullback_entry_block` count=`4` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=1(reviewed_missing_risk_regime_context)`
- `scalp_sim_pre_submit_liquidity_guard_unknown` count=`2` routing=`reviewed_unknown_token_provenance` fields=`sim_pre_submit_liquidity_guard_action=2(reviewed_sim_liquidity_not_available), __stage=2(reviewed_explicit_sim_liquidity_unknown_stage)`
- `order_bundle_submitted` count=`1` routing=`reviewed_unknown_token_provenance` fields=`latency_strategy_id=1(reviewed_pre_contract_placeholder), latency_position_tag=1(reviewed_pre_contract_placeholder), latency_spread_relief_tag=1(reviewed_pre_contract_placeholder), latency_spread_relief_signal_score=1(reviewed_pre_contract_placeholder), latency_spread_relief_configured_min_signal_score=1(reviewed_pre_contract_placeholder), latency_spread_relief_effective_min_signal_score=1(reviewed_pre_contract_placeholder), filled_qty=1(reviewed_pre_contract_placeholder), remaining_qty=1(reviewed_pre_contract_placeholder)`

## Top Stages
- `scalping_scanner_candidate_observed`: `14876`
- `scalping_scanner_real_source_guard_block`: `14874`
- `scalping_scanner_fast_precheck`: `6433`
- `scalping_scanner_runtime_queue_lag`: `6243`
- `scalping_scanner_watching_runtime_skip`: `5483`
- `bad_entry_refined_candidate`: `3272`
- `scalping_scanner_runtime_target_attach`: `2625`
- `scalping_scanner_heavy_eval_lag`: `2611`
- `scalping_scanner_candidate_promoted`: `2606`
- `strength_momentum_observed`: `2124`
- `stat_action_decision_snapshot`: `2047`
- `ai_holding_fast_reuse_band`: `1695`
- `ai_holding_reuse_bypass`: `1691`
- `scalp_sim_ai_holding_live_call`: `1520`
- `ai_holding_review`: `1520`
- `swing_probe_discarded`: `1440`
- `scalp_entry_action_decision_snapshot`: `1166`
- `blocked_strength_momentum`: `1040`
- `reversal_add_blocked_reason`: `1039`
- `scalp_sim_panic_scale_in_blocked`: `871`

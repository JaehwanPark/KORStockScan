# Observation Source Quality Audit - 2026-06-30

- status: `pass`
- event_count: `143848`
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
- `scalp_sim_panic_context_warning` count=`2109` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=2109(reviewed_missing_risk_regime_context), market_risk_state=2109(reviewed_missing_risk_regime_context), liquidity_state=2109(reviewed_missing_risk_regime_context), risk_regime_epoch_id=2109(reviewed_missing_risk_regime_context)`
- `scalp_entry_action_decision_snapshot` count=`688` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=60(reviewed_missing_risk_regime_context), liquidity_guard_action=4(reviewed_pre_submit_liquidity_not_available)`
- `latency_pass` count=`130` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=121(reviewed_pre_submit_liquidity_not_available)`
- `lifecycle_decision_matrix_runtime_policy` count=`126` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=48(reviewed_missing_risk_regime_context)`
- `order_bundle_submitted` count=`98` routing=`reviewed_unknown_token_provenance` fields=`latency_strategy_id=98(reviewed_pre_contract_placeholder), latency_position_tag=98(reviewed_pre_contract_placeholder), latency_spread_relief_tag=98(reviewed_pre_contract_placeholder), latency_spread_relief_signal_score=98(reviewed_pre_contract_placeholder), latency_spread_relief_configured_min_signal_score=98(reviewed_pre_contract_placeholder), latency_spread_relief_effective_min_signal_score=98(reviewed_pre_contract_placeholder), filled_qty=98(reviewed_pre_contract_placeholder), remaining_qty=98(reviewed_pre_contract_placeholder)`
- `order_leg_request` count=`98` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=94(reviewed_pre_submit_liquidity_not_available), risk_regime_context=48(reviewed_missing_risk_regime_context)`
- `order_leg_sent` count=`98` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=94(reviewed_pre_submit_liquidity_not_available)`
- `real_weak_pullback_entry_block` count=`28` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=25(reviewed_pre_submit_liquidity_not_available)`
- `entry_submit_revalidation_block` count=`2` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=2(reviewed_pre_submit_liquidity_not_available)`
- `entry_submit_revalidation_warning` count=`2` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=2(reviewed_pre_submit_liquidity_not_available)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `21257`
- `scalping_scanner_fast_precheck`: `17012`
- `scalping_scanner_runtime_queue_lag`: `11936`
- `bad_entry_refined_candidate`: `11486`
- `scalping_scanner_watching_runtime_skip`: `10092`
- `stat_action_decision_snapshot`: `7191`
- `ai_holding_fast_reuse_band`: `6819`
- `ai_holding_reuse_bypass`: `6811`
- `ai_holding_review`: `6810`
- `reversal_add_blocked_reason`: `5046`
- `holding_ws_freshness_recovered`: `4938`
- `scalping_scanner_heavy_eval_lag`: `4245`
- `rising_missed_scout_upgrade_eval`: `2116`
- `scalp_sim_panic_context_warning`: `2109`
- `pyramid_blocked_reason`: `1847`
- `scalp_sim_scale_in_candidate_funnel`: `1171`
- `scalp_sim_panic_scale_in_blocked`: `1075`
- `budget_pass`: `1045`
- `orderbook_stability_observed`: `1044`
- `rising_missed_one_share_entry`: `1031`

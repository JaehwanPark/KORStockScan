# Observation Source Quality Audit - 2026-06-30

- status: `warning`
- event_count: `73109`
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
- `scalp_entry_action_decision_snapshot` count=`495` routing=`source_quality_blocker_or_provenance_backfill` fields=`liquidity_guard_action=4(0.0081)`
- `latency_pass` count=`100` routing=`source_quality_blocker_or_provenance_backfill` fields=`liquidity_guard_action=96(0.96)`
- `order_bundle_submitted` count=`71` routing=`source_quality_blocker_or_provenance_backfill` fields=`liquidity_guard_action=69(0.9718)`
- `order_leg_request` count=`71` routing=`source_quality_blocker_or_provenance_backfill` fields=`liquidity_guard_action=69(0.9718)`
- `order_leg_sent` count=`71` routing=`source_quality_blocker_or_provenance_backfill` fields=`liquidity_guard_action=69(0.9718)`
- `real_weak_pullback_entry_block` count=`26` routing=`source_quality_blocker_or_provenance_backfill` fields=`liquidity_guard_action=25(0.9615)`
- `entry_submit_revalidation_block` count=`2` routing=`source_quality_blocker_or_provenance_backfill` fields=`liquidity_guard_action=2(1.0)`
- `entry_submit_revalidation_warning` count=`2` routing=`source_quality_blocker_or_provenance_backfill` fields=`liquidity_guard_action=2(1.0)`

## Reviewed Unknown Token Findings
- `scalp_entry_action_decision_snapshot` count=`495` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=17(reviewed_missing_risk_regime_context)`
- `scalp_sim_panic_context_warning` count=`375` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=375(reviewed_missing_risk_regime_context), market_risk_state=375(reviewed_missing_risk_regime_context), liquidity_state=375(reviewed_missing_risk_regime_context), risk_regime_epoch_id=375(reviewed_missing_risk_regime_context)`
- `lifecycle_decision_matrix_runtime_policy` count=`97` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=26(reviewed_missing_risk_regime_context)`
- `order_bundle_submitted` count=`71` routing=`reviewed_unknown_token_provenance` fields=`latency_strategy_id=71(reviewed_pre_contract_placeholder), latency_position_tag=71(reviewed_pre_contract_placeholder), latency_spread_relief_tag=71(reviewed_pre_contract_placeholder), latency_spread_relief_signal_score=71(reviewed_pre_contract_placeholder), latency_spread_relief_configured_min_signal_score=71(reviewed_pre_contract_placeholder), latency_spread_relief_effective_min_signal_score=71(reviewed_pre_contract_placeholder), filled_qty=71(reviewed_pre_contract_placeholder), remaining_qty=71(reviewed_pre_contract_placeholder)`
- `order_leg_request` count=`71` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=26(reviewed_missing_risk_regime_context)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `12970`
- `scalping_scanner_fast_precheck`: `9970`
- `scalping_scanner_runtime_queue_lag`: `6696`
- `scalping_scanner_watching_runtime_skip`: `4873`
- `bad_entry_refined_candidate`: `4545`
- `stat_action_decision_snapshot`: `3574`
- `scalping_scanner_heavy_eval_lag`: `3000`
- `ai_holding_fast_reuse_band`: `2608`
- `ai_holding_reuse_bypass`: `2604`
- `ai_holding_review`: `2603`
- `reversal_add_blocked_reason`: `2280`
- `rising_missed_scout_upgrade_eval`: `1706`
- `pyramid_blocked_reason`: `974`
- `scalp_sim_panic_scale_in_blocked`: `828`
- `budget_pass`: `711`
- `orderbook_stability_observed`: `711`
- `rising_missed_one_share_entry`: `702`
- `strength_momentum_observed`: `687`
- `holding_ws_freshness_recovered`: `679`
- `latency_block`: `611`

# Observation Source Quality Audit - 2026-07-02

- status: `warning`
- event_count: `105490`
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
- `sell_order_sent` count=`17` routing=`source_quality_blocker_or_provenance_backfill` fields=`sell_order_exchange_resolution_reason=9(0.5294)`

## Reviewed Unknown Token Findings
- `scalp_sim_panic_context_warning` count=`666` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=666(reviewed_missing_risk_regime_context), market_risk_state=666(reviewed_missing_risk_regime_context), liquidity_state=666(reviewed_missing_risk_regime_context), risk_regime_epoch_id=666(reviewed_missing_risk_regime_context)`
- `scalp_entry_action_decision_snapshot` count=`523` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=54(reviewed_missing_risk_regime_context)`
- `latency_pass` count=`49` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=43(reviewed_pre_submit_liquidity_not_available)`
- `lifecycle_decision_matrix_runtime_policy` count=`47` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=21(reviewed_missing_risk_regime_context)`
- `order_bundle_submitted` count=`40` routing=`reviewed_unknown_token_provenance` fields=`latency_strategy_id=40(reviewed_pre_contract_placeholder), latency_position_tag=40(reviewed_pre_contract_placeholder), latency_spread_relief_tag=40(reviewed_pre_contract_placeholder), latency_spread_relief_signal_score=40(reviewed_pre_contract_placeholder), latency_spread_relief_configured_min_signal_score=40(reviewed_pre_contract_placeholder), latency_spread_relief_effective_min_signal_score=40(reviewed_pre_contract_placeholder), filled_qty=40(reviewed_pre_contract_placeholder), remaining_qty=40(reviewed_pre_contract_placeholder)`
- `order_leg_request` count=`40` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=38(reviewed_pre_submit_liquidity_not_available), risk_regime_context=18(reviewed_missing_risk_regime_context)`
- `order_leg_sent` count=`40` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=38(reviewed_pre_submit_liquidity_not_available)`
- `real_weak_pullback_entry_block` count=`6` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=3(reviewed_pre_submit_liquidity_not_available), risk_regime_context=2(reviewed_missing_risk_regime_context)`
- `entry_submit_revalidation_block` count=`1` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=1(reviewed_pre_submit_liquidity_not_available)`
- `entry_submit_revalidation_warning` count=`1` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=1(reviewed_pre_submit_liquidity_not_available)`
- `order_bundle_failed` count=`1` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=1(reviewed_pre_submit_liquidity_not_available)`
- `pre_submit_weak_context_late_entry_guard_block` count=`1` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=1(reviewed_pre_submit_liquidity_not_available)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `21593`
- `scalping_scanner_fast_precheck`: `19145`
- `scalping_scanner_watching_runtime_skip`: `12717`
- `scalping_scanner_runtime_queue_lag`: `11308`
- `bad_entry_refined_candidate`: `3269`
- `scalping_scanner_heavy_eval_lag`: `2448`
- `holding_ws_freshness_blocked`: `2437`
- `stat_action_decision_snapshot`: `2226`
- `scalping_scanner_candidate_observed`: `2111`
- `scalping_scanner_real_source_guard_block`: `2111`
- `scalping_scanner_runtime_target_attach`: `1353`
- `ai_holding_fast_reuse_band`: `1347`
- `ai_holding_reuse_bypass`: `1347`
- `ai_holding_review`: `1344`
- `reversal_add_blocked_reason`: `1334`
- `strength_momentum_observed`: `1253`
- `holding_ws_freshness_recovered`: `1177`
- `blocked_strength_momentum`: `1099`
- `scalp_sim_panic_scale_in_blocked`: `1027`
- `exit_signal`: `759`

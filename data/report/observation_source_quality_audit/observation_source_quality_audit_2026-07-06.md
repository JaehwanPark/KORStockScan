# Observation Source Quality Audit - 2026-07-06

- status: `warning`
- event_count: `36603`
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
- `scalping_scanner_watching_runtime_skip` count=`3294` routing=`source_quality_blocker_or_provenance_backfill` fields=`minute_candle_context_quality=3(0.0009), tick_context_quality=3(0.0009)`
- `scalp_entry_action_decision_snapshot` count=`258` routing=`source_quality_blocker_or_provenance_backfill` fields=`entry_score_source=26(0.1008), entry_score_excluded_reason=26(0.1008)`
- `ai_confirmed_terminal_no_budget` count=`148` routing=`source_quality_blocker_or_provenance_backfill` fields=`entry_score_source=43(0.2905), entry_score_excluded_reason=43(0.2905)`
- `blocked_ai_score` count=`141` routing=`source_quality_blocker_or_provenance_backfill` fields=`entry_score_source=43(0.305), entry_score_excluded_reason=43(0.305)`
- `early_accel_recheck_evaluated` count=`31` routing=`source_quality_blocker_or_provenance_backfill` fields=`tick_accel_source=31(1.0), tick_context_quality=31(1.0), minute_candle_context_quality=31(1.0)`
- `early_accel_recheck_skipped` count=`31` routing=`source_quality_blocker_or_provenance_backfill` fields=`tick_accel_source=31(1.0), tick_context_quality=31(1.0), minute_candle_context_quality=31(1.0)`
- `ai_numeric_consistency_recheck_evaluated` count=`15` routing=`source_quality_blocker_or_provenance_backfill` fields=`minute_candle_context_quality=1(0.0667)`
- `ai_numeric_consistency_recheck_skipped` count=`15` routing=`source_quality_blocker_or_provenance_backfill` fields=`minute_candle_context_quality=1(0.0667)`

## Reviewed Unknown Token Findings
- `scalping_scanner_watching_runtime_skip` count=`3294` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=3(reviewed_stale_flag_not_available)`
- `stat_action_decision_snapshot` count=`671` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=132(reviewed_stale_flag_not_available), quote_stale=132(reviewed_stale_flag_not_available)`
- `scalp_sim_panic_context_warning` count=`310` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=310(reviewed_missing_risk_regime_context), market_risk_state=310(reviewed_missing_risk_regime_context), liquidity_state=310(reviewed_missing_risk_regime_context), risk_regime_epoch_id=310(reviewed_missing_risk_regime_context)`
- `scalp_entry_action_decision_snapshot` count=`258` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=5(reviewed_missing_risk_regime_context)`
- `latency_pass` count=`17` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=14(reviewed_pre_submit_liquidity_not_available)`
- `order_bundle_submitted` count=`14` routing=`reviewed_unknown_token_provenance` fields=`latency_strategy_id=14(reviewed_pre_contract_placeholder), latency_position_tag=14(reviewed_pre_contract_placeholder), latency_spread_relief_tag=14(reviewed_pre_contract_placeholder), latency_spread_relief_signal_score=14(reviewed_pre_contract_placeholder), latency_spread_relief_configured_min_signal_score=14(reviewed_pre_contract_placeholder), latency_spread_relief_effective_min_signal_score=14(reviewed_pre_contract_placeholder), filled_qty=14(reviewed_pre_contract_placeholder), remaining_qty=14(reviewed_pre_contract_placeholder)`
- `order_leg_request` count=`14` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=12(reviewed_pre_submit_liquidity_not_available), risk_regime_context=5(reviewed_missing_risk_regime_context)`
- `order_leg_sent` count=`14` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=12(reviewed_pre_submit_liquidity_not_available)`
- `sell_order_sent` count=`10` routing=`reviewed_unknown_token_provenance` fields=`sell_order_exchange_resolution_reason=1(reviewed_sell_order_exchange_resolution_not_available)`
- `scale_in_qty_block` count=`7` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=5(reviewed_stale_flag_not_available), quote_stale=5(reviewed_stale_flag_not_available)`
- `real_weak_pullback_entry_block` count=`2` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=2(reviewed_pre_submit_liquidity_not_available)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `7289`
- `scalping_scanner_fast_precheck`: `6111`
- `scalping_scanner_runtime_queue_lag`: `3645`
- `scalping_scanner_watching_runtime_skip`: `3294`
- `scalping_scanner_runtime_target_attach`: `2070`
- `scalping_scanner_heavy_eval_lag`: `1178`
- `bad_entry_refined_candidate`: `1088`
- `holding_ws_freshness_blocked`: `913`
- `rising_missed_scout_upgrade_eval`: `756`
- `manual_control_excluded_symbol_blocked`: `738`
- `stat_action_decision_snapshot`: `671`
- `ai_holding_fast_reuse_band`: `564`
- `ai_holding_reuse_bypass`: `552`
- `ai_holding_review`: `552`
- `budget_pass`: `424`
- `orderbook_stability_observed`: `424`
- `rising_missed_one_share_entry`: `414`
- `latency_block`: `407`
- `scale_in_feature_context_refresh`: `369`
- `strength_momentum_observed`: `347`

# Observation Source Quality Audit - 2026-07-06

- status: `warning`
- event_count: `93645`
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
- `blocked_ai_score` count=`294` routing=`source_quality_blocker_or_provenance_backfill` fields=`entry_score_source=74(0.2517), entry_score_excluded_reason=74(0.2517), score_prior_band=49(0.1667), score_prior_confidence=49(0.1667)`
- `soft_stop_micro_grace` count=`41` routing=`source_quality_blocker_or_provenance_backfill` fields=`soft_stop_dynamic_grace_score_prior_band=7(0.1707)`

## Reviewed Unknown Token Findings
- `scalping_scanner_watching_runtime_skip` count=`10829` routing=`reviewed_unknown_token_provenance` fields=`minute_candle_context_quality=3(reviewed_runtime_skip_context_not_evaluated), tick_context_quality=3(reviewed_runtime_skip_context_not_evaluated), tick_context_stale=3(reviewed_stale_flag_not_available)`
- `stat_action_decision_snapshot` count=`1994` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=158(reviewed_stale_flag_not_available), quote_stale=158(reviewed_stale_flag_not_available)`
- `ai_holding_review` count=`1533` routing=`reviewed_unknown_token_provenance` fields=`holding_score_preflight_source_quality=658(reviewed_holding_score_preflight_not_available)`
- `scalp_sim_panic_context_warning` count=`1438` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=1438(reviewed_missing_risk_regime_context), market_risk_state=1438(reviewed_missing_risk_regime_context), liquidity_state=1438(reviewed_missing_risk_regime_context), risk_regime_epoch_id=1438(reviewed_missing_risk_regime_context)`
- `scalp_entry_action_decision_snapshot` count=`529` routing=`reviewed_unknown_token_provenance` fields=`holding_exit_matrix_score_prior_band=139(reviewed_score_prior_neutral_unknown_not_decision_input), risk_regime_context=79(reviewed_missing_risk_regime_context), entry_score_source=48(reviewed_entry_score_source_not_available), entry_score_excluded_reason=48(reviewed_entry_score_source_not_available), score_prior_band=46(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=46(reviewed_score_prior_neutral_unknown_not_decision_input)`
- `ai_confirmed_terminal_no_budget` count=`314` routing=`reviewed_unknown_token_provenance` fields=`entry_score_source=74(reviewed_entry_score_source_not_available), entry_score_excluded_reason=74(reviewed_entry_score_source_not_available), score_prior_band=49(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=49(reviewed_score_prior_neutral_unknown_not_decision_input)`
- `ai_numeric_consistency_recheck_evaluated` count=`63` routing=`reviewed_unknown_token_provenance` fields=`minute_candle_context_quality=17(reviewed_unusable_micro_context_not_available)`
- `ai_numeric_consistency_recheck_skipped` count=`63` routing=`reviewed_unknown_token_provenance` fields=`minute_candle_context_quality=17(reviewed_unusable_micro_context_not_available)`
- `early_accel_recheck_evaluated` count=`56` routing=`reviewed_unknown_token_provenance` fields=`tick_accel_source=56(reviewed_unusable_micro_context_not_available), tick_context_quality=56(reviewed_unusable_micro_context_not_available), minute_candle_context_quality=56(reviewed_unusable_micro_context_not_available)`
- `early_accel_recheck_skipped` count=`56` routing=`reviewed_unknown_token_provenance` fields=`tick_accel_source=56(reviewed_unusable_micro_context_not_available), tick_context_quality=56(reviewed_unusable_micro_context_not_available), minute_candle_context_quality=56(reviewed_unusable_micro_context_not_available)`
- `latency_pass` count=`36` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=33(reviewed_pre_submit_liquidity_not_available)`
- `order_bundle_submitted` count=`33` routing=`reviewed_unknown_token_provenance` fields=`latency_strategy_id=33(reviewed_pre_contract_placeholder), latency_position_tag=33(reviewed_pre_contract_placeholder), latency_spread_relief_tag=33(reviewed_pre_contract_placeholder), latency_spread_relief_signal_score=33(reviewed_pre_contract_placeholder), latency_spread_relief_configured_min_signal_score=33(reviewed_pre_contract_placeholder), latency_spread_relief_effective_min_signal_score=33(reviewed_pre_contract_placeholder), filled_qty=33(reviewed_pre_contract_placeholder), remaining_qty=33(reviewed_pre_contract_placeholder)`
- `order_leg_request` count=`33` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=31(reviewed_pre_submit_liquidity_not_available), risk_regime_context=19(reviewed_missing_risk_regime_context)`
- `order_leg_sent` count=`33` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=31(reviewed_pre_submit_liquidity_not_available)`
- `scale_in_qty_block` count=`22` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=13(reviewed_stale_flag_not_available), quote_stale=13(reviewed_stale_flag_not_available)`
- `sell_order_sent` count=`19` routing=`reviewed_unknown_token_provenance` fields=`sell_order_exchange_resolution_reason=7(reviewed_sell_order_exchange_resolution_not_available)`
- `loss_fallback_probe` count=`11` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=1(reviewed_stale_flag_not_available), quote_stale=1(reviewed_stale_flag_not_available)`
- `real_weak_pullback_entry_block` count=`2` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=2(reviewed_pre_submit_liquidity_not_available)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `18646`
- `scalping_scanner_fast_precheck`: `15870`
- `scalping_scanner_watching_runtime_skip`: `10829`
- `scalping_scanner_runtime_queue_lag`: `10069`
- `scalping_scanner_runtime_target_attach`: `5371`
- `bad_entry_refined_candidate`: `2789`
- `scalping_scanner_heavy_eval_lag`: `2776`
- `manual_control_excluded_symbol_blocked`: `2353`
- `stat_action_decision_snapshot`: `1994`
- `ai_holding_fast_reuse_band`: `1550`
- `ai_holding_reuse_bypass`: `1536`
- `ai_holding_review`: `1533`
- `scalp_sim_panic_context_warning`: `1438`
- `scale_in_feature_context_refresh`: `1233`
- `rising_missed_scout_upgrade_eval`: `994`
- `strength_momentum_observed`: `982`
- `holding_ws_freshness_blocked`: `934`
- `blocked_strength_momentum`: `856`
- `scalp_sim_scale_in_candidate_funnel`: `702`
- `budget_pass`: `658`

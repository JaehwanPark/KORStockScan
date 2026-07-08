# Observation Source Quality Audit - 2026-07-08

- status: `pass`
- event_count: `105913`
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
- `stat_action_decision_snapshot` count=`2071` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=144(reviewed_stale_flag_not_available), quote_stale=144(reviewed_stale_flag_not_available)`
- `scalp_sim_panic_context_warning` count=`1609` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=1609(reviewed_missing_risk_regime_context), market_risk_state=1609(reviewed_missing_risk_regime_context), liquidity_state=1609(reviewed_missing_risk_regime_context), risk_regime_epoch_id=1609(reviewed_missing_risk_regime_context)`
- `ai_holding_review` count=`1460` routing=`reviewed_unknown_token_provenance` fields=`holding_score_preflight_source_quality=1423(reviewed_holding_score_preflight_not_available)`
- `scalp_entry_action_decision_snapshot` count=`765` routing=`reviewed_unknown_token_provenance` fields=`holding_exit_matrix_score_prior_band=568(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_band=175(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=175(reviewed_score_prior_neutral_unknown_not_decision_input), risk_regime_context=168(reviewed_missing_risk_regime_context), entry_score_source=29(reviewed_entry_score_source_not_available), entry_score_excluded_reason=29(reviewed_entry_score_source_not_available), block_reason=22(reviewed_entry_block_source_quality_unknown_provenance), liquidity_guard_action=1(reviewed_pre_submit_liquidity_not_available)`
- `ai_confirmed_terminal_no_budget` count=`398` routing=`reviewed_unknown_token_provenance` fields=`score_prior_band=180(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=180(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=34(reviewed_entry_score_source_not_available), entry_score_excluded_reason=34(reviewed_entry_score_source_not_available)`
- `latency_block` count=`368` routing=`reviewed_unknown_token_provenance` fields=`latency_spread_relief_signal_score_source=368(reviewed_pre_contract_placeholder), latency_spread_relief_signal_source_quality_state=368(reviewed_pre_contract_placeholder), latency_spread_relief_candidate_ai_score=368(reviewed_pre_contract_placeholder), latency_spread_relief_candidate_ai_score_source=368(reviewed_pre_contract_placeholder), latency_spread_block_bucket=368(reviewed_pre_contract_placeholder), latency_spread_block_price_bucket=368(reviewed_pre_contract_placeholder), latency_spread_block_signal_context_bucket=368(reviewed_pre_contract_placeholder), latency_spread_block_spread_bps=368(reviewed_pre_contract_placeholder)`
- `blocked_ai_score` count=`307` routing=`reviewed_unknown_token_provenance` fields=`score_prior_band=180(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=180(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=34(reviewed_entry_score_source_not_available), entry_score_excluded_reason=34(reviewed_entry_score_source_not_available)`
- `soft_stop_micro_grace` count=`120` routing=`reviewed_unknown_token_provenance` fields=`soft_stop_dynamic_grace_score_prior_band=39(reviewed_score_prior_neutral_unknown_not_decision_input)`
- `loss_fallback_probe` count=`69` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=32(reviewed_stale_flag_not_available), quote_stale=32(reviewed_stale_flag_not_available)`
- `real_weak_ai_micro_entry_block` count=`66` routing=`reviewed_unknown_token_provenance` fields=`reason=61(reviewed_entry_block_source_quality_unknown_provenance), block_reason=61(reviewed_entry_block_source_quality_unknown_provenance)`
- `early_accel_recheck_evaluated` count=`59` routing=`reviewed_unknown_token_provenance` fields=`tick_accel_source=59(reviewed_unusable_micro_context_not_available), tick_context_quality=59(reviewed_unusable_micro_context_not_available), minute_candle_context_quality=59(reviewed_unusable_micro_context_not_available)`
- `early_accel_recheck_skipped` count=`59` routing=`reviewed_unknown_token_provenance` fields=`tick_accel_source=59(reviewed_unusable_micro_context_not_available), tick_context_quality=59(reviewed_unusable_micro_context_not_available), minute_candle_context_quality=59(reviewed_unusable_micro_context_not_available)`
- `order_leg_request` count=`49` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=30(reviewed_missing_risk_regime_context), liquidity_guard_action=19(reviewed_pre_submit_liquidity_not_available)`
- `order_leg_sent` count=`49` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=19(reviewed_pre_submit_liquidity_not_available)`
- `scale_in_qty_block` count=`38` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=27(reviewed_stale_flag_not_available), quote_stale=27(reviewed_stale_flag_not_available)`
- `order_bundle_submitted` count=`25` routing=`reviewed_unknown_token_provenance` fields=`latency_danger_reasons=25(reviewed_pre_contract_placeholder), latency_danger_detail_reason=25(reviewed_pre_contract_placeholder), latency_danger_source_quality_state=25(reviewed_pre_contract_placeholder), latency_danger_reason_taxonomy_gap=25(reviewed_pre_contract_placeholder), latency_danger_max_ws_age_ms_for_caution=25(reviewed_pre_contract_placeholder), latency_danger_max_ws_jitter_ms_for_caution=25(reviewed_pre_contract_placeholder), latency_danger_max_spread_ratio_for_caution=25(reviewed_pre_contract_placeholder), latency_danger_guard_max_spread_ratio=25(reviewed_pre_contract_placeholder)`
- `latency_pass` count=`23` routing=`reviewed_unknown_token_provenance` fields=`latency_danger_detail_reason=23(reviewed_pre_contract_placeholder), latency_danger_source_quality_state=23(reviewed_pre_contract_placeholder), latency_danger_reason_taxonomy_gap=23(reviewed_pre_contract_placeholder), latency_danger_max_ws_age_ms_for_caution=23(reviewed_pre_contract_placeholder), latency_danger_max_ws_jitter_ms_for_caution=23(reviewed_pre_contract_placeholder), latency_danger_max_spread_ratio_for_caution=23(reviewed_pre_contract_placeholder), latency_danger_guard_max_spread_ratio=23(reviewed_pre_contract_placeholder), latency_spread_relief_signal_score_source=23(reviewed_pre_contract_placeholder)`
- `sell_order_sent` count=`20` routing=`reviewed_unknown_token_provenance` fields=`sell_order_exchange_resolution_reason=8(reviewed_sell_order_exchange_resolution_not_available)`
- `scale_in_price_guard_block` count=`7` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=1(reviewed_stale_flag_not_available), quote_stale=1(reviewed_stale_flag_not_available)`

## Top Stages
- `scalping_scanner_candidate_observed`: `15424`
- `scalping_scanner_real_source_guard_block`: `15424`
- `scalping_scanner_promotion_latency_trace`: `11510`
- `scalping_scanner_fast_precheck`: `9564`
- `scalping_scanner_runtime_target_attach`: `7307`
- `scalping_scanner_watching_runtime_skip`: `7068`
- `scalping_scanner_runtime_queue_lag`: `6066`
- `bad_entry_refined_candidate`: `2979`
- `stat_action_decision_snapshot`: `2071`
- `manual_control_excluded_symbol_blocked`: `1951`
- `scalping_scanner_heavy_eval_lag`: `1946`
- `scalp_sim_panic_context_warning`: `1609`
- `ai_holding_fast_reuse_band`: `1491`
- `ai_holding_reuse_bypass`: `1474`
- `ai_holding_review`: `1460`
- `holding_ws_freshness_blocked`: `1326`
- `strength_momentum_observed`: `1099`
- `blocked_strength_momentum`: `972`
- `scale_in_feature_context_refresh`: `885`
- `scalp_sim_panic_scale_in_blocked`: `842`

# Observation Source Quality Audit - 2026-07-08

- status: `fail`
- event_count: `45777`
- tuning_input_policy: `exclude_defective_rows_not_full_day_raw`
- hard_blocking_excluded_row_count: `3`
- tuning_input_allowed: `False`
- decision_authority: `source_quality_only`
- runtime_effect: `False`
- forbidden_uses: `runtime_threshold_apply, order_submit, provider_route_change, bot_restart, real_execution_quality_approval`

## Warning Stages
- `score65_74_recovery_probe_blocked` sample=`57` missing=`{}` zero=`{}`
- `early_accel_strong_bundle_recheck_evaluated` sample=`44` missing=`{}` zero=`{}`
- `early_accel_strong_bundle_recheck_skipped` sample=`16` missing=`{}` zero=`{}`

## Hard Blocking Row Exclusions
- line=`45759` stage=`early_accel_strong_bundle_recheck_evaluated` code=`477850` missing=`[]` zero=`[]` invalid=`['tick_aggressor_pressure_usable_contract']`
- line=`45760` stage=`early_accel_strong_bundle_recheck_skipped` code=`477850` missing=`[]` zero=`[]` invalid=`['tick_aggressor_pressure_usable_contract']`
- line=`45761` stage=`score65_74_recovery_probe_blocked` code=`477850` missing=`[]` zero=`[]` invalid=`['tick_aggressor_pressure_usable_contract']`

## Invalid Label Findings
- none

## High Volume Stages Without Source-Like Fields
- none

## Unknown Token Findings
- `scalp_entry_action_decision_snapshot` count=`531` routing=`source_quality_blocker_or_provenance_backfill` fields=`block_reason=4(0.0075)`
- `real_weak_ai_micro_entry_block` count=`10` routing=`source_quality_blocker_or_provenance_backfill` fields=`reason=5(0.5), block_reason=5(0.5)`

## Reviewed Unknown Token Findings
- `stat_action_decision_snapshot` count=`1344` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=117(reviewed_stale_flag_not_available), quote_stale=117(reviewed_stale_flag_not_available)`
- `ai_holding_review` count=`946` routing=`reviewed_unknown_token_provenance` fields=`holding_score_preflight_source_quality=909(reviewed_holding_score_preflight_not_available)`
- `scalp_entry_action_decision_snapshot` count=`531` routing=`reviewed_unknown_token_provenance` fields=`holding_exit_matrix_score_prior_band=414(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_band=109(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=109(reviewed_score_prior_neutral_unknown_not_decision_input), risk_regime_context=47(reviewed_missing_risk_regime_context), entry_score_source=16(reviewed_entry_score_source_not_available), entry_score_excluded_reason=16(reviewed_entry_score_source_not_available), liquidity_guard_action=1(reviewed_pre_submit_liquidity_not_available)`
- `scalp_sim_panic_context_warning` count=`488` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=488(reviewed_missing_risk_regime_context), market_risk_state=488(reviewed_missing_risk_regime_context), liquidity_state=488(reviewed_missing_risk_regime_context), risk_regime_epoch_id=488(reviewed_missing_risk_regime_context)`
- `ai_confirmed_terminal_no_budget` count=`298` routing=`reviewed_unknown_token_provenance` fields=`score_prior_band=114(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=114(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=21(reviewed_entry_score_source_not_available), entry_score_excluded_reason=21(reviewed_entry_score_source_not_available)`
- `blocked_ai_score` count=`222` routing=`reviewed_unknown_token_provenance` fields=`score_prior_band=114(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=114(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=21(reviewed_entry_score_source_not_available), entry_score_excluded_reason=21(reviewed_entry_score_source_not_available)`
- `latency_block` count=`203` routing=`reviewed_unknown_token_provenance` fields=`latency_danger_detail_reason=187(reviewed_pre_contract_placeholder), latency_danger_source_quality_state=187(reviewed_pre_contract_placeholder), latency_danger_reason_taxonomy_gap=187(reviewed_pre_contract_placeholder), latency_danger_max_ws_age_ms_for_caution=187(reviewed_pre_contract_placeholder), latency_danger_max_ws_jitter_ms_for_caution=187(reviewed_pre_contract_placeholder), latency_danger_max_spread_ratio_for_caution=187(reviewed_pre_contract_placeholder), latency_danger_guard_max_spread_ratio=187(reviewed_pre_contract_placeholder), latency_relief_attempted=187(reviewed_pre_contract_placeholder)`
- `soft_stop_micro_grace` count=`106` routing=`reviewed_unknown_token_provenance` fields=`soft_stop_dynamic_grace_score_prior_band=26(reviewed_score_prior_neutral_unknown_not_decision_input)`
- `loss_fallback_probe` count=`60` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=32(reviewed_stale_flag_not_available), quote_stale=32(reviewed_stale_flag_not_available)`
- `early_accel_recheck_evaluated` count=`39` routing=`reviewed_unknown_token_provenance` fields=`tick_accel_source=39(reviewed_unusable_micro_context_not_available), tick_context_quality=39(reviewed_unusable_micro_context_not_available), minute_candle_context_quality=39(reviewed_unusable_micro_context_not_available)`
- `early_accel_recheck_skipped` count=`39` routing=`reviewed_unknown_token_provenance` fields=`tick_accel_source=39(reviewed_unusable_micro_context_not_available), tick_context_quality=39(reviewed_unusable_micro_context_not_available), minute_candle_context_quality=39(reviewed_unusable_micro_context_not_available)`
- `order_leg_request` count=`38` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=19(reviewed_pre_submit_liquidity_not_available), risk_regime_context=19(reviewed_missing_risk_regime_context)`
- `order_leg_sent` count=`38` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=19(reviewed_pre_submit_liquidity_not_available)`
- `latency_pass` count=`23` routing=`reviewed_unknown_token_provenance` fields=`latency_danger_detail_reason=23(reviewed_pre_contract_placeholder), latency_danger_source_quality_state=23(reviewed_pre_contract_placeholder), latency_danger_reason_taxonomy_gap=23(reviewed_pre_contract_placeholder), latency_danger_max_ws_age_ms_for_caution=23(reviewed_pre_contract_placeholder), latency_danger_max_ws_jitter_ms_for_caution=23(reviewed_pre_contract_placeholder), latency_danger_max_spread_ratio_for_caution=23(reviewed_pre_contract_placeholder), latency_danger_guard_max_spread_ratio=23(reviewed_pre_contract_placeholder), latency_relief_attempted=23(reviewed_pre_contract_placeholder)`
- `order_bundle_submitted` count=`19` routing=`reviewed_unknown_token_provenance` fields=`latency_danger_reasons=19(reviewed_pre_contract_placeholder), latency_danger_detail_reason=19(reviewed_pre_contract_placeholder), latency_danger_source_quality_state=19(reviewed_pre_contract_placeholder), latency_danger_reason_taxonomy_gap=19(reviewed_pre_contract_placeholder), latency_danger_max_ws_age_ms_for_caution=19(reviewed_pre_contract_placeholder), latency_danger_max_ws_jitter_ms_for_caution=19(reviewed_pre_contract_placeholder), latency_danger_max_spread_ratio_for_caution=19(reviewed_pre_contract_placeholder), latency_danger_guard_max_spread_ratio=19(reviewed_pre_contract_placeholder)`
- `scale_in_qty_block` count=`19` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=14(reviewed_stale_flag_not_available), quote_stale=14(reviewed_stale_flag_not_available)`
- `sell_order_sent` count=`17` routing=`reviewed_unknown_token_provenance` fields=`sell_order_exchange_resolution_reason=5(reviewed_sell_order_exchange_resolution_not_available)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `6818`
- `scalping_scanner_fast_precheck`: `5620`
- `scalping_scanner_watching_runtime_skip`: `4196`
- `scalping_scanner_runtime_queue_lag`: `3383`
- `scalping_scanner_runtime_target_attach`: `3217`
- `bad_entry_refined_candidate`: `1806`
- `stat_action_decision_snapshot`: `1344`
- `scalping_scanner_heavy_eval_lag`: `1198`
- `manual_control_excluded_symbol_blocked`: `1035`
- `ai_holding_fast_reuse_band`: `971`
- `ai_holding_reuse_bypass`: `956`
- `ai_holding_review`: `946`
- `holding_ws_freshness_blocked`: `829`
- `scalping_scanner_candidate_observed`: `790`
- `scalping_scanner_real_source_guard_block`: `790`
- `strength_momentum_observed`: `789`
- `blocked_strength_momentum`: `705`
- `scalp_sim_panic_scale_in_blocked`: `660`
- `scalp_entry_action_decision_snapshot`: `531`
- `scalp_sim_panic_context_warning`: `488`

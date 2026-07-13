# Observation Source Quality Audit - 2026-07-13

- status: `pass`
- event_count: `114448`
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
- `scalping_scanner_fast_precheck` count=`8841` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_submit_safety_backoff_reason=19(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `stat_action_decision_snapshot` count=`532` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=37(reviewed_stale_flag_not_available), quote_stale=37(reviewed_stale_flag_not_available), shallow_tick_context_stale=32(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=32(reviewed_shallow_stale_flag_not_available)`
- `rising_missed_scout_quality_guard_blocked` count=`350` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_submit_safety_backoff_reason=45(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `ai_holding_review` count=`252` routing=`reviewed_unknown_token_provenance` fields=`holding_score_preflight_source_quality=246(reviewed_holding_score_preflight_not_available), entry_order_flow_status=54(reviewed_entry_order_flow_not_available)`
- `scalp_entry_action_decision_snapshot` count=`185` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=111(reviewed_entry_order_flow_not_available), holding_exit_matrix_score_prior_band=94(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_band=41(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=41(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=10(reviewed_entry_score_source_not_available), entry_score_excluded_reason=10(reviewed_entry_score_source_not_available), risk_regime_context=2(reviewed_missing_risk_regime_context), block_reason=2(reviewed_entry_block_source_quality_unknown_provenance)`
- `ai_confirmed_terminal_no_budget` count=`62` routing=`reviewed_unknown_token_provenance` fields=`score_prior_band=41(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=41(reviewed_score_prior_neutral_unknown_not_decision_input), entry_order_flow_status=37(reviewed_entry_order_flow_not_available), entry_score_source=10(reviewed_entry_score_source_not_available), entry_score_excluded_reason=10(reviewed_entry_score_source_not_available)`
- `ai_confirmed` count=`61` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=38(reviewed_entry_order_flow_not_available)`
- `real_weak_ai_micro_entry_block` count=`60` routing=`reviewed_unknown_token_provenance` fields=`reason=60(reviewed_entry_block_source_quality_unknown_provenance), block_reason=60(reviewed_entry_block_source_quality_unknown_provenance), rising_missed_submit_safety_backoff_reason=60(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `soft_stop_micro_grace` count=`53` routing=`reviewed_unknown_token_provenance` fields=`soft_stop_dynamic_grace_score_prior_band=32(reviewed_score_prior_neutral_unknown_not_decision_input)`
- `blocked_ai_score` count=`51` routing=`reviewed_unknown_token_provenance` fields=`score_prior_band=26(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=26(reviewed_score_prior_neutral_unknown_not_decision_input), entry_order_flow_status=15(reviewed_entry_order_flow_not_available), entry_score_source=10(reviewed_entry_score_source_not_available), entry_score_excluded_reason=10(reviewed_entry_score_source_not_available)`
- `rising_missed_tick_speed_entry_block` count=`35` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=27(reviewed_entry_order_flow_not_available)`
- `scalp_sim_panic_context_warning` count=`23` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=23(reviewed_missing_risk_regime_context), market_risk_state=23(reviewed_missing_risk_regime_context), liquidity_state=23(reviewed_missing_risk_regime_context), risk_regime_epoch_id=23(reviewed_missing_risk_regime_context)`
- `loss_fallback_probe` count=`7` routing=`reviewed_unknown_token_provenance` fields=`shallow_tick_context_stale=1(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=1(reviewed_shallow_stale_flag_not_available), tick_context_stale=1(reviewed_stale_flag_not_available), quote_stale=1(reviewed_stale_flag_not_available)`
- `early_accel_recheck_evaluated` count=`5` routing=`reviewed_unknown_token_provenance` fields=`tick_accel_source=5(reviewed_unusable_micro_context_not_available), tick_context_quality=5(reviewed_unusable_micro_context_not_available), minute_candle_context_quality=5(reviewed_unusable_micro_context_not_available)`
- `early_accel_recheck_skipped` count=`5` routing=`reviewed_unknown_token_provenance` fields=`tick_accel_source=5(reviewed_unusable_micro_context_not_available), tick_context_quality=5(reviewed_unusable_micro_context_not_available), minute_candle_context_quality=5(reviewed_unusable_micro_context_not_available)`
- `pre_submit_entry_ai_authority_guard_block` count=`5` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=4(reviewed_entry_order_flow_not_available)`
- `sell_order_sent` count=`5` routing=`reviewed_unknown_token_provenance` fields=`sell_order_exchange_resolution_reason=2(reviewed_sell_order_exchange_resolution_not_available)`
- `order_bundle_submitted` count=`4` routing=`reviewed_unknown_token_provenance` fields=`latency_danger_reasons=4(reviewed_pre_contract_placeholder), latency_danger_detail_reason=4(reviewed_pre_contract_placeholder), latency_danger_source_quality_state=4(reviewed_pre_contract_placeholder), latency_danger_reason_taxonomy_gap=4(reviewed_pre_contract_placeholder), latency_danger_max_ws_age_ms_for_caution=4(reviewed_pre_contract_placeholder), latency_danger_max_ws_jitter_ms_for_caution=4(reviewed_pre_contract_placeholder), latency_danger_max_spread_ratio_for_caution=4(reviewed_pre_contract_placeholder), latency_danger_guard_max_spread_ratio=4(reviewed_pre_contract_placeholder)`
- `order_leg_request` count=`4` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=1(reviewed_missing_risk_regime_context)`
- `pre_submit_micro_unavailable_block` count=`1` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_submit_safety_backoff_reason=1(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`

## Top Stages
- `scalping_scanner_candidate_observed`: `24470`
- `scalping_scanner_real_source_guard_block`: `24470`
- `scalping_scanner_promotion_latency_trace`: `12696`
- `scalping_scanner_fast_precheck`: `8841`
- `scalping_scanner_runtime_target_attach`: `8784`
- `scalping_scanner_runtime_queue_lag`: `7131`
- `scalping_scanner_watching_runtime_skip`: `6751`
- `scalping_scanner_heavy_eval_lag`: `3855`
- `rising_missed_watch_not_rising_skipped`: `3352`
- `scalping_scanner_candidate_promoted`: `2835`
- `scalping_scanner_watch_eviction`: `2680`
- `manual_control_excluded_symbol_blocked`: `1114`
- `bad_entry_refined_candidate`: `685`
- `stat_action_decision_snapshot`: `532`
- `scalp_sim_panic_scale_in_blocked`: `468`
- `scalping_scanner_low_rebound_source_observed`: `379`
- `rising_missed_scout_quality_guard_blocked`: `350`
- `strength_momentum_observed`: `292`
- `blocked_strength_momentum`: `282`
- `budget_pass`: `270`

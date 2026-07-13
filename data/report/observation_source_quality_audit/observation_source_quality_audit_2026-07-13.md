# Observation Source Quality Audit - 2026-07-13

- status: `warning`
- event_count: `56056`
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
- `stat_action_decision_snapshot` count=`532` routing=`source_quality_blocker_or_provenance_backfill` fields=`shallow_tick_context_stale=32(0.0602), shallow_quote_stale=32(0.0602)`
- `ai_holding_review` count=`252` routing=`source_quality_blocker_or_provenance_backfill` fields=`entry_order_flow_status=54(0.2143)`
- `scalp_entry_action_decision_snapshot` count=`146` routing=`source_quality_blocker_or_provenance_backfill` fields=`entry_order_flow_status=82(0.5616)`
- `ai_confirmed_terminal_no_budget` count=`62` routing=`source_quality_blocker_or_provenance_backfill` fields=`entry_order_flow_status=37(0.5968)`
- `ai_confirmed` count=`58` routing=`source_quality_blocker_or_provenance_backfill` fields=`entry_order_flow_status=36(0.6207)`
- `blocked_ai_score` count=`51` routing=`source_quality_blocker_or_provenance_backfill` fields=`entry_order_flow_status=15(0.2941)`
- `rising_missed_tick_speed_entry_block` count=`12` routing=`source_quality_blocker_or_provenance_backfill` fields=`entry_order_flow_status=9(0.75)`
- `loss_fallback_probe` count=`7` routing=`source_quality_blocker_or_provenance_backfill` fields=`shallow_tick_context_stale=1(0.1429), shallow_quote_stale=1(0.1429)`
- `order_bundle_submitted` count=`4` routing=`source_quality_blocker_or_provenance_backfill` fields=`entry_order_flow_status=1(0.25)`
- `pre_submit_entry_ai_authority_guard_block` count=`2` routing=`source_quality_blocker_or_provenance_backfill` fields=`entry_order_flow_status=2(1.0)`

## Reviewed Unknown Token Findings
- `scalping_scanner_fast_precheck` count=`5477` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_submit_safety_backoff_reason=1(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `stat_action_decision_snapshot` count=`532` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=37(reviewed_stale_flag_not_available), quote_stale=37(reviewed_stale_flag_not_available)`
- `ai_holding_review` count=`252` routing=`reviewed_unknown_token_provenance` fields=`holding_score_preflight_source_quality=246(reviewed_holding_score_preflight_not_available)`
- `scalp_entry_action_decision_snapshot` count=`146` routing=`reviewed_unknown_token_provenance` fields=`holding_exit_matrix_score_prior_band=91(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_band=41(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=41(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=10(reviewed_entry_score_source_not_available), entry_score_excluded_reason=10(reviewed_entry_score_source_not_available), risk_regime_context=1(reviewed_missing_risk_regime_context)`
- `ai_confirmed_terminal_no_budget` count=`62` routing=`reviewed_unknown_token_provenance` fields=`score_prior_band=41(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=41(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=10(reviewed_entry_score_source_not_available), entry_score_excluded_reason=10(reviewed_entry_score_source_not_available)`
- `soft_stop_micro_grace` count=`53` routing=`reviewed_unknown_token_provenance` fields=`soft_stop_dynamic_grace_score_prior_band=32(reviewed_score_prior_neutral_unknown_not_decision_input)`
- `blocked_ai_score` count=`51` routing=`reviewed_unknown_token_provenance` fields=`score_prior_band=26(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=26(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=10(reviewed_entry_score_source_not_available), entry_score_excluded_reason=10(reviewed_entry_score_source_not_available)`
- `scalp_sim_panic_context_warning` count=`23` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=23(reviewed_missing_risk_regime_context), market_risk_state=23(reviewed_missing_risk_regime_context), liquidity_state=23(reviewed_missing_risk_regime_context), risk_regime_epoch_id=23(reviewed_missing_risk_regime_context)`
- `real_weak_ai_micro_entry_block` count=`16` routing=`reviewed_unknown_token_provenance` fields=`reason=16(reviewed_entry_block_source_quality_unknown_provenance), block_reason=16(reviewed_entry_block_source_quality_unknown_provenance), rising_missed_submit_safety_backoff_reason=16(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `loss_fallback_probe` count=`7` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=1(reviewed_stale_flag_not_available), quote_stale=1(reviewed_stale_flag_not_available)`
- `early_accel_recheck_evaluated` count=`5` routing=`reviewed_unknown_token_provenance` fields=`tick_accel_source=5(reviewed_unusable_micro_context_not_available), tick_context_quality=5(reviewed_unusable_micro_context_not_available), minute_candle_context_quality=5(reviewed_unusable_micro_context_not_available)`
- `early_accel_recheck_skipped` count=`5` routing=`reviewed_unknown_token_provenance` fields=`tick_accel_source=5(reviewed_unusable_micro_context_not_available), tick_context_quality=5(reviewed_unusable_micro_context_not_available), minute_candle_context_quality=5(reviewed_unusable_micro_context_not_available)`
- `sell_order_sent` count=`5` routing=`reviewed_unknown_token_provenance` fields=`sell_order_exchange_resolution_reason=2(reviewed_sell_order_exchange_resolution_not_available)`
- `order_bundle_submitted` count=`4` routing=`reviewed_unknown_token_provenance` fields=`latency_danger_reasons=4(reviewed_pre_contract_placeholder), latency_danger_detail_reason=4(reviewed_pre_contract_placeholder), latency_danger_source_quality_state=4(reviewed_pre_contract_placeholder), latency_danger_reason_taxonomy_gap=4(reviewed_pre_contract_placeholder), latency_danger_max_ws_age_ms_for_caution=4(reviewed_pre_contract_placeholder), latency_danger_max_ws_jitter_ms_for_caution=4(reviewed_pre_contract_placeholder), latency_danger_max_spread_ratio_for_caution=4(reviewed_pre_contract_placeholder), latency_danger_guard_max_spread_ratio=4(reviewed_pre_contract_placeholder)`
- `order_leg_request` count=`4` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=1(reviewed_missing_risk_regime_context)`
- `pre_submit_micro_unavailable_block` count=`1` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_submit_safety_backoff_reason=1(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `scale_in_qty_block` count=`1` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=1(reviewed_stale_flag_not_available), quote_stale=1(reviewed_stale_flag_not_available)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `8474`
- `scalping_scanner_candidate_observed`: `8109`
- `scalping_scanner_real_source_guard_block`: `8109`
- `scalping_scanner_fast_precheck`: `5477`
- `scalping_scanner_runtime_queue_lag`: `4156`
- `scalping_scanner_runtime_target_attach`: `3675`
- `scalping_scanner_heavy_eval_lag`: `2997`
- `rising_missed_watch_not_rising_skipped`: `2917`
- `scalping_scanner_watching_runtime_skip`: `2857`
- `scalping_scanner_candidate_promoted`: `1337`
- `scalping_scanner_watch_eviction`: `1248`
- `bad_entry_refined_candidate`: `685`
- `stat_action_decision_snapshot`: `532`
- `scalp_sim_panic_scale_in_blocked`: `468`
- `manual_control_excluded_symbol_blocked`: `462`
- `strength_momentum_observed`: `258`
- `ai_holding_fast_reuse_band`: `252`
- `ai_holding_reuse_bypass`: `252`
- `ai_holding_review`: `252`
- `holding_ws_freshness_blocked`: `249`

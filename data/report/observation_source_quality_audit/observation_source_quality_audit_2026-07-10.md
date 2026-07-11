# Observation Source Quality Audit - 2026-07-10

- status: `pass`
- event_count: `72435`
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
- `scalping_scanner_fast_precheck` count=`8459` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_submit_safety_backoff_reason=17(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `stat_action_decision_snapshot` count=`1206` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=33(reviewed_stale_flag_not_available), quote_stale=33(reviewed_stale_flag_not_available)`
- `ai_holding_review` count=`912` routing=`reviewed_unknown_token_provenance` fields=`holding_score_preflight_source_quality=908(reviewed_holding_score_preflight_not_available)`
- `scalp_entry_action_decision_snapshot` count=`534` routing=`reviewed_unknown_token_provenance` fields=`holding_exit_matrix_score_prior_band=316(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_band=58(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=58(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=21(reviewed_entry_score_source_not_available), entry_score_excluded_reason=21(reviewed_entry_score_source_not_available), risk_regime_context=8(reviewed_missing_risk_regime_context), block_reason=4(reviewed_entry_block_source_quality_unknown_provenance)`
- `scalp_sim_panic_context_warning` count=`235` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=235(reviewed_missing_risk_regime_context), market_risk_state=235(reviewed_missing_risk_regime_context), liquidity_state=235(reviewed_missing_risk_regime_context), risk_regime_epoch_id=235(reviewed_missing_risk_regime_context)`
- `ai_confirmed_terminal_no_budget` count=`185` routing=`reviewed_unknown_token_provenance` fields=`score_prior_band=58(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=58(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=21(reviewed_entry_score_source_not_available), entry_score_excluded_reason=21(reviewed_entry_score_source_not_available)`
- `blocked_ai_score` count=`89` routing=`reviewed_unknown_token_provenance` fields=`score_prior_band=58(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=58(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=21(reviewed_entry_score_source_not_available), entry_score_excluded_reason=21(reviewed_entry_score_source_not_available)`
- `scale_in_qty_block` count=`50` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=32(reviewed_stale_flag_not_available), quote_stale=32(reviewed_stale_flag_not_available)`
- `real_weak_ai_micro_entry_block` count=`38` routing=`reviewed_unknown_token_provenance` fields=`reason=38(reviewed_entry_block_source_quality_unknown_provenance), block_reason=38(reviewed_entry_block_source_quality_unknown_provenance), rising_missed_submit_safety_backoff_reason=38(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `order_leg_request` count=`29` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=2(reviewed_missing_risk_regime_context)`
- `order_bundle_submitted` count=`19` routing=`reviewed_unknown_token_provenance` fields=`latency_danger_reasons=19(reviewed_pre_contract_placeholder), latency_danger_detail_reason=19(reviewed_pre_contract_placeholder), latency_danger_source_quality_state=19(reviewed_pre_contract_placeholder), latency_danger_reason_taxonomy_gap=19(reviewed_pre_contract_placeholder), latency_danger_max_ws_age_ms_for_caution=19(reviewed_pre_contract_placeholder), latency_danger_max_ws_jitter_ms_for_caution=19(reviewed_pre_contract_placeholder), latency_danger_max_spread_ratio_for_caution=19(reviewed_pre_contract_placeholder), latency_danger_guard_max_spread_ratio=19(reviewed_pre_contract_placeholder)`
- `early_accel_recheck_evaluated` count=`12` routing=`reviewed_unknown_token_provenance` fields=`tick_accel_source=12(reviewed_unusable_micro_context_not_available), tick_context_quality=12(reviewed_unusable_micro_context_not_available), minute_candle_context_quality=12(reviewed_unusable_micro_context_not_available)`
- `early_accel_recheck_skipped` count=`12` routing=`reviewed_unknown_token_provenance` fields=`tick_accel_source=12(reviewed_unusable_micro_context_not_available), tick_context_quality=12(reviewed_unusable_micro_context_not_available), minute_candle_context_quality=12(reviewed_unusable_micro_context_not_available)`
- `scale_in_price_guard_block` count=`3` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=1(reviewed_stale_flag_not_available), quote_stale=1(reviewed_stale_flag_not_available)`
- `pre_submit_micro_unavailable_block` count=`2` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_submit_safety_backoff_reason=2(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `soft_stop_micro_grace` count=`2` routing=`reviewed_unknown_token_provenance` fields=`soft_stop_dynamic_grace_score_prior_band=1(reviewed_score_prior_neutral_unknown_not_decision_input)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `11962`
- `scalping_scanner_runtime_target_attach`: `9080`
- `scalping_scanner_fast_precheck`: `8459`
- `scalping_scanner_runtime_queue_lag`: `6662`
- `scalping_scanner_watching_runtime_skip`: `6233`
- `scalping_scanner_heavy_eval_lag`: `3503`
- `rising_missed_watch_not_rising_skipped`: `3207`
- `scalping_scanner_candidate_promoted`: `2468`
- `scalping_scanner_watch_eviction`: `2242`
- `bad_entry_refined_candidate`: `1807`
- `manual_control_excluded_symbol_blocked`: `1311`
- `scale_in_feature_context_refresh`: `1214`
- `stat_action_decision_snapshot`: `1206`
- `ai_holding_fast_reuse_band`: `931`
- `ai_holding_reuse_bypass`: `918`
- `ai_holding_review`: `912`
- `condition_unmatch_guard`: `903`
- `scalping_scanner_candidate_observed`: `867`
- `scalping_scanner_real_source_guard_block`: `867`
- `scalp_sim_scale_in_candidate_funnel`: `824`

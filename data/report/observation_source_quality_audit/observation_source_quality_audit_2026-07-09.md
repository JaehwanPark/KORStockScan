# Observation Source Quality Audit - 2026-07-09

- status: `pass`
- event_count: `78658`
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
- `scalping_scanner_watching_runtime_skip` count=`10372` routing=`reviewed_unknown_token_provenance` fields=`minute_candle_context_quality=1(reviewed_runtime_skip_context_not_evaluated), tick_context_quality=1(reviewed_runtime_skip_context_not_evaluated), tick_context_stale=1(reviewed_stale_flag_not_available)`
- `stat_action_decision_snapshot` count=`628` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=27(reviewed_stale_flag_not_available), quote_stale=27(reviewed_stale_flag_not_available)`
- `scalp_sim_panic_context_warning` count=`520` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=520(reviewed_missing_risk_regime_context), market_risk_state=520(reviewed_missing_risk_regime_context), liquidity_state=520(reviewed_missing_risk_regime_context), risk_regime_epoch_id=520(reviewed_missing_risk_regime_context)`
- `ai_holding_review` count=`496` routing=`reviewed_unknown_token_provenance` fields=`holding_score_preflight_source_quality=484(reviewed_holding_score_preflight_not_available)`
- `scalp_entry_action_decision_snapshot` count=`341` routing=`reviewed_unknown_token_provenance` fields=`holding_exit_matrix_score_prior_band=85(reviewed_score_prior_neutral_unknown_not_decision_input), risk_regime_context=31(reviewed_missing_risk_regime_context), block_reason=24(reviewed_entry_block_source_quality_unknown_provenance), score_prior_band=15(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=15(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=6(reviewed_entry_score_source_not_available), entry_score_excluded_reason=6(reviewed_entry_score_source_not_available)`
- `ai_confirmed_terminal_no_budget` count=`53` routing=`reviewed_unknown_token_provenance` fields=`score_prior_band=15(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=15(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=6(reviewed_entry_score_source_not_available), entry_score_excluded_reason=6(reviewed_entry_score_source_not_available)`
- `real_weak_ai_micro_entry_block` count=`53` routing=`reviewed_unknown_token_provenance` fields=`reason=53(reviewed_entry_block_source_quality_unknown_provenance), block_reason=53(reviewed_entry_block_source_quality_unknown_provenance)`
- `blocked_ai_score` count=`38` routing=`reviewed_unknown_token_provenance` fields=`score_prior_band=15(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=15(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=6(reviewed_entry_score_source_not_available), entry_score_excluded_reason=6(reviewed_entry_score_source_not_available)`
- `soft_stop_micro_grace` count=`23` routing=`reviewed_unknown_token_provenance` fields=`soft_stop_dynamic_grace_score_prior_band=7(reviewed_score_prior_neutral_unknown_not_decision_input)`
- `order_bundle_submitted` count=`13` routing=`reviewed_unknown_token_provenance` fields=`latency_danger_reasons=13(reviewed_pre_contract_placeholder), latency_danger_detail_reason=13(reviewed_pre_contract_placeholder), latency_danger_source_quality_state=13(reviewed_pre_contract_placeholder), latency_danger_reason_taxonomy_gap=13(reviewed_pre_contract_placeholder), latency_danger_max_ws_age_ms_for_caution=13(reviewed_pre_contract_placeholder), latency_danger_max_ws_jitter_ms_for_caution=13(reviewed_pre_contract_placeholder), latency_danger_max_spread_ratio_for_caution=13(reviewed_pre_contract_placeholder), latency_danger_guard_max_spread_ratio=13(reviewed_pre_contract_placeholder)`
- `scale_in_qty_block` count=`9` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=7(reviewed_stale_flag_not_available), quote_stale=7(reviewed_stale_flag_not_available)`
- `sell_order_sent` count=`6` routing=`reviewed_unknown_token_provenance` fields=`sell_order_exchange_resolution_reason=1(reviewed_sell_order_exchange_resolution_not_available)`
- `early_accel_recheck_evaluated` count=`5` routing=`reviewed_unknown_token_provenance` fields=`tick_accel_source=5(reviewed_unusable_micro_context_not_available), tick_context_quality=5(reviewed_unusable_micro_context_not_available), minute_candle_context_quality=5(reviewed_unusable_micro_context_not_available)`
- `early_accel_recheck_skipped` count=`5` routing=`reviewed_unknown_token_provenance` fields=`tick_accel_source=5(reviewed_unusable_micro_context_not_available), tick_context_quality=5(reviewed_unusable_micro_context_not_available), minute_candle_context_quality=5(reviewed_unusable_micro_context_not_available)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `18106`
- `scalping_scanner_fast_precheck`: `15295`
- `scalping_scanner_watching_runtime_skip`: `10372`
- `scalping_scanner_runtime_queue_lag`: `9857`
- `scalping_scanner_runtime_target_attach`: `6753`
- `scalping_scanner_heavy_eval_lag`: `2811`
- `manual_control_excluded_symbol_blocked`: `1569`
- `rising_missed_watch_not_rising_skipped`: `1062`
- `bad_entry_refined_candidate`: `1001`
- `scalping_scanner_candidate_promoted`: `910`
- `stat_action_decision_snapshot`: `628`
- `rising_missed_scout_quality_guard_blocked`: `598`
- `scalping_scanner_candidate_observed`: `572`
- `scalping_scanner_real_source_guard_block`: `572`
- `scalping_scanner_watch_eviction`: `566`
- `scalp_sim_panic_context_warning`: `520`
- `ai_holding_fast_reuse_band`: `508`
- `ai_holding_reuse_bypass`: `508`
- `ai_holding_review`: `496`
- `budget_pass`: `420`

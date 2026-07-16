# Observation Source Quality Audit - 2026-07-16

- status: `pass`
- event_count: `110411`
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
- `scalping_scanner_fast_precheck` count=`8458` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_submit_safety_backoff_reason=14(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `scalping_scanner_watching_runtime_skip` count=`7954` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=577(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_nxt_post_block_price_sample` count=`1207` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_post_block_ws_0b_route=3(reviewed_rising_missed_nxt_post_block_route_not_available), rising_missed_nxt_post_block_ws_0d_route=3(reviewed_rising_missed_nxt_post_block_route_not_available)`
- `stat_action_decision_snapshot` count=`490` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=12(reviewed_stale_flag_not_available), quote_stale=12(reviewed_stale_flag_not_available), shallow_tick_context_stale=10(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=10(reviewed_shallow_stale_flag_not_available)`
- `rising_missed_one_share_entry` count=`374` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=316(reviewed_rising_missed_nxt_eligibility_not_available)`
- `blocked_zero_qty` count=`320` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=316(reviewed_rising_missed_nxt_eligibility_not_available)`
- `ai_holding_review` count=`289` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=101(reviewed_entry_order_flow_not_available)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`193` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=165(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_candidate_blocked` count=`180` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=155(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalp_sim_panic_context_warning` count=`171` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=171(reviewed_missing_risk_regime_context), market_risk_state=171(reviewed_missing_risk_regime_context), liquidity_state=171(reviewed_missing_risk_regime_context), risk_regime_epoch_id=171(reviewed_missing_risk_regime_context)`
- `scalp_entry_action_decision_snapshot` count=`88` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=67(reviewed_entry_order_flow_not_available), holding_exit_matrix_score_prior_band=53(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_band=20(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=20(reviewed_score_prior_neutral_unknown_not_decision_input), risk_regime_context=8(reviewed_missing_risk_regime_context), entry_score_source=5(reviewed_entry_score_source_not_available), entry_score_excluded_reason=5(reviewed_entry_score_source_not_available)`
- `ai_confirmed` count=`35` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=26(reviewed_entry_order_flow_not_available)`
- `ai_confirmed_terminal_no_budget` count=`34` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=28(reviewed_entry_order_flow_not_available), score_prior_band=20(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=20(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=5(reviewed_entry_score_source_not_available), entry_score_excluded_reason=5(reviewed_entry_score_source_not_available)`
- `real_weak_ai_micro_entry_block` count=`24` routing=`reviewed_unknown_token_provenance` fields=`reason=24(reviewed_entry_block_source_quality_unknown_provenance), block_reason=24(reviewed_entry_block_source_quality_unknown_provenance), rising_missed_submit_safety_backoff_reason=24(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `blocked_ai_score` count=`19` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=8(reviewed_entry_order_flow_not_available), score_prior_band=8(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=8(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=5(reviewed_entry_score_source_not_available), entry_score_excluded_reason=5(reviewed_entry_score_source_not_available)`
- `rising_missed_tp1_candidate_deferred` count=`13` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=10(reviewed_rising_missed_nxt_eligibility_not_available)`
- `soft_stop_micro_grace` count=`11` routing=`reviewed_unknown_token_provenance` fields=`soft_stop_dynamic_grace_score_prior_band=5(reviewed_score_prior_neutral_unknown_not_decision_input)`
- `rising_missed_tick_speed_entry_block` count=`10` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=7(reviewed_entry_order_flow_not_available)`
- `loss_fallback_probe` count=`4` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=2(reviewed_stale_flag_not_available), quote_stale=2(reviewed_stale_flag_not_available)`
- `pre_submit_entry_ai_authority_guard_block` count=`3` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=3(reviewed_entry_order_flow_not_available)`

## Top Stages
- `scalping_scanner_candidate_observed`: `20663`
- `scalping_scanner_real_source_guard_block`: `20663`
- `scalping_scanner_promotion_latency_trace`: `11868`
- `scalping_scanner_runtime_target_attach`: `11663`
- `scalping_scanner_fast_precheck`: `8458`
- `scalping_scanner_watching_runtime_skip`: `7954`
- `scalping_scanner_runtime_queue_lag`: `6856`
- `scalping_scanner_candidate_promoted`: `3453`
- `scalping_scanner_heavy_eval_lag`: `3410`
- `scalping_scanner_watch_eviction`: `3280`
- `rising_missed_watch_not_rising_skipped`: `2552`
- `manual_control_excluded_symbol_blocked`: `2048`
- `rising_missed_nxt_post_block_price_sample`: `1207`
- `bad_entry_refined_candidate`: `795`
- `scalp_sim_panic_scale_in_blocked`: `620`
- `stat_action_decision_snapshot`: `490`
- `scalping_scanner_low_rebound_source_observed`: `383`
- `rising_missed_one_share_entry`: `374`
- `scalp_sim_panic_action_deduped`: `340`
- `blocked_zero_qty`: `320`

# Observation Source Quality Audit - 2026-09-01

- status: `pass`
- event_count: `107998`
- tuning_input_policy: `exclude_defective_rows_not_full_day_raw`
- hard_blocking_excluded_row_count: `0`
- pre_exclusion_hard_blocking_excluded_row_count: `None`
- current_scan_hard_blocking_excluded_row_count: `None`
- post_exclusion_hard_blocking_excluded_row_count: `None`
- raw_row_exclusion_applied: `False`
- raw_row_exclusion_deferred_writer_active: `False`
- raw_row_exclusion_revalidation_required: `False`
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
- `scalping_scanner_fast_precheck` count=`15110` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=359(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=173(reviewed_scanner_stale_backoff_route_not_available)`
- `scalping_scanner_watching_runtime_skip` count=`3109` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=399(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=10(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=10(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=10(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_watch_not_rising_skipped` count=`2617` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=2617(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalp_entry_action_decision_snapshot` count=`443` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=301(reviewed_rising_missed_nxt_eligibility_not_available), holding_exit_matrix_score_prior_band=152(reviewed_score_prior_neutral_unknown_not_decision_input), entry_order_flow_status=70(reviewed_entry_order_flow_not_available), score_prior_band=19(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=19(reviewed_score_prior_neutral_unknown_not_decision_input), tier_reason=16(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=16(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=16(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`304` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=304(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=2(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=2(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=2(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_one_share_entry` count=`300` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=300(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=2(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=2(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=2(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_tp1_candidate_blocked` count=`250` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=250(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=2(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=2(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=2(reviewed_explicit_sizing_unknown_venue_fallback)`
- `budget_pass` count=`243` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=240(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=12(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=12(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=12(reviewed_explicit_sizing_unknown_venue_fallback)`
- `orderbook_stability_observed` count=`243` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=240(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=12(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=12(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=12(reviewed_explicit_sizing_unknown_venue_fallback)`
- `ai_holding_review` count=`237` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=13(reviewed_entry_order_flow_not_available)`
- `risky_micro_episode_source_candidate_observed` count=`190` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=190(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=9(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=9(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=9(reviewed_explicit_sizing_unknown_venue_fallback)`
- `stat_action_decision_snapshot` count=`177` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=25(reviewed_stale_flag_not_available), quote_stale=25(reviewed_stale_flag_not_available), shallow_tick_context_stale=21(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=21(reviewed_shallow_stale_flag_not_available)`
- `rising_missed_adverse_micro_recovery_checkpoint` count=`165` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_adverse_micro_recovery_ws_0b_raw_route=6(reviewed_adverse_micro_recovery_route_not_available)`
- `prev_close_gainer_entry_ai_handoff` count=`164` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=144(reviewed_rising_missed_nxt_eligibility_not_available)`
- `latency_block` count=`157` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=155(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=6(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=6(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=6(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scalp_sim_panic_context_warning` count=`112` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=112(reviewed_missing_risk_regime_context), market_risk_state=112(reviewed_missing_risk_regime_context), liquidity_state=112(reviewed_missing_risk_regime_context), risk_regime_epoch_id=112(reviewed_missing_risk_regime_context)`
- `ai_confirmed` count=`107` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=31(reviewed_rising_missed_nxt_eligibility_not_available), entry_order_flow_status=20(reviewed_entry_order_flow_not_available), tier_reason=2(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=2(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=2(reviewed_explicit_sizing_unknown_venue_fallback)`
- `reversal_add_blocked_reason` count=`105` routing=`reviewed_unknown_token_provenance` fields=`shallow_tick_context_stale=21(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=21(reviewed_shallow_stale_flag_not_available), tick_context_stale=21(reviewed_stale_flag_not_available), quote_stale=21(reviewed_stale_flag_not_available)`
- `blocked_ai_score` count=`101` routing=`reviewed_unknown_token_provenance` fields=`score_prior_band=19(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=19(reviewed_score_prior_neutral_unknown_not_decision_input), entry_order_flow_status=12(reviewed_entry_order_flow_not_available), entry_score_source=9(reviewed_entry_score_source_not_available), entry_recheck_excluded_reason=9(reviewed_entry_score_source_not_available), entry_score_excluded_reason=9(reviewed_entry_score_source_not_available)`
- `entry_ai_price_canary_applied` count=`79` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=71(reviewed_rising_missed_nxt_eligibility_not_available), entry_order_flow_status=18(reviewed_entry_order_flow_not_available), tier_reason=6(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=6(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=6(reviewed_explicit_sizing_unknown_venue_fallback)`

## Top Stages
- `scalping_scanner_candidate_pruned`: `30726`
- `scalping_scanner_promotion_latency_trace`: `19967`
- `scalping_scanner_fast_precheck`: `15110`
- `scalping_scanner_runtime_queue_lag`: `8805`
- `scalping_scanner_heavy_eval_completion`: `4940`
- `scalping_scanner_heavy_eval_lag`: `4857`
- `risky_micro_episode_executable_bbo_observed`: `3720`
- `scalping_scanner_watching_runtime_skip`: `3109`
- `rising_missed_watch_not_rising_skipped`: `2617`
- `scalping_scanner_candidate_observed`: `1688`
- `scalping_scanner_real_source_guard_block`: `1688`
- `scalping_scanner_runtime_target_attach`: `818`
- `scalping_scanner_candidate_promoted`: `810`
- `scalping_scanner_watch_eviction`: `740`
- `bad_entry_refined_candidate`: `739`
- `strength_momentum_observed`: `527`
- `scalp_entry_action_decision_snapshot`: `443`
- `blocked_strength_momentum`: `402`
- `scalping_scanner_ws_backoff_watch_retained`: `319`
- `rising_missed_tp1_counterfactual_submit_safety`: `304`

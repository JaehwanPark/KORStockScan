# Observation Source Quality Audit - 2026-09-04

- status: `pass`
- event_count: `313710`
- tuning_input_policy: `exclude_defective_rows_not_full_day_raw`
- hard_blocking_excluded_row_count: `1`
- pre_exclusion_hard_blocking_excluded_row_count: `1`
- current_scan_hard_blocking_excluded_row_count: `0`
- post_exclusion_hard_blocking_excluded_row_count: `0`
- raw_row_exclusion_applied: `True`
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
- `scalping_scanner_fast_precheck` count=`38226` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=1033(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=536(reviewed_scanner_stale_backoff_route_not_available), rising_missed_submit_safety_backoff_reason=1(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `scalping_scanner_watching_runtime_skip` count=`11509` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=590(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=174(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=174(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=174(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_effective_venue=4(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_nxt_post_block_price_sample` count=`11108` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_post_block_ws_0b_route=6(reviewed_rising_missed_nxt_post_block_route_not_available), rising_missed_nxt_post_block_ws_0d_route=6(reviewed_rising_missed_nxt_post_block_route_not_available)`
- `rising_missed_watch_not_rising_skipped` count=`4696` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=2490(reviewed_rising_missed_nxt_eligibility_not_available), venue=568(reviewed_observation_only_venue_not_available), rising_missed_effective_venue=568(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`2793` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=892(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=86(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_entry_turn_pre_anchor_bbo_path` count=`2690` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=103(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=86(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_tp1_candidate_deferred` count=`1950` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=336(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=60(reviewed_rising_missed_nxt_eligibility_not_available)`
- `strength_momentum_observed` count=`1575` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=3(reviewed_rising_missed_nxt_eligibility_not_available)`
- `blocked_strength_momentum` count=`1256` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=2(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalp_entry_action_decision_snapshot` count=`952` routing=`reviewed_unknown_token_provenance` fields=`holding_exit_matrix_score_prior_band=452(reviewed_score_prior_neutral_unknown_not_decision_input), rising_missed_nxt_eligible=421(reviewed_rising_missed_nxt_eligibility_not_available), entry_order_flow_status=173(reviewed_entry_order_flow_not_available), score_prior_band=134(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=134(reviewed_score_prior_neutral_unknown_not_decision_input), risk_regime_context=96(reviewed_missing_risk_regime_context), rising_missed_effective_venue=18(reviewed_rising_missed_nxt_eligibility_not_available), latency_true_ofi_nxt_probability_band_effective_venue=16(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_candidate_blocked` count=`843` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=556(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=26(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_one_share_entry` count=`474` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=380(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=15(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback)`
- `budget_pass` count=`437` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=342(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=15(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=11(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=11(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=11(reviewed_explicit_sizing_unknown_venue_fallback)`
- `orderbook_stability_observed` count=`437` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=342(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=15(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=11(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=11(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=11(reviewed_explicit_sizing_unknown_venue_fallback)`
- `prev_close_gainer_entry_ai_handoff` count=`396` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=221(reviewed_rising_missed_nxt_eligibility_not_available)`
- `opening_rotation_krx_regular_scope_skipped` count=`390` routing=`reviewed_unknown_token_provenance` fields=`forbidden_uses=390(reviewed_forbidden_uses_unknown_literal_not_source_value)`
- `risky_micro_episode_source_candidate_observed` count=`315` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=240(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=11(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=11(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=11(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_effective_venue=8(reviewed_rising_missed_nxt_eligibility_not_available)`
- `ai_confirmed` count=`280` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=40(reviewed_entry_order_flow_not_available), rising_missed_nxt_eligible=33(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=2(reviewed_rising_missed_nxt_eligibility_not_available)`
- `reversal_add_blocked_reason` count=`275` routing=`reviewed_unknown_token_provenance` fields=`shallow_tick_context_stale=17(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=17(reviewed_shallow_stale_flag_not_available), tick_context_stale=17(reviewed_stale_flag_not_available), quote_stale=17(reviewed_stale_flag_not_available), prior_probe_residual_direction_state=2(reviewed_prior_probe_residual_source_gap), prior_probe_residual_orderbook_state=2(reviewed_prior_probe_residual_source_gap), prior_probe_residual_failure_signature=2(reviewed_prior_probe_residual_source_gap)`
- `latency_block` count=`270` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=202(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=11(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=11(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=11(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_effective_venue=4(reviewed_rising_missed_nxt_eligibility_not_available), latency_true_ofi_nxt_probability_band_effective_venue=4(reviewed_rising_missed_nxt_eligibility_not_available)`

## Top Stages
- `scalping_scanner_candidate_pruned`: `66048`
- `scalping_scanner_prune_bbo_schedule`: `55074`
- `scalping_scanner_promotion_latency_trace`: `48711`
- `scalping_scanner_fast_precheck`: `38226`
- `scalping_scanner_runtime_queue_lag`: `21993`
- `scalping_scanner_watching_runtime_skip`: `11509`
- `rising_missed_nxt_post_block_price_sample`: `11108`
- `scalping_scanner_heavy_eval_completion`: `10692`
- `scalping_scanner_heavy_eval_lag`: `10485`
- `rising_missed_watch_not_rising_skipped`: `4696`
- `risky_micro_episode_executable_bbo_observed`: `4239`
- `rising_missed_tp1_counterfactual_submit_safety`: `2793`
- `rising_missed_entry_turn_pre_anchor_bbo_path`: `2690`
- `scalping_scanner_runtime_target_attach`: `2345`
- `scalping_scanner_candidate_promoted`: `2142`
- `rising_missed_tp1_candidate_deferred`: `1950`
- `scalping_scanner_watch_eviction`: `1828`
- `strength_momentum_observed`: `1575`
- `blocked_strength_momentum`: `1256`
- `scalping_scanner_ws_backoff_watch_retained`: `1205`

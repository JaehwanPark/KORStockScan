# Observation Source Quality Audit - 2026-08-26

- status: `pass`
- event_count: `264379`
- tuning_input_policy: `exclude_defective_rows_not_full_day_raw`
- hard_blocking_excluded_row_count: `56`
- pre_exclusion_hard_blocking_excluded_row_count: `56`
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
- `scalping_scanner_promotion_latency_trace` count=`59595` routing=`reviewed_unknown_token_provenance` fields=`venue=2(reviewed_scanner_venue_fail_closed_provenance), effective_venue=2(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_fast_precheck` count=`45973` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=1286(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=470(reviewed_scanner_stale_backoff_route_not_available), rising_missed_submit_safety_backoff_reason=2(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance), venue=1(reviewed_scanner_venue_fail_closed_provenance), effective_venue=1(reviewed_scanner_venue_fail_closed_provenance), scanner_promotion_reanchor_effective_venue=1(reviewed_scanner_venue_fail_closed_provenance), scanner_stale_backoff_canonical_effective_venue=1(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_runtime_queue_lag` count=`26077` routing=`reviewed_unknown_token_provenance` fields=`venue=1(reviewed_scanner_venue_fail_closed_provenance), effective_venue=1(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_heavy_eval_completion` count=`13982` routing=`reviewed_unknown_token_provenance` fields=`venue=1(reviewed_scanner_venue_fail_closed_provenance), effective_venue=1(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_heavy_eval_lag` count=`13622` routing=`reviewed_unknown_token_provenance` fields=`venue=1(reviewed_scanner_venue_fail_closed_provenance), effective_venue=1(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_watching_runtime_skip` count=`10426` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=886(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=67(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=49(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=49(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=49(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_nxt_post_block_price_sample` count=`8200` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_post_block_ws_0b_route=1(reviewed_rising_missed_nxt_post_block_route_not_available), rising_missed_nxt_post_block_ws_0d_route=1(reviewed_rising_missed_nxt_post_block_route_not_available)`
- `rising_missed_watch_not_rising_skipped` count=`6636` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=5041(reviewed_rising_missed_nxt_eligibility_not_available), venue=32(reviewed_observation_only_venue_not_available), rising_missed_effective_venue=32(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`3001` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1708(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=274(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=4(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=4(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=4(reviewed_explicit_sizing_unknown_venue_fallback)`
- `strength_momentum_observed` count=`1593` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=29(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalp_entry_action_decision_snapshot` count=`1576` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1057(reviewed_rising_missed_nxt_eligibility_not_available), holding_exit_matrix_score_prior_band=536(reviewed_score_prior_neutral_unknown_not_decision_input), entry_order_flow_status=182(reviewed_entry_order_flow_not_available), risk_regime_context=153(reviewed_missing_risk_regime_context), score_prior_band=74(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=74(reviewed_score_prior_neutral_unknown_not_decision_input), tier_reason=32(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=32(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_tp1_candidate_blocked` count=`1558` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1247(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=21(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=3(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=3(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=3(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_tp1_candidate_deferred` count=`1443` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=461(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=253(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback)`
- `reversal_add_blocked_reason` count=`1430` routing=`reviewed_unknown_token_provenance` fields=`shallow_tick_context_stale=1(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=1(reviewed_shallow_stale_flag_not_available), tick_context_stale=1(reviewed_stale_flag_not_available), quote_stale=1(reviewed_stale_flag_not_available)`
- `stat_action_decision_snapshot` count=`1394` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=18(reviewed_stale_flag_not_available), quote_stale=18(reviewed_stale_flag_not_available), shallow_tick_context_stale=1(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=1(reviewed_shallow_stale_flag_not_available)`
- `scalp_sim_panic_context_warning` count=`1142` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=1142(reviewed_missing_risk_regime_context), market_risk_state=1142(reviewed_missing_risk_regime_context), liquidity_state=1142(reviewed_missing_risk_regime_context), risk_regime_epoch_id=1142(reviewed_missing_risk_regime_context)`
- `blocked_strength_momentum` count=`1128` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=25(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_one_share_entry` count=`931` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=875(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=33(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=6(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=6(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=6(reviewed_explicit_sizing_unknown_venue_fallback), venue=1(reviewed_rising_missed_explicit_venue_conflict), effective_venue=1(reviewed_rising_missed_explicit_venue_conflict)`
- `budget_pass` count=`850` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=795(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=33(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=30(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=30(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=30(reviewed_explicit_sizing_unknown_venue_fallback)`
- `orderbook_stability_observed` count=`850` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=795(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=33(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=30(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=30(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=30(reviewed_explicit_sizing_unknown_venue_fallback)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `59595`
- `scalping_scanner_fast_precheck`: `45973`
- `scalping_scanner_runtime_queue_lag`: `26077`
- `scalping_scanner_runtime_target_attach`: `24040`
- `scalping_scanner_heavy_eval_completion`: `13982`
- `scalping_scanner_heavy_eval_lag`: `13622`
- `scalping_scanner_watching_runtime_skip`: `10426`
- `risky_micro_episode_executable_bbo_observed`: `9532`
- `rising_missed_nxt_post_block_price_sample`: `8200`
- `rising_missed_watch_not_rising_skipped`: `6636`
- `scalping_scanner_candidate_observed`: `3166`
- `scalping_scanner_real_source_guard_block`: `3166`
- `rising_missed_tp1_counterfactual_submit_safety`: `3001`
- `scalp_sim_scale_in_candidate_funnel`: `2755`
- `bad_entry_refined_candidate`: `2547`
- `scalping_scanner_candidate_promoted`: `2267`
- `scalping_scanner_watch_eviction`: `1835`
- `strength_momentum_observed`: `1593`
- `scalp_entry_action_decision_snapshot`: `1576`
- `rising_missed_tp1_candidate_blocked`: `1558`

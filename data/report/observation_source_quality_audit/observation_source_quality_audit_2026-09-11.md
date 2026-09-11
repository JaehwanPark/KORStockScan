# Observation Source Quality Audit - 2026-09-11

- status: `fail`
- event_count: `160931`
- tuning_input_policy: `exclude_defective_rows_not_full_day_raw`
- hard_blocking_excluded_row_count: `0`
- pre_exclusion_hard_blocking_excluded_row_count: `None`
- current_scan_hard_blocking_excluded_row_count: `None`
- post_exclusion_hard_blocking_excluded_row_count: `None`
- raw_row_exclusion_applied: `False`
- raw_row_exclusion_deferred_writer_active: `False`
- raw_row_exclusion_revalidation_required: `False`
- tuning_input_allowed: `False`
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
- `scalping_scanner_source_fetch_census` count=`1540` routing=`source_quality_blocker_or_provenance_backfill` fields=`scanner_source_rows_json=1382(0.8974)`
- `scalping_scanner_candidate_pool_census` count=`148` routing=`source_quality_blocker_or_provenance_backfill` fields=`scanner_source_rows_json=148(1.0)`
- `scale_in_ai_authority_retry` count=`30` routing=`source_quality_blocker_or_provenance_backfill` fields=`ai_input_preflight_source_timing=2(0.0667)`
- `scalp_fast_exit_quote_blocked` count=`3` routing=`source_quality_blocker_or_provenance_backfill` fields=`fast_exit_ws_0d_route=3(1.0)`

## Reviewed Unknown Token Findings
- `scalping_scanner_promotion_latency_trace` count=`15663` routing=`reviewed_unknown_token_provenance` fields=`venue=57(reviewed_scanner_venue_fail_closed_provenance), effective_venue=57(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_fast_precheck` count=`12181` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=519(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=278(reviewed_scanner_stale_backoff_route_not_available), venue=46(reviewed_scanner_venue_fail_closed_provenance), effective_venue=46(reviewed_scanner_venue_fail_closed_provenance), scanner_promotion_reanchor_effective_venue=46(reviewed_scanner_venue_fail_closed_provenance), scanner_stale_backoff_canonical_effective_venue=46(reviewed_scanner_venue_fail_closed_provenance), rising_missed_submit_safety_backoff_reason=4(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `scalping_scanner_runtime_queue_lag` count=`8338` routing=`reviewed_unknown_token_provenance` fields=`venue=27(reviewed_scanner_venue_fail_closed_provenance), effective_venue=27(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_watching_runtime_skip` count=`5386` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=686(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=67(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=67(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=67(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scalping_scanner_heavy_eval_completion` count=`3531` routing=`reviewed_unknown_token_provenance` fields=`venue=11(reviewed_scanner_venue_fail_closed_provenance), effective_venue=11(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_heavy_eval_lag` count=`3482` routing=`reviewed_unknown_token_provenance` fields=`venue=11(reviewed_scanner_venue_fail_closed_provenance), effective_venue=11(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_watch_not_rising_skipped` count=`1315` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1315(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalping_scanner_watch_eviction` count=`1302` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalping_scanner_ws_backoff_watch_retained` count=`867` routing=`reviewed_unknown_token_provenance` fields=`venue=1(reviewed_scanner_venue_fail_closed_provenance), effective_venue=1(reviewed_scanner_venue_fail_closed_provenance)`
- `scalp_entry_action_decision_snapshot` count=`814` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=568(reviewed_rising_missed_nxt_eligibility_not_available), score_prior_band=49(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=49(reviewed_score_prior_neutral_unknown_not_decision_input), entry_order_flow_status=32(reviewed_entry_order_flow_not_available), entry_score_source=17(reviewed_entry_score_source_not_available), entry_recheck_excluded_reason=17(reviewed_entry_score_source_not_available), entry_score_excluded_reason=17(reviewed_entry_score_source_not_available), tier_reason=8(reviewed_explicit_sizing_unknown_venue_fallback)`
- `ai_holding_review` count=`743` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=13(reviewed_entry_order_flow_not_available)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`516` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=516(reviewed_rising_missed_nxt_eligibility_not_available), effective_venue=9(reviewed_rising_missed_explicit_venue_conflict), tier_reason=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback), venue=5(reviewed_rising_missed_explicit_venue_conflict), venue=4(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_entry_turn_pre_anchor_bbo_path` count=`514` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=124(reviewed_rising_missed_nxt_eligibility_not_available), effective_venue=9(reviewed_rising_missed_explicit_venue_conflict), tier_reason=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback), venue=5(reviewed_rising_missed_explicit_venue_conflict), venue=4(reviewed_explicit_sizing_unknown_venue_fallback)`
- `entry_submit_attempt_finished` count=`442` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=433(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=11(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=11(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=11(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_one_share_entry` count=`436` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=436(reviewed_rising_missed_nxt_eligibility_not_available), effective_venue=2(reviewed_rising_missed_explicit_venue_conflict), tier_reason=1(reviewed_explicit_sizing_unknown_venue_fallback), venue=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback), venue=1(reviewed_rising_missed_explicit_venue_conflict)`
- `budget_pass` count=`428` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=419(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=8(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=8(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=8(reviewed_explicit_sizing_unknown_venue_fallback)`
- `orderbook_stability_observed` count=`427` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=418(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=8(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=8(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=8(reviewed_explicit_sizing_unknown_venue_fallback)`
- `reversal_add_blocked_reason` count=`323` routing=`reviewed_unknown_token_provenance` fields=`shallow_tick_context_stale=3(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=3(reviewed_shallow_stale_flag_not_available), tick_context_stale=3(reviewed_stale_flag_not_available), quote_stale=3(reviewed_stale_flag_not_available)`
- `rising_missed_tp1_candidate_blocked` count=`321` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=321(reviewed_rising_missed_nxt_eligibility_not_available)`
- `prev_close_gainer_entry_ai_handoff` count=`313` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=293(reviewed_rising_missed_nxt_eligibility_not_available)`

## Top Stages
- `scalping_scanner_candidate_pruned`: `44654`
- `scalping_scanner_prune_bbo_schedule`: `33767`
- `scalping_scanner_promotion_latency_trace`: `15663`
- `scalping_scanner_fast_precheck`: `12181`
- `scalping_scanner_runtime_queue_lag`: `8338`
- `scalping_scanner_watching_runtime_skip`: `5386`
- `risky_micro_episode_executable_bbo_observed`: `4280`
- `scalping_scanner_heavy_eval_completion`: `3531`
- `scalping_scanner_heavy_eval_lag`: `3482`
- `scalping_scanner_runtime_target_attach`: `2311`
- `bad_entry_refined_candidate`: `1748`
- `scalping_scanner_source_fetch_census`: `1540`
- `scalping_scanner_prune_bbo_observation`: `1488`
- `scalping_scanner_candidate_promoted`: `1395`
- `avg_down_exit_replay_frame_observed`: `1336`
- `rising_missed_watch_not_rising_skipped`: `1315`
- `scalping_scanner_watch_eviction`: `1302`
- `scalping_scanner_candidate_observed`: `966`
- `scalping_scanner_real_source_guard_block`: `966`
- `scalping_scanner_ws_backoff_watch_retained`: `867`

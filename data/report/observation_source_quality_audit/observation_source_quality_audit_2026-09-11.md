# Observation Source Quality Audit - 2026-09-11

- status: `warning`
- event_count: `344412`
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
- `scalping_scanner_source_fetch_census` count=`2860` routing=`source_quality_blocker_or_provenance_backfill` fields=`scanner_source_rows_json=2570(0.8986), venue=10(0.0035), effective_venue=10(0.0035)`
- `scalping_scanner_candidate_pool_census` count=`280` routing=`source_quality_blocker_or_provenance_backfill` fields=`scanner_source_rows_json=280(1.0)`
- `scalp_fast_exit_quote_blocked` count=`36` routing=`source_quality_blocker_or_provenance_backfill` fields=`fast_exit_ws_0d_route=3(0.0833)`
- `scale_in_ai_authority_retry` count=`31` routing=`source_quality_blocker_or_provenance_backfill` fields=`ai_input_preflight_source_timing=2(0.0645)`

## Reviewed Unknown Token Findings
- `scalping_scanner_promotion_latency_trace` count=`42429` routing=`reviewed_unknown_token_provenance` fields=`venue=57(reviewed_scanner_venue_fail_closed_provenance), effective_venue=57(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_fast_precheck` count=`33673` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=756(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=440(reviewed_scanner_stale_backoff_route_not_available), venue=46(reviewed_scanner_venue_fail_closed_provenance), effective_venue=46(reviewed_scanner_venue_fail_closed_provenance), scanner_promotion_reanchor_effective_venue=46(reviewed_scanner_venue_fail_closed_provenance), scanner_stale_backoff_canonical_effective_venue=46(reviewed_scanner_venue_fail_closed_provenance), rising_missed_submit_safety_backoff_reason=4(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `scalping_scanner_runtime_queue_lag` count=`19909` routing=`reviewed_unknown_token_provenance` fields=`venue=27(reviewed_scanner_venue_fail_closed_provenance), effective_venue=27(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_watching_runtime_skip` count=`14312` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=876(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=67(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=67(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=67(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_effective_venue=1(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalping_scanner_heavy_eval_completion` count=`8982` routing=`reviewed_unknown_token_provenance` fields=`venue=11(reviewed_scanner_venue_fail_closed_provenance), effective_venue=11(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_heavy_eval_lag` count=`8756` routing=`reviewed_unknown_token_provenance` fields=`venue=11(reviewed_scanner_venue_fail_closed_provenance), effective_venue=11(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_watch_not_rising_skipped` count=`2819` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1653(reviewed_rising_missed_nxt_eligibility_not_available), venue=132(reviewed_observation_only_venue_not_available), rising_missed_effective_venue=132(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalping_scanner_watch_eviction` count=`2533` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`2431` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=600(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=12(reviewed_rising_missed_nxt_eligibility_not_available), effective_venue=9(reviewed_rising_missed_explicit_venue_conflict), tier_reason=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback), venue=5(reviewed_rising_missed_explicit_venue_conflict), venue=4(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_entry_turn_pre_anchor_bbo_path` count=`2423` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=136(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=12(reviewed_rising_missed_nxt_eligibility_not_available), effective_venue=9(reviewed_rising_missed_explicit_venue_conflict), tier_reason=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback), venue=5(reviewed_rising_missed_explicit_venue_conflict), venue=4(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scalping_scanner_ws_backoff_watch_retained` count=`1758` routing=`reviewed_unknown_token_provenance` fields=`venue=1(reviewed_scanner_venue_fail_closed_provenance), effective_venue=1(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_tp1_candidate_deferred` count=`1728` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=233(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=11(reviewed_rising_missed_nxt_eligibility_not_available), effective_venue=9(reviewed_rising_missed_explicit_venue_conflict), tier_reason=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback), venue=5(reviewed_rising_missed_explicit_venue_conflict), venue=4(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scalp_entry_action_decision_snapshot` count=`1069` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=616(reviewed_rising_missed_nxt_eligibility_not_available), score_prior_band=69(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=69(reviewed_score_prior_neutral_unknown_not_decision_input), entry_order_flow_status=51(reviewed_entry_order_flow_not_available), entry_score_source=19(reviewed_entry_score_source_not_available), entry_recheck_excluded_reason=19(reviewed_entry_score_source_not_available), entry_score_excluded_reason=19(reviewed_entry_score_source_not_available), tier_reason=8(reviewed_explicit_sizing_unknown_venue_fallback)`
- `ai_holding_review` count=`864` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=21(reviewed_entry_order_flow_not_available), holding_context_blockers=5(reviewed_holding_input_preflight_blocked_provenance)`
- `rising_missed_tp1_candidate_blocked` count=`703` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=367(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=1(reviewed_rising_missed_nxt_eligibility_not_available)`
- `entry_submit_attempt_finished` count=`576` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=482(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=11(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=11(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=11(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_effective_venue=1(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_one_share_entry` count=`565` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=484(reviewed_rising_missed_nxt_eligibility_not_available), effective_venue=2(reviewed_rising_missed_explicit_venue_conflict), tier_reason=1(reviewed_explicit_sizing_unknown_venue_fallback), venue=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback), venue=1(reviewed_rising_missed_explicit_venue_conflict), rising_missed_effective_venue=1(reviewed_rising_missed_nxt_eligibility_not_available)`
- `budget_pass` count=`551` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=460(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=8(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=8(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=8(reviewed_explicit_sizing_unknown_venue_fallback)`
- `orderbook_stability_observed` count=`551` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=460(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=8(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=8(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=8(reviewed_explicit_sizing_unknown_venue_fallback)`
- `prev_close_gainer_entry_ai_handoff` count=`526` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=330(reviewed_rising_missed_nxt_eligibility_not_available), venue=1(reviewed_observation_only_venue_not_available), rising_missed_effective_venue=1(reviewed_rising_missed_nxt_eligibility_not_available)`

## Top Stages
- `scalping_scanner_candidate_pruned`: `83615`
- `scalping_scanner_prune_bbo_schedule`: `58883`
- `scalping_scanner_promotion_latency_trace`: `42429`
- `scalping_scanner_fast_precheck`: `33673`
- `scalping_scanner_runtime_queue_lag`: `19909`
- `scalping_scanner_watching_runtime_skip`: `14312`
- `rising_missed_nxt_post_block_price_sample`: `9668`
- `scalping_scanner_heavy_eval_completion`: `8982`
- `scalping_scanner_heavy_eval_lag`: `8756`
- `scalping_scanner_runtime_target_attach`: `6899`
- `risky_micro_episode_executable_bbo_observed`: `4983`
- `scalping_scanner_candidate_observed`: `3874`
- `scalping_scanner_real_source_guard_block`: `3874`
- `scalping_scanner_source_fetch_census`: `2860`
- `rising_missed_watch_not_rising_skipped`: `2819`
- `scalping_scanner_candidate_promoted`: `2778`
- `scalping_scanner_prune_bbo_observation`: `2543`
- `scalping_scanner_watch_eviction`: `2533`
- `rising_missed_tp1_counterfactual_submit_safety`: `2431`
- `rising_missed_entry_turn_pre_anchor_bbo_path`: `2423`

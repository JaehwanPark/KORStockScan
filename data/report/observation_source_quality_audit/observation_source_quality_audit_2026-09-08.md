# Observation Source Quality Audit - 2026-09-08

- status: `warning`
- event_count: `212051`
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
- `stat_action_decision_snapshot` count=`307` routing=`source_quality_blocker_or_provenance_backfill` fields=`score_prior_band=48(0.1564)`

## Reviewed Unknown Token Findings
- `scalping_scanner_fast_precheck` count=`25093` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=1096(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=814(reviewed_scanner_stale_backoff_route_not_available), rising_missed_submit_safety_backoff_reason=1(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `scalping_scanner_watching_runtime_skip` count=`7330` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=878(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=15(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=15(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=15(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_watch_not_rising_skipped` count=`3961` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=3961(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`1668` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1668(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=6(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=6(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=6(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_tp1_candidate_blocked` count=`1245` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1245(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_entry_turn_pre_anchor_bbo_path` count=`1187` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=509(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=6(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=6(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=6(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scalp_entry_action_decision_snapshot` count=`1023` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=806(reviewed_rising_missed_nxt_eligibility_not_available), entry_order_flow_status=135(reviewed_entry_order_flow_not_available), score_prior_band=42(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=42(reviewed_score_prior_neutral_unknown_not_decision_input), tier_reason=30(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=30(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=30(reviewed_explicit_sizing_unknown_venue_fallback), entry_score_source=7(reviewed_entry_score_source_not_available)`
- `strength_momentum_observed` count=`675` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=10(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_one_share_entry` count=`633` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=633(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback)`
- `budget_pass` count=`617` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=617(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=28(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=28(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=28(reviewed_explicit_sizing_unknown_venue_fallback)`
- `orderbook_stability_observed` count=`617` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=617(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=28(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=28(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=28(reviewed_explicit_sizing_unknown_venue_fallback)`
- `blocked_strength_momentum` count=`526` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=6(reviewed_rising_missed_nxt_eligibility_not_available)`
- `risky_micro_episode_source_candidate_observed` count=`428` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=428(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=25(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=25(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=25(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_tp1_candidate_deferred` count=`423` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=423(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback)`
- `entry_submit_attempt_finished` count=`370` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=370(reviewed_rising_missed_nxt_eligibility_not_available)`
- `latency_block` count=`367` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=367(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=23(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=23(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=23(reviewed_explicit_sizing_unknown_venue_fallback)`
- `stat_action_decision_snapshot` count=`307` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=27(reviewed_stale_flag_not_available), quote_stale=27(reviewed_stale_flag_not_available), shallow_tick_context_stale=27(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=27(reviewed_shallow_stale_flag_not_available)`
- `reversal_add_blocked_reason` count=`288` routing=`reviewed_unknown_token_provenance` fields=`shallow_tick_context_stale=29(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=29(reviewed_shallow_stale_flag_not_available), tick_context_stale=29(reviewed_stale_flag_not_available), quote_stale=29(reviewed_stale_flag_not_available)`
- `prev_close_gainer_entry_ai_handoff` count=`234` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=206(reviewed_rising_missed_nxt_eligibility_not_available)`
- `ai_confirmed` count=`224` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=88(reviewed_rising_missed_nxt_eligibility_not_available), entry_order_flow_status=24(reviewed_entry_order_flow_not_available)`

## Top Stages
- `scalping_scanner_candidate_pruned`: `45288`
- `scalping_scanner_promotion_latency_trace`: `32681`
- `scalping_scanner_prune_bbo_schedule`: `31092`
- `scalping_scanner_fast_precheck`: `25093`
- `scalping_scanner_runtime_queue_lag`: `15061`
- `risky_micro_episode_executable_bbo_observed`: `8951`
- `scalping_scanner_heavy_eval_completion`: `7691`
- `scalping_scanner_heavy_eval_lag`: `7588`
- `scalping_scanner_watching_runtime_skip`: `7330`
- `rising_missed_watch_not_rising_skipped`: `3961`
- `scalping_scanner_candidate_observed`: `1937`
- `scalping_scanner_real_source_guard_block`: `1937`
- `rising_missed_tp1_counterfactual_submit_safety`: `1668`
- `scalping_scanner_runtime_target_attach`: `1651`
- `scalping_scanner_prune_bbo_observation`: `1639`
- `scalping_scanner_candidate_promoted`: `1524`
- `scalping_scanner_watch_eviction`: `1328`
- `rising_missed_tp1_candidate_blocked`: `1245`
- `rising_missed_entry_turn_pre_anchor_bbo_path`: `1187`
- `scalp_entry_action_decision_snapshot`: `1023`

# Observation Source Quality Audit - 2026-09-08

- status: `warning`
- event_count: `379029`
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
- `stat_action_decision_snapshot` count=`345` routing=`source_quality_blocker_or_provenance_backfill` fields=`score_prior_band=61(0.1768)`

## Reviewed Unknown Token Findings
- `scalping_scanner_fast_precheck` count=`47118` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=1549(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=1139(reviewed_scanner_stale_backoff_route_not_available), rising_missed_submit_safety_backoff_reason=1(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `scalping_scanner_watching_runtime_skip` count=`13617` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=878(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=15(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=15(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=15(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_nxt_post_block_price_sample` count=`11042` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_post_block_ws_0b_route=83(reviewed_rising_missed_nxt_post_block_route_not_available), rising_missed_nxt_post_block_ws_0d_route=65(reviewed_rising_missed_nxt_post_block_route_not_available)`
- `rising_missed_watch_not_rising_skipped` count=`7007` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=4153(reviewed_rising_missed_nxt_eligibility_not_available), venue=192(reviewed_observation_only_venue_not_available), rising_missed_effective_venue=192(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`3329` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1668(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=6(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=6(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=6(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_entry_turn_pre_anchor_bbo_path` count=`2842` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=509(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=6(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=6(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=6(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_tp1_candidate_deferred` count=`1812` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=423(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_tp1_candidate_blocked` count=`1517` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1245(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scalp_entry_action_decision_snapshot` count=`1194` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=806(reviewed_rising_missed_nxt_eligibility_not_available), entry_order_flow_status=149(reviewed_entry_order_flow_not_available), score_prior_band=51(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=51(reviewed_score_prior_neutral_unknown_not_decision_input), tier_reason=30(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=30(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=30(reviewed_explicit_sizing_unknown_venue_fallback), entry_score_source=11(reviewed_entry_score_source_not_available)`
- `strength_momentum_observed` count=`1183` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=10(reviewed_rising_missed_nxt_eligibility_not_available)`
- `blocked_strength_momentum` count=`894` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=6(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_one_share_entry` count=`714` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=633(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback)`
- `budget_pass` count=`694` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=617(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=28(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=28(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=28(reviewed_explicit_sizing_unknown_venue_fallback)`
- `orderbook_stability_observed` count=`694` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=617(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=28(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=28(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=28(reviewed_explicit_sizing_unknown_venue_fallback)`
- `risky_micro_episode_source_candidate_observed` count=`474` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=428(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=25(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=25(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=25(reviewed_explicit_sizing_unknown_venue_fallback)`
- `entry_submit_attempt_finished` count=`451` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=370(reviewed_rising_missed_nxt_eligibility_not_available)`
- `latency_block` count=`401` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=367(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=23(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=23(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=23(reviewed_explicit_sizing_unknown_venue_fallback)`
- `prev_close_gainer_entry_ai_handoff` count=`373` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=209(reviewed_rising_missed_nxt_eligibility_not_available), venue=3(reviewed_observation_only_venue_not_available), rising_missed_effective_venue=3(reviewed_rising_missed_nxt_eligibility_not_available)`
- `stat_action_decision_snapshot` count=`345` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=28(reviewed_stale_flag_not_available), quote_stale=28(reviewed_stale_flag_not_available), shallow_tick_context_stale=27(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=27(reviewed_shallow_stale_flag_not_available)`
- `reversal_add_blocked_reason` count=`306` routing=`reviewed_unknown_token_provenance` fields=`shallow_tick_context_stale=29(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=29(reviewed_shallow_stale_flag_not_available), tick_context_stale=29(reviewed_stale_flag_not_available), quote_stale=29(reviewed_stale_flag_not_available)`

## Top Stages
- `scalping_scanner_candidate_pruned`: `77426`
- `scalping_scanner_promotion_latency_trace`: `60466`
- `scalping_scanner_prune_bbo_schedule`: `47185`
- `scalping_scanner_fast_precheck`: `47118`
- `scalping_scanner_runtime_queue_lag`: `26779`
- `scalping_scanner_watching_runtime_skip`: `13617`
- `scalping_scanner_heavy_eval_completion`: `13592`
- `scalping_scanner_heavy_eval_lag`: `13348`
- `rising_missed_nxt_post_block_price_sample`: `11042`
- `risky_micro_episode_executable_bbo_observed`: `8951`
- `scalping_scanner_candidate_observed`: `8095`
- `scalping_scanner_real_source_guard_block`: `8095`
- `rising_missed_watch_not_rising_skipped`: `7007`
- `rising_missed_tp1_counterfactual_submit_safety`: `3329`
- `rising_missed_entry_turn_pre_anchor_bbo_path`: `2842`
- `scalping_scanner_runtime_target_attach`: `2775`
- `scalping_scanner_candidate_promoted`: `2538`
- `scalping_scanner_prune_bbo_observation`: `2511`
- `scalping_scanner_watch_eviction`: `2169`
- `rising_missed_tp1_candidate_deferred`: `1812`

# Observation Source Quality Audit - 2026-07-22

- status: `pass`
- event_count: `87926`
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
- `scalping_scanner_watching_runtime_skip` count=`9356` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=174(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=156(reviewed_explicit_sizing_unknown_venue_fallback), venue=156(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scalping_scanner_fast_precheck` count=`8051` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_submit_safety_backoff_reason=30(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `rising_missed_nxt_post_block_price_sample` count=`3026` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_post_block_selector_reason=93(reviewed_nxt_post_block_source_gap_provenance), rising_missed_nxt_post_block_source_block_reason=93(reviewed_nxt_post_block_source_gap_provenance), rising_missed_nxt_post_block_ws_0b_route=17(reviewed_rising_missed_nxt_post_block_route_not_available), rising_missed_nxt_post_block_ws_0d_route=14(reviewed_rising_missed_nxt_post_block_route_not_available)`
- `stat_action_decision_snapshot` count=`1133` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=63(reviewed_stale_flag_not_available), quote_stale=63(reviewed_stale_flag_not_available), shallow_tick_context_stale=63(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=63(reviewed_shallow_stale_flag_not_available)`
- `ai_holding_review` count=`996` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=206(reviewed_entry_order_flow_not_available)`
- `rising_missed_one_share_entry` count=`278` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=223(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=38(reviewed_explicit_sizing_unknown_venue_fallback), venue=38(reviewed_explicit_sizing_unknown_venue_fallback)`
- `budget_pass` count=`277` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=220(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=197(reviewed_explicit_sizing_unknown_venue_fallback), venue=197(reviewed_explicit_sizing_unknown_venue_fallback)`
- `orderbook_stability_observed` count=`277` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=220(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=197(reviewed_explicit_sizing_unknown_venue_fallback), venue=197(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scalp_entry_action_decision_snapshot` count=`270` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=143(reviewed_entry_order_flow_not_available), tier_reason=130(reviewed_explicit_sizing_unknown_venue_fallback), venue=130(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_nxt_eligible=116(reviewed_rising_missed_nxt_eligibility_not_available), holding_exit_matrix_score_prior_band=103(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_band=37(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=37(reviewed_score_prior_neutral_unknown_not_decision_input), risk_regime_context=29(reviewed_missing_risk_regime_context)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`197` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=175(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=41(reviewed_explicit_sizing_unknown_venue_fallback), venue=41(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scalp_trailing_continuation_recheck` count=`187` routing=`reviewed_unknown_token_provenance` fields=`quote_recovery_large_sell_state=113(reviewed_quote_recovery_large_sell_not_available)`
- `rising_missed_tp1_candidate_blocked` count=`184` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=165(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=40(reviewed_explicit_sizing_unknown_venue_fallback), venue=40(reviewed_explicit_sizing_unknown_venue_fallback)`
- `entry_ai_price_canary_applied` count=`142` routing=`reviewed_unknown_token_provenance` fields=`tier_reason=109(reviewed_explicit_sizing_unknown_venue_fallback), venue=109(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_nxt_eligible=99(reviewed_rising_missed_nxt_eligibility_not_available), entry_order_flow_status=18(reviewed_entry_order_flow_not_available)`
- `ai_confirmed` count=`78` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=40(reviewed_entry_order_flow_not_available), rising_missed_nxt_eligible=23(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=23(reviewed_explicit_sizing_unknown_venue_fallback), venue=23(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_nxt_post_block_price_sampler_completed` count=`66` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_post_block_selector_reason=2(reviewed_nxt_post_block_source_gap_provenance), rising_missed_nxt_post_block_source_block_reason=2(reviewed_nxt_post_block_source_gap_provenance)`
- `rising_missed_nxt_post_block_sampler_registered` count=`66` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_post_block_selector_reason=2(reviewed_nxt_post_block_source_gap_provenance), rising_missed_nxt_post_block_source_block_reason=2(reviewed_nxt_post_block_source_gap_provenance)`
- `probe_continuation_deferred` count=`58` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=58(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=58(reviewed_explicit_sizing_unknown_venue_fallback), venue=58(reviewed_explicit_sizing_unknown_venue_fallback), post_probe_direction_state=33(reviewed_post_probe_direction_source_gap)`
- `real_weak_ai_micro_entry_block` count=`57` routing=`reviewed_unknown_token_provenance` fields=`reason=57(reviewed_entry_block_source_quality_unknown_provenance), block_reason=57(reviewed_entry_block_source_quality_unknown_provenance), rising_missed_submit_safety_backoff_reason=57(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance), rising_missed_nxt_eligible=55(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=52(reviewed_explicit_sizing_unknown_venue_fallback), venue=52(reviewed_explicit_sizing_unknown_venue_fallback)`
- `ai_confirmed_terminal_no_budget` count=`56` routing=`reviewed_unknown_token_provenance` fields=`score_prior_band=37(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=37(reviewed_score_prior_neutral_unknown_not_decision_input), entry_order_flow_status=32(reviewed_entry_order_flow_not_available), entry_score_source=13(reviewed_entry_score_source_not_available), entry_score_excluded_reason=13(reviewed_entry_score_source_not_available)`
- `rising_missed_scout_allocator_order_plan` count=`39` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=28(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=27(reviewed_explicit_sizing_unknown_venue_fallback), venue=27(reviewed_explicit_sizing_unknown_venue_fallback)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `10198`
- `scalping_scanner_watching_runtime_skip`: `9356`
- `scalping_scanner_fast_precheck`: `8051`
- `scalping_scanner_candidate_observed`: `7448`
- `scalping_scanner_real_source_guard_block`: `7448`
- `scalping_scanner_runtime_queue_lag`: `6755`
- `scalping_scanner_runtime_target_attach`: `6574`
- `scalping_scanner_candidate_promoted`: `3603`
- `scalping_scanner_watch_eviction`: `3471`
- `rising_missed_nxt_post_block_price_sample`: `3026`
- `scalping_scanner_heavy_eval_lag`: `2147`
- `holding_ws_freshness_blocked`: `1929`
- `bad_entry_refined_candidate`: `1901`
- `opening_rotation_1pct_upstream_blocked`: `1807`
- `rising_missed_watch_not_rising_skipped`: `1491`
- `stat_action_decision_snapshot`: `1133`
- `ai_holding_fast_reuse_band`: `1010`
- `ai_holding_reuse_bypass`: `998`
- `ai_holding_review`: `996`
- `scale_in_feature_context_refresh`: `731`

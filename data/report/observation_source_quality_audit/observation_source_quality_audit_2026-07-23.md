# Observation Source Quality Audit - 2026-07-23

- status: `pass`
- event_count: `77960`
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
- `scalping_scanner_watching_runtime_skip` count=`6446` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=133(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=20(reviewed_explicit_sizing_unknown_venue_fallback), venue=20(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_watch_not_rising_skipped` count=`2201` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=2(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_nxt_post_block_price_sample` count=`1971` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_post_block_ws_0b_route=42(reviewed_rising_missed_nxt_post_block_route_not_available), rising_missed_nxt_post_block_ws_0d_route=32(reviewed_rising_missed_nxt_post_block_route_not_available)`
- `opening_rotation_1pct_upstream_blocked` count=`967` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=2(reviewed_rising_missed_nxt_eligibility_not_available)`
- `opening_rotation_1pct_observed` count=`716` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=33(reviewed_rising_missed_nxt_eligibility_not_available)`
- `stat_action_decision_snapshot` count=`708` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=16(reviewed_stale_flag_not_available), quote_stale=16(reviewed_stale_flag_not_available), shallow_tick_context_stale=16(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=16(reviewed_shallow_stale_flag_not_available)`
- `ai_holding_review` count=`529` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=115(reviewed_entry_order_flow_not_available)`
- `reversal_add_blocked_reason` count=`311` routing=`reviewed_unknown_token_provenance` fields=`state=311(reviewed_reversal_state_not_initialized)`
- `scalp_entry_action_decision_snapshot` count=`279` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=141(reviewed_entry_order_flow_not_available), rising_missed_nxt_eligible=124(reviewed_rising_missed_nxt_eligibility_not_available), holding_exit_matrix_score_prior_band=108(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_band=43(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=43(reviewed_score_prior_neutral_unknown_not_decision_input), tier_reason=22(reviewed_explicit_sizing_unknown_venue_fallback), venue=22(reviewed_explicit_sizing_unknown_venue_fallback), entry_score_source=14(reviewed_entry_score_source_not_available)`
- `budget_pass` count=`202` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=153(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=23(reviewed_explicit_sizing_unknown_venue_fallback), venue=23(reviewed_explicit_sizing_unknown_venue_fallback)`
- `orderbook_stability_observed` count=`202` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=153(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=23(reviewed_explicit_sizing_unknown_venue_fallback), venue=23(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_one_share_entry` count=`202` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=153(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalp_trailing_continuation_recheck` count=`183` routing=`reviewed_unknown_token_provenance` fields=`quote_recovery_large_sell_state=174(reviewed_quote_recovery_large_sell_not_available)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`137` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=116(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_candidate_blocked` count=`120` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=102(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalp_fast_exit_quote_blocked` count=`113` routing=`reviewed_unknown_token_provenance` fields=`fast_exit_route_resolution_reason=15(reviewed_legacy_fast_exit_route_provenance), fast_exit_execution_cohort=1(reviewed_legacy_fast_exit_route_provenance)`
- `ai_confirmed` count=`78` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=52(reviewed_entry_order_flow_not_available), rising_missed_nxt_eligible=17(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=2(reviewed_explicit_sizing_unknown_venue_fallback), venue=2(reviewed_explicit_sizing_unknown_venue_fallback)`
- `ai_confirmed_terminal_no_budget` count=`77` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=60(reviewed_entry_order_flow_not_available), score_prior_band=43(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=43(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=15(reviewed_entry_score_source_not_available), entry_score_excluded_reason=15(reviewed_entry_score_source_not_available)`
- `entry_ai_price_canary_applied` count=`75` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=50(reviewed_rising_missed_nxt_eligibility_not_available), entry_order_flow_status=39(reviewed_entry_order_flow_not_available), tier_reason=16(reviewed_explicit_sizing_unknown_venue_fallback), venue=16(reviewed_explicit_sizing_unknown_venue_fallback)`
- `probe_continuation_deferred` count=`71` routing=`reviewed_unknown_token_provenance` fields=`post_probe_direction_state=71(reviewed_post_probe_direction_source_gap), rising_missed_nxt_eligible=53(reviewed_rising_missed_nxt_eligibility_not_available)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `10757`
- `scalping_scanner_fast_precheck`: `7772`
- `scalping_scanner_candidate_observed`: `7253`
- `scalping_scanner_real_source_guard_block`: `7253`
- `scalping_scanner_watching_runtime_skip`: `6446`
- `scalping_scanner_runtime_queue_lag`: `6284`
- `scalping_scanner_runtime_target_attach`: `6233`
- `scalping_scanner_heavy_eval_lag`: `2984`
- `scalping_scanner_candidate_promoted`: `2944`
- `scalping_scanner_watch_eviction`: `2583`
- `rising_missed_watch_not_rising_skipped`: `2201`
- `rising_missed_nxt_post_block_price_sample`: `1971`
- `bad_entry_refined_candidate`: `1086`
- `opening_rotation_1pct_upstream_blocked`: `967`
- `opening_rotation_1pct_observed`: `716`
- `stat_action_decision_snapshot`: `708`
- `early_volatility_tp_decision_observed`: `674`
- `scale_in_ai_authority_retry`: `594`
- `manual_control_fast_exit_monitor_blocked`: `551`
- `ai_holding_fast_reuse_band`: `549`

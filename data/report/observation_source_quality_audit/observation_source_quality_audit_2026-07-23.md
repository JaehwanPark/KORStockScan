# Observation Source Quality Audit - 2026-07-23

- status: `warning`
- event_count: `55654`
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
- `scalp_trailing_continuation_recheck` count=`183` routing=`source_quality_blocker_or_provenance_backfill` fields=`quote_recovery_large_sell_state=3(0.0164)`
- `probe_continuation_deferred` count=`41` routing=`source_quality_blocker_or_provenance_backfill` fields=`post_probe_direction_state=41(1.0)`
- `reversal_add_blocked_reason` count=`15` routing=`source_quality_blocker_or_provenance_backfill` fields=`state=15(1.0)`

## Reviewed Unknown Token Findings
- `scalping_scanner_watching_runtime_skip` count=`3360` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=133(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=19(reviewed_explicit_sizing_unknown_venue_fallback), venue=19(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_watch_not_rising_skipped` count=`2097` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=2(reviewed_rising_missed_nxt_eligibility_not_available)`
- `opening_rotation_1pct_upstream_blocked` count=`967` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=2(reviewed_rising_missed_nxt_eligibility_not_available)`
- `opening_rotation_1pct_observed` count=`716` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=33(reviewed_rising_missed_nxt_eligibility_not_available)`
- `stat_action_decision_snapshot` count=`357` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=16(reviewed_stale_flag_not_available), quote_stale=16(reviewed_stale_flag_not_available), shallow_tick_context_stale=16(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=16(reviewed_shallow_stale_flag_not_available)`
- `scalp_entry_action_decision_snapshot` count=`236` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=126(reviewed_entry_order_flow_not_available), rising_missed_nxt_eligible=121(reviewed_rising_missed_nxt_eligibility_not_available), holding_exit_matrix_score_prior_band=104(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_band=43(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=43(reviewed_score_prior_neutral_unknown_not_decision_input), tier_reason=21(reviewed_explicit_sizing_unknown_venue_fallback), venue=21(reviewed_explicit_sizing_unknown_venue_fallback), entry_score_source=14(reviewed_entry_score_source_not_available)`
- `scalp_trailing_continuation_recheck` count=`183` routing=`reviewed_unknown_token_provenance` fields=`quote_recovery_large_sell_state=171(reviewed_quote_recovery_large_sell_not_available)`
- `budget_pass` count=`152` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=152(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=22(reviewed_explicit_sizing_unknown_venue_fallback), venue=22(reviewed_explicit_sizing_unknown_venue_fallback)`
- `orderbook_stability_observed` count=`152` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=152(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=22(reviewed_explicit_sizing_unknown_venue_fallback), venue=22(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_one_share_entry` count=`152` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=152(reviewed_rising_missed_nxt_eligibility_not_available)`
- `ai_holding_review` count=`150` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=14(reviewed_entry_order_flow_not_available)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`115` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=115(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_candidate_blocked` count=`102` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=102(reviewed_rising_missed_nxt_eligibility_not_available)`
- `ai_confirmed_terminal_no_budget` count=`77` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=60(reviewed_entry_order_flow_not_available), score_prior_band=43(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=43(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=15(reviewed_entry_score_source_not_available), entry_score_excluded_reason=15(reviewed_entry_score_source_not_available)`
- `ai_confirmed` count=`74` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=50(reviewed_entry_order_flow_not_available), rising_missed_nxt_eligible=16(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=2(reviewed_explicit_sizing_unknown_venue_fallback), venue=2(reviewed_explicit_sizing_unknown_venue_fallback)`
- `entry_ai_price_canary_applied` count=`61` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=49(reviewed_rising_missed_nxt_eligibility_not_available), entry_order_flow_status=28(reviewed_entry_order_flow_not_available), tier_reason=16(reviewed_explicit_sizing_unknown_venue_fallback), venue=16(reviewed_explicit_sizing_unknown_venue_fallback)`
- `probe_continuation_deferred` count=`41` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=41(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tick_speed_entry_block` count=`31` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=31(reviewed_rising_missed_nxt_eligibility_not_available), entry_order_flow_status=15(reviewed_entry_order_flow_not_available), tier_reason=2(reviewed_explicit_sizing_unknown_venue_fallback), venue=2(reviewed_explicit_sizing_unknown_venue_fallback)`
- `latency_block` count=`30` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=30(reviewed_rising_missed_nxt_eligibility_not_available)`
- `blocked_ai_score` count=`23` routing=`reviewed_unknown_token_provenance` fields=`score_prior_band=19(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=19(reviewed_score_prior_neutral_unknown_not_decision_input), entry_order_flow_status=14(reviewed_entry_order_flow_not_available), entry_score_source=14(reviewed_entry_score_source_not_available), entry_score_excluded_reason=14(reviewed_entry_score_source_not_available)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `8379`
- `scalping_scanner_candidate_observed`: `7160`
- `scalping_scanner_real_source_guard_block`: `7160`
- `scalping_scanner_fast_precheck`: `5628`
- `scalping_scanner_runtime_queue_lag`: `4442`
- `scalping_scanner_runtime_target_attach`: `3737`
- `scalping_scanner_watching_runtime_skip`: `3360`
- `scalping_scanner_heavy_eval_lag`: `2750`
- `rising_missed_watch_not_rising_skipped`: `2097`
- `scalping_scanner_candidate_promoted`: `1786`
- `scalping_scanner_watch_eviction`: `1460`
- `opening_rotation_1pct_upstream_blocked`: `967`
- `opening_rotation_1pct_observed`: `716`
- `stat_action_decision_snapshot`: `357`
- `bad_entry_refined_candidate`: `324`
- `scalping_scanner_watch_budget_reallocated`: `265`
- `manual_control_fast_exit_monitor_blocked`: `264`
- `holding_ws_freshness_blocked`: `250`
- `scalp_entry_action_decision_snapshot`: `236`
- `exit_signal`: `201`

# Observation Source Quality Audit - 2026-07-29

- status: `pass`
- event_count: `101695`
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
- `scalping_scanner_watching_runtime_skip` count=`16851` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=338(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=231(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scalping_scanner_runtime_target_attach` count=`15145` routing=`reviewed_unknown_token_provenance` fields=`venue=14644(reviewed_scanner_venue_fail_closed_provenance), effective_venue=14644(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_nxt_post_block_price_sample` count=`5868` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_post_block_ws_0b_route=40(reviewed_rising_missed_nxt_post_block_route_not_available), rising_missed_nxt_post_block_ws_0d_route=40(reviewed_rising_missed_nxt_post_block_route_not_available)`
- `scalping_scanner_fast_precheck` count=`3193` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=499(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=476(reviewed_scanner_stale_backoff_route_not_available)`
- `opening_rotation_1pct_upstream_blocked` count=`2707` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=8(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_async_commit_phase` count=`966` routing=`reviewed_unknown_token_provenance` fields=`tier_reason=13(reviewed_explicit_sizing_unknown_venue_fallback), entry_order_flow_status=11(reviewed_entry_order_flow_not_available), rising_missed_nxt_eligible=10(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_watch_not_rising_skipped` count=`706` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=598(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_async_freshness_dispatched` count=`657` routing=`reviewed_unknown_token_provenance` fields=`tier_reason=8(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_nxt_eligible=7(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_async_freshness_commit` count=`638` routing=`reviewed_unknown_token_provenance` fields=`tier_reason=8(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_nxt_eligible=7(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scanner_async_eval_dispatched` count=`517` routing=`reviewed_unknown_token_provenance` fields=`tier_reason=7(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_nxt_eligible=5(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scanner_async_result_commit` count=`483` routing=`reviewed_unknown_token_provenance` fields=`tier_reason=7(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_nxt_eligible=4(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_entry_ai_async_result_applied` count=`459` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=11(reviewed_entry_order_flow_not_available), tier_reason=7(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_nxt_eligible=4(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalping_scanner_scheduler_generation_invalidated` count=`338` routing=`reviewed_unknown_token_provenance` fields=`venue=338(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`273` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=122(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=3(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_one_share_entry_blocked` count=`164` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=50(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=4(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_tp1_candidate_deferred` count=`150` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=67(reviewed_rising_missed_nxt_eligibility_not_available), entry_order_flow_status=7(reviewed_entry_order_flow_not_available), tier_reason=3(reviewed_explicit_sizing_unknown_venue_fallback)`
- `stat_action_decision_snapshot` count=`147` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=7(reviewed_stale_flag_not_available), quote_stale=7(reviewed_stale_flag_not_available), shallow_tick_context_stale=6(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=6(reviewed_shallow_stale_flag_not_available)`
- `rising_missed_tp1_candidate_blocked` count=`123` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=55(reviewed_rising_missed_nxt_eligibility_not_available), entry_order_flow_status=2(reviewed_entry_order_flow_not_available)`
- `rising_missed_entry_ai_async_pending` count=`114` routing=`reviewed_unknown_token_provenance` fields=`tier_reason=2(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_nxt_eligible=1(reviewed_rising_missed_nxt_eligibility_not_available)`
- `reversal_add_blocked_reason` count=`112` routing=`reviewed_unknown_token_provenance` fields=`shallow_tick_context_stale=6(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=6(reviewed_shallow_stale_flag_not_available), tick_context_stale=6(reviewed_stale_flag_not_available), quote_stale=6(reviewed_stale_flag_not_available)`

## Top Stages
- `scalping_scanner_watching_runtime_skip`: `16851`
- `scalping_scanner_runtime_target_attach`: `15145`
- `scalping_scanner_scheduler_work_completed`: `7940`
- `scalping_scanner_scheduler_work_dispatched`: `7012`
- `scalping_scanner_scheduler_work_enqueued`: `7004`
- `scalping_scanner_scheduler_claim_deferred`: `6363`
- `rising_missed_nxt_post_block_price_sample`: `5868`
- `scalping_scanner_promotion_latency_trace`: `5297`
- `scalping_scanner_candidate_observed`: `3222`
- `scalping_scanner_real_source_guard_block`: `3222`
- `scalping_scanner_fast_precheck`: `3193`
- `opening_rotation_1pct_upstream_blocked`: `2707`
- `scalping_scanner_heavy_eval_lag`: `2104`
- `manual_control_fast_exit_monitor_blocked`: `1399`
- `scalping_scanner_async_transport_ready`: `1199`
- `rising_missed_async_commit_phase`: `966`
- `rising_missed_watch_not_rising_skipped`: `706`
- `scalping_scanner_scheduler_generation_registered`: `666`
- `rising_missed_async_freshness_dispatched`: `657`
- `rising_missed_async_freshness_commit`: `638`

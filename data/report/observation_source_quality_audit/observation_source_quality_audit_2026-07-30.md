# Observation Source Quality Audit - 2026-07-30

- status: `pass`
- event_count: `62744`
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
- `scalping_scanner_runtime_target_attach` count=`15244` routing=`reviewed_unknown_token_provenance` fields=`venue=14836(reviewed_scanner_venue_fail_closed_provenance), effective_venue=14836(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_watching_runtime_skip` count=`15133` routing=`reviewed_unknown_token_provenance` fields=`tier_reason=176(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_nxt_eligible=117(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_nxt_post_block_price_sample` count=`1412` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_post_block_ws_0b_route=8(reviewed_rising_missed_nxt_post_block_route_not_available), rising_missed_nxt_post_block_ws_0d_route=7(reviewed_rising_missed_nxt_post_block_route_not_available)`
- `scalping_scanner_fast_precheck` count=`1286` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=322(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=305(reviewed_scanner_stale_backoff_route_not_available)`
- `stat_action_decision_snapshot` count=`516` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=14(reviewed_stale_flag_not_available), quote_stale=14(reviewed_stale_flag_not_available), shallow_tick_context_stale=14(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=14(reviewed_shallow_stale_flag_not_available)`
- `rising_missed_async_commit_phase` count=`471` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=16(reviewed_entry_order_flow_not_available)`
- `loss_fallback_probe` count=`457` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=457(reviewed_stale_flag_not_available), quote_stale=457(reviewed_stale_flag_not_available)`
- `scalp_fast_exit_quote_blocked` count=`370` routing=`reviewed_unknown_token_provenance` fields=`fast_exit_ws_0d_route=283(reviewed_legacy_fast_exit_route_provenance)`
- `scalping_scanner_scheduler_generation_invalidated` count=`300` routing=`reviewed_unknown_token_provenance` fields=`venue=300(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_watch_not_rising_skipped` count=`274` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=132(reviewed_rising_missed_nxt_eligibility_not_available), venue=7(reviewed_observation_only_venue_not_available)`
- `strength_momentum_observed` count=`221` routing=`reviewed_unknown_token_provenance` fields=`tier_reason=4(reviewed_explicit_sizing_unknown_venue_fallback), venue=4(reviewed_explicit_sizing_unknown_venue_fallback)`
- `blocked_strength_momentum` count=`218` routing=`reviewed_unknown_token_provenance` fields=`tier_reason=4(reviewed_explicit_sizing_unknown_venue_fallback), venue=4(reviewed_explicit_sizing_unknown_venue_fallback)`
- `soft_stop_micro_grace` count=`132` routing=`reviewed_unknown_token_provenance` fields=`soft_stop_dynamic_grace_score_prior_band=132(reviewed_score_prior_neutral_unknown_not_decision_input)`
- `rising_missed_entry_ai_async_result_applied` count=`108` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=12(reviewed_entry_order_flow_not_available)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`69` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=36(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_entry_ai_async_result_unusable` count=`66` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=4(reviewed_entry_order_flow_not_available)`
- `scalp_entry_action_decision_snapshot` count=`64` routing=`reviewed_unknown_token_provenance` fields=`holding_exit_matrix_score_prior_band=42(reviewed_score_prior_neutral_unknown_not_decision_input), tier_reason=16(reviewed_explicit_sizing_unknown_venue_fallback), venue=11(reviewed_explicit_sizing_unknown_venue_fallback), entry_order_flow_status=8(reviewed_entry_order_flow_not_available), entry_score_source=6(reviewed_entry_score_source_not_available), entry_score_excluded_reason=6(reviewed_entry_score_source_not_available), score_prior_band=6(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=6(reviewed_score_prior_neutral_unknown_not_decision_input)`
- `scalping_scanner_ws_prewarm_selected` count=`64` routing=`reviewed_unknown_token_provenance` fields=`venue=16(reviewed_scanner_venue_fail_closed_provenance), effective_venue=16(reviewed_scanner_venue_fail_closed_provenance)`
- `holding_flow_override_exit_confirmed` count=`60` routing=`reviewed_unknown_token_provenance` fields=`flow_state=60(reviewed_canonical_unknown_flow_state)`
- `holding_flow_override_review` count=`60` routing=`reviewed_unknown_token_provenance` fields=`flow_state=60(reviewed_canonical_unknown_flow_state)`

## Top Stages
- `scalping_scanner_runtime_target_attach`: `15244`
- `scalping_scanner_watching_runtime_skip`: `15133`
- `scalping_scanner_scheduler_work_completed`: `3901`
- `scalping_scanner_scheduler_work_dispatched`: `2918`
- `scalping_scanner_scheduler_work_enqueued`: `2608`
- `scalping_scanner_promotion_latency_trace`: `2003`
- `rising_missed_nxt_post_block_price_sample`: `1412`
- `manual_control_fast_exit_monitor_blocked`: `1392`
- `opening_rotation_1pct_upstream_blocked`: `1343`
- `scalping_scanner_fast_precheck`: `1286`
- `stop_line_touch_mandatory_avg_down_not_eligible`: `1129`
- `scalping_scanner_candidate_observed`: `744`
- `scalping_scanner_real_source_guard_block`: `744`
- `scalping_scanner_heavy_eval_lag`: `717`
- `scalping_scanner_async_transport_ready`: `586`
- `scalping_scanner_scheduler_generation_registered`: `552`
- `stat_action_decision_snapshot`: `516`
- `rising_missed_async_commit_phase`: `471`
- `scalping_scanner_scheduler_warm_park_reactivated`: `468`
- `exit_signal`: `459`

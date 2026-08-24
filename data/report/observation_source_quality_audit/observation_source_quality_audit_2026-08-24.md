# Observation Source Quality Audit - 2026-08-24

- status: `pass`
- event_count: `274337`
- tuning_input_policy: `exclude_defective_rows_not_full_day_raw`
- hard_blocking_excluded_row_count: `22`
- pre_exclusion_hard_blocking_excluded_row_count: `22`
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
- `scalping_scanner_promotion_latency_trace` count=`64336` routing=`reviewed_unknown_token_provenance` fields=`venue=4(reviewed_scanner_venue_fail_closed_provenance), effective_venue=4(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_fast_precheck` count=`50994` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=1723(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=504(reviewed_scanner_stale_backoff_route_not_available), venue=4(reviewed_scanner_venue_fail_closed_provenance), effective_venue=4(reviewed_scanner_venue_fail_closed_provenance), scanner_promotion_reanchor_effective_venue=4(reviewed_scanner_venue_fail_closed_provenance), scanner_stale_backoff_canonical_effective_venue=4(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_runtime_queue_lag` count=`28034` routing=`reviewed_unknown_token_provenance` fields=`venue=4(reviewed_scanner_venue_fail_closed_provenance), effective_venue=4(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_watching_runtime_skip` count=`14457` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1049(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=28(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=28(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=28(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scalping_scanner_runtime_target_attach` count=`12688` routing=`reviewed_unknown_token_provenance` fields=`venue=7(reviewed_scanner_venue_fail_closed_provenance), effective_venue=7(reviewed_scanner_venue_fail_closed_provenance), market_session_bucket=7(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_nxt_post_block_price_sample` count=`9714` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_post_block_ws_0b_route=230(reviewed_rising_missed_nxt_post_block_route_not_available), rising_missed_nxt_post_block_ws_0d_route=221(reviewed_rising_missed_nxt_post_block_route_not_available)`
- `rising_missed_watch_not_rising_skipped` count=`6055` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=4476(reviewed_rising_missed_nxt_eligibility_not_available), venue=120(reviewed_observation_only_venue_not_available), rising_missed_effective_venue=47(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`2623` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=845(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=46(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=15(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=15(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=15(reviewed_explicit_sizing_unknown_venue_fallback), venue=1(reviewed_rising_missed_explicit_venue_conflict), effective_venue=1(reviewed_rising_missed_explicit_venue_conflict)`
- `strength_momentum_observed` count=`2211` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=9(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalp_fast_exit_venue_blocked` count=`1794` routing=`reviewed_unknown_token_provenance` fields=`fast_exit_ws_0d_route=1205(reviewed_legacy_fast_exit_route_provenance)`
- `blocked_strength_momentum` count=`1678` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=9(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_candidate_deferred` count=`1592` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=213(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=46(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalp_entry_action_decision_snapshot` count=`1202` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=630(reviewed_rising_missed_nxt_eligibility_not_available), holding_exit_matrix_score_prior_band=459(reviewed_score_prior_neutral_unknown_not_decision_input), risk_regime_context=121(reviewed_missing_risk_regime_context), entry_order_flow_status=120(reviewed_entry_order_flow_not_available), score_prior_band=54(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=54(reviewed_score_prior_neutral_unknown_not_decision_input), tier_reason=50(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=50(reviewed_explicit_sizing_unknown_venue_fallback)`
- `ai_holding_review` count=`1120` routing=`reviewed_unknown_token_provenance` fields=`holding_context_ws_route=38(reviewed_holding_input_preflight_blocked_provenance), holding_context_selected_route_partition=38(reviewed_holding_input_preflight_blocked_provenance), holding_context_blockers=38(reviewed_holding_input_preflight_blocked_provenance), entry_order_flow_status=20(reviewed_entry_order_flow_not_available)`
- `rising_missed_tp1_candidate_blocked` count=`1031` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=632(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=15(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=15(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=15(reviewed_explicit_sizing_unknown_venue_fallback), venue=1(reviewed_rising_missed_explicit_venue_conflict), effective_venue=1(reviewed_rising_missed_explicit_venue_conflict)`
- `stat_action_decision_snapshot` count=`990` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=38(reviewed_stale_flag_not_available), quote_stale=38(reviewed_stale_flag_not_available), shallow_tick_context_stale=36(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=36(reviewed_shallow_stale_flag_not_available)`
- `rising_missed_one_share_entry` count=`741` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=651(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=7(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=7(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=7(reviewed_explicit_sizing_unknown_venue_fallback), venue=1(reviewed_rising_missed_explicit_venue_conflict), effective_venue=1(reviewed_rising_missed_explicit_venue_conflict)`
- `budget_pass` count=`608` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=508(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=36(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=36(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=36(reviewed_explicit_sizing_unknown_venue_fallback)`
- `orderbook_stability_observed` count=`608` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=508(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=36(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=36(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=36(reviewed_explicit_sizing_unknown_venue_fallback)`
- `prev_close_gainer_entry_ai_handoff` count=`571` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=333(reviewed_rising_missed_nxt_eligibility_not_available), venue=32(reviewed_observation_only_venue_not_available), rising_missed_effective_venue=11(reviewed_rising_missed_nxt_eligibility_not_available)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `64336`
- `scalping_scanner_fast_precheck`: `50994`
- `scalping_scanner_runtime_queue_lag`: `28034`
- `scalping_scanner_watching_runtime_skip`: `14457`
- `scalping_scanner_heavy_eval_completion`: `13765`
- `scalping_scanner_heavy_eval_lag`: `13342`
- `scalping_scanner_runtime_target_attach`: `12688`
- `rising_missed_nxt_post_block_price_sample`: `9714`
- `rising_missed_watch_not_rising_skipped`: `6055`
- `risky_micro_episode_executable_bbo_observed`: `5668`
- `scalping_scanner_candidate_observed`: `3721`
- `scalping_scanner_real_source_guard_block`: `3721`
- `holding_ws_freshness_blocked`: `3575`
- `scalping_scanner_candidate_promoted`: `2820`
- `rising_missed_tp1_counterfactual_submit_safety`: `2623`
- `bad_entry_refined_candidate`: `2368`
- `scalping_scanner_watch_eviction`: `2355`
- `strength_momentum_observed`: `2211`
- `scalp_fast_exit_venue_blocked`: `1794`
- `scalping_scanner_ws_backoff_watch_retained`: `1752`

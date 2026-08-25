# Observation Source Quality Audit - 2026-08-25

- status: `pass`
- event_count: `262393`
- tuning_input_policy: `exclude_defective_rows_not_full_day_raw`
- hard_blocking_excluded_row_count: `69`
- pre_exclusion_hard_blocking_excluded_row_count: `69`
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
- `scalping_scanner_promotion_latency_trace` count=`59802` routing=`reviewed_unknown_token_provenance` fields=`venue=28(reviewed_scanner_venue_fail_closed_provenance), effective_venue=28(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_fast_precheck` count=`45885` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=1022(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=387(reviewed_scanner_stale_backoff_route_not_available), venue=23(reviewed_scanner_venue_fail_closed_provenance), effective_venue=23(reviewed_scanner_venue_fail_closed_provenance), scanner_promotion_reanchor_effective_venue=23(reviewed_scanner_venue_fail_closed_provenance), scanner_stale_backoff_canonical_effective_venue=23(reviewed_scanner_venue_fail_closed_provenance), main_lifecycle_session_bucket=23(reviewed_main_lifecycle_session_not_available), main_lifecycle_venue=7(reviewed_main_lifecycle_venue_not_available)`
- `scalping_scanner_runtime_queue_lag` count=`25128` routing=`reviewed_unknown_token_provenance` fields=`venue=13(reviewed_scanner_venue_fail_closed_provenance), effective_venue=13(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_runtime_target_attach` count=`24683` routing=`reviewed_unknown_token_provenance` fields=`venue=13(reviewed_scanner_venue_fail_closed_provenance), effective_venue=13(reviewed_scanner_venue_fail_closed_provenance), market_session_bucket=13(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_heavy_eval_completion` count=`14239` routing=`reviewed_unknown_token_provenance` fields=`venue=5(reviewed_scanner_venue_fail_closed_provenance), effective_venue=5(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_heavy_eval_lag` count=`13917` routing=`reviewed_unknown_token_provenance` fields=`venue=5(reviewed_scanner_venue_fail_closed_provenance), effective_venue=5(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_watching_runtime_skip` count=`9504` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1001(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=65(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=60(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=60(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=60(reviewed_explicit_sizing_unknown_venue_fallback), venue=4(reviewed_scanner_venue_fail_closed_provenance), effective_venue=4(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_nxt_post_block_price_sample` count=`8548` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_post_block_ws_0b_route=1(reviewed_rising_missed_nxt_post_block_route_not_available), rising_missed_nxt_post_block_ws_0d_route=1(reviewed_rising_missed_nxt_post_block_route_not_available)`
- `rising_missed_watch_not_rising_skipped` count=`7169` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=5031(reviewed_rising_missed_nxt_eligibility_not_available), venue=23(reviewed_observation_only_venue_not_available), rising_missed_effective_venue=23(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`2694` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1330(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=269(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=22(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=22(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=22(reviewed_explicit_sizing_unknown_venue_fallback)`
- `strength_momentum_observed` count=`1557` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=2(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_candidate_deferred` count=`1455` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=467(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=251(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=9(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=9(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=9(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scalp_entry_action_decision_snapshot` count=`1445` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=920(reviewed_rising_missed_nxt_eligibility_not_available), holding_exit_matrix_score_prior_band=492(reviewed_score_prior_neutral_unknown_not_decision_input), entry_order_flow_status=133(reviewed_entry_order_flow_not_available), risk_regime_context=98(reviewed_missing_risk_regime_context), tier_reason=50(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=50(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=50(reviewed_explicit_sizing_unknown_venue_fallback), score_prior_band=42(reviewed_score_prior_neutral_unknown_not_decision_input)`
- `rising_missed_tp1_candidate_blocked` count=`1239` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=863(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=18(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=13(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=13(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=13(reviewed_explicit_sizing_unknown_venue_fallback)`
- `ai_holding_review` count=`1238` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=15(reviewed_entry_order_flow_not_available), holding_context_ws_route=1(reviewed_holding_input_preflight_blocked_provenance), holding_context_selected_route_partition=1(reviewed_holding_input_preflight_blocked_provenance), holding_context_blockers=1(reviewed_holding_input_preflight_blocked_provenance)`
- `blocked_strength_momentum` count=`1151` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=2(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_one_share_entry` count=`891` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=820(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=22(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=9(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=9(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=9(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scalping_scanner_ws_backoff_watch_retained` count=`814` routing=`reviewed_unknown_token_provenance` fields=`venue=1(reviewed_scanner_venue_fail_closed_provenance), effective_venue=1(reviewed_scanner_venue_fail_closed_provenance)`
- `budget_pass` count=`771` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=688(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=36(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=36(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=36(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_effective_venue=22(reviewed_rising_missed_nxt_eligibility_not_available)`
- `orderbook_stability_observed` count=`771` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=688(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=36(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=36(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=36(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_effective_venue=22(reviewed_rising_missed_nxt_eligibility_not_available)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `59802`
- `scalping_scanner_fast_precheck`: `45885`
- `scalping_scanner_runtime_queue_lag`: `25128`
- `scalping_scanner_runtime_target_attach`: `24683`
- `scalping_scanner_heavy_eval_completion`: `14239`
- `scalping_scanner_heavy_eval_lag`: `13917`
- `risky_micro_episode_executable_bbo_observed`: `9833`
- `scalping_scanner_watching_runtime_skip`: `9504`
- `rising_missed_nxt_post_block_price_sample`: `8548`
- `rising_missed_watch_not_rising_skipped`: `7169`
- `holding_ws_freshness_blocked`: `3958`
- `bad_entry_refined_candidate`: `3013`
- `rising_missed_tp1_counterfactual_submit_safety`: `2694`
- `scalping_scanner_candidate_promoted`: `2029`
- `scalping_scanner_watch_eviction`: `1634`
- `strength_momentum_observed`: `1557`
- `rising_missed_tp1_candidate_deferred`: `1455`
- `scalp_entry_action_decision_snapshot`: `1445`
- `ai_holding_fast_reuse_band`: `1271`
- `ai_holding_reuse_bypass`: `1241`

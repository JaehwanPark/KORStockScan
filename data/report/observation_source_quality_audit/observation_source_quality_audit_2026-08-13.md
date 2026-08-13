# Observation Source Quality Audit - 2026-08-13

- status: `pass`
- event_count: `293853`
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
- `scalping_scanner_promotion_latency_trace` count=`70531` routing=`reviewed_unknown_token_provenance` fields=`venue=557(reviewed_scanner_venue_fail_closed_provenance), effective_venue=557(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_fast_precheck` count=`54265` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=1421(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=466(reviewed_scanner_stale_backoff_route_not_available), venue=396(reviewed_scanner_venue_fail_closed_provenance), effective_venue=396(reviewed_scanner_venue_fail_closed_provenance), scanner_promotion_reanchor_effective_venue=396(reviewed_scanner_venue_fail_closed_provenance), scanner_stale_backoff_canonical_effective_venue=396(reviewed_scanner_venue_fail_closed_provenance), rising_missed_submit_safety_backoff_reason=1(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `scalping_scanner_runtime_queue_lag` count=`29491` routing=`reviewed_unknown_token_provenance` fields=`venue=232(reviewed_scanner_venue_fail_closed_provenance), effective_venue=232(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_heavy_eval_completion` count=`16679` routing=`reviewed_unknown_token_provenance` fields=`venue=175(reviewed_scanner_venue_fail_closed_provenance), effective_venue=175(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_heavy_eval_lag` count=`16268` routing=`reviewed_unknown_token_provenance` fields=`venue=161(reviewed_scanner_venue_fail_closed_provenance), effective_venue=161(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_watching_runtime_skip` count=`10659` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1234(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=144(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=144(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=144(reviewed_explicit_sizing_unknown_venue_fallback), effective_venue=70(reviewed_scanner_venue_fail_closed_provenance), venue=46(reviewed_scanner_venue_fail_closed_provenance), venue=24(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_nxt_post_block_price_sample` count=`9694` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_post_block_ws_0b_route=74(reviewed_rising_missed_nxt_post_block_route_not_available), rising_missed_nxt_post_block_ws_0d_route=72(reviewed_rising_missed_nxt_post_block_route_not_available)`
- `rising_missed_watch_not_rising_skipped` count=`7483` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=5039(reviewed_rising_missed_nxt_eligibility_not_available), venue=163(reviewed_observation_only_venue_not_available)`
- `strength_momentum_observed` count=`2369` routing=`reviewed_unknown_token_provenance` fields=`effective_venue=43(reviewed_scanner_venue_fail_closed_provenance), venue=40(reviewed_scanner_venue_fail_closed_provenance), rising_missed_nxt_eligible=5(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=3(reviewed_explicit_sizing_unknown_venue_fallback), venue=3(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=3(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=3(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`2163` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=663(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback)`
- `blocked_strength_momentum` count=`1829` routing=`reviewed_unknown_token_provenance` fields=`effective_venue=13(reviewed_scanner_venue_fail_closed_provenance), venue=11(reviewed_scanner_venue_fail_closed_provenance), tier_reason=2(reviewed_explicit_sizing_unknown_venue_fallback), venue=2(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=2(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=2(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_nxt_eligible=2(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_candidate_deferred` count=`1203` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=151(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalp_sim_panic_context_warning` count=`1139` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=1139(reviewed_missing_risk_regime_context), market_risk_state=1139(reviewed_missing_risk_regime_context), liquidity_state=1139(reviewed_missing_risk_regime_context), risk_regime_epoch_id=1139(reviewed_missing_risk_regime_context)`
- `scalp_fast_exit_venue_blocked` count=`1073` routing=`reviewed_unknown_token_provenance` fields=`fast_exit_ws_0d_route=906(reviewed_legacy_fast_exit_route_provenance)`
- `scalp_entry_action_decision_snapshot` count=`1068` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=512(reviewed_rising_missed_nxt_eligibility_not_available), holding_exit_matrix_score_prior_band=422(reviewed_score_prior_neutral_unknown_not_decision_input), risk_regime_context=103(reviewed_missing_risk_regime_context), entry_order_flow_status=98(reviewed_entry_order_flow_not_available), score_prior_band=31(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=31(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=30(reviewed_entry_score_source_not_available), entry_recheck_excluded_reason=30(reviewed_entry_score_source_not_available)`
- `ai_holding_review` count=`1012` routing=`reviewed_unknown_token_provenance` fields=`holding_context_ws_route=2(reviewed_holding_input_preflight_blocked_provenance), holding_context_selected_route_partition=2(reviewed_holding_input_preflight_blocked_provenance), holding_context_blockers=2(reviewed_holding_input_preflight_blocked_provenance), entry_order_flow_status=1(reviewed_entry_order_flow_not_available)`
- `stat_action_decision_snapshot` count=`982` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=14(reviewed_stale_flag_not_available), quote_stale=14(reviewed_stale_flag_not_available)`
- `rising_missed_tp1_candidate_blocked` count=`960` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=512(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_one_share_entry` count=`622` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=528(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback), venue=1(reviewed_rising_missed_explicit_venue_conflict), effective_venue=1(reviewed_rising_missed_explicit_venue_conflict)`
- `strength_momentum_stability_recheck_pending` count=`530` routing=`reviewed_unknown_token_provenance` fields=`venue=26(reviewed_scanner_venue_fail_closed_provenance), effective_venue=26(reviewed_scanner_venue_fail_closed_provenance), rising_missed_nxt_eligible=3(reviewed_rising_missed_nxt_eligibility_not_available)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `70531`
- `scalping_scanner_fast_precheck`: `54265`
- `scalping_scanner_runtime_queue_lag`: `29491`
- `scalping_scanner_runtime_target_attach`: `25484`
- `scalping_scanner_heavy_eval_completion`: `16679`
- `scalping_scanner_heavy_eval_lag`: `16268`
- `scalping_scanner_watching_runtime_skip`: `10659`
- `rising_missed_nxt_post_block_price_sample`: `9694`
- `rising_missed_watch_not_rising_skipped`: `7483`
- `scalping_scanner_candidate_observed`: `6265`
- `scalping_scanner_real_source_guard_block`: `6265`
- `holding_ws_freshness_blocked`: `3101`
- `bad_entry_refined_candidate`: `2440`
- `strength_momentum_observed`: `2369`
- `rising_missed_tp1_counterfactual_submit_safety`: `2163`
- `scalping_scanner_candidate_promoted`: `2096`
- `blocked_strength_momentum`: `1829`
- `scalping_scanner_watch_eviction`: `1583`
- `rising_missed_tp1_candidate_deferred`: `1203`
- `scalp_sim_panic_context_warning`: `1139`

# Observation Source Quality Audit - 2026-08-03

- status: `pass`
- event_count: `480717`
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
- `scalping_scanner_promotion_latency_trace` count=`87476` routing=`reviewed_unknown_token_provenance` fields=`venue=96(reviewed_scanner_venue_fail_closed_provenance), effective_venue=96(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_watch_not_rising_skipped` count=`55406` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=32855(reviewed_rising_missed_nxt_eligibility_not_available), venue=839(reviewed_observation_only_venue_not_available)`
- `scalping_scanner_fast_precheck` count=`52523` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=2878(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=641(reviewed_scanner_stale_backoff_route_not_available), venue=52(reviewed_scanner_venue_fail_closed_provenance), effective_venue=52(reviewed_scanner_venue_fail_closed_provenance), scanner_promotion_reanchor_effective_venue=52(reviewed_scanner_venue_fail_closed_provenance), scanner_stale_backoff_canonical_effective_venue=52(reviewed_scanner_venue_fail_closed_provenance), rising_missed_submit_safety_backoff_reason=4(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `scalping_scanner_heavy_eval_lag` count=`34953` routing=`reviewed_unknown_token_provenance` fields=`venue=44(reviewed_scanner_venue_fail_closed_provenance), effective_venue=44(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_runtime_queue_lag` count=`29860` routing=`reviewed_unknown_token_provenance` fields=`venue=3168(reviewed_scanner_venue_fail_closed_provenance), effective_venue=3168(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_watching_runtime_skip` count=`18587` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1410(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=929(reviewed_explicit_sizing_unknown_venue_fallback), venue=16(reviewed_scanner_venue_fail_closed_provenance), effective_venue=16(reviewed_scanner_venue_fail_closed_provenance)`
- `scalp_fast_exit_venue_blocked` count=`16869` routing=`reviewed_unknown_token_provenance` fields=`fast_exit_ws_0d_route=16575(reviewed_legacy_fast_exit_route_provenance)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`14780` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1792(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_nxt_post_block_price_sample` count=`13596` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_post_block_ws_0b_route=427(reviewed_rising_missed_nxt_post_block_route_not_available), rising_missed_nxt_post_block_ws_0d_route=369(reviewed_rising_missed_nxt_post_block_route_not_available)`
- `rising_missed_tp1_candidate_deferred` count=`11790` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=716(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalping_scanner_watch_eviction` count=`3565` routing=`reviewed_unknown_token_provenance` fields=`venue=203(reviewed_observation_only_venue_not_available), effective_venue=203(reviewed_observation_only_venue_not_available)`
- `strength_momentum_observed` count=`3507` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=10(reviewed_rising_missed_nxt_eligibility_not_available), venue=4(reviewed_scanner_venue_fail_closed_provenance), effective_venue=4(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_tp1_candidate_blocked` count=`2990` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1076(reviewed_rising_missed_nxt_eligibility_not_available)`
- `blocked_strength_momentum` count=`2745` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=9(reviewed_rising_missed_nxt_eligibility_not_available), venue=4(reviewed_scanner_venue_fail_closed_provenance), effective_venue=4(reviewed_scanner_venue_fail_closed_provenance)`
- `prev_close_gainer_entry_ai_handoff` count=`2590` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1451(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalp_entry_action_decision_snapshot` count=`1746` routing=`reviewed_unknown_token_provenance` fields=`holding_exit_matrix_score_prior_band=791(reviewed_score_prior_neutral_unknown_not_decision_input), rising_missed_nxt_eligible=708(reviewed_rising_missed_nxt_eligibility_not_available), entry_order_flow_status=211(reviewed_entry_order_flow_not_available), risk_regime_context=161(reviewed_missing_risk_regime_context), tier_reason=142(reviewed_explicit_sizing_unknown_venue_fallback), score_prior_band=114(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=114(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=104(reviewed_entry_score_source_not_available)`
- `opening_rotation_1pct_observed` count=`1400` routing=`reviewed_unknown_token_provenance` fields=`venue=4(reviewed_scanner_venue_fail_closed_provenance), effective_venue=4(reviewed_scanner_venue_fail_closed_provenance), scanner_promotion_reanchor_effective_venue=4(reviewed_scanner_venue_fail_closed_provenance), opening_rotation_no_pullback_continuation_effective_venue=4(reviewed_scanner_venue_fail_closed_provenance), rising_missed_nxt_eligible=3(reviewed_rising_missed_nxt_eligibility_not_available)`
- `opening_rotation_1pct_upstream_blocked` count=`1170` routing=`reviewed_unknown_token_provenance` fields=`venue=11(reviewed_scanner_venue_fail_closed_provenance), effective_venue=11(reviewed_scanner_venue_fail_closed_provenance), rising_missed_nxt_eligible=1(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_one_share_entry` count=`1125` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=951(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=73(reviewed_explicit_sizing_unknown_venue_fallback)`
- `budget_pass` count=`800` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=628(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=128(reviewed_explicit_sizing_unknown_venue_fallback)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `87476`
- `scalping_scanner_heavy_eval_completion`: `59697`
- `rising_missed_watch_not_rising_skipped`: `55406`
- `scalping_scanner_fast_precheck`: `52523`
- `scalping_scanner_heavy_eval_lag`: `34953`
- `scalping_scanner_runtime_queue_lag`: `29860`
- `scalping_scanner_watching_runtime_skip`: `18587`
- `scalp_fast_exit_venue_blocked`: `16869`
- `rising_missed_tp1_counterfactual_submit_safety`: `14780`
- `rising_missed_nxt_post_block_price_sample`: `13596`
- `rising_missed_tp1_candidate_deferred`: `11790`
- `scalping_scanner_runtime_target_attach`: `10877`
- `scalping_scanner_candidate_observed`: `8432`
- `scalping_scanner_real_source_guard_block`: `8432`
- `holding_ws_freshness_blocked`: `5264`
- `scalping_scanner_candidate_promoted`: `3874`
- `scalping_scanner_watch_eviction`: `3565`
- `strength_momentum_observed`: `3507`
- `rising_missed_nxt_post_block_sampler_registration_skipped`: `3014`
- `rising_missed_tp1_candidate_blocked`: `2990`

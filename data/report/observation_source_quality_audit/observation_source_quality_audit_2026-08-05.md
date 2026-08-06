# Observation Source Quality Audit - 2026-08-05

- status: `warning`
- event_count: `612745`
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
- `scalping_scanner_watch_budget_reallocated` count=`218` routing=`source_quality_blocker_or_provenance_backfill` fields=`venue=1(0.0046), effective_venue=1(0.0046)`

## Reviewed Unknown Token Findings
- `scalping_scanner_heavy_eval_completion` count=`162049` routing=`reviewed_unknown_token_provenance` fields=`venue=1069(reviewed_scanner_venue_fail_closed_provenance), effective_venue=1069(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_promotion_latency_trace` count=`110654` routing=`reviewed_unknown_token_provenance` fields=`venue=795(reviewed_scanner_venue_fail_closed_provenance), effective_venue=795(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_watch_not_rising_skipped` count=`109905` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=54209(reviewed_rising_missed_nxt_eligibility_not_available), venue=470(reviewed_observation_only_venue_not_available)`
- `scalping_scanner_fast_precheck` count=`64407` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=1806(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=538(reviewed_scanner_stale_backoff_route_not_available), venue=472(reviewed_scanner_venue_fail_closed_provenance), effective_venue=472(reviewed_scanner_venue_fail_closed_provenance), scanner_promotion_reanchor_effective_venue=472(reviewed_scanner_venue_fail_closed_provenance), scanner_stale_backoff_canonical_effective_venue=472(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_heavy_eval_lag` count=`46247` routing=`reviewed_unknown_token_provenance` fields=`venue=323(reviewed_scanner_venue_fail_closed_provenance), effective_venue=323(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_runtime_queue_lag` count=`34916` routing=`reviewed_unknown_token_provenance` fields=`venue=245(reviewed_scanner_venue_fail_closed_provenance), effective_venue=245(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_watching_runtime_skip` count=`14033` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1605(reviewed_rising_missed_nxt_eligibility_not_available), venue=155(reviewed_scanner_venue_fail_closed_provenance), effective_venue=155(reviewed_scanner_venue_fail_closed_provenance), tier_reason=14(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`5170` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=922(reviewed_rising_missed_nxt_eligibility_not_available)`
- `strength_momentum_observed` count=`4687` routing=`reviewed_unknown_token_provenance` fields=`venue=40(reviewed_scanner_venue_fail_closed_provenance), effective_venue=40(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_nxt_post_block_price_sample` count=`4623` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_post_block_ws_0b_route=2(reviewed_rising_missed_nxt_post_block_route_not_available), rising_missed_nxt_post_block_ws_0d_route=2(reviewed_rising_missed_nxt_post_block_route_not_available)`
- `rising_missed_tp1_candidate_deferred` count=`4127` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=340(reviewed_rising_missed_nxt_eligibility_not_available)`
- `blocked_strength_momentum` count=`3960` routing=`reviewed_unknown_token_provenance` fields=`venue=39(reviewed_scanner_venue_fail_closed_provenance), effective_venue=39(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_tp1_candidate_blocked` count=`1043` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=582(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalping_scanner_ws_backoff_watch_retained` count=`947` routing=`reviewed_unknown_token_provenance` fields=`venue=16(reviewed_scanner_venue_fail_closed_provenance), effective_venue=16(reviewed_scanner_venue_fail_closed_provenance)`
- `opening_rotation_1pct_observed` count=`917` routing=`reviewed_unknown_token_provenance` fields=`venue=32(reviewed_scanner_venue_fail_closed_provenance), effective_venue=32(reviewed_scanner_venue_fail_closed_provenance), scanner_promotion_reanchor_effective_venue=32(reviewed_scanner_venue_fail_closed_provenance), opening_rotation_no_pullback_continuation_effective_venue=32(reviewed_scanner_venue_fail_closed_provenance)`
- `opening_rotation_1pct_upstream_blocked` count=`831` routing=`reviewed_unknown_token_provenance` fields=`venue=90(reviewed_scanner_venue_fail_closed_provenance), effective_venue=90(reviewed_scanner_venue_fail_closed_provenance)`
- `scalp_entry_action_decision_snapshot` count=`781` routing=`reviewed_unknown_token_provenance` fields=`holding_exit_matrix_score_prior_band=715(reviewed_score_prior_neutral_unknown_not_decision_input), risk_regime_context=129(reviewed_missing_risk_regime_context), entry_order_flow_status=125(reviewed_entry_order_flow_not_available), score_prior_band=51(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=51(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=49(reviewed_entry_score_source_not_available), entry_score_excluded_reason=49(reviewed_entry_score_source_not_available), venue=21(reviewed_scanner_venue_fail_closed_provenance)`
- `strength_momentum_stability_recheck_pending` count=`684` routing=`reviewed_unknown_token_provenance` fields=`venue=1(reviewed_scanner_venue_fail_closed_provenance), effective_venue=1(reviewed_scanner_venue_fail_closed_provenance)`
- `prev_close_gainer_entry_ai_handoff` count=`574` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=347(reviewed_rising_missed_nxt_eligibility_not_available), venue=12(reviewed_observation_only_venue_not_available)`
- `ai_confirmed` count=`526` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=79(reviewed_entry_order_flow_not_available), venue=13(reviewed_scanner_venue_fail_closed_provenance), effective_venue=13(reviewed_scanner_venue_fail_closed_provenance)`

## Top Stages
- `scalping_scanner_heavy_eval_completion`: `162049`
- `scalping_scanner_promotion_latency_trace`: `110654`
- `rising_missed_watch_not_rising_skipped`: `109905`
- `scalping_scanner_fast_precheck`: `64407`
- `scalping_scanner_heavy_eval_lag`: `46247`
- `scalping_scanner_runtime_queue_lag`: `34916`
- `scalping_scanner_watching_runtime_skip`: `14033`
- `scalping_scanner_runtime_target_attach`: `13937`
- `scalping_scanner_candidate_observed`: `7641`
- `scalping_scanner_real_source_guard_block`: `7641`
- `rising_missed_tp1_counterfactual_submit_safety`: `5170`
- `strength_momentum_observed`: `4687`
- `rising_missed_nxt_post_block_price_sample`: `4623`
- `rising_missed_tp1_candidate_deferred`: `4127`
- `blocked_strength_momentum`: `3960`
- `scalping_scanner_candidate_promoted`: `2594`
- `scalping_scanner_watch_eviction`: `2165`
- `rising_missed_tp1_candidate_blocked`: `1043`
- `scalping_scanner_ws_backoff_watch_retained`: `947`
- `opening_rotation_1pct_observed`: `917`

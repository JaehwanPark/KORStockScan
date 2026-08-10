# Observation Source Quality Audit - 2026-08-10

- status: `pass`
- event_count: `327383`
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
- `scalping_scanner_promotion_latency_trace` count=`93139` routing=`reviewed_unknown_token_provenance` fields=`venue=213(reviewed_scanner_venue_fail_closed_provenance), effective_venue=213(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_fast_precheck` count=`71004` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=1587(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=350(reviewed_scanner_stale_backoff_route_not_available), venue=157(reviewed_scanner_venue_fail_closed_provenance), effective_venue=157(reviewed_scanner_venue_fail_closed_provenance), scanner_promotion_reanchor_effective_venue=157(reviewed_scanner_venue_fail_closed_provenance), scanner_stale_backoff_canonical_effective_venue=157(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_runtime_queue_lag` count=`38248` routing=`reviewed_unknown_token_provenance` fields=`venue=96(reviewed_scanner_venue_fail_closed_provenance), effective_venue=96(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_heavy_eval_completion` count=`22671` routing=`reviewed_unknown_token_provenance` fields=`venue=56(reviewed_scanner_venue_fail_closed_provenance), effective_venue=56(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_heavy_eval_lag` count=`22135` routing=`reviewed_unknown_token_provenance` fields=`venue=56(reviewed_scanner_venue_fail_closed_provenance), effective_venue=56(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_watching_runtime_skip` count=`12370` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1989(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=230(reviewed_explicit_sizing_unknown_venue_fallback), venue=16(reviewed_scanner_venue_fail_closed_provenance), effective_venue=16(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_watch_not_rising_skipped` count=`9021` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=4635(reviewed_rising_missed_nxt_eligibility_not_available), venue=456(reviewed_observation_only_venue_not_available)`
- `rising_missed_nxt_post_block_price_sample` count=`6739` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_post_block_ws_0b_route=1(reviewed_rising_missed_nxt_post_block_route_not_available), rising_missed_nxt_post_block_ws_0d_route=1(reviewed_rising_missed_nxt_post_block_route_not_available)`
- `strength_momentum_observed` count=`3063` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=5(reviewed_rising_missed_nxt_eligibility_not_available), venue=1(reviewed_scanner_venue_fail_closed_provenance), effective_venue=1(reviewed_scanner_venue_fail_closed_provenance)`
- `blocked_strength_momentum` count=`2421` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1(reviewed_rising_missed_nxt_eligibility_not_available), venue=1(reviewed_scanner_venue_fail_closed_provenance), effective_venue=1(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`1378` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=538(reviewed_rising_missed_nxt_eligibility_not_available), effective_venue=5(reviewed_rising_missed_explicit_venue_conflict), tier_reason=4(reviewed_explicit_sizing_unknown_venue_fallback), venue=4(reviewed_explicit_sizing_unknown_venue_fallback), venue=1(reviewed_rising_missed_explicit_venue_conflict)`
- `blocked_overbought` count=`1131` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=5(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_candidate_deferred` count=`814` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=141(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalping_scanner_ws_backoff_watch_retained` count=`798` routing=`reviewed_unknown_token_provenance` fields=`venue=6(reviewed_scanner_venue_fail_closed_provenance), effective_venue=6(reviewed_scanner_venue_fail_closed_provenance)`
- `scalp_entry_action_decision_snapshot` count=`724` routing=`reviewed_unknown_token_provenance` fields=`holding_exit_matrix_score_prior_band=561(reviewed_score_prior_neutral_unknown_not_decision_input), risk_regime_context=84(reviewed_missing_risk_regime_context), score_prior_band=80(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=80(reviewed_score_prior_neutral_unknown_not_decision_input), rising_missed_nxt_eligible=80(reviewed_rising_missed_nxt_eligibility_not_available), entry_order_flow_status=74(reviewed_entry_order_flow_not_available), entry_score_source=72(reviewed_entry_score_source_not_available), entry_recheck_excluded_reason=72(reviewed_entry_score_source_not_available)`
- `strength_momentum_stability_recheck_pending` count=`612` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=4(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_candidate_blocked` count=`564` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=397(reviewed_rising_missed_nxt_eligibility_not_available), effective_venue=5(reviewed_rising_missed_explicit_venue_conflict), tier_reason=4(reviewed_explicit_sizing_unknown_venue_fallback), venue=4(reviewed_explicit_sizing_unknown_venue_fallback), venue=1(reviewed_rising_missed_explicit_venue_conflict)`
- `prev_close_gainer_entry_ai_handoff` count=`562` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=314(reviewed_rising_missed_nxt_eligibility_not_available), venue=18(reviewed_observation_only_venue_not_available)`
- `stat_action_decision_snapshot` count=`549` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=13(reviewed_stale_flag_not_available), quote_stale=13(reviewed_stale_flag_not_available)`
- `ai_confirmed` count=`494` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=34(reviewed_entry_order_flow_not_available), rising_missed_nxt_eligible=8(reviewed_rising_missed_nxt_eligibility_not_available), venue=1(reviewed_scanner_venue_fail_closed_provenance), effective_venue=1(reviewed_scanner_venue_fail_closed_provenance)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `93139`
- `scalping_scanner_fast_precheck`: `71004`
- `scalping_scanner_runtime_queue_lag`: `38248`
- `scalping_scanner_heavy_eval_completion`: `22671`
- `scalping_scanner_heavy_eval_lag`: `22135`
- `scalping_scanner_runtime_target_attach`: `16004`
- `scalping_scanner_watching_runtime_skip`: `12370`
- `rising_missed_watch_not_rising_skipped`: `9021`
- `rising_missed_nxt_post_block_price_sample`: `6739`
- `scalping_scanner_candidate_observed`: `3501`
- `scalping_scanner_real_source_guard_block`: `3501`
- `strength_momentum_observed`: `3063`
- `blocked_strength_momentum`: `2421`
- `scalping_scanner_candidate_promoted`: `1942`
- `scalping_scanner_watch_eviction`: `1510`
- `rising_missed_tp1_counterfactual_submit_safety`: `1378`
- `blocked_overbought`: `1131`
- `scalp_sim_scale_in_candidate_funnel`: `1094`
- `bad_entry_refined_candidate`: `978`
- `rising_missed_tp1_candidate_deferred`: `814`

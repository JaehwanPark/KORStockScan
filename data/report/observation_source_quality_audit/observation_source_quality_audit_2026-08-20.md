# Observation Source Quality Audit - 2026-08-20

- status: `pass`
- event_count: `270207`
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
- `scalping_scanner_promotion_latency_trace` count=`66411` routing=`reviewed_unknown_token_provenance` fields=`venue=31(reviewed_scanner_venue_fail_closed_provenance), effective_venue=31(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_fast_precheck` count=`51354` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=1271(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=522(reviewed_scanner_stale_backoff_route_not_available), venue=27(reviewed_scanner_venue_fail_closed_provenance), effective_venue=27(reviewed_scanner_venue_fail_closed_provenance), scanner_promotion_reanchor_effective_venue=27(reviewed_scanner_venue_fail_closed_provenance), scanner_stale_backoff_canonical_effective_venue=27(reviewed_scanner_venue_fail_closed_provenance), rising_missed_submit_safety_backoff_reason=2(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `scalping_scanner_runtime_queue_lag` count=`27755` routing=`reviewed_unknown_token_provenance` fields=`venue=21(reviewed_scanner_venue_fail_closed_provenance), effective_venue=21(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_heavy_eval_completion` count=`15474` routing=`reviewed_unknown_token_provenance` fields=`venue=4(reviewed_scanner_venue_fail_closed_provenance), effective_venue=4(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_heavy_eval_lag` count=`15057` routing=`reviewed_unknown_token_provenance` fields=`venue=4(reviewed_scanner_venue_fail_closed_provenance), effective_venue=4(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_watching_runtime_skip` count=`11286` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=907(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=104(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=104(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=104(reviewed_explicit_sizing_unknown_venue_fallback), minute_candle_context_quality=2(reviewed_runtime_skip_context_not_evaluated), tick_context_quality=2(reviewed_runtime_skip_context_not_evaluated), tick_context_stale=2(reviewed_stale_flag_not_available)`
- `rising_missed_watch_not_rising_skipped` count=`6708` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=4328(reviewed_rising_missed_nxt_eligibility_not_available), venue=30(reviewed_observation_only_venue_not_available)`
- `strength_momentum_observed` count=`2290` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=37(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`2184` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=946(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback), venue=1(reviewed_rising_missed_explicit_venue_conflict), effective_venue=1(reviewed_rising_missed_explicit_venue_conflict)`
- `blocked_strength_momentum` count=`1778` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=36(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalp_sim_scale_in_candidate_funnel` count=`1657` routing=`reviewed_unknown_token_provenance` fields=`prior_probe_residual_direction_state=21(reviewed_prior_probe_residual_source_gap), prior_probe_residual_failure_signature=21(reviewed_prior_probe_residual_source_gap)`
- `scalp_entry_action_decision_snapshot` count=`1315` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=703(reviewed_rising_missed_nxt_eligibility_not_available), holding_exit_matrix_score_prior_band=558(reviewed_score_prior_neutral_unknown_not_decision_input), risk_regime_context=137(reviewed_missing_risk_regime_context), entry_order_flow_status=101(reviewed_entry_order_flow_not_available), score_prior_band=25(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=25(reviewed_score_prior_neutral_unknown_not_decision_input), tier_reason=19(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=19(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_tp1_candidate_deferred` count=`1163` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=171(reviewed_rising_missed_nxt_eligibility_not_available), venue=1(reviewed_rising_missed_explicit_venue_conflict), effective_venue=1(reviewed_rising_missed_explicit_venue_conflict)`
- `stat_action_decision_snapshot` count=`1086` routing=`reviewed_unknown_token_provenance` fields=`prior_probe_residual_direction_state=282(reviewed_prior_probe_residual_source_gap), prior_probe_residual_failure_signature=282(reviewed_prior_probe_residual_source_gap), tick_context_stale=13(reviewed_stale_flag_not_available), quote_stale=13(reviewed_stale_flag_not_available), prior_probe_residual_orderbook_state=1(reviewed_prior_probe_residual_source_gap)`
- `ai_holding_review` count=`1028` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=4(reviewed_entry_order_flow_not_available)`
- `rising_missed_tp1_candidate_blocked` count=`1021` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=775(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback)`
- `reversal_add_blocked_reason` count=`944` routing=`reviewed_unknown_token_provenance` fields=`prior_probe_residual_direction_state=246(reviewed_prior_probe_residual_source_gap), prior_probe_residual_failure_signature=246(reviewed_prior_probe_residual_source_gap)`
- `scalping_scanner_ws_backoff_watch_retained` count=`923` routing=`reviewed_unknown_token_provenance` fields=`venue=3(reviewed_scanner_venue_fail_closed_provenance), effective_venue=3(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_one_share_entry` count=`734` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=654(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=4(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=4(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=4(reviewed_explicit_sizing_unknown_venue_fallback), venue=2(reviewed_rising_missed_explicit_venue_conflict), effective_venue=2(reviewed_rising_missed_explicit_venue_conflict)`
- `scale_in_feature_context_refresh` count=`686` routing=`reviewed_unknown_token_provenance` fields=`prior_probe_residual_direction_state=293(reviewed_prior_probe_residual_source_gap), prior_probe_residual_failure_signature=293(reviewed_prior_probe_residual_source_gap)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `66411`
- `scalping_scanner_fast_precheck`: `51354`
- `scalping_scanner_runtime_queue_lag`: `27755`
- `scalping_scanner_runtime_target_attach`: `25845`
- `scalping_scanner_heavy_eval_completion`: `15474`
- `scalping_scanner_heavy_eval_lag`: `15057`
- `scalping_scanner_watching_runtime_skip`: `11286`
- `rising_missed_watch_not_rising_skipped`: `6708`
- `rising_missed_nxt_post_block_price_sample`: `5789`
- `bad_entry_refined_candidate`: `3021`
- `scalping_scanner_candidate_observed`: `2587`
- `scalping_scanner_real_source_guard_block`: `2587`
- `strength_momentum_observed`: `2290`
- `rising_missed_tp1_counterfactual_submit_safety`: `2184`
- `scalping_scanner_candidate_promoted`: `2146`
- `blocked_strength_momentum`: `1778`
- `scalping_scanner_watch_eviction`: `1762`
- `scalp_sim_scale_in_candidate_funnel`: `1657`
- `risky_micro_episode_executable_bbo_observed`: `1477`
- `scalp_entry_action_decision_snapshot`: `1315`

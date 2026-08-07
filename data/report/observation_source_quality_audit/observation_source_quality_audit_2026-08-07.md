# Observation Source Quality Audit - 2026-08-07

- status: `pass`
- event_count: `471544`
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
- `scalping_scanner_promotion_latency_trace` count=`102693` routing=`reviewed_unknown_token_provenance` fields=`venue=742(reviewed_scanner_venue_fail_closed_provenance), effective_venue=742(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_heavy_eval_completion` count=`90959` routing=`reviewed_unknown_token_provenance` fields=`venue=958(reviewed_scanner_venue_fail_closed_provenance), effective_venue=958(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_fast_precheck` count=`67802` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=2363(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=499(reviewed_scanner_stale_backoff_route_not_available), venue=390(reviewed_scanner_venue_fail_closed_provenance), effective_venue=390(reviewed_scanner_venue_fail_closed_provenance), scanner_promotion_reanchor_effective_venue=390(reviewed_scanner_venue_fail_closed_provenance), scanner_stale_backoff_canonical_effective_venue=390(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_watch_not_rising_skipped` count=`47177` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=45250(reviewed_rising_missed_nxt_eligibility_not_available), venue=204(reviewed_observation_only_venue_not_available)`
- `scalping_scanner_runtime_queue_lag` count=`36746` routing=`reviewed_unknown_token_provenance` fields=`venue=236(reviewed_scanner_venue_fail_closed_provenance), effective_venue=236(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_heavy_eval_lag` count=`34891` routing=`reviewed_unknown_token_provenance` fields=`venue=352(reviewed_scanner_venue_fail_closed_provenance), effective_venue=352(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_watching_runtime_skip` count=`14226` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1551(reviewed_rising_missed_nxt_eligibility_not_available), venue=98(reviewed_scanner_venue_fail_closed_provenance), effective_venue=98(reviewed_scanner_venue_fail_closed_provenance), tier_reason=82(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`4164` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1120(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=16(reviewed_explicit_sizing_unknown_venue_fallback)`
- `strength_momentum_observed` count=`2958` routing=`reviewed_unknown_token_provenance` fields=`venue=39(reviewed_scanner_venue_fail_closed_provenance), effective_venue=39(reviewed_scanner_venue_fail_closed_provenance), rising_missed_nxt_eligible=14(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_candidate_deferred` count=`2666` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=431(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=5(reviewed_explicit_sizing_unknown_venue_fallback)`
- `blocked_strength_momentum` count=`2255` routing=`reviewed_unknown_token_provenance` fields=`venue=33(reviewed_scanner_venue_fail_closed_provenance), effective_venue=33(reviewed_scanner_venue_fail_closed_provenance), rising_missed_nxt_eligible=13(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_candidate_blocked` count=`1498` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=689(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=11(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scalping_scanner_ws_backoff_watch_retained` count=`1016` routing=`reviewed_unknown_token_provenance` fields=`venue=6(reviewed_scanner_venue_fail_closed_provenance), effective_venue=6(reviewed_scanner_venue_fail_closed_provenance)`
- `opening_rotation_1pct_observed` count=`934` routing=`reviewed_unknown_token_provenance` fields=`venue=43(reviewed_scanner_venue_fail_closed_provenance), effective_venue=43(reviewed_scanner_venue_fail_closed_provenance), scanner_promotion_reanchor_effective_venue=43(reviewed_scanner_venue_fail_closed_provenance), opening_rotation_no_pullback_continuation_effective_venue=43(reviewed_scanner_venue_fail_closed_provenance), rising_missed_nxt_eligible=8(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalp_entry_action_decision_snapshot` count=`815` routing=`reviewed_unknown_token_provenance` fields=`holding_exit_matrix_score_prior_band=573(reviewed_score_prior_neutral_unknown_not_decision_input), rising_missed_nxt_eligible=228(reviewed_rising_missed_nxt_eligibility_not_available), entry_order_flow_status=87(reviewed_entry_order_flow_not_available), risk_regime_context=56(reviewed_missing_risk_regime_context), score_prior_band=25(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=25(reviewed_score_prior_neutral_unknown_not_decision_input), venue=24(reviewed_scanner_venue_fail_closed_provenance), effective_venue=24(reviewed_scanner_venue_fail_closed_provenance)`
- `opening_rotation_1pct_upstream_blocked` count=`723` routing=`reviewed_unknown_token_provenance` fields=`venue=41(reviewed_scanner_venue_fail_closed_provenance), effective_venue=41(reviewed_scanner_venue_fail_closed_provenance), rising_missed_nxt_eligible=2(reviewed_rising_missed_nxt_eligibility_not_available)`
- `strength_momentum_stability_recheck_pending` count=`630` routing=`reviewed_unknown_token_provenance` fields=`venue=6(reviewed_scanner_venue_fail_closed_provenance), effective_venue=6(reviewed_scanner_venue_fail_closed_provenance), rising_missed_nxt_eligible=1(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_one_share_entry` count=`609` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=530(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=3(reviewed_explicit_sizing_unknown_venue_fallback)`
- `blocked_ai_score` count=`507` routing=`reviewed_unknown_token_provenance` fields=`score_prior_band=67(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=67(reviewed_score_prior_neutral_unknown_not_decision_input), entry_order_flow_status=40(reviewed_entry_order_flow_not_available), entry_score_source=21(reviewed_entry_score_source_not_available), entry_score_excluded_reason=21(reviewed_entry_score_source_not_available), venue=15(reviewed_scanner_venue_fail_closed_provenance), effective_venue=15(reviewed_scanner_venue_fail_closed_provenance), entry_recheck_excluded_reason=11(reviewed_entry_score_source_not_available)`
- `opening_rotation_entry_owner_handoff` count=`502` routing=`reviewed_unknown_token_provenance` fields=`venue=26(reviewed_scanner_venue_fail_closed_provenance), effective_venue=26(reviewed_scanner_venue_fail_closed_provenance), rising_missed_nxt_eligible=5(reviewed_rising_missed_nxt_eligibility_not_available)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `102693`
- `scalping_scanner_heavy_eval_completion`: `90959`
- `scalping_scanner_fast_precheck`: `67802`
- `rising_missed_watch_not_rising_skipped`: `47177`
- `scalping_scanner_runtime_queue_lag`: `36746`
- `scalping_scanner_heavy_eval_lag`: `34891`
- `rising_missed_nxt_post_block_price_sample`: `15267`
- `scalping_scanner_watching_runtime_skip`: `14226`
- `scalping_scanner_runtime_target_attach`: `14041`
- `scalping_scanner_candidate_observed`: `7164`
- `scalping_scanner_real_source_guard_block`: `7164`
- `rising_missed_tp1_counterfactual_submit_safety`: `4164`
- `strength_momentum_observed`: `2958`
- `rising_missed_tp1_candidate_deferred`: `2666`
- `scalping_scanner_candidate_promoted`: `2553`
- `blocked_strength_momentum`: `2255`
- `scalping_scanner_watch_eviction`: `2122`
- `rising_missed_tp1_candidate_blocked`: `1498`
- `manual_control_fast_exit_monitor_blocked`: `1055`
- `scalping_scanner_ws_backoff_watch_retained`: `1016`

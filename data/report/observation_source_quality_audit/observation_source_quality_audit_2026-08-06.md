# Observation Source Quality Audit - 2026-08-06

- status: `pass`
- event_count: `538755`
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
- `scalping_scanner_heavy_eval_completion` count=`126347` routing=`reviewed_unknown_token_provenance` fields=`venue=2039(reviewed_scanner_venue_fail_closed_provenance), effective_venue=2039(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_promotion_latency_trace` count=`97255` routing=`reviewed_unknown_token_provenance` fields=`venue=1461(reviewed_scanner_venue_fail_closed_provenance), effective_venue=1461(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_watch_not_rising_skipped` count=`74578` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=52558(reviewed_rising_missed_nxt_eligibility_not_available), venue=2776(reviewed_observation_only_venue_not_available)`
- `scalping_scanner_fast_precheck` count=`58623` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=2005(reviewed_scanner_stale_backoff_route_not_available), venue=773(reviewed_scanner_venue_fail_closed_provenance), effective_venue=773(reviewed_scanner_venue_fail_closed_provenance), scanner_promotion_reanchor_effective_venue=773(reviewed_scanner_venue_fail_closed_provenance), scanner_stale_backoff_canonical_effective_venue=773(reviewed_scanner_venue_fail_closed_provenance), scanner_stale_backoff_raw_0d_route=488(reviewed_scanner_stale_backoff_route_not_available), rising_missed_submit_safety_backoff_reason=2(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `scalping_scanner_heavy_eval_lag` count=`38632` routing=`reviewed_unknown_token_provenance` fields=`venue=688(reviewed_scanner_venue_fail_closed_provenance), effective_venue=688(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_runtime_queue_lag` count=`32188` routing=`reviewed_unknown_token_provenance` fields=`venue=428(reviewed_scanner_venue_fail_closed_provenance), effective_venue=428(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_watching_runtime_skip` count=`15681` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1206(reviewed_rising_missed_nxt_eligibility_not_available), venue=165(reviewed_scanner_venue_fail_closed_provenance), effective_venue=165(reviewed_scanner_venue_fail_closed_provenance), tier_reason=118(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`12164` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1781(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=13(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_nxt_post_block_price_sample` count=`10546` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_post_block_ws_0b_route=193(reviewed_rising_missed_nxt_post_block_route_not_available), rising_missed_nxt_post_block_ws_0d_route=181(reviewed_rising_missed_nxt_post_block_route_not_available)`
- `rising_missed_tp1_candidate_deferred` count=`8685` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=628(reviewed_rising_missed_nxt_eligibility_not_available)`
- `strength_momentum_observed` count=`4496` routing=`reviewed_unknown_token_provenance` fields=`venue=26(reviewed_scanner_venue_fail_closed_provenance), effective_venue=26(reviewed_scanner_venue_fail_closed_provenance), rising_missed_nxt_eligible=25(reviewed_rising_missed_nxt_eligibility_not_available)`
- `blocked_strength_momentum` count=`3729` routing=`reviewed_unknown_token_provenance` fields=`venue=25(reviewed_scanner_venue_fail_closed_provenance), effective_venue=25(reviewed_scanner_venue_fail_closed_provenance), rising_missed_nxt_eligible=22(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_candidate_blocked` count=`3479` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1153(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=13(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scalping_scanner_watch_eviction` count=`2624` routing=`reviewed_unknown_token_provenance` fields=`venue=1(reviewed_observation_only_venue_not_available), effective_venue=1(reviewed_observation_only_venue_not_available)`
- `scalp_entry_action_decision_snapshot` count=`1893` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1041(reviewed_rising_missed_nxt_eligibility_not_available), holding_exit_matrix_score_prior_band=884(reviewed_score_prior_neutral_unknown_not_decision_input), entry_order_flow_status=199(reviewed_entry_order_flow_not_available), risk_regime_context=122(reviewed_missing_risk_regime_context), score_prior_band=41(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=41(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=37(reviewed_entry_score_source_not_available), entry_score_excluded_reason=37(reviewed_entry_score_source_not_available)`
- `scalping_scanner_ws_backoff_watch_retained` count=`1325` routing=`reviewed_unknown_token_provenance` fields=`venue=8(reviewed_scanner_venue_fail_closed_provenance), effective_venue=8(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_one_share_entry` count=`1107` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1055(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=4(reviewed_explicit_sizing_unknown_venue_fallback)`
- `opening_rotation_1pct_observed` count=`996` routing=`reviewed_unknown_token_provenance` fields=`venue=47(reviewed_scanner_venue_fail_closed_provenance), effective_venue=47(reviewed_scanner_venue_fail_closed_provenance), scanner_promotion_reanchor_effective_venue=47(reviewed_scanner_venue_fail_closed_provenance), opening_rotation_no_pullback_continuation_effective_venue=47(reviewed_scanner_venue_fail_closed_provenance), rising_missed_nxt_eligible=5(reviewed_rising_missed_nxt_eligibility_not_available)`
- `budget_pass` count=`910` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=893(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=8(reviewed_explicit_sizing_unknown_venue_fallback)`
- `orderbook_stability_observed` count=`910` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=893(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=8(reviewed_explicit_sizing_unknown_venue_fallback)`

## Top Stages
- `scalping_scanner_heavy_eval_completion`: `126347`
- `scalping_scanner_promotion_latency_trace`: `97255`
- `rising_missed_watch_not_rising_skipped`: `74578`
- `scalping_scanner_fast_precheck`: `58623`
- `scalping_scanner_heavy_eval_lag`: `38632`
- `scalping_scanner_runtime_queue_lag`: `32188`
- `scalping_scanner_watching_runtime_skip`: `15681`
- `scalping_scanner_runtime_target_attach`: `13528`
- `rising_missed_tp1_counterfactual_submit_safety`: `12164`
- `rising_missed_nxt_post_block_price_sample`: `10546`
- `rising_missed_tp1_candidate_deferred`: `8685`
- `scalping_scanner_candidate_observed`: `6591`
- `scalping_scanner_real_source_guard_block`: `6591`
- `strength_momentum_observed`: `4496`
- `blocked_strength_momentum`: `3729`
- `rising_missed_tp1_candidate_blocked`: `3479`
- `scalping_scanner_candidate_promoted`: `2967`
- `scalping_scanner_watch_eviction`: `2624`
- `scalp_entry_action_decision_snapshot`: `1893`
- `scalping_scanner_ws_backoff_watch_retained`: `1325`

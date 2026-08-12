# Observation Source Quality Audit - 2026-08-12

- status: `pass`
- event_count: `322263`
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
- `scalping_scanner_promotion_latency_trace` count=`87256` routing=`reviewed_unknown_token_provenance` fields=`venue=1254(reviewed_scanner_venue_fail_closed_provenance), effective_venue=1254(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_fast_precheck` count=`66718` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=1323(reviewed_scanner_stale_backoff_route_not_available), venue=910(reviewed_scanner_venue_fail_closed_provenance), effective_venue=910(reviewed_scanner_venue_fail_closed_provenance), scanner_promotion_reanchor_effective_venue=910(reviewed_scanner_venue_fail_closed_provenance), scanner_stale_backoff_canonical_effective_venue=910(reviewed_scanner_venue_fail_closed_provenance), scanner_stale_backoff_raw_0d_route=313(reviewed_scanner_stale_backoff_route_not_available), rising_missed_submit_safety_backoff_reason=9(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `scalping_scanner_runtime_queue_lag` count=`35581` routing=`reviewed_unknown_token_provenance` fields=`venue=504(reviewed_scanner_venue_fail_closed_provenance), effective_venue=504(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_heavy_eval_completion` count=`21023` routing=`reviewed_unknown_token_provenance` fields=`venue=348(reviewed_scanner_venue_fail_closed_provenance), effective_venue=348(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_heavy_eval_lag` count=`20538` routing=`reviewed_unknown_token_provenance` fields=`venue=344(reviewed_scanner_venue_fail_closed_provenance), effective_venue=344(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_watch_not_rising_skipped` count=`10876` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=6637(reviewed_rising_missed_nxt_eligibility_not_available), venue=18(reviewed_observation_only_venue_not_available)`
- `scalping_scanner_watching_runtime_skip` count=`10779` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1295(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=222(reviewed_explicit_sizing_unknown_venue_fallback), venue=151(reviewed_scanner_venue_fail_closed_provenance), effective_venue=151(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_nxt_post_block_price_sample` count=`9669` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_post_block_ws_0b_route=528(reviewed_rising_missed_nxt_post_block_route_not_available), rising_missed_nxt_post_block_ws_0d_route=496(reviewed_rising_missed_nxt_post_block_route_not_available)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`2636` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=972(reviewed_rising_missed_nxt_eligibility_not_available), venue=1(reviewed_rising_missed_explicit_venue_conflict), effective_venue=1(reviewed_rising_missed_explicit_venue_conflict)`
- `strength_momentum_observed` count=`2396` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=16(reviewed_rising_missed_nxt_eligibility_not_available), venue=13(reviewed_scanner_venue_fail_closed_provenance), effective_venue=13(reviewed_scanner_venue_fail_closed_provenance)`
- `blocked_strength_momentum` count=`1842` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=14(reviewed_rising_missed_nxt_eligibility_not_available), venue=9(reviewed_scanner_venue_fail_closed_provenance), effective_venue=9(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_tp1_candidate_deferred` count=`1712` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=270(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalp_entry_action_decision_snapshot` count=`1201` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=589(reviewed_rising_missed_nxt_eligibility_not_available), holding_exit_matrix_score_prior_band=553(reviewed_score_prior_neutral_unknown_not_decision_input), risk_regime_context=124(reviewed_missing_risk_regime_context), entry_order_flow_status=104(reviewed_entry_order_flow_not_available), score_prior_band=34(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=34(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=32(reviewed_entry_score_source_not_available), entry_recheck_excluded_reason=32(reviewed_entry_score_source_not_available)`
- `rising_missed_tp1_candidate_blocked` count=`924` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=702(reviewed_rising_missed_nxt_eligibility_not_available), venue=1(reviewed_rising_missed_explicit_venue_conflict), effective_venue=1(reviewed_rising_missed_explicit_venue_conflict)`
- `rising_missed_one_share_entry` count=`720` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=601(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=4(reviewed_explicit_sizing_unknown_venue_fallback), effective_venue=2(reviewed_rising_missed_explicit_venue_conflict), venue=1(reviewed_rising_missed_explicit_venue_conflict), venue=1(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scalping_scanner_ws_backoff_watch_retained` count=`694` routing=`reviewed_unknown_token_provenance` fields=`venue=5(reviewed_scanner_venue_fail_closed_provenance), effective_venue=5(reviewed_scanner_venue_fail_closed_provenance)`
- `budget_pass` count=`591` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=469(reviewed_rising_missed_nxt_eligibility_not_available)`
- `orderbook_stability_observed` count=`591` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=469(reviewed_rising_missed_nxt_eligibility_not_available)`
- `prev_close_gainer_entry_ai_handoff` count=`532` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=306(reviewed_rising_missed_nxt_eligibility_not_available), venue=23(reviewed_observation_only_venue_not_available)`
- `strength_momentum_stability_recheck_pending` count=`531` routing=`reviewed_unknown_token_provenance` fields=`venue=4(reviewed_scanner_venue_fail_closed_provenance), effective_venue=4(reviewed_scanner_venue_fail_closed_provenance), rising_missed_nxt_eligible=2(reviewed_rising_missed_nxt_eligibility_not_available)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `87256`
- `scalping_scanner_fast_precheck`: `66718`
- `scalping_scanner_runtime_queue_lag`: `35581`
- `scalping_scanner_runtime_target_attach`: `21378`
- `scalping_scanner_heavy_eval_completion`: `21023`
- `scalping_scanner_heavy_eval_lag`: `20538`
- `rising_missed_watch_not_rising_skipped`: `10876`
- `scalping_scanner_watching_runtime_skip`: `10779`
- `rising_missed_nxt_post_block_price_sample`: `9669`
- `scalping_scanner_candidate_observed`: `4576`
- `scalping_scanner_real_source_guard_block`: `4576`
- `rising_missed_tp1_counterfactual_submit_safety`: `2636`
- `strength_momentum_observed`: `2396`
- `scalping_scanner_candidate_promoted`: `1958`
- `blocked_strength_momentum`: `1842`
- `rising_missed_tp1_candidate_deferred`: `1712`
- `scalping_scanner_watch_eviction`: `1470`
- `scalp_entry_action_decision_snapshot`: `1201`
- `rising_missed_tp1_candidate_blocked`: `924`
- `scalp_sim_scale_in_candidate_funnel`: `770`

# Observation Source Quality Audit - 2026-08-19

- status: `pass`
- event_count: `256453`
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
- `scalping_scanner_fast_precheck` count=`46908` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=1133(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=348(reviewed_scanner_stale_backoff_route_not_available)`
- `scalping_scanner_watching_runtime_skip` count=`10433` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=935(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=66(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=66(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=66(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`5191` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1392(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=12(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=12(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=12(reviewed_explicit_sizing_unknown_venue_fallback), venue=1(reviewed_rising_missed_explicit_venue_conflict), effective_venue=1(reviewed_rising_missed_explicit_venue_conflict)`
- `rising_missed_watch_not_rising_skipped` count=`4187` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=2927(reviewed_rising_missed_nxt_eligibility_not_available), venue=204(reviewed_observation_only_venue_not_available)`
- `rising_missed_tp1_candidate_deferred` count=`3223` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=192(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=2(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=2(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=2(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_tp1_candidate_blocked` count=`1968` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1200(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=10(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=10(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=10(reviewed_explicit_sizing_unknown_venue_fallback), venue=1(reviewed_rising_missed_explicit_venue_conflict), effective_venue=1(reviewed_rising_missed_explicit_venue_conflict)`
- `strength_momentum_observed` count=`1873` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1(reviewed_rising_missed_nxt_eligibility_not_available)`
- `blocked_strength_momentum` count=`1326` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalp_entry_action_decision_snapshot` count=`929` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=576(reviewed_rising_missed_nxt_eligibility_not_available), holding_exit_matrix_score_prior_band=361(reviewed_score_prior_neutral_unknown_not_decision_input), risk_regime_context=91(reviewed_missing_risk_regime_context), entry_order_flow_status=83(reviewed_entry_order_flow_not_available), tier_reason=50(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=50(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=50(reviewed_explicit_sizing_unknown_venue_fallback), score_prior_band=7(reviewed_score_prior_neutral_unknown_not_decision_input)`
- `rising_missed_one_share_entry` count=`578` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=525(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=6(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=6(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=6(reviewed_explicit_sizing_unknown_venue_fallback), venue=1(reviewed_rising_missed_explicit_venue_conflict), effective_venue=1(reviewed_rising_missed_explicit_venue_conflict)`
- `prev_close_gainer_entry_ai_handoff` count=`546` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=338(reviewed_rising_missed_nxt_eligibility_not_available), venue=24(reviewed_observation_only_venue_not_available)`
- `ai_holding_review` count=`492` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=11(reviewed_entry_order_flow_not_available)`
- `budget_pass` count=`479` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=431(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=41(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=41(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=41(reviewed_explicit_sizing_unknown_venue_fallback)`
- `orderbook_stability_observed` count=`479` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=431(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=41(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=41(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=41(reviewed_explicit_sizing_unknown_venue_fallback)`
- `opening_rotation_krx_regular_scope_skipped` count=`417` routing=`reviewed_unknown_token_provenance` fields=`forbidden_uses=417(reviewed_forbidden_uses_unknown_literal_not_source_value)`
- `blocked_overbought` count=`400` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=2(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_adverse_micro_recovery_checkpoint` count=`369` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_adverse_micro_recovery_ws_0b_raw_route=60(reviewed_adverse_micro_recovery_route_not_available)`
- `risky_micro_episode_source_candidate_observed` count=`359` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=321(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=32(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=32(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=32(reviewed_explicit_sizing_unknown_venue_fallback)`
- `ai_confirmed` count=`310` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=83(reviewed_rising_missed_nxt_eligibility_not_available), entry_order_flow_status=32(reviewed_entry_order_flow_not_available), tier_reason=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback)`
- `latency_block` count=`288` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=254(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=26(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=26(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=26(reviewed_explicit_sizing_unknown_venue_fallback)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `60357`
- `scalping_scanner_fast_precheck`: `46908`
- `scalping_scanner_runtime_target_attach`: `31990`
- `scalping_scanner_runtime_queue_lag`: `24905`
- `scalping_scanner_heavy_eval_completion`: `13935`
- `scalping_scanner_heavy_eval_lag`: `13449`
- `scalping_scanner_watching_runtime_skip`: `10433`
- `rising_missed_nxt_post_block_price_sample`: `10067`
- `rising_missed_tp1_counterfactual_submit_safety`: `5191`
- `rising_missed_watch_not_rising_skipped`: `4187`
- `rising_missed_tp1_candidate_deferred`: `3223`
- `holding_ws_freshness_blocked`: `3131`
- `scalping_scanner_candidate_observed`: `1977`
- `scalping_scanner_real_source_guard_block`: `1977`
- `rising_missed_tp1_candidate_blocked`: `1968`
- `strength_momentum_observed`: `1873`
- `scalping_scanner_candidate_promoted`: `1846`
- `scalping_scanner_watch_eviction`: `1469`
- `bad_entry_refined_candidate`: `1366`
- `risky_micro_episode_executable_bbo_observed`: `1342`

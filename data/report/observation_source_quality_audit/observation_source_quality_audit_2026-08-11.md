# Observation Source Quality Audit - 2026-08-11

- status: `warning`
- event_count: `320664`
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
- `scalping_scanner_ws_prewarm_filtered` count=`3` routing=`source_quality_blocker_or_provenance_backfill` fields=`venue=2(0.6667), effective_venue=2(0.6667)`

## Reviewed Unknown Token Findings
- `scalping_scanner_promotion_latency_trace` count=`93230` routing=`reviewed_unknown_token_provenance` fields=`venue=106(reviewed_scanner_venue_fail_closed_provenance), effective_venue=106(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_fast_precheck` count=`71245` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=1652(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=361(reviewed_scanner_stale_backoff_route_not_available), venue=79(reviewed_scanner_venue_fail_closed_provenance), effective_venue=79(reviewed_scanner_venue_fail_closed_provenance), scanner_promotion_reanchor_effective_venue=79(reviewed_scanner_venue_fail_closed_provenance), scanner_stale_backoff_canonical_effective_venue=79(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_runtime_queue_lag` count=`38088` routing=`reviewed_unknown_token_provenance` fields=`venue=49(reviewed_scanner_venue_fail_closed_provenance), effective_venue=49(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_heavy_eval_completion` count=`22547` routing=`reviewed_unknown_token_provenance` fields=`venue=35(reviewed_scanner_venue_fail_closed_provenance), effective_venue=35(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_heavy_eval_lag` count=`21985` routing=`reviewed_unknown_token_provenance` fields=`venue=27(reviewed_scanner_venue_fail_closed_provenance), effective_venue=27(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_watching_runtime_skip` count=`12377` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=2091(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=244(reviewed_explicit_sizing_unknown_venue_fallback), venue=8(reviewed_scanner_venue_fail_closed_provenance), effective_venue=8(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_watch_not_rising_skipped` count=`9271` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=5925(reviewed_rising_missed_nxt_eligibility_not_available), venue=85(reviewed_observation_only_venue_not_available)`
- `strength_momentum_observed` count=`2330` routing=`reviewed_unknown_token_provenance` fields=`venue=23(reviewed_scanner_venue_fail_closed_provenance), effective_venue=23(reviewed_scanner_venue_fail_closed_provenance), rising_missed_nxt_eligible=10(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`2136` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=554(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=1(reviewed_explicit_sizing_unknown_venue_fallback)`
- `blocked_strength_momentum` count=`1710` routing=`reviewed_unknown_token_provenance` fields=`venue=14(reviewed_scanner_venue_fail_closed_provenance), effective_venue=14(reviewed_scanner_venue_fail_closed_provenance), rising_missed_nxt_eligible=8(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_candidate_deferred` count=`1422` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=171(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=1(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scalping_scanner_ws_backoff_watch_retained` count=`817` routing=`reviewed_unknown_token_provenance` fields=`venue=3(reviewed_scanner_venue_fail_closed_provenance), effective_venue=3(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_tp1_candidate_blocked` count=`714` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=383(reviewed_rising_missed_nxt_eligibility_not_available)`
- `strength_momentum_stability_recheck_pending` count=`614` routing=`reviewed_unknown_token_provenance` fields=`venue=9(reviewed_scanner_venue_fail_closed_provenance), effective_venue=9(reviewed_scanner_venue_fail_closed_provenance), rising_missed_nxt_eligible=2(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalp_entry_action_decision_snapshot` count=`602` routing=`reviewed_unknown_token_provenance` fields=`holding_exit_matrix_score_prior_band=435(reviewed_score_prior_neutral_unknown_not_decision_input), rising_missed_nxt_eligible=151(reviewed_rising_missed_nxt_eligibility_not_available), risk_regime_context=128(reviewed_missing_risk_regime_context), entry_order_flow_status=59(reviewed_entry_order_flow_not_available), score_prior_band=24(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=24(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=19(reviewed_entry_score_source_not_available), entry_recheck_excluded_reason=19(reviewed_entry_score_source_not_available)`
- `prev_close_gainer_entry_ai_handoff` count=`600` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=345(reviewed_rising_missed_nxt_eligibility_not_available), venue=19(reviewed_observation_only_venue_not_available)`
- `blocked_overbought` count=`586` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=10(reviewed_rising_missed_nxt_eligibility_not_available)`
- `opening_rotation_krx_regular_scope_skipped` count=`493` routing=`reviewed_unknown_token_provenance` fields=`forbidden_uses=493(reviewed_forbidden_uses_unknown_literal_not_source_value), venue=92(reviewed_scanner_venue_fail_closed_provenance), effective_venue=92(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_one_share_entry` count=`476` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=443(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=6(reviewed_explicit_sizing_unknown_venue_fallback), venue=2(reviewed_explicit_sizing_unknown_venue_fallback), effective_venue=2(reviewed_rising_missed_explicit_venue_conflict)`
- `opening_rotation_1pct_observed` count=`406` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1(reviewed_rising_missed_nxt_eligibility_not_available)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `93230`
- `scalping_scanner_fast_precheck`: `71245`
- `scalping_scanner_runtime_queue_lag`: `38088`
- `scalping_scanner_heavy_eval_completion`: `22547`
- `scalping_scanner_heavy_eval_lag`: `21985`
- `scalping_scanner_watching_runtime_skip`: `12377`
- `scalping_scanner_runtime_target_attach`: `11982`
- `rising_missed_watch_not_rising_skipped`: `9271`
- `rising_missed_nxt_post_block_price_sample`: `7584`
- `scalping_scanner_candidate_observed`: `4677`
- `scalping_scanner_real_source_guard_block`: `4677`
- `strength_momentum_observed`: `2330`
- `rising_missed_tp1_counterfactual_submit_safety`: `2136`
- `scalping_scanner_candidate_promoted`: `2108`
- `blocked_strength_momentum`: `1710`
- `scalping_scanner_watch_eviction`: `1647`
- `rising_missed_tp1_candidate_deferred`: `1422`
- `scalping_scanner_ws_backoff_watch_retained`: `817`
- `rising_missed_tp1_candidate_blocked`: `714`
- `manual_control_fast_exit_monitor_blocked`: `692`

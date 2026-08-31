# Observation Source Quality Audit - 2026-08-31

- status: `pass`
- event_count: `344705`
- tuning_input_policy: `exclude_defective_rows_not_full_day_raw`
- hard_blocking_excluded_row_count: `0`
- pre_exclusion_hard_blocking_excluded_row_count: `None`
- current_scan_hard_blocking_excluded_row_count: `None`
- post_exclusion_hard_blocking_excluded_row_count: `None`
- raw_row_exclusion_applied: `False`
- raw_row_exclusion_deferred_writer_active: `False`
- raw_row_exclusion_revalidation_required: `False`
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
- `scalping_scanner_fast_precheck` count=`56879` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=1817(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=487(reviewed_scanner_stale_backoff_route_not_available), rising_missed_submit_safety_backoff_reason=3(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `scalping_scanner_watching_runtime_skip` count=`11154` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=863(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=55(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=55(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=55(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_effective_venue=29(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_watch_not_rising_skipped` count=`9370` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=6951(reviewed_rising_missed_nxt_eligibility_not_available), venue=435(reviewed_observation_only_venue_not_available), rising_missed_effective_venue=435(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`4266` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1444(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=116(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=18(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=18(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=18(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_tp1_candidate_deferred` count=`2612` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=497(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=112(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scalp_entry_action_decision_snapshot` count=`1772` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1197(reviewed_rising_missed_nxt_eligibility_not_available), holding_exit_matrix_score_prior_band=506(reviewed_score_prior_neutral_unknown_not_decision_input), entry_order_flow_status=108(reviewed_entry_order_flow_not_available), risk_regime_context=98(reviewed_missing_risk_regime_context), tier_reason=50(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=50(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=50(reviewed_explicit_sizing_unknown_venue_fallback), score_prior_band=48(reviewed_score_prior_neutral_unknown_not_decision_input)`
- `rising_missed_tp1_candidate_blocked` count=`1654` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=947(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=17(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=17(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=17(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_effective_venue=4(reviewed_rising_missed_nxt_eligibility_not_available)`
- `strength_momentum_observed` count=`1610` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=10(reviewed_rising_missed_nxt_eligibility_not_available)`
- `blocked_strength_momentum` count=`1188` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=6(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_one_share_entry` count=`1143` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=991(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=15(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=9(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=9(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=9(reviewed_explicit_sizing_unknown_venue_fallback)`
- `budget_pass` count=`1103` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=952(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=32(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=32(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=32(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_effective_venue=9(reviewed_rising_missed_nxt_eligibility_not_available)`
- `orderbook_stability_observed` count=`1103` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=952(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=32(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=32(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=32(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_effective_venue=9(reviewed_rising_missed_nxt_eligibility_not_available)`
- `risky_micro_episode_source_candidate_observed` count=`764` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=673(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=21(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=21(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=21(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_effective_venue=3(reviewed_rising_missed_nxt_eligibility_not_available)`
- `latency_block` count=`565` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=503(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=11(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=11(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=11(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_effective_venue=3(reviewed_rising_missed_nxt_eligibility_not_available), latency_true_ofi_nxt_probability_band_effective_venue=3(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_adverse_micro_recovery_checkpoint` count=`522` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_adverse_micro_recovery_ws_0b_raw_route=27(reviewed_adverse_micro_recovery_route_not_available)`
- `prev_close_gainer_entry_ai_handoff` count=`440` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=285(reviewed_rising_missed_nxt_eligibility_not_available)`
- `entry_ai_price_canary_applied` count=`433` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=364(reviewed_rising_missed_nxt_eligibility_not_available), entry_order_flow_status=31(reviewed_entry_order_flow_not_available), tier_reason=19(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=19(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=19(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_effective_venue=3(reviewed_rising_missed_nxt_eligibility_not_available)`
- `strength_momentum_stability_recheck_pending` count=`388` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=4(reviewed_rising_missed_nxt_eligibility_not_available)`
- `ai_confirmed` count=`373` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=132(reviewed_rising_missed_nxt_eligibility_not_available), entry_order_flow_status=27(reviewed_entry_order_flow_not_available), tier_reason=9(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=9(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=9(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_effective_venue=1(reviewed_rising_missed_nxt_eligibility_not_available)`
- `blocked_overbought` count=`372` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=11(reviewed_rising_missed_nxt_eligibility_not_available)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `74091`
- `scalping_scanner_fast_precheck`: `56879`
- `scalping_scanner_candidate_pruned`: `49418`
- `scalping_scanner_runtime_queue_lag`: `31673`
- `scalping_scanner_heavy_eval_completion`: `17589`
- `scalping_scanner_heavy_eval_lag`: `17212`
- `rising_missed_nxt_post_block_price_sample`: `16510`
- `risky_micro_episode_executable_bbo_observed`: `12849`
- `scalping_scanner_watching_runtime_skip`: `11154`
- `scalping_scanner_runtime_target_attach`: `10110`
- `rising_missed_watch_not_rising_skipped`: `9370`
- `rising_missed_tp1_counterfactual_submit_safety`: `4266`
- `rising_missed_tp1_candidate_deferred`: `2612`
- `scalping_scanner_candidate_promoted`: `2437`
- `scalping_scanner_watch_eviction`: `2215`
- `scalp_entry_action_decision_snapshot`: `1772`
- `scalping_scanner_candidate_observed`: `1741`
- `scalping_scanner_real_source_guard_block`: `1741`
- `rising_missed_tp1_candidate_blocked`: `1654`
- `strength_momentum_observed`: `1610`

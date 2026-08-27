# Observation Source Quality Audit - 2026-08-27

- status: `pass`
- event_count: `283384`
- tuning_input_policy: `exclude_defective_rows_not_full_day_raw`
- hard_blocking_excluded_row_count: `3`
- pre_exclusion_hard_blocking_excluded_row_count: `3`
- current_scan_hard_blocking_excluded_row_count: `0`
- post_exclusion_hard_blocking_excluded_row_count: `0`
- raw_row_exclusion_applied: `True`
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
- `scalping_scanner_promotion_latency_trace` count=`70724` routing=`reviewed_unknown_token_provenance` fields=`venue=66(reviewed_scanner_venue_fail_closed_provenance), effective_venue=66(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_fast_precheck` count=`54307` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=1099(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=423(reviewed_scanner_stale_backoff_route_not_available), venue=52(reviewed_scanner_venue_fail_closed_provenance), effective_venue=52(reviewed_scanner_venue_fail_closed_provenance), scanner_promotion_reanchor_effective_venue=52(reviewed_scanner_venue_fail_closed_provenance), scanner_stale_backoff_canonical_effective_venue=52(reviewed_scanner_venue_fail_closed_provenance), rising_missed_submit_safety_backoff_reason=2(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `scalping_scanner_runtime_queue_lag` count=`29715` routing=`reviewed_unknown_token_provenance` fields=`venue=35(reviewed_scanner_venue_fail_closed_provenance), effective_venue=35(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_heavy_eval_completion` count=`16830` routing=`reviewed_unknown_token_provenance` fields=`venue=15(reviewed_scanner_venue_fail_closed_provenance), effective_venue=15(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_heavy_eval_lag` count=`16417` routing=`reviewed_unknown_token_provenance` fields=`venue=14(reviewed_scanner_venue_fail_closed_provenance), effective_venue=14(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_watching_runtime_skip` count=`10210` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=969(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=109(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=109(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=109(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_effective_venue=55(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_nxt_post_block_price_sample` count=`9684` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_post_block_ws_0b_route=1(reviewed_rising_missed_nxt_post_block_route_not_available), rising_missed_nxt_post_block_ws_0d_route=1(reviewed_rising_missed_nxt_post_block_route_not_available)`
- `rising_missed_watch_not_rising_skipped` count=`8207` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=5322(reviewed_rising_missed_nxt_eligibility_not_available), venue=174(reviewed_observation_only_venue_not_available), rising_missed_effective_venue=174(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`4286` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=2245(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=257(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=7(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=7(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=7(reviewed_explicit_sizing_unknown_venue_fallback), venue=6(reviewed_rising_missed_explicit_venue_conflict), effective_venue=6(reviewed_rising_missed_explicit_venue_conflict)`
- `rising_missed_tp1_candidate_blocked` count=`2475` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1885(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=105(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=7(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=7(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=7(reviewed_explicit_sizing_unknown_venue_fallback), venue=6(reviewed_rising_missed_explicit_venue_conflict), effective_venue=6(reviewed_rising_missed_explicit_venue_conflict)`
- `rising_missed_tp1_candidate_deferred` count=`1811` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=360(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=152(reviewed_rising_missed_nxt_eligibility_not_available)`
- `strength_momentum_observed` count=`1804` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=10(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalp_entry_action_decision_snapshot` count=`1625` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1107(reviewed_rising_missed_nxt_eligibility_not_available), holding_exit_matrix_score_prior_band=526(reviewed_score_prior_neutral_unknown_not_decision_input), entry_order_flow_status=230(reviewed_entry_order_flow_not_available), risk_regime_context=170(reviewed_missing_risk_regime_context), score_prior_band=93(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=93(reviewed_score_prior_neutral_unknown_not_decision_input), rising_missed_effective_venue=60(reviewed_rising_missed_nxt_eligibility_not_available), latency_true_ofi_nxt_probability_band_effective_venue=51(reviewed_rising_missed_nxt_eligibility_not_available)`
- `blocked_strength_momentum` count=`1283` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=7(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_one_share_entry` count=`1005` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=946(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=45(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback), venue=3(reviewed_rising_missed_explicit_venue_conflict), effective_venue=3(reviewed_rising_missed_explicit_venue_conflict)`
- `budget_pass` count=`896` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=842(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=45(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=28(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=28(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=28(reviewed_explicit_sizing_unknown_venue_fallback)`
- `orderbook_stability_observed` count=`896` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=842(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=45(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=28(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=28(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=28(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scalping_scanner_ws_backoff_watch_retained` count=`845` routing=`reviewed_unknown_token_provenance` fields=`venue=5(reviewed_scanner_venue_fail_closed_provenance), effective_venue=5(reviewed_scanner_venue_fail_closed_provenance)`
- `risky_micro_episode_source_candidate_observed` count=`672` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=643(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=22(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=19(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=19(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=19(reviewed_explicit_sizing_unknown_venue_fallback)`
- `stat_action_decision_snapshot` count=`548` routing=`reviewed_unknown_token_provenance` fields=`prior_probe_residual_direction_state=47(reviewed_prior_probe_residual_source_gap), prior_probe_residual_failure_signature=47(reviewed_prior_probe_residual_source_gap), tick_context_stale=17(reviewed_stale_flag_not_available), quote_stale=17(reviewed_stale_flag_not_available)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `70724`
- `scalping_scanner_fast_precheck`: `54307`
- `scalping_scanner_runtime_queue_lag`: `29715`
- `scalping_scanner_runtime_target_attach`: `22232`
- `scalping_scanner_heavy_eval_completion`: `16830`
- `scalping_scanner_heavy_eval_lag`: `16417`
- `scalping_scanner_watching_runtime_skip`: `10210`
- `risky_micro_episode_executable_bbo_observed`: `10134`
- `rising_missed_nxt_post_block_price_sample`: `9684`
- `rising_missed_watch_not_rising_skipped`: `8207`
- `rising_missed_tp1_counterfactual_submit_safety`: `4286`
- `rising_missed_tp1_candidate_blocked`: `2475`
- `scalping_scanner_candidate_promoted`: `2031`
- `rising_missed_tp1_candidate_deferred`: `1811`
- `strength_momentum_observed`: `1804`
- `scalping_scanner_watch_eviction`: `1640`
- `scalp_entry_action_decision_snapshot`: `1625`
- `blocked_strength_momentum`: `1283`
- `rising_missed_one_share_entry`: `1005`
- `bad_entry_refined_candidate`: `947`

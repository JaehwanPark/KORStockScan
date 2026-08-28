# Observation Source Quality Audit - 2026-08-28

- status: `warning`
- event_count: `250197`
- tuning_input_policy: `exclude_defective_rows_not_full_day_raw`
- hard_blocking_excluded_row_count: `1`
- pre_exclusion_hard_blocking_excluded_row_count: `1`
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
- `order_bundle_failed` count=`36` routing=`source_quality_blocker_or_provenance_backfill` fields=`entry_order_flow_status=2(0.0556)`

## Reviewed Unknown Token Findings
- `scalping_scanner_promotion_latency_trace` count=`62183` routing=`reviewed_unknown_token_provenance` fields=`venue=21(reviewed_scanner_venue_fail_closed_provenance), effective_venue=21(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_fast_precheck` count=`49211` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=1729(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=833(reviewed_scanner_stale_backoff_route_not_available), venue=18(reviewed_scanner_venue_fail_closed_provenance), effective_venue=18(reviewed_scanner_venue_fail_closed_provenance), scanner_promotion_reanchor_effective_venue=18(reviewed_scanner_venue_fail_closed_provenance), scanner_stale_backoff_canonical_effective_venue=18(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_runtime_queue_lag` count=`27304` routing=`reviewed_unknown_token_provenance` fields=`venue=14(reviewed_scanner_venue_fail_closed_provenance), effective_venue=14(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_watching_runtime_skip` count=`14958` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1140(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=148(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=148(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=148(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_effective_venue=7(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalping_scanner_heavy_eval_completion` count=`13374` routing=`reviewed_unknown_token_provenance` fields=`venue=3(reviewed_scanner_venue_fail_closed_provenance), effective_venue=3(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_heavy_eval_lag` count=`12972` routing=`reviewed_unknown_token_provenance` fields=`venue=3(reviewed_scanner_venue_fail_closed_provenance), effective_venue=3(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_watch_not_rising_skipped` count=`6578` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=4236(reviewed_rising_missed_nxt_eligibility_not_available), venue=52(reviewed_observation_only_venue_not_available), rising_missed_effective_venue=52(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`2225` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1406(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=48(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback)`
- `strength_momentum_observed` count=`1899` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=50(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalping_scanner_ws_backoff_watch_retained` count=`1565` routing=`reviewed_unknown_token_provenance` fields=`venue=3(reviewed_scanner_venue_fail_closed_provenance), effective_venue=3(reviewed_scanner_venue_fail_closed_provenance)`
- `blocked_strength_momentum` count=`1428` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=46(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalp_entry_action_decision_snapshot` count=`1383` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=805(reviewed_rising_missed_nxt_eligibility_not_available), holding_exit_matrix_score_prior_band=540(reviewed_score_prior_neutral_unknown_not_decision_input), risk_regime_context=190(reviewed_missing_risk_regime_context), entry_order_flow_status=141(reviewed_entry_order_flow_not_available), score_prior_band=83(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=83(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=25(reviewed_entry_score_source_not_available), entry_recheck_excluded_reason=25(reviewed_entry_score_source_not_available)`
- `rising_missed_tp1_candidate_blocked` count=`1301` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1123(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=24(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_tp1_candidate_deferred` count=`924` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=283(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=24(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_one_share_entry` count=`796` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=715(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=12(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=6(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=6(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=6(reviewed_explicit_sizing_unknown_venue_fallback), venue=1(reviewed_explicit_sizing_unknown_venue_fallback), effective_venue=1(reviewed_rising_missed_explicit_venue_conflict)`
- `budget_pass` count=`661` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=580(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=20(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=20(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=20(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_effective_venue=11(reviewed_rising_missed_nxt_eligibility_not_available)`
- `orderbook_stability_observed` count=`661` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=580(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=20(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=20(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=20(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_effective_venue=11(reviewed_rising_missed_nxt_eligibility_not_available)`
- `stat_action_decision_snapshot` count=`513` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=12(reviewed_stale_flag_not_available), quote_stale=12(reviewed_stale_flag_not_available), prior_probe_residual_direction_state=5(reviewed_prior_probe_residual_source_gap), prior_probe_residual_failure_signature=5(reviewed_prior_probe_residual_source_gap), shallow_tick_context_stale=1(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=1(reviewed_shallow_stale_flag_not_available)`
- `prev_close_gainer_entry_ai_handoff` count=`503` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=282(reviewed_rising_missed_nxt_eligibility_not_available), venue=12(reviewed_observation_only_venue_not_available), rising_missed_effective_venue=12(reviewed_rising_missed_nxt_eligibility_not_available)`
- `reversal_add_blocked_reason` count=`476` routing=`reviewed_unknown_token_provenance` fields=`prior_probe_residual_direction_state=2(reviewed_prior_probe_residual_source_gap), prior_probe_residual_failure_signature=2(reviewed_prior_probe_residual_source_gap), shallow_tick_context_stale=1(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=1(reviewed_shallow_stale_flag_not_available), tick_context_stale=1(reviewed_stale_flag_not_available), quote_stale=1(reviewed_stale_flag_not_available)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `62183`
- `scalping_scanner_fast_precheck`: `49211`
- `scalping_scanner_runtime_queue_lag`: `27304`
- `scalping_scanner_watching_runtime_skip`: `14958`
- `scalping_scanner_heavy_eval_completion`: `13374`
- `scalping_scanner_heavy_eval_lag`: `12972`
- `scalping_scanner_runtime_target_attach`: `12358`
- `rising_missed_nxt_post_block_price_sample`: `8130`
- `risky_micro_episode_executable_bbo_observed`: `6987`
- `rising_missed_watch_not_rising_skipped`: `6578`
- `scalping_scanner_candidate_promoted`: `2807`
- `scalping_scanner_candidate_observed`: `2777`
- `scalping_scanner_real_source_guard_block`: `2777`
- `scalping_scanner_watch_eviction`: `2387`
- `rising_missed_tp1_counterfactual_submit_safety`: `2225`
- `strength_momentum_observed`: `1899`
- `scalping_scanner_ws_backoff_watch_retained`: `1565`
- `blocked_strength_momentum`: `1428`
- `scalp_entry_action_decision_snapshot`: `1383`
- `rising_missed_tp1_candidate_blocked`: `1301`

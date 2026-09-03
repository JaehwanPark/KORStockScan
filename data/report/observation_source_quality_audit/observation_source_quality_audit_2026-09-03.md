# Observation Source Quality Audit - 2026-09-03

- status: `pass`
- event_count: `406489`
- tuning_input_policy: `exclude_defective_rows_not_full_day_raw`
- hard_blocking_excluded_row_count: `31`
- pre_exclusion_hard_blocking_excluded_row_count: `31`
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
- `scalping_scanner_promotion_latency_trace` count=`59190` routing=`reviewed_unknown_token_provenance` fields=`venue=82(reviewed_scanner_venue_fail_closed_provenance), effective_venue=82(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_fast_precheck` count=`46068` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=1206(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=406(reviewed_scanner_stale_backoff_route_not_available), venue=61(reviewed_scanner_venue_fail_closed_provenance), effective_venue=61(reviewed_scanner_venue_fail_closed_provenance), scanner_promotion_reanchor_effective_venue=61(reviewed_scanner_venue_fail_closed_provenance), scanner_stale_backoff_canonical_effective_venue=61(reviewed_scanner_venue_fail_closed_provenance), rising_missed_submit_safety_backoff_reason=1(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `scalping_scanner_runtime_queue_lag` count=`26068` routing=`reviewed_unknown_token_provenance` fields=`venue=35(reviewed_scanner_venue_fail_closed_provenance), effective_venue=35(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_heavy_eval_completion` count=`13422` routing=`reviewed_unknown_token_provenance` fields=`venue=22(reviewed_scanner_venue_fail_closed_provenance), effective_venue=22(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_heavy_eval_lag` count=`13122` routing=`reviewed_unknown_token_provenance` fields=`venue=21(reviewed_scanner_venue_fail_closed_provenance), effective_venue=21(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_watching_runtime_skip` count=`12537` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=805(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=83(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=83(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=83(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_effective_venue=41(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_nxt_post_block_price_sample` count=`12038` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_post_block_ws_0b_route=3(reviewed_rising_missed_nxt_post_block_route_not_available), rising_missed_nxt_post_block_ws_0d_route=3(reviewed_rising_missed_nxt_post_block_route_not_available)`
- `rising_missed_watch_not_rising_skipped` count=`5817` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=4576(reviewed_rising_missed_nxt_eligibility_not_available), venue=26(reviewed_observation_only_venue_not_available), rising_missed_effective_venue=26(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`3225` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=892(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=99(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=6(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=6(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=6(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_entry_turn_pre_anchor_bbo_path` count=`3160` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=407(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=99(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=6(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=6(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=6(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_tp1_candidate_deferred` count=`2261` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=256(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=96(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback)`
- `strength_momentum_observed` count=`1853` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=5(reviewed_rising_missed_nxt_eligibility_not_available)`
- `blocked_strength_momentum` count=`1471` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=2(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalping_scanner_ws_backoff_watch_retained` count=`1269` routing=`reviewed_unknown_token_provenance` fields=`venue=2(reviewed_scanner_venue_fail_closed_provenance), effective_venue=2(reviewed_scanner_venue_fail_closed_provenance)`
- `scalp_entry_action_decision_snapshot` count=`1257` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=691(reviewed_rising_missed_nxt_eligibility_not_available), holding_exit_matrix_score_prior_band=483(reviewed_score_prior_neutral_unknown_not_decision_input), entry_order_flow_status=125(reviewed_entry_order_flow_not_available), risk_regime_context=88(reviewed_missing_risk_regime_context), score_prior_band=73(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=73(reviewed_score_prior_neutral_unknown_not_decision_input), tier_reason=52(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=52(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_tp1_candidate_blocked` count=`964` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=636(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_effective_venue=3(reviewed_rising_missed_nxt_eligibility_not_available)`
- `reversal_add_blocked_reason` count=`894` routing=`reviewed_unknown_token_provenance` fields=`shallow_tick_context_stale=21(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=21(reviewed_shallow_stale_flag_not_available), tick_context_stale=21(reviewed_stale_flag_not_available), quote_stale=21(reviewed_stale_flag_not_available)`
- `stat_action_decision_snapshot` count=`856` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=29(reviewed_stale_flag_not_available), quote_stale=29(reviewed_stale_flag_not_available), shallow_tick_context_stale=21(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=21(reviewed_shallow_stale_flag_not_available)`
- `rising_missed_one_share_entry` count=`713` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=608(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=11(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=11(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=11(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_effective_venue=6(reviewed_rising_missed_nxt_eligibility_not_available), effective_venue=2(reviewed_rising_missed_explicit_venue_conflict), venue=1(reviewed_rising_missed_explicit_venue_conflict), venue=1(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scalp_sim_panic_context_warning` count=`606` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=606(reviewed_missing_risk_regime_context), market_risk_state=606(reviewed_missing_risk_regime_context), liquidity_state=606(reviewed_missing_risk_regime_context), risk_regime_epoch_id=606(reviewed_missing_risk_regime_context)`

## Top Stages
- `scalping_scanner_candidate_pruned`: `90342`
- `scalping_scanner_prune_bbo_schedule`: `71873`
- `scalping_scanner_promotion_latency_trace`: `59190`
- `scalping_scanner_fast_precheck`: `46068`
- `scalping_scanner_runtime_queue_lag`: `26068`
- `scalping_scanner_heavy_eval_completion`: `13422`
- `scalping_scanner_heavy_eval_lag`: `13122`
- `scalping_scanner_watching_runtime_skip`: `12537`
- `rising_missed_nxt_post_block_price_sample`: `12038`
- `risky_micro_episode_executable_bbo_observed`: `6382`
- `rising_missed_watch_not_rising_skipped`: `5817`
- `rising_missed_tp1_counterfactual_submit_safety`: `3225`
- `rising_missed_entry_turn_pre_anchor_bbo_path`: `3160`
- `scalping_scanner_runtime_target_attach`: `3026`
- `scalping_scanner_candidate_promoted`: `2747`
- `scalping_scanner_prune_bbo_observation`: `2557`
- `scalping_scanner_candidate_observed`: `2546`
- `scalping_scanner_real_source_guard_block`: `2546`
- `scalping_scanner_watch_eviction`: `2333`
- `rising_missed_tp1_candidate_deferred`: `2261`

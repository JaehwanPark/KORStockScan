# Observation Source Quality Audit - 2026-08-04

- status: `pass`
- event_count: `540745`
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
- `scalping_scanner_heavy_eval_completion` count=`123537` routing=`reviewed_unknown_token_provenance` fields=`venue=193(reviewed_scanner_venue_fail_closed_provenance), effective_venue=193(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_promotion_latency_trace` count=`95561` routing=`reviewed_unknown_token_provenance` fields=`venue=290(reviewed_scanner_venue_fail_closed_provenance), effective_venue=290(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_watch_not_rising_skipped` count=`70051` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=30233(reviewed_rising_missed_nxt_eligibility_not_available), venue=2279(reviewed_observation_only_venue_not_available)`
- `scalping_scanner_fast_precheck` count=`57070` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=2086(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=476(reviewed_scanner_stale_backoff_route_not_available), venue=187(reviewed_scanner_venue_fail_closed_provenance), effective_venue=187(reviewed_scanner_venue_fail_closed_provenance), scanner_promotion_reanchor_effective_venue=187(reviewed_scanner_venue_fail_closed_provenance), scanner_stale_backoff_canonical_effective_venue=187(reviewed_scanner_venue_fail_closed_provenance), rising_missed_submit_safety_backoff_reason=1(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `scalping_scanner_heavy_eval_lag` count=`38491` routing=`reviewed_unknown_token_provenance` fields=`venue=103(reviewed_scanner_venue_fail_closed_provenance), effective_venue=103(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_runtime_queue_lag` count=`31029` routing=`reviewed_unknown_token_provenance` fields=`venue=103(reviewed_scanner_venue_fail_closed_provenance), effective_venue=103(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`17045` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1116(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=42(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_tp1_candidate_deferred` count=`13385` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=278(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=11(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scalping_scanner_watching_runtime_skip` count=`13159` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1471(reviewed_rising_missed_nxt_eligibility_not_available), venue=87(reviewed_scanner_venue_fail_closed_provenance), effective_venue=87(reviewed_scanner_venue_fail_closed_provenance), tier_reason=51(reviewed_explicit_sizing_unknown_venue_fallback)`
- `strength_momentum_observed` count=`4169` routing=`reviewed_unknown_token_provenance` fields=`venue=27(reviewed_scanner_venue_fail_closed_provenance), effective_venue=27(reviewed_scanner_venue_fail_closed_provenance), tier_reason=14(reviewed_explicit_sizing_unknown_venue_fallback), venue=14(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_nxt_eligible=9(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_candidate_blocked` count=`3660` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=838(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=31(reviewed_explicit_sizing_unknown_venue_fallback)`
- `blocked_strength_momentum` count=`3493` routing=`reviewed_unknown_token_provenance` fields=`venue=26(reviewed_scanner_venue_fail_closed_provenance), effective_venue=26(reviewed_scanner_venue_fail_closed_provenance), tier_reason=14(reviewed_explicit_sizing_unknown_venue_fallback), venue=14(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_nxt_eligible=9(reviewed_rising_missed_nxt_eligibility_not_available)`
- `blocked_overbought` count=`1949` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=9(reviewed_rising_missed_nxt_eligibility_not_available)`
- `stat_action_decision_snapshot` count=`1246` routing=`reviewed_unknown_token_provenance` fields=`prior_probe_residual_direction_state=426(reviewed_prior_probe_residual_source_gap), prior_probe_residual_failure_signature=386(reviewed_prior_probe_residual_source_gap), tick_context_stale=37(reviewed_stale_flag_not_available), quote_stale=37(reviewed_stale_flag_not_available), shallow_tick_context_stale=32(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=32(reviewed_shallow_stale_flag_not_available)`
- `scalp_entry_action_decision_snapshot` count=`1231` routing=`reviewed_unknown_token_provenance` fields=`holding_exit_matrix_score_prior_band=644(reviewed_score_prior_neutral_unknown_not_decision_input), rising_missed_nxt_eligible=559(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=129(reviewed_explicit_sizing_unknown_venue_fallback), entry_order_flow_status=125(reviewed_entry_order_flow_not_available), score_prior_band=71(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=71(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=68(reviewed_entry_score_source_not_available), entry_score_excluded_reason=68(reviewed_entry_score_source_not_available)`
- `scalping_scanner_ws_backoff_watch_retained` count=`1179` routing=`reviewed_unknown_token_provenance` fields=`venue=19(reviewed_scanner_venue_fail_closed_provenance), effective_venue=19(reviewed_scanner_venue_fail_closed_provenance)`
- `reversal_add_blocked_reason` count=`1148` routing=`reviewed_unknown_token_provenance` fields=`prior_probe_residual_direction_state=381(reviewed_prior_probe_residual_source_gap), prior_probe_residual_failure_signature=342(reviewed_prior_probe_residual_source_gap), shallow_tick_context_stale=33(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=33(reviewed_shallow_stale_flag_not_available), tick_context_stale=33(reviewed_stale_flag_not_available), quote_stale=33(reviewed_stale_flag_not_available)`
- `ai_holding_review` count=`1126` routing=`reviewed_unknown_token_provenance` fields=`holding_context_ws_route=2(reviewed_holding_input_preflight_blocked_provenance), holding_context_blockers=2(reviewed_holding_input_preflight_blocked_provenance), entry_order_flow_status=1(reviewed_entry_order_flow_not_available)`
- `opening_rotation_1pct_observed` count=`946` routing=`reviewed_unknown_token_provenance` fields=`venue=23(reviewed_scanner_venue_fail_closed_provenance), effective_venue=23(reviewed_scanner_venue_fail_closed_provenance), scanner_promotion_reanchor_effective_venue=23(reviewed_scanner_venue_fail_closed_provenance), opening_rotation_no_pullback_continuation_effective_venue=23(reviewed_scanner_venue_fail_closed_provenance)`
- `opening_rotation_1pct_upstream_blocked` count=`792` routing=`reviewed_unknown_token_provenance` fields=`venue=46(reviewed_scanner_venue_fail_closed_provenance), effective_venue=46(reviewed_scanner_venue_fail_closed_provenance), rising_missed_nxt_eligible=1(reviewed_rising_missed_nxt_eligibility_not_available)`

## Top Stages
- `scalping_scanner_heavy_eval_completion`: `123537`
- `scalping_scanner_promotion_latency_trace`: `95561`
- `rising_missed_watch_not_rising_skipped`: `70051`
- `scalping_scanner_fast_precheck`: `57070`
- `scalping_scanner_heavy_eval_lag`: `38491`
- `scalping_scanner_runtime_queue_lag`: `31029`
- `rising_missed_tp1_counterfactual_submit_safety`: `17045`
- `rising_missed_tp1_candidate_deferred`: `13385`
- `scalping_scanner_watching_runtime_skip`: `13159`
- `rising_missed_nxt_post_block_price_sample`: `12172`
- `scalping_scanner_runtime_target_attach`: `11373`
- `scalping_scanner_candidate_observed`: `4929`
- `scalping_scanner_real_source_guard_block`: `4929`
- `strength_momentum_observed`: `4169`
- `rising_missed_tp1_candidate_blocked`: `3660`
- `blocked_strength_momentum`: `3493`
- `scalping_scanner_candidate_promoted`: `2593`
- `bad_entry_refined_candidate`: `2240`
- `scalping_scanner_watch_eviction`: `2180`
- `blocked_overbought`: `1949`

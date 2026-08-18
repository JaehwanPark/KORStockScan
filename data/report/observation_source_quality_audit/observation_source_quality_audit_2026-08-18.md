# Observation Source Quality Audit - 2026-08-18

- status: `pass`
- event_count: `330669`
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
- `scalping_scanner_promotion_latency_trace` count=`74676` routing=`reviewed_unknown_token_provenance` fields=`venue=45(reviewed_scanner_venue_fail_closed_provenance), effective_venue=45(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_fast_precheck` count=`58419` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=1846(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=365(reviewed_scanner_stale_backoff_route_not_available), venue=39(reviewed_scanner_venue_fail_closed_provenance), effective_venue=39(reviewed_scanner_venue_fail_closed_provenance), scanner_promotion_reanchor_effective_venue=39(reviewed_scanner_venue_fail_closed_provenance), scanner_stale_backoff_canonical_effective_venue=39(reviewed_scanner_venue_fail_closed_provenance), rising_missed_submit_safety_backoff_reason=1(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `scalping_scanner_runtime_queue_lag` count=`31478` routing=`reviewed_unknown_token_provenance` fields=`venue=23(reviewed_scanner_venue_fail_closed_provenance), effective_venue=23(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_heavy_eval_completion` count=`16787` routing=`reviewed_unknown_token_provenance` fields=`venue=6(reviewed_scanner_venue_fail_closed_provenance), effective_venue=6(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_heavy_eval_lag` count=`16257` routing=`reviewed_unknown_token_provenance` fields=`venue=6(reviewed_scanner_venue_fail_closed_provenance), effective_venue=6(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_watching_runtime_skip` count=`12526` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=870(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=11(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=11(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=11(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_watch_not_rising_skipped` count=`9049` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=7046(reviewed_rising_missed_nxt_eligibility_not_available), venue=13(reviewed_observation_only_venue_not_available)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`2445` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1340(reviewed_rising_missed_nxt_eligibility_not_available)`
- `strength_momentum_observed` count=`2435` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=14(reviewed_rising_missed_nxt_eligibility_not_available)`
- `blocked_strength_momentum` count=`1826` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=12(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalp_entry_action_decision_snapshot` count=`1536` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=951(reviewed_rising_missed_nxt_eligibility_not_available), holding_exit_matrix_score_prior_band=519(reviewed_score_prior_neutral_unknown_not_decision_input), entry_order_flow_status=117(reviewed_entry_order_flow_not_available), risk_regime_context=93(reviewed_missing_risk_regime_context), score_prior_band=24(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=24(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=23(reviewed_entry_score_source_not_available), entry_recheck_excluded_reason=23(reviewed_entry_score_source_not_available)`
- `rising_missed_tp1_candidate_blocked` count=`1334` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1106(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_candidate_deferred` count=`1111` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=234(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalping_scanner_ws_backoff_watch_retained` count=`945` routing=`reviewed_unknown_token_provenance` fields=`venue=1(reviewed_scanner_venue_fail_closed_provenance), effective_venue=1(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_one_share_entry` count=`892` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=776(reviewed_rising_missed_nxt_eligibility_not_available), venue=1(reviewed_rising_missed_explicit_venue_conflict), effective_venue=1(reviewed_rising_missed_explicit_venue_conflict)`
- `budget_pass` count=`843` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=727(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=9(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=9(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=9(reviewed_explicit_sizing_unknown_venue_fallback)`
- `orderbook_stability_observed` count=`843` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=727(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=9(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=9(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=9(reviewed_explicit_sizing_unknown_venue_fallback)`
- `stat_action_decision_snapshot` count=`788` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=71(reviewed_stale_flag_not_available), quote_stale=71(reviewed_stale_flag_not_available), shallow_tick_context_stale=56(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=56(reviewed_shallow_stale_flag_not_available), prior_probe_residual_direction_state=34(reviewed_prior_probe_residual_source_gap), prior_probe_residual_failure_signature=34(reviewed_prior_probe_residual_source_gap)`
- `scalp_sim_panic_context_warning` count=`758` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=758(reviewed_missing_risk_regime_context), market_risk_state=758(reviewed_missing_risk_regime_context), liquidity_state=758(reviewed_missing_risk_regime_context), risk_regime_epoch_id=758(reviewed_missing_risk_regime_context)`
- `reversal_add_blocked_reason` count=`753` routing=`reviewed_unknown_token_provenance` fields=`shallow_tick_context_stale=57(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=57(reviewed_shallow_stale_flag_not_available), tick_context_stale=57(reviewed_stale_flag_not_available), quote_stale=57(reviewed_stale_flag_not_available), prior_probe_residual_direction_state=33(reviewed_prior_probe_residual_source_gap), prior_probe_residual_failure_signature=33(reviewed_prior_probe_residual_source_gap)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `74676`
- `scalping_scanner_fast_precheck`: `58419`
- `scalping_scanner_runtime_queue_lag`: `31478`
- `scalping_scanner_candidate_observed`: `27549`
- `scalping_scanner_real_source_guard_block`: `27549`
- `scalping_scanner_heavy_eval_completion`: `16787`
- `scalping_scanner_heavy_eval_lag`: `16257`
- `scalping_scanner_watching_runtime_skip`: `12526`
- `scalping_scanner_runtime_target_attach`: `10575`
- `rising_missed_watch_not_rising_skipped`: `9049`
- `rising_missed_nxt_post_block_price_sample`: `6113`
- `rising_missed_tp1_counterfactual_submit_safety`: `2445`
- `strength_momentum_observed`: `2435`
- `risky_micro_episode_executable_bbo_observed`: `2305`
- `scalping_scanner_candidate_promoted`: `2097`
- `blocked_strength_momentum`: `1826`
- `scalping_scanner_watch_eviction`: `1794`
- `bad_entry_refined_candidate`: `1561`
- `scalp_entry_action_decision_snapshot`: `1536`
- `rising_missed_tp1_candidate_blocked`: `1334`

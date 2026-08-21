# Observation Source Quality Audit - 2026-08-21

- status: `pass`
- event_count: `322361`
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
- `scalping_scanner_promotion_latency_trace` count=`70606` routing=`reviewed_unknown_token_provenance` fields=`venue=40(reviewed_scanner_venue_fail_closed_provenance), effective_venue=40(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_fast_precheck` count=`54921` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=1616(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=550(reviewed_scanner_stale_backoff_route_not_available), venue=30(reviewed_scanner_venue_fail_closed_provenance), effective_venue=30(reviewed_scanner_venue_fail_closed_provenance), scanner_promotion_reanchor_effective_venue=30(reviewed_scanner_venue_fail_closed_provenance), scanner_stale_backoff_canonical_effective_venue=30(reviewed_scanner_venue_fail_closed_provenance), main_lifecycle_venue=22(reviewed_main_lifecycle_venue_not_available), rising_missed_submit_safety_backoff_reason=4(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `scalping_scanner_runtime_queue_lag` count=`29517` routing=`reviewed_unknown_token_provenance` fields=`venue=20(reviewed_scanner_venue_fail_closed_provenance), effective_venue=20(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_heavy_eval_completion` count=`16165` routing=`reviewed_unknown_token_provenance` fields=`venue=10(reviewed_scanner_venue_fail_closed_provenance), effective_venue=10(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_heavy_eval_lag` count=`15685` routing=`reviewed_unknown_token_provenance` fields=`venue=10(reviewed_scanner_venue_fail_closed_provenance), effective_venue=10(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_runtime_target_attach` count=`14818` routing=`reviewed_unknown_token_provenance` fields=`venue=4(reviewed_scanner_venue_fail_closed_provenance), effective_venue=4(reviewed_scanner_venue_fail_closed_provenance), market_session_bucket=4(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_watching_runtime_skip` count=`13184` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=990(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=51(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=51(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=51(reviewed_explicit_sizing_unknown_venue_fallback), venue=8(reviewed_scanner_venue_fail_closed_provenance), effective_venue=8(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_nxt_post_block_price_sample` count=`10859` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_post_block_ws_0b_route=200(reviewed_rising_missed_nxt_post_block_route_not_available), rising_missed_nxt_post_block_ws_0d_route=195(reviewed_rising_missed_nxt_post_block_route_not_available)`
- `rising_missed_watch_not_rising_skipped` count=`6789` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=5429(reviewed_rising_missed_nxt_eligibility_not_available), venue=2(reviewed_observation_only_venue_not_available)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`4028` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=2328(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=4(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=4(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=4(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_tp1_candidate_blocked` count=`2456` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=2078(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=4(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=4(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=4(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scalping_scanner_watch_eviction` count=`2196` routing=`reviewed_unknown_token_provenance` fields=`venue=1(reviewed_scanner_venue_fail_closed_provenance), effective_venue=1(reviewed_scanner_venue_fail_closed_provenance), venue=1(reviewed_observation_only_venue_not_available), effective_venue=1(reviewed_observation_only_venue_not_available)`
- `strength_momentum_observed` count=`1964` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=5(reviewed_rising_missed_nxt_eligibility_not_available)`
- `stat_action_decision_snapshot` count=`1797` routing=`reviewed_unknown_token_provenance` fields=`prior_probe_residual_direction_state=50(reviewed_prior_probe_residual_source_gap), prior_probe_residual_failure_signature=50(reviewed_prior_probe_residual_source_gap), main_lifecycle_venue=24(reviewed_main_lifecycle_venue_not_available), tick_context_stale=15(reviewed_stale_flag_not_available), quote_stale=15(reviewed_stale_flag_not_available), shallow_tick_context_stale=10(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=10(reviewed_shallow_stale_flag_not_available), prior_probe_residual_orderbook_state=5(reviewed_prior_probe_residual_source_gap)`
- `rising_missed_tp1_candidate_deferred` count=`1572` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=250(reviewed_rising_missed_nxt_eligibility_not_available)`
- `exit_signal` count=`1395` routing=`reviewed_unknown_token_provenance` fields=`main_lifecycle_venue=20(reviewed_main_lifecycle_venue_not_available)`
- `blocked_strength_momentum` count=`1380` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=5(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalp_entry_action_decision_snapshot` count=`1376` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=916(reviewed_rising_missed_nxt_eligibility_not_available), holding_exit_matrix_score_prior_band=348(reviewed_score_prior_neutral_unknown_not_decision_input), entry_order_flow_status=91(reviewed_entry_order_flow_not_available), risk_regime_context=88(reviewed_missing_risk_regime_context), score_prior_band=29(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=29(reviewed_score_prior_neutral_unknown_not_decision_input), tier_reason=28(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=28(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scalp_sim_panic_context_warning` count=`1172` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=1172(reviewed_missing_risk_regime_context), market_risk_state=1172(reviewed_missing_risk_regime_context), liquidity_state=1172(reviewed_missing_risk_regime_context), risk_regime_epoch_id=1172(reviewed_missing_risk_regime_context)`
- `scalping_scanner_ws_backoff_watch_retained` count=`1146` routing=`reviewed_unknown_token_provenance` fields=`venue=1(reviewed_scanner_venue_fail_closed_provenance), effective_venue=1(reviewed_scanner_venue_fail_closed_provenance)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `70606`
- `scalping_scanner_fast_precheck`: `54921`
- `scalping_scanner_runtime_queue_lag`: `29517`
- `scalping_scanner_candidate_observed`: `19570`
- `scalping_scanner_real_source_guard_block`: `19570`
- `scalping_scanner_heavy_eval_completion`: `16165`
- `scalping_scanner_heavy_eval_lag`: `15685`
- `scalping_scanner_runtime_target_attach`: `14818`
- `scalping_scanner_watching_runtime_skip`: `13184`
- `rising_missed_nxt_post_block_price_sample`: `10859`
- `rising_missed_watch_not_rising_skipped`: `6789`
- `rising_missed_tp1_counterfactual_submit_safety`: `4028`
- `scalping_scanner_candidate_promoted`: `2576`
- `rising_missed_tp1_candidate_blocked`: `2456`
- `scalping_scanner_watch_eviction`: `2196`
- `bad_entry_refined_candidate`: `2140`
- `strength_momentum_observed`: `1964`
- `stat_action_decision_snapshot`: `1797`
- `risky_micro_episode_executable_bbo_observed`: `1720`
- `scalp_sim_panic_level1_partial_skipped_min_remaining`: `1629`

# Observation Source Quality Audit - 2026-08-14

- status: `pass`
- event_count: `311915`
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
- `scalping_scanner_promotion_latency_trace` count=`77153` routing=`reviewed_unknown_token_provenance` fields=`venue=20(reviewed_scanner_venue_fail_closed_provenance), effective_venue=20(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_fast_precheck` count=`59384` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=1812(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=486(reviewed_scanner_stale_backoff_route_not_available), venue=11(reviewed_scanner_venue_fail_closed_provenance), effective_venue=11(reviewed_scanner_venue_fail_closed_provenance), scanner_promotion_reanchor_effective_venue=11(reviewed_scanner_venue_fail_closed_provenance), scanner_stale_backoff_canonical_effective_venue=11(reviewed_scanner_venue_fail_closed_provenance), rising_missed_submit_safety_backoff_reason=5(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `scalping_scanner_runtime_queue_lag` count=`32150` routing=`reviewed_unknown_token_provenance` fields=`venue=9(reviewed_scanner_venue_fail_closed_provenance), effective_venue=9(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_heavy_eval_completion` count=`18248` routing=`reviewed_unknown_token_provenance` fields=`venue=16(reviewed_scanner_venue_fail_closed_provenance), effective_venue=16(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_heavy_eval_lag` count=`17769` routing=`reviewed_unknown_token_provenance` fields=`venue=9(reviewed_scanner_venue_fail_closed_provenance), effective_venue=9(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_nxt_post_block_price_sample` count=`12640` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_post_block_ws_0d_route=3(reviewed_rising_missed_nxt_post_block_route_not_available), rising_missed_nxt_post_block_ws_0b_route=2(reviewed_rising_missed_nxt_post_block_route_not_available)`
- `scalping_scanner_watching_runtime_skip` count=`11349` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1207(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=25(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=25(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=25(reviewed_explicit_sizing_unknown_venue_fallback), venue=15(reviewed_scanner_venue_fail_closed_provenance), effective_venue=15(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_watch_not_rising_skipped` count=`8438` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=4928(reviewed_rising_missed_nxt_eligibility_not_available), venue=3(reviewed_observation_only_venue_not_available)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`2947` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=914(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=2(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=2(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=2(reviewed_explicit_sizing_unknown_venue_fallback)`
- `strength_momentum_observed` count=`2439` routing=`reviewed_unknown_token_provenance` fields=`venue=15(reviewed_scanner_venue_fail_closed_provenance), effective_venue=15(reviewed_scanner_venue_fail_closed_provenance), rising_missed_nxt_eligible=9(reviewed_rising_missed_nxt_eligibility_not_available)`
- `blocked_strength_momentum` count=`1847` routing=`reviewed_unknown_token_provenance` fields=`venue=7(reviewed_scanner_venue_fail_closed_provenance), effective_venue=7(reviewed_scanner_venue_fail_closed_provenance), rising_missed_nxt_eligible=7(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_candidate_deferred` count=`1667` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=253(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalp_fast_exit_venue_blocked` count=`1334` routing=`reviewed_unknown_token_provenance` fields=`fast_exit_ws_0d_route=219(reviewed_legacy_fast_exit_route_provenance)`
- `rising_missed_tp1_candidate_blocked` count=`1280` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=661(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=2(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=2(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=2(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scalp_entry_action_decision_snapshot` count=`1159` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=658(reviewed_rising_missed_nxt_eligibility_not_available), holding_exit_matrix_score_prior_band=430(reviewed_score_prior_neutral_unknown_not_decision_input), entry_order_flow_status=142(reviewed_entry_order_flow_not_available), risk_regime_context=107(reviewed_missing_risk_regime_context), tier_reason=39(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=39(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=39(reviewed_explicit_sizing_unknown_venue_fallback), score_prior_band=38(reviewed_score_prior_neutral_unknown_not_decision_input)`
- `scalp_sim_panic_context_warning` count=`1072` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=1072(reviewed_missing_risk_regime_context), market_risk_state=1072(reviewed_missing_risk_regime_context), liquidity_state=1072(reviewed_missing_risk_regime_context), risk_regime_epoch_id=1072(reviewed_missing_risk_regime_context)`
- `stat_action_decision_snapshot` count=`828` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=21(reviewed_stale_flag_not_available), quote_stale=21(reviewed_stale_flag_not_available), shallow_tick_context_stale=6(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=6(reviewed_shallow_stale_flag_not_available)`
- `rising_missed_one_share_entry` count=`767` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=694(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback)`
- `reversal_add_blocked_reason` count=`747` routing=`reviewed_unknown_token_provenance` fields=`shallow_tick_context_stale=6(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=6(reviewed_shallow_stale_flag_not_available), tick_context_stale=6(reviewed_stale_flag_not_available), quote_stale=6(reviewed_stale_flag_not_available)`
- `ai_holding_review` count=`712` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=9(reviewed_entry_order_flow_not_available), holding_context_ws_route=3(reviewed_holding_input_preflight_blocked_provenance), holding_context_selected_route_partition=3(reviewed_holding_input_preflight_blocked_provenance), holding_context_blockers=3(reviewed_holding_input_preflight_blocked_provenance)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `77153`
- `scalping_scanner_fast_precheck`: `59384`
- `scalping_scanner_runtime_queue_lag`: `32150`
- `scalping_scanner_runtime_target_attach`: `19292`
- `scalping_scanner_heavy_eval_completion`: `18248`
- `scalping_scanner_heavy_eval_lag`: `17769`
- `rising_missed_nxt_post_block_price_sample`: `12640`
- `scalping_scanner_watching_runtime_skip`: `11349`
- `rising_missed_watch_not_rising_skipped`: `8438`
- `scalping_scanner_candidate_observed`: `5103`
- `scalping_scanner_real_source_guard_block`: `5103`
- `holding_ws_freshness_blocked`: `3802`
- `rising_missed_tp1_counterfactual_submit_safety`: `2947`
- `strength_momentum_observed`: `2439`
- `scalping_scanner_candidate_promoted`: `2319`
- `bad_entry_refined_candidate`: `2092`
- `blocked_strength_momentum`: `1847`
- `scalping_scanner_watch_eviction`: `1768`
- `rising_missed_tp1_candidate_deferred`: `1667`
- `scalp_fast_exit_venue_blocked`: `1334`

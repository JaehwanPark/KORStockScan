# Observation Source Quality Audit - 2026-09-07

- status: `warning`
- event_count: `329378`
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
- `stat_action_decision_snapshot` count=`1529` routing=`source_quality_blocker_or_provenance_backfill` fields=`score_prior_band=104(0.068)`
- `avg_down_route_arbitration_observed` count=`3` routing=`source_quality_blocker_or_provenance_backfill` fields=`runtime_previous_min_buy_pressure=3(1.0), holding_pipeline_stable_block_signature=3(1.0)`

## Reviewed Unknown Token Findings
- `scalping_scanner_fast_precheck` count=`36178` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=727(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=431(reviewed_scanner_stale_backoff_route_not_available), rising_missed_submit_safety_backoff_reason=2(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `scalping_scanner_watching_runtime_skip` count=`12339` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=680(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=25(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=25(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=25(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_nxt_post_block_price_sample` count=`9950` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_post_block_ws_0b_route=10(reviewed_rising_missed_nxt_post_block_route_not_available), rising_missed_nxt_post_block_ws_0d_route=9(reviewed_rising_missed_nxt_post_block_route_not_available)`
- `rising_missed_watch_not_rising_skipped` count=`4606` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=3322(reviewed_rising_missed_nxt_eligibility_not_available), venue=170(reviewed_observation_only_venue_not_available), rising_missed_effective_venue=128(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`2096` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=948(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=7(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=7(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=7(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_entry_turn_pre_anchor_bbo_path` count=`2044` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=265(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=7(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=7(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=7(reviewed_explicit_sizing_unknown_venue_fallback)`
- `strength_momentum_observed` count=`1582` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=3(reviewed_rising_missed_nxt_eligibility_not_available)`
- `stat_action_decision_snapshot` count=`1529` routing=`reviewed_unknown_token_provenance` fields=`prior_probe_residual_direction_state=70(reviewed_prior_probe_residual_source_gap), prior_probe_residual_failure_signature=70(reviewed_prior_probe_residual_source_gap), tick_context_stale=41(reviewed_stale_flag_not_available), quote_stale=41(reviewed_stale_flag_not_available), shallow_tick_context_stale=36(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=36(reviewed_shallow_stale_flag_not_available)`
- `reversal_add_blocked_reason` count=`1519` routing=`reviewed_unknown_token_provenance` fields=`prior_probe_residual_direction_state=68(reviewed_prior_probe_residual_source_gap), prior_probe_residual_failure_signature=68(reviewed_prior_probe_residual_source_gap), shallow_tick_context_stale=38(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=38(reviewed_shallow_stale_flag_not_available), tick_context_stale=38(reviewed_stale_flag_not_available), quote_stale=38(reviewed_stale_flag_not_available)`
- `scalp_sim_panic_context_warning` count=`1340` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=1340(reviewed_missing_risk_regime_context), market_risk_state=1340(reviewed_missing_risk_regime_context), liquidity_state=1340(reviewed_missing_risk_regime_context), risk_regime_epoch_id=1340(reviewed_missing_risk_regime_context)`
- `rising_missed_tp1_candidate_deferred` count=`1316` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=382(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback)`
- `blocked_strength_momentum` count=`1250` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=3(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalp_entry_action_decision_snapshot` count=`1115` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=578(reviewed_rising_missed_nxt_eligibility_not_available), entry_order_flow_status=199(reviewed_entry_order_flow_not_available), score_prior_band=90(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=90(reviewed_score_prior_neutral_unknown_not_decision_input), tier_reason=33(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=33(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=33(reviewed_explicit_sizing_unknown_venue_fallback), entry_score_source=13(reviewed_entry_score_source_not_available)`
- `ai_holding_review` count=`786` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=11(reviewed_entry_order_flow_not_available), holding_context_blockers=1(reviewed_holding_input_preflight_blocked_provenance)`
- `rising_missed_tp1_candidate_blocked` count=`780` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=566(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=2(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=2(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=2(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_one_share_entry` count=`607` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=494(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=9(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=9(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=9(reviewed_explicit_sizing_unknown_venue_fallback)`
- `budget_pass` count=`553` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=440(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=29(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=29(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=29(reviewed_explicit_sizing_unknown_venue_fallback)`
- `orderbook_stability_observed` count=`553` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=440(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=29(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=29(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=29(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scale_in_feature_context_refresh` count=`476` routing=`reviewed_unknown_token_provenance` fields=`prior_probe_residual_direction_state=76(reviewed_prior_probe_residual_source_gap), prior_probe_residual_failure_signature=76(reviewed_prior_probe_residual_source_gap)`
- `prev_close_gainer_entry_ai_handoff` count=`442` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=272(reviewed_rising_missed_nxt_eligibility_not_available), venue=14(reviewed_observation_only_venue_not_available), rising_missed_effective_venue=14(reviewed_rising_missed_nxt_eligibility_not_available)`

## Top Stages
- `scalping_scanner_candidate_pruned`: `66550`
- `scalping_scanner_prune_bbo_schedule`: `58096`
- `scalping_scanner_promotion_latency_trace`: `46425`
- `scalping_scanner_fast_precheck`: `36178`
- `scalping_scanner_runtime_queue_lag`: `21396`
- `scalping_scanner_watching_runtime_skip`: `12339`
- `scalping_scanner_heavy_eval_completion`: `10446`
- `scalping_scanner_heavy_eval_lag`: `10247`
- `rising_missed_nxt_post_block_price_sample`: `9950`
- `risky_micro_episode_executable_bbo_observed`: `6017`
- `rising_missed_watch_not_rising_skipped`: `4606`
- `avg_down_exit_replay_frame_observed`: `2848`
- `bad_entry_refined_candidate`: `2670`
- `scalping_scanner_prune_bbo_observation`: `2500`
- `scalping_scanner_runtime_target_attach`: `2424`
- `scalping_scanner_candidate_promoted`: `2284`
- `rising_missed_tp1_counterfactual_submit_safety`: `2096`
- `scalping_scanner_watch_eviction`: `2056`
- `rising_missed_entry_turn_pre_anchor_bbo_path`: `2044`
- `scalp_sim_panic_scale_in_blocked`: `1611`

# Observation Source Quality Audit - 2026-09-09

- status: `warning`
- event_count: `507521`
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
- `stat_action_decision_snapshot` count=`2126` routing=`source_quality_blocker_or_provenance_backfill` fields=`score_prior_band=449(0.2112)`
- `scalping_scanner_source_fetch_census` count=`2010` routing=`source_quality_blocker_or_provenance_backfill` fields=`scanner_source_rows_json=1809(0.9), venue=10(0.005), effective_venue=10(0.005)`
- `ai_holding_review` count=`899` routing=`source_quality_blocker_or_provenance_backfill` fields=`holding_score_model_reason=1(0.0011)`
- `scalping_scanner_candidate_pool_census` count=`200` routing=`source_quality_blocker_or_provenance_backfill` fields=`scanner_source_rows_json=200(1.0)`

## Reviewed Unknown Token Findings
- `scalping_scanner_promotion_latency_trace` count=`91557` routing=`reviewed_unknown_token_provenance` fields=`venue=105(reviewed_scanner_venue_fail_closed_provenance), effective_venue=105(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_fast_precheck` count=`69052` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=635(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=364(reviewed_scanner_stale_backoff_route_not_available), venue=91(reviewed_scanner_venue_fail_closed_provenance), effective_venue=91(reviewed_scanner_venue_fail_closed_provenance), scanner_promotion_reanchor_effective_venue=91(reviewed_scanner_venue_fail_closed_provenance), scanner_stale_backoff_canonical_effective_venue=91(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_runtime_queue_lag` count=`38669` routing=`reviewed_unknown_token_provenance` fields=`venue=51(reviewed_scanner_venue_fail_closed_provenance), effective_venue=51(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_heavy_eval_completion` count=`22839` routing=`reviewed_unknown_token_provenance` fields=`venue=16(reviewed_scanner_venue_fail_closed_provenance), effective_venue=16(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_heavy_eval_lag` count=`22505` routing=`reviewed_unknown_token_provenance` fields=`venue=14(reviewed_scanner_venue_fail_closed_provenance), effective_venue=14(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_watch_not_rising_skipped` count=`12956` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=9682(reviewed_rising_missed_nxt_eligibility_not_available), venue=333(reviewed_observation_only_venue_not_available), rising_missed_effective_venue=333(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalping_scanner_watching_runtime_skip` count=`12615` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1407(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=75(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=75(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=75(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_effective_venue=45(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalp_sim_panic_context_warning` count=`4300` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=4300(reviewed_missing_risk_regime_context), market_risk_state=4300(reviewed_missing_risk_regime_context), liquidity_state=4300(reviewed_missing_risk_regime_context), risk_regime_epoch_id=4300(reviewed_missing_risk_regime_context)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`2892` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1244(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=44(reviewed_rising_missed_nxt_eligibility_not_available), venue=13(reviewed_rising_missed_explicit_venue_conflict), effective_venue=13(reviewed_rising_missed_explicit_venue_conflict), tier_reason=6(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=6(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=6(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_entry_turn_pre_anchor_bbo_path` count=`2782` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=335(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=44(reviewed_rising_missed_nxt_eligibility_not_available), venue=13(reviewed_rising_missed_explicit_venue_conflict), effective_venue=13(reviewed_rising_missed_explicit_venue_conflict), tier_reason=6(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=6(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=6(reviewed_explicit_sizing_unknown_venue_fallback)`
- `stat_action_decision_snapshot` count=`2126` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=88(reviewed_stale_flag_not_available), quote_stale=88(reviewed_stale_flag_not_available), shallow_tick_context_stale=75(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=75(reviewed_shallow_stale_flag_not_available)`
- `strength_momentum_observed` count=`2115` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=38(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_candidate_deferred` count=`1799` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=440(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=31(reviewed_rising_missed_nxt_eligibility_not_available), venue=10(reviewed_rising_missed_explicit_venue_conflict), effective_venue=10(reviewed_rising_missed_explicit_venue_conflict)`
- `reversal_add_blocked_reason` count=`1717` routing=`reviewed_unknown_token_provenance` fields=`shallow_tick_context_stale=82(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=82(reviewed_shallow_stale_flag_not_available), tick_context_stale=82(reviewed_stale_flag_not_available), quote_stale=82(reviewed_stale_flag_not_available)`
- `blocked_strength_momentum` count=`1695` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=31(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalp_entry_action_decision_snapshot` count=`1460` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=834(reviewed_rising_missed_nxt_eligibility_not_available), score_prior_band=117(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=117(reviewed_score_prior_neutral_unknown_not_decision_input), entry_order_flow_status=77(reviewed_entry_order_flow_not_available), entry_score_source=63(reviewed_entry_score_source_not_available), entry_recheck_excluded_reason=63(reviewed_entry_score_source_not_available), entry_score_excluded_reason=63(reviewed_entry_score_source_not_available), tier_reason=27(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_tp1_candidate_blocked` count=`1093` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=804(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=13(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=6(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=6(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=6(reviewed_explicit_sizing_unknown_venue_fallback), venue=3(reviewed_rising_missed_explicit_venue_conflict), effective_venue=3(reviewed_rising_missed_explicit_venue_conflict)`
- `ai_holding_review` count=`899` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=1(reviewed_entry_order_flow_not_available)`
- `entry_submit_attempt_finished` count=`809` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=741(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=29(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=29(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=29(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_effective_venue=17(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_one_share_entry` count=`809` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=741(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=17(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=4(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=4(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=4(reviewed_explicit_sizing_unknown_venue_fallback), venue=3(reviewed_rising_missed_explicit_venue_conflict), effective_venue=3(reviewed_rising_missed_explicit_venue_conflict)`

## Top Stages
- `scalping_scanner_candidate_pruned`: `92126`
- `scalping_scanner_promotion_latency_trace`: `91557`
- `scalping_scanner_fast_precheck`: `69052`
- `scalping_scanner_prune_bbo_schedule`: `59278`
- `scalping_scanner_runtime_queue_lag`: `38669`
- `scalping_scanner_heavy_eval_completion`: `22839`
- `scalping_scanner_heavy_eval_lag`: `22505`
- `rising_missed_watch_not_rising_skipped`: `12956`
- `scalping_scanner_watching_runtime_skip`: `12615`
- `rising_missed_nxt_post_block_price_sample`: `8430`
- `risky_micro_episode_executable_bbo_observed`: `7685`
- `scalping_scanner_candidate_observed`: `5575`
- `scalping_scanner_real_source_guard_block`: `5575`
- `scalp_sim_panic_context_warning`: `4300`
- `bad_entry_refined_candidate`: `3928`
- `rising_missed_tp1_counterfactual_submit_safety`: `2892`
- `rising_missed_entry_turn_pre_anchor_bbo_path`: `2782`
- `scalping_scanner_prune_bbo_observation`: `2587`
- `scalping_scanner_runtime_target_attach`: `2566`
- `scalping_scanner_candidate_promoted`: `2317`

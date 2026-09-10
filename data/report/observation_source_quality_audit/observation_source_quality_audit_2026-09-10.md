# Observation Source Quality Audit - 2026-09-10

- status: `warning`
- event_count: `385928`
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
- `avg_down_exit_replay_frame_observed` count=`14586` routing=`source_quality_blocker_or_provenance_backfill` fields=`market=1(0.0001)`
- `scalping_scanner_source_fetch_census` count=`2840` routing=`source_quality_blocker_or_provenance_backfill` fields=`scanner_source_rows_json=2553(0.8989), venue=10(0.0035), effective_venue=10(0.0035)`
- `stat_action_decision_snapshot` count=`384` routing=`source_quality_blocker_or_provenance_backfill` fields=`score_prior_band=19(0.0495)`
- `scalping_scanner_candidate_pool_census` count=`281` routing=`source_quality_blocker_or_provenance_backfill` fields=`scanner_source_rows_json=281(1.0)`

## Reviewed Unknown Token Findings
- `scalping_scanner_fast_precheck` count=`40915` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=814(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=533(reviewed_scanner_stale_backoff_route_not_available), rising_missed_submit_safety_backoff_reason=1(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `scalping_scanner_watching_runtime_skip` count=`13959` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1267(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=49(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=49(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=49(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_effective_venue=38(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_nxt_post_block_price_sample` count=`8503` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_post_block_ws_0b_route=193(reviewed_rising_missed_nxt_post_block_route_not_available), rising_missed_nxt_post_block_ws_0d_route=163(reviewed_rising_missed_nxt_post_block_route_not_available)`
- `rising_missed_watch_not_rising_skipped` count=`5274` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=3276(reviewed_rising_missed_nxt_eligibility_not_available), venue=182(reviewed_observation_only_venue_not_available), rising_missed_effective_venue=182(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`2705` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1316(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=90(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=15(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=15(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=15(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_entry_turn_pre_anchor_bbo_path` count=`2607` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=357(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=90(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=15(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=15(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=15(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_tp1_candidate_deferred` count=`1644` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=425(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=53(reviewed_rising_missed_nxt_eligibility_not_available)`
- `strength_momentum_observed` count=`1453` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=7(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalp_entry_action_decision_snapshot` count=`1314` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=871(reviewed_rising_missed_nxt_eligibility_not_available), entry_order_flow_status=79(reviewed_entry_order_flow_not_available), score_prior_band=68(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=68(reviewed_score_prior_neutral_unknown_not_decision_input), tier_reason=38(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=38(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=38(reviewed_explicit_sizing_unknown_venue_fallback), block_reason=24(reviewed_entry_block_source_quality_unknown_provenance)`
- `blocked_strength_momentum` count=`1074` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=7(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_candidate_blocked` count=`1061` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=891(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=37(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=15(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=15(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=15(reviewed_explicit_sizing_unknown_venue_fallback)`
- `ai_holding_review` count=`827` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=13(reviewed_entry_order_flow_not_available)`
- `entry_submit_attempt_finished` count=`799` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=714(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=39(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=39(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=39(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_effective_venue=10(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_one_share_entry` count=`794` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=715(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=10(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=8(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=8(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=8(reviewed_explicit_sizing_unknown_venue_fallback)`
- `sell_completed` count=`789` routing=`reviewed_unknown_token_provenance` fields=`broker_actual_execution_venue=789(reviewed_broker_actual_venue_not_available)`
- `budget_pass` count=`684` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=607(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=32(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=32(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=32(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_effective_venue=10(reviewed_rising_missed_nxt_eligibility_not_available)`
- `orderbook_stability_observed` count=`684` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=607(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=32(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=32(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=32(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_effective_venue=10(reviewed_rising_missed_nxt_eligibility_not_available)`
- `prev_close_gainer_entry_ai_handoff` count=`521` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=317(reviewed_rising_missed_nxt_eligibility_not_available), venue=27(reviewed_observation_only_venue_not_available), rising_missed_effective_venue=27(reviewed_rising_missed_nxt_eligibility_not_available)`
- `opening_rotation_krx_regular_scope_skipped` count=`460` routing=`reviewed_unknown_token_provenance` fields=`forbidden_uses=460(reviewed_forbidden_uses_unknown_literal_not_source_value)`
- `risky_micro_episode_source_candidate_observed` count=`434` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=373(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=29(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=29(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=29(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_effective_venue=6(reviewed_rising_missed_nxt_eligibility_not_available)`

## Top Stages
- `scalping_scanner_candidate_pruned`: `83846`
- `scalping_scanner_prune_bbo_schedule`: `64204`
- `scalping_scanner_promotion_latency_trace`: `52548`
- `scalping_scanner_fast_precheck`: `40915`
- `scalping_scanner_runtime_queue_lag`: `24085`
- `avg_down_exit_replay_frame_observed`: `14586`
- `scalping_scanner_watching_runtime_skip`: `13959`
- `scalping_scanner_heavy_eval_completion`: `11880`
- `scalping_scanner_heavy_eval_lag`: `11633`
- `rising_missed_nxt_post_block_price_sample`: `8503`
- `rising_missed_watch_not_rising_skipped`: `5274`
- `risky_micro_episode_executable_bbo_observed`: `5101`
- `scalping_scanner_source_fetch_census`: `2840`
- `rising_missed_tp1_counterfactual_submit_safety`: `2705`
- `scalping_scanner_runtime_target_attach`: `2697`
- `scalping_scanner_prune_bbo_observation`: `2616`
- `rising_missed_entry_turn_pre_anchor_bbo_path`: `2607`
- `scalping_scanner_candidate_promoted`: `2558`
- `scalping_scanner_watch_eviction`: `2259`
- `scalping_scanner_candidate_observed`: `2157`

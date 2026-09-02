# Observation Source Quality Audit - 2026-09-02

- status: `pass`
- event_count: `138774`
- tuning_input_policy: `exclude_defective_rows_not_full_day_raw`
- hard_blocking_excluded_row_count: `0`
- pre_exclusion_hard_blocking_excluded_row_count: `None`
- current_scan_hard_blocking_excluded_row_count: `None`
- post_exclusion_hard_blocking_excluded_row_count: `None`
- raw_row_exclusion_applied: `False`
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
- `scalping_scanner_fast_precheck` count=`17169` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=593(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=357(reviewed_scanner_stale_backoff_route_not_available)`
- `scalping_scanner_watching_runtime_skip` count=`4596` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=570(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=40(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=40(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=40(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_watch_not_rising_skipped` count=`2613` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=2613(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalp_entry_action_decision_snapshot` count=`828` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=668(reviewed_rising_missed_nxt_eligibility_not_available), holding_exit_matrix_score_prior_band=236(reviewed_score_prior_neutral_unknown_not_decision_input), entry_order_flow_status=93(reviewed_entry_order_flow_not_available), tier_reason=64(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=64(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=64(reviewed_explicit_sizing_unknown_venue_fallback), score_prior_band=25(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=25(reviewed_score_prior_neutral_unknown_not_decision_input)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`557` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=557(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=11(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=11(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=11(reviewed_explicit_sizing_unknown_venue_fallback), venue=1(reviewed_rising_missed_explicit_venue_conflict), effective_venue=1(reviewed_rising_missed_explicit_venue_conflict)`
- `rising_missed_one_share_entry` count=`539` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=539(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=13(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=13(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=13(reviewed_explicit_sizing_unknown_venue_fallback)`
- `budget_pass` count=`489` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=488(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=41(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=41(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=41(reviewed_explicit_sizing_unknown_venue_fallback)`
- `orderbook_stability_observed` count=`489` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=488(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=41(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=41(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=41(reviewed_explicit_sizing_unknown_venue_fallback)`
- `strength_momentum_observed` count=`438` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=6(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_candidate_blocked` count=`430` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=430(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=10(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=10(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=10(reviewed_explicit_sizing_unknown_venue_fallback), venue=1(reviewed_rising_missed_explicit_venue_conflict), effective_venue=1(reviewed_rising_missed_explicit_venue_conflict)`
- `risky_micro_episode_source_candidate_observed` count=`331` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=331(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=28(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=28(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=28(reviewed_explicit_sizing_unknown_venue_fallback)`
- `blocked_strength_momentum` count=`310` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=6(reviewed_rising_missed_nxt_eligibility_not_available)`
- `latency_block` count=`237` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=236(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=9(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=9(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=9(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_adverse_micro_recovery_checkpoint` count=`231` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_adverse_micro_recovery_ws_0b_raw_route=12(reviewed_adverse_micro_recovery_route_not_available)`
- `entry_ai_price_canary_applied` count=`207` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=200(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=30(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=30(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=30(reviewed_explicit_sizing_unknown_venue_fallback), entry_order_flow_status=29(reviewed_entry_order_flow_not_available)`
- `ai_confirmed` count=`195` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=96(reviewed_rising_missed_nxt_eligibility_not_available), entry_order_flow_status=30(reviewed_entry_order_flow_not_available), tier_reason=11(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=11(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=11(reviewed_explicit_sizing_unknown_venue_fallback)`
- `prev_close_gainer_entry_ai_handoff` count=`189` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=158(reviewed_rising_missed_nxt_eligibility_not_available)`
- `reversal_add_blocked_reason` count=`184` routing=`reviewed_unknown_token_provenance` fields=`shallow_tick_context_stale=28(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=28(reviewed_shallow_stale_flag_not_available), tick_context_stale=28(reviewed_stale_flag_not_available), quote_stale=28(reviewed_stale_flag_not_available)`
- `stat_action_decision_snapshot` count=`183` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=27(reviewed_stale_flag_not_available), quote_stale=27(reviewed_stale_flag_not_available), shallow_tick_context_stale=27(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=27(reviewed_shallow_stale_flag_not_available)`
- `blocked_overbought` count=`182` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=7(reviewed_rising_missed_nxt_eligibility_not_available)`

## Top Stages
- `scalping_scanner_candidate_pruned`: `41947`
- `scalping_scanner_promotion_latency_trace`: `22395`
- `scalping_scanner_fast_precheck`: `17169`
- `scalping_scanner_runtime_queue_lag`: `10352`
- `risky_micro_episode_executable_bbo_observed`: `6681`
- `scalping_scanner_heavy_eval_completion`: `5335`
- `scalping_scanner_heavy_eval_lag`: `5226`
- `scalping_scanner_watching_runtime_skip`: `4596`
- `scalping_scanner_candidate_observed`: `4130`
- `scalping_scanner_real_source_guard_block`: `4130`
- `rising_missed_watch_not_rising_skipped`: `2613`
- `scalping_scanner_runtime_target_attach`: `1390`
- `scalping_scanner_candidate_promoted`: `1253`
- `scalping_scanner_watch_eviction`: `1163`
- `scalp_entry_action_decision_snapshot`: `828`
- `scalping_scanner_ws_backoff_watch_retained`: `607`
- `rising_missed_tp1_counterfactual_submit_safety`: `557`
- `rising_missed_one_share_entry`: `539`
- `budget_pass`: `489`
- `orderbook_stability_observed`: `489`

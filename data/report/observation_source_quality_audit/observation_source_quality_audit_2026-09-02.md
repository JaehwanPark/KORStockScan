# Observation Source Quality Audit - 2026-09-02

- status: `pass`
- event_count: `79922`
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
- `scalping_scanner_fast_precheck` count=`9063` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=377(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=270(reviewed_scanner_stale_backoff_route_not_available)`
- `scalping_scanner_watching_runtime_skip` count=`2923` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=306(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=40(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=40(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=40(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_watch_not_rising_skipped` count=`1223` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1223(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalp_entry_action_decision_snapshot` count=`421` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=328(reviewed_rising_missed_nxt_eligibility_not_available), holding_exit_matrix_score_prior_band=119(reviewed_score_prior_neutral_unknown_not_decision_input), entry_order_flow_status=74(reviewed_entry_order_flow_not_available), tier_reason=64(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=64(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=64(reviewed_explicit_sizing_unknown_venue_fallback), score_prior_band=18(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=18(reviewed_score_prior_neutral_unknown_not_decision_input)`
- `rising_missed_one_share_entry` count=`279` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=279(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=13(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=13(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=13(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`262` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=262(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=11(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=11(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=11(reviewed_explicit_sizing_unknown_venue_fallback), venue=1(reviewed_rising_missed_explicit_venue_conflict), effective_venue=1(reviewed_rising_missed_explicit_venue_conflict)`
- `budget_pass` count=`247` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=246(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=41(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=41(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=41(reviewed_explicit_sizing_unknown_venue_fallback)`
- `orderbook_stability_observed` count=`247` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=246(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=41(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=41(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=41(reviewed_explicit_sizing_unknown_venue_fallback)`
- `strength_momentum_observed` count=`220` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_candidate_blocked` count=`203` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=203(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=10(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=10(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=10(reviewed_explicit_sizing_unknown_venue_fallback), venue=1(reviewed_rising_missed_explicit_venue_conflict), effective_venue=1(reviewed_rising_missed_explicit_venue_conflict)`
- `risky_micro_episode_source_candidate_observed` count=`183` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=183(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=28(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=28(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=28(reviewed_explicit_sizing_unknown_venue_fallback)`
- `blocked_strength_momentum` count=`160` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1(reviewed_rising_missed_nxt_eligibility_not_available)`
- `reversal_add_blocked_reason` count=`129` routing=`reviewed_unknown_token_provenance` fields=`shallow_tick_context_stale=13(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=13(reviewed_shallow_stale_flag_not_available), tick_context_stale=13(reviewed_stale_flag_not_available), quote_stale=13(reviewed_stale_flag_not_available)`
- `latency_block` count=`128` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=127(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=9(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=9(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=9(reviewed_explicit_sizing_unknown_venue_fallback)`
- `stat_action_decision_snapshot` count=`121` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=12(reviewed_stale_flag_not_available), quote_stale=12(reviewed_stale_flag_not_available), shallow_tick_context_stale=12(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=12(reviewed_shallow_stale_flag_not_available)`
- `ai_holding_review` count=`114` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=26(reviewed_entry_order_flow_not_available)`
- `entry_ai_price_canary_applied` count=`104` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=100(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=30(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=30(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=30(reviewed_explicit_sizing_unknown_venue_fallback), entry_order_flow_status=23(reviewed_entry_order_flow_not_available)`
- `ai_confirmed` count=`99` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=41(reviewed_rising_missed_nxt_eligibility_not_available), entry_order_flow_status=23(reviewed_entry_order_flow_not_available), tier_reason=11(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=11(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=11(reviewed_explicit_sizing_unknown_venue_fallback)`
- `prev_close_gainer_entry_ai_handoff` count=`97` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=82(reviewed_rising_missed_nxt_eligibility_not_available)`
- `blocked_overbought` count=`70` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1(reviewed_rising_missed_nxt_eligibility_not_available)`

## Top Stages
- `scalping_scanner_candidate_pruned`: `25627`
- `scalping_scanner_promotion_latency_trace`: `11647`
- `scalping_scanner_fast_precheck`: `9063`
- `scalping_scanner_runtime_queue_lag`: `5626`
- `scalping_scanner_candidate_observed`: `3678`
- `scalping_scanner_real_source_guard_block`: `3678`
- `risky_micro_episode_executable_bbo_observed`: `3178`
- `scalping_scanner_watching_runtime_skip`: `2923`
- `scalping_scanner_heavy_eval_completion`: `2627`
- `scalping_scanner_heavy_eval_lag`: `2584`
- `rising_missed_watch_not_rising_skipped`: `1223`
- `scalping_scanner_runtime_target_attach`: `938`
- `scalping_scanner_candidate_promoted`: `802`
- `scalping_scanner_watch_eviction`: `731`
- `scalp_entry_action_decision_snapshot`: `421`
- `scalping_scanner_ws_backoff_watch_retained`: `408`
- `rising_missed_one_share_entry`: `279`
- `rising_missed_tp1_counterfactual_submit_safety`: `262`
- `bad_entry_refined_candidate`: `249`
- `budget_pass`: `247`

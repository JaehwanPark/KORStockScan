# Observation Source Quality Audit - 2026-08-21

- status: `pass`
- event_count: `23949`
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
- `scalping_scanner_fast_precheck` count=`5893` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0d_route=10(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0b_route=9(reviewed_scanner_stale_backoff_route_not_available)`
- `rising_missed_watch_not_rising_skipped` count=`1290` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1290(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalping_scanner_watching_runtime_skip` count=`632` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=51(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=51(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=51(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=51(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_one_share_entry` count=`28` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=28(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=2(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=2(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=2(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scalp_entry_action_decision_snapshot` count=`28` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=28(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=28(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=28(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=28(reviewed_explicit_sizing_unknown_venue_fallback), holding_exit_matrix_score_prior_band=4(reviewed_score_prior_neutral_unknown_not_decision_input), risk_regime_context=4(reviewed_missing_risk_regime_context)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`24` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=24(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=4(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=4(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=4(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_tp1_candidate_blocked` count=`22` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=22(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=4(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=4(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=4(reviewed_explicit_sizing_unknown_venue_fallback)`
- `budget_pass` count=`19` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=19(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=19(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=19(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=19(reviewed_explicit_sizing_unknown_venue_fallback)`
- `orderbook_stability_observed` count=`19` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=19(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=19(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=19(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=19(reviewed_explicit_sizing_unknown_venue_fallback)`
- `risky_micro_episode_source_candidate_observed` count=`14` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=14(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=14(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=14(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=14(reviewed_explicit_sizing_unknown_venue_fallback)`
- `entry_ai_price_canary_applied` count=`10` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=10(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=10(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=10(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=10(reviewed_explicit_sizing_unknown_venue_fallback)`
- `blocked_zero_qty` count=`9` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=9(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=9(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=9(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=9(reviewed_explicit_sizing_unknown_venue_fallback)`
- `latency_block` count=`9` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=9(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=9(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=9(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=9(reviewed_explicit_sizing_unknown_venue_fallback)`
- `ai_confirmed` count=`5` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=5(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback)`
- `latency_pass` count=`5` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=5(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback)`
- `pre_submit_entry_ai_authority_guard_block` count=`5` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=5(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_scout_allocator_order_plan` count=`5` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=5(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_tick_speed_entry_block` count=`5` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=5(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=5(reviewed_explicit_sizing_unknown_venue_fallback), entry_order_flow_status=2(reviewed_entry_order_flow_not_available)`
- `rising_missed_reversal_up_volatile_recheck_enqueued` count=`3` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=3(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=3(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=3(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=3(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_tp1_candidate_deferred` count=`2` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=2(reviewed_rising_missed_nxt_eligibility_not_available)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `7795`
- `scalping_scanner_fast_precheck`: `5893`
- `scalping_scanner_runtime_queue_lag`: `3129`
- `scalping_scanner_heavy_eval_lag`: `1902`
- `scalping_scanner_heavy_eval_completion`: `1902`
- `rising_missed_watch_not_rising_skipped`: `1290`
- `scalping_scanner_runtime_target_attach`: `835`
- `scalping_scanner_watching_runtime_skip`: `632`
- `scalping_scanner_candidate_promoted`: `74`
- `scalping_scanner_candidate_observed`: `58`
- `scalping_scanner_real_source_guard_block`: `58`
- `scalping_scanner_watch_eviction`: `47`
- `scalping_scanner_ws_backoff_watch_retained`: `36`
- `risky_micro_episode_executable_bbo_observed`: `34`
- `rising_missed_one_share_entry`: `28`
- `scalp_entry_action_decision_snapshot`: `28`
- `rising_missed_tp1_counterfactual_submit_safety`: `24`
- `scalping_scanner_low_rebound_source_observed`: `22`
- `rising_missed_tp1_candidate_blocked`: `22`
- `budget_pass`: `19`

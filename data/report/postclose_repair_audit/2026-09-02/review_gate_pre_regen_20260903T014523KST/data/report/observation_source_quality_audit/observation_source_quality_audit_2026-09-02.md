# Observation Source Quality Audit - 2026-09-02

- status: `pass`
- event_count: `383195`
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
- `scalping_scanner_fast_precheck` count=`42259` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=1351(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=751(reviewed_scanner_stale_backoff_route_not_available)`
- `scalping_scanner_watching_runtime_skip` count=`12090` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=877(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=40(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=40(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=40(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_effective_venue=11(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_nxt_post_block_price_sample` count=`10767` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_post_block_selector_reason=71(reviewed_nxt_post_block_source_gap_provenance), rising_missed_nxt_post_block_source_block_reason=71(reviewed_nxt_post_block_source_gap_provenance), rising_missed_nxt_post_block_ws_0b_route=2(reviewed_rising_missed_nxt_post_block_route_not_available)`
- `rising_missed_watch_not_rising_skipped` count=`4278` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=3964(reviewed_rising_missed_nxt_eligibility_not_available), venue=10(reviewed_observation_only_venue_not_available), rising_missed_effective_venue=10(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`2512` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=877(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=11(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=11(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=11(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_effective_venue=7(reviewed_rising_missed_nxt_eligibility_not_available), venue=1(reviewed_rising_missed_explicit_venue_conflict), effective_venue=1(reviewed_rising_missed_explicit_venue_conflict)`
- `scalp_entry_action_decision_snapshot` count=`1539` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1054(reviewed_rising_missed_nxt_eligibility_not_available), holding_exit_matrix_score_prior_band=465(reviewed_score_prior_neutral_unknown_not_decision_input), entry_order_flow_status=144(reviewed_entry_order_flow_not_available), risk_regime_context=109(reviewed_missing_risk_regime_context), tier_reason=64(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=64(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=64(reviewed_explicit_sizing_unknown_venue_fallback), score_prior_band=49(reviewed_score_prior_neutral_unknown_not_decision_input)`
- `rising_missed_tp1_candidate_deferred` count=`1472` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=191(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=5(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=1(reviewed_explicit_sizing_unknown_venue_fallback)`
- `strength_momentum_observed` count=`1386` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=10(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_candidate_blocked` count=`1040` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=686(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=10(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=10(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=10(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_effective_venue=2(reviewed_rising_missed_nxt_eligibility_not_available), venue=1(reviewed_rising_missed_explicit_venue_conflict), effective_venue=1(reviewed_rising_missed_explicit_venue_conflict)`
- `blocked_strength_momentum` count=`1004` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=8(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_one_share_entry` count=`972` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=851(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=17(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=13(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=13(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=13(reviewed_explicit_sizing_unknown_venue_fallback)`
- `budget_pass` count=`882` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=773(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=41(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=41(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=41(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_effective_venue=17(reviewed_rising_missed_nxt_eligibility_not_available)`
- `orderbook_stability_observed` count=`882` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=773(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=41(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=41(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=41(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_effective_venue=17(reviewed_rising_missed_nxt_eligibility_not_available)`
- `reversal_add_blocked_reason` count=`663` routing=`reviewed_unknown_token_provenance` fields=`shallow_tick_context_stale=45(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=45(reviewed_shallow_stale_flag_not_available), tick_context_stale=45(reviewed_stale_flag_not_available), quote_stale=45(reviewed_stale_flag_not_available)`
- `stat_action_decision_snapshot` count=`638` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=45(reviewed_stale_flag_not_available), quote_stale=45(reviewed_stale_flag_not_available), shallow_tick_context_stale=44(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=44(reviewed_shallow_stale_flag_not_available)`
- `risky_micro_episode_source_candidate_observed` count=`575` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=514(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=28(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=28(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=28(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_effective_venue=15(reviewed_rising_missed_nxt_eligibility_not_available)`
- `prev_close_gainer_entry_ai_handoff` count=`472` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=252(reviewed_rising_missed_nxt_eligibility_not_available), venue=6(reviewed_observation_only_venue_not_available), rising_missed_effective_venue=6(reviewed_rising_missed_nxt_eligibility_not_available)`
- `ai_holding_review` count=`458` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=29(reviewed_entry_order_flow_not_available)`
- `opening_rotation_krx_regular_scope_skipped` count=`412` routing=`reviewed_unknown_token_provenance` fields=`forbidden_uses=412(reviewed_forbidden_uses_unknown_literal_not_source_value)`
- `latency_block` count=`410` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=385(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=15(reviewed_rising_missed_nxt_eligibility_not_available), latency_true_ofi_nxt_probability_band_effective_venue=15(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=9(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=9(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=9(reviewed_explicit_sizing_unknown_venue_fallback)`

## Top Stages
- `scalping_scanner_candidate_pruned`: `99637`
- `scalping_scanner_promotion_latency_trace`: `53594`
- `scalping_scanner_fast_precheck`: `42259`
- `scalping_scanner_candidate_observed`: `33196`
- `scalping_scanner_real_source_guard_block`: `33196`
- `scalping_scanner_runtime_queue_lag`: `24327`
- `scalping_scanner_watching_runtime_skip`: `12090`
- `scalping_scanner_heavy_eval_completion`: `11673`
- `scalping_scanner_heavy_eval_lag`: `11335`
- `rising_missed_nxt_post_block_price_sample`: `10767`
- `risky_micro_episode_executable_bbo_observed`: `10605`
- `rising_missed_watch_not_rising_skipped`: `4278`
- `scalping_scanner_runtime_target_attach`: `2727`
- `scalping_scanner_candidate_promoted`: `2557`
- `rising_missed_tp1_counterfactual_submit_safety`: `2512`
- `scalping_scanner_watch_eviction`: `2340`
- `scalp_entry_action_decision_snapshot`: `1539`
- `scalping_scanner_ws_backoff_watch_retained`: `1474`
- `rising_missed_tp1_candidate_deferred`: `1472`
- `strength_momentum_observed`: `1386`

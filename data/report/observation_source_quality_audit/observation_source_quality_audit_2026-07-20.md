# Observation Source Quality Audit - 2026-07-20

- status: `pass`
- event_count: `166830`
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
- `scalping_scanner_fast_precheck` count=`7927` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_submit_safety_backoff_reason=26(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `scalping_scanner_watching_runtime_skip` count=`7037` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=202(reviewed_rising_missed_nxt_eligibility_not_available)`
- `ai_holding_review` count=`956` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=220(reviewed_entry_order_flow_not_available)`
- `stat_action_decision_snapshot` count=`948` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=4(reviewed_stale_flag_not_available), quote_stale=4(reviewed_stale_flag_not_available), shallow_tick_context_stale=1(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=1(reviewed_shallow_stale_flag_not_available)`
- `budget_pass` count=`274` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=263(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_one_share_entry` count=`274` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=263(reviewed_rising_missed_nxt_eligibility_not_available)`
- `orderbook_stability_observed` count=`273` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=262(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`256` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=249(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_candidate_blocked` count=`231` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=227(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_nxt_post_block_price_sample` count=`181` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_post_block_ws_0b_route=1(reviewed_rising_missed_nxt_post_block_route_not_available), rising_missed_nxt_post_block_ws_0d_route=1(reviewed_rising_missed_nxt_post_block_route_not_available)`
- `scalp_entry_action_decision_snapshot` count=`155` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=144(reviewed_rising_missed_nxt_eligibility_not_available), entry_order_flow_status=76(reviewed_entry_order_flow_not_available), holding_exit_matrix_score_prior_band=37(reviewed_score_prior_neutral_unknown_not_decision_input), risk_regime_context=6(reviewed_missing_risk_regime_context), score_prior_band=4(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=4(reviewed_score_prior_neutral_unknown_not_decision_input), block_reason=4(reviewed_entry_block_source_quality_unknown_provenance), entry_action_final_block_reason=4(reviewed_entry_block_source_quality_unknown_provenance)`
- `entry_ai_price_canary_applied` count=`120` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=112(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_one_share_entry_blocked` count=`63` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=2(reviewed_rising_missed_nxt_eligibility_not_available)`
- `real_weak_ai_micro_entry_block` count=`54` routing=`reviewed_unknown_token_provenance` fields=`reason=54(reviewed_entry_block_source_quality_unknown_provenance), block_reason=54(reviewed_entry_block_source_quality_unknown_provenance), rising_missed_submit_safety_backoff_reason=54(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance), rising_missed_nxt_eligible=51(reviewed_rising_missed_nxt_eligibility_not_available)`
- `order_leg_request` count=`40` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=37(reviewed_rising_missed_nxt_eligibility_not_available), risk_regime_context=3(reviewed_missing_risk_regime_context)`
- `order_leg_sent` count=`40` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=37(reviewed_rising_missed_nxt_eligibility_not_available)`
- `ai_confirmed` count=`35` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=30(reviewed_rising_missed_nxt_eligibility_not_available), entry_order_flow_status=17(reviewed_entry_order_flow_not_available)`
- `rising_missed_tp1_source_gap_relief_applied` count=`35` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=34(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tick_speed_entry_block` count=`34` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=33(reviewed_rising_missed_nxt_eligibility_not_available), entry_order_flow_status=16(reviewed_entry_order_flow_not_available)`
- `shallow_source_gap_recheck` count=`31` routing=`reviewed_unknown_token_provenance` fields=`forbidden_uses=31(reviewed_forbidden_uses_unknown_literal_not_source_value)`

## Top Stages
- `scalping_scanner_candidate_observed`: `48200`
- `scalping_scanner_real_source_guard_block`: `48200`
- `scalping_scanner_promotion_latency_trace`: `11001`
- `scalping_scanner_runtime_target_attach`: `9390`
- `scalping_scanner_fast_precheck`: `7927`
- `scalping_scanner_watching_runtime_skip`: `7037`
- `scalping_scanner_runtime_queue_lag`: `6063`
- `holding_ws_freshness_blocked`: `4041`
- `scalping_scanner_heavy_eval_lag`: `3074`
- `scalping_scanner_candidate_promoted`: `2686`
- `rising_missed_watch_not_rising_skipped`: `2592`
- `scalping_scanner_watch_eviction`: `2522`
- `bad_entry_refined_candidate`: `1765`
- `manual_control_excluded_symbol_blocked`: `1591`
- `holding_ws_freshness_recovered`: `1371`
- `scale_in_feature_context_refresh`: `1169`
- `scale_in_ai_authority_retry`: `1084`
- `ai_holding_fast_reuse_band`: `959`
- `ai_holding_reuse_bypass`: `956`
- `ai_holding_review`: `956`

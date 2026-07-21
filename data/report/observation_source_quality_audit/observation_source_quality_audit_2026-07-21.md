# Observation Source Quality Audit - 2026-07-21

- status: `pass`
- event_count: `94067`
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
- `scalping_scanner_watching_runtime_skip` count=`9010` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=223(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalping_scanner_fast_precheck` count=`7796` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_submit_safety_backoff_reason=32(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `ai_holding_review` count=`851` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=179(reviewed_entry_order_flow_not_available)`
- `stat_action_decision_snapshot` count=`528` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=82(reviewed_stale_flag_not_available), quote_stale=82(reviewed_stale_flag_not_available), shallow_tick_context_stale=46(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=46(reviewed_shallow_stale_flag_not_available)`
- `rising_missed_one_share_entry` count=`305` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=283(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`297` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=286(reviewed_rising_missed_nxt_eligibility_not_available)`
- `budget_pass` count=`282` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=260(reviewed_rising_missed_nxt_eligibility_not_available)`
- `orderbook_stability_observed` count=`280` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=258(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_candidate_blocked` count=`261` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=252(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalp_entry_action_decision_snapshot` count=`122` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=105(reviewed_rising_missed_nxt_eligibility_not_available), entry_order_flow_status=44(reviewed_entry_order_flow_not_available), holding_exit_matrix_score_prior_band=24(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_band=8(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=8(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=7(reviewed_entry_score_source_not_available), entry_score_excluded_reason=7(reviewed_entry_score_source_not_available), risk_regime_context=2(reviewed_missing_risk_regime_context)`
- `entry_ai_price_canary_applied` count=`121` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=109(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_scout_upgrade_eval` count=`94` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=53(reviewed_rising_missed_nxt_eligibility_not_available)`
- `real_weak_ai_micro_entry_block` count=`64` routing=`reviewed_unknown_token_provenance` fields=`reason=64(reviewed_entry_block_source_quality_unknown_provenance), block_reason=64(reviewed_entry_block_source_quality_unknown_provenance), rising_missed_submit_safety_backoff_reason=64(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance), rising_missed_nxt_eligible=59(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_candidate_deferred` count=`36` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=34(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tick_speed_entry_block` count=`35` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=30(reviewed_rising_missed_nxt_eligibility_not_available), entry_order_flow_status=24(reviewed_entry_order_flow_not_available)`
- `strength_momentum_observed` count=`35` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=17(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_source_gap_relief_applied` count=`33` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=32(reviewed_rising_missed_nxt_eligibility_not_available)`
- `blocked_strength_momentum` count=`31` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=14(reviewed_rising_missed_nxt_eligibility_not_available)`
- `blocked_zero_qty` count=`23` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=23(reviewed_rising_missed_nxt_eligibility_not_available)`
- `ai_confirmed` count=`22` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=19(reviewed_rising_missed_nxt_eligibility_not_available), entry_order_flow_status=5(reviewed_entry_order_flow_not_available)`

## Top Stages
- `scalping_scanner_candidate_observed`: `12071`
- `scalping_scanner_real_source_guard_block`: `12071`
- `scalping_scanner_promotion_latency_trace`: `10157`
- `scalping_scanner_watching_runtime_skip`: `9010`
- `scalping_scanner_runtime_target_attach`: `8536`
- `scalping_scanner_fast_precheck`: `7796`
- `scalping_scanner_runtime_queue_lag`: `6352`
- `holding_ws_freshness_blocked`: `4391`
- `scalping_scanner_candidate_promoted`: `3474`
- `scalping_scanner_watch_eviction`: `3318`
- `scalping_scanner_heavy_eval_lag`: `2361`
- `rising_missed_watch_not_rising_skipped`: `1740`
- `bad_entry_refined_candidate`: `1601`
- `holding_ws_freshness_recovered`: `1429`
- `ai_holding_fast_reuse_band`: `854`
- `ai_holding_reuse_bypass`: `852`
- `ai_holding_review`: `851`
- `opening_rotation_1pct_upstream_blocked`: `833`
- `manual_control_excluded_symbol_blocked`: `821`
- `scale_in_feature_context_refresh`: `755`

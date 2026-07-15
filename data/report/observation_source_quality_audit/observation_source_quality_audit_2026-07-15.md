# Observation Source Quality Audit - 2026-07-15

- status: `pass`
- event_count: `78425`
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
- `scalping_scanner_fast_precheck` count=`7151` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_submit_safety_backoff_reason=29(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `scalping_scanner_watching_runtime_skip` count=`6905` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=121(reviewed_rising_missed_nxt_eligibility_not_available)`
- `stat_action_decision_snapshot` count=`1809` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=23(reviewed_stale_flag_not_available), quote_stale=23(reviewed_stale_flag_not_available), shallow_tick_context_stale=22(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=22(reviewed_shallow_stale_flag_not_available)`
- `ai_holding_review` count=`1415` routing=`reviewed_unknown_token_provenance` fields=`holding_score_preflight_source_quality=269(reviewed_holding_score_preflight_not_available), entry_order_flow_status=224(reviewed_entry_order_flow_not_available)`
- `blocked_strength_momentum` count=`594` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=6(reviewed_rising_missed_nxt_eligibility_not_available)`
- `strength_momentum_observed` count=`594` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=6(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_nxt_post_block_price_sample` count=`446` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_post_block_ws_0b_route=1(reviewed_rising_missed_nxt_post_block_route_not_available), rising_missed_nxt_post_block_ws_0d_route=1(reviewed_rising_missed_nxt_post_block_route_not_available)`
- `rising_missed_scout_upgrade_eval` count=`370` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=111(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalp_entry_action_decision_snapshot` count=`325` routing=`reviewed_unknown_token_provenance` fields=`holding_exit_matrix_score_prior_band=230(reviewed_score_prior_neutral_unknown_not_decision_input), entry_order_flow_status=186(reviewed_entry_order_flow_not_available), score_prior_band=61(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=61(reviewed_score_prior_neutral_unknown_not_decision_input), rising_missed_nxt_eligible=59(reviewed_rising_missed_nxt_eligibility_not_available), entry_score_source=18(reviewed_entry_score_source_not_available), entry_score_excluded_reason=18(reviewed_entry_score_source_not_available), risk_regime_context=6(reviewed_missing_risk_regime_context)`
- `ai_confirmed_terminal_no_budget` count=`181` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=113(reviewed_entry_order_flow_not_available), score_prior_band=61(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=61(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=18(reviewed_entry_score_source_not_available), entry_score_excluded_reason=18(reviewed_entry_score_source_not_available), rising_missed_nxt_eligible=3(reviewed_rising_missed_nxt_eligibility_not_available)`
- `ai_confirmed` count=`151` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=97(reviewed_entry_order_flow_not_available), rising_missed_nxt_eligible=11(reviewed_rising_missed_nxt_eligibility_not_available)`
- `budget_pass` count=`151` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=127(reviewed_rising_missed_nxt_eligibility_not_available)`
- `orderbook_stability_observed` count=`151` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=127(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_one_share_entry` count=`149` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=127(reviewed_rising_missed_nxt_eligibility_not_available)`
- `soft_stop_micro_grace` count=`118` routing=`reviewed_unknown_token_provenance` fields=`soft_stop_dynamic_grace_score_prior_band=20(reviewed_score_prior_neutral_unknown_not_decision_input)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`98` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=88(reviewed_rising_missed_nxt_eligibility_not_available)`
- `entry_ai_price_canary_applied` count=`95` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=64(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalp_sim_candidate_window_discarded` count=`92` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=2(reviewed_rising_missed_nxt_eligibility_not_available)`
- `blocked_liquidity` count=`90` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_candidate_blocked` count=`88` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=79(reviewed_rising_missed_nxt_eligibility_not_available)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `9685`
- `scalping_scanner_runtime_target_attach`: `7855`
- `scalping_scanner_fast_precheck`: `7151`
- `scalping_scanner_watching_runtime_skip`: `6905`
- `scalping_scanner_runtime_queue_lag`: `5429`
- `holding_ws_freshness_blocked`: `4090`
- `bad_entry_refined_candidate`: `2953`
- `scalping_scanner_candidate_promoted`: `2760`
- `scalping_scanner_watch_eviction`: `2633`
- `holding_ws_freshness_recovered`: `2605`
- `scalping_scanner_heavy_eval_lag`: `2534`
- `rising_missed_watch_not_rising_skipped`: `2354`
- `stat_action_decision_snapshot`: `1809`
- `scale_in_feature_context_refresh`: `1562`
- `scalping_scanner_candidate_observed`: `1496`
- `scalping_scanner_real_source_guard_block`: `1496`
- `scale_in_ai_authority_retry`: `1483`
- `ai_holding_fast_reuse_band`: `1418`
- `ai_holding_reuse_bypass`: `1416`
- `ai_holding_review`: `1415`

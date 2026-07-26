# Observation Source Quality Audit - 2026-07-24

- status: `pass`
- event_count: `60957`
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
- `scalping_scanner_watching_runtime_skip` count=`4152` routing=`reviewed_unknown_token_provenance` fields=`scanner_observed_venue=267(reviewed_scanner_venue_fail_closed_provenance), rising_missed_nxt_eligible=149(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=70(reviewed_explicit_sizing_unknown_venue_fallback), venue=70(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scalping_scanner_runtime_target_attach` count=`3991` routing=`reviewed_unknown_token_provenance` fields=`venue=1506(reviewed_scanner_venue_fail_closed_provenance), effective_venue=1506(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_nxt_post_block_price_sample` count=`3624` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_post_block_ws_0b_route=200(reviewed_rising_missed_nxt_post_block_route_not_available), rising_missed_nxt_post_block_ws_0d_route=155(reviewed_rising_missed_nxt_post_block_route_not_available)`
- `rising_missed_watch_not_rising_skipped` count=`1868` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1449(reviewed_rising_missed_nxt_eligibility_not_available)`
- `opening_rotation_1pct_upstream_blocked` count=`446` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1(reviewed_rising_missed_nxt_eligibility_not_available)`
- `opening_rotation_1pct_observed` count=`382` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=3(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalp_fast_exit_quote_blocked` count=`284` routing=`reviewed_unknown_token_provenance` fields=`fast_exit_ws_0d_route=284(reviewed_legacy_fast_exit_route_provenance)`
- `budget_pass` count=`237` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=157(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=70(reviewed_explicit_sizing_unknown_venue_fallback), venue=70(reviewed_explicit_sizing_unknown_venue_fallback)`
- `orderbook_stability_observed` count=`237` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=157(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=70(reviewed_explicit_sizing_unknown_venue_fallback), venue=70(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_one_share_entry` count=`237` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=157(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=52(reviewed_explicit_sizing_unknown_venue_fallback), venue=52(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`204` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=118(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=36(reviewed_explicit_sizing_unknown_venue_fallback), venue=36(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_tp1_candidate_blocked` count=`168` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=99(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=23(reviewed_explicit_sizing_unknown_venue_fallback), venue=23(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scalp_entry_action_decision_snapshot` count=`146` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=111(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=31(reviewed_explicit_sizing_unknown_venue_fallback), venue=31(reviewed_explicit_sizing_unknown_venue_fallback), holding_exit_matrix_score_prior_band=23(reviewed_score_prior_neutral_unknown_not_decision_input), entry_order_flow_status=11(reviewed_entry_order_flow_not_available), risk_regime_context=6(reviewed_missing_risk_regime_context)`
- `scale_in_ai_authority_retry` count=`132` routing=`reviewed_unknown_token_provenance` fields=`holding_context_ws_route=2(reviewed_holding_input_preflight_blocked_provenance), holding_context_ai_market_snapshot=2(reviewed_holding_input_preflight_blocked_provenance), ai_market_snapshot_market_data_route=2(reviewed_holding_input_preflight_blocked_provenance), ai_input_preflight_blockers=2(reviewed_holding_input_preflight_blocked_provenance), holding_context_blockers=2(reviewed_holding_input_preflight_blocked_provenance)`
- `ai_holding_review` count=`121` routing=`reviewed_unknown_token_provenance` fields=`holding_context_ws_route=4(reviewed_holding_input_preflight_blocked_provenance), holding_context_ai_market_snapshot=4(reviewed_holding_input_preflight_blocked_provenance), holding_context_blockers=4(reviewed_holding_input_preflight_blocked_provenance), holding_context_candle_route_partition_expected_key=1(reviewed_holding_input_preflight_blocked_provenance), holding_context_tape_route_partition_expected_key=1(reviewed_holding_input_preflight_blocked_provenance)`
- `latency_block` count=`117` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=77(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=31(reviewed_explicit_sizing_unknown_venue_fallback), venue=31(reviewed_explicit_sizing_unknown_venue_fallback)`
- `soft_stop_micro_grace` count=`111` routing=`reviewed_unknown_token_provenance` fields=`soft_stop_dynamic_grace_score_prior_band=111(reviewed_score_prior_neutral_unknown_not_decision_input)`
- `scalping_scanner_scheduler_venue_not_selected` count=`103` routing=`reviewed_unknown_token_provenance` fields=`venue=103(reviewed_scanner_venue_fail_closed_provenance), effective_venue=103(reviewed_scanner_venue_fail_closed_provenance)`
- `entry_price_canary_submit_block` count=`100` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=62(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=39(reviewed_explicit_sizing_unknown_venue_fallback), venue=39(reviewed_explicit_sizing_unknown_venue_fallback)`
- `loss_fallback_probe` count=`87` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=84(reviewed_stale_flag_not_available), quote_stale=84(reviewed_stale_flag_not_available)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `8808`
- `scalping_scanner_fast_precheck`: `6108`
- `scalping_scanner_candidate_observed`: `5004`
- `scalping_scanner_real_source_guard_block`: `5004`
- `scalping_scanner_runtime_queue_lag`: `4308`
- `scalping_scanner_watching_runtime_skip`: `4152`
- `scalping_scanner_runtime_target_attach`: `3991`
- `rising_missed_nxt_post_block_price_sample`: `3624`
- `scalping_scanner_heavy_eval_lag`: `2700`
- `rising_missed_watch_not_rising_skipped`: `1868`
- `scalping_scanner_candidate_promoted`: `1644`
- `scalping_scanner_scheduler_work_enqueued`: `1350`
- `scalping_scanner_watch_eviction`: `1296`
- `scalping_scanner_scheduler_work_dispatched`: `948`
- `scalping_scanner_scheduler_work_completed`: `947`
- `manual_control_fast_exit_monitor_blocked`: `849`
- `scalping_scanner_ws_backoff_watch_retained`: `526`
- `scalping_scanner_scheduler_claim_deferred`: `455`
- `opening_rotation_1pct_upstream_blocked`: `446`
- `scalping_scanner_scheduler_deadline_expired`: `418`

# Observation Source Quality Audit - 2026-07-27

- status: `pass`
- event_count: `506738`
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
- `scalping_scanner_fast_precheck` count=`54035` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_submit_safety_backoff_reason=9(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `rising_missed_watch_not_rising_skipped` count=`17418` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1588(reviewed_rising_missed_nxt_eligibility_not_available), venue=340(reviewed_observation_only_venue_not_available)`
- `scalping_scanner_runtime_target_attach` count=`8864` routing=`reviewed_unknown_token_provenance` fields=`venue=6905(reviewed_scanner_venue_fail_closed_provenance), effective_venue=6905(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_watching_runtime_skip` count=`7599` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=54(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=5(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_nxt_post_block_price_sample` count=`4106` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_post_block_selector_reason=218(reviewed_nxt_post_block_source_gap_provenance), rising_missed_nxt_post_block_source_block_reason=218(reviewed_nxt_post_block_source_gap_provenance), rising_missed_nxt_post_block_ws_0b_route=112(reviewed_rising_missed_nxt_post_block_route_not_available), rising_missed_nxt_post_block_ws_0d_route=60(reviewed_rising_missed_nxt_post_block_route_not_available)`
- `scalping_scanner_watch_eviction` count=`1050` routing=`reviewed_unknown_token_provenance` fields=`venue=616(reviewed_observation_only_venue_not_available), effective_venue=616(reviewed_observation_only_venue_not_available)`
- `scalping_scanner_scheduler_generation_invalidated` count=`1031` routing=`reviewed_unknown_token_provenance` fields=`venue=1031(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`376` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=104(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=6(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_ws_0d_route=1(reviewed_rising_missed_ws_route_not_available)`
- `rising_missed_one_share_entry_blocked` count=`258` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=44(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_ws_0d_route=1(reviewed_rising_missed_ws_route_not_available)`
- `rising_missed_tp1_candidate_blocked` count=`200` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=78(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=3(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_tp1_candidate_deferred` count=`176` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=26(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=3(reviewed_explicit_sizing_unknown_venue_fallback), rising_missed_ws_0d_route=1(reviewed_rising_missed_ws_route_not_available)`
- `budget_pass` count=`150` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=78(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=14(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_one_share_entry` count=`150` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=78(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=1(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scalp_entry_action_decision_snapshot` count=`148` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=87(reviewed_rising_missed_nxt_eligibility_not_available), holding_exit_matrix_score_prior_band=40(reviewed_score_prior_neutral_unknown_not_decision_input), entry_order_flow_status=22(reviewed_entry_order_flow_not_available), risk_regime_context=18(reviewed_missing_risk_regime_context), tier_reason=16(reviewed_explicit_sizing_unknown_venue_fallback), latency_true_ofi_direct_canary_signed_tape_event_time_latest_side=5(reviewed_signed_tape_event_side_not_available), block_reason=3(reviewed_entry_block_source_quality_unknown_provenance), entry_action_final_block_reason=3(reviewed_entry_block_source_quality_unknown_provenance)`
- `orderbook_stability_observed` count=`147` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=75(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=14(reviewed_explicit_sizing_unknown_venue_fallback)`
- `latency_block` count=`80` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=45(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=10(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_entry_ai_async_pending` count=`73` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=21(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scanner_async_eval_dispatched` count=`73` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=21(reviewed_rising_missed_nxt_eligibility_not_available)`
- `ai_confirmed` count=`68` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=39(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=7(reviewed_explicit_sizing_unknown_venue_fallback), entry_order_flow_status=2(reviewed_entry_order_flow_not_available)`
- `scanner_async_result_commit` count=`66` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=18(reviewed_rising_missed_nxt_eligibility_not_available)`

## Top Stages
- `scalping_scanner_scheduler_work_enqueued`: `84589`
- `scalping_scanner_scheduler_work_dispatched`: `82669`
- `scalping_scanner_scheduler_work_completed`: `82660`
- `scalping_scanner_scheduler_claim_deferred`: `66774`
- `scalping_scanner_promotion_latency_trace`: `65208`
- `scalping_scanner_fast_precheck`: `54035`
- `rising_missed_watch_not_rising_skipped`: `17418`
- `scalping_scanner_heavy_eval_lag`: `11173`
- `scalping_scanner_runtime_target_attach`: `8864`
- `scalping_scanner_watching_runtime_skip`: `7599`
- `rising_missed_nxt_post_block_price_sample`: `4106`
- `scalping_scanner_scheduler_deadline_expired`: `2852`
- `scalping_scanner_ws_backoff_watch_retained`: `2362`
- `scalping_scanner_candidate_promoted`: `1629`
- `scalping_scanner_scheduler_inbox_enqueued`: `1609`
- `scalping_scanner_scheduler_generation_registered`: `1595`
- `manual_control_fast_exit_monitor_blocked`: `1349`
- `scalping_scanner_watch_eviction`: `1050`
- `scalping_scanner_scheduler_generation_invalidated`: `1031`
- `scalping_scanner_candidate_observed`: `885`

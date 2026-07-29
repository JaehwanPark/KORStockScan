# Observation Source Quality Audit - 2026-07-28

- status: `pass`
- event_count: `500734`
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
- `scalping_scanner_fast_precheck` count=`35035` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=2425(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=1998(reviewed_scanner_stale_backoff_route_not_available), rising_missed_submit_safety_backoff_reason=1(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `scalping_scanner_runtime_target_attach` count=`13506` routing=`reviewed_unknown_token_provenance` fields=`venue=12364(reviewed_scanner_venue_fail_closed_provenance), effective_venue=12364(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_watching_runtime_skip` count=`7942` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=187(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=97(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_watch_not_rising_skipped` count=`7128` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=3774(reviewed_rising_missed_nxt_eligibility_not_available), venue=82(reviewed_observation_only_venue_not_available)`
- `rising_missed_nxt_post_block_price_sample` count=`5218` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_post_block_ws_0b_route=39(reviewed_rising_missed_nxt_post_block_route_not_available), rising_missed_nxt_post_block_ws_0d_route=14(reviewed_rising_missed_nxt_post_block_route_not_available)`
- `rising_missed_one_share_entry_blocked` count=`2459` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=2162(reviewed_rising_missed_nxt_eligibility_not_available), venue=16(reviewed_observation_only_venue_not_available), tier_reason=1(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scanner_async_eval_dispatched` count=`2278` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=41(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=29(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scanner_async_result_commit` count=`1886` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=32(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=24(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_entry_ai_async_result_applied` count=`1691` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=32(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=24(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_entry_ai_async_pending` count=`1516` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=10(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=3(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_async_commit_phase` count=`1466` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=60(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=49(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_async_freshness_dispatched` count=`1153` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=39(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=32(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_async_freshness_commit` count=`1058` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=35(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=28(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scalping_scanner_watch_eviction` count=`838` routing=`reviewed_unknown_token_provenance` fields=`venue=838(reviewed_observation_only_venue_not_available), effective_venue=838(reviewed_observation_only_venue_not_available)`
- `scalping_scanner_scheduler_generation_invalidated` count=`802` routing=`reviewed_unknown_token_provenance` fields=`venue=802(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`321` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=163(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=17(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scalping_scanner_async_result_rejected` count=`246` routing=`reviewed_unknown_token_provenance` fields=`scanner_async_transport_namespace=246(reviewed_scanner_async_transport_not_available)`
- `rising_missed_tp1_candidate_deferred` count=`213` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=73(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=11(reviewed_explicit_sizing_unknown_venue_fallback)`
- `ai_holding_review` count=`189` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=11(reviewed_entry_order_flow_not_available), holding_context_ws_route=2(reviewed_holding_input_preflight_blocked_provenance), holding_context_blockers=1(reviewed_holding_input_preflight_blocked_provenance)`
- `soft_stop_micro_grace` count=`146` routing=`reviewed_unknown_token_provenance` fields=`soft_stop_dynamic_grace_score_prior_band=146(reviewed_score_prior_neutral_unknown_not_decision_input)`

## Top Stages
- `scalping_scanner_scheduler_claim_deferred`: `72787`
- `scalping_scanner_scheduler_work_enqueued`: `62812`
- `scalping_scanner_scheduler_work_dispatched`: `58350`
- `scalping_scanner_scheduler_work_completed`: `58347`
- `scalping_scanner_promotion_latency_trace`: `47004`
- `scalping_scanner_candidate_observed`: `35418`
- `scalping_scanner_real_source_guard_block`: `35418`
- `scalping_scanner_fast_precheck`: `35035`
- `scalping_scanner_runtime_target_attach`: `13506`
- `scalping_scanner_heavy_eval_lag`: `11968`
- `scalping_scanner_watching_runtime_skip`: `7942`
- `rising_missed_watch_not_rising_skipped`: `7128`
- `scalping_scanner_scheduler_claim_missing`: `6517`
- `scalping_scanner_async_transport_ready`: `5237`
- `rising_missed_nxt_post_block_price_sample`: `5218`
- `scalping_scanner_scheduler_deadline_expired`: `2771`
- `rising_missed_one_share_entry_blocked`: `2459`
- `scanner_async_eval_dispatched`: `2278`
- `opening_rotation_async_context_dispatched`: `2066`
- `opening_rotation_async_context_commit`: `1923`

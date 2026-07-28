# Observation Source Quality Audit - 2026-07-28

- status: `warning`
- event_count: `291823`
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
- `scalping_scanner_fast_precheck` count=`26271` routing=`source_quality_blocker_or_provenance_backfill` fields=`scanner_stale_backoff_raw_0b_route=684(0.026), scanner_stale_backoff_raw_0d_route=550(0.0209)`
- `ai_holding_review` count=`142` routing=`source_quality_blocker_or_provenance_backfill` fields=`holding_context_entry_time_context=20(0.1408), holding_context_ws_route=1(0.007), holding_context_ai_market_snapshot=1(0.007)`

## Reviewed Unknown Token Findings
- `scalping_scanner_fast_precheck` count=`26271` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_submit_safety_backoff_reason=1(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `scalping_scanner_runtime_target_attach` count=`6682` routing=`reviewed_unknown_token_provenance` fields=`venue=6070(reviewed_scanner_venue_fail_closed_provenance), effective_venue=6070(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_watching_runtime_skip` count=`4505` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=156(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=97(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_watch_not_rising_skipped` count=`3535` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=3535(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_one_share_entry_blocked` count=`2117` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=2117(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=1(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scanner_async_eval_dispatched` count=`1777` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=41(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=29(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scanner_async_result_commit` count=`1421` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=32(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=24(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_entry_ai_async_result_applied` count=`1336` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=32(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=24(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_entry_ai_async_pending` count=`1296` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=10(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=3(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_async_commit_phase` count=`851` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=60(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=49(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_async_freshness_dispatched` count=`675` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=39(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=32(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_async_freshness_commit` count=`584` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=35(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=28(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scalping_scanner_watch_eviction` count=`450` routing=`reviewed_unknown_token_provenance` fields=`venue=450(reviewed_observation_only_venue_not_available), effective_venue=450(reviewed_observation_only_venue_not_available)`
- `scalping_scanner_scheduler_generation_invalidated` count=`441` routing=`reviewed_unknown_token_provenance` fields=`venue=441(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_async_result_rejected` count=`207` routing=`reviewed_unknown_token_provenance` fields=`scanner_async_transport_namespace=207(reviewed_scanner_async_transport_not_available)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`148` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=148(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=17(reviewed_explicit_sizing_unknown_venue_fallback)`
- `ai_holding_review` count=`142` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=11(reviewed_entry_order_flow_not_available)`
- `soft_stop_micro_grace` count=`107` routing=`reviewed_unknown_token_provenance` fields=`soft_stop_dynamic_grace_score_prior_band=107(reviewed_score_prior_neutral_unknown_not_decision_input)`
- `rising_missed_tp1_candidate_blocked` count=`79` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=79(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=6(reviewed_explicit_sizing_unknown_venue_fallback)`
- `probe_continuation_deferred` count=`69` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=69(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=69(reviewed_explicit_sizing_unknown_venue_fallback), post_probe_direction_state=68(reviewed_post_probe_direction_source_gap)`

## Top Stages
- `scalping_scanner_scheduler_work_enqueued`: `46805`
- `scalping_scanner_scheduler_work_dispatched`: `42465`
- `scalping_scanner_scheduler_work_completed`: `42461`
- `scalping_scanner_promotion_latency_trace`: `33446`
- `scalping_scanner_scheduler_claim_deferred`: `28505`
- `scalping_scanner_fast_precheck`: `26271`
- `scalping_scanner_heavy_eval_lag`: `7174`
- `scalping_scanner_runtime_target_attach`: `6682`
- `scalping_scanner_scheduler_claim_missing`: `6438`
- `scalping_scanner_candidate_observed`: `5322`
- `scalping_scanner_real_source_guard_block`: `5322`
- `scalping_scanner_watching_runtime_skip`: `4505`
- `scalping_scanner_async_transport_ready`: `4255`
- `rising_missed_watch_not_rising_skipped`: `3535`
- `scalping_scanner_scheduler_deadline_expired`: `2698`
- `rising_missed_one_share_entry_blocked`: `2117`
- `opening_rotation_async_context_dispatched`: `2023`
- `opening_rotation_async_context_commit`: `1882`
- `scanner_async_eval_dispatched`: `1777`
- `scanner_async_result_commit`: `1421`

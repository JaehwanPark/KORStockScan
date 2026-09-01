# Observation Source Quality Audit - 2026-09-01

- status: `pass`
- event_count: `358647`
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
- `scalping_scanner_fast_precheck` count=`50108` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=1217(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=453(reviewed_scanner_stale_backoff_route_not_available)`
- `scalping_scanner_watching_runtime_skip` count=`14479` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=885(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=10(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=10(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=10(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_watch_not_rising_skipped` count=`6965` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=4088(reviewed_rising_missed_nxt_eligibility_not_available), venue=8(reviewed_observation_only_venue_not_available), rising_missed_effective_venue=8(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`1519` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=638(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=2(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=2(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=2(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scalp_entry_action_decision_snapshot` count=`975` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=552(reviewed_rising_missed_nxt_eligibility_not_available), holding_exit_matrix_score_prior_band=401(reviewed_score_prior_neutral_unknown_not_decision_input), risk_regime_context=124(reviewed_missing_risk_regime_context), entry_order_flow_status=89(reviewed_entry_order_flow_not_available), score_prior_band=55(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=55(reviewed_score_prior_neutral_unknown_not_decision_input), tier_reason=16(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=16(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_tp1_candidate_deferred` count=`823` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=119(reviewed_rising_missed_nxt_eligibility_not_available)`
- `ai_holding_review` count=`710` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=14(reviewed_entry_order_flow_not_available)`
- `rising_missed_tp1_candidate_blocked` count=`696` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=519(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=2(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=2(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=2(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_one_share_entry` count=`587` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=544(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=2(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=2(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=2(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scalp_sim_panic_context_warning` count=`567` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=567(reviewed_missing_risk_regime_context), market_risk_state=567(reviewed_missing_risk_regime_context), liquidity_state=567(reviewed_missing_risk_regime_context), risk_regime_epoch_id=567(reviewed_missing_risk_regime_context)`
- `stat_action_decision_snapshot` count=`547` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=30(reviewed_stale_flag_not_available), quote_stale=30(reviewed_stale_flag_not_available), shallow_tick_context_stale=25(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=25(reviewed_shallow_stale_flag_not_available)`
- `opening_rotation_krx_regular_scope_skipped` count=`543` routing=`reviewed_unknown_token_provenance` fields=`forbidden_uses=543(reviewed_forbidden_uses_unknown_literal_not_source_value)`
- `prev_close_gainer_entry_ai_handoff` count=`521` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=259(reviewed_rising_missed_nxt_eligibility_not_available)`
- `budget_pass` count=`471` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=426(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=12(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=12(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=12(reviewed_explicit_sizing_unknown_venue_fallback)`
- `orderbook_stability_observed` count=`471` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=426(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=12(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=12(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=12(reviewed_explicit_sizing_unknown_venue_fallback)`
- `reversal_add_blocked_reason` count=`439` routing=`reviewed_unknown_token_provenance` fields=`shallow_tick_context_stale=25(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=25(reviewed_shallow_stale_flag_not_available), tick_context_stale=25(reviewed_stale_flag_not_available), quote_stale=25(reviewed_stale_flag_not_available)`
- `risky_micro_episode_source_candidate_observed` count=`336` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=317(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=9(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=9(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=9(reviewed_explicit_sizing_unknown_venue_fallback)`
- `ai_confirmed` count=`287` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=65(reviewed_rising_missed_nxt_eligibility_not_available), entry_order_flow_status=31(reviewed_entry_order_flow_not_available), tier_reason=2(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=2(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=2(reviewed_explicit_sizing_unknown_venue_fallback)`
- `blocked_ai_score` count=`281` routing=`reviewed_unknown_token_provenance` fields=`score_prior_band=55(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=55(reviewed_score_prior_neutral_unknown_not_decision_input), entry_order_flow_status=24(reviewed_entry_order_flow_not_available), entry_score_source=14(reviewed_entry_score_source_not_available), entry_recheck_excluded_reason=14(reviewed_entry_score_source_not_available), entry_score_excluded_reason=14(reviewed_entry_score_source_not_available)`
- `rising_missed_adverse_micro_recovery_checkpoint` count=`276` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_adverse_micro_recovery_ws_0b_raw_route=15(reviewed_adverse_micro_recovery_route_not_available)`

## Top Stages
- `scalping_scanner_candidate_pruned`: `96901`
- `scalping_scanner_promotion_latency_trace`: `63327`
- `scalping_scanner_fast_precheck`: `50108`
- `scalping_scanner_runtime_queue_lag`: `27300`
- `scalping_scanner_watching_runtime_skip`: `14479`
- `scalping_scanner_candidate_observed`: `13961`
- `scalping_scanner_real_source_guard_block`: `13961`
- `scalping_scanner_heavy_eval_completion`: `13606`
- `scalping_scanner_heavy_eval_lag`: `13219`
- `rising_missed_watch_not_rising_skipped`: `6965`
- `risky_micro_episode_executable_bbo_observed`: `6948`
- `rising_missed_nxt_post_block_price_sample`: `5068`
- `scalping_scanner_runtime_target_attach`: `2726`
- `scalping_scanner_candidate_promoted`: `2595`
- `scalping_scanner_watch_eviction`: `2299`
- `bad_entry_refined_candidate`: `1937`
- `strength_momentum_observed`: `1862`
- `rising_missed_tp1_counterfactual_submit_safety`: `1519`
- `scalping_scanner_ws_backoff_watch_retained`: `1457`
- `blocked_strength_momentum`: `1359`

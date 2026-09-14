# Observation Source Quality Audit - 2026-09-14

- status: `warning`
- event_count: `377361`
- tuning_input_policy: `exclude_defective_rows_not_full_day_raw`
- hard_blocking_excluded_row_count: `4914`
- pre_exclusion_hard_blocking_excluded_row_count: `4914`
- current_scan_hard_blocking_excluded_row_count: `0`
- post_exclusion_hard_blocking_excluded_row_count: `0`
- raw_row_exclusion_applied: `True`
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
- `scalping_scanner_candidate_pruned` count=`91970` routing=`source_quality_blocker_or_provenance_backfill` fields=`actual_execution_venue=60130(0.6538), lookup_attention_weight_effective_venue=31840(0.3462), effective_venue=31840(0.3462), market_data_route=4285(0.0466), scanner_market_gainer_venue=1644(0.0179), scanner_market_gainer_source_observations=1644(0.0179)`
- `scalping_scanner_prune_bbo_schedule` count=`73510` routing=`source_quality_blocker_or_provenance_backfill` fields=`actual_execution_venue=48117(0.6546), lookup_attention_weight_effective_venue=25393(0.3454), effective_venue=25393(0.3454), market_data_route=3620(0.0492), scanner_market_gainer_venue=1636(0.0223), scanner_market_gainer_source_observations=1636(0.0223)`
- `rising_missed_one_share_entry_blocked` count=`5763` routing=`source_quality_blocker_or_provenance_backfill` fields=`effective_venue=2241(0.3889), venue=79(0.0137)`
- `rising_missed_watch_not_rising_skipped` count=`4230` routing=`source_quality_blocker_or_provenance_backfill` fields=`effective_venue=633(0.1496), venue=85(0.0201)`
- `scalping_scanner_runtime_target_attach` count=`3439` routing=`source_quality_blocker_or_provenance_backfill` fields=`lookup_attention_weight_effective_venue=896(0.2605)`
- `scalp_entry_action_decision_snapshot` count=`3088` routing=`source_quality_blocker_or_provenance_backfill` fields=`entry_candle_actual_execution_venue=2864(0.9275), ai_market_snapshot_actual_execution_venue=2864(0.9275), ai_input_preflight_source_timing=1970(0.638), ai_input_preflight_blockers=1970(0.638)`
- `scalping_scanner_source_fetch_census` count=`2970` routing=`source_quality_blocker_or_provenance_backfill` fields=`scanner_source_rows_json=2784(0.9374), actual_execution_venue=2010(0.6768), effective_venue=969(0.3263), market_data_route=190(0.064), venue=9(0.003)`
- `scalping_scanner_candidate_promoted` count=`2540` routing=`source_quality_blocker_or_provenance_backfill` fields=`lookup_attention_weight_effective_venue=896(0.3528), effective_venue=896(0.3528), scanner_market_gainer_venue=256(0.1008), scanner_market_gainer_source_observations=256(0.1008)`
- `scalping_scanner_candidate_observed` count=`2441` routing=`source_quality_blocker_or_provenance_backfill` fields=`actual_execution_venue=1379(0.5649), lookup_attention_weight_effective_venue=1062(0.4351), effective_venue=1062(0.4351), market_data_route=101(0.0414), scanner_market_gainer_venue=8(0.0033), scanner_market_gainer_source_observations=8(0.0033)`
- `scalping_scanner_real_source_guard_block` count=`2441` routing=`source_quality_blocker_or_provenance_backfill` fields=`actual_execution_venue=1379(0.5649), lookup_attention_weight_effective_venue=1062(0.4351), effective_venue=1062(0.4351), market_data_route=101(0.0414), scanner_market_gainer_venue=8(0.0033), scanner_market_gainer_source_observations=8(0.0033)`
- `prev_close_gainer_entry_ai_handoff` count=`468` routing=`source_quality_blocker_or_provenance_backfill` fields=`effective_venue=103(0.2201)`
- `scalp_sim_panic_context_warning` count=`450` routing=`source_quality_blocker_or_provenance_backfill` fields=`holding_context_venue=449(0.9978)`
- `bad_entry_refined_candidate` count=`444` routing=`source_quality_blocker_or_provenance_backfill` fields=`holding_context_venue=206(0.464)`
- `scalping_scanner_candidate_pool_census` count=`293` routing=`source_quality_blocker_or_provenance_backfill` fields=`scanner_source_rows_json=293(1.0), actual_execution_venue=198(0.6758), effective_venue=95(0.3242), market_data_route=19(0.0648)`
- `scalping_scanner_low_rebound_source_observed` count=`293` routing=`source_quality_blocker_or_provenance_backfill` fields=`actual_execution_venue=198(0.6758), effective_venue=95(0.3242), market_data_route=19(0.0648)`
- `scale_in_feature_context_refresh` count=`290` routing=`source_quality_blocker_or_provenance_backfill` fields=`holding_context_venue=125(0.431)`
- `scalping_scanner_iteration_timing` count=`290` routing=`source_quality_blocker_or_provenance_backfill` fields=`actual_execution_venue=195(0.6724), effective_venue=95(0.3276), market_data_route=19(0.0655)`
- `stat_action_decision_snapshot` count=`268` routing=`source_quality_blocker_or_provenance_backfill` fields=`holding_context_venue=115(0.4291), score_prior_band=14(0.0522)`
- `reversal_add_blocked_reason` count=`234` routing=`source_quality_blocker_or_provenance_backfill` fields=`holding_context_venue=117(0.5)`
- `ai_holding_fast_reuse_band` count=`187` routing=`source_quality_blocker_or_provenance_backfill` fields=`holding_context_venue=43(0.2299)`

## Reviewed Unknown Token Findings
- `scalping_scanner_candidate_pruned` count=`91970` routing=`reviewed_unknown_token_provenance` fields=`actual_execution_venue=31840(reviewed_integrated_route_actual_execution_venue_unobserved)`
- `scalping_scanner_prune_bbo_schedule` count=`73510` routing=`reviewed_unknown_token_provenance` fields=`actual_execution_venue=25393(reviewed_integrated_route_actual_execution_venue_unobserved)`
- `scalping_scanner_promotion_latency_trace` count=`54520` routing=`reviewed_unknown_token_provenance` fields=`venue=27685(reviewed_scanner_venue_fail_closed_provenance), effective_venue=27685(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_fast_precheck` count=`41555` routing=`reviewed_unknown_token_provenance` fields=`venue=21423(reviewed_scanner_venue_fail_closed_provenance), effective_venue=21423(reviewed_scanner_venue_fail_closed_provenance), scanner_promotion_reanchor_effective_venue=21423(reviewed_scanner_venue_fail_closed_provenance), scanner_stale_backoff_canonical_effective_venue=21423(reviewed_scanner_venue_fail_closed_provenance), main_lifecycle_venue=21149(reviewed_main_lifecycle_venue_not_available), scanner_stale_backoff_raw_0b_route=986(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=546(reviewed_scanner_stale_backoff_route_not_available)`
- `scalping_scanner_runtime_queue_lag` count=`25042` routing=`reviewed_unknown_token_provenance` fields=`venue=12106(reviewed_scanner_venue_fail_closed_provenance), effective_venue=12106(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_heavy_eval_completion` count=`13157` routing=`reviewed_unknown_token_provenance` fields=`venue=6385(reviewed_scanner_venue_fail_closed_provenance), effective_venue=6385(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_heavy_eval_lag` count=`12965` routing=`reviewed_unknown_token_provenance` fields=`venue=6262(reviewed_scanner_venue_fail_closed_provenance), effective_venue=6262(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_watching_runtime_skip` count=`12802` routing=`reviewed_unknown_token_provenance` fields=`venue=6386(reviewed_scanner_venue_fail_closed_provenance), effective_venue=6386(reviewed_scanner_venue_fail_closed_provenance), rising_missed_nxt_eligible=97(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_one_share_entry_blocked` count=`5763` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=3580(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=79(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_watch_not_rising_skipped` count=`4230` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=3270(reviewed_rising_missed_nxt_eligibility_not_available), rising_missed_effective_venue=85(reviewed_rising_missed_nxt_eligibility_not_available)`
- `ai_confirmed` count=`3782` routing=`reviewed_unknown_token_provenance` fields=`venue=253(reviewed_scanner_venue_fail_closed_provenance), effective_venue=253(reviewed_scanner_venue_fail_closed_provenance), main_lifecycle_venue=253(reviewed_main_lifecycle_venue_not_available), entry_order_flow_status=8(reviewed_entry_order_flow_not_available), rising_missed_nxt_eligible=4(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalping_scanner_runtime_target_attach` count=`3439` routing=`reviewed_unknown_token_provenance` fields=`venue=174(reviewed_scanner_venue_fail_closed_provenance), effective_venue=174(reviewed_scanner_venue_fail_closed_provenance)`
- `scalp_entry_action_decision_snapshot` count=`3088` routing=`reviewed_unknown_token_provenance` fields=`venue=2243(reviewed_scanner_venue_fail_closed_provenance), effective_venue=2243(reviewed_scanner_venue_fail_closed_provenance), rising_missed_nxt_eligible=217(reviewed_rising_missed_nxt_eligibility_not_available), score_prior_band=28(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=28(reviewed_score_prior_neutral_unknown_not_decision_input), entry_order_flow_status=10(reviewed_entry_order_flow_not_available), entry_score_source=1(reviewed_entry_score_source_not_available), entry_recheck_excluded_reason=1(reviewed_entry_score_source_not_available)`
- `scalping_scanner_source_fetch_census` count=`2970` routing=`reviewed_unknown_token_provenance` fields=`actual_execution_venue=960(reviewed_integrated_route_actual_execution_venue_unobserved)`
- `scalping_scanner_candidate_observed` count=`2441` routing=`reviewed_unknown_token_provenance` fields=`actual_execution_venue=1062(reviewed_integrated_route_actual_execution_venue_unobserved)`
- `scalping_scanner_real_source_guard_block` count=`2441` routing=`reviewed_unknown_token_provenance` fields=`actual_execution_venue=1062(reviewed_integrated_route_actual_execution_venue_unobserved)`
- `scalping_scanner_watch_eviction` count=`2187` routing=`reviewed_unknown_token_provenance` fields=`venue=797(reviewed_observation_only_venue_not_available), effective_venue=797(reviewed_observation_only_venue_not_available), venue=3(reviewed_scanner_venue_fail_closed_provenance), effective_venue=3(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_ws_backoff_watch_retained` count=`1610` routing=`reviewed_unknown_token_provenance` fields=`venue=34(reviewed_scanner_venue_fail_closed_provenance), effective_venue=34(reviewed_scanner_venue_fail_closed_provenance)`
- `strength_momentum_observed` count=`1174` routing=`reviewed_unknown_token_provenance` fields=`venue=396(reviewed_scanner_venue_fail_closed_provenance), effective_venue=396(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`946` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=759(reviewed_rising_missed_nxt_eligibility_not_available), venue=91(reviewed_scanner_venue_fail_closed_provenance), effective_venue=91(reviewed_scanner_venue_fail_closed_provenance), rising_missed_effective_venue=1(reviewed_rising_missed_nxt_eligibility_not_available)`

## Top Stages
- `scalping_scanner_candidate_pruned`: `91970`
- `scalping_scanner_prune_bbo_schedule`: `73510`
- `scalping_scanner_promotion_latency_trace`: `54520`
- `scalping_scanner_fast_precheck`: `41555`
- `scalping_scanner_runtime_queue_lag`: `25042`
- `scalping_scanner_heavy_eval_completion`: `13157`
- `scalping_scanner_heavy_eval_lag`: `12965`
- `scalping_scanner_watching_runtime_skip`: `12802`
- `rising_missed_one_share_entry_blocked`: `5763`
- `rising_missed_watch_not_rising_skipped`: `4230`
- `ai_confirmed`: `3782`
- `scalping_scanner_runtime_target_attach`: `3439`
- `scalp_entry_action_decision_snapshot`: `3088`
- `scalping_scanner_source_fetch_census`: `2970`
- `scalping_scanner_candidate_promoted`: `2540`
- `scalping_scanner_candidate_observed`: `2441`
- `scalping_scanner_real_source_guard_block`: `2441`
- `scalping_scanner_watch_eviction`: `2187`
- `scalping_scanner_prune_bbo_observation`: `2077`
- `rising_missed_nxt_post_block_price_sample`: `1790`

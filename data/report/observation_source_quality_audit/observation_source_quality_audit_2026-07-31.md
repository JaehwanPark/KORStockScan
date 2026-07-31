# Observation Source Quality Audit - 2026-07-31

- status: `warning`
- event_count: `406281`
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
- `scalping_scanner_runtime_target_attach` count=`10698` routing=`source_quality_blocker_or_provenance_backfill` fields=`venue=7(0.0007), effective_venue=7(0.0007), market_session_bucket=7(0.0007)`
- `strength_momentum_observed` count=`2951` routing=`source_quality_blocker_or_provenance_backfill` fields=`venue=37(0.0125), effective_venue=37(0.0125)`
- `prev_close_gainer_entry_ai_handoff` count=`1730` routing=`source_quality_blocker_or_provenance_backfill` fields=`venue=113(0.0653)`
- `scalping_scanner_ws_backoff_watch_retained` count=`1550` routing=`source_quality_blocker_or_provenance_backfill` fields=`venue=8(0.0052), effective_venue=8(0.0052)`
- `opening_rotation_entry_owner_handoff` count=`513` routing=`source_quality_blocker_or_provenance_backfill` fields=`venue=31(0.0604), effective_venue=31(0.0604)`
- `ai_confirmed` count=`503` routing=`source_quality_blocker_or_provenance_backfill` fields=`venue=16(0.0318), effective_venue=16(0.0318)`
- `ai_numeric_consistency_recheck_evaluated` count=`378` routing=`source_quality_blocker_or_provenance_backfill` fields=`venue=12(0.0317), effective_venue=12(0.0317)`
- `ai_numeric_consistency_recheck_skipped` count=`378` routing=`source_quality_blocker_or_provenance_backfill` fields=`venue=12(0.0317), effective_venue=12(0.0317)`
- `first_ai_wait` count=`205` routing=`source_quality_blocker_or_provenance_backfill` fields=`score_prior_band=3(0.0146), score_prior_confidence=3(0.0146), venue=1(0.0049), effective_venue=1(0.0049)`
- `scalping_scanner_watch_budget_reallocated` count=`165` routing=`source_quality_blocker_or_provenance_backfill` fields=`venue=1(0.0061), effective_venue=1(0.0061)`
- `scalp_sim_entry_ai_price_skip_order` count=`92` routing=`source_quality_blocker_or_provenance_backfill` fields=`effective_venue=4(0.0435)`
- `scalp_sim_euphoria_context_noop` count=`75` routing=`source_quality_blocker_or_provenance_backfill` fields=`venue=2(0.0267), effective_venue=2(0.0267)`
- `strength_momentum_pass` count=`70` routing=`source_quality_blocker_or_provenance_backfill` fields=`venue=6(0.0857), effective_venue=6(0.0857)`
- `wait65_79_ev_candidate` count=`59` routing=`source_quality_blocker_or_provenance_backfill` fields=`venue=2(0.0339), effective_venue=2(0.0339)`
- `early_accel_strong_bundle_recheck_evaluated` count=`42` routing=`source_quality_blocker_or_provenance_backfill` fields=`venue=4(0.0952), effective_venue=4(0.0952)`
- `early_accel_strong_bundle_recheck_allowed` count=`36` routing=`source_quality_blocker_or_provenance_backfill` fields=`venue=2(0.0556), effective_venue=2(0.0556)`
- `early_accel_strong_bundle_recheck_failed` count=`36` routing=`source_quality_blocker_or_provenance_backfill` fields=`venue=2(0.0556), effective_venue=2(0.0556)`
- `pre_submit_micro_unavailable_block` count=`9` routing=`source_quality_blocker_or_provenance_backfill` fields=`entry_order_flow_status=7(0.7778)`
- `scale_in_qty_block` count=`8` routing=`source_quality_blocker_or_provenance_backfill` fields=`tier_reason=2(0.25), venue=2(0.25)`
- `blocked_gap_from_scan` count=`7` routing=`source_quality_blocker_or_provenance_backfill` fields=`venue=1(0.1429), effective_venue=1(0.1429)`

## Reviewed Unknown Token Findings
- `scalping_scanner_promotion_latency_trace` count=`94286` routing=`reviewed_unknown_token_provenance` fields=`venue=958(reviewed_scanner_venue_fail_closed_provenance), effective_venue=958(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_watch_not_rising_skipped` count=`79639` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=61565(reviewed_rising_missed_nxt_eligibility_not_available), venue=1280(reviewed_observation_only_venue_not_available)`
- `scalping_scanner_fast_precheck` count=`56650` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=1949(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=571(reviewed_scanner_stale_backoff_route_not_available), venue=519(reviewed_scanner_venue_fail_closed_provenance), effective_venue=519(reviewed_scanner_venue_fail_closed_provenance), scanner_promotion_reanchor_effective_venue=519(reviewed_scanner_venue_fail_closed_provenance), scanner_stale_backoff_canonical_effective_venue=519(reviewed_scanner_venue_fail_closed_provenance), rising_missed_submit_safety_backoff_reason=4(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `scalping_scanner_heavy_eval_lag` count=`37636` routing=`reviewed_unknown_token_provenance` fields=`venue=439(reviewed_scanner_venue_fail_closed_provenance), effective_venue=439(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_runtime_queue_lag` count=`31125` routing=`reviewed_unknown_token_provenance` fields=`venue=31125(reviewed_scanner_venue_fail_closed_provenance), effective_venue=31125(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_nxt_post_block_price_sample` count=`19038` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_post_block_ws_0b_route=191(reviewed_rising_missed_nxt_post_block_route_not_available), rising_missed_nxt_post_block_ws_0d_route=146(reviewed_rising_missed_nxt_post_block_route_not_available)`
- `scalping_scanner_watching_runtime_skip` count=`14384` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=946(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=139(reviewed_explicit_sizing_unknown_venue_fallback), venue=125(reviewed_scanner_venue_fail_closed_provenance), effective_venue=125(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_runtime_target_attach` count=`10698` routing=`reviewed_unknown_token_provenance` fields=`venue=2102(reviewed_scanner_venue_fail_closed_provenance), effective_venue=2102(reviewed_scanner_venue_fail_closed_provenance)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`7079` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=2147(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_candidate_deferred` count=`4508` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=329(reviewed_rising_missed_nxt_eligibility_not_available)`
- `strength_momentum_observed` count=`2951` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=3(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_candidate_blocked` count=`2571` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1818(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalping_scanner_watch_eviction` count=`2510` routing=`reviewed_unknown_token_provenance` fields=`venue=2510(reviewed_observation_only_venue_not_available), effective_venue=2510(reviewed_observation_only_venue_not_available)`
- `blocked_strength_momentum` count=`2348` routing=`reviewed_unknown_token_provenance` fields=`venue=34(reviewed_scanner_venue_fail_closed_provenance), effective_venue=34(reviewed_scanner_venue_fail_closed_provenance), rising_missed_nxt_eligible=1(reviewed_rising_missed_nxt_eligibility_not_available)`
- `prev_close_gainer_entry_ai_handoff` count=`1730` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=262(reviewed_rising_missed_nxt_eligibility_not_available)`
- `opening_rotation_1pct_observed` count=`1066` routing=`reviewed_unknown_token_provenance` fields=`venue=41(reviewed_scanner_venue_fail_closed_provenance), effective_venue=41(reviewed_scanner_venue_fail_closed_provenance), scanner_promotion_reanchor_effective_venue=41(reviewed_scanner_venue_fail_closed_provenance), opening_rotation_no_pullback_continuation_effective_venue=41(reviewed_scanner_venue_fail_closed_provenance), rising_missed_nxt_eligible=2(reviewed_rising_missed_nxt_eligibility_not_available)`
- `opening_rotation_1pct_upstream_blocked` count=`929` routing=`reviewed_unknown_token_provenance` fields=`venue=64(reviewed_scanner_venue_fail_closed_provenance), effective_venue=64(reviewed_scanner_venue_fail_closed_provenance), rising_missed_nxt_eligible=2(reviewed_rising_missed_nxt_eligibility_not_available)`
- `scalp_entry_action_decision_snapshot` count=`910` routing=`reviewed_unknown_token_provenance` fields=`holding_exit_matrix_score_prior_band=538(reviewed_score_prior_neutral_unknown_not_decision_input), rising_missed_nxt_eligible=297(reviewed_rising_missed_nxt_eligibility_not_available), risk_regime_context=165(reviewed_missing_risk_regime_context), entry_order_flow_status=122(reviewed_entry_order_flow_not_available), score_prior_band=84(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=84(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=59(reviewed_entry_score_source_not_available), entry_score_excluded_reason=59(reviewed_entry_score_source_not_available)`
- `rising_missed_one_share_entry` count=`744` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=682(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=3(reviewed_explicit_sizing_unknown_venue_fallback)`
- `stat_action_decision_snapshot` count=`610` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=4(reviewed_stale_flag_not_available), quote_stale=4(reviewed_stale_flag_not_available)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `94286`
- `rising_missed_watch_not_rising_skipped`: `79639`
- `scalping_scanner_fast_precheck`: `56650`
- `scalping_scanner_heavy_eval_lag`: `37636`
- `scalping_scanner_runtime_queue_lag`: `31125`
- `rising_missed_nxt_post_block_price_sample`: `19038`
- `scalping_scanner_watching_runtime_skip`: `14384`
- `scalping_scanner_runtime_target_attach`: `10698`
- `rising_missed_tp1_counterfactual_submit_safety`: `7079`
- `scalping_scanner_candidate_observed`: `4564`
- `scalping_scanner_real_source_guard_block`: `4564`
- `rising_missed_tp1_candidate_deferred`: `4508`
- `rising_missed_nxt_post_block_sampler_registration_skipped`: `4079`
- `strength_momentum_observed`: `2951`
- `scalping_scanner_candidate_promoted`: `2865`
- `rising_missed_tp1_candidate_blocked`: `2571`
- `scalping_scanner_watch_eviction`: `2510`
- `blocked_strength_momentum`: `2348`
- `prev_close_gainer_entry_ai_handoff`: `1730`
- `blocked_overbought`: `1721`

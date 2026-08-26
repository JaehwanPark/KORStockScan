# Observation Source Quality Audit - 2026-08-26

- status: `fail`
- event_count: `134586`
- tuning_input_policy: `exclude_defective_rows_not_full_day_raw`
- hard_blocking_excluded_row_count: `37`
- pre_exclusion_hard_blocking_excluded_row_count: `37`
- current_scan_hard_blocking_excluded_row_count: `37`
- post_exclusion_hard_blocking_excluded_row_count: `37`
- raw_row_exclusion_applied: `False`
- raw_row_exclusion_deferred_writer_active: `True`
- raw_row_exclusion_revalidation_required: `False`
- tuning_input_allowed: `False`
- decision_authority: `source_quality_only`
- runtime_effect: `False`
- forbidden_uses: `runtime_threshold_apply, order_submit, provider_route_change, bot_restart, real_execution_quality_approval`

## Warning Stages
- `scalp_entry_action_decision_snapshot` sample=`1133` missing=`{}` zero=`{}`
- `blocked_ai_score` sample=`206` missing=`{}` zero=`{'distance_from_day_high_pct': 0.1456}`

## Hard Blocking Row Exclusions
- line=`28108` stage=`blocked_ai_score` code=`069540` missing=`[]` zero=`['distance_from_day_high_pct']` invalid=`[]`
- line=`34778` stage=`blocked_ai_score` code=`388050` missing=`[]` zero=`['distance_from_day_high_pct']` invalid=`[]`
- line=`36067` stage=`blocked_ai_score` code=`189860` missing=`[]` zero=`['distance_from_day_high_pct']` invalid=`[]`
- line=`41707` stage=`blocked_ai_score` code=`039610` missing=`[]` zero=`['distance_from_day_high_pct']` invalid=`[]`
- line=`44352` stage=`blocked_ai_score` code=`375500` missing=`[]` zero=`['distance_from_day_high_pct']` invalid=`[]`
- line=`46767` stage=`blocked_ai_score` code=`375500` missing=`[]` zero=`['distance_from_day_high_pct']` invalid=`[]`
- line=`53482` stage=`blocked_ai_score` code=`000100` missing=`[]` zero=`['distance_from_day_high_pct']` invalid=`[]`
- line=`54707` stage=`blocked_ai_score` code=`096530` missing=`[]` zero=`['distance_from_day_high_pct']` invalid=`[]`
- line=`56325` stage=`scalp_entry_action_decision_snapshot` code=`196170` missing=`[]` zero=`[]` invalid=`['minute_candle_window_fresh_contract']`
- line=`57783` stage=`blocked_ai_score` code=`375500` missing=`[]` zero=`['distance_from_day_high_pct']` invalid=`[]`
- line=`60652` stage=`blocked_ai_score` code=`096530` missing=`[]` zero=`['distance_from_day_high_pct']` invalid=`[]`
- line=`61018` stage=`blocked_ai_score` code=`037440` missing=`[]` zero=`['distance_from_day_high_pct']` invalid=`[]`
- line=`61890` stage=`blocked_ai_score` code=`047040` missing=`[]` zero=`['distance_from_day_high_pct']` invalid=`[]`
- line=`63778` stage=`blocked_ai_score` code=`375500` missing=`[]` zero=`['distance_from_day_high_pct']` invalid=`[]`
- line=`74477` stage=`scalp_entry_action_decision_snapshot` code=`088350` missing=`[]` zero=`[]` invalid=`['minute_candle_window_fresh_contract']`
- line=`78590` stage=`blocked_ai_score` code=`064800` missing=`[]` zero=`['distance_from_day_high_pct']` invalid=`[]`
- line=`79194` stage=`blocked_ai_score` code=`088350` missing=`[]` zero=`['distance_from_day_high_pct']` invalid=`[]`
- line=`80573` stage=`blocked_ai_score` code=`088350` missing=`[]` zero=`['distance_from_day_high_pct']` invalid=`[]`
- line=`84571` stage=`blocked_ai_score` code=`103590` missing=`[]` zero=`['distance_from_day_high_pct']` invalid=`[]`
- line=`84781` stage=`blocked_ai_score` code=`950260` missing=`[]` zero=`['distance_from_day_high_pct']` invalid=`[]`
- line=`85265` stage=`blocked_ai_score` code=`088350` missing=`[]` zero=`['distance_from_day_high_pct']` invalid=`[]`
- line=`89227` stage=`blocked_ai_score` code=`200470` missing=`[]` zero=`['distance_from_day_high_pct']` invalid=`[]`
- line=`89857` stage=`blocked_ai_score` code=`088350` missing=`[]` zero=`['distance_from_day_high_pct']` invalid=`[]`
- line=`90952` stage=`blocked_ai_score` code=`088350` missing=`[]` zero=`['distance_from_day_high_pct']` invalid=`[]`
- line=`100975` stage=`blocked_ai_score` code=`088350` missing=`[]` zero=`['distance_from_day_high_pct']` invalid=`[]`
- line=`102091` stage=`blocked_ai_score` code=`088350` missing=`[]` zero=`['distance_from_day_high_pct']` invalid=`[]`
- line=`104506` stage=`blocked_ai_score` code=`103590` missing=`[]` zero=`['distance_from_day_high_pct']` invalid=`[]`
- line=`106830` stage=`scalp_entry_action_decision_snapshot` code=`336260` missing=`[]` zero=`[]` invalid=`['minute_candle_window_fresh_contract']`
- line=`106834` stage=`blocked_ai_score` code=`336260` missing=`[]` zero=`['distance_from_day_high_pct']` invalid=`[]`
- line=`106836` stage=`scalp_entry_action_decision_snapshot` code=`336260` missing=`[]` zero=`[]` invalid=`['minute_candle_window_fresh_contract']`
- line=`108383` stage=`scalp_entry_action_decision_snapshot` code=`373110` missing=`[]` zero=`[]` invalid=`['minute_candle_window_fresh_contract']`
- line=`108388` stage=`scalp_entry_action_decision_snapshot` code=`373110` missing=`[]` zero=`[]` invalid=`['minute_candle_window_fresh_contract']`
- line=`113495` stage=`blocked_ai_score` code=`078340` missing=`[]` zero=`['distance_from_day_high_pct']` invalid=`[]`
- line=`115907` stage=`blocked_ai_score` code=`000100` missing=`[]` zero=`['distance_from_day_high_pct']` invalid=`[]`
- line=`116862` stage=`blocked_ai_score` code=`000100` missing=`[]` zero=`['distance_from_day_high_pct']` invalid=`[]`
- line=`120638` stage=`scalp_entry_action_decision_snapshot` code=`130660` missing=`[]` zero=`[]` invalid=`['minute_candle_window_fresh_contract']`
- line=`132286` stage=`blocked_ai_score` code=`413630` missing=`[]` zero=`['distance_from_day_high_pct']` invalid=`[]`

## Invalid Label Findings
- none

## High Volume Stages Without Source-Like Fields
- none

## Unknown Token Findings
- none

## Reviewed Unknown Token Findings
- `scalping_scanner_promotion_latency_trace` count=`30075` routing=`reviewed_unknown_token_provenance` fields=`venue=2(reviewed_scanner_venue_fail_closed_provenance), effective_venue=2(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_fast_precheck` count=`22648` routing=`reviewed_unknown_token_provenance` fields=`scanner_stale_backoff_raw_0b_route=509(reviewed_scanner_stale_backoff_route_not_available), scanner_stale_backoff_raw_0d_route=241(reviewed_scanner_stale_backoff_route_not_available), venue=1(reviewed_scanner_venue_fail_closed_provenance), effective_venue=1(reviewed_scanner_venue_fail_closed_provenance), scanner_promotion_reanchor_effective_venue=1(reviewed_scanner_venue_fail_closed_provenance), scanner_stale_backoff_canonical_effective_venue=1(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_runtime_queue_lag` count=`13597` routing=`reviewed_unknown_token_provenance` fields=`venue=1(reviewed_scanner_venue_fail_closed_provenance), effective_venue=1(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_heavy_eval_completion` count=`7552` routing=`reviewed_unknown_token_provenance` fields=`venue=1(reviewed_scanner_venue_fail_closed_provenance), effective_venue=1(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_heavy_eval_lag` count=`7427` routing=`reviewed_unknown_token_provenance` fields=`venue=1(reviewed_scanner_venue_fail_closed_provenance), effective_venue=1(reviewed_scanner_venue_fail_closed_provenance)`
- `scalping_scanner_watching_runtime_skip` count=`4331` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=674(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=49(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=49(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=49(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_watch_not_rising_skipped` count=`4234` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=4234(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_tp1_counterfactual_submit_safety` count=`1242` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1242(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=4(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=4(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=4(reviewed_explicit_sizing_unknown_venue_fallback)`
- `scalp_entry_action_decision_snapshot` count=`1133` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=880(reviewed_rising_missed_nxt_eligibility_not_available), holding_exit_matrix_score_prior_band=328(reviewed_score_prior_neutral_unknown_not_decision_input), entry_order_flow_status=129(reviewed_entry_order_flow_not_available), score_prior_band=45(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=45(reviewed_score_prior_neutral_unknown_not_decision_input), tier_reason=32(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=32(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=32(reviewed_explicit_sizing_unknown_venue_fallback)`
- `rising_missed_tp1_candidate_blocked` count=`1070` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=1070(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=3(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=3(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=3(reviewed_explicit_sizing_unknown_venue_fallback)`
- `reversal_add_blocked_reason` count=`978` routing=`reviewed_unknown_token_provenance` fields=`shallow_tick_context_stale=1(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=1(reviewed_shallow_stale_flag_not_available), tick_context_stale=1(reviewed_stale_flag_not_available), quote_stale=1(reviewed_stale_flag_not_available)`
- `stat_action_decision_snapshot` count=`927` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=14(reviewed_stale_flag_not_available), quote_stale=14(reviewed_stale_flag_not_available), shallow_tick_context_stale=1(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=1(reviewed_shallow_stale_flag_not_available)`
- `strength_momentum_observed` count=`847` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=27(reviewed_rising_missed_nxt_eligibility_not_available)`
- `rising_missed_one_share_entry` count=`716` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=716(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=6(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=6(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=6(reviewed_explicit_sizing_unknown_venue_fallback), venue=1(reviewed_rising_missed_explicit_venue_conflict), effective_venue=1(reviewed_rising_missed_explicit_venue_conflict)`
- `budget_pass` count=`652` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=652(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=30(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=30(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=30(reviewed_explicit_sizing_unknown_venue_fallback)`
- `orderbook_stability_observed` count=`652` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=652(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=30(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=30(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=30(reviewed_explicit_sizing_unknown_venue_fallback)`
- `blocked_strength_momentum` count=`640` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=24(reviewed_rising_missed_nxt_eligibility_not_available)`
- `ai_holding_review` count=`538` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=16(reviewed_entry_order_flow_not_available)`
- `risky_micro_episode_source_candidate_observed` count=`499` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=499(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=26(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=26(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=26(reviewed_explicit_sizing_unknown_venue_fallback)`
- `latency_block` count=`417` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_nxt_eligible=417(reviewed_rising_missed_nxt_eligibility_not_available), tier_reason=18(reviewed_explicit_sizing_unknown_venue_fallback), sizing_venue_at_allocation=18(reviewed_explicit_sizing_unknown_venue_fallback), sizing_tier_reason_at_allocation=18(reviewed_explicit_sizing_unknown_venue_fallback)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `30075`
- `scalping_scanner_fast_precheck`: `22648`
- `scalping_scanner_runtime_queue_lag`: `13597`
- `scalping_scanner_runtime_target_attach`: `8901`
- `risky_micro_episode_executable_bbo_observed`: `7567`
- `scalping_scanner_heavy_eval_completion`: `7552`
- `scalping_scanner_heavy_eval_lag`: `7427`
- `scalping_scanner_watching_runtime_skip`: `4331`
- `rising_missed_watch_not_rising_skipped`: `4234`
- `scalping_scanner_candidate_observed`: `2299`
- `scalping_scanner_real_source_guard_block`: `2299`
- `scalp_sim_scale_in_candidate_funnel`: `1815`
- `bad_entry_refined_candidate`: `1715`
- `rising_missed_tp1_counterfactual_submit_safety`: `1242`
- `scalping_scanner_candidate_promoted`: `1238`
- `scalp_entry_action_decision_snapshot`: `1133`
- `scalping_scanner_watch_eviction`: `1071`
- `rising_missed_tp1_candidate_blocked`: `1070`
- `reversal_add_blocked_reason`: `978`
- `stat_action_decision_snapshot`: `927`

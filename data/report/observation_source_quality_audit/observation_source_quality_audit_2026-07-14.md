# Observation Source Quality Audit - 2026-07-14

- status: `pass`
- event_count: `104805`
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
- `scalping_scanner_fast_precheck` count=`8585` routing=`reviewed_unknown_token_provenance` fields=`rising_missed_submit_safety_backoff_reason=33(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `stat_action_decision_snapshot` count=`748` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=26(reviewed_stale_flag_not_available), quote_stale=26(reviewed_stale_flag_not_available), shallow_tick_context_stale=26(reviewed_shallow_stale_flag_not_available), shallow_quote_stale=26(reviewed_shallow_stale_flag_not_available)`
- `ai_holding_review` count=`725` routing=`reviewed_unknown_token_provenance` fields=`holding_score_preflight_source_quality=724(reviewed_holding_score_preflight_not_available), entry_order_flow_status=344(reviewed_entry_order_flow_not_available)`
- `scalp_entry_action_decision_snapshot` count=`137` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=76(reviewed_entry_order_flow_not_available), holding_exit_matrix_score_prior_band=63(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_band=32(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=32(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=21(reviewed_entry_score_source_not_available), entry_score_excluded_reason=21(reviewed_entry_score_source_not_available), risk_regime_context=2(reviewed_missing_risk_regime_context)`
- `ai_confirmed_terminal_no_budget` count=`62` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=33(reviewed_entry_order_flow_not_available), score_prior_band=32(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=32(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=21(reviewed_entry_score_source_not_available), entry_score_excluded_reason=21(reviewed_entry_score_source_not_available)`
- `real_weak_ai_micro_entry_block` count=`60` routing=`reviewed_unknown_token_provenance` fields=`reason=60(reviewed_entry_block_source_quality_unknown_provenance), block_reason=60(reviewed_entry_block_source_quality_unknown_provenance), rising_missed_submit_safety_backoff_reason=60(reviewed_rising_missed_submit_safety_backoff_source_quality_provenance)`
- `ai_confirmed` count=`42` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=22(reviewed_entry_order_flow_not_available)`
- `blocked_ai_score` count=`37` routing=`reviewed_unknown_token_provenance` fields=`score_prior_band=25(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=25(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=21(reviewed_entry_score_source_not_available), entry_score_excluded_reason=21(reviewed_entry_score_source_not_available), entry_order_flow_status=15(reviewed_entry_order_flow_not_available)`
- `rising_missed_tick_speed_entry_block` count=`11` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=9(reviewed_entry_order_flow_not_available)`
- `scalp_sim_panic_context_warning` count=`10` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=10(reviewed_missing_risk_regime_context), market_risk_state=10(reviewed_missing_risk_regime_context), liquidity_state=10(reviewed_missing_risk_regime_context), risk_regime_epoch_id=10(reviewed_missing_risk_regime_context)`
- `order_leg_request` count=`9` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=2(reviewed_missing_risk_regime_context)`
- `order_bundle_submitted` count=`5` routing=`reviewed_unknown_token_provenance` fields=`latency_danger_reasons=5(reviewed_pre_contract_placeholder), latency_danger_detail_reason=5(reviewed_pre_contract_placeholder), latency_danger_source_quality_state=5(reviewed_pre_contract_placeholder), latency_danger_reason_taxonomy_gap=5(reviewed_pre_contract_placeholder), latency_danger_max_ws_age_ms_for_caution=5(reviewed_pre_contract_placeholder), latency_danger_max_ws_jitter_ms_for_caution=5(reviewed_pre_contract_placeholder), latency_danger_max_spread_ratio_for_caution=5(reviewed_pre_contract_placeholder), latency_danger_guard_max_spread_ratio=5(reviewed_pre_contract_placeholder)`
- `pre_submit_entry_ai_authority_guard_block` count=`1` routing=`reviewed_unknown_token_provenance` fields=`entry_order_flow_status=1(reviewed_entry_order_flow_not_available)`

## Top Stages
- `scalping_scanner_candidate_observed`: `19491`
- `scalping_scanner_real_source_guard_block`: `19491`
- `scalping_scanner_promotion_latency_trace`: `11633`
- `scalping_scanner_runtime_target_attach`: `8646`
- `scalping_scanner_fast_precheck`: `8585`
- `scalping_scanner_runtime_queue_lag`: `7055`
- `scalping_scanner_watching_runtime_skip`: `6981`
- `scalping_scanner_heavy_eval_lag`: `3048`
- `scalping_scanner_candidate_promoted`: `2929`
- `scalping_scanner_watch_eviction`: `2747`
- `rising_missed_watch_not_rising_skipped`: `2460`
- `bad_entry_refined_candidate`: `1493`
- `manual_control_excluded_symbol_blocked`: `1076`
- `rising_missed_nxt_post_block_price_sample`: `822`
- `ai_holding_fast_reuse_band`: `751`
- `stat_action_decision_snapshot`: `748`
- `ai_holding_reuse_bypass`: `725`
- `ai_holding_review`: `725`
- `rising_missed_tp1_candidate_blocked`: `669`
- `scale_in_feature_context_refresh`: `618`

# Observation Source Quality Audit - 2026-07-07

- status: `pass`
- event_count: `103175`
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
- `scalping_scanner_watching_runtime_skip` count=`10259` routing=`reviewed_unknown_token_provenance` fields=`minute_candle_context_quality=8(reviewed_runtime_skip_context_not_evaluated), tick_context_quality=8(reviewed_runtime_skip_context_not_evaluated), tick_context_stale=8(reviewed_stale_flag_not_available)`
- `stat_action_decision_snapshot` count=`2924` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=88(reviewed_stale_flag_not_available), quote_stale=88(reviewed_stale_flag_not_available)`
- `scalp_sim_panic_context_warning` count=`2269` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=2269(reviewed_missing_risk_regime_context), market_risk_state=2269(reviewed_missing_risk_regime_context), liquidity_state=2269(reviewed_missing_risk_regime_context), risk_regime_epoch_id=2269(reviewed_missing_risk_regime_context)`
- `ai_holding_review` count=`1448` routing=`reviewed_unknown_token_provenance` fields=`holding_score_preflight_source_quality=1424(reviewed_holding_score_preflight_not_available)`
- `scalp_entry_action_decision_snapshot` count=`422` routing=`reviewed_unknown_token_provenance` fields=`holding_exit_matrix_score_prior_band=351(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_band=95(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=95(reviewed_score_prior_neutral_unknown_not_decision_input), risk_regime_context=44(reviewed_missing_risk_regime_context), entry_score_source=20(reviewed_entry_score_source_not_available), entry_score_excluded_reason=20(reviewed_entry_score_source_not_available)`
- `ai_confirmed_terminal_no_budget` count=`299` routing=`reviewed_unknown_token_provenance` fields=`score_prior_band=127(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=127(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=52(reviewed_entry_score_source_not_available), entry_score_excluded_reason=52(reviewed_entry_score_source_not_available)`
- `blocked_ai_score` count=`233` routing=`reviewed_unknown_token_provenance` fields=`score_prior_band=127(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=127(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=52(reviewed_entry_score_source_not_available), entry_score_excluded_reason=52(reviewed_entry_score_source_not_available)`
- `soft_stop_micro_grace` count=`108` routing=`reviewed_unknown_token_provenance` fields=`soft_stop_dynamic_grace_score_prior_band=41(reviewed_score_prior_neutral_unknown_not_decision_input)`
- `loss_fallback_probe` count=`90` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=73(reviewed_stale_flag_not_available), quote_stale=73(reviewed_stale_flag_not_available)`
- `early_accel_recheck_evaluated` count=`83` routing=`reviewed_unknown_token_provenance` fields=`tick_accel_source=83(reviewed_unusable_micro_context_not_available), tick_context_quality=83(reviewed_unusable_micro_context_not_available), minute_candle_context_quality=83(reviewed_unusable_micro_context_not_available)`
- `early_accel_recheck_skipped` count=`83` routing=`reviewed_unknown_token_provenance` fields=`tick_accel_source=83(reviewed_unusable_micro_context_not_available), tick_context_quality=83(reviewed_unusable_micro_context_not_available), minute_candle_context_quality=83(reviewed_unusable_micro_context_not_available)`
- `latency_pass` count=`43` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=41(reviewed_pre_submit_liquidity_not_available)`
- `order_bundle_submitted` count=`42` routing=`reviewed_unknown_token_provenance` fields=`latency_strategy_id=42(reviewed_pre_contract_placeholder), latency_position_tag=42(reviewed_pre_contract_placeholder), latency_spread_relief_tag=42(reviewed_pre_contract_placeholder), latency_spread_relief_signal_score=42(reviewed_pre_contract_placeholder), latency_spread_relief_configured_min_signal_score=42(reviewed_pre_contract_placeholder), latency_spread_relief_effective_min_signal_score=42(reviewed_pre_contract_placeholder), filled_qty=42(reviewed_pre_contract_placeholder), remaining_qty=42(reviewed_pre_contract_placeholder)`
- `order_leg_request` count=`42` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=41(reviewed_pre_submit_liquidity_not_available), risk_regime_context=26(reviewed_missing_risk_regime_context)`
- `order_leg_sent` count=`42` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=41(reviewed_pre_submit_liquidity_not_available)`
- `stop_line_touch_first_touch_avgdown_decision_blocked` count=`35` routing=`reviewed_unknown_token_provenance` fields=`first_touch_quote_stale=1(reviewed_first_touch_quote_stale_not_available)`
- `scale_in_qty_block` count=`28` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=12(reviewed_stale_flag_not_available), quote_stale=12(reviewed_stale_flag_not_available)`
- `sell_order_sent` count=`22` routing=`reviewed_unknown_token_provenance` fields=`sell_order_exchange_resolution_reason=12(reviewed_sell_order_exchange_resolution_not_available)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `16393`
- `scalping_scanner_fast_precheck`: `14462`
- `scalping_scanner_watching_runtime_skip`: `10259`
- `scalping_scanner_runtime_queue_lag`: `10097`
- `scalping_scanner_runtime_target_attach`: `8657`
- `bad_entry_refined_candidate`: `3912`
- `stat_action_decision_snapshot`: `2924`
- `holding_ws_freshness_blocked`: `2357`
- `rising_missed_scout_upgrade_eval`: `2330`
- `manual_control_excluded_symbol_blocked`: `2269`
- `scalp_sim_panic_context_warning`: `2269`
- `scalping_scanner_heavy_eval_lag`: `1931`
- `scalping_scanner_candidate_observed`: `1498`
- `scalping_scanner_real_source_guard_block`: `1498`
- `ai_holding_fast_reuse_band`: `1462`
- `ai_holding_reuse_bypass`: `1453`
- `ai_holding_review`: `1448`
- `scale_in_feature_context_refresh`: `1394`
- `scalp_sim_scale_in_candidate_funnel`: `1108`
- `strength_momentum_observed`: `965`

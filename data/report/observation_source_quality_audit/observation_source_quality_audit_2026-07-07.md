# Observation Source Quality Audit - 2026-07-07

- status: `warning`
- event_count: `55774`
- tuning_input_policy: `exclude_defective_rows_not_full_day_raw`
- hard_blocking_excluded_row_count: `1`
- tuning_input_allowed: `False`
- decision_authority: `source_quality_only`
- runtime_effect: `False`
- forbidden_uses: `runtime_threshold_apply, order_submit, provider_route_change, bot_restart, real_execution_quality_approval`

## Warning Stages
- `reversal_add_blocked_reason` sample=`1` missing=`{'minute_candle_latest_age_ms': 1.0}` zero=`{}`

## Hard Blocking Row Exclusions
- line=`55719` stage=`reversal_add_blocked_reason` code=`200710` missing=`['minute_candle_latest_age_ms']` zero=`[]` invalid=`[]`

## Invalid Label Findings
- none

## High Volume Stages Without Source-Like Fields
- none

## Unknown Token Findings
- `stop_line_touch_first_touch_avgdown_decision_blocked` count=`35` routing=`source_quality_blocker_or_provenance_backfill` fields=`first_touch_quote_stale=1(0.0286)`
- `reversal_add_blocked_reason` count=`1` routing=`source_quality_blocker_or_provenance_backfill` fields=`state=1(1.0)`

## Reviewed Unknown Token Findings
- `scalping_scanner_watching_runtime_skip` count=`5967` routing=`reviewed_unknown_token_provenance` fields=`minute_candle_context_quality=3(reviewed_runtime_skip_context_not_evaluated), tick_context_quality=3(reviewed_runtime_skip_context_not_evaluated), tick_context_stale=3(reviewed_stale_flag_not_available)`
- `stat_action_decision_snapshot` count=`1091` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=76(reviewed_stale_flag_not_available), quote_stale=76(reviewed_stale_flag_not_available)`
- `ai_holding_review` count=`705` routing=`reviewed_unknown_token_provenance` fields=`holding_score_preflight_source_quality=682(reviewed_holding_score_preflight_not_available)`
- `scalp_entry_action_decision_snapshot` count=`348` routing=`reviewed_unknown_token_provenance` fields=`holding_exit_matrix_score_prior_band=292(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_band=73(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=73(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=13(reviewed_entry_score_source_not_available), entry_score_excluded_reason=13(reviewed_entry_score_source_not_available), risk_regime_context=10(reviewed_missing_risk_regime_context), liquidity_guard_action=2(reviewed_pre_submit_liquidity_not_available)`
- `scalp_sim_panic_context_warning` count=`306` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=306(reviewed_missing_risk_regime_context), market_risk_state=306(reviewed_missing_risk_regime_context), liquidity_state=306(reviewed_missing_risk_regime_context), risk_regime_epoch_id=306(reviewed_missing_risk_regime_context)`
- `ai_confirmed_terminal_no_budget` count=`224` routing=`reviewed_unknown_token_provenance` fields=`score_prior_band=80(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=80(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=20(reviewed_entry_score_source_not_available), entry_score_excluded_reason=20(reviewed_entry_score_source_not_available)`
- `blocked_ai_score` count=`164` routing=`reviewed_unknown_token_provenance` fields=`score_prior_band=80(reviewed_score_prior_neutral_unknown_not_decision_input), score_prior_confidence=80(reviewed_score_prior_neutral_unknown_not_decision_input), entry_score_source=20(reviewed_entry_score_source_not_available), entry_score_excluded_reason=20(reviewed_entry_score_source_not_available)`
- `soft_stop_micro_grace` count=`102` routing=`reviewed_unknown_token_provenance` fields=`soft_stop_dynamic_grace_score_prior_band=35(reviewed_score_prior_neutral_unknown_not_decision_input)`
- `loss_fallback_probe` count=`90` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=73(reviewed_stale_flag_not_available), quote_stale=73(reviewed_stale_flag_not_available)`
- `early_accel_recheck_evaluated` count=`37` routing=`reviewed_unknown_token_provenance` fields=`tick_accel_source=37(reviewed_unusable_micro_context_not_available), tick_context_quality=37(reviewed_unusable_micro_context_not_available), minute_candle_context_quality=37(reviewed_unusable_micro_context_not_available)`
- `early_accel_recheck_skipped` count=`37` routing=`reviewed_unknown_token_provenance` fields=`tick_accel_source=37(reviewed_unusable_micro_context_not_available), tick_context_quality=37(reviewed_unusable_micro_context_not_available), minute_candle_context_quality=37(reviewed_unusable_micro_context_not_available)`
- `latency_pass` count=`20` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=18(reviewed_pre_submit_liquidity_not_available)`
- `order_bundle_submitted` count=`19` routing=`reviewed_unknown_token_provenance` fields=`latency_strategy_id=19(reviewed_pre_contract_placeholder), latency_position_tag=19(reviewed_pre_contract_placeholder), latency_spread_relief_tag=19(reviewed_pre_contract_placeholder), latency_spread_relief_signal_score=19(reviewed_pre_contract_placeholder), latency_spread_relief_configured_min_signal_score=19(reviewed_pre_contract_placeholder), latency_spread_relief_effective_min_signal_score=19(reviewed_pre_contract_placeholder), filled_qty=19(reviewed_pre_contract_placeholder), remaining_qty=19(reviewed_pre_contract_placeholder)`
- `order_leg_request` count=`19` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=18(reviewed_pre_submit_liquidity_not_available), risk_regime_context=5(reviewed_missing_risk_regime_context)`
- `order_leg_sent` count=`19` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=18(reviewed_pre_submit_liquidity_not_available)`
- `sell_order_sent` count=`15` routing=`reviewed_unknown_token_provenance` fields=`sell_order_exchange_resolution_reason=6(reviewed_sell_order_exchange_resolution_not_available)`
- `scale_in_qty_block` count=`9` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=5(reviewed_stale_flag_not_available), quote_stale=5(reviewed_stale_flag_not_available)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `10920`
- `scalping_scanner_fast_precheck`: `9305`
- `scalping_scanner_watching_runtime_skip`: `5967`
- `scalping_scanner_runtime_queue_lag`: `5585`
- `scalping_scanner_runtime_target_attach`: `3596`
- `scalping_scanner_heavy_eval_lag`: `1615`
- `bad_entry_refined_candidate`: `1319`
- `manual_control_excluded_symbol_blocked`: `1179`
- `scalping_scanner_candidate_observed`: `1107`
- `scalping_scanner_real_source_guard_block`: `1107`
- `stat_action_decision_snapshot`: `1091`
- `holding_ws_freshness_blocked`: `1033`
- `ai_holding_fast_reuse_band`: `710`
- `ai_holding_reuse_bypass`: `709`
- `ai_holding_review`: `705`
- `strength_momentum_observed`: `615`
- `scalp_sim_panic_scale_in_blocked`: `613`
- `blocked_strength_momentum`: `557`
- `scalp_sim_ai_holding_live_call`: `366`
- `scalp_entry_action_decision_snapshot`: `348`

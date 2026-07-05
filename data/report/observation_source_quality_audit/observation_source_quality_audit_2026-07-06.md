# Observation Source Quality Audit - 2026-07-06

- status: `fail`
- event_count: `11096`
- tuning_input_policy: `exclude_defective_rows_not_full_day_raw`
- hard_blocking_excluded_row_count: `1`
- tuning_input_allowed: `False`
- decision_authority: `source_quality_only`
- runtime_effect: `False`
- forbidden_uses: `runtime_threshold_apply, order_submit, provider_route_change, bot_restart, real_execution_quality_approval`

## Warning Stages
- `reversal_add_blocked_reason` sample=`1` missing=`{'state': 1.0, 'micro_vwap_available': 1.0, 'minute_candle_context_quality': 1.0, 'minute_candle_window_fresh': 1.0, 'minute_candle_latest_age_ms': 1.0}` zero=`{}`

## Hard Blocking Row Exclusions
- line=`11031` stage=`reversal_add_blocked_reason` code=`200710` missing=`['state', 'micro_vwap_available', 'minute_candle_context_quality', 'minute_candle_window_fresh', 'minute_candle_latest_age_ms']` zero=`[]` invalid=`['minute_candle_window_fresh_contract']`

## Invalid Label Findings
- none

## High Volume Stages Without Source-Like Fields
- none

## Unknown Token Findings
- `scalp_entry_action_decision_snapshot` count=`17` routing=`source_quality_blocker_or_provenance_backfill` fields=`entry_score_source=8(0.4706), entry_score_excluded_reason=8(0.4706)`
- `ai_confirmed_terminal_no_budget` count=`15` routing=`source_quality_blocker_or_provenance_backfill` fields=`entry_score_source=12(0.8), entry_score_excluded_reason=12(0.8)`
- `blocked_ai_score` count=`13` routing=`source_quality_blocker_or_provenance_backfill` fields=`entry_score_source=12(0.9231), entry_score_excluded_reason=12(0.9231)`
- `early_accel_recheck_evaluated` count=`12` routing=`source_quality_blocker_or_provenance_backfill` fields=`tick_accel_source=12(1.0), tick_context_quality=12(1.0), minute_candle_context_quality=12(1.0)`
- `early_accel_recheck_skipped` count=`12` routing=`source_quality_blocker_or_provenance_backfill` fields=`tick_accel_source=12(1.0), tick_context_quality=12(1.0), minute_candle_context_quality=12(1.0)`

## Reviewed Unknown Token Findings
- `stat_action_decision_snapshot` count=`222` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=84(reviewed_stale_flag_not_available), quote_stale=84(reviewed_stale_flag_not_available)`
- `scalp_sim_panic_context_warning` count=`189` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=189(reviewed_missing_risk_regime_context), market_risk_state=189(reviewed_missing_risk_regime_context), liquidity_state=189(reviewed_missing_risk_regime_context), risk_regime_epoch_id=189(reviewed_missing_risk_regime_context)`
- `scalp_entry_action_decision_snapshot` count=`17` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=5(reviewed_missing_risk_regime_context)`
- `scale_in_qty_block` count=`6` routing=`reviewed_unknown_token_provenance` fields=`tick_context_stale=5(reviewed_stale_flag_not_available), quote_stale=5(reviewed_stale_flag_not_available)`
- `latency_pass` count=`5` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=5(reviewed_pre_submit_liquidity_not_available)`
- `order_bundle_submitted` count=`5` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=5(reviewed_pre_submit_liquidity_not_available), risk_regime_context=5(reviewed_missing_risk_regime_context), latency_strategy_id=5(reviewed_pre_contract_placeholder), latency_position_tag=5(reviewed_pre_contract_placeholder), latency_spread_relief_tag=5(reviewed_pre_contract_placeholder), latency_spread_relief_signal_score=5(reviewed_pre_contract_placeholder), latency_spread_relief_configured_min_signal_score=5(reviewed_pre_contract_placeholder), latency_spread_relief_effective_min_signal_score=5(reviewed_pre_contract_placeholder)`
- `order_leg_request` count=`5` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=5(reviewed_pre_submit_liquidity_not_available), risk_regime_context=5(reviewed_missing_risk_regime_context)`
- `order_leg_sent` count=`5` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=5(reviewed_pre_submit_liquidity_not_available)`
- `sell_order_sent` count=`1` routing=`reviewed_unknown_token_provenance` fields=`sell_order_exchange_resolution_reason=1(reviewed_sell_order_exchange_resolution_not_available)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `2014`
- `scalping_scanner_fast_precheck`: `1615`
- `scalping_scanner_runtime_queue_lag`: `1058`
- `holding_ws_freshness_blocked`: `872`
- `scalping_scanner_runtime_target_attach`: `790`
- `scalping_scanner_watching_runtime_skip`: `749`
- `scalping_scanner_heavy_eval_lag`: `399`
- `bad_entry_refined_candidate`: `279`
- `rising_missed_one_share_entry`: `277`
- `budget_pass`: `277`
- `orderbook_stability_observed`: `277`
- `latency_block`: `272`
- `stat_action_decision_snapshot`: `222`
- `scalp_sim_panic_context_warning`: `189`
- `holding_ws_freshness_recovered`: `180`
- `scale_in_feature_context_refresh`: `153`
- `manual_control_excluded_symbol_blocked`: `145`
- `ai_holding_fast_reuse_band`: `122`
- `ai_holding_reuse_bypass`: `122`
- `ai_holding_review`: `122`

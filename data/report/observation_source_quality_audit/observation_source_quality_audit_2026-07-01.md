# Observation Source Quality Audit - 2026-07-01

- status: `pass`
- event_count: `156472`
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
- `scalp_sim_panic_context_warning` count=`3074` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=3074(reviewed_missing_risk_regime_context), market_risk_state=3074(reviewed_missing_risk_regime_context), liquidity_state=3074(reviewed_missing_risk_regime_context), risk_regime_epoch_id=3074(reviewed_missing_risk_regime_context)`
- `scalp_entry_action_decision_snapshot` count=`522` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=60(reviewed_missing_risk_regime_context), liquidity_guard_action=2(reviewed_pre_submit_liquidity_not_available)`
- `latency_pass` count=`138` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=134(reviewed_pre_submit_liquidity_not_available)`
- `order_leg_request` count=`87` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=85(reviewed_pre_submit_liquidity_not_available), risk_regime_context=38(reviewed_missing_risk_regime_context)`
- `order_leg_sent` count=`87` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=85(reviewed_pre_submit_liquidity_not_available)`
- `order_bundle_submitted` count=`86` routing=`reviewed_unknown_token_provenance` fields=`latency_strategy_id=86(reviewed_pre_contract_placeholder), latency_position_tag=86(reviewed_pre_contract_placeholder), latency_spread_relief_tag=86(reviewed_pre_contract_placeholder), latency_spread_relief_signal_score=86(reviewed_pre_contract_placeholder), latency_spread_relief_configured_min_signal_score=86(reviewed_pre_contract_placeholder), latency_spread_relief_effective_min_signal_score=86(reviewed_pre_contract_placeholder), filled_qty=86(reviewed_pre_contract_placeholder), remaining_qty=86(reviewed_pre_contract_placeholder)`
- `order_bundle_failed` count=`35` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=35(reviewed_pre_submit_liquidity_not_available)`
- `pre_submit_weak_context_late_entry_guard_block` count=`35` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=35(reviewed_pre_submit_liquidity_not_available)`
- `real_weak_pullback_entry_block` count=`16` routing=`reviewed_unknown_token_provenance` fields=`liquidity_guard_action=14(reviewed_pre_submit_liquidity_not_available), risk_regime_context=14(reviewed_missing_risk_regime_context)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `24978`
- `scalping_scanner_fast_precheck`: `22038`
- `scalping_scanner_runtime_queue_lag`: `15605`
- `scalping_scanner_watching_runtime_skip`: `14628`
- `bad_entry_refined_candidate`: `9451`
- `holding_ws_freshness_recovered`: `5891`
- `holding_ws_freshness_blocked`: `5752`
- `ai_holding_fast_reuse_band`: `4807`
- `stat_action_decision_snapshot`: `4806`
- `ai_holding_reuse_bypass`: `4803`
- `ai_holding_review`: `4801`
- `reversal_add_blocked_reason`: `3265`
- `scalp_sim_panic_context_warning`: `3074`
- `scalping_scanner_heavy_eval_lag`: `2940`
- `rising_missed_scout_upgrade_eval`: `1845`
- `scalp_sim_scale_in_candidate_funnel`: `1588`
- `holding_flow_override_force_exit`: `1283`
- `stop_line_touch_avg_down_rest_quote_only_confirmation_blocked`: `1275`
- `strength_momentum_observed`: `1222`
- `pyramid_blocked_reason`: `1139`

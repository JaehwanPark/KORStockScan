# Observation Source Quality Audit - 2026-06-25

- status: `pass`
- event_count: `188307`
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
- `scalp_sim_panic_context_warning` count=`1694` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=1694(reviewed_missing_risk_regime_context), market_risk_state=1694(reviewed_missing_risk_regime_context), liquidity_state=1694(reviewed_missing_risk_regime_context), risk_regime_epoch_id=1694(reviewed_missing_risk_regime_context)`
- `scalp_entry_action_decision_snapshot` count=`1492` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=469(reviewed_missing_risk_regime_context)`
- `order_leg_request` count=`11` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=7(reviewed_missing_risk_regime_context)`
- `order_bundle_submitted` count=`6` routing=`reviewed_unknown_token_provenance` fields=`latency_strategy_id=6(reviewed_pre_contract_placeholder), latency_position_tag=6(reviewed_pre_contract_placeholder), latency_spread_relief_tag=6(reviewed_pre_contract_placeholder), latency_spread_relief_signal_score=6(reviewed_pre_contract_placeholder), latency_spread_relief_configured_min_signal_score=6(reviewed_pre_contract_placeholder), latency_spread_relief_effective_min_signal_score=6(reviewed_pre_contract_placeholder), filled_qty=6(reviewed_pre_contract_placeholder), remaining_qty=6(reviewed_pre_contract_placeholder)`
- `real_weak_pullback_entry_block` count=`6` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=3(reviewed_missing_risk_regime_context)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `37391`
- `scalping_scanner_fast_precheck`: `30319`
- `scalping_scanner_watching_runtime_skip`: `21628`
- `scalping_scanner_runtime_queue_lag`: `18046`
- `scalping_scanner_candidate_observed`: `14665`
- `scalping_scanner_real_source_guard_block`: `14665`
- `scalping_scanner_heavy_eval_lag`: `7072`
- `scalping_scanner_runtime_target_attach`: `3509`
- `strength_momentum_observed`: `3096`
- `bad_entry_refined_candidate`: `3071`
- `scalping_scanner_candidate_promoted`: `2475`
- `blocked_strength_momentum`: `1986`
- `stat_action_decision_snapshot`: `1925`
- `scalp_sim_panic_context_warning`: `1694`
- `scalp_entry_action_decision_snapshot`: `1492`
- `scalp_sim_panic_scale_in_blocked`: `1341`
- `holding_flow_override_force_exit`: `1328`
- `reversal_add_blocked_reason`: `1232`
- `loss_fallback_probe`: `988`
- `scalp_sim_scale_in_candidate_funnel`: `948`

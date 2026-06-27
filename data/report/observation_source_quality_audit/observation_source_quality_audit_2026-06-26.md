# Observation Source Quality Audit - 2026-06-26

- status: `pass`
- event_count: `246757`
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
- `scalp_sim_panic_context_warning` count=`1911` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=1911(reviewed_missing_risk_regime_context), market_risk_state=1911(reviewed_missing_risk_regime_context), liquidity_state=1911(reviewed_missing_risk_regime_context), risk_regime_epoch_id=1911(reviewed_missing_risk_regime_context)`
- `scalp_entry_action_decision_snapshot` count=`1558` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=359(reviewed_missing_risk_regime_context)`
- `lifecycle_decision_matrix_runtime_policy` count=`16` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=6(reviewed_missing_risk_regime_context)`
- `order_leg_request` count=`13` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=5(reviewed_missing_risk_regime_context)`
- `order_bundle_submitted` count=`10` routing=`reviewed_unknown_token_provenance` fields=`latency_strategy_id=10(reviewed_pre_contract_placeholder), latency_position_tag=10(reviewed_pre_contract_placeholder), latency_spread_relief_tag=10(reviewed_pre_contract_placeholder), latency_spread_relief_signal_score=10(reviewed_pre_contract_placeholder), latency_spread_relief_configured_min_signal_score=10(reviewed_pre_contract_placeholder), latency_spread_relief_effective_min_signal_score=10(reviewed_pre_contract_placeholder), filled_qty=10(reviewed_pre_contract_placeholder), remaining_qty=10(reviewed_pre_contract_placeholder)`
- `real_weak_pullback_entry_block` count=`3` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=1(reviewed_missing_risk_regime_context)`

## Top Stages
- `scalping_scanner_candidate_observed`: `51253`
- `scalping_scanner_real_source_guard_block`: `51253`
- `scalping_scanner_promotion_latency_trace`: `32309`
- `scalping_scanner_fast_precheck`: `27047`
- `scalping_scanner_runtime_queue_lag`: `19064`
- `scalping_scanner_watching_runtime_skip`: `16802`
- `scalping_scanner_heavy_eval_lag`: `5262`
- `bad_entry_refined_candidate`: `3809`
- `scalping_scanner_runtime_target_attach`: `2783`
- `strength_momentum_observed`: `2554`
- `stat_action_decision_snapshot`: `2073`
- `scalping_scanner_candidate_promoted`: `1990`
- `scalp_sim_panic_context_warning`: `1911`
- `scalp_sim_panic_scale_in_blocked`: `1667`
- `scalp_entry_action_decision_snapshot`: `1558`
- `holding_flow_override_force_exit`: `1350`
- `blocked_strength_momentum`: `1227`
- `ai_holding_fast_reuse_band`: `1159`
- `ai_holding_reuse_bypass`: `1157`
- `ai_holding_review`: `1134`

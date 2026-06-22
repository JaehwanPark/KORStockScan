# Observation Source Quality Audit - 2026-06-22

- status: `pass`
- event_count: `24110`
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
- `scalp_entry_action_decision_snapshot` count=`418` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=11(reviewed_missing_risk_regime_context)`
- `scalp_sim_panic_context_warning` count=`52` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=52(reviewed_missing_risk_regime_context), market_risk_state=52(reviewed_missing_risk_regime_context), liquidity_state=52(reviewed_missing_risk_regime_context), risk_regime_epoch_id=52(reviewed_missing_risk_regime_context)`
- `order_bundle_submitted` count=`1` routing=`reviewed_unknown_token_provenance` fields=`latency_strategy_id=1(reviewed_pre_contract_placeholder), latency_position_tag=1(reviewed_pre_contract_placeholder), latency_spread_relief_tag=1(reviewed_pre_contract_placeholder), latency_spread_relief_signal_score=1(reviewed_pre_contract_placeholder), latency_spread_relief_configured_min_signal_score=1(reviewed_pre_contract_placeholder), latency_spread_relief_effective_min_signal_score=1(reviewed_pre_contract_placeholder), filled_qty=1(reviewed_pre_contract_placeholder), remaining_qty=1(reviewed_pre_contract_placeholder)`

## Top Stages
- `scalping_scanner_candidate_observed`: `1833`
- `scalping_scanner_real_source_guard_block`: `1833`
- `scalping_scanner_fast_precheck`: `1797`
- `scalping_scanner_runtime_queue_lag`: `1792`
- `scalping_scanner_watching_runtime_skip`: `1081`
- `bad_entry_refined_candidate`: `875`
- `scalping_scanner_heavy_eval_lag`: `824`
- `stat_action_decision_snapshot`: `802`
- `scalp_sim_scale_in_candidate_funnel`: `801`
- `strength_momentum_observed`: `691`
- `blocked_strength_momentum`: `685`
- `ai_holding_fast_reuse_band`: `484`
- `ai_holding_reuse_bypass`: `484`
- `scalping_scanner_candidate_promoted`: `461`
- `scalp_entry_action_decision_snapshot`: `418`
- `scalping_scanner_runtime_target_attach`: `417`
- `scalp_sim_ai_holding_live_call`: `399`
- `ai_holding_review`: `399`
- `reversal_add_blocked_reason`: `396`
- `swing_probe_discarded`: `348`

# Observation Source Quality Audit - 2026-06-24

- status: `pass`
- event_count: `184175`
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
- `scalp_entry_action_decision_snapshot` count=`1435` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=357(reviewed_missing_risk_regime_context)`
- `scalp_sim_panic_context_warning` count=`1383` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=1383(reviewed_missing_risk_regime_context), market_risk_state=1383(reviewed_missing_risk_regime_context), liquidity_state=1383(reviewed_missing_risk_regime_context), risk_regime_epoch_id=1383(reviewed_missing_risk_regime_context)`
- `lifecycle_decision_matrix_runtime_policy` count=`12` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=1(reviewed_missing_risk_regime_context)`
- `order_bundle_submitted` count=`9` routing=`reviewed_unknown_token_provenance` fields=`latency_strategy_id=9(reviewed_pre_contract_placeholder), latency_position_tag=9(reviewed_pre_contract_placeholder), latency_spread_relief_tag=9(reviewed_pre_contract_placeholder), latency_spread_relief_signal_score=9(reviewed_pre_contract_placeholder), latency_spread_relief_configured_min_signal_score=9(reviewed_pre_contract_placeholder), latency_spread_relief_effective_min_signal_score=9(reviewed_pre_contract_placeholder), filled_qty=9(reviewed_pre_contract_placeholder), remaining_qty=9(reviewed_pre_contract_placeholder)`
- `order_leg_request` count=`9` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=1(reviewed_missing_risk_regime_context)`

## Top Stages
- `scalping_scanner_promotion_latency_trace`: `38492`
- `scalping_scanner_fast_precheck`: `34988`
- `scalping_scanner_watching_runtime_skip`: `24319`
- `scalping_scanner_runtime_queue_lag`: `20232`
- `scalping_scanner_heavy_eval_lag`: `10029`
- `scalping_scanner_candidate_observed`: `5158`
- `scalping_scanner_real_source_guard_block`: `5158`
- `strength_momentum_observed`: `4535`
- `bad_entry_refined_candidate`: `3282`
- `blocked_strength_momentum`: `2255`
- `scalping_scanner_candidate_promoted`: `2041`
- `scalping_scanner_runtime_target_attach`: `1918`
- `stat_action_decision_snapshot`: `1792`
- `strength_momentum_stability_recheck_pending`: `1729`
- `scalp_sim_panic_scale_in_blocked`: `1666`
- `scalping_scanner_watch_eviction`: `1514`
- `scalp_entry_action_decision_snapshot`: `1435`
- `scalp_sim_panic_context_warning`: `1383`
- `reversal_add_blocked_reason`: `1337`
- `loss_fallback_probe`: `954`

# Observation Source Quality Audit - 2026-06-17

- status: `pass`
- event_count: `18790`
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
- `scalp_entry_action_decision_snapshot` count=`591` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=2(reviewed_missing_risk_regime_context)`
- `lifecycle_decision_matrix_runtime_policy` count=`8` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=4(reviewed_missing_risk_regime_context)`
- `order_leg_request` count=`7` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=4(reviewed_missing_risk_regime_context)`
- `swing_sim_buy_order_assumed_filled` count=`6` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=4(reviewed_missing_risk_regime_context)`
- `swing_sim_order_bundle_assumed_filled` count=`6` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=4(reviewed_missing_risk_regime_context)`
- `scalp_sim_panic_context_warning` count=`3` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=3(reviewed_missing_risk_regime_context), market_risk_state=3(reviewed_missing_risk_regime_context), liquidity_state=3(reviewed_missing_risk_regime_context), risk_regime_epoch_id=3(reviewed_missing_risk_regime_context)`
- `order_bundle_submitted` count=`1` routing=`reviewed_unknown_token_provenance` fields=`filled_qty=1(reviewed_pre_contract_placeholder), remaining_qty=1(reviewed_pre_contract_placeholder), fill_quality=1(reviewed_pre_contract_placeholder)`

## Top Stages
- `bad_entry_refined_candidate`: `1078`
- `scalping_scanner_candidate_observed`: `1074`
- `scalp_sim_scale_in_candidate_funnel`: `929`
- `budget_pass`: `857`
- `orderbook_stability_observed`: `856`
- `latency_block`: `847`
- `stat_action_decision_snapshot`: `832`
- `market_regime_pass`: `826`
- `swing_entry_policy_evaluated`: `826`
- `swing_entry_micro_context_observed`: `824`
- `strength_momentum_observed`: `740`
- `blocked_strength_momentum`: `740`
- `scalp_entry_action_decision_snapshot`: `591`
- `blocked_swing_score_vpw`: `533`
- `reversal_add_blocked_reason`: `432`
- `ai_holding_fast_reuse_band`: `403`
- `ai_holding_reuse_bypass`: `403`
- `scalp_sim_ai_holding_live_call`: `304`
- `ai_holding_review`: `304`
- `blocked_gatekeeper_reject`: `293`

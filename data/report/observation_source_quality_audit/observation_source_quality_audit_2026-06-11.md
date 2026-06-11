# Observation Source Quality Audit - 2026-06-11

- status: `pass`
- event_count: `113544`
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
- `scalp_sim_panic_context_warning` count=`82` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=82(reviewed_missing_risk_regime_context), market_risk_state=82(reviewed_missing_risk_regime_context), liquidity_state=82(reviewed_missing_risk_regime_context), risk_regime_epoch_id=82(reviewed_missing_risk_regime_context)`
- `order_bundle_submitted` count=`24` routing=`reviewed_unknown_token_provenance` fields=`broker_order_no=24(reviewed_pre_contract_placeholder), broker_receipt_status=24(reviewed_pre_contract_placeholder), filled_qty=24(reviewed_pre_contract_placeholder), remaining_qty=24(reviewed_pre_contract_placeholder), fill_quality=24(reviewed_pre_contract_placeholder)`

## Top Stages
- `budget_pass`: `6841`
- `orderbook_stability_observed`: `6835`
- `latency_block`: `6760`
- `swing_entry_policy_evaluated`: `6016`
- `bad_entry_refined_candidate`: `6005`
- `swing_entry_micro_context_observed`: `5988`
- `scalp_sim_panic_scale_in_blocked`: `4845`
- `market_regime_prior_observed`: `4791`
- `blocked_swing_score_vpw`: `4325`
- `scalp_entry_action_decision_snapshot`: `4010`
- `stat_action_decision_snapshot`: `4005`
- `strength_momentum_observed`: `3407`
- `blocked_strength_momentum`: `3407`
- `swing_probe_discarded`: `3383`
- `reversal_add_blocked_reason`: `2640`
- `ai_holding_fast_reuse_band`: `2465`
- `ai_holding_reuse_bypass`: `2465`
- `scalp_sim_panic_action_deduped`: `2247`
- `ai_holding_review`: `1836`
- `scalp_sim_ai_holding_live_call`: `1797`

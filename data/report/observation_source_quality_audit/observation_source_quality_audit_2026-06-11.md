# Observation Source Quality Audit - 2026-06-11

- status: `pass`
- event_count: `179471`
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
- `scalp_sim_panic_context_warning` count=`211` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=211(reviewed_missing_risk_regime_context), market_risk_state=211(reviewed_missing_risk_regime_context), liquidity_state=211(reviewed_missing_risk_regime_context), risk_regime_epoch_id=211(reviewed_missing_risk_regime_context)`
- `order_bundle_submitted` count=`41` routing=`reviewed_unknown_token_provenance` fields=`broker_order_no=41(reviewed_pre_contract_placeholder), broker_receipt_status=41(reviewed_pre_contract_placeholder), filled_qty=41(reviewed_pre_contract_placeholder), remaining_qty=41(reviewed_pre_contract_placeholder), fill_quality=41(reviewed_pre_contract_placeholder)`

## Top Stages
- `budget_pass`: `10170`
- `orderbook_stability_observed`: `10162`
- `latency_block`: `10034`
- `bad_entry_refined_candidate`: `9828`
- `swing_entry_policy_evaluated`: `8807`
- `swing_entry_micro_context_observed`: `8770`
- `scalp_sim_panic_scale_in_blocked`: `7792`
- `market_regime_prior_observed`: `7582`
- `stat_action_decision_snapshot`: `7053`
- `scalp_entry_action_decision_snapshot`: `6196`
- `blocked_swing_score_vpw`: `6025`
- `swing_probe_discarded`: `5449`
- `strength_momentum_observed`: `5131`
- `blocked_strength_momentum`: `5131`
- `ai_holding_fast_reuse_band`: `4614`
- `ai_holding_reuse_bypass`: `4614`
- `reversal_add_blocked_reason`: `4446`
- `scalp_sim_panic_action_deduped`: `3788`
- `ai_holding_review`: `3306`
- `scalp_sim_ai_holding_live_call`: `3230`

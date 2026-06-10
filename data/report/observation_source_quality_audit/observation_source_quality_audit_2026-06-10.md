# Observation Source Quality Audit - 2026-06-10

- status: `pass`
- event_count: `143430`
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
- `order_leg_request` count=`98` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=1(reviewed_missing_risk_regime_context)`
- `scalp_sim_panic_context_warning` count=`66` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=66(reviewed_missing_risk_regime_context), market_risk_state=66(reviewed_missing_risk_regime_context), liquidity_state=66(reviewed_missing_risk_regime_context), risk_regime_epoch_id=66(reviewed_missing_risk_regime_context)`
- `swing_sim_buy_order_assumed_filled` count=`50` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=1(reviewed_missing_risk_regime_context)`
- `swing_sim_order_bundle_assumed_filled` count=`50` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=1(reviewed_missing_risk_regime_context)`
- `order_bundle_submitted` count=`25` routing=`reviewed_unknown_token_provenance` fields=`broker_order_no=25(reviewed_pre_contract_placeholder), broker_receipt_status=25(reviewed_pre_contract_placeholder), filled_qty=25(reviewed_pre_contract_placeholder), remaining_qty=25(reviewed_pre_contract_placeholder), fill_quality=25(reviewed_pre_contract_placeholder)`

## Top Stages
- `bad_entry_refined_candidate`: `9465`
- `budget_pass`: `8602`
- `orderbook_stability_observed`: `8589`
- `latency_block`: `8406`
- `stat_action_decision_snapshot`: `6581`
- `swing_entry_policy_evaluated`: `6580`
- `swing_entry_micro_context_observed`: `6469`
- `blocked_swing_score_vpw`: `5426`
- `scalp_entry_action_decision_snapshot`: `5275`
- `scalp_sim_panic_scale_in_blocked`: `5057`
- `strength_momentum_observed`: `4704`
- `blocked_strength_momentum`: `4704`
- `market_regime_block`: `4671`
- `reversal_add_blocked_reason`: `4482`
- `ai_holding_fast_reuse_band`: `3491`
- `ai_holding_reuse_bypass`: `3487`
- `ai_holding_review`: `2465`
- `scalp_sim_ai_holding_live_call`: `2253`
- `scalp_sim_panic_action_deduped`: `2155`
- `swing_probe_discarded`: `1990`

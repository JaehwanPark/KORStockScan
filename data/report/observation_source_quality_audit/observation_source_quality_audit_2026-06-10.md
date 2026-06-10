# Observation Source Quality Audit - 2026-06-10

- status: `pass`
- event_count: `325931`
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
- `order_leg_request` count=`146` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=1(reviewed_missing_risk_regime_context)`
- `swing_sim_buy_order_assumed_filled` count=`74` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=1(reviewed_missing_risk_regime_context)`
- `swing_sim_order_bundle_assumed_filled` count=`74` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=1(reviewed_missing_risk_regime_context)`
- `scalp_sim_panic_context_warning` count=`68` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=68(reviewed_missing_risk_regime_context), market_risk_state=68(reviewed_missing_risk_regime_context), liquidity_state=68(reviewed_missing_risk_regime_context), risk_regime_epoch_id=68(reviewed_missing_risk_regime_context)`
- `order_bundle_submitted` count=`49` routing=`reviewed_unknown_token_provenance` fields=`broker_order_no=49(reviewed_pre_contract_placeholder), broker_receipt_status=49(reviewed_pre_contract_placeholder), filled_qty=49(reviewed_pre_contract_placeholder), remaining_qty=49(reviewed_pre_contract_placeholder), fill_quality=49(reviewed_pre_contract_placeholder)`

## Top Stages
- `budget_pass`: `22091`
- `orderbook_stability_observed`: `22073`
- `latency_block`: `21743`
- `bad_entry_refined_candidate`: `19617`
- `swing_entry_policy_evaluated`: `18091`
- `swing_entry_micro_context_observed`: `17895`
- `market_regime_block`: `16182`
- `blocked_swing_score_vpw`: `15322`
- `scalp_sim_panic_scale_in_blocked`: `13434`
- `stat_action_decision_snapshot`: `12690`
- `scalp_entry_action_decision_snapshot`: `9658`
- `strength_momentum_observed`: `9198`
- `blocked_strength_momentum`: `9198`
- `reversal_add_blocked_reason`: `8708`
- `ai_holding_fast_reuse_band`: `6884`
- `ai_holding_reuse_bypass`: `6872`
- `scalp_sim_panic_action_deduped`: `5891`
- `swing_probe_discarded`: `5017`
- `ai_holding_review`: `4935`
- `scalp_sim_ai_holding_live_call`: `4577`

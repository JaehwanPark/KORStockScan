# Observation Source Quality Audit - 2026-06-09

- status: `pass`
- event_count: `274293`
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
- `scalp_entry_action_decision_snapshot` count=`5911` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=5(reviewed_missing_risk_regime_context)`
- `lifecycle_decision_matrix_runtime_policy` count=`22` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=1(reviewed_missing_risk_regime_context)`
- `order_leg_request` count=`21` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=1(reviewed_missing_risk_regime_context)`
- `swing_sim_buy_order_assumed_filled` count=`13` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=1(reviewed_missing_risk_regime_context)`
- `swing_sim_order_bundle_assumed_filled` count=`13` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=1(reviewed_missing_risk_regime_context)`
- `scalp_sim_panic_context_warning` count=`8` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=8(reviewed_missing_risk_regime_context), market_risk_state=8(reviewed_missing_risk_regime_context), liquidity_state=8(reviewed_missing_risk_regime_context), risk_regime_epoch_id=8(reviewed_missing_risk_regime_context)`
- `order_bundle_submitted` count=`6` routing=`reviewed_unknown_token_provenance` fields=`broker_order_no=6(reviewed_pre_contract_placeholder), broker_receipt_status=6(reviewed_pre_contract_placeholder), filled_qty=6(reviewed_pre_contract_placeholder), remaining_qty=6(reviewed_pre_contract_placeholder), fill_quality=6(reviewed_pre_contract_placeholder)`

## Top Stages
- `bad_entry_refined_candidate`: `15688`
- `scalp_sim_panic_scale_in_blocked`: `14850`
- `budget_pass`: `14109`
- `orderbook_stability_observed`: `14108`
- `latency_block`: `14045`
- `market_regime_prior_observed`: `13097`
- `swing_entry_policy_evaluated`: `13097`
- `swing_entry_micro_context_observed`: `13049`
- `strength_momentum_observed`: `12000`
- `blocked_strength_momentum`: `12000`
- `blocked_swing_gap`: `11055`
- `stat_action_decision_snapshot`: `10401`
- `blocked_gatekeeper_reject`: `8377`
- `gatekeeper_fast_reuse_bypass`: `8057`
- `gatekeeper_reject_cache_reuse`: `7359`
- `scalp_sim_panic_action_deduped`: `6585`
- `scalp_entry_action_decision_snapshot`: `5911`
- `ai_holding_fast_reuse_band`: `5738`
- `ai_holding_reuse_bypass`: `5728`
- `reversal_add_blocked_reason`: `5469`

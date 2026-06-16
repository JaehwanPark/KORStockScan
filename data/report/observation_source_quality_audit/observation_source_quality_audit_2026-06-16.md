# Observation Source Quality Audit - 2026-06-16

- status: `pass`
- event_count: `298906`
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
- `lifecycle_decision_matrix_runtime_policy` count=`190` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=4(reviewed_missing_risk_regime_context)`
- `order_leg_request` count=`82` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=4(reviewed_missing_risk_regime_context)`
- `swing_sim_buy_order_assumed_filled` count=`79` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=4(reviewed_missing_risk_regime_context)`
- `swing_sim_order_bundle_assumed_filled` count=`79` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=4(reviewed_missing_risk_regime_context)`
- `scalp_sim_panic_context_warning` count=`19` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=19(reviewed_missing_risk_regime_context), market_risk_state=19(reviewed_missing_risk_regime_context), liquidity_state=19(reviewed_missing_risk_regime_context), risk_regime_epoch_id=19(reviewed_missing_risk_regime_context)`
- `order_bundle_submitted` count=`3` routing=`reviewed_unknown_token_provenance` fields=`filled_qty=3(reviewed_pre_contract_placeholder), remaining_qty=3(reviewed_pre_contract_placeholder), fill_quality=3(reviewed_pre_contract_placeholder)`

## Top Stages
- `budget_pass`: `21215`
- `orderbook_stability_observed`: `21209`
- `latency_block`: `20986`
- `swing_entry_policy_evaluated`: `20708`
- `swing_entry_micro_context_observed`: `20702`
- `market_regime_prior_observed`: `15469`
- `bad_entry_refined_candidate`: `15211`
- `blocked_swing_score_vpw`: `11285`
- `scalp_sim_scale_in_candidate_funnel`: `9831`
- `blocked_gatekeeper_reject`: `9422`
- `stat_action_decision_snapshot`: `9050`
- `gatekeeper_fast_reuse_bypass`: `8790`
- `strength_momentum_observed`: `7787`
- `blocked_strength_momentum`: `7787`
- `gatekeeper_reject_cache_reuse`: `7383`
- `reversal_add_blocked_reason`: `6889`
- `scalping_scanner_candidate_observed`: `6730`
- `market_regime_pass`: `5239`
- `scalp_entry_action_decision_snapshot`: `4826`
- `ai_holding_fast_reuse_band`: `4715`

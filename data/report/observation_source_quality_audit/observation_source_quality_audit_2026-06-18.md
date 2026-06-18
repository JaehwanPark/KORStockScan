# Observation Source Quality Audit - 2026-06-18

- status: `pass`
- event_count: `236843`
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
- `lifecycle_decision_matrix_runtime_policy` count=`483` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=8(reviewed_missing_risk_regime_context)`
- `order_leg_request` count=`371` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=8(reviewed_missing_risk_regime_context)`
- `swing_sim_buy_order_assumed_filled` count=`350` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=8(reviewed_missing_risk_regime_context)`
- `swing_sim_order_bundle_assumed_filled` count=`350` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=8(reviewed_missing_risk_regime_context)`
- `scalp_sim_panic_context_warning` count=`30` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=30(reviewed_missing_risk_regime_context), market_risk_state=30(reviewed_missing_risk_regime_context), liquidity_state=30(reviewed_missing_risk_regime_context), risk_regime_epoch_id=30(reviewed_missing_risk_regime_context)`
- `order_bundle_submitted` count=`21` routing=`reviewed_unknown_token_provenance` fields=`filled_qty=21(reviewed_pre_contract_placeholder), remaining_qty=21(reviewed_pre_contract_placeholder), fill_quality=21(reviewed_pre_contract_placeholder)`
- `position_rebased_after_fill` count=`18` routing=`reviewed_unknown_token_provenance` fields=`fill_quality=2(reviewed_fill_quality_pre_contract_no_requested_qty)`

## Top Stages
- `scalping_scanner_candidate_observed`: `23145`
- `scalping_scanner_real_source_guard_block`: `23145`
- `strength_momentum_observed`: `17933`
- `blocked_strength_momentum`: `17933`
- `bad_entry_refined_candidate`: `15758`
- `scalp_sim_panic_scale_in_blocked`: `14030`
- `stat_action_decision_snapshot`: `10698`
- `reversal_add_blocked_reason`: `6577`
- `scalp_sim_panic_action_deduped`: `6055`
- `ai_holding_fast_reuse_band`: `4931`
- `ai_holding_reuse_bypass`: `4909`
- `budget_pass`: `4893`
- `orderbook_stability_observed`: `4871`
- `scalp_sim_panic_level1_partial_skipped_min_remaining`: `4622`
- `latency_block`: `4284`
- `ai_holding_review`: `3898`
- `swing_entry_policy_evaluated`: `3792`
- `swing_entry_micro_context_observed`: `3714`
- `market_regime_prior_observed`: `3634`
- `blocked_swing_score_vpw`: `3395`

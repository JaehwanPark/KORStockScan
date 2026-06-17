# Observation Source Quality Audit - 2026-06-17

- status: `pass`
- event_count: `494127`
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
- `scalp_entry_action_decision_snapshot` count=`4945` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=2(reviewed_missing_risk_regime_context)`
- `lifecycle_decision_matrix_runtime_policy` count=`53` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=4(reviewed_missing_risk_regime_context)`
- `order_leg_request` count=`37` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=4(reviewed_missing_risk_regime_context)`
- `swing_sim_buy_order_assumed_filled` count=`31` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=4(reviewed_missing_risk_regime_context)`
- `swing_sim_order_bundle_assumed_filled` count=`31` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=4(reviewed_missing_risk_regime_context)`
- `order_bundle_submitted` count=`6` routing=`reviewed_unknown_token_provenance` fields=`filled_qty=6(reviewed_pre_contract_placeholder), remaining_qty=6(reviewed_pre_contract_placeholder), fill_quality=6(reviewed_pre_contract_placeholder)`
- `scalp_sim_panic_context_warning` count=`4` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=4(reviewed_missing_risk_regime_context), market_risk_state=4(reviewed_missing_risk_regime_context), liquidity_state=4(reviewed_missing_risk_regime_context), risk_regime_epoch_id=4(reviewed_missing_risk_regime_context)`

## Top Stages
- `budget_pass`: `45425`
- `orderbook_stability_observed`: `45423`
- `latency_block`: `45315`
- `market_regime_pass`: `44756`
- `swing_entry_policy_evaluated`: `44756`
- `swing_entry_micro_context_observed`: `44754`
- `blocked_swing_score_vpw`: `35987`
- `scalp_sim_scale_in_candidate_funnel`: `16175`
- `bad_entry_refined_candidate`: `16015`
- `strength_momentum_observed`: `13464`
- `blocked_strength_momentum`: `13464`
- `stat_action_decision_snapshot`: `10899`
- `scalping_scanner_candidate_observed`: `10368`
- `scalping_scanner_real_source_guard_block`: `9293`
- `blocked_gatekeeper_reject`: `8769`
- `gatekeeper_fast_reuse_bypass`: `8031`
- `gatekeeper_reject_cache_reuse`: `7402`
- `reversal_add_blocked_reason`: `6572`
- `scalp_entry_action_decision_snapshot`: `4945`
- `ai_holding_fast_reuse_band`: `4530`

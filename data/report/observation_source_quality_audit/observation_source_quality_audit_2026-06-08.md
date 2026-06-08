# Observation Source Quality Audit - 2026-06-08

- status: `pass`
- event_count: `303744`
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
- `orderbook_stability_observed` count=`16748` routing=`reviewed_unknown_token_provenance` fields=`orderbook_micro_ofi_threshold_bucket_key=1751(reviewed_insufficient_sample), orderbook_micro_ofi_calibration_bucket=1751(reviewed_insufficient_sample), orderbook_micro_ofi_bucket_key=1751(reviewed_insufficient_sample)`
- `latency_block` count=`16584` routing=`reviewed_unknown_token_provenance` fields=`orderbook_micro_ofi_threshold_bucket_key=1745(reviewed_insufficient_sample), orderbook_micro_ofi_calibration_bucket=1745(reviewed_insufficient_sample), orderbook_micro_ofi_bucket_key=1745(reviewed_insufficient_sample)`
- `swing_entry_policy_evaluated` count=`13230` routing=`reviewed_unknown_token_provenance` fields=`feature_snapshot=1762(reviewed_insufficient_sample)`
- `market_regime_block` count=`13053` routing=`reviewed_unknown_token_provenance` fields=`orderbook_micro_ofi_threshold_bucket_key=1762(reviewed_insufficient_sample), orderbook_micro_ofi_calibration_bucket=1762(reviewed_insufficient_sample), orderbook_micro_ofi_bucket_key=1762(reviewed_insufficient_sample)`
- `swing_entry_micro_context_observed` count=`13035` routing=`reviewed_unknown_token_provenance` fields=`orderbook_micro_ofi_threshold_bucket_key=1751(reviewed_insufficient_sample), orderbook_micro_ofi_calibration_bucket=1751(reviewed_insufficient_sample), orderbook_micro_ofi_bucket_key=1751(reviewed_insufficient_sample)`
- `entry_ai_price_canary_applied` count=`332` routing=`reviewed_unknown_token_provenance` fields=`orderbook_micro_ofi_calibration_bucket=208(reviewed_insufficient_sample), orderbook_micro_ofi_bucket_key=208(reviewed_insufficient_sample)`
- `entry_ai_price_canary_fallback` count=`171` routing=`reviewed_unknown_token_provenance` fields=`orderbook_micro_ofi_calibration_bucket=168(reviewed_insufficient_sample), orderbook_micro_ofi_bucket_key=168(reviewed_insufficient_sample)`
- `latency_pass` count=`164` routing=`reviewed_unknown_token_provenance` fields=`orderbook_micro_ofi_threshold_bucket_key=6(reviewed_insufficient_sample), orderbook_micro_ofi_calibration_bucket=6(reviewed_insufficient_sample), orderbook_micro_ofi_bucket_key=6(reviewed_insufficient_sample)`
- `lifecycle_decision_matrix_runtime_policy` count=`81` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=6(reviewed_missing_risk_regime_context)`
- `order_leg_request` count=`81` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=6(reviewed_missing_risk_regime_context), orderbook_micro_ofi_threshold_bucket_key=6(reviewed_insufficient_sample), orderbook_micro_ofi_calibration_bucket=6(reviewed_insufficient_sample), orderbook_micro_ofi_bucket_key=6(reviewed_insufficient_sample)`
- `swing_scale_in_micro_context_observed` count=`49` routing=`reviewed_unknown_token_provenance` fields=`orderbook_micro_ofi_threshold_bucket_key=35(reviewed_orderbook_micro_legacy_not_available_bucket), orderbook_micro_ofi_calibration_bucket=35(reviewed_orderbook_micro_legacy_not_available_bucket), orderbook_micro_ofi_bucket_key=35(reviewed_orderbook_micro_legacy_not_available_bucket), orderbook_micro_ofi_threshold_bucket_key=1(reviewed_insufficient_sample), orderbook_micro_ofi_calibration_bucket=1(reviewed_insufficient_sample), orderbook_micro_ofi_bucket_key=1(reviewed_insufficient_sample)`
- `scale_in_qty_block` count=`44` routing=`reviewed_unknown_token_provenance` fields=`orderbook_micro_ofi_threshold_bucket_key=35(reviewed_orderbook_micro_legacy_not_available_bucket), orderbook_micro_ofi_calibration_bucket=35(reviewed_orderbook_micro_legacy_not_available_bucket), orderbook_micro_ofi_bucket_key=35(reviewed_orderbook_micro_legacy_not_available_bucket), orderbook_micro_ofi_threshold_bucket_key=1(reviewed_insufficient_sample), orderbook_micro_ofi_calibration_bucket=1(reviewed_insufficient_sample), orderbook_micro_ofi_bucket_key=1(reviewed_insufficient_sample)`
- `swing_sim_buy_order_assumed_filled` count=`36` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=6(reviewed_missing_risk_regime_context), orderbook_micro_ofi_threshold_bucket_key=6(reviewed_insufficient_sample), orderbook_micro_ofi_calibration_bucket=6(reviewed_insufficient_sample), orderbook_micro_ofi_bucket_key=6(reviewed_insufficient_sample)`
- `swing_sim_order_bundle_assumed_filled` count=`36` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=6(reviewed_missing_risk_regime_context), orderbook_micro_ofi_threshold_bucket_key=6(reviewed_insufficient_sample), orderbook_micro_ofi_calibration_bucket=6(reviewed_insufficient_sample), orderbook_micro_ofi_bucket_key=6(reviewed_insufficient_sample)`
- `order_bundle_submitted` count=`32` routing=`reviewed_unknown_token_provenance` fields=`broker_order_no=32(reviewed_pre_contract_placeholder), broker_receipt_status=32(reviewed_pre_contract_placeholder), filled_qty=32(reviewed_pre_contract_placeholder), remaining_qty=32(reviewed_pre_contract_placeholder), fill_quality=32(reviewed_pre_contract_placeholder)`
- `swing_reentry_counterfactual_after_loss` count=`30` routing=`reviewed_unknown_token_provenance` fields=`orderbook_micro_ofi_threshold_bucket_key=2(reviewed_insufficient_sample), orderbook_micro_ofi_calibration_bucket=2(reviewed_insufficient_sample), orderbook_micro_ofi_bucket_key=2(reviewed_insufficient_sample)`
- `scalp_sim_panic_context_warning` count=`27` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=27(reviewed_missing_risk_regime_context), market_risk_state=27(reviewed_missing_risk_regime_context), liquidity_state=27(reviewed_missing_risk_regime_context), risk_regime_epoch_id=27(reviewed_missing_risk_regime_context)`
- `swing_probe_sell_order_assumed_filled` count=`13` routing=`reviewed_unknown_token_provenance` fields=`orderbook_micro_ofi_threshold_bucket_key=1(reviewed_orderbook_micro_legacy_not_available_bucket), orderbook_micro_ofi_calibration_bucket=1(reviewed_orderbook_micro_legacy_not_available_bucket), orderbook_micro_ofi_bucket_key=1(reviewed_orderbook_micro_legacy_not_available_bucket)`

## Top Stages
- `bad_entry_refined_candidate`: `20334`
- `budget_pass`: `16755`
- `orderbook_stability_observed`: `16748`
- `scalp_sim_panic_scale_in_blocked`: `16595`
- `latency_block`: `16584`
- `strength_momentum_observed`: `16553`
- `blocked_strength_momentum`: `16053`
- `swing_entry_policy_evaluated`: `13230`
- `market_regime_block`: `13053`
- `swing_entry_micro_context_observed`: `13035`
- `stat_action_decision_snapshot`: `12849`
- `scalp_entry_action_decision_snapshot`: `8575`
- `reversal_add_blocked_reason`: `8554`
- `scalp_sim_panic_action_deduped`: `7630`
- `blocked_swing_score_vpw`: `7276`
- `ai_holding_fast_reuse_band`: `6663`
- `ai_holding_reuse_bypass`: `6649`
- `blocked_gatekeeper_reject`: `5955`
- `gatekeeper_fast_reuse_bypass`: `5761`
- `ai_holding_review`: `5215`

# Observation Source Quality Audit - 2026-06-05

- status: `pass`
- event_count: `309653`
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
- `orderbook_stability_observed` count=`25120` routing=`reviewed_unknown_token_provenance` fields=`orderbook_micro_ofi_threshold_bucket_key=1(reviewed_insufficient_sample), orderbook_micro_ofi_calibration_bucket=1(reviewed_insufficient_sample), orderbook_micro_ofi_bucket_key=1(reviewed_insufficient_sample)`
- `swing_entry_policy_evaluated` count=`23695` routing=`reviewed_unknown_token_provenance` fields=`feature_snapshot=2(reviewed_insufficient_sample)`
- `market_regime_block` count=`23589` routing=`reviewed_unknown_token_provenance` fields=`orderbook_micro_ofi_threshold_bucket_key=2(reviewed_insufficient_sample), orderbook_micro_ofi_calibration_bucket=2(reviewed_insufficient_sample), orderbook_micro_ofi_bucket_key=2(reviewed_insufficient_sample)`
- `swing_entry_micro_context_observed` count=`23486` routing=`reviewed_unknown_token_provenance` fields=`orderbook_micro_ofi_threshold_bucket_key=1(reviewed_insufficient_sample), orderbook_micro_ofi_calibration_bucket=1(reviewed_insufficient_sample), orderbook_micro_ofi_bucket_key=1(reviewed_insufficient_sample)`
- `scalp_entry_action_decision_snapshot` count=`6016` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=3(reviewed_missing_risk_regime_context)`
- `latency_pass` count=`330` routing=`reviewed_unknown_token_provenance` fields=`orderbook_micro_ofi_threshold_bucket_key=1(reviewed_insufficient_sample), orderbook_micro_ofi_calibration_bucket=1(reviewed_insufficient_sample), orderbook_micro_ofi_bucket_key=1(reviewed_insufficient_sample)`
- `entry_ai_price_canary_applied` count=`314` routing=`reviewed_unknown_token_provenance` fields=`orderbook_micro_ofi_calibration_bucket=14(reviewed_insufficient_sample), orderbook_micro_ofi_bucket_key=14(reviewed_insufficient_sample)`
- `entry_ai_price_canary_fallback` count=`143` routing=`reviewed_unknown_token_provenance` fields=`orderbook_micro_ofi_calibration_bucket=137(reviewed_insufficient_sample), orderbook_micro_ofi_bucket_key=137(reviewed_insufficient_sample)`
- `order_leg_request` count=`16` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=4(reviewed_missing_risk_regime_context), orderbook_micro_ofi_threshold_bucket_key=1(reviewed_insufficient_sample), orderbook_micro_ofi_calibration_bucket=1(reviewed_insufficient_sample), orderbook_micro_ofi_bucket_key=1(reviewed_insufficient_sample)`
- `swing_sim_buy_order_assumed_filled` count=`15` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=4(reviewed_missing_risk_regime_context), orderbook_micro_ofi_threshold_bucket_key=1(reviewed_insufficient_sample), orderbook_micro_ofi_calibration_bucket=1(reviewed_insufficient_sample), orderbook_micro_ofi_bucket_key=1(reviewed_insufficient_sample)`
- `swing_sim_order_bundle_assumed_filled` count=`15` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=4(reviewed_missing_risk_regime_context), orderbook_micro_ofi_threshold_bucket_key=1(reviewed_insufficient_sample), orderbook_micro_ofi_calibration_bucket=1(reviewed_insufficient_sample), orderbook_micro_ofi_bucket_key=1(reviewed_insufficient_sample)`
- `order_bundle_submitted` count=`1` routing=`reviewed_unknown_token_provenance` fields=`broker_order_no=1(reviewed_pre_contract_placeholder), broker_receipt_status=1(reviewed_pre_contract_placeholder), filled_qty=1(reviewed_pre_contract_placeholder), remaining_qty=1(reviewed_pre_contract_placeholder), fill_quality=1(reviewed_pre_contract_placeholder)`
- `scalp_sim_panic_context_warning` count=`1` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=1(reviewed_missing_risk_regime_context), market_risk_state=1(reviewed_missing_risk_regime_context), liquidity_state=1(reviewed_missing_risk_regime_context), risk_regime_epoch_id=1(reviewed_missing_risk_regime_context)`

## Top Stages
- `budget_pass`: `25126`
- `orderbook_stability_observed`: `25120`
- `latency_block`: `24790`
- `swing_entry_policy_evaluated`: `23695`
- `market_regime_block`: `23589`
- `swing_entry_micro_context_observed`: `23486`
- `blocked_swing_score_vpw`: `22972`
- `strength_momentum_observed`: `18310`
- `blocked_strength_momentum`: `13561`
- `bad_entry_refined_candidate`: `10137`
- `scalp_sim_panic_scale_in_blocked`: `9635`
- `scalp_sim_panic_level1_partial_skipped_min_remaining`: `7951`
- `stat_action_decision_snapshot`: `7791`
- `scalp_entry_action_decision_snapshot`: `6016`
- `blocked_swing_gap`: `4854`
- `swing_probe_discarded`: `4408`
- `reversal_add_blocked_reason`: `4075`
- `scalp_sim_panic_action_deduped`: `3669`
- `ai_holding_fast_reuse_band`: `3655`
- `ai_holding_reuse_bypass`: `3635`

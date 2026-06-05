# Observation Source Quality Audit - 2026-06-05

- status: `warning`
- event_count: `122702`
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
- `scalp_entry_action_decision_snapshot` count=`3917` routing=`source_quality_blocker_or_provenance_backfill` fields=`risk_regime_context=3(0.0008)`
- `order_leg_request` count=`11` routing=`source_quality_blocker_or_provenance_backfill` fields=`risk_regime_context=4(0.3636)`
- `swing_sim_buy_order_assumed_filled` count=`11` routing=`source_quality_blocker_or_provenance_backfill` fields=`risk_regime_context=4(0.3636)`
- `swing_sim_order_bundle_assumed_filled` count=`11` routing=`source_quality_blocker_or_provenance_backfill` fields=`risk_regime_context=4(0.3636)`

## Reviewed Unknown Token Findings
- `orderbook_stability_observed` count=`12748` routing=`reviewed_unknown_token_provenance` fields=`orderbook_micro_ofi_threshold_bucket_key=1(reviewed_insufficient_sample), orderbook_micro_ofi_calibration_bucket=1(reviewed_insufficient_sample), orderbook_micro_ofi_bucket_key=1(reviewed_insufficient_sample)`
- `swing_entry_policy_evaluated` count=`11322` routing=`reviewed_unknown_token_provenance` fields=`feature_snapshot=2(reviewed_insufficient_sample)`
- `swing_entry_micro_context_observed` count=`11233` routing=`reviewed_unknown_token_provenance` fields=`orderbook_micro_ofi_threshold_bucket_key=1(reviewed_insufficient_sample), orderbook_micro_ofi_calibration_bucket=1(reviewed_insufficient_sample), orderbook_micro_ofi_bucket_key=1(reviewed_insufficient_sample)`
- `market_regime_block` count=`11216` routing=`reviewed_unknown_token_provenance` fields=`orderbook_micro_ofi_threshold_bucket_key=2(reviewed_insufficient_sample), orderbook_micro_ofi_calibration_bucket=2(reviewed_insufficient_sample), orderbook_micro_ofi_bucket_key=2(reviewed_insufficient_sample)`
- `latency_pass` count=`312` routing=`reviewed_unknown_token_provenance` fields=`orderbook_micro_ofi_threshold_bucket_key=1(reviewed_insufficient_sample), orderbook_micro_ofi_calibration_bucket=1(reviewed_insufficient_sample), orderbook_micro_ofi_bucket_key=1(reviewed_insufficient_sample)`
- `entry_ai_price_canary_applied` count=`297` routing=`reviewed_unknown_token_provenance` fields=`orderbook_micro_ofi_calibration_bucket=9(reviewed_insufficient_sample), orderbook_micro_ofi_bucket_key=9(reviewed_insufficient_sample)`
- `entry_ai_price_canary_fallback` count=`28` routing=`reviewed_unknown_token_provenance` fields=`orderbook_micro_ofi_calibration_bucket=22(reviewed_insufficient_sample), orderbook_micro_ofi_bucket_key=22(reviewed_insufficient_sample)`
- `order_leg_request` count=`11` routing=`reviewed_unknown_token_provenance` fields=`orderbook_micro_ofi_threshold_bucket_key=1(reviewed_insufficient_sample), orderbook_micro_ofi_calibration_bucket=1(reviewed_insufficient_sample), orderbook_micro_ofi_bucket_key=1(reviewed_insufficient_sample)`
- `swing_sim_buy_order_assumed_filled` count=`11` routing=`reviewed_unknown_token_provenance` fields=`orderbook_micro_ofi_threshold_bucket_key=1(reviewed_insufficient_sample), orderbook_micro_ofi_calibration_bucket=1(reviewed_insufficient_sample), orderbook_micro_ofi_bucket_key=1(reviewed_insufficient_sample)`
- `swing_sim_order_bundle_assumed_filled` count=`11` routing=`reviewed_unknown_token_provenance` fields=`orderbook_micro_ofi_threshold_bucket_key=1(reviewed_insufficient_sample), orderbook_micro_ofi_calibration_bucket=1(reviewed_insufficient_sample), orderbook_micro_ofi_bucket_key=1(reviewed_insufficient_sample)`

## Top Stages
- `budget_pass`: `12754`
- `orderbook_stability_observed`: `12748`
- `latency_block`: `12436`
- `swing_entry_policy_evaluated`: `11322`
- `swing_entry_micro_context_observed`: `11233`
- `market_regime_block`: `11216`
- `blocked_swing_score_vpw`: `10599`
- `strength_momentum_observed`: `9263`
- `blocked_strength_momentum`: `6079`
- `scalp_entry_action_decision_snapshot`: `3917`
- `blocked_swing_gap`: `1768`
- `swing_probe_discarded`: `1664`
- `scalp_sim_duplicate_buy_signal`: `1514`
- `entry_armed_resume`: `1314`
- `blocked_vpw`: `1210`
- `blocked_ai_score`: `1182`
- `ai_confirmed`: `908`
- `blocked_liquidity`: `813`
- `blocked_gatekeeper_reject`: `723`
- `gatekeeper_fast_reuse_bypass`: `695`

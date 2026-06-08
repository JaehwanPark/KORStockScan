# Observation Source Quality Audit - 2026-06-08

- status: `warning`
- event_count: `30449`
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
- `scale_in_qty_block` count=`36` routing=`source_quality_blocker_or_provenance_backfill` fields=`orderbook_micro_ofi_threshold_bucket_key=35(0.9722), orderbook_micro_ofi_calibration_bucket=35(0.9722), orderbook_micro_ofi_bucket_key=35(0.9722)`
- `swing_scale_in_micro_context_observed` count=`36` routing=`source_quality_blocker_or_provenance_backfill` fields=`orderbook_micro_ofi_threshold_bucket_key=35(0.9722), orderbook_micro_ofi_calibration_bucket=35(0.9722), orderbook_micro_ofi_bucket_key=35(0.9722)`
- `swing_probe_sell_order_assumed_filled` count=`10` routing=`source_quality_blocker_or_provenance_backfill` fields=`orderbook_micro_ofi_threshold_bucket_key=1(0.1), orderbook_micro_ofi_calibration_bucket=1(0.1), orderbook_micro_ofi_bucket_key=1(0.1)`

## Reviewed Unknown Token Findings
- `entry_ai_price_canary_applied` count=`76` routing=`reviewed_unknown_token_provenance` fields=`orderbook_micro_ofi_calibration_bucket=46(reviewed_insufficient_sample), orderbook_micro_ofi_bucket_key=46(reviewed_insufficient_sample)`
- `entry_ai_price_canary_fallback` count=`47` routing=`reviewed_unknown_token_provenance` fields=`orderbook_micro_ofi_calibration_bucket=46(reviewed_insufficient_sample), orderbook_micro_ofi_bucket_key=46(reviewed_insufficient_sample)`
- `scale_in_qty_block` count=`36` routing=`reviewed_unknown_token_provenance` fields=`orderbook_micro_ofi_threshold_bucket_key=1(reviewed_insufficient_sample), orderbook_micro_ofi_calibration_bucket=1(reviewed_insufficient_sample), orderbook_micro_ofi_bucket_key=1(reviewed_insufficient_sample)`
- `swing_scale_in_micro_context_observed` count=`36` routing=`reviewed_unknown_token_provenance` fields=`orderbook_micro_ofi_threshold_bucket_key=1(reviewed_insufficient_sample), orderbook_micro_ofi_calibration_bucket=1(reviewed_insufficient_sample), orderbook_micro_ofi_bucket_key=1(reviewed_insufficient_sample)`

## Top Stages
- `budget_pass`: `2335`
- `orderbook_stability_observed`: `2334`
- `latency_block`: `2289`
- `swing_entry_policy_evaluated`: `1736`
- `swing_entry_micro_context_observed`: `1719`
- `market_regime_block`: `1558`
- `strength_momentum_observed`: `1340`
- `scalp_entry_action_decision_snapshot`: `1337`
- `bad_entry_refined_candidate`: `1005`
- `blocked_swing_score_vpw`: `884`
- `gatekeeper_fast_reuse_bypass`: `852`
- `blocked_gatekeeper_reject`: `852`
- `blocked_strength_momentum`: `840`
- `gatekeeper_reject_cache_reuse`: `759`
- `scalp_sim_panic_scale_in_blocked`: `731`
- `stat_action_decision_snapshot`: `670`
- `scalp_sim_duplicate_buy_signal`: `575`
- `scalp_sim_panic_action_deduped`: `377`
- `ai_holding_fast_reuse_band`: `370`
- `ai_holding_reuse_bypass`: `370`

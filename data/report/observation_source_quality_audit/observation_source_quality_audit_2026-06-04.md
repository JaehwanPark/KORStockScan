# Observation Source Quality Audit - 2026-06-04

- status: `warning`
- event_count: `52522`
- decision_authority: `source_quality_only`
- runtime_effect: `False`
- forbidden_uses: `runtime_threshold_apply, order_submit, provider_route_change, bot_restart, real_execution_quality_approval`

## Warning Stages
- none

## Invalid Label Findings
- none

## High Volume Stages Without Source-Like Fields
- none

## Unknown Token Findings
- `latency_block` count=`4418` routing=`source_quality_blocker_or_provenance_backfill` fields=`swing_micro_ws_quote_stale=4384(0.9923)`
- `market_regime_prior_observed` count=`4416` routing=`source_quality_blocker_or_provenance_backfill` fields=`swing_micro_ws_quote_stale=4416(1.0)`
- `swing_entry_policy_evaluated` count=`4416` routing=`source_quality_blocker_or_provenance_backfill` fields=`feature_snapshot=4416(1.0)`
- `swing_entry_micro_context_observed` count=`4401` routing=`source_quality_blocker_or_provenance_backfill` fields=`swing_micro_ws_quote_stale=4401(1.0)`
- `scalp_sim_panic_scale_in_blocked` count=`1539` routing=`source_quality_blocker_or_provenance_backfill` fields=`lifecycle_bucket_entry_bucket_key=1539(1.0), lifecycle_bucket_entry_bucket_id=1062(0.6901), lifecycle_bucket_bucket_id=232(0.1507)`
- `scalp_sim_sell_order_assumed_filled` count=`31` routing=`source_quality_blocker_or_provenance_backfill` fields=`lifecycle_bucket_entry_bucket_key=13(0.4194), lifecycle_bucket_entry_bucket_id=11(0.3548), lifecycle_bucket_bucket_id=3(0.0968)`
- `latency_pass` count=`24` routing=`source_quality_blocker_or_provenance_backfill` fields=`pre_submit_liquidity_value=17(0.7083), swing_micro_ws_quote_stale=17(0.7083), overbought_guard_reason=7(0.2917), pre_submit_overbought_reason=7(0.2917), orderbook_micro_ofi_threshold_bucket_key=2(0.0833), orderbook_micro_ofi_calibration_bucket=2(0.0833), orderbook_micro_ofi_bucket_key=2(0.0833)`
- `order_leg_request` count=`18` routing=`source_quality_blocker_or_provenance_backfill` fields=`pre_submit_liquidity_value=17(0.9444), swing_micro_ws_quote_stale=17(0.9444), orderbook_micro_ofi_threshold_bucket_key=2(0.1111), orderbook_micro_ofi_calibration_bucket=2(0.1111), orderbook_micro_ofi_bucket_key=2(0.1111), overbought_guard_reason=1(0.0556), pre_submit_overbought_reason=1(0.0556)`
- `swing_sim_buy_order_assumed_filled` count=`17` routing=`source_quality_blocker_or_provenance_backfill` fields=`swing_micro_ws_quote_stale=17(1.0), orderbook_micro_ofi_threshold_bucket_key=2(0.1176), orderbook_micro_ofi_calibration_bucket=2(0.1176), orderbook_micro_ofi_bucket_key=2(0.1176)`
- `swing_sim_order_bundle_assumed_filled` count=`17` routing=`source_quality_blocker_or_provenance_backfill` fields=`swing_micro_ws_quote_stale=17(1.0), orderbook_micro_ofi_threshold_bucket_key=2(0.1176), orderbook_micro_ofi_calibration_bucket=2(0.1176), orderbook_micro_ofi_bucket_key=2(0.1176)`
- `scalp_sim_buy_order_assumed_filled` count=`11` routing=`source_quality_blocker_or_provenance_backfill` fields=`lifecycle_bucket_entry_bucket_key=11(1.0), lifecycle_bucket_entry_bucket_id=8(0.7273)`
- `scalp_sim_buy_order_virtual_pending` count=`11` routing=`source_quality_blocker_or_provenance_backfill` fields=`lifecycle_bucket_entry_bucket_key=11(1.0), lifecycle_bucket_entry_bucket_id=8(0.7273)`
- `scalp_sim_entry_armed` count=`11` routing=`source_quality_blocker_or_provenance_backfill` fields=`lifecycle_bucket_entry_bucket_key=11(1.0), lifecycle_bucket_entry_bucket_id=8(0.7273)`
- `scalp_sim_holding_started` count=`11` routing=`source_quality_blocker_or_provenance_backfill` fields=`lifecycle_bucket_entry_bucket_key=11(1.0), lifecycle_bucket_entry_bucket_id=8(0.7273)`
- `scalp_sim_panic_level1_entry_observed` count=`11` routing=`source_quality_blocker_or_provenance_backfill` fields=`lifecycle_bucket_entry_bucket_key=11(1.0), lifecycle_bucket_entry_bucket_id=8(0.7273)`
- `scalp_sim_pre_submit_overbought_guard_would_pass` count=`11` routing=`source_quality_blocker_or_provenance_backfill` fields=`lifecycle_bucket_entry_bucket_key=11(1.0), lifecycle_bucket_entry_bucket_id=8(0.7273)`
- `entry_ai_price_canary_applied` count=`10` routing=`source_quality_blocker_or_provenance_backfill` fields=`orderbook_micro_ofi_calibration_bucket=3(0.3), orderbook_micro_ofi_bucket_key=3(0.3)`
- `entry_ai_price_canary_fallback` count=`8` routing=`source_quality_blocker_or_provenance_backfill` fields=`orderbook_micro_ofi_calibration_bucket=8(1.0), orderbook_micro_ofi_bucket_key=8(1.0)`
- `scalp_sim_entry_submit_revalidation_warning` count=`8` routing=`source_quality_blocker_or_provenance_backfill` fields=`lifecycle_bucket_entry_bucket_key=8(1.0), lifecycle_bucket_entry_bucket_id=6(0.75)`
- `swing_reentry_counterfactual_after_loss` count=`8` routing=`source_quality_blocker_or_provenance_backfill` fields=`swing_micro_ws_quote_stale=2(0.25)`

## Top Stages
- `budget_pass`: `4444`
- `orderbook_stability_observed`: `4442`
- `latency_block`: `4418`
- `market_regime_prior_observed`: `4416`
- `swing_entry_policy_evaluated`: `4416`
- `swing_entry_micro_context_observed`: `4401`
- `blocked_swing_score_vpw`: `3587`
- `bad_entry_refined_candidate`: `2113`
- `strength_momentum_observed`: `1669`
- `blocked_strength_momentum`: `1669`
- `scalp_sim_panic_scale_in_blocked`: `1539`
- `scalp_sim_panic_level1_partial_skipped_min_remaining`: `1357`
- `stat_action_decision_snapshot`: `1244`
- `blocked_swing_gap`: `836`
- `blocked_gatekeeper_reject`: `829`
- `blocked_overbought`: `824`
- `gatekeeper_fast_reuse_bypass`: `818`
- `swing_probe_discarded`: `802`
- `gatekeeper_reject_cache_reuse`: `768`
- `scalp_sim_panic_action_deduped`: `748`

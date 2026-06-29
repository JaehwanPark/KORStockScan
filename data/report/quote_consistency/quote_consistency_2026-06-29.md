# Quote Consistency Report 2026-06-29

- runtime_family: `quote_consistency_normalization`
- observed_count: `423`
- rest_fallback_count: `36`
- safety_exit_count: `0`
- ev_input_blocked_count: `51`
- missing_required_fields: `12`

## Verifier Findings
- `warning` `quote_consistency_source_missing`
- `warning` `quote_consistency_required_fields_excluded`

## Stage State Counts
- `entry_reprice_after_submit_blocked`: stale=1
- `entry_reprice_after_submit_evaluated`: single_source=1, stale=1
- `latency_block`: single_source=35, stale=6
- `latency_pass`: single_source=21
- `scale_in_price_guard_block`: stale=13
- `scale_in_price_p2_observe`: stale=2
- `scale_in_price_resolved`: stale=2
- `scale_in_qty_block`: single_source=7, stale=20
- `scalp_entry_action_decision_snapshot`: single_source=141, stale=6
- `scalp_sim_buy_order_virtual_pending`: single_source=49
- `scalp_sim_entry_submit_revalidation_warning`: single_source=19
- `scalp_sim_pre_submit_liquidity_guard_would_block`: single_source=13
- `scalp_sim_pre_submit_liquidity_guard_would_pass`: single_source=36
- `scalp_sim_pre_submit_overbought_guard_would_pass`: single_source=49
- `sell_order_sent`: single_source=1

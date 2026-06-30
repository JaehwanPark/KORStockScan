# Quote Consistency Report 2026-06-30

- runtime_family: `quote_consistency_normalization`
- observed_count: `2071`
- rest_fallback_count: `243`
- safety_exit_count: `23`
- ev_input_blocked_count: `566`
- missing_required_fields: `81`

## Verifier Findings
- `warning` `quote_consistency_source_missing`
- `warning` `quote_consistency_required_fields_excluded`

## Stage State Counts
- `entry_reprice_after_submit_blocked`: diverged=1, ok=26, single_source=39, stale=11, warning=7
- `entry_reprice_after_submit_evaluated`: diverged=1, ok=28, single_source=39, stale=11, warning=7
- `hard_stop_quote_revalidation_blocked`: single_source=1, stale=8
- `latency_block`: single_source=693, stale=220, warning=1
- `latency_pass`: ok=9, single_source=121
- `scale_in_price_guard_block`: single_source=67, stale=176
- `scale_in_price_p2_observe`: single_source=15, stale=8
- `scale_in_qty_block`: single_source=58, stale=17
- `scale_in_quote_consistency_defensive_bypass`: stale=18
- `scalp_entry_action_decision_snapshot`: single_source=180, stale=8
- `scalp_sim_buy_order_virtual_pending`: single_source=83, stale=3
- `scalp_sim_entry_submit_revalidation_warning`: stale=3
- `scalp_sim_pre_submit_liquidity_guard_would_block`: single_source=19
- `scalp_sim_pre_submit_liquidity_guard_would_pass`: single_source=64, stale=3
- `scalp_sim_pre_submit_overbought_guard_would_pass`: single_source=83, stale=3
- `sell_order_sent`: diverged=4, ok=3, single_source=29, stale=4

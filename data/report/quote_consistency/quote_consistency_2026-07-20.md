# Quote Consistency Report 2026-07-20

- runtime_family: `quote_consistency_normalization`
- observed_count: `1123`
- rest_fallback_count: `561`
- safety_exit_count: `0`
- ev_input_blocked_count: `8`
- missing_required_fields: `0`

## Verifier Findings
- `warning` `quote_consistency_divergence_without_safety_exit_rows`

## Stage State Counts
- `ai_holding_review`: single_source=427
- `entry_reprice_after_submit_evaluated`: ok=1
- `latency_block`: single_source=152, stale=3
- `latency_pass`: single_source=29
- `scale_in_price_p2_observe`: single_source=12
- `scale_in_price_resolved`: single_source=6
- `scale_in_qty_block`: single_source=1
- `scalp_entry_action_decision_snapshot`: single_source=431, stale=3
- `scalp_sim_buy_order_virtual_pending`: single_source=14
- `scalp_sim_pre_submit_liquidity_guard_would_block`: single_source=12
- `scalp_sim_pre_submit_liquidity_guard_would_pass`: single_source=2
- `scalp_sim_pre_submit_overbought_guard_would_pass`: single_source=14
- `sell_order_sent`: ok=8, single_source=3, stale=1, warning=3
- `trailing_sell_quote_revalidation_blocked`: diverged=1

# Quote Consistency Report 2026-07-09

- runtime_family: `quote_consistency_normalization`
- observed_count: `1214`
- rest_fallback_count: `222`
- safety_exit_count: `1`
- ev_input_blocked_count: `14`
- missing_required_fields: `0`

## Verifier Findings
- `ok` `none`

## Stage State Counts
- `ai_holding_review`: single_source=23, stale=7
- `entry_reprice_after_submit_blocked`: diverged=1, ok=1, single_source=1, warning=1
- `entry_reprice_after_submit_evaluated`: diverged=1, ok=1, single_source=1, warning=1
- `latency_block`: single_source=286
- `latency_pass`: single_source=21
- `scale_in_price_p2_observe`: single_source=2, stale=2
- `scale_in_price_resolved`: single_source=2, stale=2
- `scale_in_qty_block`: single_source=8, stale=1
- `scalp_entry_action_decision_snapshot`: ok=1, single_source=712
- `scalp_sim_buy_order_virtual_pending`: single_source=44
- `scalp_sim_pre_submit_liquidity_guard_would_block`: single_source=18
- `scalp_sim_pre_submit_liquidity_guard_would_pass`: single_source=26
- `scalp_sim_pre_submit_overbought_guard_would_block`: single_source=2
- `scalp_sim_pre_submit_overbought_guard_would_pass`: single_source=42
- `sell_order_sent`: ok=1, single_source=4
- `stop_line_touch_avg_down_price_improvement_deferred`: single_source=2

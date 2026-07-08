# Quote Consistency Report 2026-07-08

- runtime_family: `quote_consistency_normalization`
- observed_count: `2128`
- rest_fallback_count: `346`
- safety_exit_count: `11`
- ev_input_blocked_count: `72`
- missing_required_fields: `0`

## Verifier Findings
- `ok` `none`

## Stage State Counts
- `ai_holding_review`: ok=2, single_source=136, stale=26
- `entry_reprice_after_submit_blocked`: ok=2, single_source=5
- `entry_reprice_after_submit_evaluated`: ok=2, single_source=5
- `hard_stop_quote_revalidation_blocked`: single_source=8
- `latency_block`: single_source=753, stale=8
- `latency_pass`: single_source=54
- `scale_in_price_guard_block`: single_source=8, stale=6
- `scale_in_price_p2_observe`: single_source=12, stale=10
- `scale_in_price_resolved`: single_source=4, stale=10
- `scale_in_qty_block`: single_source=30, stale=8
- `scalp_entry_action_decision_snapshot`: single_source=553
- `scalp_sim_buy_order_virtual_pending`: single_source=148
- `scalp_sim_pre_submit_liquidity_guard_would_block`: single_source=64
- `scalp_sim_pre_submit_liquidity_guard_would_pass`: single_source=84
- `scalp_sim_pre_submit_overbought_guard_would_block`: single_source=4
- `scalp_sim_pre_submit_overbought_guard_would_pass`: single_source=144
- `sell_order_sent`: ok=1, single_source=14, stale=4, warning=1
- `stop_line_touch_avg_down_price_improvement_deferred`: single_source=12
- `stop_line_touch_first_touch_avgdown_decision_blocked`: single_source=10

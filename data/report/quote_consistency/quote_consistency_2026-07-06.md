# Quote Consistency Report 2026-07-06

- runtime_family: `quote_consistency_normalization`
- observed_count: `1251`
- rest_fallback_count: `140`
- safety_exit_count: `8`
- ev_input_blocked_count: `96`
- missing_required_fields: `1`

## Verifier Findings
- `warning` `quote_consistency_source_missing`
- `warning` `quote_consistency_required_fields_excluded`

## Stage State Counts
- `ai_holding_review`: single_source=102, stale=75
- `entry_reprice_after_submit_blocked`: diverged=1, ok=4, single_source=4, warning=3
- `entry_reprice_after_submit_evaluated`: diverged=1, ok=4, single_source=4, warning=3
- `hard_stop_quote_revalidation_blocked`: single_source=6
- `latency_block`: single_source=621, stale=1
- `latency_pass`: single_source=36
- `scale_in_price_guard_block`: single_source=1
- `scale_in_price_p2_observe`: single_source=11, stale=3
- `scale_in_price_resolved`: single_source=7, stale=3
- `scale_in_qty_block`: single_source=11, stale=11
- `scalp_entry_action_decision_snapshot`: single_source=99
- `scalp_sim_buy_order_virtual_pending`: single_source=73
- `scalp_sim_pre_submit_liquidity_guard_would_block`: single_source=37
- `scalp_sim_pre_submit_liquidity_guard_would_pass`: single_source=36
- `scalp_sim_pre_submit_overbought_guard_would_pass`: single_source=73
- `sell_order_blocked`: single_source=1
- `sell_order_sent`: ok=1, single_source=16, warning=1
- `stop_line_touch_avg_down_price_improvement_deferred`: single_source=1
- `stop_line_touch_first_touch_avgdown_decision_blocked`: single_source=1

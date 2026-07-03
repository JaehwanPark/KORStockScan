# Quote Consistency Report 2026-07-03

- runtime_family: `quote_consistency_normalization`
- observed_count: `1871`
- rest_fallback_count: `610`
- safety_exit_count: `486`
- ev_input_blocked_count: `499`
- missing_required_fields: `5`

## Verifier Findings
- `warning` `quote_consistency_source_missing`
- `warning` `quote_consistency_required_fields_excluded`

## Stage State Counts
- `ai_holding_review`: ok=2, single_source=115, stale=162
- `entry_reprice_after_submit_blocked`: diverged=2, ok=10, single_source=18, stale=32, warning=3
- `entry_reprice_after_submit_evaluated`: diverged=2, ok=10, single_source=18, stale=32, warning=3
- `hard_stop_quote_revalidation_blocked`: single_source=333, stale=103
- `latency_block`: single_source=389, stale=44
- `latency_pass`: ok=10, single_source=51, warning=1
- `scale_in_price_guard_block`: single_source=1, stale=4
- `scale_in_price_p2_observe`: single_source=19, stale=3
- `scale_in_price_resolved`: single_source=1, stale=1
- `scale_in_qty_block`: single_source=12, stale=11
- `scale_in_quote_consistency_defensive_bypass`: stale=2
- `scalp_entry_action_decision_snapshot`: single_source=64, stale=7
- `scalp_sim_buy_order_virtual_pending`: single_source=47, stale=1
- `scalp_sim_entry_submit_revalidation_warning`: stale=1
- `scalp_sim_pre_submit_liquidity_guard_would_block`: single_source=18
- `scalp_sim_pre_submit_liquidity_guard_would_pass`: single_source=29, stale=1
- `scalp_sim_pre_submit_overbought_guard_would_pass`: single_source=47, stale=1
- `sell_order_blocked`: single_source=87
- `sell_order_sent`: single_source=16, stale=4
- `stop_line_touch_avg_down_price_improvement_deferred`: diverged=2, single_source=5
- `stop_line_touch_avg_down_rest_quote_only_confirmation_blocked`: single_source=57, stale=79
- `stop_line_touch_mandatory_avg_down_blocked`: single_source=1
- `stop_line_touch_mandatory_avg_down_candidate`: diverged=2, single_source=4
- `stop_line_touch_mandatory_avg_down_submitted`: diverged=2, single_source=2

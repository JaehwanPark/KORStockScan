# Quote Consistency Report 2026-07-01

- runtime_family: `quote_consistency_normalization`
- observed_count: `3604`
- rest_fallback_count: `981`
- safety_exit_count: `255`
- ev_input_blocked_count: `1630`
- missing_required_fields: `92`

## Verifier Findings
- `warning` `quote_consistency_source_missing`
- `warning` `quote_consistency_required_fields_excluded`

## Stage State Counts
- `entry_reprice_after_submit_blocked`: ok=19, single_source=40, stale=3, warning=2
- `entry_reprice_after_submit_evaluated`: ok=19, single_source=41, stale=3, warning=2
- `hard_stop_quote_revalidation_blocked`: single_source=204, stale=48
- `latency_block`: single_source=710, stale=174
- `latency_pass`: ok=3, single_source=135
- `scale_in_price_guard_block`: single_source=85, stale=121
- `scale_in_price_p2_observe`: single_source=9, stale=22
- `scale_in_price_resolved`: single_source=1, stale=1
- `scale_in_qty_block`: single_source=43, stale=21
- `scale_in_quote_consistency_defensive_bypass`: stale=21
- `scalp_entry_action_decision_snapshot`: single_source=209
- `scalp_sim_buy_order_virtual_pending`: single_source=67
- `scalp_sim_pre_submit_liquidity_guard_would_block`: single_source=11
- `scalp_sim_pre_submit_liquidity_guard_would_pass`: single_source=56
- `scalp_sim_pre_submit_overbought_guard_would_pass`: single_source=67
- `sell_order_sent`: single_source=20, stale=6
- `stop_line_touch_avg_down_price_improvement_deferred`: single_source=309
- `stop_line_touch_avg_down_rest_quote_only_confirmation_blocked`: single_source=1, stale=1125
- `stop_line_touch_mandatory_avg_down_candidate`: single_source=3
- `stop_line_touch_mandatory_avg_down_submitted`: single_source=3

# Quote Consistency Report 2026-07-02

- runtime_family: `quote_consistency_normalization`
- observed_count: `1993`
- rest_fallback_count: `424`
- safety_exit_count: `115`
- ev_input_blocked_count: `625`
- missing_required_fields: `24`

## Verifier Findings
- `warning` `quote_consistency_source_missing`
- `warning` `quote_consistency_required_fields_excluded`

## Stage State Counts
- `entry_reprice_after_submit_blocked`: ok=9, single_source=29, stale=14, warning=4
- `entry_reprice_after_submit_evaluated`: ok=9, single_source=29, stale=14, warning=4
- `hard_stop_quote_revalidation_blocked`: single_source=47, stale=68
- `latency_block`: single_source=253, stale=120
- `latency_pass`: ok=3, single_source=57
- `scale_in_price_guard_block`: single_source=16, stale=14
- `scale_in_price_p2_observe`: single_source=15, stale=10
- `scale_in_price_resolved`: single_source=7, stale=8
- `scale_in_qty_block`: single_source=12, stale=18
- `scale_in_quote_consistency_defensive_bypass`: stale=7
- `scalp_entry_action_decision_snapshot`: single_source=136, stale=7
- `scalp_sim_buy_order_virtual_pending`: single_source=97, stale=3
- `scalp_sim_entry_submit_revalidation_warning`: stale=3
- `scalp_sim_pre_submit_liquidity_guard_would_block`: single_source=43
- `scalp_sim_pre_submit_liquidity_guard_would_pass`: single_source=54, stale=3
- `scalp_sim_pre_submit_overbought_guard_would_pass`: single_source=97, stale=3
- `sell_order_blocked`: single_source=79
- `sell_order_sent`: single_source=13, stale=6
- `stop_line_touch_avg_down_price_improvement_deferred`: diverged=29, single_source=127
- `stop_line_touch_avg_down_rest_quote_only_confirmation_blocked`: single_source=235, stale=282
- `stop_line_touch_mandatory_avg_down_blocked`: single_source=2
- `stop_line_touch_mandatory_avg_down_candidate`: single_source=4
- `stop_line_touch_mandatory_avg_down_submitted`: single_source=3

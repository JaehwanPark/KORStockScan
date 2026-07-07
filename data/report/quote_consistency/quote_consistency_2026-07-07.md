# Quote Consistency Report 2026-07-07

- runtime_family: `quote_consistency_normalization`
- observed_count: `1000`
- rest_fallback_count: `277`
- safety_exit_count: `25`
- ev_input_blocked_count: `73`
- missing_required_fields: `4`

## Verifier Findings
- `warning` `quote_consistency_source_missing`
- `warning` `quote_consistency_required_fields_excluded`

## Stage State Counts
- `ai_holding_review`: single_source=195, stale=21
- `entry_reprice_after_submit_blocked`: diverged=1, ok=8, single_source=14
- `entry_reprice_after_submit_evaluated`: diverged=1, ok=8, single_source=14
- `hard_stop_quote_revalidation_blocked`: single_source=21
- `latency_block`: single_source=332
- `latency_pass`: ok=1, single_source=42
- `scale_in_price_guard_block`: single_source=4
- `scale_in_price_p2_observe`: single_source=3
- `scale_in_qty_block`: single_source=13, stale=15
- `scalp_entry_action_decision_snapshot`: single_source=51
- `scalp_sim_buy_order_virtual_pending`: single_source=50
- `scalp_sim_pre_submit_liquidity_guard_would_block`: single_source=15
- `scalp_sim_pre_submit_liquidity_guard_would_pass`: single_source=35
- `scalp_sim_pre_submit_overbought_guard_would_pass`: single_source=50
- `sell_order_sent`: ok=2, single_source=16, stale=3, warning=1
- `stop_line_touch_avg_down_rest_quote_only_confirmation_blocked`: single_source=56, stale=28

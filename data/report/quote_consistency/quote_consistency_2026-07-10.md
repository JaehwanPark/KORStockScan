# Quote Consistency Report 2026-07-10

- runtime_family: `quote_consistency_normalization`
- observed_count: `1502`
- rest_fallback_count: `544`
- safety_exit_count: `0`
- ev_input_blocked_count: `50`
- missing_required_fields: `0`

## Verifier Findings
- `ok` `none`

## Stage State Counts
- `ai_holding_review`: single_source=117
- `entry_reprice_after_submit_blocked`: ok=3, single_source=2, warning=1
- `entry_reprice_after_submit_evaluated`: ok=6, single_source=5, warning=1
- `latency_block`: single_source=179, stale=3
- `latency_pass`: single_source=28
- `rising_missed_one_share_entry`: single_source=85
- `rising_missed_scout_quality_guard_blocked`: single_source=164
- `scale_in_price_guard_block`: stale=6
- `scale_in_price_p2_observe`: single_source=6, stale=2
- `scale_in_price_resolved`: single_source=3, stale=2
- `scale_in_qty_block`: single_source=18, stale=32
- `scalp_entry_action_decision_snapshot`: single_source=595, stale=3
- `scalp_sim_buy_order_virtual_pending`: single_source=76
- `scalp_sim_pre_submit_liquidity_guard_would_block`: single_source=24
- `scalp_sim_pre_submit_liquidity_guard_would_pass`: single_source=52
- `scalp_sim_pre_submit_overbought_guard_would_pass`: single_source=76
- `sell_order_sent`: single_source=7, stale=2
- `stop_line_touch_avg_down_price_improvement_deferred`: single_source=2
- `stop_line_touch_first_touch_avgdown_decision_blocked`: single_source=2

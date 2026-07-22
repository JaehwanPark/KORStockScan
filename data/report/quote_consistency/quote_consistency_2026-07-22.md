# Quote Consistency Report 2026-07-22

- runtime_family: `quote_consistency_normalization`
- observed_count: `1153`
- rest_fallback_count: `227`
- safety_exit_count: `154`
- ev_input_blocked_count: `77`
- missing_required_fields: `0`

## Verifier Findings
- `ok` `none`

## Stage State Counts
- `ai_holding_review`: single_source=52, stale=70
- `entry_reprice_after_submit_blocked`: ok=7, single_source=15
- `entry_reprice_after_submit_evaluated`: ok=8, single_source=16
- `latency_block`: single_source=144, stale=3
- `latency_pass`: single_source=39
- `nxt_rising_missed_tp1_partial_order_sent`: single_source=1
- `residual_planned`: single_source=20
- `scale_in_price_p2_observe`: single_source=2
- `scale_in_price_resolved`: single_source=1
- `scalp_entry_action_decision_snapshot`: single_source=504, stale=3
- `scalp_sim_buy_order_virtual_pending`: single_source=32
- `scalp_sim_pre_submit_liquidity_guard_would_block`: single_source=2
- `scalp_sim_pre_submit_liquidity_guard_would_pass`: single_source=30
- `scalp_sim_pre_submit_overbought_guard_would_pass`: single_source=32
- `scalp_trailing_continuation_recheck`: ok=146, single_source=2, warning=2
- `scalp_trailing_loss_conversion_recheck`: ok=4
- `sell_order_sent`: ok=10, single_source=7, stale=1

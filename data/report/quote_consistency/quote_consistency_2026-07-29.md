# Quote Consistency Report 2026-07-29

- runtime_family: `quote_consistency_normalization`
- observed_count: `260`
- rest_fallback_count: `18`
- safety_exit_count: `67`
- ev_input_blocked_count: `5`
- missing_required_fields: `0`

## Verifier Findings
- `ok` `none`

## Stage State Counts
- `entry_reprice_after_submit_blocked`: ok=3
- `entry_reprice_after_submit_evaluated`: ok=6
- `fresh_spread_ai_recheck`: single_source=3, stale=1
- `latency_block`: single_source=26, stale=2
- `latency_pass`: single_source=22
- `scale_in_qty_block`: single_source=4
- `scalp_entry_action_decision_snapshot`: single_source=102, stale=2
- `scalp_fast_exit_claimed`: ok=1, single_source=3
- `scalp_sim_buy_order_virtual_pending`: single_source=6
- `scalp_sim_pre_submit_liquidity_guard_would_pass`: single_source=6
- `scalp_sim_pre_submit_overbought_guard_would_pass`: single_source=6
- `scalp_trailing_continuation_recheck`: ok=42, single_source=2, warning=6
- `scalp_trailing_loss_conversion_recheck`: ok=10, single_source=2, warning=4
- `sell_order_sent`: single_source=1

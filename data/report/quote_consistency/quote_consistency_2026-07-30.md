# Quote Consistency Report 2026-07-30

- runtime_family: `quote_consistency_normalization`
- observed_count: `471`
- rest_fallback_count: `10`
- safety_exit_count: `97`
- ev_input_blocked_count: `379`
- missing_required_fields: `0`

## Verifier Findings
- `ok` `none`

## Stage State Counts
- `ai_holding_review`: single_source=10, stale=9
- `entry_reprice_after_submit_blocked`: ok=1
- `entry_reprice_after_submit_evaluated`: ok=1
- `latency_block`: single_source=14
- `latency_pass`: single_source=4
- `scalp_entry_action_decision_snapshot`: single_source=32
- `scalp_fast_exit_quote_blocked`: diverged=3, missing=283, stale=84
- `scalp_sim_buy_order_virtual_pending`: single_source=6
- `scalp_sim_pre_submit_liquidity_guard_would_pass`: single_source=6
- `scalp_sim_pre_submit_overbought_guard_would_pass`: single_source=6
- `scalp_trailing_continuation_recheck`: ok=6
- `scalp_trailing_loss_conversion_recheck`: ok=4
- `sell_order_sent`: single_source=2

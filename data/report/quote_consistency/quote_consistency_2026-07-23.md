# Quote Consistency Report 2026-07-23

- runtime_family: `quote_consistency_normalization`
- observed_count: `726`
- rest_fallback_count: `122`
- safety_exit_count: `135`
- ev_input_blocked_count: `121`
- missing_required_fields: `0`

## Verifier Findings
- `ok` `none`

## Stage State Counts
- `ai_holding_review`: single_source=39, stale=6
- `entry_reprice_after_submit_blocked`: ok=7, single_source=1
- `entry_reprice_after_submit_evaluated`: ok=8, single_source=1
- `latency_block`: single_source=100
- `latency_pass`: single_source=16
- `residual_planned`: single_source=10
- `scale_in_price_p2_observe`: single_source=4
- `scale_in_qty_block`: single_source=1
- `scalp_entry_action_decision_snapshot`: single_source=314
- `scalp_fast_exit_claimed`: single_source=2
- `scalp_fast_exit_quote_blocked`: single_source=1, stale=112
- `scalp_sim_buy_order_virtual_pending`: single_source=24
- `scalp_sim_pre_submit_liquidity_guard_would_block`: single_source=2
- `scalp_sim_pre_submit_liquidity_guard_would_pass`: single_source=22
- `scalp_sim_pre_submit_overbought_guard_would_pass`: single_source=24
- `scalp_trailing_continuation_recheck`: ok=16
- `scalp_trailing_loss_conversion_recheck`: ok=4, warning=2
- `sell_order_sent`: ok=4, single_source=3, stale=2
- `trailing_sell_quote_revalidation_blocked`: diverged=1

# Quote Consistency Report 2026-07-28

- runtime_family: `quote_consistency_normalization`
- observed_count: `455`
- rest_fallback_count: `52`
- safety_exit_count: `96`
- ev_input_blocked_count: `38`
- missing_required_fields: `0`

## Verifier Findings
- `ok` `none`

## Stage State Counts
- `ai_holding_review`: single_source=33
- `entry_reprice_after_submit_evaluated`: ok=1
- `hard_stop_quote_revalidation_blocked`: single_source=4
- `latency_block`: single_source=60, stale=2
- `latency_pass`: single_source=24
- `residual_planned`: single_source=2
- `scalp_entry_action_decision_snapshot`: single_source=134, stale=2
- `scalp_fast_exit_claimed`: ok=8, single_source=79, warning=1
- `scalp_fast_exit_quote_blocked`: diverged=1, single_source=3, stale=29
- `scalp_trailing_continuation_recheck`: ok=32, single_source=4, warning=2
- `scalp_trailing_loss_conversion_recheck`: ok=10, single_source=2
- `scalping_discretionary_sell_quote_revalidation_blocked`: diverged=4
- `sell_order_sent`: ok=3, single_source=9, warning=6

# Quote Consistency Report 2026-07-14

- runtime_family: `quote_consistency_normalization`
- observed_count: `338`
- rest_fallback_count: `70`
- safety_exit_count: `0`
- ev_input_blocked_count: `10`
- missing_required_fields: `0`

## Verifier Findings
- `ok` `none`

## Stage State Counts
- `ai_holding_review`: single_source=32
- `entry_reprice_after_submit_blocked`: single_source=1, warning=1
- `entry_reprice_after_submit_evaluated`: single_source=1, warning=1
- `latency_block`: single_source=25
- `latency_pass`: single_source=1
- `scalp_entry_action_decision_snapshot`: single_source=138, stale=2
- `scalp_sim_buy_order_virtual_pending`: single_source=42, stale=2
- `scalp_sim_entry_submit_revalidation_warning`: stale=2
- `scalp_sim_pre_submit_liquidity_guard_would_block`: single_source=16
- `scalp_sim_pre_submit_liquidity_guard_would_pass`: single_source=26, stale=2
- `scalp_sim_pre_submit_overbought_guard_would_pass`: single_source=42, stale=2
- `sell_order_sent`: ok=2

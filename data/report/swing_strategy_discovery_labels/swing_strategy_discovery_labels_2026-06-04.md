# Swing Strategy Discovery Labels - 2026-06-04

- generated_at: `2026-06-04T17:59:01`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `5480`
- arm_status_counts: `{'ENTERED': 1894, 'EXPIRED': 1459, 'EXITED': 228, 'PENDING_ENTRY': 1899}`
- label_status_counts: `{'labeled': 2350, 'pending_future_quotes': 13734, 'expired_entry_no_trigger': 5836}`
- maturity_status_counts: `{'pending_future_quotes': 3793, 'matured_no_entry': 1459, 'matured_labeled': 228}`
- pending_future_quote_count: `13734`
- bottom_rebound_processed_arm_count: `504`
- bottom_rebound_label_status_counts: `{'labeled': 385, 'pending_future_quotes': 1631}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

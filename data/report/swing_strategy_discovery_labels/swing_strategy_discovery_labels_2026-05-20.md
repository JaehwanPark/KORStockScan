# Swing Strategy Discovery Labels - 2026-05-20

- generated_at: `2026-06-01T18:20:08`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `400`
- arm_status_counts: `{'ENTERED': 103, 'EXPIRED': 287, 'EXITED': 10}`
- label_status_counts: `{'labeled': 123, 'pending_future_quotes': 329, 'expired_entry_no_trigger': 1148}`
- maturity_status_counts: `{'pending_future_quotes': 103, 'matured_no_entry': 287, 'matured_labeled': 10}`
- pending_future_quote_count: `329`
- bottom_rebound_processed_arm_count: `0`
- bottom_rebound_label_status_counts: `{}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

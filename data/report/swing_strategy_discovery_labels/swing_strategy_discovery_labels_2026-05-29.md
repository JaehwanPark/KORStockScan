# Swing Strategy Discovery Labels - 2026-05-29

- generated_at: `2026-06-01T18:53:58`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `3954`
- arm_status_counts: `{'ENTERED': 997, 'EXPIRED': 845, 'EXITED': 54, 'PENDING_ENTRY': 2058}`
- label_status_counts: `{'labeled': 1105, 'pending_future_quotes': 11331, 'expired_entry_no_trigger': 3380}`
- maturity_status_counts: `{'pending_future_quotes': 3055, 'matured_no_entry': 845, 'matured_labeled': 54}`
- pending_future_quote_count: `11331`
- bottom_rebound_processed_arm_count: `306`
- bottom_rebound_label_status_counts: `{'labeled': 137, 'pending_future_quotes': 1087}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

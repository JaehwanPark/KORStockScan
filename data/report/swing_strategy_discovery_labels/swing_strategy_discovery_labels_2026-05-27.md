# Swing Strategy Discovery Labels - 2026-05-27

- generated_at: `2026-05-27T19:06:30`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `2272`
- arm_status_counts: `{'ENTERED': 407, 'PENDING_ENTRY': 1649, 'EXITED': 84, 'EXPIRED': 132}`
- label_status_counts: `{'labeled': 575, 'pending_future_quotes': 7985, 'expired_entry_no_trigger': 528}`
- maturity_status_counts: `{'pending_future_quotes': 2056, 'matured_labeled': 84, 'matured_no_entry': 132}`
- pending_future_quote_count: `7985`
- bottom_rebound_processed_arm_count: `0`
- bottom_rebound_label_status_counts: `{}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

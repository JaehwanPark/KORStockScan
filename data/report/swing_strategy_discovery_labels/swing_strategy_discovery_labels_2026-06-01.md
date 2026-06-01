# Swing Strategy Discovery Labels - 2026-06-01

- generated_at: `2026-06-01T19:01:14`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `4354`
- arm_status_counts: `{'ENTERED': 943, 'EXPIRED': 855, 'EXITED': 41, 'PENDING_ENTRY': 2515}`
- label_status_counts: `{'labeled': 1025, 'pending_future_quotes': 12971, 'expired_entry_no_trigger': 3420}`
- maturity_status_counts: `{'pending_future_quotes': 3458, 'matured_no_entry': 855, 'matured_labeled': 41}`
- pending_future_quote_count: `12971`
- bottom_rebound_processed_arm_count: `306`
- bottom_rebound_label_status_counts: `{'labeled': 130, 'pending_future_quotes': 1094}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

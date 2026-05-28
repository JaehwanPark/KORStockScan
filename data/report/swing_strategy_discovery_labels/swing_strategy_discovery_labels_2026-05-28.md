# Swing Strategy Discovery Labels - 2026-05-28

- generated_at: `2026-05-28T13:08:59`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `2854`
- arm_status_counts: `{'ENTERED': 918, 'PENDING_ENTRY': 1565, 'EXITED': 165, 'EXPIRED': 206}`
- label_status_counts: `{'labeled': 1248, 'pending_future_quotes': 9344, 'expired_entry_no_trigger': 824}`
- maturity_status_counts: `{'pending_future_quotes': 2483, 'matured_labeled': 165, 'matured_no_entry': 206}`
- pending_future_quote_count: `9344`
- bottom_rebound_processed_arm_count: `102`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 408}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

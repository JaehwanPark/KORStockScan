# Swing Strategy Discovery Labels - 2026-05-22

- generated_at: `2026-05-22T17:02:58`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `1200`
- arm_status_counts: `{'ENTERED': 220, 'PENDING_ENTRY': 898, 'EXITED': 32, 'EXPIRED': 50}`
- label_status_counts: `{'labeled': 284, 'pending_future_quotes': 4316, 'expired_entry_no_trigger': 200}`
- maturity_status_counts: `{'pending_future_quotes': 1118, 'matured_labeled': 32, 'matured_no_entry': 50}`
- pending_future_quote_count: `4316`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

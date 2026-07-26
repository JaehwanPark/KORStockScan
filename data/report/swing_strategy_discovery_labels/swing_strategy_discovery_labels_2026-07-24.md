# Swing Strategy Discovery Labels - 2026-07-24

- generated_at: `2026-07-24T20:40:23`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `25257`
- arm_status_counts: `{'EXITED': 5083, 'EXPIRED': 13122, 'ENTERED': 4337, 'PENDING_ENTRY': 2715}`
- label_status_counts: `{'labeled': 23701, 'expired_entry_no_trigger': 52488, 'pending_future_quotes': 24839}`
- maturity_status_counts: `{'matured_labeled': 5083, 'matured_no_entry': 13122, 'pending_future_quotes': 7052}`
- pending_future_quote_count: `24839`
- bottom_rebound_processed_arm_count: `3345`
- bottom_rebound_label_status_counts: `{'labeled': 5450, 'expired_entry_no_trigger': 4288, 'pending_future_quotes': 3642}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

# Swing Strategy Discovery Labels - 2026-07-28

- generated_at: `2026-07-29T07:34:36`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `26481`
- arm_status_counts: `{'EXITED': 5850, 'EXPIRED': 14651, 'ENTERED': 4753, 'PENDING_ENTRY': 1227}`
- label_status_counts: `{'labeled': 26576, 'expired_entry_no_trigger': 58604, 'pending_future_quotes': 20744}`
- maturity_status_counts: `{'matured_labeled': 5850, 'matured_no_entry': 14651, 'pending_future_quotes': 5980}`
- pending_future_quote_count: `20744`
- bottom_rebound_processed_arm_count: `3441`
- bottom_rebound_label_status_counts: `{'labeled': 5706, 'expired_entry_no_trigger': 5008, 'pending_future_quotes': 3050}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

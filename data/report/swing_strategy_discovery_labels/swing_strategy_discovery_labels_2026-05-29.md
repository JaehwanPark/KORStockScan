# Swing Strategy Discovery Labels - 2026-05-29

- generated_at: `2026-05-29T16:47:13`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `3604`
- arm_status_counts: `{'ENTERED': 769, 'EXPIRED': 512, 'EXITED': 59, 'PENDING_ENTRY': 2264}`
- label_status_counts: `{'labeled': 887, 'pending_future_quotes': 11481, 'expired_entry_no_trigger': 2048}`
- maturity_status_counts: `{'pending_future_quotes': 3033, 'matured_no_entry': 512, 'matured_labeled': 59}`
- pending_future_quote_count: `11481`
- bottom_rebound_processed_arm_count: `204`
- bottom_rebound_label_status_counts: `{'labeled': 67, 'pending_future_quotes': 749}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

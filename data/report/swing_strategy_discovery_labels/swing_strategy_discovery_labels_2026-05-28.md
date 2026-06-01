# Swing Strategy Discovery Labels - 2026-05-28

- generated_at: `2026-06-01T18:46:21`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `3204`
- arm_status_counts: `{'ENTERED': 1053, 'EXPIRED': 839, 'EXITED': 66, 'PENDING_ENTRY': 1246}`
- label_status_counts: `{'labeled': 1185, 'pending_future_quotes': 8275, 'expired_entry_no_trigger': 3356}`
- maturity_status_counts: `{'pending_future_quotes': 2299, 'matured_no_entry': 839, 'matured_labeled': 66}`
- pending_future_quote_count: `8275`
- bottom_rebound_processed_arm_count: `204`
- bottom_rebound_label_status_counts: `{'labeled': 144, 'pending_future_quotes': 672}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

# Swing Strategy Discovery Labels - 2026-05-28

- generated_at: `2026-05-29T14:17:27`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `3204`
- arm_status_counts: `{'ENTERED': 876, 'EXPIRED': 503, 'EXITED': 84, 'PENDING_ENTRY': 1741}`
- label_status_counts: `{'labeled': 1044, 'pending_future_quotes': 9760, 'expired_entry_no_trigger': 2012}`
- maturity_status_counts: `{'pending_future_quotes': 2617, 'matured_no_entry': 503, 'matured_labeled': 84}`
- pending_future_quote_count: `9760`
- bottom_rebound_processed_arm_count: `204`
- bottom_rebound_label_status_counts: `{'labeled': 73, 'pending_future_quotes': 743}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

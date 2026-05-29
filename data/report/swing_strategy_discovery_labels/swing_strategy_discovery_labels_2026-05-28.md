# Swing Strategy Discovery Labels - 2026-05-28

- generated_at: `2026-05-29T13:36:21`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `3204`
- arm_status_counts: `{'ENTERED': 949, 'EXPIRED': 484, 'EXITED': 96, 'PENDING_ENTRY': 1675}`
- label_status_counts: `{'labeled': 1141, 'pending_future_quotes': 9739, 'expired_entry_no_trigger': 1936}`
- maturity_status_counts: `{'pending_future_quotes': 2624, 'matured_no_entry': 484, 'matured_labeled': 96}`
- pending_future_quote_count: `9739`
- bottom_rebound_processed_arm_count: `204`
- bottom_rebound_label_status_counts: `{'labeled': 81, 'pending_future_quotes': 735}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

# Swing Strategy Discovery Labels - 2026-05-26

- generated_at: `2026-05-26T16:26:05`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `1600`
- arm_status_counts: `{'ENTERED': 346, 'PENDING_ENTRY': 1088, 'EXITED': 71, 'EXPIRED': 95}`
- label_status_counts: `{'labeled': 488, 'pending_future_quotes': 5532, 'expired_entry_no_trigger': 380}`
- maturity_status_counts: `{'pending_future_quotes': 1434, 'matured_labeled': 71, 'matured_no_entry': 95}`
- pending_future_quote_count: `5532`
- bottom_rebound_processed_arm_count: `0`
- bottom_rebound_label_status_counts: `{}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

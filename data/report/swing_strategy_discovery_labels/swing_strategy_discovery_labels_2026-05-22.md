# Swing Strategy Discovery Labels - 2026-05-22

- generated_at: `2026-06-01T15:55:50`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `400`
- arm_status_counts: `{'ENTERED': 149, 'PENDING_ENTRY': 197, 'EXPIRED': 43, 'EXITED': 11}`
- label_status_counts: `{'labeled': 171, 'pending_future_quotes': 1257, 'expired_entry_no_trigger': 172}`
- maturity_status_counts: `{'pending_future_quotes': 346, 'matured_no_entry': 43, 'matured_labeled': 11}`
- pending_future_quote_count: `1257`
- bottom_rebound_processed_arm_count: `0`
- bottom_rebound_label_status_counts: `{}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

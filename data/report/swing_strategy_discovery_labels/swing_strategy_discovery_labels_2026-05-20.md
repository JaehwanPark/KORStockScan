# Swing Strategy Discovery Labels - 2026-05-20

- generated_at: `2026-06-01T15:45:59`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `400`
- arm_status_counts: `{'ENTERED': 128, 'EXPIRED': 259, 'EXITED': 13}`
- label_status_counts: `{'labeled': 154, 'pending_future_quotes': 410, 'expired_entry_no_trigger': 1036}`
- maturity_status_counts: `{'pending_future_quotes': 128, 'matured_no_entry': 259, 'matured_labeled': 13}`
- pending_future_quote_count: `410`
- bottom_rebound_processed_arm_count: `0`
- bottom_rebound_label_status_counts: `{}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

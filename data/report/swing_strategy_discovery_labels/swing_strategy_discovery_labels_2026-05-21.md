# Swing Strategy Discovery Labels - 2026-05-21

- generated_at: `2026-06-01T18:23:55`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `800`
- arm_status_counts: `{'ENTERED': 210, 'EXPIRED': 570, 'EXITED': 20}`
- label_status_counts: `{'labeled': 250, 'pending_future_quotes': 670, 'expired_entry_no_trigger': 2280}`
- maturity_status_counts: `{'pending_future_quotes': 210, 'matured_no_entry': 570, 'matured_labeled': 20}`
- pending_future_quote_count: `670`
- bottom_rebound_processed_arm_count: `0`
- bottom_rebound_label_status_counts: `{}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

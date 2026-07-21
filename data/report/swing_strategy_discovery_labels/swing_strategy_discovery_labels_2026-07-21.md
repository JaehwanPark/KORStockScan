# Swing Strategy Discovery Labels - 2026-07-21

- generated_at: `2026-07-21T20:41:35`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `22393`
- arm_status_counts: `{'EXITED': 4837, 'EXPIRED': 11671, 'ENTERED': 3535, 'PENDING_ENTRY': 2350}`
- label_status_counts: `{'labeled': 21982, 'expired_entry_no_trigger': 46684, 'pending_future_quotes': 20906}`
- maturity_status_counts: `{'matured_labeled': 4837, 'matured_no_entry': 11671, 'pending_future_quotes': 5885}`
- pending_future_quote_count: `20906`
- bottom_rebound_processed_arm_count: `3057`
- bottom_rebound_label_status_counts: `{'labeled': 5342, 'expired_entry_no_trigger': 3784, 'pending_future_quotes': 3102}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

# Swing Strategy Discovery Labels - 2026-05-27

- generated_at: `2026-06-01T18:40:33`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `2454`
- arm_status_counts: `{'ENTERED': 708, 'EXPIRED': 767, 'EXITED': 39, 'PENDING_ENTRY': 940}`
- label_status_counts: `{'labeled': 786, 'pending_future_quotes': 5962, 'expired_entry_no_trigger': 3068}`
- maturity_status_counts: `{'pending_future_quotes': 1648, 'matured_no_entry': 767, 'matured_labeled': 39}`
- pending_future_quote_count: `5962`
- bottom_rebound_processed_arm_count: `102`
- bottom_rebound_label_status_counts: `{'labeled': 65, 'pending_future_quotes': 343}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

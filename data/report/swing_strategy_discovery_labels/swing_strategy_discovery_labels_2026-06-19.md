# Swing Strategy Discovery Labels - 2026-06-19

- generated_at: `2026-06-19T16:46:56`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `11740`
- arm_status_counts: `{'EXITED': 1273, 'EXPIRED': 5278, 'ENTERED': 3478, 'PENDING_ENTRY': 1711}`
- label_status_counts: `{'labeled': 8398, 'expired_entry_no_trigger': 21112, 'pending_future_quotes': 17450}`
- maturity_status_counts: `{'matured_labeled': 1273, 'matured_no_entry': 5278, 'pending_future_quotes': 5189}`
- pending_future_quote_count: `17450`
- bottom_rebound_processed_arm_count: `1596`
- bottom_rebound_label_status_counts: `{'labeled': 1460, 'pending_future_quotes': 3124, 'expired_entry_no_trigger': 1800}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

# Swing Strategy Discovery Labels - 2026-06-22

- generated_at: `2026-06-22T16:02:44`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `12277`
- arm_status_counts: `{'EXITED': 1710, 'EXPIRED': 5339, 'ENTERED': 3871, 'PENDING_ENTRY': 1357}`
- label_status_counts: `{'labeled': 9790, 'expired_entry_no_trigger': 21356, 'pending_future_quotes': 17962}`
- maturity_status_counts: `{'matured_labeled': 1710, 'matured_no_entry': 5339, 'pending_future_quotes': 5228}`
- pending_future_quote_count: `17962`
- bottom_rebound_processed_arm_count: `1701`
- bottom_rebound_label_status_counts: `{'labeled': 1801, 'pending_future_quotes': 3391, 'expired_entry_no_trigger': 1612}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

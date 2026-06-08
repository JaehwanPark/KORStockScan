# Swing Strategy Discovery Labels - 2026-06-08

- generated_at: `2026-06-08T17:05:21`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `6642`
- arm_status_counts: `{'EXITED': 388, 'ENTERED': 2323, 'EXPIRED': 2214, 'PENDING_ENTRY': 1717}`
- label_status_counts: `{'labeled': 3299, 'pending_future_quotes': 14413, 'expired_entry_no_trigger': 8856}`
- maturity_status_counts: `{'matured_labeled': 388, 'pending_future_quotes': 4040, 'matured_no_entry': 2214}`
- pending_future_quote_count: `14413`
- bottom_rebound_processed_arm_count: `690`
- bottom_rebound_label_status_counts: `{'labeled': 508, 'pending_future_quotes': 2088, 'expired_entry_no_trigger': 164}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

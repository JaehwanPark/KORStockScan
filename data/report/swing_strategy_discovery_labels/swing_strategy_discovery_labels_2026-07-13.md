# Swing Strategy Discovery Labels - 2026-07-13

- generated_at: `2026-07-13T20:35:53`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `17888`
- arm_status_counts: `{'EXITED': 3688, 'EXPIRED': 10237, 'ENTERED': 2687, 'PENDING_ENTRY': 1276}`
- label_status_counts: `{'labeled': 17278, 'expired_entry_no_trigger': 40948, 'pending_future_quotes': 13326}`
- maturity_status_counts: `{'matured_labeled': 3688, 'matured_no_entry': 10237, 'pending_future_quotes': 3963}`
- pending_future_quote_count: `13326`
- bottom_rebound_processed_arm_count: `2520`
- bottom_rebound_label_status_counts: `{'labeled': 3968, 'expired_entry_no_trigger': 3124, 'pending_future_quotes': 2988}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

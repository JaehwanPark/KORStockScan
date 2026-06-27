# Swing Strategy Discovery Labels - 2026-06-26

- generated_at: `2026-06-26T21:32:09`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `13755`
- arm_status_counts: `{'EXITED': 2108, 'EXPIRED': 6938, 'ENTERED': 3475, 'PENDING_ENTRY': 1234}`
- label_status_counts: `{'labeled': 11414, 'expired_entry_no_trigger': 27752, 'pending_future_quotes': 15854}`
- maturity_status_counts: `{'matured_labeled': 2108, 'matured_no_entry': 6938, 'pending_future_quotes': 4709}`
- pending_future_quote_count: `15854`
- bottom_rebound_processed_arm_count: `1803`
- bottom_rebound_label_status_counts: `{'labeled': 2202, 'pending_future_quotes': 2958, 'expired_entry_no_trigger': 2052}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

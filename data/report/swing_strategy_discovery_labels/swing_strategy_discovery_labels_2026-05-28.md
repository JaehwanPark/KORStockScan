# Swing Strategy Discovery Labels - 2026-05-28

- generated_at: `2026-05-28T18:08:48`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `2854`
- arm_status_counts: `{'ENTERED': 619, 'PENDING_ENTRY': 1947, 'EXITED': 70, 'EXPIRED': 218}`
- label_status_counts: `{'labeled': 759, 'pending_future_quotes': 9785, 'expired_entry_no_trigger': 872}`
- maturity_status_counts: `{'pending_future_quotes': 2566, 'matured_labeled': 70, 'matured_no_entry': 218}`
- pending_future_quote_count: `9785`
- bottom_rebound_processed_arm_count: `102`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 408}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

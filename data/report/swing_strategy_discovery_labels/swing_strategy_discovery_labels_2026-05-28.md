# Swing Strategy Discovery Labels - 2026-05-28

- generated_at: `2026-05-29T11:14:33`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `3102`
- arm_status_counts: `{'ENTERED': 1318, 'EXPIRED': 384, 'EXITED': 261, 'PENDING_ENTRY': 1139}`
- label_status_counts: `{'labeled': 1840, 'pending_future_quotes': 9032, 'expired_entry_no_trigger': 1536}`
- maturity_status_counts: `{'pending_future_quotes': 2457, 'matured_no_entry': 384, 'matured_labeled': 261}`
- pending_future_quote_count: `9032`
- bottom_rebound_processed_arm_count: `102`
- bottom_rebound_label_status_counts: `{'labeled': 114, 'pending_future_quotes': 294}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

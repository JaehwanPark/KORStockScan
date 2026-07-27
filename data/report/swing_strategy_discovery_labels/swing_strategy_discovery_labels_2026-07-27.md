# Swing Strategy Discovery Labels - 2026-07-27

- generated_at: `2026-07-27T23:50:38`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `25841`
- arm_status_counts: `{'EXITED': 5461, 'EXPIRED': 14103, 'ENTERED': 4921, 'PENDING_ENTRY': 1356}`
- label_status_counts: `{'labeled': 25710, 'expired_entry_no_trigger': 56412, 'pending_future_quotes': 21242}`
- maturity_status_counts: `{'matured_labeled': 5461, 'matured_no_entry': 14103, 'pending_future_quotes': 6277}`
- pending_future_quote_count: `21242`
- bottom_rebound_processed_arm_count: `3441`
- bottom_rebound_label_status_counts: `{'labeled': 5660, 'expired_entry_no_trigger': 4628, 'pending_future_quotes': 3476}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

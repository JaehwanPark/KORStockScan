# Swing Strategy Discovery Labels - 2026-06-15

- generated_at: `2026-06-15T16:12:18`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `9390`
- arm_status_counts: `{'EXITED': 1120, 'ENTERED': 3268, 'EXPIRED': 3292, 'PENDING_ENTRY': 1710}`
- label_status_counts: `{'labeled': 6674, 'pending_future_quotes': 17718, 'expired_entry_no_trigger': 13168}`
- maturity_status_counts: `{'matured_labeled': 1120, 'pending_future_quotes': 4978, 'matured_no_entry': 3292}`
- pending_future_quote_count: `17718`
- bottom_rebound_processed_arm_count: `1206`
- bottom_rebound_label_status_counts: `{'labeled': 1040, 'pending_future_quotes': 3408, 'expired_entry_no_trigger': 376}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

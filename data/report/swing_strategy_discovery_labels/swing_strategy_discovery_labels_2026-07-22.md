# Swing Strategy Discovery Labels - 2026-07-22

- generated_at: `2026-07-22T20:43:40`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `23347`
- arm_status_counts: `{'EXITED': 4850, 'EXPIRED': 12257, 'ENTERED': 3835, 'PENDING_ENTRY': 2405}`
- label_status_counts: `{'labeled': 22450, 'expired_entry_no_trigger': 49028, 'pending_future_quotes': 21910}`
- maturity_status_counts: `{'matured_labeled': 4850, 'matured_no_entry': 12257, 'pending_future_quotes': 6240}`
- pending_future_quote_count: `21910`
- bottom_rebound_processed_arm_count: `3147`
- bottom_rebound_label_status_counts: `{'labeled': 5422, 'expired_entry_no_trigger': 4068, 'pending_future_quotes': 3098}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

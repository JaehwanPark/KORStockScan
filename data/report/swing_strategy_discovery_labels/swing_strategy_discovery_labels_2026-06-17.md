# Swing Strategy Discovery Labels - 2026-06-17

- generated_at: `2026-06-17T16:23:00`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `10593`
- arm_status_counts: `{'EXITED': 1238, 'ENTERED': 3473, 'EXPIRED': 4047, 'PENDING_ENTRY': 1835}`
- label_status_counts: `{'labeled': 7486, 'pending_future_quotes': 18698, 'expired_entry_no_trigger': 16188}`
- maturity_status_counts: `{'matured_labeled': 1238, 'pending_future_quotes': 5308, 'matured_no_entry': 4047}`
- pending_future_quote_count: `18698`
- bottom_rebound_processed_arm_count: `1377`
- bottom_rebound_label_status_counts: `{'labeled': 1150, 'pending_future_quotes': 3426, 'expired_entry_no_trigger': 932}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

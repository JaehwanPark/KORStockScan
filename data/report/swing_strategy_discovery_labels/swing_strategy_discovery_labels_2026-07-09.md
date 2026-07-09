# Swing Strategy Discovery Labels - 2026-07-09

- generated_at: `2026-07-09T20:21:51`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `16792`
- arm_status_counts: `{'EXITED': 3648, 'EXPIRED': 9490, 'ENTERED': 2919, 'PENDING_ENTRY': 735}`
- label_status_counts: `{'labeled': 17198, 'expired_entry_no_trigger': 37960, 'pending_future_quotes': 12010}`
- maturity_status_counts: `{'matured_labeled': 3648, 'matured_no_entry': 9490, 'pending_future_quotes': 3654}`
- pending_future_quote_count: `12010`
- bottom_rebound_processed_arm_count: `2400`
- bottom_rebound_label_status_counts: `{'labeled': 3929, 'expired_entry_no_trigger': 2812, 'pending_future_quotes': 2859}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

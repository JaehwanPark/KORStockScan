# Swing Strategy Discovery Labels - 2026-07-23

- generated_at: `2026-07-23T20:34:22`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `24294`
- arm_status_counts: `{'EXITED': 4817, 'EXPIRED': 12812, 'ENTERED': 3964, 'PENDING_ENTRY': 2701}`
- label_status_counts: `{'labeled': 22743, 'expired_entry_no_trigger': 51248, 'pending_future_quotes': 23185}`
- maturity_status_counts: `{'matured_labeled': 4817, 'matured_no_entry': 12812, 'pending_future_quotes': 6665}`
- pending_future_quote_count: `23185`
- bottom_rebound_processed_arm_count: `3246`
- bottom_rebound_label_status_counts: `{'labeled': 5402, 'expired_entry_no_trigger': 4264, 'pending_future_quotes': 3318}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

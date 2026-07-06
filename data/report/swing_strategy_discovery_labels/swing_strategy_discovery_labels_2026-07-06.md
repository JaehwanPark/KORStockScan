# Swing Strategy Discovery Labels - 2026-07-06

- generated_at: `2026-07-06T20:28:24`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `15832`
- arm_status_counts: `{'EXITED': 3190, 'EXPIRED': 8726, 'ENTERED': 2883, 'PENDING_ENTRY': 1033}`
- label_status_counts: `{'labeled': 15514, 'expired_entry_no_trigger': 34904, 'pending_future_quotes': 12910}`
- maturity_status_counts: `{'matured_labeled': 3190, 'matured_no_entry': 8726, 'pending_future_quotes': 3916}`
- pending_future_quote_count: `12910`
- bottom_rebound_processed_arm_count: `2040`
- bottom_rebound_label_status_counts: `{'labeled': 3374, 'expired_entry_no_trigger': 2588, 'pending_future_quotes': 2198}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

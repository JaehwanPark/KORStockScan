# Swing Strategy Discovery Labels - 2026-06-29

- generated_at: `2026-06-29T20:21:32`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `13899`
- arm_status_counts: `{'EXITED': 2343, 'EXPIRED': 7419, 'ENTERED': 3262, 'PENDING_ENTRY': 875}`
- label_status_counts: `{'labeled': 11979, 'expired_entry_no_trigger': 29676, 'pending_future_quotes': 13941}`
- maturity_status_counts: `{'matured_labeled': 2343, 'matured_no_entry': 7419, 'pending_future_quotes': 4137}`
- pending_future_quote_count: `13941`
- bottom_rebound_processed_arm_count: `1803`
- bottom_rebound_label_status_counts: `{'labeled': 2324, 'expired_entry_no_trigger': 2284, 'pending_future_quotes': 2604}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

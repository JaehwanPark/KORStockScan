# Swing Strategy Discovery Labels - 2026-06-09

- generated_at: `2026-06-09T16:05:50`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `6983`
- arm_status_counts: `{'EXITED': 806, 'ENTERED': 2590, 'EXPIRED': 2406, 'PENDING_ENTRY': 1181}`
- label_status_counts: `{'labeled': 4507, 'pending_future_quotes': 13801, 'expired_entry_no_trigger': 9624}`
- maturity_status_counts: `{'matured_labeled': 806, 'pending_future_quotes': 3771, 'matured_no_entry': 2406}`
- pending_future_quote_count: `13801`
- bottom_rebound_processed_arm_count: `807`
- bottom_rebound_label_status_counts: `{'labeled': 791, 'pending_future_quotes': 2257, 'expired_entry_no_trigger': 180}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

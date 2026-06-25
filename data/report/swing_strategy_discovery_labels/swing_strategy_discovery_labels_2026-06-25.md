# Swing Strategy Discovery Labels - 2026-06-25

- generated_at: `2026-06-25T21:39:07`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `13355`
- arm_status_counts: `{'EXITED': 1985, 'EXPIRED': 6857, 'ENTERED': 3568, 'PENDING_ENTRY': 945}`
- label_status_counts: `{'labeled': 10820, 'expired_entry_no_trigger': 27428, 'pending_future_quotes': 15172}`
- maturity_status_counts: `{'matured_labeled': 1985, 'matured_no_entry': 6857, 'pending_future_quotes': 4513}`
- pending_future_quote_count: `15172`
- bottom_rebound_processed_arm_count: `1803`
- bottom_rebound_label_status_counts: `{'labeled': 2101, 'pending_future_quotes': 2979, 'expired_entry_no_trigger': 2132}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

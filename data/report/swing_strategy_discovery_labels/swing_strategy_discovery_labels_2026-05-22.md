# Swing Strategy Discovery Labels - 2026-05-22

- generated_at: `2026-06-01T18:28:56`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `1200`
- arm_status_counts: `{'ENTERED': 320, 'EXPIRED': 620, 'EXITED': 22, 'PENDING_ENTRY': 238}`
- label_status_counts: `{'labeled': 364, 'pending_future_quotes': 1956, 'expired_entry_no_trigger': 2480}`
- maturity_status_counts: `{'pending_future_quotes': 558, 'matured_no_entry': 620, 'matured_labeled': 22}`
- pending_future_quote_count: `1956`
- bottom_rebound_processed_arm_count: `0`
- bottom_rebound_label_status_counts: `{}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

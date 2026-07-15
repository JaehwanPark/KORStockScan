# Swing Strategy Discovery Labels - 2026-07-15

- generated_at: `2026-07-15T20:32:07`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `19562`
- arm_status_counts: `{'EXITED': 4141, 'EXPIRED': 10820, 'ENTERED': 2937, 'PENDING_ENTRY': 1664}`
- label_status_counts: `{'labeled': 18910, 'expired_entry_no_trigger': 43280, 'pending_future_quotes': 16058}`
- maturity_status_counts: `{'matured_labeled': 4141, 'matured_no_entry': 10820, 'pending_future_quotes': 4601}`
- pending_future_quote_count: `16058`
- bottom_rebound_processed_arm_count: `2754`
- bottom_rebound_label_status_counts: `{'labeled': 4369, 'expired_entry_no_trigger': 3340, 'pending_future_quotes': 3307}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

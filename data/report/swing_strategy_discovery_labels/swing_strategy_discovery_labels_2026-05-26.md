# Swing Strategy Discovery Labels - 2026-05-26

- generated_at: `2026-06-01T18:33:32`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `1872`
- arm_status_counts: `{'ENTERED': 513, 'EXPIRED': 704, 'EXITED': 36, 'PENDING_ENTRY': 619}`
- label_status_counts: `{'labeled': 585, 'pending_future_quotes': 4087, 'expired_entry_no_trigger': 2816}`
- maturity_status_counts: `{'pending_future_quotes': 1132, 'matured_no_entry': 704, 'matured_labeled': 36}`
- pending_future_quote_count: `4087`
- bottom_rebound_processed_arm_count: `0`
- bottom_rebound_label_status_counts: `{}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

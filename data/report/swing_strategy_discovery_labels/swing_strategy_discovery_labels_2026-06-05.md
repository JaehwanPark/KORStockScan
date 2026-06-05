# Swing Strategy Discovery Labels - 2026-06-05

- generated_at: `2026-06-05T18:01:41`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `6062`
- arm_status_counts: `{'EXITED': 301, 'ENTERED': 1934, 'EXPIRED': 1884, 'PENDING_ENTRY': 1943}`
- label_status_counts: `{'labeled': 2636, 'pending_future_quotes': 14076, 'expired_entry_no_trigger': 7536}`
- maturity_status_counts: `{'matured_labeled': 301, 'pending_future_quotes': 3877, 'matured_no_entry': 1884}`
- pending_future_quote_count: `14076`
- bottom_rebound_processed_arm_count: `606`
- bottom_rebound_label_status_counts: `{'labeled': 392, 'pending_future_quotes': 1924, 'expired_entry_no_trigger': 108}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

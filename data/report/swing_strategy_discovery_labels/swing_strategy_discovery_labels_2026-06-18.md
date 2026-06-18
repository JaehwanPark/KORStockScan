# Swing Strategy Discovery Labels - 2026-06-18

- generated_at: `2026-06-18T16:10:43`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `11163`
- arm_status_counts: `{'EXITED': 1276, 'ENTERED': 3558, 'EXPIRED': 4558, 'PENDING_ENTRY': 1771}`
- label_status_counts: `{'labeled': 7948, 'pending_future_quotes': 18472, 'expired_entry_no_trigger': 18232}`
- maturity_status_counts: `{'matured_labeled': 1276, 'pending_future_quotes': 5329, 'matured_no_entry': 4558}`
- pending_future_quote_count: `18472`
- bottom_rebound_processed_arm_count: `1491`
- bottom_rebound_label_status_counts: `{'labeled': 1284, 'pending_future_quotes': 3432, 'expired_entry_no_trigger': 1248}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

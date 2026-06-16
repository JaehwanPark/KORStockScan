# Swing Strategy Discovery Labels - 2026-06-16

- generated_at: `2026-06-16T16:15:43`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `10009`
- arm_status_counts: `{'EXITED': 1157, 'ENTERED': 3298, 'EXPIRED': 3926, 'PENDING_ENTRY': 1628}`
- label_status_counts: `{'labeled': 7015, 'pending_future_quotes': 17317, 'expired_entry_no_trigger': 15704}`
- maturity_status_counts: `{'matured_labeled': 1157, 'pending_future_quotes': 4926, 'matured_no_entry': 3926}`
- pending_future_quote_count: `17317`
- bottom_rebound_processed_arm_count: `1281`
- bottom_rebound_label_status_counts: `{'labeled': 1105, 'pending_future_quotes': 3139, 'expired_entry_no_trigger': 880}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

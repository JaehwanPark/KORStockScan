# Swing Strategy Discovery Labels - 2026-07-08

- generated_at: `2026-07-08T20:23:28`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `16536`
- arm_status_counts: `{'EXITED': 3414, 'EXPIRED': 9313, 'ENTERED': 2872, 'PENDING_ENTRY': 937}`
- label_status_counts: `{'labeled': 16302, 'expired_entry_no_trigger': 37252, 'pending_future_quotes': 12590}`
- maturity_status_counts: `{'matured_labeled': 3414, 'matured_no_entry': 9313, 'pending_future_quotes': 3809}`
- pending_future_quote_count: `12590`
- bottom_rebound_processed_arm_count: `2280`
- bottom_rebound_label_status_counts: `{'labeled': 3736, 'expired_entry_no_trigger': 2764, 'pending_future_quotes': 2620}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

# Swing Strategy Discovery Labels - 2026-07-16

- generated_at: `2026-07-16T21:26:53`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `20781`
- arm_status_counts: `{'EXITED': 4495, 'EXPIRED': 11333, 'ENTERED': 3309, 'PENDING_ENTRY': 1644}`
- label_status_counts: `{'labeled': 20654, 'expired_entry_no_trigger': 45332, 'pending_future_quotes': 17138}`
- maturity_status_counts: `{'matured_labeled': 4495, 'matured_no_entry': 11333, 'pending_future_quotes': 4953}`
- pending_future_quote_count: `17138`
- bottom_rebound_processed_arm_count: `2973`
- bottom_rebound_label_status_counts: `{'labeled': 4933, 'expired_entry_no_trigger': 3640, 'pending_future_quotes': 3319}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

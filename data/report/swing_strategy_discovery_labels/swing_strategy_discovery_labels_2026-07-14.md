# Swing Strategy Discovery Labels - 2026-07-14

- generated_at: `2026-07-14T20:35:43`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `18922`
- arm_status_counts: `{'EXITED': 4028, 'EXPIRED': 10249, 'ENTERED': 2929, 'PENDING_ENTRY': 1716}`
- label_status_counts: `{'labeled': 18546, 'expired_entry_no_trigger': 40996, 'pending_future_quotes': 16146}`
- maturity_status_counts: `{'matured_labeled': 4028, 'matured_no_entry': 10249, 'pending_future_quotes': 4645}`
- pending_future_quote_count: `16146`
- bottom_rebound_processed_arm_count: `2634`
- bottom_rebound_label_status_counts: `{'labeled': 4219, 'expired_entry_no_trigger': 3032, 'pending_future_quotes': 3285}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

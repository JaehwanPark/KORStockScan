# Swing Strategy Discovery Labels - 2026-06-30

- generated_at: `2026-06-30T20:23:56`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `14299`
- arm_status_counts: `{'EXITED': 2622, 'EXPIRED': 7530, 'ENTERED': 3344, 'PENDING_ENTRY': 803}`
- label_status_counts: `{'labeled': 13073, 'expired_entry_no_trigger': 30120, 'pending_future_quotes': 14003}`
- maturity_status_counts: `{'matured_labeled': 2622, 'matured_no_entry': 7530, 'pending_future_quotes': 4147}`
- pending_future_quote_count: `14003`
- bottom_rebound_processed_arm_count: `1803`
- bottom_rebound_label_status_counts: `{'labeled': 2514, 'expired_entry_no_trigger': 2204, 'pending_future_quotes': 2494}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

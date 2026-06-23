# Swing Strategy Discovery Labels - 2026-06-23

- generated_at: `2026-06-23T20:40:27`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `12867`
- arm_status_counts: `{'EXITED': 1716, 'EXPIRED': 5925, 'ENTERED': 3818, 'PENDING_ENTRY': 1408}`
- label_status_counts: `{'labeled': 10062, 'expired_entry_no_trigger': 23700, 'pending_future_quotes': 17706}`
- maturity_status_counts: `{'matured_labeled': 1716, 'matured_no_entry': 5925, 'pending_future_quotes': 5226}`
- pending_future_quote_count: `17706`
- bottom_rebound_processed_arm_count: `1803`
- bottom_rebound_label_status_counts: `{'labeled': 1861, 'pending_future_quotes': 3395, 'expired_entry_no_trigger': 1956}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

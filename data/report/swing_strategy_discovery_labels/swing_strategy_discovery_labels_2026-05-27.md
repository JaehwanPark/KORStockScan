# Swing Strategy Discovery Labels - 2026-05-27

- generated_at: `2026-05-27T22:15:45`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `582`
- arm_status_counts: `{'PENDING_ENTRY': 582}`
- label_status_counts: `{'pending_future_quotes': 2328}`
- maturity_status_counts: `{'pending_future_quotes': 582}`
- pending_future_quote_count: `2328`
- bottom_rebound_processed_arm_count: `102`
- bottom_rebound_label_status_counts: `{'pending_future_quotes': 408}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

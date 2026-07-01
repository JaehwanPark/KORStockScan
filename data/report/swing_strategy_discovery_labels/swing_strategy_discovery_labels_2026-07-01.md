# Swing Strategy Discovery Labels - 2026-07-01

- generated_at: `2026-07-01T20:24:21`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `14699`
- arm_status_counts: `{'EXITED': 2603, 'EXPIRED': 7918, 'ENTERED': 3108, 'PENDING_ENTRY': 1070}`
- label_status_counts: `{'labeled': 13038, 'expired_entry_no_trigger': 31672, 'pending_future_quotes': 14086}`
- maturity_status_counts: `{'matured_labeled': 2603, 'matured_no_entry': 7918, 'pending_future_quotes': 4178}`
- pending_future_quote_count: `14086`
- bottom_rebound_processed_arm_count: `1803`
- bottom_rebound_label_status_counts: `{'labeled': 2573, 'expired_entry_no_trigger': 2432, 'pending_future_quotes': 2207}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

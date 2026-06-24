# Swing Strategy Discovery Labels - 2026-06-24

- generated_at: `2026-06-24T20:22:10`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `12955`
- arm_status_counts: `{'EXITED': 2117, 'EXPIRED': 6039, 'ENTERED': 3931, 'PENDING_ENTRY': 868}`
- label_status_counts: `{'labeled': 11394, 'expired_entry_no_trigger': 24156, 'pending_future_quotes': 16270}`
- maturity_status_counts: `{'matured_labeled': 2117, 'matured_no_entry': 6039, 'pending_future_quotes': 4799}`
- pending_future_quote_count: `16270`
- bottom_rebound_processed_arm_count: `1803`
- bottom_rebound_label_status_counts: `{'labeled': 2173, 'pending_future_quotes': 3259, 'expired_entry_no_trigger': 1780}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

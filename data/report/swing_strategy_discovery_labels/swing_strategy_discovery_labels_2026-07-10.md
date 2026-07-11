# Swing Strategy Discovery Labels - 2026-07-10

- generated_at: `2026-07-11T13:04:22`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `17456`
- arm_status_counts: `{'EXITED': 3828, 'EXPIRED': 10029, 'ENTERED': 2842, 'PENDING_ENTRY': 757}`
- label_status_counts: `{'labeled': 17822, 'expired_entry_no_trigger': 40116, 'pending_future_quotes': 11886}`
- maturity_status_counts: `{'matured_labeled': 3828, 'matured_no_entry': 10029, 'pending_future_quotes': 3599}`
- pending_future_quote_count: `11886`
- bottom_rebound_processed_arm_count: `2520`
- bottom_rebound_label_status_counts: `{'labeled': 4080, 'expired_entry_no_trigger': 3012, 'pending_future_quotes': 2988}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

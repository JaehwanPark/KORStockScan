# Swing Strategy Discovery Labels - 2026-07-03

- generated_at: `2026-07-03T20:23:47`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `15496`
- arm_status_counts: `{'EXITED': 3043, 'EXPIRED': 8366, 'ENTERED': 2901, 'PENDING_ENTRY': 1186}`
- label_status_counts: `{'labeled': 14596, 'expired_entry_no_trigger': 33464, 'pending_future_quotes': 13924}`
- maturity_status_counts: `{'matured_labeled': 3043, 'matured_no_entry': 8366, 'pending_future_quotes': 4087}`
- pending_future_quote_count: `13924`
- bottom_rebound_processed_arm_count: `1920`
- bottom_rebound_label_status_counts: `{'labeled': 3062, 'expired_entry_no_trigger': 2580, 'pending_future_quotes': 2038}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

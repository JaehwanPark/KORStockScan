# Swing Strategy Discovery Labels - 2026-06-02

- generated_at: `2026-06-02T16:18:20`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `4925`
- arm_status_counts: `{'ENTERED': 1671, 'EXPIRED': 1059, 'EXITED': 232, 'PENDING_ENTRY': 1963}`
- label_status_counts: `{'labeled': 2135, 'pending_future_quotes': 13329, 'expired_entry_no_trigger': 4236}`
- maturity_status_counts: `{'pending_future_quotes': 3634, 'matured_no_entry': 1059, 'matured_labeled': 232}`
- pending_future_quote_count: `13329`
- bottom_rebound_processed_arm_count: `405`
- bottom_rebound_label_status_counts: `{'labeled': 303, 'pending_future_quotes': 1317}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

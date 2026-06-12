# Swing Strategy Discovery Labels - 2026-06-12

- generated_at: `2026-06-12T16:07:47`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `8782`
- arm_status_counts: `{'EXITED': 1004, 'ENTERED': 3063, 'EXPIRED': 3301, 'PENDING_ENTRY': 1414}`
- label_status_counts: `{'labeled': 5929, 'pending_future_quotes': 15995, 'expired_entry_no_trigger': 13204}`
- maturity_status_counts: `{'matured_labeled': 1004, 'pending_future_quotes': 4477, 'matured_no_entry': 3301}`
- pending_future_quote_count: `15995`
- bottom_rebound_processed_arm_count: `1110`
- bottom_rebound_label_status_counts: `{'labeled': 993, 'pending_future_quotes': 3003, 'expired_entry_no_trigger': 444}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

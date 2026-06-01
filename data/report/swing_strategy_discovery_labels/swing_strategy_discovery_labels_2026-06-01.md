# Swing Strategy Discovery Labels - 2026-06-01

- generated_at: `2026-06-01T22:35:58`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `4525`
- arm_status_counts: `{'ENTERED': 1857, 'EXPIRED': 998, 'EXITED': 315, 'PENDING_ENTRY': 1355}`
- label_status_counts: `{'labeled': 2487, 'pending_future_quotes': 11621, 'expired_entry_no_trigger': 3992}`
- maturity_status_counts: `{'pending_future_quotes': 3212, 'matured_no_entry': 998, 'matured_labeled': 315}`
- pending_future_quote_count: `11621`
- bottom_rebound_processed_arm_count: `405`
- bottom_rebound_label_status_counts: `{'labeled': 329, 'pending_future_quotes': 1291}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

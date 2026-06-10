# Swing Strategy Discovery Labels - 2026-06-10

- generated_at: `2026-06-10T16:16:13`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `7640`
- arm_status_counts: `{'EXITED': 819, 'ENTERED': 2759, 'EXPIRED': 2760, 'PENDING_ENTRY': 1302}`
- label_status_counts: `{'labeled': 4869, 'pending_future_quotes': 14651, 'expired_entry_no_trigger': 11040}`
- maturity_status_counts: `{'matured_labeled': 819, 'pending_future_quotes': 4061, 'matured_no_entry': 2760}`
- pending_future_quote_count: `14651`
- bottom_rebound_processed_arm_count: `888`
- bottom_rebound_label_status_counts: `{'labeled': 782, 'pending_future_quotes': 2478, 'expired_entry_no_trigger': 292}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

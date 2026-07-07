# Swing Strategy Discovery Labels - 2026-07-07

- generated_at: `2026-07-07T20:23:45`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `16216`
- arm_status_counts: `{'EXITED': 3317, 'EXPIRED': 8926, 'ENTERED': 2969, 'PENDING_ENTRY': 1004}`
- label_status_counts: `{'labeled': 15993, 'expired_entry_no_trigger': 35704, 'pending_future_quotes': 13167}`
- maturity_status_counts: `{'matured_labeled': 3317, 'matured_no_entry': 8926, 'pending_future_quotes': 3973}`
- pending_future_quote_count: `13167`
- bottom_rebound_processed_arm_count: `2160`
- bottom_rebound_label_status_counts: `{'labeled': 3466, 'expired_entry_no_trigger': 2688, 'pending_future_quotes': 2486}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

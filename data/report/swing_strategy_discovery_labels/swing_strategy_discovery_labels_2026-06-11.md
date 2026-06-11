# Swing Strategy Discovery Labels - 2026-06-11

- generated_at: `2026-06-11T16:06:50`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `8226`
- arm_status_counts: `{'EXITED': 966, 'ENTERED': 2999, 'EXPIRED': 2829, 'PENDING_ENTRY': 1432}`
- label_status_counts: `{'labeled': 5571, 'pending_future_quotes': 16017, 'expired_entry_no_trigger': 11316}`
- maturity_status_counts: `{'matured_labeled': 966, 'pending_future_quotes': 4431, 'matured_no_entry': 2829}`
- pending_future_quote_count: `16017`
- bottom_rebound_processed_arm_count: `1002`
- bottom_rebound_label_status_counts: `{'labeled': 908, 'pending_future_quotes': 2844, 'expired_entry_no_trigger': 256}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

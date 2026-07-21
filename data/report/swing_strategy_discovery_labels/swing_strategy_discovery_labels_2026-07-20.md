# Swing Strategy Discovery Labels - 2026-07-20

- generated_at: `2026-07-20T20:46:44`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `21421`
- arm_status_counts: `{'EXITED': 4354, 'EXPIRED': 11515, 'ENTERED': 3003, 'PENDING_ENTRY': 2549}`
- label_status_counts: `{'labeled': 19943, 'expired_entry_no_trigger': 46060, 'pending_future_quotes': 19681}`
- maturity_status_counts: `{'matured_labeled': 4354, 'matured_no_entry': 11515, 'pending_future_quotes': 5552}`
- pending_future_quote_count: `19681`
- bottom_rebound_processed_arm_count: `2973`
- bottom_rebound_label_status_counts: `{'labeled': 4768, 'expired_entry_no_trigger': 3828, 'pending_future_quotes': 3296}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

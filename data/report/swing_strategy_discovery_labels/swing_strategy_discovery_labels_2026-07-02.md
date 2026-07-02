# Swing Strategy Discovery Labels - 2026-07-02

- generated_at: `2026-07-02T20:21:49`
- label_version: `swing_strategy_discovery_label_v1`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- processed_arm_count: `14923`
- arm_status_counts: `{'EXITED': 2824, 'EXPIRED': 8069, 'ENTERED': 3116, 'PENDING_ENTRY': 914}`
- label_status_counts: `{'labeled': 14055, 'expired_entry_no_trigger': 32276, 'pending_future_quotes': 13361}`
- maturity_status_counts: `{'matured_labeled': 2824, 'matured_no_entry': 8069, 'pending_future_quotes': 4030}`
- pending_future_quote_count: `13361`
- bottom_rebound_processed_arm_count: `1803`
- bottom_rebound_label_status_counts: `{'labeled': 2834, 'expired_entry_no_trigger': 2396, 'pending_future_quotes': 1982}`
- implementation_status: `implemented`

## Contract

- Horizon labels use 1d/5d/10d close basis.
- `policy_exit` uses the arm exit policy final return basis.
- Future-only label fields are never runtime inputs.
- All rows remain sim exploration only.

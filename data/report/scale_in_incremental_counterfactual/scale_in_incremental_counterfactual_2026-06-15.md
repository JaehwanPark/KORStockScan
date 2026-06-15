# Scale-In Incremental Counterfactual - 2026-06-15

## Contract
- ev_label_version: `incremental_counterfactual_v2`
- primary_decision_metric: `incremental_notional_ev_pct`
- decision_authority: `sim_scale_in_counterfactual_only`
- runtime_effect: `False`

## Summary
- counterfactual_event_count: `1`
- complete_row_count: `1`
- incomplete_row_count: `1`
- arm_counts: `{'PYRAMID': 1}`
- execution_arm_counts: `{'LEGACY_PASSIVE': 1}`
- filled_count: `0`
- unfilled_count: `1`
- candidate_funnel_by_arm: `{'AVG_DOWN': {'None': 581, 'eligible': 32, 'price_guard_blocked': 2, 'position_quota_blocked': 198, 'qty_guard_blocked': 29, 'profit_window_blocked': 8, 'daily_quota_blocked': 1}, 'PYRAMID': {'None': 27, 'eligible': 19, 'qty_guard_blocked': 17, 'position_quota_blocked': 86, 'price_guard_blocked': 2, 'profit_window_blocked': 17}, 'UNKNOWN': {'panic_blocked': 12096}}`
- incomplete_reasons: `{'horizon_incomplete_30min': 1, 'horizon_incomplete_60min': 1}`

## Horizon Summary
- `10min`: sample=0, ev=None, win_rate=None
- `30min`: sample=0, ev=None, win_rate=None
- `60min`: sample=0, ev=None, win_rate=None
- `final`: sample=0, ev=None, win_rate=None

## Cohort Summary

### by_arm
- `AVG_DOWN`: sample=0, final_ev=None, final_win_rate=None
- `PYRAMID`: sample=0, final_ev=None, final_win_rate=None
### by_quote_touched
- `filled`: sample=0, final_ev=None, final_win_rate=None
- `unfilled`: sample=1, final_ev=-0.6891, final_win_rate=0.0
### combined
### combined_primary_filled
- `horizons`: sample=None, final_ev=None, final_win_rate=None
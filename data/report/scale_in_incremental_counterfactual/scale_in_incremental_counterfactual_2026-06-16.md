# Scale-In Incremental Counterfactual - 2026-06-16

## Contract
- ev_label_version: `incremental_counterfactual_v2`
- primary_decision_metric: `incremental_notional_ev_pct`
- decision_authority: `sim_scale_in_counterfactual_only`
- runtime_effect: `False`

## Summary
- counterfactual_event_count: `20`
- complete_row_count: `14`
- incomplete_row_count: `20`
- arm_counts: `{'PYRAMID': 14, 'unknown': 6}`
- execution_arm_counts: `{'LEGACY_PASSIVE': 14, 'unknown': 6}`
- filled_count: `0`
- unfilled_count: `20`
- candidate_funnel_by_arm: `{'PYRAMID': {'eligible': 91, 'qty_guard_blocked': 75, 'position_quota_blocked': 1735, 'profit_window_blocked': 139, 'None': 291, 'price_guard_blocked': 10, 'passive_unfilled': 6, 'marketable_filled': 5, 'quote_unavailable': 1, 'daily_quota_blocked': 200}, 'AVG_DOWN': {'eligible': 147, 'qty_guard_blocked': 113, 'position_quota_blocked': 2688, 'price_guard_blocked': 33, 'profit_window_blocked': 42, 'daily_quota_blocked': 4789, 'None': 693}, 'UNKNOWN': {'panic_blocked': 4027}}`
- incomplete_reasons: `{'horizon_incomplete_10min': 14, 'horizon_incomplete_30min': 14, 'horizon_incomplete_60min': 14, 'missing_qty_or_price': 6}`

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
- `unfilled`: sample=14, final_ev=-0.7264, final_win_rate=0.0
### combined
### combined_primary_filled
- `horizons`: sample=None, final_ev=None, final_win_rate=None
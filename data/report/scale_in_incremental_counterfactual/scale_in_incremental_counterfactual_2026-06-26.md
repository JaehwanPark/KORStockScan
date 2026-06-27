# Scale-In Incremental Counterfactual - 2026-06-26

## Contract
- ev_label_version: `incremental_counterfactual_v2`
- primary_decision_metric: `incremental_notional_ev_pct`
- decision_authority: `sim_scale_in_counterfactual_only`
- runtime_effect: `False`

## Summary
- counterfactual_event_count: `27`
- complete_row_count: `1`
- incomplete_row_count: `27`
- arm_counts: `{'AVG_DOWN': 1, 'unknown': 1, 'PYRAMID': 25}`
- execution_arm_counts: `{'LEGACY_PASSIVE': 26, 'unknown': 1}`
- filled_count: `0`
- unfilled_count: `27`
- candidate_funnel_by_arm: `{'AVG_DOWN': {'eligible': 16, 'qty_guard_blocked': 16, 'position_quota_blocked': 298, 'profit_window_blocked': 1}, 'PYRAMID': {'eligible': 14, 'qty_guard_blocked': 8, 'profit_window_blocked': 74, 'None': 149, 'position_quota_blocked': 529, 'price_guard_blocked': 5, 'passive_unfilled': 1, 'quote_unavailable': 1}, 'UNKNOWN': {'panic_blocked': 1667}}`
- incomplete_reasons: `{'horizon_incomplete_30min': 17, 'horizon_incomplete_60min': 17, 'missing_qty_or_price': 1, 'horizon_incomplete_final': 25, 'horizon_incomplete_10min': 9}`

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
- `unfilled`: sample=1, final_ev=-1.2167, final_win_rate=0.0
### combined
### combined_primary_filled
- `horizons`: sample=None, final_ev=None, final_win_rate=None
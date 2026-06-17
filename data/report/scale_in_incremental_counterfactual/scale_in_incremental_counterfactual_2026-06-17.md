# Scale-In Incremental Counterfactual - 2026-06-17

## Contract
- ev_label_version: `incremental_counterfactual_v2`
- primary_decision_metric: `incremental_notional_ev_pct`
- decision_authority: `sim_scale_in_counterfactual_only`
- runtime_effect: `False`

## Summary
- counterfactual_event_count: `22`
- complete_row_count: `19`
- incomplete_row_count: `22`
- arm_counts: `{'PYRAMID': 19, 'unknown': 3}`
- execution_arm_counts: `{'LEGACY_PASSIVE': 19, 'unknown': 3}`
- filled_count: `0`
- unfilled_count: `22`
- candidate_funnel_by_arm: `{'AVG_DOWN': {'eligible': 116, 'qty_guard_blocked': 104, 'position_quota_blocked': 10373, 'profit_window_blocked': 39, 'price_guard_blocked': 12, 'None': 51, 'daily_quota_blocked': 1633}, 'PYRAMID': {'eligible': 79, 'qty_guard_blocked': 65, 'position_quota_blocked': 3693, 'price_guard_blocked': 11, 'None': 416, 'profit_window_blocked': 203, 'passive_unfilled': 3, 'quote_unavailable': 2, 'daily_quota_blocked': 39, 'marketable_filled': 1}, 'UNKNOWN': {'panic_blocked': 145}}`
- incomplete_reasons: `{'horizon_incomplete_10min': 16, 'horizon_incomplete_30min': 19, 'horizon_incomplete_60min': 19, 'missing_qty_or_price': 3}`

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
- `unfilled`: sample=19, final_ev=-0.0688, final_win_rate=0.3158
### combined
### combined_primary_filled
- `horizons`: sample=None, final_ev=None, final_win_rate=None
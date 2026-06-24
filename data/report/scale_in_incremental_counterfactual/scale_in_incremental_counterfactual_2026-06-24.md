# Scale-In Incremental Counterfactual - 2026-06-24

## Contract
- ev_label_version: `incremental_counterfactual_v2`
- primary_decision_metric: `incremental_notional_ev_pct`
- decision_authority: `sim_scale_in_counterfactual_only`
- runtime_effect: `False`

## Summary
- counterfactual_event_count: `3`
- complete_row_count: `3`
- incomplete_row_count: `3`
- arm_counts: `{'PYRAMID': 3}`
- execution_arm_counts: `{'LEGACY_PASSIVE': 3}`
- filled_count: `0`
- unfilled_count: `3`
- candidate_funnel_by_arm: `{'AVG_DOWN': {'eligible': 27, 'qty_guard_blocked': 27, 'position_quota_blocked': 461, 'profit_window_blocked': 153}, 'PYRAMID': {'eligible': 12, 'qty_guard_blocked': 11, 'position_quota_blocked': 154, 'None': 61, 'price_guard_blocked': 1, 'profit_window_blocked': 55}, 'UNKNOWN': {'panic_blocked': 1666}}`
- incomplete_reasons: `{'horizon_incomplete_30min': 3, 'horizon_incomplete_60min': 3}`

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
- `unfilled`: sample=3, final_ev=4.0419, final_win_rate=1.0
### combined
### combined_primary_filled
- `horizons`: sample=None, final_ev=None, final_win_rate=None
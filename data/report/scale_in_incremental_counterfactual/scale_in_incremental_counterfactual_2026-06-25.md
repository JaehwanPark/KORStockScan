# Scale-In Incremental Counterfactual - 2026-06-25

## Contract
- ev_label_version: `incremental_counterfactual_v2`
- primary_decision_metric: `incremental_notional_ev_pct`
- decision_authority: `sim_scale_in_counterfactual_only`
- runtime_effect: `False`

## Summary
- counterfactual_event_count: `4`
- complete_row_count: `0`
- incomplete_row_count: `4`
- arm_counts: `{'AVG_DOWN': 4}`
- execution_arm_counts: `{'LEGACY_PASSIVE': 4}`
- filled_count: `0`
- unfilled_count: `4`
- candidate_funnel_by_arm: `{'PYRAMID': {'profit_window_blocked': 25, 'None': 30, 'eligible': 8, 'qty_guard_blocked': 7, 'position_quota_blocked': 156, 'price_guard_blocked': 1}, 'AVG_DOWN': {'eligible': 24, 'qty_guard_blocked': 18, 'position_quota_blocked': 723, 'profit_window_blocked': 12, 'price_guard_blocked': 5}, 'UNKNOWN': {'panic_blocked': 1341}}`
- incomplete_reasons: `{'horizon_incomplete_10min': 4, 'horizon_incomplete_30min': 4, 'horizon_incomplete_60min': 4, 'horizon_incomplete_final': 4}`

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
- `unfilled`: sample=0, final_ev=None, final_win_rate=None
### combined
### combined_primary_filled
- `horizons`: sample=None, final_ev=None, final_win_rate=None
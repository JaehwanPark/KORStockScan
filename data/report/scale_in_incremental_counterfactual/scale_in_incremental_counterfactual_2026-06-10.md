# Scale-In Incremental Counterfactual - 2026-06-10

## Contract
- ev_label_version: `incremental_counterfactual_v2`
- primary_decision_metric: `incremental_notional_ev_pct`
- decision_authority: `sim_scale_in_counterfactual_only`
- runtime_effect: `False`

## Summary
- counterfactual_event_count: `6`
- complete_row_count: `0`
- incomplete_row_count: `6`
- arm_counts: `{'PYRAMID': 6}`
- filled_count: `0`
- unfilled_count: `6`
- incomplete_reasons: `{'horizon_incomplete_30min': 5, 'horizon_incomplete_60min': 6, 'horizon_incomplete_10min': 3}`

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
- `horizons`: sample=None, final_ev=None, final_win_rate=None
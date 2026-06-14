# Scale-In Incremental Counterfactual - 2026-06-12

## Contract
- ev_label_version: `incremental_counterfactual_v2`
- primary_decision_metric: `incremental_notional_ev_pct`
- decision_authority: `sim_scale_in_counterfactual_only`
- runtime_effect: `False`

## Summary
- counterfactual_event_count: `10`
- complete_row_count: `4`
- incomplete_row_count: `10`
- arm_counts: `{'PYRAMID': 10}`
- filled_count: `0`
- unfilled_count: `10`
- incomplete_reasons: `{'horizon_incomplete_10min': 7, 'horizon_incomplete_30min': 10, 'horizon_incomplete_60min': 10, 'horizon_incomplete_final': 6}`

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
- `unfilled`: sample=4, final_ev=-0.0031, final_win_rate=0.5
### combined
### combined_primary_filled
- `horizons`: sample=None, final_ev=None, final_win_rate=None
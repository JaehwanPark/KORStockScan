# Scale-In Incremental Counterfactual - 2026-06-29

## Contract
- ev_label_version: `incremental_counterfactual_v2`
- primary_decision_metric: `incremental_notional_ev_pct`
- decision_authority: `sim_scale_in_counterfactual_only`
- runtime_effect: `False`

## Summary
- counterfactual_event_count: `2`
- complete_row_count: `0`
- incomplete_row_count: `2`
- arm_counts: `{'unknown': 2}`
- execution_arm_counts: `{'unknown': 2}`
- filled_count: `0`
- unfilled_count: `2`
- candidate_funnel_by_arm: `{'AVG_DOWN': {'eligible': 22, 'qty_guard_blocked': 20, 'position_quota_blocked': 1209, 'profit_window_blocked': 41, 'price_guard_blocked': 2}, 'PYRAMID': {'eligible': 11, 'qty_guard_blocked': 6, 'position_quota_blocked': 151, 'price_guard_blocked': 3, 'profit_window_blocked': 2, 'None': 9, 'passive_unfilled': 2, 'quote_unavailable': 2}, 'UNKNOWN': {'panic_blocked': 2018}}`
- incomplete_reasons: `{'missing_qty_or_price': 2}`

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
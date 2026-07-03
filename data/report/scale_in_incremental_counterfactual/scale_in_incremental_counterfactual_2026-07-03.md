# Scale-In Incremental Counterfactual - 2026-07-03

## Contract
- ev_label_version: `incremental_counterfactual_v2`
- primary_decision_metric: `incremental_notional_ev_pct`
- decision_authority: `sim_scale_in_counterfactual_only`
- runtime_effect: `False`

## Summary
- counterfactual_event_count: `1`
- complete_row_count: `0`
- incomplete_row_count: `1`
- arm_counts: `{'unknown': 1}`
- execution_arm_counts: `{'unknown': 1}`
- filled_count: `0`
- unfilled_count: `1`
- candidate_funnel_by_arm: `{'PYRAMID': {'eligible': 8, 'qty_guard_blocked': 6, 'position_quota_blocked': 22, 'price_guard_blocked': 1, 'passive_unfilled': 1, 'marketable_filled': 1}, 'AVG_DOWN': {'eligible': 20, 'qty_guard_blocked': 16, 'price_guard_blocked': 4, 'position_quota_blocked': 746, 'profit_window_blocked': 20, 'None': 1}, 'UNKNOWN': {'panic_blocked': 1234}}`
- incomplete_reasons: `{'missing_qty_or_price': 1}`

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
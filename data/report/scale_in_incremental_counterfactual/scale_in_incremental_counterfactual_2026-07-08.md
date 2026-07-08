# Scale-In Incremental Counterfactual - 2026-07-08

## Contract
- ev_label_version: `incremental_counterfactual_v2`
- primary_decision_metric: `incremental_notional_ev_pct`
- decision_authority: `sim_scale_in_counterfactual_only`
- runtime_effect: `False`

## Summary
- counterfactual_event_count: `7`
- complete_row_count: `3`
- incomplete_row_count: `7`
- arm_counts: `{'unknown': 3, 'PYRAMID': 4}`
- execution_arm_counts: `{'unknown': 3, 'LEGACY_PASSIVE': 4}`
- filled_count: `0`
- unfilled_count: `7`
- candidate_funnel_by_arm: `{'AVG_DOWN': {'eligible': 33, 'qty_guard_blocked': 28, 'position_quota_blocked': 589, 'profit_window_blocked': 59, 'price_guard_blocked': 5, 'None': 1}, 'PYRAMID': {'eligible': 12, 'qty_guard_blocked': 9, 'position_quota_blocked': 82, 'passive_unfilled': 2, 'quote_unavailable': 1, 'marketable_filled': 1, 'price_guard_blocked': 1, 'None': 1}, 'UNKNOWN': {'panic_blocked': 842}}`
- incomplete_reasons: `{'missing_qty_or_price': 3, 'horizon_incomplete_60min': 4, 'horizon_incomplete_10min': 1, 'horizon_incomplete_30min': 1, 'horizon_incomplete_final': 1}`

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
- `unfilled`: sample=3, final_ev=-5.1791, final_win_rate=0.0
### combined
### combined_primary_filled
- `horizons`: sample=None, final_ev=None, final_win_rate=None
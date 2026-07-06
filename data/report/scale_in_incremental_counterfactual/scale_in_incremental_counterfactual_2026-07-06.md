# Scale-In Incremental Counterfactual - 2026-07-06

## Contract
- ev_label_version: `incremental_counterfactual_v2`
- primary_decision_metric: `incremental_notional_ev_pct`
- decision_authority: `sim_scale_in_counterfactual_only`
- runtime_effect: `False`

## Summary
- counterfactual_event_count: `6`
- complete_row_count: `4`
- incomplete_row_count: `6`
- arm_counts: `{'unknown': 1, 'PYRAMID': 5}`
- execution_arm_counts: `{'unknown': 1, 'LEGACY_PASSIVE': 5}`
- filled_count: `0`
- unfilled_count: `6`
- candidate_funnel_by_arm: `{'AVG_DOWN': {'eligible': 14, 'qty_guard_blocked': 13, 'position_quota_blocked': 534, 'profit_window_blocked': 28, 'price_guard_blocked': 1}, 'PYRAMID': {'eligible': 8, 'qty_guard_blocked': 7, 'position_quota_blocked': 118, 'passive_unfilled': 1, 'marketable_filled': 1, 'None': 2}, 'UNKNOWN': {'panic_blocked': 370}}`
- incomplete_reasons: `{'missing_qty_or_price': 1, 'horizon_incomplete_10min': 5, 'horizon_incomplete_30min': 5, 'horizon_incomplete_60min': 5, 'horizon_incomplete_final': 1}`

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
- `unfilled`: sample=4, final_ev=-0.19, final_win_rate=0.5
### combined
### combined_primary_filled
- `horizons`: sample=None, final_ev=None, final_win_rate=None
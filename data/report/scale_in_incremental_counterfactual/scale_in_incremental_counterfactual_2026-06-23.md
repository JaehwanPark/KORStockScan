# Scale-In Incremental Counterfactual - 2026-06-23

## Contract
- ev_label_version: `incremental_counterfactual_v2`
- primary_decision_metric: `incremental_notional_ev_pct`
- decision_authority: `sim_scale_in_counterfactual_only`
- runtime_effect: `False`

## Summary
- counterfactual_event_count: `5`
- complete_row_count: `0`
- incomplete_row_count: `5`
- arm_counts: `{'unknown': 1, 'PYRAMID': 4}`
- execution_arm_counts: `{'unknown': 1, 'LEGACY_PASSIVE': 4}`
- filled_count: `0`
- unfilled_count: `5`
- candidate_funnel_by_arm: `{'AVG_DOWN': {'eligible': 21, 'price_guard_blocked': 5, 'position_quota_blocked': 693, 'qty_guard_blocked': 16, 'profit_window_blocked': 59, 'None': 3}, 'PYRAMID': {'profit_window_blocked': 11, 'None': 29, 'eligible': 13, 'qty_guard_blocked': 11, 'position_quota_blocked': 197, 'passive_unfilled': 1, 'marketable_filled': 1, 'price_guard_blocked': 1}, 'UNKNOWN': {'panic_blocked': 1755}}`
- incomplete_reasons: `{'missing_qty_or_price': 1, 'horizon_incomplete_10min': 4, 'horizon_incomplete_30min': 4, 'horizon_incomplete_60min': 4, 'horizon_incomplete_final': 4}`

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
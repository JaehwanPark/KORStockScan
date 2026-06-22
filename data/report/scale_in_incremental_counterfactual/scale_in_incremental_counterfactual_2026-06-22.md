# Scale-In Incremental Counterfactual - 2026-06-22

## Contract
- ev_label_version: `incremental_counterfactual_v2`
- primary_decision_metric: `incremental_notional_ev_pct`
- decision_authority: `sim_scale_in_counterfactual_only`
- runtime_effect: `False`

## Summary
- counterfactual_event_count: `8`
- complete_row_count: `4`
- incomplete_row_count: `8`
- arm_counts: `{'unknown': 2, 'PYRAMID': 6}`
- execution_arm_counts: `{'unknown': 2, 'LEGACY_PASSIVE': 6}`
- filled_count: `0`
- unfilled_count: `8`
- candidate_funnel_by_arm: `{'AVG_DOWN': {'eligible': 52, 'qty_guard_blocked': 39, 'position_quota_blocked': 432, 'profit_window_blocked': 20, 'price_guard_blocked': 12}, 'PYRAMID': {'eligible': 31, 'price_guard_blocked': 7, 'passive_unfilled': 2, 'marketable_filled': 2, 'profit_window_blocked': 63, 'None': 124, 'qty_guard_blocked': 22, 'position_quota_blocked': 203}, 'UNKNOWN': {'panic_blocked': 871}}`
- incomplete_reasons: `{'missing_qty_or_price': 2, 'horizon_incomplete_10min': 3, 'horizon_incomplete_30min': 4, 'horizon_incomplete_60min': 6, 'horizon_incomplete_final': 2}`

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
- `unfilled`: sample=4, final_ev=-2.2757, final_win_rate=0.0
### combined
### combined_primary_filled
- `horizons`: sample=None, final_ev=None, final_win_rate=None
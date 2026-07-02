# Scale-In Incremental Counterfactual - 2026-07-02

## Contract
- ev_label_version: `incremental_counterfactual_v2`
- primary_decision_metric: `incremental_notional_ev_pct`
- decision_authority: `sim_scale_in_counterfactual_only`
- runtime_effect: `False`

## Summary
- counterfactual_event_count: `8`
- complete_row_count: `7`
- incomplete_row_count: `8`
- arm_counts: `{'unknown': 1, 'PYRAMID': 7}`
- execution_arm_counts: `{'unknown': 1, 'LEGACY_PASSIVE': 7}`
- filled_count: `0`
- unfilled_count: `8`
- candidate_funnel_by_arm: `{'AVG_DOWN': {'None': 7, 'position_quota_blocked': 1109, 'eligible': 21, 'qty_guard_blocked': 16, 'profit_window_blocked': 22, 'price_guard_blocked': 5}, 'PYRAMID': {'None': 25, 'eligible': 8, 'qty_guard_blocked': 6, 'position_quota_blocked': 181, 'price_guard_blocked': 1, 'passive_unfilled': 1, 'marketable_filled': 1}, 'UNKNOWN': {'panic_blocked': 1027}}`
- incomplete_reasons: `{'missing_qty_or_price': 1, 'horizon_incomplete_10min': 7, 'horizon_incomplete_30min': 7, 'horizon_incomplete_60min': 7}`

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
- `unfilled`: sample=7, final_ev=-0.667, final_win_rate=0.0
### combined
### combined_primary_filled
- `horizons`: sample=None, final_ev=None, final_win_rate=None
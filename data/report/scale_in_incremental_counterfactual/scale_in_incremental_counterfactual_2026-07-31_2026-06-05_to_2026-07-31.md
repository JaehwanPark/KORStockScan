# Scale-In Incremental Counterfactual - 2026-07-31

## Contract
- ev_label_version: `incremental_counterfactual_v2`
- primary_decision_metric: `incremental_notional_ev_pct`
- decision_authority: `sim_scale_in_counterfactual_only`
- runtime_effect: `False`

## Summary
- status: `evaluated`
- window_policy: `2026-06-05_to_2026-07-31`
- counterfactual_event_count: `134`
- complete_row_count: `66`
- incomplete_row_count: `134`
- arm_counts: `{'PYRAMID': 104, 'unknown': 25, 'AVG_DOWN': 5}`
- execution_arm_counts: `{'LEGACY_PASSIVE': 109, 'unknown': 25}`
- filled_count: `0`
- unfilled_count: `134`
- candidate_funnel_by_arm: `{'UNKNOWN': {'panic_blocked': 112446}, 'AVG_DOWN': {'None': 1459, 'eligible': 683, 'price_guard_blocked': 108, 'position_quota_blocked': 24474, 'qty_guard_blocked': 569, 'profit_window_blocked': 816, 'daily_quota_blocked': 6423}, 'PYRAMID': {'None': 1716, 'eligible': 367, 'qty_guard_blocked': 291, 'position_quota_blocked': 7926, 'price_guard_blocked': 52, 'profit_window_blocked': 599, 'passive_unfilled': 24, 'marketable_filled': 15, 'quote_unavailable': 9, 'daily_quota_blocked': 239}}`
- source_status_counts: `{'no_natural_sample': 22, 'evaluated': 18}`
- eligible_candidate_count: `1050`
- guard_blocked_before_execution_count: `1020`
- unresolved_eligible_candidate_count: `0`
- no_sample_reason: `None`
- incomplete_reasons: `{'horizon_incomplete_30min': 94, 'horizon_incomplete_60min': 100, 'horizon_incomplete_10min': 73, 'horizon_incomplete_final': 43, 'missing_qty_or_price': 25}`

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
- `unfilled`: sample=66, final_ev=-0.6239, final_win_rate=0.2121
### combined
### combined_primary_filled
- `horizons`: sample=None, final_ev=None, final_win_rate=None
# Scale-In Incremental Counterfactual - 2026-08-31

## Contract
- ev_label_version: `incremental_counterfactual_v2`
- primary_decision_metric: `incremental_notional_ev_pct`
- decision_authority: `sim_scale_in_counterfactual_only`
- runtime_effect: `False`

## Summary
- status: `evaluated`
- window_policy: `daily_only`
- counterfactual_event_count: `1`
- complete_row_count: `0`
- incomplete_row_count: `1`
- arm_counts: `{'unknown': 1}`
- execution_arm_counts: `{'unknown': 1}`
- filled_count: `0`
- unfilled_count: `1`
- candidate_funnel_by_arm: `{'UNKNOWN': {'panic_blocked': 555}, 'PYRAMID': {'eligible': 4, 'qty_guard_blocked': 2, 'position_quota_blocked': 27, 'profit_window_blocked': 3, 'passive_unfilled': 1, 'marketable_filled': 1, 'price_guard_blocked': 1, 'execution_closed_without_result': 1}, 'AVG_DOWN': {'eligible': 4, 'qty_guard_blocked': 4, 'position_quota_blocked': 188, 'profit_window_blocked': 5}}`
- source_status_counts: `None`
- eligible_candidate_count: `8`
- guard_blocked_before_execution_count: `7`
- unresolved_eligible_candidate_count: `0`
- no_sample_reason: `None`
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
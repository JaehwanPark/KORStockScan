# Scale-In Incremental Counterfactual - 2026-07-31

## Contract
- ev_label_version: `incremental_counterfactual_v2`
- primary_decision_metric: `incremental_notional_ev_pct`
- decision_authority: `sim_scale_in_counterfactual_only`
- runtime_effect: `False`

## Summary
- status: `no_natural_sample`
- window_policy: `2026-07-20_to_2026-07-31`
- counterfactual_event_count: `0`
- complete_row_count: `0`
- incomplete_row_count: `0`
- arm_counts: `{}`
- execution_arm_counts: `{}`
- filled_count: `0`
- unfilled_count: `0`
- candidate_funnel_by_arm: `{'AVG_DOWN': {'eligible': 7, 'position_quota_blocked': 396, 'qty_guard_blocked': 5, 'profit_window_blocked': 3, 'price_guard_blocked': 1}, 'UNKNOWN': {'panic_blocked': 799}, 'PYRAMID': {'None': 8, 'eligible': 5, 'qty_guard_blocked': 3, 'position_quota_blocked': 57, 'price_guard_blocked': 2}}`
- source_status_counts: `{'no_natural_sample': 10}`
- eligible_candidate_count: `12`
- guard_blocked_before_execution_count: `11`
- unresolved_eligible_candidate_count: `0`
- no_sample_reason: `None`
- incomplete_reasons: `{}`

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
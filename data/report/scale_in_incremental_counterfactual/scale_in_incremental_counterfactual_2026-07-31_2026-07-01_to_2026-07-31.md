# Scale-In Incremental Counterfactual - 2026-07-31

## Contract
- ev_label_version: `incremental_counterfactual_v2`
- primary_decision_metric: `incremental_notional_ev_pct`
- decision_authority: `sim_scale_in_counterfactual_only`
- runtime_effect: `False`

## Summary
- status: `evaluated`
- window_policy: `2026-07-01_to_2026-07-31`
- counterfactual_event_count: `26`
- complete_row_count: `14`
- incomplete_row_count: `26`
- arm_counts: `{'unknown': 10, 'PYRAMID': 16}`
- execution_arm_counts: `{'unknown': 10, 'LEGACY_PASSIVE': 16}`
- filled_count: `0`
- unfilled_count: `26`
- candidate_funnel_by_arm: `{'PYRAMID': {'None': 296, 'eligible': 72, 'qty_guard_blocked': 55, 'position_quota_blocked': 863, 'passive_unfilled': 9, 'marketable_filled': 6, 'quote_unavailable': 3, 'price_guard_blocked': 8, 'profit_window_blocked': 4}, 'AVG_DOWN': {'eligible': 177, 'qty_guard_blocked': 154, 'position_quota_blocked': 6633, 'profit_window_blocked': 212, 'price_guard_blocked': 22, 'None': 10}, 'UNKNOWN': {'panic_blocked': 8539}}`
- source_status_counts: `{'evaluated': 7, 'no_natural_sample': 15}`
- eligible_candidate_count: `249`
- guard_blocked_before_execution_count: `239`
- unresolved_eligible_candidate_count: `0`
- no_sample_reason: `None`
- incomplete_reasons: `{'missing_qty_or_price': 10, 'horizon_incomplete_10min': 13, 'horizon_incomplete_30min': 13, 'horizon_incomplete_60min': 16, 'horizon_incomplete_final': 2}`

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
- `unfilled`: sample=14, final_ev=-1.4976, final_win_rate=0.1429
### combined
### combined_primary_filled
- `horizons`: sample=None, final_ev=None, final_win_rate=None
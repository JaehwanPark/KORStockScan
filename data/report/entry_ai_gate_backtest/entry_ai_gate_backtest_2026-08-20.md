# Entry AI Gate Backtest - 2026-08-20

- calibration_state: `source_contract_not_evaluable`
- allowed_runtime_apply: `False`
- bounded_calibration_candidate_count: `0`
- diagnostic_conflict_detected: `True`
- runtime_update_mode: `single_cumulative_quality_update`
- runtime_apply_candidate_count: `0`
- allowed_runtime_apply_count: `0`
- effective_source_date_count: `33`
- artifact_excluded_date_count: `19`
- source_quality_excluded_date_count: `1`
- source_quality_excluded_dates: `[{"artifact": "/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-06-19.json", "blocked_reason": "blocked_contract_gap", "hard_blocking_contract_gap_count": 3, "load_error": null, "source_date": "2026-06-19", "source_quality_gate": "blocked_contract_gap", "status": "fail"}]`
- counterfactual_context_joined_count: `16479`
- supported_wait_recovery_source_contract_status: `source_contract_not_evaluable`
- supported_wait_recovery_policy_eligible_rows(realized/counterfactual): `0/0`
- supported_wait_recovery_missing_reason_counts: `{"counterfactual": {"canonical_action_missing": 629, "decision_quality_contract_status_missing": 9211, "edge_state_missing": 9265, "entry_probe_intent_missing": 16522, "entry_probe_intent_status_missing": 9193, "micro_vwap_provenance_missing": 4019, "recovery_trigger_missing": 17038, "score_outside_supported_wait_band": 12801, "source_quality_blocked": 17030, "tick_pressure_provenance_missing": 3714}, "realized": {"decision_quality_contract_status_missing": 237, "edge_state_missing": 237, "entry_probe_intent_missing": 237, "entry_probe_intent_status_missing": 237, "micro_vwap_provenance_missing": 120, "recovery_trigger_missing": 247, "score_outside_supported_wait_band": 154, "tick_pressure_provenance_missing": 119}}`
- realized_joined_rows: `247`
- counterfactual_rows: `17108`
- best_policy: `strict_buy`
- best_threshold: `55`
- best_realized_source_quality_adjusted_ev_pct: `-1.365`
- best_counterfactual_close_10m_pct: `0.0`
- best_apply_policy: `None`
- best_apply_threshold: `None`
- best_diagnostic_score_only_threshold: `63`
- best_diagnostic_score_only_realized_source_quality_adjusted_ev_pct: `0.166031`
- best_diagnostic_score_only_counterfactual_close_10m_pct: `-0.201235`
- best_positive_realized_diagnostic_threshold: `63`
- best_positive_realized_diagnostic_ev_pct: `0.166031`
- best_positive_realized_diagnostic_sample_floor_passed: `True`

## Best Candidate

```json
{
  "policy": "strict_buy",
  "threshold": 55,
  "realized": {
    "sample": 2,
    "diagnostic_win_rate": 50.0,
    "equal_weight_avg_profit_pct": -1.365,
    "notional_weighted_ev_pct": -1.365,
    "source_quality_adjusted_ev_pct": -1.365,
    "simple_sum_profit_pct": -2.73
  },
  "counterfactual": {
    "sample": 0,
    "diagnostic_win_rate": 0.0,
    "equal_weight_avg_profit_pct": 0.0,
    "notional_weighted_ev_pct": 0.0,
    "source_quality_adjusted_ev_pct": 0.0,
    "simple_sum_profit_pct": 0.0,
    "missed_upside_close_10m_pct": 0.0,
    "mfe_10m_pct": 0.0,
    "mae_10m_pct": 0.0
  },
  "sample_floor_passed": false,
  "primary_ev_positive": false,
  "counterfactual_opportunity_positive": false,
  "calibration_state": "hold_sample",
  "allowed_runtime_apply": false,
  "apply_block_reason": "hold_sample",
  "runtime_effect": false,
  "actual_order_submitted": false,
  "broker_order_forbidden": true,
  "forbidden_uses": [
    "score_only_buy",
    "intraday_threshold_mutation",
    "provider_route_change",
    "bot_restart",
    "broker_guard_bypass",
    "stale_quote_submit_bypass",
    "quantity_or_cap_change",
    "entry_price_reprice"
  ]
}
```

## Bounded Calibration Candidates

```json
[]
```

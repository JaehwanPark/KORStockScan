# Entry AI Gate Backtest - 2026-07-31

- calibration_state: `source_contract_not_evaluable`
- allowed_runtime_apply: `False`
- bounded_calibration_candidate_count: `0`
- diagnostic_conflict_detected: `True`
- runtime_update_mode: `single_cumulative_quality_update`
- runtime_apply_candidate_count: `0`
- allowed_runtime_apply_count: `0`
- effective_source_date_count: `38`
- artifact_excluded_date_count: `1`
- source_quality_excluded_date_count: `1`
- source_quality_excluded_dates: `[{"artifact": "/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-06-19.json", "blocked_reason": "blocked_contract_gap", "hard_blocking_contract_gap_count": 3, "load_error": null, "source_date": "2026-06-19", "source_quality_gate": "blocked_contract_gap", "status": "fail"}]`
- counterfactual_context_joined_count: `5709`
- supported_wait_recovery_source_contract_status: `source_contract_not_evaluable`
- supported_wait_recovery_policy_eligible_rows(realized/counterfactual): `0/0`
- supported_wait_recovery_missing_reason_counts: `{"counterfactual": {"canonical_action_missing": 515, "decision_quality_contract_status_missing": 6224, "edge_state_missing": 6224, "entry_probe_intent_missing": 6224, "entry_probe_intent_status_missing": 6224, "micro_vwap_provenance_missing": 3710, "recovery_trigger_missing": 6224, "score_outside_supported_wait_band": 3447, "source_quality_blocked": 6210, "tick_pressure_provenance_missing": 3597}, "realized": {"decision_quality_contract_status_missing": 292, "edge_state_missing": 292, "entry_probe_intent_missing": 292, "entry_probe_intent_status_missing": 292, "micro_vwap_provenance_missing": 205, "recovery_trigger_missing": 292, "score_outside_supported_wait_band": 144, "tick_pressure_provenance_missing": 204}}`
- realized_joined_rows: `292`
- counterfactual_rows: `6224`
- best_policy: `strict_buy`
- best_threshold: `55`
- best_realized_source_quality_adjusted_ev_pct: `-0.151429`
- best_counterfactual_close_10m_pct: `0.0`
- best_apply_policy: `None`
- best_apply_threshold: `None`
- best_diagnostic_score_only_threshold: `69`
- best_diagnostic_score_only_realized_source_quality_adjusted_ev_pct: `0.106104`
- best_diagnostic_score_only_counterfactual_close_10m_pct: `-0.277414`
- best_positive_realized_diagnostic_threshold: `69`
- best_positive_realized_diagnostic_ev_pct: `0.106104`
- best_positive_realized_diagnostic_sample_floor_passed: `True`

## Best Candidate

```json
{
  "actual_order_submitted": false,
  "allowed_runtime_apply": false,
  "apply_block_reason": "hold_sample",
  "broker_order_forbidden": true,
  "calibration_state": "hold_sample",
  "counterfactual": {
    "diagnostic_win_rate": 0.0,
    "equal_weight_avg_profit_pct": 0.0,
    "mae_10m_pct": 0.0,
    "mfe_10m_pct": 0.0,
    "missed_upside_close_10m_pct": 0.0,
    "notional_weighted_ev_pct": 0.0,
    "sample": 0,
    "simple_sum_profit_pct": 0.0,
    "source_quality_adjusted_ev_pct": 0.0
  },
  "counterfactual_opportunity_positive": false,
  "forbidden_uses": [
    "score_only_buy",
    "intraday_threshold_mutation",
    "provider_route_change",
    "bot_restart",
    "broker_guard_bypass",
    "stale_quote_submit_bypass",
    "quantity_or_cap_change",
    "entry_price_reprice"
  ],
  "policy": "strict_buy",
  "primary_ev_positive": false,
  "realized": {
    "diagnostic_win_rate": 57.14,
    "equal_weight_avg_profit_pct": -0.151429,
    "notional_weighted_ev_pct": -0.151429,
    "sample": 7,
    "simple_sum_profit_pct": -1.06,
    "source_quality_adjusted_ev_pct": -0.151429
  },
  "runtime_effect": false,
  "sample_floor_passed": false,
  "threshold": 55
}
```

## Bounded Calibration Candidates

```json
[]
```

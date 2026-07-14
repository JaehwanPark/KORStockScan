# Entry AI Gate Backtest - 2026-07-14

- calibration_state: `hold_sample`
- allowed_runtime_apply: `False`
- realized_joined_rows: `215`
- counterfactual_rows: `4082`
- best_policy: `strict_buy`
- best_threshold: `55`
- best_realized_source_quality_adjusted_ev_pct: `-0.248333`
- best_counterfactual_close_10m_pct: `0.0`
- best_apply_policy: `None`
- best_apply_threshold: `None`
- best_diagnostic_score_only_threshold: `69`
- best_diagnostic_score_only_realized_source_quality_adjusted_ev_pct: `0.176029`
- best_diagnostic_score_only_counterfactual_close_10m_pct: `-0.18241`
- best_positive_realized_diagnostic_threshold: `69`
- best_positive_realized_diagnostic_ev_pct: `0.176029`
- best_positive_realized_diagnostic_sample_floor_passed: `True`

## Best Candidate

```json
{
  "policy": "strict_buy",
  "threshold": 55,
  "realized": {
    "sample": 6,
    "diagnostic_win_rate": 50.0,
    "equal_weight_avg_profit_pct": -0.248333,
    "notional_weighted_ev_pct": -0.248333,
    "source_quality_adjusted_ev_pct": -0.248333,
    "simple_sum_profit_pct": -1.49
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

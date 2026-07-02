# Panic Buying 2026-07-02

## 판정

- panic_buy_state: `NORMAL`
- panic_buy_regime_mode: `NORMAL`
- risk_regime_gate_state: `normal`
- risk_regime_threshold_mode: `dynamic_quantile`
- report_only: `true`
- runtime_effect: `report_only_no_mutation`
- as_of: `2026-07-02T13:39:03`
- latest_event_at: `2026-07-02T13:39:02`
- reasons: `no panic buying threshold breached`

## 패닉바잉 지표

- evaluated_symbol_count: `398`
- panic_buy_active_count: `0`
- panic_buy_watch_count: `0`
- allow_tp_override_count: `0`
- allow_runner_count: `0`
- max_panic_buy_score: `0.4299`
- avg_confidence: `0.5577`

## 소진 지표

- exhaustion_candidate_count: `0`
- exhaustion_confirmed_count: `0`
- force_exit_runner_count: `0`
- max_exhaustion_score: `0.505`

## TP Counterfactual

- tp_like_exit_count: `0`
- real_exit_count: `0`
- non_real_exit_count: `1946`
- unproven_exit_count: `0`
- trailing_winner_count: `0`
- candidate_context_count: `0`
- avg_tp_profit_rate_pct: `-`
- runtime_effect: `counterfactual_only_no_order_change`

## Microstructure Detector

- input_universe: `entry_observation_only`
- input_event_count: `57337`
- excluded_holding_row_count: `19596`
- excluded_exit_sell_row_count: `1946`
- missing_orderbook_count: `232`
- degraded_orderbook_count: `232`
- missing_trade_aggressor_count: `151`
- carried_orderbook_snapshot_count: `3111`
- carried_trade_aggressor_snapshot_count: `7113`
- micro_cusum_triggered_symbol_count: `1`
- micro_consensus_pass_symbol_count: `0`
- micro_cusum_decision_authority: `source_quality_only`

## Market Breadth Context

- market_panic_breadth_source_quality_status: `ok`
- market_panic_breadth_risk_on_advisory: `false`
- market_panic_breadth_risk_off_advisory: `true`
- market_panic_breadth_single_market_risk_on_advisory: `false`
- market_panic_breadth_single_market_risk_off_advisory: `false`
- market_wide_panic_buy_confirmed: `false`
- market_panic_buy_interpretation: `normal`
- market_breadth_decision_authority: `source_quality_only`

## Canary Candidates

- `panic_buy_runner_tp_canary`: `hold_until_confirmed_panic_buy_with_tp_context`, allowed_runtime_apply=`false`

## 금지된 자동변경

- `live_threshold_runtime_mutation`
- `take_profit_policy_change`
- `trailing_policy_change`
- `auto_sell`
- `auto_buy`
- `bot_restart`
- `provider_route_change`

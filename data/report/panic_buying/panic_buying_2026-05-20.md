# Panic Buying 2026-05-20

## 판정

- panic_buy_state: `NORMAL`
- panic_buy_regime_mode: `NORMAL`
- report_only: `true`
- runtime_effect: `report_only_no_mutation`
- as_of: `2026-05-20T11:49:04`
- latest_event_at: `2026-05-20T11:49:03`
- reasons: `no panic buying threshold breached`

## 패닉바잉 지표

- evaluated_symbol_count: `63`
- panic_buy_active_count: `0`
- panic_buy_watch_count: `0`
- allow_tp_override_count: `0`
- allow_runner_count: `0`
- max_panic_buy_score: `0.3762`
- avg_confidence: `0.8127`

## 소진 지표

- exhaustion_candidate_count: `0`
- exhaustion_confirmed_count: `0`
- force_exit_runner_count: `0`
- max_exhaustion_score: `0.545`

## TP Counterfactual

- tp_like_exit_count: `15`
- trailing_winner_count: `14`
- candidate_context_count: `29`
- avg_tp_profit_rate_pct: `-1.3287`
- runtime_effect: `counterfactual_only_no_order_change`

## Microstructure Detector

- missing_orderbook_count: `10`
- degraded_orderbook_count: `10`
- missing_trade_aggressor_count: `10`
- carried_orderbook_snapshot_count: `3746`
- carried_trade_aggressor_snapshot_count: `2129`
- micro_cusum_triggered_symbol_count: `4`
- micro_consensus_pass_symbol_count: `1`
- micro_cusum_decision_authority: `source_quality_only`

## Market Breadth Context

- market_panic_breadth_source_quality_status: `ok`
- market_panic_breadth_risk_on_advisory: `false`
- market_panic_breadth_risk_off_advisory: `true`
- market_panic_breadth_single_market_risk_on_advisory: `false`
- market_panic_breadth_single_market_risk_off_advisory: `false`
- market_wide_panic_buy_confirmed: `false`
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

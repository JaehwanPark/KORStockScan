# Panic Sell Defense 2026-05-19

## 판정

- panic_state: `RECOVERY_WATCH`
- panic_regime_mode: `STABILIZING`
- report_only: `true`
- runtime_effect: `report_only_no_mutation`
- as_of: `2026-05-19T16:12:23`
- latest_event_at: `2026-05-19T16:12:23`
- reasons: `live market panic breadth risk_off advisory; market breadth risk-off watch without panic confirmation`

## 패닉 지표

- real_exit_count: `0`
- non_real_exit_count: `115`
- stop_loss_exit_count: `0`
- current_30m_stop_loss_exit_count: `0`
- max_rolling_30m_stop_loss_exit_count: `0`
- stop_loss_exit_ratio_pct: `0`
- avg_exit_profit_rate_pct: `-`
- confirmation_eligible_exit_count: `0`
- never_delay_exit_count: `0`

## 회복 지표

- active_positions: `9`
- active_profit_sample: `9`
- active_avg_unrealized_profit_rate_pct: `-0.2903`
- active_win_rate_pct: `33.3`
- sim_probe_provenance_passed: `true`
- post_sell_rebound_above_sell_10_20m_pct: `0`
- post_sell_rebound_above_buy_10_20m_pct: `0`

## Microstructure Detector

- evaluated_symbol_count: `74`
- risk_off_advisory_count: `0`
- allow_new_long_false_count: `0`
- panic_signal_count: `0`
- recovery_candidate_count: `0`
- recovery_confirmed_count: `0`
- missing_orderbook_count: `62`
- degraded_orderbook_count: `62`
- max_panic_score: `0.3436`
- max_recovery_score: `0.4793`
- micro_cusum_triggered_symbol_count: `0`
- micro_consensus_pass_symbol_count: `0`
- micro_cusum_decision_authority: `source_quality_only`

## Microstructure Market Context

- market_risk_state: `NEUTRAL`
- market_panic_breadth_as_of: `2026-05-19T16:12:16`
- market_panic_breadth_source_quality_status: `ok`
- market_panic_breadth_risk_off_advisory: `true`
- market_panic_breadth_single_market_risk_off_advisory: `false`
- evaluated_symbol_count: `74`
- risk_off_advisory_ratio_pct: `0`
- confirmed_micro_risk_off_advisory: `false`
- confirmed_risk_off_advisory: `true`
- portfolio_local_risk_off_only: `false`
- source_quality_gate: `microstructure risk_off requires market RISK_OFF or broad evaluated-symbol confirmation`
- reasons: `market_panic_breadth_risk_off`

## 방어 액션

- `hard_protect_emergency_delay_forbidden`: `enforced` / runtime_effect=`false`
- `live_threshold_mutation_forbidden`: `enforced` / runtime_effect=`false`
- `recovery_probe_review`: `candidate_only` / runtime_effect=`false`

## Canary Candidates

- `panic_entry_freeze_guard`: `report_only_candidate`, allowed_runtime_apply=`false`
- `panic_stop_confirmation`: `hold_no_eligible_exit`, allowed_runtime_apply=`false`
- `panic_rebound_probe`: `hold_until_recovery_confirmed`, allowed_runtime_apply=`false`
- `panic_attribution_pack`: `active_report_only`, allowed_runtime_apply=`false`

## 금지된 자동변경

- `live_threshold_runtime_mutation`
- `score_threshold_relaxation`
- `stop_loss_relaxation`
- `auto_sell`
- `bot_restart`
- `swing_real_order_enable`

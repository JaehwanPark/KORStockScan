# Panic Sell Defense 2026-07-03

## 판정

- panic_state: `NORMAL`
- panic_regime_mode: `NORMAL`
- risk_regime_gate_state: `normal`
- risk_regime_threshold_mode: `insufficient_sample`
- panic_confirmation_policy: `portfolio stop-loss clusters are evidence; PANIC_DETECTED requires market or microstructure confirmation`
- report_only: `true`
- runtime_effect: `report_only_no_mutation`
- as_of: `2026-07-03T10:48:02`
- latest_event_at: `2026-07-03T10:48:00`
- reasons: `panic thresholds not breached`

## 패닉 지표

- panic_decision_basis: `real_exit_with_broker_provenance_only`
- real_exit_provenance_required: `true`
- real_exit_count: `0`
- non_real_exit_count: `152`
- unproven_exit_count: `152`
- sim_probe_exit_excluded_from_panic: `true`
- stop_loss_exit_count: `0`
- current_30m_stop_loss_exit_count: `0`
- max_rolling_30m_stop_loss_exit_count: `0`
- rolling_30m_stop_loss_count_quantile: `0.95`
- rolling_30m_stop_loss_count_quantile_threshold: `-`
- rolling_30m_stop_loss_count_sample: `0`
- rolling_30m_stop_loss_count_sample_ready: `false`
- panic_threshold_mode: `insufficient_sample`
- panic_source_quality_blockers: `insufficient_quantile_baseline`
- stop_loss_exit_ratio_pct: `0`
- avg_exit_profit_rate_pct: `-`
- confirmation_eligible_exit_count: `0`
- never_delay_exit_count: `0`

## 회복 지표

- active_positions: `7`
- active_profit_sample: `4`
- active_avg_unrealized_profit_rate_pct: `-1.0046`
- active_win_rate_pct: `0`
- sim_probe_provenance_passed: `true`
- post_sell_rebound_above_sell_10_20m_pct: `100`
- post_sell_rebound_above_buy_10_20m_pct: `100`

## Microstructure Detector

- evaluated_symbol_count: `231`
- risk_off_advisory_count: `0`
- allow_new_long_false_count: `0`
- panic_signal_count: `0`
- recovery_candidate_count: `0`
- recovery_confirmed_count: `0`
- missing_orderbook_count: `141`
- degraded_orderbook_count: `141`
- max_panic_score: `0.3`
- max_recovery_score: `0.4`
- micro_cusum_triggered_symbol_count: `0`
- micro_consensus_pass_symbol_count: `0`
- micro_cusum_decision_authority: `source_quality_only`

## Microstructure Market Context

- market_risk_state: `RISK_OFF`
- market_panic_breadth_as_of: `2026-07-03T10:48:01`
- market_panic_breadth_source_quality_status: `ok`
- market_panic_breadth_risk_off_advisory: `false`
- market_panic_breadth_single_market_risk_off_advisory: `true`
- evaluated_symbol_count: `231`
- risk_off_advisory_ratio_pct: `0`
- confirmed_micro_risk_off_advisory: `false`
- confirmed_risk_off_advisory: `false`
- portfolio_local_risk_off_only: `false`
- source_quality_gate: `microstructure risk_off requires market RISK_OFF or broad evaluated-symbol confirmation`
- reasons: `market_regime_risk_off`

## 방어 액션

- `hard_protect_emergency_delay_forbidden`: `enforced` / runtime_effect=`false`
- `live_threshold_mutation_forbidden`: `enforced` / runtime_effect=`false`

## Canary Candidates

- `panic_entry_freeze_guard`: `inactive_no_panic`, allowed_runtime_apply=`false`
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

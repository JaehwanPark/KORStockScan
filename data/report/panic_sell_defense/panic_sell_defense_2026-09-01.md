# Panic Sell Defense 2026-09-01

## 판정

- panic_state: `NORMAL`
- panic_regime_mode: `NORMAL`
- risk_regime_gate_state: `source_quality_blocked`
- risk_regime_threshold_mode: `insufficient_sample`
- panic_confirmation_policy: `portfolio stop-loss clusters are evidence; PANIC_DETECTED requires market or microstructure confirmation`
- report_only: `true`
- runtime_effect: `report_only_no_mutation`
- as_of: `2026-09-01T21:23:00`
- latest_event_at: `2026-09-01T19:59:59`
- reasons: `panic thresholds not breached`

## 입력 자원 계약

- memory_bounded_streaming: `true`
- scanned_row_count: `358647`
- retained_exit_event_count: `3643`
- full_event_list_materialized: `false`
- out_of_order_event_count: `0`
- unique_market_observation_count: `114425`
- duplicate_snapshot_skipped_count: `43736`

## 패닉 지표

- panic_decision_basis: `broker_confirmed_exit_identity_deduplicated`
- real_exit_provenance_required: `true`
- raw_exit_signal_count: `14`
- real_exit_count: `3`
- duplicate_real_exit_signal_count: `1`
- duplicate_real_exit_signals_excluded_from_panic: `true`
- non_real_exit_count: `10`
- unproven_exit_count: `10`
- exit_signal_partition_reconciled: `true`
- sim_probe_exit_excluded_from_panic: `true`
- stop_loss_exit_count: `1`
- current_30m_stop_loss_exit_count: `0`
- max_rolling_30m_stop_loss_exit_count: `1`
- rolling_30m_stop_loss_count_quantile: `0.95`
- rolling_30m_stop_loss_count_quantile_threshold: `1`
- rolling_30m_stop_loss_count_sample: `1`
- rolling_30m_stop_loss_count_sample_ready: `false`
- panic_threshold_mode: `insufficient_sample`
- panic_source_quality_blockers: `insufficient_quantile_baseline`
- stop_loss_exit_ratio_pct: `33.3`
- avg_exit_profit_rate_pct: `0.41`
- confirmation_eligible_exit_count: `3`
- never_delay_exit_count: `0`

## 회복 지표

- active_positions: `4`
- active_profit_sample: `1`
- active_avg_unrealized_profit_rate_pct: `-0.2959`
- active_win_rate_pct: `0`
- sim_probe_provenance_passed: `true`
- post_sell_rebound_above_sell_10_20m_pct: `0`
- post_sell_rebound_above_buy_10_20m_pct: `0`

## Microstructure Detector

- evaluated_symbol_count: `2865`
- risk_off_advisory_count: `0`
- allow_new_long_false_count: `0`
- panic_signal_count: `0`
- recovery_candidate_count: `0`
- recovery_confirmed_count: `0`
- missing_orderbook_count: `2254`
- degraded_orderbook_count: `2254`
- stale_or_unhealthy_orderbook_count: `0`
- panic_report_entry_count: `0`
- panic_active_confirmation_count: `0`
- recovery_release_transition_count: `0`
- max_observed_panic_score: `0.4309`
- panic_near_threshold_observation_count: `0`
- max_panic_score: `0.3`
- max_recovery_score: `0.3793`
- micro_cusum_triggered_symbol_count: `0`
- micro_consensus_pass_symbol_count: `0`
- micro_cusum_decision_authority: `source_quality_only`

## Microstructure Market Context

- market_risk_state: `RISK_OFF`
- market_panic_breadth_as_of: `2026-09-01T21:23:00+09:00`
- market_panic_breadth_source_quality_status: `ok`
- market_panic_breadth_risk_off_advisory: `false`
- market_panic_breadth_single_market_risk_off_advisory: `true`
- evaluated_symbol_count: `2865`
- risk_off_advisory_ratio_pct: `0`
- confirmed_micro_risk_off_advisory: `false`
- confirmed_risk_off_advisory: `false`
- portfolio_local_risk_off_only: `false`
- source_quality_gate: `microstructure risk_off requires market RISK_OFF or broad evaluated-symbol confirmation`
- reasons: `market_regime_risk_off`

## Market Weakness Observation

- raw_state: `SINGLE_MARKET_WEAKNESS`
- observation_id: `market-weakness-7dcb7ecbfb54e3309ed9`
- source_quality_ready: `true`
- release_margin_passed: `false`
- runtime_effect: `false`
- allowed_runtime_apply: `false`

## 방어 액션

- `hard_protect_emergency_delay_forbidden`: `enforced` / runtime_effect=`false`
- `live_threshold_mutation_forbidden`: `enforced` / runtime_effect=`false`
- `soft_trailing_flow_confirmation_review`: `candidate_only` / runtime_effect=`false`

## Canary Candidates

- `panic_entry_freeze_guard`: `inactive_no_panic`, allowed_runtime_apply=`false`
- `panic_stop_confirmation`: `report_only_candidate`, allowed_runtime_apply=`false`
- `panic_rebound_probe`: `hold_until_recovery_confirmed`, allowed_runtime_apply=`false`
- `panic_attribution_pack`: `active_report_only`, allowed_runtime_apply=`false`

## 금지된 자동변경

- `live_threshold_runtime_mutation`
- `score_threshold_relaxation`
- `stop_loss_relaxation`
- `auto_sell`
- `bot_restart`
- `swing_real_order_enable`

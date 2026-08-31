# Intraday WS Freshness Postclose Workorder - 2026-08-31

Codex execution scope: implement only source-quality, instrumentation, report, provenance, and tests.

## 2-Pass Execution

1. First pass: implement instrumentation/report/provenance fixes, run code review, fix defects, and re-review.
2. Second pass: confirm final review, regenerate the related report, and inspect workorder diff.

## Guardrails

- runtime_effect=false
- allowed_runtime_apply=false
- broker_order_forbidden=true
- forbidden_uses=EV,rolling_tuning,MTD_tuning,cumulative_tuning,live_auto_promotion,runtime_apply_bridge,intraday_threshold_mutation,stale_submit_bypass,broker_guard_bypass,provider_route_change,order_price_change,quantity_cap_change,position_cap_release,bot_restart,real_execution_quality_approval

## Selected Directives

### order_scanner_eligible_no_heavy_closed_loop

- decision: `defer_evidence`
- priority: `1`
- title: Scanner eligible-to-heavy evaluation loss closure
- intent: Attribute unique promotions that passed fast precheck but never reached heavy evaluation, preserving WS stale, queue-lag, eviction, venue, and terminal outcome.
- evidence: `['eligible_without_heavy_evaluation_count=58', 'eligible_without_heavy_evaluation_rate_pct=4.7193', "final_outcome_counts={'active_queue_lag_right_censored': 1, 'active_right_censored': 3, 'direct_ws_recovery_exhausted': 185, 'downstream_guard_passed_right_censored': 9, 'fast_precheck_only_right_censored': 2, 'latency_blocked': 15, 'manual_control_exclusion_attach_skipped': 10, 'order_bundle_failed': 8, 'other_evicted': 462, 'queue_lag_with_stale_context': 586, 'recovered_ai': 12, 'recovered_heavy_no_ai': 63, 'runtime_attach_skipped': 7, 'submitted': 3}", "economic_cohorts={'eligible_no_heavy': 58, 'heavy_then_stale_queue_evict': 644, 'non_gainer_not_rising_repeat': 710, 'executable_bbo_ev_status': 'source_quality_blocked_until_exact_bbo_join'}"]`
- files_likely_touched: `['src/engine/monitoring/intraday_ws_freshness_monitor.py', 'src/engine/scalping/scanner_scheduler_replay.py', 'src/tests/test_intraday_ws_freshness_monitor.py']`
- acceptance_tests: `['pipeline_threshold_mirror_events_are_deduplicated', 'every_unique_promotion_has_one_final_outcome_or_active_right_censored', 'missing_executable_bbo_remains_source_quality_blocked_not_zero_ev']`

### order_scanner_manual_exclusion_slot_leak

- decision: `defer_evidence`
- priority: `1`
- title: Scanner manual-exclusion WATCHING slot leak verification
- intent: Verify manually controlled symbols are pruned before WATCHING persistence and that legacy exact zero-fill generations are terminalized without touching holdings.
- evidence: `['manual_control_exclusion_attach_skip_count=10', 'manual_control_exclusion_terminalized_count=1']`
- files_likely_touched: `['src/scanners/scalping_scanner.py', 'src/engine/kiwoom_sniper_v2.py', 'src/tests/test_scalping_scanner_candidate_pool.py', 'src/tests/test_kiwoom_sniper_market_regime_runtime.py']`
- acceptance_tests: `['manual_excluded_scanner_promotion_count=0', 'manual_excluded_scanner_ws_reg_count=0', 'manual_excluded_zero_fill_watching_count=0', 'other_owner_and_filled_position_mutation_count=0']`

### order_scanner_runtime_handoff_provenance_gap

- decision: `defer_evidence`
- priority: `1`
- title: Scanner runtime handoff provenance closure
- intent: Require an exact promotion id, local runtime handoff epoch, runtime instance id, and provenance version on every successful scanner WATCHING attach.
- evidence: `['attach_success_count=1351', 'handoff_provenance_complete_count=298', 'handoff_provenance_coverage_pct=22.0577']`
- files_likely_touched: `['src/engine/kiwoom_sniper_v2.py', 'src/engine/monitoring/intraday_ws_freshness_monitor.py', 'src/tests/test_kiwoom_sniper_market_regime_runtime.py', 'src/tests/test_intraday_ws_freshness_monitor.py']`
- acceptance_tests: `['successful_attach_handoff_provenance_coverage_pct=100', 'same_promotion_refresh_preserves_handoff_epoch', 'new_promotion_rotates_handoff_epoch']`

### order_ws_decision_stage_stale_backoff_attribution

- decision: `defer_evidence`
- priority: `1`
- title: WS decision-stage stale backoff attribution
- intent: Attribute explicit scanner stale/backoff rows to subscription repair, decision-stage freshness, and watchlist eviction timing without weakening the stale submit boundary.
- evidence: `['decision_stage_stale_backoff_count=11084', "causal_attribution={'sample_count': 11084, 'reason_counts': {'ws_snapshot_missing_or_zero': 1156, 'persistent_ws_gap': 3087, 'stale_ws_snapshot': 4236, 'scanner_ws_stale_backoff_active': 2605}, 'repair_cycle_state_counts': {'ws_reg_reissued_waiting_snapshot': 1076, 'persistent_ws_gap': 2050, 'not_observed': 7929, 'ws_repair_cycle_waiting_snapshot': 29}, 'recheck_reason_counts': {'not_applicable_active_backoff': 3132, 'not_observed': 4898, 'not_applicable_ws_stale_backoff_recheck': 3054}, 'watchlist_outcome_counts': {'decision_stage_only': 10021, 'evicted': 601, 'retained': 462}}"]`
- files_likely_touched: `['src/engine/kiwoom_websocket.py', 'src/engine/sniper_state_handlers.py', 'src/engine/monitoring/intraday_ws_freshness_monitor.py', 'src/tests/test_intraday_ws_freshness_monitor.py']`
- acceptance_tests: `['PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_kiwoom_websocket.py src/tests/test_intraday_ws_freshness_monitor.py']`

### order_ws_total_stale_escalation

- decision: `defer_evidence`
- priority: `1`
- title: WS total stale escalation
- intent: Treat rows where both trade and orderbook websocket freshness are stale as subscription/connection quality incidents and verify repair evidence after postclose.
- evidence: `['both_ws_stale_count=52', "repair_attribution={'sample_count': 52, 'repair_cycle_state_counts': {'not_observed': 50, 'persistent_ws_gap': 2}, 'repair_required_counts': {'not_observed': 50, 'required': 2}}"]`
- files_likely_touched: `['src/engine/kiwoom_websocket.py', 'src/engine/monitoring/quote_stale_frequency_report.py', 'src/engine/monitoring/intraday_ws_freshness_monitor.py']`
- acceptance_tests: `['PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_kiwoom_websocket.py src/tests/test_intraday_ws_freshness_monitor.py']`

### order_scanner_funnel_executable_bbo_join

- decision: `defer_evidence`
- priority: `2`
- title: Scanner funnel executable-BBO economic attribution
- intent: Join each unique lost scanner generation to fresh executable bid/ask, quote age, venue/session, fixed effective-dated costs, target/adverse first-hit, and timeout exit.
- evidence: `['economic_candidate_count=1412', "economic_cohorts={'eligible_no_heavy': 58, 'heavy_then_stale_queue_evict': 644, 'non_gainer_not_rising_repeat': 710, 'executable_bbo_ev_status': 'source_quality_blocked_until_exact_bbo_join'}"]`
- files_likely_touched: `['src/engine/scalping/rising_missed_intraday_feedback.py', 'src/engine/monitoring/intraday_ws_freshness_monitor.py', 'src/tests/test_rising_missed_intraday_feedback.py']`
- acceptance_tests: `['exact_promotion_venue_session_bbo_join_coverage_pct>=95', 'missing_bbo_is_source_quality_blocked_not_zero_profit', 'KRX_PREMARKET_KRX_LIKE_NXT_results_are_separate', 'fixed_cost_contract_effective_date_and_source_hash_match']`

### order_ws_trade_tick_quiet_low_liquidity_classification

- decision: `defer_evidence`
- priority: `2`
- title: WS trade tick quiet low-liquidity classification
- intent: Keep fresh 0D plus stale/missing 0B as trade_tick_quiet source-quality evidence, and enrich low-liquidity classification with cumulative-volume provenance before requesting subscription repair.
- evidence: `['pipeline_trade_tick_quiet_count=1501', 'fresh_0d_stale_0b_count=763', 'snapshot_trade_tick_quiet_count=2', "cumulative_volume_provenance={'signed_tape_only_cumulative_volume_missing': 342, 'cumulative_volume_missing': 1159}", "snapshot_cumulative_volume_provenance={'cumulative_volume_missing': 2}"]`
- files_likely_touched: `['src/engine/kiwoom_websocket.py', 'src/engine/sniper_state_handlers.py', 'src/engine/monitoring/intraday_ws_freshness_monitor.py', 'src/tests/test_state_handler_fast_signatures.py']`
- acceptance_tests: `['PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_state_handler_fast_signatures.py src/tests/test_intraday_ws_freshness_monitor.py']`

## Required Final Report Split

- Existing implementation
- New implementation
- Deferred or non-implement items

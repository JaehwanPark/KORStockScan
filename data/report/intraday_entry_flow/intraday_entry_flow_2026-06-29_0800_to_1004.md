# 2026-06-30 08:00 이후 감시대상 BUY 전 흐름

- generated_at: 2026-06-30T08:03:24+09:00
- source_events: data/pipeline_events/pipeline_events_2026-06-30.jsonl
- source_diagnostic: data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-30_0803_goal.json
- event_window_since: 2026-06-30T08:00:00+09:00
- symbol_count: 14
- rising_symbol_count_by_max_delta: 9
- rising_missed_buy_count_in_latest_diagnostic: 3
- rising_missed_symbol_count_in_report: 3
- real_submit_symbol_count_in_latest_diagnostic: 6
- buy_signal_or_pre_submit_pass_seen_symbols: 11
- stale_eval_symbol_count: 14
- rising_stale_eval_symbol_count: 9
- rising_fresh_only_symbol_count: 0
- stale_refresh_recovered_symbol_count: 5

## blocker rollup

- 7: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 2: `scalping_scanner_promotion_latency_trace` / `before_strategy_start`
- 2: `scalping_scanner_promotion_latency_trace` / `caution_normal_entry_allowed`
- 1: `blocked_liquidity` / `-`
- 1: `scalping_scanner_promotion_latency_trace` / `latency_state_danger`
- 1: `score65_74_recovery_probe_blocked` / `-`

## blocker taxonomy

- 20: `strategy_reject`
- 9: `runtime_backpressure`
- 2: `source_freshness_recovering`

## suppressed non-major blocker counts

- 9: `runtime_backpressure` / `scalping_scanner_watching_runtime_skip` / `scanner_full_eval_loop_budget_deferred`
- 2: `source_freshness_recovering` / `scalping_scanner_watching_runtime_skip` / `ws_snapshot_missing_or_zero`

## rising-symbol blocker rollup

- 2: `scalping_scanner_promotion_latency_trace` / `before_strategy_start`
- 2: `scalping_scanner_promotion_latency_trace` / `caution_normal_entry_allowed`
- 2: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 1: `blocked_liquidity` / `-`
- 1: `scalping_scanner_promotion_latency_trace` / `latency_state_danger`
- 1: `score65_74_recovery_probe_blocked` / `-`

## rising fresh-only blocker rollup


## rising stale-mixed blocker rollup

- 2: `scalping_scanner_promotion_latency_trace` / `before_strategy_start`
- 2: `scalping_scanner_promotion_latency_trace` / `caution_normal_entry_allowed`
- 2: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 1: `blocked_liquidity` / `-`
- 1: `scalping_scanner_promotion_latency_trace` / `latency_state_danger`
- 1: `score65_74_recovery_probe_blocked` / `-`

## stale-eval rollup

- 11: `scalping_scanner_fast_precheck`
- 2: `scalping_scanner_watching_runtime_skip`
- 1: `scalp_entry_action_decision_snapshot`

## stale-eval category rollup

- 12: `diagnostic_quote_age_stale`
- 2: `ws_snapshot_missing_or_zero`

## top rows by max delta

|종목|첫감시|마지막|상승여부|maxΔ|latestΔ|BUY전 주 blocker|class|stale평가|refresh회복|stale유형|max quote age|BUY전 통과신호|AI|실제submit|흐름|
|---|---:|---:|---|---:|---:|---|---|---:|---:|---|---:|---:|---:|---:|---|
|가온전선(000500)|08:01:42|08:03:38|rising|11.19%|11.19%|`scalping_scanner_promotion_latency_trace`/before_strategy_start|-|3|2|diagnostic_quote_age_stale|11446.0|08:03:00|0/not_evaluated|0|08:00:12 scalping_scanner_candidate_observed -> 08:00:12 scalping_scanner_real_source_guard_block -> 08:01:42 scalping_scanner_candidate_promoted(+11.19%) -> 08:01:43 scalping_scanner_runtime_target_attach(+11.19%) -> ... -> 08:03:57 scalping_scanner_promotion_latency_trace(+11.19%) -> 08:03:57 scalping_scanner_fast_precheck(+11.19%) -> 08:03:57 scalping_scanner_runtime_queue_lag(+11.19%)|
|데브시스터즈(194480)|08:01:42|08:03:37|rising|6.43%|6.43%|`blocked_liquidity`/-|strategy_reject|2|3|diagnostic_quote_age_stale|11436.0|08:03:00|60/WAIT|3|08:00:12 scalping_scanner_candidate_observed -> 08:00:12 scalping_scanner_real_source_guard_block -> 08:01:42 scalping_scanner_candidate_promoted(+6.43%) -> 08:01:43 scalping_scanner_runtime_target_attach(+6.43%) -> ... -> 08:03:57 blocked_ai_score(+6.43%) -> 08:03:57 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+6.43%) -> 08:03:57 scalp_entry_action_decision_snapshot(+6.43%)|
|제룡전기(033100)|08:01:42|08:03:30|rising|2.72%|2.72%|`scalping_scanner_promotion_latency_trace`/before_strategy_start|-|3|2|diagnostic_quote_age_stale|23586.0|08:03:18|0/not_evaluated|0|08:00:12 scalping_scanner_candidate_observed -> 08:00:12 scalping_scanner_real_source_guard_block -> 08:01:42 scalping_scanner_candidate_promoted(+2.72%) -> 08:01:43 scalping_scanner_runtime_target_attach(+2.72%) -> ... -> 08:03:55 scalping_scanner_promotion_latency_trace(+2.72%) -> 08:03:55 scalping_scanner_fast_precheck(+2.72%) -> 08:03:55 scalping_scanner_runtime_queue_lag(+2.72%)|
|LS ELECTRIC(010120)|08:01:43|08:03:38|rising|2.60%|2.60%|`scalping_scanner_promotion_latency_trace`/latency_state_danger|-|3|0|diagnostic_quote_age_stale|11443.0|08:03:06|0/not_evaluated|0|08:00:12 scalping_scanner_candidate_observed -> 08:00:12 scalping_scanner_real_source_guard_block -> 08:01:43 scalping_scanner_candidate_promoted(+1.73%) -> 08:01:43 scalping_scanner_runtime_target_attach(+1.73%) -> ... -> 08:03:57 scalping_scanner_promotion_latency_trace(+2.60%) -> 08:03:57 scalping_scanner_fast_precheck(+2.60%) -> 08:03:57 scalping_scanner_runtime_queue_lag(+2.60%)|
|엑스게이트(356680)|08:01:42|08:03:38|rising|1.60%|1.32%|`score65_74_recovery_probe_blocked`/-|strategy_reject|9|0|diagnostic_quote_age_stale|6785.0|08:03:00|63/WAIT|3|08:00:12 scalping_scanner_candidate_observed -> 08:00:12 scalping_scanner_real_source_guard_block -> 08:01:42 scalping_scanner_candidate_promoted(+1.32%) -> 08:01:43 scalping_scanner_runtime_target_attach(+1.32%) -> ... -> 08:03:38 scalp_entry_action_decision_snapshot(+1.32%) -> 08:03:57 rising_missed_scout_upgrade_eval(+1.32%) -> 08:03:57 scalping_scanner_watching_runtime_skip:entry_cooldown_active(+1.32%)|
|SK하이닉스(000660)|08:01:42|08:03:49|rising|0.83%|0.83%|`scalping_scanner_promotion_latency_trace`/caution_normal_entry_allowed|-|4|0|diagnostic_quote_age_stale|18934.0|08:03:44|0/not_evaluated|3|08:00:12 scalping_scanner_candidate_observed -> 08:00:12 scalping_scanner_real_source_guard_block -> 08:01:42 scalping_scanner_candidate_promoted(+0.83%) -> 08:01:43 scalping_scanner_runtime_target_attach(+0.83%) -> ... -> 08:03:49 buy_signal_telegram_enqueued(+0.83%) -> 08:03:49 order_bundle_submitted:caution_normal_entry_allowed(+0.83%) -> 08:03:49 scalp_entry_action_decision_snapshot:caution_normal_entry_allowed(+0.83%)|
|두산에너빌리티(034020)|08:01:42|08:03:43|rising|0.67%|0.67%|`scalping_scanner_promotion_latency_trace`/caution_normal_entry_allowed|-|3|5|diagnostic_quote_age_stale|11439.0|08:03:18|0/not_evaluated|3|08:00:12 scalping_scanner_candidate_observed -> 08:00:12 scalping_scanner_real_source_guard_block -> 08:01:42 scalping_scanner_candidate_promoted(+0.67%) -> 08:01:43 scalping_scanner_runtime_target_attach(+0.67%) -> ... -> 08:03:43 scalp_entry_action_decision_snapshot:caution_normal_entry_allowed(+0.67%) -> 08:03:57 entry_reprice_after_submit_evaluated(+0.67%) -> 08:03:57 entry_reprice_after_submit_blocked(+0.67%)|
|원익IPS(240810)|08:01:42|08:03:32|rising|0.55%|0.55%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|3|0|ws_snapshot_missing_or_zero|1798.0|08:03:12|0/not_evaluated|3|08:00:12 scalping_scanner_candidate_observed -> 08:00:12 scalping_scanner_real_source_guard_block -> 08:01:42 scalping_scanner_candidate_promoted(+0.55%) -> 08:01:43 scalping_scanner_runtime_target_attach(+0.55%) -> ... -> 08:03:18 scalp_entry_action_decision_snapshot:caution_normal_entry_allowed(+0.55%) -> 08:03:32 entry_reprice_after_submit_evaluated(+0.55%) -> 08:03:32 entry_reprice_after_submit_blocked(+0.55%)|
|삼성전자(005930)|08:01:42|08:03:49|rising|0.46%|0.46%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|6|3|diagnostic_quote_age_stale|18934.0|08:03:49|0/not_evaluated|3|08:00:12 scalping_scanner_candidate_observed -> 08:00:12 scalping_scanner_real_source_guard_block -> 08:01:42 scalping_scanner_candidate_promoted(+0.46%) -> 08:01:43 scalping_scanner_runtime_target_attach(+0.46%) -> ... -> 08:03:54 order_bundle_submitted:caution_normal_entry_allowed(+0.46%) -> 08:03:54 scalp_entry_action_decision_snapshot:caution_normal_entry_allowed(+0.46%) -> 08:03:55 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.46%)|
|애경케미칼(161000)|08:00:12|08:03:30|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|6|0|diagnostic_quote_age_stale|23788.0|-||0|08:00:12 scalping_scanner_candidate_promoted(+0.00%) -> 08:00:12 scalping_scanner_runtime_target_attach(+0.00%) -> 08:00:13 scalping_scanner_promotion_latency_trace(+0.00%) -> 08:00:13 scalping_scanner_watching_runtime_skip:before_strategy_start(+0.00%) -> ... -> 08:03:55 scalping_scanner_fast_precheck(+0.00%) -> 08:03:55 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%) -> 08:03:55 scalping_scanner_watching_runtime_skip:scanner_full_eval_loop_budget_deferred(+0.00%)|
|현대무벡스(319400)|08:03:13|08:03:30|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|2|0|diagnostic_quote_age_stale|23579.0|08:04:00|82/BUY|0|08:03:13 scalping_scanner_candidate_promoted(+0.00%) -> 08:03:13 scalping_scanner_runtime_target_attach(+0.00%) -> 08:03:30 scalping_scanner_promotion_latency_trace(+0.00%) -> 08:03:30 scalping_scanner_fast_precheck(+0.00%) -> ... -> 08:04:00 ai_numeric_consistency_recheck_skipped:original_action_not_wait(+0.00%) -> 08:04:00 entry_armed:qualification_passed(+0.00%) -> 08:04:00 scalp_entry_action_decision_snapshot:Position advantage present: curr_vs_micro_vwap_bp > 0 and curr_vs_ma5_bp > 0; Speed favorable: tick_acceleration_ratio >(+0.00%)|
|화신(010690)|08:01:42|08:03:30|flat_or_falling|-0.18%|-0.18%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|5|0|diagnostic_quote_age_stale|23630.0|-||0|08:00:12 scalping_scanner_candidate_observed -> 08:00:12 scalping_scanner_real_source_guard_block -> 08:01:42 scalping_scanner_candidate_promoted(-0.18%) -> 08:01:43 scalping_scanner_runtime_target_attach(-0.18%) -> ... -> 08:03:55 scalping_scanner_fast_precheck(-0.18%) -> 08:03:55 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(-0.18%) -> 08:03:55 scalping_scanner_watching_runtime_skip:scanner_full_eval_loop_budget_deferred(-0.18%)|
|한미반도체(042700)|08:01:43|08:03:30|flat_or_falling|-0.19%|-0.19%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|5|0|diagnostic_quote_age_stale|23622.0|-||0|08:00:12 scalping_scanner_candidate_observed -> 08:00:12 scalping_scanner_real_source_guard_block -> 08:01:43 scalping_scanner_candidate_promoted(-0.19%) -> 08:01:43 scalping_scanner_runtime_target_attach(-0.19%) -> ... -> 08:03:55 scalping_scanner_fast_precheck(-0.19%) -> 08:03:55 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(-0.19%) -> 08:03:55 scalping_scanner_watching_runtime_skip:scanner_full_eval_loop_budget_deferred(-0.19%)|
|에코프로비엠(247540)|08:01:43|08:03:32|flat_or_falling|-1.41%|-1.41%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|3|0|ws_snapshot_missing_or_zero|1327.0|08:03:07|0/not_evaluated|3|08:00:12 scalping_scanner_candidate_observed -> 08:00:12 scalping_scanner_real_source_guard_block -> 08:01:43 scalping_scanner_candidate_promoted(-1.41%) -> 08:01:43 scalping_scanner_runtime_target_attach(-1.41%) -> ... -> 08:03:12 scalp_entry_action_decision_snapshot:caution_normal_entry_allowed(-1.41%) -> 08:03:32 entry_reprice_after_submit_evaluated(-1.41%) -> 08:03:32 entry_reprice_after_submit_blocked(-1.41%)|

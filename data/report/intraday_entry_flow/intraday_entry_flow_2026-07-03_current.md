# 2026-07-03 10:00 이후 감시대상 BUY 전 흐름

- generated_at: 2026-07-03T10:40:20
- source_events: /home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-03.jsonl
- source_diagnostic: /home/ubuntu/KORStockScan/data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-07-03.json
- event_window_since: 10:00
- event_window_until: 10:40
- symbol_count: 40
- rising_symbol_count_by_max_delta: 10
- rising_missed_buy_count_in_latest_diagnostic: 9
- rising_missed_symbol_count_in_report: 9
- rising_missed_residual_excluding_forced_scout_symbol_count: 1
- rising_missed_forced_scout_event_count: 9
- rising_missed_forced_scout_symbol_count: 15
- rising_missed_forced_scout_residual_symbol_count: 8
- real_submit_symbol_count_in_latest_diagnostic: 0
- buy_signal_or_pre_submit_pass_seen_symbols: 6
- stale_eval_symbol_count: 28
- rising_stale_eval_symbol_count: 10
- rising_fresh_only_symbol_count: 0
- stale_refresh_recovered_symbol_count: 13

## forced scout observation

- event_count: 9
- symbol_count: 15
- symbols: 000500, 009520, 010120, 033100, 037710, 042660, 090460, 094360, 095500, 161890, 373220, 376900, 441270, 484810, 486990
- rising_missed_residual_symbols: 000500, 033100, 037710, 094360, 095500, 376900, 441270, 484810
- rising_missed_residual_excluding_forced_scout_symbols: 004440
- decision_authority: source_quality_only
- runtime_effect: False

## blocker rollup

- 12: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 9: `blocked_strength_momentum` / `insufficient_history`
- 7: `scalping_scanner_runtime_target_attach` / `operator_manual_control_excluded_symbol`
- 3: `scalping_scanner_runtime_target_attach` / `scanner_identity_name_mismatch`
- 2: `scalping_scanner_watching_runtime_skip` / `ws_snapshot_missing_or_zero`
- 2: `scalping_scanner_candidate_observed` / `-`
- 1: `scalping_scanner_runtime_target_attach` / `eventbus_attach_missing_recovered_from_database_poll`
- 1: `scalping_scanner_runtime_target_attach` / `same_symbol_active_order_or_holding`
- 1: `scalping_scanner_runtime_target_attach` / `new_watching_target_attached`
- 1: `blocked_liquidity` / `-`
- 1: `scalping_scanner_runtime_target_attach` / `-`

## blocker taxonomy

- 121: `strategy_reject`
- 57: `intended_guard`
- 11: `source_quality_exclusion_candidate`
- 11: `watch_budget_reallocated`
- 9: `source_freshness_recovering`
- 4: `runtime_backpressure`

## suppressed non-major blocker counts

- 74: `strategy_reject` / `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 53: `intended_guard` / `scalping_scanner_runtime_target_attach` / `operator_manual_control_excluded_symbol`
- 14: `strategy_reject` / `scalping_scanner_runtime_target_attach` / `new_watching_target_attached`
- 11: `source_quality_exclusion_candidate` / `blocked_strength_momentum` / `insufficient_history`
- 9: `source_freshness_recovering` / `scalping_scanner_watching_runtime_skip` / `ws_snapshot_missing_or_zero`
- 9: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `stale_recovery_failed`
- 6: `strategy_reject` / `blocked_strength_momentum` / `below_strength_base`
- 4: `runtime_backpressure` / `scalping_scanner_watching_runtime_skip` / `scanner_full_eval_loop_budget_deferred`
- 4: `strategy_reject` / `blocked_ai_score` / ``
- 4: `intended_guard` / `scalping_scanner_watching_runtime_skip` / `entry_cooldown_active`
- 3: `strategy_reject` / `blocked_vpw` / ``
- 3: `strategy_reject` / `ai_confirmed_terminal_no_budget` / `first_ai_wait_big_bite_not_confirmed`

## rising-symbol blocker rollup

- 6: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 1: `scalping_scanner_runtime_target_attach` / `eventbus_attach_missing_recovered_from_database_poll`
- 1: `scalping_scanner_runtime_target_attach` / `operator_manual_control_excluded_symbol`
- 1: `scalping_scanner_runtime_target_attach` / `same_symbol_active_order_or_holding`
- 1: `blocked_strength_momentum` / `insufficient_history`

## rising fresh-only blocker rollup


## rising stale-mixed blocker rollup

- 6: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 1: `scalping_scanner_runtime_target_attach` / `eventbus_attach_missing_recovered_from_database_poll`
- 1: `scalping_scanner_runtime_target_attach` / `operator_manual_control_excluded_symbol`
- 1: `scalping_scanner_runtime_target_attach` / `same_symbol_active_order_or_holding`
- 1: `blocked_strength_momentum` / `insufficient_history`

## stale-eval rollup

- 21: `scalping_scanner_fast_precheck`
- 7: `scalping_scanner_watching_runtime_skip`

## stale-eval category rollup

- 21: `diagnostic_quote_age_stale`
- 7: `ws_snapshot_missing_or_zero`

## bounded freshness recheck workorders

|종목|건수|diagnostic stale|history gap|latest|next action|authority|runtime|
|---|---:|---:|---:|---|---|---|---|
|삼일씨엔에스(004440)|1|1|0|scalping_scanner_runtime_target_attach:new_watching_target_attached|add_or_tune_bounded_fresh_recheck_enqueue_after_stale_or_history_gap|source_quality_only|effect=False,apply=False|

## latency danger root cause

|종목|건수|top cause|spread ratio med/max|ws age med/max|spread ticks med/max|micro|bucket|
|---|---:|---|---:|---:|---:|---|---|
|NH투자증권(005940)|1|spread_microstructure_wide|0.006515/0.006515|22.0/22.0|4.0/4.0|neutral|spread=wide\|price=mid\|depth=thick\|sample=rich|

## top rows by max delta

|종목|첫감시|마지막|상승여부|maxΔ|latestΔ|BUY전 주 blocker|class|stale평가|refresh회복|stale유형|max quote age|BUY전 통과신호|AI|실제submit|흐름|
|---|---:|---:|---|---:|---:|---|---|---:|---:|---|---:|---:|---:|---:|---|
|티엑스알로보틱스(484810)|10:29:29|10:39:22|rising|6.29%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|non_actionable_guard_or_backpressure|6|0|diagnostic_quote_age_stale|36041.0|-||0|10:29:29 scalping_scanner_promotion_latency_trace(+6.29%) -> 10:29:29 scalping_scanner_fast_precheck(+6.29%) -> 10:29:29 scalping_scanner_runtime_queue_lag(+6.29%) -> 10:29:29 scalping_scanner_watching_runtime_skip:ws_snapshot_missing_or_zero_recovered(+6.29%) -> ... -> 10:39:22 scalping_scanner_runtime_queue_lag(+0.00%) -> 10:39:22 scalping_scanner_promotion_latency_trace(+0.00%) -> 10:39:22 scalping_scanner_fast_precheck(+0.00%)|
|칩스앤미디어(094360)|10:29:29|10:33:23|rising|6.06%|6.06%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|non_actionable_guard_or_backpressure|2|0|ws_snapshot_missing_or_zero|6158.0|-||0|10:29:29 scalping_scanner_promotion_latency_trace(+6.06%) -> 10:29:29 scalping_scanner_fast_precheck(+6.06%) -> 10:29:29 scalping_scanner_runtime_queue_lag(+6.06%) -> 10:29:29 scalping_scanner_watching_runtime_skip:ws_snapshot_missing_or_zero_recovered(+6.06%) -> ... -> 10:29:38 scalping_scanner_watching_runtime_skip:scanner_heavy_eval_stale_snapshot_recheck(+6.06%) -> 10:33:23 scalping_scanner_candidate_observed -> 10:33:23 scalping_scanner_real_source_guard_block|
|제룡전기(033100)|10:29:33|10:29:38|rising|5.76%|5.76%|`scalping_scanner_runtime_target_attach`/eventbus_attach_missing_recovered_from_database_poll|non_actionable_guard_or_backpressure|1|0|ws_snapshot_missing_or_zero||-||0|10:29:33 scalping_scanner_runtime_target_attach -> 10:29:38 scalping_scanner_promotion_latency_trace(+5.76%) -> 10:29:38 scalping_scanner_fast_precheck(+5.76%) -> 10:29:38 scalping_scanner_runtime_queue_lag(+5.76%) -> 10:29:38 scalping_scanner_watching_runtime_skip:ws_snapshot_missing_or_zero_recovered(+5.76%) -> 10:29:38 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+5.76%)|
|가온전선(000500)|10:29:29|10:30:23|rising|5.39%|0.00%|`scalping_scanner_runtime_target_attach`/operator_manual_control_excluded_symbol|non_actionable_guard_or_backpressure|3|0|diagnostic_quote_age_stale|25943.0|-||0|10:29:29 scalping_scanner_promotion_latency_trace(+5.39%) -> 10:29:29 scalping_scanner_fast_precheck(+5.39%) -> 10:29:29 scalping_scanner_runtime_queue_lag(+5.39%) -> 10:29:29 scalping_scanner_watching_runtime_skip:ws_snapshot_missing_or_zero_recovered(+5.39%) -> ... -> 10:29:56 scalping_scanner_runtime_queue_lag(+5.39%) -> 10:30:22 scalping_scanner_candidate_promoted(+0.00%) -> 10:30:22 scalping_scanner_runtime_target_attach(+0.00%)|
|파인엠텍(441270)|10:29:29|10:39:22|rising|4.26%|4.26%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|non_actionable_guard_or_backpressure|15|0|diagnostic_quote_age_stale|77880.0|-||0|10:29:29 scalping_scanner_promotion_latency_trace(+4.26%) -> 10:29:29 scalping_scanner_fast_precheck(+4.26%) -> 10:29:29 scalping_scanner_runtime_queue_lag(+4.26%) -> 10:29:29 scalping_scanner_watching_runtime_skip:ws_snapshot_missing_or_zero_recovered(+4.26%) -> ... -> 10:39:22 scalping_scanner_runtime_queue_lag(+4.26%) -> 10:39:22 scalping_scanner_promotion_latency_trace(+4.26%) -> 10:39:22 scalping_scanner_heavy_eval_lag(+4.26%)|
|광주신세계(037710)|10:34:54|10:39:18|rising|3.60%|3.60%|`scalping_scanner_runtime_target_attach`/same_symbol_active_order_or_holding|non_actionable_guard_or_backpressure|5|0|diagnostic_quote_age_stale|77768.0|-||0|10:34:54 scalping_scanner_candidate_promoted(+0.00%) -> 10:34:54 scalping_scanner_runtime_target_attach(+0.00%) -> 10:36:12 scalping_scanner_promotion_latency_trace(+3.60%) -> 10:36:12 scalping_scanner_fast_precheck(+3.60%) -> ... -> 10:39:18 scalping_scanner_promotion_latency_trace(+3.60%) -> 10:39:18 scalping_scanner_fast_precheck(+3.60%) -> 10:39:18 scalping_scanner_runtime_queue_lag(+3.60%)|
|미래나노텍(095500)|10:29:29|10:29:32|rising|2.64%|2.64%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|non_actionable_guard_or_backpressure|2|0|ws_snapshot_missing_or_zero||-||0|10:29:29 scalping_scanner_promotion_latency_trace(+2.64%) -> 10:29:29 scalping_scanner_fast_precheck(+2.64%) -> 10:29:29 scalping_scanner_runtime_queue_lag(+2.64%) -> 10:29:29 scalping_scanner_watching_runtime_skip:ws_snapshot_missing_or_zero_recovered(+2.64%) -> 10:29:29 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+2.64%) -> 10:29:32 scalping_scanner_watching_runtime_skip:ws_snapshot_missing_or_zero(+2.64%)|
|삼일씨엔에스(004440)|10:31:52|10:39:22|rising|1.32%|1.32%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|non_actionable_guard_or_backpressure|6|2|diagnostic_quote_age_stale|80419.0|-|50/|0|10:31:52 scalping_scanner_candidate_observed -> 10:31:52 scalping_scanner_real_source_guard_block -> 10:33:23 scalping_scanner_candidate_promoted(+0.66%) -> 10:33:23 scalping_scanner_runtime_target_attach(+0.66%) -> ... -> 10:39:22 scalping_scanner_promotion_latency_trace(+1.32%) -> 10:39:22 scalping_scanner_fast_precheck(+1.32%) -> 10:39:22 scalping_scanner_runtime_queue_lag(+1.32%)|
|로킷헬스케어(376900)|10:29:29|10:34:54|rising|1.04%|1.04%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|non_actionable_guard_or_backpressure|2|0|ws_snapshot_missing_or_zero||-||0|10:29:29 scalping_scanner_promotion_latency_trace(+1.04%) -> 10:29:29 scalping_scanner_fast_precheck(+1.04%) -> 10:29:29 scalping_scanner_runtime_queue_lag(+1.04%) -> 10:29:29 scalping_scanner_watching_runtime_skip:ws_snapshot_missing_or_zero_recovered(+1.04%) -> ... -> 10:33:23 scalping_scanner_real_source_guard_block -> 10:34:54 scalping_scanner_candidate_observed -> 10:34:54 scalping_scanner_real_source_guard_block|
|한국콜마(161890)|10:29:29|10:32:19|rising|0.66%|0.00%|`blocked_strength_momentum`/insufficient_history|source_freshness_blocker|8|5|diagnostic_quote_age_stale|17526.0|10:31:53|58/WAIT|0|10:29:29 scalping_scanner_promotion_latency_trace(+0.66%) -> 10:29:29 scalping_scanner_fast_precheck(+0.66%) -> 10:29:29 scalping_scanner_runtime_queue_lag(+0.66%) -> 10:29:29 scalping_scanner_watching_runtime_skip:ws_snapshot_missing_or_zero_recovered(+0.66%) -> ... -> 10:32:10 scalping_scanner_runtime_queue_lag(+0.00%) -> 10:32:10 scalping_scanner_watch_eviction:stale_recovery_failed(+0.00%) -> 10:32:19 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%)|
|실리콘투(257720)|10:29:56|10:39:22|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/insufficient_history|source_freshness_blocker|6|5|diagnostic_quote_age_stale|78283.0|10:30:06|57/WAIT|0|10:29:56 scalping_scanner_promotion_latency_trace(+0.00%) -> 10:29:56 scalping_scanner_fast_precheck(+0.00%) -> 10:29:56 scalping_scanner_runtime_queue_lag(+0.00%) -> 10:29:56 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 10:39:22 scalping_scanner_promotion_latency_trace(+0.00%) -> 10:39:22 scalping_scanner_fast_precheck(+0.00%) -> 10:39:22 scalping_scanner_runtime_queue_lag(+0.00%)|
|파세코(037070)|10:30:22|10:39:18|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/insufficient_history|source_freshness_blocker|18|8|diagnostic_quote_age_stale|71613.0|10:34:11|62/WAIT|0|10:30:22 scalping_scanner_candidate_promoted(+0.00%) -> 10:30:22 scalping_scanner_runtime_target_attach(+0.00%) -> 10:30:48 scalping_scanner_watching_runtime_skip:ws_snapshot_missing_or_zero(+0.00%) -> 10:32:10 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 10:39:18 scalping_scanner_fast_precheck(+0.00%) -> 10:39:18 scalping_scanner_runtime_queue_lag(+0.00%) -> 10:39:18 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%)|
|NH투자증권(005940)|10:30:22|10:39:18|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|non_actionable_guard_or_backpressure|21|14|diagnostic_quote_age_stale|71618.0|10:32:41|50/WAIT|0|10:30:22 scalping_scanner_candidate_promoted(+0.00%) -> 10:30:22 scalping_scanner_runtime_target_attach(+0.00%) -> 10:30:30 scalping_scanner_promotion_latency_trace(+0.00%) -> 10:30:30 scalping_scanner_fast_precheck(+0.00%) -> ... -> 10:39:18 scalping_scanner_promotion_latency_trace(+0.00%) -> 10:39:18 scalping_scanner_fast_precheck(+0.00%) -> 10:39:18 scalping_scanner_runtime_queue_lag(+0.00%)|
|아로마티카(000150)|10:30:22|10:30:22|flat_or_falling|0.00%|0.00%|`scalping_scanner_runtime_target_attach`/scanner_identity_name_mismatch|non_actionable_guard_or_backpressure|0|0|-||-||0|10:30:22 scalping_scanner_candidate_promoted(+0.00%) -> 10:30:22 scalping_scanner_runtime_target_attach(+0.00%)|
|KoAct 미국바이오헬스케어액티브(001130)|10:30:22|10:30:22|flat_or_falling|0.00%|0.00%|`scalping_scanner_runtime_target_attach`/scanner_identity_name_mismatch|non_actionable_guard_or_backpressure|0|0|-||-||0|10:30:22 scalping_scanner_candidate_promoted(+0.00%) -> 10:30:22 scalping_scanner_runtime_target_attach(+0.00%)|
|뉴파워프라즈마(144960)|10:30:22|10:31:26|flat_or_falling|0.00%|0.00%|`scalping_scanner_runtime_target_attach`/new_watching_target_attached|non_actionable_guard_or_backpressure|2|2|ws_snapshot_missing_or_zero|3267.0|-|50/|0|10:30:22 scalping_scanner_candidate_promoted(+0.00%) -> 10:30:22 scalping_scanner_runtime_target_attach(+0.00%) -> 10:30:48 scalping_scanner_watching_runtime_skip:ws_snapshot_missing_or_zero(+0.00%) -> 10:31:06 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 10:31:12 blocked_strength_momentum:below_strength_base(+0.00%) -> 10:31:26 scalping_scanner_watch_eviction:scanner_hardgate_prefilter(+0.00%) -> 10:31:26 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%)|
|송원산업(004430)|10:30:22|10:32:19|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/insufficient_history|source_freshness_blocker|5|0|diagnostic_quote_age_stale|44120.0|-|50/|0|10:30:22 scalping_scanner_candidate_promoted(+0.00%) -> 10:30:22 scalping_scanner_runtime_target_attach(+0.00%) -> 10:30:30 scalping_scanner_promotion_latency_trace(+0.00%) -> 10:30:30 scalping_scanner_fast_precheck(+0.00%) -> ... -> 10:32:10 scalping_scanner_runtime_queue_lag(+0.00%) -> 10:32:10 scalping_scanner_watch_eviction:stale_recovery_failed(+0.00%) -> 10:32:19 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%)|
|코오롱티슈진(950160)|10:30:22|10:33:26|flat_or_falling|0.00%|0.00%|`blocked_liquidity`/-|non_actionable_guard_or_backpressure|2|8|diagnostic_quote_age_stale|17524.0|10:30:41|62/WAIT|0|10:30:22 scalping_scanner_candidate_promoted(+0.00%) -> 10:30:22 scalping_scanner_runtime_target_attach(+0.00%) -> 10:30:30 scalping_scanner_promotion_latency_trace(+0.00%) -> 10:30:30 scalping_scanner_fast_precheck(+0.00%) -> ... -> 10:33:11 scalping_scanner_heavy_eval_lag(+0.00%) -> 10:33:13 scalping_scanner_watching_runtime_skip:entry_cooldown_active(+0.00%) -> 10:33:26 scalping_scanner_watch_eviction:safety_cooldown_pool_blocked(+0.00%)|
|플리토(300080)|10:30:22|10:33:05|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|non_actionable_guard_or_backpressure|4|0|ws_snapshot_missing_or_zero|16255.0|-||0|10:30:22 scalping_scanner_candidate_promoted(+0.00%) -> 10:30:22 scalping_scanner_runtime_target_attach(+0.00%) -> 10:30:48 scalping_scanner_watching_runtime_skip:ws_snapshot_missing_or_zero(+0.00%) -> 10:31:33 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 10:32:24 scalping_scanner_runtime_queue_lag(+0.00%) -> 10:32:24 scalping_scanner_watch_eviction:stale_recovery_failed(+0.00%) -> 10:33:05 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%)|
|마키나락스(477850)|10:31:52|10:34:42|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/insufficient_history|source_freshness_blocker|5|0|diagnostic_quote_age_stale|63485.0|-|50/|0|10:31:52 scalping_scanner_candidate_promoted(+0.00%) -> 10:31:52 scalping_scanner_runtime_target_attach(+0.00%) -> 10:32:10 scalping_scanner_promotion_latency_trace(+0.00%) -> 10:32:10 scalping_scanner_fast_precheck(+0.00%) -> ... -> 10:34:04 scalping_scanner_runtime_queue_lag(+0.00%) -> 10:34:04 scalping_scanner_watch_eviction:stale_recovery_failed(+0.00%) -> 10:34:42 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%)|
|매드업(000390)|10:31:52|10:31:53|flat_or_falling|0.00%|0.00%|`scalping_scanner_runtime_target_attach`/scanner_identity_name_mismatch|non_actionable_guard_or_backpressure|0|0|-||-||0|10:31:52 scalping_scanner_candidate_promoted(+0.00%) -> 10:31:53 scalping_scanner_runtime_target_attach(+0.00%)|
|엘티씨(170920)|10:31:52|10:34:42|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/insufficient_history|source_freshness_blocker|5|0|diagnostic_quote_age_stale|63387.0|-|50/|0|10:31:52 scalping_scanner_candidate_promoted(+0.00%) -> 10:31:53 scalping_scanner_runtime_target_attach(+0.00%) -> 10:32:10 scalping_scanner_promotion_latency_trace(+0.00%) -> 10:32:10 scalping_scanner_fast_precheck(+0.00%) -> ... -> 10:34:04 scalping_scanner_runtime_queue_lag(+0.00%) -> 10:34:04 scalping_scanner_watch_eviction:stale_recovery_failed(+0.00%) -> 10:34:42 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%)|
|한국금융지주(071050)|10:31:52|10:39:18|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/insufficient_history|source_freshness_blocker|15|4|diagnostic_quote_age_stale|71679.0|-|50/|0|10:31:52 scalping_scanner_candidate_promoted(+0.00%) -> 10:31:53 scalping_scanner_runtime_target_attach(+0.00%) -> 10:32:02 condition_unmatch_guard -> 10:32:10 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 10:39:18 scalping_scanner_fast_precheck(+0.00%) -> 10:39:18 scalping_scanner_runtime_queue_lag(+0.00%) -> 10:39:18 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%)|
|대원전선(006340)|10:33:23|10:39:33|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|non_actionable_guard_or_backpressure|14|4|diagnostic_quote_age_stale|71610.0|-|50/|0|10:33:23 scalping_scanner_candidate_promoted(+0.00%) -> 10:33:23 scalping_scanner_runtime_target_attach(+0.00%) -> 10:33:29 scalping_scanner_promotion_latency_trace(+0.00%) -> 10:33:29 scalping_scanner_fast_precheck(+0.00%) -> ... -> 10:39:27 scalping_scanner_heavy_eval_lag(+0.00%) -> 10:39:33 strength_momentum_observed:insufficient_history(+0.00%) -> 10:39:33 strength_momentum_stability_recheck_pending:insufficient_history(+0.00%)|
|SK하이닉스(000660)|10:33:23|10:38:59|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/insufficient_history|source_freshness_blocker|15|0|diagnostic_quote_age_stale|49003.0|-|50/|0|10:33:23 scalping_scanner_candidate_promoted(+0.00%) -> 10:33:23 scalping_scanner_runtime_target_attach(+0.00%) -> 10:33:29 scalping_scanner_promotion_latency_trace(+0.00%) -> 10:33:29 scalping_scanner_fast_precheck(+0.00%) -> ... -> 10:38:57 scalping_scanner_heavy_eval_lag(+0.00%) -> 10:38:59 strength_momentum_observed:insufficient_history(+0.00%) -> 10:38:59 blocked_strength_momentum:insufficient_history(+0.00%)|
|대웅제약(069620)|10:33:23|10:39:42|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|non_actionable_guard_or_backpressure|11|3|diagnostic_quote_age_stale|80318.0|-|50/|0|10:33:23 scalping_scanner_candidate_promoted(+0.00%) -> 10:33:23 scalping_scanner_runtime_target_attach(+0.00%) -> 10:33:29 scalping_scanner_promotion_latency_trace(+0.00%) -> 10:33:29 scalping_scanner_fast_precheck(+0.00%) -> ... -> 10:39:39 strength_momentum_observed:below_window_buy_value(+0.00%) -> 10:39:42 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 10:39:42 blocked_liquidity(+0.00%)|
|티엘비(356860)|10:33:23|10:35:19|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|non_actionable_guard_or_backpressure|3|0|ws_snapshot_missing_or_zero|4657.0|-||0|10:33:23 scalping_scanner_candidate_promoted(+0.00%) -> 10:33:23 scalping_scanner_runtime_target_attach(+0.00%) -> 10:33:56 scalping_scanner_watching_runtime_skip:ws_snapshot_missing_or_zero(+0.00%) -> 10:35:19 scalping_scanner_promotion_latency_trace(+0.00%) -> 10:35:19 scalping_scanner_fast_precheck(+0.00%) -> 10:35:19 scalping_scanner_runtime_queue_lag(+0.00%) -> 10:35:19 scalping_scanner_watch_eviction:stale_recovery_failed(+0.00%) -> 10:35:19 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%)|
|KBI메탈(024840)|10:34:54|10:37:19|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/insufficient_history|source_freshness_blocker|4|0|diagnostic_quote_age_stale|58812.0|-|50/|0|10:34:54 scalping_scanner_candidate_promoted(+0.00%) -> 10:34:54 scalping_scanner_runtime_target_attach(+0.00%) -> 10:34:59 scalping_scanner_promotion_latency_trace(+0.00%) -> 10:34:59 scalping_scanner_fast_precheck(+0.00%) -> ... -> 10:36:37 scalping_scanner_runtime_queue_lag(+0.00%) -> 10:36:37 scalping_scanner_watch_eviction:stale_recovery_failed(+0.00%) -> 10:37:19 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%)|
|HPSP(403870)|10:34:54|10:39:18|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|non_actionable_guard_or_backpressure|7|8|diagnostic_quote_age_stale|52575.0|10:36:47|58/WAIT|0|10:34:54 scalping_scanner_candidate_promoted(+0.00%) -> 10:34:54 scalping_scanner_runtime_target_attach(+0.00%) -> 10:34:59 scalping_scanner_promotion_latency_trace(+0.00%) -> 10:34:59 scalping_scanner_fast_precheck(+0.00%) -> ... -> 10:39:18 scalping_scanner_fast_precheck(+0.00%) -> 10:39:18 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%) -> 10:39:18 scalping_scanner_watching_runtime_skip:scanner_full_eval_loop_budget_deferred(+0.00%)|
|이수화학(005950)|10:36:24|10:39:18|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|non_actionable_guard_or_backpressure|4|2|diagnostic_quote_age_stale|77762.0|-|50/|0|10:36:24 scalping_scanner_candidate_promoted(+0.00%) -> 10:36:24 scalping_scanner_runtime_target_attach(+0.00%) -> 10:36:37 scalping_scanner_promotion_latency_trace(+0.00%) -> 10:36:37 scalping_scanner_fast_precheck(+0.00%) -> ... -> 10:39:18 scalping_scanner_fast_precheck(+0.00%) -> 10:39:18 scalping_scanner_runtime_queue_lag(+0.00%) -> 10:39:18 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%)|
|삼천당제약(000250)|10:36:24|10:39:18|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|non_actionable_guard_or_backpressure|5|3|diagnostic_quote_age_stale|78324.0|-|50/|0|10:36:24 scalping_scanner_candidate_promoted(+0.00%) -> 10:36:24 scalping_scanner_runtime_target_attach(+0.00%) -> 10:36:37 scalping_scanner_promotion_latency_trace(+0.00%) -> 10:36:37 scalping_scanner_fast_precheck(+0.00%) -> ... -> 10:39:18 scalping_scanner_fast_precheck(+0.00%) -> 10:39:18 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%) -> 10:39:18 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%)|
|노타(486990)|10:29:33|10:39:19|unknown|||`scalping_scanner_runtime_target_attach`/operator_manual_control_excluded_symbol|non_actionable_guard_or_backpressure|0|0|-||-||0|10:29:33 scalping_scanner_runtime_target_attach|
|비에이치(090460)|10:29:33|10:39:19|unknown|||`scalping_scanner_runtime_target_attach`/operator_manual_control_excluded_symbol|non_actionable_guard_or_backpressure|0|0|-||-||0|10:29:33 scalping_scanner_runtime_target_attach|
|LS ELECTRIC(010120)|10:29:33|10:39:19|unknown|||`scalping_scanner_runtime_target_attach`/operator_manual_control_excluded_symbol|non_actionable_guard_or_backpressure|0|0|-||-||0|10:29:33 scalping_scanner_runtime_target_attach|
|포스코엠텍(009520)|10:29:33|10:39:19|unknown|||`scalping_scanner_runtime_target_attach`/operator_manual_control_excluded_symbol|non_actionable_guard_or_backpressure|0|0|-||-||0|10:29:33 scalping_scanner_runtime_target_attach|
|한화오션(042660)|10:29:33|10:39:19|unknown|||`scalping_scanner_runtime_target_attach`/operator_manual_control_excluded_symbol|non_actionable_guard_or_backpressure|0|0|-||-||0|10:29:33 scalping_scanner_runtime_target_attach|
|삼성전자(005930)|10:29:33|10:39:19|unknown|||`scalping_scanner_runtime_target_attach`/operator_manual_control_excluded_symbol|non_actionable_guard_or_backpressure|0|0|-||-||0|10:29:33 scalping_scanner_runtime_target_attach|
|삼표시멘트(038500)|10:29:33|10:39:19|unknown|||`scalping_scanner_runtime_target_attach`/-|-|0|0|-||-||0|10:29:33 scalping_scanner_runtime_target_attach|
|셀트리온(068270)|10:31:52|10:34:54|unknown|||`scalping_scanner_candidate_observed`/-|-|0|0|-||-||0|10:31:52 scalping_scanner_candidate_observed -> 10:31:52 scalping_scanner_real_source_guard_block -> 10:33:23 scalping_scanner_candidate_observed -> 10:33:23 scalping_scanner_real_source_guard_block -> 10:34:54 scalping_scanner_candidate_observed -> 10:34:54 scalping_scanner_real_source_guard_block|
|LG에너지솔루션(373220)|10:31:52|10:34:54|unknown|||`scalping_scanner_candidate_observed`/-|-|0|0|-||-||0|10:31:52 scalping_scanner_candidate_observed -> 10:31:52 scalping_scanner_real_source_guard_block -> 10:33:23 scalping_scanner_candidate_observed -> 10:33:23 scalping_scanner_real_source_guard_block -> 10:34:54 scalping_scanner_candidate_observed -> 10:34:54 scalping_scanner_real_source_guard_block|

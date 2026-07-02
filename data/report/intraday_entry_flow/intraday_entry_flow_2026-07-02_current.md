# 2026-07-02 18:00 이후 감시대상 BUY 전 흐름

- generated_at: 2026-07-02T18:35:00+09:00
- source_events: /home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-02.jsonl
- source_diagnostic: /home/ubuntu/KORStockScan/data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-07-02.json
- event_window_since: 2026-07-02T18:00:00+09:00
- event_window_until: None
- symbol_count: 26
- rising_symbol_count_by_max_delta: 4
- rising_missed_buy_count_in_latest_diagnostic: 3
- rising_missed_symbol_count_in_report: 3
- rising_missed_residual_excluding_forced_scout_symbol_count: 0
- rising_missed_forced_scout_event_count: 61
- rising_missed_forced_scout_symbol_count: 4
- rising_missed_forced_scout_residual_symbol_count: 3
- real_submit_symbol_count_in_latest_diagnostic: 0
- buy_signal_or_pre_submit_pass_seen_symbols: 8
- stale_eval_symbol_count: 22
- rising_stale_eval_symbol_count: 4
- rising_fresh_only_symbol_count: 0
- stale_refresh_recovered_symbol_count: 12

## forced scout observation

- event_count: 61
- symbol_count: 4
- symbols: 018260, 094360, 378340, 486990
- rising_missed_residual_symbols: 094360, 378340, 486990
- rising_missed_residual_excluding_forced_scout_symbols: -
- decision_authority: source_quality_only
- runtime_effect: False

## blocker rollup

- 15: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 2: `blocked_strength_momentum` / `below_strength_base`
- 2: `scalping_scanner_watching_runtime_skip` / `entry_cooldown_active`
- 2: `scalping_scanner_watching_runtime_skip` / `ws_snapshot_missing_or_zero`
- 2: `scalping_scanner_runtime_target_attach` / `-`
- 2: `scalping_scanner_candidate_observed` / `-`
- 1: `latency_block` / `latency_state_danger`

## blocker taxonomy

- 95: `strategy_reject`
- 25: `runtime_backpressure`
- 16: `source_freshness_evictable`
- 15: `pre_submit_quality_guard`
- 6: `intended_guard`
- 6: `watch_budget_reallocated`
- 2: `source_freshness_recovering`
- 1: `source_freshness_blocker`

## suppressed non-major blocker counts

- 25: `runtime_backpressure` / `scalping_scanner_watching_runtime_skip` / `scanner_full_eval_loop_budget_deferred`
- 16: `source_freshness_evictable` / `scalping_scanner_watching_runtime_skip` / `ws_snapshot_missing_or_zero`
- 15: `pre_submit_quality_guard` / `latency_block` / `latency_state_danger`
- 3: `intended_guard` / `scalping_scanner_watching_runtime_skip` / `entry_cooldown_active`
- 3: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `scanner_hardgate_prefilter`
- 2: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `stale_recovery_failed`
- 2: `source_freshness_recovering` / `scalping_scanner_watching_runtime_skip` / `ws_snapshot_missing_or_zero`
- 1: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `safety_cooldown_pool_blocked`

## rising-symbol blocker rollup

- 2: `scalping_scanner_watching_runtime_skip` / `entry_cooldown_active`
- 1: `latency_block` / `latency_state_danger`
- 1: `blocked_strength_momentum` / `below_strength_base`

## rising fresh-only blocker rollup


## rising stale-mixed blocker rollup

- 2: `scalping_scanner_watching_runtime_skip` / `entry_cooldown_active`
- 1: `latency_block` / `latency_state_danger`
- 1: `blocked_strength_momentum` / `below_strength_base`

## stale-eval rollup

- 18: `scalping_scanner_fast_precheck`
- 3: `scalping_scanner_watching_runtime_skip`
- 1: `blocked_overbought`

## stale-eval category rollup

- 19: `diagnostic_quote_age_stale`
- 3: `ws_snapshot_missing_or_zero`

## bounded freshness recheck workorders

|종목|건수|diagnostic stale|history gap|latest|next action|authority|runtime|
|---|---:|---:|---:|---|---|---|---|
|칩스앤미디어(094360)|37|36|1|scalping_scanner_watching_runtime_skip:entry_cooldown_active|add_or_tune_bounded_fresh_recheck_enqueue_after_stale_or_history_gap|source_quality_only|effect=False,apply=False|
|필에너지(378340)|35|35|0|scalping_scanner_watching_runtime_skip:entry_cooldown_active|add_or_tune_bounded_fresh_recheck_enqueue_after_stale_or_history_gap|source_quality_only|effect=False,apply=False|
|노타(486990)|12|10|2|latency_block:latency_state_danger|add_or_tune_bounded_fresh_recheck_enqueue_after_stale_or_history_gap|source_quality_only|effect=False,apply=False|

## latency danger root cause

|종목|건수|top cause|spread ratio med/max|ws age med/max|spread ticks med/max|micro|bucket|
|---|---:|---|---:|---:|---:|---|---|
|필에너지(378340)|16|quote_stale|0.010749/0.014683|12866.5/21183.0|14.0/19.0|insufficient|spread=wide\|price=mid\|depth=thin\|sample=insufficient|
|노타(486990)|12|quote_stale|0.011628/0.016204|15290.0/20387.0|5.0/7.0|insufficient|spread=wide\|price=mid\|depth=normal\|sample=insufficient|

## top rows by max delta

|종목|첫감시|마지막|상승여부|maxΔ|latestΔ|BUY전 주 blocker|class|stale평가|refresh회복|stale유형|max quote age|BUY전 통과신호|AI|실제submit|흐름|
|---|---:|---:|---|---:|---:|---|---|---:|---:|---|---:|---:|---:|---:|---|
|필에너지(378340)|18:00:04|18:34:45|rising|6.45%|6.45%|`latency_block`/latency_state_danger|non_actionable_guard_or_backpressure|48|7|diagnostic_quote_age_stale|125810.0|18:00:18|0/not_evaluated|0|18:00:04 scalping_scanner_promotion_latency_trace(+6.45%) -> 18:00:04 scalping_scanner_fast_precheck(+6.45%) -> 18:00:04 scalping_scanner_runtime_queue_lag(+6.45%) -> 18:00:04 scalping_scanner_promotion_latency_trace(+6.45%) -> ... -> 18:34:41 scalping_scanner_promotion_latency_trace(+6.45%) -> 18:34:41 scalping_scanner_heavy_eval_lag(+6.45%) -> 18:34:45 scalping_scanner_watching_runtime_skip:entry_cooldown_active(+6.45%)|
|노타(486990)|18:00:56|18:34:38|rising|3.48%|3.48%|`blocked_strength_momentum`/below_strength_base|strategy_reject|42|10|diagnostic_quote_age_stale|75120.0|18:01:07|70/not_evaluated|0|18:00:56 rising_missed_scout_upgrade_eval(+3.48%) -> 18:01:04 strength_momentum_observed:below_strength_base(+3.48%) -> 18:01:07 strength_momentum_scanner_rising_override(+3.48%) -> 18:01:07 dynamic_vpw_override_pass(+3.48%) -> ... -> 18:34:38 scalping_scanner_promotion_latency_trace(+3.48%) -> 18:34:38 scalping_scanner_fast_precheck(+3.48%) -> 18:34:38 scalping_scanner_runtime_queue_lag(+3.48%)|
|칩스앤미디어(094360)|18:00:00|18:35:02|rising|2.20%|2.20%|`scalping_scanner_watching_runtime_skip`/entry_cooldown_active|intended_guard|10|67|diagnostic_quote_age_stale|16819.0|18:02:18|58/WAIT|0|18:00:00 scalping_scanner_watching_runtime_skip:entry_cooldown_active(+2.20%) -> 18:01:17 rising_missed_scout_upgrade_eval(+2.20%) -> 18:01:20 blocked_overbought(+2.20%) -> 18:01:20 strength_momentum_observed:insufficient_history(+2.20%) -> ... -> 18:34:05 rising_missed_scout_upgrade_eval(+2.20%) -> 18:34:12 scalping_scanner_watching_runtime_skip:entry_cooldown_active(+2.20%) -> 18:34:30 rising_missed_scout_upgrade_eval(+2.20%)|
|LG에너지솔루션(373220)|18:00:04|18:00:42|rising|0.85%|0.85%|`scalping_scanner_watching_runtime_skip`/entry_cooldown_active|non_actionable_guard_or_backpressure|1|0|diagnostic_quote_age_stale|11893.0|-||0|18:00:04 scalping_scanner_promotion_latency_trace(+0.85%) -> 18:00:04 scalping_scanner_fast_precheck(+0.85%) -> 18:00:04 scalping_scanner_runtime_queue_lag(+0.85%) -> 18:00:04 scalping_scanner_promotion_latency_trace(+0.85%) -> ... -> 18:00:33 scalping_scanner_watching_runtime_skip:entry_cooldown_active(+0.85%) -> 18:00:42 scalping_scanner_watch_eviction:safety_cooldown_pool_blocked(+0.85%) -> 18:00:42 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.85%)|
|POSCO홀딩스(005490)|18:00:04|18:20:31|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|35|24|diagnostic_quote_age_stale|74714.0|18:01:39|60/WAIT|0|18:00:04 scalping_scanner_promotion_latency_trace(+0.00%) -> 18:00:04 scalping_scanner_fast_precheck(+0.00%) -> 18:00:04 scalping_scanner_runtime_queue_lag(+0.00%) -> 18:00:42 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%) -> ... -> 18:20:21 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 18:20:31 scalping_scanner_watch_eviction:scanner_hardgate_prefilter(+0.00%) -> 18:20:31 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%)|
|신한지주(055550)|18:00:04|18:34:38|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|56|6|diagnostic_quote_age_stale|100873.0|-|62/|0|18:00:04 scalping_scanner_promotion_latency_trace(+0.00%) -> 18:00:04 scalping_scanner_fast_precheck(+0.00%) -> 18:00:04 scalping_scanner_runtime_queue_lag(+0.00%) -> 18:00:04 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 18:34:38 scalping_scanner_promotion_latency_trace(+0.00%) -> 18:34:38 scalping_scanner_fast_precheck(+0.00%) -> 18:34:38 scalping_scanner_runtime_queue_lag(+0.00%)|
|제이에스코퍼레이션(194370)|18:00:04|18:34:53|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|53|7|diagnostic_quote_age_stale|239092.0|18:28:06|62/WAIT|0|18:00:04 scalping_scanner_promotion_latency_trace(+0.00%) -> 18:00:04 scalping_scanner_fast_precheck(+0.00%) -> 18:00:04 scalping_scanner_runtime_queue_lag(+0.00%) -> 18:01:10 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 18:34:49 strength_momentum_observed:insufficient_history(+0.00%) -> 18:34:49 strength_momentum_stability_recheck_pending:insufficient_history(+0.00%) -> 18:34:53 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%)|
|큐리오시스(494120)|18:00:04|18:34:38|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|49|0|diagnostic_quote_age_stale|145029.0|-||0|18:00:04 scalping_scanner_promotion_latency_trace(+0.00%) -> 18:00:04 scalping_scanner_fast_precheck(+0.00%) -> 18:00:04 scalping_scanner_runtime_queue_lag(+0.00%) -> 18:01:10 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 18:34:38 scalping_scanner_promotion_latency_trace(+0.00%) -> 18:34:38 scalping_scanner_fast_precheck(+0.00%) -> 18:34:38 scalping_scanner_runtime_queue_lag(+0.00%)|
|SBS(034120)|18:00:04|18:34:38|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|48|0|diagnostic_quote_age_stale|616842.0|-||0|18:00:04 scalping_scanner_promotion_latency_trace(+0.00%) -> 18:00:04 scalping_scanner_fast_precheck(+0.00%) -> 18:00:04 scalping_scanner_runtime_queue_lag(+0.00%) -> 18:01:10 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 18:34:38 scalping_scanner_promotion_latency_trace(+0.00%) -> 18:34:38 scalping_scanner_fast_precheck(+0.00%) -> 18:34:38 scalping_scanner_runtime_queue_lag(+0.00%)|
|영원무역(111770)|18:00:04|18:34:38|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|51|0|diagnostic_quote_age_stale|179245.0|-||0|18:00:04 scalping_scanner_promotion_latency_trace(+0.00%) -> 18:00:04 scalping_scanner_fast_precheck(+0.00%) -> 18:00:04 scalping_scanner_runtime_queue_lag(+0.00%) -> 18:00:04 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 18:34:38 scalping_scanner_promotion_latency_trace(+0.00%) -> 18:34:38 scalping_scanner_fast_precheck(+0.00%) -> 18:34:38 scalping_scanner_runtime_queue_lag(+0.00%)|
|카카오뱅크(323410)|18:00:42|18:34:53|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|54|0|diagnostic_quote_age_stale|74172.0|-|50/|0|18:00:42 scalping_scanner_promotion_latency_trace(+0.00%) -> 18:00:42 scalping_scanner_fast_precheck(+0.00%) -> 18:00:42 scalping_scanner_runtime_queue_lag(+0.00%) -> 18:00:42 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%) -> ... -> 18:34:53 scalping_scanner_fast_precheck(+0.00%) -> 18:34:53 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%) -> 18:34:53 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%)|
|HMM(011200)|18:00:42|18:34:53|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|55|4|diagnostic_quote_age_stale|86027.0|-|62/|0|18:00:42 scalping_scanner_promotion_latency_trace(+0.00%) -> 18:00:42 scalping_scanner_fast_precheck(+0.00%) -> 18:00:42 scalping_scanner_runtime_queue_lag(+0.00%) -> 18:00:42 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 18:34:53 scalping_scanner_fast_precheck(+0.00%) -> 18:34:53 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%) -> 18:34:53 scalping_scanner_watching_runtime_skip:scanner_full_eval_loop_budget_deferred(+0.00%)|
|NAVER(035420)|18:00:42|18:34:53|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|55|23|diagnostic_quote_age_stale|74074.0|18:15:50|60/WAIT|0|18:00:42 scalping_scanner_promotion_latency_trace(+0.00%) -> 18:00:42 scalping_scanner_fast_precheck(+0.00%) -> 18:00:42 scalping_scanner_runtime_queue_lag(+0.00%) -> 18:00:42 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 18:34:53 scalping_scanner_fast_precheck(+0.00%) -> 18:34:53 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%) -> 18:34:53 scalping_scanner_watching_runtime_skip:scanner_full_eval_loop_budget_deferred(+0.00%)|
|엔켐(348370)|18:00:42|18:34:38|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|58|8|diagnostic_quote_age_stale|111060.0|18:23:33|62/WAIT|0|18:00:42 scalping_scanner_promotion_latency_trace(+0.00%) -> 18:00:42 scalping_scanner_fast_precheck(+0.00%) -> 18:00:42 scalping_scanner_runtime_queue_lag(+0.00%) -> 18:00:42 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%) -> ... -> 18:34:38 scalping_scanner_promotion_latency_trace(+0.00%) -> 18:34:38 scalping_scanner_fast_precheck(+0.00%) -> 18:34:38 scalping_scanner_runtime_queue_lag(+0.00%)|
|한국전력(015760)|18:00:42|18:34:53|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|62|26|diagnostic_quote_age_stale|74069.0|18:02:53|74/WAIT|0|18:00:42 scalping_scanner_promotion_latency_trace(+0.00%) -> 18:00:42 scalping_scanner_fast_precheck(+0.00%) -> 18:00:42 scalping_scanner_runtime_queue_lag(+0.00%) -> 18:00:42 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 18:34:53 scalping_scanner_fast_precheck(+0.00%) -> 18:34:53 scalping_scanner_runtime_queue_lag(+0.00%) -> 18:34:53 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%)|
|동양생명(082640)|18:00:42|18:34:22|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|non_actionable_guard_or_backpressure|37|0|ws_snapshot_missing_or_zero||-||0|18:00:42 scalping_scanner_watching_runtime_skip:ws_snapshot_missing_or_zero(+0.00%)|
|오성첨단소재(052420)|18:00:42|18:34:22|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|non_actionable_guard_or_backpressure|37|0|ws_snapshot_missing_or_zero||-||0|18:00:42 scalping_scanner_watching_runtime_skip:ws_snapshot_missing_or_zero(+0.00%)|
|한국타이어앤테크놀로지(161390)|18:00:44|18:04:02|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|3|0|diagnostic_quote_age_stale|89579.0|-||0|18:00:44 scalping_scanner_candidate_promoted(+0.00%) -> 18:00:44 scalping_scanner_runtime_target_attach(+0.00%) -> 18:01:24 scalping_scanner_promotion_latency_trace(+0.00%) -> 18:01:24 scalping_scanner_fast_precheck(+0.00%) -> ... -> 18:03:37 scalping_scanner_runtime_queue_lag(+0.00%) -> 18:03:37 scalping_scanner_watch_eviction:stale_recovery_failed(+0.00%) -> 18:04:02 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%)|
|삼성에스디에스(018260)|18:03:45|18:34:53|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|12|8|diagnostic_quote_age_stale|30423.0|-|50/|0|18:03:45 scalping_scanner_candidate_promoted(+0.00%) -> 18:03:45 scalping_scanner_runtime_target_attach(+0.00%) -> 18:04:30 scalping_scanner_promotion_latency_trace(+0.00%) -> 18:04:30 scalping_scanner_fast_precheck(+0.00%) -> ... -> 18:34:53 scalping_scanner_fast_precheck(+0.00%) -> 18:34:53 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%) -> 18:34:53 scalping_scanner_watching_runtime_skip:scanner_full_eval_loop_budget_deferred(+0.00%)|
|호텔신라(008770)|18:21:50|18:24:10|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|3|0|diagnostic_quote_age_stale|39803.0|-||0|18:21:50 scalping_scanner_candidate_promoted(+0.00%) -> 18:21:50 scalping_scanner_runtime_target_attach(+0.00%) -> 18:22:30 scalping_scanner_promotion_latency_trace(+0.00%) -> 18:22:30 scalping_scanner_fast_precheck(+0.00%) -> ... -> 18:23:58 scalping_scanner_runtime_queue_lag(+0.00%) -> 18:23:58 scalping_scanner_watch_eviction:stale_recovery_failed(+0.00%) -> 18:24:10 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%)|
|포스코엠텍(009520)|18:24:51|18:27:35|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_strength_base|strategy_reject|2|2|ws_snapshot_missing_or_zero|8630.0|-|50/|0|18:24:51 scalping_scanner_candidate_promoted(+0.00%) -> 18:24:51 scalping_scanner_runtime_target_attach(+0.00%) -> 18:25:36 scalping_scanner_watching_runtime_skip:ws_snapshot_missing_or_zero(+0.00%) -> 18:26:40 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 18:26:47 blocked_strength_momentum:below_strength_base(+0.00%) -> 18:26:53 scalping_scanner_watch_eviction:scanner_hardgate_prefilter(+0.00%) -> 18:27:35 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%)|
|한국콜마(161890)|18:33:54|18:34:53|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|3|0|diagnostic_quote_age_stale|25811.0|-|50/|0|18:33:54 scalping_scanner_candidate_promoted(+0.00%) -> 18:33:54 scalping_scanner_runtime_target_attach(+0.00%) -> 18:34:22 scalping_scanner_promotion_latency_trace(+0.00%) -> 18:34:22 scalping_scanner_fast_precheck(+0.00%) -> ... -> 18:34:41 strength_momentum_observed:below_window_buy_value(+0.00%) -> 18:34:41 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 18:34:53 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%)|
|삼성전자(005930)|18:00:43|18:34:54|unknown|||`scalping_scanner_runtime_target_attach`/-|-|0|0|-||-||0|18:00:43 scalping_scanner_runtime_target_attach|
|삼표시멘트(038500)|18:00:43|18:34:54|unknown|||`scalping_scanner_runtime_target_attach`/-|-|0|0|-||-||0|18:00:43 scalping_scanner_runtime_target_attach|
|에이피알(278470)|18:00:44|18:00:44|unknown|||`scalping_scanner_candidate_observed`/-|-|0|0|-||-||0|18:00:44 scalping_scanner_candidate_observed -> 18:00:44 scalping_scanner_real_source_guard_block|
|현대차(005380)|18:00:44|18:00:44|unknown|||`scalping_scanner_candidate_observed`/-|-|0|0|-||-||0|18:00:44 scalping_scanner_candidate_observed -> 18:00:44 scalping_scanner_real_source_guard_block|

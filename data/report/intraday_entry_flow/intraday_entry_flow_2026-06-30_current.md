# 2026-06-30 16:00 이후 감시대상 BUY 전 흐름

- generated_at: 2026-06-30T19:22:49
- source_events: /home/ubuntu/KORStockScan/data/runtime/sentinel_event_cache/buy_funnel_sentinel_events_2026-06-30.jsonl
- source_diagnostic: data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-30_1600_1900_goal.json
- event_window_since: 2026-06-30T16:00:00
- event_window_until: 2026-06-30T19:00:00
- symbol_count: 15
- rising_symbol_count_by_max_delta: 1
- rising_missed_buy_count_in_latest_diagnostic: 7
- rising_missed_symbol_count_in_report: 0
- rising_missed_residual_excluding_forced_scout_symbol_count: 7
- rising_missed_forced_scout_event_count: 0
- rising_missed_forced_scout_symbol_count: 0
- rising_missed_forced_scout_residual_symbol_count: 0
- real_submit_symbol_count_in_latest_diagnostic: 0
- buy_signal_or_pre_submit_pass_seen_symbols: 0
- stale_eval_symbol_count: 0
- rising_stale_eval_symbol_count: 0
- rising_fresh_only_symbol_count: 1
- stale_refresh_recovered_symbol_count: 0

## forced scout observation

- event_count: 0
- symbol_count: 0
- symbols: -
- rising_missed_residual_symbols: -
- rising_missed_residual_excluding_forced_scout_symbols: 000660, 002990, 010120, 025320, 034730, 281820, 319400
- decision_authority: source_quality_only
- runtime_effect: False

## blocker rollup

- 14: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 1: `blocked_strength_momentum` / `below_strength_base`

## blocker taxonomy

- 144: `strategy_reject`
- 37: `source_freshness_evictable`
- 29: `watch_budget_reallocated`
- 23: `pre_submit_quality_guard`
- 9: `source_freshness_recovering`
- 5: `intended_guard`
- 1: `runtime_backpressure`

## suppressed non-major blocker counts

- 37: `source_freshness_evictable` / `scalping_scanner_watching_runtime_skip` / `ws_snapshot_missing_or_zero`
- 23: `pre_submit_quality_guard` / `latency_block` / `latency_state_danger`
- 22: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `stale_recovery_failed`
- 9: `source_freshness_recovering` / `scalping_scanner_watching_runtime_skip` / `ws_snapshot_missing_or_zero`
- 5: `intended_guard` / `scalping_scanner_watching_runtime_skip` / `entry_cooldown_active`
- 4: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `scanner_hardgate_prefilter`
- 2: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `source_quality_unresolved`
- 1: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `safety_cooldown_pool_blocked`
- 1: `runtime_backpressure` / `scalping_scanner_watching_runtime_skip` / `scanner_full_eval_loop_budget_deferred`

## rising-symbol blocker rollup

- 1: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`

## rising fresh-only blocker rollup

- 1: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`

## rising stale-mixed blocker rollup


## stale-eval rollup


## stale-eval category rollup


## latency danger root cause

|종목|건수|top cause|spread ratio med/max|ws age med/max|spread ticks med/max|micro|bucket|
|---|---:|---|---:|---:|---:|---|---|
|LS ELECTRIC(010120)|68|spread_too_wide|0.010549/0.012712|355.0/21649.0|5.0/6.0|neutral|spread=wide\|price=high\|depth=thick\|sample=normal|
|시노펙스(025320)|67|quote_stale|0.008306/0.01|7577.0/24307.0|5.0/6.0|insufficient|spread=wide\|price=low\|depth=thick\|sample=insufficient|
|현대무벡스(319400)|28|quote_stale|0.009452/0.011364|1220.5/22227.0|5.0/6.0|insufficient|spread=wide\|price=mid\|depth=thick\|sample=insufficient|
|SK(034730)|17|quote_stale|0.006039/0.007273|1424.0/22808.0|5.0/6.0|insufficient|spread=wide\|price=high\|depth=thin\|sample=insufficient|

## top rows by max delta

|종목|첫감시|마지막|상승여부|maxΔ|latestΔ|BUY전 주 blocker|class|stale평가|refresh회복|stale유형|max quote age|BUY전 통과신호|AI|실제submit|흐름|
|---|---:|---:|---|---:|---:|---|---|---:|---:|---|---:|---:|---:|---:|---|
|KB금융(105560)|17:54:51|18:36:12|rising|0.19%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|위메이드(112040)|16:14:34|16:17:40|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|비나텍(126340)|16:26:38|18:59:56|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-|62/WAIT|0|-|
|큐리옥스바이오시스템즈(445680)|17:29:13|17:31:17|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|롯데렌탈(089860)|17:33:44|17:35:46|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|이수페타시스(007660)|17:36:45|18:59:56|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|케이씨(029460)|17:39:46|17:47:01|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-|62/WAIT|0|-|
|코세스(089890)|17:41:17|18:18:39|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|티엘비(356860)|17:41:17|17:44:29|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|카카오게임즈(293490)|17:47:18|17:48:48|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_strength_base|strategy_reject|0|0|-||-||0|-|
|큐리오시스(494120)|17:47:18|17:49:13|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|두산퓨얼셀(336260)|17:47:18|17:49:13|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|에이치브이엠(295310)|18:06:55|18:10:38|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|LG이노텍(011070)|18:17:28|18:26:18|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-|62/WAIT|0|-|
|피에스케이홀딩스(031980)|18:38:34|18:42:53|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|

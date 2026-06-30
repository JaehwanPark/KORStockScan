# 2026-06-30 11:00 이후 감시대상 BUY 전 흐름

- generated_at: 2026-06-30T11:20:00
- source_events: /home/ubuntu/KORStockScan/data/runtime/sentinel_event_cache/buy_funnel_sentinel_events_2026-06-30.jsonl
- source_diagnostic: data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-30_1120_1100_goal.json
- event_window_since: 2026-06-30T11:00:00
- event_window_until: 2026-06-30T11:20:00
- symbol_count: 9
- rising_symbol_count_by_max_delta: 4
- rising_missed_buy_count_in_latest_diagnostic: 8
- rising_missed_symbol_count_in_report: 4
- rising_missed_residual_excluding_forced_scout_symbol_count: 5
- rising_missed_forced_scout_event_count: 22
- rising_missed_forced_scout_symbol_count: 3
- rising_missed_forced_scout_residual_symbol_count: 3
- real_submit_symbol_count_in_latest_diagnostic: 0
- buy_signal_or_pre_submit_pass_seen_symbols: 0
- stale_eval_symbol_count: 5
- rising_stale_eval_symbol_count: 2
- rising_fresh_only_symbol_count: 2
- stale_refresh_recovered_symbol_count: 9

## forced scout observation

- event_count: 22
- symbol_count: 3
- symbols: 000500, 010120, 240810
- rising_missed_residual_symbols: 000500, 010120, 240810
- rising_missed_residual_excluding_forced_scout_symbols: 001820, 033100, 095610, 153890, 475150
- decision_authority: source_quality_only
- runtime_effect: False

## blocker rollup

- 2: `latency_block` / `latency_state_danger`
- 2: `blocked_ai_score` / `blocked_ai_score_below_buy_score_threshold`
- 2: `blocked_strength_momentum` / `below_window_buy_value`
- 1: `blocked_overbought` / `insufficient_history`
- 1: `blocked_strength_momentum` / `below_strength_base`
- 1: `blocked_gap_from_scan` / `blocked_ai_score_below_buy_score_threshold`

## blocker taxonomy

- 43: `runtime_backpressure`
- 34: `strategy_reject`
- 12: `intended_guard`
- 11: `pre_submit_quality_guard`
- 1: `watch_budget_reallocated`
- 1: `source_freshness_blocker`

## suppressed non-major blocker counts

- 43: `runtime_backpressure` / `scalping_scanner_watching_runtime_skip` / `scanner_full_eval_loop_budget_deferred`
- 4: `intended_guard` / `scalping_scanner_watching_runtime_skip` / `entry_cooldown_active`
- 1: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `scanner_hardgate_prefilter`

## rising-symbol blocker rollup

- 2: `latency_block` / `latency_state_danger`
- 2: `blocked_ai_score` / `blocked_ai_score_below_buy_score_threshold`

## rising fresh-only blocker rollup

- 2: `latency_block` / `latency_state_danger`

## rising stale-mixed blocker rollup

- 2: `blocked_ai_score` / `blocked_ai_score_below_buy_score_threshold`

## stale-eval rollup

- 3: `blocked_vpw`
- 1: `blocked_overbought`
- 1: `ai_confirmed`

## stale-eval category rollup

- 5: `diagnostic_quote_age_stale`

## top rows by max delta

|종목|첫감시|마지막|상승여부|maxΔ|latestΔ|BUY전 주 blocker|class|stale평가|refresh회복|stale유형|max quote age|BUY전 통과신호|AI|실제submit|흐름|
|---|---:|---:|---|---:|---:|---|---|---:|---:|---|---:|---:|---:|---:|---|
|가온전선(000500)|11:17:44|11:19:59|rising|20.44%|20.44%|`latency_block`/latency_state_danger|-|0|3|-||-|70/|0|11:17:44 latency_block:latency_state_danger(+20.44%)|
|삼화콘덴서(001820)|11:01:20|11:18:41|rising|2.57%|2.57%|`blocked_ai_score`/blocked_ai_score_below_buy_score_threshold|-|3|4|diagnostic_quote_age_stale|11094.0|-|76/WAIT|0|11:01:20 blocked_strength_momentum:below_window_buy_value(+2.57%) -> 11:01:44 blocked_ai_score(+2.57%) -> 11:01:44 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+2.57%) -> 11:05:31 blocked_strength_momentum:below_buy_ratio(+2.57%) -> ... -> 11:18:41 blocked_vpw(+2.57%) -> 11:18:41 blocked_ai_score(+2.57%) -> 11:18:41 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+2.57%)|
|테스(095610)|11:00:16|11:17:26|rising|1.24%|1.24%|`blocked_ai_score`/blocked_ai_score_below_buy_score_threshold|-|1|2|diagnostic_quote_age_stale|3406.0|-|70/WAIT|0|11:00:16 blocked_ai_score(+1.24%) -> 11:00:16 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+1.24%) -> 11:03:56 blocked_strength_momentum:below_buy_ratio(+1.24%) -> 11:03:56 blocked_vpw(+1.24%) -> ... -> 11:14:29 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+1.24%) -> 11:17:26 blocked_ai_score(+1.24%) -> 11:17:26 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+1.24%)|
|LS ELECTRIC(010120)|11:02:09|11:19:13|rising|1.07%|1.07%|`latency_block`/latency_state_danger|-|0|18|-||-|70/|0|11:02:09 latency_block:latency_state_danger(+1.07%)|
|저스템(417840)|11:00:51|11:00:51|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|-|0|1|-|73.0|-|50/|0|11:00:51 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|미래산업(025560)|11:01:30|11:10:25|flat_or_falling|0.00%|0.00%|`blocked_overbought`/insufficient_history|-|4|1|diagnostic_quote_age_stale|4851.0|-|50/|0|11:01:30 blocked_overbought(+0.00%) -> 11:01:30 blocked_strength_momentum:insufficient_history(+0.00%) -> 11:09:46 blocked_overbought(+0.00%) -> 11:10:25 blocked_strength_momentum:insufficient_history(+0.00%)|
|금호건설(002990)|11:05:12|11:18:10|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_strength_base|-|1|3|diagnostic_quote_age_stale|5184.0|-|50/|0|11:05:12 blocked_strength_momentum:below_strength_base(+0.00%) -> 11:05:12 blocked_vpw(+0.00%) -> 11:05:12 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%) -> 11:09:17 blocked_strength_momentum:below_strength_base(+0.00%) -> 11:18:10 blocked_vpw(+0.00%) -> 11:18:10 blocked_liquidity(+0.00%) -> 11:18:10 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%)|
|스피어(347700)|11:06:13|11:15:51|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|-|0|2|-|323.0|-|50/|0|11:06:13 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 11:15:51 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%)|
|주성엔지니어링(036930)|11:07:05|11:13:53|flat_or_falling|0.00%|0.00%|`blocked_gap_from_scan`/blocked_ai_score_below_buy_score_threshold|-|3|2|diagnostic_quote_age_stale|5220.0|-|68/BUY|0|11:07:05 blocked_strength_momentum:below_buy_ratio(+0.00%) -> 11:07:05 blocked_vpw(+0.00%) -> 11:07:05 blocked_gap_from_scan(+0.00%) -> 11:07:06 ai_confirmed(+0.00%) -> ... -> 11:13:51 wait65_79_ev_candidate(+0.00%) -> 11:13:53 blocked_ai_score(+0.00%) -> 11:13:53 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.00%)|

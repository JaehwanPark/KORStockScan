# 2026-06-30 11:00 이후 감시대상 BUY 전 흐름

- generated_at: 2026-06-30T12:20:00
- source_events: /home/ubuntu/KORStockScan/data/runtime/sentinel_event_cache/buy_funnel_sentinel_events_2026-06-30.jsonl
- source_diagnostic: data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-30_1220_1100_goal.json
- event_window_since: 2026-06-30T11:00:00
- event_window_until: 2026-06-30T12:20:00
- symbol_count: 14
- rising_symbol_count_by_max_delta: 9
- rising_missed_buy_count_in_latest_diagnostic: 10
- rising_missed_symbol_count_in_report: 9
- rising_missed_residual_excluding_forced_scout_symbol_count: 2
- rising_missed_forced_scout_event_count: 100
- rising_missed_forced_scout_symbol_count: 8
- rising_missed_forced_scout_residual_symbol_count: 8
- real_submit_symbol_count_in_latest_diagnostic: 0
- buy_signal_or_pre_submit_pass_seen_symbols: 1
- stale_eval_symbol_count: 11
- rising_stale_eval_symbol_count: 7
- rising_fresh_only_symbol_count: 2
- stale_refresh_recovered_symbol_count: 14

## forced scout observation

- event_count: 100
- symbol_count: 8
- symbols: 000500, 001820, 002990, 010120, 080220, 153890, 240810, 475150
- rising_missed_residual_symbols: 000500, 001820, 002990, 010120, 080220, 153890, 240810, 475150
- rising_missed_residual_excluding_forced_scout_symbols: 033100, 095610
- decision_authority: source_quality_only
- runtime_effect: False

## blocker rollup

- 3: `latency_block` / `latency_state_danger`
- 3: `blocked_strength_momentum` / `below_window_buy_value`
- 2: `ai_confirmed_terminal_no_budget` / `blocked_ai_score_below_buy_score_threshold`
- 1: `blocked_strength_momentum` / `below_strength_base`
- 1: `blocked_strength_momentum` / `blocked_ai_score_below_buy_score_threshold`
- 1: `blocked_ai_score` / `blocked_ai_score_below_buy_score_threshold`
- 1: `blocked_overbought` / `insufficient_history`
- 1: `blocked_strength_momentum` / `below_buy_ratio`
- 1: `blocked_strength_momentum` / `insufficient_history`

## blocker taxonomy

- 117: `runtime_backpressure`
- 67: `strategy_reject`
- 25: `intended_guard`
- 19: `pre_submit_quality_guard`
- 3: `watch_budget_reallocated`

## suppressed non-major blocker counts

- 117: `runtime_backpressure` / `scalping_scanner_watching_runtime_skip` / `scanner_full_eval_loop_budget_deferred`
- 10: `intended_guard` / `scalping_scanner_watching_runtime_skip` / `entry_cooldown_active`
- 2: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `scanner_hardgate_prefilter`
- 1: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `safety_cooldown_pool_blocked`

## rising-symbol blocker rollup

- 3: `latency_block` / `latency_state_danger`
- 2: `ai_confirmed_terminal_no_budget` / `blocked_ai_score_below_buy_score_threshold`
- 1: `blocked_strength_momentum` / `below_strength_base`
- 1: `blocked_strength_momentum` / `blocked_ai_score_below_buy_score_threshold`
- 1: `blocked_ai_score` / `blocked_ai_score_below_buy_score_threshold`
- 1: `blocked_strength_momentum` / `below_window_buy_value`

## rising fresh-only blocker rollup

- 2: `latency_block` / `latency_state_danger`

## rising stale-mixed blocker rollup

- 2: `ai_confirmed_terminal_no_budget` / `blocked_ai_score_below_buy_score_threshold`
- 1: `blocked_strength_momentum` / `below_strength_base`
- 1: `latency_block` / `latency_state_danger`
- 1: `blocked_strength_momentum` / `blocked_ai_score_below_buy_score_threshold`
- 1: `blocked_ai_score` / `blocked_ai_score_below_buy_score_threshold`
- 1: `blocked_strength_momentum` / `below_window_buy_value`

## stale-eval rollup

- 4: `blocked_vpw`
- 3: `ai_confirmed`
- 2: `ai_confirmed_terminal_no_budget`
- 1: `blocked_strength_momentum`
- 1: `blocked_overbought`

## stale-eval category rollup

- 11: `diagnostic_quote_age_stale`

## latency danger root cause

|종목|건수|top cause|spread ratio med/max|ws age med/max|spread ticks med/max|micro|bucket|
|---|---:|---|---:|---:|---:|---|---|
|제룡전기(033100)|38|latency_provenance_gap|-/-|-/-|-/-|-|diagnostic_latency_without_source_event_fields|
|LS ELECTRIC(010120)|31|spread_too_wide|0.010684/0.010776|88.0/569.0|5.0/5.0|neutral|spread=wide\|price=high\|depth=thick\|sample=rich|
|가온전선(000500)|30|spread_too_wide|0.011186/0.011312|173.5/10026.0|5.0/5.0|neutral|spread=wide\|price=high\|depth=normal\|sample=rich|
|SK이터닉스(475150)|23|spread_microstructure_wide|0.009597/0.011538|81.0/1282.0|5.0/6.0|neutral|spread=wide\|price=high\|depth=thick\|sample=rich|
|금호건설(002990)|6|spread_microstructure_wide|0.005918/0.009184|71.5/133.0|6.0/9.0|neutral|spread=wide\|price=low\|depth=thick\|sample=rich|

## top rows by max delta

|종목|첫감시|마지막|상승여부|maxΔ|latestΔ|BUY전 주 blocker|class|stale평가|refresh회복|stale유형|max quote age|BUY전 통과신호|AI|실제submit|흐름|
|---|---:|---:|---|---:|---:|---|---|---:|---:|---|---:|---:|---:|---:|---|
|가온전선(000500)|11:17:44|12:18:23|rising|20.44%|20.44%|`latency_block`/latency_state_danger|-|0|28|-||-|70/WAIT|0|11:17:44 latency_block:latency_state_danger(+20.44%) -> 11:52:05 blocked_ai_score(+20.44%) -> 11:52:05 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+20.44%) -> 11:55:34 blocked_ai_score(+20.44%) -> ... -> 12:15:10 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+20.44%) -> 12:18:23 blocked_ai_score(+20.44%) -> 12:18:23 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+20.44%)|
|금호건설(002990)|11:05:12|12:18:58|rising|7.00%|7.00%|`blocked_strength_momentum`/below_strength_base|-|8|9|diagnostic_quote_age_stale|5184.0|-|62/WAIT|0|11:05:12 blocked_strength_momentum:below_strength_base(+0.00%) -> 11:05:12 blocked_vpw(+0.00%) -> 11:05:12 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%) -> 11:09:17 blocked_strength_momentum:below_strength_base(+0.00%) -> ... -> 12:00:15 blocked_ai_score(+0.00%) -> 12:00:15 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.00%) -> 12:04:20 latency_block:latency_state_danger(+0.72%)|
|SK이터닉스(475150)|11:21:09|12:18:10|rising|4.06%|4.06%|`latency_block`/latency_state_danger|-|19|23|diagnostic_quote_age_stale|5460.0|-|73/WAIT|0|11:21:09 latency_block:latency_state_danger(+4.06%) -> 11:47:28 ai_confirmed(+4.06%) -> 11:47:28 wait65_79_ev_candidate(+4.06%) -> 11:47:28 first_ai_wait(+4.06%) -> ... -> 12:15:01 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+4.06%) -> 12:18:10 blocked_ai_score(+4.06%) -> 12:18:10 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+4.06%)|
|삼화콘덴서(001820)|11:01:20|12:17:57|rising|2.57%|2.57%|`blocked_strength_momentum`/blocked_ai_score_below_buy_score_threshold|-|12|16|diagnostic_quote_age_stale|29882.0|-|66/WAIT|0|11:01:20 blocked_strength_momentum:below_window_buy_value(+2.57%) -> 11:01:44 blocked_ai_score(+2.57%) -> 11:01:44 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+2.57%) -> 11:05:31 blocked_strength_momentum:below_buy_ratio(+2.57%) -> ... -> 12:14:56 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+2.57%) -> 12:17:57 blocked_ai_score(+2.57%) -> 12:17:57 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+2.57%)|
|져스텍(153890)|11:59:06|12:17:52|rising|2.49%|2.49%|`ai_confirmed_terminal_no_budget`/blocked_ai_score_below_buy_score_threshold|-|1|5|diagnostic_quote_age_stale|15127.0|-|64/WAIT|0|11:59:06 blocked_liquidity(+2.49%) -> 11:59:08 ai_confirmed(+2.49%) -> 11:59:10 first_ai_wait(+2.49%) -> 11:59:10 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+2.49%) -> ... -> 12:17:52 ai_confirmed(+2.49%) -> 12:17:52 blocked_ai_score(+2.49%) -> 12:17:52 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+2.49%)|
|테스(095610)|11:00:16|12:18:39|rising|1.24%|1.24%|`blocked_ai_score`/blocked_ai_score_below_buy_score_threshold|-|1|4|diagnostic_quote_age_stale|5354.0|-|67/WAIT|0|11:00:16 blocked_ai_score(+1.24%) -> 11:00:16 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+1.24%) -> 11:03:56 blocked_strength_momentum:below_buy_ratio(+1.24%) -> 11:03:56 blocked_vpw(+1.24%) -> ... -> 12:15:19 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+1.24%) -> 12:18:39 blocked_ai_score(+1.24%) -> 12:18:39 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+1.24%)|
|LS ELECTRIC(010120)|11:02:09|12:00:09|rising|1.07%|1.07%|`latency_block`/latency_state_danger|-|0|31|-||-|70/|0|11:02:09 latency_block:latency_state_danger(+1.07%)|
|제주반도체(080220)|12:04:35|12:19:26|rising|0.78%|0.78%|`blocked_strength_momentum`/below_window_buy_value|strategy_reject|10|2|diagnostic_quote_age_stale|5743.0|-|60/WAIT|0|12:06:51 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 12:06:51 blocked_vpw(+0.00%) -> 12:06:53 ai_confirmed(+0.00%) -> 12:06:53 first_ai_wait(+0.00%) -> ... -> 12:16:04 ai_confirmed(+0.00%) -> 12:16:04 blocked_ai_score(+0.00%) -> 12:16:04 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.00%)|
|원익IPS(240810)|11:29:00|12:18:47|rising|0.55%|0.55%|`ai_confirmed_terminal_no_budget`/blocked_ai_score_below_buy_score_threshold|-|26|13|diagnostic_quote_age_stale|19186.0|-|64/WAIT|0|11:29:00 blocked_strength_momentum:below_buy_ratio(+0.55%) -> 11:29:00 blocked_vpw(+0.55%) -> 11:29:01 ai_confirmed(+0.55%) -> 11:29:01 first_ai_wait(+0.55%) -> ... -> 12:18:47 blocked_vpw(+0.55%) -> 12:18:47 blocked_ai_score(+0.55%) -> 12:18:47 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.55%)|
|저스템(417840)|11:00:51|11:00:51|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|-|0|1|-|73.0|-|50/|0|11:00:51 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|미래산업(025560)|11:01:30|12:11:05|flat_or_falling|0.00%|0.00%|`blocked_overbought`/insufficient_history|-|6|3|diagnostic_quote_age_stale|4851.0|-|50/|0|11:01:30 blocked_overbought(+0.00%) -> 11:01:30 blocked_strength_momentum:insufficient_history(+0.00%) -> 11:09:46 blocked_overbought(+0.00%) -> 11:10:25 blocked_strength_momentum:insufficient_history(+0.00%) -> 12:08:16 blocked_overbought(+0.00%) -> 12:08:16 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 12:11:02 blocked_overbought(+0.00%) -> 12:11:05 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|스피어(347700)|11:06:13|12:19:12|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|-|1|9|diagnostic_quote_age_stale|5647.0|-|50/|0|11:06:13 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 11:15:51 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%) -> 11:20:10 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 11:20:10 blocked_vpw(+0.00%) -> ... -> 12:12:21 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 12:19:12 blocked_vpw(+0.00%) -> 12:19:12 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%)|
|주성엔지니어링(036930)|11:07:05|12:18:54|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_buy_ratio|-|13|6|diagnostic_quote_age_stale|5220.0|12:02:53|74/WAIT|0|11:07:05 blocked_strength_momentum:below_buy_ratio(+0.00%) -> 11:07:05 blocked_vpw(+0.00%) -> 11:07:05 blocked_gap_from_scan(+0.00%) -> 11:07:06 ai_confirmed(+0.00%) -> ... -> 12:18:54 blocked_vpw(+0.00%) -> 12:18:54 blocked_ai_score(+0.00%) -> 12:18:54 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.00%)|
|한울반도체(320000)|12:04:35|12:16:21|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/insufficient_history|source_freshness_blocker|3|3|diagnostic_quote_age_stale|6072.0|-|72/WAIT|0|12:08:07 blocked_strength_momentum:insufficient_history(+0.00%) -> 12:13:52 blocked_strength_momentum:below_strength_base(+0.00%) -> 12:13:52 blocked_vpw(+0.00%) -> 12:13:52 blocked_liquidity(+0.00%) -> ... -> 12:13:53 first_ai_wait(+0.00%) -> 12:13:53 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> 12:16:08 blocked_strength_momentum:below_strength_base(+0.00%)|

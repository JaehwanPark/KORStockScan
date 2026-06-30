# 2026-06-30 11:00 이후 감시대상 BUY 전 흐름

- generated_at: 2026-06-30T12:00:00
- source_events: /home/ubuntu/KORStockScan/data/runtime/sentinel_event_cache/buy_funnel_sentinel_events_2026-06-30.jsonl
- source_diagnostic: data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-30_1200_1100_goal.json
- event_window_since: 2026-06-30T11:00:00
- event_window_until: 2026-06-30T12:00:00
- symbol_count: 12
- rising_symbol_count_by_max_delta: 7
- rising_missed_buy_count_in_latest_diagnostic: 8
- rising_missed_symbol_count_in_report: 7
- rising_missed_residual_excluding_forced_scout_symbol_count: 3
- rising_missed_forced_scout_event_count: 88
- rising_missed_forced_scout_symbol_count: 5
- rising_missed_forced_scout_residual_symbol_count: 5
- real_submit_symbol_count_in_latest_diagnostic: 0
- buy_signal_or_pre_submit_pass_seen_symbols: 0
- stale_eval_symbol_count: 8
- rising_stale_eval_symbol_count: 4
- rising_fresh_only_symbol_count: 3
- stale_refresh_recovered_symbol_count: 12

## forced scout observation

- event_count: 88
- symbol_count: 5
- symbols: 000500, 010120, 153890, 240810, 475150
- rising_missed_residual_symbols: 000500, 010120, 153890, 240810, 475150
- rising_missed_residual_excluding_forced_scout_symbols: 001820, 033100, 095610
- decision_authority: source_quality_only
- runtime_effect: False

## blocker rollup

- 3: `latency_block` / `latency_state_danger`
- 2: `blocked_strength_momentum` / `below_window_buy_value`
- 1: `blocked_strength_momentum` / `blocked_ai_score_below_buy_score_threshold`
- 1: `blocked_liquidity` / `first_ai_wait_big_bite_not_confirmed`
- 1: `blocked_ai_score` / `blocked_ai_score_below_buy_score_threshold`
- 1: `ai_confirmed_terminal_no_budget` / `blocked_ai_score_below_buy_score_threshold`
- 1: `blocked_overbought` / `insufficient_history`
- 1: `blocked_strength_momentum` / `below_strength_base`
- 1: `blocked_strength_momentum` / `below_buy_ratio`

## blocker taxonomy

- 145: `runtime_backpressure`
- 40: `strategy_reject`
- 22: `intended_guard`
- 16: `pre_submit_quality_guard`
- 1: `watch_budget_reallocated`

## suppressed non-major blocker counts

- 145: `runtime_backpressure` / `scalping_scanner_watching_runtime_skip` / `scanner_full_eval_loop_budget_deferred`
- 5: `intended_guard` / `scalping_scanner_watching_runtime_skip` / `entry_cooldown_active`
- 1: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `scanner_hardgate_prefilter`

## rising-symbol blocker rollup

- 3: `latency_block` / `latency_state_danger`
- 1: `blocked_strength_momentum` / `blocked_ai_score_below_buy_score_threshold`
- 1: `blocked_liquidity` / `first_ai_wait_big_bite_not_confirmed`
- 1: `blocked_ai_score` / `blocked_ai_score_below_buy_score_threshold`
- 1: `ai_confirmed_terminal_no_budget` / `blocked_ai_score_below_buy_score_threshold`

## rising fresh-only blocker rollup

- 2: `latency_block` / `latency_state_danger`
- 1: `blocked_liquidity` / `first_ai_wait_big_bite_not_confirmed`

## rising stale-mixed blocker rollup

- 1: `latency_block` / `latency_state_danger`
- 1: `blocked_strength_momentum` / `blocked_ai_score_below_buy_score_threshold`
- 1: `blocked_ai_score` / `blocked_ai_score_below_buy_score_threshold`
- 1: `ai_confirmed_terminal_no_budget` / `blocked_ai_score_below_buy_score_threshold`

## stale-eval rollup

- 3: `blocked_vpw`
- 2: `ai_confirmed_terminal_no_budget`
- 1: `blocked_strength_momentum`
- 1: `blocked_overbought`
- 1: `ai_confirmed`

## stale-eval category rollup

- 8: `diagnostic_quote_age_stale`

## latency danger root cause

|종목|건수|top cause|spread ratio med/max|ws age med/max|spread ticks med/max|micro|bucket|
|---|---:|---|---:|---:|---:|---|---|
|제룡전기(033100)|34|latency_provenance_gap|-/-|-/-|-/-|-|diagnostic_latency_without_source_event_fields|
|LS ELECTRIC(010120)|30|spread_too_wide|0.010696/0.010776|95.5/569.0|5.0/5.0|neutral|spread=wide\|price=high\|depth=thick\|sample=rich|
|가온전선(000500)|30|spread_too_wide|0.011186/0.011312|173.5/10026.0|5.0/5.0|neutral|spread=wide\|price=high\|depth=normal\|sample=rich|
|SK이터닉스(475150)|23|spread_microstructure_wide|0.009597/0.011538|81.0/1282.0|5.0/6.0|neutral|spread=wide\|price=high\|depth=thick\|sample=rich|

## top rows by max delta

|종목|첫감시|마지막|상승여부|maxΔ|latestΔ|BUY전 주 blocker|class|stale평가|refresh회복|stale유형|max quote age|BUY전 통과신호|AI|실제submit|흐름|
|---|---:|---:|---|---:|---:|---|---|---:|---:|---|---:|---:|---:|---:|---|
|가온전선(000500)|11:17:44|11:59:33|rising|20.44%|20.44%|`latency_block`/latency_state_danger|-|0|28|-||-|71/WAIT|0|11:17:44 latency_block:latency_state_danger(+20.44%) -> 11:52:05 blocked_ai_score(+20.44%) -> 11:52:05 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+20.44%) -> 11:55:34 blocked_ai_score(+20.44%) -> 11:55:34 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+20.44%) -> 11:59:33 blocked_ai_score(+20.44%) -> 11:59:33 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+20.44%)|
|SK이터닉스(475150)|11:21:09|11:59:20|rising|4.06%|4.06%|`latency_block`/latency_state_danger|-|9|23|diagnostic_quote_age_stale|5460.0|-|73/WAIT|0|11:21:09 latency_block:latency_state_danger(+4.06%) -> 11:47:28 ai_confirmed(+4.06%) -> 11:47:28 wait65_79_ev_candidate(+4.06%) -> 11:47:28 first_ai_wait(+4.06%) -> ... -> 11:55:22 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+4.06%) -> 11:59:20 blocked_ai_score(+4.06%) -> 11:59:20 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+4.06%)|
|삼화콘덴서(001820)|11:01:20|11:41:24|rising|2.57%|2.57%|`blocked_strength_momentum`/blocked_ai_score_below_buy_score_threshold|-|6|12|diagnostic_quote_age_stale|29882.0|-|69/WAIT|0|11:01:20 blocked_strength_momentum:below_window_buy_value(+2.57%) -> 11:01:44 blocked_ai_score(+2.57%) -> 11:01:44 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+2.57%) -> 11:05:31 blocked_strength_momentum:below_buy_ratio(+2.57%) -> ... -> 11:41:24 blocked_gap_from_scan(+2.57%) -> 11:41:24 blocked_ai_score(+2.57%) -> 11:41:24 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+2.57%)|
|져스텍(153890)|11:59:06|11:59:10|rising|2.49%|2.49%|`blocked_liquidity`/first_ai_wait_big_bite_not_confirmed|-|0|1|-|227.0|-|62/WAIT|0|11:59:06 blocked_liquidity(+2.49%) -> 11:59:08 ai_confirmed(+2.49%) -> 11:59:10 first_ai_wait(+2.49%) -> 11:59:10 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+2.49%)|
|테스(095610)|11:00:16|11:59:46|rising|1.24%|1.24%|`blocked_ai_score`/blocked_ai_score_below_buy_score_threshold|-|1|2|diagnostic_quote_age_stale|3406.0|-|74/WAIT|0|11:00:16 blocked_ai_score(+1.24%) -> 11:00:16 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+1.24%) -> 11:03:56 blocked_strength_momentum:below_buy_ratio(+1.24%) -> 11:03:56 blocked_vpw(+1.24%) -> ... -> 11:55:41 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+1.24%) -> 11:59:46 blocked_ai_score(+1.24%) -> 11:59:46 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+1.24%)|
|LS ELECTRIC(010120)|11:02:09|11:58:39|rising|1.07%|1.07%|`latency_block`/latency_state_danger|-|0|30|-||-|70/|0|11:02:09 latency_block:latency_state_danger(+1.07%)|
|원익IPS(240810)|11:29:00|11:56:55|rising|0.55%|0.55%|`ai_confirmed_terminal_no_budget`/blocked_ai_score_below_buy_score_threshold|-|20|8|diagnostic_quote_age_stale|17614.0|-|67/WAIT|0|11:29:00 blocked_strength_momentum:below_buy_ratio(+0.55%) -> 11:29:00 blocked_vpw(+0.55%) -> 11:29:01 ai_confirmed(+0.55%) -> 11:29:01 first_ai_wait(+0.55%) -> ... -> 11:56:54 blocked_vpw(+0.55%) -> 11:56:55 blocked_ai_score(+0.55%) -> 11:56:55 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.55%)|
|저스템(417840)|11:00:51|11:00:51|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|-|0|1|-|73.0|-|50/|0|11:00:51 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|미래산업(025560)|11:01:30|11:10:25|flat_or_falling|0.00%|0.00%|`blocked_overbought`/insufficient_history|-|4|1|diagnostic_quote_age_stale|4851.0|-|50/|0|11:01:30 blocked_overbought(+0.00%) -> 11:01:30 blocked_strength_momentum:insufficient_history(+0.00%) -> 11:09:46 blocked_overbought(+0.00%) -> 11:10:25 blocked_strength_momentum:insufficient_history(+0.00%)|
|금호건설(002990)|11:05:12|11:56:06|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_strength_base|-|3|3|diagnostic_quote_age_stale|5184.0|-|50/|0|11:05:12 blocked_strength_momentum:below_strength_base(+0.00%) -> 11:05:12 blocked_vpw(+0.00%) -> 11:05:12 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%) -> 11:09:17 blocked_strength_momentum:below_strength_base(+0.00%) -> ... -> 11:56:06 blocked_vpw(+0.00%) -> 11:56:06 blocked_liquidity(+0.00%) -> 11:56:06 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%)|
|스피어(347700)|11:06:13|11:58:44|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|-|1|2|diagnostic_quote_age_stale|5647.0|-|50/|0|11:06:13 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 11:15:51 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%) -> 11:20:10 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 11:20:10 blocked_vpw(+0.00%) -> 11:20:10 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%) -> 11:58:44 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|주성엔지니어링(036930)|11:07:05|11:58:48|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_buy_ratio|-|3|3|diagnostic_quote_age_stale|5220.0|-|68/BUY|0|11:07:05 blocked_strength_momentum:below_buy_ratio(+0.00%) -> 11:07:05 blocked_vpw(+0.00%) -> 11:07:05 blocked_gap_from_scan(+0.00%) -> 11:07:06 ai_confirmed(+0.00%) -> ... -> 11:13:53 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.00%) -> 11:52:57 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 11:58:48 blocked_strength_momentum:below_buy_ratio(+0.00%)|

# 2026-06-29 15:00 이후 감시대상 BUY 전 흐름

- generated_at: 2026-06-29T19:54:05
- source_events: /home/ubuntu/KORStockScan/data/runtime/sentinel_event_cache/buy_funnel_sentinel_events_2026-06-29.jsonl
- source_diagnostic: data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1930_taxonomy.json
- event_window_since: 2026-06-29T15:00:00+09:00
- symbol_count: 68
- rising_symbol_count_by_max_delta: 10
- rising_missed_buy_count_in_latest_diagnostic: 32
- rising_missed_symbol_count_in_report: 9
- real_submit_symbol_count_in_latest_diagnostic: 1
- buy_signal_or_pre_submit_pass_seen_symbols: 0
- stale_eval_symbol_count: 14
- rising_stale_eval_symbol_count: 7
- rising_fresh_only_symbol_count: 3
- stale_refresh_recovered_symbol_count: 12

## blocker rollup

- 28: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 20: `scalping_scanner_watching_runtime_skip` / `ws_snapshot_missing_or_zero`
- 5: `blocked_strength_momentum` / `insufficient_history`
- 4: `blocked_strength_momentum` / `below_window_buy_value`
- 2: `blocked_overbought` / `insufficient_history`
- 2: `blocked_overbought` / `below_window_buy_value`
- 1: `blocked_liquidity` / `ai_score_50_buy_hold_override`
- 1: `ai_confirmed` / `first_ai_wait_big_bite_not_confirmed`
- 1: `blocked_overbought` / `below_buy_ratio`
- 1: `blocked_overbought` / `blocked_ai_score_below_buy_score_threshold`
- 1: `blocked_strength_momentum` / `below_strength_base`
- 1: `ai_confirmed_terminal_no_budget` / `below_buy_ratio`

## blocker taxonomy

- 583: `runtime_backpressure`
- 495: `strategy_reject`
- 271: `source_freshness_evictable`
- 124: `watch_budget_reallocated`
- 118: `source_freshness_recovering`
- 28: `source_freshness_blocker`
- 9: `intended_guard`

## suppressed non-major blocker counts

- 583: `runtime_backpressure` / `scalping_scanner_watching_runtime_skip` / `scanner_full_eval_loop_budget_deferred`
- 271: `source_freshness_evictable` / `scalping_scanner_watching_runtime_skip` / `ws_snapshot_missing_or_zero`
- 118: `source_freshness_recovering` / `scalping_scanner_watching_runtime_skip` / `ws_snapshot_missing_or_zero`
- 113: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `stale_recovery_failed`
- 5: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `scanner_hardgate_prefilter`
- 4: `intended_guard` / `scalping_scanner_watching_runtime_skip` / `entry_cooldown_active`
- 4: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `source_quality_unresolved_after_buy_window`
- 2: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `terminal_blocker_repeated`

## rising-symbol blocker rollup

- 2: `blocked_strength_momentum` / `insufficient_history`
- 1: `blocked_liquidity` / `ai_score_50_buy_hold_override`
- 1: `blocked_overbought` / `insufficient_history`
- 1: `ai_confirmed` / `first_ai_wait_big_bite_not_confirmed`
- 1: `blocked_overbought` / `below_buy_ratio`
- 1: `blocked_overbought` / `blocked_ai_score_below_buy_score_threshold`
- 1: `blocked_strength_momentum` / `below_strength_base`
- 1: `ai_confirmed_terminal_no_budget` / `below_buy_ratio`
- 1: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`

## rising fresh-only blocker rollup

- 2: `blocked_strength_momentum` / `insufficient_history`
- 1: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`

## rising stale-mixed blocker rollup

- 1: `blocked_liquidity` / `ai_score_50_buy_hold_override`
- 1: `blocked_overbought` / `insufficient_history`
- 1: `ai_confirmed` / `first_ai_wait_big_bite_not_confirmed`
- 1: `blocked_overbought` / `below_buy_ratio`
- 1: `blocked_overbought` / `blocked_ai_score_below_buy_score_threshold`
- 1: `blocked_strength_momentum` / `below_strength_base`
- 1: `ai_confirmed_terminal_no_budget` / `below_buy_ratio`

## stale-eval rollup

- 7: `ai_confirmed`
- 4: `blocked_strength_momentum`
- 3: `blocked_overbought`

## stale-eval category rollup

- 14: `diagnostic_quote_age_stale`

## top rows by max delta

|종목|첫감시|마지막|상승여부|maxΔ|latestΔ|BUY전 주 blocker|class|stale평가|refresh회복|stale유형|max quote age|BUY전 통과신호|AI|실제submit|흐름|
|---|---:|---:|---|---:|---:|---|---|---:|---:|---|---:|---:|---:|---:|---|
|ACE 리츠부동산인프라액티브(001530)|15:32:20|17:32:34|rising|138.50%|138.50%|`blocked_strength_momentum`/insufficient_history|source_freshness_blocker|0|0|-||-||0|-|
|성신양회(004980)|15:00:10|15:19:34|rising|7.01%|7.01%|`blocked_liquidity`/ai_score_50_buy_hold_override|-|6|6|diagnostic_quote_age_stale|10659.0|-|50/WAIT|0|15:00:10 blocked_liquidity(+7.01%) -> 15:00:10 blocked_ai_score:ai_score_50_buy_hold_override(+7.01%) -> 15:03:53 blocked_liquidity(+7.01%) -> 15:03:53 blocked_ai_score:ai_score_50_buy_hold_override(+7.01%) -> ... -> 15:19:34 blocked_liquidity(+7.01%) -> 15:19:34 blocked_gap_from_scan(+7.01%) -> 15:19:34 blocked_ai_score:ai_score_50_buy_hold_override(+7.01%)|
|져스텍(153890)|15:06:44|15:19:41|rising|4.80%|4.80%|`blocked_overbought`/insufficient_history|-|5|9|diagnostic_quote_age_stale|9818.0|-|50/USE_DEFENSIVE|0|15:06:44 blocked_overbought(+4.80%) -> 15:06:54 blocked_liquidity(+4.80%) -> 15:06:55 ai_confirmed(+4.80%) -> 15:06:55 first_ai_wait(+4.80%) -> ... -> 15:19:38 blocked_overbought(+4.80%) -> 15:19:41 blocked_liquidity(+4.80%) -> 15:19:41 blocked_ai_score:ai_score_50_buy_hold_override(+4.80%)|
|금호타이어(073240)|15:18:26|15:19:51|rising|2.28%|2.28%|`ai_confirmed`/first_ai_wait_big_bite_not_confirmed|-|4|0|diagnostic_quote_age_stale|6776.0|-|62/WAIT|0|15:18:26 ai_confirmed(+2.28%) -> 15:18:26 first_ai_wait(+2.28%) -> 15:18:26 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+2.28%) -> 15:19:51 ai_confirmed(+2.28%) -> 15:19:51 first_ai_wait(+2.28%) -> 15:19:51 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+2.28%)|
|에코프로(086520)|15:10:41|15:20:01|rising|1.93%|1.93%|`blocked_overbought`/below_buy_ratio|-|4|3|diagnostic_quote_age_stale|4089.0|-|62/WAIT|0|15:10:41 blocked_overbought(+1.93%) -> 15:10:41 blocked_strength_momentum:below_buy_ratio(+1.93%) -> 15:19:55 blocked_overbought(+1.93%) -> 15:19:59 blocked_strength_momentum:below_buy_ratio(+1.93%) -> 15:19:59 blocked_vpw(+1.93%) -> 15:20:01 ai_confirmed(+1.93%) -> 15:20:01 first_ai_wait(+1.93%) -> 15:20:01 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+1.93%)|
|올릭스(226950)|15:14:14|15:14:25|rising|1.31%|1.31%|`blocked_overbought`/blocked_ai_score_below_buy_score_threshold|-|3|1|diagnostic_quote_age_stale|8279.0|-|62/USE_DEFENSIVE|0|15:14:14 blocked_overbought(+1.31%) -> 15:14:24 ai_confirmed(+1.31%) -> 15:14:24 blocked_ai_score(+1.31%) -> 15:14:24 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+1.31%) -> 15:14:25 entry_ai_price_canary_fallback:invalid_price(+1.31%)|
|후성(093370)|15:18:58|15:19:25|rising|1.22%|1.22%|`blocked_strength_momentum`/insufficient_history|-|0|2|-|313.0|-|62/WAIT|0|15:18:58 blocked_strength_momentum:insufficient_history(+1.22%) -> 15:19:21 blocked_liquidity(+1.22%) -> 15:19:23 ai_confirmed(+1.22%) -> 15:19:25 first_ai_wait(+1.22%) -> 15:19:25 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+1.22%)|
|SK텔레콤(017670)|15:01:17|15:04:03|rising|1.08%|1.08%|`blocked_strength_momentum`/below_strength_base|-|5|5|diagnostic_quote_age_stale|4757.0|-|60/WAIT|0|15:01:17 blocked_strength_momentum:below_strength_base(+1.08%) -> 15:01:17 blocked_vpw(+1.08%) -> 15:01:18 ai_confirmed(+1.08%) -> 15:01:18 first_ai_wait(+1.08%) -> ... -> 15:04:03 ai_confirmed(+1.08%) -> 15:04:03 blocked_ai_score(+1.08%) -> 15:04:03 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+1.08%)|
|삼성SDI(006400)|15:02:33|15:19:07|rising|1.00%|1.00%|`ai_confirmed_terminal_no_budget`/below_buy_ratio|-|5|4|diagnostic_quote_age_stale|3998.0|-|62/WAIT|0|15:02:33 blocked_strength_momentum:below_buy_ratio(+1.00%) -> 15:02:35 ai_confirmed(+1.00%) -> 15:02:35 blocked_ai_score(+1.00%) -> 15:02:35 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+1.00%) -> ... -> 15:19:07 ai_confirmed(+1.00%) -> 15:19:07 first_ai_wait(+1.00%) -> 15:19:07 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+1.00%)|
|HD현대중공업(329180)|15:42:53|19:42:19|rising|0.51%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|금양그린파워(282720)|15:00:27|15:00:27|flat_or_falling|0.00%|0.00%|`blocked_overbought`/below_window_buy_value|-|2|0|diagnostic_quote_age_stale|9540.0|-|50/|0|15:00:27 blocked_overbought(+0.00%) -> 15:00:27 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|씨어스(458870)|15:03:11|15:03:11|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|-|0|1|-|1428.0|-|50/|0|15:03:11 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|차AI헬스케어(025620)|15:05:11|15:05:11|flat_or_falling|0.00%|0.00%|`blocked_overbought`/insufficient_history|-|2|0|diagnostic_quote_age_stale|3813.0|-|50/|0|15:05:11 blocked_overbought(+0.00%) -> 15:05:11 blocked_strength_momentum:insufficient_history(+0.00%)|
|계룡건설(013580)|15:05:29|15:05:37|flat_or_falling|0.00%|0.00%|`blocked_overbought`/below_strength_base|-|0|3|-|7661.0|-|50/|0|15:05:29 blocked_overbought(+0.00%) -> 15:05:37 blocked_strength_momentum:below_strength_base(+0.00%) -> 15:05:37 blocked_vpw(+0.00%) -> 15:05:37 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%)|
|셀비온(308430)|15:09:07|15:20:20|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|1|0|diagnostic_quote_age_stale|4193.0|-|50/|0|15:14:28 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|그래피(318060)|15:09:09|15:09:09|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/insufficient_history|-|1|0|diagnostic_quote_age_stale|5744.0|-|50/|0|15:09:09 blocked_strength_momentum:insufficient_history(+0.00%)|
|와이바이오로직스(338840)|15:09:11|15:09:11|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|-|1|0|diagnostic_quote_age_stale|5666.0|-|50/|0|15:09:11 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|에이프릴바이오(397030)|15:09:36|15:09:37|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|-|2|2|diagnostic_quote_age_stale|7792.0|-|62/WAIT|0|15:09:36 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 15:09:36 blocked_vpw(+0.00%) -> 15:09:37 ai_confirmed(+0.00%) -> 15:09:37 first_ai_wait(+0.00%) -> 15:09:37 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|
|쓰리빌리언(394800)|15:13:05|15:13:05|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|-|0|1|-|2204.0|-|50/|0|15:13:05 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|엠오티(413390)|15:13:38|15:16:33|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|와이지-원(019210)|15:13:40|15:13:48|flat_or_falling|0.00%|0.00%|`blocked_overbought`/below_window_buy_value|-|0|2|-|1997.0|-|50/|0|15:13:40 blocked_overbought(+0.00%) -> 15:13:48 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 15:13:48 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%)|
|일진홀딩스(015860)|15:16:14|15:16:14|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/insufficient_history|-|1|0|diagnostic_quote_age_stale|11385.0|-|50/|0|15:16:14 blocked_strength_momentum:insufficient_history(+0.00%)|
|대화제약(067080)|15:32:20|15:34:17|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|non_actionable_guard_or_backpressure|0|0|-||-||0|-|
|티에프이(425420)|15:32:20|15:34:17|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|non_actionable_guard_or_backpressure|0|0|-||-||0|-|
|디케이락(105740)|15:32:20|15:34:17|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|non_actionable_guard_or_backpressure|0|0|-||-||0|-|
|기아(000270)|15:35:21|15:36:59|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|non_actionable_guard_or_backpressure|0|0|-||-||0|-|
|제이오(418550)|15:39:52|15:41:44|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|non_actionable_guard_or_backpressure|0|0|-||-||0|-|
|네이처셀(007390)|15:41:23|19:54:00|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|풍산(103140)|19:19:39|19:21:36|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|non_actionable_guard_or_backpressure|0|0|-||-||0|-|
|포스코퓨처엠(003670)|19:21:10|19:22:31|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-|63/WAIT|0|-|
|비에이치(090460)|19:21:10|19:23:32|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|non_actionable_guard_or_backpressure|0|0|-||-||0|-|
|한화비전(489790)|19:21:10|19:23:32|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|non_actionable_guard_or_backpressure|0|0|-||-||0|-|
|코나아이(052400)|19:21:10|19:23:32|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|non_actionable_guard_or_backpressure|0|0|-||-||0|-|
|성일하이텍(365340)|19:22:41|19:24:33|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/insufficient_history|source_freshness_blocker|0|0|-||-||0|-|
|웹젠(069080)|19:24:11|19:25:59|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|세진중공업(075580)|19:24:11|19:26:59|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|한진칼(180640)|19:24:11|19:25:59|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|non_actionable_guard_or_backpressure|0|0|-||-||0|-|
|덕산테코피아(317330)|19:27:13|19:29:16|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|넥스틸(092790)|19:27:13|19:29:02|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|우리금융지주(316140)|19:27:13|19:29:16|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|non_actionable_guard_or_backpressure|0|0|-||-||0|-|
|나이벡(138610)|19:28:43|19:30:44|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|non_actionable_guard_or_backpressure|0|0|-||-||0|-|
|덕산네오룩스(213420)|19:28:43|19:32:03|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|넥슨게임즈(225570)|19:28:43|19:30:32|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|코오롱생명과학(102940)|19:28:43|19:30:32|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|non_actionable_guard_or_backpressure|0|0|-||-||0|-|
|SOOP(067160)|19:30:14|19:32:17|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|non_actionable_guard_or_backpressure|0|0|-||-||0|-|
|SK바이오사이언스(302440)|19:30:14|19:32:17|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|한국타이어앤테크놀로지(161390)|19:30:14|19:32:17|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|대상홀딩스(084690)|19:30:14|19:32:17|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|코웨이(021240)|19:30:14|19:32:30|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|non_actionable_guard_or_backpressure|0|0|-||-||0|-|
|신한지주(055550)|19:30:14|19:32:03|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|NHN(181710)|19:33:15|19:35:14|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|non_actionable_guard_or_backpressure|0|0|-||-||0|-|
|현대코퍼레이션(011760)|19:33:15|19:35:14|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|non_actionable_guard_or_backpressure|0|0|-||-||0|-|
|교보증권(030610)|19:33:15|19:36:29|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|보원케미칼(000100)|19:34:46|19:37:56|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|세방전지(004490)|19:34:46|19:37:56|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|SFA(056190)|19:36:16|19:38:15|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|non_actionable_guard_or_backpressure|0|0|-||-||0|-|
|한화시스템(272210)|19:37:47|19:40:10|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|애경산업(018250)|19:37:47|19:39:19|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|non_actionable_guard_or_backpressure|0|0|-||-||0|-|
|하나금융지주(086790)|19:39:18|19:41:01|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|두산테스나(131970)|19:39:18|19:41:01|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|RFHIC(218410)|19:40:48|19:43:30|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|한텍(098070)|19:42:19|19:44:29|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|non_actionable_guard_or_backpressure|0|0|-||-||0|-|
|KG이니시스(035600)|19:42:19|19:54:00|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|나우로보틱스(459510)|19:43:50|19:45:51|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|DS단석(017860)|19:43:50|19:54:00|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|HD현대(267250)|19:43:50|19:45:42|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|네오팜(092730)|19:43:50|19:45:42|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|네패스(033640)|19:43:50|19:49:46|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|

# 2026-06-29 13:40 이후 감시대상 BUY 전 흐름

- generated_at: 2026-06-29T15:00:21+09:00
- source_events: /home/ubuntu/KORStockScan/data/runtime/sentinel_event_cache/buy_funnel_sentinel_events_2026-06-29.jsonl
- source_diagnostic: data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1500_1340_goal.json
- event_window_since: 13:40
- symbol_count: 80
- rising_symbol_count_by_max_delta: 34
- rising_missed_buy_count_in_latest_diagnostic: 32
- rising_missed_symbol_count_in_report: 32
- real_submit_symbol_count_in_latest_diagnostic: 1
- buy_signal_or_pre_submit_pass_seen_symbols: 6
- stale_eval_symbol_count: 40
- rising_stale_eval_symbol_count: 26
- rising_fresh_only_symbol_count: 8
- stale_refresh_recovered_symbol_count: 48

## blocker rollup

- 16: `scalping_scanner_watching_runtime_skip` / `ws_snapshot_missing_or_zero`
- 15: `blocked_strength_momentum` / `below_window_buy_value`
- 8: `blocked_strength_momentum` / `insufficient_history`
- 6: `ai_confirmed` / `first_ai_wait_big_bite_not_confirmed`
- 6: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 5: `blocked_overbought` / `below_window_buy_value`
- 2: `blocked_liquidity` / `blocked_ai_score_below_buy_score_threshold`
- 2: `blocked_overbought` / `insufficient_history`
- 2: `ai_confirmed` / `blocked_ai_score_below_buy_score_threshold`
- 2: `blocked_overbought` / `first_ai_wait_big_bite_not_confirmed`
- 2: `blocked_strength_momentum` / `below_buy_ratio`
- 2: `blocked_strength_momentum` / `below_strength_base`

## rising-symbol blocker rollup

- 5: `blocked_strength_momentum` / `insufficient_history`
- 5: `ai_confirmed` / `first_ai_wait_big_bite_not_confirmed`
- 4: `blocked_strength_momentum` / `below_window_buy_value`
- 2: `blocked_liquidity` / `blocked_ai_score_below_buy_score_threshold`
- 2: `blocked_overbought` / `insufficient_history`
- 2: `ai_confirmed` / `blocked_ai_score_below_buy_score_threshold`
- 2: `blocked_overbought` / `first_ai_wait_big_bite_not_confirmed`
- 2: `blocked_overbought` / `below_window_buy_value`
- 2: `blocked_strength_momentum` / `below_buy_ratio`
- 1: `blocked_liquidity` / `-`
- 1: `blocked_overbought` / `below_buy_ratio`
- 1: `blocked_ai_score` / `qualification_passed`

## rising fresh-only blocker rollup

- 2: `blocked_strength_momentum` / `insufficient_history`
- 1: `blocked_liquidity` / `-`
- 1: `blocked_overbought` / `first_ai_wait_big_bite_not_confirmed`
- 1: `blocked_overbought` / `below_window_buy_value`
- 1: `ai_confirmed` / `first_ai_wait_big_bite_not_confirmed`
- 1: `blocked_strength_momentum` / `below_window_buy_value`
- 1: `blocked_liquidity` / `ai_score_50_buy_hold_override`

## rising stale-mixed blocker rollup

- 4: `ai_confirmed` / `first_ai_wait_big_bite_not_confirmed`
- 3: `blocked_strength_momentum` / `insufficient_history`
- 3: `blocked_strength_momentum` / `below_window_buy_value`
- 2: `blocked_liquidity` / `blocked_ai_score_below_buy_score_threshold`
- 2: `blocked_overbought` / `insufficient_history`
- 2: `ai_confirmed` / `blocked_ai_score_below_buy_score_threshold`
- 2: `blocked_strength_momentum` / `below_buy_ratio`
- 1: `blocked_overbought` / `below_buy_ratio`
- 1: `blocked_ai_score` / `qualification_passed`
- 1: `blocked_overbought` / `qualification_passed`
- 1: `blocked_overbought` / `below_window_buy_value`
- 1: `blocked_ai_score` / `below_buy_ratio`

## stale-eval rollup

- 18: `ai_confirmed`
- 14: `blocked_strength_momentum`
- 5: `blocked_overbought`
- 3: `ai_confirmed_terminal_no_budget`

## stale-eval category rollup

- 40: `diagnostic_quote_age_stale`

## top rows by max delta

|종목|첫감시|마지막|상승여부|maxΔ|latestΔ|BUY전 주 blocker|stale평가|refresh회복|stale유형|max quote age|BUY전 통과신호|AI|실제submit|흐름|
|---|---:|---:|---|---:|---:|---|---:|---:|---|---:|---:|---:|---:|---|
|사피엔반도체(452430)|13:46:59|14:02:35|rising|19.66%|19.66%|`blocked_liquidity`/-|0|5|-|7786.0|-|57/WAIT|0|13:48:15 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 13:48:15 blocked_liquidity(+0.00%) -> 13:48:15 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%) -> 13:55:38 blocked_liquidity(+19.66%) -> ... -> 13:59:34 blocked_liquidity(+19.66%) -> 13:59:34 blocked_ai_score(+19.66%) -> 13:59:34 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+19.66%)|
|올릭스(226950)|13:51:27|14:49:11|rising|14.00%|1.31%|`blocked_overbought`/below_buy_ratio|16|12|diagnostic_quote_age_stale|11334.0|14:49:06|82/BUY|0|13:51:27 blocked_overbought(+14.00%) -> 13:51:30 blocked_strength_momentum:below_buy_ratio(+14.00%) -> 13:51:32 ai_confirmed(+14.00%) -> 13:51:32 wait65_79_ev_candidate(+14.00%) -> ... -> 14:49:06 entry_armed:qualification_passed(+1.31%) -> 14:49:07 budget_pass(+1.31%) -> 14:49:11 latency_pass:caution_normal_entry_allowed(+1.31%)|
|광주신세계(037710)|13:54:15|14:57:10|rising|7.58%|3.70%|`blocked_ai_score`/qualification_passed|10|2|diagnostic_quote_age_stale|7666.0|14:04:55|50/WAIT|0|13:54:15 blocked_strength_momentum:insufficient_history(+7.58%) -> 13:56:49 blocked_ai_score:ai_score_50_buy_hold_override(+7.58%) -> 14:00:14 blocked_gap_from_scan(+7.58%) -> 14:00:16 ai_confirmed(+7.58%) -> ... -> 14:08:17 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+7.58%) -> 14:55:36 blocked_strength_momentum:below_strength_base(+3.70%) -> 14:57:10 blocked_ai_score:ai_score_50_buy_hold_override(+3.70%)|
|로킷헬스케어(376900)|14:29:11|14:41:07|rising|7.34%|7.34%|`blocked_strength_momentum`/insufficient_history|4|4|diagnostic_quote_age_stale|10464.0|-|58/WAIT|0|14:29:11 blocked_strength_momentum:insufficient_history(+7.34%) -> 14:31:24 blocked_strength_momentum:below_window_buy_value(+7.34%) -> 14:33:02 blocked_liquidity(+7.34%) -> 14:33:04 ai_confirmed(+7.34%) -> ... -> 14:41:07 ai_confirmed(+7.34%) -> 14:41:07 blocked_ai_score(+7.34%) -> 14:41:07 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+7.34%)|
|한올바이오파마(009420)|13:46:31|14:19:24|rising|7.13%|7.13%|`blocked_overbought`/qualification_passed|4|8|diagnostic_quote_age_stale|6237.0|13:46:33|50/WAIT|0|13:46:31 ai_confirmed(+7.13%) -> 13:46:33 entry_armed:qualification_passed(+7.13%) -> 13:46:33 budget_pass(+7.13%) -> 13:46:42 latency_block:latency_state_danger(+7.13%) -> ... -> 14:16:21 blocked_ai_score:ai_score_50_buy_hold_override(+7.13%) -> 14:19:15 blocked_overbought(+7.13%) -> 14:19:24 blocked_ai_score:ai_score_50_buy_hold_override(+7.13%)|
|성신양회(004980)|14:13:26|14:56:07|rising|7.01%|7.01%|`blocked_strength_momentum`/insufficient_history|6|4|diagnostic_quote_age_stale|8754.0|-|50/WAIT|0|14:13:26 blocked_strength_momentum:insufficient_history(+7.01%) -> 14:16:34 blocked_liquidity(+7.01%) -> 14:16:37 ai_confirmed(+7.01%) -> 14:16:37 first_ai_wait(+7.01%) -> ... -> 14:20:54 blocked_strength_momentum:insufficient_history(+7.01%) -> 14:56:07 blocked_liquidity(+7.01%) -> 14:56:07 blocked_ai_score:ai_score_50_buy_hold_override(+7.01%)|
|서산(079650)|13:40:28|14:24:10|rising|5.49%|5.49%|`blocked_liquidity`/blocked_ai_score_below_buy_score_threshold|5|6|diagnostic_quote_age_stale|5534.0|-|50/WAIT|0|13:40:28 blocked_liquidity(+0.63%) -> 13:40:29 ai_confirmed(+0.63%) -> 13:40:29 blocked_ai_score(+0.63%) -> 13:40:29 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.63%) -> ... -> 14:19:32 blocked_ai_score:ai_score_50_buy_hold_override(+5.49%) -> 14:24:10 blocked_liquidity(+5.49%) -> 14:24:10 blocked_ai_score:ai_score_50_buy_hold_override(+5.49%)|
|져스텍(153890)|13:47:29|14:25:01|rising|4.80%|4.80%|`blocked_overbought`/insufficient_history|8|5|diagnostic_quote_age_stale|6902.0|-|50/WAIT|0|13:47:29 blocked_overbought(+4.80%) -> 13:47:31 ai_confirmed(+4.80%) -> 13:47:31 wait65_79_ev_candidate(+4.80%) -> 13:47:32 first_ai_wait(+4.80%) -> ... -> 14:05:06 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+4.80%) -> 14:25:00 blocked_overbought(+4.80%) -> 14:25:01 blocked_strength_momentum:insufficient_history(+4.80%)|
|후성(093370)|14:42:23|14:54:23|rising|4.22%|4.22%|`ai_confirmed`/blocked_ai_score_below_buy_score_threshold|10|2|diagnostic_quote_age_stale|4911.0|-|62/WAIT|0|14:42:23 ai_confirmed(+4.22%) -> 14:42:24 first_ai_wait(+4.22%) -> 14:42:24 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+4.22%) -> 14:45:01 ai_confirmed(+4.22%) -> ... -> 14:54:23 ai_confirmed(+4.22%) -> 14:54:23 blocked_ai_score(+4.22%) -> 14:54:23 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+4.22%)|
|남화산업(111710)|13:47:57|14:07:22|rising|3.76%|3.76%|`blocked_overbought`/first_ai_wait_big_bite_not_confirmed|0|7|-|1019.0|-|62/WAIT|0|13:47:57 blocked_overbought(+0.85%) -> 13:47:57 blocked_liquidity(+0.85%) -> 13:47:59 ai_confirmed(+0.85%) -> 13:47:59 wait65_79_ev_candidate(+0.85%) -> ... -> 14:07:22 ai_confirmed(+3.76%) -> 14:07:22 blocked_ai_score(+3.76%) -> 14:07:22 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+3.76%)|
|에이직랜드(445090)|13:41:53|14:41:09|rising|3.65%|3.65%|`blocked_overbought`/below_window_buy_value|4|5|diagnostic_quote_age_stale|8241.0|14:38:55|82/BUY|0|13:41:53 blocked_overbought(+0.00%) -> 13:41:53 blocked_strength_momentum:insufficient_history(+0.00%) -> 14:20:30 blocked_overbought(+0.00%) -> 14:20:38 blocked_strength_momentum:below_window_buy_value(+0.00%) -> ... -> 14:41:09 entry_armed_expired:qualification_passed(+3.65%) -> 14:41:09 blocked_overbought(+3.65%) -> 14:41:09 blocked_strength_momentum:below_window_buy_value(+3.65%)|
|해태제과식품(101530)|13:41:48|13:41:48|rising|3.18%|3.18%|`blocked_strength_momentum`/insufficient_history|0|0|-|2500.0|-|50/|0|13:41:48 blocked_strength_momentum:insufficient_history(+3.18%)|
|포바이포(389140)|14:39:57|14:40:04|rising|3.10%|3.10%|`blocked_overbought`/below_window_buy_value|0|2|-|1387.0|-|50/|0|14:39:57 blocked_overbought(+3.10%) -> 14:40:04 blocked_strength_momentum:below_window_buy_value(+3.10%)|
|금호타이어(073240)|14:02:04|14:34:47|rising|2.85%|2.28%|`ai_confirmed`/first_ai_wait_big_bite_not_confirmed|0|2|-|2902.0|-|50/WAIT|0|14:02:04 blocked_gap_from_scan(+2.85%) -> 14:02:06 ai_confirmed(+2.85%) -> 14:02:06 wait65_79_ev_candidate(+2.85%) -> 14:02:07 first_ai_wait(+2.85%) -> ... -> 14:06:07 blocked_ai_score(+2.85%) -> 14:06:07 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+2.85%) -> 14:34:47 blocked_ai_score:ai_score_50_buy_hold_override(+2.28%)|
|대명에너지(389260)|14:02:28|14:58:30|rising|2.61%|2.61%|`blocked_liquidity`/blocked_ai_score_below_buy_score_threshold|4|7|diagnostic_quote_age_stale|9488.0|-|62/WAIT|0|14:02:28 blocked_strength_momentum:insufficient_history(+2.61%) -> 14:22:22 blocked_overbought(+2.61%) -> 14:22:22 blocked_liquidity(+2.61%) -> 14:22:22 blocked_gap_from_scan(+2.61%) -> ... -> 14:58:30 ai_confirmed(+2.61%) -> 14:58:30 blocked_ai_score(+2.61%) -> 14:58:30 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+2.61%)|
|로보스타(090360)|14:31:48|14:33:13|rising|2.41%|2.41%|`blocked_strength_momentum`/below_buy_ratio|4|3|diagnostic_quote_age_stale|5718.0|-|60/WAIT|0|14:31:48 blocked_strength_momentum:below_buy_ratio(+2.41%) -> 14:31:50 ai_confirmed(+2.41%) -> 14:31:50 first_ai_wait(+2.41%) -> 14:31:50 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+2.41%) -> 14:33:13 blocked_strength_momentum:below_buy_ratio(+2.41%) -> 14:33:13 blocked_liquidity(+2.41%) -> 14:33:13 blocked_ai_score(+2.41%) -> 14:33:13 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+2.41%)|
|녹십자웰빙(234690)|14:06:36|14:06:37|rising|1.97%|1.97%|`blocked_strength_momentum`/below_window_buy_value|2|3|diagnostic_quote_age_stale|16381.0|-|62/WAIT|0|14:06:36 blocked_strength_momentum:below_window_buy_value(+1.97%) -> 14:06:36 blocked_vpw(+1.97%) -> 14:06:36 blocked_liquidity(+1.97%) -> 14:06:37 ai_confirmed(+1.97%) -> 14:06:37 first_ai_wait(+1.97%) -> 14:06:37 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+1.97%)|
|로보티즈(108490)|14:31:07|14:32:18|rising|1.95%|1.95%|`blocked_strength_momentum`/below_buy_ratio|1|1|diagnostic_quote_age_stale|9255.0|-|50/|0|14:31:07 blocked_strength_momentum:below_buy_ratio(+1.95%) -> 14:32:18 blocked_strength_momentum:below_window_buy_value(+1.95%)|
|에코프로(086520)|14:23:35|14:23:35|rising|1.93%|1.93%|`blocked_overbought`/insufficient_history|2|0|diagnostic_quote_age_stale|6785.0|-|50/|0|14:23:35 blocked_overbought(+1.93%) -> 14:23:35 blocked_strength_momentum:insufficient_history(+1.93%)|
|LS ELECTRIC(010120)|13:52:09|14:56:27|rising|1.81%|1.81%|`ai_confirmed`/first_ai_wait_big_bite_not_confirmed|11|2|diagnostic_quote_age_stale|9338.0|-|72/WAIT|0|13:52:09 ai_confirmed(+1.81%) -> 13:52:09 first_ai_wait(+1.81%) -> 13:52:09 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+1.81%) -> 14:19:06 ai_confirmed(+1.81%) -> ... -> 14:56:27 wait65_79_ev_candidate(+1.81%) -> 14:56:27 blocked_ai_score(+1.81%) -> 14:56:27 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+1.81%)|
|SK이터닉스(475150)|14:03:23|14:43:55|rising|1.58%|0.59%|`blocked_ai_score`/below_buy_ratio|2|4|diagnostic_quote_age_stale|7138.0|-|62/WAIT|0|14:03:23 blocked_ai_score:ai_score_50_buy_hold_override(+1.58%) -> 14:22:00 blocked_strength_momentum:below_buy_ratio(+1.58%) -> 14:22:00 blocked_vpw(+1.58%) -> 14:22:01 ai_confirmed(+1.58%) -> ... -> 14:43:54 ai_confirmed(+0.59%) -> 14:43:55 blocked_ai_score(+0.59%) -> 14:43:55 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.59%)|
|한화솔루션(009830)|14:12:00|14:56:36|rising|1.58%|1.58%|`ai_confirmed`/first_ai_wait_big_bite_not_confirmed|5|0|diagnostic_quote_age_stale|15294.0|-|50/WAIT|0|14:12:00 ai_confirmed(+0.87%) -> 14:12:00 first_ai_wait(+0.87%) -> 14:12:00 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.87%) -> 14:36:27 ai_confirmed(+0.87%) -> 14:36:27 first_ai_wait(+0.87%) -> 14:36:27 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.87%) -> 14:56:36 blocked_strength_momentum:below_window_buy_value(+1.58%)|
|디앤디파마텍(347850)|13:52:18|14:47:46|rising|1.38%|1.38%|`ai_confirmed`/first_ai_wait_big_bite_not_confirmed|1|1|diagnostic_quote_age_stale|6929.0|-|50/WAIT|0|13:52:18 blocked_overbought(+1.38%) -> 13:52:19 ai_confirmed(+1.38%) -> 13:52:20 first_ai_wait(+1.38%) -> 13:52:20 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+1.38%) -> 14:38:21 ai_confirmed(+1.38%) -> 14:38:21 first_ai_wait(+1.38%) -> 14:38:21 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+1.38%) -> 14:47:46 blocked_strength_momentum:insufficient_history(+1.38%)|
|모헨즈(006920)|13:47:40|13:53:37|rising|1.37%|1.37%|`blocked_overbought`/first_ai_wait_big_bite_not_confirmed|4|4|diagnostic_quote_age_stale|8280.0|-|62/WAIT|0|13:47:40 blocked_overbought(+1.37%) -> 13:47:48 blocked_liquidity(+1.37%) -> 13:47:49 ai_confirmed(+1.37%) -> 13:47:50 first_ai_wait(+1.37%) -> ... -> 13:53:37 ai_confirmed(+1.37%) -> 13:53:37 first_ai_wait(+1.37%) -> 13:53:37 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+1.37%)|
|아세아시멘트(183190)|14:27:36|14:27:36|rising|1.08%|1.08%|`blocked_strength_momentum`/insufficient_history|1|0|diagnostic_quote_age_stale|6701.0|-|50/|0|14:27:36 blocked_strength_momentum:insufficient_history(+1.08%)|
|SK텔레콤(017670)|14:57:31|14:59:58|rising|1.08%|1.08%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|1|0|diagnostic_quote_age_stale|6533.0|-|50/|0|14:58:38 blocked_strength_momentum:insufficient_history(+1.08%)|
|삼성SDI(006400)|13:50:53|14:58:35|rising|1.00%|1.00%|`ai_confirmed`/blocked_ai_score_below_buy_score_threshold|2|2|diagnostic_quote_age_stale|3217.0|13:52:30|62/WAIT|0|13:50:53 blocked_strength_momentum:below_buy_ratio(+1.00%) -> 13:52:30 ai_confirmed(+1.00%) -> 13:52:30 wait65_79_ev_candidate(+1.00%) -> 13:52:30 entry_armed:qualification_passed(+1.00%) -> ... -> 14:58:35 ai_confirmed(+1.00%) -> 14:58:35 blocked_ai_score(+1.00%) -> 14:58:35 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+1.00%)|
|유니셈(036200)|14:37:29|14:37:29|rising|0.83%|0.83%|`blocked_strength_momentum`/below_window_buy_value|0|1|-|2860.0|-|50/|0|14:37:29 blocked_strength_momentum:below_window_buy_value(+0.83%)|
|SK오션플랜트(100090)|14:12:57|14:19:40|rising|0.79%|0.79%|`blocked_liquidity`/first_ai_wait_big_bite_not_confirmed|4|2|diagnostic_quote_age_stale|4338.0|-|62/WAIT|0|14:12:57 blocked_liquidity(+0.79%) -> 14:12:59 ai_confirmed(+0.79%) -> 14:12:59 first_ai_wait(+0.79%) -> 14:12:59 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.79%) -> 14:19:38 blocked_liquidity(+0.79%) -> 14:19:40 ai_confirmed(+0.79%) -> 14:19:40 first_ai_wait(+0.79%) -> 14:19:40 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.79%)|
|삼성에스디에스(018260)|14:30:18|14:30:18|rising|0.76%|0.76%|`ai_confirmed`/first_ai_wait_big_bite_not_confirmed|2|0|diagnostic_quote_age_stale|4087.0|-|62/WAIT|0|14:30:18 ai_confirmed(+0.76%) -> 14:30:18 first_ai_wait(+0.76%) -> 14:30:18 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.76%)|
|HPSP(403870)|14:36:59|14:36:59|rising|0.57%|0.57%|`blocked_strength_momentum`/insufficient_history|0|1|-|67.0|-|50/|0|14:36:59 blocked_strength_momentum:insufficient_history(+0.57%)|
|동아엘텍(088130)|14:09:22|14:09:22|rising|0.55%|0.55%|`blocked_liquidity`/ai_score_50_buy_hold_override|0|1|-|105.0|-|50/|0|14:09:22 blocked_liquidity(+0.55%) -> 14:09:22 blocked_ai_score:ai_score_50_buy_hold_override(+0.55%)|
|씨어스(458870)|13:42:01|14:38:24|rising|0.27%|0.27%|`blocked_strength_momentum`/below_window_buy_value|3|3|diagnostic_quote_age_stale|6870.0|-|50/WAIT|0|13:42:01 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 13:42:01 blocked_vpw(+0.00%) -> 13:42:01 blocked_liquidity(+0.00%) -> 13:42:02 ai_confirmed(+0.00%) -> ... -> 14:15:35 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 14:38:24 blocked_overbought(+0.27%) -> 14:38:24 blocked_strength_momentum:below_buy_ratio(+0.27%)|
|와이지-원(019210)|13:58:07|13:58:09|rising|0.25%|0.25%|`blocked_strength_momentum`/below_window_buy_value|2|1|diagnostic_quote_age_stale|3963.0|-|62/WAIT|0|13:58:07 blocked_strength_momentum:below_window_buy_value(+0.25%) -> 13:58:09 ai_confirmed(+0.25%) -> 13:58:09 first_ai_wait(+0.25%) -> 13:58:09 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.25%)|
|코스맥스(192820)|13:40:37|13:40:38|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|2|2|diagnostic_quote_age_stale|3514.0|-|62/WAIT|0|13:40:37 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 13:40:37 blocked_liquidity(+0.00%) -> 13:40:38 ai_confirmed(+0.00%) -> 13:40:38 first_ai_wait(+0.00%) -> 13:40:38 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|
|지엔씨에너지(119850)|13:40:47|13:40:47|flat_or_falling|0.00%|0.00%|`blocked_overbought`/-|0|1|-|2110.0|-|50/|0|13:40:47 blocked_overbought(+0.00%)|
|대한제강(084010)|13:42:23|13:43:27|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|0|0|-||-||0|-|
|원준(382840)|13:42:23|14:51:34|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|0|0|-||-||0|-|
|슈프리마(236200)|13:42:23|13:44:09|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|0|0|-||-||0|-|
|태광(023160)|13:43:11|13:43:17|flat_or_falling|0.00%|0.00%|`blocked_overbought`/below_window_buy_value|0|1|-|2902.0|-|50/|0|13:43:11 blocked_overbought(+0.00%) -> 13:43:17 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|신성델타테크(065350)|13:43:47|13:43:49|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|2|2|diagnostic_quote_age_stale|7069.0|-|62/WAIT|0|13:43:47 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 13:43:47 blocked_liquidity(+0.00%) -> 13:43:49 ai_confirmed(+0.00%) -> 13:43:49 first_ai_wait(+0.00%) -> 13:43:49 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|
|기업은행(024110)|13:43:54|13:45:42|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|2|2|diagnostic_quote_age_stale|7720.0|-|62/WAIT|0|13:44:55 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 13:44:55 blocked_vpw(+0.00%) -> 13:44:57 ai_confirmed(+0.00%) -> 13:44:57 first_ai_wait(+0.00%) -> 13:44:57 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|
|휴메딕스(200670)|13:45:08|13:45:08|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|0|1|-|1664.0|-|50/|0|13:45:08 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|링크솔루션(474650)|13:45:25|13:52:54|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|0|3|-|6672.0|-|50/|0|13:49:12 blocked_strength_momentum:below_strength_base(+0.00%) -> 13:49:12 blocked_vpw(+0.00%) -> 13:49:12 blocked_liquidity(+0.00%) -> 13:49:12 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%)|
|세명전기(017510)|13:45:25|13:50:20|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|0|0|-||-||0|-|
|코오롱인더(120110)|13:45:25|13:52:37|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|0|0|-||-||0|-|
|컴퍼니케이(307930)|13:45:25|13:49:39|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|0|0|-||-||0|-|
|현대제철(004020)|13:45:59|13:45:59|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|0|1|-|974.0|-|50/|0|13:45:59 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|LG에너지솔루션(373220)|13:48:22|13:48:33|flat_or_falling|0.00%|0.00%|`blocked_overbought`/latency_quote_fresh_composite_normal_override|0|2|-|954.0|13:48:24|83/BUY|1|13:48:22 blocked_overbought(+0.00%) -> 13:48:24 ai_confirmed(+0.00%) -> 13:48:24 entry_armed:qualification_passed(+0.00%) -> 13:48:24 budget_pass(+0.00%) -> 13:48:28 latency_pass:latency_quote_fresh_composite_normal_override(+0.00%) -> 13:48:33 order_bundle_submitted:latency_quote_fresh_composite_normal_override(+0.00%)|
|인바디(041830)|13:48:36|14:46:25|flat_or_falling|0.00%|0.00%|`blocked_overbought`/below_window_buy_value|4|2|diagnostic_quote_age_stale|6099.0|-|63/WAIT|0|13:48:36 blocked_overbought(+0.00%) -> 13:48:36 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 14:46:21 blocked_overbought(+0.00%) -> 14:46:24 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 14:46:25 ai_confirmed(+0.00%) -> 14:46:25 first_ai_wait(+0.00%) -> 14:46:25 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|
|아이엠바이오로직스(493280)|13:49:25|13:49:25|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|0|1|-|856.0|-|50/|0|13:49:25 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|KoAct 팔란티어밸류체인액티브(000930)|13:50:01|13:54:09|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|0|0|-||-||0|-|
|HJ중공업(097230)|13:54:16|13:56:26|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|0|0|-||-||0|-|
|광동제약(009290)|13:58:22|13:58:22|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/insufficient_history|1|0|diagnostic_quote_age_stale|7458.0|-|50/|0|13:58:22 blocked_strength_momentum:insufficient_history(+0.00%)|
|포스코인터내셔널(047050)|14:10:04|14:10:06|flat_or_falling|0.00%|0.00%|`ai_confirmed`/first_ai_wait_big_bite_not_confirmed|0|0|-|307.0|-|62/WAIT|0|14:10:04 ai_confirmed(+0.00%) -> 14:10:06 first_ai_wait(+0.00%) -> 14:10:06 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|
|계룡건설(013580)|14:10:09|14:10:12|flat_or_falling|0.00%|0.00%|`blocked_overbought`/below_strength_base|0|2|-|159.0|-|50/|0|14:10:09 blocked_overbought(+0.00%) -> 14:10:12 blocked_strength_momentum:below_strength_base(+0.00%)|
|동방메디컬(240550)|14:11:18|14:11:18|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/insufficient_history|1|0|diagnostic_quote_age_stale|7351.0|-|50/|0|14:11:18 blocked_strength_momentum:insufficient_history(+0.00%)|
|대한전선(001440)|14:16:51|14:16:51|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/insufficient_history|1|0|diagnostic_quote_age_stale|5463.0|-|50/|0|14:16:51 blocked_strength_momentum:insufficient_history(+0.00%)|
|한선엔지니어링(452280)|14:19:43|14:26:28|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|1|1|diagnostic_quote_age_stale|3644.0|-|50/|0|14:19:43 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|에이팩트(200470)|14:19:56|14:19:56|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_strength_base|0|1|-|621.0|-|50/|0|14:19:56 blocked_strength_momentum:below_strength_base(+0.00%)|
|리센스메디컬(394420)|14:23:15|14:23:15|flat_or_falling|0.00%|0.00%|`blocked_overbought`/below_window_buy_value|2|0|diagnostic_quote_age_stale|9515.0|-|50/|0|14:23:15 blocked_overbought(+0.00%) -> 14:23:15 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|케이씨텍(281820)|14:27:59|14:28:00|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|2|3|diagnostic_quote_age_stale|7375.0|-|62/WAIT|0|14:27:59 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 14:27:59 blocked_vpw(+0.00%) -> 14:27:59 blocked_liquidity(+0.00%) -> 14:28:00 ai_confirmed(+0.00%) -> 14:28:00 first_ai_wait(+0.00%) -> 14:28:00 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|
|탑머티리얼(360070)|14:29:12|14:31:41|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|0|0|-||-||0|-|
|마음AI(377480)|14:31:14|14:34:19|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|0|0|-||-||0|-|
|씨에스윈드(112610)|14:32:56|14:32:56|flat_or_falling|0.00%|0.00%|`blocked_overbought`/ai_score_50_buy_hold_override|0|2|-|121.0|-|50/|0|14:32:56 blocked_overbought(+0.00%) -> 14:32:56 blocked_liquidity(+0.00%) -> 14:32:56 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%)|
|KG스틸(016380)|14:35:16|14:38:31|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|0|0|-||-||0|-|
|DSC인베스트먼트(241520)|14:40:21|14:40:23|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|2|3|diagnostic_quote_age_stale|9484.0|-|62/WAIT|0|14:40:21 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 14:40:21 blocked_vpw(+0.00%) -> 14:40:21 blocked_liquidity(+0.00%) -> 14:40:23 ai_confirmed(+0.00%) -> 14:40:23 first_ai_wait(+0.00%) -> 14:40:23 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|
|시노펙스(025320)|14:40:58|14:41:00|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|0|1|-|2815.0|-|62/WAIT|0|14:40:58 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 14:40:58 blocked_gap_from_scan(+0.00%) -> 14:41:00 ai_confirmed(+0.00%) -> 14:41:00 first_ai_wait(+0.00%) -> 14:41:00 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|
|자람테크놀로지(389020)|14:42:21|14:45:46|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|0|0|-||-||0|-|
|한미반도체(042700)|14:43:43|14:45:08|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_strength_base|0|3|-|3437.0|-|50/|0|14:43:43 blocked_strength_momentum:below_strength_base(+0.00%) -> 14:45:08 blocked_vpw(+0.00%) -> 14:45:08 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%)|
|하나기술(299030)|14:45:23|14:49:42|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|2|3|diagnostic_quote_age_stale|8730.0|-|64/WAIT|0|14:47:20 blocked_overbought(+0.00%) -> 14:47:28 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 14:47:28 blocked_liquidity(+0.00%) -> 14:47:30 ai_confirmed(+0.00%) -> 14:47:30 first_ai_wait(+0.00%) -> 14:47:30 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|
|SFA넥셀(222080)|14:46:18|14:46:18|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|1|0|diagnostic_quote_age_stale|3152.0|-|50/|0|14:46:18 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|나노신소재(121600)|14:48:31|14:48:31|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|1|0|diagnostic_quote_age_stale|9289.0|-|50/|0|14:48:31 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|에스피시스템스(317830)|14:50:26|14:53:00|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|0|0|-||-||0|-|
|셀레믹스(331920)|14:50:26|14:53:38|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|0|0|-||-||0|-|
|화성밸브(039610)|14:51:27|14:54:30|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|0|0|-||-||0|-|
|레인보우로보틱스(277810)|14:53:28|14:56:45|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|0|0|-||-||0|-|
|BNK 카카오그룹포커스(001200)|14:54:29|14:54:29|flat_or_falling|0.00%|0.00%|`-`/-|0|0|-||-||0|-|
|삼지전자(037460)|14:55:29|14:58:44|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|0|0|-||-||0|-|
|파로스아이바이오(388870)|14:56:30|14:59:58|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|0|0|-||-||0|-|

# 2026-06-29 11:30 이후 감시대상 BUY 전 흐름

- generated_at: 13:40
- source_events: /home/ubuntu/KORStockScan/data/runtime/sentinel_event_cache/buy_funnel_sentinel_events_2026-06-29.jsonl
- source_diagnostic: data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1340_1130_goal.json
- event_window_since: 11:30
- symbol_count: 250
- rising_symbol_count_by_max_delta: 43
- rising_missed_buy_count_in_latest_diagnostic: 51
- rising_missed_symbol_count_in_report: 45
- real_submit_symbol_count_in_latest_diagnostic: 0
- buy_signal_or_pre_submit_pass_seen_symbols: 8
- stale_eval_symbol_count: 111
- rising_stale_eval_symbol_count: 30
- rising_fresh_only_symbol_count: 13
- stale_refresh_recovered_symbol_count: 101

## blocker rollup

- 65: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 54: `scalping_scanner_watching_runtime_skip` / `ws_snapshot_missing_or_zero`
- 31: `blocked_strength_momentum` / `below_window_buy_value`
- 21: `blocked_strength_momentum` / `insufficient_history`
- 15: `blocked_overbought` / `below_window_buy_value`
- 12: `blocked_strength_momentum` / `below_strength_base`
- 6: `blocked_strength_momentum` / `below_buy_ratio`
- 6: `blocked_overbought` / `insufficient_history`
- 5: `blocked_overbought` / `-`
- 5: `ai_confirmed` / `first_ai_wait_big_bite_not_confirmed`
- 4: `blocked_liquidity` / `first_ai_wait_big_bite_not_confirmed`
- 4: `-` / `-`

## rising-symbol blocker rollup

- 4: `blocked_strength_momentum` / `insufficient_history`
- 4: `blocked_strength_momentum` / `below_buy_ratio`
- 4: `blocked_strength_momentum` / `below_strength_base`
- 3: `blocked_overbought` / `blocked_ai_score_below_buy_score_threshold`
- 3: `blocked_liquidity` / `first_ai_wait_big_bite_not_confirmed`
- 3: `ai_confirmed` / `first_ai_wait_big_bite_not_confirmed`
- 3: `blocked_overbought` / `below_window_buy_value`
- 2: `blocked_overbought` / `-`
- 2: `blocked_overbought` / `insufficient_history`
- 2: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 2: `ai_confirmed` / `blocked_ai_score_below_buy_score_threshold`
- 2: `ai_confirmed_terminal_no_budget` / `below_buy_ratio`

## rising fresh-only blocker rollup

- 2: `blocked_strength_momentum` / `insufficient_history`
- 2: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 2: `ai_confirmed` / `blocked_ai_score_below_buy_score_threshold`
- 1: `blocked_strength_momentum` / `below_strength_base`
- 1: `ai_confirmed` / `first_ai_wait_big_bite_not_confirmed`
- 1: `blocked_overbought` / `-`
- 1: `ai_confirmed_terminal_no_budget` / `first_ai_wait_big_bite_not_confirmed`
- 1: `scalping_scanner_watching_runtime_skip` / `ws_snapshot_missing_or_zero`
- 1: `ai_confirmed` / `below_buy_ratio`
- 1: `ai_confirmed_terminal_no_budget` / `below_buy_ratio`

## rising stale-mixed blocker rollup

- 4: `blocked_strength_momentum` / `below_buy_ratio`
- 3: `blocked_overbought` / `blocked_ai_score_below_buy_score_threshold`
- 3: `blocked_liquidity` / `first_ai_wait_big_bite_not_confirmed`
- 3: `blocked_strength_momentum` / `below_strength_base`
- 3: `blocked_overbought` / `below_window_buy_value`
- 2: `blocked_strength_momentum` / `insufficient_history`
- 2: `blocked_overbought` / `insufficient_history`
- 2: `ai_confirmed` / `first_ai_wait_big_bite_not_confirmed`
- 1: `ai_confirmed_terminal_no_budget` / `insufficient_history`
- 1: `blocked_liquidity` / `blocked_ai_score_below_buy_score_threshold`
- 1: `blocked_overbought` / `-`
- 1: `blocked_overbought` / `ai_score_50_buy_hold_override`

## stale-eval rollup

- 42: `blocked_strength_momentum`
- 41: `ai_confirmed`
- 22: `blocked_overbought`
- 5: `ai_confirmed_terminal_no_budget`
- 1: `blocked_liquidity`

## stale-eval category rollup

- 111: `diagnostic_quote_age_stale`

## top rows by max delta

|종목|첫감시|마지막|상승여부|maxΔ|latestΔ|BUY전 주 blocker|stale평가|refresh회복|stale유형|max quote age|BUY전 통과신호|AI|실제submit|흐름|
|---|---:|---:|---|---:|---:|---|---:|---:|---|---:|---:|---:|---:|---|
|올릭스(226950)|11:41:50|13:32:29|rising|14.00%|14.00%|`blocked_overbought`/blocked_ai_score_below_buy_score_threshold|19|14|diagnostic_quote_age_stale|8415.0|12:11:38|62/USE_DEFENSIVE|0|11:41:50 blocked_overbought(+14.00%) -> 11:41:59 ai_confirmed(+14.00%) -> 11:41:59 wait65_79_ev_candidate(+14.00%) -> 11:41:59 blocked_ai_score(+14.00%) -> ... -> 13:32:28 blocked_ai_score(+14.00%) -> 13:32:28 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+14.00%) -> 13:32:29 entry_ai_price_canary_fallback:invalid_price(+14.00%)|
|광주신세계(037710)|11:50:35|13:38:01|rising|7.58%|7.58%|`ai_confirmed_terminal_no_budget`/insufficient_history|12|0|diagnostic_quote_age_stale|5962.0|-|50/USE_DEFENSIVE|0|11:50:35 blocked_strength_momentum:insufficient_history(+7.58%) -> 11:51:40 ai_confirmed(+7.58%) -> 11:51:40 blocked_ai_score(+7.58%) -> 11:51:40 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+7.58%) -> ... -> 13:07:16 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+7.58%) -> 13:07:18 entry_ai_price_canary_fallback:invalid_price(+7.58%) -> 13:38:01 blocked_strength_momentum:insufficient_history(+7.58%)|
|화신(010690)|11:57:42|11:57:43|rising|7.49%|7.49%|`blocked_liquidity`/blocked_ai_score_below_buy_score_threshold|3|1|diagnostic_quote_age_stale|6499.0|-|58/WAIT|0|11:57:42 blocked_liquidity(+7.49%) -> 11:57:43 ai_confirmed(+7.49%) -> 11:57:43 blocked_ai_score(+7.49%) -> 11:57:43 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+7.49%)|
|로킷헬스케어(376900)|11:57:10|11:58:13|rising|7.34%|7.34%|`blocked_strength_momentum`/insufficient_history|0|1|-|2444.0|-|50/|0|11:57:10 blocked_strength_momentum:insufficient_history(+7.34%)|
|한올바이오파마(009420)|11:34:28|12:23:11|rising|7.13%|7.13%|`blocked_overbought`/blocked_ai_score_below_buy_score_threshold|6|2|diagnostic_quote_age_stale|5758.0|-|62/WAIT|0|11:34:28 blocked_overbought(+7.13%) -> 11:34:30 blocked_strength_momentum:insufficient_history(+7.13%) -> 11:54:18 blocked_overbought(+7.13%) -> 11:54:19 ai_confirmed(+7.13%) -> ... -> 12:23:11 blocked_overbought(+7.13%) -> 12:23:11 blocked_ai_score(+7.13%) -> 12:23:11 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+7.13%)|
|성신양회(004980)|11:55:30|13:39:08|rising|7.01%|7.01%|`blocked_strength_momentum`/insufficient_history|7|5|diagnostic_quote_age_stale|8428.0|-|74/WAIT|0|11:55:30 blocked_strength_momentum:insufficient_history(+7.01%) -> 12:18:18 blocked_liquidity(+7.01%) -> 12:18:19 ai_confirmed(+7.01%) -> 12:18:19 first_ai_wait(+7.01%) -> ... -> 13:39:08 wait65_79_ev_candidate(+7.01%) -> 13:39:08 first_ai_wait(+7.01%) -> 13:39:08 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+7.01%)|
|주성엔지니어링(036930)|11:34:38|12:50:09|rising|6.22%|6.22%|`blocked_strength_momentum`/below_buy_ratio|3|2|diagnostic_quote_age_stale|8466.0|-|61/WAIT|0|11:34:38 blocked_strength_momentum:below_buy_ratio(+6.22%) -> 12:04:51 blocked_vpw(+6.22%) -> 12:04:53 ai_confirmed(+6.22%) -> 12:04:53 first_ai_wait(+6.22%) -> ... -> 12:50:08 ai_confirmed(+6.22%) -> 12:50:09 first_ai_wait(+6.22%) -> 12:50:09 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+6.22%)|
|SK이터닉스(475150)|11:36:03|13:39:14|rising|5.99%|1.58%|`blocked_strength_momentum`/below_buy_ratio|1|9|diagnostic_quote_age_stale|11070.0|13:17:20|50/BUY|0|11:36:03 blocked_strength_momentum:below_buy_ratio(+5.99%) -> 11:38:22 blocked_strength_momentum:insufficient_history(+5.99%) -> 12:25:11 blocked_strength_momentum:below_buy_ratio(+1.59%) -> 12:29:36 ai_confirmed(+0.59%) -> ... -> 13:22:05 blocked_vpw(+1.58%) -> 13:22:05 blocked_ai_score:ai_score_50_buy_hold_override(+1.58%) -> 13:39:14 blocked_strength_momentum:below_buy_ratio(+1.58%)|
|HPSP(403870)|12:31:34|12:47:58|rising|4.94%|4.94%|`blocked_strength_momentum`/below_strength_base|0|6|-|6462.0|-|50/|0|12:31:34 blocked_strength_momentum:below_strength_base(+4.94%) -> 12:31:34 blocked_vpw(+4.94%) -> 12:31:34 blocked_ai_score:ai_score_50_buy_hold_override(+4.94%) -> 12:32:05 blocked_strength_momentum:below_strength_base(+4.94%) -> ... -> 12:47:58 blocked_strength_momentum:below_strength_base(+4.94%) -> 12:47:58 blocked_vpw(+4.94%) -> 12:47:58 blocked_ai_score:ai_score_50_buy_hold_override(+4.94%)|
|나노팀(417010)|11:43:14|11:43:14|rising|4.57%|4.57%|`blocked_overbought`/-|1|0|diagnostic_quote_age_stale|7441.0|-|50/|0|11:43:14 blocked_overbought(+4.57%)|
|티씨머티리얼즈(125020)|13:20:52|13:22:12|rising|4.25%|4.25%|`blocked_liquidity`/first_ai_wait_big_bite_not_confirmed|4|1|diagnostic_quote_age_stale|9412.0|-|62/WAIT|0|13:20:52 blocked_liquidity(+4.25%) -> 13:20:54 ai_confirmed(+4.25%) -> 13:20:54 first_ai_wait(+4.25%) -> 13:20:54 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+4.25%) -> 13:22:12 blocked_overbought(+4.25%) -> 13:22:12 blocked_strength_momentum:insufficient_history(+4.25%)|
|후성(093370)|12:25:03|13:31:04|rising|4.22%|4.22%|`blocked_liquidity`/first_ai_wait_big_bite_not_confirmed|6|3|diagnostic_quote_age_stale|7118.0|-|62/WAIT|0|12:25:03 blocked_liquidity(+4.22%) -> 12:25:05 ai_confirmed(+4.22%) -> 12:25:05 first_ai_wait(+4.22%) -> 12:25:05 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+4.22%) -> ... -> 13:31:04 ai_confirmed(+4.22%) -> 13:31:04 first_ai_wait(+4.22%) -> 13:31:04 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+4.22%)|
|일신방직(003200)|11:54:25|11:56:21|rising|3.75%|3.75%|`blocked_strength_momentum`/below_strength_base|1|2|diagnostic_quote_age_stale|4753.0|-|50/|0|11:54:25 blocked_strength_momentum:below_strength_base(+3.75%)|
|스피어(347700)|11:36:09|11:36:09|rising|3.62%|3.62%|`blocked_overbought`/ai_score_50_buy_hold_override|1|0|diagnostic_quote_age_stale|6325.0|-|50/|0|11:36:09 blocked_overbought(+3.62%) -> 11:36:09 blocked_ai_score:ai_score_50_buy_hold_override(+3.62%)|
|대원전선(006340)|13:25:54|13:25:54|rising|3.54%|3.54%|`blocked_strength_momentum`/insufficient_history|0|1|-|628.0|-|50/|0|13:25:54 blocked_strength_momentum:insufficient_history(+3.54%)|
|남화산업(111710)|11:59:16|13:22:50|rising|3.11%|0.85%|`blocked_overbought`/insufficient_history|6|7|diagnostic_quote_age_stale|8521.0|-|62/WAIT|0|11:59:16 blocked_overbought(+2.44%) -> 12:00:50 blocked_strength_momentum:insufficient_history(+2.44%) -> 12:01:06 blocked_overbought(+2.44%) -> 12:01:06 blocked_strength_momentum:below_window_buy_value(+2.44%) -> ... -> 13:22:50 blocked_liquidity(+0.85%) -> 13:22:50 blocked_ai_score(+0.85%) -> 13:22:50 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.85%)|
|져스텍(153890)|11:51:42|13:36:16|rising|2.97%|2.97%|`blocked_overbought`/insufficient_history|4|11|diagnostic_quote_age_stale|4955.0|13:35:20|78/BUY|0|11:51:42 blocked_overbought(+2.97%) -> 11:51:44 blocked_strength_momentum:insufficient_history(+2.97%) -> 12:13:12 blocked_overbought(+2.97%) -> 12:13:15 blocked_strength_momentum:insufficient_history(+2.97%) -> ... -> 13:36:09 entry_armed:qualification_passed(+2.97%) -> 13:36:09 budget_pass(+2.97%) -> 13:36:16 latency_block:latency_state_danger(+2.97%)|
|금호타이어(073240)|12:50:31|13:20:18|rising|2.85%|2.85%|`ai_confirmed`/first_ai_wait_big_bite_not_confirmed|0|0|-|607.0|-|50/WAIT|0|12:50:31 ai_confirmed(+2.85%) -> 12:50:34 first_ai_wait(+2.85%) -> 12:50:34 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+2.85%) -> 13:20:18 blocked_ai_score:ai_score_50_buy_hold_override(+2.85%)|
|대명에너지(389260)|11:50:25|13:35:46|rising|2.61%|2.61%|`blocked_strength_momentum`/below_strength_base|16|13|diagnostic_quote_age_stale|6944.0|13:23:07|62/WAIT|0|11:50:25 blocked_strength_momentum:below_strength_base(+1.57%) -> 11:51:00 blocked_vpw(+1.57%) -> 11:51:00 blocked_liquidity(+1.57%) -> 11:51:02 ai_confirmed(+1.57%) -> ... -> 13:35:46 ai_confirmed(+2.61%) -> 13:35:46 blocked_ai_score(+2.61%) -> 13:35:46 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+2.61%)|
|메디포스트(078160)|12:23:39|12:23:39|rising|2.45%|2.45%|`blocked_overbought`/-|0|1|-|969.0|-|50/|0|12:23:39 blocked_overbought(+2.45%)|
|제너셈(217190)|11:49:13|11:49:50|rising|2.43%|2.43%|`blocked_overbought`/below_window_buy_value|3|0|diagnostic_quote_age_stale|6858.0|-|50/|0|11:49:13 blocked_overbought(+2.43%) -> 11:49:13 blocked_strength_momentum:below_window_buy_value(+2.43%) -> 11:49:50 blocked_overbought(+2.43%)|
|LS ELECTRIC(010120)|11:39:36|13:34:14|rising|2.33%|1.81%|`blocked_ai_score`/ai_score_50_buy_hold_override|10|8|diagnostic_quote_age_stale|8549.0|-|50/WAIT|0|11:39:36 blocked_strength_momentum:below_buy_ratio(+2.33%) -> 11:39:36 blocked_vpw(+2.33%) -> 11:39:36 blocked_ai_score:ai_score_50_buy_hold_override(+2.33%) -> 11:47:52 blocked_strength_momentum:below_window_buy_value(+1.14%) -> ... -> 13:31:10 blocked_strength_momentum:below_buy_ratio(+1.81%) -> 13:31:10 blocked_vpw(+1.81%) -> 13:31:10 blocked_ai_score:ai_score_50_buy_hold_override(+1.81%)|
|애경케미칼(161000)|12:38:30|12:40:09|rising|2.33%|2.33%|`blocked_strength_momentum`/below_window_buy_value|2|4|diagnostic_quote_age_stale|7593.0|-|60/WAIT|0|12:38:30 blocked_strength_momentum:below_window_buy_value(+2.33%) -> 12:38:30 blocked_liquidity(+2.33%) -> 12:38:32 ai_confirmed(+2.33%) -> 12:38:32 first_ai_wait(+2.33%) -> 12:38:32 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+2.33%) -> 12:39:54 blocked_strength_momentum:below_window_buy_value(+2.33%)|
|파마리서치(214450)|13:33:10|13:33:58|rising|2.11%|2.11%|`ai_confirmed_terminal_no_budget`/first_ai_wait_big_bite_not_confirmed|0|0|-|173.0|-|62/WAIT|0|13:33:10 ai_confirmed(+2.11%) -> 13:33:12 first_ai_wait(+2.11%) -> 13:33:12 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+2.11%) -> 13:33:58 blocked_ai_score(+2.11%) -> 13:33:58 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+2.11%)|
|에코프로(086520)|11:35:51|13:15:15|rising|1.93%|1.93%|`blocked_overbought`/below_buy_ratio|7|9|diagnostic_quote_age_stale|9591.0|-|50/WAIT|0|11:35:51 blocked_overbought(+0.74%) -> 11:36:16 ai_confirmed(+0.74%) -> 11:36:18 blocked_ai_score(+0.74%) -> 11:36:18 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.74%) -> ... -> 13:05:43 blocked_strength_momentum:below_buy_ratio(+1.93%) -> 13:15:12 blocked_overbought(+1.93%) -> 13:15:15 blocked_strength_momentum:below_buy_ratio(+1.93%)|
|디앤디파마텍(347850)|11:33:31|13:32:39|rising|1.38%|1.38%|`blocked_overbought`/blocked_ai_score_below_buy_score_threshold|22|9|diagnostic_quote_age_stale|7990.0|-|58/WAIT|0|11:33:31 blocked_overbought(+1.38%) -> 11:33:38 ai_confirmed(+1.38%) -> 11:33:38 blocked_ai_score(+1.38%) -> 11:33:38 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+1.38%) -> ... -> 13:32:39 ai_confirmed(+1.38%) -> 13:32:39 blocked_ai_score(+1.38%) -> 13:32:39 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+1.38%)|
|모헨즈(006920)|12:50:54|13:17:12|rising|1.37%|1.37%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|0|2|-|17.0|-|50/|0|13:17:12 blocked_overbought(+1.37%) -> 13:17:12 blocked_liquidity(+1.37%) -> 13:17:12 blocked_ai_score:ai_score_50_buy_hold_override(+1.37%)|
|포스코인터내셔널(047050)|13:19:02|13:23:31|rising|1.30%|1.30%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|0|1|-|572.0|-|50/|0|13:20:21 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%) -> 13:23:31 blocked_strength_momentum:below_window_buy_value(+1.30%)|
|삼성E&A(028050)|11:35:35|13:08:12|rising|1.19%|1.19%|`ai_confirmed`/first_ai_wait_big_bite_not_confirmed|7|2|diagnostic_quote_age_stale|8304.0|-|62/USE_DEFENSIVE|0|11:35:35 ai_confirmed(+0.69%) -> 11:35:35 first_ai_wait(+0.69%) -> 11:35:35 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.69%) -> 11:38:00 ai_confirmed(+0.69%) -> ... -> 13:08:11 first_ai_wait(+1.19%) -> 13:08:11 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+1.19%) -> 13:08:12 entry_ai_price_canary_fallback:invalid_price(+1.19%)|
|리가켐바이오(141080)|11:40:29|11:40:29|rising|1.09%|1.09%|`ai_confirmed`/blocked_ai_score_below_buy_score_threshold|0|0|-|245.0|-|58/WAIT|0|11:40:29 ai_confirmed(+1.09%) -> 11:40:29 blocked_ai_score(+1.09%) -> 11:40:29 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+1.09%)|
|대우건설(047040)|12:07:22|13:12:32|rising|1.09%|0.75%|`ai_confirmed`/below_buy_ratio|0|3|-|2787.0|-|62/WAIT|0|12:07:22 blocked_strength_momentum:below_buy_ratio(+1.09%) -> 12:07:24 ai_confirmed(+1.09%) -> 12:07:24 blocked_ai_score(+1.09%) -> 12:07:24 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+1.09%) -> ... -> 13:12:30 ai_confirmed(+0.75%) -> 13:12:32 first_ai_wait(+0.75%) -> 13:12:32 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.75%)|
|아세아시멘트(183190)|12:17:31|13:34:56|rising|1.08%|1.08%|`blocked_strength_momentum`/insufficient_history|1|1|diagnostic_quote_age_stale|9934.0|-|50/|0|12:17:31 blocked_strength_momentum:insufficient_history(+1.08%) -> 13:34:56 blocked_liquidity(+1.08%) -> 13:34:56 blocked_ai_score:ai_score_50_buy_hold_override(+1.08%)|
|에이비엘바이오(298380)|11:31:43|12:57:31|rising|1.04%|0.00%|`blocked_overbought`/below_window_buy_value|4|1|diagnostic_quote_age_stale|7350.0|-|62/WAIT|0|11:31:43 blocked_overbought(+1.04%) -> 11:31:43 blocked_strength_momentum:below_window_buy_value(+1.04%) -> 11:56:46 blocked_overbought(+0.00%) -> 11:56:48 ai_confirmed(+0.00%) -> ... -> 12:57:31 ai_confirmed(+0.00%) -> 12:57:31 first_ai_wait(+0.00%) -> 12:57:31 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|
|삼성SDI(006400)|12:09:40|13:31:23|rising|1.00%|1.00%|`blocked_strength_momentum`/below_buy_ratio|6|5|diagnostic_quote_age_stale|7839.0|-|66/WAIT|0|12:09:40 ai_confirmed(+0.00%) -> 12:09:40 first_ai_wait(+0.00%) -> 12:09:40 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> 12:32:36 blocked_strength_momentum:below_buy_ratio(+0.00%) -> ... -> 13:31:23 wait65_79_ev_candidate(+1.00%) -> 13:31:23 first_ai_wait(+1.00%) -> 13:31:23 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+1.00%)|
|한화솔루션(009830)|13:17:56|13:18:13|rising|0.87%|0.87%|`ai_confirmed_terminal_no_budget`/below_buy_ratio|0|2|-|2766.0|-|58/WAIT|0|13:17:56 blocked_strength_momentum:below_buy_ratio(+0.87%) -> 13:17:56 blocked_vpw(+0.87%) -> 13:17:57 ai_confirmed(+0.87%) -> 13:17:57 first_ai_wait(+0.87%) -> 13:17:57 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.87%) -> 13:18:13 blocked_ai_score(+0.87%) -> 13:18:13 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.87%)|
|SK오션플랜트(100090)|13:18:37|13:18:41|rising|0.79%|0.79%|`blocked_liquidity`/first_ai_wait_big_bite_not_confirmed|2|1|diagnostic_quote_age_stale|7932.0|-|62/WAIT|0|13:18:37 blocked_liquidity(+0.79%) -> 13:18:41 ai_confirmed(+0.79%) -> 13:18:41 first_ai_wait(+0.79%) -> 13:18:41 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.79%)|
|지어소프트(051160)|12:07:11|12:16:15|rising|0.77%|0.77%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|0|0|-||-||0|-|
|삼성에스디에스(018260)|13:37:31|13:38:41|rising|0.76%|0.76%|`blocked_strength_momentum`/below_strength_base|5|6|diagnostic_quote_age_stale|7112.0|-|62/WAIT|0|13:37:31 blocked_strength_momentum:below_strength_base(+0.76%) -> 13:37:31 blocked_vpw(+0.76%) -> 13:37:31 blocked_liquidity(+0.76%) -> 13:37:32 ai_confirmed(+0.76%) -> ... -> 13:38:41 blocked_liquidity(+0.76%) -> 13:38:41 blocked_ai_score(+0.76%) -> 13:38:41 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.76%)|
|가온전선(000500)|13:14:30|13:15:04|rising|0.72%|0.72%|`ai_confirmed_terminal_no_budget`/below_buy_ratio|4|2|diagnostic_quote_age_stale|6538.0|-|62/WAIT|0|13:14:30 blocked_strength_momentum:below_buy_ratio(+0.72%) -> 13:14:30 blocked_vpw(+0.72%) -> 13:14:32 ai_confirmed(+0.72%) -> 13:14:32 first_ai_wait(+0.72%) -> 13:14:32 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.72%) -> 13:15:04 blocked_ai_score(+0.72%) -> 13:15:04 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.72%)|
|서산(079650)|11:57:30|13:38:13|rising|0.63%|0.63%|`ai_confirmed`/first_ai_wait_big_bite_not_confirmed|7|3|diagnostic_quote_age_stale|6666.0|-|62/WAIT|0|11:57:30 ai_confirmed(+0.63%) -> 11:57:30 blocked_ai_score(+0.63%) -> 11:57:30 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.63%) -> 12:14:03 blocked_liquidity(+0.63%) -> ... -> 13:38:13 ai_confirmed(+0.63%) -> 13:38:13 first_ai_wait(+0.63%) -> 13:38:13 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.63%)|
|알테오젠(196170)|12:00:34|12:00:34|rising|0.57%|0.57%|`ai_confirmed`/blocked_ai_score_below_buy_score_threshold|0|0|-|660.0|-|62/WAIT|0|12:00:34 ai_confirmed(+0.57%) -> 12:00:34 blocked_ai_score(+0.57%) -> 12:00:34 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.57%)|
|LG에너지솔루션(373220)|11:32:12|13:31:51|rising|0.39%|0.00%|`blocked_strength_momentum`/below_buy_ratio|9|11|diagnostic_quote_age_stale|8495.0|-|62/WAIT|0|11:32:12 blocked_strength_momentum:below_buy_ratio(+0.00%) -> 11:43:35 ai_confirmed(+0.39%) -> 11:43:35 first_ai_wait(+0.39%) -> 11:43:35 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.39%) -> ... -> 13:31:51 ai_confirmed(+0.00%) -> 13:31:51 first_ai_wait(+0.00%) -> 13:31:51 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|
|계룡건설(013580)|11:36:39|13:39:25|rising|0.22%|0.00%|`blocked_overbought`/below_window_buy_value|3|3|diagnostic_quote_age_stale|6396.0|-|50/|0|11:36:39 blocked_overbought(+0.22%) -> 11:36:45 blocked_strength_momentum:below_window_buy_value(+0.22%) -> 11:36:45 blocked_vpw(+0.22%) -> 11:36:45 blocked_liquidity(+0.22%) -> 11:36:45 blocked_ai_score:ai_score_50_buy_hold_override(+0.22%) -> 13:39:25 blocked_overbought(+0.00%) -> 13:39:25 blocked_strength_momentum:below_strength_base(+0.00%)|
|펩트론(087010)|11:30:01|13:02:43|flat_or_falling|0.00%|0.00%|`blocked_overbought`/below_window_buy_value|1|3|diagnostic_quote_age_stale|5355.0|-|50/|0|11:30:01 blocked_overbought(+0.00%) -> 11:30:06 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 13:02:19 blocked_overbought(+0.00%) -> 13:02:43 blocked_strength_momentum:insufficient_history(+0.00%)|
|씨어스(458870)|11:30:28|11:31:46|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|1|0|diagnostic_quote_age_stale|3242.0|-|50/|0|11:30:28 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 11:31:46 blocked_strength_momentum:insufficient_history(+0.00%)|
|포바이포(389140)|11:30:41|12:43:53|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|0|0|-||-||0|-|
|에이직랜드(445090)|11:32:39|12:50:55|flat_or_falling|0.00%|0.00%|`blocked_overbought`/-|1|1|diagnostic_quote_age_stale|7627.0|-|50/|0|11:32:39 blocked_overbought(+0.00%)|
|인바디(041830)|11:32:46|11:32:46|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|1|0|diagnostic_quote_age_stale|6860.0|-|50/|0|11:32:46 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|제닉(123330)|11:32:56|11:32:56|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|1|0|diagnostic_quote_age_stale|4591.0|-|50/|0|11:32:56 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|리브스메드(491000)|11:32:58|11:32:58|flat_or_falling|0.00%|0.00%|`blocked_overbought`/-|0|0|-|2650.0|-|50/|0|11:32:58 blocked_overbought(+0.00%)|
|오름테라퓨틱(475830)|11:33:00|13:24:36|flat_or_falling|0.00%|0.00%|`blocked_overbought`/below_window_buy_value|4|3|diagnostic_quote_age_stale|3592.0|-|50/WAIT|0|11:33:00 blocked_overbought(+0.00%) -> 11:33:02 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 11:33:04 ai_confirmed(+0.00%) -> 11:33:04 blocked_ai_score(+0.00%) -> ... -> 12:54:44 first_ai_wait(+0.00%) -> 12:54:44 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> 13:24:36 blocked_overbought(+0.00%)|
|동원시스템즈(014820)|11:33:05|12:41:13|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|0|0|-||-||0|-|
|갤럭시아머니트리(094480)|11:33:08|11:33:08|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/insufficient_history|1|0|diagnostic_quote_age_stale|4296.0|-|50/|0|11:33:08 blocked_strength_momentum:insufficient_history(+0.00%)|
|지투지바이오(456160)|11:33:58|12:56:38|flat_or_falling|0.00%|0.00%|`blocked_overbought`/below_window_buy_value|2|2|diagnostic_quote_age_stale|8001.0|-|50/|0|11:33:58 blocked_overbought(+0.00%) -> 11:34:14 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 12:56:38 blocked_overbought(+0.00%)|
|큐리옥스바이오시스템즈(445680)|11:34:04|11:35:44|flat_or_falling|0.00%|0.00%|`blocked_overbought`/below_window_buy_value|4|0|diagnostic_quote_age_stale|5682.0|-|62/WAIT|0|11:34:04 blocked_overbought(+0.00%) -> 11:34:18 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 11:34:18 blocked_liquidity(+0.00%) -> 11:34:20 ai_confirmed(+0.00%) -> 11:34:20 first_ai_wait(+0.00%) -> 11:34:20 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> 11:35:44 blocked_overbought(+0.00%) -> 11:35:44 blocked_strength_momentum:insufficient_history(+0.00%)|
|에스오에스랩(464080)|11:34:22|13:01:20|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|3|0|diagnostic_quote_age_stale|5190.0|-|50/|0|11:34:22 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 13:01:20 blocked_overbought(+0.00%) -> 13:01:20 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|지노믹트리(228760)|11:34:46|13:41:11|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|0|0|-||-||0|-|
|대한조선(439260)|11:34:47|11:37:39|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|0|0|-||-||0|-|
|엘앤씨바이오(290650)|11:34:54|11:34:54|flat_or_falling|0.00%|0.00%|`ai_confirmed`/first_ai_wait_big_bite_not_confirmed|2|0|diagnostic_quote_age_stale|8720.0|-|55/WAIT|0|11:34:54 ai_confirmed(+0.00%) -> 11:34:54 first_ai_wait(+0.00%) -> 11:34:54 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|
|에스엠(041510)|11:36:49|11:39:21|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|0|0|-||-||0|-|
|LG유플러스(032640)|11:36:49|11:39:21|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|0|0|-||-||0|-|
|세미파이브(490470)|11:38:13|11:39:11|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|2|4|diagnostic_quote_age_stale|7090.0|-|62/WAIT|0|11:38:13 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 11:39:09 blocked_vpw(+0.00%) -> 11:39:09 blocked_liquidity(+0.00%) -> 11:39:11 ai_confirmed(+0.00%) -> 11:39:11 first_ai_wait(+0.00%) -> 11:39:11 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|
|KH바텍(060720)|11:39:06|11:40:56|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|0|0|-||-||0|-|
|이엔셀(456070)|11:39:56|11:39:56|flat_or_falling|0.00%|0.00%|`blocked_overbought`/insufficient_history|2|0|diagnostic_quote_age_stale|4526.0|-|50/|0|11:39:56 blocked_overbought(+0.00%) -> 11:39:56 blocked_strength_momentum:insufficient_history(+0.00%)|
|에스비비테크(389500)|11:40:51|11:44:06|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|0|0|-||-||0|-|
|에스바이오메딕스(304360)|11:40:51|11:42:41|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|0|0|-||-||0|-|
|워트(396470)|11:40:52|12:22:40|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|0|0|-||-||0|-|
|AP시스템(265520)|11:40:52|11:42:41|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|0|0|-||-||0|-|
|원익QnC(074600)|11:40:52|13:29:48|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|0|0|-||-||0|-|
|광전자(017900)|11:40:52|11:42:41|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|0|0|-||-||0|-|
|LS(006260)|11:42:23|11:42:23|flat_or_falling|0.00%|0.00%|`ai_confirmed`/blocked_ai_score_below_buy_score_threshold|0|0|-|2263.0|-|62/WAIT|0|11:42:23 ai_confirmed(+0.00%) -> 11:42:23 blocked_ai_score(+0.00%) -> 11:42:23 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.00%)|
|HLB이노베이션(024850)|11:44:09|11:46:35|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|0|1|-|2887.0|-|50/|0|11:45:31 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|덕산하이메탈(077360)|11:44:09|12:31:02|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|2|4|diagnostic_quote_age_stale|6579.0|-|59/WAIT|0|11:45:55 blocked_strength_momentum:below_strength_base(+0.00%) -> 11:45:55 blocked_vpw(+0.00%) -> 11:45:55 blocked_liquidity(+0.00%) -> 11:45:57 ai_confirmed(+0.00%) -> 11:45:57 first_ai_wait(+0.00%) -> 11:45:57 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> 12:29:00 blocked_strength_momentum:below_strength_base(+0.00%)|
|자화전자(033240)|11:44:09|11:46:32|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|1|0|diagnostic_quote_age_stale|10090.0|-|50/|0|11:46:13 blocked_strength_momentum:below_strength_base(+0.00%)|
|에코앤드림(101360)|11:44:09|12:33:21|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|0|0|-||-||0|-|
|나무가(190510)|11:44:09|11:46:24|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|0|0|-||-||0|-|
|삼아알미늄(006110)|11:44:14|11:44:14|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_strength_base|1|0|diagnostic_quote_age_stale|8574.0|-|50/|0|11:44:14 blocked_strength_momentum:below_strength_base(+0.00%)|
|한양이엔지(045100)|11:44:56|11:44:56|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/insufficient_history|1|0|diagnostic_quote_age_stale|7157.0|-|50/|0|11:44:56 blocked_strength_momentum:insufficient_history(+0.00%)|
|산일전기(062040)|11:45:11|11:45:11|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_strength_base|0|1|-|514.0|-|50/|0|11:45:11 blocked_strength_momentum:below_strength_base(+0.00%)|
|SK아이이테크놀로지(361610)|11:45:25|13:04:57|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|0|3|-|634.0|-|50/|0|11:45:25 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 13:04:50 blocked_overbought(+0.00%) -> 13:04:57 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|한패스(408470)|11:46:04|13:36:26|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|0|1|-|961.0|-|50/|0|13:10:58 blocked_overbought(+0.00%)|
|카카오뱅크(323410)|11:46:40|12:25:32|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/insufficient_history|1|1|diagnostic_quote_age_stale|8147.0|-|50/|0|11:46:40 blocked_strength_momentum:insufficient_history(+0.00%) -> 12:25:32 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|현대모비스(012330)|11:47:24|11:47:26|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_strength_base|2|2|diagnostic_quote_age_stale|5358.0|-|62/WAIT|0|11:47:24 blocked_strength_momentum:below_strength_base(+0.00%) -> 11:47:24 blocked_vpw(+0.00%) -> 11:47:26 ai_confirmed(+0.00%) -> 11:47:26 first_ai_wait(+0.00%) -> 11:47:26 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|
|태웅(044490)|11:47:36|12:58:06|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|2|3|diagnostic_quote_age_stale|5929.0|-|50/WAIT|0|11:47:36 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 11:47:36 blocked_liquidity(+0.00%) -> 11:47:37 ai_confirmed(+0.00%) -> 11:47:37 first_ai_wait(+0.00%) -> 11:47:37 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> 12:58:06 blocked_overbought(+0.00%)|
|덕양에너젠(000010)|11:47:58|12:29:53|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|0|0|-||-||0|-|
|SNT에너지(100840)|11:47:58|11:50:30|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|0|0|-||-||0|-|
|서연이화(200880)|11:47:58|11:50:30|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|0|0|-||-||0|-|
|금강철강(053260)|11:47:58|13:20:32|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|0|0|-||-||0|-|
|한솔아이원스(114810)|11:47:58|11:50:30|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|0|0|-||-||0|-|
|오로스테크놀로지(322310)|11:48:01|11:48:01|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/insufficient_history|1|0|diagnostic_quote_age_stale|7838.0|-|50/|0|11:48:01 blocked_strength_momentum:insufficient_history(+0.00%)|
|아이에스동서(010780)|11:50:17|11:52:12|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_strength_base|1|1|diagnostic_quote_age_stale|14179.0|-|50/|0|11:50:17 blocked_strength_momentum:below_strength_base(+0.00%) -> 11:52:12 blocked_strength_momentum:insufficient_history(+0.00%)|
|한양디지텍(078350)|11:50:28|11:53:29|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|0|0|-|2348.0|-|50/|0|11:51:51 blocked_strength_momentum:below_strength_base(+0.00%)|
|IPARK현대산업개발(294870)|11:50:28|11:55:11|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|2|2|diagnostic_quote_age_stale|7239.0|-|62/WAIT|0|11:53:56 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 11:53:56 blocked_liquidity(+0.00%) -> 11:53:58 ai_confirmed(+0.00%) -> 11:53:58 first_ai_wait(+0.00%) -> 11:53:58 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|
|세아베스틸지주(001430)|11:51:59|11:55:11|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|0|0|-||-||0|-|
|SAMG엔터(419530)|11:53:00|11:53:00|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/insufficient_history|0|0|-|2365.0|-|50/|0|11:53:00 blocked_strength_momentum:insufficient_history(+0.00%)|
|한국화장품(123690)|11:54:22|11:56:10|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|0|0|-||-||0|-|
|동화기업(025900)|11:56:57|11:56:57|flat_or_falling|0.00%|0.00%|`blocked_overbought`/insufficient_history|2|0|diagnostic_quote_age_stale|10847.0|-|50/|0|11:56:57 blocked_overbought(+0.00%) -> 11:56:57 blocked_strength_momentum:insufficient_history(+0.00%)|
|루닛(328130)|11:57:14|12:58:14|flat_or_falling|0.00%|0.00%|`blocked_overbought`/below_window_buy_value|3|0|diagnostic_quote_age_stale|9273.0|-|50/|0|11:57:14 blocked_overbought(+0.00%) -> 12:58:14 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|엔켐(348370)|11:57:49|12:54:50|flat_or_falling|0.00%|0.00%|`blocked_overbought`/below_window_buy_value|4|2|diagnostic_quote_age_stale|8856.0|-|74/WAIT|0|11:57:49 blocked_overbought(+0.00%) -> 12:54:49 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 12:54:50 ai_confirmed(+0.00%) -> 12:54:50 wait65_79_ev_candidate(+0.00%) -> 12:54:50 first_ai_wait(+0.00%) -> 12:54:50 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|
|그린리소스(402490)|11:58:02|13:01:23|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|2|3|diagnostic_quote_age_stale|7312.0|-|58/WAIT|0|13:00:38 blocked_strength_momentum:below_strength_base(+0.00%) -> 13:00:38 blocked_vpw(+0.00%) -> 13:00:38 blocked_liquidity(+0.00%) -> 13:00:40 ai_confirmed(+0.00%) -> 13:00:40 first_ai_wait(+0.00%) -> 13:00:40 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|

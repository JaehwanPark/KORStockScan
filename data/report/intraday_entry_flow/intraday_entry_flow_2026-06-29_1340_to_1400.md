# 2026-06-29 13:40 이후 감시대상 BUY 전 흐름

- generated_at: 14:00
- source_events: /home/ubuntu/KORStockScan/data/runtime/sentinel_event_cache/buy_funnel_sentinel_events_2026-06-29.jsonl
- source_diagnostic: data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-29_1400_1340_goal.json
- event_window_since: 13:40
- symbol_count: 33
- rising_symbol_count_by_max_delta: 12
- rising_missed_buy_count_in_latest_diagnostic: 16
- rising_missed_symbol_count_in_report: 12
- real_submit_symbol_count_in_latest_diagnostic: 1
- buy_signal_or_pre_submit_pass_seen_symbols: 3
- stale_eval_symbol_count: 11
- rising_stale_eval_symbol_count: 6
- rising_fresh_only_symbol_count: 6
- stale_refresh_recovered_symbol_count: 20

## blocker rollup

- 7: `scalping_scanner_watching_runtime_skip` / `ws_snapshot_missing_or_zero`
- 6: `blocked_strength_momentum` / `below_window_buy_value`
- 4: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 4: `blocked_overbought` / `first_ai_wait_big_bite_not_confirmed`
- 2: `blocked_strength_momentum` / `insufficient_history`
- 2: `blocked_overbought` / `below_window_buy_value`
- 1: `blocked_overbought` / `below_buy_ratio`
- 1: `ai_confirmed` / `qualification_passed`
- 1: `ai_confirmed` / `first_ai_wait_big_bite_not_confirmed`
- 1: `blocked_strength_momentum` / `below_buy_ratio`
- 1: `blocked_liquidity` / `blocked_ai_score_below_buy_score_threshold`
- 1: `blocked_overbought` / `-`

## rising-symbol blocker rollup

- 4: `blocked_overbought` / `first_ai_wait_big_bite_not_confirmed`
- 2: `blocked_strength_momentum` / `insufficient_history`
- 1: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 1: `blocked_overbought` / `below_buy_ratio`
- 1: `ai_confirmed` / `qualification_passed`
- 1: `ai_confirmed` / `first_ai_wait_big_bite_not_confirmed`
- 1: `blocked_strength_momentum` / `below_buy_ratio`
- 1: `blocked_liquidity` / `blocked_ai_score_below_buy_score_threshold`

## rising fresh-only blocker rollup

- 2: `blocked_strength_momentum` / `insufficient_history`
- 2: `blocked_overbought` / `first_ai_wait_big_bite_not_confirmed`
- 1: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 1: `blocked_strength_momentum` / `below_buy_ratio`

## rising stale-mixed blocker rollup

- 2: `blocked_overbought` / `first_ai_wait_big_bite_not_confirmed`
- 1: `blocked_overbought` / `below_buy_ratio`
- 1: `ai_confirmed` / `qualification_passed`
- 1: `ai_confirmed` / `first_ai_wait_big_bite_not_confirmed`
- 1: `blocked_liquidity` / `blocked_ai_score_below_buy_score_threshold`

## stale-eval rollup

- 8: `ai_confirmed`
- 3: `blocked_overbought`

## stale-eval category rollup

- 11: `diagnostic_quote_age_stale`

## top rows by max delta

|종목|첫감시|마지막|상승여부|maxΔ|latestΔ|BUY전 주 blocker|stale평가|refresh회복|stale유형|max quote age|BUY전 통과신호|AI|실제submit|흐름|
|---|---:|---:|---|---:|---:|---|---:|---:|---|---:|---:|---:|---:|---|
|사피엔반도체(452430)|13:46:59|13:59:23|rising|19.66%|19.66%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|0|2|-|7786.0|-|57/WAIT|0|13:48:15 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 13:48:15 blocked_liquidity(+0.00%) -> 13:48:15 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%)|
|올릭스(226950)|13:51:27|13:51:32|rising|14.00%|14.00%|`blocked_overbought`/below_buy_ratio|3|2|diagnostic_quote_age_stale|3243.0|-|74/WAIT|0|13:51:27 blocked_overbought(+14.00%) -> 13:51:30 blocked_strength_momentum:below_buy_ratio(+14.00%) -> 13:51:32 ai_confirmed(+14.00%) -> 13:51:32 wait65_79_ev_candidate(+14.00%) -> 13:51:32 first_ai_wait(+14.00%) -> 13:51:32 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+14.00%)|
|광주신세계(037710)|13:54:15|13:54:15|rising|7.58%|7.58%|`blocked_strength_momentum`/insufficient_history|0|0|-|2474.0|-|50/|0|13:54:15 blocked_strength_momentum:insufficient_history(+7.58%)|
|한올바이오파마(009420)|13:46:31|13:51:50|rising|7.13%|7.13%|`ai_confirmed`/qualification_passed|4|4|diagnostic_quote_age_stale|6237.0|13:46:33|74/WAIT|0|13:46:31 ai_confirmed(+7.13%) -> 13:46:33 entry_armed:qualification_passed(+7.13%) -> 13:46:33 budget_pass(+7.13%) -> 13:46:42 latency_block:latency_state_danger(+7.13%) -> ... -> 13:51:41 entry_armed:qualification_passed(+7.13%) -> 13:51:41 budget_pass(+7.13%) -> 13:51:50 latency_block:latency_state_danger(+7.13%)|
|져스텍(153890)|13:47:29|13:52:51|rising|4.80%|4.80%|`blocked_overbought`/first_ai_wait_big_bite_not_confirmed|2|1|diagnostic_quote_age_stale|5955.0|-|50/BUY|0|13:47:29 blocked_overbought(+4.80%) -> 13:47:31 ai_confirmed(+4.80%) -> 13:47:31 wait65_79_ev_candidate(+4.80%) -> 13:47:32 first_ai_wait(+4.80%) -> 13:47:32 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+4.80%) -> 13:52:51 blocked_overbought(+4.80%) -> 13:52:51 blocked_strength_momentum:below_strength_base(+4.80%)|
|해태제과식품(101530)|13:41:48|13:41:48|rising|3.18%|3.18%|`blocked_strength_momentum`/insufficient_history|0|0|-|2500.0|-|50/|0|13:41:48 blocked_strength_momentum:insufficient_history(+3.18%)|
|LS ELECTRIC(010120)|13:52:09|13:52:09|rising|1.81%|1.81%|`ai_confirmed`/first_ai_wait_big_bite_not_confirmed|2|0|diagnostic_quote_age_stale|8556.0|-|62/WAIT|0|13:52:09 ai_confirmed(+1.81%) -> 13:52:09 first_ai_wait(+1.81%) -> 13:52:09 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+1.81%)|
|디앤디파마텍(347850)|13:52:18|13:52:20|rising|1.38%|1.38%|`blocked_overbought`/first_ai_wait_big_bite_not_confirmed|0|1|-|213.0|-|60/WAIT|0|13:52:18 blocked_overbought(+1.38%) -> 13:52:19 ai_confirmed(+1.38%) -> 13:52:20 first_ai_wait(+1.38%) -> 13:52:20 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+1.38%)|
|모헨즈(006920)|13:47:40|13:53:37|rising|1.37%|1.37%|`blocked_overbought`/first_ai_wait_big_bite_not_confirmed|4|4|diagnostic_quote_age_stale|8280.0|-|62/WAIT|0|13:47:40 blocked_overbought(+1.37%) -> 13:47:48 blocked_liquidity(+1.37%) -> 13:47:49 ai_confirmed(+1.37%) -> 13:47:50 first_ai_wait(+1.37%) -> ... -> 13:53:37 ai_confirmed(+1.37%) -> 13:53:37 first_ai_wait(+1.37%) -> 13:53:37 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+1.37%)|
|삼성SDI(006400)|13:50:53|13:52:36|rising|1.00%|1.00%|`blocked_strength_momentum`/below_buy_ratio|0|2|-|212.0|13:52:30|68/WAIT|0|13:50:53 blocked_strength_momentum:below_buy_ratio(+1.00%) -> 13:52:30 ai_confirmed(+1.00%) -> 13:52:30 wait65_79_ev_candidate(+1.00%) -> 13:52:30 entry_armed:qualification_passed(+1.00%) -> 13:52:30 budget_pass(+1.00%) -> 13:52:36 latency_block:latency_state_danger(+1.00%)|
|남화산업(111710)|13:47:57|13:55:01|rising|0.85%|0.85%|`blocked_overbought`/first_ai_wait_big_bite_not_confirmed|0|5|-|1019.0|-|62/WAIT|0|13:47:57 blocked_overbought(+0.85%) -> 13:47:57 blocked_liquidity(+0.85%) -> 13:47:59 ai_confirmed(+0.85%) -> 13:47:59 wait65_79_ev_candidate(+0.85%) -> ... -> 13:54:59 ai_confirmed(+0.85%) -> 13:55:01 first_ai_wait(+0.85%) -> 13:55:01 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.85%)|
|서산(079650)|13:40:28|13:53:57|rising|0.63%|0.63%|`blocked_liquidity`/blocked_ai_score_below_buy_score_threshold|5|2|diagnostic_quote_age_stale|5534.0|-|62/WAIT|0|13:40:28 blocked_liquidity(+0.63%) -> 13:40:29 ai_confirmed(+0.63%) -> 13:40:29 blocked_ai_score(+0.63%) -> 13:40:29 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.63%) -> ... -> 13:53:57 ai_confirmed(+0.63%) -> 13:53:57 first_ai_wait(+0.63%) -> 13:53:57 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.63%)|
|코스맥스(192820)|13:40:37|13:40:38|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|2|2|diagnostic_quote_age_stale|3514.0|-|62/WAIT|0|13:40:37 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 13:40:37 blocked_liquidity(+0.00%) -> 13:40:38 ai_confirmed(+0.00%) -> 13:40:38 first_ai_wait(+0.00%) -> 13:40:38 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|
|지엔씨에너지(119850)|13:40:47|13:40:47|flat_or_falling|0.00%|0.00%|`blocked_overbought`/-|0|1|-|2110.0|-|50/|0|13:40:47 blocked_overbought(+0.00%)|
|에이직랜드(445090)|13:41:53|13:41:53|flat_or_falling|0.00%|0.00%|`blocked_overbought`/insufficient_history|2|0|diagnostic_quote_age_stale|3498.0|-|50/|0|13:41:53 blocked_overbought(+0.00%) -> 13:41:53 blocked_strength_momentum:insufficient_history(+0.00%)|
|씨어스(458870)|13:42:01|13:42:02|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|0|3|-|2560.0|-|74/WAIT|0|13:42:01 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 13:42:01 blocked_vpw(+0.00%) -> 13:42:01 blocked_liquidity(+0.00%) -> 13:42:02 ai_confirmed(+0.00%) -> 13:42:02 wait65_79_ev_candidate(+0.00%) -> 13:42:02 first_ai_wait(+0.00%) -> 13:42:02 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|
|대한제강(084010)|13:42:23|13:43:27|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|0|0|-||-||0|-|
|원준(382840)|13:42:23|13:44:33|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|0|0|-||-||0|-|
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
|인바디(041830)|13:48:36|13:48:36|flat_or_falling|0.00%|0.00%|`blocked_overbought`/below_window_buy_value|2|0|diagnostic_quote_age_stale|6099.0|-|50/|0|13:48:36 blocked_overbought(+0.00%) -> 13:48:36 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|아이엠바이오로직스(493280)|13:49:25|13:49:25|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|0|1|-|856.0|-|50/|0|13:49:25 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|KoAct 팔란티어밸류체인액티브(000930)|13:50:01|13:54:09|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|0|0|-||-||0|-|
|HJ중공업(097230)|13:54:16|13:56:26|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|0|0|-||-||0|-|

# 2026-07-01 12:30 이후 감시대상 BUY 전 흐름

- generated_at: 2026-07-01T15:00:00+09:00
- source_events: /home/ubuntu/KORStockScan/data/runtime/sentinel_event_cache/buy_funnel_sentinel_events_2026-07-01.jsonl
- source_diagnostic: /home/ubuntu/KORStockScan/data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-07-01.json
- event_window_since: 2026-07-01T12:30:00+09:00
- event_window_until: 2026-07-01T15:00:00+09:00
- symbol_count: 43
- rising_symbol_count_by_max_delta: 16
- rising_missed_buy_count_in_latest_diagnostic: 14
- rising_missed_symbol_count_in_report: 14
- rising_missed_residual_excluding_forced_scout_symbol_count: 0
- rising_missed_forced_scout_event_count: 321
- rising_missed_forced_scout_symbol_count: 14
- rising_missed_forced_scout_residual_symbol_count: 14
- real_submit_symbol_count_in_latest_diagnostic: 0
- buy_signal_or_pre_submit_pass_seen_symbols: 3
- stale_eval_symbol_count: 25
- rising_stale_eval_symbol_count: 8
- rising_fresh_only_symbol_count: 8
- stale_refresh_recovered_symbol_count: 37

## forced scout observation

- event_count: 321
- symbol_count: 14
- symbols: 000500, 001260, 006340, 006360, 010120, 037350, 037710, 038500, 045100, 062040, 073240, 084370, 295310, 347700
- rising_missed_residual_symbols: 000500, 001260, 006340, 006360, 010120, 037350, 037710, 038500, 045100, 062040, 073240, 084370, 295310, 347700
- rising_missed_residual_excluding_forced_scout_symbols: -
- decision_authority: source_quality_only
- runtime_effect: False

## blocker rollup

- 14: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 10: `latency_block` / `latency_state_danger`
- 8: `blocked_strength_momentum` / `below_window_buy_value`
- 4: `blocked_strength_momentum` / `below_strength_base`
- 2: `blocked_overbought` / `below_buy_ratio`
- 1: `blocked_overbought` / `latency_state_danger`
- 1: `blocked_ai_score` / `below_buy_ratio`
- 1: `blocked_overbought` / `first_ai_wait_big_bite_not_confirmed`
- 1: `blocked_overbought` / `-`
- 1: `blocked_strength_momentum` / `below_buy_ratio`

## blocker taxonomy

- 369: `runtime_backpressure`
- 124: `strategy_reject`
- 72: `pre_submit_quality_guard`
- 23: `intended_guard`
- 21: `watch_budget_reallocated`
- 1: `source_freshness_blocker`

## suppressed non-major blocker counts

- 369: `runtime_backpressure` / `scalping_scanner_watching_runtime_skip` / `scanner_full_eval_loop_budget_deferred`
- 72: `pre_submit_quality_guard` / `latency_block` / `latency_state_danger`
- 12: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `stale_recovery_failed`
- 9: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `scanner_hardgate_prefilter`

## rising-symbol blocker rollup

- 10: `latency_block` / `latency_state_danger`
- 2: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 1: `blocked_overbought` / `latency_state_danger`
- 1: `blocked_overbought` / `below_buy_ratio`
- 1: `blocked_ai_score` / `below_buy_ratio`
- 1: `blocked_overbought` / `first_ai_wait_big_bite_not_confirmed`

## rising fresh-only blocker rollup

- 6: `latency_block` / `latency_state_danger`
- 1: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 1: `blocked_overbought` / `first_ai_wait_big_bite_not_confirmed`

## rising stale-mixed blocker rollup

- 4: `latency_block` / `latency_state_danger`
- 1: `blocked_overbought` / `latency_state_danger`
- 1: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 1: `blocked_overbought` / `below_buy_ratio`
- 1: `blocked_ai_score` / `below_buy_ratio`

## stale-eval rollup

- 13: `ai_confirmed`
- 7: `blocked_strength_momentum`
- 3: `ai_confirmed_terminal_no_budget`
- 1: `blocked_overbought`
- 1: `blocked_ai_score`

## stale-eval category rollup

- 25: `diagnostic_quote_age_stale`

## latency danger root cause

|종목|건수|top cause|spread ratio med/max|ws age med/max|spread ticks med/max|micro|bucket|
|---|---:|---|---:|---:|---:|---|---|
|스피어(347700)|82|spread_microstructure_wide|0.008432/0.010256|83.5/1141.0|5.0/6.0|neutral|spread=wide\|price=mid\|depth=thick\|sample=rich|
|가온전선(000500)|61|spread_microstructure_wide|0.008606/0.010526|97.0/17207.0|5.0/6.0|neutral|spread=wide\|price=high\|depth=normal\|sample=rich|
|금호타이어(073240)|53|spread_microstructure_wide|0.009921/0.01|150.0/17363.0|5.0/8.0|neutral|spread=wide\|price=low\|depth=thick\|sample=rich|
|한양이엔지(045100)|22|spread_microstructure_wide|0.006506/0.009498|219.5/19819.0|5.0/7.0|neutral|spread=wide\|price=mid\|depth=normal\|sample=rich|
|유진테크(084370)|14|spread_too_wide|0.011876/0.012107|461.0/17722.0|5.0/5.0|neutral|spread=wide\|price=high\|depth=normal\|sample=rich|
|LS ELECTRIC(010120)|13|spread_microstructure_wide|0.009542/0.009597|109.0/909.0|5.0/5.0|neutral|spread=wide\|price=high\|depth=thick\|sample=rich|
|에이치브이엠(295310)|12|spread_microstructure_wide|0.009479/0.011111|407.0/17574.0|6.0/7.0|neutral|spread=wide\|price=high\|depth=normal\|sample=rich|
|남광토건(001260)|11|quote_stale|0.0/0.0|12938.0/21990.0|0.0/0.0|insufficient|spread=not_available_no_bid_ask\|price=mid\|depth=thick\|sample=insufficient|
|성도이엔지(037350)|10|spread_microstructure_wide|0.005772/0.008865|689.5/19257.0|6.5/10.0|neutral|spread=wide\|price=mid\|depth=normal\|sample=rich|
|GS건설(006360)|9|spread_microstructure_wide|0.008432/0.010169|301.0/1427.0|5.0/6.0|neutral|spread=wide\|price=mid\|depth=thick\|sample=rich|
|대원전선(006340)|6|quote_stale|0.0/0.0|12859.5/18048.0|0.0/0.0|neutral|spread=tight\|price=mid\|depth=thick\|sample=rich|
|광주신세계(037710)|6|spread_microstructure_wide|0.00565/0.006742|108.0/724.0|5.0/6.0|neutral|spread=wide\|price=mid\|depth=normal\|sample=rich|

## top rows by max delta

|종목|첫감시|마지막|상승여부|maxΔ|latestΔ|BUY전 주 blocker|class|stale평가|refresh회복|stale유형|max quote age|BUY전 통과신호|AI|실제submit|흐름|
|---|---:|---:|---|---:|---:|---|---|---:|---:|---|---:|---:|---:|---:|---|
|한양이엔지(045100)|12:30:00|14:59:42|rising|10.26%|10.26%|`blocked_overbought`/latency_state_danger|-|56|57|diagnostic_quote_age_stale|21470.0|-|70/WAIT|0|12:30:00 latency_block:latency_state_danger(+10.26%) -> 12:39:35 blocked_overbought(+10.26%) -> 12:39:38 blocked_liquidity(+10.26%) -> 12:39:40 ai_confirmed(+10.26%) -> ... -> 14:00:13 blocked_ai_score(+10.26%) -> 14:00:13 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+10.26%) -> 14:33:50 latency_block:latency_state_danger(+10.26%)|
|남광토건(001260)|12:33:02|13:03:01|rising|6.37%|6.37%|`latency_block`/latency_state_danger|-|0|0|-||-|70/|0|12:33:02 latency_block:latency_state_danger(+6.37%)|
|금호타이어(073240)|13:18:24|14:37:53|rising|6.36%|6.36%|`latency_block`/latency_state_danger|-|3|61|diagnostic_quote_age_stale|17445.0|-|54/WAIT|0|13:18:24 latency_block:latency_state_danger(+6.36%) -> 14:24:50 entry_ai_price_canary_skip_order:orderbook_micro is bearish with negative OFI and soft execution strength(+6.36%) -> 14:27:01 blocked_strength_momentum:below_strength_base(+6.36%) -> 14:28:15 blocked_strength_momentum:insufficient_history(+6.36%) -> ... -> 14:37:53 blocked_vpw(+6.36%) -> 14:37:53 blocked_ai_score(+6.36%) -> 14:37:53 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+6.36%)|
|성도이엔지(037350)|12:55:46|14:45:47|rising|5.49%|5.49%|`latency_block`/latency_state_danger|-|0|7|-||-|70/|0|12:55:46 latency_block:latency_state_danger(+5.49%)|
|가온전선(000500)|12:34:09|14:58:36|rising|5.43%|5.43%|`latency_block`/latency_state_danger|-|3|69|diagnostic_quote_age_stale|3565.0|12:34:14|70/WAIT|0|12:34:09 blocked_overbought(+0.00%) -> 12:34:12 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 12:34:12 blocked_vpw(+0.00%) -> 12:34:14 ai_confirmed(+0.00%) -> ... -> 13:19:47 blocked_ai_score(+0.00%) -> 13:19:47 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.00%) -> 13:24:01 latency_block:latency_state_danger(+5.43%)|
|삼표시멘트(038500)|12:48:04|13:36:10|rising|3.65%|3.65%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|5|11|diagnostic_quote_age_stale|21133.0|-|61/WAIT|0|12:51:50 blocked_strength_momentum:below_buy_ratio(+0.00%) -> 12:51:50 blocked_vpw(+0.00%) -> 12:51:50 blocked_gap_from_scan(+0.00%) -> 12:51:50 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%) -> ... -> 13:36:10 blocked_liquidity(+3.65%) -> 13:36:10 blocked_ai_score(+3.65%) -> 13:36:10 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+3.65%)|
|스피어(347700)|12:33:55|14:39:40|rising|2.46%|2.46%|`latency_block`/latency_state_danger|-|10|90|diagnostic_quote_age_stale|7199.0|-|63/WAIT|0|12:33:55 blocked_overbought(+0.00%) -> 12:34:02 blocked_gap_from_scan(+0.00%) -> 12:34:04 ai_confirmed(+0.00%) -> 12:34:04 first_ai_wait(+0.00%) -> ... -> 14:39:40 ai_confirmed(+2.46%) -> 14:39:40 blocked_ai_score(+2.46%) -> 14:39:40 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+2.46%)|
|유진테크(084370)|12:30:31|14:58:50|rising|2.30%|2.30%|`latency_block`/latency_state_danger|-|1|12|diagnostic_quote_age_stale|11440.0|-|70/|0|12:30:31 blocked_strength_momentum:below_strength_base(+2.30%) -> 13:33:53 latency_block:latency_state_danger(+2.30%)|
|에이치브이엠(295310)|13:22:49|14:59:22|rising|1.86%|1.86%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|10|-||-|70/|0|13:28:29 latency_block:latency_state_danger(+1.86%)|
|산일전기(062040)|13:29:45|14:45:06|rising|1.82%|1.82%|`latency_block`/latency_state_danger|-|0|5|-||-|70/|0|13:29:45 latency_block:latency_state_danger(+1.82%)|
|GS건설(006360)|13:01:09|14:43:39|rising|1.53%|1.53%|`latency_block`/latency_state_danger|-|0|9|-||-|70/|0|13:01:09 latency_block:latency_state_danger(+1.53%)|
|LS ELECTRIC(010120)|12:30:08|14:43:56|rising|1.44%|1.44%|`latency_block`/latency_state_danger|-|0|13|-||-|70/|0|12:30:08 latency_block:latency_state_danger(+1.44%)|
|광주신세계(037710)|13:06:25|14:45:22|rising|1.43%|1.43%|`latency_block`/latency_state_danger|-|0|6|-||-|70/SKIP|0|13:06:25 latency_block:latency_state_danger(+1.43%) -> 13:09:31 entry_ai_price_canary_fallback:skip_low_confidence(+1.43%) -> 13:34:09 latency_block:latency_state_danger(+1.43%)|
|대원전선(006340)|12:32:31|14:49:16|rising|1.40%|1.40%|`blocked_overbought`/below_buy_ratio|-|12|15|diagnostic_quote_age_stale|16017.0|-|70/WAIT|0|12:32:31 blocked_overbought(+1.40%) -> 12:32:38 blocked_strength_momentum:below_buy_ratio(+1.40%) -> 12:33:33 blocked_overbought(+1.40%) -> 12:33:40 blocked_strength_momentum:below_buy_ratio(+1.40%) -> ... -> 12:54:12 blocked_ai_score(+1.40%) -> 12:54:12 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+1.40%) -> 13:38:46 latency_block:latency_state_danger(+1.40%)|
|이수페타시스(007660)|12:30:14|13:11:44|rising|0.72%|0.00%|`blocked_ai_score`/below_buy_ratio|-|6|7|diagnostic_quote_age_stale|5705.0|-|74/WAIT|0|12:30:14 blocked_strength_momentum:below_buy_ratio(+0.72%) -> 12:30:14 blocked_gap_from_scan(+0.72%) -> 12:30:16 ai_confirmed(+0.72%) -> 12:30:16 blocked_ai_score(+0.72%) -> ... -> 13:11:43 wait65_79_ev_candidate(+0.00%) -> 13:11:44 blocked_ai_score(+0.00%) -> 13:11:44 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.00%)|
|남화산업(111710)|12:35:08|12:35:10|rising|0.57%|0.57%|`blocked_overbought`/first_ai_wait_big_bite_not_confirmed|-|0|1|-|603.0|-|58/WAIT|0|12:35:08 blocked_overbought(+0.57%) -> 12:35:10 ai_confirmed(+0.57%) -> 12:35:10 first_ai_wait(+0.57%) -> 12:35:10 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.57%)|
|주성엔지니어링(036930)|12:33:09|14:47:52|flat_or_falling|0.00%|0.00%|`blocked_overbought`/below_buy_ratio|-|13|13|diagnostic_quote_age_stale|10546.0|-|50/BUY|0|12:33:09 blocked_overbought(+0.00%) -> 12:33:10 ai_confirmed(+0.00%) -> 12:33:10 wait65_79_ev_candidate(+0.00%) -> 12:33:10 first_ai_wait(+0.00%) -> ... -> 14:38:33 blocked_strength_momentum:below_buy_ratio(+0.00%) -> 14:47:43 blocked_overbought(+0.00%) -> 14:47:52 blocked_strength_momentum:below_buy_ratio(+0.00%)|
|피에스케이(319660)|12:34:25|13:21:15|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|-|6|9|diagnostic_quote_age_stale|7879.0|-|74/WAIT|0|12:34:25 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 12:34:25 blocked_vpw(+0.00%) -> 12:34:25 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%) -> 12:45:51 blocked_strength_momentum:below_window_buy_value(+0.00%) -> ... -> 13:12:46 blocked_ai_score(+0.00%) -> 13:12:46 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.00%) -> 13:21:15 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|태광(023160)|12:35:03|13:03:11|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|-|1|3|diagnostic_quote_age_stale|8909.0|-|50/|0|12:35:03 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 12:46:08 blocked_gap_from_scan(+0.00%) -> 12:46:08 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%) -> 12:53:06 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 13:03:11 blocked_gap_from_scan(+0.00%) -> 13:03:11 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%)|
|크래프톤(259960)|12:35:29|12:54:24|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|-|2|4|diagnostic_quote_age_stale|6578.0|-|64/WAIT|0|12:35:29 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 12:35:29 blocked_vpw(+0.00%) -> 12:35:31 ai_confirmed(+0.00%) -> 12:35:31 first_ai_wait(+0.00%) -> 12:35:31 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> 12:46:40 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|지엔씨에너지(119850)|12:35:50|12:54:56|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|-|1|3|diagnostic_quote_age_stale|7424.0|-|50/|0|12:35:50 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 12:46:55 blocked_liquidity(+0.00%) -> 12:46:55 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%) -> 12:54:56 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|제주은행(006220)|12:37:00|13:05:34|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|-|5|2|diagnostic_quote_age_stale|8817.0|-|62/WAIT|0|12:37:00 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 12:48:02 blocked_liquidity(+0.00%) -> 12:48:04 ai_confirmed(+0.00%) -> 12:48:04 first_ai_wait(+0.00%) -> 12:48:04 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> 13:05:34 blocked_strength_momentum:insufficient_history(+0.00%)|
|SK스퀘어(402340)|12:43:10|12:43:10|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_strength_base|-|0|1|-|36.0|-|50/|0|12:43:10 blocked_strength_momentum:below_strength_base(+0.00%)|
|서산(079650)|12:45:03|14:28:51|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|6|8|diagnostic_quote_age_stale|10155.0|-|74/WAIT|0|12:47:42 blocked_overbought(+0.00%) -> 12:47:45 blocked_strength_momentum:below_strength_base(+0.00%) -> 12:47:45 blocked_vpw(+0.00%) -> 12:47:45 blocked_liquidity(+0.00%) -> ... -> 13:16:37 wait65_79_ev_candidate(+0.00%) -> 13:16:37 blocked_ai_score(+0.00%) -> 13:16:37 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.00%)|
|동신건설(025950)|13:06:11|13:09:04|flat_or_falling|0.00%|0.00%|`blocked_overbought`/-|strategy_reject|0|3|-|1766.0|-|50/|0|13:07:21 blocked_overbought(+0.00%) -> 13:08:29 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|예스티(122640)|13:06:11|14:51:52|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|2|-|38.0|-|50/|0|13:07:50 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|SK이터닉스(475150)|13:07:37|14:47:00|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_buy_ratio|-|7|13|diagnostic_quote_age_stale|13687.0|13:07:39|58/WAIT|0|13:07:37 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 13:07:37 blocked_vpw(+0.00%) -> 13:07:39 ai_confirmed(+0.00%) -> 13:07:39 entry_armed:qualification_passed(+0.00%) -> ... -> 14:47:00 ai_confirmed(+0.00%) -> 14:47:00 first_ai_wait(+0.00%) -> 14:47:00 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|
|실리콘투(257720)|13:09:13|13:15:39|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|2|1|diagnostic_quote_age_stale|3438.0|-|64/WAIT|0|13:11:51 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 13:11:52 ai_confirmed(+0.00%) -> 13:11:52 first_ai_wait(+0.00%) -> 13:11:52 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|
|하이브(352820)|13:10:43|13:17:05|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|2|1|diagnostic_quote_age_stale|5458.0|-|54/WAIT|0|13:12:58 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 13:12:59 ai_confirmed(+0.00%) -> 13:12:59 first_ai_wait(+0.00%) -> 13:12:59 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|
|코세스(089890)|13:13:04|13:13:04|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_strength_base|-|0|1|-|28.0|-|50/|0|13:13:04 blocked_strength_momentum:below_strength_base(+0.00%)|
|일신방직(003200)|13:16:46|13:23:48|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|2|3|diagnostic_quote_age_stale|9685.0|-|60/WAIT|0|13:19:40 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 13:19:40 blocked_vpw(+0.00%) -> 13:19:40 blocked_liquidity(+0.00%) -> 13:19:41 ai_confirmed(+0.00%) -> 13:19:41 first_ai_wait(+0.00%) -> 13:19:41 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|
|서연(007860)|13:16:46|13:21:53|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|서부T&D(006730)|13:22:49|13:25:39|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|대한전선(001440)|13:26:35|13:26:35|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_strength_base|-|0|1|-|186.0|-|50/|0|13:26:35 blocked_strength_momentum:below_strength_base(+0.00%)|
|세명전기(017510)|13:26:47|13:26:57|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|-|2|3|diagnostic_quote_age_stale|6182.0|13:26:48|68/WAIT|0|13:26:47 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 13:26:47 blocked_liquidity(+0.00%) -> 13:26:48 ai_confirmed(+0.00%) -> 13:26:48 wait65_79_ev_candidate(+0.00%) -> 13:26:48 entry_armed:qualification_passed(+0.00%) -> 13:26:49 budget_pass(+0.00%) -> 13:26:57 latency_block:latency_state_danger(+0.00%)|
|일진전기(103590)|13:27:18|13:27:18|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|-|0|1|-|121.0|-|50/|0|13:27:18 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|비에이치아이(083650)|13:27:20|14:28:39|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|2|1|diagnostic_quote_age_stale|10055.0|-|62/WAIT|0|13:30:03 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 13:30:05 ai_confirmed(+0.00%) -> 13:30:05 first_ai_wait(+0.00%) -> 13:30:05 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|
|인텍플러스(064290)|13:28:51|14:28:39|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-|50/|0|13:30:41 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%)|
|티씨머티리얼즈(125020)|13:31:18|13:31:18|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|-|1|0|diagnostic_quote_age_stale|8904.0|-|50/|0|13:31:18 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|삼일씨엔에스(004440)|14:28:51|14:59:06|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|4|7|diagnostic_quote_age_stale|9820.0|-|60/WAIT|0|14:31:47 blocked_strength_momentum:below_strength_base(+0.00%) -> 14:31:47 blocked_vpw(+0.00%) -> 14:31:47 blocked_liquidity(+0.00%) -> 14:31:49 ai_confirmed(+0.00%) -> ... -> 14:46:47 ai_confirmed(+0.00%) -> 14:46:47 first_ai_wait(+0.00%) -> 14:46:47 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|
|티에스이(131290)|14:28:51|14:59:06|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|4|4|diagnostic_quote_age_stale|9442.0|-|62/WAIT|0|14:32:55 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 14:32:55 blocked_vpw(+0.00%) -> 14:32:57 ai_confirmed(+0.00%) -> 14:32:57 first_ai_wait(+0.00%) -> ... -> 14:46:28 ai_confirmed(+0.00%) -> 14:46:28 first_ai_wait(+0.00%) -> 14:46:28 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|
|글로벌텍스프리(204620)|14:28:51|14:31:59|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|키스트론(475430)|14:34:07|14:46:51|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_strength_base|-|4|3|diagnostic_quote_age_stale|8507.0|-|50/WAIT|0|14:34:07 blocked_strength_momentum:below_strength_base(+0.00%) -> 14:34:07 blocked_vpw(+0.00%) -> 14:34:07 blocked_liquidity(+0.00%) -> 14:34:10 ai_confirmed(+0.00%) -> 14:34:10 wait65_79_ev_candidate(+0.00%) -> 14:34:10 first_ai_wait(+0.00%) -> 14:34:10 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> 14:46:51 blocked_strength_momentum:below_strength_base(+0.00%)|

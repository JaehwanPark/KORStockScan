# 2026-06-30 08:00 이후 감시대상 BUY 전 흐름

- generated_at: 2026-06-30T10:30:00
- source_events: /home/ubuntu/KORStockScan/data/runtime/sentinel_event_cache/buy_funnel_sentinel_events_2026-06-30.jsonl
- source_diagnostic: data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-30_1030_goal.json
- event_window_since: 2026-06-30T08:00:00
- event_window_until: 2026-06-30T10:30:00
- symbol_count: 38
- rising_symbol_count_by_max_delta: 19
- rising_missed_buy_count_in_latest_diagnostic: 1
- rising_missed_symbol_count_in_report: 1
- real_submit_symbol_count_in_latest_diagnostic: 19
- buy_signal_or_pre_submit_pass_seen_symbols: 19
- stale_eval_symbol_count: 20
- rising_stale_eval_symbol_count: 12
- rising_fresh_only_symbol_count: 7
- stale_refresh_recovered_symbol_count: 25

## blocker rollup

- 18: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 16: `latency_block` / `latency_state_danger`
- 2: `blocked_strength_momentum` / `below_buy_ratio`
- 1: `scalping_scanner_watching_runtime_skip` / `entry_cooldown_active`
- 1: `blocked_strength_momentum` / `below_strength_base`

## blocker taxonomy

- 174: `runtime_backpressure`
- 141: `strategy_reject`
- 58: `intended_guard`
- 25: `pre_submit_quality_guard`
- 13: `source_freshness_blocker`
- 12: `watch_budget_reallocated`
- 4: `source_freshness_recovering`

## suppressed non-major blocker counts

- 174: `runtime_backpressure` / `scalping_scanner_watching_runtime_skip` / `scanner_full_eval_loop_budget_deferred`
- 16: `intended_guard` / `scalping_scanner_watching_runtime_skip` / `entry_cooldown_active`
- 10: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `scanner_hardgate_prefilter`
- 4: `source_freshness_recovering` / `scalping_scanner_watching_runtime_skip` / `ws_snapshot_missing_or_zero`
- 1: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `safety_cooldown_pool_blocked`
- 1: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `stale_recovery_failed`

## rising-symbol blocker rollup

- 15: `latency_block` / `latency_state_danger`
- 2: `blocked_strength_momentum` / `below_buy_ratio`
- 1: `scalping_scanner_watching_runtime_skip` / `entry_cooldown_active`
- 1: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`

## rising fresh-only blocker rollup

- 6: `latency_block` / `latency_state_danger`
- 1: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`

## rising stale-mixed blocker rollup

- 9: `latency_block` / `latency_state_danger`
- 2: `blocked_strength_momentum` / `below_buy_ratio`
- 1: `scalping_scanner_watching_runtime_skip` / `entry_cooldown_active`

## stale-eval rollup

- 10: `blocked_strength_momentum`
- 5: `ai_confirmed`
- 3: `blocked_overbought`
- 1: `ai_confirmed_terminal_no_budget`
- 1: `blocked_vpw`

## stale-eval category rollup

- 20: `diagnostic_quote_age_stale`

## top rows by max delta

|종목|첫감시|마지막|상승여부|maxΔ|latestΔ|BUY전 주 blocker|class|stale평가|refresh회복|stale유형|max quote age|BUY전 통과신호|AI|실제submit|흐름|
|---|---:|---:|---|---:|---:|---|---|---:|---:|---|---:|---:|---:|---:|---|
|가온전선(000500)|08:01:42|10:29:56|rising|20.44%|20.44%|`latency_block`/latency_state_danger|pre_submit_quality_guard|1|34|diagnostic_quote_age_stale|11646.0|08:04:23|62/WAIT|9|08:03:00 latency_block:latency_state_danger(+11.19%) -> 08:03:55 latency_block:safe_slippage_exceeded(+11.19%) -> 08:04:01 latency_block:latency_state_danger(+11.19%) -> 08:04:23 latency_pass:caution_normal_entry_allowed(+11.19%) -> ... -> 09:59:12 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+20.44%) -> 10:02:28 blocked_ai_score(+20.44%) -> 10:02:28 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+20.44%)|
|데브시스터즈(194480)|08:01:42|10:07:03|rising|6.43%|4.99%|`latency_block`/latency_state_danger|pre_submit_quality_guard|3|10|diagnostic_quote_age_stale|12250.0|08:03:26|60/WAIT|9|08:03:00 latency_block:latency_state_danger(+6.43%) -> 08:03:26 latency_pass:caution_normal_entry_allowed(+6.43%) -> 08:03:30 order_bundle_submitted:caution_normal_entry_allowed(+6.43%) -> 08:03:32 blocked_liquidity(+6.43%) -> ... -> 09:45:36 blocked_liquidity(+4.99%) -> 09:45:36 blocked_ai_score(+4.99%) -> 09:45:36 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+4.99%)|
|현대무벡스(319400)|08:03:13|10:25:30|rising|5.78%|4.10%|`latency_block`/latency_state_danger|pre_submit_quality_guard|1|58|diagnostic_quote_age_stale|10343.0|08:04:00|82/BUY|12|08:04:00 ai_confirmed(+0.00%) -> 08:04:00 entry_armed:qualification_passed(+0.00%) -> 08:04:01 budget_pass(+0.00%) -> 08:04:01 latency_block:latency_state_danger(+0.00%) -> ... -> 10:20:07 latency_block:latency_state_danger(+4.10%) -> 10:20:50 latency_pass:caution_normal_entry_allowed(+4.10%) -> 10:20:55 order_bundle_submitted:caution_normal_entry_allowed(+4.10%)|
|제룡전기(033100)|08:01:42|10:27:29|rising|5.25%|0.00%|`latency_block`/latency_state_danger|pre_submit_quality_guard|0|0|-||-||9|-|
|일진전기(103590)|08:06:14|10:26:40|rising|5.14%|5.14%|`latency_block`/latency_state_danger|pre_submit_quality_guard|0|43|-|2132.0|08:10:53|62/WAIT|12|08:07:18 blocked_strength_momentum:below_buy_ratio(+0.00%) -> 08:07:18 blocked_gap_from_scan(+0.00%) -> 08:07:20 ai_confirmed(+0.00%) -> 08:07:22 first_ai_wait(+0.00%) -> ... -> 10:20:00 latency_block:latency_state_danger(+5.14%) -> 10:22:17 latency_pass:caution_normal_entry_allowed(+5.14%) -> 10:22:28 order_bundle_submitted:caution_normal_entry_allowed(+5.14%)|
|SK이터닉스(475150)|10:11:58|10:26:54|rising|4.06%|4.06%|`latency_block`/latency_state_danger|pre_submit_quality_guard|0|6|-|2668.0|10:23:16|70/USE_DEFENSIVE|3|10:12:52 blocked_strength_momentum:below_strength_base(+0.00%) -> 10:12:52 blocked_vpw(+0.00%) -> 10:12:52 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%) -> 10:16:55 latency_block:latency_state_danger(+4.06%) -> ... -> 10:24:59 blocked_ai_score(+4.06%) -> 10:24:59 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+4.06%) -> 10:25:00 entry_ai_price_canary_fallback:pre_submit_price_guard(+4.06%)|
|LS ELECTRIC(010120)|08:01:43|10:29:56|rising|3.25%|3.25%|`latency_block`/latency_state_danger|pre_submit_quality_guard|5|122|diagnostic_quote_age_stale|221288.0|08:04:28|74/WAIT|6|08:03:07 latency_block:latency_state_danger(+1.73%) -> 08:04:28 latency_pass:caution_normal_entry_allowed(+2.60%) -> 08:04:43 latency_pass:caution_normal_entry_allowed(+2.60%) -> 08:04:47 order_bundle_submitted:caution_normal_entry_allowed(+2.60%) -> ... -> 10:19:40 first_ai_wait(+3.25%) -> 10:19:40 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+3.25%) -> 10:22:54 blocked_strength_momentum:below_strength_base(+3.25%)|
|삼화콘덴서(001820)|08:26:25|10:29:56|rising|2.57%|2.57%|`latency_block`/latency_state_danger|pre_submit_quality_guard|8|10|diagnostic_quote_age_stale|4569.0|-|54/WAIT|0|08:26:49 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 08:26:50 ai_confirmed(+0.00%) -> 08:26:52 first_ai_wait(+0.00%) -> 08:26:52 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> ... -> 10:28:23 blocked_strength_momentum:below_buy_ratio(+0.00%) -> 10:28:56 latency_block:latency_state_danger(+2.57%) -> 10:29:43 latency_block:caution_slippage_exceeded(+2.57%)|
|져스텍(153890)|10:06:54|10:18:35|rising|2.49%|2.49%|`latency_block`/latency_state_danger|pre_submit_quality_guard|6|6|diagnostic_quote_age_stale|19433.0|10:11:06|62/WAIT|3|10:07:44 blocked_overbought(+0.00%) -> 10:08:57 blocked_strength_momentum:below_buy_ratio(+0.00%) -> 10:08:57 blocked_vpw(+0.00%) -> 10:08:57 blocked_gap_from_scan(+0.00%) -> ... -> 10:17:09 blocked_liquidity(+2.49%) -> 10:17:09 blocked_ai_score(+2.49%) -> 10:17:09 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+2.49%)|
|두산에너빌리티(034020)|08:01:42|10:07:03|rising|2.02%|2.02%|`latency_block`/latency_state_danger|pre_submit_quality_guard|0|8|-|2444.0|08:03:39|65/WAIT|12|08:03:19 latency_block:latency_state_danger(+0.67%) -> 08:03:39 entry_ai_price_canary_skip_order:orderbook_micro is bearish with negative OFI and soft stop risk(+0.67%) -> 08:03:39 latency_pass:caution_normal_entry_allowed(+0.67%) -> 08:03:43 order_bundle_submitted:caution_normal_entry_allowed(+0.67%) -> ... -> 08:37:39 entry_ai_price_canary_fallback:above_best_ask(+2.02%) -> 10:03:16 latency_pass:caution_normal_entry_allowed(+2.02%) -> 10:03:20 order_bundle_submitted:caution_normal_entry_allowed(+2.02%)|
|엑스게이트(356680)|08:01:42|09:37:18|rising|1.60%|1.60%|`scalping_scanner_watching_runtime_skip`/entry_cooldown_active|intended_guard|10|2|diagnostic_quote_age_stale|6785.0|08:03:02|66/WAIT|9|08:03:02 entry_ai_price_canary_skip_order:orderbook_micro indicates bearish state with negative OFI and stale quote risk(+1.32%) -> 08:03:02 latency_pass:caution_normal_entry_allowed(+1.32%) -> 08:03:06 order_bundle_submitted:caution_normal_entry_allowed(+1.32%) -> 08:03:24 ai_confirmed(+1.32%) -> ... -> 09:35:16 blocked_ai_score(+1.60%) -> 09:35:16 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+1.60%) -> 09:35:17 entry_ai_price_canary_fallback:above_best_ask(+1.60%)|
|LG전자(066570)|08:04:44|10:29:30|rising|1.49%|0.00%|`latency_block`/latency_state_danger|pre_submit_quality_guard|1|2|diagnostic_quote_age_stale|5718.0|08:05:12|68/WAIT|3|08:05:01 latency_block:latency_state_danger(+1.49%) -> 08:05:12 latency_pass:caution_normal_entry_allowed(+1.49%) -> 08:05:16 order_bundle_submitted:caution_normal_entry_allowed(+1.49%) -> 08:06:20 blocked_strength_momentum:below_buy_ratio(+1.49%) -> ... -> 08:12:36 blocked_gap_from_scan(+1.49%) -> 08:12:36 blocked_ai_score(+1.49%) -> 08:12:36 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+1.49%)|
|화신(010690)|08:01:42|10:05:05|rising|1.33%|1.33%|`latency_block`/latency_state_danger|pre_submit_quality_guard|1|6|diagnostic_quote_age_stale|13295.0|08:04:49|62/WAIT|9|08:04:12 ai_confirmed(-0.18%) -> 08:04:13 first_ai_wait(-0.18%) -> 08:04:13 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(-0.18%) -> 08:04:49 latency_pass:caution_normal_entry_allowed(+1.33%) -> ... -> 09:47:14 latency_block:latency_state_danger(+1.33%) -> 09:48:21 latency_pass:caution_normal_entry_allowed(+1.33%) -> 09:48:25 order_bundle_submitted:caution_normal_entry_allowed(+1.33%)|
|테스(095610)|10:06:54|10:29:24|rising|1.24%|1.24%|`latency_block`/latency_state_danger|pre_submit_quality_guard|0|7|-|1673.0|10:23:34|62/WAIT|6|10:07:42 ai_confirmed(+0.00%) -> 10:07:42 first_ai_wait(+0.00%) -> 10:07:42 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> 10:10:28 blocked_strength_momentum:below_window_buy_value(+0.00%) -> ... -> 10:28:00 latency_block:latency_state_danger(+1.24%) -> 10:28:59 latency_pass:caution_normal_entry_allowed(+1.24%) -> 10:29:16 order_bundle_submitted:caution_normal_entry_allowed(+1.24%)|
|삼성중공업(010140)|08:04:44|10:04:56|rising|1.22%|1.22%|`latency_block`/latency_state_danger|pre_submit_quality_guard|0|20|-|2213.0|08:06:44|70/SKIP|6|08:05:02 latency_block:latency_state_danger(+1.22%) -> 08:06:44 entry_ai_price_canary_skip_order:orderbook_micro is bearish with negative OFI and low signal score(+1.22%) -> 08:06:44 latency_pass:caution_normal_entry_allowed(+1.22%) -> 08:06:48 order_bundle_submitted:caution_normal_entry_allowed(+1.22%) -> 08:21:32 latency_block:latency_state_danger(+1.22%) -> 08:28:51 latency_pass:caution_normal_entry_allowed(+1.22%) -> 08:28:55 order_bundle_submitted:caution_normal_entry_allowed(+1.22%) -> 09:31:28 latency_block:latency_state_danger(+1.22%)|
|SK하이닉스(000660)|08:01:42|10:02:05|rising|0.83%|0.83%|`blocked_strength_momentum`/below_buy_ratio|strategy_reject|1|0|diagnostic_quote_age_stale|15022.0|08:03:45|70/WAIT|3|08:03:45 latency_pass:caution_normal_entry_allowed(+0.83%) -> 08:03:49 order_bundle_submitted:caution_normal_entry_allowed(+0.83%) -> 08:04:41 blocked_strength_momentum:below_buy_ratio(+0.83%) -> 08:05:07 blocked_vpw(+0.83%) -> ... -> 08:11:29 blocked_vpw(+0.83%) -> 08:11:29 blocked_ai_score(+0.83%) -> 08:11:29 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.83%)|
|HL만도(204320)|08:06:14|10:18:55|rising|0.77%|0.77%|`latency_block`/latency_state_danger|pre_submit_quality_guard|8|13|diagnostic_quote_age_stale|14690.0|08:13:33|62/WAIT|9|08:07:23 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 08:07:25 ai_confirmed(+0.00%) -> 08:07:27 first_ai_wait(+0.00%) -> 08:07:27 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> ... -> 10:13:59 blocked_ai_score(+0.77%) -> 10:13:59 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.77%) -> 10:17:06 blocked_strength_momentum:insufficient_history(+0.77%)|
|원익IPS(240810)|08:01:42|10:29:56|rising|0.55%|0.55%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|5|-|3055.0|08:03:14|76/WAIT|12|08:03:14 latency_pass:caution_normal_entry_allowed(+0.55%) -> 08:03:18 order_bundle_submitted:caution_normal_entry_allowed(+0.55%) -> 08:20:59 latency_pass:caution_normal_entry_allowed(+0.12%) -> 08:21:14 order_bundle_submitted:caution_normal_entry_allowed(+0.12%) -> ... -> 10:00:06 blocked_gap_from_scan(+0.12%) -> 10:00:06 blocked_ai_score(+0.12%) -> 10:00:06 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.12%)|
|삼성전자(005930)|08:01:42|08:14:03|rising|0.46%|0.46%|`blocked_strength_momentum`/below_buy_ratio|strategy_reject|1|1|diagnostic_quote_age_stale|11438.0|08:03:50|61/WAIT|3|08:03:50 latency_pass:caution_normal_entry_allowed(+0.46%) -> 08:03:54 order_bundle_submitted:caution_normal_entry_allowed(+0.46%) -> 08:04:55 blocked_strength_momentum:insufficient_history(+0.46%) -> 08:05:05 blocked_strength_momentum:below_buy_ratio(+0.46%) -> ... -> 08:13:12 blocked_vpw(+0.46%) -> 08:13:12 blocked_ai_score(+0.46%) -> 08:13:12 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.46%)|
|애경케미칼(161000)|08:00:12|08:04:16|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-|314.0|-|60/WAIT|0|08:04:01 blocked_strength_momentum:below_strength_base(+0.00%) -> 08:04:01 blocked_vpw(+0.00%) -> 08:04:01 blocked_liquidity(+0.00%) -> 08:04:03 ai_confirmed(+0.00%) -> 08:04:04 first_ai_wait(+0.00%) -> 08:04:04 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> 08:04:16 blocked_strength_momentum:below_strength_base(+0.00%)|
|스피어(347700)|08:04:44|10:29:56|flat_or_falling|0.00%|0.00%|`latency_block`/latency_state_danger|pre_submit_quality_guard|4|7|diagnostic_quote_age_stale|4241.0|10:18:07|62/WAIT|0|08:05:24 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 10:10:15 blocked_overbought(+0.00%) -> 10:10:17 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 10:10:17 blocked_vpw(+0.00%) -> ... -> 10:28:32 ai_confirmed(+0.00%) -> 10:28:32 first_ai_wait(+0.00%) -> 10:28:32 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|
|산일전기(062040)|08:13:47|10:14:08|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|3|4|diagnostic_quote_age_stale|4716.0|-|62/WAIT|0|08:20:34 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 09:31:37 blocked_strength_momentum:below_strength_base(+0.00%) -> 09:31:37 blocked_vpw(+0.00%) -> 09:31:39 ai_confirmed(+0.00%) -> ... -> 10:09:37 ai_confirmed(+0.00%) -> 10:09:37 blocked_ai_score(+0.00%) -> 10:09:37 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.00%)|
|티로보틱스(117730)|08:21:45|08:22:30|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-|774.0|-|50/|0|08:22:24 blocked_overbought(+0.00%) -> 08:22:25 blocked_strength_momentum:below_buy_ratio(+0.00%)|
|나우로보틱스(459510)|08:23:16|08:23:54|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-|878.0|-|50/|0|08:23:47 blocked_overbought(+0.00%) -> 08:23:47 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|로보스타(090360)|08:23:16|08:23:54|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-|719.0|-|50/|0|08:23:49 blocked_strength_momentum:below_buy_ratio(+0.00%)|
|두산로보틱스(454910)|08:24:46|08:25:34|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-|850.0|-|50/|0|08:25:27 blocked_strength_momentum:below_buy_ratio(+0.00%)|
|에브리봇(270660)|10:05:54|10:13:10|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|2|3|diagnostic_quote_age_stale|5186.0|-|62/WAIT|0|10:07:00 blocked_overbought(+0.00%) -> 10:07:00 blocked_strength_momentum:below_strength_base(+0.00%) -> 10:09:40 blocked_overbought(+0.00%) -> 10:09:42 blocked_strength_momentum:below_strength_base(+0.00%) -> ... -> 10:09:44 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> 10:12:58 blocked_overbought(+0.00%) -> 10:12:58 blocked_strength_momentum:below_strength_base(+0.00%)|
|후성(093370)|10:06:54|10:13:10|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-|2443.0|-|62/WAIT|0|10:07:36 blocked_liquidity(+0.00%) -> 10:07:38 ai_confirmed(+0.00%) -> 10:07:39 first_ai_wait(+0.00%) -> 10:07:39 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> ... -> 10:09:47 blocked_ai_score(+0.00%) -> 10:09:47 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.00%) -> 10:13:01 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|삼성전기(009150)|10:06:54|10:29:56|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|8|2|diagnostic_quote_age_stale|13427.0|-|58/WAIT|0|10:09:11 ai_confirmed(+0.00%) -> 10:09:11 first_ai_wait(+0.00%) -> 10:09:11 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> 10:11:48 blocked_strength_momentum:below_buy_ratio(+0.00%) -> ... -> 10:22:12 ai_confirmed(+0.00%) -> 10:22:12 first_ai_wait(+0.00%) -> 10:22:12 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|
|시노펙스(025320)|10:07:55|10:12:04|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|2|0|diagnostic_quote_age_stale|8577.0|-|50/|0|10:09:04 blocked_overbought(+0.00%) -> 10:09:04 blocked_strength_momentum:below_buy_ratio(+0.00%) -> 10:11:38 blocked_overbought(+0.00%) -> 10:11:40 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|미래산업(025560)|10:10:57|10:29:51|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|4|-|2841.0|-|64/WAIT|0|10:12:53 blocked_overbought(+0.00%) -> 10:12:55 blocked_strength_momentum:below_buy_ratio(+0.00%) -> 10:12:55 blocked_vpw(+0.00%) -> 10:12:56 ai_confirmed(+0.00%) -> ... -> 10:21:49 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 10:26:32 blocked_overbought(+0.00%) -> 10:26:36 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|씨어스(458870)|10:12:58|10:15:22|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|주성엔지니어링(036930)|10:13:59|10:29:51|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|2|4|diagnostic_quote_age_stale|3682.0|-|60/WAIT|0|10:15:58 blocked_strength_momentum:below_buy_ratio(+0.00%) -> 10:15:58 blocked_vpw(+0.00%) -> 10:16:00 ai_confirmed(+0.00%) -> 10:16:00 first_ai_wait(+0.00%) -> 10:16:00 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> 10:21:43 blocked_strength_momentum:below_buy_ratio(+0.00%)|
|금호건설(002990)|10:15:00|10:29:56|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|4|5|diagnostic_quote_age_stale|3652.0|-|62/WAIT|0|10:18:10 blocked_overbought(+0.00%) -> 10:18:12 blocked_strength_momentum:below_strength_base(+0.00%) -> 10:18:12 blocked_vpw(+0.00%) -> 10:18:14 ai_confirmed(+0.00%) -> ... -> 10:28:44 ai_confirmed(+0.00%) -> 10:28:44 first_ai_wait(+0.00%) -> 10:28:44 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|
|키스트론(475430)|10:29:30|10:29:56|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|신성델타테크(065350)|08:04:44|08:05:27|flat_or_falling|-0.14%|-0.14%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-|161.0|-|50/|0|08:05:25 blocked_strength_momentum:below_window_buy_value(-0.14%)|
|한미반도체(042700)|08:01:43|08:05:36|flat_or_falling|-0.19%|-0.19%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-|221.0|-|50/|0|08:04:10 blocked_strength_momentum:below_strength_base(-0.19%) -> 08:04:10 blocked_vpw(-0.19%) -> 08:04:10 blocked_ai_score:ai_score_50_buy_hold_override(-0.19%)|
|에코프로비엠(247540)|08:01:43|10:22:57|flat_or_falling|-1.41%|-1.41%|`blocked_strength_momentum`/below_strength_base|strategy_reject|9|7|diagnostic_quote_age_stale|194169.0|08:03:08|76/WAIT|9|08:03:08 latency_pass:caution_normal_entry_allowed(-1.41%) -> 08:03:12 order_bundle_submitted:caution_normal_entry_allowed(-1.41%) -> 08:21:18 latency_pass:caution_normal_entry_allowed(-1.41%) -> 08:21:28 order_bundle_submitted:caution_normal_entry_allowed(-1.41%) -> ... -> 10:15:01 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(-1.41%) -> 10:18:43 blocked_strength_momentum:insufficient_history(-1.41%) -> 10:19:42 blocked_strength_momentum:below_strength_base(-1.41%)|

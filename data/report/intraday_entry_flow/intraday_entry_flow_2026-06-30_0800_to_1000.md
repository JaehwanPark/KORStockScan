# 2026-06-30 08:00 이후 감시대상 BUY 전 흐름

- generated_at: 2026-06-30T10:00:00
- source_events: /home/ubuntu/KORStockScan/data/runtime/sentinel_event_cache/buy_funnel_sentinel_events_2026-06-30.jsonl
- source_diagnostic: data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-30_1000_goal.json
- event_window_since: 2026-06-30T08:00:00
- event_window_until: 2026-06-30T10:00:00
- symbol_count: 26
- rising_symbol_count_by_max_delta: 15
- rising_missed_buy_count_in_latest_diagnostic: 0
- rising_missed_symbol_count_in_report: 0
- real_submit_symbol_count_in_latest_diagnostic: 16
- buy_signal_or_pre_submit_pass_seen_symbols: 15
- stale_eval_symbol_count: 10
- rising_stale_eval_symbol_count: 9
- rising_fresh_only_symbol_count: 6
- stale_refresh_recovered_symbol_count: 14

## blocker rollup

- 14: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 9: `scalping_scanner_watching_runtime_skip` / `entry_cooldown_active`
- 2: `blocked_strength_momentum` / `below_buy_ratio`
- 1: `blocked_strength_momentum` / `below_strength_base`

## blocker taxonomy

- 254: `runtime_backpressure`
- 109: `strategy_reject`
- 48: `intended_guard`
- 9: `watch_budget_reallocated`

## suppressed non-major blocker counts

- 254: `runtime_backpressure` / `scalping_scanner_watching_runtime_skip` / `scanner_full_eval_loop_budget_deferred`
- 19: `intended_guard` / `scalping_scanner_watching_runtime_skip` / `entry_cooldown_active`
- 8: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `scanner_hardgate_prefilter`
- 1: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `safety_cooldown_pool_blocked`

## rising-symbol blocker rollup

- 9: `scalping_scanner_watching_runtime_skip` / `entry_cooldown_active`
- 3: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 2: `blocked_strength_momentum` / `below_buy_ratio`
- 1: `blocked_strength_momentum` / `below_strength_base`

## rising fresh-only blocker rollup

- 3: `scalping_scanner_watching_runtime_skip` / `entry_cooldown_active`
- 2: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 1: `blocked_strength_momentum` / `below_strength_base`

## rising stale-mixed blocker rollup

- 6: `scalping_scanner_watching_runtime_skip` / `entry_cooldown_active`
- 2: `blocked_strength_momentum` / `below_buy_ratio`
- 1: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`

## stale-eval rollup

- 7: `blocked_strength_momentum`
- 1: `ai_confirmed_terminal_no_budget`
- 1: `ai_confirmed`
- 1: `blocked_vpw`

## stale-eval category rollup

- 10: `diagnostic_quote_age_stale`

## top rows by max delta

|종목|첫감시|마지막|상승여부|maxΔ|latestΔ|BUY전 주 blocker|class|stale평가|refresh회복|stale유형|max quote age|BUY전 통과신호|AI|실제submit|흐름|
|---|---:|---:|---|---:|---:|---|---|---:|---:|---|---:|---:|---:|---:|---|
|가온전선(000500)|08:01:42|09:59:57|rising|20.44%|20.44%|`scalping_scanner_watching_runtime_skip`/entry_cooldown_active|intended_guard|1|34|diagnostic_quote_age_stale|11646.0|08:04:23|62/WAIT|9|08:03:00 latency_block:latency_state_danger(+11.19%) -> 08:03:55 latency_block:safe_slippage_exceeded(+11.19%) -> 08:04:01 latency_block:latency_state_danger(+11.19%) -> 08:04:23 latency_pass:caution_normal_entry_allowed(+11.19%) -> ... -> 09:55:45 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+20.44%) -> 09:59:12 blocked_ai_score(+20.44%) -> 09:59:12 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+20.44%)|
|데브시스터즈(194480)|08:01:42|09:59:33|rising|6.43%|4.99%|`scalping_scanner_watching_runtime_skip`/entry_cooldown_active|intended_guard|3|10|diagnostic_quote_age_stale|12250.0|08:03:26|60/WAIT|9|08:03:00 latency_block:latency_state_danger(+6.43%) -> 08:03:26 latency_pass:caution_normal_entry_allowed(+6.43%) -> 08:03:30 order_bundle_submitted:caution_normal_entry_allowed(+6.43%) -> 08:03:32 blocked_liquidity(+6.43%) -> ... -> 09:45:36 blocked_liquidity(+4.99%) -> 09:45:36 blocked_ai_score(+4.99%) -> 09:45:36 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+4.99%)|
|현대무벡스(319400)|08:03:13|09:59:47|rising|5.78%|4.10%|`scalping_scanner_watching_runtime_skip`/entry_cooldown_active|intended_guard|1|45|diagnostic_quote_age_stale|10343.0|08:04:00|82/BUY|6|08:04:00 ai_confirmed(+0.00%) -> 08:04:00 entry_armed:qualification_passed(+0.00%) -> 08:04:01 budget_pass(+0.00%) -> 08:04:01 latency_block:latency_state_danger(+0.00%) -> ... -> 08:24:18 blocked_ai_score(+4.10%) -> 08:24:18 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+4.10%) -> 09:31:02 latency_block:latency_state_danger(+4.10%)|
|제룡전기(033100)|08:01:42|09:59:37|rising|5.25%|5.25%|`scalping_scanner_watching_runtime_skip`/entry_cooldown_active|intended_guard|0|0|-||-||6|-|
|일진전기(103590)|08:06:14|09:46:27|rising|5.14%|5.14%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|36|-|2132.0|08:10:53|62/WAIT|6|08:07:18 blocked_strength_momentum:below_buy_ratio(+0.00%) -> 08:07:18 blocked_gap_from_scan(+0.00%) -> 08:07:20 ai_confirmed(+0.00%) -> 08:07:22 first_ai_wait(+0.00%) -> ... -> 09:45:15 latency_pass:caution_normal_entry_allowed(+5.14%) -> 09:45:19 order_bundle_submitted:caution_normal_entry_allowed(+5.14%) -> 09:45:51 blocked_strength_momentum:below_strength_base(+5.14%)|
|LS ELECTRIC(010120)|08:01:43|09:59:33|rising|3.25%|3.25%|`scalping_scanner_watching_runtime_skip`/entry_cooldown_active|intended_guard|0|122|-|1623.0|08:04:28|71/WAIT|6|08:03:07 latency_block:latency_state_danger(+1.73%) -> 08:04:28 latency_pass:caution_normal_entry_allowed(+2.60%) -> 08:04:43 latency_pass:caution_normal_entry_allowed(+2.60%) -> 08:04:47 order_bundle_submitted:caution_normal_entry_allowed(+2.60%) -> ... -> 09:54:24 blocked_gap_from_scan(+3.25%) -> 09:54:24 blocked_ai_score(+3.25%) -> 09:54:24 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+3.25%)|
|두산에너빌리티(034020)|08:01:42|09:59:50|rising|2.02%|2.02%|`scalping_scanner_watching_runtime_skip`/entry_cooldown_active|intended_guard|0|7|-|2444.0|08:03:39|65/WAIT|9|08:03:19 latency_block:latency_state_danger(+0.67%) -> 08:03:39 entry_ai_price_canary_skip_order:orderbook_micro is bearish with negative OFI and soft stop risk(+0.67%) -> 08:03:39 latency_pass:caution_normal_entry_allowed(+0.67%) -> 08:03:43 order_bundle_submitted:caution_normal_entry_allowed(+0.67%) -> ... -> 08:37:38 blocked_ai_score(+2.02%) -> 08:37:38 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+2.02%) -> 08:37:39 entry_ai_price_canary_fallback:above_best_ask(+2.02%)|
|엑스게이트(356680)|08:01:42|09:37:18|rising|1.60%|1.60%|`scalping_scanner_watching_runtime_skip`/entry_cooldown_active|intended_guard|10|2|diagnostic_quote_age_stale|6785.0|08:03:02|66/WAIT|9|08:03:02 entry_ai_price_canary_skip_order:orderbook_micro indicates bearish state with negative OFI and stale quote risk(+1.32%) -> 08:03:02 latency_pass:caution_normal_entry_allowed(+1.32%) -> 08:03:06 order_bundle_submitted:caution_normal_entry_allowed(+1.32%) -> 08:03:24 ai_confirmed(+1.32%) -> ... -> 09:35:16 blocked_ai_score(+1.60%) -> 09:35:16 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+1.60%) -> 09:35:17 entry_ai_price_canary_fallback:above_best_ask(+1.60%)|
|LG전자(066570)|08:04:44|08:27:55|rising|1.49%|0.00%|`scalping_scanner_watching_runtime_skip`/entry_cooldown_active|intended_guard|1|2|diagnostic_quote_age_stale|5718.0|08:05:12|68/WAIT|3|08:05:01 latency_block:latency_state_danger(+1.49%) -> 08:05:12 latency_pass:caution_normal_entry_allowed(+1.49%) -> 08:05:16 order_bundle_submitted:caution_normal_entry_allowed(+1.49%) -> 08:06:20 blocked_strength_momentum:below_buy_ratio(+1.49%) -> ... -> 08:12:36 blocked_gap_from_scan(+1.49%) -> 08:12:36 blocked_ai_score(+1.49%) -> 08:12:36 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+1.49%)|
|화신(010690)|08:01:42|09:59:33|rising|1.33%|1.33%|`scalping_scanner_watching_runtime_skip`/entry_cooldown_active|intended_guard|1|6|diagnostic_quote_age_stale|13295.0|08:04:49|62/WAIT|9|08:04:12 ai_confirmed(-0.18%) -> 08:04:13 first_ai_wait(-0.18%) -> 08:04:13 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(-0.18%) -> 08:04:49 latency_pass:caution_normal_entry_allowed(+1.33%) -> ... -> 09:47:14 latency_block:latency_state_danger(+1.33%) -> 09:48:21 latency_pass:caution_normal_entry_allowed(+1.33%) -> 09:48:25 order_bundle_submitted:caution_normal_entry_allowed(+1.33%)|
|삼성중공업(010140)|08:04:44|09:59:33|rising|1.22%|1.22%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|17|-|2213.0|08:06:44|70/SKIP|6|08:05:02 latency_block:latency_state_danger(+1.22%) -> 08:06:44 entry_ai_price_canary_skip_order:orderbook_micro is bearish with negative OFI and low signal score(+1.22%) -> 08:06:44 latency_pass:caution_normal_entry_allowed(+1.22%) -> 08:06:48 order_bundle_submitted:caution_normal_entry_allowed(+1.22%) -> 08:21:32 latency_block:latency_state_danger(+1.22%) -> 08:28:51 latency_pass:caution_normal_entry_allowed(+1.22%) -> 08:28:55 order_bundle_submitted:caution_normal_entry_allowed(+1.22%) -> 09:31:28 latency_block:latency_state_danger(+1.22%)|
|SK하이닉스(000660)|08:01:42|09:59:33|rising|0.83%|0.83%|`blocked_strength_momentum`/below_buy_ratio|strategy_reject|1|0|diagnostic_quote_age_stale|15022.0|08:03:45|70/WAIT|3|08:03:45 latency_pass:caution_normal_entry_allowed(+0.83%) -> 08:03:49 order_bundle_submitted:caution_normal_entry_allowed(+0.83%) -> 08:04:41 blocked_strength_momentum:below_buy_ratio(+0.83%) -> 08:05:07 blocked_vpw(+0.83%) -> ... -> 08:11:29 blocked_vpw(+0.83%) -> 08:11:29 blocked_ai_score(+0.83%) -> 08:11:29 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.83%)|
|HL만도(204320)|08:06:14|09:59:33|rising|0.77%|0.77%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|3|9|diagnostic_quote_age_stale|7720.0|08:13:33|62/WAIT|6|08:07:23 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 08:07:25 ai_confirmed(+0.00%) -> 08:07:27 first_ai_wait(+0.00%) -> 08:07:27 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> ... -> 08:27:02 latency_pass:caution_normal_entry_allowed(+0.77%) -> 08:27:07 order_bundle_submitted:caution_normal_entry_allowed(+0.77%) -> 09:31:30 latency_block:latency_state_danger(+0.77%)|
|원익IPS(240810)|08:01:42|09:59:30|rising|0.55%|0.12%|`blocked_strength_momentum`/below_strength_base|strategy_reject|0|3|-|2803.0|08:03:14|75/WAIT|12|08:03:14 latency_pass:caution_normal_entry_allowed(+0.55%) -> 08:03:18 order_bundle_submitted:caution_normal_entry_allowed(+0.55%) -> 08:20:59 latency_pass:caution_normal_entry_allowed(+0.12%) -> 08:21:14 order_bundle_submitted:caution_normal_entry_allowed(+0.12%) -> ... -> 09:56:48 blocked_gap_from_scan(+0.12%) -> 09:56:48 blocked_ai_score(+0.12%) -> 09:56:48 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.12%)|
|삼성전자(005930)|08:01:42|08:14:03|rising|0.46%|0.46%|`blocked_strength_momentum`/below_buy_ratio|strategy_reject|1|1|diagnostic_quote_age_stale|11438.0|08:03:50|61/WAIT|3|08:03:50 latency_pass:caution_normal_entry_allowed(+0.46%) -> 08:03:54 order_bundle_submitted:caution_normal_entry_allowed(+0.46%) -> 08:04:55 blocked_strength_momentum:insufficient_history(+0.46%) -> 08:05:05 blocked_strength_momentum:below_buy_ratio(+0.46%) -> ... -> 08:13:12 blocked_vpw(+0.46%) -> 08:13:12 blocked_ai_score(+0.46%) -> 08:13:12 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.46%)|
|애경케미칼(161000)|08:00:12|08:04:16|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-|314.0|-|60/WAIT|0|08:04:01 blocked_strength_momentum:below_strength_base(+0.00%) -> 08:04:01 blocked_vpw(+0.00%) -> 08:04:01 blocked_liquidity(+0.00%) -> 08:04:03 ai_confirmed(+0.00%) -> 08:04:04 first_ai_wait(+0.00%) -> 08:04:04 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> 08:04:16 blocked_strength_momentum:below_strength_base(+0.00%)|
|스피어(347700)|08:04:44|08:07:59|flat_or_falling|0.00%|-0.90%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-|441.0|-|50/|0|08:05:24 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|산일전기(062040)|08:13:47|09:59:33|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|3|0|diagnostic_quote_age_stale|4716.0|-|62/WAIT|0|08:20:34 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 09:31:37 blocked_strength_momentum:below_strength_base(+0.00%) -> 09:31:37 blocked_vpw(+0.00%) -> 09:31:39 ai_confirmed(+0.00%) -> 09:31:39 first_ai_wait(+0.00%) -> 09:31:39 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> 09:39:02 blocked_strength_momentum:below_strength_base(+0.00%)|
|티로보틱스(117730)|08:21:45|08:22:30|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-|774.0|-|50/|0|08:22:24 blocked_overbought(+0.00%) -> 08:22:25 blocked_strength_momentum:below_buy_ratio(+0.00%)|
|나우로보틱스(459510)|08:23:16|08:23:54|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-|878.0|-|50/|0|08:23:47 blocked_overbought(+0.00%) -> 08:23:47 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|로보스타(090360)|08:23:16|08:23:54|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-|719.0|-|50/|0|08:23:49 blocked_strength_momentum:below_buy_ratio(+0.00%)|
|두산로보틱스(454910)|08:24:46|08:25:34|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-|850.0|-|50/|0|08:25:27 blocked_strength_momentum:below_buy_ratio(+0.00%)|
|삼화콘덴서(001820)|08:26:25|09:59:33|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-|2420.0|-|60/WAIT|0|08:26:49 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 08:26:50 ai_confirmed(+0.00%) -> 08:26:52 first_ai_wait(+0.00%) -> 08:26:52 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> ... -> 08:29:09 blocked_ai_score(+0.00%) -> 08:29:09 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.00%) -> 09:31:33 blocked_strength_momentum:below_strength_base(+0.00%)|
|신성델타테크(065350)|08:04:44|08:05:27|flat_or_falling|-0.14%|-0.14%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-|161.0|-|50/|0|08:05:25 blocked_strength_momentum:below_window_buy_value(-0.14%)|
|한미반도체(042700)|08:01:43|08:05:36|flat_or_falling|-0.19%|-0.19%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-|221.0|-|50/|0|08:04:10 blocked_strength_momentum:below_strength_base(-0.19%) -> 08:04:10 blocked_vpw(-0.19%) -> 08:04:10 blocked_ai_score:ai_score_50_buy_hold_override(-0.19%)|
|에코프로비엠(247540)|08:01:43|09:59:47|flat_or_falling|-1.41%|-1.41%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|1|-|1767.0|08:03:08|70/WAIT|6|08:03:08 latency_pass:caution_normal_entry_allowed(-1.41%) -> 08:03:12 order_bundle_submitted:caution_normal_entry_allowed(-1.41%) -> 08:21:18 latency_pass:caution_normal_entry_allowed(-1.41%) -> 08:21:28 order_bundle_submitted:caution_normal_entry_allowed(-1.41%) -> ... -> 08:25:24 blocked_vpw(-1.41%) -> 08:25:24 blocked_ai_score(-1.41%) -> 08:25:24 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(-1.41%)|

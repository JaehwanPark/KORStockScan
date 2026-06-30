# 2026-06-30 13:00 이후 감시대상 BUY 전 흐름

- generated_at: 2026-06-30T15:00:00
- source_events: /home/ubuntu/KORStockScan/data/runtime/sentinel_event_cache/buy_funnel_sentinel_events_2026-06-30.jsonl
- source_diagnostic: data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-30_1500_1300_goal.json
- event_window_since: 2026-06-30T13:00:00
- event_window_until: 2026-06-30T15:00:00
- symbol_count: 18
- rising_symbol_count_by_max_delta: 10
- rising_missed_buy_count_in_latest_diagnostic: 10
- rising_missed_symbol_count_in_report: 10
- rising_missed_residual_excluding_forced_scout_symbol_count: 5
- rising_missed_forced_scout_event_count: 198
- rising_missed_forced_scout_symbol_count: 5
- rising_missed_forced_scout_residual_symbol_count: 5
- real_submit_symbol_count_in_latest_diagnostic: 3
- buy_signal_or_pre_submit_pass_seen_symbols: 6
- stale_eval_symbol_count: 13
- rising_stale_eval_symbol_count: 5
- rising_fresh_only_symbol_count: 5
- stale_refresh_recovered_symbol_count: 15

## forced scout observation

- event_count: 198
- symbol_count: 5
- symbols: 002990, 010120, 025320, 080220, 103590
- rising_missed_residual_symbols: 002990, 010120, 025320, 080220, 103590
- rising_missed_residual_excluding_forced_scout_symbols: 000500, 001820, 095610, 240810, 475150
- decision_authority: source_quality_only
- runtime_effect: False

## blocker rollup

- 5: `blocked_ai_score` / `blocked_ai_score_below_buy_score_threshold`
- 4: `latency_block` / `latency_state_danger`
- 4: `blocked_strength_momentum` / `below_strength_base`
- 2: `blocked_strength_momentum` / `below_buy_ratio`
- 2: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 1: `blocked_strength_momentum` / `below_window_buy_value`

## blocker taxonomy

- 323: `runtime_backpressure`
- 66: `strategy_reject`
- 31: `pre_submit_quality_guard`
- 25: `intended_guard`
- 3: `watch_budget_reallocated`

## suppressed non-major blocker counts

- 323: `runtime_backpressure` / `scalping_scanner_watching_runtime_skip` / `scanner_full_eval_loop_budget_deferred`
- 31: `pre_submit_quality_guard` / `latency_block` / `latency_state_danger`
- 12: `intended_guard` / `scalping_scanner_watching_runtime_skip` / `entry_cooldown_active`
- 2: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `scanner_hardgate_prefilter`
- 1: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `stale_recovery_failed`

## rising-symbol blocker rollup

- 5: `blocked_ai_score` / `blocked_ai_score_below_buy_score_threshold`
- 4: `latency_block` / `latency_state_danger`
- 1: `blocked_strength_momentum` / `below_strength_base`

## rising fresh-only blocker rollup

- 4: `latency_block` / `latency_state_danger`
- 1: `blocked_ai_score` / `blocked_ai_score_below_buy_score_threshold`

## rising stale-mixed blocker rollup

- 4: `blocked_ai_score` / `blocked_ai_score_below_buy_score_threshold`
- 1: `blocked_strength_momentum` / `below_strength_base`

## stale-eval rollup

- 8: `ai_confirmed`
- 4: `blocked_ai_score`
- 1: `ai_confirmed_terminal_no_budget`

## stale-eval category rollup

- 13: `diagnostic_quote_age_stale`

## latency danger root cause

|종목|건수|top cause|spread ratio med/max|ws age med/max|spread ticks med/max|micro|bucket|
|---|---:|---|---:|---:|---:|---|---|
|금호건설(002990)|79|quote_stale|0.0/0.0|9498.0/18993.0|0.0/0.0|neutral|spread=not_available_no_bid_ask\|price=mid\|depth=thick\|sample=rich|
|LS ELECTRIC(010120)|43|spread_too_wide|0.01046/0.010616|78.0/857.0|5.0/5.0|neutral|spread=wide\|price=high\|depth=thick\|sample=rich|
|시노펙스(025320)|41|spread_microstructure_wide|0.008347/0.010101|144.0/14749.0|5.0/6.0|neutral|spread=wide\|price=low\|depth=thick\|sample=rich|
|일진전기(103590)|14|spread_microstructure_wide|0.006557/0.009309|194.0/16625.0|5.0/7.0|neutral|spread=wide\|price=high\|depth=normal\|sample=rich|
|제주반도체(080220)|3|spread_microstructure_wide|0.005825/0.005831|87.0/1475.0|6.0/6.0|neutral|spread=wide\|price=high\|depth=normal\|sample=rich|

## top rows by max delta

|종목|첫감시|마지막|상승여부|maxΔ|latestΔ|BUY전 주 blocker|class|stale평가|refresh회복|stale유형|max quote age|BUY전 통과신호|AI|실제submit|흐름|
|---|---:|---:|---|---:|---:|---|---|---:|---:|---|---:|---:|---:|---:|---|
|가온전선(000500)|13:01:38|13:16:04|rising|20.44%|20.44%|`blocked_ai_score`/blocked_ai_score_below_buy_score_threshold|-|0|0|-||-|69/WAIT|0|13:01:38 blocked_ai_score(+20.44%) -> 13:01:38 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+20.44%) -> 13:04:31 blocked_ai_score(+20.44%) -> 13:04:31 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+20.44%) -> ... -> 13:12:21 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+20.44%) -> 13:16:04 blocked_ai_score(+20.44%) -> 13:16:04 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+20.44%)|
|금호건설(002990)|13:11:09|14:59:46|rising|7.00%|5.34%|`latency_block`/latency_state_danger|-|0|0|-||-|0/|0|13:11:09 latency_block:latency_state_danger(+7.00%)|
|일진전기(103590)|13:00:45|14:55:45|rising|5.14%|5.14%|`latency_block`/latency_state_danger|-|0|12|-||-|70/|0|13:00:45 latency_block:latency_state_danger(+5.14%)|
|SK이터닉스(475150)|13:00:53|13:13:19|rising|4.06%|4.06%|`blocked_ai_score`/blocked_ai_score_below_buy_score_threshold|-|9|0|diagnostic_quote_age_stale|25129.0|-|76/WAIT|0|13:00:53 blocked_strength_momentum:below_strength_base(+4.06%) -> 13:02:49 blocked_ai_score(+4.06%) -> 13:02:49 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+4.06%) -> 13:05:51 blocked_ai_score(+4.06%) -> ... -> 13:09:52 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+4.06%) -> 13:13:19 blocked_ai_score(+4.06%) -> 13:13:19 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+4.06%)|
|삼화콘덴서(001820)|13:01:26|13:42:03|rising|2.57%|2.57%|`blocked_strength_momentum`/below_strength_base|-|5|16|diagnostic_quote_age_stale|7744.0|-|76/WAIT|0|13:01:26 blocked_strength_momentum:below_buy_ratio(+2.57%) -> 13:01:26 blocked_vpw(+2.57%) -> 13:01:26 blocked_ai_score(+2.57%) -> 13:01:26 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+2.57%) -> ... -> 13:38:25 blocked_ai_score(+2.57%) -> 13:38:25 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+2.57%) -> 13:42:03 blocked_strength_momentum:below_strength_base(+2.57%)|
|시노펙스(025320)|13:09:40|14:38:19|rising|1.31%|1.31%|`latency_block`/latency_state_danger|-|0|37|-||-|70/|0|13:09:40 latency_block:latency_state_danger(+1.31%)|
|테스(095610)|13:00:18|13:42:12|rising|1.24%|1.24%|`blocked_ai_score`/blocked_ai_score_below_buy_score_threshold|-|19|5|diagnostic_quote_age_stale|61274.0|-|72/WAIT|0|13:00:18 blocked_ai_score(+1.24%) -> 13:00:18 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+1.24%) -> 13:00:19 entry_ai_price_canary_fallback:above_best_ask(+1.24%) -> 13:03:27 ai_confirmed(+1.24%) -> ... -> 13:38:40 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+1.24%) -> 13:42:12 blocked_ai_score(+1.24%) -> 13:42:12 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+1.24%)|
|LS ELECTRIC(010120)|13:02:04|14:59:38|rising|1.07%|1.07%|`latency_block`/latency_state_danger|-|0|43|-||-|70/|0|13:02:04 latency_block:latency_state_danger(+1.07%)|
|제주반도체(080220)|13:01:54|14:58:19|rising|0.78%|0.78%|`blocked_ai_score`/blocked_ai_score_below_buy_score_threshold|-|27|18|diagnostic_quote_age_stale|31585.0|14:08:07|74/WAIT|0|13:01:54 latency_block:latency_state_danger(+0.78%) -> 13:20:23 entry_ai_price_canary_skip_order:orderbook_micro is bearish with negative ofi and high top_depth_ratio indicating strong sell pressure(+0.78%) -> 13:22:57 latency_block:latency_state_danger(+0.78%) -> 13:47:08 blocked_strength_momentum:below_buy_ratio(+0.78%) -> ... -> 14:58:19 wait65_79_ev_candidate(+0.78%) -> 14:58:19 blocked_ai_score(+0.78%) -> 14:58:19 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.78%)|
|원익IPS(240810)|13:01:47|13:42:27|rising|0.55%|0.55%|`blocked_ai_score`/blocked_ai_score_below_buy_score_threshold|-|9|12|diagnostic_quote_age_stale|8252.0|13:09:04|73/WAIT|0|13:01:47 ai_confirmed(+0.55%) -> 13:01:47 blocked_ai_score(+0.55%) -> 13:01:47 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.55%) -> 13:04:48 blocked_strength_momentum:below_buy_ratio(+0.55%) -> ... -> 13:42:27 blocked_vpw(+0.55%) -> 13:42:27 blocked_ai_score(+0.55%) -> 13:42:27 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.55%)|
|삼성E&A(028050)|13:00:28|14:59:55|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_strength_base|strategy_reject|31|37|diagnostic_quote_age_stale|10297.0|14:19:34|62/WAIT|0|13:05:24 blocked_strength_momentum:below_strength_base(+0.00%) -> 13:05:24 blocked_vpw(+0.00%) -> 13:05:26 ai_confirmed(+0.00%) -> 13:05:26 wait65_79_ev_candidate(+0.00%) -> ... -> 14:52:51 blocked_ai_score(+0.00%) -> 14:52:51 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.00%) -> 14:57:41 blocked_strength_momentum:below_strength_base(+0.00%)|
|후성(093370)|13:00:29|14:50:31|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|-|19|30|diagnostic_quote_age_stale|6707.0|14:23:46|80/BUY|1|13:00:29 blocked_strength_momentum:below_buy_ratio(+0.00%) -> 13:00:29 blocked_vpw(+0.00%) -> 13:00:29 blocked_liquidity(+0.00%) -> 13:00:30 ai_confirmed(+0.00%) -> ... -> 14:50:23 budget_pass(+0.00%) -> 14:50:27 latency_pass:safe_normal_entry_allowed(+0.00%) -> 14:50:31 order_bundle_submitted:safe_normal_entry_allowed(+0.00%)|
|심텍(222800)|13:00:32|14:59:50|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_buy_ratio|-|10|11|diagnostic_quote_age_stale|4815.0|14:08:38|62/WAIT|1|13:00:32 blocked_strength_momentum:below_buy_ratio(+0.00%) -> 13:35:07 blocked_gap_from_scan(+0.00%) -> 13:35:09 ai_confirmed(+0.00%) -> 13:35:11 first_ai_wait(+0.00%) -> ... -> 14:59:50 ai_confirmed(+0.00%) -> 14:59:50 blocked_ai_score(+0.00%) -> 14:59:50 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.00%)|
|SK스퀘어(402340)|13:03:29|14:59:00|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|12|20|diagnostic_quote_age_stale|7695.0|-|62/WAIT|0|13:07:39 ai_confirmed(+0.00%) -> 13:07:41 first_ai_wait(+0.00%) -> 13:07:41 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> 13:23:10 blocked_gap_from_scan(+0.00%) -> ... -> 14:52:55 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.00%) -> 14:57:45 blocked_ai_score(+0.00%) -> 14:57:45 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.00%)|
|남화산업(111710)|13:21:37|14:59:00|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_strength_base|strategy_reject|32|42|diagnostic_quote_age_stale|7014.0|-|58/WAIT|0|13:23:05 blocked_strength_momentum:below_strength_base(+0.00%) -> 13:23:05 blocked_vpw(+0.00%) -> 13:23:05 blocked_liquidity(+0.00%) -> 13:23:06 ai_confirmed(+0.00%) -> ... -> 14:58:49 blocked_liquidity(+0.00%) -> 14:58:49 blocked_ai_score(+0.00%) -> 14:58:49 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.00%)|
|주성엔지니어링(036930)|13:24:34|14:43:57|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_buy_ratio|-|6|14|diagnostic_quote_age_stale|6658.0|14:20:50|80/BUY|1|13:24:34 ai_confirmed(+0.00%) -> 13:24:35 first_ai_wait(+0.00%) -> 13:24:35 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> 13:36:44 blocked_strength_momentum:below_buy_ratio(+0.00%) -> ... -> 14:20:53 latency_pass:latency_spread_relief_normal_override(+0.00%) -> 14:20:58 order_bundle_submitted:latency_spread_relief_normal_override(+0.00%) -> 14:43:57 blocked_strength_momentum:below_buy_ratio(+0.00%)|
|대덕전자(353200)|13:47:20|14:59:00|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|3|3|diagnostic_quote_age_stale|4781.0|-|62/WAIT|0|13:48:43 blocked_overbought(+0.00%) -> 13:48:46 blocked_strength_momentum:below_buy_ratio(+0.00%) -> 14:22:46 blocked_overbought(+0.00%) -> 14:22:48 ai_confirmed(+0.00%) -> ... -> 14:58:35 ai_confirmed(+0.00%) -> 14:58:35 blocked_ai_score(+0.00%) -> 14:58:35 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.00%)|
|SK네트웍스(001740)|13:47:20|14:07:37|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_strength_base|strategy_reject|2|11|diagnostic_quote_age_stale|4980.0|-|62/WAIT|0|13:48:57 blocked_strength_momentum:below_strength_base(+0.00%) -> 13:48:57 blocked_vpw(+0.00%) -> 13:48:58 ai_confirmed(+0.00%) -> 13:48:58 first_ai_wait(+0.00%) -> ... -> 14:03:30 blocked_ai_score(+0.00%) -> 14:03:30 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.00%) -> 14:07:21 blocked_strength_momentum:below_strength_base(+0.00%)|

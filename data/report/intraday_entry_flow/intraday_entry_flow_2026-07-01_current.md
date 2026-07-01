# 2026-07-01 08:00 이후 감시대상 BUY 전 흐름

- generated_at: 2026-07-01T09:55:18
- source_events: /home/ubuntu/KORStockScan/data/runtime/sentinel_event_cache/buy_funnel_sentinel_events_2026-07-01.jsonl
- source_diagnostic: /home/ubuntu/KORStockScan/data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-07-01.json
- event_window_since: 08:00:00
- event_window_until: 2026-07-01T09:55:18
- symbol_count: 24
- rising_symbol_count_by_max_delta: 13
- rising_missed_buy_count_in_latest_diagnostic: 9
- rising_missed_symbol_count_in_report: 9
- rising_missed_residual_excluding_forced_scout_symbol_count: 1
- rising_missed_forced_scout_event_count: 202
- rising_missed_forced_scout_symbol_count: 9
- rising_missed_forced_scout_residual_symbol_count: 8
- real_submit_symbol_count_in_latest_diagnostic: 0
- buy_signal_or_pre_submit_pass_seen_symbols: 2
- stale_eval_symbol_count: 19
- rising_stale_eval_symbol_count: 11
- rising_fresh_only_symbol_count: 2
- stale_refresh_recovered_symbol_count: 17

## forced scout observation

- event_count: 202
- symbol_count: 9
- symbols: 010120, 037710, 062040, 067080, 073240, 084370, 112040, 270660, 336260
- rising_missed_residual_symbols: 010120, 037710, 062040, 067080, 073240, 084370, 270660, 336260
- rising_missed_residual_excluding_forced_scout_symbols: 033100
- decision_authority: source_quality_only
- runtime_effect: False

## blocker rollup

- 15: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 4: `latency_block` / `caution_slippage_exceeded`
- 3: `blocked_strength_momentum` / `insufficient_history`
- 2: `scalping_scanner_watching_runtime_skip` / `entry_cooldown_active`

## blocker taxonomy

- 577: `runtime_backpressure`
- 66: `strategy_reject`
- 27: `source_freshness_blocker`
- 19: `pre_submit_quality_guard`
- 11: `intended_guard`
- 4: `watch_budget_reallocated`
- 2: `source_freshness_recovering`

## suppressed non-major blocker counts

- 577: `runtime_backpressure` / `scalping_scanner_watching_runtime_skip` / `scanner_full_eval_loop_budget_deferred`
- 18: `pre_submit_quality_guard` / `latency_block` / `latency_state_danger`
- 4: `intended_guard` / `scalping_scanner_watching_runtime_skip` / `entry_cooldown_active`
- 2: `source_freshness_recovering` / `scalping_scanner_watching_runtime_skip` / `ws_snapshot_missing_or_zero`
- 2: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `scanner_hardgate_prefilter`
- 2: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `safety_cooldown_pool_blocked`

## rising-symbol blocker rollup

- 4: `latency_block` / `caution_slippage_exceeded`
- 4: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 3: `blocked_strength_momentum` / `insufficient_history`
- 2: `scalping_scanner_watching_runtime_skip` / `entry_cooldown_active`

## rising fresh-only blocker rollup

- 1: `latency_block` / `caution_slippage_exceeded`
- 1: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`

## rising stale-mixed blocker rollup

- 3: `latency_block` / `caution_slippage_exceeded`
- 3: `blocked_strength_momentum` / `insufficient_history`
- 3: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 2: `scalping_scanner_watching_runtime_skip` / `entry_cooldown_active`

## stale-eval rollup

- 15: `blocked_strength_momentum`
- 2: `blocked_overbought`
- 1: `ai_confirmed_terminal_no_budget`
- 1: `ai_confirmed`

## stale-eval category rollup

- 19: `diagnostic_quote_age_stale`

## latency danger root cause

|종목|건수|top cause|spread ratio med/max|ws age med/max|spread ticks med/max|micro|bucket|
|---|---:|---|---:|---:|---:|---|---|
|유진테크(084370)|44|spread_too_wide|0.011227/0.014963|162.0/1158.0|5.0/22.0|neutral|spread=wide\|price=high\|depth=normal\|sample=rich|
|두산퓨얼셀(336260)|27|spread_microstructure_wide|0.008803/0.010676|191.0/1139.0|5.0/6.0|neutral|spread=wide\|price=high\|depth=normal\|sample=rich|
|제룡전기(033100)|24|spread_microstructure_wide|0.009174/0.011342|117.5/1125.0|5.0/6.0|neutral|spread=wide\|price=high\|depth=normal\|sample=rich|
|산일전기(062040)|18|quote_stale|0.009653/0.013944|449.5/11700.0|5.0/7.0|neutral|spread=wide\|price=high\|depth=thick\|sample=rich|
|위메이드(112040)|16|quote_stale|0.0/0.0|5098.5/11562.0|0.0/0.0|insufficient|spread=not_available_no_bid_ask\|price=mid\|depth=thick\|sample=insufficient|
|대화제약(067080)|12|quote_stale|0.001705/0.006092|794.5/1084.0|2.0/7.0|neutral|spread=wide\|price=mid\|depth=normal\|sample=rich|
|LS ELECTRIC(010120)|6|spread_too_wide|0.009927/0.010183|238.0/450.0|5.0/5.0|neutral|spread=wide\|price=high\|depth=thick\|sample=rich|
|에브리봇(270660)|2|spread_microstructure_wide|0.00979/0.010996|136.0/187.0|15.5/17.0|neutral|spread=wide\|price=mid\|depth=normal\|sample=rich|
|코세스(089890)|2|spread_microstructure_wide|0.008691/0.010145|81.5/134.0|6.0/7.0|neutral|spread=wide\|price=mid\|depth=thin\|sample=rich|
|금호타이어(073240)|1|spread_too_wide|0.011342/0.011342|447.0/447.0|6.0/6.0|neutral|spread=wide\|price=low\|depth=thick\|sample=rich|

## top rows by max delta

|종목|첫감시|마지막|상승여부|maxΔ|latestΔ|BUY전 주 blocker|class|stale평가|refresh회복|stale유형|max quote age|BUY전 통과신호|AI|실제submit|흐름|
|---|---:|---:|---|---:|---:|---|---|---:|---:|---|---:|---:|---:|---:|---|
|대화제약(067080)|08:01:41|09:55:08|rising|7.07%|7.07%|`latency_block`/caution_slippage_exceeded|pre_submit_quality_guard|31|16|diagnostic_quote_age_stale|16209.0|-|62/WAIT|0|08:03:29 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 08:04:59 blocked_vpw(+0.00%) -> 08:04:59 blocked_liquidity(+0.00%) -> 08:05:00 ai_confirmed(+0.00%) -> ... -> 08:39:33 blocked_strength_momentum:insufficient_history(+7.07%) -> 08:39:52 blocked_overbought(+7.07%) -> 08:39:52 blocked_strength_momentum:insufficient_history(+7.07%)|
|금호타이어(073240)|08:01:41|09:55:10|rising|6.36%|6.36%|`blocked_strength_momentum`/insufficient_history|source_freshness_blocker|69|6|diagnostic_quote_age_stale|16014.0|08:03:56|78/BUY|0|08:03:38 latency_block:latency_state_danger(+6.36%) -> 08:03:54 blocked_strength_momentum:below_buy_ratio(+6.36%) -> 08:03:56 ai_confirmed(+6.36%) -> 08:03:56 entry_armed:qualification_passed(+6.36%) -> ... -> 08:16:36 blocked_strength_momentum:insufficient_history(+6.36%) -> 08:17:45 blocked_strength_momentum:below_buy_ratio(+6.36%) -> 08:18:30 blocked_strength_momentum:insufficient_history(+6.36%)|
|에브리봇(270660)|08:01:41|09:10:49|rising|5.63%|5.63%|`latency_block`/caution_slippage_exceeded|pre_submit_quality_guard|7|6|diagnostic_quote_age_stale|14650.0|-|70/SKIP|0|08:34:43 entry_ai_price_canary_skip_order:orderbook_micro is bearish with negative ofi and high top_depth_ratio indicating strong sell pressure(+5.63%) -> 09:03:18 latency_block:latency_state_danger(+5.63%) -> 09:04:24 latency_block:caution_slippage_exceeded(+5.63%) -> 09:04:59 latency_block:latency_state_danger(+5.63%) -> 09:05:54 latency_block:caution_slippage_exceeded(+5.63%) -> 09:07:41 blocked_strength_momentum:insufficient_history(+5.63%) -> 09:07:58 blocked_strength_momentum:below_strength_base(+5.63%) -> 09:09:12 blocked_strength_momentum:insufficient_history(+5.63%)|
|유진테크(084370)|08:04:32|09:55:16|rising|3.57%|2.30%|`latency_block`/caution_slippage_exceeded|pre_submit_quality_guard|35|49|diagnostic_quote_age_stale|15012.0|-|70/SKIP|0|08:05:04 blocked_strength_momentum:insufficient_history(+0.00%) -> 08:06:03 blocked_strength_momentum:below_strength_base(+0.00%) -> 08:06:30 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 08:06:45 blocked_strength_momentum:below_strength_base(+0.00%) -> ... -> 08:33:12 blocked_strength_momentum:insufficient_history(+3.57%) -> 09:36:28 latency_block:latency_state_danger(+3.57%) -> 09:55:02 latency_block:safe_slippage_exceeded(+2.30%)|
|두산퓨얼셀(336260)|08:01:41|09:55:16|rising|3.50%|3.50%|`scalping_scanner_watching_runtime_skip`/entry_cooldown_active|intended_guard|6|27|diagnostic_quote_age_stale|20623.0|-|70/USE_DEFENSIVE|0|08:03:43 latency_block:latency_state_danger(+3.50%) -> 09:07:47 blocked_strength_momentum:insufficient_history(+3.50%) -> 09:08:03 blocked_strength_momentum:below_strength_base(+3.50%) -> 09:09:34 blocked_strength_momentum:insufficient_history(+3.50%) -> ... -> 09:10:57 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+3.50%) -> 09:10:58 entry_ai_price_canary_fallback:pre_submit_price_guard(+3.50%) -> 09:32:06 latency_block:latency_state_danger(+3.50%)|
|제룡전기(033100)|08:04:32|09:55:08|rising|3.28%|3.28%|`latency_block`/caution_slippage_exceeded|pre_submit_quality_guard|0|0|-||-|62/WAIT|0|-|
|산일전기(062040)|08:04:32|09:55:03|rising|1.82%|1.82%|`blocked_strength_momentum`/insufficient_history|source_freshness_blocker|15|19|diagnostic_quote_age_stale|18870.0|-|62/WAIT|0|08:05:04 blocked_strength_momentum:insufficient_history(+0.00%) -> 08:05:57 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 08:05:59 ai_confirmed(+0.00%) -> 08:05:59 first_ai_wait(+0.00%) -> ... -> 09:09:15 blocked_strength_momentum:insufficient_history(+1.82%) -> 09:12:39 blocked_strength_momentum:below_buy_ratio(+1.82%) -> 09:32:45 latency_block:latency_state_danger(+1.82%)|
|LS ELECTRIC(010120)|08:01:41|09:55:03|rising|1.44%|1.44%|`scalping_scanner_watching_runtime_skip`/entry_cooldown_active|intended_guard|6|4|diagnostic_quote_age_stale|14405.0|-|70/USE_DEFENSIVE|0|08:03:43 latency_block:latency_state_danger(+1.44%) -> 09:09:10 blocked_strength_momentum:below_buy_ratio(+1.44%) -> 09:10:47 blocked_strength_momentum:insufficient_history(+1.44%) -> 09:12:19 blocked_strength_momentum:below_buy_ratio(+1.44%) -> ... -> 09:12:19 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+1.44%) -> 09:12:20 entry_ai_price_canary_fallback:pre_submit_price_guard(+1.44%) -> 09:34:05 latency_block:latency_state_danger(+1.44%)|
|광주신세계(037710)|08:09:03|09:55:03|rising|1.43%|1.43%|`blocked_strength_momentum`/insufficient_history|source_freshness_blocker|21|1|diagnostic_quote_age_stale|15202.0|-|62/WAIT|0|08:09:14 blocked_liquidity(+0.00%) -> 08:09:15 ai_confirmed(+0.00%) -> 08:09:15 first_ai_wait(+0.00%) -> 08:09:15 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> 08:11:23 blocked_strength_momentum:insufficient_history(+1.43%)|
|두산에너빌리티(034020)|08:01:41|09:45:33|rising|0.90%|0.90%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|14|5|diagnostic_quote_age_stale|6516.0|-|64/WAIT|0|08:03:21 blocked_strength_momentum:below_buy_ratio(+0.34%) -> 08:03:22 ai_confirmed(+0.34%) -> 08:03:25 first_ai_wait(+0.34%) -> 08:03:25 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.34%) -> ... -> 09:44:25 ai_confirmed(+0.90%) -> 09:44:25 first_ai_wait(+0.90%) -> 09:44:25 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.90%)|
|비나텍(126340)|08:01:41|09:55:03|rising|0.67%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|12|5|diagnostic_quote_age_stale|11911.0|-|50/|0|08:03:28 blocked_overbought(+0.00%) -> 08:03:29 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 08:04:32 blocked_overbought(+0.00%) -> 08:04:32 blocked_strength_momentum:below_strength_base(+0.00%) -> ... -> 09:17:47 blocked_strength_momentum:below_strength_base(+0.00%) -> 09:44:35 blocked_overbought(+0.00%) -> 09:44:36 blocked_strength_momentum:below_strength_base(+0.00%)|
|SK스퀘어(402340)|08:01:41|09:55:03|rising|0.23%|0.23%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|한미반도체(042700)|08:01:41|09:15:53|rising|0.19%|0.19%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|6|0|diagnostic_quote_age_stale|12345.0|-|52/WAIT|0|08:03:27 ai_confirmed(+0.19%) -> 08:03:27 first_ai_wait(+0.19%) -> 08:03:27 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.19%) -> 08:04:22 blocked_strength_momentum:below_strength_base(+0.19%) -> ... -> 08:20:28 blocked_strength_momentum:below_strength_base(+0.19%) -> 08:21:10 blocked_strength_momentum:insufficient_history(+0.19%) -> 08:23:11 blocked_strength_momentum:below_strength_base(+0.19%)|
|SK하이닉스(000660)|08:01:41|09:55:03|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|4|2|diagnostic_quote_age_stale|5808.0|-|62/WAIT|0|08:03:14 blocked_strength_momentum:below_buy_ratio(-0.34%) -> 08:03:14 blocked_vpw(-0.34%) -> 08:03:17 ai_confirmed(-0.34%) -> 08:03:19 first_ai_wait(-0.34%) -> ... -> 09:45:27 ai_confirmed(+0.00%) -> 09:45:27 first_ai_wait(+0.00%) -> 09:45:27 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|
|삼성전자(005930)|08:01:41|09:55:03|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|9|3|diagnostic_quote_age_stale|9681.0|-|60/WAIT|0|08:03:26 blocked_strength_momentum:below_strength_base(-0.45%) -> 08:04:05 ai_confirmed(-0.45%) -> 08:04:05 first_ai_wait(-0.45%) -> 08:04:05 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(-0.45%) -> ... -> 08:28:53 blocked_ai_score(+0.00%) -> 08:28:53 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.00%) -> 08:36:55 blocked_strength_momentum:below_strength_base(+0.00%)|
|위메이드(112040)|08:01:41|09:55:03|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|2|4|diagnostic_quote_age_stale|4406.0|-|50/|0|08:24:47 latency_block:latency_state_danger(+0.00%) -> 08:35:51 blocked_overbought(+0.00%) -> 08:35:51 blocked_strength_momentum:insufficient_history(+0.00%) -> 09:17:05 blocked_overbought(+0.00%) -> ... -> 09:37:27 blocked_strength_momentum:below_strength_base(+0.00%) -> 09:45:08 blocked_overbought(+0.00%) -> 09:45:08 blocked_strength_momentum:below_strength_base(+0.00%)|
|삼성전기(009150)|08:04:32|08:07:22|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|6|1|diagnostic_quote_age_stale|6756.0|-|54/WAIT|0|08:05:04 blocked_strength_momentum:insufficient_history(+0.00%) -> 08:06:02 ai_confirmed(+0.00%) -> 08:06:02 first_ai_wait(+0.00%) -> 08:06:02 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> 08:06:29 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 08:06:42 blocked_strength_momentum:below_buy_ratio(+0.00%) -> 08:06:42 blocked_ai_score(+0.00%) -> 08:06:42 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.00%)|
|시노펙스(025320)|08:07:32|08:09:35|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|1|0|diagnostic_quote_age_stale|8355.0|-|50/|0|08:08:18 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 08:09:25 blocked_vpw(+0.00%) -> 08:09:25 blocked_liquidity(+0.00%) -> 08:09:25 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%)|
|일진전기(103590)|08:12:04|08:15:29|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-|1187.0|-|56/WAIT|0|08:13:06 ai_confirmed(+0.00%) -> 08:13:06 first_ai_wait(+0.00%) -> 08:13:06 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> 08:15:28 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|가온전선(000500)|08:16:35|09:55:03|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|3|5|diagnostic_quote_age_stale|9842.0|-|56/WAIT|0|08:35:01 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 09:04:00 blocked_overbought(+0.00%) -> 09:10:25 blocked_strength_momentum:below_buy_ratio(+0.00%) -> 09:10:25 blocked_vpw(+0.00%) -> ... -> 09:45:03 ai_confirmed(+0.00%) -> 09:45:03 first_ai_wait(+0.00%) -> 09:45:03 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|
|필에너지(378340)|08:25:37|08:26:32|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-|1503.0|-|50/|0|08:26:28 blocked_strength_momentum:below_buy_ratio(+0.00%)|
|셀트리온(068270)|08:25:37|09:05:37|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|2|0|diagnostic_quote_age_stale|8923.0|-|62/WAIT|0|08:26:39 blocked_strength_momentum:insufficient_history(+0.00%) -> 08:34:59 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 08:38:58 ai_confirmed(+0.00%) -> 08:38:59 first_ai_wait(+0.00%) -> 08:38:59 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|
|코세스(089890)|08:35:34|09:55:03|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|3|6|diagnostic_quote_age_stale|3236.0|09:12:52|78/BUY|0|08:36:17 blocked_strength_momentum:below_buy_ratio(+0.00%) -> 08:36:17 blocked_vpw(+0.00%) -> 08:36:17 blocked_liquidity(+0.00%) -> 08:36:17 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%) -> ... -> 09:17:50 budget_pass(+0.00%) -> 09:17:52 latency_block:latency_state_danger(+0.00%) -> 09:44:33 blocked_strength_momentum:below_strength_base(+0.00%)|
|금호건설(002990)|09:08:27|09:55:03|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|2|-|1727.0|-|50/|0|09:14:01 blocked_overbought(+0.00%) -> 09:14:04 blocked_strength_momentum:below_strength_base(+0.00%) -> 09:44:28 blocked_overbought(+0.00%) -> 09:44:30 blocked_strength_momentum:below_strength_base(+0.00%)|

# 2026-07-01 09:50 이후 감시대상 BUY 전 흐름

- generated_at: 2026-07-01T11:56:44
- source_events: /home/ubuntu/KORStockScan/data/runtime/sentinel_event_cache/buy_funnel_sentinel_events_2026-07-01.jsonl
- source_diagnostic: /home/ubuntu/KORStockScan/data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-07-01.json
- event_window_since: 09:50:00
- event_window_until: 2026-07-01T11:56:44
- symbol_count: 72
- rising_symbol_count_by_max_delta: 14
- rising_missed_buy_count_in_latest_diagnostic: 14
- rising_missed_symbol_count_in_report: 11
- rising_missed_residual_excluding_forced_scout_symbol_count: 4
- rising_missed_forced_scout_event_count: 192
- rising_missed_forced_scout_symbol_count: 11
- rising_missed_forced_scout_residual_symbol_count: 10
- real_submit_symbol_count_in_latest_diagnostic: 1
- buy_signal_or_pre_submit_pass_seen_symbols: 4
- stale_eval_symbol_count: 27
- rising_stale_eval_symbol_count: 9
- rising_fresh_only_symbol_count: 5
- stale_refresh_recovered_symbol_count: 42

## forced scout observation

- event_count: 192
- symbol_count: 11
- symbols: 001260, 006340, 006360, 010120, 037350, 037710, 045100, 062040, 084370, 336260, 347700
- rising_missed_residual_symbols: 001260, 006340, 006360, 010120, 037350, 037710, 045100, 062040, 084370, 336260
- rising_missed_residual_excluding_forced_scout_symbols: 000390, 033100, 067080, 073240
- decision_authority: source_quality_only
- runtime_effect: False

## blocker rollup

- 49: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 3: `scalping_scanner_watching_runtime_skip` / `entry_cooldown_active`
- 3: `latency_block` / `latency_state_danger`
- 3: `-` / `-`
- 3: `blocked_overbought` / `below_strength_base`
- 3: `blocked_strength_momentum` / `below_strength_base`
- 2: `blocked_strength_momentum` / `below_window_buy_value`
- 2: `scalping_scanner_watching_runtime_skip` / `ws_snapshot_missing_or_zero`
- 1: `blocked_strength_momentum` / `latency_state_danger`
- 1: `blocked_strength_momentum` / `below_buy_ratio`
- 1: `blocked_overbought` / `-`
- 1: `latency_block` / `caution_slippage_exceeded`

## blocker taxonomy

- 533: `runtime_backpressure`
- 261: `strategy_reject`
- 49: `watch_budget_reallocated`
- 38: `pre_submit_quality_guard`
- 23: `intended_guard`
- 7: `source_freshness_blocker`
- 6: `source_freshness_evictable`
- 4: `source_freshness_recovering`

## suppressed non-major blocker counts

- 533: `runtime_backpressure` / `scalping_scanner_watching_runtime_skip` / `scanner_full_eval_loop_budget_deferred`
- 38: `pre_submit_quality_guard` / `latency_block` / `latency_state_danger`
- 33: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `stale_recovery_failed`
- 16: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `scanner_hardgate_prefilter`
- 6: `source_freshness_evictable` / `scalping_scanner_watching_runtime_skip` / `ws_snapshot_missing_or_zero`
- 4: `source_freshness_recovering` / `scalping_scanner_watching_runtime_skip` / `ws_snapshot_missing_or_zero`
- 3: `intended_guard` / `scalping_scanner_watching_runtime_skip` / `entry_cooldown_active`

## rising-symbol blocker rollup

- 3: `scalping_scanner_watching_runtime_skip` / `entry_cooldown_active`
- 3: `latency_block` / `latency_state_danger`
- 3: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 1: `blocked_strength_momentum` / `below_window_buy_value`
- 1: `-` / `-`
- 1: `blocked_strength_momentum` / `latency_state_danger`
- 1: `blocked_strength_momentum` / `below_buy_ratio`
- 1: `blocked_overbought` / `-`

## rising fresh-only blocker rollup

- 2: `latency_block` / `latency_state_danger`
- 1: `-` / `-`
- 1: `scalping_scanner_watching_runtime_skip` / `entry_cooldown_active`
- 1: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`

## rising stale-mixed blocker rollup

- 2: `scalping_scanner_watching_runtime_skip` / `entry_cooldown_active`
- 2: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 1: `blocked_strength_momentum` / `below_window_buy_value`
- 1: `latency_block` / `latency_state_danger`
- 1: `blocked_strength_momentum` / `latency_state_danger`
- 1: `blocked_strength_momentum` / `below_buy_ratio`
- 1: `blocked_overbought` / `-`

## stale-eval rollup

- 13: `blocked_strength_momentum`
- 7: `ai_confirmed`
- 3: `blocked_overbought`
- 3: `blocked_vpw`
- 1: `blocked_liquidity`

## stale-eval category rollup

- 27: `diagnostic_quote_age_stale`

## latency danger root cause

|종목|건수|top cause|spread ratio med/max|ws age med/max|spread ticks med/max|micro|bucket|
|---|---:|---|---:|---:|---:|---|---|
|한양이엔지(045100)|38|spread_microstructure_wide|0.00672/0.009511|351.5/12973.0|5.0/7.0|neutral|spread=wide\|price=mid\|depth=normal\|sample=rich|
|남광토건(001260)|35|quote_stale|0.0/0.011881|10174.0/16612.0|0.0/12.0|insufficient|spread=not_available_no_bid_ask\|price=mid\|depth=thick\|sample=insufficient|
|LS ELECTRIC(010120)|30|spread_microstructure_wide|0.00956/0.009804|62.0/961.0|5.0/5.0|neutral|spread=wide\|price=high\|depth=thick\|sample=rich|
|유진테크(084370)|24|spread_too_wide|0.010977/0.013605|106.0/11066.0|5.0/6.0|neutral|spread=wide\|price=high\|depth=normal\|sample=rich|
|산일전기(062040)|14|spread_microstructure_wide|0.009506/0.009615|91.5/263.0|5.0/5.0|neutral|spread=wide\|price=high\|depth=normal\|sample=rich|
|GS건설(006360)|12|spread_microstructure_wide|0.008425/0.010135|302.5/1152.0|5.0/6.0|neutral|spread=wide\|price=mid\|depth=thick\|sample=rich|
|두산퓨얼셀(336260)|10|spread_microstructure_wide|0.008795/0.010601|404.0/816.0|5.0/6.0|neutral|spread=wide\|price=high\|depth=normal\|sample=rich|
|스피어(347700)|9|spread_microstructure_wide|0.008961/0.011132|586.0/1037.0|5.0/6.0|neutral|spread=wide\|price=mid\|depth=thick\|sample=rich|
|광주신세계(037710)|3|spread_microstructure_wide|0.005828/0.006985|272.0/327.0|5.0/6.0|neutral|spread=wide\|price=mid\|depth=normal\|sample=rich|
|성도이엔지(037350)|3|spread_microstructure_wide|0.005272/0.00644|697.0/709.0|6.0/7.0|neutral|spread=wide\|price=mid\|depth=normal\|sample=rich|
|심텍(222800)|1|latency_provenance_gap|-/-|-/-|-/-|-|diagnostic_latency_without_source_event_fields|

## top rows by max delta

|종목|첫감시|마지막|상승여부|maxΔ|latestΔ|BUY전 주 blocker|class|stale평가|refresh회복|stale유형|max quote age|BUY전 통과신호|AI|실제submit|흐름|
|---|---:|---:|---|---:|---:|---|---|---:|---:|---|---:|---:|---:|---:|---|
|한양이엔지(045100)|10:15:16|11:56:16|rising|10.26%|10.26%|`scalping_scanner_watching_runtime_skip`/entry_cooldown_active|intended_guard|3|44|diagnostic_quote_age_stale|16356.0|10:21:05|62/WAIT|0|10:16:20 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 10:21:03 ai_confirmed(+0.00%) -> 10:21:05 entry_armed:qualification_passed(+0.00%) -> 10:21:06 budget_pass(+0.00%) -> ... -> 10:49:40 blocked_ai_score(+10.26%) -> 10:49:40 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+10.26%) -> 11:10:17 latency_block:latency_state_danger(+10.26%)|
|남광토건(001260)|10:05:10|11:56:43|rising|6.37%|6.37%|`scalping_scanner_watching_runtime_skip`/entry_cooldown_active|intended_guard|8|11|diagnostic_quote_age_stale|20090.0|-|70/|0|10:06:02 blocked_overbought(+0.00%) -> 10:06:04 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 10:12:19 latency_block:latency_state_danger(+6.37%) -> 10:15:43 blocked_overbought(+6.37%) -> ... -> 10:24:59 blocked_overbought(+6.37%) -> 10:24:59 blocked_strength_momentum:insufficient_history(+6.37%) -> 10:45:40 latency_block:latency_state_danger(+6.37%)|
|성도이엔지(037350)|10:42:30|11:56:29|rising|5.49%|5.49%|`blocked_strength_momentum`/below_window_buy_value|strategy_reject|5|8|diagnostic_quote_age_stale|18095.0|-|73/WAIT|0|10:44:51 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 10:57:35 latency_block:latency_state_danger(+5.49%) -> 11:02:17 blocked_strength_momentum:insufficient_history(+5.49%) -> 11:02:43 blocked_strength_momentum:below_buy_ratio(+5.49%) -> ... -> 11:06:02 blocked_ai_score(+5.49%) -> 11:06:02 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+5.49%) -> 11:43:53 latency_block:latency_state_danger(+5.49%)|
|두산퓨얼셀(336260)|09:50:21|10:35:31|rising|3.50%|3.50%|`latency_block`/latency_state_danger|-|6|13|diagnostic_quote_age_stale|15244.0|-|69/WAIT|0|09:50:21 latency_block:latency_state_danger(+3.50%) -> 09:59:20 blocked_ai_score(+3.50%) -> 09:59:20 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+3.50%) -> 10:02:27 blocked_ai_score(+3.50%) -> ... -> 10:32:19 blocked_ai_score(+3.50%) -> 10:32:19 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+3.50%) -> 10:35:31 blocked_strength_momentum:below_strength_base(+3.50%)|
|매드업(000390)|10:04:09|11:09:53|rising|2.47%|0.00%|`-`/-|-|0|0|-||-||0|-|
|유진테크(084370)|09:52:23|11:08:54|rising|2.30%|2.30%|`blocked_strength_momentum`/latency_state_danger|-|18|37|diagnostic_quote_age_stale|18936.0|-|72/WAIT|0|09:52:23 latency_block:latency_state_danger(+2.30%) -> 09:55:02 latency_block:safe_slippage_exceeded(+2.30%) -> 09:55:19 latency_block:latency_state_danger(+2.30%) -> 10:51:36 blocked_strength_momentum:insufficient_history(+2.30%) -> ... -> 11:05:16 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+2.30%) -> 11:08:21 blocked_strength_momentum:insufficient_history(+2.30%) -> 11:08:54 blocked_strength_momentum:below_strength_base(+2.30%)|
|산일전기(062040)|09:56:28|11:09:16|rising|1.82%|1.82%|`blocked_strength_momentum`/below_buy_ratio|-|43|15|diagnostic_quote_age_stale|201945.0|-|70/WAIT|0|09:56:28 latency_block:latency_state_danger(+1.82%) -> 10:11:48 blocked_strength_momentum:below_window_buy_value(+1.82%) -> 10:12:12 blocked_strength_momentum:below_buy_ratio(+1.82%) -> 10:12:12 blocked_vpw(+1.82%) -> ... -> 10:50:53 blocked_strength_momentum:below_buy_ratio(+1.82%) -> 10:59:29 blocked_strength_momentum:insufficient_history(+1.82%) -> 11:05:31 blocked_strength_momentum:below_window_buy_value(+1.82%)|
|GS건설(006360)|10:28:24|11:56:43|rising|1.53%|1.53%|`scalping_scanner_watching_runtime_skip`/entry_cooldown_active|intended_guard|0|12|-||-|70/|0|10:31:24 latency_block:latency_state_danger(+1.02%)|
|LS ELECTRIC(010120)|09:56:31|11:54:53|rising|1.44%|1.44%|`latency_block`/latency_state_danger|-|0|30|-||-|70/|0|09:56:31 latency_block:latency_state_danger(+1.44%)|
|광주신세계(037710)|10:05:51|10:10:09|rising|1.43%|1.43%|`latency_block`/latency_state_danger|-|0|3|-||-|70/|0|10:05:51 latency_block:latency_state_danger(+1.43%)|
|대원전선(006340)|10:08:12|11:11:18|rising|1.40%|0.00%|`blocked_overbought`/-|strategy_reject|38|18|diagnostic_quote_age_stale|95007.0|-|62/WAIT|0|10:09:35 blocked_overbought(+0.00%) -> 10:09:37 ai_confirmed(+0.00%) -> 10:09:39 first_ai_wait(+0.00%) -> 10:09:39 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> ... -> 11:08:43 blocked_strength_momentum:insufficient_history(+1.40%) -> 11:09:20 blocked_overbought(+1.40%) -> 11:09:20 blocked_strength_momentum:insufficient_history(+1.40%)|
|스피어(347700)|10:06:11|11:56:43|rising|0.92%|0.92%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|1|11|diagnostic_quote_age_stale|6843.0|10:16:10|80/BUY|0|10:07:49 ai_confirmed(+0.00%) -> 10:07:52 first_ai_wait(+0.00%) -> 10:07:52 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> 10:16:10 ai_confirmed(+0.00%) -> ... -> 10:56:06 latency_block:latency_state_danger(+0.92%) -> 11:09:33 blocked_strength_momentum:below_window_buy_value(+0.92%) -> 11:49:02 latency_block:latency_state_danger(+0.92%)|
|이수페타시스(007660)|10:10:13|11:56:43|rising|0.72%|0.72%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|12|6|diagnostic_quote_age_stale|6949.0|-|62/WAIT|0|10:11:14 blocked_strength_momentum:below_buy_ratio(+0.00%) -> 10:11:14 blocked_vpw(+0.00%) -> 10:11:16 ai_confirmed(+0.00%) -> 10:11:16 first_ai_wait(+0.00%) -> ... -> 11:54:08 ai_confirmed(+0.72%) -> 11:54:08 blocked_ai_score(+0.72%) -> 11:54:08 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.72%)|
|디앤디파마텍(347850)|10:51:33|10:56:48|rising|0.64%|0.64%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|2|-|2455.0|-|58/WAIT|0|10:53:28 blocked_strength_momentum:below_buy_ratio(+0.00%) -> 10:53:28 blocked_vpw(+0.00%) -> 10:53:29 ai_confirmed(+0.00%) -> 10:53:29 first_ai_wait(+0.00%) -> 10:53:29 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> 10:54:35 blocked_ai_score(+0.00%) -> 10:54:35 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.00%)|
|금호건설(002990)|09:57:02|10:39:26|flat_or_falling|0.00%|0.00%|`blocked_overbought`/below_strength_base|-|2|12|diagnostic_quote_age_stale|5307.0|-|50/|0|09:57:02 blocked_overbought(+0.00%) -> 09:57:02 blocked_strength_momentum:below_strength_base(+0.00%) -> 10:10:14 blocked_overbought(+0.00%) -> 10:10:18 blocked_strength_momentum:below_strength_base(+0.00%) -> ... -> 10:36:53 blocked_strength_momentum:below_strength_base(+0.00%) -> 10:39:26 blocked_overbought(+0.00%) -> 10:39:26 blocked_strength_momentum:below_strength_base(+0.00%)|
|코세스(089890)|09:57:43|10:33:01|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_strength_base|-|2|7|diagnostic_quote_age_stale|3602.0|-|50/|0|09:57:43 blocked_overbought(+0.00%) -> 09:58:57 blocked_strength_momentum:below_strength_base(+0.00%) -> 10:11:40 blocked_vpw(+0.00%) -> 10:11:40 blocked_liquidity(+0.00%) -> ... -> 10:18:52 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%) -> 10:25:34 blocked_strength_momentum:below_strength_base(+0.00%) -> 10:33:01 blocked_strength_momentum:insufficient_history(+0.00%)|
|가온전선(000500)|09:57:45|11:31:12|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|-|13|18|diagnostic_quote_age_stale|6682.0|-|62/WAIT|0|09:57:45 blocked_overbought(+0.00%) -> 09:57:46 blocked_strength_momentum:below_buy_ratio(+0.00%) -> 09:57:46 blocked_vpw(+0.00%) -> 09:57:46 blocked_gap_from_scan(+0.00%) -> ... -> 11:26:35 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.00%) -> 11:31:06 blocked_overbought(+0.00%) -> 11:31:12 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|위메이드(112040)|09:57:48|09:57:49|flat_or_falling|0.00%|0.00%|`blocked_overbought`/below_strength_base|-|0|1|-|2704.0|-|50/|0|09:57:48 blocked_overbought(+0.00%) -> 09:57:49 blocked_strength_momentum:below_strength_base(+0.00%)|
|삼성전자(005930)|09:57:52|09:57:52|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_strength_base|-|0|0|-|1474.0|-|50/|0|09:57:52 blocked_strength_momentum:below_strength_base(+0.00%)|
|비나텍(126340)|09:58:03|10:29:23|flat_or_falling|0.00%|0.00%|`blocked_overbought`/below_strength_base|-|0|7|-|2482.0|-|50/|0|09:58:03 blocked_overbought(+0.00%) -> 09:58:03 blocked_strength_momentum:below_strength_base(+0.00%) -> 10:10:37 blocked_overbought(+0.00%) -> 10:11:37 blocked_strength_momentum:below_strength_base(+0.00%) -> ... -> 10:21:58 blocked_strength_momentum:below_strength_base(+0.00%) -> 10:29:23 blocked_overbought(+0.00%) -> 10:29:23 blocked_strength_momentum:below_strength_base(+0.00%)|
|SK하이닉스(000660)|09:59:04|09:59:05|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_strength_base|-|0|2|-|2515.0|-|62/WAIT|0|09:59:04 blocked_strength_momentum:below_strength_base(+0.00%) -> 09:59:04 blocked_vpw(+0.00%) -> 09:59:05 ai_confirmed(+0.00%) -> 09:59:05 first_ai_wait(+0.00%) -> 09:59:05 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|
|원익QnC(074600)|10:05:10|10:50:34|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|9|3|diagnostic_quote_age_stale|7833.0|-|58/WAIT|0|10:06:17 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 10:13:09 blocked_gap_from_scan(+0.00%) -> 10:13:11 ai_confirmed(+0.00%) -> 10:13:11 first_ai_wait(+0.00%) -> ... -> 10:42:26 ai_confirmed(+0.00%) -> 10:42:26 blocked_ai_score(+0.00%) -> 10:42:26 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.00%)|
|한선엔지니어링(452280)|10:05:10|10:13:57|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|1|1|diagnostic_quote_age_stale|13023.0|-|50/|0|10:06:24 blocked_strength_momentum:below_strength_base(+0.00%)|
|키스트론(475430)|10:05:10|11:12:44|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|1|-|1670.0|-|50/|0|10:06:53 blocked_strength_momentum:below_buy_ratio(+0.00%) -> 11:12:43 blocked_strength_momentum:below_strength_base(+0.00%)|
|주성엔지니어링(036930)|10:05:10|11:56:43|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|6|1|diagnostic_quote_age_stale|8124.0|-|62/WAIT|0|10:34:59 blocked_strength_momentum:below_buy_ratio(+0.00%) -> 11:16:12 ai_confirmed(+0.00%) -> 11:16:14 first_ai_wait(+0.00%) -> 11:16:14 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> ... -> 11:34:01 ai_confirmed(+0.00%) -> 11:34:01 blocked_ai_score(+0.00%) -> 11:34:01 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.00%)|
|심텍(222800)|10:06:11|11:25:56|flat_or_falling|0.00%|0.00%|`latency_block`/caution_slippage_exceeded|pre_submit_quality_guard|9|11|diagnostic_quote_age_stale|7518.0|10:22:26|62/WAIT|0|10:08:02 blocked_strength_momentum:below_buy_ratio(+0.00%) -> 10:17:45 blocked_vpw(-0.32%) -> 10:17:47 ai_confirmed(-0.32%) -> 10:17:47 first_ai_wait(-0.32%) -> ... -> 11:19:52 blocked_ai_score(+0.00%) -> 11:19:52 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.00%) -> 11:25:38 blocked_strength_momentum:below_buy_ratio(+0.00%)|
|SK이터닉스(475150)|10:07:11|10:45:20|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|2|-|1957.0|-|50/|0|10:09:16 blocked_strength_momentum:insufficient_history(+0.00%) -> 10:14:59 blocked_strength_momentum:below_buy_ratio(+0.00%)|
|아모센스(357580)|10:07:11|10:09:45|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|1|-|730.0|-|50/|0|10:09:25 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|휴맥스(115160)|10:12:14|11:05:32|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-|2051.0|-|50/|0|10:13:35 blocked_overbought(+0.00%)|
|아모텍(052710)|10:14:15|10:49:30|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|1|4|diagnostic_quote_age_stale|7231.0|-|50/|0|10:16:24 blocked_liquidity(+0.00%) -> 10:16:24 blocked_gap_from_scan(+0.00%) -> 10:16:24 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%) -> 10:21:23 blocked_strength_momentum:below_buy_ratio(+0.00%) -> ... -> 10:21:23 blocked_gap_from_scan(+0.00%) -> 10:21:23 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%) -> 10:28:05 blocked_strength_momentum:below_strength_base(+0.00%)|
|지엔씨에너지(119850)|10:15:16|11:56:43|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|7|13|diagnostic_quote_age_stale|7056.0|-|62/WAIT|0|10:16:14 blocked_overbought(+0.00%) -> 10:16:16 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 10:16:18 ai_confirmed(+0.00%) -> 10:16:18 first_ai_wait(+0.00%) -> ... -> 11:27:27 blocked_ai_score(+0.00%) -> 11:27:27 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.00%) -> 11:32:25 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|대한전선(001440)|10:22:20|10:46:56|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|1|2|diagnostic_quote_age_stale|6932.0|-|60/WAIT|0|10:24:03 blocked_strength_momentum:below_strength_base(+0.00%) -> 10:24:03 blocked_vpw(+0.00%) -> 10:24:04 ai_confirmed(+0.00%) -> 10:24:04 first_ai_wait(+0.00%) -> 10:24:04 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> 10:29:31 blocked_strength_momentum:below_strength_base(+0.00%)|
|티씨머티리얼즈(125020)|10:24:22|10:31:55|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|3|-|5968.0|-|50/|0|10:26:21 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 10:26:21 blocked_liquidity(+0.00%) -> 10:26:21 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%) -> 10:31:07 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|삼화콘덴서(001820)|10:26:23|11:09:47|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|1|-|166.0|-|50/|0|10:29:14 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|파미셀(005690)|10:28:24|10:50:34|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|1|-|987.0|10:30:05|83/BUY|3|10:30:05 ai_confirmed(+0.00%) -> 10:30:05 entry_armed:qualification_passed(+0.00%) -> 10:30:06 budget_pass(+0.00%) -> 10:30:11 latency_pass:caution_normal_entry_allowed(+0.00%) -> 10:30:15 order_bundle_submitted:caution_normal_entry_allowed(+0.00%)|
|HPSP(403870)|10:28:24|11:11:18|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|1|-|56.0|-|50/|0|10:31:49 blocked_strength_momentum:below_strength_base(+0.00%)|
|에임드바이오(000090)|10:28:24|10:31:55|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|non_actionable_guard_or_backpressure|0|0|-||-||0|-|
|테크윙(089030)|10:29:25|11:02:26|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|2|1|diagnostic_quote_age_stale|6407.0|-|64/WAIT|0|10:31:36 blocked_strength_momentum:below_buy_ratio(+0.00%) -> 10:31:38 ai_confirmed(+0.00%) -> 10:31:38 first_ai_wait(+0.00%) -> 10:31:38 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|
|대우건설(047040)|10:31:56|10:50:34|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-|582.0|-|62/WAIT|0|10:35:06 ai_confirmed(+0.00%) -> 10:35:08 first_ai_wait(+0.00%) -> 10:35:08 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|
|엠앤씨솔루션(484870)|10:36:28|10:40:50|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|5|-|2520.0|-|61/WAIT|0|10:37:57 blocked_overbought(+0.00%) -> 10:38:48 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 10:38:48 blocked_liquidity(+0.00%) -> 10:38:50 ai_confirmed(+0.00%) -> 10:38:50 first_ai_wait(+0.00%) -> 10:38:50 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> 10:40:41 blocked_overbought(+0.00%) -> 10:40:41 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|카카오게임즈(293490)|10:37:58|10:43:42|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|1|-|1307.0|-|50/|0|10:43:00 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|계룡건설(013580)|10:40:59|10:50:34|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-|2378.0|-|50/|0|10:43:04 blocked_liquidity(+0.00%) -> 10:43:04 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%)|
|TIME 코스닥액티브(001620)|10:45:31|10:45:31|flat_or_falling|0.00%|0.00%|`-`/-|-|0|0|-||-||0|-|
|샘씨엔에스(252990)|10:48:32|10:55:32|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|1|0|diagnostic_quote_age_stale|9130.0|-|50/|0|10:50:12 blocked_strength_momentum:below_strength_base(+0.00%)|
|세명전기(017510)|10:50:03|10:52:58|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|RF시스템즈(474610)|10:51:33|10:56:20|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|1|0|diagnostic_quote_age_stale|8853.0|-|50/|0|10:53:33 blocked_strength_momentum:insufficient_history(+0.00%)|
|디아이(003160)|10:51:33|10:55:32|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|바이오다인(314930)|10:51:33|10:53:57|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|엔에프씨(265740)|10:51:33|10:53:57|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|세보엠이씨(011560)|10:51:33|10:53:57|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|엘앤씨바이오(290650)|10:51:33|10:55:32|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|양지사(030960)|10:51:33|10:55:32|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|삼성E&A(028050)|10:54:35|10:58:29|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|1|0|diagnostic_quote_age_stale|3310.0|-|50/|0|10:56:09 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|아크릴(000070)|10:54:35|10:54:35|flat_or_falling|0.00%|0.00%|`-`/-|-|0|0|-||-||0|-|
|브이엠(089970)|10:56:05|10:57:56|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-|2061.0|-|50/|0|10:57:39 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|HD현대에너지솔루션(322000)|10:56:05|10:59:59|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|1|0|diagnostic_quote_age_stale|6689.0|-|50/|0|10:57:43 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|선진뷰티사이언스(086710)|10:56:05|10:59:18|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|인벤티지랩(389470)|10:59:07|11:01:31|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|리센스메디컬(394420)|10:59:07|11:02:26|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|제일테크노스(038010)|10:59:07|11:01:31|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|한신공영(004960)|10:59:07|11:01:31|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|non_actionable_guard_or_backpressure|0|0|-||-||0|-|
|크래프톤(259960)|11:02:08|11:56:43|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|2|-|1246.0|-|62/WAIT|0|11:16:03 ai_confirmed(+0.00%) -> 11:16:03 first_ai_wait(+0.00%) -> 11:16:03 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> 11:20:46 blocked_strength_momentum:below_window_buy_value(+0.00%) -> ... -> 11:29:59 blocked_ai_score(+0.00%) -> 11:29:59 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.00%) -> 11:33:18 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|롯데렌탈(089860)|11:02:08|11:04:21|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|삼양컴텍(484590)|11:02:08|11:04:11|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|지노믹트리(228760)|11:02:08|11:04:28|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|대성하이텍(129920)|11:02:08|11:08:14|flat_or_falling|0.00%|-0.20%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|아모그린텍(125210)|11:03:38|11:08:26|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|3|-|7545.0|-|50/|0|11:06:18 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 11:06:18 blocked_vpw(+0.00%) -> 11:06:18 blocked_liquidity(+0.00%) -> 11:06:18 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%)|
|피에스케이(319660)|11:05:09|11:56:43|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|1|7|diagnostic_quote_age_stale|6744.0|-|50/|0|11:07:23 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 11:07:23 blocked_vpw(+0.00%) -> 11:07:23 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%) -> 11:12:15 blocked_strength_momentum:below_buy_ratio(+0.00%) -> ... -> 11:22:25 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 11:27:21 blocked_vpw(+0.00%) -> 11:27:21 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%)|
|남화산업(111710)|11:06:40|11:08:26|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|제주은행(006220)|11:08:10|11:56:43|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|4|6|diagnostic_quote_age_stale|6354.0|-|62/WAIT|0|11:11:59 blocked_liquidity(+0.00%) -> 11:12:01 ai_confirmed(+0.00%) -> 11:12:02 first_ai_wait(+0.00%) -> 11:12:02 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> ... -> 11:53:14 ai_confirmed(+0.00%) -> 11:53:14 blocked_ai_score(+0.00%) -> 11:53:14 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.00%)|
|태광(023160)|11:08:10|11:56:43|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|5|-|2465.0|-|74/WAIT|0|11:15:13 blocked_liquidity(+0.00%) -> 11:15:13 blocked_gap_from_scan(+0.00%) -> 11:15:16 ai_confirmed(+0.00%) -> 11:15:16 wait65_79_ev_candidate(+0.00%) -> 11:15:17 first_ai_wait(+0.00%) -> 11:15:17 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> 11:19:39 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|피델릭스(032580)|11:11:18|11:22:49|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|2|4|diagnostic_quote_age_stale|7195.0|-|50/|0|11:12:39 blocked_strength_momentum:below_strength_base(+0.00%) -> 11:12:39 blocked_vpw(+0.00%) -> 11:12:39 blocked_liquidity(+0.00%) -> 11:12:39 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%) -> ... -> 11:18:46 blocked_liquidity(+0.00%) -> 11:18:46 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%) -> 11:22:37 blocked_strength_momentum:below_strength_base(+0.00%)|

# 2026-06-30 11:00 이후 감시대상 BUY 전 흐름

- generated_at: 2026-06-30T13:00:00
- source_events: /home/ubuntu/KORStockScan/data/runtime/sentinel_event_cache/buy_funnel_sentinel_events_2026-06-30.jsonl
- source_diagnostic: data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-30_1300_1100_goal.json
- event_window_since: 2026-06-30T11:00:00
- event_window_until: 2026-06-30T13:00:00
- symbol_count: 37
- rising_symbol_count_by_max_delta: 11
- rising_missed_buy_count_in_latest_diagnostic: 13
- rising_missed_symbol_count_in_report: 11
- rising_missed_residual_excluding_forced_scout_symbol_count: 3
- rising_missed_forced_scout_event_count: 127
- rising_missed_forced_scout_symbol_count: 10
- rising_missed_forced_scout_residual_symbol_count: 10
- real_submit_symbol_count_in_latest_diagnostic: 0
- buy_signal_or_pre_submit_pass_seen_symbols: 1
- stale_eval_symbol_count: 13
- rising_stale_eval_symbol_count: 8
- rising_fresh_only_symbol_count: 3
- stale_refresh_recovered_symbol_count: 22

## forced scout observation

- event_count: 127
- symbol_count: 10
- symbols: 000500, 001820, 002990, 010120, 025320, 080220, 103590, 153890, 240810, 475150
- rising_missed_residual_symbols: 000500, 001820, 002990, 010120, 025320, 080220, 103590, 153890, 240810, 475150
- rising_missed_residual_excluding_forced_scout_symbols: 033100, 095610, 356680
- decision_authority: source_quality_only
- runtime_effect: False

## blocker rollup

- 17: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 5: `latency_block` / `latency_state_danger`
- 2: `blocked_strength_momentum` / `latency_state_danger`
- 2: `blocked_strength_momentum` / `below_buy_ratio`
- 2: `blocked_strength_momentum` / `below_window_buy_value`
- 2: `scalping_scanner_watching_runtime_skip` / `ws_snapshot_missing_or_zero`
- 2: `blocked_strength_momentum` / `below_strength_base`
- 1: `blocked_strength_momentum` / `blocked_ai_score_below_buy_score_threshold`
- 1: `ai_confirmed_terminal_no_budget` / `blocked_ai_score_below_buy_score_threshold`
- 1: `blocked_ai_score` / `blocked_ai_score_below_buy_score_threshold`
- 1: `blocked_overbought` / `insufficient_history`
- 1: `-` / `-`

## blocker taxonomy

- 136: `strategy_reject`
- 122: `runtime_backpressure`
- 24: `intended_guard`
- 24: `pre_submit_quality_guard`
- 23: `watch_budget_reallocated`
- 6: `source_freshness_evictable`
- 3: `source_freshness_blocker`
- 1: `source_freshness_recovering`

## suppressed non-major blocker counts

- 122: `runtime_backpressure` / `scalping_scanner_watching_runtime_skip` / `scanner_full_eval_loop_budget_deferred`
- 15: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `stale_recovery_failed`
- 7: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `scanner_hardgate_prefilter`
- 6: `intended_guard` / `scalping_scanner_watching_runtime_skip` / `entry_cooldown_active`
- 6: `source_freshness_evictable` / `scalping_scanner_watching_runtime_skip` / `ws_snapshot_missing_or_zero`
- 1: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `safety_cooldown_pool_blocked`
- 1: `source_freshness_recovering` / `scalping_scanner_watching_runtime_skip` / `ws_snapshot_missing_or_zero`

## rising-symbol blocker rollup

- 5: `latency_block` / `latency_state_danger`
- 2: `blocked_strength_momentum` / `latency_state_danger`
- 1: `blocked_strength_momentum` / `blocked_ai_score_below_buy_score_threshold`
- 1: `ai_confirmed_terminal_no_budget` / `blocked_ai_score_below_buy_score_threshold`
- 1: `blocked_ai_score` / `blocked_ai_score_below_buy_score_threshold`
- 1: `blocked_strength_momentum` / `below_buy_ratio`

## rising fresh-only blocker rollup

- 3: `latency_block` / `latency_state_danger`

## rising stale-mixed blocker rollup

- 2: `blocked_strength_momentum` / `latency_state_danger`
- 2: `latency_block` / `latency_state_danger`
- 1: `blocked_strength_momentum` / `blocked_ai_score_below_buy_score_threshold`
- 1: `ai_confirmed_terminal_no_budget` / `blocked_ai_score_below_buy_score_threshold`
- 1: `blocked_ai_score` / `blocked_ai_score_below_buy_score_threshold`
- 1: `blocked_strength_momentum` / `below_buy_ratio`

## stale-eval rollup

- 6: `blocked_strength_momentum`
- 2: `blocked_vpw`
- 2: `ai_confirmed`
- 1: `ai_confirmed_terminal_no_budget`
- 1: `blocked_overbought`
- 1: `blocked_ai_score`

## stale-eval category rollup

- 13: `diagnostic_quote_age_stale`

## latency danger root cause

|종목|건수|top cause|spread ratio med/max|ws age med/max|spread ticks med/max|micro|bucket|
|---|---:|---|---:|---:|---:|---|---|
|제룡전기(033100)|38|latency_provenance_gap|-/-|-/-|-/-|-|diagnostic_latency_without_source_event_fields|
|LS ELECTRIC(010120)|36|spread_too_wide|0.010661/0.010776|95.5/569.0|5.0/5.0|neutral|spread=wide\|price=high\|depth=thick\|sample=rich|
|가온전선(000500)|30|spread_too_wide|0.011186/0.011312|173.5/10026.0|5.0/5.0|neutral|spread=wide\|price=high\|depth=normal\|sample=rich|
|SK이터닉스(475150)|23|spread_microstructure_wide|0.009597/0.011538|81.0/1282.0|5.0/6.0|neutral|spread=wide\|price=high\|depth=thick\|sample=rich|
|금호건설(002990)|10|spread_microstructure_wide|0.005825/0.009184|81.0/879.0|6.0/9.0|neutral|spread=wide\|price=mid\|depth=thick\|sample=rich|
|제주반도체(080220)|3|spread_microstructure_wide|0.005865/0.006849|220.0/932.0|6.0/7.0|neutral|spread=wide\|price=high\|depth=normal\|sample=rich|
|시노펙스(025320)|2|spread_microstructure_wide|0.004143/0.006623|887.0/1400.0|2.5/4.0|neutral|spread=wide\|price=low\|depth=thick\|sample=rich|
|일진전기(103590)|1|spread_microstructure_wide|0.006485/0.006485|290.0/290.0|5.0/5.0|neutral|spread=wide\|price=high\|depth=thick\|sample=rich|

## top rows by max delta

|종목|첫감시|마지막|상승여부|maxΔ|latestΔ|BUY전 주 blocker|class|stale평가|refresh회복|stale유형|max quote age|BUY전 통과신호|AI|실제submit|흐름|
|---|---:|---:|---|---:|---:|---|---|---:|---:|---|---:|---:|---:|---:|---|
|가온전선(000500)|11:17:44|12:58:11|rising|20.44%|20.44%|`blocked_strength_momentum`/latency_state_danger|-|25|34|diagnostic_quote_age_stale|71310.0|-|73/WAIT|0|11:17:44 latency_block:latency_state_danger(+20.44%) -> 11:52:05 blocked_ai_score(+20.44%) -> 11:52:05 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+20.44%) -> 11:55:34 blocked_ai_score(+20.44%) -> ... -> 12:57:41 blocked_strength_momentum:below_strength_base(+20.44%) -> 12:58:11 blocked_ai_score(+20.44%) -> 12:58:11 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+20.44%)|
|금호건설(002990)|11:05:12|12:56:10|rising|7.00%|7.00%|`latency_block`/latency_state_danger|-|8|13|diagnostic_quote_age_stale|5184.0|-|62/WAIT|0|11:05:12 blocked_strength_momentum:below_strength_base(+0.00%) -> 11:05:12 blocked_vpw(+0.00%) -> 11:05:12 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%) -> 11:09:17 blocked_strength_momentum:below_strength_base(+0.00%) -> ... -> 12:00:15 blocked_ai_score(+0.00%) -> 12:00:15 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.00%) -> 12:04:20 latency_block:latency_state_danger(+0.72%)|
|일진전기(103590)|12:58:54|12:58:54|rising|5.14%|5.14%|`latency_block`/latency_state_danger|-|0|1|-||-|0/|0|12:58:54 latency_block:latency_state_danger(+5.14%)|
|SK이터닉스(475150)|11:21:09|12:59:41|rising|4.06%|4.06%|`blocked_strength_momentum`/latency_state_danger|-|53|29|diagnostic_quote_age_stale|74880.0|-|75/WAIT|0|11:21:09 latency_block:latency_state_danger(+4.06%) -> 11:47:28 ai_confirmed(+4.06%) -> 11:47:28 wait65_79_ev_candidate(+4.06%) -> 11:47:28 first_ai_wait(+4.06%) -> ... -> 12:56:16 blocked_strength_momentum:below_strength_base(+4.06%) -> 12:56:57 blocked_strength_momentum:insufficient_history(+4.06%) -> 12:59:06 blocked_strength_momentum:below_strength_base(+4.06%)|
|삼화콘덴서(001820)|11:01:20|12:57:55|rising|2.57%|2.57%|`blocked_strength_momentum`/blocked_ai_score_below_buy_score_threshold|-|33|18|diagnostic_quote_age_stale|29882.0|-|69/WAIT|0|11:01:20 blocked_strength_momentum:below_window_buy_value(+2.57%) -> 11:01:44 blocked_ai_score(+2.57%) -> 11:01:44 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+2.57%) -> 11:05:31 blocked_strength_momentum:below_buy_ratio(+2.57%) -> ... -> 12:57:43 blocked_strength_momentum:below_buy_ratio(+2.57%) -> 12:57:55 blocked_ai_score(+2.57%) -> 12:57:55 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+2.57%)|
|져스텍(153890)|11:59:06|12:56:25|rising|2.49%|2.49%|`ai_confirmed_terminal_no_budget`/blocked_ai_score_below_buy_score_threshold|-|4|9|diagnostic_quote_age_stale|18322.0|-|66/WAIT|0|11:59:06 blocked_liquidity(+2.49%) -> 11:59:08 ai_confirmed(+2.49%) -> 11:59:10 first_ai_wait(+2.49%) -> 11:59:10 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+2.49%) -> ... -> 12:53:18 blocked_ai_score(+2.49%) -> 12:53:18 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+2.49%) -> 12:56:25 blocked_strength_momentum:below_strength_base(+2.49%)|
|시노펙스(025320)|12:33:30|12:54:34|rising|1.31%|1.31%|`latency_block`/latency_state_danger|-|0|4|-|2713.0|-|74/WAIT|0|12:33:30 blocked_overbought(+0.00%) -> 12:33:32 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 12:33:32 blocked_vpw(+0.00%) -> 12:33:33 ai_confirmed(+0.00%) -> 12:33:33 wait65_79_ev_candidate(+0.00%) -> 12:33:33 first_ai_wait(+0.00%) -> 12:33:33 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> 12:45:47 latency_block:latency_state_danger(+1.31%)|
|테스(095610)|11:00:16|12:55:15|rising|1.24%|1.24%|`blocked_ai_score`/blocked_ai_score_below_buy_score_threshold|-|19|6|diagnostic_quote_age_stale|30243.0|-|60/WAIT|0|11:00:16 blocked_ai_score(+1.24%) -> 11:00:16 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+1.24%) -> 11:03:56 blocked_strength_momentum:below_buy_ratio(+1.24%) -> 11:03:56 blocked_vpw(+1.24%) -> ... -> 12:55:15 ai_confirmed(+1.24%) -> 12:55:15 blocked_ai_score(+1.24%) -> 12:55:15 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+1.24%)|
|LS ELECTRIC(010120)|11:02:09|12:36:09|rising|1.07%|1.07%|`latency_block`/latency_state_danger|-|0|36|-||-|70/|0|11:02:09 latency_block:latency_state_danger(+1.07%)|
|제주반도체(080220)|12:04:35|12:59:49|rising|0.78%|0.78%|`latency_block`/latency_state_danger|pre_submit_quality_guard|10|5|diagnostic_quote_age_stale|5743.0|-|60/WAIT|0|12:06:51 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 12:06:51 blocked_vpw(+0.00%) -> 12:06:53 ai_confirmed(+0.00%) -> 12:06:53 first_ai_wait(+0.00%) -> ... -> 12:16:04 blocked_ai_score(+0.00%) -> 12:16:04 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.00%) -> 12:32:03 latency_block:latency_state_danger(+0.78%)|
|원익IPS(240810)|11:29:00|12:57:35|rising|0.55%|0.55%|`blocked_strength_momentum`/below_buy_ratio|-|46|21|diagnostic_quote_age_stale|33231.0|-|73/WAIT|0|11:29:00 blocked_strength_momentum:below_buy_ratio(+0.55%) -> 11:29:00 blocked_vpw(+0.55%) -> 11:29:01 ai_confirmed(+0.55%) -> 11:29:01 first_ai_wait(+0.55%) -> ... -> 12:55:28 blocked_strength_momentum:below_buy_ratio(+0.55%) -> 12:57:35 blocked_ai_score(+0.55%) -> 12:57:35 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.55%)|
|저스템(417840)|11:00:51|11:00:51|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|-|0|1|-|73.0|-|50/|0|11:00:51 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|미래산업(025560)|11:01:30|12:11:05|flat_or_falling|0.00%|0.00%|`blocked_overbought`/insufficient_history|-|6|3|diagnostic_quote_age_stale|4851.0|-|50/|0|11:01:30 blocked_overbought(+0.00%) -> 11:01:30 blocked_strength_momentum:insufficient_history(+0.00%) -> 11:09:46 blocked_overbought(+0.00%) -> 11:10:25 blocked_strength_momentum:insufficient_history(+0.00%) -> 12:08:16 blocked_overbought(+0.00%) -> 12:08:16 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 12:11:02 blocked_overbought(+0.00%) -> 12:11:05 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|스피어(347700)|11:06:13|12:28:21|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_window_buy_value|-|2|9|diagnostic_quote_age_stale|5647.0|-|50/|0|11:06:13 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 11:15:51 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%) -> 11:20:10 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 11:20:10 blocked_vpw(+0.00%) -> ... -> 12:28:21 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 12:28:21 blocked_vpw(+0.00%) -> 12:28:21 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%)|
|주성엔지니어링(036930)|11:07:05|12:45:51|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_buy_ratio|-|19|8|diagnostic_quote_age_stale|5220.0|12:02:53|62/WAIT|0|11:07:05 blocked_strength_momentum:below_buy_ratio(+0.00%) -> 11:07:05 blocked_vpw(+0.00%) -> 11:07:05 blocked_gap_from_scan(+0.00%) -> 11:07:06 ai_confirmed(+0.00%) -> ... -> 12:45:51 ai_confirmed(+0.00%) -> 12:45:51 blocked_ai_score(+0.00%) -> 12:45:51 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.00%)|
|한울반도체(320000)|12:04:35|12:43:50|flat_or_falling|0.00%|-3.37%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|3|3|diagnostic_quote_age_stale|6072.0|-|72/WAIT|0|12:08:07 blocked_strength_momentum:insufficient_history(+0.00%) -> 12:13:52 blocked_strength_momentum:below_strength_base(+0.00%) -> 12:13:52 blocked_vpw(+0.00%) -> 12:13:52 blocked_liquidity(+0.00%) -> ... -> 12:13:53 first_ai_wait(+0.00%) -> 12:13:53 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> 12:16:08 blocked_strength_momentum:below_strength_base(+0.00%)|
|케이씨텍(281820)|12:22:42|12:57:02|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|4|-|2761.0|-|63/WAIT|0|12:26:19 blocked_overbought(+0.00%) -> 12:26:21 ai_confirmed(+0.00%) -> 12:26:21 wait65_79_ev_candidate(+0.00%) -> 12:26:21 first_ai_wait(+0.00%) -> ... -> 12:52:33 ai_confirmed(+0.00%) -> 12:52:33 blocked_ai_score(+0.00%) -> 12:52:33 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.00%)|
|SK(034730)|12:30:15|12:34:01|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-|2400.0|-|50/|0|12:33:38 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|솔브레인(357780)|12:31:46|12:39:07|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|3|-|4343.0|-|50/|0|12:36:20 blocked_strength_momentum:below_buy_ratio(+0.00%) -> 12:36:20 blocked_vpw(+0.00%) -> 12:36:20 blocked_liquidity(+0.00%) -> 12:36:20 blocked_ai_score:ai_score_50_buy_hold_override(+0.00%)|
|사조산업(007160)|12:36:18|12:39:07|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|non_actionable_guard_or_backpressure|0|0|-||-||0|-|
|피에스케이(319660)|12:37:48|12:41:33|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|소룩스(290690)|12:39:19|12:42:17|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|프로텍(053610)|12:39:19|12:42:17|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|나인앤컴퍼니(366030)|12:39:19|12:39:19|flat_or_falling|0.00%|0.00%|`-`/-|-|0|0|-||-||0|-|
|HPSP(403870)|12:42:20|12:48:47|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|성호전자(043260)|12:42:20|12:48:47|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|아바텍(149950)|12:42:20|12:46:29|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|코칩(126730)|12:43:51|12:46:29|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|1|-|505.0|-|50/|0|12:46:03 blocked_strength_momentum:below_strength_base(+0.00%)|
|뉴파워프라즈마(144960)|12:46:52|12:49:39|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|아스플로(159010)|12:46:52|12:49:39|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|케이뱅크(279570)|12:49:54|12:56:17|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|1|-|2462.0|-|50/|0|12:55:56 blocked_strength_momentum:below_window_buy_value(+0.00%)|
|액스비스(000110)|12:49:54|12:54:47|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/ws_snapshot_missing_or_zero|non_actionable_guard_or_backpressure|0|0|-||-||0|-|
|산일전기(062040)|12:54:05|12:54:05|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_strength_base|-|0|1|-|528.0|-|50/|0|12:54:05 blocked_strength_momentum:below_strength_base(+0.00%)|
|아이에스티이(212710)|12:54:25|12:57:43|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|신성에스티(416180)|12:55:56|12:59:49|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|1|0|diagnostic_quote_age_stale|5181.0|-|50/|0|12:59:02 blocked_strength_momentum:below_strength_base(+0.00%)|
|심텍(222800)|12:57:27|12:59:49|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|0|0|-||-||0|-|
|키스트론(475430)|12:58:59|12:58:59|flat_or_falling|0.00%|0.00%|`blocked_strength_momentum`/below_strength_base|-|0|1|-|157.0|-|50/|0|12:58:59 blocked_strength_momentum:below_strength_base(+0.00%)|

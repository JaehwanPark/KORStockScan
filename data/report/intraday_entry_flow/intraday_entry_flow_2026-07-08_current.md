# 2026-07-08 12:00 이후 감시대상 BUY 전 흐름

- generated_at: 2026-07-08T12:20:00+09:00
- source_events: /home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-08.jsonl
- source_diagnostic: /home/ubuntu/KORStockScan/data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-07-08.json
- event_window_since: 12:00:00
- event_window_until: None
- symbol_count: 24
- rising_symbol_count_by_max_delta: 3
- rising_missed_buy_count_in_latest_diagnostic: 0
- rising_missed_symbol_count_in_report: 0
- rising_missed_residual_excluding_forced_scout_symbol_count: 0
- rising_missed_forced_scout_event_count: 3
- rising_missed_forced_scout_symbol_count: 17
- rising_missed_forced_scout_residual_symbol_count: 0
- real_submit_symbol_count_in_latest_diagnostic: None
- buy_signal_or_pre_submit_pass_seen_symbols: 14
- stale_eval_symbol_count: 19
- rising_stale_eval_symbol_count: 3
- rising_fresh_only_symbol_count: 0
- stale_refresh_recovered_symbol_count: 16

## forced scout observation

- event_count: 3
- symbol_count: 17
- symbols: 008930, 009150, 014970, 018260, 042040, 042660, 043260, 073240, 078160, 086520, 114840, 200710, 226320, 352820, 365660, 399720, 402340
- rising_missed_residual_symbols: -
- rising_missed_residual_excluding_forced_scout_symbols: -
- decision_authority: source_quality_only
- runtime_effect: False

## blocker rollup

- 8: `scalping_scanner_promotion_latency_trace` / `scanner_fast_precheck_subscription_recheck_snapshot_applied`
- 5: `scalping_scanner_runtime_target_attach` / `-`
- 4: `scalping_scanner_promotion_latency_trace` / `below_strength_base`
- 2: `scalping_scanner_promotion_latency_trace` / `scanner_fast_precheck_stability_pending`
- 2: `scalping_scanner_promotion_latency_trace` / `below_window_buy_value`
- 1: `scalping_scanner_promotion_latency_trace` / `ws_snapshot_missing_or_zero_recovered`
- 1: `scalping_scanner_promotion_latency_trace` / `-`
- 1: `strength_momentum_observed` / `below_window_buy_value`

## rising-symbol blocker rollup

- 1: `scalping_scanner_promotion_latency_trace` / `ws_snapshot_missing_or_zero_recovered`
- 1: `scalping_scanner_promotion_latency_trace` / `-`
- 1: `scalping_scanner_promotion_latency_trace` / `scanner_fast_precheck_subscription_recheck_snapshot_applied`

## rising fresh-only blocker rollup


## rising stale-mixed blocker rollup

- 1: `scalping_scanner_promotion_latency_trace` / `ws_snapshot_missing_or_zero_recovered`
- 1: `scalping_scanner_promotion_latency_trace` / `-`
- 1: `scalping_scanner_promotion_latency_trace` / `scanner_fast_precheck_subscription_recheck_snapshot_applied`

## stale-eval rollup

- 18: `scalping_scanner_fast_precheck`
- 1: `score65_74_recovery_probe_blocked`

## stale-eval category rollup

- 19: `diagnostic_quote_age_stale`

## latency danger root cause

|종목|건수|top cause|spread ratio med/max|ws age med/max|spread ticks med/max|micro|bucket|
|---|---:|---|---:|---:|---:|---|---|
|브이엠(089970)|1|spread_microstructure_wide|0.005807/0.005807|326.0/326.0|5.0/5.0|neutral|spread=wide\|price=high\|depth=normal\|sample=rich|

## top rows by max delta

|종목|첫감시|마지막|상승여부|maxΔ|latestΔ|BUY전 주 blocker|class|stale평가|refresh회복|stale유형|max quote age|BUY전 통과신호|AI|실제submit|흐름|
|---|---:|---:|---|---:|---:|---|---|---:|---:|---|---:|---:|---:|---:|---|
|레몬헬스케어(365660)|12:00:07|12:15:24|rising|6.19%|6.19%|`scalping_scanner_promotion_latency_trace`/ws_snapshot_missing_or_zero_recovered|-|11|0|diagnostic_quote_age_stale|70794.0|-|62/WAIT|0|12:00:07 scalping_scanner_promotion_latency_trace(+6.19%) -> 12:00:07 scalping_scanner_fast_precheck(+6.19%) -> 12:00:07 scalping_scanner_runtime_queue_lag(+6.19%) -> 12:00:52 scalping_scanner_promotion_latency_trace(+6.19%) -> ... -> 12:13:40 entry_split_order_plan_applied(+6.19%) -> 12:13:55 entry_reprice_after_submit_blocked(+6.19%) -> 12:15:24 partial_fill_reconciled(+6.19%)|
|성호전자(043260)|12:00:52|12:10:57|rising|1.52%|1.52%|`scalping_scanner_promotion_latency_trace`/-|-|8|0|diagnostic_quote_age_stale|70803.0|-||0|12:00:52 scalping_scanner_promotion_latency_trace(+1.52%) -> 12:00:52 scalping_scanner_fast_precheck(+1.52%) -> 12:00:52 scalping_scanner_runtime_queue_lag(+1.52%) -> 12:01:49 scalping_scanner_promotion_latency_trace(+1.52%) -> ... -> 12:10:57 scalping_scanner_promotion_latency_trace(+1.52%) -> 12:10:57 scalping_scanner_fast_precheck(+1.52%) -> 12:10:57 scalping_scanner_runtime_queue_lag(+1.52%)|
|한국콜마(161890)|12:00:07|12:10:57|rising|0.57%|-0.27%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|10|23|diagnostic_quote_age_stale|57516.0|12:00:30|58/WAIT|0|12:00:07 scalping_scanner_promotion_latency_trace(-0.27%) -> 12:00:07 scalping_scanner_fast_precheck(-0.27%) -> 12:00:07 scalping_scanner_runtime_queue_lag(-0.27%) -> 12:00:07 scalping_scanner_promotion_latency_trace(-0.27%) -> ... -> 12:09:09 ai_confirmed_terminal_no_budget:entry_policy_no_buy_score_prior(-0.27%) -> 12:09:09 scalp_entry_action_decision_snapshot:mixed core signals: supply-demand neutral (buy_pressure_10t 50), speed improving (tick_acceleration_ratio 4.0, recent_5t(-0.27%) -> 12:10:57 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(-0.27%)|
|삼성전기(009150)|12:00:07|12:18:59|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|21|21|diagnostic_quote_age_stale|70816.0|12:00:22|63/WAIT|0|12:00:07 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:07 scalping_scanner_fast_precheck(+0.00%) -> 12:00:07 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:00:07 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 12:18:57 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> 12:18:59 entry_ai_price_canary_applied:Defensive price aligns with best bid; low latency risk and sufficient bid depth(+0.00%) -> 12:18:59 scalp_entry_action_decision_snapshot:scalp_live_simulator(+0.00%)|
|현대차(005380)|12:00:07|12:19:09|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|17|30|diagnostic_quote_age_stale|57540.0|12:05:41|64/WAIT|0|12:00:07 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:07 scalping_scanner_fast_precheck(+0.00%) -> 12:00:07 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:00:07 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 12:19:07 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> 12:19:09 entry_ai_price_canary_applied:Defensive price aligns with best bid and avoids aggressive chase cost(+0.00%) -> 12:19:09 scalp_entry_action_decision_snapshot:scalp_live_simulator(+0.00%)|
|서산(079650)|12:00:07|12:10:57|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|7|8|diagnostic_quote_age_stale|57434.0|-|50/|0|12:00:07 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:07 scalping_scanner_fast_precheck(+0.00%) -> 12:00:07 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:00:07 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 12:09:36 blocked_strength_momentum:below_strength_base(+0.00%) -> 12:09:38 scalping_scanner_watch_eviction:scanner_hardgate_prefilter(+0.00%) -> 12:10:57 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%)|
|SK스퀘어(402340)|12:00:07|12:18:51|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|15|22|diagnostic_quote_age_stale|57527.0|12:09:46|62/WAIT|0|12:00:07 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:07 scalping_scanner_fast_precheck(+0.00%) -> 12:00:07 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:00:07 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 12:18:49 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> 12:18:51 entry_ai_price_canary_applied:Defensive price aligns with best bid; orderbook depth supports immediate fill probability(+0.00%) -> 12:18:51 scalp_entry_action_decision_snapshot:scalp_live_simulator(+0.00%)|
|상지건설(042940)|12:00:07|12:19:09|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_stability_pending|-|21|0|diagnostic_quote_age_stale|75561.0|-||0|12:00:07 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:07 scalping_scanner_fast_precheck(+0.00%) -> 12:00:07 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:00:07 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%) -> ... -> 12:18:30 scalping_scanner_fast_precheck(+0.00%) -> 12:18:30 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:19:09 scalping_scanner_watching_runtime_skip:scanner_heavy_eval_stale_snapshot_recheck(+0.00%)|
|LG유플러스(032640)|12:00:07|12:19:09|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|24|15|diagnostic_quote_age_stale|50179.0|12:11:39|50/DROP|0|12:00:07 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:07 scalping_scanner_fast_precheck(+0.00%) -> 12:00:07 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:00:07 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 12:18:30 scalping_scanner_fast_precheck(+0.00%) -> 12:18:30 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:19:09 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%)|
|에스에이엠티(031330)|12:00:07|12:06:55|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_stability_pending|-|7|2|diagnostic_quote_age_stale|75824.0|-|50/|0|12:00:07 scalping_scanner_watching_runtime_skip:scanner_heavy_eval_stale_snapshot_recheck(+0.00%) -> 12:00:14 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:14 scalping_scanner_fast_precheck(+0.00%) -> 12:00:14 scalping_scanner_runtime_queue_lag(+0.00%) -> ... -> 12:05:32 blocked_strength_momentum:below_strength_base(+0.00%) -> 12:05:34 scalping_scanner_watch_eviction:scanner_hardgate_prefilter(+0.00%) -> 12:06:55 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%)|
|삼성전자(005930)|12:00:08|12:19:10|flat_or_falling|0.00%|0.00%|`scalping_scanner_runtime_target_attach`/-|-|0|0|-||-||0|12:00:08 scalping_scanner_runtime_target_attach -> 12:12:11 scalping_scanner_candidate_promoted(+0.00%) -> 12:12:11 scalping_scanner_runtime_target_attach(+0.00%) -> 12:14:41 scalping_scanner_candidate_promoted(+0.00%) -> 12:14:41 scalping_scanner_runtime_target_attach(+0.00%)|
|현대백화점(069960)|12:00:52|12:14:54|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|12|16|diagnostic_quote_age_stale|72400.0|12:07:38|0/DROP|0|12:00:52 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:52 scalping_scanner_fast_precheck(+0.00%) -> 12:00:52 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:00:52 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 12:14:54 scalping_scanner_fast_precheck(+0.00%) -> 12:14:54 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%) -> 12:14:54 scalping_scanner_watching_runtime_skip:scanner_full_eval_loop_budget_deferred(+0.00%)|
|주성엔지니어링(036930)|12:00:52|12:19:09|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/below_strength_base|-|18|20|diagnostic_quote_age_stale|70822.0|12:01:42|62/WAIT|0|12:00:52 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:52 scalping_scanner_fast_precheck(+0.00%) -> 12:00:52 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:00:52 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 12:18:30 scalping_scanner_fast_precheck(+0.00%) -> 12:18:30 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:19:09 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%)|
|브이엠(089970)|12:06:54|12:12:09|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/below_window_buy_value|-|2|11|diagnostic_quote_age_stale|71381.0|12:07:10|62/WAIT|0|12:06:54 scalping_scanner_candidate_promoted(+0.00%) -> 12:06:54 scalping_scanner_runtime_target_attach(+0.00%) -> 12:07:01 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:07:01 scalping_scanner_fast_precheck(+0.00%) -> ... -> 12:12:03 latency_block:latency_state_danger(+0.00%) -> 12:12:03 scalp_entry_action_decision_snapshot:latency_state_danger(+0.00%) -> 12:12:09 scalping_scanner_watch_eviction:scanner_hardgate_prefilter(+0.00%)|
|금호타이어(073240)|12:10:25|12:18:42|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/below_strength_base|-|9|11|diagnostic_quote_age_stale|42143.0|12:18:42|0/DROP|0|12:10:25 scalping_scanner_candidate_promoted(+0.00%) -> 12:10:25 scalping_scanner_runtime_target_attach(+0.00%) -> 12:11:04 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:11:04 scalping_scanner_fast_precheck(+0.00%) -> ... -> 12:18:42 score65_74_recovery_probe_blocked(+0.00%) -> 12:18:42 first_ai_wait(+0.00%) -> 12:18:42 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|
|동신건설(025950)|12:12:11|12:19:54|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/below_strength_base|-|12|12|diagnostic_quote_age_stale|42212.0|12:19:53|62/WAIT|0|12:12:11 scalping_scanner_candidate_promoted(+0.00%) -> 12:12:11 scalping_scanner_runtime_target_attach(+0.00%) -> 12:12:51 scalping_scanner_watching_runtime_skip:ws_snapshot_missing_or_zero(+0.00%) -> 12:12:53 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 12:19:53 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%) -> 12:19:54 entry_ai_price_canary_applied:defensive_order_price is default due to insufficient micro data and no bearish signal(+0.00%) -> 12:19:54 scalp_entry_action_decision_snapshot:scalp_live_simulator(+0.00%)|
|효성화학(298000)|12:12:11|12:19:54|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|9|6|diagnostic_quote_age_stale|42248.0|12:14:04|60/WAIT|0|12:12:11 scalping_scanner_candidate_promoted(+0.00%) -> 12:12:11 scalping_scanner_runtime_target_attach(+0.00%) -> 12:12:51 scalping_scanner_watching_runtime_skip:ws_snapshot_missing_or_zero(+0.00%) -> 12:13:52 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 12:19:20 scalping_scanner_fast_precheck(+0.00%) -> 12:19:54 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:19:54 scalping_scanner_heavy_eval_lag(+0.00%)|
|그래피(318060)|12:12:11|12:19:38|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/below_strength_base|-|10|10|diagnostic_quote_age_stale|31097.0|12:14:34|50/DROP|0|12:12:11 scalping_scanner_candidate_promoted(+0.00%) -> 12:12:11 scalping_scanner_runtime_target_attach(+0.00%) -> 12:12:51 scalping_scanner_watching_runtime_skip:ws_snapshot_missing_or_zero(+0.00%) -> 12:13:52 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 12:19:31 scalping_scanner_heavy_eval_lag(+0.00%) -> 12:19:38 strength_momentum_observed:below_strength_base(+0.00%) -> 12:19:38 blocked_strength_momentum:below_strength_base(+0.00%)|
|덕산하이메탈(077360)|12:12:11|12:19:27|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/below_window_buy_value|-|12|10|diagnostic_quote_age_stale|33868.0|12:17:32|0/DROP|0|12:12:11 scalping_scanner_candidate_promoted(+0.00%) -> 12:12:11 scalping_scanner_runtime_target_attach(+0.00%) -> 12:12:51 scalping_scanner_watching_runtime_skip:ws_snapshot_missing_or_zero(+0.00%) -> 12:12:53 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 12:19:20 scalping_scanner_heavy_eval_lag(+0.00%) -> 12:19:27 strength_momentum_observed:below_window_buy_value(+0.00%) -> 12:19:27 strength_momentum_stability_recheck_pending:below_window_buy_value(+0.00%)|
|한올바이오파마(009420)|12:10:48|12:10:57|flat_or_falling|-1.80%|-1.80%|`strength_momentum_observed`/below_window_buy_value|-|2|5|diagnostic_quote_age_stale|5924.0|12:10:57|0/DROP|0|12:10:48 strength_momentum_observed:below_window_buy_value(-1.80%) -> 12:10:53 blocked_strength_momentum:below_window_buy_value(-1.80%) -> 12:10:53 blocked_vpw(-1.80%) -> 12:10:57 ai_confirmed(-1.80%) -> ... -> 12:10:57 score65_74_recovery_probe_blocked(-1.80%) -> 12:10:57 first_ai_wait(-1.80%) -> 12:10:57 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(-1.80%)|
|메디포스트(078160)|12:00:08|12:19:10|unknown|||`scalping_scanner_runtime_target_attach`/-|-|0|0|-||-||0|12:00:08 scalping_scanner_runtime_target_attach|
|한미반도체(042700)|12:00:08|12:19:10|unknown|||`scalping_scanner_runtime_target_attach`/-|-|0|0|-||-||0|12:00:08 scalping_scanner_runtime_target_attach|
|LS ELECTRIC(010120)|12:00:08|12:19:10|unknown|||`scalping_scanner_runtime_target_attach`/-|-|0|0|-||-||0|12:00:08 scalping_scanner_runtime_target_attach|
|삼표시멘트(038500)|12:00:08|12:19:10|unknown|||`scalping_scanner_runtime_target_attach`/-|-|0|0|-||-||0|12:00:08 scalping_scanner_runtime_target_attach|

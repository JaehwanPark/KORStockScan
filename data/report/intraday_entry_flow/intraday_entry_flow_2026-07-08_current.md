# 2026-07-08 12:00 이후 감시대상 BUY 전 흐름

- generated_at: 2026-07-08T12:10:00+09:00
- source_events: /home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-08.jsonl
- source_diagnostic: /home/ubuntu/KORStockScan/data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-07-08.json
- event_window_since: 12:00:00
- event_window_until: None
- symbol_count: 18
- rising_symbol_count_by_max_delta: 3
- rising_missed_buy_count_in_latest_diagnostic: 0
- rising_missed_symbol_count_in_report: 0
- rising_missed_residual_excluding_forced_scout_symbol_count: 0
- rising_missed_forced_scout_event_count: 0
- rising_missed_forced_scout_symbol_count: 17
- rising_missed_forced_scout_residual_symbol_count: 0
- real_submit_symbol_count_in_latest_diagnostic: None
- buy_signal_or_pre_submit_pass_seen_symbols: 7
- stale_eval_symbol_count: 12
- rising_stale_eval_symbol_count: 3
- rising_fresh_only_symbol_count: 0
- stale_refresh_recovered_symbol_count: 10

## forced scout observation

- event_count: 0
- symbol_count: 17
- symbols: 008930, 009150, 014970, 018260, 042040, 042660, 043260, 073240, 078160, 086520, 114840, 200710, 226320, 352820, 365660, 399720, 402340
- rising_missed_residual_symbols: -
- rising_missed_residual_excluding_forced_scout_symbols: -
- decision_authority: source_quality_only
- runtime_effect: False

## blocker rollup

- 7: `scalping_scanner_promotion_latency_trace` / `scanner_fast_precheck_subscription_recheck_snapshot_applied`
- 5: `scalping_scanner_runtime_target_attach` / `-`
- 2: `scalping_scanner_promotion_latency_trace` / `-`
- 2: `scalping_scanner_promotion_latency_trace` / `scanner_fast_precheck_stability_pending`
- 2: `scalping_scanner_promotion_latency_trace` / `below_window_buy_value`

## rising-symbol blocker rollup

- 2: `scalping_scanner_promotion_latency_trace` / `-`
- 1: `scalping_scanner_promotion_latency_trace` / `scanner_fast_precheck_subscription_recheck_snapshot_applied`

## rising fresh-only blocker rollup


## rising stale-mixed blocker rollup

- 2: `scalping_scanner_promotion_latency_trace` / `-`
- 1: `scalping_scanner_promotion_latency_trace` / `scanner_fast_precheck_subscription_recheck_snapshot_applied`

## stale-eval rollup

- 12: `scalping_scanner_fast_precheck`

## stale-eval category rollup

- 12: `diagnostic_quote_age_stale`

## top rows by max delta

|종목|첫감시|마지막|상승여부|maxΔ|latestΔ|BUY전 주 blocker|class|stale평가|refresh회복|stale유형|max quote age|BUY전 통과신호|AI|실제submit|흐름|
|---|---:|---:|---|---:|---:|---|---|---:|---:|---|---:|---:|---:|---:|---|
|레몬헬스케어(365660)|12:00:07|12:08:31|rising|6.19%|6.19%|`scalping_scanner_promotion_latency_trace`/-|-|8|0|diagnostic_quote_age_stale|57466.0|-||0|12:00:07 scalping_scanner_promotion_latency_trace(+6.19%) -> 12:00:07 scalping_scanner_fast_precheck(+6.19%) -> 12:00:07 scalping_scanner_runtime_queue_lag(+6.19%) -> 12:00:52 scalping_scanner_promotion_latency_trace(+6.19%) -> ... -> 12:08:31 scalping_scanner_promotion_latency_trace(+6.19%) -> 12:08:31 scalping_scanner_fast_precheck(+6.19%) -> 12:08:31 scalping_scanner_runtime_queue_lag(+6.19%)|
|성호전자(043260)|12:00:52|12:08:31|rising|1.52%|1.52%|`scalping_scanner_promotion_latency_trace`/-|-|7|0|diagnostic_quote_age_stale|57691.0|-||0|12:00:52 scalping_scanner_promotion_latency_trace(+1.52%) -> 12:00:52 scalping_scanner_fast_precheck(+1.52%) -> 12:00:52 scalping_scanner_runtime_queue_lag(+1.52%) -> 12:01:49 scalping_scanner_promotion_latency_trace(+1.52%) -> ... -> 12:08:31 scalping_scanner_promotion_latency_trace(+1.52%) -> 12:08:31 scalping_scanner_fast_precheck(+1.52%) -> 12:08:31 scalping_scanner_runtime_queue_lag(+1.52%)|
|한국콜마(161890)|12:00:07|12:09:09|rising|0.57%|-0.27%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|10|23|diagnostic_quote_age_stale|57516.0|12:00:30|58/WAIT|0|12:00:07 scalping_scanner_promotion_latency_trace(-0.27%) -> 12:00:07 scalping_scanner_fast_precheck(-0.27%) -> 12:00:07 scalping_scanner_runtime_queue_lag(-0.27%) -> 12:00:07 scalping_scanner_promotion_latency_trace(-0.27%) -> ... -> 12:09:09 blocked_ai_score(-0.27%) -> 12:09:09 ai_confirmed_terminal_no_budget:entry_policy_no_buy_score_prior(-0.27%) -> 12:09:09 scalp_entry_action_decision_snapshot:mixed core signals: supply-demand neutral (buy_pressure_10t 50), speed improving (tick_acceleration_ratio 4.0, recent_5t(-0.27%)|
|삼성전기(009150)|12:00:07|12:07:51|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|6|14|diagnostic_quote_age_stale|49456.0|12:00:22|0/DROP|0|12:00:07 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:07 scalping_scanner_fast_precheck(+0.00%) -> 12:00:07 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:00:07 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 12:07:51 blocked_ai_score(+0.00%) -> 12:07:51 ai_confirmed_terminal_no_budget:entry_policy_no_buy_score_prior(+0.00%) -> 12:07:51 scalp_entry_action_decision_snapshot:openai_ws_http_fallback_timeout_fail_closed(+0.00%)|
|현대차(005380)|12:00:07|12:09:28|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|10|13|diagnostic_quote_age_stale|57540.0|12:05:41|62/WAIT|0|12:00:07 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:07 scalping_scanner_fast_precheck(+0.00%) -> 12:00:07 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:00:07 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 12:09:28 blocked_ai_score(+0.00%) -> 12:09:28 ai_confirmed_terminal_no_budget:entry_policy_no_buy_score_prior(+0.00%) -> 12:09:28 scalp_entry_action_decision_snapshot:mixed signals: buy_pressure_10t 50.0 and curr_vs_ma5_bp 10.6 with favorable micro_vwap distance, but quote_stale true, q(+0.00%)|
|서산(079650)|12:00:07|12:09:38|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|7|8|diagnostic_quote_age_stale|57434.0|-|50/|0|12:00:07 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:07 scalping_scanner_fast_precheck(+0.00%) -> 12:00:07 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:00:07 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 12:09:35 strength_momentum_observed:below_strength_base(+0.00%) -> 12:09:36 blocked_strength_momentum:below_strength_base(+0.00%) -> 12:09:38 scalping_scanner_watch_eviction:scanner_hardgate_prefilter(+0.00%)|
|SK스퀘어(402340)|12:00:07|12:09:46|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|7|12|diagnostic_quote_age_stale|57527.0|12:09:46|0/DROP|0|12:00:07 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:07 scalping_scanner_fast_precheck(+0.00%) -> 12:00:07 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:00:07 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 12:09:46 blocked_ai_score(+0.00%) -> 12:09:46 ai_confirmed_terminal_no_budget:entry_policy_no_buy_score_prior(+0.00%) -> 12:09:46 scalp_entry_action_decision_snapshot:openai_ws_http_fallback_timeout_fail_closed(+0.00%)|
|상지건설(042940)|12:00:07|12:08:49|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_stability_pending|-|11|0|diagnostic_quote_age_stale|75561.0|-||0|12:00:07 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:07 scalping_scanner_fast_precheck(+0.00%) -> 12:00:07 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:00:07 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%) -> ... -> 12:08:49 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:08:49 scalping_scanner_fast_precheck(+0.00%) -> 12:08:49 scalping_scanner_runtime_queue_lag(+0.00%)|
|LG유플러스(032640)|12:00:07|12:08:49|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|13|2|diagnostic_quote_age_stale|50179.0|-|50/|0|12:00:07 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:07 scalping_scanner_fast_precheck(+0.00%) -> 12:00:07 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:00:07 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 12:08:49 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:08:49 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:08:49 scalping_scanner_fast_precheck(+0.00%)|
|에스에이엠티(031330)|12:00:07|12:06:55|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_stability_pending|-|7|2|diagnostic_quote_age_stale|75824.0|-|50/|0|12:00:07 scalping_scanner_watching_runtime_skip:scanner_heavy_eval_stale_snapshot_recheck(+0.00%) -> 12:00:14 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:14 scalping_scanner_fast_precheck(+0.00%) -> 12:00:14 scalping_scanner_runtime_queue_lag(+0.00%) -> ... -> 12:05:32 blocked_strength_momentum:below_strength_base(+0.00%) -> 12:05:34 scalping_scanner_watch_eviction:scanner_hardgate_prefilter(+0.00%) -> 12:06:55 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%)|
|현대백화점(069960)|12:00:52|12:08:31|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/below_window_buy_value|-|7|11|diagnostic_quote_age_stale|49174.0|12:07:38|0/DROP|0|12:00:52 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:52 scalping_scanner_fast_precheck(+0.00%) -> 12:00:52 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:00:52 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 12:07:38 ai_confirmed_terminal_no_budget:entry_policy_no_buy_score_prior(+0.00%) -> 12:07:38 scalp_entry_action_decision_snapshot:openai_ws_http_fallback_timeout_fail_closed(+0.00%) -> 12:08:31 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%)|
|주성엔지니어링(036930)|12:00:52|12:07:21|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|6|9|diagnostic_quote_age_stale|49756.0|12:01:42|50/DROP|0|12:00:52 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:52 scalping_scanner_fast_precheck(+0.00%) -> 12:00:52 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:00:52 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 12:07:10 scalping_scanner_heavy_eval_lag(+0.00%) -> 12:07:16 strength_momentum_observed:below_strength_base(+0.00%) -> 12:07:21 blocked_strength_momentum:below_strength_base(+0.00%)|
|브이엠(089970)|12:06:54|12:07:10|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/below_window_buy_value|-|0|4|-|2783.0|12:07:10|62/WAIT|0|12:06:54 scalping_scanner_candidate_promoted(+0.00%) -> 12:06:54 scalping_scanner_runtime_target_attach(+0.00%) -> 12:07:01 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:07:01 scalping_scanner_fast_precheck(+0.00%) -> ... -> 12:07:10 first_ai_wait(+0.00%) -> 12:07:10 first_ai_wait_rebound_anchor_armed(+0.00%) -> 12:07:10 ai_confirmed_terminal_no_budget:first_ai_wait_big_bite_not_confirmed(+0.00%)|
|메디포스트(078160)|12:00:08|12:08:32|unknown|||`scalping_scanner_runtime_target_attach`/-|-|0|0|-||-||0|12:00:08 scalping_scanner_runtime_target_attach|
|한미반도체(042700)|12:00:08|12:08:32|unknown|||`scalping_scanner_runtime_target_attach`/-|-|0|0|-||-||0|12:00:08 scalping_scanner_runtime_target_attach|
|삼성전자(005930)|12:00:08|12:08:32|unknown|||`scalping_scanner_runtime_target_attach`/-|-|0|0|-||-||0|12:00:08 scalping_scanner_runtime_target_attach|
|LS ELECTRIC(010120)|12:00:08|12:08:32|unknown|||`scalping_scanner_runtime_target_attach`/-|-|0|0|-||-||0|12:00:08 scalping_scanner_runtime_target_attach|
|삼표시멘트(038500)|12:00:08|12:08:32|unknown|||`scalping_scanner_runtime_target_attach`/-|-|0|0|-||-||0|12:00:08 scalping_scanner_runtime_target_attach|

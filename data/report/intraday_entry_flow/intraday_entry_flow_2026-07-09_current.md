# 2026-07-09 12:00 이후 감시대상 BUY 전 흐름

- generated_at: 2026-07-09T12:20:00
- source_events: /home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-09.jsonl
- source_diagnostic: /home/ubuntu/KORStockScan/data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-07-09.json
- event_window_since: 2026-07-09T12:00:00
- event_window_until: 2026-07-09T12:20:00
- symbol_count: 29
- rising_symbol_count_by_max_delta: 3
- rising_missed_buy_count_in_latest_diagnostic: 0
- rising_missed_symbol_count_in_report: 0
- rising_missed_residual_excluding_forced_scout_symbol_count: 0
- rising_missed_forced_scout_event_count: 74
- rising_missed_forced_scout_symbol_count: 63
- rising_missed_forced_scout_residual_symbol_count: 0
- real_submit_symbol_count_in_latest_diagnostic: None
- buy_signal_or_pre_submit_pass_seen_symbols: 1
- stale_eval_symbol_count: 22
- rising_stale_eval_symbol_count: 3
- rising_fresh_only_symbol_count: 0
- stale_refresh_recovered_symbol_count: 3

## forced scout observation

- event_count: 74
- symbol_count: 63
- symbols: 000440, 000660, 000720, 001820, 002990, 003490, 004090, 005380, 005950, 006360, 006800, 007390, 007660, 008930, 009150, 010140, 010170, 011070, 015760, 017960, 024060, 032820, 032830, 036930, 037710, 042660, 042700, 043260, 047040, 052710, 055550, 068270, 080220, 082740, 086520, 086790, 091590, 094360, 105560, 161890, 178320, 189330, 200710, 204320, 214330, 222800, 257720, 319660, 336260, 347700, 347850, 348340, 352820, 365660, 394280, 399720, 402340, 415640, 439960, 445090, 476060, 476830, 477850
- rising_missed_residual_symbols: -
- rising_missed_residual_excluding_forced_scout_symbols: -
- decision_authority: source_quality_only
- runtime_effect: False

## blocker rollup

- 10: `scalping_scanner_promotion_latency_trace` / `scanner_fast_precheck_subscription_recheck_snapshot_applied`
- 5: `scalping_scanner_candidate_promoted` / `-`
- 4: `scalping_scanner_promotion_latency_trace` / `scanner_fast_precheck_stability_pending`
- 3: `scalping_scanner_runtime_target_attach` / `-`
- 2: `scalping_scanner_promotion_latency_trace` / `scanner_full_eval_loop_budget_deferred`
- 1: `scalping_scanner_promotion_latency_trace` / `latency_state_danger`
- 1: `scalping_scanner_promotion_latency_trace` / `ws_snapshot_missing_or_zero_recovered`
- 1: `scalping_scanner_promotion_latency_trace` / `insufficient_history`
- 1: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 1: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_subscription_recheck_snapshot_applied`

## rising-symbol blocker rollup

- 1: `scalping_scanner_promotion_latency_trace` / `latency_state_danger`
- 1: `scalping_scanner_promotion_latency_trace` / `ws_snapshot_missing_or_zero_recovered`
- 1: `scalping_scanner_promotion_latency_trace` / `insufficient_history`

## rising fresh-only blocker rollup


## rising stale-mixed blocker rollup

- 1: `scalping_scanner_promotion_latency_trace` / `latency_state_danger`
- 1: `scalping_scanner_promotion_latency_trace` / `ws_snapshot_missing_or_zero_recovered`
- 1: `scalping_scanner_promotion_latency_trace` / `insufficient_history`

## stale-eval rollup

- 21: `scalping_scanner_fast_precheck`
- 1: `scalping_scanner_watching_runtime_skip`

## stale-eval category rollup

- 21: `diagnostic_quote_age_stale`
- 1: `ws_snapshot_missing_or_zero`

## latency danger root cause

|종목|건수|top cause|spread ratio med/max|ws age med/max|spread ticks med/max|micro|bucket|
|---|---:|---|---:|---:|---:|---|---|
|한국석유(004090)|3|spread_microstructure_wide|0.005609/0.007974|82.0/522.0|7.0/10.0|neutral|spread=wide\|price=mid\|depth=normal\|sample=rich|
|흥구석유(024060)|2|spread_microstructure_wide|0.005494/0.005507|76.0/100.0|7.0/7.0|neutral|spread=wide\|price=mid\|depth=thick\|sample=rich|
|마키나락스(477850)|1|spread_too_wide|0.010471/0.010471|39.0/39.0|6.0/6.0|neutral|spread=wide\|price=mid\|depth=normal\|sample=rich|

## top rows by max delta

|종목|첫감시|마지막|상승여부|maxΔ|latestΔ|BUY전 주 blocker|class|stale평가|refresh회복|stale유형|max quote age|BUY전 통과신호|AI|실제submit|흐름|
|---|---:|---:|---|---:|---:|---|---|---:|---:|---|---:|---:|---:|---:|---|
|한국석유(004090)|12:01:09|12:19:57|rising|2.78%|2.78%|`scalping_scanner_promotion_latency_trace`/latency_state_danger|-|17|3|diagnostic_quote_age_stale|57707.0|-|70/USE_DEFENSIVE|0|12:01:09 scalping_scanner_promotion_latency_trace(+2.78%) -> 12:01:09 scalping_scanner_fast_precheck(+2.78%) -> 12:01:09 scalping_scanner_runtime_queue_lag(+2.78%) -> 12:01:09 scalping_scanner_promotion_latency_trace(+2.78%) -> ... -> 12:19:30 scalping_scanner_heavy_eval_lag(+2.78%) -> 12:19:55 orderbook_stability_observed(+2.78%) -> 12:19:57 entry_ai_price_canary_applied:Defensive price is below bid with latency caution and neutral micro state(+2.78%)|
|마키나락스(477850)|12:16:06|12:19:30|rising|1.51%|1.51%|`scalping_scanner_promotion_latency_trace`/ws_snapshot_missing_or_zero_recovered|-|2|1|ws_snapshot_missing_or_zero|7510.0|-|70/|0|12:16:06 scalping_scanner_candidate_promoted(+0.00%) -> 12:16:06 scalping_scanner_runtime_target_attach(+0.00%) -> 12:18:26 scalping_scanner_promotion_latency_trace(+1.51%) -> 12:18:26 scalping_scanner_fast_precheck(+1.51%) -> ... -> 12:19:05 scalping_scanner_heavy_eval_lag(+1.51%) -> 12:19:30 orderbook_stability_observed(+1.51%) -> 12:19:30 latency_block:latency_state_danger(+1.51%)|
|흥구석유(024060)|12:00:08|12:18:52|rising|1.35%|1.35%|`scalping_scanner_promotion_latency_trace`/insufficient_history|-|13|20|diagnostic_quote_age_stale|26212.0|12:17:02|62/WAIT|0|12:00:08 orderbook_stability_observed(+1.35%) -> 12:00:10 entry_ai_price_canary_applied:Defensive price is resolved with latency caution and spread ratio(+1.35%) -> 12:01:09 scalping_scanner_promotion_latency_trace(+1.35%) -> 12:01:09 scalping_scanner_fast_precheck(+1.35%) -> ... -> 12:18:13 scalping_scanner_watching_runtime_skip:entry_cooldown_active(+1.35%) -> 12:18:50 rising_missed_scout_upgrade_eval(+1.35%) -> 12:18:52 scalping_scanner_watching_runtime_skip:entry_cooldown_active(+1.35%)|
|중앙에너비스(000440)|12:00:28|12:18:46|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|14|0|diagnostic_quote_age_stale|122714.0|-||0|12:00:28 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:28 scalping_scanner_fast_precheck(+0.00%) -> 12:00:28 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:00:28 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 12:18:46 scalping_scanner_fast_precheck(+0.00%) -> 12:18:46 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%) -> 12:18:46 scalping_scanner_watching_runtime_skip:scanner_full_eval_loop_budget_deferred(+0.00%)|
|뉴로메카(348340)|12:00:28|12:18:46|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|18|0|diagnostic_quote_age_stale|86558.0|-||0|12:00:28 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:28 scalping_scanner_fast_precheck(+0.00%) -> 12:00:28 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:00:28 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 12:18:46 scalping_scanner_fast_precheck(+0.00%) -> 12:18:46 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%) -> 12:18:46 scalping_scanner_watching_runtime_skip:scanner_full_eval_loop_budget_deferred(+0.00%)|
|에이디테크놀로지(200710)|12:00:28|12:18:46|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|14|0|diagnostic_quote_age_stale|122908.0|-||0|12:00:28 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:28 scalping_scanner_fast_precheck(+0.00%) -> 12:00:28 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:00:28 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 12:18:46 scalping_scanner_fast_precheck(+0.00%) -> 12:18:46 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%) -> 12:18:46 scalping_scanner_watching_runtime_skip:scanner_full_eval_loop_budget_deferred(+0.00%)|
|레몬헬스케어(365660)|12:00:28|12:17:45|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|13|0|diagnostic_quote_age_stale|122826.0|-||0|12:00:28 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:28 scalping_scanner_fast_precheck(+0.00%) -> 12:00:28 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:00:28 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 12:17:45 scalping_scanner_fast_precheck(+0.00%) -> 12:17:45 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%) -> 12:17:45 scalping_scanner_watching_runtime_skip:scanner_full_eval_loop_budget_deferred(+0.00%)|
|심텍(222800)|12:00:28|12:17:45|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|13|0|diagnostic_quote_age_stale|116105.0|-||0|12:00:28 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:28 scalping_scanner_fast_precheck(+0.00%) -> 12:00:28 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:00:28 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 12:17:45 scalping_scanner_fast_precheck(+0.00%) -> 12:17:45 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%) -> 12:17:45 scalping_scanner_watching_runtime_skip:scanner_full_eval_loop_budget_deferred(+0.00%)|
|가온칩스(399720)|12:00:28|12:19:05|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|15|0|diagnostic_quote_age_stale|122417.0|-||0|12:00:28 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:28 scalping_scanner_fast_precheck(+0.00%) -> 12:00:28 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:00:28 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 12:19:05 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:19:05 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:19:05 scalping_scanner_fast_precheck(+0.00%)|
|온코닉테라퓨틱스(476060)|12:00:28|12:14:58|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|14|0|diagnostic_quote_age_stale|122619.0|-||0|12:00:28 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:28 scalping_scanner_fast_precheck(+0.00%) -> 12:00:28 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:00:28 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 12:14:31 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:14:31 scalping_scanner_heavy_eval_lag(+0.00%) -> 12:14:58 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%)|
|삼성전기(009150)|12:00:28|12:13:39|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|11|0|diagnostic_quote_age_stale|122462.0|-||0|12:00:28 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:28 scalping_scanner_fast_precheck(+0.00%) -> 12:00:28 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:00:28 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 12:13:39 scalping_scanner_fast_precheck(+0.00%) -> 12:13:39 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%) -> 12:13:39 scalping_scanner_watching_runtime_skip:scanner_full_eval_loop_budget_deferred(+0.00%)|
|한미반도체(042700)|12:00:28|12:13:39|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|11|0|diagnostic_quote_age_stale|122978.0|-||0|12:00:28 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:28 scalping_scanner_fast_precheck(+0.00%) -> 12:00:28 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:00:28 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 12:13:39 scalping_scanner_fast_precheck(+0.00%) -> 12:13:39 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%) -> 12:13:39 scalping_scanner_watching_runtime_skip:scanner_full_eval_loop_budget_deferred(+0.00%)|
|두산퓨얼셀(336260)|12:00:28|12:05:56|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|4|0|diagnostic_quote_age_stale|122612.0|-||0|12:00:28 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:28 scalping_scanner_fast_precheck(+0.00%) -> 12:00:28 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:00:28 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%) -> ... -> 12:05:56 scalping_scanner_fast_precheck(+0.00%) -> 12:05:56 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%) -> 12:05:56 scalping_scanner_watching_runtime_skip:scanner_full_eval_loop_budget_deferred(+0.00%)|
|KB발해인프라(415640)|12:00:28|12:11:20|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|-|8|0|diagnostic_quote_age_stale|124999.0|-||0|12:00:28 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%) -> 12:01:09 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:01:09 scalping_scanner_fast_precheck(+0.00%) -> 12:01:09 scalping_scanner_runtime_queue_lag(+0.00%) -> ... -> 12:11:20 scalping_scanner_fast_precheck(+0.00%) -> 12:11:20 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%) -> 12:11:20 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%)|
|SK스퀘어(402340)|12:02:59|12:19:05|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_full_eval_loop_budget_deferred|-|12|0|diagnostic_quote_age_stale|81502.0|-||0|12:02:59 scalping_scanner_candidate_promoted(+0.00%) -> 12:02:59 scalping_scanner_runtime_target_attach(+0.00%) -> 12:04:00 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:04:00 scalping_scanner_fast_precheck(+0.00%) -> ... -> 12:19:05 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:19:05 scalping_scanner_fast_precheck(+0.00%) -> 12:19:05 scalping_scanner_runtime_queue_lag(+0.00%)|
|SK하이닉스(000660)|12:16:06|12:18:46|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_stability_pending|-|2|0|diagnostic_quote_age_stale|33329.0|-||0|12:16:06 scalping_scanner_candidate_promoted(+0.00%) -> 12:16:06 scalping_scanner_runtime_target_attach(+0.00%) -> 12:17:13 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:17:13 scalping_scanner_fast_precheck(+0.00%) -> ... -> 12:18:26 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:18:26 scalping_scanner_heavy_eval_lag(+0.00%) -> 12:18:46 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%)|
|씨이랩(189330)|12:16:06|12:18:46|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_stability_pending|-|2|0|diagnostic_quote_age_stale|33353.0|-||0|12:16:06 scalping_scanner_candidate_promoted(+0.00%) -> 12:16:06 scalping_scanner_runtime_target_attach(+0.00%) -> 12:17:13 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:17:13 scalping_scanner_fast_precheck(+0.00%) -> ... -> 12:18:34 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:18:34 scalping_scanner_heavy_eval_lag(+0.00%) -> 12:18:46 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%)|
|디앤디파마텍(347850)|12:16:06|12:18:46|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_stability_pending|-|2|0|diagnostic_quote_age_stale|33348.0|-||0|12:16:06 scalping_scanner_candidate_promoted(+0.00%) -> 12:16:06 scalping_scanner_runtime_target_attach(+0.00%) -> 12:17:13 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:17:13 scalping_scanner_fast_precheck(+0.00%) -> ... -> 12:18:37 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:18:37 scalping_scanner_heavy_eval_lag(+0.00%) -> 12:18:46 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%)|
|네이처셀(007390)|12:16:06|12:19:05|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_stability_pending|-|4|0|diagnostic_quote_age_stale|42653.0|-||0|12:16:06 scalping_scanner_candidate_promoted(+0.00%) -> 12:16:06 scalping_scanner_runtime_target_attach(+0.00%) -> 12:17:13 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:17:13 scalping_scanner_fast_precheck(+0.00%) -> ... -> 12:19:05 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:19:05 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:19:05 scalping_scanner_fast_precheck(+0.00%)|
|테크윙(089030)|12:17:52|12:19:05|flat_or_falling|0.00%|0.00%|`scalping_scanner_candidate_promoted`/-|-|1|0|diagnostic_quote_age_stale|16195.0|-||0|12:17:52 scalping_scanner_candidate_promoted(+0.00%) -> 12:17:52 scalping_scanner_runtime_target_attach(+0.00%) -> 12:19:05 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:19:05 scalping_scanner_fast_precheck(+0.00%) -> 12:19:05 scalping_scanner_runtime_queue_lag(+0.00%)|
|금호건설(002990)|12:19:39|12:19:39|flat_or_falling|0.00%|0.00%|`scalping_scanner_candidate_promoted`/-|-|0|0|-||-||0|12:19:39 scalping_scanner_candidate_promoted(+0.00%) -> 12:19:39 scalping_scanner_runtime_target_attach(+0.00%)|
|삼현(437730)|12:19:39|12:19:39|flat_or_falling|0.00%|0.00%|`scalping_scanner_candidate_promoted`/-|-|0|0|-||-||0|12:19:39 scalping_scanner_candidate_promoted(+0.00%) -> 12:19:39 scalping_scanner_runtime_target_attach(+0.00%)|
|에스피지(058610)|12:19:39|12:19:39|flat_or_falling|0.00%|0.00%|`scalping_scanner_candidate_promoted`/-|-|0|0|-||-||0|12:19:39 scalping_scanner_candidate_promoted(+0.00%) -> 12:19:39 scalping_scanner_runtime_target_attach(+0.00%)|
|삼천당제약(000250)|12:19:39|12:19:39|flat_or_falling|0.00%|0.00%|`scalping_scanner_candidate_promoted`/-|-|0|0|-||-||0|12:19:39 scalping_scanner_candidate_promoted(+0.00%) -> 12:19:39 scalping_scanner_runtime_target_attach(+0.00%)|
|한국카본(017960)|12:02:39|12:18:46|flat_or_falling|-0.22%|-0.22%|`scalping_scanner_promotion_latency_trace`/scanner_full_eval_loop_budget_deferred|-|13|0|diagnostic_quote_age_stale|122648.0|-||0|12:02:39 scalping_scanner_promotion_latency_trace(-0.22%) -> 12:02:39 scalping_scanner_fast_precheck(-0.22%) -> 12:02:39 scalping_scanner_runtime_queue_lag(-0.22%) -> 12:02:39 scalping_scanner_watching_runtime_skip:scanner_full_eval_loop_budget_deferred(-0.22%) -> ... -> 12:18:46 scalping_scanner_fast_precheck(-0.22%) -> 12:18:46 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(-0.22%) -> 12:18:46 scalping_scanner_watching_runtime_skip:scanner_full_eval_loop_budget_deferred(-0.22%)|
|현대건설(000720)|12:00:28|12:05:56|flat_or_falling|-1.00%|-1.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|3|0|diagnostic_quote_age_stale|122849.0|-||0|12:00:28 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(-1.00%) -> 12:02:39 scalping_scanner_promotion_latency_trace(-1.00%) -> 12:02:39 scalping_scanner_fast_precheck(-1.00%) -> 12:02:39 scalping_scanner_runtime_queue_lag(-1.00%) -> ... -> 12:05:56 scalping_scanner_fast_precheck(-1.00%) -> 12:05:56 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(-1.00%) -> 12:05:56 scalping_scanner_watching_runtime_skip:scanner_full_eval_loop_budget_deferred(-1.00%)|
|삼성전자(005930)|12:00:29|12:18:47|unknown|||`scalping_scanner_runtime_target_attach`/-|-|0|0|-||-||0|12:00:29 scalping_scanner_runtime_target_attach|
|LS ELECTRIC(010120)|12:00:29|12:18:47|unknown|||`scalping_scanner_runtime_target_attach`/-|-|0|0|-||-||0|12:00:29 scalping_scanner_runtime_target_attach|
|삼표시멘트(038500)|12:00:29|12:18:47|unknown|||`scalping_scanner_runtime_target_attach`/-|-|0|0|-||-||0|12:00:29 scalping_scanner_runtime_target_attach|

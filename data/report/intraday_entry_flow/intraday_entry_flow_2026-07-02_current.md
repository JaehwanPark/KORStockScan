# 2026-07-02 12:00 이후 감시대상 BUY 전 흐름

- generated_at: 2026-07-02T12:30:00+09:00
- source_events: /home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-02.jsonl
- source_diagnostic: /home/ubuntu/KORStockScan/data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-07-02.json
- event_window_since: 2026-07-02T12:00:00+09:00
- event_window_until: None
- symbol_count: 19
- rising_symbol_count_by_max_delta: 5
- rising_missed_buy_count_in_latest_diagnostic: 5
- rising_missed_symbol_count_in_report: 5
- rising_missed_residual_excluding_forced_scout_symbol_count: 0
- rising_missed_forced_scout_event_count: 48
- rising_missed_forced_scout_symbol_count: 5
- rising_missed_forced_scout_residual_symbol_count: 5
- real_submit_symbol_count_in_latest_diagnostic: 0
- buy_signal_or_pre_submit_pass_seen_symbols: 9
- stale_eval_symbol_count: 17
- rising_stale_eval_symbol_count: 5
- rising_fresh_only_symbol_count: 0
- stale_refresh_recovered_symbol_count: 14

## forced scout observation

- event_count: 48
- symbol_count: 5
- symbols: 001260, 007610, 267260, 378340, 486990
- rising_missed_residual_symbols: 001260, 007610, 267260, 378340, 486990
- rising_missed_residual_excluding_forced_scout_symbols: -
- decision_authority: source_quality_only
- runtime_effect: False

## blocker rollup

- 12: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 4: `scalping_scanner_watching_runtime_skip` / `entry_cooldown_active`
- 1: `same_symbol_loss_reentry_cooldown` / `-`
- 1: `scalping_scanner_runtime_target_attach` / `-`
- 1: `condition_unmatch_guard` / `-`

## blocker taxonomy

- 139: `runtime_backpressure`
- 76: `strategy_reject`
- 14: `intended_guard`
- 12: `pre_submit_quality_guard`

## suppressed non-major blocker counts

- 139: `runtime_backpressure` / `scalping_scanner_watching_runtime_skip` / `scanner_full_eval_loop_budget_deferred`
- 12: `pre_submit_quality_guard` / `latency_block` / `latency_state_danger`
- 1: `intended_guard` / `same_symbol_loss_reentry_cooldown` / ``

## rising-symbol blocker rollup

- 4: `scalping_scanner_watching_runtime_skip` / `entry_cooldown_active`
- 1: `same_symbol_loss_reentry_cooldown` / `-`

## rising fresh-only blocker rollup


## rising stale-mixed blocker rollup

- 4: `scalping_scanner_watching_runtime_skip` / `entry_cooldown_active`
- 1: `same_symbol_loss_reentry_cooldown` / `-`

## stale-eval rollup

- 17: `scalping_scanner_fast_precheck`

## stale-eval category rollup

- 17: `diagnostic_quote_age_stale`

## latency danger root cause

|종목|건수|top cause|spread ratio med/max|ws age med/max|spread ticks med/max|micro|bucket|
|---|---:|---|---:|---:|---:|---|---|
|선도전기(007610)|11|quote_stale|0.008065/0.013029|908.0/19488.0|5.0/8.0|neutral|spread=wide\|price=low\|depth=normal\|sample=rich|
|필에너지(378340)|5|quote_stale|0.007418/0.008118|3671.0/11939.0|10.0/11.0|insufficient|spread=wide\|price=mid\|depth=normal\|sample=insufficient|
|상지건설(042940)|1|spread_microstructure_wide|0.00715/0.00715|89.0/89.0|7.0/7.0|bearish|spread=wide\|price=low\|depth=normal\|sample=rich|

## top rows by max delta

|종목|첫감시|마지막|상승여부|maxΔ|latestΔ|BUY전 주 blocker|class|stale평가|refresh회복|stale유형|max quote age|BUY전 통과신호|AI|실제submit|흐름|
|---|---:|---:|---|---:|---:|---|---|---:|---:|---|---:|---:|---:|---:|---|
|필에너지(378340)|12:00:02|12:29:56|rising|6.45%|6.45%|`scalping_scanner_watching_runtime_skip`/entry_cooldown_active|intended_guard|78|9|diagnostic_quote_age_stale|161545.0|12:00:23|70/not_evaluated|0|12:00:02 scalping_scanner_watching_runtime_skip:scanner_heavy_eval_stale_snapshot_recheck(+6.45%) -> 12:00:15 scalping_scanner_promotion_latency_trace(+6.45%) -> 12:00:15 scalping_scanner_fast_precheck(+6.45%) -> 12:00:15 scalping_scanner_runtime_queue_lag(+6.45%) -> ... -> 12:29:43 entry_reprice_after_submit_blocked(+6.45%) -> 12:29:56 entry_reprice_after_submit_evaluated(+6.45%) -> 12:29:56 entry_reprice_after_submit_blocked(+6.45%)|
|남광토건(001260)|12:02:38|12:30:01|rising|5.11%|5.11%|`scalping_scanner_watching_runtime_skip`/entry_cooldown_active|intended_guard|28|0|diagnostic_quote_age_stale|83403.0|-||0|12:02:38 scalping_scanner_candidate_promoted(+0.00%) -> 12:02:38 scalping_scanner_runtime_target_attach(+0.00%) -> 12:19:39 scalping_scanner_promotion_latency_trace(+5.11%) -> 12:19:39 scalping_scanner_fast_precheck(+5.11%) -> ... -> 12:30:01 scalping_scanner_promotion_latency_trace(+5.11%) -> 12:30:01 scalping_scanner_fast_precheck(+5.11%) -> 12:30:01 scalping_scanner_runtime_queue_lag(+5.11%)|
|노타(486990)|12:11:42|12:30:01|rising|3.48%|3.48%|`same_symbol_loss_reentry_cooldown`/-|non_actionable_guard_or_backpressure|31|0|diagnostic_quote_age_stale|65021.0|-||0|12:11:42 same_symbol_loss_reentry_cooldown(+0.00%) -> 12:11:58 scalping_scanner_promotion_latency_trace(+3.48%) -> 12:11:58 scalping_scanner_fast_precheck(+3.48%) -> 12:11:58 scalping_scanner_runtime_queue_lag(+3.48%) -> ... -> 12:30:01 scalping_scanner_promotion_latency_trace(+3.48%) -> 12:30:01 scalping_scanner_fast_precheck(+3.48%) -> 12:30:01 scalping_scanner_runtime_queue_lag(+3.48%)|
|선도전기(007610)|12:00:02|12:30:01|rising|2.37%|2.37%|`scalping_scanner_watching_runtime_skip`/entry_cooldown_active|intended_guard|66|17|diagnostic_quote_age_stale|125410.0|12:01:38|70/not_evaluated|0|12:00:02 scalping_scanner_promotion_latency_trace(+2.37%) -> 12:00:02 scalping_scanner_fast_precheck(+2.37%) -> 12:00:02 scalping_scanner_runtime_queue_lag(+2.37%) -> 12:00:15 scalping_scanner_promotion_latency_trace(+2.37%) -> ... -> 12:30:01 scalping_scanner_runtime_queue_lag(+2.37%) -> 12:30:01 scalping_scanner_promotion_latency_trace(+2.37%) -> 12:30:01 scalping_scanner_heavy_eval_lag(+2.37%)|
|HD현대일렉트릭(267260)|12:00:02|12:30:01|rising|1.46%|1.46%|`scalping_scanner_watching_runtime_skip`/entry_cooldown_active|intended_guard|79|0|diagnostic_quote_age_stale|92075.0|-||0|12:00:02 scalping_scanner_promotion_latency_trace(+1.46%) -> 12:00:02 scalping_scanner_fast_precheck(+1.46%) -> 12:00:02 scalping_scanner_runtime_queue_lag(+1.46%) -> 12:00:15 scalping_scanner_promotion_latency_trace(+1.46%) -> ... -> 12:30:01 scalping_scanner_promotion_latency_trace(+1.46%) -> 12:30:01 scalping_scanner_fast_precheck(+1.46%) -> 12:30:01 scalping_scanner_runtime_queue_lag(+1.46%)|
|JYP Ent.(035900)|12:00:02|12:19:39|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|62|8|diagnostic_quote_age_stale|60458.0|12:08:19|62/WAIT|0|12:00:02 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:02 scalping_scanner_fast_precheck(+0.00%) -> 12:00:02 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:00:02 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 12:19:36 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:19:36 scalping_scanner_fast_precheck(+0.00%) -> 12:19:39 scalping_scanner_runtime_queue_lag(+0.00%)|
|KBI메탈(024840)|12:00:02|12:30:01|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|102|4|diagnostic_quote_age_stale|57895.0|-|50/|0|12:00:02 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:02 scalping_scanner_fast_precheck(+0.00%) -> 12:00:02 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:00:02 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 12:30:01 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:30:01 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:30:01 scalping_scanner_fast_precheck(+0.00%)|
|엔켐(348370)|12:00:02|12:30:01|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|93|13|diagnostic_quote_age_stale|75912.0|-|50/|0|12:00:02 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:02 scalping_scanner_fast_precheck(+0.00%) -> 12:00:02 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:00:02 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%) -> ... -> 12:30:01 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:30:01 scalping_scanner_fast_precheck(+0.00%) -> 12:30:01 scalping_scanner_runtime_queue_lag(+0.00%)|
|케이뱅크(279570)|12:00:02|12:30:01|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|95|12|diagnostic_quote_age_stale|58862.0|-|50/|0|12:00:02 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:02 scalping_scanner_fast_precheck(+0.00%) -> 12:00:02 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:00:02 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 12:30:01 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:30:01 scalping_scanner_fast_precheck(+0.00%) -> 12:30:01 scalping_scanner_runtime_queue_lag(+0.00%)|
|미스토홀딩스(081660)|12:00:02|12:30:01|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|101|17|diagnostic_quote_age_stale|58096.0|12:11:03|62/WAIT|0|12:00:02 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:02 scalping_scanner_fast_precheck(+0.00%) -> 12:00:02 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:00:02 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 12:30:01 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:30:01 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:30:01 scalping_scanner_fast_precheck(+0.00%)|
|상지건설(042940)|12:00:02|12:30:01|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|106|17|diagnostic_quote_age_stale|75220.0|12:12:43|78/BUY|0|12:00:02 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:02 scalping_scanner_fast_precheck(+0.00%) -> 12:00:02 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:00:02 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 12:30:01 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:30:01 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:30:01 scalping_scanner_fast_precheck(+0.00%)|
|한화에어로스페이스(012450)|12:00:02|12:30:01|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|105|15|diagnostic_quote_age_stale|55710.0|12:11:10|63/WAIT|0|12:00:02 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:02 scalping_scanner_fast_precheck(+0.00%) -> 12:00:02 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:00:02 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 12:30:01 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:30:01 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:30:01 scalping_scanner_fast_precheck(+0.00%)|
|한국콜마(161890)|12:00:02|12:30:01|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|112|12|diagnostic_quote_age_stale|61080.0|12:11:19|62/WAIT|0|12:00:02 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:02 scalping_scanner_fast_precheck(+0.00%) -> 12:00:02 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:00:02 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 12:30:01 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:30:01 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:30:01 scalping_scanner_fast_precheck(+0.00%)|
|한국알콜(017890)|12:00:02|12:30:01|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|91|4|diagnostic_quote_age_stale|58377.0|-|62/|0|12:00:02 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%) -> 12:00:39 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:39 scalping_scanner_fast_precheck(+0.00%) -> 12:00:39 scalping_scanner_runtime_queue_lag(+0.00%) -> ... -> 12:30:01 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:30:01 scalping_scanner_fast_precheck(+0.00%) -> 12:30:01 scalping_scanner_runtime_queue_lag(+0.00%)|
|아모레퍼시픽(090430)|12:00:02|12:30:01|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|101|11|diagnostic_quote_age_stale|57894.0|12:13:07|58/WAIT|0|12:00:02 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%) -> 12:00:15 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:15 scalping_scanner_fast_precheck(+0.00%) -> 12:00:15 scalping_scanner_runtime_queue_lag(+0.00%) -> ... -> 12:30:01 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:30:01 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:30:01 scalping_scanner_fast_precheck(+0.00%)|
|DN오토모티브(007340)|12:00:02|12:30:01|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|101|28|diagnostic_quote_age_stale|79585.0|12:06:56|58/WAIT|0|12:00:02 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%) -> 12:00:15 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:15 scalping_scanner_fast_precheck(+0.00%) -> 12:00:15 scalping_scanner_runtime_queue_lag(+0.00%) -> ... -> 12:30:01 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:30:01 scalping_scanner_fast_precheck(+0.00%) -> 12:30:01 scalping_scanner_runtime_queue_lag(+0.00%)|
|위메이드(112040)|12:00:02|12:30:01|flat_or_falling|-0.58%|-0.58%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|strategy_reject|100|8|diagnostic_quote_age_stale|57613.0|-|50/|0|12:00:02 scalping_scanner_promotion_latency_trace(-0.58%) -> 12:00:02 scalping_scanner_fast_precheck(-0.58%) -> 12:00:02 scalping_scanner_runtime_queue_lag(-0.58%) -> 12:00:02 scalping_scanner_promotion_latency_trace(-0.58%) -> ... -> 12:30:01 scalping_scanner_runtime_queue_lag(-0.58%) -> 12:30:01 scalping_scanner_promotion_latency_trace(-0.58%) -> 12:30:01 scalping_scanner_fast_precheck(-0.58%)|
|삼표시멘트(038500)|12:00:03|12:29:51|unknown|||`scalping_scanner_runtime_target_attach`/-|-|0|0|-||-||0|12:00:03 scalping_scanner_runtime_target_attach|
|-(161390)|12:27:04|12:27:04|unknown|||`condition_unmatch_guard`/-|-|0|0|-||-||0|12:27:04 condition_unmatch_guard|

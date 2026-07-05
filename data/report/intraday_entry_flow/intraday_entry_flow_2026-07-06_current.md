# 2026-07-06 08:00 이후 감시대상 BUY 전 흐름

- generated_at: 2026-07-06T08:50:24
- source_events: /home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-06.jsonl
- source_diagnostic: /home/ubuntu/KORStockScan/data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-07-06.json
- event_window_since: 08:00:00
- event_window_until: None
- symbol_count: 25
- rising_symbol_count_by_max_delta: 12
- rising_missed_buy_count_in_latest_diagnostic: 0
- rising_missed_symbol_count_in_report: 0
- rising_missed_residual_excluding_forced_scout_symbol_count: 0
- rising_missed_forced_scout_event_count: 0
- rising_missed_forced_scout_symbol_count: 0
- rising_missed_forced_scout_residual_symbol_count: 0
- real_submit_symbol_count_in_latest_diagnostic: None
- buy_signal_or_pre_submit_pass_seen_symbols: 11
- stale_eval_symbol_count: 20
- rising_stale_eval_symbol_count: 11
- rising_fresh_only_symbol_count: 1
- stale_refresh_recovered_symbol_count: 13

## forced scout observation

- event_count: 0
- symbol_count: 0
- symbols: -
- rising_missed_residual_symbols: -
- rising_missed_residual_excluding_forced_scout_symbols: -
- decision_authority: source_quality_only
- runtime_effect: False

## blocker rollup

- 10: `scalping_scanner_promotion_latency_trace` / `scanner_fast_precheck_subscription_recheck_snapshot_applied`
- 6: `scalping_scanner_promotion_latency_trace` / `latency_state_danger`
- 5: `scalping_scanner_runtime_target_attach` / `-`
- 1: `scalping_scanner_promotion_latency_trace` / `entry_cooldown_active`
- 1: `scalping_scanner_promotion_latency_trace` / `outside_scalping_buy_window`
- 1: `rising_missed_scout_upgrade_eval` / `entry_cooldown_active`
- 1: `scalping_scanner_promotion_latency_trace` / `below_strength_base`

## rising-symbol blocker rollup

- 5: `scalping_scanner_promotion_latency_trace` / `latency_state_danger`
- 3: `scalping_scanner_promotion_latency_trace` / `scanner_fast_precheck_subscription_recheck_snapshot_applied`
- 1: `scalping_scanner_promotion_latency_trace` / `entry_cooldown_active`
- 1: `scalping_scanner_promotion_latency_trace` / `outside_scalping_buy_window`
- 1: `rising_missed_scout_upgrade_eval` / `entry_cooldown_active`
- 1: `scalping_scanner_runtime_target_attach` / `-`

## rising fresh-only blocker rollup

- 1: `scalping_scanner_runtime_target_attach` / `-`

## rising stale-mixed blocker rollup

- 5: `scalping_scanner_promotion_latency_trace` / `latency_state_danger`
- 3: `scalping_scanner_promotion_latency_trace` / `scanner_fast_precheck_subscription_recheck_snapshot_applied`
- 1: `scalping_scanner_promotion_latency_trace` / `entry_cooldown_active`
- 1: `scalping_scanner_promotion_latency_trace` / `outside_scalping_buy_window`
- 1: `rising_missed_scout_upgrade_eval` / `entry_cooldown_active`

## stale-eval rollup

- 20: `scalping_scanner_fast_precheck`

## stale-eval category rollup

- 20: `diagnostic_quote_age_stale`

## latency danger root cause

|종목|건수|top cause|spread ratio med/max|ws age med/max|spread ticks med/max|micro|bucket|
|---|---:|---|---:|---:|---:|---|---|
|가온전선(000500)|95|spread_microstructure_wide|0.008489/0.011804|114.0/549.0|5.0/7.0|neutral|spread=wide\|price=high\|depth=normal\|sample=rich|
|한미반도체(042700)|62|spread_too_wide|0.010438/0.012526|110.5/304.0|5.0/6.0|neutral|spread=wide\|price=high\|depth=thick\|sample=rich|
|에코프로(086520)|61|spread_microstructure_wide|0.005637/0.00678|97.0/3661.0|5.0/6.0|neutral|spread=wide\|price=high\|depth=thick\|sample=rich|
|LG이노텍(011070)|48|spread_microstructure_wide|0.005476/0.008705|120.5/554.0|5.0/8.0|neutral|spread=wide\|price=high\|depth=normal\|sample=rich|
|삼성전자(005930)|34|spread_microstructure_wide|0.007776/0.007825|56.5/116.0|5.0/5.0|neutral|spread=wide\|price=high\|depth=thick\|sample=rich|
|두산에너빌리티(034020)|28|spread_microstructure_wide|0.00565/0.005663|78.0/338.0|5.0/5.0|neutral|spread=wide\|price=high\|depth=thick\|sample=rich|
|가온칩스(399720)|4|spread_microstructure_wide|0.00565/0.005656|162.0/332.0|5.0/5.0|neutral|spread=wide\|price=mid\|depth=normal\|sample=rich|
|에이디테크놀로지(200710)|2|spread_too_wide|0.011165/0.011218|181.0/292.0|7.0/7.0|neutral|spread=wide\|price=mid\|depth=normal\|sample=rich|
|한화오션(042660)|1|spread_microstructure_wide|0.006195/0.006195|23.0/23.0|7.0/7.0|neutral|spread=wide\|price=high\|depth=normal\|sample=rich|

## top rows by max delta

|종목|첫감시|마지막|상승여부|maxΔ|latestΔ|BUY전 주 blocker|class|stale평가|refresh회복|stale유형|max quote age|BUY전 통과신호|AI|실제submit|흐름|
|---|---:|---:|---|---:|---:|---|---|---:|---:|---|---:|---:|---:|---:|---|
|에이디테크놀로지(200710)|08:04:44|08:50:21|rising|9.98%|6.26%|`scalping_scanner_promotion_latency_trace`/entry_cooldown_active|-|129|3|diagnostic_quote_age_stale|31561.0|08:21:25|58/USE_DEFENSIVE|2|08:04:44 scalping_scanner_candidate_promoted(+4.06%) -> 08:04:44 scalping_scanner_runtime_target_attach(+4.06%) -> 08:05:15 scalping_scanner_promotion_latency_trace(+4.06%) -> 08:05:15 scalping_scanner_fast_precheck(+4.06%) -> ... -> 08:50:12 scalping_scanner_runtime_queue_lag(+6.26%) -> 08:50:21 scalping_scanner_promotion_latency_trace(+6.26%) -> 08:50:21 scalping_scanner_fast_precheck(+6.26%)|
|가온칩스(399720)|08:04:44|08:50:21|rising|4.61%|4.61%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|138|5|diagnostic_quote_age_stale|38047.0|08:23:49|0/USE_DEFENSIVE|2|08:04:44 scalping_scanner_candidate_promoted(+0.00%) -> 08:04:44 scalping_scanner_runtime_target_attach(+0.00%) -> 08:05:15 scalping_scanner_promotion_latency_trace(+0.00%) -> 08:05:15 scalping_scanner_fast_precheck(+0.00%) -> ... -> 08:50:12 scalping_scanner_runtime_queue_lag(+4.61%) -> 08:50:21 scalping_scanner_promotion_latency_trace(+4.61%) -> 08:50:21 scalping_scanner_fast_precheck(+4.61%)|
|SK하이닉스(000660)|08:01:42|08:50:21|rising|1.92%|1.92%|`scalping_scanner_promotion_latency_trace`/outside_scalping_buy_window|-|104|0|diagnostic_quote_age_stale|44417.0|-||0|08:01:42 scalping_scanner_candidate_promoted(+1.06%) -> 08:01:42 scalping_scanner_runtime_target_attach(+1.06%) -> 08:01:43 scalping_scanner_promotion_latency_trace(+1.06%) -> 08:01:43 scalping_scanner_fast_precheck(+1.06%) -> ... -> 08:50:16 scalping_scanner_fast_precheck(+1.92%) -> 08:50:16 scalping_scanner_watching_runtime_skip:scanner_heavy_eval_stale_snapshot_recheck(+1.92%) -> 08:50:21 scalping_scanner_runtime_queue_lag(+1.92%)|
|에코프로(086520)|08:01:42|08:50:21|rising|1.36%|1.36%|`scalping_scanner_promotion_latency_trace`/latency_state_danger|-|89|60|diagnostic_quote_age_stale|36503.0|-|0/|0|08:01:42 scalping_scanner_candidate_promoted(+1.02%) -> 08:01:42 scalping_scanner_runtime_target_attach(+1.02%) -> 08:01:43 scalping_scanner_promotion_latency_trace(+1.02%) -> 08:01:43 scalping_scanner_fast_precheck(+1.02%) -> ... -> 08:50:16 scalping_scanner_promotion_latency_trace(+1.36%) -> 08:50:16 scalping_scanner_fast_precheck(+1.36%) -> 08:50:21 scalping_scanner_runtime_queue_lag(+1.36%)|
|삼성전자(005930)|08:01:42|08:50:21|rising|1.26%|1.26%|`scalping_scanner_promotion_latency_trace`/latency_state_danger|-|107|55|diagnostic_quote_age_stale|44403.0|08:30:35|0/not_evaluated|0|08:01:42 scalping_scanner_candidate_promoted(+0.63%) -> 08:01:42 scalping_scanner_runtime_target_attach(+0.63%) -> 08:01:43 scalping_scanner_watching_runtime_skip:before_strategy_start(+0.63%) -> 08:01:43 scalping_scanner_promotion_latency_trace(+0.63%) -> ... -> 08:50:16 scalping_scanner_fast_precheck(+1.26%) -> 08:50:16 scalping_scanner_watching_runtime_skip:scanner_heavy_eval_stale_snapshot_recheck(+1.26%) -> 08:50:21 scalping_scanner_runtime_queue_lag(+1.26%)|
|제룡전기(033100)|08:01:42|08:50:21|rising|0.94%|0.94%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|162|0|diagnostic_quote_age_stale|46632.0|-||0|08:01:42 scalping_scanner_candidate_promoted(+0.94%) -> 08:01:42 scalping_scanner_runtime_target_attach(+0.94%) -> 08:01:43 scalping_scanner_watching_runtime_skip:before_strategy_start(+0.94%) -> 08:01:43 scalping_scanner_promotion_latency_trace(+0.94%) -> ... -> 08:50:16 scalping_scanner_promotion_latency_trace(+0.94%) -> 08:50:16 scalping_scanner_fast_precheck(+0.94%) -> 08:50:21 scalping_scanner_runtime_queue_lag(+0.94%)|
|두산에너빌리티(034020)|08:01:42|08:50:21|rising|0.91%|0.91%|`scalping_scanner_promotion_latency_trace`/latency_state_danger|-|109|49|diagnostic_quote_age_stale|44522.0|08:30:41|0/not_evaluated|0|08:01:42 scalping_scanner_candidate_promoted(+0.91%) -> 08:01:42 scalping_scanner_runtime_target_attach(+0.91%) -> 08:01:43 scalping_scanner_watching_runtime_skip:before_strategy_start(+0.91%) -> 08:01:43 scalping_scanner_promotion_latency_trace(+0.91%) -> ... -> 08:50:16 scalping_scanner_fast_precheck(+0.91%) -> 08:50:16 scalping_scanner_watching_runtime_skip:scanner_heavy_eval_stale_snapshot_recheck(+0.91%) -> 08:50:21 scalping_scanner_runtime_queue_lag(+0.91%)|
|한화오션(042660)|08:01:42|08:50:23|rising|0.90%|0.90%|`rising_missed_scout_upgrade_eval`/entry_cooldown_active|-|6|2|diagnostic_quote_age_stale|4393.0|08:03:33|57/BUY|2|08:01:42 scalping_scanner_candidate_promoted(+0.90%) -> 08:01:42 scalping_scanner_runtime_target_attach(+0.90%) -> 08:01:43 scalping_scanner_watching_runtime_skip:before_strategy_start(+0.90%) -> 08:01:43 scalping_scanner_promotion_latency_trace(+0.90%) -> ... -> 08:49:51 scalping_scanner_watching_runtime_skip:outside_scalping_buy_window(+0.90%) -> 08:49:57 rising_missed_scout_upgrade_eval(+0.90%) -> 08:50:23 scalping_scanner_watching_runtime_skip:outside_scalping_buy_window(+0.90%)|
|LS ELECTRIC(010120)|08:00:02|08:50:22|rising|0.64%|0.64%|`scalping_scanner_runtime_target_attach`/-|-|0|0|-||-||0|08:00:02 scalping_scanner_runtime_target_attach -> 08:01:42 scalping_scanner_candidate_promoted(+0.64%) -> 08:01:42 scalping_scanner_runtime_target_attach(+0.64%)|
|NAVER(035420)|08:01:42|08:50:21|rising|0.25%|0.25%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|158|0|diagnostic_quote_age_stale|46235.0|-||0|08:01:42 scalping_scanner_candidate_promoted(+0.25%) -> 08:01:42 scalping_scanner_runtime_target_attach(+0.25%) -> 08:01:43 scalping_scanner_watching_runtime_skip:ws_snapshot_missing_or_zero(+0.25%) -> 08:01:44 scalping_scanner_promotion_latency_trace(+0.25%) -> ... -> 08:50:12 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.25%) -> 08:50:21 scalping_scanner_promotion_latency_trace(+0.25%) -> 08:50:21 scalping_scanner_fast_precheck(+0.25%)|
|한미반도체(042700)|08:01:42|08:50:23|rising|0.21%|0.21%|`scalping_scanner_promotion_latency_trace`/latency_state_danger|-|37|63|diagnostic_quote_age_stale|13948.0|08:23:33|57/not_evaluated|2|08:01:42 scalping_scanner_candidate_promoted(+0.21%) -> 08:01:42 scalping_scanner_runtime_target_attach(+0.21%) -> 08:01:43 scalping_scanner_watching_runtime_skip:before_strategy_start(+0.21%) -> 08:01:43 scalping_scanner_promotion_latency_trace(+0.21%) -> ... -> 08:49:51 scalping_scanner_watching_runtime_skip:outside_scalping_buy_window(+0.21%) -> 08:49:57 rising_missed_scout_upgrade_eval(+0.21%) -> 08:50:23 scalping_scanner_watching_runtime_skip:outside_scalping_buy_window(+0.21%)|
|LG이노텍(011070)|08:01:42|08:50:21|rising|0.11%|0.11%|`scalping_scanner_promotion_latency_trace`/latency_state_danger|-|128|49|diagnostic_quote_age_stale|46205.0|08:17:53|0/SKIP|2|08:01:42 scalping_scanner_candidate_promoted(+0.11%) -> 08:01:42 scalping_scanner_runtime_target_attach(+0.11%) -> 08:01:43 scalping_scanner_promotion_latency_trace(+0.11%) -> 08:01:43 scalping_scanner_fast_precheck(+0.11%) -> ... -> 08:50:12 scalping_scanner_runtime_queue_lag(+0.11%) -> 08:50:21 scalping_scanner_promotion_latency_trace(+0.11%) -> 08:50:21 scalping_scanner_fast_precheck(+0.11%)|
|삼성SDI(006400)|08:01:42|08:50:21|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|159|0|diagnostic_quote_age_stale|46259.0|-||0|08:01:42 scalping_scanner_candidate_promoted(+0.00%) -> 08:01:42 scalping_scanner_runtime_target_attach(+0.00%) -> 08:01:43 scalping_scanner_watching_runtime_skip:ws_snapshot_missing_or_zero(+0.00%) -> 08:01:44 scalping_scanner_watching_runtime_skip:before_strategy_start(+0.00%) -> ... -> 08:50:12 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%) -> 08:50:21 scalping_scanner_promotion_latency_trace(+0.00%) -> 08:50:21 scalping_scanner_fast_precheck(+0.00%)|
|도우인시스(484120)|08:03:13|08:50:21|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|155|5|diagnostic_quote_age_stale|46145.0|08:19:59|62/WAIT|0|08:03:13 scalping_scanner_candidate_promoted(+0.00%) -> 08:03:13 scalping_scanner_runtime_target_attach(+0.00%) -> 08:03:45 scalping_scanner_promotion_latency_trace(+0.00%) -> 08:03:45 scalping_scanner_fast_precheck(+0.00%) -> ... -> 08:50:12 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%) -> 08:50:21 scalping_scanner_promotion_latency_trace(+0.00%) -> 08:50:21 scalping_scanner_fast_precheck(+0.00%)|
|삼성중공업(010140)|08:03:13|08:20:40|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|54|2|diagnostic_quote_age_stale|30005.0|-|50/|0|08:03:13 scalping_scanner_candidate_promoted(+0.00%) -> 08:03:13 scalping_scanner_runtime_target_attach(+0.00%) -> 08:03:45 scalping_scanner_promotion_latency_trace(+0.00%) -> 08:03:45 scalping_scanner_fast_precheck(+0.00%) -> ... -> 08:20:36 strength_momentum_observed:below_window_buy_value(+0.00%) -> 08:20:37 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 08:20:40 scalping_scanner_watch_eviction:scanner_hardgate_prefilter(+0.00%)|
|칩스앤미디어(094360)|08:09:16|08:18:59|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|30|0|diagnostic_quote_age_stale|26443.0|-|50/|0|08:09:16 scalping_scanner_candidate_promoted(+0.00%) -> 08:09:16 scalping_scanner_runtime_target_attach(+0.00%) -> 08:09:48 scalping_scanner_promotion_latency_trace(+0.00%) -> 08:09:48 scalping_scanner_fast_precheck(+0.00%) -> ... -> 08:18:57 strength_momentum_observed:below_window_buy_value(+0.00%) -> 08:18:58 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 08:18:59 scalping_scanner_watch_eviction:scanner_hardgate_prefilter(+0.00%)|
|이노테크(469610)|08:18:20|08:50:21|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|102|6|diagnostic_quote_age_stale|46142.0|08:19:28|58/WAIT|0|08:18:20 scalping_scanner_candidate_promoted(+0.00%) -> 08:18:20 scalping_scanner_runtime_target_attach(+0.00%) -> 08:18:48 scalping_scanner_promotion_latency_trace(+0.00%) -> 08:18:48 scalping_scanner_fast_precheck(+0.00%) -> ... -> 08:50:12 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%) -> 08:50:21 scalping_scanner_promotion_latency_trace(+0.00%) -> 08:50:21 scalping_scanner_fast_precheck(+0.00%)|
|위메이드(112040)|08:21:21|08:50:21|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|92|4|diagnostic_quote_age_stale|46180.0|-|50/|0|08:21:21 scalping_scanner_candidate_promoted(+0.00%) -> 08:21:21 scalping_scanner_runtime_target_attach(+0.00%) -> 08:21:34 scalping_scanner_promotion_latency_trace(+0.00%) -> 08:21:34 scalping_scanner_fast_precheck(+0.00%) -> ... -> 08:50:12 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%) -> 08:50:21 scalping_scanner_promotion_latency_trace(+0.00%) -> 08:50:21 scalping_scanner_fast_precheck(+0.00%)|
|미래에셋증권(006800)|08:22:52|08:50:21|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|89|0|diagnostic_quote_age_stale|38125.0|08:24:19|74/WAIT|0|08:22:52 scalping_scanner_candidate_promoted(+0.00%) -> 08:22:52 scalping_scanner_runtime_target_attach(+0.00%) -> 08:23:21 scalping_scanner_promotion_latency_trace(+0.00%) -> 08:23:21 scalping_scanner_fast_precheck(+0.00%) -> ... -> 08:50:12 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%) -> 08:50:21 scalping_scanner_promotion_latency_trace(+0.00%) -> 08:50:21 scalping_scanner_fast_precheck(+0.00%)|
|강원에너지(114190)|08:24:22|08:25:40|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/below_strength_base|-|2|0|diagnostic_quote_age_stale|14041.0|-|50/|0|08:24:22 scalping_scanner_candidate_promoted(+0.00%) -> 08:24:22 scalping_scanner_runtime_target_attach(+0.00%) -> 08:24:48 scalping_scanner_promotion_latency_trace(+0.00%) -> 08:24:48 scalping_scanner_fast_precheck(+0.00%) -> ... -> 08:25:33 blocked_strength_momentum:below_strength_base(+0.00%) -> 08:25:34 scalping_scanner_watch_eviction:scanner_hardgate_prefilter(+0.00%) -> 08:25:40 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%)|
|가온전선(000500)|08:01:42|08:50:21|flat_or_falling|-2.91%|-2.91%|`scalping_scanner_promotion_latency_trace`/latency_state_danger|-|80|116|diagnostic_quote_age_stale|19678.0|08:30:31|0/not_evaluated|0|08:01:42 scalping_scanner_candidate_promoted(-2.91%) -> 08:01:42 scalping_scanner_runtime_target_attach(-2.91%) -> 08:01:43 scalping_scanner_watching_runtime_skip:before_strategy_start(-2.91%) -> 08:01:43 scalping_scanner_promotion_latency_trace(-2.91%) -> ... -> 08:50:16 scalping_scanner_fast_precheck(-2.91%) -> 08:50:16 scalping_scanner_watching_runtime_skip:scanner_heavy_eval_stale_snapshot_recheck(-2.91%) -> 08:50:21 scalping_scanner_runtime_queue_lag(-2.91%)|
|노타(486990)|08:00:02|08:50:22|unknown|||`scalping_scanner_runtime_target_attach`/-|-|0|0|-||-||0|08:00:02 scalping_scanner_runtime_target_attach|
|비에이치(090460)|08:00:02|08:18:49|unknown|||`scalping_scanner_runtime_target_attach`/-|-|0|0|-||-||0|08:00:02 scalping_scanner_runtime_target_attach|
|포스코엠텍(009520)|08:00:02|08:50:22|unknown|||`scalping_scanner_runtime_target_attach`/-|-|0|0|-||-||0|08:00:02 scalping_scanner_runtime_target_attach|
|삼표시멘트(038500)|08:00:02|08:50:22|unknown|||`scalping_scanner_runtime_target_attach`/-|-|0|0|-||-||0|08:00:02 scalping_scanner_runtime_target_attach|

# 2026-07-06 12:00 이후 감시대상 BUY 전 흐름

- generated_at: 2026-07-06T13:39:00
- source_events: /home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-06.jsonl
- source_diagnostic: /home/ubuntu/KORStockScan/data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-07-06.json
- event_window_since: 12:00:00
- event_window_until: None
- symbol_count: 31
- rising_symbol_count_by_max_delta: 7
- rising_missed_buy_count_in_latest_diagnostic: 4
- rising_missed_symbol_count_in_report: 1
- rising_missed_residual_excluding_forced_scout_symbol_count: 0
- rising_missed_forced_scout_event_count: 154
- rising_missed_forced_scout_symbol_count: 15
- rising_missed_forced_scout_residual_symbol_count: 4
- real_submit_symbol_count_in_latest_diagnostic: 1
- buy_signal_or_pre_submit_pass_seen_symbols: 12
- stale_eval_symbol_count: 24
- rising_stale_eval_symbol_count: 7
- rising_fresh_only_symbol_count: 0
- stale_refresh_recovered_symbol_count: 19

## forced scout observation

- event_count: 154
- symbol_count: 15
- symbols: 000500, 000660, 002990, 005930, 011070, 024840, 034020, 042660, 042700, 086520, 200710, 272210, 399720, 402340, 477850
- rising_missed_residual_symbols: 000660, 086520, 272210, 399720
- rising_missed_residual_excluding_forced_scout_symbols: -
- decision_authority: source_quality_only
- runtime_effect: False

## blocker rollup

- 10: `scalping_scanner_promotion_latency_trace` / `scanner_fast_precheck_subscription_recheck_snapshot_applied`
- 5: `scalping_scanner_runtime_target_attach` / `-`
- 4: `scalping_scanner_promotion_latency_trace` / `scanner_fast_precheck_stability_pending`
- 2: `scalping_scanner_promotion_latency_trace` / `below_window_buy_value`
- 2: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 1: `scalp_entry_action_decision_snapshot` / `below_strength_base`
- 1: `rising_missed_scout_upgrade_eval` / `entry_cooldown_active`
- 1: `scalping_scanner_promotion_latency_trace` / `latency_state_danger`
- 1: `scalping_scanner_promotion_latency_trace` / `ws_snapshot_missing_or_zero_recovered`
- 1: `scalping_scanner_promotion_latency_trace` / `price_below_promotion_anchor`
- 1: `scalping_scanner_candidate_promoted` / `-`
- 1: `scalping_scanner_promotion_latency_trace` / `below_strength_base`

## blocker taxonomy

- 720: `runtime_backpressure`
- 112: `strategy_reject`
- 49: `pre_submit_quality_guard`
- 29: `watch_budget_reallocated`
- 22: `intended_guard`
- 21: `source_freshness_evictable`
- 5: `source_freshness_recovering`
- 2: `source_quality_exclusion_candidate`

## suppressed non-major blocker counts

- 720: `runtime_backpressure` / `scalping_scanner_watching_runtime_skip` / `scanner_full_eval_loop_budget_deferred`
- 49: `pre_submit_quality_guard` / `latency_block` / `latency_state_danger`
- 34: `strategy_reject` / `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 21: `source_freshness_evictable` / `scalping_scanner_watching_runtime_skip` / `ws_snapshot_missing_or_zero`
- 16: `intended_guard` / `scalping_scanner_runtime_target_attach` / `operator_manual_control_excluded_symbol`
- 16: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `stale_recovery_failed`
- 14: `strategy_reject` / `scalping_scanner_runtime_target_attach` / `new_watching_target_attached`
- 12: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `scanner_hardgate_prefilter`
- 10: `strategy_reject` / `scalping_scanner_runtime_target_attach` / `existing_watching_refreshed`
- 10: `strategy_reject` / `blocked_strength_momentum` / `below_window_buy_value`
- 8: `strategy_reject` / `ai_confirmed_terminal_no_budget` / `first_ai_wait_big_bite_not_confirmed`
- 7: `strategy_reject` / `blocked_strength_momentum` / `below_strength_base`

## rising-symbol blocker rollup

- 2: `scalping_scanner_promotion_latency_trace` / `scanner_fast_precheck_subscription_recheck_snapshot_applied`
- 1: `scalp_entry_action_decision_snapshot` / `below_strength_base`
- 1: `rising_missed_scout_upgrade_eval` / `entry_cooldown_active`
- 1: `scalping_scanner_promotion_latency_trace` / `latency_state_danger`
- 1: `scalping_scanner_promotion_latency_trace` / `ws_snapshot_missing_or_zero_recovered`
- 1: `scalping_scanner_promotion_latency_trace` / `price_below_promotion_anchor`

## rising fresh-only blocker rollup


## rising stale-mixed blocker rollup

- 2: `scalping_scanner_promotion_latency_trace` / `scanner_fast_precheck_subscription_recheck_snapshot_applied`
- 1: `scalp_entry_action_decision_snapshot` / `below_strength_base`
- 1: `rising_missed_scout_upgrade_eval` / `entry_cooldown_active`
- 1: `scalping_scanner_promotion_latency_trace` / `latency_state_danger`
- 1: `scalping_scanner_promotion_latency_trace` / `ws_snapshot_missing_or_zero_recovered`
- 1: `scalping_scanner_promotion_latency_trace` / `price_below_promotion_anchor`

## stale-eval rollup

- 23: `scalping_scanner_fast_precheck`
- 1: `scalp_entry_action_decision_snapshot`

## stale-eval category rollup

- 24: `diagnostic_quote_age_stale`

## bounded freshness recheck workorders

|종목|건수|diagnostic stale|history gap|latest|next action|authority|runtime|
|---|---:|---:|---:|---|---|---|---|
|에코프로(086520)|61|61|0|latency_block:latency_state_danger|add_or_tune_bounded_fresh_recheck_enqueue_after_stale_or_history_gap|source_quality_only|effect=False,apply=False|
|한화시스템(272210)|28|28|0|scalping_scanner_watching_runtime_skip:entry_cooldown_active|add_or_tune_bounded_fresh_recheck_enqueue_after_stale_or_history_gap|source_quality_only|effect=False,apply=False|
|가온칩스(399720)|4|4|0|scalping_scanner_runtime_target_attach:existing_watching_refreshed|add_or_tune_bounded_fresh_recheck_enqueue_after_stale_or_history_gap|source_quality_only|effect=False,apply=False|

## latency danger root cause

|종목|건수|top cause|spread ratio med/max|ws age med/max|spread ticks med/max|micro|bucket|
|---|---:|---|---:|---:|---:|---|---|
|가온전선(000500)|95|spread_microstructure_wide|0.008489/0.011804|114.0/549.0|5.0/7.0|neutral|spread=wide\|price=high\|depth=normal\|sample=rich|
|한미반도체(042700)|62|spread_too_wide|0.010438/0.012526|110.5/304.0|5.0/6.0|neutral|spread=wide\|price=high\|depth=thick\|sample=rich|
|에코프로(086520)|61|spread_microstructure_wide|0.005637/0.00678|97.0/3661.0|5.0/6.0|neutral|spread=wide\|price=high\|depth=thick\|sample=rich|
|LG이노텍(011070)|48|spread_microstructure_wide|0.005476/0.008705|120.5/554.0|5.0/8.0|neutral|spread=wide\|price=high\|depth=normal\|sample=rich|
|삼성전자(005930)|34|spread_microstructure_wide|0.007776/0.007825|56.5/116.0|5.0/5.0|neutral|spread=wide\|price=high\|depth=thick\|sample=rich|
|에이디테크놀로지(200710)|32|spread_microstructure_wide|0.009828/0.013289|96.0/531.0|6.0/8.0|neutral|spread=wide\|price=mid\|depth=normal\|sample=rich|
|두산에너빌리티(034020)|28|spread_microstructure_wide|0.00565/0.005663|78.0/338.0|5.0/5.0|neutral|spread=wide\|price=high\|depth=thick\|sample=rich|
|마키나락스(477850)|16|spread_microstructure_wide|0.008697/0.010221|57.0/277.0|5.0/6.0|neutral|spread=wide\|price=mid\|depth=thick\|sample=rich|
|KBI메탈(024840)|12|spread_microstructure_wide|0.009166/0.012939|76.0/400.0|5.0/7.0|neutral|spread=wide\|price=low\|depth=thick\|sample=rich|
|한화시스템(272210)|9|spread_microstructure_wide|0.006053/0.007034|49.0/88.0|5.0/6.0|neutral|spread=wide\|price=high\|depth=normal\|sample=rich|
|와이지-원(019210)|1|spread_microstructure_wide|0.009124/0.009124|337.0/337.0|5.0/5.0|neutral|spread=wide\|price=mid\|depth=thick\|sample=rich|
|오성첨단소재(052420)|1|spread_too_wide|0.025258/0.025258|41.0/41.0|22.0/22.0|neutral|spread=wide\|price=low\|depth=normal\|sample=rich|

## top rows by max delta

|종목|첫감시|마지막|상승여부|maxΔ|latestΔ|BUY전 주 blocker|class|stale평가|refresh회복|stale유형|max quote age|BUY전 통과신호|AI|실제submit|흐름|
|---|---:|---:|---|---:|---:|---|---|---:|---:|---|---:|---:|---:|---:|---|
|에이디테크놀로지(200710)|13:15:22|13:20:58|rising|9.98%|9.98%|`scalp_entry_action_decision_snapshot`/below_strength_base|-|11|3|diagnostic_quote_age_stale|8318.0|13:16:20|74/WAIT|0|13:15:22 scalping_scanner_candidate_promoted(+0.00%) -> 13:15:22 scalping_scanner_runtime_target_attach(+0.00%) -> 13:16:03 scalping_scanner_promotion_latency_trace(+9.98%) -> 13:16:03 scalping_scanner_fast_precheck(+9.98%) -> ... -> 13:19:17 scalp_entry_action_decision_snapshot:scalp_live_simulator(+9.98%) -> 13:20:53 rising_missed_scout_upgrade_eval(+9.98%) -> 13:20:58 scalping_scanner_watching_runtime_skip:entry_cooldown_active(+9.98%)|
|마키나락스(477850)|12:00:37|13:37:47|rising|8.74%|8.74%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|82|71|diagnostic_quote_age_stale|70819.0|12:06:51|70/not_evaluated|0|12:00:37 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%) -> 12:00:58 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:58 scalping_scanner_fast_precheck(+0.00%) -> 12:00:58 scalping_scanner_runtime_queue_lag(+0.00%) -> ... -> 13:37:22 scalping_scanner_runtime_queue_lag(+8.74%) -> 13:37:47 scalping_scanner_promotion_latency_trace(+8.74%) -> 13:37:47 scalping_scanner_heavy_eval_lag(+8.74%)|
|KBI메탈(024840)|12:00:04|13:37:59|rising|4.66%|4.66%|`rising_missed_scout_upgrade_eval`/entry_cooldown_active|-|45|60|diagnostic_quote_age_stale|71630.0|12:05:19|70/not_evaluated|0|12:00:04 rising_missed_scout_upgrade_eval(+4.66%) -> 12:00:06 scalping_scanner_watching_runtime_skip:entry_cooldown_active(+4.66%) -> 12:00:37 scalping_scanner_promotion_latency_trace(+4.66%) -> 12:00:37 scalping_scanner_fast_precheck(+4.66%) -> ... -> 13:37:59 orderbook_stability_observed(+4.66%) -> 13:37:59 latency_block:latency_state_danger(+4.66%) -> 13:37:59 scalp_entry_action_decision_snapshot:latency_state_danger(+4.66%)|
|가온칩스(399720)|13:36:30|13:37:47|rising|4.61%|4.61%|`scalping_scanner_promotion_latency_trace`/latency_state_danger|-|1|2|diagnostic_quote_age_stale|8935.0|13:37:47|0/not_evaluated|0|13:36:30 scalping_scanner_candidate_promoted(+0.00%) -> 13:36:30 scalping_scanner_runtime_target_attach(+0.00%) -> 13:37:22 scalping_scanner_promotion_latency_trace(+4.61%) -> 13:37:22 scalping_scanner_fast_precheck(+4.61%) -> ... -> 13:37:47 orderbook_stability_observed(+4.61%) -> 13:37:47 latency_block:latency_state_danger(+4.61%) -> 13:37:47 scalp_entry_action_decision_snapshot:latency_state_danger(+4.61%)|
|금호건설(002990)|12:00:58|13:36:09|rising|4.49%|4.49%|`scalping_scanner_promotion_latency_trace`/ws_snapshot_missing_or_zero_recovered|-|73|0|diagnostic_quote_age_stale|71034.0|-||0|12:00:58 scalping_scanner_promotion_latency_trace(+4.49%) -> 12:00:58 scalping_scanner_fast_precheck(+4.49%) -> 12:00:58 scalping_scanner_runtime_queue_lag(+4.49%) -> 12:01:13 scalping_scanner_promotion_latency_trace(+4.49%) -> ... -> 13:35:28 scalping_scanner_runtime_queue_lag(+4.49%) -> 13:36:09 scalping_scanner_promotion_latency_trace(+4.49%) -> 13:36:09 scalping_scanner_heavy_eval_lag(+4.49%)|
|남광토건(001260)|12:00:45|13:15:14|rising|3.80%|3.80%|`scalping_scanner_promotion_latency_trace`/price_below_promotion_anchor|-|55|8|diagnostic_quote_age_stale|26366.0|12:02:16|62/WAIT|0|12:00:45 rising_missed_scout_upgrade_eval(+3.80%) -> 12:00:50 scalping_scanner_watching_runtime_skip:entry_cooldown_active(+3.80%) -> 12:02:10 rising_missed_scout_upgrade_eval(+3.80%) -> 12:02:16 strength_momentum_observed:below_window_buy_value(+3.80%) -> ... -> 13:14:57 scalping_scanner_runtime_queue_lag(+3.80%) -> 13:15:14 scalping_scanner_promotion_latency_trace(+3.80%) -> 13:15:14 scalping_scanner_heavy_eval_lag(+3.80%)|
|위메이드(112040)|12:03:31|13:37:07|rising|0.48%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|83|101|diagnostic_quote_age_stale|70134.0|12:30:58|50/WAIT|0|12:03:31 scalping_scanner_candidate_promoted(+0.00%) -> 12:03:31 scalping_scanner_runtime_target_attach(+0.00%) -> 12:03:56 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:03:56 scalping_scanner_fast_precheck(+0.00%) -> ... -> 13:37:07 scalping_scanner_fast_precheck(+0.00%) -> 13:37:07 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%) -> 13:37:07 scalping_scanner_watching_runtime_skip:scanner_full_eval_loop_budget_deferred(+0.00%)|
|위메이드플레이(123420)|12:00:29|12:04:50|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/below_window_buy_value|-|4|8|diagnostic_quote_age_stale|17642.0|12:02:39|62/WAIT|0|12:00:29 scalping_scanner_candidate_promoted(+0.00%) -> 12:00:29 scalping_scanner_runtime_target_attach(+0.00%) -> 12:00:58 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:58 scalping_scanner_fast_precheck(+0.00%) -> ... -> 12:04:32 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 12:04:50 scalping_scanner_watch_eviction:scanner_hardgate_prefilter(+0.00%) -> 12:04:50 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%)|
|와이지-원(019210)|12:00:37|13:37:07|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|93|59|diagnostic_quote_age_stale|70846.0|12:04:08|62/WAIT|0|12:00:37 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:37 scalping_scanner_fast_precheck(+0.00%) -> 12:00:37 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:00:37 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 13:37:07 scalping_scanner_fast_precheck(+0.00%) -> 13:37:07 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%) -> 13:37:07 scalping_scanner_watching_runtime_skip:scanner_full_eval_loop_budget_deferred(+0.00%)|
|레몬헬스케어(365660)|12:00:37|13:37:33|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|85|59|diagnostic_quote_age_stale|69894.0|12:04:15|50/WAIT|0|12:00:37 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%) -> 12:00:58 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:58 scalping_scanner_fast_precheck(+0.00%) -> 12:00:58 scalping_scanner_runtime_queue_lag(+0.00%) -> ... -> 13:37:33 blocked_overbought(+0.00%) -> 13:37:33 strength_momentum_observed:insufficient_history(+0.00%) -> 13:37:33 blocked_strength_momentum:insufficient_history(+0.00%)|
|케이피항공산업(288180)|12:00:37|13:01:48|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|-|11|0|diagnostic_quote_age_stale|33414.0|-||0|12:00:37 scalping_scanner_watching_runtime_skip:ws_snapshot_missing_or_zero(+0.00%) -> 12:00:58 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:58 scalping_scanner_fast_precheck(+0.00%) -> 12:00:58 scalping_scanner_runtime_queue_lag(+0.00%) -> ... -> 13:00:32 scalping_scanner_runtime_queue_lag(+0.00%) -> 13:00:32 scalping_scanner_watch_eviction:stale_recovery_failed(+0.00%) -> 13:01:48 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%)|
|제닉(123330)|12:00:37|12:04:50|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|-|4|0|diagnostic_quote_age_stale|17528.0|-||0|12:00:37 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%) -> 12:00:58 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:58 scalping_scanner_fast_precheck(+0.00%) -> 12:00:58 scalping_scanner_runtime_queue_lag(+0.00%) -> ... -> 12:03:56 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:03:56 scalping_scanner_watch_eviction:stale_recovery_failed(+0.00%) -> 12:04:50 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%)|
|엠앤씨솔루션(484870)|12:00:37|12:55:43|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|3|3|diagnostic_quote_age_stale|50563.0|-|50/|0|12:00:37 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%) -> 12:02:01 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:02:01 scalping_scanner_fast_precheck(+0.00%) -> 12:02:01 scalping_scanner_runtime_queue_lag(+0.00%) -> ... -> 12:55:02 blocked_strength_momentum:below_strength_base(+0.00%) -> 12:55:04 scalping_scanner_watch_eviction:scanner_hardgate_prefilter(+0.00%) -> 12:55:43 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%)|
|상지건설(042940)|12:00:37|13:30:46|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|84|14|diagnostic_quote_age_stale|78658.0|-|50/|0|12:00:37 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%) -> 12:00:58 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:58 scalping_scanner_fast_precheck(+0.00%) -> 12:00:58 scalping_scanner_runtime_queue_lag(+0.00%) -> ... -> 13:30:46 scalping_scanner_fast_precheck(+0.00%) -> 13:30:46 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%) -> 13:30:46 scalping_scanner_watching_runtime_skip:scanner_full_eval_loop_budget_deferred(+0.00%)|
|파세코(037070)|12:00:37|13:33:44|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_stability_pending|-|85|21|diagnostic_quote_age_stale|74741.0|-|50/|0|12:00:37 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%) -> 12:02:01 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:02:01 scalping_scanner_fast_precheck(+0.00%) -> 12:02:01 scalping_scanner_runtime_queue_lag(+0.00%) -> ... -> 13:32:42 scalping_scanner_fast_precheck(+0.00%) -> 13:33:44 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%) -> 13:33:44 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%)|
|삼성공조(006660)|12:05:02|13:37:07|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|59|38|diagnostic_quote_age_stale|70150.0|12:18:42|50/DROP|0|12:05:02 scalping_scanner_candidate_promoted(+0.00%) -> 12:05:02 scalping_scanner_runtime_target_attach(+0.00%) -> 12:06:34 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:06:34 scalping_scanner_fast_precheck(+0.00%) -> ... -> 13:37:07 scalping_scanner_fast_precheck(+0.00%) -> 13:37:07 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%) -> 13:37:07 scalping_scanner_watching_runtime_skip:scanner_full_eval_loop_budget_deferred(+0.00%)|
|효성화학(298000)|12:05:02|13:37:07|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_stability_pending|-|86|8|diagnostic_quote_age_stale|78192.0|-|50/|0|12:05:02 scalping_scanner_candidate_promoted(+0.00%) -> 12:05:02 scalping_scanner_runtime_target_attach(+0.00%) -> 12:06:34 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:06:34 scalping_scanner_fast_precheck(+0.00%) -> ... -> 13:37:07 scalping_scanner_fast_precheck(+0.00%) -> 13:37:07 scalping_scanner_runtime_queue_lag(+0.00%) -> 13:37:07 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%)|
|NHN(181710)|12:05:02|13:37:07|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|81|18|diagnostic_quote_age_stale|72354.0|-|50/|0|12:05:02 scalping_scanner_candidate_promoted(+0.00%) -> 12:05:02 scalping_scanner_runtime_target_attach(+0.00%) -> 12:06:34 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:06:34 scalping_scanner_fast_precheck(+0.00%) -> ... -> 13:37:07 scalping_scanner_fast_precheck(+0.00%) -> 13:37:07 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%) -> 13:37:07 scalping_scanner_watching_runtime_skip:scanner_full_eval_loop_budget_deferred(+0.00%)|
|코스맥스엔비티(222040)|12:45:44|12:50:08|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_stability_pending|-|3|0|diagnostic_quote_age_stale|28843.0|-||0|12:45:44 scalping_scanner_candidate_promoted(+0.00%) -> 12:45:44 scalping_scanner_runtime_target_attach(+0.00%) -> 12:46:02 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:46:02 scalping_scanner_fast_precheck(+0.00%) -> ... -> 12:48:45 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:48:45 scalping_scanner_watch_eviction:stale_recovery_failed(+0.00%) -> 12:50:08 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%)|
|한화오션(042660)|12:50:31|12:52:19|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_stability_pending|-|1|0|diagnostic_quote_age_stale|17404.0|-||0|12:50:31 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:50:31 scalping_scanner_fast_precheck(+0.00%) -> 12:50:31 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:51:10 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%) -> 12:52:19 scalping_scanner_runtime_target_attach|
|지엔씨에너지(119850)|13:02:21|13:07:02|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|5|4|diagnostic_quote_age_stale|20991.0|-|50/|0|13:02:21 scalping_scanner_candidate_promoted(+0.00%) -> 13:02:21 scalping_scanner_runtime_target_attach(+0.00%) -> 13:03:37 scalping_scanner_promotion_latency_trace(+0.00%) -> 13:03:37 scalping_scanner_fast_precheck(+0.00%) -> ... -> 13:06:22 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 13:06:26 scalping_scanner_watch_eviction:scanner_hardgate_prefilter(+0.00%) -> 13:07:02 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%)|
|WON K-글로벌수급상위(000880)|13:12:20|13:12:20|flat_or_falling|0.00%|0.00%|`scalping_scanner_candidate_promoted`/-|-|0|0|-||-||0|13:12:20 scalping_scanner_candidate_promoted(+0.00%) -> 13:12:20 scalping_scanner_runtime_target_attach(+0.00%)|
|뉴파워프라즈마(144960)|13:16:53|13:20:47|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/below_strength_base|-|2|2|diagnostic_quote_age_stale|20674.0|-|50/|0|13:16:53 scalping_scanner_candidate_promoted(+0.00%) -> 13:16:53 scalping_scanner_runtime_target_attach(+0.00%) -> 13:17:41 scalping_scanner_promotion_latency_trace(+0.00%) -> 13:17:41 scalping_scanner_fast_precheck(+0.00%) -> ... -> 13:19:42 blocked_strength_momentum:below_strength_base(+0.00%) -> 13:19:47 scalping_scanner_watch_eviction:scanner_hardgate_prefilter(+0.00%) -> 13:20:47 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%)|
|가온전선(000500)|13:19:54|13:37:07|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|13|7|diagnostic_quote_age_stale|70847.0|13:22:40|50/DROP|0|13:19:54 scalping_scanner_candidate_promoted(+0.00%) -> 13:19:54 scalping_scanner_runtime_target_attach(+0.00%) -> 13:21:07 scalping_scanner_promotion_latency_trace(+0.00%) -> 13:21:07 scalping_scanner_fast_precheck(+0.00%) -> ... -> 13:37:07 scalping_scanner_fast_precheck(+0.00%) -> 13:37:07 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%) -> 13:37:07 scalping_scanner_watching_runtime_skip:scanner_full_eval_loop_budget_deferred(+0.00%)|
|오성첨단소재(052420)|13:31:58|13:37:07|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/below_window_buy_value|-|2|8|diagnostic_quote_age_stale|65853.0|13:33:59|76/BUY|0|13:31:58 scalping_scanner_candidate_promoted(+0.00%) -> 13:31:58 scalping_scanner_runtime_target_attach(+0.00%) -> 13:32:42 scalping_scanner_promotion_latency_trace(+0.00%) -> 13:32:42 scalping_scanner_fast_precheck(+0.00%) -> ... -> 13:37:07 scalping_scanner_fast_precheck(+0.00%) -> 13:37:07 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%) -> 13:37:07 scalping_scanner_watching_runtime_skip:scanner_full_eval_loop_budget_deferred(+0.00%)|
|한미반도체(042700)|12:00:38|13:37:08|unknown|||`scalping_scanner_runtime_target_attach`/-|-|0|0|-||-||0|12:00:38 scalping_scanner_runtime_target_attach|
|노타(486990)|12:00:38|13:37:08|unknown|||`scalping_scanner_runtime_target_attach`/-|-|0|0|-||-||0|12:00:38 scalping_scanner_runtime_target_attach|
|LS ELECTRIC(010120)|12:00:38|13:37:08|unknown|||`scalping_scanner_runtime_target_attach`/-|-|0|0|-||-||0|12:00:38 scalping_scanner_runtime_target_attach|
|포스코엠텍(009520)|12:00:38|13:37:08|unknown|||`scalping_scanner_runtime_target_attach`/-|-|0|0|-||-||0|12:00:38 scalping_scanner_runtime_target_attach|
|삼표시멘트(038500)|12:00:38|13:37:08|unknown|||`scalping_scanner_runtime_target_attach`/-|-|0|0|-||-||0|12:00:38 scalping_scanner_runtime_target_attach|
|대원전선(006340)|13:00:50|13:31:58|unknown|||`scalping_scanner_candidate_observed`/-|-|0|0|-||-||0|13:00:50 scalping_scanner_candidate_observed -> 13:00:50 scalping_scanner_real_source_guard_block -> 13:19:54 scalping_scanner_candidate_observed -> 13:19:54 scalping_scanner_real_source_guard_block -> 13:31:58 scalping_scanner_candidate_observed -> 13:31:58 scalping_scanner_real_source_guard_block|

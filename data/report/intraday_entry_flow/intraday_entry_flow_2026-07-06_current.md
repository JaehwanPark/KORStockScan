# 2026-07-06 12:00 이후 감시대상 BUY 전 흐름

- generated_at: 2026-07-06T12:06:59
- source_events: /home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-06.jsonl
- source_diagnostic: /home/ubuntu/KORStockScan/data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-07-06.json
- event_window_since: 12:00:00
- event_window_until: None
- symbol_count: 21
- rising_symbol_count_by_max_delta: 3
- rising_missed_buy_count_in_latest_diagnostic: 4
- rising_missed_symbol_count_in_report: 0
- rising_missed_residual_excluding_forced_scout_symbol_count: 0
- rising_missed_forced_scout_event_count: 7
- rising_missed_forced_scout_symbol_count: 14
- rising_missed_forced_scout_residual_symbol_count: 4
- real_submit_symbol_count_in_latest_diagnostic: 1
- buy_signal_or_pre_submit_pass_seen_symbols: 6
- stale_eval_symbol_count: 15
- rising_stale_eval_symbol_count: 2
- rising_fresh_only_symbol_count: 1
- stale_refresh_recovered_symbol_count: 9

## forced scout observation

- event_count: 7
- symbol_count: 14
- symbols: 000500, 000660, 002990, 005930, 011070, 024840, 034020, 042660, 042700, 086520, 200710, 272210, 399720, 402340
- rising_missed_residual_symbols: 000660, 086520, 272210, 399720
- rising_missed_residual_excluding_forced_scout_symbols: -
- decision_authority: source_quality_only
- runtime_effect: False

## blocker rollup

- 5: `scalping_scanner_runtime_target_attach` / `-`
- 3: `scalping_scanner_promotion_latency_trace` / `scanner_fast_precheck_subscription_recheck_snapshot_applied`
- 3: `scalping_scanner_candidate_promoted` / `-`
- 2: `scalping_scanner_promotion_latency_trace` / `below_strength_base`
- 2: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 1: `rising_missed_scout_upgrade_eval` / `entry_cooldown_active`
- 1: `scalping_scanner_promotion_latency_trace` / `-`
- 1: `rising_missed_scout_upgrade_eval` / `price_below_promotion_anchor`
- 1: `scalping_scanner_promotion_latency_trace` / `below_window_buy_value`
- 1: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_subscription_recheck_snapshot_applied`
- 1: `scalping_scanner_promotion_latency_trace` / `scanner_fast_precheck_stability_pending`

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

- 1: `rising_missed_scout_upgrade_eval` / `entry_cooldown_active`
- 1: `scalping_scanner_promotion_latency_trace` / `-`
- 1: `rising_missed_scout_upgrade_eval` / `price_below_promotion_anchor`

## rising fresh-only blocker rollup

- 1: `rising_missed_scout_upgrade_eval` / `price_below_promotion_anchor`

## rising stale-mixed blocker rollup

- 1: `rising_missed_scout_upgrade_eval` / `entry_cooldown_active`
- 1: `scalping_scanner_promotion_latency_trace` / `-`

## stale-eval rollup

- 15: `scalping_scanner_fast_precheck`

## stale-eval category rollup

- 15: `diagnostic_quote_age_stale`

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
|한화시스템(272210)|9|spread_microstructure_wide|0.006053/0.007034|49.0/88.0|5.0/6.0|neutral|spread=wide\|price=high\|depth=normal\|sample=rich|
|KBI메탈(024840)|1|spread_too_wide|0.011321/0.011321|194.0/194.0|6.0/6.0|neutral|spread=wide\|price=low\|depth=thick\|sample=rich|

## top rows by max delta

|종목|첫감시|마지막|상승여부|maxΔ|latestΔ|BUY전 주 blocker|class|stale평가|refresh회복|stale유형|max quote age|BUY전 통과신호|AI|실제submit|흐름|
|---|---:|---:|---|---:|---:|---|---|---:|---:|---|---:|---:|---:|---:|---|
|KBI메탈(024840)|12:00:04|12:06:57|rising|4.66%|4.66%|`rising_missed_scout_upgrade_eval`/entry_cooldown_active|-|5|5|diagnostic_quote_age_stale|57925.0|12:05:19|54/not_evaluated|0|12:00:04 rising_missed_scout_upgrade_eval(+4.66%) -> 12:00:06 scalping_scanner_watching_runtime_skip:entry_cooldown_active(+4.66%) -> 12:00:37 scalping_scanner_promotion_latency_trace(+4.66%) -> 12:00:37 scalping_scanner_fast_precheck(+4.66%) -> ... -> 12:05:47 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+4.66%) -> 12:05:47 scalp_entry_action_decision_snapshot(+4.66%) -> 12:06:57 rising_missed_scout_upgrade_eval(+4.66%)|
|금호건설(002990)|12:00:58|12:06:34|rising|4.49%|4.49%|`scalping_scanner_promotion_latency_trace`/-|-|5|0|diagnostic_quote_age_stale|23363.0|-||0|12:00:58 scalping_scanner_promotion_latency_trace(+4.49%) -> 12:00:58 scalping_scanner_fast_precheck(+4.49%) -> 12:00:58 scalping_scanner_runtime_queue_lag(+4.49%) -> 12:01:13 scalping_scanner_promotion_latency_trace(+4.49%) -> ... -> 12:06:34 scalping_scanner_runtime_queue_lag(+4.49%) -> 12:06:34 scalping_scanner_promotion_latency_trace(+4.49%) -> 12:06:34 scalping_scanner_heavy_eval_lag(+4.49%)|
|남광토건(001260)|12:00:45|12:06:22|rising|3.80%|3.80%|`rising_missed_scout_upgrade_eval`/price_below_promotion_anchor|-|0|8|-|2909.0|12:02:16|62/WAIT|0|12:00:45 rising_missed_scout_upgrade_eval(+3.80%) -> 12:00:50 scalping_scanner_watching_runtime_skip:entry_cooldown_active(+3.80%) -> 12:02:10 rising_missed_scout_upgrade_eval(+3.80%) -> 12:02:16 strength_momentum_observed:below_window_buy_value(+3.80%) -> ... -> 12:06:19 scalp_entry_action_decision_snapshot(+3.80%) -> 12:06:22 rising_missed_same_day_reentry_risk_marked(+3.80%) -> 12:06:22 same_symbol_loss_reentry_cooldown(+3.80%)|
|위메이드플레이(123420)|12:00:29|12:04:50|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/below_window_buy_value|-|4|8|diagnostic_quote_age_stale|17642.0|12:02:39|62/WAIT|0|12:00:29 scalping_scanner_candidate_promoted(+0.00%) -> 12:00:29 scalping_scanner_runtime_target_attach(+0.00%) -> 12:00:58 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:58 scalping_scanner_fast_precheck(+0.00%) -> ... -> 12:04:32 blocked_strength_momentum:below_window_buy_value(+0.00%) -> 12:04:50 scalping_scanner_watch_eviction:scanner_hardgate_prefilter(+0.00%) -> 12:04:50 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%)|
|와이지-원(019210)|12:00:37|12:06:54|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|7|9|diagnostic_quote_age_stale|58051.0|12:04:08|62/WAIT|0|12:00:37 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:37 scalping_scanner_fast_precheck(+0.00%) -> 12:00:37 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:00:37 scalping_scanner_promotion_latency_trace(+0.00%) -> ... -> 12:06:53 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:06:53 scalping_scanner_heavy_eval_lag(+0.00%) -> 12:06:54 scalping_scanner_watching_runtime_skip:entry_cooldown_active(+0.00%)|
|레몬헬스케어(365660)|12:00:37|12:06:05|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|4|11|diagnostic_quote_age_stale|47652.0|12:04:15|54/WAIT|0|12:00:37 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%) -> 12:00:58 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:58 scalping_scanner_fast_precheck(+0.00%) -> 12:00:58 scalping_scanner_runtime_queue_lag(+0.00%) -> ... -> 12:06:05 scalping_scanner_fast_precheck(+0.00%) -> 12:06:05 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%) -> 12:06:05 scalping_scanner_watching_runtime_skip:scanner_full_eval_loop_budget_deferred(+0.00%)|
|마키나락스(477850)|12:00:37|12:06:51|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/below_strength_base|-|5|10|diagnostic_quote_age_stale|55761.0|12:06:51|58/WAIT|0|12:00:37 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%) -> 12:00:58 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:58 scalping_scanner_fast_precheck(+0.00%) -> 12:00:58 scalping_scanner_runtime_queue_lag(+0.00%) -> ... -> 12:06:51 blocked_ai_score(+0.00%) -> 12:06:51 ai_confirmed_terminal_no_budget:blocked_ai_score_below_buy_score_threshold(+0.00%) -> 12:06:51 scalp_entry_action_decision_snapshot:Position advantage not met (curr_vs_ma5_bp > 0 but curr_vs_micro_vwap_bp > 0 as positive; however, speed condition not s(+0.00%)|
|케이피항공산업(288180)|12:00:37|12:04:50|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|-|5|0|diagnostic_quote_age_stale|27727.0|-||0|12:00:37 scalping_scanner_watching_runtime_skip:ws_snapshot_missing_or_zero(+0.00%) -> 12:00:58 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:58 scalping_scanner_fast_precheck(+0.00%) -> 12:00:58 scalping_scanner_runtime_queue_lag(+0.00%) -> ... -> 12:03:56 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:03:56 scalping_scanner_watch_eviction:stale_recovery_failed(+0.00%) -> 12:04:50 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%)|
|제닉(123330)|12:00:37|12:04:50|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_stability_pending|-|4|0|diagnostic_quote_age_stale|17528.0|-||0|12:00:37 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%) -> 12:00:58 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:58 scalping_scanner_fast_precheck(+0.00%) -> 12:00:58 scalping_scanner_runtime_queue_lag(+0.00%) -> ... -> 12:03:56 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:03:56 scalping_scanner_watch_eviction:stale_recovery_failed(+0.00%) -> 12:04:50 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%)|
|엠앤씨솔루션(484870)|12:00:37|12:02:01|flat_or_falling|0.00%|0.00%|`scalping_scanner_watching_runtime_skip`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|1|0|diagnostic_quote_age_stale|50563.0|-||0|12:00:37 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%) -> 12:02:01 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:02:01 scalping_scanner_fast_precheck(+0.00%) -> 12:02:01 scalping_scanner_runtime_queue_lag(+0.00%) -> 12:02:01 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:02:01 scalping_scanner_fast_precheck(+0.00%) -> 12:02:01 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%) -> 12:02:01 scalping_scanner_watching_runtime_skip:scanner_full_eval_loop_budget_deferred(+0.00%)|
|상지건설(042940)|12:00:37|12:06:05|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_stability_pending|-|4|2|diagnostic_quote_age_stale|22389.0|-|62/|0|12:00:37 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_stability_pending(+0.00%) -> 12:00:58 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:00:58 scalping_scanner_fast_precheck(+0.00%) -> 12:00:58 scalping_scanner_runtime_queue_lag(+0.00%) -> ... -> 12:05:37 strength_momentum_observed:below_strength_base(+0.00%) -> 12:05:37 blocked_strength_momentum:below_strength_base(+0.00%) -> 12:06:05 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%)|
|파세코(037070)|12:00:37|12:06:43|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/scanner_fast_precheck_subscription_recheck_snapshot_applied|-|5|6|diagnostic_quote_age_stale|55761.0|-|75/|0|12:00:37 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%) -> 12:02:01 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:02:01 scalping_scanner_fast_precheck(+0.00%) -> 12:02:01 scalping_scanner_runtime_queue_lag(+0.00%) -> ... -> 12:06:42 blocked_overbought(+0.00%) -> 12:06:42 strength_momentum_observed:below_strength_base(+0.00%) -> 12:06:43 blocked_strength_momentum:below_strength_base(+0.00%)|
|위메이드(112040)|12:03:31|12:06:05|flat_or_falling|0.00%|0.00%|`scalping_scanner_promotion_latency_trace`/below_strength_base|-|2|2|diagnostic_quote_age_stale|16356.0|-|50/|0|12:03:31 scalping_scanner_candidate_promoted(+0.00%) -> 12:03:31 scalping_scanner_runtime_target_attach(+0.00%) -> 12:03:56 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:03:56 scalping_scanner_fast_precheck(+0.00%) -> ... -> 12:05:25 blocked_strength_momentum:below_strength_base(+0.00%) -> 12:05:27 scalping_scanner_watch_eviction:scanner_hardgate_prefilter(+0.00%) -> 12:06:05 scalping_scanner_watching_runtime_skip:scanner_fast_precheck_subscription_recheck_snapshot_applied(+0.00%)|
|삼성공조(006660)|12:05:02|12:06:34|flat_or_falling|0.00%|0.00%|`scalping_scanner_candidate_promoted`/-|-|1|0|diagnostic_quote_age_stale|23255.0|-||0|12:05:02 scalping_scanner_candidate_promoted(+0.00%) -> 12:05:02 scalping_scanner_runtime_target_attach(+0.00%) -> 12:06:34 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:06:34 scalping_scanner_fast_precheck(+0.00%) -> 12:06:34 scalping_scanner_runtime_queue_lag(+0.00%)|
|효성화학(298000)|12:05:02|12:06:34|flat_or_falling|0.00%|0.00%|`scalping_scanner_candidate_promoted`/-|-|1|0|diagnostic_quote_age_stale|27975.0|-||0|12:05:02 scalping_scanner_candidate_promoted(+0.00%) -> 12:05:02 scalping_scanner_runtime_target_attach(+0.00%) -> 12:06:34 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:06:34 scalping_scanner_fast_precheck(+0.00%) -> 12:06:34 scalping_scanner_runtime_queue_lag(+0.00%)|
|NHN(181710)|12:05:02|12:06:34|flat_or_falling|0.00%|0.00%|`scalping_scanner_candidate_promoted`/-|-|1|0|diagnostic_quote_age_stale|23544.0|-||0|12:05:02 scalping_scanner_candidate_promoted(+0.00%) -> 12:05:02 scalping_scanner_runtime_target_attach(+0.00%) -> 12:06:34 scalping_scanner_promotion_latency_trace(+0.00%) -> 12:06:34 scalping_scanner_fast_precheck(+0.00%) -> 12:06:34 scalping_scanner_runtime_queue_lag(+0.00%)|
|한미반도체(042700)|12:00:38|12:06:06|unknown|||`scalping_scanner_runtime_target_attach`/-|-|0|0|-||-||0|12:00:38 scalping_scanner_runtime_target_attach|
|노타(486990)|12:00:38|12:06:06|unknown|||`scalping_scanner_runtime_target_attach`/-|-|0|0|-||-||0|12:00:38 scalping_scanner_runtime_target_attach|
|LS ELECTRIC(010120)|12:00:38|12:06:06|unknown|||`scalping_scanner_runtime_target_attach`/-|-|0|0|-||-||0|12:00:38 scalping_scanner_runtime_target_attach|
|포스코엠텍(009520)|12:00:38|12:06:06|unknown|||`scalping_scanner_runtime_target_attach`/-|-|0|0|-||-||0|12:00:38 scalping_scanner_runtime_target_attach|
|삼표시멘트(038500)|12:00:38|12:06:06|unknown|||`scalping_scanner_runtime_target_attach`/-|-|0|0|-||-||0|12:00:38 scalping_scanner_runtime_target_attach|

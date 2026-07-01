# 2026-07-01 16:00~19:00 intraday entry flow final stabilization

- source_flow_final: data/report/intraday_entry_flow/intraday_entry_flow_2026-07-01_current.md
- source_events_final: /home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-01.jsonl
- generated_from: fixed current flow artifact, not timestamp snapshots
- analysis_window: 2026-07-01T16:00:00+09:00 -> 2026-07-01T19:00:00+09:00
- runtime_effect: false
- allowed_runtime_apply: false

## decision

16:00~19:00 KST goal is closed as final stabilization from the fixed current flow artifact. Forced `rising_missed_one_share_entry` scout rows remain excluded from normal BUY/submit/fill success and from general BUY bottleneck resolution.

## evidence

- symbol_count: 81
- rising_symbol_count_by_max_delta: 15
- rising_missed_residual_excluding_forced_scout_symbol_count: 4
- rising_missed_forced_scout_event_count: 274
- real_submit_symbol_count_in_latest_diagnostic: 1
- buy_signal_or_pre_submit_pass_seen_symbols: 15

## operating boundary

No runtime threshold mutation, provider route change, broker/account/order/quantity/cooldown guard relaxation, hard/protect/emergency safety relaxation, or direct bot process kill was performed by this finalization step.

## final current-flow excerpt

# 2026-07-01 16:00 이후 감시대상 BUY 전 흐름

- generated_at: 2026-07-01T19:00:15
- source_events: /home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-01.jsonl
- source_diagnostic: /home/ubuntu/KORStockScan/data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-07-01.json
- event_window_since: 2026-07-01T16:00:00+09:00
- event_window_until: 2026-07-01T19:00:10+09:00
- symbol_count: 81
- rising_symbol_count_by_max_delta: 15
- rising_missed_buy_count_in_latest_diagnostic: 13
- rising_missed_symbol_count_in_report: 13
- rising_missed_residual_excluding_forced_scout_symbol_count: 4
- rising_missed_forced_scout_event_count: 274
- rising_missed_forced_scout_symbol_count: 9
- rising_missed_forced_scout_residual_symbol_count: 9
- real_submit_symbol_count_in_latest_diagnostic: 1
- buy_signal_or_pre_submit_pass_seen_symbols: 15
- stale_eval_symbol_count: 75
- rising_stale_eval_symbol_count: 15
- rising_fresh_only_symbol_count: 0
- stale_refresh_recovered_symbol_count: 27

## forced scout observation

- event_count: 274
- symbol_count: 9
- symbols: 000500, 010120, 033100, 037710, 045100, 060370, 062040, 084370, 336260
- rising_missed_residual_symbols: 000500, 010120, 033100, 037710, 045100, 060370, 062040, 084370, 336260
- rising_missed_residual_excluding_forced_scout_symbols: 006340, 037350, 067080, 295310
- decision_authority: source_quality_only
- runtime_effect: False

## blocker rollup

- 47: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 20: `scalping_scanner_watching_runtime_skip` / `ws_snapshot_missing_or_zero`
- 5: `scalping_scanner_watching_runtime_skip` / `entry_cooldown_active`
- 5: `scalping_scanner_candidate_observed` / `-`
- 2: `blocked_strength_momentum` / `insufficient_history`
- 1: `latency_block` / `latency_state_danger`
- 1: `scalping_scanner_candidate_promoted` / `-`

## blocker taxonomy

- 197: `strategy_reject`
- 104: `source_freshness_evictable`
- 86: `watch_budget_reallocated`
- 47: `pre_submit_quality_guard`
- 21: `source_freshness_recovering`
- 11: `intended_guard`
- 7: `runtime_backpressure`
- 2: `source_freshness_blocker`

## suppressed non-major blocker counts

- 104: `source_freshness_evictable` / `scalping_scanner_watching_runtime_skip` / `ws_snapshot_missing_or_zero`
- 80: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `stale_recovery_failed`
- 47: `pre_submit_quality_guard` / `latency_block` / `latency_state_danger`
- 21: `source_freshness_recovering` / `scalping_scanner_watching_runtime_skip` / `ws_snapshot_missing_or_zero`
- 7: `runtime_backpressure` / `scalping_scanner_watching_runtime_skip` / `scanner_full_eval_loop_budget_deferred`
- 4: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `scanner_hardgate_prefilter`
- 1: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `source_quality_unresolved`
- 1: `watch_budget_reallocated` / `scalping_scanner_watch_eviction` / `scanner_no_trade_hot_slot_rotation`

## rising-symbol blocker rollup

- 5: `scalping_scanner_watching_runtime_skip` / `entry_cooldown_active`
- 4: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 3: `scalping_scanner_watching_runtime_skip` / `ws_snapshot_missing_or_zero`
- 2: `blocked_strength_momentum` / `insufficient_history`
- 1: `latency_block` / `latency_state_danger`

## rising fresh-only blocker rollup


## rising stale-mixed blocker rollup

- 5: `scalping_scanner_watching_runtime_skip` / `entry_cooldown_active`
- 4: `scalping_scanner_watching_runtime_skip` / `scanner_fast_precheck_stability_pending`
- 3: `scalping_scanner_watching_runtime_skip` / `ws_snapshot_missing_or_zero`
- 2: `blocked_strength_momentum` / `insufficient_history`
- 1: `latency_block` / `latency_state_danger`

## stale-eval rollup

- 49: `scalping_scanner_fast_precheck`
- 25: `scalping_scanner_watching_runtime_skip`
- 1: `blocked_strength_momentum`

## stale-eval category rollup

- 50: `diagnostic_quote_age_stale`
- 25: `ws_snapshot_missing_or_zero`

## bounded freshness recheck workorders

|종목|건수|diagnostic stale|history gap|latest|next action|authority|runtime|
|---|---:|---:|---:|---|---|---|---|
|광주신세계(037710)|124|69|55|blocked_strength_momentum:insufficient_history|add_or_tune_bounded_fresh_recheck_enqueue_after_stale_or_history_gap|source_quality_only|effect=False,apply=False|
|제룡전기(033100)|41|29|12|blocked_strength_momentum:below_window_buy_value|add_or_tune_bounded_fresh_recheck_enqueue_after_stale_or_history_gap|source_quality_only|effect=False,apply=False|
|유진테크(084370)|38|27|11|latency_block:latency_state_danger|add_or_tune_bounded_fresh_recheck_enqueue_after_stale_or_history_gap|source_quality_only|effect=False,apply=False|
|한양이엔지(045100)|28|26|2|latency_block:latency_state_danger|add_or_tune_bounded_fresh_recheck_enqueue_after_stale_or_history_gap|source_quality_only|effect=False,apply=False|
|산일전기(062040)|25|25|0|latency_block:latency_state_danger|add_or_tune_bounded_fresh_recheck_enqueue_after_stale_or_history_gap|source_quality_only|effect=False,apply=False|
|LS ELECTRIC(010120)|19|19|0|latency_block:latency_state_danger|add_or_tune_bounded_fresh_recheck_enqueue_after_stale_or_history_gap|source_quality_only|effect=False,apply=False|
|LS마린솔루션(060370)|18|18|0|latency_block:latency_state_danger|add_or_tune_bounded_fresh_recheck_enqueue_after_stale_or_history_gap|source_quality_only|effect=False,apply=False|
|에이치브이엠(295310)|12|9|3|scalping_scanner_watch_eviction:stale_recovery_failed|add_or_tune_bounded_fresh_recheck_enqueue_after_stale_or_history_gap|source_quality_only|effect=False,apply=False|
|가온전선(000500)|6|6|0|latency_block:latency_state_danger|add_or_tune_bounded_fresh_recheck_enqueue_after_stale_or_history_gap|source_quality_only|effect=False,apply=False|
|두산퓨얼셀(336260)|6|6|0|latency_block:latency_state_danger|add_or_tune_bounded_fresh_recheck_enqueue_after_stale_or_history_gap|source_quality_only|effect=False,apply=False|

## latency da

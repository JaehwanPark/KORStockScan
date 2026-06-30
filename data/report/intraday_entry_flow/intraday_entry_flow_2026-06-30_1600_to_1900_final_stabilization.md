# 2026-06-30 16:00-19:00 intraday entry flow final stabilization

- generated_at: 2026-06-30T19:22:49+09:00
- time_window_kst: 2026-06-30T16:00:00+09:00/2026-06-30T19:00:00+09:00
- monitor_interval: 10 minutes
- monitor_mode: live_intraday_current_artifact_refresh
- buy_window_status: within_scalping_buy_window_16:00_to_19:45
- buy_window_source: data/threshold_cycle/runtime_env/threshold_runtime_env_2026-06-30.env, data/threshold_cycle/runtime_env/operator_runtime_overrides.env
- source_events: data/runtime/sentinel_event_cache/buy_funnel_sentinel_events_2026-06-30.jsonl
- source_diagnostic_final: data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-30_1600_1900_goal.json
- source_flow_final: data/report/intraday_entry_flow/intraday_entry_flow_2026-06-30_current.md
- decision_authority: diagnostic_only_no_runtime_change
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses_preserved: threshold_mutation, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, quantity_or_cap_change, provider_route_change, bot_restart

## Decision

- 판정: 16:00-19:00 KST 감시는 정상 buy window 안에서 수행됐다. 이전 `after_buy_window` 판정은 잘못된 기본창 해석이며, 최종 기준은 `16:00:00-19:45:00` operator/runtime env다.
- 판정: 일반 BUY/pre-submit/real submit까지 도달한 종목은 없었다. `buy_signal_or_pre_submit_pass_seen_symbols=0`, `real_submit_symbol_count_in_latest_diagnostic=0`.
- 판정: 상승 관측은 1종목이었지만 BUY 전 단계에서 `scanner_fast_precheck_stability_pending` 전략 reject로 남았고 submit path에 진입하지 않았다.
- 판정: forced 1-share scout는 0건이다. 따라서 `rising_missed_one_share_entry`와 일반 BUY/submit/fill 성공을 섞어 해석할 여지가 없다.
- 판정: 보완 후 `scanner_strength_history_or_stale_eval`는 root cause 우선순위에서 제거됐다. `eligible_for_heavy_entry_eval` fast-precheck relief/progress row를 zero-strength source-quality workorder로 세던 진단 false-positive를 수정했고, rising-missed 반복 zero-strength workorder는 0건이다.

## Final Flow Summary

|metric|value|
|---|---:|
|symbol_count|15|
|rising_symbol_count_by_max_delta|1|
|rising_fresh_only_symbol_count|1|
|rising_missed_buy_count_in_latest_diagnostic|7|
|rising_missed_residual_excluding_forced_scout_symbol_count|7|
|forced_scout_event_count|0|
|forced_scout_symbol_count|0|
|buy_signal_or_pre_submit_pass_seen_symbols|0|
|real_submit_symbol_count_in_latest_diagnostic|0|
|stale_eval_symbol_count_in_flow_report|0|
|stale_refresh_recovered_symbol_count|0|

## Diagnostic Summary

|metric|value|
|---|---:|
|entry_event_count|13743|
|actionable_major_blocker_count|144|
|promoted_symbol_count|44|
|promoted_before_window_symbol_count|6|
|repeated_zero_strength_history_workorder_count|7|
|rising_missed_repeated_zero_strength_history_workorder_count|0|
|rising_missed_low_ai_or_negative_pressure_stale_or_delayed_eval|224|
|rising_missed_stale_or_delayed_diagnostic_quote_age_stale|224|
|rising_missed_full_eval_budget_deferred_count|0|
|suppressed_non_actionable_blocker_count|104|

## Blocker Taxonomy

|class|count|interpretation|
|---|---:|---|
|strategy_reject|144|BUY path did not advance; dominant blocker is scanner fast precheck stability pending.|
|source_freshness_evictable|37|WS snapshot missing/zero or stale source candidate; rotate/recover source before tuning.|
|watch_budget_reallocated|29|Watch budget eviction/reallocation observation, not submit failure.|
|pre_submit_quality_guard|23|Latency DANGER quality guard; stale/spread guard remains preserved.|
|source_freshness_recovering|9|Freshness recovery observation only.|
|intended_guard|5|Cooldown or other intended guard, not a defect.|
|runtime_backpressure|1|Full-eval loop budget deferred observation, not BUY submit failure.|

## Rising And Forced Scout Separation

- Rising row: KB금융(105560), max_delta=0.19%, latest_delta=0.00%, blocker=`scalping_scanner_watching_runtime_skip/scanner_fast_precheck_stability_pending`, class=`strategy_reject`, actual_submit=0.
- Rising missed residual excluding forced scout symbols: 000660, 002990, 010120, 025320, 034730, 281820, 319400.
- Forced scout event/symbol/residual counts are all 0, so no forced scout row can be counted as normal BUY/submit/fill success.

## Root Cause Closure

1. `scanner_strength_history_or_stale_eval` - closed as diagnostic false-positive for this window
   - Evidence before fix: one rising-missed symbol was incorrectly counted as repeated zero-strength source-quality workorder because `scalping_scanner_fast_precheck` rows with `fast_precheck_result=eligible_for_heavy_entry_eval` and relief reasons still carried `ws_strength_history_count=0`.
   - Fix: exclude eligible fast-precheck relief/progress rows from zero-strength workorder classification.
   - Evidence after regeneration: `rising_missed_repeated_zero_strength_history_workorder_count=0`; `scanner_strength_history_or_stale_eval` no longer appears in `root_cause_priorities`.
   - Remaining diagnostic-only signal: `rising_missed_low_ai_or_negative_pressure_stale_or_delayed_eval=224`, all `diagnostic_quote_age_stale`.
   - Forbidden uses preserved: BUY score relaxation, strength threshold relaxation, stale submit bypass, broker guard bypass.

2. `scale_in_blocked`
   - Evidence: blocked_count=2513, executed_count=0. Top reasons include `profit_not_enough=534`, `pnl_out_of_range(-0.61)=209`, `pnl_out_of_range(-1.64)=127`, `quote_stale=106`.
   - Decision: preserve scale-in safety and separate price guard, quantity guard, and window guard before any scale-in change.
   - Forbidden uses: scale-in guard bypass, quantity/cap release, hard safety relaxation, broker guard bypass.

3. `post_sell_missed_upside_or_bad_entry`
   - Evidence: bad_entry_after_sell_count=11, missed_upside_count=11.
   - Decision: exit/entry diagnostic only. No intraday exit threshold mutation or automatic exit deferral.
   - Next action: split stop-loss and take-profit flows after post-sell window matures.

## Operating Boundary

- No threshold, order, provider, bot, restart, cap, quantity, stale-submit, broker guard, or hard/protect/emergency safety change was performed.
- Temporary CSV output was generated only under `/tmp` and removed after each run.
- No timestamped intermediate md/csv flow snapshots were retained. The fixed current artifact is `data/report/intraday_entry_flow/intraday_entry_flow_2026-06-30_current.md`; this final stabilization file points to that current artifact as `source_flow_final`.

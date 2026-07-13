# Intraday Entry Flow Final Stabilization - 2026-07-13 08:00 to 19:00 KST

- source_flow_final: `data/report/intraday_entry_flow/intraday_entry_flow_2026-07-13_current.md`
- source_diagnostic: `data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-07-13.json`
- source_rising_missed_feedback: `data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-13.md`
- source_pyramid_feedback: `data/report/scalping_pyramid_intraday_feedback/scalping_pyramid_intraday_feedback_2026-07-13.md`
- source_buy_funnel_sentinel: `data/report/buy_funnel_sentinel/buy_funnel_sentinel_2026-07-13.md`
- generated_at: 2026-07-13T19:00:25+09:00
- decision_authority: source_only_final_stabilization_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false

## Decision

- 판정: `window_submit_drought_observation` 지속.
- 식별: 08:00~19:00 KST promoted/rising/BUY-candidate 접근 흐름은 유효한 source-only 진단으로 식별됐다.
- sim/source-only 적용: intraday diagnostics, fixed current flow, rising-missed feedback, pyramid feedback, BUY Funnel Sentinel의 source-only handoff 근거가 생성됐다.
- real runtime 반영: 미반영. 다음 PREOPEN `auto_bounded_live` 후보가 되려면 postclose workorder/LDM/bridge 산출물, source-quality exclusion, hard safety guard, stale quote/price freshness, broker/account/order/quantity/cooldown guard를 모두 통과해야 한다.

## Evidence

- normal BUY/submit/fill: diagnostics 기준 promoted_symbol_count=`672`, real_submit_symbol_count=`0`, actionable_major_blocker_count=`2`. flow 기준 buy_signal_or_pre_submit_pass_seen_symbols=`14`, real_submit_symbol_count_in_latest_diagnostic=`0`.
- rising missed: rising_missed_buy_count=`66`, rising_missed_one_share_eligible_symbol_count=`35`. class split은 `rising_missed_raw=33`, `runtime_backpressure_observation=18`, `source_quality_excluded=13`, `actionable_major_missed=2`.
- forced scout 분리: flow 기준 rising_missed_forced_scout_event_count=`5460`, symbol_count=`281`, residual_excluding_forced_scout_symbol_count=`8`. forced scout/one-share 결과는 일반 BUY submit 성공으로 세지 않는다.
- source freshness / delayed eval: stale_eval_symbol_count=`662`, rising_stale_eval_symbol_count=`156`, stale_refresh_recovered_symbol_count=`26`, rising_missed low-AI/negative-pressure stale_or_delayed_eval=`12`, unknown_eval_quality=`2`, diagnostic_quote_age_stale=`12`.
- submit-safety decomposition: stale quote with weak AI/strength events/symbols/records=`348/77/78`; latency danger events/symbols/records=`164/30/30`; latency causes=`spread_microstructure_wide=107`, `spread_too_wide=53`, `quote_stale=4`.
- runtime/backpressure: rising_missed full_eval_budget_deferred=`57` events / `22` symbols, suppressed_non_actionable_blocker_count=`4323`.
- source-quality exclusion: ai_not_evaluated excluded symbols=`045100,101730,067080,024060,003280,004090,086790,005830,205500,021240`; freshness recovery workorder_count=`4`; runtime attach identity mismatch workorder_count=`1`; repeated_zero_strength_history_workorder_count=`82`.
- rising-missed feedback: forced_rising_missed_record_count=`289`, submit_lineage_record_count=`8`, entry_submitted_count=`4`, submit_safety_block_count=`521`, backoff_recovered_eval_symbol_count=`175`, potential_backoff_opportunity_loss_count=`19`, code_improvement_order_count=`0`.
- one-share / pyramid opportunity: one_share_event_count=`293`, one_share_closed_count=`4`, one_share_pyramid_opportunity_count=`2`, one_share_pyramid_missed_upside_count=`1`, missed_upside_rate=`0.25`. This is opportunity-cost evidence only.
- official BUY Funnel Sentinel: as_of=`2026-07-13T15:20:02`, primary drought critical by `ai_confirmed=25`, `budget_pass=50`, `submitted=3`, `submitted/ai=12.0%`, and critical threshold `submitted/ai < 20.0%` with floor `ai>=20`.
- holding/exit: as_of=`2026-07-13T15:30:01`, exit_signal=`11`, sell_order_sent=`3`, sell_completed=`3`, real exit/sell_sent/sell_completed=`0/0/0`. Holding/exit evidence remains non-real/source-only for this goal.
- panic context: panic_sell=`RECOVERY_WATCH`, market_risk_state=`RISK_OFF`, panic_signal_count=`0`, allowed_runtime_apply=`false`; panic_buy=`NORMAL`, active_count=`0`, allowed_runtime_apply=`false`.

## Next Action

- postclose 자동 handoff: `rising_missed_intraday_feedback`, `rising_missed_scout_workorder`, `rising_missed_first_touch_calibration`, `one_share_threshold_opportunity`, `code_improvement_workorder`가 source-only/code-improvement 후보를 이어받는다.
- 우선순위: source freshness/history/AI provenance 결손, stale quote weak-AI 재평가 후보, latency DANGER spread/quote-stale 분해, full-eval deferred high-delta 후보, pre-submit entry AI authority guard를 postclose LDM/submit bucket/workorder로 분리한다.
- 금지 유지: intraday runtime threshold mutation, stale submit bypass, broker/account/order/quantity/cooldown guard bypass, hard/protect/emergency safety relaxation, provider route change, bot restart, cap release.
- real runtime 반영 조건: 다음 PREOPEN `auto_bounded_live` env 선택, bridge/live-auto contract closure, parsed Tier2/guard pass, source-quality exclusion or repair, post-apply attribution readiness.

## Artifact Cleanup

- Fixed current flow artifact retained: `data/report/intraday_entry_flow/intraday_entry_flow_2026-07-13_current.md`.
- Final stabilization retained: `data/report/intraday_entry_flow/intraday_entry_flow_2026-07-13_0800_to_1900_final_stabilization.md`.
- No timestamped same-day intraday flow md/csv snapshots are retained.
- Temporary CSV path `/tmp/intraday_entry_flow_2026-07-13_0800_to_1900.csv` was deleted after verification.
- `source_flow_final` points to the fixed current md, not a deleted timestamp snapshot.

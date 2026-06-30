# 2026-06-30 intraday entry flow final stabilization

- target_window: 2026-06-30T10:00:00 <= monitoring_loop <= 2026-06-30T11:00:00 KST
- source_event_window: 2026-06-30T08:00:00 <= event <= 2026-06-30T11:00:00 KST
- analysis_scope: general BUY bottleneck excludes sim/swing events and rising_missed forced one-share scout entries.
- excluded_for_general_buy: forced_entry_reason=rising_missed_one_share_entry, rising_missed_one_share_entry_forced=true with forced_entry_qty=1.
- diagnostic_artifact: data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-30_1100_goal.json
- flow_artifact: data/report/intraday_entry_flow/intraday_entry_flow_2026-06-30_0800_to_1100.md
- csv_artifact: data/report/intraday_entry_flow/intraday_entry_flow_2026-06-30_0800_to_1100.csv

## Decision

강제 1주 rising_missed scout는 일반 BUY 병목 분석에서 제외했다. 10:00~11:00 monitor loop 기준으로 일반 BUY 전 actionable major blocker는 최종 잔여 없음으로 판정한다.

10:20과 10:30에는 rising missed가 일시 재발했지만, 최신 병목은 scanner precheck가 아니라 `latency_block` pre-submit quality guard로 정정됐다. 10:40, 10:50, 11:00 루프에서는 `rising_missed_buy_count=0`으로 회복됐고, 일반 real-submit 종목은 21개까지 증가했다.

다만 submit 이후 체결 품질과 취소/가격 해결 품질은 별도 개선 대상이다. order price, cancel wait, threshold, broker/account/order/quantity/cooldown, stale quote, hard/protect/emergency guard는 변경하지 않았다.

## Evidence

- symbol_count: 41
- rising_symbol_count_by_max_delta: 19
- real_submit_symbol_count_in_latest_diagnostic: 21
- rising_missed_buy_count_in_latest_diagnostic: 0
- rising_missed_symbol_count_in_report: 0
- buy_signal_or_pre_submit_pass_seen_symbols: 22
- stale_eval_symbol_count: 22
- rising_stale_eval_symbol_count: 12
- rising_fresh_only_symbol_count: 7
- stale_refresh_recovered_symbol_count: 29

Loop summary:

- 10:00: promoted=26, real_submit=16, rising_missed=0, deferred_symbols=0, repeated_zero_history=0
- 10:20: promoted=37, real_submit=17, rising_missed=2, deferred_symbols=1, repeated_zero_history=0
- 10:30: promoted=38, real_submit=19, rising_missed=1, deferred_symbols=1, repeated_zero_history=0
- 10:40: promoted=40, real_submit=20, rising_missed=0, deferred_symbols=0, repeated_zero_history=0
- 10:50: promoted=40, real_submit=21, rising_missed=0, deferred_symbols=0, repeated_zero_history=0
- 11:00: promoted=41, real_submit=21, rising_missed=0, deferred_symbols=0, repeated_zero_history=0

Blocker rollup:

- 19: scalping_scanner_watching_runtime_skip / scanner_fast_precheck_stability_pending
- 16: latency_block / latency_state_danger
- 2: blocked_strength_momentum / below_buy_ratio
- 1: scalping_scanner_watching_runtime_skip / entry_cooldown_active
- 1: blocked_overbought / -
- 1: blocked_strength_momentum / below_strength_base

Blocker taxonomy:

- runtime_backpressure: 255
- strategy_reject: 147
- intended_guard: 58
- pre_submit_quality_guard: 35
- watch_budget_reallocated: 15
- source_freshness_blocker: 8
- source_freshness_recovering: 2

Execution-quality evidence:

- entry_price_execution block_or_unfilled_count: 48
- entry_price_execution candidate_failure_count: 13
- recent cancel rows now preserve submitted_price as submitted_order_price.
- scale_in_diagnostics blocked_count: 1629, executed_count: 1 within the 11:00 source window.
- 10:20/10:30 latency DANGER or slippage rows were treated as pre-submit quality guard evidence, not as scanner source-quality or full-eval budget failure.

## Next Action

- Do not use rising_missed forced one-share scout rows to justify BUY threshold relaxation, runtime approval, or bottleneck success/failure.
- Keep hard safety, cooldown, stale quote, broker, account, order, and quantity guards intact.
- Next concrete review target is entry price/cancel execution quality, not BUY threshold loosening.
- Because the updated goal ends at 2026-06-30T11:00:00 KST, stop 10-minute target-loop changes after the 11:00 artifact. Later events belong to a separate post-window observation.

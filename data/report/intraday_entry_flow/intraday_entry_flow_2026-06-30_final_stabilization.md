# 2026-06-30 intraday entry flow final stabilization

- target_window: 2026-06-30T08:00:00 <= event <= 2026-06-30T10:00:00 KST
- analysis_scope: general BUY bottleneck excludes sim/swing events and rising_missed forced one-share scout entries.
- excluded_for_general_buy: forced_entry_reason=rising_missed_one_share_entry, rising_missed_one_share_entry_forced=true with forced_entry_qty=1.
- diagnostic_artifact: data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-06-30_1000_goal.json
- flow_artifact: data/report/intraday_entry_flow/intraday_entry_flow_2026-06-30_0800_to_1000.md
- csv_artifact: data/report/intraday_entry_flow/intraday_entry_flow_2026-06-30_0800_to_1000.csv

## Decision

강제 1주 rising_missed scout는 일반 BUY 병목 분석에서 제외했다. 10:00 window 재산출 기준으로 상승 또는 BUY 후보 접근 후 일반 BUY가 전혀 없었다는 결론은 아니다. 일반 real-submit 종목은 16개이고, rising_missed general BUY count는 0개다.

다만 submit 이후 체결 품질과 취소/가격 해결 품질은 별도 개선 대상이다. 10:00 이후 이벤트는 본 목표 window에서 제외한다.

## Evidence

- symbol_count: 26
- rising_symbol_count_by_max_delta: 15
- real_submit_symbol_count_in_latest_diagnostic: 16
- rising_missed_buy_count_in_latest_diagnostic: 0
- rising_missed_symbol_count_in_report: 0
- buy_signal_or_pre_submit_pass_seen_symbols: 15
- stale_eval_symbol_count: 10
- rising_stale_eval_symbol_count: 9
- rising_fresh_only_symbol_count: 6
- stale_refresh_recovered_symbol_count: 14

Blocker rollup:

- 14: scalping_scanner_watching_runtime_skip / scanner_fast_precheck_stability_pending
- 9: scalping_scanner_watching_runtime_skip / entry_cooldown_active
- 2: blocked_strength_momentum / below_buy_ratio
- 1: blocked_strength_momentum / below_strength_base

Blocker taxonomy:

- runtime_backpressure: 254
- strategy_reject: 109
- intended_guard: 48
- watch_budget_reallocated: 9

Execution-quality evidence:

- entry_price_execution block_or_unfilled_count: 31
- entry_price_execution candidate_failure_count: 10
- recent cancel rows now preserve submitted_price as submitted_order_price.
- scale_in_diagnostics blocked_count: 997, executed_count: 0 within the 10:00 window.

## Next Action

- Do not use rising_missed forced one-share scout rows to justify BUY threshold relaxation, runtime approval, or bottleneck success/failure.
- Keep hard safety, cooldown, stale quote, broker, account, order, and quantity guards intact.
- Next concrete review target is entry price/cancel execution quality, not BUY threshold loosening.
- Any event after 2026-06-30T10:00:00 KST belongs to a separate post-window observation.

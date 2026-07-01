# 2026-07-01 09:50~12:00 KST intraday entry flow final stabilization

- generated_at: 2026-07-01T12:06:47+09:00
- source_flow_final: data/report/intraday_entry_flow/intraday_entry_flow_2026-07-01_current.md
- source_diagnostic_final: data/report/intraday_entry_blocker_diagnostics/intraday_entry_blocker_diagnostics_2026-07-01.json
- event_window: 2026-07-01T09:50:00 ~ 2026-07-01T11:56:44 KST
- monitor_until: 2026-07-01T12:00:00 KST
- monitor_stop_observed_at: 2026-07-01T12:06:47 KST
- decision_authority: diagnostic_and_code_improvement_workorder_only
- runtime_effect: false
- forbidden_uses: threshold_relaxation, stale_submit_bypass, broker_guard_bypass, forced_one_share_success_counting, real_execution_quality_approval

## Decision

09:50~12:00 KST 감시 구간에서 `rising_missed_one_share_entry` 강제 1주 scout는 일반 BUY 병목, normal submit, fill, holding 성공으로 집계하지 않는다. 최종 진단 기준 `rising_missed_one_share_eligible_symbol_count=0`이며, 강제 scout 잔여 관찰은 source-quality-only 성격이다.

정상 일반 BUY/submit은 `005690/파미셀` 1건만 확인됐다. 이 건은 `ai_confirmed -> entry_armed -> budget_pass -> latency_pass -> order_bundle_submitted`로 제출됐으나 `entry_timeout_or_reconcile`로 101주 취소 요청/확인됐고, 실제 fill/holding 성공으로 닫히지 않았다.

상승 미체결군 14건은 BUY/submit 완화 근거가 아니다. 분류는 `intended_guard_preserved=9`, `strategy_reject_missed=2`, `source_quality_excluded=2`, `runtime_backpressure_observation=1`이며, 우선 보완축은 source quality와 stale/freshness 회복이다.

## Evidence

- promoted_symbol_count: 78
- actionable_major_blocker_count: 288
- rising_symbol_count_by_max_delta: 14
- rising_missed_buy_count: 14
- rising_missed_one_share_eligible_symbol_count: 0
- real_submit_symbol_count: 1
- falling_real_submitted_count: 0
- buy_signal_or_pre_submit_pass_seen_symbols: 4
- rising_missed_forced_scout_event_count: 192
- rising_missed_forced_scout_symbol_count: 11
- rising_missed_residual_excluding_forced_scout_symbol_count: 4
- stale_eval_symbol_count: 27
- rising_stale_eval_symbol_count: 9
- stale_refresh_recovered_symbol_count: 42
- rising_missed_stale_or_delayed_eval: diagnostic_quote_age_stale=183, pre_ai_stale_or_history_gap=35, pre_submit_hard_stale=0, ws_quote_missing=0

## Source-quality workorders

1. `000390/매드업`: runtime attach identity mismatch 반복.
   - evidence: `runtime_attach_identity_mismatch.count=5`, `payload_name=매드업`, `db_name=SP삼화`, latest_reason=`scanner_identity_name_mismatch`, mismatch_expired=`True`
   - decision: source-quality excluded. 일반 BUY/submit 후보가 아니며, 코드/종목명 attach 정합성 보완 전 실주문 판단에 사용하지 않는다.
   - next_action: scanner promotion payload와 DB runtime target attach 이름/코드 정규화 경로를 점검하고, mismatch 만료 시 재조회 또는 workorder handoff를 명시한다.

2. `336260/두산퓨얼셀`: stale/history-gap 평가 품질 문제.
   - evidence: max_delta=3.50%, `diagnostic_quote_age_stale=9`, `pre_ai_stale_or_history_gap=6`, latest AI context WAIT/strength block
   - decision: source-quality excluded. score/strength 완화가 아니라 fresh 재평가와 strength history 회복을 먼저 닫는다.
   - next_action: WS strength/momentum history와 subscription recheck flow를 점검한다.

## Stale-heavy intended guard workorders

`intended_guard_preserved=9`는 가드 완화 대상이 아니라 stale 상태에서 가드가 주문을 막은 정상 보호 동작이다. 다만 상승 후 stale 평가가 반복된 종목은 fresh re-eval 보완 대상이다.

- `084370/유진테크`: diagnostic_quote_age_stale=37, pre_ai_stale_or_history_gap=16
- `006340/대원전선`: diagnostic_quote_age_stale=47, pre_ai_stale_or_history_gap=6
- `001260/남광토건`: diagnostic_quote_age_stale=17, pre_ai_stale_or_history_gap=1
- `045100/한양이엔지`: diagnostic_quote_age_stale=16, pre_ai_stale_or_history_gap=1, max_delta=10.26%
- `010120/LS ELECTRIC`: diagnostic_quote_age_stale=11
- `006360/GS건설`: diagnostic_quote_age_stale=21
- `037350/성도이엔지`: diagnostic_quote_age_stale=11, pre_ai_stale_or_history_gap=3
- `062040/산일전기`: diagnostic_quote_age_stale=6, pre_ai_stale_or_history_gap=2

Required repair direction:

- keep `pre_submit_hard_stale` and broker/quote guards intact
- do not convert stale observations into BUY threshold relaxation
- add or tune fresh re-eval enqueue for rising candidates after stale/history gap
- inspect WS snapshot, quote age, strength/momentum history, and scanner watch eviction recovery before any strategy threshold change
- keep any budget increase bounded; `scanner_full_eval_budget_diagnostics` remains diagnostic-only

## Normal submit / fill / holding separation

`005690/파미셀` is the only normal submit symbol in the window.

- order path: `ai_confirmed` at 10:30:05, `entry_armed` at 10:30:05, `budget_pass` at 10:30:06, `latency_pass` at 10:30:11, `order_bundle_submitted` at 10:30:15
- order_no: 0034472
- submitted_order_price: 14160
- quantity observed before submit: 101
- cancellation: `entry_order_cancel_requested` and `entry_order_cancel_confirmed` at 10:32:01, reason `entry_timeout_or_reconcile`
- fill/holding decision: no real fill/holding success was confirmed. Later holding-like rows are sim/provenance rows with `actual_order_submitted=false` and `broker_order_forbidden=true`.

## Final next action

1. Prioritize source-quality repair for runtime attach identity mismatch and stale/history-gap evaluation before any BUY/submit tuning.
2. Add a bounded freshness recovery workorder for rising candidates with repeated `diagnostic_quote_age_stale` or `pre_ai_stale_or_history_gap`.
3. Review 파미셀 entry timeout attribution under entry cancel wait diagnostics, but do not relax order price, stale submit, or broker guards from this single cancelled submit.

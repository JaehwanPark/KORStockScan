# 부속문서: 2026-04-21 Plan Rebase 실행 로그 및 상세 근거

작성일: `2026-04-21`  
실행 시점: `2026-04-21 INTRADAY 10:40~11:50 KST (정렬)` + `POSTCLOSE 15:20~16:35 KST (확정)` + `2026-04-22 PREOPEN 08:00~08:10 KST (canary 적용)`  
대상: 운영 트레이더 / Codex / 감사인 검토  
현재 중심 문서: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)  
기준 보조 문서: [plan-korStockScanPerformanceOptimization.performance-report.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.performance-report.md), [2026-04-21-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-21-stage2-todo-checklist.md)

> 역할 고정: 이 문서는 Plan Rebase의 실행 로그, 상세 근거, 과거 체크리스트를 보존하는 부속문서다. 현재 튜닝 원칙, 판정축, pain point별 실행과제, 일정, 기대효과/실제효과의 중심 기준은 `plan-korStockScanPerformanceOptimization.rebase.md`를 우선한다.

---

## 0. 용어 범례

| 표현 | 한글 설명 | 현재 처리 |
| --- | --- | --- |
| `fallback` | 정상 진입이 막힌 상황에서 보조 주문 경로로 진입을 시도하던 예외 경로 | Plan Rebase에서 폐기 유지 |
| `fallback_scout/main` | `fallback_scout` 탐색 주문과 `fallback_main` 본 주문이 함께 나가던 2-leg fallback 분할진입 | 영구 폐기, 재개/승격/canary 대상 아님 |
| `fallback_single` | scout/main으로 나뉘지 않은 단일 fallback 진입 경로 | 영구 폐기, 재개/승격/canary 대상 아님 |
| `latency fallback split-entry` | latency 상태가 `CAUTION/DANGER`일 때 fallback 허용으로 분할진입을 시도하던 경로 | 영구 폐기, latency bugfix와 분리 |
| `main-only` | `songstock`/remote 비교를 제외하고 메인서버 실전 로그만 기준으로 보는 방식 | 현재 기준선 |
| `normal_only` | fallback 태그와 예외 진입이 섞이지 않은 정상 진입 표본 | 손익/성과 비교의 우선 기준 |
| `post_fallback_deprecation` | `2026-04-21 09:45 KST` fallback 폐기 이후 새로 쌓인 표본 | 폐기 이후 효과 확인 기준 |
| `canary` | 작은 범위로 실전에 적용해 성과와 리스크를 검증하는 1축 변경 | 하루 1축만 허용 |
| `shadow` | 실전 주문에는 반영하지 않고 병렬 계산만 하던 검증 방식 | 신규/보완축에서는 금지 |

## 1. 판정

기존 튜닝 plan은 `2026-04-21 09:45 KST` 이후 그대로 진행하지 않는다.  
`fallback_scout/main`(탐색 주문/본 주문 동시 fallback 분할진입) 폐기와 불타기 수익 확대 관찰로 인해, 현재 단계는 `파라미터 튜닝`이 아니라 `로직 전수점검 + 관찰축 재정렬 + 튜닝포인트 재선정`이다.

`songstock` 원격서버는 더 이상 운영 비교대상이 아니다. 본 문서의 모든 판정과 후속 액션은 `main-only baseline`(메인서버 단독 기준선) 기준으로만 내린다.

---

## 2. 개편 사유

1. `fallback_scout/main`은 탐색형 분할진입이 아니라 동시 2-leg 주문이었고, `partial/rebase/soft_stop`(부분체결/기준가 재조정/소프트스탑) 손실축을 오염시켰다.
2. 오늘 수익 확대는 손실 억제형 분할진입이 아니라 `불타기/추가진입` 쪽 기대값 개선 가능성을 보여줬다.
3. 물타기, 불타기, 분할진입은 별도 튜닝축이 아니라 하나의 `포지션 증감 상태머신`으로 설계해야 한다.
4. 감사인이 의견을 주려면 `진입/보유/청산` 로직의 현재 동작과 관찰축이 먼저 정리되어야 한다.
5. `songstock` 비교축은 `remote_error`와 운영 폐기 상태가 겹쳐 더 이상 의사결정 품질을 높이지 못한다. 현재 병목은 `서버 간 차이`가 아니라 `메인서버 Gemini BUY 신호 급감 -> 진입 표본 부족 -> 튜닝 지연`이다.

---

## 3. 전수점검 범위

### 3-1. 진입 로직

- 정상 진입: `SAFE -> ALLOW_NORMAL -> tag=normal`
- 폐기 경로: `CAUTION/DANGER override -> ALLOW_FALLBACK`, `fallback_scout/main`(탐색/본 주문 동시 fallback), `fallback_single`(단일 fallback)
- blocker: `latency`, `liquidity`, `AI threshold`, `overbought`
- 관찰축: `entry_mode`, `order_tag`, `latency_state`, `decision`, `blocked_stage`, `submitted_qty`, `filled_qty`

### 3-2. 보유 로직

- `HOLDING` 판단: AI score, peak profit, elapsed time, near-exit, never-green
- 추가진입 후보: 불타기, 물타기, 추가진입 중단
- 관찰축: `MISSED_UPSIDE`, `GOOD_EXIT`, `capture_efficiency`, `peak_profit`, `time_to_exit`, `add_position_candidate`

### 3-3. 청산 로직

- soft stop, hard stop, AI early exit, preset exit, overnight gatekeeper
- NXT 가능/불가능 종목의 EOD 판단 분리 필요
- 관찰축: `exit_rule`, `profit_rate`, `hold_sec`, `sell_order_status`, `sell_fail_reason`, `is_nxt`

---

## 4. 코호트 재정렬

기존 통합 집계는 아래 코호트로 재분리한 뒤에만 해석한다.

1. `normal_only`: `entry_mode=normal`, `tag=normal`, `SAFE -> ALLOW_NORMAL`
2. `fallback_scout_main_contaminated`: `fallback_scout` 또는 `fallback_main` 포함
3. `fallback_single_contaminated`: `fallback_single` 포함
4. `post_fallback_deprecation`: `2026-04-21 09:45 KST` 이후 신규 표본
5. `scale_in_profit_expansion`: 불타기/추가진입으로 수익이 확대된 표본
6. `avg_down_candidate`: 물타기 후보였으나 실행되지 않은 표본

---

## 5. 튜닝 중단/재개 규칙

1. 신규 live canary는 `진입/보유/청산` 로직표와 `normal_only/fallback 오염` 코호트 분리가 끝나기 전까지 금지한다.
2. `fallback_scout/main`(탐색/본 주문 동시 fallback)과 `fallback_single`(단일 fallback)은 영구 폐기한다. 재개/승격/재평가 canary 대상이 아니다.
3. 기존 `partial/rebase/soft_stop` 통합 지표는 fallback 오염 제거 후 재집계하기 전까지 승격/롤백 판단에 사용하지 않는다.
4. 다음 튜닝포인트는 감사인 정의의 `entry_filter_quality`를 1순위 후보로 두고, 장후 코호트 데이터로 최종 확인한다.
5. `holding_exit`, `position_addition_policy`, `EOD/NXT`는 후순위 후보로 유지한다. 특히 보유 AI `position_context` 입력은 더 빠른 `holding_exit` 축에서 별도 1축으로 먼저 설계하고, 물타기/불타기/분할진입은 그 결과를 소비하는 `position_addition_policy` 상태머신으로 재설계한다.
6. shadow/counterfactual 선행 원칙은 철회한다. 다음 1축은 `canary 즉시 적용 + 당일 rollback guard`로 설계한다.
7. canary는 한 번에 한 축만 적용한다. rollback guard는 `N_min`, `reject_rate`, `loss_cap`, `latency_p95`, `partial_fill_ratio`를 문서와 로그에 고정한다.
8. AI 엔진 A/B 테스트는 감사인 정의의 `entry_filter_quality` canary 1차 판정 완료 후 재개 여부를 별도 판정한다. 최대 기한은 `2026-04-24 POSTCLOSE`다.
9. Plan Rebase 기간의 live 스캘핑 AI 라우팅은 Gemini로 고정하고, OpenAI 스캘핑 라우팅 및 dual-persona shadow는 `entry_filter_quality` canary 1차 판정 완료 후 재개 여부를 별도 판정하기 전까지 비활성화한다.
10. `songstock` 원격서버 비교, 원격 canary, 서버 간 승격/보류 판정은 현재 Plan Rebase 범위에서 제외한다. baseline은 `normal_only`, `post_fallback_deprecation`, `main-only missed_entry_counterfactual`로만 고정한다.

---

## 6. Main-only Gemini BUY 정상화

### 6-1. 판정

현재 메인 병목은 `손실 억제 실패`보다 먼저 `Gemini 전환 후 BUY 신호 급감으로 인한 표본 고갈`이다.  
이 상태가 지속되면 `진입 후 체결품질`, `보유`, `청산` 튜닝이 모두 저표본으로 묶여 기대값 개선 속도가 급격히 느려진다.

### 6-2. 근거

1. `2026-04-21 11:35:51 KST` 기준 main-only `missed_entry_counterfactual`은 `total_candidates=115`, `missed_winner_rate=76.5%`, `estimated_counterfactual_pnl_10m_krw_sum=647,365원`이다.
2. 같은 시각 terminal 기준 `latency guard miss=97/115(84.3%)`가 1차 축이지만, `blocked_ai_score` event overlap도 `233건`으로 적지 않다. 즉 `BUY 자체 감소`와 `BUY 후 주문전 차단`이 동시에 병목이다.
3. 메인 히스토리 기준 `WAIT 65` 군집은 이미 반복 관찰됐다. `2026-04-09~2026-04-13` 3일 집계에서 `WAIT 65=286건`, 그중 `missed_entry_counterfactual`에 연결된 `85건` 중 `MISSED_WINNER=62`였다.
4. 따라서 지금 필요한 것은 추가 비교대상 탐색이 아니라, 메인서버 내에서 `Gemini WAIT 과밀 구간을 BUY 회복형으로 정상화`하는 1축 canary다.

### 6-3. 해결방안

1. 감사인 정의의 `entry_filter_quality` 1순위는 유지한다.  
   다만 오늘 긴급 적용한 실전 축은 그와 별개인 `main-only buy_recovery_canary`다. `더 많이 거르기`가 아니라 `Gemini WAIT 과밀 구간의 BUY 회복`만 다룬다.
2. 진입 1차 결과가 `WAIT`이고 score가 `65~79`인 구간만 재평가한다. 전면 threshold 완화는 금지한다.
3. 재평가 대상은 아래 조건을 동시에 만족하는 표본으로만 제한한다.
   - `latency_state != DANGER`
   - `blocked_liquidity=0`
   - `blocked_overbought=0`
   - `buy_pressure_10t >= 65`
   - `tick_acceleration_ratio >= 1.20`
   - `curr_vs_micro_vwap_bp >= 0`
   - `large_sell_print_detected=False`
4. 위 표본에 한해 Gemini 2차 판정을 호출한다. 구현은 기존 `SCALPING_SYSTEM_PROMPT_75_CANARY` 경로를 재사용하되, 기존 `75~79 shadow-only`가 아니라 `65~79 WAIT` 구간의 `buy_recovery_canary`로 재정의한다.
5. 2차 판정이 `BUY`이고 score가 `>= 75`이면 진입 후보로 승격한다. 단, `full fill`과 `partial fill`은 손익 표본을 합치지 않고 분리한다.
6. 평가 지표는 손익 단독이 아니라 아래 순서로 본다.
   - `ai_confirmed_buy_count`, `ai_confirmed_buy_share`
   - `WAIT 65/70/75~79` 분포
   - `blocked_ai_score` 비중
   - `ai_confirmed -> entry_armed -> order_bundle_submitted`
   - `BUY 후 미진입 4축`
   - `full fill / partial fill`
   - `COMPLETED + valid profit_rate`

### 6-4. 실행 원칙

1. 이번 축은 `main-only`다. `songstock`, remote shadow, 서버 비교 리포트는 기준에서 제외한다.
2. canary는 한 번에 한 축만 적용한다. `BUY 회복형 normalization` 외 다른 완화는 같은 날 같이 태우지 않는다.
3. `WAIT 65` 과밀이 재현되지 않거나 `65~79` 표본이 0에 가깝다면, 임계값을 더 낮추지 말고 먼저 `score histogram`, `reason`, `blocked_ai_score`, `prompt_profile` 정합성을 재검증한다.

### 6-5. 즉시 반영된 계측/판정 축 (`2026-04-21 13:37 KST`)

1. `WAIT 65~79` 전용 EV 코호트를 별도 고정수집한다.
   - 수집행 필드: `buy_pressure`, `tick_accel`, `micro_vwap_bp`, `latency_state`, `parse_ok`, `ai_response_ms`, `terminal_blocker`
   - 구현: `ENTRY_PIPELINE stage=wait65_79_ev_candidate` + 장후 스냅샷 `wait6579_ev_cohort`
2. `WAIT 65~79` 표본은 paper-fill(가상체결) 시뮬레이션을 함께 계산한다.
   - 산출: `expected_fill_rate_pct`, `full_fill_prob`, `partial_fill_prob`, `expected_ev_pct`, `expected_ev_krw`
   - 목적: `들어갔으면 체결됐는지`와 `체결됐을 때 EV 방향`을 동시 판정
3. 임계값 하향 승인은 `full/partial` 분리 표본 최소 N을 먼저 통과해야 한다.
   - gate: `AI_WAIT6579_EV_MIN_FULL_SAMPLES` / `AI_WAIT6579_EV_MIN_PARTIAL_SAMPLES` (기본 `20/20`)
   - 승인 조건: `min_sample_gate_passed=True` 이후에만 EV 방향성(`ev_directional_check_passed`)을 확인한다.
4. `WAIT 65~79`에서 `BUY`로 승격된 표본은 소량 실전 probe canary를 강제한다.
   - 조건: `buy_recovery_canary promoted=true` + `SCALPING`
   - 실행: `AI_WAIT6579_PROBE_CANARY_MAX_BUDGET_KRW` / `AI_WAIT6579_PROBE_CANARY_MIN_QTY` / `AI_WAIT6579_PROBE_CANARY_MAX_QTY`
   - 로그: `wait6579_probe_canary_applied`, `order_bundle_submitted.wait6579_probe_canary_applied`
5. Gemini 라우팅 전환 시점에 누락된 OpenAI v2 입력 피처 parity를 복구한다.
   - 조치: `ai_engine.py`에 `_extract_scalping_features`를 추가해 `extract_scalping_feature_packet`을 직접 반환한다.
   - 조치: `[정량형 수급 피처]` 블록에 `spread/top-depth/microprice_edge/price_change_10t/recent_5tick_seconds/prev_5tick_seconds/large_buy_print/volume_ratio/curr_vs_micro_vwap_bp/curr_vs_ma5_bp`를 확장 반영한다.
   - 기대효과: `WAIT65~79` probe의 0값 고정 리스크를 제거해 `buy_recovery_canary` 승격 후보 표본 복구.
6. Gemini analyze 경로에 프롬프트 프로파일/액션 스키마를 OpenAI v2 수준으로 이식한다.
   - 조치: `prompt_profile=watching/holding/exit/shared` 전부 분기 반영(`scalping_entry/scalping_holding/scalping_exit/scalping_shared`).
   - 조치: 보유/청산 액션은 `HOLD/TRIM/EXIT`(`action_v2`)로 분리하고, 기존 핸들러 호환을 위해 `action` legacy 매핑(`HOLD->WAIT`, `TRIM->SELL`, `EXIT->DROP`)을 동시 제공한다.
   - 기대효과: 프로파일 누락으로 인한 판정 혼선 제거 + 단계별 액션 귀속 명확화.

---

## 7. 실행 체크리스트

- [x] `[PlanRebase0421] fallback 관련 축 영구 폐기 + 신규 축 canary 전환 선언` (`Due: 2026-04-21`, `Slot: INTRADAY`, `TimeWindow: 10:40~10:50`, `Track: Plan`) (`실행: 2026-04-21 11:44 KST`)
  - 판정 기준: `fallback_scout/main`, `fallback_single`, split-entry leakage/재평가 항목을 폐기로 닫고, 다음 신규 1축은 canary + rollback guard로 전환한다고 선언한다.
  - 판정: 완료. fallback 관련 축은 영구 폐기하고 신규 canary는 감사인 정의의 `entry_filter_quality` 1축으로만 유지한다.
  - 검증: `09:45 KST` 이후 live 로그 기준 `fallback_bundle_ready=0`, `ALLOW_FALLBACK=0`.
- [x] `[PlanRebase0421] AI 엔진 A/B 보류 + Gemini 라우팅 고정` (`Due: 2026-04-21`, `Slot: INTRADAY`, `TimeWindow: 10:55~11:05`, `Track: AIPrompt`) (`실행: 2026-04-21 11:44 KST`)
  - 판정 기준: `KORSTOCKSCAN_SCALPING_AI_ROUTE` 기본값이 `gemini`이고, live 스캘핑 라우터 로그가 `scalping_route=gemini`, `main_scalping_openai=OFF`로 확인된다. `OPENAI_DUAL_PERSONA_ENABLED=False`로 dual-persona shadow도 비활성화한다.
  - 판정: 완료. 스캘핑 기본 route는 Gemini로 고정하고 OpenAI/Gemini A/B 및 dual-persona shadow는 `entry_filter_quality` canary 1차 판정 이후로 보류한다.
  - 검증: `src/tests/test_runtime_ai_router.py` 포함 5개 관련 테스트 묶음 `25 passed`.
- [x] `[PlanRebase0421] 진입/보유/청산 로직표 확정` (`Due: 2026-04-21`, `Slot: INTRADAY`, `TimeWindow: 10:50~11:30`, `Track: ScalpingLogic`) (`실행: 2026-04-21 11:44 KST`)
  - 판정 기준: 기존 §3 표를 검증·보완해 정상 진입, 폐기 fallback, blocker 4축, HOLDING, 추가진입 후보, soft/hard/AI/preset/EOD/NXT 청산 경로를 한 표로 확정한다.
  - 판정: 완료. §3 로직표를 확정하고 `진입/보유/청산`별 관찰필드와 폐기경로를 분리했다.
- [x] `[PlanRebase0421] fallback 오염 코호트 재집계` (`Due: 2026-04-21`, `Slot: INTRADAY`, `TimeWindow: 11:30~11:50`, `Track: Plan`) (`실행: 2026-04-21 11:44 KST`)
  - 판정 기준: `normal_only`, `fallback_scout_main_contaminated`, `fallback_single_contaminated`, `post_fallback_deprecation`, `scale_in_profit_expansion`, `avg_down_candidate` 코호트를 분리한다. `fallback_single`은 `symbol + timestamp`로 HOLDING/청산 합산 오염 여부를 교차검증한다.
  - 판정: 완료. `COMPLETED + valid profit_rate`만 사용해 normal/fallback/post-deprecation 코호트를 분리했다.
- [x] `[PlanRebase0421] 다음 튜닝포인트 1축 재선정` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 15:20~15:40`, `Track: Plan`) (`실행: 2026-04-21 12:18 KST`)
  - 판정 기준: 감사인 권고에 따라 다음 정식 1순위 후보는 `entry_filter_quality`로 고정한다. 단, 오늘 긴급 적용한 실전 조치는 별도 `buy_recovery_canary`로 분리 기록한다. `holding_exit`, `position_addition_policy`, `EOD/NXT`는 후순위로 기록한다. 코호트 데이터가 반대 근거를 보이면 사유를 명시한다.
  - 판정: 완료. 문서상 정식 1순위 축은 `entry_filter_quality`로 복원했고, 이미 반영된 실전 변경은 `main-only buy_recovery_canary`로 분리했다.
- [x] `[PlanRebase0421] buy_recovery_canary 설계 + rollback guard 고정` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 15:40~16:10`, `Track: ScalpingLogic`) (`실행: 2026-04-21 12:18 KST`)
  - 판정 기준: `main-only buy_recovery_canary` 규칙(`WAIT 65~79 2차 재평가`, feature allowlist, `SCALPING_SYSTEM_PROMPT_75_CANARY` 재사용)과 `N_min`, `reject_rate`, `loss_cap`, `latency_p95`, `partial_fill_ratio` guard를 함께 고정하고 04-22 장전 적용 가능 여부를 결정한다.
  - 판정: 완료. `buy_recovery_canary` 규칙을 코드에 반영했고 runtime 반영까지 끝냈다.
  - 검증: `py_compile` 통과, `pytest` `21 passed`, `src/bot_main.py` 재기동(PID 갱신) 확인.
- [x] `[AIPrompt0421] WAIT65_79 EV 코호트 + paper-fill + full/partial N gate 반영` (`Due: 2026-04-21`, `Slot: INTRADAY`, `TimeWindow: 13:00~13:20`, `Track: AIPrompt`) (`실행: 2026-04-21 13:37 KST`)
  - 판정 기준: `wait65_79_ev_candidate` 수집 필드 고정, `wait6579_ev_cohort` 스냅샷 생성, `paper-fill` 기대 체결/EV 산출, `full/partial` 최소 N gate, `소량 실전 probe canary`를 코드/리포트에 반영한다.
  - 판정: 완료. 코드베이스와 스냅샷 파이프라인에 동시 반영했다.
  - 검증: `src/tests/test_wait6579_ev_cohort_report.py`, `src/tests/test_log_archive_service.py`, `src/tests/test_state_handler_fast_signatures.py` 묶음 `16 passed`.
- [x] `[MainOnly0421] songstock 비교축 종료 + main-only baseline 고정` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:10~16:20`, `Track: Plan`) (`실행: 2026-04-21 15:24 KST, 사전 실행`)
  - 판정 기준: 서버 비교, 원격 canary, remote_error 해석을 현재 의사결정 입력에서 제거하고 `normal_only`, `post_fallback_deprecation`, `main-only missed_entry_counterfactual`만 기준으로 남긴다.
- [x] `[PlanRebase0421] 용어 분리 잠금(entry_filter_quality vs buy_recovery_canary)` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:20~16:30`, `Track: Plan`) (`실행: 2026-04-21 15:24 KST, 사전 실행`)
  - 판정 기준: 감사인 문맥의 `entry_filter_quality=불량 진입 감소/진입 품질 개선`과 오늘 실전 적용한 `buy_recovery_canary=Gemini WAIT 65~79 BUY 회복`을 문서/리포트/체크리스트에서 혼용하지 않도록 고정한다.
- [x] `[AIPrompt0421] Gemini BUY drought main-only 계량` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:20~16:35`, `Track: AIPrompt`) (`실행: 2026-04-21 15:24 KST, 15:23 스냅샷 기준`)
  - 판정 기준: 메인 로그 기준 `ai_confirmed_buy_count/share`, `WAIT 65/70/75~79` 분포, `blocked_ai_score`, `buy_after_recheck_candidate`, `missed_winner_rate`를 같은 표로 잠근다.
- [x] `[PlanRebase0421] 감사인 전달용 개편 요약 작성` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:10~16:30`, `Track: Plan`) (`실행: 2026-04-21 22:20 KST`)
  - 판정 기준: 감사인이 의견을 줄 수 있도록 `현재 로직표`, `오염 제거 기준`, `entry_filter_quality` 정의, `main-only buy_recovery_canary`, `rollback guard`를 한 페이지로 요약한다.
  - 판정: 완료. §11에 현재 리베이스 플랜의 코드/문서 반영 검증 요약을 추가했다.
  - 검증: `fallback` 폐기, Gemini 라우팅 고정, `buy_recovery_canary`, WAIT65~79 EV 코호트, Gemini 프롬프트/액션 스키마 분리는 코드와 테스트로 확인했다. 단, 보유 AI 포지션 컨텍스트 직접 전달은 현 리베이스 즉시축 범위 밖 미완으로 별도 후순위 보완 대상이다.
- [x] `[PlanRebase0422] buy_recovery_canary 장전 적용` (`Due: 2026-04-22`, `Slot: PREOPEN`, `TimeWindow: 08:00~08:10`, `Track: ScalpingLogic`) (`실행: 2026-04-21 12:18 KST, 조기적용`)
  - 판정 기준: 04-21 장후 확정된 `main-only buy_recovery_canary`와 guard를 확인하고 canary ON 여부를 결정한다. 적용 시 같은 날 rollback 판정 시각을 문서에 남긴다.
  - 판정: 완료(조기적용). 장전 예정 항목을 장중 긴급 적용으로 앞당겼다.
- [ ] `[HoldingCtx0422] 보유 AI position_context 입력 1축 설계` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 15:40~15:50`, `Track: AIPrompt`)
  - 판정 기준: `holding_exit` 축에서 `profit_rate`, `peak_profit`, `drawdown_from_peak`, `held_sec`, `buy_price`, `position_size_ratio`, `position_tag`를 Gemini 보유 프롬프트 입력으로 직접 전달하는 `position_context` 스키마를 확정한다.
  - 실행 원칙: 04-22에는 live 완화/추가진입과 묶지 않고 설계/테스트/로그 필드 고정까지만 1축으로 처리한다. 검증은 shadow/counterfactual 없이 별도 `holding_exit position_context canary` 1축으로만 수행한다.
  - canary 조건: live 적용 여부는 `HOLDING` 성과판정과 `buy_recovery_canary` 1일차 판정 이후 별도 결정한다. canary를 열 경우 같은 날 다른 보유/청산 완화축과 병행하지 않고, `N_min`, `loss_cap`, `missed_upside_rate`, `GOOD_EXIT`, `capture_efficiency`, `forced_exit/early_exit` rollback guard를 문서와 로그에 고정한다.
  - 후속 연결: `position_addition_policy`는 이 `position_context`를 전제로 불타기/물타기/추가진입 중단 상태머신을 설계한다.
- [ ] `[PlanRebase0422] position_addition_policy 후순위 설계 초안` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~17:00`, `Track: ScalpingLogic`)
  - 판정 기준: 불타기/물타기/추가진입 중단 상태머신 초안을 작성하되, `entry_filter_quality` canary 결과와 충돌하지 않게 후순위 후보로 유지한다. `HoldingCtx0422`에서 확정한 `position_context` 스키마가 있으면 이를 입력 전제로 사용하고, 미확정이면 상태머신 설계를 live 적용 없이 보류한다.
- [ ] `[AIPrompt0422] Gemini BUY recovery canary 1일차 판정` (`Due: 2026-04-22`, `Slot: INTRADAY`, `TimeWindow: 12:00~12:20`, `Track: AIPrompt`)
  - 판정 기준: `2026-04-22` 오전 구간까지만 표본을 수집하고, `12:00` 이후 생성된 스냅샷 시점을 판정 고정 시점으로 사용한다. `ai_confirmed_buy_count/share`, `WAIT 65/70/75~79`, `blocked_ai_score`, `ai_confirmed -> submitted`, `missed_winner_rate`, `full fill / partial fill`을 main-only로 판정하고 다음 축 유지/롤백을 기록한다.
- [ ] `[AIPrompt0422] 프로파일별 특화 프롬프트 1축 canary go/no-go 최종판정` (`Due: 2026-04-22`, `Slot: INTRADAY`, `TimeWindow: 12:20~12:30`, `Track: AIPrompt`)
  - 판정 기준: `09:00~12:00` 오전 반나절 관찰과 `12:00~12:20` 고정 스냅샷으로 `watching 특화`, `holding 특화`, `exit 특화`, `shared 제거`, `전부 미착수` 중 하나를 확정한다. 추가 관찰 유예는 금지한다.
  - shared 규칙: 오전 중 `ai_prompt_type=scalping_shared`가 주문 제출, latency/budget gate, holding review, exit decision 중 하나에 연결되면 `shared 제거`를 live canary 후보로 올린다. 관측되지 않으면 live canary 후보에서 제외하고 코드정리 또는 현행 유지로 닫는다.
- [ ] `[AIPrompt0424] AI 엔진 A/B 재개 여부 판정` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:20`, `Track: AIPrompt`)
  - 판정 기준: `entry_filter_quality` canary 1차 판정이 완료됐으면 A/B 재개 여부를 결정한다. 3영업일 내 판정이 불충분하면 A/B 재개/추가보류를 별도 사유와 함께 기록한다.

---

## 8. buy_recovery_canary 정식 rollback guard

04-22 PREOPEN canary 적용 전 아래 guard를 문서와 운영 로그에 고정한다. 손익은 `COMPLETED + valid profit_rate`만 사용하며, 모든 증가/감소 방향을 명시해 부호 혼동을 제거한다.

| Guard 지표 | 발동 조건 | 기준 | 발동 시 조치 |
| --- | --- | --- | --- |
| `N_min` | 판정 시점 `trade_count < 50`이고 `submitted_orders < 20` | 절대값 | hard pass/fail 금지, 방향성 판정으로 전환, 승격 금지 |
| `loss_cap` | canary cohort의 일간 합산 실현손익이 당일 스캘핑 배정 NAV 대비 `<= -0.35%` | 당일 NAV 대비 일간 합산, 종목별 아님 | canary OFF + 전일 설정 복귀 + 원인 코호트 기록 |
| `reject_rate` | canary 적용 후 `entry_reject_rate`가 `normal_only` baseline 대비 `+15.0%p` 이상 증가 | `normal_only` baseline | canary OFF. blocker 품질 개선 여부는 사후 분석으로만 기록 |
| `latency_p95` | canary 적용 후 `gatekeeper_eval_ms_p95 > 15,900ms` | 절대값, `gatekeeper_eval_samples >= 50` | canary OFF + latency 경로 재점검 |
| `partial_fill_ratio` | baseline 대비 `+10.0%p` 이상 증가 | `normal_only` baseline | 단독 rollback은 하지 않고 경고로 기록. 동시에 `loss_cap` 또는 `soft_stop_count/completed_trades >= 35.0%`이면 canary OFF |
| `fallback_regression` | `fallback_scout/main` 또는 `fallback_single` 신규 1건 이상 발생 | 절대값 0건 | 즉시 canary OFF + fallback 차단 회귀 조사 |
| `buy_drought_persist` | canary 적용 후에도 `ai_confirmed_buy_count`가 main baseline 하위 3분위수보다 낮고 `blocked_ai_score_share`가 개선되지 않음 | main-only 최근 3거래일 baseline | canary 유지 금지. prompt/score histogram 재교정으로 되돌리고 2차 완화 금지 |

부호 규칙: `reject_rate`, `partial_fill_ratio`, `latency_p95`는 증가가 위험 방향이다. 음수 %p 표기는 사용하지 않는다.

## 9. 감사인 의견 반영 및 문의

- 반영: R-1 shadow/counterfactual 선행 원칙을 철회하고 `canary 즉시 적용 + rollback guard` 원칙으로 변경한다.
- 반영: R-2 split-entry 재평가/leakage, 에이럭스 별도 4분해, legacy shadow 2건, 범위확정 실패 분리항목은 체크리스트에서 제거하거나 상위 항목에 흡수한다.
- 반영: R-3 일정은 04-21 장후 `15:20~16:10`에 1축 선정과 canary guard 설계까지 끝내고, 04-22 PREOPEN에 canary 적용 판단을 하도록 압축한다.
- 반영: R-4 다음 튜닝 1순위는 `position_addition_policy`가 아니라 감사인 정의의 `entry_filter_quality`로 유지한다.
- 반영: 오늘 장중 긴급 적용한 실전 조치는 감사인 정의의 `entry_filter_quality`와 별개인 `buy_recovery_canary`로 분리한다.
- 반영: 재검토 시정 A에 따라 AI 엔진 A/B 재개 여부는 `entry_filter_quality` canary 1차 판정 완료 후, 늦어도 `2026-04-24 POSTCLOSE`에 별도 판정한다.
- 반영: 재검토 시정 B에 따라 rollback guard를 §8 정식 표로 승격하고 발동 조건/기준/방향/조치를 고정했다.
- 반영: 재검토 시정 C에 따라 guard 수치가 정의된 뒤 감사인 Q5를 재질의하는 구조로 정리한다.

## 10. INTRADAY 실행 결과

기준 스냅샷은 `trade_review=2026-04-21 11:35:07`, `performance_tuning=2026-04-21 11:35:35`, `missed_entry_counterfactual=2026-04-21 11:35:51`이다. 현재 시각 기준 `12:30~13:00` 장중 잠금 항목은 TimeWindow 전이라 사전 산출만 기록하고 체크박스는 열어둔다.

### 10-1. 코호트 재집계

| 코호트 | 표본 | 평균 profit_rate | 실현손익 | 판정 |
| --- | ---: | ---: | ---: | --- |
| `normal_only` | 6 | `-0.670%` | `-23,731원` | fallback 제외 정상 표본. 오늘 손실 주축이므로 `entry_filter_quality` 우선순위 유지 |
| `fallback_single_contaminated` | 2 | `+0.295%` | `+6,540원` | 수익 방향이어도 구조 폐기 유지. 관찰 후 추가/중단 없는 fallback은 재도입 금지 |
| `fallback_scout_main_contaminated` | 0 | `N/A` | `0원` | 완료표본에는 scout/main tag 없음 |
| `post_fallback_deprecation` | 1 | `+1.170%` | `+12,001원` | `09:45` 이후 신규 완료 표본 |
| `scale_in_profit_expansion` | 0 | `N/A` | `0원` | 현재 완료표본에 추가진입 확정 태그 없음 |
| `avg_down_candidate` | 0 | `N/A` | `0원` | 현재 완료표본에 물타기 후보 확정 태그 없음 |

### 10-2. 오전 체결 사전 판정

| 지표 | 값 | 해석 |
| --- | ---: | --- |
| `completed_trades` | 8 | low-N |
| `realized_pnl_krw` | `-17,191원` | 당일 누적 음수 |
| `soft_stop_count/partial_fill_events` | `4/7 = 57.1%` | `partial_fill_events < 20`이므로 hard fail 금지, 방향성 부정 |
| `position_rebased_after_fill_events/partial_fill_events` | `13/7 = 1.86` | partial/rebase 부담 과다 |
| `partial_fill_completed_avg_profit_rate` | `-1.038%` | full fill과 분리 필요 |
| `full_fill_completed_avg_profit_rate` | `+0.587%` | partial과 합산 금지 |
| `gatekeeper_fast_reuse_ratio` | `0.0%` | 개선 미확인 |
| `gatekeeper_eval_ms_p95` | `21,033ms` | 목표 `15,900ms` 초과 |
| `gatekeeper_bypass_evaluation_samples` | 50 | sample은 최소선이지만 partial low-N 때문에 방향성 판정만 허용 |

### 10-3. 미진입 blocker 사전 분포

terminal 후보 기준 `total_candidates=115`, `missed_winner_rate=76.5%`, `estimated_counterfactual_pnl_10m_krw_sum=647,365원`이다.

| 축 | terminal 후보 | 해석 |
| --- | ---: | --- |
| `latency guard miss` | `97/115 = 84.3%` | 오전 기회비용의 1차 축 |
| `liquidity gate miss` | `1/115 = 0.9%` | 표본 적음 |
| `AI threshold miss` | `0/115` | terminal 기준 0. event overlap 기준 `blocked_ai_score=233`과 합산 금지 |
| `overbought gate miss` | `0/115` | terminal 기준 0. event overlap 기준 `blocked_overbought=20,819`와 합산 금지 |
| `blocked_strength_momentum` | `17/115 = 14.8%` | 체크리스트 4축 밖이지만 별도 관찰 필요 |

### 10-4. 1차 후보축

- canary 착수축 후보: `main-only buy_recovery_canary`
- 보류축 후보: `holding_exit`, `position_addition_policy`, `EOD/NXT`, `AI 엔진 A/B`
- 오후 추가확인: `latency p95 21,033ms` 지속 여부, `partial_fill` low-N 방향성, `09:45` 이후 fallback 회귀 0건 유지, `watching_buy_recovery_canary promoted=true` 증가 여부

## 11. 현재 리베이스 플랜 반영 검증 (`2026-04-21 22:20 KST`)

### 11-1. 판정

현재 리베이스 플랜은 `main-only + Gemini 중심 정상화` 기준으로 실전 의사결정에 필요한 핵심 축은 대부분 반영됐다.  
다만 `보유 AI 포지션 컨텍스트 직접 전달`은 Gemini 보유 프롬프트/액션 분리와 별개로 아직 미완이며, `remote` 수집 스크립트 파일은 남아 있지만 crontab/설치 스크립트 기준으로는 비활성화 상태다.

### 11-2. 반영 완료로 확인한 항목

| 항목 | 현재 상태 | 코드/운영 근거 |
| --- | --- | --- |
| `main-only baseline` | 반영 | `songstock`/원격 비교는 의사결정 기준에서 제외. 현재 crontab에 `REMOTE_*`, `SHADOW_CANARY_*`, `fetch_remote` 실행 항목 없음 |
| Gemini live 고정 | 반영 | `runtime_ai_router.resolve_scalping_ai_route()` 기본값 `gemini`; `RuntimeAIEngineRouter`는 `openai` 명시 + main + 엔진 존재 시에만 OpenAI 사용 |
| OpenAI/Gemini A/B 보류 | 반영 | `OPENAI_DUAL_PERSONA_ENABLED=False`; `kiwoom_sniper_v2.py`는 `scalping_ai_route == "openai"`일 때만 OpenAI 스캘핑 엔진 초기화 |
| fallback 폐기 | 반영 | `SCALP_LATENCY_FALLBACK_ENABLED=False`, `SCALP_SPLIT_ENTRY_ENABLED=False`, `SCALP_LATENCY_GUARD_CANARY_ENABLED=False`; `FallbackStrategy.build()`는 빈 주문 반환 |
| fallback 빈 주문 reject | 반영 | `EntryOrchestrator`가 빈 fallback 주문을 `latency_fallback_deprecated`로 reject |
| `buy_recovery_canary` | 반영 | `AI_MAIN_BUY_RECOVERY_CANARY_ENABLED=True`, score `65~79`, promote `>=75`, buy pressure/tick accel/micro VWAP/large sell print 조건 확인 |
| 소량 probe canary | 반영 | `AI_WAIT6579_PROBE_CANARY_ENABLED=True`, budget `50,000원`, qty `1~1`, `wait6579_probe_canary_applied` 로그 경로 존재 |
| WAIT65~79 EV 코호트 | 반영 | `wait65_79_ev_candidate` stage에 `buy_pressure`, `tick_accel`, `micro_vwap_bp`, `latency_state`, `parse_ok`, `ai_response_ms`, `terminal_blocker` 기록 |
| Gemini 정량 수급 피처 parity | 반영 | Gemini `_format_market_data()`의 `[정량형 수급 피처]`에 spread/top-depth/microprice/VWAP/MA5/대량체결/체결속도 계열 반영 |
| Gemini 프롬프트/액션 스키마 분리 | 반영 | `watching/holding/exit/shared` 분기, `HOLD/TRIM/EXIT`는 `action_v2`, legacy `action`은 `WAIT/SELL/DROP`로 호환 매핑 |

검증 명령:

```bash
PYTHONPATH=. .venv/bin/pytest -q \
  src/tests/test_runtime_ai_router.py \
  src/trading/tests/test_entry_policy.py \
  src/trading/tests/test_entry_orchestrator.py \
  src/tests/test_sniper_entry_latency.py \
  src/tests/test_ai_engine_cache.py \
  src/tests/test_scalping_feature_packet.py \
  src/tests/test_wait6579_ev_cohort_report.py \
  src/tests/test_log_archive_service.py \
  src/tests/test_state_handler_fast_signatures.py
```

결과: `59 passed, 1 warning`. warning은 `pandas_ta`의 pandas copy-on-write deprecation이며 이번 검증 판정과 무관하다.

### 11-3. 부분 반영/잔여 리스크

| 항목 | 판정 | 사유 | 다음 처리 |
| --- | --- | --- | --- |
| 보유 AI 포지션 컨텍스트 직접 전달 | 부분 반영 | `prompt_profile="holding"`과 `HOLD/TRIM/EXIT` 정규화는 반영됐지만, `profit_rate`, `peak_profit`, `drawdown_from_peak`, `held_sec`, `buy_price`, `position_size_ratio`가 Gemini `analyze_target()` 프롬프트 패킷에 직접 들어가는 구조는 아직 없다 | 더 빠른 `holding_exit` 축의 `[HoldingCtx0422]`에서 `position_context` 인자와 `[보유 포지션 컨텍스트]` 섹션을 별도 1축으로 설계한다. 검증은 shadow 없이 `holding_exit position_context canary` + rollback guard로만 수행하고, `position_addition_policy`는 그 결과를 후속 입력으로 사용 |
| 원격 수집 스크립트 파일 | 비활성 잔존 | `deploy/run_remote_latency_baseline.sh`, `deploy/fetch_remote_scalping_logs_cron.sh`, `src/engine/fetch_remote_scalping_logs.py`, `src/engine/collect_remote_latency_baseline.py` 파일은 남아 있다. 다만 crontab 및 설치 스크립트는 원격 항목을 추가하지 않는다 | 현 의사결정 입력에서는 제외. 완전 삭제는 별도 정리축으로만 수행 |
| OpenAI v2 보유 action schema | 현 즉시축 범위 밖 | 현재 live 라우팅은 Gemini라 운영 병목에는 직접 영향이 없다. OpenAI v2는 아직 `BUY/WAIT/DROP` 중심 정규화다 | `2026-04-24 POSTCLOSE` A/B 재개 여부 판정 시 parity 보완 여부 재검토 |

### 11-4. 결론

리베이스 플랜의 현재 반영률은 운영 기준으로 `높음`이다.  
즉시 의사결정에 필요한 `fallback 폐기`, `main-only`, `Gemini live 고정`, `BUY drought 회복 canary`, `WAIT65~79 EV 계측`, `Gemini 프롬프트/액션 분리`는 코드와 테스트로 확인됐다.

남은 핵심 보완은 `보유 AI가 실제 포지션 수익/보유시간/고점대비 하락을 프롬프트 입력으로 받게 만드는 것`이다. 이 항목은 현재 `main-only buy_recovery_canary`와 같은 날 묶어 적용하지 않고, 더 빠른 `holding_exit` 축의 `[HoldingCtx0422]`에서 별도 1축으로 먼저 설계한다. 검증은 shadow 없이 `holding_exit position_context canary`로만 수행하며, `position_addition_policy`는 해당 입력 스키마가 확정된 뒤 불타기/물타기/추가진입 중단 상태머신에 연결한다.

## 12. 완료 기준

1. 진입/보유/청산 로직표가 확정된다.
2. fallback 오염 표본과 normal-only 표본이 분리된다.
3. 기존 split-entry/fallback/legacy shadow 후보가 폐기 또는 후순위 재설계로 재분류된다.
4. `main-only buy_recovery_canary`와 rollback guard가 문서에 고정되고, 감사인 정의의 `entry_filter_quality`와 혼용되지 않는다.
5. `2026-04-22` 장전 canary 적용 과제가 체크리스트에 연결된다.

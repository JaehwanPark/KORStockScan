# 작업지시서: 2026-04-21 장후 `2026-04-20` 적용사항 결과검증

작성일: `2026-04-20`  
실행 시점: `2026-04-21 INTRADAY 12:30~13:00 KST (1차)` + `POSTCLOSE 17:00~17:30 KST (최종)`  
대상: 운영 트레이더 / Codex  
기준 문서: [2026-04-21-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-21-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.performance-report.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.performance-report.md)

참조 우선순위:
1. [2026-04-20-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-20-stage2-todo-checklist.md)
2. [2026-04-20-postclose-audit-result-report.md](/home/ubuntu/KORStockScan/docs/2026-04-20-postclose-audit-result-report.md)
3. [2026-04-20-operator-response.md](/home/ubuntu/KORStockScan/docs/2026-04-20-operator-response.md)
4. [plan-korStockScanPerformanceOptimization.performance-report.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.performance-report.md)

---

## 1. 목적

`2026-04-20`에 적용한 실전 변경의 다음날 효과를 **정량 기준으로 판정**하되, `2026-04-21 09:45 KST` 이후에는 기존 승격 판단을 일시중단하고 `Plan Rebase` 기준으로 재해석한다.

1. 기대효과가 수치로 확인되는지
2. 기대효과가 없거나 역효과면 즉시 보류/롤백 조건을 충족했는지
3. 내일(`2026-04-22`) 운영에서 canary 착수축 1개와 보류할 축을 분리했는지
4. 오전 집중구간 기준 1차 판정과 장후 최종판정을 분리해 기록했는지
5. 진입/보유/청산 로직 전수점검 후 튜닝포인트를 다시 선정해야 하는지

---

## 2. 검증 대상 변경

1. `SCALP_PARTIAL_FILL_RATIO_GUARD_ENABLED=True` (`partial fill min_fill_ratio` guard)
2. `INVEST_RATIO_SCALPING_MIN/MAX`, `SCALPING_MAX_BUY_BUDGET_KRW` 하향
3. `gatekeeper fast_reuse` 시그니처 coarsening
4. OpenAI parse fallback 메타 복구 + JSON parser 강건화
5. `system_metric_sampler` 1분 수집
6. `2026-04-21 09:29 KST` 응급 정정: 지연대응 fallback 분할진입 전체 OFF
   - 정정 사유: 기존 진단은 `partial/rebase 관찰축`으로 과소 귀속했다. 실제 손실 증폭 경로는 `fallback split-entry -> partial/rebase -> soft_stop`로 정정한다.
   - 조치: `SCALP_LATENCY_FALLBACK_ENABLED=False`, `SCALP_SPLIT_ENTRY_ENABLED=False`, `SCALP_LATENCY_GUARD_CANARY_ENABLED=False`, `latency_fallback_disabled` reject 적용, 봇 재기동.
   - 검증: 1차 가드 후에도 `fallback_bundle_ready orders=1`이 발생했으므로 1-leg 축소가 아니라 fallback 진입 자체 차단이 필요했다.
7. `2026-04-21 09:45 KST` 응급 폐기: `fallback_scout/main` 생성 로직 제거
   - 정정 사유: 기존 scout/main은 관찰형 분할진입이 아니라 동시 주문 번들이었다. `scout 투입 -> 가격 확인 -> 추가/중단` 의사결정이 없었으므로 물타기/불타기의 탐색형 버전으로 볼 수 없다.
   - 조치: `FallbackStrategy.build()`는 빈 주문 리스트를 반환하는 deprecated null-object로 변경한다. fallback 호출자는 빈 주문을 `latency_fallback_deprecated` reject로 처리한다.
   - 운영 규칙: `fallback_scout/main`, `fallback_single` 재개 금지. 재도입은 금지한다. 유사 패턴은 AI 생성 코드 체크게이트와 운영자 수동 승인을 통과하기 전 실전 적용할 수 없다.
8. `2026-04-21 Plan Rebase`: 기존 튜닝 plan 개편
   - 정정 사유: 감사인이 의견을 주기에는 기존 관찰축이 `fallback` 오염과 분리되지 않았고, 진입/보유/청산 로직 간 연결이 불명확하다.
   - 조치: [workorder-0421-tuning-plan-rebase.md](/home/ubuntu/KORStockScan/docs/workorder-0421-tuning-plan-rebase.md)에 따라 `진입/보유/청산 전수점검`, `fallback 오염 코호트 재집계`, `다음 튜닝포인트 1축 재선정`을 수행한다.
   - 운영 규칙: 전수점검/코호트 분리 완료 전 신규 live canary 금지. 완료 후 다음 1축은 shadow 선행이 아니라 canary 즉시 적용 + 당일 rollback guard로 검증한다.
9. `2026-04-21 10:55 KST` AI 라우팅 정렬
   - 조치: live 스캘핑 라우팅을 Gemini로 고정하고 OpenAI/Gemini A/B 및 dual-persona shadow를 보류한다.
   - 재개 조건: 감사인 정의의 `entry_filter_quality` canary 1차 판정 완료 후 별도 판정한다. 최대 기한은 `2026-04-24 POSTCLOSE`다.
   - 검증: `py_compile` 통과, `src/tests/test_runtime_ai_router.py` `3 passed`, 라우터 로그 `scalping_route=gemini scalping_openai=off`, 런타임 상수 `OPENAI_DUAL_PERSONA_ENABLED=False`, `SCALPING_AI_ROUTE=gemini`.
10. `2026-04-21 12:18 KST` BUY 표본 고갈 긴급 대응
   - 정정 사유: 감사인이 요구한 `entry_filter`는 원래 `불량 진입 감소/진입 품질 개선` 축인데, 장중 긴급 적용은 그 의미와 다르게 `Gemini WAIT 65~79 BUY 회복`을 위한 완화성 재평가였다.
   - 조치: 실전 반영 명칭을 `buy_recovery_canary`로 분리한다. `WAIT 65~79` 구간에서 `latency_state != DANGER`, `buy_pressure_10t >= 65`, `tick_acceleration_ratio >= 1.20`, `curr_vs_micro_vwap_bp >= 0`, `large_sell_print_detected=False`를 만족할 때만 2차 Gemini 판정을 수행하고 `BUY score >= 75`면 승격한다.
   - 운영 규칙: `entry_filter_quality`와 `buy_recovery_canary`는 문서/리포트/체크리스트에서 혼용하지 않는다. A/B 재개 조건은 여전히 `entry_filter_quality` 1차 판정 완료다.
11. `2026-04-21 13:37 KST` WAIT65_79 EV 코호트/가상체결/N gate 즉시 반영
   - 조치: `wait65_79_ev_candidate` 이벤트를 추가해 `buy_pressure`, `tick_accel`, `micro_vwap_bp`, `latency_state`, `parse_ok`, `ai_response_ms`를 고정 수집하고, terminal blocker를 결합한 `wait6579_ev_cohort` 스냅샷을 생성한다.
   - 조치: `WAIT 65~79` 표본에 paper-fill(가상체결) 시뮬레이션을 적용해 `expected_fill_rate_pct`, `expected_ev_pct`, `expected_ev_krw`를 동시 산출한다.
   - 조치: `WAIT 65~79 -> BUY 승격` 케이스에는 소량 실전 `probe canary`를 강제한다. (`AI_WAIT6579_PROBE_CANARY_MAX_BUDGET_KRW`, `AI_WAIT6579_PROBE_CANARY_MIN_QTY`, `AI_WAIT6579_PROBE_CANARY_MAX_QTY`)
   - 운영 규칙: 임계값 하향 승인은 `full/partial` 분리 표본 최소 N(`AI_WAIT6579_EV_MIN_FULL_SAMPLES`, `AI_WAIT6579_EV_MIN_PARTIAL_SAMPLES`, 기본 `20/20`)을 먼저 통과해야 한다.

---

## 3. 핵심 판정 지표

### 3-1. 체결품질/손실축

- `soft_stop_count / partial_fill_events` (목표 `<= 0.46`)
- `position_rebased_after_fill_events / partial_fill_events` (목표 `<= 1.15`)
- `partial_fill_completed_avg_profit_rate` (목표 `>= -0.15`)
- `full_fill_events` vs `partial_fill_events` 분포

### 3-2. latency 축

- `gatekeeper_fast_reuse_ratio` (목표 `>= 10.0%`)
- `gatekeeper_eval_ms_p95` (목표 `<= 15,900ms`)
- `latency_block_events / budget_pass_events`
- `gatekeeper_reuse_blockers` 상위 분포 (`signature_changed` 비중 확인)

### 3-3. AI 결과 경로

- `ai_result_source=-` 신규 표본 (`0건`)
- `ai_parse_ok=False` 중 `ai_parse_fail=False` 표본 (`0건`)
- `openai_parse_fallback` 건수/비율

### 3-4. 운영 관측 완전성

- `logs/system_metric_samples.jsonl` 장중 샘플 `>= 360`
- 최대 샘플 간격 `<= 180초`
- 필드 누락(`cpu/load/memory/io/top`) `0건`

### 3-5. WAIT65_79 EV 코호트 판정축

- `wait6579_ev_cohort.metrics.expected_fill_rate_pct`
- `wait6579_ev_cohort.metrics.avg_expected_ev_pct`, `expected_ev_krw_sum`
- `wait6579_ev_cohort.fill_split(FULL/PARTIAL/NONE)` 분포
- `wait6579_ev_cohort.approval_gate.min_sample_gate_passed` (임계값 하향 1차 통과조건)
- `wait6579_ev_cohort.approval_gate.ev_directional_check_passed` (N 통과 후 방향성 확인)

---

## 4. 실행 규칙

1. 손익 단독 판정 금지. `거래수 -> 퍼널 -> blocker -> 체결품질 -> HOLDING -> 손익` 순서 유지.
2. `COMPLETED + valid profit_rate`만 손익 판정에 사용한다.
3. 표본 부족(`partial_fill_events < 20` 또는 `gatekeeper_eval_samples < 50`)이면 hard pass/fail 대신 방향성 판정으로 남긴다. 방향성 판정은 2영업일 이내 재판정하며, 미재판정 시 자동 보류한다.
4. 지표가 목표 미달이면 즉시 “유지/보류/롤백 후보”를 분리 기록한다.
5. `1차 판정(12:30~13:00)`은 오전 표본 고정용이며, `최종 판정(17:00~17:30)`은 오후 미진입/기회비용 보정을 포함한다.
6. 오후 구간에서 실제 체결이 없어도 `AI BUY 미진입 blocker 4축(latency/liquidity/AI threshold/overbought)` 분포는 반드시 최종판정에 반영한다.
7. 지연대응 fallback 분할진입은 `재평가 canary`가 아니라 `응급 폐기축`으로 다룬다. 장후에는 해당 축의 재개 여부가 아니라 손실 증폭 기여도와 GPT 금지패턴/AI 생성 코드 체크게이트 필요성을 판정한다.
8. `fallback_scout/main` 과거 동작은 성과 개선 후보가 아니라 실패 설계로 분류한다. 감사 보고에는 “동시 2-leg 주문이라 탐색형 분할진입 요건을 충족하지 못했다”는 정정 사유를 포함한다.
9. 장후 최종판정은 기존 승격/유지 후보를 강제로 고르지 않는다. `Plan Rebase` 결과에 따라 `canary 착수축 1개 + 보류축`으로 닫고 rollback guard를 함께 기록한다.

---

## 5. 보고 템플릿

### 5-1. 장중 1차 보고 템플릿 (12:30~13:00)

```md
## Workorder0421 Midday 1차

- 판정:
  - 오전 기준 canary 착수축 후보 = `<축명>`
  - 오전 기준 보류축 후보 = `<축명>`
  - 표본 품질 = `<충분/부족>`

- 근거:
  - soft_stop_count/partial_fill_events = `<수치>`
  - rebase/partial_fill = `<수치>`
  - partial_fill_completed_avg_profit_rate = `<수치>`
  - gatekeeper_fast_reuse_ratio = `<수치>`
  - gatekeeper_eval_ms_p95 = `<수치>`
  - 오전 미진입 blocker 4축 분포 = `<latency/liquidity/ai_threshold/overbought>`
  - 지연대응 fallback 응급중단 이후 신규 fallback 발생 = `<0건/발생>`

- 다음 액션:
  - 장후 최종에서 추가 확인할 항목 = `<항목>`
```

### 5-3. 장중 1차 실행 결과 (`2026-04-21 12:36 KST`, 지연실행)

```md
## Workorder0421 Midday 1차 (실행본)

- 판정:
  - 오전 기준 canary 착수축 후보 = `main-only buy_recovery_canary (유지)`
  - 오전 기준 보류축 후보 = `holding_exit / position_addition_policy / EOD-NXT / AI 엔진 A/B`
  - 표본 품질 = `부족 (partial_fill_events=7, gatekeeper_eval_samples=55)`

- 근거:
  - soft_stop_count/partial_fill_events = `4/7 = 57.1%` (사전 잠금값 유지)
  - rebase/partial_fill = `13/7 = 1.86`
  - partial_fill_completed_avg_profit_rate = `-1.038%`
  - gatekeeper_fast_reuse_ratio = `0.0%`
  - gatekeeper_eval_ms_p95 = `21,033ms`
  - 오전 미진입 blocker 4축 분포 = `latency 97/115(84.3%), liquidity 1/115(0.9%), AI threshold 0/115, overbought 0/115`
  - 지연대응 fallback 응급중단 이후 신규 fallback 발생 = `0건`

- 다음 액션:
  - 장후 최종에서 `latency_block`을 1차 해석축으로 고정
  - `buy_recovery_canary` 실측(`WAIT 65~79 -> BUY`)은 `2026-04-22` 오전까지 수집 후 `12:00` 이후 첫 스냅샷 시점에 판정 고정
```

### 5-2. 장후 최종 보고 템플릿 (17:00~17:30)

```md
## Workorder0421 결과검증

- 판정:
  - canary 착수축 1개 = `main-only buy_recovery_canary`
  - 보류축 = `entry_filter_quality`, `AI engine A/B`, `프로파일별 특화 프롬프트 확대`
  - 즉시 재검토 필요 = `latency guard miss`, `partial fill 손실 증폭`
  - 주의 = `2026-04-21 15:37 KST` 수동 최종 스냅샷 갱신 기준으로 재확인 완료

- 근거:
  - soft_stop_count/partial_fill_events = `4/7 = 57.1%` (문서 집계 기준)
  - rebase/partial_fill = `13/7 = 1.86`
  - partial_fill_completed_avg_profit_rate = `-1.038%`
  - gatekeeper_fast_reuse_ratio = `0.0%`
  - gatekeeper_eval_ms_p95 = `17,594ms`
  - ai_result_source='-' 신규 건수 = `blocked_ai_score 612건의 block 로그에는 '-'가 존재하나 손익 표본으로 사용하지 않음`
  - system_metric 장중 샘플/최대간격 = `391건 / 61초`
  - `fallback split-entry -> partial/rebase -> soft_stop` 손실 증폭 기여도 = `fallback split-entry는 폐기됐고, 오늘 관측상 partial/rebase/latency 병목이 기대값 훼손의 우선 원인`

- 다음 액션:
  - `2026-04-22` canary 착수축 1개 = `main-only buy_recovery_canary` 유지 관찰
  - rollback guard = `N_min, loss_cap 일간 합산 NAV 대비 -0.35%, reject_rate +15.0%p 증가, latency_p95 15,900ms 초과, partial_fill_ratio 복합 경고, fallback_regression, buy_drought_persist`
  - 추가 확인 필요 데이터 = `04-22 12:00 이후 ai_confirmed->submitted, full/partial, missed_entry_counterfactual`
  - 오후 미진입 blocker 4축 보정 결과 = `latency guard miss가 주 원인, liquidity/AI threshold/overbought는 terminal blocker로는 낮음`
  - Plan Rebase 결과 = `entry_filter_quality와 buy_recovery_canary 용어 분리 완료, rollback source-of-truth는 main-only snapshot으로 고정`
```

---

## 6. 완료 기준

1. 장중 1차 보고(`12:30~13:00`)가 작성된다.
2. 장후 최종 보고(`17:00~17:30`)가 작성된다.
3. 위 핵심 지표가 모두 채워진다.
4. canary 착수축 1개/보류축이 분리된다.
5. `2026-04-22`로 넘길 후속 액션이 체크리스트에 기록된다.
6. `Plan Rebase` 필요 여부와 신규 live canary 보류 여부가 명시된다.
7. 감사인 정의의 `entry_filter_quality`와 장중 긴급 적용한 `buy_recovery_canary`가 분리 기록된다.

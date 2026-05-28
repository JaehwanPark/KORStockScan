# 작업지시서: 2026-04-21 감사인 전달용 성과측정결과 및 분석보고서 생성

작성일: `2026-04-20`  
실행 시점: `2026-04-21 INTRADAY 13:00 이전(예비본)` + `POSTCLOSE 17:30~18:00 KST(확정본)`  
대상: 운영 트레이더 / Codex  
기준 문서: [2026-04-21-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-21-stage2-todo-checklist.md), [workorder-0421-validate-0420-applies.md](/home/ubuntu/KORStockScan/docs/archive/workorders/workorder-0421-validate-0420-applies.md)
Plan Rebase 감사보고서: [2026-04-21-plan-rebase-auditor-report.md](/home/ubuntu/KORStockScan/docs/archive/plan-rebase-transition-2026-04-20-to-2026-04-22/2026-04-21-plan-rebase-auditor-report.md)

참조 우선순위:
1. [plan-korStockScanPerformanceOptimization.performance-report.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.performance-report.md)
2. [2026-04-20-auditor-third-review.md](/home/ubuntu/KORStockScan/docs/archive/plan-rebase-transition-2026-04-20-to-2026-04-22/2026-04-20-auditor-third-review.md)
3. [2026-04-20-operator-response.md](/home/ubuntu/KORStockScan/docs/archive/plan-rebase-transition-2026-04-20-to-2026-04-22/2026-04-20-operator-response.md)
4. [workorder-0421-validate-0420-applies.md](/home/ubuntu/KORStockScan/docs/archive/workorders/workorder-0421-validate-0420-applies.md)

---

## 1. 목적

`2026-04-21` 장후 기준으로 감사인에게 제출할 **성과측정 결과 + 분석보고서**를 생성한다.

1. 오늘 적용분 검증 결과를 판정/근거/다음액션으로 압축
2. 수치 근거와 해석을 분리해 감사 추적 가능성 확보
3. 미결 리스크(거버넌스, 데이터 품질, 표본 부족)를 명시
4. `Plan Rebase` 필요성과 진입/보유/청산 전수점검 범위를 감사인이 검토할 수 있게 제시

---

## 2. 분리 제공 사유

1. 실제 매매와 손실 이벤트가 오전에 집중되므로, `13:00 이전` 예비본으로 손실 연쇄(`partial/rebase -> soft_stop`)를 먼저 잠가 운영 판단 지연을 줄인다.
2. 오후에는 체결이 적어도 `미진입 blocker 4축(latency/liquidity/AI threshold/overbought)`과 기회비용 데이터가 추가되므로, 장후 확정본에서 오전 예비판정을 보정해야 감사 정합성이 유지된다.
3. 단일 장후본만 유지하면 오전 대응 판단이 늦고, 단일 장중본만 유지하면 오후 미진입 데이터 누락으로 감사 근거가 약해진다.

---

## 3. 필수 포함 항목

1. 판정 요약
2. 핵심 지표 결과표 (`기준선`, `당일값`, `목표`, `판정`)
3. 축별 분석 (`partial/rebase`, `latency`, `AI 결과 경로`, `운영 관측`)
4. 감사 미결 항목 상태 (`요청 D/E/F`, 승인/보류 상태)
5. 다음 영업일 액션 (`canary 착수축 1개`, `보류축`, `정식 rollback guard`, `재검토 시각`)
6. `2026-04-21 09:29 KST` 응급 정정 사유
   - 기존 `partial/rebase 관찰축` 진단은 불충분했다.
   - 원인 귀속은 `fallback split-entry -> partial/rebase -> soft_stop` 손실 증폭축으로 정정한다.
   - 지연대응 fallback은 `SCALP_LATENCY_FALLBACK_ENABLED=False`, `SCALP_SPLIT_ENTRY_ENABLED=False`, `SCALP_LATENCY_GUARD_CANARY_ENABLED=False`로 실전 재개 금지 상태임을 명시한다.
7. `2026-04-21 09:45 KST` 설계 폐기 사유
   - `fallback_scout/main`은 `scout 투입 -> 충분히 낮은 가격이면 추가 -> 달아나면 중단` 구조가 아니었다.
   - 실제 구현은 지연 판정 후 scout/main을 동시에 제출하는 번들이어서 탐색형 물타기/불타기 요건을 충족하지 못했다.
   - 따라서 감사 보고에는 `fallback_scout/main`을 개선 후보가 아니라 폐기된 실패 설계로 명시한다.
8. `Plan Rebase` 개편 사유
   - 기존 관찰축은 진입/보유/청산 로직이 분리되어 있지 않고, fallback 오염 표본이 섞여 감사 의견을 주기 어렵다.
   - 감사 보고에는 [workorder-0421-tuning-plan-rebase.md](/home/ubuntu/KORStockScan/docs/archive/workorders/workorder-0421-tuning-plan-rebase.md)의 `전수점검 범위`, `코호트 재정렬`, `다음 튜닝포인트 후보`를 포함한다.
   - 예비 감사보고서는 [2026-04-21-plan-rebase-auditor-report.md](/home/ubuntu/KORStockScan/docs/archive/plan-rebase-transition-2026-04-20-to-2026-04-22/2026-04-21-plan-rebase-auditor-report.md)를 기준으로 한다.
9. `2026-04-21 10:55 KST` AI 라우팅 정렬 검증
   - live 스캘핑 라우팅은 Gemini로 고정한다.
   - OpenAI/Gemini A/B와 dual-persona shadow는 `entry_filter` canary 1차 판정 완료 후, 늦어도 `2026-04-24 POSTCLOSE`에 재개 여부를 별도 판정한다.
   - 검증 증거는 `py_compile`, `src/tests/test_runtime_ai_router.py`, 라우터 로그, 런타임 상수 확인을 포함한다.


---

## 4. 결과표 기준 지표

- `soft_stop_count / partial_fill_events`
- `position_rebased_after_fill_events / partial_fill_events`
- `partial_fill_completed_avg_profit_rate`
- `gatekeeper_fast_reuse_ratio`
- `gatekeeper_eval_ms_p95`
- `latency_block_events / budget_pass_events`
- `ai_result_source=-` 신규 건수
- `ai_parse_ok=False` 중 `ai_parse_fail=False` 건수
- `system_metric_samples` 장중 coverage (`count`, `max_gap_sec`)

---

## 5. 작성 규칙

1. 수익률 파생값보다 `거래수/퍼널/blocker/체결품질` 우선.
2. 손익은 `COMPLETED + valid profit_rate`만 사용.
3. `full fill`과 `partial fill`은 분리 해석.
4. 표본 부족 시 “방향성 판정”으로 명시하고 과잉 결론 금지.
5. 미결 항목은 “해결됨/부분해소/미결” 3단계로 표시.
6. 예비본에서 제시한 유지/보류 후보가 확정본에서 바뀌면 `변경 사유(오후 추가 데이터)`를 반드시 1줄로 남긴다.
7. 감사 정정은 별도 섹션으로 작성한다. 운영자가 손실 확대를 지적한 뒤 확인된 사후 정정이므로, 기존 판단의 누락점과 응급 차단 조치를 분리해 기록한다.
8. `fallback_scout/main`은 이름과 의도가 실제 구현과 불일치한 설계 실패로 분류한다. 향후 재도입 가능성 표현은 금지하고, 유사 패턴은 GPT 금지패턴과 AI 생성 코드 체크게이트 대상으로 기록한다.
9. 감사인 의견 요청은 기존 튜닝축 승격 여부가 아니라 `진입/보유/청산 로직표`, `fallback 오염 제거 기준`, `entry_filter canary`, `rollback guard`에 맞춘다.
10. 표본 부족으로 방향성 판정을 한 경우 유효기간은 2영업일이며, 미재판정 시 자동 보류로 처리한다.

---

## 6. 제출 보고 템플릿

### 6-1. 장중 예비본 (13:00 이전)

```md
## AuditorDelivery0421 Preclose Draft

- 분리 사유:
  - 오전 집중 체결 기반 선판정 + 오후 미진입/기회비용 보정 필요

- 판정(예비):
  - 종합 등급(예비) = `<등급>`
  - canary 착수축 후보 = `<축명>`
  - 보류축 후보 = `<축명>`

- 근거(오전 기준):
  - <지표표 1개: 기준선/오전값/목표/방향성>
  - partial/rebase 분석(오전) = `<한 단락>`
  - 감사 정정 = `fallback split-entry -> partial/rebase -> soft_stop` 원인 귀속 정정 및 09:29 fallback 전체 OFF, 09:45 `fallback_scout/main` 생성 로직 폐기
  - latency 분석(오전) = `<한 단락>`

- 장후 보정 예정:
  - 오후 미진입 blocker 4축 분포
  - 기회비용 보정
  - Plan Rebase 전수점검 범위
```

### 6-2. 장후 확정본 (17:30~18:00)

```md
## AuditorDelivery0421

- 판정:
  - 종합 등급 = `조건부 보류`
  - canary 착수축 1개 = `main-only buy_recovery_canary`
  - 보류축 = `entry_filter_quality`, `AI engine A/B`, `프로파일별 특화 프롬프트 확대`
  - 산출물 = [2026-04-21-auditor-performance-result-report.md](/home/ubuntu/KORStockScan/docs/archive/plan-rebase-transition-2026-04-20-to-2026-04-22/2026-04-21-auditor-performance-result-report.md)

- 근거:
  - 지표표 = `완료. completed_trades, realized_pnl, full/partial 수익률, rebase/partial, latency, BUY drought, missed_winner, sampler coverage 포함`
  - partial/rebase 분석 = `partial_fill_events=7로 N gate 미달이나 rebase/partial=1.86, partial 평균=-1.038%로 방향성 미달`
  - 감사 정정 = `fallback split-entry 축은 폐기하고 scout/main 비교축은 rollback 기준에서 제외`
  - latency 분석 = `latency_block_events/budget_pass_events=4,848/4,858=99.8%, missed winner 74.8%`
  - AI 결과 경로 분석 = `ai_confirmed BUY 115/744=15.5%, WAIT 474/744=63.7%, blocked_ai_score=612`
  - 운영 관측 완전성 = `system metric 391건, max gap 61초, 필드 누락 0건`
  - Plan Rebase = `entry_filter_quality와 buy_recovery_canary 분리 완료, rollback guard는 main-only source-of-truth로 고정`

- 감사 미결:
  - D(ai_parse_ok=False 분포/진입 여부) = `보류`
  - E(same_symbol_repeat_flag 산식) = `보류`
  - F(테스트 카운트 불일치) = `조치 완료 상태 유지`

- 다음 액션:
  - `2026-04-22` canary 착수축 1개 = `main-only buy_recovery_canary`
  - rollback guard = `N_min, loss_cap(일간 합산 NAV 대비 -0.35%), reject_rate(+15.0%p 증가), latency_p95(15,900ms 초과), partial_fill_ratio 복합 경고, fallback_regression`
  - 재검토 시각 = `2026-04-22 INTRADAY 12:00~12:20`
  - 예비본 대비 변경 사유 = `15:37 KST 수동 최종 스냅샷으로 gatekeeper/latency/missed_winner 값을 보정`
  - 감사인 검토 요청 = `entry_filter_quality와 buy_recovery_canary 분리 해석, A/B 재개조건 검토`
```

---

## 7. 완료 기준

1. 장중 예비본(`13:00 이전`) 1건 생성
2. 장후 확정본(`17:30~18:00`) 1건 생성
3. 지표표에 최소 8개 지표가 채워짐
4. 미결 항목 D/E/F 상태가 모두 명시됨
5. 다음 영업일 액션이 체크리스트로 연결됨
6. Plan Rebase 여부와 감사인 검토 요청사항이 명시됨

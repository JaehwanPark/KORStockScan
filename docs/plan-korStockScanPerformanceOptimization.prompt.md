# 계획: KORStockScan 성능 최적화 실행안 (Session Prompt)

기준 시각: `2026-04-19 KST`  
역할: 다음 세션에서 바로 실행할 **현재 기준 플랜**만 유지한다.

이 문서는 `현재 실행 기준`, `우선순위`, `주간 실행 맵`, `승격/보류 게이트`만 남긴 경량본이다.  
과거 일정, 장문 경과, 상세 해설은 `archive`, `Q&A`, `실행 변경사항`, `정기 성과측정` 문서로 분리한다.

## 문서 맵

| 문서 | 역할 | 언제 먼저 보나 |
| --- | --- | --- |
| [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md) | 현재 실행 기준 | 세션 시작 직후 |
| [plan-korStockScanPerformanceOptimization.qna.md](./plan-korStockScanPerformanceOptimization.qna.md) | 운영 판단 기준/자주 묻는 질문 | 왜 이렇게 운영하는지 확인할 때 |
| [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md) | 기본계획 대비 실행 변경사항 | 원안과 실제 실행이 달라졌을 때 |
| [plan-korStockScanPerformanceOptimization.performance-report.md](./plan-korStockScanPerformanceOptimization.performance-report.md) | 정기 성과측정 기준과 최신 baseline | 장후/주간 성과판정 때 |
| [plan-korStockScanPerformanceOptimization.archive-2026-04-19.md](./plan-korStockScanPerformanceOptimization.archive-2026-04-19.md) | `2026-04-19` 정리 시점에 prompt에서 걷어낸 상세 경과 | 과거 판단 맥락이 필요할 때 |
| [plan-korStockScanPerformanceOptimization.archive-2026-04-08.md](./plan-korStockScanPerformanceOptimization.archive-2026-04-08.md) | 초기 장문 백업본 | 초기 설계와 초반 구현 이력 확인 시 |
| [2026-04-18-nextweek-validation-axis-table-audited.md](./2026-04-18-nextweek-validation-axis-table-audited.md) | 다음주 일자별 검증축 감사표 | 주간 일정/정합성 점검 시 |
| [2026-04-17-midterm-tuning-performance-report.md](./2026-04-17-midterm-tuning-performance-report.md) | `2026-04-17` 고밀도 표본 기준 중간 진단 | 다음주 우선순위 재판정 시 |
| [workorder-integrated-dashboard-db-migration.md](./workorder-integrated-dashboard-db-migration.md) | 통합대시보드 데이터 DB화 작업지시서 | 저장소/API 구조개편 착수 시 |
| `2026-04-20~2026-04-24 stage2 todo checklist` | 날짜별 실제 실행표 | 당일 PREOPEN/INTRADAY/POSTCLOSE 수행 시 |
| [2026-04-10-scalping-ai-coding-instructions.md](./2026-04-10-scalping-ai-coding-instructions.md) | 스캘핑 매매로직 기준 | 코드축 원문 확인 시 |
| [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md) | AI 프롬프트 트랙 기준 | 프롬프트축 원문 확인 시 |

## 문서 운영 규칙

1. `prompt`는 항상 현재 기준만 남긴다.
2. 기본계획과 실제 실행이 달라지면 `execution-delta`에 먼저 적고, 그 결과만 `prompt`에 반영한다.
3. 장후/주간 성과 기준선과 최근 수치는 `performance-report`에 누적하고, `midterm` 보고서는 시점 진단본으로만 유지한다.
4. 과거 일정표, 완료된 실험의 상세 경과, 이미 지나간 공격 일정은 `archive`로 이동한다.
5. `Q&A`는 문서 책임, 모니터링 기간, 해석 기준 같은 **반복 참조 정책**만 남긴다.

## 최종 목표와 운영 원칙

1. 최종 목표는 `손실 억제`가 아니라 `기대값/순이익 극대화`다.
2. 현재 단계의 주제는 `리포트 정합성 유지 + split-entry leakage 제거 + HOLDING/청산 판단 분리`다.
3. 실전 변경은 항상 `한 번에 한 축 canary` 원칙을 지킨다.
4. shadow는 공격적 실행을 늦추기 위한 장치가 아니라 `원인 귀속 정확도`를 확보하기 위한 장치다.
5. `develop=원격 실험서버`, `main=본서버`를 유지하고 `main` 선반영은 금지한다.
6. `NULL`, 미완료 상태, fallback 정규화 값은 손익 기준에서 제외한다. 손익 계산은 `COMPLETED + valid profit_rate`만 사용한다.
7. 장후 리포트의 우선 지표는 `거래수 -> 퍼널 -> blocker -> 체결품질 -> missed_upside -> 손익` 순서다.
8. BUY 후 미진입은 `latency guard miss`, `liquidity gate miss`, `AI threshold miss`, `overbought gate miss`로 분리 해석한다.
9. `full fill`과 `partial fill`은 같은 표본으로 합치지 않는다.
10. 원인 귀속이 불명확하면 먼저 `리포트 정합성`, `이벤트 복원`, `집계 품질`을 점검한다.
11. HOLDING 축 승격은 `missed_upside_rate`, `capture_efficiency`, `GOOD_EXIT`와 shadow 로그 축을 함께 본다.
12. broad relax(`latency/tag/threshold`)는 `split-entry leakage` 1차 판정 이후에만 재오픈한다.

## 현재 기준 우선순위

| 워크스트림 | 현재 상태 | 판정 | 다음 닫힘 시점 |
| --- | --- | --- | --- |
| `리포트/집계 정합성` | 핵심 게이트는 정리됐으나 장후 판정 규칙 유지 필요 | `완료 유지 / 품질게이트 지속` | 날짜별 checklist 장후 판정 |
| `split-entry leakage` | 다음주 실손익 개선 레버리지 1순위 | `최우선` | `2026-04-20~2026-04-22` 순차 shadow |
| `HOLDING action schema / prompt split` | shadow-only 착수와 D+2 판정 구조 필요 | `2순위` | `2026-04-20 착수`, `2026-04-22 최종판정` |
| `AIPrompt 작업 8/9/10/11/12` | `8/10`은 보류 사유가 생겼고 `9`는 실표본 확인 단계 | `진행 중` | `2026-04-20~2026-04-23` |
| `latency/tag/threshold broad relax` | bugfix-only 외 확장은 근거 부족 | `후순위 유지` | split-entry 1차 판정 후 재오픈 |
| `정기 성과측정` | 중간 진단은 있으나 정기 보고 기준 분리 필요 | `이번 정리에서 기준 문서화` | 장후/주간 반복 운영 |

## 2026-04-20~2026-04-24 실행 맵

| 일자 | 핵심 실행축 | 실행 원칙 | 기대 산출물 |
| --- | --- | --- | --- |
| `2026-04-20 (월)` | `split-entry rebase` shadow 1일차, `HOLDING action schema` shadow-only 착수, `작업 9/8/10` 장후 판정 | split-entry 3축 동시 가동 금지, HOLDING 성과판정은 D+2로 미룬다 | `rebase` 1차 판정, HOLDING baseline/rollback 경로, 작업 8/10 보류 또는 유지 |
| `2026-04-21 (화)` | `split-entry 즉시 재평가` 착수 또는 보류, `split-entry leakage` 승격/보류, `작업 12` 범위 확정 | `N_min/Δ_min/false_entry_rate` 없으면 착수 금지 | 다음 승격축 `1개` 또는 보류 사유 |
| `2026-04-22 (수)` | `same-symbol cooldown` 착수 또는 보류, `HOLDING shadow` 최종판정, `작업 10` 확대 여부 최종판정, `작업 11` 보강 | `schema 변경 효과`와 `critical 경량화 효과`를 분리 기록 | HOLDING 축 go/no-go, cooldown 착수 여부 |
| `2026-04-23 (목)` | `작업 12` 미확정분 최종정리 | `2026-04-21` 미확정이었을 때만 닫는다 | 범위 확정 또는 사유+재시각+escalation |
| `2026-04-24 (금)` | 주간 통합판정 | `regime 태그` 병기, `canary 1축 + 독립 shadow 최대 2축` 원칙 재확인 | 다음주 PREOPEN 승격축 `1개` |

## 승격/보류 게이트

1. `live` 승격은 하루에 `1축`만 연다.
2. 같은 날 shadow 착수축은 최대 `3개`로 제한한다.
3. 모든 판정 행에는 최소 `N_min`, `Δ_min`, `PrimaryMetric`을 남긴다.
4. rollback guard는 `reject_rate`, `partial_fill_ratio`, `latency_p95`, `reentry_freq` 같은 정량값을 포함해야 한다.
5. HOLDING 성과판정은 schema 변경 직후에 내리지 않고 최소 `D+2`에 내린다.
6. `counterfactual` 수치는 직접 실현손익과 합산하지 않고 우선순위 판단 자료로만 쓴다.
7. `full fill`, `partial fill`, `split-entry`, `same_symbol_repeat`는 항상 별도 코호트로 본다.

## 현재 기준 문서 입력 규칙

1. 날짜별 실제 실행과 판정은 해당 `stage2 todo checklist`에 남긴다.
2. 원문 계획과 다른 실행 변경은 [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md)에 남긴다.
3. 장후/주간 baseline과 반복 성과값은 [plan-korStockScanPerformanceOptimization.performance-report.md](./plan-korStockScanPerformanceOptimization.performance-report.md)에 누적한다.
4. 장문 경과, 이미 지난 공격 일정, 세부 구현 경위는 archive로 이동한다.

## 현재 참고 문서

- [2026-04-18-nextweek-validation-axis-table-audited.md](./2026-04-18-nextweek-validation-axis-table-audited.md)
- [2026-04-17-midterm-tuning-performance-report.md](./2026-04-17-midterm-tuning-performance-report.md)
- [workorder-integrated-dashboard-db-migration.md](./workorder-integrated-dashboard-db-migration.md)
- [2026-04-20-stage2-todo-checklist.md](./2026-04-20-stage2-todo-checklist.md)
- [2026-04-21-stage2-todo-checklist.md](./2026-04-21-stage2-todo-checklist.md)
- [2026-04-22-stage2-todo-checklist.md](./2026-04-22-stage2-todo-checklist.md)
- [2026-04-23-stage2-todo-checklist.md](./2026-04-23-stage2-todo-checklist.md)
- [2026-04-24-stage2-todo-checklist.md](./2026-04-24-stage2-todo-checklist.md)
- [2026-04-10-scalping-ai-coding-instructions.md](./2026-04-10-scalping-ai-coding-instructions.md)
- [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md)
- [2026-04-16-holding-profit-conversion-plan.md](./2026-04-16-holding-profit-conversion-plan.md)

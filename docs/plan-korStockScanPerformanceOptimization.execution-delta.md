# KORStockScan 기본계획 대비 실행 변경사항

기준 시각: `2026-04-19 KST`

이 문서는 `2026-04-11` 원안 계획과 `2026-04-19` 현재 실행 기준 사이에서 실제로 변경된 사항만 추린다.  
현재 기준 실행안은 [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)를 본다.

## 1. 판정

1. 계획은 유지하되 실행 방식은 `공격적 동시 추진`에서 `원인 귀속 우선 순차 실행`으로 조정됐다.
2. 가장 큰 변경은 `split-entry 3축 동시 shadow`를 버리고 `rebase -> 즉시 재평가 -> cooldown` 순차 도입으로 바꾼 점이다.
3. HOLDING 축도 `schema 착수`와 `성과판정`을 분리해 `D+2` 판정 구조로 변경됐다.

## 2. 변경사항 요약

| 영역 | 기본계획 | 현재 실행 기준 | 변경 이유 | 현재 닫힘 시점 |
| --- | --- | --- | --- | --- |
| `split-entry shadow` | `2026-04-20`에 `rebase/즉시 재평가/cooldown` 3축 동시 판정 | `2026-04-20 rebase`, `2026-04-21 즉시 재평가`, `2026-04-22 cooldown` 순차 도입 | 동일 세션 원인귀속 불가, audited table `S-1` 반영 | `2026-04-22` |
| `split-entry 판정 조건` | 표본 부족 시 결론 유예 수준의 서술형 | 각 판정 행에 `N_min/Δ_min/PrimaryMetric` 명시 필요 | audited table `S-2` 반영 | `2026-04-20 PREOPEN` |
| `rollback guard` | 문서상 점검 수준 | `reject_rate/partial_fill_ratio/latency_p95/reentry_freq` 정량화 필요 | audited table `S-3` 반영 | `2026-04-20 PREOPEN` |
| `HOLDING 성과판정` | `2026-04-21` 1일차 판정 | `2026-04-22 D+2` 최종판정 | schema 변경 직후 자기참조 오염 방지, audited table `S-4` 반영 | `2026-04-22 POSTCLOSE` |
| `AIPrompt 작업 10` | `2026-04-19` 1차 결과 평가 후 확대 여부 판정 | `2026-04-20`에는 `shadow-only 유지/확대 보류`만 판정, 최종 확대는 `2026-04-22` | `holding_action_applied`, `holding_force_exit_triggered`, `holding_override_rule_version` 관찰축 부족 | `2026-04-22 POSTCLOSE` |
| `AIPrompt 작업 8` | 핵심값 3종 투입 결과 정리 후 완료 후보 | 값 주입은 존재하나 `*_sent` 감사 로그 부족으로 미완료 유지 | 완료 기준과 감사 필드 범위 불일치 | `2026-04-20 POSTCLOSE` 재판정 |
| `broad relax` | `latency/tag/threshold` 확장 후보를 빠르게 재오픈 | `split-entry leakage` 1차 판정 전 재오픈 금지 | 거래수 확대보다 손실축 제거 우선 | split-entry 1차 판정 후 |
| `운영판정` | 실험축별 판정 중심 | `No-Decision Day` 게이트와 `report integrity / event restoration / aggregation quality` 품질게이트 병행 | 잘못된 집계로 잘못된 승격을 막기 위함 | 장후 반복 적용 |

## 3. 변경의 의미

### 3-1. 공격성은 낮춘 것이 아니라 방향을 바꿨다

1. 거래수 확대보다 `split-entry soft-stop` 손실축 제거가 먼저라는 점이 더 명확해졌다.
2. HOLDING 축도 `지금 바로 확대`가 아니라 `측정 가능한 shadow 로그 축 확보 -> D+2 판정`으로 바뀌었다.
3. 이는 보수화가 아니라 `기대값 개선 실패 확률`을 낮추는 방향의 공격성 조정이다.

### 3-2. 문서 운영도 변경됐다

1. `prompt`는 현재 기준만 남긴 경량 실행본으로 바뀌었다.
2. 계획과 실행의 차이는 이 문서에 남긴다.
3. 정기 성과 baseline은 [plan-korStockScanPerformanceOptimization.performance-report.md](./plan-korStockScanPerformanceOptimization.performance-report.md)로 분리했다.

## 4. 앞으로 이 문서를 갱신하는 조건

다음 중 하나가 생기면 이 문서를 먼저 갱신한다.

1. 주간 검증축 표와 날짜별 checklist가 달라질 때
2. 기본계획의 날짜/순서/승격 조건이 바뀔 때
3. shadow-only가 live canary로 바뀌거나 반대로 축소될 때
4. 성과판정 시점이 이동할 때
5. broad relax 재오픈 조건이 변경될 때

## 참고 문서

- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)
- [plan-korStockScanPerformanceOptimization.qna.md](./plan-korStockScanPerformanceOptimization.qna.md)
- [2026-04-18-nextweek-validation-axis-table-audited.md](./2026-04-18-nextweek-validation-axis-table-audited.md)
- [2026-04-20-stage2-todo-checklist.md](./2026-04-20-stage2-todo-checklist.md)
- [2026-04-21-stage2-todo-checklist.md](./2026-04-21-stage2-todo-checklist.md)
- [2026-04-22-stage2-todo-checklist.md](./2026-04-22-stage2-todo-checklist.md)

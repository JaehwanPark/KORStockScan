# KORStockScan 기본계획 대비 실행 변경사항

기준 시각: `2026-04-19 KST`

이 문서는 `2026-04-11` 원안 계획과 `2026-04-19` 현재 실행 기준 사이에서 실제로 변경된 사항만 추린다.  
현재 기준 실행안은 [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)를 본다.

## 1. 판정

1. 계획은 유지하되 실행 방식은 `공격적 동시 추진`에서 `원인 귀속 우선 순차 실행`으로 조정됐다.
2. 가장 큰 변경은 `split-entry 3축 동시 shadow`를 버리고 `rebase -> 즉시 재평가 -> cooldown` 순차 도입으로 바꾼 점이다.
3. HOLDING 축도 `schema 착수`와 `성과판정`을 분리해 `D+2` 판정 구조로 변경됐다.
4. `2026-04-20` 기준으로 baseline/rollback 수치 해석도 조정됐다. 문서 파생값과 rolling trend 값을 hard KPI로 섞어 쓰지 않도록 `DB 우선 실필드 기준`으로 재고정한다.
5. `2026-04-20`부터 신규 관찰축/보완축은 `shadow`를 열지 않고 `canary-only`로 운영한다.
6. `TRADING_RULES` 운영 상수, 특히 모델명/투자비율/주문한도/실전 canary 스위치는 요청 범위를 넘겨 바꾸지 않는다. 변경 필요 시 사용자 명시 승인과 롤백 조건을 먼저 기록한다.

## 2. 변경사항 요약

| 영역 | 기본계획 | 현재 실행 기준 | 변경 이유 | 현재 닫힘 시점 |
| --- | --- | --- | --- | --- |
| `split-entry shadow` | `2026-04-20`에 `rebase/즉시 재평가/cooldown` 3축 동시 판정 | `2026-04-20 rebase`, `2026-04-21 즉시 재평가`, `2026-04-22 cooldown` 순차 도입 | 동일 세션 원인귀속 불가, audited table `S-1` 반영 | `2026-04-22` |
| `split-entry 판정 조건` | 표본 부족 시 결론 유예 수준의 서술형 | 각 판정 행에 `N_min/Δ_min/PrimaryMetric` 명시 필요 | audited table `S-2` 반영 | `2026-04-20 PREOPEN` |
| `rollback guard` | 문서상 점검 수준 | `reject_rate/partial_fill_ratio/latency_p95/reentry_freq` 정량화 필요 | audited table `S-3` 반영 | `2026-04-20 PREOPEN` |
| `HOLDING 성과판정` | `2026-04-21` 1일차 판정 | `2026-04-22 D+2` 최종판정 | schema 변경 직후 자기참조 오염 방지, audited table `S-4` 반영 | `2026-04-22 POSTCLOSE` |
| `AIPrompt 작업 10` | `2026-04-19` 1차 결과 평가 후 확대 여부 판정 | `2026-04-20`에는 `shadow-only 유지/확대 보류`만 판정, 최종 확대는 `2026-04-22` | `holding_action_applied`, `holding_force_exit_triggered`, `holding_override_rule_version` 관찰축 부족 | `2026-04-22 POSTCLOSE` |
| `AIPrompt 작업 8` | 핵심값 3종 투입 결과 정리 후 완료 후보 | 값 주입은 존재하나 `*_sent` 감사 로그 부족으로 미완료 유지 | 완료 기준과 감사 필드 범위 불일치 | `2026-04-20 POSTCLOSE` 재판정 |
| `원격 canary 운용` | 튜닝축 신규 변경은 원격 canary 선행을 기본값으로 사용 | 현재 튜닝기간은 `신규 원격 canary 강제`를 보류하고, `AI 엔진 A/B` 직전에만 원격 정합화 후 사용 | split-entry/HOLDING 우선순위 집중 + 실험축 분리 원칙 | `2026-04-23 POSTCLOSE` 재판정 |
| `PYRAMID zero_qty Stage 1 반영` | 수량 패치가 유효하면 `PYRAMID/REVERSAL_ADD` 동시 범위로 확장 가능 | 현재 실행 기준은 `SCALPING/PYRAMID bugfix-only`에 한해 `remote 범위확정 -> remote canary 판정 -> main code-load(flag OFF)` 순서로만 허용 | LIVE/OFF 축 혼동 방지 + split-entry/HOLDING 관찰축 보존 + main 선반영 금지 | `2026-04-24 POSTCLOSE` go/no-go |
| `개별 종목 이슈 해석 범위` | scale-in 이슈 중심으로 빠른 수량 패치 논의 가능 | 개별 종목은 `entry gate + latency + liquidity + holding exit` 4축 분해 관찰 후에만 로직 변경 후보화 | 단일 원인 오판 방지 + 기대값 손실의 실제 누수지점 분리 | `2026-04-21 POSTCLOSE` 재확인 |
| `물타기축(AVG_DOWN/REVERSAL_ADD)` | holding-profit-conversion 플랜 기준으로 `2026-04-20~2026-04-21` 관찰/전환 가능 | 현재 활성 플랜에서는 우선순위에서 내려 `일정 확정만` 수행, 실제 재오픈 여부는 `2026-04-24 POSTCLOSE`에 다음주 shadow go/no-go로 판정 | split-entry/HOLDING 우선 + 실주문 변경축 과밀 방지 | `2026-04-23 일정 확정`, `2026-04-24 go/no-go` |
| `장전 리포트 빌드 운영` | 장전에도 필요 시 full build 실행 가능으로 운용 | `PREOPEN`에는 `sanity check` 우선, full build는 `bot_main` 동작 중 차단(락 + override 필요) | `2026-04-20` 장전 부하/장애 재발 방지 | 즉시 적용 (`deploy/run_monitor_snapshot_safe.sh`) |
| `AI 엔진 A/B 착수` | 운영 튜닝과 병행 | 운영 튜닝 종료판정 이후 `remote shadow -> remote canary -> main canary`로 분리 착수 | 원인 귀속 혼선 방지 + 단일축 실험 유지 | `2026-04-24 POSTCLOSE` go/no-go |
| `신규축 실행 방식` | shadow 선행 후 canary | 신규/보완축은 `shadow 금지`, `canary-only` | 영향도 확인을 실거래 경로에서 즉시 검증하고, 다축 실험은 금지 | 즉시 적용 (`2026-04-20`) |
| `broad relax` | `latency/tag/threshold` 확장 후보를 빠르게 재오픈 | `split-entry leakage` 1차 판정 전 재오픈 금지 | 거래수 확대보다 손실축 제거 우선 | split-entry 1차 판정 후 |
| `운영판정` | 실험축별 판정 중심 | `No-Decision Day` 게이트와 `report integrity / event restoration / aggregation quality` 품질게이트 병행 | 잘못된 집계로 잘못된 승격을 막기 위함 | 장후 반복 적용 |
| `baseline source-of-truth` | 문서 baseline과 스냅샷 baseline을 혼용 가능 | `DB 우선 스냅샷 실필드`만 하드 기준으로 사용, 문서 파생값은 raw 산식 추적 전까지 참고치로 격하 | `same_symbol_repeat_flag=55.1%`, rolling trend 등 basis 혼선 정리 필요 | `2026-04-21 POSTCLOSE` |
| `운영 상수 변경 통제` | 하드코딩 제거 중 상수값까지 함께 보정 가능 | `TRADING_RULES` 모델명/투자비율/주문한도/canary 스위치는 별도 명시 승인 없이는 전략 변경 금지 | `2026-04-20` 모델명 오판 재발 방지. 하드코딩 제거와 운영 모델 전략 변경을 분리 | 즉시 적용 (`2026-04-20`) |

## 3. 변경의 의미

### 3-1. 공격성은 낮춘 것이 아니라 방향을 바꿨다

1. 거래수 확대보다 `split-entry soft-stop` 손실축 제거가 먼저라는 점이 더 명확해졌다.
2. HOLDING 축도 `지금 바로 확대`가 아니라 `측정 가능한 운영 로그 축 확보 -> D+2 판정`으로 바뀌었다.
3. 이는 보수화가 아니라 `기대값 개선 실패 확률`을 낮추는 방향의 공격성 조정이다.

### 3-2. 문서 운영도 변경됐다

1. `prompt`는 현재 기준만 남긴 경량 실행본으로 바뀌었다.
2. 계획과 실행의 차이는 이 문서에 남긴다.
3. 정기 성과 baseline은 [plan-korStockScanPerformanceOptimization.performance-report.md](./plan-korStockScanPerformanceOptimization.performance-report.md)로 분리했다.
4. 단, baseline 문서에 적힌 모든 숫자가 곧바로 hard KPI는 아니다. 리포트별 소유 지표와 금지 지표를 먼저 고정한다.

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

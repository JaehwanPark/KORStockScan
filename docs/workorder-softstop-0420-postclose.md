# 작업지시서: 2026-04-20 장후 Soft-Stop 대량발생 RCA 및 즉시 파라미터 확정

작성일: `2026-04-20`  
실행 시점: `2026-04-20 POSTCLOSE 18:20~18:45 KST`  
대상: 운영 트레이더 / Codex  
기준 문서: [2026-04-20-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-20-stage2-todo-checklist.md), [2026-04-17-midterm-tuning-performance-report.md](/home/ubuntu/KORStockScan/docs/2026-04-17-midterm-tuning-performance-report.md)

참조 우선순위:
1. [plan-korStockScanPerformanceOptimization.performance-report.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.performance-report.md)
2. [plan-korStockScanPerformanceOptimization.execution-delta.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.execution-delta.md)
3. [2026-04-20-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-20-stage2-todo-checklist.md)
4. [2026-04-17-midterm-tuning-performance-report.md](/home/ubuntu/KORStockScan/docs/2026-04-17-midterm-tuning-performance-report.md)

---

## 1. 목적

오늘 장중 대량 발생한 `soft-stop`을 장후에 반드시 복기하고, 아래 두 가지를 같은 세션에서 닫는다.

1. 내일 운영에서 가장 먼저 다룰 `원인축 1개`
2. 내일 즉시 적용할 `파라미터 1개`

이 작업은 관찰 메모가 아니라 **운영 판정 작업**이다.  
결론은 `다축 병렬`이 아니라 `1축만` 남겨야 한다.

---

## 2. 절대 원칙

1. 손익 파생 추정치보다 `soft_stop_count`, `soft_stop_rate`, `latency_ratio`, `partial_fill`, `rebase`, `same_symbol_repeat` 같은 raw 운영지표를 우선한다.
2. `same_symbol_repeat`는 raw 산식 추적 전까지 자동으로 root-cause로 단정하지 않는다.
3. `원인축 1개`와 연결되지 않는 파라미터는 오늘 확정하지 않는다.
4. 장후 분석 후에는 **사용자 확인 요청을 반드시 1회 수행**하고, 승인 전에는 추가 파라미터 변경을 하지 않는다.

---

## 3. 분석 입력

아래 항목을 종목별 또는 코호트별로 최소 1회는 분해해 본다.

- `soft_stop_count`
- `soft_stop_rate`
- `latency_ratio`
- `partial_fill_completed_avg_profit_rate`
- `position_rebased_after_fill_events`
- `same_symbol_repeat`
- `fallback 진입 여부`
- `entry_mode(full/partial/split-entry)`

우선 해석 순서:

1. `latency`
2. `partial/rebase`
3. `same-symbol repeat`
4. `holding/exit 판단`
5. `과도한 투자사이즈`

---

## 4. 판정 규칙

### 4-1. 원인축 1개 선정 규칙

아래 중 **오늘 soft-stop 건에 가장 많이 겹친 공통 전조**를 `원인축 1개`로 고정한다.

- `latency`
- `partial/rebase`
- `same-symbol repeat`
- `holding/exit 판단`
- `risk size`

선정 기준:

1. soft-stop 발생 종목 중 중복 출현 비중이 가장 높은 축
2. 내일 운영에서 단일 canary 또는 live 파라미터로 바로 다룰 수 있는 축
3. 다른 축의 하위 증상에 불과한 경우는 제외

### 4-2. 즉시 파라미터 1개 선정 규칙

`원인축 1개`가 정해지면, 그 축에 직접 연결된 **숫자형 파라미터 1개만** 확정한다.

예시:

- `risk size` → `INVEST_RATIO_SCALPING_MAX`, `SCALPING_MAX_BUY_BUDGET_KRW`
- `same-symbol repeat` → 재진입 차단시간, 차단 횟수
- `partial/rebase` → partial fill 최소비율, immediate recheck window
- `holding/exit 판단` → AI early exit 손실 허용폭, 연속 히트 수

금지:

1. 원인축과 무관한 숫자 수정
2. 한 번에 2개 이상 파라미터 확정

---

## 5. 장후 보고 템플릿

아래 형식으로 장후 보고를 작성한다.

```md
## SoftStop0420 판정

- 판정:
  - 원인축 1개 = `<latency | partial/rebase | same-symbol repeat | holding/exit 판단 | risk size>`
  - 즉시 파라미터 1개 = `<파라미터명=값>`

- 근거:
  - soft_stop_count = `<수치>`
  - soft_stop_rate = `<수치>`
  - latency_ratio = `<수치>`
  - partial_fill_completed_avg_profit_rate = `<수치>`
  - rebase_count = `<수치>`
  - same_symbol_repeat = `<수치 또는 해석>`
  - 오늘 soft-stop 종목 공통 전조 = `<한 줄>`

- 다음 액션:
  - 내일 장전 검증 항목 1개 = `<항목>`
  - 적용 방식 = `<live | canary>`
  - 중단조건 = `<한 줄>`
```

---

## 6. 사용자 확인 요청 템플릿

장후 분석이 끝나면 아래 형식으로 **사용자 확인 요청**을 반드시 보낸다.

```md
## 사용자 확인 요청

- 오늘 SoftStop0420 장후 판정 결과, 원인축은 `<원인축>`으로 닫았습니다.
- 즉시 적용 파라미터는 `<파라미터명=값>` 1개만 제안합니다.
- 보류한 다른 축은 `<축명>` 입니다.

확인 요청:
1. 위 원인축/파라미터로 내일 운영 반영을 진행할지
2. 아니면 오늘은 기록만 남기고 반영은 보류할지
```

이 확인 요청 전에는 추가 파라미터 조정을 하지 않는다.

---

## 7. 완료 기준

1. `원인축 1개`가 문서에 확정됨
2. `즉시 파라미터 1개`가 문서에 확정됨
3. 사용자 확인 요청 메시지가 1회 작성됨
4. 내일 장전 검증 항목이 1개 기록됨

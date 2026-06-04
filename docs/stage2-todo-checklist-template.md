# Stage2 To-Do Checklist Template

목적: 날짜별 `docs/checklists/YYYY-MM-DD-stage2-todo-checklist.md`의 상단 운영 형식을 공통화한다.  
기준: 상세 정책/용어/가드는 [plan-korStockScanPerformanceOptimization.rebase.md](./plan-korStockScanPerformanceOptimization.rebase.md) §1~§6을 따르고, 날짜별 checklist 상단에는 `오늘 목적`과 `오늘 강제 규칙`만 짧고 강하게 유지한다.
튜닝 데이터 기준: `clean_tuning_baseline_date=2026-06-04`, `clean_tuning_baseline_ts_kst=2026-06-04T14:29:09+09:00` 이후 데이터만 현재 tuning decision input으로 허용한다.

---

## 사용 규칙

1. 날짜별 checklist 상단은 항상 아래 2개 섹션 순서를 유지한다.
   - `## 오늘 목적`
   - `## 오늘 강제 규칙`
2. `오늘 목적`은 당일 핵심 판정/승격/보류 축만 3~6개 bullet로 적는다.
3. `오늘 강제 규칙`은 아래 공통 bullet를 기본값으로 쓰고, 당일 예외는 최소한으로만 추가한다.
4. PREOPEN checklist도 같은 템플릿을 쓰되, PREOPEN은 전일 준비완료 carry-over 승인/롤백 슬롯만 받는다.
5. 날짜별 checklist는 장문의 정책 반복본 대신 이 템플릿과 `Plan Rebase`를 참조한다.
6. `shadow/canary/cohort` 별도 workorder는 LDM 전환 이후 active 기준문서에서 제외한다. 현재 원칙과 open state는 `Plan Rebase` §1~§8, 실행 항목은 일일 checklist, 산출물 계약은 report traceability가 소유한다.
7. 새 lifecycle bucket, runtime family, sim-auto/live-auto 후보, cohort 상태, 제외 규칙이 생기면 같은 change set에서 `Plan Rebase` active/open state 또는 해당 일일 checklist와 report traceability/source contract를 갱신한다.
8. live 축 교체 또는 stage-disjoint 병렬 검토가 있으면 checklist 메모에 `stage`, `manipulation point`, `cohort tag`, `rollback guard`, `apply timing`, `post-apply attribution`을 남긴다.

---

## 상단 템플릿

```md
## 오늘 목적

- `<당일 결론 1>`
- `<당일 결론 2>`
- `<당일 검증축/주병목/승격후보>`
- `<운영상 분리 관찰 또는 적용 제한>`

## 오늘 강제 규칙

- 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이며 상세 기준은 `Plan Rebase` §1~§6을 따른다.
- 튜닝 데이터 기준은 `clean_tuning_baseline_date=2026-06-04`, `clean_tuning_baseline_ts_kst=2026-06-04T14:29:09+09:00`이다. 기준 이전 raw/report/analytics artifact는 archive/audit evidence로만 보고 EV/rolling/MTD/cumulative tuning, live-auto promotion, runtime approval, pattern lab promotion, real execution quality approval 입력으로 쓰지 않는다.
- live 변경은 동일 단계 내 `1축 canary`만 허용한다. 진입병목축과 보유/청산축은 별개 단계이므로 병렬 canary가 가능하지만, 같은 단계 안에서는 canary 중복을 금지한다.
- 동일 단계 replacement는 `기존 축 OFF -> restart.flag -> 새 축 ON` 순서만 쓴다.
- 관찰창이 끝나면 `즉시 판정 -> 다음 축 즉시 착수`를 기본으로 한다. 이미 수집된 데이터로 닫을 수 있는 판정은 장후/익일로 미루지 않는다.
- `장후/익일/다음 장전` 이관은 예외사유 4종(`단일 조작점 미정`, `rollback guard 미문서화`, `restart/code-load 불가`, `운영 경계상 same-day 반영 불가`) 중 하나로만 허용한다. 막힌 조건과 다음 절대시각이 없으면 이관 판정은 무효다.
- PREOPEN은 전일에 이미 `단일 조작점 + rollback guard + 코드/테스트 + restart 절차`가 준비된 carry-over 축만 받는다.
- 일정은 모두 `YYYY-MM-DD KST`, `Slot`, `TimeWindow`로 고정한다.
- 손익은 `COMPLETED + valid profit_rate`만 사용하고 `full fill`과 `partial fill`은 분리한다.
- live 승인, replacement, stage-disjoint 예외, 관찰 개시 판정에는 `cohort`를 같이 잠근다. 최소 `baseline cohort`, `candidate live cohort`, `observe-only cohort`, `excluded cohort`를 구분하고 `partial/full`, `initial/pyramid`, `fallback` 혼합 결론을 금지한다.
- `ApplyTarget`은 문서에 명시된 값만 사용하고, parser/workorder가 `remote`를 추정하지 않도록 유지한다.
- 다축 동시 변경 금지, 승인 전 `main` 실주문 변경 금지 규칙을 유지한다.
```

---

## 체크 포인트

- future checklist를 새로 만들 때는 이 템플릿을 먼저 복사한 뒤 task section을 채운다.
- same-day에 분해 가능한 축을 `다음 장전 검토`로 넘기면 템플릿 위반이다.
- PREOPEN checklist가 carry-over 승인 슬롯이 아니라 설계 검토 슬롯으로 변질되면 템플릿 위반이다.
- POSTCLOSE checklist는 별도 shadow/canary 문서 확인 항목을 만들지 않는다. LDM/ADM/lifecycle bucket 상태는 `ThresholdDailyEVReport`, `RuntimeApplyGapDirectiveReview`, `HumanInterventionSummary`, `CodeImprovementWorkorderReview` 같은 산출물 기반 항목에서 닫는다.
- 새 `shadow` 경로를 코드에 추가하면 템플릿 위반이다. 새 관찰/후보 축은 `runtime_effect`, `decision_authority`, `source_quality_gate`, `forbidden_uses`, `stage`, `rollback guard`를 산출물 계약에 포함해야 한다.
- 새 cohort를 문서/코드/리포트에서 만들고 checklist 또는 report/source contract에 잠금 필드를 같은 change set에서 갱신하지 않으면 템플릿 위반이다.

# Stage2 To-Do Checklist Template

목적: 날짜별 `docs/YYYY-MM-DD-stage2-todo-checklist.md`의 상단 운영 형식을 공통화한다.  
기준: 상세 정책/용어/가드는 [plan-korStockScanPerformanceOptimization.rebase.md](./plan-korStockScanPerformanceOptimization.rebase.md) §1~§6을 따르고, 날짜별 checklist 상단에는 `오늘 목적`과 `오늘 강제 규칙`만 짧고 강하게 유지한다.

---

## 사용 규칙

1. 날짜별 checklist 상단은 항상 아래 2개 섹션 순서를 유지한다.
   - `## 오늘 목적`
   - `## 오늘 강제 규칙`
2. `오늘 목적`은 당일 핵심 판정/승격/보류 축만 3~6개 bullet로 적는다.
3. `오늘 강제 규칙`은 아래 공통 bullet를 기본값으로 쓰고, 당일 예외는 최소한으로만 추가한다.
4. PREOPEN checklist도 같은 템플릿을 쓰되, PREOPEN은 전일 준비완료 carry-over 승인/롤백 슬롯만 받는다.
5. 날짜별 checklist는 장문의 정책 반복본 대신 이 템플릿과 `Plan Rebase`를 참조한다.
6. 매일 `POSTCLOSE`에는 [workorder-shadow-canary-runtime-classification.md](./workorder-shadow-canary-runtime-classification.md)를 참조한 `shadow/canary/cohort 분류 및 정리` 항목을 최소 1건 포함한다.
7. 새 `shadow/canary` 경로를 추가하거나 기존 항목의 분류 상태를 바꾸면, 같은 change set에서 [workorder-shadow-canary-runtime-classification.md](./workorder-shadow-canary-runtime-classification.md) 판정표를 먼저 갱신한다. `POSTCLOSE` daily review는 이 규칙의 대체가 아니다.
8. 새 cohort가 생기거나 기존 cohort의 상태/이름/제외규칙이 바뀌면, 같은 change set에서 위 workorder의 `현행 Decision Cohort Inventory`를 갱신하고 checklist에도 `baseline cohort / candidate live cohort / observe-only cohort / excluded cohort / rollback owner / cross-contamination check`를 남긴다.

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
- live 변경은 `1축 canary`만 허용하고, replacement도 `기존 축 OFF -> restart.flag -> 새 축 ON` 순서만 쓴다.
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
- POSTCLOSE checklist에는 `shadow/canary/cohort 런타임 분류/정리` 항목을 넣고, Source는 [workorder-shadow-canary-runtime-classification.md](./workorder-shadow-canary-runtime-classification.md)로 고정한다.
- 새 `shadow/canary`를 코드에 추가하고 판정표를 같은 change set에서 갱신하지 않으면 템플릿 위반이다.
- 새 cohort를 문서/코드/리포트에서 만들고 inventory나 checklist 잠금 필드를 같은 change set에서 갱신하지 않으면 템플릿 위반이다.

### POSTCLOSE 기본 항목 예시

```md
- [ ] `[CodeDebtNNNN] shadow/canary/cohort 런타임 분류/정리 판정` (`Due: YYYY-MM-DD`, `Slot: POSTCLOSE`, `TimeWindow: 18:40~18:55`, `Track: Plan`)
  - Source: [workorder-shadow-canary-runtime-classification.md](./workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: 당일 변경/관찰 결과를 기준으로 `remove`, `observe-only`, `baseline-promote`, `active-canary` 중 변동이 필요한 항목이 있는지 닫고, live 전환에 쓰는 cohort도 `baseline-decision / active-canary-decision / provisional-stage-disjoint / observe-only / excluded` 상태로 잠근다.
  - why: `shadow 금지`, `canary-only`, `baseline 승격` 원칙을 코드/문서 상태와 매일 다시 맞춰야 다음 기대값 개선축의 원인귀속이 흐려지지 않는다.
  - 다음 액션: 상태 변경이 있으면 checklist와 관련 기준문서에 함께 반영하고, 변경이 없으면 `변동 없음`과 근거를 남긴다. live 축 교체 또는 stage-disjoint 병렬 검토가 있었다면 `baseline cohort / candidate live cohort / observe-only cohort / excluded cohort / rollback owner / cross-contamination check` 6개 잠금 필드도 같은 메모에 함께 적는다.
```

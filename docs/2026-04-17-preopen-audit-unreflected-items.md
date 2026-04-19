# 2026-04-17 PREOPEN 미반영 항목 Audit

작성일: 2026-04-17  
감사 대상: `docs/2026-04-17-preopen-judgment-basis-for-auditor.md`  
감사 기준: 미반영 항목 중 "더 모니터링 후 판단" vs "지금 판단 가능한데 연기된 건" 분류

휴일 보정: `2026-04-18~2026-04-19`는 휴일이므로 후속 일정 기준일을 `2026-04-20`으로 재배치함.

---

## 0. 반영 결과 (2026-04-17 07:31 KST)

아래 지적사항은 `docs/2026-04-17-stage2-todo-checklist.md` 및 관련 문서에 반영 완료.

1. `SCALP lock 분리 vs 롤백 선택`:
   - `롤백 우선`으로 고정했고, 코드에서 `loss_fallback_probe`의 `skip_add_judgment_lock` 우회 제거 적용.
2. `scalping_exit schema shadow 착수 일정`:
   - `Due/Slot/TimeWindow`를 체크리스트에 명시.
3. `GH_PROJECT_TOKEN 동기화 오분류`:
   - 모니터링 대기 항목이 아닌 운영장애/수동동기화 항목으로 분리 기록.
4. `올릭스/제우스 데이터 해석 갭`:
   - `제우스 timeout cohort`, `올릭스 add_lock cohort` 분리 기준으로 체크리스트/플랜 문서에 반영.
5. `장후 체크리스트 3건`:
   - `착수 또는 보류 사유 기록` 조건으로 모두 판정/근거/다음 액션까지 기록.

---

## 1. 미반영 항목 분류 요약

| 항목 | 미반영 사유 | 판단 |
|---|---|---|
| latency canary 추가 완화 (tag/min_score) | bugfix-only 실표본 미확인 | 연기 타당 |
| SCALP loss_fallback 실전 전환 | fallback_candidate=0건, lock충돌 25% | 연기 타당 (하위 결정 미진) |
| SCANNER 일반 포지션 timeout (shadow-only) | 1일치 표본 수집 전 | 연기 타당, 데이터 해석 갭 있음 |
| scalping_exit action schema 분리 | shadow-only 선행 미완료 | 연기 타당, 착수 일정 미기입 |
| GH_PROJECT_TOKEN 자동화 동기화 | 토큰 누락 | **연기 사유 아님 — 즉시 실행 가능** |
| 장후 체크리스트 3건 (AIPrompt P2/작업7/작업9) | 미착수 | 오늘 장후 처리 여부 확인 필요 |

---

## 2. 항목별 상세 Audit

### 2-1. latency canary 추가 완화 — 연기 타당

- bugfix-only 잠재 복구 `110건` vs min_score 80 완화 `490건`, 리스크 차이 4.5배.
- 실표본 없이 추가 완화 승인은 근거 부족.
- 후속 체크리스트에 `Due: 2026-04-20, Slot: PREOPEN`으로 등록되어 있어 재판정 경로 열려 있음.
- **판정: 문제 없음.**

---

### 2-2. SCALP loss_fallback 실전 전환 — 연기 타당하나 하위 결정 미진

- 실전 전환 미승인은 타당 (`fallback_candidate=True` 0건, lock 충돌 25%).
- **문제**: lock 분리 vs 롤백 선택이 아직 결정되지 않음.
  - `skip_add_judgment_lock` 롤백은 즉시 원복 가능.
  - 별도 lock key 분리는 구현 공수 필요.
  - 어느 축으로 갈지는 장중 데이터가 필요한 판단이 아닌 구조적 결정이므로 오늘 안으로 확정 가능했음.
- 후속 체크리스트에 `Due: 2026-04-20`으로 이월됐고 선택지가 고정되지 않은 상태.
- **판정: 연기 자체는 타당, lock 분리 vs 롤백 방향은 오늘 결정 가능한 건.**

---

### 2-3. SCANNER 일반 포지션 timeout shadow — shadow-only 판단 타당, 데이터 해석 갭

shadow-only 판단 자체는 타당하나 `add_blocked_lock_2026-04-16` 데이터에서 설명이 빠진 패턴이 있음.

| 종목 | blocked_count | held_sec | stagnation_cohort | 주목점 |
|---|---:|---:|---|---|
| 올릭스 | 416 | 461 | **false** | threshold 600s 미달인데 blocked 최다 |
| 롯데쇼핑 | 397 | 675 | true | timeout shadow 대상 |
| 파라다이스 | 194 | 1013 | true | — |
| 파미셀 | 191 | 777 | true | — |
| 제우스 | 159 | **3348** | true | held_sec 56분, 극단적 표류 — 판정 근거서 미언급 |

**갭 1 — 올릭스 패턴**: held_sec=461로 timeout threshold(600s) 미달이므로 stagnation=false. 판정 근거서에서 올릭스를 timeout shadow 대상으로 언급하고 있으나, 실제는 반복 ADD lock 차단 패턴이다. `scanner_never_green_timeout_shadow` 로직 커버 범위와 충돌 가능성 있음.

**갭 2 — 제우스 미언급**: held_sec=3348(약 56분)으로 데이터 내 가장 극단적인 표류 케이스인데 판정 근거서에서 전혀 언급 없음. shadow 설계 시 포함 여부 불명확.

- **판정: shadow-only 연기는 타당. 올릭스 패턴 분리 여부와 제우스 포함 여부를 shadow 조건 설계 시 명시 필요.**

---

### 2-4. scalping_exit action schema 분리 — 연기 타당, 착수 일정 미기입

- 실전 미포함은 타당 (원인 귀속 희석 리스크).
- 진행 순서는 이미 확정됨: `파싱 양방향 호환 → HOLDING schema shadow-only → parse/미체결/지연 가드 통과 시 canary`.
- **문제**: shadow-only 구현 착수는 모니터링 결과와 무관한 구현 결정인데, 후속 체크리스트에 Due 날짜가 없음.
- **판정: 연기 타당. shadow-only 착수 일정을 체크리스트에 추가 필요.**

---

### 2-5. GH_PROJECT_TOKEN 자동화 동기화 — 연기 항목이 아닌 인프라 장애

- 근거서 §4에서 "다음 액션: 권한 보강 후 재실행"으로 기록됨.
- 토큰 발급/설정 문제로, 실표본 수집이나 모니터링 대기가 필요한 항목이 아님.
- 판정 미반영 항목과 인프라 미완료 항목이 같은 카테고리에 묶여 있어 우선순위가 희석됨.
- **판정: 즉시 처리 가능. 미반영 항목이 아닌 운영 장애로 분리 추적 필요.**

---

### 2-6. 장후 체크리스트 3건 — 오늘 처리 여부 불명확

미완료 항목:

- `[ ] AIPrompt P2 HOLDING 포지션 컨텍스트 주입` 착수 또는 보류 사유 기록
- `[ ] AIPrompt 작업 7 WATCHING 선통과 조건 문맥 주입` 착수 또는 보류 사유 기록
- `[ ] AIPrompt 작업 9 정량형 수급 피처 이식 1차` helper scope 확정

- 오늘 장후(15:30~)에 처리해야 하는 항목이 근거서에 반영되지 않은 상태.
- 특히 P2 착수 여부는 Stage 2 전체 진행 방향에 영향을 주며, 미결 시 `2026-04-20 PREOPEN` 판정 입력이 빠짐.
- **판정: 장후 완료 여부를 근거서 또는 체크리스트에 반영 필요.**

---

## 3. 지적 사항 정리

### 3-1. 판단 가능한데 연기된 건

| 항목 | 지적 내용 |
|---|---|
| SCALP lock 분리 vs 롤백 선택 | 실표본 불필요한 구조적 결정인데 내일로만 이월됨 |
| scalping_exit schema shadow 착수 일정 | 순서는 정해졌으나 체크리스트 Due 미기입 |

### 3-2. 오분류 항목

| 항목 | 지적 내용 |
|---|---|
| GH_PROJECT_TOKEN 동기화 | 모니터링 대기 항목이 아닌 인프라 장애 — 별도 추적 필요 |

### 3-3. 데이터 해석 갭

| 항목 | 지적 내용 |
|---|---|
| 올릭스 stagnation=false + blocked 최다 | timeout shadow 설계 커버 범위와 충돌 가능 — 별도 분류 검토 필요 |
| 제우스 held_sec=3348 미언급 | shadow 후보 포함 여부 불명확 |

---

## 4. 정상 연기 확인 (모니터링 후 재판정 필요)

아래 3건은 연기 근거 충분, 재판정 경로도 체크리스트에 등록되어 있어 문제 없음.

1. **latency canary 추가 완화** — bugfix-only 실표본(`latency_canary_applied`, `low_signal` 분포) 확인 후 `2026-04-20 PREOPEN` 재판정.
2. **SCALP loss_fallback 실전 전환** — lock 충돌 해소 및 fallback_candidate 실효성 확인 후 재판정.
3. **SCANNER timeout shadow 표본 수집** — 1일치 `scanner_never_green_timeout_shadow` 후보 로그 수집 후 false-positive 비율 확인.

# 2026-04-17 감사보고서 — Noon 작업결과서 vs 누적매매실적 비교

작성일: 2026-04-17  
감사 대상: `2026-04-17-noon-followup-auditor-report.md` (이하 "noon 보고서")  
비교 기준: `2026-04-17-stage2-todo-checklist.md`, `server_comparison_2026-04-17.md`, `softstop-after-partial-fill-analysis.md`, `ajouib-protect-trailing-mislabel-audit.md`, `komipharm-holding-monitoring-check.md`  
감사 범위: 결정 지연, 판단 부실, 실적 불일치, 미반영 이슈

---

## 1. 종합 감사 의견

> **조건부 적정** — noon 보고서의 4개 핵심 판정 항목은 근거가 충분하고 실전 반영까지 완료됐다. 그러나 **3개 항목에서 결정 지연 또는 판단 부실**이 확인됐으며, 장중 실매매에서 발생한 손실 케이스 2종(아주IB투자 stale protection, 코미팜 매도거절)은 오전 중 원인 파악이 됐음에도 한 건은 코드 수정이 장후로 이월됐고 한 건은 재발 모니터링 기준이 문서화되지 않았다.

---

## 2. noon 보고서 4개 판정 항목 검토

### 2-1. latency canary bugfix-only 실표본 재판정

| 구분 | 내용 |
|---|---|
| 판정 결과 | 적정 |
| 근거 충분성 | 로컬/원격 수치 모두 제시됨 (`canary_applied 로컬=19, 원격=3`) |
| 반영 여부 | 추가 완화 미승인 유지 — 체크리스트와 일치 |
| 이슈 없음 | — |

단, 로컬과 원격 간 `canary_applied` 격차(19 vs 3)에 대한 원인 분석이 noon 보고서에 없다. 이 차이는 로컬/원격 서버의 signal 분포 차이 또는 코드 배포 시점 차이에서 기인할 수 있으므로, 다음 PREOPEN 판정 시 별도 확인이 필요하다.

---

### 2-2. split-entry rebase quantity 감사 기준 확정

| 구분 | 내용 |
|---|---|
| 판정 결과 | 적정 |
| 근거 충분성 | 16건 중 10건 플래그, 분포까지 제시 |
| 반영 여부 | `split_entry_rebase_integrity_shadow` stage 코드 반영, 테스트 통과 |
| 미비 사항 | shadow 수집 시작 시점이 bot 재기동 후임 — 재기동 완료 여부가 noon 보고서에 명시되지 않음 ⚠️ |

**감사 지적 (경미)**: noon 보고서 3-3절에서 "사용자가 직접 재기동할 예정"이라고만 기술하고 실제 재기동 완료 여부, 완료 시각을 기록하지 않았다. 재기동 전 발생한 장중 표본은 이 shadow에서 빠지므로 수집 범위 손실이 발생했을 가능성이 있다.

---

### 2-3. split-entry 즉시 재평가 shadow 설계 확정

| 구분 | 내용 |
|---|---|
| 판정 결과 | 적정 |
| 근거 충분성 | `partial 이후 확대` 코호트 수치와 shadow 파라미터 명시 |
| 반영 여부 | `split_entry_immediate_recheck_shadow` stage 반영, 테스트 통과 |
| 이슈 없음 | — |

---

### 2-4. same-symbol cooldown 초안 유지 / 장후 최종 판정 보류

| 구분 | 내용 |
|---|---|
| 판정 결과 | 조건부 적정 — 보류 사유 자체는 타당 |
| 이슈 | 최종 판정이 장후(15:20~15:40)로 명시됐으나 체크리스트에서 미완료(☐) |

**감사 지적 (중요)**: 2026-04-16에 이미 지투파워가 같은 날 3회 반복 손절됐다. 이 패턴은 4월 16일 보고서에 기록됐음에도 cooldown 설계 결정이 4월 17일 장후로 다시 연기됐다. 연기 판단 자체의 근거(장후 추가 표본 필요)는 문서화돼 있으나, 이미 2일에 걸쳐 반복 확인된 패턴임을 고려할 때 오전 중 1축 shadow 활성화 결정을 더 일찍 내릴 수 있었다. 또한 체크리스트 항목(`15:20~15:40`)이 장 종료 후 처리됐는지 여부가 noon 보고서 작성 시점 기준으로 미완료 상태이며, 본 감사 시점에도 미체크 상태다.

---

## 3. 누적 매매실적 비교 감사

### 3-1. 실적 현황 (server_comparison 기준)

| 지표 | 로컬(메인) | 원격 | 델타 |
|---|---:|---:|---:|
| total_trades | 45 | 30 | -15 |
| completed_trades | 43 | 27 | -16 |
| open_trades | 2 | 3 | +1 |
| post_sell evaluated_candidates | 46 | 25 | -21 |
| Performance Tuning | — | **timeout** | — |
| Entry Pipeline Flow | — | **timeout** | — |

**감사 지적 (중요)**: 원격 `Performance Tuning`과 `Entry Pipeline Flow` API가 모두 `TimeoutError`로 응답 실패 상태다. noon 보고서는 이 원격 API 장애를 한 줄도 언급하지 않는다. 로컬 대비 원격의 trades가 -15건 적고 holding_events가 -2,650건 적은 상황에서, 원격 퍼널 지표를 확인하지 못하면 어느 단계에서 진입 격차가 발생했는지 판단할 수 없다. 원격 timeout 해소 또는 대체 판정 경로가 noon 보고서에서 완전히 누락돼 있다.

---

### 3-2. 아주IB투자 stale protection 손실 건 (id=2710, id=2722)

| 항목 | 내용 |
|---|---|
| 발생 시각 | 11:47:55 (id=2710), 12:13:37 (id=2722) |
| 문제 | 이전 PYRAMID 포지션의 `trailing_stop_price=12,607원`이 초기화되지 않아 신규 포지션에 stale 보호선으로 작동 |
| 손익 | id=2710: -0.47%, id=2722: -0.15% (둘 다 "익절 완료"로 오표시) |
| 원인 파악 시각 | 12:27 KST (체크리스트 기록 기준) |
| 코드 수정 결정 | **즉시 수정 보류 — 장후 계획으로 이월** |

**감사 지적 (중요)**: id=2710은 11:47에 발생했다. 원인 분석이 12:27에 완료됐으므로 이후 장중에도 동일한 stale protection 발동 위험이 존재하는 상태로 장 후반부가 운영됐다. noon 보고서는 이 이슈를 언급하지 않았으며, 감사 대상 항목으로도 포함되지 않았다. 두 건 모두 `익절 완료`로 오표시돼 운영자 판단을 왜곡할 수 있다.

코드 수정을 "즉시 보류"한 판단은 회귀 테스트 선행 원칙 측면에서 이해 가능하나, 최소한 noon 보고서에 리스크 인지 사항으로 명시했어야 한다.

---

### 3-3. 코미팜 sell_order_failed → COMPLETED 오판정 건 (id=2602)

| 항목 | 내용 |
|---|---|
| 발생 | `125주 매도가능` 문자열이 있을 때 무조건 COMPLETED 전환 |
| 수정 | 07:47 KST에 로컬/원격 코드 반영 + 테스트 3건 통과 |
| 원격 재기동 | 완료 (bot_main.py 신규 PID 확인) |
| 미비 사항 | id=1664 유령 shadow 이벤트(`hard_time_stop_shadow` 잔존) 후속 처리는 다음 PREOPEN으로 이월 |

**감사 지적 (경미)**: 코드 수정과 재기동은 오전에 완료됐으나, id=1664 포지션 객체의 유령 shadow 이슈 (`COMPLETED` 전환 후에도 `hard_time_stop_shadow` 재발)는 명시적인 재발 방지 기준 없이 이월됐다. 이 이슈가 오늘 장중 에러 로그에 잡혔는지 여부가 점검되지 않았다.

---

### 3-4. split-entry soft stop 실적 — noon 보고서 수치와 실적 비교

| 항목 | noon 보고서 | softstop 분석 문서 |
|---|---|---|
| 메인 soft stop 건수 | 16건 | 16건 ✓ |
| 원격 soft stop 건수 | 7건 | 7건 ✓ |
| 메인 정합성 플래그 | 10건 | 10건 ✓ |
| 메인 partial 후 확대 | 13건 | 13건 ✓ |

수치 일치. 단, softstop 분석 문서 하단의 "검증 결과" 섹션에서는 메인 2026-04-17 = **10건**, rebase 정합성 이상 = **5건**으로 기재돼 있어 noon 보고서의 16건/10건과 불일치한다.

**감사 지적 (경미)**: `softstop-after-partial-fill-analysis.md` 섹션 6("검증 결과")의 요약 수치(`메인 2026-04-17: 10건`, `rebase 이상: 5건`)가 본문 수치(16건, 10건)와 내부 불일치 상태다. 이 문서를 후속 분석 입력으로 사용할 경우 혼선이 발생할 수 있다.

---

## 4. 결정 지연 항목 정리

| # | 항목 | 지연 수준 | 판단 |
|---|---|---|---|
| 1 | **same-symbol cooldown 최종 판정** | 2026-04-16부터 반복 확인된 패턴임에도 4월 17일 장후로 2차 연기. 장후 체크리스트도 미완료 상태 | **결정 지연 — 중간 수준** |
| 2 | **아주IB투자 stale protection 코드 수정** | 12:27에 원인 파악 완료. 장후로 수정 이월. 이후 장중에도 동일 위험 잔존 | **결정 지연 — 중간 수준** |
| 3 | **원격 API timeout 대응** | Performance Tuning / Entry Pipeline Flow 모두 timeout. noon 보고서에서 완전 미언급 | **판단 부실 — 누락** |
| 4 | **bot_main.py 재기동 완료 여부 기록** | shadow 2종 수집 범위가 재기동 시점에 의존. 완료 시각 미기록 | **판단 부실 — 경미** |
| 5 | **id=1664 유령 shadow 재발 점검** | 오전 이후 당일 재발 여부 미확인 | **판단 부실 — 경미** |

---

## 5. 미완료 체크리스트 항목 (본 감사 시점 기준)

| 항목 | Due | 슬롯 | 상태 |
|---|---|---|---|
| split-entry soft-stop 동일종목 cooldown shadow 여부 판정 | 2026-04-17 | POSTCLOSE 15:20~15:40 | **미완료** |
| split-entry partial-only timeout shadow 기준 확정 | 2026-04-20 | POSTCLOSE 15:30~15:50 | 미완료 (예정) |
| protect_trailing_stop 음수청산 라벨/상태초기화 분리 수정안 확정 | 2026-04-20 | PREOPEN 09:00~09:20 | 미완료 (예정) |
| HolidayReassign AIPrompt 작업 9 정량형 수급 피처 이식 1차 착수 여부 판정 | 2026-04-17 | POSTCLOSE 15:30~15:45 | **미완료** |
| HolidayReassign 작업 6/7 보류 항목 다음 실행시각 재기록 | 2026-04-17 | POSTCLOSE 15:45~16:00 | **미완료** |

---

## 6. 감사 권고사항

### 권고 1 (즉시) — 원격 API timeout 원인 파악 및 기록

장 마감 후 또는 2026-04-20 PREOPEN 이전에 원격 `performance-tuning` / `entry-pipeline-flow` timeout 원인을 파악하고 해소 여부를 stage2 체크리스트에 기록한다. 원격 퍼널 수치 없이 로컬/원격 진입 건수 차이(-15건)의 원인을 판단할 수 없다.

### 권고 2 (즉시) — same-symbol cooldown 오늘 장후 최종 판정 완료

체크리스트 Due가 2026-04-17 POSTCLOSE로 명시돼 있다. 2026-04-16부터 2회 이상 반복 확인된 패턴이므로 오늘 내 최소 shadow ON/OFF 결정을 완료하고 체크를 닫아야 한다.

### 권고 3 (2026-04-20 PREOPEN) — stale protection 코드 수정 및 회귀테스트 우선 진행

`protect_trailing_stop` 음수 손익 라벨 교정과 `trailing_stop_price/hard_stop_price/protect_profit_pct` 초기화 로직은 장중에도 동일한 비정상 청산을 유발할 수 있는 live bug다. 2026-04-20 PREOPEN 9:00~9:20 슬롯에서 코드 수정 + 회귀테스트를 완료하고, 동일 종목(아주IB투자) 재진입 케이스를 모니터링한다.

### 권고 4 (2026-04-20 PREOPEN) — bot 재기동 완료 시각과 shadow 수집 시작 시각 문서 고정

noon 이후 shadow stage 2종이 실제로 수집을 시작한 시각을 다음 감사 시점 전에 체크리스트에 역기록한다. 미기록 시 장중 후반 표본의 수집 범위 추정이 불가능하다.

### 권고 5 (2026-04-20 PREOPEN) — softstop 분석 문서 내부 수치 불일치 정정

`softstop-after-partial-fill-analysis.md` 섹션 6의 "검증 결과" 요약을 본문 수치(메인 2026-04-17 = 16건, rebase 이상 = 10건)와 일치시킨다.

---

## 7. 긍정 평가 항목

- split-entry 감사 기준과 shadow 2종 설계를 **같은 날 장중에 코드 반영 + 테스트 통과**까지 완료한 것은 실행 속도 기준으로 적정하다.
- 코미팜 매도거절 버그 수정을 **오전 중 원격 반영 + bot 재기동**까지 마친 것은 신속했다.
- noon 보고서의 4개 판정이 체크리스트 기준과 일치하고 near-realtime으로 문서화된 점은 추적 가능성 면에서 양호하다.
- latency canary 추가 완화 미승인 유지 판정은 실표본 근거가 충분하고 보수적 원칙이 유지됐다.

---

## 8. 참고 문서

- [2026-04-17-noon-followup-auditor-report.md](./2026-04-17-noon-followup-auditor-report.md)
- [2026-04-17-stage2-todo-checklist.md](./2026-04-17-stage2-todo-checklist.md)
- [2026-04-17-softstop-after-partial-fill-analysis.md](./2026-04-17-softstop-after-partial-fill-analysis.md)
- [2026-04-17-ajouib-protect-trailing-mislabel-audit.md](./2026-04-17-ajouib-protect-trailing-mislabel-audit.md)
- [2026-04-17-komipharm-holding-monitoring-check.md](./2026-04-17-komipharm-holding-monitoring-check.md)
- [server_comparison_2026-04-17.md](../data/report/server_comparison/server_comparison_2026-04-17.md)

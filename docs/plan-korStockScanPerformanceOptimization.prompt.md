## 계획: KORStockScan 성능 최적화 실행안 (Session Prompt)

기준 시각: `2026-04-11 KST`  
역할: 다음 세션에서 바로 실행할 우선순위, 완료/잔여 상태, 일단위 모니터링 체크포인트를 고정한다.

이 문서는 `지금 기준의 실행 플랜`만 남긴 경량본이다.  
과거 세부 로그, 장중/장후 해석, 장문 분석은 별도 문서에서만 관리한다.

## 문서 분할 안내

1. 현재 문서(실행 프롬프트)
   - [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)
   - 역할: 지금 기준 실행 순서, 상태, 체크포인트
2. 상세 이력(원본 보관)
   - [plan-korStockScanPerformanceOptimization.archive-2026-04-08.md](./plan-korStockScanPerformanceOptimization.archive-2026-04-08.md)
   - 역할: 과거 구현 내역, 장중/장후 보고, 세부 로그 해석
3. 확인 질문/답변 분리본
   - [plan-korStockScanPerformanceOptimization.qna.md](./plan-korStockScanPerformanceOptimization.qna.md)
   - 역할: 모니터링 기간, canary 길이, 운영 원칙 관련 질답
4. 스캘핑 매매로직 코딩지시
   - [2026-04-10-scalping-ai-coding-instructions.md](./2026-04-10-scalping-ai-coding-instructions.md)
   - 역할: 스캘핑 매매로직 코드개선안(`Phase 0~3`)의 기준 문서
5. Phase 0~1 구현 검토
   - [2026-04-10-phase0-phase1-implementation-review.md](./2026-04-10-phase0-phase1-implementation-review.md)
   - 역할: `Phase 0/1` 완료/미완료 상태의 현재 근거
6. AI 프롬프트 개선 코딩지시
   - [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md)
   - 역할: 프롬프트 개선의 최종 구현 순서
7. 프롬프트 플랜 검토/운영자 메모
   - [2026-04-11-scalping-ai-prompt-plan-review.md](./2026-04-11-scalping-ai-prompt-plan-review.md)
   - [2026-04-11-ai-operator-message-validation.md](./2026-04-11-ai-operator-message-validation.md)
   - 역할: 프롬프트 트랙의 최종 분류와 운영 원칙
8. 다음 영업일 운영 체크리스트
   - [2026-04-13-stage2-todo-checklist.md](./2026-04-13-stage2-todo-checklist.md)
   - 역할: `2026-04-13` 장중/장후 실행표

## 문서 정합성 재점검 결과

### 현재 기준 문서

- 스캘핑 매매로직 기준:
  - `2026-04-10-scalping-ai-coding-instructions.md`
  - `2026-04-10-phase0-phase1-implementation-review.md`
  - `2026-04-13-stage2-todo-checklist.md`
- AI 프롬프트 개선 기준:
  - `2026-04-11-scalping-ai-prompt-coding-instructions.md`
  - `2026-04-11-scalping-ai-prompt-plan-review.md`
  - `2026-04-11-ai-operator-message-validation.md`

### 과거 상태 문서 처리 원칙

- `2026-04-08`, `2026-04-09` 상태 요약은 역사적 맥락으로만 본다.
- `2026-04-08 장마감 기준`, `fallback canary 초기판정`, `초기 cache 튜닝 상태`는 더 이상 현재 상태를 대표하지 않는다.
- 현재 플랜에서는 `완료`, `진행 중`, `잔여`를 `2026-04-10 구현 리뷰`와 `2026-04-11 재검토 결과` 기준으로 다시 쓴다.

## 최종 목표와 접근 원칙

1. 최종 목표는 `손실 억제`가 아니라 `기대값/순이익 극대화`다.
2. 현재 단계는 `1단계: 음수 leakage 제거 + 주문전 차단 구조 분해`다.
3. 스캘핑은 `과감한 적용 + 빠른 피드백`, 스윙은 `정확도 우선 + 표본 축적 우선`으로 분리 운영한다.
4. `한 번에 한 축 canary`, `shadow-only`, `즉시 롤백 가드`는 보수적 철학이 아니라 `원인 귀속 정확도`와 `실전 리스크 관리`를 위한 운영 규율이다.
5. 실전 변경은 `원격 선행`, `본서버 후행`으로만 간다.
6. 해석 기준은 항상 `판정 -> 근거 -> 다음 액션` 순서로 남긴다.

## 현재 상태 요약 (`2026-04-11` 기준)

### 완료된 일

1. 스캘핑 매매로직 `Phase 0/1` 중 아래 항목은 코드 반영 및 구현 검토까지 완료됐다.
   - `0-1 latency reason breakdown`
   - `0-2 expired_armed 분리`
   - `0-3 partial fill sync 검증`
   - `0-4 AI overlap audit`
   - `0-5 live hard stop taxonomy audit`
   - `1-1 리포트 집계 확장`
2. 동일 `Phase 0/1` 변경은 원격 `songstockscan` 코드베이스에도 반영 완료 상태다.
3. 원격 `RELAX-LATENCY-20260410-V1`는 `2026-04-10 14:35 KST` 반영 후 추가 관찰이 필요한 상태다.
4. `RELAX-DYNSTR`는 현재 재오픈보다 `유지 + 재설계` 쪽으로 읽고 있다.
5. `RELAX-OVERBOUGHT`는 표본 부족으로 보류 유지다.
6. 스캘핑 AI 프롬프트 관련 팩트 리포트, 전문가 검토, 운영자 재분류 문서는 작성 완료됐다.

### 진행 중인 일

1. 원격 `RELAX-LATENCY` 추가 관찰 및 운영서버 롤아웃 판단
2. `fetch_remote_scalping_logs` 장중 갱신 파일 읽기 실패 보강 여부 판단
3. `trade_review` 해석에서 `entry_mode/fill quality` 복원 품질 점검
4. 프롬프트 개선 트랙의 최종 구현 순서 고정

### 아직 남아있는 일

1. 스캘핑 매매로직 `0-1b 원격 경량 프로파일링`
2. 스캘핑 매매로직 `Phase 2` 원격 실전 로직 변경
3. 스캘핑 매매로직 `Phase 3` 분석 품질 고도화
4. AI 프롬프트 개선 코드 구현 전반
5. 프롬프트 트랙의 `원격 canary -> 장후 평가 -> 1~2세션 후속 확인`

## 활성 워크스트림

| 워크스트림 | 현재 상태 | 완료된 일 | 남은 일 |
| --- | --- | --- | --- |
| `WS-A 스캘핑 관측/리포트` | `진행 중` | `Phase 0/1` 대부분 반영 완료 | `0-1b`, 리포트 품질 최종 검증 |
| `WS-B 원격 canary/롤아웃` | `진행 중` | `RELAX-LATENCY` 원격 반영, `RELAX-DYNSTR/OVERBOUGHT` 분류 고정 | `2026-04-13~14` 추가 모니터링, `2026-04-15` 판단 |
| `WS-C AI 프롬프트 개선` | `설계 완료 / 미구현` | 팩트/검토/반박/운영자 메모 완료 | `P0~P5` 순차 구현 및 원격 canary |
| `WS-D 보조 운영/데이터 품질` | `진행 중` | `trade_review`, `post_sell`, `pipeline_events` 기반 보강 축 정리 | 원격 fetch 안정화, 추가 파서/대시보드 |

## 후순위/비차단 백로그

아래 항목은 문서에서 빠진 것이 아니라, 현재 `운영서버 롤아웃 판단`의 critical path 밖으로 밀린 상태다.

| 항목 | 현재 상태 | 비고 |
| --- | --- | --- |
| `holding/gatekeeper cache reuse 튜닝` | `보류` | archive/Q&A 문서에 상세 이력 유지 |
| `스윙 Gatekeeper missed case 심화` | `관찰 유지` | 스캘핑 롤아웃 이후 우선순위 재판정 |
| `스캘핑 -> 스윙 자동전환 shadow` | `초안 단계` | 최소 `5거래일 shadow` 전 실전 금지 |
| `post-sell feedback 메인 카드 병합` | `잔여` | 파이프라인은 존재, 메인 리포트 병합만 남음 |
| `이벤트 스키마/JSONL 파서 고도화` | `잔여` | `performance_tuning/trade_review` 직접 소비 고도화 필요 |
| `Dual Persona 실전 승급` | `보류` | 즉시 승급 금지 원칙 유지 |

## 스캘핑 매매로직 코드개선안 반영 상태

### 기준 문서

- [2026-04-10-scalping-ai-coding-instructions.md](./2026-04-10-scalping-ai-coding-instructions.md)
- [2026-04-10-phase0-phase1-implementation-review.md](./2026-04-10-phase0-phase1-implementation-review.md)

### Phase 상태

| Phase | 상태 | 현재 판정 |
| --- | --- | --- |
| `Phase 0` | `대부분 완료` | `0-1b 원격 경량 프로파일링`만 잔여 |
| `Phase 1` | `완료` | 집계/리포트 반영 완료 |
| `Phase 2` | `미착수` | 원격 canary 결과를 더 본 뒤 착수 여부 판정 |
| `Phase 3` | `미착수` | 현재 critical path 아님 |

### 잔여 작업 명세

1. `0-1b 원격 경량 프로파일링`
   - `quote_stale=False latency_block` hot path 후보 1~3개 정리
2. `Phase 2-1 EV-aware latency degrade`
   - 원격 추가 모니터링 후 강화/축소/롤백 결정
3. `Phase 2-2 dynamic strength selective override`
   - `momentum_tag × threshold_profile` 재설계 근거 확보 후만 착수
4. `Phase 3-1 realistic/conservative counterfactual`
5. `Phase 3-2 exit authority 명문화`

## AI 프롬프트 개선작업 반영 상태

### 기준 문서

- [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md)
- [2026-04-11-scalping-ai-prompt-plan-review.md](./2026-04-11-scalping-ai-prompt-plan-review.md)
- [2026-04-11-ai-operator-message-validation.md](./2026-04-11-ai-operator-message-validation.md)

### 현재 고정된 분류

1. `SCALP_PRESET_TP SELL` 문제는 `의도 확인 후 처리`
2. `WATCHING 75 정합화`는 `원격 canary`
3. `HOLDING hybrid`는 `override 조건 명세` 선행
4. `프롬프트 분리`와 `컨텍스트 주입`은 `순차 canary`
5. raw 즉시 제거, OpenAI 라이브 즉시 전환, 본서버 즉시 반영은 계속 보류

### 프롬프트 Phase 상태

| Phase | 상태 | 현재 판정 |
| --- | --- | --- |
| `P0 확인/계측` | `미착수` | 즉시 착수 가능 |
| `P1 판단 기준/프롬프트 분리` | `미착수` | 원격 canary 대상 |
| `P2 컨텍스트 주입` | `미착수` | `HOLDING -> WATCHING` 순차 진행 |
| `P3 피처 패킷 보강` | `미착수` | helper 추출 후 진행 |
| `P4 hybrid/critical` | `미착수` | 후순위 |

### 현재 순서

1. `P0`
   - `SCALP_PRESET_TP SELL` 의도 확인
   - AI 운영계측 추가
   - HOLDING hybrid override 조건 명세
2. `P1`
   - WATCHING 75 정합화 원격 canary
   - WATCHING/HOLDING 프롬프트 물리 분리
3. `P2`
   - `2-A HOLDING 포지션 컨텍스트`
   - `2-B WATCHING 선통과 문맥`
4. `P3`
   - 감사 3값
   - 정량형 수급 피처 이식
5. `P4`
   - HOLDING hybrid 적용
   - HOLDING critical 경량 프롬프트
   - raw 축소 A/B

## 운영서버 롤아웃 판단용 추가 모니터링 기간

### 기본 원칙

- `스캘핑 국소 canary`는 `당일 30~60분 + 장후 평가 + 필요 시 1~2세션 추가`가 기본이다.
- 현재 `RELAX-LATENCY`는 `2026-04-10` 장중 후반 반영으로 표본 시간이 짧았다.
- 따라서 **운영서버 롤아웃 판단 전 추가 모니터링은 최소 `2026-04-14 장후`까지** 필요하다.

### 현재 판단

1. `2026-04-13` = 원격 추가 관찰 1일차
2. `2026-04-14` = 원격 추가 관찰 2일차
3. `2026-04-15 08:00~08:30 KST` = 현재 스캘핑 매매로직 canary의 운영서버 롤아웃 여부를 판단할 수 있는 가장 이른 시점
4. 단, 아래 체크포인트를 충족하지 못하면 `2026-04-15` 롤아웃 판단은 보류하고 `1~2세션` 연장 관찰한다

### 롤아웃 체크포인트

1. `quote_stale=False` 축에서 `submitted` 또는 `holding_started` 개선 근거가 있어야 한다
2. `MISSED_WINNER` 분포가 악화 일변도가 아니어야 한다
3. `full fill vs partial fill` 체결 품질이 유의미하게 악화되지 않아야 한다
4. `preset_exit_sync_mismatch`가 롤아웃을 막을 수준으로 증가하지 않아야 한다
5. `fetch_remote_scalping_logs`와 스냅샷 수집이 재현 가능해야 한다
6. `0-1b 원격 경량 프로파일링` 결과로 hot path 후보가 정리돼 있어야 한다

### 프롬프트 트랙 롤아웃 규칙

- 프롬프트 트랙은 아직 구현 전이므로 현재 시점에는 운영서버 롤아웃 판단 대상이 아니다.
- 프롬프트 축은 구현 후에도 아래 순서를 별도로 따른다.
  1. 원격 1축 canary
  2. `30~60분` 압축 모니터링
  3. 장후 평가
  4. 필요 시 `1~2세션` 추가 관찰
  5. 그 후 본서버 반영 여부 판정

## 일단위 계획 (`2026-04-11` 재작성)

### `2026-04-11` 비시장시간

목표:
- 문서 정합성 확정
- 프롬프트 코딩지시 수정
- 운영서버 롤아웃 판단 기준 고정

완료 기준:
- 현재 문서와 관련 작업지시서 간 모순 제거
- `완료/잔여` 상태가 최신 기준으로 재작성됨

### `2026-04-13` 원격 모니터링 1일차

핵심 목적:
- `RELAX-LATENCY` 추가 표본 확보
- `0-1b 원격 경량 프로파일링` 수행
- `trade_review/fetch_remote` 품질 점검

장전 체크포인트:
1. 원격 `latency remote_v2` 설정 유지 상태 확인
2. 프로파일링 방식 확정
3. `RELAX-LATENCY / RELAX-DYNSTR / RELAX-OVERBOUGHT` 시작 상태 고정
4. 원격 fetch/cron 상태 확인

장중 체크포인트:
1. `AI BUY -> entry_armed -> budget_pass -> submitted` 퍼널 추적
2. `quote_stale=False latency_block` 표본 우선 기록
3. `expired_armed`와 `latency_block` 분리 기록
4. `full fill / partial fill / preset_exit_sync_mismatch` 확인
5. 프로파일링 장중 2회 수집

장후 체크포인트:
1. `RELAX-LATENCY` 유지/강화/축소/롤백 1차 판정
2. `RELAX-DYNSTR` 재오픈 여부 재검토 금지, 재설계 후보만 기록
3. 프로파일링 hot path 후보 1~3개 정리

### `2026-04-14` 원격 모니터링 2일차

핵심 목적:
- `RELAX-LATENCY` 반복 재현성 확인
- 롤아웃 게이트 충족 여부 최종 판단
- 프롬프트 트랙은 여전히 설계/구현 준비만 유지

장전 체크포인트:
1. 전일 판정 반영 상태 확인
2. 롤아웃 게이트 항목별 관측 계획 고정

장중 체크포인트:
1. `quote_stale=False` 개선이 반복되는지 확인
2. `full fill vs partial fill` 체결 품질 재확인
3. `AI overlap audit`, `hard stop taxonomy`, `sync mismatch`가 해석 가능 수준인지 확인

장후 체크포인트:
1. `RELAX-LATENCY` 운영서버 승격 가능/불가 1차 결론
2. 미충족 시 어떤 항목 때문에 연장 관찰하는지 명시
3. `2026-04-15` 장전 판단안 초안 작성

### `2026-04-15` 운영서버 롤아웃 판단 시점

핵심 목적:
- 현재 스캘핑 매매로직 canary의 운영서버 반영 여부를 최종 결정

장전 체크포인트 (`08:00~08:30`):
1. `2026-04-13~2026-04-14` 결과가 롤아웃 체크포인트를 충족하는지 확인
2. 충족 시:
   - 운영서버 `유지/강화/축소/반영` 중 하나 확정
3. 미충족 시:
   - 롤아웃 보류
   - `2026-04-15~2026-04-16` 추가 관찰 계획으로 연장

주의:
- 이 날짜의 판단은 `현재 스캘핑 매매로직 canary`에 대한 것이다.
- `AI 프롬프트 개선` 롤아웃 판단은 별도 일정으로 시작한다.

## 즉시 착수 체크리스트

1. `0-1b 원격 경량 프로파일링` 방식 확정
2. `fetch_remote_scalping_logs` 장중 갱신 파일 실패 대응 여부 결정
3. `SCALP_PRESET_TP SELL` 의도 확인
4. HOLDING hybrid override 조건 명세 문서화
5. WATCHING 75 정합화는 `원격 canary`로만 분류했는지 재확인
6. 프롬프트 분리와 컨텍스트 주입이 같은 단계로 묶이지 않았는지 재확인
7. `2026-04-13~2026-04-15` 체크포인트를 운영 문서에 고정

## 가드레일

1. `near_safe_profit`/`near_ai_exit` 즉시 완화 금지
2. 공통 hard time stop 실전 적용 보류
3. `RISK_OFF` day에서 스윙 완화 금지
4. 듀얼 페르소나 즉시 실전 승급 금지
5. 단일일자 결과 기반의 공통 파라미터 일괄 조정 금지
6. 프롬프트 구조 변경은 본서버 즉시 반영 금지

메모:
- 위 가드레일은 `보수적 운영철학`이 아니라 `공격적 튜닝의 원인 귀속 유지`를 위한 최소 제약이다.

## 작업관리 스택 (신규)

1. 실행 소스는 `GitHub Projects`로 단일화한다.
2. 일정 가시성은 `Google Calendar`로 단방향 동기화한다.
3. 동기화 기준은 `Project Due Date`이며 캘린더는 표시/알림 레이어로만 사용한다.
4. 코덱스 작업지시는 `Issue/Project 링크 + 체크리스트`를 함께 전달한다.
5. 코덱스 작업지시는 `Slot(PREOPEN/INTRADAY/POSTCLOSE)` 기준 자동 분리한다.

운영 파일:
- `.github/workflows/sync_project_to_google_calendar.yml`
- `.github/workflows/sync_docs_backlog_to_project.yml`
- `.github/workflows/build_codex_daily_workorder.yml`
- `src/engine/sync_github_project_calendar.py`
- `src/engine/sync_docs_backlog_to_project.py`
- `src/engine/build_codex_daily_workorder.py`

## 관련 문서

- [2026-04-10-scalping-ai-coding-instructions.md](./2026-04-10-scalping-ai-coding-instructions.md)
- [2026-04-10-phase0-phase1-implementation-review.md](./2026-04-10-phase0-phase1-implementation-review.md)
- [2026-04-13-stage2-todo-checklist.md](./2026-04-13-stage2-todo-checklist.md)
- [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md)
- [2026-04-11-scalping-ai-prompt-plan-review.md](./2026-04-11-scalping-ai-prompt-plan-review.md)
- [2026-04-11-ai-operator-message-validation.md](./2026-04-11-ai-operator-message-validation.md)
- [2026-04-11-github-project-google-calendar-setup.md](./2026-04-11-github-project-google-calendar-setup.md)
- [plan-korStockScanPerformanceOptimization.archive-2026-04-08.md](./plan-korStockScanPerformanceOptimization.archive-2026-04-08.md)
- [plan-korStockScanPerformanceOptimization.qna.md](./plan-korStockScanPerformanceOptimization.qna.md)

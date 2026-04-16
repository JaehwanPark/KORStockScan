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
8. 일자별 운영 체크리스트
   - [2026-04-13-stage2-todo-checklist.md](./2026-04-13-stage2-todo-checklist.md)
   - [2026-04-14-stage2-todo-checklist.md](./2026-04-14-stage2-todo-checklist.md)
   - [2026-04-15-stage2-todo-checklist.md](./2026-04-15-stage2-todo-checklist.md)
   - [2026-04-16-stage2-todo-checklist.md](./2026-04-16-stage2-todo-checklist.md)
   - [2026-04-17-stage2-todo-checklist.md](./2026-04-17-stage2-todo-checklist.md)
   - [2026-04-18-stage2-todo-checklist.md](./2026-04-18-stage2-todo-checklist.md)
   - [2026-04-19-stage2-todo-checklist.md](./2026-04-19-stage2-todo-checklist.md)
   - [2026-04-20-stage2-todo-checklist.md](./2026-04-20-stage2-todo-checklist.md)
   - [2026-04-21-stage2-todo-checklist.md](./2026-04-21-stage2-todo-checklist.md)
   - [2026-04-22-stage2-todo-checklist.md](./2026-04-22-stage2-todo-checklist.md)
   - [2026-04-23-stage2-todo-checklist.md](./2026-04-23-stage2-todo-checklist.md)
   - 역할: `2026-04-13~2026-04-23` 장중/장후 실행표
9. 관찰 축 vs 코드 반영 감사표
   - [2026-04-13-observation-axis-code-reflection-audit.md](./2026-04-13-observation-axis-code-reflection-audit.md)
   - 역할: 관찰 축별 분석결과와 실제 코드/실전 반영 상태를 한 번에 점검
10. AI 프롬프트 트랙 감사표
   - [2026-04-14-ai-prompt-track-audit.md](./2026-04-14-ai-prompt-track-audit.md)
   - 역할: `P0~P5`의 일정/체크리스트 반영/구현 지연 위험을 한 번에 점검
11. 관측/canary 효과 리포트
   - [2026-04-13-observation-canary-effect-report.md](./2026-04-13-observation-canary-effect-report.md)
   - 역할: 관측, canary, shadow, simulation이 실제로 방향 설정에 준 도움과 무효 구간을 수치로 정리

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
5. 실전 변경은 `develop=원격 실험서버`, `main=본서버` 기준으로 운영한다. 원격 실험 반영은 `develop`에서 먼저 만들고, 본서버 승격만 `main`으로 올린다.
6. 메인서버 작업계획이 잡히면 동일 축은 원격 `develop`에 `T-2` 또는 늦어도 `T-1` 영업일 먼저 적용한다. `main`은 원격 장후 판정이 남아 있을 때만 반영한다.
7. 해석 기준은 항상 `판정 -> 근거 -> 다음 액션` 순서로 남긴다.
8. `관찰 축 추가`는 상시 전략이 아니다. `2026-04-14 장후`까지는 이미 고정한 축만 재검증하고, `2026-04-14 장후`에는 반드시 `반영 / 보류+단일축 전환 / 관찰 종료 후 재설계` 중 하나로 결론낸다.
9. 원격 비교검증 `remote_error`는 재발 시 원인 수정 대상으로 다루되, `2026-04-13` 기준 현재 잔여 작업축에는 올리지 않는다.
10. `계측 완료 + 실전반영 확신도 50% 이상`인 축은 같은 주 canary 착수를 기본값으로 한다. 착수하지 않으려면 장후 문서에 명시적 보류 사유를 남긴다.
11. 장후 결론은 `유지/보류` 같은 상태 기록으로 끝내지 않는다. `날짜 + 액션 + 실행시각`이 없으면 결론으로 인정하지 않는다.
12. 서비스 오류/재기동 다발일에는 `No-Decision Day` 모드로 전환한다. 당일은 `분석/복기`만 진행하고, 실전 파라미터 변경/승격은 `리포트 정합성 + 이벤트 복원 + 집계 품질` 3개 게이트 통과 후 익일 장전에만 판정한다.

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

1. `main` 반영 예정 축을 원격 `develop`에 `1~2일 선행` 적용하는 운영계획 재정렬
2. 원격 `RELAX-LATENCY` 추가 관찰 및 `2026-04-14 장후` 운영서버 롤아웃 최종 판단
3. `RELAX-DYNSTR` `momentum_tag` 1축 원격 canary의 `2026-04-15 08:30` 착수 준비
4. `partial fill min_fill_ratio` 원격 canary의 `2026-04-15` 착수 준비
5. `expired_armed` 처리 로직 설계 문서의 `2026-04-15 장후` 완료 준비
6. `AI overlap audit -> selective override` 설계 착수 입력 정리 (`2026-04-16` 이내)
7. `2026-04-15` 장후는 `No-Decision Day`로 운영하며, 게이트 통과 여부만 판정
   - gate-1: report integrity (`COMPLETED + valid profit_rate`)
   - gate-2: event restoration (재기동 구간 상태전이 복원)
   - gate-3: aggregation quality (대시보드 기준일/실보유 분리, full/partial 분리)
   - `2026-04-15 15:55 KST` 실행 결과: `gate-1/2 PASS`, `gate-3 FAIL` → `No-Decision Day 유지`, 신규 canary/승격 보류
8. `2026-04-15 POSTCLOSE` 체크리스트 실행 완료
   - `RELAX-DYNSTR`/`partial fill`/`shadow`/`expired_armed` 항목은 수치 근거를 남겨 1차 종료
   - `task8 감사키 로그`, `shadow EV 확정`, `kt00007/ka10076`는 `사유+재시각`으로 이월
9. `2026-04-15` 감사 후속 검토 결과 기준 최우선 액션 재정렬 완료
   - `P0`: `entry_pipeline` 지표 정의 보정 (`submitted latest` vs `submitted ever` vs `filled`)
   - `P0`: `Gatekeeper fast reuse` / `holding skip` 실패사유 계측 승격
   - `P1`: `aggregation gate` 기준을 `daily_report schema` / `trade_review snapshot schema`로 분리
   - `P1`: `partial fill sync mismatch` 코호트 추적항목 고정

### 아직 남아있는 일

1. `2026-04-16 PREOPEN` `entry_pipeline` 지표 정의 보정
   - `submitted latest` / `submitted ever` / `filled`를 분리해 체결 수와 퍼널 지표를 동시에 설명 가능하게 만든다
   - 수집 목적: 가짜 병목(`submitted 0%`)과 실제 병목을 분리한다
   - 기대값: 주문 제출/체결 전환이 어느 단계에서 끊기는지 명확해져 다음 수정 1축을 직접 고를 수 있다
   - 관찰 종료 기준: `submitted ever`/`filled`만으로 체결 수와 퍼널이 모순 없이 설명되면 종료
   - 구현 단위: `sniper_entry_pipeline_report.py` metric 추가 -> `web/app.py` 카드/표 반영 -> API 응답 검증
2. `2026-04-16 PREOPEN` `Gatekeeper fast reuse` / `holding skip` 실패사유 계측 승격
   - 현재 비율 수치만으로는 원인 귀속이 안 되므로 `reason_codes` 상위 분포를 직접 노출한다
   - 수집 목적: latency를 유발하는 주된 실패사유를 1~2개로 압축한다
   - 기대값: 캐시 키/TTL/조건 완화 중 무엇을 먼저 건드릴지 추정이 아니라 근거로 결정한다
   - 관찰 종료 기준: 상위 실패사유가 2거래일 이상 안정적으로 반복되면 관찰 종료 후 수정 단계로 전환
   - 구현 단위: `sniper_performance_tuning_report.py` breakdown 승격 -> `web/app.py` 시각화 반영 -> snapshot 재생성 검증
3. `2026-04-16 PREOPEN` `aggregation gate` 기준 재정의
   - `daily_report`와 `trade_review snapshot`의 schema 차이를 분리해 잘못된 FAIL 판정을 제거한다
   - 수집 목적: 문서 계약 오류를 데이터 품질 실패로 잘못 해석하는 상태를 제거한다
   - 기대값: `No-Decision Day`가 실제 복원/정합성 결함에만 반응한다
   - 관찰 종료 기준: schema 기준과 gate 검사 대상이 일치하고 동일 사유 재발이 없으면 종료
   - 구현 단위: gate 기준 문서 수정 -> daily report schema 확인 -> checklist 판정 문구 교체
4. `2026-04-16 PREOPEN` `partial fill sync mismatch` 코호트 추적항목 고정
   - `sync_status -> exit_rule -> realized_pnl` 연결이 장후 표에 바로 나오게 만든다
   - 수집 목적: mismatch를 단순 이벤트 수가 아니라 손익영향 기준으로 해석한다
   - 기대값: partial fill 축이 EV 훼손의 주범인지, 우선순위를 낮춰도 되는지 빠르게 판정한다
   - 관찰 종료 기준: `mismatch`와 손익 악화의 연결 여부가 2거래일 연속 같은 결론으로 수렴하면 종료
   - 구현 단위: `trade_review` 또는 `performance_tuning`에 코호트 요약 추가 -> 감사 표 기본 반영 -> 장후 검증 명령 고정
5. 스캘핑 매매로직 `0-1b 원격 경량 프로파일링`
6. `AI overlap audit` 기반 `selective override` 설계 착수 (`2026-04-16` 이내)
7. AI 프롬프트 개선 코드 구현 전반
8. AI 프롬프트 `작업 5/8/10`의 `develop` 선행 적용과 `main` 후행 승격 기준 확정
9. `No-Decision Day` 해제 조건 문서화 및 `2026-04-16 PREOPEN` canary 1축 판정

## 활성 워크스트림

| 워크스트림 | 현재 상태 | 완료된 일 | 남은 일 |
| --- | --- | --- | --- |
| `WS-A 스캘핑 관측/리포트` | `진행 중` | `Phase 0/1` 대부분 반영 완료 | `0-1b`, 리포트 품질 최종 검증 |
| `WS-B 원격 canary/롤아웃` | `진행 중` | `RELAX-LATENCY` 원격 반영, `RELAX-DYNSTR/OVERBOUGHT` 분류 고정 | `main` 예정 축의 `develop T-2/T-1` 선행 적용, `2026-04-14` 장후 결론, `2026-04-15 08:30` `RELAX-DYNSTR` canary/`Phase 2` 착수 |
| `WS-C AI 프롬프트 개선` | `즉시 착수` | 팩트/검토/반박/운영자 메모 완료, `작업 1/2/3` 완료, `작업 4` Deferred | `develop`에 `작업 5/8/10` 선행 적용, `2026-04-16` 1차 평가 후 `main` 승격 여부 결정, `2026-04-17~21` `작업 6/7/9/11/12` 고정 |
| `WS-D 보조 운영/데이터 품질` | `진행 중` | `trade_review`, `pipeline_events` 기반 보강 축 정리 | `partial fill min_fill_ratio` canary, `expired_armed` 설계, `AI overlap selective override` |

## 원격 선행 적용 운영계획

| 축 | `develop` 원격 실험서버 | `main` 본서버 |
| --- | --- | --- |
| `RELAX-LATENCY` | `2026-04-14` 장후 결론 확정 | `2026-04-15` 장전/장중 반영 여부 결정 |
| `RELAX-DYNSTR momentum_tag 1축` | `2026-04-15 08:30` canary 시작 | `2026-04-16` 장후 승격 여부 판단 |
| `partial fill min_fill_ratio` | `2026-04-15 08:30` canary 시작 | `2026-04-16` 장후 승격 여부 판단 |
| `AIPrompt 작업 5/8/10` | `2026-04-14 POSTCLOSE` 착수, `2026-04-15~16` 원격 검증 | `2026-04-16` 이후 장후 판정이 남는 경우만 승격 |

운영 메모:
- `main` 작업계획에는 반드시 대응하는 `develop` 선행 적용 일자가 같이 있어야 한다.
- 같은 축을 `main`에 먼저 적용하는 일정은 금지한다.
- `develop` 선행 적용이 누락된 항목은 장후 체크리스트에서 `미착수`가 아니라 `계획 오류`로 기록한다.

## 후순위/비차단 백로그

아래 항목은 문서에서 빠진 것이 아니라, 현재 `운영서버 롤아웃 판단`의 critical path 밖으로 밀린 상태다.

| 항목 | 현재 상태 | 비고 |
| --- | --- | --- |
| `holding/gatekeeper cache reuse 튜닝` | `보류` | archive/Q&A 문서에 상세 이력 유지 |
| `스윙 Gatekeeper missed case 심화` | `관찰 유지` | 스캘핑 롤아웃 이후 우선순위 재판정 |
| `스캘핑 -> 스윙 자동전환 shadow` | `초안 단계` | 최소 `5거래일 shadow` 전 실전 금지 |
| `post-sell feedback 메인 카드 병합` | `Parked` | 현재 잔여 작업축에서 제외, entry/holding 직접 코드축 이후 재판정 |
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
| `Phase 2` | `착수 확정` | `2026-04-14 장후` `RELAX-LATENCY` 결론 후 `2026-04-15 장전`에 `2-1` 또는 `2-2` 중 하나를 반드시 시작 |
| `Phase 3` | `미착수` | 현재 critical path 아님 |

### 잔여 작업 명세

1. `0-1b 원격 경량 프로파일링`
   - `quote_stale=False latency_block` hot path 후보 1~3개 정리
2. `Phase 2-1 EV-aware latency degrade`
   - `2026-04-14 장후` `RELAX-LATENCY` 승격 결론이 나면 `2026-04-15 장전` 병행 착수
3. `Phase 2-2 dynamic strength selective override`
   - `2026-04-15 08:30`까지 `missed_winner` 빈도가 가장 높은 `momentum_tag` 1개를 골라 원격 canary 시작
   - `근거 부족`을 사유로 미루지 않고, 보류 시 명시적 사유와 다음 실행시각을 남긴다
4. `partial fill min_fill_ratio` 원격 canary
   - `2026-04-15` 원격 기본값 `0.5`로 시작하고 체결 기회 감소 여부를 장중에 확인
5. `expired_armed` 처리 로직 설계
   - `2026-04-15 장후`까지 재진입 허용 여부와 조건을 문서화한다
   - `태광` 같은 anchor case는 이벤트 복원용으로만 쓰고, 의사결정 기준은 전수 `expired_armed` 분포와 상위 코호트 통계로 둔다
6. `AI overlap audit` 기반 `selective override` 설계 착수
   - `2026-04-16` 이내에 `blocked_stage / momentum_tag / threshold_profile` 연결표 기준으로 시작한다
7. `SCALPING 모델 shadow 비교안`
   - `2026-04-15 PREOPEN`에 `WATCHING shared prompt` shadow 구현 착수
   - `2026-04-15 INTRADAY`에 `Tier2 Gemini Flash vs GPT-4.1-mini` 첫 실표본 수집 시작
   - `2026-04-15 POSTCLOSE`에 `counterfactual realized outcome` 1차 비교표 생성
8. `Phase 3-1 realistic/conservative counterfactual`
9. `Phase 3-2 exit authority 명문화`
10. `Phase 3-3 post-sell exit timing canary`
   - 현재 잔여 작업축에서는 제외한다.
   - entry/holding 직접 코드축(`작업 5/8/10`, `RELAX-DYNSTR`, `partial fill`) 1차 평가 후 재오픈 여부를 다시 본다.

## AI 프롬프트 개선작업 반영 상태

### 기준 문서

- [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md)
- [2026-04-11-scalping-ai-prompt-plan-review.md](./2026-04-11-scalping-ai-prompt-plan-review.md)
- [2026-04-11-ai-operator-message-validation.md](./2026-04-11-ai-operator-message-validation.md)

### 현재 고정된 분류

1. `SCALP_PRESET_TP SELL` 문제는 `의도 확인 후 처리`
2. `WATCHING 75 정합화`는 `Deferred`
3. `HOLDING hybrid`는 `override 조건 명세` 선행
4. `프롬프트 분리`와 `컨텍스트 주입`은 `순차 canary`
5. raw 즉시 제거, OpenAI 라이브 즉시 전환, 본서버 즉시 반영은 계속 보류
6. `스캘핑 HOLDING AI 프롬프트 최종 통합 설계안`은 북극성 문서로만 사용하고, 실제 실행 순서는 `AI 프롬프트 코딩지시서`의 `P1~P5` 분해 순서를 따른다.
7. `WAIT 65`는 `AI threshold miss` 단독 문제로 보지 않고, `latency_block` 1순위, `blocked_strength_momentum` 2순위, `overbought` 후순위로 고정한다.

참고 문서:
- [2026-04-13-scalping-holding-prompt-final-design.md](./2026-04-13-scalping-holding-prompt-final-design.md)

### 프롬프트 Phase 상태

| Phase | 상태 | 현재 판정 |
| --- | --- | --- |
| `P0 확인/계측` | `완료` | `작업 1/2/3` 완료, 후속 구현은 `작업 10`으로 분리 추적 |
| `P1 판단 기준/프롬프트 분리` | `즉시 착수` | `작업 4`는 Deferred, `작업 5`는 `2026-04-14 POSTCLOSE` 같은 날 착수, `2026-04-16` 1차 평가 |
| `P2 컨텍스트 주입` | `공격 일정` | `작업 6`은 `2026-04-17` 착수 또는 보류 사유, `작업 7`도 같은 날 병렬 착수 또는 보류 사유 |
| `P3 피처 패킷 보강` | `공격 일정` | `작업 8` 즉시 착수, `작업 9`는 `2026-04-17` scope / `2026-04-18` 착수 |
| `P4/P5 hybrid/critical` | `공격 일정` | `작업 10` `2026-04-14 POSTCLOSE` MVP 착수, `2026-04-19` 1차 평가, `작업 11` `2026-04-20`, `작업 12` 범위 확정 `2026-04-21` |

### 현재 순서

1. `P0`
   - `SCALP_PRESET_TP SELL` 의도 확인
   - AI 운영계측 추가
   - HOLDING hybrid override 조건 명세
2. `P1`
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

### 프롬프트 트랙 일정 고정 (`2026-04-14`, 공격 재배치)

1. `2026-04-14 POSTCLOSE`
   - `작업 5 WATCHING/HOLDING 프롬프트 물리 분리`
   - `작업 8 감사용 핵심값 3종 투입`
   - `작업 10 HOLDING hybrid 적용` `FORCE_EXIT` 제한형 MVP
   - 위 작업들은 범위 확정으로 끝내지 않고 같은 날 바로 착수
2. `2026-04-15`
   - `작업 5` 구현 진행 / 로그 비교축 확인
   - `작업 8 감사용 핵심값 3종 투입` 구현/검증 지속
   - `작업 10 HOLDING hybrid 적용` `FORCE_EXIT` 제한형 MVP 구현 지속
   - `SCALPING 모델 shadow 비교안`은 `WATCHING shared prompt` 기준 `Tier2 Gemini Flash vs GPT-4.1-mini` 1차 shadow 설계를 닫고, 장후 `counterfactual realized outcome` 비교표까지 이어지게 한다
3. `2026-04-16`
   - `작업 5/8/10` 1차 평가
   - `작업 10` canary-ready 입력 정리와 `작업 9` helper scope 초안 정리
4. `2026-04-17`
   - `작업 6` 착수 또는 보류 사유 기록
   - `작업 7` 착수 또는 보류 사유 기록
   - `작업 9` helper scope 확정
5. `2026-04-18`
   - `작업 9` 착수
6. `2026-04-19`
   - `작업 10` 1차 결과 평가 / 확대 여부 판정
7. `2026-04-20`
   - `작업 11` 착수
8. `2026-04-21`
   - `작업 12` 범위 확정

### `2026-04-16` 감사 반영 보정

1. `REVERSAL_ADD observe-only shadow` 단계는 제거한다.
   - 현재 코드에는 observe-only 전용 가드가 없어 `REVERSAL_ADD_ENABLED=True`가 곧 실주문 경로 진입을 뜻한다.
   - 따라서 readiness 판단은 기존 `reversal_add_candidate` 표본과 포지션 수량 분포 로그로 먼저 수행한다.
2. `SCANNER timeout`은 완전 신설 과제가 아니라 `SCANNER fallback` 한정 never-green/retrace 조기정리 로직의 일반 SCANNER 확장 과제로 정리한다.
3. `SCALP_LOSS_FALLBACK`은 신규 shadow가 아니라 이미 `SCALP_LOSS_FALLBACK_OBSERVE_ONLY=True`로 진행 중인 관찰축으로 본다.
   - `2026-04-17 PREOPEN` 1차 판정
   - `2026-04-21 POSTCLOSE` 활성화 여부 최종 판정
4. 상세 실행계획은 [2026-04-16-holding-profit-conversion-plan.md](./2026-04-16-holding-profit-conversion-plan.md)를 따른다.

### `2026-04-12` P0 진행 메모

1. `SCALP_PRESET_TP SELL`
   - 현재 라이브 공유 프롬프트에서는 비도달
   - 즉시 제거 대신 placeholder 의도 명시 + `ai_action_raw` 로그 추적 유지
2. AI 운영계측
   - `ai_parse_ok / ai_parse_fail / ai_fallback_score_50 / ai_response_ms / ai_prompt_type / ai_result_source` 로그 반영
   - `ai_score_raw / ai_score_after_bonus / entry_score_threshold / big_bite_bonus_applied / ai_cooldown_blocked` 운영 로그 반영
3. `HOLDING hybrid override`
   - `FORCE_EXIT`만 즉시집행 후보
   - `SELL`은 1차 canary에서 로그 우선
   - `SCALP_PRESET_TP`는 전용 검문에서만 `DROP` 즉시집행 허용
4. `SCALPING 모델 shadow 비교`
   - 현재 `OpenAI 듀얼 페르소나 shadow`는 `gatekeeper/overnight` 전용이라 라이브 스캘핑 공용 프롬프트 비교에는 바로 못 쓴다
   - 1차 범위는 `WATCHING shared prompt` 동일 입력의 `Tier2 Gemini Flash vs GPT-4.1-mini`
   - 비교 결과는 `action/score divergence`와 장후 `counterfactual realized outcome`으로 읽고, `HOLDING/SCALP_PRESET_TP` 확장은 후순위로 둔다

### `2026-04-12` P1 작업 4 착수 메모

1. 라이브 프롬프트는 유지
2. `75~79` 경계구간만 `75 정합화 shadow prompt` 재평가
3. 실주문 연결 없이 `watching_prompt_75_shadow` 로그만 기록
4. 원격 환경에서 `AI_WATCHING_75_PROMPT_SHADOW_ENABLED=true`일 때만 활성화
5. `2026-04-12` 기준 원격 `songstockscan`에는 최소 패치 + env 주입 완료, 단 실제 표본은 다음 거래일 `tmux bot` 재기동 이후부터 누적됨
6. 집계는 `src/engine/watching_prompt_75_shadow_report.py`로 `buy_diverged / 75~79 분포 / missed_winner 교차표`까지 같이 본다
7. 운영 점검은 `src/engine/check_watching_prompt_75_shadow_canary.py`로 `preopen/open_check/midmorning/postclose` 4개 phase를 표준화한다

### `2026-04-13 10:50 KST` WAIT 65 통합 운영판단

1. `WAIT 65`는 추가 분석만 계속할 단계도, 전면 완화로 갈 단계도 아니다.
2. 저위험 축은 즉시 canary를 시작하고, 하위 원인 분해는 그 폭을 제어하는 범위에서만 병행한다.
3. 현재 즉시 착수 가능한 축은 `quote_stale=False` 중심 `latency canary`다.
4. `blocked_strength_momentum`은 전역 완화가 아니라 `below_window_buy_value / below_buy_ratio / below_strength_base` 3축 기준 국소 재설계로 간다.
5. `shadow 하한 60/55` 조정, `WAIT 65` 전면 완화, `overbought` 우선 착수는 보류한다.
6. 이번 세션 코드 개선은 `latency_state_danger`를 `quote_stale / ws_age / ws_jitter / spread` 하위 이유로 로깅하고, canary를 해당 reason allowlist로 더 좁게 제어할 수 있게 만드는 것까지로 제한한다.
7. `post-sell`은 관측지표로만 남기고 현재 잔여 작업축에서는 제외한다. 당장 코드를 바꿀 축은 `작업 5/8/10`과 entry/holding 직접 개선축이다.
8. 다만 이 결론은 `관찰 축을 계속 늘리자`는 뜻이 아니다. `2026-04-14 장후`까지는 기존 축만 재확인하고, `2026-04-14 장후`에는 `반영 / 보류+축전환 / 관찰종료` 중 하나를 강제한다.
9. `2026-04-14` 이후 관찰축의 역할은 `개선 착수 전 추가 분석`이 아니라 `개선 후 지속 점검`이다.

## 운영서버 롤아웃 판단용 추가 모니터링 기간

### 기본 원칙

- `스캘핑 국소 canary`는 `당일 30~60분 + 장후 평가 + 필요 시 1~2세션 추가`가 기본이다.
- 현재 `RELAX-LATENCY`는 `2026-04-10` 장중 후반 반영으로 표본 시간이 짧았다.
- 따라서 **운영서버 롤아웃 판단 전 추가 모니터링은 최소 `2026-04-14 장후`까지** 필요하다.
- 이 기간은 `기존 관찰축 재검증` 기간이며, 새로운 관찰축을 계속 추가하는 기간이 아니다.
- 더 정확히는 `2026-04-14 장후 결론`을 내릴 만큼만 재검증하는 기간이며, 그 이후에는 속도 우선으로 바로 반영/착수한다.
- `2026-04-15 08:30`까지는 최소 한 개의 실행 축이 실제로 시작돼 있어야 한다. `결론만 있고 실행 없음`은 허용하지 않는다.

### 현재 판단

1. `2026-04-13` = 원격 추가 관찰 1일차
2. `2026-04-14` = 원격 추가 관찰 2일차
3. `2026-04-14 장후` = 현재 스캘핑 매매로직 canary의 `결론 확정` 시점
4. `2026-04-15 08:30` = `RELAX-DYNSTR` 1축 canary, `partial fill min_fill_ratio` canary, `Phase 2` 시작이 실제 실행되는 시점
5. 단, 아래 체크포인트를 충족하지 못해도 `결론 미룸`부터 하지 않는다. `2026-04-14 장후`에는 `보류 + 단일축 실행` 또는 `관찰 종료 후 재설계`를 명시한다.

### 롤아웃 체크포인트

1. `quote_stale=False` 축에서 `submitted` 또는 `holding_started` 개선 근거가 있어야 한다
2. `MISSED_WINNER` 분포가 악화 일변도가 아니어야 한다
3. `full fill vs partial fill` 체결 품질이 유의미하게 악화되지 않아야 한다
4. `preset_exit_sync_mismatch`가 롤아웃을 막을 수준으로 증가하지 않아야 한다
5. `fetch_remote_scalping_logs`와 스냅샷 수집이 재현 가능해야 한다
6. `0-1b 원격 경량 프로파일링` 결과로 hot path 후보가 정리돼 있어야 한다
7. 원격 비교검증 이슈는 재발 시 별도 원인 수정으로 다루고, 현재 잔여 작업축의 critical path에는 올리지 않는다

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
5. 운영 자동화:
   - `08:20/10:20/13:20` 원격 baseline 수집 cron
   - `10:00/12:00` monitor snapshot cron
   - `16:00` 원격 fetch cron

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
- 신규 관찰축 추가 없이 `개선 착수 결론`을 강제한다
- `RELAX-DYNSTR`, `partial fill min_fill_ratio`, `expired_armed`, `AI overlap`의 다음 실행시각을 오늘 장후에 고정한다
- `WATCHING 75 shadow`, `post-sell canary`, `remote_error snapshot 재점검`은 오늘 잔여 작업축에서 제외한다

장전 체크포인트:
1. 전일 판정 반영 상태 확인
2. 롤아웃 게이트 항목별 관측 계획 고정

장중 체크포인트:
1. `quote_stale=False` 개선이 반복되는지 확인
2. `full fill vs partial fill` 체결 품질 재확인
3. `AI overlap audit`, `hard stop taxonomy`, `sync mismatch`가 해석 가능 수준인지 확인
4. 새로운 분석축 발굴이 아니라 `장후 개선 결론`을 내릴 수 있을 정도로만 기존 축을 재점검한다

장후 체크포인트:
1. `RELAX-LATENCY` 운영서버 승격 가능/불가 최종 결론
2. `RELAX-DYNSTR` `momentum_tag` 1축 canary 설정값과 rollback 가드를 `2026-04-15 08:30` 실행형으로 확정
3. `partial fill min_fill_ratio` 원격 canary 설정값과 `2026-04-15` 관찰 포인트를 확정
4. `expired_armed` 처리 로직 설계 범위와 `2026-04-15 장후` 완료 기준을 확정
5. `AI overlap audit -> selective override` 설계 착수일을 `2026-04-16`로 고정
7. 이미 구축된 관찰축은 `2026-04-15 장중 지속 점검용`으로만 재정리한다
8. 장후 결론은 반드시 `날짜 + 액션 + 실행시각` 형식으로 문서화한다

### `2026-04-15` 장전 반영/착수 시점

핵심 목적:
- `2026-04-14 장후 결론`을 실제 운영/개발 액션으로 즉시 반영한다
- `RELAX-DYNSTR` 1축 canary와 `partial fill min_fill_ratio` canary를 `08:30`까지 실제로 시작한다
- `Phase 2`를 오늘 시작하고, `expired_armed` 설계는 오늘 장후에 닫는다

장전 체크포인트 (`08:00~08:30`):
1. `2026-04-14 장후` 결론대로 `RELAX-LATENCY` 반영/보류 상태를 실제 설정에 적용한다
2. `RELAX-DYNSTR` `momentum_tag` 1축 원격 canary를 `08:30`까지 시작한다
3. `partial fill min_fill_ratio` 원격 canary를 `08:30`까지 시작한다
4. `RELAX-LATENCY`가 승격되면 `Phase 2-1`을 병행 착수하고, 승격이 보류되면 `Phase 2-2`를 단독 착수한다
5. 실행 축의 롤백 가드와 장중 관찰 포인트를 재확인한다

장중 체크포인트:
1. `RELAX-DYNSTR` 1축 canary 퍼널 변화를 기록한다
2. `partial fill min_fill_ratio` canary의 체결 기회 감소/partial 억제 효과를 함께 본다
3. `2026-04-15` 장중에는 `전일 결론이 실제로 기대한 방향으로 움직이는지`만 점검한다

장후 체크포인트:
1. `expired_armed` 처리 로직 설계 문서를 완료한다
2. `RELAX-DYNSTR`와 `partial fill min_fill_ratio` 1일차 canary 결과를 1차 정리한다
3. `2026-04-16` `AI overlap audit -> selective override` 설계 착수 입력을 고정한다

주의:
- `2026-04-15`는 새 결론을 내는 날이 아니라 `2026-04-14 장후 결론`을 검증하는 날이다.
- `AI 프롬프트 개선` 롤아웃 판단은 별도 일정으로 시작한다.
- 별도 일정은 더 미정 상태가 아니라 `2026-04-14 POSTCLOSE 작업 5/8/10 착수 -> 2026-04-15 진행 -> 2026-04-16 평가`로 고정한다.
- 기존 관찰축은 이 시점부터 `반영 후 지속 점검` 용도로만 유지한다.

### `2026-04-16` 설계 착수 시점

핵심 목적:
- `AI overlap audit`를 `selective override` 설계 착수로 연결한다
- `reversal_add` 결함 핫픽스 반영 상태를 기준으로 기존 후보 로그 -> limited canary 전환 기준을 고정한다

체크포인트:
1. `blocked_stage / momentum_tag / threshold_profile` 연결표를 설계 입력으로 고정한다
2. `RELAX-DYNSTR` canary 1일차 결과와 연결해 `selective override` 초안을 시작한다
3. 추가 canary가 필요하면 `한 축만` 남기고 보류 사유를 기록한다
4. `reversal_add`는 `REVERSAL_ADD_SIZE_RATIO` 반영 핫픽스가 적용된 버전을 기준으로 운영한다
5. `reversal_add` 모니터링은 기존 후보 로그와 실주문 로그를 분리해 읽는다.
   - readiness: `reversal_add_candidate`, `reversal_add_blocked_reason`
   - live canary 이후: `[ADD_SIGNAL]`, `[ADD_ORDER_SENT]`, `reversal_add_post_eval_fail`

## 즉시 착수 체크리스트

1. `RELAX-LATENCY` `2026-04-14 장후` 최종 결론 확정
2. `RELAX-DYNSTR` `momentum_tag` 1축과 rollback 가드를 `2026-04-15 08:30` 실행형으로 고정
3. `partial fill min_fill_ratio` 원격 canary 값을 `2026-04-15` 실행형으로 고정
4. `expired_armed` 설계 문서 위치와 완료 기준을 `2026-04-15 장후`로 못박기
5. `AI 프롬프트 작업 5/8/10`을 `2026-04-14 POSTCLOSE` 즉시 착수 대상으로 고정
6. `AI overlap audit -> selective override` 착수일을 `2026-04-16`로 고정
7. `2026-04-14~2026-04-16` 체크포인트를 운영 문서와 체크리스트에 고정
8. `reversal_add`는 기존 후보 로그와 포지션 수량 분포 readiness가 통과할 때에만 원격 1축 limited canary를 연다

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
- [2026-04-15-scalp-reversal-add-implementation-result.md](./2026-04-15-scalp-reversal-add-implementation-result.md)
- [2026-04-11-github-project-google-calendar-setup.md](./2026-04-11-github-project-google-calendar-setup.md)
- [plan-korStockScanPerformanceOptimization.archive-2026-04-08.md](./plan-korStockScanPerformanceOptimization.archive-2026-04-08.md)
- [plan-korStockScanPerformanceOptimization.qna.md](./plan-korStockScanPerformanceOptimization.qna.md)

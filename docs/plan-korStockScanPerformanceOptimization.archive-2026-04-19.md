# KORStockScan 성능 최적화 계획 아카이브 (2026-04-19 정리본)

이 문서는 `2026-04-19` 계획서 cleansing 과정에서 `plan-korStockScanPerformanceOptimization.prompt.md`에서 걷어낸 상세 경과를 보관하는 문서다.  
현재 실행 기준은 반드시 [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)를 우선 본다.

## 아카이브 범위

이번 정리에서 prompt 원문에서 분리한 내용은 아래 4묶음이다.

| 묶음 | 왜 prompt에서 뺐나 | 지금 어디에 쓰이나 |
| --- | --- | --- |
| `2026-04-11 기준 완료/진행/잔여 상태` | 현재 실행 기준보다 역사적 맥락 비중이 커짐 | 과거 우선순위 변화 추적 |
| `프롬프트 트랙 2026-04-12~2026-04-21 상세 일정` | 이미 지난 공격 일정이 많아 현재 실행 가독성을 해침 | 작업 5/8/9/10/11/12 경과 확인 |
| `2026-04-11~2026-04-16 롤아웃/모니터링 상세 계획` | 현재는 차주 실행표와 audited table이 우선 | 롤아웃 판단 규칙의 형성 배경 확인 |
| `즉시 착수 체크리스트/가드레일 상세판` | 현재 checklist와 prompt에 핵심만 남기면 충분 | 왜 특정 가드레일이 생겼는지 설명 |

## 1. `2026-04-11` 기준 역사적 상태 스냅샷

### 완료로 보던 것

1. 스캘핑 매매로직 `Phase 0/1` 주요 항목
2. 원격 `songstockscan` 코드 반영
3. `RELAX-LATENCY` 1차 반영 후 추가 관찰 체계
4. 스캘핑 AI 프롬프트 관련 팩트/검토/운영자 메모 작성

### 진행 중으로 보던 것

1. `develop T-2/T-1` 선행 적용 운영계획 재정렬
2. `RELAX-LATENCY` 추가 관찰 후 `2026-04-14` 장후 판정
3. `RELAX-DYNSTR`, `partial fill min_fill_ratio`, `expired_armed`, `AI overlap selective override` 준비
4. `2026-04-15 No-Decision Day` 게이트 운영

### 잔여로 보던 것

1. `entry_pipeline` 지표 정의 보정
2. `Gatekeeper fast reuse / holding skip` 실패사유 계측 승격
3. `aggregation gate` 재정의
4. `partial fill sync mismatch` 코호트 추적
5. 프롬프트 구현 전반과 `작업 5/8/10` 승격 기준 정리

## 2. 프롬프트 트랙 상세 경과 스냅샷

### 당시 고정 분류

1. `SCALP_PRESET_TP SELL`은 의도 확인 후 처리
2. `WATCHING 75 정합화`는 deferred
3. `HOLDING hybrid`는 `override 조건 명세` 선행
4. `프롬프트 분리`와 `컨텍스트 주입`은 순차 canary
5. raw 즉시 제거, OpenAI 라이브 즉시 전환, 본서버 즉시 반영은 보류

### 당시 공격 일정

1. `2026-04-14 POSTCLOSE`
   - 작업 5 `WATCHING/HOLDING` 프롬프트 물리 분리
   - 작업 8 감사용 핵심값 3종 투입
   - 작업 10 `HOLDING hybrid` `FORCE_EXIT` 제한형 MVP
2. `2026-04-15`
   - 작업 5/8/10 구현 지속
   - `WATCHING shared prompt` shadow 비교 설계
3. `2026-04-16`
   - 작업 5/8/10 1차 평가
   - 작업 9 helper scope 초안
4. `2026-04-17~2026-04-21`
   - 작업 6/7/9/11/12 순차 확정

### 이번 정리 후 살아남은 핵심 규칙

1. 작업 5/8/10은 `develop 선행`, `main 후행` 원칙 유지
2. 작업 10은 `FORCE_EXIT` 제한형 MVP 관찰축이 확보되기 전 확대 금지
3. HOLDING 성과판정은 schema 변경 직후가 아니라 `D+2`에 수행

## 3. `2026-04-11~2026-04-16` 롤아웃/모니터링 상세판

### 당시 핵심 전제

1. `2026-04-14 장후`에 canary 결론을 강제한다.
2. `2026-04-15 08:30`까지 최소 한 개의 실행 축이 실제로 시작돼 있어야 한다.
3. `2026-04-15`는 새 결론의 날이 아니라 `2026-04-14 장후` 결론 검증의 날로 본다.
4. `2026-04-16`에는 `AI overlap audit -> selective override` 설계 착수 입력을 고정한다.

### 당시 체크포인트가 남긴 교훈

1. 관찰축을 무한히 늘리는 방식은 실행 속도를 해친다.
2. 장후 결론은 `날짜 + 액션 + 실행시각`이 없으면 결론이 아니다.
3. broad relax보다 `손실축 분리`가 먼저다.

## 4. 현재 prompt에서 요약만 남긴 가드레일 원형

1. `near_safe_profit`, `near_ai_exit` 즉시 완화 금지
2. 공통 hard time stop 실전 적용 보류
3. `RISK_OFF` day에서 스윙 완화 금지
4. 듀얼 페르소나 즉시 실전 승급 금지
5. 단일일자 결과 기반 공통 파라미터 일괄 조정 금지
6. 프롬프트 구조 변경의 본서버 즉시 반영 금지

현재 기준에서는 위 규칙을 세부 문구 그대로 반복하지 않고, `원인 귀속 유지`, `한 번에 한 축 canary`, `develop 선행`, `D+2 HOLDING 판정`으로 요약해 prompt에 남겼다.

## 5. 아카이브 사용법

1. 현재 무엇을 해야 하는지는 `prompt`와 날짜별 checklist를 본다.
2. 왜 이런 운영 규칙이 생겼는지는 이 문서와 `archive-2026-04-08`을 본다.
3. 기본계획과 실제 실행의 차이는 `execution-delta`를 본다.
4. 반복 성과 baseline은 `performance-report`를 본다.

## 참고 문서

- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)
- [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md)
- [plan-korStockScanPerformanceOptimization.performance-report.md](./plan-korStockScanPerformanceOptimization.performance-report.md)
- [plan-korStockScanPerformanceOptimization.archive-2026-04-08.md](./plan-korStockScanPerformanceOptimization.archive-2026-04-08.md)

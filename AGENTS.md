KORStockScan 작업 기본 규칙:

## 1. 우선 참조

- 작업 시작 전 `docs/plan-korStockScanPerformanceOptimization.rebase.md` §1~§6과 당일 `docs/YYYY-MM-DD-stage2-todo-checklist.md` 상단 요약(`오늘 목적`, `오늘 강제 규칙`)을 먼저 읽는다.
- 튜닝 원칙, 판정축, 일정, rollback guard는 `Plan Rebase` 문서를 기준으로 삼고, 실행 작업항목은 날짜별 checklist가 소유한다.

## 2. 판정 원칙

- 목표는 손실 억제가 아니라 기대값/순이익 극대화다.
- `Plan Rebase` 기간 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이다.
- 실전 변경은 하루 1축 canary만 허용하며, 신규/보완축은 shadow 없이 `canary-only`로 본다.
- 원격/server 비교값은 Plan Rebase 의사결정 입력에서 제외한다.
- 손익은 `COMPLETED + valid profit_rate`만 사용한다. `NULL`, 미완료, fallback 정규화 값은 손익 기준에서 제외한다.
- 비교는 손익 파생값보다 거래수, 퍼널, blocker 분포, 체결 품질을 우선 본다.
- BUY 후 미진입은 `latency guard miss`, `liquidity gate miss`, `AI threshold miss`, `overbought gate miss`로 분리한다.
- `full fill`과 `partial fill`은 합치지 않는다.
- 원인 귀속이 불명확하면 리포트 정합성, 이벤트 복원, 집계 품질부터 점검한다.
- 답변은 가능하면 `판정 -> 근거 -> 다음 액션` 순서로 정리한다.

## 3. 문서/자동화

- 관련 문서가 있으면 함께 업데이트한다.
- 날짜별 checklist 상단은 매번 장문의 `목적/용어 범례/운영 규칙` 반복본을 복제하지 말고, `오늘 목적`과 `오늘 강제 규칙`만 짧게 적는다. 상세 용어/정책/가드는 `Plan Rebase` 또는 관련 부속문서를 참조한다.
- 개인문서(`docs/personal-decision-flow-notes.md`)는 다른 문서의 `Source`/판정 근거 링크로 참조되지 않는다.  
  즉, 개인문서는 보조 메모 성격으로 유지하고, 실행 판정의 근거는 checklist/report/plan 기준문서에서 직접 가져온다.
- 미래 작업, 특정 시각 작업, 재확인 작업은 답변에만 남기지 말고 날짜별 checklist에 자동 파싱 가능한 `- [ ]` 항목으로 기록한다.
- checklist 작업항목을 만들거나 수정했으면 parser 검증을 수행하고, Project/Calendar 동기화는 토큰 존재 여부를 확인하지 말고 사용자에게 실행할 1개 명령을 남긴다.
- 자동화 규칙, cron, workflow, wrapper를 바꾸면 운영문서와 checklist를 같은 변경 세트로 맞춘다.

## 4. 실행 환경

- Python 작업은 프로젝트 `.venv`를 기본으로 사용한다.
- 패키지 설치/업그레이드/제거 전에는 사용자 의사결정을 받는다.
- 임시 스크립트보다 재현 가능한 명령과 프로젝트 표준 실행 경로를 우선한다.

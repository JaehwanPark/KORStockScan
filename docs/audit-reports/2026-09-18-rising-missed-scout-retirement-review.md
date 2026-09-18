# 2026-09-18 RISING_MISSED_ONE_SHARE_ENTRY 폐기 review

사용자 지시: 전용 런타임, 관련 산출물 및 장후작업 모두 삭제. 이 문서는 구현과 검증 증거이며 과거 전략의 복원/주문 승인이 아니다.

## 변경과 경계

- 신규 scout 진입·upgrade·scanner async commit adapter와 전용 진입 API를 삭제했다. 복원된 WATCHING scout intent 및 명시적 scout/upgrade 요청은 공통 submit의 budget/broker 접근 전에 차단한다.
- 전용 장후 `monitoring.one_share_threshold_opportunity`, `monitoring.rising_missed_scout_workorder` 소스·CLI·AI review schema·wrapper 초기/후행 호출·DONE 필수 검증을 삭제했다. workorder/checklist/prior/summary에서 전용 input/hash/후속 업무를 제거하고 과거 반복 결함도 재유입시키지 않는다.
- 기존 env와 historical report/stage를 retirement 계약으로 제거한다. 일반 BUY bridge의 BUY 판정·공통 sizing/가격/현금/주문/holding/exit, TP1 안전 판정 및 기존 pending/체결/완료 원장의 정산·AI 귀속은 보존한다.
- 파일 location gate: 일반 BUY 후보 안전 판정과 과거 체결 귀속은 기존 scalping 역할에 속하므로 `src/engine/scalping/rising_missed_candidate.py`로 이동했다. 이전 `rising_missed_one_share_entry.py`와 신규 주문 API는 삭제했고 호환 wrapper를 만들지 않았다. engine root 신규 module/package는 없다. 과거 필드/이유 토큰은 정산/차단 식별에만 남으며 주문 actor는 없다.
- 활성 전용 producer 및 Main PID 부재를 확인한 뒤 worktree/release의 전용 report/cache 물리 복사본96개 root, 4,987 files, 38,521,941 bytes를 삭제했다. 혼합 주문·custody·COMPLETED 원장, 일반 missed-entry feedback/prior, 역사적 immutable source와 배포 receipt는 유지한다.

## 검증 및 적용

실행 증거: `tmp/rising-missed-scout-retirement-20260918/validation.json`, pytest logs, `artifact-deletion.json` 및 파일 metadata manifest, `workspace-integration.json`, `deployment.json`. 구현→review→누락 소비자/재유입 보완→re-review→회귀 검증을 수행한다. 정상 일반 entry·TP1·공통 주문·기존 체결 귀속과 OFF 재유입 차단을 함께 검증한다.

배포는 검증 commit의 immutable managed release 선택과 Main PID 소비를 분리한다. 기존 Main은 dated integrated-entry handoff 결손으로 정지 상태이며 이번 폐기로 재시작하지 않는다. 날짜/정책/해시/가격·수량/provider/safety 변경, 실제 주문, 전체 장후 재실행 또는 성능 확장은 수행하지 않는다. 자연/경제성은 폐기 전략의 acceptance로 요구하지 않는다.

최종 source commit·선택 release·검증 숫자는 아래 최종 receipt에서 기록한다.

## 최종 review 결과

- Review에서 누락된 classifier prior 후행 workorder refresh, summary hash와 checklist 승계, 반복 결함 escalation의 과거 scout 재유입을 수리했다. 최종 affected producer/consumer/runtime 회귀 **2,277 PASS**(24.27초), 작업본 일반 entry/TP1/정산 회귀 **260 PASS**, restored intent·일반 WATCHING·partial pending 정산 **7 PASS**. Python27개 compile, wrapper bash syntax, diff whitespace, print-only 문서 parser PASS.
- 실제 전용 생산자0/Main PID0 확인, 전용 산출물4,987개 삭제 및 exclusive stale enabled operator override1block 제거. 다른 세션 source와 다른 override·프로세스·정책은 유지했다.
- 승인된 기존 commit/push/deploy 권한 내 immutable `rising-missed-scout-retired-20260918` release 선택에 사용할 source는 이 review를 포함한 commit이다. 정확한 SHA·원격·selector CAS·actual Main PID 상태는 `tmp/rising-missed-scout-retirement-20260918/deployment.json`에서 확인한다. 공유 data mount와 역사적 selected source는 혼동하지 않는다.
- 실제 주문/provider/API 호출·전체 장후 재생성·성능 확장·Main restart 및 외부 sync는 생략했다. 기존 PREOPEN integrated-entry handoff 결손은 폐기 작업의 해소 대상이 아니며 Main 기동/PID 증거로 대체하지 않는다.

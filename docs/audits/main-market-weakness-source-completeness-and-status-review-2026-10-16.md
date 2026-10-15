# Main 약세 연구 날짜 완전성·상태 보고 보완 리뷰 — 2026-10-16

## 결정과 범위

사용자 지시에 따라 미시작 날짜 누락, 최신 원천 처리 기회, 초기 보류 기록, 관측 건수 보고를 수정하고 반복 리뷰했다. 구현은 기존 `src/engine/automation/main_market_weakness_research.py`, 회귀는 기존 `src/tests/test_main_market_weakness_source_repair.py`가 소유한다. 새 Python 모듈·CLI·cron·worker를 만들지 않았다. [운영 계약 §12](../proposals/main-market-weakness-postclose-source-binding-and-candidate-repair-plan-2026-10-13.md#12-2026-10-16-날짜-완전성최신-원천-처리보고-보완-운영-계약)와 [현재 자연 수용 owner](../checklists/2026-10-16-stage2-todo-checklist.md)에 인계한다.

이 리뷰는 작업본 코드·fixture 검증의 완료다. 배포·선택 변경·optional 재결속·운영 원천 재집계·실제 Telegram 발송·Main 재기동은 실행하지 않았다. 기존 보조 입력/응답·연구 모집단·정책·주문·수량·Main/manual custody·퇴역 경계를 보존했다. 신규 장중 hook·로그·metadata·파일 조회·계산·queue/thread·API/AI 호출은 0이다.

## 원 실행 증거와 보고 정정

- 07:50 KST 조회 당시 selected commit은 `23a13aba62884a5d3a0d48a3f91ebff4262571f6`, 설치/선택 약세 코드 hash는 `edf33dc9719358848a5e13d449589f2faed2e36666e5c2c5f06b15c37eaeb91b`로 일치했고 설치 calendar 검증도 true였다. 10/15 야간은 9/29→9/30→10/2→10/6→10/7→10/8을 6회 처리했다. 마지막 worker exit=0, 예약 합계 360초다. 배포 누락이나 같은 양 끝 날짜의 반복은 확인되지 않았다.
- 원 누적 `1cc40800e82dbfa1308d036633ff9ac13604a8456bbdea5e49a160d7f4b7400a`는 10/12~14를 `invalidated_source_dates`로 보존했지만 `pending_source_dates=[]`였고 이전 `comparison_current=True`였다. 원천 검색은 10/15를 찾지만 그날 cursor가 없는 것이 누락 원인이다. 기존 `migration_pending=True`가 실제 outbox 변경을 막고 있었다.
- `night_summary.json` 마지막 갱신은 04:40:20, owned cron log 마지막 갱신은 05:40:01이며 마지막 실제 결과는 `regular_postclose_or_eod_active` 보류다. 초기 반환이 summary writer를 건너뛰어 최신 시도와 마지막 계산의 구분이 소비자까지 전달되지 않았다.
- 당일 장후 의미 리뷰(`main-postclose-semantic-review-and-repeated-read-findings-2026-10-16.md`)의 표35에 있는 source10/8 `native observation0`은 독립 projection census 값이다. 같은 cursor에는 `native_indexed_rows=2856`, daily에는 `native_binding_verified=684`가 있다. 0을 native 원천/연결 부재로 해석하지 않는다. 이 2,856행은 고유 관측 수나 실제 매매 수가 아니다. 이 문서가 해당 수치의 해석을 보완하며 원 감사 기록/운영 산출물을 덮어쓰지 않았다.
- 원 후보 99개는 모두 보조 이후 추가 보류 CF이며 전향 baseline resolved=0, `uncertainty_unresolved`, 직접 검사한 알림 적격=0, outbox events/recommendations는 비어 있었다. 82개는 10/15 이후, 17개는 10/14 이후 자료로 비교하도록 고정돼 있다. 10/15 처리만으로 모든 후보의 전향 검증이 충족되는 것은 아니다. 기계 numeric 역할 미지원과 과거 원천 결손도 그대로 남긴다.

## 구현과 재리뷰에서 보완한 경로

| 경로 | 변경·수용 기준 |
| --- | --- |
| 날짜 완전성 | 발견된 eligible 전체를 봉인된 `source_scope`로 공유한다. 미시작도 pending이고 신규 날짜/시작일/cursor 변동은 예전 비교의 현행성을 해제한다. publish 직전 목록이 바뀌면 defer다. |
| 원천 소실 | 현행 manifest에 있던 미시작 날짜의 파일이 사라져도 날짜를 보존한다. 다음 처리에서 source gap을 발행하며 조용히 완료로 축소하지 않는다. |
| 최신/과거 처리 | 최신 원천 미완료에 야간 한 번의 우선 기회를 주고 backlog 순환 위치를 보존한다. 다른 원천 수리가 남으면 후속 source 슬롯에서 최신 날짜를 제외해 연속 재선택을 막는다. |
| 최신 보류 | 검증된 야간의 calendar/EOD/budget/deadline 초기 보류도 lock 아래 latest attempt에 남긴다. 예약/순환/마지막 계산 bytes는 보존한다. 시간창 밖 최초 호출은 상태 쓰기 0이다. |
| 관측 보고 | native 입력 행·projection 행·검증 연결 건수를 daily/Markdown/terminal에서 구분한다. native CRC 실패 시 색인·두 census가 함께 rollback된다. |

첫 리뷰에서 후보 scope 반복문의 지역 변수와 새 source scope 이름이 충돌하는 경로를 찾아 분리했고 재검증했다. 최신 우선 선택 직후 같은 날짜가 다시 선택되는 경로도 보완했다. 날짜별 eligibility는 scheduler·누적·현행성 검사에서 공통 helper를 사용한다. 기존 신규 pending 회귀의 날짜는 실제 거래일인 10/12로 바로잡았다. 10/9 공휴일 fixture를 근거로 비거래일을 연구 입력에 새로 넣지 않는다.

작업본 helper로 운영 **메타데이터만 읽은** 확인에서도 source 상한 10/15의 대상 10일과 `not_started=10/15`를 식별했고, `source_scope` 없는 원 비교는 현행 false였다. 운영 comparison이나 cursor를 새로 발행한 결과가 아니다.

## 검증과 배포 인계

- 8 suites **289 passed in 10.89s**: `test_main_market_weakness_research.py`, `test_main_market_weakness_research_automation.py`, `test_main_market_weakness_source_repair.py`, `test_main_market_weakness_research_notify.py`, `test_market_weakness_entry_guard.py`, `test_notify_panic_state_transition.py`, `test_micro_reversion_symbol_master.py`, `test_engine_location_gate.py`. 이전 278개에 11개 회귀를 추가했다. 실전송 없이 fixture transport만 사용했다.
- 추가 회귀는 plain/gzip 미시작 날짜의 outbox 보존, 발견 후 원천 소실, source floor/night cutoff, 계산 중 신규 날짜 유입, 최신/과거 처리와 crash 호환, 4종 초기 보류, native CRC/census rollback을 다룬다. 기존 양성 native 연결 회귀에는 JSON/Markdown/terminal 보고 일치 검증을 추가했다.
- 변경 Python 2개 Ruff·Black `--check`·`py_compile`, `git diff --check` 통과. shell/installer는 변경하지 않아 shell 구문 검사를 추가 실행하지 않았다. 운영 자료 재생·성과 재계산·외부 호출 없이 검증했다.
- 작업본 문서 로컬 링크 85개 정상, print-only backlog 27개 중 현재 약세 OPEN owner 1개를 확인했다. 현재 체크리스트는 착수 때 존재한 미추적 일일 문서이며 기존 바이트에 해당 owner의 보완 한 줄만 추가했음을 대조했다. 기존 AUTO 봉인 및 다른 owner는 그대로다. 기준 문서 README/runbook/Rebase/prompt/AGENTS는 변경하지 않는다. 최종 커밋은 소스·회귀·계획·이 리뷰·현재 체크리스트 5개 파일로 제한한다.
- 배포 전용 세션은 이 검토 커밋을 통합한 선택 사본에서 기존 자기 optional code/calendar binding만 재결속하고 설정·cron 재조회를 확인한다. 기존 enabled/notify·source floor·설치 이력·후보/outbox를 유지한다. 연구 코드 hash가 바뀌므로 기완료 날짜도 다시 수리 대상이 될 수 있다. 예약을 늘리거나 EOD 우선권을 우회해 당일 완료로 만들지 않는다.
- 다음 허용 야간의 latest/backlog 실제 진전, 미시작 pending 해소, 남은 source gap, migration 종료, 누적 비교와 알림 disposition이 자연 수용이다. 적격 0은 정상 보류이며 코드 통과·커밋·배포가 조정 수치 검증이나 Telegram 배송·경제성을 증명하지 않는다. 원 `MainMarketWeaknessPostcloseObservation1008` OPEN을 유지한다.

최종 자체 리뷰에서 위 구현·producer/consumer·원천 변경·초기 반환·압축 rollback·권한 경계의 미해결 소견은 0이다. 운영 배포와 실제 야간 수용은 위 owner의 별도 잔여 작업이다. 커밋 준비 중 다른 세션의 selected release가 `580d5865b568c36331bbeed69ee65de9fc6c137a`로 진행했음을 관측했다. 수리 소스·회귀·계획의 원본이 새 부모와 같은지 확인했고, 커밋의 체크리스트는 새 부모의 추가 인계도 보존한 상태에서 약세 보완 한 줄만 추가한다. 임시 index와 별도 branch로 생성하며 이 세션은 주 작업 branch/기존 staging 또는 selected release를 변경하지 않는다.

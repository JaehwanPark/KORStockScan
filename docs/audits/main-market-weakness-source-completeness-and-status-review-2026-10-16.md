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

## 2026-10-20 갱신 원천의 야간 재처리와 수용 인계

사용자 현황 점검 후 “다음액션 실행”에 따라 기존 [현재 체크리스트](../checklists/2026-10-20-stage2-todo-checklist.md)에 `MainMarketWeaknessPostcloseObservation1008`를 복원하고 갱신 원천·label 연결·기존 예약을 대사했다. 과거 코드 완료를 재개한 것이 아니라 원 운영 수용의 날짜 인계를 복원한 것이다. 기준은 selected `661260e5f4be406760820ee2001b953ad6adf25d`, 실제 소비 영수증의 PID2724137/start12485195다. 설치 코드 `f6f009128fb691f482170f062fd75ff793cc2b4dd5d65122f0532c4bf54bcc1a`와 selected 코드가 같고 native calendar 검증도 true다.

### 원인 → 대사 → 잔여 수용

| 대상 | 확인한 첫 계약과 원인 | 실행한 대사와 다음 종료 검사 |
| --- | --- | --- |
| 10/16 원천 | 기존 daily 이후 trace/payload가 plain→gzip으로 바뀌어 `source_plan`이 달라졌다. `cursor_current=false`는 이전 물리 세대를 거부하는 정상 동작이다. | 원 cursor/일별 산출물을 보존했다. 기존 야간 producer가 새 논리 원천의 physical SHA/EOF/CRC를 검증해 새 daily/terminal을 만든 뒤 currentness를 확인한다. |
| 10/19 원천 | 연구는10/19 21:40에 구 machine 보고서를 소비했다. 상위 machine은10/20 07:44:16, auxiliary는07:49:26에 갱신됐고 새 export도 생겼다. 원 야간의 나머지8슬롯은 EOD 우선권으로 보류됐다. | 현재 `comparison_current=false`와 변경된 source 경로를 확인했다. 새 machine/aux/export를 기존 namespace에서 재처리하고 terminal→cumulative→notification disposition→night summary의 같은 세대를 대사한다. 옛 manifest의 pending0을 현행 완료로 해석하지 않는다. |
| 10/19 label | 기존 `label_bindings.sqlite`는20KiB, label0건이다. 갱신 machine의 해당 일6개 partition도 points0, `source_epoch_unverified`493,188행이다. `bind_natural_label`이 차용할 검증 label이 없다. | 기존 DB를 `mode=ro&immutable=1`로 조회했다. 현재/정규화 때 허용 epoch는 모두1792408975403344583으로 같다.1792406596116432835/1792406608106633860은 계속 제외되고, 닫힌660810 epoch receipt의 native 판정은 `unaccounted_raw_row_exclusion`이다. 상위 `main_raw_epoch_validation`의 raw 제외 증빙 없이는 옛 행을 label로 승격하지 않는다. 복구 가능성은 미확정이며 새 근거 없는 동일 전체 재생성은 하지 않는다. |

상위 원인은 `continuous_reversal_source._source_quality_receipt`가 `micro_reversion.observer_source_quality.main_raw_epoch_validation`의 닫힌 epoch 승인 범위를 적용하는 경로다. 현재 자료에서 이를 약세 reader의 label parser 오류로 판정할 근거는 없다. 허용 epoch의 새 정상 원천과 원 제외 epoch의 귀속을 분리해 확인한다. 기존324개 분석행·약세90행·PASS59행은 모두 U이고,177개 후보의 전향 확정 표본0/적격0은 유지한다. 위 수는 실제 거래나 고유 기회 수가 아니다.

### 지금 실행한 준비와 다음 자연 실행

- 현재 source scope를 메타데이터로 대사하면 수리 대상은10/16·10/19와 아직 미시작인10/20이다. 원 `schedule_cursor.json`을 복사한 격리 메타데이터 재현은10/20→10/16→10/19를 선택했다. 이는 실행 예측이며 운영 cursor/예약을 이동하거나 실제 처리한 영수증이 아니다. 원천/phase가 달라지거나 EOD가 실행 중이면 실제 선택·진입 시점도 달라진다.
- 조회 당시 운영 gate는 `outside_night_window`였다. 이미 설치된 cron의21:40~익일05:40 슬롯,06:30 종료, 최대9회/예약600초/worker1/512MiB, EOD 우선권을 유지한다. 새 cron/수동 worker/시간창 우회는 추가하지 않았다. 운영 원천 재집계는 기존 허용 야간에서 수행되며 지금 계산 완료로 표시하지 않는다.
- 완료 조건은 갱신10/16·19의 native currentness true, 해당 terminal/source hash 결속, 누적 대상 날짜/pending/invalidated·전향 분모·U 사유, 알림 적격/보류/배송 disposition의 일치다. 적격0/미지원 기계 역할은 정상 보류이며 약세만으로 Main 매매를 바꾸지 않는다. 원 epoch 제외는 별도 근거로 유지하고 새 정상 원천까지 결손인지는 다음 자연 수용으로 검증한다.
- 소비된 원 strict 체크리스트는 현 selected handoff가 참조한 historical snapshot SHA `7a91512b9e36e795d20be0f68f1e44208ef9f5d289546626771b5ab982944996`와 실제 bytes를 대조해 보존했다. 작업본 전체와 원 연구 상태/원천 참조도 수정 전에 임시 보관했다. 원 strict/controller/PREOPEN/handoff·consumed·selector·정책·runtime 연구 상태는 변경하지 않는다. 과거 PASS를 수정한 운영 문서의 새 PASS로 주장하지 않는다.

### 대체·제거와 검증 범위

| 기존 파일/함수/진입점 | 처분 | 현재 consumer와 이유 |
| --- | --- | --- |
| `automation/main_market_weakness_research.py`: scheduler/process_date/label_index/bind_natural_label | retained | 설치된 단일 야간 CLI가 그대로 사용한다. 원천 갱신을 기존 generation/checkpoint로 처리하며 중복 구현을 추가하지 않았다. |
| `deploy/run_main_market_weakness_research_postclose.sh`와 `MAIN_MARKET_WEAKNESS_RESEARCH_NIGHT` 등록 | retained | wrapper가 shared selector의 검토본을 매 진입에서 해석한다. native calendar 검증이 같은 명령·슬롯·코드 결속을 확인했다. 새 dispatch/등록은 없다. |
| 상위 epoch 검증·과거 cursor/비교/후보/outbox | retained | 원천 승인 consumer 및 불변 역사 근거다. raw 제외 증빙 부재를 우회하거나 원본을 삭제하지 않는다. |

대체 구현·이동·삭제 대상은 없고 제거 유예도 없다. 작업본 기준commit `fcd31ae7c2620a560cfca32fa25bd52e8776167e`, own scope는 기존 리뷰·당일 체크리스트 2개다. 비테스트 소스·테스트 변경은 각각 +0/-0, 문서는 +42/-0(리뷰31·owner11)이며 새 경로·모듈·진입점·branch 추가는 없다. 순증은 원인·인계·수용 기록이고 기존 작업본 prefix/다른 owner를 그대로 보존했다. 별도 보고 producer·validator·receipt framework를 만들지 않았다. 자체 리뷰→보완→재리뷰, 문서 로컬 링크53개·print-only backlog24개 중 해당 현재 owner1개·diff·보호 파일11개의 hash 불변을 확인했다. 문서·읽기 전용 메타데이터 작업이므로 Python/매매 suite, 대용량 raw 재생/전체 hash, provider/broker/Telegram 호출, 배포/재기동은 실행하지 않았다. 준비/인계 범위의 미해결 소견은0이며 야간 산출물의 실제 소비 수용은 미완료 OPEN이다.

### 10/20 마감 원천의 즉시 단회 재집계

사용자 “누락원천의 재집계는 지금해도 무방하지 않나?”를 기존 다음 액션의 즉시 실행 지시로 수용했다. 자동수집의 야간 제한을 닫힌 과거 원천의 운영자 단회 복구에까지 적용한 판단을 정정한다. 이 예외는10/16·19 원천과10/19 이하 누적 재집계에만 적용되며, 진행 중인10/20 원천·장중 writer·자동 cron/시간창 규칙은 바꾸지 않는다. 위 준비 기록과 실제 복구 결과를 구별한다.

- 16:53 기준 실제 selected는 다른 배포 세션에서 진행한 `d927d0d70f1daef2e2a6bf9aeccc0e0f1a028f26`다. 약세 코드 hash는 기존 설치와 같은f6f00912이며 calendar 검증 true, heavy owner false, 가용 메모리 약4.8GB다. 대상 물리 입력은10/16 약3.3MB·10/19 약52.4MB로 한정한다.
- 기존 selected producer의 `process_date`→`cumulative(through_date=10/19)`→알림 적격 대사→상태 발행을 사용한다. 동일 namespace lock 아래 낮은 CPU/I/O 우선순위·worker1·단계당55초/감독60초·전체180초/512MiB를 지킨다. 선택본 변경·heavy owner 진입·예산 초과 시 중단하고 checkpoint와 실제 실패를 보존한다. 운영 원천·정책/원 strict·후보 정의를 손으로 고치거나 상위493,188행을 다시 생성하지 않는다.
- 이번 예외는 두 날짜와 누적 대사 종료 또는180초 도달로 끝난다. 자동 야간 예약/설치/순환 위치는 보존하고, Telegram 전송 gate는 닫은 채 적격성만 대사한다. 단회 실행은 실제 시각과 `operator_closed_source_recovery`로 구분하며 야간 cron 실행으로 표시하지 않는다. 결과는 아래 실제 소비 대사로 추가한다.

### 단회 복구의 실제 소비 결과 — 16:56:27 KST

- 기존 namespace lock·selected producer로10/16→10/19→10/19 이하 누적/알림 대사를 실제 실행했다.3개 감독 자식 모두 exit0이고 전체6.992초, 자식 peak RSS71,380,992B(약68.1MiB)였다. 자식 합계 logical read240,407,730B·physical read110,985,216B·write8,032,256B를 기록했다. 이는 실제 작업 I/O이며 장중 성능 영향0을 측정한 결과로 해석하지 않는다. 물리 입력55,727,278B 외 native metadata·연결 검증·캐시 읽기 비용을 포함한다.
- 10/16 새 daily generation은 `0b6a593e193340f007b3fd2ce4d1160b06837acb1307e326a216270dfe4ea177`,10/19는 `196832a740a63d67d609e5873adde32443ac705c2d82ceed39b0165a219826c1`다. 두 날 모두 `completed_with_source_gaps`, phase completed, 현재 source/terminal/daily hash 결속은 true다. 원 일별 산출물·terminal은 seal과 상호 hash를 재검증해 보존했다.
- 현재 누적은 `fff32327a4ebb77c8975eae7222481a34eca3c1f4427448ac1d8f9cec5ce38e0`, through_date10/19·12거래일이며 `comparison_current=true`, pending/invalidated=[]·migration=false다. 진행 중인10/20 원천은 포함하지 않았다.177후보의 상태는 불확실171·source_gap6, 전향 resolved0·알림 적격0으로 유지됐다. 새 자료의 stored auxiliary 검증 결손은10/16 47건·10/19 51건이고 원 label/epoch 결손은 U로 남겼다.
- 실제 단회 attempt는 [7bb84aadd1194cf7b2fdda872871990d](../../data/report/main_market_weakness_research/attempts/7bb84aadd1194cf7b2fdda872871990d.json), 알림 disposition은 [7087bbfa](../../data/report/main_market_weakness_research/notifications/7087bbfa023265b44d7bd954b5f8d6d18e17990c0fdec7d31a0f1a0c85137985.json)의 `not_eligible`다. terminal→cumulative current→notification→attempt→night summary/last completed의 같은 세대를 검증했다. 단회 요약의 `night_id=null`, `execution_mode=operator_closed_source_recovery`는 이번 실행을 야간 cron으로 표시하지 않기 위한 실제 provenance다.
- 설치 설정·자동 순환 cursor·원10/19 야간 예약·outbox·selector 5개의 기존 hash가 그대로임을 확인했다. Telegram 전송은0이며 Main 배포/재기동·정책/주문 변경은 하지 않았다. 원 strict-bound snapshot도 그대로 보존한다. Python 생산 코드/테스트 수정은0이고 임시 운영 명령은 이번 두 날짜 복구 후 종료했다. 상주 worker/새 cron/CLI/validator는 추가하지 않았다.
- 갱신10/16·19의 물리 원천/누적/알림 상태 수용은 완료했다. 위 준비 단계의 “야간 대기”는 이번 사용자 예외로 해제됐고 단회 예외는 종료됐다. 즉시 복구의 비테스트 소스/테스트 증감은 각각+0/-0, 기존 리뷰/owner 문서는 직전 준비 상태 대비+19/-0이다. 재리뷰·native 소비 결속·문서 링크58개·parser24개 중 현재 owner1개·diff를 검증했고 다른 세션이 추가한 d927 배포 인계도 보존했다. 남은 owner 범위는 상위 raw 제외 증빙·새 정상 label·전향 근거의 자연 수용이며 코드/기계적 재처리 실패로 전용하지 않는다. 같은493,188행을 근거 없이 다시 재생하거나 현재 U를0/no-edge로 바꾸지 않는다.

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


## 압축 재결속·수집 증빙·일일 인계 배포 후보 — 2026-10-21

사용자 지시: 재기동 없이 배포본 준비만 실행한다. 기준 commit `faa67a01dbe6805c4b0219ec51e5cbf60b558f4e`에 이미 준비한 collector 종료/거부 전건 증빙·최초 자연 종료 전환과 지연 부모 호환성 수리를 포함한다. 격리 작업본 `KORStockScan-worktrees/weakness-source-handoff-20261021`에서 수정했으며 운영 selector는 ea68c5a85, Main PID1724066/start19233026으로 고정했다.

### 원인과 수리

- source20의 4개 normalized partition에 `source_epoch_unverified` 435,526행이 남아 있다. native close는 epoch1792493874709471241만 승인하며 해당 receipt SHA는7da52736cd1ce66406b82f621058645a71277cca6edfa35f523081bbc1e7d3d4다. normalized 행 제외를 detector 오판으로 취급하지 않는다. 앞선 collector cooperative shutdown·전건 rejection journal 수리가 후보 ancestry에 있으며 64/65/121건·reconnect와 손상/다른 PID·epoch·날짜 거부를 기존 정상화 소비자까지 검증했다. 현재 ea68 epoch는 유지하며 실제 새 closed·label 연결은 자연 수용 OPEN이다. 원 normalized 파일은 다시 만들지 않았다. 대형 normalized JSON의 추가 census는 기존32MiB 읽기 한도에 도달해 중단했고, 결론에는 원 frozen report의 행수·해시를 사용했다.
- source19 cursor196832a7은 원 trace/payload의 gzip 전환과 master 물리 파일 교체로 current=false다. master semantic hash c20d31bf는 같지만 기존 currentness는 물리 결속을 요구한다. `process_date`의 무조건 초기화 분기를 보완하여 완전한 원 읽기 해시·동일 코드/의존성·원 sealed 집계가 검증된 압축 전환만 projection을 재사용한다. gzip EOF/CRC와 전체 길이를 검증하고 기존 캐시에 세대별 증명을 보존한다. successor manifest→daily/terminal→cumulative를 통해 재결속하며 기존 산출물은 수정하지 않는다. 미래 plain native 수집도 같은 읽기에서 전체 증거 해시를 전달한다. 과거 native 읽기 해시가 없는10/19와 코드가 달라진 날짜는 정상 bounded 재처리가 필요하며, 이번 준비 작업은 운영 current=false를 해제하지 않았다.
- checklist builder `_carry_open_semantic_owners`의 제한 목록에 약세 연구 owner가 빠져 있었다. 같은 ID를 추가하고 OPEN/완료/target 우선·중복 및 원 Acceptance/History 보존을 검증한다. 원 strict-bound72fe9d12 snapshot을 native `preserve_checklist`로 검증한 후10/21 owner를 복원했다.
- 09:21 삼성전자 admission `FIXED-2026-10-21-005930-krx_regular-krx_nxt_integrated-63b8313a9eec`, generation3b66be93의 첫 warmup 서명 누락은 현재 ea68 및 후보에 기존 수리가 포함돼 있다. 기존 Main producer→pipeline→strict monitor와 rejected native claim→trace/guard/nonentry 회귀를 검증한다. 별도 관측 우회나 매매 기준 변경을 추가하지 않았다. 원 사건/누락 snapshot은 원본으로 유지하며 새 자연 영수증 수용을 테스트 결과로 대신하지 않는다.

### 리뷰·대체·검증·인계

원 구현으로 새 회귀를 실행하면 압축 재결속3건과 OPEN 인계1건이 실패했다. 수정 후 producer/consumer 관련9suite는1687 PASS였다. 재리뷰에서 원 cursor 집계까지 sealed daily/terminal과 대조하도록 보강했고, legacy native 없는 집계의0 기본값을 동일한 계약으로 보완했다. 최종 영향4suite274 PASS; CRC 손상·내용/길이/코드/마스터/의존성/집계 변경 거부, 원 cursor 보존, 동일 archive 재독0을 포함한다. 워밍업 source signature producer의 별도 회귀와 최종 candidate native checks 결과는 아래 준비 증거에 기록한다. provider/order/Telegram 호출은0이다.

| 기존 경로 | 처분 | 근거와 현재 consumer |
| --- | --- | --- |
| `process_date`의 모든 descriptor 변경 초기화 | consolidated | 동일 함수가 증명된 압축 변경에만 완료 projection을 재사용한다. 내용·코드 변경 및 증거 없는 legacy에는 기존 재생 경로를 유지한다. |
| native reader의 plain EOF 증거 누락 | removed | 같은 reader가 기존 읽기에서 전량 해시를 반환하고 기존 stream_receipts manifest가 보존한다. |
| checklist의 두-owner 제한 목록 | consolidated | 같은 builder에 약세 OPEN을 포함한다. 별도 checklist 생성기/등록은 없다. |
| 기존 collector close/거부 journal·신원 전달·엄격 detector | retained | 실제 native 정상화/trace/monitor 소비 계약에 필요하며 이미 준비된 수리를 재사용한다. |
| nightly wrapper·CLI·일정·재처리 reader·원 역사 증거 | retained | 기존 scheduled consumer와 legacy/changed-source 복구에 필요하다. 새 module/worker/CLI/dispatch는0, 삭제 유예는0이다. |

운영 연구 재집계·optional installer 재결속·정책 발행·selector 선택·재기동·자동 전환 예약은 실행하지 않는다. 후보 code closure와 실제 새 PID/closed epoch/전향 label/비용 후 경제성은 별개다. 기존 `role_unverified`·U·수집 미증명 행은 유지한다. 다음 전환 시 native 정책/currentness를 재검증하고 자기 optional code binding을 갱신한 뒤, 기존 야간 worker의 날짜별 source→누적→알림 disposition을 같은 OPEN owner에서 수용한다.

근거: [원 incident 대사](../../tmp/weakness-source-handoff-20261021/incident.json), [원 코드 실패](../../tmp/weakness-source-handoff-20261021/baseline-regression.txt), [관련 회귀](../../tmp/weakness-source-handoff-20261021/regression.txt), [보완 후 회귀](../../tmp/weakness-source-handoff-20261021/supplemental-regression.txt), [최종 준비 영수증](../../tmp/weakness-source-handoff-20261021/final-candidate/readiness.json). 이 마지막 영수증이 clean candidate/정확한 commit·native handoff·parity·보호 파일/PID 대사를 소유한다.

최종 정적 검증: 별도 fixed-watch producer/terminal135 PASS, compile·diff PASS, print-only parser23항목 중 해당 현재 owner1건이다. 기준faa67a01d 대비 비테스트 소스2파일 +117/-5, 테스트2파일 +106/-4, 문서3파일 +58/-0; 이동0·새 모듈0·신규 진입점0이다. 순증은 기존 owner 내부의 압축 원문/CRC·sealed 집계 검증과 회귀, 기존 Acceptance/History 인계 및 감사 기록이다. 다른 canonical 변경은 이 커밋에 포함하지 않는다.


## 실제 판정의 경로 라벨 수리와 제한 재처리 — 2026-10-22

사용자 지시는 장중 추가 로깅 없는 원인 수리·반복 리뷰와 과거7일 제한 재처리·누적/알림 판정 대사다. 기준 selected는b1519a2d4433401a5f969149789abfe3f1b76306, 설치 code a19fb4dd·native calendar true다. 격리 수정 branch는fix/weakness-natural-label-binding-20261022이며 Main 선택·재기동·설치/cron·매매 정책·provider/Telegram 호출 권한을 추가하지 않는다.

### 원인 → 수리 → 회귀

- 10/21 실제94행은 U였고 검증된 canonical72행 모두 기존 label key를 찾지 못했다. 기존 색인은 확인 리플레이 기회만 수록한다. 실제 WS의16자리 native epoch/route sequence와 collector의19자리 epoch/series sequence가 다르며, 실제 기회가 독립 리플레이 FSM에 다시 등장한다는 보장도 없다. timestamp 문자열 표현 차이를 느슨하게 대조하거나 가까운 가격을 차용하는 수리가 아니다.
- 기존 label_index에 native 경로 라벨 단계를 통합한다. 기존 native observation 검증과 actual ask를 그대로 사용하고, 선언된 WS namespace·event ID·종목/item·venue/session·기록 시각이 같은 원천 point에서 기존 K.label의 비용.0023/순+.4%/순-3%/1800초 CF를 계산한다. 기존 normalized streaming owner가 EOF/CRC·metadata를 먼저 검증한다. 한 partition의 완료는 기존 label SQLite에 저장하여 trace chunk마다 재독하지 않는다. 원 정책/기계/보조 응답과 guard는 바꾸지 않는다.
- 원 point가 제외됐거나 ask가 다르거나 신원이 충돌하면 U다.10/9 이전11열 역사 형식에는 WS 신원이 없어 U로 보존하고 현재/알 수 없는 namespace 계약 손상은 계속 거부한다. Source reader·path kernel·streaming reader도 연구 code binding에 포함한다.
- 제한 재생에서 새로 확인한 압축 trace 전이 결함도 수리했다. label 의존성 Deferred가 compressed source를 다음 source로 이동시켜 재개 후 빈 모집단 완료를 만들 수 있었다. 해당 이유에서는 staging을 되돌리고 같은 source/offset0을 유지한다. 기존 다른 압축 복구 소비자는 그대로 유지한다. 원 advance=True 조건을 재현하면 compressed CRC 회귀가 source_index 범위 초과로 실패하고 수리 후 정상 pending을 유지한다.
- 실제94행의 메모리 대사에서 W5/F3/U86으로 복구됐고 PASS29 중6행이 확정됐다(W3/F3). 이는 CF 경로 label이며 실체결/실현손익이 아니다. 첫 제한 native path 검증은3.358초/peak333,684,736B였다. 확인점이 제외된27건과 horizon이 짧은23건은 U를 유지했다. 이 probe는 전체 생산·누적 소비와 구분한다.

기본 원 코드의 생산→소비 회귀는 U/W assertion으로1FAIL이다. 변경 후 최종6suite312PASS는 namespace/seq/item/ask/clock/boolean/중복·source 제외·경로 gap·여러 실제 사건·완료 cache·CRC/세대 교체/namespace 손상·압축 pending·구 namespace 부재의 역사/현재 구분을 포함한다. 새 raw logging/수집기/worker/CLI/production module/주문·정책 변경은0이다. 격리 input root 재생은 source anchor와 observer source_path guard가 원대로 거부했다. 실패한 root와 시도는 남겼으며 이를 허용하는 guard 변경은 하지 않았다.

### 기존 경로의 대체·제거

| 기존 경로 | 처분 | 소비 근거 |
| --- | --- | --- |
| label_index의 replay-only 실제 label 연결 | consolidated | 같은 owner가 검증 native 사건의 path label도 기존 index에 작성한다. 새 producer/DB는 없다. |
| _index_label과 원 replay/alias reader | retained | 저장된 offline auxiliary·동일 신원의 역사 replay 소비에 필요하며 기존 부정 회귀를 유지한다. |
| bind_natural_label의 단일 alias 조회 | consolidated | 정확한 native-label 키를 우선 소비하고 원 typed/time/ask 검증을 유지한다. |
| iter_normalized_symbols | retained/extended | 기존 replay caller는 기존 기본값을 사용한다. 새 label caller만 명시적 metadata/역사 형식을 검사한다. |
| compressed Deferred의 무조건 다음 source 이동 | consolidated | label 의존성 실패에 한해 같은 source에서 pending, 다른 기존 실패 전이는 유지한다. |

새 module/worker/dispatch·제거 유예0이다. 추가 코드는 기존 owner의 native path label 기능과 서로 다른 실패 회귀에 필요하다. 기존 원천/실패/역사 reader와 퇴역 권한 경계는 보존한다.

### 실제 제한 복구와 마지막 소비

기존 selected producer로 과거7일을95.668초에 실제 재처리했다. attempt96a23e00d688455da70974c74940d0b9, peak112,721,920B, rchar1,931,948,531B/physical read952,967,168B/write413,630,464B였다. 새 누적02bee56f3d21cac201fc05cd71d0e9317119f0db4097972cadc1f83a62da98a2는9/29~10/21의14일이며 comparison_current=true·migration=false·pending/invalidated0, 후보184/적격0/not_eligible다. 설정·selector·cron cursor·원 night 예약·outbox5개 hash가 동일하다. 장중 성능 영향0을 측정했다고 해석하지 않는다.

수리본 code binding 때문에 무효화되는14일을 기존 canonical namespace에서 worker1/512MiB·단계60초/전체900초·낮은 CPU/I/O 우선순위로 단회 복구한다. 결정적 실패·무진전·selected/config 변경·heavy owner 진입 시 중단한다. 설치 code/calendar 재결속을 위조하거나 Main을 재기동하지 않는다. 정기 worker의 채택은 통합 배포/정식 installer 뒤 별도 확인한다. 이번 수동 복구와 후속 정기 소비의 코드 세대를 혼동하지 않는다.

원 strict checklist snapshot5d44c3e5b68855253bd1052229c1f6dad84e0d1eed476ea508d06bf111052747은 기존 preserve_checklist로 검증·보존했다. 원 source21/target22/미종결 owner를 유지한다. [단회 실행·원 실패·검증 근거](../../tmp/weakness-native-label-repair-20261022/)에 실제 결과를 보존하며 추가 최종 수용은 이 절에 기록한다.


### 보완 후 실제 최종 수용

추가 resource 리뷰에서 native label adapter가 전량 제외가 입증된 partition을 다시 해독하고 필요한 event horizon보다 큰 종목 배열을 메모리에 올리는 경로를 보완했다. sealed ref의 rows/epoch 제외 수와 points0이 일치하면 U를 유지하며 해독하지 않는다. 나머지는 기존 streaming reader가 native 사건의30분 window와 첫 horizon 이후 행만 보존한다. 원 symbol-row index를 함께 전달하여 label provenance가 바뀌지 않으며 invalid/sequence 단절도 남긴다. 한 symbol view는200,000행 이내다. 원10/15 v1 감독 중단은 세부reason이 남지 않아 memory/wall/순간 resource gate 중 어느 조건인지는 미확정으로 보존한다. 이후 각 supervisor의 exit/reason을 기록했고 v2의 모든 단계는exit0/reason=null이다. 이전 입력 root·계약 실패와 이 중단을 성공 이력으로 덮지 않았다.

hard interruption도 label_dependency_pending이라는 기존 압축 cursor 단계로 보존하여 다음 실행이 같은 source에서 다시 읽는다. KeyboardInterrupt 재현 뒤 실제 재개에서 판정 행/라벨이 유지되는 회귀를 추가했다. 최종6suite312PASS, compile/diff check PASS, automation/test Ruff의 신규 소견0이다. 공유 legacy stream owner의 전체 style 정리는 이번 범위에서 제외했다. 새 source helper의 기존 default consumer3곳과 기본/손상 회귀도 대조했다.

수리본의 실제 canonical 복구 attempt0886f27778594cb19a4b0fe08b7d6920은155.274초, worker peak127,467,520B(약121.6MiB)였다. 전체 rchar4,095,883,361B/physical read1,580,249,088B/write1,082,368,000B다.10/15는8.698초/92,217,344B로 완료했다. source 범위9/29~10/21의14일 전부 수리 code1b9f27f47b074c69b87ca3906d7cec4f9d2ad59ddc92af68fa4ff96003441c4c에서 cursor_current=true, 누적39d5f0b0ff5b69dc6e0cfcb2105753952674b53b76490e40062c8d1d2a20456f의 comparison_current=true/migration=false/pending·invalidated=[]를 직접 확인했다.

10/21 새 daily21d99a1580e059830839ec26b550ee43c2a78343da44f258e5c7c39d04c00ac2는 실제94행을 W5/F3/U86으로 보존하고 PASS29 중6행을 W3/F3으로 연결했다. 전체 분석18,649행의 W1513/F11931/U5205이며 원 raw epoch 제외206,358은 daily/terminal에 그대로 남았다. 복구된8행 중6행의 시장 연결은 RECOVERY/B,2행은 시장 연결U다. 이 표본을 확정 약세 조정 효과나 실현 이익으로 해석하지 않는다. 후보184의 전향 baseline resolved는 전부0, 상태178 uncertainty_unresolved/6 source_gap, 적격0이다.

native notification f569c0b602a61ba37a502e2c6169b624a893cbc3673f898219e72a4a52903d57은 not_eligible이며 같은 누적 generation·attempt·phase completed·manual summary를 대사했다. 실제 발송0, outbox/selector/설치/자동 순환 cursor/원 야간 예산5개 hash가 같다. 마지막 consumer 근거는 [직접 검증](../../tmp/weakness-native-label-repair-20261022/final-consumer-verification.json), [실제 복구](../../tmp/weakness-native-label-repair-20261022/reviewed-code-v2-recovery-result.json), [native 누적](../../data/report/main_market_weakness_research/cumulative/current.json)이다.

이 수용은 사용자 승인 단회 실행의 코드·자료·누적·알림 판정 수용이다. 실제 Main/정기 wrapper는 여전히selected b1519a2d4/설치 a19fb4dd다. 새 수리 code의 정기 채택·native optional installer 재결속과 다음 야간 소비는 미실행이며 통합 배포 owner에 남긴다. 설치를 손으로 고치거나 active selector/cron을 바꾸어 완료를 만들지 않는다. 정기 incumbent 코드가 새 연구 generation을 자기 코드로 해석할 수 없으므로 다음21:40 전에 통합 배포 세션이 이 차이를 확인해야 한다. Main 정책/PREOPEN·자연 주문·비용 후 경제성의 새 완료 주장도 없다.

Git scope baseline b1519a2d4433401a5f969149789abfe3f1b76306: source 2files +356/-19 (net 337); tests 2files +433/-2 (net 431); docs 3files +66/-0 (net 66). Moves0/new module·worker·entrypoint0이며 공용 reader는 기존3개 consumer를 유지한다. 실제 native path label·원 제외/경로 보존·chunk checkpoint와 서로 다른 부정 회귀에 필요한 순증이다. 별도 dirty 문서/런타임 변경은 포함하지 않는다.


## Effective registry 결속 수리와 7거래일 제한 복구 — 2026-10-22

판단: 실제 요청의 registry를 family 기본 binding으로 덮던 연결 결함을 수리했다. **검증 사례32건의 요청·응답 결속은32/32 verified이고, 그중 기존 실행 guard 거부15건은 조정 효과 분모에서 제외한다.** 닫힌7거래일의 daily→terminal→누적→notification→attempt/summary 수용은 완료했으나, 과거 reader 호환 증빙 누락425 PASS와 약세 경로 U 및 기계 수치 미지원은 남는다. 모든 원천이 복구됐거나 매매 조정 수치를 찾았다는 판정이 아니다.

### 원인과 기존 owner 수리

- `A.native_records`가 `G.load/binding/envelope`와 `I.validate_record/inherited/lineage_sources`를 소비해 실제 registry·원 prompt/input/schema·v2 wire/decoder·scope·확인 시점·component를 검증한다. `R.bind_native`는 기본 binding을 registry 선언에 대입하지 않는다. registry 선언의 미검증·변조·누락·미래 적용·component 불일치는 계속 거부한다. 미호출/실제 raw 보조판정·응답 후 실행 guard 상태를 구분하며, 유효 raw PASS라도 기존 실행 거부/결측 증거를 추가 보류의 이익으로 세지 않는다.
- 실제 request/response contract와 실행 contract를 분리했다. `entry_auxiliary_response_contract_valid=true`인데 `entry_ai_contract_valid=false`인 신호 만료/경로 변경은 registry 결속 실패가 아니다. 원 raw PASS는 보존하고 `auxiliary_execution_status`/이유로 기록하며, rejected 또는 증거가 없는 registry 판정은 post-auxiliary 비교에서 제외한다. 공용 `project_trace`의 장후 trailing reader도 회귀 검증했다. 기존 보조평가·기계평가·Main의 장중 request/capture/logger는 변경하지 않았다. 행별 helper는 기존 A.native_records 소유이며, bundle/cell/route만 캐시하는 scope_contract에는 실제 요청이 없어서 그 기본 계약을 변형하지 않았다. 기존 G/I 검증을 소비하는 연결부이고 별도 정책 validator/producer를 추가하지 않았다.
- 첫 제한 복구에서 전체 native machine 감사가 같은 immutable source를 행마다 재해시하는 비용을 발견해 worker를 중단했다. 연구는 기존 registry/overlay validator를 재사용하며 파일 identity가 유지된 provenance만 cache한다. 요청/schema/wire/scope/시점은 행마다 검사한다.10/14 rchar는 약13.0GB→최종 약93MB로 줄었다.20일에는 공통 ancestry를 각 index/projection 행에 복제해 `research_json_size_limit`에 도달한 원인을 수리했다. 기존 cursor의 경로별 dependency receipt만 보관하고 행의 중복 목록은 제거했다. MAX_JSON/시간/메모리/guard를 늘려 통과시키지 않았다. 초기 실패 로그·세대·oversize object·원 알림은 보존했다.

### 실제 제한 복구와 마지막 소비

범위는10/13·14·15·16·19·20·21이다. 이전9/29~10/12의7일 cursor/원본은 바꾸지 않았고22일 미종료 원천도 처리하지 않았다. `source_scope.recovery_from_date=2026-10-13`과 configured 시작일을 함께 봉인해 **새 코드로 검증한7일 누적**임을 표시한다.14일 전체가 새 코드로 current라는 주장은 하지 않는다. 후보 repair version을 갱신해 잘못된 기본 binding의 기존184후보를 재사용하지 않았으며, 원 manifest는 보존했다. 현재50후보/11scope는 모두post_auxiliary_withhold_cf이고 원천22일까지를 과거로 고정했다. 이 재처리를 새 전향 자료로 바꾸지 않는다.

| 검증 축 | 실제 결과 | 의미/잔여 |
| --- | --- | --- |
| 과거 원32 PASS 사례 | 결속32 verified; 실행 verified17/rejected15 | 기존 실행 거부를 새 보류 이익으로 계산하지 않음 |
| 7일 natural projection |4,879행; raw PASS556행 | 주문/독립 거래/실현 PnL 수가 아님 |
| raw PASS 결속 |verified131 / 과거 호환 증빙 미검증425 | 아래 missing receipt7개가 우선 장벽; 다른 검증 완료를 대신 주장하지 않음 |
| 약세 raw PASS |191행 모두U | 원 epoch/path/valid/horizon 결손을 W/F/0수익으로 바꾸지 않음 |
| 기계 수치 capability |438scope 모두role_unverified | numeric 역할·정의·before와 full confirmation/FSM producer 미지원; 기다리기만 해서 기계 후보가 생기는 상태가 아님 |
| 누적 비교·알림 |50 uncertainty_unresolved; 전향/유효 bootstrap0; 적격0/not_eligible | Telegram 발송0, 수치 조정 추천 없음 |

W/F는 원 비용.0023·목표 순+.4%/soft stop-3%/1800초의 CF 경로 라벨이며 실현 손익이 아니다.

10/13~10/19의5일에서 exact reader compatibility receipt7개가 없다(압축 alias도 없음). 해당 registry 관측1,236행 중 PASS425행은 `historical_reader_compatibility_missing`으로 별도 기록한다. 이는 시장 raw/경로 원천 결손이나 숫자 조정 미지원과 다르며, source의 원 request/registry를 잘못된 기본 binding으로 대체하는 근거도 아니다. 원 bundle/source/reader SHA에 대응하는 검증된 호환 증빙 또는 원 frozen reader 증거를 native owner에서 확보한 뒤 해당5일을 재검증해야 한다. 호환 PASS를 손으로 만들거나 guard를 생략하지 않았다. missing 파일의 출현/수정은 기존 cursor를 무효화하므로 실패가 영구 cache되지 않는다.

최종 code `e1ad38d4b460a90e4634f44092ae3b0d54b05fa95955518a425dc6c6f6a9ad33`, 누적 `9fe065264658ff3794327909b3ac545ba3c53ae396584e91ccd7ee7ff0a767ac`, comparison `9c97d9867f7917559c956b5fa26d1d58a772252a71de63bca2655e13833edacd`, notification `f1b1ac3a831f590b72a908e4228b87d5aa69171938152b8065f20113f2362810`이다. 같은 generation·source scope·candidate manifest·phase·attempt/summary를 마지막 consumer에서 대사했다. current=true, migration/pending/invalidated0은 위7일 범위의 수용이다. 최종 단일 nice19 worker 복구 93.990초, peak 158.4MiB였고 독립 projection 검증은 109,928,106B를 한 번 읽었다. source census가 복구 전과 일치하며 이전7일 cursor·설치/cron순환·outbox·manual veto·bootstrap/PREOPEN·selector hash를 보존했다. Main은selected fc51a179b/PID3913010/start30436408 그대로다.

### 리뷰·교체·남은 수용

baseline `fc51a179bfa63ff35390f5dbd3cbb7191229d0f3`에서 기존 source3파일과 test2파일을 고쳤다. 새 production module/worker/entrypoint/cron/provider0, moves0이다. 실제 registry/provenance·원 응답/실행 구분·bounded recovery scope와 큰 ancestry/음성 회귀가 순증 이유다. 최종 source +362/-20(net342), tests +561/-1(net560); docs3파일 +52/-0(net52)은 본 audit/운영계획/current checklist의 추가 기록이다.

교체/제거: registry의 기본 binding 대입과 notifier의 기본 parent-only 비교는 **consolidated**(실제 registry/parent 경로로 단일화); introduced 전체 machine 재감사 호출 및 index/projection의 반복 ancestry는 **removed/consolidated**(의존성 소유자는 기존 cursor). 기본 binding reader는 registry 미선언 자료와 원 replay consumer 때문에 **retained**다. 원 `I.audit_observation`은 submission_bottleneck_monitor의 native 감사 consumer가 있어 **retained**이며 변경하지 않았다. R의 selection·cost/label/epoch·typed machine role guard와 원 역사 자료/후보/배송 영수증도 **retained**다. 퇴역 consumer 복원이나 임시 wrapper·중복 dispatcher는 없다.

관련416회귀(공용 trailing reader와 원 보존 사례 포함)+기존 registry/wire/transition85회귀 PASS, compile/diff와 문서 link/owner/print-only parser를 검증한다. 검증 범위에 남은 코드 finding은0이며, 위 과거 호환 증빙/경로 원천/기계 capability와 후속 자연 전향 수용은 별도 OPEN이다. **Main 배포/재기동·정기 installer/code 재결속은 하지 않았다.** 설치/selected는 기존 code이므로 통합 배포 owner가21:40 전 새 커밋 채택 및 optional native 설치 재결속을 확인해야 한다. 새코드의 단회 결과를 정기 채택이나 Main PID 소비로 전용하지 않는다.

근거: [최종 소비·분모](../../tmp/weakness-effective-registry-repair-20261022/final-consumer-verification.json), [최종 복구](../../tmp/weakness-effective-registry-repair-20261022/reviewed-recovery/effective-registry-recovery-result.json), [과거 호환 증빙 결손](../../tmp/weakness-effective-registry-repair-20261022/historical-compatibility-diagnostics.json), [원 응답/실행 구분](../../tmp/weakness-effective-registry-repair-20261022/response-binding-failure-examples.json), [회귀](../../tmp/weakness-effective-registry-repair-20261022/reviewed-typed-regression-tests.log), [첫 실패](../../tmp/weakness-effective-registry-repair-20261022/recovery.log), [크기 제한 원인](../../tmp/weakness-effective-registry-repair-20261022/optimized-recovery.log).


## 2026-10-23 15거래일 제한 복구와 역사 reader 결속

사용자 승인에 따라9/29~10/22의15거래일을 현재 검토 코드로 재처리하고 daily→terminal→누적→알림→attempt/night summary의 같은 세대 소비를 확인했다. Main/정책/설치/cron·정기 야간 quota·수동 veto·outbox는 바꾸지 않았다. 현재 Main은9a8e59bfc/PID1134876/start35426396으로 유지됐다. 이 결과는 단회 source-only 복구이며 정기 코드 채택이나 자연 완주가 아니다.

- **원인과 수리:** 판정 전 거부를 native 결속·라벨 누락으로 분류한 연구 reader와 machine-only probe의 자연 판정 혼입을 수리했다. source22의148행은 사전검사51/평가 계약 거부97이며,17행은 probe다. 원 오류·U를 보존하고 사건/ask/라벨을 생성하지 않는다. 실제 native 판정304행의 결속과 별개다. 알려지지 않은 결속 누락은 계속 검출한다.
- **역사 결속:** 과거 I/G reader의 실제 검증은 원 당시 코드·원천을 요구한다. 현재 실행 적격 검사를 역사 연구에 그대로 적용하면서 누락된 현재 reader용 compatibility 증빙과 이후 코드 차이에서 탈락했다. 기존 native C owner로 exact bundle/source/old/new-reader 증빙9개를 발행했다. 원 코드 inventory/Git provenance·native overlay/inheritance 검증·lineage·registry/binding·물리 SHA를 봉인하고, 연구 A owner가 이를 현재 request/schema/wire/scope/시점에 대사한다. 현재 I/G/C/H·startup 검증과 provider/order 권한은 변경하지 않았다. 최초7조합 실제 기록 재현과 추가2조합의 원 native 검증을 통과했다. 보존된 f71c7d5f9 역사 reader worktree는 증빙 의존성이므로 잠금 보존한다.
- **리뷰와 교체:** 기존 project_native_observation/project_trace/bind_trace_native/effective_auxiliary_contract를 보완했다. 전환 전 거부의 무조건 missing 분류는 제거했고, 현재 runtime 검사를 역사 연구의 대리 판정으로 사용하던 부분을 original native proof 소비로 교체했다. 같은 코드의 현재 입력은 기존 native validator를 유지한다. 원 C issuer·현재 Main validator·shared trailing project_trace consumer는 유지한다. 새 module/worker/CLI/cron/장중 logger/보고서 producer는0이다. 현재 실행 코드를 완화하는 검토안은 반영하지 않았다.
- **검증:** 원 회귀에서 분류4FAIL을 보존했고 수리 후 관련592 pytest·compile·diff 검사를 통과했다. missing/수정된 코드·증빙·원천·registry·원 bundle/scope/응답 및 기존 실행 거부는 계속 제외한다. scope baseline은9a8e59bfcb4283416717311fc8ddd22d37aa7602다.

- **규모:** baseline9a8e59bfc 대비 non-test source2파일 +132/-5, tests1파일 +175/-0, docs2파일 +44/-0(본 항목 포함), 이동0이다. 순증127 source 행은 기존 A/R owner의 역사 증빙 검증과 판정 전 거부 분리에 필요하며 새 진입점은 없다.

| 최종 수용 | 결과 |
| --- | --- |
| 연구 코드 | `5ea7e987f646a3f16496d585d31b383609127784341c9a0a13021671fb873b11` |
| 누적 generation | `43e541740d08be2e7576c1e2d23c80895262f4aec2a52b63670092390828b8fe` |
| 비교 SHA | `80072bc10f058d94b31109c3018def8dba710cb9bd7ab95e3a59147032581b97` |
| 알림 SHA | `4cead5264634b7a2a80a642efea983f76a2f4624419e71c84b4319ece52e3a9f` |
| 날짜/현재성 | 15/15·검토 코드 current=true·migration/pending/invalidated0 |
| registry 선언 native 관측 | 2,433행 effective verified·미검증0; 고유 매매/주문 수가 아님 |
| 후보/알림 | 273후보·267 uncertainty_unresolved/6 source_gap·적격0·not_eligible·발송0 |
| 전향 기준 | cutoff10/22 110개,10/23 163개; 전향 resolved273개 모두0 |
| 자원 | 누적 연구 실행564.683/600초·단계60초·worker1/nice19·peak164.0MiB/512MiB |
| 실행/조회 시간 | 연구 실행 예산과 코드 검토·읽기 전용 대사 경과시간을 구분한다. 정기9회/예약540초는 그대로다. |

최초15일 계산479.460초 뒤10/8·12의61행에서 추가 증빙2개를 발견했다. 남은 동일 실행 예산으로 이 두 날짜만 재개하고 누적/알림을 갱신했다. 시간 제한에서 중단한10/15·22·8은 원 checkpoint의 실제 진전을 확인한 후 재개했으며 전체15일을 무변경 재실행하지 않았다. 로그와 최초 generation984e455d·후속 실패/부분 진행을 보존했다.

원천 보존의 추가 검사가 stale cursor의 물리 descriptor를 비교해 실패한 기록도 남겼다. native 계산/누적/알림은 이미 완료했으며,10/21 gzip 전환·10/22 보고서/마스터 갱신은 모두 이번 실행 전임을ctime와 현재성으로 확인했다.10/21 native stream의 decoded bytes/SHA 및 마스터 semantic SHA도 동일했다. 검증 가정을 바로잡고 현재 source signature/세대·보호 대상 hash를 재확인했으며 원천/상태를 검사에 맞춰 수정하지 않았다.

**남은 원천·의미 한계:** 기존 raw PASS95행은 실제 request/registry 증빙 누락이 아니라10/13의 원 raw-response 계약 증빙14행 부재와10/14의 계약 불합격81행(지원 fact78/인용3)이다. 이를 유효 PASS로 승격하지 않았다. 이와 별도로 오래된 PASS50행은 registry binding 항목이 없는 역사 자료다. source22 PASS48행은 결속 verified이며 W7/F21/U20, 기존 실행 거부9를 분리한다. source22의 약세 raw PASS10행은 F10이나 하루의 CF 진단이며 전향 우위·실현손익 또는 조정 수치의 근거가 아니다. 과거 epoch/path/horizon 결손과 기계 numeric role 미지원도 유지한다.

선택9a8의 연구 코드 `bc81483cf3fa51b1ba5802a34b311a9af43dfc4c414af0dd8fd2e0aa28bf6ec4`/설치 binding은 정상이나 이번 검토 코드와 다르다. 통합 배포 owner가 이 수리 commit을 선택하고 기존 optional installer를 재결속해야 정기 연구가 같은 코드를 소비한다. 매매/PID 전환은 이번에 실행하지 않았다. 다음 source23→10/24 야간의 무보정 자연 수용은 기존 MainMarketWeaknessPostcloseObservation1008에서 OPEN으로 유지한다. 운영 계약은 [§16](../proposals/main-market-weakness-postclose-source-binding-and-candidate-repair-plan-2026-10-13.md#16-2026-10-23-과거-15거래일의-제한-복구와-역사-검증)이다.

증거: `tmp/weakness-binding-recovery-20261023/final-consumer-verification.json`, `checkpoint-completion/result.json`, `legacy-response-contract-classification.json`, `final-research-regression.log`, `historical-real-cases.json`, `recovery.log`, `supplemental-recovery.log`와 원본/실패 기록.

## 2026-10-23 역사 코드 복원·정리 보호·요약 의존 검사 수리

사용자의 복원·수리·영향5일 재검증 지시에 따라 삭제된 역사 코드2곳을 복원하고 같은 `MainMarketWeaknessPostcloseObservation1008`에서 원인→수리→회귀→native 소비를 확인했다. Main/정책/selector·PID·정기 cron/설치·야간 quota·outbox는 유지했다. 원 상세 실패와 삭제 journal, 이전15일 복구564.683초 및 후속 조회 기록을 보존했다.

- **최초 위반:** 정리 보호 그래프와 삭제 직전 대사는 startup/machine/bootstrap 소비에 의존했고 optional 연구의 cumulative→날짜 cursor→source manifest→역사 코드 의존성을 누락했다. historical `operating_pointer` 제외가 이 살아 있는 소비까지 제거했다. 기존 요약 검사는 설치/calendar·세대·source scope/cursor 상태만 대사해 상세 현재성10/15 실패에도 `verified/findings=[]`를 반환했다. 검토 대상은 과거 raw-response/라벨 결손과 구분되는 현재 보존·탐지 결함이다.
- **복원:** 보관 Git ref의7e1a826318e7b8418afd2e2436b79bf2febf8f67(`main-market-weakness-20261009-v1`,1,002파일)와59c92909783e967397a8d774bab60cd22ec78c96(`holding-sentinel-performance-20261016-59c929097`,1,145파일)를 원 native inventory의 SHA256과2147개 모두 먼저 대사했다. 원 경로·공유 mount를 복원하고 Git worktree 잠금을 설정했다. inode/mtime/ctime을 과거 값으로 만들거나 원 영수증을 바꾸지 않았다. 잠금 해제는 현재 연구/증빙이 이 원 코드를 더 이상 소비하지 않는다는 동일 owner의 증거가 생긴 뒤다.
- **기존 owner 수리:** `lifecycle/research_storage.weakness_dependency_inventory`가 현재 누적 포인터·날짜 cursor·봉인된 manifest의 date/generation/authority/code와 의존 stat를 대사한다. 정리는 missing/stale 경로도 보호하며, 요약은 같은 폐쇄의 현재성을 사용한다. 원천·역사 코드 전체 hashing은 native 연구 owner에 남긴다. metadata는 파일2MiB·기존 shared64MiB 합계·256날짜/65,536참조·depth64 내 nonblocking regular-file read로 제한하고 변경/상충/예산 초과는 성공 처리하지 않는다. 현재15일 metadata15,063,759B·고유 receipt10,115개이며 raw stream을 health에서 읽지 않는다.
- **정리 소비와 경쟁 조건:** 실제 `tmp/storage-live-usage-20261023/usage_refs.py`의 graph와 `release_cleanup.py`의 삭제 직전 references가 이 폐쇄를 보호한다. 기존 `tmp/source-disk-cleanup-20261022/worktree-audit/execute_worktrees.py`는 release-set 잠금 아래 연구 writer 잠금도 삭제 끝까지 보유해 새 결과 게시와 경쟁하지 않는다. 현재 selected926의 startup/machine/bootstrap 읽기 검증과 두 잠금을 보유한 실제 references 조회에서 두 코드 원본1,002/1,145경로가 `current_research_dependency`로 보호됐다. 삭제는 호출하지 않았다.
- **리뷰·회귀:** 실제 선택 원본을 먼저 import한 재현에서 missing/changed/복원 후 새 inode3건의 잘못된 `verified`를 확인했다. 수리 후 producer/manifest/cursor→요약→semantic alert, 정리 graph/삭제 직전 소비/연구 lock, missing·변조·다른 세대/권한·symlink/FIFO·예산·기존 역사 missing/새 증빙 출현을 검증했다. 최초 검토의 manifest generation 필드 가정을 실제 descriptor digest 계약으로 바로잡고, 삭제 중 새 게시 경쟁을 writer lock으로 보완한 뒤 재리뷰했다. 최종580 pytest·compile·diff 검사를 통과했다. 최초 baseline pytest의 import 격리 미흡과 read-only 정리 검증의 control-directory helper 경로 누락은 별도 보존하고 정확한 import/동일 native caller로 재검증했다. 이를 production 재계산 실패로 합치지 않는다.

영향10/8·12·14·15·16만 선택 릴리스의 기존 A reader(code5ea7e987)와 native `process_date`로 새 dependency 세대에 재결속했다. 다른10일 cursor 바이트와 직접 source-plan/dependency/observation/listing/snapshot은 유지했다. 새 보존 결함에 대한 이번 승인 복구는 기존600초 한도 내134.539초·6단계·worker1/nice19·peak128.1MiB였다. 물리 read1,342,435,328B, 논리 rchar6,666,221,302B이며 정기9회/예약540초나 이전 복구의 예산/attempt를 초기화하지 않았다. 무변경 전체15일 replay 없이 누적·알림 등 무효화된 후행 소비만 갱신했다.

| 최종 native 소비 | 결과 |
| --- | --- |
| attempt | `3266b64c4d52454da1c00f80c22c5ffe` / `operator_historical_code_restoration_five_day_recovery` |
| generation | `8337812bbe4313ba97d5d6a55731784517bd4f455583c008a771273e069a6fac` |
| 비교 SHA | `1fffeaaa1c3b0af871e3e161b48fa9bcc79555b3119756917a6bc63ceddc1797` |
| 알림 SHA | `c4a0ad50d9849aaf324eeaf40f05fb08e0436c9456f58684e18787a14e5c83c3` |
| 상세 현재성 | 선택926 실제 A reader로 current15/15·migration/pending/invalidated0 |
| 실제 registry 관측 | effective verified2,433·미검증0; 고유 주문/매매 수가 아님 |
| 비교/알림 | 후보273·267 uncertainty_unresolved/6 source_gap·전향 resolved273개 모두0·적격0/not_eligible·Telegram0 |

새 비교는 generation을 제외한273개 후보의 정의/결과·기준 시점과 이전 비교가 모두 동일했다. native cumulative→알림 immutable receipt→attempt→night summary/last completed의 같은 세대와 hash를 확인했다. 수리한 요약 consumer는 현재 자료를 통과시키고, 실제 자료에서 두 코드 의존성 부재를 주입한 읽기 전용 음성 검사에서는 정확히 영향5일과 `optional_research_dependencies_not_current`를 검출했다. 기존 raw-response 증빙14부재/81불합격·오래된 registry 항목 없는50행·epoch/path/horizon null·기계 role 미지원은 복원된 연결 결함과 분리하며 유효 표본으로 만들지 않았다.

Replacement/removal: 기존 metadata-only `native_validated`/완료 predicate는 dependency 소비를 포함한 판정으로 consolidated; 기존 A의 full currentness/역사 hash·C issuer/validator와 정리의 기타 보호/역사 분류는 retained다. startup trace를 optional 연구 보호의 대리로 삼던 경로는 replaced이며 actual graph/locked references는 shared collector를 소비한다. 원 삭제/failed receipt와 과거 release는 retained evidence다. 임시 read-only 검증 helper alias는 실제 references 종료 후 removed; 정식 caller는 동일 owner만 유지한다. 새 production module/worker/cron/report producer/매매 entrypoint/장중 logger0이다. baseline926 대비 non-test source2파일+147/-4, tests2파일+121/-0, 운영 tmp caller3파일+19/-1이며 문서 추가는 별도다. source 순증은 기존 저장 owner의 의존 폐쇄와 안전한 bounded read에 필요하다. 운영 caller는 기존 ignored tmp owner이므로 별도 패치와 원 bytes도 보존한다.

**배포와 자연 수용:** Main은 선택926/PID1982231/start36273583으로 유지했다. 연구 A 코드와 설치 지문은5ea7로 동일해 재결속 설치 변경은 필요하지 않았다. 정리 호출부·공유 workspace helper는 적용했고 새 요약 detector 코드는 검토 후보/작업공간에 있으며 immutable 선택 릴리스에는 아직 반영하지 않았다. 통합 배포는 기존 review/P5/권한 계약으로 분리한다. 이번 결과는 수리 보조 복구이며 source23의10/23 21:40→10/24 05:40(06:30 종료) 정기 무보정 자연 연구 수용은 같은 체크리스트 owner의 OPEN이다. 매매·provider·broker·threshold·holding·수동 veto와 주문 권한은 변경하지 않았다.

증거: [복원](../../tmp/weakness-binding-recovery-20261023/restoration/result.json), [native 복구](../../tmp/weakness-binding-recovery-20261023/restoration/recovery-result.json), [최종 소비](../../tmp/weakness-binding-recovery-20261023/restoration/final-verification.json), [선택 A reader](../../tmp/weakness-binding-recovery-20261023/restoration/selected-reader-verification.json), [실제 정리 보호](../../tmp/weakness-binding-recovery-20261023/restoration/cleanup-validation/current-native-protection.json), [원 실패 재현](../../tmp/weakness-binding-recovery-20261023/restoration/original-detector-exact-import.log), [580 회귀](../../tmp/weakness-binding-recovery-20261023/restoration/final-regression.log), [운영 caller 패치](../../tmp/weakness-binding-recovery-20261023/restoration/operating-callers.patch). 운영 계약은 [정리 S2](../proposals/runtime-and-research-storage-cleanup-plan-2026-10-05.md#s2-미참조-releaseworktree)에 유지한다.

## 2026-10-23 two-market observer and retained-source revalidation

Baseline: selected6d8891ac3771d26e2f764c7d8bd87211549bfa1a, Main3299469/start38150614; isolated worktree starts at7b352107e (documentation successor). Owner remains MainMarketWeaknessPostcloseObservation1008; original evidence is preserved in tmp/weakness-cron-repair-20261023/incident-pin.json.

Cause: observation market-weakness-bbadf2ba5c5d778fa759 contains both KOSPI and KOSDAQ, but the producer emits SINGLE_MARKET_WEAKNESS when independent market triggers pass without the weighted composite panic threshold. The strict observer correctly rejects single_market_scope_invalid. build_market_weakness_observation now labels this existing two-market scope BROAD_WEAKNESS. Weighted risk_off, thresholds, affected markets, hysteresis, freshness and trading authority are unchanged. The native notifier consumer is exercised with healthy, missing and stale observations.

The panic_sell_defense cron registry now uses the existing recurring owner-terminal recovery path. Only a later genuine same-owner DONE supersedes prior errors; newer FAIL/START, SKIP and another owner's DONE remain distinct. The existing finalization late warning remains truthful: source22 finalization was rebound at07:27:27 after06:50, with current native generation valid. This is recovered completion, not on-time natural acceptance; no original log/receipt or cutoff is rewritten.

Review: original causal regressions fail6 cases; revised targeted collector/notifier/cron/research/source-repair/entry-guard/finalization suites pass587 cases. Compile and diff checks pass. Tests use private temporary DATA_DIR, production write isolation and mocked network. Replacement disposition: the one-market-only assignment is removed and replaced in the same producer; panic recurring error interpretation is consolidated into the existing owner recovery helper. The strict consumer, weighted classifier, wrapper, source readers and late completion checker are retained for their current consumers; no new source module, wrapper, registry or production entrypoint is created. Source +6/-1; tests +50/-2; docs +17/-0.

The new collector and previously integrated streaming reader change optional research code identity. Revalidate the fifteen retained dates09/29 through10/22 through existing process_date/checkpoint, cumulative and notification owners, preserving original source bytes and null/excluded economics. This operator-authorized attempt is bounded to600 seconds,55-second child checkpoints,512MiB memory and no network/notification; unchanged/no-progress stages stop. Scheduled night allowance and installation history remain unchanged. Deployment and actual consumption are recorded below after native validation. Next source23 night research and10/26 fresh observer remain OPEN under the same owner.

### Integration of d53c36e59

The user added d53c36e59 after the first fifteen-day recovery completed in496.969 seconds (generation5fcbc71d9809d03981233f0850baa7fa4098aecd29735789852acfc2d8235502, current15/15, pending/invalidated0,273 candidates, not_eligible). That exact attempt remains immutable. The new branch includes027a35968 and changes the shared continuous_reversal research kernel, so its new optional-code generation needs separate native revalidation; the earlier PASS cannot certify it.

The integration retains exact-item REST completed revisions separately from WS bars, freezes research snapshots, rejects missing/altered revisions and ambiguous/conflicting labels, and binds the producer/consumer code in native preparation. No request/FID/parser, quote clock, runtime signal rule or policy threshold is changed. Existing completed_bars is extended; its six research consumers pass their frozen source to the same owner. The previous live-source rediscovery path is replaced for new frozen populations, and existing WS/broker readers are retained. Native reviewed source pairs and independent Main preparation inventory retain the issued holding-stream profile. Incoming branch delta: source+253/-26, tests+166/-4; no new module or runtime entrypoint. Integration tests and final exact-candidate native proofs are recorded in tmp/weakness-cron-repair-20261023/integration-d53 and its sibling integrated-tests.log.

Integration review completed: targeted617 tests pass, plus9 direct pytest isolation/production-write-guard regressions. The broader legacy inventory run was intentionally stopped after2792 passing cases; its remaining unrelated matrix is not claimed passed. Capability-fixture preparation identified the setup defect already pinned at task start: autouse imports initialize a writer before per-test DATA_DIR patching, so the production write guard correctly rejects it. The existing pytest_configure now binds default data/tmp/log/config paths to its private session root before collection. Audit and Landlock protections stay enabled. The old logger-only scratch initialization is consolidated into that same session root (tests+24/-1, production source unchanged). This does not weaken production custody or permit fixture output into operating reports. Final native fixture publication and exact-candidate P5 follow from the clean successor.


### Final capability handoff review and actual recovery

The integrated97a72d632 release completed ordered deployment at16:28:43, with Main3606961/start38501423 and independent exact-PID policy consumption. Native signal parity matched128 scopes/76,800 rows/568 hits with zero mismatches. Candidate and selected P5 passed. The final fifteen-day research attempt25a2145c62624171a710fea1d3b4193c completed in433.955/600 seconds; code8a496015234381d1b8654223ae86a31a4a996bc20ebb4956cb7c7f3694a4945e, cumulative2872c16a505260c72519489ff4058e88142a186d2eae3b3ea39332132524708f, current15/15 and pending/invalidated0. Candidate count273, eligible0/not_eligible and unresolved/null economics remain unchanged. Physical read2.437GiB, logical19.509GiB, peak150.67MiB; seventeen bounded stages and one checkpoint resume. Original first attempt and subsequent code invalidation are preserved separately.

The selected native optional installer rebind passed; cron bytes, notification setting, calendar, source start/history, scheduled quota/cursor and outbox were preserved. Exact selected consumer checked15 source days and10,115 dependency receipts with10,684,051 metadata bytes. Real source collection via the existing panic owner then completed at16:31:06: observation market-weakness-ebd740b06ffecc9bcfb5, observer ready=true, consecutive_failures=0, runtime_effect=false. Full health no longer reports the panic cron failure. Historical source22 finalization remains a truthful late-recovery warning (07:27:27 after06:50); current native finalization generation is valid.

Postdeploy review found one affected-contract omission: d53c36e59 makes reversal_cumulative_postclose.build pass its frozen source to completed_bars, changing auxiliary capability generation618c3e354 to8659bf214. The reviewed successor inventory still ended at618c3e354; new independent95-test network-denied fixture existed but could not bind the original10/22 report. An added auxiliary case in the existing latest-capability regression fails before repair (1FAIL/3PASS). The existing frozen-input successor inventory now includes only the exact507700d07-to8659bf214 pair. It preserves the prior pair, original report SHA5a0c790a13a5cfd89e393fab24d5668525149687982e06e8983d66ff7269f74a, original fixture SHA459e8179ef50ddd28b96f9ffbf6df60b18253c27ea112db6cfba0238a36aa0a3 and all economic/source states. Exact native original-report consumption verifies current capability only; historical_contract_status remains unverified and native_validated=false. Missing/mutated historical/current fixture, wrong code and unknown successor negative cases remain enforced. This is not historical research-result promotion or new trading authority.

Replacement/removal for this supplement: existing frozen-input inventory and its consumer retained/extended; no parallel fallback, validator, module or report producer. Tests consolidate an unused review-map parameter and cover the omitted auxiliary family. Source+5/-0, tests+5/-7; docs counted separately. Review evidence: tmp/weakness-cron-repair-20261023/integration-d53/auxiliary-original-regression-isolated.log and auxiliary-exact-native-consumer.json. The exact successor must pass tests, candidate P5 and ordered deployment before this new capability link is operational; the research code itself is unchanged and does not require another fifteen-day replay.

Supplement validation:1,981 policy-generation/contract/ordered-deploy tests passed in61.22 seconds; compile, diff and print-only backlog checks passed. Current exact auxiliary report/old fixture/current fixture consumption passed without changing source bytes. Supplement docs+14/-2; source/test totals above are separate.

The b7550b0c6 candidate was blocked before drain by entry_consumer_reviewed_dependency_unreviewed for policy_generation_code_handoff.py: its complete native deployment profile still named the predecessor bytes. Main97a72d632/PID3606961 stayed running. The existing handoff now separately binds the exact reviewed capability reader and independent Main preparation inventory, preserving the actually consumed REST/holding profiles and original policy origins. Offline regressions cover all three family consumers and missing/dirty/committed/mixed generations; no guard or accepted-error bypass is added. This supplement changes source+50/-2, tests+21/-3; runtime research code8a496015 and auxiliary capability code8659bf214 are unchanged, so existing native recalculation/fixtures retain their exact code binding. The failed preparation and clean candidate are preserved under integration-d53/capability-deployment.

Deployment-inventory re-review:147 targeted native handoff and independent Main-preparation cases passed in115.33 seconds, including previous consumed REST/holding profiles and current missing/dirty/committed/mixed dependency rejection. Compile/diff/print-only parser passed; docs+5/-0 for this inventory supplement. Exact candidate preflight and P5 remain mandatory before any further drain.

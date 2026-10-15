# Main 약세 장후 처리 순서·관찰 근거 고정 구현 리뷰 — 2026-10-15

## 결정과 확인한 결함

사용자 “우선순위 개선하고 코드리뷰 후 수정보완을 반복하라”에 따라 날짜 처리 정체, 기존 성과 연결의 결손 설명, 관찰 근거 고정을 보완했다. 기존 `automation/main_market_weakness_research.py`와 `src/tests/test_main_market_weakness_source_repair.py`를 수정했다. 신규 Python 모듈·장중 hook·로그·조회·API/AI 호출은 없다. 기존 보조 입력/응답·정책·주문·수량·Main/manual custody·퇴역 경계는 그대로다. `korstockscan-review-gate`의 구현→자체 리뷰→수정→재리뷰→표적 검증을 적용했다.

착수 선택본은 `observer-publication-integrated-20261015-27e1b5bdf`였고, 연구 code SHA `7c12303a880d3d7eeccede1fb61a7e260718c2b6f74bb4b895bc40e2d3d67acd`와 optional 설치/cron binding은 일치했다. 이 검증은 이번 작업본의 배포를 뜻하지 않는다. 착수부터 있던 수정·미추적 파일은 보존했다.

[10/14 야간 기록](../../data/report/main_market_weakness_research/nights/2026-10-14.json)의 실제 worker 시도는 7회다. 22:40~익일 04:40에 10/14와 9/29만 반복 선택했고, 마지막 네 번은 `delta=0`이었다. 10/7·8·12·13의 old-code cursor는 누적에서 제외된 채 알림이 `deferred_migration_or_comparison`에 머물렀다. 마지막 계산의 분석 표본은 1,719개, 시장 상태 연결 857개, 약세 581개, W/F=0/U=1,719, 보조 이후 후보 17개·적격 후보 0개였다. 이는 당시 [누적 포인터](../../data/report/main_market_weakness_research/cumulative/current.json)의 역사적 계산이며 이후 자연 결과로 대체될 수 있다.

## 구현·리뷰·보완

| 결함 | 변경 | 수용 검증 |
|---|---|---|
| `notification_pending` 양 끝 날짜가 중간 날짜의 원천 갱신을 계속 선점 | 원천 미완료/무효 날짜를 phase 재시도보다 먼저 처리. 자기 namespace의 봉인된 `schedule_cursor.json`으로 날짜 순환 위치를 밤 사이에도 보존. worker 시작 전에 위치를 예약하여 실패한 날짜도 다른 날짜를 독점하지 않음 | 양 끝 알림 대기·중간 7일 갱신 필요·계속 실패하는 날짜·자정 경계에서 모든 날짜를 순환 방문 |
| 자정 이후 당일 자료가 전날 야간 작업에 섞일 가능성 | source date를 `night_id` 이하로 제한 | 아직 열려 있는 다음 날짜만 있으면 worker를 시작하지 않음 |
| 원천 파일이 사라진 날짜가 discovery에서 사라져 migration 대기가 지속 | 기존 cursor 날짜도 discovery에 포함하되 원 clean/source floor·시장일 필터 유지. 원천 부재는 `retained_decision_sources_unavailable`로 명시 | 없는 자료를 valid-empty/no-edge로 처리하지 않고 source-gap 세대로 완료; migration 갱신 가능 |
| 종료 영수증 결손으로 비어 있는 replay partition이 조용히 0개로 통과 | 빈 partition·날짜 partition 부재·상위 `source_epoch_unverified` 등 사유를 daily input exclusions와 terminal gaps까지 전달 | 보존된 정확한 event/time/ask 라벨은 W로 연결. 결손은 U 유지. 정상·결손 partition 혼합에도 정상 표본의 W 연결 유지 |
| 과거 분석이 갱신되는 `tmp/market_weakness_observer_state.json`의 stat에 결속 | 장후 읽기에서 exact observation ID/as-of가 맞는 상태의 원 bytes·SHA를 자기 immutable `observer_receipts`에 보존. 다음 계산은 같은 snapshot을 사용 | 현재 상태가 다음 날로 바뀌어도 과거 generation/delta=0 유지. 원 observation 추가/수정/삭제는 계속 무효화 |
| snapshot 저장·읽기 경계 | archive 날짜 거부를 snapshot 쓰기보다 앞에 배치. bounded read/stat 재확인·namespace·원 path·schema·authority·content hash 검사 | 손상/삭제/외부 경로/잘못된 타입·authority를 명시적으로 거부하고 현재 상태로 대체하지 않음 |

최대 9회/회당 60초/야간 예약 총 600초/worker 1/512MiB와 EOD 우선·시간창 gate를 유지했다. 시간창 밖에는 rotation, snapshot, source discovery를 시작하지 않는다. 후보 정의/동결 날짜, 통계·Telegram 적격 기준은 변경하지 않았다. 이번 code hash 변경은 원천 재검증을 요구하지만 기존 후보를 다시 탐색하거나 과거를 새로운 전향 표본으로 만들지 않는다.

## 복구할 수 없는 원천과 운영 수용

10/14 상위 [machine-comparison](../../data/report/continuous_reversal_operating/2026-10-14/machine-comparison.json)의 당일 4개 partition은 원천 325,887행, `source_epoch_unverified=325887`, 확인점 0개였다. 실제 보존된 closed collector 영수증의 허용 epoch는 장중 원천 epoch를 포함하지 않는다. 이는 이번 reader 코드로 복원할 수 있는 라벨이 아니다. 원천의 종료·대사 증거를 합성하거나 epoch 검증을 완화하지 않았으며 기존 원천/상위 보고서를 재작성하지 않았다. 진단 보완과 날짜 처리 복구를 과거 1,719개 성과 복구로 표시하지 않는다.

기계 수치 축의 `role_unverified`, 완전 확인점 재생의 `confirmation_replay_unavailable`도 남는 capability 경계다. 숫자 역할을 새로 부여하거나 실제 매매 민감도를 변경하지 않았다. 지원되는 보조 이후 연구와 원 기계/보조 패턴 연구는 분리된다.

운영 owner는 [10/15 체크리스트](../checklists/2026-10-15-stage2-todo-checklist.md)의 `MainMarketWeaknessPostcloseObservation1008` 한 개다. 이후 선택 배포본/optional code rebind 수용과 실제 허용 야간에서 중간 날짜 진전→migration 종료→누적→알림 disposition을 확인한다. 역사 결손은 분리하여 남기고 실제 적격 후보가 있을 때만 기존 Telegram 경로를 사용한다. 이번 작업은 배포·Main 재기동·cron 변경·운영 연구 재계산·Telegram 실발송을 수행하지 않았다.

## 검증

기존 연구 4 suites 169개를 먼저 통과한 뒤 날짜 순환·snapshot·실제 형태의 label 연결 회귀를 추가하고 재리뷰했다. 재리뷰에서 원천 소실 날짜의 discovery 누락, archive 거부 전 snapshot 쓰기, snapshot path/type/authority 손상을 보완했다. 최종 검토 범위의 미해결 코드 결함은 0이며, 위 역사 원천 부재와 capability 한계는 코드 완료와 별도로 남긴다.

- 최종 8 suites **278 passed in 12.19s**: `test_main_market_weakness_research.py`, `test_main_market_weakness_research_automation.py`, `test_main_market_weakness_source_repair.py`, `test_main_market_weakness_research_notify.py`, `test_market_weakness_entry_guard.py`, `test_notify_panic_state_transition.py`, `test_micro_reversion_symbol_master.py`, `test_engine_location_gate.py`. 기존 263개에 이번 회귀 15개를 추가했다.
- 변경 Python 2개 `py_compile`, Ruff, Black `--check`, 전체 `git diff --check` 통과. shell/cron 내용은 변경하지 않았다.
- 관련 문서 로컬 링크 24개 정상. print-only backlog 25개 중 약세 stable ID의 10/15 OPEN owner 1개를 확인했다. 체크리스트는 해당 owner에 한 줄만 추가했고 원 AUTO 봉인과 다른 owner 바이트를 보존했다.
- 모든 새 쓰기와 전송 경계 검증은 임시 data root/fixture에서 수행했다. 운영 원천 재생·계산·실제 Telegram 전송·provider/broker 호출·배포/rebind·재기동·외부 Project/Calendar sync는 실행하지 않았다. 새로운 장중 경로가 없다는 코드 범위를 검증했으며 실운영 성능 측정이나 자연 성과 수용을 주장하지 않는다.

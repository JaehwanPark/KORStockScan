# S6 `S2-ENT-05` — 순차 첫 BUY의 cancel-wait 첫 reader 인계

실행일: **2026-09-28 KST**. 범위: [S2 `S2-ENT-05`](2026-09-27-intraday-postclose-handoff-S2.md), [BUY parent→보유 인계](2026-09-28-intraday-postclose-handoff-S6-S2-ENT-03-S3-EXIT-02.md), [원자 sizing 행](2026-09-28-intraday-postclose-handoff-S6-S2-ENT-02.md), [현재 체크리스트 `DirectFamilySourceRepairEntryCancelWait`](../checklists/2026-09-28-stage2-todo-checklist.md). **판정: 작업본의 순차 첫 BUY 생산자·첫 reader 계약을 fixture로 수리했다. 현재 선택 릴리스·PID·미래 변경형 자연 소비와 비용 후 경제성은 미관측이다.**

## 결손 재현과 분모

- 기존 `sniper_state_handlers.py`의 `sequential_first=True` 경로는 첫 영속 intent와 broker 응답 뒤 `order_leg_sent`를 남기지만, frozen `entry_cancel_wait_submission`은 비순차 경로에서만 생성·발행했다. `entry_cancel_wait_tuning._parents`는 제출 stage의 context가 없으면 broker 주문과 owner registry가 있어도 parent를 미분류한다. **수리 전** 동일 날짜·record·attempt·주문 `B1`의 변경형 첫 leg fixture는 `parents=0 / unclassified=1`로 실패했다.
- 수리는 실주문 parent를 확인하는 기존 lossless `order_leg_sent`에 **주문 호출 전 동결한** schedule·owner·계획/첫 제출 수량·가격·route/session·두 attempt ID의 해시 context를 싣고, 첫 reader가 이 context를 직접 검증한다. 성공 주문에 별도 제출 stage를 복제하지 않아 한 broker order를 두 번 세지 않는다. 응답 불확실은 기존 lossless `entry_cancel_wait_submission`에 `dispatch_disposition=response_uncertain`, `broker_call_attempted=true`, `actual_order_submitted=false`로 기록한다. 이 값은 broker가 주문을 수락하지 않았다는 증명이 아니라 **수락 여부 미확정**이다.
- 수리 후 fixture의 성공 ACK 분모: 원본 `order_leg_sent` 1 / 정확한 parent 1 / cancel-wait 경제성 제외 1 / 격리 0 / terminal 미관측 1. 동일 frozen context의 중복 제출 stage를 더해도 parent·주문은 각각 1이다. 응답 불확실 fixture는 중복 event 2개를 고유 attempt 1개로 분류하고, 확정 주문 0 / 미확정 1을 유지한다. 나중에 같은 context의 정확한 broker·owner 주문이 나오면 확정 parent 1로 연결하지만 둘을 두 주문으로 세지 않는다.
- 9/23 bounded projection을 읽기 전용으로 재확인했다: `ready`, 관련 event 13, 검증 registry, parent 0, 미분류 10. 당시 모든 유형이 parent였고 새 순차형 자연 표본은 확인되지 않았다. 이 10건의 원인을 새 순차 경로로 돌리거나 과거 context/intent를 생성하지 않는다.

| Fixture 행 | 원본 투영 event | 유효 고유 parent | 제외·격리 | 미관측 |
| --- | ---: | ---: | --- | --- |
| ACK 첫 leg | 1 | 1 | 0 | terminal 1·비용 1 |
| 같은 주문의 제출 stage 중복 | 2 | 1 | 중복 1 제외 | terminal 1·비용 1 |
| 응답 불확실 event 중복 | 2 | 0 | 고유 미확정 attempt 1, 중복 1 제외 | broker 수락·terminal 1 |
| 상충하는 schedule SHA | 1 | 0 | source-quality 격리 1 | parent·terminal 1 |
| 부분체결·취소 대기 | 1 | 1 | 0 | 원주문 terminal 1·비용 1 |
| 정확한 terminal proof | 1 | 1 | 0 | 비용 1 |

각 행의 registry 원천은 별도 모집단이며 투영 event 건수와 합치지 않는다. 상충 행은 예외로 차단되고 불확실 행은 broker 미제출 0건으로 확정되지 않는다.

## 생산자→첫 reader 계약

| 경계 | 수리·닫힘 기준 |
| --- | --- |
| 장중 첫 영속 intent → broker I/O | `initial_quantity_bundle`의 검증된 timeout schedule을 첫 intent 영속화 **뒤**, broker 호출 **전** frozen context로 기록한다. context는 source date, record의 제출 parent와 별도 bundle evaluation attempt, owner client intent, 첫 leg·전체 계획 수량, 정책·schedule SHA, route/session·가격·시각을 포함한다. 관측 작성 실패는 `cancel_wait_source_gap`으로 표시하며 주문 경로·수량·timeout을 바꾸지 않는다. |
| ACK → `order_leg_sent` → `entry_cancel_wait_tuning._parents` | 같은 record·broker order·owner/계좌/registry intent·client intent·첫 leg index, schedule·정책 SHA, plan/submit 수량·가격·시각과 context 논리 SHA를 양방향 검사한다. source producer census와 compact projection의 현재 날짜·세대 검증을 기존 경로 그대로 요구한다. 누락·상충·다른 세대는 source gap/격리이며, 다른 owner나 주문번호만으로 parent를 추정하지 않는다. |
| 순차 timeout owner·경제성 | 순차형은 `initial_quantity_bundle_timeout_schedule` 소유다. reader의 parent에는 `economic_eligible=false`, `actual_timeout_sec=null`, 후보 timeout 없음과 별도 profile을 기록한다. 실제 제출 parent 수에는 포함하지만 `entry_cancel_wait_runtime`의 model·paired EV·policy 후보와 threshold 분모에서는 제외한다. 순차형만 있는 날짜는 `source_only_sequential_excluded`이며 `no_submitted_orders` 또는 경제성 개선으로 바꾸지 않는다. |
| 불확실·부분·취소·terminal | ACK 불확실은 고유 attempt로 남기고 제출 성공이나 verified zero로 세지 않는다. registry 누적 fill 1/2는 `partial_open`, 취소 intent 미종결은 `cancel_pending`, 취소 종결 뒤에도 원주문 terminal 영수증이 없으면 open/partial 상태다. 정확한 terminal proof가 있어야 full/partial/미체결 종결로 분류한다. 비용은 원천이 없어 `null`이다. 재기동 뒤에는 frozen context·registry·projection을 재검증하고 과거 성공 event만으로 현재 종결을 인정하지 않는다. |

## 회귀·자가 리뷰·인계

1. 실패 회귀를 먼저 작성해 순차 첫 leg의 `unclassified=1`을 확인했다. 생산자 helper와 reader를 수리한 뒤 context/SHA·다른 schedule, 중복 stage, 응답 불확실·후속 확정, 부분체결·취소 대기/종결, terminal proof 유효/상충, 다음 날짜 재기동 복원, 경제성 replay 제외를 검증했다.
2. 자가 리뷰에서 순차 bundle의 시간축을 일반 cancel-wait timeout으로 잘못 기록할 위험, 응답 지연을 broker 제출 지연으로 오판할 위험, 새 미확정 stage가 compact family에 등록되지 않을 위험을 찾아 보완했다. 기존 lossless stage에 증거를 결속하고 첫 reader에서 경제성 권한을 분리했다. 실제 registry의 terminal 증명은 생성 이벤트의 모든 owner 필드를 반복하지 않는 축약 이벤트다. 이 형식의 실패 회귀를 추가해 reader 및 재기동 후 누적 상태 갱신을 registry 순서대로 접도록 수리했다. 비순차 기존 경로와 9/23 분모를 다시 확인했다.
3. 수리 owner: `src/engine/sniper_state_handlers.py`·`src/engine/scalping/entry_cancel_wait_runtime.py` 생산자, `src/engine/automation/entry_cancel_wait_tuning.py` 첫 reader. 다음 닫힘 검사는 새로운 source date의 변경형 첫 intent→order ACK/불확실→exact registry·terminal, 생산자 census→compact SHA→reader parent/제외 수량의 보존이다. fixture 통과는 자연 주문·PID 또는 비용·독립 holdout 수용이 아니다.

`DirectFamilySourceRepairEntryCancelWait`의 운영 비용·독립 holdout은 OPEN이다. 앞선 S6 `S2-ENT-02`·`S2-ENT-03/S3-EXIT-02`의 작업본과 9/23 미분류 10건을 보존한다. `S3-EXIT-01` SELL 비용과 `S5-FIN-05` 자연일 조건부 결손은 별도 묶음이다. 전체 데이터·성능과 자연 terminal은 S7, 릴리스·PREOPEN·실제 PID 소비는 S8에 인계한다. 실주문·취소·정책·수량·timeout·서비스·provider·threshold·배포, 정규 장후작업·PREOPEN은 변경·실행하지 않았다. Broker API/parser 변경은 없었다.

## 검증

- 영향 pytest: 첫 확장 실행의 313 passed / AST fixture 1 failed 뒤 fixture를 보완했다. 축약 terminal 영수증의 `terminal_unverified` 실패를 재현해 registry 상태 fold로 고쳤다. 최종 확장 회귀 **342 passed**.
- Python compile 및 `git diff --check` 통과. 문서 링크 4개 모두 존재한다. 문서 backlog print-only parser가 현재 OPEN owner 31건을 출력했고 `DirectFamilySourceRepairEntryCancelWait`을 포함했다. Wrapper 변경이 없어 `bash -n`/계약 검사는 비대상이다.
- 남은 위험: 변경형의 실제 자연 event·main PID는 이 작업본의 fixture로 증명되지 않는다. 9/23 main BUY parent·cost가 미분류이고, 이후 broker terminal·경제성 gate는 별도 검증이 필요하다.

# S6 `S2-ENT-03`·`S3-EXIT-02` — BUY parent→보유 인계

실행일: **2026-09-28 KST**. 범위: [S2 `S2-ENT-03`](2026-09-27-intraday-postclose-handoff-S2.md), [S3 `S3-EXIT-02`](2026-09-27-intraday-postclose-handoff-S3.md), [9/28 체크리스트 `DirectFamilySourceRepairEntryCancelWait`](../checklists/2026-09-28-stage2-todo-checklist.md). **판정: 작업본의 생산자·최초 reader 계약 수리 및 fixture 검증 완료. 9/23 parent 10건은 미분류 유지. 자연 terminal·비용·독립 holdout·릴리스/PID 수용은 미완료.** 정규 장후작업·PREOPEN·실주문·취소·배포를 실행하지 않았다.

## 1. 원천 재현과 분모

| 원천/경계 | 9/23 확인 | 판정 |
|---|---:|---|
| `pipeline_events` 압축본 | 논리 SHA `4db035e3b3915644ee95fef82d50b54f0dcdfbbf6c69a19dab15594a3d1c758c`; 해제 스트림을 날짜·stage·record로 한 번 스캔 | 원래 `.jsonl` 대신 `.jsonl.gz` 사용. [archive receipt](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-09-23.jsonl.gz.archive_receipt.json)와 분리 보존 |
| execution compact producer census | `order_leg_sent=10`, `order_leg_no_response=0`, `order_leg_fail=0`, 취소 요청·응답 각 1; projection `ready`, manifest SHA `54c203d52e9afdfbe15445a0a8e3a1bc6398d39aaeeb33fd22b3a2001ae4f34d` | 10은 제출 stage event 분모이며 전체 raw/모든 owner의 주문 분모가 아님. 취소의 원주문 `0041427`을 처음 제출 10건에 건수로 합치지 않음 |
| 같은 record·broker 주문번호의 `position_rebased_after_fill` | 위 10건 모두 동일 ID의 BUY 체결 관측 1건씩. 별도로 record `47652`에 주문 `0041326`·execution `165997`·2주 BUY 체결 관측 | 동일 ID 체결 관측은 가능하나 owner registry 또는 parent 증명으로 승격 금지. 별도 주문을 첫 parent에 합치지 않음 |
| owner registry verified snapshot | 같은 날짜 31행: `manual_operator=20`, `episode=11`, `main_scalping/BUY=0` | 숫자가 가까운 수동·episode 행을 main BUY에 연결하지 않음 |
| holding/SELL 관측 | 위 record들에서 `sell_completed` 8 event 관측 | trade-review의 10 record·8 terminal과 같은 건수여도 parent custody·실제 비용 보증은 아님 |

새 인계 계약으로 9/23을 재투영한 분모는 **원본 제출 10 / 유효 parent→보유 0 / 제외 0 / 격리 10 / 미관측 0**이다. 10건은 정확한 order·record의 BUY fill 관측을 갖지만 새 parent·account·owner 필드와 main registry 원천이 없어서 격리된다. 신규 필드나 가짜 intent를 과거 영수증에 소급하지 않았다. 제출 응답 불확실 시도는 별도 `response_uncertain_attempts`로 두며, 9/23 bounded projection에서는 0건이다. 실제 9/23 [cancel-wait report](/home/ubuntu/KORStockScan/data/report/entry_cancel_wait_tuning/entry_cancel_wait_tuning_2026-09-23.json)의 `submitted_parent_count=null`, `unclassified_count=10`, `economic_tuning_input_allowed=false`를 변경하지 않았다.

## 2. 생산자→첫 소비자 연결과 수리

| 단계 | 연결 ID와 보존식 | 코드 owner·수리 |
|---|---|---|
| BUY 응답·accepted pending order | record / call-local attempt(`buy_parent_id`) / child(`parent:broker_order_no`) / owner context / account / registry intent 또는 명시적 단일-owner mode / route·session / 계획·제출 수량 | [`sniper_state_handlers.py`](../../src/engine/sniper_state_handlers.py): broker 수락 뒤 관측 필드와 pending-order 메타데이터를 남긴다. 정확한 날짜의 owner-policy 관측은 주문 adapter 판단을 대체하지 않으며 읽기 오류는 `unknown`이다. 주문 호출·수량·timeout·guard는 유지한다. |
| frozen cancel-wait context·compact stage·registry | 같은 record/order에 있는 해시 검증 context, explicit parent/child, account·owner·intent 및 제출 수량을 대사 | [`entry_cancel_wait_tuning.py`](../../src/engine/automation/entry_cancel_wait_tuning.py): 주문번호만으로 registry를 추정하던 fallback을 없앴다. registry-managed와 명시된 single-owner/no-registry를 구별한다. 후자는 intent ID를 `null`로 남기고 terminal·비용이 없으면 EV 수용하지 않는다. |
| 최초 holding projection | 같은 record/order/execution의 BUY fill 누적량 = 제출량 − 주문 잔량, 다른 BUY order 격리, 동일 record의 SELL execution 누적량 ≤ 검증 BUY fill, 가용량 = 검증 BUY fill − 검증 SELL fill | [`sniper_trade_review_report.py`](../../src/engine/sniper_trade_review_report.py): bounded execution census·registry·구조화 HOLDING source를 읽어 `buy_parent_handoff` 섹션을 만든다. 중복·owner/account/route 불일치, sim, terminal 미확정, 추가 BUY, DB 보유량 충돌은 `sellable_qty=null`과 source-quality 사유로 남긴다. 비용 원천이 없는 `cost_krw`도 `null`이다. |

single-owner 경로는 producer가 **주문 전 정확한 날짜의 비공존 policy 관측**을 남기고, 첫 reader가 같은 날짜의 policy reason·hash를 재검증하며, registry에 같은 날짜·symbol owner가 없고 같은 record/order/execution의 real fill과 DB 보유량이 보존될 때에만 source-only로 연결한다. registry-managed 경로는 intent·account·owner·route·fill execution 및 terminal proof를 요구한다. `full`, `partial_open`, `partial_terminal`, `unobserved`, `quarantined`를 나누고 응답 불확실 시도는 별도 목록으로 남긴다. 이 projection은 주문이나 런타임 보유 상태를 변경하지 않는다.

## 3. 실패 회귀→수리→자가 리뷰→재리뷰

1. 실패 fixture를 먼저 작성했다. 첫 holding reader가 없어 `AttributeError`, cancel-wait reader가 explicit attempt parent 대신 `unclassified:<intent>`를 택해 실패함을 확인했다.
2. 생산자와 두 reader를 구현한 뒤 1차 리뷰에서 동일 주문의 상충 event가 한 행을 유효로 남기던 문제, 부분 SELL 가용량 누락, 다른 BUY 주문을 한 parent에 합칠 위험, registry full terminal proof 부족, source-only policy 읽기 예외가 주문 흐름에 전파될 위험을 찾아 보완했다. 재리뷰에서는 빠른 WS fill이 제출 로그보다 먼저 찍히는 경우와 BUY·SELL·BUY 체결 순서를 추가로 보완했다.
3. 최종 fixture는 registry-managed·single-owner, owner/account 불일치, 동일 주문 상충·중복 execution, real/sim, 부분체결·open·취소 요청 대기·취소 응답 후 terminal 대기·terminal 확인, SELL 부분체결, 추가 BUY, 응답 불확실, fill-before-log, BUY·SELL·BUY, reader 재기동, source-gap/valid-empty와 policy 세대 변경을 구분한다. 9/23 재실행은 parent 0·미분류 10을 유지했다. **검토 범위 내 미해결 코드 결함 0**이며 아래 자연 증거 결손은 열려 있다.

검증: 영향 pytest **214 passed** (`entry_cancel_wait_tuning/runtime/attribution`, trade-review revival, initial-quantity timeout, main lifecycle receipt integration), 추가 **222 passed** (`entry_split_order_plan`, initial-quantity policy). 추가 suite의 오래된 AST fixture에서 누락된 입력을 보완한 뒤 재실행했다. 변경 Python 및 회귀 test `py_compile` 통과, `git diff --check` 통과. Shell wrapper를 변경하지 않아 `bash -n`/wrapper 계약 검사는 해당 없음. 정규 장후작업·PREOPEN·broker/provider 호출은 검사에 포함하지 않았다.

## 4. 남은 원천·닫힘 검사·인계

| 열린 경계 | 영향·수리 owner | 닫힘 검사 |
|---|---|---|
| 9/23 main registry/explicit parent·account 부재 | 10건 parent·비용·EV 미분류. 장중 order emitter owner + `entry_cancel_wait_tuning` | 과거에 없는 ID를 생성하지 않는다. 새 source date의 frozen context→accepted order→registry 또는 명시적 단일-owner 증거→BUY fill/terminal→보유량을 동일 ID·날짜·세대로 양방향 대사한다. |
| 수락 응답 뒤 pending-order/event 기록 전 crash 및 계좌 구분 없는 과거 holding fill | 재기동 시 terminal/owner 확인 전 SELL 가능수량 확정 불가. `sniper_state_handlers`·`sniper_execution_receipts` 관측 owner | 재기동·상충/중복·응답 불확실 fixture 및 자연 원천에서 exact broker snapshot/terminal과 현재 owner position을 재대사한다. 본 묶음은 broker parser/API를 변경하지 않았다. 필요한 parser 변경은 공식 Kiwoom reference gate를 거친 별도 결손이다. |
| `DirectFamilySourceRepairEntryCancelWait`의 경제성 closure | 비용·독립 holdout·자연 terminal이 없어 체크리스트 OPEN 유지. `entry_cancel_wait_tuning` | `native_execution_census_cancel_terminal_cost_and_independent_holdouts`를 같은 source generation으로 통과해야 한다. Fixture PASS를 비용·정책 적용으로 승격하지 않는다. |

`S2-ENT-02` sizing 행, `S2-ENT-05` 조건부 순차 첫 leg, `S3-EXIT-01` SELL 비용은 별도 묶음이다. 9/23 10건을 미래 순차형 경로의 원인으로 단정하지 않는다. 전체 데이터·성능과 자연 terminal은 S7, 선택 릴리스·PREOPEN·PID 소비는 S8에서 확인한다. 기존 SOR→KRX 작업본 오버라이드를 보존했고 선택 릴리스나 PID 적용으로 간주하지 않는다.

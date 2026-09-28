# 물타기 공통 반등 원천·체결 식별자 폐루프와 불타기 잔재 정리 구현계획 — 2026-09-28

## 1. 결정과 현재 근거

**목표:** 같은 Main 보유 건에 대해 `입력 사전검사 → 유효 반등 → 유효 ADD_REBOUND 투표 → 허가·주문·체결 → 청산·정확 비용`을 대사한다. 먼저 차단 사유를 구체적으로 기록하고 재기동 후 최초 매수 체결 식별자를 정확하게 복원한다. 그 결과로 물타기의 실제 증분 효과를 평가한다. PYRAMID의 신규 판단·튜닝·정책 적용 경로는 제거하되 과거 미결 주문의 복구, 체결 반영, 청산·정산은 유지한다.

현행 동작의 기준은 [9/18 사용자 정정](scale-in-pyramid-avg-down-economic-tuning-implementation-plan-2026-09-17.md#현행-사용자-정정--pyramid-폐기avg_down-공통-반등-신호-소비)과 [퇴역·공통 반등 검토](../audit-reports/2026-09-18-pyramid-retirement-avg-down-shared-rebound-review.md)다. [Plan Rebase](../plan-korStockScanPerformanceOptimization.rebase.md) §5/§7의 PYRAMID active 또는 이전 AVG_DOWN 후속 경로 표현과 상충하는 부분은 후속 문서 정합성 과제로 표시한다. 이 계획만으로 Plan Rebase나 운영 규칙을 수정하거나 PYRAMID를 재활성화하지 않는다.

| 확인 지점 | 9/28 대우건설 `047040`, 보유 `record_id=48376`에서 본 것 | 판단 경계 |
| --- | --- | --- |
| 최초 매수 | 10:40:55 KST, 주문 `0029186`, 체결 `131176`, 1주 19,010원 | 실제 최초 매수의 원천 식별자다. 장후 파일의 숫자를 현재 메모리 복원 성공으로 간주하지 않는다. |
| 반등 입력 | `shared_main_rebound_input_preflight_blocked`가 반복됐으나 차단 이벤트에는 세부 `primary_blocker`와 원천 시계가 없다. 유효 `BLOCK/NO_VALID_SETUP`도 별도로 관측됐다. | 원천 결손과 정상적인 비진입 판단을 구분해야 한다. 반복 polling 횟수는 독립 기회 수가 아니다. |
| 보유 투표 | 재기동 전에는 `source_preflight_blocked`, 보유 flow/tape 결손이 보였고, 11:13 무렵 재기동 뒤 `buy_fill_identity_missing`이 주된 결손이었다. 유효 `ADD_REBOUND` 투표는 확인되지 않았다. | 재기동과 식별자 결손의 인과는 복원 입력·영속 원장 대사로 확인한다. 이 증거만으로 주문 미실행의 유일 원인이라고 단정하지 않는다. |
| 재기동 복원 | `DB.get_active_targets()`는 매수 가격·수량 등 요약값을 조회하지만 주문번호별 체결 수량·체결번호 맵을 제공하지 않는다. `_restore_holding_runtime_state()`도 해당 맵을 재구성하지 않는다. 투표는 두 맵의 수량 일치를 요구한다. | 요약 가격×수량으로 체결번호를 합성하거나 기존 보유를 새 매수로 취급할 수 없다. |
| 추가매수 결과 | 위 구간에는 유효 투표·ADD 주문·ADD 체결이 없다. | 물타기 실현 손익 또는 경제적 효과를 0으로 확정할 수 없다. |

증거 경로: `data/pipeline_events/pipeline_events_2026-09-28.jsonl`, `data/runtime/holding_path_votes/bd5e45f0957971cdfdad4ba5855ebe270e11c75c1f322d1483ad39bcb65cf193.jsonl`; 생산·소비 위치는 `src/engine/ai_engine_openai.py::evaluate_main_rebound_entry`, `src/engine/scalping/ai_market_snapshot.py::ai_input_preflight`, `src/engine/sniper_state_handlers.py::{handle_holding_state,_collect_holding_path_votes,execute_scale_in_order}`, `src/engine/ai/holding_exit_vote.py::buy_fill_legs_from_runtime`, `src/database/db_manager.py::get_active_targets`, `src/engine/kiwoom_sniper_v2.py::_restore_holding_runtime_state`. 원천 파일은 크므로 후속 검증은 보유 ID·시간 범위·기존 인덱스/receipt에 한정한다.

## 2. 권한·분리 원칙

- 물타기는 **Main 기계 진입 정책의 기존 날짜별 publisher→PREOPEN→실제 PID**를 사용한다. Main 보유의 현재 bars·WS tick/BBO에서 `PULLBACK_RECOVERY`, `RECOVERY_CONFIRMATION`, `MICRO_RECOVERY`의 `ENTER_NOW`만 후보가 된다. 후보에는 기존 2초 permit, `ADD_REBOUND` 투표, 공통 안전·수량·가격·현금·pending·cooldown·SELL 우선권이 그대로 적용된다. 진단 필드나 체결 복원은 독립 threshold·후보·승격·주문 권한이 아니다.
- `scale_in_split`은 ADD가 허가된 뒤의 **수량·분할 실행 형태** 소유자다. 현행 체크리스트 `[DirectFamilySourceRepairScaleInSplit]`의 원천·경제성 수리와 본 계획의 **ADD 여부 판단·체결 식별자** 수리를 섞지 않는다. 정책 파일 존재, PREOPEN 검증, 선택 release, 실제 PID 소비, 자연 주문·체결, 순익을 각각 별도 영수증으로 판정한다.
- Main/widget/episode/manual 및 venue/session의 custody를 유지한다. 기존 operator veto, bot state, hard/protect/emergency stop, stale/conflict, broker/account/order/수량/cap·cooldown, SELL/손절 우선권을 완화하지 않는다. 결손 입력은 `UNKNOWN` 또는 source gap이며 `NO_VALID_SETUP`, 0원 효과, 유효 투표로 바꾸지 않는다.
- 9/29 후속 요청으로 이 계획의 코드 구현·리뷰·보완을 진행한다. 코드 변경은 배포·실제 PID 소비·자연 주문·체결·비용 후 성과와 별도로 검증한다. 매매 프로세스 재기동, 정책·env·provider 변경, 주문 또는 과거 체결 재주입은 이 구현 요청에 포함되지 않는다.
- S15와 VCP의 **신규 진입은 이미 제거된 상태**다. AVG_DOWN 반등 후보·원천이나 PYRAMID 대체 경로로 복원하지 않는다. 역사적 S15/VCP 보유·미결 주문의 복구, SELL·정산 custody는 실제 소비자가 남아 있는 범위에서 유지한다.

## 3. 구현 순서와 완료 조건

### A0. 원천·스키마·기준 세대 고정

1. 현재 선택 release, 설치 unit, 실제 PID와 `record_id=48376`의 보유·주문·체결·SELL custody를 각각 읽기 전용으로 묶는다. workspace 파일 차이를 실제 PID 소비로 간주하지 않는다. 9/28 관측 시각 이후의 수치는 새 영수증으로 다시 산출한다.
2. 최초 매수의 **영속 exact 원천**을 먼저 조사한다. 주문번호·체결번호·체결시각·체결수량·가격·계좌/실거래 여부·보유 ID를 갖춘 기존 receipt/ledger와 DB·broker 대사 가능성을 표로 만든다. 런타임의 `_entry_receipt_*` 맵, SELL snapshot 목록, 거대 pipeline JSONL의 존재만으로 재기동 후 복원 원천이 있다고 선언하지 않는다.
3. Main 반등 원천의 bars, tick, BBO, 보유 flow/tape, 정책 bundle·scope/hash와 시각을 조사한다. `ai_input_preflight`의 반환 계약과 차단 이벤트·보유 투표 이벤트 간 ID를 대사한다. 동일 source digest의 반복 평가를 하나의 기회로 묶을 수 있는 현재 ID 계약을 확인한다.

**산출물/통과:** `보유 ID → 원 BUY order/exec → 영속 원천 → 런타임 맵 → 투표` 필드별 대사표와 `source gap / 유효 BLOCK / 유효 ENTER_NOW` 분류표. exact 체결 원천이 없으면 해당 보유는 `identity_unrecoverable`로 남기고 ADD를 차단한다. 과거 JSONL을 전량 재생하는 startup 경로는 채택하지 않는다.

### A1. 입력 사전검사 차단 사유를 구조화

1. `ai_input_preflight`가 이미 반환하는 `blockers`, `primary_blocker`, `primary_blocker_category`를 `shared_main_rebound_input_preflight_blocked`의 기존 이벤트에 한정해 보존한다. `source_preflight_blocked` 한 문자열에 다른 원인을 뭉치지 않는다. 알려진 진단 필드만 허용하고 크기·개수를 제한하며 raw prompt, 계정번호, 토큰, 전체 호가/틱 배열은 기록하지 않는다.
2. 이벤트에 보유 ID, decision/attempt ID, 정책 날짜·scope/hash·loaded 상태, 원천 receipt/digest, 원천별 observed/as-of/decision clock, stale/conflict/missing 표시를 결속한다. `source_quality_blocked`, 유효 `BLOCK/NO_VALID_SETUP`, 쿨다운 중복, 투표 결손의 reason code를 구분한다. 로깅 오류는 ADD를 허용하지 않으며 주문 판단의 반환값·시계를 바꾸지 않는다.
3. 대우건설과 유사한 원천 결손 재생에서 세부 blocker가 event→holding vote→장후 진단에 같은 ID로 보이는지 확인한다. 기존 유효 `BLOCK`은 유효한 비진입으로 남겨야 한다.

**주 변경 후보:** `ai_engine_openai.py::evaluate_main_rebound_entry`, 기존 pipeline-event 기록 호출부, `scalping/ai_market_snapshot.py` 계약 소비부. 새 provider/collector/cron 없이 기존 snapshot만 사용한다.

### A2. 정확 체결 식별자를 영속화·재기동 복원

1. A0에서 확인한 기존 exact 체결 원천을 우선 사용한다. 재기동 시작 시 active position만 대상으로 원 BUY receipt를 조회하고 계좌·종목·보유 ID·order/exec ID·실/모의·수량·가격·시각·중복/취소/부분체결·pending 상태를 대사한 뒤 `_entry_receipt_filled_by_order_no`와 `_entry_receipt_executions_by_order_no`를 **원 체결 그대로** 재구성한다. 복원은 보유 투표 이전에 완료하고 성공/결손/충돌 receipt를 남긴다.
2. 적격 영속 원천이 없다면 기존 execution-receipt owner에 소규모 **보유 건별 write-through exact journal 또는 인덱스**를 설계한다. 신규 체결 수신 시 원 식별자와 source receipt hash를 원자적으로 기록하고 멱등 replay한다. 위치는 기존 `sniper_execution_receipts.py` 및 기존 저장소 역할을 먼저 검토하며 새 파일·모듈이 필요하면 AGENTS location gate를 거친다. 과거 건은 exact broker/ledger 영수증으로 검증 가능한 범위만 backfill한다. `buy_price`, `buy_qty`로 체결번호를 만들지 않는다.
3. A2 복원 결과가 없거나 충돌하면 해당 position의 ADD 투표·주문은 계속 차단한다. SELL, 과거 미결 주문 reconciliation, 청산·잔고 복구는 별도 custody로 계속 작동한다. 수량 합계·execution ID 중복·원 주문 귀속 충돌은 원천 결손으로 남긴다. 오래된 신호를 재기동 시 재전송하거나 지난 permit을 복원하지 않는다.

**주 변경 후보:** `database/db_manager.py::get_active_targets`의 조회·별도 exact 조회 계약, `kiwoom_sniper_v2.py::_restore_holding_runtime_state`, `sniper_execution_receipts.py`, `ai/holding_exit_vote.py`의 엄격 검증. 기존 Kiwoom wire/order API를 바꾸지 않는 것이 원칙이다. 변경이 불가피하면 수정 전에 공식 Kiwoom reference gate로 upstream SHA·경로·조회 시각·필드/real-demo 의미를 기록한다.

### A3. 같은 보유 건의 판단·집행·성과 결속

1. `position_episode_id/record_id`, BUY order/exec 집합, source digest·정책 hash, rebound evaluation/decision, `ADD_REBOUND` vote, permit/guard, ADD attempt/order/exec 집합, SELL terminal 및 비용을 잇는 기존 이벤트 키를 명세한다. 없는 연결은 추측 조인하지 않고 `lineage_gap`으로 표시한다.
2. 분모를 `보유 평가 기회 → 원천 적격 → 유효 ENTER_NOW → 유효 투표 → guard 통과 → 계획 수량 → 실제 제출 수량 → 체결 수량 → terminal 청산·정확 비용`으로 나눈다. 중복 polling, 2초 permit 만료, operator veto, 자금/수량/가격 차단, 부분체결·미제출 잔량, 보유 중/미청산을 각 단계에서 보존한다. 유효 반등과 유효 투표가 0이면 그 지점에서 멈춰 보고한다.
3. 장후에는 실제 ADD 건의 동일 보유 episode에서 `COMPLETED + valid profit_rate` 및 검증된 비용만 경제성 모집단에 넣는다. ADD/no-ADD 비교가 필요하면 동일 원천 시점·정책·custody의 사전 정의된 paired cohort와 독립 holdout을 구성하고 가격·수량·청산 반사실의 가정을 별도 표시한다. 실제 실현 순익과 Main entry 모델 EV, `scale_in_split` 실행 형태 EV, sim/probe/CF를 합산하지 않는다. 검열·결손 비용을 0으로 메우지 않는다.
4. Main 장후 정책의 기존 학습→dated publisher→PREOPEN 경로와 실제 PID hash·첫 자연 기회 receipt를 분리 검증한다. 본 수리는 AVG_DOWN 독립 grid/calibration/정책을 만들지 않는다. 원천이 없거나 유효 반등이 없으면 `valid_empty`/`source_gap`을 분리하고 incumbent를 유지한다.

**산출물/통과:** 보유 ID별 단계 보존식과 사유별 수, source/정책/주문/체결/청산 ID의 join coverage, 실제 순익·비용의 적격/결손/검열 수가 같은 장후 진단에 나타난다. 단일 대우건설 건만으로 수익성 개선을 선언하지 않는다.

### A4. PYRAMID 신규 경로 퇴역 정리

S15·VCP 신규 진입도 이미 퇴역했다. 이 단계에서 세 경로의 신규 판단·후보·주문을 재도입하지 않으며, 이름이 남은 과거 custody 복구·청산 소비자는 별도로 확인한다.

1. runtime 진입/판단/수량/신규 주문, 장중 feedback, 장후 quality·후보, Daily intake, PREOPEN 적용, env scrub/cron/docs/tests의 PYRAMID 참조를 **소비자별**로 조사한다. `OFF/retired` guard와 과거 artifact 파서는 제거 대상과 구분한다. 새 PYRAMID 판단·후보·주문은 항상 0이어야 한다.
2. 과거 주문의 pending 조회·체결 반영·취소/중복 방지·SELL/정산·원장·감사 기록은 유지한다. 이름에 `pyramid`가 들어가도 공통 미결 주문 재검증을 소유하는 `real_pyramid_scale_in_quality_guard_runtime` 같은 경로는 소비자를 확인한 뒤에만 이동/개명한다. 호환 읽기·migration 테스트 없이 저장된 enum/key를 삭제하지 않는다.
3. 신규 진입 참조를 제거한 뒤 `PYRAMID` 문자열 검색뿐 아니라 실제 dispatch→executor, 장후 producer→candidate→publisher→PREOPEN→PID consumer를 호출 그래프로 재점검한다. 역사적 DB·보고서·immutable release는 정리 대상으로 삼지 않는다. Plan Rebase §5/§7 표현 충돌은 별도 명시 요청 전까지 변경하지 않고 handoff gap으로 보고한다.

**산출물/통과:** 참조별 `신규 판단 제거 / 퇴역 guard 유지 / 과거 주문 정산 유지 / 역사적 기록 유지` 분류표와 신규 PYRAMID submit 불가 회귀, 기존 미결·부분체결·SELL 정산 회귀.

### A5. 검토·검증·출시와 자연 수용

- 코드 단계는 `구현 → self review → in-scope 수정 → 재검토 → 표적 검증`으로 닫는다. preflight reason별·중복 polling·유효 BLOCK/ENTER_NOW, 정확 체결 1건/복수 주문/부분·늦은 체결/중복/충돌/재기동 2회, 미복원 시 ADD 차단·SELL 지속, permit 만료·stop 우선권, PYRAMID 신규 주문 차단/옛 pending 정산, 장후 ID 보존식·null 비용을 회귀한다. Python compile·관련 pytest·`git diff --check`를 적용한다.
- 성능은 변경 전후 **동일 active-position 수**의 startup 복원 시간/읽기량, 보유 평가 지연·CPU/RSS, event 크기와 postclose join 시간을 비교한다. 일별 거대 raw 전량 읽기, 원천별 신규 API 조회, 250ms 경로의 무제한 직렬화가 생기면 설계를 수정한다.
- 코드 통과와 배포는 다르다. 선택 immutable release, 설치 unit, 실제 PID·정책 hash, 최초 자연 원천·투표·주문/미주문·체결/미체결을 따로 기록한다. 출시 후 exact receipt 충돌이나 성능 악화 시 새 ADD 경로를 닫고 검증된 이전 release/정책으로 복귀하되 기존 보유·SELL/정산 custody는 유지한다. 새 자연 기회가 없으면 `natural_first_use_pending`으로 남긴다.
- 경제성 수용은 clean baseline(2026-06-05 00:00 KST) 이후의 정확한 완료·비용 적격 표본, full/partial과 venue/session/custody 분리, rolling/cumulative 순익·EV 및 위험·노출 검토로만 판단한다. 코드·PID 소비 완료가 자연 증분 이익의 증거는 아니다.

## 4. 실행 소유자와 선행 관계

9/28 최초 owner는 [9/28 체크리스트](../checklists/2026-09-28-stage2-todo-checklist.md)의 `[AvgDownSharedReboundReceiptClosure0928]`였고, 9/29 후속 구현·검토 owner는 [9/29 체크리스트](../checklists/2026-09-29-stage2-todo-checklist.md)의 같은 ID다. 구현 검토 근거는 [9/29 리뷰](../audit-reports/2026-09-29-avg-down-rebound-receipt-and-pyramid-retirement-implementation-review.md)에 둔다. 순서는 `A0 → A1·A2 → A3 → A4 → A5`다. A3 자연 손익 수용은 실제 PID 소비 및 완료 표본에 의존하므로 코드 검증만으로 완료 처리하지 않는다. `[DirectFamilySourceRepairScaleInSplit]`은 별도 수량·분할 owner로 유지한다.

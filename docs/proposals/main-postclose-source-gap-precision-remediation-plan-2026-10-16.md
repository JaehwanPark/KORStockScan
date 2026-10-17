# Main 장후 source gap 정밀 점검·결함 보완안 — 2026-10-16

판정: 질문3~5의 결손은 실제다. 다만 **원천을 잘못 연결하거나 읽지 못하는 코드 결함**, **현재 대사·모델이 지원하지 않는 범위**, **기록되지 않은 과거 입력**, **아직 종결되지 않은 관측**이 섞여 있다. 단순 재실행·대기·sample floor 완화로 일괄 해소되지 않는다. 이번 작업은 읽기 점검과 보완안 작성이며 운영 코드·원장·정책·DB·provider·주문을 변경하지 않았다.

## 1. 증거 기준과 점검 범위

- 대상 source date는 `2026-10-15`; 누적 연구 창은 각 family가 선언한 날짜를 유지한다. 당일 수와 누적 수, 진단 행과 경제성 적격 행을 합치지 않는다.
- source15 코드 기준은 `23a13aba62884a5d3a0d48a3f91ebff4262571f6`. 08:00:36 선택된 `580d5865b568c36331bbeed69ee65de9fc6c137a`와 비교한 핵심6개 파일은 동일하다. 이 비교는 새 PID 소비나 기동 성공의 증명이 아니다. 실제 배포 전환은 별도 운영 owner가 관리한다.
- 정규 작업공간은 이 운영 릴리스와 다르다. 실제로 작업공간 기본 reader는 복구 원장의1529행을 거부했지만, source15 릴리스의 원 복구 계약 reader는 **1544행·tail `56819f…`**를 검증했다. 작업공간의 구 reader 결과를 현재 원장 장애로 확대하지 않는다. 구현 시 최신 선택본을 다시 고정하고 이미 배포된 복구 코드를 보존한다.
- 2.02GB trade review와97.58MB 완료 투영을 다시 전수 파싱하지 않았다. 원 생산자가 봉인한 연구 입력 partition, 작은 소비 projection, 비용 원천, 기존 읽기 전용 DB 조회와 보관 원문을 사용했다. AI trace는 추가로355,872B의 앞부분만 읽어 두 사례의 envelope를 확인했다.
- 기존 운영 규칙은 [Plan Rebase](../plan-korStockScanPerformanceOptimization.rebase.md), 실행 owner는 [10/16 checklist](../checklists/2026-10-16-stage2-todo-checklist.md)가 소유한다. 봉인된 checklist bytes를 변경하거나 OPEN owner를 추가·종결하지 않는다.

직접 점검 자료:

| 자료 | 내용 |
| --- | --- |
| [정밀 점검 결과](../../tmp/postclose-source-gap-deep-review-20261016/findings.json) | source hash, 잔여주문3건, 완료2건의 구체 비용 거부 사유, 원문 연결 및 annotation 재현 |
| [gzip·envelope 대조](../../tmp/postclose-source-gap-deep-review-20261016/logical-source-and-envelope.json) | 9/29·9/30 gzip CRC/EOF·행 수·원문 크기, 평문 전용 reader 재현, 두 trace의 envelope 일치 |
| [보유 가격 경로 census](../../tmp/postclose-source-gap-deep-review-20261016/holding-path-census.json) / [보유 입력 거부 사유](../../tmp/postclose-source-gap-deep-review-20261016/holding-vote-reasons.json) | 두 실제 완료 position의 quote/ADD/보유판정 원천을 별도 집계 |
| [코드 선택본 대조](../../tmp/postclose-source-gap-deep-review-20261016/code-selection-comparison.json) | source15와 관측 당시 선택본의 핵심 코드 동일성; 선택본의 PID 소비 미확인 상태 보존 |
| [완료 fact 읽기 조회](../../tmp/postclose-source-gap-cause-review-20261016/fact-economics-findings.json) / [label 연결 census](../../tmp/postclose-source-gap-cause-review-20261016/binding-findings.json) | DB COMPLETED3건·실제 비용 유효0건, label284건의 결손 분해 |
| [장후 의미 점검](../audits/main-postclose-semantic-review-and-repeated-read-findings-2026-10-16.md) | 운영 terminal 성공과 경제성 미완료의 구분 |

## 2. 확정 발견과 영향

| 항목 | 직접 확인 | 판단·영향 |
| --- | --- | --- |
| 완료 거래 | DB COMPLETED3, 유효 비용 후 수익률0; 정규 완료 투영2 | 삼성1건은 완료 동일성 결손, 나머지2건은 서로 다른 실제 비용 대사 결손이다. `consumer_ready`나 warning0은 경제성 완전성을 뜻하지 않는다. |
| 잔여매수 | 원장에는 HPSP8·12주와 알테오젠1주가 있으나 cancel-wait 제출 census에서3건 미분류 | 정규 제출 이벤트와 별도 `residual_submitted` 경로 사이의 생산자/소비자 계약 누락이다. 최초7개 부모만으로 전체 Main BUY를 대표할 수 없다. |
| 과거 census | 9/29·9/30 gzip 원문은 존재하고 무결성 검증; reader는 평문만 검사 | 두 날짜의 `missing`에는 확정 읽기 결함이 있다. 10/1의 동일 source/manifest 부재와 구분해야 한다. |
| outcome labels | label284의 primary hash가 보관 payload에 전부 없고, request ID로283건은 원문 존재·해시 불일치,1건은 미발견 | 최종 wire 해시를 이전 입력의 해시로 덮는 결함을 annotation 함수 재현으로 확인했다. 복구 후보283건과 정규 보관 원문 미발견1건을 구분한다. |
| 보유 판정 | 알테오젠72·HPSP33건 모두 INSUFFICIENT, provider_called=false | 동일한 preflight/flow/실행가능 손익 입력 결손이105건 모두에 존재한다. 프롬프트의 판정 성능을 평가할 표본으로 쓸 수 없다. |
| 손절 |7개 기회 중3개 quote/position source gap,4개 alternative lifecycle censored | 모든 censored를 코드 버그로 바꾸면 안 된다. 별도 operating 비교에는 quote 검증3, preset 미관측3, 수동 이관 후 자동 상태 원천1이 있다. |

## 3. 완료 거래 경제성: 세 거래를 따로 복구

### 3.1 삼성전자49266: 완료 상태와 경제적 종결을 분리

`trade_performance_facts.economics_source_status=source_gap_completion_projection_identity`. recommendation은 COMPLETED·매수1주이나 조회 당시 `sell_time=NULL`; source15 완료 투영과 post-sell 원문에는 이 position의 매도 종결이 없다. 이후 삼성49328은 별도 HOLDING1주다. 종목이 같다는 이유로 두 cycle을 합칠 수 없다.

확정된 것은 **DB 상태와 검증된 경제적 완료 모집단의 불일치**다. 실제 매도 누락, 상태 전이 결함, 수동/보관 이관 중 어느 사건이 COMPLETED를 만들었는지는 이 증거만으로 확정하지 않는다.

보완 위치: `sniper_execution_receipts.py`의 완료·재진입 전이, `sniper_trade_review_report.py`의 완료 census/`_completed_trade_projection`, `strategy_position_performance_report.py::_build_trade_facts`.

1. record49266의 기존 DB 전이·SELL outbox·owner journal·수동 이관 영수증을 exact cycle/order/execution으로 대조하고 최초 COMPLETED 작성자를 특정한다. 기존 원문이 없으면 전이 원인 미확인으로 남긴다.
2. 검증된 실제 매도라면 원 주문·체결·원 수신시각을 보존한 별도 보충 영수증으로 완료 투영에 연결한다. 운영 원장을 재작성하거나 새 매도를 실행하지 않는다.
3. 수동 이관·관리 종료라면 `custody disposition`과 `economic terminal`을 별도 필드로 표시하고 손익 모집단에서는 이유를 명시해 제외한다. COMPLETED를 임의로 HOLDING으로 되돌리지 않는다.
4. 향후 상태 전이에는 terminal kind, 작성자/코드 세대, 원 cycle, 종결 원문 ref를 남긴다. 경제적 완료 fact의 sell identity가 없으면 profit/null 상태를 유지하고 별도 source finding을 낸다.

완료 시험: 실제 매도/이관/미확인 세 경우가 구분되고,49266→49328의 비용·수량·손익이 혼합되지 않아야 한다. DB COMPLETED3과 투영2의 차이를 설명하거나 검증된 원문으로 해소해야 한다.

### 3.2 알테오젠49268: 같은 날짜·종목의 복수 포지션 비용 배분 미지원

거부 사유는 **`broker_day_symbol_position_not_unique`**. 같은 날49268 완료2주 외49300 HOLDING1주가 존재한다. 공식 비용 원천은 있지만 현재 `broker_cost_source.reconcile_position`은 한 날짜·한 종목의 모든 거래를 한 완결된 Main intraday position이 소유하는 경우만 지원한다. 이 guard 자체는 잘못된 비용 귀속을 막는다.

보완 위치: `lifecycle/broker_cost_source.py`, `lifecycle/broker_cost_reconciliation.py`, trade review의 `cost_peer_records` 구성 및 실제 비용 receipt 소비.

1. 먼저 현재 보유·과거 carry를 섞어 만든 peer 목록과 **그 날짜 실제 경제 활동**의 peer를 구분한다. 다만 이번49268/49300은 같은 날 실제 활동이므로 단순 날짜 필터로 해결되지 않는다.
2. 기존 공식 원천의 order/execution/account/owner/route와 Main BUY·SELL leg를 전수 대사한다. 비용을 해당 position에 유일하게 귀속할 수 있는 공식 세부 근거가 있는 경우만 exact receipt를 발급한다.
3. 일계표 합계만 있고 position별 비용이 분해되지 않으면 정확한 배분은 불가능하다. `account/day/symbol` 수준 합계 검증과 position별 미배분 잔액을 표시하되 각 position의 비용 후 PnL은 null로 유지한다. 수량·거래대금 비례 추정 비용은 actual cost로 인정하지 않는다.
4. 이후 공식 정산 세부 원천이 들어오면 원 비용 세대와 보충 세대를 모두 남기고 정규 source generation에 포함한다. 주문번호와 거래번호를 임의로 같은 키로 취급하지 않는다.

완료 시험: 단일 position 회귀, 복수 완료+보유, carry+당일 매매, 부분체결/부분매도, 중복 execution, 다른 계좌·owner, KRW 반올림 잔액까지 검증한다. position별 수량·체결금액·배분 비용과 미배분 잔액의 합이 공식 합계와 보존되어야 한다. 공식 원천이 분해 불가능하면 정확히 그 상태로 종료한다.

### 3.3 HPSP49293: 잔여 leg 누락과 Main custody 대사 범위

거부 사유는 **`broker_cost_main_custody_unproven`**이며 알테오젠의 복수 position 사유와 다르다. 원장에는 BUY `0041093`1주, `0041094`8주, `0041096`12주가 존재한다. 정규 제출 census는 첫1주만 연결한다. [기존 HPSP 감사](../audits/main-hpsp-trailing-event-replay-and-sell-outbox-repair-review-2026-10-15.md)는 실제 SELL `0043525/61455`21주의 원 종결·후속 attribution ACK와 비용/원천 미확정을 분리해 보존한다.

현재 `_buy_parent_handoff_projection`은 `order_leg_sent`만 제출 원천으로 받고, `single_parent`/DB buy_qty 대조도 한 주문 중심이다. 따라서 잔여 주문을 이벤트 목록에 넣기만 해도 여러 child의 전체 position 수량21주 검증은 추가로 필요하다. 이번 점검은 기존 비용 거부 사유와 제출 누락을 확정했으며 전체97MB 투영의 하위 reject 목록까지 재생성하지 않았다.

보완은 §4.1의 공통 leg 계약을 먼저 적용한 뒤 **주문별 체결 보존 → position별 전체 수량 보존**의 두 단계로 한다. 원 parent/cycle이 입증된1+8+12주와 실제 SELL21주를 대조한다. `ORDER_TERMINAL` 문자열만으로 cancel/잔량/비용 증명을 만들어서는 안 된다. 정상 전량체결의 정규 종결 증거와 취소 후 종결 증거도 구분한다.

완료 시험: 첫 leg+잔여2개가 하나의 원 position으로 정확히 결합되고, 누락/중복/late fill/다른 cycle은 거부해야 한다. custody 복구 후 비용·실행 venue·매도 provenance의 다음 blocker가 남는지도 재검증한다. custody 복구만으로 실제 비용 PASS를 약속하지 않는다.

## 4. entry split·cancel-wait: 공통 누락을 먼저 고친다

### 4.1 잔여매수 제출 영수증을 공통 계약으로 연결

확정 미분류:

| record | 종목 | 주문 | 수량 | 실제 원장 action |
| --- | --- | --- | --- | --- |
|49293|403870|0041094|8|ENTRY_RESIDUAL_BUY|
|49293|403870|0041096|12|ENTRY_RESIDUAL_BUY|
|49268|196170|0046834|1|ENTRY_RESIDUAL_BUY|

생산자 `sniper_state_handlers.py`의 잔여매수 경로는 broker 접수 후 `residual_submitted`를 기록한다. 최초 경로의 `order_leg_sent`와 달리 공통 제출/timeout context를 전달하지 않는다. 소비자 `entry_cancel_wait_tuning._parents`, `entry_split_order_plan.build_execution_model_validation`, trade review BUY handoff는 이 주문들을 정규 lineage에 연결하지 못한다. 당일 declared-stage census `entry_cancel_wait_submission=9`, `order_leg_sent=7`이 정확하다는 사실은 **다른 실제 주문 stage까지 완전하다**는 뜻이 아니다.

제안 계약은 기존 producer 안에 넣고, 정규 ledger와 projection이 같은 제출을 두 번 세지 않게 한다. 새 engine-root 모듈을 만들지 않는다.

- 공통 식별자: source date, 원 position/cycle, parent/child/attempt, frozen plan ID/SHA, action receipt, owner/account, broker order·route, requested/submitted quantity·price, 실제 접수시각, 기존 timeout owner/schedule ref, 원 broker response ref.
- 결과 분기: accepted, rejected-before-dispatch, response-uncertain, accepted-but-receipt-pending을 구분한다. 응답 실패나 빈 주문번호를 주문0/비체결로 만들지 않는다.
- 최초 leg와 residual을 동일한 **정규 제출 식별자**로 census에 포함하되 실제 timeout owner는 보존한다. residual이 독립 cancel-wait 튜닝 대상이 아니면 명시적으로 source-only/excluded로 분류한다. 최초 timeout을 잔여 주문에 복사하거나 현재90/120/600/1200을 바꾸지 않는다.
- broker 성공 직후 receipt를 내고, callback이 먼저 체결/완료하는 경로에도 동일 영수증을 남긴다. source writer 실패는 연구 결손으로 분명히 기록하고 성공한 주문을 재발주하지 않는다.
- 과거3건은 원 `residual_submitted`·probe bundle·registry order/execution을 모두 검증한 **별도 불변 reconciliation receipt**로만 연결한다. ID suffix나 종목/근접시각만으로 parent를 추정하지 않는다. 입증할 수 없는 부분은 원 미분류로 남긴다.

수용: 정규 제출과 원장 실제 초기 진입 leg의 차집합이 없거나 명시적 격리 이유로 설명되어야 한다. 중복 stage·재시작·동시 callback에서도 같은 order는1회만 집계한다. HPSP21주·알테오젠2주를 보존하고 AVG_DOWN/다른 cycle/수동/퇴역 owner를 흡수하지 않는다. 원 source census를 조용히 소급 수정하지 않고 보충 세대의 lineage를 낸다.

### 4.2 gzip 원천을 평문과 같은 논리 원천으로 읽는다

`entry_split_order_plan._execution_projection_census`가 `producer_summary_paths`의 평문 `.jsonl`에 `is_file/stat`을 직접 적용한다.9/29·9/30은 `.jsonl.gz`만 남아 `execution_producer_census_missing`이 재현된다.

| 날짜 | gzip 원문 크기 | 행 수 | 검증 |
| --- | ---: | ---: | --- |
|9/29|3,542,017B|3,761|CRC/EOF, manifest 원문 크기·행 수 일치|
|9/30|3,601,825B|3,864|동일|
|10/1|미발견|미확인|producer census·manifest와 지정 execution partition 부재|

보완 대상은 읽기 함수 하나에 그치지 않는다. 기존 `utils/jsonl_io.py`의 gzip reader/동일성 계약을 재사용해 **discovery → manifest seal → reader → predecessor 비교 → bounded reconciliation metadata generation/cache currentness**가 같은 논리 source를 선택하게 한다. `_reconciliation_metadata_generation`의 평문 `lstat`도 함께 수정한다.

압축 파일 크기를 원문 manifest 크기와 비교하지 않는다. 물리 세대(stat/SHA)와 논리 원문 크기·해시·identity census를 분리한다. 평문/gzip이 함께 있으면 논리 내용의 동일성을 확인하고 충돌·CRC/EOF 실패·교체/append는 source invalid로 남긴다. 같다는 검증 없이 어느 쪽을 임의 우선하지 않는다.

9/29·9/30은 첫 읽기 결함을 고친 후 원 retained event hash/producer identity/부모 불변값을 다시 대조해야 한다. 이번 CRC/크기 일치는 그 후속 의미 검증의 PASS가 아니다.10/1은 정규 archive에서 원 ledger가 확인되면 이와 별도로 복구하고, 없으면 `unrecoverable_source_gap`으로 명시한다. zero-order day·새 수집본으로 과거를 대체하지 않는다.

### 4.3 checkpoint와 historical/source gap을 별도로 판정

현재 broker checkpoint에는 검증된 계좌 조회가 있지만 `current_custody=unknown / since_checkpoint_dispatch_continuity_missing`. `main_custody_checkpoint`는 checkpoint 날짜~평가 날짜 사이 어느 row라도 미분류이면 continuity를 거부한다. 따라서 위 당일3건 누락은 이 blocker에도 직접 영향을 준다. 빈 open-order 조회만으로 과거 불확실 주문이 정리됐다고 선언하지 않는다.

잔여 leg 분류 후 원 checkpoint·registry prefix/tail을 그대로 대사해 현재 custody를 재판정한다. 과거9/29~10/1 커버리지, 현재 custody, 경제성 eligible 날짜를 별도 필드로 유지한다. irrecoverable 과거 날짜를 제외할 때도 그 안의 미해결 custody를 숨기지 않는다. 이후 자료는 실제 checkpoint 이후 발생한 정규 dispatch/terminal의 연속성을 검증한다.

### 4.4 split 모델은 원천 복구 뒤에도 독립 검증이 필요

source15 경제성 input/model/paired 모두0, model scope0이며 진단 source count6은 적격 경제성6건을 뜻하지 않는다. post-sell2건 모두 exact split economic receipt가 없고 `cost_missing`이다. `build_execution_model_validation`의 기본 source-gap 결과 뒤에는 `_apply_operating_model_support`의 검증된 scope 지원 경로가 실제 존재한다. 모델이 영구 hardcoded 실패라고 단정하지 않는다.

순서:

1. 공통 leg·frozen plan/action receipt·정확한 완료 비용을 복구하고 지원/미지원 상태의 census를 공개한다.
2. 실제 모델 calibration과 시간상 뒤의 독립 model holdout으로 수량/가격/체결시계·비용·자본 노출 오차를 구한다. receipt 수신시각과 거래소 체결시각을 혼동하지 않는다.
3. scope별 tolerance를 calibration에서 봉인한 후 holdout을 검증한다. paired 후보 calibration/holdout은 모델 holdout과 독립시켜 consumed-holdout 이력을 보존한다.
4. passive queue·알 수 없는 partial fill·미확인 CF cancel/late fill·후속 ADD/partial sell·상태별 AI 입력 부재는 현재 모델의 미지원 상태로 남긴다. 필요한 원천과 모델을 보완하기 전 경제성 후보로 올리지 않는다.

기존 계약의 모델20·paired30(15/15) floor를 낮추지 않는다. 데이터 연결 코드의 수정 완료는 fixture/원천 검증으로 닫고, 실제 표본·모델·경제성 수용은 기존 family owner의 별도 OPEN으로 유지한다. Main 전체 신규 진입을 막거나 승인된 초기 기계정책에 새 경제성 gate를 붙이지 않는다.

## 5. outcome labels: 두 개의 독립 결함을 분리

### 5.1 최종 wire 해시의 덮어쓰기

`AIEngine._resolve_ai_input_contract_fields`가 기존 `formatted_data` 해시를 만든 뒤 continuous-reversal 분기에서 실제 wire를 `continuous_reversal_input`으로 다시 구성한다. `capture_ai_request`는 최종 wire의 올바른 해시/envelope를 기록한다. 그러나 `_annotate_analysis_result_frame`의 `payload.update(input_contract_fields)`가 capture 해시를 이전 해시로 덮어 trace/label에 저장한다. 이 함수만 AST로 분리해 provider나 파일 쓰기 없이 재현했다.

대표 trace `analyze_target:034020:1792018982868:0293a8fe`:

- 보관 actual payload SHA: `3c7cf243a2ca8ba48bfa75c94b9527eb87bf9a3c7b021191f91d24223f33c7b0`.
- trace/label SHA: `3f4ad3401859b8b69ff733c08658a73b1b86a06d7131e7af797eb19a6162037d`.
- 두 표본 모두 trace request-envelope SHA는 실제 archive와 같으나 payload SHA만 다르다. `_payload_for_trace`의 엄격한 불일치 거부는 유지해야 한다.

보완:

1. 최종 요청 캡처를 `wire payload hash/bytes/envelope/prompt`의 단일 소유자로 정한다. pre-composition 해시는 별도 진단 필드로 보존하고 capture provenance 예약 키를 일반 input field merge가 덮지 못하게 한다.
2. cache delivery/parent trace, timeout·exception·provider 미호출 경로도 각각 원 요청과 연결한다. provenance 검증 실패는 연구 source finding으로 남기며 새 BUY veto나 provider 재호출로 바꾸지 않는다.
3. 과거283건은 복구 **후보**다. request ID만으로 승인하지 않고 envelope, model/schema/prompt, source/policy 세대, 심볼·stage·venue/session, 원 시각, actual payload 재직렬화 규칙, 원 response를 모두 검증한다. 불변 정정 영수증에 old trace SHA·old payload SHA·actual payload SHA·검증자 코드 SHA를 묶고 새로운 파생 label 세대를 만든다. 원 trace/label bytes는 보존한다.
4. 미발견1건 `analyze_target:403870:1792025902532:5833c760`은 원 request/기준가가 없다. 대체 source가 없으면 미관측으로 종결 표시한다. label horizon은 이미 지났으므로 계속 기다린다고 해결되지 않는다.

반대 방향에도 원 request는 있지만 label 집합에는 없는1건 `analyze_target:034020:1792019019119:30a149b8`이 있다.08:03:39의034020 요청으로 위09:58:24 HPSP 결손과 심볼·시각·ID가 다르다. 남은 건수가 같다는 이유로 서로 연결하지 않는다. [양방향 차집합](../../tmp/postclose-source-gap-deep-review-20261016/unmatched-request-identities.json)을 보존하고 요청 캡처→최종 trace/outcome 사이의 누락/실패 ending을 따로 대사한다. 요청 캡처만으로 provider 실제 접수나 응답을 합성하지 않는다.

수용: 정상 provider 호출의 trace/envelope/payload hash가 일치하고, 의도적 변조·동일 ID 다른 body·cache parent·partial archive 쓰기를 구분해야 한다. 과거 label 복구 성공/거부/원문 미발견의 합이284건이며, 별도 orphan request1건도 고유 ending 또는 미확인 상태로 보존해야 한다.

### 5.2 compact 현재 입력과 legacy exact_v2 연구 계약 불일치

보관 입력은 `continuous_reversal_union_auxiliary_v3`이고283건은 archive `replay_exact=true`, replay context도 exact다. 이것은 **보관한 compact 원문을 정확히 재생할 수 있음**을 뜻한다. legacy `entry_candle_context_v1`/`exact_v2`에 필요한 완료 bar·input bundle·context schema가 있다는 뜻이 아니다. 현재 labels284건의 exact_v2/preflight/canonical bars 요건은 충족되지 않았다.

따라서 해시를 고쳐도 기존 canonical-primary 적격 표본이284건으로 바뀌지 않는다. `baseline_v1`을 exact_v2로 개명하거나 없는 bar를 생성해서는 안 된다.

- 현재 compact family에는 실제 승인된 schema·wire envelope·원 machine opportunity·prompt/policy·as-of source·response validator·관측 horizon을 기준으로 별도 typed eligibility를 둔다. 기존 canonical-primary 연구의 요구조건은 보존한다.
- compact 내부에 존재하지 않는 필드는 `not_in_this_contract`로 명시하고, 그 필드가 필요한 다른 실험에는 `unsupported/source_gap`으로 유지한다. prompt 비교는 동일 원 opportunity/input의 paired 비교만 허용하며 기존 보조평가 응답·구성원·지표를 변형하지 않는다.
- live239/timeout45와 parse/semantic-validation 결과는 복구 후에도 분리한다. transport 오류나 validator 미적용을 프롬프트 판단 실패/성공으로 바꾸지 않는다.
- 단순 가격 horizon label의 mature160/partial123/pending1과 primary 연구 적격성은 별도다. 참조가 없는 pending은 만기 후 source-gap 상태와 이유를 낼 수 있게 하고 가격이나 손익을0으로 채우지 않는다.

## 6. holding·손절 연구: 실제 입력 경로를 보완

### 6.1 실제 두 거래의 보유 입력 결손

완료 position의 봉인 경로를 직접 확인했다.

| record | QUOTE | 재구성 ADD | quote coverage=true | vote coverage=true | EXIT_TRAILING_TP 판정 |
| --- | ---: | ---: | ---: | ---: | --- |
|49268|195|1|195|0|72건 전부 INSUFFICIENT, provider 미호출|
|49293|196|2|196|20|33건 전부 INSUFFICIENT, provider 미호출|

105건의 공통 거부 사유는 `path_input_missing:source_preflight_blocked,holding_flow_evidence_missing,executable_exit_pnl_missing`; route/epoch는 `SOURCE_GAP`, actual_input_verified=0. 보관 가격/BBO가 있다고 해서 같은 시각의 보유 flow/context·실행가능 손익·vote collector coverage까지 있었다고 간주할 수 없다. HPSP의 일부20개 coverage는 다른176개 구간이나 모든 signal의 coverage로 확대할 수 없다.

보완 위치: `sniper_state_handlers._run_vote_review/_collect_holding_path_votes/_holding_context_call_views`, `ai/holding_exit_vote.build_path_vote_input/path_vote_input_gaps`, `ai/holding_vote_replay_source.begin_coverage/runtime_source/PreparedVotes`, `scalping/holding_decision_context.py`.

1. source preflight의 실제 거부 입력을 작은 불변 ref로 보관한다. context 생성 실패, 비활성 forensic view, schema 불일치, canonical bar/flow 결손을 구별할 수 있도록 원 `source_quality.blockers`, 활성 정책 영수증, source hash/clock를 남긴다. 현재105개 짧은 gap 문자열만으로 어떤 상위 필드가 왜 없어졌는지까지는 확정할 수 없다.
2. 기존 승인된 activation 계약을 기준으로 runtime context와 forensic-only context의 전달을 점검한다. 누락을 없애려고 env/promotion gate를 켜거나 forensic 자료를 실제 입력으로 승격하지 않는다.
3. 동일 frozen BBO·position 수량/원가와 기존 비용 모델에서 실행가능 손익을 구성하고 flow/context adapter에 전달한다. runtime의 추정 실행가능 손익과 실제 정산 PnL을 다른 필드·authority로 유지한다. 신선하지 않은 source를 재사용하거나 `flow={}`를 정상으로 통과시키지 않는다.
4. quote transition 전에 native buy generation의 collector 시작/checked/PID를 기록하고 frozen worker 결과는 position·buy-fill generation이 동일할 때만 live state에 전달한다. 원 코드에는 이미 이 전송 경로가 있으므로 무작정 추가 복사하지 말고 호출순서·조기 return·restart/ADD 경쟁을 시험한다. 재시작 전 coverage를 소급 발급하지 않는다.
5. 입력이 적격해진 뒤 기존 due 호출·budget 안에서 자연 발생한 요청→응답→VALID/INSUFFICIENT→원 input ref의 소비를 확인한다. 과거 미호출105건을 새 모델 호출로 채우지 않는다. prompt 성능 연구는 원 입력이 유효한 paired 모집단에서 시작한다.

수용: 유효 fixture는 완전 경로를 통과하고, 위3개 입력이 빠진 fixture는 각각 정확한 이유로 거부해야 한다. 자연 호출 유무·quote/vote coverage·actual input 검증을 별도로 보고한다. source 코드 수리의 완료에 수익률 개선을 추가 조건으로 붙이지 않는다.

### 6.2 470개 ENTER/PASS 기회에 후속 경로가 없는 문제

all-scope 연구는 scope20,832개의 계산을 완료했으나 population474·eligible/common0이다. 구성은 실제 완료2, 대체 exit2, native 기회470이며, assembler는470건 모두 `native_forward_path_unobserved`로 기록했다. 또한 완료 거래에는 `classification_source_gap/legacy_context_unbound`가 있다. 이미 계산한 조합을 더 돌리는 것이 해결책이 아니다.

`main_trailing_source_assembler._trace_rows`는 AI trace event 안의 `universal_trailing_quote`, planned quantity/basis/cost/context를 기대한다. 현재 입력과 소비 기대가 연결되지 않은 상태다. 다음과 같이 보완한다.

- 원 evaluation_attempt/opportunity/source·policy 세대에 결속된 작은 frozen execution snapshot을 실제 생산자에서 발급하고 assembler는 그 ref를 읽는다. trace에 대형 quote/전체 context를 반복 복사하지 않는다.
- 기존 관측 경로 중 동일 item/venue/session/transport epoch·시계·순서가 입증되는 자료만 ref로 결합한다. 기존 자료가 없으면 향후 source-only 관측을 기존 collector/budget에 편입한다. 새 WS 등록·REST/provider 증설은 별도 프로토콜/운영 검토 없이 실행하지 않는다.
- forward path의 시작/마지막/중단·갭·재접속·관측 horizon과 frozen quantity·비용 모델을 봉인한다. 자연 actual BUY와 미진입 CF는 서로 다른 namespace로 유지하고 실제 SELL을 CF exit로 재사용하지 않는다.
- 과거470건의 기준 시점/호가/후속 경로가 없으면 원 gap을 유지한다. 사후 현재 가격으로 경로를 만들지 않는다. classification pin은 원 entry feature가 검증될 때만 복구한다.

### 6.3 손절 operating 원천과 수동 custody

7개 기회의 별도 operating 비교 사유는 `operating_quote_source_unverified`3, `preset_effective_stop_unobserved`3, `automatic_source_after_manual_handoff`1이다. 어떤 예에는 유효한 preset와 실제 registered manual handoff가 있으므로 “preset/수동 영수증이 전부 없다”는 진단은 틀리다.

우선 수리할 것은 **수동 이관 후 자동 상태 원천1건의 시계·custody 세대**다. 실제 자동 주문이 있었다는 증거로 확대하지 않되 연구 원천의 ownership 불일치로 취급한다. `main_stop_policy.source_row`와 collector가 공통 native journal의 관리 disposition을 같은 position/pin/시각에 읽도록 하고, frozen worker의 예전 자동 flags가 수동 이관 뒤 source에 섞이는지 시험한다. manual veto를 해제하거나 과거 이관을 취소하지 않는다.

quote 불량3건은 coverage/item/route/epoch/quote_at freshness의 개별 실패를 작은 projection에 남긴다. 원 BBO가 있으면 원 시각·세대로 연결하고, 없으면 source-gap을 유지한다. preset 미관측3건은 기존 [preset·cost-clock·handoff 수리](../audits/main-holding-preset-cost-clock-and-manual-handoff-contract-repair-2026-10-15.md)의 배포 시점과 자연 수용을 대조한다. 이미 닫힌 구현을 전부 재개하지 않고, 새 재현 결함이나 배포 후 누락이 있을 때 그 부분만 수리한다.

`alternative_lifecycle_unidentified`4건은 반사실 경로가 관측 종료·부분체결·후속 상태 미확정으로 censored된 표본이다. 실제 terminal·no-add/ADD·quote/cost 경로가 입증될 때만 재평가하며 손실·0원·실제 미매도 확정으로 바꾸지 않는다. hard/protect/emergency 및 실제 preset 안전장치는 연구 적격성과 별개로 보존한다.

## 7. 구현 순서·기존 owner·검증

아래 WP는 이 제안의 작업 단위이며 신규 checklist stable ID가 아니다. 실제 작업 예약·OPEN 관리에는 기존 owner를 사용한다. 소스 구현은 착수 시 재고정한 운영 릴리스 기반 격리 작업공간에서 진행한다.

| 순서 | 작업·주요 위치 | 기존 실행 owner와 경계 | 코드 검증·원천 수용 |
| --- | --- | --- | --- |
|WP1 병행|wire capture/annotation 해시 소유권; gzip 논리 source 전 구간|`DirectFamilySourceRepairCompactAuxiliary`, `DirectFamilySourceRepairEntryCancelWait`, split owner의 영향 부분|기존 AI trace/quality/transport·cancel-wait/split 테스트에 hash 변조·gzip CRC/alias 충돌·세대 교체·cache 무효화 회귀; 과거283건 및 두 날짜는 별도 정정 receipt|
|WP2 우선|residual 공통 제출·position 전체 체결 대사; 수동 이관 후 source 상태|`DirectFamilySourceRepairEntrySplit`, `DirectFamilySourceRepairEntryCancelWait`, `HoldingProfitExitSourceContractRepair`|HPSP1+8+12·알테오젠1+1·duplicate·uncertain·callback 선행·partial/cancel/late fill·manual race 시험; 미분류3과 custody 재판정|
|WP3 WP2 후|완료 census/경제적 terminal, exact cost allocator·receipt|`HoldingProfitExitSourceContractRepair`; split/cancel의 완료-cost 소비 부분|삼성 cycle 불일치, 동일 종목 다회매매·carry·mixed owner·금액/수량/비용 잔액 보존; 분해 불가능 비용은 명시적 null|
|WP4|보유 context/preflight/추정 executable PnL·collector coverage와 typed compact eligibility|`HoldingProfitExitSourceContractRepair`, `MainStopLossRetirementRuntimeTuning1010`, `DirectFamilySourceRepairCompactAuxiliary`|입력 gap별 fixture, restart/ADD/PID·frozen/live 경쟁, 실패한 activation 격리, 원 request/response·policy 연결; 임의 provider 호출 없음|
|WP5 앞선 원천 후|기존 bounded opportunity forward-path ref·split 독립 모델/paired holdout|기존 split·holding owner; scope 밖 collector 증설은 그 owner에 구체 범위 인계|실제/CF·동일 원 opportunity 보존, 모델·후보 holdout 분리, 원천 적격 범위의 경제성 검증|
|WP6 허용된 장후|변경 family만 불변 successor로 재생성하고 정상 consumer까지 확인|`DirectFamilyPreopenPolicyHandoff`가 날짜별 후속 정책/PREOPEN/PID 소비를 관리|native receipt→family reader→summary/controller/handoff를 동일 source/target/hash로 검증; 코드·발행·선택·PID·자연 행동·경제성은 따로 보고|

관련 기존 테스트는 `test_ai_decision_trace.py`, `test_ai_decision_quality.py`, `test_ai_engine_openai_transport.py`, `test_entry_cancel_wait_tuning.py`, `test_entry_cancel_wait_attribution.py`, `test_broker_cost_source.py`, `test_main_trailing_source_assembler.py`, `test_research_json_stream.py`와 해당 holding/stop/receipt 시험이다. 목록 전체를 무조건 돌리지 않고 변경된 생산자/소비자 계약에 맞는 표적 집합을 고른다. 새 파일이 필요하면 역할별 기존 package/test 위치를 먼저 검토하며 engine-root를 늘리지 않는다.

각 WP는 `구현→자체 리뷰→보완→재리뷰→표적 pytest/compile→diff 검사`로 닫는다. 코드 closure와 실제 historical recovery/natural acceptance/경제성을 별도로 기록한다. Kiwoom 요청·parser·FID·continuation·auth·계좌/주문 호출에 손대야 한다면 당시 공식 저장소 revision·관련 upstream 파일·조회시각을 먼저 확인하고 [공식 참조 gate](../kiwoom-api-data-contract.md)를 적용한다. 이번 제안의 로컬 진단은 protocol 변경이나 실제 호출을 하지 않았다.

성능 수용도 결손 수리와 함께 확인한다. 원 production event에 작은 source ref를 한 번 남기고 기존 bounded writer·봉인 partition/manifest를 재사용한다. 변경 없는1회 실행에서 같은 원천의 반복 full decode/hash를 추가하지 않는다. monitor에는 개별 사유·census·세대만 내보내고 native 의미 검증을 생략하지 않는다. 기존 메모리·decoded-byte·임시 디스크/queue 한도를 늘려 gap을 숨기지 않는다. frozen fixture의 논리 읽기량·CPU/벽시계와 저용량 projection의 의미 동등성을 전후 비교한다.

## 8. 재처리·종료 기준과 이번 검토의 한계

원 보고서·journal·label·정책·checkpoint와 과거 실패 시도는 보존한다. 먼저 작은 source-only 정정 manifest에 복구 성공/거부/원문 없음, 원 hash·보충 hash·코드 세대·exact identity를 남긴다. 원천 수리가 검증되기 전 대용량 연구나 전체 장후 체인을 반복 실행하지 않는다.

후속 재처리가 허용된 장후에는 변경된 비용/lineage→완료 projection/fact→해당 split/cancel/label/holding family 순서로 의존성을 따라 새 세대를 만든다. 현재 봉인 checklist·정책/PREOPEN을 문서 수정으로 무효화하지 않는다. operational handoff가 바뀌는 재발행은 기존 family/runtime owner의 정상 세대 전환으로 처리한다.

최종 결과는 다음5개 상태로 구분한다: **코드 결함 수정**, **검증된 원문으로 복구**, **원문 부재로 과거 복구 불가**, **관측/모델 미지원 또는 censored**, **향후 자연 수용 대기**. 전체 경고를0으로 만들거나 과거 표본을 전부 적격으로 만드는 것이 종료 기준이 아니다. 각 결손의 정확한 owner·원천·상태·다음 행위·완료 시험이 있어야 한다.

이번 점검에서 source15의 해시 덮어쓰기와 gzip 오판독을 재현했고, residual3건·완료2건의 서로 다른 비용 거부·보유105건의 입력 거부를 구체화했다. 삼성 COMPLETED 작성 원인, 공식 자료의 position별 비용 분해 가능성, 보유 preflight 내부의 최초 누락 필드는 추가 구현 전 원문 대사가 남아 있다. 이를 확정 원인으로 꾸미지 않았다. 이 문서는 구현/배포 완료, 정상 기동 보장 또는 비용 후 성과 개선의 영수증이 아니다.

문서 검토·검증 기록은 [review-validation.json](../../tmp/postclose-source-gap-deep-review-20261016/review-validation.json)에 남긴다. 이전 대화의 checklist SHA `f9b27d…`는 이 점검의 변경 전 기준으로 쓰지 않는다. 이번 진단에서08:06:53 실제 관측한 `394a2f6ec09faf8eb31446a802848a66e2b3330ae0fecc64085197a97ffc7d6f`와 문서 검토 후 bytes를 대조하며, 동시 운영 작업의 변경을 되돌리지 않는다. 문서 외 작업공간의 동시 변경은 보존한다.

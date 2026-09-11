# 위젯·에피소드 진입 직전 악화 보류 — 최종 구현안

작성일: 2026-09-10 KST. 최초 문서 작성은 설계-only였으며, 후속 명시 구현 요청의 최신 상태는 [구현·리뷰](../audit-reports/2026-09-10-entry-adverse-flow-implementation-review.md)를 따른다. **개발 코드 구현/검증과 배포·정책/PID·경제성은 별개다.** 아래 최초 문서 검증 receipt는 역사로 보존한다.

2026-09-11 자연 표본 후 사용자 확인에 따라, 최근 체결이 드문 종목은 진입 후 청산 유동성과 자본 회전에 불리하므로 live guard에서 정상 0체결 창을 `CONTINUE`로 허용하지 않는다. 0D/등록/writer가 정상이어도 최근 0B watermark가 freshness를 충족하지 않으면 `SOURCE_UNAVAILABLE`로 미제출하며, 이는 source pipeline 장애와 구분하는 의도된 유동성 차단이다. 이 명확화는 기존 runtime 동작을 유지하며 실주문 조건을 완화하지 않는다.

사용자 요청: “일단은 구현해서 가동을 해봐야 무엇이 맞을지 판단이 가능할 것 같아. 최종 구현안 작성해줘.” 이번 산출물은 구현안이며 해당 문장이 이번 문서 작성 중 실주문·재기동을 실행하라는 지시로 확대되지는 않는다. 이후 명시적인 구현/배포 요청의 범위를 기준으로 진행한다.

원칙 owner는 [Plan Rebase §1~§8](../plan-korStockScanPerformanceOptimization.rebase.md), 후속 owner는 [9/10 체크리스트](../checklists/2026-09-10-stage2-todo-checklist.md)의 `MachineLifecycleTurnoverObjectiveFollowup0910`이다. 새 정기 producer나 별도 OPEN ID를 만들지 않는다. 이 설계명과 아래 제안 contract 이름은 producer가 발급한 native recommendation ID가 아니다.

## 1. 결정과 1차 범위

**기존 매수 신호가 생긴 뒤, 제출 직전 하락·매도 체결 우세가 함께 확인되면 바로 버리지 않고 짧게 기다린다. 정해진 시간 안에 악화가 해소되고 원 진입조건도 유효하면 제출하고, 아니면 이번 신호만 종료한다.**

- 1차 구현: 공통 순수 계산기, bounded 대기 상태, 위젯/에피소드의 제출 전 adapter, exact receipt와 장후 집계, 테스트 및 최초 canary 활성화/철회 계약.
- 최초 live 대상: 기존 validator가 정상적으로 허용한 `baseline_immediate` 경로 중 승인 manifest가 지정한 owner/symbol/profile/venue/session의 **신규 진입**. 위젯 추가매수/scale-in은 제외하며, 에피소드는 원래 두 개 10주 leg의 각 미제출 진입을 확인한다.
- 기존 fixed-delay/dynamic timing이 선택된 scope는 1차 활성화에서 제외한다. 신호 확인 횟수·진입 timing 선정과 같은 stage의 canary를 겹치지 않는다. 배포 전 충돌 scope를 명시하고, runtime에서 정책이 바뀌면 대기 신호를 종료한다. 기존 정책을 baseline으로 강제 변경하지 않는다.
- 매수 가격 산식·수량·target·cap·원 신호 선정/확인 횟수·원 주문 유효기간·시장약세/유동성/가격 freshness/broker/custody safety는 그대로 유지한다. 새 AI 호출과 실시간 API 조회는 없다.
- **이미 제출된 BUY의 악화 취소는 2차 별도 범위**다. 1차에서 대기 종료는 미제출 신호 종료이지 broker 취소가 아니다. 기존 pending BUY 취소·부분체결·보유/SELL 관리는 원 owner가 계속 수행한다.
- 최소 profit-stagnation 보조청산, 별도 WS target-ratchet 개발 및 main submit drought 수리는 별개다. 이 변경에 함께 배포하거나 이 변경의 효과로 합산하지 않는다.

가설은 “하락 중 체결되기 쉬운 주문을 잠깐 늦추면 불리한 체결을 줄일 수 있다”이다. 지정가 주문의 역선택과 지연 문제는 [Lehalle·Mounjid 연구](https://arxiv.org/abs/1610.00261v4)의 검토 대상이지만, 이 연구는 아래 한국 주식용 조건·5초 설정의 수익 개선을 입증하지 않는다. 본 안의 초기값은 실전 검증할 휴리스틱이다.

## 2. 기존 동작과 새 정책의 차이

현재 [timing loader](../../src/trading/config/machine_entry_timing_policy.py)의 `baseline_immediate` 자체에는 추가 5초 감시권이 없다. 따라서 아래 대기는 **새 entry 정책 변경**이며 일반 source-only 수리 또는 기존 일별 자동 승인으로 간주하지 않는다. loader의 baseline 반환만 보지 않고, 원 owner의 정책 유효성·승인·오류 처리까지 통과했는지 확인한다.

현재 [동적 확인](../../src/trading/market/micro_confirmation.py)의 `evaluate_live_dynamic_confirmation_progress`는 `ADVERSE`를 `REJECT/adverse_checkpoint_veto`로 끝낸다. source gap은 정책에 따라 `BASELINE_REVALIDATE` 또는 `REJECT`다. 이 구현안은 그 결정을 WAIT로 바꾸거나 거절된 신호를 부활시키지 않는다.

현재 동적 checkpoint에는 nominal cutoff와 최대 1,500ms 처리 지연이 따로 있다. 이를 참고해 **새 정책에서는 판정 관측시점 T0+5초까지, 처리/전송 진입의 절대 상한 T0+6.5초**로 정한다. 기존 코드에서 발견한 것은 checkpoint 처리 지연 허용이며, 모든 현재 기계에 이미 6.5초 대기/전송 상한이 구현돼 있다는 뜻은 아니다.

## 3. 감시 시계와 종료

| 항목 | 1차 계약 |
| --- | --- |
| T0 | episode는 원 `signal_decision_at`, widget은 원 loop가 해당 신호를 진입 확인 단계에 처음 전달한 저장 `observed` 시각. 신호/episode/leg identity에 고정하며 반복 guard 호출·마지막 WAIT 시각으로 재설정하지 않음. bar/snapshot 시각을 실제 판단시각으로 가장하지 않음 |
| nominal checkpoint | T0+0/1/3/5초. 0초도 직전 1초의 완전한 자료로 판단하므로 무조건 1초를 먼저 기다리지 않음 |
| checkpoint 자료 | cutoff C의 `(C−1,000ms, C]` 체결과 그 창을 덮는 causal 호가. C 뒤 도착 자료로 당시 판정을 유리하게 고치지 않음 |
| 처리 허용 | 각 checkpoint는 C부터 C+1,500ms 안에서만 처리. 같은 checkpoint의 성공/악화 판정을 나중 자료로 덮지 않음 |
| 마지막 상한 | 모든 새 전송 진입은 T0+6,500ms 이하이며 원 신호/세션/주문 진입 deadline이 더 빠르면 그 시각이 우선 |
| 새 신호 | 기존 owner가 새로 발급한 신호만 새 T0 허용. 같은 payload 재수신·loop 반복·재시작·두 번째 leg 순회는 연장이 아님 |

단일 owner loop가 기한을 관리하고 WS snapshot 갱신은 기존 공급 계약을 사용한다. 새 주문 thread, raw callback 주문, sleep으로 owner 전체 차단 또는 API polling 빈도 상향을 추가하지 않는다. 여러 checkpoint를 지나 재개되면 지난 미처리 checkpoint를 `missed_checkpoint`로 남기고 허용 지연 안의 최신 due checkpoint 하나만 처리한다. 과거 시점의 가짜 재생/연속 PASS를 만들지 않는다.

신호가 10:00:00에 발생했다면 00/01/03/05초에 판단한다. 01초에 악화가 해소되어도 원 진입조건 재검증을 통과해야 제출한다. 05초까지 악화/근거 결손이면 이번 신호를 종료한다. 마지막 판정 처리가 늦어져도 새 전송 진입을 허용하는 절대 끝은 06.5초이며, 이미 보낸 요청의 응답은 그 뒤 도착할 수 있다. 응답 지연은 취소/재전송 권한이 아니다.

마지막 전송 직전의 최신 시장 재검사는 아래 §5의 별도 veto다. T0+5초 뒤 자료로 새 긍정 checkpoint를 만들거나 감시를 늘리지 않는다. 기존 신호 소멸·정책/route 변경·원 safety 거절·세션 종료는 5초 전이라도 종료한다.

## 4. 공통 악화 계산 — 최초 고정값

공통 계산은 네트워크·주문·정책 발행 없는 `src/trading/market` 소유다. 기존 [fixed-price kernel](../../src/trading/market/confirmation_window.py)의 정규화·route/epoch/sequence·고정창 검증을 재사용하되, 그 feature version의 기존 의미나 BUY/WAIT 결과를 조용히 변경하지 않는다. 새 계산 결과는 제안명 `machine_entry_adverse_flow_v1`로 별도 version/hash를 가진다.

완전한 1초 창을 앞/뒤 500ms로 나눠 다음 값을 만든다. 체결은 `(C−1,000,C−500]`, `(C−500,C]`로 한 번만 배정한다. `BUY_i`, `SELL_i`는 각 반창의 확인된 aggressor별 실제 체결수량, `sell_rate_i = SELL_i / 0.5초`다. `bid_start`는 창 시작까지 수신된 유효 시작 bid, `bid_end`는 cutoff까지의 마지막 유효 bid, `bid_min`은 창 내 유효 bid 최저값이다.

다음 **네 조건이 모두 참일 때만** 새 guard는 `DEFER_ADVERSE_FLOW`를 반환한다.

1. `bid_end < bid_start`: bid 가격이 하락했다.
2. `SELL_1 > BUY_1` 및 `SELL_2 > BUY_2`: 두 반창 모두 실제 매도 체결이 우세하다.
3. `sell_rate_2 >= sell_rate_1`: 후반 매도 속도가 줄지 않았다.
4. `bid_end == bid_min`: 현재 bid가 창 내 저점에서 회복하지 못했다.

입력이 유효하지만 결합이 거짓이면 `CONTINUE`다. 이는 BUY 지시나 반등의 경제성 보장이 아니라 **이 추가 악화 조건은 현재 충족하지 않음**이다. 하나의 완전한 후속 checkpoint에서 악화가 해소되면 추가 연속 PASS 횟수를 요구하지 않는다. 원 신호와 기존 guard가 제출 권한을 계속 소유한다.

매도잔량 감소·동일 가격 BUY 설명·refill·bid 반등은 기존 계산에서 얻는 진단값으로 함께 기록한다. 1차에 모두 독립 threshold로 추가하지 않으며, 매도잔량 감소만으로 BUY를 만들지 않는다. 기존 kernel에 없는 bid 잔량 감소를 계산했다고 주장하지 않는다. 수익 최적 속도 임계값·종목별 자동 grid·밤마다 threshold 자동변경은 범위 밖이다.

### 4.1 원천 불충분

- exact owner의 symbol/venue/session/item, 수신시각, 0B/0D epoch·route 연결, 순서·중복·truncation과 양 끝 호가 freshness를 검증한다. 기존 더 엄격한 freshness 기준을 완화하지 않는다.
- 120행/5호가 버퍼가 존재한다는 사실만으로 1초 완전성을 인정하지 않는다. local sequence 연속성은 로컬 투영 증거이며 거래소 전체 무손실 보증이 아니다. transport/collector의 원 health·누락 증거도 보존한다.
- 불명 aggressor, clock 역행, 음수/비유한 값, cross-epoch, 과거 창 탈락, stale 시작/끝 호가와 최근 체결 watermark 결손은 `SOURCE_UNAVAILABLE`다. UNKNOWN을 SELL로 간주하거나 결측·저빈도 체결을 0으로 보간하지 않는다. source-only 진단에는 정상 무체결 사실을 그대로 보존할 수 있지만 live `CONTINUE` 권한은 만들지 않는다.
- 활성 scope에서는 유효한 checkpoint가 남으면 다음 시점까지 기다리고, 끝까지 결손이면 `SKIP_SOURCE_UNAVAILABLE`로 이번 신호를 종료한다. 원래 baseline으로 조용히 우회하지 않는다. 기존 dynamic의 source fallback 계약을 변경하는 것은 아니다.
- 결손은 영향 route/scope에만 적용한다. 전역 snapshot 계약이 깨졌으면 이 guard에 의존하는 활성 scope의 새 진입을 차단하되 기존 보유/청산·비대상 owner까지 중단하지 않는다. 반복 결손은 source owner 결함으로 보고하며 threshold/호출량을 완화하지 않는다.

## 5. 상태·제출 원자성·재시작

| 현재 상태/사건 | 다음 동작 |
| --- | --- |
| 새 신호, 원 guard 허용, 활성 baseline scope | `PENDING_CONFIRMATION`; identity/T0/deadline/policy pin 저장, due checkpoint 판단 |
| CONTINUE | 현재 원 신호·정책·가격·quantity/custody·시장약세/유동성 등 전체 기존 guard 재검사 후 제출 준비 |
| DEFER_ADVERSE_FLOW / SOURCE_UNAVAILABLE, 다음 checkpoint 존재 | 해당 사유의 WAIT; 주문 미제출. 다른 owner 작업/원 보유관리는 계속 |
| 최종 악화 / 최종 source gap / 처리 상한 초과 | 각각 `SKIP_ADVERSE_FLOW` / `SKIP_SOURCE_UNAVAILABLE` / `SKIP_DEADLINE`; 해당 신호 terminal |
| 원 신호 무효, 기존 terminal safety veto, policy/route/epoch identity 변경 | 원 사유를 보존하고 terminal; 새 guard의 악화로 재라벨링하지 않음 |
| 기존 guard가 정상 WAIT를 반환 | 원 bounded wait를 존중하되 새 절대 deadline도 연장하지 않음. 원 WAIT를 악화/terminal 거절로 재라벨링하지 않음 |
| 전송 시작 뒤 성공/부분성공/모호한 응답 | 원 주문 owner/reconciler로 넘김. 이 감시 상태로 돌아가 새 주문하지 않음 |

`CONTINUE`와 broker 전송 사이의 quota 대기·비동기 preflight 동안 시장이 바뀔 수 있다. 따라서 transport를 실제 호출하기 직전에 **같은 owner의 동기식 검사**로 deadline, frozen policy/identity, 최신 fresh source와 악화 조건을 다시 확인한다. 후속 구현에서는 최신 메모리 view 공급 경로가 없어 검증된 로컬 snapshot/정책을 다시 읽고 I/O·상태 저장 뒤 deadline을 재검사하도록 구체화했다. 새 broker/API 호출은 없으며, 최신0B/0D receipt와 window endpoint의 sequence/time을 대조한다. 이 최신 창 검사는 별도 receipt로 남기며 nominal checkpoint 판정을 덮지 않는다. 새 악화/결손이면 남은 checkpoint로만 돌아가고, 남지 않으면 종료한다. 전송 직전 기존 hard guard도 그대로 유효해야 한다. raw WS 즉시 반응이나 네트워크 지연 제거를 보장하지 않는다.

gateway 내부 대기 뒤 이 검사를 삽입할 수 없는 경로는 `pre_transport_revalidation_not_supported`로 최초 활성화 대상에서 제외한다. 호출 바깥 검사만 붙여 실제 전송 직전 보장을 했다고 보고하지 않는다. 검사와 transport 사이 무대기 구간 및 남는 네트워크 지연을 테스트/receipt로 명시한다.

대기 중에는 broker 주문번호가 없어야 한다. 가능한 한 예약/BUY_SUBMITTING 전 판단하고, gateway 내부 마지막 veto 때문에 이미 예약했다면 **전송 전임이 확정된 자기 예약만** 원 registry 계약으로 되돌린다. 전송 시작·모호한 응답 뒤에는 예약을 풀거나 같은 signal을 재시도하지 않는다. adapter 반환형은 `not_sent_deferred`와 실제 broker reject/ambiguous를 구분하며 기존 예외 처리에 섞지 않는다.

identity는 원 owner/account scope·거래일·symbol/venue/session·signal ID·episode/leg ID에 결속한다. 유효 기존 signal ID가 없으면 hash를 새 거래 권한으로 발명하지 않고 source gap으로 종료한다. terminal/전송 증거는 원 dedupe 저장소에서 그 신호의 재사용 가능기간 전체에 걸쳐 보존한다. restart 뒤 유효한 미전송 상태만 원 T0로 복원하며 시계 일관성을 입증하지 못하면 종료한다. 코드·정책 변경을 이유로 과거 pending 신호에 새 5초를 주지 않는다.

에피소드 두 leg는 매번 제출 직전 다시 판단한다. 첫 leg가 전송/체결된 뒤 두 번째가 악화·deadline으로 종료돼도 첫 leg를 취소/청산하거나 두 번째 수량을 합치지 않는다. 각 leg의 원 신호시각을 보존하고, 순회 시작시각을 새 T0로 쓰지 않는다. 이미 보유한 leg의 target/복구는 계속한다.

## 6. 구현 위치와 순서

| 작업 | 직접 수정/재사용 경로와 마지막 consumer | 종료 조건 |
| --- | --- | --- |
| 공통 계산/clock | `src/trading/market`의 새 순수 계산 모듈, 기존 confirmation kernel adapter | 같은 입력·cutoff의 runtime/offline metric/action/hash 일치; 기존 kernel 회귀 불변 |
| opt-in 정책 | `src/trading/config`의 새 loader 및 기존 timing resolver 호환 검사 | absent=비활성, 유효 승인된 baseline scope만 활성; malformed 활성 pin은 해당 신규 진입 fail-closed, silent OFF 금지 |
| 위젯 adapter | `src/trading/widget_auto_trade/engine.py`의 원 신호→제출 경로와 실제 gateway | scale-in 제외, WAIT/terminal/중복·원 EXIT 우선·전송 직전 veto 검증 |
| 에피소드 adapter | `src/trading/order/regular_two_leg_machine.py`의 `_consider_entry`/`_submit_planned_buys`와 각 gateway | 기존 PLANNED→NO_FILL helper로 정상 WAIT를 조기 terminal 처리하지 않음; 2×10주/leg별 보존 |
| 원천·receipt/집계 | 기존 signal/decision receipt 및 `src/engine/monitoring/machine_microstructure_attribution.py`의 선택적 adverse child | guard intake/미제출/전송 시작·order 연결 보존. 최종 executable 분모와 구분하고 full/partial/terminal/비용은 기존 lifecycle owner에 대사; 새 정기 producer/자동 정책 승격 없음 |
| 회귀·인계 | `src/tests`의 해당 owner/confirmation 테스트와 본 문서·기존 checklist owner | review/fix/재검증 후 finding 0; 선택 배포와 실제 PID는 별도 |

새 Python 파일은 `src/engine` root에 만들지 않는다. 구현 시 각 gateway 실제 호출 체인과 nearby tests를 먼저 다시 읽는다. 순서는 **순수 계산/상태 계약 → 양 owner 및 전송 직전 hook → 정책·receipt/직접 consumer → 통합 review/fix → 검증 코드 인계 → 승인된 canary 배포/가동**이다. 모든 항목을 소스만 추가한 완료가 아니라 마지막 consumer까지 검증한다.

1차는 기존 normalized WS 입력만 소비한다. 구현 중 Kiwoom parser/FID/REG/복구 또는 REST 요청·주문 전송 코드를 변경해야 한다면 [공식 API reference gate](../kiwoom-api-data-contract.md)를 먼저 적용하고 upstream revision/검토 파일/시각을 기록한다. 이 문서에 공식 wire contract 검증 완료를 가정하지 않는다.

## 7. 반드시 통과할 테스트

1. 악화 결합 참/각 조건 하나씩 거짓, 매도 속도 감소, bid 저점 회복, 최근 체결 없는 창, 매도잔량 감소만 있는 경우. 최근 체결 없는 창·알려지지 않은 aggressor·결측은 live 정상 0이나 `CONTINUE`로 처리되지 않는다.
2. 정확한 반창 경계·동일 timestamp 순서·중복·late/out-of-order·cross-route/epoch·truncation·stale 왼쪽 호가·cutoff 이후 자료 배제. 같은 원천의 runtime/offline 결과 일치.
3. 즉시 CONTINUE, 0초 악화→1/3초 회복, 마지막 5초 회복/악화/결손, 각 checkpoint+1,500ms 경계와 초과, 전체6,500ms 상한과 더 빠른 원 deadline, missed checkpoint·clock 역행·재시작.
4. 신호 소멸/새 ID/중복 payload·policy/source pin 변경·기존 fixed/dynamic 충돌. 기존 dynamic ADVERSE→REJECT와 source fallback 동작은 불변.
5. gateway quota/비동기 대기 중 악화·원 safety 변경·deadline 초과 시 전송0. 확정 미전송 예약만 해제; 실제 send/ambiguous 뒤 추가 submit0. 동시 wake에서도 단일 제출.
6. widget 최초 entry만 대상/scale-in 제외/EXIT 우선, episode 첫 leg 전송 뒤 두 번째 DEFER·SKIP, full/partial/cancel-recovery·다른 owner 수량 불변, 과거 보유 신규 편입0.
7. absent/유효/손상/만료/충돌 정책의 서로 다른 처리, 비대상 scope 불변, pin 철회 후 pending 종료·기존 주문 recovery 유지. 미래-date/전일 승인 재사용 거절.
8. receipt 분모 보존, 재시도와 새 신호 분리, 시세 touch의 가짜 fill 금지, 비용 null·partial/full·미성숙 label 분리, policy/code/source hash와 consumer 일치.

관련 pytest·compile·`git diff --check`, 문서/checklist parser를 실행하고 review finding을 수정한 뒤 재검증한다. 최초 설계 작성 당시 구현 테스트는 미실행이었으며, 후속 구현 결과는 [구현 리뷰 §6](../audit-reports/2026-09-10-entry-adverse-flow-implementation-review.md#6-검증과-실행-인계)를 따른다. 실체결·양수 EV는 코드 검증 테스트의 선행조건이 아니다.

## 8. 최초 가동과 철회

기본 OFF로 구현한 뒤, 검증된 코드/원천 공급/전송 직전 hook/권한·safety 회귀가 통과하면 **양수 EV나 새 실체결 표본을 미리 요구하지 않고 승인된 소규모 live canary로 평가**한다. 새 alpha를 shadow로 자동 등록하지 않는다. offline fixture/replay 검증은 실전 주문이나 shadow 승격이 아니다.

최초 활성화 manifest에는 최종 code commit/root, 새 contract/정책 hash, 정확한 owner/symbol/profile/venue/session, 허용 baseline 모드, effective date/기존 entry 배제, T0·checkpoint·처리상한·source-gap 정책, 기존 cap/수량/guard 및 rollback owner를 명시한다. 활성화 대상은 구현 후 exact-date 정책으로 확인하며 현재 문서에서 임의 종목·서비스를 골라 가동하지 않는다. 대상이 없으면 `no_compatible_scope`이지 강제 baseline 전환 사유가 아니다.

최초 canary는 승인된 한 scope에서 시작하고, **첫 5개 거래일을 초기 점검 구간**으로 제안한다. 이는 고정 가동 중단일·경제성 충분 표본·자동 확대 조건이 아니다. 지속/만료는 승인 manifest가 명시하며, 지속 승인인 경우 매일 새 승인을 요구하지 않는다. 5일 뒤 근거 부족이면 기존 owner에 미확정으로 남기고 자동 최적화/확대하지 않는다. 다음 실행일 체크리스트의 같은 lifecycle owner로 이관한다.

동일 entry stage의 signal/timing 변경을 겹치지 않는다. 독립 exit canary가 함께 있어야 한다면 stage·cohort·적용시각·rollback을 분리해 승인하고, 손익 비교에서 exit policy가 같은 표본끼리만 비교한다. 자연 entry 수를 만들려고 cap/quantity/cooldown을 늘리지 않는다.

배포는 [release routing](../runtime-release-routing.md)을 따른다. 선택 배포본 직접 patch 또는 전체 dirty workspace 배포 금지. 실제 machine manifest/drop-in과 검토 commit만 바꾸는 별도 승인된 배포 범위가 필요하며, main/장후 selector는 이번 변경 대상이 아니다. 서비스별 기존 주문/custody·진행 successor를 보존하고 새 PID의 root/commit·pin·첫 실제 source/decision receipt를 확인한다. unit 시작 성공이나 과거 PID receipt로 소비 완료를 주장하지 않는다.

중복 주문·owner/수량 오염·deadline 위반 제출·invalid source/정책의 허용·원 safety 우회는 즉시 신규 canary 진입 중지/철회 대상이다. 일시적 무표본은 장애가 아니며, source gap 급증과 참여 감소는 사유별로 운영 점검한다. 경제성 악화의 유지/철회 판단은 아래 §9의 동일 계약 비교로 수행한다. 새 수치형 자동 rollback threshold는 검증·승인 없이 발명하지 않는다.

철회 시 새 후보는 닫고 미제출 WAIT를 `SKIP_POLICY_REVOKED`로 종료한다. 그 신호를 원 baseline에 즉시 재투입하지 않는다. 이미 보낸 주문·모호한 응답·기존 보유는 원 reconciler/청산이 계속 처리한다. 상태 schema가 남아 있는 동안 이전 코드로 단순 되돌리거나 원장을 지우지 않는다. 기존 profit-stagnation의 지속 pin/기존 보유 제외·복구 계약도 유지한다.

## 9. 무엇이 맞았는지 판정하는 기록

각 신호의 `signal → checkpoint → 최종 pre-transport 검사 → submit/미제출 → broker receipt → full/partial fill → terminal/비용`을 연결한다. receipt에는 identity/T0/cutoff/실제 평가·전송시각/deadline, 원 정책·새 정책/code/source hash, source-quality 사유, 4개 판단값, 전후 상태·원 guard blocker, 최종 order/leg 및 consumer를 담는다. cutoff 이후 자료를 쓴 최신 veto는 별도 row로 남긴다.

기본 보존식은 `신규 대상 신호 = 대기 중 + 미제출 terminal + 전송 시작`이다. 전송 시작은 accepted/rejected/ambiguous를 나누고, accepted 뒤 full/partial/open/cancel을 별도 추적한다. 동일 신호 재검사·두 adapter 중복 투영을 신규 신호로 세지 않는다. episode는 leg 단위와 원 signal 단위의 분모를 따로 기록한다.

최우선 비교는 **비용 후 EV·순익/일**이며, 유효 참여/미제출 기회손실·fill quality·tail·자본점유·양수 terminal 빈도를 함께 본다. 체결 직후 손실을 초기 spread/비용과 이후 bid 하락으로 나누고, 단순 체결률·승률 상승만으로 성공 처리하지 않는다. 최초 기록은 체결 후1/3/5초의 유효 bid markout과 실제 lifecycle 비용 후 손익으로 제한하며, 긴 horizon이나 미관측 label을 활성화의 추가 gate로 만들지 않는다.

분모는 새 guard 적용 **이전 원 조건을 통과한 대상 신호/leg**에서 고정한다. source gap·악화 SKIP를 분모에서 삭제해 성과를 높이지 않는다. EV는 대상 신호당 비용 후 순손익과 체결 lifecycle당 값을 구분하며, 전자는 실제 미제출·무노출 terminal이 입증된 경우의 실제 손익0을 포함한다. 이것은 거래했다면 벌었을 CF 손익0이나 누락된 비용0이 아니다. 미성숙/비용 미대사 표본은 null·coverage로 남기고, 전체 EV가 완전 대사되지 않았으면 부분 관측 평균을 전체 EV로 표시하지 않는다.

비교는 clean baseline 이후 동일 owner/symbol/profile/venue/session·원 signal/exit/비용 계약의 baseline과 canary version window를 분리해 수행한다. 기존 chronological holdout/rolling 보고 경로를 사용하되 새 guard를 기존 timing 4군 연구의 완료된 arm으로 위장하지 않는다. 비무작위 전후 비교의 시장 국면 혼입을 명시하며, 거절 신호에 가상의 즉시 full-fill/실현손익을 만들지 않는다. 반등을 놓친 경우는 source-backed CF/기회 진단으로 분리한다.

비용·fill/exit 원천 결손은 null, partial/full과 미성숙/censored는 별도다. 유입0·교집합0은 그 직접 사유를 남기며 EV0·성공으로 바꾸지 않는다. 첫5일은 초기 판단 자료일 뿐 부족한 evidence를 자동 채우지 않는다. 결론은 `유지 / 철회 / 근거 부족`으로 기존 owner가 남기며, 자동 수량 확대·threshold 최적화는 하지 않는다.

## 10. 완료 상태와 문서 검증

후속 코드 범위: 위젯 최초 entry와 shared regular two-leg(midday/afternoon/low-price) adapter다. 별도 morning legacy owner는 미포함이다. 위젯 최초 owner 진입 확인 단계의 저장 시각과 episode의 기존 signal_decision_at을 T0로 사용한다. 새 receipt child는 흐름 진단이며 경제성 자체를 추정하지 않는다. 최초 배포/pin 설치는 별도 승인, 승인 후 pin 소비는 자동이며 최신 검증/잔여는 위 구현 리뷰를 따른다.

구분해서 닫는다: **문서 설계 → 코드/계약·테스트 → 검토 코드 배포 → 정책/PID 실제 소비 → 자연 동작 → 비용 후 경제성**. 앞 단계 완료를 뒤 단계 완료로 바꾸지 않는다.

최초 설계 작성 변경은 본 구현안과 기존 체크리스트 owner의 링크/잔여 조건뿐이었다. 당시 `korstockscan-review-gate`의 문서 모드로 감시 시계, baseline 신규 권한, 기존 dynamic 거절 보존, source gap, 전송 전/후 예약 경계, code/PID/경제성 상태와 링크·parser를 검토했다. 아래는 그 최초 문서 receipt이며 후속 코드 구현 리뷰/배포 상태와 구분한다.

- 문서 자체 리뷰/보완: 기존 checkpoint 지연과 새 전송 상한을 분리하고, 기존 WAIT 보존·최신 메모리 view·guard 이전 EV 분모를 보완했다. 재리뷰 범위는 본 설계/직접 owner 연결이며 미해결 finding 0; 거래 코드 리뷰 PASS가 아니다.
- print-only checklist parser: exit0, 28개 파싱, 현재 날짜 checklist 12개 중 후속 owner 정확히1개 확인. 로컬 링크7개 확인 및 `git diff --check` 통과. 최종 보완 후 parser/owner 유일성과 공백 검사를 재검증했다.
- 코드 구현·report 재생성·운영 정책/PID 변경·실주문·외부 Project/Calendar sync: 이번 요청에서 실행하지 않음.

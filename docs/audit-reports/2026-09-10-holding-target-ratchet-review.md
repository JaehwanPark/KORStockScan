# Holding AI 공통 호출·미체결 목표 1틱 상향 구현 리뷰

작성: 2026-09-10 KST. 개발 작업폴더 검증이며 배포/정책/PID/실주문 receipt가 아니다.

**최신 판정은 §9를 따른다.** §1~§7은 Holding AI 방식, §8은 목표 도달만으로 상향하던 개발 이력이다. 후속 사용자 지시로 AI를 제거하고 WS 압력 결합 조건 및 snapshot wake를 구현했다. 새 ratchet은 미배포이며, 이미 별도 배포된 profit-stagnation 기능의 결함/철회를 의미하지 않는다.

## 1. 판정과 구현 범위

기존 widget/episode owner의 목표 SELL이 **전량 미체결**이고, 실행 가능한 bid가 현재 목표에 도달했을 때 기존 Holding AI를 직접 호출한다. 정상 파싱된 live `HOLD + recovery|absorption`이면 현재 브로커 목표에서 **1틱만** 정정한다. 이후 같은 조건이면 정정이 확인된 새 주문을 대상으로 다음 1틱을 판단한다. 2틱 선택/grid, 별도 prompt/model/parser, 취소 후 재주문 fallback은 추가하지 않았다.

`target_ratchet.py`는 기존 `profit_stagnation_owners.py`의 실제 owner loop에 연결된다. 비동기 AI 대기 중 원 목표 주문과 기존 reconciliation은 유지한다. 실제 AMEND 직전에만 원 owner journal에 배타적 pending claim을 저장한다. 기존 adaptive exit 세션/진행 중 보조청산은 경쟁하지 않으며, widget 원래 final EXIT를 확인하지 못한 missing-payload 경로에서는 새 상향을 시작하지 않는다.

수정 파일의 역할:

- `src/trading/order/holding_target_review.py`: 기존 공통 context builder와 `GPTSniperEngine.evaluate_scalping_holding_flow()` 직접 호출, owner별 실제 position 입력, 비동기 1개 요청/서비스 및 기존 재검토 주기.
- `src/trading/order/target_ratchet.py`: 실제 owner loop 연결, 후보·최종 guard, 원장 projection 및 pending 복구.
- `src/trading/order/target_amend.py`: 기존 paging/pacing transport를 통한 dated/current 정정 대사.
- `src/trading/config/machine_target_ratchet_policy.py`: 별도 승인 pin 읽기. 기본 OFF, 일별 재승인/새 경제성 floor 없음.
- 기존 broker adapter/owner registry: `kt10002` 직접 정정, AMEND 예약과 단일 원자 commitment 이전. regular/widget owner는 pending 상태를 reload/date rollover/단일 writer 검사에서 보존한다.

## 2. Holding AI 재사용과 장후 튜닝

복사본이 아니라 기존 인스턴스 메서드를 호출 시점에 해석한다. 공통 prompt/input/model routing/parser가 이후 변경되고 해당 코드·승인 설정을 실제 process가 로딩하면 이 경로에도 반영된다. 같은 종목의 main 포지션 판단이나 결과 캐시를 가져오는 방식은 아니다. machine owner/position/order ID를 별도 전달한다.

공통 holding context의 `enabled`가 false일 때는 기존 방식대로 forensic/preflight 입력으로만 전달한다. 이 연결이 확장 prompt 입력을 임의 활성화하지 않는다. 기존 raw source/완료 분봉을 소비하며 없는 체결/비용/손익을 0으로 채우지 않는다.

**공통 함수 재사용과 장후 후보의 live 자동 승격은 별개다.** 장후 연구 report가 생기는 것만으로 미승인 holding 후보가 선택되거나 실행 중인 고정 release/PID가 reload되지는 않는다. 기존 승인된 holding 튜닝의 선택/소비 계약을 공유하며, main-only 경제성이나 미등록 machine cohort를 혼합 승인하지 않는다.

## 3. 자동 적용과 과도한 조건 검토

최초 운영은 별도 배포 세션이 검토 코드와 `KORSTOCKSCAN_MACHINE_TARGET_RATCHET_POLICY_PATH/SHA256`을 승인·설치해야 한다. 이 리뷰는 실제 pin/정책/env를 만들지 않았다. 기존 profit-stagnation pin으로 새 목표 상향이 켜지지 않는다.

정책은 `family=machine_holding_target_ratchet_v1`, `enabled`, timezone-aware `valid_from/valid_until`, `owners`, 실제 근거의 `round_trip_cost_pct/slippage_bps/cost_source_sha256`을 요구한다. 유효 기간 안의 승인 후 신규 진입만 대상이다. 원래 service loop에서 정책 확인→AI→가격/수량 최종검사→직접 정정→동일 날짜 내역 대사가 자동 실행된다. 각 정정마다 사람 승인 또는 장후 sample floor를 새로 요구하지 않는다.

리뷰에서 수정한 조건/결함:

1. 임의 5초 AI 결과 TTL은 기존 약 6초 episode polling과 맞지 않았다. 공통 Holding AI의 `next_review_sec` 30~90초를 사용하고, broker 조회/registry fsync 뒤에도 결과 만료를 다시 검사한다. 호가 2초 신선도와 exact 미체결 수량 검사는 유지한다.
2. 별개 leg의 BUY 완료를 현재 전량 미체결 목표의 추가 승인 조건으로 두지 않는다. 같은 target의 수량/owner 및 reconciliation 오류 차단은 유지한다.
3. 실제 broker 목표가격과 owner 가격 불일치 또는 dated/current 가격 충돌을 차단하고, broker adapter에서도 정확히 1틱 상향인지 검사한다.
4. AMEND ACK만으로 원 주문 commitment를 해제하지 않는다. confirmed parent/child의 수량 보존식과 현재 미체결을 확인한 뒤 hash-chain 원장 한 event로 이전한다. 기존 `canceled_qty` projection은 이전된 commitment 수량이며 실제 취소 API 실행으로 해석하지 않는다. `amended_to`와 정정 증거를 함께 보존한다.
5. 원장 AMEND에 BUY side가 들어갈 수 없도록 제한하고, 부분체결 ancestor는 다음 정정 대상에서 제외한다.
6. widget 원래 EXIT 우선순위, missing-source 신규 상향 차단, 정책 OFF 뒤 이미 시작한 pending 복구, thread/불명 ACK 중복 요청 차단을 검증했다.

1% 최소 수익, 5/10/20일 동시 floor, 최초 활성화 전 새 정정 실체결 또는 별도 AI score cutoff는 추가하지 않았다. 예상 비용·slippage 차감 후 현재 executable bid가 양수인 조건은 유지한다. 이 비용 추정 검사는 실제 broker 정산이나 AI 사용료 대사를 완료했다는 뜻이 아니다.

## 4. 브로커 경쟁과 지원 경계

공식 Kiwoom reference: `234560d213acd8871ae344b5481aecd2f30287fa`, 2026-09-10 19:32:07 KST 확인. `kiwoom/_data/kiwoom_api_spec.json`의 kt10002/kt00007/ka10075, `kiwoom/specs.py`, `kiwoom/core/client.py`, PRD/MOCK Postman을 대사했다. 해당 revision에는 `kiwoom_docs`가 없었다. 실제 API/Provider 호출은 하지 않았다.

이 API에는 "현재 filled=0일 때만 정정"하는 원자적 조건이 없다. 직전 검사 이후 체결 경쟁은 완전히 제거할 수 없다. 이미 확인된 부분체결은 정정하지 않고, 경쟁이 발생하면 추가 정정을 중단한다.

- 정상 ACK identity와 dated/current 증거가 있으면 재기동 또는 정책 OFF 뒤에도 원래 journal에서 대사를 재개한다.
- ACK identity가 없거나 충돌하면 자동 재주문/추정 adoption을 하지 않는다. `amendment_ack_identity_unresolved`로 원 주문·reservation·pending claim을 보존한다.
- parent가 정정 경쟁에서 부분체결된 경우 widget은 exact parent fill과 child 잔량을 분리한다. episode는 기존 leg 수량 계약을 자동 재작성하지 않고 `amendment_race_partial_fill_requires_exact_episode_recovery`로 남긴다. 비용/평균 체결가를 발명하지 않는다.
- 날짜를 넘긴 미완료 정정은 기존 owner의 exact-date 복구가 필요하다. 이를 일반 자동 적용 완료로 보고하지 않는다.

위 예외의 범용 자동 복구·실계좌 정정 정책 확장은 이번 최소 구현 범위 밖이다. 따라서 "모든 장애까지 무인 자동 복구" 또는 "부분체결 경쟁 불가능"을 주장하지 않는다.

## 5. 목적 적합성과 기대효과

상승 지속 판단이 맞고 추가 목표가 실제 체결되면 같은 수량에서 1틱의 추가 gross 수익을 얻을 가능성이 있다. 반대로 원 목표에서 끝났을 거래가 미체결/장기 보유로 바뀌거나 가격이 되돌아갈 수 있다. 따라서 이 기능 자체가 **작은 수익의 빈번한 실현**을 보장하지 않으며, 정체 보조청산과도 다른 축이다.

실효성은 같은 owner/진입/원 목표 대비 정정 여부·추가 체결대금·broker 비용·AI 사용료·총 순이익/일·양수 terminal 빈도·자본점유·불리한 tail로 구분한다. 1틱 상승 건수나 AI HOLD 빈도를 성공지표로 대신하지 않는다. 지금은 fake-wire 코드 검증뿐이며 실제 추가 순익/빈도 개선은 미관측이다.

## 6. 검증 및 인계

`korstockscan-review-gate`의 self-review→수정→재리뷰 뒤 **검토한 정상 경로/명시적 fail-closed 경계 안의 미해결 finding 0**이다. §4의 지원 밖 자동 복구를 구현 완료로 세지 않는다.

- 최종 targeted pytest: **457 passed, 4 skipped / 21.17초**. `test_holding_target_ratchet`, `test_profit_stagnation_exit`, `test_machine_adaptive_exit_broker`, `test_machine_adaptive_exit_owner_loop`, `test_machine_adaptive_exit_terminal`, `test_holding_decision_context`를 함께 실행했다. 이전 279/71/396/455 결과와 합산하지 않는다. 초기 테스트 fixture 연결 오류는 수정 후 같은 suite에서 해소했다.
- 신규 경로 검증: 1틱/두 번째 정정의 실제 owner 루프, ACK와 terminal 구분, 부분체결/경쟁, timeout 중복 금지, 정책 OFF/재시작, 원 EXIT/lock, broker 가격 불일치, BUY AMEND 거절, 공통 메서드 동적 호출, 공통 context OFF 보존, 6초 polling, 독립 leg 추가 floor 부재.
- 변경 Python compile 및 신규 파일 Ruff, `git diff --check` 통과. 운영 Provider/실계좌 호출은 실행하지 않았으며 wrapper/service 배포 테스트를 실제 PID 소비로 표현하지 않는다.
- 문서 print-only parser `--print-backlog-only --limit 500`은 exit 0, 28 tasks로 통과했다. 외부 Project/Calendar sync는 실행하지 않았다.

코드 검증, 다른 세션의 배포·pin·실제 PID 소비, 자연 source/주문 전환, 비용 후 경제성은 각각 별도 상태다.

현재 후속 owner는 [9/10 체크리스트](../checklists/2026-09-10-stage2-todo-checklist.md)의 `MachineLifecycleTurnoverObjectiveFollowup0910`이다. 이미 별도 배포된 profit-stagnation 273807e3의 다음날 acceptance를 이 새 ratchet의 배포 receipt로 재사용하지 않는다. 공통 release selector/cron/서비스/PID/운영 원장/정책·실주문·Provider·정기 report·외부 sync·commit/push는 이번에 변경/실행하지 않았다.

## 7. 목적·도달 가능성 재검토와 입력 계약 수리

2026-09-10 20:13 KST 재확인. 사용자의 권고 보완 지시에 따라 개발 adapter와 회귀 테스트를 수정했다. 선택 release·운영 정책·Provider·매매 process는 변경하지 않았다.

- **수리 완료 — 공통 route 계약:** adapter가 전달하던 `broker_order_route/execution_broker_route`는 실제 `_holding_execution_route`가 소비하지 않는다. KRX/NXT/SOR 모두 `missing`이 되는 반례를 확인하고 `entry_execution_broker_route`로 교체했다. 세 route와 context ON/OFF 조합에서 실제 route resolver를 호출하는 회귀를 추가했다. 잘못된 필드명을 고친 것이며 원천 freshness/owner 또는 승격 guard를 제거한 것이 아니다. 이 검사는 전체 live input preflight 성공을 대신하지 않는다.
- **안전 처리 검증 — 비동기 체결 경쟁:** 실제 `holding_target_review.review` thread를 Event로 제어하고, 가상 6초 뒤 원 target이 부분/전량 체결된 fake broker 상태를 전달했다. 뒤늦은 live HOLD가 반환돼도 AMEND/새 claim이 생기지 않는다. 기존 즉시 AI 응답 fixture만으로 시장 도달 가능성을 검증했다는 해석을 바로잡는다. 실제 Provider latency나 시장 체결 확률을 측정한 것은 아니다.
- **미해결 P1 — trigger 설계:** 전량 executable bid가 이미 원 목표 이상이고 원 target 전량 미체결인 상태에서 broker 조회→AI→다음 poll→재검사를 요구한다. 원 목표가 먼저 체결되는 정상 경로와 경쟁하므로 지속적 추가 수익 기회라고 입증할 수 없다. 미체결/호가 guard 완화가 해결책은 아니다. 원 목표 유지 우선으로 상향 제외 또는 목표 도달 전 판단 준비 중 전략 선택이 필요하며, 임의의 사전 호출 거리·새 threshold·정책 envelope를 만들지 않았다.
- **미해결 P2 — 증분경제성:** 현재 양수 net 조건은 원 entry 대비 가격·추정 거래비용 검사다. 원 목표 유지 대비 1틱 증분가치, AI 비용, 미체결/자본시간 증가를 판정하지 않는다. 이를 추가 수익이나 빈번한 양수 terminal 개선으로 보고하지 않는다. 기능을 유지한다면 기존 owner별 원 목표 대조와 실제 비용/결측·partial/terminal 구분이 필요하다. 별도 대규모 연구나 새 경제성 gate를 구현하지 않았다.
- **자동화 경계:** 조건부 owner loop와 정책 reader는 있으나 ratchet 전용 정책 발행/장후 튜닝 승격/선택 release 갱신 경로를 확인하지 못했다. 공통 Holding AI 메서드 재사용은 유지되지만 장후 holding 후보의 자동 live 승격을 뜻하지 않는다. 현재 widget PID1138215의 WorkingDirectory는 기존 machine-profit-stagnation-20260911이며 새 ratchet 적용 증거가 아니다. 전략 선택과 별도 배포 승인 전 활성화하지 않는다.

이번 입력 수리와 체결 경쟁 테스트는 해당 코드 계약으로 닫는다. 기능 전체는 `design_decision_pending / deployment_pending`이며 finding 0이 아니다. 전략 제외/재설계 결정을 요청했고, 기존 checklist owner를 유지한다. 기존 주문·수량·비용·정체 보조청산을 바꾸지 않는다.

검증: `test_holding_target_ratchet` 단독 46 PASS, 실제 thread 회귀 보완 후 §6과 같은 6개 suite 통합 **465 PASS / 4 SKIP, 21.52초**. 두 수치를 합산하지 않는다. Python compile·수정 파일 Ruff·`git diff --check` 통과. print-only parser 28 tasks, 현재 checklist의 `MachineLifecycleTurnoverObjectiveFollowup0910` 1건 확인. Provider/실계좌 호출·경제성 report 재생성·외부 sync·배포는 실행하지 않았다. 잔여 P1/P2를 테스트 통과로 완료 처리하지 않는다.

## 8. 사용자 결정 후 WS 상향 전환과 남은 수신 지연 경계

2026-09-10 후속 사용자 결정: Holding AI를 기다리지 않고 WS 목표 도달로 직접 정정하며, 상향 횟수의 전략 상한을 두지 않는다. 이 결정으로 §7의 AI 유지/제외 선택 대기는 해소됐다. 각 단계 +1틱, 같은 원 주문 소유자·수량·기존 EXIT 우선순위는 유지한다. 이후 사용자의 체결속도/매도잔량/감소속도 활용 질문은 설계 검토이며 추가 live 조건 변경 지시로 해석하지 않았다.

- 개발 코드: `target_ratchet.py`에서 Holding AI 호출·결과/TTL gate·중복 preflight를 제거했다. 기존 WS 기반 전량 executable bid가 목표 이상이고 원 비용 조건을 통과하면 같은 owner 평가 회차에서 adapter로 전달한다. trigger 시각/quote ID·epoch·가격을 pending에 보존한다. 원 adapter의 한 번의 exact broker preflight, 예약 전후 freshness/owner/정책 guard는 유지한다.
- 불필요해진 기능 전용 `holding_target_review.py`와 해당 AI 전용 테스트는 제거했다. 공통 Holding AI 엔진/다른 owner의 AI는 제거하지 않았다. 새 family는 `machine_ws_target_ratchet_v1`이며 옛 AI family pin은 거절한다. 운영 정책을 발행하거나 기존 pin을 수정하지 않았다.
- 무제한의 의미: 정정 확인된 최신 child가 다시 목표 조건을 만족할 때 +1틱을 계속 평가한다. 전략 횟수 cap은 없지만 원 주문 한 개에 동시에 하나만 전송한다. 브로커 가격 범위·호가단위·공유 호출 한도·단일 writer는 무제한이 아니다.
- 오류: 명시적 broker rejection은 해당 original order의 추가 상향을 중단하고 기존 주문 대사를 유지한다. 거절을 체결로 기록하지 않는다. timeout/HTTP429·5xx/불완전 또는 충돌 ACK는 pending/원장 증거를 유지하고 재전송하지 않는다. 기존 부분체결 경쟁과 익일 exact recovery 경계는 §4대로 남는다.
- **즉시성 미완료:** 현재 입력은 WS raw callback이 아니라 공유 snapshot을 기존 owner loop가 읽는 방식이다. widget 기본1초, episode 기본2초/일부 설치6초의 poll 및 broker guard 지연이 남는다. 이번 보완은 AI 대기를 없앤 것이며 raw WS 수신 즉시 전송/체결 경쟁 승리를 구현·검증한 것은 아니다. 원 owner로의 event wake/직전 신호 준비와 실제 수신→판단→전송 지연 검증은 기존 아래 owner에서 이어질 설계 항목이다. API polling 증가나 경쟁 주문 writer로 우회하지 않았다.
- 기대효과: 상향 기능의 추가 Holding AI 호출/대기가 없어지고 사전 broker snapshot이 두 번에서 한 번으로 줄었다. 실제 1틱 추가 체결·순익/빈도 증가는 미관측이다. 목표를 계속 옮겨 미체결/자본점유가 늘거나 되돌림을 맞을 수 있으므로 작은 수익의 빈번한 실현으로 단정하지 않는다. 추가 경제성 연구/실체결을 코드 수리 통과 gate로 붙이지 않는다.

공식 API gate 재확인: `2026-09-10T20:29:24+09:00`, remote HEAD와 로컬 공식 checkout 모두 `234560d213acd8871ae344b5481aecd2f30287fa`. `kiwoom/specs.py`, `kiwoom/core/client.py`, packaged `kt10002/kt00007/ka10075` 전 request/response, PRD/MOCK Postman을 읽었다. `kiwoom_docs` 부재, endpoint/양수 수량/원 주문·새 ACK identity/continuation 계약 불변. 실계좌/Provider 호출은 없다.

검증: 변경 후 ratchet 48 PASS, §6과 같은 6개 suite 통합 **467 PASS / 4 SKIP, 23.42초**. 단일 preflight, Holding AI 호출0, 목표 미달, 12단계 연속 상향, 거절 후 중단/체결 미합성, 모호한 응답 재전송 금지, fsync 뒤 source 손실 차단, 옛 정책의 새 전략 활성화 거절을 추가했다. 이후 최종 lint/compile/parser 결과는 아래에 별도로 기록한다. 이 결과를 raw WS event 구동 전체 finding0·배포·실수익 완료로 확대하지 않는다.

현재 owner는 `MachineLifecycleTurnoverObjectiveFollowup0910`이며 `WS snapshot decision_code_verified / event_wake_not_implemented / deployment_pending / economics_unobserved`를 분리한다. 최신 질문의 체결속도·고정 가격 잔량 감소·실제 BUY 설명·refill·bid 지지 결합은 기존 공통 계산의 재사용 가능성만 검토한다. entry용 4군 연구를 exit 상향 효과나 선정 threshold의 검증으로 전용하지 않는다.

최종 검증 보완: AI 전용 테스트 제거 뒤 남은 미사용 import 한 건을 제거했다. 변경 Python compile, 대상 Ruff, `git diff --check`, print-only parser(28 tasks, 현재 owner 1건)를 재확인했다. 제거한 AI 전용 adapter는 이 개발 변경의 폐기 대상이며 별도 배포본/공통 Holding AI 코드는 보존했다. 외부 sync는 실행하지 않았다.

## 9. WS 압력 결합 상향 구현과 목적 적합성

2026-09-10 21:03 KST 개발 검토. 사용자가 권장 설계의 구현·반복 리뷰·과도한 적용 조건 및 작은 비용 후 수익/회전 목적 점검을 명시했다. §8의 추가 조건 설계 대기는 이 지시로 대체됐다. 실제 배포·재기동·운영 정책/env 변경은 별도이며 이번에 실행하지 않았다.

### 구현 계약

- 위치 gate: 순수 시장데이터 판단은 기존 역할 패키지 `src/trading/market/target_pressure.py`, 실행은 기존 `target_ratchet.py`/widget/episode owner, 테스트는 `src/tests/test_target_pressure.py`와 기존 ratchet suite에 둔다. 새 engine-root producer/정기 연구/별도 주문 writer를 만들지 않는다.
- `machine_target_pressure_v1`: 호출 시점 이전의 닫힌 1초 창을 공유 `machine_confirmation_fixed_price_window_v1`로 계산한다. 목표 도달 후 새 1초를 기다리지 않는다. 앞/뒤 0.5초 실제 BUY 수량/초, BUY/SELL 우세, 동일 시작 ask의 감소속도·그 최소점 이전 실제 BUY 설명·이후 refill, bid 지지와 다음 목표까지의 표시 매도잔량을 함께 소비한다. entry용 kernel이나 entry 승격 조건 자체는 바꾸지 않는다.
- 초기 해석 가능한 조건: 최근 BUY 속도 양수·직전 반초 이상, BUY 수량>SELL, 감소속도 양수, 실제 BUY 설명비율>설명되지 않은 감소비율, refill<감소량의 절반, endpoint bid>=시작 bid, 관측 중 ask 하향 없음, 다음 목표까지 표시 잔량+내 수량<=최근 BUY 속도의 1초 상당량. 현재 목표의 전량 executable bid·비용/slippage 후 양수 조건은 기존대로 유지한다. 이 기준은 사용자 위임에 따른 초기 휴리스틱이며 최적 threshold·교환소 전체 주문흐름·체결확률 모델로 검증된 값이 아니다.
- 해당 조건을 모두 통과할 때만 **현재 목표 +1틱**, 아니면 **현재 목표 유지**다. 횟수 cap은 없지만 정정 확인된 최신 child에서만 다음 단계가 가능하다. 약세 시 추가 상향을 멈추는 것이며 이미 높인 목표를 자동 하향하거나 새 trailing/손절을 추가하지 않는다. 기존 profit-stagnation 및 원 final EXIT의 별도 계약은 유지한다.
- 원 snapshot 한 세대에서 압력과 전량 bid를 계산한다. receipt/epoch/sequence/시각·1초 왼쪽 경계·UNKNOWN·truncation·필요한 다음 가격대 결손은 상향을 차단하고 원 목표/대사를 유지한다. 120행이 항상 1초를 담는다고 가정하지 않는다. duplicate trade는 수량에서 중복 제거하고 미래 행을 제외한다. local projection continuity를 exchange completeness로 확대하지 않는다.
- 비용 판정은 원 entry 대비 추정 순이익이며, 상향 자체의 증분 EV가 아니다. 유지 사유·feature/version/hash·quote 및 최초/최종 guard 압력 판정을 기록한다. `prewrite_pressure`는 최종 guard 관측이며 실제 wire-send timestamp가 아니다. process crash 직전 메모리 변경까지 저장됐다고 보장하지 않는다. 모호한 전송 결과는 기존 durable AMEND 원장으로 복구한다.

### 반복 리뷰에서 보완한 결함과 지연

1. 목표 도달만으로 무조건 상향하던 경로를 압력 조건으로 교체했다. 재보충/취소성 감소/매수세 둔화/큰 다음 잔량의 유지 반례를 추가했다.
2. 초기 판단 후 broker preflight·원장 fsync 사이 압력 변화가 있으면 전송 직전 재계산으로 차단한다. 명시적 거절 후 중단, 불명 응답 재전송 금지, 원 주문/수량 보존 및 정책 OFF 뒤 pending 복구는 그대로다.
3. snapshot JSON이 배열일 때 loader가 `.get`에서 예외를 내던 결함을 수정했다. NaN/무한/boolean receipt 시각·epoch, duplicate volume, source 실패 후 이전 RAISE 진단이 남는 문제도 회귀로 보완했다.
4. `wait_for_pressure`가 기존 sleep 안에서 **50ms 간격으로 로컬 파일 stat만 확인**, 새 snapshot에서 유효 후보가 있을 때만 동일 owner loop를 일찍 깨운다. probe는 원장/주문 상태를 변경하거나 API를 호출하지 않는다. 원 owner가 다시 source final EXIT·정책·수량·계좌/guard를 검사한다. 약한/없는 원천, pending 복구 또는 정책 OFF에서는 기존 cadence를 유지한다. 실제 서비스 loop의 wait 연결도 테스트한다.
5. publisher는 기존 `_maybe_write_dashboard_snapshot`의 비동기/단일 writer와 기본1초 발행 간격을 유지한다. 따라서 raw WS callback 즉시 전송이 아니라 **snapshot 도착 기반 조기 wake**다. 50ms는 로컬 stat 확인 주기이지 end-to-end SLA가 아니다. publisher/I/O·owner 실행 중 작업·broker preflight 지연과 원 목표 선체결 경쟁은 남는다. 구독/REST retry/공유 quota·동시성·원래 broker safety를 변경하지 않았다.

### 자동 적용 및 과도한 gate 판정

| 단계 | 현재 코드/운영 상태 |
| --- | --- |
| source→압력→원 owner 정정→확인 | 검토 코드와 유효 pin이 로딩된 뒤 기존 loop에서 자동. 매 목표마다 AI/사람 승인을 요구하지 않음 |
| 전략 pin | 기존 `machine_ws_target_ratchet_v1`에 필수 `decision_contract=machine_target_pressure_v1` 추가. 이전 무조건 상향 pin을 새 전략으로 조용히 재사용하지 않음. 이미 pending인 이전 계약의 receipt 복구는 보존 |
| 최초 발행·배포·PID | ratchet용 자동 정책 publisher/PREOPEN 승격/선택 release 교체는 현재 경로에 없음. 이번에는 개발 코드만 변경했으며 실제 활성화되지 않음 |
| 기존 최소 보조청산 | 조회한 manifest는273807e3 / machine-profit-stagnation-20260911 /9월11일 신규 entry부터 지속 정책. 이것을 새 ratchet의 배포/자연 소비 receipt로 사용하지 않음 |

일별 재승인, 새 AMEND 실체결을 최초 활성화의 선행조건으로 요구하는 순환, 5/10/20일 동시 floor, 1% 최소 이익, 별도 Holding AI cutoff를 추가하지 않았다. 비용 후 양수·정확한 owner/미체결 수량·fresh source·하나의 outstanding AMEND·기존 EXIT 우선은 주문 안전/이번 전략 정의에 필요한 조건이다. source 부족 시 **원 매도를 막지 않고 상향만 생략**하므로 표본 생성을 위해 guard를 낮추지 않는다. 1초/반초 비교·절반 refill/1초 wall 소화 기준의 경제적 적정성은 아직 미측정이며 과도하지 않다고 실증 확정하지 않는다.

### 기대효과와 미확인 효과

확인한 코드 효과는 Holding AI 호출/대기0, 한 번의 broker preflight, 강한 압력에서만 +1틱, 약한 경우 원 목표 유지, 새 snapshot 후보에서 긴 owner sleep 단축이다. 목적은 모든 목표를 도망가게 하는 것이 아니라 작은 원 수익을 기본으로 유지하고 제한적인 추가 가격을 시도하는 것이다. 같은 수량이 양쪽 모두 완전 체결됐다는 가정에서만 `1틱×수량`이 추가 매출이며, 10원 tick/10주 예시는100원 **추가 총매출**이지 기대 순이익100원이 아니다. 추가 비용·미체결·되돌림·자본점유의 영향을 빼야 한다.

실전 순익/일, 비용 후 EV, 양수 terminal 빈도, full/partial fill, 체결까지 시간, tail 및 자본시간이 기존 목표 유지보다 개선됐다는 증거는 없다. 새 pressure receipt는 원천/판단 증거이며 경제성 report나 실체결로 세지 않는다. 기존 entry 4군 연구도 exit 승격 증거로 전용하지 않는다. 시장가 체결·지정가 공급·취소를 구분해야 한다는 [주문흐름 연구](https://arxiv.org/abs/0904.0900)는 설계 배경일 뿐 이 초기 조건이나 한국시장 실전 수익성의 검증이 아니다.

공식 gate: 20:53:02 KST remote HEAD 재조회는 기존 공식 checkout과 같은 `234560d213acd8871ae344b5481aecd2f30287fa`. §8에서 읽은 packaged kt10002/kt00007/ka10075·specs/core·Postman 계약을 유지하며 새 request/parser/FID/구독을 만들지 않았다. `kiwoom_docs` 부재는 그대로다. 실제 계좌/Provider/API는 호출하지 않았다.

검증은 아래 최종 결과로 닫는다. 코드 리뷰, 최초 배포/정책 공급, 실제 snapshot/PID 소비·수신→정정 지연, 경제성은 독립 상태다. 자연 acceptance는 기존 `MachineLifecycleTurnoverObjectiveFollowup0910`에서 원 목표 유지 대비 같은 owner/정책·기간·비용의 결과로 확인하며 기존 최소 보조청산 다음날 기동 owner와 합치지 않는다.

최종 검증: `korstockscan-review-gate`로 원천→loader→압력→실제 owner loop→broker guard/정정 대사와 기존 소비자를 재검토했다. 최종 통합12개 suite **792 PASS / 4 기존 owner 비대상 SKIP, 29.99초**. 최초 통합에서 제거된 `time_module.sleep`에 묶인 기존 terminal-manager 테스트1건이 실패하여 새 실제 `wait_for_pressure` 경계를 검사하도록 수정하고 전체를 다시 통과했다. 이 회귀는 BLOCKED라도 미보호 manager를 종료하지 않는 기존 assertion을 유지한다. 원천/owner 통합, 비용/최종 guard, 약한 신호 유지, source 붕괴·NaN·future·중복, 정책 세대, snapshot wake의 무API/무변경과 실제 loop 연결, 기존 거절/모호한 ACK/12단계 무상한·수량·EXIT 회귀를 포함한다.

대상 Python Ruff·compile 및 `git diff --check` 통과, print-only parser28 tasks/현재 owner1건. 검토 범위의 unresolved 코드 finding0이며 경제성 또는 실전 전달 SLA finding0을 뜻하지 않는다. 선택된 별도 machine root의 실제 HEAD는273807e3767bc92cd89cd0394e8aa374679795c6이며 HEAD tree에 새 ratchet/pressure 모듈이 없음을 읽기 전용 확인했다. 따라서 새 기능의 `selected_release_updated=false / actual_pid_consumed=not_verified / economics=unobserved`다. 운영 원장/정책/PID/공통 selector·cron/패키지·실주문/Provider/외부 sync는 변경하지 않았다.

검토 코드 SHA256: pressure `f0c7cfcc25263ebad88167b26d3c3c19f1c1fb66ef42b25271e4cd08566d0bb1`, ratchet `5a88026605c3ba06bf3c788b5a98799b895c353ef839f5aa207b4c81fa706a18`, policy `61c1e9d63311cb1de24398e06fa23a00ebf2e0561b4584e8dc2c4d3f90e36e8f`. 이 해시는 개발 파일 증거이며 검토된 배포 commit이나 runtime pin으로 대신 사용하지 않는다.

21:07:46 종료 점검: 검증 관련9개 코드/테스트 파일 SHA256 불변, 최종 Ruff/compile/diff 검사 및 parser28/owner1 재확인. systemd 조회의 widget MainPID1138215/ActiveState=active/WorkingDirectory=기존 machine-profit-stagnation-20260911이며 새 PID 기동 또는 ratchet 소비 증거가 아니다. source→wire 실제 지연은 측정하지 않았다.

## Subsequent approved deployment — 2026-09-10 23:53 KST

The user explicitly authorized deployment and all existing widget/episode scopes. The [final review and deployment receipt](2026-09-10-approved-additions-deployment.md) supersedes earlier deployment-pending or single-scope statements in this historical review. Frozen code f9d53a9a, widget PID2651657, all nine service/preflight paths and policy pins are verified. New signals/entries from September11 are eligible; actual transitions and economics remain separate natural acceptance.

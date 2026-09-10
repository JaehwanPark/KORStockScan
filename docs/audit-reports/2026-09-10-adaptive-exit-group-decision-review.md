# 적응형 청산 group 판단 receipt 후속 구현

현행 범위는 **§30 최소안 → §31 공통 계산 → §32 실제 owner/service 연결 → §33 관찰 비차단 재검토**다. §1~§29는 이전 설계/검증 이력이며 전체 adaptive family 활성화 개발을 재개하는 목록이 아니다. 기계의1% 유지 제약 변경은 사용자 결정 위임으로 해결됐다. 최소 보조청산의 실제 owner·정책 로딩·서비스 잠금·원 목표 복구를 구현했다. 배포·재기동·운영 설정은 다른 세션이며 실거래 활성화/경제성 완료를 주장하지 않는다.

작성: `2026-09-10 KST`. 직전 [9/9 리뷰 §16](2026-09-09-widget-episode-adaptive-exit-all-scope-review.md#16-group-부분취소와-첫-runner-sellttl-연결)의 다음 액션 중 **취소 전 group 판단→저장된 최신 receipt→기존 첫 부분취소 consumer**를 구현했다. 선택된 장중 지시문을 전체 모니터링·실주문·재기동 지시로 확대하지 않았다.

## 1. 판정과 구현 경계

`PARTIAL_ALL_SCOPE_IMPLEMENTATION` 유지. 이번 pre-release 판단/증거 연결은 코드·격리 fixture 검증 범위다. **실제 launcher·numeric envelope·독립 승인 validator·PREOPEN publisher/enrollment가 없고 적응형 청산은 이번 작업으로 활성화되지 않았다.** whole-target 및 부분취소 이후의 실제 trailing 판단/재무장·SELL 가격 결정, 잔량 복구와 group 전체 종료/기존 owner handoff는 별도 미완료다.

위치 gate에 따라 공통 주문 owner 패키지의 [group_decision.py](../../src/trading/order/adaptive_exit/group_decision.py), 기존 [group_execution.py](../../src/trading/order/adaptive_exit/group_execution.py), [전용 테스트](../../src/tests/test_machine_adaptive_exit_group_decision.py)에 변경을 한정했다. 새 engine-root 모듈·정기 report producer·주문 daemon·서비스를 추가하지 않았다. 원 `decision.evaluate_exit`와 broker request/parser는 변경하지 않았다.

## 2. 구현·직접 consumer·재리뷰

1. `evaluate_group_exit`는 동결 group/명시적 allocation·내용 hash 검증 정책, open BOOK lot 전수, 원 first-fill **관측시각**·가격/수량/position epoch·cost hash와 같은 시장 snapshot을 결속한다. 기존 lot별 시간진행/빠른 접근 trailing 판정을 재사용하며 target·수량·수익률/시간 임계값 기본값을 새로 만들지 않는다. 누락 lot·다른 owner/route/session·정책/가격/cost 변경은 차단한다.
2. runner들은 선언된 `allocation.lot_order`에 따라 같은 bid depth를 **한 번만** 나누어 평가한다(`runner_depth_once_in_declared_lot_order_v1`). 사용하지 않은 마지막 호가도 invalid/crossed/nonpositive이면 차단한다. nonrunner는 별도의 target 유지 진단이며 이 값을 runner와 더해 group 체결 EV로 쓰지 않는다. 이 depth 순서도 최초 독립 승인/정책 연결 시 검증할 계산 계약이지 현재 승인값이 아니다. BOOK 배분을 실제 broker BUY-lot 매도 귀속으로 바꾸지 않는다.
3. open runner 전부가 동일한 `REQUEST_TRAIL_ARM` 또는 `REQUEST_EARLY_EXIT`이고 nonrunner 목표잔량이 유지될 때만 `REQUEST_RUNNER_RELEASE` intent를 만든다. 일부 runner만 요청하거나 다른 요청이 섞이거나 전체 target 청산이 필요하면 `UNSUPPORTED_GROUP_EXIT_REQUIRES_OWNER_RECOVERY`다. 정상 KEEP나 무기한 표본 대기로 숨기지 않고 별도 실행 분기가 필요함을 전달한다. 이 pre-release 판단으로 trailing high-water/stop/활성 상태를 만들지 않는다.
4. `GroupDecisionBook`은 원 owner의 동일 잠금/atomic CAS 저장 아래 최신 판단과 상태를 보존한다. 새 평가 전에 pending veto를 저장하고, malformed 입력/평가 실패는 이전 release를 최신 성공으로 남기지 않는다. 한 lot라도 source gap/recovery이면 모든 lot의 이전 수용 상태를 유지한다. 한 번의 시간 연장은 재시작 후 초기화하지 않는다. 저장 전/후 실패·무저장 callback은 호출을 실패시키고 같은 객체의 실행을 차단한다. 저장 이전 실패의 미기록 외부 원천까지 복원할 수 있다는 주장은 하지 않으며, 재시작 후에도 독립 validator의 실제 최신 원천 검사가 필수다.
5. executor의 opt-in `decision_policy`가 book을 정확히 같은 coordinator에 결속한다. `request_decided_release`는 저장 receipt를 재계산하여 기존 `GroupAction`/부분취소 경로로 넘긴다. 정책 내용/배분/수량/동결 source·최신 veto·receipt 변조를 검사하며 **원장 예약 전과 예약 후 전송 직전**에도 최신 book과 실제 호가 age를 다시 읽는다. 재리뷰에서 판단 자체는 아직 young이어도 원장 저장 대기 중 원 호가가 stale해지는 반례를 보완했다. mandatory `authorize_action`의 독립 numeric/시장/계좌/수량/manual/operator/broker safety 검사는 그대로다. hash·파일 존재·source-only flag를 실주문 승인으로 대체하지 않는다.
6. 실행 action 슬롯 생성 뒤에는 book을 새 판단으로 덮지 않는다. 같은 immutable action의 ACK 회복은 시세 만료 뒤에도 읽기 전용으로 가능하지만 새 취소를 재전송하지 않는다. 외부 cancel의 사후 채택, book 교체/정책 변경, 이전 receipt 재사용은 차단한다. 첫 SELL/TTL·runner terminal은 기존 §16 consumer를 유지하며 runner 종료를 group flat·수익 완료로 바꾸지 않는다.
7. 마지막 재리뷰에서는 최초 invalid 비용 입력을 아직 수용하지 않았는데도 고정하여 이후 정상 원천 회복을 막는 반례를 수정했다. group 전체의 최초 유효 판단 전에는 검증된 position/cost 원천으로 보완할 수 있고, 최초 수용 후에는 같은 epoch의 비용·position을 조용히 바꾸지 못한다. immutable group의 원 BUY 수량/가격·첫 관측시각은 어느 경우에도 변경하지 않는다. 전용 회귀로 첫 gap→재시작→정상 판단→수용 후 변경 차단을 확인했다.

## 3. 공식 API 대사와 변경하지 않은 영역

공식 `Kiwoom-Securities/Kiwoom-REST-API`를 `2026-09-10T07:40:53+09:00`에 다시 취득했다. SHA `234560d213acd8871ae344b5481aecd2f30287fa`; `kiwoom_docs`는 이 revision에 없다. `kiwoom/specs.py`, `kiwoom/core/client.py`, packaged `kt10003/kt00007/ka10075`와 Postman production/demo envelope를 대사했다. 기존 positive exact `cncl_qty`, dated/current account proof·원 target reservation 계약을 재사용한다. query 예시를 별도 wire 계약으로 적용하지 않고 JSON POST·header/continuation 및 원 parser를 유지했다. upstream 예시나 실제 API는 실행하지 않았다.

실제 주문/취소·운영 registry/custody·policy/env/lock·PID/재기동·cron/systemd·report 재생성·Project/Calendar sync·commit/push는 실행하지 않았다. `machine_adaptive_exit_source`의 `live_partial_cancel_supported=false`, `current_target_epoch_verified=false`와 연구 exclusion을 유지했다. 새 모듈은 opt-in executor와 테스트에서만 참조하며 실제 owner loop/launcher가 생성하지 않는다. main submit drought·Entry AI·위젯 신호/target·기존 episode 수량/보호 계약도 변경하지 않았다. 병행 사용자/자동 생성 변경은 보존했다.

## 4. 검증 receipt

최종 receipt `2026-09-10T08:02:47+09:00`: 전체 영향 회귀 **1811 PASS / 4 owner-비대상 SKIP / 52.97초**. 신규 전용72개와 기존 group 실행기62개의 별도 검증은 **134 PASS / 7.41초**이며 전체에 포함되므로 합산하지 않는다. 4 SKIP은 widget catalog/episode terminal loop 및 episode manager/widget daily cap의 비대상 owner 조합이다. 전체 범위는 adaptive-exit producer/replay/decision/driver/broker/registry/owner-loop/terminal, attribution/approval, widget/low-price/Samsung 4경로 및 preflight, owner coexistence, 다음 체크리스트 builder다.

Ruff lint·Black check·compile·`git diff --check`·로컬 링크5개·print-only parser 통과. parser30개 중 현재 `MachineLifecycleTurnoverObjectiveFollowup0910`은1개다. 중간 테스트의 예상 예외를 독립 승인 거절(`PermissionError`)과 신규 stale 차단(`ValueError`)으로 구분해 수정했고 실제 guard를 완화하지 않았다. `korstockscan-review-gate`로 producer→동결 저장/재시작→선택적 executor→기존 adapter/registry와 미연결 실제 consumer 경계를 반복 리뷰/보완하여 **이번 pre-release 판단·증거 연결 범위 미해결 finding0**이다. 전체 exit 구현·배포·자연 소비·경제성 완료는 아니다.

검증 코드 SHA256:

- `group_decision.py`: `c89650f9a05a41c9e66be151726e63c7e6ddc5540d6ec8c5be15f370871efafc`
- `group_execution.py`: `e48b4784bcff9d1bcfe6917d5388de16e8a685456d1dcfa0765be7d89f10b487`
- 직접 broker consumer: `6adfe6762adc4dc83c84036215d58d0ca0809fda356e0541aa0297659fffe890`. 병행 `d34bfffe` 커밋의 조건식 괄호/포맷 변경을 읽고 보존한 현재 파일에서 재검증했다. 이 hash나 test PASS를 현재 PID/운영 반영 receipt로 쓰지 않는다.

## 5. 다음 액션과 현재 owner

다음 구현은 **부분취소 후 fresh depth의 실제 trailing arm/추적·SELL 판단, whole-target 전량 분기, TTL 후 residual/일부확인·거절 복구 및 group 전체 수량 terminal→기존 owner handoff**다. pending BUY 취소/late fill·legacy/force-flat·미해결 전일 복구도 기존 미완료 경계로 유지한다. 정확한 broker 주문별 금액/비용 source gap은 null/직접 사유로 남기며 별도 경제성 대기 gate를 다음 진입에 추가하지 않는다. 작은 비용 후 수익 빈도·누적 순이익·자본 회전 개선은 아직 미측정이다.

9/9 `MachineLifecycleTurnoverObjectiveFollowup0909`는 이전 구현/acceptance 이력이다. 현재 [9/10 checklist](../checklists/2026-09-10-stage2-todo-checklist.md)의 **기존 생성 ID `MachineLifecycleTurnoverObjectiveFollowup0910`**에 후속을 연결했다. 오늘 `21:30~21:40 POSTCLOSE` 확인은 예정 전이며 이 아침 코드 검증으로 해당 자연 점검을 완료 처리하지 않는다. checklist 자체는 source-only 권한이고 별도 구현 지시나 실제 최초 활성화 승인을 대신하지 않는다. 새로운 중복 OPEN ID를 만들지 않았다.

## 6. 전체 종료·전체 활성화 요청의 선행조건 확인

`2026-09-10 08:07:33 KST` 사용자가 전체 종료 연결 및 전체 활성화 단계까지 계속 진행하도록 요청했다. 요청 범위는 확대됐지만 최초 운용 수치가 제시되거나 승인된 artifact가 생성된 것은 아니다. 이번 추가 확인에서는 코드·운영 상태를 변경하지 않았으며, 위§4의1811 PASS는 이전 pre-release 범위의 검증이다. 이를 새 전체 종료/활성화 범위의 PASS로 재사용하지 않는다.

- `data/config`, `data/runtime`를 ignored 파일까지 포함해 확인했으나 adaptive-exit approval/envelope/applied policy 파일은 없었다. 현재 공통 trusted runtime registry에도 새 exit family가 등록되어 있지 않고 실제 service launcher의 `OwnerLoopServices` 공급은 없다. §5의 전체 target/잔량/종료 handoff 미구현을 단순 표본 대기로 숨기지 않는다.
- 읽기 전용 source9/9 attribution JSON SHA256은 `b5068924d29491da163a469da05b8634b1528ee5249723012e103d13999e1db5`다. `rolling_policy_research_v2`는 `schema=machine_adaptive_exit_source_census_v1`, `status=blocked_source_contract`, 원천30행·승격 후보0, `economic_acceptance=not_evaluated`, `net_ev_pct=null`; 최초 fill/lot epoch와 ordered post-target path 결속이 next action이다. 연구 원천 행을 경제성 pair나 실제 청산 표본으로 세지 않는다. `eligible_for_next_preopen=false`, 실제 adapter/consumer 미연결도 유지한다.
- [상세계획 §3.1](../proposals/widget-episode-adaptive-exit-implementation-plan-2026-09-09.md#31-사전-확정할-승인-envelope)의 미결정은 적용 owner/scope·모드·신규 episode/유효기간, 보유/유예·손실/무보호시간, runner 배분, 매도 가격/TTL/시도상한/최종 미체결 처리, 세션/정지/원천상실 정책, 평가창/표본·rollback이다. 기존 연구/test fixture 숫자나 “전체 활성화”라는 종결 목표로 이 값을 승인하지 않는다. 기존 보유의 목표유지 계약을 변경하지 않는다.
- 진행을 재개할 때는 최초 운용 envelope를 사용자에게 확정받고, 그 범위에 맞춰 미완료 실행·독립 검증/정책 발행/enrollment/launcher를 구현·review/fix·검증한 뒤 실제 활성화 가능 여부를 다시 판정한다. 최초 활성화 전 새 exit 실체결이라는 순환 조건은 추가하지 않되, 현재 원천 결손·경제성 미평가를 무시하거나 가짜 승인 receipt를 발급하지 않는다. 전체 종료·활성화는 **미완료/차단**, 현재 owner는 동일0910 OPEN이다.

## 7. 조합 선택 위임 후 운용 방향과 group 수량 종료 구현

사용자가 질문을 하나씩 선택하는 대신 **“네가 제안하는 최적의 조합으로 진행”**하도록 지시했다. §6의 사용자 선택 대기는 이 설계·구현 위임으로 갱신한다. 같은 선택 질문을 반복하지 않는다. 다만 현재 데이터로 최적 수치나 수익 개선을 입증한 것은 아니며, 위임을 이미 발급된 live policy/검증 receipt로 표시하지 않는다.

### 선택한 운용 방향

| 항목 | 채택 방향 | 근거·잔여 조건 |
| --- | --- | --- |
| 범위 | 전체 위젯·episode profile 지원, 검증된 신규 episode만 편입 | 기존 보유/수동 보유·원 target은 이관하지 않음. main은 별도 owner |
| 청산 조합 | 시간·진행률 조기청산 + 완전 체결된 일부 lot/leg trailing | 동일 scope의 baseline/단독 모드/결합 비교에서 결합이 열위면 강제 선택하지 않음 |
| 손실 | 전체 paired 비용 후 EV/순이익 개선을 평가하며 개별 손실 청산을 일괄 금지하지 않음 | 원천·비용·위험 한도 검증 전 실주문 금지. 손실 기준은 실제 손실 보장 상한이 아님 |
| 시간 | 상태 기반 soft 시간/한 번의 유예 우선 비교, 첫 운용안의 일률적인 hard-wall 청산은 미채택 | 최대 보유시간·완료 시각 보장 없음. 기존 보유 무손절/목표유지를 소급 변경하지 않음 |
| runner | 사전 명시한 완전 체결 lot/leg 단위, 나머지 원 target 유지 | 사후 성과로 lot 선택·총수량 확대·암묵적 전량 배분 금지 |
| SELL | fresh depth와 별도 가격 하한을 검증한 보통 지정가 | 시장가·하한 없는 추격·stale 매도 없음. 실제 TTL/가격 bound는 계측된 지연에 결속 |
| 최종 잔량 | 시도 상한 뒤 새 자동 주문 중지, 대사·잔량 관리·알림 유지 | 원 target 복원이나 무한 재호가는 자동 default 아님. 원 주문 terminal/late fill이 먼저 |
| 세션/장애 | 지원 세션의 원 owner 관리, 정지/원천 결손은 새 전환 금지 | 이미 취소된 잔량 manager는 종료하지 않음. 전일 주문 복구 코드는 별도 미완료 |
| 편입/기간 | 전체 자동 선택 연결, 대상별 검증 통과분만 다음 가능한 PREOPEN 편입 | 같은 stage 단일 owner·유한 신규 편입 유효기간/기존 관리 수명 분리. 날짜 도래로 강제 ON 하지 않음 |
| 평가 | 같은 episode/비용의 chronological train/holdout·base/stress EV·순익, tail/자본점유 | actual/CF 분리. 유입률·분산·제외율로 평가 계약을 정하며 연구 최소2episode/2일을 live floor로 복사하지 않음 |
| 중지/재개 | 주문/소유권/source incident는 신규 편입 중지, 수리·동일 범위 재검증 뒤 재개 검토 | 활성 잔량 관리 중지 아님. 저수익/무표본은 운영 사고와 분리해 rolling owner에서 판정 |

수치 선택도 위임 범위에서 추진한다. 현재 source9/9가 `blocked_source_contract`/승격 후보0/경제성 미평가이므로 확정 가능한 최적값은 없다. [기존 연구 grid](../../src/engine/monitoring/machine_adaptive_exit_source.py)의 soft60/120/180초·유예30초, trailing30초/진행75%/1tick, 손실1%·SELL TTL5초/최대2시도 등은 **source-only 탐색/실행모델 가정**으로만 보존한다. 이를 검증된 최적 조합·최초 승인 수치로 복사하지 않는다. 새 grid·연구 실행은 이번에 하지 않았다. 다음 수치 확정의 선행조건은 사용자 재설문이 아니라 최초 fill/lot/target epoch→ordered path→비용/실행 지연의 유효 원천과 독립 검증이다.

### 이번 실제 코드 범위

위치 gate에 따라 공통 주문 owner 패키지에 [group_terminal.py](../../src/trading/order/adaptive_exit/group_terminal.py)를 추가하고 기존 `GroupRunnerExecutor.reconcile_group_terminal()`에서 직접 소비한다. registry에는 **읽기 전용** `position_intents`를 추가했다. 신규 engine-root 모듈·정기 producer·daemon·서비스는 없다.

- 동결 group의 완전 체결 BUY 전수·원 target·저장 action과 실제 registry intent 전수를 대사한다. account/position/symbol의 **다른 날짜·route·terminal·미결속 intent도 숨기지 않는다**. 알려진 주문만 확인하거나 net 수량0으로 미해결 주문을 덮지 않는다.
- 기존 adapter의 dated/current 조회로 원 target와 첫 runner를 모두 대사하고 exact terminal proof·부분취소 proof·수량 보존을 검증한다. `target fills + runner fills = group BUY fills`, 전체 position 잔량0일 때만 원 owner의 같은 lock/CAS 아래 terminal receipt를 저장한다.
- 취소수량은 SELL fill이 아니다. runner만 완료·target 진행 중은 `group_orders_working`, runner 미체결 종료 잔량은 복구로 남는다. 취소 없이 원 target 전량 체결된 동결 group도 정상 종료 가능하다.
- 저장 전/후 실패·무저장 callback·lock 상실·source 실패/시간 초과·위조 hash·다른 날짜/route intent를 검증한다. 저장 receipt의 재시작 재소비는 broker 재호출/재전송 없이 현재 registry와 재대사한다. terminal slot 뒤 신규 실행 action은 전송 전 차단한다.
- 결과는 **group 수량 종료**이며 일반 owner episode archive/완료 횟수/다음 신호 handoff가 아니다. lot별 실제 매도 귀속·체결금액/수수료/세금/순이익은 null, `economic_acceptance=false`, `new_entry_authority=false`다. TTL cancel의 ACK를 runner 종료로 대신 닫지 않으며 별도 취소 복구·후속 replacement generation은 미완료다.

공식 API gate는 이번 실행의 `git ls-remote`/로컬 revision 대사로 다시 확인했다. upstream SHA `234560d213acd8871ae344b5481aecd2f30287fa`, `kiwoom_docs` 부재, `kiwoom/specs.py`, `kiwoom/core/client.py`, packaged `kt00007/ka10075/kt10001/kt10003`, Postman PRD/MOCK JSON body/header/continuation을 열람했다. [공식 저장소](https://github.com/Kiwoom-Securities/Kiwoom-REST-API)와 기존 안전 경계를 유지하며 요청/parser/호출량 상향은 없다. 테스트는 fake transport만 사용한다.

실제 broker 주문·정책/env·운영 registry/custody·PID/service·장후 원본은 변경하지 않았다. 공유 registry 모듈에는 read API만 추가했고 이미 로드된 process의 새 코드 소비를 주장하지 않는다. 별도 병행 WS/PREOPEN 수정은 건드리지 않았다.

### 남은 실제 차단

전체 활성화는 아직 미완료다. 새 종료 receipt의 일반 owner archive/다음 신호 연결, 부분취소 뒤 trailing/SELL 판단, whole-target·TTL cancel/잔량·거절/전일 복구, 실제 승인 validator/발행/enrollment/launcher가 남아 있다. 원천 결손·경제성 미평가도 유지한다. 숫자 선택 질문이나 표본 대기 하나로 합치지 않으며 후속 구현·오늘21:30~21:40 자연 확인은 기존 `MachineLifecycleTurnoverObjectiveFollowup0910` OPEN에서 이어간다.

## 8. 조합 선택 위임 후속의 검증 receipt

전체 영향 회귀는 **1854 PASS / 4 owner-비대상 SKIP / 58.51초**다(위§4와 같은 범위 + 당시 group terminal43개). 이후 재리뷰에서 BUY/SELL proof의 수량을 literal int로 검증하고 `true=1` 반례2개를 추가했다. 마지막 직접 영향 재검증은 **296 PASS / 13.60초**이며 group terminal45·group execution62·group runtime·symbol owner coexistence를 포함한다. 두 실행은 중복 포함이므로 합산하지 않는다. 위§4의1811 PASS와도 합산하지 않는다.

Ruff/Black check·compile·`git diff --check` 통과. 문서의 신규 직접 링크5개·§7 anchor를 점검했고 print-only parser30개 중 현재 checklist14개/`MachineLifecycleTurnoverObjectiveFollowup0910`1개를 확인했다. 새 checkbox를 만들지 않았다. 실제 broker/Provider·report 재생성·PID/정책/주문 변경은 검사하지 않았으며 수행하지도 않았다.

`korstockscan-review-gate`로 registry producer/전수 census→group proof/CAS→executor 재소비·전송 차단을 검토하고 수량 bool, 저장/잠금/시각, ACK/잔량과 실제 미연결 owner를 분리했다. **이번 group 수량 종료·문서 운용 방향 범위의 미해결 finding0**이며 전체 종료/활성화 연결은 §7의 잔여가 있으므로 전체-scope PASS가 아니다. 공식 revision은 `2026-09-10T08:31:19+09:00`에 재조회하여 동일 SHA를 확인했다.

최종 검증 파일 SHA256:

- `group_terminal.py`: `c444bac2a6ce8c92d63b3822bf7b9c4c5dcdb2a7a0bf7a97b449ec3c01db1807`
- `group_execution.py`: `4b1663ef4023c0a0063a1984d868f8138ae742ebafd659428f3d8bf4660ab80b`
- `owner_custody_registry.py`: `eea843906173738759cde260682ca144d55ba8ab30348adb671de558a780f641`
- `test_machine_adaptive_exit_group_terminal.py`: `8764554b35e98d497ea42815cc8bdc6db6ad5ffd4bd96355c99a31e26f0168ad`

## 9. 전체 활성화 목표 후속: trailing·취소 자식 종료 통합

사용자가 **전체 활성화 자체가 목표**임을 다시 명시했다. 목표를 개별 helper 완료로 축소하지 않으며 §7의 조합·수치 설계 위임을 유지한다. 같은 선택 질문을 다시 요구하지 않는다. 실제 금융계좌 운용을 시작하는 최종 live 기동/적용은 사용자 실행으로 분리하고, 코드·독립 검증·안전한 전달 준비와 실제 활성화/자연 효과를 각각 판정한다. 이번에는 목표 상태를 `active`로 유지했으며 전체 완료로 닫지 않았다.

### 실제 구현과 직접 소비

- 기존 공통 주문 패키지의 [group_trailing.py](../../src/trading/order/adaptive_exit/group_trailing.py)를 추가했다. 최초 pre-release 판단·동결 position/비용·exact 부분취소 proof→선택 runner의 fresh snapshot→같은 `evaluate_exit`→실제 arm/high-water/stop→첫 SELL 판단→`sell_decided_released`를 연결한다. runner별 같은 depth를 한 번만 소비하고 최악 실행 호가를 지정가로 사용한다. 원 first-fill/한 번의 연장 시계는 유지한다. 혼합 runner 의도는 선택적 executor 미지원으로 명시하고 전량 매도로 대체하지 않는다.
- 최신 판단 pending veto·CAS 저장/재시작 재계산·policy/position 불변·저장 실패 객체 차단을 유지한다. 최신 판단과 실제 quote age는 원장 예약 전/후에도 재검증한다. 취소 ACK만으로 arm하지 않으며 새 관측은 이미 저장된 SELL action을 교체하지 않는다. 원장·승인 callback의 독립 전체 guard는 필수다.
- `RegisteredSellAdapter.reconcile_terminal_cancel`은 같은 날짜의 원 SELL 종료와 **별도 취소 자식의 양수 확인수량/확인시각**을 함께 대사한다. 요청6→late fill 뒤 실제확인2처럼 `0 < confirmed <= requested`, `Q = F + prior C + confirmed C`, `R=0`인 경우를 지원한다. ACK·0확인·미정의 거절·current child·route/날짜/연속조회 결손을 종료로 추정하지 않는다.
- `OrderOwnerRegistry.record_terminal_cancel_reconciliation`은 원 주문과 자식 종료를 하나의 fsynced event로 원자 투영한다. 기존 원 SELL terminal proof는 유지하고 자식 proof를 따로 보존하며, 재관측 시 취소수량을 중복 해제하지 않는다. 취소수량은 SELL fill이나 청산 수익이 아니고 `Q-F`는 계속 잔량이다.
- group TTL consumer뿐 아니라 **실제 위젯·공통 episode가 소비하는 `RegisteredOwnerExitPort.reconcile`과 terminal 원장**에 같은 child proof를 연결했다. 원 SELL만 종료되고 취소 child가 미확인인 상태는 `CANCEL_PENDING`/잔량 관리에 남으며 다음 SELL·episode archive/완료 횟수로 넘어가지 않는다. 정상 원 목표가 취소 없이 체결된 경우는 별도 정상 종료다. 추가된 읽기는 기존 bounded dated/current 대사이며 신규 retry/호출량 상한을 만들지 않는다.
- 이미 정상 부분취소가 확인된 뒤 **남겨둔 원 target가 먼저 전량 체결**되는 순서를 보완했다. 최초 partial proof/해제수량을 보존한 채 fresh target terminal을 대사하여 freed runner의 첫 SELL을 계속 소비한다. 최초 proof가 없는 전량취소/불명확 확인을 이 경로로 승인하지 않는다. 과거 proof만으로 현재 root/child source 결손을 덮지 않는다.

### 전체 완료를 막는 항목별 상태

| 경로 | 현재 판정 | 다음 직접 완료조건 |
| --- | --- | --- |
| pre/post-release 판단→첫 runner SELL | 코드 구현·격리 검증 | 실제 owner 저장/독립 서비스·enrollment 소비 |
| TTL child 양수 확인·단일 lot 실제 owner 종료 | 코드 구현·격리 검증 | 실제 exact receipt·현재 process 반영은 별도 |
| group 전체 수량 terminal | 구현 | 일반 widget/episode archive·기존 다음 신호 handoff 연결 |
| whole-target·혼합 선택·TTL 뒤 다음 runner generation | 미구현 | 단일 writer/수량/시도 bound 아래 원 owner 통합 |
| pending BUY/late fill·legacy/force-flat·전일/미정의 취소·거절 | 미완료 | 원 주문/custody·날짜별 직접 복구 계약과 테스트 |
| 최초 envelope·독립 validator·PREOPEN publisher/enrollment·실제 launcher | 미구현/미발급 | 실제 유효 원천 기반 수치와 같은 코드/정책/서비스 검증 |
| 자연 경제성/정산 원천 | 미수용 | exact lot/path·비용/base/stress·holdout; 비용 결손 null 유지 |
| 최종 실거래 활성화 | 미실행 | 위 준비 검증 후 사용자 실행; 코드 PASS를 실거래 receipt로 바꾸지 않음 |

`2026-09-10T09:05:40+09:00` 읽기 전용 재확인: source9/9 attribution SHA256 `b5068924d29491da163a469da05b8634b1528ee5249723012e103d13999e1db5` 유지. child `blocked_source_contract`, 원천30행/승격 후보0, `economic_acceptance=not_evaluated`, `net_ev_pct=null`, `eligible_for_next_preopen=false`, `live_owner_adapter_connected=false`. `data/config`/`data/runtime` ignored 파일 포함 검색에서도 adaptive-exit 적용/envelope 파일을 찾지 못했다. 최초 fill/lot epoch와 ordered post-target path 결손을 연구 숫자·0원·가짜 승인으로 메우지 않는다. 이는 **코드 미연결과 별도인 원천 결손**이며 유한 완료 ETA나 전체 정상으로 표시하지 않는다.

공식 API gate는 구현 전에 upstream/spec/core·packaged `kt10001/kt10003/kt00007/ka10075`·Postman PRD/MOCK를 열람했고, `2026-09-10T09:06:49+09:00` 재조회에서도 SHA `234560d213acd8871ae344b5481aecd2f30287fa`를 확인했다. `kiwoom_docs` 부재와 미정의 zero-confirm/rejection 경계는 유지한다. REST endpoint/header/body·shared budget·continuation 상한은 바꾸지 않았으며 실제 API/주문을 실행하지 않았다.

운영 env/정책/registry/custody/PID/service·원천 report 재생성·Provider 호출·외부 sync·commit/push는 실행하지 않았다. 관련 없는 병행 Entry AI/PREOPEN 변경은 덮지 않았다. 현재 후속은 기존 `MachineLifecycleTurnoverObjectiveFollowup0910` 하나이며 오늘21:30~21:40 자연 acceptance는 OPEN이다.

## 10. 전체 활성화 목표 후속 검증 receipt

최종 확인 `2026-09-10T09:10:06+09:00`: 전체 영향 회귀 **1927 PASS / 4 owner-비대상 SKIP / 66.80초**. `test_machine_adaptive_exit_*.py` 전부와 기존 turnover/attribution/approval·widget·low-price/Samsung4경로 및3 preflight·owner coexistence·체크리스트 builder를 포함했다. 중간 직접 검증은 단일 lot·실제 owner-loop/terminal·group trailing·취소 확인206 PASS/4 비대상 SKIP, group release/execution/terminal·broker/registry505 PASS다. 중복 포함이므로 서로 또는 이전§4/§8과 합산하지 않는다.

전체 영향 첫 실행은 병행 수정 중인 `entry_setup_live_policy.py`의 구문 오류로 수집 단계에서 중단됐다. 해당 파일은 수정하지 않았다. 독립 compile이 다시 성공한 뒤 같은 전체 영향 범위를 재실행해 위 결과를 얻었다. 또한 과거 성공 fixture가 cancel ACK만 넣었던 단일 lot·원 EXIT 테스트는 명시적 positive confirmation fixture로 수정하고, confirmation 결손에서 실제 owner가 종료/재주문하지 않는 반례를 추가했다. guard를 완화하여 테스트를 맞추지 않았다.

Ruff·Black check(관련16파일)·compile·`git diff --check` 통과. print-only parser30개/현재 checklist14개/현재 owner1개, 중복 title0이다. 새 checkbox나 외부 동기화는 없다. `korstockscan-review-gate`로 producer→cancel registry 원자 투영→실제 단일-lot owner·group book/executor·terminal을 반복 검토하고 보완하여 **이번 post-release trailing/positive cancel confirmation/원 target 선행 완료 범위 미해결 finding0**으로 닫았다. §9의 전체 통합 미구현·자연/경제성/실거래 활성화는 이 scoped finding0으로 지우지 않는다.

최종 검증 코드 SHA256:

| 파일 | SHA256 |
| --- | --- |
| `group_trailing.py` | `8b5b10939d36f3923907bc2ce2ee019be6bb1bd8051b3071db888dbbc28ad938` |
| `group_decision.py` | `93bbb1e082159f9f658a2cd250fd83d4c3c4d75d76fe3feeea7be8f4b9874c3b` |
| `group_terminal.py` | `8176d70504dbccff16006c643792424dc71548801921882914542624c50f362b` |
| `group_execution.py` | `412433878962106114d4299974564597730dc3391c1b9634ecd42fc17d92a744` |
| `group_runtime.py` | `eb4a62777ce1c841b169131c6e33f79159ba8c39ae9bb8ac6767aded8f9a339a` |
| `broker.py` | `3da6a8e4c16522e35263febda262059ea5673a8a30bda88ac43b04f42e1d84a6` |
| `runtime.py` | `c62504db10259ab4da90f3255181a5c9035c1741b041636ce26e6e94f50ca8b4` |
| `terminal.py` | `cde226b5a85772b0150edb80970afa7908180ae2262c4352b262d2b471541856` |
| `owner_custody_registry.py` | `c0d0b3d577ac364ac619d0781b170e7187814b531f3d89e80732a8e3c24de6c4` |

## 11. Bounded runner 후속 generation과 전체 종료 연결

전체 활성화 목표는 `active`로 유지한다. 이번 후속은 기존 공통 [group_execution.py](../../src/trading/order/adaptive_exit/group_execution.py)와 [group_terminal.py](../../src/trading/order/adaptive_exit/group_terminal.py)를 확장한 **실행 연결 코드**이며 새로운 정기 worker나 실제 기동이 아니다. 테스트는 기존 주문 역할의 `src/tests/test_machine_adaptive_exit_group_retry.py`에 둔다.

- 첫 SELL 뒤 TTL 취소의 원 주문 **및 자식** terminal proof가 모두 닫힌 경우에만 `Q-F`를 다음 generation의 정확한 수량으로 사용한다. late fill로 요청 취소량보다 실제 취소량이 줄면 successor도 감소한다. 해제수량을 체결·실현수익으로 세지 않는다.
- `RunnerBounds.maximum_sell_attempts`의 구현 지원 상한은 기존 single-lot과 같은3이다. 기존 호출 기본1과 기존 binding/action slot/hash를 보존한다. 2~3회는 **명시적 별도 bound와 필수 `authorize_retry`** 없이는 구성할 수 없으며3을 운용 최적값·발행 승인값으로 선택한 것은 아니다. binding 이후 cap 변경은 차단한다.
- 세대2 이상은 action schema v2로 `attempt_no`, 최초 `original_sell_action_hash`, 직전 주문번호와 잔량을 영속한다. 중간 세대 누락·원 청산 의도 변경·외부/미등록 intent 사후 채택을 막는다. 저장된 의도는 유지하되 새 source/가격·depth/loss bound 검증을 mandatory retry validator와 전체 owner/account/custody/manual/operator/broker guard가 예약 전/후에 수행해야 한다. 기존 book이 있으면 최초 SELL receipt도 재계산하여 그대로 유지한다. **새 alpha 재신호를 요구하거나 오래된 첫 가격/receipt를 새 실행 가격으로 쓰지 않는다.** 독립 실제 validator 구현/launcher 공급은 아래 미완료와 별도다.
- 예약·거절·ACK 불명확 상태는 같은 intent의 읽기 전용 회복만 허용한다. 재시작으로 재제출·재가격·세대 건너뛰기를 하지 않는다. 저장 실패나 저장 대기 뒤 guard 거절에서는 전송하지 않으며 durable reservation을 보존한다.
- `poll_runner`는 최신 연속 세대의 TTL/취소/체결을 소비한다. 상한 소진 시 `attempts_exhausted=true`, `manager_must_remain=true`, 실제 잔량을 남기며 강제매도/목표복구/다음 BUY로 전환하지 않는다. 그룹 전체 수량 terminal은 원 target+모든 runner generation의 **실제 체결 합**과 완전한 position intent census로 닫는다. 각 cancel child는 별도 proof가 필요하다. 비용/PnL·실제 BUY-lot 매도 귀속은 여전히 null이며 신규 진입 권한이 아니다.
- 재리뷰에서 이전 terminal generation의 동일 broker 조회 반복을 제거했다. successor 승인 때 이미 닫힌 이전 root/child proof는 로컬에서 다시 검증하고, 마지막 group reconciliation의 fresh 조회는 원 target+최신 runner로 제한한다. 기존 최대2주문 observation window·query/continuation/shared limit를 늘리지 않는다. 과거 취소 source가 처음부터 결손이면 이 재사용 경로가 열리지 않는다.

공식 API gate: 구현 전 `2026-09-10T09:13:30+09:00` upstream HEAD `234560d213acd8871ae344b5481aecd2f30287fa` 재확인. `kiwoom/specs.py`, `kiwoom/core/client.py`, `kiwoom/_data/kiwoom_api_spec.json`의 `kt10001/kt10003/kt00007/ka10075`, `postman/kiwoom-openapi.postman_collection.json` PRD/MOCK를 대사했다. 이 revision의 `kiwoom_docs` 부재를 보존한다. 보통 지정가 SELL/양수 exact 취소·dated/current proof 계약을 재사용하며 wire/parser/호출 상한은 변경하지 않는다. 실제 broker·Provider API는 실행하지 않았다.

최종 확인 `2026-09-10T09:29:49+09:00`: 직접 회귀182 PASS(기존147+새35), **전체 영향1962 PASS/4 owner-비대상 SKIP/71.92초**. 범위는 §10과 같은 adaptive-exit 전체·turnover/attribution/approval·위젯/low-price/Samsung4/3preflight·owner coexistence·체크리스트 builder다. 서로 또는 이전§10과 중복 합산하지 않는다. 마지막 테스트 파일 format 후 새35개를 다시 실행해35 PASS/5.00초를 확인했다. 최초 Ruff의 테스트 lambda style2건은 함수로 보완했고 Black·Ruff·compile·`git diff --check`가 최종 통과했다. print-only parser28개/현재 checklist12개/현재 owner1개/중복title0이며 병행 당일 checklist 변경은 보존했다.

`korstockscan-review-gate`로 bound/저장·예약/모든 guard→기존 book의 원 의도→retry ancestor/취소 proof→전체 terminal consumer·조회 반복을 리뷰/보완/재검증하여 **이번 bounded generation·전체 수량 종료 범위 미해결 finding0**으로 닫았다. 실제 fresh-price validator/owner-loop 공급을 mock PASS로 완성했다고 보고하지 않는다.

| 최종 파일 | SHA256 |
| --- | --- |
| `group_execution.py` | `b9e908c68c71fce9b86443b1142ff603fac7ffc55e4efbb06a2031ca58655a6c` |
| `group_terminal.py` | `15c12642cabcd6fd3846b1f34348486f6c2ffb1ff533c648484c61a031575830` |
| `test_machine_adaptive_exit_group_retry.py` | `6de8a175a4676c9c772e8a4e50c5c9bc3b900adab76401c97e2e9916178f4095` |

남은 전체 목표는 **group 일반 widget/episode archive·다음 기존 신호 handoff, whole-target/선택적 runner 중재, pending BUY/late fill·legacy/force-flat·전일/취소거절 복구, 실제 독립 envelope/가격 validator·PREOPEN 발행/enrollment/launcher, 자연 lot/path·paired 경제성/정산**이다. 이 실행기 확장으로 그 연결이나 source9/9 후보0을 완료로 재라벨링하지 않는다. 최종 live 기동/계좌 운용은 사용자 실행으로 분리한다. 운영 정책/env/원장/custody/PID/service·원천 재생성·외부 sync·commit/push는 변경/실행하지 않았다. 다음 owner는 같은 `MachineLifecycleTurnoverObjectiveFollowup0910`이며 예정21:30~21:40 자연 acceptance는 OPEN이다.

## 12. Group session과 실제 위젯 원장 종료 연결

전체 활성화 목표는 `active`다. 이번 후속은 **shared target의 group executor를 기존 위젯 `run_once`·원자 state file·일반 주문 원장/episode 종료에 연결한 코드 구현**이다. 독립 target 두 개를 쓰는 Samsung/저가주 공통 two-leg는 기존 단일-lot owner 경로를 유지한다. 그 주문을 합산하거나 별도 group process를 만들지 않았다.

- 위치 gate: 기존 주문 역할 패키지의 [group_owner_loop.py](../../src/trading/order/adaptive_exit/group_owner_loop.py)에 frozen `GroupOwnerSession`/`GroupLoopServices`/`GroupOwnerPort`를 두고, [기존 owner services](../../src/trading/order/adaptive_exit/owner_loop.py)와 [위젯 engine](../../src/trading/widget_auto_trade/engine.py)에 연결했다. 별도 lock·일반 gateway·새 engine-root/producer는 없다. `OwnerLoopServices.group`는 기본 없음이다.
- group·원 BUY lot/첫 관측/가격·target·배분·policy·explicit bounds·execution 승인 hash를 불변 정의로 저장한다. 실제 독립 validator/원 custody 검사는 필수 callback이며 파일/hash 존재가 승인이 아니다. 원 owner 잠금 아래 record별 CAS→동일 state 파일 원자 저장/fsync→파일 read-back→재시작 재구성으로 pre-release 판단, 부분취소, post-release trail, SELL/TTL/잔량 retry, 전체 terminal을 소비한다. 새 loader 원천·검증 시계가 없으면 이전 판단을 재사용하여 주문하지 않는다.
- `run_once`와 `process_payload`가 group을 일반 BUY/EXIT보다 먼저 claim한다. 삭제된 catalog 종목·source snapshot 부재·날짜 변경 때도 동결 group/원 주문일을 보존한다. single-lot 동시 claim, pending BUY/진입 확인, 수동/기존 EXIT, scale-in, 미해결 전일 custody, ordinary→registry intent/client/owner 불일치와 unaccounted order는 recovery이며 baseline 주문으로 우회하지 않는다. 기존 source EXIT의 observe-only는 매도 권한으로 올리지 않고, 실제 final EXIT/force-flat의 group 중재는 명시적 별도 미완료다.
- 원 target와 모든 runner 세대의 실제 full terminal/cancel proof·체결합·registry 잔량0을 재계산한 뒤 original target와 replacement SELL을 일반 `orders`에 반영한다. archive에 frozen session/모든 action/terminal을 보존하고 원 entry signal의 완료 횟수와 완료시각을 **한 번만** 기록한다. 단일 runner 종료는 전체 episode 완료가 아니다. 다음 호출은 기존 신규 신호·cooldown/cap/전체 safety owner를 그대로 사용하며 이 terminal은 신규 BUY authority가 아니다. 비용 미대사/lot별 실제 SELL 귀속은 `null`이며 수량 flat를 수익 검증으로 바꾸지 않는다.
- 재리뷰 보완: owner cycle 시작시각은 날짜/미래시각만 검증하고 이후 단계는 매번 actual clock·원천 age·기존 bound를 재검증한다. 앞 종목의 처리시간 때문에 뒤 종목의 fresh 판단을 stale loop로 오판하지 않는다. 원장 완료시각도 loop 시작/재복구시각이 아니라 exact terminal receipt의 관측시각이다. 취소 전 동결 target의 자연 full-fill도 기존 bounded dated/current 확인 후 직접 닫는다. callback 성공만으로 파일 저장을 승인하지 않고, directory open/fsync 실패·no-op 저장·archive read-back 실패는 예외/원장 보존으로 처리한다. 손상된 on-disk JSON은 이전 메모리 상태로 덮지 않고 원본을 보존한다. guard 도중 잠금 상실·새 unknown slot·ordinary registry ID/client 불일치도 전송 전에 다시 검사한다. 재검증 중 발견한 전일 복구 사유/일반 clock 오류 혼동은 `group_cross_date_requires_owner_recovery`로 분리했다.

공식 API gate: `2026-09-10T09:33:00+09:00` [공식 upstream](https://github.com/Kiwoom-Securities/Kiwoom-REST-API)의 HEAD `234560d213acd8871ae344b5481aecd2f30287fa`를 재확인했다. 이 revision에 `kiwoom_docs` 없음, `kiwoom/specs.py`, `kiwoom/core/client.py`, `kiwoom/_data/kiwoom_api_spec.json`의 `kt10001/kt10003/kt00007/ka10075`, Postman PRD/MOCK를 열람했다. 기존 JSON POST/ordinary limit SELL·양수 exact cancel·dated/current/continuation·공통 한도 계약을 재사용하며 protocol/parser를 변경하지 않았다. 실제 broker/API/auth/주문·서비스 기동은 실행하지 않았다.

최종 검증 receipt `2026-09-10T10:01:20+09:00`: **1997 PASS / 4 owner-비대상 SKIP / 99.08초**. 기존 `test_machine_adaptive_exit_*.py` 전부와 turnover/attribution/approval·widget·low-price/Samsung4경로/3 preflight·owner coexistence·checklist builder를 포함한다. 새 group owner 전용35개는 이 합계에 포함하며 이전1962개/중간33개/1995 PASS와 합산하지 않는다. 중간 시계 보완 세대의 cross-date reason 실패1건을 확인·수정한 뒤 마지막 전체 명령을 다시 통과했다. 해당 이전 FAIL이나 첫 PASS를 최종 receipt로 재사용하지 않았다.

`korstockscan-review-gate`로 shared group producer/book/registry→실제 위젯 consumer→ordinary archive 및 독립 episode 회귀를 반복 검토해 **이번 group session/동일 owner 연결/일반 종료 원장 범위 finding0**으로 닫았다. Ruff·Black check·compile·`git diff --check` 통과. print-only parser28개/현재 checklist12개/현재 owner1개·중복 title0이며 외부 sync는 없다. 새 테스트 fixture의 정책·가격·수량·approval=True는 임시 원장용이며 운영 승인값/실계좌 실행 근거가 아니다. 병행 사용자 변경과 이번 네 파일의 검증 세대를 분리했다.

| 검증 코드/테스트 | SHA256 |
| --- | --- |
| `group_owner_loop.py` | `b9b95a6fe8d3a3df9e3529910d6047f829b6a813e28933a421f64f3a67b9a5b4` |
| `owner_loop.py` | `6b367d8eab8535a570e413ecadbefa74c26b2f3744661b6fb546cd198ffea707` |
| `widget_auto_trade/engine.py` | `9b6a954f6cbc6aa8b73d93270bee456fb131d010a3be921d3e9c371df456296d` |
| `test_machine_adaptive_exit_group_owner_loop.py` | `f57ef6d24e2cc928856de8e7b0b414e59608e4787706a37e1f9c1500847aaade` |

남은 전체 목표는 whole-target/선택적 runner·실제 pending BUY/late fill·group final EXIT/force-flat·legacy/전일/거절 복구, 독립 envelope/시장·가격 validator·PREOPEN 발행/enrollment/실제 launcher, 자연 lot/path·paired 경제성·정산이다. 이것은 표본 대기만이 아니라 **미완료 코드/연결**을 포함한다. source9/9 기존 결손·후보0을 재생성하거나 승인값을 발명하지 않았다. 새 코드 검증으로 전체 활성화·자연 PID 소비를 선언하지 않고, 최종 live 기동/계좌 운용은 사용자 실행으로 분리한다. 다음 실행 owner는 같은 `MachineLifecycleTurnoverObjectiveFollowup0910`이며21:30~21:40 자연 acceptance는 OPEN이다.

## 13. 원 정책 whole-target EXIT와 runner 단일 writer 중재

전체 활성화 목표는 `active`다. 이번 후속은 **기존 위젯 entry execution policy의 source final EXIT/명시적 force-flat을 shared-target 전체 청산 journal로 동결하고, 모든 기존 SELL·취소 자식 종료→실제 잔량→후속 지정가 SELL/TTL→일반 episode archive까지 연결한 코드 구현**이다. 연구의 전체/혼합 lot 조기청산 결정을 자동 승격하거나 새 시간청산 정책을 만든 것은 아니다.

- 위치 gate: 기존 주문 역할 패키지 [group_whole_exit.py](../../src/trading/order/adaptive_exit/group_whole_exit.py)와 [group_settlement.py](../../src/trading/order/adaptive_exit/group_settlement.py)를 사용한다. 기존 group port·broker adapter·위젯 `run_once/process_payload`의 직접 consumer를 함께 수정했다. engine-root·별도 producer/process/lock/자동 trigger는 추가하지 않았다.
- 원 entry signal·entry policy hash·group 정의·route/session·실제 source/수용시각에 결속한 전체 EXIT는 원 owner state 파일의 단일 CAS journal에 보존한다. 원천 신호가 사라져도 접수 의도는 유지하고 기존 runner action hash를 고정해 병렬 release/SELL writer를 차단한다. 관찰 전용 EXIT는 매도 권한이 아니며 `force_flat_at_session_end=true`와 원 cutoff가 없으면 시간청산을 만들지 않는다. `WholeExitServices`의 독립 request/action 승인·fresh 가격/깊이/모든 safety 공급은 필수이며 기본 공급자는 없다.
- 원 목표·기존 runner·각 generation의 SELL root와 CANCEL child를 전수 대사한다. pending partial release는 기존 양수 확정 proof를 먼저 소비하고 새 전체취소를 중복 보내지 않는다. 전체취소는 양수 실제 잔량만 요청하며 `Q=F+기존 부분취소 C+이번 확정 C`를 닫는다. late fill 뒤 작은 양수 확정량도 그대로 보존하고 ACK/거절/0 확인/미정의 terminal을 체결이나 안전한 재시도로 바꾸지 않는다. 원장 밖 intent·다른 owner·unbound/ambiguous 행은 recovery다.
- 최초 pooled SELL은 원 dated target의 고정 single-use namespace와 **전체 closed census hash/모든 child proof/실제 owned residual**을 요구한다. 이미 부분 runner가 쓴 target successor를 재사용하지 않는다. 다음 residual generation은 직전 whole SELL terminal을 predecessor로 사용하며 명시적 bound와 fresh action 승인 아래서만 가능하다. ordinal·clock·predecessor·취소 중복을 재검증하고 저장/원장 예약 전후의 승인·source age·census·동일 journal generation을 확인한다. 기본1/지원상한3은 live 최적화/승인값이 아니다.
- 매 owner step의 조회는 기존 root 한 건의 bounded dated/current 경로다. TTL과 기존 무보호 상한을 재사용하되 새 상한을 발명하지 않았다. 확인 기한을 넘긴 취소는 반복 broker 조회로 무한 대기하지 않고 직접 deadline recovery로 남긴다. 무보호 상한 뒤 새 SELL·상한 소진 뒤 잔량을 자동 성공으로 바꾸지 않는다. 원장 예약/거절/응답 불명확은 재시작해도 재전송하지 않는다.
- 전체 실제 BUY 체결합=전체 SELL 체결합·모든 root/child exact terminal·registry잔량0일 때만 §12의 기존 ordinary orders/archive·완료 횟수1회 consumer로 넘긴다. 목표1+후속9, 목표2+기존runner3+pooled5, whole 후속 residual generation을 임시 원장으로 검증한다. 수량 terminal과 주문별 실제 비용/lot별 SELL 귀속은 별개이며 손익/경제성은 `null/미수용`이다. 신규 BUY는 기존 다음 signal/cooldown/cap/전체 guard를 따르고 이 receipt 자체에는 권한이 없다.

공식 API gate: 구현 전 `2026-09-10T10:03:46+09:00` [공식 upstream](https://github.com/Kiwoom-Securities/Kiwoom-REST-API)의 HEAD `234560d213acd8871ae344b5481aecd2f30287fa`와 로컬 검증 checkout의 SHA 일치를 확인했다. 이 revision의 `kiwoom_docs` 부재, `kiwoom/specs.py`, `kiwoom/core/client.py`, packaged `kt10001/kt10003/kt00007/ka10075` 전체 request/response 및 Postman PRD/MOCK를 열람했다. Postman 시장가 예시는 실행하지 않았으며 현재 ordinary 지정가 `trde_tp=0`, 양수 exact cancel, dated/current·HTTP/body 오류·연속조회·공통 한도를 유지한다. 새 pooled method는 같은 wire 계약과 registry/guard를 재사용한다. 실제 auth/API/계좌 조회·주문/기동은 실행하지 않았다.

최종 검증 receipt `2026-09-10T10:28:27+09:00`: **2024 PASS / 4 owner-비대상 SKIP / 137.27초**. §12와 같은 전체 직접 영향 명령(`test_machine_adaptive_exit_*.py` 전부, turnover/attribution/approval·widget·low-price/Samsung4경로/3 preflight·owner coexistence·checklist builder)을 실행했다. whole 전용27개는 합계에 포함하며 이전1997/중간19·26·2023 PASS와 합산하지 않는다. 첫 전체2023 PASS 이후 competing terminal journal·adapter/bounds 변조를 추가 차단하고 마지막 전체 명령을 재통과했다.

`korstockscan-review-gate`로 original policy/source→group journal/기존 runner veto→broker/registry→ordinary archive를 리뷰/보완/재검증하여 **이번 원 정책 whole EXIT·단일 writer·수량 종료 연결 범위 finding0**으로 닫았다. 저장/예약 뒤 승인 상실·stale·위조 generation·취소 기한/늦은 체결·whole residual TTL·source 소실·원 target 자연 full-fill 반례를 포함한다. Ruff·Black check·compile·`git diff --check` 통과, print-only parser28개/당일 checklist12개/해당 owner1개·중복 title0이다. 아래7개 코드/테스트 SHA는 마지막 전체 검증 뒤 재대사해 불변을 확인했다. 병행 main/WS/recheck/보고서 변경은 별도 사용자 작업이며 이번 활성화 검증/배포에 포함하지 않는다. 테스트용 numeric/승인 callback은 운영 승인값이 아니다.

| 이번 검증 코드/테스트 | SHA256 |
| --- | --- |
| `group_whole_exit.py` | `9420c1bea765bd5e3e41b0a5f501b99c5da41e1343d15102e32cfe88bc2d0765` |
| `group_settlement.py` | `60ea74552a8a870a8e7fc06723ddb971af62a2ce5e10fa3ca7f2962c05e2bc32` |
| `group_owner_loop.py` | `207e9b1b520783ba6469a0ffc185a760f8c27be9ead10bdf37695495ce6e18a5` |
| `group_execution.py` | `598ce035002198152ea2399e8e40c263d26d5d658235cc2e0adc2dfae129c24e` |
| `broker.py` | `e58bf3177775ed48c9aeb0616e428aa2eb051c6fc799bd9ff283c379242e529e` |
| `widget_auto_trade/engine.py` | `00598db79a1d0660212c5e3f0605f599c5cf37746377c8e0340e1bf12f84f75a` |
| `test_machine_adaptive_exit_group_whole_exit.py` | `85da7bbac6b86e5f524e74c5825aa24e9ea418602e106e5338fbf7d79b6d1f10` |

남은 전체 목표: **연구 whole/선택적 lot 결정의 실제 정책 중재, pending BUY 취소/late fill·scale-in·legacy/전일/거절 복구, 독립 numeric envelope/시장·가격 validator·PREOPEN 발행/enrollment/실제 launcher, 자연 lot/path·paired 경제성·정산**이다. 기존 final EXIT/force-flat 실행의 이번 코드 연결과 이 잔여를 혼동하지 않는다. source9/9 결손·후보0을 재생성하거나 live 승인값을 발명하지 않았다. 운영 정책/env/PID/custody/주문·report 재생성·Provider/외부 sync·commit/push는 실행/변경하지 않았다. 최종 live 기동/계좌 운용은 사용자 실행으로 분리한다. 같은 `MachineLifecycleTurnoverObjectiveFollowup0910`의21:30~21:40 자연 확인은 OPEN이다.

## 14. Pending BUY 취소와 late fill의 전체 청산 연결

전체 활성화 목표는 `active`다. 이번에는 **기존 위젯 shared-target owner의 별도 pending BUY를 exact 원주문/부모 entry signal에 동결하고, 취소·최종 매수 체결 확인→whole pooled 잔량 SELL→ordinary 원장/archive까지 연결**했다. 신규 BUY를 제출하는 기능이나 기존 독립 episode의 두 target를 합치는 변경은 아니다.

- 위치 gate: [buy_cancel.py](../../src/trading/order/adaptive_exit/buy_cancel.py), [group_pending_buy.py](../../src/trading/order/adaptive_exit/group_pending_buy.py)를 기존 주문 역할 패키지에 두고 broker/registry·whole journal/settlement·실제 widget `run_once` consumer를 함께 수정했다. 신규 engine-root·cron·별도 process/lock/자동 trigger는 없다.
- 매수 전용 adapter는 기존 매도 adapter를 상속하지 않는다. 공개 기능은 exact BUY 조회/확인/취소뿐이며 NEW BUY/SELL 메서드는 없다. 공유 private parser의 BUY 조회는 공식 `kt00007.sell_tp=2`, `ka10075.trde_tp=2`, 원 주문일·symbol·route/continuation을 결속한다. SELL 공개 경로는 그대로 SELL-only다. 취소는 `kt10003`의 원 BUY 주문번호와 **현재 확인된 양수 전체 미체결 수량**으로만 요청한다. 원 owner 잠금·독립 승인/guard·계좌·날짜·최대 수량·원천 age를 원장 예약 전후 재확인한다.
- 원 dated BUY당 고정 single-use cancel namespace를 사용한다. ACK/timeout/거절/응답 불명확/예약만 남은 intent는 action ID나 재시작으로 재전송하지 않는다. 최종 대사는 원 BUY의 `Q=F+확정 C`, 실제 취소 child의 양수 `cnfm_qty`·확인시각·현재 미체결 부재를 함께 요구한다. late fill 때문에 요청보다 작은 양수 취소 확인이 와도 실제 F/C를 보존한다. BUY root/child terminal과 F/C/proof는 registry 단일 append로 함께 투영하여 fsync 중간 실패의 반쪽 종료를 막는다. ACK·0확인/미정의 거절을 terminal로 추정하지 않는다.
- 요청 v2는 원 ordinary 주문 hash·immutable registry identity·초기 체결수량/registry event hash·대기 진입 확인 hash·scale-in 의도를 보존한다. 현재 원장/일반 주문/원 entry signal이 다른 주문을 symbol/수량으로 흡수하지 않는다. group의 기존 full BUY lot/최초 시각/가격/decision policy는 바꾸지 않는다. 새 늦은 매수 체결은 **전체 청산 잔량 계산에만** 더하고 연구 lot·trailing 초기시각·경제성 표본으로 보간하지 않는다.
- 전체 journal이 기존 BUY 의도를 claim한 동안 일반 BUY/scale-in/원 target 재생성은 진행하지 않는다. pending BUY root와 그 cancel child가 끝나기 전에는 새 target 취소/pooled SELL로 진행하지 않는다. 기존 진행 중 SELL 취소는 먼저 읽기 전용 대사한다. 매수 전용 terminal proof가 없는 partial BUY는 새 `closed_census`의 명시적 pending ID 집합에 있어도 차단된다. 집합을 전달하지 않는 기존 consumer는 full BUY 계약을 유지한다. 전체 F(BUY)=F(SELL)·모든 자주문 terminal·registry 잔량0일 때만 archive로 넘긴다.
- 실제 위젯 consumer가 supplemental BUY의 최종 수량/terminal proof와 모든 SELL을 ordinary 원장에 반영한다. 체결 증가 시 기존 평균 체결가/금액/비용으로 새 수량을 계산하지 않고 미대사 값을 null로 둔다. 원 pending entry confirmation은 archive에 보존하고 종료 후 제거하여 다음 cycle에서 낡은 intent를 제출하지 않는다. 기존 entry signal 완료 횟수는 한 번만 증가하며 다음 신호/cooldown/cap/모든 safety는 유지한다. 테스트에서 원 BUY10+추가 BUY 최종2=SELL1+11을 확인했으나 이는 임시 원장의 수량 검증이지 실체결·실수익이 아니다.

공식 API gate: 구현 전 `2026-09-10T10:30:52+09:00` [공식 upstream](https://github.com/Kiwoom-Securities/Kiwoom-REST-API)의 HEAD와 검증 checkout SHA `234560d213acd8871ae344b5481aecd2f30287fa` 일치를 재확인했다. 이 revision에는 `kiwoom_docs`가 없다. `kiwoom/specs.py`, `kiwoom/core/client.py`, packaged `kiwoom/_data/kiwoom_api_spec.json`의 `kt10003/kt00007/ka10075` request/response 및 Postman PRD/MOCK를 대사했다. Postman query 예시와 별도로 공식 JSON POST·headers를 유지하며, 0-quantity cancel·market order·자동 write retry·한도 상향은 사용하지 않는다. 실제 auth/API/계좌·주문을 호출하지 않았다.

재리뷰 보완: ordinary 원장에는 아직 SUBMITTED이지만 registry/WS에는 full-fill이 먼저 반영된 경우도 같은 exact root를 조회해 닫는다. 원장 간 도착 순서 차이만으로 후속 청산을 영구 차단하지 않되 terminal WS만으로 BUY source proof를 발행하지 않는다. 별도 full-fill/WS terminal 두 반례와 0-fill 전량 취소를 검증 목록에 추가했다. 지원 상태는 ordinary SUBMITTED의 exact 원 owner이며 unknown/legacy 상태를 확장 정규화하지 않는다.

최종 검증 receipt `2026-09-10T11:02:47+09:00`: **2088 PASS / 4 owner-비대상 SKIP / 156.84초**. §13과 동일한 전체 직접 영향 명령(`test_machine_adaptive_exit_*.py` 전부, turnover/attribution/approval·widget·low-price/Samsung4경로/3 preflight·owner coexistence·checklist builder)을 마지막 코드 세대로 재실행했다. 새 BUY/actual widget pending 전용64개는 이 합계에 포함하며 최초61 PASS·중간2085/2086 PASS 및 이전§13의2024 PASS와 합산하지 않는다. 첫 전용 검증의 예외 유형 기대값 오류1건은 SELL scope 차단의 직접 예외로 테스트를 바로잡았고, 후속 full-fill 선도착 코드 보완 뒤 이전 PASS를 재사용하지 않았다.

`korstockscan-review-gate`로 원 ordinary BUY/entry intent→frozen request→BUY-only transport/registry→전체 closed census/SELL→ordinary archive와 SELL/독립 episode 회귀를 리뷰/보완/재검증해 **이번 지원된 위젯 pending BUY·late fill·수량 종료 consumer 범위 finding0**으로 닫았다. Ruff·Black check·compile·`git diff --check` 및 print-only parser28개/당일12개/해당 owner1개/중복 title0 통과. 아래9개 코드/테스트 hash를 최종 전체 검증 뒤 재대사해 동일함을 확인했다. 테스트의20주 최대값/독립 승인 callback은 격리 fixture의 명시적 bound이며 실제 기존 cap을 올리거나 운용 승인값으로 사용하지 않는다. main/WS/recheck 등 병행 사용자 변경은 이번 검증/배포 범위에 포함하지 않는다.

자연 원천 읽기 전용 재확인 `2026-09-10T11:01:29+09:00`: source9/9 attribution SHA `b5068924d29491da163a469da05b8634b1528ee5249723012e103d13999e1db5` 불변, `machine_adaptive_exit_source_census_v1`은 `blocked_source_contract`, 경제성 `not_evaluated`다. 새 코드 테스트를 이 원천의 복구/새 자연 표본/경제성 승인으로 표시하지 않는다.

| 최종 검증 대상 코드/테스트 | SHA256 |
| --- | --- |
| `buy_cancel.py` | `3a747cc322decc7e9f963c260ac5a3eb22090e18acc6571e05c07eebab1aff7a` |
| `group_pending_buy.py` | `178bf435815b0f642d856f658c309b7b86f4b236ee8b9f81614b16fb001753e4` |
| `group_settlement.py` | `47afc6f7b45a1e830032de8f62695594235d9b993ea3ee99235aa4329e283eb9` |
| `group_whole_exit.py` | `b01e67479021e4f070e01cb83e7f069b8ebc0954666d5cb1cb995ef3c1ebe946` |
| `broker.py` | `08205ad3b0182c626113e083a4b24b54d827d98f322898f08553e3f7a8a7ee1a` |
| `owner_custody_registry.py` | `bf5b316657ed6c11c27a11c6224c404aba48863e281164d964718964594ae81e` |
| `widget_auto_trade/engine.py` | `9cb304126c76ff4ae3ca6ba4b436b3e3aa2f066a34664a2afa348aed09fd64b4` |
| `test_machine_adaptive_exit_buy_cancel.py` | `4ab260701341e3fb12ef632bebe1923ddd94dae8768f3d63207f0de7801305ea` |
| `test_machine_adaptive_exit_group_pending_buy.py` | `81b763f21d1c514137f3cd4a9ffdacc4e8297c536882b1a6c5e75fc57c8c01ad` |

잔여는 **연구 whole/선택적 lot 판단의 정책 중재, 기존 target를 이미 취소한 baseline scale-in/legacy intent의 명시적 복구, 독립 episode pending BUY 연결·전일/거절/0확인 복구, 독립 envelope/시장·가격 validator·PREOPEN 발행/enrollment/실제 launcher, 자연 lot/path·paired 경제성·정산**이다. 지원된 위젯 pending BUY 연결을 이 잔여 전체의 완료로 확대하지 않는다. 단일 owner/기존 bound가 남은 수량을 감당하지 못하면 cap을 올리지 않고 recovery로 둔다. source9/9 결손 원천은 재생성하지 않았다. 정책/env/PID/운영 custody/주문·report·Provider·외부 sync·commit/push는 변경/실행하지 않았다. 실제 계좌 운용과 최종 live 기동은 사용자 실행으로 분리하며, 같은 `MachineLifecycleTurnoverObjectiveFollowup0910`의21:30~21:40 자연 acceptance는 OPEN이다.

## 15. 독립 episode 전량체결 sibling 연결

전체 활성화 목표는 계속 `active`다. 이번 범위는 **한 leg의 적응형 청산 등록 뒤 다른 leg의 자연 전량체결까지 `BUY_OPEN`으로 영구 대기하던 연결 결손**이다. 공통 two-leg owner에서 exact BUY 최종 수량·가격 확인→해당 leg의 `POSITION_OPEN` 원자 저장→다음 loop의 그 leg 원래 목표주문으로 연결했다. 위젯 shared-target와 독립 episode 두 target를 합치지 않고, 적응형 청산에 등록된 lot/정책/수량은 바꾸지 않는다. 신규 BUY·자동 재진입·미지원 부분체결 취소를 추가하지 않았다.

- 새 broker 읽기 계약은 `reconcile_priced_full_buy`다. 기존 bounded `kt00007.sell_tp=2`/`ka10075.trde_tp=2` exact date/route/원주문 대사에 더해 `F=Q, R=0`, 취소·정정 descendant 부재와 하나로 일치하는 양수 `cntr_uv`를 요구한다. 공식 체결단가는 기존 목표가격 계산 입력일 뿐이며 실제 총금액·평균원가·수수료·세금·실현손익으로 확대하지 않는다. missing/0/음수/소수/충돌 가격, 부분체결·취소 뒤 잔량0은 추정 가격이나 0으로 메우지 않는다. 새 method는 broker read-only이며 BUY/SELL/cancel을 호출하지 않는다.
- 실제 consumer는 동일 episode/leg의 기존 `NEW:BUY:route:attempt` client intent·registry root·주문일/수량/route와 ordinary 원장을 결속한다. 미확인/기존 cancel intent, 미제출 PLANNED, BUY_SUBMITTING/BUY_CANCEL_PENDING, 전일 원주문은 이 전량체결 경로로 정규화하지 않는다. 기존 cancel-all 수량0/재시도나 Samsung 오전 NXT→SOR 재진입을 호출하지 않는다. 검증된 원 BUY 최종 F와 가격/source hash·원 target 가격을 별도 self-hash receipt에 기록하고, 실제 최초 체결시각·비용을 만들어내지 않는다. first-fill은 현재 **관측** 시각으로만 기록한다.
- 복구 loop에서는 target/cancel/SELL을 쓰지 않는다. 저장 후 다음 loop가 그 leg의 원래 `_submit_target`을 사용한다. receipt/hash·원 target 가격이 달라지거나 날짜가 바뀌면 새 target을 제출하지 않는다. 선택된 adaptive lot의 frozen session은 유지하며 새 sibling을 연구 lot나 승격 표본에 자동 등록하지 않는다.
- 재리뷰 보완: 서비스 누락/승인 상실이 adaptive 단계에서 반환됐어도 뒤의 unselected target 경로로 진행할 수 있던 경계를 막았다. 공통 owner와 Samsung 오전 override 모두 target 예약 전·예약 저장 후 실제 wire 직전에 원 잠금/동결 승인·owner veto를 재확인한다. 조회 중 BLOCKED·미확인 entry·registry reconciliation veto가 생겨도 전량체결 projection의 aggregate 갱신으로 지우지 않는다. 저장 전 실패와 publish 후 directory-fsync 오류 모두 재시작 시 중복 조회/목표주문을 만들지 않는지 확인한다.

위치 gate: 기존 `adaptive_exit/broker.py`, `buy_cancel.py`, 공통 `regular_two_leg_machine.py`와 Samsung 오전 override를 수정하고, 새 직접 consumer 테스트를 `src/tests/test_machine_adaptive_exit_episode_sibling.py`에 두었다. 새 engine-root 모듈·producer·service·trigger는 없다.

공식 API gate: `2026-09-10T11:07:51+09:00` upstream HEAD와 기존 검증 checkout의 SHA `234560d213acd8871ae344b5481aecd2f30287fa` 일치를 재확인했다. `kiwoom/specs.py`, `kiwoom/core/client.py`, packaged spec의 `kt00007/ka10075/kt10003` 및 Postman PRD/MOCK를 읽었다. 이 revision에는 `kiwoom_docs`가 없다. `cntr_uv`는 공식 원 단위 체결단가이며 다중 가격을 임의 평균하지 않는다. JSON POST·side 필터·연속조회/한도·실/모의 분리를 유지한다. 실제 auth/API/계좌 호출은 실행하지 않았다.

최종 검증 receipt `2026-09-10T11:28:20+09:00`: **2133 PASS / 4 owner-비대상 SKIP / 226.84초**. §14와 같은 직접 영향 전체 명령(`test_machine_adaptive_exit_*.py`, turnover/attribution/approval·widget·low-price/Samsung4경로/3 preflight·owner coexistence·checklist builder)을 마지막 코드 세대로 재실행했다. 이번 신규45개(가격 대사14·실제 episode consumer31)는 이 합계에 포함한다. 중간2130 PASS는 실행 중 veto 보완 전 세대이고, 전용90 PASS도 부분집합이므로 합산하거나 최종 전체 검증을 대신하지 않는다. Ruff·Black check·compile·`git diff --check` 통과. 문서 print-only parser28개/당일12개/해당 owner1개/중복 title0을 확인했다.

`korstockscan-review-gate`로 producer의 side/date/price source→registry BUY proof→원자 sibling 원장→기존 target consumer·Samsung 오전 override와 잠금/권한·source gap·silent fallback·단일 owner 회귀를 리뷰/보완/재검증하여 **이번 지원된 자연 full BUY sibling 연결 범위 finding0**으로 닫았다. 이는 아래 미지원 복구·실제 서비스/정책 공급·자연 소비·경제성의 완료가 아니다. 최종 세대 hash는 다음과 같다.

| 최종 검증 대상 코드/테스트 | SHA256 |
| --- | --- |
| `adaptive_exit/broker.py` | `2e3cb1701cfecf0ac95a6e28b8d0e0a49310b3235fa9daa2e6cd77e9280d9e69` |
| `adaptive_exit/buy_cancel.py` | `e734a6ec3f4fb8c073fd86ca145a9da656030ef7108e9c75c1a58d1248c438a6` |
| `regular_two_leg_machine.py` | `a3558d1690bb2809474d11637b0ba4e6a5c330e046c979b8c588e95b0d9e4ddb` |
| `samsung_morning_one_share/machine.py` | `07fcd4d34f84f5a43949678ba2290c21b46267e946838851936f3ce3821f7cb5` |
| `test_machine_adaptive_exit_buy_cancel.py` | `e934c18abc5023673269df1589fca6bf1bdc6c3d3529287b78dca7b814e7a1e4` |
| `test_machine_adaptive_exit_episode_sibling.py` | `b21d443dde1823e978f268f13ae5b9734823410287f4593a839234db109c4079` |

자연 원천 읽기 전용 재확인 `2026-09-10T11:25:35+09:00`: source9/9 attribution SHA `b5068924d29491da163a469da05b8634b1528ee5249723012e103d13999e1db5` 불변, adaptive child `status=blocked_source_contract`, `economic_acceptance=not_evaluated`, `net_ev_pct=null`, `policy_promotion_candidates=[]`. 새 자연 체결이나 연구 입력이 생겼다고 보고하지 않는다. 병행 main/WS/recheck 및 테스트 공통 fixture의 사용자 변경은 이번 구현/배포의 귀속이 아니다.

잔여: **부분체결/기존 취소/거절/0확인·전일 및 baseline 선행 target 취소 복구, 연구 whole/선택적 lot 정책 중재, 독립 envelope/validator·PREOPEN 발행/enrollment/실제 launcher, 자연 lot/path·paired 경제성·정산**. 자연 전량체결 경로의 연결은 이 전체 잔여의 완료가 아니다. 원천 source9/9 결손을 재생성/정상화하지 않았고 정책/env/PID/운영 custody/실주문·Provider·외부 sync·commit/push를 변경/실행하지 않았다. 최종 실계좌 운용/기동은 사용자 실행이며, 기존 `MachineLifecycleTurnoverObjectiveFollowup0910` 21:30~21:40 자연 acceptance는 OPEN이다.

## 16. 독립 episode 부분체결 BUY 취소와 원 target 연결

전체 활성화 목표는 `active`다. 이번에는 **적응형 청산 등록 leg 옆의 기존 BUY_OPEN leg를 원래 부분체결 잔량/진입 유효기간 사유로 취소하고, 양수 취소 확인과 최종 실제 체결단가·수량을 원자 저장한 뒤 그 leg의 기존 target owner로 넘기는 연결**을 구현했다. 두 10주 leg의 원 수량·등록된 adaptive lot·target/연구 분모를 합치지 않는다. 위젯 shared-target 전체 청산과도 독립이다.

- 위치 gate: 새 `src/trading/order/adaptive_exit/episode_pending_buy.py`는 기존 주문 owner의 bounded journal/consumer다. `OwnerLoopServices.pending_buy`는 기본 없음이며 실제 launcher가 독립 원 owner 승인 callback과 명시적인 확인 기한을 공급해야 한다. 테스트의5000ms는 격리 fixture 값이지 승인된 운용값/새 holding 손실 기준이 아니다. 새 engine-root/producer/cron/service는 없다.
- 최초 읽기→원 ordinary leg hash/immutable BUY context·주문일/route/Q/session binding→동일 state 파일 `INTENT_SAVED`→양수 정확 잔량 취소→`ACK_SAVED`→BUY/child 최종 proof→`PROJECTED`로 연결한다. 기존 regular owner의 completed-bar expiry와 Samsung 오전의 route deadline을 사용하며 부분체결은 기존 `partial_fill_remainder` 사유다. cancel-all 수량0·신규 BUY·임의 조기 유효기간·수량 합산은 없다.
- 취소 직전 추가 체결로 잔량이 변하면 예약 전 요청을 멈추고 같은 action/원 기한 안에서 새 정확 잔량을 확인한다. 이때 전량 체결되면 취소 없이 full BUY로 회수한다. 반면 registry 예약 이후 ACK/timeout/거절/불명확/누락 child는 새 ID나 재시작으로 재전송하지 않는다. 확인 기한이 지나면 조회도 멈추고 명시적 owner recovery로 남긴다.
- 새 `reconcile_priced_terminal_cancel`은 기존 side-specific BUY parser/원자 registry proof에 체결단가 검증을 추가한다. `Q=최종 F+확정 C`, root/child terminal·현재 미체결 부재, 양수 `cnfm_qty`·확인시각과 하나로 일치하는 양수 `cntr_uv`를 요구한다. F=0일 때 가격은 null이다. 원 체결시각/총금액/평균원가/비용/실현손익을 새로 만들어내지 않는다. late fill 때문에 요청8·확정6·최종F4인 경우 F4/실제 단가만 같은 leg의 목표 계산에 사용한다.
- 재리뷰 보완: 취소 의도 저장 뒤 자연 full-fill race, 초기 leg/현재 state 객체/잠금·승인 교체, 조회 중 기한 초과, ACK 뒤 registry 소실과 nested journal 오염을 차단했다. projection 및 원 target 예약 전후에 같은 session/원 BUY root·취소 child terminal proof와 frozen source hash를 다시 대사한다. 저장 전·publish 후 fsync 오류 뒤 재시작도 취소/target 중복 없이 이어지는지 검사했다.
- SOR의 확정 F0는 `NO_FILL`이지만 Samsung 오전 NXT F0는 기존 SOR fallback을 생략해 종료하지 않는다. 현재 `pending_buy_zero_fill_original_nxt_fallback_handoff_required`로 유지하며 **이 fallback의 실제 다음 진입 연결은 아직 미완료**다. 기존 legacy 취소/전일/거절/0확인·deadline 이후 복구를 성공으로 정규화하지 않는다.

공식 API gate: 구현 전 `2026-09-10T11:33:21+09:00` upstream HEAD와 검증 checkout의 SHA `234560d213acd8871ae344b5481aecd2f30287fa` 일치를 재확인했다. `kiwoom/specs.py`, `kiwoom/core/client.py`, packaged spec `kt10003/kt00007/ka10075` request/response와 Postman PRD/MOCK를 대사했다. 이 revision에는 `kiwoom_docs`가 없다. 기존 JSON POST·BUY side2/원주문일·exact route/최대3page·공유 한도를 유지한다. 실제 auth/API/계좌·주문은 호출하지 않았다.

최종 검증 receipt `2026-09-10T11:57:37+09:00`: **2199 PASS / 4 owner-비대상 SKIP / 165.90초**. §15와 동일한 직접 영향 전체 명령(`test_machine_adaptive_exit_*.py` 전부, turnover/attribution/approval·widget·low-price/Samsung4경로/3 preflight·owner coexistence·checklist builder)을 마지막 코드 세대로 재실행했다. 신규66개(BUY 가격12·실제 pending consumer/계약54)는 이 합계에 포함한다. 전용156 PASS와 이전§15의2133 PASS는 별도 가산하지 않는다. 초기 테스트의 JSON roundtrip tuple/list 비교·간접 fixture 지정 문제와 full-fill race의 없는 cancel proof hash 처리 결함을 수정한 뒤 재검증했다. 마지막 코드 세대는 Ruff·Black check·compile·`git diff --check` 통과, 문서 print-only parser28개/당일12개/현재 owner1개/중복 title0 통과다.

`korstockscan-review-gate`로 원 expiry/부분체결 사유→BUY 전용 가격/취소 source→side-specific 원자 registry proof→durable leg journal→기존 target/동결 session·Samsung 오전 consumer를 리뷰/보완/재검증하여 **이번 지원된 독립 episode partial/expired BUY 연결 범위 finding0**으로 닫았다. NXT F0 fallback과 아래 미지원 복구·실제 launcher·자연/경제성의 완료는 아니다. 병행 main/WS/recheck/restart 등 사용자 변경은 이번 검증/배포 귀속에 포함하지 않는다.

자연 원천 읽기 전용 확인 `2026-09-10T11:56:19+09:00`: source9/9 attribution SHA `b5068924d29491da163a469da05b8634b1528ee5249723012e103d13999e1db5` 불변. adaptive child는 `status=blocked_source_contract`, `economic_acceptance=not_evaluated`, `net_ev_pct=null`, `policy_promotion_candidates=[]`다. 새 자연 source/실체결·수익으로 재라벨링하거나 같은 원천을 재생성하지 않았다.

| 최종 검증 대상 코드/테스트 | SHA256 |
| --- | --- |
| `adaptive_exit/episode_pending_buy.py` | `d88d729c5483e0315f1077b098f64ac9e151f4e28c432f6cb419b7399f15c021` |
| `adaptive_exit/broker.py` | `8884f70fe8403e4a77d949f7dcca40e38afdaa77b5424146fddc5a8a9baeb88a` |
| `adaptive_exit/buy_cancel.py` | `5e234fb6481c8a70444b98efdee9914408ba9b38a3926f7f3e6ef97c5b05895c` |
| `adaptive_exit/owner_loop.py` | `64d2e65c0d94815cb722869b1faaf0d6840387c6ddb1916afb7ee1d3c648b783` |
| `regular_two_leg_machine.py` | `b78ec48d48bf92fdfb60e5d3c3d2b7c22f6fb8b199146eb92ac0a9d2389d1abf` |
| `samsung_morning_one_share/machine.py` | `0f81a4c50cbdb84ffa3ca6e4120865ac01d82310e4b00824a3141ffca5b36e19` |
| `test_machine_adaptive_exit_episode_pending_buy.py` | `81e4991dd2ef73417f8fb585e7bbe3dd9dbcf18ace6cc220fef6d24b357375b2` |
| `test_machine_adaptive_exit_buy_cancel.py` | `0d30bb1b1942a30d9389747950153f858ac2dd76f383b681a304e7be060ea732` |

잔여는 **NXT F0의 기존 fallback/다음 진입 handoff, legacy/전일/거절/0확인·기한 경과 및 baseline 선행 target 취소 복구, 연구 whole/선택적 정책 중재, 독립 numeric envelope/시장·가격·clock·safety validator/PREOPEN 발행/enrollment/실제 launcher, 자연 lot/path·paired 경제성/정산**이다. 이번 코드 범위를 전체 활성화로 보고하지 않는다. 운영 정책/env/PID/custody/실주문·report/Provider·외부 sync·commit/push는 변경/실행하지 않았고 최종 실계좌 운용·기동은 사용자 실행으로 분리한다. 현재 `MachineLifecycleTurnoverObjectiveFollowup0910` 21:30~21:40 자연 acceptance는 OPEN이다.

## 17. NXT 무체결 종료와 기존 SOR fallback 연결

전체 활성화 목표는 `active`다. §16에서 남긴 **Samsung 오전 NXT BUY의 확정 F0 종료→원 SOR 시간창/진입 guard→새 SOR 원주문→기존 target**을 opt-in으로 연결했다. 이는 기존 오전 owner의 fallback 복구이며 새 adaptive 진입 규칙이나 현재 보유 이관이 아니다. 다른 등록 leg의 NXT session/원 target·수량은 그대로 유지한다.

- 위치 gate: `src/trading/order/adaptive_exit/episode_sor_fallback.py`는 기존 주문 owner의 journal/consumer이며 신규 engine-root·producer·service가 아니다. 실제 `OwnerLoopServices.pending_buy`/독립 승인 공급 전에는 비활성이다.
- 정확한 NXT root/양수 취소 child terminal·Q=F0+C proof를 가진 원 leg 전체와 정책/hash를 동결 archive한다. SOR 상태로 옮길 때 원 NXT 주문/취소 증거를 지우거나 SOR 체결로 재라벨링하지 않는다. 현재 소비 시에도 원 registry proof·정책·당일·route/session·leg 수량·후속 attempt를 다시 검증한다.
- 기존 `_move_to_sor`와 `_submit_planned_buys`를 직접 재사용한다. 원 SOR open 전에는 조기 제출하지 않으며, 정해진 창에서 기존 opening price/확인/시장약세/유동성·속도 및 gateway safety를 사용한다. 신규 가격/수량/시간창을 만들지 않는다. 창이 끝난 미제출 leg는 원 `NO_FILL`이고 늦은 보상 매수는 없다. 정상 SOR 대기/BUY 유효기간 대기는 다른 등록 adaptive leg의 관리까지 막지 않는다.
- 후속 BUY는 동결된 하나의 native `BUY:SOR:attempt` slot과 별도 submit plan으로 결속한다. 예약 전/후에 독립 승인·원 잠금·현재 owner snapshot/정책·durable state를 재검증한다. 예약/승인 후 저장 실패나 `AUTHORITY_BLOCKED`를 새 attempt/재전송으로 바꾸지 않는다. 어떠한 durable intent/전송도 없었던 publish 전 실패만 원 미제출 상태로 남는다.
- 재리뷰 보완: 실제 오전 constructor의 fresh leg가 loader read-back 기본 필드와 달라 권한 검사를 실패시키는 결함을 공통 `_new_leg` 기본값 재사용으로 고쳤다. 상위 `BLOCKED` 보존, 승인 callback 중 state/신호/다른 leg 변경, 원 증거 삭제 후 재hash, 잘못된 submit schema/route/시각·가격과 NXT/SOR session 혼합을 차단했다. 가짜 gateway/임시 원장으로 저장 전·publish 후 fsync 실패와 재개, 기존 guard 상실, 새로운 SOR full fill→그 leg의 기존 target을 검사했다.

공식 API gate: 구현 전 `2026-09-10T11:59:57+09:00` upstream HEAD와 checkout SHA `234560d213acd8871ae344b5481aecd2f30287fa` 일치를 확인했다. 이 revision에 `kiwoom_docs`는 없다. `kiwoom/specs.py`, `kiwoom/core/client.py`, packaged `kt10000/kt10003/kt00007/ka10075` request/response 및 Postman PRD/MOCK를 열람했다. 기존 JSON POST `/api/dostk/ordr`, normal limit `trde_tp=0`·양수 수량/가격·exact route와 날짜별 BUY side2·양수 취소/확인 계약을 유지한다. upstream 시장가 예제/인증 retry를 복사하지 않았고 실제 인증/API·계좌·주문은 호출하지 않았다.

최종 검증 receipt `2026-09-10T12:29:25+09:00`: **2249 PASS / 4 owner-비대상 SKIP / 169.74초**. §16과 동일한 직접 영향 전체 명령(`test_machine_adaptive_exit_*.py` 전부, turnover/attribution/approval·widget·low-price/Samsung4경로/3 preflight·owner coexistence·checklist builder)을 마지막 코드 세대로 재실행했다. 신규 전용50개는 합계에 포함하며 전용50 PASS/7.70초, 중간2245/2248 PASS와 이전§16의2199 PASS를 가산하지 않는다. 예약 조회 사이 원장이 사라지는 반례도 명시적 recovery 오류로 처리하며 attribute exception으로 manager를 잃지 않도록 보완했다. 최초 fixture aggregate 불일치/tuple-list 비교와 circular import는 보완 후 재검증했다.

`korstockscan-review-gate`로 원 NXT terminal/registry proof→동결 fallback/정책→기존 SOR 진입 guard/예약·durable read-back→새 BUY reconciliation/그 leg 원 target 및 다른 adaptive lot 관리를 리뷰/보완/재검증했다. **이번 지원된 같은 날 오전 fallback 연결 범위 finding0**이다. Ruff·Black check·compile·`git diff --check` 통과, 문서 print-only parser28개/당일12개/현재 owner1개/중복 title0이다. 코드 해시는 마지막 전체 회귀 전후 불변이며 아래 미완료 경로·실제 서비스/정책·자연/경제성의 PASS로 확대하지 않는다.

| 최종 검증 대상 코드/테스트 | SHA256 |
| --- | --- |
| `adaptive_exit/episode_sor_fallback.py` | `8d24ef1cc7617f6bd1a67516a1991762d91f33994579de4d73d017d99e969d89` |
| `adaptive_exit/episode_pending_buy.py` | `0e082ad9ce73fc30ca8d232b0aa6bbf23c3de2c1bbce925985b1ead5295dc3ae` |
| `regular_two_leg_machine.py` | `fa3143cb907076e814474b95d35e189c09a76cc3588857e7088bd915812fad9f` |
| `samsung_morning_one_share/machine.py` | `3f75a717e4312fa47c7c12c2f93054f8fe88625d5318e0f774ce099a64918ab6` |
| `test_machine_adaptive_exit_episode_sor_fallback.py` | `2c79d292d24fb87df12885095d7acbae50c42f8751451a33b73dd2f2cf6decef` |

자연 원천 읽기 전용 재확인 `2026-09-10T12:27:54+09:00`: source9/9 attribution SHA `b5068924d29491da163a469da05b8634b1528ee5249723012e103d13999e1db5` 불변. `rolling_policy_research_v2`의 `machine_adaptive_exit_source_census_v1`은 `blocked_source_contract`, `economic_acceptance=not_evaluated`, `net_ev_pct=null`, `policy_promotion_candidates=[]`다. 재생성/과거 시각 합성·새 자연 표본/경제성 승인은 하지 않았다.

잔여는 **legacy/전일/거절/0확인·기한 경과 및 baseline 선행 target 취소 복구, 연구 whole/선택적 정책 중재, 독립 numeric envelope/시장·가격·clock·safety validator/PREOPEN 발행/enrollment/실제 launcher, 자연 lot/path·paired 경제성/정산**이다. 과거 NXT F0 전체 미연결 기록은 이번 지원된 같은 날 오전 fallback 범위에서만 갱신한다. 최종 실계좌 기동/운용은 사용자 실행으로 분리하며 같은 `MachineLifecycleTurnoverObjectiveFollowup0910` 자연 acceptance는 OPEN이다. 병행 main/WS/recheck/restart 등 사용자 변경은 이 작업의 검증/배포 귀속에 포함하지 않는다.

## 18. 확인 기한 경과 BUY의 bounded terminal-only 복구

전체 활성화 목표는 `active`다. §17까지 남았던 **원 BUY 확인 기한 이후, 같은 날의 확정 terminal→그 leg 원 target 또는 NXT F0→기존 SOR fallback**을 지원한다. 미체결/기한 경과를 자동 완료로 바꾸지 않으며 이 복구 경로에서 새 취소·대체주문을 제출하지 않는다. 최종 실계좌 기동/운용은 사용자 실행으로 분리한다.

- 위치 gate: 새 `src/trading/order/adaptive_exit/episode_buy_recovery.py`는 기존 주문 owner의 복구 helper이고, producer/daemon/engine-root/launcher가 아니다. 기존 `EpisodePendingBuyServices`에 optional `TerminalRecoveryServices`를 결속한다. 기본값은 비활성이고 독립 승인 callback·조회 횟수/최소 간격/고정 window를 모두 명시해야 한다. 테스트의2회/1000ms/10000ms는 fixture 값이지 승인된 운영 수치가 아니다.
- 원 journal의 action ID·취소 수량·확인 deadline을 변경하지 않는다. 복구 종료는 **원 확인 deadline + 명시적 window**이며 첫 늦은 점검/재시작 시각으로 새로 계산하지 않는다. 횟수는 기존 bounded account read 한 묶음당 broker I/O 전에 원자 저장한다. 개별 page/TR cap·공통 API budget/continuation 계약은 그대로다. 조회 간격/횟수/기한 소진·잘못된 clock은 명시적 대기/복구 잔여이며 새 취소 슬롯을 만들지 않는다.
- 기존 `kt00007` dated BUY/취소 child와 `ka10075` 현재 원천을 같은 owner/route/day/원주문에 결속한다. ACK나 현재 부재만으로 terminal을 인정하지 않는다. 등록된 양수 취소 child의 최종 F+C/단가 proof 또는 취소 미전송 journal의 자연 full BUY proof만 원자 projection한다. 부분 open·가격 결손/충돌·0확인·거절/불명 ACK·전일 원천은 정상 terminal로 보간하지 않는다.
- direct consumer는 기존 공통 episode loop/그 leg의 원 target과 Samsung 오전 SOR fallback이다. 현재 서비스 identity·원 잠금/owner veto·frozen policy와 ordinary state를 조회/원장 대사/저장 때 재확인한다. 복구 모드의 write guard는 무조건 새 취소를 차단한다. 승인 callback의 마지막 clock 역행도 차단하며 실제 관측시각을 과거 체결시각으로 쓰지 않는다.
- 리뷰에서 **publish 후 fsync 실패→오래된 메모리로 조회 횟수/terminal proof 덮어쓰기** 결함을 보완했다. schema/clock/권한 오류의 상태 저장보다 먼저 durable leg를 검사하고, 차이가 나면 typed reload-required 결과만 반환하여 운영 state를 쓰지 않는다. 저장 전 실패·publish 후 실패·재로딩·기한 소진·clock 역행·권한 상실 조합을 검증한다. 자동으로 custody를 재구성하거나 새 계좌 조회로 실패를 덮지 않는다.
- projection의 recovery hash/고정 contract/조회 시각·횟수는 다음 원 target consumer도 다시 검증한다. F0는 `NO_FILL` 또는 원 오전 fallback이며 비용/경제성은 null/미대사 상태다. NXT 늦은 F0 이후 SOR 새 BUY와 다른 등록 leg의 기존 SELL 관리도 서로 다른 주문번호로 검증한다. 다른 leg의 기존 target 취소를 pending BUY 재시도로 집계하지 않는다.

공식 API gate: 구현 전 `2026-09-10T12:31:20+09:00` upstream HEAD/checkout SHA `234560d213acd8871ae344b5481aecd2f30287fa` 일치를 확인했다. 이 revision에는 `kiwoom_docs`가 없다. `kiwoom/specs.py`, `kiwoom/core/client.py`, packaged `kt00007/ka10075/kt10003`의 request/response 전 필드와 Postman PRD/MOCK를 읽었다. JSON POST/header/side2/dated/current·양수 확인/가격/route/continuation과 기존 API bound를 유지하며 upstream 인증 retry/취소0/시장가 예제를 실행 경로로 복사하지 않았다. 실제 auth/API·계좌·주문을 호출하지 않았다.

코드 검증 receipt 확인 `2026-09-10T12:54:40+09:00`: **2308 PASS / 4 owner-비대상 SKIP / 173.74초**. §17과 동일한 전체 영향 명령을 마지막 코드 세대로 실행했다. 신규 recovery58개·기존 오전 fallback에 추가한1개는 전체에 포함하고, 중간 전용162 PASS·마지막 clock 반례1 PASS 및 이전§17의2249 PASS를 가산하지 않는다. 초기 테스트의 잘못된 권한 fixture key·격리 registry 충돌과 다른 leg의 SELL 취소를 BUY 재시도로 집계한 기대값을 수정했으며 실제 guard를 완화하지 않았다.

`korstockscan-review-gate`로 journal/독립 권한→고정 bounded read→기존 broker/registry proof→원자 projection→원 target/SOR consumer·저장 실패 재개 경계를 재리뷰하여 **이번 지원된 같은 날 terminal-only 복구 범위 finding0**이다. Ruff·Black check·compile·`git diff --check` 통과. 아래5개 코드/테스트 hash는 마지막 전체 회귀 전후 불변이다. 문서 print-only parser29개/당일13개/해당 owner1개/중복 title0, 신규§18 링크5개 존재·표준 sync 명령1개를 확인했다. 이전 parser28/당일12개는 이전 관찰값이며 병행 checklist 변경을 되돌리지 않았다. 운영 활성화·미지원 예외·자연/경제성은 이 검증의 완료 대상이 아니다.

| 검증 대상 코드/테스트 | SHA256 |
| --- | --- |
| `adaptive_exit/episode_buy_recovery.py` | `1281bd052628e3c989a6fd2182d84689c386fd728b0c71a5ca377833b1d864f0` |
| `adaptive_exit/episode_pending_buy.py` | `c8193ee4b476687bf57af10ff4cd801ef782f16aa88fbf29647a6a230cdc54c6` |
| `regular_two_leg_machine.py` | `c8d956ef0fb726174ff0777e9ddf8471f001953825fee2387c331b1c26bb2b22` |
| `test_machine_adaptive_exit_episode_buy_recovery.py` | `2e7ed27a97170c3ef2b463d74f32a5ab5854414c0164d054caeadfc90392517d` |
| `test_machine_adaptive_exit_episode_sor_fallback.py` | `15f0bc7827a9f26a135ba43a076be251db1a04b3edc88d0505322843f92526bf` |

자연 원천 읽기 전용 재확인 `2026-09-10T12:51:06+09:00`: source9/9 attribution SHA `b5068924d29491da163a469da05b8634b1528ee5249723012e103d13999e1db5` 불변. `rolling_policy_research_v2`는 `machine_adaptive_exit_source_census_v1`/`blocked_source_contract`, `economic_acceptance=not_evaluated`, `net_ev_pct=null`, `policy_promotion_candidates=[]`다. 이번 복구 fixture를 신규 자연 source/체결·경제성 pair나 정책 승인으로 쓰지 않는다.

잔여는 **legacy/전일/거절·불명 ACK/0확인 및 새 복구 budget/window 밖·baseline 선행 target 취소 복구, 연구 whole/선택적 정책 중재, 독립 numeric envelope/시장·가격·clock·safety validator/PREOPEN 발행/enrollment/실제 launcher, 자연 lot/path·paired 경제성/정산**이다. 위§17의 기한 경과 전체 미연결은 이번 지원된 같은 날 bounded terminal 범위에서만 갱신한다. 운영 정책/env/PID/custody/기동·실주문·report 재생성/Provider·외부 sync·commit/push는 실행하지 않았다. 병행 main/WS/recheck 등 사용자 변경은 보존하고 이번 검증/배포 귀속에 포함하지 않는다. 현재 `MachineLifecycleTurnoverObjectiveFollowup0910` 21:30~21:40 자연 acceptance는 OPEN이다.

## 19. 중간 점검과 개발·운영 세션 분리

사용자는 남은 단계와 과도한 구현 여부를 점검하고 **이 세션은 개발을 계속하되 배포·재기동·운영 설정 변경은 다른 세션에서 진행**하도록 명시했다. `2026-09-10T12:56:32+09:00` 현재 코드/원천을 읽고 아래 우선순위로 재정리했다. 전체 종목·프로필 지원 목표와 선택 위임을 유지하며 같은 선택 질문을 반복하지 않는다. 기존 보유 자동 이관이나 운영 적용을 이번 개발에 포함하지 않는다.

### 중간 판정

**안전 핵심 구현은 필요했으나, 복구 예외의 수평 확장이 실제 활성화 경로 연결보다 앞선 부분은 과도했다.** 단일 writer, exact 수량·취소 child proof, late fill, 저장 후 장애/중복 주문 방지는 삭제하거나 테스트를 완화할 영역이 아니다. 반면 모든 legacy·미정의 broker 응답을 자동 복구하는 범용 엔진, 모든 혼합 정책/연구 조합, 과거 경제성 완전 복원까지 첫 활성화의 공통 선행조건으로 둘 이유는 없다. 앞으로 새 helper/예외를 추가하기 전에 아래 필수 단계 또는 선택한 실제 정책의 도달 가능한 분기를 닫는지 확인한다.

직접 근거:

- `machine_adaptive_exit_policy.py`는 아직 research-only이고 `assess_research_evidence`가 PREOPEN eligibility를 항상 false로 반환한다. `machine_adaptive_exit_evidence.build_candidate`도 연구 native 후보까지만 발급한다. 이 false를 단순 true로 바꾸는 수리는 금지다.
- `machine_microstructure_policy_approval.py`의 trusted registry에는 새 exit family가 없다. 계획한 family-owned apply/publisher 모듈도 아직 없으므로 유효 후보가 생겨도 정식 발행·선택·소비 경로가 닫히지 않는다.
- widget/low-price/Samsung 오전·정오·오후 실제 `service.py`의 constructor 호출에는 `adaptive_exit_services` 공급이 없다. production `OwnerLoopServices(...)` 생성 및 신규 position enrollment 호출도 없다. 현재 테스트가 실제 owner class를 사용하는 것은 이 배포·구성 결손을 대체하지 않는다. 오전 SOR 재진입 생성 경로도 같은 공급 대상이다.
- source9/9의 모집단30개는 `source_invalid=30`, 유효0, 연구 evidence/승격 후보0이다. 최초 fill/lot/target epoch·ordered path가 결손이며 과거 원천을 반복 재생성해서 정상화할 수 없다. 실제 정산 결손과 비교비용 기반 연구 EV는 별개다. 이 표본 결손은 코드 연결 개발을 멈출 이유도, 가짜 live 수치를 발행할 근거도 아니다.

### 목표까지 남은 경로와 완료 기준

| 단계 | 현재 상태 / 다음 개발 | 완료 기준 / 실행 세션 |
| --- | --- | --- |
| 1. 최초 정책·승인·선택 연결 | 독립 envelope/평가·실행 readiness validator, family-owned candidate→exact-date publisher→loader 연결 | 유효/무효·만료·다른 source/hash·미지원 scope를 구분하는 end-to-end 테스트. 연구 후보가 스스로 승인하지 않음. **이 세션 코드/임시 fixture만**, 운영 정책 발행 없음 |
| 2. 실제 서비스·신규 편입 연결 | 기존 서비스 entrypoint에 실제 snapshot/clock/owner lock·account/order safety 공급, 신규 position에 정책/hash·원 lot/target을 동결 편입 | widget·Samsung4경로·low-price 공통 profile 소비 검증, 미승인/구 보유는 baseline carry. **이 세션 코드만**, 서비스 기동·설치/운영 env 변경 없음 |
| 3. 선택 정책의 필수 lifecycle 종결 | 기존 구현을 재사용해 정상/partial/취소·late fill/TTL·잔량/원 EXIT와 다음 기존 신호를 통합. 새 편입 position의 세션 종료·익일 잔량 관리 포함 | 원장 보존·한 writer·중복0·잔량 manager 유지·재시작 후 같은 정책을 테스트. 실제 도달 가능한 필수 분기는 해결하고 미정의 source는 명시적 안전 중지/직접 owner handoff |
| 4. 개발 완료·다른 세션 인계 | 하나의 코드 generation으로 관련 end-to-end/회귀·정적 검사, owner별 지원/제외·preflight·rollback·미충족 원천 목록 고정 | **코드/계약 완료와 운영 준비 미충족을 분리한 인계**. 이 세션에서 deploy/start/restart, 운영 설정/원장/정책·주문을 변경하지 않음 |
| 5. 실제 활성화·관측 | 새로운 유효 자연 source/기존 경제성 조건 확인, 검증한 코드 배포/운영 설정·정책 발행·기동 | **다른 세션**에서 같은 date/hash·PID/서비스 load receipt·실제 신규 enrollment 확인. 자연 체결/비용 후 효과는 별도 판정이며 조건 미달을 강제 ON 하지 않음 |

1→2를 다음 개발의 우선 경로로 진행하고, 3의 미결손은 해당 연결에서 실제 도달 가능한 분기 순으로 닫는다. 이미 편입된 잔량이 익일이 됐다는 이유로 manager를 없애는 것은 허용하지 않으므로 이 익일 관리 계약은 필수다. 반대로 **최초 편입 이전 legacy/manual 보유의 자동 이관, provenance가 없는 과거 주문의 추정 복구, 모든 혼합 runner/후보의 자동 거래, 과거 손익 완전 복원**은 첫 개발 완료의 공통 gate에서 제외한다. 해당 상태에 신규 편입/주문을 막고 원 owner의 구체적 복구/알림 경로가 유지되는지는 검증한다. 선택한 정책에서 발생 가능한 잔량/원 target 충돌을 이 제외 목록으로 숨기지 않는다.

검증도 각 수정의 targeted 테스트→기능 연결 단위 전체 회귀로 운영한다. 단순 문서·무관한 변경마다2308개를 반복하거나 테스트 개수를 진척률로 사용하지 않는다. 이 중간 점검은 기존 필수 안전 검사·경제성 계약을 낮추거나 전체 활성화 범위를 임의 축소한 결정이 아니다. 전역 최적 수익 보장, 새 exit 실거래 표본을 최초 기동 이전에 요구하는 순환 gate, 모든 horizon/legacy 결손0 같은 미승인 조건도 추가하지 않는다.

현재 `MachineLifecycleTurnoverObjectiveFollowup0910` 한 항목에 위 개발 경로·운영 세션 분리를 기록했다. 향후 receipt는 변경된 단계와 실제 통과 gate를 기존 기록에 연결하며 신규 중복 owner/정기 producer를 만들지 않는다. **전체 활성화 목표는 진행 중, 이번 세션의 종료 산출물은 개발 검증·운영 인계 준비**로 구분한다. 실제 활성화와 경제성은 다른 세션 receipt 없이 완료 처리하지 않는다.

## 20. 초기 승인 후보의 독립 검증·발행·로딩 연결

`2026-09-10T13:18:00+09:00` 코드/정적 검사 receipt. §19에서 정한 활성화 연결을 우선하여 다음 세 파일을 추가했다. 위치는 연구 계약과 분리된 `src/trading/config`의 적용 검증/로딩 owner, 계획된 `src/engine/automation`의 발행 owner, `src/tests`다. engine root·신규 연구 producer·정기 trigger는 추가하지 않았다.

- `machine_adaptive_exit_activation.py`: `machine_adaptive_exit_initial_approval_v1`의 외부 고정 approval hash·검증 코드 hash, exact 다음 KRX 거래일/신규 편입 창, owner/profile/symbol/route/session 및 entry policy hash, 명시적 policy/실행 bound·독립 평가 계약을 검사한다. 후보의 native ID와 base/stress hash·비용/표본/holdout/EV를 다시 검증한다. 기존 연구의 `eligible_for_next_preopen=false`와 source-only 권한은 그대로다.
- `machine_adaptive_exit_policy_apply.publish_initial_policy`: 기존 attribution의 `rolling_policy_research_v2.all_scope_study`에서 승인된 native 후보만 소비한다. 원 parent **byte SHA256**과 child canonical hash를 구분하고 선정 scope 전수를 성공/실패로 닫는다. 미선정 scope의 source gap은 전체 veto로 확대하지 않는다. target-date PREOPEN에서만 선정 근거와 `published_not_loaded` receipt를 한 JSON으로 원자 저장하며, 같은 세대의 재호출은 원 receipt를 보존하고 다른/잘못된 기존 세대는 덮지 않는다.
- `load_for_new_position`: 현재 승인과 발행 정책을 읽기 전용으로 재검증하여 typed policy/bounds를 반환한다. 현재 코드·owner·entry policy·날짜/창이 다르거나 로딩 중 승인/정책이 바뀌면 거절한다. 이후 canonical source 재생성만으로 이미 발행한 frozen evidence를 교체하지 않으며 현재 approval 변경/폐기는 별도로 차단한다. 기존 편입 잔량은 이 신규 admission loader로 재선택하지 않고 원 owner의 동결 정책/관리 계약을 유지해야 한다.

독립 approval은 후보가 발급한 자기 hash나 `research_ready` 문구가 아니다. 호출 owner가 **별도로 검토·고정한 envelope digest와 runtime-code digest**를 공급해야 한다. 테스트가 쓴 숫자/승인 ID/코드 hash는 임시 fixture이며 운영값으로 제안·발행하지 않았다. 이번 버전은 **초기 exact 후보/날짜 승인**만 처리한다. `auto_maintenance`를 초기 승인으로 우회하지 않으며 R6에 결속된 자동 유지·확대와 공통 approval ledger의 family/schema dispatch는 다음 연결에 남는다.

### 검증과 남은 경계

검토 중 로딩 도중 정책 교체, 발행 완료 직전 승인 변경, 비정규 날짜 표현을 추가 차단했다. 신규59개와 기존 연구/정책/공통 approval 직접 consumer 회귀를 합해 **191 PASS / 4.00초**, Ruff·Black·compile·`git diff --check` 통과, 이번 초기 control-plane 검토 범위 미해결 finding0이다. 검증 명령은 `.venv/bin/python -m pytest -q src/tests/test_machine_adaptive_exit_activation.py src/tests/test_machine_adaptive_exit_policy.py src/tests/test_machine_adaptive_exit_study.py src/tests/test_machine_microstructure_policy_approval.py --maxfail=3 --tb=short`다. 이전 전체 lifecycle2308개를 무관하게 반복 실행하지 않았고, 이번191개를 실제 launcher/주문 통합 테스트라고 보고하지 않는다.

| 신규 파일 | 검증 SHA256 |
| --- | --- |
| `src/trading/config/machine_adaptive_exit_activation.py` | `4260003488bcbb89b344a0c92861dc21bff474dd1a4dcc38232b886c53f1b877` |
| `src/engine/automation/machine_adaptive_exit_policy_apply.py` | `220237110c67896780ecdd6d0bc7b1bc75ce07ae745d9abe7572bf72286819e2` |
| `src/tests/test_machine_adaptive_exit_activation.py` | `ebe585eaa6c3e3bac5d298c29200b37207bdcd87dc0af3a7248bdb0c3f767b71` |

13:18 읽기 전용 재확인에서 source9/9 parent SHA는 `b5068924d29491da163a469da05b8634b1528ee5249723012e103d13999e1db5`, census30/invalid30/eligible0, 연구 evidence0/후보0, `net_ev_pct=null`이다. **유효한 운영 초기 envelope·정책은 발행하지 않았고 실거래 활성화되지 않았다.** 초기 control-plane 코드는 테스트됐지만 실제 시장/clock/가격·account/order safety 공급, 생산 서비스 호출·신규 position 편입, 기존 편입 잔량의 익일 유지, 공통 승인 dispatch/자동 유지 R6가 남아 있으므로 §19 단계1 전체와 단계2~4를 완료 처리하지 않는다.

다음 개발은 이 발행·로더를 실제 서비스/신규 편입의 단일 경로와 연결하고 그 경로의 필수 lifecycle을 검증하는 것이다. 범용 legacy 복구를 다시 선행작업으로 늘리지 않는다. 운영 설정/정책/원장·PID/서비스·계좌/주문·Provider·cron은 변경하지 않았고 report 재생성·배포/재기동·외부 sync·commit/push도 실행하지 않았다. 운영 실행은 다른 세션, 남은 개발·자연/경제성 acceptance는 동일 `MachineLifecycleTurnoverObjectiveFollowup0910` OPEN에 유지한다.

## 21. 초기 정책과 원 owner의 신규 lot 편입 연결

`2026-09-10T13:51:28+09:00` 개발/격리 검증 receipt. §19의 우선순위에 따라 별도 연구 producer나 범용 legacy 복구를 추가하지 않고, §20 정책을 실제 원장 consumer까지 연결했다. 새 파일 위치는 기존 주문 owner 패키지 `src/trading/order/adaptive_exit/enrollment.py`와 `src/tests/test_machine_adaptive_exit_enrollment.py`다. 실제 서비스의 `OwnerLoopServices.admission` 공급은 기본 없음이며 이번에 주입/활성화하지 않았다.

- `InitialPolicyAdmission`: 외부 고정 envelope/code hash와 발행 정책을 재검증하고, 기동 이후·당일 승인 창 안의 실제 **첫 체결 관측**→원 target ACK→편입 시각을 결속한다. 그 시각은 exchange fill time으로 바꾸지 않는다. 현재 owner/계좌의 exact BUY·SELL registry, 단일 full-fill lot/원 수량·가격·entry policy·scope가 일치해야 하며 registry나 custody를 새로 만들거나 이관하지 않는다.
- 기존 episode/widget `run_once`에 신규 편입 hook을 연결했다. 편입은 **broker 호출 없이**, session과 편입 receipt를 기존 owner 파일에 함께 원자 저장한다. 이후 기존 실행 루프의 gateway 생성 전과 write guard, final EXIT/terminal handoff에서 동결 근거를 다시 검사한다. 위젯 source-native `entry/scale_in:N` lot과 기존 target intent를 분리하고, 삼성 source의 `samsung:` profile을 기존 timing 이름으로 잘못 비교하지 않도록 했다.
- 만료는 새 편입을 차단한다. 이미 편입된 lot의 동일 동결 정책/receipt 재검증은 만료 후·재시작에도 가능하다. 이는 **다음 날짜 정책 catalog의 다세대 관리나 익일 주문·잔량 복구 전체가 완성됐다는 뜻은 아니다**. source-only 연구 비용 owner는 `live_order_or_exit_decision` 사용을 금지하므로, 실행 비용 guard는 별도 envelope의 근거 hash/명시적 값으로 결속했다. 테스트의 비용값은 운영 승인값이 아니다.
- 리뷰 보완: bool 수량/비정상 시각·clock provenance, 미승인 entry policy, 원 target 부분체결, 중복 BUY/target과 미대사 위젯 수량, 승인/파일/receipt 변조·서비스 제거를 차단했다. 편입 저장이 publish 뒤 실패할 수 있으므로 그 process는 재로드 전 run/write를 차단한다. 편입 receipt만 남고 session이 없거나 정책이 사라진 경우 기존 주문 경로로 조용히 복귀하지 않는다.

### 검증과 실제 남은 단계

신규 편입→원장 재로드→기존 port의 fake-wire 취소 연결, 만료/재시작·원 owner/수량·authority·저장 실패와 기본 비활성 위젯/삼성 오전·정오·오후/저가주 회귀를 합해 **704 PASS / 4 owner 비대상 SKIP / 36.45초**다. 마지막 리뷰에서 서비스 제거+빈 영수증이 기존 방식으로 낮춰 허용되지 않도록 session/receipt 일대일 coverage와 형식을 보완한 최종 세대다. `korstockscan-review-gate`에 따른 직접 consumer·권한·실패 경로 재리뷰의 이번 범위 미해결 finding0, Ruff·Black·compile·`git diff --check` 통과다. Print-only parser29개/현재 checklist13개/기존 owner1개/중복 title0을 확인했다. 실제 broker/계좌 테스트나 live launcher 검증으로 확대하지 않는다.

검증 명령: `.venv/bin/python -m pytest -q src/tests/test_machine_adaptive_exit_enrollment.py src/tests/test_machine_adaptive_exit_activation.py src/tests/test_machine_adaptive_exit_owner_loop.py src/tests/test_machine_adaptive_exit_runtime.py src/tests/test_machine_adaptive_exit_arbitration.py src/tests/test_machine_adaptive_exit_terminal.py src/tests/test_widget_signal_auto_trade.py src/tests/test_samsung_morning_one_share.py src/tests/test_samsung_midday_one_share.py src/tests/test_samsung_afternoon_one_share.py src/tests/test_low_price_two_leg.py --maxfail=2 --tb=short`.

| 검증 파일 | SHA256 |
| --- | --- |
| `src/trading/order/adaptive_exit/enrollment.py` | `1bba5d1bad216fe3d82bbd69098829c191a05cea57bf84c6b4122a787079b55c` |
| `src/trading/order/adaptive_exit/owner_loop.py` | `e491853342b24cfd9420d16af8d5a2c2267487d5d21d86d5fa24f3fd097c8e78` |
| `src/trading/order/regular_two_leg_machine.py` | `7c1ceae2fc7e306dd1b23f6fefd4c72304eea0e4f08a9613d9b6e2ec13a419ba` |
| `src/trading/widget_auto_trade/engine.py` | `f0d15d58c1d93429480ec973f20c87786f99867a1a8bcc9a85669869445d63df` |
| `src/trading/config/machine_adaptive_exit_activation.py` | `de11cc7020d4b19b7746d668e9281343e7cc6fe41f4a03a3a8cfb024bbb75e54` |
| `src/tests/test_machine_adaptive_exit_enrollment.py` | `9f2a1f4ced09a82d74212bcb5cc3a96c639e6153ce3499b0be8160b9db91ed9f` |
| `src/tests/test_machine_adaptive_exit_activation.py` | `af2be234ca69678480cd95382e46a8e1ee655911e1e27d343399000558898830` |

13:46 source9/9 parent SHA `b5068924d29491da163a469da05b8634b1528ee5249723012e103d13999e1db5`는 §20과 동일하다. 기존 census30/invalid30/eligible0·연구0/후보0·EV null을 새 자연 근거로 재라벨링하지 않았고 재생성하지 않았다. 이번 편입은 **독립 target의 신규 full-fill lot** 연결이며 합산 target/group의 실제 편입은 별도 미완료다. 초기 실행 비용 근거와 numeric envelope의 운영 승인/발행도 없다.

남은 개발 순서는 **실제 서비스의 시장·clock·계좌/order safety 공급과 승인 dispatch → group/다세대 정책의 신규 편입 및 선택 정책 필수 익일 lifecycle → 자동 유지 R6·개발 통합 검증/인계**다. 이미 코드로 닫힌 예외를 재구현하거나 모든 과거 보유 이관을 첫 활성화 공통 gate로 늘리지 않는다. 배포·재기동·운영 설정, 실제 launcher/PID/신규 정책 소비와 자연 terminal/비용 경제성은 다른 세션의 별도 단계다. 운영 env/정책/원장/custody/PID/service·실주문·Provider·report 재생성·외부 sync·commit/push는 이번에 변경/실행하지 않았다. 전체 목표와 `MachineLifecycleTurnoverObjectiveFollowup0910`의21:30~21:40 자연 acceptance는 OPEN이다.

## 22. 기존 WS 투영과 공통 청산 입력 연결

`2026-09-10T14:11:44+09:00` 개발/격리 검증 receipt. §19 중간 점검의 **활성화에 필요한 실제 입력 연결**만 진행했다. 새 시장 collector/API·범용 복구 framework·정기 producer는 추가하지 않았다. 위치는 기존 주문 owner 패키지의 `market_source.py`, 기존 attribution source/owner loop와 전용 테스트다.

- `WSExitSnapshotReader`는 기존 `bd_fbuy_accum_pre_scanner._ws_machine_route_payload`가 만든 로컬 JSON의 단일 실제 byte generation을 읽는다. source-only 입력 권한, exact item/route·0B/0D epoch, 최근1초 left watermark/sequence·시각·현재 endpoint의 가격/수량 일치, 실제 bid depth와 발행 freshness를 검증한다.120행 자체를1초 완전성으로 인정하지 않고 cross-epoch·미래·stale·동일 sequence 상충·UNKNOWN·호가 결손·압축/alias 대체를 명시적 gap으로 남긴다.
- 장후 `machine_adaptive_exit_source`와 reader가 같은 `snapshot_payload_from_window`를 사용한다. 기존 bid 비하락+실제 BUY 설명+refill 지지 및 개선 bps 계산을 유지하고 유효한 연구 snapshot의 기존 hash/필드를 보존한다. 매도잔량 감소 자체를 신호로 추가하거나 entry classifier·live threshold를 변경하지 않는다. 비정상 bid depth는 연구 source에서도 먼저 제외하며 실제 report는 재생성하지 않았다.
- `step_session`은 adapter의 명시적 source gap을 새 가격 판단용 입력으로 보간하지 않는다. 다만 이미 소유한 주문의 receipt reconciliation을 막지 않아 원 target 전량체결·수량 terminal/위젯 archive가 계속 연결된다. 남은 manager에는 원 실행 이유와 market source gap을 함께 기록한다. 기존 취소 복구/수량·owner guard는 유지하며 시세 결손으로 새로운 SELL 가격을 만들지 않는다.

### 검증과 아직 없는 서비스 공급

실제 WS **투영 함수**→임시 JSON→reader, 실제 초기 정책/편입→기존 위젯·episode loop→fake broker wire를 검증했다. 지지 입력은 기존1회 연장, 비지지·진행 미달은 기존 취소 요청, 시세 결손은 새 판단 차단/원 체결 확인 유지로 분리된다. 코드 리뷰에서 endpoint 내용 상충과 시세 결손 시 수량 확인까지 막히는 경로를 보완했다. 테스트 중 발견한 지지 입력의 정상 연장·위젯 자동 archive는 제품 결함으로 오인하지 않고 assertion을 실제 계약에 맞췄다.

최종 **318 PASS / 2 owner 비대상 SKIP / 13.21초**, Ruff·Black·compile·`git diff --check` 통과다. `korstockscan-review-gate`의 이번 adapter/직접 consumer 범위 미해결 finding0이며 전체 서비스 활성화 gate PASS는 아니다. 검증 명령은 `.venv/bin/python -m pytest -q src/tests/test_machine_adaptive_exit_market_source.py src/tests/test_machine_adaptive_exit_natural_source.py src/tests/test_machine_confirmation_window.py src/tests/test_machine_adaptive_exit_owner_loop.py src/tests/test_machine_adaptive_exit_runtime.py src/tests/test_machine_adaptive_exit_enrollment.py src/tests/test_machine_adaptive_exit_study.py src/tests/test_machine_adaptive_exit_activation.py --maxfail=2 --tb=short`다.

| 검증 파일 | SHA256 |
| --- | --- |
| `src/trading/order/adaptive_exit/market_source.py` | `eb232b80923c4ede819a866ca0882ded3d3d5a7fb67a44b87390764ae757797c` |
| `src/trading/order/adaptive_exit/owner_loop.py` | `cde3a11813f77a685b70c0a4a743a84d3fe57dd0fdac7e86d71c314fc61b59b0` |
| `src/engine/monitoring/machine_adaptive_exit_source.py` | `802622f995adb94b477f8eb7105934fb43ff1b5a6c0b26da99ed2bd75d9f57c0` |
| `src/tests/test_machine_adaptive_exit_market_source.py` | `df75d068326688649c0b0d593414d8e85f637c0ec38abaa15f72e06aab5576d7` |

문서/체크리스트 보완 후 print-only parser29개·현재 checklist13개·기존 owner1개·중복 title0을 확인했다. 링크·owner·권한 경계를 재리뷰했으며 최종 네 코드/테스트 hash는 위 표와 동일하다. 병행 main AI/holding/recheck 변경은 이번 검증 범위에 넣지 않았다.

읽고 재사용한 기존 WS producer 코드 SHA는 `3efe43dc3abc2433fb4c4a278e62b5cfaa6d00a25c9b7088fb4d8f208907c3ca`다. Kiwoom 요청/응답 parser·FID/REG·account/order adapter는 이번에 수정하거나 실제 호출하지 않았다. 이 hash는 실제 PID가 해당 코드를 소비했다는 receipt가 아니다.

**시세 reader는 거래정지/세션 시계를 인증하지 않는다.** 기존 `market_halt_windows`의 파일 부재→빈 목록 또는 source-only 연구의 `verified_halt_ms=0`을 정상 live clock으로 사용하지 않았다. 실제 service의 clock/session 검증·계좌/order 안전검사와 외부 고정 승인 공급, 공통 승인 dispatch가 다음 필수 연결이다. 이어 group/다세대 신규 편입·선택 정책의 필수 익일 manager, 자동 유지 R6·한 세대 통합 검증/인계가 남는다. 전체 과거 보유 이관·미정의 응답 범용 복구는 첫 활성화 공통 gate로 다시 늘리지 않는다.

운영 env/정책/원장·custody·PID/service·실주문·Provider·report 재생성·외부 sync·commit/push는 실행/변경하지 않았다. 배포·재기동·운영 설정과 실제 활성화·자연/경제성 검증은 다른 세션이다. §20~§21의 source9/9 후보0/EV null 기록을 새로운 자연 근거로 바꾸지 않으며 `MachineLifecycleTurnoverObjectiveFollowup0910`의21:30~21:40 acceptance와 전체 활성화 목표는 OPEN이다.

## 23. 동결 정책 세대 분리와 활성화 결손 재점검

`2026-09-10T14:29:23+09:00` 개발/격리 검증 receipt. §19의 과도한 수평 확장 방지 원칙에 따라 범용 복구·새 전략을 추가하지 않고, **다음 정책 선택 또는 신규 편입 중지 때문에 이미 편입된 잔량의 동결 근거를 잃는 연결 결손**을 보완했다.

- 기존 `enrollment.py`의 `PolicyAdmissionCatalog`는 명시적 current 한 세대에서만 신규 편입하고, retained 목록에서는 기존 영수증의 정확한 승인 hash·발행 정책·binding·원천을 재검증한다. 날짜/최신 파일 탐색·미달 시 구 정책 fallback·새 승인 생성은 없다. `current=None`은 신규 **adaptive 편입**만 중지하며 원래 BUY 정책을 바꾸거나 기존 lot의 청산 manager를 제거하지 않는다.
- 각 세대의 고정 envelope/hash와 독립 파일을 요구하고 중복 pin·path alias·상이한 검증 코드 hash를 거절한다. 기존 세대 손상/제거·영수증의 세대 바꿔치기는 계속 차단한다. 반대로 무관한 다음 세대 파일 결손은 정상 retained lot의 승인 재검증까지 막지 않는다. 외부 owner/계좌·주문 guard는 여전히 별도이며 catalog가 true를 대신 공급하지 않는다.
- `OwnerLoopServices.admission`과 기존 widget/episode 편입·실행 consumer가 이 catalog를 받도록 연결했다. 테스트는9/10 원장 재로드→9/11 승인 파일과 기존 binding 동시 검증, 새9/11 proposal의 current 전용 선택, 신규 편입 중지와 기존 owner fake-wire 실행을 분리한다. **다음날 실제 broker 주문조회/잔량 관리, 서로 다른 runtime code 간 migration, 합산 target/group 편입은 이번 지원 범위가 아니다.** 실제 service constructor/configuration은 변경하지 않았다.

### 입력 결손과 남은 단계

14:17:23 읽기 전용 공식 규격 확인은 upstream HEAD `234560d213acd8871ae344b5481aecd2f30287fa`의 `kiwoom/specs.py`, `kiwoom/realtime/schemas.py`, `decoders.py`, packaged `kiwoom/_data/kiwoom_api_spec.json`의 `0s`·`1h`다. 이 범위에서 `0s`는 시장상태를 기술하지만 `1h` FID9068의 발동/해제 enum 설명이 비어 있고1223/1224만으로 완전한 종목별 정지 구간을 인증할 수 없다. 예시값으로 의미를 추정하지 않았다. [검사한 공식 spec](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/blob/234560d213acd8871ae344b5481aecd2f30287fa/kiwoom/_data/kiwoom_api_spec.json). 이번 점검은 전체 protocol gate/실제 수신 검증 완료가 아니며 Kiwoom 요청·parser·FID·REG 변경/호출은 없다.

로컬 `market_halt_windows.load_market_halt_windows`의 결손→빈 목록과 source-only session event는 live clock의 연속성 증거가 아니다. 따라서 `clock_source_contract_gap`을 기존0910 owner에 유지하며, 공식 상태 의미 및 실제 epoch/수신 연속성·정지 구간이 검증된 원천→service clock 소비가 수용조건이다. `Clock(now, 0)` 또는 `lambda: True`로 service 공급을 완료 처리하지 않는다. 합산 target은 기존 초기 envelope의 단일-lot 실행 bound와 다른 배분/판단/실행 계약이므로 자동 재해석하지 않았고, group의 승인·신규 편입 연결은 여전히 개발 잔여다.

남은 경로는 **① 실제 service의 clock/session·원 owner 안전검사/승인 공급 및 공통 승인 dispatch ② group 승인·편입과 선택 정책의 필수 익일 주문/잔량 lifecycle ③ 자동 유지 R6 및 한 코드 세대 통합 검증·인계 ④ 다른 세션의 원천/승인 조건 확인·배포/운영 설정/정책 발행·기동 ⑤ 실제 PID/신규 편입/terminal 및 비용 후 효과 확인**이다. 정책 catalog 코드 완료를①·② 전체 또는 실제 활성화 완료로 합치지 않는다. 모든 legacy/manual 자동 이관·과거 정산 복원을 첫 활성화의 추가 공통 gate로 늘리지 않는다.

### 검증

최종 **242 PASS / 2 owner 비대상 SKIP / 14.18초**, Ruff·Black·compile·`git diff --check` 통과다. 첫 테스트의 episode 상태 위치 assertion을 기존 owner 구조에 맞춰 수정했고, 제품 상태를 테스트에 맞춰 바꾸지 않았다. `korstockscan-review-gate`로 generation 선택/변조·직접 owner 소비·권한·실패 경로를 재리뷰했으며 이번 수정 범위 미해결 finding0이다. 명령: `.venv/bin/python -m pytest -q src/tests/test_machine_adaptive_exit_policy_catalog.py src/tests/test_machine_adaptive_exit_activation.py src/tests/test_machine_adaptive_exit_enrollment.py src/tests/test_machine_adaptive_exit_owner_loop.py src/tests/test_machine_adaptive_exit_market_source.py --maxfail=2 --tb=short`. 신규 테스트는 기존 `src/tests` 위치를 사용했고 engine-root 모듈·정기 producer는 추가하지 않았다.

| 검증 파일 | SHA256 |
| --- | --- |
| `src/trading/order/adaptive_exit/enrollment.py` | `6491c04de49f7f88cf0210235fcff07196c21042700e4fb132b8bd574357d403` |
| `src/trading/order/adaptive_exit/owner_loop.py` | `dbc19f550fbab6af8576097ac629e76dc9c86a96368ba81f121fdab6ec85c3f5` |
| `src/tests/test_machine_adaptive_exit_activation.py` | `bd15e1a16a79dfab841c8ee9867e6a67447c36f188e3bc56a59e1a672f7dad56` |
| `src/tests/test_machine_adaptive_exit_policy_catalog.py` | `723db19e9f555ef4cbb02f41ec441217e6d65e51e37d853c889cf4fefd12c9d0` |

Print-only parser29개·현재 checklist13개·기존 owner1개·중복 title0과 문서 링크/권한 경계를 확인했다. 위 네 파일의 최종 hash는 표와 같고 병행 Main AI/holding/recheck 변경은 이번 검증 범위가 아니다.

운영 env/정책/원장·custody·PID/service·실주문·Provider·report 재생성·외부 sync·commit/push는 변경/실행하지 않았다. 임시 정책과 fake wire만 검증했으며 source9/9의 이전 후보0/EV null receipt를 새 자연 점검으로 재사용하지 않는다. 배포·재기동·운영 설정과 실제 활성화는 다른 세션이다. `MachineLifecycleTurnoverObjectiveFollowup0910`의21:30~21:40 자연/경제성 acceptance와 전체 목표는 OPEN이다.

## 24. 시계 원천 결손과 원 주문 receipt-only 종료 연결

`2026-09-10T14:46:19+09:00` 개발/격리 검증 receipt. 서비스 연결을 검토하면서 **시계 공급 결손이 새 가격/시간 판단뿐 아니라 이미 제출된 원 주문의 체결·취소 terminal 확인까지 멈추는 단절**을 발견했다. §19의 필수 종결 경로에 해당하여 기존 단일-lot owner/driver를 보완했으며 새 시계 daemon·범용 복구 engine·운영 기본값은 추가하지 않았다.

- `Clock.verified_halt_ms=None`은 검증되지 않은 활성 거래시간이다. `ClockSourceGap` 또는 명시적 None만 receipt-only로 분류하고, 음수/문자/bool/벽시각보다 긴 정지시간·최초 체결 전 시각은 여전히 거절한다. 원천 결손을 정지0초로 바꾸지 않는다.
- `owner_loop.step_session`은 원 잠금·동결 정책/편입 권한을 먼저 확인한다. typed clock gap이면 시장 snapshot을 요청하지 않고 기존 `RegisteredOwnerExitPort`에 receipt-only를 전달한다. 임의 예외를 정상 시계나 정상 실행으로 삼키지 않는다. 실제 서비스의 clock 공급자는 아직 없으므로 이 보완을 service 연결 완료로 표시하지 않는다.
- 기존 target의 부분/전량 체결, 이미 요청된 취소의 exact child terminal, ACK 뒤 저장 실패한 기존 SELL의 조회 복구, 기존 SELL/취소의 부분·전량 종료는 확인한다. 동일 주문·원 owner·정확한 누적 수량과 원자 저장/재시작 계약을 유지하고, 종료 후 기존 원장/terminal consumer로 전달한다. 실제 비용 결손은 null/미대사이며 수량 FLAT을 실현손익 완료로 바꾸지 않는다.
- driver와 실제 port의 전송 guard 모두 새 intent/취소·예약 전 취소 복구·TTL 취소·SELL·잔량 재시도·연장/trail 판단을 차단한다. 남은 수량 manager는 유지한다. 검증된 시계·fresh 시장·기존 guard가 회복된 후에만 기존 실행 경로로 돌아갈 수 있다. 이 동작은 테스트의 fake wire에서만 실행했다.
- 공통 nullable Clock의 직접 소비자인 순수 decision, source replay, 실행 replay와 group decision도 None을 경제성/연장 입력으로 쓰지 않고 source gap으로 남기는지 검증했다. **group owner의 receipt-only 서비스 연결, 익일 broker lifecycle 또는 실제 정지 구간 reader를 이번 변경으로 구현했다고 주장하지 않는다.**

### 공식 원천과 재리뷰

코드 수정 전 `2026-09-10T14:37:26+09:00`에 upstream HEAD `234560d213acd8871ae344b5481aecd2f30287fa`를 확인했다. 현재 tree에 `kiwoom_docs`가 없음을 보존하고 `kiwoom/specs.py`, `kiwoom/core/client.py`의 요청/오류·continuation, packaged `kiwoom/_data/kiwoom_api_spec.json`의 `kt00007`·`ka10075`·`kt10003` 전체 request/response와 Postman PRD/MOCK method/header/url/body를 대사했다. [검사한 공식 spec](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/blob/234560d213acd8871ae344b5481aecd2f30287fa/kiwoom/_data/kiwoom_api_spec.json). 날짜별 주문조회·현재 미체결을 구분하고 취소 ACK는 terminal proof가 아니며 local 양수 수량 제한을 유지한다. 이번 변경은 wire/parser/FID/auth/REG·retry/조회 bound를 바꾸거나 실제 API를 호출하지 않았다. §23의 VI 의미/연속성 결손을 새 공식 근거 없이 해소하지 않는다.

`korstockscan-review-gate`로 변경 경로의 직접 consumer·silent failure·권한 손실·불명확한 clock·저장 후 장애·partial/terminal/restart를 재검토했다. 이번 범위 미해결 finding0. 최종 **533 PASS / 4 owner 비대상 SKIP / 33.17초**, Ruff·Black·compile·`git diff --check` 통과다. 전용 clock gap37개는 이533개에 포함되며 합산하지 않는다. 광범위한 기존2308개 재실행이나 자연 경제성 재생성을 요구하지 않았다.

검증 명령: `.venv/bin/python -m pytest -q src/tests/test_machine_adaptive_exit_clock_gap.py src/tests/test_machine_adaptive_exit_driver.py src/tests/test_machine_adaptive_exit_runtime.py src/tests/test_machine_adaptive_exit_owner_loop.py src/tests/test_machine_adaptive_exit_decision.py src/tests/test_machine_adaptive_exit_replay.py src/tests/test_machine_adaptive_exit_execution_replay.py src/tests/test_machine_adaptive_exit_group_decision.py src/tests/test_machine_adaptive_exit_group_trailing.py src/tests/test_machine_adaptive_exit_terminal.py src/tests/test_machine_adaptive_exit_terminal_cancel.py src/tests/test_machine_adaptive_exit_market_source.py src/tests/test_machine_adaptive_exit_enrollment.py src/tests/test_machine_adaptive_exit_policy_catalog.py --maxfail=2 --tb=short`.

| 검증 파일 | SHA256 |
| --- | --- |
| `src/trading/order/adaptive_exit/models.py` | `3960be77c955dc02e3caa0f132b84a05bb6cb03175c9a993dd5879242bfe4cd2` |
| `src/trading/order/adaptive_exit/driver.py` | `8e8a93591f235d56159010a31447681b74515118ea6965a420a5f2ff15a5ab6c` |
| `src/trading/order/adaptive_exit/runtime.py` | `92b0ed92bd40d12a4d5b6550593efadfa3e733c76b4e2b31b78c48ad75c85167` |
| `src/trading/order/adaptive_exit/owner_loop.py` | `82104b2eb1aa66d5d625046314ad938d370e7880ab76fcebc15da5913afc6367` |
| `src/tests/test_machine_adaptive_exit_clock_gap.py` | `c14c24e4e698ae82854ec922ae33516590c4917194ccd57331a719f9c4e8e84d` |

Print-only parser는29개·현재 checklist13개·기존 owner1개·중복 title0이며 관련 문서 링크·권한 경계를 검토했다. 최종 소스5개 hash는 표와 동일하다.

이 개발은 §23의 필수 종결 경로 한 결손을 닫았으며 남은 단계는 **검증된 clock/session·원 안전검사/승인 공급과 service 연결 → group 승인·편입/필수 익일 잔량 관리 → 자동 유지 R6·한 코드 세대 통합 검증/인계 → 다른 세션의 원천/승인 검증·배포/운영 설정·실제 활성화**다. 전체 목표·자연 terminal·비용 후 효과는 OPEN이다. 운영 policy/env/custody/registry/PID/service·주문/취소·Provider·정기 report 재생성·외부 sync·commit/push는 실행하지 않았으며, 병행 Main AI/holding/recheck 변경은 검증 범위가 아니다. `MachineLifecycleTurnoverObjectiveFollowup0910`의21:30~21:40 acceptance를 현재 코드 검증으로 닫지 않는다.

## 25. 기존 공통 승인 handoff와 초기 발행의 직접 연결

`2026-09-10T15:25:33+09:00` 개발 세대와 격리 검증 기록. 직전 읽기 전용 재점검에서 **R6 자동 유지를 최초 활성화 앞에 묶은 순서**와 발행기의 **08:00 마감 결손**을 확인했다. 전체 owner/profile 목표는 유지하되 이미 구현한 초기 검증기·발행기를 다시 만들지 않고 기존 승인 ledger와 직접 연결했다. 신규 코드는 `src/engine/automation/machine_adaptive_exit_approval.py`와 기존 `src/tests`의 전용 테스트다. 새로운 engine-root 모듈·중앙 승인 DB·정기 producer·상시 daemon은 없다.

### 구현·권한 경계

- 기존 attribution parent byte hash/child canonical hash→선정 scope의 native recommendation ID→공통 queue/명시적 operator decision→exact-date handoff→기존 초기 publisher→loader를 연결했다. projection이 새로운 경제성/고유 작업/권한을 만들지 않으며 원 canonical report는 수정·재생성하지 않는다.
- 공통 CLI의 선택 인자 `--adaptive-exit-initial-context`와 `--adaptive-exit-initial-context-sha256`는 **별도 검토된 operator context와 외부 byte pin**을 함께 요구한다. context는 기존 envelope/고정 hash·검증 코드 hash 및 독립된 실행준비 근거의 hash/선정 scope/동일 stage 비충돌·service 검토 결과를 포함한다. 해당 결과의 기본 True는 없으며 후보/report가 registry를 공급하지 못한다. **실제 실행준비 검증기·service 공급자가 완성됐거나 운영 context가 발급됐다는 뜻이 아니다. 테스트의 readiness/숫자/hash는 임시 fixture다.** 전역 trusted registry·설치 cron 인자는 변경하지 않았다.
- exact family/초기 schema의 독립 `EvaluationContract`만 사용한다. 기존 다른 family의5/10/20일·상대1% gate는 그대로이며 exit에 복사하지 않는다. intake뿐 아니라 operator 승인/스케줄에서도 근거를 재검증하고 초기 envelope의 approval ID/target date를 결속한다. 초기 후보를 `AUTO_CHAIN_ELIGIBLE` 또는 자동 유지 승인으로 바꾸지 못한다.
- 공개 consumer는 `machine_adaptive_exit_approval.publish_preopen`이다. 기존 발행 primitive는 같은 모듈의 `_publish_initial_policy`로 내부화했으며 연구 validator를 복제하지 않는다. 현재 queue·operator decision·handoff의 날짜/hash/권한/필드 전수를 확인하고 **선정 scope 중 하나라도 누락/hold/손상되면 부분 정책을 발행하지 않는다**. 원 queue/decision/handoff byte hash는 policy의 내장 receipt에 보존한다. 무관한 queue refresh에는 최초 정상 발행 receipt를 유지한다. `published_not_loaded`는 실제 PID/매매 적용 성공이 아니다.
- 발행 consumer CLI는 모든 context/queue/source/envelope/output 경로와 context pin을 명시한다. 기본 및 `--check-only`는 handoff 검증만 하고 파일/정책/알림/주문을 변경하지 않는다. 실제 발행은 별도 운영 세션의 `--publish`에 한정한다. 승인 context·queue·decision/handoff의 cooperative lock/세대 재확인과 output의 authority 파일 덮어쓰기 차단을 유지한다. **CLI를 운영 경로에 실행하거나 설치하지 않았다.**
- 초기 발행과 loader 양쪽에08:00 KST 독립 마감을 적용했다. 예컨대 `valid_from=09:00`이어도08:30 발행/그 receipt의 로딩은 거절한다. 원래 신규 편입 창과 source/code/envelope 검증을 대신하거나 완화하지 않는다.

### 리뷰·검증

리뷰에서 메모리 tuple/JSON list의 세대 표현, 숫자0/1의 bool 위장, 승인·handoff의 미등록 권한 필드, 잘못된 승인 ID, check-only 중 queue 교체, 변경된 승인/원천 및 다중 scope 누락을 보완·재검증했다. 이번 변경의 producer→공통 CLI→consumer→loader 및 기존 편입/catalog 검토 범위 미해결 finding0. **281 PASS / 15.09초**이며 운영 broker/서비스/자연 경제성 테스트가 아니다. 기존 수천 건의 무관한 회귀나 자연 표본을 진단 완료조건으로 추가하지 않았다.

검증 명령: `.venv/bin/python -m pytest -q src/tests/test_machine_adaptive_exit_approval.py src/tests/test_machine_adaptive_exit_activation.py src/tests/test_machine_microstructure_policy_approval.py src/tests/test_machine_adaptive_exit_enrollment.py src/tests/test_machine_adaptive_exit_policy_catalog.py --maxfail=2 --tb=short`.

| 검증 파일 | SHA256 |
| --- | --- |
| `src/engine/automation/machine_adaptive_exit_approval.py` | `d58071cba8886ec321560d24919ee64776a2cc2ed56d13762a7395085bec7433` |
| `src/engine/automation/machine_adaptive_exit_policy_apply.py` | `e6fb9192313c4cced508a1dc1b97c23747293de0d47daf6dcf4bb584d8462212` |
| `src/engine/automation/machine_microstructure_policy_approval.py` | `62b4e51a760176ac0d511fcd2c61e40e27d0e149edfe24208bc4d3935f2d25d5` |
| `src/trading/config/machine_adaptive_exit_activation.py` | `2646b18f1f3a2bcbdd14349e40ca3efe9e6dd270405ca00aa267f4fc3ca1a353` |
| `src/tests/test_machine_adaptive_exit_approval.py` | `9e0d8511633c6e579d6421ef4d6bbeb249e8a33e2a9b55c5def6ed486aa90327` |
| `src/tests/test_machine_adaptive_exit_activation.py` | `f6ced62a68b3466aab2534fbcf2c6208d3c40b43022369b736d383b2d6a3250e` |

### 다음 단계 분리

이 세션의 남은 필수 개발은 **검증 가능한 clock/session·원 안전검사/승인 공급과 실제 service 연결 → group 승인·편입/선택 정책의 필수 익일 lifecycle → 동일 세대 통합 검증·운영 인계**다. 신규 편입된 잔량 관리·단일 writer·late fill/부분체결/원 EXIT 중재는 유지하고, 모든 legacy/manual 자동 이관·과거 손익 복원·새 연구 조합을 다시 공통 선행조건으로 늘리지 않는다. **R6 기록 수집 경로의 준비와 최초 활성화 후 실제 효과/자동 유지·확대 판정을 분리**하며 후자의 완료를 최초 기동 전에 요구하지 않는다. §21~§24의 “자동 유지 R6→인계” 순서는 이 재정리가 후속한다.

배포·재기동·운영 설정/정책 발행·서비스 설치/기동은 다른 세션이다. 이 실행에서는 운영 env/policy/custody/registry/PID·주문/취소·Provider·실제 API·정기 report 재생성·외부 sync·commit/push를 실행하지 않았다. source9/9의 과거 후보0/EV null을 새 자연 검증으로 재라벨링하지 않으며 `MachineLifecycleTurnoverObjectiveFollowup0910`의21:30~21:40 자연/경제성 acceptance와 전체 활성화 목표는 OPEN이다.

## 26. Group 시계 결손의 주문 전환 차단과 기존 종료 유지

`2026-09-10T15:51:49+09:00` 재대사. 직전 개발의 group 시계 보완을 검증·기록하며 실제 service 공급을 완료했다고 하지 않는다. 기존 `GroupOwnerPort`에서 runner polling/whole EXIT가 가격 관측 전에 진행되므로, 가격 관측의 clock 검사만으로 새 TTL 취소 등의 시계 결손을 막을 수 없었다. 이는 opt-in 코드의 연결 결손이며 현재 live 사고로 관측한 결과가 아니다.

- 기존 `GroupLoopServices.clock_loader`에 이미 수집된 원천을 읽는 독립 callback을 추가했다. 동결 lot 전수·현재 시각·first-fill 이후의 literal 정수 정지시간을 검증하고 가격 관측의 clock과 대사한다. 누락/명시적 unknown/typed `ClockSourceGap`은 receipt-only이며, 잘못된 schema·시각·다른 lot은 오류로 남긴다. 새 수집기/API·정기 producer·기본 0초 시계는 없다.
- 기존 runner/whole EXIT는 결손 때 새 release·SELL·TTL/BUY 취소·재시도 의도를 만들거나 전송하지 않는다. 원 target/runner의 자연 체결, 이미 제출한 취소 child와 pending BUY의 exact 대사·수량 terminal은 유지한다. 원래 시도/확인 기한과 잔량 manager·비용 null을 보존한다. 원 승인 callback 전후 및 전송 경로에서 시계를 재검사한다. 별도 안전검사/정책을 대체하지 않는다.
- 이미 실행 중이던 최종 회귀를 같은 handle로 수거했다: **281 PASS / 116.37초**. `group_owner_loop`, `group_whole_exit`, `group_pending_buy`, `group_execution`, `group_retry`, `group_terminal`, `group_trailing`의 전용 pytest 7개 파일이다. §25의 동수281/15.09초와 다른 집합이며 합산하지 않는다. fake transport/임시 원장만 사용했다. 이후 생산 코드 변경 없이 Ruff/compile/`git diff --check`를 재확인했다. 이 시계 결손 보완의 producer→port→실행/terminal consumer 검토 범위 미해결 finding0이며 실제 source/service/전체 활성화 PASS가 아니다.

| 검증 파일 | SHA256 |
| --- | --- |
| `src/trading/order/adaptive_exit/group_owner_loop.py` | `7a85875da7cf0473f6d98ad880d091d7d07de6eb0f7fa3ff91d5307dacd2225c` |
| `src/trading/order/adaptive_exit/group_execution.py` | `535804daa1ba50c70cb7dc2cbbe4e004559ee9e977b8438537781ade5341ad07` |
| `src/trading/order/adaptive_exit/group_whole_exit.py` | `a75d2183ba0286c7f3957389f6863db245e392b5544c85b22b59a249b362c8c6` |
| `src/tests/test_machine_adaptive_exit_group_owner_loop.py` | `bea7fa07603ffc2416444b1a21c1a077ed1b2571d6eb171f179cbc816f117b5c` |
| `src/tests/test_machine_adaptive_exit_group_whole_exit.py` | `7b8ba43d797f3f67a94eae445b77751671264af7a58f69530e497fd36dd8326c` |
| `src/tests/test_machine_adaptive_exit_group_pending_buy.py` | `4889396270066415496905486036a3d287600ca558ece51d8f1323b31e0604e4` |

### 실제 원천과 다음 연결의 범위

공식 upstream HEAD는 위 재조회 시각에도 `234560d213acd8871ae344b5481aecd2f30287fa`다. 직전 구현 조사15:37:33의 `kiwoom/specs.py`, `kiwoom/core/client.py`, packaged spec의 `kt00007/ka10075/kt10003/kt10001`, PRD/MOCK Postman 확인을 보존하며 wire/parser/인증/REG/호출량은 변경하지 않았다. **공식 [1h 안내](https://openapi.kiwoom.com/m/guide/apiguide/14/1h) 재확인에서9068은 정적/동적 유형(1/2),1223/1224는 발동/해제 시각(HHmmss)이다.** 과거 packaged spec의 빈 설명을 발동/해제 상태 enum 결손으로만 해석했던 조사 범위는 이 공식 내용으로 보완한다.9068을 on/off로 변환하지 않으며, 이것만으로 현재 수집의 epoch/정지 이력 연속성이나 live clock을 인증하지 않는다.

실제 서비스5파일/6생성 경로의 `adaptive_exit_services` 공급은 여전히 없다. 추가로 `machine_adaptive_exit_study.eligible_execution_paths`가 동일 target의 다중 lot를 `aggregated_target_requires_owned_partial_cancel_adapter`로 전수 제외함을 확인했다. **group 실행 코드 존재→개별 lot replay의 제외 해제→경제성 승인으로 바로 연결하면 안 된다.** 같은 합산 주문/단일 호가 잔량·부분취소/late fill·동결 회계 배분을 반영한 기존 연구 consumer 연결이 group 승인·편입의 직접 선행조건이다. 새 전략 grid/별도 producer/일괄 표본 floor를 추가하는 요청이 아니다. 기존 독립 target 연구의 정상 표본까지 차단하지 않는다.

따라서 남은 필수 묶음은 그대로 세 개다: **① 검증 가능한 clock/session·원 안전검사/승인과 실제 service 연결 ② 선택한 group 정책의 평가→승인·신규 편입 및 새 편입 잔량의 익일 lifecycle ③ 같은 세대 통합 검증·운영 인계**. 합산 target 연구 결손은② 내부의 확인된 consumer 결손이지 별도 범용 연구 프로젝트가 아니다. 당일 실제 원천의 첫 결손과도 구분한다. 이미 구현한 초기 발행/로더·단일-lot 편입과 시계 결손 차단을 다시 만들지 않고, 모든 legacy/manual 자동 이관·과거 손익 복원·미정의 응답 자동복구는 최초 활성화 공통 gate에서 제외한다. 실제 원천이 없어 막힌 부분을 새로운 callback/helper 수로 완료 처리하지 않는다.

문서 print-only parser는29개/당일 checklist13개/현재 owner1개/중복 title0을 확인했다. 새 checkbox·외부 동기화는 없으며 직접 링크·권한/이력 구분과 `git diff --check`를 검증했다.

이번 재대사는 기존 개발의 검증 종결과 선행 관계 확인이다. 실제 service 생성·신규 group 편입·운영 승인값/정책 발행은 구현 완료로 보고하지 않는다. 운영 설정/env/registry/custody/PID·실제 API/계좌/주문·재기동/배포·report 재생성·외부 sync·commit/push는 실행하지 않았다. 같은 `MachineLifecycleTurnoverObjectiveFollowup0910`의21:30~21:40 자연/경제성과 전체 활성화는 OPEN이다.

## 27. 합산 target 원천과 기존 연구 consumer 연결

`2026-09-10T16:35:06+09:00` 개발·격리 검증 receipt. 직전 읽기 전용 중간 점검은 **40 PASS/1 FAIL**로 새 보고서 테스트의 필수 `summary` 누락과 실제 service 미연결을 확인했다. 전체 활성화 목표를 축소하지 않고, 이미 시작한 연구 변경의 직접 consumer만 닫았다. 신규 전략 grid·정기 producer·시장/API 호출·운영 정책은 추가하지 않았다. 새 replay/test 위치는 기존 `src/engine/monitoring`과 `src/tests`이며 engine root 모듈은 없다.

### 직접 결손과 보완

- `machine_adaptive_exit_study.shared_target_research`→`machine_adaptive_exit_group_replay`를 연결했어도 최초 source의 `_add_lot`가 합산 target을 전수 제외하여 자연 경로가 도달 불가능했다. 기존 `group_from_observation`으로 exact scope/target/모든 full-fill BUY lot/수량/관측 clock을 검증하고 현재 owner census까지 맞을 때만 연구 경로 seed를 만든다. 현재 lot 누락/변경·partial BUY·대체 target은 유효 합산 경로가 아니며, 실제 partial-cancel/편입 권한은 발급하지 않는다.
- 서로 다른 first-fill **관측시각**을 보존한다. 가장 이른 관측 fill부터 기존 고정 horizon의 공통 종료시점을 잡고, 같은 group cadence·실제 fill/ACK checkpoint로 post-ACK 시장/sequence를 일치시킨다. 사후 성과에 따른 horizon 선택이나 실제 거래소 체결시각 합성은 없다. 기존 anchor/row/total budget은 그대로다. source-only의 기존 `verified_halt_ms=0` 연구 관례는 live clock 인증이 아니다.
- 같은 target와 working runner는 quote별 유동성 budget을 한 번만 소비한다. 원 target queue/취소 경계 선행 체결, 부분취소 중 runner 수량 변화, 원 SELL 잔량 예약·TTL/취소 terminal, runner/whole successor별 bounded attempt를 분리한다. 비교 종료의 전체 청산은 두 arm 공통 **평가용**이며 새 runtime whole-exit 권한이 아니다. runtime과 공유한 `classify_group_request`가 미지원 전량/혼합 정책 요청을 계속 차단한다.
- pre-release 취소 대기 중 runner 판단 book은 동결한다. 중간 시장 tick으로 연장이나 마지막 수용시각을 대신 갱신하지 않으며, 실제 post-cancel 판단 gap이면 연구 비용/EV를 null로 남긴다. 후행 원천 결손, 미해결/부분 체결은 완료 또는 0원으로 바꾸지 않는다. lot별 비용은 완료된 모델 BOOK 배분에 한 번 반영하며 broker lot 체결 귀속·실현손익과 분리한다.
- `propose_study_contract`의 기존 최대5개 grid/base·stress에 source census 순서의 동결 BOOK 배분만 전달했다. 누락된 import를 직접 자연 source 테스트로 발견·수리했다. rolling 원천에는 날짜가 붙은 기존 group topology를 보존하여 누락된 group path도 배타적 분모에서 사라지지 않게 했다. 현재일 자연 census 자체를 전일 원천으로 덮지 않는다.
- scope의 `shared_target_research[]`에 execution/evidence/native research candidate를 남기고 기존 attribution Markdown이 이를 표시한다. 기존 독립 target `policy_promotion_candidates/evidence`와 분리하며, 초기 publisher에서 group candidate를 선택하려 해도 거절되는 것을 검증했다. 별도 group geometry 승인·신규 편입 consumer는 미완료이며 이 연구 성공으로 대체하지 않는다.

### 리뷰·검증

`korstockscan-review-gate`에 따라 source→ordered path→공유 수량/가격 모델→기존 evidence/native ID→Markdown과 기존 초기 publisher의 비소비 경계를 검토·보완했다. 이번 연결 범위 미해결 finding0이며 실제 service/전체 활성화 gate PASS가 아니다. 최종 **361 PASS / 18.06초**; 앞선102/239개는 중복 집합이므로 합산하지 않는다. synthetic source/임시 원장·파일만 검증했다. Ruff·Black check·compile·`git diff --check` 통과. 문서 parser와 기존0910 ID 유일성은 아래 최종 검증 receipt로 별도 확인한다.

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider src/tests/test_machine_adaptive_exit_group_replay.py src/tests/test_machine_adaptive_exit_execution_replay.py src/tests/test_machine_adaptive_exit_study.py src/tests/test_machine_adaptive_exit_group_decision.py src/tests/test_machine_adaptive_exit_group_trailing.py src/tests/test_machine_adaptive_exit_target_group.py src/tests/test_machine_adaptive_exit_natural_source.py src/tests/test_machine_adaptive_exit_replay.py src/tests/test_machine_adaptive_exit_activation.py src/tests/test_machine_adaptive_exit_approval.py src/tests/test_machine_microstructure_attribution.py::test_report_writer_creates_json_and_markdown --maxfail=2 --tb=short
```

| 검증 파일 | SHA256 |
| --- | --- |
| `machine_adaptive_exit_execution_replay.py` | `a0bf85d39ac15ee8b3ffebbe62a7b3753763b8f4889d039a1ab977335559aa89` |
| `machine_adaptive_exit_group_replay.py` | `3ceabc5c7fd0e5274885bebaafffc955b5f3cbf7cf45408a3018c8095306254d` |
| `machine_adaptive_exit_study.py` | `bacd6de9754f2808a0d42a6dea0d7430acf19022af62f7d9e899cf444cc445df` |
| `machine_adaptive_exit_source.py` | `c5604974370668f9e865493ef2cbc7ff6d864bb394d8f73c7b5cf725e783b897` |
| `machine_microstructure_attribution.py` | `a652de0ac2baf78b77e65ec9d55de58f3f9d5452b73ea252f14031c8576722d6` |
| `src/trading/order/adaptive_exit/group_decision.py` | `87dcebc25e4505e2b280cc78555ecbd805dc0182bafabe7a37da189f147764f4` |
| `test_machine_adaptive_exit_group_replay.py` | `d2e24717f3cc2249c42331037a9045334e0039cd9476e8226e19d3d12be666ed` |
| `test_machine_adaptive_exit_target_group.py` | `d0dfb9f13ad0fe817e8473c5b1e8e10a80245966debf39f84a6b16dd4d7c3b15` |

문서 최종 대사 `2026-09-10T16:37:30+09:00`: print-only parser exit0, 전체29개/현재 checklist13개/기존0910 owner1개/중복 title0이다. 직접 링크와 `git diff --check`를 확인했고 위8개 코드/test SHA는 최종361 PASS 이후 동일하다. source9/9 canonical parent SHA도 `b5068924d29491da163a469da05b8634b1528ee5249723012e103d13999e1db5`로 불변이며 새 자연 실행 receipt가 아니다.

### 다음 개발과 운영 경계

다음 우선순위는 **실제 service의 검증 가능한 clock/session·원 safety/승인 공급**이다. 이어 선택 group의 실행 승인·신규 편입/필수 익일 잔량 관리, 같은 코드 세대 통합·운영 인계가 남는다. 이미 구현한 초기 발행/로더·단일-lot 편입을 재구현하거나 모든 legacy/manual 이관·미정의 응답 자동복구·과거 손익 완전 복원·추가 전략 조합을 첫 활성화 선행조건으로 늘리지 않는다. R6 기록 수집 준비와 최초 활성화 후 실제 효과/자동 유지 판정을 구분한다.

실제 broker/API/계좌·주문/취소·운영 policy/env/registry/custody/PID/service·배포/재기동·정기 report 재생성·Provider·외부 sync·commit/push는 실행하지 않았다. canonical source9/9를 이 개발로 재생성/재라벨링하지 않았다. 이번 검증은 새 source의 다음 자연 생성이나 경제성 승인 receipt가 아니다. 같은 `MachineLifecycleTurnoverObjectiveFollowup0910` 21:30~21:40 자연/경제성 acceptance와 전체 활성화 목표는 OPEN이다.

## 28. 사용자 재지시에 따른 개발 범위 최소화

`2026-09-10 16:55 KST` 재점검. 실제 service 공급이 닫히지 않은 상태에서 보조 모듈과 조회 경로를 추가한 것은 순서·범위가 과도했다. 기존 검증을 되풀이하며 잔여 기능을 계속 늘리는 진행을 중단한다.

- **목적/목표:** 기존 전체 위젯·에피소드 owner에서 선택된 적응형 청산을 실제 종료·다음 기존 진입까지 연결하여 비용 후 순이익·회전·자본점유를 개선한다. 전체 대상 지원 목표는 유지하되, 모든 가상 장애의 자동복구와 과거 보유 이관은 목표에 포함하지 않는다. 코드 완료와 실거래 효과는 별도다.
- **이번 축소 실행:** 이번 연속 작업에서만 추가한 미검증 `service_binding.py` 230행, `broker.py`의 `account_guard_snapshot` 및 두 gateway/read-control의 `kt00018` 확장을 철회했다. 새 모듈은 실제 호출자가 없고 clock 예외·guard false를 가진 초안이었다. 이 초안을 완성하기 위한 추가 개발을 하지 않는다. 직전 다른 변경은 보존했다. 철회 전 네 파일은 `/tmp/adaptive-exit-scope-withdrawal-bHGOQgNB/`에 복구용으로 보존했다.
- **남길 개발 단위:** 기존 정책→기존 실제 service/owner loop→기존 청산·수량 terminal 경로 하나를 끝까지 연결한다. 독립 target과 공유 target은 기존 owner 분기를 사용한다. clock/session·원 safety 공급, 선택 group 승인/신규 편입·신규 잔량 익일 관리 중 이 경로에서 실제로 막히는 부분만 최소 수정한다. 이 결손들은 아직 해결되지 않았으며 범위 축소를 완료 판정으로 바꾸지 않는다.
- **추가 코드 진입조건:** 수정 전에 `기존 호출 위치 → 직접 결손 → 최소 수정 → 종료 테스트`를 명시한다. 새 모듈/API/schema/수집기/정기 producer는 기본 제외하며, 기존 경로로 해결할 수 없는 필수 결손이 입증되지 않으면 추가하지 않는다. 여러 미완성 연결을 동시에 늘리지 않는다.
- **제외:** 새 전략 조합/grid, 범용 계좌 조회·복구 프레임워크, 모든 legacy/manual 보유 자동 이관, 미정의 응답의 전면 자동복구, 과거 손익 완전 복원, 이미 닫힌 모듈 재구현, 효과 미관측을 이유로 한 추가 기능. 정확한 수량·취소 증거·late fill·단일 주문 writer·기존 safety는 생략하지 않는다. 지원 밖 복구는 원 owner에 명시적으로 남긴다.
- **이 세션 종료조건:** 대상 owner의 같은 코드 세대에서 기존 연결의 통합 검증과 운영 인계가 닫히면 개발을 멈춘다. 배포·재기동·운영 설정/정책 발행은 다른 세션이다. 새 실체결·수익 개선을 개발 완료 전에 요구하거나 실제 전체 활성화 완료로 선보고하지 않는다. 후속은 기존 `MachineLifecycleTurnoverObjectiveFollowup0910`에서만 관리한다.

이번 철회 범위 검증: 삭제 전 직접 참조는 철회 대상 정의뿐이었고 삭제 후 source/test 참조0, `broker.py`는 백업 대비 해당55행 제거만 확인했다. read-control/widget gateway 두 파일은 HEAD 대비 diff0이다. 기존 fake transport/임시 원장 기반 broker 차단·부분취소·terminal idempotence와 read-control 주문 API 거절의 선택 회귀48 PASS/4.17초, syntax와 `git diff --check` 통과. print-only parser exit0/전체29/현재 checklist13/기존0910 owner1/중복 title0. 이 철회·문서 범위의 미해결 finding0이며 §27의361 PASS를 전체 활성화 검증으로 재사용하지 않는다. 운영 API·배포·설정 변경은 하지 않았다.

### 진행 중 목표의 교체 문구와 반복 방지

사용자가 현재 목표 자체의 수정을 요청했다. 당시 제품 active objective는 기존 전체 종료/복구/활성화 문구였고 goal 도구는 문구 수정·일시정지를 지원하지 않아 사용자 교체용 문구를 남겼다. 이후 paused를 거쳐 재개한 목표가 **기존 실행 경로 최소 연결·필수 검증·인계 후 종료, 운영은 다른 세션**으로 실제 교체됐음을 `get_goal`로 확인했다. 아래는 그 변경 목적의 작업 계약이며 이전 목표를 완료로 위장하여 교체하지 않았다.

> 이 세션의 목표는 기존 위젯·에피소드 적응형 청산 구현을 실제 owner 실행 경로에 최소 연결하고, 동일 코드 세대의 필수 통합 검증 및 운영 세션 인계를 완료하는 것이다. 기존 구현을 재사용하고 직접 연결을 막는 입증된 결함만 수정한다. 새 범용 프레임워크·전략/연구 확대·과거 보유 전면 복구는 제외한다. 외부 원천·승인·운영 권한 결손은 구체적 차단으로 인계하고 이를 메우기 위한 임의 기능을 추가하지 않는다. 배포·재기동·운영 설정/정책 발행과 실제 활성화·경제성 확인은 다른 세션이다. 검증 코드 세대·지원 범위·잔여 차단·운영 적용/복구 절차를 인계하면 이 세션 개발을 종료한다.

각 수정은 기존 호출 위치/실패 근거/최소 diff/종료 테스트가 있어야 한다. 검증 완료 경로는 새 회귀 근거 없이는 재개하지 않는다. 수익 미관측·자연 표본 부족·운영 미적용은 새 개발 과제가 아니다. 새 잔여 목록을 만들어 종료조건을 연장하지 않는다. 위 최소 범위를 벗어나는 결손은 별도 명시하며, 전체 활성화 미완료를 숨기거나 safety를 생략하지 않는다.

## 29. 최소 서비스 연결 검증과 운영 인계

`2026-09-10 17:10 KST` 기준. 직접 결손은 기존 service `main` 5개/생성 분기6개에 `OwnerLoopServices` 공급 경로가 없다는 것이었다. **기존 `owner_loop.py`의 작은 연결 함수와 service 호출부만 보완**했다. 새 모듈·API/parser·설정 schema·CLI flag·producer·전략/복구 기능은 추가하지 않았다. 기존 원장/정책/시세 계산/주문 전환 코드는 변경하지 않았고 다른 dirty 변경을 보존했다.

### 연결 계약과 검증

- 기존 widget, low-price, Samsung morning/midday/afternoon service의 `main(argv, *, adaptive_exit_services_factory=None)`는 원 권한/정책 검사와 원 잠금 획득·owner 생성 뒤, 첫 실행 루프 **이전**에 `factory(owner=owner, lock_handle=lock_handle)`를 호출한다. morning의 첫 COMPLETE 뒤 SOR reentry에도 별도 owner를 전달한다. 독립 target·공유 target·pending BUY·admission은 공급된 기존 services의 해당 필드를 그대로 사용한다.
- 기본 `None`은 기존 비활성 연결 경로 그대로다. 공급 시 dry/disabled·닫힌 잠금·잘못된 의존성·기존 services 덮어쓰기를 거절하고 원 handle 종료 뒤 lock 검사는 false다. callback 존재/연결 성공은 실제 안전검사나 승인 성공의 증거가 아니다. 권한·원천 부재를 `True`/0초로 채우지 않는다.
- 실제 service 함수→기존 실제 owner loop→fake broker/임시 원장의 독립 target 취소 및 공유 target 부분취소→SELL→수량 terminal을 검증했다. 삼성 재진입에는 서로 다른 owner가 전달된다. 기존 source/권한 결손·시계 gap·재시작·저장 실패·중복 주문 방지·terminal 귀속 회귀도 유지했다.
- owner 통합 **115 PASS/2 owner 비대상 SKIP,43.94초**; 삼성 기존 service 회귀11 PASS/1.99초(앞 집합과2개 중복), 위젯 service 회귀13 PASS/2.18초. 세 집합은 단순 합산하지 않는다. Ruff·Black·compile·`git diff --check` 통과. 검토 범위 미해결 finding0은 이 **연결 접점과 격리 검증**에 한하며 실전 공급 함수/활성화 gate PASS가 아니다.

재현 명령(모두 fake/임시 원장; 운영 service 실행 명령이 아님):

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider src/tests/test_machine_adaptive_exit_owner_loop.py src/tests/test_machine_adaptive_exit_group_owner_loop.py src/tests/test_samsung_morning_one_share.py::test_live_service_runs_reentry_only_after_first_episode_complete --maxfail=1 --tb=short
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider src/tests/test_samsung_morning_one_share.py src/tests/test_samsung_midday_one_share.py src/tests/test_samsung_afternoon_one_share.py -k 'service_' --maxfail=1 --tb=short
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider src/tests/test_widget_runtime_verification.py::test_service_wires_receipt_before_trade_cycle_and_failure_is_nonfatal src/tests/test_widget_signal_auto_trade.py -k 'service_' --maxfail=1 --tb=short
```

이번 변경 파일 SHA256(전체 배포 release 검증을 대체하지 않음):

| 파일 | SHA256 |
| --- | --- |
| `src/trading/order/adaptive_exit/owner_loop.py` | `77161eb4c11e8b88df344bb70cfd2757ca095b535e5b4015ee9818290ece939f` |
| `src/trading/widget_auto_trade/service.py` | `a2c91c3f59753c2869eea5da03e613bebc3450a0b944206cb2c35921cf21968c` |
| `src/trading/low_price_two_leg/service.py` | `02d4d946779b90b347f31e211e4049b2ec06088cc6e520a5ee73786c94a03267` |
| `src/trading/samsung_morning_one_share/service.py` | `85d803c0f7fa6a30ed0997c7795d104a7266a9066b511d992706b2330bf8671b` |
| `src/trading/samsung_midday_one_share/service.py` | `ae520a87a64573ccd909faa735bc9419f80c939f3cb43b2057590580d6a2e587` |
| `src/trading/samsung_afternoon_one_share/service.py` | `a41f8b018b7c55206cbbdfc4b978669b4f7594916bba26c215ee8689ed33bdd1` |
| `src/tests/test_machine_adaptive_exit_owner_loop.py` | `dd37bc906636a7165be6e8b13c78355cf9c49f2e45fb10ca71f5f1d213c6d1c0` |
| `src/tests/test_machine_adaptive_exit_group_owner_loop.py` | `2d2dc287fa121bafc815de4ce0473e37f920bfcc011ada183e9c61bc983093ce` |
| `src/tests/test_samsung_morning_one_share.py` | `61183fc0b38a57cc029b4a57ddc33c50896c616d21cb2c5a15fe85e23522fe8d` |

### 다른 운영 세션에 넘기는 필수 경계

1. **실제 공급 함수는 아직 없다.** 검증된 in-process launcher가 위 `main`의 keyword로 공급해야 하며, 기존 `python -m ...service`/설치 unit은 factory=None이다. CLI만 실행하면 적응형 청산이 켜진다는 안내나 ready-to-run 활성화 명령을 제공하지 않는다. factory는 받은 실제 owner/gateway/잠금에만 결속하고 독립 검증 clock/session·정확한 정책/승인·계좌/주문 safety를 제공해야 한다. `WSExitSnapshotReader`·기존 admission/catalog는 재사용하되 source/권한 결손을 fake callback으로 대체하지 않는다.
2. **승인/원천 및 미지원 경계:** 초기 numeric envelope·실제 검증 receipt/정책 발행, 선택 group 신규 편입 승인과 신규 잔량의 익일 복구는 미완료다. 이들은 이번 접점 연결로 해결되지 않았으며 운영 owner가 실제 지원/권한을 확인해야 한다. 지원 밖 group/익일/legacy를 임의 편입하지 않고 기존 원 target/정확한 수량 terminal·receipt-only 보존 계약을 따른다. 현재 계좌/미체결·운영 원장은 조회/수정하지 않았다.
3. **적용 전/후:** 다른 세션에서 full release 코드 세대와 위 변경 hash, owner별 exact-date 정책·미체결/보유·복구 범위를 대사한 뒤 승인된 배포/기동 여부를 결정한다. 공급 없는 기존 경로 복귀는 신규 adaptive 편입 비활성일 뿐, 이미 편입된 manager/custody를 지우는 rollback이 아니다. 활성 manager가 있다면 검증된 이전 코드/동결 정책/필수 공급을 유지하고 별도 승인된 종료·복구를 따른다. PID·정책 실제 소비·자연 주문/terminal·경제성은 그 세션의 검증이다.

이 인계는 실행 명령/승인이나 미완료 기능의 구현 완료 선언이 아니다. 변경된 **이 세션 목표는 최소 연결·격리 통합 검증·차단 인계에서 종료**하며 운영 미적용·효과 미관측으로 개발을 자동 연장하지 않는다. 자연/경제성 owner `MachineLifecycleTurnoverObjectiveFollowup0910`은 OPEN을 유지한다. 실제 API/주문·Provider·정기 report·운영 policy/env/custody/PID·배포/재기동·외부 sync·commit/push는 실행하지 않았다.

최종 문서/세대 검증: print-only parser exit0/전체28/현재 checklist12/기존0910 owner1/중복 title0. 이전§28의29/13은 당시 집계로 보존하며 다른 세션의 checklist 변경을 되돌리지 않았다. 위9개 SHA는 마지막 코드 검증 후 동일하며 직접 인계 링크·`git diff --check`를 확인했다. 테스트의2 SKIP은 각각 widget catalog 전용/episode terminal-loop 전용 사례의 다른 owner 조합으로, 서비스 분기 미검증을 숨긴 것이 아니다.

## 30. 수익 정체 보조청산 최소안과 불필요 연결 삭제

기준: 2026-09-10 17:39 KST. 사용자 요청은 **구현방안 구체화와 불필요 코드 삭제**다. 새 청산 연결의 구현·활성화 완료가 아니다. 이 절이 §1~§29의 광범위한 후속 개발 목록을 대체한다. 배포·재기동·운영 설정 변경은 다른 세션이며, 과거 연구 후보/테스트/승인은 새 보조청산의 활성화 근거가 아니다.

### 최소 기능과 구현 경계

기존 목표가 주문은 그대로 유지한다. 기존 메인의 `_evaluate_scalp_profit_stagnation_exit`에 있는 **수익권 정체 판정**만 공유하고, 참이면 해당 기계가 자기 목표주문 취소→실제 잔량 매도→체결 대사를 소유한다. 손실 청산·최대시간 강제청산·부분 trailing·추가매수·새 연구/grid·새 자동승인 체계는 범위 밖이다. `_evaluate_scalp_low_profit_stagnation_hard_exit`는 별도 함수/조건이므로 첫 범위에 자동 추가하지 않는다.

| 부분 | 구체 계약 |
| --- | --- |
| 판단 입력 | 원 owner/episode/leg와 정책 세대, 비용 계약에 맞는 현재 실행가능 매도가 기반 순수익률, 같은 기준의 관측 최고수익률, 현재 시각, 정체 시작/anchor 수익/anchor peak. 미관측 peak·비용·시각을 0으로 합성하지 않는다. |
| 공유 판단 | 기존 enable·최소수익·정체 지속시간·anchor 수익변동·peak 개선 조건을 유지한다. 수익 미달이면 anchor 해제, 가격/peak 진행이면 anchor 재설정, 정체 지속조건 충족 때만 후보. 시간만 경과한 손실 청산이 아니다. |
| 코드 위치/분리 | 구현 시 공통 순수 판정은 주문 판단 역할의 `src/trading/order/profit_stagnation.py` 한 모듈에 둔다(아직 생성하지 않음). 기존 main 함수는 자기 정책/상태 adapter로 같은 함수를 호출하도록 한다. engine-root 새 파일·전략 복사본·범용 plug-in/factory는 만들지 않는다. |
| 정책 공급 | 메인의 기존 정책 해석에서 확정한 해당 조건만 명시적으로 전달하며, 위젯/episode를 가짜 SCALPING position으로 등록하거나 전역 env를 읽혀서 권한을 상속하지 않는다. 코드 기본값은 현재 PID 적용값이나 새 기계 승인값이 아니다. 기존 dated policy 소비 범위에서 필요한 명시적 설정/활성화 근거만 받는다. |
| 상태 소유 | 정체 state는 각 기존 owner 원장에 저장한다. 최초 정상 관측에서 시작하고, 원천 결손/거래일·정책·수량·평균단가 변경 때 연속 정체 증거를 재설정한다. 과거 원천 복원·거래정지 전용 clock 서비스는 만들지 않는다. 기존 주문 reconciliation은 계속한다. |
| 실행 | 후보 뒤 원 owner의 account/manual/global-pause/order/quote/quantity guard를 재검증한다. 기존 target이 먼저 체결됐으면 그 receipt로 종료한다. 취소 ACK만으로 매도하지 않고 확정 취소·동시 체결·잔량을 확인한다. 새 quote에서 판단/수익이 무효이면 SELL을 강행하지 않고 기존 목표 복구 경로로 넘긴다. |
| 최소 주문 단위 | 원 주문번호로 보호된 자기 잔량을 처리한다. 합산 target은 같은 owner의 해당 target 잔량 전체를 한 단위로 다루며 lot별 선택적 부분취소/runner를 만들지 않는다. pending BUY/기존 복구가 있으면 신규 보조청산 후보를 보류하고 기존 owner가 먼저 대사한다. |
| 취소 후 잔량 | 기존 검증된 executor/terminal을 재사용할 수 있는지 먼저 확인한다. SELL 부분체결·확정 미체결·재시작·거절/응답 불명확 시 자기 잔량/주문 의도를 계속 보존하며 중복 제출하지 않는다. 목표 재설정·잔량 회복을 처리하지 못한 연결은 개발 완료가 아니다. |
| 검증 종료 | 동일 입력의 기존 메인 후보/공유 함수 parity, main 기존 회귀, 위젯·episode 실제 loop와 fake broker의 target 선행체결/취소 중 체결/부분체결/실패·재시작·다른 owner 비간섭. 설정과 정상 입력만 주면 실제 서비스 경로가 동작해야 완료이며 공급 함수 개발을 운영 세션에 떠넘기지 않는다. |

**의미상 차이:** 메인 함수의 AI score는 이 후보 함수 안에서는 prior/설명값이지 SELL veto가 아니다. 하지만 메인 최종 SELL은 그 뒤 `_evaluate_holding_flow_override`와 추가매수 중재·quote 재검증을 거친다. 이 최소안은 그 전체 최종 판단의 동일성이나 AI 청산을 주장하지 않는다. 메인 경로의 후행 검사는 그대로 유지하고, 기계에는 기존 기계 guard를 적용하는 결정론적 보조청산으로 한정한다. 새 AI 호출/메인 전용 holding state 이식이 필요해지면 이 범위를 확장하지 않고 별도로 보고한다.

**효용 사전 확인:** 소스 기본 최소수익은 1.0%, 기본 정체시간은 180초이며 enable 기본값은 false다. 이는 검증한 코드 기본값일 뿐 현재 live 선택값이 아니다. 기계의 원 목표가 해당 수익 조건보다 낮으면 목표가 먼저 끝나거나 보조청산 조건에 도달하지 못할 수 있다. 실제 기존 설정·목표/비용의 도달가능성을 확인하기 전 “회전 개선”을 주장하지 않는다. 도달 불가능하면 그 owner는 비적용으로 기록하며 임계값 하향·새 저수익/손절 전략을 자동 개발하지 않는다. 이 결론이 나오면 연결 개발을 밀어붙이지 않는다.

### 실제 삭제와 보존

- 삭제: 서비스 5개의 `main(..., adaptive_exit_services_factory=...)` 및 6개 owner 분기의 주입 호출, `bind_service_dependencies`, 해당 주입 전용 테스트. 실제 공급 함수가 없고 표준 CLI는 None이었던 연결이다. 기존 서비스의 원 정책·lock·startup receipt·기본 실행 경로를 보존했다.
- 삭제: `market_source.py`의 `WSExitSnapshotReader`와 reader 전용 투영 검증/선별 보조함수 및 전용 테스트. 저장소의 비테스트 consumer는 없었다. 기존 원천/장후가 사용하는 `snapshot_payload_from_window`, `SUPPORT_CONTRACT`, `MarketSourceGap`는 그대로 남겼다. Kiwoom wire request/parser/FID·WS collector는 수정하지 않았다.
- 보존: 공유 계산 parity 테스트, 원천 부재에도 원 target 체결/수량 terminal을 확인하는 두 테스트(삭제 reader 대신 명시적 gap fixture), 기존 owner·취소·잔량·group terminal 테스트. 파일명에 adaptive가 있다는 이유로 실제 사용 코드를 삭제하지 않았다.
- 보존: 현재 owner/연구 consumer가 참조하는 decision/replay/study/approval/enrollment 및 broker/reducer/driver/terminal·pending BUY/SOR 복구. 이것들은 새 보조청산의 필수 개발 목록이 아니다. 현재 참조를 끊는 전면 폐기는 이번 최소 삭제 범위가 아니며 그대로 자동 활성화하지 않는다.
- 복구 사본: `/tmp/korstockscan-exit-minimal-cleanup-TpqRos/`에 변경 전 11개 Python 파일과 5개 문서를 원 경로대로 보존했다. git 미추적 파일도 포함한다. 사본은 로컬 임시 보관이며 영구 백업을 보장하지 않는다. 파일 전체를 운영 위에 덮어쓰기 전에 이후 다른 세션 변경을 대사해야 한다.
- 변경 전 사본 대비 11개 Python 파일에서 **순 747줄 감소**했다. 파일 전체 삭제는 없고 미사용 함수/클래스/호출부와 전용 테스트를 제거했다. 새 청산 구현·운영 파일/state/PID/env/주문 수정은 하지 않았다.

### 검증 결과

- 삭제/보존 영역과 직접 소비자 재검토: 서비스 표준 CLI/권한·정책·lock·startup receipt, 원천 공유 계산, snapshot gap에서도 receipt/수량 terminal 유지. 삭제한 심볼의 source/deploy 참조 0, 5개 service는 HEAD 대비 diff 0. 저장소 밖의 임의 사용자 launcher까지 부재를 인증한 것은 아니며 새 배포 전 다른 운영 세션의 변경 대사가 필요하다.
- owner/group/source-gap/삼성 회귀: `pytest -q src/tests/test_machine_adaptive_exit_owner_loop.py src/tests/test_machine_adaptive_exit_group_owner_loop.py src/tests/test_machine_adaptive_exit_market_source.py src/tests/test_samsung_morning_one_share.py -k 'not systemd'` → 134 PASS, 2 비대상 SKIP, 1 systemd 테스트 미선택 / 39.77초.
- 장후 원천/episode 서비스: `pytest -q src/tests/test_machine_adaptive_exit_source.py src/tests/test_widget_auto_trade_policy.py src/tests/test_low_price_two_leg.py src/tests/test_samsung_midday_one_share.py src/tests/test_samsung_afternoon_one_share.py -k 'service or source'` → 24 PASS, 253 비관련 미선택 / 1.32초.
- 위젯 서비스/startup receipt: `pytest -q src/tests/test_widget_signal_auto_trade.py src/tests/test_widget_runtime_verification.py -k service` → 13 PASS, 154 비관련 미선택 / 0.87초. 서로 다른 세 집합 합계 171 PASS/2 비대상 SKIP이며 전체 저장소 테스트를 실행한 것은 아니다. 모두 fake/임시 원장이고 운영 API·service 기동은 없다.
- 11개 Python 파일 Ruff/Black/compile 통과. Black이 지적한 삼성 테스트 포맷 1건 보완 후 재검증했다. `git diff --check` 통과. print-only parser exit0, 전체27/현재 checklist11/기존0910 owner1/중복 title0. 이전28/12는 과거 집계이며 병행 checklist 변경을 되돌리지 않았다.
- 이 한정 삭제·문서 검토의 미해결 finding 0. 새 보조청산 runtime 통합은 미구현/미검증이며 기존 테스트를 그 완료 근거로 쓰지 않는다. 자연/경제성·배포는 별도이고 기존 OPEN은 유지한다.

### 목적 적합성 재검토: 17:47 구현 선행 중단

사용자는 구현·review/fix 반복, 기대효과/자동 적용/과도한 조건을 **비용 차감 후 작은 수익을 빈번하게**라는 목표로 확인하도록 요청했다. 선행 적합성 검사에서 아래 설계 불일치를 확인했으므로 §30에 적은 중단 조건을 적용했다. 이번 후속은 읽기 전용 확인과 이 문서/현재 owner 갱신이며 **새 청산 코드 연결은 구현하지 않았다**. 747줄 삭제와171 PASS는 앞 작업 기록이다.

| 확인 대상 | 실제 읽은 값 | 판정 |
| --- | --- | --- |
| 9/10 main runtime env 파일 | `SCALP_PROFIT_STAGNATION_EXIT_ENABLED=true`, `MIN_PROFIT_PCT=1.0`, `MIN_SEC=180`; strategy-owner component baseline도 동일, policies=[] | 코드 기본값만의 문제가 아니라 생성된 당일 정책 값이다. 현재 PID 소비 확인은 이번 범위가 아님. |
| 9/10 삼성 widget dated policy | NXT_PREMARKET target40bps / NXT_AFTERMARKET80bps, enabled=true | gross 목표0.4%/0.8%보다 순수익1%가 높다. KRX/다른 종목의 현재 목표까지 이 수치로 일반화하지 않는다. |
| 9/10 삼성 오전 state | 267000→268500, 266500→268000 | gross 목표 약0.5618%/0.5629%; 비용 전부터1% 미만. 완료 당시 가격 근거이며 새 실현손익/체결 검증 아님. |
| 9/10 SK텔레콤 오전 state | 90300→90700 | gross 목표 약0.4430%; 원장 HELD/late receipt 정합성은 별도 OPEN이며 여기서는 목표 가격 비교만 사용. |

P1 설계 finding: 위 확인 scope는 기존 target 가격 이하에서 순수익1%에 도달할 수 없어 **목표 이전 보조청산의 유효 구간이 없다**. target 위로 급등했는데 미체결인 예외까지 불가능하다는 의미는 아니지만, 그것을 작은 수익의 정체 청산 효과로 주장할 수 없다. 180초는 검증되지 않은 최적값이며 낮은 수익 별도 함수의1800초 최소보유/0.20% 조정수익 band를 대신 이식하는 것도 첫 범위를 벗어난다. 이 불일치는 표본/Provider 부족 또는 다음 PREOPEN을 기다리면 해결되는 문제가 아니다.

P2 구현 결손: `profit_stagnation_exit_runtime`의 기존 main PREOPEN env 경로는 있으나 새로운 widget/episode 보조청산의 candidate→dated policy→service/owner loop 자동 연결은 없다. 원 widget 정책 자동 소비와 새 보조청산 자동화를 혼동하지 않는다. 보존된 `machine_adaptive_exit_v1` 초기 approval/publisher는 다른 전략 계약이고 명시적 외부 context/envelope가 필요하다. 새 기능은 단순 배포만 남은 상태가 아니다.

조건 과도성: 확인 scope의1% 후보 진입조건은 목표 대비 구조적으로 맞지 않는다. 반면 원천 freshness, 정확한 비용, 원 owner/수량·취소확정·중복방지·정책 권한 검증은 삭제할 불필요한 gate가 아니다. 기존 adaptive 연구 validator는 **모든 거래 양수·추가 상대1%·5/10/20일 동시 양수**를 요구하지 않는다(`machine_adaptive_exit_policy.py`); 미발행 계약의 실제 표본 숫자가 과도하다고 단정하거나 그 전체 연구 gate를 새 보조청산에 복사하지 않는다. 코드 정확성 검증과 최초 전략 적용/이후 경제성 검증을 별도로 유지한다.

기대효과는 아직 미입증이다. 원래 목표 이전에 비용/예상슬리피지 차감 후 양의 실행가능 잔여수익에서 정체를 판정하도록 범위를 바꾼다면 자본 회수가 빨라질 가능성이 있지만, 건당 이익 감소·취소 후 가격 악화로 총순이익은 오히려 줄 수 있다. 이후 실제 새 진입 없이 회전 수익을 발명하지 않는다. 이번에는 비용률을 임의 적용해 실현손익/EV 숫자를 만들지 않았다.

다음에 필요한 사용자 결정은 하나다: **앞선1% 유지 제약을 해제하고, 비용·예상슬리피지 후 순이익이 양수인 구간을 보조청산 판단 대상으로 바꿀지**. 이는 기존 함수 연결만이 아니라 새 기계의 전략 조건 변경이다. 선택 전 임계값 하향/새 helper·factory/자동승인 체계를 구현하지 않는다. 승인되더라도 main 값/운영 env/기존 보유를 바꾸지 않고 개발과 배포 세션을 분리한다.

직접 검증: `.venv/bin/python -m pytest -q src/tests/test_sniper_scale_in.py -k profit_stagnation --maxfail=1` → **16 PASS / 1029 비관련 미선택 / 3.13초**. 이는 기존 코드 계약 확인이지 새 기능 완료 테스트가 아니다. 위 P1/P2는 미해결로 유지하며 전체 finding0/자동 적용 완료를 선언하지 않는다. 문서 gate는 링크/권한/현재 owner/print-only parser/diff로 검증한다. 이번 production code·운영 artifact·env·PID·주문 변경 없음.

원천 SHA256(17:47 읽기 전용 snapshot): main env `e0f8668eff706d1df97fadad85f994b3c16ed74f10bae8163c29ea4efe9dc1a5`; widget dated policy `16ad23cc849b1169720bfbd01add9ae94ecf69467a9c38b67812421d1999f52a`; 삼성 오전 state `4394b012e3a501ff9dceed220a20b43ec66c1b2ed6b5678634993daca539fa10`; SK텔레콤 오전 state `295a03a156c1de9ae06814b4018089b44cc2d1023dfcf39bb6b57192be6b8490`. 경로는 각각 `data/threshold_cycle/runtime_env/threshold_runtime_env_2026-09-10.env`, `data/runtime/widget_auto_trade_policy/widget_auto_trade_policy_2026-09-10.json`, `data/runtime/samsung_morning_one_share_state.json`, `data/runtime/low_price_two_leg/sk_telecom_morning_state.json`이다.

## 31. 양수 순수익 정체 계산 구현과 실행 연결 재검토

9/10 18:01 개발 점검. **부분 구현이며 전체 기능 review gate는 아직 통과하지 않았다.** 사용자의 “수익극대화·구현범위 최소화” 결정 위임과 후속 구현 요청에 따라 기계 보조청산은 비용/예상슬리피지 후 양수 구간으로 정했다. §30의17:47 사용자 선택 대기는 과거 기록이다. main의1% 등 정책과 최종 holding-flow/주문 guard는 변경하지 않았다.

### 이번 코드와 review/fix

- `src/trading/order/profit_stagnation.py`: main의 절대 수익변동/peak 개선/지속시간 계산을 순수 함수로 분리했다. engine-root 신설이나 범용 service factory는 없다.
- `sniper_state_handlers._evaluate_scalp_profit_stagnation_exit`: 기존 enable/실거래 구분/최소수익·정책 해석/state 저장/AI prior/후행 실행은 유지하면서 공유 함수만 호출한다. 현재 실행 프로세스를 갱신하지 않았다.
- `positive_net_stagnation`: 독립 owner가 사용할 비용 후 양수 후보 계산. 전 잔량을 감당하는 최악 실행가능 bid와 명시적 비용/추가 슬리피지를 입력받는다. **현재 production caller는 없고 테스트만 소비**한다. 스스로 depth/venue/정책 권한을 수집·검증하거나 주문하지 않는다. 이를 실제 기계 적용 코드로 표시하지 않는다.
- 후보는 즉시 양수만으로 참이 되지 않는다. 정체창이 필요하고 결측/비양수/오래된 원천/관측 공백이면 창을 비운다. 같은 호가 polling으로 기간을 늘리지 않고 owner/정책·비용·수량·평균단가 변경은 창을 재시작한다. peak/state 입력도 재검증한다. 이 state는 판단창이지 custody/주문 원장이 아니다.
- 자체 리뷰에서 정확한 손익분기점의 float 뺄셈 오차를 발견해 Decimal의 매도대금−원가/비용 비교로 보완했다. 손익분기점3종/미세 양수/후속 비양수와 훼손된 peak state 반례를 추가해 재검증했다. 작은 순익을2자리 반올림으로0으로 만들지 않는다.

### 직접 consumer에서 확인한 미완료

| 중요도 | 현재 코드의 직접 근거 | 최소 closure |
| --- | --- | --- |
| P1 | widget `_maybe_submit_exit`는 취소 뒤 일반 시장가 SELL이며 양수 재검증이 없다. old adaptive driver의 `vanished_arm=exit_with_fresh_guard`는 신호 소실 후 원 target 복구가 아니다. | 새 후보를 이 경로에 바로 연결하지 않는다. 확정 취소/동시체결/잔량→새 양수 판단·보호 지정가, 무효이면 원 목표 복구를 원 owner 안에서 처리하고 부분체결/거절/재시작을 실제 loop fixture로 검증한다. |
| P1 | low-price `_validate_state_contract`는 target_price가 원 policy target과 다르면 차단한다. common `_submit_target`/`_reconcile_target`는 원 목표 원장이다. | 이 검증을 지우지 않고 원 목표와 보조청산 successor/체결합을 구분해 기존 수량·owner 검증을 유지한다. shared target은 해당 target 전체 자기 잔량 단위이며 runner 분할을 추가하지 않는다. |
| P2 | 새 후보의 production caller0. 기존 main PREOPEN family는 machine 권한이 아니며 표준 service에는 새 정책/실행가능 원천 공급이 없다. | 기존 dated policy/서비스/원 owner loop에 실제 공급과 소비를 연결한다. 새 범용 factory·연구 grid/승인 플랫폼을 만들거나 공급 함수 구현을 다른 운영 세션에 떠넘기지 않는다. |

이 세 행은 같은 **기계 보조청산 end-to-end 연결**의 결손이지 새 전략3개가 아니다. 일반 개발 권한 부족이나 표본 대기라는 뜻도 아니다. 이번에는 계산 구현만 끝났으므로 이 미완료를 숨긴 “전체 finding0”, “배포만 남음”, “자동 적용 완료”를 선언하지 않는다. 실제 cancel/SELL/계좌/API·운영 정책 생성은 없었고 기존 broker/parser/registry/서비스 파일은 수정하지 않았다. 원천·주문 안전검증 없이 억지로 기존 손실청산 실행기에 태우지 않는다.

### 목표 적합성·조건·기대효과

- 기계의 원 target 이전 순이익1% gate는 제거한 설계다. main1%는 불변이며 실제 기계 운영값은 아직 발행하지 않았다. 소액 순수익에 정체가 겹칠 때 자본 회수를 앞당길 **가능성**이 목적이다. 손절/최대보유시간 강제매도·추가매수/AI·부분trailing은 범위 밖이다.
- 비용/슬리피지 후 양수는 신규 보조청산 후보 조건이다. 과거 모든 거래 양수, 상대1% uplift,5/10/20일 동시 양수, 최초 활성화 이전 새 기능 실체결 같은 순환 gate는 추가하지 않는다. quote/owner/취소확정/수량/중복방지/정책 권한은 필요한 안전조건이다.
- 계산 기본180초·변동0.15%p/peak0.10%p는 기존 main 계산 참조값이지 경제적 최적값이나 자동 승인값이 아니다.2초 quote age/5초 관측 gap은 단절 구간을 정체로 합성하지 않기 위한 함수 기본값이며 실제 source cadence/기존 owner 정책에 맞는 공급 검증이 남는다. 이를 추가 연구 프로젝트나 최소 보유1800초로 확대하지 않는다.
- 가상 테스트는 entry10000원·worst bid10040원·entry-notional 비용0.23%·추가slippage5bps일 때 추정 net0.1198%에서180초 정체 후 후보가 됨을 확인한다. 수수료 정책 추천/현재 실현수익/실증 EV가 아니다. 목표가를 더 기다렸을 때의 더 큰 이익을 놓칠 수 있어 **전체 비용 후 순이익·자본점유·불리한 결과**를 봐야 하며 종료 건수 증가나 새 진입을 가정한 회전 수익으로 성공을 주장하지 않는다.

### 한정 검증 및 인계

`pytest -q src/tests/test_profit_stagnation.py src/tests/test_sniper_scale_in.py -k stagnation --maxfail=1` → **136 PASS / 1029 비관련 미선택 / 1.23초**. 새 계산/80개 기존 산술 parity 및 기존 main 회귀가 대상이며 machine 실주문 loop 테스트가 아니다. Ruff(신규2파일), compile(변경Python3파일), `git diff --check` 통과. 계산 범위의 미해결 finding0과 위 P1/P2 미완료를 분리한다. 문서 검증은 동일 현재 OPEN owner/링크/print-only parser로 닫는다. 운영 배포·재기동·설정 변경 및 수익성 검증은 하지 않았다.

기존 `MachineLifecycleTurnoverObjectiveFollowup0910`에 개발 잔여를 기록했다. 수용조건은 계산 단품 PASS가 아니라 **정상 입력·설정으로 표준 service가 원 owner의 주문 전환/복구까지 실행되고, 원 정책·다른 owner가 보존되는 격리 통합검증**이다. 그 뒤에만 다른 세션으로 운영 적용을 인계한다. 기존 custody 사고/장후 자연 acceptance를 이 계산 수정으로 닫지 않는다.

외부 sync는 실행하지 않았다. 필요할 때 사용자가 실행할 표준 명령은 다음 하나다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

## 32. 최소 보조청산 실제 owner와 서비스 연결

9/10 후속 사용자 지시: 계산 단품의 PASS를 종료조건으로 오판했던 것을 수정하고 실제 연결까지 개발했다. 과거 전체 adaptive 설계의 잔여 WP·확률모형·부분 trailing·별도 AI/연구 grid는 재개하지 않았다. 검증은 임시 원장·가짜 broker wire이며 운영 파일·PID·env·주문은 변경하지 않았다.

### 구현과 필요한 자동 적용 조건

- 기존 main `stagnation_window` 산술을 재사용한다. 기계는 **전량을 커버하는 실제 bid depth의 최저 가격에서 명시적 비용·예상 slippage를 차감한 순수익 > 0**이며 정체가 지속된 경우만 원 목표 취소를 검토한다. main의 기존1%/180초 및 후행 guard는 불변이다. 회전 수/승률을 위해 음수 구간을 새로 청산하지 않는다.
- `machine_profit_stagnation_policy` → 기존 서비스5개/삼성 후속 재진입 포함 owner → `profit_stagnation_owners` → `profit_stagnation_exit` → 기존 registry-bound SELL adapter로 연결했다. 공통 주문 패키지가 전환을, market 패키지가 기존 WS 읽기를, config 패키지가 정책 핀을 소유한다. engine-root 모듈·새 daemon·generic service factory·provider 호출·WS 등록/REST 시세 조회는 추가하지 않았다.
- 최초 운영 세션이 `KORSTOCKSCAN_MACHINE_PROFIT_STAGNATION_POLICY_PATH`와 `KORSTOCKSCAN_MACHINE_PROFIT_STAGNATION_POLICY_SHA256`을 명시해야 한다. 둘 다 없으면 OFF, 불완전 핀/잘못된 내용은 비활성·진단 사유로 남긴다. 정상 기존 service는 자체 flock 안에서 매번 유효 정책을 읽으므로 별도 공급 함수 구현은 필요 없다. 처음부터 승인 창 안에 들어온 신규 entry만 편입하며 과거 보유 이관은 하지 않는다.
- 정책의 정확한 필드는 `family=machine_profit_stagnation_v1`, `enabled`, `valid_from`, `valid_until`, `owners=[widget_auto_trade, episode]`의 허용 부분집합, `round_trip_cost_pct`, `slippage_bps`, `cost_source_sha256`, `min_sec`, `max_profit_move`, `max_peak_improve`, `sell_ttl_sec`, `max_observation_gap_sec`다. 기존 비용 owner의 검증된 값/hash와 승인 기간을 운영 세션에서 결속한다. 최소 표본/양수 EV/5·10·20일 동시 gate나 첫 활성화 전 실체결을 요구하지 않는다. `max_observation_gap_sec`는 기존6초 polling 등을 수용하도록 명시하며 polling/호출량 자체는 늘리지 않는다. 180초/.15%p/.10%p는 main 참조값이지 최적화 완료 주장이 아니다.
- 원 목표·원 주문번호는 보존한다. `TARGET → CANCEL → 취소확정 → READY → 보호 지정가 → EXIT → TTL/부분체결 취소확정 → 잔량 원 목표 복구`를 같은 owner가 저장/재개한다. 취소 ACK만으로 새 매도를 내지 않는다. 손익/원가·호가를 전송 직전 재검증하며 결손·비양수·정책 철회는 원 목표로 복귀한다. 단정적 거절만 최대3회 예약 슬롯 내 원 목표 복구로 진행하고, 모호한 응답/예약을 같은 주문 재제출로 처리하지 않는다. 복구된 원 목표에서 정체 보조청산을 무한 반복하지 않는다.
- 위젯 원래 정책의 final EXIT가 우선한다. 보조 주문의 취소와 수량 정합성이 확인되면 기존 EXIT owner로 반환한다. 이미 해제된 목표를 다시 만들었다가 즉시 취소하는 중복 전환은 하지 않는다. 에피소드는 원 target quantity/price를 덮지 않고 별도 successor fill 수량을 보존한다. 삼성 다음 기존 episode는 수량 terminal receipt·확인 시각을 읽으며 원 목표 체결시각/새 수익을 발명하지 않는다.

### 리뷰에서 발견해 수정한 결함

기존 WS projection의 역순 배열을 최신 호가로 잘못 읽는 가정, 6초 polling과5초 관측 gap의 불일치, 원 목표 일부 체결 수량의 초기화, 보조청산 full-fill 후 기존 다음 진입 연결 결손을 수정했다. PIN 철회·원장 fsync 도중 source 변화·의도 저장 후 프로세스 재개·manual veto·서로 다른 leg/root·원 정책 보존을 직접 consumer까지 확인했다. 파일 저장 실패 뒤 같은 객체의 후속 실행은 reload-required로 차단한다. main/widget/episode의 원장을 합치지 않았고 손익 결손은 null이다.

### 자동화의 명시적 예외와 완료 경계

명확한 같은 거래일 receipt로 닫히는 전환/복구는 기존 owner에서 자동 처리한다. **응답 유실로 주문번호가 불명확한 예약, 취소와 동시 전량체결 후 미종결 cancel child, 익일의 재사용 가능한 주문번호/전일 current-ledger 결손은 자동 추정 복구하지 않는다.** 원장을 보존하고 직접 사유와 함께 기존 owner recovery를 기다린다. 따라서 장애와 무관한 완전 무인복구 또는 모든 구간 실거래 활성화 완료라고 표현하지 않는다. 이 예외를 새 연구·다중 승인 플랫폼 구현 목록으로 확대하지 않는다.

기대효과는 목표가 미도달 양수 순수익권의 정체 보유를 줄일 가능성이다. 이후 더 큰 상승을 놓칠 수 있고 비용 추정 오차도 있으므로 수익 증가를 보장하지 않는다. 자연 acceptance는 동일 owner의 비용 후 **총 순이익·자본점유·불리한 결과**이며 거래 건수만으로 판단하지 않는다. 개발 검증, 다른 세션의 배포/설정/PID, 자연 주문 전환, 실제 비용 대사/경제성을 각각 구분한다. 기존 `MachineLifecycleTurnoverObjectiveFollowup0910`은 운영/자연 acceptance OPEN으로 유지한다.

공식 API 재확인: upstream HEAD/local checkout `234560d213acd8871ae344b5481aecd2f30287fa`; 9/10 개발 중 `kiwoom/specs.py`, `kiwoom/core/client.py`, `kiwoom/_data/kiwoom_api_spec.json`의 kt10001/kt10003/kt00007/ka10075와 Postman을 확인했다. 요청/응답 필드는 기존 adapter를 재사용하며 취소 ACK≠terminal, 양수 수량/지정가·동일 account/date/owner·원장 예약 계약을 유지한다. 현재 checkout에 `kiwoom_docs`가 없음을 보존한다.

### 최종 검증 receipt

최종 통합 실행은 `test_profit_stagnation{,_exit}`, 기존 broker/terminal-cancel/owner-loop, low-price, Samsung 오전·정오·오후/오전 재진입, widget signal/notification, machine rebound-reentry의 **975 PASS / 2 기존 owner 비대상 SKIP / 28.20초**다. 별도 main `test_sniper_scale_in.py -k stagnation`은 **16 PASS / 1029 비관련 미선택 / 0.92초**다. 새 helper만이 아니라 현재 owner의 run_once와 실제 정책 pin reader, 임시 registry/원장 재로드·가짜 wire를 포함한다. 마지막 보완으로 원 목표가 이미 executable이거나 취소 직전 source/net 후보가 소실되면 원 목표를 취소하지 않는 것을 확인했다.

변경 Python compile, 신규 파일 Ruff/Black, `git diff --check` 통과. print-only backlog는27행·현재0910 owner1행·중복 제목0이다. 이 최소 변경/직접 consumer 검토 범위에서 남은 코드 finding은0이며, §32의 명시적 외부 receipt 복구 예외와 미배포·자연/경제성 미관측을 코드 결함 해소나 실거래 완료로 바꾸지 않는다. 정상 설정·입력에서 실제 서비스→원 owner 전환까지 구현하는 개발 종료조건을 충족했으며 추가 연구/승인 체계를 새로 개발하지 않는다.

## 33. 관찰 비차단 재검토와 다음 거래일 기대 동작

9/10 18:51~18:58 읽기 전용 운영 확인 및 개발 재검토. 대상 다음 거래일은 **9/11**이다. 배포·재기동·운영 설정 변경은 계속 다른 세션 범위다.

### 발견·수정과 검증

- **위젯 관찰의 진입 차단**: 첫 관찰부터 exclusive claim을 저장하고 `process_payload`가 반환하여 기존 scale-in을 건너뛰는 반례를 재현했다(수정 전 회귀 FAIL). `profit_stagnation_observation`은 주문 권한 없는 계산 상태로 분리하고, 실제 취소 전환부터만 기존 exclusive claim을 저장한다. 관찰 중에는 기존 reconciliation·scale-in 경로를 유지한다. 추가 BUY pending 또는 원가/수량 변경이면 관찰을 폐기·다시 시작하며 원 주문은 변경하지 않는다. WS 관찰 자체에는 broker 조회를 추가하지 않았다.
- **정체 해소 후 불필요한 claim 유지**: 취소 전 후보 철회, 명확한 취소 거절, 확인된 원 목표 복원 후에는 기존 owner로 반환한다. 복원·거절된 목표는 재편입하지 않아 같은 목표의 취소/복원을 반복하지 않는다. 취소 진행·모호한 예약·보조 SELL·미보호 잔량은 계속 exclusive이며 기존 EXIT 우선권·exact 수량 계약을 유지한다.
- **OFF 표시 잔존**: pin 제거 후 예전 `selected` 표시가 남는 경우를 `off_no_policy_pin`으로 바로잡았다. 설정 변경이나 활성화가 아니라 진단 표시 수리다.

직접 회귀는 관찰 중 실제 `process_payload`의 scale-in 호출 도달, pending BUY/원가 변경, 취소 전 철회/복원 후 반환, lock 상실·원장 실패, 기존 취소확정/부분체결/TTL/재시작을 포함한다. 통합 **984 PASS / 2 기존 owner 비대상 SKIP / 29.09초**, 별도 main 정체 계산 **16 PASS / 0.88초**. 대상 helper/bridge/test Ruff·Black 및 변경 Python compile·diff 검사 통과. 이번 변경은 기존 파일4개이며 새 서비스·전략 grid·승인 계층·API protocol 변경은 없다. §32의 외부 receipt 복구 예외는 그대로다. 이 직접 검토 범위 미해결 finding0이며 실거래/경제성은 미검증이다.

### 내일 동작과 자동화 경계

확인한 widget unit은 작업폴더 service·1초 loop, low-price template도 작업폴더 기존 launcher다. widget PID327676은07:58 시작/active로 이번 코드의 새 PID receipt가 아니다. unit/drop-in(없음), systemd manager 환경과 조회 가능한 `.env`/runtime 설정에서 새 policy PATH/SHA256 pin은 발견되지 않았다. `/proc/327676/environ`은 읽기 권한 부족이므로 현재 PID의 모든 환경을 검증했다고 주장하지 않는다. [별도 배포 리뷰의18:31 설치 후속](2026-09-10-fixed-release-postclose-startup-review.md#1831-후속-사용자-승인에-따른-공통-경로-설치)은 main/장후 공통 release에서 적응형 청산을 제외한 기록이며 widget/episode 배포 또는 ON 증거가 아니다.

따라서 별도 배포/설정 receipt가 추가되기 전 **9/11 새 보조 익절 ON을 약속할 수 없다**. 기본 기대는 각 owner의 기존 신호·당일 정책으로 진입하고 원 목표/기존 EXIT를 유지하는 매매다. 에피소드의 두10주 leg·시간창·기존 재진입 조건은 변경하지 않는다. 내일 정책의 실제 종목/값은 장후·당일 기존 loader의 결과로 따로 확인한다.

새 코드와 검증된 비용/기간/hash 설정이 반영되면 기존 서비스가 자동으로 정책을 읽는다. 이후 **양수 추정 순이익 + fresh 전량 잔량 호가 + 연속 정체 → 원 목표 취소확정 → 보호 지정가 보조 익절 → 미체결/부분체결 잔량은 원 목표 복원**을 원 owner에서 자동 수행한다. 최초 코드 배포와 pin/수치 설정은 자동 발행하지 않으며, 기존 오래된 보유를 자동 이관하지 않는다. 이 구분을 “완전 자동 활성화”로 축약하지 않는다.

### 목적 적합성과 적용 조건

메인1% 최소수익을 기계에 복사하지 않았고, 새 최소 표본·5/10/20일 동시 floor·최초 활성화 전 새 exit 실체결을 요구하지 않는다. 유효한 비용/정책·양수 net·fresh depth·원 주문 terminal·단일 owner 조건은 유지한다. 정체시간은 승인 정책 값이며180초 참조값을 최적치로 주장하지 않는다. 기존6초 episode polling보다 짧은 관찰 gap을 설정하면 매번 창이 초기화되므로 실제 loop 간격/지연을 수용하는 값의 운영 검증이 필요하다; 호출량/호가 신선도 완화로 해결하지 않는다.

예상 이점은 **원 목표 아래 양수 순수익권에서 정체된 보유를 줄여 자본을 회수할 가능성**이다. `비용 손익분기 < 실행 가능한 매도가 < 원 목표가` 구간 자체가 없는 짧은 tick 목표에는 이 보조 기능의 기회가 없다. 모든 profile의 매매 빈도/수익 증가를 보장하거나 이를 위해 target·수량·손절을 변경하지 않는다. 더 큰 후속 상승을 놓치거나 비용 추정 오차가 생길 수 있다. 실제 효과는 비용 후 총 순이익·양수 완료 빈도·자본점유·불리한 결과를 함께 보며, 표본 부재를 새 구현 순환으로 만들지 않는다. 기존 `MachineLifecycleTurnoverObjectiveFollowup0910`에서 운영/자연 acceptance만 이어간다.

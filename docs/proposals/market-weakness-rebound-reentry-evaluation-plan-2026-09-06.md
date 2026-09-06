# Market weakness 반등·재진입 평가 구현안과 다음 권장 액션

작성일: `2026-09-06 KST`
상태: **1차 구현·검증 완료(1,075 PASS) / 일반 2-leg episode bounded 자동 PREOPEN 연결 / 자연 EV 미확인**

## 현재 실행 계약 — 2026-09-06 후속 사용자 지시

사용자가 조건 충족 시 별도 명시적 승인 없이 자동 장전 적용하도록 지시했다. 아래 최초 계획의 “실전 설계 검토 후 별도 승인”은 이번에 구현한 **일반 2-leg episode의 flat 신규 진입 한 scope**에 한해 이 상시 승인으로 대체된다. 다른 family의 승인·operator lock은 변경하지 않는다.

- owner가 자연 검증한 유효 신호를 기록하고, 기존 재개 A0와 약세 중 최초 상승·반등 A2의 owner-target 모델 경제성을 기존 timing 보고서의 별도 section에서 비교한다. 횡보는 상승이 아니며 시장 회복만으로 주문하지 않는다.
- A1은 현행 재개의 중복 귀속 진단이다. A0와 동일하면 별도 전략이나 정책을 만들지 않는다. A0 이후 실제 owner 신호가 없는 사례를 가격만으로 만들어 A1 EV라고 보고하지 않는다.
- 자동 적용은 기존 양 leg 모두 현재 ask/충분한 depth로 즉시 실행 가능한 범위다. 미체결 취소·target ticks·quantity·no-stop·주문/계좌/소유권/유동성/가격/하드 가드는 그대로다. 새 독립 주문 함수는 없다.
- 표본은 exact scope 5일·8 unique pair, paired coverage 85%, 누적 ΔEV ≥0.005%p, rolling 5일/최신 날짜 holdout ΔEV >0, 각 창 candidate EV >0, p10 악화 ≤0.01%p다. Samsung 자연 표본 lag 4거래일, 기타 1거래일을 허용한다. 10/20일 창은 미완결이면 진단 unavailable이며 추가 승인 허들이 아니다.
- 장후 `machine_entry_timing_tuning` → 기존 장전 wrapper의 동일 CLI `--phase preopen --write` → source 재평가·같은 단계 충돌 검사 → immutable evidence snapshot/exact-date receipt → regular owner의 진입·동일 batch 재검증이다. 사용자 재승인 파일은 없다. 장전 자동 적용 스위치가 OFF이면 쓰지 않고, 08:00 이후에는 발행하지 않는다.
- 정책 누락/변조/만료·scope 불일치·source 또는 EV 재검증 실패는 baseline이다. 장전 재검증 실패 시 해당 날짜 family receipt를 비활성 baseline으로 원자 갱신한다. 생산 보고서 재생성은 immutable 적용 snapshot을 변경하지 않는다.
- 위젯 순차매수·부분/수동체결·대기 지정가·terminal no-entry receipt 없는 A0·세션 초과 no-stop outcome은 아직 지원하지 않는 replay 범위다. `gap_handoff`로 수리/범위 축소에 전달하며 “기다리면 완료된다”고 표시하지 않는다. 모든 최초 계획 범위가 구현됐다는 의미가 아니다.
- 원천은 자연 owner journal과 기존 attribution의 단일 raw decode를 사용한다. 비적용 관측은 parent당 최대 최초/반등/재개의 세 기록으로 축약한다. 공통 정규 세션 관측 종료까지 owner target touch를 비교하며 30분 강제 청산은 없다. target touch는 실체결이 아니다.
- 재개 없이 scan이 끝난 경우 기존 owner loop의 정상 연속 추적·무보유/미시도 terminal receipt가 있으면 A0 손익 0을 인정한다. 추적 공백이나 source 실패는 여전히 결손이다. 재개 주문을 반드시 요구하여 약세일의 미진입 연구를 영구 차단하지 않는다.
- 격리 확인 CLI는 `--report-only-dir <production 외 경로>`다. report와 policy 원본을 덮지 않으며 snapshot이 참조하는 production report hash도 보존한다. 봇 재기동·생산 정책 발행은 이번 offline 검증에 포함하지 않는다.

아래 P0~P6와 원 설계는 전체 목표와 미지원 범위의 검토 근거로 남긴다. 현재 구현/검증 결과의 정본은 [구현 리뷰](../audit-reports/2026-09-06-rebound-reentry-implementation-review.md)다.

## 1. 판정과 목표

반등·재진입 평가는 구현한다. 다만 독립 전략·별도 cron·실주문 경로를 만들지 않고 기존 Machine entry timing의 **source-only 경제성 평가 section**으로 통합한다. 현행 guard 유지, 회복 후 재평가, 약세 중 개별 종목 반등 가설의 비용 차감 증분 EV를 비교하고, 차이가 없거나 지속적으로 근거를 만들 수 없는 arm은 종료/on-demand 전환 대상으로 판정한다.

핵심 목표는 매수 횟수 증가나 손실 회피 자체가 아니라 **유효한 상승·반등 기회를 보존하면서 순이익을 개선할 수 있는지 식별**하는 것이다. 시장 회복만으로 매수하거나 만료 신호를 부활시키지 않는다. 기존 주문·보유·수량·target/exit·scan window·operator lock·broker/hard safety를 보존한다. 폐기된 ADM/LDM·swing·panic-buying 경로는 재사용하지 않는다.

현재 근거는 [R1~R5 보완 리뷰 §8](../audit-reports/2026-09-06-market-panic-breadth-remediation-review.md#8-r1r5-보완재검증-및-반등재진입-구현-결정)다. 기존 데이터의 읽기 전용 재평가에서 정상 breadth 관측 688건, 유효 30분 CF 4/778건을 확인했지만 실제 realized 비교는 0건이며 개선 후보도 없다. 이 4건을 새 재진입 paired 표본으로 간주하지 않는다. 9/7 정책 2/3 carry-forward는 유지한다.

기대효과는 다음 세 가지이며 아직 실현 성과가 아니다.

- 기존 매수 재개와 새 개선안을 중복 계산하지 않고, 회피 손실과 놓친 상승을 동일 기회 단위에서 비교한다.
- 실제 주문이 없어서 평가도 영구적으로 0건이 되는 경로를 분리한다. 관측 가능한 source-only 비교를 생성하되 실체결 성과로 승격하지 않는다.
- 원천·신호·경제성·적용 계약 중 어디서 막히는지 수량과 사유로 노출해 유지/수리/중단 결정을 가능하게 한다.

## 2. 현재 코드에서 확인한 제약과 통합 위치

| 경로 / 현재 사실 | 구현 설계 |
| --- | --- |
| [`machine_entry_timing_tuning.py`](../../src/engine/automation/machine_entry_timing_tuning.py)의 `ENTRY_ROLES`는 actual widget signal / episode decision leg다. `_dynamic_baseline_observation()`은 owner outcome과 replay를 요구한다. | 미매수 사례를 기존 실제 주문 cohort에 섞거나 `actual_order_submitted=true`로 바꾸지 않는다. 별도 입력·집계 section을 동일 보고서에 추가하고 기존 `runtime_winner` 선택에는 전달하지 않는다. |
| [`machine_market_weakness_response.py`](../../src/engine/monitoring/machine_market_weakness_response.py)는 market별 latch 및 CF를 제공하나 delay/relative-strength arm은 `integration_required`다. | 시장 상태·원인 연결을 재사용한다. 재진입 평가의 정본은 timing 보고서 한 곳으로 하고 attribution은 원천과 lineage만 제공한다. 역방향 순환 의존이나 두 곳의 동일 EV 계산을 만들지 않는다. |
| [`market_weakness_entry_guard.py`](../../src/engine/risk/market_weakness_entry_guard.py)의 blocked anchor는 실제 guard 적용 사실과 source-only CF 권한을 구분한다. | outer `runtime_effect=true`를 평가 결과로 복사하지 않는다. 새 section은 항상 source-only 권한이다. blocked 사실만으로 나머지 매수 조건이 모두 통과했다고 추정하지 않는다. |
| [`regular_two_leg_machine.py`](../../src/trading/order/regular_two_leg_machine.py), [`widget_auto_trade/engine.py`](../../src/trading/widget_auto_trade/engine.py)는 약세 차단 시 일부 신호·attempt를 소비하지 않고 해제 후 재평가한다. | 현행 재개 동작을 A0 control에 반드시 재현한다. 이미 같은 시각·가격·행동으로 재개되는 사례는 새 알파가 아니라 `equivalent_to_control`이다. |
| [`micro_confirmation.py`](../../src/trading/market/micro_confirmation.py)는 신호 기준 0/1/3/5초 causal checkpoint와 owner별 dynamic confirmation을 공유한다. | 수분 뒤 시장 회복을 `entry_confirmation_delay_sec=300` 같은 값으로 위장하지 않는다. 새 유효 신호 시각에 0/1/3/5초 확인을 다시 기준 맞춤한다. |
| 일반 dynamic policy의 bid return 하한은 0bps이며 Samsung 전용은 2bps다. | 단순 횡보를 상승으로 부르지 않는다. 연구 arm의 상승/반등 여부는 별도 명시적 causal 판정으로 기록하고 기존 live threshold는 바꾸지 않는다. |
| [`machine_entry_timing_policy.py`](../../src/trading/config/machine_entry_timing_policy.py)는 fixed/dynamic confirmation만 허용한다. | 반등 가설 통과를 기존 timing 정책으로 몰래 발행할 수 없다. 신규 live 의미가 필요하면 별도 versioned 범위·허용 동작·owner 계약을 설계/승인해야 한다. |
| [`run_machine_microstructure_final_refresh.sh`](../../deploy/run_machine_microstructure_final_refresh.sh)는 attribution→hysteresis→timing→policy approval→checklist를 실행한다. | 기존 timing 단계에서 평가 section을 자동 생성하도록 연결한다. 신규 timer/독립 전수 스캔은 만들지 않는다. 평가 section 부재/실패가 정상 완료로 은폐되지 않도록 verifier·summary에 연결한다. |

문서 위치는 `docs/proposals`다. 이후 순수 evaluator가 필요하면 `src/engine/monitoring/machine_rebound_reentry_evaluation.py`에 두고, orchestration/누적 집계·판정은 기존 `src/engine/automation/machine_entry_timing_tuning.py`가 소유한다. `src/engine` root 신규 모듈과 compatibility wrapper는 만들지 않는다. 이 모듈명·section/schema 이름은 제안이며 현재 callable 구현이 아니다.

## 3. 평가 대상과 비교 arm

### 3.1 대상·기회 단위

- 초기 범위는 활성 widget/episode의 **포지션 없는 신규 진입 기회**다. 기존 episode가 정상 종료된 뒤 owner 규칙으로 허용되는 다음 신규 진입은 별도 entry state로 포함할 수 있다. 추가매수, 부분체결 잔량, 보유 청산, 진행 중 원주문 취소/대체는 제외하고 제외 수를 보고한다.
- 키는 `trade_date + owner + scope_id + symbol + listing_market + execution_venue + session + entry_state + parent_opportunity_id`다. KOSPI/KOSDAQ는 상장시장, KRX/NXT/SOR는 집행 경로이므로 서로 대체하지 않는다. SOR는 실제 선택 route와 확인 가능한 quote lineage가 없으면 해당 사례를 제외한다.
- 원 blocked signal을 parent로 하고 같은 owner의 후속 신호 generation을 자식으로 결속한다. 같은 signal의 반복 poll, leg 2개, 연속 block 로그를 독립 표본으로 세지 않는다. 동시에 겹치는 parent에는 후속 신호를 중복 배정하지 않는다.
- A0의 아직 유효한 기존 신호 재평가는 보존한다. A1/A2의 fresh signal은 실제 owner 이벤트/완료 봉·generation 또는 **원 유효기간 안에서 owner가 다시 검증한 현재 decision**으로 확인한다. 같은 signal ID라는 이유만으로 정상 재평가를 배제하지 않으며, 새 평가 시각의 상승/반등·유효성 근거를 요구한다. loop마다 임의 ID를 발급하거나 재평가 시 원 만료시각을 연장하지 않는다. 원 신호가 만료되면 독립적으로 성립한 새 owner 신호가 필요하다. 어느 경우에도 기존 daily count/cooldown/scan window 제한은 그대로다.
- owner/profile/시장/session/state별 결과를 분리한다. 초기 산출은 원천이 있는 모든 활성 scope에 대해 시도하되 일부 scope 결손이 정상 scope의 진단 생성까지 막지 않도록 한다. 승격 근거를 만들려고 서로 다른 owner·시장·세션을 합치지 않는다.

### 3.2 고정 비교안 — 초기에 grid 탐색하지 않음

| Arm | 판단과 관측 행동 | 구분해야 할 효과 |
| --- | --- | --- |
| A0 `current_guard_control` | exact-date 현행 guard/TTL·owner 재평가·유효성·기존 confirmation·수량/target/exit를 그대로 재현 | 단순 `skip forever`가 아니다. 실제 자동 재개를 포함한 기준 행동이며 receipt와 대사해야 한다. |
| A1 `recovery_then_fresh_owner_signal` | 동일 listing market의 정상 source로 회복 확인 후, 기존 scan window 안에서 새 유효 owner 신호 및 상승/반등·기존 confirmation을 만족한 최초 시점만 선택 | 회복 후 진입의 비용·지연·놓친 상승을 A0와 비교한다. A0와 동일하면 중복 arm으로 닫는다. 더 늦게 들어가는 효과가 악화될 수도 있다. |
| A2 `fresh_owner_rebound_during_weakness` | market latch가 fresh active인 상태에서 새 유효 owner 상승/반등 신호, 비용 후 양의 가격 여지, 기존 micro/source/유동성 조건이 확인되는 최초 시점 | **연구에서만** market veto 예외의 경제성을 계산한다. 비시장 guard까지 확인된 경우만 시장 단일 blocker의 실행 가능 기회로 분류한다. 미평가 guard는 경제성 가능성과 실전 도달 가능성을 분리해 표시한다. 실제 veto/cancel은 우회하지 않는다. |

상승은 causal pre-signal bid보다 개선되었는지, 반등은 **현재 checkpoint까지** 관측된 저점 대비 기존 owner confirmation recipe의 반등 기준을 만족하는지로 확인한다. `bid return=0`만 있는 횡보, 체결/호가 근거 없는 상대강도, 이후 고점·최저점·target 도달 결과를 입력으로 쓰는 판정은 제외한다. Samsung 전용 recipe와 일반 owner recipe의 차이는 보존한다.

TTL 만료·observer 실패는 `recovery_confirmed`가 아니다. A0는 실제 TTL 동작을 재현하지만 A1의 정상 회복 시점으로 사용하지 않는다. 회복이나 새 신호를 기다리다 scan/유효기간이 끝나면 `expired_no_entry`다. 해당 owner의 next-session 신규 신호는 다른 기회이지 오래된 신호의 부활이 아니다.

## 4. 원천과 평가 로직 구현

### 4.1 P1: 최소 source contract부터 닫기

기존 blocked anchor, 허용/차단 guard receipt, owner 이벤트/정책 snapshot, exact-route 0B/0D를 먼저 조인한다. 부족한 필드만 기존 owner 기록 경로에 보완한다. 실제로 진행하지 않은 뒤쪽 broker/account 검사 결과를 `passed`로 기록하거나 평가를 위해 신규 계좌/주문 API를 호출하지 않는다.

`economic_pair_eligible`과 `runtime_reachability_status`를 분리한다. 신호·요청수량/가격·owner recipe·quote/비용이 완결되면 source-only 경제성은 계산할 수 있다. 미매수로 인해 호출되지 않은 broker/account 검사 자체를 이 계산의 필수 실주문 증거로 요구하지 않는다. 다만 known blocked/unknown/verified를 별도 strata로 보고하고, unknown을 시장 단일 blocker나 live-ready로 해석하지 않는다. 가격·수량·owner exit 등 **경제성 자체에 필수인** 결손은 계속 제외한다. 따라서 경제성 계산을 열기 위해 안전검사를 우회할 필요도, 가상 검사 통과를 합성할 필요도 없다.

필수 입력은 다음과 같다.

| 입력 묶음 | 최소 결속 필드 / 실패 판정 |
| --- | --- |
| 기회·신호 | parent/child signal ID, generation, decision/event/received 시각, source bar, owner/scope/session/state, observed validity/cutoff, 최신 snapshot 기준 non-market blocker 결과. 미평가 결과는 `unknown_not_evaluated` |
| 시장 | listing market 검증 근거, observation ID/hash, 정책 hash, latch/replay version, last healthy 시각·age, recovery/TTL/source-failure 사유 |
| owner 계약 | 적용 정책 hash, 기존 가격해결기 limit, 실제 요청/계획 수량과 leg 구조, target/exit recipe, position/open-order/daily count/cooldown 상태와 관측 시각. 필수 context를 사후 추정하지 않음 |
| micro | source/PID/manifest/REG receipt, symbol/item/venue/session/sequence epoch, signal 및 각 checkpoint의 bid/ask·depth·trade backing·refill·freshness. 원 timestamp와 receipt 순서 충돌 시 제외 |
| outcome | A0 실제 receipt와 모델 대사, 각 가설의 자체 entry/target/exit·observed path·종료/검열 상태, 비용 버전·source hash. 다른 arm의 실제 매도가를 근거 없이 재사용하지 않음 |

신규 source section 제안은 attribution의 `market_weakness_rebound_reentry_source_v1`이다. 정상/결손 행을 분리하고 원 guard 기록의 실전 권한과 독립된 `runtime_effect=false`, `allowed_runtime_apply=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`, `decision_authority=source_only_rebound_reentry_evaluation`을 명시한다.

현재 collector가 기존 t0에만 30분 horizon을 제공한다면 후속 신호 시점의 BBO를 대신할 수 없다. 등록된 기존 owner/route의 자연 이벤트에 새 anchor를 결속하고 그 시각 이후 필요한 checkpoint/outcome을 수집한다. 신규 종목/구독 범위 확장·bot restart는 이 계획의 자동 권한이 아니다. Kiwoom protocol·FID·REG/복구 로직 수정이 실제로 필요하면 공식 reference gate를 별도로 통과한다.

### 4.2 P2: 순수 paired replay

1. clean baseline `2026-06-05 KST` 이후 원천과 exact-date source-quality exclusion을 적용한다. 중복/경쟁 identity와 semantic conflict는 행·window별 제외하며 정상 자료를 보존한다.
2. A0를 실제 guard/owner receipt와 먼저 대사한다. causal cut-off까지의 입력만 사용하며 실제 동작 불일치는 전략 효과가 아니라 `baseline_replay_mismatch`다. legacy 실제 모델과 현재 TTL 가설은 별도로 유지한다.
3. 후속 유효 owner 신호를 시간순으로 처리하고 A1/A2가 최초로 만족하는 시점을 선택한다. 결과를 본 뒤 가장 수익이 좋은 진입 시각을 고르지 않는다. 새 신호에서 기존 0/1/3/5초 checkpoint 함수를 재사용한다.
4. 미래의 실제 fill 가격을 checkpoint 입력으로 쓰지 않는다. causal owner limit/요청수량과 fresh BBO/depth로 실행 가능성을 검사한다. 가격 미도달·depth 부족을 실제 full fill로 합성하지 않는다.
5. 각 arm의 entry부터 **그 arm의 기존 owner target/exit 규칙**을 적용한다. 2-leg면 leg별 가격·수량·target을 보존해 full-position 경제성을 계산하고 partial/full은 분리한다. 첫 target touch는 시장 경로상 모델 결과이지 broker fill 증거가 아니다.
6. target/exit 경로를 재현할 원천이 부족하면 `owner_exit_replay_gap`, 아직 종료 안 됐으면 `right_censored`다. no-stop 보유를 임의 30분 청산으로 바꾸지 않는다. 기존 completed outcome 평가와 별도로 1/3/5/10/20/30분 markout을 진단할 수 있으나 실제/terminal EV로 바꾸지 않는다.
7. markout 비교는 parent 기준 **같은 평가 종료 시각**을 사용한다. 늦게 진입한 arm에만 추가 30분을 줘 유리한 미래 구간을 더 주지 않는다. horizon별 eligibility를 분리하고 다른 horizon 결손을 전파하지 않는다.

비거래 손익 0은 source가 완결되어 해당 arm이 유효기간 내 거래하지 않았음이 확인된 경우에만 사용한다. 신호·quote·owner 상태 결손, 미완료 거래를 0으로 채우지 않는다. 겹치는 기회는 같은 owner의 상태/수량 한도와 일별 진입 제한을 재현하며 하나의 후속 주문을 여러 parent에 중복 귀속하지 않는다.

### 4.3 성과 산식과 결과 분리

동일 parent의 최초 결정 시점에 고정한 비교 기준금액 `B_i`를 모든 arm에 공통으로 사용한다. 기존 요청수량/owner limit으로 재현할 수 없으면 해당 기회는 경제성 제외다. 후보마다 유리한 미래 가격으로 기준금액을 다시 정하지 않는다.

`R(i, arm) = 100 × modeled_net_profit_krw(i, arm) / B_i`
`ΔR(i, arm) = R(i, arm) − R(i, A0)`

- primary는 완결된 동일 표본에서 `mean(ΔR)`이며 `primary_ev.source_quality_adjusted_ev_pct`로 기록한다. 각 arm의 수준 EV와 delta의 `metric_basis`를 구분한다. A0가 원래 매수하지 않았던 비용 없는 기회를 포함해 분모를 고정한다.
- 순이익 원화·capital-minute, p10, 놓친 상승/회피 손실·coverage·미완료 비율은 함께 보고한다. 단순 수익률 합계나 승률로 대체하지 않는다.
- 비용은 기존 `comparison_cost_contract(source_date)`와 해당 owner/venue 비용 계약을 재사용하고 수수료/세금/spread/slippage 중복 차감을 검사한다. BBO 모델·비교 비용을 broker-exact로 표기하지 않는다.
- `actual_realized`, `modeled_owner_exit`, `horizon_markout`은 별도 evidence class다. A0 실체결과 모델의 오차도 분리한다. 실제 realized는 `COMPLETED + valid profit_rate`만 허용한다.
- A0/A1/A2 공통 완결 표본 비교와 각 arm의 제외/검열 분포를 함께 내고, 특정 arm의 손실/미완료 사례만 탈락시키지 않는다. 더 넓은 A0-A1/A0-A2 pair 비교는 별도 분모를 표기하고 그 평균으로 서로의 우열을 직접 결정하지 않는다.

## 5. 산출·자동화·권한 계약

### 5.1 같은 보고서 안에서 생성

`machine_entry_timing_tuning_YYYY-MM-DD.{json,md}`에 `market_weakness_rebound_reentry_evaluation` section을 추가한다. source schema/hash·case trace·A0/A1/A2·daily/rolling/cumulative·제외 사유·달성가능성·다음 조치를 담는다. 현재 `micro_entry_confirmation`의 actual-only 승인 cohort와 별도다. 새 자료가 existing winner, policy scopes, `actual_order_submitted` 의미를 바꾸지 않는 회귀를 필수로 둔다.

제안 metric contract:

| 항목 | 계약 |
| --- | --- |
| `metric_role` | `paired_market_weakness_rebound_reentry_evaluation` |
| `decision_authority` | `source_only_rebound_reentry_evaluation` |
| `window_policy` | clean baseline 이후 exact scope daily diagnostics + fixed rolling 5/10/20 source-day 및 cumulative; look-ahead 없는 versioned pair |
| `sample_floor` | 보고서/결손 census는 0건도 생성. case trace는 유효 1건부터. 정책 설계 검토용 provisional 조건은 §6이며 live approval과 다름 |
| `primary_decision_metric` | `source_quality_adjusted_ev_pct` — 동일 기준금액/동일 표본의 A0 대비 증분 |
| `source_quality_gate` | exact identity/route/causal signal·market health·owner context·BBO/depth·비용·해당 outcome 계약 |
| `forbidden_uses` | expired signal revival, market-recovery-only BUY, missing-as-zero, counterfactual-as-realized, actual-only policy cohort contamination, live veto/cancel/quantity/target/provider/bot/cap/hard-safety mutation |

### 5.2 상태와 handoff

| 상태 | 의미 / 다음 액션 |
| --- | --- |
| `integration_required` | 아직 구현 안 됨. 자연 표본 대기로 해소되지 않음 |
| `no_natural_opportunity` | 수집/owner census는 정상이나 대상 기회 없음. 전략 실패나 실전 확대 근거가 아님 |
| `source_contract_gap` / `baseline_replay_mismatch` | source 또는 대사 결함. 해당 행/window 제외 + exact owner 수리 작업 항목 |
| `owner_exit_replay_gap` | markout은 있을 수 있어도 owner별 완료 경제성 구현/원천 없음. 수리/범위 축소 결정, 무기한 maturity 대기 금지 |
| `outcome_pending` / `hold_sample` | 구현·원천은 정상이고 검열/표본만 부족. 실제 유입률·완결률이 확인된 경우에만 유한한 추정치를 제시 |
| `equivalent_to_control` | 동일 행동/가격/시각/경제성의 중복 arm. 독립 후보 제거, baseline 귀속 검사만 유지 |
| `hold_no_edge` | 검토 가능한 표본에서 순비용 우위 없음. baseline 유지 및 arm on-demand/중단 검토 |
| `source_only_positive_needs_runtime_design` | 유효 비교가 양수이나 실전 적용 계약 없음. 실제 예외 적용 완료가 아님 |

부재/예외로 section을 누락하거나 기존 timing 보고서 전체를 빈 성공으로 덮지 않는다. evaluator 계약·실행 실패는 해당 follow-up을 FAIL로 남기고 정상 기존 tuning 결과/정책은 보존한다. 자연 0건·성숙 대기는 정상 상태와 원인 census를 출력한다. existing policy approval/checklist builder는 새 section의 상태·owner·next action만 소비하며 새 후보를 existing policy approval에 오인 연결하지 않는다.

검증용 재생성에는 report-only/no-policy-write 실행면을 추가한다. 현재 `--write`는 정책 발행을 동반할 수 있으므로 이를 그대로 검증 명령으로 사용하지 않는다. 기존 `write_outputs(..., publish_policy=False)`를 재사용하되 기본 scheduling 의미는 바꾸지 않고, 임시/검증 output dir과 production policy hash 불변을 시험한다. 새 플래그명은 구현 때 확정하며 이 문서는 존재하지 않는 CLI를 실행하도록 지시하지 않는다.

`publish_policy=False`만으로는 충분하지 않다. 기존 timing loader가 production source report의 hash도 검증하므로 그 보고서를 제자리 재생성하면 적용 정책이 무효화될 수 있다. 검증 output은 production source와 다른 경로에 고정하고, 정책 파일뿐 아니라 참조 보고서 bytes/hash·기존 loader 판정도 불변인지 확인한다. 자연 다음-session 발행 때 새 report hash가 바뀌는 것은 정상이나 selected scope/동작이 새 연구 section 때문에 달라지면 회귀다.

### 5.3 처리 비용과 반복 실행 범위

- attribution의 기존 단일 raw decode/route index를 재사용한다. A0/A1/A2별 전체 JSONL 재스캔이나 모든 과거 거래일의 반복 replay는 금지한다. 장중에는 bounded source receipt만 기록하고 경제성 계산은 장후에 둔다.
- normalized case 결과는 `source hash + owner policy hash + replay/schema version + opportunity ID`로 재사용한다. 변경된 source 날짜와 pending outcome의 새 원천만 갱신하며 rolling 5/10/20은 같은 case 집계에서 계산한다. 원천/hash가 달라지면 cache를 무효화한다.
- 자연 기회가 0건이면 census/정상 상태만 생성하고 quote/outcome 전량 decode를 건너뛴다. `integration_required` 또는 복구 불가능한 과거 source를 매일 다시 시도하지 않는다.
- 구현 검증에서 동일 데이터의 before/after wall-clock, CPU, peak RSS, read bytes, cache hit/재평가 case 수를 기록한다. 신규 독립 스케줄 0개·AI 호출 0회·추가 브로커 API 호출 0회를 유지한다. 정기 실행 비용이 큰데 eligible pair가 늘지 않으면 P5에서 수리 또는 on-demand 전환을 판정한다. 아직 측정하지 않은 속도 개선율을 기대 성과로 확정하지 않는다.

## 6. 허들·유지 여부·향후 실전 적용 판단

### 6.1 세 단계의 조건을 분리

1. **구현 수용:** source-only paired fixture 1건부터 끝까지 계산되어야 한다. 원천 0건이어도 완전한 census/상태 보고서가 생성된다. 실제 주문/완료 거래를 필수로 요구해 미매수 연구를 막지 않는다.
2. **실전 설계 검토를 열 최소 근거(신규 제안, 자동 승인 아님):** exact scope에서 5개 유효 source trading date·8개 unique paired opportunity·8개 완결 paired outcome을 초기 기준으로 삼는다. 이는 기존 dynamic timing 5일/8 lifecycle/8 outcome을 참고한 검토 기준이지 기존 live 승인을 blocked CF로 대체하는 것이 아니다. 해당 scope의 paired/replay coverage 85% 이상을 참고하고 우량 표본만 남는 편향을 검사한다. 공통 완결 분모·검열 비율 정의를 구현 시 고정해 분모를 유리하게 바꾸지 않는다.
3. **경제성과 독립 검증:** 사전에 고정한 A1/A2와 거래일 순서의 calibration/최신 날짜 holdout으로 비교한다. holdout이 독립 날짜/고유 기회를 갖지 못하면 `hold_sample`이다. cumulative·완결 rolling 5일과 holdout의 비용 차감 delta가 모두 양수이고 절대 candidate EV도 양수여야 실전 설계 검토를 연다. 초기 최소 개선폭은 existing timing의 `0.005%p`, p10 악화 허용 상한은 `0.01%p`를 재사용하는 제안이며 source-only 검토에서 비용 민감도를 함께 확인한다. 작은 표본의 통과를 통계적 수익 보장으로 해석하지 않는다.

보고서 생성에 10/20일 창 전체 완결을 요구하지 않는다. 창이 덜 찼으면 unavailable로 표시하며 live 기준을 daily-only로 바꾸지는 않는다. 시장 hysteresis 공통 policy의 10일/50건·양 owner/market/OOS floor는 별개로 유지한다. 새 source-only 평가에 그 공통 floor를 복사하지 않으며, 한 scope의 우위를 공통 market veto 해제 근거로 쓰지 않는다. 오분류 건수 비증가, 무조건 같은 날 실체결 발생, 모든 horizon 동시 완결 조건은 추가하지 않는다.

### 6.2 무기한 대기 방지

- P1/P2 첫 재평가에서 `natural opportunities → owner context → fresh signal → BBO/confirmation → executable entry → completed/pending outcome → comparable pair` 전환 수를 표로 낸다. 최초 소진 단계의 담당 함수/필드/수리 테스트를 지정한다.
- 현재 4/778 CF, 58일 단순 외삽은 반등·재진입 표본 유입률이 아니다. 새 paired 표본의 yield가 확인되기 전 완료 예상일을 만들지 않는다.
- 첫 주 점검일은 `2026-09-11`로 잡되, 구현·정상 원천 시작 후 실제 관측일이 부족하면 조기 현황 점검으로만 해석한다. 기회가 있었는데 pair가 0이면 단순 대기가 아니라 구조 수리/범위 축소를 검토한다. 기회 자체가 없으면 `no_natural_opportunity`다.
- A1이 A0와 구조적으로 같은 코드 경로면 추가 표본을 기다리지 않고 독립 개선 arm을 제거한다. 완결된 자연 사례로도 행동 동일성이 반복되면 중복 진단으로 유지할 필요만 평가한다.
- A2가 검토 가능한 근거에서 비용 차감 우위가 없으면 기존 guard를 유지하고 정기 평가 중단/on-demand 전환을 권고한다. 소수 손실 사례만으로 모든 반등 연구를 폐기하지 않는다.
- owner exit가 구조적으로 재현 불가한 scope는 `owner_exit_replay_gap`으로 분리하고 구현비용/개선 가능성을 비교한다. 원천 없는 과거 거래일을 반복 재생성하거나 no-stop 청산을 합성해 성과를 만들지 않는다.

### 6.3 실전 연결: 현재 상시 승인과 미지원 범위 분리

기존 timing fixed/dynamic 정책과 hysteresis 정책의 자동 발행/소비는 유지한다. 후속 사용자 지시로 일반 2-leg episode의 지원 범위는 조건을 충족하면 **추가 승인 없이 다음 PREOPEN에 자동 적용**한다. evaluator 자체는 source-only이며 별도 exact-date 적용 receipt를 실전 owner가 검증해야 한다.

reviewed source hash·exact owner/symbol/listing market/venue/session/state·새 schema·한 scope·다음 session·rollback·실전 provenance를 결속한다. 선택 scope 외에는 baseline이며 양의 CF를 실체결 성과로 승인하지 않는다. 미체결 취소·보유·추가매수는 변경하지 않는다. 위젯 순차매수 등 미지원 owner recipe는 구현/검증 과제이며 사용자 승인 파일이 없어서 막히는 상태가 아니다.

## 7. 권장 실행 순서와 완료 기준

| 순서 | 다음 액션 | 완료 기준 / 담당 체크리스트 |
| --- | --- | --- |
| P0 다음 정상 session | 기존 9/7 2/3 policy, manifest/0B·0D receipt, health/TTL·허용/차단 receipt 확인 | 정책 준비와 실제 PID 소비를 분리. 자연 source 확인은 `MarketWeaknessNaturalEvidence0907` 및 기존 `MachineExactRouteReceiptRuntimeAcceptance0907`; 기동/구독 확대를 자동 허용하지 않음 |
| P1 구현 착수 시 | blocked/allowed/new-signal/owner context 최소 source adapter와 parent identity·실패 census | 실제 미제출 사례가 source-only 입력으로 수용되고 duplicate·미평가 guard·만료 신호가 구분됨; `MarketWeaknessReboundReentryIntegration0907` |
| P2 | 순수 A0/A1/A2 causal replay·owner exit/markout 분리·동일 분모 EV | 상승·반등 조건, A0 parity, 비용·수량·route·검열 반례 통과; 같은 integration owner |
| P3 | timing JSON/Markdown section·기존 final-refresh/approval-summary/checklist handoff·report-only 재평가 실행면 | 자연 0건/미구현/실행 실패/양수 후보가 분리되고 existing policy 결과 불변; 같은 integration owner |
| P4 | 코드리뷰→수리→재리뷰→회귀 뒤 격리 재평가 | 첫 8/31~9/4 재평가로 복구/복구 불가 범위를 명시하고 이후 새 source 거래일을 검증. 생산 정책/원자료 hash 불변 및 review gate 종결; 같은 integration owner |
| P5 첫 주/유효 창 확보 시 | paired yield·원인·A1 중복·A2 순비용 우위와 유지비용 판정 | 유지/수리/중복 제거/on-demand/실전 설계 검토 중 하나. `MarketWeaknessReboundReentryRetention0911` |
| P6 양의 독립 근거가 있을 때만 | 지원 scope의 exact-date PREOPEN 자동 발행·실전 소비 | 추가 사용자 승인 없이 재검증 후 적용. 미지원 recipe는 코드/원천 과제로 분리하며 P5에 수리/범위 축소 판정 기록 |

P0의 자연 검증과 offline 구현은 서로 기다릴 필요가 없다. 다만 신호·0B/0D 입력의 자연 생성과 경제성 검증 전에는 실전 효과를 주장하지 않는다. 최초 계획 수립 시에는 코드/정책 변경이 없었으며, 후속 구현 지시의 현재 범위는 문서 상단 실행 계약을 따른다.

## 8. 구현 후 필수 리뷰·회귀

- 원천: historical v1/v2 구분, clean baseline, duplicate/conflict, as-of/received 순서, venue/session/epoch 불일치, 정상/결손 scope 분리.
- 시간/신호: TTL 300/301초, source failure를 회복으로 오인하지 않음, 같은 timestamp 순서 불명확, 만료 signal, 재시작/역순 기록, 새 signal generation, scan cutoff, 기존 재진입 cooldown/daily limit.
- 조건: 횡보는 상승 아님, 저점 이후 실제 반등, fake trade backing/refill, fresh·stale BBO, 단일 market blocker와 비시장 미평가 blocker 구분.
- 경제성: A0 parity·A1 equivalent, 최초 만족 시점 vs 사후 최적 시점, 비용 중복 차감, 같은 기준금액/종료 시각, no-entry 0 vs missing null, partial/full·2-leg·manual exit 구분, arm별 target/exit·right censor, 후속 신호 중복 귀속 차단.
- 권한/자동화: evaluator gateway/API 호출 0, real event authority 복사 금지, existing runtime winner/policy 불변, 지원하지 않는 새 mode 거부, missing section/failure handoff, report-only 실행의 policy hash 불변, JSON/Markdown 상태 일치, 다음-checklist parser.
- 격리/비용: 검증용 source report 경로와 production hash/loader 불변, non-market guard unknown의 경제성·실전 도달성 구분, source/policy/schema 변경 시 cache 무효화, pending outcome 재성숙, 자연 0건 fast path와 동일 raw 중복 decode 없음.
- 회귀 범위: 기존 `test_machine_entry_timing_tuning`의 producer·applied-policy 검증, `test_dynamic_micro_confirmation`, `test_machine_microstructure_attribution`, `test_machine_market_weakness_response`, `test_market_weakness_hysteresis_tuning`, `test_notify_panic_state_transition`, `test_market_weakness_entry_guard`, widget/episode 및 `test_samsung_morning_sor_reentry`, `test_machine_microstructure_policy_approval`, final-refresh wrapper/error detector/checklist builder. 새 evaluator unit test는 `src/tests`에 배치한다.

이번 계획 문서는 문서 리뷰·parser/diff 검사 대상이며 실제 evaluator 테스트 통과나 런타임 승인 근거가 아니다.

계획 리뷰 완료: actual-only cohort 혼합, 미평가 broker 검사에 의한 경제성 영구 차단, production source hash 훼손, 동일 유효 signal ID의 불필요한 제외, 미구현 상태/OPEN owner 혼선을 문서에서 보완했다. 문서/parser 관련 회귀 **47 PASS**, 실제 backlog parser와 `git diff --check` PASS다. 이번에는 코드·정책·봇·생산 보고서를 변경하지 않았고 새 evaluator의 실데이터 성능/수익 검증은 아직 수행하지 않았다.

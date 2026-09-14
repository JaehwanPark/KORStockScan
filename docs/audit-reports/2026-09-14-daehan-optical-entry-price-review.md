# 대한광통신 주문가 선정·재호가 검토

검토 기준: `2026-09-14 KST`

## 판정

대한광통신(`010170`) 주문번호 `0031943`의 미체결 취소는 `price_selection_too_passive_candidate`이면서 `entry_price_or_reprice_authority_mismatch`다. 최초 14,320원 주문이 안전 계약을 위반했다는 근거는 없지만, 당시 최우선 매수호가보다 3틱 낮아 참여 가능성이 낮았고, 시장이 위로 이동한 뒤 실행될 예정이던 재호가는 부모 AI PASS 점수 78을 전달받지 못해 `ai_score=0`으로 차단됐다.

이 단일 사례만으로 최우선 매도호가 추격, 방어폭 축소 또는 cancel wait 연장을 적용할 수는 없다. 같은 시점의 queue 우선순위와 공격적 매도 체결을 완전히 복원하지 못했으므로 14,350원 주문의 체결도 확정할 수 없다.

## 시간순 근거

| 시각 KST | 단계 | 확인 결과 |
| --- | --- | --- |
| 10:41:24.733 | 메인 진입 AI | 같은 promotion에서 `BUY`, score `78`, prompt `decision_quality_v2_15_2_balanced_bounded_recovery` |
| 10:42:05.207~10:42:05.361 | entry-price 및 제출 | Entry-price AI `USE_DEFENSIVE`, confidence `85`; 주문 3주를 14,320원에 제출. 최종 fresh BBO는 14,350/14,370원으로 주문가는 bid보다 30원, 3틱, 약 20.9bp 낮음 |
| 10:42:23.205 | post-submit reprice | fresh BBO 14,360/14,370원, quote age 0.9ms, buy pressure 95.56, trusted aggressor 10인데 `low_ai_score`로 차단. 이벤트에는 부모 `scout_ai_parent_score=78`과 reprice 입력 `ai_score=0`이 동시에 기록됨 |
| 10:43:44.168~10:43:44.799 | 취소 | 90초 wait 뒤 fill 0/3, 전량 미체결 상태로 취소 요청·확인. 제출부터 취소까지 기록된 현재가는 14,350~14,370원으로 14,320원에 접근하지 않음 |

원천은 [당일 pipeline events](../../data/pipeline_events/pipeline_events_2026-09-14.jsonl)의 promotion `SCANPROM-010170-1789350027339`, entry-price trace `entry_price:010170:1789350123078:d00561f9`, 주문 `0031943`, 취소 `0032187`이다.

## 최초 주문가 검토

Entry-price AI가 읽은 호가는 14,350/14,410원이었고 `fresh_consistent`, `entry_price_v1_contract_status=pass`였다. 최종 제출 직전 effective BBO는 14,350/14,370원으로 갱신됐지만 `normal_defensive_percent_bps`가 14,320원을 유지했고, 14,350원 reference target은 `not_better_than_defensive`로 배제됐다.

최종 submit context에는 buy pressure 95.560, trusted aggressor 10과 fresh micro reaction이 있었지만, entry-price 판단용 gap profile에는 positive signal 0, buy pressure false, trusted aggressor 0으로 기록됐다. 이후 bundle에는 ask sweep 87, bid replenishment 64, post-sweep hold 52가 계산됐으나 `computed_not_sent`였다. 따라서 방어가를 선택한 모델 판단 자체보다 **entry-price 결정 시점에 이용한 micro 입력과 최종 submit 시점의 관측 사이 단절**도 입력품질 후보로 남는다.

14,370원 ask를 즉시 지불했다면 최초 주문보다 50원, 약 34.9bp 비싸다. 고정 비교비용 23bp와 작은 순수익 목표를 고려하면 자동 ask crossing은 기대수익을 쉽게 훼손할 수 있다. 이 사례가 직접 지지하는 후보는 fresh best bid 또는 bounded reprice의 참여율 비교이며, 무조건 공격적 주문은 아니다.

## 확인된 구현 결함

[sniper_state_handlers.py](../../src/engine/sniper_state_handlers.py)는 broker 제출 후 pending order에 `ai_score=latency_signal_score`를 저장한다. 대한광통신에서는 이 값이 0이었다. [entry_reprice_after_submit.py](../../src/engine/scalping/entry_reprice_after_submit.py)는 이 `order.ai_score`가 score floor보다 낮으면 `low_ai_score`로 종결한다. 같은 pending order에 보존된 부모 AI attribution의 `scout_ai_parent_score=78`은 재호가 판정에 사용되지 않는다.

재호가는 이미 승인된 BUY attempt의 미체결 주문을 다루므로 score owner와 lineage를 명시적으로 고정해야 한다. 후속 수리는 부모 AI trace의 검증된 score/action을 pending order의 canonical reprice provenance로 전달하거나, 현행 기계+AI 계약에서 재호가가 사용해야 할 별도 score를 정의해야 한다. missing score를 0으로 보간해 경제적 veto로 사용하는 현재 동작은 허용하지 않는 편이 맞다.

### 현 배포의 초기 가격 보완축도 이 주문을 구제하지 못함

현재 PID에는 `KORSTOCKSCAN_INTRADAY_ENTRY_PRICE_DISCOVERY_ENABLED=true`가 로드돼 있고, 최초 방어가가 과도하게 낮을 때 best bid 근처로 올리는 `defensive_missed_upside_v1` 및 `reference_target_cap_missed_upside_v1`도 배포 코드에 존재한다. 그러나 이 주문에서는 다음 순서로 둘 다 적용되지 않았다.

- reference target 14,350원은 best bid 14,350원보다 낮지 않다는 이유로 `reference_target_not_below_bid`가 됐다.
- 일반 profile의 방어폭은 25bp였는데 `defensive_missed_upside_v1`의 기본 진입 조건은 원래 방어폭 35bp 이상이다. 따라서 동일 주문을 best bid 근처로 보정하지 못한다.
- fallback 진단은 두 번째 후보의 `original_bps_below_min`보다 첫 후보의 `reference_target_not_below_bid`만 최종 skip reason으로 남겨, 실제로 25bp normal profile이 보완 대상 밖이었다는 사실을 숨긴다.

즉 과도한 수동성 완화 코드가 존재하고 활성화돼 있다는 사실만으로 이 결함이 닫히지 않는다. 대한광통신과 같은 `normal:25bp + reference=best_bid` 조합은 현재도 보완축의 사각지대다.

### 장후 자동 튜닝의 목적함수·표본 결함

`dynamic_entry_price_resolver`는 현재 `normal 25bp`, `strong 10bp`, `favorable 15bp`, `weak 40bp`와 max-below-bid 80bp를 profile별로 비교해 다음 PREOPEN 후보를 만드는 기계식 튜닝축이다. 9/14 apply plan은 `hold_sample`이고 새 선택값은 없다.

이 자동화에는 수익극대화 판정을 막는 두 결함이 있다.

1. 실거래 profile grid의 `missed_upside`는 실제 미체결 후행 BBO/outcome으로 계산되지 않는다. exact completed 손익이 하나라도 join되면 코드가 `0.0`을 기록한다. 따라서 미체결·취소로 놓친 상승을 0으로 정상화할 수 있다.
2. counterfactual join은 eligible event 25,218건 중 29건, 0.1%만 연결됐다. 실패는 attempt key 결손 8,152건, candidate ID 불일치 17,063건이 주원인이다. 실제 profile 손익도 체결 후 완료된 거래에 치우쳐 미체결의 기회비용을 반영하지 못한다.

실거래 전체 join은 914개 관측 중 483개이고 비용 차감 EV는 -0.1207%다. `strong_1tick_pressure:10`만 52개 exact outcome에서 +0.5094%로 조건을 통과했지만 현재값 자체가 10bp라 새 변경 후보가 아니다. 이 값은 incumbent strong profile의 제한된 체결표본 지지일 뿐, normal 25bp를 유지하거나 미체결 기회비용이 없다는 근거가 아니다.

현재 20건 floor 자체는 과도하지 않다. 같은 attempt의 후보별 체결·미체결·취소·후행 executable outcome이 거의 연결되지 않는 것이 먼저 고칠 문제다.

## 현행 entry-price 축

| 축 | 현재 역할 | 한계 |
| --- | --- | --- |
| 기계식 최초 가격 resolver | fresh BBO와 normal/strong/favorable/weak profile의 bp 방어폭으로 기준 가격을 생성하고 reference target과 비교 | 대한광통신처럼 normal 25bp가 참여율 보완 조건 밖일 수 있음 |
| Entry-price AI | `USE_DEFENSIVE|USE_REFERENCE|IMPROVE_LIMIT|SKIP`을 반환하는 가격 advisor. 최종 가격·stale·broker guard는 코드가 다시 제한 | 호출 중 시장이 움직이며 이 건의 가격 context는 제출 시점에 약 4.2초 오래됨. 당시 prompt는 `entry_price_v1` |
| V2.5 prompt selector | KRX regular의 검증된 evidence/date/hash가 모두 맞을 때만 V2.5 prompt 선택 | 현재 PID에는 V2.5 enable/date/evidence env가 없어 미적용. deterministic tuning ON과 prompt V2.5 적용은 다른 상태 |
| post-submit reprice | 15초 뒤 fresh BBO·spread·tape·score로 bounded 취소/재주문 판단 | 이 주문은 부모 score 78 대신 `latency_signal_score=0`을 받아 잘못 차단됨 |
| 장후 profile calibration | profile별 exact 완료 손익으로 다음 PREOPEN bp 후보를 선택 | 미체결 opportunity denominator와 counterfactual join이 불완전해 참여율 최적화에 부적합 |

## 기계판정기 도입 적정성

Entry price의 최종 결정은 기계판정기가 소유하는 편이 수익극대화 목적에 맞다. 가격은 후보가 유한하고 최신 BBO·tick·queue·비용에 즉시 재계산해야 하므로, 수 초 걸릴 수 있는 AI가 exact 주문가를 직접 고르는 구조보다 결정론적 비교가 재현성과 참여율 관리에 유리하다. 다만 기계판정기는 진입 BUY 결정을 다시 승격하는 새 owner가 아니라, 이미 승인된 entry attempt의 가격 후보만 비교해야 한다.

권장 구조는 다음과 같다.

1. 최신 same-route BBO에서 `현 방어가`, `best bid-1tick`, `best bid`, 필요할 때만 `bounded ask` 후보를 생성한다.
2. 같은 attempt에서 `체결확률 × 체결 후 비용차감 EV - 미체결 기회비용 - adverse/tail - 자본점유`를 후보별로 비교한다.
3. AI는 regime·setup·semantic risk와 후보 mode에 대한 보조 의견만 제공한다. 실제 제출 직전 기계판정기가 새 BBO로 가격을 재계산하고 stale·spread·broker/order guard를 다시 적용한다.
4. ask crossing은 추가 체결확률의 기대이득이 가격상승 비용과 tail을 보수적으로 초과할 때만 허용한다. 대한광통신에서 ask 14,370원은 14,320원보다 약 34.9bp 비싸 고정 비교비용 23bp를 합치면 작은 순수익을 쉽게 없앨 수 있으므로 이 사례만으로 허용할 수 없다.
5. 15초 reprice도 동일 parent attempt와 동일 utility 계약을 사용한다. canonical parent action/score가 없으면 0점 경제적 veto가 아니라 `source_quality_blocked`로 남긴다.

초기 적용은 source-only paired 평가가 적정하다. 후보별 동일 attempt 분모에서 fill participation, 취소·late fill, 비용 차감 순이익/eligible signal, target/adverse first-hit, tail과 자본점유를 비교한 뒤 bounded live mode로 넘긴다. 이 설계에서는 AI prompt Provider replay floor를 기계 가격 선택의 필수 gate로 복사하지 않는다. 반대로 실제 주문가 변경에는 실거래 exact outcome과 rollback이 계속 필요하다.

## 다음 수용조건

- 같은 submit attempt의 machine action, AI PASS trace/score, entry-price trace와 pending order/reprice event가 하나의 lineage로 연결된다.
- 재호가 입력 score가 결손이면 `source_quality_blocked`로 직접 기록하며 `low_ai_score`로 오분류하지 않는다.
- 부모 score 78과 fresh quote/micro가 주어진 회귀 테스트에서 reprice가 score 결손 때문에 차단되지 않는다. 기존 spread, stale, broker/order, partial fill, cap과 hard-safety guard는 유지한다.
- 최초 방어가, best-bid 후보와 bounded reprice를 동일 시점 executable source로 누적 비교해 fill participation, 비용 차감 target/adverse first-hit와 tail을 함께 산출한다.
- profile ledger가 `submitted = full fill + partial fill + confirmed unfilled/cancel + pending/right-censored`를 보존하고, 미체결 후행 기회비용을 0으로 보간하지 않는다.
- counterfactual attempt/candidate join 결손을 수리하고 동일 eligible attempt의 후보별 비교 coverage를 직접 보고한다.
- 최초 가격 기계판정기는 이미 승인된 entry attempt의 가격만 선택하며 BUY 승격, 수량·cap·provider 또는 hard-safety 변경 권한을 갖지 않는다.
- 코드 수리, 선택 release 배포, 현재 PID 소비와 자연 미체결 개선은 각각 별도로 확인한다.

후속 구현·장후 handoff owner는 당일 체크리스트의 기존 `CodeImprovementWorkorderReview0914`를 사용한다. 이 리뷰만으로 닫힌 `RuntimeEnvIntradayObserve0914`의 과거 수용 범위를 다시 OPEN하거나 새 실주문 권한을 만들지 않는다.

이번 검토는 읽기 전용 주문 분석과 장중 지시문 보완이다. 주문가·threshold·provider·bot/env를 변경하거나 재기동하지 않았다.

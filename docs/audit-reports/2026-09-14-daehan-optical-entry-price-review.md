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

## 다음 액션 최소 구현계획

### 구현 결정과 범위 상한

새 가격 엔진·새 AI prompt·새 정기 producer를 만들지 않는다. 기존 `dynamic_entry_price_resolver`, post-submit reprice와 PREOPEN apply consumer를 그대로 사용하고, 이 경로가 정확한 부모 판정과 미체결 기회비용을 읽도록 수리한다. 구현은 아래 기존 파일을 우선 대상으로 하며, exact key를 기존 producer에서 발행할 수 없는 것이 코드로 입증될 때만 같은 owner 파일을 추가 검토한다.

| 작업 묶음 | 우선 수정 owner | 수정 상한 |
| --- | --- | --- |
| 재호가 부모 판정 lineage | `src/engine/sniper_state_handlers.py`, `src/engine/scalping/entry_reprice_after_submit.py` | 새 AI 호출·새 주문 owner 없이 기존 pending-order schema와 판정만 보완 |
| 실거래·미체결 경제성 분모 | `src/engine/daily_threshold_cycle_report.py` | 기존 profile grid·counterfactual join·보존식 수리 |
| exact counterfactual key | `src/engine/sniper_missed_entry_counterfactual.py` | 기존 산출물에 canonical key가 실제로 없을 때만 수정 |
| 다음 PREOPEN 소비 | `src/engine/threshold_cycle_preopen_apply.py` | 기존 selected/carry 계약 검증이 먼저이며, 명시적 carry receipt가 빠질 때만 최소 보완 |
| 자동화 계약 | `docs/report-based-automation-traceability.md`, 당일 checklist의 기존 `CodeImprovementWorkorderReview0914` 근거 | 새 stable ID·새 cron·새 family 생성 금지 |

테스트도 기존 `test_entry_reprice_after_submit.py`, `test_sniper_entry_latency.py`, `test_daily_threshold_cycle_report.py`, `test_threshold_cycle_preopen_apply.py`에만 추가한다. 새 모듈이나 중복 test file을 만들지 않는다.

### WP1 — 재호가의 canonical 부모 판정 복구

pending order에 최초 승인 attempt의 다음 정보를 immutable provenance로 보존한다.

- machine adjudicator의 최종 `PASS`와 정책/trace hash
- auxiliary AI의 action·contract·trace와 존재하는 경우 score
- entry-price trace, submit attempt ID, promotion ID와 broker 원주문번호
- 이 값을 생성한 stage와 source-quality 상태

현행 기계 주판정·AI 보조 계약의 재호가는 숫자형 `latency_signal_score`를 단독 권한으로 사용하지 않는다. 최초 attempt가 기계 `PASS`로 제출됐고 명시적 AI veto가 없으면 그 승인 상태를 재사용하며, score는 진단 provenance로만 남긴다. canonical 부모 판정이 없거나 서로 충돌하면 0점으로 보간하지 않고 `source_quality_blocked`로 종결한다. 과거 AI-score 주판정 계약을 아직 소비하는 legacy 경로가 있으면 계약을 명시적으로 분기해 기존 안전 동작을 보존한다.

직접 회귀 수용조건은 다음과 같다.

1. 대한광통신 형태의 `machine PASS + auxiliary AI BUY/78 + latency score 0` 입력이 `low_ai_score`로 차단되지 않는다.
2. 부모 action/hash 결손 또는 불일치는 `source_quality_blocked`가 된다.
3. 명시적 veto, stale BBO, 과도한 spread, partial fill, cancel/replace 중복, broker·수량·cap·hard-safety 차단은 그대로 유지된다.
4. reprice event가 실제로 사용한 부모 field와 원 trace ID를 기록해 이후 report가 추정 join을 하지 않는다.

### WP2 — 미체결 기회비용과 exact join 복구

`dynamic_entry_price_resolver`의 profile ledger를 `submit attempt × 가격후보 × venue/session`으로 고정한다. broker 응답 순서가 바뀌어도 submit attempt ID, 원주문번호, 정정·취소의 `ori_ord`, entry-price candidate ID와 promotion ID로 연결한다. symbol·근접시각만으로 연결하는 fuzzy join은 허용하지 않는다.

각 submitted attempt는 다음 배타적 상태 중 하나만 가진다.

`full_fill | partial_fill | confirmed_unfilled_cancel | pending | right_censored | source_quality_excluded`

그리고 다음 보존식을 report named field와 테스트로 닫는다.

`submitted = full_fill + partial_fill + confirmed_unfilled_cancel + pending + right_censored + source_quality_excluded`

현재 상수 `0.0`인 `missed_upside`는 제거한다. 미체결·취소 뒤 fresh executable BBO가 있고 exact horizon이 성숙한 행만 target/adverse first-hit, 예상 fill, 비용 차감 opportunity loss를 계산한다. BBO·master·비용·terminal이 없으면 `null`과 직접 gap reason을 남긴다. 실제 체결 손익과 source-only counterfactual은 별도 denominator와 field로 유지하고 합산하지 않는다.

counterfactual join은 기존 candidate/attempt ID namespace를 하나의 canonical field로 정규화한다. 기존 producer가 이 key를 이미 기록하면 report parser만 고치고, 원천에 key가 없을 때만 `sniper_missed_entry_counterfactual.py`를 수정한다. 전체 25,218행을 억지로 연결하는 것이 목표가 아니라, 연결 가능한 exact-key 행과 구조적으로 연결 불가능한 행을 전수 보존하는 것이 목표다.

### WP3 — 기존 기계 가격 resolver의 목적함수 보완

가격 후보와 bounds는 현행 `normal/strong/favorable/weak`, best-bid 계열, reference, timeout 후보를 재사용한다. 첫 구현에서 learned utility model, 새 threshold family 또는 ask-cross 확대를 추가하지 않는다.

후보 선정 우선순위는 다음과 같이 고정한다.

1. exact real attempt의 비용 차감 순이익과 fill/terminal 결과
2. 같은 attempt·같은 horizon의 미체결 opportunity loss와 참여율
3. adverse-first·tail, late fill, 취소/재호가 비용과 자본점유
4. source-only counterfactual은 방향과 기회비용 진단에만 사용하고 단독 live 승인에는 사용하지 않음

현재 20건 real sample floor, profile bounds와 일일 최대 step은 유지한다. floor를 낮추거나 sim/CF로 채우지 않는다. 대한광통신 한 건만으로 normal 25bp를 축소하거나 ask를 추격하지 않는다. 기존 aggressive-override 진단은 `reference_target_not_below_bid`와 `original_bps_below_min`을 함께 남겨 어느 조건이 실제 후보를 제외했는지 보이게 한다.

장후 candidate의 결과는 두 가지 중 하나여야 한다.

- `selected_change`: exact real/paired 경제성과 기존 bounds·max-step·source-quality gate를 모두 통과한 challenger의 env 값을 발행한다.
- `verified_carry`: 통과한 challenger가 없으면 현재 검증 정책 값을 그대로 발행하고, 미변경 사유·source hash·남은 blocker를 기록한다.

두 이름은 구현계획의 판정 라벨이며 새 runtime family나 필수 새 schema가 아니다. `selected_change`는 기존 candidate의 `runtime_apply_eligible_now=true`와 PREOPEN `policy_refreshed|newly_enabled`, `verified_carry`는 기존 carry receipt와 `carried_forward_unchanged`에 대응시킨다.

`verified_carry`도 다음 장전용 정책 산출물이다. 다만 경제적 개선을 입증한 변경으로 표시하지 않는다. source/hash/기존 정책 값을 결속하지 못해 단순 `hold_sample`만 남는 경우는 정책 생성 성공이 아니라 handoff 결함으로 처리한다.

### WP4 — 장후 단회 재생성과 다음 장전 자동 적용

구현·리뷰가 닫힌 검토 commit을 immutable release로 만든 뒤, 20:10 장후 chain 시작 전 안전한 공백에 선택 release를 교체한다. 실행 중인 장후 wrapper나 다른 consumer가 있으면 세대를 중간 교체하지 않는다. 정상 예약 전에 배포가 끝나면 설치된 장후 wrapper를 한 번만 실행되게 두며 수동 중복 실행하지 않는다.

장후 source date `2026-09-14`의 필수 산출물은 다음과 같다.

1. `data/report/threshold_cycle_2026-09-14.json`
2. `data/report/threshold_cycle_calibration/threshold_cycle_calibration_2026-09-14_postclose.json`
3. `data/report/threshold_cycle_ai_review/threshold_cycle_ai_review_2026-09-14_postclose.json`
4. 같은 generation을 읽은 verifier·controller·finalization terminal receipt

이 generation의 `dynamic_entry_price_resolver`에는 exact real/missed-opportunity denominator, join coverage, source-quality exclusion, 현재값, 추천값, `selected_change|verified_carry`에 대응하는 decision 근거가 있어야 한다. AI review는 기존 예약 계약만 수행하며 이 수리를 이유로 별도 Provider replay나 prompt 생성을 추가하지 않는다.

다음 거래일은 달력 owner로 계산한다. 다음 PREOPEN의 기존 apply consumer가 위 장후 generation을 읽어 다음 파일을 생성·검증해야 한다.

1. `data/threshold_cycle/apply_plans/threshold_apply_NEXT_TRADING_DATE.json`
2. `data/threshold_cycle/runtime_env/threshold_runtime_env_NEXT_TRADING_DATE.env`
3. 같은 날짜 runtime env JSON과 verify artifact

apply plan에서 `dynamic_entry_price_resolver` decision, source path/SHA256, `selection_change_class`, env overrides와 rollback을 확인한다. `selected_change`이면 변경값을, `verified_carry`이면 이전 검증값과 `carried_forward_unchanged`를 정확히 포함해야 한다. 다음 main PID가 이 env/hash를 읽은 receipt가 생겨야 배포·적용을 완료로 판정한다. 자연 submit/fill과 비용 차감 EV 개선은 그 다음 별도 acceptance다.

예약 chain이 이미 구 release로 시작했다면 해당 run을 중단하거나 산출물을 섞지 않는다. 구 run이 terminal인 뒤 검토 release로 최초 영향 producer와 필수 downstream만 한 번 재생성하고, 선택 release commit과 output generation을 함께 기록한다. 봇이 살아 있는 동안 stop 부작용이 있는 전체 postclose wrapper를 임의 재실행하지 않는다.

### 구현·리뷰·실행 순서

1. 현 원천과 대한광통신 exact IDs/hash를 회귀 fixture로 고정한다.
2. WP1을 구현하고 재호가 safety 회귀를 통과시킨다.
3. WP2를 구현해 보존식과 null/gap reason, actual/CF 분리를 검증한다.
4. WP3의 기존 candidate 선정과 명시적 carry 소비를 검증하고, 실제 누락이 있을 때만 PREOPEN consumer를 수정한다.
5. affected producer/consumer와 authority leak을 self-review하고 finding을 수정한 뒤 같은 범위를 재리뷰한다.
6. 관련 pytest·compile·`git diff --check`와 문서 print-only parser를 통과한다.
7. 검토 commit/release를 고정하고 안전한 시점에 배포한다.
8. 9/14 장후 producer를 한 generation만 생성하고 verifier→controller→finalization까지 확인한다.
9. 다음 PREOPEN apply plan/runtime env/verify와 새 PID 소비를 확인한다.

targeted validation은 다음 범위로 제한한다.

```bash
PYTHONPATH=. .venv/bin/pytest -q \
  src/tests/test_entry_reprice_after_submit.py \
  src/tests/test_sniper_entry_latency.py \
  src/tests/test_daily_threshold_cycle_report.py \
  src/tests/test_threshold_cycle_preopen_apply.py
PYTHONPATH=. .venv/bin/python -m compileall -q \
  src/engine/sniper_state_handlers.py \
  src/engine/sniper_entry_latency.py \
  src/engine/scalping/entry_reprice_after_submit.py \
  src/engine/daily_threshold_cycle_report.py \
  src/engine/threshold_cycle_preopen_apply.py
git diff --check
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500
```

Provider 호출, 광범위 trading suite, 같은 날짜의 반복 full postclose와 새 연구 grid는 이 변경의 기본 검증에 포함하지 않는다.

### 중단·재작업 방지 조건

- 구현 중 새 파일이 필요해 보이면 먼저 기존 producer가 같은 field를 발행할 수 없는지 입증한다. 입증되지 않으면 기존 파일을 보완한다.
- review 재반복은 failing test, 새 P0~P2 finding 또는 실제 producer/consumer contract 불일치가 있을 때만 한다. BUY가 나오지 않았다는 이유만으로 코드를 반복 변경하지 않는다.
- 장후 재생성은 검토 release가 실제 선택됐고 동일 target-date worker·lock이 없을 때 한 번 수행한다. 정상 generation을 더 큰 표본으로 만들 목적으로 반복하지 않는다.
- `selected_change`가 없더라도 exact `verified_carry`가 다음 PREOPEN까지 전달되면 자동화는 정상이다. 반대로 정책 파일을 만들기 위해 경제성 gate를 낮추거나 candidate를 합성하지 않는다.
- 이번 구현은 가격과 재호가의 기존 owner만 수리한다. BUY 진입 threshold, 수량, 제출 한도, cancel wait, provider/model, broker·hard safety는 변경하지 않는다.

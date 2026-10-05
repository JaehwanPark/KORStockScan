# 비삼성 고정 pullback 후보 구현계획 — 2026-10-05

## 1. 목적과 단계

[연구 종결 기준 §16](main-machine-auxiliary-samsung-scope-reorganization-plan-2026-10-03.md)의 F3 산출물이다. F1의 고정 비교에서 개선이 확인되면 아래 후보의 공용 기계 판정 구현을 권고한다. 비교·민감도·권고 상태의 계산 근거는 `tmp/non-samsung-final-policy-decision-20261005/{comparisons,candidate-recommendation,report}.json`에 보관한다. 본 계획 작성은 운영 구현·정책 등록·배포 완료를 뜻하지 않는다.

현재 소유자는 [10/5 체크리스트](../checklists/2026-10-05-stage2-todo-checklist.md)의 `NonSamsungFinalPolicyDecision1005`다. 이번 실행은 기존 자료 연구·계획 확정까지다. 아래 운영 코드 변경은 후속 구현 범위이며 이 문서만으로 실행하지 않는다.

## 2. 구현할 규칙을 고정

- ID: `pullback_p60_v0`, 교체형 `replace`, 대상 `stock_code != 005930`의 `KRX|KRX_REGULAR`.
- 부모: 연구 시점 `d94fecaf16ac7fa038ee3dafb6f8d6eea7110e49aa5a5f0326fed56f859d713a`. 실제 연결할 부모가 다르면 같은 대상·입력으로 행동 차이를 먼저 대사하며 현재 부모를 이 과거 hash로 덮어쓰지 않는다.
- 수치 조건: `60 <= buy_pressure_10t <= 100`, `net_aggressive_delta_10t > 0`, `curr_vs_micro_vwap_bp <= 0`, `tick_aggressor_trusted_count >= 10`.
- 필수 품질: `tick_aggressor_pressure_usable is True`, `micro_vwap_available is True`, `tick_context_stale is False`, `quote_stale is False`. 누락·비수치·비유한 값은 조건 불충족이다. 당시 cutoff·exact item/venue/session·원 capture hash를 사용한다.
- 판정 의미는 기존 [연구 평가 함수](../../src/engine/scalping/entry_pullback_buy_flow_research.py)의 행동과 같아야 한다. 기존 `BLOCK`은 유지한다. 대상 내 기존 `ENTER_NOW`도 조건/guard 미충족이면 `RECHECK`가 될 수 있으며 성공 보존을 강제하지 않는다.
- 기존 `RECHECK`에서 해소 가능한 것은 `CONFIRMATION_MISSING + RECHECKABLE` 중 `trigger_confirmation_missing`, `volume_confirmation_missing`, `micro_continuation_unconfirmed`, `no_supported_setup`뿐이다. 원 위험 fact는 보존하고 별도 상쇄 근거를 남긴다. 다른 미해소 위험·invalidation·source·liquidity·micro recipe·situation veto가 남으면 승격하지 않는다.
- 대상 밖은 기존 정책을 상속한다. 삼성·NXT·다른 세션의 정책을 이 성과로 변경하지 않는다. 기계 `ENTER_NOW` 이후 보조 AI·제출·주문·계좌·수량·보유 guard는 기존 소비 경로를 유지한다.

## 3. 수정할 생산자·소비자와 수용 조건

| 경로 | 계획된 변경 | 완료 검증 |
| --- | --- | --- |
| `src/engine/scalping/entry_strategy_policy.py` | 수치 profile에 종목 가격 등을 대용 키로 넣지 않고 exact symbol 제외·scope·recipe·parent/hash·버전을 검증하는 명시적 계약을 추가한다. 기존 schema의 허용 필드/REGISTRY를 우회하지 않는다. | 미등록 recipe, 잘못된 scope/parent, 무효 field를 거절. 기존 정책 직렬화·행동 회귀 유지. |
| `src/engine/scalping/entry_setup_evidence.py` | 위 recipe의 순수 기계 판정을 공용 평가 경로로 편입한다. 연구 함수의 위험 ledger·상쇄 범위·사후 situation veto와 일치시킨다. 연구 전용 모듈을 live에서 직접 import하지 않는다. | 고정 원 capture의 기존 행동과 후보 행동을 대사. 부모 BLOCK 유지·각 hard guard·범위 밖 상속·조건 경계·결손·미래 입력 검증. |
| `src/engine/scalping_feature_packet.py`, `src/engine/scalping/entry_machine_observation.py`, `src/engine/ai_engine_openai.py` | 기존 feature 생산 및 `_final_entry_machine_inputs` cutoff/원천을 소비한다. 정책 hash·원 capture hash·rule match·guard 결과를 판정 receipt에 결속한다. 부분 feature와 다른 시점 snapshot을 혼합하지 않는다. | 기존 필드로 판정 가능한지 확인. capture와 실제 공용 evaluator가 같은 입력에서 같은 행동을 내는지 대사. API/WS 프로토콜 변경은 현재 계획에 없다. |
| `src/engine/scalping/ai_action_outcome_calibration.py`, `src/engine/scalping/entry_observation_recipe_policy.py` | 이미 있는 명시적 격리 관측 경로와 공용 evaluator가 같은 후보를 평가하도록 연결한다. probe 관측과 native 실행 원천의 분모를 별도 schema/receipt로 보존한다. | 후보1개·고정 날짜/표현식, 군집 동일 가중 raw/지원조정 승률, 성공100%/80% veto 없음, 결손/미도달 분리. probe를 가짜 promotion으로 바꾸지 않음. |
| `src/engine/scalping/mechanistic_entry_runtime_policy.py` | 현재 연구 schema를 곧바로 `publish`/`activate_strategy_report`에 넘기지 않는다. 승인된 machine component로 변환하는 검증 계약과 dated activation/parent CAS/loader/hash/rollback을 설계·구현한다. | 유효일·부모·source/kernel/hash 불일치 거절, 기존 삼성/보조/청산 component 보존, 실제 consumer의 대상별 정책 선택 검증. 연구 권고만으로 live flag가 켜지지 않음. |
| `src/tests` | 공용 판정·생성기·loader 및 범위/원천/권한 경계에 대한 표적 회귀를 추가한다. | 기존 연구 evaluator와 공용 판정의 차이0, guard 우회0, 잘못된 정책의 publish/activation 거절, 되돌림 검증. |

새 순수 helper가 필요하면 역할에 맞는 `src/engine/scalping`에 둔다. `src/engine` root에 새 모듈이나 영구 중복 wrapper를 만들지 않는다. 공용화 이후 연구 helper는 같은 순수 판정을 검증하는 adapter로 줄이고 중복 구현을 유지하지 않는다.

## 4. 관측 최초 신호와 실제 주문 상태의 차이

연구의 사건은 부모 또는 후보 ENTER가 관측되는 연속 구간에서 각 정책의 첫 신호를 남기는 방식이다. 관측 사이의 실제 연속성을 보장하지 않는다. 미래 승패로 사건을 선택하지 않지만, 원 목표/손절에 따른 가상 점유는 실제 주문·보유 점유와 다르다.

따라서 연구의60분 점유나 가상 종료를 live 재진입 제한으로 복사하지 않는다. 실제 pending order·holding·cooldown은 기존 owner가 결정한다. 후속 구현 검증에는 다음을 명시한다.

1. 공용 evaluator는 단일 capture에서 기존 연구 행동을 재현한다. 이것으로 주문 수·최초 신호 효과의 동일성까지 입증하지 않는다.
2. runtime의 실제 평가 cadence와 admission/custody 이벤트에서 판정 receipt를 연결한다. 이전600초 축소에서9/29 우열이 뒤집힌 민감도를 공개하고, 빈도와 무관한 우월성으로 주장하지 않는다.
3. 관측 사건 latch가 필요하다면 별도의 상태 계약·generation reset·source gap 처리와 영향 비교를 먼저 제시한다. 이번 후보에 임의의600초 쿨다운이나 미래 손절/목표 기반 latch를 추가하지 않는다.

## 5. 선정·권고·운영 검증의 구분

- 연구 권고: §16의 기존 비용 결합 목표-first 승률 개선과 구현 가능한 규칙을 근거로 판단한다. 기존 성공 보존·청산CF 양수·미확정 전량 해소는 추가 탈락 조건이 아니다.
- 불확실성: F1의 공통 trace를 결속한 가상 승패 배정, 결손 원인별 수, F2의 조건부 청산을 함께 공개한다. 개선된 관측 부분집합의 승률을 전체 미확정 결과까지 확정한 값으로 쓰지 않는다.
- 운영 준비: 공용 판정 일치와 정책 schema/loader/guard/rollback 검증을 별도로 닫는다.9/29·9/30·10/2는 재사용한 탐색 자료이므로 새 독립 검증 완료라고 표시하지 않는다. 기존 family의 운영 검증 요건은 코드 편입 전에 실제 현재 계약으로 대사하되, 폐기된 성공 보존 조건을 되살리지 않는다.
- 자연 적용·성과: 이후 적용 지시가 있을 때 정책 발행/정확한 유효일/PREOPEN/PID 소비를 구분하고, 주문·체결·완료·전비용 수익은 해당 실제 원천으로 검증한다. 이를 기다리며 현재 기존 자료 연구를 OPEN으로 연장하지 않는다.

## 6. 되돌림과 후속 구현 종료 조건

되돌림은 candidate machine component를 직전 유효 parent로 복귀시키며 삼성·보조·청산·주문 owner를 변경하지 않는다. 잘못된 scope 선택, source/hash 결속 손상, 연구/공용 판정 불일치, hard guard 우회가 발견되면 적용 준비를 중단하고 해당 결함을 수정한다. 독립 검증 부족과 당일 표본 부족을 구현 버그나 이미 발생한 주문 실패로 표시하지 않는다.

후속 구현의 종료는 공용 평가 일치→schema/loader/범위 회귀→리뷰/수정/재리뷰→표적 검증→구체적인 배포 검토 산출물이다. 현재 연구의 종료는 [§16](main-machine-auxiliary-samsung-scope-reorganization-plan-2026-10-03.md)의 최종 결론이며 이 후속 운영 작업을 이미 완료했다고 주장하지 않는다.

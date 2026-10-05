# 삼성전자 보합 매수 수급 원천·기계 evaluator 구현계획

작성: 2026-10-04 KST. 사용자 `다음액션 실행`의 범위는 [선행 리뷰 §7](../audits/samsung-machine-horizon-pattern-research-review-2026-10-04.md)의 보관 원천 대조·기계 경로 재생·후속 구현계획이다. 이번 실행 결과는 [대사 리뷰](../audits/samsung-flat-buy-flow-source-and-evaluator-review-2026-10-04.md)에 둔다.

## 1. 고정할 연구 대상

- `absorption_p60_v10`: 신뢰 가능한 최근10체결 매수 비중≥60%, 순공격 매수 수량>0, 첫·끝 체결 가격 변화=0, 현재가와 micro VWAP 차이≤10bp. VWAP 하한을 새로 넣지 않는다.
- 이름의 absorption은 가설이다. 첫·끝 가격 보합만으로 매도 물량 흡수·호가 재보충·전 체결 동일 가격을 입증하지 않는다. 구현용 관측 fact는 `flat_price_buy_flow`로 명확히 표현한다.
- 삼성전자 `005930`, 기존 KRX 정규장 판정 scope를 유지한다. 실제 원천 `005930_AL/krx_nxt_integrated`의 통합 관측 성격을 보존한다. 통합 원천을 KRX 단독 체결·실행 가능성으로 바꾸지 않는다.
- 기존 전략 raw/parent/hash·native·가격·비용·원 invalidation을 보존한다. 보조 AI 입력·판정·provider/주문 실패를 이 연구에 사용하지 않는다.
- 이번 단계는 격리 재생과 계획 작성이다. 운영 코드·정책·배포·기동·10/6 준비 계약 변경은 포함하지 않는다.

## 2. 이미 완료한 원천 및 evaluator 검증

- 삼성전자 정규장519관측의 원 행동과 현 parent 재생이 일치한다. 고정 조건73관측과 비중복24선택을 보존한다.
- 10/2 원8관측은 모두 RECHECK다. 원 체결 수치는 해당 관측이 소비한 시점의 보관 체결과8/8 일치한다. 최신 판정시각 체결과는4/8 일치한다.
- 차이4건은 locked BBO(`bid==ask`)에 대한 최신 스냅샷 갱신 보류와 연결된다. 기존3초 이내 receipt를 소비했으므로 원 값을 허위·무효로 바꾸지 않는다. 후보가 `최신 수급`과 `허용 유효기간 안의 보관 수급` 중 무엇을 뜻하는지 분리해야 한다.
- 기존 규칙은 `micro_positive_price_response`가 있어야 ADVERSE_TAPE를 상쇄한다. 보합을 상승으로 위조하거나 임계값0만 낮춰서는 원하는 전략을 표현하지 못한다. 현재 supported family 여부, local breakout, liquidity fact도 별도 남는다.

## 3. P0 — 원천 관측과 제출 검증의 갱신 계약 분리

### 소유 코드

- 준비 입력: `src/engine/sniper_state_handlers.py::_refresh_prepared_entry_inputs`.
- 기계 입력 동결: `src/engine/ai_engine_openai.py::_final_entry_machine_inputs`.
- feature 생성: `src/engine/scalping_feature_packet.py::build_scalping_feature_packet`, `src/engine/scalping/microstructure_reaction_context.py::precompute_microstructure_reaction_inputs`.
- 기존 `_pre_submit_refresh_real_ws_snapshot`는 주문 직전에서도 쓰인다. 이 공유 함수의 `ask>bid` 검사를 일괄 완화하지 않는다.

### 구현 내용

1. 기계 **관측용** 최신 route snapshot을 선택하는 계약을 별도로 둔다. 동일 item/route/transport epoch, 정상 가격, non-crossed BBO, 각 source의 원래 freshness와 timestamp를 검증한다. locked BBO는 관측 상태로 명시하고 주문 가능 상태와 분리한다.
2. 최신 체결·BBO·depth의 cutoff를 동결한 뒤 한 번의 feature 계산에 사용한다. 과거 timestamp를 현재 시각으로 덮어쓰지 않는다. 최근10개를 고를 때 미래 체결, 다른 epoch/route, 끊긴 sequence, 명시적 비신뢰 수량을 건너뛰어 좋은10개로 채우지 않는다.
3. 최신 관측 채택 실패 시 기존 source fail-closed/유효기간 계약을 유지한다. 과거 snapshot 소비가 허용되는 경우도 `retained_snapshot`과 실제 age를 출력해 `latest_snapshot`과 구분한다. `0 spread`를 결손0이나 실행 비용0으로 해석하지 않는다.
4. 기존 자료로 두 계약을 완전 feature 단위로 재생한다. 이번의 체결3필드 치환은 시점 차이 확인용이다. 새 VWAP/BBO/current price/비용을 동반하는 재계산은 별도 결과로 기록하고 기존8진입 고정 비교와 전체 점유 재생을 함께 낸다.

### 원천 receipt 제안

`samsung_flat_buy_flow_observation_v1`:

- `observation_hash`, 원 `decision_trace_id`, 원 native/watch ID 또는 명시적 null, parent/strategy raw hash.
- `decision_scope`, `source_item`, `market_route`, source 소유자, transport epoch; 외부 collector epoch를 Main epoch와 동일시하지 않는다.
- `feature_cutoff`, `snapshot_selection`, receipt/source별 observed time과 age, tick sequence 범위·개수·window hash·usable 판정 및 사유.
- 원 buy/sell 수량, buy pressure, 첫·끝·최소·최대 가격, `endpoints_flat`, `all_prices_equal`, VWAP와 유효성.
- quote source type, bid/ask, `locked/nonlocked/crossed`, depth receipt·유효성. 정확한 수량/venue 결속이 없는 관측은 실행 가능 BBO로 승격하지 않는다.
- 산출 fact와 원 source gap을 별도 보존. 과거 raw나 projection을 덮어쓰지 않고 복구/재생 receipt로 연결한다.

**완료 기준:** 같은 입력/cutoff의 live feature producer와 오프라인 소비자가 같은 수치·receipt hash를 만든다. locked·crossed·stale·route/epoch 변경·빈/짧은 tick window·미래 tick·잔존 source 혼합 회귀가 통과한다. REST/WS parser·수신/복구 흐름을 수정하게 되면 AGENTS의 공식 Kiwoom revision·경로·조회시각 확인을 먼저 수행한다. 새 API 호출/수집은 이 계획의 전제가 아니다.

## 4. P1 — 보합 수급을 표현하는 기계 규칙 계약

### 코드 위치와 함수 경계

`src/engine/scalping/entry_setup_evidence.py`의 fact/위험 결속, `entry_strategy_policy.py`의 검증·재구성, 기존 오프라인 `entry_policy_confirmation_research.py`를 연결한다. 새 공통 함수가 필요하면 `src/engine/scalping`이 소유하며 engine root에 모듈을 추가하지 않는다.

순수 함수 입력은 `(source_receipt, rebuilt_setup, exact_profile)`이다. 미래 가격·결과·AI를 받지 않는다. 출력은 조건 일치 여부, source 검증, 원 위험별 fact 목록, 제안 counterweight, unresolved risk, parent action과 report-only 제안이다. 실제 행동 변경과 risk fact 삭제를 숨기지 않는다.

| 현재 결손/위험 | 구현해야 할 명시적 처리 |
|---|---|
| 가격 반응0 | 기존 `micro_positive_price_response=false`를 유지하고 `flat_price_buy_flow`를 별도 산출한다. |
| ADVERSE_TAPE | program 순매도·program 증분 매도·외국인/기관 동반 매도의 **각 fact**를 원 ledger에 남긴다. 보합 수급으로 어떤 fact를 상쇄하는지 새 recipe의 허용 목록과 근거를 명시한다. 전체 risk code를 통째로 삭제하지 않는다. |
| trigger 미확인 | 새 보합 수급 trigger가 기존 가격 상승 trigger를 대체하는 조건을 독립적으로 검증한다. |
| local breakout 재확인 | 기존 돌파 조건 미충족을 그대로 기록한다. 보합 회복 family의 진입을 허용할 경우 돌파 통과로 위조하지 않고 별도 family/recipe 선택으로 표현한다. |
| NO_VALID_SETUP | 보합 수급 family 자체의 setup 성립 계약을 둔다. 임의로 기존 family나 READY를 부여하지 않는다. |
| LIQUIDITY_FRAGILE | 수치 hard 경계 통과와 fact 상쇄를 구분한다. 매수 수급만으로 liquidity fact를 지우지 않는다. |
| invalidation/source/보호 위험 | 원 BLOCK·source·hard safety·owner·bot-state·order/quantity/cooldown·situation veto를 보존한다. |

처음에는 report-only schema를 사용하고 운영 validator가 이를 live policy로 받아들이지 않게 한다. 이를 이유로 원천 진단까지 추가 승인에 묶지는 않는다. 정책 표현이 등록되면 같은 순수 함수를 runtime와 장후에서 소비하고 profile scope는 삼성전자로 제한한다. 삼성전자외 parent 행동 불변 회귀를 포함한다.

## 5. P2 — 같은 평가 함수로 후보와 기준선 비교

1. 원519행·조건73행·비중복24행에서 parent 재현, source 분기, risk별 처리와 실제 제안 행동을 ledger로 만든다. 원 ENTER 보존률은 진단이며100%/80% 미만을 탈락 조건으로 사용하지 않는다.
2. 9/29·9/30에서 이미 선정한 조건을 유지한다. 10/2의 새14:52 결과를 보고 임계값·허용 risk를 다시 고르지 않는다. 새 family/counterweight 계약의 변화는 사후 연구 버전으로 밝힌다.
3. 목표/손절·시간종료·후속 부족/비용 결손을 각각 집계한다. 10분 미도달은20/30/60분·세션 종료로 보조하되 손절 선도달 뒤 반등을 최초 목표로 바꾸지 않는다.
4. 양쪽에 동일 가격·비용·점유를 적용한다. 원8진입 고정 비교와 전체 신호 재점유를 둘 다 낸다. 기준선10/2는 경계 확정0이므로 목표/(목표+손절)는 null이며 후보와의 승률 차이를0% 대비로 계산하지 않는다.
5. 날짜·원 native·source clock·비용·첫 봉 불확실성 민감도를 재검토한다. 같은 watch의 여러 진입을 독립 native 기회로 바꾸지 않는다. 연구 승률 우선 순위와 실제 운영 성과 검증을 분리한다.

**완료 기준:** 후보 조건 일치와 기계 ENTER 제안 수가 명확히 구분되고, 각각의 미승격 이유가 source/fact/guard에 결속된다. 기존 정책보다 우수하다는 결론은 비교 가능한 분모에서만 낸다. 등록 계약 부재를 원 패턴의 성과 부재로 해석하지 않는다.

## 6. P3 — 리뷰·결함 수정·정식 채택 경계

- 순수 함수의 runtime/postclose 동등성, 모든 risk fact 처리, source 미래 누출·scope 혼합·누락값0 대체·고정 후보 재선정 여부를 검토한다. 표적 회귀→보완→재리뷰→compile/diff/문서 parser로 닫는다.
- report-only로 유효 후보가 표현되면 기존 정책 발행/선정 계약에 따라 별도 정식 검증한다. 현10/2의 반복 연구 결과를 새 독립 검증이나 실현 손익으로 표현하지 않는다.
- 연구 결과가 불충분하면 어떤 추가 계산/원천 결속이 필요한지 명시한다. 이미 보유한 archive로 할 수 있는 검증을 먼저 완료하며 수집 확대를 기본 해법으로 삼지 않는다.

실행 owner와 날짜별 완료 기록은 [10/4 checklist](../checklists/2026-10-04-stage2-todo-checklist.md)의 `SamsungFlatBuyFlowContract1004`가 소유한다. 위 P0–P3 운영 구현은 후속 범위이며 이번 완료 항목에 구현 완료로 합산하지 않는다.

## 7. 사용자 후속 실행 — 2026-10-04

위 계획 수립 이후 사용자가 다음 액션 실행을 지시했다. 실행 owner는 `SamsungFlatBuyFlowImplementation1004`이며 [구현·재생 리뷰](../audits/samsung-source-recipe-and-non-samsung-horizon-review-2026-10-04.md)가 완료 범위와 한계를 소유한다.

- P0: 로컬 exact-route 관측 선택·실제 feature window receipt를 구현했다. locked BBO 관측과 실행 호가를 구분하고 원 epoch/시각/sequence를 결속했다. source producer 및 기존 prepared-entry 소비자 표적 회귀를 통과했다.
- P1: 미등록 report-only 보합 수급 평가 함수를 scalping 패키지에 구현했다. 허용 위험별 제안 상쇄와 남은 위험을 보존한다. 기존 ENTER 유지형뿐 아니라 조건 불일치 기존 ENTER를 제외하는 교체형도 비교한다. 성공100%/80% 보존 veto는 없다.
- P2: 원 전체 captured feature로519행을 재생하고 archive 같은 원천시각의 체결값을 대사했다. 조건76·신규 ENTER 제안54관측, 앞선 두 날짜에서 교체형 연구 선택,10/2 비중복 목표4·손절2·시간종료2다. **과거 최신 snapshot의 전체 market/program/candle feature 재구축은 입력 부족으로 미입증**이다. 부분3필드 덮어쓰기를 전체 재구축으로 간주하지 않는다.
- P3: 리뷰→보완→재리뷰 및 관련202회귀·compile·location·hash·문서/diff/parser 검증을 완료했다. 운영 recipe 등록/발행·배포·자연 소비·독립 날짜·실현 경제성 검증은 완료 범위에 포함하지 않는다.

삼성전자외 전체 행동 통합 및10분 이후 가격 연구는 같은 리뷰의 별도 집합/후보로 기록했다. 원 native 연결이나 완전 입력이 확인된 범위에서 후속 evaluator 재생을 진행하며 이번 연구 승률을 정책 적용 receipt로 쓰지 않는다.

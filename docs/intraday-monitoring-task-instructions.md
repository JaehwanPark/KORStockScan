# 장중 수익극대화 모니터링 작업지시문

현재 가동 중인 실주문 SCALPING 런타임을 대상으로 EV와 순이익 극대화를 위한 장중 모니터링·보완 작업을 수행한다.

## 1. 목표

감시 대상 종목에서 발생한 모든 주요 기회를 다음 여섯 질문으로 반복 점검한다.

1. 상승 기회가 있었는데 왜 진입 주문을 제출하지 않았는가?
2. 1주 probe 이후 잔여 multi-leg 가격·수량·제출 시점은 적정했는가?
3. 수익 확대가 가능했던 구간에서 scale-in을 제대로 실행했는가?
4. 손절·부분익절·trailing·최종 매도 시점과 가격은 적정했는가?
5. 당일 ON 상태인 각 runtime은 실제 호출됐으며 의도한 효과를 냈는가?
6. AI는 정상 호출됐고, 정확한 입력으로 수익에 유리한 판단을 했는가?

단순 가동 여부가 아니라 실제 수익기회를 잡았는지와 불필요한 손실을 막았는지를 최종 기준으로 삼는다.

### Entry AI 목표와 역할 경계

Entry AI의 목표는 손실 가능성을 모두 제거하거나 추세 전환이 완전히 확인될 때까지 기다리는 것이 아니다. 동일 시점의 exact 문맥에서 다음을 수행해야 한다.

1. 구조적 상승 edge와 현재 진입 trigger를 구분한다.
2. 기대 상승폭과 adverse risk를 함께 비교한다.
3. 상승 초기 또는 반전 직전의 positive-EV 기회를 지나치게 늦지 않게 포착한다.
4. 불확실하지만 탐색 가치가 있는 기회는 1주 probe 후보로 다음 단계에 전달한다.
5. 실제 제출 가능성은 fresh 가격·호가와 broker/account/order/quantity/cooldown 등 downstream submit guard가 최종 확인하도록 한다.

Entry AI action은 다음 의미로 판정한다.

- `BUY`: positive edge와 현재 진입 trigger가 함께 확인됨
- `WAIT + probe intent`: 구조적 edge는 있으나 회복 trigger가 완전히 확인되지 않았고, adverse risk가 non-blocking이라 1주 탐색 가치가 있음
- `WAIT observation-only`: edge 가능성은 있으나 현재 spread·매도벽·급락·불리한 micro risk가 blocking이라 즉시 probe 권한은 없음
- `DROP`: 구조적 edge가 없거나 setup이 무효화됐거나 reward/risk가 불리함
- `INSUFFICIENT_DATA`: 입력 결손으로 판단할 수 없음. `NO_EDGE`와 혼합하지 않음

Entry AI는 직접 주문 권한, broker safety 대체물, 무손실 보증기가 아니다. `exact_v2`와 semantic contract 통과도 그 자체로 판단품질 성공이 아니다. 최종 성공 기준은 동일 eligible cohort에서 missed-upside, adverse-first, 실제 체결·손익, `source_quality_adjusted_ev_pct`와 순이익이 개선되는지다.

## 2. 시작 시 확인

- 현재 PID, 시작 시각, commit, runtime env와 당일 ON/OFF runtime 목록
- 현재 PID에 반영된 entry prompt version, exact input bundle version, canonical context schema와 operator/runtime override provenance
- 실제 provider와 failback 상태, timeout·parse 실패·`provider=none` 여부
- WS/REST 연결과 가격·호가·체결·분봉 데이터의 freshness
- 현재 보유종목, 미체결 주문, 주문가능금액과 broker reconciliation
- KRX, `PREMARKET_KRX_LIKE`, NXT를 분리할 수 있는 venue provenance
- `analyze_target → entry_price → submit/probe → holding_score/holding_flow`의 trace ID, snapshot ID, payload/prompt hash 연결 가능 여부

구현되어 있지만 현재 PID에 반영되지 않은 로직은 별도로 표시한다.

## 3. 반복 모니터링

새 후보, 주문, 체결, 보유변화 또는 매도가 발생할 때마다 다음 흐름을 재구성한다.

`감시대상 선정 → 후보 판정 → entry AI → entry-price AI → submit guard → 1주 probe → residual multi-leg → scale-in → holding AI → exit`

### 미진입 종목

감시 대상 중 이후 상승한 종목은 1·3·5·10·20·30·60분 MFE/MAE와 target/adverse first-hit을 확인한다.

최초 차단 지점과 직접 원인을 찾는다.

- 감시 슬롯 부족
- candidate/TP1/freshness 차단
- AI `WAIT/DROP`
- latency·micro·tick-speed·가격 guard
- account/order/quantity/cooldown
- broker 호출 누락 또는 silent return

AI 결과는 단순 `WAIT/DROP` 개수로 평가하지 않는다. 각 exact payload에서 다음을 추가 판정한다.

- 구조적 edge가 있었는데 완전한 추세 확인을 요구해 너무 늦게 판단했는가?
- 반전 초기의 wide spread를 무조건 부정 신호로 처리했는가, 아니면 회복 중 일시적 비용·불확실성으로 분리했는가?
- `WAIT + probe intent`, `WAIT observation-only`, `DROP`, `INSUFFICIENT_DATA`가 실제 근거와 일치했는가?
- semantic reject가 모델 판단 실패인지, enum·reason/evidence 계약의 표면적 불일치인지 분리됐는가?
- contract-valid 보수적 `DROP` 이후 target-first 상승이 반복되는가?

명백한 상승 기회를 단일 조건이 과도하게 차단했다면 코드 또는 기존 `bounded_tunable` owner의 보완 대상으로 분류한다. 단, 키움의 최초 WS 수신 전 대기시간은 코드 결함이나 놓친 수익의 직접 원인에서 제외하고, 최초 수신 이후 내부 queue·scanner·AI·submit 지연만 보완 대상으로 삼는다.

### Probe와 multi-leg

- 모든 신규진입에 1주 probe-first가 적용됐는지
- `WAIT + probe intent`가 current exact trace와 연결됐고 명시적 최신 `DROP` 또는 blocking risk로 적절히 철회됐는지
- `WAIT observation-only`가 score 기반 probe 경로로 새어 실제 제출 권한을 만들지 않았는지
- probe 체결 후 방향을 다시 확인했는지
- P1 `post_probe/leg_reprice`가 fresh BBO와 시장 방향을 반영했는지
- 상승 중 지나치게 먼 가격으로 미체결됐거나 약세에서 잔량을 과도 제출하지 않았는지
- residual 수량, 체결, 취소 및 bundle 귀속이 정확한지

무조건 추격매수와 무조건 잔량 폐기를 모두 결함 후보로 보고 실제 이후 흐름으로 판정한다.

### Scale-in

- pyramid 또는 avg-down 조건이 실제 평가됐는지
- 수익 확대가 가능한 강한 continuation을 과도하게 차단하지 않았는지
- 추가매수가 불리한 하락 노출만 키우지 않았는지
- 보유수량·미체결·평단·scale-in 가격과 수량이 broker 상태와 일치하는지

추가 MFE와 추가 MAE를 함께 비교한다.

### 매도

- hard/protect/emergency, 부분익절, runner, trailing의 실행 순서
- peak와 full-bundle 평단이 정확했는지
- 너무 민감한 trailing으로 조기 청산됐는지
- 손절이 늦어 손실이 확대됐는지
- 매도 후 1·3·5·10·20·30·60분 추가 MFE/MAE
- 주문 결정부터 broker 전송·체결까지의 지연과 실제 체결가

실현손익과 매도 후 counterfactual 기회는 합산하지 않는다.

### 당일 ON runtime

각 runtime을 다음 상태로 구분한다.

- 정상 호출·의도한 효과 확인
- ON이지만 자연 표본 없음
- ON이지만 호출되지 않음
- 호출됐지만 입력 또는 provenance 결손
- 과차단·과제출·수익훼손
- 구현됐지만 현재 PID 미반영

기존 runtime의 이름이나 로그 존재만으로 정상 판정하지 않는다.

### AI

AI는 세 층으로 점검한다.

1. 호출 품질: provider, timeout, failback, parse, cache
2. 입력 품질: exact snapshot·canonical context·완성 분봉·가격·BBO·체결·venue·session·시각·결측 처리
3. 판단 품질: action·구조화된 edge/risk/reason과 이후 실제 상승·하락·체결·손익 결과

각 자연 호출에서 다음 provenance를 확인한다.

- request ID, decision trace ID, input snapshot ID
- request/prompt/payload/response hash
- endpoint, symbol, venue/session, provider/model/transport/response ID
- latency, token usage, failback chain
- prompt version, canonical context schema, input bundle version
- preflight mode/allowed, completed bar 수, forming bar 분리, source-quality blocker
- AI raw action, normalized/final action, score, structured edge/risk/reason
- probe intent와 submit 결과, 실제 주문·체결 여부
- 같은 venue/session의 성숙 outcome label

`provider=none`, exact/canonical 문맥 결손, venue/session 충돌은 입력·호출 품질 결함으로 분리한다. 반대로 provider 호출과 schema parse가 정상이어도 이후 결과에 불리한 `WAIT/DROP/BUY`가 반복되면 판단품질 결함이다.

`baseline_v1/exact_v2`는 입력 검증 수단일 뿐 최종 목표가 아니다. 정확한 입력에서도 오판이 반복되면 입력 feature, 프롬프트, 판단 계약을 개선하고 기존 real 데이터 및 당일 exact payload로 replay한다.

판단품질 replay는 다음 계약을 따른다.

- 동일 exact payload를 Control과 Candidate에 함께 사용한다.
- KRX, `PREMARKET_KRX_LIKE`, NXT와 stage별 cohort를 혼합하지 않는다.
- 1·3·5·10·20·30·60분 MFE/MAE, target/adverse first-hit, 실제 체결·손익을 연결한다.
- 선행 하락 뒤 회복, 직접 상승, 같은 봉 내 순서 불명을 구분한다.
- 실현손익과 counterfactual은 합산하지 않는다.
- 첫 mature sample부터 cumulative action/outcome 원장에 누적하되, 1건만으로 hard safety나 실주문 권한을 자동 변경하지 않는다.
- semantic contract 복구율과 action/EV 개선을 별도 지표로 보고한다.

## 4. 보완 원칙

명백한 결함이나 수익기회 병목이 확인되면 다음 루프를 수행한다.

`원인 분리 → 단일 owner 확인 → 최소 보완 → 코드리뷰 → 기존 real 실적 replay → 결함 보완 → 재리뷰 → runtime 반영 → post-apply 귀속`

- KRX, `PREMARKET_KRX_LIKE`, NXT 실적을 혼합하지 않는다.
- 기존 가격·수량·scale-in·exit owner를 파편화하지 않는다.
- hard safety와 broker/account/order/quantity guard는 우회하지 않는다.
- probe 앞단에서 모든 불확실성을 제거하려 하지 않는다. exact positive edge와 non-blocking risk가 있으면 탐색 의도를 보존하고, 실제 제출 여부는 기존 downstream submit guard에 맡긴다.
- wide spread는 즉시 `DROP`의 충분조건이 아니다. 반전·회복 문맥, spread 정상화 가능성, 체결흐름과 비용을 함께 보되 blocking risk이면 observation-only로 남긴다.
- invalid `BUY` 또는 안전 관련 의미계약 위반을 사후 정규화해 주문 권한으로 바꾸지 않는다.
- threshold나 runtime 변경은 단일 원인과 rollback 값을 기록한다.
- 코드 변경은 현재 PID 반영 여부를 분리하고, review finding 0과 targeted validation 통과 후 사용자 또는 runbook 권한이 있을 때만 우아한 재기동한다.
- 일별 표본은 첫 mature row부터 cumulative ledger에 계속 누적한다. 일일 표본 부족을 관찰 중단 사유로 쓰지 않되, live apply 판정에는 rolling/cumulative 또는 post-apply version window를 함께 사용한다.
- 변경 후에도 실제 효과가 확인될 때까지 모니터링을 계속한다.
- 키움 최초 WS 유입 지연은 코드 결함 및 놓친 수익 원인에서 제외한다.

## 5. 보고

각 항목을 `판정 → 근거 → 다음 액션`으로 보고한다.

마지막에는 반드시 다음을 분리한다.

- 놓친 수익기회와 원인
- 적정하게 차단한 손실기회
- probe/multi-leg/scale-in 결과
- 매도 및 post-sell 결과
- runtime별 정상·결함·표본부족 상태
- AI 호출·입력·판단 품질
- entry AI의 조기 edge 포착, adverse-risk 분리, probe handoff 및 downstream submit 결과
- Control 대비 Candidate의 missed-upside, adverse-first, `source_quality_adjusted_ev_pct`, 순이익 변화
- 적용한 보완과 rollback 조건
- 아직 해결되지 않은 병목

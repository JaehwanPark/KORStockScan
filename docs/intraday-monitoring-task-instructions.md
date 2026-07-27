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

## 2. 시작 시 확인

- 현재 PID, 시작 시각, commit, runtime env와 당일 ON/OFF runtime 목록
- 실제 provider와 failback 상태, timeout·parse 실패·`provider=none` 여부
- WS/REST 연결과 가격·호가·체결·분봉 데이터의 freshness
- 현재 보유종목, 미체결 주문, 주문가능금액과 broker reconciliation
- KRX, `PREMARKET_KRX_LIKE`, NXT를 분리할 수 있는 venue provenance

구현되어 있지만 현재 PID에 반영되지 않은 로직은 별도로 표시한다.

## 3. 반복 모니터링

새 후보, 주문, 체결, 보유변화 또는 매도가 발생할 때마다 다음 흐름을 재구성한다.

`감시대상 선정 → 후보 판정 → AI 판단 → submit guard → 1주 probe → residual multi-leg → scale-in → holding → exit`

### 미진입 종목

감시 대상 중 이후 상승한 종목은 1·3·5·10·20·30·60분 MFE/MAE와 target/adverse first-hit을 확인한다.

최초 차단 지점과 직접 원인을 찾는다.

- 감시 슬롯 부족
- candidate/TP1/freshness 차단
- AI `WAIT/DROP`
- latency·micro·tick-speed·가격 guard
- account/order/quantity/cooldown
- broker 호출 누락 또는 silent return

명백한 상승 기회를 단일 조건이 과도하게 차단했다면 코드 또는 bounded runtime 보완 대상으로 분류한다.

### Probe와 multi-leg

- 모든 신규진입에 1주 probe-first가 적용됐는지
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
2. 입력 품질: 분봉·가격·BBO·체결·venue·시각·결측 처리
3. 판단 품질: AI 판단 이후 실제 상승·하락 및 손익 결과

`baseline_v1/exact_v2`는 입력 검증 수단일 뿐 최종 목표가 아니다. 정확한 입력에서도 오판이 반복되면 입력 feature, 프롬프트, 판단 계약을 개선하고 기존 real 데이터 및 당일 exact payload로 replay한다.

## 4. 보완 원칙

명백한 결함이나 수익기회 병목이 확인되면 다음 루프를 수행한다.

`원인 분리 → 단일 owner 확인 → 최소 보완 → 코드리뷰 → 기존 real 실적 replay → 결함 보완 → 재리뷰 → runtime 반영 → post-apply 귀속`

- KRX와 NXT 실적을 혼합하지 않는다.
- 기존 가격·수량·scale-in·exit owner를 파편화하지 않는다.
- hard safety와 broker/account/order/quantity guard는 우회하지 않는다.
- threshold나 runtime 변경은 단일 원인과 rollback 값을 기록한다.
- 변경 후에도 실제 효과가 확인될 때까지 모니터링을 계속한다.

## 5. 보고

각 항목을 `판정 → 근거 → 다음 액션`으로 보고한다.

마지막에는 반드시 다음을 분리한다.

- 놓친 수익기회와 원인
- 적정하게 차단한 손실기회
- probe/multi-leg/scale-in 결과
- 매도 및 post-sell 결과
- runtime별 정상·결함·표본부족 상태
- AI 호출·입력·판단 품질
- 적용한 보완과 rollback 조건
- 아직 해결되지 않은 병목

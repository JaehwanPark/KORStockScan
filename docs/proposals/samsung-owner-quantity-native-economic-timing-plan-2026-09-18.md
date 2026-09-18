# 삼성 위젯·에피소드 승인 수량 기준 경제성 timing 개선

사용자 지시: 기존 성과를 출발점의 우월성 근거로 삼지 않고, 삼성전자 위젯·에피소드에서 비용 차감 경제성이 나아지는 판단을 탐색한다. 2026-09-19 자본 계약 회신은 **owner별 승인 수량으로 독립 비교**이다. 공유 삼성 예산이나 새 자본 배분 권한을 만들지 않는다. 합산 자본은 수요·노출 진단이다.

## 범위와 기존 owner

- 원 기회·주문·custody: 기존 `SamsungRegularTwoLegMachine`, morning subclass, `WidgetSignalAutoTrader`의 journal/checkpoint. 별도 collector·서비스·DB를 만들지 않는다.
- 시장 원천·projection: 기존 `monitoring.machine_microstructure_attribution`의 한 번 수행되는 bounded canonical 0B/0D traversal.
- 계산·모델 검증: 기존 `monitoring.machine_entry_confirmation_study`에 native operating adapter를 둔다. 공통 300초/1200초 첫 도달 진단은 승격 근거가 아니다.
- 단일 timing 정책 owner: `automation.machine_entry_timing_tuning`; 기존 `run_machine_microstructure_final_refresh.sh`가 source 이후 실행한다. Daily/PREOPEN reader와 장중 native loader가 같은 dated policy/evidence hash를 읽는다.
- `monitoring.samsung_machine_entry_tuning`은 actual·기존 tightening 원복 진단 역할을 유지한다. 신규 confirmation 탐색은 timing owner로 집중한다.
- 실행 중 immutable release와 다른 세션 변경을 보존한다. 후속 release·독립 Samsung/widget unit의 **미래 기동 경로**를 배포하되 수동 restart·주문·조기 PREOPEN 확정은 하지 않는다.

## S0. frozen 모집단과 가설

원 신호를 체결 leg 대신 하나의 frozen parent opportunity로 기록한다. 거절·recheck·guard 차단·미체결·보유도 분모에 남긴다. 동일 root 재시도는 중복 제거하고 identity 충돌은 제외 사유를 기록한다.

기존 네 arm `baseline / bid_rebound / depletion_flow / combined`만 비교한다. 질문은 공통 hard guard를 유지한 상태에서 bid 회복 확인이나 실제 체결이 뒷받침한 ask 소진 확인이 불리한 진입·수익 부족·긴 보유를 줄이는가이다. 후보는 새 매매 전략·수량·손절·목표가·예산을 만들지 않는다.

기존 approved native 수량과 각 owner의 plan/target/route가 frozen된다. 위젯 현행 equal-share 3-leg의 최대 승인 수량, initial/add의 서로 다른 주문, pooled target을 재현한다. 에피소드는 실제 적용 native quantity receipt·tick target을 사용한다. 두 owner 및 서로 다른 scope의 자본을 임의 공유하지 않는다.

## S1. 미래 원천 계약

1. native confirmation 전 plan·정확한 decision clock·native policy type/content·quantity authority·owner code SHA·cost contract·선택된 exit programme pin을 저장한다.
2. SOR prearm처럼 아직 주문가가 없는 상태를 완성된 plan으로 만들지 않는다. 원 opening price가 도착한 기존 resolver에서 그 **최초 실행 가능한 시점**에 frozen source를 만든다. raw 14자리 native bar identity를 보존하며 검증된 날짜/시각 형식만 해석한다.
3. 원 BUY 제출을 허용한 공통 guard barrier를 기록한다. 차단 후 원 recheck가 실제 제출을 허용하면 그 최초 허용 시각부터 갱신한다. 모든 CF arm은 그 시각 이전에 주문하지 못한다. 알려진 공통 guard 차단은 no-order 진단이며 missing fill/PnL을 0으로 대체하지 않는다. 첫 BUY 이후 guard 변경은 별도 unsupported intervention이다.
4. initial와 각 add leg의 as-of guard를 구분한다. ADD1 허용을 ADD2에 쓰지 않는다. target cancel 이후 마지막 weakness 확인을 통과한 실제 BUY 직전 허용 receipt를 기록한다.
5. owner의 programme write guard는 unchanged interval과 측정된 cadence로 압축한다. 매초 같은 사실을 누적한 새 거대 ledger/쓰기 loop를 만들지 않는다. 범위·overflow·continuity 결손은 명시한다.
6. native root→leg/intent→broker order→fill/terminal identity를 유지한다. NXT/SOR route 변환이 이전 root의 leg를 덮어쓰지 않는다. 위젯 KRX 판단 호가와 SOR execution depth를 분리하여 서로 대체하지 않는다. supplemental SELL은 **자신의** custody registry quantity/amount/clock만 사용한다. terminal lookup은 크기 검사 및 재사용하며 원 ledger는 변경하지 않는다.

## S2. native 경제성 재현

- 원 full-fill native BUY basis로 target을 만든다. 여러 가격 체결의 weighted basis를 leg별 실제 target 계약으로 변환한다. 같은 quote의 depth를 두 leg에 중복 사용하지 않는다.
- 주문 reserve와 보유 자본 KRW-minutes, 체결 참여율·완료 비용 순익·EV·P10/worst tail을 계산한다. fee는 frozen shared trade-profit configuration을 SELL notional에 한 번 적용하고 code/value SHA를 보존한다. broker settlement fee·tax 또는 account cash net으로 표기하지 않는다.
- target-only뿐 아니라 선택된 profit-stagnation·target-ratchet pin을 인계한다. 기존 `positive_net_stagnation`, `pressure_from_snapshot`, `executable_quote`를 재사용한다. selected pin 자체는 unsupported 사유가 아니다.
- native target을 유지하는 입력 fallback, own guard veto, 정정/취소·replacement의 measured clock을 구분한다. 실제로 해당 action이 필요할 때만 독립 검증된 action-model witness를 요구한다. 원 target의 보호를 ack 전까지 유지하며 loss guard를 재검사한다.
- 시장 경로 끝에서 forced SELL·synthetic liquidation을 만들지 않는다. 원 window 내 미완료는 pending/null. bounded prefix 소진은 source gap이다. partial BUY·cancel race·복잡한 remainder·carry market replay 등 모델로 입증하지 못한 범위는 unsupported/null로 명시한다. 실제 완료 손익의 원 owner 연결은 별도로 유지한다.

## S3. 운영 모델 검증

기존 실측 full-fill native owner 주문의 submit/target ack·full-marketability→owner terminal 관측 clock·depth coverage·scale cadence/cancel·supplemental action clock을 사용한다. 이는 local owner reconciliation 모델이며 실제 exchange queue rank나 wire latency라는 주장은 하지 않는다.

가장 이른 모델 prefix를 calibration→더 늦은 model holdout으로 나눈다. 기존 모델 표본 floor 20과 coverage 계약을 유지한다. 오차 tolerance는 calibration 실측에서 계산하고 chronological holdout에서 quantity/비용 순익/capital/reserve/terminal clock 오차를 검증한다. 값이나 tolerance를 새로 가정하지 않는다.

새 action의 native witness와 이후 독립 witness가 축적되면 model prefix와 버전을 갱신한다. 최초 target-only prefix에 영구 고정하여 미래 action을 계속 결손으로 두지 않는다. action은 양쪽 partition의 관측 계약을 충족해야 지원한다. model의 마지막 knowledge date 이후 입력만 candidate 연구에 쓴다.

## S4. paired 선정

동일 frozen demand envelope·총수량·후행 hard guard에서 네 arm을 계산한다. 변하지 않는 비교는 진단/no-edge로 남긴다. 자본 배분 계약 없이 겹치는 root에 같은 자본을 재사용해 portfolio 이익을 만들지 않는다.

기존 후보 floor(5 trading days, 8 unique/completed pairs, 85% paired coverage), 보수적 ΔEV 하한 0.005%p, P10 악화 한도 0.01%p를 완화하지 않는다. observed worst paired delta에서 양 arm의 검증 오차를 차감하고 native clock stress를 실제 재생한다. 이 값은 관측 하한이며 통계적 신뢰구간·미래 이익 보장이 아니다.

candidate calibration에서 한 번 선택한 arm을 별도 마지막 chronological candidate holdout에서 검증한다. holdout을 재선정에 쓰지 않는다. rolling 5 source days/cumulative에서도 양수 비용 EV·하한·tail 계약을 요구한다. 모형 불확실성·pending 손실 경로는 승격에서 제외하고 분모와 blocker를 보존한다.

## S5. 정책 전달 및 fallback

검증된 receipt만 기존 v3 dated timing policy로 변환한다. immutable evidence snapshot→policy SHA→Daily/PREOPEN reader→native loader의 native policy/quantity/cost/code/exit pin/scope 계약을 대사한다. 삼성 feature-arm 변화는 기존 confirmation 범위에서만 허용한다.

양수 조건을 충족한 통제 입력에서는 활성 정책 생성·소비가 작동해야 한다. stale/hash/tamper/scope/quantity/holdout 실패에서는 incumbent/baseline으로 fallback한다. 후보0은 source gap·unsupported scope·pending·insufficient sample·valid no-edge로 구분한다. 새로운 경제성 후보가 없어도 다음 적용일 dated incumbent 정책을 준비하되 positive edge로 보고하지 않는다.

## S6. 실제 적용 버전별 평가와 closure

native scope/code/cost/선택 programme 및 실제 confirmation policy hash별로 exact root를 중복 제거한다. rolling/cumulative native priced net·EV·tail·capital/reserve·참여율과 모델 오차를 연결한다. carry가 완료되면 기존 bounded owner checkpoint에서 **actual terminal만** 갱신한다. 원 date reset은 bounded terminal history를 보존하며, 검증된 exact-root actual은 기존 timing 보고서의 sealed completion history에 누적하여 checkpoint 교체 후에도 잃지 않는다. history의 미래 knowledge date·identity 충돌·tamper는 배제하고 CF path를 변경하지 않는다. 늦게 관측한 actual을 이전 as-of로 앞당기거나 CF 시장 경로/SELL로 붙이지 않는다.

구현 closure는 원 producer/저장/projection/지원 입력 계산/독립 holdout/선정/dated 소비/fallback 회귀 증거다. OPEN은 미래 source 정상 생성, 독립 자연 표본 축적, 실제 적용 PID/행동, 원 주문 완료 가격 및 실제 broker 비용/settled cash net, 인과적 개선 확인이다. 모델 ΔEV, broker-price+frozen-cost 순익, settled 실제 순익, 인과적 개선을 분리한다.

현재 KST는 9/19이며 당일 checklist는 없다. source-day 9/18 작업을 자정 후 다른 거래일로 재라벨링하지 않는다. 기존 stable 실행 ID의 다음 acceptance owner는 [9/21 checklist](../checklists/2026-09-21-stage2-todo-checklist.md)로 인계한다. 결과/commit/deployment/regeneration 증거는 [owning review](../audit-reports/2026-09-18-samsung-owner-native-economic-timing-implementation-review.md)에 기록한다.

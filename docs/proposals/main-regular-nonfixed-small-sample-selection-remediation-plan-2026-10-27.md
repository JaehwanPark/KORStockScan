# 정규장 비상시 소표본 완승 고착 보완계획 — 2026-10-27

## 1. 결정·범위

**제안:** 비용을 반영한 WIN/STOP/TIMEOUT 라벨은 유지하고, 기계정책 순위를 `반복 확인점의 단순 승률`에서 `시간 중복을 제거한 누적 승률의 불확실성 보정 점수`로 바꾼다. 추가 패턴이 실패1건 때문에 소표본100% 현행에 영구히 밀리는 문제를 보완한다. 손익비·EV·AI 점수·호가 guard 완화를 순위에 넣지 않는다.

이 문서는 **선택 계약의 변경안과 구현 owner**다. 현행 `cost_bound_cumulative_target_first_fraction`과 구분한다. 후속 구현 지시에 따라 격리 작업본에서 구현·리뷰·검증을 수행했다. 운영 채택·배포는 미실행이며, source27 종료 재검증은 아직 미래 창이다. [구현·원천·잔여 검증](../audits/main-regular-nonfixed-pattern-contribution-review-2026-10-27.md#8-선택구조-구현과-원천-소비-재점검--1439)이 현재 상태를 소유한다.

첫 범위는 `other_non_fixed|REGULAR|LT_20000/20000_TO_100000/GE_100000|SOR`다. 상시·PRE·AFTER·다른 route의 정책은 그대로 둔다. 기존 [MachinePatternOpportunityResearch1023 / MainEntrySourceTerminalRepair1022](../checklists/2026-10-27-stage2-todo-checklist.md)의 원 작업 창과 Acceptance를 유지하고 새 owner/예약을 만들지 않는다. 선행 [연구계획 §8](main-auxiliary-spread-liquidity-and-deadline-remediation-plan-2026-10-27.md#8-정규장-비상시-추가-패턴-비교-완료와-보완안)을 구체화한 문서다.

## 2. 제안하는 단일 선택 규칙

### 비교 단위

1. 원 source26의09/29 이후 적격 누적 원천과 같은 item·epoch·sequence·entry ask·비용을 사용한다. 계약은 비용0.0023,30분 이내 비용 후+0.4%,소프트손절−3% 선도달 없음이다. 손실 금액은 순위에 사용하지 않는다.
2. 각 사전 등록 조합의 TRUE 확인점을 종목·날짜·route별 시각 순서로 정렬한다. 첫 확인점을 평가하고1800초 동안 다른 확인점을 통계에서 중복 진입으로 세지 않는다. 첫 결과가 미확정/실패라도 뒤의 WIN으로 교체하지 않는다. 같은 시각은 원 key 순서로 결정한다.
3. 이1800초는 **통계 단위**다. 실제 주문 cooldown·보유·청산 시간을1800초로 바꾸지 않는다. 기존 반복 확인점 성적도 별도 보존한다. 시간 중복을 없애도 동일 종목·날짜 상관관계가 없어지는 것은 아니므로 독립 표본이라고 단정하지 않는다.
4. `N=WIN+FAIL_STOP+FAIL_TIMEOUT`, `U`는 별도다. `N=0`이면 비율/점수 null이며 비교 불가다. 미진입·미관측을0승 또는100%로 채우지 않는다. 첫 U도1800초 구간을 차지한다.

### 순위 점수

`p=W/N`, `z=1.959963984540054`를 고정한다. 제안 점수는 다음 Wilson 하한이다.

```text
L = (p + z*z/(2*N) - z*sqrt(p*(1-p)/N + z*z/(4*N*N))) / (1 + z*z/N)
```

공식은 [NIST Wilson proportion interval](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm)을 확인했다. 여기서는 **표본 수를 반영한 승률 순위 점수**로 쓰는 안이며, 많은 후보를 탐색한 시계열 자료의 실제 성과가95% 확률로 보장된다는 뜻이 아니다. 신뢰수준을 결과에 맞춰 변경하거나 다른 보정식 중 유리한 것을 고르지 않는다. 원 승률 W/N은 점수와 항상 함께 표시한다.

- 비교대상: 현행과 사전 등록된 exact-scope 후보 조합. 다른 기회에 참여하지 않은 현행을 추가기회의0%/100% 대조군으로 만들지 않는다.
- `L`이 높은 후보를 연구 추천으로 선택한다. 같은 점수이면 W가 큰 후보, 그마저 같으면 현행, 이후 적은 branch 수·고정 ID 순으로 결정한다. 수치 비교는 고정 binary64·공통 구현/반올림 전 값으로 한다.
- 현행보다 `L`이 높지 않으면 carry한다. 현행 N=0이면 후보를 연구 순위로만 내고 현행보다 우월하다고 판정하지 않는다. 모든 후보 N=0/필수 원천 불완전이면 명시적 comparison_incomplete다.
- 새 최소 표본수·승률70%·+5pp·손익비 등 별도 탈락 조건을 더하지 않는다. 표본 수는 L 안에서 연속적으로 반영한다. 날짜/종목 편중·U·추가/제거 WIN은 의무 보고 값이며 숨겨진 veto가 아니다.
- 한 branch를 추가한 성적과 전체 합집합 성적을 모두 남긴다. 실제 시간순 재생에서 먼저 진입해 기존 나중 WIN을 대체한 경우, 추가 WIN/FAIL뿐 아니라 제거된 원 key·WIN/U를 기록한다. 승리100% 보존을 새 통과 조건으로 삼지 않는다.
- 이번 최초 비교의 후보 정의와 단일 additive-root 문법은 원 등록 계약을 유지한다. 기존 문법에서 허용하지 않는 A05+A09/A12+A14는 보고용이다. 복수 추가가 필요해지면 기존 `valid_membership`의 개수 조건을 사전 등록된 조합의 membership 검증으로 대체하는 별도 명시 변경을 한다. 개수 제한 해제만으로 성과가 좋아진다고 가정하지 않는다.

### 현재 자료에서의 차이

| 범위 | 현행 시간중복 제외 W/N ·L | 단일 추가 후보 W/N ·L | 제안 규칙의 연구 순위 |
|---|---|---|---|
| 저가 | 2/2 ·34.24% | A05 36/62 ·45.67%, A09 102/188 ·47.12% | A09 우선, A05 비교 유지 |
| 중가 | 4/4 ·51.01% | A08 166/534 ·27.31% | 현행 carry, A08 실패 원인 보완 |
| 고가 | 1/1 ·20.65% | A12 12/20 ·38.66%, A14 13/29 ·28.41% | A12 우선, A14 비교 유지 |

이는 등록된 모든 패턴의 새 전역 최적화가 아니라 사용자가 지정한 후보와 A08의 탐색 비교다. 저가 A05+A09는112/210·L46.59%로 A09보다 낮다. 고가 A12+A14는22/41·L38.75%로 A12 대비 차이가0.088pp뿐이고 원 문법에서 허용되지 않는다. 이 수치만으로 복수 등록을 확정하지 않는다.

## 3. 구현 대상과 기존 owner 변경

| 단계 | 기존 owner | 구현 내용·소비 계약 |
|---|---|---|
| S1. 선택 계약 동결 | `reversal_cumulative_registration`와 원 등록 request | 원 v2 raw-fraction 계약은 불변 보존. 새 exact-scope 선택 버전, z·통계단위·후보 ID·부모 bundle·source hash를 승인/등록 계약에 결속. 초기 등록의 호환 승계와 성과 선택을 구분 |
| S2. 누적 집계 | `reversal_cumulative_postclose` | 기존 Store/partition record를 재사용하고 key·확인시각·label을 시간순 재생. raw 및 chronological W/S/T/U, 자체 추가분·합집합·교체된 key를 생성. 미래 label로 첫 확인점을 골라서는 안 됨 |
| S3. 선택 | `reversal_cumulative_registration.select_variant` | 승인된 버전·scope일 때만 공통 Wilson 점수 적용. 원 raw selector를 다른 scope에 유지. 임의 fallback 없음. 보고서 `metric_role`, `primary_decision_metric`, `sample_floor`, `window_policy`, `source_quality_gate`, `forbidden_uses` 선언 |
| S4. 원장·보고서 | 기존 fixed comparison gzip archive와 CURRENT/SELECTED projection | 원 full comparison은 한 번의 불변 archive, 소비자는 작은 projection. 입력·응답 원장 새 복제 금지. 캐시 identity에 통계단위/score 버전/원천 세대를 포함해 예전 raw 결과를 새 점수로 재사용하지 않음 |
| S5. 직접 소비 | 기존 machine manifest·auxiliary compatibility·policy bootstrap reader | 추천과 실제 등록/게시/적용을 분리. raw 계약 report를 새 score 계약으로 잘못 읽으면 차단. 보조정책에는 선택 branch별 원 입력/동일 prompt registry 연결을 확인하고 비교 미완료를 최초 기계 등록의 임의 veto로 복원하지 않음 |
| S6. 운영 전환 | 기존 runtime release router·ordered transition | 승인된 변경만 후보 통합/리뷰/준비/부모 정책 인계 후 반영. 실제 PID의 같은 REGULAR/SOR/_AL 소비와 natural terminal을 확인. 코드/연구 통과를 배포·실제 주문 증거로 쓰지 않음 |

신규 Python root module·병행 selector·별도 자동 prompt 생성기를 만들지 않는다. 현 selector를 버전 분기해 확장하고, 이 연구 driver는 live dispatch에 등록하지 않는다. 원 raw-v2 reader는 역사 report와 범위 밖 정책의 현재 소비자가 있어 retained다. 전환 후 중복 raw-v2 계산 경로는 새 scope 소비자를 확인한 뒤 제거/통합하고 원 archive는 보존한다.

회귀: N0/null,1/1·2/2·큰 실패 포함 표본,동률/현행 유지,원천·부모 세대 충돌,중복 key/branch,시간/날짜/route 경계,첫 U/STOP,조합에 따른 기존 승리 대체,같은 입력 다른 score 버전 cache miss,기존 raw 계약 parity를 시험한다. 동일 mock 자료를 producer→selector→projection→준비 reader까지 대조한다. 선택 권한만 바뀌며 가격·계좌·수량·AI provider·기한·hard safety 권한은 생기지 않아야 한다.

## 4. 이번 추가 연구 결과와 다음 검증

이번에는 지정 후보에 닿는6,416확인점을 읽고, native-tick 라벨5,359개를 exact epoch/sequence/item/ask로 원 스트림에 연결해30분 승패를 모두 재현했다. 원천10개 partition은 한 번씩 bounded stream으로 읽었고88.5초에 완료했다. 나머지1,057개는 원 계약의 completed-bar 라벨로 보존했으며 tick 후행 경로로 꾸며내지 않았다. 신규 AI 호출0이다.

### 저가 A05/A09·고가 A12/A14

| 후보 | 중복 제외 누적 | 10/26 | 가장 많은 승리 종목 제외 | 날짜 한 개씩 제외한 승률 범위 | 판단 |
|---|---:|---:|---:|---:|---|
| 저가 A05 | 36/62,58.1% | 2/4 | 30/54,55.6% | 52.5~62.5% | 반복 확인점 기준3/18을 독립 실패18개처럼 해석하지 않음 |
| 저가 A09 | 102/188,54.3% | 16/24 | 90/160,56.3% | 49.0~59.9% | 최근 포착은 좋으나 누적 압도적 우월성은 미증명 |
| 고가 A12 | 12/20,60.0% | 0/0, U3 | 8/15,53.3% | 50.0~64.7% | WIN12개 중10개가09/29에 집중; 새 날짜 필요 |
| 고가 A14 | 13/29,44.8% | 1/5 | 6/21,28.6% | 28.6~55.6% | WIN13개 중7개가031980; 확장 우선순위 낮춤 |

현재 자료는 후보 선정에 이미 사용된 자료이므로 독립 holdout이 아니다. 다음 기존 source27 장후 창에서 종료·봉인된 적격 원천을 동일 정의로 추가하고 raw/순차/날짜별 W/S/T/U와 L을 갱신한다. source27을 사용할 수 없으면 미완료 이유를 원 owner에 유지하고 다른 날을 미래 검증처럼 대체하지 않는다. 현재 연구만으로 live 후보를 승인하지 않는다.

### 중가 A08의30분 미달

현행∪A08의 순차 표본은166WIN/4STOP/364TIMEOUT/U359다. TIMEOUT364 중 원 tick 경로가 있는246건의 원인 형태를 구분했다.

| 원 경로에서 확인한 형태 | 건수 |
|---|---:|
| 30분 내 최대 비용 후 수익률이0 이하 | 132 |
| 비용 후 양의 진전은 있었지만30분 말 음수로 종료 | 90 |
| 30분 말에도 양수이나+0.4% 미달 | 24 |

246건의 최대 비용 후 수익률 중앙값은−0.0267%,30분 말 중앙값은−0.3924%다. 60분까지의 원 첫 도달 결과는22WIN/2STOP/109TIMEOUT/U113이며, 뒤늦은22승을30분 WIN으로 바꾸지 않는다. 보강 bar118건의 세부 tick 경로는 미확정이다.

사전 관측에서 WIN/미달의 spread 중앙값은0.1479%/0.1386%,최근 매수비중은93.28/89.77,거래량비율은1.63/1.51이다. **단순 spread 확대·매수세 부재가 보편 원인이라는 근거는 없다.** A08은 작은 고점 돌파도 잡으며,60초 수익률 중앙값은 WIN0.2974%/미달0.1952%다. 사전 고정 구간 비교에서60초수익률≥0.4%는56/112,0.1~0.2%는44/196,상승구조는48/105,MIXED는76/300이었다. 연관성 진단이며 지금 즉시 hard veto로 넣지 않는다. 강한 구간만 고르면 다른 승리도 잃는다.

다음 보완 가설은 **고점 돌파의 존재와 목표까지 지속되는 거래가격 진전을 분리하는 입력**이다. 돌파 직전/확인시점의60초 거래가격 수익률,고점 대비 거리,현재 구조,매수 체결수량의 시간 변화와 비용 포함 목표거리를 같은 구간으로 보여준다. spread는 중립 호가 사실로 유지하고 실제 연속 bid 하락·되밀림과 분리한다. 확정 뒤5분/30분 경로는 평가자료로만 쓰며 AI 입력/진입 조건에 유출하지 않는다. 새 입력과 현행 입력은 동일 후보의 WIN/STOP/TIMEOUT에서 paired 비교하되 기존 응답을 우선 재사용한다. 이번에는 추가 provider 호출을 하지 않았다.

## 5. 원천 도달 재점검과 완료 경계

14:02:26, 동일6d0d19756/PID670131/start71972259에서 비상시87고유 lease·81종목을 확인했다.0B62·0D64,둘 다 없음23,native도달56이다. native56건은 모두 마지막 collector0B sequence와 일치했다. 이 일치는 마지막 sequence의 대사이며 모든 raw 패킷·이벤트 중간 이력의 완전성 보장은 아니다. 이력 TRUE/ready 및 정규장 비상시 AI/capture는0이다.

13:50 이후 새28lease는 무수신4,0B age초과2,0B없음1,현재 source stale16,패턴 불일치5다. 새로운 결손이 계속 생겨 원천 문제가 해소됐다고 볼 수 없다. 거래소/네트워크 책임을 단정하거나 gap·TTL을 늘려 해결하지 않는다.

기존 source owner의 다음 액션은 (a)새 무수신4lease의 정확 REG/0B/0D/epoch 원본 대조,(b)stale16의 마지막 거래소시각→앱 수신→정규화→native 관측 clock 차이 분리,(c)유효하나 불일치5의 선택 branch 특징 대사다. 과거6일 `source_epoch_unverified`와10/13 미수록은 별도 원 보강 receipt 대조 대상으로 남긴다. 후속 구현에서는 아래 §6의 범위까지 진행했으며, 운영 복구/장후 재생은 실행하지 않았다.

상세 데이터와 검증은 [검토서 후속 절](../audits/main-regular-nonfixed-pattern-contribution-review-2026-10-27.md#7-선택구조-구체화와-추가-검증--1402-후속)이 소유한다. 현행 contract와 실제 정책은 retained이며, 구현/배포/새 날짜 자연 성과는 별도 OPEN이다. 체크리스트의 기존 원 owner·원 창을 유지한다.


## 6. 구현된 계약과 source27 검증 경계

- `reversal_cumulative_registration`에 `cumulative_scoring_contract_v1`과 `chronological_target_first_wilson_v1`을 추가했다. 지정3scope·5개 단일 추가 후보·기존 current를 결속하며 다른 scope는 raw-v2를 유지한다. `prepare-scoring`은 native machine stage와 봉인 population을 검증한 뒤 비승인 준비물만 만든다. `intake-scoring`은 별도 명시 선택 승인, attested parent/CAS, 코드·원천 SHA, 경쟁 등록 요청을 확인한다. 이번에는 운영 intake를 실행하지 않았다.
- `reversal_cumulative_postclose`의 기존 point Store를 사용한다. timestamp/item/route가 맞지 않는 식별 가능한 row는 exact key로 제외하고 나머지 자료를 집계한다. 첫 U/STOP도1800초를 점유한다. raw와 chronological counts·점수·날짜/종목별 결과, 추가/제거 key·자체 추가분을 같은 archive에 남긴다. 큰 key 목록은 full gzip table에 두고 CURRENT/SELECTED projection은 집계만 보유한다. 신규 raw/AI 원장 복제와 provider 호출은 없다.
- `continuous_reversal_policy_v6`는 새 계약·선택 영수증을 후속 manifest에 전달하고, family의 선택 지표/부모/source hash를 확인한다. 새 점수 결과를 기존 raw 지표로 선언한 family 또는 raw 계약에 새 receipt만 끼운 경우를 거부한다. 기존 초기 등록/보조 호환 승계 경로와 hard safety는 유지한다.
- raw replay checkpoint는 기존 코드/원천 identity를 유지하며, 점수 계산은 기존 확인점 객체에서 수행한다. raw checkpoint를 점수 캐시로 사용하지 않는다. score spec/승인 계약/source SHA는 비교 archive의 content hash와 실제 선택 영수증에 결속된다.
- source26의 새 구현 재집계와 앞선 독립 연구의8조합에 대해 W/N/U·선택 key32개 대조가 모두 일치했다. 이는 source27의 독립 검증이 아니다. 실제 source27 machine report와 native machine terminal은14시대에 아직 없었다.
- source27 검증 실행기는 [기존 원장을 읽는 재검증 도구](../../tmp/regular-selection-score-20261027/revalidate.py)다. 동일 source date의 native stage를 원 reader로 검증하고 Store의 partition hash·동결 population·candidate contract를 연결하며 결과를 code hash별 불변 파일로 쓴다. `--source-date 2026-10-27`로 실행하되 자료가 없으면 `source_terminal_not_available`만 기록한다. 실행·판정값을 임의로 채우지 않는다.
- 다음 창은 기존 `MachinePatternOpportunityResearch1023`의10/27 **20:05~23:59**다. source27 종료·적격 partition을 확인한 뒤 동일 정의로 후보5개와 current의 raw/순차 누적·당일 W/S/T/U/L, 추가/제거 WIN, 중가 A08의30분 미달 경로를 비교한다. 결과가 좋더라도 별도 운영 채택/정상 code-policy 인계·배포·실제 PID 소비를 구분한다. 신규 자동 예약은 만들지 않는다.

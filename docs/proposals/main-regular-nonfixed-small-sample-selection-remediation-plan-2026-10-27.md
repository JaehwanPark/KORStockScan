# 정규장 비상시 소표본 완승 고착 보완계획 — 2026-10-27

## 1. 결정·범위

**제안:** 비용을 반영한 WIN/STOP/TIMEOUT 라벨은 유지하고, 기계정책 순위를 `반복 확인점의 단순 승률`에서 `시간 중복을 제거한 누적 승률의 불확실성 보정 점수`로 바꾼다. 추가 패턴이 실패1건 때문에 소표본100% 현행에 영구히 밀리는 문제를 보완한다. 손익비·EV·AI 점수·호가 guard 완화를 순위에 넣지 않는다.

이 문서는 **선택 계약의 변경안과 구현 owner**다. 현행 `cost_bound_cumulative_target_first_fraction`과 구분한다. 후속 구현 지시에 따라 격리 작업본에서 구현·리뷰·검증을 수행했다. 운영 채택·배포는 미실행이다. source27 정규장 연구는 하루 전체 장후 terminal을 기다리지 않고 별도로 검증한 정규장 원천부터 수행했다. 15:36 입력 고정 후 지정5후보의 당일·누적 재검증을 완료했으며 연구 순위는 저가A09·고가A12·중가현행이다. 미확정86점의 동일 item 원천 보강으로75점을 확정했고11점만 제외한다. 저가A09는 당일11/16승·누적113/204승으로 채택을 권고한다. 최신 운영3a 위 불변 후보a1b1b0f8a의 현행 정책 인계·격리기동 PASS이며 정식 A09 게시와 실제 PID 소비는 OPEN이다. [재집계와 운영 준비 §12](../audits/main-regular-nonfixed-pattern-contribution-review-2026-10-27.md)가 최신 상태를 소유한다.

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

현재 자료는 후보 선정에 이미 사용된 자료이므로 독립 holdout이 아니다. source27의 정규장 종료 후 별도 동결·검증한 적격 원천부터 동일 정의로 추가하고 raw/순차/날짜별 W/S/T/U와 L을 갱신한다. 아래 §7의 선행 연구는 하루 전체 native machine terminal을 요구하지 않는다. 이후 기존 장후 창의 정식 세대와 원 key·라벨·원천 차이를 대조한다. source27을 사용할 수 없으면 미완료 이유를 원 owner에 유지하고 다른 날을 미래 검증처럼 대체하지 않는다. 현재 연구만으로 live 후보를 승인하지 않는다.

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
- source27 **정식 장후 세대** 검증 실행기는 [기존 원장을 읽는 재검증 도구](../../tmp/regular-selection-score-20261027/revalidate.py)다. 동일 source date의 native stage를 원 reader로 검증하고 Store의 partition hash·동결 population·candidate contract를 연결하며 결과를 code hash별 불변 파일로 쓴다. `--source-date 2026-10-27`로 실행하되 자료가 없으면 `source_terminal_not_available`만 기록한다. 이 실행기의 입력 조건은 아래 정규장 선행 연구의 필수 조건이 아니다. 실행·판정값을 임의로 채우지 않는다.
- 다음 창은 기존 `MachinePatternOpportunityResearch1023`의10/27 **20:05~23:59**다. source27 종료·적격 partition을 확인한 뒤 동일 정의로 후보5개와 current의 raw/순차 누적·당일 W/S/T/U/L, 추가/제거 WIN, 중가 A08의30분 미달 경로를 비교한다. 결과가 좋더라도 별도 운영 채택/정상 code-policy 인계·배포·실제 PID 소비를 구분한다. 이전 구현 단계에서는 신규 자동 예약을 만들지 않았다. 후속 사용자의 source27 생성 후 계속 실행 지시에 따라 동일 owner의 단회 연구 대기 프로세스를 준비했다. cron/systemd·운영 dispatch 변경 없이 같은20:05~23:59 창에서만 실행하며, [원52건 추가 대사·동결 protocol·리뷰](../audits/main-regular-nonfixed-pattern-contribution-review-2026-10-27.md#9-source27-조건부-재검증과-원-무수신52건-추가-대사--1513)를 따른다.

## 7. 정규장 종료 후 선행 연구 — 15:36 정정

정규장 비상시 연구를 AFTER 종료까지 일괄 대기시킨 것은 연구 실행기를 하루 전체 native machine terminal에 연결했기 때문이다. 연구 목적 자체의 요구가 아니다. **정규장 source-only 동결 → 해당 구간 검증 → 지정 후보 재생**을 먼저 수행하고, 정식 장후 세대는 이후 원천/라벨 차이를 대조하는 별도 단계로 둔다. 운영 등록의 native stage 요구는 유지한다.

- 입력은 `2026-10-27/SOR/SOR_REGULAR` 하나의 partition이다. 기존 `freeze_normalized_sources`의 완성 행 prefix hash·원 inode/절단 검사·native closed-epoch 검증을 재사용했다. PRE/AFTER 파일은 입력 참조 트리에 포함하지 않는다. 원 raw는 복제하지 않고 별도 정규화 gzip 약4.4MB만 만들었다.
- native 원천 종료 검증을 통과한 epoch만 유효 처리한다. 15:36 기준 비상시 적격 행은 저가21,120·중가16,841·고가8,512이며 부적격13,350행은 계산에서 제외한다. 이는 체결 관측 행 수이고 독립 기회/승패 건수가 아니다. 고정된 원천은 [분리·검증 영수증](/home/ubuntu/KORStockScan/tmp/regular-selection-score-20261027/regular-only-feasibility/feasibility.json)을 따른다.
- 마지막 raw 체결은15:17:43.168이다. 정규장 종료 시각까지 완전 수신했다고 표시하지 않는다. 각 정확 item/epoch/sequence별 연속 경로에서30분 내 WIN/STOP이 먼저 확정되면 그 결과를 쓰며, 목표·손절 어느 쪽도 관측하지 못하고30분이 부족하면 U다. 장말 구간 전체를 일괄 BLOCK/FAIL_TIMEOUT으로 바꾸지 않고 AFTER의 다른 session/route 가격을 붙이지 않는다.
- 다음 계산은 동결한 원 current와 저가A05/A09·고가A12/A14·중가A08의 동일 정의를 사용한다. source26까지의 검증된 기존 객체는 재사용하고27일분만 추가한다. 당일/누적 raw·순차 W/S/T/U/L과 추가/제거 WIN을 구분한다. 완성봉 보강이 필요하면 같은 item·정규장 시간창·고정 revision과30분 도달 순서 검증을 통과한 것만 별도 출처로 사용한다.
- 이번 요청에서 **정규장 입력 분리·검증 및 선행 연구 가능 여부 확인을 완료**했다. source27 후보별 승패 재집계는 아직 실행하지 않았으며 운영 채택은 OPEN이다. 기존20:05 대기 프로세스와 동결 protocol은 정식 장후 세대 검증용으로 보존했다. 해당 프로세스의 대기 상태를 정규장 연구 전체가 불가능하다는 뜻으로 사용하지 않는다.

## 8. 지정5후보 재검증 완료와 적용 판단 — 15:52

§7 뒤 사용자의 즉시 실행 지시에 따라 source27 정규장 분리 입력으로 재생을 완료했다. 이전 원장 전체를 다시 만들지 않고 source26까지의 검증된 집계와 당일분을 날짜별 통계 계약으로 합쳤다. 새 날이 이미 포함된 집계는 거부한다. source26의6종목157확인점은 native producer의 원 key·입력 특징·라벨과 일치했고 당일 통계 확인점93개의 exact item/epoch/sequence/ask·원 후행 경로도 재검증했다. 신규 provider 호출은0이다.

| 후보(현행∪단일 추가) | 당일 W/N · U | 누적 W/N · U | 누적 점수 L | 다음 판단 |
|---|---:|---:|---:|---|
| 저가 A05 |0/1 ·9|36/63,57.1% ·59|44.86%|A09 대비 후순위. 당일 손절1 추가 |
| 저가 A09 |1/1 ·20|103/189,54.5% ·133|47.38%|저가 우선 적용 검토 후보. 당일 확정 승리1 추가 |
| 고가 A12 |0/0 ·1|12/20,60.0% ·18|38.66%|누적 연구 순위 유지. 당일 효과는 미확정 |
| 고가 A14 |0/0 ·10|13/29,44.8% ·33|28.41%|A12 대비 후순위. 당일 효과는 미확정 |
| 중가 A08 |5/5 ·46|171/539,31.7% ·405|27.94%|현행 유지. 당일5승만으로 누적 미달을 뒤집지 않음 |

분모N은 WIN+STOP+TIMEOUT이며 U는 별도다. 당일 고정 현행 규칙의 재생 확인점은3유형 모두0이며 이는 운영 전체 이벤트 건수의 주장과 다르다. 당일 확정7점만으로1/1·5/5를 일반화하지 않는다. U86은 종목 원 경로 종료75·collector epoch 전환9·다음 행 부적격2이고, 보관된23개 완성봉 원천에도 해당86점의 동일 item 자료가 없었다. 원천을 보강하지 않은 채 U를실패/승리로 채우거나 새로운 최소 표본·승률 문턱을 붙이지 않는다.

15:52 실제 선택 릴리스d5ddc0ae0의 활성3scope는 동결 비교 현행과 일치했다. 해당 릴리스에는 새 점수 코드가 없고, 활성/대기 scoring 계약도 없다. 따라서 연구 추천은 완료했으나 이 산출물만으로 즉시 운영 적용된 상태는 아니다. 저가A09는 다음 명시적 선택/등록·검토본 통합 배포의 우선 후보로 제안한다. 고가A12는 누적 후보를 유지하되 새 날짜 효과 미확정을 명시한다. 중가A08은 적용하지 않고 원 현행을 유지하는 결론이다. 기존 native 등록 경로의 정식 원천·부모/source/code 결속은 유지하며, 이 요건을 선행 연구 금지 조건으로 되돌리지 않는다.

후속은 기존 owner에서 (1)86미확정 exact item의 정규장 후행 원천 보강 가능 여부,(2)정식 source27 세대의 동일 key/라벨 차이,(3)채택할 범위의 승인된 선택 계약·부모 인계/배포·실제 PID 소비 순서다. AFTER로 시장을 바꾸거나 정규장30분을60분으로 확대하지 않는다. 수치·추가/제거 승리·검증 및 남은 조건은 [검토서 §11](../audits/main-regular-nonfixed-pattern-contribution-review-2026-10-27.md#11-정규장-5후보-당일누적-재검증-완료--1552)을 따른다.

## 9. 원천 보강 후 A09 단독 준비와 완료 경계 — 17:16

[최신 실행 결과 §12](../audits/main-regular-nonfixed-pattern-contribution-review-2026-10-27.md)를 기준으로 원 U86 중 WIN32/TIMEOUT42/STOP1을 확정했고 잔여11은 중간 결손5·종료 부족3·clock 충돌3으로 제외했다. A09의 누적113/204승(55.4%)·L48.53%가 현행2/2의 L34.24%와 A05의44.77%보다 높아 저가 단독 채택을 권고한다. 고가A12의 당일0/1과 중가A08의 누적187/581은 이번 적용에 포함하지 않는다.

구현은 `prepare-scoring --scope 'other_non_fixed|REGULAR|LT_20000|SOR' --candidate A09`로 후보를 고정하고 전체128개 부모 구성을 결속한다. 부분 계약은 `carry_parent`가 필수이며 나머지127개 범위는 자동 재선택하지 않는다. 현행 보조정책·hard guard·route·자금·수량·주문 제한을 변경하지 않는다. 새 최소 표본/EV/기존 WIN 보존 gate를 추가하지 않는다.

최종 코드 `a1b1b0f8a54aaad8b1ac5546824329b4e958cdd8`는 최신 운영 `3a989b283446805cf5c2e5523b9d986228175b1a`를 통합했다. native complete dependency profile과 독립 preparation reader의 첫 결손을 수리해 현행 정책 신호569건 parity·정책 인계·격리 P5가 통과했다. A09의 private native family/보조 입력29건 검증도 통과했지만 정식 A09 정책 P5나 actual PID 소비로 대체 표시하지 않는다. 저장 제안은 미승인 상태이며 pending/active pointer에 쓰지 않았다.

[최종 준비 JSON](/home/ubuntu/KORStockScan/tmp/regular-selection-score-20261027/a09-preparation/readiness-review.json)의 남은 조건은 source27 native machine terminal→저가A09 exact prepared-scoring→명시적 채택/배포 지시→native intake/변경된 직접 의존 stage 재생성→실제 A09 정책 인계/P5→ordered transition/정확 PID 소비다. 실제 terminal 이전에 정규장 연구를 대기시키지 않으며, 게시를 위해 하루 전체 terminal을 조작하거나 옛 receipt를 재사용하지 않는다. 코드만 배포할 경우 현행 정책 유지 범위의 준비는 완료했다.

기존 `MachinePatternOpportunityResearch1023`에서20:05~23:59 source27 대조와 다음 영업일2026-10-28 09:30~10:00 REGULAR/SOR/_AL 자연 수용을 이어간다. 원 실패·이전 후보·running waiter·source26 근거는 실제 소비자가 있어 보존한다. 실행 결과를 이유로 원 소표본 규칙 외의 임의 제약이나 새 스케줄을 추가하지 않는다.

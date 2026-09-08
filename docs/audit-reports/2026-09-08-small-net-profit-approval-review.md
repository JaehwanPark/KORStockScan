# 작은 순이익 반복 목표: 승인 기준 재설계·완료 작업 재점검

기준: 2026-09-08 KST. 요청 범위는 승인 기준 구현과 기존 상세검토 완료 작업의 허들 재점검이다. 장후 전체 모니터링 실행 지시가 아니며 주문·봇 재기동·운영 env·operator lock·provider·수량·안전 한도를 변경하지 않는다.

## 판정

후속 상태: 아래는 첫 Daily 보완 시점의 기록이다. 당시 남겨 둔 #49 고정 +0.10%p 문턱과 Daily 한 주기 지연은 [1~3 후속 구현 리뷰](2026-09-08-scanner-daily-net-approval-followup-review.md)에서 보완한다. 이 문서의 당시 테스트·실측 이력을 새 자연 성과로 바꾸지 않는다.

Daily threshold의 `score65_74_recovery_probe` 자동승인에서 **CF EV 2%, 10분 close 1%, MFE 2%, 제출 drought**의 결합 조건을 제거했다. 다른 고정 수익률로 치환하지 않고 실제 적용 profile의 비용 차감 실현손익과 반복성으로 평가한다. 이는 기존 profile의 승인/유지 판단 개선이며 최적 entry threshold·exit target의 자동 탐색 구현은 아니다.

승률이나 매수 횟수를 최대화하지 않는다. 손실을 포함한 순EV·원화 순이익이 양수인 상승/반등 진입 기회를 반복하는 것이 목표다. 실제 매수가·매도가에 슬리피지가 이미 반영되어 있으면 수수료·세금 차감 후 슬리피지를 또 빼지 않는다. 미체결 CF의 비교비용을 실제 체결 비용으로 취급하지 않는다.

## 구현된 승인 계약

| 구분 | 현행 구현 | 유지 이유/경계 |
|---|---|---|
| 경제성 | 같은 profile·venue/session의 완전체결 최종 청산 순수익률 평균 > 0, 평균−2 표준오차 > 0, 순손익 합계 > 0 | 고정 2% 목표 없음. 분산 여유는 견고성 검사이며 독립 표본의 신뢰구간이나 수익 보장으로 주장하지 않음 |
| 반복성 | 기존 20건 floor 유지, 최소 2개 실제 거래일; primary는 최근 20 KRX 거래일 | 5일 내 큰 수익을 요구하지 않음. 승률·일별 전승·최소 매수 횟수는 승인 조건 아님 |
| 빈도/자본 효율 | 관측 거래일당 건수, 유효 source 일수당 완료 건수/순이익, 자본 점유시간당 순이익 표시 | 거래 0일을 포함한 빈도를 별도 표시. 이 지표를 아직 다른 exit 정책 최적화 성과로 해석하지 않음 |
| 손실·부분체결 | 모든 full-only 손실 포함. partial을 별도 장부로 보존하고 관측 partial 합계 손실은 승인 거부 | partial을 full 분모에 합치거나 유리한 full-only 결과만으로 손실을 숨기지 않음. partial 최소 20건을 별도 의무로 만들지는 않음 |
| 원천 | exact lifecycle, 실제 주문/체결/최종 청산, 금액·비용 대사, 날짜·자기해시·source generation, 정책/시장 구간 일치 | 비용 결손·미청산·mixed scale-in·과거 비승격 복원 자료는 승인 근거 제외 |
| 불필요한 원천 문턱 | 실현손익에 불필요한 AI replay BBO95%/depth90%, scanner 노출시간, 명시적 NO_ADD 및 별도 slippage basis 조건은 분리 | 실제 체결가/비용/공식 체결시간·주문 식별·수량 대사와 source guard는 유지. AI replay 자체 승격 조건은 변경하지 않음 |
| 적용 | Daily/cumulative와 PREOPEN이 같은 판정 함수를 사용. 적용 시 기존 5개 profile 값과 활성화 값을 모두 전달하고 승인된 시장 구간을 버전에 고정 | 미승인 venue/session·다른 profile에는 새 자동승인 버전으로 진입 불가. 실제 주문 전에 기존 상승/반등 및 hard safety를 그대로 재검사 |
| 운영 override | 기존 lock의 별도 권한·기존 version 유지 | 오래됐거나 새 표본이 없다는 이유로 override를 해제하지 않음. 이번 변경을 전체 매수 차단으로 해석하지 않음 |

신규 공통 계약은 `src/engine/scalping/score_recovery_economics.py`가 소유한다. 실전은 신규 source-only `score_recovery_real_economics_observed` event에 당시 실효 profile을 기록하고 기존 lifecycle writer의 exact identity를 사용한다. 과거 `score65_74_recovery_probe` event를 새 필수 lifecycle stage로 재해석하지 않는다. 최종 paired producer는 실제 매입/매도 금액과 profile을 보존한다.

Daily의 현재 profile은 검증된 동일 거래일 PREOPEN env를 우선한다. 장후 process의 기본 설정과 실전 override 설정이 달라 영구적으로 표본이 불일치하는 경로를 방지했다. PREOPEN은 KORSTOCKSCAN 이름의 실제 runtime env로 전체 profile과 scoped version을 전달한다. profile 숫자를 이 패치가 새로 최적화하거나 확대하지 않는다.

### 자동화 순서와 성과의 구분

`실전 source-only 계측 → 기존 Main AI materialization의 lifecycle paired producer → Daily 20거래일 집계 → 기존 AI 검토/장전 guard → PREOPEN env → 런타임 scope 재검사`로 연결한다. 수동 env 작성이나 별도 매번 사용자 승인은 추가하지 않는다.

현재 wrapper에서 lifecycle paired owner는 Daily보다 뒤에 실행된다. 따라서 Daily는 이전까지 완료된 paired 날짜를 사용하며, 당일 paired가 아직 없으면 정상 source 대기로 표시한다. 새 장후 자료가 **다음 Daily에 편입되는 한 번의 장후 주기 지연**이 있다. 당일 paired를 당일 Daily가 이미 반영했다고 주장하지 않으며, 중복 heavy producer나 전체 wrapper 재실행은 추가하지 않았다.

9/7 기존 paired 원천에는 이 변경의 당시 profile metadata가 없다. 이를 추정 복원하거나 CF로 대신 승인하지 않는다. 기존 9/8 apply plan의 operator override도 덮어쓰지 않았다. 신규 source는 수정 코드가 다음 정상 매매 process에 로드된 이후부터 확인할 수 있다. 해당 자연 확인은 `DailyThresholdNaturalAcceptance0908`을 유지한다. OFF 상태이고 유효한 과거 applied 표본도 없다면 이 경로는 최초 실전 권한을 스스로 만들지 않는다. 무한 대기 대신 20개 유효 source 거래일 내 `profile 없음/매매 없음/체결 없음/청산·비용 결손/양수 edge 없음`을 구분해 유지·통합·폐기 재판정한다.

## 상세검토 완료 작업 재점검

아래는 승인 문턱의 목적 부합성 재점검이다. 과거 완료 표시를 실제 수익개선 완료로 바꾸지 않는다. #75 Entry split 등 inventory의 `상세검토 대기`를 완료 작업으로 포함하지 않는다.

| 완료 검토 영역 | 확인한 현재 조건/역할 | 재판정 |
|---|---|---|
| #1~5 격리·snapshot·compact | 실행 원자성, freshness, resource/source 계약 | 경제성 문턱 아님. 안전/오염 방지 조건 유지 |
| #6~11, #21 원천·missed·workorder·SQ | source-only 진단·원천 격리·stable ID | 양수 EV나 실체결을 진단 완료 조건으로 추가하지 않음. retired/sim 결과에 live 권한 부여 안 함 |
| #12 PYRAMID | 동일 complete episode의 candidate-current 순기여 > 0 및 candidate 순기여 > 0, 다음 step eligible 20 | 작은 양수 개선 허용. `min_profit_pct=1.5`는 비교 대상 전략값이지 개선폭 1.5% 요구가 아님 |
| #13 AVG_DOWN | paired 10, current 대비 순EV/원화 개선 > 0; ADD 제거형은 NO_ADD와 동률 가능 | 고정 큰 개선폭 없음. loss suppression만 유리하게 보이지 않도록 같은 universe 유지 |
| #14 Samsung / 21:15 timing | notional uplift 0.005%p; fixed20/5일, dynamic8/5일; 실제 quote/깊이·지연 가능성·같은 episode 비교 | 2% 급 절대 문턱은 아님. 9/7 ingress loss는 표본 수를 낮춰도 해결되지 않는 source 결손. 새 exact source로 확인; 낮은 빈도/최신성 경계는 자연 owner에서 기간 한정 점검 |
| #15~16 저가주·확장 추천 | applied 정책 carry/동일기간 net EV 비교, subset은 진단; 별도 사용자 승인 적용 ledger | source-only 연구를 자동 실전 승인으로 오인하지 않음. 큰 공통 EV floor를 신규 적용하지 않음 |
| #23 Entry recheck / #119 BUY Funnel | 고정 profile의 시장별 drought 제어, exact attempt/full-position net, 3거래일 history | drought는 이 제어기의 목적 자체다. Daily의 일반 경제성 승인에서 제거한 drought를 여기에 일괄 삭제하지 않음. 누적 sweep는 on-demand 유지 |
| #27 microstructure reaction context | finite 20건은 전달/결과 진단 기준, PREOPEN 승격 N/A | 20건·양수 EV를 실전 context 전달의 새로운 필수 문턱으로 만들지 않음 |
| #45 panic breadth / 반등 재진입 | same-owner A0/A2, 누적 0.005%p 및 rolling/holdout 양수, 5일·실행가능 quote/source | 작은 개선과 약세장 노출 위험의 균형. 무조건 매수로 전환하거나 quote·venue/cost guard 완화 안 함 |
| #47 scale-in split | paired3/2일, 순EV > 0, 실제 outcome+동일 가격경로·참여율/하방 guard | 큰 절대 수익률 없음. 이름이 MFE/MAE floor여도 실제 price-join 3건이며 replay 입력 조건. 무관한 모든 horizon 수익률 목표로 해석하지 않음 |
| **#49 Scanner lookup-attention** | base와 독립 holdout 각각 완료20/5일·군별10/3일, **각각 uplift≥0.10%p**. 별도 marginal pair3/2일 | **추가 보완 검토 필요**. 고정 0.10%p는 작고 반복적인 양수 증분을 차단할 수 있음. 독립 holdout·실제 full fill·tail guard는 유지하되 고정 개선폭을 분포/불확실성 기반으로 대체 검토. 이번 변경은 이 family 정책을 수정하지 않음 |
| #50/51/54 Daily·AI correction·누적 | 위 재설계 적용, exact real book/20거래일, eligible 후보만 기존 AI 검토 | 절대2%/10분/drought 제거. source/AI 검토/PREOPEN/PID/실수익 상태는 분리 |
| #76~82 중 완료된 연결부·R0–R3/optimizer/calibration | 지속 offline prompt/input 연구와 partial-success learning; 실제 live owner/등록·승인은 별도 | offline 연구를 큰 live floor 때문에 정지시키지 않는 분리 유지. legacy #81 OFF는 높은 표본 문턱이 아니라 권한 폐기 상태. 신규 current-axis 활성화는 별도 OPEN owner |
| #17~20 사본, ADM/LDM·bucket·incremental CF 독립 단계 등 폐기 영역 | 단일 owner 이관 또는 RETIRED | 허들을 낮춰 복구하지 않음. surviving helper/owner만 유지 |
| 기타 이미 검토한 verifier/controller/tower/receipt 연결 | target-date·hash·최신 terminal 및 권한 검사 | 운영 성공과 전략 수익 분리 유지. strict source hash를 수익률 문턱으로 오인해 삭제하지 않음 |

코드 근거: `scalping_pyramid_quality_calibration._profit_grid_decision`, `scalping_avg_down_recovery_calibration._positive_economic_improvement`, `machine_entry_timing_policy.py`, `machine_rebound_reentry_policy.py`, `scale_in_split_order_plan.py`, `scanner_lookup_attention_policy.py`, `ai_action_outcome_calibration.py`. #49 고정0.10%p는 producer·policy validator·post-apply 판정에 함께 남아 있어 한 곳만 낮추면 안 된다. 다음 보완 판단은 기존 `ScannerLookupAttentionNaturalEvidence0908`에서 exact base/holdout 분포와 연결해 추적한다.

## 검증 및 남은 상태

- 합성 실체결 계약 20건/2일, 건당 순이익30원/매입금액50,000원(0.06%)은 Daily→PREOPEN 공통 판정과 scoped runtime version 검사를 통과한다. 실제로 이 수익이 발생했다는 뜻이 아니다.
- 다수 소액 이익 뒤 큰 손실, 양수 평균이나 분산 여유 미달, partial 손실, CF-only, 비용 결손·중복 slippage 차감, mixed scale-in, 미청산, policy/venue/date/hash 충돌, 과거 baseline 자료는 승인되지 않는 반례를 검증한다.
- 실제 lifecycle producer fixture에서도 새 scalar profile을 보존하고 매입50,000/매도50,050/비용20/순이익30을 대사한다. 추가 slippage5를 또 차감하지 않는다.
- 운영 report 재생성·PREOPEN 실행·봇 재기동·주문·lock 변경·commit/push는 수행하지 않았다.

### 최종 review gate

- `korstockscan-review-gate`로 producer→Daily/cumulative→AI/장전→runtime 소비와 authority 경계를 반복 검토했다. 처음 발견한 scalar metadata 누락, legacy stage 재해석 위험, 잘못된 source gate 필드명, 장후 기본값/실전 profile 불일치, 환경변수 prefix, CF 기반 이전 enable 추천 잔여, full/partial 손실 누락, 잘못된 metric shape·None parent의 실패 전파를 수정하고 재검증했다.
- 11개 관련 test module 1차 **1,076 PASS / 34.12초**, 직접 lifecycle producer 호출을 소유하는 Main AI cycle 회귀 **188 PASS / 2.41초**. 이후 원 미만 대사 오차로 0/손실을 양수로 바꾸지 않는 보수적 net 산식과 35번째 신규 회귀를 추가했다. 최종 12개 module 동시 재검증은 **1,265 PASS / 35.16초**다. pandas_ta의 기존 pandas Copy-on-Write deprecation warning 1종은 패키지 변경 없이 남겼다.
- Black, 신규 helper/test Ruff, 변경 Python compile, `git diff --check`를 확인했다. 전체 저장소의 무관한 테스트·실제 Provider 평가·실매매 검증은 수행하지 않았다.
- print-only 문서 parser가 성공했고 `DailyThresholdNaturalAcceptance0908`와 `ScannerLookupAttentionNaturalEvidence0908`가 각각 현재 9/8 checklist에서 정확히 한 번 검색됐다. 전자의 구 9/7 OPEN은 완료로 바꾸지 않고 이관 이력으로 보존했다. 외부 Project/Calendar sync는 실행하지 않았다.
- 9/7 실제 paired 파일을 새 helper로 읽기 전용 확인한 결과 source 자기해시/날짜 계약 유효, 신규 profile 결속 full/partial 각각0건, 판정 `hold_sample/real_applied_evidence_missing`이다. 검증된 9/8 PREOPEN profile은 score69~74, buy-pressure65, tick1.2, 실효 micro10bp로 읽혔다. 새 순이익 승인이나 실제 수익 증가를 주장하지 않는다.
- **이번 Daily 승인 재설계 구현 범위의 미해결 코드 finding 0**. 자연 source·실제 PREOPEN/PID 소비·수익 수용은 OPEN이다. 재점검으로 식별한 #49 고정 개선폭의 보완 판단은 별도 미종결이며 이 finding 0에 포함하지 않는다.

코드/계약 보완, 자연 source 생성, PREOPEN 선택, PID 소비, 실제 순수익 개선은 별도 상태다. #49의 새 허들 finding은 이번 Daily 구현 범위의 finding 0으로 닫지 않는다.

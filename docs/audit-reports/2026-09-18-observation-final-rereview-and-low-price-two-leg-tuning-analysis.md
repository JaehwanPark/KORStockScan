# Final source-quality 재리뷰 및 low-price two-leg actual 튜닝 분석

사용자 승인 범위: final 감사의 리뷰/보완, commit/push/배포 재확인 및 불필요 과거 산출물 정리. `monitoring.low_price_two_leg_tuning`은 읽기 전용 분석이며 코드·정책·표본 기준을 변경하지 않았다. Source9/17, publication9/18, 기존 prepared effective9/21을 구분한다. Bot restart, 주문, 조기 PREOPEN, 전체 native/raw 재실행은 실행하지 않았다.

## Final 감사 재리뷰·정리 결과

[기존 Q0–Q5 owning review](2026-09-18-observation-source-quality-final-lineage-review.md)의 검증 source `35947abb64e8c920424c56670544e4fab19ffe5e`에서 producer→final binding→trigger/wrapper→source gate→summary/tower/checklist→compact consumer를 재확인했다. 변경된 계약이나 추가 코드 결함은 확인되지 않았다. 기존 완료 리뷰를 재구현하지 않고 phase/consumer 변경 감지, raw 의미 digest, 대형 funnel projection, final의 raw bootstrap 금지 회귀4개를 재실행했다: **4 PASS**. 앞선213/488/126/251/18 검증은 동일 source의 원 receipt를 재사용하며 합산하지 않는다.

새 산출물 결함은9/17 `.reuse-contract.json`이 이전 artifact SHA `b9f66a…`를 가리키고 현재 final JSON의 SHA `c36104…`와 다른 것이었다. 이는 generic wrapper의 구형 재사용 영수증이며 현재 `.final-contract.json`과 별개다. Exact 원본이 기존 조사 `original/`에 보존돼 있음을 byte 비교하고, active writer 부재와 native generation lock 획득을 확인한 뒤 구형 영수증 **1개/1,268 bytes 삭제**했다. 정상 wrapper의 `wait_for_report_artifact`는 현재 publication의 generic 영수증을 다시 작성한다. Pure final reusable check와 역할별 소비는 삭제 전후 모두 정상이다.

9/14–9/16 final JSON/MD/reuse 영수증은 rolling actual history, 기존 정책 provenance 및 rollback에 필요하므로 보존했다. Current final JSON/MD/binding, raw generation, low-price 후보·applied policy 전체 SHA는 정리 전후 동일하다. 기존 raw/signed ledger/funnel·original 조사 증거·generation lock·managed release를 삭제하지 않았다. Cleanup 요청을 전체 역사 제거로 확대하지 않았다.

현재 final은 source input allowed=true, operational reconciled=false, economic eligible=false, EV=null이다. 과거 PASS4의 terminal gap4는 원천 미복구로 남는다. Compact9/21 정책은 기존 incumbent carry이며 신규 EV 개선 정책이 아니다. Whole strict/controller는 기존 선행 실패·AI correction·저가주 dated native artifact·machine timing·Swing/research loop 등 외부 owner 때문에 DONE=false다. 감사의 코드 closure와 전체 장후 완료를 분리한다.

Receipt: `tmp/observation-final-rereview-low-price-20260918/{review,cleanup,low-price-readonly-analysis,consumer-verification-before-docs,deployment}.json`, `targeted-tests.txt`, `parser.txt`. 원 Q0–Q5 결과와 policy9/21은 `tmp/observation-source-quality-20260918/`의 as-of receipt를 따른다. 이번 문서 commit은 source/deploy 변경이 없으며 기존 immutable reviewed source를 유지하고 push/배포 재확인 receipt를 갱신한다. 실제 PID·자연 정책 소비를 새로 증명한 것은 아니다.

## `monitoring.low_price_two_leg_tuning`의 의도와 실행 경로

선택 release의 `src/engine/monitoring/low_price_two_leg_tuning.py`는 실제 저가주 두 leg 전략의 profile별 state·broker receipt·완료/보유 상태와 자기 과거 보고서를 집계한다. 시장 가격 이력을 재조회하거나 미진입 가상 거래를 만들어 평가하는 작업이 아니다. Target price proxy, 실제 broker sell fill, 수동 청산, full/partial fill 및 exact 비용/추정 비용을 구분한다.

Current applied policy와 의미가 같은 **연속 적용 구간 `post_apply_version`**을 평가한다. 전체 버전/다른 profile을 후보 승격 표본으로 합치지 않는다. 일별 순익의 주 지표는 `cost_adjusted_net_profit_krw_per_source_valid_observation_day`, 보조 지표는 notional EV·시도 빈도·자본 점유/시간이다. 정상 관측 무거래 날짜와 원천 결손 날짜를 구분하고 미관측 날짜를0으로 채우지 않는다.

현재 drawdown·near-low 두 진입 필터를 더 엄격하게 했을 때의 **관측 실적 부분집합**을 최대2개/profile 평가한다. 진단 조건은 후보 관측5일·완료 및 broker 가격 완료8 leg, inventory clear, 양수 후보 EV, 기존 대비 EV uplift0.005%p 이상과 일별 순익 차이>0 등이다. 그러나 `ready=False`, `allowed_runtime_apply=False`이며 선정은 항상 `carry_forward_profile_policy`다. 이 작업에서 부분집합의 신규 조건 승격은 명시적으로 폐기돼 있다(`carry_actual_policy_subset_promotion_retired`). 이는 우연한 선정 버그가 아니라 잘못된 인과 추론을 막는 권한 경계다.

기존조건을 거부했다면 이후 진입 시점·주문·재고·청산·자본 가용성이 달라진다. 실현 거래 일부를 삭제하는 방법은 그 경로를 재구성하지 못한다. Economic replay owner는 별도 `low_price_two_leg_expanded_candidate_research`의 `existing_axis_economic_replay`로 기록돼 있으며 source-only다. 그 연구 결과/holdout과 실제 tuner 결과를 하나의 비교 성공 건수로 합치지 않는다.

Runtime 연결은 구현돼 있다: actual report→dated candidate→`automation.low_price_two_leg_policy_apply`→exact-date applied artifact→`src/trading/low_price_two_leg/service.py`의 `load_applied_profile_policy`→machine profile. PREOPEN consumer는 candidate date/age·source files·policy/hash·owner/guard 계약을 검사한다. 서비스는 live 권한과 exact-date applied policy가 유효한 경우에만 broker gateway를 구성한다. **현재 소비 가능한 산출물은 기존 정책 보존 결과이며 신규 부분집합 조건은 전달하지 않는다.**

## 확인한 실제 산출물과 EV 현황

Latest actual report/candidate source는 **2026-09-16**이다.9/17·9/18 dated actual 보고서 및9/17 후보는 존재하지 않는다.9/17 strict의 schema/date/hash/profile/authority 오류들은 해당 날짜 native source가 없는 상태를 반영하므로9/16 정상 보고서가 전부 손상됐다고 해석하지 않는다. 누락 artifact의 최초 실행 중단 원인은 이번 bounded 분석으로 확정하지 않았다. 현재 controller는 upstream repair가 필요하다고 기록하며 완료 상태가 아니다.

대형9/16 JSON82,683,428 bytes는 전체 객체를 적재하지 않고 기존 MD, 작은 candidate 및 필요한 top-level section을 streaming으로 읽었다. 다음은 **9/16 보고서에 포함된 profile별 현재 적용 구간** 합계이며 하루 실적이 아니다.

| 확인 항목 | 결과 | 해석 |
|---|---:|---|
| Profile |61개 |58 pass,3 gap; gap3은 현행 비용 재검증에 따른 명시적 runtime 제외 profile과 일치 |
| 시도 episode / 완료 leg |139 /80 |두 leg와 episode는 서로 다른 분모 |
| 미청산·미해결 leg |16 |평가 cutoff의 재고/불확실성; 손익0 또는 전부 확정 손실로 대체하지 않음 |
| Broker 가격 완료 |80 leg |Exact 비용 완료10, 고정 왕복비용0.23% 추정70 |
| EV 표시 profile |32개 |양수29, 음수3, 나머지29 null; 신규 조건의 개선 실적이 아님 |
| 수동 청산 / 그중 손실 |8 /7 leg |실제 손실을 보존하며 machine target 성공과 분리 |
| 관측 기간 coverage |26/72 거래일 |Profile 운영 시작 전/미관측 포함;46일을 자동 결손·무거래0으로 해석하지 않음 |
| 진단 대안 |118개 |hold_sample97, hold_inventory_custody16, hold_source_quality5 |
| 진단 경제조건 통과 / 신규 정책 선정 |0 /0 |승격 권한은 결과와 무관하게 꺼져 있음 |

Current 정책 구간의 accounting 합계는 완료 매입 notional35,861,050원, 비용 후 순익 **22,257.107원(정확 비용·추정 비용 혼합)**이다. 이는 각 profile의 서로 다른 적용 구간을 합산한 감사용 값이며 공통 전략 EV·일평균 순익·후보 개선 Δ가 아니다. Held16을 포함한 전체 경제성이나 동일 정책 대비 우위를 증명하지 않는다. Exact10개는 역사에서 유지된 대사 결과이며, 최신 report의 reconciliation `api_requests=0/matched=0`과 모순되지 않는다.

음수 profile은 삼성E&A 오후−1.627206%, 한국전력 오전−0.526924%, NHN 늦은 오전−2.500816%다. 모두 broker 가격/비용 계약에 따른 현재 보고서의 notional EV이고 미래 수익 예측이나 청산 권고가 아니다. 수동 청산 손실을 제거해 수익성을 높여 표시하지 않는다.

9/18 applied artifact는 존재하며 source9/16, selection=`candidate_applied`, 정책 변경0, policy hash `590642d99e263254fc10663b01f62966d6461f78a63a4574998115296a738ebb`다. Read-only `validate_applied`와 카카오 늦은 오전 profile loader는 valid/ready를 반환한다. 따라서 파일 전달 경로는 존재한다. `candidate_applied`는 보존 정책이 적용 파일로 발행됐다는 뜻이며 튜닝 수익 개선이나 실제 주문/PID 소비를 증명하지 않는다.9/21 low-price exact-date applied 파일은 아직 없으며 정규 PREOPEN 전 부재 자체를 결함으로 집계하지 않는다.

## 시간 경과로 개선 가능한 부분과 구조적 문제

| 구분 | 현재 상황 | 해소 조건 / closure |
|---|---|---|
| 표본 미성숙 |대안97개 hold_sample; 현재 구간 broker 완료8 leg 이상 profile도1개뿐 |실제 유효 체결·완료와 정책 구간이 유지된 관측 누적. 날짜만 지나거나 다른 profile 합산으로 통과하지 않음. ETA 미정 |
| 재고·terminal 미성숙 |대안16개 custody 보류, 관측 cutoff 미청산·미해결16 leg |자연 체결/청산 및 exact owner·terminal receipt 대사. 장시간 보유가 자동 timeout/no-fill로 바뀌지 않음 |
| 비용 증거 부족 |완료70개는 고정0.23% 추정 |유일한 symbol/day/수량/매입·매도 평균가와 commission/tax 대사. 미래 거래는 개선 가능하지만 과거 데이터 부재는 시간만으로 복구되지 않음 |
| Intentional 제외 |비용 재검증 제외3 profile, 진단 quality 보류5개 |기존 quarantine release contract 및 별도 승인된 새로운 독립 경제성 증거. 체결 표본 증가만으로 해제하지 않음 |
| Dated native 미생성 |9/17 actual report/candidate 없음, strict 소비 미완료 |기존 native owner의 선행 상태/실행 receipt를 식별하고 제한 복구·동일 날짜 마지막 소비 검증.9/16 artifact를9/17로 재봉인하지 않음 |
| 인과 비교의 한계 |실제 거래 부분집합은 이후 entry/재고·기회비용을 재현하지 못함 |기존 replay owner에서 동일 입력·예산·청산·비용의 서로 다른 정책 paired 경로와 미사용 holdout 검증. 단순 누적으로 해결되지 않음 |
| Source admission 검증 약함 |actual tuner `_source_quality_preflight`는 파일명의 날짜와 flags/status/SHA를 사용하나 내부 target_date/report_type/final freshness binding은 자체 검사하지 않음 |기존 공유 gate의 exact-date/schema/content 계약을 consumer에 적용하고 날짜 오염·stale 계약 회귀 확인. item2 코드변경 금지에 따라 수정하지 않음 |
| 자동 개선 권한 부재 |이 작업의 신규 subset 승격은 retired; 모든 selected policy는 prior copy |데이터 부족과 구분할 설계 경계. 신규 EV 탐색/선정 연결은 별도 replay/consumer owner에서 닫아야 하며 이 작업의 ready를 강제로 켜지 않음 |

## 판단과 다음 조치

**실제 전략의 회계·재고·손실·비용 확인과 기존 정책 보존을 위해 유지할 가치가 있다. 현재 이 작업 자체를 EV 개선 탐색기로 보기는 어렵다.** 양수 기존 EV29개와 신규 개선0개는 다른 사실이다. 현 상태의0개는 충분한 독립 비교로 개선안을 모두 소진했다는 결과가 아니다.

우선순위는 (1) dated native 미생성 원인과 후행 소비 결손 확인, (2) exact source admission 및 실제 terminal/cost 신뢰성 보완, (3) 기존 causal replay owner의 정책 차이·same-budget 경로·holdout→선정 consumer 연결이다. 그 뒤에만 분석 비용을 줄인다. 보고서 중복 windows/rows로 대형 파일이 생기지만 이번에는 기존 summary/candidate projection으로 분석을 마쳤으며 성능 가드·추가 프레임워크·시장 조회·후보 확장을 만들지 않았다.

이번 분석으로 low-price producer, runtime, 실제 정책, source exclusion 및 holdout은 변경하지 않았다.9/17 전체 장후 DONE과 신규 EV·일별 순익 동시 개선은 여전히 증명되지 않았다. 별도 세션 산출물/정책을 재평가하거나 부재 표본 때문에 기존 완료 code review를 재개하지 않는다.

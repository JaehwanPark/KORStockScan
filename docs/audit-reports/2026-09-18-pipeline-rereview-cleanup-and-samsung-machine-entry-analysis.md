# Pipeline 재리뷰·과거 정리 및 Samsung machine entry 분석

작성:2026-09-18 KST. 사용자 범위는 pipeline 반복 코드리뷰/보완/검증·관련 commit/push·immutable successor 선택·불필요한 과거 진단 삭제이며 삼성 작업은 **분석만, 코드/정책/장후 결과 변경 금지**다. 봇 재시작·주문·조기 PREOPEN·독립 service pin/authority·guard/threshold/provider 변경과 전체 raw 재스캔/장후 chain 재실행은 수행하지 않는다. 증거 owner는 `tmp/pipeline-rereview-samsung-analysis-20260918/`다.

## 1. Pipeline 재리뷰

기존 PV0–PV6 구현·검증은 [owning review](2026-09-18-pipeline-event-verbosity-incremental-review.md)와 그 receipts를 확인했다. 이번 새 결함은 중첩 schema가 손상된 경우다. policy가 list/scalar면 reusable check가 AttributeError로 끝났고, checkpoint producer_rollup이 list면 explicit source blocker 대신 예외가 났다. strict reader도 policy/parity가 list일 때 OPEN을 출력하지 못했다.

기존 report/strict reader에 shape 검사만 보완했다. 잘못된 policy는 cache miss 후 기존 정상 checkpoint로 실제 계산·parity PASS/fallback을 복구한다. 잘못된 producer rollup은 producer_summary_invalid와 producer_rollup_contract_invalid를 출력한다. 잘못된 policy/parity의 strict 인계는 report_contract_invalid·같은 native owner의 OPEN이다. 정상 지원 입력을 모두 inactive로 만드는 수정이 아니다. 새 producer/service/module은 없다.

최종 report/strict/controller 영향 회귀326PASS, logger/summary/Sentinel/strict/handoff 회귀400PASS다. 앞선 report56PASS는 추가 strict 보완 전 중간 검증이며 최종 수에 합산하지 않는다. compile·diff·링크·parser 및 selected root/공유경로/router·선택 CAS는 최종 validation/deployment receipts를 따른다. 실행 중 immutable 소스와 다른 세션의 canonical dirty 변경은 보존한다.

과거 exact-date 진단125개/537,121bytes를 삭제했다. 불일치·부분coverage·PASS·9/14 직전 및9/15–17 근거23개, raw·producer/derived summary·checkpoint·주문/custody/비용·현재 정책/rollback은 보존했다. old generated workorder의 과거 파일 참조는 historical-cleanup-manifest의 날짜/원 SHA/state로 추적하며 현재 exact-date consumer 입력으로 사용하지 않는다. 이전 PASS promotion reader는 없고 count0이다. 삭제 전후 active cwd/FD·hash/path 대사를 시행했다. [삭제 manifest](../../tmp/pipeline-rereview-samsung-analysis-20260918/historical-cleanup-manifest.json), [삭제 receipt](../../tmp/pipeline-rereview-samsung-analysis-20260918/historical-cleanup.json).

새 code binding 때문에9/17 작은 진단과 해당 후행 인계만 갱신한다. 기존 volume/identity checkpoint를 재사용하며5.71GB bootstrap·benchmark·다른 튜너 재실행은 하지 않는다. 전체 strict의 타 축 FAIL과 pipeline 자연 parity OPEN은 해소됐다고 보고하지 않는다. selected release/PID/자연 경제성은 별도다.

## 2. 삼성 작업의 역할·원천·런타임

`monitoring.samsung_machine_entry_tuning`은 Main 일반 매수/compact AI 튜너가 아니라 삼성005930 독립 morning·조건부 morning_reentry·midday·afternoon machine의 실제 시도/체결/terminal/custody 관측 ledger다. wrapper는 최종 observation_source_quality_audit 다음에 report와 candidate를 한 번 생성한다. command는 `--target-date DATE --print-summary`이며 history API/raw 재조회는 없다.

입력은 현재 날짜4개 durable runtime state, 본 producer의 기존 날짜별 report, broker-verified manual exit/close reconciliation 및 append-only outcome amendment, exact-date applied policy/hash·signal features·source-quality audit이다. prebaseline/legacy one-leg/다른 quantity·target·confirmation/cohort를 섞지 않으며 mutable old state의 custody resolution은 원 entry date amendment로만 보존한다. daily·rolling10/20·clean cumulative·실제 적용 epoch를 분리한다. 날짜별 report는 과거 machine state를 대신하는 중요한 원천이므로 pipeline 과거 진단과 함께 지우지 않았다.

예전 threshold subset 탐색은 기존에 발생한 signal의 feature 조건을 강화해 남는 실제 결과를 집계했다. 조건을 바꾸면 첫 진입시각·체결·보유경로도 바뀌므로 이러한 부분집합을 인과적 challenger EV로 승인할 수 없다. 현행 v9는 **신규 subset tightening 승격을 폐기**하고 causal confirmation owner를 machine_entry_timing_tuning으로 정했다. 여기서 유일하게 남는 mutation은 실제 APPLIED legacy tightening1축의 손실을 exact epoch로 확인한 후 다음 PREOPEN에서 baseline 방향으로 되돌리는 bounded unwind다. morning은 해당 자동 unwind 대상도 아니다.

runtime 전달은 report→candidate→각 morning/midday/afternoon preflight의 samsung_machine_entry_policy_apply→dated applied policy→각 service의 load_applied_machine_policy→machine이다. confirmation 정책은 별도로 machine_entry_timing_policy resolver를 morning machine/regular two-leg machine이 소비한다. 구현된 reader가 존재하며 파일/해시/date/scope 실패 시 baseline/fallback 또는 해당 신규 BUY 차단이 적용된다. stage별 guard와 custody/override를 그대로 유지한다.

baseline 파일은 morning NXT drawdown3.0%/SOR0.75%, midday·afternoon high drawdown1.25%/low proximity0.20%/lookback30/entry validity5 bars, 총20주(leg당10주)·target2ticks다. **실효 target은 별도 승인된8/14 09:21 이후3ticks override**이며 actual report cohort도3ticks다. applied JSON의2ticks 숫자만 보고 현재 target이2ticks라고 판단하면 잘못이다. 새 매수량 override/기존 owned quantity는 별도 owner 계약을 따른다.

최신 삼성 report는9/16, source-quality preflight PASS·report artifact hash 유효·candidate validator PASS다. candidate policy_mutations=[]·selected_axis=None: 새 경제성 정책0, baseline/carry 유지다. 머신별 allowed_runtime_apply=true는 carry된 기존 policy의 전달 가능성이고, 전체 candidate runtime_effect/allowed_runtime_apply=false는 postclose의 직접 적용 금지다. `auto_bounded_live` applied 파일도 새 alpha 승격을 뜻하지 않는다.9/17·9/18 applied는9/16 source의 같은 policy hash를 사용한다.

## 3. 최신 완료성과:9/16 exact policy cohort

아래 순익은 **실제 broker BUY/SELL 가격에 고정 round-trip cost0.20%를 차감한 추정치**다. field 이름 broker_realized_net_profit_krw를 실제 수수료/세금까지 정산된 계좌 순익으로 읽으면 안 된다. 모델 ΔEV·신규 튜닝 이익도 아니다.

| machine | terminal episode / broker-priced 완료 leg | notional weighted EV | 비용모형 순익원 | 핵심 판정 |
| --- | --- | --- | --- | --- |
| morning | 10 / 10 | −0.678836% | −177,210.011 | rolling10 +0.370523%지만 rolling20/cumulative 음수. sample/source readiness 표시는 challenger 승인 아님 |
| morning_reentry | 2 / 2 | +0.357103% | +19,229.998 | 최신 daily source gap, low signal. 과거 두 번의 양수 결과만으로 승격 불가 |
| midday | 1 / 0 | null | 0(유효 완료 이익 없음) | NO_FILL로 terminal episode1이 될 수 있다. 수익 round trip1이라는 뜻이 아니며 평균EV는 계산 불가 |
| afternoon | 3 / 6 | +0.373066% | +58,589.993 | 소표본·low signal. 새 후보와 차이가 없거나 강화축의 candidate signal이 없었음 |

morning의 target 성공8legs와 검증 manual loss2legs를 합치면 손실이다. manual loss 추정 순익은−255,770.014원이고 average realized holding은1,319.387분이다. 다른 machine의 양수 결과나 최근10일만으로 이를 가리지 않는다. realized holding duration coverage도 morning100%·afternoon66.7%여서 보유시간 평균을 완전한 자본 점유/노출 검증으로 사용하지 않는다. 최신 cohort HELD/unresolved0은 원 amendment/custody resolution 반영 결과이며 보고서가 강제 청산/손절을 생성한 증거가 아니다.

clean window는72개 거래일 중 본 report 관측26개이고46개는 coverage 부재다. 이46일은6/5–8/10으로 현재 report 관측 시작8/11 이전이다. 이 숫자만으로 현행 producer 결함을 판정하거나 과거 raw backfill을 요구하지 않는다. 39/69일 같은 sample floor ETA는 정상 수집·과거 completion rate가 유지된다는 단순 projection이며 positive EV·source 복구·정책 적용일의 예상이 아니다. midday는 broker 완료율을 추정할 근거가 없어 ETA null이다.

## 4.9/17 결과와 현행 confirmation 탐색

9/17 삼성 report/candidate가 없다. 원 전체 wrapper가 앞 단계 resource guard에서 중단돼 이 단계에 도달하지 않았으므로 execution failure/미생성이고 valid-empty/no-edge가 아니다. 이번 분석은 report를 재생성하지 않았다.

남아 있는9/17 state를 기존 pure extractor로 읽은 결과 morning은 attempt1·NO_TRADE이며 entry_liquidity_touch_depth_insufficient에서 BUY 전 차단됐다. midday·afternoon은9/17 NO_TRADE/attemptfalse, reentry는9/10 state가 남아 target-date source gap이다. 이것은 실제0신호·guard block·당일 기록 부재를 분리해야 하는 근거이며 매수 guard를 풀어 표본을 만들 이유가 아니다.

9/17 machine_entry_timing_tuning의 전체winner/runtime_winner는null·baseline immediate carry다. 삼성005930 episode scope의 현재 dynamic source-only 비교는 다음과 같다. 일반/다른 종목의36개 cohort 집계를 모두 삼성 결손으로 전가하지 않는다.

| scope | owner signal row | owner eligible | dynamic replay eligible | 완료 economic pair | disposition |
| --- | --- | --- | --- | --- | --- |
| morning | 8 | 8 | 0 | 0 | source_quality_blocked8 |
| afternoon | 4 | 4 | 0 | 0 | source_quality_blocked2·economic_or_control_gap2 |

두 scope의 realized_pairing_gap은8/4, observed economic day/lifecycle0·ΔEV null이다. owner eligible8/4가 dynamic executable replay eligible이라는 뜻은 아니다. modeled net sum0도 빈 비교의 합계이며 EV0/no-edge가 아니다. fixed-delay와 current dynamic 분모/지원범위도 별개다. morning의 current floor assessment는 structural_population_exhaustion, afternoon은 terminal/executable pair 도착률 미입증이다. 현재 상태에서 단순 기다림이 승인으로 이어진다는 근거는 없다.

별도 installed 삼성 service들은 Main 선택 selector와 독립적으로9/16 intraday release에 pin돼 있다. 조회 시 morning은inactive/PID0, midday·afternoon은auto-restart/PID0·exit4였고 journal 원인은 authority_not_ready_or_target_date_mismatch다. 휴장 당일 authority 차단을 자동 완화하거나 거래일의 영구 결함으로 단정하지 않는다. 다음 정상 적용일 authority·preflight·해당 service pin/consumer receipt를 별도 owner가 확인해야 한다. 이번 pipeline 선택이 그 service들을 새로 기동/업데이트했다고 보고하지 않는다.

## 5. 시간으로 풀릴 것과 구조 보완·closure

| 쟁점 | 시간만으로 해소? | owner·다음 조치·closure test |
| --- | --- | --- |
| 정상 actual ledger의 낮은 signal/완료 표본 | 조건부 가능, 양수 edge 보장 없음 | machine services·daily producer: 신규 exact-date state→dated report→동일 cohort 실제 완료/cost 증가 확인. NO_FILL/HELD는 수익 표본으로 계산하지 않음 |
| 아직 HELD인 진짜 거래의 terminal | 자연 SELL/검증 수동 resolution 시 가능 | order/custody/amendment owner: exact broker receipt·exit/knowledge time, 동일 원 episode에 amendment1회·현재 보유량 대사 |
|9/17 report 미생성 | 자동 표본 누적으로 해당 날짜 복구 안 됨, 기존 state가 남았으므로 조건부 복구 가능 | final audit→삼성 producer: 승인된 단일 날짜·현 원천/당시 비용 계약으로 생성 후 hash/date·candidate0/carry 확인. 과거46일은 원천 없는 상태를 현재값으로 채우지 않음 |
| conditional reentry의 old-date UNKNOWN | 신규 episode 없이 부재가 계속될 수 있음 | morning reentry producer/custody: 해당 날짜 reentry eligibility/선행 종료·비실행 사유 근거 확인. 의도된 no-op은 NOT_APPLICABLE/NO_TRADE 관측과 실제 source loss를 구분하는 기존 계약으로 수리; 원 position을 새 날짜 episode로 복사하지 않음 |
| 고정0.20% report와 timing runtime0.23%·비용 provenance/정산 | 구조 계약 보완 필요 | broker cost/episode outcome·timing evaluator: 당시 frozen fee/tax/slippage·SELL net receipt와 reserve/holding 계약을 같은 date/hash로 전달.0.20%를 실제 계좌 손익으로 승격하지 않음 |
| owner outcome는 있지만 replay/pair0 | 현재 도착률이 입증되지 않아 단순 maturity라 부를 수 없음 | microstructure attribution→timing: 첫 replay 불충족 원천/identity/horizon/실행 가능한 venue/session/cost/exit 모델을 scope별 추적. 지원 운영 producer→stored projection→동일 자본 baseline/candidate→독립 holdout→dated policy→실제 machine loader의 지원/실패 경로 회귀. 실제 SELL을 다른 CF 보유 경로에 붙이지 않음 |
| 부분집합·candidate가 원동작과 같음 | 아무리 누적해도 그 비교는 행동 변화 검증 아님 | timing owner: first signal/confirmation 변화가 실제 entry/fill/guard/exit를 어떻게 바꾸는지 재현, distinct behavior·net/tail/exposure/reserve·capital competition 검증. signal rate 감소만으로 경제성 승인하지 않음 |
| PID/service authority 경계 | 정상 거래일 준비 여부 확인 필요, 자동 변경 금지 | 기존 preflight/독립 service owner: 정확한 적용일 policy/hash·override·new-BUY authority·immutable pin→PID 소비→자연 행동 receipt. 현 휴장 차단은 보존 |

판정: 실제 성과·손실·custody·정책 lineage를 보존하는 이 작업은 유지 가치가 있다. **별도 신규 alpha 탐색을 여기로 되살릴 가치는 없으며 현행 timing/기계 evaluator에 집중해야 한다.** morning의 손실을 숨기지 않고 same-capital confirmation 후보를 검증할 수 있게 만드는 원천/실행경로 수리가 먼저다. 표본 준비 숫자와 양수 afternoon 실제 거래 평균은 그 수리/독립 검증을 대체하지 않는다. 삼성의 코드는 변경하지 않았고 원 report/candidate/policy/service 상태도 변경하지 않았다. [read-only 분석 receipt](../../tmp/pipeline-rereview-samsung-analysis-20260918/samsung-analysis.json)와 bounded service/journal evidence를 따른다.

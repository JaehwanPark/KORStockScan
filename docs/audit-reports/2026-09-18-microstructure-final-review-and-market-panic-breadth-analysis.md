# Microstructure 최종 재리뷰 및 다음 장후 단위 분석 — 2026-09-18

## 판단과 검증 범위

사용자가 microstructure 통합 변경의 반복 코드리뷰·수정보완·commit/push·배포와 다음 장후 단위 분석을 승인했다. selected `53aecf7466d1f4aa52807ab9e8c1b175734b898a`를 기준으로 별도 clean worktree에서 재리뷰했다. unrelated 작업본 변경, 실행 중 worker, broker/provider/주문·정책·env·cron은 보존한다.

다음 실제 단위는 **`market_panic_breadth_collector`**다. 이는 독립 수익 튜너가 아니라 현행 시장 위험 관측의 공통 수집기다. **운영 원천으로 유지할 가치가 있다.** 실행 비용이 작고 widget/episode의 현행 위험 소비 연결과 자연 관측이 확인된다. 후속 hysteresis 튜닝의 EV 개선은 현재 입증되지 않았다. 원천 결손을 해결하기 전 표본 대기나 floor 완화로 해결할 수 없다.

## 재리뷰 결함·보완·검증

1. Modern 진단 보고서가 기존 `runtime_effect`/`allowed_runtime_apply=true`를 계승할 수 있었다. 갱신 전에 두 값이 명시적으로 false인지 검증하고 위반 시 실패시킨다. Legacy 보고서는 기존 보관/전환 계약을 유지한다.
2. Summary 소비가 부모 hash·날짜·payload는 확인하면서 부모의 calibration schema와 적용 권한은 재검증하지 않았다. 동일 SHA로 다시 결속된 권한 오염 부모도 source gap으로 처리한다.
3. 새 진단 보고서의 지표 계약에서 window/sample/source-quality 선언이 빠졌다. 기존 case labeler와 기존 owner promotion gate를 선언한다. 새로운 floor·tuner·실행 권한은 추가하지 않는다.

회귀 검증: `test_microstructure_reaction_context_report.py`와 `test_ai_action_outcome_calibration.py`에서 microstructure/발행 연결 관련 **11 PASS, 157 deselected, 3.16초**. 변조 부모/보고서 거부, 필수 지표 계약, 날짜/hash 인계, 일일 보고서의 비대상 metadata 보존을 검증했다. Compile, diff, print-only backlog parser 및 변경 범위 재리뷰 결과는 `tmp/microstructure-final-review-20260918/validation.json`에 기록한다. 배포 commit/root/selector/router 검증은 같은 경로 `deployment.json`을 따른다. 직전 대규모 guard/consumer 회귀 증거는 [통합 배포 review](2026-09-18-microstructure-postclose-consolidation-review.md)를 재사용한다. 이번 변화는 진단 계약만이며 실시간 특징/guard/API 구현을 변경하지 않는다.

배포는 source 선택이다. Main/PID 재시작·자연 소비·경제성 승인은 별도다. 기존 postclose cron 부재를 보존하므로 자연 장후 Acceptance는 OPEN이다. intraday 관측은 별도 활성 cron으로 실행되고 있다. 이번 재리뷰에서 raw replay·전체 연구·calibration/model/grid 재산출은 하지 않았다.

## 실행 순서·시간·원천

- Owner: `deploy/run_threshold_cycle_postclose.sh`. 전용 microstructure raw 호출 폐기 위치 다음의 첫 실행 가능 producer가 `src.engine.market_panic_breadth_collector --date "$TARGET_DATE"`다. panic report와 breadth report 두 flag가 모두 true일 때 실행하며 기본값은 둘 다 true다. 이어서 `panic_sell_defense_report`를 실행한다.
- 9/17 실제 `logs/threshold_cycle_postclose_cron.log`의 PERF/ready: collector **0.663918405초**, child peak RSS **116,012KiB**, exit0 및 dated JSON ready. 앞선 구 raw microstructure는68.839563초였다. 이 수치는 해당 실행 receipt이며 성능 benchmark/전체 chain 성공을 의미하지 않는다. 후행 chain은 resource guard로 중단됐다.
- Collector: `src/engine/market_panic_breadth_collector.py`. 기존 Kiwoom `ka20003` 업종 조회를 KOSPI(001)/KOSDAQ(101) 각각 수행하고 request market provenance를 붙여 지수2개와 산업/상승·하락 종목 수를 정규화한다. 시장별 응답 준비·HTTP/semantic-empty 상태를 확인한다. 이번 분석은 저장된 artifact/source만 읽었으며 API를 호출하거나 protocol을 수정하지 않았다.
- 출력: `data/report/market_panic_breadth/market_panic_breadth_<date>.json` 및 `data/report/market_weakness_observations/<date>/`의 관측 이력. source-only/no-order 보고서이며 이 단위에 candidate/actual EV는 정의돼 있지 않다.

## 현행 판단 로직

기준은 지수 −1.2%, 산업 하락 비율62%, −2% 이하 산업 비율15%, 하락 종목 비율70%다. 전체 weighted risk-off는 **weighted 지수 약세 AND (산업 하락 OR 심한 산업 하락 OR weighted 종목 하락)**이다. 시장별 weakness는 **(시장 지수 약세 OR 시장 종목 하락) AND (산업 하락 OR 심한 산업 하락 OR 시장 종목 하락)**이며 source scope 준비가 선행한다. 따라서 네 기준을 모두 넘어야 하는 구조도, 하나만 넘으면 무조건 전체 시장 위험을 발동하는 구조도 아니다.

회복 evidence는 완화 margin을 적용한 시장별 조건으로 판단한다. 현재 hysteresis는 서로 다른 유효 관측 **발동2회·해제3회**, 최소 간격60초다. Collector는 관측/정책 identity를 만들며 직접 latch streak나 주문을 변경하지 않는다. 관측의 recovery evidence 한 건만으로 실제 release가 완료됐다고 판단하지 않는다.

## 9/17 실행 결과와 현행 소비

9/17 collector 보고서의 as_of는 **23:48:35 KST**, source-quality=ok, normalized65행(지수2/산업63), errors=[]이다.

| 항목 | 저장된 결과 |
|---|---:|
| KOSPI / KOSDAQ 지수 변화 | −0.04% / +0.76% |
| Weighted 지수 변화 | +0.24% |
| 전체 산업 하락 / 심한 하락 비율 | 22.2% / 3.2% |
| 시장 중 최대 종목 하락 비율 | 42.3% |
| Raw 관측 | RECOVERY_EVIDENCE |
| Weakness affected markets | 없음 |
| Recovery evidence markets | KOSPI, KOSDAQ |

관측 ID는 `market-weakness-310f2b8ac01e7e9ae7ae`. dated hysteresis 적용 hash는 `af75d4132a58f38402438a82bab6b7e26ecd55ad3b0a6464388a5ec5ad0aa597`이며 9/16 연구의 **기존2/3 carry-forward**다. 새 정책 선정 receipt가 아니다.

원천→소비:

1. Collector→dated panic report의 `market_weakness_observation`→`notify_panic_state_transition --kind market_weakness`→`tmp/market_weakness_observer_state.json`의 시장별 latch/health.
2. Intraday wrapper `deploy/run_panic_sell_defense_intraday.sh`는 신선한 breadth를 제한적으로 재사용(기본75초), 필요하면 수집하고 notifier까지 실행한다. 현행 cron은 정규장9:06–15:28 구간의 반복 실행이다. postclose collector/report 한 번이 같은 notifier 경로를 자동 완료한다는 근거로 사용하지 않는다.
3. `risk/market_weakness_entry_guard.py`는 current session·freshness·verified listing market·owner를 확인한다. widget/episode의 신규 매수 veto와 **같은 owner의 broker-reconciled 미체결 매수 잔량** 취소 소비를 담당한다. Main/manual/타 owner 매수·보유 SELL·목표/수량 변경 권한은 없다. 실제 취소/주문이 발생했다는 주장은 하지 않는다.
4. `trading/widget_auto_trade/engine.py`, `trading/order/regular_two_leg_machine.py`의 소비가 확인된다. Main 직접 entry guard 소비는 이 경로의 적용 범위가 아니다.
5. 9/18 **12:52:01 KST** 검증된 observer state는 session9/18, phase=released, active markets=[], health.ready=true, consecutive failures0이다. 이는 자연 관측/정상 health 증거이며 정책 수익·실제 발동/취소 증거가 아니다. 별도 intraday cron은 작업본 wrapper를 사용한다. Managed release 선택만으로 이 consumer의 source/PID까지 같은 commit이라고 주장하지 않는다.

## 실제 튜닝은 어디서 하는가

별도 `machine_microstructure_attribution`의 `market_weakness_entry_response`와 `automation/market_weakness_hysteresis_tuning.py`가 수행한다. `run_machine_microstructure_final_refresh.sh`가 이 인계를 소유한다. Collector와 전용 raw microstructure 폐기는 이 tuner를 제거하지 않는다.

중복 제거된 owner/시장별 진입 anchor와 시장 관측을 조인하고, depth-backed 진입 ask/수량·horizon 청산 bid·왕복 비용을 갖춘30분 CF를 계산한다. 현행2/3에서 한 축만 ±1인 **2/2,2/4,3/3**을 비교한다. Calibration ΔEV≥0.005%p, full ΔEV≥0.003%p, holdout≥0, p10≥−0.05%p와 기존 날짜/시장/owner floor를 모두 충족해야 후보가 된다. 이 허들은 가격수익1.5%가 아니다. 실제 realized control 비교와 CF candidate ΔEV는 별도다.

최신 유효 연구는 **9/16**이다. 9/17 attribution/tuning 보고서와 effective9/18 정책 artifact는 확인 시 부재했다. 9/16의 carry-forward를 9/18 적용 증거로 바꿔 읽지 않는다.

| 모집단/검증 | 최신9/16 결과 | 의미 |
|---|---:|---|
| 당일 진입 anchor / source eligible | 24 / 24 | 시장/state 조인 준비; 호가 horizon 경제성 준비와 별도 |
| 당일 confirmed weakness / actual comparison | 0 / 0 | 당일 실제 비교 없음 |
| 누적 unique anchor | 1,238 | episode/anchor primary key 중복 제거 |
| 30분 CF eligible / 제외 | 11 / 1,227 | 유효율0.88853%; 구조적 수집 결손 포함 |
| CF 날짜 / holdout | 2 / 0 | 9/3·9/15; 분리 검증 미달 |
| CF KOSPI / KOSDAQ | 11 / 0 | KOSDAQ zero-yield |
| CF widget / episode | 6 / 5 | owner floor도 미달 |
| 세 후보의 현행 대비 평균 ΔEV | 모두0.0%p | 후보 변화가 이 작은 표본에서 경제적 차이를 만들지 않음 |
| 현행/세 후보 model 비용 차감 평균 | −0.41349624% | CF 모델 값; 실제 신규 손익 아님 |
| 누적 실제 realized control 비교 | 1건 / 1거래일 | 순수익에 근거한 비교지만 새 정책 실제 결과 아님 |
| 해당 실제 control 대비 skip 가정 Δ | −0.35014535%p | 기존 실제 control 수익을 놓친 것으로 계산; 실제 skip의 실현 손실 아님 |
| 정책 선정 | 없음 | `current_policy_carried_forward`,2/3 유지 |

누적 actual 비교는 **zero-exposure skip 가정 − 실제 control 비용 차감 수익**이다. 실제 control1건이 있다는 사실을 새로운 guard 정책의 realized EV/순익·인과 효과로 해석하지 않는다. Actual 제외 사유는 주문 미제출1,109·control 누락39·skip arm invalid48·source quality41이다(한 row 여러 사유 가능). 미제출 기회를 CF에서 삭제하거나 강제 체결해 actual 분모를 채워서는 안 된다. 지연 진입/상대강도 예외 arm은 구현되지 않은 진단 placeholder이며 현재 평가 성공으로 표시하지 않는다. 이를 새 런타임으로 확장할 필요가 입증된 상태도 아니다.

## 시간이 해결할 부분과 구조적 결손

| 구분·판단 | Owner / 원 artifact | 다음 보완 | Closure test |
|---|---|---|---|
| 유효 관측 후 signal50·거래일10·holdout3·current-policy3·시장별/owner별10 등 floor 부족 | response `metric_contract` / threshold recommendation | 기존 자연 signal을 기다리되 유효 yield/시장별 분모 확인 | 정상 날짜의 eligible 증가·시장/owner floor·holdout을 같은 계약으로 확인 |
| KOSDAQ0 및 30분 BBO1,227건 제외는 기다림만으로 복구되지 않음 | 기존 exact-route 0B/0D/horizon producer→response source census | 최초 결손인 등록 route/item·entry ask/잔량·청산 bid path·quantity·source-quality·cost 연결부터 수리; floor/grid 신규 확장 금지 | 자연 KOSDAQ/widget/episode anchor 각각 exact-route 등록→depth/quantity→30m path→full-cost 조인→동일 native ID CF eligible; 누락은 null/제외 유지 |
| 9/17 late attribution/tuner/effective9/18 정책 인계 부재 | `run_machine_microstructure_final_refresh.sh` / dated artifacts | 해당 worker terminal/실제 date/정책 인계 receipt 확인. 중단된 native chain만을 원인으로 단정하지 않음 | 9/17 attribution→source snapshot/hash→9/17 tuning disposition→effective9/18 dated policy/hash·consumer 확인; carry와 selected 구분 |
| collection clock와 market event clock/venue/session 의미 결속 미입증 | collector normalized row +23:48 as_of / observation | 저장된 collection time을 시세 freshness로 간주하지 않음. 프로토콜 변경 필요 시 공식 Kiwoom reference gate와 원 packet clock 의미 검증 | 원천 event time·market scope·session 기준 검증, 동일 closing 값 반복 수집이 fresh market 관측으로 오인되지 않는 회귀 |
| 통합 aftermarket/NXT 반복 관측 미입증 | intraday cron15:28 종료 / collector provenance | listing-market 공통 위험과 NXT venue-specific breadth를 구분. 장후 snapshot을 aftermarket 자연 guard 증거로 사용하지 않음 | 해당 session 실제 관측→verified listing/owner→guard freshness trace; 범위 미지원은 명시, 임의 schedule/authority 확대 금지 |
| 실제 적용 버전의 비용 차감 성과 부족 | applied policy→owner natural action→COMPLETED control | 정책 선정/소비 후 실제 완료 경제성 별도 추적 | 적용 hash·시장/owner·중복제거 episode별 rolling/cumulative net EV·순익·tail·노출·model error; missing은 null |

보고서의47추가 거래일은 현재 eligible yield를 신호 floor에 단순 외삽한 값이다. `attainability.status=collection_contract_gap`, KOSDAQ zero-yield, holdout0이므로 완료 ETA는 **미정(null)**이다. 현재 후보0은 유효 no-edge 판정이 아니라 **source gap + insufficient sample + 현재 관측 후보 ΔEV0**의 조합이다.

권고 우선순위는 **수집기 유지 → exact-route/horizon 원천 수리 → late producer 날짜별 인계 확인 → 자연 유효 표본 → 기존 후보/holdout → 실제 버전별 경제성**이다. Collector0.664초의 성능 확대 점검이나 별도 튜너 신설은 우선순위가 아니다. 이번 분석에서는 관련 원천/guard/cron을 수정하거나 재실행하지 않았다.

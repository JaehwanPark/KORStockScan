# Low-price actual 튜닝 후속계획 — 탐색·적용 자격 분리와 경제 증거 종결

작성: 2026-09-19 KST. 상태: **LP-B0–B6 구현·리뷰·제한 재생성 완료 / 자연 PREOPEN·실제 개선 Acceptance OPEN**.

## 1. 목표와 기존 구현의 경계

목표는 실체결이 있는 기존 profile에서 서로 다른 두 entry-filter 정책의 비용 후 EV·일별 순익 개선 가능성을 실제로 탐색하고, 적용 증거가 닫힌 한 정책만 다음 정상 PREOPEN에 전달하는 것이다. 구조 결손 해결→비교 가능한 경제값→자동 소비→실행시간 순으로 진행한다. 양수 결과를 보장하거나 적용 기준을 낮추지 않는다.

부모 [LP-A0–A7 계획](low-price-two-leg-actual-conditioned-paired-economic-search-and-preopen-runtime-consumer-improvement-plan-2026-09-18.md)에서 구현한 actual cohort/cost, paired replay, 관측 capture, candidate v4, 단일 lock/atomic/freeze, PREOPEN·loader·summary 경로를 재사용한다. 새 replay engine/CLI/service/root Python module을 만들지 않는다. 이번 문서는 후속 계획 수립이며 원래 실행 승인을 문서 작성 중 호출하지 않는다.

9/19 현재 checklist는 없다. 미래 실행 owner는 [9/21 checklist](../checklists/2026-09-21-stage2-todo-checklist.md)의 기존 `LowPriceExpandedResearchRepair0918` 하나다. LP-B0–B6은 같은 owner의 후속 상세 package로, 새 checkbox/병렬 canary가 아니다. 완료 LP0–LP6/Q0–Q5는 재개하지 않는다.

## 2. 재확인한 원인과 정정

Frozen v9의 실제 epoch와 모델 custody를 재대사한 결과, 기존 “적용 eligibility0·paired replay0” 설명은 잘못이었다. 카카오 오전 후반은 실제8leg·20일·epoch unresolved0으로 actual floor를 통과했고 이미 distinct calibration1개를 계산했다. `hold_inventory_custody`가 모델의 미확정 carry를 뜻했는데 실제 재고로 오인했다. 실제 floor와 최종 승격은 별개다.

| 우선 대상 | broker 가격 완료leg / source-valid 일 | 실제 epoch unresolved | 후속 처리 |
| --- | --- | --- | --- |
| kakao_late_morning | 8 / 20 | 0 | 기존 모델 carry 및 native execution/capital 결손을 별도 진단; 적용 보류 |
| youngone_morning | 6 / 19 | 0 | 유효 완료1leg 연구 착수 조건으로 calibration 수행; 실제8leg 적용 floor 유지 |

별도 결함으로 카카오 오전/정오의 과거 HELD 행에는 이후 applied 수동 청산 journal이 반영되지 않았다. owner·symbol·entry date·broker order identity·whole remaining quantity를 검증해 projection만 보정한다. 현재 state나 journal을 다시 완료처리하지 않는다. 수동 손실/추정 비용/알 수 없는 실제 fill time을 보존한다. 영수증이 없는 역사적 미확정 행을 현재 flat 상태만으로 청산하지 않는다.

현행 `_paired_economic_search`는 source→held/custody→8leg·5일을 통과해야 context를 불러 탐색한다. 적용용 floor와 현재재고 조건을 탐색 시작 조건으로도 사용한다. 이 결합을 분리한다. 과거 durable 관측/BBO/자본 원천의 부재는 별도 결손이며 floor 분리만으로 복구되지 않는다.

## 3. LP-B0 — 입력과 단계별 blocker 대사

작은 existing report/candidate manifest와 source-valid actual rows에서 profile·policy epoch·owner/venue/session·실제 buy fill/완료leg·정확/추정 비용·미청산·manual exit를 대사한다. Stage count를 source quality/status와 함께 고정하며 현재 state를 과거 날짜로 바꾸지 않는다. 날짜/raw/cache/proof의 path/hash/as-of를 기존 필드에 남긴다.

탐색·승격·발행·자연소비를 각각 집계한다: 실체결profile, source 확인완료profile, calibration 평가profile/축 수, distinct resolved pair 수, 미사용holdout 대기 수, promotion eligible 수, 실제 mutation/보존 수. 적용 eligible0이 research tested0으로 표시되지 않도록 한다. Source gap·재고·소표본은 서로 다른 축이므로 차단 사유 전체와 그 최초 경계를 보존한다.

Closure:61profile main disposition 대사, 카카오8leg/20일·영원무역6leg/19일 재현, 서로 다른 epoch/CF 실적을 합쳐 floor를 채우지 않음. Source quality가 허용됐다는 사실만으로 custody/경제성을 PASS로 바꾸지 않음.

## 4. LP-B1 — 탐색·고정 후보·적용의 세 단계

| 단계 | 최소 조건 / 허용 동작 | 금지 |
| --- | --- | --- |
| 실제 체결 조건부 원천진단 | 기존 profile·실제 buy fill>0, dated owner/receipt 식별 | 무체결 종목의 시장 전체 탐색, retired/OFF 복원 |
| 제한적 calibration 탐색 | 같은 actual epoch에 source-valid COMPLETED·valid cost/profit leg가1개 이상, 유효 applied baseline과 정식 cached bars/cost contract 존재 | 이것을 통계적 개선 확정/실행 동등성/적용 자격으로 해석 |
| 독립 후보 고정·정책 적용 | 선정은 기존 calibration30일·6episode/8leg 및 stability floor; 검증은 사전 고정 미래30/16일·holdout3episode/4leg; 적용은 actual5일/8leg·custody·execution/capital/authority·경제조건 전부 | 연구 bool/소표본 결과만으로 v4 mutation 또는 live 권한 생성 |

1leg는 연구 착수의 자원·원천 조건이며 새 통계적 승인 floor가 아니다. Partial/held만 있고 유효 완료 결과가 없다면 source/custody 진단까지만 수행한다. Manual 청산 손실과 estimated 비용은 기존 cohort로 보존하고 좋은 실제 거래만 골라 연구 여부를 정하지 않는다. 관측일5일·실제 완료8leg는 적용 조건으로 유지한다.

Current actual inventory는 새 entry-filter 적용을 계속 막지만 사전 고정 cached market window의 calibration 진단 전체를 막지는 않는다. 전체 actual 성과의 미확정 손익과 모델 결과는 별개로 표기한다. 현재 재고를 가상 강제청산하거나 replay에서 삭제하지 않는다.

`actual_eligibility_passed`는 기존 엄격한 적용 의미로 유지하고 별도의 research admission 필드를 추가한다. Frozen candidate pointer는 기존 단일profile/axis를 유지한다. 소표본 actual profile도 모델 calibration floor를 통과하면 source-only 미래 후보를 고정할 수 있지만 actual 적용 floor를 통과할 때까지 선택 정책은 incumbent carry다.

Closure: 무체결은 replay0, 영원무역의 valid source가 있으면8leg 전에도 research 수행, 카카오 모델 custody/native proof gap은 promotion false 유지, 연구 값만 조작해 mutation 생성 불가.

## 5. LP-B2 — 첫 bounded 실행과 원천 등급

초기 범위는 위2profile·기존 두 axis의 bound challenger 각1개로 제한한다. Source 진단에서 불가능한 profile을 다른 종목으로 자동 교체하지 않는다. 서로 다른 후보 최대4개와 profile별 baseline1회를 calibration에서만 평가하고 동일context/cache를 재사용한다. 이미 고정된 미래 후보가 있다면 그 계약을 먼저 검증하고 새 후보를 병렬로 고정하지 않는다.

Baseline은 해당 실제 applied epoch의 값/hash를 사용한다. Quantity20·각leg10, target/offset/lookback/validbar/session/venue, 비용·자본 규칙은 바꾸지 않는다. Challenger는 rolling_high_drawdown_pct 증가 또는 rolling_low_proximity_pct 감소 중 한 축만 기존 bound에서 조정한다. Identical 정책은 self_comparison으로 제외한다.

| 증거 등급 | 계산 가능한 결과 | 후행 허용 범위 |
| --- | --- | --- |
| actual state/정식 cached bars/cost valid, 과거 durable/BBO/자본 없음 | 전체 순차 bar-model calibration 진단과 원천 결손 | hypothesis/report-only, 승격 증거 아님 |
| durable signal+policy와 native execution/자본 결속 valid | next-entry/custody·실행/자본 검증된 paired model | 기존 미래window·적용 floor·authority 단계로 전달 |
| applied/bar/비용/owner 자체 결손 | 해당 원천 gap·복구 가능성 | EV null, replay 미실행, incumbent 독립검증 후 보존 |

과거 native capture0을 bars나 최근100개 state audit로 대체하지 않는다. Cached bars가 유효할 경우 그 시장 모델의 진단을 허용하되 실제 누락된 관측/quote/order/자본을 재현했다고 하지 않는다. Hypothesis를 complete execution receipt로 위장하지 않는다. 동일 source signature의 미복구 gap에는 전체 retry를 반복하지 않는다.

Closure: 가능한2profile의 실제 calibration 진단 또는 profile별 정확한 source blocker가 남음; current eligibility0 문구로 분석 결과를 대체하지 않음; 전체204종목/1,020profile 재계산·추가 API 조회 없음.

## 6. LP-B3 — 전체 시간순 경로와 경제값

기존 `_evaluate_candidate_windows`/continuous carry/replay/`paired_economics`를 사용한다. 같은 사전 고정 날짜·baseline initial custody·native quantity/비용·예산으로 entry→full/partial/no-fill→target/manual exit→다음 기회·자본 해제를 양측 계산한다. Baseline 거래 몇 개를 삭제해 challenger로 간주하지 않는다.

Actual 완료leg의 비용 후 지표는 COMPLETED+valid profit/cost만 집계하되 unresolved 수/재고/비용 gap을 같은 표에 남긴다. 이를 전체actual epoch의 확정 EV/일별순익으로 오인하지 않도록 metric role을 분리한다. 미청산을 제외한 actual PnL subset은 정책 우위의 paired 증거가 아니다.

Model 지표는 source-valid 사전 고정 관측일과 비용 후 유효 executed notional을 사용한다. 기존 모델이 unit quantity1이면 `CF calibration unit quantity1`과 native10-share 실행 미확정 사실을 명시한다. Unit net/day를 실제20-share 또는 portfolio 순익으로 이름만 바꾸거나 선형확대로 승인하지 않는다. Native quantity 실행·capital 증거가 닫힌 projected 값과 실제 손익은 별도다.

Distinct resolved 양측에 한해 baseline/challenger EV·순익/day·ΔEV·Δ순익/day·비용·완료episode/leg·no-fill·unresolved·occupancy/MAE를 제시한다. 정상 flat/no-trade0은 공통 관측일에 포함하지만 baseline no-fill EV는null이다. Held/carry·missing cost는 순익0으로 채우지 않는다. 양측이 미확정이면 partial-realized 진단만 표기하고 전체 joint ΔEV/Δ순익은null과 이유다.

동시 개선 기준은 기존 distinct+resolved+양측EV유효+candidate EV양수+ΔEV≥0.005%p+Δ순익/day>0와 tail/stress/자본/실행 계약이다. Win rate/양수 actual 총합을 대신 쓰지 않는다. “측정 no-edge”는 유효 양측 비교가 실제 완료된 경우만 사용한다.

경제 metric 계약은 기존 필드를 재사용한다. `metric_role=primary_ev`, primary metric은 `notional_weighted_ev_pct`와 동일 관측일당 비용 후 순익이다. Research 결과의 `decision_authority`는 report-only이며 actual/CF evidence role과 source-quality gate를 함께 기록한다. Window/sample floor는 B1/B4의 단계별 계약으로 명시한다. Forbidden uses는 actual PnL 합산·무증거 quantity 환산·runtime mutation/order/provider/수량/target 변경이다. Actual 완료 cohort의 EV도 미청산을 포함한 전체 정책 우위를 증명하지 않는다.

Closure: custody-censored/무체결/자기비교를 joint 개선 집계에서 제외; 음수/손실manual 결과도 보존; 가용 값만 수치화하고 미확정값은null; 실제/모델/단위수량/비용 source 구분.

## 7. LP-B4 — 단일 후보·독립 검증·버전 계약

Research와 promotion disposition을 동시에 보존한다. 예: 영원무역 `research_tested + promotion_hold_sample`, 카카오 `research_tested/censored + promotion_hold_model_inventory_custody`. 두 단계 수를 더해 profile 분모를 늘리지 않는다.

최대4대안의 ranking은 calibration에서만 계산한다. Calibration/stability floor를 통과한 단일profile/axis를 기존 registered revision·미래window 계약으로 고정한다. 이미 본 exploratory holdout은 승인 증거로 쓰지 않는다. 미래30/16일 기간과 실제필요표본이 채워져도 signal/policy durable, 양측 BBO/full-depth execution·일별 native capital, broker baseline terminal, 비용/authority/same-stage가 없으면 승격은 계속 보류한다. 원천을 기다린다는 말 대신 각 producer/consumer·blocker·closure를 명시한다.

Report는 탐색/적용 의미를 바꾸므로 기존 producer에 v10 successor를 추가한다. V9/history와 candidate v4 reader는 보존한다. 새 candidate version을 만들지 않고 v4의 source-report 허용 branch 및 source hash/brief를 v10에 맞춘다. Research admission은 실제 적용 proof를 대체하지 못하며 validator는 기존8leg·5일·단일axis·보수적 bound·quantity/target 불변·native proof 재검산을 유지한다.

Schema intake는 actual report의 v9/v10과 candidate에 선언된 source_report_schema를 정확히 결속한다. 모든 역사 report에 최신 REPORT_SCHEMA만 요구해 v9 frozen proof를 무효화하지 않는다. V9의 research 필드 부재는 legacy_research_not_reported로 표시하고 tested0으로 추정하지 않는다. Research/disposition/count 추가는 기존 report profile section과 native brief에 국한한다.

성숙 실패/parent/source-cost correction 시 기존 revision renewal 경로만 사용한다. Holdout 결과를 본 뒤 profile/challenger를 교체해 동일holdout으로 승인하지 않는다. Synthetic adapter positive는 구성 테스트로만 쓰고 fully closed real evidence로 발표하지 않는다.

Closure: v9 legacy/frozen 보존, v10 research-only positive mutation 거절, forged source/date/baseline/quantity/extra axis/holdout/source gap 거절, 기존정상 carry 및 증거를 갖춘 정책의 동일경로 소비.

## 8. LP-B5 — 마지막 소비와 다음 PREOPEN

연결은 기존 final audit/actual rows/cache→v10 research+promotion→dated candidate v4→Daily/EV/runtime brief→tower/checklist→strict require-summary-handoff→controller→정상 PREOPEN native applied→preflight/service/machine→actual post-apply다. 기존 `paired_search_handoff`에 research tested/진단 source grade/수치 여부/gap와 strict promotion selected/effective/hash를 함께 전달한다. Promotion0이 research 결과를 지우지 않게 한다.

Source/publication/effective date를 구분하며 effective는 실제 발행일과 source 중 늦은 날 이후의 다음 KRX거래일이다. 구현/발행이 늦어지면 이미 지난 장전에 적용했다고 하지 않는다. 이번 계획이9/21 파일을 새로 발행한 것은 아니다. Native single lock·atomic/frozen file·candidate already-consumed 보호·operator transitions·quarantine3·재고 custody·fallback/invalid 구분을 재사용한다.

승격 증거가 없으면 다음 장전 후보는 verified incumbent copy, mutation0이며 research 수치/gap는 후행에서 계속 소비한다. 정책 적용 서비스는 research 기준을 읽어 entry 조건을 바꾸지 않고 validated applied policy만 읽는다. 공통PREOPEN7:35→Main7:55→해당profile preflight의 기존 시간/실제 source pin을 확인하되 추가timer·daemon·hot reload/restart는 하지 않는다. Auto-expansion은 별도정책 consumer이므로 actual 연구의 범위 확대나 복원 경로로 사용하지 않는다.

Native source/candidate를 재생성하기 전 active writer/consumed file·input signature를 확인하고 원본/proof·이전candidate를 보존한다. 필요한 producer와 후행만 갱신한다. Whole strict/controller의 외부 실패는 별도 owner로 유지하며 family diagnostics PASS를 전체DONE으로 바꾸지 않는다.

Closure: EV/runtime/Daily·tower/checklist/strict에서 current research/promote generation이 일치; 후보/준비 applied loader date/hash일치; source-only 연구가 실제 mutation으로 새지 않음; 자연 PID/체결/비용 성과는 동일owner OPEN.

## 9. LP-B6 — 구현 위치·검증·종결

| 순서 | 기존 수정 위치 | 필수 회귀 / 실제 종결 |
| --- | --- | --- |
| B0–B1 | monitoring/low_price_two_leg_tuning.py | 실체결0/완료1/완료6/완료8+held, bad-source/비용/owner; research/promotion 분리 |
| B2–B3 | 같은producer·기존entry spot/episode prospective helper | 최대2profile×2축·baseline context 재사용, 순차next-entry/custody·partial/held/self/no-fill·비용 후paired |
| B4 | trading/low_price_two_leg/policy_runtime.py·기존candidate writer | source-schema v9/v10·research-only rejection·strict promotion proof·single frozen selection |
| B5 | 기존paired_search_handoff·Daily/EV/runtime/strict reader | generation/diagnostic 소실 검출·promotion0에서도연구결과전달·applied/held불변 |

실제 code/runtime contract 문자열은 English ASCII를 사용한다.

Implementation→review→fix→re-review→targeted pytest/import/compile·wrapper 영향시bash-n·diff-check→허용된 최소 native 재생성 순서로 진행한다. 기존테스트에 회귀를 추가하고 새test framework/root module을 만들지 않는다. 변경 없는 lock/loader/wrapper의 기존receipt는 source equivalence 검증 후 재사용한다. 문서는 link/owner/authority와 print-only parser를 검증하며 Project/Calendar는 실행하지 않는다.

종결은 세 가지로 보고한다. (1) 연구 착수 구조가 분리되고 실제 후행에서 소비됨, (2) 캐시/actual 원천으로 가능한 비교 수치가 제시됐거나 정확한 복구 불가 gap으로 소진됨, (3) 적용 가능한 승격 또는 검증 보존 정책이 다음 정상 장전 소비 경로에 준비됨. 보존만으로 EV 개선 목표 완료라고 하지 않는다. 양수 정책을 만들려고 기준을 낮추거나 데이터를 새로 만들어내지 않는다.

성능은 2profile/cache/두 축/단일 선정의 범위 제한과 동일 입력 checkpoint 재사용으로 관리한다. 시간 단축이 어려우면 진단 상세를 줄이고 남은 대상을 pending/carry로 표시한다. Floor/비용/holdout/custody를 줄이는 성능 최적화는 금지한다. Source gap의 재시도 조건은 새 입력/원천 수리이며 변동 없는 raw/cache 재구축은 하지 않는다.

## 10. 최종 산출물과 Acceptance

- Source9/17 또는 새로 확정한 native source의 profile별 research/promotion 표, 전체 경로 CF 비교 가능 수치와 실제 비용 cohort, 각 null의 원인/복구 가능성/producer/closure를 기존 JSON/MD에 남긴다.
- 두 우선 대상이 source 진단만으로 끝나는 경우도 missing applied/bar/cost/capture/BBO/capital 중 최초 경계와 증거를 명시한다. 탐색 조건 미달0을 경제 분석 완료로 취급하지 않는다.
- 선정 보류일에도 기존 정책의 valid dated candidate를 발행하고 research 결과의 current hash를 마지막 consumer에 전달한다. 소비된 동일 날짜 파일은 덮지 않는다.
- 검증된 joint 개선은 실제 unused independent window·execution/capital/authority/floor를 갖춘 단일 정책에 한한다. 신규 실현 개선은 actual applied version의 COMPLETED/full-cost 성과로 확인한다.
- 계획 수립 현재는 후속 code/정책/서비스/원천 재생성 변경0이다. 이후 구현 증거와 자연 적용·경제성 Acceptance를 분리해 기존 stable ID로 보고한다.

## 11. 이번 문서 검토

자체 리뷰→보완→재리뷰에서 카카오8leg 설명, exploration/promotion floor 분리, held 거래 누락 금지, 과거 capture 부재와 cached CF의 증거 등급, unit quantity1과 실제 순익 구분, v9/v10 reader 결속, 단일 미래 후보와 마지막 consumer 연결을 점검했다. Relative link 검증과 print-only parser의 OPEN stable owner1개를 확인했다. 후속 코드 테스트·report 재생성·commit/push·배포는 계획 수립 범위라 실행하지 않았다. 양수 수치나 복구 불가 과거 원천의 해소를 보장하지 않는다.

## 12. LP-B0–B6 실제 구현 종결 및 수동 청산 정정

기존 tuner에 applied 수동 receipt의 역사 projection, research admission과 strict promotion 분리, 최초2profile/두 기존 축의 bounded 탐색, report v10 및 v9 intake 보존, candidate v4 source binding, compact diagnostic handoff를 구현했다. 기존 원래 목표 carry continuation 모델은 보조 price-touch CF 진단으로만 재사용하며 primary ranking/승격에는 사용하지 않는다. Target/quantity/lookback/비용/floor/authority/관측 수집/서비스 개수 변경0이다.

Native9/17 재생성: research2profile/서로 다른3축 후보, primary resolved0(모델 carry), 보조 CF resolved3, 동시 개선0, mutation0. 카카오 보조 ΔEV +0.005356%p이나 Δ순익/day -19.51228071원이다. 영원무역 drawdown/near-low의 ΔEV는 각각 -0.000036/+0.000236%p, Δ순익/day는 -0.77982456/-1.10140351원이다. 모두 unit quantity1/calibration57일/실행 미확정 CF이며 실제 순익으로 환산하지 않는다. 기존 policy가 이번 범위에서 더 높은 일별 순익이다. 숫자가 계산됐다는 사실과 실제 경제 개선은 구분한다.

Applied manual journal13행·20leg를 전체 기존 owner에 보정했고 카카오 오전3leg/정오2leg의 역사 unresolved가0으로 바뀌었다. 역사 실제 비용 후 합계는 오전 -30,034.049원, 정오 -64,288.249원(고정 비용 추정)이며 좋은 거래만 보존하지 않았다. Kakao late-morning8/18의 두 역사leg는 exact closing receipt가 없어 원천 미확정으로 유지하되 current actual epoch unresolved0 및 CF held1과 구분한다.

검증·후행 소비·미래 immutable 배포와 외부 whole-chain blocker는 [종결 리뷰](../audit-reports/2026-09-19-low-price-exploration-manual-close-implementation-review.md) 및 `tmp/low-price-exploration-manual-close-20260919/`를 따른다. LP-B 구현사항은 닫고 자연 source/PID/applied-version EV는 동일9/21 stable ID로 유지한다. 양수 CF 또는 신규 실제 개선을 얻었다고 하지 않는다.

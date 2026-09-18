# 저가주 2차 진입 확장 후보 연구 — EV·일별 순익 개선 상세계획

작성: 2026-09-18 KST. 상태: **구현·반복 리뷰/보완·검증·제한 재평가·commit/push·소스 배포 및 장후 결과 갱신 완료. 미래·실제·joint 경제성 acceptance는 OPEN**.

## 1. 목적·현재 결정·소유권

목표는 비용 차감 EV와 유효 관측일당 순익을 함께 개선하는 **서로 다른 정책**을 찾는 것이다. 첫 단계는 자기 비교와 미청산 비교를 경제성 개선 집계에서 분리하는 평가 수리다. 그 뒤 기존 후보 grid 안에서 신호·체결·목표가의 영향을 분해하고, 학습 구간에서 고정한 후보만 검증한다. 개선이 입증되지 않으면 기존 정책을 보존한다.

최초 요청은 상세계획 작성이었다. 2026-09-18 후속 사용자 지시는 LP0–LP6 구현·반복 리뷰/보완·검증과 완료 후 commit/push·배포·장후 결과 갱신을 승인했다. 다음 문단의 미실행 경계는 최초 계획 작성 단계의 이력이며 후속 구현·제한 재평가 권한을 막지 않는다. 신규 실주문·임의 env/lock/threshold/provider/quantity/cap 변경·전체chain 재실행은 승인 범위로 확대하지 않는다.

최초 계획 작성 시점에는 추가 시장/API/provider/계좌 조회, 연구 재실행, 코드 수정, 정책 발행, commit/push, 배포, 프로세스 기동, env/lock/threshold/quantity/cap 변경과 주문은 실행하지 않는다. 앞선 재실행 권한·queue 재개 지시보다 이번의 **추가 조회·전체 재실행 중단**을 우선한다. 후속 구현·제한 재평가는 그 작업의 지시와 기존 운영 계약에 따라 실행한다.

- 원칙: [Plan Rebase §1–§8](../plan-korStockScanPerformanceOptimization.rebase.md). clean baseline은 `2026-06-05T00:00:00+09:00` 이후이며 remote 비교값을 제외한다.
- 실행 owner: [9/18 checklist](../checklists/2026-09-18-stage2-todo-checklist.md)의 `LowPriceExpandedResearchRepair0918` 하나를 유지한다. 아래 LP0–LP6은 상세 package이며 별도 OPEN owner가 아니다. 날짜 이관 때 stable ID·Acceptance·History를 보존한다.
- 기존 근거: [입출력·추천 handoff 보완 receipt](../audit-reports/2026-09-18-low-price-expanded-research-repair.md), [전체 연구 재계산 기록](../audit-reports/2026-09-18-low-price-full-research-rerun.md), [기존 정책 비교 JSON](../../data/report/postclose_research_successor_20260917_20260918/low_price_existing_logic_full_comparison_2026-09-17.json).
- 장후 결과 지침은 이번에 호출하지 않는다. 이 계획은 모니터링·복구 절차를 실행하는 지시가 아니다. README/runbook/Plan Rebase/prompt/AGENTS를 수정하지 않는다.

여기서 2차 진입은 저가주 전용 machine의 두 initial entry leg 중 두 번째 다리다. Main AVG_DOWN, 폐기된 PYRAMID, widget/manual 보유분 추가매수와 혼합하지 않는다. 기본 두 다리 각10주와 별도 승인 수량·기존 재고 custody는 원 owning contract를 유지한다. 연구의 단위 다리 금액을 실제10주 주문 순익으로 단순 환산하지 않는다.

## 2. 기존 결과 정정과 배포 코드 확인

### 2.1 현재 해석

| 확인한 항목 | 유효한 해석 | 계획에 반영할 조치 |
| --- | --- | --- |
| 1,020프로필·기존로직64·수치 비교13 | 프로필 수, 서로 다른 정책 수, 성숙 경제성 비교 수는 다른 분모다 | inventory→정책 identity→후보 검증→경제성 유효성의 단계별 수를 분리 |
| 종전 성숙 비교3: 두산에너빌리티 늦은오전·팬오션 늦은오전·SK텔레콤 오전 | 사용자 정정에 따르면 모두 기존·후보 매개변수가 동일한 자기 비교다. 세 건은 기존 정책 보존 기록 | 이 세 건을 독립 개선 비교 분모·성공/실패 집계에서 제외 |
| 팬오션 오전 후보 EV `+0.280032%`, signal4/완료5/held1 | 기존 EV·ΔEV는 null, 기존 carry-in1 및 custody 미해결. 후보 수치도 완료 부분의 모델 지표 | 부분 실현 차이만 진단으로 표시; 종합 경제성 우위 미확정 |
| 팬오션 오전 후보 `8.211875 KRW/일` vs 기존 실현0 | 기존16관측일 모두 custody 차단. 정상 무거래의0과 다름 | 원 실현값은 보존하되 경제성 Δ순익·개선 판정은 null/보류 |
| 팬오션 점심 EV `0.070402→0.222456%` | 후보1signal/1완료, 빈도 `0.375→0.0625/일`, 단위 모델 Δ순익 `-1.3525 KRW/일` | 높은 거래당 지표만으로 순익 개선 추천하지 않음 |
| 학습 순익이 낮은 후보가 선택된2건 | 사용자 점검 범위에서는 기존 정책이 미청산 손실 가드로 제외된 결과 | 순위 오류로 단정하지 않고 baseline의 탈락 이유·후보 rank를 함께 제시 |

소규모 비교 JSON에는 여전히 `valid_mature_comparison_count=3`와 `net_profit_improved=true`가 있다. 이 필드는 구 평가 계약의 산출물이며 새 판단의 근거로 재사용하지 않는다. **“다른 정책을 충분히 비교했으나 EV·일별 순익 개선0”은 철회한다. 독립적인 개선 여부는 아직 확정할 수 없다.** 원본 파일·원 hash·추천 ledger는 보존하고 후속 구현 때 successor 분류를 발행한다. 세 자기 비교의 제외만으로 다른64프로필 전체의 신규 유효 분모를 추정하지 않는다.

### 2.2 읽기 전용 확인 범위

이번 계획에서는 [선택 manifest](../../data/runtime/runtime_release_selection.json)를 확인했다. 확인 시 selected root는 `/home/ubuntu/KORStockScan-runtime-releases/low-price-postclose-source-resume-20260918`, source commit은 `2a1388c6929e3c4cd037d507140939fb4c0bb513`였다. manifest의 `actual_pid_consumed=false`는 현재 PID 소비 성공의 증거가 아니다. 읽기 전용 systemd 조회는 저가주 auto-expansion unit의 active/MainPID41757과 별도 `low-price-research-repaired-20260918` WorkingDirectory를 표시했다. `/proc/41757/cwd` 확인은 실패하여 해당 PID의 현재 코드 소비를 새로 확정하지 않았다. selector·서비스 설정·actual PID 소비는 별개다.

실제 selected root의 다음 구현을 읽어 workspace와 대조했다.

| 구현 소유 파일 | 확인한 동작 | selected SHA256 |
| --- | --- | --- |
| `src/engine/monitoring/low_price_two_leg_entry_spot_research.py` | baseline을 grid에 포함; 학습 순익/관측일 우선 rank, robust score·EV·완료 수 순 tie-break; 1위만 holdout 평가 | `af2a51a6c9b894f18ebe07363f0ca536f64686e5df21d3591b948ba0e101bb65` |
| `src/engine/monitoring/low_price_two_leg_expanded_candidate_research.py` | profile checkpoint, 추천 생성/검증, 보고서·추천 소비 계약 | `08385bca6ef8e40b38eb231b8abcae20c5208056de7d71ef5eb995f689b4fba2` |
| `src/engine/automation/low_price_two_leg_auto_expansion_policy.py` | 자동 확장은 `new_symbol`/`existing_symbol_time_extension`만 지원; 기존로직 개선 lane은 지원하지 않음 | `be391e58c7ba101e8330d2db283629c1bb54eec9485463b88e37803e8cff0a37` |

앞의 두 파일은 workspace와 selected 코드가 달랐고 정책 consumer는 같았다. 따라서 후속 구현은 workspace diff를 배포 기준으로 간주하지 않고 clean managed source와 병행 변경을 먼저 대조한다. 이번에는 116,045byte 비교 JSON을 읽었으며 86,225,855byte 연구 원본은 stat만 확인했다. 큰 원본 전체를 다시 파싱하거나 grid를 재계산하지 않았다. 세 건의 매개변수 동일성은 사용자 제공 정정을 채택하고, 후속 LP0에서 원 policy identity에 결속해 검증한다.

확인한 코드의 추가 제약:

1. `paired_economics`는 날짜·비용·replay 계약 일치와 실현 순익 차이로 `net_profit_improved`를 만든다. carry-in/held/custody 미해결과 정책 동일성은 개선 판정의 필수 조건이 아니다.
2. `_summary`의 현 `notional_weighted_ev_pct`는 완료 다리 순익을 모든 시도 다리의 단위 entry notional로 나눈다. 무체결·미청산까지 분모에 들어가므로 완전 청산 거래의 평균 EV와 구분해야 한다.
3. selected `_advance_candidate_day`는 이월 HELD의 mark·MAE·보유 bar를 갱신하지만 다음 날 target 도달을 COMPLETE로 전환하지 않는다. 후속날 원천 추가만으로 이 replay carry가 자연 청산된다고 가정할 수 없다.
4. live machine에는 `_submit_target`, `_reconcile_target`, `_roll_date`와 별도 custody/adaptive exit 경로가 있다. 연구의 이월 보수 처리와 live order 완료 의미가 다를 수 있다. 이를 곧바로 live 결함 또는 다음 날 bar-touch 청산 허용으로 단정하지 않는다.

## 3. LP0 — 평가 모집단·정책 identity 고정

먼저 이미 저장된 원천과 기존 결과의 manifest를 동결한다. target date는 `2026-09-17`을 유지하고 이후 거래일 성과와 섞지 않는다. 모집단204종목/1,020프로필·기존로직64, 원천 유효197/격리7, calibration 전체 clean prefix와 latest16거래일 holdout, 원 grid·비용·표본 floor를 보존한다. profile 수를 grid policy 수로 보고하지 않는다.

정책 identity는 symbol/profile/session/venue/route·stage·신호 version과 실제 effective scan window/lookback/drawdown/near-low/offsets/유효bar/target·execution/cost/quantity 계약의 canonical hash로 정한다. 추천 ID, 새 작성 시각, 다른 dictionary 순서와 다른 source commit만으로 새 정책이 되지 않는다. baseline은 target-date applied policy와 hash가 우선이며 compiled baseline은 연구 비교용으로 별도 표시한다. 과거 실제 적용을 입증하지 못한 compiled 비교는 live 개선 추천의 근거가 아니다.

산출 필드: `baseline_policy_identity`, `challenger_policy_identity`, `is_distinct_policy`, `candidate_changed_fields`, `baseline_provenance_status`, `evaluated_candidate_basis`. 최종 `selected`가 baseline으로 carry된 경우에도 원 calibration challenger와 그 탈락 사유를 보존한다.

분모를 `inventory_profiles`, `evaluated_grid_policies`, `distinct_calibration_eligible_policies`, `holdout_tested_challengers`, `incumbent_retained_profiles`, `valid_distinct_economic_pairs`, `censored_pairs`, `sample_insufficient_pairs`, `source_excluded_profiles`로 분리한다. profile별 종결 분류는 하나, 후보별 검증 수는 별도로 대사한다. `no_robust_candidate`, `not_tested`, `hold_sample`, `custody_censored`를 `measured_no_edge`로 바꾸지 않는다.

Acceptance: 세 자기 비교가 incumbent 보존으로 분류되고 독립 분모에서 제외됨; 정책 동등성/출처/원 추천 ID·hash 대사; grid/profile/비교 분모가 각 manifest와 일치; 원본 변경0.

## 4. LP1 — 0·null·미청산·EV 정의 수리

### 4.1 상태와 비교 가능성

| 상태 | 실현 ledger 값 | 경제성 비교 처리 |
| --- | --- | --- |
| source-valid·flat·유효 시도 없음 | 확인된 실현0 | 일별 순익0 유효; 거래 EV null. 후보와 일별 참여 효과 비교 가능하지만 양측 거래 EV 우위로 부르지 않음 |
| 유효 주문 모델의 전량 no-fill·flat | 확인된 실현0 | 기회/체결률 진단 및 flat day 순익0. 청산 EV 표본으로 추가하지 않음 |
| partial fill 또는 완료+HELD 혼합 | 완료분 비용차감 실현값 | 부분 실현 진단만 유효; 미청산 포함 종합 ΔEV/Δ순익 우위 미확정 |
| carry-in HELD·custody 차단 | 해당 창의 신규 실현0일 수 있음 | 정상 무거래0과 분리; carry 원가·노출·평가손익 결손을0으로 대체하지 않음 |
| missing/invalid source·cost·terminal | 알려진 일부 ledger만 보존 | 비교 지표 null, 식별 가능한 row/window 제외 manifest |
| 양측 distinct·완료/비용 유효·custody 해결 | 비용차감 완료 결과 | 기존 표본·source·tail 계약을 통과해야 성숙 경제성 비교 |

`comparable_observation_window`, `comparable_policy_identity`, `comparable_terminal_economics`, `sample_floor_passed`를 각각 표시한다. 날짜 일치만으로 경제성 유효성을 선언하지 않는다. baseline/candidate의 held뿐 아니라 carry-in, `custody_resolution_required`, unresolved inventory/order/cost까지 확인한다. 둘 중 한 arm이라도 censoring이면 `economic_comparison_status`에 원인을 기록한다.

구 `net_profit_uplift_krw_per_observation_day`의 수치는 필요하면 `diagnostic_partial_realized_net_delta_krw_per_day`로 보존한다. 의사결정용 `economic_net_profit_uplift_krw_per_day`, `ev_uplift_pct_point`, `economic_superiority_confirmed`는 미확정이면 null/null/false다. 실제로 확정된 실현 ledger0 자체를 null로 덮어쓰지는 않는다.

### 4.2 지표 계약과 산식

| 지표 | 역할·산식 | 허용/금지 용도 |
| --- | --- | --- |
| `notional_weighted_ev_pct` | 완료+유효 비용/return인 다리의 `100×Σnet_profit/Σexecuted_entry_notional` | 새 의미는 version을 올리고 구 값을 보존. 모델과 actual 별도. 미청산 포함 종합 성과 확정 금지 |
| `equal_weight_avg_profit_pct` | 유효 완료 episode return 평균 | 다리 수로 episode 독립 표본을 부풀리지 않음 |
| `attempted_notional_realized_return_pct` | 구 산식 `100×Σ완료 순익/Σ시도 단위 notional` | 기존 결과 재현·진단용. 완료 거래 EV로 표시하지 않음 |
| `cost_adjusted_net_profit_krw_per_source_valid_observation_day` | 동일 사전 고정 유효 관측일의 비용차감 실현 순익합/일수 | flat 무거래0 포함, census에서 임의로 좋은 날만 제외 금지. censored면 부분 실현 진단으로 역할 제한 |
| `attempt_frequency`, `fill/completion_rate` | 관측일당 시도·leg별 체결/완료 수 | 순익 차이의 원인 진단; standalone EV 증거 아님 |
| `active_unrealized`, `held/carry`, `capital_exposure`, MAE·tail | 노출·source/custody·위험 진단 | 완료 순익/EV에 합산하거나 missing 비용을0으로 대체하지 않음 |

새 계약은 `metric_role`, `decision_authority`, `window_policy`, `sample_floor`, `primary_decision_metric`, `source_quality_gate`, `forbidden_uses`를 명시한다. EV는 `primary_ev`, 일별 순익은 동시 경제성 목표, 빈도는 `funnel_count`, 미청산은 `active_unrealized`, 결손은 `source_quality_gate`로 둔다. 연구 권한은 `source_only_no_runtime_or_order_authority`다. clean expanding calibration/latest16 holdout과 기존 family floor를 유지한다. 진단 지표에는 승격 floor를 부과하지 않는다.

모델 round-trip 비용은 canonical `0.23%`를 유지한다. 실제 성과는 exact broker notional·수수료/세금·fill/exit cost reconciliation을 사용한다. canonical 비용에 이미 포함된 요소를 다시 더하지 않는다. cost/stress contract가 없으면 임의 비용값이나 gross 값을 쓰지 않는다. 모델 `COMPLETE`와 실제 `COMPLETED + valid profit_rate/cost`를 별도 label/ledger로 유지한다.

일별 현금 실현 성과는 exit-date에 귀속하는 회계와 entry-cohort terminal EV를 분리해야 한다. holdout 시작 전 carry의 청산을 holdout 신규 거래 수익으로 바꾸지 않는다. 현 창은 baseline carry 때문에 거래할 수 없었다는 상태를 보존한다. 기간 현금 실현 비교는 opening inventory/cost/exit ledger까지 대사될 때만 유효하다.

Acceptance: 정상 무거래·no-fill·carry-only·부분완료·cost missing fixture가 서로 다른 결과; 팬오션 오전은 부분 실현 차이 유지/종합 우위 보류; 비용·분모·entry/exit 귀속이 원 ledger로 대사; finite/type/0/null 검증.

## 5. LP2 — 기존 정책 보존과 독립 challenger 선택 분리

현재의 “전체 학습1위→holdout1개”를 두 역할로 나눈다.

1. **운영 선택 역할**: baseline을 포함한 기존 eligibility/rank를 그대로 계산해 incumbent 보존 여부를 판단한다. 기존 정책이1위면 `incumbent_retained`이며 challenger 검증 성공이 아니다.
2. **개선 연구 역할**: 같은 전체 grid·학습 eligibility 안에서 baseline과 identity가 다른 **최상위1개**를 별도 challenger로 고정한다. baseline이1위여도 독립 challenger 존재·학습 순익/ΔEV·탈락 이유가 보인다. 적격 distinct 후보가 없으면 `no_distinct_eligible_challenger`다.
3. 후보 고정 manifest에는 학습 종료일·원천/정책/비용 hash·rank·eligibility·baseline 탈락 사유·변경 필드·평가 version을 남긴다. validation 결과를 보고2위·3위로 바꾸지 않는다.
4. 학습 rank는 현재의 관측일당 비용차감 순익 우선, robust score·EV·완료 수·안정된 tie-break를 출발점으로 보존한다. LP1 지표 의미가 변경되면 새 version의 학습 rank를 다시 만들고 구 rank와 구분한다. 낮은 순익 후보의 baseline 탈락 원인과 risk trade-off를 표시한다.

LP2 초기 범위는 독립1개다. top-K holdout 중 양수만 뽑는 기능은 넣지 않는다. 나중에1개 초과가 필요한 경우 calibration에서 후보 수·우선순위·다중비교 계약을 먼저 고정하고 새로운 검증창을 사용한다. 표본 floor·carry25%/worst-held 손실3%의 기존 eligibility를 임의로 낮추지 않는다. 경제성 확정과 초기 source-only 후보 관측을 별도 상태로 둔다.

현재 실행 gate의 학습 최소6signal/8완료leg, holdout 최소3signal/4완료leg, full-window 최소10완료leg를 명시적으로 대사한다. expanded `METRIC_CONTRACT`에는 학습 각 절반3완료leg도 선언돼 있지만, 읽은 selector의 `_calibration_sample_ready`는 full6/8만 검사한다. **선언 계약과 실행 gate의 불일치**를 LP2 검토 finding으로 남긴다. 진단 필드인지 필수 eligibility인지 원 owner에서 확정한 뒤 계약/version·consumer·회귀를 함께 맞춘다. 이번 계획만으로 half-floor를 묵시적으로 새로 강제하거나 삭제하지 않으며 기존261PASS를 이 불일치의 closure로 쓰지 않는다.

기존 9/17 holdout은 이미 사람과 코드가 관찰했다. 새 challenger 선택/rank 수정 후 이 창에서 얻은 결과는 **탐색적 재평가**다. 같은 창에서 parameter 조정을 반복해 확증 holdout PASS로 만들지 않는다. 확증은 후보 고정 후 아직 사용하지 않은 다음 적격 거래일 창 또는 원 계약의 독립 validation partition에서 수행한다. eligibility/latest16·기존 promotion guard를 우회하는 새 시간 분할은 만들지 않는다. 사용 이력을 검증할 수 없으면 source-only/hold 상태로 남긴다.

Acceptance: incumbent1위에서도 distinct challenger는 별도로 보임; identical/tie/적격 없음/guard 제외/selected carry 시 원 challenger 보존; candidate selection이 validation outcome을 읽지 않는 실제 producer 회귀; 검증 실패 후 후보 교체0.

## 6. LP3 — EV·일별 순익을 개선할 로직 가설

LP0–LP2 이후 기존 grid의 후보로 아래 가설을 비교한다. 아래는 실험 순서이며 특정 종목 매수 추천이나 수익 보장이 아니다. price-band/session별 비용·tick 비율은 기존 저장 원천에서 계산하고 추가 조회하지 않는다.

| 가설 | 기존 지원 후보·비교 방법 | 개선 경로 | 실패/보류 조건 |
| --- | --- | --- | --- |
| H1 비용 대비 작은 target 보완 | 같은 signal·offset/validity에서 native `((0,-1),5,2)` vs `((0,-1),5,4)` | 완료당 net margin 증가 | 완료 빈도 감소·HELD 증가·일별 순익 감소면 개선 아님 |
| H2 두 다리 가격 배치 보완 | 같은 signal에서 native `((0,-1),5,4)` vs `((-1,-2),5,4)` | 체결 원가·MAE·순 EV 개선 | 체결/참여 급감으로 일별 순익 감소, 주문가/잔량 모델 결손 |
| H3 주문 유효기간 보완 | 같은 signal에서 native `((0,-1),5,4)` vs `((0,-1),3,4)` | 늦은 불리한 체결·노출 감소 | 정상 완료 기회 손실·빈도 감소가 순익 감소로 이어짐 |
| H4 진입 signal 품질 보완 | 동일 execution tuple에서 기존 lookback/drawdown/near-low/window grid | 과도한 하락 중 진입 감소·완료 빈도/순익 개선 | 좁은 시간/소수 양수 거래만 선택, 광범위 적용 근거 부재 |
| H5 signal·execution의 결합 효과 | 기존 native 전체 tuple만 사용, calibration에서 최종 한 정책 고정 | 신호 품질과 비용/빈도의 균형 | 축별 진단 결과를 조합해 native에 없는 policy를 생성하거나 holdout을 재선택 |

tick 이동은 기존 `tick_utils`의 실제 price-band 규칙으로 계산한다. `target_price/entry_price-1`과 비용0.23%의 관계를 표시하되 수익률 부호만으로 target4를 승격하지 않는다. 기존 profile 전용 extension은 해당 profile scope에서만 사용한다. grid 밖의 임의3tick·offset 조합, 시간창 확장, stop/forced exit·adaptive exit 신규 도입, 수량 증가·새 종목 서비스 생성은 이번 package에 넣지 않는다.

2차 다리 기여는 각 episode에서 first/second의 attempted→no-fill/full/partial→completed/held와 순익·노출을 분리한다. 공유 budget/order/custody guard 때문에 두 다리 결과가 독립이 아님을 유지한다. 단위 touch 모델이 실제10주 잔량·partial fill을 설명하지 못하면 해당 실제 성과 예측은 gap이다. first-leg-only 대안은 실제 supported policy·상태 모델이 있을 때만 비교하며 없는 arm을 합성하지 않는다.

H1–H4는 원인 진단이다. 그중 좋아 보이는 결과를 validation에서 조합하지 않고, 전체 native grid의 calibration 선택 규칙으로 H5 정책 하나를 고정한다. 일별 순익을 `시도빈도×완료/체결 구조×완료당 순익`으로 설명할 때 partial·carry·반올림 잔차를 별도 대사한다. 높은 EV/낮은 일별 순익은 `ev_only_gain`, 반대는 `participation_only_gain`, 둘 다 개선은 `joint_economic_gain`으로 구분한다.

Acceptance: 정책 차이와2차 다리 기여가 재현됨; 동일 source/cost/시간 상태에서 비교; EV·일별 순익·체결빈도·미청산 위험 동시 보고; 승격은 원 family guard에 따르며 diagnostic state만으로 live 연결0.

## 7. LP4 — carry의 구조적 검증 가능성 판정

selected replay에서 HELD는 다음 날 mark만 갱신한다. 따라서 팬오션 baseline carry의 경제성은 **재실행 반복이나 오래 기다리기만으로 이 모델에서 닫히지 않는다**. 원 owning custody/order receipt와 frozen target/exit policy를 읽어 다음 중 어느 경로인지 판정한다.

- 원 durable execution/cost terminal을 회수할 수 있으면 baseline 당시 basis·수량·정책·exit-date에 정확히 연결한다. 회수한 과거 실현값을 새 로직의 증분 수익으로 보고하지 않는다.
- 기존 frozen exit가 다음 날에도 같은 owner·route/session·기한에서 유효하며 저장 source로 재현 가능한 경우에만 순수 연구 custody transition 보완을 설계한다. bar high touch만으로 실제 target 주문 유효·체결을 단정하지 않는다. window boundary를 봉인하여 뒤 날짜 청산이 앞 calibration/holdout snapshot을 수정하지 않게 한다.
- 주문 취소/만료·장간 route·partial·adaptive enrollment·original owner가 불명확하면 `unsupported_carry_exit_contract`/`custody_censored`를 유지한다. 과거 종료창은 영구 제외 사유를 남기고, flat/정책 출처가 유효한 다음 전향적 cohort를 새로 고정한다. 좋은 결과를 위해 과거 carry를 삭제하거나 flat 시작으로 다시 돌리지 않는다.

LP4는 연구 모델과 실제 owner 의미의 차이를 닫는 작업이다. live exit/REG/REMOVE/account/order/continuation을 수정해야 한다면 그 부분은 별도 범위·권한이다. 해당 후속 구현 전에는 [Kiwoom API Data Contract](../kiwoom-api-data-contract.md)의 Official Kiwoom Reference Gate에 따라 현 upstream SHA·paths·retrieval time을 다시 확인한다. 이번 계획은 API 프로토콜 변경을 하지 않았으므로 과거 official reference를 현재 확인 receipt로 재사용하지 않는다.

Acceptance: recoverable/maturity/unsupported/irrecoverable 원인을 분리; owner·입력·다음 조치·closure가 명시됨; 불명확한 carry 청산 합성0·기존 guard/custody 변경0. 재현 불가능한 과거는 excluded로 닫을 수 있으며 복구 성공을 강제하지 않는다. ETA는 근거 없으면 null이다.

## 8. LP5 — 제한 재평가·cache·최종 소비 연결

### 8.1 재평가 순서와 상한

후속 구현·리뷰·validation이 닫히고 제한 재평가 지시가 있을 때만 실행한다.

1. **분류만 갱신**: 기존 결과와 policy identity로 자기 비교·censored·source/sample 상태를 successor에 분류한다. 원천/API0·grid replay0. 분류와 산식 수리를 새 alpha 연구로 세지 않는다.
2. **지표만 재집계**: 필요한 완료 leg/원 cost/notional이 기존 결과에 있으면 LP1 지표를 재집계한다. 필요한 입력이 없으면 null/gap이며 추가 조회하지 않는다.
3. **선택 변경 profile만**: 기존로직64 중 calibration 저장 결과로 distinct1위를 확정할 수 있는 profile을 manifest로 고정한다. shortlist 저장이 잘려서 distinct 후보가 누락될 수 있으면 그 profile의 기존 source·전체 native calibration grid를 재평가해야 한다. 저장 top10을 전체 grid로 간주하지 않는다.
4. **검증 pair만**: 고정한 distinct1개+incumbent의 검증 결과가 계약 일치 cache에 있으면 재사용한다. 없을 때만 그 pair와 필요 clean custody prefix를 재생한다. 초기 상한은 profile당 distinct challenger1개, 대상은 기존로직 최대64다.1,020프로필/전체chain/widget queue 재개로 확대하지 않는다.

raw 원천 hash·source generation/범위·scope·split·baseline identity·grid hash·cost version·selector/metric/replay version·custody basis가 cache key에 들어간다. 분류 변화만이면 검증된 raw/leg kernel을 보존할 수 있지만 구 `net_profit_improved`·구 EV/rank/profile-selection checkpoint는 새 계약의 결론으로 재사용하지 않는다. 기존 `_valid_profile_selection`은 baseline/selected 중심이므로 challenger identity/validation/상태 검증까지 함께 보완해야 한다.

시작 전에 `selected_profiles`, `evaluation_pairs`, `reused_artifacts`, `invalidated_checkpoints`, `required_missing_inputs`, expected compute count를 고정한다. 알려진 source7종목·integrated-aftermarket 결손을 재요청하거나 격리 이유를 지우지 않는다. 진행 중 source는 덮어쓰지 않는다. 64MiB 초과/growing JSONL은 stat→manifest/streaming/bounded read만 사용한다. 경과시간/CPU/RSS·hit/miss를 측정하며 실패는 source_waiting/source_quality/custody/model/compute로 구분하고 EV0/완료 처리하지 않는다.

### 8.2 기존 producer→consumer 경로

| 경로 | 필요한 후속 수정·검증 |
| --- | --- |
| entry spot `paired_economics`/`select_profile_spot` | LP0/LP1 state·LP2 incumbent/challenger 분리, 경제성/진단 필드 일관성 |
| expanded profile checkpoint→report→추천 validator | 새 version/hash/terminal/type 검증, 원 challenger 보존, self/censored가 확정 개선 추천으로 통과하지 않음 |
| Markdown/Telegram rendering | incumbent 보존·독립 검증·부분 실현/종합 미확정 표시. 이번에는 메시지를 보내지 않음 |
| auto expansion publisher/load | 지원 lane·원 floor·flat/no-held/custody·날짜/해시·동결·수량/owner 유지; unsupported 기존로직 lane을 자동 등록하지 않음 |
| `research_closed_loop`/control tower/summary intake | 새 comparison status·EV 정의를 실제 소비 위치에서 검증. 직접 연결이 없는 consumer에는 이름만으로 통합 claim을 만들지 않음 |
| dated policy→preflight/loader→PID→자연 outcome | 별도 승인·기존 stage owner 경로. workspace PASS나 successor 생성으로 현재 동결 정책·실제 적용을 주장하지 않음 |

producer/report/consumer는 새 schema와 metric contract version을 일관되게 검증한다. legacy 결과는 진단 조회로 읽을 수 있지만 legacy 추천을 새 경제성 PASS로 자동 승계하지 않는다. validator가 기준0·missing을 `or 0`로 통과시키지 않는지 확인한다. same-date publication conflict를 우회하지 않는다. source-only 평가 수리와 기존 정상 승인 carry 정책 유지 의미를 구분하여 deployed 정책을 임의 폐기하지 않는다.

새 production 모듈은 우선 만들지 않고 기존 `monitoring` 연구 producer·`automation` 정책 consumer·`src/tests`를 수정한다. 분리가 필요하면 먼저 주변 role/consumer·location gate를 확인하고 `src/engine` root에 새 파일을 두지 않는다. 별도 collector/job/cache/cron을 추가하지 않는다. 후속 wrapper/automation 운영 규칙을 바꾸면 operating docs와 checklist를 같은 변경으로 맞춘다.

Acceptance: 기존 source 불변·정확한 subset/pair/cost manifest; cache 오승계0; 신규 상태가 실제 마지막 consumer까지 전달; 현재 동결 policy/service/selector·원 ledger 변경0. 같은 날짜 widget peer·과거 cash/inventory/same-stage가 없으면 joint EV/net은 계속 null이다. 독립 연구의 분류 수리를 joint 자본 승인 완료의 선행조건으로 불필요하게 막지 않는다.

## 9. LP6 — 검증·경제성 acceptance·후속 적용

### 9.1 후속 구현의 필수 회귀

| 검증 사례 | 예상 결과 |
| --- | --- |
| 동일 policy, dictionary 순서/작성시각만 다름 | distinct=false, incumbent 보존, 독립 개선 분모 제외 |
| baseline1위·distinct2위 / distinct 없음 | 각각 독립1개 고정 / no distinct; holdout 보고 후보 교체 없음 |
| baseline carry-only 실현0 / source-valid flat0 | 각각 종합 비교 censored / 일별 순익0 유효·거래EV null |
| candidate 완료5+held1 / carry-in가 holdout episode 밖에 있음 | 부분 실현 진단·종합 미확정, carry 노출 누락 탐지 |
| EV상승·빈도 감소·일별 순익 하락 | ev_only_gain, joint_economic_gain=false |
| missing/NaN/Infinity/bool 비용·금액·count / 다른 날짜·cost | null/source-quality fail,0/성숙 비교로 대체 없음 |
| guard 제외 baseline 때문에 낮은 학습 순익 후보 선택 | 순위·eligibility·탈락 이유 표시; rank 오류와 구분 |
| 구 profile checkpoint/구 metric hash/새 challenger | 결론 cache 무효화·kernel 조건부 재사용 |
| self/censored/미지원 lane→publisher/load | 경제성 확정 추천 거부, live authority0, 기존 custody 보존 |
| boundary 후 carry mark/terminal 변경 | 이전 snapshot 불변·exit-date/entry-cohort 별도 귀속 |

실제 source→정책 선택→추천 writer/read/validator→정책 consumer fixture를 사용한다. 구현과 같은 산식을 복사한 테스트만으로 닫지 않는다. relevant tests는 기존 `test_low_price_two_leg_entry_spot_research.py`, `test_low_price_two_leg_expanded_candidate_research.py`, `test_low_price_two_leg.py`, 실제 영향이 있으면 `test_research_closed_loop.py`를 대상으로 좁힌다. Python compile, `git diff --check`, 문서 print-only parser를 수행한다. wrapper 수정 시에만 `bash -n`/계약 회귀를 추가한다. real order/provider 테스트·전체 research/postclose suite 재실행은 하지 않는다.

### 9.2 완료 상태

1. **평가 수리 완료**: 자기 비교·미청산·0/null·metric/version·consumer 회귀가 닫히면 완료다. 양수 EV·새 추천·실거래 발생은 수리 완료 조건이 아니다.
2. **연구 우위 확인**: distinct 후보의 독립 validation에서 source/표본/terminal/cost가 유효하고 ΔEV>0·Δ일별 순익>0·tail/carry/capital/stress의 원 family 계약을 통과해야 joint gain이다. 양측 completed sample이 없는 정상 no-trade baseline은 별도 참여/순익 효과이며 paired trade EV 우위로 부르지 않는다.
3. **미확정/측정 no-edge**: sample/cost/source/custody 결손은 hold/gap다. 유효한 distinct 검증에서 개선이 없을 때만 measured no-edge다. 소수 pair로 전체 grid/전체 저가주의 no-edge를 주장하지 않는다.
4. **실제 적용**: 기존로직 개선 lane은 현재 auto expansion 미지원이다. 연구 PASS만으로 서비스를 등록하거나 live 기존 정책을 바꾸지 않는다. 후속 live 적용 지시가 있을 때 실제 기존 policy owner·mapping/bounds·같은 stage canary·rollback·immutable release와 dated PREOPEN·PID 소비를 별도로 닫는다. 지원되는 정상 bounded family에 불필요한 매일 수동 승인 gate를 추가하지 않는다.
5. **실제 EV·일별 순익 개선**: 적용 code/policy/version/hash에 결속된 실제 full/partial·owner·venue/session·entry/exit/cost ledger와 rolling/cumulative 또는 사전 post-apply 창을 평가한다. 적용/미적용 cohort·market regime·노출/거래일 분모를 맞추며 actual 표본 없으면 null/OPEN. 모델 touch EV를 실현 이익으로 바꾸지 않는다.

rollback은 기존 severe loss·order failure·provenance/custody 손상·동일 stage 충돌·hard/protect/emergency stop 지연의 원 계약을 따른다. edge 없음/소표본은 baseline 보존·hold이며 hard safety 완화나 폐기 family 복원 이유가 아니다.

## 10. 단계별 실행·종결 표

| 단계 | 선행조건 | 결과물·종결 기준 | 막힐 때 다음 조치 |
| --- | --- | --- | --- |
| LP0 | 기존 artifact·target-date baseline | identity/census manifest, self 비교 제외·분모 대사 | 원 policy receipt 결손 표시; compiled 연구와 분리 |
| LP1 | LP0·원 완료/cost 결과 | 0/null/censored/EV 지표 계약·source→consumer 회귀 | missing 비용/terminal null·격리 manifest |
| LP2 | LP1·전체 calibration 후보 근거 | incumbent+distinct1개 freeze manifest | shortlist만으로 전체 rank 불가면 필요한 profile만 재평가 범위 제시 |
| LP3 | LP2·native tuple·source | EV·빈도·순익·2차 다리·risk 가설 진단 | 소표본/체결 모델 결손은 hold/model gap |
| LP4 | carry 존재·원 exit/custody | 재현/회수/unsupported 경로와 closure | irrecoverable 과거 제외·전향적 cohort, ETA null |
| LP5 | 리뷰/회귀 closure·제한 재평가 지시 | subset successor·cache manifest·실제 consumer handoff | 새 조회 없이 missing/wait 유지; 전체chain 재개로 확대 금지 |
| LP6 | 독립 validation·원 family gate | 연구 확정/미확정/no-edge 분리; 실제 적용/경제성은 별도 receipt | 미지원 live lane·PID/joint/cost blocker의 원 owner 유지 |

일정은 현재 checklist의 같은 stable owner에서 관리한다. 표본 성숙·carry 복구·독립 검증의 완료 날짜는 원천 없이 약속하지 않는다. 상세계획 자체는 parser/link/owner/authority·review/fix/re-review 검증으로 닫고, 위 구현 acceptance를 완료로 표시하지 않는다.

## 11. 최초 문서 변경 검증 이력

평가 분모·0/null·carry 경계·후보 선택·cache/schema 소비·지원 lane·runtime 권한을 자체 리뷰했다. 검토 중 같은 문서의 동시 보완을 보존하고 최신 내용으로 재리뷰했다. selected 세 파일의 SHA256과 workspace 차이, 지원 lane, 팬오션 오전의 부분 완료/미청산 수치를 기존 코드와 작은 비교 artifact로 대사했다. PID 조회의 확인 한계를 보완했다.

로컬 링크7개와 당일 단일 OPEN owner/parsed owner 각1개를 확인했고 print-only backlog parser·`git diff --check`를 통과했다. 문서만 변경하여 pytest/compile·provider/API 호출·연구 재계산·policy 발행·배포·재시작·외부 sync는 생략했다. 구현·독립 검증·joint 및 실제 손익 acceptance는 LP0–LP6에 남아 있다.


## 12. 후속 구현·검증 경계

후속 사용자 지시에 따라 기존 연구 producer·prospective/policy consumer를 수정하고 기존로직64개를 캐시 원천만으로 재평가한다. 최신 구현·검증·결과·배포 receipt는 [경제성 평가 수리 결과](../audit-reports/2026-09-18-low-price-distinct-economic-review.md)를 따른다. 최초 문서 단계의 조회/재실행 중단·문서만 검증 문구는 당시 이력이다.

완료 다리 원가 EV와 구 시도 원가 수익률을 분리하고, 정상 flat0의 참여·순익 개선은 `participation_net_profit_confirmed`, 양측 완료 EV·일별 순익 동시 개선은 `economic_superiority_confirmed`로 구분한다. 정상 flat0을 새 경제성 PASS의 baseline EV0으로 바꾸지 않는다. 기존로직 개선 추천은 양측 비교가 성숙할 때만 검토 대상으로 전달하며 unsupported live lane을 자동 등록하지 않는다.

half sign과 half3 선언의 정리는 과거 proxy selector의 diagnostic 계약에 한정한다. 별도 등록 prospective owner의 기존 각 학습 절반3완료leg·full10·holdout3signal/4leg guard는 그대로 유지한다. 이 scope 구분으로 기존 floor를 완화하거나 과거 승인/격리 profile을 재활성화하지 않는다. HELD carry는 관찰 자료만으로 청산을 합성하지 않는 원 계약을 유지하고 구조적으로 지원되지 않는 종료를 명시한다.

이번9/17 검증창은 이미 관찰했으므로 수치가 양수여도 탐색적 모델 결과다. 미래 독립 validation·실제 dated/PID consumption·정확한 완료 비용 손익과 joint 자본 입력은 별도 acceptance로 남긴다.

구현 source `581b17cb1` atomic push·12:27 KST managed release/기존unit 다음 실행 source 선택을 마쳤다. 기존 캐시64개156.6초의 결과는 distinct 성숙2·동시개선0·custody/terminal미확정55이다. 실제 검증·배포·단위 모델 수치·잔여 결손은 [최신 owning review](../audit-reports/2026-09-18-low-price-distinct-economic-review.md)를 따른다. H1–H4 전 조합 인과 분석을 추가 반복하지 않고 native 전체 calibration grid의 distinct1개 선택과 다리별 경제성/노출 진단으로 분석 깊이를 제한했다. 모델이 설명하지 못하는 carry terminal·실제 partial fill과 joint 입력은 null/gap으로 명시했다.

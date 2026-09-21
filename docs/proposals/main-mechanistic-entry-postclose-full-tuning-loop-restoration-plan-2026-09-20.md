# 메인 기계 진입판정 장후 전체 튜닝·다음 거래일 소비 루프 복구 계획

작성·재검토일: 2026-09-20 KST. 상태: 최초 실행·발행 루프의 배포 receipt는 §13에 보존한다. 후속 점검에서 경제성 연결·scope·선정·결손 분류의 잔여를 확인했으며 **전체 구조결손 해소는 미완료**다. 현재 보완 구현계획은 §14가 소유하고 PREOPEN/PID·자연 성과는 별도다.

## 1. 결정

메인봇의 `mechanistic_entry_adjudicator`는 진입 여부를 가장 먼저 결정하는 주 owner다. 이 owner의 임계치를 실제 후행 결과와 비용으로 재평가하고, 통과 후보 또는 incumbent 보존 결정을 다음 거래일 정책으로 발행하는 장후 작업은 필수 작업으로 복구한다.

재확인한 선택 릴리스 `compact-ai-exact-plan-reviewed-20260920-01a5889a7`(SHA `01a5889a7db3b1a2ed25f57b77c3734dc770699d`)에서는 `ai_action_outcome_calibration --ensure-economic-reference-only`와 compact AI 후보 평가만 실행한다. 전자는 비용 원천 준비만 하고 정책 발행을 금지하며, 후자는 기계가 이미 `ENTER_NOW`로 고른 사례의 AI 보조판정만 비교한다. 따라서 메인 기계판정 임계치의 전체 평가·후보 생성·발행이 매일 실행되지 않는다.

작업 디렉터리에는 전체 `ai_action_outcome_calibration --write --require-policy-publication` 호출이 남아 있지만, 선택 릴리스와 다른 대규모 변경·퇴역 코드도 섞여 있다. 이를 완성된 복구 초안으로 간주하거나 파일 전체를 복사하지 않는다. 구현은 최신 승인 release/commit을 기준으로 분리하고, 재사용 가능한 함수·호출만 최소 diff로 이식한다.

목표 우선순위는 다음과 같다.

1. 메인 기계판정 전체 평가가 매 장후 독립적으로 종결되는 구조를 복구한다.
2. 동일 기회·동일 비용·동일 후행 owner의 paired 비교로 비용 후 EV와 관측일당 순익 차이를 산출한다.
3. 검증된 후보만 다음 거래일 정책에 반영하고, 후보가 없으면 평가된 incumbent 보존 사유를 남긴다.
4. PREOPEN·메인봇 실제 소비와 다음 자연 결과가 다시 장후 평가로 돌아오는 폐쇄 루프를 검증한다.
5. compact AI 평가, 삼성 전용 `samsung_machine_entry_tuning`, 공통 진입 시점 `machine_entry_timing_tuning`과 역할을 섞지 않는다.

이 문서는 구현 계획이다. 작성 과정에서 코드·wrapper·정책·런타임을 변경하거나 장후작업/PREOPEN을 실행하지 않는다. 기존 계획 파일과 checklist의 `MainMechanisticEntryPostcloseLoopRestore0920`를 유지한다.

관련 기준은 [Plan Rebase](../plan-korStockScanPerformanceOptimization.rebase.md), [compact 통합계획](compact-ai-postclose-source-paired-evaluation-and-preopen-consumer-integration-plan-2026-09-19.md), [direct summary 계획](runtime-approval-summary-direct-evidence-handoff-optimization-plan-2026-09-19.md), [checklist 인계 계획](build-next-stage2-checklist-direct-family-handoff-improvement-plan-2026-09-19.md)이다. compact 통합계획의 “calibration은 진단만 담당하고 정책 발행 owner가 되지 않는다”는 표현은 compact 후보 실행·중복 coordinator 제거에 한정한다. 메인 기계평가와 그 정책 승계까지 제거하는 해석은 본 복구계획으로 정정한다. 퇴역 Daily/EV·R0–R3·legacy AI 연구는 복원하지 않는다.

2026-09-20 당일 checklist는 없고 다음 거래일 9/21 checklist에 기존 복구 ID가 있다. 이를 9/20 실행 완료 증거로 간주하지 않는다. 이번 user crontab 조회에는 공통 PREOPEN 호출은 있지만 main postclose 직접 호출은 확인되지 않았다. systemd·EOD 내부 호출까지 확인하기 전 예약 전체 부재로 단정하지 않으며, ME0의 필수 실행 경로 대사 대상으로 둔다.

## 2. 결함의 정확한 범위

### 2.1 유지돼 있는 기능

- 장중 메인봇은 `entry_setup_live_policy`가 해석한 정책 bundle을 받아 AI 호출 전에 `mechanistic_entry_policy_decision()`으로 `ENTER_NOW`, `RECHECK`, `BLOCK`을 결정한다.
- `ai_decision_trace.capture_machine_observation`은 당시 입력, 판정, 이유, bundle hash와 attempt identity를 기록한다.
- `ai_action_outcome_calibration`에는 누적 관측 적재, 비용·terminal 결합, 공통 임계치 후보, 계층·scope 후보, chronological holdout과 promotion gate가 구현돼 있다.
- `mechanistic_entry_runtime_policy.publish()`는 검증된 후보 또는 incumbent carry를 다음 KRX 거래일의 immutable bundle로 발행할 수 있다.
- `entry_setup_live_policy`와 strict verifier에는 후보 projection 및 정책 source/hash 검증 경로가 있다.

### 2.2 끊긴 연결

선택 릴리스의 정상 장후 wrapper가 전체 calibration CLI를 호출하지 않는다. 최신 canonical 보고서는 compact bridge가 작성한 `report_scope=compact_auxiliary_only`, `noncompact_sections_refreshed=false` 상태이며 메인 기계 임계치 평가를 갱신하지 않는다. 2026-09-21 정책은 `mechanistic_entry_thresholds_initial_v1`과 `machine_disposition=incumbent_carried`를 보존하지만, 그 보존은 당일 전체 재평가 결과가 아니라 이전 2026-09-16 전체 평가와 이후 compact-only 발행의 결합이다.

따라서 다음 네 상태가 현재 한 묶음으로 오인될 수 있다.

| 상태 | 올바른 의미 |
| --- | --- |
| 전체 평가 미실행 | 구조 결함. no-edge나 표본 부족이 아님 |
| 전체 평가 실행·필수 원천 결손 | `source_gap`; 결손 owner와 closure를 남기고 승격 금지 |
| 유효 paired 평가·후보 불합격 | `measured_no_edge` 또는 `evaluated_hold`; incumbent 보존 |
| 유효 후보 promotion 통과 | 다음 거래일 정책 후보. PREOPEN·PID·자연 성과는 별도 |

### 2.3 이름 충돌 제거

보고서와 요약에서는 다음 명칭을 고정한다.

- `main_mechanistic_entry`: 메인봇 기계 진입판정 임계치와 계층 정책
- `compact_auxiliary`: 기계 `ENTER_NOW` 뒤 AI PASS/VETO 보조판정
- `samsung_machine_entry`: 삼성 전용 진입 owner
- `machine_entry_timing`: 공통 확인 시간·recheck timing owner

기존 삼성 `machine_entry` key를 전면 개명하지 않는다. 호환 key는 유지하고 표시명/owner module을 삼성 전용으로 명시한다. 메인 기계에는 `main_mechanistic_entry`라는 별도 direct-family key를 사용한다. 필요 없는 전역 rename·중복 alias·보고서 family 증설을 피한다.

## 3. 목표 폐쇄 루프

```text
장중 exact entry input
  -> mechanistic_entry_policy_decision
  -> machine observation + attempt/bundle hash
  -> submit/no-submit/fill/terminal/cost 또는 검증된 missed-entry outcome
  -> final source-quality admission
  -> main mechanistic paired calibration
  -> 후보 통과 또는 평가된 incumbent carry
  -> next-KRX-date mechanistic_entry_runtime_policy
  -> PREOPEN exact-date/hash 검증
  -> 다음 정상 메인봇 PID 소비
  -> 새 판정·후행 결과가 다음 장후 입력으로 환류
```

compact AI는 같은 최종 정책 bundle에 함께 실릴 수 있지만 compact 후보 실행의 성공은 메인 기계 평가의 선행 필수 조건이 아니다. compact 원천 결손·provider defer·후보 없음 때문에 메인 기계 전체 평가가 생략되어서는 안 된다. 반대로 메인 기계 후보가 없다는 이유로 유효한 compact 결과를 지우지 않는다. 두 평가 결과를 결합하는 단일 owner는 기존 `mechanistic_entry_runtime_policy`다.

## 4. 원천·평가 모집단 계약

### 4.1 판정 당시 원천

각 행은 다음 값을 exact attempt identity로 결속한다.

- 거래일, 종목, venue/session, scanner·setup identity
- 당시 정책 bundle/version/hash와 기계 action·reason
- 판정에 실제 사용한 setup state, micro window, spread, fillability, top3 ask/bid, 위험 상쇄 feature
- 판정·AI·final guard·주문 제출의 순서와 각 terminal
- 선택된 entry plan, 수량, 가격, stop/exit owner, 비용 모델과 해시

현재 snapshot이나 이후 정책으로 과거 결손을 채우지 않는다. 동일 attempt의 중복 기록은 같은 action·bundle이면 하나로 축약하고, 충돌하면 해당 identity만 제외한다.

### 4.2 후행 결과 분리

| 모집단 | 평가 용도 | 금지 |
| --- | --- | --- |
| 실제 `ENTER_NOW` 후 제출·체결·`COMPLETED + valid profit_rate` | 실제 비용 후 결과 및 운영 model 검증 | partial/HELD/미확정 비용을 0으로 대체 금지 |
| `ENTER_NOW`이나 no-submit/no-fill | 실행 병목과 기회비용 진단 | 실제 손익으로 합산 금지 |
| `RECHECK/BLOCK` | 독립 검증된 missed-entry CF가 있을 때 후보 action 비교 | 합성 BUY·현재 가격·미검증 outcome 사용 금지 |
| partial/held/manual custody | 별도 상태와 terminal lineage | 정상 무거래 또는 완료 손익으로 처리 금지 |
| source-quality 제외 행 | 결손 census | 후보 순위·EV 분모 편입 금지 |

기계 임계치 후보가 과거 `BLOCK/RECHECK`를 `ENTER_NOW`로 바꾸는 경우 실제 미체결 경로이므로 독립 운영 CF 모델 검증이 필수다. 실제 `ENTER_NOW`를 막는 후보도 당시 실행 결과와 동일 frozen opportunity에서 비교한다. actual PnL과 CF PnL은 별도 열·별도 합계로 유지한다.

### 4.3 시간 경계

- clean baseline은 `2026-06-05T00:00:00+09:00` 이후만 사용한다.
- calibration/holdout은 거래일 순서로 분리하고 holdout을 후보 선택에 재사용하지 않는다.
- source date, publication date, effective date를 분리한다.
- 이미 PREOPEN 동결 시간이 지난 당일 정책을 뒤늦게 덮어쓰지 않는다.
- 과거 복구 불가능 source gap은 제외 manifest로 고정하고 같은 raw를 반복 재생하지 않는다.

### 4.4 모집단 축소 결함의 선행 보완

선택 릴리스의 `_common_refinement_population()`은 `operating_projection`이 전달되면 natural `ENTER_NOW`와 compact PASS/VETO·owner replay에 맞는 행만 통과시키고 paired/non-entry 행을 제외한다. 현재 `build_report()`는 compact `.source.json`을 이 인자로 공급한다. 전체 CLI를 다시 호출하기만 하면 기계판정 전체 모집단 연구가 복구된다고 볼 수 없는 이유다.

수정은 기존 함수 안에서 입력 lane과 지원되는 결론을 명시하는 범위로 제한한다.

| lane | 필요한 보완 | 허용 결론 |
| --- | --- | --- |
| 자연 machine `ENTER_NOW` + 당시 downstream | compact의 후보 평가 성공 여부 대신 독립 machine source gate와 검증된 owner plan/terminal을 사용 | 실제 판정 억제 후보의 전체 downstream 비용 비교 |
| machine `BLOCK/RECHECK` + 유효 CF | compact projection이 있다는 이유로 행을 버리지 않고 원천·비용·후행 지원범위별 유지 | 기계 선택의 기회비용 연구. 미호출 AI·실행 경로까지 지원되지 않으면 운영 승격은 불가 |
| legacy paired 경로 | 현재 machine 입력 재현성과 비용/모델 version을 확인하고 자연 trace와 중복 제거 | 검증 범위 내 연구. 구형 경로 proxy를 현행 실현 순익으로 재명명하지 않음 |
| source/실행 모델 미지원 | 처음 제외된 사유와 중첩 결손을 별도 집계 | 구조 수리 또는 역사적 제외. 정상 무거래로 변환 금지 |

`BLOCK/RECHECK`에 AI를 호출했다고 합성하거나 PASS를 가정하지 않는다. 당시 AI가 실행되지 않은 완화 후보는 기계 자체의 유효 CF 진단까지 먼저 계산하고, 전체 machine→AI→submit 경제성 proof가 없으면 `unsupported_downstream_ai_scope`로 승격을 보류한다. 이는 실제 체결이 있을 때만 기계 연구를 허용한다는 뜻이 아니다. 반대로 `ENTER_NOW` 부분집합에서 유효한 강화 후보의 결과를 전체 시장·전체 기계판정 정확도 향상으로 일반화하지 않는다.

원천 손실과 코드 결함은 다음처럼 처리한다. 유효 원천이 reader 필터·identity alias·label join 때문에 빠지는 경우는 지금 수정한다. source/cost/plan을 과거에 기록하지 않았고 다른 원장으로 exact 복원이 안 되는 경우는 역사적 제외로 확정한다. 미래 writer가 같은 필드를 생산하고 reader가 실제로 읽는 회귀를 통과한 뒤에만 자연 성숙 대기로 분류한다. null 값에 `기다리면 해결`이라고 쓰는 것으로 수리를 끝내지 않는다.

## 5. 경제성 목표와 후보 탐색

### 5.1 주 지표

후보 선택의 주 목적은 동일 opportunity·동일 예산에서 다음 두 값의 동시 개선이다.

1. 비용 차감 paired EV delta
2. 관측 거래일당 비용 차감 순익 delta

보조 guard는 exposure·unique symbol·독립 source day·terminal coverage·capital/reserve·fill participation·tail loss·MAE/MFE·catastrophic loss proxy다. win rate와 gross return은 진단값이며 승격 근거가 아니다.

### 5.2 후보 범위

초기 복구는 현행 `MECHANISTIC_COMMON_FEATURE_GRID`와 `MECHANISTIC_REFINEMENT_GATE`를 재사용한다. 9/16 결과의 유효 선택 25개는 당시 데이터에서 중복 선택을 제거한 결과이며 고정 grid 수가 아니다. 현재 공통 grid가 직접 탐색하는 축은 spread/fillability/top3 ratio 세 가지다. 아래 micro 두 값은 현재 정책의 고정 좌표로 보존하고 신규 탐색 축으로 확대하지 않는다.

- `minimum_micro_net_aggressive_delta_10t`
- `minimum_micro_price_change_10t_pct`
- `maximum_spread_bp`
- `minimum_fillability_score`
- `maximum_top3_ask_to_bid_ratio`

새 feature, 신규 모델, 별도 optimizer, 별도 DB나 report family를 만들지 않는다. 복구된 루프에서 유효 비교가 충분히 생성됐는데도 모든 후보가 같은 action을 만드는 경우에만 기존 grid의 식별력을 별도 검토한다. 양수 결과를 만들기 위해 threshold, holdout, 비용, 표본 floor를 완화하지 않는다.

재검토 시 코드에는 `full_population_positive_net_paired_delta_v2`(양수 비용 후 EV)와 legacy 10bp 계약이 함께 있다. Plan Rebase §7의 10bp 설명과 차이가 있으므로 ME0에서 승인된 버전·candidate validator·publisher·loader의 gate를 대조한다. 근거가 확인된 현행 v2는 그대로 재사용하고 legacy 10bp를 모든 연구에 재부과하지 않는다. 승인 충돌이 해소되지 않은 후보는 자동 승격만 보류하고 연구 계산·기존 정책 발행은 진행한다. 이 계획 작성으로 적용 gate나 기준 문서를 조용히 바꾸지 않는다.

### 5.3 결과 분류

전체 평가 보고서는 다음 중 하나로 종결한다.

- `source_blocked`: 필수 source/admission/identity/cost/terminal 계약 결손
- `valid_empty`: 적격 opportunity가 실제로 0이며 원천 계약은 완결
- `insufficient_mature_sample`: 유효 비교는 있으나 기존 표본·holdout floor 미달
- `evaluated_no_edge`: 유효 비교 완료, 비용 후 동시 개선 후보 없음
- `evaluated_hold`: 양수 진단은 있으나 tail·coverage·holdout gate 불합격
- `validated_edge`: 모든 promotion check를 통과한 단일 후보

`full_evaluation_executed`, `candidate_count`, `distinct_action_comparison_count`, `paired_terminal_count`, `actual_count`, `counterfactual_count`, `cost_adjusted_ev_delta_pct`, `daily_net_profit_delta_krw`, `promotion_pass`, `first_blocker`를 top-level terminal projection으로 제공한다. null은 이유와 함께 유지한다.

### 5.4 금액 지표·분모·탐색과 승격 분리

기존 함수가 내는 `terminal_proxy_ev_pct`와 발생 빈도의 곱은 원화 일별 순익이 아니다. 실제 reader가 원화 금액·수량·비용을 제공하는지 확인하고, 없으면 현재 `entry_split_order_plan`·strategy owner replay의 검증된 금액 반환을 연결한다. 비율에 임의 매수금액을 곱해 채우지 않는다.

동일 비교 집합 U, 동일 완결 관측일 D, 정책 p에 대해 아래를 명시한다.

- `N(i,p)`: 해당 정책이 지원하는 실행·청산 순익에서 수수료·세금·슬리피지·허용 추론비용을 정확히 한 번 차감한 원화 금액. 모델 결과에는 modeled 표기를 붙인다.
- 후보와 기준의 opportunity 단위 순익 차이: `N(i,candidate) - N(i,incumbent)`.
- 동일 사전 기준금액 `B(i)>0`에 대한 opportunity 평균 ΔEV: `mean(100 * delta_N(i) / B(i))`. 계약과 단위 `%p`를 명시하고 기존 trade EV·notional-weighted 지표와 섞지 않는다.
- 관측일당 Δ순익: `sum(delta_N(i)) / len(D)`. D는 후보별 거래 발생일이 아니라 양측에 공통인 완결 관측일이다. 실제로 완결된 무거래일은 포함하고 원천 결손일을 0원으로 편입하지 않는다.
- 자본 중복 점유가 있으면 기존 owner의 지원 portfolio 결과를 사용한다. 지원되지 않으면 opportunity 평균만 연구로 표시하고 portfolio/day headline은 null 및 구체적 원인을 기록한다.

정상 비진입 arm은 0 노출·0 거래손익일 수 있으나 해당 arm에서 이미 발생한 추론비용 등은 계약에 따라 반영한다. no-fill도 종료/비용 확정 전에는 0이 아니다. 양측이 같은 결정을 내린 유효 opportunity는 delta 0으로 공통 분모에 유지하고, 정책 전체가 같은 self-comparison은 독립 개선 후보 수에서 제외한다. matched/support coverage와 제외 사유를 함께 공개해 좋은 사례만 선택하는 편향을 막는다.

탐색과 승격을 다음처럼 분리한다.

1. source·비용·모델이 유효한 비교는 표본 floor 미달이어도 baseline/candidate/Δ 지표를 계산한다. 모든 후보가 promotion floor 아래라고 진단값까지 지우지 않는다.
2. calibration에서만 후보·동작 signature를 비교해 중복을 제거하고, 유효한 ΔEV·일별 순익 개선을 우선 순위로 둔다. 기존 지원 후보 수를 늘리지 않는다.
3. calibration에서 선정한 후보만 미사용 chronological holdout으로 검증한다. 음수인 1위를 본 뒤 같은 holdout으로 2위·3위를 다시 고르지 않는다. 모델 검증 holdout과 정책 선택 holdout의 재사용도 금지한다.
4. 표본 수·비용·tail·coverage·승인된 version gate를 충족한 candidate만 발행한다. 숫자가 양수라는 이유만으로 승격하지 않는다.
5. 판정 정합성은 동일 입력에 대한 runtime/replay action 일치, 지원 outcome label에 대한 잘못된 진입·놓친 기회로 진단한다. raw accuracy·win rate를 승격 점수로 사용하지 않는다.

### 5.5 비용과 실행시간

기존 날짜별 projection·봉인 source·결과 fingerprint를 먼저 재사용한다. 변경된 source day/terminal revision의 영향 scope만 재계산한다. 64MiB 초과 또는 growing JSONL은 stat 후 summary/manifest·bounded streaming을 사용한다. 새 cache DB·범용 성능가드·대량 병렬 provider 탐색을 추가하지 않는다.

시간이 부족하면 flow 설명·비필수 세부 분석·추가 계층 후보 수를 줄이고, 비교 원천·비용·holdout·parent 검증은 유지한다. 예산으로 미평가한 후보 수와 범위를 기록하고 이를 `전체 후보 no-edge`라고 보고하지 않는다. 같은 fingerprint의 결손 원천을 여러 번 재생해 결과0을 반복 생산하지 않는다.

## 6. 구현 단계

### ME0. 현행 초안과 선택 릴리스 차이 고정

1. 선택 릴리스와 작업 디렉터리의 wrapper, calibration, publisher, verifier 변경을 좁게 비교하고, 현행 gate의 version·승인 근거·scope를 고정한다. user/system crontab·timer/service·EOD 내부 호출에서 실제 main postclose 진입점과 사용 release를 추적한다.
2. 선택 릴리스를 기준으로 기존 기계 evaluator 함수를 재사용한다. 오래된 full builder가 퇴역 AI/Daily owner를 다시 호출하지 않도록 호출 의존성을 확인한다. 필요하면 기존 CLI 안의 `--machine-only` 실행 경계로 기계 필수 함수만 조합하며 새 모듈/coordinator는 만들지 않는다.
3. 다른 세션의 변경을 보존하고 이 결함 범위만 별도 review diff로 고정한다.

완료 조건:

- 선택 릴리스의 결손과 작업 디렉터리 초안의 보완 범위가 파일·함수·호출 순서로 대사된다.
- 한 source fingerprint의 기계평가는 한 번만 수행하고 동일 입력 재시도는 재사용한다. terminal/cost 정정 또는 source/code/contract 변경은 새로운 generation으로 허용한다.
- wrapper가 실제 예약 진입점에서 호출됨을 확인한다. 자동 실행 경로가 없으면 기존 운영 owner에 연결하는 수정까지 범위에 포함하며, 수동 성공만으로 자동 루프 복구를 완료하지 않는다.

### ME1. 장후 순서 복구

정상 순서는 기계평가를 provider 작업보다 먼저 진행한다.

1. 기존 full-cost reference 준비, 실제 trade fact·원천 label·final source-quality를 확인한다. 독립적으로 유효한 machine 원천은 compact screen 수와 무관하게 허용한다.
2. source date와 frozen incumbent를 고정하고 기계 공통·계층·scope 평가를 실행한다. 기존 CLI에 `--machine-only` 경계가 필요하면 이때 적용한다.
3. 기계 평가 보고서를 봉인하고 기존 publisher가 미래일 machine 후보/carry 정책을 준비한다. compact는 검증된 incumbent를 보존한다.
4. compact evaluator는 canonical paired 보고서에 독립적으로 실행/재사용한다. 최종화는 현재 machine parent와의 호환성을 확인하고 같은 publisher 안에서 AI 부분만 보존/선택한다.
5. 두 family의 최종 원천 참조와 최종 bundle hash를 consumer→summary→checklist→strict verifier에 인계한다. 마지막 writer 이후에만 최종 요약을 확정한다.

이것은 두 evaluator를 다시 하나의 대형 계산으로 합치는 작업이 아니다. 기존 compact 평가·최종화 함수를 유지하고 메인 기계의 독립 계산/발행을 복구한다. 물리적 immutable bundle generation은 최대 필요한 단계만 발행하며, 단일 publisher module과 최종 dated pointer를 유지한다. 앞선 기계 결과를 뒤의 compact 발행이 지우지 못해야 한다.

reference-only 성공, compact-only 완료, 오래된 report 존재는 full machine 평가 성공을 대신하지 않는다. compact 실패 후에도 이미 수행한 machine 결과·carry는 보존하되 compact가 필수 작업이면 전체 chain 실패를 숨기지 않는다. machine 평가/발행 자체 실패는 DONE을 막는다. 결손을 유효하게 보고한 기계 terminal은 기계적 완료일 수 있지만, 해결 가능한 구조 결손이 남으면 구현 owner는 OPEN이다.

### ME2. 기계 보고서와 compact 산출물 소유권

기존 calibration canonical path는 메인 기계평가가 소유하고 compact는 기존 `compact_auxiliary_paired_economic_<date>.json`을 소유한다. compact coordinator/bridge와 복제 보고서를 되살리지 않는다.

- 기계 report는 명시적 machine scope와 기계평가 수행/재사용 receipt를 갖는다. 필수 내용은 `mechanistic_entry_refinement`, 공통/등록 scope별 hierarchy 결과, machine case census, 원천·비용 상태와 economic projection이다.
- `mechanistic_flow_groups` 등 비권한 진단은 기존 산출물을 재사용할 수 있고, 새 기계 경제평가를 지연시키는 필수 재계산으로 만들지 않는다. 생략된 진단은 갱신했다고 표시하지 않는다.
- 기계 report에 compact 전체 내용을 복제하지 않는다. 필요한 source 경로·semantic hash·평가일만 참조하고, compact 원천이 없으면 독립 machine lane을 계속 평가한다.
- 기존 `report_scope=compact_auxiliary_only` 파일은 historical compact 결과이며 메인 평가 수행 증거로 통과시키지 않는다. 새 scope/section 계약은 생산자와 모든 실제 reader를 같이 변경한다.
- 보고서는 먼저 봉인하고 publisher가 그 hash를 참조한다. 발행 후 `runtime_policy_publication` 결과나 bundle hash를 원 보고서에 다시 넣어 self hash를 바꾸지 않는다. 발행 receipt는 기존 bundle/consumer에 둔다. report↔policy의 순환 hash 의존을 만들지 않는다.
- fingerprint는 source partition·cost/terminal revision·현재 machine/AI parent·code/contract·후보 grid·holdout 경계를 포함한다. report lock을 풀고 publisher lock을 얻는 순서를 고정하고, 같은 target에 다른 writer가 갱신했다면 최신 parent를 다시 읽어 조건 검증 후 발행한다.

### ME3. 메인 기계 evaluator 독립성

현재 flag의 의미와 실제 호출을 대사하고 main machine은 기본 필수 owner로 선언한다. compact의 OFF/defer/provider budget이 machine 실행을 끄지 못하도록 기존 wrapper 안에서 조건을 분리한다. 명시적 operator OFF는 보존한다. 누락된 결과에서 required 여부를 역으로 유추하지 않고 expected owner 목록과 observed receipt를 대조한다.

전체 기계평가는 provider 호출 없이 기존 관측과 후행 결과로 실행 가능해야 한다. compact provider 예산, timeout, candidate eligibility가 메인 기계평가의 source gate가 되어서는 안 된다.

### ME4. 단일 정책 발행

`mechanistic_entry_runtime_policy.publish()`를 유일한 bundle publisher로 유지한다.

- `validated_edge`이면 정확한 parent hash에 결속된 candidate만 machine policy로 채택한다.
- 그 외에는 incumbent thresholds를 보존하고 `machine_disposition`에 평가 결과를 기록한다.
- compact 결과는 독립 proof를 통과한 경우에만 AI policy 부분을 갱신한다. machine 후보 평가에서도 고정한 AI는 단순 version만이 아니라 유효 prompt bytes·계약·기계 evidence 입력 의미까지 일치해야 한다. 기계 policy 변경으로 그 전제가 깨지면 해당 운영 비교는 다시 검증한다.
- machine와 compact 중 한쪽이 불합격이어도 다른 쪽의 결과를 보존한다. 단, 독립 통과가 두 변경의 동시 적용 근거는 아니다. 동일 entry stage의 기존 단일 변경 규칙을 따른다. machine 후보는 현재 AI 정책을 고정한 full downstream 결과가 유효할 때 우선하고 compact는 carry한다. 두 변경을 함께 채택하려면 정확한 조합의 독립 검증·scope/기존 same-stage 권한이 있어야 한다.
- compact 후보 proof는 당시 machine parent와 실제 downstream prompt/input 계약에 결속한다. machine 정책이 달라지면 기존 compact proof를 새 모집단으로 승격하지 않고 `parent_changed_revalidation_required`로 보존한다. machine 후보도 고정한 AI 정책/hash가 바뀌면 재검증 대상이다.
- bundle의 기존 단일 `source_artifact_sha256`만으로 두 owner를 증명하지 않는다. 같은 bundle 안에 machine/compact별 evaluation source date·source path/hash·parent policy hash·disposition 참조를 최소 추가한다. 마지막 compact 발행이 machine source를 상실시키지 않도록 validator·PREOPEN reader·direct verifier를 함께 전환한다.
- 다음 KRX 거래일 날짜, source artifact hash, policy self hash, 이전 bundle hash와 scope를 검증한다.
- 07:35 freeze 이후 동일 effective-date bundle을 변경하지 않는다.

정책 발행 성공은 EV 개선이 아니다. `machine_disposition=incumbent_carried`도 당일 전체 평가가 실행됐는지, 이전 보고서를 단순 승계했는지를 별도 필드로 구분한다.

### ME5. PREOPEN·메인봇 소비 검증

기존 `entry_setup_live_policy`와 `mechanistic_entry_runtime_policy.load/load_effective`를 재사용한다.

1. PREOPEN에서 exact-date bundle·source artifact·self hash·scope를 검증한다.
2. target date 정책이 없을 때 허용된 incumbent carry와 손상된 target 정책을 구분한다.
3. 메인 SCALPING의 등록된 venue/session scope만 적용하고 삼성·위젯·에피소드·holding으로 확장하지 않는다.
4. 실제 메인봇이 AI provider 호출 전에 선택 bundle의 machine thresholds로 판정하는지 trace에 bundle hash를 기록한다.
5. 다음 정상 기동의 실제 PID/cwd/release/policy hash를 확인한다. 실행 중 PID hot reload는 하지 않는다.

### ME6. 후행 요약·checklist·strict verifier 보완

`runtime_approval_summary`에 새 evaluator를 만들지 않고 canonical 보고서의 terminal projection을 직접 전달한다.

- `main_mechanistic_entry`와 `compact_auxiliary`를 별도 family 상태로 표시한다.
- `samsung_machine_entry`와 명칭을 분리한다.
- 전체 평가 미실행을 `not_applicable`이나 compact 완료로 닫지 않는다.
- `source_gap`, `insufficient_mature_sample`, `evaluated_no_edge`, `validated_edge`를 그대로 투영한다.
- policy handoff, PREOPEN 소비, 실제 PID, 자연 경제성을 별도 축으로 유지한다.

`build_next_stage2_checklist`는 구조 결손일 때만 동일 stable ID의 producer-repair 작업을 유지하고, 표본 성숙은 기존 자연 acceptance owner에 넘긴다. no-edge·incumbent carry는 새 구현 작업을 만들지 않는다.

strict verifier는 다음을 모두 요구한다.

- compact-only가 아닌 전체 report scope
- `noncompact_sections_refreshed=true`
- 유효 `mechanistic_entry_refinement`와 scope extension 계약
- report artifact hash와 최종 bundle의 machine 전용 source 참조 일치; compact 전용 source 참조도 독립 검증
- full evaluation terminal projection과 `machine_disposition` 일치
- 장후 wrapper에서 full calibration이 summary/checklist보다 먼저 종결

### ME7. 작업목록과 운영 문서 정합화

[장후 작업목록](../audit-reports/2026-09-05-postclose-work-inventory.md)에 삼성 작업과 분리된 `main_mechanistic_entry` 항목을 복구한다. owner 설명은 “기계 진입판정 exact outcome·비용 후 paired threshold 평가와 다음 거래일 bundle 발행”으로 고정한다. compact AI 항목은 보조판정 전용으로 유지한다.

완료된 구현 이력은 audit report에 남긴다. 실제 wrapper/예약 변경 시 운영 작업목록과 checklist를 같이 갱신하며 Plan Rebase·AGENTS·README·runbook은 별도 명시 요청 없이 수정하지 않는다. 장후작업 이름만으로 정책 적용이나 경제 개선을 주장하지 않는다.

## 7. 코드 변경 범위

기존 파일을 우선 재사용한다.

| 파일 | 최소 변경 |
| --- | --- |
| `deploy/run_threshold_cycle_postclose.sh` | 전체 calibration의 독립 실행·순서·artifact/policy wait·fatal boundary 복구 |
| `src/engine/scalping/ai_action_outcome_calibration.py` | machine 실행 경계, 공통 모집단 lane 분리, paired 금액 지표, terminal projection·재사용 |
| `src/engine/scalping/compact_auxiliary_paired_replay.py` 및 기존 consumer | 기계 모집단과 compact 모집단 혼합 방지, parent 검증·최종 bundle 직접 인계 |
| `src/engine/scalping/mechanistic_entry_runtime_policy.py` | machine/compact 독립 disposition과 full-evaluation source 결속 |
| `src/engine/scalping/entry_setup_live_policy.py` | candidate projection·parent/source/hash fail-closed 재검증 |
| `src/engine/verify_threshold_cycle_postclose_chain.py` | full report→future bundle 직접 검증, compact-only 대체 차단 |
| `src/engine/runtime_approval_summary.py` | main/compact/Samsung owner 상태 분리 및 직접 projection |
| `src/engine/build_next_stage2_checklist.py` | 구조 결손·자연 성숙·no-edge의 올바른 인계 |
| 기존 관련 테스트 | 위 계약의 회귀만 추가 |

새 Python 모듈, 별도 DB, 별도 evaluator, 별도 정책 publisher, 별도 cron은 만들지 않는다. `src/engine` root 신규 모듈도 없다.

## 8. 리뷰·회귀 검증

### 8.1 필수 단위·계약 검증

- `test_ai_action_outcome_calibration.py`
  - compact source 있음/없음에 따라 독립 machine CF 모집단이 소실되지 않음
  - 실제 ENTER_NOW 0건이나 유효 CF 존재 시 연구 수치 계산·미지원 downstream 승격 차단
  - actual/CF/censored 분리
  - 동일 정책 self-comparison 제외
  - full report 필수 section과 terminal projection
  - source gap, valid empty, insufficient sample, no-edge, validated edge 반례
- `test_mechanistic_entry_runtime_policy.py`
  - qualified candidate 채택
  - no-edge/source-gap incumbent carry
  - compact 결과와 machine 결과의 독립 결합
  - parent/source/self hash, next trading date와 freeze
  - machine 변경 후 stale compact proof 거절, 두 독립 후보의 무검증 동시 승격 금지
  - machine→compact 및 compact→machine 재시도에서 다른 owner source/policy 소실 없음
  - report 봉인→publisher→consumer의 hash 순환 없음과 동시 writer 충돌 검증
- `test_entry_setup_live_policy.py`
  - full candidate projection과 exact bundle 소비
  - malformed target 정책 fail-closed
- `test_threshold_cycle_wrappers.py`
  - cost-reference-only → final source → machine evaluation/publication → compact finalize → final policy/consumer → summary/checklist/verifier 순서
  - compact 실패가 full calibration을 생략하지 않음
  - full calibration 실패가 DONE으로 진행하지 않음
- `test_verify_threshold_cycle_postclose_chain.py`
  - compact-only 보고서 거절
  - full report와 future policy hash 일치
  - 평가 terminal과 machine disposition 불일치 거절
- runtime summary/checklist 기존 테스트
  - main mechanistic, compact, Samsung 상태 분리
  - compact PASS와 정책 파일이 있어도 필수 machine 평가가 빠지면 direct complete/DONE 불가

### 8.2 실행 검증

1. 관련 pytest와 Python compile
2. `bash -n deploy/run_threshold_cycle_postclose.sh`
3. wrapper contract tests
4. `git diff --check`
5. 문서 link/owner 확인과 print-only parser

전수 raw replay, provider 후보 재호출, 전체 장후 wrapper 재실행은 코드 리뷰가 닫히기 전에 실행하지 않는다.

## 9. 제한 재생성과 배포 기준

코드 리뷰와 targeted validation이 통과한 뒤 영향 범위만 재생성한다. 첫 대상은 실제 immutable source·quality·terminal이 확인된 마지막 거래일로 고정한다. 9/17 source를 주말 9/20에 재생성한다면 source date는 9/17, publication date는 9/20, effective date는 거래일 calendar로 계산한 9/21이다. 최신 파일의 생성일을 source trading date로 바꾸지 않는다.

기존 full publisher가 `next_target(source_date)`만 계산한다면 source/publication/effective date 분리 기능을 기존 함수/CLI에 보완한다. 지금 없는 인자를 지원한다고 가정한 실행 명령은 사용하지 않는다. 종료 전 정확한 검증 명령과 실제 출력 경로를 구현 audit에 남긴다.

| 단계 | 산출물·검증 | 완료를 막는 조건 |
| --- | --- | --- |
| 입력 동결 | 마지막 유효 source day, manifest, 원천 크기/hash, 현재 parent, 후보 grid·비용/모델/holdout version | 활성 writer·대체 snapshot·identity 미확인 |
| 기계 재평가 | 기존 calibration 경로의 machine report, 기준/후보/Δ·원화/day·평가/제외 count | 계산 가능한 원천이 있는데 reader/모델 연결 결함으로 null |
| 미래 정책 | 기존 `data/runtime/mechanistic_entry_policy/policy_<effective>.json`와 immutable sources/generations | freeze 위반, 두 family source 소실, parent 충돌 |
| 최종 인계 | 기존 compact consumer·runtime summary·checklist·strict verifier가 최종 bundle 참조 | 오래된 generation 인계, 기계 report 미실행을 PASS로 집계 |
| 정상 PREOPEN/PID | 실제 loader·bootstrap의 해당 정책 읽기와 bot trace/hash | 문서상 연결만 있고 callable 경로 없음 |

현재 유효 비교가 하나도 없으면 raw→admission→경제모델→holdout의 첫 결손과 수리 가능성을 구체적으로 기록한다. 미래 수집만 가능한 결손은 원천 필드·writer·consumer·필요 사건·회귀 검증을 명시한다. 모든 실제 EV가 null인 채 `구조 결손 모두 해소`라고 결론내리지 않는다. 유효 input fixture로 계산과 자동 소비가 확인된 코드 종결, 실제 자료 결손, 자연 경제성 미종결을 각각 기록한다.

1. 기존 exact-date 비용·terminal·source-quality artifact를 재사용한다.
2. 메인 기계 full calibration과 미래 정책 발행 경로만 제한 실행한다.
3. source/model/parent까지 fingerprint가 동일하면 compact 결과를 재사용한다. parent가 바뀌면 기존 proof는 연구 증거로 보존하고 승격하지 않으며 불필요한 provider 재호출 없이 carry한다.
4. canonical report가 full scope이고 다음 거래일 policy hash가 일치하는지 확인한다.
5. runtime summary→checklist→strict verifier의 직접 인계를 갱신한다.

과거 effective date 정책을 소급 변경하지 않는다. 재생성 시점의 다음 정상 KRX 거래일 정책만 발행한다. 기존 2026-09-21 bundle이 이미 PREOPEN freeze 경계를 지났다면 다음 거래일을 대상으로 발행하고 9/21 파일을 덮어쓰지 않는다.

검증된 변경은 immutable release로 만들고 선택 릴리스를 갱신한다. 실제 실행 중 메인봇을 재시작하지 않으며 다음 정상 기동에서만 소비한다. 배포 완료, PREOPEN 검증, 실제 PID 소비, 자연 판정 변화와 비용 후 EV 개선은 별도 상태로 보고한다.

## 10. 완료 기준

구현 완료는 다음 조건을 모두 만족해야 한다.

1. 실제 예약 경로의 정상 장후 wrapper에서 같은 fingerprint의 메인 기계평가가 한 번 실행되거나 검증 재사용된다.
2. compact 작업의 실패·차단이 메인 기계평가 실행을 제거하지 않는다.
3. canonical 보고서는 machine scope이며 지원 기계 모집단 전체의 후보·EV·일별 순익 또는 정확한 null 사유를 가진다. full은 퇴역 연구 전부의 재실행을 의미하지 않는다.
4. 후보0은 미실행, source gap, 표본 부족, no-edge로 구분된다.
5. 검증된 후보 또는 평가된 incumbent carry가 다음 거래일 단일 bundle로 발행된다.
6. report→최종 bundle의 family별 source→PREOPEN loader의 날짜·scope·hash가 일치하고 동일 fixture에서 runtime/replay가 같은 action을 낸다.
7. runtime summary/checklist/verifier가 main mechanistic, compact AI, 삼성 owner를 분리한다.
8. targeted validation과 재리뷰에 미해결 범위 내 결함이 없다.
9. 허가된 immutable release 선택과 제한 재생성 결과를 남긴다. 아직 도래하지 않은 정상 PREOPEN·실제 PID·자연 성과는 기존 acceptance owner에 인계하며 구현 테스트 통과와 구분한다.
10. 유효한 실제 원천이 있는데도 비용 후 계산이 null이면 원인을 수정할 때까지 이 결손을 닫지 않는다. 실제 원천이 없거나 과거 복구 불가능이면 제외 근거·미래 writer/reader 계약 검증·남은 natural acceptance를 명시하고 경제성 종결은 주장하지 않는다.

경제적 완료는 구현 완료와 분리한다. 다음 자연 표본에서 적용 bundle별 `COMPLETED + valid profit_rate`와 검증된 missed-entry CF를 누적해 비용 후 paired EV·관측일당 순익·tail을 산출하고, 기존 promotion gate를 통과했을 때만 성과 개선으로 인정한다. 유효 평가 결과가 no-edge이면 incumbent 보존도 정상 종결이지만, 전체 평가 자체가 빠진 상태는 다시 완료로 처리하지 않는다.

## 11. 중단·롤백 조건

- source identity, 비용, terminal 또는 parent policy hash가 불일치하면 후보 승격만 차단하고 incumbent와 원 증거를 보존한다.
- canonical report를 compact-only writer가 다시 덮어쓰면 배포를 중단한다.
- full calibration이 장후 DONE 뒤에 실행되거나 summary/checklist가 이전 generation을 읽으면 순서를 수리할 때까지 완료하지 않는다.
- scope가 메인 SCALPING 밖으로 확장되거나 AI가 기계 `BLOCK/RECHECK`를 승격하면 배포를 중단한다.
- broker/account/order/quantity/cap/provider/custody/operator lock/hard safety 변경이 diff에 섞이면 이 계획 범위에서 분리한다.

롤백은 이전 immutable release와 이전 검증 policy bundle 선택으로 수행한다. 산출물 삭제나 과거 정책 덮어쓰기로 롤백하지 않는다.


## 12. 이번 재검토에서 수정한 계획 결손

| 초안의 미비점 | 보완 결정 |
| --- | --- |
| 전체 CLI 한 줄 복원으로 종결 가능 | compact projection의 machine 모집단 축소와 후행 AI 미지원까지 별도 수리 |
| 과거25개·10bp를 모든 평가에 고정 | 현행 grid/version별 gate 검증, legacy/v2 충돌은 승격 전 해소 |
| compact 뒤 full만 호출하면 단일 발행 보장 | 기계 우선 계산, 기존 publisher 내 최소 generation 승계와 family별 source 보존 |
| 두 후보 각각 합격이면 동시 적용 가능 | 정확한 조합 proof/기존 same-stage 권한 없으면 한 후보만 승격 |
| report에 publication 결과를 다시 저장 | 봉인 report→policy→consumer 단방향 hash, 보고서 재해시 금지 |
| null 이유 기록만으로 결손 완료 | 계산 가능 source의 null은 수리, 역사적 소실·미래 생성·자연 성숙은 증거로 구분 |
| wrapper 코드만 확인 | 실제 cron/systemd/EOD 호출→selected release→main postclose 실행 경로 검증 |

문서 재검토는 기존 review gate의 implementation→self review→보완→re-review→targeted validation 순서를 따른다. 이 절은 계획 검토 결과이며 실제 코드 결손 해결 receipt가 아니다.

## 13. 구현·배포·제한 재생성 결과

2026-09-20 KST에 본 계획의 코드 범위를 구현하고 재검토했다. 메인 기계평가를 compact보다 먼저 실행하고, 공통·계층 모집단의 비용 후 paired 평가, 미래 정책 발행, family별 source lineage, runtime summary/checklist/direct verifier를 기존 owner 안에서 연결했다. 같은 입력의 재시도는 평가기·원천·incumbent를 포함한 fingerprint가 일치할 때 봉인 보고서를 재사용한다. compact 최종화가 메인 최상위 source date/hash를 덮던 결함과 비활성 선택 작업까지 크론 필수 대상으로 요구하던 배포 검사 결함도 보완했다.

- 최종 런타임 소스 커밋: `df2931b19bebf4a93be54207fea05e0ba32c0cc4` (`origin/main`에 포함). 후속 리뷰에서 과거 owner replay 결손과 미래 자연 성숙을 분리한 `e4f47ffec`, compact 전용 source receipt 검증을 바로잡은 `df2931b19`를 추가했다.
- 선택 릴리스: `/home/ubuntu/KORStockScan-runtime-releases/main-mechanistic-evidence-reviewed-20260920-df2931b19`
- 실제 예약 경로: 평일 07:35 PREOPEN, 20:10 postclose가 공통 release router를 사용하며 필수 네 경로 검증이 통과했다.
- 검증: 최초 구현 관련 suite 1,695개 통과 후 lineage·router·summary·strict verifier 보완 suite 390개를 재검증했다. 후속 리뷰의 단계별 suite 72·155·82개와 최종 선택 릴리스 suite 204개도 통과했다. Python compile, shell syntax, `git diff --check`, strict chain 및 print-only 문서 parser를 별도로 검증한다.

9/17 동결 원천을 9/20 publication으로 제한 재생성한 결과는 다음과 같다.

| 항목 | 결과 |
| --- | --- |
| canonical report | `data/report/ai_decision_action_outcome_calibration/ai_decision_action_outcome_calibration_2026-09-17.json` |
| report artifact hash | `83a088cdc8a5b378a36459aec0678c8cc306d530a59328c34c04279f5f74cbe7` |
| 평가 모집단 | 입력 paired 956·natural 2,330, 수용 paired 7·natural 1,708, 전체 1,715 |
| 후보 상태 | 서로 다른 정책 1개 평가, 독립 비교·calibration gate 통과·승격 후보는 모두 0개 |
| 비용 후 경제값 | calibration EV 0.0000%, holdout EV 0.0000%, holdout paired ΔEV +0.0054462573%p |
| 일별 원화 순익 | `null`; holdout 판단 변경 8건 모두 operating enrichment 미연결. 이것만으로 원천 복구 불가를 입증하지 못하며 §14에서 원장·adapter·모델 지원 여부를 재대사한다. |
| 판정 | `insufficient_mature_sample`, `incumbent_carried`; 양의 EV 개선이나 실제 순익 개선으로 인정하지 않음 |
| 다음 거래일 bundle | `data/runtime/mechanistic_entry_policy/policy_2026-09-21.json`, bundle `c6a7253ceda07cbfec7bcc04d78b868d610b016624fa0c7f47d00f3675e3a6b7`, file SHA256 `f2466fda9a4f5cf7b2e42f4cb3881d27bb8fad8b33b4bc6c12651f75657d122a` |
| family lineage | machine source 9/17/report hash `83a088...`, compact source 9/17/artifact `822c6f...`를 독립 보존 |
| 직접 검증 | main mechanistic `pass`, compact auxiliary `PASS`, 전체 strict chain `pass`; 동일 fingerprint 재시도 `evaluation_reused=true` |
| 후행 상태 | runtime summary `ddcb647a...`; main·compact policy receipt 모두 `valid=true`. 당시 출력된 `historical_unrecoverable`/`natural_maturity`는 §14 점검에서 판정 근거 부족을 확인했다. 정책 receipt 유효성과 경제성 결손 해소는 별개다. |

후속 점검 정정: 후보가 비진입을 선택한 arm에는 실제 주문·체결 receipt가 없는 것이 정상이다. 기존 진입 arm의 검증된 실행·청산·비용·자본과 후보 비노출·발생비용을 비교할 수 있는지 먼저 확인해야 한다. 8건의 operating enrichment 부재만으로 계산 가능한 손익 누락이 없거나 복구 불가능하다고 확정한 설명은 철회한다. 현재 수치는 경로 대리 EV이며 원화 순익은 미확정이다. 미래 writer/reader 검증도 report scope·갱신 flag만으로 입증되지 않는다. §14의 원천별 복구 판정과 후행 계약 검증 후에만 자연 성숙 또는 복구 불가로 분류한다. 기존 `DirectFamilyNaturalEvidenceMainMechanisticEntry`의 자동 분류는 해당 수정·재생성 때 정합화한다.

후속 리뷰에서는 통합 bundle의 최상위 `source_artifact_sha256`가 machine source를 소유하는데 runtime summary의 compact receipt가 이를 compact hash로도 요구하는 상충을 발견했다. compact 검증을 `compact_paired_artifact_sha256`와 compact fingerprint에 결속해 두 family source를 독립 검증하도록 수정했다. 재생성 후 main·compact receipt가 모두 유효하며, compact는 source gap 때문에 계속 incumbent를 보존한다.

코드 배포와 다음 거래일 bundle 생성은 완료됐다. 2026-09-21 PREOPEN bootstrap, 실제 PID의 bundle hash 소비, 자연 판정 변화와 비용 후 순익 개선은 아직 도래하지 않았으므로 완료로 표시하지 않는다. 실행 중 봇 재시작·hot reload·주문은 수행하지 않았다.

## 14. 공통 데이터·미진입 기회비용 경제성 연결 상세 보완계획

### 14.1 결정·범위·재작업 금지

이 절은 [공통 데이터·기회비용 통합계획](entry-opportunity-cost-full-population-tuning-implementation-plan-2026-09-17.md)의 U6/U7/U11/U12와 이 문서 ME2–ME6의 잔여를 구체화한다. 별도 운영 family·독립 실행계획·새 일정이 아니다. 기존 §5의 목표는 유지하고, §13의 전체 완료·복구 불가 해석보다 이 절의 보완 판정을 우선한다.

우선순위는 **잘못된 결손 분류 해소 → 실행 가능한 동일 모집단 경제성 → 활성 scope별 평가 → 경제성 중심 선정 → 다음 장전 자동 소비 → 필요한 계산 절약**이다. 양수 숫자·새 후보·실거래 수를 만들기 위해 근거를 완화하지 않는다. 음수·무개선이라도 유효한 기존/후보/차이와 원화 일별 순익을 산출하면 의미 있는 연구 결과다.

- 이미 검증된 common health·원시각·공백/feature 분리·중복 억제·306파일 정적 역할 ledger를 다시 구현하지 않는다. 이번 adapter가 소비하는 필드의 탈락/충돌이나 새 재현 결함만 수리한다.
- 기존 `ai_action_outcome_calibration`, owner replay, compact helper, publisher, PREOPEN, summary/checklist를 사용한다. 새 production module·DB·collector·service·cron·CLI·report family·범용 optimizer를 만들지 않는다. 기존 test 파일을 확장한다.
- compact [EO1–EO7 후속계획](compact-auxiliary-economic-tuning-optimization-followup-plan-2026-09-20.md)의 frozen plan·실행모델·portfolio 작업을 공유하고 중복 구현하지 않는다. 동일 helper의 편집 owner를 하나로 정하고 machine 지원 범위와 compact 지원 범위를 구분한다.
- 메인 최초진입만 보완한다. widget/episode/삼성/scale-in/exit 연구 전체를 재개하거나 퇴역 Daily/EV producer를 복원하지 않는다. 해당 owner 입력은 원천 계약 재사용 범위에 한정한다.
- 이번 요청은 **문서 계획 수립**이다. 코드·테스트 실행·Provider/API 호출·원천 재생성·commit/push·배포·PREOPEN·주문·env 변경은 실행하지 않는다. 후속 구현 승인 시 아래 검증과 필요한 재생성을 수행한다.

### 14.2 고정 증거와 해석

점검 기준은 선택 release `df2931b19`, source date 9/17, report hash `83a088cd...`다. 구현 시작 시 selector/commit/다른 세션 변경·보고서 generation을 다시 확인한다. 작업본의 큰 diff를 배포본에 일괄 복사하지 않는다.

| 사실 | 해석·보완 |
| --- | --- |
| 수용 1,715건 중 calibration 4건, holdout 1,711건 | 날짜 분리는 지키되 실제 학습 지지와 미완료 원천을 공개한다. holdout을 학습에 되돌려 유효 표본을 만들지 않는다. |
| grid 80 → calibration 행동 signature 1, 모두 비진입 | 80개 독립 개선 비교가 아니다. 첫 번째 엄격한 좌표가 대표가 되는 tie 처리와 후보 식별력을 보완한다. |
| holdout 후보 대리 EV 0%, 기준 −0.005446%, 차이 +0.005446%p | 무진입 후보의 대리 손실 회피다. 실제 원화 이익·양수 후보 EV가 아니다. |
| changed 8건, unsupported 8건, operating enrichment 0 | 결손 위치를 먼저 조사해야 한다. 후보 비진입의 실제 체결 부재는 결함이 아니다. |
| 다른 cohort 564건 제외, 새 hierarchy scope는 KRX 정규장 하나 | 정당한 scope 분리와 전수 평가 누락을 구분한다. raw 전체를 한 KRX 분모로 섞지 않는다. |
| 원화 일별 순익 null·9/21 incumbent carry | 정책 파일 발행은 확인되지만 경제성 연결 완료는 아니다. |

이전 검증 구간은 이미 사람이 결과를 열람했다. 수정된 모델·후보·랭킹을 같은 과거 구간에 다시 적용한 결과는 역사적 진단으로만 사용한다. 독립 승격 검증에는 후보 freeze 이후의 미사용 구간이 필요하며 이 제약을 artifact에 보존한다.

### 14.3 ME8 — 결손 판정과 source-to-consumer 복구

대상: calibration의 `_common_refinement_population`/`_machine_full_evaluation_projection`, summary의 `_economic_section`/`_economic_projection`, 기존 checklist 생성기.

1. 기존 accepted/excluded ledger에서 changed 8건부터 exact attempt·scope·당시 bundle·당시 action·현재 incumbent 재판정·후단 terminal을 추출한다. 전 raw를 재탐색하지 않고 manifest/index/기존 원장으로 필요한 식별자만 추적한다.
2. 각 행의 당시 입력 → plan → submit/no-submit → fill/no-fill → exit/cost → 자본 점유 → reader를 대사한다. 첫 누락 필드와 중첩 결손을 기존 report의 exclusions에 남긴다. 심볼/시간 근접 join, 다른 owner의 체결 흡수는 금지한다.
3. 기존 파일에 값이 있으면 adapter/join 복구, 당시 입력으로 pure planner가 재현 가능하면 검증된 modeled plan, 원천이 존재하지 않고 대체 원장도 exact 복원이 안 되면 역사적 제외로 판정한다. 단순 `owner_replay 없음`을 복구 불가로 변환하지 않는다.
4. 미래 자연 대기는 실제 writer/reader 경로·필수 필드·scope·계약 version과 연결 회귀가 통과하고 실제 유입 owner가 있을 때만 사용한다. report_scope/noncompact flag는 보고서 실행 증거일 뿐 미래 생성 계약 증거가 아니다.
5. summary는 source/model gap을 표본 부족보다 먼저 보존한다. 기존 scalar 상태를 유지할 필요가 있으면 gap 이유와 `prospective_resolution_mode=producer_repair`를 함께 전달해 repair가 자연 대기로 사라지지 않게 한다.

최소 상태 의미: `source_gap`(복구 작업 필요), `unsupported_scope`(설계 미지원), `pending_maturity`(기록된 후행 관측의 선언 기한 대기), `insufficient_sample`(지원된 모델/유효 원천의 표본 부족), `historical_unrecoverable`(exact 복원 불가 근거 있음), `evaluated_no_edge`(유효 비교 후 개선 없음). 과거 결손과 미래 지원 상태는 독립 필드로 둔다. ETA는 근거 없으면 null이다.

종료: 8건의 disposition과 근거가 대사되고 source gap을 natural wait로 잘못 보내는 fixture가 실패한다. 기존 완료 receipt는 보존하되 경제성 잔여의 자동 checklist 역할을 `producer_contract_repair`로 수정할 수 있어야 한다.

### 14.4 ME9 — machine 독립 실행 경제성 adapter

대상: 기존 calibration 내부 정규화/paired helper, `compact_auxiliary_paired_replay.owner_operating_arm`·`owner_model_scope_valid`·`operating_comparison_metrics`·`portfolio_metrics`, 기존 `entry_split_order_plan`/`strategy_owner_replay`/`entry_execution_sizing_plan`의 직접 재사용 지점. 공유 helper가 compact verdict를 전제하면 기존 module 안에 machine action을 받는 얇은 정규화만 추가한다. machine action을 허위 compact PASS/VETO 기록으로 저장하지 않는다.

| 실제 원천과 후보 action | 경제성 구성 | 지원 불가 시 처리 |
| --- | --- | --- |
| incumbent ENTER → candidate BLOCK/RECHECK | incumbent의 지원된 실행/청산/비용, candidate 비노출 및 발생비용을 비교한다. 후보 arm의 실제 broker fill을 요구하지 않는다. RECHECK는 즉시 영구 비진입으로 바꾸지 않고 기존 재평가/기한 행동을 재현한다. | 기존 진입 경로의 plan/terminal/cost/자본 결손을 직접 표시한다. |
| incumbent BLOCK/RECHECK → candidate ENTER | 같은 과거 cutoff의 입력으로 현재 고정 compact·price·qty·guard·exit owner를 차례로 재현한다. 실제 provider 미호출이면 지원된 offline compact 결과를 modeled로 구분한다. | 필수 입력·AI replay·모델 scope·price/sizing/자본 중 첫 미지원 지점을 남기고 upstream 기계 기회값까지만 진단한다. |
| 양측 ENTER·동일 행동 | 동일 지원 outcome/비용을 공유해 delta 0, 분모는 유지한다. | 절대 EV가 불명인 행을 outcome 0으로 채우지 않는다. |
| 양측 비진입 | 비노출·발생비용이 입증되면 해당 값과 delta를 사용한다. | source-invalid/후단 노출 불명/RECHECK 미종결은 확정 무거래 0이 아니다. |
| submitted no-fill/partial/held | no-fill terminal 및 비용, 부분 잔량, 보유 자본과 선언 exit window를 그대로 평가한다. | 실제 HELD/미확정 청산을 정상 0으로 대체하지 않는다. |

당시 원래 owner-issued plan이 있으면 그대로 우선 사용한다. BLOCK 때문에 plan이 원래 없더라도 당시 frozen price/qty/account context가 충분하면 기존 pure planner를 사용한 **연구용 재구성 plan**을 허용할 수 있다. planner version·입력 hash·cutoff·cost/exit·scope를 봉인하고 runtime 동일입력 parity로 검증한다. 원래 계획/실제 submit receipt로 재라벨링하지 않는다. 당시 budget/quantity/필수 feature가 없으면 현재값이나 임의 금액으로 보간하지 않는다.

실행모델은 실제 지원 scope의 독립 actual 검증이 필요하지만 **각 미진입 후보가 먼저 실체결돼야 하는 순환조건은 금지**한다. compact EO2의 검증 결과는 exact scope/model contract가 같을 때만 재사용한다. 후보 holdout으로 모델을 보정하지 않는다. 실제 청산 검증과 CF 선언 exit를 구분하고 가격 touch만으로 체결·청산을 확정하지 않는다.

비용은 actual/model 계약별 한 번만 차감한다. AI를 호출하지 않는 arm의 회피 비용과 이미 발생한 비용을 구분하고 reviewed zero-cost 근거가 없으면 0으로 두지 않는다. 새로운 action/price/qty/exit/Provider 권한은 만들지 않는다.

종료: 세 가지 방향(진입 억제·신규 진입·동일 행동)의 기존/후보/차이 원화값을 offline fixture로 재현한다. 기존 실제 원천에서도 지원 가능한 changed pair를 계산하고 미지원 행과 별도로 출력한다. 모든 행이 여전히 null이면 원천 복구나 모델 지원을 완료한 것으로 표시하지 않는다.

### 14.5 ME10 — 공통 기회·관측일·scope 분모

대상: common population, main report 조립, 기존 hierarchy/scoped publisher.

- 등록된 현재 main runtime scope를 publisher의 `for_cohort`/loader와 대사해 평가 목록을 만든다. KRX/NXT/SOR의 정확한 enum·session은 기존 registry를 사용한다. 새 venue·운영 universe를 추가하지 않는다.
- 각 scope에 동일 평가 함수를 호출하고 incumbent parent/cost/AI/exit/source hash를 독립 결속한다. 지원된 scope만 계산하고 나머지는 census·직접 사유와 incumbent carry를 남긴다. `different_cohort`를 전수 처리 완료의 유일 근거로 쓰지 않는다.
- raw event, exact attempt, 경제성 opportunity episode를 구분한다. 기존 promotion/watch TTL/reset·episode 키를 사용하고 동일 기회의 반복 RECHECK를 독립 수익으로 합산하지 않는다. 근거 없는 episode를 합성하지 않으며 episode 집계 불가능 시 attempt 진단으로 명시한다.
- scope별 `raw = retained + duplicate + excluded`, `retained = economic_complete + waiting + source_gap + not_applicable` 보존식을 대사한다. 기존 identity 충돌 격리와 비용 계약은 유지한다.
- 관측일 D는 source coverage가 완결된 공통 날짜다. 거래가 없는 정상 날짜는 포함하고 source missing일은 제외 사유를 남긴다. candidate별 참여 날짜를 분모로 쓰지 않는다.
- 동일 symbol/동시 기회·잔고·예약·cooldown의 충돌은 기존 portfolio 시간순 replay에서 처리한다. 여러 scope가 같은 실제 자본을 공유하면 scope별 수익을 단순 합산하지 않고 전체 bundle의 공통 예산 replay를 검증한다. 미지원이면 scope 진단과 전체 portfolio null을 구분한다.
- hierarchy는 공통 threshold 후보의 선행 승격을 요구하지 않는다. 변경되지 않은 incumbent를 parent로 한 단일 child 후보가 동일 full downstream 경제성 검증을 독립 통과하면 검토 가능해야 한다. proxy-only child 우회는 계속 금지한다. 기존 same-stage/단일 변경 계약과 bundle의 최종 paired 검증을 유지한다.

종료: 현재 활성 scope 모두 평가·원천/모델 미지원·valid empty 중 하나로 처분되고 미분류 0. KRX 결과를 전체 scope 개선으로 보고하지 않는다. 한 scope의 결손이 무관한 scope 연구를 중단시키지 않지만 공통 자본/필수 계약 결손은 bundle 승격을 차단한다.

### 14.6 ME11 — 작은 후보군과 경제성 선정

1. 먼저 현행 세 축을 `hard_safety/bounded_tunable/baseline_prior`·허용 bounds·incumbent 좌표와 대사한다. 최대 spread 100/최소 fillability 15/최대 ratio 5에 대한 현재 grid는 동등·강화뿐이라는 사실을 report에 표시한다. 신규 micro/feature 축이나 무조건 완화 grid를 추가하지 않는다.
2. 기존 허용 범위 내에서 incumbent와 최근접 이웃을 우선 사용한다. incumbent가 bound 끝에 있으면 반대 방향의 합법적 후보가 없는 것으로 기록한다. 현재 bounds에서 회복 후보가 불가능하면 데이터 대기가 아니라 `search_space_limited` 진단이며, 별도 근거·권한 검토 없이 bounds를 확장하지 않는다.
3. calibration 행동 signature 중복 계산은 재사용하되 파라미터 identity를 보존한다. 동률 대표는 incumbent 우선, 그다음 incumbent에서 가장 작은 정규화 거리, 마지막 고정 정렬 순서로 정한다. 첫 등장하는 가장 엄격한 조합을 자동 winner로 만들지 않는다. 검증 데이터로 signature나 대표를 선정하지 않는다.
4. 학습 4건처럼 지지가 부족하면 산출 가능한 진단값은 남기고 승격을 보류한다. 유효한 미사용 과거 source-day의 누락이 확인될 때만 adapter/manifest 복구 후 학습에 편입한다. 이미 열람한 holdout 이동이나 임의 80→대규모 grid 확장은 하지 않는다.
5. 실행 지원되는 후보와 proxy-only 후보의 순위를 분리한다. proxy-only 1위가 실행 지원 후보 탐색을 가리거나 자동 발행되는 경로를 없앤다. promotion floor 미달이라도 실행 가능한 후보는 EV·원화 결과를 출력한다.

같은 episode 집합 U와 완결 관측일 D에서 정책 p의 자본 제약 후 순익을 `P(p,d)`라 한다. full cost·exit·발생 AI비용을 반영하고 actual/model을 분리한다. 동일 기회별 사전 참조 notional `B(i)>0`가 입증될 때 `EV(p)=mean(100*N(i,p)/B(i))`, `ΔEV=EV(candidate)-EV(incumbent)`를 사용한다. candidate의 체결 건수만 분모로 쓰지 않는다. `ΔDailyNet=mean(P(candidate,d)-P(incumbent,d))`이며 단위는 원/완결 관측일이다. 전체 portfolio P와 N의 충돌/미체결 반영이 일치해야 한다. 기존 metric name을 재사용하되 formula/분모가 달라지면 계약 version을 올려 혼용을 막는다.

**선정 규칙:** source/model/공통분모 유효 → ΔEV 및 ΔDailyNet 동시 양수·기존 stress/tail/coverage/자본 guard 통과 → ΔDailyNet 내림차순 → ΔEV → 더 작은 정책 변경 → 고정 identity 순. 노출 빈도·승률·단순 손익합은 독립 승격 기준이 아니다. 위험회피로 Δ가 양수라도 candidate EV 0인 전면 비진입 정책은 현행 positive-EV gate를 충족하지 않는다.

현행 메인 승격의 0.10%·표본·holdout 계약은 유지한다. 이를 연구 산출의 사전조건으로 사용하지 않는다. 작고 유효한 양수 개선이 절대 floor만으로 막히는 경우 숫자와 직접 사유를 출력하되 이번 계획으로 gate를 변경하지 않는다. 승격 기준 변경이 필요하면 owner 근거와 publisher/PREOPEN/loader 동시 변경 범위를 별도 확정한다.

선택한 단일 후보를 freeze하고 미사용 chronological holdout으로 한 번 검증한다. model validation → candidate calibration/freeze → candidate holdout의 순서와 사용 이력을 보존한다. 실패 후 같은 holdout에 차순위를 채택하지 않는다. scope/hierarchy 후보를 같은 holdout으로 순차 골라 최종 조합을 만들지 않고 calibration에서 최종 조합을 고정한다.

### 14.7 ME12 — 발행·PREOPEN·후행 소비 계약

| 경계 | 입력·출력과 필수 확인 |
| --- | --- |
| 원천 → evaluator | exact cutoff·scope·parent·원래/재구성 plan 구분·model 지원 hash·비용·관측일·제외 보존식 |
| evaluator → publisher | scope별 기존/후보/Δ EV·원화/day·tail/capital·candidate freeze/holdout·source/model/code hashes·promotion checks |
| machine + compact → 단일 bundle | 각 family의 독립 원천·parent·검증 계약을 보존. 새 machine과 새 compact의 조합 proof가 없으면 동시 변경하지 않고 다른 축은 carry |
| bundle → PREOPEN | exchange calendar가 정한 effective date·parent·scope·허용 좌표·source/economic proof·same-stage/lock guard 검증 |
| PREOPEN → loader/PID | loader가 같은 날짜·bundle hash·scope 정책을 읽고 실제 판정에 사용한 receipt. 파일 선택·bootstrap 성공과 구분 |
| evaluator → summary/checklist/strict | proxy/operating/actual·source gap/sample·평가 수/독립 후보 수를 보존. 메인 값으로 compact receipt를 덮거나 incumbent EV를 이유 없이 null로 투영하지 않음 |
| 자연 판정 → 다음 장후 | 적용 bundle/threshold/prompt/model version별 exact outcome을 연결해 R6를 분리 산출 |

다음 장전 산출물은 기존 `data/runtime/mechanistic_entry_policy/policy_<next-trading-date>.json`이다. 현 시점 예상일은 9/21이나 구현 시점·거래소 달력·PREOPEN freeze를 다시 확인한다. 이미 소비되거나 동결된 당일 정책을 덮어쓰지 않는다. 새 후보가 기준을 통과하면 해당 scope의 검증 정책, 없으면 최신 평가 사유가 결속된 incumbent carry를 발행한다. 필수 기존 정책 자체가 없거나 무효이면 carry 성공으로 가장하지 않고 기존 fail-closed 경로를 유지한다.

후보 승격 없는 carry는 운영 연속성의 성공이다. **이를 EV 개선·모든 구조결손 해소로 계산하지 않는다.** 새 후보를 보장하는 계획은 아니며 경제성 미산출 결손이 남아 있으면 전체 완료를 선언하지 않는다. 정책 파일 생성만으로 actual PID/자연 수익을 완료 처리하지 않는다.

### 14.8 ME13 — 최소 구현 순서·리뷰·회귀

| 순서 | 책임·선행 | 종료 증거 |
| --- | --- | --- |
| A | ME8, 현행 release·원천 고정 | changed 8건의 결손 위치, source/model/prospective 판정; 무근거 복구 불가/자연 대기 제거 |
| B | ME9, compact EO1/EO2의 공유 계약 대사 | 당시 입력의 실행 arm·비노출 arm·CF plan·비용/exit 모델 지원 검증 |
| C | ME10, B의 지원 scope | episode/일자/자본 보존, 활성 scope 처분, hierarchy의 독립 full 경제성 gate |
| D | ME11, B/C | 실행 경제성 중심 순위·동률·freeze/미사용 holdout·proxy 분리 |
| E | ME12, A–D 검증 | bundle→PREOPEN→loader 및 summary/checklist/strict의 동일 계약 |
| F | ME14, E review finding 0 | 영향 구간 재생성·다음 날짜 정책·정량 결과 및 미해결 목록 |

각 단계는 구현→self review→수정→재리뷰→targeted validation을 수행한다. 외부 세션의 같은 helper 변경은 source hash로 대사하고 영향 경로만 재검증한다. 검증 없이 먼저 비싼 보고서를 생성하지 않는다.

필수 fixture는 기존 calibration/compact/owner replay/policy/summary/checklist/strict test 파일에 추가한다.

1. report scope/refresh flag만 정상이고 owner writer 필드가 없으면 source_gap이며 natural wait 아님.
2. 실제 ENTER→후보 비진입에 후보 fill을 요구하지 않음; 기존 arm 비용·자본 누락은 null.
3. 실제 BLOCK→후보 ENTER: 유효 frozen context+검증 모델의 연구용 plan은 계산 가능; AI/quantity/guard 결손이면 승격 불가. 실제 호출·계획으로 위조하지 않음.
4. 전부 BLOCK/전부 VETO에서도 raw census 보존; 실제 AI 미호출을 모델 품질 실패로 학습하지 않음.
5. 같은 opportunity 여러 RECHECK, cross-owner/route, scope별 같은 종목, 자본 중복·cooldown 경계의 보존/배제.
6. 정상 무거래일·손실일·원천 결손일, partial/held/no-fill·후행 exit 개정의 분모/비용 처리.
7. proxy EV 1위와 원화/day 1위가 다르면 규칙대로 실행 지원 후보를 선정. EV 개선/일별 순익 악화 후보는 탈락.
8. 80개 동률에서 incumbent 또는 가장 가까운 허용 좌표를 선택; holdout을 이용한 대표 교체·차순위 재선정 금지.
9. KRX 공통 후보 불합격과 무관하게 지원된 scope/child의 진단 계산 가능; 동일 full gate 미통과 child 우회 발행 금지.
10. source/model/cost/parent/scope/hash 불일치·이미 freeze된 날짜·다른 compact generation의 발행 및 loader 차단.
11. eligible fixture의 next-date publication→PREOPEN→loader 성공, no-edge fixture의 carry 및 gap fixture의 repair 전달.
12. 표본 floor 미달이어도 지원된 수치 출력, 손익 null을 0으로 바꾸거나 proxy를 operating EV로 표기하지 않음.

관련 pytest/변경 Python compile, wrapper 변경 시 `bash -n`·해당 contract test, `git diff --check`를 수행한다. Provider는 mock/offline을 기본으로 하고 runtime API/request/parser를 바꾸지 않는다. protocol 변경이 불가피하면 해당 범위에만 공식 Kiwoom reference gate를 수행한다.

### 14.9 ME14 — 제한 재생성·최종 완료 판정

후속 구현 승인 후 검증된 code generation에서 실행한다. 기존 wrapper/CLI의 실행 옵션은 구현 시 확인하며 새 운영 CLI를 만들지 않는다.

1. 재생성 전 frozen source/model/candidate/holdout 소비 이력·현재 bundle을 보존한다. changed 8건과 영향 scope를 먼저 복구·계산하고 동일 fingerprint의 무변경 재실행을 금지한다.
2. 최초 변경 producer가 source projection/owner replay이면 해당 날짜·scope만 갱신한다. 그 뒤 source-quality admission → machine full evaluator → 필요한 compact 결속 → 단일 publisher 순으로 실행한다. compact prompt 재탐색/Provider 재호출은 기계 연결 수리만으로 자동 요구하지 않는다.
3. 새 main 결과/정책에 영향을 받는 runtime summary → workorder/gap/lineage의 현재 활성 소비자 → tower → checklist → strict verifier → controller까지 기존 의존 경로를 필요한 범위로 갱신한다. 이미 퇴역한 Daily/EV 단계는 생성하지 않는다. unchanged artifact는 original source date/hash를 유지한다.
4. next-date policy와 기존 PREOPEN 검증 경로의 날짜·parent·source/model/metric hash를 확인한다. 정상 예정 PREOPEN·PID 소비는 자연 후속으로 분리하며 수동 env/lock·즉시 hot reload로 대체하지 않는다.
5. 긴 작업에서는 기존 projection/checkpoint를 재사용하고 비필수 상세 설명·추가 hierarchy 분석을 줄인다. 미평가 수/범위를 남기며 동일 모집단·비용·자본·holdout의 핵심 검증은 줄이지 않는다. 성능 framework·과도한 guard·반복 benchmark는 추가하지 않는다.

완료는 네 상태를 별도로 기록한다.

- **코드/구조 closure:** ME8–ME12와 직접 소비자의 actionable finding 0, 상태 오분류 0, 실제 미지원 설계는 별도 OPEN. offline 성공만으로 원천 결손 해소를 선언하지 않는다.
- **경제성 산출:** 실제 보존 원천의 지원된 독립 비교에 대해 기존/후보/Δ EV, 비용/stress, 원화/day, 표본·episode·날짜·tail·capital을 산출한다. 수익은 음수·개선 없음이어도 유효 결과다. proxy-only·전부 동일 행동·전부 null은 이 목표의 완료가 아니다. 실제 원천으로 도달 불가하면 첫 결손과 exact 복구 불가 근거·미래 생성 검증·다음 유입 조건을 남기고 경제성 목표는 OPEN으로 유지한다.
- **발행/소비 준비:** 검증된 next-date candidate 또는 유효 incumbent carry, source/policy/consumer hash 일치. eligible fixture의 자동 소비 검증과 실제 발행 결과를 모두 기록한다.
- **자연 성과:** 실제 PREOPEN/PID receipt·판정 변화·`COMPLETED + valid profit_rate`의 비용 후 성과. CF 결과나 release selection으로 대체하지 않는다.

기존 `MainMechanisticEntryPostcloseLoopRestore0920`는 최초 루프 복구 receipt를 보존한다. 후속 구현·재생성 시 확인된 새 결손 때문에 필요한 범위만 재개하고 기존 direct-family 자동 항목의 역할을 조정한다. 새 일정 ID를 중복 생성하지 않는다. 9/20 checklist가 없으므로 계획 문서에서 오늘 실행 owner를 발명하지 않으며, 다음 실제 실행일 checklist의 한 owner로 인계한다.

이번 문서 변경의 검증은 링크/owner/권한/기존 계획과의 중복 검토·print-only backlog parser·diff check다. 실API·Provider·경제성 재생성·정책 갱신·배포는 실행하지 않는다.


### 14.10 9/20 구현·재생성 receipt

[메인 기계 operating evidence 보완 리뷰](../audit-reports/2026-09-20-main-machine-operating-evidence-closure-review.md)를 따른다. 471개 배포본 회귀 통과, scoped publisher/consumer 검증과 9/21 incumbent carry 발행을 확인했다. 원화 operating enrichment0·비용 후 EV/day 미산출 및 ME8/ME9/ME10 잔여, 과거 native terminal 누락은 OPEN이다. §14 전체 종결 또는 자연 수익 개선 receipt가 아니다.

### 14.10 이번 후속의 지원 범위·원천 계약 정정

사용자는 BLOCK/RECHECK에도 기존 `kt00011` bounded 계좌 읽기를 허용했다. AI 추가 호출·주문·예약은 금지한다. 기존 source-only 요청(1회, rate 대기0, connect/read timeout 각각0.15초)을 그대로 사용하고, clone 위에서 기존 sizing/price/guard/exit owner를 적용한다. 실패는 그 시점의 원천 결손이며 현재 계좌로 과거를 복구하지 않는다.

2026-09-21 추가 수리 승인: 비동기 스캐너의 기존 market-preparation worker에서 최종 시세 갱신 전 source-only 증거를 준비한다. 공유 한도/주문 우선권은 그대로 두고 기존 source-only 대기 상한1.25초 및 worker 잔여 deadline 안에서만 수집한다(transport 여유0.30초 제외). 관측 시점에는 계좌·종목·가격·주문/잔고 세대가 일치하는 2초 이내 성공 증거만 재사용한다. 동기 관측의 rate 대기0, 주문 직전 fresh 조회와 최종 시세/취소/deadline 검증은 유지한다. 과거 결손은 소급 복구하지 않으며 날짜형 DB 상태는 원형 보존 직렬화한다. [수리·검증·배포 근거](../audit-reports/2026-09-21-preflight-submit-bottleneck-repair.md).

- ENTER/BLOCK/RECHECK 관측 계획은 실제 machine action을 유지한다. non-entry에는 compact PASS/VETO 또는 AI 응답 시각을 만들지 않는다. 기존 split producer가 `nonentry_plan_only`를 보존하고 main evaluator가 직접 소비한다. 원래 AI 미호출 지점을 새 ENTER로 바꾸려면 exact 보조 판정이 별도로 필요하며 없으면 `frozen_auxiliary_verdict_missing`이다.
- 동일 promotion의 RECHECK는 시간순 후속 판단으로 이어진다. 원천 모집단의 모든 평가가 남았는지 확인한다. 실제 WATCHING TTL owner의 기한·종료 receipt가 일치할 때만 비노출 종결한다. FIFO는 같은 CF 큐 점유가 입증되지 않으므로 TTL로 대체하지 않는다. 미종결 RECHECK는 pending이다.
- 경제성의 지원 실험은 **동일 frozen 현금 한도·동일 총수량의 조건부 비교**다. 실제 계좌 전체 수익을 복원하는 backtest가 아니다. 동시 reserve/보유 종목을 시간순으로 처리하고 이익 재투자는 하지 않는다. 관측 사이 승인 수량·budget가 바뀌거나 다른 owner의 현금 흐름 증거가 없으면 해당 비교를 `unsupported_scope`로 남긴다. 단순 표본 증가로 이 범위 제한이 해소된다고 보고하지 않는다.
- 모델의 calibration 완료일은 model holdout 시작일보다 빨라야 한다. 모델 오차와 stress의 하한은 실측 오차 범위이지 통계적 신뢰구간이 아니다. 모델 오차로 후속 자본 배정 여부가 바뀔 수 있는 경계는 별도 차단한다.
- 복수 scope는 calibration에서 전체 조합을 고정하고 이후 날짜의 독립 holdout을 검증한다. scope별 통과분만 사후 조합하지 않는다. publisher는 동일 조합·source rows로 공통 자본 계산을 재검증한다. 한 scope 및 hierarchy의 기존 개별 승격 기준도 보존한다.
- 기존 적용 버전별 완료 손익 owner를 main report에서도 소비한다. summary는 비용 차감 operating EV를 읽고 terminal-path proxy는 별도 진단 필드에만 둔다.

검증·배포·과거 원천 대사 및 잔여 범위의 최종 판정은 기존 [operating evidence 리뷰](../audit-reports/2026-09-20-main-machine-operating-evidence-closure-review.md)에 이어 기록한다. 합성 producer 회귀와 자연 모델 검증, 다음 PREOPEN/PID 소비는 각각 별도 증거다.

- full-population 선정/consumer의 경제성 지표는 검증된 운영 replay의 비용 차감 EV·paired Δ이며 terminal proxy는 진단이다. 기존 10bp·tail·holdout 기준은 유지한다. 지원 밖의 변동 자본·AI 미호출·미종결 경로는 계약 미지원으로 기록하고 자연 대기로 숨기지 않는다.

### 14.11 후속 구현 closure — 2026-09-20 17시

§14.9 이전 실행의 ME8/9/10 OPEN은 당시 기록이다. 후속 `beb0c1578`→`f339f47bb`→`e89e9da12`에서 지원 범위 producer/순차·동시 자본 replay/실제 경제성 선정/다중 scope 검증/alias 분모 및 소비 회귀를 닫았다. 상세 범위·미지원 운영 계약·308개 최종 회귀·정책·terminal 증거는 [리뷰의 최신 종결](../audit-reports/2026-09-20-main-machine-operating-evidence-closure-review.md#920-17시-후속-종결)을 따른다. 9/21 incumbent 준비와 경제성 입증은 분리한다. 과거 원천 결손, fixed-capital v1 밖의 운영 계약, 자연 model/candidate holdout 및 실제 PID/완료 손익은 이 구현 closure로 해결되었다고 주장하지 않는다.

## 15. 변동 자본·부분 체결·미호출 AI의 지원 범위 보완계획

작성: 2026-09-20. 상태: **조건부 지원 범위 구현·회귀·배포·제한 재생성 완료 / 추가 운영 계약 미종결**. 기존 ME8–ME13의 후속 범위이며 별도 evaluator·정책 family를 만들지 않는다. 2026-09-20 후속 구현 승인을 반영한다. 기존 완료·이번 보완·미확정 운영 계약을 구분한다.

### 15.1 현재 근거와 완료 판정 정정

- 코드 기준은 선택 release `main-machine-operating-completion-20260920-e89e9da12`이다. 기존 bounded 계좌 읽기 허용, 추가 AI 호출 금지, 주문·예약 없는 관측 승인 조건을 유지한다.
- `ai_action_outcome_calibration._machine_sequence_operating_metrics`는 같은 episode 내 수량/예산 변경을 `sequence_frozen_quantity_or_budget_changed`, 일중 공통 예산 변경을 `shared_cash_envelope_changed_without_cashflow_witness`로 제외한다. 최초 non-entry를 ENTER로 바꾸면서 실제 보조 판정이 없으면 `frozen_auxiliary_verdict_missing`이다.
- `strategy_owner_replay.replay_entry_opportunity`에는 관측된 깊이/가격에 기반한 지원 체결·청산 계산이 있다. 부분 체결 전체가 미구현인 것은 아니다. `passive_queue_fill_or_partial_unproven`, 취소 경합·late fill·미청산 경로를 구분하여 보완한다. 기존 지원 arm을 재작성하지 않는다.
- 고정 자본 v1의 합성 회귀 완료는 변동 계좌·수량·모든 주문 경로의 지원 완료가 아니다. 9/17 원천의 `machine_operating_population_unbound`, 신규 후보0, 운영 ΔEV·원화 순익 null은 그대로 유지한다. 준비된 9/21 incumbent와 신규 경제성 입증은 별개다.
- 9/20 daily checklist 파일은 확인 시 없었다. 9/21 checklist는 다음 적용일의 실제 owner 문서로만 참조하며 현재 날짜 문서로 가장하지 않는다. 그 안의 과거 완료 문장과 최신 리뷰가 다르면 최신 receipt/코드를 우선하고, 실제 구현 시 기존 자동 owner를 재생성하여 정합화한다. Plan Rebase의 퇴역 축 언급도 현행 코드 권한으로 복원하지 않는다.

### 15.2 경제성 비교의 고정 조건

검증 질문은 “동일한 초기 자본과 외부 조건에서 기계 판단만 달라지면 비용 차감 일별 순익·EV·tail·점유가 개선되는가”이다.

1. 각 arm은 동일한 초기 사용 가능 자본, 기존 승인 한도, 공통 guard, 외부 현금흐름과 당시 관측을 사용한다. 실제 후행 계좌 잔고를 candidate의 잔고로 복사하지 않는다.
2. 판단 시점별 승인 가능 수량·가격·비용 원천은 frozen 입력으로 보존한다. 자본 때문에 실행하지 못한 기회도 분모에 남긴다. 후보 수량·cap을 늘리거나 제출 순서를 수익 최대화 방식으로 사후 재배열하지 않는다.
3. 재평가 중 수량이 달라지면 같은 attempt라고 덮어쓰지 않는다. 새 attempt의 당시 승인 수량과 planner 입력을 연결한다. 실제 입력으로 재현 가능한 pure planner만 사용하며, 한 arm의 수량만 임의 축소해 비교를 성립시키지 않는다.
4. owner별 독립 예산인지 공통 계좌 제약인지 기존 운영 원장으로 확정한다. 삼성 owner별 승인 수량 독립 비교 승인을 메인·위젯·에피소드 통합 자본 승인으로 확대하지 않는다.
5. 위젯·수동 주문 등이 메인의 가용 자본에 영향을 주면 실제 동일 외부 흐름을 조건부 고정할 수 있는지 확인한다. candidate 행동에 따라 그 외부 주문도 달라지는 경합은 독립 외생 흐름으로 가장하지 않는다. 해당 상호작용은 명시적 미지원으로 분리한다.

### 15.3 ME8/ME10 보완 — 원장 기반 변동 자본 재현

기존 계좌 관측·주문 owner·custody·체결 원장을 재사용한다. 새 collector/DB와 반복 계좌 조회를 만들지 않는다.

| 입력/경계 | 구현 사항 | 검증 완료 조건 |
| --- | --- | --- |
| 시작 snapshot | source timestamp, 계좌/owner 식별자, 승인 예산·주문 가능 금액·기존 보유/예약, 원천 version/hash를 결속. 계좌 비밀정보는 보고서에 복제하지 않음 | 초기 자본과 별도 reserve를 이중 차감하지 않는다는 원장 대사 |
| 주문→체결→취소 | parent/attempt→owner→broker order→fill ID→취소 확인을 연결. 예약→보유 전환, 확정 미체결 취소분 해제, late fill 반영 | 주문/체결 중복·순서 역전·취소 경합에서도 수량·현금 보존 |
| 매도·비용·자본 반환 | 자기 arm의 청산 계약과 순매도대금 사용. 결제 전 대금의 재사용 가능 여부는 기존 broker/account owner 의미를 따름 | 매도대금·실현손익·원금의 중복 가산0; 실제 계좌 원천과 대사 |
| 입출금·한도 변경 | 증거 있는 외부 흐름만 동일 timestamp로 두 arm에 주입. snapshot 차이를 임의 입출금으로 추정하지 않음 | 흐름 적용 전후 balance가 일치하거나 구체 미대사 잔차 반환 |
| 겹친 기회/scope | 기존 전역 시간순 실행과 owner/custody 사용. 자본 부족·동일 종목 보유로 막힌 기회도 기록 | 두 scope가 같은 자본을 동시에 쓰는 회귀가 차단됨 |

가용액·예약액·보유 원가·수수료/세금의 보존식을 현금과 자산 장부로 분리한다. 체결 시 현금 차감과 예약 해제를 두 번 비용 처리하지 않는다. `reserve_krw_minutes`와 `capital_krw_minutes`는 서로 다른 진단값이다. peak exposure, overlap 거절 수, 비용 후 일별 순익을 함께 산출한다.

첫 지원은 **증거가 완전한 외부 흐름 + 기존 승인 수량 + 비선견적 실행 순서**다. CF마다 가능한 재진입/손실 이후 현금은 각각 계산한다. 이익 재투자 여부는 기존 자본 owner 규칙에 따르며 고정 자본 v1의 무재투자를 설명 없이 변경하지 않는다. 흐름 결손은 해당 공유 자본 경로와 영향을 받는 후행을 격리하고, 전체 영향 경계를 특정할 수 없을 때만 해당 자본 cohort를 차단한다.

### 15.4 ME8/ME9 보완 — 부분 체결·취소·미청산

운영 원장 상태와 가상 후보 체결 모델 상태를 별도로 둔다.

- 실제 주문은 승인 수량 = 누적 체결 + 확정 취소 + 유효 잔량으로 대사한다. 정정/취소 재주문은 parent lineage로 연결하고 누적 체결 통보를 신규 fill로 중복 합산하지 않는다.
- 취소 요청만으로 잔량·reserve를 해제하지 않는다. 취소 확인 이전 체결과 지연 통보를 처리한 뒤 terminal 여부를 판정한다.
- 실제 완료 손익은 소유권이 확정된 체결 lot의 실제 비용·매도 결과만 사용한다. manual custody 이전, HELD, 비용 미확정은 별도 상태다.
- 후보 arm은 같은 관측 호가/거래와 검증된 도착·체결·취소 모델로 자신의 체결 수량을 산출하고, 그 수량에 자기 청산 계약을 적용한다. 실제 전량 SELL을 다른 부분 체결 arm에 붙이지 않는다.
- passive queue 순서가 관측되지 않으면 정확한 fill을 만들지 않는다. 가능한 보수적 실행 구간이 검증된 경우에만 구간을 사용한다. 가능한 결과 사이에서 후보 우열/자본 가용성이 뒤집히면 승격하지 않는다. 검증되지 않은 구간 모델 자체도 지원으로 간주하지 않는다.
- 정상 원장이 연결됐고 terminal 시각만 미도래이면 `pending`; 이미 종료됐는데 identity/원천이 없으면 `source_gap`; 지원 모델이 없으면 `unsupported_scope`다. 모두 0원 무거래와 구분한다.

### 15.5 ME9 보완 — 미호출 AI의 실제 판단 차이

추가 AI 호출 없이 즉시 지원할 후보부터 기존 후보 공간 안에서 평가한다.

| 판단 변경 | 지원 조건/처리 |
| --- | --- |
| 실제 ENTER→후보 BLOCK/RECHECK | 실제 당시 AI·가격·수량·비용이 연결된 incumbent와 후보 비노출/후속 sequence 비교. RECHECK는 영구 BLOCK이 아님 |
| 실제 RECHECK→후속 실제 ENTER | 후속 timestamp의 자기 AI 판정과 가격/계획만 사용. 그 결과를 앞선 RECHECK 시점으로 이동 금지 |
| 실제 BLOCK→후보 즉시 ENTER | 같은 cutoff의 검증된 AI replay가 없으면 full-chain EV 미지원. 기계 upstream 기회 진단과 운영 개선을 분리 |
| 동일 행동 | 기준 보존/모델 대사에 사용. 순수 자기 비교를 새 후보/ΔEV 개선으로 세지 않음 |

미호출 AI를 해결하기 위해 임의 PASS·VETO를 만들거나 장중 추가 AI를 호출하지 않는다. 누락된 당시 저장 response가 실제 존재하면 exact request/response hash로 제한 복구한다. 별도 offline 재판정은 현재 금지된 추가 AI 호출의 예외 승인이 필요한 옵션이며 기본 구현의 필수 조건으로 두지 않는다.

그 옵션을 나중에 열 경우 고정 prompt/model·당시 payload·단일 response·측정된 비용/지연·독립 model holdout을 갖춘 modeled 판정으로 표시한다. 현재 모델이 과거 모델과 같다고 가정하거나 offline 결과를 실제 자연 AI receipt로 바꾸지 않는다. 미호출 영역의 원천 보존/차단 사유/지원 후보 실행은 그 승인 없이 구현 가능하다.

### 15.6 ME11/ME12 보완 — 계산·선정·정책 소비

1. 기존 `strategy_owner_replay`, `entry_split_order_plan`의 운영 proof/비용 모델 및 `ai_action_outcome_calibration`을 확장한다. 새 비용·청산·tolerance 수치를 만들어 비교를 통과시키지 않는다. Kiwoom request/parser 자체를 수정해야 하는 경우에만 기존 Official Reference Gate를 수행한다.
2. 실제 운영 모델 오차를 독립 chronological model holdout에서 검증한다. 후보 탐색/calibration 이후 별도 candidate holdout을 사용한다. 이미 분석한 9/17을 새 독립 표본으로 사용하지 않는다.
3. 동일 기회·자본의 paired 원화 순익/EV, 일별 순익, tail, reserve/보유 노출, 체결 참여율, 자본 부족 누락을 함께 산출한다. EV 분모는 기존 명명된 계약을 유지하고, 원화 ΔPnL·자본 대비 수익률·거래당 EV를 혼합하지 않는다.
4. 모델 오차·stress를 포함한 보수적 ΔEV 하한으로 선정한다. 현금 경계의 불확실성이 후행 제출 가능 여부를 바꾸면 경로 전체를 보수적으로 재평가한다. 기존 10bp·표본·tail·holdout gate를 완화하지 않는다.
5. 입력별 `source_gap / unsupported_scope / pending / insufficient_sample / valid_no_edge / eligible`와 구체 blocker·owner·closure test를 반환한다. 후보0 대표 사유와 전체 원인별 수를 함께 남기며 source gap이 valid no-edge에 섞이지 않게 한다.
6. 기존 publisher→dated policy→summary/checklist→PREOPEN reader→장중 loader를 그대로 사용한다. 지원 범위·모델 version/hash가 바뀌면 stale proof를 무효화한다. 기존 유효 incumbent/fallback 및 operator override는 유지한다.
7. 실제 적용 버전별 episode 중복 제거와 rolling/cumulative 완료 비용 손익 경로를 검증한다. 탐색 모델 ΔEV, 실제 순익, 인과적 개선은 별도 필드다.

### 15.7 구현 순서와 회귀 종료 기준

| 순서 | 기존 owner 내 작업 | 필수 회귀/closure |
| --- | --- | --- |
| E0 | 선택 release/병행 변경 및 원천 contract 대사 | 과거 결손·현재 지원·추가 구현·자연 대기를 분리한 표, 기존 v1 재사용 증거 |
| E1 | ME8/10 현금흐름·주문 lineage | 기존 운영 producer의 snapshot/주문 이벤트→저장→projection 연결, 미래 생성 가능 입력과 최초 결손 분리 |
| E2 | ME9 부분 체결/cancel·E1 자본 전이 | 부분 체결 후 취소·late fill·순서 역전·중복·미청산·manual custody·외부 자본 변화·동시 두 scope의 수량/현금 보존 |
| E3 | ME9 supported AI/RECHECK 비교 | 세 방향 판단 변경의 지원/미지원 명시, 실제 후속 ENTER 연결, AI 호출0·주문0·관측 reserve0 |
| E4 | ME11 경제성/독립 검증 | 지원 양수·음수·동률, 자본 경합에 따른 우열 변경, 오차/stress 경계, holdout 오염 차단 |
| E5 | ME12 소비 | 정상 활성 후보 생성/소비, stale/hash/date/scope/model 실패의 incumbent/fallback, 적용 버전별 실제 성과 분모 |
| E6 | ME13 리뷰/제한 재생성 | 운영 producer부터 연결한 fixture와 자연 자료를 별도 보고. 바뀐 owner와 후행만 재실행, 기존 receipt/rollback 보존 |

각 단계는 구현→리뷰→수정→재리뷰→영향 pytest/compile/diff로 닫는다. 수동 완성 evaluator 입력만으로 E1/E2를 완료하지 않는다. 임의 비용을 사용하는 fixture를 운영 계약의 근거로 삼지 않는다. 완전한 지원 fixture에서 실제 계산·후보 선정이 작동해야 하며 전부 null을 반환하는 구현은 불합격이다.

**완료 조건:** 실행 가능한 E0–E6 구현과 회귀에 미완료가 없고, 자연 표본 부족과 승인되지 않은 AI 확장/미확정 운영 의미가 별도 표로 남아야 한다. unsupported를 완전히 없애는 것이 아니라, 일상적으로 발생하는 지원 가능한 자본·체결 경로를 영구 결손으로 방치하지 않는 것이 목표다. 유효 비교 수/전체 수, changed 비교 수/전체 changed 수, 첫 blocker 분포로 개선을 측정한다. 양수 후보 수를 구현 완료 목표로 강제하지 않는다.

### 15.8 내일 기동 및 의미적 감시와의 관계

9/21 incumbent 준비를 이 확장 연구 때문에 취소하거나 조기 PREOPEN으로 바꾸지 않는다. 배포 요청 시점에 이미 freeze/기동됐으면 실행 중 release·당일 정책은 보존하고 검증된 후속 적용일로 보낸다. main/widget/episode는 각각 기존 정책·기동/guard owner를 따른다.

장중 source 결손·ENTER 부족·AI VETO 집중·PASS 후 미제출의 지속 감시는 별도 장중 의미적 이상 감시 검토계획이 소유한다. 감시 알림은 경제성 후보 선정이나 자동 threshold 변경 권한이 아니다. 본 절은 ME8–ME13의 상세 보완 owner이고, 통합 복구 계획은 배포/후행 인계 owner를 유지한다.

### 15.9 구현 범위 확정과 잔여 운영 계약 (2026-09-20)

- 기존 `kt00011` bounded 읽기의 normalized capacity hash/clock, 계좌 비밀정보를 제외한 account hash, 종목별 승인 cap과 예수금 구성요소를 기존 frozen operating context에 저장한다. 새 호출·원장·collector는 없다.
- `entr` 예수금과 종목별 주문가능금액의 변화를 입출금으로 환산하지 않는다. **첫 승인 예산을 고정한 조건부 실험**에서 시점별 새 승인 수량/cap, 자기 arm의 reserve→보유→확정 취소→독립 청산을 재현한다. 동일 시각의 시작 예산 충돌이나 예수금 basis 변화는 명시적 제외한다. 실제 계좌의 결제 전 재사용 가능 대금·외부 입출금·타 owner의 반사실 행동까지 재현하는 계좌 backtest는 운영 계약 미확정이다. 자연 표본 대기로 분류하지 않는다.
- 부분/무체결은 기존 cancel owner의 과거 독립 모델과 해당 상태의 운영 model holdout을 모두 요구한다. 연속 native 관측에서 잔여 limit 미접촉을 확인하고, 취소 ACK/late-fill 종료 이전에는 예약금을 반환하지 않는다. 보유 판단 frame을 취소 전이라는 이유로 삭제하지 않는다. 실제 SELL을 후보 청산으로 복사하지 않는다.
- 취소 전 조기 청산이 추가 취소를 요구하는 경로, 서로 다른 child 취소시각, 체결 사이 보유 상태 전이가 필요한 경로, 관측되지 않은 passive queue 순서는 현재 모델 지원 밖이다. 기존 모델에 없는 ACK·체결 확률을 만들지 않는다. 이는 전체 부분 체결 차단과 다르며 정상 지원 입력의 계산 회귀를 별도로 둔다.
- 미호출 AI는 추가 호출 금지를 유지한다. 실제 후속 ENTER에는 그 시점의 frozen AI만 사용한다. BLOCK을 즉시 ENTER로 바꾸는 데 당시 AI가 없으면 full-chain EV를 산출하지 않는다.
- 구현 종료는 위 조건부 지원 범위의 생성→저장→계산→독립 검증→정책 인계에 적용한다. 미확정 계좌 운영 의미/미지원 모델 확장을 전체 완료 또는 자연 대기로 표시하지 않는다. 이번 리뷰·검증·배포 증거는 기존 메인 운영 경제성 closure 리뷰에 기록한다.

최종 evidence: 코드 `5d60b4afe`, run `f7e6be607be944b8a45fa8f5775494a8`, source9/17→publication9/20→effective9/21. main succeeded/controller done/strict pass. `tmp/main-machine-capital-partial-20260920/final-reconciliation.json`에 정책·서비스·자연 결과를 대사했다. 신규 승격0·운영 EV null이며 자연 경제적 개선은 입증되지 않았다.


런타임 생산자 역추적에서 새로 확인한 자본 시점·설치 source binding·scanner 생성 불가능 입력·SOR 소비 제한은 [통합 계획 §12 PR0–PR5](./postclose-integrated-verification-recovery-and-next-preopen-readiness-plan-2026-09-20.md#12-런타임-생산자-역추적-결함의-최소-보완계획)가 소유한다. 기존 ME8–ME13을 재작성하지 않으며, 이 링크는 후속 구현/배포 완료를 뜻하지 않는다.

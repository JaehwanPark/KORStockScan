# Compact 보조 AI의 paired 경제성 튜닝·후행 소비 상세개선계획

작성 기준: 2026-09-18 KST. 사용자 요청에 따른 **계획 수립**이다. 코드 변경·provider 호출·보고서 재생성·정책 발행·배포·기동 receipt가 아니다.

기존 [통합 기회비용 구현계획](entry-opportunity-cost-full-population-tuning-implementation-plan-2026-09-17.md)의 **U8 → U11 → U12 연결을 구체화**한다. 별도 튜너/실행 owner를 추가하지 않는다. 실행 owner는 [오늘 체크리스트](../checklists/2026-09-18-stage2-todo-checklist.md)의 `KiwoomCommonHealthOpportunityCostAcceptance0917`을 유지한다. 다른 세션의 `entry_split_order_plan` 검증은 독립 작업이며 완료를 이 연구의 선행조건으로 만들지 않는다.

## 1. 확정 방향과 현행 진단

목표는 Main 기계의 `ENTER_NOW` 이후 compact AI 판정이 불필요한 미진입을 줄이면서 위험한 진입을 차단하도록, **같은 입력·같은 실행 조건의 기존/후보 정책을 비용 후 EV와 일별 순익으로 비교**하는 것이다. 기계 선정·가격·수량·주문 권한은 기존 소유자가 유지한다. 실제 체결은 자연 성과 검증에 사용하며, VETO 때문에 미체결된 기회도 원천이 유효하면 CF 평가할 수 있다. scale-in의 체결 조건부 평가와 구분한다.

현재 selected release는 `data/runtime/runtime_release_selection.json`의 `scale-in-final-reviewed-20260918`, source commit `54fe6399b2135706671d259788ade8d01bc5381f`이다. 이번 확인에서 아래 calibration/optimizer/consumer/runtime-policy 네 모듈은 작업본과 selected release의 내용이 일치했다. 이 사실은 실제 PID 소비를 뜻하지 않는다.

| 확인한 연결/결과 | 진단 | 필요한 보완 |
| --- | --- | --- |
| `ai_decision_quality.build_daily_materialization_reports`의 9/17 paired 준비 10건, 응답 0건·비교 0건 | 이 단계는 `results=[]`로 준비물만 생성한다. 기본 후보는 legacy BUY/WAIT/DROP 역할이다 | compact 역할의 실행 분기와 완료 receipt를 연결한다. 준비 건수를 비교 실적으로 집계하지 않는다 |
| 현행 `main_ai_prompt_optimizer.compact_evaluation_plan` | 자연 기록만 소비하며 `provider_calls=0`, `candidate_improvement_proven=false`, `legacy_replay_may_tune_compact=false`를 명시한다 | 이미 있는 compact 평가 경로를 확장한다. legacy detailed replay를 compact 후보 응답으로 사용하지 않는다 |
| `ai_action_outcome_calibration` → `main_ai_prompt_consumer` → `mechanistic_entry_runtime_policy` | 비용 후 미진입 이익·위험 PASS·회피 손실을 통해 등록된 프롬프트 방향을 선택하고 미래 날짜 bundle로 전달하는 경로가 있다 | 방향 선택과 후보의 paired ΔEV 입증을 분리하고, 입증 결과의 해시를 같은 경로에 결속한다 |
| generic baseline의 `source_quality_adjusted_ev` | 시장 수익률 기반 decision proxy이며 비용 후 금액 순익이 아니다. 9/17 baseline 14건과 paired 준비 10건도 분모가 다르다 | proxy를 진단으로 남기고 공통 paired 모집단의 net 지표를 primary로 사용한다 |
| 9/17 generic primary eligible 15건 중 10분 관측 가능 14건, 해당 14건 모두 exact stop distance 결손 | mature 표기가 실행 가능한 손절·비용 경로를 보장하지 않는다 | 최초 결손 경계를 기록하고 실행 plan/exit/cost owner에 연결한다. 시간을 기다리는 것으로 해결했다고 판단하지 않는다 |
| 9/17 현행 source-quality receipt의 compact provider 호출 21건과 generic paired 준비 10건 | scope·버전·역할이 다른 집계다 | 21→10 누락이라고 단정하지 않고 모집단 reconciliation을 작성한다 |
| legacy candidate lifecycle 0건·R0/R3 source block | retired/연구 scope의 상태다 | 현행 compact 자연 기록의 전역 차단 조건으로 승계하지 않는다. 필요한 직접 원천만 검증한다 |

증거: [9/17 원천 품질 보고서](../../data/report/observation_source_quality_audit/observation_source_quality_audit_2026-09-17.md), [paired 준비 보고서](../../data/report/ai_prompt_paired_replay/ai_prompt_paired_replay_2026-09-17.json), [baseline](../../data/report/ai_decision_quality_baseline/ai_decision_quality_baseline_2026-09-17.json), `tmp/postclose_stepwise_2026-09-17/{request,result,review}_1021.json`, `review_1022.json`.

## 2. 모집단·원천 계약: 먼저 비교 가능한 기회를 만든다

하루의 모집단을 다음 순서로 대사한다. 중복 stage/attempt는 canonical evaluation key로 정리하고 충돌 행은 위치를 보존하여 제외한다.

1. Main 기계 전체 decision census: BLOCK/RECHECK/ENTER_NOW를 구분한다. AI를 호출하지 않도록 설계된 BLOCK/RECHECK는 정상 미호출이다.
2. AI 심사가 필요한 ENTER_NOW: 현재 적용 machine bundle, compact prompt version/body hash, provider/model, owner, venue/session/route별로 분리한다.
3. 실제 심사 원천: frozen payload·issued prompt·raw response·terminal verdict의 계보가 일치하는 행만 후보 재판정에 사용한다. 미호출/실패/해석 불가를 VETO로 바꾸지 않는다.
4. 경제성 원천: decision 시점에 승인된 가격/수량 계획과 후행 가격·체결 가능성·손절/청산·비용이 확보된 행을 paired eligible로 삼는다. 제외 사유는 배타적인 최초 탈락 사유로 기록한다.

`screen_required = valid_screen + screen_failure + not_called` 및 `comparison_population = paired_eligible + exclusions`를 검증한다. semantic-valid, outcome-evaluable 등 중간 카운트도 따로 보고한다. 모든 행을 current version으로 재표기하지 않는다. KRX regular와 integrated/aftermarket를 섞어 한 cohort로 승격하지 않는다.

기존 자연 producer에서 compact payload와 **AI 거부 이전의 기계 실행 plan**이 이미 저장되는지 먼저 확인한다. 저장되지 않는 필드만 기존 projection에 보완한다. 사후 고점·저점이나 나중에 알게 된 주문가격을 frozen 입력에 넣지 않는다. 별도 수집기·DB·cron은 만들지 않는다. 실제 Kiwoom API/parser/continuation 수정이 필요할 경우에는 공식 reference gate를 별도로 충족한다.

## 3. 후보 실행과 선택: 현재 역할을 유지한 독립 비교

### 3.1 후보 고정과 실행

- 기존 compact registry의 incumbent·opportunity·risk variant를 재사용한다. 초기에는 학습 구간의 결손 유형으로 **서로 다른 후보 한 개**만 고정해 비교한다. incumbent가 선택되면 `incumbent_preserved`이며 신규 후보 검증 성공이 아니다.
- provider/model은 현행 OpenAI `gpt-5.4-nano`로 고정한다. 내부 prompt/schema는 English ASCII이고 출력·판정은 실제 compact runtime 계약을 따른다. 후보가 BUY/가격/수량을 새로 결정하게 하지 않는다.
- 동일 frozen payload에 incumbent와 후보를 재판정한다. incumbent는 동일 조건의 자연 응답을 우선 재사용한다. 자연 응답이 없으면 그 행은 기록된 자연 심사 모집단에서 제외하며, 별도 미호출 연구를 본 비교에 섞지 않는다.
- 기존 `entry_setup_paired_replay_batch`/`ai_decision_quality`의 실행·checkpoint·lock 경로에 compact 역할 분기를 넣는다. 기존 legacy 실행을 compact 호출로 묵시적으로 바꾸지 않는다. 연결 전에는 기존 `evaluation_mode`와 improvement false를 유지한다.
- 등록 후보·프롬프트 hash·payload hash·response schema·provider/model·budget scope를 실행 manifest에 고정한다. 기존 provider 승인/공유 ledger/상한이 compact offline scope까지 허용하는지 확인한다. legacy 연구 budget만으로 호출을 허가하거나 상한을 늘리지 않는다.
- idempotency key에 source day/evaluation key/payload/prompt/model/schema를 포함한다. 유효 응답은 재사용하고 실패·미완료 행만 재개한다. 응답 누락·timeout·잘못된 schema는 execution exclusion으로 남긴다.

### 3.2 학습·검증 및 후보 발행 기준

학습 날짜에서 후보를 고정한 뒤 시간순으로 분리된 sealed holdout에서 한 번 검증한다. 본 연구에서 이미 본 9/17 결과는 새 전향 holdout이라고 부르지 않는다. 실패한 후보 다음 순위를 같은 holdout에서 반복 선택하지 않는다. holdout consumption ledger와 candidate freeze hash를 기존 보고서/manifest에 결속한다.

기존 compact 방향 선택은 `economic_eligible>=20`, 관련 분모 5, error 3, error rate 0.25 등 기존 계약을 사용한다. 이 floor는 **후보 paired 검증이나 독립 holdout의 충분성을 보장하지 않는다.** 다른 기계 refinement/legacy의 holdout 숫자를 자동 이식하지 않는다. 초기 설계안은 cohort별 학습 적격 독립 episode 20건 이상에서 후보를 고정하고, **고정 이후 최소 2개 source day·독립 paired episode 20건 이상**을 전향 검증에 누적하는 것이다. 이는 신규 compact paired 검증의 제안값이며 현행 적용값·통계적 충분성 보증이 아니다. 날짜별 결과·불확실성도 함께 제시한다. 기존 승인 기준이 더 엄격하면 그 기준을 따른다.

CP0에서 이 설계안과 기존 canary/승격 계약을 대조하고, 후보 응답 coverage 최소값·cohort별 tail/stress 허용값까지 결과 조회 전에 확정한다. evaluator/publisher/verifier는 같은 계약 hash를 소비한다. 정의되지 않았으면 `promotion_contract_missing`으로 발행을 보류한다. 양수 결과를 만들기 위해 기준을 사후 완화하지 않는다. 9/17만 재생성해 새 holdout을 채웠다고 주장하거나 다음 장전 신규 승격을 보장하지 않는다.

개선된 경로에서 **경제성 튜닝으로 다른 compact 프롬프트를 신규 선정하려면** 기존 source/terminal/partition gate에 더해 공통 모집단의 비용 후 ΔEV>0, 동일 검증 거래일의 평균 portfolio 일별 순익 Δ>0, 독립 holdout·stress/tail 통과가 필요하다. 모든 개별 날짜 양수를 요구하는 조건과는 구분하며 날짜별 손실 악화는 기존 tail/rollback 기준으로 심사한다. 금액/portfolio 재현이 불가능하면 동시 개선 판정은 미확정이다. 현재의 비용 기반 방향 추천은 학습 후보 선정 입력으로 재사용한다. paired proof가 없을 때에는 기존 정책 보존/carry를 명시한다. 코드 계약 교정에 따른 명시적 migration은 성과 기반 승격과 구분한다.

## 4. 경제성 평가: 판정만 바꿔 실행 결과를 비교한다

각 기회 i에 대해 같은 기계 plan·가격/수량·예산·venue/session·후행 경로를 고정하고, compact 응답만 바꾼다. verdict는 기존 runtime router와 합성한다. PASS도 남은 guard를 통과해야 실행 가능하며 CAUTION/INSUFFICIENT의 실제 routing을 임의로 PASS/VETO로 축약하지 않는다.

- **실행 가능한 PASS**: 기존 replay의 full/partial/no-fill·취소·자금 점유·exit/stop 계약과 당시 유효 수수료/세금/슬리피지를 적용한다. 후보의 체결은 시뮬레이션이며 실제 fill로 표기하지 않는다.
- **최종 미진입**: 신규 포지션 순익 0은 routing·주문 부재가 확정된 경우만 인정한다. 같은 plan을 실행했다면 얻었을 비용 후 결과를 미진입 이익/회피 손실로 함께 표시한다. 원래 보유 포지션의 손익은 신규 진입 효과와 분리한다.
- **미청산/자료 결손**: 실현 순익 0을 종료 경제성으로 사용하지 않는다. realized/marked/open exposure와 terminal net을 구분하며 미확정 net은 null이다. CF terminal mark/exit를 쓸 때에는 기존 승인된 horizon/청산 모델과 한계를 명시한다.
- **VETO의 plan 부재**: 가격·수량·손절을 사후 추정하지 않는다. pre-veto 원천이 없으면 rate 진단까지만 허용한다. notional이 없을 때 퍼센트 CF는 가능하더라도 금액 일별 순익 개선은 미확정이다.

primary 계산은 비교 가능한 **공통 전체 모집단**에서 `delta_i = candidate_net_i - incumbent_net_i`, `ΔEV = sum(delta_i)/N`이다. 판정이 같은 행도 포함하며 Δ0이다. 가격 대비 퍼센트와 원화 금액은 단위를 분리한다. changed-verdict subset은 원인 진단용이다. 두 정책의 필터를 각각 적용해 서로 다른 분모의 평균을 빼지 않는다. 후보 timeout/실패를 임의로 빼서 좋은 결과만 남기지 않도록 준비 모집단 대비 paired coverage와 verdict/cohort별 실패 편향을 검사한다. 사전 고정 coverage 계약에 미달하면 진단만 게시하고 신규 선정은 보류한다.

일별 순익은 거래일별 기존 공통 allocation/capital replay로 계산한다. 겹치는 진입의 동일 현금을 중복 사용하지 않는다. 독립 episode 합산밖에 할 수 없으면 `independent_episode_cf_sum`으로 명명하고 실행 가능한 portfolio 일별 순익이라고 주장하지 않는다. CF 비용과 실제 provider 평가비를 구분해 표시하고, runtime inference 비용 차이도 단위·배분 기준을 고정해 반영한다.

보고 항목: N/coverage/exclusions, current-version·cohort별 incumbent/candidate net EV, 원화 일별 순익·Δ, 거래/미진입/부분체결/미청산, tail·stress·노출·자금 점유, verdict 전환 matrix, calibration/holdout 결과, selection reason. 유효 비교 후 개선0, 자기 비교, 준비만 완료, 원천 결손, 미확정 경제성을 서로 다른 상태로 표시한다. Actual 경제성은 applied-version 자연 `COMPLETED + valid profit_rate + 비용` 원장으로 별도 검증한다.

## 5. producer → 마지막 consumer 연결 설계

| 순서 | 기존 소유 경로 | 전달물과 downstream 확인 기준 |
| --- | --- | --- |
| 1 | 자연 source producer → `ai_decision_quality`/calibration case projection | frozen input/plan/route/version census와 배타적 exclusion manifest. compact/legacy 모집단 대사 성공 |
| 2 | optimizer의 compact plan → `entry_setup_paired_replay_batch` compact 실행 분기 | outcome-blind candidate freeze, source/prompt hash, scope별 요청/응답 checkpoint. terminal 비교 수와 provider calls 보존 |
| 3 | `ai_decision_quality` paired 경제성 evaluator | 동일 공통 모집단의 net 결과·일별 capital replay·holdout receipt. self comparison/미확정 null 구분 |
| 4 | `ai_action_outcome_calibration`의 `compact_auxiliary_screen_outcomes` | 자연 방향 추천과 paired 검증을 별도 section으로 결속. result/contract/holdout hash·selection disposition 전달 |
| 5 | `main_ai_prompt_optimizer.compact_evaluation_plan` 및 batch metadata refresh | 최종 calibration hash와 평가 mode 갱신. 당일 실행 후보는 변경하지 않고 다음 후보 선택은 다음 generation으로 넘김 |
| 6 | `mechanistic_entry_runtime_policy.publish` | 기존 날짜별 Main bundle에 등록 prompt와 proof hash를 발행/보존. `_selected_compact_prompt_version`이 evaluator와 동일 contract를 재검증 |
| 7 | `main_ai_prompt_consumer.compact_auxiliary` | source→calibration→optimizer→proof→published bundle generation 일치. 이 section의 독립 status/owner/closure test를 검증 |
| 8 | `daily_threshold_cycle_report` → EV/runtime-approval summary → control tower/checklist → strict handoff | 마지막 compact generation과 선정/보존/미확정 사유가 전파되었는지 확인. 파일 존재나 전체 DONE만으로 수용하지 않음 |
| 9 | 기존 PREOPEN·`entry_setup_live_policy` → `mechanistic_entry_runtime_policy.load_effective` 및 runtime verify → 실제 Main runtime | source/effective day·bundle/prompt/contract hash·release/consumer receipt. 실제 호출 연결은 `entry_setup_live_policy.py`의 effective-policy 선택/검증 경로로 확인. PREOPEN 동결 이후 같은 날짜 bundle을 덮어쓰지 않음 |
| 10 | 자연 판단/주문/COMPLETED 원장 → 다음 calibration | 실제 applied version/owner/route로 귀속. 자연 비용 후 EV/순익을 CF ΔEV와 분리하여 rolling/cumulative 및 rollback 판정에 전달 |

새 pipeline을 만들지 않고 위 모듈의 기존 section·manifest·helper를 확장한다. `src/engine` root 신규 Python module, 별도 policy publisher/consumer, 별도 cron/collector/DB는 필요하지 않다. legacy R0/R3/BUY-WAIT 연구 결과는 compact 후보 승격 근거가 아니며 retired one-share/lifecycle 경로도 복원하지 않는다.

### 5.1 실행 순서와 끊김 방지

현재 native wrapper는 calibration → optimizer → consumer 뒤 Daily를 생성한다. 별도 follower는 batch → calibration/policy publication → optimizer selection 보존 → metadata rebind → holding 단계 → consumer까지 수행하지만 **그 후 Daily/EV/strict handoff 갱신 호출은 없다.** 따라서 follower의 최종 generation이 앞서 생성된 summary에 반영되는지 추가 연결해야 한다.

우선 기존 native/follower의 실제 설치 경로·선행 조건을 확인하고 다음 DAG로 정리한다. 새 cron 설치/정지 cron 복원 없이 기존 허용 실행 경로만 수정한다.

`source-ready → candidate-plan(G) → bounded execution(G) → paired evaluation(G) → final calibration(G) → next-date policy → optimizer metadata/consumer → affected Daily/EV/runtime summaries → tower/checklist/strict handoff`

후행 작업이 전체 postclose DONE을 기다리면서 native가 그 후행 완료를 기다리는 순환이 없어야 한다. 선행 준비 artifact의 exact-date readiness/권한 범위를 확인한다. initial optimizer plan을 만들기 위한 자연 calibration과 candidate 결과를 반영한 final calibration을 generation으로 구분한다. final optimizer는 당일 후보 선택을 보존한다. 결과로 다시 당일 후보를 바꾸는 반복 루프를 금지한다.

비동기 follower가 남으면 native 보고서는 `candidate_execution_deferred`이며 compact 경제성 family의 완료를 주장하지 않는다. follower terminal 이후 기존 scope-limited finalization 경로에서 **영향받은 summary만 한 번** 갱신하고 strict handoff를 재검증한다. holding/legacy/R0R3의 별도 block이 compact handoff를 어떤 이유로 막는지 명시한다. 직접 의존하지 않는 연구 단계는 compact 완료의 필수조건에서 분리하되 각 family의 실패 상태는 보존한다.

기존 consumer/report의 전체 schema를 깨지 않도록 compact section에 scope별 terminality를 추가하고 기존 strict verifier도 함께 갱신한다. 부분 성공을 전체 연결 성공으로 표시하지 않는다. wrapper/자동화 변경은 해당 운영 문서·오늘 owner와 같은 구현 change set에서 정합화한다. 이 계획에서 wrapper나 운영 baseline을 수정하지 않는다.

### 5.2 상태·재개·원자적 발행 계약

공통 section에 `source_date`, `generation_id`, `incumbent/candidate_prompt_version`, source/result/calibration/policy/contract hash, `status`, `reason`, `next_owner`, `closure_test`를 둔다. terminal 결과를 원자적으로 기록한 뒤 완료 marker를 기록한다.

| 상태 | 경제성/후행 처리 |
| --- | --- |
| `valid_empty` | 실제 심사 대상 없음. 준비/실행 failure와 구분하고 기존 policy carry 규칙으로 후행 진행 |
| `prepared` / `execution_deferred` | 요청 준비만 완료. provider/result 미완료와 next owner 기록. 신규 후보 발행 금지 |
| `source_contract_blocked` / `execution_failed` | 최초 탈락 위치·재개 key·유효 checkpoint 보존. 기존 dated policy의 사용 가능성은 별도 검증 |
| `insufficient_mature_sample` | 원천 유효·실제 필요한 horizon/표본만 부족한 경우. 구조 결손을 이 상태로 숨기지 않음 |
| `comparison_complete_rejected` / `incumbent_preserved` | 유효 음수/무개선 또는 자기 보존. result hash와 carry reason 소비, 성공 후보로 집계하지 않음 |
| `candidate_selected` / `policy_carried` | proof 또는 보존 사유와 미래 날짜 bundle hash를 연결. 실제 PID/자연 성과는 별도 상태 |

보존 policy도 정확한 날짜·source age·hash·기존 승인 expiry/rollback을 통과해야 한다. old policy를 오늘의 신규 후보로 재표기하지 않는다. 발행 실패는 `require-policy-publication` 경로에서 성공 exit로 숨기지 않는다. PREOPEN 동결/기존 bootstrap 경계는 유지한다. policy root 부재를 묵시적인 bootstrap 권한으로 바꾸지 않는다.

## 6. 시간으로 해결될 항목과 구조 수리 대상

| 분류 | 확인 및 다음 조치 |
| --- | --- |
| 유효 quote/plan/cost가 있고 지정 horizon만 미도달 | outcome as-of/required horizon으로 maturity를 계산하고 기존 후행 label update를 기다림 |
| current version의 유효 독립 날짜/episode 부족 | 자연 적격 유입을 누적. 적격 유입률이 없으면 ETA null; actual fill을 CF 평가의 새 전제조건으로 추가하지 않음 |
| 준비10·실행0, compact 대신 legacy 역할 | 실행 route/schema·budget scope와 완료 receipt 수리. 표본 증가로 해결되지 않음 |
| pre-veto 가격/손절/수량·당일 비용/route·frozen 입력 계보 부재 | 해당 producer/owner projection 수리. 과거 불복구 원천은 exclusion/audit로 남기며 현재 master나0으로 대체하지 않음 |
| 비교 완료 후 summary/정책/loader 미소비 | 마지막 consumer hash와 순서/strict 계약 수리. DONE/배포 receipt로 대체하지 않음 |
| retired legacy lifecycle 0·연구용 R0/R3 block | 현행 compact의 직접 의존 여부만 검증. retired 경로 복원이나 unrelated 전체 재실행 없음 |

## 7. 최소 구현 순서·검증·완료 기준

| 패키지 | 범위 | 종료 확인 |
| --- | --- | --- |
| CP0 원천/계약 | 실제 producer·선정일/역할/route 대사, current compact holdout/승격 계약 확정 | 호출 census와 economic exclusions 보존, 직접 원천 gap 및 owner 확정 |
| CP1 준비→실행 | 기존 batch/quality에 compact 분기·checkpoint·budget binding | 기존/후보 동일 input, legacy 격리, 유효 응답 재실행0·누락만 재개 |
| CP2 paired 경제성 | 기존 비용/exit/capital replay·공통 분모·holdout 연결 | self/동일 verdict/미확정/partial/capital 충돌·손실 사례가 올바른 net으로 평가됨 |
| CP3 선정→발행→consumer | calibration/optimizer/modern publisher/consumer 동시 계약 보완 | proof 누락·다른 cohort/hash·consumed holdout은 발행 차단, carry/next-date freeze 정상 |
| CP4 마지막 handoff | 기존 wrapper/follower 순서와 scope-limited finalization·verifier | final generation이 Daily/EV/approval/tower/checklist/strict에 동일하게 반영, 실패 상태 유실0 |
| CP5 자연 수용 | 구현 승인 후 필요한 범위의 release/PREOPEN/실제 consumer·자연 원장 확인 | source 검증, selected release, PID 소비, 자연 적용, actual 비용 후 성과를 각각 보고 |

각 패키지는 implementation → self review → 보완 → re-review → targeted validation으로 닫는다. 기존 `src/tests/test_ai_decision_quality.py`, `test_entry_setup_paired_replay_batch.py`, `test_ai_action_outcome_calibration.py`, `test_main_ai_prompt_optimizer.py`, `test_main_ai_prompt_consumer.py`, `test_mechanistic_entry_runtime_policy.py`, `test_postclose_summary_handoff.py`, `test_verify_threshold_cycle_postclose_chain.py` 중 영향을 받는 계약을 보강한다. 새 유사 테스트/모듈을 남발하지 않는다.

필수 integration fixture는 기존 public orchestration을 통과한다. 같은 verdict Δ0, VETO→실행 이익/손실, PASS→미진입 회피 손실/기회 손실, CAUTION routing, no-call, null cost/stop/notional, partial/open, current-version contamination, payload/result/hash mismatch, budget exhaustion/checkpoint retry, holdout reuse, stale summary, carry·PREOPEN freeze를 검증한다. fixture의 양수 ΔEV는 **연결 검증**이며 실제 정책 개선 실적이 아니다.

구조 closure는 준비→응답→net 비교→선정/보존→미래 bundle→마지막 summary/strict까지 같은 generation의 terminal receipt를 확보하는 것이다. 경제성 closure는 실제 유효 모집단에서 나온 ΔEV·일별 순익·holdout 판정이고, 양수 후보가 없으면 유효 비교 후 보존이 올바른 결과다. 자연 actual closure는 적용 버전의 비용 정산 원장으로 별도 확인한다.

## 8. 실행 비용과 이번 문서 검증

긴 JSONL을 여러 consumer가 반복 읽지 않도록 기존 producer projection·receipt를 한 번 생성해 재사용한다. 64MiB 이상/증가 중 JSONL은 bounded manifest/streaming 계약을 따르며 전체 로드를 피한다. provider 병렬수·예산·재시도·resource guard는 기존 상한을 유지한다. 후보 수와 추가 horizon/보조 진단 깊이를 줄일 수 있으나 경제성 공통 분모·불리한 행·holdout·비용/exit 계약을 삭제하여 속도를 얻지 않는다. 구조 연결과 유효 net 결과가 먼저이며 별도 성능 framework/guard는 추가하지 않는다.

이번 계획 변경은 링크·owner/권한·연결 순서 self review/fix/re-review, `git diff --check`, print-only backlog parser로 검증한다. Python/runtime 변경이 없으므로 trading/provider 테스트·재생성·실행·외부 sync는 수행하지 않는다. 실제 설치 follower와 자연 consumer의 최신 receipt 확인 및 holdout numeric 계약 확정은 CP0/CP4 구현 착수 시점의 필수 입력으로 남는다.


## 9. 승인된 구현 closure

사용자 후속 지시로 구현·반복 review/보완·commit/push·배포 및 제한 장후 재생성을 실행한다. 계획 작성 단계의 미실행 설명은 그 단계의 이력이다. 기존 batch에 compact 분기를 추가하고 offline projection/evaluator의 소유 경계는 `src/engine/scalping/compact_auxiliary_paired_replay.py`로 둔다. 새 engine-root module/CLI/cron/collector/publisher는 추가하지 않는다. 실제 유효 비용/plan/terminal이 있는 경우만 후보 요청을 실행하며 physical source gap은 추정으로 채우지 않는다. 적용 가능한 dated carry와 양수 경제성 승격을 구분한다.

실제 source-2026-09-17 → publication-2026-09-18 → effective-2026-09-21 successor와 최종 parent/summary/checklist/정책 연결, 검증 및 배포 상태는 [구현 review](../audit-reports/2026-09-18-compact-auxiliary-paired-economic-implementation-review.md)를 따른다. 원래 9/17 native 실패를 whole DONE으로 바꾸지 않는다. Reviewed provider pricing/원화 inference 비용 차이, owner plan/cost/독립 holdout이 없는 행은 신규 승격 근거가 아니다.

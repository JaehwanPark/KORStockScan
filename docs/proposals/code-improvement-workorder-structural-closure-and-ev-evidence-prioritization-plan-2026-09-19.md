# Code improvement workorder 구조결손 종결·EV 증거 우선순위 개선계획

작성일: 2026-09-19 KST

상태: 구현·제한 재생성·수동 intake 검증 완료. `ee9fcb8db`에서 공통 Daily/EV/generic PREOPEN selector가 퇴역했으므로 해당 경로를 복구하지 않는다. `build_code_improvement_workorder`는 사용자의 명시적 구현 지시 때만 실행되는 source-only intake로 유지하며, family-native 경제 증거와 구조결손을 같은 generation에 결속한다.

## 0. 최신 구조 rebase 결정

- 원 계획의 `threshold_cycle_ev_report` producer와 wrapper 자동 workorder 단계는 폐기 상태를 보존한다.
- workorder의 유일한 후행 소비자는 수동 검토용 `postclose_recommendation_intake`다. runtime summary/bootstrap은 family-native receipt만 소비한다.
- scanner lookup-attention 경제 결과는 `intraday_ws_freshness_monitor`의 native section을 투영한다. workorder가 EV를 재계산하지 않는다.
- 다음 장전 정책은 기존 scanner publisher가 발행한 `hold_no_edge/incumbent_preserved` receipt를 `runtime_policy_bootstrap`이 소비한다. workorder는 정책 후보를 만들지 않는다.
- 따라서 W5의 공통 EV→workorder→runtime chain은 구현 대상에서 제외하고, direct family producer→publisher→bootstrap 경로를 현재 owner로 확정한다.

## 1. 목표와 완료 기준

이 작업의 목적은 workorder 자체를 새 백테스트 엔진으로 만드는 것이 아니다. **EV를 측정할 수 없게 만드는 구조결손을 가장 먼저 구현 대상으로 올리고, 이미 측정된 edge/no-edge/null의 의미를 훼손하지 않은 채 기존 owner와 다음 장전 consumer까지 연결하는 것**이 목적이다.

우선순위는 다음과 같다.

1. source producer·terminal·비용·수량·정책 version·consumer generation의 구조결손을 닫는다.
2. 동일 기회·동일 자본·비용 후 paired EV와 일별 순익 차이를 기존 evaluator에서 받아 유의미한 경제 결과를 만든다.
3. 검증된 양수 후보는 기존 family publisher/PREOPEN/runtime consumer에 인계하고, no-edge·위험 악화는 incumbent 보존으로 종결한다.
4. 자연 표본 성숙과 성능 최적화는 그 이후다.

완료는 아래 다섯 상태를 별도로 충족해야 한다.

| 상태 | 완료 기준 |
| --- | --- |
| Source closure | 모든 선택 order가 exact native ID, source date/hash, 최초 결손 owner, 복구 가능성, closure test를 가진다. |
| Generation closure | final workorder의 semantic source digest가 마지막 producer 이후 변하지 않으며 모든 후행 consumer가 같은 generation ID를 확인한다. |
| Economic measurement | 비교 가능한 family는 baseline/candidate 비용 후 EV, paired delta, 일별 순익 delta, tail/capital을 표시한다. 자료가 없으면 정확한 null reason을 표시한다. |
| Policy handoff | positive-ready/no-edge/source-gap 각각이 기존 publisher에서 candidate/incumbent carry/apply-blocked 중 하나로 닫힌다. workorder는 정책 권한을 갖지 않는다. |
| Natural acceptance | 정규 PREOPEN·실제 PID 소비·자연 주문/체결·post-apply 비용 후 결과는 별도 기존 owner가 확인한다. 코드와 fixture 완료로 대체하지 않는다. |

양수 EV는 보장하지 않는다. 검증된 음수 또는 no-edge도 유의미한 결과다. `null`만 남았는데 producer repair나 미래 실험 owner가 없으면 구조결손 미종결이다.

## 2. 현재 확인된 상태

현재 exact-date 산출물은 [workorder JSON](../../data/report/code_improvement_workorder/code_improvement_workorder_2026-09-17.json), [workorder Markdown](../code-improvement-workorders/code_improvement_workorder_2026-09-17.md), [WS family report](../../data/report/intraday_ws_freshness_monitor/intraday_ws_freshness_monitor_2026-09-17.json)이다.

| 항목 | 현재 값·판정 |
| --- | --- |
| final generation | `2026-09-17-37f1a42d3b7c`, source/semantic hash `315464ab68fa2659d64a8a05c390cffc5342df025ca44ad865ff245823945906`; generation input에 `direct_family_only=true` 결속 |
| generation 계약 | `manual_final_direct_family`, consumer는 `postclose_recommendation_intake` 1개, contract issue 0 |
| 현재 inventory | source order23, selected12, non-selected11, implement_now0, attach_existing_family14, defer_evidence9 |
| 권한 | 전체23건 `runtime_effect=false`, `allowed_runtime_apply=false` |
| root cause | open6은 구현 누락이 아니라 기존 owner의 자연 영수증/표본 대기이며 `implementation_required_count=0` |
| 전체 경제 평가 | scanner lookup-attention family 1개를 native evaluator에서 투영. validated improvement0, measured no-edge1 |
| WS opportunity | resolved pair3/3일, 비용 후 `-2.38954987%`, 일별 delta 모두 음수, `hold_no_edge` |
| WS primary actual comparison | baseline/candidate EV·paired delta·원화 일별 순익 null. 과거 unselected recipe/quantity/guard가 없음 |
| submit drought | 과거 superseded terminal51건은 복구 불가. 현행 `call_local_submit_attempt_v1` 종료 receipt 구현을 확인해 P3 natural maturity로 종결 |
| unknown/WS repair order | unknown warning은 `tuning_input_allowed=true`라 P4 evidence로 유지. WS REMOVE→REG/cooldown receipt는 구현 완료·자연 PID 영수증 대기 |

수동 intake는 issue0·conservation PASS·implementation request0이다. 다른 recommendation family 4개가 과거 source-day에 없어 intake 전체 상태는 `waiting_sources`지만, workorder generation/authority 계약 결손은 아니다. Workorder는 runtime policy owner가 아니므로 이 상태를 PREOPEN·PID·자연 경제성 완료로 해석하지 않는다.

## 3. 보존할 계약과 변경 금지 범위

- clean tuning 시작 `2026-06-05T00:00:00+09:00`, main-only/normal-only/post-fallback-deprecation을 유지한다.
- 비용 후 PnL은 `COMPLETED + valid profit_rate`와 검증된 비용만 사용한다. missing·HELD·partial realization·custody-censored를0으로 바꾸지 않는다.
- full/partial fill, real/sim/probe/counterfactual, owner, venue/session, policy/version을 분리한다.
- `BLOCK/RECHECK/REJECT`와 AI `VETO` 기회비용은 실제 체결 timing과 합치지 않는다.
- `max_orders=12` 운영 상한과 selected/non-selected 전체 inventory 보존을 유지한다. 상한을 늘려 결손을 가리지 않는다.
- workorder는 repo/runtime 자동 수정, 정책 발행, 주문, provider·threshold·수량·cap·hard guard 변경 권한을 갖지 않는다.
- 새 root module·DB·service·ledger·report family·범용 optimizer를 만들지 않는다. 기존 `build_code_improvement_workorder.py`, economic owner, wrapper, summary, verifier를 보완한다.
- historical missing recipe·수량·guard·terminal을1주, gross return, 미래 체결 또는 임의 모델로 합성하지 않는다.

## 4. 목표 producer→consumer 구조

최신 퇴역 이후 소유 경계는 다음과 같다.

| 역할 | 현행 owner와 구현 범위 |
| --- | --- |
| 수동 workorder intake·분류·직렬화 | `build_code_improvement_workorder.py`: direct-family mode, resolution projection, deterministic P0–P4 ranking |
| 경제 증거 | 각 family evaluator. 이번 구현은 `intraday_ws_freshness_monitor`의 scanner lookup-attention section을 그대로 투영 |
| workorder 검증·수동 대사 | `postclose_workorder_contract.py`와 `postclose_recommendation_intake.py` |
| 장후 자동 chain | family producer→`runtime_approval_summary`→direct verifier. workorder는 기본 OFF이며 자동 chain 입력이 아님 |
| 장전 정책 | family publisher→`runtime_policy_bootstrap`→기존 장중 consumer |
| 자연 경제성 | 실제 PID·decision·submit/fill·COMPLETED 비용 후 결과를 기존 family acceptance owner가 판정 |

```text
family-native source/evaluator
        ├─ measured edge/no-edge/source-gap
        │        └─ family publisher → runtime bootstrap → intraday consumer
        └─ explicit user-requested workorder
                 ├─ structural resolution/closure owner
                 ├─ native economic evidence projection
                 └─ postclose recommendation intake (source-only)
```

workorder generation과 runtime policy generation은 분리한다. Workorder PASS가 policy selection, PID consumption 또는 경제 개선을 의미하지 않는다.

## 5. W0 — 현재 generation과 최초 결손 동결

1. 선택 release, wrapper, current workorder, WS/source-quality/buy-funnel, direct runtime summary/verifier의 date·size·hash를 bounded inspection한다.
2. 64MiB 초과 또는 growing source는 summary/manifest projection만 사용한다.
3. 기존 native order의 selected/non-selected, decision, contract digest와 root-cause status를 lineage로 보존한다.
4. 공통 Daily/EV/workorder 자동 wrapper 단계가 0개인지 확인하고, 퇴역 owner가 수동 order의 수정 파일·테스트·후행 소비자로 남지 않게 한다.
5. workorder 부재는 자동 chain failure가 아니다. 사용자가 실행을 지시한 경우에만 manual final generation을 생성하고 intake contract로 검증한다.

Closure: direct-family source와 수동 workorder의 경계가 재현되며 퇴역 owner를 복구하지 않는다.

## 6. W1 — source fingerprint와 manual generation 계약

공통 `threshold_cycle_ev`가 제거되어 workorder 자기참조도 제거됐다. `--direct-family-only`는 historical source date를 재평가할 때에도 퇴역 Daily/EV 입력과 그 전용 order를 배제한다.

Workorder는 다음을 기록한다.

- `generation_phase=manual_final_direct_family`
- 모든 exact source file의 byte fingerprint와 `source_hash`
- `semantic_source_hash`: 현재 direct input set의 exact hash. family 경제 section은 별도 `semantic_sha256`으로 결속
- `consumer_generation_required=['postclose_recommendation_intake']`
- selected/non-selected 전체 inventory와 이전 generation lineage

Family 경제 projection은 renderer timestamp·workorder echo를 포함하지 않는다. Scanner section의 경제 값·source gap·policy publication만 canonical JSON으로 hash한다. 경제 section 변경은 hash를 바꾸고 Markdown 표현 변경은 family 경제 hash를 바꾸지 않는다.

Closure tests:

- 퇴역 EV artifact 유무가 direct-family generation에 영향을 주지 않음
- WS 경제 metric/source gap/policy hash 변경 시 family semantic hash 변경
- 같은 native 경제 input은 같은 family semantic hash 생성
- source read 중 파일 변경은 publication 전에 fail
- JSON render 실패는 이전 JSON/Markdown을 보존

## 7. W2 — 구조결손과 시간 성숙의 명시적 분리

각 order에 기존 필드를 재사용해 다음 projection을 추가한다. 범용 상태 framework를 새로 만들지 않고 workorder serialization과 consumer validation에 필요한 최소 contract로 제한한다.

| 필드 | 허용 값·의미 |
| --- | --- |
| `resolution_mode` | `producer_repair`, `consumer_rebind`, `natural_maturity`, `historical_unrecoverable`, `measured_no_edge`, `retired_or_not_applicable` |
| `economic_eligibility` | `eligible`, `pending_maturity`, `blocked_structural`, `not_applicable` |
| `first_blocker` | 최초 producer/consumer 결손 하나. broad blocker 목록으로 우선순위를 부풀리지 않음 |
| `closure_owner` | existing producer/evaluator/publisher/acceptance owner |
| `closure_test` | exact artifact·field·count/hash와 통과 조건 |
| `eta` | 근거 있는 일정만 기록하고 아니면 null |

상태 판정 원칙:

- 자연 row가 추가되면 닫힐 수 있고 producer·consumer가 이미 구현된 경우만 `natural_maturity`다.
- producer/reader가 없거나 source가 mandatory 필드를 만들지 않는 경우 `producer_repair` 또는 `consumer_rebind`다.
- 과거 unselected arm의 recipe/quantity/guard처럼 되살릴 수 없는 값은 `historical_unrecoverable`이며 미래 prospective 실험 owner를 별도로 가리킨다.
- 검증된 음수 EV는 `measured_no_edge`다. 표본 부족이나 source gap으로 되돌리지 않는다.
- `implementation_done`은 code closure일 뿐 `root_cause_closed`가 아니다. 자연 evidence/economic acceptance를 별도 상태로 둔다.

현재 order에 대한 예상 재판정:

| order/family | 예상 상태 | 필요한 실제 closure |
| --- | --- | --- |
| `entry_submit_drought_auto_resolution` | `producer_repair`, P0 | 정상 submit path의 단일 실행 가능한 가설을 검증하고 AI-confirmed→budget/latency→submitted 또는 exact final block conservation을 복구. 양수 EV는 code closure 조건이 아님 |
| unknown-token provenance | EV eligibility에 영향을 주는 field만 `producer_repair`; reviewed unavailable은 not-applicable | exact producer context 또는 reviewed unavailable. unknown 문자열을 다른 unknown label로 치환하지 않음 |
| WS stale observability | 구현된 부분은 natural maturity, 과거 actual arm은 historical unrecoverable | future pair ID·사전 배정 arm·recipe/quantity/guard·terminal 자연 생성 |
| WS opportunity selection | `measured_no_edge` | 현재 `-2.38954987%`와 세 날짜 음수 delta를 incumbent 보존으로 인계. implement_now 계측 order로 중복 승격하지 않음 |
| entry receipt/fill/post-submit/Telegram | code implemented, natural evidence pending | 다음 실제 submit/fill에서 exact lineage와 비용 결과 확인 |

## 8. W3 — EV evidence projection과 우선순위

workorder는 EV를 다시 계산하지 않는다. 각 기존 evaluator가 검증한 결과만 아래 `economic_evidence` projection으로 복사하고 source artifact/hash를 결속한다.

- `comparison_status`: `validated_edge`, `measured_no_edge`, `identical_policy`, `pending_maturity`, `source_gap`, `not_applicable`
- `metric_role`: `realized`, `sim_probe_ev`, `supporting_proxy`, `diagnostic_only`
- baseline/candidate 비용 후 EV와 paired delta
- baseline/candidate 날짜별 순익과 평균 일별 delta
- paired sample·source day·holdout day
- costs, capital/exposure, downside/tail/stress/model-error 상태
- source quality, holdout, policy-difference, self-comparison 여부
- exact evidence artifact와 semantic SHA
- null reason과 next evidence owner

값이 없는 필드는 null을 보존한다. `expected_ev_effect` 설명문을 수치처럼 정렬하지 않는다. gross·win rate·관심도 proxy를 primary EV로 승격하지 않는다.

선택 순서는 기존 max12 안에서 다음 lexicographic contract를 사용한다.

1. **P0 EV-measurement structural blocker:** 실제 정상 경로에서 비용 후 비교를 불가능하게 만드는 producer/terminal/cost/consumer 결손이며 closure가 실행 가능함.
2. **P1 validated economic action:** paired EV·일별 순익·위험 gate가 검증된 edge 또는 no-edge. Edge는 기존 publisher로, no-edge는 incumbent 보존으로 보낸다.
3. **P2 measurement integrity:** source provenance·identity·dedup처럼 EV 분모의 정확성을 직접 바꾸는 보완.
4. **P3 natural maturity/visibility:** 구현이 끝났고 새 자연 표본만 필요한 항목. 선택 슬롯을 반복 점유하지 않고 existing-family inventory에서 추적한다.
5. **P4 defer/not-applicable:** exact first owner가 없거나 retired/unsupported인 진단.

동일 priority에서는 source severity, comparison eligibility, expected measurable population, source date, native order ID 순으로 결정론 정렬한다. 예상 양수 크기를 임의 추정해 정렬하지 않는다. source gap이 많은 항목이 단순 개수 때문에 P0가 되지 않도록 first blocker와 closure actionability를 요구한다.

Closure tests:

- 동일 정책은 improvement가 아니라 `identical_policy/incumbent_preserved`
- 음수 paired EV는 `measured_no_edge`로 보존되고 implement_now에서 제외
- 비용/holdout/일별 순익이 없는 양수 proxy는 validated edge가 아님
- source gap order가 valid economic candidate를 max12 밖으로 밀어내지 않음
- 모든 non-selected order도 inventory·reason·owner를 유지

## 9. W4 — submit drought 단일 구조 수리

현재 P0는 `SUBMIT_DROUGHT_CRITICAL`이다. 새 병목 taxonomy를 늘리지 않고 정상 submit path 가설 하나로 좁힌다.

1. 동일 evaluation/attempt identity에서 AI-confirmed, budget, latency, final guard, submit intent, broker dispatch/receipt의 conservation을 확인한다.
2. 현재 `budget_pass=8`, `latency_pass=4`, submitted0이므로 최초 누락 stage 하나를 producer/reader 증거로 확정한다.
3. 실제 final guard 또는 broker 결과가 존재하면 reader/join을 수리한다. producer가 사건을 남기지 않았다면 미래 capture를 수리하고 과거는 unrecoverable로 둔다.
4. 주문 guard·provider·threshold·수량·cap·cooldown을 완화하지 않는다. 제출을 만들기 위해 정책을 바꾸지 않는다.
5. closure는 자연 정상 path에서 `submitted` 또는 exact terminal block/reject가 동일 identity로 관측되는 것이다. EV는 이후 completed cost outcome owner가 평가한다.

이 order가 장기간 반복됐다는 사실만으로 우선순위를 계속 올리지 않는다. 새 source/closure 변화가 없으면 같은 P0 instruction을 재렌더링하고 신규 구현 주문으로 중복 생성하지 않는다.

구현 결과: 현행 submit 함수는 `observe_submit_attempt`와 `entry_submit_attempt_finished`로 모든 call-local invocation을 종료한다. 9/17 artifact의 unclassified51건은 이 계약 이전의 `new_evaluation_without_previous_terminal`이며 missing identity0·stage-order violation0이라 소급 수리 대상이 아니다. Workorder는 이를 `implemented_source_quality_contract_waiting_sample`/P3로 분류하고, 새 call-local 자연 receipt가 submitted 또는 정확한 terminal block/reject로 닫히는지를 closure test로 남긴다. 진짜 identity/order/unknown-latency 결손은 계속 P0로 유지된다.

## 10. W5 — 현행 direct-family 소비 경계

공통 EV→workorder→runtime suffix는 퇴역했으므로 복구하지 않는다. 현행 순서는 다음과 같다.

1. WS final, source-quality final, compact/machine finalize와 mandatory family producer 완료
2. family-native evaluator와 dated publisher가 edge/no-edge/source-gap을 확정
3. `runtime_approval_summary`와 direct verifier가 family receipt를 검증
4. `runtime_policy_bootstrap`이 승인된 incumbent·operator lock·명시 OFF만 다음 장전 env/manifest로 합성
5. 사용자가 workorder 구현을 명시적으로 지시한 경우에만 `build_code_improvement_workorder --direct-family-only` 실행
6. workorder는 `postclose_recommendation_intake`에서 native ID·authority·resolution·economic evidence hash를 수동 대사

partial family refresh는 해당 family publisher와 direct summary/verifier만 갱신한다. workorder 자동 재실행이나 runtime mutation을 유발하지 않는다. Workorder source가 이후 바뀌면 다음 수동 intake에서 full source fingerprint 차이로 stale을 검출한다.

Closure:

- wrapper에 workorder 또는 공통 Daily/EV 단계가 없다.
- direct-family workorder의 `required_downstream`·수정 파일·테스트에 퇴역 owner가 없다.
- scanner no-edge policy hash는 family publication과 동일하며 bootstrap 입력은 workorder가 아니라 family policy receipt다.
- 실제 PID와 자연 경제 결과는 별도 acceptance로 남는다.

## 11. W6 — 기존 정책 owner와 다음 장전 인계

workorder decision과 runtime policy decision을 분리한다.

| 경제 결과 | workorder | 기존 publisher/PREOPEN |
| --- | --- | --- |
| validated edge | 기존 family의 bounded candidate handoff | 기존 promotion gate·독립 holdout·정확한 target-date policy가 통과한 경우만 발행 |
| measured no-edge/위험 악화 | 구현 order를 만들지 않고 측정 결과 보존 | incumbent/baseline 유지 |
| pending maturity | existing-family tracking | 기존 정책 유지, 새 표본만 수집 |
| structural source gap | P0/P2 repair order | apply 차단 또는 유효 incumbent carry |
| historical unrecoverable | 과거 repair 종료, future experiment owner 인계 | 역사 값을 합성하지 않음 |

현재 WS 결과는 `measured_no_edge`이므로 baseline 유지가 올바른 정책 결과다. Primary actual paired EV는 미래 사전 배정 arm이 자연 생성될 때만 측정한다. Opportunity EV가 양수로 바뀌더라도 actual arm·cost·holdout 계약 없이 live-ready로 승격하지 않는다.

정규 다음 PREOPEN, selected release, 실제 PID 소비, 자연 order/terminal, 비용 후 post-apply 성과는 기존 `KiwoomCommonHealthOpportunityCostAcceptance0917` owner에서 확인한다. workorder generation PASS는 자연 적용이나 이익 개선 증거가 아니다.

## 12. 제한 재생성과 현재 날짜 기대 결과

코드 리뷰·수정·대상 테스트가 끝난 뒤에만 current source-day의 bounded handoff suffix를 재생성한다. provider 호출, raw 전수 재스캔, 주문, 봇 재기동, 조기 PREOPEN은 수행하지 않는다.

제한 재생성 결과는 다음과 같다.

- WS opportunity order는 `-2.38954987% / hold_no_edge / incumbent_preserved`로 재분류된다.
- actual scanner paired EV와 원화 일별 순익은 미래 arm 전까지 null이며 `historical_unrecoverable + prospective owner`가 붙는다.
- submit drought의 현행 종료 capture는 구현 완료이고 과거51건은 소급 불가라 P3 자연 receipt 대기로 닫혔다.
- unknown provenance는 audit가 tuning input을 허용하므로 P4 reviewed evidence이며 implement_now에서 제외됐다.
- WS stale repair observability는 기존 REMOVE→REG/cooldown receipt 구현을 재사용하며 P3 자연 PID receipt 대기다.
- source order23개 중 implement_now0, attach14, defer9이며 선택12개는 모두 existing-family다.
- paired comparable0·actual profit improvement null이면 경제성은 종결하지 않는다. no-edge 측정 부분만 경제 결과로 인정한다.

## 13. 구현·리뷰·검증 순서

| 단계 | 주요 변경 | 필수 검증 |
| --- | --- | --- |
| T0 baseline | current generation/source/consumer receipt 동결 | bounded artifact inspection, no writes |
| T1 source/economic digest | existing workorder와 intake contract에 direct-family projection | retired input exclusion·economic mutation·source-race tests |
| T2 status/evidence | existing serialization/classification에 resolution/economic projection | null/zero, no-edge, identical, source-gap, maturity tests |
| T3 ranking | max12 안의 P0–P4 deterministic ordering | source-gap flood, edge/no-edge, non-selected inventory regression |
| T4 chain | automatic wrapper OFF와 family publisher→bootstrap 경계 검사 | wrapper, runtime summary/verifier/bootstrap tests |
| T5 review | producer/consumer·silent stale·authority leak 재리뷰 후 수정 | relevant pytest, compileall, wrapper `bash -n`, `git diff --check` |
| T6 bounded regeneration | 승인된 current source의 handoff suffix만 재생성 | final generation/hash 일치, provider0/raw full rescan0/order0 |
| T7 release/natural | immutable release와 정규 schedule 소비 확인 | source tests, selected release, route/PID를 분리; 자연 EV는 후속 acceptance |

기존 테스트 family를 확장하고 큰 fixture·새 benchmark·성능 guard를 만들지 않는다. 대형 report를 테스트 fixture로 복제하지 않고 최소 semantic projection을 사용한다. 성능 문제는 source semantic hash와 bounded suffix 재생성으로 필요한 만큼만 줄인다.

## 14. 작업 소유와 문서 인계

- 구조·consumer 구현은 [현재 checklist](../checklists/2026-09-21-stage2-todo-checklist.md)의 기존 `CodeImprovementWorkorderReview0918`에 연결한다. 새 중복 OPEN ID를 만들지 않는다.
- submit drought는 해당 기존 entry owner의 단일 정상-path closure로 연결한다.
- WS prospective pair와 자연 EV는 기존 `KiwoomCommonHealthOpportunityCostAcceptance0917`가 계속 소유한다.
- source-quality unknown provenance는 기존 observation source-quality owner에 연결한다.
- 구현으로 wrapper/automation 규칙이 바뀌면 owning 운영 문서와 당일 checklist를 같은 change set에서 갱신한다.
- README, Plan Rebase, prompt, AGENTS는 별도 명시 요청 없이 수정하지 않는다.

## 15. 계획 종결 정의

계획 구현은 다음 조건을 모두 만족해야 종결한다.

1. workorder final source hash가 자기참조 없이 upstream 경제 의미를 식별한다.
2. late source writer가 silent stale을 만들지 못하며 affected suffix가 같은 generation으로 재결속된다.
3. 구조결손·자연 성숙·과거 복구 불가·측정 no-edge가 분리된다.
4. 정량 EV·일별 순익·risk evidence가 있는 order만 경제 action으로 분류된다.
5. submit drought에 실제 실행 가능한 단일 closure가 있고 반복 진단만 재생성하지 않는다.
6. 수동 intake가 workorder generation/hash를 검증하고 runtime summary/bootstrap은 family-native receipt만 소비한다.
7. 다음 장전에는 기존 publisher가 발행한 candidate 또는 검증된 incumbent 보존 정책이 있으며 runtime이 기존 guard 아래 자동 소비할 수 있다.
8. actual paired EV가 null이면 경제성 완료를 주장하지 않고 future arm owner와 closure test를 남긴다.

최종 목적은 workorder의 개수나 PASS를 늘리는 것이 아니라 **EV 측정을 막는 최초 구조결손을 줄이고, 검증된 edge/no-edge를 다음 정책 판단에 손실 없이 전달하는 것**이다.

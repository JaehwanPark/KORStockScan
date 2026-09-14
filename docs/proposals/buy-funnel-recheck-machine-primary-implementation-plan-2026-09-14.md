# #119 BUY funnel → #23 recheck 기계 주판정 전환 상세 구현안

작성일: 2026-09-14 KST. 상태: **구현·코드 검토 완료, 선택 release/PID 자연 검증 및 경제성 수용 대기**.

초기 상세 설계 뒤 명시적인 사용자 구현 요청에 따라 §11의 최소 source-only 보완을 적용했다. 이 문서는 여전히 장후 전체 재생성, Provider 호출, PREOPEN 수동 적용 또는 주문 권한을 만들지 않는다.

## 1. 결정과 범위

**#119는 기계 평가부터 broker accepted submit까지 원인을 분리하고, #23은 그중 자신의 기존 실행 계약으로 처리 가능한 원인만 선택한다. 기계의 RECHECK와 기존 1주 recheck policy는 다른 권한이다.**

- 기계 `ENTER_NOW` + 유효 AI `PASS`: 기존 최종 authority·가격·수량·broker guard로 전달한다. PASS 자체가 주문 성공은 아니다.
- 기계 `ENTER_NOW` + 유효 AI `VETO`: 해당 타점 비진입. AI 오류·CAUTION·INSUFFICIENT는 별도 비진입/관찰이며 VETO 또는 PASS로 정규화하지 않는다.
- 기계 `RECHECK/BLOCK`: AI 없이도 유효한 기계 판정이다. 다음 scanner loop 관찰과 현재 타점 차단을 구분한다. AI로 승격하거나 #23 probe로 우회하지 않는다.
- raw AI action/score는 원본 보존용이다. 최종 기계+AI 역할 계약과 충돌하면 score 또는 `WAIT` 문자열로 실제 authority를 역추정하지 않는다.
- scanner 밖 독립 기회 분모는 #8/#9/#49 및 census owner에 남긴다. 기계 평가 원장은 전체 시장 탐색 recall을 대신하지 않는다.
- main 신규 진입만 대상으로 한다. 위젯·에피소드·holding/scale-in·sim·수동 주문을 합산하지 않는다. 별도 scout 경로는 실제 owner/entry route/정책으로 분리한다.

현재 역할 근거는 [전환 설계 §16](entry-prompt-balanced-adjudication-design-review-plan-2026-09-13.md#16-기계-타점-선정ai-passveto-역할-정정), 기존 구현은 [§18~§20](entry-prompt-balanced-adjudication-design-review-plan-2026-09-13.md#18-17-사용자-구현-지시-후-reviewfix-결과)를 따른다. 앞선 no-veto 설계·과거 receipt를 최신 계약으로 사용하지 않는다.

## 2. 현재 구현과 확인된 간극

| Owner/파일 | 현재 확인한 계약 | 이번 설계의 변경점 |
| --- | --- | --- |
| [#119 producer](../../src/engine/buy_funnel_sentinel.py) | report6, lossless cache12; `ai_confirmed/budget_pass/latency_pass/order_bundle_submitted`; exact submit ledger와 call-local parent 존재 | 기계 평가·AI screen의 별도 원장과 exact 연결을 추가. 기존 submit ledger를 기계 평가 수로 덮어쓰지 않음 |
| [공통 drought validator](../../src/engine/automation/submit_drought_contract.py) | report6와 5개 causal axis, scope evidence 재계산 | 새 role/version/cohort·보존식·미관측 상태를 함께 검증 |
| [#23 daily controller](../../src/engine/scalping/entry_recheck_drought_controller.py) / [기존 계산 owner](../../src/engine/scalping/entry_ai_gate_backtest.py) | daily producer가 기존 계산 함수를 재사용; 정확한 최근 3거래일·source binding1·20일 exact attribution | 읽기 전용 진단 route와 기존 policy 후보를 분리하고 role 호환성을 후보 조건에 결속 |
| [recheck policy](../../src/engine/scalping/entry_recheck_policy.py) | controller v4/exact attribution v3/profile v2. AI69~74.999, WAIT probe intent, bounded cap·probe-first 계약 | machine RECHECK/AI screen WAIT를 legacy WAIT-probe로 매핑하지 않음. 기존 수량·cap·floor 변경 없음 |
| [recheck exact attribution](../../src/engine/scalping/entry_ai_gate_backtest.py) / [submit budget](../../src/engine/scalping/entry_recheck_submit_budget.py) | exact direct submit은 요청1주 확인. arm과 durable reservation/accepted budget 분리 | 일반 기계 normal-sizing 제출을 recheck 성공으로 귀속하지 않음. 과거 reservation/custody 보존 |
| [기계 capture](../../src/engine/scalping/ai_decision_trace.py) | `mechanistic_entry_observation_v1`, evaluation attempt·snapshot·promotion·bundle hash 저장 | 기존 archive 재사용; 기계 무호출과 실제 AI response/terminal의 exact bridge 확인 |
| [판정 합성](../../src/engine/scalping/entry_setup_evidence.py) | `entry_mechanistic_action`, `entry_ai_screen_status`, `entry_ai_followup_disposition` 존재 | 공통 의미를 재사용. group trigger는 AI PASS여도 호환 `WAIT`/probe 표현일 수 있어 raw action 단독 분류 금지 |
| [handoff](../../src/engine/automation/drought_handoff.py) / [PREOPEN](../../src/engine/threshold_cycle_preopen_apply.py) | canonical bytes뿐 아니라 normalized history·candidate 의미까지 재검증; candidate 정확히1개 계약 | schema 이행·diagnostic-only 후보의 allowed=false 및 generation을 생산자와 같은 규칙으로 확인 |

특히 `scope_summary()`는 단순 axis 이름만 보지 않고 exact terminal stage allowlist까지 확인한다. 이 보호를 유지해야 한다. 현재 addressable 축은 `UPSTREAM_GATE`, `ENTRY_AI_AUTHORITY_REVALIDATION`이지만, 동일 stage 이름을 사용한 새 AI VETO/오류까지 재검사 가능으로 인정할 위험이 있으므로 **role·원인·실제 runtime eligibility를 추가 대사**한다. 해당 우회가 실거래에서 발생했다는 판정은 이번 설계에 포함하지 않는다.

## 3. 데이터 모델: 평가·호출·제출을 분리

### 3.1 기존 artifact 안의 신규 블록

#119 JSON에 `entry_decision_funnel`을 추가한다. 별도 정기 producer·DB·Provider replay를 만들지 않는다. 소형 정규화 helper가 필요하면 기존 `src/engine/automation` 또는 `src/engine/scalping` 역할 패키지에 두며 engine root에 새 module을 만들지 않는다.

| 블록 | 제안 내용 |
| --- | --- |
| `contract` | `schema=machine_primary_entry_funnel_v1`, `metric_role=funnel_count`, `decision_authority=source_only_attribution`, `runtime_effect=false`, `allowed_runtime_apply=false`; 분모·window·quality·금지 용도 |
| `source_manifest` | target date/as-of, pipeline·payload archive·preflight path/hash/읽은 byte 범위, cache version, capture 가능 구간, release/정책 receipt 참조 |
| `by_cohort` | owner + entry route + canonical venue/session + decision-role version. 일중 policy bundle별 하위 집계를 유지 |
| `evaluation_ledger` | 기계 평가·AI screen·해당 평가의 최종 비진입/제출연결 상태. identity 결손/충돌은 별도 exclusion |
| `evaluation_submit_links` | evaluation → AI trace/response → submit call → exact submit attempt/order의 명시적 연결. 한 평가의 다중 call도 목록으로 보존 |
| `counts/ratios` | 기계 분기, AI 분기, accepted submit, pending·unresolved·excluded 분모와 보존식 |
| `routing` | 관찰/수리의 최초 owner, 원인, legacy recheck addressability, 근거 key. policy 실행권한 없음 |

기존 `entry_submit_drought_contract`/5개 submit axis와 raw counts는 compatibility로 보존한다. `MACHINE_GATE`/`AI_AUXILIARY_SCREEN`은 신규 상위 진단 taxonomy이며 기존 submit axis allowlist에 무조건 추가하지 않는다.

### 3.2 Identity와 중복 제거

1. 평가 key는 명시적 `evaluation_attempt_id`를 우선 사용하고 owner·symbol·venue/session·판정 시각·policy bundle을 함께 검증한다. snapshot fallback은 원 producer가 발급한 경우만 허용하고 `identity_kind=snapshot_fallback`을 보존한다. symbol+근접 시각 join은 금지한다.
2. archive의 `machine_observation_sha256`으로 byte-identical capture를 제거한다. 동일 evaluation identity의 상충 action/bundle은 마지막 행으로 덮지 않고 격리한다. capture 시각만 다른 반복행도 canonical evaluation identity로 대사하고 collision을 기록한다.
3. `scanner_promotion_id`는 평가의 parent다. submit call은 기존 `entry_submit_attempt_id`와 frozen `entry_submit_attempt_parent_promotion_id`를 보존한다. 같은 symbol의 다음 promotion으로 재귀속하지 않는다.
4. 평가→submit 연결은 실제 trace/snapshot/evaluation key가 전달된 경우만 허용한다. key 미전달은 `evaluation_submit_link_missing`으로 남긴다. submit call ID가 없는 기계 BLOCK 평가에 가짜 submit ID를 만들지 않는다.
5. 기존 ledger의 cycle/attempt/retry 의미와 순서를 유지한다. 먼저 있던 blocker가 동일 call에서 회복돼 제출됐다면 해당 blocker는 secondary 이력이며 최종 차단으로 중복 집계하지 않는다.
6. machine capture의 `provider_called=false`는 **그 capture 단계가 Provider를 호출하지 않았다는 뜻**이다. 같은 평가 뒤 실제 AI request가 없는 증거로 쓰지 않는다. 실제 request/response receipt를 별도로 결속한다.

### 3.3 필요한 원천 필드와 fallback

- 기계: action, reason codes, role/version, policy bundle/hash, evaluation/snapshot/promotion identity, assessment source hash.
- AI: request/response ID, input/response hash, screen required/status, advisory contract validity/errors, fact-bound VETO 사유, 최종 합성 action, followup disposition/authority.
- submit: call ID/frozen parent, exact terminal event·시각, 최종 authority/price/latency 결과, broker accepted/rejected/ambiguous receipt.
- 기존 typed payload archive를 정본으로 읽는다. pipeline cache는 현재 값을 문자열로 변환하므로 JSON bool/list/dict를 `str()` 결과에서 임의 복원하지 않는다. 필요한 scalar projection은 명시적 schema로 보완한다.
- 필수 field가 원천에 없으면 먼저 어느 producer에서 사라졌는지 확인한다. 필요한 최소 계측은 기존 capture/trace/call 종료 event에 추가하며, 새 시장수집·API 호출·재시도 주기 상향은 하지 않는다.
- entry trace 원문이나 인증 정보는 요약으로 복사하지 않는다. 요약에는 ID/hash·안전한 reason만 투영한다.

## 4. 상태 전이·보존식·분모

```text
scanner promotion (별도 탐색 분모)
  → evaluation
      ├─ machine BLOCK   → point blocked
      ├─ machine RECHECK → existing scanner observation; no entry authority
      └─ machine ENTER_NOW
           ├─ valid AI VETO → point blocked
           ├─ CAUTION / INSUFFICIENT / invalid / pending → no entry yet
           └─ valid AI PASS → existing authority/price/budget/latency guards
                                  → submit call → broker receipt
```

이 그림은 역할 순서다. budget·latency·price의 실제 실행 순서를 재배치하거나 각 unique count를 선형 인과 분모로 간주하지 않는다.

각 보고 window에서 다음을 검증한다.

```text
raw_unique_evaluations = valid_evaluations + excluded_evaluations
valid_evaluations = machine_enter + machine_recheck + machine_block
machine_enter = ai_pass + ai_veto + ai_caution + ai_insufficient
              + ai_invalid + ai_pending + ai_handoff_unresolved
ai_pass = eval_with_accepted_submit + eval_terminal_without_accepted_submit
        + eval_pending + eval_submit_link_unresolved
```

- 각 식의 항은 상호배타적이다. AI unknown role/action은 valid branch에 넣지 않고 exclusion 사유로 보존한다. 응답이 없다는 사실만으로 timeout이나 VETO로 분류하지 않는다.
- evaluation 기준 accepted는 유효한 연결 중 broker accepted가 하나 이상인 평가 수다. 제출 call/order 개수는 별도 집계한다. `order_bundle_submitted` 이벤트만으로 broker accepted 또는 full fill을 추정하지 않는다.
- 다중 call 중 하나 accepted면 평가 단위 accepted로 한 번 세고 실패한 다른 call은 call 원장에 유지한다. accepted는 있으나 추가 call 미해결이면 accepted 통계와 별도의 residual/ambiguous incident를 함께 보고한다.
- 과거 원천에 없는 기계 평가의 개수는 알 수 없다. `raw_unique_evaluations`는 실제 포착된 raw 안의 보존식이지 완전 수집의 증명이 아니다. 별도 expected capture receipt/coverage가 없으면 completeness unknown이다.
- window는 기존 #119 5/10/30분·session·as-of를 재사용한다. 평가시각으로 cohort를 고정하고 그 window의 평가에 연결되는 후행 event를 as-of까지만 읽는다. carry-in 평가/submit은 별도 열로 표시하여 window 바깥 성공을 분자에 섞지 않는다.
- pending 종료는 해당 runtime의 실제 terminal/TTL/timeout 계약으로 판정한다. 새로운 임의 대기시간을 만들지 않는다. deadline 이후 receipt 부재는 unresolved이지 가짜 실패 event가 아니다.
- ratio는 분모0/결손이면 null과 reason. `machine_enter/valid_evaluations`, `ai_pass/machine_enter`, `accepted_evaluations/ai_pass` 등을 각각 표시하며 경제적 EV로 사용하지 않는다.
- latency는 evaluation→machine 판정, machine ENTER→AI request, request→유효 response, AI PASS→submit call, call→broker receipt를 나눠 sample count/p50/p95와 결측수를 표시한다. source clock·실제 timestamp 의미가 다른 구간을 직접 빼지 않으며 음수·역전은 결손으로 보존한다. 시각 연결 진단은 새 latency threshold 추천 권한이 아니다.

### 4.1 Critical 경보의 단계적 전환

**1차 구현에서 기존 경보 수치와 #23 활성화 floor는 변경하지 않는다.** legacy 조건은 해당 legacy 의미가 확인되는 cohort의 compatibility 결과로 보존한다: AI unique>=20 및 submitted/AI<20%, 또는 budget unique>=3 및 submitted/budget<=10%.

새 machine primary 분모에 20/3 또는 20%/10%를 그대로 복사하지 않는다. 초기 신규 metric은 진단용이며 `sample_floor=not_defined_for_policy_activation`, `primary_decision_metric=legacy_contract_only`, `activation_use_allowed=false`를 명시한다. 이는 신규 alpha shadow가 아니라 비권한 계측이다.

machine cohort에서 legacy critical가 발생하면 관측 경보는 지우지 않고 새 원인 분석을 붙인다. 반대로 AI 호출 감소·전환기 표본 미달로 legacy critical가 없어져도 `transition_unverified/insufficient_evidence`를 표시하고 NORMAL·해소로 확정하지 않는다. 새 critical metric을 정책 활성화 기준으로 쓰는 변경은 별도 metric 설계·수치 검토·기존 승인 계약 확인이 필요한 후속이며 이번 source-only 수리의 숨은 단계가 아니다.

## 5. #23 소비: diagnostic routing과 runtime addressability 분리

| 실제 원인/상태 | #23이 발급할 진단 disposition | 기존 recheck policy 후보 사용 |
| --- | --- | --- |
| 기존 legacy score/WAIT-probe 차단, role·terminal·predicate 모두 exact | `legacy_recheck_addressable` | 기존 scope·최근3거래일·preflight·현재 env·guard 전체 통과 시에만 기존 계약 사용 |
| machine RECHECK | `machine_observation_followup` | 불가. 기존 scanner loop의 새 평가와 연결하며 #82 조건 연구로 handoff |
| machine BLOCK | `machine_point_block_review` | 불가. 정당한 차단/입력 결함/조건 경제성을 분리; hard block 우회 금지 |
| machine ENTER + valid AI VETO | `ai_auxiliary_veto_review` | 불가. 같은 타점 재probe 금지; #76/#82와 기존 AI 평가 owner로 전달 |
| CAUTION/INSUFFICIENT | `ai_auxiliary_evidence_followup` | 불가. 현재 계약의 무노출 관찰을 보존하며 새 호출 주기를 만들지 않음 |
| response/schema/transport 결손 | `source_or_transport_repair` | 불가. threshold 완화가 아니라 최초 source/transport owner 수리 |
| AI PASS 후 final authority 결손 | `final_authority_contract_review` | stage 이름만으로 허용 금지. legacy 소유권과 predicate가 모두 입증된 경우만 기존 후보 판정 |
| latency/price/DANGER/budget/broker 실패 | `downstream_owner_review` | recheck 첫 해법 아님. 기존 5축·direct consumer 유지 |
| role·evaluation linkage 결손/혼합 | `blocked_missing_evidence` | 활성화 근거로 사용 불가. 해당 row/cohort 격리 |

### 5.1 알고리즘 변경

1. `submit_drought_contract`가 source role/cohort와 새 분기 보존식을 검증한다. raw label을 소비자마다 다르게 해석하지 않는다.
2. `scope_summary()`는 `diagnostic_bottleneck`과 `legacy_runtime_addressability`를 별도로 계산한다. 현재 terminal stage allowlist에 role compatibility·명시적 source predicate 검사를 추가한다. machine `WAIT` 또는 score70을 legacy proof로 쓰지 않는다.
3. `_drought_day_summary()`는 정확한 날짜·scope 외에 role/cohort별 floor/critical/addressable와 source manifest hash를 보존한다. 동일 날짜 legacy/machine 혼재를 한 행의 `any()`로 policy 승인하지 않는다.
4. `eligible_scopes()`/`controller_decision()`은 같은 의미의 legacy policy lane에서 최신일 critical+최근 정확한3거래일 중2일 조건을 재계산한다. 누락일을 4~5일 전 자료로 채우지 않는다. machine9개 scope를 기존 #23 scope allowlist로 자동 확대하지 않는다. NXT overlap alias는 현재 `runtime_scope()`의 명시적 mapping만 사용한다.
5. controller report에는 기존 `calibration_candidates`와 별개인 `maintenance_review`/진단 route를 확장한다. machine 진단 때문에 legacy candidate가 allowed=true가 되지 않도록 PREOPEN도 독립 재검증한다.
6. 기존 candidate 정확히1개 구조는 유지하되, 신규 cohort·이행 결손만 있는 경우 `allowed_runtime_apply=false`와 직접 사유를 기록한다. unknown current env를 임의 OFF/ON으로 채우지 않는다. 후보 의미의 변경은 producer/validator/PREOPEN을 같은 change set에서 맞춘다.

### 5.2 상태 이관과 안전한 경계

- v4 stop latch·stopped_at·evidence_start·cooldown·scope별 economics와 durable reservation은 보존한다. 새 schema나 role가 생겼다고 stop 해제·episode reset·budget 초기화를 하지 않는다.
- 설계상 v5 reader는 검증 가능한 v4 state를 명시적 migration provenance와 함께 읽는다. 새 role의 critical를 v4 activation/recovery history로 재라벨링하지 않는다. migration 불가면 해당 정책의 평가 불가 사유를 내며 상태를 버리고 빈 `{}`로 재시작하지 않는다.
- unknown/mixed role는 noncritical/nonaddressable의 **입증된 날짜**가 아니다. 따라서 3일 정상·2일 비대상에 따른 disable 또는 stop renewal 근거로 세지 않는다. valid legacy 상태에서는 현행 stop/renewal 규칙을 유지한다.
- 정책 평가 불가와 현재 실행 중 env의 OFF는 다르다. 이 계획은 수동 env disable/enable을 수행하지 않는다. 현재 PID가 새 machine 비진입을 legacy probe로 우회하는 것이 확인되면 별도 runtime 결함/권한 검토가 필요하며 단순 report 완료로 덮지 않는다.
- 모든 main entry가 machine owner로 전환되어 legacy lane이 없어졌다면 결과는 `legacy_owner_not_applicable_for_machine_lane`이다. #23의 **진단 owner 역할은 유지**하되 legacy actuator의 유지·통합·퇴역은 실제 적용 상태·소유권을 검토한 별도 결정으로 남긴다. 표본 부족으로 무기한 대기하거나 임의 재활성화하지 않는다.

## 6. Cache·버전·source generation 이행

제안 버전은 구현 시작 시 현행 값과 충돌 여부를 다시 확인한다: report6→7, lossless cache12→13, 기존 submit exact3 유지 + 신규 machine funnel v1, controller policy v4→v5, source binding1→2. report outer schema1은 의미 변경을 감지할 수 있는 내부 버전 검증과 함께 유지할 수 있다. 기존 recheck attribution v3는 이 변경만으로 올리지 않는다.

- 새 reader/validator는 legacy schema와 신규 schema를 effective-date/role별로 명시적으로 분기한다. historical old schema는 history 진단용이고 machine 근거로 승격하지 않는다.
- cache identity에 source fingerprint·reader schema·as-of/읽은 범위를 포함한다. raw/cache/summary 3경로 parity와 일중 append 뒤 재읽기를 검증한다. append 중 마지막 불완전 행은 pending tail로, 닫힌 원본의 malformed 행은 결손으로 구분한다.
- 기존 full payload archive는 `iter_jsonl` 계열 streaming으로 target date/capture schema를 한 번 읽는다. #82의 고비용 후행 calibration을 #119/#23의 선행으로 만들지 않는다. postclose wrapper에서 #23은 #82보다 먼저 실행될 수 있다.
- 저장된 원본이 있는 target-date에 한해 새 parser로 재생성할 수 있다. 구일의 미수집 machine capture는 생성하지 않으며 과거 cache의 schema 번호만 고쳐 새 원천처럼 사용하지 않는다.
- source hash가 generation 중 바뀌면 부분 결과를 정책 승인하지 않는다. 기존 lock/atomic publish/bounded retry로 다음 완전 generation을 만든다. 성공 report를 failed partial로 덮거나 실행 중 main wrapper 코드를 교체하지 않는다.
- strict target-date 검증은 새 schema 경계·source bytes·정규화 의미·role별 합계·candidate 동일성을 모두 확인한다. 날짜 경계는 구현 실제 적용일로 기록하며 9/14로 소급 고정하지 않는다.

## 7. 수정 단위와 검증 책임

아래 WP는 설계 구분이며 native workorder ID가 아니다. 구현 시 기존 producer가 발급한 native ID와 전수 ledger에 연결한다.

| WP | 수정 예정 owner | 결과/완료조건 |
| --- | --- | --- |
| A. 정본 fixture·schema | `automation/submit_drought_contract.py`, 기존 `submit_drought_fixtures.py`/contract tests | 역할/identity/보존식/unknown/null·legacy 호환을 fixture로 고정 |
| B. source 연결 | `scalping/ai_decision_trace.py`, 필요시 기존 emit owner만; `buy_funnel_sentinel.py` | 기존 기계 archive와 AI trace/submit 연결. 신규 필드 누락이면 gap, fake AI/submit 생성0 |
| C. #119 진단 | `buy_funnel_sentinel.py`, 필요시 `pipeline_event_summary.py`/`sentinel_event_cache.py` | 평가와 call 원장·5축·cache parity·window/carry-in 및 Markdown 설명 일치 |
| D. #23 정책 격리 | `entry_recheck_policy.py`, `entry_ai_gate_backtest.py`, `entry_recheck_drought_controller.py`, `entry_recheck_review.py` | diagnostic route와 policy addressability 분리, exact3일·latch migration·scope 경계 |
| E. 직접 consumer | `threshold_cycle_preopen_apply.py`, `automation/drought_handoff.py`, `build_code_improvement_workorder.py`, `verify_threshold_cycle_postclose_chain.py` | 변조/오래된 role·source를 거절. 기존 native ID와 allowed=false 결과 전달 |
| F. 요약·회귀 | 실제 관련 EV/runtime summary/tower/checklist builder 및 기존 wrapper tests | 변경 필드가 직접 소비되는 곳만 수정. source→workorder→summary→tower→checklist→strict까지 동일 세대 |

wrapper 순서·cron·resource cap은 바꾸지 않는다. schema 계약이 바뀌는 구현 change set에서는 관련 traceability/운영 문서·당일 checklist를 함께 맞추되, 이번 계획 수립에서 baseline 문서나 운영 receipt를 수정하지 않는다. 신규 code module이 필요하면 위치 gate를 먼저 통과한다.

## 8. 필수 반례 테스트

| 반례 | 기대 결과 |
| --- | --- |
| machine BLOCK/RECHECK + AI 미호출 | 정상 기계 분기; AI failure0; legacy addressable=false |
| machine ENTER + AI PASS이나 호환 raw action WAIT/score70 | PASS로 분류하되 기존 주문 guard 유지; legacy WAIT-probe로 추정 금지 |
| valid VETO와 malformed VETO·CAUTION·missing response | 서로 다른 branch; 어느 것도 recheck probe 승인 금지 |
| transport 실패 뒤 같은 유효 요청이 회복됨 | terminal 성공 1건, 실패는 이력; 다른 request로 덮은 성공은 별도 identity |
| 동일 평가에서 다중 call, 실패 후 accepted | 평가accepted1; call 개수 별도; 최초 회복된 blocker 최종중복0 |
| bundle submitted이나 broker receipt 미확인/ambiguous | accepted 추정0, pending/unresolved와 원 call 보존 |
| submit 중 promotion 교체 | frozen parent 유지, 다음 wave 결속0 |
| 동일 evaluation의 bundle/action 충돌·source hash 위조 | 해당 identity exclusion; 식별 가능하면 다른 cohort까지 전면차단하지 않음 |
| raw/cache/summary/archive 중 한 경로 필드 탈락 | parity 실패; 요약count로 exact causal 원장 복원 금지 |
| as-of 이전 평가/이후 outcome, carry-in 제출 | future leakage0, 해당 window 평가분모 보존 |
| 전일 legacy + 당일 machine 혼재, 같은 날짜 role 혼재 | cross-role 2-of-3 활성화0; role 결손을 정상회복으로 집계0 |
| v4 stop state→v5, 중단 source가 rolling에서 빠짐 | latch·reservation 유지; 시간 경과만으로 ON0 |
| 정상 legacy 조건충족, 별도 machine 원천 결손 | 명시적으로 분리 가능한 legacy 판정 보존; machine 후보로 확대0 |
| machine9scope vs recheck4scope·integrated observe-only | 기존 live scope 확대0; 명시alias 외 venue/session 혼합0 |
| normal-sizing machine submit·타 owner fill 유입 | recheck direct1주/economics로 집계0 |
| source 갱신 후 과거 controller/hash/후행 PASS 재사용 | PREOPEN/strict 거절; 현재 command 실패를 옛 PASS로 대체0 |
| 새 report7인데 maintenance review가6만 허용 | schema transition 오진 없이 명시 버전 분기로 처리 |
| machine capture `provider_called=false` 뒤 실제 AI response | capture 단계와 AI 단계 독립 연결; 미호출 오분류0 |

구현 시 기존 테스트를 확장한다: `test_buy_funnel_sentinel.py`, `test_submit_drought_contract.py`, `test_sentinel_event_cache_parity.py`, `test_pipeline_event_summary.py`, `test_ai_decision_trace.py`, `test_entry_setup_evidence.py`, `test_entry_recheck_policy.py`, `test_entry_recheck_drought_controller.py`, `test_entry_recheck_review.py`, `test_entry_ai_gate_backtest.py`, `test_entry_recheck_submit_budget.py`, `test_threshold_cycle_preopen_apply.py`, `test_drought_handoff.py`, `test_threshold_cycle_wrappers.py` 및 실제 변경 consumer의 테스트. 전부 일괄 실행을 최소 요건으로 삼기보다 WP별 targeted selector를 고정하고 마지막 통합 회귀를 수행한다.

## 9. 구현 순서와 종료조건

1. **A → B → C:** schema/반례부터 고정하고 source와 #119를 구현한다. 분석 과정에서 기존 active predicate를 변경하지 않는다. 필요한 trace 추가가 live decision을 바꾸지 않는지 검토한다.
2. **D → E:** #23과 PREOPEN/strict reader를 함께 보완한다. 구·신 schema 및 stop state migration 검토가 끝나기 전 새 승인 artifact를 발행하지 않는다.
3. **F:** self-review→finding 수정→재리뷰→targeted pytest/compile, shell 변경 시 bash-n, diff check를 닫는다. 문서-only 검증에 trading test/Provider 호출은 요구하지 않는다.
4. 별도 구현/최소 재생성 권한과 active PID/lock·immutable run 확인 후에만 대상일 #119→#23→실제로 영향받은 workorder/요약 consumer를 재생성한다. 일반/strict verifier·controller/finalization은 해당 runbook 범위로 닫는다. 전체 backtest·Provider·성공한 upstream을 반복하지 않는다.
5. 새 generation 추천을 다시 intake해 eligible new/changed 항목과 미분류0을 확인한다. 권한 밖 actuator 변경은 `user_authority`, 과거 비가역적 원천은 `blocked_missing_evidence`로 별도 유지한다.

완료 판정은 다음 네 층이다.

- **설계/코드:** 이 문서의 원인·schema·consumer·회귀조건 검토 완료. 구현 시 해당 범위 P0~P2 미해결0, 보존식/authority 반례 PASS. 이 층에 양수EV·실주문 표본을 요구하지 않는다.
- **장후 전달:** canonical target date/hash와 신규 분모·#23 disposition이 workorder→요약→최종 strict에 동일하게 소비됨. report 생성만으로 완료하지 않는다.
- **반영/자연 acceptance:** 수정 release가 실제 source producer/PID에 반영됐는지, 이후 자연 평가·AI screen·submit 연결이 닫혔는지 별도 확인. 단순 보고서 수정이라 PID 교체가 필요 없는 경우 재기동을 요구하지 않는다.
- **효과:** 동일 scope/window·정책의 accepted submit 회복과 실제 비용 후 경제성은 별도 판정. 정상 비진입, 표본 미달, 분모 축소, 과거 receipt 복구를 drought 해소나 새로운 순이익으로 보고하지 않는다.

계획의 당일 검토 연결은 [기존 CodeImprovementWorkorderReview0914](../checklists/2026-09-14-stage2-todo-checklist.md), source-quality는 같은 checklist의 `PostcloseSourceQualityGateReview0914`, strict 요약은 `AutomationTriggerDecisionSummary0914`를 재사용한다. 향후 실제 구현/자연 acceptance는 그때의 current checklist에서 같은 owner의 유효 이관 여부를 확인한다. 계획 WP나 과거 `EntryRecheckNaturalAttribution0907` 이름만으로 새로운 실행 일정을 만들지 않는다.

## 10. 계획 문서 검증 기록

이 절의 초기 문서 검토 범위는 현재/제안 구분, producer/consumer 경로, AI PASS/VETO 의미, legacy probe 권한 분리, 분모·state 이행, 링크와 문서 파서였다. 당시에는 코드 구현·운영 실행·새 자연 표본 및 경제성을 검증하지 않았으며, 이후 구현 receipt는 §11에 분리해 기록한다.

- self-review 보완: raw WAIT/score70과 AI PASS의 분리, capture의 provider 미호출 의미, 평가/다중 submit call 분모, mixed-role 이행의 false recovery 방지, v4 latch/reservation 보존을 명시했다. 검토한 설계 범위의 미해결 finding은 0이며 구현 코드의 finding 0을 뜻하지 않는다.
- 상대 링크 14개 대상 존재 확인, print-only parser exit0/26개 task, 현재 날짜 checklist의 parsed stable ID 10개 유일성 확인. 새 실행 ID·체크박스는 추가하지 않았다.
- `git diff --check`와 신규 untracked 문서의 별도 whitespace check 통과. 문서-only이므로 pytest/compile·보고서 재생성·Provider·runtime 점검은 미실행이다.
- 외부 sync는 실행하지 않았다. 필요 시 사용자 실행 표준 명령은 다음 한 개다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

## 11. 구현·검토 receipt (2026-09-14)

### 적용한 최소 범위

- `buy_funnel_sentinel.py`에 `machine_primary_entry_funnel_v1`을 추가했다. producer-issued evaluation ID 기준으로 machine action → AI screen → pipeline submit → 성공 broker-response의 order identity를 분리한다. 이 receipt는 fill·terminal·비용 차감 손익으로 승격하지 않는다.
- `ai_decision_trace.py`가 이미 정의한 exact snapshot/caller evaluation identity를 capture 결과에도 투영했고, `ai_engine_openai.py`는 그 source-only provenance를 최종 AI result에 보존한다.
- `sniper_state_handlers.py`의 기존 AI event projection allowlist에 기계 owner/action/screen, evaluation identity와 capture receipt를 추가했다. 따라서 `ai_confirmed`가 #119 입력까지 필요한 scalar provenance를 전달한다. 주문·수량·threshold·provider·broker/safety guard는 변경하지 않았다.
- `entry_recheck_policy.py`는 machine-primary event만으로 legacy #23 WAIT-probe가 열리지 않게 한다. 별도로 입증된 legacy terminal candidate가 없는 machine-only scope는 `machine_primary_only_no_legacy_recheck_authority`이며 auto candidate를 발급하지 않는다.

### 검토 결과와 기대효과 경계

- source-bound identity, machine owner 누락/충돌, RECHECK/BLOCK, AI VETO, transport/local non-evaluation, pipeline submit과 broker acceptance response·fill/손익의 분리를 반례로 고정했다. source/role 결손은 정상 분모가 아니라 `identity_or_contract_gap`으로 남는다.
- 기대효과는 **기계 ENTER+AI PASS 이후 어느 guard/receipt에서 소실되는지 정확히 보이게 하는 것**이다. 이는 비용 차감 작은 수익의 빈도를 늘릴 후보를 찾는 전제이며, guard 완화나 재진입 증가 자체를 효과로 주장하지 않는다.
- 기존 #23 3일 exact attribution·bounded cap·probe-first·PREOPEN validation은 그대로다. 이 신규 funnel에는 activation floor를 복사하지 않았고 `allowed_runtime_apply=false`다. 따라서 현행 자동화는 legacy 조건이 검증된 후보만 PREOPEN으로 전달하며 machine 진단은 자동 매매 정책 변경으로 오인되지 않는다.
- targeted pytest 744개, Python compile, `git diff --check`를 통과했다. 코드 review/fix/re-review 범위의 unresolved finding은 0이다. 자연 이벤트가 새 PID/release에서 발생해 #119→#23→PREOPEN handoff를 닫는지와 동일 scope의 accepted submit·비용 차감 경제성은 별도 acceptance다.

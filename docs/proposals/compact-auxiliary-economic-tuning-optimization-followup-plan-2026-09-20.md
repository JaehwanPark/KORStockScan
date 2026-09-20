# Compact 보조 AI 경제성 튜닝 최적화 후속 계획

작성일: 2026-09-20 KST

범위: `verify_threshold_cycle_postclose_chain --compact-summary-only`가 검증하는 compact 보조 AI 직접 경로의 **미래 자연 원천, 후보 탐색, 비용 차감 paired 경제성, 정책 발행, PREOPEN·장중 소비 및 적용 후 성과** 최적화

권한: 이 문서는 구현 계획이다. 코드·보고서·정책·배포 선택·PREOPEN·PID·주문을 변경하거나 provider를 호출하지 않는다.

관련 기준: [Plan Rebase](../plan-korStockScanPerformanceOptimization.rebase.md), [메인 기계 진입판정 full-loop 복구계획](./main-mechanistic-entry-postclose-full-tuning-loop-restoration-plan-2026-09-20.md), [compact 단일 owner 구현계획](./compact-ai-postclose-source-paired-evaluation-and-preopen-consumer-integration-plan-2026-09-19.md), [다음 Stage2 checklist 인계계획](./build-next-stage2-checklist-direct-family-handoff-improvement-plan-2026-09-19.md), [2026-09-21 체크리스트](../checklists/2026-09-21-stage2-todo-checklist.md)

## 1. 결정

최적화 순서는 다음과 같이 고정한다.

1. 미래 자연 `ENTER_NOW` 기회마다 당시 plan·stop·수량·예산·비용·route·응답·identity를 손실 없이 결속한다.
2. 실제 주문·체결·완료 결과로 먼저 검증한 운영모델만 같은 scope의 counterfactual에 사용한다.
3. 경제성 계산이 가능한 입력에만 등록된 compact 후보 하나를 실행한다.
4. 동일 frozen 자본·수량·후행 guard에서 incumbent/candidate의 비용 차감 paired 결과를 비교한다.
5. 학습 이후의 독립 holdout에서 보수적 ΔEV, 일별 순익, tail, 자본 점유가 모두 통과한 scope만 dated policy로 승격한다.
6. 정상 PREOPEN·실제 PID·자연 판단·완료 손익을 적용 버전별로 추적한다.

현재 `paired -> dated policy -> main consumer -> checklist` 직접 인계와 scoped verifier는 완료된 기반으로 유지한다. 새 결함이 확인되지 않는 한 coordinator, 별도 handoff, 전용 schedule, 중복 publisher를 다시 만들지 않는다.

이 계획은 메인 기계 진입판정의 전체 튜닝을 대체하지 않는다. 메인 계획은 `ENTER_NOW`와 지원 가능한 `BLOCK/RECHECK` 반사실을 포함한 전체 기계 모집단, 기계 threshold 후보와 full report를 소유한다. 본 계획은 **현재 기계 parent가 `ENTER_NOW`로 통과시킨 기회 이후** compact 보조 AI가 PASS/VETO 계열 판단을 바꾸는 경제성만 소유한다. 장후 wrapper는 provider가 필요 없는 메인 기계평가를 먼저 종결하고 compact 평가를 뒤에서 독립 실행해야 하며, compact 실패·예산·표본 부족이 메인 평가를 생략하게 해서는 안 된다.

`PASS`의 의미도 분리한다.

- verifier `PASS`: 동일 source·policy·consumer·checklist hash가 연결됨
- evaluator `validated_edge`: 독립 holdout까지 통과한 모델 ΔEV 후보가 있음
- PREOPEN/PID `consumed`: 실제 프로세스가 해당 정책을 읽음
- actual economic acceptance: 적용 버전의 `COMPLETED + valid profit_rate + valid cost` 성과가 확인됨

앞 단계의 성공을 뒤 단계의 성공으로 대체하지 않는다.

## 2. 현재 기준선과 재작업 금지 경계

계획 기준선은 현재 확인된 immutable successor `compact-ai-exact-plan-reviewed-20260920-01a5889a7`, commit `01a5889a7db3b1a2ed25f57b77c3734dc770699d`이다. 이 successor에는 `compact_pre_ai_execution_source_v7`과 owner replay의 `plan_sha256`에 결속된 exact `entry_economic_plan_sha256` 검증이 들어 있다. 이는 미래 호출용 코드 closure이며 자연 첫 행, 실제 PID 소비, 경제성 acceptance를 증명하지 않는다. 작업본에는 다른 세션의 변경이 누적되어 있으므로 구현 시 실제 selected release·현재 PID와 이 기준선을 다시 대조하고, 관련 변경만 별도 작업공간에서 다룬다.

현재 확인된 상태는 다음과 같다.

| 축 | 현재 상태 | 계획에서의 처리 |
| --- | --- | --- |
| 직접 인계 | scoped verifier `PASS` | 유지, 경제성 계산기로 확장하지 않음 |
| 과거 자연 입력 | screen 21, source 제외 21, paired 0 | 재생·추정 복구하지 않고 audit/exclusion 보존 |
| 주된 과거 결손 | exact stop/plan 10, transport 8, identity 2, semantic 1 | 과거 결손과 미래 producer 정상 생성을 분리 |
| 후보·경제성 | candidate 0, ΔEV·일별 순익 null | `valid_no_edge`가 아니라 `blocked_source` 유지 |
| 정책 | 2026-09-21 incumbent carry | 정상 dated fallback으로 보존 |
| runtime | 실제 PID 소비 미확인 | 정상 PREOPEN 이후 별도 acceptance |
| exact plan 결속 | v7·`entry_economic_plan_sha256 == owner replay plan_sha256` 코드 closure | 재구현하지 않고 첫 자연 행과 downstream 보존만 검증 |
| 메인 기계 full-loop | 별도 계획·체크리스트 owner에서 복구 진행 중 | compact PASS로 대체하지 않고 wrapper 선행 단계로 결속 |

현재 구현에서 경제적 탐색 효율을 더 높여야 하는 지점은 다음과 같다.

| 잔여 지점 | 영향 | 최적화 방향 |
| --- | --- | --- |
| exact plan 결속은 구현됐지만 자연 첫 행으로 아직 입증되지 않음 | 같은 source exclusion이 반복될 수 있음 | 재구현 없이 첫 자연 행을 plan hash→response→label→owner replay까지 즉시 대사 |
| 기본 후보가 opportunity variant로 정해짐 | 실제 손실 원인이 false PASS인데도 맞지 않는 후보에 비용을 쓸 수 있음 | incumbent 학습구간의 missed-profit/avoided-loss 기여로 opportunity 또는 risk 한 개를 사전 고정 |
| source가 적격이면 실행모델 검증 전에도 후보 호출 가능 | 나중에 운영모델 결손으로 EV가 null인데 provider 비용만 발생할 수 있음 | exact scope의 prior model validation까지 candidate execution admission에 포함 |
| 현재 보수적 하한은 model error·stress envelope이며 통계적 신뢰구간은 아님 | 작은 날짜 수의 양수 결과를 과대해석할 수 있음 | 현재 gate를 유지하고 날짜별 분산·최악 구간을 병기하며 표본 부족을 명시 |
| runtime inference 비용은 검토된 operator zero-cost만 직접 지원 | 실제 nonzero 비용 환경에서는 정책 승격이 계속 차단될 수 있음 | 기존 pricing owner의 measured token delta와 검토된 KRW 환산 계약이 있을 때만 nonzero 비용 지원 |
| integrated aftermarket는 정상 SOR 연구 scope이나 authority가 별도임 | route 지원과 live 권한을 혼동할 수 있음 | source admission은 허용하고 기존 observe/live authority를 정책 승격에서 별도 검증 |

다음 구현은 이미 닫힌 항목을 반복하지 않는다.

- compact evaluator 단일 owner화
- candidate fingerprint·checkpoint·provider budget·idempotency
- `blocked_source|waiting_model_or_sample|ready_to_evaluate|evaluated_hold|validated_edge` 상태
- paired artifact에 직접 결속된 dated policy와 consumer
- `source_gap|unsupported_scope|pending|insufficient_sample|valid_no_edge` 구분
- compact scoped verifier의 직접 hash fail-close 연결

메인 full-loop의 `full report scope`, `noncompact_sections_refreshed`, wrapper 선행 순서와 family별 source 보존은 진행 중인 메인 계획의 구현 범위다. `--compact-summary-only` PASS는 compact 내부 인계만 닫으며 장후 전체 chain 완료를 증명하지 않는다.

## 3. 목표 데이터 흐름과 owner

```text
final source / cost / terminal evidence
  +-> main mechanistic full evaluator
  |     -> all supported machine decisions and machine CF population
  |     -> machine candidate/carry disposition
  |
  +-> machine ENTER_NOW frozen parent
        -> natural compact request/response
        -> exact plan-hash-bound owner operating replay
        -> independently validated execution model
        -> one frozen compact candidate
        -> same-input paired economics
        -> independent compact holdout
        -> compact candidate/carry disposition

machine disposition + compact disposition
  -> mechanistic_entry_runtime_policy single publisher
  -> family-specific source/parent references in one dated bundle
  -> Daily / runtime summary / checklist / full verifier
  -> PREOPEN bootstrap / live loader / actual PID
  -> natural decision / order / fill / COMPLETED net result
  -> applied-version rolling and cumulative evaluation
```

기존 owner를 다음과 같이 재사용한다.

| 계약 | 기존 owner |
| --- | --- |
| 메인 기계 전체 모집단·threshold 평가 | `ai_action_outcome_calibration` full evaluation |
| 기계 판단·compact 호출 원천 | `ai_decision_trace`, `ai_decision_payloads` |
| 결과 라벨·identity | `ai_decision_outcome_labels`, `ai_decision_quality` |
| AI 이전 frozen plan·수량·예산 | `strategy_owner_replay.freeze_entry_opportunity` |
| 운영 arm·모델 검증 | `entry_split_order_plan`의 `compact_pre_ai_execution_replay`, `execution_model_validation` |
| 후보 실행·paired 평가 | `compact_auxiliary_paired_replay`를 호출하는 기존 `entry_setup_paired_replay_batch` |
| 단일 정책 발행·장중 소비 | `mechanistic_entry_runtime_policy`, `entry_setup_live_policy` |
| 최종 인계 | `main_ai_prompt_consumer`, runtime summary, checklist, `verify_threshold_cycle_postclose_chain` |

새 서비스·DB·collector·cron·root CLI·별도 policy family는 추가하지 않는다.

### 3.1 메인 기계 lane과 공유·분리할 계약

| 항목 | 처리 |
| --- | --- |
| exact opportunity identity·frozen plan·cost/terminal provenance | 공유한다. 같은 자연 episode의 원천 사실을 복제하지 않는다. |
| 실행모델 | 검증된 scope는 공유할 수 있으나 compact `ENTER_NOW` 지원이 기계 `BLOCK/RECHECK` downstream 지원을 증명하지 않는다. |
| 모집단·분모 | 분리한다. machine은 전체 지원 기계결정, compact는 현재 machine parent의 `ENTER_NOW`만 사용한다. |
| 후보 grid·prompt/threshold | 분리한다. compact 후보로 기계 threshold를 바꾸거나 machine 후보로 compact prompt를 바꾸지 않는다. |
| model holdout·candidate holdout·consumption ledger | family별 namespace와 소비 이력을 분리한다. 같은 결과를 양쪽 독립 승격 증거로 중복 소비하지 않는다. |
| disposition·경제성 지표 | family별로 보존한다. 한쪽 결손이나 no-edge를 다른 쪽 결과로 덮지 않는다. |
| publisher·dated bundle·PREOPEN loader | 기존 단일 경로를 공유하며 family별 source date/path/hash·parent·disposition을 함께 보존한다. |

두 family 후보가 각각 독립 gate를 통과해도 동시 적용 권한은 생기지 않는다. 같은 entry stage에서는 exact 조합의 독립 proof와 기존 same-stage 권한이 없으면 한 번에 하나만 바꾼다. 메인 후보가 현재 compact 정책을 고정한 full downstream 검증을 통과하면 메인을 우선하고 compact는 carry한다. 기계 parent가 바뀌면 기존 compact proof는 `parent_changed_revalidation_required`로 유지하며 새 parent에 자동 승격하지 않는다. compact prompt/input semantics가 바뀐 경우에도 고정 AI를 전제로 한 machine proof를 재검증한다.

## 4. EO0 — 구현 기준선과 변경 분리

구현 착수 시 다음을 먼저 수행한다.

1. selected release의 compact 관련 파일과 작업본 diff를 대조한다.
2. 다른 세션이 수정 중인 `entry_split_order_plan`, low-price, checklist 생성기 변경을 보존한다.
3. successor에 이미 있는 v7 exact plan-hash source 계약과 기존 model/holdout 계약을 기준으로 누락만 수정한다.
4. 실행 중 release를 직접 편집하지 않고 검증된 successor를 만든다.
5. 과거 21건을 복구하기 위한 raw 전수 재스캔이나 가상 stop·SELL·비용 생성은 금지한다.

종료 조건:

- 변경 대상 함수·producer·consumer 목록 확정
- 기존 완료 코드와 신규 결손을 구분한 review manifest 작성
- 관련 없는 workspace 변경 0건 포함

## 5. EO1 — 미래 자연 source admission을 경제성 기준으로 닫기

### 5.1 AI 호출 전 frozen plan의 자연 전달 검증

v7에서 exact plan-hash 결속은 이미 구현됐다. 동일 필드를 다른 producer에 다시 기록하지 않는다. 기계가 `ENTER_NOW`를 결정한 시점에 AI 응답과 무관하게 기존 owner replay에 고정된 다음 내용이 request/trace/label/projection까지 같은 hash로 전달되는지 검증하고, 실제 누락 필드만 기존 producer에서 수리한다.

- `evaluation_attempt_id`, `scanner_promotion_id`, `decision_trace_id`
- stock, decision timestamp, policy/bundle hash
- `effective_venue`, `session_bucket`, `broker_route`
- 승인된 total quantity와 leg plan
- owner별 승인 budget과 reserve
- 당시 사용 가능한 entry price·stop·exit policy version
- fee/tax/slippage cost policy와 provenance
- operator lock·custody·hard guard 상태

AI가 이후 `VETO`, `CAUTION`, `INSUFFICIENT`를 반환해 실제 주문이 없더라도 pre-AI plan은 보존되어야 한다. 후보가 없던 주문·수량·손절을 장후에 새로 만들지 않는다.

`owner_operating_arm`이 완전한 경우 generic 10분 label의 stop 결손 때문에 같은 행을 다시 제외하지 않는다. 운영 arm이 없을 때만 기존 terminal path를 진단용 fallback으로 사용하며, 이 fallback만으로 정책을 승격하지 않는다.

### 5.2 route 계약

다음은 지원 가능한 정상 시장 계약으로 다룬다.

- 프리마켓: NXT 계열 session, broker order route `SOR` 허용
- 정규장: KRX/NXT decision venue와 해당 session, broker order route `SOR` 허용
- 통합 애프터마켓: `KRX_NXT_INTEGRATED|KRX_NXT_AFTERMARKET`, broker order route `SOR`

`SOR`는 broker routing이며 실제 체결시장과 동일한 값으로 강제하지 않는다. 직접 KRX/NXT route가 아니라는 이유만으로 제외하지 않는다. 실제 scope 권한은 기존 `scope_authority_mode`, rollout, operator promotion artifact를 그대로 따른다. observe-only scope를 이 계획만으로 live scope로 바꾸지 않는다.

### 5.3 identity와 자연 응답

trace·payload·label·owner replay는 다음 키를 일대일로 대사한다.

```text
decision_trace_id
+ evaluation_attempt_id
+ scanner_promotion_id
+ stock_code
+ venue/session/route
+ payload_sha256
+ issued_prompt_sha256
+ machine_bundle_sha256
+ entry_economic_plan_sha256
+ owner_replay.seed.plan_sha256
```

`entry_economic_plan_sha256`와 owner replay `plan_sha256`가 불일치하거나 한쪽이 없으면 `source_gap`이며 candidate 호출·승격을 차단한다. 과거 21건에는 값을 추정 삽입하지 않는다.

응답은 provider/model, transport, response schema, semantic validation을 별도 단계로 기록한다. timeout/transport 실패는 향후 정상 호출로 새 적격 행이 생길 수 있지만 실패한 과거 행 자체는 복구된 것으로 간주하지 않는다. identity 불일치가 재발하면 표본 대기가 아니라 producer/materialization 결함으로 즉시 분류한다.

### 5.4 admission funnel

새 report family를 만들지 않고 기존 paired report에 scope/route별 funnel을 추가·검증한다.

```text
machine_enter_now
-> compact_call_required
-> natural_response_received
-> response_contract_valid
-> frozen_input_valid
-> owner_plan_valid
-> operating_arm_valid
-> prior_model_scope_valid
-> economic_eligible
-> candidate_response_valid
-> paired_comparable
```

각 행은 최초 탈락 사유 하나만 갖는다. 합계 보존과 중복 없는 episode identity를 검사한다.

구현 종료 조건:

- 지원 scope의 합성·통제 입력에서 funnel conservation PASS
- 실제 producer와 같은 호출 경로의 통제 입력에서 plan hash·response·identity·operating arm이 한 episode로 연결됨
- 같은 결손이 반복될 때 정확한 producer owner와 closure test가 출력됨

다음 자연 입력의 동일 연결 확인은 구현 closure를 다시 대신하지 않는 자연 acceptance다. 통제 경로가 실패하면 구현 미완료이고, 통제 경로가 통과한 뒤 자연 입력이 아직 없으면 `waiting_model_or_sample` 또는 해당 자연 owner의 OPEN으로 남긴다.

## 6. EO2 — 운영모델을 후보 탐색보다 먼저 검증

compact 후보의 경제성은 실제 주문·체결·완료 결과로 검증된 기존 실행모델을 사용한다. 후보 holdout을 운영모델 보정에 재사용하지 않는다.

이 모델의 compact 지원 단위는 현재 machine parent가 통과시킨 `ENTER_NOW` 이후의 frozen owner plan이다. 이 scope 검증만으로 기계 `BLOCK/RECHECK` 완화 후보의 미호출 AI·submit·exit 경로까지 지원한다고 확장하지 않는다. 반대로 compact model/provider 결손은 provider-free 메인 기계 full evaluation을 막지 않는다.

### 6.1 운영모델 모집단

실제 submit owner가 확인되는 episode에서 다음을 구성한다.

- frozen owner plan·requested quantity·budget
- broker order와 full/partial/no-fill/terminal
- 운영 exit owner와 완료 시점
- 비용 policy version과 실제 사용된 비용 provenance
- capital/reserve 점유 시간

`actual fill`은 실행모델 오차 검증에 사용하고, compact VETO의 counterfactual 결과는 동일 frozen plan을 검증된 모델에 통과시켜 계산한다. 실제 SELL이나 다른 CF 보유 경로를 붙이지 않는다.

### 6.2 시간순 독립성

scope별 실행모델은 다음 순서를 만족해야 한다.

```text
model calibration actuals
< model holdout actuals
< model available_after_date
< compact candidate learning episodes
< candidate freeze
< candidate holdout episodes
```

운영모델 holdout에서는 VWAP, receipt clock, quantity, net error budget, capital, reserve 오차를 검증한다. false fill, missed fill, quantity error가 있는 scope는 compact 후보를 평가하지 않는다.

### 6.3 모델 상태

- 입력 원천 미완전: `source_gap`
- 해당 route/scope 설계 미지원: `unsupported_scope`
- 계약은 정상이나 실제 model holdout 부족: `waiting_model_or_sample`
- holdout tolerance 실패: `model_validation_failed`
- exact scope 검증 완료: `validated_scope`

종료 조건:

- candidate 학습일보다 이전인 독립 실제 model holdout receipt
- exact venue/session/route·cost·exit·quantity scope hash 일치
- model tolerance와 error envelope가 실제 holdout 관측치에서 산출됨
- 모델 결손 상태에서는 candidate provider 호출 0

## 7. EO3 — 후보 탐색 공간을 작고 경제적으로 유지

후보 탐색은 현행 기계 `ENTER_NOW` 이후 compact 보조 AI의 PASS/VETO 역할에만 한정한다. 기계 non-entry, 가격, 수량, split, provider/model을 같은 탐색에 섞지 않는다.

### 7.1 후보 가설

기존 registry의 두 successor만 사용한다.

- opportunity candidate: incumbent VETO가 회피한 이익보다 놓친 비용 차감 이익이 큰 학습구간
- risk candidate: incumbent PASS의 손실·tail 악화가 VETO 기회비용보다 큰 학습구간

학습구간에서 incumbent VETO의 frozen operating outcome과 incumbent PASS의 비용 차감 operating outcome을 이용해 missed-profit·avoided-loss 기여를 계산하고 둘 중 하나만 고른다. 이 단계에는 후보 응답이나 후보 holdout을 사용하지 않는다. 후보 선택 규칙과 prompt hash를 candidate plan에 먼저 고정한 뒤 holdout을 연다. 같은 holdout을 보고 opportunity/risk 후보를 바꿔 다시 선택하지 않는다.

### 7.2 중복 탐색 차단

- incumbent와 prompt/schema hash가 같은 후보는 `identical_policy`
- learning에서 판정 변경 0이며 의미상 규칙도 같은 후보는 `redundant_candidate`
- source/model이 준비되지 않은 입력에는 provider 호출 0
- exact machine parent·prompt input semantics가 freeze되지 않은 입력에는 provider 호출 0
- 유효 checkpoint는 재사용하고 실패한 입력만 기존 상한 안에서 재개
- 한 scope·generation에는 distinct candidate 하나만 유지
- 기존 후보가 `valid_no_edge`로 닫히기 전 새 후보 generation을 열지 않음

후보 수를 늘려 양수 결과를 찾지 않는다. 두 후보가 모두 필요해 보이면 서로 다른 미래 generation과 서로 다른 미사용 holdout을 사용한다.

종료 조건:

- candidate 선택이 holdout 결과에 의존하지 않음
- candidate version·prompt/schema/model/source/cost hash가 fingerprint에 포함됨
- retry에서 provider·pair·policy 중복 0

## 8. EO4 — 동일 자본의 paired 경제성 계산

### 8.1 공통 모집단

각 episode i의 plan·수량·budget·entry/exit/cost·후행 guard를 고정하고 compact verdict만 바꾼다.

```text
incumbent_net_i = operating_net_i if incumbent executes else 0
candidate_net_i = operating_net_i if candidate executes else 0
paired_delta_i  = candidate_net_i - incumbent_net_i
```

같은 verdict도 모집단에 포함하며 delta는 0이다. changed-decision subset은 원인 진단일 뿐 primary 분모가 아니다.

`CAUTION`·`INSUFFICIENT`는 장중 router가 해당 attempt에서 주문을 내지 않는다는 계약과 terminal 상태가 확인될 때만 no-exposure로 계산한다. recheck가 이어지는 계약이면 parent/attempt 종료까지 연결되기 전에는 `pending`으로 둔다.

### 8.2 포트폴리오 재현

incumbent와 candidate를 각각 동일한 one-position budget으로 시간순 replay한다.

- 겹치는 episode가 같은 자본을 동시에 사용하지 않도록 차단
- owner가 승인한 동일 총수량과 budget 사용
- full/partial/no-fill·capital/reserve minutes 분리
- runtime inference 비용 차감
- scope·route별 독립 계산 후 허가된 portfolio 수준에서만 합산

독립 episode 합만 가능하면 `independent_episode_cf_sum`으로 표시하고 실행 가능한 일별 순익으로 사용하지 않는다.

### 8.3 필수 지표

- incumbent/candidate 비용 차감 EV
- paired ΔEV와 stress ΔEV
- 원화 일별 순익과 paired 일별 순익 차이
- worst, ES10, 손실 episode 수
- capital/reserve `KRW-minutes`
- fill participation과 no-fill 비율
- 판정 전환 matrix와 변경률
- provider runtime 비용
- 모집단 coverage와 exclusion 편향

모델 오차는 판정이 달라진 pair에만 적용한다. 보수적 지표는 현재처럼 base/stress 중 작은 delta에서 실제 model error envelope와 inference 비용을 차감한다. 이를 통계적 신뢰구간이나 실제 이익으로 부르지 않는다.

runtime inference 비용이 0이 아니라면 기존 provider pricing artifact, incumbent/candidate의 측정 token delta, 검토된 USD→KRW 환산 provenance가 모두 있어야 한다. 하나라도 없으면 비용을 0으로 놓지 않고 `source_gap`으로 남긴다.

종료 조건:

- 같은 frozen 입력에서 양팔 계산 재현 가능
- 비용·quantity·capital·reserve 보존
- missing 값을 0으로 대체하지 않음
- 겹치는 자본이나 지원하지 않는 scope는 구체 blocker로 차단

## 9. EO5 — 후보 freeze와 독립 holdout

현재 승인된 최소 gate를 결과를 본 뒤 완화하지 않는다.

- scope·route별 learning 독립 episode 20 이상
- candidate freeze 이후 holdout episode 20 이상
- holdout source day 2 이상
- response coverage 1.0
- candidate selection holdout 미사용
- model holdout이 candidate learning보다 선행

20/20/2는 최소 실행 gate이지 통계적 충분성 보장이 아니다. 보고서에는 날짜별 delta와 표본 분산을 함께 노출한다. 표본 변동이 큰 경우 기준을 낮추지 않고 `insufficient_sample`을 유지한다.

holdout은 한 번만 소비한다. 실패한 후보의 다음 후보를 같은 holdout에서 선택하지 않으며 consumption ledger를 policy proof와 결속한다.

machine과 compact의 candidate-selection holdout ledger는 분리한다. 같은 자연 episode가 양쪽 진단 모집단에 나타날 수는 있지만, 같은 결과를 두 family의 독립 승격 증거로 소비하거나 두 변경의 동시 적용 근거로 사용하지 않는다. exact combination candidate를 사전에 freeze하고 별도 미사용 holdout에서 검증한 경우에만 조합 proof로 인정한다.

## 10. EO6 — 승격·fallback·runtime 소비

scope별 승격에는 다음이 모두 필요하다.

1. source funnel과 denominator 보존
2. prior operating model `validated_scope`
3. learning·holdout 시간순 독립성
4. holdout의 보수적 paired ΔEV 하한 양수
5. 동일 budget portfolio 일별 순익 차이 양수
6. candidate worst와 ES10이 incumbent보다 악화되지 않음
7. stress delta 양수
8. inference 비용 포함
9. holdout 미소비 및 exact scope authority

한 scope의 증거로 다른 scope의 prompt를 바꾸지 않는다. 승격 scope만 후보 prompt를 선택하고 나머지는 incumbent를 유지한다. observe-only scope는 기존 별도 authority가 없으면 연구 결과만 남긴다.

compact evaluator는 독립 최종 정책을 발행하지 않고 family terminal proof만 기존 단일 publisher에 넘긴다. publisher는 machine과 compact의 `source_date`, source path/hash, parent policy/prompt hash, disposition을 같은 dated bundle에 각각 보존한다. compact finalize 직전에 최신 machine parent를 다시 읽어 proof의 parent와 대사하며, 달라졌으면 `parent_changed_revalidation_required`로 carry한다. 마지막 compact finalize가 앞선 machine report·source reference를 덮어쓰면 발행 실패로 처리한다.

machine과 compact가 모두 `validated_edge`여도 exact 조합 proof가 없으면 동시 적용하지 않는다. 메인 계획의 same-stage 규칙에 따라 machine 후보를 현재 compact incumbent에 대해 먼저 적용하고 compact candidate는 carry한다. compact만 검증되고 machine이 carry이면 compact scope만 갱신할 수 있다. 한쪽 실패·결손은 다른 쪽의 유효 결과를 삭제하지 않지만, 필수 full machine evaluation 미실행은 장후 전체 완료를 막는다.

실패 처리는 다음과 같다.

| 상태 | 정책 동작 |
| --- | --- |
| `source_gap` / `unsupported_scope` | incumbent carry, mutation 0 |
| `pending` / `insufficient_sample` | incumbent carry, 자연 누적 |
| `valid_no_edge` | incumbent carry, 동일 후보 반복 금지 |
| `validated_edge` | 해당 scope만 dated successor 발행 |
| stale/hash/scope/holdout 실패 | fail closed, 이전 유효 incumbent |

정책 발행 후 기존 경로로 Daily·runtime summary·checklist·scoped verifier까지 compact 직접 hash를 확인한다. `--compact-summary-only`는 compact 내부의 빠른 인계 gate로 유지하고 튜너나 정책 선택기를 추가하지 않는다. 장후 전체 closure는 별도로 full machine report scope, `noncompact_sections_refreshed=true`, wrapper의 machine→compact 순서, machine/compact family source reference를 strict verifier에서 확인해야 한다.

## 11. EO7 — PREOPEN·PID·자연 성과

### 11.1 PREOPEN과 PID

정상 PREOPEN에서 다음을 별도 확인한다.

- source/publication/effective date
- policy bundle·machine threshold policy·compact prompt·scope·각 parent hash
- incumbent carry의 mutation 0 또는 validated scope만 변경
- stale/operator lock/same-stage conflict
- selected release와 bootstrap receipt
- 실제 child PID의 cwd·bundle·prompt 소비

파일 검증만으로 PID 소비를 주장하지 않는다. 이 계획은 조기 PREOPEN 확정이나 봇 재시작을 허가하지 않는다.

### 11.2 적용 후 성과

실제 compact decision version별로 다음 identity를 사용해 episode 중복을 제거한다.

```text
policy_bundle_sha256
+ machine_policy_version/machine_policy_sha256
+ prompt_version/prompt_sha256
+ decision_trace_id
+ evaluation_attempt_id
+ scanner_promotion_id
+ order owner/broker order
```

성과는 rolling/cumulative 양쪽에서 평가한다.

- 실제 issued PASS/VETO/CAUTION/INSUFFICIENT
- order submitted, full/partial/no-fill, terminal
- `COMPLETED + valid profit_rate + valid cost` 실제 순익
- 자본·reserve·노출·tail
- 모델 예측과 실제 완료 결과의 오차

counterfactual 모델 ΔEV와 실제 적용 순익은 다른 필드·다른 판정으로 유지한다. 실제 후보 성과가 나쁘면 기존 family의 rollback/safety owner가 판단하며, 본 계획이 새 손실 threshold를 만들지 않는다.

## 12. 상태 전이와 candidate 0 해석

```text
blocked_source
  -> waiting_model_or_sample
  -> ready_to_evaluate
  -> evaluated_hold | validated_edge
```

candidate 0은 다음 중 하나로만 보고한다.

| 분류 | 의미 | 다음 조치 |
| --- | --- | --- |
| `source_gap` | 미래 producer/identity/cost/plan 계약 미완성 | owner 수리와 회귀 검증 |
| `unsupported_scope` | 설계·authority상 지원하지 않음 | 지원/제외 결정과 consumer 검증 |
| `pending` | 유효 입력이나 candidate response/terminal 미완료 | 실패 입력만 재개 |
| `insufficient_sample` | 미래 생성 계약은 정상이나 독립 표본 부족 | 자연 누적 |
| `valid_no_edge` | 완전한 독립 비교에서 경제성 gate 실패 | incumbent 유지, 동일 후보 종료 |

`decision_changed_count=0`은 paired 모집단이 0일 때 중복 후보 증거가 아니다. 유효 paired 비교가 존재할 때만 동일 판정 여부를 해석한다.

## 13. 구현 패키지와 검증

| 패키지 | 구현 범위 | 핵심 검증 |
| --- | --- | --- |
| EO0 | 기준선·diff·owner 확정 | 다른 세션 변경 보존, selected release 대조 |
| EO1 | v7 exact pre-AI plan·identity·route·funnel | plan hash producer→projection one-to-one, SOR/통합시장 정상 admission |
| EO2 | 실제 execution model calibration/holdout | chronological independence, exact scope, error envelope |
| EO3 | outcome-blind 한 후보 freeze | opportunity/risk 중 하나, holdout 비열람, provider 중복0 |
| EO4 | same-budget paired economics | cost·capital·reserve·tail·overlap·null 처리 |
| EO5 | learning/holdout consumption | 20/20/2, 날짜 분리, holdout 재사용 차단 |
| EO6 | family disposition과 단일 publisher handoff | parent change·candidate/hold/fallback·동시 승격 차단·family source 보존 |
| EO7 | 적용 조합 버전 성과 연결 | machine policy+compact prompt+PID·자연 decision·order/fill·COMPLETED PnL dedup |

기존 테스트 파일을 보강한다. 새 테스트 family를 만들지 않는다.

- `test_strategy_owner_replay.py`
- `test_entry_split_order_plan.py`
- `test_ai_decision_quality.py`
- `test_entry_setup_paired_replay_batch.py`
- `test_ai_action_outcome_calibration.py`
- `test_mechanistic_entry_runtime_policy.py`
- `test_entry_setup_live_policy.py`
- `test_main_ai_prompt_consumer.py`
- `test_verify_threshold_cycle_postclose_chain.py`

필수 회귀 사례:

- AI VETO 전 plan/stop/cost/quantity 보존
- NXT premarket·KRX/NXT regular·통합 aftermarket의 SOR route
- transport/semantic/identity 오류의 배타적 최초 blocker
- source/model 미완료 시 provider 0
- compact 결손에도 provider-free full machine evaluation 실행
- same verdict delta 0과 changed verdict signed delta
- CAUTION follow-up 완료/미완료 구분
- full/partial/no-fill, overlapping capital, reserve, null cost
- model holdout과 candidate holdout 교차 사용 차단
- machine/compact holdout consumption 분리와 exact 조합 proof 없는 동시 승격 차단
- opportunity/risk 후보의 outcome-blind freeze
- scope별 한정 승격과 다른 scope incumbent 보존
- stale/hash/consumed holdout fallback
- machine parent 변경 시 compact proof carry·재검증, compact finalize의 machine source 보존
- full machine report·noncompact refresh 없는 compact-only 전체 closure 차단
- PREOPEN 파일 PASS와 실제 PID 소비 분리
- applied version episode dedup과 actual/model PnL 분리

검증은 targeted pytest, Python compile, affected wrapper `bash -n`, `git diff --check`, print-only checklist parser로 제한한다. provider·broker·주문·봇 재시작·전수 raw replay·과도한 성능검사는 수행하지 않는다.

## 14. 2026-09-21 자연·장후 closure 순서

다음 영업일에는 결과를 기다리기만 하지 않고 최초 자연 행의 경계를 순서대로 확인한다.

1. 정상 PREOPEN에서는 전일 발행된 incumbent dated policy와 실제 PID 소비만 확인한다. 같은 날 POSTCLOSE에 생성할 새 정책을 조기 PREOPEN 적용으로 보고하지 않는다.
2. 첫 machine `ENTER_NOW`에서 v7 exact plan hash·quantity·budget·route receipt를 확인한다.
3. natural compact response와 exact trace/payload/label/owner replay identity를 확인한다.
4. POSTCLOSE wrapper는 final source·cost·terminal을 봉인한 뒤 provider-free 메인 기계 full evaluation을 먼저 실행하거나 동일 fingerprint의 검증 결과를 재사용한다.
5. 메인 report와 machine candidate/carry disposition을 봉인한 뒤 그 parent에 결속해 compact evaluator를 실행하거나 재사용한다.
6. owner operating replay와 이전 날짜의 validated model scope가 맞는지 확인하고 compact funnel의 `economic_eligible`·`paired_comparable` 증가를 확인한다.
7. 단일 publisher가 machine·compact 결과를 family별 source/parent와 함께 다음 거래일 bundle에 발행하고 summary·checklist·full verifier가 같은 generation을 읽는지 확인한다.
8. 증가하지 않으면 최초 탈락 producer를 수리하고 관련 범위만 재검증한다. model·표본만 부족하면 `waiting_model_or_sample`로 이관한다.
9. 독립 holdout과 same-stage 적용 조건 전에는 incumbent carry를 정상 결과로 유지한다.

현재 체크리스트의 stable owner를 재사용한다.

- 구조 수리: `DirectFamilySourceRepairCompactAuxiliary`
- 메인 full evaluation·wrapper·publisher·full verifier: `MainMechanisticEntryPostcloseLoopRestore0920`
- PREOPEN·PID·자연 경제성: `KiwoomCommonHealthOpportunityCostAcceptance0917`

새 날짜별 task ID나 중복 OPEN owner를 만들지 않는다.

## 15. 완료 기준

### 구현 closure

- 지원 scope의 미래 `ENTER_NOW`가 pre-AI plan부터 paired evaluator까지 손실 없이 전달됨
- source/model이 준비되지 않은 입력에 provider 호출 0
- SOR·통합시장 경로가 route 문자열 때문에 제외되지 않음
- prior execution-model holdout과 candidate holdout 독립성이 코드·receipt로 검증됨
- 유효 입력에서 후보 실행→paired 계산→선정/보존→dated policy→consumer가 작동함
- candidate 0의 다섯 상태가 정확히 구분됨
- scoped verifier가 compact direct hash를 확인하고, full verifier가 별도로 full machine scope·noncompact refresh·machine/compact family source·wrapper 순서를 확인함
- compact 결손이 메인 기계평가를 생략하지 않고, compact finalize가 machine 결과를 소실시키지 않음
- exact 조합 proof 없이 machine·compact 두 후보가 동시에 적용되지 않음

### 경제성 closure

- 동일 자본·수량의 paired EV·원화 일별 순익·tail·노출·reserve·fill participation 산출
- 보수적 모델/stress/inference 비용 차감 ΔEV와 실제 순익 분리
- 독립 holdout 통과 시 해당 scope만 `validated_edge`
- 실패 시 기준 완화 없이 `valid_no_edge` 또는 정확한 대기/결손 상태

### 자연 OPEN

다음은 구현 완료 후에도 자연 증거가 생길 때까지 OPEN이다.

- 정상 PREOPEN·실제 PID 소비
- 신규 자연 eligible episode와 독립 holdout 누적
- 실제 적용 버전의 주문·체결·COMPLETED 비용 손익
- rolling/cumulative 순익·EV·tail·모델 오차
- 인과적 개선 판정

양수 후보나 실제 EV 개선은 완료 조건으로 강제하지 않는다. 유효 비교가 가능하도록 구조를 닫고, 양수 증거가 없으면 incumbent를 보존하는 것이 올바른 완료다.

## 16. 계획 단계 검증과 비실행 항목

이 계획 작성에서는 문서만 추가한다. 기존 계획·체크리스트·코드·wrapper·산출물·release selection을 수정하지 않는다. 구현, 장후 재생성, 배포, PREOPEN, PID 확인, provider 호출과 실제 주문은 수행하지 않는다.

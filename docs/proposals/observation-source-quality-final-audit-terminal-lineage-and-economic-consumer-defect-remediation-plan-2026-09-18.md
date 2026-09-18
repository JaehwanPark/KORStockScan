# Observation source quality 최종 감사·terminal lineage·경제성 소비 결함 보완계획

작성일: 2026-09-18 KST

상태: 후속 사용자가 Q0–Q5 구현·반복 리뷰/수정·검증·commit/push·배포 및 제한 재생성을 승인했다. [Owning review](../audit-reports/2026-09-18-observation-source-quality-final-lineage-review.md)에서 코드 closure와 원천/후행 소비/배포/자연 경제성을 분리한다. 병행 verbosity/AI decision quality 수리는 해당 세션 소유이며 이번 변경에 보존한다.

## 1. 목적과 우선순위

목표는 `observation_source_quality_audit`를 독립 EV 튜너로 확장하는 것이 아니라 **실제 판단→주문 결과→원천 품질→경제성 evaluator의 연결 결손을 해소**하는 것이다. 감사 통과·보고서 존재·결과 연결·모델 EV·실제 순익은 별도로 판정한다. Clean tuning 시작은 `2026-06-05T00:00:00+09:00`이며 이전 자료는 archive/audit 전용이다. Main-only/normal-only/post-fallback-deprecation 및 원 owner·venue/session·hard safety 경계를 보존한다.

구현 순서는 **정확한 원천/연결 확인(Q0) → 실제 terminal lineage 보완(Q1) → final 감사 재사용 보완(Q2) → 평가 역할별 소비 조건 보완(Q3) → unknown provenance 종결(Q4) → 제한 검증·마지막 소비 인계(Q5)**다. Q1/Q3이 EV 개선 탐색의 구조적 기반이며 성능은 이후다. Q2는 Q1 결과가 오래된 감사에 가려지지 않도록 같은 change set에서 닫는다.

원칙 owner는 [Plan Rebase §1–§8](../plan-korStockScanPerformanceOptimization.rebase.md), 실행 owner는 [현재 checklist](../checklists/2026-09-18-stage2-todo-checklist.md)의 `PostcloseSourceQualityGateReview0918`다. 기존 `CodeImprovementWorkorderReview0918`, `AutomationTriggerDecisionSummary0918`, `KiwoomCommonHealthOpportunityCostAcceptance0917`은 각 인계/자연 acceptance를 계속 소유한다. Q0–Q5는 구현 묶음이며 신규 native ID·별도 일정이 아니다.

최우선 성공 기준:

- 관측된 AI PASS의 제출/최종 차단/거절/미해결을 동일 evaluation/attempt의 원 증거로 분류한다. 새 평가로 기존 PASS가 덮이거나 제출 전 실패가 누락되지 않는다.
- 역사적 복구 불가능한 gap은 exact key·분모·null·수리 owner를 보존한다. 진단 수리 완료에 양수 EV·신규 체결을 요구하지 않는다.
- 감사의 입력 허용이 운영 완료나 비용 후 경제성 평가 승인으로 확장되지 않는다.
- 유효한 다른 scope와 BLOCK/RECHECK/VETO 반사실 연구가 unrelated PASS gap 때문에 함께 막히지 않는다.
- report→workorder/EV→tower/checklist→strict의 상태·source hash·원 평가일이 일치한다. 전체 native DONE·PID 소비·실제 이익 개선은 별도 증거 없이는 주장하지 않는다.

## 2. 현재 확인된 근거와 미확정 경계

확인 배포본: `609f3dbb09a2e398f2d573dd939dea3a3f85e945`. 구현 시작 전 현재 선택 배포본·remote와 병행 변경을 재확인한다. 이 SHA는 조사 기준이며 미래 배포 대상으로 고정하지 않는다.

| 확인 사항 | 사실·판단 |
| --- | --- |
| 다음 wrapper 단계 | verbosity 후 `observation_source_quality_audit --target-date TARGET_DATE --audit-phase final --write --print-summary`; trigger skip이면 기존 JSON/MD만 확인 |
| 9/17 실제 artifact | `audit_phase=preflight`, generated_at=9/17 23:17:18. 앞선 단계 중단으로 final까지 도달하지 못함 |
| Raw 감사 |337,300events/87stages, hard gap0/제외0, unknown28stages, reviewed unknown57stages. 둘은 중복 가능한 stage 집합이며 합산하지 않음 |
| 공용 validator 현재 확인 | exact-date/raw generation validation errors0, `tuning_input_allowed=true`. 최신 감사 구현으로 재계산한 final이라는 뜻은 아님 |
| Aggregate 재사용 | raw contract projection의 원 audited_at=9/17 20:50:24; 해당 preflight의 raw read0. machine/AI 소비까지 재사용됐다는 뜻은 아님 |
| 기계 평가 연결 |4,508건 중 정확 trace 연결4,507·미연결1. 평가 분모4,507=assessed3,341+source-invalid 제외747+feature 부족 제외419, unaccounted0 |
| AI/provider | screen4,578·provider 호출63의 request/prompt/outcome 연결 존재. Compact 현행 partition 호출21=KRX11+통합 애프터10 |
| AI PASS terminal |PASS4=제출0+최종 차단0+거절0+lineage gap4+pending0. 경제성 terminal 인정0; 실제 주문이 없었다고 입증된 것은 아님 |
| Gap 상세 | `lineage_gap_superseded_without_terminal`; 종목031330/272210/443670/950260, 통합 애프터 scope. 재평가로 terminal 없이 교체된 원천 연결 결손 |
| 현행 후행 지시 | `order_observation_source_quality_unknown_token_provenance_gap`가 workorder `implement_now`, runtime_apply=false로 소비됨 |
| 재사용 위험 | generic trigger는 파일 상태/mtime 중심. audit phase·감사 구현/소비 원천 generation을 직접 조건화하지 않음. 옛 receipt의 감사 코드 SHA는 조사 배포본과 다름 |

9/17에서 실제 잘못된 final skip이 발생했다는 증거는 없다. 해당 단계가 미도달한 사실과 재사용 계약의 결손을 구분한다. 특정 PID·broker 거절·실체결·guard 원인이었다고 추정하지 않는다. source-invalid/feature 부족1,166건 모두가 코드 버그라는 뜻도 아니다.

근거: [원 감사 JSON](../../data/report/observation_source_quality_audit/observation_source_quality_audit_2026-09-17.json), [원 감사 MD](../../data/report/observation_source_quality_audit/observation_source_quality_audit_2026-09-17.md), [현재 배포 선택](../../data/runtime/runtime_release_selection.json), [wrapper](../../deploy/run_threshold_cycle_postclose.sh), [감사](../../src/engine/observation_source_quality_audit.py), [공용 gate](../../src/engine/automation/source_quality_hard_gate.py). Canonical source는 병행 변경 중일 수 있으므로 구현 조사에서는 실제 선택 배포본과 함께 대조한다.

## 3. 코드 소유와 변경 경계

| 기존 owner | 필요한 보완 |
| --- | --- |
| `sniper_state_handlers.py` 및 실제 terminal을 생성하는 기존 entry owner | evaluation/attempt 원 identity의 전파, 기존 final guard/submit 결과의 누락·재평가 교체 분기 보완. 실제 결손 분기에 한정 |
| `buy_funnel_sentinel.py` | 원 identity 기반 PASS→terminal reconciliation, retry·late event·중복/상충 및 exact exclusion. 원 terminal 없이 분류 추정 금지 |
| `observation_source_quality_audit.py` | final 소비 원천 binding, raw aggregate/소비 검사 분리, source/decision/operating terminal/economics 상태의 명시적 표현 |
| `automation/source_quality_hard_gate.py` 및 실제 affected evaluator | 역할별 입력 허용 검증, source date/hash/partition/exclusion 전파. 기존 BOOL 하나로 승격하지 않음 |
| `automation/automation_chain_trigger_decision.py`, postclose wrapper | 이 감사 단계의 phase·구현·dependency binding을 재사용 조건에 반영. generic trigger 전체 재설계 금지 |
| 기존 workorder/EV/tower/checklist/strict owner | missing/stale/partial/excluded/ready 의미와 원 generation의 마지막 소비 확인 |
| 기존 테스트 | 해당 owner의 실제 경로를 사용하는 제한 회귀. 신규 framework/거대한 fixture 금지 |

새 root Python module·DB·ledger·service·report producer·별도 replay engine을 만들지 않는다. broker 주문 원장은 기존 signed registry를 유지한다. 출력은 기존 보고서·receipt·정책 구조를 확장하되 실제 consumer에 필요한 최소 필드만 추가하고 필요한 경우 기존 schema/version 관례를 따른다.

`pipeline_event_logger.py`/`pipeline_event_summary.py`는 verbosity 세션과 공용이다. 본 세션은 기본적으로 읽기만 한다. Q1의 실제 사건이 현재 lossless projection에서 누락되는 경우에만 기존 owner와 변경 범위를 대조하고 event population·hash 계약을 한 change set으로 정합하게 반영한다. 병행 코드를 덮거나 같은 compactor 수리를 중복 구현하지 않는다.

Kiwoom request/response parser·계좌/주문 call·FID·continuation/recovery 의미를 바꾸지 않는다. 필요성이 새로 확인되면 공식 Kiwoom reference gate를 적용하고 현재 허용 범위에서 판단한다. provenance 수리는 protocol 추정이나 guard 완화 근거가 아니다.

## 4. Q0 — 동일 원천에서 최초 연결 결손 확정

1. 현재 선택 release, canonical/worktree diff, 활성 wrapper/lock, 보고서 날짜/phase/hash와 병행 세션 소유 파일을 확인한다. 실행 중 원천/immutable snapshot을 교체하지 않는다.
2. 4개 gap evaluation key의 원 ledger와 machine trace를 기준으로 PASS 직후 마지막 증명 stage를 좁힌다. symbol/time 근접 매칭 대신 snapshot/promotion/evaluation key·attempt·order intent의 기존 identity를 사용한다.
3. 관련 source manifest, bounded compact projection, signed registry, terminal receipt를 대사한다. 재평가 전 early return·guard 차단·broker call 실패·늦은 결과·reader join 누락 중 원 증거가 있는 분기만 결함으로 확정한다. 일반 제출병목 taxonomy를 새로 만들지 않는다.
4. 실제 terminal이 존재하지만 reader가 놓친 경우 join을 수리한다. producer가 사건을 기록하지 않은 경우 미래 capture를 수리하고 과거 gap은 unrecoverable로 남긴다. 둘을 같은 recovered count로 집계하지 않는다.
5. 1개 machine→trace 미연결과 health companion 부재도 최초 producer/소비 경계를 확인한다. 원 경로상 생성 의무가 없는 companion까지 mandatory 결손으로 만들지 않는다.
6. stat-first/bounded reads를 사용한다. 대형/growing JSONL과 giant raw의 unrestricted scan·materialization을 금지한다. 기존 ledger/manifest도 필요한 section/keys만 확인한다. 조사에 불필요한 broad backfill은 하지 않는다.

산출: 각 gap의 exact key, 마지막 증명 stage, producer/reader 책임 파일, 복구 가능성, excluded role/partition, 다음 액션, closure test. 원 증거가 없으면 ETA=null이다.

## 5. Q1 — 기존 entry terminal capture와 reconciliation 보완

- 제출 전 기존 final guard의 모든 영향 분기를 읽고, 실제로 실행된 차단 결과에 동일 evaluation/attempt identity와 기존 guard reason을 기록한다. 수리 때문에 guard 판정/순서를 바꾸지 않는다.
- 정상 제출·명시 broker 거절·응답 불명확·예외를 구분한다. broker call attempted를 accepted submission으로 취급하지 않는다. 응답 없는 dispatch는 기존 pending/reconciliation 경로를 따르며 no-submit/순익0으로 바꾸지 않는다.
- broker intent/order mapping은 existing signed registry와 exact account/order/date/owner/route identity를 대조한다. 경제성 보고서에는 불필요한 계좌/민감 payload를 복제하지 않는다.
- 재평가/stock 상태 교체가 기존 PASS의 identity를 덮지 않게 실제 attempt context를 유지한다. 기존 runtime attempt/order lifecycle에 필요한 최소 context만 추가하며 전용 state machine/영구 원장을 만들지 않는다.
- retry는 별도 attempt로 보존하고 같은 evaluation의 terminal은 원 causal order로 정합화한다. late ACK/fill은 원 attempt로 연결하며 새 평가의 성과로 옮기지 않는다. 중복 terminal은 dedup, 서로 상충하면 해당 key만 fail closed/excluded 처리한다.
- telemetry capture/append 실패는 실제 주문/guard 처리 의미를 바꾸지 않는다. existing error/provenance로 source gap을 드러내며 누락된 기록을 terminal 성공으로 발급하지 않는다.
- `buy_funnel_sentinel`의 기존 conservation을 유지한다: `AI_PASS = submitted + final_guard_blocked + broker_rejected + lineage_gap + pending`. 분모를 줄여 difference0을 만들지 않는다. Size/leg parent/child의 원 분모도 보존한다.
- 실제 registry/order 결과를 찾지 못한 9/17 4건은 gap 상태를 유지한다. 미래 capture 회귀가 통과하면 코드 결함 수리는 종결할 수 있으며 과거 gap0이나 새 양수 EV를 완료 요건으로 요구하지 않는다.

Closure: 기존 실제 처리 분기의 제한 fixture에서 PASS→terminal identity가 보존되고 supersede/retry/late/conflict/불명확 dispatch가 위 계약대로 반영된다. 보고서 변경이 주문 호출 횟수·인자·guard·수량·provider를 바꾸지 않는다.

## 6. Q2 — final 감사와 aggregate 재사용 정합성

### 6.1 분리된 두 계산 경계

Raw contract aggregate는 기존 verified projection을 재사용한다. Final의 machine/AI/provider/funnel 검사와 별도 provenance를 둔다. Raw가 같아도 terminal/funnel/provider manifest가 달라지면 affected consumer 검사만 다시 수행한다. raw read0을 전체 검증 read0으로 표시하지 않는다.

재사용 key/receipt에는 target date, 감사/검증 구현 의미 hash, schema/contract version, 검증된 raw generation/content binding, 실제 machine/AI/provider/funnel dependency와 각 처리 cutoff를 결속한다. Existing native manifest/receipt가 검증된 immutable 또는 append-only 계약을 제공하는 경우만 대형 prefix 재사용을 허용한다. 파일 metadata만으로 in-place 정정 부재를 입증했다고 주장하지 않는다.

### 6.2 phase와 publication

- 같은 JSON 경로에 preflight/final을 쓰는 현행 caller는 유지한다. preflight receipt 존재만으로 final 완료를 발급하지 않는다.
- 요청 phase를 trigger에 전달하거나 감사의 pure reusable check를 기존 wrapper에서 호출한다. 선택은 실제 호출 구조에 맞는 더 작은 변경으로 확정한다. 모든 generic step에 새 검증 framework를 강제하지 않는다.
- 동일 원천에서 final을 완료할 때 검증된 raw aggregate를 재사용하고 최종 dependency 검증·final phase·실행 terminal을 새로 결속한다. 단순 phase 문자열 변경만으로 final을 발급하지 않는다.
- invalid/hash mismatch/코드 계약 변경/원천 교체/late terminal은 해당 날짜·역할의 invalidation 이유를 명시한다. 자동 전체 raw bootstrap 대신 기존 검증 projection 또는 필요한 bounded 입력을 사용한다. 없는 집계는 explicit blocker다.
- Report/receipt/MD를 기존 generation-safe publication 방식으로 정합하게 쓴다. 중간 crash/mixed generation에서 old PASS를 재사용하지 않는다. Failed resource/lock/CLI execution은 분석 PASS와 분리한다.
- 보고서의 warning/fail과 CLI 실행 성공을 구분한다. 기존 exit 계약은 실제 caller 호환성을 검토해 유지하고, strict/controller는 semantic fail을 성공 exit로 무시하지 않는다.

Closure: preflight만 존재하면 final receipt가 필요하고, 같은 final dependency는 bounded reusable, terminal dependency 변경은 consumer 검사 refresh, contract 변경/변조는 invalid이다. Unchanged 경로에서 giant raw 재독 없음을 검증한다.

## 7. Q3 — 역할별 경제성 소비 조건 보완

기존 보고서와 affected consumers에서 아래 네 의미를 명시한다. 새 이름은 실제 caller 대조 후 정하며 범용 상태 enum을 새로 만들지 않는다.

| 검증 의미 | 필요한 증거 | 허용하지 않는 해석 |
| --- | --- | --- |
| Source input allowed |exact date/schema/원 generation·격리 가능한 exclusion/필수 provenance | 전체 COMPLETE, 정책 승격, 순익 존재 |
| Decision CF measurable |기계/compact 원 partition·판정·독립 반사실 실행/exit/cost owner의 검증·gap key exclusion | BLOCK/VETO를 실제 주문 손익으로 합산 |
| Operational terminal reconciled |PASS 분모 conservation·exact submitted/guard/rejected/pending/gap | guard 차단/거절이 COMPLETED trade임 |
| Economic comparison eligible |평가 역할에 맞는 검증된 실행모델·동일 기회/자본·terminal/cost·미사용 holdout | 제출만 확인하고 EV 계산; missing을0/gross로 대체 |

1. 현행 `_machine_terminal_tuning_gate`는 submitted+guard-blocked+rejected를 terminal admitted로 계산한다. 이 값은 **운영 결과 연결**이며 그 자체가 비용 후 trade 경제성을 증명하지 않는다. 기존 `economic_tuning_input_allowed`를 소비하는 실제 callers를 찾아 오용을 수리한다. field rename이 필요하면 affected consumer/schema를 함께 변경하고 불필요 호환 wrapper를 남기지 않는다.
2. Real trade PnL은 main real owner·full/partial fill·venue/session·COMPLETED valid profit_rate·effective costs·exact version/lineage로만 인정한다. Pending/HELD/custody-censored/미확정 비용은 null이다.
3. Reject/final guard/no-fill의 결과 연결은 기회/자본 진단 또는 검증된 counterfactual owner에서만 사용한다. 실제 미체결 terminal과 flat/no-cost가 입증된 경우만 해당 arm의0을 허용하며 파일 부재로0을 만들지 않는다.
4. BLOCK/RECHECK/VETO 및 미진입 기회비용은 기존 decision CF evaluator를 유지한다. 전체 작업을 체결 실적 있을 때만 평가하는 방식으로 바꾸지 않는다. 모델/정책 holdout·cost·same-budget 계약은 해당 existing owner의 기준을 그대로 따른다.
5. Identifiable gap key/partition만 excluded로 전달하고 유효 다른 기회는 보존한다. 무표본/유효 empty/미성숙/구조결손/no-edge/no-policy-difference를 분리한다.
6. 삼성/저가주 튜너·entry/compact 경제 evaluator가 읽는 source date/hash/exclusion을 각각 확인한다. 필요한 reader만 수정하고 다른 세션의 AI decision quality evaluator를 중복 검증/구현하지 않는다.

Closure: source 허용·terminal 분모 보존이 true여도 cost/exit 없는 실제 EV는 null이고 승격 불가다. 유효 BLOCK/VETO CF partition은 무관한 PASS gap으로 전역 차단되지 않는다. 동일 고정 원천에서 후보선정/ΔEV를 새 구현이 추정으로 바꾸지 않는다.

## 8. Q4 — unknown provenance의 최소 수리와 종결

1. 기존28개 stage의 field별 count/rate와 producer를 기준으로 영향받는 source 역할을 좁힌다. 개별 warning 수치가 전체 hard block이라는 해석을 금지한다.
2. 원 증거가 있으면 provenance mapping을 보완한다. 없으면 `not_available`/`insufficient_sample` 등 기존 reviewed canonical label과 검토 이유를 사용한다. 단순 경고 숫자 감소를 위해 token을 지우거나 route를 추정하지 않는다.
3. 통합 route에서 관측되지 않은 actual execution venue, source-invalid 이전에 생성되지 않는 context 등 합법적 부재를 결함과 구분한다. 필드 요구는 실제 producer/평가 stage의 계약에 맞춘다.
4. 이미 source 수리가 된 항목은 해당 구현/계약 hash와 exact scope 재검증을 바인딩해 `already_implemented` 또는 자연 acceptance로 인계한다. 오래된 원천의 경고 자체를 반복 수정 이유로 사용하지 않는다.
5. 기존 `order_observation_source_quality_unknown_token_provenance_gap` ID를 유지한다. Workorder의 source hash·remaining fields·producer·closure test·disposition을 갱신하고 같은 gap을 매 refresh마다 신규 지시/AI 조회로 만들지 않는다.

Closure: 미해결 실제 결손은 지시/owner가 있고 정상 unavailable은 explicit reviewed 의미를 가진다. Unknown-only는 warning이고 hard 결손 제외 규칙을 임의 완화하지 않는다.

## 9. Q5 — 제한 검증·재리뷰·마지막 소비 인계

### 9.1 필수 회귀

기존 테스트 파일에서 필요한 case만 추가한다.

- PASS 이후 실제 guard block/accepted submit/reject/ambiguous response/exception 및 새 평가로의 supersede.
- Retry·late ACK/fill·중복/상충 terminal·parent/child 원 identity와 conservation.
- 역사적 source absent/unknown gap 유지; verified no-submit/no-fill과 미확정0 구분.
- Preflight→final, final reuse, raw aggregate reuse와 machine/funnel 변경에 따른 affected refresh.
- Schema/구현/원 generation/receipt 변조·mixed publication·failed execution의 old PASS 재사용 거절.
- 운영 terminal admitted와 완료 trade/cost 경제성의 분리, source pass지만 economic null.
- 유효 BLOCK/VETO CF와 unrelated PASS gap의 isolation; compact/legacy·real/sim/CF·venue/session partition 보존.
- Unknown-only warning→동일 native workorder 인계와 reviewed unavailable 의미.
- Source hash/exclusion/phase가 workorder·EV·tower·checklist·strict에서 동일하게 소비되는 통합 회귀.

기존 `test_buy_funnel_sentinel.py`, `test_observation_source_quality_audit.py`, `test_source_quality_hard_gate.py`, `test_automation_chain_trigger_decision.py` 및 변경된 entry/consumer/wrapper/summary 테스트 중 관련 subset을 선택한다. Compile, shell 변경 시 bash-n/contract test, diff-check, 문서 print-only parser를 수행한다. 불필요 broad trading/provider suite는 실행하지 않는다.

### 9.2 승인 후 제한 실행과 chain closure

이번 계획 작성에서는 실행하지 않는다. 후속 구현/배포/재생성 승인이 있을 때만 아래 절차를 적용한다.

1. 구현→리뷰→수정→재리뷰→targeted validation을 닫는다. 현재 selected release/active writer·원 snapshot·rollback 증거를 확인한다.
2. 원9/17 source를 보존하고 필요한 날짜의 sentinel section/audit와 직접 affected recommendation만 bounded 재생성한다. Existing reader가 bounded 갱신을 지원하지 않으면 그 결손을 명시하고 scoped support를 보완한다. 원 population 검증 없이 report 일부를 수동 재봉인해 전체 sentinel을 최신으로 발급하지 않는다. 미복구 과거 gap은 유지한다. Giant raw full rerun·provider/model 재호출·수동 raw 정정/삭제는 필요성과 별도 권한 없이 수행하지 않는다.
3. Audit 갱신 뒤 exact hash를 읽는 삼성/저가주·기타 affected 후보만 invalidation/re-intake한다. 이전 정책/holdout은 보존하고 동일 holdout을 새 검증으로 재사용하지 않는다. 정책 발행일과 평가일을 alias하지 않는다.
4. 기존 recommendation→workorder/EV→tower→체크리스트→strict `--require-summary-handoff`를 새 generation으로 확인한다. Verifier/controller 자체 hash는 summary input에서 제외한다.
5. 관련 변경에 따른 controller/finalization disposition을 기존 owner로 인계한다. 다른 선행 resource/source 실패가 남으면 whole native DONE=false다. 필요한 마지막 소비자를 미갱신한 상태로 chain closure를 선언하지 않는다.
6. 이 감사는 매매 정책을 생성하지 않는다. 후행 경제 evaluator가 새 유효 후보를 만들지 못하면 기존 정책/carry를 유지한다. 조기 PREOPEN·봇 재시작·실주문·provider/threshold/env/cap/hard guard 변경은 감사 수리의 부수 효과로 실행하지 않는다.

### 9.3 완료와 자연 acceptance

| 완료 축 | closure evidence |
| --- | --- |
| 코드 수리 |Q1–Q4 finding 수정·재리뷰·실제 경로 회귀 PASS, unresolved in-scope defect0 |
| 원천 결과 |gap별 recoverable/unrecoverable/isolated·분모·null와 원 generation |
| Final 감사 |requested phase와 dependency/구현/hash 결속, aggregate/consumer 계산 역할 분리 |
| 마지막 소비 |workorder/EV/tower/checklist/strict 새 generation·동일 의미·외부 blocker disposition |
| 배포 |승인된 immutable release 선택 receipt. 기존 PID와 새 소비는 별도 |
| 자연 성과 |신규 정상 PASS의 실제 terminal capture, 정규 PREOPEN/PID가 필요한 후행 정책은 해당 owner의 검증, version-bound 완료 비용/경제성 |

과거4건의 gap0·신규 양수 ΔEV·실제 주문 발생을 코드 closure 조건으로 강제하지 않는다. 반대로 code/release PASS를 경제성 성공으로 대신하지 않는다. 후속 미래 체결·성숙·미사용 holdout이 필요하면 기존 owner OPEN/ETA 미확정으로 남긴다.

## 10. 범위 제한·비용·rollback

- 먼저 existing manifests/projections/ledger section으로 결손을 좁힌다. 속도 개선을 위해 forensic depth를4개 gap/첫 결손 분기로 제한할 수 있지만 원 분모/cost/hash 검증을 샘플로 대체하지 않는다.
- 새 성능 guard·메모리 floor 완화·복잡한 캐시 framework를 만들지 않는다. 검증된 raw aggregate 재사용과 affected consumer refresh로만 중복 작업을 줄인다.
- 보호 대상: raw/signed orders/custody/fills/cost·원 model/holdout·selected/current 정책·PREOPEN/PID/rollback evidence. 이번 계획에 산출물 삭제는 없다.
- 잘못된 future source capture/consumer gate가 확인되면 기존 release/policy rollback 절차로 되돌린다. 감사 report의 미확정 경제성은 null/source-gap으로 유지하며 operator OFF/override 및 원 주문 상태를 복구 대상으로 덮지 않는다.
- 운영 문서/checklist의 관련 section과 wrapper 변경을 같은 change set에 반영한다. README/runbook/Rebase/prompt/AGENTS 전체 재작성은 하지 않는다.

## 11. 계획 문서 리뷰

기존 producer/terminal gate/trigger/reader·원 보고서를 대조했다. 초기 설명의 모호함을 보완해 `terminal admitted`를 COMPLETED trade 경제성과 분리하고, BLOCK/VETO 반사실 연구의 비체결 분모를 보존했다. Final 미도달 사실과 잘못된 skip 가능성을 분리하고, Q1 미래 수리와 역사적4건 복구를 별도 closure로 명시했다. 다른 세션의 verbosity/AI decision quality 작업을 중복 구현하지 않는 범위를 확정했다.

이번 턴 검증은 문서 링크/owner/권한·우선순위·diff 및 print-only parser에 한정한다. Trading tests/provider/보고서 재생성·외부 sync는 계획 수립에 필요하지 않아 생략한다.

## 12. 후속 승인 구현 종결

Q0–Q5 구현·반복 리뷰/보완·제한 회귀/재생성을 수행했다. 상세 code/final/마지막 소비/dated incumbent carry 및 외부 native blocker는 [Owning review](../audit-reports/2026-09-18-observation-source-quality-final-lineage-review.md#q0q5-구현-closure-및-제한-결과)를 따른다. 과거4 gap·미연결1·unknown 경고와 null 경제성을 보존하며 자연 terminal/PREOPEN/PID/비용 후 성과는 완료로 바꾸지 않는다.

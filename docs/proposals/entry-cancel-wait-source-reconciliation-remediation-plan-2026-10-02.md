# BUY 취소 대기 원천 대사·승계·의미감시 보완구현 계획

계획 작성일: 2026-10-02 KST. 구현 검증 종료일: 2026-10-03 KST. 원 분석일: 2026-10-02. 상태: 작업본 구현·추가 반복 리뷰·595개 표적 검증 완료, 실행 세대 수용 OPEN.
구현 근거: [반복 리뷰 및 검증 기록](../audits/entry-cancel-wait-source-reconciliation-implementation-review-2026-10-02.md).
실행 소유자: [10/6 인계 checklist](../checklists/2026-10-06-stage2-todo-checklist.md)의 `EntryCancelWaitSourceReconciliation1002`.
사용자 추가 요청으로 현재 장후 모니터링 작업본에 생산자·직접 소비자·의미감시·알림 보완을 구현하고 반복 리뷰·보완·회귀검증했다. 격리 코드 검증과 실제 새 장후 세대·배포/PID 수용은 구분한다.

## 1. 목적과 확인한 결함

당일 실제 제출 0건과 과거 주문의 대사 미완료를 각각 증명하고, 과거 결손을 0건 또는 대사 완료로 정상화하는 계산과 소비를 제거한다. 유효 무표본의 기존 정책 유지와 원천·집계·세대 모순을 의미감시와 조치 알림에서 구분한다.

| 번호 | 코드·원천 근거 | 보완 결과 |
| --- | --- | --- |
| F1 | [생산자](../../src/engine/automation/entry_cancel_wait_tuning.py)의 `_previous_state`는 상태의 내부 hash를 검사하지만 `source_counts`와 정상 `parents`에 있는 날짜만 원천 재검증한다. 미분류 주문만 남은 날짜는 둘 다 비어 검증에서 빠진다. | 승계한 이벤트와 미분류 항목의 날짜까지 검증하고, 미검증 원천을 경제성 상태에 채택하지 않는다. |
| F2 | 같은 생산자의 `build_report`는 과거 제출 이벤트를 승계하되 미분류 상태는 승계하지 않는다. `_unresolved_prior_custody`는 registry만 집계한다. | 정상 parent, 미분류 제출, registry 및 source-only custody의 합집합을 대사하고 당일·과거 상태를 분리한다. |
| F3 | [장후 의미감시](../../src/engine/error_detectors/artifact_freshness.py)는 기계·보조·handoff 검사에 집중하며 cancel wait 전용 검사가 없다. [알림 소비자](../../src/engine/notify_error_detection_admin.py)의 semantic stage 허용 목록에도 없다. | 기존 detector에 전용 의미 검사를 연결하고 조치 대상만 기존 알림 흐름으로 전달한다. |
| F4 | `verify_handoff`는 tower의 `entry_cancel_wait_economic_tuning`을 요구하지만 [실제 tower 생산자](../../src/engine/automation/tuning_performance_control_tower.py)는 이 필드를 발행하지 않는다. [다음 checklist 생산자](../../src/engine/build_next_stage2_checklist.py)는 이미 전용 block을 생성한다. | 실제 tower → checklist → strict 경로가 동일한 검증 projection을 소비하는 시험과 발행을 보완한다. |

10/2 21:27:55 보고서는 당일 제출·미분류·registry 미해결을 모두 0으로 표시한다. 실행 projection 293개/1,985,421 bytes의 해시, 당일 원본 pipeline·threshold 로그의 해당 stage 부재, registry hash chain을 읽기 전용으로 대조했다. EV 및 후보 선택은 null, 90/120/600/1200초 유지다.

9/30 보고서는 실제 제출 2건이 `single_owner_unregistered`이며 `actual_dispatch_or_parent_lineage_unclassified`다. 제출/취소 이벤트 8개는 승계되지만 정상 parent와 source count가 비어 있다. 이 상태를 넣은 격리 재현에서 과거 원천 검증 호출 0회, 오늘 `no_submitted_orders`·`unresolved_prior_custody_count=0`·경제성 blocker 없음이 확인됐다. 이는 실제 미체결 주문 2건이 지금도 열려 있다는 증거가 아니다. 제출 2건의 소유·최종 상태 대사가 미완료라는 증거다.

점검 후 장후 source-only 복구가 producer manifest를 교체했다. 최신 당일 projection도 0건이며 293개 source hash는 동일하지만 21:27 보고서와 producer manifest hash는 다르다. 현재 장후 복구 진행과 report generation 수용은 별도다. 기존 배포본의 관련 3개 suite 60 PASS는 재현한 결함의 회귀 coverage를 보증하지 않는다.

## 2. 분석 모집단과 원천 계약

| 원천 | 역할 | 결손 처리 |
| --- | --- | --- |
| `threshold_cycle/date=DATE/family=dynamic_entry_price_resolver/part-execution-*.jsonl` | `entry_cancel_wait_submission`, `order_leg_sent`의 실제 제출·frozen context·가격/수량·owner/부모 identity | bounded projection과 producer census의 count/identity/hash 불일치는 해당 날짜·항목의 source gap |
| 같은 날짜의 `family=entry_price_execution_quality` | 취소 요청·성공·실패와 시각 | 성공 응답만으로 최종 주문 대사를 합성하지 않음 |
| `pipeline_event_summaries/pipeline_event_producer_summary_DATE.jsonl` 및 manifest/raw ledger | 선언된 제출·취소 stage의 전체 보존·원천 세대 증명 | 봉인·날짜·stage/identity 계약 부재를 유효 empty로 바꾸지 않음 |
| `runtime/order_owner_registry.jsonl` | 해시 검증한 주문 소유·체결·최종 상태 | 미등록 단일 owner 제출도 과거 관측 ledger로 따로 보존; registry 부재를 주문 부재로 해석하지 않음 |
| 날짜별 과거 cancel-wait report의 economic state | 증거가 검증된 parent·미분류 제출·검증 날짜와 공백의 승계 | 기존 report의 자기 hash만으로 원천/소유 증명을 대신하지 않음 |
| `post_sell/post_sell_candidates_DATE.jsonl` | 실제 체결 주문의 정확 lineage·청산·비용 | 해당 체결 parent의 경제성만 null/결손; 당일 제출 0의 증명을 청산 부재로 무효화하지 않음 |
| native observation의 exact venue/session 호가·체결 | 대기시간 arm과 비용·자본 비교의 기존 입력 | 실제 모델·CF 비교의 기존 적격성 계약 유지 |
| 검증된 당일 bootstrap 및 cancel-wait policy | incumbent 값·scope/hash 보존 | 기본값, 준비 정책, PID 소비를 서로 구분 |

경제성 갱신은 현행 `policy_refresh_start_date`의 9/29 이후 적격 원천을 사용한다. 6/5 clean baseline 이후의 기존 실제 custody는 소유·안전 대사에만 남기며 이를 새 경제성 학습 창으로 확대하지 않는다. `history_scope_start`/`history_scope_end`를 공개하고 검증 범위 밖의 모든 과거 주문이 0이라고 주장하지 않는다.

`pre_submit_delay` 가격 경로 분석, 미제출 기회, Widget/Episode/manual, AVG_DOWN/PYRAMID를 이 취소 대기 경제성 모집단에 합치지 않는다. 순차 첫 leg는 실제 제출 census에 포함하되 `initial_quantity_bundle_timeout_schedule` 소유자로 유지해 cancel-wait 경제성 arm에서 제외한다. 새 실제 체결이나 양의 EV는 이번 진단 수리의 완료 조건이 아니다.

## 3. 보고서와 승계 ledger의 구체적 변경

### 3.1 기존 정책 schema를 보존하는 진단 확장

기존 `economic_schema=entry_cancel_wait_submitted_paired_v2`, runtime policy의 대기시간·scope 구조는 유지한다. report/state에 `reconciliation_contract_version=entry_cancel_wait_source_reconciliation_v1`을 추가한다. 새 field도 기존 state hash/report proof 및 input fingerprint에 포함한다. 기존 v2 report는 수정하지 않고 검증 후 다음 state로 변환한다.

새 대사·감시 projection의 metric 계약은 `metric_role=source_quality_gate`, `decision_authority=report_only`, `window_policy=exact_target_date_and_declared_historical_scope`, `sample_floor=one_verified_identity_or_sealed_valid_empty`, `primary_decision_metric=submission_identity_conservation_and_unresolved_source_counts`, `source_quality_gate=stable_bounded_owner_source_and_report_policy_generation`이다. `forbidden_uses`는 threshold/order/provider/bot 변경, CF의 실제 PnL 대체, 결측의 0 대체다. 원 producer의 비용 후 EV 정책 계약은 별도로 유지한다.

- `submission_census`는 `source_date`, `coverage_scope=target_date_main_initial_buy_submission`을 명시한다. 기존 `submitted_parent_count`, `unclassified_count`, `coverage_verified`는 당일 값이다. `zero_is_verified`는 당일 projection·registry·source quality·미분류 0을 모두 확인했을 때만 true이며 전체 경제성 상태 문자열에서 추론하지 않는다.
- `economic_state.submission_reconciliation` 한 곳에 날짜별 `source_bindings`, 제출 identity, 정상/미분류/응답불확실 항목, 결손 이유와 disposition을 보존한다. top-level `historical_reconciliation`은 이 ledger의 작은 검증 projection이며 독립 집계 원천으로 다시 만들지 않는다.
- 각 항목은 원 `source_date`, 원 이벤트 hash, stock/record/route/session, 실제 owner/account/order 또는 명시적 fallback identity, parent/child/context hash를 보존한다. 모호한 식별자가 추가되었다고 기존 항목을 삭제하지 않는다. consumer/알림에는 민감한 account/order 원문을 출력하지 않는다.
- 동일 registry intent 또는 정확 date/account/order/owner 결속이 증명될 때만 합친다. 날짜가 다른 같은 주문번호, 다른 account/owner/route, 재시도 child를 임의로 합치지 않는다. identity 보강 전후 key alias와 원천 hash를 유지한다.
- historical projection은 검증 범위, `required_dates`, `verified_dates`, `missing_dates`, `known_open_order_count`, `unclassified_submission_count`, `terminal_unverified_count`, `filled_cost_unresolved_count`, `coverage_verified`, `zero_is_verified`, blocker/owner/closure test를 제공한다.
- 기존 `unresolved_prior_custody_count`는 범위 전체가 검증된 경우에만 확정 정수를 제공한다. 대사 불능이면 null이며 `known_open_order_count` 등의 확인된 하한과 미분류 수를 함께 출력한다. 소비자가 null을 `0`으로 정규화하지 않는다.
- 정상 원천, 결손, 알려진 open custody, terminal 미검증, 체결 cost 미완료를 따로 집계한다. 취소 응답 success + filled 0만으로 `terminal_verified`를 만들지 않는다. 기존 신뢰 가능한 owner-issued terminal/cost receipt만 사용한다.

### 3.2 `_previous_state`와 legacy 변환

1. 검증 날짜를 `source_counts`, parent, `source_events.emitted_date`, 승계 reconciliation 항목, 원천 binding 날짜의 합집합으로 만든다. 내부 날짜 형식·scope·중복 conflict와 report/date/state through-date도 검사한다.
2. 모든 관련 날짜에서 bounded compact projection·producer census·원 이벤트 hash를 검증한다. 같은 날짜의 원천은 한 번 읽고 결과를 재사용한다. source event만 있는 날짜도 건너뛰지 않는다.
3. 새 ledger가 없는 legacy v2는 검증한 각 날짜의 원 이벤트와 durable registry로 `_parents`를 다시 실행해 미분류 identity와 이유를 복원한다. 기존 보고서의 `source_gap`을 기본 0으로 변환하지 않는다.
4. 원천 결손 시 검증되지 않은 row를 경제성 history에 채택하지 않는다. 검증 실패한 artifact path/hash/날짜와 기존 결손 참조는 report의 excluded/quarantined 진단으로 보존한다. 변환 실패 후 predecessor를 빈 dict로 만들면서 결손을 지우는 흐름을 제거한다.
5. 중간 거래일 report가 없다고 그 날의 제출 0을 만들어 넣지 않는다. 선언된 history 범위의 날짜는 기존 거래일 resolver와 봉인 원천으로 확인한다. missing day는 coverage false/unknown이며 보고서 없는 휴장일은 거래일 공백으로 오인하지 않는다.
6. 같은 원천 세대와 같은 identity의 검증 실패는 다음 실행에서도 보존한다. 새 증거가 없는 반복 재생으로 closed/excluded 결정을 바꾸지 않는다.

### 3.3 과거 custody 대사와 경제성 상태

`_unresolved_prior_custody`를 정상 parent + 미분류 실제 제출 + registry + 검증된 단일 owner source-only 항목의 합집합을 반환하는 구조로 바꾼다. private 함수의 기존 호출·시험도 함께 수정한다. 실제 open 수와 대사 미완료 수를 구분하며, 종료 조건은 항목별 terminal 증명과 체결된 경우의 정확 cost 증명이다.

| 당일 상태 | 과거 상태 | 계산/보고 결과 |
| --- | --- | --- |
| 제출 0, 당일 coverage 검증 | 선언한 과거 범위도 검증된 0 | 당일 `no_submitted_orders`, history `verified_empty`; EV null·incumbent carry |
| 제출 0, 당일 coverage 검증 | 미분류 제출·필수 source 결손 | 당일 zero 증명은 유지, history/economic comparison은 `source_gap`; 과거 미해결 확정 count null·변경 정책 없음 |
| 제출 0, 당일 coverage 검증 | 알려진 open/partial custody 또는 cost 미완료 | history `waiting_outcome`; 실제 pending 이유·분모 보존, EV null·carry |
| 당일 projection/registry/quality 결손 | 어떤 과거 상태든 | 당일 count null 또는 검증된 관측 하한, zero false; 필수 계약 결손 공개 |
| 순차 첫 leg만 제출 | 별도 timeout owner | 실제 제출 count >0, 경제성 대상 0·별도 owner 제외 수; `no_submitted_orders` 아님 |
| 유효 경제성 표본 있음 | 식별 가능한 다른 결손 cohort 존재 | 결손 cohort와 제외 수를 고정하고 유효 scope만 현행 계약으로 평가. 미해결 주문이 동일 자본 portfolio 분모에 섞여 격리 불능이면 그 비교를 차단 |

`evidence_summary`에 당일 상태와 history 상태를 별도 표기한다. `economic_source_gap`/`economic_evaluation.blocker`는 실제 과거 결손을 승계하며 `incumbent_preserved`는 정책 disposition이다. 무표본·결손·기존 값 유지 중 어느 것도 `measured_no_edge`/EV 0/대사 완료로 바꾸지 않는다. 전역 source 계약 불명 또는 격리 실패 외에는 다른 날짜·family 전체를 차단하지 않는다.

## 4. 공통 의미 검증과 직접 소비자

[기존 생산자 모듈](../../src/engine/automation/entry_cancel_wait_tuning.py)에 `validated_reconciliation_view`를 두고 작은 진단 projection을 반환한다. 새 engine root 모듈이나 별도 daemon/report producer를 만들지 않는다.

- 검증은 report/date/schema/contract version, state/report proof, 당일 census와 history ledger 분모 보존, null/0 의미, parent·미분류 identity 중복, policy disposition·scope·report proof 결속을 검사한다. bool을 count로 인정하지 않으며 음수·비정수·NaN·모순된 합계를 거부한다.
- 표본이 없으면 경제성 숫자는 null, 변경 후보 없음, incumbent 값/scope 그대로인지를 확인한다. 적법한 기존 scope 승계는 새 후보 검증과 구분한다.
- producer manifest/raw ledger digest, source binding, registry receipt와 native command/reuse generation을 검증한다. 공유 data root의 정상 symlink와 개별 source/report의 금지된 final symlink를 구분한다.
- 감시용 read-only 모드에서 `build_report`, replay, broker/provider/API, raw 전체 스캔, 원천 봉인/재구성, 보고서·정책 write를 호출하지 않는다. 이미 봉인된 receipt와 bounded report/ledger만 읽는다. 캐시 key는 target date·report/policy/ledger SHA·producer manifest 세대·관련 registry revision이다.
- 읽는 동안 파일/receipt 세대가 바뀌면 `unobservable/generation_in_transition`이다. 동일한 안정된 세대에서 report가 뒤처진 것은 `stale_generation`이며 최신 성공 receipt로 재사용하지 않는다. registry의 append-only 증가는 기존 verified tail의 조상 증명과 관련 order revision으로 해석하고 unrelated owner append를 일괄 손상으로 오인하지 않는다.

| 수정 대상 | 구체적인 변경 |
| --- | --- |
| `entry_cancel_wait_tuning.py`: `build_report`, `verify_report`, `prepare_policy`, `handoff_view`, `checklist_handoff`, `verify_handoff` | 새 ledger·semantic projection 검증, 일관된 이유와 분모 발행, 날짜/세대/cache 결속. 검증된 결손 + 적격 incumbent carry는 계약상 정상 결과이며 허위 zero/누락된 ledger는 검증 실패. |
| [runtime summary](../../src/engine/runtime_approval_summary.py) | cancel-wait 전용 projection을 소비해 daily empty/history gap/pending/carry를 구분한다. `_comparison_status`의 `not_applicable`로 결손을 숨기거나 `_first_nonempty`/기본값 처리로 null을 0으로 바꾸지 않는다. |
| [control tower](../../src/engine/automation/tuning_performance_control_tower.py) | 검증한 `handoff_view`를 `entry_cancel_wait_economic_tuning`으로 실제 발행하고 source generation receipt에 report/policy/reconciliation binding을 포함한다. 동일 report proof의 summary projection과 대사한다. |
| [summary handoff](../../src/engine/automation/postclose_summary_handoff.py), [다음 checklist](../../src/engine/build_next_stage2_checklist.py) | mandatory source 결속 및 단일 cancel-wait block의 day/history/count/null/정책 상태 일치 검사. repair actionable owner는 현행 stable ID로 표시한다. |
| [strict verifier](../../src/engine/verify_threshold_cycle_postclose_chain.py) | 기존 cancel-wait scope entrypoint가 공통 semantic validator와 실제 tower/checklist를 대사하게 한다. source gap 보고를 올바르게 보존한 carry와 generation/의미 계약 실패를 구분한다. |

기존 policy bytes를 소급 수정하지 않는다. 새 report proof로 발행하는 carry policy도 effective trading date·원 incumbent 값을 유지하고 검증한다. 준비/PREOPEN/PID 소비는 각각 별도 evidence다.

## 5. 의미감시기와 알림의 보완

### 5.1 장후 검사 소유자

[artifact_freshness.py](../../src/engine/error_detectors/artifact_freshness.py)에 `_entry_cancel_wait_result_semantics`를 추가하고 `ArtifactFreshnessDetector.check`의 `details.entry_cancel_wait_result_semantics`에 연결한다. 위 공통 projection을 사용해 다음을 각각 보여준다.

- execution: 정규 wrapper의 실제 `postclose_command_metrics_v1`·native reuse receipt·run identity·exit 상태. cancel-wait는 현재 독립 stage-terminal을 만들지 않으므로 존재하지 않는 stage receipt를 필수로 가정하지 않는다.
- source: 당일 projection와 과거 ledger의 coverage, 누락 날짜·identity·stable generation.
- reconciliation: 당일 count/zero, 과거 실제 open·미분류·terminal/cost 대사 결손, 각각의 범위와 nullable count.
- policy: incumbent carry/candidate, report-policy proof·source date·publication/effective date·scope 결속.
- consumer: 준비된 동일 세대의 summary/tower/checklist projection 일치. 후행 producer가 아직 실행 전이면 pending으로 표시하고 선행 계산의 의미 성공과 전체 DONE을 구분한다.

native command 시작 전/예약 전은 `not_yet_due`, 진행 중은 `pending`, 읽기 세대 전환은 `unobservable`이다. wrapper 성공 뒤 report 부재·날짜 오류·안정된 다른 세대는 결함이다. source date는 run identity에서 가져와 자정 이후에도 10/2를 유지하고 다음 적용일을 현재 날짜로 덮어쓰지 않는다.

### 5.2 조치 finding과 알림 계약

| finding code | 탐지 조건 | 알림/다음 조치 |
| --- | --- | --- |
| `cancel_wait_false_historical_zero` | 미분류·미검증 항목/날짜가 있는데 과거 zero true 또는 확정 미해결 0 | 조치 warning: 계산/승계 수리 owner, 해당 count와 비교 범위 표시 |
| `cancel_wait_history_source_binding_missing` | 승계 이벤트 날짜가 검증 ledger/binding에서 빠짐 또는 원 source hash 불일치 | 조치 warning: producer 원천 계약 보완. 해당 cohort 경제성 제외 |
| `cancel_wait_completed_report_generation_mismatch` | 성공 command/reuse generation과 안정된 report/policy/source 세대 불일치 | 조치 warning: 기존 복구 owner의 최소 재생성 경계. 전환 중에는 발송하지 않음 |
| `cancel_wait_census_semantics_invalid` | bool/음수/중복·분모 모순·null→0·순차 제외를 미제출로 표현 | 조치 warning: 계산/표시 수리 |
| `cancel_wait_consumer_projection_mismatch` | 소비 단계 완료 뒤 summary/tower/checklist가 다른 count/상태/proof 사용 | 조치 warning: 직접 소비 연결 수리·strict 실패 |
| `cancel_wait_candidate_without_reconciled_scope` | 미검증/미분류 주문이 같은 비교 scope/capital 분모에 있는데 새 후보 선정 | 조치 warning: 해당 후보 부적격. 기존 적격 carry 보존 |
| 정상 verified daily empty·기존 carry·표본 부족·known waiting outcome·올바르게 격리한 과거 source gap | 보고서가 범위·결손·owner를 정확하게 보존하고 후보 권한 없음 | 진단 상태로 공개. 반복 일반 장애 알림이나 매매 조치 요청 없음 |

`_semantic_alerts`에 cancel-wait stage/owner/closure test 분기를 추가한다. [notify_error_detection_admin.py](../../src/engine/notify_error_detection_admin.py)의 stage allowlist에 `entry_cancel_wait_tuning`을 연결하고 `_signature`/기존 중복·회복 처리에 원 source date·finding·scope·의미를 바꾸는 세대 identity를 사용한다. 생성시각 변경만으로 새 사고를 만들지 않는다. 다른 기계/보조 알림의 기존 허용 범위는 유지한다. 실제 발송 시험은 하지 않고 mock 전달·중복·회복을 검증한다.

### 5.3 장중 감시의 역할

[submission_bottleneck_monitor.py](../../src/engine/monitoring/submission_bottleneck_monitor.py)의 기존 `entry_execution_tuning_semantics`에 `entry_cancel_wait` 진단 projection을 붙인다. 장후 ledger를 다시 계산하거나 전체 과거 raw를 읽지 않는다. 마지막 검증 세대·당일 zero 범위·history gap·carry·bootstrap 선택/PID 미증명을 표시한다. 무거운 감시와 조치 알림의 주 소유자는 artifact freshness이며, 장중 projection이 동일 사건을 중복 발송하지 않게 한다. 과거 성공 report를 오늘 무제출 증거로 재사용하지 않는다.

## 6. 구현 순서와 파일 위치

| 단계 | 범위 | 완료 조건 |
| --- | --- | --- |
| P0 | 기존 `test_entry_cancel_wait_tuning.py`에 재현 fixture 추가 | 9/30 두 제출/8 events + 정상 parent/count 없음 + 10/2 verified empty에서 현행 false historical zero와 날짜 검증 누락을 실패 시험으로 고정 |
| P1 | 기존 producer의 source 날짜 검증·ledger·legacy 변환·custody union·cache proof | 미분류 두 건과 source gap 승계, 당일 zero 독립 유지, malformed/missing/변경 세대 fail-closed, idempotent count/hash |
| P2 | 같은 모듈의 공통 의미 validator + summary/tower/checklist/strict | 실제 producer 출력과 모든 직접 소비자가 같은 분모·상태·proof를 사용. tower 누락 경로 회귀 포함 |
| P3 | 기존 artifact detector·장중 projection·알림 filter/signature | false zero·누락 binding·stable stale·후행 불일치 탐지, 정상 carry/전환 중 오탐 없음, mock 조치 알림 도달 |
| P4 | self review → 추가 보완 → 재리뷰 → 영향 회귀·고정 fixture 성능 | 아래 계약 모두 통과. 새 실제 주문/경제성 표본 요구 없음 |
| P5 | 승인된 후속 범위에서만 정확 source generation 수용 | 실행 중 wrapper 종료/세대 소유권 확인 후 최소 producer→consumer→strict 재생성. 실제 적용/PID·경제성은 별도 |

Python 구현과 시험은 위 기존 role 모듈/시험을 사용한다. 새 `src/engine` root 모듈·daemon·cron·API 호출·관측 축을 만들지 않는다. 다른 작업트리 변경, 실행 중 immutable release, 봉인된 과거 report는 그대로 보존한다.

## 7. 회귀시험과 검증 명령

| 시험 | 핵심 기대 |
| --- | --- |
| 역사 미분류만 존재 | 원천 날짜 검증 호출 발생, 두 identity 보존, historical zero false·확정 count null·경제성 source gap |
| 정상 당일 empty + 검증 과거 empty | 당일/과거 zero true, EV null·incumbent carry, 조치 알림 없음 |
| ledger 없는 legacy v2 | 원 source 재검증으로 변환; 자기 hash 재봉인만으로 변조 source 채택 불가 |
| source event 날짜만 존재/중간 거래일 결손 | 모든 필요한 날짜 대사, missing day를 0으로 보충하지 않음; 휴장일 오탐 없음 |
| alias·중복·다른 날짜/account/owner의 같은 주문번호 | 정확 결속일 때만 중복 제거, count/identity 보존, conflict 격리 |
| registry 미등록/response uncertain/순차 첫 leg | 실제 제출·모호한 dispatch·경제성 제외 owner 구분, uncertain을 verified zero로 만들지 않음 |
| 취소 success/filled 0, terminal proof 없음 | terminal 미검증으로 유지. 응답만으로 custody 종료 합성 없음 |
| full/partial fill terminal, 정확 cost 부재/다음 날 도착 | 해당 항목의 pending→증거 기반 해결. 다른 scope/날짜의 cost receipt 대입 불가 |
| source 결손 cohort + 유효 scope | 식별 가능한 row/cohort 격리, 동일 capital 분모 격리 불가 시 해당 비교 차단 |
| bool/음수/count 합계/NaN/null·0 모순 | 공통 validator·감시·strict 모두 거부, missing EV는 null |
| raw/manifest/registry 및 읽기 전환 | stable stale와 generation-in-transition 분리; unrelated registry append 오탐 없음 |
| 성공 command의 report 부재·기존 실패 run/reuse | 현재 run/원 source date/결과 hash만 수용, exit 0만으로 완료 추론 없음 |
| 실제 tower→checklist→strict | fixture에서 tower 필드를 직접 수동 주입하지 않고 실제 tower 생산자를 실행해 누락·변조·중복 block 탐지 |
| detector→notification filter→signature | mock에서 조치 warning 전달, 정상 carry/미도래/전환 중 무알림, 동일 사고 중복 억제·회복 뒤 재발 탐지 |
| legacy 감시/장중 표시/자정 경계 | 새 계약 이전 artifact를 소급 손상 판정하지 않고 legacy 미검증 표시, source date와 next effective date 유지 |

구현 검증은 아래 suite를 영향 범위에 맞게 묶어 실행한다. Python 실행은 project `.venv`를 사용한다.

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_entry_cancel_wait_tuning.py src/tests/test_entry_cancel_wait_runtime.py src/tests/test_entry_cancel_wait_attribution.py src/tests/test_runtime_approval_summary.py src/tests/test_submission_bottleneck_monitor.py
PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_error_detector_artifact_freshness.py src/tests/test_notify_error_detection_admin.py src/tests/test_tuning_performance_control_tower.py src/tests/test_build_next_stage2_checklist.py src/tests/test_postclose_summary_handoff.py src/tests/test_verify_threshold_cycle_postclose_chain.py
git diff --check
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500
```

변경한 Python에는 개별 `py_compile`을 실행한다. wrapper를 실제 수정할 때만 `bash -n`/관련 wrapper 계약 시험 및 운영 문서 현행화를 추가한다. 현 계획은 cron/wrapper 변경을 요구하지 않는다. 현재 운영 source를 pytest fixture로 직접 쓰지 않고 작은 비식별 고정 입력을 사용하며 logger/notification은 격리한다.

고정 fixture에서 당일 empty·미분류 과거·정상/partial/uncertain 혼합을 각각 3회 비교한다. 입력 SHA·row/identity·후보 범위는 같아야 하며 날짜별 source는 호출당 한 번 읽는다. 감시가 full raw/replay/build_report/API/write를 호출하면 시험 실패다. wall/CPU/RSS·읽은 bytes를 기록하고 bounded receipt 규모에 선형인지를 확인한다. 신규 raw 재스캔이나 반복 history 재계산으로 시간을 줄였다고 주장하지 않는다.

## 8. 수용·원천 결손 종료·운영 경계

코드 수용은 F1~F4와 의미감시/알림 누락의 회귀, validator/실제 직접 소비 parity, 원천 세대·count/hash 보존, targeted validation으로 닫는다. 알려진 원천 손실을 report에 올바르게 남기는 것은 코드 결함 0 수용과 양립한다. 이를 역사 대사 완료·새 수익으로 표시하지 않는다.

자연 수용은 10/2 당일 무제출과 9/30 두 제출의 대사 미완료를 동시에 표시한 새 generation, 기존 90/120/600/1200 및 scope carry, EV null, 직접 summary/tower/checklist와 detector projection 동일성으로 확인한다. 정확한 terminal/cost 원천이 실제 있으면 그 항목만 해결하고, 없으면 `blocked`/`historical_unrecoverable`과 artifact/owner/closure test를 남긴다. 동일 결손 세대를 반복 재생하거나 현재 계좌 상태로 과거 terminal/체결/비용을 합성하지 않는다.

현재 진행 중인 장후 recovery의 command/selector/정책/준비본을 이 문서로 교체하지 않는다. 구현·리뷰 gate 통과 후 현재 사용자가 허용한 후속 범위를 실제 run owner와 대조해 최소 재생성 또는 다음 정규 실행을 선택한다. 배포/재기동은 이 계획 요청 자체에서 실행하지 않으며 앞선 다른 작업의 승인으로 임의 확장하지 않는다. 다음 거래일 10/6 준비/PREOPEN/실제 PID 소비는 각각 별도 수용이다.

실행이 다음 날짜로 넘어가면 source date 10/2·stable ID·위 acceptance/history를 보존해 현행 daily checklist로 한 번 이전한다. 이미 완료된 기계/보조 의미감시 owner를 일반적으로 재개하지 않고 이번에 새로 확인한 cancel-wait 결함만 이 owner가 맡는다.

## 9. 계획 리뷰 및 현 상태

계획 리뷰에서 registry만 보는 과거 0 판정, 이벤트 날짜만 남은 predecessor의 검증 누락, 기존 generic 상태의 `not_applicable` 축약, 실제 tower 전용 필드 누락, cancel-wait semantic stage의 notification filter 누락을 반영했다. 존재하지 않는 cancel-wait stage terminal을 요구하는 안과 전체 raw를 감시 주기마다 읽는 안은 채택하지 않았다.

계획 작성은 문서/link·단일 OPEN owner·authority·diff·print-only parser로 검증한다. 구현/pytest/보고서 재생성/실제 알림/배포/재기동/외부 sync는 이 계획 단계에서 실행하지 않는다. 문서-only 검증 결과는 이번 결과 보고에 기록하며 운영 보고서의 기존 숫자와 성공/실패 이력은 수정하지 않는다.

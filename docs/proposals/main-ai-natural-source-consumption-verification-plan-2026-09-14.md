# #76·#82 / #11·#74 Main AI 자연 원천 전수 소비 검증 구현안

작성: `2026-09-14 KST`

상태: **구현 계획**. 이 문서는 코드 수정, 장후 producer 실행, Provider 호출, 정책 발행, 배포 또는 매매 process 재기동 receipt가 아니다.

## 1. 결론

새 collector를 만들지 않는다. 현재 runtime은 AI 호출 전에 모든 기계 `ENTER_NOW / RECHECK / BLOCK` 판정을 `mechanistic_entry_observation_v1`으로 보존하고, 실제 AI 판단은 별도 `ai_decision_trace_v1`에 기록한다. 필요한 보완은 다음 세 가지다.

1. #11/#74 `observation_source_quality_audit`가 현재 `pipeline_events`뿐 아니라 기존 `ai_decision_payloads`, `ai_decision_trace`, `ai_decision_requests`, `ai_decision_prompts`, `ai_decision_outcomes`의 **전수·불변 generation·행 보존식**을 감사한다.
2. #76 `ai_decision_quality`가 기계 평가 모집단과 실제 AI screen 모집단을 서로 다른 named denominator로 materialize하고, #82가 그 manifest와 같은 generation만 소비한다.
3. #82 `ai_action_outcome_calibration`과 final verifier가 모든 기계 평가를 action·선정 이유·정책 bundle·micro 창·후행 outcome의 첫 결손까지 상호배타적으로 분류한다. 유효 사례만 남기고 탈락 행을 조용히 버리지 않는다.

기존 [기계 타점·AI PASS/VETO 계약](./entry-prompt-balanced-adjudication-design-review-plan-2026-09-13.md#16-기계-타점-선정ai-passveto-역할-정정)과 [판정 시점 기반 장후 학습 계획](./entry-prompt-balanced-adjudication-design-review-plan-2026-09-13.md#20-판정-시점후속-경로-기반-장후-학습과-다음-장전-정책--914-구현계획)은 유지한다. 이번 작업은 그 원천의 전수 소비·감사 경계를 닫는 보완이다.

## 2. 현재 구현과 확인된 결손

### 2.1 이미 구현된 수집·소비

| Owner | 현재 동작 | 재사용 범위 |
| --- | --- | --- |
| `src/engine/scalping/ai_decision_trace.py` | `capture_machine_observation`이 provider 호출 전 기계 판정과 exact payload/evidence/assessment를 기존 payload archive에 저장 | 새 collector 없이 그대로 사용 |
| `src/engine/ai_engine_openai.py` | 기계 non-entry는 Provider를 호출하지 않고 `mechanistic_pre_adjudication` trace를 남기며, `ENTER_NOW`만 AI PASS/VETO screen으로 전달 | 현행 runtime action·호출 정책 유지 |
| `src/engine/scalping/ai_decision_quality.py` (#76) | 실제 AI trace/request/outcome을 materialize하고 기존 경로 label을 생성 | 공통 outcome labeler와 exact source 계약 재사용 |
| `src/engine/scalping/ai_action_outcome_calibration.py` (#82) | `load_machine_observation_rows`와 `machine_decision_case_table`이 machine-only capture를 읽어 후행 경로를 평가 | 기존 loader/case table을 보존식 중심으로 확장 |
| `src/engine/observation_source_quality_audit.py` (#11/#74) | `pipeline_events`의 schema·행 결손·generation 안정성을 감사 | auxiliary AI 원천 감사 section 추가 |
| `src/engine/verify_threshold_cycle_postclose_chain.py` | #82 case table과 optimizer handoff의 일부 count/authority 계약 검증 | 전수 digest·분모·scope·#11/#74 hash 연결 추가 |

### 2.2 오늘 자연 원천의 비종결 사전 census

`2026-09-14T14:52:36+09:00` 읽기 전용 streaming census는 다음과 같다. 장중 writer가 계속 append 중이므로 이는 terminal receipt가 아니라 구현·검증 fixture의 하한이다.

| 원천/분모 | 관측값 |
| --- | ---: |
| `mechanistic_entry_observation_v1` | 2,744 |
| 기계 `BLOCK / RECHECK / ENTER_NOW` | 1,645 / 1,070 / 29 |
| 기계 scope `KRX regular / PREMARKET_KRX_LIKE` | 2,742 / 2 |
| `entry_screen` trace의 `mechanistic_pre_adjudication`, provider 미호출 | 2,715 |
| `entry_screen` trace의 `input_preflight_blocked`, provider 미호출 | 512 |
| 실제 provider 시도 `live / timeout` | 39 / 6 |

현재 기계 판정 보존식 `2,744 = 1,645 + 1,070 + 29`와 non-entry 보존식 `2,715 = 1,645 + 1,070`은 닫힌다. 그러나 `entry_screen` 전체에는 기계 capture와 일대일이 아닌 preflight·legacy/별도 경로도 포함되므로 `2,715 + 512 + 45`를 기계 평가 2,744와 직접 비교할 수 없다. exact snapshot/bundle/action join을 거친 뒤에만 `ENTER_NOW`의 AI screen 소비 여부를 판정해야 한다.

같은 시각 #11 수동 audit는 writer가 움직이는 동안 `generation_stable=false`, `blocked_reason=source_quality_raw_changed_during_audit`였다. 이는 장후 최종 #74 성공 근거가 아니며, 장중 원천을 삭제·격리하거나 현재 수치를 terminal로 동결할 이유도 아니다.

### 2.3 구체적인 계약 결손

1. #11/#74는 같은 `observation_source_quality_audit`이지만 현재 직접 source는 `pipeline_events` 하나다. #76 및 actual-call provenance가 사용하는 다섯 AI archive의 누락·변조·append 경계는 #74가 독립적으로 닫지 않는다.
2. #82 loader는 invalid/hash·cost·path·unsupported scope 행을 census counter에 더한 뒤 유효 row에서 제외한다. 이 counter들은 상호배타적 최종 disposition이 아니어서 `raw = valid + excluded + pending` 보존식을 verifier가 재현할 수 없다.
3. `machine_decision_case_table.rows`는 최근 200건만 내보낸다. 전체 count map은 검사하지만 전체 case identity/content digest와 scope별 보존식이 없다.
4. case row에는 action·reason·hierarchy·적용 threshold가 있지만 compact micro-window receipt가 직접 투영되지 않는다. 원 evidence를 다시 펼치지 않으면 창 version/status/hash/route/epoch와 refill·trade backing을 대사하기 어렵다.
5. AI join은 snapshot/time을 사용하지만, 정책 학습에서 action/bundle이 다른 단일 snapshot fallback을 허용할 수 있다. 현행 자연 자료에서도 `ENTER_NOW` 일부가 exact action+bundle join에서 벗어날 가능성을 별도 gap으로 보존해야 한다.
6. 분석 artifact의 `actual_order_submitted=false`는 “이 분석기가 주문하지 않음”을 뜻한다. 원 lifecycle의 실제 제출 여부는 `observed_actual_order_submitted`다. 이름과 분모를 분리하지 않으면 무제출 분석행을 실제 제출 0으로 오해할 수 있다.

## 3. 목표 데이터 흐름

```text
기존 runtime capture
  ├─ ai_decision_payloads: machine evaluation 전수
  ├─ ai_decision_trace: AI 미호출/실제 호출/결과 전수
  └─ requests/prompts/outcomes: actual-call envelope·prompt·pending outcome
          │
          ▼
#11 preflight: pipeline + 다섯 AI raw generation/schema/hash/authority/exclusion
          │ same source generation/hash
          ▼
#76 materialization
  ├─ machine_evaluation_population
  ├─ ai_screen_population
  └─ outcome_materialization_population
          │ exact manifest/hash
          ▼
#74 final raw/source audit
          │ final generation/hash
          ▼
#82 calibration
  ├─ machine decision case table
  ├─ actual AI screen attribution
  └─ scope/action/micro/outcome first-gap ledger
          │
          ▼
optimizer handoff → final verifier → tower/checklist
```

#11은 실행 전 source contract를 고정하고, #74는 #82 직전에 같은 raw generation이 소비 가능한지 재검사한다. 둘 사이 원천이 달라지면 #76 결과를 성공으로 유지하지 않고 **변경된 최초 source부터 Provider 호출 없이** #76→#74→#82를 한 번 다시 닫는다. #82 이후 최종 hash 대사는 verifier가 소유한다.

## 4. 분모와 보존식

### 4.1 서로 합치지 않을 세 모집단

| 모집단 | 단위 | 포함 | 금지 |
| --- | --- | --- | --- |
| `machine_evaluation_population` | `target_date × evaluation_attempt_id × snapshot_id × venue × session × machine_bundle_sha256` | AI 호출 여부와 무관한 모든 기계 판정 | provider-called 행만을 기계 전체 분모로 사용 |
| `ai_screen_population` | 위 machine identity에 결속된 canonical entry-screen decision | 기계 `ENTER_NOW` 뒤 실제 호출, fail-closed, 명시적 재사용 결과 | `BLOCK/RECHECK` 미호출을 AI 실패·WAIT 정답으로 변환 |
| `provider_attempt_population` | `decision_trace_id/request_id` | 실제 provider 송신·timeout·parse/schema terminal | retry/attempt 수를 고유 machine 기회 수로 사용 |

`ai_screen_population`과 `provider_attempt_population`도 같지 않다. 한 machine evaluation에 bounded retry가 있을 수 있고, cache/validated reuse가 있으면 새 Provider 호출 없이 screen 결과가 존재할 수 있다. 따라서 “AI 판단 소비”와 “외부 Provider 호출”을 별도 지표로 둔다.

### 4.2 필수 보존식

아래 count는 전체와 `effective_venue × session_bucket × machine_action × machine_bundle_sha256`별로 모두 닫는다.

```text
machine_raw_total
  = machine_valid_total
  + machine_invalid_hash_or_authority_total
  + machine_duplicate_conflict_total

machine_valid_total
  = BLOCK + RECHECK + ENTER_NOW

machine_valid_total
  = evaluable_outcome
  + maturity_pending_or_right_censored
  + exact_outcome_join_gap
  + cost_contract_gap
  + micro_contract_gap
  + unsupported_scope
  + explicitly_excluded_other

ENTER_NOW
  = ai_screen_exact_joined
  + ai_screen_missing
  + ai_screen_ambiguous_or_conflicting

ai_screen_exact_joined
  = decision_usable_pass
  + decision_usable_veto
  + bounded_caution_or_insufficient
  + provider_or_transport_failure
  + response_or_schema_invalid
  + explicit_reuse_without_new_provider_call

BLOCK + RECHECK
  = expected_machine_nonentry_no_provider
  + unexpected_ai_call
  + nonentry_trace_gap_or_conflict
```

모든 행은 마지막 식의 상호배타 `final_disposition` 하나만 가진다. 진단 counter는 중복 집계할 수 있지만 `conservation_counts`에는 사용하지 않는다. `unclassified=0`, 동일 identity의 서로 다른 action/bundle 충돌 `0`, cross-date/cross-scope join `0`이 필수다.

한 행에 결손이 여러 개면 최초 결손 우선순위를 `raw integrity/authority → identity·duplicate conflict → supported scope → policy/action/micro contract → AI screen join → outcome route/path → maturity → cost/realized reconciliation → evaluable`로 고정한다. 뒤 단계의 추가 결손은 `secondary_reasons`에만 기록한다. 이렇게 해야 cost와 path가 동시에 없는 한 행을 두 번 제외하지 않는다.

## 5. 행·join 계약

### 5.1 기계 판정 필수 필드

| 축 | 필수 필드/검사 |
| --- | --- |
| identity | `captured_at`, `evaluation_attempt_id`, `snapshot_id`, `stock_code`, `effective_venue`, `session_bucket` |
| action | `assessment.action`, `assessment.reason`, `assessment.primary_decision_owner` |
| selection | `hierarchy_selection.level/rule_id/reason`, `applied_thresholds`, `liquidity_inputs` |
| policy | `bundle_sha256`, `assessment.policy_version`, 선택 rule의 parent/source hash |
| micro | `mechanistic_context.micro_window.contract`, feature version, window start/checkpoint/horizon, source-quality status, route/item/epoch/sequence, `window_source_sha256` |
| authority | capture 자체 `provider_called=false`, `runtime_effect=false`, `allowed_runtime_apply=false`, `actual_order_submitted=false`, `broker_order_forbidden=true` |
| integrity | `machine_observation_sha256` 재계산 일치, redaction/regular-file/dual plain-gzip conflict 검사 |

micro 창은 raw depth 전체를 case table에 복사하지 않는다. version/status/hash, completeness, depletion velocity, BUY trade-backed ratio, refill ratio/half-life, bid/rebound 상태와 gap reason만 compact receipt로 투영한다. `unavailable`은 0으로 보간하지 않고 `micro_contract_gap|not_applicable_parent_policy`를 구분한다.

### 5.2 AI screen 결속

우선순위는 다음과 같다.

1. 같은 `target_date/evaluation_attempt_id/snapshot_id/stock_code/venue/session`.
2. `machine_bundle_sha256`와 `entry_mechanistic_action` 일치.
3. canonical final screen trace와 그 bounded provider attempts를 `decision_trace_id/request_id`로 결속.
4. 허용 시간차는 보조 검증일 뿐 identity를 대체하지 않는다.

action/bundle이 다른 단일 snapshot을 정책 학습용 exact join으로 승격하지 않는다. 과거 호환상 fallback이 필요하면 `diagnostic_fallback_only`, `policy_learning_eligible=false`로 남긴다. 일반 symbol+근접시각 join, 다른 session/venue, 다른 promotion wave, 현재값 backfill은 금지한다.

### 5.3 후행 outcome 결속

기존 #76 action-neutral labeler를 재사용해 다음을 분리한다.

- 판단시각 executable ask 기준 30/60/180/300초와 기존 1/3/5/10/20/30/60분 진단 경로
- target/adverse first-hit, 목표 전 MAE·횡보/underwater, 비용 후 `+0.10%` 도달
- 실제 submit → full/partial fill → confirmed unfilled/cancel → pending/right-censored → terminal
- 실제 `COMPLETED + valid cost/PnL`과 고정 exit counterfactual

실제 제출은 `source_observed_actual_order_submitted`처럼 명시해 분석기의 no-order authority 필드와 분리한다. partial/HELD/right-censored/비용 결손은 0원이나 completed로 바꾸지 않는다.

## 6. 구현 작업 패키지

### P0 — 현행 generation과 owner 동결

- postclose 실행 snapshot의 release/commit, target date, `pipeline_events`와 다섯 AI raw path/generation을 기록한다.
- 장중 writer가 살아 있으면 `waiting_active_writer`; #74 terminal 성공으로 보지 않는다.
- 기존 #11 preflight와 #74 final의 역할을 wrapper argument로 명시한다. 제안 CLI는 `--audit-phase preflight|final`이며 기존 단독 실행의 기본값은 호환되게 유지한다.
- 오늘의 자연 source가 닫히기 전 새 코드를 active wrapper에 끼워 넣지 않는다.

### P1 — #11/#74 auxiliary 원천 감사

수정 위치는 기존 `src/engine/observation_source_quality_audit.py`와 wrapper/test다. 새 audit service를 만들지 않는다.

- 다섯 AI archive를 streaming 1회씩 읽고 검사 전후 device/inode/size/mtime, logical SHA-256, nonempty/invalid JSON count를 기록한다. request/prompt/payload/trace/outcome의 canonical ID·저장 hash 보존식도 actual-call lane에서 검사한다.
- `mechanistic_entry_observation_v1`와 `ai_decision_trace_v1/entry_screen`만 명시 schema registry로 분류한다. 다른 endpoint payload/trace는 전체 file 보존식에는 남기되 기계 entry 분모에 섞지 않는다.
- identifiable invalid row는 raw를 수정하지 않고 hash-bound exclusion manifest에 identity/reason을 기록한다. source 전체 차단은 file missing/invalid, generation 불안정, identity 충돌의 격리 실패, unclassifiable high-volume loss에 한정한다.
- companion 위치는 기존 owner 아래 `data/source_quality/ai_natural_source_consumption/<target_date>/<source_generation_digest>.json`으로 제한하고 원자 publish한다. 이는 report producer나 새 원천이 아니라 #11/#74의 재현 가능한 source/exclusion manifest다.
- preflight report에는 `machine_ai_source_preflight`, final report에는 `machine_ai_source_final_audit`와 preflight source digest 대조를 남긴다.
- `pipeline_events`의 기존 `raw_row_exclusion` 계약은 변경하지 않는다. AI archive exclusion을 같은 raw mutation 경로로 오용하지 않는다.

### P2 — #76 이중 materialization manifest

기존 `src/engine/scalping/ai_decision_quality.py` artifact에 compact `machine_ai_natural_source_consumption` section을 추가한다.

- #11이 고정한 raw generation/hash와 exclusion manifest를 입력으로 받는다.
- `machine_evaluation_population`, `ai_screen_population`, `provider_attempt_population`을 별도 count/digest/scope map으로 출력한다.
- outcome label 대상이 아닌 정상 `BLOCK/RECHECK`도 “미사용”으로 버리지 않고 `expected_machine_nonentry_no_provider`로 보존한다.
- AI actual-call materialization은 기존 provider/request/response/outcome 경로를 유지한다. machine-only capture로 가짜 request, response, WAIT label을 만들지 않는다.
- 전체 identity의 canonical sorted digest와 per-scope digest를 생성한다. report row sample은 제한할 수 있지만 full population digest/count는 제한하지 않는다.

### P3 — #82 전수 소비 ledger와 사례표 확장

수정 위치는 기존 `load_machine_observation_rows`, `build_machine_decision_case_table`, `build_report`다.

- #76 manifest와 raw generation이 정확히 일치할 때만 policy-learning lane을 연다.
- loader의 현재 diagnostic counter와 별도로 상호배타 `final_disposition` ledger를 만든다.
- `case_count`는 유효 사례 수, `machine_valid_total`은 전체 유효 capture 수로 명칭을 분리한다. `case_count=0`도 capture가 모두 pending/gap이면 정상 empty가 아니라 그 이유를 보존한다.
- action/reason/hierarchy/policy bundle/compact micro/outcome/AI screen join을 한 case identity에 투영한다.
- `rows[-200:]`와 별도로 full case identity/content SHA-256, 전체·scope별 conservation map을 저장한다.
- exact AI join이 없는 행도 counterfactual 경로 평가와 실제 lifecycle 결속 상태를 각각 남긴다. exact AI 결손을 이유로 machine-only outcome 자체를 삭제하지 않는다.
- scope extension은 해당 scope의 machine rows만 사용하고, KRX/NXT/PREMARKET/aftermarket 근거를 교차 투영하지 않는다.

### P4 — #74 최종 소비 대사

#74는 다음 세 계층을 같은 표에 대사한다.

1. final `pipeline_events`와 다섯 AI raw generation/logical hash
2. #11 preflight의 source digest
3. #76 materialization source/identity digest

raw가 preflight 뒤 정상 append됐다면 “#11 성공 재사용”이 아니라 source 변경으로 표시하고 #76→#74를 최신 generation으로 최소 재실행한 뒤 #82를 진행한다. final source가 안정된 뒤에도 digest/count/scope가 다르면 `machine_ai_natural_source_consumption_gap`으로 fail closed한다. Provider replay를 다시 호출하지 않는다.

### P5 — 후행 consumer와 verifier

- #82 `optimizer_handoff.hierarchical_entry_quality.machine_decision_case_table`에 full digest와 conservation summary가 그대로 전달되는지 검증한다.
- 기계 threshold 학습은 `machine_evaluation_population`, AI prompt 품질 평가는 `ai_screen_population`, 외부 호출 품질은 `provider_attempt_population`만 사용한다.
- `main_ai_prompt_optimizer`와 `main_ai_prompt_consumer`가 machine non-entry를 AI WAIT/오답/무응답으로 재분류하지 않는지 검사한다.
- final verifier는 cutover date 이후 #11/#74 auxiliary audit, #76/#82 source hash, per-scope count, full case digest, optimizer handoff 일치를 필수로 한다. #82가 소비한 identity의 `valid + pending + gap + excluded` digest가 #74 final manifest와 같은지도 여기서 검사한다.
- machine capture 도입일인 `2026-09-13` 이전에는 `not_applicable_pre_capture_contract`를 허용하고, `2026-09-14`부터는 auxiliary manifest와 case-table 보존식을 필수로 한다. 과거 행을 현재 payload로 합성하지 않는다.
- verifier→tower→checklist의 요약에는 “machine evaluated / AI screen eligible / provider attempted / outcome evaluable” 네 분모를 별도 필드로 전달한다.

## 7. 필수 회귀 테스트

| 테스트 | 필수 반례 |
| --- | --- |
| `test_observation_source_quality_audit.py` | pipeline+다섯 AI raw 안정/append 중, invalid JSON, hash 변조, plain+gzip conflict, 식별 가능한 1행 exclusion, unisolatable source block, preflight→final generation drift |
| `test_ai_decision_quality.py` | BLOCK/RECHECK 정상 미호출, ENTER 실제 호출, preflight 미호출, timeout/schema invalid, reuse/no-new-call, 분모·scope digest 보존 |
| `test_ai_action_outcome_calibration.py` | action/bundle exact join, 다른 action의 단일 snapshot fallback 차단, duplicate/conflict, micro complete/gap/refill, cost/path/pending, scope 교차 금지, full digest와 recent-200 sample 분리 |
| `test_verify_threshold_cycle_postclose_chain.py` | raw→#11→#76→#74→#82 digest mismatch, 보존식 drift, 한 scope 누락, handoff 변조, 분석 authority와 source actual submit 혼동 차단 |
| `test_threshold_cycle_wrappers.py` | preflight/final phase 순서, 변경 generation 최소 재실행, Provider 재호출 없음, 기존 producer 순서 유지 |

직접 fixture에는 최소 다음 사례가 있어야 한다.

1. `BLOCK`/`RECHECK` + `provider_called=false` + `not_requested_machine_nonentry`는 정상 소비.
2. `ENTER_NOW` + PASS/VETO/CAUTION/invalid/timeout 각각의 canonical final screen.
3. 같은 machine evaluation의 bounded Provider retry는 machine 1건, provider attempt N건.
4. snapshot은 같지만 bundle/action이 다른 trace는 policy-learning 제외.
5. valid micro, source gap, cross-epoch, excessive refill, BUY trade backing 없는 depletion을 서로 다른 상태로 유지.
6. submit/full/partial/unfilled/pending/terminal/cost-null을 별도 상태로 유지.
7. KRX regular·PREMARKET·NXT continuous scope별 한 scope 누락을 전체 count 일치로 숨기지 않음.

## 8. 실행·review 순서

```text
계약 fixture로 현 결손 재현
→ P1 #11/#74 감사 보완
→ P2 #76 manifest
→ P3 #82 ledger/case table
→ P4/P5 final audit·verifier·handoff
→ self review/fix/re-review
→ targeted pytest + compile + wrapper syntax/test + git diff --check
→ 오늘 닫힌 자연 raw에 Provider 없이 #11→#76→#74→#82 최소 실행
→ verifier/tower/checklist 직접 consumer 확인
```

각 단계의 finding을 수정한 뒤 같은 반례와 직접 consumer를 다시 검사한다. 전수 장후 wrapper, Provider replay, 매매 process 재기동, PREOPEN env 수동 작성은 기본 검증 수단이 아니다. source hash가 바뀐 최초 producer와 영향 consumer만 재실행한다.

문서 변경은 print-only parser로 닫는다. Python 변경 시 관련 pytest와 compile, shell 변경 시 `bash -n deploy/run_threshold_cycle_postclose.sh`와 wrapper contract test, 모든 변경에 `git diff --check`를 수행한다.

## 9. 완료 조건

다음이 모두 충족돼야 구현 완료다.

- 오늘 닫힌 `pipeline_events`와 다섯 AI raw source의 검사 전후 generation 안정 및 logical hash 존재
- machine/AI/provider 세 분모의 전체·scope별 보존식과 `unclassified=0`
- 모든 valid machine capture가 유효·pending·gap·excluded 중 정확히 하나로 소비됨
- action·reason·policy bundle·micro receipt·후행 outcome의 exact identity 결속 또는 직접 gap reason
- 정상 machine non-entry 미호출을 AI 실패로 세지 않고, `ENTER_NOW` AI screen 누락을 정상 미호출로 숨기지 않음
- #11→#76→#74→#82→optimizer handoff→verifier의 source generation/hash 일치
- full population digest 검증과 recent-200 sample 제한의 분리
- row-level 결손 격리와 whole-source block 경계 유지
- review P0~P2 finding 0, targeted validation 통과
- Provider 신규 호출 0, 새 collector/cron/service 0, runtime/order/threshold/quantity/safety authority 변화 0

코드 완료와 오늘 자연 원천의 terminal 소비 검증은 별도 상태다. 자연 원천이 아직 append 중이면 구현은 검증 가능해도 #74 terminal은 `waiting_active_writer`다. 반대로 최종 자연 표본이 0이더라도 stable valid-empty와 직접 consumer가 닫히면 실행 결함은 아니다.

## 10. 기대효과와 한계

기대효과는 다음과 같다.

- 기계가 걸러 AI를 부르지 않은 정상 2,715건과 preflight/transport 결손을 분리해 AI 품질을 왜곡하지 않는다.
- `ENTER_NOW`가 실제 PASS/VETO screen과 후행 submit/fill/terminal로 이어졌는지 scope별 최초 결손을 찾을 수 있다.
- 선정 rule·정책 hash·micro depletion/trade backing/refill과 비용 후 빠른 outcome을 같은 사례로 비교할 수 있다.
- #82의 threshold 학습과 AI prompt calibration이 서로 다른 분모를 사용해 기계 개선과 AI 개선의 책임을 혼합하지 않는다.
- “비용 차감 후 작은 수익을 빈번하게”라는 목표를 `참여 기회 수 × 비용 후 EV × 도달시간/자본점유 × tail`로 검증할 수 있다.

이 보완만으로 BUY 수, 실현수익 또는 정책 승격이 증가하는 것은 아니다. 새 collector를 추가하거나 guard를 완화하지 않으며, 실제 개선은 다음 정책의 exact PREOPEN/PID 소비 뒤 동일 scope의 submit/fill/terminal·비용 후 순익으로 별도 판정한다.

## 11. 현재 owner 인계

새 checklist ID를 만들지 않는다. 구현 판단·코드 보완은 [9/14 체크리스트의 `CodeImprovementWorkorderReview0914`](../checklists/2026-09-14-stage2-todo-checklist.md), 오늘 final source 대사는 [`PostcloseSourceQualityGateReview0914`](../checklists/2026-09-14-stage2-todo-checklist.md), submitted trace/custody 결손은 기존 `MainAIQualitySourceGapMainAIAllocatorSubmittedTraceCustodyRepair0914`에서 각각 닫는다.

이 문서 수립 단계에서는 체크리스트 상태, raw source, report, PID, policy, env 또는 주문을 변경하지 않는다.

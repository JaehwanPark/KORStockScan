# Postclose AI Call Audit Report - 2026-05-21

## 1. Audit Scope

- 대상 체인: `2026-05-20` postclose 자동화체인과 `2026-05-21` PREOPEN 적용 확인에 연결되는 ADM/LDM/threshold-cycle 관련 산출물.
- 주요 확인 대상:
  - `deploy/run_threshold_cycle_postclose.sh`
  - `src/engine/daily_threshold_cycle_report.py`
  - `src/engine/lifecycle_decision_matrix.py`
  - `src/engine/scalp_entry_action_decision_matrix.py`
  - `src/engine/lifecycle_ai_context.py`
  - `src/engine/swing_lifecycle_audit.py`
  - `src/engine/openai_ws_stability_report.py`
  - `src/engine/scalp_sim_ai_deferred_review.py`
- 감리 질문: postclose 자동화 단계에서 AI 호출이 필요한 위치에서만 수행되는지, schema/guard/authority가 닫혀 있는지, 비용/지연/재시도 정책이 과하지 않은지.

## 2. Executive Decision

판정: `YELLOW`

요약:
- 안전성 관점은 대체로 양호하다. 실제 postclose AI 호출은 proposal-only로 제한되고, strict schema, deterministic guard, `store=false`, runtime mutation 금지선이 있다.
- 효율성 관점은 보완 필요하다. `threshold_cycle_ai_correction`의 실제 5/20 입력 컨텍스트가 약 `366,226` characters로 크며, token usage/cost가 산출물에 기록되지 않는다.
- ADM/LDM 자체는 외부 AI 호출을 하지 않는다. `scalp_entry_action_decision_matrix`, `lifecycle_decision_matrix`는 이벤트/리포트 row를 deterministic하게 소비한다.
- `lifecycle_ai_context`는 이름과 달리 postclose에서 AI API를 호출하지 않고, LDM/ADM 요약을 다음 runtime AI prompt에 넣기 위한 context artifact를 만든다.

감리 제출용 결론:
- "AI가 자동으로 runtime을 바꾼다"는 구조는 아니다.
- "AI 호출이 전혀 없다"도 아니다. threshold-cycle postclose correction에는 기본 OpenAI 호출이 있고, 이 호출은 deterministic guard의 보조 제안자다.
- 효율 개선의 1순위는 호출 수가 아니라 입력 압축, usage/cost observability, retry/error telemetry 보강이다.

## 3. R0~R6 Chain AI Call Map

| 단계 | 모듈/산출물 | 외부 AI 호출 | 기본 상태 | authority | runtime 영향 |
| --- | --- | ---: | --- | --- | --- |
| R0 collect | runtime OpenAI events | 없음, 기존 runtime event 읽기 | enabled in live runtime | source observation | 없음 |
| R1 daily report | `openai_ws_stability_report` | 없음 | report-only | transport audit | 없음 |
| R1/R2 report | `scalp_entry_action_decision_matrix` | 없음 | deterministic | ADM source/report | 없음 |
| R1/R2 report | `lifecycle_decision_matrix` | 없음 | deterministic | LDM policy source | 없음 |
| R1/R2 report | `lifecycle_ai_context --mode attribution` | 없음 | deterministic replay/aggregate | postclose attribution only | 없음 |
| R1/R2 report | `lifecycle_ai_context --mode context` | 없음 | provider=`none` | AI prompt context source | 직접 없음 |
| R3/R4 candidate | `daily_threshold_cycle_report --ai-correction-provider openai` | 있음 | postclose default openai | proposal-only | 직접 없음 |
| R4/R5 apply | `threshold_cycle_preopen_apply` | 없음 | consumes AI review artifact | deterministic guard owner | PREOPEN env only |
| R6 attribution | `threshold_cycle_ev_report`, `runtime_approval_summary` | 없음 | report-only | attribution/approval summary | 없음 |
| Swing postclose | `swing_lifecycle_audit --ai-review-provider none` | 기본 없음 | provider=`none` | proposal artifact | 없음 |
| Pattern labs | Gemini/Claude/DeepSeek named labs | 현재 scripts는 payload/report 생성, provider SDK 호출 없음 | source/report only | analysis source | 없음 |

## 4. Actual 2026-05-20 Artifact Evidence

### 4.1 Threshold Cycle AI Correction

- Artifact: `data/report/threshold_cycle_ai_review/threshold_cycle_ai_review_2026-05-20_postclose.json`
- `ai_status`: `parsed`
- `ai_provider_status.provider`: `openai`
- `status`: `success`
- `model`: `gpt-5.5`
- `attempt_index`: `1`
- `model_index`: `1`
- `attempted_keys`: `2`
- `attempted_models`: `["gpt-5.5", "gpt-5.4", "gpt-5.4-mini"]`
- `schema_name`: `threshold_ai_correction_v1`
- `reasoning_effort`: `high`
- `candidate_count`: `15`
- `guard_accepted`: `13 / 15`
- `runtime_change_any_in_ai_report`: `false`
- `ai_input_context_chars`: `366,226`

판정:
- 호출은 정상 성공했고 strict schema parse까지 닫혔다.
- deterministic guard가 최종 source of truth로 남아 있어 AI 단독 적용은 차단된다.
- 다만 입력 컨텍스트 크기가 크므로 비용/latency 효율은 `YELLOW`다.

### 4.2 Lifecycle AI Context

- Artifact: `data/report/lifecycle_ai_context/lifecycle_ai_context_2026-05-20.json`
- `provider_status`: `{"provider": "none", "status": "deterministic_fallback", "schema_name": "lifecycle_ai_context_v1", "fallback_used": true}`
- `runtime_effect`: `false`
- `decision_authority`: `ai_advisory_prompt_context_only`
- `prompt_stage_count`: `3`
- `warnings`: `[]`

판정:
- postclose API 호출 없음.
- LDM policy와 attribution을 `entry`, `holding`, `exit` prompt context로 압축하는 산출물이다.
- `submit`, `scale_in`은 prompt injection 대상이 아니라 provenance/report-only로 제한된다.

### 4.3 Lifecycle AI Context Attribution

- Artifact: `data/report/lifecycle_ai_context_attribution/lifecycle_ai_context_attribution_2026-05-20.json`
- `context_eligible_count`: `0`
- `context_applied_count`: `0`
- `no_context_replay_sample`: `0`
- `replay_budget`: `30`
- `stage_quality_counts`: `{"hold_sample": 5}`
- `warnings`: `["lifecycle_ai_context_runtime_provenance_missing"]`

판정:
- 외부 AI replay 호출 없음.
- 현재는 attribution 표본 부족으로 `hold_sample`이다.
- 감리 관점에서는 비용 문제가 아니라 provenance/표본 문제다.

### 4.4 Swing Threshold AI Review

- Artifact: `data/report/swing_threshold_ai_review/swing_threshold_ai_review_2026-05-20.json`
- `ai_status`: `unavailable`
- `ai_provider_status`: `{"provider": "none", "status": "not_requested"}`
- `candidate_count`: `12`

판정:
- 기본값 `SWING_THRESHOLD_AI_REVIEW_PROVIDER=none`이 작동해 OpenAI 호출이 차단됐다.
- 스윙은 proposal artifact만 생성하고 approval artifact 없이 runtime env/live order로 연결되지 않는다.

### 4.5 OpenAI WS Stability Report

- Artifact: `data/report/openai_ws/openai_ws_stability_2026-05-20.json`
- `decision`: `keep_ws`
- 이 리포트는 신규 OpenAI API 호출을 하지 않고 `pipeline_events`의 runtime OpenAI transport metadata를 읽는다.

판정:
- postclose 비용을 발생시키는 AI 호출이 아니다.
- runtime transport 효율성 감리에는 유효하지만 postclose AI call cost에는 직접 기여하지 않는다.

### 4.6 Scalp Sim AI Deferred Review

- Artifact: `data/report/scalp_sim_ai_deferred_review/scalp_sim_ai_deferred_review_2026-05-20.json`
- `deferred_count`: `715`
- `defer_reason_counts`: `{"sim_ai_budget_exhausted": 715}`
- `decision_authority`: `sim_observation_only`
- `runtime_effect`: `false`

판정:
- 이 단계도 외부 AI 호출 없음.
- sim holding AI budget 때문에 호출하지 못한 deferred source를 정리하는 비용 방어/품질 보고서다.

## 5. Code-Level Call Contracts

### 5.1 OpenAI Threshold Correction

Source:
- `src/engine/daily_threshold_cycle_report.py:6079`
- `src/engine/daily_threshold_cycle_report.py:6107`
- `src/engine/daily_threshold_cycle_report.py:6210`
- `src/engine/daily_threshold_cycle_report.py:6228`
- `src/engine/daily_threshold_cycle_report.py:6233`

Contract:
- API key loader는 `OPENAI_API_KEY*`를 정렬해 key rotation 후보로 쓴다.
- model sequence는 기본 `gpt-5.5 -> gpt-5.4 -> gpt-5.4-mini`다.
- Responses API를 사용한다.
- `text.format`은 `threshold_ai_correction_v1` strict schema를 쓴다.
- `text.verbosity`는 `low`다.
- `reasoning.effort`는 postclose `high`, intraday `medium`이다.
- `store=false`다.
- metadata는 `endpoint_name=threshold_ai_correction`, `schema_name=threshold_ai_correction_v1`, `run_phase`를 남긴다.
- timeout은 `180s`다.

Safety:
- prompt instruction은 env/code/runtime 변경, restart, 장중 threshold mutation, safety guard 우회를 금지한다.
- parse 후 `_guard_ai_correction_proposal()`이 family bounds, max step, state, safety rule을 다시 검증한다.
- AI correction artifact 자체의 `runtime_change`는 `false`다.

Efficiency assessment:
- 장점: 호출 성공 시 즉시 반환하므로 5/20은 1 key x 1 model만 사용했다.
- 장점: schema와 low verbosity로 출력 token 낭비를 줄인다.
- 보완: 입력 context가 `366,226` characters로 커서 prompt token 비용이 크다.
- 보완: response usage/cost/latency가 artifact에 없다.
- 보완: full context를 그대로 artifact에 저장해 report size도 커진다.

### 5.2 Gemini Threshold Correction

Source:
- `src/engine/daily_threshold_cycle_report.py:6274`
- `src/engine/daily_threshold_cycle_report.py:6290`

Contract:
- `--ai-correction-provider gemini`일 때만 호출된다.
- postclose wrapper 기본값은 `openai`라 5/20에는 사용하지 않았다.

Efficiency assessment:
- 현재 기본 경로가 아니므로 postclose 비용에는 기여하지 않았다.
- fallback/provider split은 명확하지만 Gemini 경로도 usage/cost 기록은 없다.

### 5.3 Swing Threshold AI Review

Source:
- `src/engine/swing_lifecycle_audit.py:2583`
- `src/engine/swing_lifecycle_audit.py:2598`
- `src/engine/swing_lifecycle_audit.py:2619`
- `deploy/run_threshold_cycle_postclose.sh:36`
- `deploy/run_threshold_cycle_postclose.sh:640`

Contract:
- wrapper 기본값은 `SWING_THRESHOLD_AI_REVIEW_PROVIDER=none`.
- 명시적으로 `openai`를 줄 때만 OpenAI Responses API를 호출한다.
- threshold correction과 같은 `threshold_ai_correction_v1` schema를 사용한다.
- reasoning effort는 `medium`, timeout은 `180s`, `store=false`.

Safety:
- proposal-only instruction이다.
- broker order, runtime/env/code, restart, intraday threshold mutation 금지선이 명시돼 있다.

Efficiency assessment:
- 기본 OFF라 비용 방어는 강하다.
- 켜는 경우 threshold correction과 같은 usage/cost observability gap이 있다.

### 5.4 LDM/ADM Context Generation

Source:
- `deploy/run_threshold_cycle_postclose.sh:473`
- `deploy/run_threshold_cycle_postclose.sh:485`
- `src/engine/lifecycle_ai_context.py:242`
- `src/engine/lifecycle_ai_context.py:293`

Contract:
- LDM은 postclose에서 2회 실행된다. 1차는 raw policy 생성, 2차는 attribution feedback 이후 refresh다.
- `lifecycle_ai_context`는 attribution/context artifact를 생성하지만 provider=`none`이면 API 호출하지 않는다.
- `provider`가 `openai`여도 현재 구현은 `not_called_v1`로 기록하며 실제 API call implementation은 없다.

Safety:
- `runtime_effect=false`
- `decision_authority=ai_advisory_prompt_context_only`
- `actual_order_submitted=false`
- `broker_order_forbidden=true`
- prompt injection allowed stage는 `entry`, `holding`, `exit`로 제한된다.

Efficiency assessment:
- postclose API 비용은 없다.
- context artifact가 다음 runtime AI prompt에 붙으므로 runtime 호출 비용에는 간접 영향이 있다.
- context text hash가 있으므로 중복/변경 감지는 가능하지만, runtime prompt token 증가량의 계량은 별도 필요하다.

## 6. Efficiency Review

### Positive Controls

- 실제 postclose AI 호출 수가 제한적이다. 5/20 기준 성공한 외부 AI call은 threshold correction 1회로 복원된다.
- swing AI review는 기본 OFF다.
- LDM/ADM은 AI API가 아니라 deterministic matrix/report layer다.
- OpenAI threshold correction은 structured output schema, low verbosity, `store=false`, metadata를 사용한다.
- wrapper는 AI correction retry를 최대 2회로 제한한다.
- OpenAI 실패 시 postclose status에 `ai_correction_status`를 남기며, verifier가 후행 품질을 확인한다.
- sim AI deferred review는 `sim_ai_budget_exhausted`를 별도 artifact로 표면화해 호출량 통제 실패를 숨기지 않는다.

### Efficiency Gaps

| severity | gap | evidence | risk | recommendation |
| --- | --- | --- | --- | --- |
| must_fix_before_scale | AI input context too large | 5/20 `ai_input_context_chars=366,226` | 비용/latency 증가, schema retry 시 비용 급증 | threshold AI input에 section별 cap, top-N, hash+path reference, source metrics summary를 적용 |
| should_fix | no token usage/cost telemetry | `ai_provider_status`에 usage 없음 | 비용 감리에서 호출당 비용 복원 불가 | response usage fields와 elapsed_ms, prompt_chars, output_chars 기록 |
| should_fix | no cache/keyed idempotency | 같은 date/phase 재생성 시 재호출 가능 | 재생성/재시도 비용 증가 | input_context_hash가 동일하고 parsed artifact가 있으면 reuse option 제공 |
| should_fix | swing review callable path shares heavy model sequence | swing provider openai 활성화 시 `gpt-5.5` 우선 | proposal-only swing review에 과한 모델 비용 가능 | swing default none 유지, 활성화 시 mini/medium model override 가능하게 분리 |
| defer | lifecycle context runtime token impact not measured | context artifact has hash but no token estimate | 다음 runtime OpenAI prompt 비용 증가 가능 | context_text chars/token estimate와 per-stage max length gate 추가 |

## 7. Safety Review

### Confirmed Safe

- AI correction is proposal-only.
- Deterministic guard remains source of truth.
- AI artifacts have `runtime_change=false`.
- PREOPEN apply is the only runtime env path; intraday mutation is forbidden.
- LDM/ADM cannot bypass hard safety, broker guard, stale quote guard, account/order/qty/cooldown guard.
- sim/probe artifacts keep `actual_order_submitted=false` and `broker_order_forbidden=true`.

### Remaining Safety Watch

- `threshold_cycle_ai_review` can have `guard_accepted=true` items, but final application still depends on preopen deterministic apply rules. Audit should review both AI review and `threshold_apply_YYYY-MM-DD.json`, not the AI report alone.
- `lifecycle_ai_context` is direct prompt context for runtime AI. It is not a deterministic order rule, but prompt influence should remain observable through `lifecycle_ai_context_*` provenance fields.
- Pattern labs have model-branded names, but current automated path builds payloads/reports rather than calling those external models. Audit wording should distinguish "payload for AI review" from "AI API call".

## 8. Auditor Questions and Direct Answers

### Q1. ADM/LDM에서 AI를 매번 호출하나?

아니다. `scalp_entry_action_decision_matrix`와 `lifecycle_decision_matrix`는 postclose source rows를 deterministic하게 집계한다. 외부 AI 호출은 없다.

### Q2. LDM AI context는 AI 호출인가?

아니다. `lifecycle_ai_context`는 context artifact builder다. 5/20 산출물의 provider status는 `deterministic_fallback`이며, API call이 아니다. 다만 이 context가 다음 runtime OpenAI prompt에 붙을 수 있으므로 runtime token 비용에는 간접 영향이 있다.

### Q3. postclose에서 실제 OpenAI 호출은 무엇인가?

`daily_threshold_cycle_report --ai-correction-provider openai`가 생성하는 `threshold_cycle_ai_correction`이다. 5/20에는 `gpt-5.5` 1회 성공, strict schema parsed로 닫혔다.

### Q4. AI가 threshold를 직접 바꾸나?

아니다. AI는 correction proposal을 만들고, deterministic guard가 bounds/max step/safety를 검증한다. 실제 env 반영은 다음 PREOPEN apply artifact에서만 발생한다.

### Q5. 비용 효율은 충분한가?

현재 호출 수 제한은 충분하지만 입력 크기와 usage telemetry는 부족하다. 5/20 threshold AI context가 약 36.6만 character이므로 감리 관점에서는 `YELLOW`다.

## 9. Recommended Remediation Plan

### Must Fix Before Increasing AI Usage

1. `threshold_ai_correction` input context cap 도입
   - candidate별 `source_metrics` full blob 대신 summary top-N만 전달한다.
   - full source는 artifact path/hash로 참조한다.
   - `calibration_source_bundle`, `trade_lifecycle_attribution`, `threshold_cycle_cumulative`에 section별 char cap을 둔다.

2. AI usage telemetry 기록
   - `prompt_chars`, `input_context_hash`, `elapsed_ms`, `output_chars`를 `ai_provider_status`에 기록한다.
   - OpenAI response usage가 제공되면 `input_tokens`, `output_tokens`, `total_tokens`도 기록한다.

### Should Fix

1. idempotent reuse option
   - 동일 date/phase/input_hash의 parsed AI review가 있으면 `--reuse-ai-review-if-valid`로 재호출을 피한다.

2. lifecycle context token budget
   - `stage_contexts[].context_text_chars`, `context_token_estimate`, `max_context_chars`를 추가한다.
   - stage별 context가 상한을 넘으면 deterministic summary로 축약한다.

3. swing AI review model policy split
   - 기본 none 유지.
   - 명시 활성화 시 swing review 전용 model sequence를 둘 수 있게 한다.

### Defer

1. Pattern lab external model execution
   - 현재 자동화는 payload/report 생성 경로다.
   - 외부 model 실행을 다시 붙이려면 별도 provider contract, usage telemetry, runtime forbidden uses가 필요하다.

## 10. Final Audit Position

최종 판정: `YELLOW - safe but efficiency observability incomplete`

- 안전성: `GREEN`
- 호출 범위 통제: `GREEN`
- 비용 효율: `YELLOW`
- usage/cost 관측성: `YELLOW`
- ADM/LDM AI 호출 오해 가능성: `YELLOW`, 문서/감리 설명으로 해소 가능

감리 제출 시 강조할 문장:

> ADM/LDM은 postclose에서 AI API를 호출하지 않는 deterministic matrix/report 계층이다. 실제 postclose AI API 호출은 threshold-cycle correction proposal에 한정되며, strict schema와 deterministic guard 뒤에 놓인다. 현재 보완해야 할 핵심은 호출 남용이 아니라 큰 입력 컨텍스트와 usage/cost telemetry 부재다.


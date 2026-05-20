# 감리보고서 검토 결과서

- **검토 대상:** `postclose_ai_call_audit_2026-05-21.md`
- **검토 목적:** postclose 자동화체인의 AI 호출 범위, runtime authority 통제, schema/guard 폐쇄성, 비용·지연·재시도 관측성 검토
- **최종 판정:** `YELLOW 유지`
- **제출 의견:** 조건부 제출 가능. 안전성은 대체로 양호하나, 비용·관측성 보완 전 `GREEN` 승격은 보류한다.

---

## 1. 최종 검토 판정

제출된 감리보고서의 핵심 결론은 타당하다.

보고서는 `2026-05-20` postclose 자동화체인과 `2026-05-21` PREOPEN 적용 확인에 연결되는 ADM/LDM/threshold-cycle 산출물을 대상으로 다음 사항을 점검하고 있다.

- postclose 자동화 단계에서 AI 호출이 필요한 위치에서만 수행되는지
- schema, guard, authority가 닫혀 있는지
- 비용, 지연, 재시도 정책이 과하지 않은지
- ADM/LDM과 실제 AI API 호출 경로가 명확히 구분되는지
- AI proposal이 runtime을 직접 변경하지 않는지

검토 결과, 보고서의 최종 판정인 **`YELLOW - safe but efficiency observability incomplete`**는 적정하다.

안전성 측면에서는 AI correction이 proposal-only로 제한되어 있고, deterministic guard와 PREOPEN apply 경로에 의해 runtime 변경 권한이 통제된다. 반면 효율성 측면에서는 `threshold_cycle_ai_correction` 입력 컨텍스트가 약 `366,226` characters로 과대하고, token usage/cost/latency가 산출물에 기록되지 않아 비용 감리와 재현성이 불완전하다.

---

## 2. 핵심 검토 의견

### 2.1 안전성 결론은 대체로 타당함

ADM/LDM은 postclose에서 외부 AI API를 호출하지 않는 deterministic matrix/report 계층으로 정리되어 있다.

실제 postclose AI 호출은 다음 경로에 한정된다.

```text
daily_threshold_cycle_report
  --ai-correction-provider openai
  → threshold_cycle_ai_correction proposal
```

이 경로는 correction proposal을 생성할 뿐이며, runtime threshold를 직접 변경하지 않는다. 이후 적용은 deterministic guard와 PREOPEN apply 경로에서만 이루어진다.

확인된 안전 장치는 다음과 같다.

- AI correction은 proposal-only 구조
- strict schema 사용
- deterministic guard가 최종 source of truth 역할 수행
- `store=false` 적용
- runtime mutation 금지선 존재
- intraday threshold mutation 금지
- broker order, restart, env/code 변경 금지
- PREOPEN apply만 runtime env 반영 경로로 허용

따라서 “AI가 자동으로 runtime을 바꾼다”는 구조는 아닌 것으로 판단한다.

### 2.2 “AI 호출이 없다”가 아니라 “제한된 proposal-only 호출이 있다”가 정확함

보고서는 ADM/LDM 자체가 AI 호출이 아니며, `lifecycle_ai_context`도 postclose API 호출이 아니라 runtime prompt context artifact 생성이라고 구분하고 있다.

반면 threshold-cycle correction에는 실제 OpenAI 호출이 존재한다.

따라서 제출 시 표현은 다음과 같이 정리하는 것이 적절하다.

> 본 체인은 AI가 runtime을 직접 변경하는 구조가 아니다. 다만 postclose threshold-cycle correction 단계에는 OpenAI 기반 proposal-only 호출이 존재하며, 이 제안은 strict schema와 deterministic guard 뒤에서만 소비된다.

이 문구는 “AI 호출 없음”이라는 과소진술과 “AI가 자동 반영함”이라는 과대해석을 모두 방지한다.

### 2.3 비용·지연 감리는 아직 미흡함

가장 큰 문제는 호출 수가 아니라 **입력 규모와 관측성 부족**이다.

보고서 기준으로 `2026-05-20` 성공한 외부 AI call은 threshold correction 1회로 제한되어 있다. 그러나 `ai_input_context_chars=366,226`로 입력이 과대하며, `ai_provider_status`에 usage/cost telemetry가 없다.

이 상태에서는 다음 리스크가 남는다.

- schema retry 발생 시 비용 급증
- key retry 발생 시 중복 비용 발생
- model fallback 발생 시 latency 증가
- 동일 input 재생성 시 불필요한 AI 재호출 가능
- 호출당 비용, token 수, latency 사후 복원 불가
- input/output hash 외 비용 감사 근거 부족

따라서 비용·지연 감리 관점에서는 `YELLOW` 유지가 적정하다.

---

## 3. 주요 증거 검토

### 3.1 Threshold Cycle AI Correction

확인된 산출물:

```text
data/report/threshold_cycle_ai_review/
threshold_cycle_ai_review_2026-05-20_postclose.json
```

핵심 값:

```text
ai_status: parsed
provider: openai
model: gpt-5.5
schema_name: threshold_ai_correction_v1
candidate_count: 15
guard_accepted: 13 / 15
runtime_change_any_in_ai_report: false
ai_input_context_chars: 366,226
```

판정:

- 호출은 정상 성공했고 strict schema parse까지 완료되었다.
- deterministic guard가 최종 적용 여부를 통제하므로 AI 단독 적용은 차단된다.
- 다만 입력 컨텍스트가 과대하여 비용·latency 효율은 미흡하다.

### 3.2 Lifecycle AI Context

확인된 산출물:

```text
data/report/lifecycle_ai_context/
lifecycle_ai_context_2026-05-20.json
```

핵심 값:

```text
provider: none
status: deterministic_fallback
runtime_effect: false
decision_authority: ai_advisory_prompt_context_only
prompt_stage_count: 3
warnings: []
```

판정:

- postclose API 호출이 아니다.
- LDM policy와 attribution을 `entry`, `holding`, `exit` prompt context로 압축하는 deterministic context artifact다.
- runtime prompt에 붙을 수 있으므로 향후 token budget 관리가 필요하다.

### 3.3 Lifecycle AI Context Attribution

확인된 산출물:

```text
data/report/lifecycle_ai_context_attribution/
lifecycle_ai_context_attribution_2026-05-20.json
```

핵심 값:

```text
context_eligible_count: 0
context_applied_count: 0
stage_quality_counts: {"hold_sample": 5}
warnings: ["lifecycle_ai_context_runtime_provenance_missing"]
```

판정:

- 외부 AI replay 호출 없음.
- 비용 문제보다는 provenance 및 표본 부족 문제가 크다.
- 다음 감리에서는 runtime provenance 보강 여부를 확인해야 한다.

### 3.4 Swing Threshold AI Review

확인된 산출물:

```text
data/report/swing_threshold_ai_review/
swing_threshold_ai_review_2026-05-20.json
```

핵심 값:

```text
ai_status: unavailable
provider: none
status: not_requested
candidate_count: 12
```

판정:

- 기본값 `SWING_THRESHOLD_AI_REVIEW_PROVIDER=none`이 작동하여 OpenAI 호출이 차단되었다.
- swing review는 기본 OFF 상태를 유지하는 것이 적절하다.
- 활성화 시에는 threshold correction과 동일한 heavy model sequence를 그대로 쓰지 말고 별도 mini/medium model policy가 필요하다.

### 3.5 OpenAI WS Stability Report

확인된 산출물:

```text
data/report/openai_ws/
openai_ws_stability_2026-05-20.json
```

핵심 값:

```text
decision: keep_ws
```

판정:

- 신규 OpenAI API 호출을 발생시키는 postclose 단계가 아니다.
- runtime OpenAI transport metadata를 읽어 안정성을 평가하는 report-only 계층이다.
- postclose AI call cost에는 직접 기여하지 않는다.

### 3.6 Scalp Sim AI Deferred Review

확인된 산출물:

```text
data/report/scalp_sim_ai_deferred_review/
scalp_sim_ai_deferred_review_2026-05-20.json
```

핵심 값:

```text
deferred_count: 715
defer_reason_counts: {"sim_ai_budget_exhausted": 715}
decision_authority: sim_observation_only
runtime_effect: false
```

판정:

- 외부 AI 호출 없음.
- budget exhausted 상태를 숨기지 않고 artifact로 표면화한 점은 비용 방어 측면에서 긍정적이다.
- 다만 deferred source가 누적되는 경우 품질 감리와 원인 분석은 별도로 필요하다.

---

## 4. 보완 필요 사항

### 4.1 필수 보완 — AI 입력 컨텍스트 상한 도입

`threshold_ai_correction` 입력 context가 과대하다.

현재 `ai_input_context_chars=366,226` 수준이면 호출 1회는 통제되어도, retry 또는 fallback 발생 시 비용과 지연이 급격히 증가할 수 있다.

조치 방향:

```text
- candidate별 source_metrics full blob 전달 금지
- source_metrics는 summary top-N만 전달
- full source는 artifact path/hash로 참조
- calibration_source_bundle section cap 도입
- trade_lifecycle_attribution section cap 도입
- threshold_cycle_cumulative section cap 도입
- total input context hard cap 도입
```

제출 의견:

> 이 항목은 단순 성능 개선이 아니라 비용 통제와 재시도 리스크 통제 항목이다. AI 사용 확대 전 필수 보완사항으로 지정해야 한다.

### 4.2 필수 보완 — usage/cost/latency telemetry 기록

`ai_provider_status`에는 최소한 다음 필드를 추가해야 한다.

```text
prompt_chars
input_context_hash
elapsed_ms
output_chars
input_tokens
output_tokens
total_tokens
estimated_cost
attempted_key_count
attempted_model_count
retry_reason
```

제출 의견:

> usage/cost telemetry가 없는 상태에서는 “호출 수가 제한적이었다”는 판단은 가능하지만, “비용 효율이 충분하다”는 판단은 불가능하다.

### 4.3 필수 보완 — idempotent reuse 옵션 도입

동일한 date/phase/input_hash의 parsed AI review가 이미 존재하면 재호출하지 않고 재사용해야 한다.

권장 옵션:

```text
--reuse-ai-review-if-valid
```

권장 동작:

```text
if existing_review.status == parsed
and existing_review.input_context_hash == current_input_context_hash
and existing_review.schema_name == threshold_ai_correction_v1:
    reuse existing artifact
else:
    call provider
```

제출 의견:

> 이 항목은 재생성, verifier 재실행, postclose rerun 상황에서 불필요한 AI 비용을 막는 핵심 장치다.

### 4.4 추가 확인 필요 — PREOPEN apply artifact 대조

`threshold_cycle_ai_review`에서 `guard_accepted=true`인 항목이 존재해도 최종 적용은 PREOPEN deterministic apply rules에 달려 있다.

따라서 다음 대조 체계가 필요하다.

```text
AI proposal artifact
→ deterministic guard result
→ threshold_apply_YYYY-MM-DD.json
→ PREOPEN env diff
→ runtime threshold loaded evidence
```

제출 의견:

> 현재 보고서는 PREOPEN apply 대조 필요성을 언급하고 있으나, 실제 `threshold_apply_YYYY-MM-DD.json` 값 대조표는 포함하지 않았다. 다음 감리 산출물에는 반드시 대조표를 포함해야 한다.

### 4.5 추가 확인 필요 — attempted_keys 서술 불일치 가능성

보고서에는 다음 두 표현이 함께 존재한다.

```text
attempted_keys: 2
5/20은 1 key x 1 model만 사용했다
```

두 표현은 의미가 다를 수 있다.

정정 방향:

```text
1안:
attempted_keys=2는 후보 key 수이며,
실제 성공 호출은 1 key x 1 model이었다고 주석 처리한다.

2안:
실제 2개 key가 시도되었으면,
“1 key x 1 model” 표현을 삭제하거나 수정한다.
```

제출 의견:

> 비용 감리 문맥에서 오해를 유발할 수 있으므로 제출 전 의미를 명확히 해야 한다.

---

## 5. 최종 제출 의견

본 감리보고서는 **조건부 제출 가능**하다.

안전성 측면에서는 AI correction이 proposal-only로 제한되고, strict schema, deterministic guard, `store=false`, runtime mutation 금지선, PREOPEN apply 경로 분리 등 주요 통제 장치가 확인된다.

ADM/LDM 및 `lifecycle_ai_context`는 postclose 외부 AI 호출이 아니며, deterministic report/context artifact 계층으로 분류하는 것이 타당하다.

반면 효율성 측면에서는 다음 문제가 남아 있다.

```text
- threshold_cycle_ai_correction 입력 컨텍스트 과대
- token usage/cost/latency telemetry 부재
- 동일 input hash에 대한 재사용 옵션 미구현
- PREOPEN apply artifact 대조표 미포함
- attempted_keys 관련 서술 불명확
```

따라서 최종 제출 문구는 다음과 같이 확정한다.

> 감리 결과, postclose 자동화체인의 AI 호출 범위와 runtime authority 통제는 대체로 안전하게 구성되어 있다. ADM/LDM은 AI API 호출 계층이 아니며, 실제 postclose AI 호출은 threshold-cycle correction proposal에 한정된다. 다만 threshold AI 입력 컨텍스트 과대, usage/cost/latency telemetry 부재, idempotent reuse 미구현으로 인해 비용 효율성과 사후 감리 관측성이 불완전하다. 이에 따라 최종 판정은 `YELLOW - safe but efficiency observability incomplete`로 유지하며, AI 사용 확대 전 input cap, usage telemetry, reuse guard를 필수 보완사항으로 지정한다.

---

## 6. 조치 지시

### 6.1 즉시 조치

1. `threshold_ai_correction` 입력 context cap을 도입한다.
2. `ai_provider_status`에 usage/cost/latency telemetry를 기록한다.
3. 동일 `date/phase/input_context_hash`의 parsed artifact 재사용 옵션을 추가한다.
4. `attempted_keys=2`와 “1 key x 1 model” 표현의 의미 차이를 정정한다.

### 6.2 다음 감리 산출물 반영

1. `threshold_cycle_ai_review`와 `threshold_apply_YYYY-MM-DD.json`의 대조표를 포함한다.
2. PREOPEN env diff와 runtime threshold loaded evidence를 연결한다.
3. `lifecycle_ai_context`의 runtime prompt token 증가량을 stage별로 계량한다.
4. stage별 max context length gate를 둔다.
5. swing AI review는 기본 `none`을 유지하고, 활성화 시 mini/medium model sequence를 별도 정책으로 분리한다.

### 6.3 보류 가능 항목

1. Pattern lab external model execution은 현재 자동화 경로에 붙이지 않는다.
2. 외부 model execution을 재도입할 경우 별도 provider contract, usage telemetry, runtime forbidden uses를 먼저 정의한다.

---

## 7. 최종 결론

보고서는 제출 가능하다.

단, `GREEN` 승격은 보류한다.

최종 결론은 다음과 같다.

```text
YELLOW 유지
안전성 양호
호출 범위 통제 양호
비용·관측성 보완 필요
AI 사용 확대 전 input cap / usage telemetry / reuse guard 필수
```

제출 판정:

> **조건부 제출 가능 — `YELLOW 유지 / 안전성 양호 / 비용·관측성 보완 필요`**

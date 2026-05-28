# 2026-04-29 DeepSeek Enable Acceptance / Backlog Spec

작성일: `2026-04-29 KST`
Source: [workorder_deepseek_engine_review.md](/home/ubuntu/KORStockScan/docs/archive/workorders/workorder_deepseek_engine_review.md), [2026-04-27-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-27-stage2-todo-checklist.md), [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-28-stage2-todo-checklist.md)
대상 코드: [ai_engine_deepseek.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_deepseek.py), [test_ai_engine_cache.py](/home/ubuntu/KORStockScan/src/tests/test_ai_engine_cache.py)

## 1. 판정

1. `P1 context-aware bounded backoff`는 **flag-off 운영 승인**까지만 유지하고, `remote` 실전 enable은 아직 미승인이다. `2026-04-29 14:10 KST` 기준 acceptance snapshot/logging 묶음은 코드에 반영했다.
2. `P2 gatekeeper structured-output`은 **설계 메모 유지 / 실전 미승인**이다.
3. `holding cache bucket reduction`은 **EV 근거 부족으로 backlog 유지**다.
4. `Tool Calling`은 **code debt / 설계 메모 backlog 유지**다.

## 2. 근거

1. DeepSeek P1 guard는 코드상 이미 준비돼 있다.
   - [ai_engine_deepseek.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_deepseek.py:534) `DEEPSEEK_CONTEXT_AWARE_BACKOFF_ENABLED`
   - [ai_engine_deepseek.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_deepseek.py:562) `response_format={"type":"json_object"}`
   - [ai_engine_deepseek.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_deepseek.py:545) `_build_retry_acceptance_snapshot`
2. `_call_deepseek_safe()`는 이미 `system role + user role` 구조이며, `require_json=True`면 `json.loads(raw_text)` fast-path 후 fallback parser를 탄다.
3. `live_sensitive` 분기도 이미 있다.
   - [ai_engine_deepseek.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_deepseek.py:568)
   - 다만 same-day enable에 필요한 `api_call_lock` 체류시간 관찰, retry 후 rate-limit/log acceptance 메모는 문서에 아직 잠기지 않았다.
4. gatekeeper는 text report shared path를 그대로 사용한다.
   - [ai_engine_deepseek.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_deepseek.py:1090) `_generate_realtime_report_payload()`
   - [ai_engine_deepseek.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_deepseek.py:1511) `evaluate_realtime_gatekeeper()`
   - 따라서 JSON structured-output 전환은 `flag-off + text fallback + contract test` 없이는 승격하면 안 된다.
5. holding cache는 노이즈 흡수 목적이 명확하고 테스트도 그 전제를 가진다.
   - [ai_engine_deepseek.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_deepseek.py:228)
   - [ai_engine_deepseek.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_deepseek.py:290)
   - [test_ai_engine_cache.py](/home/ubuntu/KORStockScan/src/tests/test_ai_engine_cache.py:206)

## 3. Acceptance Table

| axis | enable acceptance | not now reason | required proof | next slot |
| --- | --- | --- | --- | --- |
| `context-aware backoff` | `flag default OFF`, `live_sensitive cap <= 0.8s`, `report/eod cap`, retry 후 rate-limit/log acceptance, `api_call_lock` worst-case 관찰 | live enable 전 post-restart 표본이 아직 없다 | remote cohort별 `lock_wait_ms`, retry count, rate-limit log 샘플 | `2026-04-30 POSTCLOSE` |
| `gatekeeper structured-output` | `flag default OFF`, text fallback, `action_label/allow_entry/report/selected_mode/timing` contract test | shared text path를 그대로 쓰고 있어 JSON option ingress 부재 | option flag, fallback path, cache contract tests | `2026-04-30 POSTCLOSE` |
| `holding cache bucket reduction` | `completed_valid`, `partial/full`, `initial/pyramid`, `missed_upside`, `exit quality` 개선 근거 | 호출량 증가 대비 EV 개선 근거 없음 | hold/exit cohort 비교표 | backlog only |
| `Tool Calling` | 퍼블릭 schema/fallback/test/rollback 구조 | 설계 메모 단계, 기대값 개선 직접근거 없음 | response schema, fallback, SDK 제약 메모 | backlog only |

## 4. Cohort / Guard

1. `baseline cohort`
   - 현재 remote DeepSeek 경로
   - `DEEPSEEK_CONTEXT_AWARE_BACKOFF_ENABLED=False`
   - gatekeeper는 shared text report path 유지
2. `candidate live cohort`
   - 없음. same-day enable 금지
3. `observe-only cohort`
   - retry sleep/lock_wait/log acceptance 수집
   - gatekeeper structured-output option spec
4. `excluded cohort`
   - holding cache bucket reduction live 변경
   - Tool Calling 구현 승격
5. `rollback owner`
   - remote 경로라도 live-sensitive call latency가 늘면 미진입 기회비용이 커지므로 `flag-off` 즉시 복귀가 가능해야 한다.

## 5. 다음 액션

1. `2026-04-30`에는 `remote enable`이 아니라 `acceptance snapshot/log field`가 실제 로그에서 보이는지 확인한다.
2. backoff 축은 `api_call_lock` 체류시간과 retry 후 로그 acceptance가 문서화되기 전까지 OFF 유지다.
3. gatekeeper structured-output은 text report 경로를 대체하지 않고 `option path`로만 설계한다.
4. holding cache / Tool Calling은 새로운 EV 근거가 생기기 전까지 backlog로만 유지한다.

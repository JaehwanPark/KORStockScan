# 2026-04-29 Gemini Enable Acceptance / Schema Matrix

작성일: `2026-04-29 KST`
Source: [workorder_gemini_engine_review.md](/home/ubuntu/KORStockScan/docs/archive/workorders/workorder_gemini_engine_review.md), [2026-04-27-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-27-stage2-todo-checklist.md), [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-28-stage2-todo-checklist.md)
대상 코드: [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py), [test_ai_engine_cache.py](/home/ubuntu/KORStockScan/src/tests/test_ai_engine_cache.py), [test_gemini_live_prompt_smoke.py](/home/ubuntu/KORStockScan/src/tests/test_gemini_live_prompt_smoke.py)

## 1. 판정

1. `P1 system_instruction`과 `P1 deterministic JSON config`는 `flag default OFF` 상태의 **관찰/설계 승인**까지만 허용한다.
2. `P2 response schema registry`는 `2026-04-29 14:10 KST` 기준 `flag-off 코드 묶음`까지 반영했다. 실전 enable은 여전히 미승인이다.
3. 다음 범위는 `main live enable`이 아니라 `schema registry load/contract 관찰`이다.

## 2. 근거

1. Gemini P1 flag는 이미 코드상 준비돼 있다.
   - [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py:1193) `GEMINI_SYSTEM_INSTRUCTION_JSON_ENABLED`
   - [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py:1206) `GEMINI_JSON_DETERMINISTIC_CONFIG_ENABLED`
2. 현재 `_call_gemini_safe()`는 `require_json=True` 경로에서만 `system_instruction`, `temperature/top_p/top_k`를 분기하므로, 설계상 `JSON path limited change`는 가능하다.
3. 하지만 Gemini는 `main` 실전 엔진이고, 아래 경로가 모두 같은 호출부를 지나간다.
   - `entry/holding`: [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py:1020)
   - `overnight`: [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py:2023)
   - `condition_entry/exit`: [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py:2061), [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py:2090)
   - `eod_top5`: [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py:2165)
4. `response_schema` registry 묶음은 코드에 생겼다.
   - [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py:28)
   - [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py:1296)
   - [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py:326)
   - 기본값은 `GEMINI_RESPONSE_SCHEMA_REGISTRY_ENABLED=False`라 live 응답 분포는 바꾸지 않는다.
5. 실전 smoke/test 근거는 최소 수준까지만 있다.
   - cache/gatekeeper/condition/eod regression: [test_ai_engine_cache.py](/home/ubuntu/KORStockScan/src/tests/test_ai_engine_cache.py:114)
   - live prompt contract smoke: [test_gemini_live_prompt_smoke.py](/home/ubuntu/KORStockScan/src/tests/test_gemini_live_prompt_smoke.py:271)
   - `schema registry` 인입과 6 endpoint coverage는 [test_ai_engine_api_config.py](/home/ubuntu/KORStockScan/src/tests/test_ai_engine_api_config.py:122)에 추가했다.

## 3. Cohort / Guard

1. `baseline cohort`
   - 현재 `main` Gemini live 경로 전체
   - `GEMINI_SYSTEM_INSTRUCTION_JSON_ENABLED=False`
   - `GEMINI_JSON_DETERMINISTIC_CONFIG_ENABLED=False`
2. `candidate live cohort`
   - 없음. same-day enable 금지.
3. `observe-only cohort`
   - `require_json=True` 경로 한정 schema ingress 설계
   - endpoint registry 메모와 contract test 추가 change set
4. `excluded cohort`
   - `generate_realtime_report()` markdown/text path
   - `analyze_scanner_results()` market briefing prose path
   - active entry/holding canary와 same-day 동시 승격
5. `rollback owner`
   - Gemini P1/P2는 `main` 판정분포를 바꾸므로 `flag-off 즉시 복귀` 가능한 단일 조작점이 문서/코드에 함께 있어야 한다.

## 4. 6 Endpoint Matrix

| endpoint | current contract | next schema name | fallback owner | required tests | status |
| --- | --- | --- | --- | --- | --- |
| `entry/watch` | `action/score/reason` | `entry_v1` | `_call_gemini_safe()` raw `json.loads -> regex` fallback + `_normalize_scalping_action_schema()` | BUY/WAIT/DROP contract, parse_fail, submitted/full/partial observe field | flag-off wired |
| `holding/exit` | compat `action_v2(HOLD/TRIM/EXIT)` + legacy `action` | `holding_exit_v1` | `_normalize_scalping_action_schema(prompt_type=holding/exit)` | HOLD/TRIM/EXIT compat, partial/full split, missed_upside linkage | flag-off wired |
| `overnight` | `action/confidence/reason/risk_note` | `overnight_v1` | method-local conservative fallback `SELL_TODAY` | overnight JSON contract + fallback preservation | flag-off wired |
| `condition_entry` | `decision/confidence/order_type/position_size_ratio/invalidation_price/reasons/risks` | `condition_entry_v1` | method-local `SKIP` fallback | contract test + fallback list fields | flag-off wired |
| `condition_exit` | `decision/confidence/trim_ratio/new_stop_price/reason_primary/warning` | `condition_exit_v1` | method-local `HOLD` fallback | contract test + fallback text fields | flag-off wired |
| `eod_top5` | removed | removed | removed by 2026-05-21 EOD TOP5 cleanup | no longer an acceptance endpoint | removed |

## 5. Acceptance

1. `P1 system_instruction`
   - 승인 상태: `flag-off 준비 완료`, `live enable 미승인`
   - required proof:
     - `baseline/candidate/observe-only/excluded cohort` 고정
     - parse_fail/consecutive_failures/ai_disabled observe fields 명시
     - rollback owner 명시
2. `P1 deterministic JSON config`
   - 승인 상태: `flag-off 준비 완료`, `live enable 미승인`
   - required proof:
     - `require_json=True` 전용
     - text/briefing path 제외
     - contract drift 비교 기준 명시
3. `P2 schema registry`
   - 승인 상태: `flag-off 코드 묶음 반영`, `실전 미승인`
   - not now reason:
     - endpoint별 live response_schema 효과 검증 전
     - active entry/holding canary와 same-day 원인귀속 충돌 위험

## 6. 다음 액션

1. `2026-04-30`에는 `main live enable`이 아니라 `flag-off schema registry load + contract 관찰`만 확인한다.
2. `GEMINI_SYSTEM_INSTRUCTION_JSON_ENABLED`, `GEMINI_JSON_DETERMINISTIC_CONFIG_ENABLED`는 관찰필드/rollback 메모 없이 켜지지 않는다.
3. `GEMINI_RESPONSE_SCHEMA_REGISTRY_ENABLED`도 live enable 전 별도 rollback owner와 cohort가 필요하다.

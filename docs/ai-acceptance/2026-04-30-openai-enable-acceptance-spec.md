# 2026-04-30 OpenAI Enable Acceptance / Transport Parity Spec

작성일: `2026-04-30 KST`  
Source: [2026-04-30-openai-parity-responses-ws-review-report.md](/home/ubuntu/KORStockScan/docs/ai-acceptance/2026-04-30-openai-parity-responses-ws-review-report.md), [2026-04-29-gemini-enable-acceptance-spec.md](/home/ubuntu/KORStockScan/docs/ai-acceptance/2026-04-29-gemini-enable-acceptance-spec.md), [2026-04-29-deepseek-enable-acceptance-spec.md](/home/ubuntu/KORStockScan/docs/ai-acceptance/2026-04-29-deepseek-enable-acceptance-spec.md)  
대상 코드: [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py), [ai_response_contracts.py](/home/ubuntu/KORStockScan/src/engine/ai_response_contracts.py), [test_ai_engine_openai_transport.py](/home/ubuntu/KORStockScan/src/tests/test_ai_engine_openai_transport.py), [test_ai_engine_api_config.py](/home/ubuntu/KORStockScan/src/tests/test_ai_engine_api_config.py)

## 1. 판정

1. `P1 JSON deterministic config`와 `P2 response schema registry`는 `flag default OFF` 상태의 관찰/설계 승인까지만 허용한다.
2. `P3 Responses WS transport`는 `2026-04-30` 코드 반영과 회귀 테스트까지 끝났지만, 여전히 `shadow-first flag-off` 관찰 단계다. same-day live enable은 미승인이다.
3. 다음 범위는 `OpenAI live routing 전환`이 아니라 `schema registry load/contract 관찰 + WS provenance/timeout/fallback 관찰`이다.

## 2. 근거

1. OpenAI JSON 경로는 Gemini와 같은 공용 schema registry를 이미 공유한다.
   - [ai_response_contracts.py](/home/ubuntu/KORStockScan/src/engine/ai_response_contracts.py)
   - [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py)
2. endpoint별 계약은 Gemini와 같은 schema registry를 공유한다. 단, `condition_entry/condition_exit`는 `2026-05-02` 이후 runtime 전용 프롬프트/endpoint에서 제외하고 기존 scalping 라우팅 결과를 호환 응답 형태로 변환한다.
   - `entry_v1`
   - `holding_exit_v1`
   - `overnight_v1`
   - `eod_top5_v1`은 2026-05-21 EOD TOP5 제거로 제외
3. 하지만 OpenAI는 현재 `main` live 스캘핑 기준 엔진이 아니라 parity/transport 관찰 대상이다.
   - `OPENAI_TRANSPORT_MODE=http`
   - `OPENAI_RESPONSES_WS_ENABLED=False`
   - `OPENAI_RESPONSE_SCHEMA_REGISTRY_ENABLED=False`
   - `OPENAI_JSON_DETERMINISTIC_CONFIG_ENABLED=False`
4. `Responses WS`는 phase1 scope를 제한해 반영됐다.
   - 허용 endpoint: `analyze_target`, `analyze_target_shadow_prompt`
   - 제외 endpoint: `condition_entry`, `condition_exit`, `realtime_report`, `gatekeeper`, `overnight`, `EOD` text/prose path
5. fail-closed guard도 이미 코드와 테스트로 잠겼다.
   - `request_id mismatch`와 `late response`는 HTTP fallback으로 재해석하지 않고 fail-closed
   - BUY-side timeout/parse failure는 `DROP/SKIP` 보수 폴백
6. 현재 검증 근거는 최소 acceptance 수준을 충족한다.
   - `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_ai_engine_openai_transport.py`
   - `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_ai_engine_api_config.py src/tests/test_ai_engine_cache.py`

## 3. Cohort / Guard

1. `baseline cohort`
   - 현재 OpenAI HTTP contract path
   - `OPENAI_TRANSPORT_MODE=http`
   - `OPENAI_RESPONSES_WS_ENABLED=False`
   - `OPENAI_RESPONSE_SCHEMA_REGISTRY_ENABLED=False`
   - `OPENAI_JSON_DETERMINISTIC_CONFIG_ENABLED=False`
2. `candidate live cohort`
   - 없음. same-day live enable 금지.
3. `observe-only cohort`
   - `openai_responses_ws_shadow_flag_off`
   - flag-off schema registry/transport provenance 관찰
4. `excluded cohort`
   - `realtime_report/gatekeeper` text path
   - `overnight/EOD` prose path의 live 분포 변경
   - Gemini/DeepSeek 라우팅 우열 비교
5. `rollback owner`
   - `OPENAI_TRANSPORT_MODE`
   - `OPENAI_RESPONSES_WS_ENABLED`
   - `OPENAI_RESPONSE_SCHEMA_REGISTRY_ENABLED`
   - `OPENAI_JSON_DETERMINISTIC_CONFIG_ENABLED`

## 4. Acceptance Table

| axis | enable acceptance | not now reason | required proof | next slot |
| --- | --- | --- | --- | --- |
| `JSON deterministic config` | `require_json=True` 전용, text/prose path 제외, rollback flag 1개로 즉시 복귀 가능 | 현재는 parity 관찰 우선이며 live contract drift를 아직 보지 않았다 | endpoint별 contract test, parse_fail drift 없음, excluded cohort 고정 | `2026-05-04 PREOPEN` |
| `response schema registry` | 6 endpoint schema name/fallback/test matrix 고정, live flag 기본 OFF, endpoint별 후처리와 충돌 없음 | schema는 wiring 됐지만 live enable 관찰과 cohort 기준이 아직 없다 | `test_ai_engine_api_config`, `test_ai_engine_cache`, endpoint별 fallback owner 메모 | `2026-05-04 PREOPEN` |
| `Responses WS transport` | `request_id mismatch=0`, `late_discard=0`, `http fallback<=2%`, `parse_fail<=0.5%`, `timeout_reject_rate<=1%`, excluded cohort 고정 | private low-level recv dependency와 live queue/timeout 분포가 아직 미검증 | runtime metrics, request_id correlation, fail-closed 회귀 테스트, restart provenance | `2026-05-04 INTRADAY/POSTCLOSE` |
| `previous_response_id reuse` | 종목 간 오염 방지 기준과 동종목 재사용 근거가 같이 있어야 함 | 현재는 symbol/cache_key 단위 provenance만 있고 상태오염 회피가 우선 | request correlation 메모, symbol-scope proof, rollback owner | backlog only |
| `OpenAI live routing promotion` | `submitted/full/partial`, `COMPLETED + valid profit_rate`, parse_fail, timeout, transport provenance가 Gemini baseline과 분리 비교 가능 | Plan Rebase 기간의 live 스캘핑 AI 기준선은 Gemini 고정이고 entry/holding active canary와 원인귀속 충돌 위험이 크다 | 별도 routing workorder, live cohort, rollback guard, routing diff test | backlog only |

## 5. Gemini / DeepSeek 연동 기준

1. Gemini와 동일하게 `6 endpoint schema/fallback/test matrix`를 공용 registry 기준으로 잠근다.
2. DeepSeek와 동일하게 `flag-off acceptance -> observe-only provenance -> 별도 live enable` 순서를 강제한다.
3. OpenAI는 Gemini처럼 `main` 실전 분포를 아직 소유하지 않으므로, 당분간은 `engine replacement`가 아니라 `contract parity + transport provenance` 축으로만 관리한다.
4. 세 엔진 공통으로 `text/prose path`와 `require_json path`를 섞어 같은 acceptance로 판정하지 않는다.

## 6. 다음 액션

1. `2026-05-04`에는 `live enable`이 아니라 `flag-off schema registry/transport load`와 `WS shadow metrics`만 확인한다.
2. `OPENAI_RESPONSE_SCHEMA_REGISTRY_ENABLED`와 `OPENAI_JSON_DETERMINISTIC_CONFIG_ENABLED`는 rollback owner와 contract drift 기준 없이 켜지지 않는다.
3. `OPENAI_RESPONSES_WS_ENABLED`는 `request_id mismatch=0`, `late_discard=0`이 shadow 기준으로 먼저 닫히기 전까지 OFF 유지다.
4. OpenAI live routing 승격 검토는 Gemini/DeepSeek acceptance와 별개 backlog로 남기고, active entry/holding canary와 같은 날 병행하지 않는다.

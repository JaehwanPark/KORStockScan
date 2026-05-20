# 2026-04-29 Gemini/DeepSeek Acceptance Bundle 작업결과서

작성시각: `2026-04-29 14:20 KST`  
기준 Source/Section: [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-29-stage2-todo-checklist.md) / `장중 설계/후속 체크리스트 (12:20~14:20)`  
관련 문서: [2026-04-29-gemini-enable-acceptance-spec.md](/home/ubuntu/KORStockScan/docs/ai-acceptance/2026-04-29-gemini-enable-acceptance-spec.md), [2026-04-29-deepseek-enable-acceptance-spec.md](/home/ubuntu/KORStockScan/docs/ai-acceptance/2026-04-29-deepseek-enable-acceptance-spec.md)

---

## 1. 판정

1. 이번 change set은 `Gemini/DeepSeek 실전 enable`이 아니라 `flag-off acceptance bundle` 반영으로 닫는다.
2. Gemini는 endpoint별 `response_schema registry ingress + callsite wiring + contract test`까지 반영됐다.
3. DeepSeek는 `retry acceptance snapshot + retry log field + contract test`까지 반영됐다.
4. 두 엔진 모두 기본 flag는 OFF 유지이며, same-day runtime 분포 변경은 의도적으로 만들지 않았다.

## 2. 근거

### 2-1. Gemini

1. [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py:28)에 `GEMINI_RESPONSE_SCHEMA_REGISTRY`를 추가했다.
2. [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py:1291) `_call_gemini_safe()`에 `schema_name` 인자를 추가했고, [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py:1324)에서 `GEMINI_RESPONSE_SCHEMA_REGISTRY_ENABLED`가 켜진 경우만 `response_schema`를 주입한다.
3. 6개 endpoint callsite에 `schema_name`을 연결했다.
   - `entry/watch`: [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py:1131), [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py:1750)
   - `overnight`: [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py:2141)
   - `condition_entry`: [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py:2180)
   - `condition_exit`: [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py:2210)
   - `eod_top5`: [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py:2287)
4. [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py:326)에 `GEMINI_RESPONSE_SCHEMA_REGISTRY_ENABLED=False`를 추가해 기본 동작을 유지했다.
5. fallback은 그대로 유지된다. 즉 `response_schema`는 `flag-off ingress`만 생겼고, 현재 live는 여전히 `json.loads -> regex fallback` 경로를 탄다.

### 2-2. DeepSeek

1. [ai_engine_deepseek.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_deepseek.py:545)에 `_build_retry_acceptance_snapshot()`을 추가했다.
2. [ai_engine_deepseek.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_deepseek.py:591)에서 `context_name`, `target_model`, `context_aware_backoff_enabled`, `live_sensitive`, `base_sleep_sec`, `jitter_max_sec`, `max_sleep_sec`, `lock_scope`를 묶은 acceptance snapshot을 만든다.
3. retry/rotate 로그에 `retry_acceptance=...`를 함께 남기도록 바꿨다.
   - rate-limit 계열: [ai_engine_deepseek.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_deepseek.py:628)
   - server/unavailable 계열: [ai_engine_deepseek.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_deepseek.py:642)
4. `DEEPSEEK_CONTEXT_AWARE_BACKOFF_ENABLED` 기본값은 그대로 OFF라 remote sleep 정책은 바뀌지 않는다.

## 3. 코드리뷰 포인트

1. [필수] Gemini registry shape가 현재 normalization contract와 충돌하지 않는지 본다. 특히 `holding_exit_v1`의 `action enum`, `condition_*`의 필수 필드를 parser와 정합성. `eod_top5_v1`은 2026-05-21 EOD TOP5 제거로 검토 범위에서 제외한다.
2. [권장] `_call_gemini_safe()`의 `response_schema` 주입이 `require_json=True` 경로에만 한정되는지, prose/text path에 새 부작용이 없는지 본다.
3. [권장] DeepSeek acceptance snapshot이 retry 로그에만 붙고 일반 성공 경로에는 노이즈를 추가하지 않는지 본다.
4. [권장] `live_sensitive` 판단이 `tier3 != report/eod`라는 가정에 묶여 있으므로, 추후 model routing 변경 시 acceptance snapshot 의미가 유지되는지 본다.
5. [권장] 이번 change set은 `flag-off bundle`이므로 runtime enable을 암묵적으로 유도하는 기본값 변경이 없는지 다시 확인한다.
6. [권장] 공통 caller 관점에서 DeepSeek의 `analyze_condition_target`, `evaluate_condition_gatekeeper` 인터페이스 gap이 없는지 점검한다.

## 4. 테스트 / 검증

1. `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_ai_engine_api_config.py src/tests/test_ai_engine_cache.py`
   - 결과: `23 passed`
2. 추가된 핵심 테스트:
   - [test_ai_engine_api_config.py](/home/ubuntu/KORStockScan/src/tests/test_ai_engine_api_config.py:122) `Gemini response_schema` 인입 검증
   - [test_ai_engine_api_config.py](/home/ubuntu/KORStockScan/src/tests/test_ai_engine_api_config.py:159) 6 endpoint registry coverage 검증
   - [test_ai_engine_api_config.py](/home/ubuntu/KORStockScan/src/tests/test_ai_engine_api_config.py:220) DeepSeek retry acceptance snapshot live/report 분리 검증
3. `git diff --check`
   - 결과: 통과

## 5. 미완 / 가드

1. Gemini는 `flag-off schema registry`까지만 반영됐고 live enable acceptance는 아직 없다.
2. DeepSeek는 retry acceptance 관찰성만 보강됐고 `context-aware backoff` live enable은 아직 아니다.
3. 따라서 내일 확인할 것은 `효과`가 아니라 `flag-off load/contract/log visibility`다.
4. 후속 슬롯은 이미 [2026-04-30-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-30-stage2-todo-checklist.md:63)에 고정했다.
   - `GeminiSchemaIngress0430`
   - `DeepSeekRemoteAcceptance0430`
   - `GeminiSchemaContractCarry0430` (필수)
   - `DeepSeekAcceptanceCarry0430` (권장)
   - `DeepSeekInterfaceGap0430` (권장)

## 6. 결론

이번 결과물은 “문서만 만들고 종료”가 아니라, `문서 + 코드 ingress + 테스트`까지 묶은 acceptance bundle이다. 다만 `실전 enable`은 아니다. 코드리뷰에서는 live 변화가 아니라 `flag-off 상태에서의 계약 정합성`과 `후속 enable 시 rollback 가능성`을 우선 보면 된다.

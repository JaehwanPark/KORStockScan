# Holding Flow Override 코드 리뷰 결과보고서

작성일: `2026-05-01 KST`

## 1. 판정

- `holding_flow_override` 구현은 요청된 운영 목적과 대체로 일치한다.
- 이 변경의 성격은 `active canary`가 아니라 `운영 override`다. 따라서 `soft_stop_micro_grace`나 `bad_entry_refined_canary`의 성과와 합산하지 않고 별도 cohort로 판정해야 한다.
- 장중 보유/청산 후보와 오버나이트 `SELL_TODAY` 후보에 공통 flow 재검문이 연결되었고, hard stop/protect/order safety는 override 대상에서 제외됐다.
- `15:20 KST` 오버나이트 선행 판정, 추가악화 하한 `0.80%p`, 누적 보류 상한 `90초`도 코드와 문서에 반영됐다.
- 현재 기준 치명적 정합성 결함은 발견하지 못했다. 다만 `next_review_sec`는 결과 payload에 저장되지만 실제 cadence 제어는 전역 runtime rule(`30~90초`, `0.35%p`)이 우선한다는 점을 잔여 리스크로 둔다.

## 1.1 분류 메모

- `shadow`: 해당 없음. 이번 change set은 실판단을 실제로 바꾸므로 shadow 분류가 아니다.
- `canary`: 해당 없음. `holding_flow_override`는 튜닝 가설 검증 owner가 아니라 실전 운영 override owner다.
- `cohort`: 최소 `baseline holding/overnight cohort`, `override applied cohort`, `force-exit cohort`, `excluded hard/protect/order-safety cohort`를 분리해야 한다.
- `live 유지/종료 기준`: `defer -> 후행 EV`, `force_reason`, `hard/protect bypass=0`, `overnight hold/revert` 분포가 장후 판정셋에 같이 있어야 한다.

## 2. 변경 범위

### 2.1 AI 계약과 flow prompt

- `src/engine/ai_response_contracts.py`
  - `holding_exit_flow_v1` schema 추가
  - 필수 응답: `action`, `score`, `flow_state`, `thesis`, `evidence`, `reason`, `next_review_sec`

- `src/engine/ai_engine.py`
  - `SCALPING_HOLDING_FLOW_SYSTEM_PROMPT` 추가
  - `evaluate_scalping_holding_flow(...)` 추가
  - 최근 tick 30개, 분봉 60개, 최근 flow review history, 당일 고점 대비 위치, 수급/호가 요약을 묶어 흐름 판정을 수행
  - 단일 score cutoff 금지와 `흡수/회복/분배/붕괴/소강` 중심 판단을 프롬프트에 명시

### 2.2 장중 청산 후보 override

- `src/engine/sniper_state_handlers.py`
  - `scalp_soft_stop_pct`
  - `scalp_ai_momentum_decay`
  - `scalp_trailing_take_profit`
  - `scalp_bad_entry_refined_canary`

위 4개 exit rule에 대해 기존 전량청산 직전에 `_evaluate_holding_flow_override(...)`를 통과하도록 변경했다.

- flow `EXIT`면 기존 청산 유지
- flow `HOLD/TRIM`이면 전량청산 보류
- `AI unavailable`, `parse_fail`, `ws_stale`, `context_fetch_failed`, `no_recent_ticks`, `max_defer_sec`, `worsen_floor`는 기존 청산 허용
- 최초 후보 이후 review cadence는 `최소 30초`, `최대 90초`, `손익 변화 0.35%p` 규칙으로 제어

### 2.3 오버나이트 선행 판정과 복귀 로직

- `src/utils/constants.py`
  - `SCALPING_OVERNIGHT_DECISION_TIME="15:20:00"`
  - flow override 관련 runtime rule / env override 추가

- `src/engine/sniper_time.py`
  - `TIME_SCALPING_OVERNIGHT_DECISION` 기본값을 `15:20:00`으로 변경

- `src/engine/sniper_overnight_gatekeeper.py`
  - `SELL_TODAY` 결과에 한해 `_apply_overnight_flow_override(...)` 1회 재검문 추가
  - flow `HOLD/TRIM`이면 `HOLD_OVERNIGHT`로 뒤집고 `overnight_flow_override_hold` stage를 적재
  - hard stop 위험, 잔고/주문 정합성 문제, context fetch 실패 시 override 없이 기존 `SELL_TODAY` 유지

- `src/engine/sniper_state_handlers.py`
  - `15:20~15:30` 사이 `overnight_flow_override_hold` 상태에서 추가악화 `0.80%p` 도달 시 `overnight_flow_worsen_revert`로 당일청산 복귀

### 2.4 문서와 운영 체크리스트

- `docs/plan-korStockScanPerformanceOptimization.rebase.md`
  - `holding_flow_override`를 기존 튜닝 관찰축과 별개인 운영 override로 명시

- `docs/checklists/2026-05-04-stage2-todo-checklist.md`
  - `[HoldingFlowOverride0504-Preopen]`
  - `[HoldingFlowOverride0504-Intraday]`
  - `[HoldingFlowOverride0504-Overnight]`
  - `[HoldingFlowOverride0504-Postclose]`

## 3. 코드 리뷰 포인트

### 3.1 요청사항 충족 여부

- 보유/청산 AI가 단일 순간 점수로 바로 전량청산하던 경로를 flow 재검문 뒤로 이동시켰다.
- `TRIM`은 v1에서 부분청산 주문이 아니라 전량청산 보류 의미로만 해석된다.
- hard stop/protect/order safety 우선순위는 유지된다.
- 오버나이트는 기존 `15:30`이 아니라 `15:20` 선행 판정으로 바뀌었다.

### 3.2 운영 guard 정합성

- 최초 후보 대비 추가악화 `0.80%p`는 장중/오버나이트 모두 공통 guard로 반영됐다.
- 보류 무한 연장을 막기 위해 `90초` 상한이 들어갔다.
- stale WS와 context fetch 실패는 fail-open이 아니라 기존 청산 허용으로 닫았다.

### 3.3 관측성

- 신규/확장 pipeline stage:
  - `holding_flow_override_review`
  - `holding_flow_override_defer_exit`
  - `holding_flow_override_exit_confirmed`
  - `holding_flow_override_force_exit`
  - `overnight_flow_override_review`
  - `overnight_flow_override_hold`
  - `overnight_flow_override_revert_sell_today`

- `holding_flow_review_history`를 메모리 상태에 남겨 이후 재판정과 오버나이트 입력에서 재사용한다.

## 4. 검증 결과

- `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_holding_ai_fast_signature.py src/tests/test_trade_review_report.py src/tests/test_holding_exit_observation_report.py src/tests/test_holding_flow_override.py`
  - `13 passed`

- `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_sniper_overnight_gatekeeper.py`
  - `7 passed`

- `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/ai_engine.py src/engine/sniper_state_handlers.py src/engine/sniper_overnight_gatekeeper.py src/engine/ai_response_contracts.py src/utils/constants.py`
  - 통과

- `PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500`
  - checklist parser 검증 통과
  - `HoldingFlowOverride0504-*` 4개 항목 파싱 확인

추가 확인:

- `src/tests/test_gemini_live_prompt_smoke.py`
  - 실패
  - 원인: Gemini API `503 UNAVAILABLE` (`models/gemini-3.1-flash-lite-preview` 고부하)
  - 코드 회귀라기보다 외부 모델 가용성 문제로 해석한다.

## 5. 잔여 리스크

- `next_review_sec`는 AI 응답에 포함되지만 현재 runtime cadence 결정은 전역 rule이 소유한다.
  - 즉, 모델이 `45초`를 제안해도 실제 재호출은 `30~90초 + 0.35%p` 규칙으로만 닫힌다.
  - v2에서 `model hint`를 runtime scheduler에 반영할지 별도 결정이 필요하다.

- flow review는 hot path에서 `ka10003`/`ka10080` 조회를 수행한다.
  - 현재는 대상 exit rule을 제한하고 cadence guard를 둬서 통제하지만, 실제 장중 동시 후보 수가 커지면 IO/latency 분포 재점검이 필요하다.

- 오버나이트 `HOLD_OVERNIGHT` 전환은 메모리 상태(`ACTIVE_TARGETS`)를 전제로 한다.
  - DB 상태와 메모리 상태가 어긋난 비정상 케이스에서는 보수적으로 `SELL_TODAY` 유지 경로를 타도록 했지만, 실제 운영 로그에서 해당 skip 분포를 따로 확인해야 한다.

## 6. 최종 의견

- 이번 변경은 canary 축이 아니라 운영 override로서 성격이 명확하고, 기존 청산 rule을 무조건 약화시키지 않고 `flow EXIT`와 fail-safe 조건에서 원래 청산을 유지하도록 설계된 점이 적절하다.
- 코드, 테스트, 문서, 체크리스트가 한 세트로 정렬돼 있어 `2026-05-04 KST` 장전 로드 준비 수준은 충족했다.
- 운영 판단은 `HoldingFlowOverride0504-*` 체크리스트 기준으로 장중 `defer/force/exit_confirmed` 분포와 오버나이트 `hold/revert` 분포를 분리 관찰한 뒤 닫는 것이 맞다.

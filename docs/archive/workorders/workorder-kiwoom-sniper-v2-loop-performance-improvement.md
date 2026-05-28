# 작업지시서: KiwoomSniperV2 루프/동기 I/O 성능개선

작성일: `2026-04-25 KST`  
실행 기준 슬롯: `2026-04-27 POSTCLOSE 16:10~16:35 KST` 1차 착수 판정  
대상: 운영 트레이더 / Codex  
기준 문서:

1. [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
2. [2026-04-27-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-27-stage2-todo-checklist.md)
3. [kiwoom_sniper_v2_performance_review.md](/home/ubuntu/KORStockScan/docs/code-reviews/kiwoom_sniper_v2_performance_review.md)

---

## 1. 판정

`kiwoom_sniper_v2_performance_review.md`의 핵심 진단은 대체로 타당하다. 현재 `run_sniper()`는 웹소켓 push 데이터를 메모리에 유지하면서도, 메인 루프가 `time.sleep(1)`과 동기 DB/API/AI 호출을 같은 스레드에서 처리한다. 이 구조는 `entry_armed -> budget_pass -> latency_block/submitted` 병목을 줄이려는 Plan Rebase 목표와 직접 충돌한다.

다만 `time.sleep(1)`을 바로 `10~50ms`로 낮추는 즉시 변경은 승인하지 않는다. 현재 루프 안에는 DB polling, 주문가능금액 조회, Kiwoom 주문/취소, AI 분석, 계좌동기화 스레드 생성이 남아 있어, sleep만 줄이면 기대값 개선보다 API 폭주, CPU 점유, 중복 주문 판단, 로그 과증폭이 먼저 생길 수 있다.

1차 개선축은 실전 전략 canary가 아니라 운영 성능/계측 개선이다. live 매매 판단값을 바꾸지 않고 `loop lag`, 동기 I/O 소요, blocker 분포를 먼저 계측한 뒤, 다음 코드 변경을 한 번에 한 축씩 적용한다.

---

## 2. 코드 정합성 검토

| 보고서 주장 | 코드 확인 | 판정 |
| --- | --- | --- |
| 메인 루프 마지막 `time.sleep(1)`이 반응 지연을 만든다 | [kiwoom_sniper_v2.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_sniper_v2.py:1344) | 맞음. 단독 변경 금지, 계측/가드 선행 |
| `DB.get_active_targets()`가 5초마다 동기 호출된다 | [kiwoom_sniper_v2.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_sniper_v2.py:1201), [db_manager.py](/home/ubuntu/KORStockScan/src/database/db_manager.py:445) | 맞음. `pd.read_sql` + dict 변환 포함 |
| `_resolve_stock_marcap()`이 루프 중 DB를 조회한다 | [kiwoom_sniper_v2.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_sniper_v2.py:192), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:878) | 조건부 맞음. `stock['marcap']`이 있으면 캐시되며 `get_active_targets()`도 marcap을 채운다. 캐시 미스 경로만 차단 대상 |
| WATCHING/HOLDING AI 호출이 동기 실행된다 | [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:2239), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:3804) | 맞음. 이미 fast reuse 일부는 있으나, 네트워크 호출은 메인 루프를 막는다 |
| 주문/취소 API가 동기 실행된다 | [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:1588), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:3235), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:3453) | 맞음. 주문 worker 도입 후보 |
| 매 루프 리스트 재생성이 있다 | [kiwoom_sniper_v2.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_sniper_v2.py:1340) | 맞음. 단, 40개 내외에서는 1차 병목 아님 |
| 90초마다 계좌 동기화 스레드가 새로 생성된다 | [kiwoom_sniper_v2.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_sniper_v2.py:1268) | 맞음. 저위험 개선 후보 |

보고서에서 빠진 추가 병목도 있다. `handle_watching_state()`는 최종 주문 판단 직전 [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:2894)에서 `kiwoom_orders.get_deposit()`을 동기 호출하고, 추가매수도 [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:5032)에서 같은 경로를 쓴다. `get_deposit()`은 HTTP timeout/retry/cache fallback을 포함하므로 [kiwoom_orders.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_orders.py:143) 기준 별도 계측 대상이다.

---

## 3. 실행 원칙

1. 목표는 루프 지연 자체 축소가 아니라 `submitted/full_fill/partial_fill/COMPLETED + valid profit_rate`까지 이어지는 기대값 개선이다.
2. 전략 판단 변경과 성능 구조 변경을 같은 canary로 묶지 않는다.
3. sleep 단축, DB polling 분리, 주문 worker, AI worker는 각각 별도 조작점이다.
4. `fallback_scout/main`, `fallback_single`, `latency fallback split-entry` 재개는 금지한다.
5. 성능개선 판정에서도 손익보다 `budget_pass -> submitted`, `latency_block`, `quote_fresh_latency_pass_rate`, `gatekeeper_eval_ms_p95`, 주문 실패/중복 제출 여부를 먼저 본다.
6. full fill과 partial fill은 결과 해석에서 분리한다.
7. `NULL`, 미완료 상태, fallback 정규화 값은 성과 기준으로 쓰지 않는다.

---

## 4. 작업 범위

### 4-1. P0 계측 보강

목표: live 동작을 바꾸지 않고 병목을 계량한다.

1. `run_sniper()` 루프 최상단/종단에 `loop_started_ts`, `loop_elapsed_ms`, `sleep_ms`, `target_count`, `watching_count`, `holding_count`를 샘플링한다.
2. 동기 I/O 구간별 elapsed를 기록한다.
   - `db_active_targets_ms`
   - `deposit_lookup_ms`
   - `buy_order_submit_ms`
   - `sell_order_submit_ms`
   - `cancel_order_ms`
   - `watching_ai_ms`
   - `holding_ai_ms`
   - `account_sync_dispatch_ms`
3. 로그/스냅샷 필드는 기존 `performance_tuning` 계열에 붙이되, 손익 필드와 합산하지 않는다.
4. 테스트에는 `COMPLETED + valid profit_rate` 필터와 무관한 운영 계측임을 명시한다.

완료 기준:

- `src/tests/test_performance_tuning_report.py` 또는 신규 테스트에서 loop/I/O 계측 필드가 report dict에 포함된다.
- 미계측 구간은 `0` 또는 `"-"`로 남기되 p95 계산에 sentinel이 섞이지 않는다.
- live 판단값, 주문 수량, latency gate 결정값이 바뀌지 않는다.

### 4-2. P1 저위험 구조개선

목표: 주문/AI worker 도입 전, 루프 안정성을 해치지 않는 변경만 적용한다.

1. `periodic_account_sync`는 매번 새 `threading.Thread`를 만들지 말고 단일 `ThreadPoolExecutor(max_workers=1)` 또는 전용 worker로 교체한다.
2. `time.time()`/`datetime.now()`는 메인 루프에서 `now_ts`, `now_dt`를 만든 뒤 하위 함수로 점진 전달한다. 전면 리팩토링 대신 hot path부터 적용한다.
3. `_resolve_stock_marcap()`은 프로세스 레벨 TTL 캐시를 우선 조회하고, 캐시 미스 때도 동일 코드 반복 DB 조회를 막는다.
4. `targets[:] = [...]`는 sleep 단축 전까지는 유지 가능하다. dict 전환은 상태 동기화 리스크가 있어 P2로 둔다.

완료 기준:

- 기존 테스트 통과.
- 신규 테스트에서 `DB.get_latest_marcap()` 중복 호출이 같은 code/TTL 안에서 1회 이하임을 확인한다.
- 계좌동기화 worker가 중복 실행 중이면 다음 실행을 skip 또는 coalesce한다.

### 4-3. P2 루프 tick 단축 canary

목표: 계측과 저위험 개선 후에만 sleep을 낮춘다.

1. 상수 또는 env로 `SNIPER_LOOP_SLEEP_SEC`를 추가한다.
2. 기본값은 기존 `1.0` 유지 또는 `0.25` 이하로 내리기 전에 P0/P1 계측 기준을 충족해야 한다.
3. canary 값은 `0.25 -> 0.10 -> 0.05` 순서로만 낮춘다.
4. rollback guard를 명시한다.
   - `loop_elapsed_ms_p95`가 sleep 목표의 2배 초과
   - Kiwoom REST 오류/timeout 증가
   - `order_leg_request` 대비 `order_bundle_submitted` 불일치 증가
   - `fallback_regression >= 1`
   - CPU 과점유 또는 로그 backlog 증가

완료 기준:

- `budget_pass_to_submitted_rate` 또는 `quote_fresh_latency_pass_rate`가 개선 방향을 보인다.
- `submitted/full_fill/partial_fill` 품질이 baseline 대비 악화되지 않는다.
- fallback 회귀가 없다.

### 4-4. P3 주문 worker 설계

목표: 주문 실행 I/O를 루프에서 분리하되, 중복 주문과 상태 오염을 막는다.

1. 전용 `OrderRequest` queue를 만들고 idempotency key를 `record_id + code + side + entry_bundle_id/exit_rule`로 고정한다.
2. 메인 루프는 `ORDER_REQUESTED` 또는 기존 `BUY_ORDERED/SELL_ORDERED` 호환 상태를 먼저 기록하고 즉시 복귀한다.
3. worker 결과는 EventBus 또는 receipt store로 회수한다.
4. 매수/매도/취소를 한 worker에 넣되, 우선순위는 `cancel -> sell -> buy`로 둔다.
5. partial fill과 full fill은 worker 결과 처리에서도 분리한다.

완료 기준:

- 주문 중복 방지 테스트.
- worker 실패 시 재시도/보류 상태가 명확하다.
- `restart.flag` 중 worker drain 정책이 문서화된다.

### 4-5. P4 AI worker 설계

목표: AI 네트워크 호출을 분리하되, 오래된 AI 결과가 최신 시세에 적용되지 않게 한다.

1. `AI_ANALYZING`은 새 live 상태로 바로 쓰지 말고 내부 pending marker부터 둔다.
2. 요청에는 `market_signature`, `ws_age`, `price`, `ai_score_before`, `prompt_profile`, `record_id`를 포함한다.
3. 응답 적용 전 `market_signature` stale 여부를 검사한다.
4. `watching_buy_recovery_canary`, `gatekeeper_fast_reuse`, `holding fast reuse` 기존 계측과 충돌하지 않게 profile을 분리한다.

완료 기준:

- stale AI 응답 무시 테스트.
- `ai_parse_ok`, `ai_response_ms`, `ai_prompt_type`, `ai_result_source`가 유지된다.
- BUY 후 미진입 blocker 4축 분해가 유지된다.

---

## 5. 제외 범위

1. 이번 작업지시서만으로 `entry_filter_quality`, `soft_stop_rebound_split`, `gatekeeper_fast_reuse` live 정책을 바꾸지 않는다.
2. `time.sleep(1)` 즉시 `0.01` 변경은 금지한다.
3. `targets` dict 전환은 단독 리팩토링으로 분리하기 전까지 보류한다.
4. `Condition Variable`/Event wake-up 전환은 주문/AI worker 이후 P5 후보로만 둔다.

---

## 6. 검증 명령

```bash
PYTHONPATH=. .venv/bin/pytest -q src/tests/test_performance_tuning_report.py src/tests/test_sniper_entry_latency.py
```

추가 테스트를 만들었다면 해당 테스트 파일을 같은 명령 뒤에 붙인다.

---

## 7. DeepSeek 전달 메모

이 문서는 체크리스트/Project/Calendar 자동관리 대상이 아니라 DeepSeek 구현 지시용이다. 구현 완료 후 별도 코드리뷰 지시가 들어오면, 그때 변경 diff 기준으로 리뷰한다.

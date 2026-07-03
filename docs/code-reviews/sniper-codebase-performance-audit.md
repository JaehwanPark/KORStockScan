# sniper_*.py 코드베이스 성능 점검 리포트

> **작성일**: 2026-04-25  
> **대상**: `src/engine/` 내 `sniper_*.py` 전 모듈 (총 ~18,900라인) + `kiwoom_sniper_v2.py` 메인 루프  
> **목적**: 핫패스 병목 식별, 계측 정합성 검증, 구조적 개선포인트 도출

---

## 목차

1. [메인 루프 (`run_sniper`)](#1-메인-루프-runsniper)
2. [상태 핸들러 (`sniper_state_handlers.py`)](#2-상태-핸들러-sniper_state_handlerspy)
3. [진입 latency 시스템 (`sniper_entry_latency.py`)](#3-진입-latency-시스템-sniper_entry_latencypy)
4. [Gatekeeper replay (`sniper_gatekeeper_replay.py`)](#4-gatekeeper-replay-sniper_gatekeeper_replaypy)
5. [동적 임계값 (`sniper_dynamic_thresholds.py`)](#5-동적-임계값-sniper_dynamic_thresholdspy)
6. [스케일인/진입 상태](#6-스케일인진입-상태)
7. [계측 정합성](#7-계측-정합성)
8. [구조적 개선](#8-구조적-개선)
9. [우선순위 요약](#9-우선순위-요약)

---

## 1. 메인 루프 (`run_sniper`)

**파일**: [`kiwoom_sniper_v2.py`](../../src/engine/kiwoom_sniper_v2.py)

### 1.1 `_ensure_state_handler_deps()` — 매 루프 중복 체크

```python
# kiwoom_sniper_v2.py:309-330
def _ensure_state_handler_deps():
    snapshot = {  # 15개 키
        'kiwoom_token': KIWOOM_TOKEN, 'db': DB, ...
    }
    if any(_STATE_HANDLER_DEPS.get(k) is not v for k, v in snapshot.items()):
        bind_state_dependencies(**snapshot)
        _STATE_HANDLER_DEPS = snapshot
```

- **문제**: 모든 종목의 `handle_watching_state`/`handle_holding_state` 호출마다 실행됨 (매초 N회).
- **영향**: 15개 `dict` 조회 + `any()` 비교. 대부분 deps가 변하지 않으므로 실질적 `no-op`이지만 N=40개 타겟 기준 초당 40회 불필요한 비교.
- **개선안**: 루프 상단에서 1회만 실행하고, deps 변경 시 플래그로 통지. 또는 `_ensure_state_handler_deps`를 루프 시작점으로 이동.

### 1.2 `time.perf_counter()` 오버 측정

```python
# kiwoom_sniper_v2.py:1243
_t0_db = time.perf_counter()
if now_ts - last_db_poll_time > 5:  # 5초에 한번만 실행
    ...
_db_elapsed_ms = (time.perf_counter() - _t0_db) * 1000  # 매초 실행

# kiwoom_sniper_v2.py:1309
_t0_acct = time.perf_counter()
if now_ts - getattr(run_sniper, 'last_account_sync_time', 0) > 90:  # 90초에 한번
    ...
_acct_elapsed_ms = (time.perf_counter() - _t0_acct) * 1000  # 매초 실행
```

- **문제**: `_db_elapsed_ms`는 5초 주기 작업이지만 매초 `perf_counter()` 2회 호출. `_acct_elapsed_ms`는 90초 주기인데 매초 계측.
- **영향**: 초당 `perf_counter()` 4회 중 2회가 불필요. 단일 호출 비용은 ~50ns지만 가독성 대비 미미.
- **개선안**: (선택) 계측 블록을 `if` 내부로 이동. 단, 계측 목적상 매초 실행해도 무방 — **P4 우선순위**.

### 1.3 고정 sleep (1초)

```python
# kiwoom_sniper_v2.py:1419
time.sleep(1)
```

- **문제**: 종목 수와 상관없이 항상 1초 고정. 타겟이 5개일 때와 40개일 때 동일한 대기.
- **영향**: 타겟이 적을 때는 불필요한 idle. 타겟이 많을 때는 1초 내 처리가 밀리면 지연 누적.
- **개선안**: `max(0.1, 1.0 - loop_elapsed_ms/1000)`로 adaptive sleep 도입. 단, `ws_data` 갱신 주기(1초)와의 정합성 확인 필요. **P3.**

### 1.4 `targets[:]` cleanup — 매 루프 새 리스트

```python
# kiwoom_sniper_v2.py:1394
targets[:] = [t for t in targets if t.get('status') not in ['COMPLETED', 'EXPIRED']]
```

- **문제**: 매 루프 `targets` 전체 순회하며 새 리스트 생성.
- **영향**: 타겟 40개 기준 초당 약 40회 필터 체크. 1초에 ~40회 연산 — 부하 자체는 미미.
- **개선안**: COMPLETED/EXPIRED만 `pop`하는 방식으로 변경 가능하나 현재도 충분히 빠름. **P4.**

### 1.5 `_ACCOUNT_SYNC_IN_FLIGHT` 플래그 — 예외 안전성

현재 Fix 4에서 `_run_account_sync_with_cleanup()` 래퍼로 try/finally 처리했지만, `_clear_account_sync_in_flight`가 `finally` 블록에서도 호출되고 `add_done_callback`에서도 호출되어 중복 해제 가능.

- **영향**: 중복 `_ACCOUNT_SYNC_IN_FLIGHT = False` 자체는 무해.
- **개선안**: (선택) `finally` 블록만으로 충분하므로 `add_done_callback` 제거 가능. **P4.**

---

## 2. 상태 핸들러 (`sniper_state_handlers.py`)

**파일**: [`sniper_state_handlers.py`](../../src/engine/sniper_state_handlers.py) — **5,389라인**, 전체 스나이퍼 코드베이스 중 28%

### 2.1 `getattr(TRADING_RULES, ...)` 반복 호출

모듈 전체에 걸쳐 수백 회의 `getattr(TRADING_RULES, 'SCALP_TIME_LIMIT_MIN', 30)` 패턴이 산재.

```python
# sniper_state_handlers.py:1878-1891 — handler 진입부에서만 14회 호출
INVEST_RATIO_KOSDAQ_MIN = getattr(TRADING_RULES, 'INVEST_RATIO_KOSDAQ_MIN', 0.05)
AI_SCORE_THRESHOLD_KOSDAQ = getattr(TRADING_RULES, 'AI_SCORE_THRESHOLD_KOSDAQ', 60)
...
```

- **문제**: `handle_watching_state()` 진입마다 14회 `getattr()` 호출. 각 `getattr`은 `TRADING_RULES` 객체의 `__getattribute__`를 거침.
- **영향**: 타겟 40개 × 초당 1회 × 14회 = 초당 560회 `getattr`.
- **개선안 2a**: `_get_trading_rule(name, default)` 로컬 캐시 래퍼 도입 (dict 캐시로 1회 조회 후 재사용). **P2.**
- **개선안 2b**: 핸들러 진입 시 한 번에 필요한 모든 rule을 `dict`로 스냅샷. **P2.**

### 2.2 `DB.get_session()` 반복 호출

```python
# sniper_state_handlers.py:5185-5209 (buy timeout)
with DB.get_session() as session:
    session.query(...).update(...)

# 동일 패턴이 여러 곳에서 반복 (매수타임아웃, 매도타임아웃, BUY_ORDERED, 매수취소 등)
```

- **문제**: 각 핸들러 상태 전이마다 개별 DB 세션을 열고 닫음. 모든 세션이 동일 DB 연결 풀 사용.
- **영향**: 세션 생성/종료 오버헤드. PostgreSQL 연결 풀을 재사용하더라도 반복 세션 생성 비용은 남음.
- **개선안**: 단일 루프 iteration 내 여러 DB write가 필요한 경우 세션 재사용. **P3.**

### 2.3 `_resolve_stock_marcap()` — 캐시 적용 완료 (Fix 3)

- 수정 완료. 프로세스 레벨 `_MARCAP_CACHE` (TTL 300초) 적용.

### 2.4 `estimate_turnover_hint()` 반복 호출

```python
# sniper_state_handlers.py:1958, 2583, 2615
turnover_hint = estimate_turnover_hint(curr_price, ws_data.get('volume', 0))
```

- **문제**: SCALPING, KOSDAQ_ML, KOSPI_ML 각 경로에서 `estimate_turnover_hint()` + `_resolve_stock_marcap()` 쌍으로 호출.
- **영향**: `marcap`은 캐시되었으나 `turnover_hint`는 동일 `ws_data`에 대해 중복 계산 가능.
- **개선안**: 핸들러 진입 시 `marcap` + `turnover_hint`를 한 번만 계산하고 전달. **P3.**

### 2.5 HOLDING AI review — 동기 API 호출

```python
# sniper_state_handlers.py:3583
recent_ticks = kiwoom_utils.get_tick_history_ka10003(KIWOOM_TOKEN, code, limit=10)
ai_decision = ai_engine.analyze_target(...)
```

- **문제**: `get_tick_history_ka10003()`는 증권사 API 호출로 네트워크 I/O. `ai_engine.analyze_target()`은 LLM API 호출 (수백 ms~수 초).
- **영향**: HOLDING 상태 종목이 많으면 블로킹 호출이 메인 루프 지연의 주요 원인.
- **개선안**: HOLDING AI 리뷰를 별도 `ThreadPoolExecutor`로 분리하거나, AI 호출 자체를 비동기(async)로 전환. 단, 현재 `ai_engine` 인터페이스가 동기이므로 `run_in_executor` 래핑 필요. **P1.**

### 2.6 `_log_entry_pipeline()` / `_log_holding_pipeline()` — 문자열 포맷 오버헤드

```python
# sniper_state_handlers.py:1997-2016 예시
_log_entry_pipeline(
    stock, code, "blocked_overbought",
    fluctuation=f"{fluctuation:.2f}",
    intraday_surge=f"{intraday_surge:.2f}",
    ...
    **_build_ai_overlap_log_fields(...),
    **_build_ai_ops_log_fields(...),
)
```

- **문제**: 진입 pipeline blocker마다 `_build_ai_overlap_log_fields()`와 `_build_ai_ops_log_fields()` 호출. 내부에서 추가 dict 생성.
- **영향**: blocker가 많을 때(예: 조건 불충족으로 빠르게 return하는 경로) 불필요한 dict 병합.
- **개선안**: 로깅 레벨 체크를 먼저 하고 dict를 빌드하거나, lazy evaluation 적용. **P3.**

### 2.7 `normalize_strategy()` / `normalize_position_tag()` 반복

```python
# sniper_state_handlers.py:1893-1894 (handler 진입마다)
strategy = normalize_strategy(stock.get('strategy'))
pos_tag = normalize_position_tag(strategy, stock.get('position_tag'))
```

- **문제**: 40개 타겟 × 초당 1회 = 초당 40회 문자열 정규화.
- **영향**: 대부분의 종목은 동일 strategy/pos_tag 유지. 캐시 가능.
- **개선안**: `stock` dict에 정규화된 값을 1회 저장하고 재사용. **P4.**

---

## 3. 진입 latency 시스템 (`sniper_entry_latency.py`)

**파일**: [`sniper_entry_latency.py`](../../src/engine/sniper_entry_latency.py) — 641라인

### 3.1 `_CACHE_LOCK` 경합

```python
# sniper_entry_latency.py:404
with _CACHE_LOCK:
    _CACHE.update(...)
    quote_health = _CACHE.get_quote_health(code)
```

- **문제**: `_CACHE_LOCK`은 `RLock`이지만, WATCHING 루프에서 모든 종목이 동일 lock 경합.
- **영향**: 종목 수가 늘어날수록 lock 대기 시간 선형 증가.
- **개선안**: `per-code` Lock 또는 lock-free 자료구조(최신 데이터만 필요하므로 `dict` assign으로 충분할 수 있음). **P2.**

### 3.2 `LatencyMonitor.evaluate()` + `EntryPolicy.evaluate()` 객체 생성

```python
# sniper_entry_latency.py:414-440
latency = _LATENCY_MONITOR.evaluate(...)  # LatencyStatus namedtuple 생성
snapshot = build_signal_snapshot(...)      # SignalSnapshot 생성
policy = _ENTRY_POLICY.evaluate(...)       # EntryDecision enum + reason
```

- **문제**: 매 진입 시도마다 2-3개의 중간 객체 생성.
- **영향**: GC 압력. 단, 진입 시도는 실제 BUY 조건 근접 시에만 발생하므로 빈도 낮음.
- **개선안**: (선택) 경량 `dict` 반환으로 전환. **P4.**

---

## 4. Gatekeeper replay (`sniper_gatekeeper_replay.py`)

**파일**: [`sniper_gatekeeper_replay.py`](../../src/engine/sniper_gatekeeper_replay.py) — 262라인

### 4.1 동기 파일 I/O in hot path

```python
# sniper_gatekeeper_replay.py:47-49
def _append_jsonl(path: Path, payload: dict) -> None:
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
```

- **문제**: 모든 gatekeeper 평가 결과를 JSONL 파일에 동기 쓰기. 디스크 I/O는 메인 루프를 블로킹.
- **영향**: 평가 자체가 ~200ms 걸리는 상황에서 파일 쓰기까지 더해짐.
- **개선안**: `ThreadPoolExecutor`로 파일 I/O 분리. 또는 메모리 버퍼링 후 배치 write. **P2.**

### 4.2 `_RECENT_SNAPSHOT_SIGNATURES` TTL 없음

```python
# sniper_gatekeeper_replay.py:17
_RECENT_SNAPSHOT_SIGNATURES: dict[str, float] = {}
```

- **문제**: 시그니처(TTL-의도된 키)는 timestamp를 값으로 갖지만, 만료된 엔트리를 정리하지 않음.
- **영향**: 장기 실행 시 dict 크기 무한 증가 (메모리 leakage).
- **개선안**: 주기적 prune (예: 10분마다 1시간 이상된 sig 제거). **P3.**

---

## 5. 동적 임계값 (`sniper_dynamic_thresholds.py`)

**파일**: [`sniper_dynamic_thresholds.py`](../../src/engine/sniper_dynamic_thresholds.py) — 114라인. **경량 모듈, 큰 문제 없음.**

### 5.1 `classify_market_cap_bucket()` — marcap 기준 미세 중복

```python
# sniper_dynamic_thresholds.py:26-32
def classify_market_cap_bucket(marcap) -> str:
    market_cap = _coerce_int(marcap, 0)
    ...
```

- **문제**: 동일 marcap 값으로 `get_dynamic_scalp_thresholds`와 `get_dynamic_swing_gap_threshold`에서 각각 `classify_market_cap_bucket()` 호출.
- **영향**: KOSDAQ_ML 경로에서 두 함수 모두 호출되어 중복 분류.
- **개선안**: 버킷을 한 번만 계산하고 결과 재사용. `get_dynamic_scalp_thresholds()`가 반환하는 dict에 `bucket`이 이미 포함되어 있음. **P4.**

---

## 6. 스케일인/진입 상태

### 6.1 `_calc_held_minutes()` — datetime.now() 반복 (`sniper_scale_in.py`)

```python
# sniper_scale_in.py:16-34
def _calc_held_minutes(stock):
    if stock.get('order_time'):
        return (datetime.now().timestamp() - float(stock['order_time'])) / 60.0
    ...
```

- **문제**: 매 스케일인 평가마다 `datetime.now()` 호출.
- **영향**: `datetime.now()`는 시스템콜 + locale 연산 포함. 초당 수십회 호출 시 누적.
- **개선안**: `now_ts` (float timestamp)를 파라미터로 받도록 변경. **P3.**

### 6.2 `ENTRY_LOCK` (`sniper_entry_state.py`)

```python
# sniper_entry_state.py:10
ENTRY_LOCK = threading.RLock()
```

- **문제**: 전역 RLock. 진입 관련 모든 상태 변경이 이 lock에 직렬화.
- **영향**: 동시성 제한. 단, 메인 루프는 단일 스레드이므로 영향 없음.
- **개선안**: 구조 변경 전까지 현재 상태 유지. **P4.**

---

## 7. 계측 정합성

### 7.1 `_loop_elapsed_ms` = wall time 측정 위치

```python
# kiwoom_sniper_v2.py:1400
_loop_elapsed_ms = (time.time() - now_ts) * 1000  # now_ts는 1219번째 줄에서 설정
```

- **정확함**: `now_ts`는 루프 시작 시점, 측정은 sleep 직전. 즉 순수 처리 시간(DB poll + 상태 라우팅 + 클린업)만 측정.
- **문제**: `time.time()`은 NTP 조정/점프 영향을 받을 수 있음. `time.monotonic()`이 더 적절.
- **개선안**: `time.monotonic()`으로 변경. **P4.**

### 7.2 `_db_elapsed_ms` / `_acct_elapsed_ms` — 조건부 skip 시에도 측정

- DB 폴링 5초 주기 — 80%의 iteration에서 측정값 = 0에 가깝지만 여전히 `perf_counter()` 호출.
- 90초 주기 계좌 동기화 — 98.9%의 iteration에서 `_acct_elapsed_ms ≈ 0`.
- **영향 없음** (`perf_counter`는 ~50ns).

### 7.3 [LOOP_METRICS] 60초 로그 — `watching_count` / `holding_count` 중복 계산

```python
# kiwoom_sniper_v2.py:1403-1404
_watching_count = len([t for t in targets if t.get('status') == 'WATCHING'])
_holding_count = len([t for t in targets if t.get('status') == 'HOLDING'])
```

- **문제**: 매 루프 list comprehension으로 watching/holding 카운트 계산. 60초에 한 번만 로깅하지만 매 루프 계산.
- **영향**: 타겟 40개 기준, 초당 80회 조건부 체크.
- **개선안**: 로깅 시점(60초)에만 계산. **P4.**

---

## 8. 구조적 개선

### 8.1 `sniper_state_handlers.py` — 5.4K라인 단일 모듈

- WATCHING 진입 로직 (라인 ~1860-2640)
- HOLDING 진입/exit 로직 (라인 ~3500-4500)
- BUY_ORDERED 처리
- SELL_ORDERED 처리
- 공통 유틸

**개선안**: `sniper_state_handlers_*.py`로 기능별 분할. 단, 모든 handler가 동일한 모듈 레벨 전역변수(`KIWOOM_TOKEN`, `DB`, `ACTIVE_TARGETS` 등)에 의존하므로 분할 시 의존성 주입 패턴 도입 필요. **P3 (장기).**

### 8.2 `getattr(TRADING_RULES, ...)` 중앙 집중화

현재 최소 20개 이상의 모듈에서 산발적으로 TRADING_RULES 참조.

**개선안**: `sniper_config.py`를 확장하여 모든 rule 접근을 `TradingRulesCache` 클래스로 통일. 핫스왑 가능하고 계측 가능. **P2 (중기).**

### 8.3 상태 핸들러 래퍼 체인 최적화

```
run_sniper()
  → kiwoom_sniper_v2.handle_watching_state()    # 15-key deps 체크
    → sniper_state_handlers.handle_watching_state()  # 실제 로직
```

- 매 호출마다 `_ensure_state_handler_deps()` 실행. 루프 시작 1회로 충분.
- **개선안**: 루프 시작 시 1회 `_ensure_state_handler_deps()` 호출 후, 핸들러 래퍼에서는 생략. **P1.**

---

## 9. 우선순위 요약

| # | 영역 | 이슈 | 영향 | 난이도 | 우선순위 |
|---|------|------|------|--------|----------|
| 1 | 상태 핸들러 | HOLDING AI review 동기 blocking (API + LLM) | 루프 지연 수백 ms~초 | 중 | **P1** |
| 2 | 메인 루프 | `_ensure_state_handler_deps()` 매 호출 15-key 비교 | 초당 수십회 불필요 비교 | 하 | **P1** |
| 3 | 공통 | `getattr(TRADING_RULES, ...)` 산발 수백 회 | 초당 500+회 동적 lookup | 중 | **P2** |
| 4 | Gatekeeper | 동기 파일 I/O (`_append_jsonl`) | 디스크 write blocking | 하 | **P2** |
| 5 | 진입 latency | `_CACHE_LOCK` 전역 RLock 경합 | 종목 증가 시 lock 대기 | 중 | **P2** |
| 6 | 진입 latency | `get_tick_history_ka10003()` 동기 API + AI 호출 | 핫패스 blocking (P1과 중복) | 중 | **P1** |
| 7 | 메인 루프 | Adaptive sleep 부재 (고정 1초) | 유휴/지연 tradeoff | 하 | **P3** |
| 8 | 스케일인 | `_calc_held_minutes()` `datetime.now()` 반복 | 초당 수십회 시스템콜 | 하 | **P3** |
| 9 | Gatekeeper | `_RECENT_SNAPSHOT_SIGNATURES` 무증가 | 메모리 leakage | 하 | **P3** |
| 10 | 상태 핸들러 | `_log_entry_pipeline()` dict 병합 오버헤드 | Blocker 많을 때 누적 | 하 | **P3** |
| 11 | 계측 | `time.time()` → `time.monotonic()` | NTP 점프 영향 가능 | 하 | **P4** |
| 12 | 상태 핸들러 | `normalize_strategy`/`position_tag` 캐시 | 초당 수십회 중복 | 하 | **P4** |
| 13 | 계측 | `watching_count`/`holding_count` 매 루프 계산 | 60초 로그용 중복 | 하 | **P4** |
| 14 | 구조 | `sniper_state_handlers.py` 5.4K 단일모듈 분할 | 유지보수/가독성 | 상 | **P3 (장기)** |

### 즉시 조치 권장 (P1)

1. **HOLDING AI 리뷰 → 별도 executor**: [`sniper_state_handlers.py:3583`](../../src/engine/sniper_state_handlers.py:3583) `get_tick_history_ka10003()` + `analyze_target()`을 `ThreadPoolExecutor`로 오프로드. AI 리뷰 완료 전까지는 `last_ai_reviewed_at` 업데이트 연기.
2. **`_ensure_state_handler_deps()` → 루프 시작 1회**: [`kiwoom_sniper_v2.py:309`](../../src/engine/kiwoom_sniper_v2.py:309)를 `run_sniper()` 진입 1회 또는 루프 상단 1회로 이동하고, 각 래퍼에서는 생략.

### 중기 권장 (P2)

1. **`TradingRulesCache`** 도입으로 `getattr(TRADING_RULES, ...)` 중앙 집중.
2. **Gatekeeper JSONL write**를 `ThreadPoolExecutor`로 오프로드.
3. **`_CACHE_LOCK`** 을 per-code lock으로 세분화.

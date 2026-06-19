# KORStockScan 코드베이스 성능 병목 분석 및 개선 제안

생성: `2026-05-14 KST`
범위: 로직 변경 없이 적용 가능한 성능 최적화 지점
분석 방법: I/O 패턴, DB 쿼리, CPU 바운드, 메모리, Pandas/DataFrame 안티패턴, 네트워크 호출 전수 조사

---

## 개요

`src/` 트리 전체 180+ Python 파일을 3개 축(I/O·네트워크, Pandas/DataFrame, DB 쿼리·CPU)으로 분석하여 **37개 잠재 병목 지점**을 식별. 중복·충돌 제거 후 **19개 핵심 개선항목**으로 정리.

## 2026-05-14 반영 메모

- BUY `blocked_*` 고빈도 이벤트는 V1에서 raw를 줄이지 않고 Sentinel 소비 경로만 1분 summary sidecar로 전환했다.
- V2는 producer-side compaction interface와 postclose verbosity report를 자동화체인에 편입했다. 기본값은 `PIPELINE_EVENT_HIGH_VOLUME_COMPACTION_MODE=off`이고, `shadow`는 raw JSONL/DB upsert를 보존한 채 producer summary만 생성한다.
- `suppress`는 코드 경로가 있어도 기본 비활성이며 2영업일 이상 V1 raw-derived summary parity 통과와 별도 approval owner 전에는 사용하지 않는다.
- V2 산출물 authority는 `diagnostic_aggregation`이며 threshold/order/provider/bot restart 권한은 없다.

---

## 우선순위 요약

| Phase | 항목 | 영향 | 적용 난이도 | 추정 개선폭 |
|-------|------|------|------------|------------|
| **Phase 1 (즉시)** | #2 json.dumps substring 검사, #3 HTTP Session, #4 config cache, #11 copy 제거 | HIGH | 사소함 | 주문 레이턴시 100-250ms 절감 |
| **Phase 2 (당일)** | #1 bulk query, #6 #7 apply 벡터화, #8 itertuples | HIGH | 보통 | 일일리포트 60-80% 단축 |
| **Phase 3 (계획)** | #5 event cache, #9 engine singleton, #10 connection pool, #12 numpy 인덱싱 | MEDIUM | 보통-어려움 | sentinel 30-40% 단축 |
| **Phase 4 (백로그)** | #13~#19 마이크로 최적화 | LOW-MEDIUM | 사소함 | 누적 개선 |

---

## Phase 1 — 즉시 적용 (비용 低, 로직 변경 없음)

### #1. N+1 쿼리 — `_build_market_snapshot()` 개별 SELECT

| 항목 | 내용 |
|------|------|
| **파일** | `src/engine/daily_report_service.py:306-411` |
| **패턴** | 종목당 `SELECT * FROM daily_stock_quotes WHERE stock_code = :code ... LIMIT 60` 실행 |
| **문제** | 최대 150개 종목 × 개별 SQL round-trip. 각 쿼리마다 `SELECT *`로 불필요 컬럼 전송. pandas `read_sql()` 호출당 DataFrame 객체 생성 오버헤드 |
| **영향** | **HIGH** — 일일리포트 생성의 최대 병목. 150회 네트워크 I/O + 150회 DataFrame 구축 |
| **개선** | 모든 대상 종목코드를 수집하여 단일 bulk 쿼리로 전환 |

```python
# Before (150 queries)
for _, row in targets.iterrows():
    code = str(row.get("stock_code", "")).strip().zfill(6)
    history = pd.read_sql(
        text("SELECT * FROM daily_stock_quotes WHERE stock_code = :code AND quote_date <= :quote_date ORDER BY quote_date DESC LIMIT 60"),
        engine, params={"code": code, "quote_date": quote_date}
    )

# After (1 query)
all_codes = targets["stock_code"].astype(str).str.strip().str.zfill(6).tolist()
all_history = pd.read_sql(
    text("SELECT stock_code, quote_date, open_price, high_price, low_price, close_price, volume, foreign_net, inst_net, margin_rate FROM daily_stock_quotes WHERE stock_code = ANY(:codes) AND quote_date <= :quote_date ORDER BY stock_code, quote_date DESC"),
    engine, params={"codes": all_codes, "quote_date": quote_date}
)
history_by_code = dict(tuple(all_history.groupby("stock_code")))
# 이후 loop에서는 history_by_code[code].head(60) 사용
```

---

### #2. `json.dumps()` substring 검사 — `buy_funnel_sentinel.py`

| 항목 | 내용 |
|------|------|
| **파일** | `src/engine/buy_funnel_sentinel.py:322-336,143-176` |
| **패턴** | `"ai_score_50_buy_hold_override" in json.dumps(event.fields, ensure_ascii=False)` |
| **문제** | 이벤트당 1-2회 전체 dict→JSON 직렬화 후 `in` substring 검사. 1만 이벤트 기준 2만회 `json.dumps()` 호출. 직렬화된 문자열은 즉시 폐기 |
| **영향** | **HIGH** — 모든 sentinel 이벤트 필터링에서 발생. CPU 낭비 누적 |
| **개선** | dict를 직접 검사하여 직렬화 제거 |

```python
# Before
or "ai_score_50_buy_hold_override" in json.dumps(event.fields, ensure_ascii=False)

# After
def _field_value_contains(fields: dict, target: str) -> bool:
    return any(target in str(v) for v in fields.values())

or _field_value_contains(raw_fields, "ai_score_50_buy_hold_override")
```

---

### #3. `requests.post()` Session 부재 — 주문 게이트웨이

| 항목 | 내용 |
|------|------|
| **파일** | `src/engine/kiwoom_orders.py:168,238,363,447,498` |
| **패턴** | 매수/매도/취소/잔고조회/재고조회 5개 엔드포인트 모두 `requests.post(url, headers={...}, json=...)` 사용 |
| **문제** | 매 호출 TCP+TLS 핸드셰이크 (50-200ms). keep-alive 없음. 스캘핑 핫패스에서 buy/sell/cancel 연속 호출 시 누적 지연 |
| **영향** | **HIGH** — 주문 제출 레이턴시에 직결 |
| **개선** | 모듈레벨 `requests.Session()` 싱글톤 |

```python
# Before
res = requests.post(url, headers=headers, json=payload, timeout=5)

# After (module level)
_API_SESSION = None

def _get_api_session() -> requests.Session:
    global _API_SESSION
    if _API_SESSION is None:
        _API_SESSION = requests.Session()
        _API_SESSION.headers.update({"Content-Type": "application/json;charset=UTF-8"})
    return _API_SESSION

# 호출부
res = _get_api_session().post(url, headers={**base_headers, "Authorization": f"Bearer {token}"}, json=payload, timeout=5)
```

---

### #4. 설정파일 반복 로드 — 14개 모듈 중복 I/O

| 항목 | 내용 |
|------|------|
| **파일** | `src/utils/kiwoom_utils.py`, `src/engine/kiwoom_websocket.py`, `src/notify/telegram_manager.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/notify_panic_state_transition.py`, `src/engine/notify_error_detection_admin.py`, `src/engine/notify_monitor_snapshot_admin.py`, `src/engine/ipo_listing_day_runner.py`, `src/engine/macro_briefing_complete.py`, `src/scanners/final_ensemble_scanner.py` 등 |
| **패턴** | `CONFIG_PATH if CONFIG_PATH.exists() else DEV_PATH` → `open()` → `json.load()` |
| **문제** | 동일 config JSON을 14개 모듈이 각각 stat→open→read→parse. 봇 기동 시 5회+ 중복 I/O |
| **영향** | **HIGH** — startup 오버헤드. 각 모듈 초기화 지연 누적 |
| **개선** | `@functools.cache` 단일 loader. `sniper_config.py`의 `CONF`를 단일 진실공급원으로 통일 |

```python
# src/utils/constants.py 또는 공유 모듈
import functools
import json
from pathlib import Path

@functools.cache
def get_system_config() -> dict:
    target = CONFIG_PATH if CONFIG_PATH.exists() else DEV_PATH
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        return {}
```

---

### #5. Sentinel event cache 재파싱 — `sentinel_event_cache.py`

| 항목 | 내용 |
|------|------|
| **파일** | `src/engine/sentinel_event_cache.py:85-124` |
| **패턴** | `update_and_load_cached_event_rows()` 호출마다 raw JSONL 전체 읽기 + 캐시파일 전체 재파싱 |
| **문제** | sentinel마다 raw 라인 N개 `json.loads()` + 캐시 M행 `json.loads()` 재실행. 하루 1만 이벤트 기준 2만회 직렬화 연산. 신규 이벤트가 없어도 전체 재파싱 |
| **영향** | **HIGH** — sentinel scan 호출마다 발생. 하루 수십 회 누적 |
| **개선** | appended_rows를 메모리에 보관. 캐시 재파싱은 신규 행이 있을 때만 수행 |

```python
# Before: 항상 전체 캐시파일을 다시 읽음
rows: list[dict[str, Any]] = []
if cache_path.exists():
    with cache_path.open("r", encoding="utf-8", errors="replace") as cache_handle:
        for raw_line in cache_handle:
            line = raw_line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
                rows.append(row)
            except json.JSONDecodeError:
                continue

# After: 메모리에 보관 중인 rows 반환. appended_cache_rows == 0이면 추가 파싱 스킵
# (상세 구현은 sentinel_event_cache 내부 상태 관리 필요)
```

---

## Phase 2 — 당일 적용 (비용 中, 벡터화·구조 변경)

### #6. `.apply(lambda, axis=1)` 2회 패스 — `recommend_daily_v2.py`

| 항목 | 내용 |
|------|------|
| **파일** | `src/model/recommend_daily_v2.py:62-64,76` |
| **패턴** | `score_df.apply(lambda row: (row['date'], row['code']) in selected_keys, axis=1)` |
| **문제** | 수백 종목 × 2회 Python-level 행 순회. 튜플 생성 + set 조회를 람다로 매 행 수행 |
| **영향** | **HIGH** — 일일 추천 파이프라인의 핫패스 |
| **개선** | MultiIndex `isin()`으로 벡터화 |

```python
# Before (line 62-64)
diagnostic['selection_mode'] = diagnostic.apply(
    lambda row: 'SELECTED' if (row['date'], row['code']) in selected_keys else 'DIAGNOSTIC_ONLY',
    axis=1,
)
# Before (line 76)
pick_df = score_df[
    score_df.apply(lambda row: (row['date'], row['code']) in selected_keys, axis=1)
].copy()

# After
score_df['_key'] = list(zip(score_df['date'], score_df['code']))
mask = score_df['_key'].isin(selected_keys)
diagnostic['selection_mode'] = np.where(mask, 'SELECTED', 'DIAGNOSTIC_ONLY')
pick_df = score_df[mask].copy()
score_df.drop(columns=['_key'], inplace=True)
```

---

### #7. `.apply(lambda, axis=1)` on bulk DataFrame — `update_kospi.py`

| 항목 | 내용 |
|------|------|
| **파일** | `src/utils/update_kospi.py:526-528` |
| **패턴** | `final_bulk_df.apply(lambda row: (row['quote_date'], row['stock_code']) not in existing_keys, axis=1)` |
| **문제** | 수천 행 대규모 DataFrame에서 Python-level 튜플 생성 + set 조회 |
| **영향** | **HIGH** — bulk update 시 수천 행 처리 |
| **개선** | MultiIndex `isin()`으로 벡터화 |

```python
# Before
mask = final_bulk_df.apply(
    lambda row: (row['quote_date'], row['stock_code']) not in existing_keys, axis=1
)
final_bulk_df = final_bulk_df[mask].copy()

# After
existing_mi = pd.MultiIndex.from_tuples(existing_keys, names=['quote_date', 'stock_code'])
bulk_mi = pd.MultiIndex.from_frame(final_bulk_df[['quote_date', 'stock_code']])
mask = ~bulk_mi.isin(existing_mi)
final_bulk_df = final_bulk_df.loc[mask].copy()
```

---

### #8. `.iterrows()` 시뮬레이션 핫패스 — `swing_daily_simulation_report.py`

| 항목 | 내용 |
|------|------|
| **파일** | `src/engine/swing_daily_simulation_report.py:504,574,652` |
| **패턴** | `for _, row in recommendations.iterrows():` → 루프 내 `quote_df[quote_df["stock_code"] == code]` 필터링 |
| **문제** | `.iterrows()` Series boxing overhead (`.itertuples()` 대비 3-10배 느림) + 매 반복 O(N) boolean 필터링 |
| **영향** | **MEDIUM-HIGH** — swing 일일 시뮬레이션 리포트 |
| **개선** | `.itertuples()` + quote_df pre-grouping |

```python
# Before
for _, row in recommendations.iterrows():
    code = str(row.get("code") or row.get("stock_code") or "").zfill(6)
    future = quote_df[quote_df["stock_code"] == code].copy()

# After
quote_groups = dict(tuple(quote_df.groupby("stock_code")))
for row in recommendations.itertuples(index=False):
    code = str(row.code or row.stock_code or "").zfill(6)
    future = quote_groups.get(code, pd.DataFrame())
```

---

## Phase 3 — 계획 적용 (비용 中高, 캐시·풀링 리팩터링)

### #9. `create_engine()` 반복 호출 — `daily_report_service.py`

| 항목 | 내용 |
|------|------|
| **파일** | `src/engine/daily_report_service.py:125-128` |
| **패턴** | `_get_engine()` 호출마다 `create_engine(POSTGRES_URL, pool_pre_ping=True)` |
| **문제** | `build_daily_report()` 1회 호출에 엔진 3-4회 생성. 각각 pool 초기화 |
| **영향** | **MEDIUM** — report 생성 startup/teardown 오버헤드 |
| **개선** | 모듈레벨 싱글톤 |

```python
# Before
def _get_engine():
    create_engine, _ = _import_sqlalchemy()
    return create_engine(POSTGRES_URL, pool_pre_ping=True)

# After
_ENGINE = None

def _get_engine():
    global _ENGINE
    if _ENGINE is None:
        create_engine, _ = _import_sqlalchemy()
        _ENGINE = create_engine(POSTGRES_URL, pool_pre_ping=True)
    return _ENGINE
```

---

### #10. 완료: legacy dashboard DB upsert path 제거

`dashboard_data_repository.py`의 legacy PostgreSQL raw dashboard 저장 경로는 제거됐다. 현재 dashboard/API canonical source는 `data/report/monitor_snapshots/*.json*`, `data/pipeline_events/*.jsonl*`, Parquet, DuckDB다.

---

### #11. DataFrame `.copy()` 연쇄 — `swing_daily_simulation_report.py`

| 항목 | 내용 |
|------|------|
| **파일** | `src/engine/swing_daily_simulation_report.py:65,70,82,91,96` |
| **패턴** | `exact = df[df["date"] == target_ts].copy()` → `df = df[df["date"] == latest_date].copy()` → `out = df.copy()` → `live = out[live_mask].copy()` |
| **문제** | DataFrame 1개가 함수 경계 통과하며 4-5회 deep copy. boolean filter 결과는 이미 새 DataFrame인데도 복제 |
| **영향** | **MEDIUM** — 누적 메모리 할당 + 복사 오버헤드 |
| **개선** | mutation 지점에서만 1회 복제. boolean filter 결과는 `.copy()` 불필요 |

```python
# Before (4-5 copies)
exact = df[df["date"] == target_ts].copy()      # copy 1 — filter returns new
df = df[df["date"] == latest_date].copy()         # copy 2 — filter returns new
return df.copy(), {...}                           # copy 3 — empty df copy
out = df.copy()                                   # copy 4 — if not mutated, unnecessary
live = out[live_mask].copy()                      # copy 5 — filter returns new

# After (1 copy at mutation point only)
exact = df[df["date"] == target_ts]               # no copy
if exact.empty:
    exact = df[df["date"] == latest_date]          # no copy
if need_mutation:
    out = exact.copy()                             # single copy
```

---

### #12. `.loc` in nested loops — `dataset_builder_v2.py`

| 항목 | 내용 |
|------|------|
| **파일** | `src/model/dataset_builder_v2.py:59-123` |
| **패턴** | `for i in range(len(df) - hold_days - 1): df.loc[entry_idx, 'open'] ... for j in range(entry_idx, ...): df.loc[j, 'open']` |
| **문제** | 이중 루프에서 `.loc` 인덱스 조회 overhead. 잠재 수만 행 × 내부 루프 |
| **영향** | **MEDIUM** — 학습 데이터셋 구축 시 |
| **개선** | numpy 배열로 사전 변환 후 정수 인덱싱 |

```python
# Before
for i in range(len(df) - hold_days - 1):
    buy_price = df.loc[entry_idx, 'open']
    for j in range(entry_idx, min(...)):
        op = df.loc[j, 'open']
        hi = df.loc[j, 'high']

# After
open_arr = df['open'].values
high_arr = df['high'].values
for i in range(len(df) - hold_days - 1):
    buy_price = open_arr[entry_idx]
    for j in range(entry_idx, min(...)):
        op = open_arr[j]
        hi = high_arr[j]
```

---

## Phase 4 — 백로그 (마이크로 최적화, 누적 시 유의미)

### #13. `_safe_float/_safe_int` try/except 누적

| 항목 | 내용 |
|------|------|
| **파일** | `src/engine/daily_report_service.py:306-411` |
| **패턴** | `_safe_float(row.get("close_price"))`, `_safe_float(latest["rsi"].values[0])` 등 종목당 10회+ try/except |
| **문제** | 150종목 × 10회 = 1500회 try/except. Python에서 예외 처리 오버헤드 유의미 |
| **영향** | **LOW-MEDIUM** |
| **개선** | DataFrame 전체 컬럼을 `pd.to_numeric(..., errors='coerce').fillna(0)`로 사전 변환 |

---

### #14. 핫패스 로깅 f-string

| 항목 | 내용 |
|------|------|
| **파일** | `src/utils/kiwoom_utils.py:244` |
| **패턴** | `get_api_url()` 호출마다 `log_info(f"🌐 [KIWOOM API] base_url=...")` |
| **문제** | 주문/체결/잔고조회 등 모든 API URL 생성 시 f-string 평가. 로그레벨 무관 즉시 평가 |
| **영향** | **LOW-MEDIUM** |
| **개선** | `if LOG_VERBOSE:` 가드 또는 `%s` 지연평가 포맷 사용 |

---

### #15. WS 틱 루프 내 문자열 변환

| 항목 | 내용 |
|------|------|
| **파일** | `src/engine/kiwoom_websocket.py:82-86,845-854` |
| **패턴** | `_safe_abs_int()` → `str(val).replace(',', '').replace('+', '').strip()` → `int(float(...))`. 호가창 파싱 루프에서 `for i in range(1, 6): ask_p = values.get(str(40+i))` |
| **문제** | 매 틱마다 str→replace→float→int 변환 + 루프 내 `str()` 5회 |
| **영향** | **LOW-MEDIUM** |
| **개선** | `pd.to_numeric(val, errors='coerce')` + `KEYS = {1: '41', 2: '42', ...}` pre-compute |

---

### #16. 문자열 `+=` 반복 연결

| 항목 | 내용 |
|------|------|
| **파일** | `src/engine/sniper_analysis.py:326,329` |
| **패턴** | `report += f"{icon} {label}: ...\n"` |
| **문제** | Python 문자열 `+=`은 O(n²) 복사. 10-20회 연결이지만 패턴 개선이 사소함 |
| **영향** | **LOW** |
| **개선** | `parts = []` → `parts.append(...)` → `'\n'.join(parts)` |

---

### #17. `df.replace().fillna()` 2-pass

| 항목 | 내용 |
|------|------|
| **파일** | `src/model/feature_engineering_v2.py:132-133`, `src/model/dataset_builder_v2.py:207-208` |
| **패턴** | `df = df.replace([np.inf, -np.inf], np.nan); df = df.fillna(0.0)` |
| **문제** | DataFrame 전체 2회 스캔 |
| **영향** | **LOW** |
| **개선** | `df = df.replace([np.inf, -np.inf, np.nan], 0.0)` 1-pass |

---

### #18. `read_text().splitlines()` 전체 파일 메모리 로드

| 항목 | 내용 |
|------|------|
| **파일** | `src/engine/monitor_snapshot_runtime.py:42-59` |
| **패턴** | `target.read_text().splitlines()` 후 마지막 유효 JSON 라인만 사용 |
| **문제** | 대용량 로그파일을 통째로 메모리에 올린 후 마지막 한 줄만 보관 |
| **영향** | **LOW-MEDIUM** |
| **개선** | `with target.open("r") as fh: for line in fh:` 스트리밍 |

---

### #19. `.iterrows()` → list comprehension

| 항목 | 내용 |
|------|------|
| **파일** | `src/scanners/final_ensemble_scanner.py:233` |
| **패턴** | `[{'Code': r['Code'], 'Name': r['Name']} for _, r in target_df.iterrows()]` |
| **문제** | `.iterrows()` Series boxing overhead로 dict 변환 |
| **영향** | **LOW** |
| **개선** | `target_df[['Code', 'Name']].to_dict('records')` — 5-10배 빠름 |

---

## 기타 관찰 (No Issue Found — 올바른 패턴)

아래 패턴은 조사했으나 코드베이스에서 올바르게 사용 중입니다:

| 검사 패턴 | 결과 |
|-----------|------|
| `pd.DataFrame().append()` (deprecated) | 미발견 — `pd.concat()` + list accumulation 사용 |
| `pd.concat()` inside loops | 미발견 — frames list 수집 후 루프 외 concat |
| `pd.read_csv()` / `pd.read_parquet()` inside loops | 미발견 — 함수당 1회 호출 |
| Chained `.loc[]` assignments | 미발견 — 라인당 단일 할당 |
| String operations on object columns vs StringDtype | 적절함 — 코드 정규화는 `.astype(str)` 필요 |

---

## 적용 추정 효과

| 적용 범위 | 추정 개선폭 | 측정 지표 |
|-----------|------------|-----------|
| Phase 1 완료 | 주문 게이트웨이 레이턴시 100-250ms 절감, 봇 기동시간 15-20% 단축 | `kiwoom_orders.py` 응답시간, 기동 로그 timestamp 간격 |
| Phase 1+2 완료 | **일일리포트 생성시간 60-80% 단축** | `daily_report_service.py` wall-clock 시간 |
| Phase 1+2+3 완료 | sentinel scan 30-40% 단축, 일일 리포트 추가 5-10% 단축 | sentinel 호출 간격, DB 쿼리 수 카운트 |
| 전체 완료 | CPU 사용률 10-15% 감소, 메모리 할당률 5-8% 감소 | 프로파일러 비교 측정 |

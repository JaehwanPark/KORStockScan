
# daily_stock_quotes.is_nxt + get_effective_kiwoom_code 통합 설계안 (최신 update_kospi 기준)

## 목표
- `daily_stock_quotes`에 `is_nxt` 컬럼을 추가한다.
- `is_nxt`의 의미는 **해당 거래일 기준 Kiwoom 요청 시 `_AL` suffix 적용 대상 여부**다.
- `update_kospi.py`가 매일 저녁 **넥스트레이드 공식 “매매체결대상종목(정규시장)”** 페이지를 source of truth로 조회해 `is_nxt`를 함께 적재한다.
- `kiwoom_utils.py`에는 `get_effective_kiwoom_code()` 헬퍼를 추가해, 최신 거래일 `is_nxt`를 기준으로 `005930` 또는 `005930_AL` 형태의 요청 코드를 반환한다.

## 왜 이렇게 하나
- 사용 목적은 “오늘 NXT에서 실제 거래가 있었는지”가 아니라, **Kiwoom API 호출 시 `_AL` suffix를 붙여야 더 정확한 데이터를 가져오는지**다.
- 따라서 `is_nxt`는 거래량/체결 여부가 아니라 **NXT 대상 종목 플래그**로 저장하는 것이 맞다.
- `update_kospi.py`는 현재 키움 OHLCV/수급/기본정보를 병합해 `daily_stock_quotes`를 일괄 적재하는 배치이므로, `is_nxt`를 함께 넣기에 가장 자연스럽다.

## source of truth
- 1순위: 넥스트레이드 공식 `매매체결대상종목(정규시장)` 페이지
- 2순위 폴백: 최신 거래일의 기존 `daily_stock_quotes.is_nxt`

## 변경 대상 파일
1. `models.py`
   - `DailyStockQuote.is_nxt = Column(Boolean)` 추가

2. `db_manager.py`
   - `init_db()`에 `ALTER TABLE daily_stock_quotes ADD COLUMN IF NOT EXISTS is_nxt BOOLEAN;`
   - `get_latest_is_nxt(code)` 추가
   - `get_latest_is_nxt_map(codes)` 추가

3. `update_kospi.py`
   - 넥스트레이드 공식 대상 종목 fetch 헬퍼 추가
   - `COLUMN_MAPPING`에 `Is_NXT -> is_nxt` 추가
   - `process_and_save_stock(..., is_nxt=False)`로 시그니처 확장
   - 적재 직전 `df['Is_NXT'] = bool(is_nxt)` 주입
   - nightly 배치 시작 시 NXT 대상 종목 목록을 1회 수집 후 각 종목 적재에 사용
   - fetch 실패 시 직전 DB 플래그 fallback

4. `kiwoom_utils.py`
   - `normalize_stock_code(code)` 추가
   - `get_effective_kiwoom_code(code, db=None, is_nxt=None)` 추가

## is_nxt 조회/사용 방식
### 저장
- `update_kospi.py`가 당일 적재 시 `is_nxt`를 함께 적재

### 조회
- 실행 시점에는 최신 거래일 기준 한 건만 읽는다.

```python
is_nxt = db.get_latest_is_nxt("005930")
req_code = get_effective_kiwoom_code("005930", is_nxt=is_nxt)
```

또는 DB를 내부에서 조회하게 둘 수도 있다.

```python
req_code = get_effective_kiwoom_code("005930")
```

## 운영 안전장치
- `daily_stock_quotes`는 메인 시세 테이블이므로 **additive 컬럼 추가**만 수행한다.
- fetch 실패 시 전 종목을 False로 덮지 않도록, 최신 거래일 `is_nxt`를 폴백 사용한다.
- 기존 조회 로직은 대부분 `SELECT *` 또는 명시 컬럼 조회이므로, 새 컬럼 추가 자체로 깨질 가능성은 낮다.
- `_AL` suffix 결정은 호출부에서 분산 구현하지 말고, `get_effective_kiwoom_code()`로 중앙화한다.

## 권장 사용 규칙
- 키움 REST/WebSocket 호출 직전에는 항상:
  1. `normalize_stock_code()`
  2. `get_effective_kiwoom_code()`
  순서로 요청 코드를 확정한다.
- 직접 `code + "_AL"`를 여기저기서 붙이지 않는다.

# 작업지시서: `data_client.py` 해체 및 부작용 버그 수정

**작성일:** 2026-04-25  
**대상 파일:** `src/utils/data_client.py`, `src/utils/kiwoom_utils.py`  
**작업 유형:** 데드코드 제거 + 연쇄 버그 수정

---

## 1. 배경 및 진단

### 왜 `DataClient`가 만들어졌나

`DataClient`는 **Repository Pattern**을 의도한 데이터 수집 단일창구 클래스로 설계됐다.  
호출자가 데이터 출처(FDR / Kiwoom API / DB)를 신경 쓰지 않아도 되도록 캡슐화하는 것이 목적이었다.

```
[설계 의도]
호출자 → DataClient → FDR (1순위)
                     → Kiwoom API (2순위 fallback)
                     → 로컬 DB (최후 fallback)
```

### 실제 상태: 데드코드

코드베이스 전체를 grep한 결과, **`DataClient`를 import하거나 호출하는 파일이 단 하나도 없다.**

```
$ grep -rn "DataClient\|data_client" src/ --include="*.py"
# (data_client.py 자체 제외 시) 결과 없음
```

실제 호출자들은 `DataClient`를 우회하고 FDR을 직접 호출하고 있다.

| 파일 | 직접 호출 패턴 |
|---|---|
| `scanners/final_ensemble_scanner.py` | `fdr.DataReader(...)`, `fdr.StockListing('KOSPI')` |
| `model/ml_v2_common.py` | `fdr.StockListing('KOSPI')`, `fdr.DataReader('KS11', ...)` |
| `model/common_v2.py` | `fdr.StockListing('KOSPI')` |
| `model/dataset_builder_v2.py` | `fdr.DataReader('KS11', ...)` |
| `engine/signal_radar.py` | `fdr.DataReader('KS11')` |
| `utils/update_kospi.py` | `fdr.StockListing('KRX')` |

`DataClient`는 **태어났지만 한 번도 호출된 적 없는 클래스**다.

---

## 2. 발견된 버그

### 버그 A: `DataClient.get_top_marketcap_stocks` — `self` 누락

```python
# src/utils/data_client.py:127
class DataClient:
    ...
    def get_top_marketcap_stocks(limit=300):  # ← self 없음, 런타임 오류
```

인스턴스 메서드이지만 `self`가 없다. 호출하면 즉시 `TypeError`.

### 버그 B: `kiwoom_utils.get_top_marketcap_stocks` — 유령 `self`

```python
# src/utils/kiwoom_utils.py:1572
def get_top_marketcap_stocks(self, limit=300):  # ← 모듈 함수인데 self가 있음
```

`DataClient`에서 복사된 것으로 추정되는 **모듈 레벨 함수**인데 `self` 파라미터가 남아있다.  
이 함수를 직접 호출하면 `self`에 `limit` 값이 바인딩되고 `limit`는 기본값 300으로 고정된다.  
이 함수도 **호출하는 코드가 없어** 현재는 무해하지만, 언제든 잘못 사용될 수 있는 시한폭탄.

---

## 3. 아키텍처 판단: 보강 vs 해체

### 보강 안이 불리한 이유

- 호출자들이 각자의 컨텍스트에서 **서로 다른 subset**을 필요로 한다.  
  - `final_ensemble_scanner`: OHLCV만 필요, DB fallback 불필요  
  - `signal_radar`: KS11 지수 데이터만 필요  
  - `ml_v2_common`: KOSPI 종목 리스트만 필요  
  - `update_kospi`: KRX 전체 종목 리스트 필요
- `DataClient`의 fallback 체인(FDR→Kiwoom→DB)은 배치 훈련 파이프라인에만 의미 있는 설계다.  
  실시간 스캐너는 DB fallback을 원하지 않는다.
- 이미 **`market_regime/data_provider.py`**가 외부 시장 데이터(VIX, WTI)에 대해 동일한 패턴으로 올바르게 구현돼 있고 실제로 사용되고 있다.  
  코드베이스는 이미 **도메인별 DataProvider 분리**를 채택하는 방향으로 진행 중이다.

### 결론: 해체

`DataClient`는 삭제한다. 기능을 분산하지 않고 **그냥 삭제**한다.  
각 호출자가 이미 FDR을 직접 사용하고 있으므로 이관할 로직이 없다.

---

## 4. 작업 목록

### Task 1: `data_client.py` 삭제

```bash
git rm src/utils/data_client.py
```

- 전체 코드베이스에서 이 파일을 import하는 곳이 없으므로 연쇄 영향 없음.
- 삭제 전 `git grep "data_client\|DataClient"` 로 재확인 후 실행.

---

### Task 2: `kiwoom_utils.get_top_marketcap_stocks` — `self` 제거

**파일:** `src/utils/kiwoom_utils.py:1572`

```python
# Before
def get_top_marketcap_stocks(self, limit=300):

# After
def get_top_marketcap_stocks(limit=300):
```

수정 후 함수 본문에서 `self.`를 사용하는 코드가 있는지 확인하고 있으면 제거한다.  
(현재 본문에는 `self.` 참조 없음 — 확인 완료.)

---

### Task 3: 회귀 확인

```bash
# import 잔재 없음 확인
grep -rn "data_client\|DataClient" src/ --include="*.py"

# kiwoom_utils 함수 시그니처 확인
grep -n "def get_top_marketcap_stocks" src/utils/kiwoom_utils.py

# 테스트 실행
pytest src/tests/ -x -q 2>&1 | tail -20
```

---

## 5. 비작업 항목 (하지 않는 것)

| 항목 | 이유 |
|---|---|
| FDR 직접 호출 코드를 DataClient로 통합 | 각 호출자 컨텍스트가 달라 억지 통합은 오히려 복잡도 증가 |
| `get_full_daily_data` 로직 보존 | 호출자가 없고, 동일 기능이 필요하면 해당 파이프라인에서 직접 구현 |
| `get_kospi_symbols` DB fallback 이관 | `update_kospi.py`에 이미 충분한 fallback 로직 있음 |

---

## 6. 예상 파급 범위

| 범위 | 영향 |
|---|---|
| import 깨짐 | 없음 (import 하는 파일 전무) |
| 테스트 깨짐 | 없음 (DataClient를 테스트하는 테스트 없음) |
| `kiwoom_utils` 함수 시그니처 변경 | 무해 (호출하는 코드 없음) |

총 변경 파일: **2개** (`data_client.py` 삭제, `kiwoom_utils.py` 1줄 수정)

---

## 7. 향후 DataProvider가 다시 필요해질 때

`DataClient` 방식이 아닌 `market_regime/data_provider.py` 패턴을 참조한다.  
- 단일 클래스에 모든 소스를 욱여넣지 말고 **도메인별 Provider 클래스**로 분리
- fallback 로직은 Provider 내부가 아닌 **Use Case 레이어(엔진/스캐너)에서** 결정
- 실시간 경로와 배치 경로의 DataProvider는 **별도 클래스**로 분리

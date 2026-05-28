# 2026-04-28 NaN Cast Guard Hotfix Report

## 1. 판정

- `kiwoom_sniper_v2` 및 `ORDER_EXECUTED` 체결 이벤트 경로에서 발생한 `cannot convert float NaN to integer` 오류는 `NaN/inf`가 주문·체결·DB 복원 숫자 필드에 유입된 상태에서 `int(float(...))`를 직접 호출한 것이 원인으로 판단한다.
- 이번 수정은 손실 억제 목적의 예외 봉합이 아니라, 장중 루프 중단과 체결 후 상태 전이 실패를 제거해 기대값 손실과 미진입/미청산 기회비용을 줄이기 위한 런타임 안정화 hotfix다.

## 2. 변경 사유

1. `2026-04-28 09:14:41`, `10:27:26`, `10:42:06 KST`에 `ORDER_EXECUTED` 이벤트 처리 중 동일 오류가 반복 발생했다.
2. `2026-04-28 10:56:43`, `13:06:25 KST`에는 스나이퍼 메인 루프 자체가 같은 오류로 중단됐다.
3. 체결 이벤트 실패는 `BUY_ORDERED -> HOLDING` 전이, preset TP 재설정, DB 반영을 흔들고, 루프 실패는 장중 감시·진입·취소 복귀 전체를 멈춰 기대값 훼손이 더 크다.
4. 오전 체결 이벤트와 오후 메인 루프 크래시가 모두 같은 메시지로 반복된 점을 근거로, 개별 전략 로직 문제가 아니라 숫자 정규화 공통 경계가 약한 문제로 판단했다.

## 3. 원인

- `stock`, `ws_data`, DB 조회값, 체결 payload 중 일부 필드가 문자열 `"nan"`, `numpy.nan`, `float("nan")`, `inf` 계열 값으로 들어와도 직접 `int(float(value))` 또는 `float(value)` 경로를 탔다.
- 대표 위험 필드는 아래와 같다.
  - 가격: `curr`, `target_buy_price`, `preset_tp_price`, `buy_price`
  - 수량: `qty`, `buy_qty`, `pending_add_qty`, `entry_filled_qty`
  - 메타 숫자: `marcap`, `ratio`, `order_price`
- 기존 코드는 예외는 잡아도 `NaN/inf`를 별도 비정상값으로 판정하지 않아 `ValueError: cannot convert float NaN to integer`가 핫패스에서 그대로 발생했다.

## 4. 작업 결과

### 4.1 공용 숫자 정규화 강화

- 아래 모듈에 `NaN/inf` 안전 캐스팅을 추가했다.
  - [src/engine/kiwoom_sniper_v2.py](/home/windy80xyt/KORStockScan/src/engine/kiwoom_sniper_v2.py)
  - [src/engine/sniper_state_handlers.py](/home/windy80xyt/KORStockScan/src/engine/sniper_state_handlers.py)
  - [src/engine/sniper_execution_receipts.py](/home/windy80xyt/KORStockScan/src/engine/sniper_execution_receipts.py)
  - [src/database/db_manager.py](/home/windy80xyt/KORStockScan/src/database/db_manager.py)
  - [src/utils/kiwoom_utils.py](/home/windy80xyt/KORStockScan/src/utils/kiwoom_utils.py)

- 공통 원칙:
  - `None`, 빈값, `"nan"`, `NaN`, `inf`, `-inf`는 모두 안전 기본값으로 폴백
  - 정수 필드는 `_safe_int(..., default=0)` 계열로 통일
  - 실수 필드는 `_safe_float(..., default=0.0)` 계열로 통일

### 4.2 체결 이벤트 핫패스 방어

- `ORDER_EXECUTED`에서 읽는 `price`, `qty`를 안전 캐스팅으로 교체했다.
- 신규 진입/추가매수 체결 후 누적 수량, 평균단가, preset TP 수량/가격 재설정 경로를 `NaN` 안전 계산으로 교체했다.
- 체결 직후 DB 반영 시 `buy_qty`, `buy_price`, `hard_stop_price`, `trailing_stop_price`도 동일 기준으로 정규화했다.

### 4.3 메인 루프 및 상태 핸들러 방어

- WATCHING/HOLDING/BUY_ORDERED 경로의 `curr`, `ask_tot`, `bid_tot`, `buy_qty`, `target_buy_price`, `buy_price`, `marcap` 직접 캐스팅을 제거했다.
- 취소 후 복귀, 보유 수량 폴백, 추가매수 계산, preset exit setup 등 루프 재진입에 자주 걸리는 경계도 같은 기준으로 정리했다.

### 4.4 DB 로드 시 정규화

- 활성 타깃 로드 시 아래 필드를 엔진 진입 전에 정규화하도록 보강했다.
  - `prob`, `buy_qty`, `buy_price`, `ratio`, `order_price`, `target_buy_price`, `marcap`, `preset_tp_price`, `preset_tp_qty`
- 목적은 런타임에서 `dirty numeric state`를 계속 방어하는 비용을 줄이고, DB 복원 단계에서 1차 차단하는 것이다.

## 5. 검증 결과

### 5.1 테스트

- 실행 명령:
  - `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_nan_numeric_normalization.py`
  - `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/kiwoom_sniper_v2.py src/engine/sniper_state_handlers.py src/engine/sniper_execution_receipts.py src/database/db_manager.py src/utils/kiwoom_utils.py`

- 결과:
  - `pytest`: `4 passed`
  - `py_compile`: 통과

### 5.1a 후속 보정

- 초기 hotfix 반영 후 `2026-04-28 13:45:25 KST`에 아래 후속 오류가 추가 확인됐다.
  - `ERROR in db_manager: 최신 시가총액 조회 실패 [004430]: name 'np' is not defined`
- 원인:
  - [db_manager.py](/home/windy80xyt/KORStockScan/src/database/db_manager.py)에서 `np.isfinite(...)`를 사용하도록 보강했지만 `import numpy as np`가 누락돼 있었다.
- 조치:
  - `db_manager.py` 상단에 `import numpy as np`를 추가했다.
- 재검증:
  - `PYTHONPATH=. .venv/bin/python -m py_compile src/database/db_manager.py` 통과
- 판정:
  - 이번 건은 `NaN` 방어 설계 자체의 실패라기보다 hotfix change set 누락 1건이며, 동일 보고서 범위 안의 후속 수정으로 포함한다.

### 5.2 추가 테스트 파일

- [src/tests/test_nan_numeric_normalization.py](/home/windy80xyt/KORStockScan/src/tests/test_nan_numeric_normalization.py)
  - `kiwoom_sniper_v2._safe_int/_safe_float`
  - `sniper_state_handlers._safe_int/_safe_float`
  - `sniper_execution_receipts._safe_int/_safe_float`
  - `kiwoom_utils._coerce_int/_coerce_float`
  - 위 함수들에 `NaN/inf` 입력 시 기본값으로 폴백되는지 확인

## 6. 영향 범위

- 기대 효과:
  - `ORDER_EXECUTED` 후 상태 전이 실패 감소
  - 장중 루프 중단 제거
  - 취소 후 `WATCHING` 복귀와 체결 후 `HOLDING` 전환 연속성 회복

- 남는 리스크:
  - 이번 패치는 `NaN` 값 자체의 업스트림 생성 원인을 제거한 것은 아니다.
  - 즉, 런타임 중단은 막았지만 어떤 source가 `NaN`을 만들었는지는 장후 재분해가 필요하다.

## 7. 다음 액션

1. 운영 반영은 `restart.flag` 기준 우아한 재시작으로 적용한다.
2. 장후 체크리스트에 `NaNCastGuard0428` 재발 점검 항목을 추가했다.
   - Source: [2026-04-28-stage2-todo-checklist.md](/home/windy80xyt/KORStockScan/docs/checklists/2026-04-28-stage2-todo-checklist.md)
3. 재발이 0건이면 패치를 유지한다.
4. 재발이 1건 이상이면 `buy_qty/buy_price/target_buy_price/marcap/preset_tp_*`, websocket `curr/ask_tot/bid_tot`, 체결 payload `price/qty` 중 어느 source가 `NaN`을 만들었는지 `2026-04-29 PREOPEN` 후속 항목으로 승격한다.

## 8. 전달용 요약

> `2026-04-28` 장중 발생한 `cannot convert float NaN to integer` 오류는 주문·체결·DB 복원 숫자 필드에 `NaN/inf`가 유입된 상태에서 직접 정수 변환을 수행한 것이 원인이었습니다.  
> 이번 hotfix는 `kiwoom_sniper_v2`, `sniper_state_handlers`, `sniper_execution_receipts`, `db_manager`, `kiwoom_utils`에 공통 숫자 정규화 가드를 추가해 루프 중단과 체결 후 상태 전이 실패를 막도록 수정했습니다.  
> 이후 `db_manager`에서 `np.isfinite(...)` 사용 대비 `numpy` import 누락으로 발생한 후속 오류 1건도 즉시 보정했으며, 관련 컴파일 검증까지 다시 통과했습니다.  
> 단위 테스트 `4 passed`, 관련 모듈 `py_compile` 통과까지 확인했습니다.  
> 다만 `NaN`을 만든 업스트림 source 자체는 별도 장후 재분해가 필요하며, 재발 여부는 `NaNCastGuard0428` 항목으로 후속 점검합니다.

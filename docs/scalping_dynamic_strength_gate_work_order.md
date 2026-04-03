# 스캘핑 동적 체결강도 게이트 작업지시서

## 목적

스캘핑 진입의 고정 임계값 `VPW_SCALP_LIMIT=120`을 바로 제거하지 않고, 실제 키움 웹소켓에서 수집 가능한 필드만 이용해 `동적 체결강도 기울기 + 거래대금 필터` 게이트를 추가한다.

이 문서는 가설이 아니라 아래 실문서 확인 결과를 기준으로 작성한다.

- API 문서 원본: [키움 REST API 문서.xlsx](/home/ubuntu/KORStockScan/docs/키움%20REST%20API%20문서.xlsx)
- 확인 범위: 실시간 API ID `00` ~ `0w`

## 실제 수집 가능 데이터 확인 결과

### 1. `0B` 주식체결

`0B`는 이번 작업의 핵심 데이터 소스다.

실제 문서상 확인된 주요 FID:

- `20`: 체결시간
- `10`: 현재가
- `15`: 거래량
  `+`는 매수체결, `-`는 매도체결
- `13`: 누적거래량
- `14`: 누적거래대금
- `228`: 체결강도
- `1030`: 매도체결량
- `1031`: 매수체결량
- `1032`: 매수비율
- `1313`: 순간거래대금
- `1314`: 순매수체결량
- `1315`: 매도체결량_단건
- `1316`: 매수체결량_단건
- `27`, `28`: 최우선 매도/매수호가
- `16`, `17`, `18`: 시가/고가/저가
- `290`: 장구분
- `9081`: 거래소구분

중요 결론:

- 체결강도 기울기 계산에 필요한 `228`이 실제 제공된다.
- 윈도우 거래대금 필터에 필요한 `1313` 순간거래대금이 실제 제공된다.
- 매수/매도 방향 분리에 필요한 `15`, `1030`, `1031`, `1032`, `1314`, `1315`, `1316`이 실제 제공된다.

즉 이번 기능은 별도 REST fallback 없이 `0B`만으로 1차 구현이 가능하다.

### 2. `0D` 주식호가잔량

`0D`는 호가 깊이와 잔량 불균형 보정용으로 사용한다.

실제 문서상 확인된 주요 FID:

- `41~50`: 매도호가1~10
- `51~60`: 매수호가1~10
- `61~70`: 매도호가수량1~10
- `71~80`: 매수호가수량1~10
- `121`: 매도호가총잔량
- `125`: 매수호가총잔량
- `128`: 순매수잔량
- `129`: 매수비율
- `138`: 순매도잔량
- `139`: 매도비율
- `21`: 호가시간

중요 결론:

- 기존 코드가 쓰는 `121`, `125` 외에도 `128`, `129`, `138`, `139`를 실제로 받을 수 있다.
- 동적 게이트에서 `호가 우위 악화` 방어 로직을 더 정교하게 만들 수 있다.

### 3. `0w` 종목프로그램매매

`0w`는 보조 필터다.

실제 문서상 확인된 주요 FID:

- `202`: 매도수량
- `204`: 매도금액
- `206`: 매수수량
- `208`: 매수금액
- `210`: 순매수수량
- `211`: 순매수수량증감
- `212`: 순매수금액
- `213`: 순매수금액증감
- `214`: 장시작예상잔여시간
- `215`: 장운영구분
- `216`: 투자자별ticker

중요 결론:

- 현재 코드가 쓰는 `210~213` 외에도 `202~208`의 절대 buy/sell 값이 실제 제공된다.
- 다만 스캘핑 1차 게이트는 `0B`만으로도 가능하므로, `0w`는 보조 가산점이나 필터로 2차 적용하는 것이 적절하다.

### 4. `0s` 장시작시간

실제 문서상 확인된 주요 FID:

- `215`: 장운영구분
- `20`: 체결시간
- `214`: 장시작예상잔여시간

중요 결론:

- `0s`만으로도 정규장, 시간외, NXT 프리/메인/애프터마켓 상태를 실제로 구분할 수 있다.
- 장 상태에 따라 동적 체결강도 게이트를 활성/비활성하는 정책 분기가 가능하다.

### 5. `0C` 주식우선호가

실제 문서상 확인된 주요 FID:

- `27`: 최우선 매도호가
- `28`: 최우선 매수호가

중요 결론:

- 현재 `0D`에서 이미 상위 호가를 가져오고 있어서 우선순위는 낮다.
- 다만 `0D` 공백 시 `0C`를 fallback best ask/bid로 활용할 수 있다.

### 6. `00` 주문체결

`00`은 계좌 체결/접수 이벤트용이다.

중요 결론:

- 진입 게이트 계산용 데이터 소스는 아니다.
- 다만 추후 “내 주문 직후 체결강도 변화” 분석용 telemetry에는 활용 가능하다.

## 현재 코드와 실제 문서 비교

현재 웹소켓 파서는 아래만 주로 사용 중이다.

- `0B`: `10`, `12`, `13`, `16`, `228`
- `0D`: `41~45`, `51~55`, `61~65`, `71~75`, `121`, `125`
- `0w`: `210`, `211`, `212`, `213`

관련 코드:

- [src/engine/kiwoom_websocket.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_websocket.py#L438)
- [src/engine/sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py#L577)

현재 미사용이지만 이번 기능에 직접 필요한 실제 수집 가능 FID:

- `0B`: `14`, `15`, `1030`, `1031`, `1032`, `1313`, `1314`, `1315`, `1316`
- `0D`: `128`, `129`, `138`, `139`
- `0w`: `202`, `204`, `206`, `208`
- `0s`: `214`, `215`

## 구현 원칙

### 원칙 1

동적 체결강도 게이트는 `0B` 실시간 수신 데이터만으로 1차 완성한다.

이유:

- 체결강도 `228`
- 단건 방향성 `15`
- 순간거래대금 `1313`
- 매수/매도체결량 `1030`, `1031`

가 모두 `0B`에 실제 존재한다.

### 원칙 2

윈도우 누적은 `sniper_state_handlers`가 아니라 `kiwoom_websocket`에서 한다.

이유:

- 현재 이벤트 디스패치는 종목별 최신 스냅샷 1개로 병합된다.
- 후단에서 윈도우를 만들면 중간 틱 유실 가능성이 있다.

### 원칙 3

Phase 1은 기존 `VPW_SCALP_LIMIT=120`을 유지한 상태에서 관측 로그만 추가한다.

## 작업 범위

### 작업 1. 웹소켓 수집 필드 확장

파일:

- [src/engine/kiwoom_websocket.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_websocket.py)

지시:

- `0B` 수신 시 아래 필드를 `target`에 파싱해서 저장한다.
  - `tick_strength` from `228`
  - `tick_trade_value` from `1313`
  - `tick_signed_volume` from `15`
  - `cum_trade_value` from `14`
  - `buy_exec_volume` from `1031`
  - `sell_exec_volume` from `1030`
  - `buy_ratio` from `1032`
  - `net_buy_exec_volume` from `1314`
  - `sell_exec_single` from `1315`
  - `buy_exec_single` from `1316`
- `0D` 수신 시 아래 필드도 저장한다.
  - `net_bid_depth` from `128`
  - `bid_depth_ratio` from `129`
  - `net_ask_depth` from `138`
  - `ask_depth_ratio` from `139`
- `0w` 수신 시 아래 절대값도 저장한다.
  - `prog_sell_qty` from `202`
  - `prog_sell_amt` from `204`
  - `prog_buy_qty` from `206`
  - `prog_buy_amt` from `208`
- `0s` 수신 시 장상태를 전역 또는 종목 공용 상태로 저장한다.
  - `market_session_state` from `215`
  - `market_session_remaining` from `214`

### 작업 2. 체결 모멘텀 deque 추가

파일:

- [src/engine/kiwoom_websocket.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_websocket.py#L77)

지시:

- 종목별 기본 상태에 아래 deque를 추가한다.
  - `strength_momentum_history: deque(maxlen=120)`
- `0B` 수신 시 아래 구조를 append 한다.

```python
{
    "ts": time.time(),
    "v_pw": current_strength,
    "price": current_price,
    "signed_qty": signed_qty,
    "buy_qty": buy_qty,
    "sell_qty": sell_qty,
    "tick_value": tick_value,
    "buy_ratio": buy_ratio,
}
```

- 5초 윈도우 기준으로 오래된 항목은 prune 한다.

### 작업 3. 동적 체결강도 판정 함수 추가

신규 파일 권장:

- `src/engine/sniper_strength_momentum.py`

지시:

- 아래 함수 시그니처로 구현한다.

```python
def evaluate_scalping_strength_momentum(ws_data: dict, *, now_ts: float | None = None) -> dict:
    ...
```

- 입력은 `kiwoom_websocket`이 만든 최신 종목 스냅샷을 사용한다.
- 아래 결과를 반환한다.

```python
{
    "allowed": bool,
    "reason": str,
    "window_sec": int,
    "base_vpw": float,
    "current_vpw": float,
    "vpw_delta": float,
    "slope_per_sec": float,
    "window_total_value": int,
    "window_buy_value": int,
    "window_sell_value": int,
    "window_buy_ratio": float,
}
```

### 작업 4. 스캘핑 게이트 연결

파일:

- [src/engine/sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py#L577)

지시:

- 기존
  - `if current_vpw < VPW_SCALP_LIMIT:`
  구간을 바로 제거하지 않는다.
- 1차는 아래 순서로 넣는다.
  - 동적 게이트 평가
  - 결과를 `[ENTRY_PIPELINE]` 로그로 기록
  - 기존 `VPW_SCALP_LIMIT` 차단 유지

관측 로그 예시:

```text
[ENTRY_PIPELINE] 종목명(코드) stage=strength_momentum_observed allowed=False base_vpw=97.0 current_vpw=104.0 delta=7.0 buy_value=21000000 buy_ratio=0.58 reason=below_target_delta
```

### 작업 5. 운영 로그 추가

파일:

- [src/engine/sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)

지시:

- 아래 stage를 신규 추가한다.
  - `strength_momentum_observed`
  - `blocked_strength_momentum`
  - `strength_momentum_pass`

### 작업 6. 설정값 추가

파일:

- [src/utils/constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py)

지시:

- 아래 상수를 추가한다.
  - `SCALP_DYNAMIC_VPW_ENABLED = True`
  - `SCALP_VPW_WINDOW_SECONDS = 5`
  - `SCALP_VPW_MIN_BASE = 95.0`
  - `SCALP_VPW_TARGET_DELTA = 10.0`
  - `SCALP_VPW_MIN_BUY_VALUE = 30_000_000`
  - `SCALP_VPW_MIN_BUY_RATIO = 0.60`
  - `SCALP_VPW_HISTORY_MAXLEN = 120`
  - `SCALP_VPW_STRONG_ABSOLUTE = 130.0`

## 판정 로직 기준

### Phase 1

관측만 수행

- 기존 `VPW_SCALP_LIMIT=120` 유지
- 동적 게이트는 로그만 기록

### Phase 2

병행 허용

- 기존 절대값 게이트 통과 또는 동적 게이트 통과 시 허용
- 단, 거래대금 필터는 반드시 포함

### Phase 3

동적 게이트 주력화

- 절대값 게이트는 강한 예외 조건으로만 유지

## 초기 기준값

1차 운영 시작값:

- `window = 5초`
- `min_base = 95`
- `target_delta = +10`
- `min_buy_value = 3천만 원`
- `min_buy_ratio = 0.60`

추가 예외:

- `current_vpw >= 130`
- `window_buy_value >= 5천만 원`

이면 강한 절대값 예외로 통과 가능하게 설계한다.

## 검증 항목

### 로그 검증

- `0B` 수신 시 `1313`, `1030`, `1031`, `1032`가 실제 값으로 채워지는지 확인
- `0D` 수신 시 `128`, `129`, `138`, `139`가 실제 값으로 채워지는지 확인
- `0w` 수신 시 `202`, `204`, `206`, `208`이 실제 값으로 채워지는지 확인

### 기능 검증

- `current_vpw < 120` 이지만 `5초 +10`과 `3천만 원` 조건을 만족한 종목이 실제 로그에 포착되는지 확인
- 단일 작은 틱 튐에서는 `buy_value` 부족으로 차단되는지 확인
- 급등 막바지 추격 구간에서는 기존 `gap_pct`, `overbought` 차단이 계속 우선하는지 확인

## 최종 결론

이번 작업은 실제 키움 문서 기준으로 충분히 구현 가능하다.

핵심은 아래다.

- 체결강도: `0B/228`
- 순간거래대금: `0B/1313`
- 매수/매도 체결량: `0B/1030`, `0B/1031`
- 매수비율: `0B/1032`
- 방향성 단서: `0B/15`
- 호가 방어 보조: `0D/121`, `0D/125`, `0D/128`, `0D/129`, `0D/138`, `0D/139`

따라서 다음 구현은 “추정 필드 탐색”이 아니라, 위 FID를 실제로 파싱하고 관측 로그를 붙이는 작업으로 바로 진행하면 된다.

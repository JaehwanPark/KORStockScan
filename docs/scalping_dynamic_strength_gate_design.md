# 스캘핑 체결강도 동적 기울기 게이트 설계안

## 목적

현재 스캘핑 진입은 체결강도 `VPW_SCALP_LIMIT=120` 절대값을 하드 게이트로 사용한다. 이 방식은 단순하고 직관적이지만, 다음 한계가 있다.

- 초반 선행 시그널을 늦게 잡는다.
- 종목별 유동성 차이를 반영하지 못한다.
- 순간 튐과 진짜 가속도를 구분하지 못한다.
- `120` 아래에서 강하게 치고 올라오는 종목을 놓친다.

이번 변경의 목적은 체결강도 제한을 제거하는 것이 아니라, 절대값 중심의 정적 게이트를 짧은 구간의 상승 기울기와 실거래대금이 결합된 동적 게이트로 교체하는 것이다.

## 현재 구조 요약

현재 스캘핑 WATCHING 진입 경로에서 체결강도 하드 게이트는 아래 지점에 있다.

- 절대값 차단: [src/engine/sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py#L577)
- 현재 사용 값: [src/utils/constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py#L102)

현재 실시간 데이터는 웹소켓 스냅샷에 종목별로 모인다.

- 실시간 종목 스냅샷 기본 구조: [src/engine/kiwoom_websocket.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_websocket.py#L77)
- 체결/호가/체결강도 수신 파싱: [src/engine/kiwoom_websocket.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_websocket.py#L430)

중요한 제약도 있다.

- `REALTIME_TICK_ARRIVED`는 종목별 최신 스냅샷만 남기므로, 틱 단위 윈도우 계산을 후단에서 하면 일부 틱이 유실될 수 있다.
- 따라서 체결강도 기울기와 윈도우 거래대금 계산은 `sniper_state_handlers`가 아니라 `kiwoom_websocket` 내부의 종목별 메모리 상태에서 누적하는 것이 맞다.

참고로 기존 Big-Bite는 이미 짧은 구간 체결 집계를 사용하는 패턴을 가지고 있다.

- 짧은 창 집계 패턴: [src/engine/sniper_condition_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_condition_handlers.py#L804)

## 제안 요약

스캘핑 진입 게이트를 아래 3단계로 바꾼다.

1. 최소 베이스라인 통과
2. 짧은 윈도우 내 체결강도 상승 기울기 통과
3. 같은 윈도우 내 실체결대금 필터 통과

최종 진입 조건 예시는 아래처럼 본다.

`현재 체결강도 >= MIN_STRENGTH_BASE`  
`AND WINDOW_SECONDS 동안 체결강도 증가량 >= TARGET_STRENGTH_DELTA`  
`AND 같은 구간 BUY 체결대금 >= MIN_WINDOW_BUY_VALUE`

권장 초기 기준은 다음과 같다.

- `WINDOW_SECONDS = 5`
- `MIN_STRENGTH_BASE = 95`
- `TARGET_STRENGTH_DELTA = 10`
- `MIN_WINDOW_BUY_VALUE = 30_000_000`
- `MIN_WINDOW_NET_BUY_RATIO = 0.60`

즉 운영 문장으로는 이렇게 해석한다.

- "지금 체결강도가 최소 95 이상이고"
- "최근 5초 동안 체결강도가 10 이상 상승했고"
- "그 5초 동안 공격적 매수 체결대금이 3천만 원 이상이며"
- "매수 우위 비중이 60% 이상이면"
- "정적 120 절대값 대신 동적 모멘텀 가속도 진입을 허용한다"

## 핵심 설계

### 1. 데이터 구조

웹소켓 종목별 상태에 스캘핑용 모멘텀 히스토리를 추가한다.

권장 필드:

- `vpw_momentum_history: deque(maxlen=120)`
- `trade_value_window_sec: int`
- `last_strength_momentum_eval: dict`

각 원소 포맷:

```python
{
    "ts": 1712101234.512,
    "v_pw": 108.3,
    "price": 12850,
    "qty": 420,
    "side": "BUY",
    "tick_value": 5397000,
}
```

저장 위치는 [src/engine/kiwoom_websocket.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_websocket.py#L77) 의 종목별 `realtime_data[item_code]`가 적절하다.

이유:

- 웹소켓 수신 시점이 가장 원본에 가깝다.
- 종목별 최신 스냅샷 덮어쓰기 전에 틱을 축적할 수 있다.
- 후단 로직은 이미 완성된 윈도우 메트릭만 읽으면 된다.

### 2. Window 정의

윈도우 기준은 시간 기반이 적합하다.

- 스캘핑은 초 단위 반응이 중요하다.
- 틱 개수 기반은 종목별 체결 빈도 차이가 너무 크다.
- 시간 기반 5초는 운영자가 직관적으로 이해하기 쉽다.

권장 방식:

- 기본: `WINDOW_SECONDS = 5`
- 옵션: `FAST_WINDOW_SECONDS = 3`, `SLOW_WINDOW_SECONDS = 8`

초기 1차 구현은 단일 `5초` 창으로 단순하게 시작하는 것이 좋다.

### 3. 기울기 계산식

기울기는 회귀식까지 가지 않고, 우선 단순 변화량 기반으로 두는 것이 운영 친화적이다.

기본 계산:

```text
vpw_delta = current_vpw - base_vpw
slope_per_sec = vpw_delta / elapsed_sec
```

여기서 `base_vpw`는 `now - WINDOW_SECONDS` 이전의 가장 가까운 샘플이다.

판정은 `slope_per_sec`보다 `vpw_delta` 절대 증가량을 먼저 쓰는 것이 좋다.

이유:

- 로그 해석이 쉽다.
- 운영자가 "5초 동안 +10"을 바로 이해할 수 있다.
- 종목마다 샘플 밀도가 달라도 설명이 단순하다.

따라서 1차 기준은 아래를 권장한다.

- 주 판정: `vpw_delta >= TARGET_STRENGTH_DELTA`
- 보조 로그: `slope_per_sec`

### 4. 거래대금 필터

체결강도만 보면 휩소에 약하다. 그래서 반드시 체결대금 필터를 붙인다.

권장 메트릭:

- `window_total_value`: 창 내 전체 체결대금 합
- `window_buy_value`: 창 내 BUY 체결대금 합
- `window_sell_value`: 창 내 SELL 체결대금 합
- `window_net_buy_value = window_buy_value - window_sell_value`
- `window_buy_ratio = window_buy_value / max(window_total_value, 1)`

최소 조건은 아래 조합이 좋다.

- `window_buy_value >= MIN_WINDOW_BUY_VALUE`
- `window_buy_ratio >= MIN_WINDOW_NET_BUY_RATIO`

이렇게 하면 "체결강도는 튀었지만 실제로는 빈약한 체결"을 많이 걸러낼 수 있다.

### 5. 체결 방향 판정

현재도 Big-Bite에서 체결 방향을 아래 순서로 보정한다.

- 체결 raw sign
- 호가 기반 side 추정

이 패턴을 그대로 재사용하면 된다.

- 참고: [src/engine/sniper_condition_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_condition_handlers.py#L787)
- 참고: [src/engine/sniper_condition_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_condition_handlers.py#L804)

즉 `0B` raw sign이 있으면 우선 사용하고, 없으면 직전 호가 스냅샷 기준으로 `BUY/SELL`을 추정한다.

## 권장 판정 함수

새 함수 예시:

`evaluate_scalping_strength_momentum(ws_data: dict, runtime_state: dict) -> dict`

반환 예시:

```python
{
    "allowed": True,
    "reason": "momentum_ok",
    "window_sec": 5,
    "base_vpw": 97.0,
    "current_vpw": 108.5,
    "vpw_delta": 11.5,
    "slope_per_sec": 2.3,
    "window_total_value": 51000000,
    "window_buy_value": 38000000,
    "window_sell_value": 13000000,
    "window_buy_ratio": 0.745,
}
```

실패 예시 reason:

- `insufficient_history`
- `below_strength_base`
- `below_target_delta`
- `below_window_buy_value`
- `below_buy_ratio`
- `side_unreliable`

## 적용 위치

### 1차 권장 위치

체결 이력 적재:

- [src/engine/kiwoom_websocket.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_websocket.py#L430)

진입 게이트 호출:

- [src/engine/sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py#L577)

즉 기존

- `if current_vpw < VPW_SCALP_LIMIT: return`

구간을 아래 형태로 교체한다.

- `momentum_gate = evaluate_scalping_strength_momentum(...)`
- `if not momentum_gate["allowed"]: return`

### 왜 `state_handlers` 단독 구현이 아닌가

`sniper_state_handlers`는 현재 시점 스냅샷을 잘 보지만, 종목별 중간 틱이 모두 보장되지는 않는다. 반면 웹소켓 파서는 `0B` 수신 순간을 직접 본다. 따라서:

- 히스토리 누적은 `kiwoom_websocket`
- 판정 호출은 `sniper_state_handlers`

의 2단 구성이 가장 안전하다.

## 파라미터 설계

권장 신규 상수:

- `SCALP_DYNAMIC_VPW_ENABLED = True`
- `SCALP_VPW_WINDOW_SECONDS = 5`
- `SCALP_VPW_MIN_BASE = 95.0`
- `SCALP_VPW_TARGET_DELTA = 10.0`
- `SCALP_VPW_MIN_BUY_VALUE = 30_000_000`
- `SCALP_VPW_MIN_BUY_RATIO = 0.60`
- `SCALP_VPW_HISTORY_MAXLEN = 120`
- `SCALP_VPW_STRONG_ABSOLUTE = 130.0`

마지막 `SCALP_VPW_STRONG_ABSOLUTE`는 완전 폐기가 아니라 상단 예외 게이트로 유지하는 것을 권장한다.

예:

- `current_vpw >= 130` 이고
- `window_buy_value >= 50_000_000`

이면 기울기 부족이어도 통과시킬 수 있다.

이렇게 하면 정적 규칙의 장점도 일부 남길 수 있다.

## 로그 설계

운영 편의상 로그는 꼭 필요하다.

권장 로그 포맷:

```text
[ENTRY_PIPELINE] 종목명(코드) stage=blocked_strength_momentum base_vpw=96.5 current_vpw=103.0 delta=6.5 window_sec=5 buy_value=18500000 buy_ratio=0.54 reason=below_target_delta
```

통과 로그 예시:

```text
[ENTRY_PIPELINE] 종목명(코드) stage=strength_momentum_pass base_vpw=95.0 current_vpw=107.2 delta=12.2 slope=2.44 buy_value=41000000 buy_ratio=0.71
```

이 로그는 기존 `blocked_vpw`를 대체하거나, 전환 기간에는 병행 출력할 수 있다.

## 롤아웃 전략

### Phase 1

관측 전용

- 히스토리 적재만 활성화
- 기존 `VPW_SCALP_LIMIT=120` 유지
- 동적 판정 결과는 로그만 남김

목표:

- 실제로 어떤 종목이 `120 미만`인데도 강한 상승 기울기를 보였는지 확인
- 노이즈 구간에서 얼마나 자주 false positive가 나는지 확인

### Phase 2

병행 게이트

- `VPW_SCALP_LIMIT` 또는 `동적 게이트` 중 하나 통과 시 허용
- 다만 거래대금 필터는 반드시 유지

목표:

- 기회 손실 감소
- 체감 false positive 확인

### Phase 3

동적 게이트 주력화

- `VPW_SCALP_LIMIT`는 강한 절대값 예외 통로로만 유지
- 기본 게이트는 `base + delta + buy_value + buy_ratio`

## 리스크와 방어장치

### 1. 틱 손실 리스크

현재 이벤트 버스 전달은 종목별 최신값으로 합쳐진다. 그래서 윈도우 계산은 후단 이벤트 소비자가 아니라 웹소켓 파서 내부에 두어야 한다.

### 2. 허수 체결강도 튐

방어:

- `MIN_STRENGTH_BASE`
- `MIN_WINDOW_BUY_VALUE`
- `MIN_WINDOW_BUY_RATIO`

### 3. 지나친 추격매수

방어:

- 기존 `gap_pct >= 1.5` 차단 유지: [src/engine/sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py#L601)
- 기존 과열 차단 유지: [src/engine/sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py#L470)
- Big-Bite follow-through와 충돌하지 않도록 별도 stage 이름 사용

### 4. API 의존성 증가

실시간 판정마다 `ka10046` 같은 REST를 다시 치는 방식은 비권장이다.

권장:

- 1차는 웹소켓 `0B` 기반 tick_value 합산으로 해결
- `ka10046`는 디버깅 또는 fallback 참고값으로만 사용

## 구현 우선순위

1. `kiwoom_websocket`에 스캘핑 체결 모멘텀 deque 추가
2. `0B` 수신 시 `price/qty/side/tick_value/v_pw/ts` 적재
3. 전용 판정 함수 `evaluate_scalping_strength_momentum()` 추가
4. `sniper_state_handlers`의 `blocked_vpw`를 동적 판정으로 교체
5. `ENTRY_PIPELINE` 로그 상세화
6. 1주일 정도 관측 후 threshold 튜닝

## 초기 운영 기준 제안

가장 먼저 실전에 올릴 만한 보수적 시작값은 아래다.

- `WINDOW_SECONDS = 5`
- `MIN_STRENGTH_BASE = 95`
- `TARGET_STRENGTH_DELTA = 10`
- `MIN_WINDOW_BUY_VALUE = 30_000_000`
- `MIN_WINDOW_BUY_RATIO = 0.60`
- `SCALP_VPW_STRONG_ABSOLUTE = 130`

이 조합은 현재 `120 절대값`보다 더 빠르게 잡을 수 있으면서도, 단순 노이즈를 거래대금으로 걸러낼 가능성이 높다.

## 결론

이번 아이디어는 적절하다. 특히 현재 구조에서는 "체결강도 절대값"보다 "짧은 창의 상승 기울기 + 실제 매수 체결대금"이 스캘핑 진입 품질을 더 잘 설명할 가능성이 높다.

다만 구현 위치는 반드시 `state_handlers`가 아니라 `kiwoom_websocket`의 종목별 실시간 메모리 축적을 기준으로 가야 한다. 그래야 틱 유실 없이 진짜 윈도우 모멘텀을 계산할 수 있다.

다음 단계는 이 문서 기준으로 `Phase 1 관측 전용` 구현부터 들어가는 것을 권장한다.

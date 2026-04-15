# 작업지시서: 스캘핑 AI 하방카운트 도달 시 1회 물타기 후 보유 재진입

> 작성일: 2026-04-15  
> 우선순위: 중  
> 실행 시점: POSTCLOSE 또는 다음 장 전 배포  
> 토글: `SCALP_AI_EXIT_AVGDOWN_ENABLED` (기본값 `False`, 카나리 후 활성화)

## 구현 결과 문서

- [2026-04-15-scalp-ai-exit-avgdown-implementation-result.md](./2026-04-15-scalp-ai-exit-avgdown-implementation-result.md)

---

## 1. 배경 및 목적

현재 스캘핑 보유 로직에서 AI 하방 점수가 `SCALP_AI_EARLY_EXIT_MAX_SCORE` 이하로  
`SCALP_AI_EARLY_EXIT_CONSECUTIVE_HITS`회 (기본 3회) 연속 확인되면 **즉시 조기손절**한다.

```
ai_low_score_hits >= ai_exit_needed_hits → is_sell_signal = True (scalp_ai_early_exit)
```

이 로직은 하방 확인 직후 반등하는 경우에도 강제 청산해버리는 단점이 있다.  
**제안**: 하방카운트 도달 첫 1회는 즉시 청산 대신 물타기(AVG_DOWN)를 실행하고  
`ai_low_score_hits`를 초기화한 뒤 보유 로직으로 복귀한다.  
이후 동일 종목에서 하방카운트가 다시 도달하면 원래대로 즉시 청산한다.

---

## 2. 요구사항

| # | 요건 |
|---|------|
| R1 | 토글 상수 `SCALP_AI_EXIT_AVGDOWN_ENABLED` 추가, 기본값 `False` |
| R2 | 토글 ON 상태에서 하방카운트 도달 시 즉시 청산 대신 AVG_DOWN 트리거 |
| R3 | 물타기는 **1회**로 제한. 동일 종목 내 2번째 도달 시 원래 청산 로직 실행 |
| R4 | 물타기 실행 후 `ai_low_score_hits` 초기화, 보유 로직 재진입 |
| R5 | 물타기 주문 실패(예산 부족, 수량 0) 시 → 안전하게 원래 청산 로직으로 fallback |
| R6 | 기존 `SCALPING_ENABLE_AVG_DOWN` (가격낙폭 기반) 과 **독립**으로 동작 |
| R7 | 로그 및 HOLDING_PIPELINE 이벤트에 트리거 경위 명시 |

---

## 3. 현재 코드 구조

### 3.1 하방카운트 누적 및 청산 트리거 위치

**파일**: `src/engine/sniper_state_handlers.py`

```
L3117~3122  AI 점수 평가 → ai_low_score_hits 누적/초기화
L3322~3336  ai_low_score_hits >= ai_exit_needed_hits → is_sell_signal = True
```

관련 핵심 코드 (현재):

```python
# L3322~3336
elif (
    not legacy_broker_recovered
    and
    held_sec >= ai_exit_min_hold_sec
    and profit_rate <= ai_exit_min_loss_pct
    and current_ai_score <= ai_exit_score_limit
    and ai_low_score_hits >= ai_exit_needed_hits
):
    is_sell_signal = True
    sell_reason_type = "LOSS"
    reason = (
        f"🚨 AI 하방 리스크 연속 확인 {ai_low_score_hits}/{ai_exit_needed_hits}회 "
        f"({current_ai_score:.0f}점). 조기 손절 ({profit_rate:.2f}%)"
    )
    exit_rule = "scalp_ai_early_exit"
```

### 3.2 물타기 실행 인프라

**파일**: `src/engine/sniper_scale_in.py`  
- `evaluate_scalping_avg_down(stock, profit_rate)` → 가격낙폭 기반 AVG_DOWN 평가  
- 반환: `{"should_add": bool, "add_type": "AVG_DOWN", "reason": str, ...}`

**파일**: `src/engine/sniper_state_handlers.py`  
- `execute_scale_in_order(*, stock, code, ws_data, action, admin_id)` → 실제 주문 전송  
- `avg_down_count` 증가는 **주문 전송 시점이 아닌 체결 영수증 처리 시점**에 발생  
  (`src/engine/sniper_execution_receipts.py` L601~602, `pending_add_counted` 플래그로 중복 방지)

### 3.3 기존 `SCALPING_ENABLE_AVG_DOWN`과의 관계

| 구분 | 기존 (가격낙폭 기반) | 신규 (AI카운트 기반) |
|------|---------------------|---------------------|
| 토글 | `SCALPING_ENABLE_AVG_DOWN` | `SCALP_AI_EXIT_AVGDOWN_ENABLED` |
| 트리거 조건 | `profit_rate` 낙폭 구간 | `ai_low_score_hits >= ai_exit_needed_hits` |
| 평가 함수 | `evaluate_scalping_avg_down()` | 직접 action dict 생성 (평가함수 우회) |
| 회수 제한 | `SCALPING_MAX_AVG_DOWN_COUNT` | 별도 플래그 `scalp_ai_exit_avgdown_done` |

두 조건이 동시에 발생하는 경우 → **신규 AI카운트 기반 물타기를 우선** 처리하고  
가격낙폭 기반 `evaluate_scalping_avg_down()`의 `avg_down_count_limit` 체크는  
신규 물타기가 먼저 `avg_down_count`를 소모하므로 자연스럽게 차단된다.

---

## 4. 구현 상세

### 4.1 상수 추가

**파일**: `src/utils/constants.py`  
위치: `SCALP_AI_EARLY_EXIT_CONSECUTIVE_HITS` 인근 (L135 부근)

```python
SCALP_AI_EXIT_AVGDOWN_ENABLED: bool = False  # AI 하방카운트 도달 시 즉시손절 대신 1회 물타기 후 보유 재진입
```

### 4.2 stock 딕셔너리 신규 키

런타임 stock 딕셔너리에 추가되는 필드:

| 키 | 타입 | 의미 | 초기값 |
|---|---|---|---|
| `scalp_ai_exit_avgdown_done` | `bool` | 이 종목에서 AI카운트 기반 물타기가 이미 1회 실행되었음 | `False` |

DB 저장 불필요 (메모리 런타임 상태).

### 4.3 `sniper_state_handlers.py` 수정

**수정 위치**: L3322~3336의 `elif` 블록 교체

**현재 로직 (수정 전)**:
```python
elif (
    not legacy_broker_recovered
    and held_sec >= ai_exit_min_hold_sec
    and profit_rate <= ai_exit_min_loss_pct
    and current_ai_score <= ai_exit_score_limit
    and ai_low_score_hits >= ai_exit_needed_hits
):
    is_sell_signal = True
    sell_reason_type = "LOSS"
    reason = (
        f"🚨 AI 하방 리스크 연속 확인 {ai_low_score_hits}/{ai_exit_needed_hits}회 "
        f"({current_ai_score:.0f}점). 조기 손절 ({profit_rate:.2f}%)"
    )
    exit_rule = "scalp_ai_early_exit"
```

**수정 후 로직**:
```python
elif (
    not legacy_broker_recovered
    and held_sec >= ai_exit_min_hold_sec
    and profit_rate <= ai_exit_min_loss_pct
    and current_ai_score <= ai_exit_score_limit
    and ai_low_score_hits >= ai_exit_needed_hits
):
    ai_exit_avgdown_enabled = bool(
        getattr(TRADING_RULES, 'SCALP_AI_EXIT_AVGDOWN_ENABLED', False)
    )
    ai_exit_avgdown_done = bool(stock.get('scalp_ai_exit_avgdown_done', False))

    if ai_exit_avgdown_enabled and not ai_exit_avgdown_done:
        # ── 1회 물타기 후 보유 재진입 ──────────────────────────────
        action = {
            "should_add": True,
            "add_type": "AVG_DOWN",
            "reason": "scalp_ai_exit_avgdown",
            "qty": 0,   # execute_scale_in_order 내에서 calc_scale_in_qty로 계산
            "price": 0,
        }
        add_result = _process_scale_in_action(stock, code, ws_data, action, admin_id)

        if add_result:
            # 물타기 성공 → hits 초기화, 플래그 설정, 보유 유지
            stock['scalp_ai_exit_avgdown_done'] = True
            stock['ai_low_score_loss_hits'] = 0
            ai_low_score_hits = 0
            _log_holding_pipeline(
                stock, code, "scalp_ai_exit_avgdown",
                profit_rate=f"{profit_rate:+.2f}",
                ai_score=f"{current_ai_score:.0f}",
                low_score_hits=f"{ai_exit_needed_hits}/{ai_exit_needed_hits}",
                held_sec=int(held_sec),
                note="ai_exit_avgdown_triggered_reset_hits",
            )
            print(
                f"🔄 [AI카운트 물타기] {stock['name']}({code}) "
                f"하방카운트 {ai_exit_needed_hits}회 도달 → AVG_DOWN 실행 후 보유 재진입 "
                f"(수익: {profit_rate:.2f}%, AI: {current_ai_score:.0f}점)"
            )
        else:
            # 물타기 실패(예산 부족 등) → 원래 청산 로직으로 fallback
            is_sell_signal = True
            sell_reason_type = "LOSS"
            reason = (
                f"🚨 AI 하방 리스크 연속 확인 {ai_low_score_hits}/{ai_exit_needed_hits}회 "
                f"({current_ai_score:.0f}점). 조기 손절 [{profit_rate:.2f}%] "
                f"(물타기 주문 실패 — fallback)"
            )
            exit_rule = "scalp_ai_early_exit"
    else:
        # 토글 OFF 또는 물타기 이미 1회 소진 → 원래 즉시 청산
        is_sell_signal = True
        sell_reason_type = "LOSS"
        reason = (
            f"🚨 AI 하방 리스크 연속 확인 {ai_low_score_hits}/{ai_exit_needed_hits}회 "
            f"({current_ai_score:.0f}점). 조기 손절 ({profit_rate:.2f}%)"
            + (" [물타기 소진]" if ai_exit_avgdown_done else "")
        )
        exit_rule = "scalp_ai_early_exit"
```

---

## 5. 실행 흐름 다이어그램

```
ai_low_score_hits >= ai_exit_needed_hits 도달
          │
          ▼
  SCALP_AI_EXIT_AVGDOWN_ENABLED?
    No  ──────────────────────────────────────────────→ 즉시 청산 (scalp_ai_early_exit)
    Yes │
        ▼
  scalp_ai_exit_avgdown_done == True?
    Yes ──────────────────────────────────────────────→ 즉시 청산 (scalp_ai_early_exit) [물타기 소진]
    No  │
        ▼
  _process_scale_in_action() → execute_scale_in_order()
        │
        ├─ 성공 → scalp_ai_exit_avgdown_done = True
        │         ai_low_score_loss_hits = 0
        │         → 보유 로직 재진입 (is_sell_signal = False)
        │
        └─ 실패 → 즉시 청산 fallback (scalp_ai_early_exit)
```

---

## 6. 수정 파일 목록

| 파일 | 변경 내용 |
|------|----------|
| `src/utils/constants.py` | `SCALP_AI_EXIT_AVGDOWN_ENABLED: bool = False` 상수 추가 |
| `src/engine/sniper_state_handlers.py` | L3322~3336 `elif` 블록 교체 (위 4.3 참조) |
| `src/tests/test_sniper_scale_in.py` | 신규 동작 케이스 3개 추가 (아래 7항 참조) |

`sniper_scale_in.py`는 **수정하지 않는다**. 물타기 action dict는 호출부에서 직접 생성하며,  
`evaluate_scalping_avg_down()`은 별도 평가 경로로 그대로 유지된다.

---

## 7. 테스트 케이스

`src/tests/test_sniper_scale_in.py` 또는 신규 `test_scalp_ai_exit_avgdown.py`에 추가.

### TC-1: 토글 OFF → 기존 동작 유지 (즉시 청산)
```python
TRADING_RULES.SCALP_AI_EXIT_AVGDOWN_ENABLED = False
stock = {"ai_low_score_loss_hits": 3, "scalp_ai_exit_avgdown_done": False, ...}
# 결과: is_sell_signal = True, exit_rule = "scalp_ai_early_exit"
```

### TC-2: 토글 ON, 첫 도달, 물타기 성공 → 보유 재진입
```python
TRADING_RULES.SCALP_AI_EXIT_AVGDOWN_ENABLED = True
stock = {"ai_low_score_loss_hits": 3, "scalp_ai_exit_avgdown_done": False, ...}
# _process_scale_in_action mock → 성공 반환
# 결과: is_sell_signal = False
#        stock['scalp_ai_exit_avgdown_done'] == True
#        stock['ai_low_score_loss_hits'] == 0
```

### TC-3: 토글 ON, 첫 도달, 물타기 실패 → 청산 fallback
```python
TRADING_RULES.SCALP_AI_EXIT_AVGDOWN_ENABLED = True
stock = {"ai_low_score_loss_hits": 3, "scalp_ai_exit_avgdown_done": False, ...}
# _process_scale_in_action mock → None 반환 (실패)
# 결과: is_sell_signal = True, exit_rule = "scalp_ai_early_exit"
#        reason에 "물타기 주문 실패" 포함
```

### TC-4: 토글 ON, 물타기 이미 소진 → 즉시 청산
```python
TRADING_RULES.SCALP_AI_EXIT_AVGDOWN_ENABLED = True
stock = {"ai_low_score_loss_hits": 3, "scalp_ai_exit_avgdown_done": True, ...}
# 결과: is_sell_signal = True, exit_rule = "scalp_ai_early_exit"
#        reason에 "[물타기 소진]" 포함
```

---

## 8. 배포 절차 (토글 기반 카나리)

```
1단계 (기본값 유지)
  constants.py: SCALP_AI_EXIT_AVGDOWN_ENABLED = False
  → 기존 동작 100% 유지, 코드 배포 후 동작 이상 없음 확인

2단계 (카나리 활성화)
  config_prod.json에 "SCALP_AI_EXIT_AVGDOWN_ENABLED": true 추가
  또는 constants.py 직접 수정 후 봇 재시작
  → 장중 하방카운트 발생 시 물타기 → 보유 재진입 동작 확인

롤백
  config_prod.json에서 키 제거 또는 false로 변경 → 봇 재시작
  (stock 런타임 플래그는 재시작 시 초기화됨)
```

---

## 9. 주의사항

1. **`avg_down_count` 증가 시점**: `execute_scale_in_order`는 주문 전송만 수행한다.  
   `avg_down_count` 증가는 체결 영수증 처리(`sniper_execution_receipts.py` L601~602) 시점에 발생하며,  
   `pending_add_counted` 플래그로 중복 방지된다.  
   이로 인해 기존 `evaluate_scalping_avg_down()`의 `avg_down_count_limit` 차단은  
   **체결 확인 이후 다음 틱부터** 적용된다 (같은 틱 내 이중 물타기 위험은 설계상 낮음).

2. **`SCALPING_MAX_AVG_DOWN_COUNT`는 이 경로와 무관**: `calc_scale_in_qty()`는 `avg_down_count`와  
   `SCALPING_MAX_AVG_DOWN_COUNT`를 참조하지 않는다. qty=0이 되는 실제 조건은  
   잔여 주문가능금액(`deposit`) 부족 또는 `MAX_POSITION_PCT` 한도 소진이다.  
   `SCALPING_MAX_AVG_DOWN_COUNT` 설정값은 이 물타기 경로의 성공/실패에 영향 없음.

2. **물타기 후 `ai_exit_min_loss_pct` 재평가**: 물타기로 평단이 낮아지므로 다음 AI 사이클에서  
   `profit_rate`가 조건을 벗어날 수 있다. 이는 의도된 동작이다(보유 재진입 효과).

3. **kiwoom_sniper_v2.py 동일 조건 존재**: `src/engine/kiwoom_sniper_v2.py` L815~820에도  
   동일한 하방카운트 청산 조건이 존재한다. 해당 파일의 역할(레거시/브로커 복구 경로)을  
   확인하여 동일 패턴 적용 여부를 판단한다. (**배포 전 확인 항목**)

---

## 10. 미결 확인 항목 (구현 전 오퍼레이터 확인 필요)

| 항목 | 질문 | 기본 가정 |
|------|------|-----------|
| A | qty=0 fallback의 실제 원인은? | `deposit` 부족 또는 `MAX_POSITION_PCT` 소진. `SCALPING_MAX_AVG_DOWN_COUNT`와 무관 — 확인 불필요 |
| B | `kiwoom_sniper_v2.py` L815~820에도 동일 패턴 적용할 것인가? | 우선 `sniper_state_handlers.py`만 적용, 추후 확장 |
| C | 물타기 수량 비율을 별도로 지정할 것인가? | `calc_scale_in_qty` 기존 AVG_DOWN 로직 그대로 사용 |

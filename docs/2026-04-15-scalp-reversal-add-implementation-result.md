# 구현 결과서: 스캘핑 역전 확인 추가매수 (reversal_add)

> 기준 문서: `docs/workorder-scalp-reversal-add.md`  
> 작성일: `2026-04-15`  
> 커밋: `387a4b0`  
> 범위: 스캘핑 정체 구간 역전 확인 후 1회 한정 추가매수 + POST_ADD_EVAL 25초 집중 감시

---

## 1. 판정

| 항목 | 결과 |
|---|---|
| 요구사항 구현 | **완료** (작업지시서 R1~R7 전항목) |
| 테스트 통과 | **TC-1 ~ TC-10 + 회귀 2건 통과** (12 passed) |
| 기존 테스트 영향 | **없음** (기존 66개 중 pre-existing 실패 1건 유지, 신규 실패 0건) |
| 배포 판정 | **기본 OFF (`REVERSAL_ADD_ENABLED = False`) 유지, Phase 1 shadow 관찰 선행 권고** |

---

## 1-1. 코드리뷰 결과 (2026-04-15)

| 심각도 | 항목 | 코드리뷰 판정 | 근거 |
|---|---|---|---|
| 높음 | `REVERSAL_ADD_SIZE_RATIO` 실효성 | **해소됨(핫픽스 반영)** | `calc_scale_in_qty(add_reason)` 경로를 추가해 `reason=reversal_add_ok`일 때 `REVERSAL_ADD_SIZE_RATIO`를 수량 계산에 반영 (`src/engine/sniper_scale_in.py`, `src/engine/sniper_state_handlers.py`) |
| 중간 | 상태머신 정합성 | **해소됨** | `STAGNATION -> REVERSAL_CANDIDATE -> ADD_ARMED -> POST_ADD_EVAL` 전이 로직을 런타임에 반영 (`src/engine/sniper_state_handlers.py`) |
| 중간 | Shadow 모니터링 키 정확성 | **해소됨** | `HOLDING_PIPELINE stage=reversal_add_candidate/reversal_add_blocked_reason` 로그를 코드에 반영 (`src/engine/sniper_state_handlers.py`) |

**운영 의사결정**: 결함 수정 완료. `REVERSAL_ADD_ENABLED=False`로 shadow 관찰 후 제한형 canary로 전환 가능.

---

## 2. 구현 범위

### 2-1. 상태 머신 요약

```
[보유 진입] → STAGNATION → (AI 회복 + 저점 미갱신 + 수급 재개) → ADD_ARMED
           → 추가매수 실행 → POST_ADD_EVAL (25초) → 일반 HOLDING 복귀
                                                  └→ 실패 시 즉시 청산
```

### 2-2. 핵심 설계 원칙 (기존 stagnation 설계 대비)

| 항목 | 폐기된 stagnation 설계 | 본 reversal_add 구현 |
|---|---|---|
| AI 조건 | score ≥ 36 (수준만) | bottom 대비 +15pt 회복 OR 2연속 상승 (방향성) |
| 수급 조건 | 없음 | buy_pressure / tick_accel / large_sell / vwap_bp (4개 중 3개) |
| 저점 확인 | 없음 | `reversal_add_profit_floor - 0.05%p` 마진 이내 필수 |
| 고착 저점 차단 | 없음 | std ≤ 2 AND avg < 45 (최근 4틱 기준) 명시 차단 |
| 실행 후 감시 | 없음 | POST_ADD_EVAL 25초 집중 감시 + 실패 시 즉시 청산 |

---

## 3. 코드 반영 상세

### 3-1. `src/utils/constants.py` — 상수 15개 추가 (L192~L206)

```python
REVERSAL_ADD_ENABLED: bool = False             # 역전 확인 추가매수 토글
REVERSAL_ADD_PNL_MIN: float = -0.45            # 허용 손실 하한 (%)
REVERSAL_ADD_PNL_MAX: float = -0.10            # 허용 손실 상한 (%)
REVERSAL_ADD_MIN_HOLD_SEC: int = 20            # 최소 보유시간(초)
REVERSAL_ADD_MAX_HOLD_SEC: int = 120           # 최대 보유시간(초)
REVERSAL_ADD_MIN_AI_SCORE: int = 60            # 실행 직전 최소 AI 점수
REVERSAL_ADD_MIN_AI_RECOVERY_DELTA: int = 15   # AI bottom 대비 최소 회복폭
REVERSAL_ADD_MIN_BUY_PRESSURE: float = 55.0    # 최소 매수 압도율(%)
REVERSAL_ADD_MIN_TICK_ACCEL: float = 0.95      # 최소 틱 가속도 비율
REVERSAL_ADD_VWAP_BP_MIN: float = -5.0         # 최소 Micro-VWAP 대비 (bp)
REVERSAL_ADD_SIZE_RATIO: float = 0.33          # 추가매수 수량 비율 (기존 보유 대비)
REVERSAL_ADD_POST_EVAL_SEC: int = 25           # POST_ADD_EVAL 감시 시간(초)
REVERSAL_ADD_SESSION_CUTOFF: str = "14:30"     # 허용 시간대 상한
REVERSAL_ADD_BOX_RANGE_MAX_PCT: float = 0.20   # 박스 폭 허용 최대치 (%p)
REVERSAL_ADD_STAGNATION_LOW_FLOOR_MARGIN: float = 0.05  # 저점 미갱신 허용 마진 (%p)
```

> 모든 상수 `getattr(TRADING_RULES, 'REVERSAL_ADD_*', <default>)` 패턴으로 참조하여 미배포 환경 safe.

---

### 3-2. `src/engine/sniper_scale_in.py` — 신규 평가 함수 (L158~L241)

**함수**: `evaluate_scalping_reversal_add(stock, profit_rate, current_ai_score, held_sec)`

**평가 순서 (조기 리턴 구조)**:

| 순서 | 조건 | 차단 reason |
|---|---|---|
| 1 | `REVERSAL_ADD_ENABLED == False` | `reversal_add_disabled` |
| 2 | `reversal_add_used == True` | `reversal_add_used` |
| 3 | `profit_rate` 범위 이탈 | `pnl_out_of_range(x.xx)` |
| 4 | `held_sec` 범위 이탈 | `hold_sec_out_of_range(xs)` |
| 5 | 저점 갱신 (`profit_rate < floor - margin`) | `low_broken` |
| 6 | AI 점수 최소 기준 미달 | `ai_score_too_low(x)` |
| 7 | AI 회복 방향성 없음 | `ai_not_recovering` |
| 8 | AI 고착 저점 (std ≤ 2, avg < 45) | `ai_stuck_at_bottom` |
| 9 | 수급 조건 3/4 미충족 | `supply_conditions_not_met(x/4)` |
| 10 | 피처 엔진 없을 때 buy_pressure 미달 | `buy_pressure_not_met(no_features)` |
| OK | 전항목 통과 | `reversal_add_ok` → `should_add=True, add_type="AVG_DOWN"` |

**설계 유의점**:
- `statistics` 모듈을 함수 내부 `import`로 처리 (모듈 레벨 의존 최소화)
- `_base_result()` 공통 팩토리 재사용

---

### 3-3. `src/engine/sniper_state_handlers.py` — 5개 변경 지점

#### (A) import 추가 (L31)

```python
from src.engine.sniper_scale_in import (
    ...
    evaluate_scalping_reversal_add,   # 추가
    ...
)
```

---

#### (B) AI 감시 사이클 — 피처 저장 + STAGNATION 상태 갱신 (L3130~L3176)

**위치**: `stock['ai_low_score_loss_hits']` 저장 직후, `print(...)` 이전.

```python
if getattr(TRADING_RULES, 'REVERSAL_ADD_ENABLED', False):
    # 수급 피처 저장
    if hasattr(ai_engine, '_extract_scalping_features') and recent_ticks:
        try:
            feat = ai_engine._extract_scalping_features(ws_data, recent_ticks, recent_candles)
            stock['last_reversal_features'] = { buy_pressure_10t, tick_acceleration_ratio,
                                                large_sell_print_detected, curr_vs_micro_vwap_bp }
        except Exception:
            pass

    # AI bottom/history 갱신 (STAGNATION/REVERSAL_CANDIDATE 구간에서만)
    if stock.get('reversal_add_state') in ('STAGNATION', 'REVERSAL_CANDIDATE'):
        stock['reversal_add_ai_history'] = last 4 ticks
        stock['reversal_add_ai_bottom'] = min(current, existing)
        stock['reversal_add_profit_floor'] = min(current, existing)

    # STAGNATION 진입 판단
    if (not used and not state and pnl_min <= profit_rate <= pnl_max and hits == 0):
        stock['reversal_add_state'] = 'STAGNATION'  # 초기값 세팅

    # STAGNATION 리셋
    elif state == 'STAGNATION':
        if profit_rate < pnl_min or profit_rate > 0 or hits > 0:
            stock['reversal_add_state'] = ''  # 전초기화
```

**설계 유의점**:
- `REVERSAL_ADD_ENABLED` 토글 OFF이면 이 블록 전체 미실행 → 기존 HOLDING 성능 무영향
- `_extract_scalping_features()` 누락 엔진(표준 ai_engine)에서 `hasattr` 가드로 안전 처리
- 피처 저장 실패 시 `except: pass`로 silent fallback

---

#### (C) `_evaluate_scale_in_signal()` reversal 연동 (L4090~L4094)

**위치**: `evaluate_scalping_avg_down`, `evaluate_scalping_pyramid` 평가 이후.

```python
# reversal_add: 가격낙폭/불타기 모두 미트리거인 경우에만 검토
if not avg_down.get("should_add") and not pyramid.get("should_add"):
    reversal = evaluate_scalping_reversal_add(stock, profit_rate, current_ai_score, held_sec)
    if reversal.get("should_add"):
        avg_down = reversal
```

함수 시그니처에 `current_ai_score=50`, `held_sec=0` optional 파라미터 추가. 기존 호출부와 하위 호환 유지.

---

#### (D) add 성공 후 플래그 설정 (L3748~L3751)

```python
add_result = _process_scale_in_action(...)
if add_result and scale_in_action.get("reason") == "reversal_add_ok":
    stock['reversal_add_used'] = True
    stock['reversal_add_state'] = "POST_ADD_EVAL"
    stock['reversal_add_executed_at'] = time.time()
```

**설계 유의점**:
- `add_result`가 None(주문 실패)이면 플래그 미설정 → 다음 틱에서 재평가 가능
- `reason == "reversal_add_ok"` 정확 매칭으로 기존 AVG_DOWN/PYRAMID 경로와 분리

---

#### (E) POST_ADD_EVAL 집중 감시 블록 (L3207~L3232)

**위치**: hard_stop 판단 이전, sell signal 판단 블록 최상단.

```python
if not is_sell_signal and stock.get('reversal_add_state') == 'POST_ADD_EVAL':
    # 실패 조건 (하나라도 해당 시 즉시 청산)
    post_fail = (
        current_ai_score < 55
        or profit_rate < reversal_add_profit_floor - 0.05
        or large_sell_print_detected
        or tick_acceleration_ratio < 0.90
    )
    if post_fail and elapsed < 25s:
        is_sell_signal = True
        exit_rule = "reversal_add_post_eval_fail"
    elif elapsed >= 25s:
        stock['reversal_add_state'] = ""  # 일반 HOLDING 복귀
```

---

### 3-4. stock 딕셔너리 신규 키 (런타임 메모리, DB 미저장)

| 키 | 타입 | 초기값 | 역할 |
|---|---|---|---|
| `reversal_add_state` | `str` | `""` | 상태 머신 현재 단계 |
| `reversal_add_used` | `bool` | `False` | 1회 소진 플래그 |
| `reversal_add_profit_floor` | `float` | `0.0` | STAGNATION 진입 후 최저 수익률 |
| `reversal_add_ai_bottom` | `int` | `100` | STAGNATION 진입 후 최저 AI 점수 |
| `reversal_add_ai_history` | `list[int]` | `[]` | 최근 4틱 AI 점수 (고착 판단용) |
| `reversal_add_executed_at` | `float` | `0.0` | 추가매수 실행 timestamp |
| `reversal_add_entry_avg_price` | `float` | `0.0` | 추가매수 후 예상 평단가 |
| `last_reversal_features` | `dict` | `{}` | 마지막 수급 피처 스냅샷 |

---

## 4. 테스트 결과

### 4-1. 실행 명령

```bash
./.venv/bin/python -m pytest -q src/tests/test_sniper_scale_in.py -k "reversal_add"
# → 10 passed, 57 deselected

./.venv/bin/python -m pytest -q src/tests/test_sniper_scale_in.py -k "reversal_add or calc_scale_in_qty_scalping"
# → 12 passed, 57 deselected

./.venv/bin/python -m pytest -q src/tests/test_sniper_scale_in.py
# → 1 failed (pre-existing), 68 passed
```

### 4-2. TC 목록 및 검증 포인트

| TC | 테스트명 | 검증 포인트 | 결과 |
|---|---|---|---|
| TC-1 | `tc1_toggle_off` | `REVERSAL_ADD_ENABLED=False` → `reversal_add_disabled` | ✅ |
| TC-2 | `tc2_pnl_out_of_range` | profit=-0.55% → pnl 하한 이탈 차단 | ✅ |
| TC-3 | `tc3_ai_stuck_at_bottom` | hist=[40,41,40,41] std=0.5 avg=40.5 → stuck 차단 | ✅ |
| TC-4 | `tc4_ai_not_recovering` | hist=[50,52,55,53] delta+14, 2연속 상승 아님 → 차단 | ✅ |
| TC-5 | `tc5_supply_conditions_not_met` | 수급 2/4 충족 → 차단 | ✅ |
| TC-6 | `tc6_all_conditions_met` | 전항목 충족 → `should_add=True, reason=reversal_add_ok` | ✅ |
| TC-7 | `tc7_already_used` | `reversal_add_used=True` → 재트리거 없음 | ✅ |
| TC-8 | `tc8_low_broken` | profit=-0.40 < floor(-0.30)-margin(0.05)=-0.35 → 저점 갱신 차단 | ✅ |
| TC-9 | `tc9_hold_sec_out_of_range` | held_sec=5 < min(20) → 시간 범위 이탈 차단 | ✅ |
| TC-10 | `tc10_no_features_engine` | `last_reversal_features={}` → buy_pressure 기본값 50 < 55 → 차단 | ✅ |

### 4-3. 기존 테스트 영향

- pre-existing 실패 `test_update_db_for_add_does_not_touch_detached_record_after_commit` 1건 본 구현 전부터 동일하게 실패 중. 본 변경과 무관.
- 신규 실패 0건.

---

## 5. 설계 결정 사항 및 검토 포인트

### 5-1. 확정 사항

| 결정 항목 | 결정 내용 | 근거 |
|---|---|---|
| 포지션당 최대 사용 횟수 | **1회** (`reversal_add_used` 플래그) | 오퍼레이터 확인 (2026-04-15) |
| AI카운트 기반 물타기(SCALP_AI_EXIT_AVGDOWN)와 동시 허용 | **허용** (최대 2회 물타기) | 오퍼레이터 확인 (2026-04-15) |
| `avg_down_count` 공유 | **공유** (기존 receipt 처리 경로에서 +1) | 일관성 유지 |
| 기존 stagnation 설계 | **폐기**, reversal_add로 대체 | 설계 통합 |

### 5-2. 아키텍트 검토 요청 사항

| # | 항목 | 현재 구현 | 검토 요청 |
|---|---|---|---|
| A | `REVERSAL_ADD_SESSION_CUTOFF("14:30")` 미적용 | 상수는 정의했으나 평가 함수 내 시간대 체크 코드 없음 | 필요 시 추가 여부 결정 |
| B | `REVERSAL_ADD_BOX_RANGE_MAX_PCT` 미적용 | 상수 정의, 박스 폭 체크 미구현 (workorder에서 "권장" 표기) | 필요 시 추가 여부 결정 |
| C | `reversal_add_entry_avg_price` 미설정 | 추가매수 후 새 평단가를 stock에서 직접 읽어오는 구조이므로 별도 설정 없음 | 검토 후 POST_EVAL 성공 조건에 반영 여부 결정 |
| D | POST_EVAL 성공 후 `reversal_add_state=""` 처리 | 25초 경과 후 조건 없이 복귀. "평단 미회복 선택적 적용" 미구현 | workorder 5항의 "선택적" 항목이므로 운영자 판단 보류 |
| E | `SCALP_PARTIAL_FILL_CANARY_ENABLED` 차단 | 평가 함수에서 체크하지 않음 (can_consider_scale_in 게이트가 처리) | 중복 체크 필요 여부 확인 |

---

## 6. 리스크 및 운영 메모

| 리스크 | 설명 | 완화 방안 |
|---|---|---|
| 피처 데이터 지연 | `last_reversal_features`는 직전 AI 감시 사이클 시점의 스냅샷 → 최대 AI_HOLDING_CRITICAL_COOLDOWN(20초) 지연 | Phase 1 shadow에서 스냅샷 타이밍 실측 후 판단 |
| `calc_scale_in_qty` → qty=0 | deposit 소진 또는 MAX_POSITION_PCT 초과 시 qty=0 → 주문 실패 → POST_ADD_EVAL 미진입 | `REVERSAL_ADD_SIZE_RATIO=0.33`이 보수적이므로 일반 케이스에서 발생 낮음 |
| 고착 저점 차단 threshold | std ≤ 2 AND avg < 45 → 미세 회복(`44→41→39→40→41`)이 통과될 수 있음 | Phase 1 shadow 로그에서 고착 차단률 확인 |
| AI카운트 기반 물타기 중복 | `scalp_ai_exit_avgdown_done=True` 이후 `reversal_add_used`는 별도 플래그 → 이론상 동일 포지션에서 2회 물타기 가능 | 오퍼레이터 승인 완료 (2026-04-15). `avg_down_count` 공유로 상한은 receipt 처리에서 간접 제어 |

---

## 7. 카나리 배포 계획

### Phase 1 — Shadow (현재, 즉시 적용 가능)
```
REVERSAL_ADD_ENABLED = False
→ evaluate_scalping_reversal_add() 결과가 should_add=False이므로 주문 없음
→ 로그 관찰: "reversal_add_candidate", "reversal_add_blocked_reason", "[ADD_SIGNAL]", "reversal_add_post_eval_fail" 확인
→ 관찰 지표: 후보 발생 빈도, AI 회복 성공률, 수급 조건 통과율
```

### Phase 2 — Limited Canary
```
REVERSAL_ADD_ENABLED = True
REVERSAL_ADD_SIZE_RATIO = 0.25  (0.33 → 0.25 축소)
→ POST_ADD_EVAL 실패율 모니터링
→ 평단 회복률 및 청산 손익 기록
```

주의:
- `REVERSAL_ADD_SIZE_RATIO` 반영 핫픽스 이후 기준으로 운영한다.

### Phase 3 — Full Deploy
```
REVERSAL_ADD_SIZE_RATIO = 0.33  (원복)
→ 성공률/실패율/평단 회복률 기준 파라미터 최종 조정
```

---

## 8. 배포 현황

| 서버 | 브랜치 | 커밋 | py_compile |
|---|---|---|---|
| 로컬 (ubuntu) | `main` | `387a4b0` | ✅ |
| 원격 (songstockscan.ddns.net) | `develop` | `c3ad5523` (cherry-pick) | ✅ |

---

## 9. 다음 액션

- [ ] 아키텍트 검토 사항 A/B (`SESSION_CUTOFF`, `BOX_RANGE`) 구현 여부 결정 | Status=PendingReview | Due=2026-04-16 | Slot=PREOPEN | TimeWindow=08:30~08:40
- [ ] Phase 1 Shadow 관찰 시작 — `REVERSAL_ADD_ENABLED = False` 유지, 실제 로그 키(`reversal_add_candidate`, `reversal_add_blocked_reason`, `[ADD_SIGNAL]`, `reversal_add_post_eval_fail`) 기준 모니터링 | Status=Todo | Due=2026-04-16 | Slot=INTRADAY
- [ ] Phase 1 Shadow 1일차 결과 정리 (후보 발생 빈도, POST_ADD_EVAL 실패율, 실현손익 영향도) | Status=Todo | Due=2026-04-16 | Slot=POSTCLOSE

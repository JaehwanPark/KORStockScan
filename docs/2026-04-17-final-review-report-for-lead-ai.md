# 스캘핑 패턴 분석 최종검토보고서 — 총괄 AI 전달용

작성일: 2026-04-17  
분석 출처: `analysis/claude_scalping_pattern_lab/` (독립 분석 코드베이스)  
분석 기간: 2026-04-01 ~ 2026-04-17 (12 거래일, 151건)

---

## 1. 판정

### 1-1. 다음 액션 중 코드 수정이 필요한 항목

분석에서 제시된 5개 EV 개선 항목의 구현 상태를 교차 점검한 결과, 아래와 같이 분류됐다.

| # | 항목 | 현재 상태 | 코드 수정 필요 | 긴급도 |
|---|---|---|---|---|
| A | `split_entry_rebase_integrity_shadow` stage 수집 | **구현 완료** (`sniper_execution_receipts.py:148`) | 불필요 | — |
| B | `split_entry_immediate_recheck_shadow` stage 수집 | **구현 완료** (`sniper_execution_receipts.py:178`) | 불필요 | — |
| C | `protect_trailing_stop` stale 보호선 + 라벨 오표시 | **미수정** (원인 파악 완료, 코드 보류 상태) | **필요** | 🔴 2026-04-17 15:40~16:10 KST |
| D | `same-symbol split-entry soft-stop cooldown` shadow | **미구현** (초안만 존재) | **필요** | 🟡 2026-04-17 16:10~16:20 KST |
| E | `partial-only timeout shadow` | **미구현** | **필요** | 🟡 오늘(2026-04-17) 16:20 KST |

**코드 수정이 필요한 항목은 C, D, E 3건이다.**  
C는 현재 장중에도 동일한 비정상 청산이 재발할 수 있는 live bug이며 가장 먼저 처리해야 한다.

---

### 1-2. 패턴 분석 핵심 판정 (3줄 요약)

1. **기여손익 기준 1위 손실 패턴은 `split-entry + scalp_soft_stop_pct` (14건, -23.3%)** 이며, 이 코호트의 특징은 median held_sec=110.5초 — 진입 후 2분 내 청산이 과반이다. 전역 손절 강화로는 이 패턴을 겨냥할 수 없다.
2. **수익 1위는 `full_fill + scalp_trailing_take_profit` (11건, +13.2%)이며 `split-entry + scalp_trailing_take_profit` (10건, +8.5%)이 바로 뒤를 잇는다.** 전역 손절 강화는 이 수익 코호트를 함께 절단하므로 비권고.
3. **rebase_integrity_flag 19건이 손절 표본에 혼입돼 있어, 이 데이터를 임계값 튜닝 근거로 직접 사용하면 왜곡된 결론이 나온다.** `split_entry_rebase_integrity_shadow`가 이미 코드에 반영됐으므로 표본 축적 후 분리 분석을 선행해야 한다.

---

## 2. 근거

### 2-1. 코호트별 손익 현황 (148건 valid)

| 코호트 | 거래수 | 승률 | 손익 중앙값 | 기여손익 합 | 표본 |
|---|---:|---:|---:|---:|---|
| full_fill | 98 | 38.8% | -0.230% | -20.030% | ✓ 충분 |
| split-entry | 46 | 43.5% | -0.680% | -13.180% | ✓ 충분 |
| partial_fill | 4 | 0.0% | -0.425% | -2.590% | ⚠️ 부족 |

> **partial_fill 코호트는 valid 4건으로 표본 기준(30건) 미달. 이 코호트에 대한 결론 확정 금지.**

### 2-2. 시퀀스 플래그 분포 (sequence_fact, 156 records)

| 플래그 | 건수 | 의미 |
|---|---:|---|
| multi_rebase (split-entry 확인) | 57 | 진입 후 2회 이상 rebase된 포지션 |
| partial_then_expand | 57 | partial fill 이후 추가 확대된 포지션 |
| rebase_integrity 이상 | 19 | cum_filled_qty > requested_qty 또는 requested0_unknown |
| same_ts_multi_rebase | 21 | 동일 초 다중 rebase (수량 점프) |
| same_symbol_repeat_soft_stop | 59 | 동일 종목 당일 반복 soft-stop |

`same_symbol_repeat_flag=59건`은 가장 높은 수치다. 동일 종목 반복 손절이 단발 사건이 아니라 구조적 패턴임을 확인.

### 2-3. 기회비용 구조

| Blocker | 12일 합계 차단 건수 |
|---|---:|
| AI threshold miss (ai_overlap_blocked) | 1,031,746건 |
| overbought gate miss | 379,124건 |
| latency guard miss | 12,298건 |
| liquidity gate miss | 0건 |

AI overlap, overbought 차단이 압도적이다. latency canary 개선(12,298건)은 가장 현실적인 회수 후보이지만, 현재 `canary_applied=19건`으로 bugfix-only 실표본이 50건 미만이므로 아직 canary 승인 조건을 충족하지 못한다.

---

## 3. 다음 액션 — 코드 수정 명세

### [수정 C] protect_trailing_stop stale 보호선 초기화 + 라벨 교정
**긴급도: 🔴 즉시 (2026-04-17 15:40~16:10 KST 실행)**  
**배경**: 2026-04-17 id=2710(11:47), id=2722(12:13) 두 건이 이전 PYRAMID 보호선 `12,607원`이 청산 후에도 잔존해 신규 포지션에 발동됐다. 두 건 모두 `익절 완료`로 오표시됐다.

---

#### C-1. trailing/hard/protect 상태 초기화

**파일**: `src/engine/sniper_execution_receipts.py`

**수정 위치 1 — revive 경로** (약 line 1148~1155):

```python
# 현재 (revive pop 목록)
for key in [
    'odno', 'order_time', 'order_price', 'buy_time',
    'target_buy_price', 'pending_buy_msg',
    'pending_sell_msg', 'sell_odno', 'sell_order_time',
    'sell_target_price', 'pending_entry_orders', 'entry_mode',
    'entry_requested_qty', 'entry_filled_qty', 'entry_fill_amount',
    'entry_bundle_id', 'requested_buy_qty', 'buy_execution_notified'
]:
    target_stock.pop(key, None)

# 수정 후 — 아래 3개 키를 목록에 추가
for key in [
    'odno', 'order_time', 'order_price', 'buy_time',
    'target_buy_price', 'pending_buy_msg',
    'pending_sell_msg', 'sell_odno', 'sell_order_time',
    'sell_target_price', 'pending_entry_orders', 'entry_mode',
    'entry_requested_qty', 'entry_filled_qty', 'entry_fill_amount',
    'entry_bundle_id', 'requested_buy_qty', 'buy_execution_notified',
    'trailing_stop_price', 'hard_stop_price', 'protect_profit_pct',   # ← 추가
]:
    target_stock.pop(key, None)
```

**수정 위치 2 — COMPLETED(일반 매도) 경로** (약 line 1162~1165):

```python
# 현재 (COMPLETED pop 목록)
for key in [
    'pending_entry_orders', 'entry_mode', 'entry_requested_qty',
    'entry_filled_qty', 'entry_fill_amount', 'entry_bundle_id', 'requested_buy_qty',
    'buy_execution_notified'
]:
    target_stock.pop(key, None)

# 수정 후 — 아래 3개 키를 목록에 추가
for key in [
    'pending_entry_orders', 'entry_mode', 'entry_requested_qty',
    'entry_filled_qty', 'entry_fill_amount', 'entry_bundle_id', 'requested_buy_qty',
    'buy_execution_notified',
    'trailing_stop_price', 'hard_stop_price', 'protect_profit_pct',   # ← 추가
]:
    target_stock.pop(key, None)
```

> 이 수정의 효과: 청산 또는 revive 시 이전 포지션의 보호 트레일링/하드스탑/보호수익선이 신규 포지션에 잔존하지 않는다.

---

#### C-2. protect_trailing_stop 음수 손익 라벨 교정

**파일**: `src/engine/sniper_state_handlers.py`

**수정 위치** — 매도 주문 메시지 생성 분기 (line 약 2783):

```python
# 현재
sign = "📉 [손절 주문]" if sell_reason_type == 'LOSS' else "🎊 [익절 주문]"

# 수정 후
# protect_trailing_stop(TRAILING)이라도 profit_rate <= 0이면 손절 라벨 사용
_is_loss_exit = sell_reason_type == 'LOSS' or (
    sell_reason_type == 'TRAILING' and isinstance(profit_rate, (int, float)) and profit_rate <= 0
)
sign = "📉 [손절 주문]" if _is_loss_exit else "🎊 [익절 주문]"
```

> 이 수정의 효과: `protect_trailing_stop`으로 청산됐더라도 실현 손익이 음수이면 Telegram 알림이 "손절 완료"로 표기된다. 기존 receipt replace 로직(`[익절 주문]` → `[익절 완료]`)은 변경 불필요 — 상류에서 라벨이 교정되면 자동 흐름.

**검증**: 수정 후 `pytest -q src/tests/` 전체 통과 확인 및 아주IB투자 유사 케이스 로그 재현 테스트.

---

### [수정 D] same-symbol split-entry soft-stop cooldown shadow
**긴급도: 🟡 오늘(2026-04-17) 16:10~16:20 KST 실행**  
**배경**: sequence_fact 기준 `same_symbol_repeat_flag=59건`. 2026-04-16 지투파워 3회, 2026-04-17 빛과전자/코미팜 2회가 반복 확인됐다.

**파일**: `src/engine/sniper_state_handlers.py`

**구현 위치**: HOLDING 감시 루프 내 `scalp_soft_stop_pct` 발동 직후 또는 별도 진입 판단 경로의 쿨다운 체크 지점.

**구현 명세**:

1. **모듈 단위 추적 딕셔너리 추가** (파일 상단 초기화 위치):
```python
# same-symbol soft-stop cooldown shadow 추적
_same_symbol_soft_stop_timestamps: dict[str, float] = {}
```

2. **soft-stop 발동 시 타임스탬프 기록** (exit_signal stage 직후):
```python
if exit_rule == 'scalp_soft_stop_pct' and entry_mode in ('normal', 'fallback'):
    # split-entry 코호트에만 적용 (rebase 이력이 있는 경우)
    if target_stock.get('_had_rebase'):
        _same_symbol_soft_stop_timestamps[code] = time.time()
```

3. **새 진입 판단 시 shadow 로그 emit** (쿨다운 체크 위치):
```python
cooldown_sec = int(getattr(TRADING_RULES, 'SAME_SYMBOL_SOFT_STOP_COOLDOWN_SEC', 1200))  # 기본 20분
last_soft_stop_ts = _same_symbol_soft_stop_timestamps.get(code, 0)
if last_soft_stop_ts > 0 and (time.time() - last_soft_stop_ts) < cooldown_sec:
    elapsed = int(time.time() - last_soft_stop_ts)
    _log_holding_pipeline(
        name, code, record_id,
        'same_symbol_soft_stop_cooldown_shadow',
        elapsed_sec=elapsed,
        cooldown_sec=cooldown_sec,
        would_block='true',
    )
    # shadow-only: 실제 차단 없음, 로그만 기록
```

**검증 지표**: `same_symbol_soft_stop_cooldown_shadow` 이벤트 누적 건수 / 차단 후 10분 해당 종목 가격 변동 확인.

**TRADING_RULES 추가 필요**:
- `SAME_SYMBOL_SOFT_STOP_COOLDOWN_SEC` = 1200 (기본, 장후 조정 가능)
- `SAME_SYMBOL_SOFT_STOP_COOLDOWN_ENABLED` = False (shadow-only 단계)

---

### [수정 E] partial-only 표류 전용 timeout shadow
**긴급도: 🟡 오늘(2026-04-17) 16:20~16:40 KST 실행**  
**배경**: sequence_fact에서 `partial_fill` 코호트 held_sec 중앙값이 6093초(약 1.7시간). 파미셀, 현대무벡스, 대한광통신, 지투파워가 대표 케이스. 확대형 코호트와 분리된 별도 shadow가 필요하다.

**파일**: `src/engine/sniper_state_handlers.py`

**구현 위치**: HOLDING 감시 루프 내 주기 체크(매 review tick).

**구현 명세**:

```python
# partial-only timeout shadow 조건
_PARTIAL_ONLY_TIMEOUT_SHADOW_SEC = int(
    getattr(TRADING_RULES, 'PARTIAL_ONLY_TIMEOUT_SHADOW_SEC', 180)
)
_PARTIAL_ONLY_PEAK_PROFIT_MAX = float(
    getattr(TRADING_RULES, 'PARTIAL_ONLY_PEAK_PROFIT_MAX_PCT', 0.0)
)

buy_qty = int(target_stock.get('buy_qty') or 0)
requested_qty = int(target_stock.get('entry_requested_qty') or 0)
peak_profit = float(target_stock.get('peak_profit') or 0.0)
held_sec = int(time.time() - float(target_stock.get('hold_start_ts') or time.time()))

is_partial_only = (
    buy_qty <= 1
    and requested_qty > 1
    and not target_stock.get('_had_rebase')
)

if (
    is_partial_only
    and held_sec >= _PARTIAL_ONLY_TIMEOUT_SHADOW_SEC
    and peak_profit <= _PARTIAL_ONLY_PEAK_PROFIT_MAX
    and not target_stock.get('_partial_only_timeout_shadow_logged')
):
    target_stock['_partial_only_timeout_shadow_logged'] = True
    _log_holding_pipeline(
        name, code, record_id,
        'partial_only_timeout_shadow',
        held_sec=held_sec,
        buy_qty=buy_qty,
        requested_qty=requested_qty,
        peak_profit=peak_profit,
        threshold_sec=_PARTIAL_ONLY_TIMEOUT_SHADOW_SEC,
    )
```

**TRADING_RULES 추가 필요**:
- `PARTIAL_ONLY_TIMEOUT_SHADOW_SEC` = 180 (기본 3분)
- `PARTIAL_ONLY_PEAK_PROFIT_MAX_PCT` = 0.0
- `PARTIAL_ONLY_TIMEOUT_SHADOW_ENABLED` = True

**검증 지표**: `partial_only_timeout_shadow` 이벤트의 `held_sec` 분포 / 이후 실현 손익과 비교.

---

## 4. 수정 순서 및 검증 체크리스트

```
[1차 즉시 실행 — 2026-04-17 15:40~16:10 KST]
  □ 수정 C-1: sniper_execution_receipts.py revive/COMPLETED pop 목록에 3개 키 추가
  □ 수정 C-2: sniper_state_handlers.py sell_reason_type TRAILING + profit_rate <= 0 라벨 분기
  □ pytest -q src/tests/ 전체 통과 확인
  □ py_compile src/engine/sniper_execution_receipts.py src/engine/sniper_state_handlers.py 통과
  □ 원격(songstockscan) 동일 파일 반영 + bot_main.py 재기동

[2차 즉시 실행 — 2026-04-17 16:10~16:20 KST]
  □ 수정 D: same-symbol cooldown shadow 구현
  □ TRADING_RULES에 SAME_SYMBOL_SOFT_STOP_COOLDOWN_SEC / _ENABLED 추가
  □ pytest -q src/tests/ 전체 통과 확인

[3차 즉시 실행 — 2026-04-17 16:20~16:40 KST]
  □ 수정 E: partial-only timeout shadow 구현
  □ TRADING_RULES에 PARTIAL_ONLY_TIMEOUT_SHADOW_SEC / _PCT / _ENABLED 추가
  □ pytest -q src/tests/ 전체 통과 확인

[재실행 백업 슬롯 — 2026-04-17 21:00~22:00 KST]
  □ 1~3차 미완료 항목 전량 재실행
```

---

## 5. 비코드 수정 항목 (shadow 데이터 수집 중, 판단 유보)

| 항목 | 현재 상태 | 다음 판단 시점 |
|---|---|---|
| latency canary tag 완화 1축 승인 | shadow 수집 중 (`canary_applied=19건`, 목표 50건 미만) | 2026-04-20 08:00 KST — 실표본 누적 후 재판정 |
| split-entry rebase quantity 임계값 튜닝 | `rebase_integrity_shadow` 수집 중 (19건) | 2026-04-20 08:10 KST — 누적건수 점검 후 분리 분석 판정 |
| partial_then_expand 즉시 재평가 실전화 | `immediate_recheck_shadow` 수집 중 (57건) | 2026-04-20 08:20 KST — 90초 이내 soft-stop 감소 여부 기준 canary 판정 |

---

## 6. 금지 사항 재확인

- `full_fill / partial_fill / split-entry` 혼합 해석 및 혼합 임계값 적용 **금지**
- `rebase_integrity_flag` 케이스가 섞인 데이터를 손절 임계값 튜닝 근거로 직접 사용 **금지**
- 전역 `scalp_soft_stop_pct` 강화 같은 단일축 일반화 결론 **금지**
- 운영 코드 검증(pytest) 없이 원격 반영 **금지**

---

## 7. 참고 산출물

| 파일 | 설명 |
|---|---|
| `analysis/claude_scalping_pattern_lab/outputs/final_review_report_for_lead_ai.md` | 자동 생성 분석 보고서 |
| `analysis/claude_scalping_pattern_lab/outputs/ev_improvement_backlog_for_ops.md` | EV 개선 후보 백로그 상세 |
| `analysis/claude_scalping_pattern_lab/outputs/data_quality_report.md` | 표본 품질 및 플래그 분포 |
| `analysis/claude_scalping_pattern_lab/outputs/claude_payload_summary.json` | 코호트 통계 JSON |
| `analysis/claude_scalping_pattern_lab/outputs/claude_payload_cases.json` | 대표 케이스 JSON |
| `docs/2026-04-17-ajouib-protect-trailing-mislabel-audit.md` | 아주IB투자 stale protection 감사 원본 |
| `docs/2026-04-17-softstop-after-partial-fill-analysis.md` | soft-stop 분석 원본 |

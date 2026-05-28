# 대한전선(001440) 진입가 감리 후속 — Dynamic 진입가 산정 최적방안 포함 (`2026-04-29`)

> 작성시각: `2026-04-29 KST`
> 검토 대상: `대한전선(001440)` `record_id=4219`, 주문번호 `0049602`
> 후속 검토 목적: 1차 감리(`2026-04-29-daehan-cable-entry-price-audit-review.md`)의 결론을 받아, 재발 방지를 위한 **dynamic 진입가 산정 최적방안**을 설계 단위까지 확정한다.
> 검증 범위: 1차 감리 증적 + `signal_radar.py`, `sniper_entry_latency.py`, `sniper_state_handlers.py` 코드 경로 재독, 가격 결정 권한 모델 재설계
> 보완 메모: 아래 P1/P2 설계안은 유지하되, `2026-04-29` 실제 구현은 P0 hotfix와 코드리뷰 안정화 범위로 제한됐다.

---

## 0. TL;DR

- 1차 감리 결론(`radar target cap 과도`)은 **현상 진단으로는 정확**하지만, 단일 패치로 닫히지 않는다.
- 본질은 **세 가격 컴포넌트 간 권한 모호성**(`smart_target` vs `defensive_price` vs `target_cap clamp`)이다.
- 따라서 후속 조치는 **버그픽스 2건 + 로직 재설계 3건**으로 분리한다.
- Dynamic 진입가는 `Reference → Defensive → Final` 3단 파이프라인으로 재구성하며, 마지막 단에 **strategy-aware resolver**와 **microstructure-adaptive band**를 둔다.

### 0-1. 현재 상태 요약

- P0 구현 완료: `pre-submit sanity guard`, `pipeline_events` 가격 스냅샷 분리, 관련 테스트 통과
- P1 구현 완료 (`2026-05-01`): `strategy-aware resolver`, `SCALPING timeout table`
  - `SCALPING_ENTRY_PRICE_RESOLVER_ENABLED=True`
  - `SCALPING_ENTRY_PRICE_RESOLVER_MAX_BELOW_BID_BPS=80`
  - 일반 스캘핑 `90초`, `BREAKOUT 120초`, `PULLBACK 600초`, `RESERVE 1200초`
  - `target_buy_price`는 제출가의 절대 권한이 아니라 `reference_target_price`로 기록하며, best bid 대비 허용 하향 괴리를 넘으면 `scalping_reference_rejected_defensive`로 방어가 제출을 유지한다.
- P2 구현 완료 (`2026-05-01`): 운영 규칙상 entry price shadow는 열지 않고, `AI Tier2 entry_price canary`를 submitted 직전 live 경로에 적용한다.
  - canary 입력: reference target, defensive price, best bid/ask, spread/latency, 체결강도/매수비율, 호가 depth, 최근 tick/candle 요약
  - canary 출력: `USE_DEFENSIVE | USE_REFERENCE | IMPROVE_LIMIT | SKIP`, `order_price`, `confidence`, `reason`, `max_wait_sec`
  - fail-closed: AI timeout/parse fail/context fetch fail/low confidence/price guard 위반은 P1 resolver 가격을 유지한다.
- 코드리뷰 후속 분리: `sniper_state_handlers.py` 구조 debt는 `2026-05-06 checklist`로 이관
- `80bps`는 확정 정책값이 아니라 provisional threshold로 유지하고, 분포 부록과 rolling KPI로 재앵커한다

---

## 1. 1차 감리 결과 재확인

### 1-1. 사실 관계 (변동 없음)

- `latency=SAFE`, `unstable_quote_observed=False`
- `best_bid=50500`, `best_ask=50900`
- `normal_defensive_order_price=50400`
- 실제 `order_price=48800`
- `BUY_ORDERED` 상태 `20분 이상` 유지, 미체결 종료

근거: [pipeline_events_2026-04-29.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-04-29.jsonl:172794~172802)

### 1-2. 1차 판정의 한계

1차 감리는 `radar target cap 과도`를 주원인으로 지목했으나, 다음 두 가지가 누락되어 있다.

1. `pre-submit sanity guard` 부재 — **시장가 대비 −3.4% 깊이로 주문이 무차단 통과**한 것은 진단상 "가격 산정 부적정"이 아니라 **안전장치 결함**이다.
2. `trade_review.buy_price = curr_price` 기록 — 이는 단순 표기 문제가 아니라 **사후감리/PnL attribution 전반을 왜곡하는 데이터 버그**다.

→ 본 후속 보고서는 위 두 항목을 **별도 트랙(P0 버그픽스)** 으로 분리하고, 가격 산정 자체는 **Dynamic 가격 결정 아키텍처 재설계(P1)** 로 다룬다.

---

## 2. 이슈 재분류

| # | 항목 | 분류 | 트랙 |
|---|------|------|------|
| A | `trade_review.buy_price` 의미 모호 (curr_price 기록) | **버그 (데이터)** | P0 |
| B | `order_price` vs `best_bid` 괴리 sanity guard 부재 | **안전장치 부재** | P0 |
| C | `target_buy_price`가 `defensive_price`를 무조건 clamp | **로직 설계 부정합** | P1 (핵심) |
| D | round-figure 회피 `48800` 고정 | **로직 부정합 (컨텍스트 누락)** | P1 (C로 자동 무력화) |
| E | `target_buy_price>0 ⇒ 1200s` reserve timeout 일괄 적용 | **로직 부정합 (분기 키 오용)** | P1 |
| F | 미체결 주문 reprice/cancel 루프 부재 | **기능 미비** | P2 |

---

## 3. 근본 원인 — 권한 모호성(Authority Ambiguity)

세 컴포넌트가 서로 다른 의도로 가격을 만들고 있다.

| 컴포넌트 | 의도 | 본래 의미 |
|----------|------|-----------|
| `signal_radar.get_smart_target_price()` | "내가 받고 싶은 이상적 진입가" | **referential** (목표가) |
| `sniper_entry_latency.normal_defensive_order_price` | "지금 시장에서 안전하게 체결될 가격" | **executional** (실행가) |
| `sniper_entry_latency.py:823` 부근 `min(order_price, target_cap)` | 위 둘의 결합 정책 | **policy** (정책) |

문제는 결합이 단순 `min()`이라는 것이다. 그 결과 referential 컴포넌트가 **암묵적으로 최고 권한**을 가져간다. radar의 `48800` round-figure 휴리스틱은 "내가 진짜 받고 싶은 가격"을 만드는 규칙이지, **"지금 당장 시장에서 체결시킬 가격"의 규칙이 아니다**. 이 의미 차이가 실주문 단계까지 흘러가면서 본 사고가 발생했다.

> **이 권한 모호성을 해소하지 않으면, D(round-figure)를 패치해도 다음에는 다른 형태로 재발한다.**

---

## 4. Dynamic 진입가 산정 최적방안

### 4-1. 설계 원칙

1. **권한 분리(Separation of Authority)** — referential/executional/policy 세 권한을 코드와 데이터에서 명시 분리한다.
2. **전략 인지(Strategy-Aware)** — `SCALPING`, `BREAKOUT`, `PULLBACK`은 가격 결정 우선순위가 다르다. 같은 함수가 분기로 처리해서는 안 된다.
3. **시장 미시구조 반응(Microstructure-Adaptive)** — `spread`, `quote_age`, `depth imbalance`, `latency`에 따라 defensive band 폭이 동적으로 변해야 한다.
4. **Fail-loud, fail-safe** — sanity guard 위반은 silent clamp가 아니라 **abort + 로그**가 기본이다.
5. **Observability-first** — 모든 단계의 입력/출력을 `pipeline_events`에 별도 키로 남긴다.

### 4-2. 3-Layer 가격 결정 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 1: REFERENCE (referential, signal_radar)                  │
│   - smart_target_price                                          │
│   - 의미: "이상적 진입가". 라운드피겨 회피, AI 점수 반영 가능 │
│   - 권한: NONE (실주문가에 직접 영향 X)                         │
│   - 출력 키: reference_target_price                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Layer 2: DEFENSIVE (executional, sniper_entry_latency)          │
│   - microstructure-adaptive defensive band                      │
│   - 의미: "지금 시장에서 체결될 안전 가격대"                  │
│   - 권한: 실주문가의 1차 후보                                  │
│   - 출력 키: defensive_order_price, defensive_band_ticks       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Layer 3: RESOLVER (policy, strategy-aware)                      │
│   - reference + defensive를 전략에 따라 결합                   │
│   - sanity guard, abort 결정 포함                               │
│   - 권한: 최종 주문가 확정                                     │
│   - 출력 키: resolved_order_price, resolution_reason            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                       Pre-submit guard
                              │
                              ▼
                          place_order
```

### 4-3. Strategy-aware Resolver (Layer 3 핵심)

전략별 결합 정책은 다음과 같이 명시 분리한다.

| 전략 | reference의 역할 | defensive의 역할 | 최종가 |
|------|-----------------|-----------------|--------|
| `SCALPING` | abort 임계 | **authoritative** | `defensive_price` |
| `BREAKOUT` | abort 임계 | **authoritative** | `defensive_price` (단, 돌파가 위로 추가 offset 가능) |
| `PULLBACK` | **authoritative** (목표가) | 슬립 한도 | `min(defensive_price, reference_target)` |
| `RESERVE` (지정가 예약) | **authoritative** | N/A | `reference_target` |

의사 코드:

```python
def resolve_order_price(
    strategy: str,
    defensive_price: int,
    reference_target: int,
    market: MarketSnapshot,
    cfg: ResolverConfig,
) -> ResolveResult:
    # 0) 사전 검증
    if defensive_price <= 0 or market.best_bid <= 0:
        return ResolveResult(abort=True, reason="invalid_inputs")

    # 1) 전략별 권한 분기
    if strategy in ("SCALPING", "BREAKOUT"):
        # reference는 abort 신호로만 사용
        if reference_target > 0 and \
           defensive_price > reference_target * (1 + cfg.abort_premium):
            return ResolveResult(abort=True, reason="defensive_above_reference_band")
        chosen = defensive_price
        reason = "executional_authority"

    elif strategy == "PULLBACK":
        # reference가 우위. 단, defensive보다 너무 낮으면 reference도 clamp
        if reference_target <= 0:
            chosen = defensive_price
            reason = "pullback_no_reference_fallback"
        else:
            min_floor = move_price_by_ticks(defensive_price, -cfg.pullback_max_drop_ticks)
            chosen = max(min_floor, min(defensive_price, reference_target))
            reason = "pullback_referential_authority"

    elif strategy == "RESERVE":
        chosen = reference_target if reference_target > 0 else defensive_price
        reason = "reserve_referential_authority"

    else:
        chosen = defensive_price
        reason = "default_executional"

    # 2) 라운드피겨 회피는 PULLBACK/RESERVE에서만 적용
    if strategy in ("PULLBACK", "RESERVE"):
        chosen = apply_round_figure_avoidance(chosen, market)

    return ResolveResult(price=chosen, reason=reason, abort=False)
```

핵심:
- `SCALPING`/`BREAKOUT`은 `defensive_price`가 **확정**, reference는 abort gate로만 사용
- `48800` 고정 같은 round-figure 휴리스틱은 **referential authority가 있는 전략에서만** 적용 → D 이슈 자동 해소
- abort는 silent하지 않고 명시 사유와 함께 로그

### 4-4. Microstructure-adaptive Defensive Band (Layer 2 강화)

현재는 `move_price_by_ticks(latest_price, -1tick)`처럼 **고정 1틱**으로 defensive price를 만든다. 이는 다음 한계가 있다.

- 스프레드가 넓을 때(`best_ask - best_bid >> 1tick`) 너무 공격적
- 스프레드가 타이트할 때 너무 보수적
- `quote_age`가 클 때(stale book) 동일하게 처리

제안하는 dynamic band:

```python
def compute_defensive_band_ticks(market: MarketSnapshot, latency: str) -> int:
    spread_ticks = (market.best_ask - market.best_bid) / market.tick_size

    # 1) 베이스: 스프레드 절반 ± 1틱
    base = max(1, int(round(spread_ticks / 2)))

    # 2) 호가 신선도 조정
    if market.quote_age_p90_ms > 300:
        base += 1
    if market.quote_age_p90_ms > 800:
        base += 1

    # 3) 잔량 불균형 조정 (매수잔량이 두꺼우면 band 좁힘)
    if market.bid_depth_ratio >= 1.5:
        base = max(1, base - 1)
    elif market.bid_depth_ratio <= 0.5:
        base += 1

    # 4) latency 상태 반영
    if latency == "DEGRADED":
        base += 1
    elif latency == "CRITICAL":
        base += 2

    # 5) cap
    return min(base, MAX_DEFENSIVE_BAND_TICKS)


def compute_defensive_price(market: MarketSnapshot, band_ticks: int) -> int:
    # 매수 진입 기준: best_ask 우선 → 안 되면 best_bid + band
    # 즉, 체결 가능성을 1차 우선
    anchor = market.best_ask
    return move_price_by_ticks(anchor, -band_ticks + 1)
```

→ 본 케이스에 대입 시: `spread = (50900-50500)/100 = 4 tick`, `base = 2`, `quote_age=197ms`로 추가 가산 없음 → `defensive = best_ask - 1 tick = 50800` 또는 `50500~50800` 범위. **`48800` 같은 값이 나올 여지가 원천적으로 없다.**

### 4-5. Pre-submit Sanity Guard (이슈 B 해결)

resolver 출력 직후, 실주문 직전에 **마지막 brake**:

```python
def pre_submit_guard(order_price: int, market: MarketSnapshot, cfg: GuardConfig) -> GuardResult:
    # 1) 시장가 대비 괴리
    if market.best_bid > 0:
        deviation_bps = (market.best_bid - order_price) / market.best_bid * 10000
        if deviation_bps > cfg.max_below_bid_bps:        # 예: 80 bps
            return GuardResult(block=True, reason="too_far_below_bid", deviation_bps=deviation_bps)
        if -deviation_bps > cfg.max_above_ask_bps:       # 매수인데 ask 위로 너무 추격
            return GuardResult(block=True, reason="too_far_above_ask", deviation_bps=deviation_bps)

    # 2) tick 정합성
    if order_price % market.tick_size != 0:
        return GuardResult(block=True, reason="tick_misaligned")

    # 3) 호가 안정성 (이미 ENTRY_PIPELINE에서 본 값 재확인)
    if market.unstable_quote_observed:
        return GuardResult(block=True, reason="unstable_quote_at_submit")

    return GuardResult(block=False)
```

권장 임계:
- `max_below_bid_bps = 80` (= 0.8%, 본 케이스 `(50500-48800)/50500 ≈ 337bps`로 명백한 차단 대상)
- `max_above_ask_bps = 50`

### 4-6. Strategy-aware Timeout (이슈 E 해결)

분기 키를 `target_buy_price > 0`이 아니라 **전략 타입**으로 변경한다.

```python
TIMEOUT_TABLE = {
    "SCALPING":  90,    # 1.5분
    "BREAKOUT":  120,   # 2분
    "PULLBACK":  600,   # 10분
    "RESERVE":   1200,  # 20분 (기존)
}

def resolve_buy_timeout(strategy: str, has_target: bool) -> int:
    return TIMEOUT_TABLE.get(strategy, 300)
```

추가로, **타임아웃 도래 전이라도** `pre_submit_guard`의 `max_below_bid_bps`가 일정 시간 이상 위반되면 `early_cancel`을 트리거한다 (4-7 reprice 루프와 연결).

### 4-7. Reprice / Early Cancel 루프 (이슈 F)

미체결 주문은 **자본·슬롯·attention**을 점유한다. 다음 루프를 도입한다.

```
매 N초 (예: 15초)마다:
  if 주문상태 in {"접수", "부분체결"}:
      현재 best_bid, best_ask 갱신
      deviation = (best_bid - order_price) / best_bid * 10000

      if deviation > REPRICE_THRESHOLD_BPS (예: 60):
          if 누적_reprice_횟수 < MAX_REPRICE (예: 2):
              cancel + 재제출 at new defensive_price
              누적_reprice_횟수 += 1
          else:
              cancel + abort_entry (한도 초과)
```

이는 단순 timeout보다 **시장 변화에 반응적**이며, 1200초 동안 가만히 두는 현재 방식의 기대값 누수를 막는다.

---

## 5. 데이터/관측성 개선 (이슈 A 해결)

### 5-1. Snapshot 필드 분리

`trade_review`/`monitor_snapshots`의 `buy_price` 단일 필드를 다음으로 분해.

| 신규 필드 | 의미 | 소스 |
|----------|------|------|
| `submitted_order_price` | 실제 제출 주문가 | `order_bundle_submitted.order_price` |
| `mark_price_at_submit` | 제출 직전 현재가 | 기존 `buy_price`의 의미 |
| `best_bid_at_submit` | 제출 직전 best bid | `orderbook_stability_observed.best_bid` |
| `best_ask_at_submit` | 제출 직전 best ask | `orderbook_stability_observed.best_ask` |
| `defensive_price_at_submit` | resolver 입력 defensive | Layer 2 출력 |
| `reference_target_at_submit` | resolver 입력 reference | Layer 1 출력 |
| `resolution_reason` | resolver가 선택한 사유 | Layer 3 결과 |

현재 구현은 위 전체를 DB schema로 바로 분해하지 않고, 먼저 `pipeline_events`에 동일 의미 필드를 기록하는 방식으로 반영했다.
기존 `buy_price`는 downstream 손익/보유 경로 영향 때문에 이번 턴에서는 그대로 두고, 감리 해석상 `mark_price_at_submit` 성격의 legacy field로 취급한다.

### 5-2. Pipeline event 키 보강

`ENTRY_PIPELINE`에 다음 이벤트 키를 추가.

- `defensive_band_computed` — band ticks와 입력 microstructure 변수
- `price_resolved` — Layer 3 결정 (price, reason, abort 여부)
- `pre_submit_guard_evaluated` — guard 통과/차단 + 사유
- `reprice_triggered` — reprice 발동 시점 + before/after

이 키가 있어야 사후 감리에서 **"어느 레이어에서 어떤 결정이 일어났는지"** 가 단일 view로 재구성된다.

다만 `2026-04-29` 실제 hotfix는 신규 stage를 최소화해 다음 범위까지만 반영했다.

- 기존 `latency_pass`, `order_leg_request`, `order_bundle_submitted`에 가격 스냅샷 필드 추가
- 신규 차단 이벤트 `pre_submit_price_guard_block` 추가
- `defensive_band_computed`, `price_resolved`, `pre_submit_guard_evaluated`, `reprice_triggered`는 P1/P2 설계 시점에 다시 검토

추가 보완:

- 비-`SCALPING` 전략에는 차단 없는 `observe-only` 이벤트를 남기는 방안을 P1 설계 입력으로 채택한다.
- `BUY_ORDERED.buy_price`는 이번 hotfix에서 그대로 두되, `resolver` 도입 시점에 `submitted_order_price` canonical 승격 조건을 같이 잠근다.

---

## 6. 구현 우선순위

### P0 — 이번 주 (버그/안전장치)

1. **Pre-submit sanity guard** (4-5) — 완료
2. **Snapshot 필드 분리** (5-1) — `pipeline_events` 기준 완료, DB schema 분리는 보류
3. **P0 guard KPI / rollback SLO** — 추가 필요
4. **80bps 분포 부록** — 추가 필요

### P0 추가 잠금

- `80bps`는 현재 복원 가능한 `2026-04-28~2026-04-29` stage-paired submitted cohort `8건` 기준 provisional threshold로 유지한다.
- 일일 KPI는 `pre_submit_price_guard_block_rate`, `(best_bid - submitted_price)/best_bid` rolling `p99`, `deep bid 무차단 통과 재발 여부`로 고정한다.
- 롤백/재조정 기준은 `차단율 > 0.5% review`, `> 2.0% rollback 또는 threshold 완화 검토`, `= 0% 비활성/로깅 누락 점검`으로 잠근다.

### P1 — 다음 스프린트 (구조 재설계)

3. **3-Layer 아키텍처 분해** (4-2) — 함수 시그니처/명칭 변경 포함
4. **Strategy-aware Resolver** (4-3) — `resolve_order_price()` 도입
5. **Strategy-aware Timeout** (4-6) — `TIMEOUT_TABLE` 도입
6. **Pipeline event 키 보강** (5-2) — 관측성 확보 (P1 작업의 검증 도구이기도 함)

### P2 — 후속 스프린트 (고도화)

7. **Microstructure-adaptive Defensive Band** (4-4) — 스프레드/잔량/latency 반응형
8. **Reprice / Early cancel 루프** (4-7)
9. **Round-figure 회피 컨텍스트 게이팅** — P1의 (4) 적용 후에도 PULLBACK/RESERVE 내부에서 더 정교하게

---

## 7. 영향 범위 / 회귀 리스크

### 7-1. 영향받는 코드

- [signal_radar.py](/home/ubuntu/KORStockScan/src/engine/signal_radar.py:200~265) — `get_smart_target_price` 반환 의미 변경 (referential only)
- [sniper_entry_latency.py](/home/ubuntu/KORStockScan/src/engine/sniper_entry_latency.py:823) 부근 — `min(order_price, target_cap)` 제거, `resolve_order_price` 호출로 교체
- [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:2435) — `final_target_buy_price` 사용처를 reference 의미로 정리
- [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:3198) — `BUY_ORDERED` 장부에 `submitted_order_price` 분리 기록
- [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:4999) — timeout 분기 `target_buy_price>0` → `strategy` 기반

### 7-2. 회귀 리스크

| 리스크 | 영향 | 완화 |
|--------|------|------|
| `PULLBACK`이 기존 동작과 달라짐 | 중 | 기존 `min()`과 동치인 경로(`pullback_referential_authority`)를 명시적으로 보존 |
| `SCALPING`의 평균 진입가가 상승 → 기대 PnL 변화 | 중-상 | `observe-only counterfactual log`로 비교. `Plan Rebase` 기준 신규/보완축 shadow는 금지이므로 실주문과 별도 계산 결과를 같은 이벤트에 남기는 방식으로 대체 |
| `48800` 라운드피겨 효과가 SCALPING에서 사라짐 | 저 | radar reference에는 유지, resolver에서 차단 |
| Reprice 루프가 거래소 호가취소 빈도 증가 | 저-중 | `MAX_REPRICE=2`로 제한, 일/계좌 단위 cap 별도 |

### 7-3. 검증 계획

1. **백테스트** — 최근 30일 SCALPING 진입 케이스에 대해, 신규 resolver의 결정과 실제 결정 비교 → 가격 차이 분포, 기대 체결률 변화 추정
2. **Observe-only 1주** — production에서 신규 결정을 counterfactual 필드로 로깅, 실주문은 기존 경로
3. **Canary** — 특정 종목/시간대만 신규 경로로, 5영업일 모니터링
4. **전면 적용 후 KPI** — `submitted_but_unfilled rate`, `entry slippage bps`, `time_to_fill p50/p90`

---

## 8. 본 케이스(`record_id=4219`) 재시뮬레이션

신규 아키텍처 적용 시 추정 동작:

| 단계 | 기존 | 신규 |
|------|------|------|
| Layer 1 (Reference) | `48800` (round-figure 회피) | `48800` (동일, 의미만 referential) |
| Layer 2 (Defensive) | `50400` (1tick 고정) | `50800` (spread-adaptive, ask−1tick) |
| Layer 3 (Resolver, strategy=SCALPING) | `min(50400, 48800)=48800` | `defensive=50800`, `48800*(1+abort_premium=0.005)=49044` < `50800` → **abort** |
| Pre-submit guard | (없음) | (resolver에서 abort된 경우 도달하지 않음) |
| 결과 | `48800` 제출, 미체결 20분+ | 진입 자체 abort, 슬롯 즉시 해제 |

또는 abort_premium을 `0.04` 수준으로 완화한다면:
- `48800 * 1.04 = 50752` < `50800` → 여전히 abort
- abort_premium을 `0.05`로 두면 `51240` > `50800` → `defensive=50800` 제출, 즉시 체결 가능성 매우 높음

→ **abort_premium은 전략 기대 PnL과 직접 결부되므로 백테스트로 결정할 파라미터**다.

---

## 9. 의사결정 요청 사항

1. `abort_premium` 초기값 정책 — 보수(`0.005`, abort 우선) vs 적극(`0.05`, 체결 우선)?
2. `MAX_REPRICE`를 0(기존 정책 유지)으로 둘지, 1~2로 할지?
3. Round-figure 회피 규칙을 PULLBACK에만 둘지, RESERVE까지 확대할지?
4. P0 두 항목(guard, snapshot 분리)을 hotfix로 즉시 배포할지, P1과 함께 묶을지?

현재 상태 기준으로는 4번 항목 중 `P0 두 항목 즉시 배포`는 이미 닫혔다. 남은 운영 판단은 P1/P2 범위에 한정된다.

### 9-1. 의사결정 등록부

| # | 결정사항 | 처리 | 근거/조건 |
| --- | --- | --- | --- |
| 1 | `abort_premium` 초기값 | `P1로 연기` | backtest 분포 + observe-only divergence log로 결정 |
| 2 | `MAX_REPRICE` | `P2로 연기` | 덕산하이메탈 표본 후 결정 |
| 3 | round-figure 적용 범위 | `P1로 연기` | resolver와 동시 설계 |
| 4 | P0 hotfix 분리배포 | `결정 완료` | change hygiene와 원인귀속 분리를 위해 즉시 분리배포 |

### 9-2. P1 ingress gate

| 단계 | 조건 | 산출물 |
| --- | --- | --- |
| Backtest | 최근 `30~60` 영업일 `SCALPING/BREAKOUT` 진입 | 가격차 분포, 추정 체결률 변화 |
| Observe-only | production `1주` counterfactual log | resolver divergence rate, `record_id=4219` abort 여부 |
| Canary | 특정 종목군 `5영업일` | `submitted_but_unfilled_rate`, `slippage_bps`, `time_to_fill_p50/p90` |

`record_id=4219`는 P1 ingress의 anchor case로 유지한다.

---

## 10. 관련 문서 / 체크리스트

- 1차 감리: `2026-04-29-daehan-cable-entry-price-audit-review.md`
- 재보고/구현 현황: `2026-04-29-daehan-cable-entry-price-audit-rereport.md`
- [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-29-stage2-todo-checklist.md)
  - `[EntryPriceDaehanCable0429-Postclose] 대한전선(001440) submitted-but-unfilled 진입가 cap/timeout 적정성 판정`
  - `[DynamicEntryPriceP0Guard0430-Preopen] pre-submit price guard + price snapshot split 구현/검증`
  - `[DynamicEntryPriceP0Guard0430-Postclose] P0 guard KPI/rollback 1차 점검`
- [2026-05-06-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-05-06-stage2-todo-checklist.md)
  - `[LatencyEntryPriceGuardV2] bps/가격대별 defensive table 설계`
  - `[PreSubmitGuardDist0506HolidayCarry]`
  - `[PreSubmitGuardObserve0506HolidayCarry]`
  - `[BuyPriceSchemaSplitP1]`
  - `[DynamicEntryResolverIngress0506HolidayCarry]`
- [2026-05-06-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-05-06-stage2-todo-checklist.md)
  - `[StateHandlersContext0506]`
  - `[StateHandlersSplit0506]`
  - `[SwingTrailingPolicy0506]`

---

## 11. 참고 근거

- [pipeline_events_2026-04-29.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-04-29.jsonl:172794)
- [pipeline_events_2026-04-29.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-04-29.jsonl:172796)
- [pipeline_events_2026-04-29.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-04-29.jsonl:172798)
- [pipeline_events_2026-04-29.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-04-29.jsonl:172802)
- [sniper_execution_receipts_info.log](/home/ubuntu/KORStockScan/logs/sniper_execution_receipts_info.log:2529~2530)
- [trade_review_2026-04-29.json](/home/ubuntu/KORStockScan/data/report/monitor_snapshots/trade_review_2026-04-29.json:60708)
- [signal_radar.py](/home/ubuntu/KORStockScan/src/engine/signal_radar.py:200)
- [sniper_entry_latency.py](/home/ubuntu/KORStockScan/src/engine/sniper_entry_latency.py:823)
- [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:2435)
- [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:3198)
- [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:4999)

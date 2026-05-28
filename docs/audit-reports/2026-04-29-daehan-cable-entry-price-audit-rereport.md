# 대한전선(001440) 진입가 감리 재보고 (`2026-04-29`)

> 목적: 감리 후속 보고서의 dynamic 진입가 제안을 현재 코드베이스와 `Plan Rebase` 기준으로 대조해, 즉시 수용 범위와 별도 승인 범위를 분리한다.
> 보완 범위: `2026-04-29` P0 구현 반영 결과와 `sniper_state_handlers.py` 코드리뷰 후속까지 포함한다.

## 1. 판정

`대한전선(001440)` submitted-but-unfilled의 직접 원인은 유동성 부족이 아니라 `reference target cap`이 방어 진입가보다 우선한 가격결정 권한 충돌이다.

- P0 즉시 수용: `pre-submit sanity guard`와 `pipeline_events` 가격 스냅샷 분리.
- P1 별도 승인: `strategy-aware resolver`와 `SCALPING timeout table`.
- P2 보류: `microstructure-adaptive band`, `reprice/early cancel loop`.

현재 `Plan Rebase` 기준상 entry live canary는 비어 있고, `ShadowDiff0428`가 닫히기 전에는 신규 entry 축 hard pass/fail이 불가하다. 따라서 이번 조치는 신규 alpha canary가 아니라 비정상 제출가를 막는 안전가드와 감리 추적성 보강으로 제한한다.

## 2. 근거

| 항목 | 확인 내용 | 판정 |
| --- | --- | --- |
| reference target | `signal_radar.get_smart_target_price()`가 라운드피겨 회피로 `48800`을 산출할 수 있음 | 이상적 진입가 성격인데 최종 주문가 권한을 가짐 |
| defensive price | `sniper_entry_latency.evaluate_live_buy_entry()`가 `normal_defensive_order_price=50400`을 산출 | 체결 가능성 기준의 방어 주문가 |
| final clamp | `target_buy_price > 0`이면 `order_price = min(defensive_order_price, target_buy_price)` | `48800`이 최종 주문가로 내려감 |
| 호가 괴리 | `best_bid=50500`, `order_price=48800`이면 `337bps` 하향 괴리 | 체결 가능성이 구조적으로 낮음 |
| DB snapshot | `BUY_ORDERED` 업데이트는 `buy_price=curr_price`로 저장 | 제출가와 mark price 의미가 혼재됨 |
| timeout | `target_buy_price > 0`이면 `RESERVE_TIMEOUT_SEC=1200` 경로 | SCALPING 대기시간으로 과장될 수 있음 |

기존 코드에는 `latency_pass`, `order_leg_request`, `order_bundle_submitted` 이벤트가 있으나, `submitted_order_price`, `mark_price_at_submit`, `best_bid_at_submit`, `best_ask_at_submit`, `defensive_order_price`, `reference_target_price`, `resolved_order_price`, `resolution_reason`, `price_below_bid_bps`가 분리돼 있지 않아 감리 재현성이 부족했다.

## 3. 수용 범위

### P0: 즉시 반영

- `SCALPING_PRE_SUBMIT_PRICE_GUARD_ENABLED=True`를 기본값으로 둔다.
- `SCALPING_PRE_SUBMIT_MAX_BELOW_BID_BPS=80`을 기본 threshold로 둔다.
- `send_buy_order` 직전 제출가가 최우선 매수호가보다 `80bps` 초과 낮으면 주문 전송을 차단하고 `pre_submit_price_guard_block` 이벤트를 남긴다.
- DB `buy_price` 의미는 이번 패치에서 변경하지 않는다. 손익/보유 로직 의존 범위가 넓으므로 schema 변경 없이 `pipeline_events` 관측 필드로 먼저 분리한다.

단, `80bps`는 현재 **영구 정책값이 아니라 P0 안전가드의 초기값**으로 둔다. 본 케이스 `337~412bps` 수준의 명백한 outlier를 우선 차단하기 위한 값이며, 분포 부록과 rolling KPI가 붙기 전까지는 임시 threshold로 해석한다.

### P1: 별도 승인 축

- `SCALPING/BREAKOUT`은 defensive price 권한을 우선하고, reference target은 abort 또는 감리 참고값으로 낮춘다.
- `PULLBACK/RESERVE`는 reference target 권한을 유지하되 defensive price를 slip limit로 사용한다.
- `target_buy_price > 0 => 1200초` 분기는 전략 기준 timeout table로 분리한다.
- 이 변경은 체결률과 평균 진입가를 직접 바꾸므로 P0 안전가드와 같은 배포 단위에 섞지 않는다.

### P2: 보류

- microstructure-adaptive band는 2026-05-06 `LatencyEntryPriceGuardV2_0506HolidayCarry`의 bps/가격대별 defensive table 설계 입력으로 넘긴다. `2026-05-05`는 어린이날 KRX 휴장으로 실행일에서 제외한다.
- reprice/early cancel loop는 덕산하이메탈 1차 미체결 후 재진입가 상승 표본까지 같이 본 뒤 별도 후보로 다룬다.

## 4. 시스템 보완 결과

이번 턴에서 실제 반영한 항목은 다음과 같다.

- `TRADING_RULES`에 `SCALPING_PRE_SUBMIT_PRICE_GUARD_ENABLED`, `SCALPING_PRE_SUBMIT_MAX_BELOW_BID_BPS`를 추가한다.
- 주문 전송 직전 `pre_submit_price_guard_block`을 평가한다.
- `latency_pass`, `order_leg_request`, `order_bundle_submitted`, `pre_submit_price_guard_block`에 가격 스냅샷 필드를 추가한다.
- 테스트로 대한전선형 `48800 / best_bid 50500` 케이스가 주문 미전송으로 차단되는지 확인한다.

구현 기준으로는 다음이 확정됐다.

- `submitted_order_price`, `mark_price_at_submit`, `best_bid_at_submit`, `best_ask_at_submit`, `defensive_order_price`, `reference_target_price`, `resolved_order_price`, `resolution_reason`, `price_below_bid_bps`가 `pipeline_events`에 남는다.
- `BUY_ORDERED.buy_price`는 여전히 `curr_price` 의미를 유지한다. 이는 downstream 손익/보유 로직 영향 범위가 넓어 이번 P0에서는 바꾸지 않았다.
- `strategy-aware resolver`, `SCALPING timeout table`, `microstructure-adaptive band`, `reprice loop`는 아직 구현하지 않았다.

## 5. 코드리뷰 후속 판정

`sniper_state_handlers.py` 코드리뷰에서 지적된 항목 중 same-day hotfix가 필요한 부분은 반영했고, 구조 debt는 별도 checklist 축으로 분리했다.

- 즉시 수정: `locals()` 기반 분기 제거, `reversal_add` 무음 `except` 로깅 전환, `_MARCAP_CACHE` size cap 추가
- 후속 이관: 전역 의존성 context화, `watching/holding/cancel` 모듈 분해, swing trailing TODO 정량화

구조 후속은 [2026-05-06-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-05-06-stage2-todo-checklist.md)의 다음 항목으로 고정했다.

- `[StateHandlersContext0506]`
- `[StateHandlersSplit0506]`
- `[SwingTrailingPolicy0506]`

## 6. 후속조치 보강

### 6-1. 80bps 임계 근거와 한계

현재 즉시 복원 가능한 `submitted` 코호트는 `2026-04-28~2026-04-29`의 stage-paired 표본 `8건`이다.
이 코호트에서 `(best_bid - submitted_price) / best_bid * 10000` 분포는 다음과 같다.

| 지표 | 값 |
| --- | --- |
| sample_count | `8` |
| p50 | `64.44bps` |
| p90 | `239.67bps` |
| p95 | `326.12bps` |
| p99 | `395.28bps` |
| max | `412.57bps` |
| `80bps` 초과 | `3 / 8 = 37.5%` |

해석:

- `record_id=4219`의 `412.57bps`는 명백한 pathology다.
- `80bps`는 현재 복원 가능한 표본에서 상위 outlier 구간을 자르는 값으로는 동작한다.
- 그러나 표본 수가 `8`건에 불과하고, `2026-04-27` 이전에는 `best_bid_at_submit` 계열 필드가 직접 남지 않아 **30~60 영업일 분포를 아직 hard하게 복원하지 못했다.**

따라서 `80bps`는 **임의값으로 고정하지 않고 provisional threshold**로 둔다. `2026-05-06` 후속 항목에서 최근 30~60 영업일 재구성 분포를 다시 붙여 percentile 기준을 재앵커한다.

### 6-2. 비-`SCALPING` 전략 사각지대

현재 차단 가드는 `SCALPING`에만 적용된다. 이는 P0 회귀 위험을 줄이기 위한 의도적 스코핑이지만, `BREAKOUT`/`PULLBACK`/`RESERVE`에서 같은 pathology가 없는지 아직 증명한 것은 아니다.

따라서 다음 보강을 후속 조치로 둔다.

- 비-`SCALPING` 전략에는 **차단 없이** 동일 임계 기준의 `observe-only` 이벤트를 남긴다.
- event 명은 `pre_submit_price_guard_observe` 또는 동등 의미 키로 고정한다.
- 1~2주 누적 후 전략별 분포를 비교해 차단 확대 여부를 결정한다.

### 6-3. P0 회귀 모니터링과 롤백 기준

P0가 "가드를 켰다" 수준에서 끝나지 않도록 다음 KPI와 롤백 조건을 같은 change stream에 묶는다.

| 항목 | 기준 | 조치 |
| --- | --- | --- |
| `pre_submit_price_guard_block_rate` | 일간 `> 0.5%` | review trigger |
| `pre_submit_price_guard_block_rate` | 일간 `> 2.0%` | rollback / threshold 완화 검토 |
| `pre_submit_price_guard_block_rate` | 일간 `= 0%` | 가드 비활성 또는 로깅 누락 점검 |
| `submitted_price_below_bid_bps p99` | 급상승 | 분포 재앵커 및 임계 재검토 |
| 본 케이스 유형 재발 | 차단 없이 통과 | threshold 강화 또는 resolver 우선순위 상향 검토 |

### 6-4. 의사결정 등록부

| # | 결정사항 | 처리 | 근거/조건 |
| --- | --- | --- | --- |
| 1 | `abort_premium` 초기값 | `P1로 연기` | backtest 분포와 divergence log로 결정 |
| 2 | `MAX_REPRICE` | `P2로 연기` | 덕산하이메탈 재진입가 상승 표본 후 결정 |
| 3 | round-figure 적용 범위 | `P1로 연기` | resolver와 동시 설계 |
| 4 | P0 hotfix 분리배포 | `결정 완료` | 체결정책 변경과 안전가드를 분리해 원인귀속 유지 |

### 6-5. `BUY_ORDERED.buy_price` closing condition

`buy_price` 의미 보존은 이번 P0에서 맞는 결정이지만, closing condition 없이 남기지 않는다.

- P1에서 `resolver`가 도입되는 시점을 `schema split` trigger로 둔다.
- 그 시점에 `submitted_order_price`를 canonical로 승격하고, 기존 `buy_price`는 `mark_price_at_submit` alias 또는 deprecated field로 정리한다.
- 이 작업은 별도 checklist 항목 `[BuyPriceSchemaSplitP1]`로 잠근다.

### 6-6. P1 ingress criteria

P1은 "별도 승인"이라는 문구로만 남기지 않고 아래 단계로 잠근다.

| 단계 | 조건 | 산출물 |
| --- | --- | --- |
| Backtest | 최근 `30~60` 영업일 `SCALPING/BREAKOUT` 진입 | 신규 resolver vs 기존 결정의 가격차 분포, 추정 체결률 변화 |
| Observe-only | production `1주` counterfactual log | resolver divergence rate, `record_id=4219` abort 여부 |
| Canary | 특정 종목군 `5영업일` | `submitted_but_unfilled_rate`, `slippage_bps`, `time_to_fill_p50/p90` |

또한 `record_id=4219`는 P1 backtest/observe-only ingress의 **명시적 unit test anchor case**로 유지한다.

## 7. 다음 액션

- `[EntryPriceDaehanCable0429-Postclose]`는 `price cap authority conflict + timeout branch misuse + snapshot ambiguity`로 완료 처리한다.
- `[DynamicEntryPriceP0Guard0430-Preopen]`에서 restart provenance, 새 이벤트 필드 기록 여부, `pre_submit_price_guard_block` 발생 여부를 장전 확인한다.
- `2026-04-30` 장후에는 P0 guard KPI와 rollback threshold를 same-day 기준으로 1차 점검한다.
- `2026-05-06`에는 `80bps` 분포 부록, 비-`SCALPING` observe-only, `BUY_ORDERED.buy_price` schema split closing condition, P1 ingress criteria를 체크리스트로 닫는다. `2026-05-05`는 어린이날 KRX 휴장으로 이관 원본만 남긴다.

## 8. 검증

실제 수행한 검증은 다음과 같다.

```bash
PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_sniper_entry_latency.py src/tests/test_sniper_scale_in.py
DOC_CHECKLIST_PATH=docs/checklists/2026-04-29-stage2-todo-checklist.md PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --dry-run --limit 80
```

결과:

- `pytest` : `100 passed`
- checklist dry-run : `parsed_tasks=48`, `created_or_would_create=10`, 실패 없음

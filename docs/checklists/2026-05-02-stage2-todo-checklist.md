# 2026-05-02 Stage2 To-Do Checklist

## 오늘 목적

- 휴일 원칙을 바이패스하고 `dynamic_entry_ai_price_canary_p2` 내부 OFI/QI orderbook micro feature를 오늘 설계/적용까지 닫는다.
- 신규 standalone entry canary는 만들지 않고, 실주문 영향 owner는 기존 P2 canary로 유지한다.
- 목적은 미진입 회복이 아니라 submitted 직전 불량 호가 흐름 진입 차단이다.
- 실전 효과 판정과 keep/OFF 판단은 `2026-05-04` 장후 checklist로 넘긴다.

## 오늘 강제 규칙

- 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이며 상세 기준은 `Plan Rebase` §1~§6을 따른다.
- `SCALPING_ENTRY_PRICE_ORDERBOOK_MICRO_ENABLED`는 P2 내부 입력 flag이며 독립 entry canary로 세지 않는다.
- `entry_price_v1` response schema는 변경하지 않는다.
- `neutral/insufficient` OFI/QI만으로 `SKIP`하지 않는다.
- fallback/scout/split-entry 주문 경로는 열지 않는다.
- 문서 변경 후 parser 검증은 AI가 실행하고, Project/Calendar 동기화는 사용자 수동 명령으로 처리한다.

## 장후 체크리스트 (18:00~23:59)

- [x] `[OrderbookMicroP2Canary0502-DesignApply] OFI/QI P2 내부 feature 설계/코드/문서 적용` (`Due: 2026-05-02`, `Slot: POSTCLOSE`, `TimeWindow: 18:00~23:59`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [orderbook_stability_observer.py](/home/ubuntu/KORStockScan/src/trading/entry/orderbook_stability_observer.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [kiwoom_websocket.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_websocket.py)
  - 판정 기준: 0D 호가 이벤트의 best bid/ask 잔량과 top-5 depth로 `qi`, `qi_ewma`, `ofi_instant`, `ofi_ewma`, `depth_ewma`, `ofi_norm`, `ofi_z`, `micro_state`를 계산하고, P2 `price_context.orderbook_micro`에 전달한다. `entry_price_v1` schema는 유지하며, flag OFF 시 기존 P2 입력과 동일하게 동작해야 한다.
  - 구현 결과: `SCALPING_ENTRY_PRICE_ORDERBOOK_MICRO_ENABLED=True` 기본값과 env override를 추가했다. `OrderbookStabilityObserver`는 EWMA `lambda=0.3`, z-score 최소 표본 `20`, micro window `60초/300 samples` 기준으로 snapshot을 만든다. `entry_ai_price_canary_skip_order` 이후 `30초/90초` follow-up event로 `mfe_bps/mae_bps`와 `micro_state_at_skip`을 남긴다.
  - rollback guard: `SKIP` 후 `90s MFE >= +80bps`가 skip follow-up의 `30%` 이상이면 `SCALPING_ENTRY_PRICE_ORDERBOOK_MICRO_ENABLED=False`. non-skipped cohort의 fill 전환율이 baseline 대비 `-5%p` 이상 악화되면 micro flag OFF. P2 parse fail/stale context/pre-submit guard 위반은 기존 P1 resolver fail-closed를 유지한다.
  - 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_orderbook_stability_observer.py src/tests/test_sniper_scale_in.py -k 'entry_ai_price_canary or orderbook_stability or orderbook_micro'` -> `11 passed, 112 deselected`
  - 다음 액션: `2026-05-04` 장후 `[OrderbookMicroP2Canary0504-Postclose]`에서 micro-enabled P2 cohort의 `SKIP`, `entry_ai_price_canary_skip_followup`, fill, soft stop, bad-entry, missed upside를 판정한다.

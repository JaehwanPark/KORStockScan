# src/engine Refactor Inventory

기준: `2026-05-23 KST`

## 판정

- 리팩터링은 전체 일괄 이동이 아니라 safe slice 방식으로만 진행한다.
- 기존 `src.engine.<module>` import와 `python -m src.engine.<module>` 실행 경로는 현재 compatibility surface다.
- `MetaPathFinder` shim은 사용하지 않는다. 이동한 파일은 명시적 wrapper module로 old import/CLI를 유지한다.

## Phase 0 Inventory

현재 repo 기준 확인값:

- `src/engine/*.py`: `131`
- `if __name__ == "__main__"` 진입점: `71`
- `deploy/*.sh`의 `src.engine` module/import 참조 라인: `72`
- `src.engine` module 실행을 포함한 deploy script 파일: `20`
- `src/tests/*.py`의 `src.engine` import/monkeypatch 참조 라인: `397`
- `src.engine` 참조가 있는 test 파일: `132`
- README/docs/deploy/tests/engine 내 current path 참조 파일: `345`

## 이동 금지 / 후순위 파일

초기 slice에서 이동하지 않는다.

- runtime/order/provider/threshold/bot restart 경로:
  - `kiwoom_sniper_v2.py`
  - `sniper_state_handlers.py`
  - `kiwoom_orders.py`
  - `ai_engine_openai.py`
  - `threshold_cycle_preopen_apply.py`
- 현재 삭제/retired된 파일:
  - `offline_live_canary_bundle.py`
  - `offline_gatekeeper_fast_reuse_bundle/*`
  - `offline_live_canary_bundle/*`
  - `april_follow_through_backfill.py`
  - `*.bak`
  - `*.backup`
- `src/trading/*`:
  - 장기 canonical 위치는 `src.engine.scalping.<entry|market|order|logging|config>`가 더 적합하다.
  - 단 현재 `src.trading`은 `sniper_entry_latency`, `kiwoom_websocket`, `sniper_state_handlers`가 소비하는 runtime entry/order hot path이므로 report-only/infra 초기 slice 대상이 아니다.
  - 별도 `TradingToScalping` inventory에서 consumer, monkeypatch, runtime submit/stale/qty/cooldown guard 연결, old import compatibility wrapper 전략을 먼저 닫은 뒤 safe slice로만 이동한다.
  - 이동하더라도 기존 `src.trading.*` import는 wrapper로 유지하고, 최소 한 번의 preopen/postclose 안정 검증 전에는 제거하지 않는다.

## 단계별 Gate

각 slice는 아래 순서로 닫는다.

1. 구현: 최대 2~4개 report-only/infra 파일만 이동한다.
2. 코드리뷰: wrapper CLI 전달, public API re-export, monkeypatch 경로, deploy 경로, runtime 권한 누출을 확인한다.
3. 수정보완: 누락 import, wrapper 오류, 테스트/문서 경로 불일치를 즉시 수정한다.
4. 재검증: targeted tests, old/new import smoke, old/new CLI smoke, parser, `git diff --check`를 실행한다.

## Phase 1 Skeleton

이번 변경은 하위 패키지 skeleton과 side-effect-free `__init__.py`만 만든다.

- `automation`
- `scalping`
- `swing`
- `lifecycle`
- `risk`
- `ai`
- `monitoring`
- `infrastructure`

파일 이동, deploy 변경, runtime env 변경은 하지 않는다.

## Phase 2 Slice 1: monitoring report-only

첫 safe slice는 monitoring/report-only 성격의 두 파일만 이동한다.

- `src.engine.monitoring.server_report_comparison`
  - old path: `src.engine.server_report_comparison`
  - compatibility: wrapper module 유지, old CLI `python -m src.engine.server_report_comparison` 유지
- `src.engine.monitoring.error_detector_coverage`
  - old path: `src.engine.error_detector_coverage`
  - compatibility: wrapper module 유지

코드리뷰 기준:

- runtime/order/provider/threshold/bot restart 경로와 무관해야 한다.
- old import/monkeypatch path를 깨지 않아야 한다.
- old CLI와 new CLI가 모두 동작해야 한다.
- deploy 문서는 즉시 migration하지 않고 old wrapper path를 유지한다.

## Long-Running Track: src/trading -> src.engine.scalping

`src/trading`은 이름상 generic trading package지만 현재 코드 기준으로는 스캘핑 진입 latency/orderbook/order helper를 담고 있다. 장기 hierarchy는 `src.engine.scalping` 아래가 맞지만, 이 경로는 live entry/order path와 연결되어 있어 Phase 2 초기 report-only slice와 분리한다.

장기 목표 구조:

- `src.engine.scalping.config.entry_config`
- `src.engine.scalping.entry.entry_policy`
- `src.engine.scalping.entry.entry_types`
- `src.engine.scalping.entry.latency_monitor`
- `src.engine.scalping.entry.normal_entry_builder`
- `src.engine.scalping.entry.orderbook_stability_observer`
- `src.engine.scalping.entry.signal_snapshot`
- `src.engine.scalping.entry.state_machine`
- `src.engine.scalping.market.market_data_cache`
- `src.engine.scalping.market.quote_health`
- `src.engine.scalping.market.websocket_monitor`
- `src.engine.scalping.order.broker_gateway`
- `src.engine.scalping.order.order_manager`
- `src.engine.scalping.order.order_types`
- `src.engine.scalping.order.tick_utils`
- `src.engine.scalping.logging.metrics_recorder`
- `src.engine.scalping.logging.trade_logger`

진행 조건:

1. `rg` inventory로 `src.trading.*` consumer를 모두 수집한다.
2. pure type/util slice부터 시작한다. 후보는 `entry_types.py`, `order_types.py`, `tick_utils.py`, `quote_health.py`, `entry_config.py`다.
3. `sniper_entry_latency.py`, `kiwoom_websocket.py`, `sniper_state_handlers.py`, `kiwoom_orders.py`, broker submit/qty/cooldown/stale guard 경로는 마지막 consumer migration 전까지 기존 import 또는 wrapper를 유지한다.
4. 각 slice는 old/new import smoke와 targeted tests를 모두 통과해야 한다.
5. `src.trading.*` wrapper 제거는 최소 한 번의 preopen/postclose 안정 검증 이후 별도 Phase Final gate에서만 검토한다.

금지선:

- runtime threshold, provider route, broker submit semantics, order qty/cap/cooldown guard, stale quote handling, bot restart 경로를 이 migration의 부수효과로 바꾸지 않는다.
- `src/trading` 전체 디렉터리 일괄 이동이나 direct import rewrite를 금지한다.
- `src.engine.scalping` package `__init__.py`에 import side effect를 만들지 않는다.

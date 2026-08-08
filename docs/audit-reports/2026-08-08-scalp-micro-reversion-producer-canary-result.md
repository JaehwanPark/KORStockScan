# Scalp Micro-Reversion Producer Observation Canary 구현 결과

## 1. 판정

감리 재승인 범위 안에서 producer observation hook과 forward collector의 **소스 구현 및 독립 커밋 고정**을 완료했다.

- producer integration commit: `0679e9071adbe4d14e7309489092793a95cb2a99`
- source/test/deployment manifest: [producer canary integration manifest](./2026-08-08-scalp-micro-reversion-producer-canary-integration-manifest.json)
- source 상태: `producer_hook_present=true`
- 기본 runtime 상태: `observer_runtime_loaded=false`, `observer_runtime_effect=false`
- 거래 권한: `trading_runtime_effect=false`, `trading_decision_effect=false`, `sim_position_effect=false`, `threshold_effect=false`, `broker_effect=false`
- 주문 권한: `actual_order_submitted=false`, `broker_order_forbidden=true`
- Gate B: **미종료**. 장중 canary를 기동하거나 5거래일 실데이터를 수집하지 않았다.

따라서 이번 결과는 “관찰 canary를 안전하게 기동할 수 있는 코드와 배포 기준선이 준비됨”을 뜻한다. 수익성, P2 실데이터 연구, sim assumed-fill, trading runtime 또는 실주문 승인이 아니다.

## 2. 구현 범위

기존 `KiwoomWSManager`가 이미 수신한 0B snapshot만 다음 경로로 전달한다.

```text
existing 0B producer
  -> explicit item venue validation
  -> manual-control exclusion hard veto
  -> immutable RawMarketObservation
  -> bounded put_nowait queue
  -> observer worker / multi-horizon detector / parent-wave path coalescer
  -> dedicated bounded path writer
```

[kiwoom_websocket.py](../../src/engine/kiwoom_websocket.py)는 observer flag가 켜진 경우에만 collector를 lazy import/start한다. 신규 `REG`/`REMOVE`, 종목 수, depth, KRX/NXT quota는 변경하지 않았다. [forward_collector.py](../../src/engine/scalping/micro_reversion/forward_collector.py)는 producer callback에서 JSON 직렬화, 파일 I/O, fsync, detector, replay, 통계, symbol-master I/O, broker 또는 LLM 호출을 하지 않는다.

기능 플래그는 모두 기본 OFF다.

```text
SCALP_MICRO_REVERSION_OBSERVER_ENABLED=false
SCALP_MICRO_REVERSION_PATH_CAPTURE_ENABLED=false
SCALP_MICRO_REVERSION_DISCOVERY_ENABLED=false
```

관찰을 실제로 시작하려면 별도 운영 시점에 observer와 path capture만 명시적으로 켜야 한다. discovery는 Gate B 전 계속 OFF이며, 이번 작업에서는 bot 재기동이나 runtime env 변경을 수행하지 않았다.

## 3. 수동관리 제외와 venue 계약

수동관리 제외 목록은 collector 생성 시 producer callback 밖에서 적재하고, 각 envelope 생성 전에 adapter가 hard veto한다. 제외 종목은 queue, detector, path, event reference에 들어가지 않는다. synthetic regression의 `manual_control_event_leak_count=0`을 확인했다.

Kiwoom 공식 reference gate는 다음을 고정했다.

- upstream: `Kiwoom-Securities/Kiwoom-REST-API@69642586f7d84ba9fd8a6faf1f1537c7fda6568b`
- 확인 시각: `2026-08-08T20:32:10+09:00`
- 확인 경로: `kiwoom_docs/실시간시세.md`의 0B/0D, `kiwoom/realtime/decoders.py`, `kiwoom/realtime/schemas.py`, 0B/0D examples, 로컬 [Kiwoom API contract](../kiwoom-api-data-contract.md)
- 사용 field: 0B FID `20` 체결시각, `10` 현재가, `27/28` 최우선 매도/매수, `15` 체결량
- FID `9081`은 raw provenance로만 보존하고 venue 판정에 사용하지 않는다.
- plain item은 KRX, `_NX`는 NXT로만 인정한다. `_AL`은 SOR view일 뿐 실제 체결 venue 증명이 아니므로 관찰 envelope 생성을 차단한다.

Verified tax/symbol metadata가 없는 종목도 관찰은 가능하지만 경제성 headline, P2-C confirmation, sim 승격 근거로 사용할 수 없다.

## 4. Runtime health 지표

collector snapshot은 다음을 분리해 제공한다.

- producer callback 및 enqueue latency p50/p95/p99
- exchange-to-local receive gap p95, quote age p95
- observation queue depth high-water/full/drop
- path sequence gap/duplicate/out-of-order와 pre/active/post point 수
- writer alive/count/restart/error, queue/full/drop, write/flush/fsync latency
- last persisted sequence, bytes/event, bytes/trade-date, disk remaining, storage self-disable
- observer runtime effect와 trading/sim/threshold/broker effect 불변값

Snapshot 실패도 producer로 전파하지 않고 observer effect를 fail-closed로 보고한다.

## 5. 코드리뷰 및 보완

`korstockscan-review-gate`에 따라 구현 후 producer/consumer 계약, silent failure, runtime authority leak, queue/writer 장애 및 기존 WebSocket 회귀를 검토했다.

1차 리뷰에서 다음을 보완했다.

- adapter 내부 시간만 producer latency로 오인할 수 있어 0B 전처리 전체 end-to-end callback latency reservoir로 교체했다.
- Gate B에 필요한 path sequence gap/duplicate/out-of-order 지표를 collector snapshot에 연결했다.
- bytes/event, bytes/trade-date, writer last error types를 추가했다.
- snapshot 자체가 실패했을 때 `observer_runtime_effect=true`로 잘못 보일 수 있는 경로를 fail-closed `false`로 수정했다.
- writer restart 후 drain과 sequence 연속성 회귀 테스트를 추가했다.

재리뷰 결과 미해결 finding은 없다.

## 6. 검증 결과

- micro-reversion 전체 + Kiwoom WebSocket: `159 passed in 3.74s`
- producer adapter exception isolation: 통과
- observation queue full/drop 및 non-blocking latency: 통과
- writer restart/drain: 통과
- critical disk capture-only self-disable: 통과
- manual-control event leak: `0`
- `_AL` venue 추정 차단: 통과
- forbidden broker/order/execution/AI/ADM/LDM import scan: 통과
- feature flags default OFF 및 무출력: 통과
- Ruff, Black, `py_compile`, `git diff --check`: 통과
- manifest source 20개/test 16개/deployment 2개 및 Git tree/archive 재계산: 통과

## 7. Gate B와 다음 액션

다음 운영 액션은 **다음 정상 거래일에 observer/path capture만 canary로 기동하고 5거래일을 수집하는 것**이다. 기동 전에 commit/manifest 일치와 수동관리 제외 목록을 확인하고, 기동 후 `micro_reversion_forward_collector_snapshot()`을 보존한다.

Gate B는 아래 조건을 모두 만족할 때만 `collector_health_pass_research_data_only`로 닫는다.

- 최소 5거래일, 전체 성숙 event 200건 이상
- required path field coverage 90% 이상
- 정상장 queue drop 0, manual-control event leak 0
- producer p95/p99 latency가 배포 전 기준보다 유의하게 악화되지 않음
- event dedupe/hysteresis/re-arm 및 venue/session 분리 정상
- pre/active/post coverage, restart/gap/recovery, writer/disk 상태 정상
- post-session compression/retention dry-run 통과

Gate B 전에는 P2 실데이터 replay/ranking을 실행하지 않는다. Gate B가 닫혀도 의미는 collector 건강성 승인뿐이며 P2-A/B/C는 연구 전용이다. P2-C 재감리 전 sim assumed-fill을 열지 않고, 별도 사용자 승인 전 trading runtime과 실주문을 열지 않는다.

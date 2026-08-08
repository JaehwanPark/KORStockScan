# Scalp Micro-Reversion Producer Canary 감리 보완 결과

## 1. 판정

최종 감리에서 장중 canary를 보류시킨 exclusion·shutdown·venue finding을 source-only로 보완하고 독립 커밋과 manifest를 고정했다.

- remediation commit: `24b6d04bfd05c5c16c6eb315417810c6a7547989`
- remediation manifest: [producer canary integration manifest](./2026-08-08-scalp-micro-reversion-producer-canary-integration-manifest.json)
- 관련 회귀: `169 passed in 3.85s`
- 기본 상태: observer/path/discovery 모두 OFF
- runtime/order authority: `trading_runtime_effect=false`, `trading_decision_effect=false`, `sim_position_effect=false`, `actual_order_submitted=false`, `broker_order_forbidden=true`
- 운영 상태: `source_remediated_reaudit_pending`

이번 작업에서 bot 재기동, runtime env 변경, 신규 `REG`/`REMOVE`, 장중 데이터 수집, P2 replay, sim 또는 실주문은 실행하지 않았다. 따라서 canary 활성화는 아직 승인된 상태가 아니며 새 commit에 대한 감리 재승인을 먼저 받아야 한다.

## 2. 감리 finding별 조치

### 2.1 장중 수동관리 제외

collector worker가 1초 주기로 설정 파일을 갱신한다. 파일 I/O는 producer callback에서 수행하지 않는다. 외부에서 `refresh_manual_exclusions()`를 호출하는 경로도 같은 직렬화 계약을 사용한다.

새 제외 종목이 발견되면 다음 상태를 worker 처리와 상호 배제한 뒤 폐기한다.

- pre-event ring row와 sequence/timestamp watermark
- horizon별 detector state와 parent-wave state
- active path segment
- collector series sequence와 detector clock
- 제외 갱신 전에 queue에 들어온 old-version envelope의 worker-side 재검증

Envelope/path schema에는 `manual_control_exclusion_version`, `manual_control_exclusion_checked_at`, `sequence_epoch`, `series_sequence`를 추가했다. `manual_control_event_leak_count`는 더 이상 snapshot 상수가 아니라 collector 실측 counter다. 함께 추가한 실측값은 refresh/new-exclusion/state-purge/active-segment-purge/post-exclusion-envelope/post-exclusion-event count다.

### 2.2 Collector 종료와 재시작

Collector는 명시적 one-shot lifecycle(`new -> running -> closing -> closed`)을 채택했다.

- worker drain timeout이 발생해도 등록된 모든 writer의 `close()`를 시도한다.
- 한 writer의 close 실패가 나머지 writer 정리를 막지 않는다.
- shutdown 시작 후 새 writer 생성을 차단한다.
- worker와 writer 오류를 수집한 뒤 종료 오류로 보고한다.
- `close()`는 idempotent이고, closed collector의 `start()`는 fail-closed한다.

회귀 테스트는 worker timeout과 첫 writer close 실패를 동시에 주입하고 두 번째 writer까지 정리되는지 확인한다.

### 2.3 0B venue provenance

0B item은 `last_realtime_type_item["0B"]`만 사용한다. generic `last_ws_item` fallback을 제거했으며 type-specific item이 없으면 `MISSING_0B_ITEM`으로 차단한다. `_AL`은 계속 차단하고 `_NX`만 NXT로 인정한다. FID `9081`은 raw provenance일 뿐 venue 판정에 사용하지 않는다.

Kiwoom reference gate는 기존 검증을 유지한다.

- upstream: `Kiwoom-Securities/Kiwoom-REST-API@69642586f7d84ba9fd8a6faf1f1537c7fda6568b`
- 확인 경로: `kiwoom_docs/실시간시세.md` 0B/0D, realtime decoder/schema, 공식 examples, 로컬 [Kiwoom API contract](../kiwoom-api-data-contract.md)
- producer hook: [kiwoom_websocket.py](../../src/engine/kiwoom_websocket.py)의 `_queue_tick_event`는 0B에서만 observer를 호출하며, `_observe_micro_reversion_forward`가 예외를 격리한다. `_handle_message`는 lock 안에서 type-specific item/venue를 갱신한 snapshot copy를 hook에 전달한다.

### 2.4 Timestamp와 원천 validation 계측

- exchange future skew tolerance: `1,000ms`; 허용 범위는 receive timestamp로 clamp하고 adjustment count를 남긴다.
- maximum exchange-to-receive lag: `10,000ms`; 초과 row는 stale timestamp block으로 제외한다.
- `invalid_snapshot_rate`, `venue_block_rate`, `timestamp_block_rate`, `invalid_envelope_rate`, `quote_age_missing_rate`, `bbo_complete_rate`를 callback 전체 분모로 제공한다.

### 2.5 Sequence와 reference/path 정합성

Source watermark를 `(sequence_epoch, symbol, venue, session_bucket, series_sequence)`로 명시했다. queue full과 invalid envelope로 생긴 gap은 원인별 explained gap으로 집계하고, 원인이 없는 차이는 `unexplained_sequence_gap_count`로 분리한다. Writer는 aggregate max 외에 series별 마지막 persisted epoch/sequence를 제공한다.

Event reference와 path는 별도 append 파일을 유지하지만, clean shutdown에서 두 파일을 재독해 coverage, orphan reference, unreferenced segment를 대조한다. `reference_reconciliation_completed`가 false이거나 reconciliation error가 있으면 Gate B를 통과할 수 없다. Reference fsync latency p95/p99와 detector clock adjustment count/max도 추가했다.

## 3. 코드리뷰 결과

`korstockscan-review-gate`에 따라 producer/consumer, silent-fail, authority leak, 경합과 종료 경로를 재검토했다.

1차 리뷰에서 shutdown 시 writer 목록을 너무 일찍 고정하면 drain 중 새 writer가 생길 수 있는 경합을 발견했다. shutdown 플래그 아래 writer 생성을 차단하고 join 시도 후 전체 writer를 다시 수집하도록 수정했다.

재리뷰 결과 이번 remediation 범위의 미해결 코드 finding은 없다. 변경 모듈에는 broker/order/execution/AI/ADM/LDM dependency가 추가되지 않았고 producer callback은 여전히 bounded `put_nowait`까지만 수행한다.

## 4. 검증

- micro-reversion 전체 + Kiwoom WebSocket: `169 passed in 3.85s`
- 동적 file-backed exclusion refresh: 통과
- old-version queued envelope worker veto: 통과
- ring/detector/parent-wave/active segment purge: 통과
- 실측 manual-control leak: `0` synthetic regression 통과
- worker timeout + 복수 writer cleanup + one-shot restart rejection: 통과
- missing type-specific 0B item fail-closed: 통과
- future skew tolerance와 stale lag block: 통과
- queue/invalid-envelope explained gap과 unexplained gap 분리: 통과
- per-series persisted watermark: 통과
- reference/path 정상 coverage 100% 및 orphan/unreferenced synthetic 검출: 통과
- reference write latency와 detector clock adjustment 계측: 통과
- Ruff, Black, compileall, `git diff --check`: 통과
- manifest commit/tree/archive/source 20개/test 16개 hash 재검산: 통과

## 5. 아직 닫지 않은 운영 증적

감리가 요구한 collector 계측 surface는 source와 synthetic regression으로 닫았다. 다만 다음은 실제 정상 거래일 canary 없이는 만들 수 없으므로 완료로 표시하지 않는다.

- 최소 5거래일·성숙 event 200건
- 배포 전후 producer p95/p99 및 장중 detector-clock adjustment 실제 baseline
- 실제 장중 queue/writer/reference/path reconciliation zero-error 결과
- post-session compression/retention drill

또한 reference/path는 combined journal이 아니라 별도 파일 + shutdown reconciliation 방식이다. 따라서 reconciliation 미완료나 error는 fail-closed한다. 운영 증적이 없으므로 Gate B, P2-A/B/C, sim assumed-fill, trading runtime과 실주문은 계속 차단한다.

## 6. 다음 액션

다음 순서는 `감리 재승인 -> 정상 거래일 observer/path canary 활성화 -> Gate B 수집`이다. 감리 재승인 전 runtime flag를 켜거나 bot을 재기동하지 않는다.

Gate B는 최소 5거래일·성숙 event 200건과 함께 실제 leak/error/drop/reconciliation/validation-rate 지표를 모두 제출해야 한다. Gate B 통과는 research data collector 건강성 승인일 뿐 P2 또는 매매 권한 승인이 아니다.

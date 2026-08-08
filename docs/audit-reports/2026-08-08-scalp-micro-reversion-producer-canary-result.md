# Scalp Micro-Reversion Producer Canary 재감리 보완 결과

## 1. 판정

재감리에서 지적된 네 가지 장중 canary blocker와 producer hook 증적 부족을 source-only로 보완했다.

- integration commit: `746c015b52abe8880ea2a6317c9f2a4d6b54394f`
- integration tree: `4d0cf13453204862f471b4a8ddc55792e6e4185a`
- manifest: [producer canary integration manifest](./2026-08-08-scalp-micro-reversion-producer-canary-integration-manifest.json)
- 검증: micro-reversion 전체 + Kiwoom WebSocket `177 passed in 3.98s`
- 현재 상태: `monitoring_delta_reviewed_observer_off_reaudit_required`

이번 보완은 소스·테스트·감리 증적만 변경했다. observer/path/discovery는 모두 기본 OFF이며 bot 재기동, runtime env 변경, 신규 구독, 장중 수집, Gate B, P2 replay, sim, trading runtime, 실주문은 실행하지 않았다.

따라서 현재 요청 판정은 다음과 같다.

```text
source_remediation_merge=PASS
default_off_deployment=PASS
observer_canary_runtime_activation=HOLD_PENDING_MONITORING_DELTA_REAUDIT
gate_b_collector_health=NOT_STARTED
p2_real_data_replay=BLOCKED
sim_assumed_fill=NOT_APPROVED
trading_runtime=NOT_APPROVED
real_order=NOT_APPROVED
```

## 2. 재감리 finding별 폐쇄 내용

### 2.1 Exclusion add/remove 사이 stale envelope 재유입

`manual_control_exclusion_version`은 이제 종목별 generation token으로 envelope에 기록된다. worker는 detector와 sequence-gap 계산 전에 다음 순서로 현재 상태를 재검증한다.

`manual_control_exclusion_checked_at`은 점검 시각 provenance로 유지한다. 동일 exclusion set의 주기적 refresh만으로 정상 queue row를 폐기하지 않기 위해 equality authority로 쓰지 않고, 실제 상태 전환은 종목별 generation과 series epoch가 담당한다.

1. 현재 수동관리 제외 여부
2. envelope generation과 현재 종목 generation 일치
3. envelope `sequence_epoch`와 현재 series epoch 일치
4. sequence gap 계산과 detector/path 처리

불일치 row는 detector, ring, path로 전달하지 않고 `stale_manual_exclusion_generation_envelope_count` 또는 `stale_sequence_epoch_envelope_count`를 증가시킨다. `enqueue E1 → exclusion 추가·state purge → exclusion 해제 → E1 dequeue` 경합 테스트에서 detector/path 진입은 0건이다.

관련 소스: [worker generation/epoch gate](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion/forward_collector.py:831), [종목별 generation 관리](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion/observation_adapter.py:398)

### 2.2 Event leak counter 실측 경로

Detector가 event를 반환한 뒤 coalescer 등록 직전에 event symbol, 현재 exclusion, generation, epoch를 다시 검사한다. 불일치 event는 등록·reference append·path submit 전에 차단하고 다음 두 값을 실제 증가시킨다.

- `manual_control_post_exclusion_event_count`
- `manual_control_event_leak_count`

이 leak 값은 영속화된 실제 leak 수가 아니라 **등록 직전에 적발해 차단한 would-be leak 수**다. 정상 canary의 합격값은 0이다. 회귀테스트는 detector 처리 중 exclusion 변경을 주입해 두 counter가 각각 1이 되고 `shock_event_count=0`, `event_reference_persisted_count=0`인 것을 확인한다.

관련 소스: [event registration guard](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion/forward_collector.py:861)

### 2.3 In-flight producer callback 종료 barrier

`observe_kiwoom_0b()`는 accepting 확인과 active callback 증가를 동일 condition 아래 수행하고, `finally`에서 감소·notify한다. `close()`는 먼저 accepting을 닫고 active callback이 0이 될 때까지 기다린 뒤에만 stop 요청과 worker drain을 시작한다.

Callback barrier timeout이면 worker와 writer를 닫지 않고 `CLOSE_FAILED`로 남긴다. 이 때문에 이미 진입한 callback은 row를 enqueue할 수 있고 살아 있는 worker가 이를 소비한다. 후속 `close()`는 drain과 writer 종료를 재시도한다. 회귀테스트는 timestamp 처리 중 callback을 pause한 두 경우를 검증한다.

- close가 callback resume까지 대기한 뒤 `enqueued=processed=1`, queue 0으로 종료
- 첫 close timeout 후 `CLOSE_FAILED`, worker 유지, callback resume, 두 번째 close 성공, queue 0

관련 소스: [callback counter](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion/forward_collector.py:492), [shutdown barrier](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion/forward_collector.py:382)

### 2.4 Retryable shutdown lifecycle와 writer 접근 차단

Lifecycle은 `NEW → RUNNING → CLOSING → CLOSE_FAILED|CLOSED`다. worker가 살아 있거나 writer close/상태 확인 또는 reconciliation이 실패하면 CLOSED로 확정하지 않는다. 후속 `close()`가 worker와 모든 writer를 다시 확인해 모두 종료되고 clean reconciliation이 완료된 경우에만 CLOSED가 된다.

`_writer_for()`는 기존 writer 조회보다 `_writers_closing`을 먼저 검사하므로 shutdown 이후 이미 닫힌 writer도 반환하지 않는다. 다음 종료 지표를 snapshot에 추가했다.

- `collector_close_attempt_count`
- `collector_close_failure_count`
- `collector_worker_alive_after_close_count`
- `writer_alive_after_close_count`
- `collector_last_close_error_types`

WebSocket owner도 첫 close 실패 시 collector 참조를 유지하고 후속 `stop()`에서 재시도한다. 성공 후에만 참조와 오류 상태를 지운다.

관련 소스: [collector close lifecycle](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion/forward_collector.py:382), [writer shutdown gate](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion/forward_collector.py:1138), [producer retry owner](/home/ubuntu/KORStockScan/src/engine/kiwoom_websocket.py:2148)

### 2.5 Reconciliation 비용·중복 계측

Clean shutdown reconciliation에 다음 지표를 추가했다.

- `reference_reconciliation_duration_ms`
- `reference_reconciliation_path_rows_scanned`
- `reference_reconciliation_reference_rows_scanned`
- `reference_reconciliation_peak_tracked_key_count`
- `duplicate_event_reference_count`
- `duplicate_event_id_count`
- `duplicate_path_reference_pair_count`

`peak_tracked_key_count`는 Python process RSS가 아니라 reconciliation이 동시에 보유한 식별 key 수의 보수적 proxy다. 장중 canary 후 duration과 row/key 규모가 종료 예산을 초과하면 post-session 별도 작업 분리를 검토한다. Synthetic duplicate reference 2행으로 세 중복 counter가 각각 1임을 확인했다.

## 3. Producer hook line-level 증적

실제 producer 원문은 integration commit과 manifest source hash에 포함했다.

| 검증 항목 | 원문 근거 | 판정 |
| --- | --- | --- |
| 기본 OFF lazy load | [1899](/home/ubuntu/KORStockScan/src/engine/kiwoom_websocket.py:1899) | env가 false면 collector 객체를 만들지 않음 |
| 0B 전용 hook | [1875](/home/ubuntu/KORStockScan/src/engine/kiwoom_websocket.py:1875) | `normalized_realtime_type == "0B"`에서만 호출 |
| hook 예외 격리 | [1956](/home/ubuntu/KORStockScan/src/engine/kiwoom_websocket.py:1956) | 예외를 producer로 전파하지 않고 type만 기록 |
| snapshot 완성 위치 | [2697](/home/ubuntu/KORStockScan/src/engine/kiwoom_websocket.py:2697), [3439](/home/ubuntu/KORStockScan/src/engine/kiwoom_websocket.py:3439) | type-specific item/venue와 trade snapshot을 market-data lock 안에서 복제 |
| observer lock 분리 | [3440](/home/ubuntu/KORStockScan/src/engine/kiwoom_websocket.py:3440) | observer normalization/enqueue는 market-data lock 밖에서 실행 |
| bounded hot path | [observe entry](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion/forward_collector.py:492) | callback은 정규화 후 bounded `put_nowait`; detector/JSON/fsync 없음 |
| 종료 순서·재시도 | [2148](/home/ubuntu/KORStockScan/src/engine/kiwoom_websocket.py:2148) | producer threads join 후 최대 10초 collector close; 실패 시 참조 유지·재호출 가능 |

Observer close는 WebSocket producer thread join 이후 호출되므로 producer lock을 점유한 상태에서 기다리지 않는다. 종료는 무제한 대기가 아니라 collector `timeout_sec=10.0`으로 제한되며, 실패 시 프로세스 정상성보다 CLOSED를 거짓 보고하지 않는 fail-closed/retryable 계약을 우선한다.

## 4. 스키마와 검증

종목별 generation 및 새 종료·reconciliation metric의 의미 변경을 반영해 스키마를 올렸다.

- observation envelope: `scalp_micro_reversion_observation_envelope_v3`
- forward collector snapshot: `scalp_micro_reversion_forward_collector_v3`
- market path point: `scalp_micro_reversion_market_path_point_v5`

최종 review gate 결과:

- micro-reversion 전체 + Kiwoom WebSocket: `177 passed in 3.98s`
- add/remove stale generation 경합: 통과
- stale series epoch detector 이전 veto: 통과
- event-registration leak counter 증가·영속화 0: 통과
- in-flight callback wait/drain: 통과
- callback barrier timeout 후 close 재시도: 통과
- worker timeout + 모든 writer close + `CLOSE_FAILED` 재시도: 통과
- producer 0B-only/예외 격리/owner close 재시도: 통과
- reconciliation row/cost proxy/duplicate 계측: 통과
- Ruff, Black, compileall, JSON parser, `git diff --check`: 통과

코드 재리뷰에서 남은 source finding은 없다. Broker/order/execution/AI/ADM/LDM dependency 또는 신규 REG/REMOVE, threshold/provider/bot/quantity/cap 변경도 없다.

## 5. 남은 운영 증적과 다음 액션

현재 확보한 것은 source 구조와 synthetic regression이다. 다음 운영 증적은 아직 없다.

- 정상 거래일 최소 5일, 성숙 event 200건
- producer callback p95/p99와 배포 전후 latency 비교
- 장중 queue/drop/gap/manual-control leak/writer error 실측
- 실제 reference/path reconciliation duration·rows·tracked-key 규모와 zero-error 결과
- post-session compression/retention drill

이 단계의 다음 액션은 **새 commit·manifest·본 line-level 증적의 감리 재승인**이었다. 아래 §6의 최종 재감리에서 조건부 승인을 받았지만, canary는 여전히 기존 구독의 관찰 수집만 허용하며 Gate B 통과 전 P2 actual-data ranking을 실행하지 않는다. Gate B는 collector 건강성 승인일 뿐 sim, trading runtime 또는 실주문 승인이 아니다.

## 6. 최종 재감리 승인과 활성화 preflight

최종 재감리는 integration commit `746c015b52abe8880ea2a6317c9f2a4d6b54394f`에 대해 `observer_path_canary_activation=CONDITIONAL_GO`를 부여했다. 승인 범위는 기존 구독의 observer/path capture뿐이며 discovery, P2, sim, trading runtime, 주문은 계속 차단된다.

2026-08-08 22:09 KST 최초 preflight에서는 폐기된 원격 서버를 배포 대상으로 오인했다. 사용자 확인에 따라 배포 대상은 현재 main 서버 하나로 정정했으며, 원격 DNS·SSH 조건은 canary gate에서 제외한다. 정정 후 상태는 `conditional_go_latency_preflight_pending`이다.

| 조건 | 결과 | 근거 |
| --- | --- | --- |
| 핵심 파일 4개 SHA-256 | PASS | manifest 값과 모두 일치 |
| 승인 commit이 main 배포본의 ancestor | PASS | `746c015b` ancestor 확인 |
| main working tree clean | PASS | preflight 시 `git status --porcelain` 출력 없음 |
| 승인 deployment source 동일성 | PASS | `746c015b..HEAD`의 `kiwoom_websocket.py`, micro-reversion package, `run_bot.sh` diff 0건; 핵심 hash 일치 |
| 후속 HEAD 차이 | DOCUMENT_ONLY | 승인 commit 이후 변경은 감리보고서·manifest·checklist 증적 문서뿐이며 실행 소스 차이 없음 |
| producer p95/p99 baseline·허용폭 | BLOCKED | main 서버의 canary 전 baseline과 숫자 허용폭 미동결 |
| 거래일·실행 프로세스 | BLOCKED | 토요일이며 local bot process 없음 |

따라서 플래그, runtime env, bot 상태는 변경하지 않았다. 현재 허용 설정도 아직 적용하지 않았다.

```text
SCALP_MICRO_REVERSION_OBSERVER_ENABLED=false_or_unset
SCALP_MICRO_REVERSION_PATH_CAPTURE_ENABLED=false_or_unset
SCALP_MICRO_REVERSION_DISCOVERY_ENABLED=false_or_unset

observer_path_canary_activation=CONDITIONAL_GO_LATENCY_PREFLIGHT_PENDING
gate_b_collector_health=NOT_STARTED
p2_real_data_replay=BLOCKED_UNTIL_GATE_B
```

다음 실행은 main 서버에서 callback p95/p99 baseline 및 절대/상대 허용폭을 숫자로 고정하는 것이다. 승인 source/hash/clean 검증과 latency 조건이 모두 통과한 정상 거래일에만 observer/path=true, discovery=false를 적용한다. 원격 서버 접근 복구는 더 이상 선행조건이 아니다.

## 7. Main 서버 latency preflight와 fail-closed monitor 보완

2026-08-08 22:45 KST에 현재 main 서버에서 동일한 유효 합성 Kiwoom 0B snapshot으로 observer OFF/ON preflight를 각각 5회 실행했다. 각 반복은 warm-up 500회와 측정 5,000회로 구성했고 observer ON은 `path_capture_enabled=true`, `discovery_enabled=false`로 고정했다.

| 항목 | 최대 관측값 | 동결 한계 |
| --- | ---: | ---: |
| observer OFF external p95 | `0.000130ms` | 비교 기준만 사용 |
| observer OFF external p99 | `0.000145ms` | 비교 기준만 사용 |
| observer ON external p95 | `0.027391ms` | 참고값 |
| observer ON external p99 | `0.033756ms` | 참고값 |
| collector internal p95 | `0.026090ms` | `1.0ms` |
| collector internal p99 | `0.032335ms` | `2.0ms` |
| queue drop / worker error | `0 / 0` | `0 / 0` |

수치 원본은 [callback latency baseline](./2026-08-08-scalp-micro-reversion-callback-latency-baseline.json.txt), runtime 한계는 [canary guard config](/home/ubuntu/KORStockScan/configs/scalp_micro_reversion_canary_guard.toml)에 고정했다. 이 값은 main 서버 synthetic preflight일 뿐 정상장 실제 producer latency나 전략 EV 근거가 아니다. 장중 첫 1,000 callback까지는 latency만 warm-up으로 두고 drop/error/gap/leak/storage/authority 위반은 첫 snapshot부터 즉시 중단한다.

장중 관측 공백을 닫기 위해 [canary monitor](/home/ubuntu/KORStockScan/src/engine/scalping/micro_reversion/canary_monitor.py)를 추가하고 producer/dashboard와 분리된 observer 전용 10초 background monitor loop에 연결했다. monitor는 다음을 수행한다.

- `data/runtime/scalp_micro_reversion_forward_collector/latest.json`에 atomic snapshot과 `valid_until_epoch`를 기록한다.
- queue/path/writer drop, worker/writer/reference/reconciliation error, manual-control post-exclusion/leak, unexplained gap, orphan/unreferenced/duplicate, storage degrade/self-disable, close failure/alive count, authority invariant, 동결 p95/p99를 fail-closed로 판정한다.
- stop metric이 발생하면 main bot이나 주문 경로를 중단하지 않고 micro-reversion observer collector만 close한다.
- collector close를 직렬화하고 clean close 뒤 최종 reconciliation snapshot을 기록한다. final snapshot 실패는 오류 상태로 보존한다.
- config 누락·파싱 오류·monitor write 실패도 observer만 fail-closed한다.

코드리뷰에서 JSON 반환값 tuple/list 불일치, 종료 후 warm-up 상태 오표기, 상대 CWD config 경로, final snapshot 오류 상태 소실, writer liveness 미검증, auto-stop 후 동일 manager 재활성화, close-pending collector overwrite 가능성, monitor thread 시작 실패 시 collector 고립 가능성, ignored JSON 증적 누락 가능성, dashboard/callback 선후관계에 따른 마지막 tick 오류 관측 지연을 발견해 보완했다. monitor/collector targeted test는 `38 passed`, micro-reversion 전체와 Kiwoom WebSocket 회귀는 `191 passed in 4.31s`이며 Ruff, Black, compileall, JSON/TOML parser, checklist parser(`count=30`), `git diff --check`도 통과했다.

이번 monitor 연결은 `kiwoom_websocket.py` 실행 소스를 변경하므로 기존 `746c015b` exact-source 조건부 승인을 그대로 사용해 장중 활성화할 수 없다. 현재 플래그와 bot 상태는 변경하지 않았으며 최신 판정은 다음과 같다.

```text
main_server_latency_preflight=PASS_SYNTHETIC_OPERATIONAL_ONLY
numeric_latency_limits=FROZEN_P95_1MS_P99_2MS
intraday_stop_metric_persistence=IMPLEMENTED
observer_only_auto_stop=IMPLEMENTED
monitoring_delta_code_review=PASS
observer_path_canary_activation=HOLD_PENDING_MONITORING_DELTA_REAUDIT
gate_b_collector_health=NOT_STARTED
p2_real_data_replay=BLOCKED_UNTIL_GATE_B
sim_or_trading_authority=NOT_APPROVED
```

다음 액션은 이 monitoring delta를 commit/manifest로 고정해 감리 재승인을 받은 뒤, 정상 거래일 장전에만 `observer=true`, `path_capture=true`, `discovery=false`로 canary를 시작하는 것이다.

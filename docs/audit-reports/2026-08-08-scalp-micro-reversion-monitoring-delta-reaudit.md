# Scalp Micro-Reversion Monitoring Delta 재감리 보고서

## 1. 종합 판정

`c4f48a283cd497310d59129d494c85b8077c059a`의 monitoring delta는 **소스·기본 OFF 배포 기준 PASS**, observer/path canary 활성화는 **조건부 승인**으로 판정한다.

```text
monitoring_delta_source_review=PASS
manifest_integrity=PASS
default_off_deployment=PASS
observer_path_canary_activation=CONDITIONAL_GO_AFTER_ARTIFACT_COMMIT_AND_CLEAN_PREOPEN_RECHECK
gate_b_collector_health=NOT_STARTED
p2_actual_path_discovery=BLOCKED_UNTIL_GATE_B
sim_or_trading_authority=NOT_APPROVED
```

이 승인은 기존 구독 안에서 `observer=true`, `path_capture=true`, `discovery=false`로 수집하는 observer canary에만 적용된다. 현재 시점의 플래그 변경, 봇 재기동, 실제 P2 ranking, sim position, 실주문, BUY/WAIT/DROP·청산 판단, threshold/provider/quantity/cap 변경은 승인하지 않는다.

## 2. 재감리 기준 객체

| 항목 | 고정값 |
| --- | --- |
| integration commit | `c4f48a283cd497310d59129d494c85b8077c059a` |
| tree | `7266d30d71f42bee6e189d1ec7c0ff3a78674815` |
| parent | `fe12ca5ca86051b8b2a28617c98603fb8722e8f4` |
| 이전 조건부 승인 commit | `746c015b52abe8880ea2a6317c9f2a4d6b54394f` |
| git archive SHA-256 | `61626a2f9eeb8a82e6872787d8c67f7b71d4bf5f3334dc92d23b29691889184e` |
| source manifest SHA-256 | `30f84fbadc58f0d9ac2a6a225fc9176339b990d267f2da41b9eba6fd88028c49` |
| test manifest SHA-256 | `64e2f1dac1bb9628608b676c29c05b7752897f349ce1e393a657c2338888c674` |
| monitoring delta SHA-256 | `47eaabef61a35e9faab6e89fca70ecf6cb95e1ca4fd99d99072b8dec6c57c8c7` |
| deployment surface SHA-256 | `1bb8f81a1f7facb26cd0da76e533ac2c94dae960e91015ee34caf6a4135a900d` |

상세 파일별 해시는 [monitoring delta manifest](./2026-08-08-scalp-micro-reversion-monitoring-delta-manifest.json.txt)에 고정했다. Manifest 생성 직전 main과 `origin/main`은 동일했고 working tree는 clean이었다.

## 3. Delta 검토 결과

### 3.1 변경 목적과 범위

이전 조건부 승인본 이후 실행 소스 변경은 다음 두 축이다.

1. `kiwoom_websocket.py`에 observer 전용 10초 monitor lifecycle, atomic snapshot 호출, observer-only fail-closed close, auto-stop latch와 retryable close 보호를 연결했다.
2. `canary_monitor.py`와 동결 TOML guard를 추가해 drop/error/gap/leak/storage/liveness/authority/latency 위반을 observer 중단 조건으로 만들었다.

Forward collector, observation adapter, path journal의 기존 승인 해시는 각각 `64e55a…`, `0d526d…`, `2fa378…`로 유지됐다. 신규 unit/wrapper나 REG/REMOVE 호출은 추가하지 않았다.

### 3.2 Hot-path와 장애 격리

0B callback은 기존 collector의 bounded non-blocking enqueue만 호출한다. JSON 저장, guard 평가, detector/replay, fsync는 callback 및 market-data lock 밖의 monitor/worker 경로에 남아 있다.

Monitor의 파일 기록·설정 파싱·snapshot 평가가 실패하거나 stop metric이 발생하면 micro-reversion collector만 close한다. 메인 WebSocket, 봇 프로세스, 주문 경로를 중단하거나 변경할 권한은 없다. Close 실패 시 collector 참조를 보존하고 후속 close를 재시도하며, auto-stop 사유는 manager lifetime 동안 latch된다.

### 3.3 Default OFF와 권한 경계

`SCALP_MICRO_REVERSION_OBSERVER_ENABLED`의 기본값은 false다. Path/discovery flag도 기본 false이며 manifest 생성과 재감리 중 runtime env나 봇 상태를 변경하지 않았다.

Monitor metric contract는 `decision_authority=observer_canary_stop_only_no_trading_authority`이고 다음 값은 계속 false다.

- `p2_real_data_discovery_run`
- `selection_authority`
- `sim_position_effect`
- `trading_runtime_effect`
- `trading_decision_effect`
- `threshold_effect`
- `broker_effect`
- `actual_order_submitted`

`broker_order_forbidden=true`를 유지한다. Broker/order/AI/ADM/LDM dependency 및 권한 누출 scan에서도 finding이 없었다.

### 3.4 Latency guard

Main 서버의 동일 유효 합성 0B observer OFF/ON preflight는 반복 5회, 각 warm-up 500건과 측정 5,000건으로 수행됐다.

| 항목 | 최대 관측 | 동결 한계 |
| --- | ---: | ---: |
| observer OFF external p95 | `0.000130ms` | 비교 기준 |
| observer OFF external p99 | `0.000145ms` | 비교 기준 |
| observer ON internal p95 | `0.026090ms` | `1.0ms` |
| observer ON internal p99 | `0.032335ms` | `2.0ms` |
| queue drop / worker error | `0 / 0` | `0 / 0` |

Latency guard는 callback 1,000건 이후 동작한다. Drop/error/gap/leak/storage/liveness/authority 위반은 warm-up과 무관하게 첫 monitor snapshot부터 중단 조건이다. 이 preflight는 운영 안전 baseline이지 전략 EV나 실제 장중 성능 증거가 아니다.

## 4. 검증 결과

재감리 중 exact commit source를 대상으로 다음 검증을 다시 실행했다.

- `src/tests/test_micro_reversion_*.py` + `src/tests/test_kiwoom_websocket.py`: `191 passed in 4.30s`
- Ruff: PASS
- Black check: PASS
- compileall: PASS
- JSON/TOML parse와 baseline↔config source hash test: PASS
- Broker/order/AI/ADM/LDM 권한 누출 scan: PASS
- 재리뷰 미해결 finding: 0건

Kiwoom 공식 reference gate는 이번 delta에서 다시 열지 않았다. REST/WebSocket 요청·응답 필드, realtime FID, REG/REMOVE, reconnect/resubscribe, 인증, 주문, continuation 계약은 변경하지 않았고 기존 normalized 0B snapshot의 observer lifecycle만 변경했기 때문이다. 이전 공식 reference 확인 commit `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`의 0B 계약을 그대로 사용한다.

## 5. 조건부 승인 조건과 중단 기준

장전 활성화 전 다음 조건을 모두 재확인해야 한다.

1. 본 manifest와 재감리 보고서를 commit·push한 뒤 main working tree가 clean일 것.
2. `c4f48a28`가 배포 HEAD의 ancestor이고 deployment surface 7개 파일 해시가 manifest와 일치할 것.
3. 정상 거래일 장전이며 동일 stage의 다른 producer canary와 충돌하지 않을 것.
4. 최초 설정은 `observer=true`, `path_capture=true`, `discovery=false`로 제한할 것.
5. `latest.json`이 30초 이내 fresh이고 선언된 stop metric이 모두 0일 것.

다음 중 하나라도 발생하면 observer를 즉시 중단하고 Gate B를 열지 않는다.

- p95 `>1.0ms` 또는 p99 `>2.0ms` after 1,000 callbacks
- queue/path/writer drop, worker/writer/storage error 또는 writer liveness mismatch
- unexplained sequence gap, orphan/unreferenced/duplicate reference·event·pair
- manual-control post-exclusion envelope/event 또는 would-be leak
- snapshot stale/write/config failure, close/reconciliation failure
- selection/sim/trading/threshold/broker authority invariant 위반

## 6. 다음 액션

Manifest·재감리 보고서·체크리스트 갱신의 main commit·push 완료는 활성화 선행조건이다. Repository 반영 완료 후의 다음 실행 owner는 정상 거래일 PREOPEN exact source/hash/clean 재확인이며, 이를 통과한 경우에만 observer/path canary를 시작한다.

장중 결과는 `producer_canary_observation_pending`, `collector_health_pass_research_data_only`, `path_coverage_insufficient`, `journal_degraded`, `manual_control_leak_blocked` 중 하나로 닫는다. `collector_health_pass_research_data_only`가 되기 전에는 P2 actual-path discovery를 실행하지 않는다. Gate B가 통과해도 sim 또는 실거래 권한은 자동으로 열리지 않는다.

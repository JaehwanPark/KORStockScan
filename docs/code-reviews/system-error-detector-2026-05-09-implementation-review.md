# System Error Detector - 구현 코드리뷰

작성일: `2026-05-09T20:06:17+09:00`
구현 기준: 당시 구현 설계서(원본은 사용자 요청으로 삭제됨). 구현 및 검증 기록은 이 문서에 유지한다.

## 1. 구현 범위

시스템 에러탐지 및 처리 자동화 **Phase 1 + Phase 2 + Phase 3 구현 완료**. 6개 detector (process health, cron completion, log scanner, artifact freshness, resource usage, stale lock), bot_main.py daemon thread integration, Telegram alert dedup, env override, scalper/sniper thread heartbeat, disk-low auto log rotation, stale lock cleanup까지 구축.

detector 원칙: 4개 observe-only / report-only. `stale_lock`과 `resource_usage`(disk-low)는 filesystem maintenance mutation 허용 (CLEANUP_ENABLED/ROTATE_ENABLED flag gated + dry_run excluded).

## 2. 파일 목록

### 신규 파일 (20개)

| # | 파일 | 설명 |
| --- | --- | --- |
| 1 | `src/engine/error_detectors/__init__.py` | 패키지 init |
| 2 | `src/engine/error_detectors/base.py` | `BaseDetector(dry_run)`, `DetectionResult`, `register_detector` |
| 3 | `src/engine/error_detector.py` | `ErrorDetectionEngine` (6 detectors, 6 modes) |
| 4 | `src/engine/error_detectors/process_health.py` | `ProcessHealthDetector`: TRADING_RULES timeout, PID + thread staleness, atomic write |
| 5 | `src/engine/error_detectors/cron_completion.py` | `CronCompletionDetector`: KST date filter, terminal marker priority, 15 cron jobs |
| 6 | `src/engine/error_detectors/log_scanner.py` | `LogScanner`: stateful scan + rotation reset, dry-run protection, TRADING_RULES config |
| 7 | `src/engine/error_detectors/artifact_freshness.py` | `ArtifactFreshnessDetector`: window_start/end, trading_day_only, 10 artifacts |
| 8 | `src/engine/error_detectors/resource_usage.py` | `ResourceUsageDetector`: CPU/mem/swap/disk/loadavg + sampler_age + disk-low auto log rotate |
| 9 | `src/engine/error_detectors/stale_lock.py` | `StaleLockDetector`: stale flock lock detection + dry-run guard + CLEANUP_ENABLED flag 자동 정리 (Phase 3) |
| 10 | `deploy/run_error_detection.sh` | Cron wrapper: flock lock, nice/ionice, START/DONE/FAIL 로깅 |
| 11 | `deploy/install_error_detection_cron.sh` | Cron installer |
| 12 | `src/tests/test_error_detector.py` | 12 tests: BaseDetector, registry, engine, report |
| 13 | `src/tests/test_error_detector_process_health.py` | 8 tests: heartbeat, stale detection |
| 14 | `src/tests/test_error_detector_cron_completion.py` | 9 tests: terminal marker priority, KST date filter |
| 15 | `src/tests/test_error_detector_log_scanner.py` | 10 tests: dry-run protection, rotation reset |
| 16 | `src/tests/test_error_detector_artifact_freshness.py` | 7 tests: window not_yet_due, trading_day skip, pass_after_window |
| 17 | `src/tests/test_error_detector_resource_usage.py` | 12 tests: classify, high_cpu/low_mem, sampler age, disk-low rotate cooldown |
| 18 | `src/tests/test_error_detector_stale_lock.py` | 5 tests: dry-run preserves, active lock protected, clean stale (Phase 3) |
| 19 | 삭제된 구현 설계서 | 당시 구현 설계서(원본 삭제) |
| 20 | `docs/code-reviews/system-error-detector-2026-05-09-implementation-review.md` | 이 코드리뷰 문서 |

### 수정 파일 (8개)

| # | 파일 | 변경 |
| --- | --- | --- |
| 1 | `src/bot_main.py` | heartbeat instrumentation (main_loop + all daemon threads), error detection daemon (TRADING_RULES interval/ENABLED), SYSTEM_HEALTH_ALERT dedup publish |
| 2 | `src/utils/constants.py` | 14개 ERROR_DETECTOR_* 상수 + 6개 env override (KORSTOCKSCAN_ERROR_DETECTOR_*) |
| 3 | `docs/time-based-operations-runbook.md` | error detection cron 행 + runbook check 연계 |
| 4 | `AGENTS.md` | §1.1 System Error Detector observe/report-only 축 |
| 5 | `src/notify/telegram_manager.py` | SYSTEM_HEALTH_ALERT handler + html.escape + telegram sidecar heartbeat |
| 6 | `src/engine/build_codex_daily_workorder.py` | INTRADAY + POSTCLOSE runbook check에 error_detection artifact 추가 |
| 7 | `src/scanners/scalping_scanner.py` | while 루프 상단 `write_heartbeat("scalping_scanner")` (장외 대기 중에도 갱신) (Phase 3) |
| 8 | `src/engine/kiwoom_sniper_v2.py` | while 루프 상단 `write_heartbeat("sniper_engine")` (Phase 3) |

## 3. 아키텍처

```
src/engine/error_detector.py          ErrorDetectionEngine (6 detectors, 6 modes)
    |
    +-- error_detectors/base.py         BaseDetector(dry_run), DetectionResult, register_detector
    |
    +-- error_detectors/process_health.py    ProcessHealthDetector
    |        reads: tmp/error_detector_heartbeat.json (atomic Lock + os.replace)
    |        heartbeat owners: main_loop, telegram, crisis_monitor, error_detection, scalping_scanner, sniper_engine
    |
    +-- error_detectors/cron_completion.py   CronCompletionDetector
    |        reads: logs/*.log (KST date filter, terminal marker priority)
    |
    +-- error_detectors/log_scanner.py       LogScanner
    |        reads: logs/*_error.log (stateful scan + rotation reset)
    |        config: TRADING_RULES.ERROR_DETECTOR_LOG_BURST_THRESHOLD / SCAN_MAX_LINES
    |
    +-- error_detectors/artifact_freshness.py  ArtifactFreshnessDetector
    |        reads: 10 artifacts (window_start/end, trading_day_only, pass_after_window)
    |
    +-- error_detectors/resource_usage.py      ResourceUsageDetector
    |        reads: system_metric_samples.jsonl + /proc + statvfs
    |        auto-recovery: disk < 2GB -> run_logs_rotation_cleanup_cron.sh (success-based 30min file cooldown)
    |
    +-- error_detectors/stale_lock.py          StaleLockDetector (Phase 3)
             reads: tmp/*.lock (fcntl non-blocking try)
             auto-clean: CLEANUP_ENABLED=true + dry_run=false -> os.remove() stale locks
```

### 통합 아키텍처

```
bot_main.py
  |
  +-- main loop (1s)                 write_heartbeat("main_loop") every 5s
  +-- telegram daemon                sidecar 30s -> write_heartbeat("telegram")
  +-- crisis_monitor daemon          write_heartbeat("crisis_monitor") every 3600s
  +-- error_detection daemon         write_heartbeat("error_detection") every cycle
  |       TRADING_RULES.ERROR_DETECTOR_ENABLED/DAEMON_INTERVAL_SEC gated
  |       fail -> EventBus SYSTEM_HEALTH_ALERT (dedup: 600s cooldown + hash change + transition)
  +-- scalping_scanner daemon        write_heartbeat("scalping_scanner") every cycle (Phase 3)
  +-- sniper_engine daemon           write_heartbeat("sniper_engine") every cycle (Phase 3)

cron: */5 * * * * deploy/run_error_detection.sh full -> ErrorDetectionEngine(dry_run=false)

EventBus: SYSTEM_HEALTH_ALERT -> telegram_manager (html.escape, admin HTML)
```

## 4. Detector별 동작 상세

### 4.1 ProcessHealthDetector

| 항목 | 상세 |
| --- | --- |
| 입력 | `tmp/error_detector_heartbeat.json` (threading.Lock + os.replace atomic write) |
| main loop | age > 15s -> fail, PID `/proc` 검증 |
| thread | age > 7200s -> fail (TRADING_RULES.ERROR_DETECTOR_PROCESS_THREAD_TIMEOUT_SEC) |
| heartbeat owners | main_loop(5s), telegram(30s sidecar), crisis_monitor(3600s), error_detection(60s), scalping_scanner(2-3min loop top), sniper_engine(1s loop top) |

### 4.2 CronCompletionDetector

| 항목 | 상세 |
| --- | --- |
| 입력 | 15 cron job log 최근 200줄, KST date 필터 (`target_date=` pattern) |
| once job | mixed [DONE]+[FAIL] 공존 시 `_last_terminal_marker()`로 최신 marker 우선 판정 |

### 4.3 LogScanner

| 항목 | 상세 |
| --- | --- |
| burst threshold | `TRADING_RULES.ERROR_DETECTOR_LOG_BURST_THRESHOLD` (default 4) |
| scan buffer | `TRADING_RULES.ERROR_DETECTOR_LOG_SCAN_MAX_LINES * 256` (default 2000) |
| log rotation | `last_pos < 0 or file_size < last_pos` -> position 0 reset |
| dry-run | state 파일 저장 skip |

### 4.4 ArtifactFreshnessDetector

| 항목 | 상세 |
| --- | --- |
| 비영업일 | `trading_day_only=True` + `is_krx_trading_day()`=False -> `skip_non_trading_day` |
| window 전 | `window_start` 전 -> `not_yet_due` |
| window 내 | `max_staleness_sec` 기준 stale 검사 |
| window 후 | 존재 -> `pass_after_window`, 미존재 -> fail |

### 4.5 ResourceUsageDetector

| 항목 | 상세 |
| --- | --- |
| sampler age | `epoch`/`ts` 기준 >20분 fail, >10분 warning |
| disk-low auto | disk < 2GB -> `run_logs_rotation_cleanup_cron.sh 7` 호출. 성공한 호출만 `tmp/error_detector_last_log_rotate_ts.txt`에 기록해 cron process 간 30min cooldown 유지 |

### 4.6 StaleLockDetector (Phase 3)

| 항목 | 상세 |
| --- | --- |
| 입력 | `tmp/*.lock` 파일, mtime 기준 age > `MAX_LOCK_AGE_SEC`(3600s) -> stale 판정 |
| dry-run | `would_clean`만 기록, 파일 삭제 안 함 |
| CLEANUP_ENABLED=False | `cannot_remove`만 기록, 삭제 안 함 |
| CLEANUP_ENABLED=True + live | `fcntl.LOCK_EX\|LOCK_NB` non-blocking lock try -> 성공 시 `os.remove()` |
| active lock | fcntl lock fail -> `cannot_remove`로 보고 (다른 프로세스 사용 중) |
| runtime_effect | **true: filesystem mutation 허용** (CLEANUP_ENABLED flag gated, dry_run excluded) |

## 5. 테스트 결과

### 5.1 전체 테스트 (85 passed)

| suite | count |
| --- | --- |
| error detector (7개 파일) | 64 passed |
| constants (9개) | 9 passed |
| build_codex_daily_workorder (12개) | 12 passed |
| **total** | **85 passed** |

### 5.2 파일별 커버리지

| 파일 | tests | 설명 |
| --- | --- | --- |
| `test_error_detector.py` | 12 | BaseDetector, registry, engine, report |
| `test_error_detector_process_health.py` | 8 | heartbeat write/read, stale detection |
| `test_error_detector_cron_completion.py` | 9 | terminal marker priority, KST date filter |
| `test_error_detector_log_scanner.py` | 10 | dry-run protection, rotation reset, state tracking |
| `test_error_detector_artifact_freshness.py` | 7 | window/trading_day/pass_after_window |
| `test_error_detector_resource_usage.py` | 12 | classify, high_cpu/low_mem, sampler age, rotate cooldown |
| `test_error_detector_stale_lock.py` | 5 | dry-run preserve, active lock protect, clean stale |
| `test_constants.py` | 9 | env override 포함 |
| `test_build_codex_daily_workorder.py` | 12 | runbook check 포함 |

## 6. mode filtering

```
mode=full:              6 detectors (all)
mode=health_only:       1 detector  (process_health)
mode=cron_only:         1 detector  (cron_completion)
mode=log_only:          1 detector  (log_scanner)
mode=artifact_only:     1 detector  (artifact_freshness)
mode=resource_only:     1 detector  (resource_usage)
```

## 7. env override

| env var | TRADING_RULES 필드 | default |
| --- | --- | --- |
| `KORSTOCKSCAN_ERROR_DETECTOR_ENABLED` | ENABLED | True |
| `KORSTOCKSCAN_ERROR_DETECTOR_DAEMON_INTERVAL_SEC` | DAEMON_INTERVAL_SEC | 60 |
| `KORSTOCKSCAN_ERROR_DETECTOR_RESOURCE_MAX_SAMPLE_AGE_SEC` | RESOURCE_MAX_SAMPLE_AGE | 600 |
| `KORSTOCKSCAN_ERROR_DETECTOR_STALE_LOCK_CLEANUP_ENABLED` | STALE_LOCK_CLEANUP_ENABLED | True |
| `KORSTOCKSCAN_ERROR_DETECTOR_STALE_LOCK_MAX_AGE_SEC` | STALE_LOCK_MAX_AGE | 3600 |
| `KORSTOCKSCAN_ERROR_DETECTOR_DISK_LOG_ROTATE_ENABLED` | DISK_LOG_ROTATE_ENABLED | True |

## 8. 운영 원칙 준수

| 원칙 | 준수 | 근거 |
| --- | --- | --- |
| report-only | 대부분 O | 4개 detector는 pure observe-only. stale_lock + resource_usage(disk-low)는 CLEANUP_ENABLED/ROTATE_ENABLED flag gated filesystem mutation |
| 자동 복구 제한 | O | stale lock cleanup + disk-low log rotate. trading threshold/strategy/주문 변경 없음 |
| runtime_effect | 예외 있음 | stale_lock: filesystem (flag+dry_run gated), resource_usage: subprocess log rotate (flag+dry_run gated, file cooldown) |
| 확장성 | O | 6 detectors auto-discovered via @register_detector |
| env override | O | 6개 ERROR_DETECTOR_* env var -> TRADING_RULES |

## 9. 잔여 작업

- [ ] Telegram polling service health 감시 (현재 sidecar heartbeat는 module liveness proxy) - Phase 3 observation
- [ ] `error_detection` thread crash 시 auto-restart - Phase 3 observation

## 10. 승인 기준

- [x] 64 error detector + 21 regression = **85 passed**
- [x] bash syntax, py_compile all OK
- [x] `git diff --check` whitespace clean
- [x] dry-run: detector_count=6, production 로그 탐지
- [x] dry-run stale lock deletion 방지 검증 완료 (would_clean report only)
- [x] CLEANUP_ENABLED=False env override 검증 완료
- [x] Telegram alert (html.escape + dedup 600s cooldown)
- [x] bot_main.py daemon integration (TRADING_RULES gated)
- [x] build_codex_daily_workorder runbook check 통합
- [x] 6개 env override 연결 + stale_lock CLEANUP_ENABLED/MAX_AGE + disk log rotate env override
- [x] scalper/sniper heartbeat instrumentation (loop top, 장외 대기 중에도 갱신)
- [x] disk-low auto log rotate (30min cooldown)
- [ ] runtime 대기: 다음 장중 cron 실행 후 Sentinel 분류와 중복되지 않는지 확인

---

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
- `src/utils/*`:
  - `src.engine` 장기 패키지와 경계가 겹치는 파일이 있지만, 현재 `src/engine`, `src/scanners`, `src/notify`, `src/core`가 광범위하게 소비하는 shared surface다.
  - 별도 `UtilsBoundaryAudit` inventory 없이 이동하지 않는다.
  - `constants.py`, `logger.py`, `kiwoom_utils.py`는 영향 범위가 커서 초기 slice 대상이 아니다.
  - `pipeline_event_logger.py`, `threshold_cycle_registry.py`, `runtime_flags.py`, `update_kospi.py`는 장기 경계 재배치 후보지만 wrapper와 consumer migration gate가 필요하다.

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

## Phase 2 Slice 2 Candidate: monitoring sampler

2026-05-26 POSTCLOSE 판정은 `monitoring_sampler_slice_selected`다. 다음 safe slice 후보는 `src.engine.system_metric_sampler`를 `src.engine.monitoring.system_metric_sampler`로 옮기는 monitoring/infra 성격 slice다.

2026-05-27 intraday 보정: 같은 날 `greenfield_real_environment_authority`가 real `entry/submit/holding/scale_in/exit` authority와 PREOPEN env bridge를 추가했으므로, 2026-05-27에는 실제 파일 이동을 진행하지 않는다. 오늘 작업 범위는 Greenfield Real Environment 이후 refactor blast-radius와 consumer inventory를 문서로 보정하는 데 한정한다. `system_metric_sampler` 이동은 다음 영업일 이후 `greenfield_real_environment_authority` postclose/preopen 산출물과 runtime event provenance가 안정적으로 확인된 뒤 다시 safe slice로 연다.

범위:

- new canonical path: `src.engine.monitoring.system_metric_sampler`
- old path compatibility: `src.engine.system_metric_sampler` wrapper 유지
- old CLI compatibility: `python -m src.engine.system_metric_sampler` 유지
- new CLI smoke: `python -m src.engine.monitoring.system_metric_sampler` 확인

구현 전 gate:

1. 2026-05-27에는 구현하지 않고, consumer inventory와 risk note만 보강한다.
2. 실제 이동을 재개하기 전 deploy/cron/error detector/test import 경로를 다시 수집한다.
3. cron/job id, output path, JSON schema, sampler interval, resource metrics 의미를 바꾸지 않는다.
4. runtime/order/provider/threshold/bot restart 경로 및 Greenfield Real Environment authority/env/policy/Telegram 경로와 연결하지 않는다.
5. 구현 재개 시 old/new import smoke, old/new CLI smoke, targeted monitoring tests, parser, `git diff --check`를 실행한다.

개선된 실행 단계:

1. `greenfield_uptake_verified`
   - 2026-05-28 PREOPEN 이후 `runtime_apply_gap_audit` retry queue에서 `greenfield_real_environment_authority`와 `entry_wait6579_score66_69_recovery_gate_v1`가 해소됐는지 먼저 확인한다.
   - 둘 중 하나라도 `ready_but_not_applied`, `retry_pending`, `post_apply_attribution_pending`으로 남아 있으면 `defer_after_greenfield_verification`으로 닫고 파일 이동을 하지 않는다.
2. `consumer_inventory_refreshed`
   - `system_metric_sampler` consumer를 `deploy/cron`, `error_detector`, `backfill`, `tests`, `runbook`으로 분류한다.
   - 각 consumer는 `wrapper로 유지`, `canonical import 전환 후보`, `문서 reference only` 중 하나로 태깅한다.
   - 이 단계는 계획/문서 보강이며 source file 이동, deploy rewrite, cron 재설치는 하지 않는다.
3. `implement_monitoring_sampler_slice`
   - `src.engine.monitoring.system_metric_sampler`를 canonical path로 만들고 기존 `src.engine.system_metric_sampler`는 compatibility wrapper로 유지한다.
   - old import smoke, new import smoke, old CLI smoke, new CLI smoke를 같은 slice에서 닫는다.
   - root wrapper 제거와 consumer canonical import 전환은 이 slice의 필수 범위가 아니라 후속 migration 후보로 남긴다.

불변 계약:

- cron id `system_metric_sampler`, cron comment `SYSTEM_METRIC_SAMPLER_1MIN`, wrapper log marker `[START] system_metric_sampler` / `[DONE] system_metric_sampler`를 유지한다.
- output path `logs/system_metric_samples.jsonl`, state path `tmp/system_metric_sampler_state.json`, lock path `tmp/system_metric_samples.lock`를 유지한다.
- CPU affinity env `SYSTEM_METRIC_SAMPLER_CPU_AFFINITY`, sampler interval, JSONL schema, resource metric semantics를 변경하지 않는다.
- `sample_once()`와 `main()` public surface는 old root wrapper와 new canonical module 양쪽에서 import 가능해야 한다.

consumer inventory 기준표:

| Consumer | 처리방식 | 보강 기준 |
| --- | --- | --- |
| `deploy/run_system_metric_sampler_cron.sh` | `wrapper로 유지` | old CLI `python -m src.engine.system_metric_sampler`를 계속 실행한다. cron schedule, marker, log path 변경 금지 |
| `deploy/install_stage2_ops_cron.sh` | `문서/reference only` | cron comment `SYSTEM_METRIC_SAMPLER_1MIN`와 1분 주기 설치 계약 유지 |
| `src/engine/backfill_threshold_cycle_events.py` | `canonical import 전환 후보` | 초기 slice에서는 wrapper import로 동작 유지. canonical import 전환은 별도 consumer migration에서 수행 |
| `src/engine/error_detectors/cron_completion.py` | `wrapper로 유지` | job id/log contract 유지. detector registry 의미 변경 금지 |
| `src/tests/test_engine_location_gate.py` | `wrapper로 유지` | root wrapper가 남는 동안 allowlist 제거 금지. wrapper 제거는 Phase Final에서만 검토 |
| `src/tests/test_error_detector_coverage.py` | `문서/reference only` | required cron job id `system_metric_sampler` 유지 확인 |
| `docs/time-based-operations-runbook.md` | `문서 reference only` | 경로보다 산출물, marker, resource_usage 입력 계약 중심으로 유지 |

재개/보류 판정값:

| 판정값 | 의미 | 다음 액션 |
| --- | --- | --- |
| `greenfield_retry_pending` | Greenfield/preopen uptake retry가 남아 monitoring sampler 이동 원인 분리가 어려움 | 파일 이동 금지, 다음 PREOPEN/POSTCLOSE 산출물로 재확인 |
| `consumer_inventory_refreshed` | 이동 전 consumer 목록과 처리방식이 확정됨 | 구현 slice 여부를 다음 checklist에서 결정 |
| `monitoring_sampler_slice_ready` | Greenfield uptake와 consumer inventory gate가 모두 닫힘 | canonical module + wrapper 구현 가능 |
| `implemented_with_wrapper` | canonical 이동 완료, old wrapper 유지, old/new smoke 통과 | 최소 1회 preopen/postclose 안정 검증 후 consumer migration 검토 |
| `blocked_by_runtime_path` | runtime/order/provider/bot/threshold 경로와 충돌 | refactor slice 보류, 별도 workorder로 분리 |

2026-05-27 문서 보강 체크:

- `greenfield_real_environment_authority`는 `src.engine.lifecycle`, `runtime_apply_bridge`, `threshold_cycle_preopen_apply`, `sniper_state_handlers` runtime hot path를 건드린다. 같은 날 `src.engine` 파일 이동을 겹치지 않는다.
- monitoring sampler 이동은 report/monitoring infra slice지만, detector/resource warning 산출물이 장중 운영 판단과 연결되므로 Greenfield post-apply verification과 같은 검증 창에서 섞지 않는다.
- 다음 재개 시 checklist 항목은 `implement_monitoring_sampler_slice`가 아니라 먼저 `consumer_inventory_refreshed` 또는 `defer_after_greenfield_verification`으로 닫는다.

2026-05-27 POSTCLOSE 보강 판정:

- 판정: `document_plan_updated_defer_after_greenfield_verification`.
- 근거: 당일 postclose verifier는 `pass`지만 `runtime_apply_gap_audit`에 `greenfield_real_environment_authority:2026-05-27`와 `entry_wait6579_score66_69_recovery_gate_v1:2026-05-27`의 다음 PREOPEN uptake retry가 남았다. 이 상태에서 `system_metric_sampler` 파일 이동을 같은 날짜에 겹치면 monitoring warning과 Greenfield uptake 경고의 원인 분리가 흐려진다.
- 다음 액션: 2026-05-28 이후 먼저 deploy/cron/error detector/test import consumer inventory를 refresh하고, old/new import smoke와 old/new CLI smoke plan을 만든 뒤 실제 이동 여부를 다시 판단한다. 그 전에는 wrapper 제거, cron/job id 변경, output path/JSON schema/metric semantics 변경, runtime/order/provider/bot 경로 이동을 하지 않는다.

2026-05-29 POSTCLOSE 보강 판정:

- 판정: `plan_supplemented_no_new_safe_slice`.
- 근거: [codebase_performance_workorder_2026-05-29.json](/home/ubuntu/KORStockScan/data/report/codebase_performance_workorder/codebase_performance_workorder_2026-05-29.json)은 accepted `7`, implemented `7`, pending accepted `0`, deferred `3`, rejected `2`로 닫혔다. 당일 코드 보강은 lifecycle bucket discovery, observation/source-quality, runtime apply gap audit, postclose verifier의 instrumentation/report/provenance 계약 보강이며 runtime/order/provider/threshold/bot path 이동이 아니다. [runtime_apply_gap_audit_2026-05-29.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-05-29.json)은 `codex_directive_count=0`, `critical_failure_count=0`이지만 retry queue `1`과 `status=warning`을 남겼고, error detector health-only warning은 의도적 postclose bot isolation이다.
- 다음 액션: `system_metric_sampler`와 관련 report-only safe-slice 이동은 계속 보류한다. 다음 재개 전에는 deploy/cron/error detector/test import consumer inventory, old/new import smoke, old/new CLI smoke plan을 먼저 작성한다. 그 전에는 wrapper 제거, cron/job id 변경, output path/JSON schema/metric semantics 변경, runtime/order/provider/bot 경로 이동을 하지 않는다.

보류:

- `src.utils.threshold_cycle_registry -> src.engine.automation.threshold_cycle_registry`는 `UtilsBoundaryAudit` 이후 검토한다.
- `src/trading -> src.engine.scalping`은 runtime entry/order hot path이므로 별도 `TradingToScalping` inventory와 pure type/util slice 검증 전 이동하지 않는다.

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

## Long-Running Track: src/utils boundary audit

`src/utils`는 공통 기반 모듈이지만 일부 파일은 `src.engine` 장기 패키지 경계와 겹친다. 이 트랙은 `src/utils`를 통째로 없애는 작업이 아니라, shared primitive와 engine-owned automation/infrastructure를 분리하는 장기 inventory다.

현재 판정:

- 유지 적합 shared primitive:
  - `src.utils.jsonl_io`: gzip/jsonl 파일 IO helper. automation/monitoring/report 전반에서 재사용한다.
  - `src.utils.market_day`: KRX calendar helper. automation/monitoring/checklist sync가 공통 소비한다.
  - `src.utils.constants`: 경로/DB URL/TradingConfig의 central surface라 영향 범위가 매우 크다. 별도 config refactor 전까지 유지한다.
  - `src.utils.logger`: 전역 logging surface라 영향 범위가 크다. log archive/monitoring과 겹치지만 초기 이동 금지다.
- 장기 이동 후보:
  - `src.utils.pipeline_event_logger` -> `src.engine.automation` 또는 `src.engine.infrastructure`
  - `src.utils.threshold_cycle_registry` -> `src.engine.automation`
  - `src.utils.runtime_flags` -> `src.engine.infrastructure` 또는 `src.core`
  - `src.utils.update_kospi` -> `src.engine.infrastructure`
  - `src.utils.migrate_scale_in_fields` -> migration/archive 정리 후보
- 후순위 대형 후보:
  - `src.utils.kiwoom_utils` -> `src.engine.infrastructure.kiwoom` 후보지만 scanners/notify/scalping/runtime 소비자가 많아 별도 inventory 전 이동 금지다.

진행 조건:

1. `rg` inventory로 `src.utils.*` consumer를 파일별로 수집한다.
2. 각 후보가 shared primitive인지 engine-owned automation/infrastructure인지 판정한다.
3. pure registry/helper slice만 먼저 검토한다. 1차 후보는 `threshold_cycle_registry.py`다.
4. 이동 시 기존 `src.utils.<module>` wrapper를 유지하고, canonical path consumer migration은 안정화된 slice만 점진 진행한다.
5. `constants.py`, `logger.py`, `kiwoom_utils.py`는 별도 proof와 넓은 targeted test 전까지 이동하지 않는다.

금지선:

- `src/utils` 전체 일괄 이동 또는 direct import rewrite를 금지한다.
- runtime threshold, provider route, broker submit, order qty/cooldown/stale quote, bot restart, config/env 로딩 semantics를 변경하지 않는다.
- `src.engine`과 `src.utils` 사이의 순환 import를 새로 만들지 않는다.
- wrapper 제거는 최소 한 번의 preopen/postclose 안정 검증 이후 Phase Final gate에서만 검토한다.

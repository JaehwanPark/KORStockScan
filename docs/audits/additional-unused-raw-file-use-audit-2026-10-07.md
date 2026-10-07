# 추가 미사용 raw 사용처 조사 — 2026-10-07

## 1. 범위와 관측 시점

[추가 삭제 계획](../proposals/additional-unused-raw-file-deletion-plan-2026-10-07.md)의 근거 기록이다. 기존 삭제의 완료를 [실행 영수증](../../data/report/pre_september_source_retirement/2026-10-07/execution-result.json)과 [실행 문서](pre-september-source-data-retirement-execution-2026-10-07.md)로 확인한 뒤 남은 파일을 조사했다.

- 물리 inventory 시각 **10/7 10:49:36 KST**. workspace data/tmp와 프로젝트 관련 외부 보관·release/worktree 경로를 metadata로 열거하고 symlink 디렉터리는 추적하지 않았다. `.git`, `.venv`, node_modules, source/docs 등은 raw 파일 census에서 제외했다. 코드 사용처는 별도 검색했다.
- inode 중복 제거 후 **72,389파일 / 74.624GiB**, 열거 오류 0. 이는 조사한 일반 파일 총량이며 raw·미사용·회수 가능 총량이 아니다. DB 파일이 발견되어도 삭제 후보로 포함하지 않았다. `/home` 전체나 원격 저장소까지 전수 분류했다는 의미가 아니다.
- source/consumer 대조 시각 **10:52:27 KST**. 선택 릴리스는 `episode-startup-observability-20261007-v4`, 실제 PID 777785의 cwd는 그 릴리스의 `src`, UID 1000이다. 8개 핵심 reader의 workspace/selected hash가 일치했다. 다른 dirty 코드 전체의 일치나 미래 소비까지 보증하지 않는다.
- 최초 파일 inventory 뒤 runtime이 계속 쓰므로 적용 시 목록·hash·보존 의존성·열린 파일을 재고정한다.

## 2. 물리·기간 조사 결과

| 자료 | 확인 방법 | 결과·한계 |
|---|---|---|
| 전체 파일 inventory | `lstat`, inode 중복 제거, path별 할당량 | [physical-summary](../../tmp/additional-unused-raw-audit-20261007/physical-summary.json), [파일 목록](../../tmp/additional-unused-raw-audit-20261007/physical-file-inventory.jsonl). 파일명 날짜는 후보 발견용 |
| Parquet | pyarrow footer/schema metadata, row-group 시계 min/max·null·누락 통계 | [49파일 footer](../../tmp/additional-unused-raw-audit-20261007/parquet-clock-footer-census.json). 후보 39파일 6,336,400행, 9/1~28. 실제 row-query·운영 DB 접속 없음 |
| 격리 backup 16개·threshold snapshot 5개 | 파일당 최대 64행, line/전체 읽기 상한을 둔 gzip 표본 | [gzip 표본](../../tmp/additional-unused-raw-audit-20261007/gzip-payload-samples.json). 표본 날짜·원천 key 확인. `full_payload_verified=false`; 전체 CRC/내용 hash 미검증 |
| sentinel | family·대상일 파일 census와 reader 경로 확인 | 9/1~28 raw 34개 0.301GiB. `.meta.json`은 합계에서 제외. 파일명 날짜는 아직 전체 payload 기간 증명이 아님 |
| 혼합 widget archive | tar member header 목록, 분류·크기 | [member census](../../tmp/additional-unused-raw-audit-20261007/mixed-widget-archive-member-census.json). 2,205 member, archive 53.656MiB. nonraw 보존 필요, archive 추출·변경 없음 |
| 기존 보호 집합 | 이전 삭제 before receipt의 3,101개 경로와 후보 대조 | [후보·보호 겹침](../../tmp/additional-unused-raw-audit-20261007/candidate-file-groups.json): 0. 신규 연구의 보호 집합 갱신은 적용 전 별도 필요 |

후보 94개의 합계는 **22.791992GiB**다. 원본과 복구 사본, Parquet와 JSONL은 서로 다른 inode면 각각 물리 공간을 차지하지만 현재 유효 데이터 삭제 권한은 사본별 사용처로 따로 판정한다.

## 3. 실제 reader 확인

### 격리 복구 사본

- [observation_source_quality_audit.py](../../src/engine/observation_source_quality_audit.py) `_raw_row_exclusion_paths`, `_exclude_hard_blocking_rows_from_raw`: backup 생성과 manifest 발행.
- 같은 파일 `_existing_applied_raw_row_exclusion`: 이전 report와 manifest를 읽고 적용 여부를 판단. `backup_path`는 존재하는 문자열인지 확인하며 백업 파일 본문/exists는 조회하지 않음.
- [source_quality_hard_gate.py](../../src/engine/automation/source_quality_hard_gate.py) `_compact_raw_row_exclusion`: backup 경로를 metadata로 전달. `_archive_matches_source/_archived_raw_digest`가 읽는 것은 canonical 압축 raw의 별도 source-generation 검증임.
- [build_code_improvement_workorder.py](../../src/engine/build_code_improvement_workorder.py) `_raw_row_exclusion_with_manifest_details`, `_manifest_excluded_rows`: manifest의 격리 원인/행을 읽음.
- `src/engine`·`deploy`의 `backup_path` 검색에서 이 exclusion 백업을 정책 입력으로 여는 경로는 발견하지 못했다. 별도의 `pipeline_event_summary`의 동일 변수명은 summary 원자 교체용으로 다른 파일이다.
- [cleanup wrapper](../../deploy/run_logs_rotation_cleanup_cron.sh)의 오래된 사본 분기는 `DELETE_DEFERRED disabled_pending_storage_owner`를 출력한다. 기존 7일 조건은 자동 삭제가 없다는 근거이며 영구 사용 필요성의 근거가 아니다.

### Parquet

- [compare_tuning_shadow_diff.py](../../src/engine/compare_tuning_shadow_diff.py) `_count_duckdb_metrics`가 pipeline_events/post_sell dataset을 기본 등록한 후 날짜 WHERE를 적용한다.
- [tuning_duckdb_repository.py](../../src/engine/tuning_duckdb_repository.py) `register_parquet_dataset`: 기본 `date=*/*.parquet`, `union_by_name=true`. 범위 밖 파일의 schema/view 참여가 남아 있다.
- [tuning wrapper](../../deploy/run_tuning_monitoring_postclose.sh)는 3 dataset을 target일 단독 생산하고 기본 3달력일 비교를 실행한다. `ubuntu crontab`의 `TUNING_MONITORING_POSTCLOSE`가 평일 20:10에 release router의 `tuning`으로 예약돼 있다.
- [10/6 status](../../data/report/tuning_monitoring/status/tuning_monitoring_postclose_2026-10-06.json): 10/7 04:15:46 완료, start `2026-10-04`, target `2026-10-06`, 비교 성공. 이는 당시 릴리스 `continuous-reversal-20261007-v8`의 실행 근거다. 오늘 선택 릴리스의 핵심 reader hash 일치는 [대조 기록](../../tmp/additional-unused-raw-audit-20261007/consumer-code-and-selection.json)에서 별도 확인했다.
- [남기는 schema 확인](../../tmp/additional-unused-raw-audit-20261007/candidate-summary.json): 9/29 이후 pipeline 4파일의 합집합에 필요한 4필드 존재. 결과 parity는 아직 실행하지 않았다.

### threshold snapshot — 자체 리뷰에서 발견한 간접 사용

ADM report builder/CLI가 retired라는 사실만 확인하면 5개 gzip을 오분류할 수 있다. [entry_observation_source.py](../../src/engine/scalping/entry_observation_source.py)가 옛 모듈의 `_iter_relevant_events()`를 사용하고, 이 함수는 `_event_paths()`의 snapshot을 실제로 연다.

호출자는 [entry_context_intraday_probe.py](../../src/engine/scalping/entry_context_intraday_probe.py) `_read_adm_report`와 [entry_ai_gate_backtest.py](../../src/engine/scalping/entry_ai_gate_backtest.py) `build_report`다. 후자는 명시 start/end를 지원한다. 정규 wrapper에서는 `ENTRY_AI_GATE_BACKTEST_SCHEDULE=on_demand`, `RUN_ENTRY_AI_GATE_BACKTEST=false`이며 진단 실행을 skip한다. **현재 9/11~17의 자동 소비를 확인한 것은 아니며 현재 작업·연구의 요청 날짜를 확인할 후보로 분류했다.** 과거 수동 재현 가능성만으로 보존 의무나 reader 수정 조건을 만들지 않는다.

### sentinel 및 그 밖의 보존 원천

- [sentinel_event_cache.py](../../src/engine/sentinel_event_cache.py): 현재 target일 raw/cache generation 사용. [intraday_entry_flow_report.py](../../src/engine/monitoring/intraday_entry_flow_report.py)의 비압축 raw 부재 fallback 때문에 과거 cache 소비를 따로 확인해야 한다.
- [scalping_avg_down_recovery_calibration.py](../../src/engine/monitoring/scalping_avg_down_recovery_calibration.py) `_iter_events_paths_for_window`: clean baseline 이후 실제 존재하는 pipeline base/late 파일을 누적 읽음. 9월 canonical 원천은 추가 후보에서 제외했다.
- [continuous_reversal_source.py](../../src/engine/scalping/continuous_reversal_source.py)와 [삼성 병행 정책 계획 §8.3](../proposals/main-multi-policy-parallel-entry-and-samsung-shallow-pullback-implementation-plan-2026-10-07.md#83-cache와-원천-유지): 현재 frozen market source/event/bars와 연구 후보/정의 연결. research tmp를 일괄 삭제하지 않는다.
- 남은 sim post-sell에는 [entry_split_order_plan.py](../../src/engine/scalping/entry_split_order_plan.py) `_load_sim_ev_values`, [time_window_regime_counterfactual.py](../../src/engine/automation/time_window_regime_counterfactual.py) `_available_sim_dates`, [producer_gap_discovery.py](../../src/engine/automation/producer_gap_discovery.py)의 동적 날짜/helper가 있다. helper 존재와 현재 실제 창을 구분하여 후속 분류한다.

## 4. 검토 결과와 미실행 항목

1차 검토에서 snapshot의 간접 reader와 Parquet의 실제 예약 소비를 재확인하여 단순 미사용 분류를 보완했다. 2차 검토는 DB·보고서·정책·잠금 보존, 후보/확정량 구분, 현행 9월 누적 원천과 연구 입력 보존, 기존 삭제기 v1 적용 불가, raw 복원/새 백업 요구 없음에 집중했다.

계획용 근거 JSON과 위 문서 외의 코드는 수정하지 않았다. 파일 삭제, 기존 삭제기 dry-run/apply, full gzip 재생, DB query/변경, 정책/보고서 재생성, API/provider 호출, 배포·기동·외부 동기화를 실행하지 않았다. 문서 링크·owner·권한 검토, print-only parser와 diff 검사는 통과했다. 코드 회귀·실제 삭제/native 검증은 계획 §5 실행 단계의 후속 수용 조건으로 남긴다.

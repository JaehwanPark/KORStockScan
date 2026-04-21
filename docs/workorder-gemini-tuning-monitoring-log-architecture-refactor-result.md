# 튜닝 모니터링 로그 아키텍처 재설계 개선작업 결과 보고서 (재검토 반영)

**작업일**: 2026-04-21  
**작업자**: Codex (GPT-5)  
**참조**: [작업지시서](./workorder-gemini-tuning-monitoring-log-architecture-refactor.md)

---

## 1. 판정

1. **운영 전환 조건 충족 (완료)** — `원본 jsonl 보관 + parquet/DuckDB 분석 + PostgreSQL 메타` 구조로 전환했고, 과거 누적 구간(요청 범위 `2026-04-01~2026-04-20`)에 대해 Raw 대비 Parquet 커버리지를 0 누락으로 맞췄다.
2. **분석랩 2종 전환 완료** — Gemini/Claude 분석랩 모두 DuckDB 우선 경로로 동작하며, `run_manifest`에 `data_source_mode/history_coverage_*`가 기록된다.
3. **Shadow diff 합격** — `trade_count`, `funnel`, blocker 4축, `full/partial`, `missed_upside` 정수 집계가 JSONL 대비 DuckDB 0 오차로 일치했다.
4. **Legacy DB raw 테이블 제거 완료** — `dashboard_pipeline_events`, `dashboard_monitor_snapshots`를 실제 삭제했고, 삭제 후 분석랩 스모크를 재실행해 정상 동작을 확인했다.

**최종 평가**: 작업지시서의 필수 완료조건(백필, 분석랩 검증, shadow diff, legacy 제거)을 충족했으므로 **완료 승인 가능**.

---

## 2. 근거

### 2-1. 구현/수정 핵심

1. 대용량 백필 OOM 원인(`json_normalize` 전컬럼 평탄화)을 제거하고, 경량 스키마(`필수 컬럼 + 선택 fields_* + fields_json`)로 변환 파이프라인을 수정했다.
2. Parquet 뷰 등록 시 `union_by_name=true`를 적용해 파티션 간 스키마 차이로 발생하던 DuckDB cast 오류를 제거했다.
3. 분석랩에서 legacy DB fallback을 제거해 운영 canonical source를 `parquet/DuckDB + jsonl fallback`으로 고정했다.
4. Gemini 결과서 생성 단계(`generate_final_report.py`)가 `run_manifest`를 덮어쓰던 문제를 수정해 `data_source_mode/history_coverage_*`가 최종 산출물에 보존되게 했다.

### 2-2. 데이터 커버리지 (Raw vs Parquet)

출처: `data/analytics/coverage_summary.json` (생성시각: 2026-04-21 07:15 KST)

| 데이터셋 | Raw 날짜 수 | Parquet 날짜 수 | missing_in_parquet | extra_in_parquet |
|---|---:|---:|---|---|
| pipeline_events | 8 | 8 | 0 | 0 |
| post_sell(evaluations) | 8 | 8 | 0 | 0 |
| system_metric_samples (`<=2026-04-20`) | 1 | 1 | 0 | 0 |

### 2-3. Shadow diff 핵심 수치 (JSONL vs DuckDB)

출처: `data/analytics/shadow_diff_summary.json` (`2026-04-01~2026-04-20`)

| 지표 | JSONL | DuckDB | 차이 |
|---|---:|---:|---:|
| trade_count | 65 | 65 | 0 |
| completed_count | 65 | 65 | 0 |
| missed_upside | 44 | 44 | 0 |
| latency_guard miss | 19,420 | 19,420 | 0 |
| liquidity_gate miss | 13,498 | 13,498 | 0 |
| AI threshold miss | 1,039,632 | 1,039,632 | 0 |
| overbought_gate miss | 512,748 | 512,748 | 0 |
| submitted_events | 188 | 188 | 0 |
| full_fill_count | 90 | 90 | 0 |
| partial_fill_count | 220 | 220 | 0 |

판정: **all_match=true (합격)**

### 2-4. 분석랩 2종 실행 결과

1. Gemini (`analysis/gemini_scalping_pattern_lab/run.sh`) 정상 완료
   - Health check: `duckdb/pipeline_events rows=2857648`
   - `run_manifest.json`:
     - `data_source_mode=duckdb_primary`
     - `history_coverage_ok=true`
2. Claude (`analysis/claude_scalping_pattern_lab/run_all.sh`) 정상 완료
   - Health check: `duckdb/pipeline_events rows=2857648`
   - `run_manifest.json`:
     - `data_source_mode=duckdb_primary`
     - `history_coverage_ok=true`

### 2-5. Legacy 제거 결과

실행 명령:

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.decommission_legacy_dashboard_tables --execute --yes
```

삭제 결과:

- `dashboard_pipeline_events`: 2,857,696행 삭제
- `dashboard_monitor_snapshots`: 60행 삭제

사후 확인(`--dry-run`): 두 테이블 모두 **존재하지 않음**.

---

## 3. 다음 액션

- [x] `[DataArch0421] POSTCLOSE 증분 운영 루틴(cron/workflow) 고정` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 18:00~18:20`, `Track: Plan`) (`실행: 2026-04-21 07:48 KST`)
  - 실행 순서: `build_tuning_monitoring_parquet(single-date) -> compare_tuning_shadow_diff(최근 1~3영업일) -> gemini run.sh -> claude run_all.sh`
  - 판정: 완료. `deploy/run_tuning_monitoring_postclose.sh`, `deploy/install_tuning_monitoring_postclose_cron.sh` 추가 및 crontab `TUNING_MONITORING_POSTCLOSE` 등록 완료.
- [x] `[DataArch0421] 회귀 테스트 보강(post_sell candidates 혼입 방지 + stale partition 정리)` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 18:20~18:35`, `Track: Plan`) (`실행: 2026-04-21 07:48 KST`)
  - 판정 기준: `post_sell_evaluations`만 Parquet 적재되고, no-file 날짜에서 기존 파티션이 제거되는 테스트가 CI에서 통과.
  - 판정: 완료. `test_process_single_date_post_sell_ignores_candidates`, `test_process_single_date_removes_stale_partition` 추가.
- [x] `[DataArch0421] 분석랩 legacy DB fallback 재유입 방지 테스트 추가` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 18:35~18:45`, `Track: Plan`) (`실행: 2026-04-21 07:48 KST`)
  - 판정 기준: legacy raw 테이블이 없어도 Gemini/Claude 랩 실행이 실패하지 않고 `duckdb_primary/jsonl_fallback`만 사용.
  - 판정: 완료. `KORSTOCKSCAN_ENABLE_LEGACY_DASHBOARD_DB` 미설정 시 legacy raw DB 테이블 생성/쓰기/읽기를 기본 비활성화하고 회귀 테스트를 추가.
- [x] `[DataArch0421] 운영 체크리스트에 coverage/shadow/manifest 증적 고정` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 18:45~18:55`, `Track: Plan`) (`실행: 2026-04-21 07:48 KST`)
  - 첨부 대상: `data/analytics/coverage_summary.json`, `data/analytics/shadow_diff_summary.json`, 양 분석랩 `run_manifest.json`.
  - 판정: 완료. 본 결과서와 `2026-04-22` 체크리스트에 증적/후속 확인 항목 고정.

## 4. 잔여 운영 워크오더

- [ ] `[DataArch0422] TUNING_MONITORING_POSTCLOSE 첫 자동실행 결과 확인` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 18:20~18:35`, `Track: Plan`)
  - 판정 기준: `logs/tuning_monitoring_postclose_cron.log`에서 `build_tuning_monitoring_parquet`, `compare_tuning_shadow_diff all_match=true`, Gemini/Claude `run_manifest history_coverage_ok=true` 확인.
  - 2026-04-21 사전 확인: `18:05 KST` cron은 `pipeline_events` parquet 생성 중 OOM kill로 실패했다. 원인은 459MB급 당일 JSONL 원본 이벤트를 모두 메모리에 보관한 뒤 DataFrame 변환하는 구조였다.
  - 2026-04-21 보수/복구: `pipeline_events` 처리 시 원본 이벤트를 즉시 분석용 축소 row로 변환하도록 수정하고 `deploy/run_tuning_monitoring_postclose.sh 2026-04-21`를 수동 재실행했다.
  - 2026-04-21 복구 결과: `pipeline_events=421,220 rows`, `post_sell=9 rows`, `system_metric_samples=802 rows`, shadow diff `all_match=true`, Gemini/Claude `data_source_mode=duckdb_primary`, `history_coverage_ok=true`.
  - 잔여 확인: 2026-04-22 POSTCLOSE의 첫 정상 자동실행 로그 확인은 유지한다.
- [ ] `[DataArch0422] monitor snapshot raw 압축/보존 정책 재판정` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 18:35~18:45`, `Track: Plan`)
  - 판정 기준: legacy raw DB 제거 후 `dashboard_db_archive`의 snapshot `skipped_unverified`를 허용할지, parquet/별도 manifest 검증으로 압축할지 결정.

## 5. Cron 정리 결과

- [x] `[DataArch0421] 중복/불필요 cron 정리` (`Due: 2026-04-21`, `Slot: PREOPEN`, `TimeWindow: 07:50~08:00`, `Track: Plan`) (`실행: 2026-04-21 07:52 KST`)
  - 판정: 완료. `TUNING_MONITORING_POSTCLOSE`가 Gemini/Claude 분석랩을 매일 포함 실행하므로 기존 금요일 `PATTERN_LAB_CLAUDE_FRI_POSTCLOSE`, `PATTERN_LAB_GEMINI_FRI_POSTCLOSE` cron을 제거.
  - 재유입 방지: `deploy/install_pattern_lab_cron.sh`를 기존 주간 분석랩 cron 제거용 cleanup shim으로 전환.
  - 정리 대상: 오래된 1회성 실행 주석 2개, 중복 `WATCHING 75 shadow canary checks` 주석 1개, 중복 `stage2 ops cron` 주석 1개.
  - 유지 대상: 장전 scanner/bot, buy pause guard, WATCHING shadow canary, system metric sampler, remote latency/fetch, monitor snapshot, dashboard archive, log cleanup, `TUNING_MONITORING_POSTCLOSE`.

---

## 변경 파일 목록 (이번 턴 반영분)

### 신규

1. `src/engine/compare_tuning_shadow_diff.py`
2. `deploy/run_tuning_monitoring_postclose.sh`
3. `deploy/install_tuning_monitoring_postclose_cron.sh`

### 주요 수정

1. `src/engine/build_tuning_monitoring_parquet.py`
2. `src/engine/tuning_duckdb_repository.py`
3. `src/engine/decommission_legacy_dashboard_tables.py`
4. `analysis/gemini_scalping_pattern_lab/build_dataset.py`
5. `analysis/gemini_scalping_pattern_lab/run.sh`
6. `analysis/gemini_scalping_pattern_lab/generate_final_report.py`
7. `analysis/claude_scalping_pattern_lab/prepare_dataset.py`
8. `analysis/claude_scalping_pattern_lab/build_claude_payload.py`
9. `analysis/claude_scalping_pattern_lab/run_all.sh`
10. `src/engine/dashboard_data_repository.py`
11. `src/engine/compress_db_backfilled_files.py`
12. `src/engine/log_archive_service.py`
13. `src/tests/test_build_tuning_monitoring_parquet.py`
14. `src/tests/test_dashboard_data_repository.py`
15. `docs/2026-04-22-stage2-todo-checklist.md`

---

## 실행한 테스트/검증 명령과 결과

1. `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_build_tuning_monitoring_parquet.py`
   - **7 passed**
2. `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_tuning_duckdb_repository.py`
   - **9 passed**
3. `PYTHONPATH=. .venv/bin/python -m src.engine.build_tuning_monitoring_parquet --dataset <...> --single-date ...` (범위 루프 실행)
   - pipeline_events/post_sell/system_metric_samples 파티션 생성 완료
4. `PYTHONPATH=. .venv/bin/python -m src.engine.compare_tuning_shadow_diff --start 2026-04-01 --end 2026-04-20`
   - **all_match=true**
5. `bash analysis/gemini_scalping_pattern_lab/run.sh`
   - 정상 완료
6. `bash analysis/claude_scalping_pattern_lab/run_all.sh`
   - 정상 완료
7. `PYTHONPATH=. .venv/bin/python -m src.engine.decommission_legacy_dashboard_tables --dry-run`
   - 삭제 대상 확인
8. `PYTHONPATH=. .venv/bin/python -m src.engine.decommission_legacy_dashboard_tables --execute --yes`
   - 테이블 2개 삭제 완료
9. 삭제 후 스모크
   - `PYTHONPATH=. .venv/bin/python analysis/gemini_scalping_pattern_lab/build_dataset.py`
   - `PYTHONPATH=. .venv/bin/python analysis/claude_scalping_pattern_lab/prepare_dataset.py`
   - 모두 정상 완료
10. `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_pipeline_event_logger.py src/tests/test_log_archive_service.py src/tests/test_performance_tuning_report.py src/tests/test_dashboard_data_repository.py src/tests/test_build_tuning_monitoring_parquet.py src/tests/test_tuning_duckdb_repository.py`
    - **39 passed**
11. `PYTHONPATH=. .venv/bin/python -m src.engine.compress_db_backfilled_files --days 1 --dry-run`
    - legacy raw 테이블 제거 후에도 정상 완료
    - `pipeline verified=1`, `snapshots skipped_unverified=6`
12. `deploy/install_tuning_monitoring_postclose_cron.sh`
    - crontab `TUNING_MONITORING_POSTCLOSE` 등록 완료

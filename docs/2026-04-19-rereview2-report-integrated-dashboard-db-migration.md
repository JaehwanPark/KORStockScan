# 재재검토 보고서: 통합대시보드 DB 전환

작성일: 2026-04-19  
검토자: Codex  
대상: `workorder-integrated-dashboard-db-migration` 재수정본

---

## 판정

**승인**  
요구사항 기준 핵심 보완(동적 snapshot kind 스캔, 회귀 테스트 통과, 문서 근거 교정)이 확인되었고,  
DB 적재 확인된 파일에 대해서는 압축까지 완료했습니다.

---

## 근거

### 1) 해결 확인된 항목

1. `snapshot kind` 하드코딩 해소
   - 동적 스캔 함수 추가: [dashboard_data_repository.py](/home/ubuntu/KORStockScan/src/engine/dashboard_data_repository.py:266)
   - 백필/당일 업로드 적용: [dashboard_data_repository.py](/home/ubuntu/KORStockScan/src/engine/dashboard_data_repository.py:473), [dashboard_data_repository.py](/home/ubuntu/KORStockScan/src/engine/dashboard_data_repository.py:514)
2. API 빌드 경로 `meta.source` 보강 반영
   - [app.py](/home/ubuntu/KORStockScan/src/web/app.py:140), [app.py](/home/ubuntu/KORStockScan/src/web/app.py:180), [app.py](/home/ubuntu/KORStockScan/src/web/app.py:219)
3. 테스트 재실행 통과
   - 실행: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_dashboard_data_repository.py src/tests/test_log_archive_service.py src/tests/test_performance_tuning_report.py`
   - 결과: `16 passed`

### 2) 보완 완료 확인

1. `monitor_snapshots.would_insert` 중복 증가 제거
   - 확인 위치: [dashboard_data_repository.py](/home/ubuntu/KORStockScan/src/engine/dashboard_data_repository.py:485), [dashboard_data_repository.py](/home/ubuntu/KORStockScan/src/engine/dashboard_data_repository.py:487)
   - 현재는 `would_insert` 1회 증가만 수행

2. CLI 출력에 `would_insert` 노출
   - 확인 위치: [backfill_dashboard_db.py](/home/ubuntu/KORStockScan/src/engine/backfill_dashboard_db.py:57), [backfill_dashboard_db.py](/home/ubuntu/KORStockScan/src/engine/backfill_dashboard_db.py:74)

3. 기존 재검토 문서 실행시간 근거 교정
   - 확인 위치: [2026-04-19-rereview-report-integrated-dashboard-db-migration.md](/home/ubuntu/KORStockScan/docs/2026-04-19-rereview-report-integrated-dashboard-db-migration.md:42)

### 3) DB 적재 확인 및 파일 압축 완료

1. DB 적재 확인(샘플/대상일)
   - `dashboard_monitor_snapshots`:
   - `2026-04-06`: `performance_tuning`, `trade_review`
   - `2026-04-07`: `performance_tuning`, `trade_review`
   - `2026-04-08`: `performance_tuning`, `trade_review`
   - `2026-04-09`: `add_blocked_lock`, `missed_entry_counterfactual`, `performance_tuning`, `post_sell_feedback`, `server_comparison`, `trade_review`
   - `dashboard_pipeline_events`:
   - `2026-04-09`: `349,218` rows
   - `2026-04-10`: `331,676` rows
   - `2026-04-13`: `431,004` rows
   - `2026-04-14`: `456,217` rows
   - `2026-04-15`: `242,886` rows
   - `2026-04-16`: `470,000` rows
   - `2026-04-17`: `407,767` rows

2. 압축 완료 파일(디스크 확보)
   - `data/pipeline_events/pipeline_events_2026-04-09.jsonl` -> `.jsonl.gz`
   - `data/report/monitor_snapshots/*_2026-04-06.json` -> `.json.gz`
   - `data/report/monitor_snapshots/*_2026-04-07.json` -> `.json.gz`
   - `data/report/monitor_snapshots/*_2026-04-08.json` -> `.json.gz`
   - `data/report/monitor_snapshots/*_2026-04-09.json` -> `.json.gz`
   - `data/pipeline_events/pipeline_events_2026-04-10.jsonl` -> `.jsonl.gz`
   - `data/pipeline_events/pipeline_events_2026-04-13.jsonl` -> `.jsonl.gz`
   - `data/pipeline_events/pipeline_events_2026-04-14.jsonl` -> `.jsonl.gz`
   - `data/pipeline_events/pipeline_events_2026-04-15.jsonl` -> `.jsonl.gz`
   - `data/pipeline_events/pipeline_events_2026-04-16.jsonl` -> `.jsonl.gz`
   - `data/pipeline_events/pipeline_events_2026-04-17.jsonl` -> `.jsonl.gz`
   - `data/report/monitor_snapshots/*_2026-04-10.json` -> `.json.gz`
   - `data/report/monitor_snapshots/*_2026-04-11.json` -> `.json.gz`
   - `data/report/monitor_snapshots/*_2026-04-12.json` -> `.json.gz`
   - `data/report/monitor_snapshots/*_2026-04-13.json` -> `.json.gz`
   - `data/report/monitor_snapshots/*_2026-04-14.json` -> `.json.gz`
   - `data/report/monitor_snapshots/*_2026-04-15.json` -> `.json.gz`
   - `data/report/monitor_snapshots/*_2026-04-16.json` -> `.json.gz`
   - `data/report/monitor_snapshots/*_2026-04-17.json` -> `.json.gz`
   - 배치 실행 요약: `compressed pipeline=6 (2.3GB), snapshots=42 (90.4MB), skipped_unverified=0`

---

## 다음 액션

1. 운영 모니터링
   - 야간 후크(`update_kospi.py` -> `upload_today_dashboard_files`) 성공/실패 로그 추적
2. 자동압축 운영 고정 완료
   - cron: `10 23 * * 1-5 /home/ubuntu/KORStockScan/deploy/run_dashboard_db_archive_cron.sh 1`
   - 로그: `/home/ubuntu/KORStockScan/logs/dashboard_db_archive_cron.log`
   - 기준: `DB 적재 확인 + D+1 경과` 파일만 압축

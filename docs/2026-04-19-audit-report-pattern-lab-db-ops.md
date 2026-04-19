# 2026-04-19 감리 결과보고서 — 패턴랩 DB 전환/주기 실행 고정

## 1) 판정

- **승인(조건부)**: 요청한 1~3번(영향도 반영, 주기 실행 고정, 계획서 반영)은 코드/문서/운영 스크립트까지 반영 완료.
- **조건부 사유**: `문서 -> GitHub Project -> Calendar` 자동동기화는 `GH_PROJECT_TOKEN` 누락으로 이번 턴에서 미완료.

## 2) 근거

### 2-1. 코드 반영

1. `analysis/claude_scalping_pattern_lab/prepare_dataset.py`
   - 데이터 소스를 `DB -> 파일(.json/.jsonl) -> 압축(.gz)` 우선순위로 보강.
   - `src.engine.dashboard_data_repository`의 `load_monitor_snapshot_prefer_db`, `load_pipeline_events` 연동.
   - DB 미가용 시 파일 fallback, 압축파일 fallback 추가.

2. `analysis/gemini_scalping_pattern_lab/build_dataset.py`
   - local pipeline 입력을 DB 우선(`load_pipeline_events`)으로 전환.
   - local/remote 파일 입력은 `.jsonl` + `.jsonl.gz` 동시 지원.
   - 손익 유효 표본은 `GOOD_EXIT/COMPLETED + numeric profit_rate` 기준으로 정리.

3. 실행 경로 정비
   - `analysis/gemini_scalping_pattern_lab/run.sh`를 `.venv` + `PYTHONPATH` 기반으로 표준화.

### 2-2. 운영 자동화(주기 실행) 반영

1. 추가 파일
   - `deploy/run_claude_scalping_pattern_lab_cron.sh`
   - `deploy/run_gemini_scalping_pattern_lab_cron.sh`
   - `deploy/install_pattern_lab_cron.sh`

2. cron 고정 결과
   - `PATTERN_LAB_CLAUDE_FRI_POSTCLOSE`: `40 18 * * 5`
   - `PATTERN_LAB_GEMINI_FRI_POSTCLOSE`: `10 19 * * 5`
   - 로그 경로:
     - `logs/claude_scalping_pattern_lab_cron.log`
     - `logs/gemini_scalping_pattern_lab_cron.log`

### 2-3. 문서/체크리스트 반영

1. `docs/plan-korStockScanPerformanceOptimization.performance-report.md`
   - `9. 패턴랩 정기 실행 및 DB 연계 운영` 섹션 추가.
2. `docs/2026-04-19-stage2-todo-checklist.md`
   - `[OpsFix0419] 스캘핑 패턴랩 DB 우선 수집 + 주간 cron 고정` 완료 항목 추가.
3. `docs/2026-04-24-stage2-todo-checklist.md`
   - `[OpsFollowup0424] 패턴랩 주간 cron 산출물/로그 정합성 점검` 후속 항목 추가.
4. README 정합성 반영
   - `analysis/claude_scalping_pattern_lab/README.md`
   - `analysis/gemini_scalping_pattern_lab/README.md`

## 3) 테스트/검증 결과

1. 구문/실행 가능성
   - `PYTHONPATH=. .venv/bin/python -m py_compile ...` **통과**
   - `bash -n deploy/... analysis/gemini.../run.sh` **통과**

2. 기능 스모크 테스트
   - Claude 1일 샘플(`2026-04-17`) 실행:
     - `trade_fact 68`, `funnel_fact 1`, `sequence_fact 75`
     - source 표시: `db`, `db_or_mixed` 확인
   - Gemini 1일 샘플(원격/포스트셀 경로 제외 조건) 실행:
     - `Dataset built successfully.` 확인

3. cron 등록 확인
   - `bash deploy/install_pattern_lab_cron.sh` 실행 후 marker 2종 라인 존재 확인.

4. 자동화 체인 동기화 상태
   - `sync_docs_backlog_to_project`, `sync_github_project_calendar` 모두
   - 실패 원인: `missing required env: GH_PROJECT_TOKEN`

## 4) 다음 액션

1. `GH_PROJECT_TOKEN` 주입 후 문서-프로젝트-캘린더 동기화를 재실행한다.
2. `2026-04-24 POSTCLOSE`에 주간 cron 첫 실행 결과(로그 + outputs 갱신)를 판정한다.
3. Gemini full dataset 실행시간이 길어질 경우(원격 로그 대량), 날짜 필터링/증분처리 축을 별도 개선 과제로 분리한다.

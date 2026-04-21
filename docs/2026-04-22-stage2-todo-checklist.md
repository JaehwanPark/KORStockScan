# 2026-04-22 Stage 2 To-Do Checklist

## 목적

- `same-symbol split-entry cooldown`은 앞선 split-entry 축과 독립 관찰이 가능할 때만 D+2 canary 착수 후보로 본다.
- `AIPrompt 작업 11 HOLDING critical 전용 경량 프롬프트 분리` 미완료분이 있으면 오늘 보강 실행한다.
- 속도 개선축을 정확도 개선축 뒤에 무기한 두지 않는다.
- `HOLDING schema 변경(D+2)` 성과판정을 오늘 최종 수행한다.
- `프롬프트 프로파일별 특화` 잔여과제는 `shadow 없이`, 필요 시 `canary 1축`으로 가장 빠른 일정에 반영한다.

## 장전/장중 체크리스트 (08:00~12:20)

- [ ] `[AIPrompt0422] 프로파일별 특화 프롬프트 잔여과제 범위 잠금(shared 의존 제거 포함)` (`Due: 2026-04-22`, `Slot: PREOPEN`, `TimeWindow: 08:00~08:10`, `Track: AIPrompt`)
  - 판정 기준: `watching/holding/exit/shared` 중 잔여과제를 코드/로그/지표 기준으로 분해하고, `공통 프롬프트 재사용`과 `프로파일별 특화`를 구분해 문서에 잠근다.
- [ ] `[AIPrompt0422] shadow 금지 고정 + canary 필요조건 정의` (`Due: 2026-04-22`, `Slot: PREOPEN`, `TimeWindow: 08:10~08:20`, `Track: Plan`)
  - 판정 기준: 신규 프롬프트 실험은 shadow를 열지 않고 `canary 1축`으로만 진행한다. canary 조건은 `N_min`, `reject_rate`, `latency_p95`, `partial_fill_ratio`, `buy_drought_persist`를 명시한다.
- [ ] `[AIPrompt0422] 프로파일별 특화 프롬프트 1축 canary 적용 여부 결정` (`Due: 2026-04-22`, `Slot: PREOPEN`, `TimeWindow: 08:20~08:30`, `Track: AIPrompt`)
  - 판정 기준: `shared` 의존 제거를 포함한 후보 중 1축만 선택해 ON/OFF를 결정하고, 미착수 시 보류 사유와 재시각을 남긴다.
- [ ] `[LatencyPreflight0422] WAIT65~79 recheck/submitted 관측 경로 사전확인` (`Due: 2026-04-22`, `Slot: PREOPEN`, `TimeWindow: 08:30~08:40`, `Track: AIPrompt`)
  - Source: [2026-04-21-auditor-performance-result-report.md](/home/ubuntu/KORStockScan/docs/2026-04-21-auditor-performance-result-report.md)
  - 판정 기준: `wait6579_ev_cohort.preflight`에서 `behavior_change=none`, `observability_passed=true`, `recovery_check_candidates`, `recovery_promoted_candidates`, `probe_applied_candidates`, `budget_pass_candidates`, `latency_block_candidates`, `submitted_candidates`, `submission_blocker_breakdown`이 모두 산출되는지 확인한다. 장전에는 latency/AI threshold 파라미터를 추가 완화하지 않는다.
  - 감사인 응답 반영: `latency_block_reason_breakdown`에서 `latency_state_danger`와 `latency_fallback_disabled`를 분리 확인한다. 특히 `latency_fallback_disabled=7` 경로가 구조적 버그인지 먼저 판정하고, bugfix가 아니면 `[AIPrompt0422]` 1차 판정 전 행동 canary를 추가로 열지 않는다.
- [ ] `[AIPrompt0422] 프로파일별 특화 프롬프트 canary 1차 계량 잠금` (`Due: 2026-04-22`, `Slot: INTRADAY`, `TimeWindow: 12:00~12:20`, `Track: AIPrompt`)
  - 판정 기준: `ai_confirmed_buy_count/share`, `WAIT 65/70/75~79`, `blocked_ai_score`, `ai_confirmed->submitted`, `full/partial` 분리, `COMPLETED+valid profit_rate`를 main-only로 잠근다.
- [ ] `[AIPrompt0422] Gemini BUY recovery canary 1일차 판정` (`Due: 2026-04-22`, `Slot: INTRADAY`, `TimeWindow: 12:00~12:20`, `Track: AIPrompt`)
  - Source: [2026-04-21-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-21-stage2-todo-checklist.md)
  - 판정 기준: 04-22 오전 구간까지만 수집하고 `12:00` 이후 생성된 스냅샷을 고정 시점으로 사용한다. `ai_confirmed_buy_count/share`, `WAIT 65/70/75~79`, `blocked_ai_score`, `ai_confirmed->submitted`, `missed_winner_rate`, full/partial fill을 main-only로 판정한다.

## 장후 체크리스트 (15:30~)

- [x] `[AuditFix0422] same-symbol split-entry cooldown canary 1일차 착수 또는 보류 기록` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 15:30~15:40`, `Track: ScalpingLogic`) (`폐기: 2026-04-21 Plan Rebase 기준`)
  - 판정 기준: `rebase/즉시 재평가` 관찰축과 원인귀속이 분리될 때만 착수, 아니면 보류 사유와 재시각 기록
  - 선행 메모 (`2026-04-20 PREOPEN`): `D+2 이관 확정`. `rebase/즉시 재평가`와 독립 관찰 가능할 때만 착수
  - 폐기 사유: `fallback_scout/main`, `fallback_single`, latency fallback split-entry는 영구 폐기되어 canary 착수/보류 판정 대상이 아니다.
- [ ] `AIPrompt 작업 11 HOLDING critical 전용 경량 프롬프트 분리` 미완료분 보강 (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 15:40~15:50`, `Track: AIPrompt`)
  - 실행 메모: 운영 비교표에는 `schema 변경 효과`와 `경량 프롬프트 효과`를 별도 컬럼으로 남긴다.
- [ ] `[AuditFix0422] HOLDING 성과 최종판정(missed_upside_rate/capture_efficiency/GOOD_EXIT)` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 15:50~16:00`, `Track: AIPrompt`)
- [ ] `[HolidayCarry0419] AIPrompt 작업 10 HOLDING hybrid 적용` 확대 여부 최종판정 (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:10`, `Track: AIPrompt`)
  - 판정 기준: `missed_upside_rate/capture_efficiency/GOOD_EXIT`와 `holding_action_applied/holding_force_exit_triggered` 운영 로그가 모두 확보됐을 때만 확대 여부 결정
- [ ] `[AuditFix0422] HOLDING 지표 우선순위(primary/secondary) 고정 기록` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 16:10~16:20`, `Track: Plan`)
- [ ] `[PlanSync0422] AI 엔진 A/B 원격 preflight 체크리스트 항목 확정` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 16:20~16:30`, `Track: AIPrompt`)
  - 판정 기준: `2026-04-23 POSTCLOSE`에 수행할 원격 정합화 범위(설정값/관찰축/롤백가드)와 `2026-04-24` 착수 여부 판정 게이트를 문서 고정
- [ ] `[Governance0422] GPT 엔진 금지패턴 및 AI 생성 코드 체크게이트 문서 재확인` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:20`, `Track: AIPrompt`)
  - Source: [2026-04-22-ai-generated-code-governance.md](/home/ubuntu/KORStockScan/docs/2026-04-22-ai-generated-code-governance.md)
  - 판정 기준: `fallback_scout/main` 동시 다중 leg 금지, 의도-구현 일치, 단위테스트, 운영자 수동승인, `ai_generated/design_reviewed` 라벨링, rollback guard가 실제 변경/운영 로그에서 위반되지 않았는지 확인한다.
- [x] `[VisibleResult0422] legacy shadow canary 1일차 결과 기반 live 승격/롤백 판정` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:40`, `Track: Plan`) (`폐기: 2026-04-21 Plan Rebase 기준`)
  - 판정 기준: `승격 1축` 또는 `롤백` 중 하나로 강제 종료하고, shadow 복귀는 금지
- [x] `[PlanSync0422] legacy shadow 잔여항목 0화 확인(미전환 shadow 없음)` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 16:40~16:50`, `Track: Plan`) (`폐기: 2026-04-21 Plan Rebase 기준`)
  - 판정 기준: 남은 shadow 항목이 있으면 `폐기` 또는 `기존 live 축 병합`으로 닫고 독립 shadow 상태를 남기지 않는다
  - 폐기 사유: 신규/보완축은 `shadow 금지`, `canary-only` 원칙으로 통일했다. 잔여 shadow 확인은 Plan Rebase 문서 정리로 흡수한다.
- [x] `[DataArch0422] 튜닝 모니터링 로그 저장구조 전환 작업지시서 확정 + Gemini 착수` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 16:50~17:00`, `Track: Plan`) (`실행: 2026-04-21 07:48 KST`)
  - Source: [workorder-gemini-tuning-monitoring-log-architecture-refactor.md](/home/ubuntu/KORStockScan/docs/workorder-gemini-tuning-monitoring-log-architecture-refactor.md)
  - 판정 기준: `원본 jsonl 보관 + 분석 parquet/DuckDB + PostgreSQL 메타데이터` 3계층과 `shadow-only -> canary 1축` 순서를 문서 기준으로 고정한다.
  - 선행 완료: 개선작업 결과서 기준 완료 승인 가능 상태.
- [x] `[DataArch0422] DuckDB/Parquet 의존성 승인 여부 및 대안경로 확정` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:10`, `Track: Plan`) (`실행: 2026-04-21 07:48 KST`)
  - 판정 기준: 사용자 승인 전에는 패키지 설치를 진행하지 않고, 승인 실패 시 `JSONL+SQLite 임시분석` 대안 경로와 재판정 시각을 기록한다.
  - 선행 완료: 기존 `.venv` 의존성으로 처리, 신규 패키지 설치 없음.
- [x] `[DataArch0422] jsonl vs parquet shadow 집계 일치성 검증(거래수/퍼널/blocker/체결품질)` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 17:10~17:30`, `Track: Plan`) (`실행: 2026-04-21 07:44 KST`)
  - 판정 기준: 정수 집계 오차 0, `full/partial` 분리 유지, `COMPLETED + valid profit_rate` 규칙 위반 0건일 때만 다음 축 전환 검토
  - 선행 완료: `compare_tuning_shadow_diff --start 2026-04-01 --end 2026-04-20` 재실행 결과 `all_match=true`.
- [x] `[DataArch0422] 분석랩 2종(gemini/claude) 데이터 소스 우선순위 전환 및 shadow diff 기록` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 17:30~17:50`, `Track: Plan`) (`실행: 2026-04-21 07:48 KST`)
  - Source: [workorder-gemini-tuning-monitoring-log-architecture-refactor.md](/home/ubuntu/KORStockScan/docs/workorder-gemini-tuning-monitoring-log-architecture-refactor.md)
  - 판정 기준: 두 분석랩의 `trade/funnel/sequence` 정수 집계 오차 0, `run_manifest`의 `data_source_mode` 기록, fallback 발생 시 사유+재실행시각 고정
  - 선행 완료: Gemini/Claude `run_manifest`에 `data_source_mode=duckdb_primary`, `history_coverage_ok=true` 기록.
- [x] `[DataArch0422] 과거 전체 누적 데이터 parquet/DuckDB 커버리지 검증` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 17:50~18:10`, `Track: Plan`) (`실행: 2026-04-21 07:44 KST`)
  - 판정 기준: `history_start~yesterday` 누락일 0건, DuckDB 기준 리포트/분석랩 실행 성공, `history_coverage_ok=true` 증적 기록
  - 선행 완료: `coverage_summary.json` 기준 `missing_in_parquet=[]`, DuckDB 직접 조회 `pipeline_events=2,857,648 rows`.
- [x] `[DataArch0422] legacy DB raw 테이블 제거 및 운영혼선 차단 확인` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 18:10~18:30`, `Track: Plan`) (`실행: 2026-04-21 07:48 KST`)
  - Source: [workorder-gemini-tuning-monitoring-log-architecture-refactor.md](/home/ubuntu/KORStockScan/docs/workorder-gemini-tuning-monitoring-log-architecture-refactor.md)
  - 판정 기준: `dashboard_pipeline_events/dashboard_monitor_snapshots` 등 제거 대상 drop 완료, 메타 테이블만 유지, 제거 후 리포트 정상 동작 확인
  - 선행 완료: legacy raw 테이블 dry-run 기준 존재하지 않음. `KORSTOCKSCAN_ENABLE_LEGACY_DASHBOARD_DB` opt-in 없이는 재생성/쓰기 차단.
- [x] `[DataArch0422] 중복/불필요 cron 정리` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 18:20~18:30`, `Track: Plan`) (`실행: 2026-04-21 07:52 KST`)
  - 판정 기준: `TUNING_MONITORING_POSTCLOSE`와 중복되는 금요일 분석랩 cron 제거, 오래된 1회성 주석/중복 주석 정리, 유지 대상 운영 cron 확인
  - 선행 완료: `PATTERN_LAB_CLAUDE_FRI_POSTCLOSE`, `PATTERN_LAB_GEMINI_FRI_POSTCLOSE` 제거 및 `deploy/install_pattern_lab_cron.sh` cleanup shim 전환.
- [ ] `[DataArch0422] TUNING_MONITORING_POSTCLOSE 첫 자동실행 결과 확인` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 18:30~18:40`, `Track: Plan`)
  - Source: [workorder-gemini-tuning-monitoring-log-architecture-refactor-result.md](/home/ubuntu/KORStockScan/docs/workorder-gemini-tuning-monitoring-log-architecture-refactor-result.md)
  - 판정 기준: `logs/tuning_monitoring_postclose_cron.log`에서 증분 parquet 생성, shadow diff `all_match=true`, Gemini/Claude `history_coverage_ok=true` 확인
  - 2026-04-21 사전 확인: `18:05 KST` cron 실행은 `pipeline_events` parquet 생성 중 OOM kill로 실패했다. `build_tuning_monitoring_parquet`를 원본 이벤트 즉시 축소 row 변환 방식으로 보수한 뒤 `19:23~19:26 KST` 수동 재실행 성공.
  - 2026-04-21 수동 복구 증적: `pipeline_events_20260421.parquet=421,220 rows`, `post_sell_20260421.parquet=9 rows`, `system_metric_samples_20260421.parquet=802 rows`, `shadow_diff all_match=true`, Gemini/Claude `history_coverage_ok=true`.
  - 2026-04-22 항목은 유지한다. 사유: 오늘은 수동 복구 성공이고, `TUNING_MONITORING_POSTCLOSE`의 첫 정상 자동실행 여부는 2026-04-22 장후 cron 로그로 별도 확인해야 한다.
- [ ] `[DataArch0422] monitor snapshot raw 압축/보존 정책 재판정` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 18:40~18:50`, `Track: Plan`)
  - Source: [workorder-gemini-tuning-monitoring-log-architecture-refactor-result.md](/home/ubuntu/KORStockScan/docs/workorder-gemini-tuning-monitoring-log-architecture-refactor-result.md)
  - 판정 기준: `dashboard_db_archive` snapshot `skipped_unverified`를 허용 상태로 둘지, parquet/manifest 검증 기반 압축으로 전환할지 결정
- [ ] 미완료 시 `사유 + 다음 실행시각` 기록

## 참고 문서

- [2026-04-21-stage2-todo-checklist.md](./2026-04-21-stage2-todo-checklist.md)
- [2026-04-19-aiprompt-task8-task10-holiday-recheck.md](./2026-04-19-aiprompt-task8-task10-holiday-recheck.md)
- [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md)
- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)
- [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md)
- [plan-korStockScanPerformanceOptimization.performance-report.md](./plan-korStockScanPerformanceOptimization.performance-report.md)
- [workorder-gemini-tuning-monitoring-log-architecture-refactor.md](./workorder-gemini-tuning-monitoring-log-architecture-refactor.md)

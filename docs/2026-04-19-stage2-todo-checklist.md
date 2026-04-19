# 2026-04-19 Stage 2 To-Do Checklist

## 목적

- 휴일(`2026-04-19`)로 인한 비거래일 운영 원칙에 따라 실행 항목을 `2026-04-20` 장후 슬롯으로 이관한다.

## 정합성 메모

- `2026-04-18 10:21 KST` 기준 GitHub Project에 남아 있던 `[Checklist0413] AIPrompt 작업 9 정량형 수급 피처 이식 1차 착수`의 `Source=docs/2026-04-19-stage2-todo-checklist.md` 표기는 문서 정합성과 불일치한다.
- 실제 후속 체크리스트는 `docs/2026-04-20-stage2-todo-checklist.md`의 `[HolidayCarry0418] AIPrompt 작업 9 정량형 수급 피처 이식 1차` 항목이며, `2026-04-18` 선행 착수 결과를 그 문서 기준으로 이어서 판정한다.

## 휴일 이관 처리

- [x] `[HolidayReassign0419] AIPrompt 작업 10 HOLDING hybrid 적용` 1차 결과 평가/확대 여부 항목 이관 완료 (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 15:30~15:45`, `Track: AIPrompt`)
  - 판정: `2026-04-20 POSTCLOSE` 실행 항목으로 이관
  - 근거: 선행 착수 결과 확인이 필요해 휴일 선실행 불가
  - 다음 액션: `2026-04-20` 장후 결과를 기준으로 확대/보류 판정
  - 실행 메모 (`2026-04-19 09:26 KST`): 판정=`보류 유지`. `src/engine/sniper_state_handlers.py` 기준 `holding_action_applied`, `holding_force_exit_triggered`, `holding_override_rule_version` 로그 축이 아직 연결되지 않아 holiday 기준 확대 여부를 닫을 관찰축이 부족하다.
  - 후속 고정: `2026-04-20 POSTCLOSE`에는 `shadow-only 유지/확대 보류` 1차 판정만 수행하고, 최종 확대 여부는 `2026-04-22 POSTCLOSE` `HOLDING shadow` 성과판정과 함께 닫는다.
- [x] `[HolidayReassign0419] AIPrompt 작업 8 감사용 핵심값 3종 투입` 미완료 정리 항목 이관 완료 (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 15:45~16:00`, `Track: AIPrompt`)
  - 판정: `2026-04-20 POSTCLOSE` 실행 항목으로 이관
  - 근거: 작업 10 결과와 동시 점검 시 문맥 정합성이 높음
  - 다음 액션: 미완료 시 동일 슬롯에서 `사유 + 다음 실행시각` 기록
  - 실행 메모 (`2026-04-19 09:26 KST`): 판정=`미완료 유지`. `buy_pressure_10t`, `distance_from_day_high_pct`, `intraday_range_pct` 값 주입은 코드에 있으나 `buy_pressure_10t_sent`, `distance_from_day_high_pct_sent`, `intraday_range_pct_sent` 감사 로그 축이 없어 완료로 닫지 않는다.
  - 후속 고정: `2026-04-20 POSTCLOSE 15:45~16:00`에 main runtime 실표본과 sent 로그 존재 여부를 먼저 확인하고, 미충족이면 같은 항목 제목으로 `사유 + 다음 실행시각`을 재기록한다.
- [x] `[OpsFix0419] DB 적재 확인 + D+N(1일) 경과 파일 자동압축 cron 고정` 완료 (`Due: 2026-04-19`, `Slot: POSTCLOSE`, `TimeWindow: 18:00~18:20`, `Track: Plan`)
  - 판정: 승인
  - 근거: `src/engine/compress_db_backfilled_files.py` 추가, `deploy/run_dashboard_db_archive_cron.sh` 추가, crontab `DASHBOARD_DB_ARCHIVE_2310` 등록 확인
  - 실행 결과 (`2026-04-19 18:45 KST`): `2026-04-10~2026-04-17` DB 적재 후 압축 완료. `compressed pipeline=6 (2.3GB), snapshots=42 (90.4MB), skipped_unverified=0`
  - 다음 액션: `logs/dashboard_db_archive_cron.log`에서 `DASHBOARD_ARCHIVE_*` 통계와 `skipped_unverified` 추세를 장후 점검 (`2026-04-19 23:10 KST`부터 D+1 기준 적용)
- [x] `[OpsFix0419] logs 회전백업(.log.N) D+7 자동정리 cron 고정` 완료 (`Due: 2026-04-19`, `Slot: POSTCLOSE`, `TimeWindow: 23:20~23:25`, `Track: Plan`)
  - 판정: 승인
  - 근거: `deploy/run_logs_rotation_cleanup_cron.sh` 추가, crontab `LOG_ROTATION_CLEANUP_2320` 등록 확인
  - 실행 결과 (`2026-04-19 23:xx KST` 사전 실행): `retention_days=7`, `deleted=0`, `rotated_before=0`, `rotated_after=0`
  - 다음 액션: `logs/log_rotation_cleanup_cron.log`에서 `deleted/size_before/size_after` 추세를 장후 점검
- [x] `[OpsFix0419] 스캘핑 패턴랩 DB 우선 수집 + 주간 cron 고정` 완료 (`Due: 2026-04-19`, `Slot: POSTCLOSE`, `TimeWindow: 23:25~23:40`, `Track: Plan`)
  - 판정: 승인
  - 근거: `analysis/*_scalping_pattern_lab` 데이터 수집이 `DB -> 파일 -> .gz` 우선순위로 보강되었고, `deploy/install_pattern_lab_cron.sh`로 주간 자동 실행 라인이 고정됨
  - 실행 결과 (`2026-04-19 23:3x KST`): `PATTERN_LAB_CLAUDE_FRI_POSTCLOSE`, `PATTERN_LAB_GEMINI_FRI_POSTCLOSE` crontab 등록 및 래퍼 스크립트 실행 경로 검증
  - 자동화 동기화 (`문서 -> Project -> Calendar`): `GH_PROJECT_TOKEN` 누락으로 `sync_docs_backlog_to_project`, `sync_github_project_calendar` 미실행
  - 다음 액션: `2026-04-24 POSTCLOSE` 첫 주간 자동 실행 로그(`claude/gemini_scalping_pattern_lab_cron.log`)와 산출물 정합성 확인

## 참고 문서

- [2026-04-18-stage2-todo-checklist.md](./2026-04-18-stage2-todo-checklist.md)
- [2026-04-20-stage2-todo-checklist.md](./2026-04-20-stage2-todo-checklist.md)
- [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md)
- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)
- [2026-04-19-rereview2-report-integrated-dashboard-db-migration.md](./2026-04-19-rereview2-report-integrated-dashboard-db-migration.md)
- [2026-04-19-audit-report-pattern-lab-db-ops.md](./2026-04-19-audit-report-pattern-lab-db-ops.md)

# KORStockScan Session Pointer

세션 진입용 문서 지도다. 일반 작업마다 다시 읽거나 연결 문서를 전부 로드하지 않는다. 공통 작업 규칙은 [AGENTS.md](../AGENTS.md)에 있다.

| 필요 정보 | 읽을 원본 |
| --- | --- |
| 작업 시작 필수 원칙·active/observe/OFF·rollback | [Plan Rebase §1–§8](./plan-korStockScanPerformanceOptimization.rebase.md) |
| 현재 실행 항목·시간·OPEN owner·수용조건 | 현재 KST 날짜의 `docs/checklists/YYYY-MM-DD-stage2-todo-checklist.md` 상단 요약과 해당 항목 |
| 장중 모니터링을 요청받은 경우 | [장중 작업지시문](./intraday-monitoring-task-instructions.md) |
| 장후 모니터링·허용 복구·추천 구현을 요청받은 경우 | [장후 작업지시문](./postclose-tuning-result-review-task-instructions.md) |
| 실행/복구 권한·배포 경로 확인 | [Time-based runbook](./time-based-operations-runbook.md), [Runtime release routing](./runtime-release-routing.md)의 해당 절 |
| producer/consumer·R0–R6·Metric Decision Contract | [Traceability](./report-based-automation-traceability.md)의 해당 계약 |
| collector/report/apply/env 운영 | [Threshold README](../data/threshold_cycle/README.md)의 해당 절 |
| clean tuning 기준 | [Policy artifact](../data/source_quality/clean_baseline_policy.json) |
| 완료된 검토의 근거가 필요한 경우 | [Stable-index inventory](./audit-reports/2026-09-05-postclose-work-inventory.md)의 해당 행과 직접 evidence |
| 과거 결정/변경 확인을 요청받은 경우 | [Execution delta](./plan-korStockScanPerformanceOptimization.execution-delta.md), [archive](./archive/)의 해당 기록 |

현재 owner는 당일 checklist에서 찾는다. 과거 완료 ID·PID·선택값을 현재 상태로 복제하지 않는다. 문서 열람·정비는 그 안의 monitoring/repair/restart 실행 요청이 아니다. 변경 검증과 사용자 수동 sync 규칙은 AGENTS.md §3/§5를 따른다.

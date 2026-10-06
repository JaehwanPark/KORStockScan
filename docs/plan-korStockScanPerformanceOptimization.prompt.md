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
| Main 고정감시·종목/owner 퇴역 전환 | [두산 전환 owner](./proposals/doosan-episode-retirement-main-fixed-watch-initial-policy-plan-2026-10-06.md), [release 전환 절차](./runtime-release-routing.md#main-fixed-watch-owner-retirement-transition) |
| clean tuning 기준 | [Policy artifact](../data/source_quality/clean_baseline_policy.json) |
| 현재 장후작업 구성·예약·stage·OFF/퇴역·정책 소비 확인 | [장후작업 현행 활성 목록](./audit-reports/2026-09-05-postclose-work-inventory.md)의 해당 owner와 직접 코드/설치 근거 |
| 완료된 검토의 근거가 필요한 경우 | 해당 checklist의 완료 기록과 연결된 audit/원 artifact; 현행 목록을 과거 실행 결과로 사용하지 않음 |
| 과거 결정/변경 확인을 요청받은 경우 | [Execution delta](./plan-korStockScanPerformanceOptimization.execution-delta.md), [archive](./archive/)의 해당 기록 |

현재 owner는 당일 checklist에서 찾는다. 과거 완료 ID·PID·선택값을 현재 상태로 복제하지 않는다. 문서 열람·정비는 그 안의 monitoring/repair/restart 실행 요청이 아니다. 변경 검증과 사용자 수동 sync 규칙은 AGENTS.md §3/§5를 따른다.

위젯 실행·수집·연구·장후 정책 발행은 퇴역 대상이다. 새 실행 명령과 정책 복원 경로를 만들지 않는다. 공통 비용/WS/에피소드 원천과 과거 custody는 별도 보존하며 현재 제거·자연 acceptance는 당일 `WidgetFullRetirement1006` owner가 소유한다.

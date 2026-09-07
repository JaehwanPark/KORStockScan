# 계획: KORStockScan 성능 최적화 실행안 (Session Prompt)

현행화: `2026-09-07 KST`
역할: 세션 진입용 경량 포인터이며 별도의 runtime owner/ON 목록을 복제하지 않는다. 일반 작업마다 이 문서를 다시 읽을 필요는 없다.

## 현재 Source of Truth

| 용도 | 문서 |
| --- | --- |
| 튜닝 원칙·current/open 판단 | [Plan Rebase §1~§8](./plan-korStockScanPerformanceOptimization.rebase.md) |
| 실행 항목·시간·OPEN owner | 당일 `docs/checklists/YYYY-MM-DD-stage2-todo-checklist.md` — 이번 현행화 기준 [9/7 checklist](./checklists/2026-09-07-stage2-todo-checklist.md) |
| producer/consumer·승인·Metric Contract | [Traceability](./report-based-automation-traceability.md) |
| 실행·복구 권한 | [Time-based runbook](./time-based-operations-runbook.md) |
| 장후 상세검토 진행 | [Stable-index inventory](./audit-reports/2026-09-05-postclose-work-inventory.md) |
| 명시적으로 호출된 장후 모니터링·안전범위 추천 구현 | [Postclose task instructions](./postclose-tuning-result-review-task-instructions.md) |
| 장중 점검 | [Intraday task instructions](./intraday-monitoring-task-instructions.md) |
| collector/report/apply/runtime env | [Threshold README](../data/threshold_cycle/README.md) |
| clean baseline | [Policy artifact](../data/source_quality/clean_baseline_policy.json) |
| 이력·종료축 | [Execution delta](./plan-korStockScanPerformanceOptimization.execution-delta.md), [archive](./archive/) |

## 세션 시작과 판단 경계

1. Plan Rebase §1~§8, 당일 checklist의 오늘 목적·오늘 강제 규칙, `AGENTS.md` current-state snapshot을 읽는다. 과거 체크리스트 완료는 현재 OPEN owner가 아니다.
2. 목표는 EV/순이익 극대화다. Clean tuning 기준은 `2026-06-05T00:00:00+09:00`; 그 이전 자료는 archive/audit only다. 기존 문서의 6/4 시각을 현재 기준으로 쓰지 않는다.
3. 자동 적용은 활성 family의 source·경제성·AI/deterministic guard를 통과한 다음 PREOPEN candidate/policy/receipt가 소유한다. 코드 구현·merge·report 성공·selected·PID 소비·실현 EV를 각각 구분한다.
4. ADM/LDM·bucket·greenfield 및 전용 institutional aggregate는 retired, Swing은 OFF다. 비우선 sim의 단순 무표본을 복구/승격 작업으로 만들지 않는다. 실제 surviving producer와 OFF 상태는 설치 계약으로 확인한다.
5. Main AI R0–R3는 지속적 offline prompt/input 개선 경로다. #76/#82/#78 환류와 #81 legacy live OFF, 별도 KRX `entry_setup_live_policy`를 혼동하지 않는다.
6. 완료된 #8/#9 등은 신규 결함·계약 변경·필수 소비 실패 없이 재검토하지 않는다. 미관측 성과와 자연 source/receipt 대기는 기존 checklist acceptance로 추적한다.
7. Operator lock은 단지 오래됐다는 이유로 해제하지 않는다. 명시적 장중 override도 Plan Rebase의 단일 축·cohort·rollback·hard-safety 경계를 따라야 한다. provider/bot/order/quantity 변경 권한을 추론하지 않는다.
8. 문서 현행화는 그 문서 속 monitoring/repair/restart 절차를 실행하라는 요청이 아니다. 사용자 변경을 보존하고 요청 범위만 수정한다.
9. 변경 후 `korstockscan-review-gate`의 review→fix→re-review→targeted validation을 닫는다. 문서는 parser·링크·현재 owner·권한 정합성으로 검증하며 비용 큰 report/provider 실행을 요구하지 않는다.

## Metric Decision Contract

새 관찰지표에는 `metric_role`, `decision_authority`, `window_policy`, `sample_floor`, `primary_decision_metric`, `source_quality_gate`, `forbidden_uses`가 필요하다. EV는 `equal_weight_avg_profit_pct|notional_weighted_ev_pct|source_quality_adjusted_ev_pct`, 승률은 보조 `diagnostic_win_rate`다. 결측 비용/미완료 결과를 0 또는 gross EV로 대체하지 않고 real full-fill/partial/sim/CF를 분리한다. 진단 수리 완료에 별도 live 승격 허들을 추가하지 않는다.

## 문서 검증과 사용자 동기화

AI는 print-only parser 검증만 실행한다. Project/Calendar sync와 token 검사는 하지 않는다. 동기화는 사용자가 아래 표준 명령 하나로 수행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

# 계획: KORStockScan 성능 최적화 실행안 (Session Prompt)

기준 시각: `2026-05-13 KST (자동화체인 Rebase 현행화)`
역할: 다음 세션에서 중심 기준 문서로 진입하기 위한 경량 포인터다.

이 문서는 세션 시작용 포인터만 남긴다. 현재 판단의 source of truth는 [Plan Rebase](./plan-korStockScanPerformanceOptimization.rebase.md), 실행 작업은 날짜별 `stage2 todo checklist`, 자동화 산출물/consumer 계약은 [report-based-automation-traceability](./report-based-automation-traceability.md)가 소유한다. 2026-05-13 이전 prompt 원문은 [pre-automation-renewal archive](./archive/plan-korStockScanPerformanceOptimization.prompt.pre-automation-renewal-2026-05-13.md)에 보존했다. README/런북(runbook)/Plan Rebase/prompt/AGENTS 갱신은 후순위 문서 갱신(document mutation)이며 `1차 수정(first-pass bounded update) -> 2차 감리(second-pass audit review) -> 최종 수정(finalize after second-pass review)` 순서로만 닫는다.

## 현재 Source of Truth

1. 중심 기준: [plan-korStockScanPerformanceOptimization.rebase.md](./plan-korStockScanPerformanceOptimization.rebase.md)
2. 당일 실행표: [2026-05-13-stage2-todo-checklist.md](./2026-05-13-stage2-todo-checklist.md)
3. 자동화체인/Metric Decision Contract: [report-based-automation-traceability.md](./report-based-automation-traceability.md)
4. threshold collector/report/apply plan/runtime env: [data/threshold_cycle/README.md](../data/threshold_cycle/README.md)
5. report inventory와 Markdown 누락 후보: [data/report/README.md](../data/report/README.md)
6. 원안 대비 실행 변경과 종료 이력: [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md)
7. 반복 판단 기준과 감리 Q&A: [plan-korStockScanPerformanceOptimization.qna.md](./plan-korStockScanPerformanceOptimization.qna.md)
8. 종료/폐기 관찰축: [archive/closed-observation-axes-2026-05-01.md](./archive/closed-observation-axes-2026-05-01.md)

## 현재 운영 원칙

1. 목표는 손실 억제가 아니라 기대값/순이익 극대화다.
2. 중심 루프는 `R0_collect -> R1_daily_report -> R2_cumulative_report -> R3_manifest_only -> R4_preopen_apply_candidate -> R5_bounded_calibrated_apply -> R6_post_apply_attribution`다.
3. 장중 runtime threshold mutation은 금지한다. 적용은 장후 report/calibration/AI review와 다음 장전 runtime env를 통해서만 한다.
4. `2026-05-13` PREOPEN 기준 selected runtime family는 `soft_stop_whipsaw_confirmation`, `score65_74_recovery_probe`다.
5. live AI route는 OpenAI 고정이며 provider transport/provenance는 threshold, 주문가/수량, 스윙 dry-run guard 변경과 분리한다.
6. 스윙은 dry-run self-improvement 체인이다. approval request가 있어도 별도 approval artifact 없이는 env apply, real canary, live order 전환 금지다.
7. sim/probe/counterfactual은 source bundle과 approval request 근거가 될 수 있지만 real execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
8. Sentinel, panic sell/buying, system error detector는 report-only/source-quality/incident 입력이며 자동 threshold/order/provider/bot restart 변경 권한이 없다.

## Metric Decision Contract 요약

1. 새 관찰지표는 `metric_role`, `decision_authority`, `window_policy`, `sample_floor`, `primary_decision_metric`, `source_quality_gate`, `forbidden_uses`를 생성 시점에 선언한다.
2. 승률은 `diagnostic_win_rate`이며 단독 live/canary 승인 기준이 아니다.
3. EV는 `primary_ev`가 맡고, 필드명은 `equal_weight_avg_profit_pct`, `notional_weighted_ev_pct`, `source_quality_adjusted_ev_pct` 중 하나로 쓴다.
4. 단순 손익 합산은 EV가 아니며 `simple_sum_profit_pct`로 표시한다.
5. daily-only 수치는 incident/safety/source-quality/운영 trigger에는 쓸 수 있지만, edge apply 승인은 rolling/cumulative 또는 post-apply version window와 함께 본다.
6. 계약 없는 새 metric은 `instrumentation_gap` 또는 `source_quality_blocker`로만 라우팅한다.

## 세션 시작 체크

1. Plan Rebase §1~§8을 읽는다.
2. 당일 checklist 상단 `오늘 목적`, `오늘 강제 규칙`을 읽는다.
3. AGENTS.md `현재 상태 기준` 날짜가 Plan Rebase와 맞는지 확인한다.
4. dirty worktree가 있으면 사용자/runtime 변경을 되돌리지 않는다.
5. README/런북(runbook)/Plan Rebase/prompt/AGENTS를 바꾸면 1차 수정 후 2차 감리에서 이력성 내용 archive 여부, 영어 약칭의 한글/영어 병기, runtime/order/provider/bot mutation 금지선을 확인한 뒤 최종 수정으로 닫는다.
6. 문서/checklist를 바꾸면 parser 검증을 실행하고, Project/Calendar 동기화는 사용자 수동 명령으로만 남긴다.

## 문서 운영 규칙

1. 현재 원칙과 active/open 상태는 Rebase가 소유한다.
2. 실행 작업항목은 날짜별 checklist만 소유한다.
3. 자동화 산출물, source bundle, Metric Decision Contract는 report traceability 문서가 소유한다.
4. 완료된 과거 checklist `[x]` 항목은 증적이지 현재 OPEN owner가 아니다.
5. 과거 일정표, 지나간 owner 판정 메모, 종료된 latency/fallback/shadow 축은 archive 또는 execution-delta에 둔다.
6. Project/Calendar 동기화 명령은 아래 1개로 통일한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

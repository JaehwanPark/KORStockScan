# 2026-04-24 Stage 2 To-Do Checklist

## 오늘 목적

- `2026-04-20~2026-04-23` 검증 결과를 바탕으로 금요일 결론을 `승격 1축 실행` 또는 `보류+재시각` 중 하나로 닫는다.
- 주간 판정에는 regime 태그와 조건부 유효범위를 함께 남긴다.
- 오전 `10:00 KST`까지의 주병목 검증축은 `spread relief canary` 실효성 확인으로 고정한다.
- `PYRAMID zero_qty Stage 1`은 `SCALPING/PYRAMID bugfix-only` 범위의 `flag OFF` 증적을 먼저 확인하고, 승인 시에도 `main-only 1축 canary`로만 해석한다.

## 오늘 강제 규칙

- 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이며 상세 기준은 `Plan Rebase` §1~§6을 따른다.
- 금요일 운영도 live 변경은 `1축 canary`만 허용한다.
- `ApplyTarget`은 문서에 명시된 값만 사용하고, parser/workorder가 `remote`를 추정하지 않도록 유지한다.
- 일정은 모두 `YYYY-MM-DD KST`, `Slot`, `TimeWindow`로 고정한다.
- 손익은 `COMPLETED + valid profit_rate`만 사용하고 `full fill`과 `partial fill`은 분리한다.
- 다축 동시 변경 금지, 승인 전 `main` 실주문 변경 금지 규칙을 유지한다.

## 장전 체크리스트 (08:20~)

- [ ] `[ScaleIn0424] PYRAMID zero_qty Stage 1 flag OFF 코드 적재/restart/env 증적 확인` (`Due: 2026-04-24`, `Slot: PREOPEN`, `TimeWindow: 08:20~08:30`, `Track: ScalpingLogic`)
  - 판정 기준: `KORSTOCKSCAN_SCALPING_PYRAMID_ZERO_QTY_STAGE1_ENABLED`가 꺼진 상태로 배포되어야 하며, 재시작 후에도 `flag OFF`가 유지된 증적을 남긴다.
- [ ] `[FastReuseVerify0424] gatekeeper_fast_reuse 실전 호출 로그 확인` (`Due: 2026-04-24`, `Slot: PREOPEN`, `TimeWindow: 08:20~08:35`, `Track: ScalpingLogic`)
  - 판정 기준:
    - `gatekeeper_fast_reuse` 코드 경로가 실전에서 호출되었는지 로그 확인
    - `호출 건수 = 0`이면: signature 조건 과엄격 또는 코드 미도달 분기
    - `호출 건수 > 0`이고 `reuse = 0`이면: signature 일치 조건 완화 검토
    - `reuse > 0`이면: `fast_reuse` 비율 목표(>=10.0%) 대비 평가
  - 판정 연계:
    - `fast_reuse`가 활성화되면 `gatekeeper_eval_ms_p95` 하락 기대
    - p95 하락 동반 시 `quote_fresh_latency_pass_rate` 개선 기대
    - `spread relief canary`의 `fast_reuse` 미개선이면 `quote_fresh` canary 후보 판단으로 후행 이동
  - Rollback: 필요 시 코드 변경은 Plan Rebase §6 guard 전수 대조 후 진행
- [ ] `[ScaleIn0424] PYRAMID zero_qty Stage 1 zero_qty/template_qty/cap_qty/floor_applied 로그 필드 확인` (`Due: 2026-04-24`, `Slot: PREOPEN`, `TimeWindow: 08:30~08:40`, `Track: Plan`)
  - 판정 기준: `ADD_BLOCKED` 또는 `ADD_ORDER_SENT` 로그에 `template_qty`, `cap_qty`, `floor_applied`가 모두 남아야 한다.

## 장중 체크리스트 (09:00~10:00)

- [ ] `[LatencyOps0424] spread relief canary 오전 검증축 고정 확인` (`Due: 2026-04-24`, `Slot: INTRADAY`, `TimeWindow: 09:00~09:10`, `Track: ScalpingLogic`)
  - 판정 기준: 오전 `10:00 KST` 전까지의 주병목 검증축을 `spread relief canary` 하나로 고정하고, `entry_filter_quality/score-promote/HOLDING/EOD-NXT`를 주병목 판정에서 분리한다고 기록한다.
- [ ] `[LatencyOps0424] 제출축 잠금` (`Due: 2026-04-24`, `Slot: INTRADAY`, `TimeWindow: 09:50~10:00`, `Track: ScalpingLogic`)
- 판정 기준: `ai_confirmed`, `entry_armed`, `budget_pass`, `submitted`, `latency_block`, `quote_fresh_latency_blocks`, `quote_fresh_latency_pass_rate`, `full_fill`, `partial_fill`를 기준으로 `spread relief canary 유지`, `효과 미확인`, `롤백 검토` 중 하나로 닫는다.

## 장후 체크리스트 (15:10~15:40) - 주병목 판정

- [ ] `[LatencyOps0424] 오전 제출축 결과 잠금` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 15:10~15:20`, `Track: ScalpingLogic`)
- 판정 기준: 오전 `10:00 KST` checkpoint를 기준으로 `spread relief canary`의 `유지/확대/보류/롤백` 중 하나를 확정한다.
- [ ] `[VisibleResult0424] 금요일 승격 후보 1축 최종선정` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 15:20~15:30`, `Track: Plan`)
- [ ] `[VisibleResult0424] 승격 1축 실행 승인 또는 보류+재시각 확정` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 15:30~15:40`, `Track: ScalpingLogic`)
  - 판정 기준: `승격 실행`이면 축 1개만 선택하고 롤백 가드 포함, `보류`이면 원인 1개와 재실행 시각 1개를 동시에 기록

## 장후 체크리스트 (15:40~17:00) - 후순위 축 Parking

- [ ] `[PlanRebase0424] entry_filter_quality parking 재확인` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 15:40~15:50`, `Track: ScalpingLogic`)
- 판정 기준: `spread relief canary`가 여전히 주병목이면 `entry_filter_quality`는 주병목 축이 아니라 parking 상태로 유지하고, 제출축이 완화됐을 때만 후보 복귀 여부를 판단한다.
- [ ] `[OpsEODSplit0424] EOD/NXT 착수 여부 재판정` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 15:40~15:50`, `Track: ScalpingLogic`)
  - Source: [audit-reports/2026-04-22-plan-rebase-central-audit-review.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-22-plan-rebase-central-audit-review.md)
- 판정 기준: `spread relief canary`가 주병목으로 남아 있으면 출구축으로 승격하지 않고 parking 또는 다음주 이관으로만 닫는다. 착수 시에만 `exit_rule`, `sell_order_status`, `sell_fail_reason`, `is_nxt`, `COMPLETED+valid profit_rate`, full/partial 분리 기준을 함께 기록한다.
- [ ] `[AIPrompt0424] AI 엔진 A/B 재개 여부 판정` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 15:50~16:00`, `Track: AIPrompt`)
  - Source: [2026-04-21-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-21-stage2-todo-checklist.md)
- 판정 기준: `2026-04-21 15:24 KST` 확정 범위(`main-only`, `normal_only`, `COMPLETED+valid profit_rate`, `full/partial 분리`, `ai_confirmed_buy_count/share`, `WAIT65/70/75~79`, `blocked_ai_score`, `ai_confirmed->submitted`)를 그대로 사용한다. 제출병목이 잠긴 뒤에만 A/B 재개를 검토한다.
- [ ] `[ScaleIn0424] PYRAMID zero_qty Stage 1 승인 또는 보류 사유 기록` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:10`, `Track: ScalpingLogic`)
- 판정 기준: `main-only 1축 live`로만 해석한다. `spread relief canary`가 주병목이면 승인 후보로 올리지 않고 parking 상태를 유지한다. `SCALPING/PYRAMID only`, `zero_qty` 감소, `MAX_POSITION_PCT` 위반 0건, `full/partial fill` 체결품질 악화 없음, `floor_applied`가 `buy_qty=1` 예외에만 국한될 때만 승인한다.
- [ ] `[ScaleIn0424] main은 PYRAMID zero_qty Stage 1 code-load(flag OFF)와 live ON 판정을 분리 유지 확인` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:10~16:15`, `Track: Plan`)
  - 판정 기준: `main` 실주문 변경은 승인 전 금지, `flag OFF` 적재와 `live ON` 판정을 같은 슬롯에서 섞지 않는다.
- [ ] `[ScaleIn0424] 물타기축(AVG_DOWN/REVERSAL_ADD) 다음주 착수 승인 또는 보류 사유 기록` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:15~16:25`, `Track: ScalpingLogic`)
- 판정 기준: `shadow 금지 + 단일 live 후보성 재판정`으로 해석한다. `spread relief canary`가 주병목이면 다음주 후보성만 남기고 same-day 승격 후보로는 올리지 않는다. `reversal_add_candidate` 표본 충분성, `buy_qty>=3` 비율, `add_judgment_locked` 교차영향, `split-entry/HOLDING` 관찰축 비간섭 조건이 충족될 때만 다음주 후보로 남긴다.
- [ ] `[HoldingSoftStop0424] soft stop cooldown/threshold 재판정` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:30`, `Track: AIPrompt`)
  - 판정 기준: `2026-04-23` baseline(`soft_stop=1`, `rebound_above_sell_10m=100%`, `rebound_above_buy_10m=0%`, `cooldown_would_block_rate=0%`)을 바탕으로 `same-symbol cooldown` 후보와 threshold 완화 필요성을 분리 판정한다. 주병목 축이 아니라 parking 판정으로 취급한다.
- [ ] `[HolidayCarry0424] HOLDING hybrid 확대 재판정` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:35`, `Track: AIPrompt`)
  - 판정 기준: `holding_action_applied`, `holding_force_exit_triggered`, `holding_override_rule_version_count`, `force_exit_shadow_samples`가 여전히 0이면 확대 논의를 닫고 보류 유지 사유를 고정한다. 이 항목은 주병목 판정이 아니라 parking 판정이다. `holding_action_applied>0` 또는 `holding_override_rule_version_count>0`가 확인될 때만 확대 후보로 복귀시킨다.
- [ ] `[AuditFix0424] 주간 regime 태그 및 평균 거래대금 수준 병기` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:30`, `Track: Plan`)
- [ ] `[AuditFix0424] 1축 유지 규칙 확인` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:35~16:40`, `Track: Plan`)
  - 판정 기준: `1축 유지`, `shadow 금지`, `main-only` 규칙을 함께 재확인한다.
- [ ] `[VisibleResult0424] 기대값 중심 우선지표(거래수/퍼널/blocker/체결품질/missed_upside) 재검증` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:35~16:45`, `Track: Plan`)
- [ ] `[VisibleResult0424] 다음주 PREOPEN 실행지시서에 승격축 1개 반영` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~16:55`, `Track: AIPrompt`)
- [ ] `[OpsFollowup0424] 패턴랩 주간 cron 산출물/로그 정합성 점검` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:55~17:00`, `Track: Plan`)
  - 판정 기준: `logs/claude_scalping_pattern_lab_cron.log`, `logs/gemini_scalping_pattern_lab_cron.log` 에러 없음 + 각 `outputs/` 최신 산출물 갱신 확인
- [ ] 미확정 시 `사유 + 다음 실행시각` 기록 (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:10`, `Track: Plan`)

## 참고 문서

- [2026-04-18-nextweek-validation-axis-table.md](./archive/legacy-tuning-2026-04-06-to-2026-04-20/2026-04-18-nextweek-validation-axis-table.md)
- [2026-04-23-stage2-todo-checklist.md](./2026-04-23-stage2-todo-checklist.md)
- [2026-04-20-stage2-todo-checklist.md](./2026-04-20-stage2-todo-checklist.md)
- [2026-04-21-stage2-todo-checklist.md](./2026-04-21-stage2-todo-checklist.md)
- [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md)
- [plan-korStockScanPerformanceOptimization.performance-report.md](./plan-korStockScanPerformanceOptimization.performance-report.md)
- [2026-04-20-scale-in-qty-logic-final-review-v1.1.md](./archive/legacy-tuning-2026-04-06-to-2026-04-20/2026-04-20-scale-in-qty-logic-final-review-v1.1.md)

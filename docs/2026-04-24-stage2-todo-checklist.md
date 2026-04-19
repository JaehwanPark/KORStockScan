# 2026-04-24 Stage 2 To-Do Checklist

## 목적

- `2026-04-20~2026-04-23` 검증 결과를 기반으로 금요일에 결론을 미루지 않고 닫는다.
- 금요일 운영축은 `승격 1축 실행` 또는 `보류+재시각` 중 하나로 고정한다.
- 다축 동시 변경을 금지하고 `한 번에 한 축 canary` 원칙을 유지한다.
- 주간 판정에는 regime 태그(저변동/평상/고변동)와 조건부 유효범위를 함께 기록한다.

## 장후 체크리스트 (15:30~)

- [ ] `[VisibleResult0424] 금요일 승격 후보 1축 최종선정` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 15:30~15:40`, `Track: Plan`)
- [ ] `[VisibleResult0424] 승격 1축 실행 승인 또는 보류+재시각 확정` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 15:40~15:50`, `Track: ScalpingLogic`)
  - 판정 기준: `승격 실행`이면 축 1개만 선택하고 롤백 가드 포함, `보류`이면 원인 1개와 재실행 시각 1개를 동시에 기록
- [ ] `[AuditFix0424] 주간 regime 태그 및 평균 거래대금 수준 병기` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 15:50~15:55`, `Track: Plan`)
- [ ] `[AuditFix0424] canary 1축 유지 + 독립축 shadow 병렬허용 규칙 확인` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 15:55~16:00`, `Track: Plan`)
- [ ] `[VisibleResult0424] 기대값 중심 우선지표(거래수/퍼널/blocker/체결품질/missed_upside) 재검증` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:10`, `Track: Plan`)
- [ ] `[VisibleResult0424] 다음주 PREOPEN 실행지시서에 승격축 1개 반영` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:10~16:20`, `Track: AIPrompt`)
- [ ] `[OpsFollowup0424] 패턴랩 주간 cron 산출물/로그 정합성 점검` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:20~16:25`, `Track: Plan`)
  - 판정 기준: `logs/claude_scalping_pattern_lab_cron.log`, `logs/gemini_scalping_pattern_lab_cron.log` 에러 없음 + 각 `outputs/` 최신 산출물 갱신 확인
- [ ] 미확정 시 `사유 + 다음 실행시각` 기록 (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 16:20~16:30`, `Track: Plan`)

## 참고 문서

- [2026-04-18-nextweek-validation-axis-table.md](./2026-04-18-nextweek-validation-axis-table.md)
- [2026-04-23-stage2-todo-checklist.md](./2026-04-23-stage2-todo-checklist.md)
- [2026-04-20-stage2-todo-checklist.md](./2026-04-20-stage2-todo-checklist.md)
- [2026-04-21-stage2-todo-checklist.md](./2026-04-21-stage2-todo-checklist.md)
- [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md)
- [plan-korStockScanPerformanceOptimization.performance-report.md](./plan-korStockScanPerformanceOptimization.performance-report.md)

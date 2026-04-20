# 2026-04-22 Stage 2 To-Do Checklist

## 목적

- `same-symbol split-entry cooldown`은 앞선 split-entry 축과 독립 관찰이 가능할 때만 D+2 canary 착수 후보로 본다.
- `AIPrompt 작업 11 HOLDING critical 전용 경량 프롬프트 분리` 미완료분이 있으면 오늘 보강 실행한다.
- 속도 개선축을 정확도 개선축 뒤에 무기한 두지 않는다.
- `HOLDING schema 변경(D+2)` 성과판정을 오늘 최종 수행한다.

## 장후 체크리스트 (15:30~)

- [ ] `[AuditFix0422] same-symbol split-entry cooldown canary 1일차 착수 또는 보류 기록` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 15:30~15:40`, `Track: ScalpingLogic`)
  - 판정 기준: `rebase/즉시 재평가` 관찰축과 원인귀속이 분리될 때만 착수, 아니면 보류 사유와 재시각 기록
  - 선행 메모 (`2026-04-20 PREOPEN`): `D+2 이관 확정`. `rebase/즉시 재평가`와 독립 관찰 가능할 때만 착수
- [ ] `AIPrompt 작업 11 HOLDING critical 전용 경량 프롬프트 분리` 미완료분 보강 (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 15:40~15:50`, `Track: AIPrompt`)
  - 실행 메모: shadow 비교표에는 `schema 변경 효과`와 `경량 프롬프트 효과`를 별도 컬럼으로 남긴다.
- [ ] `[AuditFix0422] HOLDING 성과 최종판정(missed_upside_rate/capture_efficiency/GOOD_EXIT)` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 15:50~16:00`, `Track: AIPrompt`)
- [ ] `[HolidayCarry0419] AIPrompt 작업 10 HOLDING hybrid 적용` 확대 여부 최종판정 (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:10`, `Track: AIPrompt`)
  - 판정 기준: `missed_upside_rate/capture_efficiency/GOOD_EXIT`와 `holding_action_applied/holding_force_exit_triggered` 운영 로그가 모두 확보됐을 때만 확대 여부 결정
- [ ] `[AuditFix0422] HOLDING 지표 우선순위(primary/secondary) 고정 기록` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 16:10~16:20`, `Track: Plan`)
- [ ] `[PlanSync0422] AI 엔진 A/B 원격 preflight 체크리스트 항목 확정` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 16:20~16:30`, `Track: AIPrompt`)
  - 판정 기준: `2026-04-23 POSTCLOSE`에 수행할 원격 정합화 범위(설정값/관찰축/롤백가드)와 `2026-04-24` 착수 여부 판정 게이트를 문서 고정
- [ ] `[VisibleResult0422] legacy shadow canary 1일차 결과 기반 live 승격/롤백 판정` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:40`, `Track: Plan`)
  - 판정 기준: `승격 1축` 또는 `롤백` 중 하나로 강제 종료하고, shadow 복귀는 금지
- [ ] `[PlanSync0422] legacy shadow 잔여항목 0화 확인(미전환 shadow 없음)` (`Due: 2026-04-22`, `Slot: POSTCLOSE`, `TimeWindow: 16:40~16:50`, `Track: Plan`)
  - 판정 기준: 남은 shadow 항목이 있으면 `폐기` 또는 `기존 live 축 병합`으로 닫고 독립 shadow 상태를 남기지 않는다
- [ ] 미완료 시 `사유 + 다음 실행시각` 기록

## 참고 문서

- [2026-04-21-stage2-todo-checklist.md](./2026-04-21-stage2-todo-checklist.md)
- [2026-04-19-aiprompt-task8-task10-holiday-recheck.md](./2026-04-19-aiprompt-task8-task10-holiday-recheck.md)
- [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md)
- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)
- [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md)
- [plan-korStockScanPerformanceOptimization.performance-report.md](./plan-korStockScanPerformanceOptimization.performance-report.md)

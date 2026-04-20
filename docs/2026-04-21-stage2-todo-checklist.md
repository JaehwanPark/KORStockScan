# 2026-04-21 Stage 2 To-Do Checklist

## 목적

- `2026-04-20 rebase` 1일차 결과를 기준으로 다음 split-entry 축 착수 가능 여부를 먼저 닫는다.
- `split-entry 즉시 재평가`는 전일 `N_min/Δ_min/false_entry_rate` 기준이 고정된 경우에만 오늘 canary 착수 후보로 본다.
- `split-entry leakage`와 `HOLDING` 관측/기준정리를 `작업 12`보다 먼저 본다.
- `2026-04-20` 이후 신규 관찰축/보완축은 `shadow`를 추가하지 않고 `canary-only`로 판정한다.
- `AIPrompt 작업 12 Raw 입력 축소 A/B 점검` 범위를 확정한다.
- `작업 10/11` 결과를 본 뒤 입력 축소 범위를 뒤로 미루지 않고 닫는다.
- `HOLDING 성과 최종판정`은 schema 변경 버퍼를 두고 `2026-04-22`로 이관한다.

## 장전 체크리스트 (08:00~)

- [ ] `[AuditFix0421] gatekeeper fast_reuse 완화 구현증거 및 목표 유지 여부 장전 확인` (`Due: 2026-04-21`, `Slot: PREOPEN`, `TimeWindow: 08:00~08:10`, `Track: ScalpingLogic`)
  - 판정 기준: [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)의 `_build_gatekeeper_fast_signature()` 변경 전/후 증거를 확인한다. 변경증거가 불충분하면 `gatekeeper_fast_reuse_ratio >= 10.0%` 목표는 판정 대상에서 제외하고 보류 사유를 기록한다.
- [ ] `[Governance0421] partial fill min_fill_ratio canary 승인 로그 고정 + 유지/롤백 조건 점검` (`Due: 2026-04-21`, `Slot: PREOPEN`, `TimeWindow: 08:10~08:20`, `Track: ScalpingLogic`)
  - 판정 기준: `SCALP_PARTIAL_FILL_RATIO_CANARY_ENABLED=True` 사용자 승인 로그를 고정한다. 승인 상태를 전제로 유지/롤백 조건만 점검하고, 무승인 예외로 재분류하지 않는다.
- [ ] `[AuditFix0421] 테스트 카운트 불일치 재현 및 증적 기록` (`Due: 2026-04-21`, `Slot: PREOPEN`, `TimeWindow: 08:20~08:30`, `Track: Plan`)
  - 판정 기준: 아래 4개 파일 pytest를 재실행해 `N passed`를 고정한다. 기존 `16 passed` 주장과 불일치하면 장후 보고에서 정정 근거를 함께 기록한다.
  - 실행 명령: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_ai_engine_openai_v2_audit_fields.py src/tests/test_scalping_feature_packet.py src/tests/test_state_handler_fast_signatures.py src/tests/test_gatekeeper_fast_reuse_age.py`

## 장후 체크리스트 (15:20~)

- [ ] `[AuditResponse0421] 감사 응답 반영 상태와 timestamp/evidence 분리 검증` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 15:20~15:30`, `Track: Plan`)
  - 판정 기준: `체크리스트 예정 TimeWindow`, `실제 실행시각`, `근거 로그/스냅샷 시각`을 분리 기록한다. 사후 일괄 판정 시각은 실제 실행시각으로 쓰지 않는다.
- [ ] `[AuditFix0421] split-entry 즉시 재평가 canary 1일차 착수 또는 보류 기록` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 15:30~15:40`, `Track: ScalpingLogic`)
  - 판정 기준: `N_min/Δ_min` 충족 + `false_entry_rate` 상한 확정 시에만 canary 착수, 아니면 보류 사유와 재시각 기록
  - 선행 메모 (`2026-04-20 PREOPEN`): `D+1 이관 확정`. `N_min=50`, `Δ_min=+3.0%p`, `PrimaryMetric=budget_pass_to_submitted_rate` 미충족 시 착수 금지
- [ ] `[VisibleResult0421] split-entry leakage canary 승격 또는 보류 사유 기록` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 15:40~15:50`, `Track: ScalpingLogic`)
- [ ] `[AuditFix0421] HOLDING baseline 재계산 + 관측버퍼(D+1) 확인` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 15:50~16:00`, `Track: AIPrompt`)
- [ ] `AIPrompt 작업 12 Raw 입력 축소 A/B 점검` 범위 확정 (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:10`, `Track: AIPrompt`)
- [ ] `[VisibleResult0421] 다음 영업일 승격축 1개 고정 또는 보류 사유 기록` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:10~16:20`, `Track: Plan`)
- [ ] `[DataAudit0421] baseline source-of-truth audit 최종닫힘 및 rollback 기준 소스 고정` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:20~16:30`, `Track: Plan`)
  - 판정 기준: `trade_review=당일 손익`, `performance_tuning=퍼널/체결품질`, `post_sell_feedback=HOLDING`, `missed_entry_counterfactual=기회비용`을 고정하고 `rolling trend`와 문서 파생값을 rollback 기준에서 배제
  - 선행 메모 (`2026-04-20`): `04-06~04-17` raw 재감사 결과 `latency_ratio`가 `0.985~0.998`로 지속 고비율이고 `partial_fill_completed_avg_profit_rate`도 `04-14~-04-17` 연속 음수여서, 우선축은 `same_symbol_repeat`보다 `latency + partial/rebase + soft-stop` 재정렬이 우선
- [ ] `[PlanSync0421] 원격 canary 보류 유지 + AI 엔진 A/B 전환 일정 고정` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:20~16:30`, `Track: Plan`)
  - 판정 기준: 현재 튜닝 축에는 원격 신규 canary를 열지 않고, `A/B preflight`를 `2026-04-23 POSTCLOSE`로 고정
- [ ] `[PlanSync0421] 개별종목(에이럭스) 관찰축 4분해 유지 여부 재확인` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:40`, `Track: Plan`)
  - 판정 기준: `EntryGate/Latency/Liquidity/HoldingExit` 4축 표본이 충분하지 않으면 scale-in/holding/latency 로직 변경 모두 보류
- [ ] `[VisibleResult0421] legacy shadow 1순위 축 canary 착수 (HOLDING band 또는 WATCHING shared prompt 중 1축)` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:40~16:50`, `Track: AIPrompt`)
  - 판정 기준: `2026-04-20` 전수조사 표본수 상위 1축만 선택해 canary 착수, 나머지는 동일 세션에서는 미착수
  - 롤백 가드: `trade_count N_min=50` 미충족 또는 `reject_rate/partial_fill_ratio/latency_p95` 한계 초과 시 즉시 OFF
- [ ] `[AuditFix0421] legacy shadow 저표본 축(same_symbol/split_entry/partial_only_timeout) 폐기 또는 추후 live 병합 경로 고정` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:50~17:00`, `Track: ScalpingLogic`)
  - 판정 기준: `표본 0~2` 축은 standalone canary를 열지 않고, 기존 split-entry live 후보축에 병합하거나 폐기로 닫는다
- [ ] `[QuantVerify0421] 감사 응답 정량 기대효과 검증` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:20`, `Track: Plan`)
  - 기준선: `2026-04-20` `soft_stop_count=18`, `partial_fill_events=31`, `position_rebased_after_fill_events=44`, `partial_fill_completed_avg_profit_rate=-0.25`, `gatekeeper_fast_reuse_ratio=0.0%`, `gatekeeper_eval_ms_p95=19917ms`, `latency_block_events/budget_pass_events=838/866`
  - 판정 기준: `soft_stop_count/partial_fill_events <= 0.46`, `position_rebased_after_fill_events/partial_fill_events <= 1.15`, `partial_fill_completed_avg_profit_rate >= -0.15`, `gatekeeper_fast_reuse_ratio >= 10.0%`, `gatekeeper_eval_ms_p95 <= 15900ms`, `ai_result_source=- 신규 표본 0건`
  - 표본 기준: `partial_fill_events < 20` 또는 `gatekeeper_eval_samples < 50`이면 hard pass/fail이 아니라 방향성 판정으로 기록한다.
- [ ] `[OpsVerify0421] system metric sampler 장중 coverage 검증` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 17:20~17:25`, `Track: Plan`)
  - 판정 기준: `logs/system_metric_samples.jsonl`에서 `09:00~15:30 KST` 샘플 `>= 360`, 최대 샘플 간격 `<= 180초`, CPU/load/memory/io/top process 필드 누락 `0건`
- [ ] `[AuditFix0421] HOLDING 성과판정 D+2(2026-04-22) 이관 기록` (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:20~16:25`, `Track: AIPrompt`)
- [ ] 범위 확정 실패 시 `사유 + 다음 실행시각` 기록 (`Due: 2026-04-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:30`, `Track: AIPrompt`)

## 참고 문서

- [2026-04-19-stage2-todo-checklist.md](./2026-04-19-stage2-todo-checklist.md)
- [2026-04-17-midterm-tuning-performance-report.md](./2026-04-17-midterm-tuning-performance-report.md)
- [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md)
- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)
- [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md)
- [plan-korStockScanPerformanceOptimization.performance-report.md](./plan-korStockScanPerformanceOptimization.performance-report.md)

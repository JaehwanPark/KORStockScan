# 2026-04-20 Stage 2 To-Do Checklist

## 목적

- `2026-04-17 최고손실일`에서 확보한 고밀도 표본으로 `split-entry leakage` 1일차 판정을 먼저 닫는다.
- `split-entry` 3개 서브축은 감사표 권고대로 같은 날 병렬 가동하지 않고 `rebase -> 즉시 재평가 -> cooldown` 순차 도입 원칙을 유지한다.
- `HOLDING action schema / HOLDING critical` shadow-only 착수를 같은 날 밀어 다음주 수익전환 축을 연다.
- `latency/tag/threshold` 추가 완화는 `quote_stale` 우세와 `split-entry` 누수 분리 전에는 승격하지 않는다.
- `2026-04-18~2026-04-19(휴일)` 이관 항목을 장후 슬롯에서 우선 처리한다.
- `AIPrompt 작업 11 HOLDING critical 전용 경량 프롬프트 분리`를 착수한다.
- 속도 개선축을 정확도 개선축 뒤에 다시 미루지 않는다.
- 금요일 급손실 완화 목적의 `SCALPING_MAX_BUY_BUDGET_KRW 1,600,000` 단일축 canary를 판정한다.

## 장전 체크리스트 (08:00~09:00)

- [ ] `[VisibleResult0420] split-entry rebase 수량 정합성 shadow 1일차 판정` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:00~08:10`, `Track: ScalpingLogic`)
- [ ] `[AuditFollowup0418] remote runtime 코드 적재 상태 점검(작업9 반영분)` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:00~08:05`, `Track: AIPrompt`)
  - 실행 메모: `songstockscan`에서 `scalping_feature_packet.py` 존재 + `ai_engine.py` import 경로 정상 + `bot_main.py` 기동 시 예외 없음 확인
- [ ] `[AuditFix0420] split-entry 즉시 재평가 shadow D+1 이관 확정` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:10~08:15`, `Track: ScalpingLogic`)
  - 판정 기준: `2026-04-20`에는 미활성 유지, `rebase` 1일차 결과와 `false_entry_rate` 상한이 숫자로 고정될 때만 `2026-04-21` shadow 착수
- [ ] `[AuditFix0420] same-symbol split-entry cooldown shadow D+2 이관 확정` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:15~08:20`, `Track: ScalpingLogic`)
  - 판정 기준: `2026-04-20`에는 미활성 유지, `rebase/즉시 재평가`와 독립 관찰이 가능할 때만 `2026-04-22` shadow 착수
- [ ] `[AuditFix0420] 각 판정행 N_min/Δ_min/PrimaryMetric 확정` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:20~08:30`, `Track: Plan`)
- [ ] `[VisibleResult0420] latency canary bugfix-only 재판정 및 tag 완화 보류/승인` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:30~08:35`, `Track: ScalpingLogic`)
  - 실행 메모: baseline 관측창은 최소 `직전 5영업일 동일 시간대 p50/p95`로 고정 후 판정
- [ ] `[AuditFix0420] 공통 rollback trigger 수치표 확정` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:35~08:45`, `Track: ScalpingLogic`)
- [ ] `[RiskSize0420] SCALPING_MAX_BUY_BUDGET_KRW=1,600,000 적용 상태/기동 반영 확인` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:40~08:45`, `Track: ScalpingLogic`)
- [ ] `[VisibleResult0420] HOLDING action schema shadow-only 착수` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:45~09:00`, `Track: AIPrompt`)
  - 실행 메모: 성과판정은 `2026-04-22 POSTCLOSE`까지 미루고, 오늘은 rollback guard와 baseline 재계산 경로만 고정
- [ ] `[VisibleResult0420] live 승격 후보는 split-entry leakage 1축만 유지 확인` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: Plan`)

## 장후 체크리스트 (15:30~)

- [ ] `[VisibleResult0420] partial-only timeout shadow 1일차 판정` (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 15:30~15:40`, `Track: ScalpingLogic`)
  - 실행 메모: timeout 후 `Δt=5분` 내 동일 종목·호가 체결 여부 counterfactual을 함께 기록
- [ ] `[AuditFollowup0418] main runtime OPENAI 라우팅/감사필드 실표본 확인` (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 15:40~15:50`, `Track: AIPrompt`)
  - 실행 메모: `ai_confirmed/ai_holding_review`에서 `scalp_feature_packet_version + 4개 *_sent` 키를 확인
- [ ] `[AuditFollowup0418] main runtime OpenAI 모델 식별자 검증/수정` (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 15:50~16:00`, `Track: AIPrompt`)
  - 실행 메모: `gpt-5.4-nano` 유효성 확인 또는 교정
- [ ] `[AuditFollowup0418] 작업 6/7 보류 유지 또는 착수 전환 재판정` (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:10`, `Track: AIPrompt`)
  - 실행 메모: `HOLDING action schema shadow-only` 선행 범위와 충돌 여부를 기준으로 판정
- [ ] `[HolidayCarry0418] AIPrompt 작업 9 정량형 수급 피처 이식 1차` 실표본 기준 1차 결과/확대 여부 판정 (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 16:10~16:20`, `Track: AIPrompt`)
  - 선행 메모 (`2026-04-18 10:27 KST`): 공통 helper + Gemini/OpenAI 공용 패킷 + OpenAI `analyze_target` 감사 필드 주입까지 반영 완료
- [ ] `[HolidayCarry0419] AIPrompt 작업 10 HOLDING hybrid 적용` 1차 결과 평가 / 확대 여부 판정 (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 16:20~16:30`, `Track: AIPrompt`)
  - 실행 메모: 휴일 재점검 기준 `2026-04-20`에는 `shadow-only 유지 / 확대 보류` 1차 판정을 우선한다.
  - 필수 관찰축: `holding_action_applied`, `holding_force_exit_triggered`, `holding_override_rule_version`, `FORCE_EXIT` shadow 표본, `trailing 충돌률`
  - 미충족 시 다음 액션: `2026-04-22 POSTCLOSE` 최종판정 항목으로 넘기고 보류 사유를 같은 제목으로 기록
- [ ] `[HolidayCarry0419] AIPrompt 작업 8 감사용 핵심값 3종 투입` 미완료 시 `사유 + 다음 실행시각` 기록 (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:40`, `Track: AIPrompt`)
  - 실행 메모: `buy_pressure_10t_sent`, `distance_from_day_high_pct_sent`, `intraday_range_pct_sent` 중 하나라도 확인되지 않으면 완료 처리 금지
  - 판정 기준: 값 주입 여부와 별도로 main runtime 감사 로그 3종이 모두 남아야 완료 후보로 본다
- [ ] `AIPrompt 작업 11 HOLDING critical 전용 경량 프롬프트 분리` 착수 (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 16:40~17:00`, `Track: AIPrompt`)
- [ ] `[VisibleResult0420] HOLDING shadow 1일차 missed_upside/capture_efficiency 판정 기준 고정` (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:10`, `Track: AIPrompt`)
- [ ] `[VisibleResult0420] 장후 리포트 우선지표 순서(거래수/퍼널/blocker/체결품질/missed_upside/손익) 준수 확인` (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 17:10~17:15`, `Track: Plan`)
- [ ] `[RiskSize0420] budget cap 1일차 효과 판정(거래수/퍼널/full vs partial fill/missed_upside)` (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 17:15~17:25`, `Track: ScalpingLogic`)
- [ ] `[RiskSize0420] 동적 튜닝 대상화 여부 확정(승격/보류+재시각)` (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 17:25~17:35`, `Track: Plan`)
- [ ] `[PerfRpt0420] 정기 성과측정보고서 첫 운영 업데이트` (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 17:35~17:45`, `Track: Plan`)
  - 판정 기준: `plan-korStockScanPerformanceOptimization.performance-report.md`에 `2026-04-20` 장후 실제값(`거래수/퍼널/blocker/체결품질/missed_upside/손익`)을 첫 운영본으로 반영
- [ ] `[Workorder0420] 실행 변경사항/성과보고 기준 문서를 workorder 소스 문맥에 연결` (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 17:45~17:50`, `Track: Plan`)
  - 실행 메모: 다음 `codex_daily_workorder` 생성 시 `execution-delta`, `performance-report`를 참조문서로 포함하도록 Source 문맥을 유지
- [ ] 미착수 시 `사유 + 다음 실행시각` 기록 (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 17:50~18:00`, `Track: AIPrompt`)

## 참고 문서

- [2026-04-19-stage2-todo-checklist.md](./2026-04-19-stage2-todo-checklist.md)
- [2026-04-19-aiprompt-task8-task10-holiday-recheck.md](./2026-04-19-aiprompt-task8-task10-holiday-recheck.md)
- [2026-04-17-stage2-todo-checklist.md](./2026-04-17-stage2-todo-checklist.md)
- [2026-04-17-midterm-tuning-performance-report.md](./2026-04-17-midterm-tuning-performance-report.md)
- [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md)
- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)
- [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md)
- [plan-korStockScanPerformanceOptimization.performance-report.md](./plan-korStockScanPerformanceOptimization.performance-report.md)
- [plan-korStockScanPerformanceOptimization.qna.md](./plan-korStockScanPerformanceOptimization.qna.md)

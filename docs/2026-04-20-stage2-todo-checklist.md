# 2026-04-20 Stage 2 To-Do Checklist

## 목적

- `2026-04-17 최고손실일`에서 확보한 고밀도 표본으로 `split-entry leakage` 1일차 판정을 먼저 닫는다.
- `HOLDING action schema / HOLDING critical` shadow-only 착수를 같은 날 밀어 다음주 수익전환 축을 연다.
- `latency/tag/threshold` 추가 완화는 `quote_stale` 우세와 `split-entry` 누수 분리 전에는 승격하지 않는다.
- `2026-04-18~2026-04-19(휴일)` 이관 항목을 장후 슬롯에서 우선 처리한다.
- `AIPrompt 작업 11 HOLDING critical 전용 경량 프롬프트 분리`를 착수한다.
- 속도 개선축을 정확도 개선축 뒤에 다시 미루지 않는다.

## 장전 체크리스트 (08:00~09:00)

- [ ] `[VisibleResult0420] split-entry rebase 수량 정합성 shadow 1일차 판정` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:00~08:10`, `Track: ScalpingLogic`)
- [ ] `[AuditFollowup0418] remote runtime 코드 적재 상태 점검(작업9 반영분)` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:00~08:05`, `Track: AIPrompt`)
  - 실행 메모: `songstockscan`에서 `scalping_feature_packet.py` 존재 + `ai_engine.py` import 경로 정상 + `bot_main.py` 기동 시 예외 없음 확인
- [ ] `[VisibleResult0420] split-entry 즉시 재평가 shadow 1일차 판정` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:10~08:20`, `Track: ScalpingLogic`)
- [ ] `[VisibleResult0420] same-symbol split-entry cooldown shadow 1일차 판정` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:20~08:30`, `Track: ScalpingLogic`)
- [ ] `[VisibleResult0420] latency canary bugfix-only 재판정 및 tag 완화 보류/승인` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:30~08:40`, `Track: ScalpingLogic`)
- [ ] `[VisibleResult0420] HOLDING action schema shadow-only 착수` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:40~09:00`, `Track: AIPrompt`)
- [ ] `[VisibleResult0420] live 승격 후보는 split-entry leakage 1축만 유지 확인` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: Plan`)

## 장후 체크리스트 (15:30~)

- [ ] `[VisibleResult0420] partial-only timeout shadow 1일차 판정` (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 15:30~15:40`, `Track: ScalpingLogic`)
- [ ] `[AuditFollowup0418] main runtime OPENAI 라우팅/감사필드 실표본 확인` (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 15:40~15:50`, `Track: AIPrompt`)
  - 실행 메모: `ai_confirmed/ai_holding_review`에서 `scalp_feature_packet_version + 4개 *_sent` 키를 확인
- [ ] `[AuditFollowup0418] main runtime OpenAI 모델 식별자 검증/수정` (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 15:50~16:00`, `Track: AIPrompt`)
  - 실행 메모: `gpt-5.4-nano` 유효성 확인 또는 교정
- [ ] `[AuditFollowup0418] 작업 6/7 보류 유지 또는 착수 전환 재판정` (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:10`, `Track: AIPrompt`)
  - 실행 메모: `HOLDING action schema shadow-only` 선행 범위와 충돌 여부를 기준으로 판정
- [ ] `[HolidayCarry0418] AIPrompt 작업 9 정량형 수급 피처 이식 1차` 실표본 기준 1차 결과/확대 여부 판정 (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 16:10~16:20`, `Track: AIPrompt`)
  - 선행 메모 (`2026-04-18 10:27 KST`): 공통 helper + Gemini/OpenAI 공용 패킷 + OpenAI `analyze_target` 감사 필드 주입까지 반영 완료
- [ ] `[HolidayCarry0419] AIPrompt 작업 10 HOLDING hybrid 적용` 1차 결과 평가 / 확대 여부 판정 (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 16:20~16:30`, `Track: AIPrompt`)
- [ ] `[HolidayCarry0419] AIPrompt 작업 8 감사용 핵심값 3종 투입` 미완료 시 `사유 + 다음 실행시각` 기록 (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:40`, `Track: AIPrompt`)
- [ ] `AIPrompt 작업 11 HOLDING critical 전용 경량 프롬프트 분리` 착수 (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 16:40~17:00`, `Track: AIPrompt`)
- [ ] `[VisibleResult0420] HOLDING shadow 1일차 missed_upside/capture_efficiency 판정 기준 고정` (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:10`, `Track: AIPrompt`)
- [ ] `[VisibleResult0420] 장후 리포트 우선지표 순서(거래수/퍼널/blocker/체결품질/missed_upside/손익) 준수 확인` (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 17:10~17:15`, `Track: Plan`)
- [ ] 미착수 시 `사유 + 다음 실행시각` 기록 (`Due: 2026-04-20`, `Slot: POSTCLOSE`, `TimeWindow: 17:15~17:25`, `Track: AIPrompt`)

## 참고 문서

- [2026-04-19-stage2-todo-checklist.md](./2026-04-19-stage2-todo-checklist.md)
- [2026-04-17-stage2-todo-checklist.md](./2026-04-17-stage2-todo-checklist.md)
- [2026-04-17-midterm-tuning-performance-report.md](./2026-04-17-midterm-tuning-performance-report.md)
- [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md)
- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)

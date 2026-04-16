# 2026-04-17 Stage 2 To-Do Checklist

## 목적

- `P2 HOLDING 포지션 컨텍스트 주입`은 `착수` 또는 `보류 사유 기록` 둘 중 하나로 닫는다.
- `WATCHING 선통과 조건 문맥 주입`도 같은 날 병렬 착수 또는 보류 사유 기록으로 닫는다.
- `P1`에서 이미 본 결과를 기준으로 `P2`로 넘어갈지, `P1` 보강을 하루 더 할지 결정한다.
- `AIPrompt 작업 9 정량형 수급 피처 이식 1차` helper scope를 확정한다.

## 장후 체크리스트 (15:30~)

- [ ] `AIPrompt P2 HOLDING 포지션 컨텍스트 주입` 착수 또는 보류 사유 기록
- [ ] `AIPrompt 작업 7 WATCHING 선통과 조건 문맥 주입` 착수 또는 보류 사유 기록
- [ ] `AIPrompt 작업 9 정량형 수급 피처 이식 1차` helper scope 확정
- [ ] `P1` 보류 시 `사유 + 다음 실행시각` 기록

## 장전 체크리스트 (08:00~09:00)

- [ ] `[Checklist0417] entry_pipeline latest/event 이중 지표 정합성 확인` (`Due: 2026-04-17`, `Slot: PREOPEN`, `TimeWindow: 08:00~08:10`, `Track: Plan`)
  - 판정 기준: `entry_pipeline_flow`에서 최신 시도 기준(`budget_pass_stocks`)과 이벤트 기준(`budget_pass_events`)이 함께 보이고, 장전 판정은 이벤트 기준 퍼널로만 내린다.
  - 근거: `budget_pass_stocks=2`는 최신 시도 요약값이라 실병목 판단을 왜곡했다.
  - 다음 액션: `budget_pass_event_to_submitted_rate`와 `latency_block_events`를 첫 판정 분모로 고정
- [ ] `[Checklist0417] latency canary signal-score 정규화 bugfix 반영 검증` (`Due: 2026-04-17`, `Slot: PREOPEN`, `TimeWindow: 08:00~08:15`, `Track: ScalpingLogic`)
  - 판정 기준: `signal_strength=0.x` 입력이 canary 비교 시 점수(`0~100`)로 정규화되고, 로컬 회귀 테스트가 통과한다.
  - 근거: `2026-04-16` 실데이터에서 `latency_canary_applied=0`, `latency_canary_reason=low_signal 1949`로 버그 징후 확인
  - 다음 액션: 장중 첫 30분 `latency_canary_applied` 실제 발생 여부와 `low_signal` 감소 여부를 확인
- [ ] `[Checklist0417] latency canary 추가 완화(tag/min_score) 보류 또는 1축 승인` (`Due: 2026-04-17`, `Slot: PREOPEN`, `TimeWindow: 08:15~08:30`, `Track: ScalpingLogic`)
  - 판정 기준: bugfix-only 관찰로 충분한지, 아니면 `tag expansion` 1축만 추가할지 결정한다.
  - 근거: 동일 데이터 기준 bugfix-only 잠재 복구 `110건`, `min_score 80` 완화는 잠재 복구 `490건`으로 리스크 차이가 크다
  - 다음 액션: 승인 시 `tag` 1축만 canary, 미승인 시 bugfix-only 유지
- [ ] `[Checklist0417] 모델별 A/B 테스트 별도 시나리오 초안 확정` (`Due: 2026-04-17`, `Slot: PREOPEN`, `TimeWindow: 08:00~08:30`)
  - 판정 기준: 실험군/대조군, 중단조건, 평가지표(거래수/퍼널/blocker/체결품질) 문서 확정
  - 근거: 2026-04-16 운영반영과 실험축 분리 원칙
  - 다음 액션: 확정안 기준으로 POSTCLOSE 비교 템플릿 고정
- [ ] `[Checklist0417] SCALP loss_fallback_probe add_judgment_locked 우회 canary 검증` (`Due: 2026-04-17`, `Slot: PREOPEN`, `TimeWindow: 08:00~08:10`)
  - 판정 기준: 손절 직전 `loss_fallback_probe`에서 `gate_reason=add_judgment_locked` 비중이 0%로 내려갔는지 확인
  - 근거: 기존 lock 공유로 fallback 관찰 타이밍이 구조적으로 차단됨
  - 다음 액션: 실패 시 즉시 롤백(`skip_add_judgment_lock=False`) 또는 별도 lock key 분리안 확정
- [ ] `[Checklist0417] SCALP 손절 직전 fallback 후보(loss_fallback_probe) 전일 로그 판정` (`Due: 2026-04-17`, `Slot: PREOPEN`, `TimeWindow: 08:00~08:20`)
  - 판정 기준: `loss_fallback_probe`에서 후보(`fallback_candidate=true`) 빈도/조건을 손절건과 대조해 유효성 판정
  - 근거: 한화오션 손절 리뷰에서 fallback 기회 계측 필요성 확인
  - 다음 액션: 1) observe-only 유지 또는 2) 실전 전환 승인안 작성
- [ ] `[Checklist0417] SCALP 손절 fallback 실전 전환 여부 결정(기본 OFF)` (`Due: 2026-04-17`, `Slot: PREOPEN`, `TimeWindow: 08:20~09:00`)
  - 판정 기준: `SCALP_LOSS_FALLBACK_ENABLED/OBSERVE_ONLY` 토글값 확정 및 운영기록 반영
  - 근거: 손절 축은 체결 리스크가 높아 관찰 근거 없이 즉시 ON 금지
  - 다음 액션: 승인 시 `observe_only=False` 전환, 미승인 시 관찰기간 연장
- [ ] `[Checklist0417] SCANNER fallback timeout 일반 SCANNER 확장 shadow 판정` (`Due: 2026-04-17`, `Slot: PREOPEN`, `TimeWindow: 08:30~09:00`)
  - 판정 기준: 현행 `SCANNER fallback` 전용 조기정리 로직과 별개로 일반 SCANNER 장기 표류 shadow 조건/exit_rule을 확정
  - 근거: 롯데쇼핑/올릭스는 fallback 한정 로직으로 직접 커버되지 않음
  - 다음 액션: 승인 시 원격 shadow 우선 반영, 미승인 시 보류 사유와 재판정 시각 기록

### 장전 사전검증 (2026-04-16 15:36 KST, 모니터링 기준)

1. 판정: 내일 장전에서 **다축 신규 튜닝 승인 요건은 미충족**이지만, `latency canary signal-score` bugfix-only 반영은 가능하다.
- 근거: 최신 시도 기준 `budget_pass_stocks=2`는 착시였고, 이벤트 기준으로는 `budget_pass_events=3923`, `submitted_events=24`, `budget_pass_event_to_submitted_rate=0.6%`다. 동시에 `latency_canary_applied=0`, `latency_canary_reason=low_signal 1949`로 구현 버그가 확인됐다.
- 다음 액션: PREOPEN은 bugfix-only + 지표 정합성 보정까지 진행하고, 추가 완화는 1축만 재판정한다.

2. 판정: `COMPLETED + valid profit_rate` 집계 품질 게이트는 **충족**.
- 근거: `trade_review_2026-04-16` 기준 `completed_trades=20`, `valid_profit_rate_count=20`, full/partial 분리 이벤트(`5/27`) 확인.
- 다음 액션: 손익 평가는 동일 필터(`COMPLETED + valid profit_rate`)만 유지.

3. 판정: 지연/보유 축은 **관측 강화 단계 유지**이나, `latency canary` 경로는 먼저 정상화해야 한다.
- 근거: `performance_tuning_2026-04-16` 기준 `gatekeeper_eval_ms_p95=27408`, `latency_block_events=3899`, `quote_fresh_latency_blocks=2963`, `quote_fresh_latency_passes=24`다. stale이 아닌 차단이 대부분이고 canary 실적은 0건이었다.
- 다음 액션: bugfix 반영 후 `latency_canary_applied`, `low_signal`, `tag_not_allowed`, `quote_stale` 분포를 다시 본다.

4. 판정: 관찰축 5는 **튜닝 입력 신호는 확보**, 실전 전환 요건은 미확정.
- 근거: `add_blocked_lock_2026-04-16` 기준 `total_blocked_events=1392`, `stagnation_blocked_events=941`, 상위 코호트 편중.
- 다음 액션: 종목/시간대/held_sec 코호트 기준으로 PREOPEN 가설 1축만 고정.

5. 판정: 원격 비교 기반 승격 판정은 **보류**.
- 근거: `server_comparison_2026-04-16`에서 `performance_tuning`, `entry_pipeline_flow`가 `remote_error(timeout)`.
- 다음 액션: PREOPEN에 원격 재비교를 먼저 수행하고, timeout 해소 전에는 메인 승격 금지.

## 참고 문서

- [2026-04-16-stage2-todo-checklist.md](./2026-04-16-stage2-todo-checklist.md)
- [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md)
- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)

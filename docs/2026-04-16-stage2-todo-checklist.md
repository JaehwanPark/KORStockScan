# 2026-04-16 Stage 2 To-Do Checklist

## 목적

- `AI overlap audit`를 더 이상 관찰 메모로만 두지 않고 `selective override` 설계 착수로 연결한다.
- `2026-04-15` canary 결과를 `blocked_stage / momentum_tag / threshold_profile` 기준으로 묶어 설계 입력으로 고정한다.
- 신규 관찰축을 추가하지 않고, 이미 확보한 계측과 전일 canary 결과만 사용한다.
- `AIPrompt 즉시 코드축(작업 5/8/10)`은 오늘 1차 결과 평가를 수행한다.
- 오늘은 `2026-04-14~15`에 `develop`에서 선행 적용한 축 중 `main` 승격 가능한 것만 고른다.
- `reversal_add`는 결함 핫픽스 반영 상태를 기준으로 shadow 관찰 후 제한형 canary 판정으로 전환한다.

## 장전 체크리스트 (08:00~08:40)

- [ ] `[Checklist0416] reversal_add canary go/no-go 판정` (`Due: 2026-04-16`, `Slot: PREOPEN`, `TimeWindow: 08:20~08:30`)
  - 판정 기준: shadow 지표(`candidate→armed→ordered`, `post_eval_fail`)가 허용범위면 `Go`, 아니면 `No-Go(OFF 유지)`
  - 근거: `reversal_add_candidate`, `[ADD_SIGNAL]`, `[ADD_ORDER_SENT]`, `reversal_add_post_eval_fail`
  - 다음 액션: `Go`면 INTRADAY shadow+limited, `No-Go`면 shadow-only 지속
- [ ] `[Checklist0416] reversal_add 아키텍트 보류항목(A/B/C/D/E) 구현범위 확정` (`Due: 2026-04-16`, `Slot: PREOPEN`, `TimeWindow: 08:30~08:40`)
  - `A/B`: `SESSION_CUTOFF`, `BOX_RANGE`
  - `C/D`: `entry_avg_price`/POST_EVAL 성공조건 반영
  - `E`: partial fill canary 중복게이트 여부
  - 확정 결과는 `구현/보류 + 사유 + 재시각`으로 기록

## 장중 체크리스트 (09:00~15:30)

- [ ] `AI overlap audit` 기반 `selective override` 설계 착수
- [ ] `RELAX-DYNSTR` canary 결과와 `blocked_stage / momentum_tag / threshold_profile` 연결표 고정
- [ ] `RELAX-DYNSTR / partial fill / AIPrompt 5/8/10` 각각에 대해 `main` 승격 가능/불가 판정 초안 작성
- [ ] `AIPrompt 작업 5 WATCHING/HOLDING 프롬프트 물리 분리` 영향도 1차 평가
- [ ] `AIPrompt 작업 8 감사용 핵심값 3종 투입` 1차 결과 평가
- [ ] `[Checklist0416] reversal_add shadow 모니터링` (`Due: 2026-04-16`, `Slot: INTRADAY`)
  - 로그 키: `reversal_add_candidate`, `reversal_add_blocked_reason`, `[ADD_SIGNAL] reason=reversal_add_ok`, `[ADD_ORDER_SENT] type=AVG_DOWN`, `exit_rule=reversal_add_post_eval_fail`
  - 지표: 후보수, 주문전송 성공률, POST_ADD_EVAL 실패율, 메인/원격 실현손익 영향도
  - 주의: 상기 키는 모두 코드 반영 완료 기준으로 집계

## 장후 체크리스트 (15:30~)

- [ ] `selective override` 설계 초안 문서화
- [ ] `AIPrompt 작업 5/8/10` 구현 1일차 결과 정리
- [ ] `AIPrompt 작업 10 HOLDING hybrid 적용` canary-ready 입력 마감
- [ ] `develop` 선행 적용 축 중 `main` 승격 후보와 보류 후보를 분리 기록
- [ ] `AIPrompt 작업 9 정량형 수급 피처 이식 1차` helper scope 초안 정리
- [ ] `2026-04-17` `P2 HOLDING 포지션 컨텍스트 주입` 착수 또는 보류 사유 기록 기준을 체크리스트로 승격
- [ ] 추가 canary가 필요하면 `한 축만` 남기고 보류 사유를 기록
- [ ] `[Checklist0416] reversal_add 운영 판정` (`Due: 2026-04-16`, `Slot: POSTCLOSE`, `TimeWindow: 15:40~16:00`)
  - 판정: `OFF 유지` 또는 `Limited Canary(원격 1축)` 중 택1
  - 근거: shadow 지표(후보수/실패율/손익영향) + 품질게이트(`integrity/restoration/aggregation`)
  - 다음 액션: 선택한 경로의 `2026-04-17` 실행시각/롤백가드를 함께 명시

## 참고 문서

- [2026-04-15-stage2-todo-checklist.md](./2026-04-15-stage2-todo-checklist.md)
- [2026-04-15-scalp-reversal-add-implementation-result.md](./2026-04-15-scalp-reversal-add-implementation-result.md)
- [2026-04-13-observation-axis-code-reflection-audit.md](./2026-04-13-observation-axis-code-reflection-audit.md)
- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)
- [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md)

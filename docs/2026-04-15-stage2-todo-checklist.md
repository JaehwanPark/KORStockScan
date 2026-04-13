# 2026-04-15 Stage 2 To-Do Checklist

## 목적

- `2026-04-14 장후` 결론을 `2026-04-15 08:30`까지 실제 실행으로 옮긴다.
- 오늘은 `관찰`보다 `착수`가 우선이다. 이미 구축한 관찰축은 변경 후 지속 점검용으로만 사용한다.
- `RELAX-DYNSTR`는 `momentum_tag` 1축 원격 canary를 시작한다.
- `partial fill min_fill_ratio`는 원격 canary를 시작한다.
- `Phase 2`는 오늘 시작한다. `RELAX-LATENCY`가 승격되면 `Phase 2-1`을 병행 착수하고, 승격이 보류되면 `Phase 2-2`를 단독 착수한다.
- `expired_armed` 처리 로직은 오늘 장후까지 설계 문서 완료를 목표로 한다.
- 전일 장후에 착수한 `AIPrompt 작업 4/5`는 오늘 구현 진행과 원격 ready 확인까지 이어간다.

## 전일 장후에서 받아야 할 확정값

- `RELAX-LATENCY` 운영 반영/보류 최종 결론
- `RELAX-DYNSTR` 원격 canary 대상 `momentum_tag`
- `partial fill min_fill_ratio` 기본값과 rollback 가드
- `expired_armed` 처리 로직 설계 범위와 문서 위치
- `AI overlap audit -> selective override` 착수 입력과 일정
- `AIPrompt 작업 4/5` write scope / rollback 가드 / 비교지표

## 장전 체크리스트 (08:00~08:30)

- [ ] `2026-04-14 장후` 결론대로 `RELAX-LATENCY` 반영/보류 상태를 운영/원격 설정에 적용
- [ ] `RELAX-DYNSTR` `momentum_tag` 1축 원격 canary 설정 완료 (`08:30`까지)
- [ ] `partial fill min_fill_ratio` 원격 canary 설정 완료 (`08:30`까지)
- [ ] `Phase 2` 착수 선언 기록 (`RELAX-LATENCY 승격 시 2-1 병행`, `보류 시 2-2 단독`)
- [ ] 오늘 실행 축의 rollback 가드와 장중 관찰 포인트를 재고정

## 장중 체크리스트 (09:00~15:30)

- [ ] `RELAX-DYNSTR` 1축 canary의 `AI BUY -> entry_armed -> budget_pass -> submitted` 퍼널 변화를 기록
- [ ] `partial fill min_fill_ratio` canary의 `partial fill 억제 / 체결 기회 감소`를 함께 기록
- [ ] `RELAX-LATENCY`는 전일 결론대로 적용된 축만 지속 점검하고, 신규 완화는 추가하지 않는다
- [ ] 기존 관찰축은 `변경 후 검증`에 필요한 범위로만 유지한다
- [ ] `AIPrompt 작업 4 WATCHING 75 정합화` 구현 진행 / 원격 ready 확인
- [ ] `AIPrompt 작업 5 WATCHING/HOLDING 프롬프트 물리 분리` 구현 진행 / 로그 비교축 확인
- [ ] `AIPrompt 작업 8 감사용 핵심값 3종 투입` 전일 착수분 구현/검증 지속
- [ ] `AIPrompt 작업 9 정량형 수급 피처 이식 1차` helper scope 초안 정리

## 장후 체크리스트 (15:30~)

- [ ] `expired_armed` 처리 로직 설계 문서 작성 완료
- [ ] `RELAX-DYNSTR` 1일차 canary 결과 1차 정리
- [ ] `partial fill min_fill_ratio` 1일차 canary 결과 1차 정리
- [ ] `2026-04-16` `AI overlap audit -> selective override` 설계 착수 입력값을 고정
- [ ] `AIPrompt P1` 구현 진행 결과 정리
  - `작업 4/5`의 원격 canary ready 상태와 `2026-04-16` 평가 포인트를 고정한다
- [ ] `AIPrompt 작업 8 감사용 핵심값 3종 투입` 전일 착수분 결과 정리
- [ ] `AIPrompt 작업 9 정량형 수급 피처 이식 1차` helper scope 초안을 `2026-04-17` 확정형으로 정리
- [ ] 오늘 보류된 항목이 있으면 `사유 + 다음 실행시각`을 문서에 명시

## 참고 문서

- [2026-04-14-stage2-todo-checklist.md](./2026-04-14-stage2-todo-checklist.md)
- [2026-04-14-audit-reflection-strong-directive.md](./2026-04-14-audit-reflection-strong-directive.md)
- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)
- [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md)

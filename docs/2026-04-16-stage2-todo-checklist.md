# 2026-04-16 Stage 2 To-Do Checklist

## 목적

- `AI overlap audit`를 더 이상 관찰 메모로만 두지 않고 `selective override` 설계 착수로 연결한다.
- `2026-04-15` canary 결과를 `blocked_stage / momentum_tag / threshold_profile` 기준으로 묶어 설계 입력으로 고정한다.
- 신규 관찰축을 추가하지 않고, 이미 확보한 계측과 전일 canary 결과만 사용한다.
- `AIPrompt P1`은 오늘 1차 결과 평가를 수행한다.

## 장중 체크리스트 (09:00~15:30)

- [ ] `AI overlap audit` 기반 `selective override` 설계 착수
- [ ] `RELAX-DYNSTR` canary 결과와 `blocked_stage / momentum_tag / threshold_profile` 연결표 고정
- [ ] `AIPrompt 작업 4 WATCHING 75 정합화` 원격 canary 1차 결과 평가
- [ ] `AIPrompt 작업 5 WATCHING/HOLDING 프롬프트 물리 분리` 영향도 1차 평가

## 장후 체크리스트 (15:30~)

- [ ] `selective override` 설계 초안 문서화
- [ ] `AIPrompt P1` 구현 1일차 결과 정리
- [ ] `AIPrompt 작업 3 HOLDING hybrid override 조건 명세` 구현 착수 준비 마감
- [ ] `AIPrompt 작업 9 정량형 수급 피처 이식 1차` helper scope 초안 정리
- [ ] `2026-04-17` `P2 HOLDING 포지션 컨텍스트 주입` 착수 또는 보류 사유 기록 기준을 체크리스트로 승격
- [ ] 추가 canary가 필요하면 `한 축만` 남기고 보류 사유를 기록

## 참고 문서

- [2026-04-15-stage2-todo-checklist.md](./2026-04-15-stage2-todo-checklist.md)
- [2026-04-13-observation-axis-code-reflection-audit.md](./2026-04-13-observation-axis-code-reflection-audit.md)
- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)
- [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md)

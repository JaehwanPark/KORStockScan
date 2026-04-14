# 2026-04-15 Stage 2 To-Do Checklist

## 목적

- `2026-04-14 장후` 결론을 `2026-04-15 08:30`까지 실제 실행으로 옮긴다.
- 오늘은 `관찰`보다 `착수`가 우선이다. 이미 구축한 관찰축은 변경 후 지속 점검용으로만 사용한다.
- `main` 반영은 오늘 실행하는 `develop` 축의 장후 결과가 있을 때만 연다. 같은 축의 `main` 선적용은 금지한다.
- `RELAX-DYNSTR`는 `momentum_tag` 1축 원격 canary를 시작한다.
- `partial fill min_fill_ratio`는 원격 canary를 시작한다.
- `Phase 2`는 오늘 시작한다. `RELAX-LATENCY`가 승격되면 `Phase 2-1`을 병행 착수하고, 승격이 보류되면 `Phase 2-2`를 단독 착수한다.
- `expired_armed` 처리 로직은 오늘 장후까지 설계 문서 완료를 목표로 한다.
- 전일 장후에 착수한 `AIPrompt 작업 5/8/10`은 오늘 구현 진행과 검증 입력 고정까지 이어간다.
- `SCALPING 모델 shadow 비교안`은 `2026-04-15`에 바로 실표본을 수집한다. `PREOPEN` 구현 착수, `INTRADAY` 첫 shadow 수집, `POSTCLOSE` 첫 비교표 생성을 같은 날 닫는다.

## 전일 장후에서 받아야 할 확정값

- `RELAX-LATENCY` 운영 반영/보류 최종 결론
- `RELAX-DYNSTR` 원격 canary 대상 `momentum_tag`
- `partial fill min_fill_ratio` 기본값과 rollback 가드
  - `2026-04-14 10:00 KST` 기준 코드 경로/전용 rollback 가드가 아직 없어, 실행형 canary는 구현 없이는 시작 불가 상태다.
- `expired_armed` 처리 로직 설계 범위와 문서 위치
  - `태광` 단일표본이 아니라 전수 `expired_armed` 분포 + 상위 코호트 + anchor case 조합으로 설계한다
- `AI overlap audit -> selective override` 착수 입력과 일정
- `AIPrompt 작업 5/8/10` write scope / rollback 가드 / 비교지표

## 장전 체크리스트 (08:00~08:30)

- [ ] `2026-04-14 장후` 결론대로 `RELAX-LATENCY` 반영/보류 상태를 운영/원격 설정에 적용
- [ ] `RELAX-DYNSTR` `momentum_tag` 1축 원격 canary 설정 완료 (`08:30`까지)
- [ ] `partial fill min_fill_ratio` 원격 canary 설정 완료 (`08:30`까지)
  - blocker: `2026-04-14` 기준 `min_fill_ratio` 전용 설정 경로와 rollback env가 코드에 아직 없다.
- [ ] `Phase 2` 착수 선언 기록 (`RELAX-LATENCY 승격 시 2-1 병행`, `보류 시 2-2 단독`)
- [ ] 오늘 `develop`에 적용한 축별 `main` 승격 최소 시점(`2026-04-16` 이후)을 작업 메모에 고정
- [ ] 오늘 실행 축의 rollback 가드와 장중 관찰 포인트를 재고정
- [ ] `expired_armed` 설계 입력은 `단일 종목`이 아니라 `전수 분포 + 상위 코호트 + anchor case` 기준으로 읽는다고 오늘 메모에 고정
- [ ] `SCALPING 모델 shadow 비교안` `WATCHING shared prompt` 구현 착수 및 원격/본서버 공통 로그 필드 고정
  - `08:30`까지 `Tier2 Gemini Flash vs GPT-4.1-mini` shadow 호출 경로와 `action/score/counterfactual` 로그 스키마를 develop 기준으로 닫는다.

## 장중 체크리스트 (09:00~15:30)

- [ ] `RELAX-DYNSTR` 1축 canary의 `AI BUY -> entry_armed -> budget_pass -> submitted` 퍼널 변화를 기록
- [ ] `partial fill min_fill_ratio` canary의 `partial fill 억제 / 체결 기회 감소`를 함께 기록
- [ ] `RELAX-LATENCY`는 전일 결론대로 적용된 축만 지속 점검하고, 신규 완화는 추가하지 않는다
- [ ] 기존 관찰축은 `변경 후 검증`에 필요한 범위로만 유지한다
- [ ] `expired_armed` 전수 분포 재확인
  - 시간대 / 종목 / `momentum_tag` / `threshold_profile` / `entry_armed_expired_after_wait` 상위 코호트를 다시 묶는다
  - `태광`은 anchor case로만 유지하고 단일 종목 결론으로 확대하지 않는다
- [ ] `AIPrompt 작업 5 WATCHING/HOLDING 프롬프트 물리 분리` 구현 진행 / 로그 비교축 확인
- [ ] `AIPrompt 작업 8 감사용 핵심값 3종 투입` 전일 착수분 구현/검증 지속
- [ ] `AIPrompt 작업 10 HOLDING hybrid 적용` `FORCE_EXIT` 제한형 MVP 구현 지속 / canary-ready 입력 정리
- [ ] `AIPrompt 작업 9 정량형 수급 피처 이식 1차` helper scope 초안 정리
- [ ] `SCALPING 모델 shadow 비교안` 첫 실표본 수집 시작
  - `WATCHING shared prompt` 동일 입력에 대해 `gemini_action/score`, `gpt_action/score`, `action_diverged`, `score_gap`를 오늘 장중부터 누적한다.

## 장후 체크리스트 (15:30~)

- [ ] `expired_armed` 처리 로직 설계 문서 작성 완료
  - 재진입 허용 여부는 `태광` 1건이 아니라 전수 분포와 상위 코호트 기준으로 판정한다
  - 문서에는 `anchor case`와 `통계 입력`을 분리해서 쓴다
- [ ] `RELAX-DYNSTR` 1일차 canary 결과 1차 정리
- [ ] `partial fill min_fill_ratio` 1일차 canary 결과 1차 정리
- [ ] 오늘 `develop` 결과 기준으로 `2026-04-16 main` 승격 가능/불가 초안을 항목별로 기록
- [ ] `2026-04-16` `AI overlap audit -> selective override` 설계 착수 입력값을 고정
- [ ] `AIPrompt 즉시 코드축` 구현 진행 결과 정리
  - `작업 5/8/10`의 `2026-04-16` 평가 포인트를 고정한다
- [ ] `AIPrompt 작업 8 감사용 핵심값 3종 투입` 전일 착수분 결과 정리
- [ ] `AIPrompt 작업 9 정량형 수급 피처 이식 1차` helper scope 초안을 `2026-04-17` 확정형으로 정리
- [ ] `AIPrompt 작업 10 HOLDING hybrid 적용` `FORCE_EXIT` 제한형 MVP 착수 상태와 `2026-04-16` 입력값 정리
- [ ] `SCALPING 모델 shadow 비교안` 첫 장후 비교표 생성
  - `entered_if_gemini`, `entered_if_gpt`, `realized_pnl_if_gemini`, `realized_pnl_if_gpt`, `missed_winner_cost_if_gemini`, `missed_winner_cost_if_gpt`를 오늘 체결/미진입 복기와 연결해 1차 비교표로 남긴다.
- [ ] 오늘 보류된 항목이 있으면 `사유 + 다음 실행시각`을 문서에 명시

## 참고 문서

- [2026-04-14-stage2-todo-checklist.md](./2026-04-14-stage2-todo-checklist.md)
- [2026-04-14-audit-reflection-strong-directive.md](./2026-04-14-audit-reflection-strong-directive.md)
- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)
- [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md)

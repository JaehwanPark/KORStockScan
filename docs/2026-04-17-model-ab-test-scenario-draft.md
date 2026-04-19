# 2026-04-17 모델별 A/B 테스트 시나리오 초안

## 목적

- 2026-04-16 운영반영과 분리된 실험축으로만 A/B를 설계한다.
- 실전 로직 변경은 한 번에 한 축(canary)만 적용하고, shadow-only/롤백 가드를 기본으로 둔다.

## 실행 백로그 (자동 동기화 대상)

- [x] `[Checklist0417] 모델별 A/B 테스트 실험군/대조군 정의 확정` (`Due: 2026-04-17`, `Slot: PREOPEN`, `TimeWindow: 08:00~08:10`, `Track: AIPrompt`) (`실행: 2026-04-17 20:54 KST`)
  - 판정 기준: 대상 모델, 적용 구간(진입/보유/청산), 샘플링 비율 확정
  - 근거: 운영반영과 분리된 실험 설계 필요
  - 다음 액션: 실험군 분리 설정 및 shadow 로그 키 확정
  - 실행 메모: 대조군=`현재 운영경로`, 실험군=`모델/스키마 변경 1축`, 배포순서=`remote shadow-only -> remote canary -> main canary`.

- [x] `[Checklist0417] A/B 중단조건(손실/지연/미체결) 및 롤백 가드 명시` (`Due: 2026-04-17`, `Slot: PREOPEN`, `TimeWindow: 08:10~08:20`, `Track: ScalpingLogic`) (`실행: 2026-04-17 20:54 KST`)
  - 판정 기준: stop 조건과 즉시 롤백 조건을 수치로 명시
  - 근거: 실전 리스크 통제 및 재현성 확보
  - 다음 액션: runbook/체크리스트에 동일 조건 반영
  - 실행 메모: 중단조건=`latency_block_events +20%p`, `order_bundle_submitted_events -30%`, `parse_error>0`, `체결불능/주문실패 급증`; 롤백=`동일 슬롯 즉시 canary OFF`.

- [x] `[Checklist0417] A/B 평가 기준(거래수/퍼널/blocker/체결품질) 고정` (`Due: 2026-04-17`, `Slot: PREOPEN`, `TimeWindow: 08:20~08:30`, `Track: Plan`) (`실행: 2026-04-17 20:54 KST`)
  - 판정 기준: 손익 파생값보다 거래수, 퍼널, blocker 분포, 체결품질 우선 지표로 확정
  - 근거: fallback/NULL 정규화 왜곡 방지 원칙 준수
  - 다음 액션: 당일 POSTCLOSE 리포트 템플릿에 동일 기준 적용
  - 실행 메모: 고정지표=`budget_pass_events`, `order_bundle_submitted_events`, `latency_block_events`, `blocker 분포`, `full_fill_events`, `partial_fill_events`.

## 참고

- Source: `docs/2026-04-16-stage2-todo-checklist.md`
- Related: `docs/scalping_ai_routing_instruction_integrated.md`

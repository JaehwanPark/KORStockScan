# 원 계획·조건부 probe·과거 에피소드 생산 코드 보완 리뷰

## 요청과 범위

2026-10-06 사용자 지시: 원 계획·손절·자본 보존과 장후 연결, probe 재생 계약, 과거 에피소드 생산 코드 검증, 보조판정 기존 가격/정확한 입력·응답 연결을 보완하고 반복 리뷰 후 배포·재기동한다.

현재 owner는 [10/6 체크리스트](../checklists/2026-10-06-stage2-todo-checklist.md)의 `DirectFamilySourceRepairEntrySplit`, `DirectFamilySourceRepairCompactAuxiliary`, `DirectFamilySourceRepairLowPriceTwoLeg`다. 원천·경제성 자연 수용 기준을 완료로 덮어쓰지 않는다. 동결된 과거 summary/checklist 생성과 정책 파일은 재작성하지 않는다.

## 확인한 결함과 변경

| 구간 | 결함 | 보완 |
|---|---|---|
| 사전 probe 계획 | 빈 orders 예외가 route/TTL/context 동결을 끊음 | 1주 관측 계획과 null 잔여 가격, 전체 typed seed 보존 |
| 원자 수량 | 사전 composer가 즉시 1주를 requested total로 사용 | 원 requested quantity로 합계 검증 |
| 손절/자금 | 조회·가드 중단 뒤 원 stop 생산 결과가 사라짐 | 원 stop receipt를 조회 전 보존, 원 capacity receipt와 full context/seed 연결 |
| 후속 receipt | 새 계약을 읽는 장후 loader/compact/census 경로 누락 가능 | 기존 ENTRY pipeline과 dynamic-entry family에 exact fill/decision receipt 등록 |
| 재생 가격 | 현재 전역 규칙을 과거 계산에 사용할 위험 | 동결 규칙 namespace로 native P1 실행, live 전역 불변, original kernel 차이 시 거부 |
| 분모 | 같은 key의 다른 seed를 중복으로 처리할 위험 | 중복·충돌·거부·보존을 각각 합계 검증 |
| 실제 비용 | static validator가 conditional 실행을 제외 | 실제 제출 seed만 typed 허용, COMPLETED/cost/quantity/decision gates 유지 |
| 보조 원천 | conditional 계획과 static operating replay를 혼동 | 원 계획/stop/body를 trace→projection에 보존, conditional 운영 미지원 원인 별도 표시 |
| 보조 가격 진단 | generic 운영 label source-gap을 독립 10분 가격 평가와 혼동 | exact price-label join/native net-path count 별도 제공, 기존 운영 결손 유지 |
| 에피소드 감시 | 현재 전체 소스 SHA를 과거 producer SHA와 비교 | hash-matched 원본 bytes를 보관·검증, 원 report/policy/summary hash 검증 유지 |

관측 orders는 실제 committed quantity 0, 제출/예약 권한 없음이다. 미래 가격이나 과거 missing capital/cost를 현재 값으로 채우지 않는다. 원천 결손을 broker 주문 실패로 분류하지 않는다.

## 과거 원본 증거

- 10/2 Episode semantic projection의 두 SHA는 커밋 `96d6bc80`의 `src/engine/monitoring/low_price_two_leg_tuning.py`, `src/engine/monitoring/family_policy_semantics.py` 원본과 일치한다.
- SHA 기반 `.source` archive는 검증 전용이며 실행하지 않는다. 해시가 다른 현재 소스로 과거 원본을 대신하지 않는다.
- 원 보고서의 source-gap 16개 프로필과 capture invalid event 106개는 유지한다. 코드 출처 오탐 수리와 연구 원천 결손 수리는 별도다.
- 10/2 compact auxiliary 15개 행에는 기존 10분 가격 값이 있지만 writer-plan/stop/context 등의 운영 결손이 있다. 독립 AI stage의 전체 cumulative 표본과 해당 날짜의 운영 표본을 합산하지 않는다.

## 지원·수용 경계

조건부 가격 복원은 actual-control의 native post-probe 초기 가격/수량 대조다. 개별 leg 재호가·최종 제출·full/partial fill·cancel/late fill·청산·수수료의 완결은 별도 증빙을 요구한다. changed CF에 actual fill/AI/자금을 복사하지 않는다. guard/model 원천 미지원 또는 natural 실행 미관측은 null 경제성과 typed blocker로 유지한다.

Kiwoom 요청·응답 parser·FID·REG/REMOVE·auth·continuation은 변경하지 않았다. 기존 로컬 source receipt만 관측·소비하며 새 API/AI 호출, 수량/cap/timeout/threshold/보호·주문 guard 변경은 없다.

## 검증·배포 기록

- 새 계약/과거 original-kernel focused 회귀: 164 통과. 원본 누락/변조, source/epoch/시계/가드/자금/수량/가격 불일치, snapshot/live 불변, duplicate/conflict, native fill observer 및 wire loader를 포함한다.
- 통합 회귀 613 통과, 소비자/감시기 회귀 275 통과, 실제 제출 seed/비용 추가 회귀 324 통과. 마지막 action/guard/mark 원 receipt binding 및 정상 timeout abort 보완 후 producer/contract 회귀 127 통과. 서로 겹치는 실행 회차이며 고유 테스트 수로 합산하지 않는다.
- 변경 Python 19개 compile, `git diff --check`, print-only parser 통과. 현재 실행 owner를 변경하지 않고 동결된 과거 checklist와 summary를 보존했다. 검토 범위의 미해결 코드 결함 0; 자연 실행/운영 모델 수용은 아래 경계로 남는다.
- 원본 archive 생성 후 실제 과거 report/policy/checklist/PREOPEN 등 34개 파일 SHA 불변 확인. 에피소드 findings는 `episode_native_source_gap`, `episode_capture_invalid_events`만 남고 producer-changed 오탐이 사라졌다. 보조 15건 모두 exact price-label join/native fixed 10m net-path 평가 가능; 운영 계획/stop/paired 결손 warnings는 그대로다.
- 배포·실제 PID 소비 결과는 종료 시 같은 문서에 갱신한다.
- 증거 폴더: `tmp/probe-original-source-remediation-20261006/`. 정책 값 변경 및 연구 정책 재생성은 이 배포에 포함하지 않는다.

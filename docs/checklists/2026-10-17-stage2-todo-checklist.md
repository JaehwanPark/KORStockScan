# 2026-10-17 Stage2 To-Do Checklist

## 오늘 목적

- 사용자 명시 지시의 비상시감시 호가·기회 전달 개선을 격리 작업본에서 구현하고 리뷰·수정·표적 검증으로 닫는다.

## 오늘 강제 규칙

- 기존 동시 작업과 원천·판정·정책 영수증을 보존한다. 코드는 선택 릴리스 기준 격리 작업본에서 검증한다.
- 코드 완료, 정책 등록·배포·재기동·PID 소비, 자연 제출·체결·비용 성과를 각각 확인한다. 이번 구현은 운영 활성화 권한이 아니다.
- 원 신호 5초·Main/manual custody·수량·provider·broker 및 hard safety 계약을 유지한다. 새 시간상한 선정에는 해당 원천·단계별 비교와 적용 계약이 필요하다.
- 문서 검증은 print-only parser만 사용한다. 외부 Project/Calendar 동기화는 사용자가 수행한다.

## 실행 항목

- [x] `[NonfixedQuoteOpportunityDelivery1017] 비상시 호가·원천 전달·전송 직전 검증 구현` (`Due: 2026-10-17`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: 사용자 구현·반복 코드리뷰 지시, [최종 보완계획](../proposals/nonfixed-quote-freshness-and-opportunity-delivery-remediation-plan-2026-10-17.md), [사전점검](../audits/nonfixed-quote-remediation-contract-preflight-review-2026-10-17.md).
  - 범위: canonical 설정 조회·source-wait 경합·exact 0D wake·quote-only bounded 재계산·원천/정책 시각 영수증·Main 최초 진입/분할 leg0 물리 전송 직전 검증.
  - 완료 기준: 생산자→소비자·결손·경합·원 기한·중복·auth retry·미전송/불확실·후속 leg/SELL 비전파를 리뷰·보완하고 표적 pytest·compile·문서 링크·parser·diff 검사를 통과한다. 선택 정책/운영 환경/배포/기동/실주문은 별도 권한이다.
  - 완료: [구현 리뷰](../audits/nonfixed-quote-opportunity-delivery-implementation-review-2026-10-17.md). 통합1,610 PASS, 기존 node1개는 선택 부모의 같은 실패를 직접 재현해 별도 보존. Python21개 compile/name 검사·로컬 링크·parser·diff 검증. 새 age 상한 미선정, 정책/선택/배포/재기동/PID/자연 주문/체결/성과는 별도다.

- [ ] `[NonfixedQuoteDeploymentIsolatedPolicy1017] 비상시 호가 수리 배포 및 격리 정책 검증` (`Due: 2026-10-17`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: 사용자 명시 배포·격리 프로세스 정책 읽기/스키마/코드 호환성 검증 지시, [배포 검증 기록](../audits/nonfixed-quote-deployment-and-isolated-policy-review-2026-10-17.md).
  - 범위: 원 정책/장후/PREOPEN 영수증을 보존하고 exact code handoff·네트워크 차단 격리 검증 뒤 다음 정규 기동용 선택을 갱신한다. 새 TTL 선정은 필수가 아니다. 운영 봇의 주말 기동·당일 PREOPEN 우회·수치 재선정·실주문은 포함하지 않는다.
  - Acceptance: 새 코드의 원 128범위 native parity, 원 prepared 정책의 정확한 해시·reader·지연/보유/손절 코드 인계, current full preparation 검증 및 선택 CAS. 원 active pointer/env 불변·실제 PID 소비 false를 각각 확인한다.

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

- [ ] `[InitialQuantityResearchRepair1017] 최초 수량 연구 입력·비용 대사와 전체 거래 EV 선정 수리` (`Due: 2026-10-17`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: 사용자 다음액션 실행 및 익절 가중 후보 생성·전체 거래 비용 후 EV 최종 선정 확정, [수량 후속 연구 계약](../proposals/initial-quantity-runtime-postclose-producer-consumer-repair-plan-2026-10-10.md#7-2026-10-17-후속-연구-실행-계약).
  - 범위: 최신 선택 코드 기준 격리 작업본에서 IQ171–IQ175의 재현 여부·원천 세대를 고정하고 남은 날짜/입력 보존 및 v3 선정기를 수정한다. 비용·capture는 거래/attempt별 검증 복구·역사 결손·추가 원천 대기를 구별한다.
  - Acceptance: bounded 원천/fact 및 실제 이벤트 모수 대사, 전체 거래 EV·순이익 선정·원금/비용/부분체결·독립 holdout·v2/v3 stage 호환 회귀, 적격 fixture 성능·실제 source-gap 구분, 코드리뷰·수정·재리뷰와 print-only 문서 검증. 새 정책의 경제성·PREOPEN/PID 자연 소비는 별도 영수증으로 확인한다.
  - 진행: 선택 c5aeda844 기준 작업본 고정. 현재 fact16/완료13/보유3·비용 적격0, 입력 검증3일 PASS, compact 실행112/112 소비. 정확 비용 집계의 공식 계약 미정은 임의 배분 없이 원천 결손으로 보존하며 선정 v3와 구 평가 reader 호환을 검증 중이다.

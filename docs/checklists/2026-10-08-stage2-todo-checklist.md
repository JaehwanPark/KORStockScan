# 2026-10-08 Stage2 To-Do Checklist

## 오늘 목적

- 승인된 10/7 원천의 EOD 제외 장후 재개를 완료하고, 10/8 exact-date 정책·최종화·PREOPEN 준비와 정상 예약기동을 확인한다.
- 독립 운용 정책 구현/배포, 실제 AI 비교 완료, 신규/기존 정책 승계, 실제 PID 소비를 각각 확인한다.

## 오늘 강제 규칙

- 사용자 승인 Main 판정 계약은 실제 ask, 30분, 비용률 .0023, 비용 후 +.4% 목표와 soft -3% 선도달의 누적 raw 승률이다. EV·손익비·최소 표본/일수·holdout·기존 제출 보존 gate를 추가하지 않는다.
- 운영/오프라인 AI 횟수 quota=None을 유지한다. provider 간격·외부 rate limit·중복/불확실 예약·timeout과 broker/account/order/수량/자본/custody/manual veto/hard safety는 보존한다.
- clean tuning baseline은 `2026-06-05T00:00:00+09:00`이다. 식별 가능한 결손 row/window를 제외하고 UNKNOWN·U·valid-empty·미완료 실제 비교를 구분한다. 과거 archive를 현행 원천으로 복원하지 않는다.
- EOD와 독립 owner를 중복 재실행하지 않는다. Main-only/OFF·퇴역 정책과 기존 보유 청산 소유권을 보존한다. 코드 검증/선택 release/준비 정책/PID/자연 주문·실현 손익을 같은 완료로 표시하지 않는다.
- Project/Calendar 동기화는 사용자 표준 명령으로 수행한다. 현재 summary 미생성으로 자동 checklist builder는 아직 실패 상태이며, 생성 후 동일 stable ID에 인계하고 중복 OPEN을 만들지 않는다.

## 전일 OPEN 인계

- [ ] `[DirectFamilySourceRepairMainMechanisticEntry] 독립 운용 정책 통합 배포·10/7 장후 재개·10/8 정상 기동 준비` (`Due: 2026-10-08`, `Slot: POSTCLOSE`, `TimeWindow: 승인 코드 배포 후 장후 최종화 및 07:55 예약기동 준비`, `Track: RuntimeStability`)
  - Source: [독립 탐지·기여도 계획](../proposals/main-operating-policy-independent-detection-and-contribution-evaluation-implementation-plan-2026-10-07.md), [구현·운영 인계](../audits/main-operating-policy-implementation-and-postclose-review-2026-10-07.md), [10/7 원 Acceptance·검증 이력](2026-10-07-stage2-todo-checklist.md).
  - 승인: 사용자가 구현→반복 리뷰/보완→배포 후 중단한 EOD 제외 장후를 재개·모니터링하고 다음 기동을 준비하도록 명시했다. 20:41 보류를 새 코드 gate/배포 후 해제한다. 원천일 10/7, 정책/기동 대상 10/8을 보존한다.
  - Acceptance: 기존 실제 목록+8개 정확 정의/적용 범위, 독립 탐지/typed union, scope 실행 hash, live outbox와 offline 공유 원장 분리, full expected membership, 실제 AI 증분 호출·원 응답 보존, incomplete scope의 native pair carry, 48셀/128route loader와 report/감시 소비를 검증한다.
  - 운영 종료 조건: 원래 cron 5개와 final-refresh timer만 복원하고 장후 체인을 한 번 재개한다. 실제 최신 terminal→summary/tower→오늘 checklist→strict `--require-summary-handoff`→controller DONE→finalization→exact-date PREOPEN prepared를 재봉인한다. EOD를 재실행하지 않는다.
  - 상태: 최초 확장 회귀 699 PASS 이후 indirect consumer/보유 재현/호출 서명 결함을 보완했다(통합 395·장중 62·immutable 188 PASS). 정확 입력 투영은 실제 120개 확인점 bytes 일치(확장 135·immutable 53 PASS), 대형 native 보고서 reader는 244 PASS, final audit 순서 barrier는 작업본/immutable 각각 149 PASS다. `66fce0a9` / `operating-union-20261008-v7` 배포 및 63 owner 검증 완료. 01:46 기계 누적 확인점 117,763건(확정 77,903/U 39,860)의 native 검증 succeeded, 01:47 전체 wrapper 재개. 실제 AI 비교·최종화/PREOPEN은 진행 중이며 아직 완료 아님. 자연 주문/실현 성과는 기동 준비의 코드 종료 조건으로 요구하지 않는다.

  - 재개 보완: 분할수량 553 MiB 원천의 bounded streaming·exact census, archive 원천일 전달, episode OFF 시 미사용 capacity 승계, 실행 중 machine preflight 보존을 검증하고 보완 릴리스로 인계한다.

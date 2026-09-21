# 위젯 과거 사건 종결·정책 인계·삼성 이월 보존

- 권한: 사용자 `결함보완하여 배포 및 재기동 승인`, 후속 확인 `모두 종결되었고 삼성은 25주 보유중`. 과거 주문사건 종결과 삼성 현재 보유 25주는 별개다. 매도·체결·비용·손익을 합성하지 않는다.
- 코드 검토 범위: 기존 incident reader, paired incumbent producer/consumer, 정책 publisher, 위젯 state loader. 메인·다른 에피소드·수량/threshold/owner guard는 변경하지 않는다.

## 원인과 수리

1. 삼성 1·두산 4·한화 8건의 과거 사건이 사용자 종결 확인을 소비할 경로 없이 영구 이월됐다. 기존 event ledger에 실패 원문 SHA-256 목록을 지정한 operator closure를 소비한다. `closed_operator_confirmed`는 exact full fill과 구분하며, 다른 사건·후속 실패·당일 실패 veto·과거 날짜로 전파하지 않는다.
2. paired incumbent가 변경 가능한 날짜별 정책 파일을 참조하여 재발행·release 삭제 시 원본을 잃었다. binding과 덮어쓰기 전에 `.incumbents/<sha256>.json`에 정확한 bytes를 보존한다. 기존 손실 해시는 복원한 것으로 처리하지 않는다.
3. publisher는 실제 consumer 검증 전에 canonical report/policy를 덮어썼다. 임시 report/policy에서 먼저 consumer round trip을 통과시킨 후 발행한다.
4. 위젯 loader는 동일 날짜 정책 목록 교체 시 active orders가 없으면 state 전체를 초기화했다. 이월 수량·완료 횟수·history를 보존한다. 현재 주문/보유가 있는 정책 교체의 기존 fail-closed 검사는 유지한다.

## 검증과 적용 절차

- 관련 pytest 238 passed, 1 deselected. 제외한 `test_widget_evaluation_wrapper_reuses_one_completed_date`는 변경 전 `widget-fleet-repair-20260921-bbdf8a8b3`에서도 같은 실패를 재현했다. wrapper의 선후행 handoff 호출을 오래된 테스트가 기대하지 않는 별도 fixture 문제다.
- 격리 event 사본에서 종결 13건, 미종결 0건, 실제 체결 건수 불변 확인. source9/18 과거 판정은 그대로 남긴다.
- 삼성 KRX는 검증된 9/8 정책, NXT 장전은 검증된 9/16 정책과 기존 replay baseline의 모든 parameter가 정확히 일치한다. 기존 선택값을 유지하여 원본 보존 receipt와 selection hash를 다시 결합했다. 새 replay/경제성·다른 설정 승격은 없다.
- 격리 consumer 검증: 삼성 KRX/NXT 장전 2개 session eligible, 두산·한화는 각각 19/40·20/40일 연구 축적 조건으로 계속 blocked. 장전 session은 오늘 실행 시각이 이미 지났다.
- 현재 공통 owner registry의 삼성 순보유는 9/8 exact position 25주이고 다른 삼성 widget position은 0주다. 사용자 현재 확인과 일치한다. 오늘 broker 재조회 영수증을 새로 얻었다고 주장하지 않는다.
- 적용 시 위젯만 중지하고 기존 singleton lock을 획득한다. state/events/policy/registry/startup receipt와 unit pin을 백업한다. 사건 종결 append와 이월 25주 표시를 반영하되 orders·registry는 보존한다.
- source9/18 경제성 보고서 원본은 보존하고 `runtime_reconciliation_2026-09-21/` 아래 별도 인계 보고서로 오늘 정책을 발행한다. 20:10 평가 service는 수정된 immutable producer를 사용하도록 pin하며 장중 재실행하지 않는다.
- rollback 시 과거 빈 state나 carry0를 복원하지 않는다. 종결 receipt와 25주 보존을 유지하고, 필요하면 정책만 이전 observation 상태로 되돌린다. 이 문서는 별도 주문 권한을 만들지 않는다.

## 배포 영수증

- 적용 전 준비와 격리 검증 완료. 실제 배포·재기동 결과는 아래에 후속 기록한다.
- 작업 증거: `tmp/widget-policy-custody-repair-20260921/`.
- 미래 자연 policy 소비·주문·비용 후 성과는 오늘 checklist의 기존 `KiwoomCommonHealthOpportunityCostAcceptance0917`에서 추적한다.

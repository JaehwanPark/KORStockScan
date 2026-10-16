# 부분 보유·native 관측 이관 통합 배포 검토

- 사용자 승인: `91ffb3591956c7c84a56ed312540f7e3c32a5d29` 코드리뷰·보완 반복 후 통합 배포·재기동.
- 실제 기준: 선택48968ade9/Main PID3646205/start18963364. 별도 작업트리 `probe-partial-integrated-20261016`에서 대상91ff와 선행e04ccc579, 현재 선택48968ade9 및 보고서 수용00b8e4f 이력을 함께 보존한다.
- 원 변경 설명: [부분 보유](main-probe-partial-holding-policy-repair-review-2026-10-16.md), [native 구독 이관](main-nonfixed-native-handoff-repair-review-2026-10-16.md), [holding 성능·경보 식별](main-holding-sentinel-performance-review-and-deployment-2026-10-16.md).

## 리뷰 발견과 보완

1. 원91ff의 열린 주문 검사는 OPEN/PARTIAL/SENT만 인식한다. 실제 late-parent-fill 소비자는 child BUY를 CANCEL_PENDING으로 기록한다. 이 상태나 결손·UNKNOWN 및 broker 대사 미완료 flag가 있으면 원 종료 처리에서 pending 주문/목표 정보를 지울 수 있었다. 양수 주문번호와 명시적 FILLED/CANCELLED/REJECTED 상태, 대사 완료를 확인한 뒤 부분 보유로 전환한다. 취소 함수의 열린 주문 부재 경로와 취소 후 정리 경로도 같은 계약을 사용한다. 기존 broker 대사 owner가 남으며 새 취소·조회·재시도는 추가하지 않는다.
2. exit token 없이 매도 주문번호·주문시각·대기 메시지만 남은 경우 기존 청산 소유권을 충분히 검사하지 않았다. 기존 active SELL/reconciliation 검사와 주문시각을 함께 확인해 부분 보유 전환과 중복 비율 청산을 거부한다.
3. 공유 handler/receipt 변경으로 rising_missed·holding_vote 전체 코드 세대가 바뀐다. 원 PREOPEN 23a13aba6에서 검토 후보까지 정확한 4개 consumer 파일 해시만 등록하고, 기존 정책·원 보고서와 역사적 unverified를 유지한다. 변경된 family는 독립 network-denied fixture로 재검증한 후 인계한다. 포괄적 함수 면제나 정책 숫자 갱신은 없다.

원 커밋에서 새 회귀 10건 실패를 재현했다. 보완 후 전체 관련 3,673건과 새 exact-source-pair 변조/dirty/origin 회귀50건이 통과했다. 기존 전체 부분 체결 비율 guard, 두 probe residual phase, KRX/NXT/SOR, hard stop/exit 소유권, unknown 취소, initial-quantity durable owner, DB 실패 정리 및 WS lease/epoch/deadline을 검토했다. source_gap 5건, cost/outcome null과 원 수동·retired custody는 유지한다. 목표9주 중1주를 보유하는 계약 수리이며 새 수량 확대나 강제 매도 권한이 아니다.

## 운영 적용 절차와 수용 경계

정규 ordered_intraday_deploy를 사용한다. 배포 전 후보 delay/stop/holding 검증, active policy exact-code handoff, 변경 family fixture를 닫고 원 policy/PREOPEN/prepared·수동 제외·editable checklist 해시를 동결한다. 기존 PID drain 뒤 selector/동일 정책 prepare/기동/실제 PID 소비를 검증한다. 기동 이후 생성된 holding·BUY 보고서만 검증하며 broker inventory·미체결·WS 0B/0D를 별도 확인한다. 배포 전 보고서나 REG 등록을 새 PID의 자연 실행으로 보고하지 않는다.

검토 범위의 코드 결함은 보완했으며 배포 결과는 후속 절에 기록한다. 자연 probe 부분 체결 종료나 비고정 신호 편입은 실제 사례가 생긴 뒤 기존 NonfixedDispatchReadinessReview1012/HoldingProfitExitSourceContractRepair owner에서 수용한다. 모의 회귀를 실제 체결·비용 후 성과로 대체하지 않는다.

## 공식 참조 및 검증 자료

공식 Kiwoom upstream HEAD를 다시 조회해 `953e5dbff123f437ab4d11a78a95191a685eb51f`임을 확인했다. specs.py, core/client.py·ws_client.py, realtime/packets.py·stream.py, packaged ka10075/kt00007/kt10003/kt10001/0B/0D 및 PRD/MOCK Postman을 확인했다. kiwoom_docs는 없다. 기존 POST JSON·venue·원 주문/확인 수량·체결·잔량 및 REG/REMOVE/LOGIN 계약을 유지하며 wire/parser/FID/auth/continuation은 변경하지 않았다. 원천 조회시각/파일 SHA는 [공식 참조 기록](/home/ubuntu/KORStockScan/tmp/probe-partial-integrated-20261016/official-reference.json)에 있다.

- [원 결함 재현](/home/ubuntu/KORStockScan/tmp/probe-partial-integrated-20261016/review-reproduction.log)
- [통합 회귀](/home/ubuntu/KORStockScan/tmp/probe-partial-integrated-20261016/final-tests.log)
- [인계 변조 거부 회귀](/home/ubuntu/KORStockScan/tmp/probe-partial-integrated-20261016/exact-source-pair-tests.log)
- [검토 코드 세대](/home/ubuntu/KORStockScan/tmp/probe-partial-integrated-20261016/reviewed-code-generations.json)

실제 provider·계좌·주문·Telegram 호출은 코드 검증에서 수행하지 않았다. 정규 Main 재기동 이후의 기존 운영 호출과 구분한다. shell/wrapper 변경은 없으므로 bash 검증은 생략한다. 정책 grid 연구·경제성 재산출과 무관한 거래 suite는 실행하지 않는다.

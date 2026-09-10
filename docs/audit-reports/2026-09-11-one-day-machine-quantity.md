# 2026-09-11 신규 매수 1주 — 구현·배포 검증

사용자 지시: “오늘만 신규 1주로 변경해줘”. 적용 범위는 2026-09-11 KST의 위젯 신규 매수와 삼성/저가주 에피소드의 새 진입 계획이다. 에피소드는 기존 2개 leg를 유지해 1주씩 총 2주다. 기존 보유·접수 주문의 수량과 목표/취소 원장은 보존한다. 기본 10주/총20주 계약과 기존 exact-date 정책의 진입 veto·경제성·owner·broker guard는 유지한다.

## 구현

- `src/trading/order/episode_quantity.py`: timezone-aware 시각을 KST로 변환한 날짜가9/11일 때만 신규 수량1. 9/12 00:00부터 신규 기본값10으로 자동 복귀한다. 기존 owned validator는1/10을 모두 허용한다.
- regular two-leg 및 Samsung morning: 신규 leg·유동성 검사·시장약세 관찰·micro/rebound 입력과 frozen signal feature에 같은 실제 수량을 전달한다. 원장 로딩·기존 SELL 수량에는 날짜 override를 적용하지 않는다.
- widget: 검증된 원 정책을 복사한 신규 진입용 정책에만1주와 사용자 override receipt를 붙인다. canonical 정책 원문/hash·선정 veto를 보존하고 추가 leg와 목표매도는 해당 진입 원장의 실제 수량을 소비한다. 정책이 없는 기존 경로도 오늘 신규 BUY만1주다.
- 별도 날짜 정책 재발행이나 내일 재시작은 필요 없다. 기존 보유가 남아 있으면 기존 custody 계약이 신규 진입보다 우선한다.

## Review / validation

`korstockscan-review-gate`: 최초 구현의 누락 import를 보완하고 재검증했다. 변경 범위의 source→신규 계획→최종 주문→원장 reload→SELL/다음날 소비를 검토했으며 unresolved P0–P2 finding0.

- 핵심 owner 및 profit-stagnation/entry-adverse/target-ratchet/reentry 테스트601 PASS.
- 오후 에피소드·3개 preflight·entry-adverse 후행 테스트157 PASS.
- 전일10주 보유를9/11에도20주·각10주 목표 그대로 유지하는 추가 테스트1 PASS (동일 파일의 오늘/다음 거래일 테스트2개와 함께3 PASS).
- 고유759개 테스트. KST UTC 경계, naive timestamp 거절,1주 BUY/SELL, 두 leg 합계2, 위젯 추가매수·합산매도, 기존 정책 veto 보존을 포함한다.
- 격리 worktree에9/4 candidate와 직접 원천 report를 복사해 기존 fixture 결손을 해결했다. 운영 state를 공유한 테스트가 아니다. 실주문/Provider 호출/성과 report 재생성은 수행하지 않았다.
- Python compile 및 `git diff --check` PASS. 배포 전 마지막 source hash와 unit 명령/정책 pin을 다시 대사한다.

## 배포 경계와 후속

`deploy/machine-one-day-quantity/`의9개 drop-in을 검토했다. 위젯/삼성은 기존 f9d53a9a, 저가주는 기존4f073800 각각에 이번 변경만 적용한 별도 릴리스로 연결한다. 공통 main selector·cron·collector·timer 시각은 변경하지 않는다. 설치 시각/PID/commit/공유 경로 receipt는 아래에 추가한다.

기존 `MachineProfitStagnationStartupAcceptance0911`의 예정 기동/신규 entry 확인에서 실제 수량 receipt를 함께 확인한다. 설치와 미래 PID 소비를 구분한다. 다음 거래일 신규10주 복귀 관찰은 체크리스트의 별도 날짜 만료 확인에 남긴다. rollback은 기존 원장과 진행 중 SELL/취소를 보존해야 하며, 단순히 과거 수량값으로 보유를 재작성하지 않는다.

# 삼성E&A 수동매도 원장 정리

## 판정

사용자의 “삼성E&A 원장정리바람” 지시에 따라 `2026-09-10T14:39:57+09:00`에 전일 `samsung_ea_afternoon`의 HELD 10주를 COMPLETE 0주로 정리했다. 공통 소유권 원장에도 이미 실행된 수동 SELL을 정확한 기존 owner에 추가했다. 신규 주문·취소·정정·재기동·정책 활성화는 실행하지 않았다.

## 정확한 귀속과 증거

- 종목 `028050`, 진입 거래일 `2026-09-09`, owner/position `episode:samsung_ea_afternoon:028050:2026-09-09`.
- 대상 leg `signal_close`: BUY `0053206`, 원래 target `0053225`, 수동 successor SELL `0056859`의 10주 × 50,600원 체결/잔량 0을 당일 `kt00007(ord_dt=20260909)` 재조회로 확인했다. 원주문 연결과 수량·가격·SOR route는 보존된 broker receipt와 일치한다.
- 이미 완료된 다른 leg와 기존 BUY 필드·주문번호 목록·진입일·attempt_consumed는 변경하지 않았다. 원래 target 번호를 수동 successor로 덮어쓰지 않고 `manual_exit_receipt`와 `exit_fill_source`로 구분했다.
- 정확한 체결시각은 dated receipt에 없어 빈 값과 `unavailable_from_dated_order_receipt`를 유지했다. 주문시각 15:03:41을 체결시각으로 합성하지 않았고, 미확인 비용·순이익도 생성하지 않았다.
- 보존 증거: `tmp/intraday-monitor-20260910-0830/samsung-ea-manual-sale.json`, SHA256 `bb6028f6a82dc0721b1c04e0c2594a818dd6116b1d6dec0a205498e38016e1d7`.

## 적용과 검증

- 운영 경로는 고정 배포본 `holding-input-76995257`의 기존 `manual_episode_exit_reconciliation.reconcile_manual_exit`와 `OrderOwnerRegistry.register_reconciled_manual_exit`를 사용했다. 다른 세션의 미커밋 코드와 배포본은 변경하지 않았다.
- 원본 3개를 잠금 아래 `tmp/samsung-ea-ledger-reconcile-20260910-eoOzgM/`에 백업했다: `samsung_ea_afternoon_state.json`, `episode_manual_exit_receipts.json`, `order_owner_registry.jsonl`.
- 사전 dry-run ready 및 관련 테스트 `test_manual_episode_exit_reconciliation.py`, `test_symbol_owner_coexistence.py`: **112 passed**.
- receipt registry에는 applied 1건, 공통 원장에는 `MANUAL_EXIT_RECONCILED` 1건만 대상 종목에 추가했다. intent `de4c1bdcbf5b431b9ddf5940dee8123f`; 기존 원장 prefix/hash chain은 그대로다.
- 첫 사후 검증의 “백업 이후 전체 추가 이벤트 1건” 가정은 다른 정상 가동 owner의 동시 기록으로 실패했다. 종목/owner별 검증으로 재점검한 결과 삼성E&A 추가 이벤트는 정확히 1건이고, 나머지 4건은 별도 `fan_ocean_afternoon`의 자연 주문 기록이었다. 이를 삭제하거나 백업으로 덮어쓰지 않았다.
- 14:38:21 사전 및 14:40:24 사후 KRX/NXT 대사에서 삼성E&A 실제 잔고·미체결 0. 사후 공통 원장 registered 0 / broker 0 / manual remainder 0 / balanced true로 과거 deficit 해소를 확인했다.
- 대상 service는 전후 inactive/MainPID 0. 현재 메인 PID `772330`과 활성 정책은 건드리지 않았고, 오늘 신규 episode를 만들거나 아침의 policy 제외 artifact를 다시 발행하지 않았다.

원장 정합성 복구가 거래 수익 개선·새 정책 승인·오늘 기계 READY 성공을 의미하지 않는다. 현재 자연 기동/경제성 수락은 기존 일일 checklist owner에 남긴다. 과거 14:30 모니터링 기록은 당시 상태의 증거로 보존한다. 공통 원장 백업 전체 복원은 동시 기록을 잃게 하므로 자동 rollback 수단으로 사용하지 않는다.

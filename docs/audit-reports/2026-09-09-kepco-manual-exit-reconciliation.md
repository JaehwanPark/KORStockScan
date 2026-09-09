# 한국전력 수동 손절 원장 대사

## 판정

2026-09-09 사용자 지시 `한국전력 손절 수동매도 처리함`에 따라 이미 체결된 오전 기계 20주를 수동 손절로 귀속했다. `episode:kepco_morning:015760:2026-09-09` 원장과 공통 registry의 잔여 수량은 모두 0, episode는 `COMPLETE`다. 신규 주문·취소·정정·서비스 기동/종료/재기동·정책 변경은 실행하지 않았다.

## 체결과 owner

| Leg | 매수 | 원래 목표 주문 | 수동 정정매도 | 수량 / 체결가 | 비용 전 손익 |
| --- | --- | --- | --- | --- | --- |
| signal_close | 0021470 / 34,700원 | 0021516 | 0062072, ori_ord=0021516 | 10주 / 33,950원 | -7,500원 |
| signal_close_minus_1tick | 0021473 / 34,650원 | 0021521 | 0062075, ori_ord=0021521 | 10주 / 33,950원 | -7,000원 |

- kt00007의 수동 매도 채널은 영웅문S#, 정정확인이다. 원래 목표 주문은 체결 0·잔량 0이며 공통 registry에서도 이미 `ORDER_TERMINAL`이었다. 이를 자동 목표 체결로 바꾸지 않고, 기존 native `reconcile_manual_exit`와 `register_reconciled_manual_exit`로 각 수동 successor를 기록했다.
- 매수금액 합계 693,500원, 매도금액 679,000원, **비용 전 실현손익 -14,500원**이다. 정확한 broker 수수료·세금 및 비용 차감 실현손익은 미확인/null이며 모델 비용을 실제 비용으로 대체하지 않았다.
- `16:23:03`·`16:23:11`은 주문/정정 시각이다. 정확한 체결시각·holding duration은 null로 유지하고 복구시각과 분리했다. broker route `SOR`를 보존하며 개별 체결 venue를 추정하지 않았다.
- kt00005 KRX/NXT 조회·정규화 계약 정상, 현재 한국전력 잔고 0주. ka10075 미체결 0건, kt00007 14행이며 정상 응답·정규화·페이지 잘림 없음. 다른 owner의 공통 registry 보유수량은 0이다.
- 정오·오후 기계는 각자의 기존 목표 체결로 이미 완료됐으며 이번 손절과 합산하지 않았다. 해당 state 및 오전후반 state SHA256은 적용 전후 불변이다. widget 종목 state는 없었다.
- 오전 서비스 `inactive`, `MainPID=0`, state lock 점유 없음. 실제 적용 직전 서비스·fresh broker·원본 state SHA를 재검증했다. 기존 거래일·진입가격·목표 설정·주문목록·신호·시도 소진 상태는 보존했다.

## 검증과 증거

`korstockscan-review-gate`를 사용해 이 원장 귀속 범위의 사본 적용 → 검토 → 실제 적용 → 재검증을 수행했다. 소스 코드는 수정하지 않았고 다른 작업의 dirty 변경은 보존했다.

- 관련 manual 테스트: 41 passed, 71 deselected (`test_manual_episode_exit_reconciliation.py`, `test_symbol_owner_coexistence.py`, `-k manual`).
- 사본에서 두 주문의 exact leg 배분, registry 20→0, 중복 등록 차단을 검증했다.
- 실제 반영 후 직접 consumer `_sanitize_leg`가 두 leg를 `manual_operator_exit`, `manual_exit_realized=true`, 실현일 9/9, 체결가 33,950원으로 해석함을 확인했다. 전체 report 재생성은 하지 않았다.
- 공통 registry의 수동 exit intent는 각각 `4591e3ef559a4c87b627a02ad8b83413`, `f466d28622d8449b975664b2cc722413`이다. 실행 owner는 `manual_operator`, custody owner는 오전 episode로 유지했다.
- 증거·원장/registry 전후 백업·staged/applied 검증: `data/runtime/manual_close_reconciliation/kepco_20260909_0062072_0062075.QHROra/`.
- `evidence.json` SHA256: `7b31f807535aede10bc4c9d0308799b1998a578d9123820ed94aabed939dbb97`.

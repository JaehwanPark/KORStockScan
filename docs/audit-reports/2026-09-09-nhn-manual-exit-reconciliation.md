# NHN 수동 손절 원장 대사

## 판정

2026-09-09 사용자 지시 `nhn 손절 수동매도 처리함`에 따라 이미 체결된 오전후반 기계 20주를 수동 손절로 귀속했다. `episode:nhn_late_morning:181710:2026-09-09` 원장과 공통 registry의 잔여 수량은 모두 0, episode는 `COMPLETE`다. 신규 주문·취소·정정·서비스 기동/종료/재기동·정책 변경은 실행하지 않았다.

## 체결과 owner

| Leg | 매수 | 원래 목표 주문 | 수동 정정매도 | 수량 / 체결가 | 비용 전 손익 |
| --- | --- | --- | --- | --- | --- |
| signal_close | 0031837 / 59,500원 | 0031848 | 0061767, ori_ord=0031848 | 10주 / 58,100원 | -14,000원 |
| signal_close_minus_1tick | 0031838 / 59,400원 | 0031887 | 0062534, ori_ord=0031887 | 10주 / 58,100원 | -13,000원 |

- kt00007의 수동 매도 채널은 영웅문S#, 정정확인이다. 원래 목표 주문은 체결 0·잔량 0이며 공통 registry에서도 이미 `ORDER_TERMINAL`이었다. 이를 자동 목표 체결로 바꾸지 않고 기존 native `reconcile_manual_exit`와 `register_reconciled_manual_exit`로 각 수동 successor를 기록했다.
- 매수금액 합계 1,189,000원, 매도금액 1,162,000원, **비용 전 실현손익 -27,000원**이다. 정확한 broker 수수료·세금 및 비용 차감 실현손익은 미확인/null이며 모델 비용을 실제 비용으로 대체하지 않았다.
- `16:10:03`·`16:56:31`은 주문/정정 시각이다. 정확한 체결시각·holding duration은 null로 유지하고 복구시각과 분리했다. broker route `SOR`를 보존하며 개별 체결 venue를 추정하지 않았다.
- kt00005 KRX/NXT 조회·정규화 계약 정상, 현재 NHN 잔고 0주. ka10075 미체결 0건, kt00007 10행이며 정상 응답·정규화·페이지 잘림 없음이다. 다른 owner의 공통 registry 보유수량은 0이다.
- 오후 기계는 두 leg 모두 기존 목표 체결로 완료돼 있었다. 해당 거래는 이번 손절과 합산하지 않았으며, 오전·정오·오후 state SHA256은 적용 전후 불변이다. widget 종목 state는 없었다.
- 오전후반 서비스 `inactive`, `MainPID=0`, state lock 점유 없음. 실제 적용 직전 서비스·fresh broker·원본 state SHA를 재검증했다. 기존 거래일·진입가격·목표 설정·주문목록·신호·시도 소진 상태는 보존했다.

## 검증과 증거

`korstockscan-review-gate`를 사용해 이 원장 귀속 범위의 사본 적용 → 검토 → 실제 적용 → 재검증을 수행했다. 소스 코드는 수정하지 않았고 다른 작업의 dirty 변경은 보존했다.

- 관련 manual 테스트: 41 passed, 71 deselected (`test_manual_episode_exit_reconciliation.py`, `test_symbol_owner_coexistence.py`, `-k manual`).
- 사본에서 두 주문의 exact leg 배분, registry 20→0, 중복 등록 차단을 검증했다.
- 실제 반영 후 직접 consumer `_sanitize_leg`가 두 leg를 `manual_operator_exit`, `manual_exit_realized=true`, 실현일 9/9, 체결가 58,100원으로 해석함을 확인했다. 전체 report 재생성은 하지 않았다.
- 공통 registry의 수동 exit intent는 각각 `cc7c54f80f644993bc18eaf6def61de4`, `f6eaf0ec72a84368adadc9b7449d1ecf`이다. 실행 owner는 `manual_operator`, custody owner는 오전후반 episode로 유지했다.
- 증거·원장/registry 전후 백업·staged/applied 검증: `data/runtime/manual_close_reconciliation/nhn_20260909_0061767_0062534.yDOHx1/`.
- `evidence.json` SHA256: `72612ba680a8a6dc19b388865c2e645f041448e9274c2142449681b3c6f9c93e`.

# 삼성중공업 수동 손절 원장 대사

## 판정

2026-09-09 사용자 지시 `삼성중공업 손절 수동매도 처리함`에 따라 이미 체결된 매도만 귀속했다. `samsung_heavy_morning`의 9/8 이월 10주는 `COMPLETE`, 잔여 0주다. 신규 주문·취소·정정·서비스 기동/종료/재기동·정책 변경은 실행하지 않았다.

## 근거와 반영

- 원 owner/position: `episode:samsung_heavy_morning:010140:2026-09-08`. 매수 `0018066`, 10주 × 21,700원. 다른 leg `0018068`은 미체결 `NO_FILL`이며 그대로 보존했다.
- 9/9 영웅문S# 수동 SELL 정정 계보: `0001493 → 0061971 → 0062300`. 마지막 주문은 10주 전량 체결, 체결가 21,600원, 미체결 0주다. 정정/주문시각 `16:39:33`은 정확한 체결시각으로 대체하지 않았다. broker route는 `SOR` 그대로 보존하며 개별 체결 venue를 추정하지 않았다.
- 9/8 자동 목표 주문 `0018672`는 체결 0주였고, 원장에 `20:19:39 target_terminal_absence_position_held`가 있었다. 과거 kt00007의 잔량 10주는 과거 기록이며 현재 활성 주문이 아니다. 현재 ka10075 미체결 부재와 함께 공통 registry의 해당 목표 주문만 `ORDER_TERMINAL`로 대사했다. 수동 successor를 자동 목표 체결로 바꾸지 않았다.
- 현재 kt00005 KRX/NXT 계약 정상, 삼성중공업 잔고 0주; ka10075 미체결 0건. 9/8·9/9 kt00007 각각 4행·3행이며 정상 응답/정규화, 잘린 페이지 없음. 다른 삼성중공업 episode의 원장 수량 0, widget 종목 state 없음, 공통 registry의 다른 position 수량 0을 확인했다.
- 오전 서비스 `inactive`, `MainPID=0`; state lock 점유 없음. 기존 native `reconcile_manual_exit`와 `register_reconciled_manual_exit`를 사용했다. 원장 거래일은 9/8을 유지하고 실현일은 receipt의 9/9로 구분했다. 기존 주문번호·signal·진입가격·target 설정·시도 소진 상태는 보존했다.
- 공통 registry 수동 청산 intent: `e29bc826a7f546d694721e4fc99d7262`, 실행 owner `manual_operator`, custody owner는 위 episode다. episode 원장과 공통 registry 잔여 수량 모두 0이다.
- 실현 매도금액 216,000원, 매수금액 217,000원, **비용 전 손익 -1,000원**. exact broker 수수료·세금과 비용 차감 실현손익은 미확인이다. 모델 비용과 실제 비용을 혼동하거나 미확인 비용을 0으로 기록하지 않았다.

## 검증

`korstockscan-review-gate` 범위는 해당 체결의 원장·공통 registry 귀속이다. 관련 코드 수정은 없으며 진행 중인 다른 작업의 dirty 코드는 수정하지 않았다.

- live 원본 백업 후 별도 사본에서 native 적용과 registry 수량 10→0을 먼저 검증했다.
- `test_manual_episode_exit_reconciliation.py`: 33 passed.
- `test_symbol_owner_coexistence.py -k manual_exit`: 1 passed, 78 deselected.
- 직접 소비자 `_sanitize_leg`는 `manual_operator_exit`, `manual_exit_realized=true`, 실현일 9/9, 체결가 21,600원으로 해석했다. 정확한 체결시각과 holding duration은 null이다. 미체결 leg는 byte-equivalent JSON 값이며 기존 신호·주문목록·거래일을 보존했다.
- 위 검증 후 fresh broker 조회, 서비스 비가동, 원본 state SHA 불변을 다시 확인하고 실제 적용했다. 고비용 전체 report 재생성은 하지 않았다.

증거·원장/registry 전후 백업·staged/applied 검증은 `data/runtime/manual_close_reconciliation/samsung_heavy_20260909_0062300.lheb8z/`에 보존했다. `evidence.json` SHA256: `7377fcf767891f1f8fa3354ea45502b4807f619148d7f31a3b46151ba4a605cb`.

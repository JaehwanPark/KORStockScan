# 한화오션 수동 손절 원장 대사

## 판정

2026-09-09 사용자 지시 `한화오션 손절 수동매도 처리함`에 따라 이미 체결된 오전후반 기계의 잔여 10주를 수동 손절로 귀속했다. `episode:hanwha_ocean_late_morning:042660:2026-09-09` 원장과 공통 registry의 잔여 수량은 모두 0, episode는 `COMPLETE`다. 신규 주문·취소·정정·서비스 기동/종료/재기동·정책 변경은 실행하지 않았다.

## 체결과 귀속

- 대상 leg `signal_close`: 매수 `0027493`, 10주 × 88,200원. 원래 목표 주문 `0027525`는 체결 0·잔량 0이며 공통 registry에서도 이미 `ORDER_TERMINAL`이었다.
- 수동 정정매도 `0061957`, `ori_ord=0027525`, 영웅문S# 채널, 10주 × 88,100원 전량 체결. 현재 kt00005 KRX/NXT 계약 정상·한화오션 잔고 0주, ka10075 미체결 0건. kt00007 5행, 정상 응답·정규화·페이지 잘림 없음이다.
- 이번 수동 손절분 매수금액 882,000원, 매도금액 881,000원, **비용 전 손익 -1,000원**. 실제 broker 수수료·세금 및 비용 차감 실현손익은 미확인/null이다. 모델 비용을 실제 비용으로 대체하지 않았다.
- 다른 leg `signal_close_minus_1tick`는 매수 `0027494`, 88,100원 × 10주 → 자동 목표 매도 `0027803`, 88,500원 × 10주로 이미 완료돼 있었다. 그 비용 전 이익 +4,000원은 이번 손절과 구분하며, 해당 leg의 JSON 값 전체를 그대로 보존했다.
- `16:15:54`은 수동 주문/정정 시각이다. 정확한 체결시각과 holding duration은 null로 유지하고 복구시각과 구분했다. broker route `SOR`를 보존하며 개별 체결 venue를 추정하지 않았다.
- 다른 공통 registry position의 보유수량은 0이었다. widget의 당일 종목 주문목록은 비어 있고 이월 수동 수량은 0이다. widget 원장은 수정하지 않았다.
- 오전후반 서비스 `inactive`, `MainPID=0`, state lock 점유 없음. 실제 반영 직전 fresh broker·서비스·원본 state SHA를 재검증했다. 기존 거래일·주문목록·신호·시도 소진 상태·진입가격·목표 설정을 보존했다.

## 검증과 증거

`korstockscan-review-gate`를 사용해 이 체결 귀속 범위의 사본 적용 → 검토 → 실제 반영 → 재검증을 수행했다. 소스 코드는 수정하지 않았고 다른 작업의 dirty 변경은 보존했다.

- 기존 native `reconcile_manual_exit`와 `register_reconciled_manual_exit`를 사용했다. 수동 매도를 원래 목표 체결로 흡수하지 않았다.
- 관련 manual 테스트 41 passed, 71 deselected (`test_manual_episode_exit_reconciliation.py`, `test_symbol_owner_coexistence.py`, `-k manual`).
- 사본에서 exact leg 귀속, registry 10→0, 중복 등록 차단, 기존 자동 익절 leg 불변을 검증했다.
- 실제 적용 후 직접 consumer `_sanitize_leg`는 대상 leg를 `manual_operator_exit`, `manual_exit_realized=true`, 실현일 9/9, 체결가 88,100원으로 해석했다. 기존 자동 익절 leg는 수동 청산으로 재분류하지 않았다. 전체 report 재생성은 하지 않았다.
- 공통 registry 수동 exit intent: `358147b849974a4f90e55b0d9cd7017e`. 실행 owner는 `manual_operator`, custody owner는 기존 episode다.
- 증거·원장/registry 전후 백업·staged/applied 검증: `data/runtime/manual_close_reconciliation/hanwha_ocean_20260909_0061957.UYsyRv/`.
- `evidence.json` SHA256: `b264bed47f1a7b1d89691e66f92a9832de19f768d3d3891ed24ad8b35669021d`.

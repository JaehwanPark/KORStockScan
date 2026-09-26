# 2026-09-25 보유 익절 정리 코드리뷰

## 범위와 결론

NXT TP1 부분익절의 신규 주문 생산자·호출·설정 전달을 제거하고, `scalp_mfe_protect_exit`의 판정·SELL 후보·설정 및 장후 임계치 추천을 제거했다. 이전에 실제 제출된 NXT 부분 주문의 체결·수량·비용·잔량 복구와 과거 보고서 분류는 보관한다. 이는 새 TP1 권한이 아니며, 기존 주문 영수증을 버리면 `SELL_ORDERED` 잔량이 고아가 될 수 있기 때문이다. 현행 bootstrap은 두 제거 분기의 env prefix를 수거한다.

프리마켓 세션 계약의 구·신 버전 모두 `exit_allowed_by_clock=true`로 바꿨다. 이 플래그는 시계 허용에 한정된다. 실제 주 익절은 별도 NXT/KRX route, 유효 0D·bid, 주문·수량·쿨다운 검사를 통과해야 한다. 시작 수익률 기본값과 세 시장 bootstrap 기준선은 고점의 비용 후 순수익 `+0.4%`로 맞췄다. 이전 0.6% env를 보존한 incumbent가 다시 공급하지 않도록 bootstrap owner를 명시했으며, 별도 검증된 새 선택 후보는 rollback-parent 계약으로 평가된다.

## 공식 Kiwoom 참조

2026-09-25 19:57:51 KST에 공식 `Kiwoom-Securities/Kiwoom-REST-API` HEAD `953e5dbff123f437ab4d11a78a95191a685eb51f`를 조회했다. `kiwoom/specs.py`, `kiwoom/core/client.py`, `kiwoom/_data/kiwoom_api_spec.json`의 `kt10001`과 `postman/kiwoom-openapi.postman_collection.json`의 운영 주문 envelope를 확인했다. 공식 트리에는 `kiwoom_docs`가 없다. `kt10001`은 `/api/dostk/ordr` POST, `api-id`, Bearer 인증과 `dmst_stex_tp`, 양수 `ord_qty`, `trde_tp`를 요구한다. 이번 변경은 신규 TP1 주문 호출을 제거하고 기존 일반 SELL adapter 및 broker receipt parser wire를 변경하지 않는다. 실제 API·계좌·주문 호출은 하지 않았다.

## 리뷰와 보완

1. 첫 검토에서 코드 기본값만 0.4로 바꾸면 장후 bootstrap이 0.6 incumbent env를 다시 보존하는 결함을 발견했다. bootstrap의 세 시장 값과 owner를 0.4로 결속하고 과거 direct selector의 rollback parent를 재검증하게 했다.
2. 이전 부분 매도 주문의 terminal receipt가 남아 있을 수 있어 receipt-only 복구 경로는 보존했다. 신규 부분 매도 생산자와 날짜/enable 스위치만 제거한다. stale reset/state 필드는 기존 주문 처리용이다.
3. 프리마켓의 공유 exit clock을 열어도 route/quote가 거부하면 실주문은 차단된다. 이는 안전 계약이며 `exit_allowed_by_clock=true`만으로 실주문 성공을 주장하지 않는다.
4. 2026-09-25 일일 stage2 checklist가 없어 현재 OPEN owner를 확인할 수 없었다. 2026-09-28 파일은 미래 owner이므로 대체하지 않았다.

## 검증 경계

수정 Python 파일은 compile 문법 검사와 `git diff --check`로 확인한다. 이번 요청은 코드리뷰·수정보완이며 test 실행은 별도 지시 전까지 수행하지 않는다. 배포·PID 전환·실제 체결 또는 새 기준값의 자연 수익 증거는 이 리뷰의 결론에 포함하지 않는다.

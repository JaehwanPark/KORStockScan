# 위젯 신호 자동매매 실행기 운영 계약

## 범위와 권한

`src.trading.widget_auto_trade`는 삼성전자(005930), 두산에너빌리티(034020),
한화오션(042660) 위젯 수집기가 만든 source-qualified 공개 신호를 소비하는
별도 실주문 owner다. 위젯 producer의 `authority=widget_advisory_only`,
`runtime_effect=false`, `broker_order_forbidden=true` 계약은 변경하지 않는다.
실주문 권한은 실행기의 `operator_directed_widget_auto_trade_v1`에만 있다.

메인 봇과 동일 종목을 동시에 제어하지 않도록 대상 종목에는
`manual_operator` 수동관리 제외가 반드시 있어야 한다. 자동 손실 제외나 주석
없는 일반 제외는 실행기 소유권으로 인정하지 않는다.

## 신호와 주문 계약

- `ENTRY_CAUTION`, `ENTRY_READY`의 새 진입 에피소드마다 1회 매수한다.
  동일 에피소드의 10초 스냅샷 반복이나 CAUTION에서 READY로의 지속 상태는
  중복 주문으로 보지 않는다.
- 기본 수량은 1주이며 `KORSTOCKSCAN_WIDGET_AUTO_TRADER_ENTRY_QTY`로 변경한다.
  코드상 허용 범위는 1~100주다.
- 두산에너빌리티·한화오션은 immutable `entry_event`/`exit_event`를 사용한다.
  삼성전자는 유효한 actionable advisory로 진입하고 `EXIT_READY`만 최종 청산으로
  사용한다. `EXIT_CAUTION`과 비최종 상태는 주문 권한이 없다.
- 같은 스냅샷에 진입과 최종 청산이 함께 있으면 청산이 우선한다.
- KRX 매수와 NXT 매수는 최유리지정가(`trde_tp=6`)를 사용한다. 최종 매도는
  KRX 시장가(`trde_tp=3`), NXT 최유리지정가(`trde_tp=6`)를 사용한다.
- 주문가능현금·예수금 조회를 선행하지 않는다. 이 실행기는 국내주식 일반주문
  `kt10000`/`kt10001`을 제출하며, 미수 허용 여부와 최종 접수는 계좌 설정과
  증권사 응답이 결정한다. 신용주문 `kt10006`으로 바꾸지 않는다.
- 전역 BUY 일시정지, 신호 freshness/venue 계약, 단일 실행기 lock, 수량 상한,
  미체결 중복 방지는 우회하지 않는다.

## 당일 원장과 날짜 초기화

매도 가능 수량은 broker 보유수량이 아니라 실행기가 당일 접수한 주문번호를
`kt00007`로 조회해 확인한 매수 체결수량에서 당일 매도 체결수량을 뺀 값이다.
따라서 수동 매수분, 메인 봇 매수분, 전일 위젯 매수분은 매도하지 않는다.

거래일이 바뀌면 상태를 무조건 새 원장으로 초기화한다. 전일 미청산 수량과
미해결 주문은 `history[].unmanaged_overnight_qty`와 주문 이력으로만 보존한다.
자동 청산·취소·이월 reconciliation은 하지 않는다. 다음날 새 진입 신호가 오면
다시 설정 수량을 매수하며, 그날 최종 청산 신호는 그날 확인된 체결수량만 판다.

## 토큰과 장애 처리

`get_cached_kiwoom_token`만 사용한다. 토큰 신규 발급, 갱신, 8005 자동 재발급은
없으며 캐시 토큰이 없으면 주문을 실패 처리한다. 주문 intent는 broker 호출 전에
원자적으로 저장한다. 호출 결과가 불명확하면 `AMBIGUOUS`로 닫아 같은 신호를
재제출하지 않는다. 접수 주문은 정확한 주문번호로만 체결 귀속한다.

## 배포와 롤백

서비스 원본은
`deploy/systemd/korstockscan-widget-signal-auto-trader.service`다. 이 파일은 저장소에
추가된 것만으로 실행되지 않는다. 운영자가 systemd에 설치·enable/start해야 실제
주문이 시작된다. 시작 전 3개 collector freshness, 공유 토큰, 세 종목의
`manual_operator` 제외를 확인한다.

즉시 롤백은 서비스를 stop/disable하는 것이다. 재시작 전
`data/runtime/widget_signal_auto_trade_state.json`의 `SUBMITTING`, `SUBMITTED`,
`CANCEL_REQUESTED`, `AMBIGUOUS` 주문을 확인한다. 상태 파일 삭제는 중복 주문 또는
당일 매도 원장 유실을 만들 수 있으므로 장중에는 금지한다.

## 공식 Kiwoom 계약 검증

2026-08-08 13:11:22 KST에 공식
`Kiwoom-Securities/Kiwoom-REST-API` commit
`69642586f7d84ba9fd8a6faf1f1537c7fda6568b`의 `kiwoom_docs/주문.md`,
`kiwoom_docs/계좌.md`, `kiwoom/_data/kiwoom_api_spec.json`, `kiwoom/specs.py`,
Postman collection을 확인했다. 적용 API는 `kt10000`, `kt10001`, `kt10003`,
`kt00007`이며 REST 경로, 헤더, 주문 필드, KRX/NXT route와 continuation 계약을
교차검증했다.

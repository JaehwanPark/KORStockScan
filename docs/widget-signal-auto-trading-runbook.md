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

- source-qualified `ENTRY_CAUTION`, `ENTRY_READY`의 새 진입 에피소드마다 1회
  매수한다. 단, 삼성전자는 15~30분 하락 레짐을 벗어났거나 고점·저점 상승으로
  구조 회복을 확인하고, 직전 저항을 회복한 뒤 직전 두 확정 1분봉 종가가 그
  저항을 엄격히 상회해야 실행기가 신호를 소비한다. 이 조건은 진입을 새로
  만들지 않는 negative execution qualification이며 두산·한화 이벤트형 신호에는
  적용하지 않는다. 동일 에피소드의 10초 스냅샷 반복이나 CAUTION에서 READY로의
  지속 상태는 중복 주문으로 보지 않는다.
- 기본 수량은 1주이며 `KORSTOCKSCAN_WIDGET_AUTO_TRADER_ENTRY_QTY`로 변경한다.
  코드상 허용 범위는 1~100주다.
- 주문 대상은 `KORSTOCKSCAN_WIDGET_AUTO_TRADER_SYMBOLS`의 쉼표 구분 code
  allowlist로 제한한다. 변수를 명시한 경우 빈 값이나 미등록 code는 전체 종목으로
  되돌아가지 않고 기동을 실패시킨다. 현재 운영값은 삼성전자 `005930`만이며
  두산에너빌리티 `034020`과 한화오션 `042660`은 수집·신호·장후 calibration은
  유지하되 자동매매 대상에서 제외한다.
- 두산에너빌리티·한화오션은 immutable `entry_event`/`exit_event`를 사용한다.
  삼성전자는 유효한 actionable advisory로 진입하고 `EXIT_READY`만 최종 청산으로
  사용한다. `EXIT_CAUTION`과 비최종 상태는 주문 권한이 없다.
- 같은 스냅샷에 진입과 최종 청산이 함께 있으면 청산이 우선한다.
- KRX 매수와 NXT 매수는 최유리지정가(`trde_tp=6`)를 사용한다. 최종 매도는
  KRX 시장가(`trde_tp=3`), NXT 최유리지정가(`trde_tp=6`)를 사용한다.
- 매수 주문번호의 체결을 `kt00007`에서 확인하면 체결 평균가 대비 최소
  `+1.00%`가 되는 첫 유효 호가에 체결수량만큼 보통 지정가
  (`kt10001`, `trde_tp=0`) 익절 주문을 제출한다. 부분체결은 새로 확인된
  미보호 수량만 추가 주문하며, 수수료·세금은 목표가 계산에 가산하지 않는다.
- 최종 `EXIT_READY`가 익절 주문보다 먼저 발생하면 `kt10003`으로 익절 잔량을
  취소한다. 원 주문번호 조회에서 취소·부분체결 수량이 확정되기 전에는 최종
  청산 주문을 제출하지 않으며, 확정 뒤 당일 위젯 원장의 남은 수량만 판다.
- 익절 제출 결과가 불명확하면 중복 매도·초과 매도를 막기 위해 자동 재제출과
  최종 청산을 차단하고 해당 intent를 운영자 확인 대상으로 남긴다. 명시적
  주문 거절만 5초 간격, 최대 3회 재시도한다.
- 주문가능현금·예수금 조회를 선행하지 않는다. 이 실행기는 국내주식 일반주문
  `kt10000`/`kt10001`을 제출하며, 미수 허용 여부와 최종 접수는 계좌 설정과
  증권사 응답이 결정한다. 신용주문 `kt10006`으로 바꾸지 않는다.
- 전역 BUY 일시정지, 신호 freshness/venue 계약, 단일 실행기 lock, 수량 상한,
  미체결 중복 방지는 우회하지 않는다.

## 당일 원장과 날짜 초기화

매도 가능 수량은 broker 보유수량이 아니라 실행기가 당일 접수한 주문번호를
`kt00007`로 조회해 확인한 매수 체결수량에서 당일 매도 체결수량을 뺀 값이다.
따라서 수동 매수분, 메인 봇 매수분, 전일 위젯 매수분은 매도하지 않는다.
메인 봇의 broker-only holding 복구도 `manual_operator` 제외 종목은 건너뛰어,
위젯 체결분을 메인 봇 `HOLDING`과 별도 매도 owner로 편입하지 않는다.

거래일이 바뀌면 상태를 무조건 새 원장으로 초기화한다. 전일 미청산 수량과
미해결 주문과 익절 주문은 `history[].unmanaged_overnight_qty`와 주문 이력으로만 보존한다.
자동 청산·취소·이월 reconciliation은 하지 않는다. 다음날 새 진입 신호가 오면
다시 설정 수량을 매수하며, 그날 최종 청산 신호는 그날 확인된 체결수량만 판다.

## 토큰과 장애 처리

`get_cached_kiwoom_token`만 사용한다. 토큰 신규 발급, 갱신, 8005 자동 재발급은
없으며 캐시 토큰이 없으면 주문을 실패 처리한다. 주문 intent는 broker 호출 전에
원자적으로 저장한다. 호출 결과가 불명확하면 `AMBIGUOUS`로 닫아 같은 신호를
재제출하지 않는다. 접수 주문은 정확한 주문번호로만 체결 귀속한다.

## 배포와 롤백

서비스 원본은
`deploy/systemd/korstockscan-widget-signal-auto-trader.service`, 일일 기동 owner는
`deploy/systemd/korstockscan-widget-signal-auto-trader.timer`다. 서비스 unit은
static이며 직접 enable하지 않는다. 평일 07:58 KST timer만 enable해 07:55 메인 봇
기동과 당일 공유 토큰 준비 뒤 서비스를 시작한다. 서버가 07:58 이후 기동되면
`Persistent=true`에 따라 누락된 기동을 보충하지만, 주문 전 shared cached token과
source freshness guard는 그대로 적용한다. 시작 전 3개 collector freshness, 공유
토큰, allowlist 대상 종목의 `manual_operator` 제외를 확인한다.

allowlist에서 빠진 종목은 신규 주문뿐 아니라 기존 실행기 원장의 reconciliation과
자동 청산도 수행하지 않는다. 따라서 장중 제외 전에는 해당 종목의 활성 주문과
당일 원장 수량을 확인해야 하며, 상태 파일을 삭제해 중복 주문을 유발해서는 안 된다.

설치 시 service와 timer 파일을 `/etc/systemd/system/`에 배치한 뒤 service의 기존
boot enable을 제거하고 timer만 enable한다. `systemctl enable
korstockscan-widget-signal-auto-trader.service`는 기동 owner를 중복시키므로 금지한다.

즉시 롤백은 timer를 disable하고 서비스를 stop하는 것이다. 재시작 전
`data/runtime/widget_signal_auto_trade_state.json`의 `SUBMITTING`, `SUBMITTED`,
`CANCEL_REQUESTED`, `AMBIGUOUS` 주문을 확인한다. 상태 파일 삭제는 중복 주문 또는
당일 매도 원장 유실을 만들 수 있으므로 장중에는 금지한다.

## 공식 Kiwoom 계약 검증

2026-08-10 09:49:53 KST에 공식
`Kiwoom-Securities/Kiwoom-REST-API` commit
`69642586f7d84ba9fd8a6faf1f1537c7fda6568b`의 `kiwoom_docs/주문.md`,
`kiwoom_docs/계좌.md`, `kiwoom/_data/kiwoom_api_spec.json`, `kiwoom/specs.py`,
Postman collection을 확인했다. 적용 API는 `kt10000`, `kt10001`, `kt10003`,
`kt00007`이며 REST 경로, 헤더, 주문 필드, KRX/NXT route와 continuation 계약을
교차검증했다.

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
- 2026-08-13 11:31 KST 이후 신규 매수 leg의 운영 수량은 10주다.
  `KORSTOCKSCAN_WIDGET_AUTO_TRADER_ENTRY_QTY`, legacy fallback 정책, 장후 생성
  exact-date 정책의 `leg_quantity_each`가 모두 10으로 일치해야 기동한다. 기존
  에피소드와 이미 접수된 주문은 원래 수량으로 계속 귀속한다. 정책에 2개
  추가매수 leg가 선택되면 한 에피소드의 최대 신규 매수 노출은 30주다.
- 주문 대상은 `KORSTOCKSCAN_WIDGET_AUTO_TRADER_SYMBOLS`의 쉼표 구분 code
  allowlist로 제한한다. 변수를 명시한 경우 빈 값이나 미등록 code는 전체 종목으로
  되돌아가지 않고 기동을 실패시킨다. 현재 service allowlist에는 삼성전자
  `005930`, 두산에너빌리티 `034020`, 한화오션 `042660`이 있으나 exact-date
  정책의 `new_entry_runtime_eligible=true`인 종목·세션만 실제 신규 주문이 가능하다.
  수집·신호·장후 calibration 대상이라는 이유만으로 주문 권한을 얻지 않는다.
- 두산에너빌리티·한화오션은 immutable `entry_event`/`exit_event`를 사용한다.
  삼성전자는 유효한 actionable advisory로 진입하고 `EXIT_READY`만 최종 청산으로
  사용한다. `EXIT_CAUTION`과 비최종 상태는 주문 권한이 없다.
- 두산에너빌리티·한화오션의 실주문 승격은 매일 20:10 장후
  `widget_auto_trade_policy_calibration --write`가 단독으로 소유한다. clean
  baseline 범위 안에서 2026-08-12부터 각 종목의 40개 qualified KRX 관측일,
  calibration/chronological holdout, source quality, execution-quality safety gate를
  모두 통과한 세션만 다음
  KRX 영업일 exact-date 정책에 기록된다. 자동매매기는 07:58 기동 또는 거래일
  전환 시 그 정책을 다시 읽어 `new_entry_runtime_eligible=true`인 종목·세션을
  자동으로 주문 적격으로 연다. 수동 정책 복사나 별도 장중 재기동은 필요하지
  않으며, 한 조건이라도 실패하면 동일 exact-date 정책의 명시적 blocked session을
  읽어 관측만 계속한다.
- 삼성전자의 신규 세션/파라미터 승격은 독립 holdout의 목표 청산 확인을 계속
  요구한다. 다만 전일 exact-date 정책으로 이미 검증·가동된 세션은 누적 후보가
  계속 유효하고 당일 holdout이 무신호 또는 미청산(right-censored)으로 아직
  성숙하지 않은 경우에만 전일 파라미터를 그대로 carry-forward한다. 이 경로는
  새 파라미터를 적용하지 않으며 source-quality 실패, 실주문 submit 실패·broker-call ambiguity·terminal order/cancel failure,
  누적 후보 결함이 확인되면 사용하지 않고 해당 세션을 차단한다.
- 장후 `machine_microstructure_attribution`은 당일 위젯 calibration, prospective
  signal research, 21:15 collector-expansion recommendation 종목 inventory를
  exact-date micro-reversion 0B/0D/event-reference 경로에 결합한다. owner
  schema/date, aware timestamp, symbol·venue·session·sequence epoch를 검증하고
  `signal -> buy-fill-confirmed -> target-fill-confirmed/exit` lifecycle을
  actual/counterfactual, realized/right-censored, context-matched/policy-eligible
  unique decision lifecycle로 분리한다. 구조 계약이 유효한 HELD-only lifecycle은
  custody/결손 진단에는 남기지만 정책 readiness 표본으로 세지 않고, 다른
  source-quality 계약 불합격은 context에서도 fail closed한다. 20:10 1차
  산출 뒤 expansion service가 같은 날짜 report를 원자 갱신하므로 늦게 추가된
  후보도 누락하지 않는다. micro symbol 또는 lifecycle anchor window가 없으면
  명시적 coverage gap으로 남긴다. 결손을 0수익으로 간주하지 않고 기존 위젯 EV와
  exact-date policy 생성도 차단하지 않는다.
  repairable gap은 다음 거래일 bounded source-only 0B/0D 수집 대상으로 되먹임하며,
  일회 수집 뒤 표본이 끊기지 않도록 현재 동적 위젯 universe도 일 4종목 공통
  한도 안에서 stable priority cohort, symbol round-robin, 독립 per-symbol venue
  phase로 회전 관찰한다. 이는 공정한 bounded rotation이지 overflow 종목의 바로
  다음 거래일 선정을 보장하지 않는다. 수동관리 제외목록은 이 수집·평가·정책
  연구 단계에 적용하지 않고 최종 실주문 owner 충돌 방지에만 사용한다. 다음 거래일
  calibration은 정확한 prior owner source date의 owner-shaped diagnostic만 읽고
  `selection_effect=false`를 유지한다. 이 연결은 diagnostic-only이며 주문이나
  위젯 policy 선택 권한이 없다. micro 조건이 위젯 policy를 실제로 바꾸려면 동일
  symbol/session 5거래일·policy-eligible unique decision lifecycle 20건, BBO
  95%·depth 90%, 비용 반영 paired rolling 5/10/20일 EV와 20일 net profit·비용
  반영 자본시간당 수익 양수, downside·HELD/right-censored 비악화가 필요하다.
  최초 bounded runtime family 연결은 별도 사용자 승인을 거쳐 exact-date
  PREOPEN으로만 열린다.
- 모든 위젯 execution policy는 장후에 일일 완료 에피소드 상한 1~5회를 같은
  종목·세션·setup·목표·cooldown 조건으로 비교한다. 1~3회는 기존 비용차감
  누적 EV/chronological holdout 순위로 선택하며, 4회 또는 5회로 자동 확대하려면
  해당 추가 회차 각각의 비용차감 증분 EV가 calibration에서 양수여야 한다.
  신규 4종목의 clean-baseline 연구 경로는 calibration 양 half와 독립 holdout에서도
  같은 증분 EV 양수 조건을 요구한다. 조건을 통과한 exact-date 정책은 별도 사용자
  승인 없이 다음 거래일 적용되며, 미표본·0 이하 증분 EV이면 최대 3회 이하 후보만
  남긴다. 이 상한은 주문 leg 수가 아니라 익절 또는 최종 청산으로 완료된 독립
  에피소드 수다.
- 미청산(right-censored) 에피소드는 손익 0으로 간주하지 않고 EV 분모에서도
  제외한다. 미청산 비율과 target completion은 별도 진단값으로 유지한다.
- replay는 source-quality `PASS`인 진입·후속 가격만 사용한다. 진입 또는 추가매수
  체결 관측이 속한 1분봉의 전체 고가는 체결 전 가격을 포함할 수 있으므로 목표
  도달 근거로 사용하지 않고, 체결 이후 현재가 또는 다음 확정봉부터 익절 도달을
  인정한다.
- 같은 스냅샷에 진입과 최종 청산이 함께 있으면 청산이 우선한다.
- KRX 매수와 NXT 매수는 최유리지정가(`trde_tp=6`)를 사용한다. 최종 매도는
  KRX 시장가(`trde_tp=3`), NXT 최유리지정가(`trde_tp=6`)를 사용한다.
- 매수 주문번호의 체결을 `kt00007`에서 확인하면 해당 entry episode에 고정된
  active execution policy의 `take_profit_bps_from_equal_share_average`를 체결
  평균가에 적용한 첫 유효 호가로 체결수량만큼 보통 지정가(`kt10001`,
  `trde_tp=0`) 익절 주문을 제출한다. 현재 두산·한화 exact-date 장후 policy
  calibration grid는 30~150bp이고 2026-08-14 Samsung exact-date 정책은 80bp다.
  내장 Samsung baseline은 50bp이며 policy loader의 방어 범위는 20~300bp다.
  policy lookup이 `None`인 compatibility 경로는 100bp
  fallback을 사용한다. 따라서 고정
  `+1.00%`가 runtime 계약은 아니다. 부분체결은 새로 확인된 미보호 수량만 추가
  주문하며, 수수료·세금은 목표가 계산에 가산하지 않는다.
- 최종 `EXIT_READY`가 익절 주문보다 먼저 발생하면 `kt10003`으로 익절 잔량을
  취소한다. 원 주문번호 조회에서 취소·부분체결 수량이 확정되기 전에는 최종
  청산 주문을 제출하지 않으며, 확정 뒤 당일 위젯 원장의 남은 수량만 판다.
- 익절 제출 결과가 불명확하면 중복 매도·초과 매도를 막기 위해 자동 재제출과
  최종 청산을 차단하고 해당 intent를 운영자 확인 대상으로 남긴다. 명시적
  주문 거절만 5초 간격, 최대 3회 재시도한다.
- 주문가능현금·예수금 조회를 선행하지 않는다. 이 실행기는 국내주식 일반주문
  `kt10000`/`kt10001`을 제출하며, 미수 허용 여부와 최종 접수는 계좌 설정과
  증권사 응답이 결정한다. 신용주문 `kt10006`으로 바꾸지 않는다.
- broker가 신규 매수를 명시적으로 거절하면 해당 episode는 custody 없이 닫고,
  기본 60초 동안 뒤이어 오는 timestamp-varying 위젯 진입 신호의 broker 재제출을
  차단한다. 거절 code/message fingerprint, cooldown 종료시각과 차단 event를 원장에
  남기며, 수량 축소나 broker 승인 추정은 하지 않는다. 운영 롤백은
  `KORSTOCKSCAN_WIDGET_ENTRY_REJECT_COOLDOWN_SEC=0`이고 양수 설정은 최대 1,800초로
  제한된다. cooldown 만료 후에도 새 source-qualified 신호와 기존 guard를 모두
  다시 통과해야 재시도한다.
- 전역 BUY 일시정지, 신호 freshness/venue 계약, 단일 실행기 lock, 수량 상한,
  미체결 중복 방지는 우회하지 않는다.
- `WIDGET_EPISODE_MARKET_WEAKNESS_ENTRY_FREEZE_OPEN_BUY_CANCEL_V2`의 당일
  `active|release_pending` market latch와 verified listing market이 일치하면 위젯
  신규진입과 추가매수를 모두 차단한다. 이미 접수된 `ENTRY_BUY` 또는
  `SCALE_IN_BUY`는 위젯 원장에 저장된 당일 원주문번호를 broker execution
  snapshot으로 다시 확인한 뒤 현재 미체결 잔량만 `kt10003` 취소한다. 부분체결
  수량은 보유·목표 주문 대상으로 유지한다. snapshot 부재·불명확, market scope
  결손, 수동·main bot·episode owner 주문과 SELL/target 주문에는 취소 권한이 없다.
  취소 응답이 불명확하면 5초 간격 최대 3회 안에서 원주문 잔량을 매번 재대사한
  뒤에만 재시도한다. rollback은
  `KORSTOCKSCAN_WIDGET_EPISODE_MARKET_WEAKNESS_ENTRY_GUARD_ENABLED=0`이다.

## 회전 수익 목적과 현재 구현 경계

체결 확인 직후 정책 지정가 익절을 제출하고 익절 완료 뒤 새 source episode를
받는 흐름은 빠른 청산·재진입의 실행 기반이다. 장후 report도 lifecycle duration,
180초 이내 목표완료, 자본점유, 비용 반영 자본시간당 수익을 노출한다. 다만
micro-reversion 연결은 이 값을 관찰·귀속할 뿐 현재 entry/exit policy를 선택하지
않는다. 위젯은 open episode가 청산될 때까지 신규 entry가 막히고 exact-date
cooldown·daily completion cap을 지킨다. 별도 lower-price episode machine은 일 1회
attempt를 소비하고 미청산을 `HELD`로 종결하며 timeout/forced-exit/re-entry 축이 없다.
따라서 “최대한 빠르고 자주 거래해 소량 순이익을 누적” 목적에 대한 현재 판정은
관찰 기반과 체결 후 즉시 TP는 구현됐지만 turnover 정책은 미구현인 `partial`이다.
향후 speed/turnover 변경은 동일 lifecycle의 비용 반영 paired EV·net profit·p10·
HELD/right-censored·capital occupancy를 함께 검증한 뒤 같은 stage 단일 bounded
family, rollback, post-apply attribution, 최초 사용자 명시 승인을 요구한다.

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

2026-08-13 11:31:37 KST에 공식
`Kiwoom-Securities/Kiwoom-REST-API` commit
`69642586f7d84ba9fd8a6faf1f1537c7fda6568b`의 `kiwoom_docs/주문.md`,
`kiwoom_docs/계좌.md`, `kiwoom/_data/kiwoom_api_spec.json`, `kiwoom/specs.py`,
Postman collection을 확인했다. 적용 API는 `kt10000`, `kt10001`, `kt10003`,
`kt00007`이며 REST 경로, 헤더, 주문 필드, KRX/NXT route와 continuation 계약을
교차검증했다.

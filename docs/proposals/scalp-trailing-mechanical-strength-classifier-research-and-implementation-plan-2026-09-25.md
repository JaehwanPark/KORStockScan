# 익절 강·약폭의 75점 경계 기계판정 전환 연구·구현안

작성: 2026-09-25 KST. 상태: **즉시 적용형 구현계획, 이번 문서 작업의 런타임·정책값 변경 없음**. 대상은 메인 실거래 `scalp_trailing_take_profit`의 강폭 0.8%·약폭 0.4% 선택뿐이다. 기계판정기 전환 구현이 검토·검증되면 첫 선택 릴리스의 실제 PID부터 바로 사용한다. 시작값, 두 폭, 손절·보호·긴급 청산, 주문·수량·provider 권한은 이 계획의 변경 대상이 아니다. 정책 시장은 `PREMARKET`, `REGULAR`, `INTEGRATED_AFTERMARKET` 세 가지로 유지한다.

이 전환은 새 익절 family나 숫자 임계치 튜닝 후보의 자동 승격이 아니라, **기존 단일 익절 owner 내부의 강약 선택 방식에 대한 사용자 지시형 교체**다. Plan Rebase의 새 family canary·장후 임계치 후보 승인 절차를 M1 최초 적용에 추가하지 않는다. 다만 시세 품질·청산 가능 시각·주문 안전·릴리스 검증은 그대로 적용하며, 이후 강약 기준 또는 익절 숫자값의 조정은 별도 근거를 요구한다.

## 1. 현재 소비 경계

- `sniper_state_handlers.py`의 fast/normal 익절 평가는 유효한 holding AI 점수 `>=SCALP_TRAILING_STRONG_AI_SCORE`(기본 75)를 강 상태로 보고 `SCALP_TRAILING_LIMIT_STRONG`을, 나머지는 `SCALP_TRAILING_LIMIT_WEAK`을 선택한다. `evaluate_trailing_take_profit`은 arm 뒤 최고가 대비 **실행 가능 bid**의 되돌림을 선택된 폭과 비교한다. arm과 peak는 시장 경계에서 유지한다.
- 같은 `_holding_strong_trailing_enabled`가 일반 보유 경로의 `dynamic_stop_pct`에도 쓰인다. 익절만 기계화하려면 **익절용 강약 상태 생산자와 손절용 기존 score 소비자를 분리**해야 한다. 익절에서는 75점 소비를 끝내고, `SCALP_TRAILING_STRONG_AI_SCORE`를 전역 삭제하거나 손절 판정을 동시에 바꾸지 않는다. 현행 AI 강약은 적격한 성과 기준선으로 취급하지 않고 적용 전후 차이를 설명하는 관측값으로만 남긴다.
- fast 감시는 약 250ms 기본 poll에서, normal 감시는 보유 루프에서 평가한다. 두 평가가 같은 포지션·평가시각·시장·원천세대의 강약 결과를 사용해야 한다. 새 기계판정은 매 poll마다 추가 REST/API 호출을 만들지 않는다.
- 현재 holding flow AI의 보류 이력은 `scalp_trailing_take_profit`에 적용되지 않는다. 향후 PASS/VETO 누적 판정은 이 연구의 강약 상태 생산자와 별도 단계다.

근거: [순수 익절 판정](../../src/engine/scalping/trailing_exit_decision.py), [fast/normal·손절 소비](../../src/engine/sniper_state_handlers.py), [시장별 4축 계약](../../src/engine/scalping/trailing_threshold_policy.py).

## 2. 문헌을 가설로 옮기는 범위

| 외부 1차 근거 | 연구 입력 가설 | 적용 제한 |
| --- | --- | --- |
| [Cont·Kukanov·Stoikov, 호가 이벤트와 order-flow imbalance](https://arxiv.org/abs/1011.6402) | 연속된 최우선 bid/ask 가격·수량 변화로 정규화 OFI **대용치**를 계산한다. 체결량만으로 호가 추가·취소를 대신하지 않는다. | NYSE 연구의 계수·시간창을 KRX/NXT 임계값으로 가져오지 않는다. 0D가 개별 주문 이벤트를 모두 전송하는지 확인 전에는 원 논문의 OFI와 동등하다고 보지 않는다. 한 장의 0D 스냅샷만으로는 계산할 수 없다. |
| [Gould·Bonart, queue imbalance와 다음 가격변화](https://arxiv.org/abs/1512.03492) | 동일 시각 최우선 bid/ask 잔량의 `(bid_qty-ask_qty)/(bid_qty+ask_qty)`와 호가단위·스프레드를 후보 특징으로 둔다. | Nasdaq의 다음 mid-price 방향 예측을 이 시스템의 비용 후 매도 우위로 간주하지 않는다. 종목별 tick regime과 호가 수량 품질을 구분한다. |
| [키움 공식 실시간 decoder](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/blob/main/kiwoom/realtime/decoders.py) | 0B 체결과 0D 호가의 별도 item·route·수신시각을 보존한다. 기존 REST `ka10004` 응답은 실제 호출된 시점의 보강 원천으로만 쓴다. | 0B 체결시각을 0D 호가시각으로 복사하거나 분봉으로 과거 호가잔량을 합성하지 않는다. 새로운 요청/parser 변경은 공식 참조 게이트를 선행한다. |

## 3. 보존 자료의 가용성과 첫 결손

2026-09-25 저장 보고서의 clean-baseline 완료·유효 수익률 표시 329건은 엄격 BUY·SELL 수량·비용 대사에서 **0건 적격**이다. 기존 중립 추정 재생의 312건(프리 45, 정규 264, 통합애프터 3)은 가격 경로 진단이며 실제 첫 crossing·호가잔량·비용 후 후보 체결이 아니다. 프리마켓 표시 45건은 현행 세션 계약상 청산 불가 시각이다.

보존 `data/ai_decision_trace/`의 44개 2026년 파일을 329개 완료 ID와 읽기 전용 대조한 결과, 140개 ID에 `holding_score` 5,589회가 연결된다. 기록된 score `>=75`는 15개 ID의 22회다. 5,589회는 독립 거래가 아니라 같은 포지션의 반복 호출이고, 22회도 **실제 강폭 사용 횟수가 아니다**. 이들 중 3,309회는 `payload_replay_exact=true`, 1,381회는 `input_source_timing`이 있다. 나머지 ID·시각의 결손은 0점이나 약한 시장 상태로 재해석하지 않는다.

9/23의 완료 projection 8건 중 정확 SELL 체결시각은 6건, 추정 익절 라벨은 7건이고 직접 `exit_signal`은 0건이다. 이 8건에 AI trace 374회가 있으나, 정확 체결시각 6건의 마지막 AI 응답은 매도보다 약 3.6~50.4초 앞선다. 마지막 응답의 보존 정확 payload는 4/6건뿐이다. 이 payload에는 `top1_depth_ratio`, `net_aggressive_delta_10t`, `buy_pressure_10t`, `quote_age_ms`, 스프레드 같은 **API 유래 파생 특징**이 있으나, 두 시점 이상의 동일 route 0D 원시잔량 변화와 후보 신호 직전·직후의 실행 가능 bid/잔량 경로는 연결되지 않는다. 해당 4건의 마지막 payload `quote_age_ms`도 약 1.05~2.04초여서 700ms 공유 WS 신선도 기본값의 대체 증거가 아니다.

따라서 현재 가능한 과거 분석은 **입력 특징 분포·품질·시간차 진단**이다. M1의 비용 후 paired 우위나 최적 시장별 값을 과거 자료로 확정할 수 없다. 이 결손은 현행 75점 AI 선택의 적격성을 증명하지도 않으므로 **기계판정기 실거래 적용을 기다리게 하는 성과 게이트로 사용하지 않는다**. 원천을 position→평가→신호→체결 ID와 시각으로 연결하는 작업은 구현 시점의 입력 검증과 적용 후 경제성 측정에 이어서 수행한다. [과거 원천 조사](../audit-reports/2026-09-25-scalp-trailing-four-axis-historical-source-availability.md), [중립 추정의 한계](../audit-reports/2026-09-25-scalp-trailing-legacy-neutral-scenario-review.md), [저장 보고서](../../data/report/monitor_snapshots/holding_exit_observation_2026-09-25.json).

## 4. 최초 기계 정책: 즉시 적용 기본값

**M1이 익절 강약 선택의 첫 실거래 owner다.** 현행 75점 선택과 항상 약폭 선택은 적용 전후 설명용으로만 보존하며 AI 결과로 M1의 결손을 메우지 않는다. 아래 수치는 실증 최적값이 아니라 원천 의미와 기존 안전조건을 우선한 최초 운영 규칙이다. 시장 세 가지 모두 같은 최초 규칙을 사용하고, 시장별 개선값은 적용 후 별도로 연구한다.

1. 강 상태의 원천 조건: 현재 평가시각의 시장·청산 가능 시각, 동일 symbol/route/transport epoch의 0B·연속 0D 시각, 기존 quote consistency의 신선·무충돌 판단, 양수 실행 가능 bid와 실제 평가·주문 경로에서 요구하는 호가 잔량을 확인한다. REST는 이미 획득·검증된 경우에만 가격 보강에 쓴다. 분류기 원천 결손은 `UNKNOWN`으로 기록하고 폭 선택에서는 약폭으로 소비한다. **분류기의 추가 특징 결손을 새로운 익절 차단 조건으로 쓰지 않는다.** 실행 가능 bid가 기존 청산 원천 계약을 통과하지 못하면 현행대로 익절 신호를 생성하지 않는다.
2. `book_support`: 누락 없는 서로 다른 두 0D에서 최우선 잔량 변화로 산출한 정규화 OFI 대용치가 `>0`이고, 현재 최우선 queue imbalance `(bid_qty-ask_qty)/(bid_qty+ask_qty)`도 `>0`인 경우. bid 기여량은 가격 상승 시 현재 잔량, 가격 동일 시 잔량 변화, 가격 하락 시 이전 잔량의 음수로 정의한다. ask 기여량은 가격 하락 시 현재 잔량, 가격 동일 시 잔량 변화, 가격 상승 시 이전 잔량의 음수로 정의하고, `OFI_proxy=(bid_contribution-ask_contribution)/max(1, previous_bid_qty+previous_ask_qty)`로 고정한다. 이것은 연속 스냅샷의 **대용치**이며 개별 주문 이벤트 OFI라는 주장은 하지 않는다. 이벤트 연속성·가격단위가 깨지면 만들지 않는다. 단일한 bid 하락 틱만으로 이미 얻은 강 상태를 해제하지 않는다.
3. `trade_support`: 평가시각 직전 **1,000ms** 동안 같은 route/epoch에서 수신된 실제 aggressor 방향 검증 0B의 순매수 체결 수량이 `>0`이고 적어도 한 체결이 있는 경우. 가격변화로 매수 체결 방향을 추측한 행은 제외한다. 1,000ms는 최초 구현용 공학적 관측창이며 수익 최적값이라는 뜻이 아니다.
4. M1은 `book_support AND trade_support`가 동시 확인된 **신호 이전** 시점에 `STRONG`을 부여한다. 한 차례의 정상적인 가격 되돌림만으로 강 상태를 즉시 약화하면 0.8% 폭이 실제로 작동할 수 없으므로, 강 상태는 원천 유효기간 안에서 유지한다. 처음 구현할 약화 조건은 **연속된 서로 다른 두 0D 호가 갱신에서 book 대용치와 queue imbalance가 음수이고, 같은 1,000ms 관측창의 검증된 0B 순체결도 매도 우위**일 때 `WEAK`이다. 이 조건은 가격 되돌림 자체가 아닌 반대 수급을 요구하며, 유지 시간·횟수는 적용 후의 관측 자료로 조정한다. 원천 만료는 `UNKNOWN`, 그 외 유효 관측은 `WEAK`이다. NXT에서 0B가 낡고 0D만 유효한 경우에도 강 상태를 합성하지 않는다.

M1 외에 `queue_only`, `OFI_only`, `trade_only`를 사전 명세한 소수 대안으로 **장후 비교**한다. 강 상태가 실제로 너무 드물면 적용 후 동일 분모에서 노출률·미청산 상승·악화 손실을 보고 후속 변경을 검토한다. 기존 AI 점수, 모델 이유, 체결 **후** 가격과 미래 고점은 판정 입력에서 제외한다.

## 5. 실행 빈도와 최종 소비

- **계산은 이벤트 기반으로 최대한 자주**: 보유 중 수신한 서로 다른 신뢰 가능 0B/0D 세대마다 WS 수신부는 O(1)로 큐에 등록하고, 단일 fast 평가자가 이벤트당 O(1)로 분류기 상태를 갱신한다. R0에서 기존 WS 구독과 저장 경로가 실제로 어떤 이벤트를 관측·보존하는지 먼저 확인한다. 최신 스냅샷만 남는다면 그 자료로 OFI 대용치를 소급하지 않고, 기존 구독의 수동 관측 지점에 순번·원천시각·핵심 필드의 bounded journal을 추가한다. 필요한 구독이 없다면 결손으로 보고하고 구독을 자동 확대하지 않는다. 누락·용량 초과는 위치와 사유를 기록한다. 별도 REST polling, 모델 호출, 주문 호출은 없다.
- **최종 신호는 단일 fast 평가자가 순서대로 소비**: WS 수신부는 주문을 내지 않고 이벤트를 bounded queue에 넣어 fast 평가자를 깨운다. fast 평가자는 누적 0B/0D를 event-time 순서로 소진하면서 각 0D의 bid·peak·그 직전 강약 상태로 trailing을 평가하고 첫 crossing을 latch한다. 0B만 온 경우에는 강약을 갱신하되 새 가격 crossing을 만들지 않는다. 250ms poll은 알림 누락과 원천 만료의 안전망이다. 이벤트가 많으면 알림만 병합하고 이벤트는 건너뛰지 않는다. queue overflow·시각 역전은 `source_gap`으로 기록하고 최신 유효 bid의 현행 TP 평가를 수행하되 과거 첫 crossing을 복원했다고 주장하지 않는다. normal 경로는 같은 판정 함수·position별 상태와 이미 latch된 신호를 소비하며, fast/normal 중복 주문은 기존 주문 소유권으로 막는다.
- strong 승격에는 두 시점 이상의 동일 route 호가 및 새 0B 지지가 필요하다. 약화는 일회성 되돌림이 아닌 지속된 반대 증거로 결정하고, 원천 만료는 `UNKNOWN`으로 처리한다. 판정과 trailing 평가가 동일한 event-time snapshot을 쓰고 첫 crossing 당시의 상태·선택 폭을 고정해야 한다. 약폭 crossing이 이미 확인되면 뒤늦은 strong 승격으로 그 청산 후보를 취소하지 않는다. 시장·route 전환 또는 프로세스 재시작 시 분류기 상태는 `UNKNOWN`부터 다시 쌓되 기존 arm/peak를 잃지 않는다.
- 신호 로그에는 `classifier_version`, position ID, 평가시장·시각, 0B/0D/REST item·route·수신시각·hash, `book_support`, `trade_support`, `STRONG|WEAK|UNKNOWN`, 선택 폭과 첫 crossing, 경쟁 청산 우선순위를 기록한다. fast와 normal이 같은 원천세대에 다른 결과를 낼 수 없도록 공통 상태를 사용한다. 불일치가 감지되면 강폭 선택을 차단하고 약폭으로 기록하되, 기존 유효 호가를 통한 익절 자체를 새 분류기 오류만으로 막지 않는다.
- `SCALP_TRAILING_STRONG_AI_SCORE`는 익절의 선택 owner에서만 분리한다. soft-stop 및 다른 holding score 소비자는 현행대로 둔다. M1은 구현 검토와 입력·소비 계약 검증을 통과한 **첫 선택 릴리스의 fast/normal 및 runtime/bootstrap에 함께 연결**한다. 별도 경제성 holdout, 그림자 운영일, 시장별 순차 canary를 적용 전 조건으로 두지 않는다. 기존 보유 포지션도 새 PID의 첫 유효 평가부터 M1을 소비하며 arm/peak는 유지한다. 재시작 직후 누적 0B·0D가 없으면 `UNKNOWN`→약폭이 적용되어 기존 보유분에 익절 신호가 즉시 발생할 수 있으므로 이 전환 영향을 신호 영수증에 명시한다. 프리마켓은 현행 `exit_allowed_by_clock=false`이므로 강약 상태를 계산하더라도 청산 신호는 허용하지 않는다.
- TP 시장별 정책·장후 생산자의 선택 축은 `START_PCT`, `LIMIT_WEAK`, `LIMIT_STRONG`과 `mechanical_strength_v1` 분류기 버전으로 바꾼다. 기존 75점 score 축을 TP 후보·bootstrap 소비·적용 영수증에서 제거하거나 진단 필드로 명시해, 폐기된 점수 후보가 나중에 TP 강약을 다시 바꾸지 못하게 한다. soft-stop에 남는 75점 키는 별도 소비 계약으로 계속 대사한다.

## 6. 구현·즉시 적용·사후 연구 순서

| 단계 | 기존 소유 경로에서 할 일 | 전환·종료 근거 |
| --- | --- | --- |
| R0 입력 계약 | 기존 보유 WS가 전달하는 0B·0D의 route/epoch/시각·호가잔량·체결방향 의미를 확인한다. 신뢰 가능한 aggressor 부호가 없다면 임의 추정하지 않고 `UNKNOWN`→약폭으로 둔다. 0D가 스냅샷만 보존되면 기존 구독 관측 지점에 bounded event journal을 연결한다. API 요청/parser를 바꿔야 한다면 키움 공식 참조 게이트를 선행한다. 과거 329건과 exact payload는 결손·설계 진단으로 함께 대사한다 | 동일 시점 0B·0D의 출처, 누락/중복/역전 식별, 실행 가능 bid·잔량과 source-quality 입력이 코드 수준에서 확정된다. 과거 비용 후 paired 분모는 전환 조건이 아니다 |
| R1 판정·소비 구현 | `src/engine/scalping/`의 순수 상태기계에 M1 기본 규칙과 `UNKNOWN` 이유를 구현한다. fast/normal TP에서만 75점 소비를 M1으로 치환하고 soft-stop/다른 AI 소비는 보존한다. 첫 crossing latch, 포지션별 arm/peak, 재시작·route/시장 전환, 기존 보유분을 다룬다. 네 값의 정책 스키마에서는 점수를 TP 후보·소비에서 분리하고 다른 owner의 잔존 참조를 대사한다 | 같은 event-time snapshot은 fast/normal에서 같은 강약·폭·신호를 만든다. 75점 AI는 어떤 TP 경로에서도 선택권이 없고, 결손 시 AI로 복귀하지 않는다 |
| R2 장후 이관·적용 전 검토 | §7의 장후 재생·readiness·sentinel/summary와 bootstrap 스키마를 **같은 릴리스에 구현**한다. 기능·회귀·고빈도 성능과 주문 안전 계약을 검토→수리→재검토한다. 신선/낡음·경로 혼합·중복·큐 초과·이벤트 깨움·재시작·기존 포지션·첫 crossing·강폭 유지·약화·프리마켓 청산금지 및 다른 청산 우선순위를 검증한다. 계산 p50/p99, fast loop 지연, CPU/RSS, lock 경합과 추가 API 요청 수를 측정한다 | 새 장후 입력·빈 표본·구세대 자료에서도 보고/summary/bootstrap가 명시적 상태로 끝난다. 원천 결손이 명시되고 기존 hard/protect/emergency·broker/account/order/quantity/cooldown·시세 신선도 제한이 유지되며, 이벤트당 증분 계산으로 fast 감시가 악화되지 않는다. **경제성 우위나 자연 완료 표본은 이 단계의 통과 조건이 아니다** |
| R3 즉시 전환 | 검토가 닫힌 코드와 M1 정책 버전/hash를 한 선택 릴리스로 묶어 runtime/bootstrap·PREOPEN·fast/normal을 동일 세대로 전환한다. 선택/설치/실제 PID 소비와 원복 영수증을 분리한다. 첫 유효 평가부터 신규·기존 보유 포지션에 M1을 사용한다 | 전환 직후 PID의 TP 로그에 M1 버전·원천세대·강약·선택 폭·첫 crossing이 기록된다. 별도 그림자 운영일·paired EV·시장별 순차 canary를 기다리지 않는다. 프리마켓은 현행 청산금지 계약을 유지한다 |
| R4 개편된 장후 실행·사후 경제성 | R2에서 바꾼 장후 경로로 자연 완료 포지션의 BUY→모든 SELL/잔량0→DB `COMPLETED`·유효 수익률→체결 기반 비용 공통 분모를 대사한다. 세 시장별 직접 TP/경쟁 청산/검열과 신호 전후 0B·0D·실제 REST 호출을 연결한다. 상세 계약은 §7이다 | 비용 후 paired EV·순이익, 승률, 큰 손실, 놓친 상승과 `UNKNOWN` 비율을 동일 ID·시장·릴리스별로 보고한다. 현행 AI가 적격 기준선이었다는 주장이나 이전 M1 수익성 보증에는 쓰지 않는다 |
| R5 후속 조정 | 적용 후 충분한 직접 원천에서 강 상태 노출률과 약화 조건을 시장별로 조정한다. `queue_only`·`OFI_only`·`trade_only` 대안은 동일 분모·독립 최신 구간으로 검토한다. 심각한 원천/오판/청산 지연은 기존 운영 안전 절차의 중지·원복 대상으로 기록한다 | 후속 정책 변경만 별도 비용 후 근거와 정책/hash/PID 수용을 요구한다. M1 원천 결손만으로 75점 AI 판정에 자동 복귀하지 않는다 |

## 7. 장후 튜닝 생산자·소비자 변경 계약

**최초 M1 실거래 교체와 이후 최적화의 권한을 분리한다.** 장후 코드·bootstrap 소비자 변경은 런타임과 같은 릴리스에 넣고 R2에서 기능·빈 표본·구세대 호환을 검증한다. 최초 교체는 사용자 지시와 R0~R2의 구현·안전 검증을 근거로 즉시 적용한다. 자연 장후 계산 결과를 기다리지 않는다. 최초 적용 뒤에만 자연 M1 경로의 경제성을 측정하고, 두 번째 이후의 숫자 임계치·분류기 규칙 변경을 장후 후보·선택 절차로 다룬다.

| 현재 생산·소비 경로 | 변경 계획 | 결손·권한 처리 |
| --- | --- | --- |
| `trailing_threshold_policy.py`의 `THRESHOLD_KEYS` 4개, 12개 시장 env, `scalp_trailing_four_axis_selected_policy_v1` | 익절 정책은 시장별 시작·약폭·강폭 **9개 값**과 별도 `mechanical_strength_v1` 규칙 버전·파라미터 hash로 버전 업한다. soft-stop의 75점 설정은 익절 정책 밖에서 보존한다 | 구 4축 선택 영수증을 새 TP 소비자가 조용히 수용하지 않는다. 정책 스키마·시장·classifier hash 불일치는 명시적으로 거부하고, 최초 M1 기준선 영수증은 경제성 후보 승인 영수증과 구분한다 |
| `trailing_four_axis_replay.py`의 `score_grid`, AI 점수 경계별 `_signal`, score×폭 조합 | 현행 75점 단일축·score×폭 조합을 **익절 후보 계산에서 제거**한다. `START_PCT`, `LIMIT_WEAK`, `LIMIT_STRONG`을 M1의 시점별 강약 상태와 함께 다시 재생한다. 분류기 후보는 queue cutoff, 정규화 OFI 대용치 cutoff, 검증된 순체결 cutoff, 반대 증거 지속 횟수만 소수의 봉인 격자로 비교한다 | AI 점수/TTL은 신·구 관측 비교용 필드다. 구 score replay와 신 M1 replay를 같은 policy 세대로 합치지 않는다. 단일 스냅샷에서 과거 M1 강약 경로를 추정하지 않는다 |
| `trailing_start_replay.py`와 후보별 first crossing·수익 계산 | 시작값 재생도 점수 유효성으로 강약을 선택하지 않고 동일 M1 이벤트 상태를 소비한다. 후보별 arm·peak·강약·폭·첫 crossing·경쟁 청산을 독립적으로 재생한다. 기존 포지션의 진입시각과 청산시각 사이 정책 세대가 바뀌면 전이별 세대를 기록한다 | 과거 AI 세대의 완료 건은 공통 완료 census와 과거 진단에 남기되 **순수 M1 적용 효과** 분모에 섞지 않는다. 전환 시점 보유분은 `mixed_policy_generation`으로 분리한다 |
| `holding_exit_observation_report.py`의 `trailing_threshold_readiness`와 `trailing_four_axis_market_tuning` | score 적격 ID/`effective_input_ids`의 점수 필수 조건을 TP readiness에서 제거한다. 대신 직접 classifier 이벤트·`STRONG/WEAK/UNKNOWN`·source gap·실제 선택폭·첫 신호·완료/비용 ID를 분리한다. 세 수익축과 분류기 민감도 연구에 새 schema/필드를 주고 구 4축 필드는 명시적 구세대 진단으로 격리한다 | 직접 신호가 없는 추정 익절 라벨, 추정 체결시각, `UNKNOWN`을 강 상태로 채우지 않는다. 구 필드 빈값을 신 연구 PASS로 읽지 못하게 한다 |
| `holding_exit_sentinel.py` → `runtime_approval_summary.py` → `sniper_performance_tuning_report.py` 및 빈 snapshot schema | 새 보고서의 strict 완료 census, 시장별 노출·미식별, classifier version/hash·실제 PID 세대, 세 수익축/분류기 후보, source-gap, 적용 전후 성과를 끝까지 전달한다. 구 `four_axis_status`는 `legacy_ai_policy`로 표시하거나 새 schema에서 제거한다 | 소스 파일이나 schema가 없으면 `source_gap_report_missing`으로 공개한다. 장후 계산 성공, M1 배포, 실제 PID 소비, 자연 비용 후 성과를 각각 다른 필드로 표시한다 |
| `runtime_policy_bootstrap.py`의 `scalp_trailing_four_axis_selector` 12키 검증과 `selected_policy_env`의 양수 holdout 요구 | 최초 M1 적용에는 **사용자 지시형 기준선 교체 영수증**을 사용해 classifier version/hash·9개 현행값·rollback을 검증한다. 이 경로에서 4축 양수 holdout 조건을 요구하지 않는다. 후속 튜닝 후보에는 세 값과 classifier 파라미터를 하나의 정책 hash로 묶고 기존 원천·검증·same-stage·rollback 선택 조건을 적용한다 | 구 12키·75점 후보가 신 TP 정책에 다시 적용되지 않게 한다. baseline 교체 영수증은 향후 값 변경권이나 손절 점수 변경권을 주지 않는다 |

**계산 순서:** 세 시장에서 M1 기본값과 같은 포지션 경로를 기준으로 세 수익축을 각각 바꾼 단일축 민감도를 계산한다. 다음에 `시작×약폭`, `시작×강폭`, `약폭×강폭`과 **분류기 기준×각 폭**의 상호작용을 소수 후보로 확인한다. 강 상태 노출이 없는 시장·기간에서는 강폭과 그 상호작용을 `unidentified_no_strong_exposure`로 두고, 약폭·시작값까지 불필요하게 차단하지 않는다. 훈련 날짜에서 격자와 후보를 봉인하고 최신 독립 날짜에는 재선택하지 않는다. 프리마켓은 현행 청산금지 시각을 별도 `no_live_exit_exposure`로 기록하며 정규장이나 통합애프터마켓 성과로 대체하지 않는다.

**공통 모수와 실행모형:** 정책 튜닝의 모수는 clean baseline 이후 실제 BUY 체결 수량, 전 SELL 체결과 잔량 0, DB `COMPLETED`·유효 수익률, 체결 기반 비용을 모두 충족한 포지션 전체다. 다른 청산으로 끝난 건도 경쟁 청산으로 포함하고, 열린 포지션은 별도 검열한다. 후보가 실제보다 먼저 팔면 그 시각의 실행 가능 bid·잔량과 비용/슬리피지로 모델 손익을 계산한다. 후보가 늦으면 실제 SELL 이후의 호가·안전 청산 경로가 증명될 때만 손익을 계산한다. 증명되지 않으면 `censored_after_actual_exit`이며 0효과로 채우지 않는다. 정책 세대별 공통 지원 ID, 제외·검열 ID와 비용 후 paired EV·순이익·큰 손실을 공개한다. 반복 0B/0D 이벤트나 AI 호출 수를 독립 거래 건수로 세지 않는다.

**실행 성능:** 기존 4축 재생의 후보·원천 읽기 비용을 기준으로 신규 3축/분류기 단일·제한 복합 계산의 wall/CPU/RSS/swap, 후보 수·이벤트 수·적격/제외/검열 수를 같은 입력에서 측정한다. position별 특징과 first crossing을 선계산해 조합마다 대용량 원천을 재독하지 않는다. 실제 장후 `trade_review → post_sell_feedback → holding_exit_observation → sentinel/summary` 시간창과 최대 보존일을 측정하고, 결과·공통 ID·source hash가 단순 참조 재생과 같아야 한다. 성능 때문에 품질 좋은 행이나 불리한 후보를 버리지 않는다.

과거 비용 후 paired 분모가 계속 0이어도 **R0~R2의 코드·입력·안전 검증이 닫히면 R3에서 M1을 바로 실거래 소비에 연결한다**. 과거 보존 payload의 특징값을 새 실거래 첫 신호 원천으로 소급하지 않는다. 이후 정책 효과의 주 지표는 전체 적격 완료 포지션의 비용 후 paired EV·순이익이며, 승률은 진단 지표다. 이 문서 변경 자체는 배포 또는 실주문 실행 영수증이 아니다.

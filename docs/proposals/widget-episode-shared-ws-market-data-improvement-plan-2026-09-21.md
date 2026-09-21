# 위젯·에피소드 공통 WS 시세 수집 개선안

- 상태: **사용자 구현·리뷰·커밋푸시·배포기동 승인 후 P0/P1 첫 인계 구현**. 기존 문서 작성 단계의 실행 금지는 과거 범위이며 이번 명시 승인을 대체하지 않는다. P1은 비교 전용이고 P2 전환/확대는 P5 자연 검증 후다. [코드·검증·배포 기록](../audit-reports/2026-09-21-widget-shared-ws-transport-review.md). 앞선 수리 완료를 WS 전환 완료로 확대하지 않는다.
- 최신 인계: `6c1bfa172` 기본3종목 collector 배포·13:51 재기동·실제_AL 소비 확인. P1 인정 규칙 수리의 코드/배포/PID 검증 완료, P2 실제 입력 전환·확대와 P3 분봉은 미완료다. 다음 완전한 자연3창은14:00–14:45이며14:45 이후 판정한다. [현재 배포와 후속 의존성](../audit-reports/2026-09-21-widget-shared-ws-transport-review.md#integrated-source-deployment-and-continuation).
- 결정: 현재가·체결·호가를 기존 WS 수신기에서 공유하고 REST는 초기 이력·정적 정보·제한된 누락 복구에 사용한다. **P2 시세 전환에 더해 P2E 주문 직전 시장자료 검사 연결을 추가**한다. P3 완료 분봉 공유와 별도로 진행하며, 관측198종목 확대나 P3 완료를 기다려 제출 병목 수리를 미루지 않는다.
- 이번 보완 범위: 9/21 미제출9건을 근거로 P2E와 삼성 오전기 `WAIT` 조기 종결 수리를 계획에 반영한다. 문서 보완 자체는 코드 구현·배포·자연 검증 완료가 아니며, 기존 사용자 승인과 P4/P5 검증 경계는 유지한다.
- 사용자 정정 반영: 모든 종목에서 같은 종목의 유효한 `_AL` 체결·호가 수신을 WS 전환의 원천 검증에 인정한다. `005930` 별도 등록 부재나 KRX REST와의 값 차이만으로 `005930_AL`을 탈락시키지 않는다. [공통 reader 보완·실제 자료 확인](../audit-reports/2026-09-21-widget-shared-ws-transport-review.md#integrated-symbol-source-acceptance-correction).
- 현재 실행·자연 acceptance owner: [9/21 checklist](../checklists/2026-09-21-stage2-todo-checklist.md)의 `KiwoomCommonHealthOpportunityCostAcceptance0917`. 이 문서는 단계별 설계이며 별도 OPEN owner를 중복 생성하지 않는다.
- 상위 계약: [Plan Rebase §1–§8](../plan-korStockScanPerformanceOptimization.rebase.md), [Kiwoom API 공식 참조 gate](../kiwoom-api-data-contract.md#official-kiwoom-reference-gate). [기존 위젯 source/consumer 성능 계획](widget-postclose-performance-and-source-closure-implementation-plan-2026-09-16.md)의 원천 역할·중복 제거 원칙을 이어가며 완료된 장후 계산 개선을 다시 수행하지 않는다.

## 1. 확정된 문제와 범위

[10:30:17 KST 점검 사본](../../tmp/widget-episode-runtime-review-20260921.json)의 상태다. 아래 숫자는 해당 시각의 최신 저장 관측이며 하루 전체 실패율이나 구현 이후 결과가 아니다.

| 영역 | 관측 | 해석 |
| --- | --- | --- |
| 기본 위젯 3종목 | 삼성·두산·한화 프로세스 가동, 최신 입력 `DATA_WAIT` | `shared_read_rate_wait_budget_exhausted`로 시세 확보 지연; 시각에 따라 정상 입력과 대기가 반복됨 |
| 확장 위젯 | 58종목 중 `ok` 4, `data_wait` 54 | 대기 사유 52개는 `request_budget_deferred`, 나머지는 분봉 stale·source error |
| 연구감시 | 당일 저장 관측 198개 중 PASS63, SOURCE_ERROR125, SOURCE_QUALITY_BLOCKED10; 5분 내 갱신23개 | SOURCE_ERROR125개의 사유는 공통 읽기 예산 대기. 프로세스 가동만으로 관측 coverage를 보장하지 못함 |
| 저가주 에피소드 | 4개 분봉 평가 중, 24개 NO_TRADE, 당일 주문0 | 기존 분봉 평가 경로는 동작. 모든 미진입을 데이터 장애로 분류하지 않음 |
| 위젯 매매/보유 | 삼성1종목 정책 허용, 신규 주문0, 삼성 이월25 | 수집 개선이 정책·보유 owner·청산 권한을 변경하지 않음 |
| 오류 탐지 | process/artifact 등 전체 pass | 프로세스 생존과 실제 유효 입력 coverage가 다른 문제임 |

현재 `widget_symbol_runtime_collector`는 현재가 `ka10001`·호가 `ka10004`를 각각 30초 bucket으로, 분봉 `ka10080`을 1분 bucket으로 조회한다. `widget_research_watch_collector`는 일부 quote/BBO를 재사용하지만 미충족 시 REST로 조회하고 분봉도 요청한다. 저가주 gateway도 종목별 `_AL` 완료 분봉을 REST로 읽는다.

58종목 모두에 현재가2회+호가2회+분봉1회/분을 요구하면 **290회/분**이다. 이는 실제 요청 횟수가 아닌 캐시 주기 기반 수요 계산이며, 재사용·local pacing·미시도는 별도로 계수한다. 현행 공통 read admission의 `source_only` 상한은 코드상 초당4회, 전체 read는 초당5회이고 연구감시 local budget은 분당18회다. 이 값은 **현재 로컬 안전 설정**이며 공식 WS 한도나 변경 제안이 아니다. 58과198은 중첩하므로 구독 수를 단순 합산하지 않는다.

### 1.1 주문 직전 병목의 추가 증거

[14:18 읽기 전용 대사](../../tmp/widget-episode-nine-block-causal-check-20260921.json)는 14:06 집계의 `SOURCE_UNAVAILABLE`5건·`SKIP_DEADLINE`4건을 대상으로 한다. 분할 leg와 재시도가 포함된 미제출9건이며, 9종목/독립 기회9개 또는 당일 최종 분모가 아니다. 모두 broker 주문번호가 없고, 직접 거절 사유는 매도 압력 검출이 아니다.

| 대상 | 확인된 사실 | 후속 수리/미확정 경계 |
| --- | --- | --- |
| 삼성 오전 | 최초 검증 통과 뒤 원천 부족1·시한 초과1. 첫 leg는 guard가 `WAIT`인데 상위 machine이 `NO_FILL`로 종결 | 비종결 대기 상태를 유지하는 §3.5 수리. 과거 신호 재실행 금지 |
| 삼성E&A 늦은 오전 | 최초 통과 뒤 제출 직전 호가·체결 자료 노후화로 원천 부족2 | stale 차단 유지. 실제 무체결과 수집/발행 지연은 당시 증거만으로 모두 구분되지 않음 |
| 삼성E&A 점심 | t0+5초 검증 통과 후 REST 호가·체결 조회 완료가 각각 +7.014초/+7.491초, 두 leg 시한 초과 | §3.4에서 6.5초 예산 안의 WS 소비 연결·순차 조회 제거 검증 |
| 한국전력 점심 | 원천 부족2 후 한 leg 재시도 통과. REST 완료 +7.073초/+7.768초로 시한 초과1 | §3.4 적용. API 예산 대기·응답·로컬 처리·leg 순차 지연을 분리 |

현재 경로는 WS adverse-flow 검증 뒤 `ka10004` 유동성과 `ka10003` 체결속도를 순차 조회한다. 따라서 P2 수집기 REST 절감은 간접 개선이고, P2E가 주문 직전 병목의 직접 수리다. 6.5초 전체를 API rate-limit 대기라고 단정하지 않는다. 당시 release의 guard/owner/regular machine/gateway와 작업본의 해당 파일 해시 일치를 확인했으며, 구현 시 실제 선택 release를 다시 확인한다.

## 2. 재사용할 구성과 소유 경계

| 기존 코드 | 계획된 역할 |
| --- | --- |
| [kiwoom_websocket.py](../../src/engine/kiwoom_websocket.py) | 기존 0B/0D 수신·정규화·route 상태·연결 세대·구독 관리 재사용. 수신 callback에서 REST/큰 파일 쓰기를 실행하지 않음 |
| [기존 WS snapshot writer](../../src/engine/bd_fbuy_accum_pre_scanner.py) `write_ws_snapshot` | 기존 비동기 atomic checkpoint를 우선 재사용. 파일 이름이 속한 과거 외국인집계 전략을 재활성화하지 않음 |
| [market_data_cache.py](../../src/trading/market/market_data_cache.py), [quote_consistency.py](../../src/trading/market/quote_consistency.py) | 시세 저장·신선도·정확한 route 선택 검증. 현재 메모리 cache를 프로세스 간 공유 완료로 간주하지 않음 |
| [samsung_widget_advisory.py](../../src/engine/monitoring/samsung_widget_advisory.py)의 read client 및 삼성·두산·한화 advisory owner | 필드별 WS 우선 읽기와 제한된 REST 보충. 기존 출력 schema·신호 kernel 유지 |
| [widget_symbol_runtime_collector.py](../../src/engine/monitoring/widget_symbol_runtime_collector.py), [widget_research_watch_collector.py](../../src/engine/monitoring/widget_research_watch_collector.py) | 같은 symbol/route/session 시세를 재사용; 관측·실행 catalog를 분리하고 원천/소비 census 보존 |
| [kiwoom_read_request_control.py](../../src/utils/kiwoom_read_request_control.py) | 기존 예산·우선순위·cooldown 유지. 필요 시 시장자료에만 중복 복구 요청 합류 기능 보완 |
| [low_price_two_leg/gateway.py](../../src/trading/low_price_two_leg/gateway.py), [widget gateway](../../src/trading/widget_auto_trade/gateway.py) 및 기존 삼성 episode gateway | P2E에서 주문 직전 유동성·체결속도의 WS 입력 adapter 연결. P3에서 동일 route 완료 분봉 재사용. 주문 transport·계좌/잔고/미체결 대사 권한은 기존 owner 유지 |
| [entry_liquidity_guard.py](../../src/trading/order/entry_liquidity_guard.py), [entry_adverse_guard.py](../../src/trading/order/entry_adverse_guard.py), [entry_adverse_owners.py](../../src/trading/order/entry_adverse_owners.py) | 기존 검사·원 시각·최종 제출 검증 재사용. REST 전용 provenance와 WS provenance를 명시적으로 구분하고 자료·시간·수량 기준은 보존 |
| [삼성 오전 machine](../../src/trading/samsung_morning_one_share/machine.py), [regular_two_leg_machine.py](../../src/trading/order/regular_two_leg_machine.py) | 동일 identity의 `WAIT` 재검증과 terminal 상태를 정합화. registry 거절/새 예약, crash 복구와 중복 전송 방지 유지 |
| 기존 `process_health`·`artifact_freshness` detector | 프로세스 생존과 consumer별 데이터 신선도·coverage를 별도 판정. 별 daemon/스케줄러를 추가하지 않음 |

`data/runtime/kiwoom_ws_snapshot/latest.json`에는 이미 `machine_entry_confirmation_ws_snapshot_v1` 입력 계약과 route별 자료가 있다. 삼성 화면의 가격 비교 reader는 별도 `widget_ws_price_comparison_only` 용도다. 화면용 값이나 micro-reversion 구독 영수증을 위젯 매매용 검증으로 전용하지 않는다. 기존 snapshot의 필요한 필드/계약이 충족되면 그대로 읽고, 부족한 항목만 호환 가능한 section으로 보완한다. 최신 시세 checkpoint와 연속 체결 원장은 별개다.

새 collector daemon·DB·CLI·독립 정책 엔진은 기본안에 없다. 공통 reader가 기존 파일에 맞지 않을 때만 `src/trading/market` 아래 최소 모듈의 필요성과 테스트 위치를 구현 gate에서 기록한다. `src/engine` root에는 새 모듈을 만들지 않는다.

## 3. 목표 데이터 흐름과 필수 계약

```mermaid
flowchart LR
    WS[기존 WS 수신기] --> Q[route별 검증된 시세 checkpoint]
    Q --> W[기본·확장 위젯]
    Q --> R[연구감시]
    REST[기존 예산 내 REST 초기·복구 조회] --> B[검증된 완료 분봉 저장]
    WS --> T[연속성 검증을 통과한 체결 집계]
    T --> B
    B --> W
    B --> R
    B --> E[기존 에피소드 분봉 reader]
    Q --> G[P2E 기존 주문 직전 시장자료 검사]
    T --> G
    REST --> F[남은 시간 내 제한된 시장자료 복구]
    F --> G
    G --> O[기존 계좌·주문 안전검사와 제출 owner]
```

### 3.1 같은 값으로 대체할 수 있는 필드만 전환

- P0에서 각 consumer가 실제 사용하는 `ka10001/ka10003/ka10004/ka10080` 필드를 목록화하고 공식 WS FID와 단위·부호·시각·route를 대조한다. 현재가가 같다는 이유로 기본정보 전체를 WS로 대체하지 않는다. WS에 없는 정적 필드는 REST 저빈도 cache로 유지한다.
- key는 최소 `(trade_date, symbol, item/request_code, market_data_route, session, realtime_type)`이다. KRX·NXT·통합 `_AL` 값을 섞지 않고 통합 관측으로 실제 체결 거래소를 추정하지 않는다.
- 위젯 전환 원천은 동일 종목 `_AL`이 등록되어 있으면 통합 원천을 선택하고, 없으면 기존 요청 item을 검사한다. `request_code`와 `ws_request_code`를 따로 보존하고 선택한 원천 내부의0B/0D item·route·epoch 일치는 필수다. 통합 원천이 미완성/stale이면 결손을 기록하며 다른 원천으로 숨기지 않는다. KRX/NXT REST와 통합 WS는 `different_market_data_scope`로 기록하고 WS 유효 수신에 포함한다. 거래장소가 다른 값의 완전 일치는 전환 조건이 아니며, 실제 주문장소별 유동성 검사나 완료 분봉 계약을 이 규칙으로 바꾸지 않는다.
- 가격·최우선호가·잔량·체결마다 원 수신시각, 제공된 거래시각과 정밀도, 연결 epoch, source hash/참조, producer PID/commit, consumer 선택/거부 사유를 남긴다. snapshot 생성·읽기시각을 가격 수신시각으로 바꾸지 않는다.
- `0B`의 가격 갱신을 `0D` 잔량 갱신으로 취급하지 않는다. 같은 route여도 각 필드의 신선도와 허용 시각 차이를 기존 consumer 계약으로 검사한다. 오래된 값 혼합, 미래 시각, bid/ask 충돌은 차단한다.
- 재접속·거래일/세션 전환 시 이전 세대 cache를 무효화한다. REG 수신 응답, 요청 scope와 실제 데이터 첫 수신을 구분한다. 로컬 sequence는 내부 유실 탐지용이며 broker가 제공하지 않은 무손실 sequence 증거를 합성하지 않는다.
- 체결이 없는 시간과 연결 단절을 구별한다. quiet tape를 freshness 면제로 사용하지 않으며 무거래 분봉 생성은 기존 공식/로컬 bar 계약으로 증명되는 경우에만 허용한다.

### 3.2 구독과 프로세스 간 공유

- 기존 WS owner가 consumer별 필요 item/type을 합쳐 구독한다. 같은 symbol이라도 route/type이 다르면 별 항목이고, 동일 item/type은 중복 등록하지 않는다. consumer가 끝날 때 다른 owner가 쓰는 구독을 REMOVE하지 않는다.
- 기존 메인·보유/청산 구독을 보호하고, 당일 실행 가능 위젯/도래 episode와 관측 전용 catalog를 구분한다. 관측198개를 넣기 위해 메인 감시를 축소하지 않는다.
- 실제 등록 한도·연결 정책·처리 용량은 P0에서 공식 근거와 설치 설정을 확인한다. 전 종목 수용 가능을 가정하지 않는다. 미수용 scope는 `capacity_deferred` 등 명시적 이유·기대 cadence를 남기고 관측 분모에서 삭제하지 않는다.
- checkpoint는 단일 writer가 일관된 세대를 atomic publish하고 다중 reader가 읽는다. receiver lock 보유시간·serialization·파일 크기를 계측하며, consumer별 실패가 WS 수신을 막지 않게 한다. 기존 약1초 snapshot 발행은 모든 주문 검사에 충분하다고 가정하지 않는다.
- WS 의존성이 생긴 consumer에는 producer 재시작/정지 감지와 fail-closed 동작을 명시한다. 메인 WS가 없을 때 각 consumer가 새 연결·토큰 갱신을 무제한 시작하지 않는다.

### 3.3 REST 복구와 분봉

- WS 데이터가 consumer 계약을 충족하면 해당 시세 REST 요청을 생략한다. 누락/미구독/불완전은 기존 read budget 내 단일 복구 요청으로 제한한다. 시장자료만 exact scope로 합류시키며 계좌·주문 호출에는 적용하지 않는다.
- 현재 single-flight는 프로세스 내부 thread 단위다. 여러 service의 동시 복구를 막는 공유 조정이 필요한지 검증하고, 기존 budget/state lock을 우선 재사용한다. 198개 reader의 동시 timeout이 REST 폭주를 만들면 rollout을 중단한다.
- 분봉 초기 lookback은 기존 `ka10080` 경로로 적재한다. P1/P2에서는 분봉 출처를 그대로 유지하므로 분봉/API 병목까지 해소됐다고 판정하지 않는다.
- P3에서 실제 연속 체결 원천이 보존된 구간만 완료 분봉을 집계한다. 최신 checkpoint의 제한된 체결 tail만으로 전체 분봉을 복원하지 않는다. epoch 경계, 수신 유실, 중복/역순, late tick, 수정주가, 거래량 단위, 무거래 구간, 세션 경계를 검증한다.
- WS 집계와 REST 공식 완료 분봉이 불일치하면 해당 구간을 격리하고 bounded REST로 복구한다. 과거 분봉 복구가 당시 BBO·판정시각·체결 가능성을 복구한 것은 아니다. consumer가 받아들인 bar revision/hash와 수신 가능시각을 보존하여 hindsight를 차단한다.

### 3.4 P2E — 주문 직전 시장자료 검사의 WS 우선 소비

목표는 검증된 WS 자료가 있는데도 주문 직전 REST를 다시 기다리는 경로를 제거하는 것이다. 기존 전략·guard evaluator를 재사용하고, source adapter와 시간 예산 연결만 수리한다. 적용표는 위젯·삼성 오전/점심/오후·저가주 episode의 실제 consumer별로 작성하며 OFF/제외 profile을 활성화하지 않는다.

1. **필드 동등성:** 유동성은 동일 item/route의 0D 최우선 양방향 가격·잔량, 체결속도는 0B 최근10개 체결의 시각·수량·합산 거래량을 검증한다. 기존 잔량/요청수량 배수·최소 거래량, 호가 age2초·최신 체결 age5초·10개 체결 span20초, 별도 adverse-flow age1.5초·deadline6.5초를 각각 유지한다. 더 긴 유효기간으로 다른 검사를 대체하지 않는다. 구현 시 현행 consumer 상수/승인 pin을 대조한다.
2. **원천 계약:** SOR용 `_AL`을 유효 통합 원천으로 인정한다. 기존 `entry_liquidity_request_code`는 regular KRX 위젯을 실제 SOR 제출에 맞춰 `_AL`로 매핑하므로 이 alias를 보존한다. 별도 KRX 전용 입력이나 NXT `_NX`를 임의 대체하지 않는다. 원 수신시각·제공 거래시각의 정밀도·단위·route·연결 epoch·publisher 세대·source hash를 저장한다. WS를 REST 응답인 것처럼 표기하지 않는다. 연결 직후 부족한10개 체결, 중복/역순, reconnect 공백, coalescing 유실은 source gap이며 로컬 sequence만으로 거래소 전체 체결 무손실을 주장하지 않는다. 제한된 snapshot tail이 필요한 최근10개를 보존하는지 producer부터 검증한다.
3. **소비와 복구:** 각 검사에 충분한 유효 WS 자료가 있으면 해당 `ka10004`/`ka10003` 요청0회. fresh 자료가 잔량/속도 기준에 미달하면 기존 위험 차단을 유지하고 REST로 유리한 값을 다시 찾지 않는다. 미구독/결손/stale일 때만 같은 identity·필요 API별 최대1회 복구를 허용하며 기존 공유 예산과 남은 시한에 종속한다. timeout/예산 대기를 남은 시간 안에 제한할 수 없으면 제출 경로에서 복구를 시작하지 않는다. 늦게 완료된 응답은 폐기하고 과거 신호를 되살리지 않는다.
4. **시간 예산:** t0·checkpoint·고정 deadline을 재시도/leg/REST 응답 때 새로 시작하지 않는다. 준비·유동성·체결속도·registry 저장·gateway 최종 검사·실제 transport 직전 시간을 같은 시도에 결속한다. 각 blocking I/O와 저장 뒤 실제 현재시각으로 재검증하고, 앞 leg가 소진한 시간을 뒤 leg가 공유하는 경우도 검사한다. WS 사용 자체는 주문 허용이 아니며 원래 계좌·주문·가격·수량·cooldown·시장 약세·operator veto·adverse-flow 최종 검사를 그대로 통과해야 한다.
5. **발행 지연:** WS→publisher→파일→reader의 원 자료 age와 처리 지연을 함께 계측한다. 약1초 발행 또는 반복 전체 JSON 읽기가 1.5초 freshness/6.5초 예산을 소진하면 기존 writer/reader에서 필요한 부분만 수리한다. [메인 제출 병목 계획 S3](main-submit-bottleneck-causal-repair-plan-2026-09-21.md)의 공유 producer 변경은 동일 diff/receipt를 재사용하고 중복 구현·동시 writer 변경을 피한다. 이 계획의 주문 consumer 수리는 main 판정/threshold 변경으로 확대하지 않는다.

계좌 가용자금·보유·미체결·정정/취소·주문 전송과 실제 체결 대사는 시장시세 WS 전환 대상이 아니다. 과거 REST 완료 이력/분봉의 초기 적재·복구 역할도 유지한다. 호가 자료는 REST와 WS 어느 쪽도 실제 주문 체결을 보장하지 않는다.

### 3.5 삼성 오전기의 비종결 재검증 상태 수리

- `EntryNotSent`는 transport 전 미전송임이 확인된 경우만 처리한다. registry의 해당 예약을 안전하게 거절/해제한 뒤 guard가 `WAIT`이면 같은 signal identity/t0/deadline/checkpoint를 보존한 `PLANNED` 상태로 다음 기존 loop에서 재검증한다. regular two-leg의 비종결 분기를 기준으로 affected owner를 대조한다.
- terminal `SKIP_*`, 원래 owner 차단, policy/route/epoch 변경, 제출 시한 만료는 종결한다. `TRANSPORT_STARTED`·접수 여부 불명·이미 전송된 주문은 대기 복구 분기로 보내지 않는다. 새 예약은 기존 attempt ordinal/registry 중복 차단을 따라야 한다.
- 저장/재기동 roundtrip에서도 terminal identity가 부활하지 않아야 한다. 과거9건의 registry와 `NO_FILL` 이력을 소급 수정하거나 재주문하지 않는다. 수리는 이후 자연 신호의 상태 전이만 검증한다.

## 4. 단계·산출물·완료 조건

아래 단계는 실행 권한과 각 gate가 충족된 이후의 작업 단위다. **P4는 매 운영 인계에 선행하는 공통 release gate**다. 첫 인계는 `P0→P1 구현/격리검증→P4 소범위 배포→P5 자연 비교·소비 확인`이고, 이후 P2/P2E에 같은 P4/P5를 적용한다. P2E는 기존 reader와 해당 consumer의 필드·시각·체결 이력 계약을 먼저 닫고 소범위 적용한다. 기본3종목 P1 PASS를 삼성E&A/한국전력 등 다른 cohort나 주문 consumer의 PASS로 전용하지 않는다. P2 전체 관측 확대·P3 분봉 완료는 P2E의 선행조건이 아니며 §3.5 상태 수리도 원천 전환과 독립 검증한다. 미래 자연 실행을 앞당기는 일정이 아니다.

| 단계 | 작업 및 산출물 | 종료 조건 |
| --- | --- | --- |
| P0 계약·용량 확인 | 필드/FID 대조표, 활성 consumer×route×type 구독 합집합, REST owner/API별 시도·예산 대기·실제 전송량, 현재 설치 PID/설정과 원천 기준선 | 미확인 wire/한도/필드 의미 명시; 첫3종목의 필요한 데이터와 main 보호 용량 확인. 미확인 범위를 자동 등록하지 않음 |
| P1 공통 reader·3종목 병행 검증 | 기존 publisher 재사용, 삼성·두산·한화 reader의 WS/REST 데이터 비교 구현; 기존 주문판단 입력은 검증 완료 전 유지 | 정상·quiet·재접속·stale·route mismatch fixture PASS. P4를 거친 자연 수신의 필수값/신선도 검증. 같은 원천·관측시점에서 설명되지 않은 필수값 불일치0; KRX/NXT와_AL의 원천 차이는 유효 수신으로 분류. 기존 가격/신선도 검사 불변 |
| P2 시세 전환·관측 확장 | P1 소범위 인계를 확인한 뒤 유효 catalog의58종목/연구198종목 합집합으로 확대 준비. 각 cohort는 P4를 통과해 등록·수신·소비/거부 영수증 확보 | 구독 중복/메인 구독 손실0, scope 미분류0. 미수용·미수신은 명시적 source gap. quote/BBO 요청 및 대기가 줄었는지 동일 분모로 확인 |
| P2E 주문 직전 WS 연결·상태 수리 | §3.4의 유동성/체결속도 source adapter·시간 예산 연결, §3.5 비종결 WAIT 보존. consumer×필드 매핑과 실제 release receipt | 유효 WS 시 해당 시장자료 REST0회, guard 동등성·중복 전송0·시한/원 시각 보존. 미전송 WAIT 재검증·terminal 불변. 독립 P4/P5 검증 |
| P3 분봉 공유·에피소드 연결 | 초기 REST+증명된 WS 집계+누락 복구, 동일 route 완료 분봉의 기존 episode reader 인계 | 기존 bar와 신호 kernel 동등성, mismatch 격리, 중단·재시작 후 초기화 검증. 주문 직전 검사는 별도 P2E가 소유하며 P3가 변경하지 않음 |
| P4 검토·immutable 배포 | implementation→self review→fix→re-review→targeted tests, 별도 worktree/immutable release, 서비스별 source pin·rollback 기록 | 관련 producer/consumer/cache/recovery 모든 경로 finding0; 권한 있는 대상만 배포·재기동. 실제 PID/코드/source hash와 새 자연 소비 확인 |
| P5 자연 수집·장후 연결 | consumer별 신선도/유효 관측, raw→advisory→postclose reader, exact-date policy/PID 연결 | 미래 자연 자료로 검증. P2E는 해당 주문 consumer의 자연 경로 receipt까지 별도 확인. 생성 파일이나 health PASS만으로 종료하지 않으며 source 변경 전후 모집단·경제성은 구분 |

병행 검증은 **같은 데이터 필드의 전송 경로 검증**이며 새 alpha/정책 shadow 축이 아니다. 기존 정책·선택값·수량을 튜닝하지 않는다. 상세 캡처는 필요한 표본/짧은 window로 제한하고 성장 중 JSONL은 stat 후 bounded tail/index로 확인한다.

## 5. 수치 검증과 감시

계측 계약: `metric_role=market_data_transport_quality`, `decision_authority=source_quality_only`, `window_policy=consumer_session_windows_with_explicit_ws_source_items`, `sample_floor=three_consecutive_15_minute_windows_for_each_rollout_cohort`, `primary_decision_metric=consumer_valid_market_data_ratio`, `source_quality_gate=exact_route_original_timestamps_epoch_required_fields`, `forbidden_uses=[order_authority,threshold_relaxation,profit_claim,retired_strategy_activation]`.

| 항목 | 검증 기준 |
| --- | --- |
| 관측 분모 | expected consumer evaluations = valid WS + valid REST recovery + classified not applicable + explicit source gap; unclassified0. 별도로 registered→first received→consumed 수와 실패 사유 대사 |
| 시세 REST 절감 | WS 적용 대상의 같은 종목/route/활성시간으로 정규화한 `ka10001/ka10004` 반복 전송량 **80% 이상 감소를 초기 설계 목표**로 둠. 미시도/탈락시켜 만든 감소는 인정하지 않음 |
| 데이터 가용성 | 실행 cohort에서 기존 freshness 기준을 만족한 평가 비율 **99% 이상을 초기 운영 목표**로 두되 자연 비대상은 사전 계약으로만 제외. 충족 못 하면 원인·분모를 공개하고 해당 rollout 단계를 닫지 않음 |
| 지연/자원 | WS callback·snapshot publish·consumer read p95/p99, CPU/RSS, 파일량, main quote age/평가 지연을 P0 동일 조건과 비교. 기존 경고·stale 한도 초과나 재현 가능한 main 악화는 전환 중단 |
| P2E 제출 경로 | signal identity×leg×attempt 기준 WS eligibility·선택·원천 부족·정상 위험 차단·시한 만료·실제 transport를 구분. 유효 WS가 충족한 검사별 REST 요청0회. t0→준비/REST 대기·응답/로컬 처리/최종 검사 지연을 나누고 동일 frozen 입력·주입 지연에서 불필요 REST 제거와 시한 내 검증 도달을 재현 |
| P2E 자연 수용 | 해당 consumer/cohort별 연속3×15분 원천 창과 이후 자연 submit-path receipt를 별도 검증. 실제 시도가 없으면 source 검증만 통과, 제출 경로는 pending. 서로 다른 정책/원천 세대·기회/leg/재시도를 합산하지 않고 미시도로 지연을 개선한 것처럼 보고하지 않음 |
| 복구 | reconnect/producer restart/실패 snapshot/REST 예산 고갈에서 원 시각 보존, 이전 epoch 미채택, 무제한 retry0, 기존 main·holding 데이터 손실0 |
| 분봉/판정 | 같은 eligible 완료 분봉·동일 정책에서 신호/episode 판정 차이0. 새 원천 때문에 달라진 valid 집합은 정확한 행·시각·이유를 따로 기록; 기존 결함 결과를 복제하지 않음 |
| 감시 | unit liveness PASS와 source coverage 경고를 동시 표시. 등록 누락·필수 data wait·consumer 미소비를 기존 detector에 연결. 저활동 체결과 필수 quote 단절은 구별 |

80%·99%는 개선안을 검증할 **제안 목표**이며 현재 달성값·공식 API 보장·매매 threshold가 아니다. P0에서 재현 가능한 기준선이 없으면 성능 개선을 수치로 확정하지 않는다. 비교 REST 호출도 기존 source-only 예산에서만 수행한다. 자연 45분 관측은 전송 품질의 최소 확인이며 모든 session/전략 효과 검증을 대체하지 않는다. 이 수집 개선은 기존 WS freshness bonus/경제성 정책의 승격과 독립이며 새 점수·보너스 owner를 만들지 않는다.

## 6. 테스트·롤백·보존

- 기존 WS·quote consistency·widget collector·gateway·detector 테스트 파일을 확장한다. 단위검사 외에 writer→파일→독립 process reader→기존 신호 consumer를 연결한 통합 검증이 필요하다.
- 필수 실패 사례: 필드별 서로 다른 수신시각, 파일 재기록만 새로움, `_AL`/KRX/NXT 혼합, 부분 0D, 미래/역순 체결, 연결 세대 변경, 한 consumer 구독 해제, receiver 쓰기 실패, writer 교체 중 read, cache generation 불일치, 동시 fallback, producer 부재, 오래된 REST 복구, 분봉 late revision.
- P2E 회귀: 유효 WS에서 REST mock 호출0회, 같은 frozen 시장자료의 기존 evaluator 판정 동등성, fresh 잔량/속도 미달에서 복구 호출0회, 최근10개 부족/중복/coalescing/reconnect gap 차단, API별 bounded 복구·초과 응답 폐기. +5초 통과 뒤 REST +7초 완료·느린 저장·두 leg 순차 처리에서도 실제 전송0, 신선한 정상 입력과 시한 내 준비에서는 mock transport 도달을 확인한다. 실제 주문으로 테스트하지 않는다.
- 상태 회귀: `WAIT` 미전송→예약 거절/해제→같은 identity 재검증, 새 attempt의 정확한 예약, terminal/deadline/ambiguous/transport-started 재전송0, 저장·재시작 후 동일 결과. 기존 삼성 오전/regular machine 테스트를 재사용하며 다른 exit/holding 상태를 바꾸지 않는다.
- Python targeted pytest·compile·diff, wrapper 변경 시 bash/계약검사, 문서 변경 시 print-only parser를 실행한다. 키움 요청/파서/REG/복구를 건드리기 전에 최신 공식 참조 gate를 다시 닫는다.
- 코드 배포, WS 등록, 첫 수신, 실제 PID 소비, 자연 signal, 주문·체결, 비용 후 EV를 각각 기록한다. 정책 캐시의 예전 PASS만으로 새 source 소비를 인정하지 않는다.
- P1/P2 수집기 rollback은 새 reader 선택과 **추가 관측 구독만** 되돌리고 공유 main/holding 구독은 보존한다. REST 이전 경로도 정상 예산 내에서만 사용하고, 복구 불가 scope는 DATA_WAIT 유지한다. 구버전 schema를 소비하는 release로 전환할 때 호환성·fallback을 먼저 검증한다.
- P2E rollback은 consumer별 source adapter/해당 release를 되돌리되 제출 시한·신선도·중복 차단과 이미 기록된 주문 상태는 보존한다. 신규 상태와 구버전 loader의 호환성을 배포 전에 검사하며 `WAIT`/terminal identity를 초기화하거나 과거 시도를 재실행하지 않는다.
- 보유/주문 state·registry·operator closure receipt는 보존한다. §1의 삼성25주는10:30 과거 관측이며, [수동매도 원장 반영 receipt](../../data/runtime/manual_close_reconciliation/samsung_widget_sale_20260921_0027855/receipt.json)는 주문0027855 매도25주·원장/이월0주와 재기동 소비를 확인했다. 그 증거를 되돌려25주를 복원하지 않는다. 새로운 source 선택이 active position의 정책·target을 바꾸지 않는다. 두산·한화 연구 축적, CJ CGV/영원무역/SK텔레콤 profile 제외 및 retired auto episode는 유지한다.
- 수집 품질 개선은 수익 개선의 전제이며 수익 증명이 아니다. 후속 경제성은 기존 owner에서 실제 source/적용 버전·full/partial fill·비용 결속을 갖춘 COMPLETED 표본으로 평가한다.

## 7. 공식 근거와 구현 전 미확정 항목

- 계획 조사: `2026-09-21T10:34:58+09:00`에 공식 저장소 `main`을 조회했으며 SHA는 `953e5dbff123f437ab4d11a78a95191a685eb51f`다. 이전 작업의 SHA를 현재 공식 revision으로 재사용하지 않는다.
- 확인 경로: 공식 tree 및 `kiwoom/core/ws_client.py`, `kiwoom/realtime/packets.py`, `kiwoom/realtime/schemas.py`, `kiwoom/_data/kiwoom_api_spec.json`. 해당 tree에 `kiwoom_docs`는 없다. 계획 조사만으로 개별 FID/한도/모든 REST envelope 검증을 완료했다고 주장하지 않는다.
- [공식 실시간 packet helper](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/blob/953e5dbff123f437ab4d11a78a95191a685eb51f/kiwoom/realtime/packets.py)의 REG/REMOVE와 refresh 의미를 기존 구현과 대조해야 한다. group 교체로 다른 owner 구독을 지우는 사고를 회귀로 막는다.
- [키움 공식 API 안내](https://openapi.kiwoom.com/m/guide/apiguide?jobTpCode=07)는 주식체결0B·주식호가잔량0D 및 분봉ka10080을 구분한다. 상세 FID/route·무거래/거래량 의미·등록 한도·real/demo 차이·continuation은 P0에서 `specs/core/realtime/Postman` 및 portal을 교차 확인한다. 공식 소스와 관측이 충돌하면 해당 source 계약을 gap으로 남긴다.
- **P0에서 닫아야 할 항목:** 현재 WS의 exact item/type 등록·실수신 합집합과 남은 용량, consumer 필드별 원천 동등성, 198종목 확대 시 main 영향, 연속 체결 원장의 분봉 집계 적합성. 이 항목이 미확정인 상태에서 전 종목 WS 전환이나 REST 제거를 약속하지 않는다.

## 8. 문서 검토 결과

계획 작성 당시 범위는 기존 수집/소비 경로 개선 설계로 제한했다. 도입 단계·구독 용량 미확정·공통 예산·교차 process 복구·분봉 연속성·기존 holding 보존·detector coverage·현재 checklist 단일 owner를 재검토했다. 당시 코드/런타임 변경과 외부 sync는 수행하지 않았다. 현재 명시 승인된 P0/P1 구현·인계는 위 연결된 별도 수리 기록이 소유하며, 후속 자연 검증·확대·분봉 gate는 유지한다.

9/21 후속 계획 보완은 §1.1의9건을 근거로 주문 직전 검사를 일괄 REST 유지하던 범위를 P2E로 확장했다. 입력 adapter·시간 예산·WAIT 수리·cohort별 검증·rollback을 검토하고 P3/메인 owner와 구분했다. 이번 변경은 계획/현재 checklist 연결만이며 코드·배포·재기동·주문·외부 sync를 수행하지 않는다. 단일 실행 owner는 상단 stable ID를 유지한다.

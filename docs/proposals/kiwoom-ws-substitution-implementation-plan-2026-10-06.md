# 키움 REST → WS 대체 구현계획 — 2026-10-06

## 1. 결정·범위·완료 의미

**계측·원천 보존 → 신선한 정확 경로 호가 재사용 → 기존 완성봉의 Main 소비 연결 → 체결·잔고 이벤트 소비와 계좌 조회 최적화 → 실제 비용 대사 → 지수·breadth 전환 순으로 구현한다.** 비용 의미 미확정이나 실제 체결 표본 부재가 호가·분봉 등 독립 영역의 구현을 막지 않게 단계별로 닫는다. 제출 병목의 평가·판정 경로 수리는 기존 [Main 제출 공백 보완계획](main-submit-drought-priority-remediation-plan-2026-10-06.md)이 우선한다.

목표는 필요한 입력을 동일한 의미와 더 적은 REST 전송으로 공급하고, 체결·비용 원천 손실을 줄이는 것이다. 다음 세 가지 결과를 각각 증명한다.

1. **코드·계약 완료:** 같은 source/route/시각에서 정확한 소비, 누락·복구·동시성·custody·guard 회귀 통과.
2. **성능 완료:** 적격 구간의 실제 HTTP attempt 감소, 결정/수신 지연과 자원 사용의 비퇴행. 논리 헬퍼 호출을 HTTP로 세지 않는다.
3. **운영 수용:** 선택 release·실제 PID·새 원천·최종 소비의 직접 연결. 체결·terminal·실제 비용·실현손익은 추가로 구분한다.

현재 요청은 **계획 수립**이다. 이 문서는 코드 변경·REG/REMOVE·계좌 API 호출·기존 정책 변경·배포·재기동·장후 실행을 수행하지 않는다. 아래 신규 파일·field·mode·성능 수치는 구현 제안이며 현재 존재하거나 승인된 운영 계약이 아니다. 일정과 실행 OPEN owner는 실제 구현 지시 때 당일 checklist에서 정한다. 기존 dirty 작업본은 유지한다.

## 2. 현재 근거와 이번 계획에서 추가 확인한 제약

근거는 [전수 조사](../audits/kiwoom-rest-ws-substitution-survey-2026-10-06.md), [45 REST ID + 인증 경로의 코드 inventory](../audits/kiwoom-rest-ws-substitution-survey-2026-10-06-inventory.md), 실제 producer/consumer다. 전수 조사에서는 현재 사용·과거 분기·공통 헬퍼·선택적 복구를 구분했다.

- 조사 마지막 source: commit `fd222e315577c10853b23db583f260ef76259b39`, release `probe-original-source-20261006-fd222e31`, Main `ubuntu` PID `126945`. 이것은 10/6 조사 시점의 receipt이며 구현·배포 때 다시 확인한다.
- 공식 upstream HEAD는 이번 계획 검토 중 17:29~17:30 KST에도 `953e5dbff123f437ab4d11a78a95191a685eb51f`로 확인했다. `kiwoom_docs` 부재, packaged spec/specs/core/realtime/Postman cross-check와 비용 필드 의미 결손은 조사에 기록되어 있다. 각 protocol 변경을 작성하기 전에 [Official Reference Gate](../kiwoom-api-data-contract.md#official-kiwoom-reference-gate)를 다시 실행하고 최신 SHA·경로·조회시각을 변경 evidence에 남긴다.
- 현재 `00` 수신은 존재하지만 raw allowlist가 `938/939`, `904`, `901`, 계좌/신용 scope를 충분히 보존하지 않는다. `04`의 등록·consumer는 없다.
- 계좌는 45초 read-only snapshot과 90초 lifecycle reconciliation이 single-flight로 조정된다. 단순히 두 주기를 더해서 호출량을 계산하지 않는다.
- **[broker_symbol_verified_flat](../../src/engine/scalping/ai_market_snapshot.py)의 고정감시 편입에는 60초 이내 snapshot, KRX+NXT 모두 성공, 미체결 검증, 유효한 수량이 필요하다.** 45초 갱신을 무작정 없애면 90초 대사 사이에 편입 증빙이 stale해진다. `04`의 한 종목 통보로 양 거래소의 전체 flat census를 대체할 수 없다.
- **WS 완성봉 구현은 이미 있다.** [CompletedBarProjection](../../src/engine/scalping/micro_reversion/completed_bars.py)과 [shared_ws_snapshot](../../src/trading/market/shared_ws_snapshot.py)은 durable 원천·완료봉·checkpoint·REST seed를 가진다. 현재 selector의 consumer는 `episode`이며 reader는 `_AL`에 한정된다. Main 연결, 다른 정확 route, 대상 모집단의 natural coverage는 별도 구현/수용이다. 기존 기능을 새 collector로 복제하지 않는다.
- `selected_completed_bar_payload`는 현재 일부 plain request를 내부 `_AL`로 만드는 경로가 있다. Main은 **원 요청이 `_AL`인지 먼저 확인**하고, plain KRX/`_NX`에는 이 adapter를 전용하지 않는다.
- zero-base signed tape와 프로그램 흐름은 이미 WS-first인 부분이 있다. 호가 refresh는 `force`, source freshness, quote conflict와 함께 검토한다. 실제 실행하지 않는 legacy gatekeeper를 현재 Main 호출 절감의 분모에 넣지 않는다.
- 오늘 조사 로그의 349 capacity logical/218 HTTP attempt는 `kt00011` 한 헬퍼의 여러 PID 합이며 전체 호출량이나 새 WS 절감률이 아니다. 마지막 PID의 prefetch/관측 재사용도 이미 적용된 기준선이다.

공식 근거: [packaged spec](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/blob/953e5dbff123f437ab4d11a78a95191a685eb51f/kiwoom/_data/kiwoom_api_spec.json), [WS packet](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/blob/953e5dbff123f437ab4d11a78a95191a685eb51f/kiwoom/realtime/packets.py), [core WS](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/blob/953e5dbff123f437ab4d11a78a95191a685eb51f/kiwoom/core/ws_client.py). `938/939`는 공식 명세에 있으나 per-fill/order/symbol/account-day 누적·반올림 설명은 미확정이다. `04/951`은 Extra Item이며 예수금으로 추정하지 않는다.

## 3. 대체 범위와 유지할 REST

| 영역 | 대체할 소비 | 첫 구현 범위 | 계속 사용하는 REST |
| --- | --- | --- | --- |
| 현재 호가·tape·strength | `ka10004`, `ka10003/84`, `ka10046`의 현재값 | 기존 exact `0B/0D` receipt의 WS-first 재사용; 이미 적용된 부분 제외 | force/독립 확인·known conflict·stale/gap, 과거 tape 및 5/20/60분 broker trend |
| 분봉 | 반복 `ka10080` | 기존 `_AL` durable completed-bar를 **Main의 정확 `_AL` 적격 consumer**에 연결 | 초기 이력·미관측·다른 route·필수 session prefix·수정주가 결손·과거 backfill |
| 주문·체결 | 정상 구간 `kt00007/ka10075/76` 일부 반복 | `00` journal→기존 owner/order chain→검증된 read-only projection | boot/reconnect/gap/terminal 원장 대사, 다른 날짜·확정 취소/정정 child 불명 |
| 잔고·표시 평가 | `kt00005/18`의 일부 context 갱신 | `04` dirty/부분 사실부터; verified projection에 한해 context 소비 | 전체 account/venue/credit census, flat·수량·custody 확인, 독립 90초 대사 |
| 수수료·세금 | 현재 버리는 `00/938/939` | raw 수집·미귀속 비용 보존, REST 비교 | `kt00008` 정산, `ka10073` 일자·종목 aggregate, 필요한 order-cost 대사 |
| 지수·breadth | `ka20003`, 관측 후 `ka20005` 일부 | `0J/0U` 의미·모집단 검증 후 기존 producer에 연결 | 최초 업종/상장종목 seed, 전체 표의 미제공 항목, gap·과거 이력 |
| 매수 capacity·예수금 | 직접 WS 대체 없음 | `00/04`는 기존 영수증의 invalidation 신호만 제공 | `kt00011/kt00001` required fresh read와 기존 source-only exact reuse |
| 발굴·투자자·주문 쓰기 | 직접 WS 대체 없음 | 현행 producer 유지 | `ka10023/27` 신규 발견, 실제 투자자 집계·master·과거 차트, `kt10000~3`, OAuth |

market `0B`는 내 주문 체결이 아니다. `0F/0w`는 실제 외국인·기관 분류가 아니다. `04/933`은 종목·매수가격별 `kt00011` 주문가능수량이 아니다. WS에 실시간이라는 이름이 있어도 전체 시장·계좌 완전성, broker cost, terminal 또는 history를 자동 증명하지 않는다.

## 4. 구현 위치와 소유 경계

location gate를 적용해 기존 역할 패키지와 주변 producer를 확인했다. engine-root의 새 Python 파일, 별도 봇·daemon·구독 연결·새 전체 장후 runner는 만들지 않는다. 불필요한 module 이동이나 큰 파일 전체 정리는 묶지 않는다.

| owner / 파일 | 구현 역할 |
| --- | --- |
| [kiwoom_websocket.py](../../src/engine/kiwoom_websocket.py) | genuine `00/04` ingress, 원 field/clock/epoch/순번, 비차단 journal enqueue, 기존 이벤트 dispatch, 등록 lifecycle |
| [kiwoom_utils.py](../../src/utils/kiwoom_utils.py), [kiwoom_orders.py](../../src/engine/kiwoom_orders.py) | 기존 transport 경계의 HTTP/page/retry 계측; 실제 source metadata. 계좌 payload/토큰 로그 금지 |
| [market_data_cache.py](../../src/trading/market/market_data_cache.py), [quote_consistency.py](../../src/trading/market/quote_consistency.py) | 기존 route별 receipt·health 재사용. 선택 helper는 pure하며 network 또는 engine 역의존 없음 |
| [sniper_state_handlers.py](../../src/engine/sniper_state_handlers.py) | 제출 전 quote 선택·재검증, capacity/기존 guard 유지, 변경은 해당 함수와 caller로 제한 |
| [entry_candle_context.py](../../src/engine/scalping/entry_candle_context.py), shared_ws_snapshot/completed_bars | Main candle selector, 기존 projection/seed·feature 요구 history 보존 |
| [sniper_sync.py](../../src/engine/sniper_sync.py), [kiwoom_sniper_v2.py](../../src/engine/kiwoom_sniper_v2.py) | REST baseline·복구·90초 독립 대사, 기존 single-flight, consumer demand/증빙 만료에 따른 갱신 |
| [ai_market_snapshot.py](../../src/engine/scalping/ai_market_snapshot.py), [holding_decision_context.py](../../src/engine/scalping/holding_decision_context.py) | REST census와 WS 부분/검증 상태를 구분한 context 소비; fixed-watch flat proof 분리 |
| [sniper_execution_receipts.py](../../src/engine/sniper_execution_receipts.py), [owner_custody_registry.py](../../src/trading/order/owner_custody_registry.py) | native order/fill/parent/cancel identity와 기존 lifecycle 연결, 비용 source 수준 분리 |
| [market_panic_breadth_collector.py](../../src/engine/market_panic_breadth_collector.py) | `0J/0U` 의미 대조와 기존 breadth 보고/guard consumer 연결 |

새 파일이 필요한 두 역할은 분리한다. 제안 파일 `src/trading/order/account_event_state.py`는 network/I/O/engine import 없는 account event reducer·scope·validity를 소유한다. `src/engine/infrastructure/account_event_journal.py`는 bounded queue·append·flush/ack·checkpoint만 소유한다. source-only account 원천을 주문/매수 owner로 해석하거나 Main lifecycle ID를 mint하지 않는다. 공용 시장 cache에는 account 데이터를 넣지 않는다. 기존 lifecycle/SELL crash-safe journal의 canonical 역할은 보존하며 새 account source를 raw 복제 거래로 더하지 않는다.

테스트는 기존 `src/tests`와 `src/tests/benchmarks`에 둔다. 신규 domain test/benchmark는 계좌 reducer·durability·통합 소비·성능의 독립 불변식을 검증하는 역할이며 engine-root allowlist를 변경할 필요가 없다. 구현 때 신규 파일명/역할·imports를 다시 검토한다.

## 5. 공통 원천·선택·진단 계약

### 5.1 원천 envelope와 시간

기존 market/account envelope에 호환 확장한다. 아래는 필요한 필드군이며 현행 schema가 이미 가진 필드는 그대로 사용한다.

| 필드군 | 필요한 의미 |
| --- | --- |
| identity | schema/version, original source type, item/route, symbol, KST source date/session, account scope hash 또는 market scope, producer release/PID/start identity |
| clock | packet ingress, 실제 broker event raw time와 검증 상태, durable append ack, REST request start/receive, 소비 cutoff. 각각 원시각 유지 |
| continuity | connection epoch, 로컬 ingress sequence, durable cursor, known drop/overflow/append error/gap, register state/first data, projection revision/hash |
| scope validity | 완전 census/부분 사실, source gap/불명 이유, selected-source status, 기존 consumer별 feature/history/TTL 요구 충족 여부 |
| order binding | date+account+native order/fill/original parent, owner registry reference, actual venue와 SOR route 구분, side·credit 구분 |
| performance | logical request, actual HTTP attempt incl timeout, page/continuation/retry, admission wait, WS selection/reuse, REST seed/gap/required fallback reason |
| authority | source/context only, orders/broker mutation/quantity/provider/threshold authority 없음. 실제 체결 fact와 `actual_order_submitted` 실행 주장을 혼동하지 않음 |

PING·LOGIN·다른 type·file mtime·snapshot copy는 quote/tape/account 잔고 원시각을 갱신하지 않는다. `successful_exchanges`, verified-empty, `open_orders_request_succeeded`는 기존 REST 또는 동등성이 검증된 자기 scope의 증거에서만 온다. `04` 1건으로 KRX+NXT 성공을 찍지 않는다. `captured_at`과 per-field source 시각·만료를 분리하되 기존 strict consumer를 먼저 완화하지 않는다.

`0B/0D`의 동일 item/session/epoch를 확인한다. `_AL`은 integrated 시장 원천이며 underlying 실제 거래소가 증명되지 않으면 KRX/NXT 체결로 귀속하지 않는다. account endpoint의 raw 6자리 code와 market item suffix를 혼용하지 않는다.

### 5.2 metric decision contract

이 변경의 계측은 전략 튜닝 metric이 아니다.

- `metric_role=source_quality_gate`
- `decision_authority=source_substitution_validation_only_no_order_authority`
- `window_policy=frozen_same_source_date_scope_release_consumer_request_window`
- `sample_floor=phase_required_scenarios_and_reported_eligible_n`; 표본 수·누락은 실제 값으로 보고하며 단순 복수 날짜 대기를 부과하지 않는다.
- `primary_decision_metric=physical_http_attempts_per_valid_consumer_request`; source fidelity·freshness·lag·guard 결과·CPU/RSS를 병기한다.
- `source_quality_gate=exact_scope_original_clocks_durable_cursor_required_features_no_unexplained_consumer_divergence`
- `forbidden_uses=threshold_provider_order_price_quantity_cap_mutation,broker_pnl_claim,retired_consumer_activation`

counter 자체가 caller를 늦추거나 callback에 파일 동기 I/O를 추가해서는 안 된다. credential, 계좌번호, raw broker 응답 전체는 공용 로그에 남기지 않는다. account journal에는 승인된 보관 field만 기록하고 account를 hash로 결속한다. 정상 원 주문 필드는 필요한 내부 journal에 보존하며 Telegram/briefing에는 노출하지 않는다.

## 6. 단계별 상세 구현

### P0 — 기준선·HTTP 계측·안전한 account 원천 보존

**입력:** 현재 선택 release/PID/dirty 경계, 45 API inventory, 현재 정책/route/consumer hash, 지금 forward source 시대의 bounded 영수증.

1. utils/orders/adaptive-exit/독립 gateway의 transport 경계를 재대조한다. 직접 `requests.post`와 wrapper/continuation을 빠뜨리지 않는다. 테스트 fake transport와 실제 runtime을 구분한다.
2. HTTP 전송 **직전** attempt를 증가시켜 timeout도 전송에 포함한다. governor defer만으로 전송 수를 증가시키지 않는다. auth retry·page·업무 rate-limit·논리 caller·기존 cache hit를 각각 기록한다. `kt00011`의 기존 계측/재사용을 기준선에 포함하며 중복 계측하지 않는다.
3. `00` raw allowlist와 normalizer에 `904/901/938/939`, account hash·credit scope를 보강한다. 선택적인 비용 field 누락이 기존 체결 처리 자체를 차단하지 않게 한다. 명시 `type=00`만 native 증거로 승격한다.
4. packet ingress에서 bounded **nonblocking** 원천 enqueue를 하고 기존 `ORDER_NOTICE/ORDER_EXECUTED`를 계속 dispatch한다. 실제 SELL/보호 처리에 새 fsync 완료를 기다리게 하지 않는다. source projection은 durable ack 뒤에만 진전한다.
5. queue overflow/append 실패/disk full/consumer lag를 scope gap으로 남기고 WS 대체를 철회한다. 기존 체결 처리와 REST 복구를 유지한다. gap marker 자체가 저장되지 않는 장애도 복구 시 checkpoint/cursor 불일치로 검출한다. writer 재시작에서 새 epoch/process identity와 마지막 ack를 확인한다.
6. 계좌 journal은 승인된 compact 필드만 append, 날짜/계좌 scope partition, bounded checkpoint/index를 사용한다. 기본 제안은 최대 1,024 event queue·16KiB compact record·50ms flush batch이며 실제 event 크기와 P99 lag로 검증한다. 이 수치는 확정 거래 guard나 공식 Kiwoom 제한이 아니다. cutoff cursor를 읽으며 매 요청마다 당일 전체 파일을 재스캔하지 않는다.
7. 원천 writer의 디스크 증가량·queue capacity·fsync stall을 stress에서 측정하고 기존 저장소 보관 규칙과 연결한다. 이 작업으로 보관된 과거 raw를 삭제하거나 retention을 새로 실행하지 않는다.

**완료:** 빈/0/부호/큰 비용 raw가 손실 없이 구분되고, 메모리 enqueue 또는 수신 성공을 durable 성공으로 보고하지 않는다. snapshot writer 장애가 기존 주문/보호 처리에 추가 wait를 만들지 않는다. 계측의 전송 수가 fake transport 기록과 정확히 일치한다.

P0 source-only capture 구현은 비용의 경제적 의미 확정과 분리한다. `938/939` 해석은 P5에서만 승격한다.

### P1 — 제출 전 호가와 현재 tape의 WS 우선 재사용

1. existing quote health와 type별 receipt를 읽는 pure selector를 사용한다. caller의 정확 item·session·epoch·필수 bid/ask/depth·원 수신시각·기존 TTL·known conflict를 검사한다.
2. `force=True`, caller가 독립 broker 교차확인을 요구하는 경우, known divergence/route conflict, 부족/stale/unproven quote에는 기존 `ka10004` 경로를 유지한다. source mode만 보고 force를 무시하지 않는다.
3. 적격 `0D`/`0B`에서는 불필요한 `ka10004` refresh를 생략하고 기존 최종 가격·slippage·liquidity·DANGER/stale/account/order/수량 guard에 같은 source facts를 넘긴다. 제출 직전 다시 age/epoch/owner를 검증한다. provider/주문/재시도 권한을 새로 주지 않는다.
4. quote-consistency consumer가 REST 교차근거를 필수로 쓰는 분기는 REST를 유지하거나 기존 유효한 독립 근거를 함께 확인한다. WS 선택이 과거 conflict를 지우거나 canonical 실행가능 가격을 몰래 바꾸지 않게 한다.
5. already-WS-first zero-base tape/program 호출은 재구현하지 않는다. 실제 활성 consumer 중 REST 현재값을 다시 요청하는 부분만 바꾼다. `ka10046` broker 5/20/60분 이력은 WS 현재값 복사로 대체하지 않는다.
6. 분석 context의 WS source는 기존 source timestamp를 보존한다. RPC가 없으면 `rest_received_ts_ms`·fresh REST receipt를 발명하지 않는다. 동일 shape의 반환값과 source transport는 구분한다.

**완료:** forced/conflict/stale 경로의 호출·거부 의미가 보존되고, 적격 현재 quote/tape의 HTTP가 감소한다. 기존 가격 게이트/recipe/AI threshold 변경은 Main 제출 공백 계획의 별도 diff로 남긴다. valid BLOCK/RECHECK에 새 provider/주문을 발생시키지 않는다.

### P2 — 기존 WS 완성봉을 Main에 연결

1. `CompletedBarProjection`, durable path journal, `read_shared_completed_bars`, seed cache·lock/backoff·hash/revision 검증을 재사용한다. 기존 observer의 모집단/게이트와 신규 Main의 필요 scope를 inventory로 대조한다.
2. `shared_ws_snapshot`의 소비 enum에 명시 Main consumer를 추가하되 기본은 REST다. **원 request item `_AL`, 현 활성 Main 대상, source date/session/epoch, 적격 symbol scope**가 일치할 때만 기존 selector를 호출한다. Episode 설정을 Main에 상속하거나 plain code를 `_AL`로 바꾸지 않는다. retired Widget consumer를 다시 넣지 않는다.
3. Main `fetch_entry_candles_with_meta`의 source selector에 `rest`/`ws_when_ready` 두 후보를 연결한다. 초기 rollout은 `ws_when_ready`이고 강제 WS-only를 만들지 않는다. 부족한 rolling history/session anchor를 REST seed 또는 현재 원천 경로로 처리한다.
4. 기존 caller가 요구하는 40 completed bars와 3/5/15분·session VWAP·opening-range·prev-day 등 **feature별 history**를 검증한다. 40개 rolling 봉만 있어도 session prefix가 필요하면 미완전으로 남긴다. 기존 partial-history toggle은 Main의 floor나 source quality를 완화할 수 없다.
5. 수정주가/기업행사 기준이 REST seed와 다르면 해당 symbol/date의 WS 선택을 하지 않는다. 불일치 원인·값·생성 hash를 보존한다. seed overlap은 timestamp별 dedup하며 current partial, late revision, volume regression, reconnect, dropped point를 기존 journal integrity와 함께 판정한다.
6. `source_api_id`를 `ka10080`인 것처럼 위장하지 않고 `source_transport`, native WS types, compatibility shape, seed/WS lineage를 분리한다. 기존 preflight/calibration consumer가 WS를 모르면 그 consumer contract까지 수정하고 validation 후에만 소비한다.
7. Main/holding/장후 price source는 같은 완성봉/원천을 재사용하되 서로 다른 cutoff와 history 요구를 지킨다. 다른 requested route를 사용하거나 미래 event를 과거 evaluation에 붙이지 않는다. 목표/손절의 동일 봉 순서 불명은 unresolved이고 비용·stop·owner replay는 독립 결손이다.
8. 1차 `_AL` cohort가 닫힌 뒤 plain KRX/`_NX`는 **현재 writer가 해당 item을 정확히 보존하고 있으면** 기존 pure projection을 scope-aware하게 일반화할 별도 diff를 낸다. 수신 모집단이 없으면 REST 유지로 닫는다. 새 observer/구독을 열어 부족분을 메우는 것이 자동 전제는 아니다.

**완료:** 기존 episode 계약과 Main 최소 history가 모두 보존되고, seed·정상·gap 합계를 포함한 실제 HTTP가 감소한다. source copy/heartbeat가 봉을 fresh하게 만들지 않으며 serializer와 consumer의 단위/시각/해시가 같다. 필요 history가 0인 표본을 성공·0비용·정상 input으로 바꾸지 않는다.

### P3 — `04` 등록과 account event projection의 관측 검증

1. 공식 `04` request/response와 계좌 subscription 의미, broker/account scope, real/mock, reconnect를 재검증한다. 기존 `00`·session·market registration을 유지하는 additive packet을 만들고 중복 등록/REMOVE가 다른 type·group을 제거하지 않는지 fake WS로 검증한다.
2. `04`의 보유수량·매입단가·매매가능 관련 잔고 사실과 credit/loan scope를 보존한다. cash/deposit/신규 BUY capacity로 재명명하지 않는다. `04`에 broker 발생시각/actual venue가 없으면 null/unproven으로 남긴다.
3. 첫 버전 `04`는 **부분 원천과 dirty 알림**이다. canonical REST census·verified-flat·DB/custody·주문 수량을 직접 바꾸지 않는다. Main/수동/역사 owner 결속이 안 된 이벤트는 해당 account/symbol을 dirty로 표시한다.
4. `00`은 date/account/native order/parent/fill로 dedup한다. unit fill·누적 fill을 각각 보존해 중복 더하지 않는다. nonfill 접수·확인·거부·정정·취소 상태를 기존 정확 chain에 연결한다. `R=0` 또는 주문이 미체결 목록에서 사라졌다는 사실만으로 terminal을 만들지 않는다.
5. projection bootstrap에서 `lower_cursor`→REST request→`upper_cursor`를 기록한다. **조회 중 도착한 event가 REST에 이미 반영됐는지 불명인 경우 blind replay하지 않는다.** overlap을 dirty로 남기고 현재 bounded full snapshot을 쓰며, 필요 재조회도 기존 budget/single-flight 안에서 제한한다. 계속 이벤트가 온다고 무한 quiet 대기를 하지 않는다.
6. REST snapshot 종료 후 늦게 수신한 과거 event, `04`와 `00`의 수신 순서, 두 REST 시장 요청 사이의 체결, 연결 epoch 변경을 별도로 처리한다. broker 순서가 증명되지 않으면 수신 순서를 경제적 발생 순서로 주장하지 않는다.
7. per-field clock/revision과 completeness를 기존 broker context와 분리해 저장한다. 두 writer가 동일 account checkpoint를 소유하지 않도록 lease/process identity를 검증한다. 거래를 소유하지 않는 reducer는 복구 주문·DB update를 직접 호출하지 않는다.

**완료:** 동일 source cutoff의 REST 대조에서 qty/open-order/credit/owner 의미가 설명 가능하고, 중복/역순/수동/불명 order를 성공으로 흡수하지 않는다. 실제 비용/fill가 없으면 해당 항목의 natural 상태는 `not_observed`다. 관측 기능 검증을 위해 실제 주문을 만들지 않는다.

### P4 — account context 소비·수요 기반 조회 절감

P3의 검증된 scope만 입력으로 사용한다. 첫 rollout에서 **90초 lifecycle 대사와 exact boot/reconnect/terminal/custody REST는 유지**한다.

1. 계좌 context의 per-field WS facts와 REST census를 분리한다. 새 position fact가 다른 종목·open-order·예수금·양 거래소 census를 fresh하게 만들지 않게 한다. 보유 AI에 넘기는 부분 사실도 현재 해당 consumer의 source/freshness 계약을 충족할 때만 선택한다.
2. 45초 read-only 갱신을 timer 만료만으로 무조건 요청하는 대신 consumer 수요·dirty·진행 중 작업·마감으로 결정하는 pure planner를 만든다. caller가 요구하는 **60초 fixed-watch flat proof, 보유 context TTL, after-fill 요청**을 입력으로 받으며 만료 전에 기존 single-flight worker에 예약한다. 메인 getter는 network로 대기하지 않는다. 먼저 snapshot의 직접·간접 consumer 전체를 대조하고 demand 등록을 검증한다. consumer 누락/불명, admission 대기 때문에 deadline을 지킬 수 없는 scope에는 기존 45초 갱신을 유지한다. 새로운 pending 수요의 첫 요청이 stale로 막히는 회귀도 검증한다.
3. 소비자가 없고 canonical proof가 필요 없는 구간의 불필요한 snapshot만 생략할 수 있다. **quiet WS/PING만으로 60초 proof를 연장하지 않는다.** admission이 필요한 경우에는 REST census를 제때 확보한다. 기존 2초/5초 capacity reuse와 `kt00001/11` required fresh는 유지한다.
4. 정상 `00/04`마다 즉시 전체 REST를 호출하지 않는다. dirty scope를 coalesce하고 해당 consumer deadline에 맞춘다. 이미 after-fill refresh/90초 task가 in-flight이면 기존 rerun owner를 재사용한다. 재접속/gap/known mismatch는 기존 필수 복구로 분류하고 source-only 작업보다 우선하지만 request reserve·retry 상한을 변경하지 않는다.
5. snapshot cohort에서 생략하지 못한 이유(`flat_proof_due`, `holding_context_due`, `source_gap`, `manual_scope_unbound`, `pending_terminal`, `inflight_coalesced` 등)는 기존 진단 owner에 기록한다. 새 병목 taxonomy·alpha family를 만들지 않는다.
6. 이후 검증된 order projection으로 개별 정상 status poll을 줄일 수 있어도, 초기수량·adaptive-exit·cancel/replace의 exact terminal 소비자는 원장 완전성과 owner chain 계약을 별도로 닫을 때만 전환한다. REST 부재 증명, 확인 취소수량, `Q=F+confirmed_C`·잔여 `R`의 기존 의미를 유지한다.

**완료:** 단순 poll 감소가 아니라 다음을 함께 만족한다. 60초 편입 검사와 기존 보유 preflight가 stale 때문에 더 자주 막히지 않고, hard/account/quantity/custody 결과가 같다. 실제 `kt00005/18/75` 전송이 적격 idle 구간에서 감소한다. 수요가 항상 존재하거나 자연 표본이 없으면 절감 주기를 임의 확정하지 않는다.

### P5 — WS 비용과 실제 정산의 정확 귀속

1. `938/939`의 official 의미·단위·누적 scope·반올림·정산 수정·buy/sell/credit/venue 차이를 확인한다. 데이터에 가장 잘 맞는 누적 가설을 곧바로 protocol 사실로 채택하지 않는다.
2. 자연 수신 원천과 날짜/종목/order/fill을 결속한 REST 비용을 immutable cutoff로 비교한다. 필요한 범위의 `ka10075/76`, `kt00008`, `ka10073`을 기존 source-only/API budget 안에서 사용하며 비용 없는 행을 0원으로 채우지 않는다. 검증 목적의 새 매수·매도는 없다.
3. partial→full, 여러 fill/order/owner, cancel/amend child, 환급/수정, 장경계·익일결제, 같은 symbol의 Main/manual·역사 custody를 검증한다. 반복되는 당일 aggregate field를 fill마다 합산하지 않는다. `kt00008/ka10073`에 native order identity가 없으면 유일 귀속이 증명된 범위만 비교한다.
4. 제안 상태는 `configured_estimate`, `ws_reported_unallocated`, `broker_reconciled_exact`이다. 현재 Main의 configured cost 원천을 보존하고 actual fee/tax 필드를 별도로 둔다. delta 또는 정산 수정은 같은 ledger revision에 귀속해 두 번 비용을 빼지 않는다.
5. 실제 fee-tax가 exact해도 slippage는 동일 판정/제출 시점 route의 실행가능 quote와 실제 fill이 필요하다. gross나 modeled PnL을 broker net으로 바꾸지 않는다. source/cost version이 바뀌면 forward label/kernel의 generation과 consumer hash를 함께 검증한다.
6. official 의미가 끝내 미정이면 capture/미귀속 대조를 완료하고 **비용 승격만** `semantic_contract_gap`로 남긴다. 호가·분봉·기존 정책 초기 채택을 다시 경제성 대기로 묶지 않는다. 정확 실제 비용이 확정된 범위에서만 후행 데이터·경제성 보고에 인계한다.

**완료:** 계좌/일자 합계와 각 주문/owner 귀속이 모순 없이 설명되고, 서로 다른 집계 범위는 합산하지 않는다. P5 비용 증거는 별도이며 이 계획으로 정책 publisher를 자동 실행하지 않는다.

### P6 — 지수·breadth 일부의 WS 전환

1. `0J/0U`를 기존 WS 연결의 명시 index scope에 추가하는 후보를 검증한다. stock watch cap을 늘리거나 전 시장 모든 종목을 구독하지 않는다. 기존 market/session type를 제거하지 않는다.
2. `ka20003`의 업종 코드·필터·분모·상하한 포함관계·KRX/NXT 의미를 `0J/0U`와 비교한다. `0U/256` 거래형성종목수는 REST 상장종목수의 대체가 아니다. index FID의 generic 단위 설명이 실제 값과 모순이면 source gap을 남긴다.
3. 현재 시장약세 guard가 필요한 필드만 검증해 existing collector에 공급한다. 일부 WS field로 entire all-industries table을 성공 처리하지 않는다. 최초 census·없는 필드·과거 index history는 REST/cache를 유지한다.
4. 동일 scope snapshot의 clock/분모/guard 결과가 동등한 후 해당 current portion만 선택한다. 다른 entry-source canary와 같은 stage에서 동시에 활성화하지 않는다.

**완료:** 기존 breadth 보고와 시장약세 guard의 모집단/필드/시각·차단 의미가 보존되며 해당 REST 반복조회가 줄어든다. 동등 항목이 없으면 rest-retained로 닫는다.

## 7. 샘플·통합·성능 검증

### 7.1 원천·샘플 구성

- 실제 sample은 `2026-09-29` 이후 forward 원천 중 코드·정책·route·clock이 맞는 범위를 선택하고, 현재 source generation과 비교 가능 여부를 고정한다. 6~8월 raw를 다시 읽거나 다운로드하지 않는다. 합성 fixture 날짜는 protocol 단위 검사이며 정책 학습·실제 비용 증거가 아니다.
- 고정 manifest는 baseline/candidate commit, official SHA, API/caller/consumer, origin/account **hash**, payload/item/date/session/epoch, 원 file/hash/offset/cursor, 기존 TTL/history/guard, packet/REST cutoff, version을 담는다.
- 데이터는 frame 전체를 메모리에 읽지 않고 bounded cursor/index와 필요한 symbol·window만 읽는다. 같은 canonical source와 projection을 unique 두 건으로 세지 않는다. 재생 시 미래 seed/quote/fill을 이전 요청에 공급하지 않는다.
- sample이 없는 scope는 `not_observed`, 비교 가능한 실제 HTTP가 없으면 `no_eligible_http_reduction`이다. 기술 수용에 복수 거래일·양의 수익·실제 주문 생성을 새로 강제하지 않는다.

### 7.2 필수 결함 주입과 의미 검사

| 구분 | 샘플·결함 | 기대 결과 |
| --- | --- | --- |
| 호가/tape | 정상 fresh, 정확 TTL 경계, future clock, type clock 혼합, `_AL/_NX/plain`, epoch 변경, known conflict, forced refresh | 적격 선택만 REST 생략. stale/conflict/force 유지, guard·원시각·정확 route 보존 |
| 주문 identity | partial/full, same fill duplicate, cumulative/unit, out-of-order, cancel/amend/late parent, order number 날짜 재사용 | 이중 qty/cost 없음. owner/parent/terminal 불명 격리. 실제 fill과 market trade 혼동 없음 |
| 잔고 | 한 시장 성공, duplicate symbol, invalid qty, manual/credit, zero qty, missing open orders, `04` 단독 | 전체 census/verified-flat 성공 위조 없음. `04/933/951` 신규 BUY capacity·예수금 전용 없음 |
| bootstrap | REST 시작/종료 중 여러 event, late 이전 event, KRX/NXT 응답 사이 fill, epoch 전환 | 비원자 snapshot에 blind replay·이중 반영 없음. dirty/기존 복구, 무한 대기 없음 |
| durability | queue full, slow fsync, ENOSPC, corrupt tail/checkpoint, restart/crash before ack, writer 두 개 | 대체 상태 invalid, 원 주문 처리 계속, gap/cursor 복구. 기존 보호/SELL 경로 지연 없음 |
| 60초 편입/보유 | snapshot 59.9/60/60.1초, 45초 생략 후 입회 수요, 90초 대사와 coalescing, after-fill 중첩 | 기존 만료 기준 유지. demand 마감 전에 실제 갱신 또는 명시 defer, 새 stale 병목 없음 |
| 봉/history | 40봉 경계, partial/quiet, gap/drop, same timestamp seed, 늦은 revision, 재접속, session VWAP/OR, corporate adjustment | 부족분을 정상/0봉으로 채우지 않음. homogeneous scope·필수 prefix·해시 보존 |
| 비용 | absent/blank/zero/signed, repeated aggregate, multi-owner, settlement correction | raw 구분, unknown=null, 검증 없는 sum/delta 금지, 실제 비용/모델 비용 분리 |
| pipeline/장후 | main machine/compact caller·policy hash/date, BLOCK/RECHECK, exact stop/cost/owner gap | 정책·provider/주문 횟수 의미 보존. WS 가격 존재만으로 경제성 source-gap 승계 성공 없음 |
| retirement | 폐지 Widget·episode profile, Main/manual·역사 owner, rollback | 새 retired BUY/구독/수량 권한 0, 기존 custody/exit 및 사용자 초기 지정 보존 |

### 7.3 성능 재생의 분모와 제안 수용 기준

benchmark는 `src/tests/benchmarks/kiwoom_ws_substitution.py` 역할로 제안한다. 별도 production report CLI는 만들지 않는다. 실제 parser/selector/reducer·표적 consumer를 주입하고 fake HTTP/WS·frozen clock·실제 임시 파일 durability를 사용한다. production startup/auth/order는 import 또는 실행하지 않는다.

샘플 workload는 정상 연속·새로운 cold item·캐시 hit·forced request·mixed route/epoch·burst/gap/restart를 각각 재생한다. 예시 규모는 16 synthetic symbol, 10,000 quote 요청, 40봉 lookback, 100,000 market events와 별도 account partial/cancel fixtures다. live watch cap·실거래 표본 수의 변경이 아니다. baseline/candidate에 같은 event·cutoff·freshness·history·transport 지연을 주며 cache 상태도 동일하게 시작한다.

| 지표 | 수용 제안 / 보고 방식 |
| --- | --- |
| 실제 REST 전송 | 계측 known/unknown 분리. 적격 steady quote cohort **50% 이상 감소**, ready bar cohort **80% 이상 감소**를 시험 목표로 둔다. baseline physical HTTP>0 및 같은 valid request 분모가 전제다. 이 비율은 전체 장중/계좌 절감률이 아님 |
| 전체 요청 총량 | seed·gap·forced·required·auth·page/retry 모두 포함한 전체 replay에서도 증가하지 않아야 함. 준비 조회를 통계에서 숨기지 않음 |
| 필수 읽기 | `kt00001/11` sizing/submit, boot/reconnect/terminal/custody/독립 90초의 필요한 HTTP 100% 유지. 필수 읽기 보류/실패는 별도 결과 |
| guard/source | 설명되지 않는 order/guard/custody 결과 차이 0, unknown/stale를 성공으로 치환한 건 0. source selection 차이는 각 원천/시각과 함께 설명 |
| 지연 | 동일 상태 전환에서 p95 로컬 결정시간 **baseline 대비 +5% 이내**, 실제 WS packet→기존 체결/보호 dispatch에 새 blocking wait 0. 최소 5회 동일 조건의 중앙값/분산 및 worst stall을 기록. baseline이 측정 해상도 이하이면 백분율을 만들지 않고 절대 지연·측정 해상도를 보고하며 해당 성능 판정은 미확정으로 남김 |
| queue/journal | 정상 workload drop 0, burst 한도 초과는 명시 invalid/fallback. local sequence 연속을 broker 무누락 증명으로 사용하지 않음 |
| 자원 | 1,024-event queue/finite bar checkpoint 등 설계 한도에서 RSS·CPU·디스크 증가량을 보고. 기준선 대비 RSS +32MiB 이내를 초기 benchmark 목표로 두고 host·측정 조건을 같이 기록. 무제한 cache/queue 금지 |
| account 조회 | 60초 편입·보유 TTL과 90초 대사 수용 후 적격 idle snapshot HTTP가 실제 감소. 비율·새 poll 주기는 demand fixture와 자연 로그로 정하며 미리 고정하지 않음 |
| 운영 | 같은 활성 scope의 defer·coverage/source-gap·수신 lag·대사 mismatch·60초 flat proof 실패율이 악화되지 않음. 다른 릴리스/PID/일자를 하나의 개선률로 합치지 않음 |

위 수치는 제안 목표다. 부족한 실제 N에서 percentile·절감률을 확정하지 않는다. mock 성능은 실장중 savings 또는 수익이 아니며, natural sample이 없으면 기술 gate와 운영 미관측을 분리한다. 통과를 만들기 위해 TTL·sample floor·source reserve·보호 guard를 완화하지 않는다.

### 7.4 표적 검사와 리뷰 반복

기존 테스트를 우선 확장한다: `test_kiwoom_websocket.py`, `test_kiwoom_market_data_contract.py`, `test_kiwoom_quote_consistency.py`, `test_kiwoom_tick_history.py`, `test_kiwoom_orders.py`, `test_kiwoom_order_ref_snapshot.py`, `test_ai_market_snapshot.py`, `test_entry_snapshot_revalidation.py`, `test_micro_reversion_completed_bars.py`, `test_main_lifecycle_receipt_integration.py`, `test_kiwoom_read_request_control.py`, `test_kiwoom_episode_read_control.py`. 단계에 영향 없는 전체 suite를 매번 반복하지 않는다. account reducer/journal 테스트는 위 신규 ownership에 맞춰 필요한 독립 회귀만 추가한다.

각 단계는 **구현 → 자체 리뷰 → 발견 결함 수정 → 재리뷰 → 표적 pytest·compile → 성능 replay → 결과**로 닫는다. caller·silent drop·호환 schema·clock·authority를 diff 밖까지 확인한다. 자동화/wrapper가 바뀌는 단계에서만 `bash -n`·관련 계약 검사와 운영 문서/checklist를 같은 집합으로 갱신한다. source-only observe는 운용 진단이며 새 전략 shadow/alpha 비교를 열지 않는다.

## 8. 제출 병목·현재 OPEN 작업과의 합류

| 기존 owner / 계획 | 이번 계획과의 접점 | 분리할 변화 |
| --- | --- | --- |
| Main 제출 공백 P0-A/B | 기계 평가·recipe 근거→AI→기존 submit 경로 복구가 우선. quote/frame selector와 source/after-fill receipt만 공유 | 가격/전략 gate·CAUTION·remote guard 선택은 해당 계획의 diff/수용. HTTP 절감으로 제출 0 해결을 선언하지 않음 |
| `DirectFamilySourceRepairMainMechanisticEntry` | future exact WS 가격/주문/cost source를 필요한 attempt/owner에 연결 | 새 BLOCK/RECHECK 승격 정책 자동 생성 없음. 가격만으로 operating paired 경제성 결손 닫지 않음 |
| `DirectFamilySourceRepairCompactAuxiliary` | WS price source와 exact fill/fee를 확보한 scope의 source lineage | 정확 stop/plan/portfolio/cost 결손을 모델 값으로 채우지 않음 |
| `DirectFamilySourceRepairEntrySplit` / probe continuation | native `00` fill/parent/partial fact 공급 | continuation 수량·취소/정정 owner를 account reducer로 재작성하지 않음 |
| Doosan 및 제주/HPSP/알테오젠/주성 전환 계획 | fixed-watch의 60초 native flat census·source/퇴역 owner guards를 소비 테스트에 포함 | 새 fixed-watch 활성화·cap 상향·초기 정책 추가 경제성 proof 없음 |
| 9/28 read cadence/reuse 및 9/16 health 계획 | **현재 구현된** 공통 health, 정확 source reuse, request reserve를 재사용 | 과거 제안의 Widget/retired institutional/다중 scanner runtime을 복원하지 않음 |

실행 owner는 [당일 checklist](../checklists/2026-10-06-stage2-todo-checklist.md)가 소유한다. 구현 지시 후 기존 ID를 먼저 조회하고, 새 코드 작업이 필요할 때 `KiwoomWsSourceReplacementImplementation` 하나를 제안 owner로 등록한다. P0~P6은 하위 기술 묶음이며 별도 중복 OPEN/외부 일정으로 자동 생성하지 않는다. 등록할 Due/Slot/TimeWindow/Track·scope·Acceptance와 기존 Main/compact 수용 연결을 실제 작업일에 정한다.

## 9. 배포·활성화·rollback과 종료 조건

1. 현재 선택 release/실제 PID/installed consumer와 dirty 파일을 다시 고정하고 단계별 테스트가 통과한 구체 diff를 배포 대상으로 만든다. unrelated retirement/정책 변경을 원치 않게 묶지 않는다. 사용자가 통합 배포를 지정하면 그 실제 작업본 전체 gate를 별도로 닫는다.
2. 초기 코드의 source replacement 기본은 기존 REST 경로다. `00` raw field 보존의 호환 확장과 실제 대체 활성화를 구분한다. `04` 등록/새 market type은 명시된 active source scope에서만 실행한다. 이 문서로 수동 env/lock/REG를 바꾸지 않는다.
3. 단계별 선택 상태를 versioned activation receipt로 기록한다. 예시 mode는 quote/candle `rest|ws_when_ready`, account `off|capture|verified_context`, cost `capture|broker_reconciled_exact`, breadth `rest|ws_when_ready`다. 현행 consumer의 설정/검증 owner를 재사용하며 기능별 새 환경변수를 무제한 추가하지 않는다.
4. 계좌 capture는 source-only 상태에서 기존 poll을 유지한다. 실제 quote/bar/account substitution은 한 stage·한 scope에 순차 적용하고, Main 제출 경로 수리와 동시에 같은 조작점의 canary를 켜지 않는다. 다른 stage의 병행은 scope/rollout/rollback 분리가 확인된 경우에만 허용한다.
5. 배포·재기동이 허용된 실행 지시에서 불변 release를 선택하고 Main을 기존 `ubuntu` launcher/tmux owner로 기동한다. root 봇·중복 PID를 만들지 않는다. selector→PID cwd/commit→mode/source hash→직접 consumer receipt를 확인한다. 선택됨을 소비됨/절감됨/수익으로 표현하지 않는다.
6. 자연 검증은 구독 ACK 또는 local registry만으로 끝내지 않는다. 해당 type의 실제 packet→durable/route/epoch→selector→원 decision/holding context→required REST 복구를 연결한다. 표본 없으면 `not_observed`; 이미 끝낸 코드 검토를 계속 반복하지 않는다.
7. journal drop/지연·clock/scope 오류·qty/cost 중복·guard 결과 불명 변경·60초 flat proof 신규 실패·동일 stage conflict·보호/SELL 지연이면 **영향 scope의 대체만** 기존 REST에 복귀한다. 기존 source-gap도 baseline REST에서 해결되지 않으면 그 결손을 유지한다. 수수료·tax raw가 없는 이유로 전체 quote/bar를 되돌리지 않는다.
8. rollback은 reader를 되돌리는 절차이며 주문 DB/실제 수량/이미 생성된 journal/정책 hash를 삭제·역산하지 않는다. 새 mode가 이전 코드에 없을 때의 안전한 rest default와 version skew를 테스트한다. journal은 schema version을 보존하며 dual writer를 금지한다. code rollback이 retired Widget/episode BUY/timer를 복원하지 않는지 검증한다.
9. 장후 원천 consumer가 바뀌면 기존 Main/compact publisher의 exact source_date·code/kernel/source hash와 incumbent 정책을 보존한다. 오늘 정책 또는 이미 생성된 결과를 몰래 재발행하지 않는다. 별도로 실행하는 affected source/label generation은 해당 장후 owner와 strict/controller/finalization handoff로 종결한다. 불필요한 전체 장후 재생을 요구하지 않는다.

최종 결과표는 단계별 **code_gate / benchmark / release_selected / pid_consumed / natural_source / natural_savings / terminal / actual_cost / policy_or_profit_effect**를 구분한다. 의미 결손이 있는 비용·다른 route는 그 부분만 gap/rest-retained로 남긴다. 이 계획의 성공은 새로운 전략 수익 승인이나 거래소 비용 명세의 임의 확정이 아니다.

## 10. 계획 리뷰와 이번 검증

자체 검토에서 다음 사항을 보완했다.

- 45초 조회를 단순 삭제하면 fixed-watch 60초 proof가 막히는 문제를 consumer 수요·마감 planner와 native REST census 유지로 처리했다.
- planner에 등록되지 않은 consumer나 deadline 미준수 scope에는 기존 45초 갱신을 유지하며, 새로운 첫 입회 수요도 stale로 막히지 않는지 검사하도록 했다.
- 이미 존재하는 `_AL` 완성봉·episode selector를 새로 구현하거나 plain KRX/`_NX` 입력을 `_AL`로 바꾸지 않도록 Main 정확 item gate를 넣었다.
- `00/04` projection bootstrap의 비원자 REST overlap·late event·수신순서/경제순서 차이와 partial/aggregate 중복을 포함했다.
- async queue enqueue/로컬 sequence를 durable/broker 무누락 증명으로 사용하지 않으며, 신규 journal 때문에 기존 보호·실제 체결 처리가 기다리지 않게 했다.
- 비용은 원천 수집과 exact attribution을 분리하고 official 의미 결손이 다른 WS 대체와 초기 정책 지정을 차단하지 않도록 했다.
- 이미 적용된 source-only capacity 재사용, 미실행 legacy API, 준비/복구 HTTP를 절감률에 중복 반영하지 않도록 했다.

문서 링크·API/owner 범위·제안/현재 구현·authority·source date·retirement 경계를 재검토했다. 검증 결과는 다음과 같다.

- 문서 링크 25개 중 local 22개와 기존 표적 테스트 파일 12개의 존재를 확인했다. local link 결손·새 문서 trailing whitespace·code fence 불균형은 0이다. 새 문서의 `git diff --no-index --check` 공백 진단도 0이며, exit 1은 `/dev/null`과 새 파일의 차이에 따른 것이다.
- print-only backlog parser는 exit 0, 당시 task 27개다. 이 계획이 실행 task로 파싱된 건은 0이며, 새 OPEN/외부 일정은 생성하지 않았다.
- 전체 작업트리의 `git diff --check`는 exit 2다. 별도 dirty 변경인 `low_price_two_leg_expanded_candidate_research.py`, `low_price_two_leg_tuning.py`, `test_low_price_two_leg.py`, low-price `policy_runtime.py`·`preflight.py`·`profiles.py`의 공백 오류를 보고했다. 이번 계획 파일의 오류가 아니며 다른 작업본을 수정하지 않았다. 계획 문서 검증 통과를 전체 작업트리 배포 gate 통과로 표현하지 않는다.
- 검증 evidence는 `tmp/kiwoom-ws-substitution-plan-20261006/document-validation.json`, `backlog-print.txt`, `workspace-diff-check.txt`다. proposal이 canonical 계획 owner이며 tmp는 검증 영수증이다.

이 문서만 작성했으므로 pytest/benchmark·broker/provider 호출·구독 변경·배포·재기동·장후 재생은 이번 작업에서 실행하지 않았다. 실제 성능·WS 비용 귀속·자연 수신의 완전성은 구현 이후 단계별 수용이다.

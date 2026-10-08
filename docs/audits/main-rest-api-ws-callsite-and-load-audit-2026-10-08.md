# 전체 키움 API 호출지점·WS 부하 읽기 전용 조사 — 2026-10-08

## 1. 결론과 증거 범위

우선 절감 대상은 Main의 중복 분봉·체결이력·호가 준비와 같은 평가 내 반복 조회다. 기존 WS를 정확한 소비 계약으로 재사용한다. 전시장 발굴·과거 이력·투자자 집계·계좌/주문/인증은 각각 REST 역할이 남는다. **전체 실제 HTTP 호출량과 절감률은 현재 로그만으로 확정할 수 없다.** 전송 전 URL 준비 로그, shared gate의 admission, wrapper 호출, 실제 HTTP attempt를 구분했다.

사용자 지시대로 `kt00011`에 한정하지 않고 전체 소스를 검색했다. episode는 삭제 예정 부하/잔여 custody로 분류하며 새 WS 전환 투자를 하지 않는다. 후속 설계·단계·검증은 [REST→WS 절감 계획](../proposals/main-rest-api-ws-substitution-and-load-reduction-plan-2026-10-08.md)이 소유한다.

| 점검 범위 | 결과/한계 |
| --- | --- |
| 저장소 Python | tests 및 data/logs/tmp/models를 제외한 669파일 AST 검사, parse error0. API literal 검색과 물리 전송/positional·keyword·상수 alias/callback 참조를 대조 |
| API 목록 | REST/OAuth 46종; endpoint 지정86지점; 공통 wrapper 직접 호출266곳 + callback/함수 참조24곳. 정적 개수이며 활성/실제 전송 건수 아님 |
| 물리 HTTP 코드 | 11곳. 공통 유틸리티2, Main account/order의 최초·인증재시도2, episode gateway4, 연구/history collector3 |
| 비Python/별도 경로 | deploy/analysis 및 root shell/Python에서 Kiwoom host/path/api-id/공통 transport 호출 문자열 검색. 추가 직접 키움 wire 지점은 발견하지 못함. 동적 런타임 reachability 전수 증명은 아님 |
| 추가 HTTP 구분 | `get_top_marketcap_stocks`의 Naver, SignalRadar의 FDR, AI provider/Telegram/ECOS 등은 키움 호출량 분모에서 제외. WS callback 내 외부 I/O 비용은 성능 범위에 포함 |
| 정적 기록 | [위치 TSV](main-rest-ws-callsite-inventory-2026-10-08.tsv)는 모든 endpoint와 공통 wrapper 호출/참조를 행별 보존. [AST 결과](../../data/report/main_rest_ws_audit/2026-10-08/read-only-1031-1038/static-inventory.json)는 파일 hash/공식 API metadata/transport를 포함 |
| 재현/보존 | [조사 코드](../../data/report/main_rest_ws_audit/2026-10-08/read-only-1031-1038/inventory.py), [manifest](../../data/report/main_rest_ws_audit/2026-10-08/read-only-1031-1038/manifest.json). 프로덕션 모듈 import/실행 없이 AST·파일·프로세스·기존 로그만 조회 |

정적 목록은 통신 요청/응답을 전수 검증한 완전한 프로토콜 적합성 인증이 아니다. generic transport의 dynamic API 값, caller가 주입한 callback, OFF/퇴역/연구 경로의 도달 가능성은 명시적으로 구분한다. 동일 계좌/토큰 여부도 프로세스 이름만으로 단정하지 않는다. 계좌·인증정보 원문을 수집하지 않았다.

## 2. 기준 release와 조사 중 변경

- 오류 및 자연 부하 표본: Main PID `70105`, start ticks `613915`, release `main-loop-latency-20261008-v4`, commit `8bcf4f205d55f66a27a1a6875244133be38ce0fc`. `/proc/70105/cwd`, selector, WS producer, 성능 영수증을 대조했다.
- 별도 작업으로 10:40:58 KST에 Main PID `76094`, start ticks `674250`, release `main-loop-latency-20261008-v5`, commit `aed0ffcaf0bbce32fe84fab15a77ea36953f7202`로 변경됐다. 이 조사는 재기동하지 않았다. 이전 부하를 새 PID의 개선 성과로 사용하지 않는다.
- static inventory 최종 기준은 v5 및 그 시점 workspace다. 조사 핵심 `kiwoom_utils`, `kiwoom_orders`, `kiwoom_websocket`, `sniper_state_handlers`, `signal_radar`는 [v4/v5 hash 대조](../../data/report/main_rest_ws_audit/2026-10-08/read-only-1031-1038/release-source-comparison.json)가 모두 일치했다. 보조 연구 등 다른 작업의 dirty 변경은 보존했다.
- 초기 10:34에는 episode PID50309/55081, 이후 census에는 PID50309/74710이 있었다. 실행 인자는 별도 고정 release의 한화오션/삼성중공업/에스디바이오센서 profile 및6초 interval을 가리킨다. [후속 process census](../../data/report/main_rest_ws_audit/2026-10-08/read-only-1031-1038/process-census.json)의 episode cwd 읽기는 PermissionError였다. 각 polling당 HTTP 수, 선택 WS/REST mode와 같은 토큰 공유의 실제 상태는 이 증거로 확정하지 않는다.

## 3. 공식 원천 확인

upstream `953e5dbff123f437ab4d11a78a95191a685eb51f`, retrieval `2026-10-08T10:34:31+09:00`. [공식 spec](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/blob/953e5dbff123f437ab4d11a78a95191a685eb51f/kiwoom/_data/kiwoom_api_spec.json), [REST client](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/blob/953e5dbff123f437ab4d11a78a95191a685eb51f/kiwoom/core/client.py), [WS control packets](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/blob/953e5dbff123f437ab4d11a78a95191a685eb51f/kiwoom/realtime/packets.py) 및 [공식 한도](https://openapi.kiwoom.com/intro)를 확인했다. 전체 검사 경로/hash/미해결 차이는 [reference receipt](../../data/report/main_rest_ws_audit/2026-10-08/read-only-1031-1038/official-reference.json)에 있다.

국내 조회/주문 각각5회/초, WS 계좌·token별1세션/200종목이다. 한도를 CPU 처리용량이나 순간 메시지 throughput으로 해석하지 않는다. 현재 tree의 `kiwoom_docs` 부재, SDK/Postman envelope 차이, `04/951`의 불명확한 의미 및 일부0w 금액 단위 설명 결손은 구현 시 공식 확인 항목이다. 미확인 FID를 예수금으로 바꾸지 않는다. 브로커 확인을 위한 인증·조회·주문 API나 샘플은 실행하지 않았다.

## 4. 전체 API 대조표

아래 개수는 API를 명시한 정적 지점 수다. 실제 호출/활성 family 수가 아니다. 구체적인 모든 path·line·enclosing function·호출 및 callback 참조는 TSV를 따른다. 퇴역/삭제 예정 코드도 누락하지 않고 포함했다.

| API | 공식 기능 | endpoint 지정 지점 수 | 대표 producer | 판단 |
| --- | --- | ---: | --- | --- |
| `au10001` | 접근토큰 발급 | 1 | [kiwoom_utils.py:760](../../src/utils/kiwoom_utils.py) `_request_new_kiwoom_token` | REST 유지; token cache/정식 갱신 |
| `ka00198` | 실시간종목조회순위 | 2 | [kiwoom_utils.py:2718](../../src/utils/kiwoom_utils.py) `get_realtime_hot_stocks_ka00198` | 전시장 발굴 REST 유지; 감시종목 WS로 모집단 축소 금지 |
| `ka10001` | 주식기본정보요청 | 3 | [kiwoom_utils.py:2327](../../src/utils/kiwoom_utils.py) `get_basic_info_ka10001` | 현재가 부분만 0B; 정적 metadata REST 유지 |
| `ka10003` | 체결정보요청 | 1 | [kiwoom_utils.py:4564](../../src/utils/kiwoom_utils.py) `get_tick_history_ka10003` | 0B ordered tape; 충분한 history/정확 sign일 때 부분 전환 |
| `ka10004` | 주식호가요청 | 1 | [kiwoom_utils.py:3769](../../src/utils/kiwoom_utils.py) `get_stock_orderbook_ka10004` | 0D 부분 전환; 실행 직전 REST 비교는 별도 유지 |
| `ka10005` | 주식일주월시분요청 | 1 | [kiwoom_utils.py:2779](../../src/utils/kiwoom_utils.py) `get_daily_data_ka10005_df` | 과거/수정주가 REST 유지; 일자별 중복 읽기 절감 |
| `ka10013` | 신용매매동향요청 | 1 | [kiwoom_utils.py:2951](../../src/utils/kiwoom_utils.py) `get_margin_daily_ka10013_df` | REST 집계 유지; 0F/0w와 의미 다름 |
| `ka10016` | 신고저가요청 | 1 | [kiwoom_utils.py:3619](../../src/utils/kiwoom_utils.py) `get_new_high_ka10016` | 전시장 발굴 REST 유지; 감시종목 WS로 모집단 축소 금지 |
| `ka10018` | 고저가근접요청 | 1 | [kiwoom_utils.py:3550](../../src/utils/kiwoom_utils.py) `get_high_price_proximity_ka10018` | 전시장 발굴 REST 유지; 감시종목 WS로 모집단 축소 금지 |
| `ka10019` | 가격급등락요청 | 1 | [kiwoom_utils.py:3492](../../src/utils/kiwoom_utils.py) `get_price_jump_ka10019` | 전시장 발굴 REST 유지; 감시종목 WS로 모집단 축소 금지 |
| `ka10021` | 호가잔량급증요청 | 2 | [kiwoom_utils.py:3935](../../src/utils/kiwoom_utils.py) `get_bid_balance_surge_ka10021` | 전시장 발굴 REST 유지; 감시종목 WS로 모집단 축소 금지 |
| `ka10023` | 거래량급증요청 | 2 | [kiwoom_utils.py:4076](../../src/utils/kiwoom_utils.py) `get_zero_base_volume_surge_ka10023` | 전시장 발굴 REST 유지; 감시종목 WS로 모집단 축소 금지 |
| `ka10027` | 전일대비등락률상위요청 | 1 | [kiwoom_utils.py:3039](../../src/utils/kiwoom_utils.py) `get_top_fluctuation_ka10027` | 전시장 발굴 REST 유지; 감시종목 WS로 모집단 축소 금지 |
| `ka10028` | 시가대비등락률요청 | 1 | [kiwoom_utils.py:3171](../../src/utils/kiwoom_utils.py) `get_top_open_fluctuation_ka10028` | 전시장 발굴 REST 유지; 감시종목 WS로 모집단 축소 금지 |
| `ka10032` | 거래대금상위요청 | 1 | [kiwoom_utils.py:3676](../../src/utils/kiwoom_utils.py) `get_value_top_ka10032` | 전시장 발굴 REST 유지; 감시종목 WS로 모집단 축소 금지 |
| `ka10046` | 체결강도추이시간별요청 | 1 | [kiwoom_utils.py:4399](../../src/utils/kiwoom_utils.py) `check_execution_strength_ka10046` | 단일 0B/228로 시간별 집계 대체 금지 |
| `ka10054` | 변동성완화장치발동종목요청 | 1 | [kiwoom_utils.py:3996](../../src/utils/kiwoom_utils.py) `get_vi_triggered_ka10054` | 전시장 REST 유지; 1h는 향후 등록범위 내 부분 후보 |
| `ka10059` | 종목별투자자기관별요청 | 1 | [kiwoom_utils.py:2863](../../src/utils/kiwoom_utils.py) `get_investor_daily_ka10059_df` | REST 집계 유지; 0F/0w와 의미 다름 |
| `ka10061` | 종목별투자자기관별합계요청 | 1 | [kiwoom_utils.py:5947](../../src/utils/kiwoom_utils.py) `get_investor_period_total_ka10061` | REST 집계 유지; 0F/0w와 의미 다름 |
| `ka10063` | 장중투자자별매매요청 | 1 | [kiwoom_utils.py:6000](../../src/utils/kiwoom_utils.py) `get_intraday_investor_trade_ka10063` | REST 집계 유지; 0F/0w와 의미 다름 |
| `ka10064` | 장중투자자별매매차트요청 | 1 | [kiwoom_utils.py:6051](../../src/utils/kiwoom_utils.py) `get_intraday_investor_chart_ka10064` | REST 집계 유지; 0F/0w와 의미 다름 |
| `ka10066` | 장마감후투자자별매매요청 | 1 | [kiwoom_utils.py:6093](../../src/utils/kiwoom_utils.py) `get_postclose_investor_trade_ka10066` | REST 집계 유지; 0F/0w와 의미 다름 |
| `ka10073` | 일자별종목별실현손익요청_기간 | 1 | [low_price_two_leg_tuning.py:400](../../src/engine/monitoring/low_price_two_leg_tuning.py) `load_realized_pnl_ka10073` | episode 실현손익 호출 제거 인계; Main 비용 consumer 확인 |
| `ka10075` | 미체결요청 | 3 | [kiwoom_utils.py:1821](../../src/utils/kiwoom_utils.py) `get_unfilled_order_snapshot_ka10075` | REST 대사 유지; 00/04는 증분·무효화 후보 |
| `ka10076` | 체결요청 | 1 | [kiwoom_utils.py:1785](../../src/utils/kiwoom_utils.py) `get_order_reference_snapshot_ka10076` | REST 대사 유지; 00/04는 증분·무효화 후보 |
| `ka10080` | 주식분봉차트조회요청 | 10 | [kiwoom_utils.py:5034](../../src/utils/kiwoom_utils.py) `get_minute_candles_ka10080_with_meta` | 0B 확정봉 + REST seed/gap; 우선 절감 후보 |
| `ka10081` | 주식일봉차트조회요청 | 1 | [kiwoom_utils.py:2505](../../src/utils/kiwoom_utils.py) `get_daily_ohlcv_ka10081_df` | 과거/수정주가 REST 유지; 일자별 중복 읽기 절감 |
| `ka10084` | 당일전일체결요청 | 1 | [kiwoom_utils.py:4904](../../src/utils/kiwoom_utils.py) `get_recent_signed_trades_ka10084` | 0B ordered tape; 충분한 history/정확 sign일 때 부분 전환 |
| `ka10099` | 종목정보 리스트 | 2 | [kiwoom_utils.py:2033](../../src/utils/kiwoom_utils.py) `get_nxt_enabled_codes_ka10099` | REST metadata; exact-date/거래가능시장 cache |
| `ka10100` | 종목정보 조회 | 1 | [kiwoom_utils.py:2599](../../src/utils/kiwoom_utils.py) `get_item_info_ka10100` | REST metadata; exact-date/거래가능시장 cache |
| `ka10101` | 업종코드 리스트 | 1 | [kiwoom_utils.py:1954](../../src/utils/kiwoom_utils.py) `get_industry_list_ka10101` | REST metadata; exact-date/거래가능시장 cache |
| `ka20003` | 전업종지수요청 | 1 | [market_panic_breadth_collector.py:1238](../../src/engine/market_panic_breadth_collector.py) `fetch_kiwoom_market_breadth` | 전업종 breadth REST 유지; 일부 지수 WS로 대체 금지 |
| `ka20005` | 업종분봉조회요청 | 1 | [kiwoom_utils.py:2649](../../src/utils/kiwoom_utils.py) `get_index_minute_candles_ka20005_with_meta` | 0J 집계는 후순위; 현재 REST 이력 유지 |
| `ka20006` | 업종일봉조회요청 | 2 | [kiwoom_utils.py:2620](../../src/utils/kiwoom_utils.py) `get_index_daily_ka20006` | 일봉 REST 유지; Radar 잘못된 fallback 수리 후보 |
| `ka90001` | 테마그룹별요청 | 2 | [kiwoom_utils.py:1985](../../src/utils/kiwoom_utils.py) `get_theme_group_list_ka90001` | REST metadata; exact-date/거래가능시장 cache |
| `ka90008` | 종목시간별프로그램매매추이요청 | 1 | [kiwoom_utils.py:4284](../../src/utils/kiwoom_utils.py) `check_program_buying_ka90008` | 기존 0w 우선 보완; 단위/당일/전일 분리 |
| `kt00001` | 예수금상세현황요청 | 1 | [kiwoom_orders.py:1242](../../src/engine/kiwoom_orders.py) `_get_deposit_real` | REST 유지; 00/04로 BUY capacity 대체 금지 |
| `kt00005` | 체결잔고요청 | 2 | [kiwoom_utils.py:856](../../src/utils/kiwoom_utils.py) `get_account_balance_kt00005` | REST 대사 유지; 00/04는 증분·무효화 후보 |
| `kt00007` | 계좌별주문체결내역상세요청 | 6 | [kiwoom_utils.py:1697](../../src/utils/kiwoom_utils.py) `get_order_reference_snapshot_kt00007` | REST 대사 유지; 00/04는 증분·무효화 후보 |
| `kt00008` | 계좌별익일결제예정내역요청 | 1 | [kiwoom_utils.py:1030](../../src/utils/kiwoom_utils.py) `get_account_execution_snapshot_kt00008` | REST 대사 유지; 00/04는 증분·무효화 후보 |
| `kt00011` | 증거금율별주문가능수량조회요청 | 1 | [kiwoom_utils.py:1100](../../src/utils/kiwoom_utils.py) `get_orderable_by_margin_kt00011` | REST 유지; 00/04로 BUY capacity 대체 금지 |
| `kt00018` | 계좌평가잔고내역요청 | 1 | [kiwoom_orders.py:1406](../../src/engine/kiwoom_orders.py) `get_my_inventory` | REST 대사 유지; 00/04는 증분·무효화 후보 |
| `kt10000` | 주식 매수주문 | 2 | [kiwoom_orders.py:2193](../../src/engine/kiwoom_orders.py) `send_buy_order_market` | 주문/취소 REST 유지; WS00은 receipt이며 전송 대체 아님 |
| `kt10001` | 주식 매도주문 | 8 | [kiwoom_orders.py:2416](../../src/engine/kiwoom_orders.py) `send_sell_order_market` | 주문/취소 REST 유지; WS00은 receipt이며 전송 대체 아님 |
| `kt10002` | 주식 정정주문 | 1 | [broker.py:993](../../src/trading/order/adaptive_exit/broker.py) `amend_owned_sell` | 정정 REST; 현재 episode adapter 삭제/잔여 custody 인계 |
| `kt10003` | 주식 취소주문 | 8 | [kiwoom_orders.py:2556](../../src/engine/kiwoom_orders.py) `send_cancel_order` | 주문/취소 REST 유지; WS00은 receipt이며 전송 대체 아님 |

## 5. 물리 전송과 주요 소비 경로

| 물리 전송 owner | 코드 지점 | 호출/소비 경계 |
| --- | --- | --- |
| `kiwoom_utils` | `_request_new_kiwoom_token:760`, `_fetch_kiwoom_api_continuous_transport:5438` | token cache/auth, 전체 시장/계좌 helper, scanner/zero-base probe/Main prepare/관측/장후. 각 page·retry는 별도 attempt |
| `kiwoom_orders` | `_post_kiwoom_with_auth_retry:775,855` | Main deposit/inventory 및 BUY/SELL/cancel. account read gate와 order write는 분리 |
| episode gateway4개 | low-price277, Samsung morning207/midday189/afternoon189 | `self.session.post`; 계좌·chart·order/adaptive adapter. 삭제 계획으로 인계, 잔여 custody 전까지 안전 유지 |
| standalone research/backfill | `pure_market_kiwoom_backfill:404,579`, `low_price_two_leg_entry_spot_research:403` | injected `post`, source-only shared admission/page bounds. episode 전용 것은 삭제, Main/공통 과거 원천은 유지 |

공통 transport만 바꾸면 위 다른 직접 경로를 놓친다. 반대로 `requests.get` 문자열 검색만으로 dict/SQLAlchemy `session.get`까지 HTTP로 세면 과대 집계된다. 이 오탐을 제거하고 OAuth와 positional `ka10001`, episode의 constant alias `ka10075`, adaptive `_write`의 `kt10002`를 보완했다.

주요 Main 경로는 다음과 같다.

- `kiwoom_sniper_v2`의 zero-base/scanner panel → `scalping_scanner`/공통 helper → candidate probe/chart → WS lease/편입이다. 전시장 REST 발견과 편입 후 WS 갱신을 분리한다.
- `sniper_state_handlers`의 async prepare/refresh, 재평가, 보유·청산, scale-in → tick/candle/context/BBO/account helper다. 그 안의 `_pre_submit_refresh_rest_orderbook_snapshot`은 실행 직전 독립 REST 검사다.
- `build_realtime_analysis_context`는 strength/program/investor/tape/minute/daily를 수집한다. 이미 준비한 frozen view와 중복될 수 있어 consumer별 동일 입력 재사용 후보이며, helper 호출마다 물리 HTTP라고 세지 않는다.
- `SniperRadar._on_realtime_tick` → 조건 충족 시 `get_market_regime` → FDR/키움 fallback은 동기 EventBus callback 경로다. `find_supernova_targets`의 프로그램/강도 조회는 다른 scanner 경로다. 이를 매 tick에 모든 REST를 호출한다고 잘못 합치지 않는다.
- `sniper_sync`의 account reconciliation/broker snapshot과 startup/reconnect/holding terminal은 안전 consumer다. Main 상수상45초 broker snapshot/90초 account reconciliation, deposit loop cache·정확 capacity cache가 존재한다. 실제 호출 빈도는 추가 guard/동시 요청·cache/회복 경로에 따라 달라진다.
- pruned BBO collector의 `self._fetch_quote` 및 market opportunity census의 injected fetch는 `ka10004`/`ka10027` 참조로 추적했다. 전시장 미편입 후보 관측을 WS 등록 범위로 축소하지 않는다.

## 6. 실제 REST 관측과 오류 사례

고정 로그 창은 `[2026-10-08 10:31:00, 10:38:00) KST`다. [runtime summary](../../data/report/main_rest_ws_audit/2026-10-08/read-only-1031-1038/runtime-summary.json)와 [capacity rows](../../data/report/main_rest_ws_audit/2026-10-08/read-only-1031-1038/capacity-rows.json)에 원 증거 위치/hash와 정제값을 보존했다.

| 관측 | 결과 | 해석 |
| --- | ---: | --- |
| URL 준비 로그 | chart69, acnt54, mrkcond45, rkinfo32, stkinfo31, sect3 | 합234; PID/API/page/retry 전체 전송 계수가 없어 endpoint별 HTTP 수로 쓰지 않음 |
| Main capacity prefetch | logical16/HTTP16, 성공14/실패2 | PID70105 한정; 실패도 물리 전송에 포함 |
| Main capacity 관측 | logical15/HTTP0, exact reuse10, scope_changed4, expired1 | 관측15회를 REST15회로 계산하면 잘못된 절감 추정 |
| timeout 로그 | 중복 출력4건 → 동일 시각/PID/API의 실제 사례2건 | 10:31:47, 10:33:36; 모두034020 prefetch |
| 전체 API 전송 누계 | unknown | 오류 로그/429 부재 또는 gate의 last_admission으로 정상 전송량을 역산할 수 없음 |

10:31:47 사례는 code034020, price76,700, admission wait3.044ms, HTTP1회, result `http_failed`, response receive/valid capacity 없음이다. 시작→완료 약198.8ms다. source-only의 connect/read timeout은 각각150ms/attempt1이며, 네트워크/서버/스케줄 지연의 어느 부분이 초과 원인인지는 미확정이다. rate-limit/브로커 주문거부/체결 실패로 재분류하지 않는다. 같은 가격의 후속 `BLOCK` 관측은 cache-only `scope_changed`였으며 새 HTTP를 보내지 않았다. correlation ID가 다른 관측을 동일 거래 attempt 또는 타임아웃 때문에 BLOCK된 것으로 단정하지 않는다.

## 7. WS 전체 경로·부하 점검

`socket recv → JSON/REAL parse → exact item/type state + raw0B/0D → pending latest state → EventBus/Main → dashboard/shared snapshot + raw writer`를 따라 점검했다. 로그인 후 group2 `00`, group3 `0s`; 기본 시장 구독은 `0B/0D/0w/0F`, source-only exact probe/관측은0B/0D를 요구한다. 이번 검사에서04 등록/전용 처리와 REG/REMOVE ACK 귀속 ledger는 확인하지 못했다. 현재 producer도 `local_sent_registry_not_broker_ack`라고 명시한다.

| 항목 | PID70105 표본 | 결론/한계 |
| --- | --- | --- |
| 관측창 | 10:37:34.396~10:38:04.567, 30.17초/7snapshot | 고정한 v4 한 세대, peak/일평균 아님 |
| WS socket | `:10000` ESTAB1개 | snapshot 시점 관측 socket이며 token 전체 연결의 서버측 census 아님 |
| 로컬 등록 | exact items22~25, 설정 cap56 | 주기별 lease 변화; stock cache80행과 동시 등록 수는 다름 |
| 관측 targets | 20items, 0B+0D 수신완료18 | `036930_NX/403870_NX`는 첫 수신 미관측; ACK/eligible/session 확인 필요 |
| 해당 target 수신 증가 | 0B970/0D1541 → 32.15/51.07개/초 | 합83.22; 전체 frame/0w/0F/control traffic 수 아님 |
| TCP 수신 증가 | 3,521,779 bytes → 116,721 bytes/sec | wire/TLS 포함; REST bytes와 분리 |
| Main CPU/RSS | CPU92.83% 한 코어, RSS1,525,572→1,541,956KiB | WS 전용 CPU 아님; 같은 호스트의 다른 작업 경합 포함 |
| dashboard snapshot 임계구역 | 60.55~86.45ms/7개 | lock 획득 후 전체 frozen view 복사 구간; 짧은 helper lock 통계와 다른 계측 |
| 10:37:30 성능 영수증 | warm87회 p95=5.793s/p99=9.125s, >5s12회 | 기동 이후 누적; 짧은30초 창에 한정된 통계 아님 |
| WS lock 성능 영수증 | 최근4096표본 p99 wait87.42ms/hold23.07ms | 전체19,159관측 중 retained tail; raw callback 시간과 구별 |
| 7분 REG 시도 | Main boot1, 관측2, zero-base probe96 | 구독96종목 상시 유지/ACK96건으로 해석 금지 |

[원 sampling](../../data/report/main_rest_ws_audit/2026-10-08/read-only-1031-1038/ws-load-samples.json)을 보존했다. current cap은 공식200보다 낮지만 증가 근거가 아니다. 기동·재접속·일중 peak·세션 전환에서 전체 message rate, item×type 동시 수, queue age, raw→마지막 소비 지연과 worker별 CPU는 아직 미확정이다. 추가 socket이나 200종목 확대를 제안하지 않는다.

raw collector는 별도 bounded queue/writer/drop 계측이 있다. 후속 10:41:46 [collector snapshot](../../data/report/main_rest_ws_audit/2026-10-08/read-only-1031-1038/collector-snapshot.json)은 새 sequence epoch `1791423676514010095`, v5 기동 이후의 별도 표본이다. observation/depth high-water 각11, writer high-water15, 해당 snapshot drop/error0, callback p99 0B0.136ms/0D0.880ms를 기록했다. 이를 v4의 무손실 증명이나 전체 WS 잠금/대기 정상 증거로 합치지 않는다. epoch와 표본 생성 시각이 다르며, 전체 state queue/pending tick lag의 정상 여부는 이 artifact로 닫을 수 없다.

## 8. 발견사항과 다음 조치

| 발견사항 | owner / 다음 조치 | 종료 시험 |
| --- | --- | --- |
| 전체 HTTP 전송 계수 결손 | RW0; 전체11지점을 생존/삭제/미확인으로 분류하고 생존 transport에 bounded attempt 계측 연결 | 정상/timeout/retry/page/follower/defer의 단일 계수와 PID별 합계 reconciliation |
| SignalRadar `ka20006` wire 불일치 | RW1; `/mrkcond + upjong_cd`를 공식 `/chart + inds_cd/base_dt` 및 response 계약과 대조해 수리 | 공식 보존 fixture와 fallback 실패 경로; 실제 fallback 호출 빈도 별도 관측 |
| 반복 candle/tape/BBO/context | RW2/RW3; 같은 frozen source 공유, exact0B/0D/완성봉으로 적격 consumer만 전환 | 입력/판정/원시각 parity, 불충분 이력/epoch/route 차단, actual HTTP 감소 |
| WS 원천 존재만으로 수급 유효성 보증 불가 | RW4; 0w age/route/원천 단위·전일 fallback 소비 검증 | stale/mixed-route/금액 배율/동일0값/단위 unknown 반례 |
| dashboard 전체복사와 tick→동기 외부 I/O | 기존 latency owner와 RW5 | 전체 history/수정 격리 보존, lock 및 마지막 소비 지연·queue 계측 |
| 등록 전송과 수신/ACK의 차이 | RW5a/RW5b; per-item/type/epoch 귀속 및 lease/refcount 검증 | REG 거부/지연 ACK/reconnect/REMOVE 후 late packet/동일 item 복수 owner |
| episode 및 전용 Main writer 비용 | 제거 계획 owner; 실제 남는 Main caller와 custody 확인 후 종료 | 프로세스·예약·전용 원천 호출0 + Main 공통 source/보유 callback 보존 |

기존 source single-flight/3초 same-minute chart cache, 1초 tick/strength·3초 minute·30초 daily·60초 investor·20초 program cache는 이미 있다. 따라서 새 cache 추가 자체를 해결로 간주하지 않는다. 캐시를 늘려 원천 freshness를 연장하거나, pre-submit independent REST 검사를 제거하거나, source-only 한도·retry를 확대하는 변경은 이 계획의 절감안이 아니다.

## 9. 문서 리뷰·검증

초기 목록의 HTTP 문자열 오탐과 generic transport의 진단 literal 오분류를 제거했다. positional/constant alias/`_write` 경로와 callback 참조를 보완하고 API46종 및 실제 transport11곳을 재대조했다. timeout mirror 중복, v4/v5 세대 분리, episode 환경/cwd 읽기 제한, source subset과 전체 wire 부하 차이를 명시했다. 변경은 계획·조사·CSV 및 기존 checklist 인계 문구에 한정한다.

문서 검증: 계획/조사 로컬 링크71개 존재, CSV376행(API46종/endpoint86/공통 wrapper 호출266/함수 참조24), 기존 current OPEN owner1개 및 증거 manifest10파일 hash를 확인했다. print-only parser는 exit0/21개 작업을 반환했고 해당 owner의 현재 checklist 귀속1개를 확인했다. `git diff --check`를 통과했다. runtime/trading pytest, provider·broker 호출, 보고서 재생성, 배포·재기동, 외부 sync는 문서-only 범위이므로 실행하지 않았다. 전송량 계측·source adapter 구현·자연 절감 수용 및 발견된 fallback 결함 수정은 후속 단계다.

## 10. 절감계획 추가 리뷰 — 2026-10-08

사용자의 계획 리뷰 요청에 따라 문서만 수정했다. 위 §2/§6/§7의 부하/PID 영수증은 원 관측 시점의 증거를 보존하며 이번 리뷰 시점의 현재 상태로 바꾸지 않는다. 10:57:16 KST 공식 `git ls-remote ... HEAD`는 기존 `953e5dbff123f437ab4d11a78a95191a685eb51f`와 일치했다. 같은 checkout의 `kiwoom/realtime/packets.py` REG/REMOVE 형태를 재확인했다. 공식 [commit](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/commit/953e5dbff123f437ab4d11a78a95191a685eb51f)과 최초 §3의 spec/core/Postman 영수증을 함께 사용했다. 향후 프로토콜 코드 변경은 착수 시 공식 reference gate를 다시 적용한다.

| 발견사항 | 확인 근거와 계획 보완 | 문서 종료 기준 |
| --- | --- | --- |
| WS 전환보다 readiness 검증이 뒤에 배치됨 | RW5를 source별 최소 검증 a와 관리 개선 b로 나누고 RW0+RW5a→RW2→이력 계약/이관→RW3 의존성을 명시 | 전체 구독관리/episode 제거 완료를 모든 Main 부분군의 선행 조건으로 만들지 않음 |
| 같은 release 전후 비교 요구가 코드 교체와 충돌 | baseline/treatment release/PID·변경 차이를 각각 기록, 유효 수요당/시간당 attempts와 source coverage·처리 비용 비교 | 입력량·정책·episode 삭제 차이를 WS 절감으로 오인하지 않음; 분모0/미확인은 null |
| 지수 helper 단순 재사용으로 20일 평균 불충족 | `signal_radar.py:get_market_regime`은 20행 소비, `kiwoom_utils.py:get_index_daily_ka20006`은 최신/5일 전 2값 반환 | 공식 이력 parser/유효20일·순서·배율 검증 및 기존 보수적 실패 동작 보존을 RW1에 명시 |
| API 단위 전환이 다른 소비 목적을 덮을 위험 | Main entry·holding/exit·scale-in·scanner/census·pre-submit별 필드/age/lookback/route/cutoff 계약 추가 | 준비 view를 다음 평가/submit으로 연장하지 않고 독립 최종 REST와 계좌 안전 유지 |
| 완성봉의 Main·KRX/NXT 지원을 과대 가정할 여지 | `shared_ws_snapshot.completed_bar_mode`은 episode만 허용, `micro_reversion/forward_collector` projection은 SOR 조건, `completed_bars`는 durable journal 기반 | Main 공통 설정/writer/reader 이관, 지원 route만 전환, watermark·세션 경계·미래 backfill 금지 |
| fallback·계측 분모의 종료 조건 부족 | worker timeout≠취소, follower 자체 deadline, 시작/terminal/inflight 대사, 미확인 caller와 관측 범위 명시 | admission·retry/page·source-only reserve 보존, 계측 자체 I/O/CPU 비용 포함 |
| ACK/sequence/cap 관측값을 운영 사실로 확대할 위험 | upstream REG builder에 임의 request ID 없음; 기존 local-sent registry와 로컬 sequence의 증명 범위 제한 | ACK 미귀속은 unknown, 유효 packet과 별도; cap56은 dated 관측값이며 실제 승인 설정 보존 |
| 퇴역 전용 계측 투자 및 호출목록 보존 결손 | 11 transport를 생존/삭제/미확인으로 분류, `.gitignore:80`의 `*.csv` 확인 | episode 전용 WS/계측 신설 제외; 같은 376행을 [TSV](main-rest-ws-callsite-inventory-2026-10-08.tsv)로 보존 |

TSV는 최초 CSV의 필드·행 순서·값을 그대로 옮긴 정적 snapshot이며 runtime reachability를 새로 입증하지 않는다. 원 CSV와 sealed manifest는 변경하지 않는다. `data/report` 상세 증거는 로컬 artifact이므로 Git/배포에 자동 포함되지 않는다. 인계 시 원 manifest와 10개 파일의 hash를 함께 확인하고 별도 보존한다. 새로운 코드/계측/프로토콜 구현과 자연 절감 수용은 여전히 RW0~RW6의 후속 작업이다.

재리뷰에서는 시장 source fallback을 계좌/capacity나 frozen cache-only observer에 확대하지 않도록 범위를 명시하고, 실패/미수신 수요를 절감 분모에서 누락하지 않도록 보완했다. 문서 검증은 계획/조사 로컬 링크73개, TSV376행과 원 CSV의 전 필드/행 순서 동일, API46종/endpoint86/공통 호출266/참조24 및 파일/행 위치 유효, TSV Git 제외 없음, 원 manifest10파일 hash 일치다. TSV SHA256은 `877140b2ae07a61875833631294b54f4eb1fdce48ae5fa59044b0ed50b413fb3`다. print-only parser exit0/21개 작업과 기존 current owner1개를 확인했고 `git diff --check` 및 새 문서 공백 검사를 통과했다. 다른 작업의 소스 변경은 건드리지 않았다. 문서-only이므로 runtime/trading pytest·실 API 호출·배포·재기동·외부 sync를 실행하지 않았다. 전체 실제 호출량·peak WS 부하·자연 절감률은 후속 계측 전까지 미확정이다.

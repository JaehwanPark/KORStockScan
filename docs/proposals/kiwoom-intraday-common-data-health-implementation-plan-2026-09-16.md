# 장중 키움 공통 데이터 판정·전수 소비·latency 중복작업 개선 계획

상태: **통합 전 설계 보존본 — 독립 실행계획 아님.** 현재 실행계획은 [공통 데이터 판정·미진입 기회비용 통합 구현계획](entry-opportunity-cost-full-population-tuning-implementation-plan-2026-09-17.md)이다. 아래 C0–C7은 통합본 U0–U12로 대사하며 두 문서를 별도 작업으로 합산하거나 이중 실행하지 않는다. 코드 구현·배포·runtime 적용 receipt가 아니다.

범위: 기존 장중 WS/REST 수집·정규화·소비 경로의 보완. **작업본에서 구현·리뷰·검증한 동일 코드 세대만 기존 managed release로 전달한다. 별도 장후 작업·collector·service·timer·cron·정책 family·DB·Python 모듈은 만들지 않는다.**

## 1. 최종 개선방향과 목표

**기존 공통 수신·정규화 지점에서 type·route별 사실과 공통 상태를 계산하고, 모든 장중 소비자가 같은 판정 데이터를 읽도록 한다.** 소비자마다 `last_ws_update_ts`나 현재 시각으로 신선도를 발명하지 않는다. 다만 호가 제출 안전, 실제 체결 기반 feature, micro 창과 broker reconciliation은 서로 다른 계약이므로 하나의 `fresh=true`로 합치지 않는다.

진입 개선은 두 가지다.

1. 체결 공백, 호가 노후화, 연결/등록 결손, 로컬 처리 지연을 혼동한 입력 판정·귀속을 수정한다.
2. 같은 원천을 반복 소비해도 달라지지 않는 평가·refresh·subscription repair를 합쳐, 새로운 유효 기회의 평가에 기존 예산을 사용한다.

기계 진입판정→compact AI 보조심사, numeric 가격, 최초 수량+leg, AVG_DOWN/PYRAMID, 위젯/episode와 holding/exit owner는 유지한다. 이 계획의 공통 판정기가 AI PASS, ENTER_NOW, 가격·수량 또는 실제 주문을 직접 생성하지 않는다.

### 1.1 단순한 체결 공백 기준

제안 초기값은 **공백 10초, 서로 다른 공백 episode 3회 반복**이다. 10초는 단순한 engineering 초기 제안값이지 전문가 공인 기준·경제적 최적값 또는 현재 적용값이 아니다. 호가/주문 안전 TTL을 10초로 변경하는 값도 아니다.

| 상태 | 판정 |
| --- | --- |
| `RECENT_TRADE` | 마지막 정상 `0B` 이후 10초 미만 |
| `QUIET_TAPE_OBSERVED` | 10초 이상이고 해당 scope의 관측 경로 정상성을 확인할 수 있음 |
| `REPEATED_QUIET_TAPE_OBSERVED` | 서로 다른 공백 episode가 3회에 도달 |
| `OBSERVATION_UNPROVEN` | 첫 체결 미수신, 등록/epoch/route 불명, 연결 이상, 로컬 drop 또는 관측 연속성 미입증 |

이 상태는 **로컬 관측 체결 공백**이다. WS LOGIN/PING이나 다른 종목의 체결만으로 해당 종목의 시장 무체결을 확정하지 않는다. 반복 공백도 저유동성의 관측 징후이지 실제 무체결·손실 또는 주문 미체결의 증명은 아니다. `trade_event_age_ms`와 `trade_receive_age_ms`를 함께 보존해 오래된 체결의 뒤늦은 전달을 구분한다. provider 시각 의미가 불명확하면 null/직접 사유로 남긴다.

**평가 3회·REST 조회 3회·promotion 3개·5분 내 retry 3회로 반복을 세지 않는다.** 같은 연속 공백은 수백 번 읽어도 한 번이다. 시간대별 세분화, 종목별 adaptive p99 또는 새 EV 승격 gate를 추가하지 않는다.

### 1.2 공통화가 바꾸지 않는 것

- `0D` freshness, crossed/nonpositive BBO, quote divergence, hard/protect/emergency, broker/account/order/quantity/cooldown과 승인 override는 기존 owner 계약을 유지한다.
- 6초 전 `0B`를 현재 공격적 매수체결·buy pressure·유효한 1초 micro 창으로 바꾸지 않는다.
- 오래된 last sale는 참고 mark일 수 있어도 현재 executable 가격이 아니다. 가격 owner는 기존 fresh bid/ask와 자신의 계약만 소비한다.
- 정상 관측 공백 자체를 `SOURCE_INVALID`로 세지 않는다. 그러나 stage에 필수인 현재 tape/feature가 불충분하면 기존 owner의 명시적 입력 부족/`RECHECK`/차단을 유지한다. guard 삭제나 무조건 중립 feature 대입으로 우회하지 않는다.
- quote와 tape의 서로 다른 갱신 빈도는 통신 latency가 아니다. 반대로 새 provider 체결이 오래 지연돼 도착한 것을 정상 공백으로 숨기지 않는다.
- 이번 요청은 계획 수립이다. 코드 수정·API 호출·env 변경·배포·재기동은 문서 작성 중 실행하지 않는다.

## 2. 소스 조사에서 확인한 개선 후보

아래는 소스상 경로 확인 결과다. runtime 발생량·경제적 영향은 별도 확인하며, 파일 존재를 현재 ON/PID 소비로 간주하지 않는다.

| 경로 | 확인점 | 개선 내용 |
| --- | --- | --- |
| `ai_market_snapshot.realtime_type_provenance` | type별 시각/route를 보존하지만 `_FRESH_MS=3000`을 여러 입력에 사용 | provenance 존재·동일성, 체결 활동, feature 유효시간을 분리 |
| AI snapshot preflight | current price/tape/BBO와 source-time skew가 연결됨 | 오래된 체결·fresh quote 조합을 전체 원천 손상으로 오인하는지 stage별 확인; 실제 missing/conflict 유지 |
| scanner normalize/fresh helper | `0B`, last trade/history와 aggregate 시각으로 freshness를 따로 계산 | 공통 필드 소비; history/aggregate로 exact receipt를 대체하지 않음 |
| pre-AI refresh/freshness helper | aggregate `last_ws_update_ts` 기반 3초 판정이 존재 | 새 quote 도착과 consume lag 분리; 동일 frame 반복 refresh 제거 |
| `MarketDataCache` | symbol key와 단일 `last_packet_ts`로 quote age/jitter 계산 | route/session/epoch별 실제 `0D` 시각과 별도 trade 시각; 평가 호출을 packet으로 세지 않음 |
| `sniper_entry_latency` | 평가 시 `_CACHE.update`; observer refresh 뒤 `received_at=None` 갱신 | quote 원시각 유지; refresh 소비 시각을 새 호가 수신시각으로 발명하지 않음 |
| episode gateway | utils 외에 `post_kiwoom_episode_read`/직접 POST 경로 사용 | utils만 고쳐 완료하지 않음; response/snapshot에 같은 metadata 전달 |
| widget advisory | `KiwoomReadOnlyClient`의 별도 shared-budget POST | 동일 classifier/adapter 사용; source-only 조회 class 유지 |
| snapshot writer/reader | WS 원시 dict와 파일 투영의 schema/시각이 다름 | route별 판정 보존; 파일 생성시각으로 원천 age 초기화 금지 |
| tick/history helper | 목적·limit·payload별 cache와 여러 호출 지점 | 동일 요청만 합치고 historical/live·route별 의미를 섞지 않음 |

실제 구현 위치는 line number 대신 함수명과 구현 시 source hash로 고정한다.

- `src/engine/kiwoom_websocket.py`: `_snapshot_target`, `get_latest_data`, `get_all_data`, type별 receipt 갱신, raw trade/depth callback, subscription freshness.
- `src/engine/bd_fbuy_accum_pre_scanner.py`: `write_ws_snapshot`, `_ws_machine_route_payload`, `_ws_live_for_code`.
- `src/engine/scalping/ai_market_snapshot.py`: `realtime_type_provenance`, `build_ai_market_snapshot`, `ai_input_preflight`, venue consistency/source-time skew.
- `src/engine/kiwoom_sniper_v2.py`: `_scanner_normalize_ws_snapshot_for_entry_eval`, `_scanner_ws_snapshot_entry_realtime_fresh`, stale-park/fresh-WS reactivation, batched WS snapshot cache.
- `src/engine/sniper_state_handlers.py`: `_normalize_pre_ai_strength_ws_timestamp`, `_pre_ai_refresh_strength_momentum_ws_snapshot`, `_update_ai_quote_freshness_fields`, `_pre_submit_refresh_real_ws_snapshot`, holding refresh와 REST refresh.
- `src/engine/sniper_entry_latency.py`: entry 평가 내 `_CACHE.update`, `_maybe_refresh_stale_quote_from_observer`, relief/remeasure helper.

## 3. 신규 코드를 늘리지 않는 공통 설계

### 3.1 기존 owner의 분담

| 기존 파일 | 구현 역할 | 금지사항 |
| --- | --- | --- |
| `src/trading/market/quote_consistency.py` | 공통 health pure helper·source 시각 읽기를 최소 추가. 기존 numeric quote consistency 유지 | scalping/AI 역의존, network 호출, 새 가격/매매 owner |
| `src/trading/market/market_data_cache.py` | 기존 cache를 route/session/epoch·type별 시각으로 확장. 필요한 bounded activity state 보관 | 별 cache daemon/DB, symbol-only cross-route 합류 |
| `src/engine/kiwoom_websocket.py` | genuine event 도착으로 state 갱신. atomic snapshot에 공통 metadata 부착 | callback 내 REST, history 전체 복사 증가, getter 횟수로 gap count 갱신 |
| `src/utils/kiwoom_utils.py` | 기존 REST parser/helper·cache에 response/source 시각과 metadata 부착. 호환 return 유지 | 모든 응답을 trade/quote로 취급, quote 상태로 auth/주문/reconcile 차단 |
| `src/trading/order/kiwoom_episode_read_control.py` | 기존 pacer/짧은 TTL cache/공유 admission 재사용. market read의 metadata 결속 | 주문 single-flight, fresh account read cache화, retry/capacity 상향 |
| `src/engine/scalping/market_data_enrichment.py` | 기존 WS/REST envelope에 health 투영, common pure helper에 위임 | 두 번째 판정 로직, 정상 경로의 자동 REST 재조회 |
| `src/trading/market/quote_health.py` | 기존 `QuoteHealth`에 필요한 source/age metadata를 호환 전달 | 단일 `ws_age_ms`로 trade/quote/transport 전부 설명 |
| 기존 snapshot writer·consumer | 같은 metadata 저장·소비; consume clock으로 age만 재평가 | 생성/copy 시각으로 fresh화, 같은 공백 재계수 |

표의 추가 helper/field는 구현 예정이다. 기존 API로 오인하지 않는다. 기존 module 내부 최소 함수/field 추가는 허용하되 새 package/CLI/report producer는 추가하지 않는다. common market package가 engine을 import하지 않도록 import cycle을 검사한다. 큰 파일의 무관한 정리·이동도 함께 하지 않는다.

### 3.2 공통 판정 데이터 계약

기존 envelope 안에 `market_data_health` metadata를 추가한다. 소비자마다 competing envelope를 만들지 않는다. schema `kiwoom_market_data_health_v1`은 제안값이며 기존 versioning과 정합시킨다.

| field군 | 의미 |
| --- | --- |
| scope | symbol, requested route/item, market-data route, effective venue, actual execution venue, session, trade date, transport epoch |
| 원시각 | quote receive (`0D`), trade receive (`0B`), provider trade/event, REST response receive, snapshot capture 시각 |
| 소비시각 | `evaluated_at`, snapshot age, receive→consume lag. copy/serialize는 원시각을 바꾸지 않음 |
| age | `quote_age_ms`, `trade_receive_age_ms`, `trade_event_age_ms`, `transport_receive_age_ms`, `local_consume_lag_ms`; 불명은 null |
| identity/연속성 | type별 item/route/epoch/sequence, 등록 receipt, first-data, local drop/gap, continuity quality |
| trade activity | §1의 상태, quiet episode key, derived repeat count, 공백10초/반복3회, evidence basis |
| quote/source | fresh/stale/missing/future/conflict/unproven와 직접 reasons. stage별 quote TTL은 기존 consumer contract에서 전달 |
| REST | API/payload digest, request owner/class, requested/response route, cache/single-flight reuse, admission wait, HTTP RTT, source timestamp authority |
| authority | `decision_authority=market_data_input_only_no_order_authority`, `actual_order_submitted=false`; BUY/SELL/price/quantity/provider authority 없음 |

동일 symbol의 KRX/NXT/integrated scope는 분리한다. `last_ws_update_ts`는 transport 관측용으로 남기되 BBO/tape 대리시각으로 쓰지 않는다. `0w`/program/LOGIN/PING이 `0B`/`0D`의 freshness를 갱신하지 않는다.

WS manager가 quiet episode state의 authoritative producer다. 같은 manager의 consumer는 해당 snapshot을 공유하고, 파일 consumer는 동일 state receipt를 읽는다. REST client가 별도 repeat count를 만들지 않는다. 대응 WS 관측이 없는 REST-only scope는 `OBSERVATION_UNPROVEN` 또는 명시적 적용외로 두고, metadata 누락을 정상값으로 채우지 않는다.

### 3.3 공백 반복 episode 규칙

1. scope의 첫 정상 `0B`로 시작한다. epoch/session/route 변경·continuity 손상으로 state를 reset/invalid 처리한다.
2. 마지막 genuine trade 뒤 10초 이상 공백이면 한 episode다. key는 기존 scope·epoch·마지막 genuine trade sequence/시각에 결속한다. 새 추천/workorder ID는 만들지 않는다.
3. getter는 age와 현재 episode의 기준 도달 여부를 pure 계산한다. getter/retry/copy/promotion이 counter를 증가시키지 않는다.
4. 다음 genuine `0B` 도착 시 직전 공백이 10초 이상이었다면 closed quiet count를 한 번 증가시킨다. 동일 event/sequence 재소비는 제외한다.
5. 현재 공백도 10초 이상이면 `closed count + 현재 episode 1`이 derived count다. 긴 30초 공백을 10초×3으로 나누지 않는다.
6. 각 trade 간격이 10초 미만인 정상 활동이 10초 지속되면 반복 count를 reset한다. 별도 시간 parameter는 추가하지 않는다. connection recovery만으로 활동 회복을 선언하지 않는다.
7. provider 과거 event, regression, duplicate, route mismatch, drop/epoch 변경은 genuine 회복/반복 증거로 쓰지 않는다. 원packet은 유지한다.

10초 정확히부터 quiet로 판정한다. future 시각을 `max(0, age)`로 정상화하지 않는다. 동일 process의 duration은 monotonic clock을 우선하고, 저장 epoch 시각은 provenance/재생 기준을 명시한다. 재생은 저장된 event cutoff 기준이지 현재 시각 기준이 아니다.

## 4. 장중 소비점 전수 조사·전환 inventory

조사 범위는 `src`의 비test Python, `tools` client, `deploy` launcher다. 직접 API/WS import·alias, 직접 POST, 주입 getter/client, common parser, passed dict와 snapshot file read를 추적했다. 아래는 소스 경로 inventory이며 active runtime 전수 receipt 검증 완료표는 아니다. 구현 시작 시 callsite·source hash·installed owner를 다시 고정한다.

모든 후보를 `market_live_consume / metadata_pass_through / account_order_only / historical_only / retired_off / transport_only`로 분류한다. account/history도 조사에서 누락하지 않되 trade activity 적용외다. **모든 지점에 동일3초/10초를 적용한다는 뜻이 아니다.**

### 4.1 수신·공유·main/scanner

| 파일/경로 | 전환·검증 범위 |
| --- | --- |
| `src/utils/kiwoom_utils.py` | `fetch_kiwoom_api_continuous`, `get_stock_orderbook_ka10004`, `get_tick_history_ka10003`, `get_recent_signed_trades_ka10084`, `get_minute_candles_ka10080_with_meta`, program/investor/basic, `build_realtime_analysis_context`; API별 의미 유지 |
| `src/utils/kiwoom_read_request_control.py` | 공유 read budget/cooldown; health 재판정 없이 owner/class/대기 provenance 전달 |
| `src/engine/kiwoom_websocket.py` | raw0B/0D, target/getter, 등록/repair, async writer; 주문execution type 별도 |
| `src/engine/bd_fbuy_accum_pre_scanner.py` | file writer/route 투영, 장중 확인/daily fallback; DB/daily 가격을 freshWS로 바꾸지 않음 |
| `src/engine/kiwoom_sniper_v2.py` | batched WS, normalize, scheduler freshness, park/reactivation, REST fallback |
| `src/scanners/scalping_scanner.py` | 주입/alias getter, candidate/BBO/candle/tape, promotion; 독립 시장 분모를 quiet로 삭제하지 않음 |
| `src/scanners/final_ensemble_scanner.py`, `kosdaq_scanner.py`; `src/engine/signal_radar.py`, `market_panic_breadth_collector.py`, `ipo_listing_day_runner.py` | rank/breadth/daily/margin/live quote 분류; 현재 scope만 전환, OFF 전략 복원 금지 |
| `src/engine/sniper_state_handlers.py` | target→analysis/pre-AI/pre-submit/holding/multi-leg/scale-in frame, quote refresh, tick/candle/context 호출을 함수·callsite 단위로 대사 |
| `src/engine/sniper_analysis.py`, `sniper_condition_handlers.py` | basic/program/investor, 반복 tick/candle 조회; 기존 snapshot의 안전한 재사용 |
| `src/engine/sniper_s15_fast_track.py`, `sniper_overnight_gatekeeper.py` | live tick/candle/context, 보유 감시; quote/broker/exit 안전 유지 |
| `src/engine/sniper_scale_in.py`, `sniper_execution_receipts.py`, `scalping_feature_packet.py`; 기존 `ai_decision_trace.py`와 lifecycle/pipeline logger | passed frame/feature/receipt metadata 상속; scale-in action/sizing 변경 없음. journal에서 scope/type 시각이 탈락하지 않음 |
| `src/engine/ai_engine_openai.py` | machine-primary/compact auxiliary/holding 등 stage별 preflight; 필수feature·prompt partition 유지 |
| `src/engine/scalping/ai_market_snapshot.py`, `market_data_enrichment.py`, `entry_setup_evidence.py` | 독립 freshness 추정을 공통 판정으로 위임; source 수정과 action threshold 수정 분리 |
| `src/engine/scalping/entry_candle_context.py`, `holding_decision_context.py`, `multi_timeframe_context.py`, `microstructure_reaction_context.py`, `main_ai_current_axis_input.py` | completed bar/tape/reaction; 0B/REST/bar/source-only 분리 |
| `src/engine/scalping/scanner_async_eval.py`, `micro_estimator_state.py`, `entry_reprice_after_submit.py`, `entry_split_order_plan.py`, `scale_in_split_order_plan.py`, `risky_micro_episode/policy.py` | 주입 scheduler/quote/feature; deadline/bundle/source lineage 유지 |
| `src/trading/entry/entry_orchestrator.py`, `entry_policy.py`, `normal_entry_builder.py`, `signal_snapshot.py`, `entry_types.py`, `state_machine.py` | 직접 health 사용/pass-through 분리; SAFE/CAUTION normal-submit와 DANGER/slippage 유지 |
| `src/engine/sniper_entry_latency.py`; `src/trading/entry/latency_monitor.py`, `orderbook_stability_observer.py`; `src/trading/market/quote_consistency.py`, `quote_health.py`, `market_data_cache.py` | quote/trade 시계, observe/consume 분리; observer endpoint 원시각/route 읽기 |

### 4.2 위젯·episode·micro·기존 exit

| 파일/경로 | 전환·검증 범위 |
| --- | --- |
| `src/trading/order/kiwoom_episode_read_control.py` | utils 우회 gateway read metadata/짧은TTL; 주문/fresh broker snapshot 제외 |
| `src/trading/samsung_morning_one_share/gateway.py`, `samsung_midday_one_share/gateway.py`, `samsung_afternoon_one_share/gateway.py`, `low_price_two_leg/gateway.py`, `widget_auto_trade/gateway.py` | `_post`, liquidity/velocity, completed minute parser/read budget; dataclass/return에서 metadata 탈락 방지 |
| 위 episode package의 `machine.py`, `service.py`, `preflight.py`; `src/trading/widget_auto_trade/engine.py`, `service.py` | 직접 getter뿐 아니라 공통 wrapper/주입client의 scope, preflight/signal/SELL/보유 복구 |
| `src/trading/order/regular_two_leg_machine.py`, `entry_liquidity_guard.py` | 공통 liquidity/velocity parser/guard; print count·depth·속도·가격·수량 계약 유지 |
| `src/trading/market/confirmation_window.py`, `micro_confirmation.py` | file exact-route0B+0D, past-only1초창; health는 전제, feature validity는 기존 kernel 소유 |
| `src/trading/market/entry_adverse_flow.py`, `target_pressure.py`, `profit_stagnation_quote.py` | adverse/target pressure/depth; quiet를 trade backing으로 보간 금지, 기존 executable quote TTL 유지 |
| `src/trading/order/entry_adverse_guard.py`, `entry_adverse_owners.py`, `target_ratchet.py`, `profit_stagnation.py`, `profit_stagnation_exit.py`, `profit_stagnation_owners.py` | 파생source 소비 owner; target/수량/취소/exit 로직 변경 없음 |
| `src/trading/order/adaptive_exit/market_source.py`, `source.py`, `runtime.py`, `group_runtime.py`, `driver.py`, `owner_loop.py`, `group_owner_loop.py`, `decision.py`, `group_decision.py`, `models.py`; `src/engine/monitoring/machine_adaptive_exit_source.py` | 연구/주입source와 runtime 연결 분류; 신규 exit 활성화/enrollment/보유 이관 없음 |
| `src/engine/scalping/limit_down_watch.py`, `micro_reversion/forward_collector.py`, `micro_reversion/canary_monitor.py` | getter 우회 raw callback; ordered0B+0D, route/epoch/sequence/source-only 유지 |
| `src/engine/monitoring/samsung_widget_advisory.py` | `KiwoomReadOnlyClient._post`, collector/BBO/tape/flow parser; source-only budget 유지 |
| `src/engine/monitoring/doosan_widget_advisory.py`, `hanwha_ocean_widget_advisory.py`, `widget_auxiliary_context.py` | 공유/상속client, symbol별advisory; market/flow/bar TTL와 metadata |
| `src/engine/monitoring/widget_symbol_runtime_collector.py`, `widget_research_watch_collector.py` | 주입 API, raw current/BBO/bar와 출력; signal source→trader 전달 |
| `src/engine/monitoring/pruned_candidate_bbo_collector.py`, `market_opportunity_census.py` | source-only bounded REST/독립census; quiet로 sampling·전체prune 분모 누락 금지 |
| `src/web/samsung_price_widget_routes.py`, `doosan_price_widget_routes.py`, `hanwha_ocean_price_widget_routes.py`; `src/notify/telegram_manager.py` | WS file/REST fallback, 공유client, 수동 분석/표시; file age와 quote age 분리, 오래된 가격 표시 주석 |
| `tools/windows` widget client, `deploy` 기존 collector/trader/monitor launcher | 서버 결과 pass-through/표시와 실제 실행 entrypoint; client의 자체 source verdict 생성 금지 |

### 4.3 적용외·기존 downstream 누락 방지

- `src/engine/sniper_sync.py`, `sniper_trade_utils.py`, `kiwoom_orders.py`, `src/trading/order/broker_gateway.py`, `manual_episode_exit_reconciliation.py`, symbol-owner apply/auto-apply와 각 gateway account/order/cancel/auth/preflight: `account_order_only`. quiet 때문에 reconcile/SELL/terminal 확인을 늦추지 않는다. request budget·실제 receipt 계약 유지.
- `src/bot_main.py` calendar/auth/startup, `src/engine/error_detectors/kiwoom_auth_8005_restart.py`: `transport_only` 등. 체결 공백을 auth 실패/재기동 이유로 만들지 않는다.
- `src/engine/monitoring/low_price_two_leg_entry_spot_research.py`, `widget_symbol_signal_policy_research.py`, `pure_market_kiwoom_backfill.py`, `low_price_two_leg_expanded_candidate_research.py`, `low_price_two_leg_tuning.py`: live 수집/historical 연구 구분. 과거 tm/date 조회를 현재 activity state에 넣지 않는다. 기존 source-only budget/metadata 계약 확인.
- `src/engine/monitoring/intraday_ws_freshness_monitor.py`, `intraday_entry_flow_report.py`, `intraday_entry_blocker_diagnostics.py`, 기존 rising-missed/pyramid 진단: 기존event metadata 소비. 별도 job 없이 quote age/trade quiet 진단 혼동 수정.
- #11/#74 `observation_source_quality_audit`, #119 `buy_funnel_sentinel`, #76 materialization, #82 calibration, #77–#80/기존 replay, machine attribution/entry timing, widget calibration/evaluation: 기존 downstream. 새field/label의 false-invalid·metadata 탈락·episode 중복을 필요한 기존parser/test에서만 보완한다. **새 장후 producer·schedule·필수artifact·추천/승격 gate는 추가하지 않는다.**
- `daily_report_service.py`, `codebase_performance_workorder_report.py`, `wait6579_ev_cohort_report.py`, lifecycle/strategy replay, post-sell/missed-entry, `src/utils/update_kospi.py`: live read/historical/pass-through 분류. 검색 hit를 새 실행 owner로 만들지 않는다.
- `institutional_flow_context.py`, `swing_sector_theme_source.py`, opening rotation, 퇴역shadow/ADM/LDM/bucket/greenfield: `retired_off` 또는 historical. 적용/수집/복구/ETA를 열지 않으며 기존 custody/parser 호환만 보존한다.

### 4.4 전수 완료 계약

inventory는 `file:function:callsite/consumed_field`별 source→adapter→consumer, scope, 분류, 전환 방법, test, 현재 owner를 기록한다. alias·주입client·passed dict·file reader 미분류를0으로 한다. 적용외도 분모에서 조용히 빼지 않는다.

재조사에서는 `rg`로 실제 조회 helper·Kiwoom URL·`session.post`·WS getter·snapshot path·type 시각·signed trade 필드를 검색한 뒤 Python AST로 import alias와 callsite를 대사한다. 직접 조회가 없는 downstream도 그 return/dataclass/주입 client의 사용처를 역추적한다. `curr/best_bid/best_ask/quote_stale`만 소비하는 지점도 별도 검색한다. test·archive·퇴역 코드는 적용외 분류하되 임의 삭제하지 않는다. 실행 파일 밖 client와 launcher의 import/공유 path도 조사한다. 이 inventory는 본 문서의 부록/검증 결과로 유지하고 이를 만드는 새 운영 프로그램은 만들지 않는다.

- `candidate_total = migrated_market_live + verified_metadata_pass_through + classified_not_applicable`.
- `unclassified_count=0`, `live_consumer_missing_common_health_count=0`, `independent_trade_activity_classifier_count=0`.
- 기존 stage별 quote/micro/bar/velocity 안전validator는 마지막 계수에 포함하지 않는다. 사실 age의 독립 추정·공백 재계수만 제거한다.
- grep/AST 잔존 결과를 각각 분류한다. consumer의 현재시각 읽기는 consume age 재계산이면 정상, source receive시각 대입이면 결함이다.
- static coverage, offline 연결 coverage, 실제 active PID 자연 coverage는 별개다. 비가동 scope를 자연 소비 완료로 표시하지 않는다.

## 5. API/WS별 정규화 계약

### 5.1 type·route·시각

`0B` trade와 `0D` quote의 receipt를 별도 보관한다. provider시각의 정밀도·날짜·session을 선언하고 동일초 경계를 억지로 확정하지 않는다. future/regression/route mismatch/cross-epoch는 직접 source gap으로 남긴다.

requested route와 actual execution venue를 분리한다. integrated `AL`을 개별 KRX/NXT의 actual 체결 venue로 쓰지 않는다. 정상 과거 item/등록 binding을 동일 epoch에서 유지하더라도 **identity 증거 보존**일 뿐 최신 event freshness의 대리가 아니다.

`krx_integrated_event_venue_unproven`, `realtime_type_provenance_missing_or_stale`를 다음으로 분해한다.

1. item/route/epoch/등록/first-data 자체 결손·충돌.
2. 정상 과거 type receipt는 있지만 최근trade 없음.
3. provider/receive 지연, local drop 또는 연속성 결손.
4. 실제 최신quote가 오래돼 executable source 사용 불가.

2를1에 합치지 않는다. 1/3/4를 quiet값으로 해제하지 않는다. registered view와 event actual venue의 불명을 구분하고 근거 없는KRX/NXT 추정을 추가하지 않는다.

### 5.2 REST별 의미

- `ka10004`: response receive시각으로 REST snapshot age를 측정한다. fresh orderbook은 trade 생성/0B freshness/매수 우세 증거가 아니다. `bid_req_base_tm`의 `raw_not_freshness_input` 계약 유지.
- `ka10003`/`ka10084`: response시각과 provider trade시각 분리. 최신행·route·정렬·중복·continuation·범위 확인. 많은 응답행/HTTP200을 현재 활발한tape로 간주하지 않는다.
- `ka10080`: completed bar/date/route/coverage 계약 유지. 분봉을10초 공백 규칙으로 invalid 처리하지 않는다.
- basic/program/investor/index/rank: source별authority/TTL 유지. generic HTTP wrapper가 trade health를 임의 판정하지 않는다.
- account/order/auth: market activity 적용외. failure/rejection/rate limit 원계약 유지.

REST-only client는 기존read 응답에 metadata만 결속한다. **무체결을 증명하려고 quiet를 읽을 때마다 ka10084/ka10003을 호출하지 않는다.** 독립 확인이 필요한incident는 기존bounded 진단/공유budget 내 sample로 한정한다.

실제 구현 전 [Official Kiwoom Reference Gate](../kiwoom-api-data-contract.md#official-kiwoom-reference-gate)를 수행한다. 현재 upstream SHA·조회시각·확인paths를 review에 기록하고 `kiwoom_docs`, spec/core/realtime/Postman과 필요한portal을 대사한다. 과거SHA를 현행으로 고정하지 않는다. 미정의FID/suffix/time은 추측하지 않고 raw/null/contract gap으로 남긴다. request/parser/REG 불변 부분도 범위를 기록한다.

## 6. latency·반복호출·감시예산 개선

### 6.1 시계를 분리한다

| 값 | 측정 대상 | 잘못된 대체 |
| --- | --- | --- |
| trade gap | 해당route 정상trade 간 관측 공백 | HTTP RTT/WS delivery latency |
| provider→receive | provider시각 입증 시 전달 지연 | source시각 불명인데0ms |
| receive→consume | 새quote 이후queue/analysis/AI/guard 지연 | snapshot copy시각 |
| quote age at submit | submit 직전 채택 BBO 연령 | 최근trade/program/PING/함수return시각 |
| REST wait/RTT | admission/HTTP/retry/parse 시간 | 모든quote age를 외부API 탓으로 귀속 |

기존 `LatencyMonitor` SAFE/CAUTION/DANGER, slippage/spread/quote/price guard와 별도 승인relief를 유지한다. 700ms/1500ms/2000ms 등 stage quote 기준을10초로 치환하지 않는다. 독립latency 장후 family도 복원하지 않는다.

`MarketDataCache.update`는 genuine source quote identity/시각으로만 quote freshness/jitter를 진행한다. 같은/오래된packet 재평가로 서로 다른context의가격을 섞지 않는다. observer refresh의 `received_at=None`을 제거하는 방향으로 채택quote 원timestamp/route/epoch/endpoint를 전달한다. 원시각 불명은 unproven 그대로다.

### 6.2 동일attempt read/refresh 통합

1. 기존batched WS getter에서 atomic frame을 얻어 setup/기계판정/AI입력에 같은identity를 전달한다.
2. 동일frame/policy/attempt의pure preflight는 재사용하되 소비시점age 만료를 다시 확인한다.
3. AI 중source가 만료되면 submit 직전 새WS cache를 다시 읽는다. 이 안전 재검증은 삭제하지 않는다.
4. fresh canonical WS quote가 있으면 REST fallback을 생략한다. 없으면 기존bounded REST 계약만 이용한다.
5. REST refresh 응답은 payload/route/source/deadline이 맞을 때만 공유한다. AI전/submit전 age조건 차이를 보존한다.
6. 실패/rate limit/source rejection을 guard별로 각각retry하지 않는다. failure receipt를 공유하고 새source 또는 기존bounded 조건에서만 재개한다.

절약 대상은 동일원입력의중복조회·heavy평가다. cheap freshness 재검증, broker safety, order terminal 확인은 절약 대상으로 삼지 않는다.

### 6.3 cache/single-flight

기존 `_MARKET_DATA_CACHE`, `ShortTtlSnapshotCache`, `SameMinuteSnapshotCache`와 lock을 확장한다. 별 framework/cache/worker를 만들지 않으며 실제 동시 read 중복이 있는 기존 함수 내부에서만 single-flight를 보완한다.

- fetch key: real/demo origin, token/account scope digest, api-id, canonical wire payload, exact requested item/route, date/tm/continuation. bearer token 저장/출력은 금지한다.
- consumer owner/policy/attempt/purpose/deadline은 receipt별로 결속한다. wire data가 같아도 판단은 공유하지 않는다. query/auth scope가 다르면 fetch도 공유하지 않는다.
- limit 10/30이 같은 wire payload라면 정상 raw response 공유 가능성을 검토하되 slice/parser는 유지한다. pages/cutoff 차이는 무조건 합치지 않는다.
- 성공·source-valid 응답만 기존 TTL 안에서 재사용한다. failure/admission defer의 동일 attempt suppression은 명시적 failure receipt이며 positive cache와 구분한다.
- producer는 shared gate를 한 번 통과하고 waiter는 추가 request를 만들지 않는다. waiter deadline 만료 때문에 duplicate request를 발생시키지 않는다.
- memory/pending cap을 유지한다. timeout 후 late result가 새 epoch/current-policy context를 덮어쓰지 않게 한다. 종료되지 않은 HTTP를 끝난 worker로 가장하지 않는다.
- single-flight는 process-local이다. 다른 process까지 호출 0을 보장하는 새 daemon은 만들지 않고 기존 snapshot 공유/pacer/budget을 사용한다.
- 주문/취소/auth/fresh account·broker·terminal 확인은 대상외다. execution-critical slot을 source-only waiter가 점유하지 않는다.

### 6.4 scanner 감시·평가 예산

- 같은 scope/policy/source generation/event identity의 in-flight evaluation을 기존 coordinator에서 중복 제거한다.
- frame이 그대로인 SOURCE_INVALID를 매 loop heavy 평가/AI/REST에 재전송하지 않는다. 기존 deadline/backoff/source wakeup으로 대기하고 retry/capacity를 늘리지 않는다.
- blocker에 대응하는 genuine source에서 대기를 해제한다. quote 부족은 새 0D, trade feature 부족은 새 0B, binding 결손은 등록/epoch/source 복구다.
- 기존 stale park의 1-generation reactivation bound와 enqueue 실패 invalidate를 유지한다. quiet getter가 generation을 늘리지 않는다.
- 반복 quiet만으로 새 BUY 거부·universe 제외·slot/cap 변경을 추가하지 않는다. 기존 owner가 nonentry/입력 부족으로 닫은 같은 source의 중복 heavy 평가만 억제한다.
- slot/예약수/universe/promotion rule은 그대로 두고 기존 valid terminal/expiry의 reservation 반환·orphan 정리를 검증한다.
- 0D 변화만으로 entry 조건이 변할 수 있는 scope를 새 0B만 기다리게 하지 않는다. wakeup을 일괄 trade-only로 만들지 않는다.
- independent census/prune observer의 선언 sampling을 유지한다. 평가 절약을 시장 분모 삭제/감시 종료로 바꾸지 않는다.
- SELL/holding/custody/manual 감시와 주문 receipt는 계속 우선한다. BUY 예산 절약으로 보유 감시를 간헐화하지 않는다.

### 6.5 기존event에서 효과 확인

현재 pipeline/threshold/WS freshness/entry flow event에 최소 필드만 추가한다. 별 report/job은 없다.

- source frame/quote/trade identity, quiet episode/count, 채택 age/consume lag.
- request owner/class/API/route/payload digest, actual request/reuse/suppressed, admission wait/RTT/기존 retry 수.
- evaluation enqueue/start/end, duplicate suppression, park/wakeup reason, watch reservation 반환.
- raw event와 unique attempt/frame/promotion 분모는 분리한다. transition/terminal/기존 bounded 요약 중심으로 로그 burst를 피한다.

이 필드들의 계약은 `metric_role=source_quality_gate|funnel_count` 중 실제 역할을 명시하고, `decision_authority=diagnostic_no_order_authority`, `window_policy=exact_scope_event_or_attempt_window`, `primary_decision_metric=not_applicable_diagnostic`, `sample_floor=not_applicable_contract_validation`로 선언한다. source-quality gate는 exact route/type/epoch/time 검증이다. 금지 용도는 양수 EV/수익/BUY/SELL/정책 승격의 대용이다. quiet 반복 기준 3은 관측 상태의 기준이지 경제적 표본 floor가 아니다.

수리 acceptance는 동일 입력 1 in-flight, 동일 payload 동시 read 1 transport, 새 source 정상 복귀, 기존 guard 유지다. 공유 API 상한/source-only 예약/주문 bucket은 현재 설정을 확인하고 retry/density/capacity를 상향하지 않는다.

### 6.6 요청 목적별 budget class 점검

현재 `src/web/samsung_price_widget_routes.py._kiwoom_post`의 화면 fallback은 `request_owner=samsung_price_widget_http_fallback`, `request_class=runtime_required`를 사용한다. 화면 기본가격 `ka10001`과 account `kt00018`을 한꺼번에 같은 market-read 절약 규칙으로 바꾸지 않는다.

- 비주문 화면 가격/연구/advisory/census read는 실제 intended consumer를 확인해 기존 `source_only` reservation으로 분류 가능한지 검토한다. 화면 refresh가 execution용 slot을 소모하는 직접 후보다.
- gateway의 BUY 직전 liquidity/velocity, holding 안전 확인, 실제 broker/account/terminal read는 기존 `runtime_required|execution_critical` 역할을 유지한다.
- `get_tick_history_ka10003` 등 helper가 request owner/class를 전달하지 못하면 기존 함수에 호환 keyword 인자를 추가하고 callsite가 목적을 전달하도록 한다. 새 helper 복제 또는 API-id만으로 전체 class 변경은 하지 않는다.
- class 변경은 호출 목적의 잘못된 귀속을 고치는 범위다. source-only capacity 확대, 새 polling, shared limit 완화 또는 주문 budget 축소가 아니다. 분류 근거·API 수·대기 receipt로 검증한다.
- 여러 소비자의 동일 raw 응답을 공유하더라도 우선순위가 낮은 작업의 긴 대기 때문에 execution consumer가 같은 pending 작업에 무조건 묶이지 않게 한다. deadline/예약 계약을 먼저 검증하고, 안전하게 묶을 수 없으면 기존 명시적 defer를 유지한다.

## 7. 분할 실행 가능한 일괄 작업지시

후속 구현지시에서 아래 단위를 순서대로 실행한다. 이번에는 실행하지 않는다. C0~C7은 작업 package명이지 native 추천 ID나 새 scheduled owner가 아니다.

| 단위 | 작업 | 선행 | 완료조건 |
| --- | --- | --- | --- |
| C0 전수 고정 | callsite inventory, 작업본/release 차이, 공식 reference, stage TTL/authority | 없음 | 미분류 0, dirty 변경 분리, 금지 surface 명확 |
| C1 공통 facts/state | 기존 helper/cache/WS의 type 시각·quiet episode·scope/epoch/continuity | C0 | 경계/중복/clock/epoch test, network 없음, getter 무부작용 |
| C2 adapter 연결 | REST/direct client/episode/writer metadata와 호환 return | C1 | adapter parity, history/live 혼입 0, writer fresh화 0 |
| C3 main/scanner/AI | age 추정 위임, preflight 이유 분리, passed frame lineage | C2 | 비AI/holding/scale-in 포함 연결 test, owner 누출 0 |
| C4 독립 owner | 위젯/episode/advisory/주입 collector/micro/exit/web | C2 | scope별 direct/pass-through coverage, broker/target/수량 불변 |
| C5 latency/예산 | quote/observer 시계, read/refresh 통합, scheduler 중복 제거 | C3/C4 | 새 source 복귀, guard 유지, 중복 transport/eval test |
| C6 전수 closure | AST/grep 대사, 기존 event/downstream 호환, offline/부하/목적 review | C1~C5 | 미분류/consumer 누락 0, P0~P2 finding 0, validation PASS |
| C7 release/PID | 동일 세대 release 검증, 허용된 선택/기동, 자연 효과 | C6·실행권한 | hash 일치, PID/자연 coverage, 기존 rollback 가능 |

각 단위는 `구현 → self review → finding별 수정보완 → re-review → targeted validation`을 반복한다. finding을 남기고 다음 phase 완료/commit/deploy/비싼 report 재생성을 하지 않는다. C3/C4는 분리 review가 가능하지만 미확정 공통 schema를 각각 fork 구현하지 않는다.

diff뿐 아니라 producer→adapter→consumer→terminal을 검토한다. 다른 세션 source 변경 시 영향 package/C6를 재검증하고 구 PASS로 신 release를 기동하지 않는다.

### 7.1 필수 테스트

1. 3/6/9.999초 공백+fresh 0D, 10초 정확히, 긴 30초 공백: activity/quote age/반복 분모 일치.
2. 같은 공백 100회 get, 여러 promotion/owner의 동일 frame 소비: 반복 count 1.
3. 공백→genuine trade→공백 3회, 10초 정상 활동, scope/epoch reset: 일관 계수/복귀.
4. 첫 0B 미수신, quote-only/PING-only/타 symbol 활발, local drop/reconnect: 시장 무체결 확정 금지.
5. 과거 provider 시각 late trade/future/regression/duplicate/cross-route: fake fresh/recovery 금지.
6. program만 갱신, quote 오래됨/trade 새로움, 반대 조합: 시계 혼합 금지.
7. 동일 입력/시점/contract를 main/AI/gateway/widget/episode/file이 소비: common health parity, stage TTL 차이만 허용.
8. REST fresh book+오래된/불명 trade, minute/history: fake 0B/매수 우세/current state 갱신 금지.
9. 동일 payload 동시 read/다른 route/tm/date/origin/account/continuation/deadline: 정확한 reuse와 오공유 0.
10. rate limit/shared budget wait/timeout/parser fail/late completion: 기존 retry/예약 유지, 빈 source 성공 금지.
11. AI 중 expiry/submit 전 new frame/observer refresh 후 age 경과: submit 재검증·원시각 유지.
12. 동일 frame 반복 평가, 새 0B/0D wakeup, enqueue fail/deadline: duplicate/orphan/무기한 park 없음.
13. quiet에서도 holding SELL/cancel/terminal/custody 확인 지속, owner/주문/수량/target 불변.
14. 1초 micro/trade backing/refill 결손: 보간 금지, 기존 fallback/원 target 유지.
15. legacy/new envelope 혼재: 원packet의 pure 호환 adapter 또는 명시 unproven, blind fresh/예외 은폐/전체 날짜 false block 금지.
16. callback/getter/writer 부하: history deepcopy/global-lock network/pending 무제한/로그 burst 금지.

기존 test 파일을 우선 확장한다. 주경로: `src/tests/test_kiwoom_websocket.py`, `test_ai_market_snapshot.py`, `test_market_data_enrichment.py`, `test_quote_consistency.py`, `test_kiwoom_quote_consistency.py`, `test_kiwoom_episode_read_control.py`, `test_entry_liquidity_guard.py`, `test_sniper_entry_latency.py`, `test_scanner_async_eval.py`, `test_scanner_async_entry_bridge.py`, `test_widget_symbol_runtime_collector.py`, `test_widget_research_watch_collector.py`, `test_dynamic_micro_confirmation.py`, `test_entry_adverse_flow.py`, `test_target_pressure.py`, `test_profit_stagnation.py`; `src/trading/tests/test_market_data_cache.py`, `test_entry_orchestrator.py`, `test_latency_monitor.py`. 영향받는 기존 audit/sentinel/downstream test도 추가한다.

프로젝트 `.venv`의 관련 pytest/변경 Python compile, wrapper 변경 시 bash syntax/contract test, `git diff --check`를 실행한다. mock/offline fixture로 실API/Provider/실주문 없이 먼저 닫는다. 새 test module도 기존 파일 확장이 불가능한 이유와 role location을 확인하며 engine-root allowlist를 불필요하게 넓히지 않는다.

## 8. 작업본→배포본→실제PID

1. **작업본 고정**: branch/HEAD/diff/hash, dirty/다른 세션 변경, selected release/current PID/서비스 root 읽기. mtime/최신 폴더명으로 배포 대상을 정하지 않는다.
2. **작업본 구현·검증**: C0~C6/finding 0/targeted validation/consumer coverage. 경제성 자연 표본 부족을 코드 수리의 가짜 실주문 요구로 바꾸지 않는다.
3. **commit/push**: 후속 구현 요청 권한에 따라 검증 변경만 commit한다. 무관 생성물/custody/env/다른 세션 변경을 합치지 않고 remote branch/hash를 확인한다.
4. **기존 managed release**: `deploy/run_runtime_release.sh`/`src/engine/infrastructure/runtime_release_router.py`의 현재 contract대로 생성한다. 새 배포 script/service는 없다. 가동 release 직접 편집/rsync 덮어쓰기는 금지한다.
5. **배포본 재검증**: 변경 source·의존 helper·gateway·writer·tests/config hash가 검증 작업본과 일치해야 한다. 공유 data/.venv symlink 실체와 code 범위를 분리한다. release-local import/compile/targeted test로 workspace 오import PASS를 방지한다.
6. **선택/기동 분리**: 선택만으로 구 PID는 갱신되지 않는다. main/collector/widget trader/episode/web의 cwd/ExecStart/import 방식을 각각 확인하고 필요 대상만 허용 권한/기존 절차로 갱신한다. 포괄 재기동은 금지한다.
7. **실PID 검증**: root/commit/source hash, policy date/hash, custody·미체결/전시장 balance, WS login/REG/type first-data/epoch, common health import/config receipt를 확인한다. metadata 성공을 정책 적용/주문 성공으로 대체하지 않는다.
8. **자연 coverage**: 실제 source→공통 판정→machine/AI/price/sizing/submit 또는 valid nonentry terminal을 연결한다. widget/episode/holding은 독립 receipt다. sample 0은 설정 확인/자연 미관측을 구분한다.
9. **rollback**: route 혼합/fake freshness/guard 누출/SELL·reconcile 중단/lock·latency 악화 시 새 세대 사용을 중단한다. 갱신됐다면 기존 managed rollback·허용 기동 범위로 구 검증 release에 복귀한다. source/주문/custody는 되돌리지 않는다.

이번 계획 작성은 selected release/PID를 변경하지 않는다. 후속 기동 허가도 numeric 가격/수량/manual lock/provider/cap/안전 threshold의 포괄 변경권한은 아니다.

## 9. 기대효과·조건의 합리성

| 기대효과 | 구현 acceptance | 자연/경제성 확인 |
| --- | --- | --- |
| source-invalid 오귀속 감소 | quiet/identity/quote/전달·소비 지연 분리, same input parity | 원 floor/분모 축소 없이 valid 기회 평가 회복 |
| 중복 read/heavy 평가 감소 | same payload 동시 read 1 transport, same frame 1 in-flight, fresh WS 시 호가 REST fallback 0, new source 복귀 | API 수/budget wait/queue lag/consumer latency 개선 |
| 유효 기회 우선 소비 | 중복 억제·정상 wakeup, slot/guard 불변 | 독립 recall/promotion→eval 지연/submit·fill 유지 개선 |
| 안전·회전 유지 | quote/price/adverse/broker/quantity/cooldown/SELL 감시 유지 | full/partial/terminal/tail/자본점유/비용 후 순익 |

‘비용을 차감하고 작은 수익을 빈번하게’의 구체목표는 **fresh executable quote의 유효 기회를 빨리 평가하고, 같은 입력의 반복작업으로 다음 기회를 놓치지 않는 것**이다. guard 무차별 완화/quiet BUY화/주문 수 증가 자체는 목적이 아니다.

코드 수리 완료에 양수 EV/전 horizon/5·10·20일 동시 floor/별도 장후 승인을 요구하지 않는다. 반대로 parity/호출 절약만으로 수익 개선을 선언하지 않는다. 경제성은 기존 owner의 effective cost·exact terminal·owner/venue/session·policy/source generation·complete/censored 계약으로 측정하고 불명 cost/PnL은 null로 유지한다. 기존 장후 측정은 그대로 사용하고 quiet 10초를 자동 최적화하는 새 job/family는 없다.

호출/평가 절약은 동일 recorded 입력·도착순서·clock의 offline fixture에서 before/after 호출수·대기·queue 진행을 확인한다. 다른 시장일의 단순 평균이나 SOURCE_INVALID 분모 감소로 효과를 귀속하지 않는다. 무조건 submit 증가율, 고정 ms 감소율 또는 모든 scope 자연 sample을 코드 배포 gate로 추가하지 않는다. 실제 적용 뒤 active scope의 예산/latency가 악화하거나 새 source를 놓치면 원인을 수정한다.

최종보고는 `code/contract closure → 작업본/release 일치 → PID 소비 → 자연 coverage → latency/예산 효과 → 비용 후 경제성`을 분리한다. ENTER_NOW 부족이 기존 micro/경제성의 정상 nonentry로 남으면 해당 owner를 설명하며 입력 수리 완료와 혼동하지 않는다.

## 10. 문서·운영 정합 검증

- 구현 시 source/metadata owning contract와 기존 consumer 설명을 같은 change set에서 갱신한다. baseline README/runbook/Plan Rebase/AGENTS는 명시 요청이 있을 때만 수정한다.
- cron/ExecStart/schedule·장후 필수 owner는 추가/변경하지 않는다. 자연 확인은 기존 current checklist의 source-quality/WS continuity owner에 연결하고 완료 old item을 재개하지 않는다.
- 문서/checklist 수정 후 link/owner/authority review와 print-only parser만 실행하며 외부 sync/token 확인은 하지 않는다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500
```

필요할 때 사용자가 실행하는 표준 sync 명령:

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

# 키움 API 코드 참조 전수 목록 — 2026-10-06

[판정·대체 범위·현재성·검증 보고서](kiwoom-rest-ws-substitution-survey-2026-10-06.md)

- 코드 조사 snapshot: `2026-10-06T17:18:46.354097+09:00`.
- 선택 릴리스: `fd222e315577c10853b23db583f260ef76259b39`; `/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31`.
- 실제 Main `ubuntu` PID `126945`, cwd `/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src`, 관측 `2026-10-06T17:20:43.586552+09:00`.
- 조사 중 별도 작업에서 초기 릴리스 eeccb1f4127a39d7454c8bb464f1018cb4365812가 교체되어 최신 코드와 소비 PID를 재검증했다. API ID 집합/중앙 transport/계좌 동기화와 주요 비용·호가·capacity 함수의 의미는 동일하다.
- 상수/헬퍼/함수 전달 참조는 실행 도달성 또는 물리 HTTP 횟수의 증거가 아니다. 과거/조건부/현재 분기는 본문 판정표를 따른다.
- Python 612파일의 REST ID 45종 + 인증 endpoint 1종. 테스트/archive 제외, AST parse 실패 0.

## 1. API별 참조

### ka00198 — 실시간종목조회순위(ka00198)

- 공식 path: `/api/dostk/stkinfo`.
- 공통 헬퍼: `get_realtime_hot_stocks_ka00198`, `get_realtime_item_rank_ka00198`.
- API 상수 참조:
  - [src/utils/kiwoom_utils.py:2719 get_realtime_hot_stocks_ka00198](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:2719).
  - [src/utils/kiwoom_utils.py:3360 get_realtime_item_rank_ka00198](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:3360).
  - [src/utils/kiwoom_utils.py:3372 get_realtime_item_rank_ka00198](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:3372).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/scanners/scalping_scanner.py:6695 run_scalper_iteration](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/scanners/scalping_scanner.py:6695) → `get_realtime_item_rank_ka00198`.

### ka10001 — 주식기본정보요청(ka10001)

- 공식 path: `/api/dostk/stkinfo`.
- 공통 헬퍼: `get_basic_info_ka10001`.
- API 상수 참조:
  - [src/engine/kiwoom_sniper_v2.py:8211 _fetch_rest_quote_snapshot_for_ws_gap](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/kiwoom_sniper_v2.py:8211).
  - [src/engine/scalping/entry_strategy_policy.py:275 features](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/scalping/entry_strategy_policy.py:275).
  - [src/engine/sniper_state_handlers.py:48515 _fetch_holding_rest_quote_snapshot](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:48515).
  - [src/engine/sniper_state_handlers.py:48539 _fetch_holding_rest_quote_snapshot](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:48539).
  - [src/utils/kiwoom_read_request_control.py:77 WidgetMarketResponseCache._complete](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_read_request_control.py:77).
  - [src/utils/kiwoom_read_request_control.py:85 WidgetMarketResponseCache.run](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_read_request_control.py:85).
  - [src/utils/kiwoom_utils.py:2328 get_basic_info_ka10001](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:2328).
  - [src/utils/kiwoom_utils.py:2346 get_basic_info_ka10001](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:2346).
  - [src/utils/kiwoom_utils.py:5654 _fetch_kiwoom_api_continuous_transport](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:5654).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/engine/sniper_analysis.py:88 analyze_stock_now](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_analysis.py:88) → `get_basic_info_ka10001`.
  - [src/engine/sniper_condition_handlers.py:676 handle_condition_matched](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_condition_handlers.py:676) → `get_basic_info_ka10001`.
  - [src/notify/telegram_manager.py:914 process_manual_add_step](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/notify/telegram_manager.py:914) → `get_basic_info_ka10001`.
  - [src/utils/update_kospi.py:405 process_and_save_stock](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/update_kospi.py:405) → `get_basic_info_ka10001`.

### ka10003 — 체결정보요청(ka10003)

- 공식 path: `/api/dostk/stkinfo`.
- 공통 헬퍼: `build_realtime_analysis_context`, `get_tick_history_ka10003`, `summarize_ticks_for_realtime_ka10003`.
- API 상수 참조:
  - [src/engine/sniper_analysis.py:122 analyze_stock_now](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_analysis.py:122).
  - [src/trading/low_price_two_leg/gateway.py:64 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/low_price_two_leg/gateway.py:64).
  - [src/trading/order/entry_liquidity_guard.py:138 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/entry_liquidity_guard.py:138).
  - [src/trading/order/entry_liquidity_guard.py:446 parse_ka10003_entry_execution_velocity_snapshot](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/entry_liquidity_guard.py:446).
  - [src/trading/order/entry_liquidity_guard.py:913 evaluate_entry_execution_velocity](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/entry_liquidity_guard.py:913).
  - [src/trading/samsung_afternoon_one_share/gateway.py:61 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_afternoon_one_share/gateway.py:61).
  - [src/trading/samsung_midday_one_share/gateway.py:61 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_midday_one_share/gateway.py:61).
  - [src/trading/samsung_morning_one_share/gateway.py:66 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_morning_one_share/gateway.py:66).
  - [src/utils/kiwoom_utils.py:51 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:51).
  - [src/utils/kiwoom_utils.py:4551 get_tick_history_ka10003](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:4551).
  - [src/utils/kiwoom_utils.py:4565 get_tick_history_ka10003](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:4565).
  - [src/utils/kiwoom_utils.py:4571 get_tick_history_ka10003](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:4571).
  - [src/utils/kiwoom_utils.py:4640 get_tick_history_ka10003](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:4640).
  - [src/utils/kiwoom_utils.py:4647 get_tick_history_ka10003](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:4647).
  - [src/utils/kiwoom_utils.py:5654 _fetch_kiwoom_api_continuous_transport](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:5654).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/engine/scalping/zero_base_probe.py:440 run_zero_base_probe](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/scalping/zero_base_probe.py:440) → `get_tick_history_ka10003`.
  - [src/engine/sniper_analysis.py:104 analyze_stock_now](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_analysis.py:104) → `get_tick_history_ka10003`.
  - [src/engine/sniper_analysis.py:318 get_detailed_reason](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_analysis.py:318) → `get_tick_history_ka10003`.
  - [src/engine/sniper_analysis.py:349 get_detailed_reason](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_analysis.py:349) → `get_tick_history_ka10003`.
  - [src/engine/sniper_analysis.py:470 get_realtime_ai_scores](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_analysis.py:470) → `get_tick_history_ka10003`.
  - [src/engine/sniper_analysis.py:494 get_realtime_ai_scores](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_analysis.py:494) → `get_tick_history_ka10003`.
  - [src/engine/sniper_overnight_gatekeeper.py:273 _build_scalping_overnight_ctx](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_overnight_gatekeeper.py:273) → `build_realtime_analysis_context`.
  - [src/engine/sniper_overnight_gatekeeper.py:336 _build_overnight_holding_context](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_overnight_gatekeeper.py:336) → `get_tick_history_ka10003`.
  - [src/engine/sniper_overnight_gatekeeper.py:819 _apply_overnight_flow_override](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_overnight_gatekeeper.py:819) → `get_tick_history_ka10003`.
  - [src/engine/sniper_state_handlers.py:32397 _retry_holding_ai_submit_authority_before_block](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:32397) → `get_tick_history_ka10003`.
  - [src/engine/sniper_state_handlers.py:32833 _refresh_scale_in_reversal_features_if_needed](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:32833) → `get_tick_history_ka10003`.
  - [src/engine/sniper_state_handlers.py:41836 _refresh_pre_submit_micro_context_before_block](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:41836) → `get_tick_history_ka10003`.
  - [src/engine/sniper_state_handlers.py:42002 _retry_entry_ai_submit_authority_before_block](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:42002) → `get_tick_history_ka10003`.
  - [src/engine/sniper_state_handlers.py:47610 _apply_entry_ai_price_canary](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:47610) → `get_tick_history_ka10003`.
  - [src/engine/sniper_state_handlers.py:56216 _evaluate_holding_flow_override](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:56216) → `get_tick_history_ka10003`.
  - [src/engine/sniper_state_handlers.py:58663 _opening_rotation_holding_ai_once](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:58663) → `get_tick_history_ka10003`.
  - [src/engine/sniper_state_handlers.py:61672 _resolve_scanner_async_entry_ai.prepare](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:61672) → `get_tick_history_ka10003`.
  - [src/engine/sniper_state_handlers.py:63029 _handle_watching_strategy_branch](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:63029) → `get_tick_history_ka10003`.
  - [src/engine/sniper_state_handlers.py:64885 _handle_watching_strategy_branch](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:64885) → `build_realtime_analysis_context`.
  - [src/engine/sniper_state_handlers.py:85429 handle_holding_state._run_vote_review](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:85429) → `get_tick_history_ka10003`.
  - [src/trading/low_price_two_leg/gateway.py:518 KiwoomLowPriceTwoLegGateway.entry_execution_velocity_snapshot](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/low_price_two_leg/gateway.py:518) → `get_tick_history_ka10003`.
  - [src/trading/samsung_afternoon_one_share/gateway.py:418 KiwoomAfternoonOneShareGateway.entry_execution_velocity_snapshot](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_afternoon_one_share/gateway.py:418) → `get_tick_history_ka10003`.
  - [src/trading/samsung_midday_one_share/gateway.py:416 KiwoomMiddayOneShareGateway.entry_execution_velocity_snapshot](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_midday_one_share/gateway.py:416) → `get_tick_history_ka10003`.
  - [src/trading/samsung_morning_one_share/gateway.py:479 KiwoomOneShareGateway.entry_execution_velocity_snapshot](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_morning_one_share/gateway.py:479) → `get_tick_history_ka10003`.

### ka10004 — 주식호가요청(ka10004)

- 공식 path: `/api/dostk/mrkcond`.
- 공통 헬퍼: `get_stock_orderbook_ka10004`.
- API 상수 참조:
  - [src/engine/monitoring/market_opportunity_census.py:715 _capture_external_bbo_observation](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/monitoring/market_opportunity_census.py:715).
  - [src/engine/monitoring/pruned_candidate_bbo_collector.py:845 PrunedCandidateBBOCollector._collect_and_emit](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/monitoring/pruned_candidate_bbo_collector.py:845).
  - [src/engine/scalping/market_data_enrichment.py:610 build_market_data_enrichment](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/scalping/market_data_enrichment.py:610).
  - [src/engine/sniper_state_handlers.py:75164 _maybe_update_rising_missed_micro_estimator_from_fresh_ws](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:75164).
  - [src/engine/sniper_state_handlers.py:75437 resolve_rising_missed_decision_input](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:75437).
  - [src/engine/sniper_state_handlers.py:75443 resolve_rising_missed_decision_input](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:75443).
  - [src/trading/low_price_two_leg/gateway.py:68 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/low_price_two_leg/gateway.py:68).
  - [src/trading/market/quote_consistency.py:629 build_rest_market_data_health](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/market/quote_consistency.py:629).
  - [src/trading/order/entry_liquidity_guard.py:117 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/entry_liquidity_guard.py:117).
  - [src/trading/samsung_afternoon_one_share/gateway.py:65 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_afternoon_one_share/gateway.py:65).
  - [src/trading/samsung_midday_one_share/gateway.py:65 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_midday_one_share/gateway.py:65).
  - [src/trading/samsung_morning_one_share/gateway.py:70 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_morning_one_share/gateway.py:70).
  - [src/utils/kiwoom_read_request_control.py:80 WidgetMarketResponseCache._complete](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_read_request_control.py:80).
  - [src/utils/kiwoom_read_request_control.py:85 WidgetMarketResponseCache.run](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_read_request_control.py:85).
  - [src/utils/kiwoom_utils.py:3756 get_stock_orderbook_ka10004](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:3756).
  - [src/utils/kiwoom_utils.py:3772 get_stock_orderbook_ka10004](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:3772).
  - [src/utils/kiwoom_utils.py:3791 get_stock_orderbook_ka10004](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:3791).
  - [src/utils/kiwoom_utils.py:3802 get_stock_orderbook_ka10004](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:3802).
  - [src/utils/kiwoom_utils.py:5654 _fetch_kiwoom_api_continuous_transport](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:5654).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/engine/monitoring/market_opportunity_census.py:909 capture_market_snapshots](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/monitoring/market_opportunity_census.py:909) → `get_stock_orderbook_ka10004`.
  - [src/engine/monitoring/pruned_candidate_bbo_collector.py:161 PrunedCandidateBBOCollector.__init__](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/monitoring/pruned_candidate_bbo_collector.py:161) → `get_stock_orderbook_ka10004`.
  - [src/engine/sniper_state_handlers.py:31941 _fetch_rest_orderbook_snapshot_bounded._worker](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:31941) → `get_stock_orderbook_ka10004`.
  - [src/engine/sniper_state_handlers.py:32019 _pre_submit_refresh_rest_orderbook_snapshot](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:32019) → `get_stock_orderbook_ka10004`.
  - [src/trading/low_price_two_leg/gateway.py:496 KiwoomLowPriceTwoLegGateway.entry_liquidity_snapshot](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/low_price_two_leg/gateway.py:496) → `get_stock_orderbook_ka10004`.
  - [src/trading/samsung_afternoon_one_share/gateway.py:396 KiwoomAfternoonOneShareGateway.entry_liquidity_snapshot](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_afternoon_one_share/gateway.py:396) → `get_stock_orderbook_ka10004`.
  - [src/trading/samsung_midday_one_share/gateway.py:394 KiwoomMiddayOneShareGateway.entry_liquidity_snapshot](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_midday_one_share/gateway.py:394) → `get_stock_orderbook_ka10004`.
  - [src/trading/samsung_morning_one_share/gateway.py:457 KiwoomOneShareGateway.entry_liquidity_snapshot](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_morning_one_share/gateway.py:457) → `get_stock_orderbook_ka10004`.

### ka10005 — 주식일주월시분요청(ka10005)

- 공식 path: `/api/dostk/mrkcond`.
- 공통 헬퍼: `get_daily_data_ka10005_df`.
- API 상수 참조:
  - [src/utils/kiwoom_utils.py:2780 get_daily_data_ka10005_df](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:2780).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/engine/scalping/ai_input_external_validation.py:1437 build_live_report](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/scalping/ai_input_external_validation.py:1437) → `get_daily_data_ka10005_df`.
  - [src/engine/scalping/multi_timeframe_context.py:447 _previous_day_source](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/scalping/multi_timeframe_context.py:447) → `get_daily_data_ka10005_df`.

### ka10013 — 신용매매동향요청(ka10013)

- 공식 path: `/api/dostk/stkinfo`.
- 공통 헬퍼: `get_margin_daily_ka10013_df`.
- API 상수 참조:
  - [src/utils/kiwoom_utils.py:2952 get_margin_daily_ka10013_df](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:2952).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/scanners/kosdaq_scanner.py:187 run_kosdaq_scanner](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/scanners/kosdaq_scanner.py:187) → `get_margin_daily_ka10013_df`.
  - [src/utils/update_kospi.py:399 process_and_save_stock](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/update_kospi.py:399) → `get_margin_daily_ka10013_df`.

### ka10016 — 신고저가요청(ka10016)

- 공식 path: `/api/dostk/stkinfo`.
- 공통 헬퍼: `get_new_high_ka10016`.
- API 상수 참조:
  - [src/utils/kiwoom_utils.py:3622 get_new_high_ka10016](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:3622).
  - [src/utils/kiwoom_utils.py:3634 get_new_high_ka10016](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:3634).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/scanners/scalping_scanner.py:6746 run_scalper_iteration](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/scanners/scalping_scanner.py:6746) → `get_new_high_ka10016`.

### ka10018 — 고저가근접요청(ka10018)

- 공식 path: `/api/dostk/stkinfo`.
- 공통 헬퍼: `get_high_price_proximity_ka10018`.
- API 상수 참조:
  - [src/utils/kiwoom_utils.py:3553 get_high_price_proximity_ka10018](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:3553).
  - [src/utils/kiwoom_utils.py:3565 get_high_price_proximity_ka10018](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:3565).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/scanners/scalping_scanner.py:6733 run_scalper_iteration](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/scanners/scalping_scanner.py:6733) → `get_high_price_proximity_ka10018`.

### ka10019 — 가격급등락요청(ka10019)

- 공식 path: `/api/dostk/stkinfo`.
- 공통 헬퍼: `get_price_jump_ka10019`.
- API 상수 참조:
  - [src/utils/kiwoom_utils.py:3495 get_price_jump_ka10019](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:3495).
  - [src/utils/kiwoom_utils.py:3507 get_price_jump_ka10019](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:3507).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/scanners/scalping_scanner.py:6702 run_scalper_iteration](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/scanners/scalping_scanner.py:6702) → `get_price_jump_ka10019`.

### ka10021 — 호가잔량급증요청(ka10021)

- 공식 path: `/api/dostk/rkinfo`.
- 공통 헬퍼: `get_bid_balance_surge_ka10021`, `scan_orderbook_spike_ka10021`.
- API 상수 참조:
  - [src/utils/kiwoom_utils.py:3938 get_bid_balance_surge_ka10021](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:3938).
  - [src/utils/kiwoom_utils.py:3950 get_bid_balance_surge_ka10021](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:3950).
  - [src/utils/kiwoom_utils.py:4228 scan_orderbook_spike_ka10021](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:4228).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/scanners/scalping_scanner.py:6725 run_scalper_iteration](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/scanners/scalping_scanner.py:6725) → `get_bid_balance_surge_ka10021`.

### ka10023 — 거래량급증요청(ka10023)

- 공식 path: `/api/dostk/rkinfo`.
- 공통 헬퍼: `get_positive_volume_surge_ka10023`, `get_zero_base_volume_surge_ka10023`, `scan_volume_spike_ka10023`.
- API 상수 참조:
  - [src/utils/kiwoom_utils.py:4077 get_zero_base_volume_surge_ka10023](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:4077).
  - [src/utils/kiwoom_utils.py:4106 get_zero_base_volume_surge_ka10023](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:4106).
  - [src/utils/kiwoom_utils.py:4147 scan_volume_spike_ka10023](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:4147).
  - [src/utils/kiwoom_utils.py:4157 scan_volume_spike_ka10023](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:4157).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/engine/signal_radar.py:104 SniperRadar.find_supernova_targets](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/signal_radar.py:104) → `scan_volume_spike_ka10023`.
  - [src/scanners/kosdaq_scanner.py:135 run_kosdaq_scanner](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/scanners/kosdaq_scanner.py:135) → `scan_volume_spike_ka10023`.
  - [src/scanners/scalping_scanner.py:6715 run_scalper_iteration](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/scanners/scalping_scanner.py:6715) → `scan_volume_spike_ka10023`.
  - [src/scanners/zero_base_discovery_source.py:64 fetch_discovery_panels](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/scanners/zero_base_discovery_source.py:64) → `get_zero_base_volume_surge_ka10023`.

### ka10027 — 전일대비등락률상위요청(ka10027)

- 공식 path: `/api/dostk/rkinfo`.
- 공통 헬퍼: `get_top_fluctuation_ka10027`.
- API 상수 참조:
  - [src/engine/monitoring/market_opportunity_census.py:976 capture_market_snapshots](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/monitoring/market_opportunity_census.py:976).
  - [src/engine/monitoring/market_opportunity_census.py:1237 capture_market_snapshots](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/monitoring/market_opportunity_census.py:1237).
  - [src/utils/kiwoom_utils.py:3012 get_top_fluctuation_ka10027](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:3012).
  - [src/utils/kiwoom_utils.py:3042 get_top_fluctuation_ka10027](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:3042).
  - [src/utils/kiwoom_utils.py:3060 get_top_fluctuation_ka10027](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:3060).
  - [src/utils/kiwoom_utils.py:3108 get_top_fluctuation_ka10027](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:3108).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/engine/monitoring/market_opportunity_census.py:908 capture_market_snapshots](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/monitoring/market_opportunity_census.py:908) → `get_top_fluctuation_ka10027`.
  - [src/scanners/scalping_scanner.py:6651 run_scalper_iteration](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/scanners/scalping_scanner.py:6651) → `get_top_fluctuation_ka10027`.
  - [src/scanners/zero_base_discovery_source.py:63 fetch_discovery_panels](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/scanners/zero_base_discovery_source.py:63) → `get_top_fluctuation_ka10027`.

### ka10028 — 시가대비등락률요청(ka10028)

- 공식 path: `/api/dostk/stkinfo`.
- 공통 헬퍼: `get_top_open_fluctuation_ka10028`.
- API 상수 참조:
  - [src/utils/kiwoom_utils.py:3172 get_top_open_fluctuation_ka10028](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:3172).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/scanners/kosdaq_scanner.py:132 run_kosdaq_scanner](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/scanners/kosdaq_scanner.py:132) → `get_top_open_fluctuation_ka10028`.
  - [src/scanners/scalping_scanner.py:6759 run_scalper_iteration](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/scanners/scalping_scanner.py:6759) → `get_top_open_fluctuation_ka10028`.

### ka10032 — 거래대금상위요청(ka10032)

- 공식 path: `/api/dostk/rkinfo`.
- 공통 헬퍼: `get_value_top_ka10032`.
- API 상수 참조:
  - [src/utils/kiwoom_utils.py:3679 get_value_top_ka10032](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:3679).
  - [src/utils/kiwoom_utils.py:3700 get_value_top_ka10032](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:3700).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/scanners/scalping_scanner.py:6766 run_scalper_iteration](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/scanners/scalping_scanner.py:6766) → `get_value_top_ka10032`.

### ka10046 — 체결강도추이시간별요청(ka10046)

- 공식 path: `/api/dostk/mrkcond`.
- 공통 헬퍼: `build_realtime_analysis_context`, `check_execution_strength_ka10046`.
- API 상수 참조:
  - [src/utils/kiwoom_utils.py:52 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:52).
  - [src/utils/kiwoom_utils.py:4400 check_execution_strength_ka10046](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:4400).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/engine/signal_radar.py:124 SniperRadar.find_supernova_targets](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/signal_radar.py:124) → `check_execution_strength_ka10046`.
  - [src/engine/sniper_overnight_gatekeeper.py:273 _build_scalping_overnight_ctx](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_overnight_gatekeeper.py:273) → `build_realtime_analysis_context`.
  - [src/engine/sniper_state_handlers.py:64885 _handle_watching_strategy_branch](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:64885) → `build_realtime_analysis_context`.

### ka10054 — 변동성완화장치발동종목요청(ka10054)

- 공식 path: `/api/dostk/stkinfo`.
- 공통 헬퍼: `get_vi_triggered_ka10054`.
- API 상수 참조:
  - [src/utils/kiwoom_utils.py:3999 get_vi_triggered_ka10054](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:3999).
  - [src/utils/kiwoom_utils.py:4019 get_vi_triggered_ka10054](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:4019).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/scanners/scalping_scanner.py:6773 run_scalper_iteration](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/scanners/scalping_scanner.py:6773) → `get_vi_triggered_ka10054`.

### ka10059 — 종목별투자자기관별요청(ka10059)

- 공식 path: `/api/dostk/stkinfo`.
- 공통 헬퍼: `build_realtime_analysis_context`, `get_investor_daily_ka10059_df`, `get_investor_flow_summary_ka10059`.
- API 상수 참조:
  - [src/engine/institutional_flow_context.py:186 normalize_institutional_flow_context](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/institutional_flow_context.py:186).
  - [src/engine/institutional_flow_context.py:205 normalize_institutional_flow_context](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/institutional_flow_context.py:205).
  - [src/utils/kiwoom_utils.py:53 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:53).
  - [src/utils/kiwoom_utils.py:2864 get_investor_daily_ka10059_df](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:2864).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/engine/institutional_flow_context.py:254 resolve_institutional_flow_context](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/institutional_flow_context.py:254) → `get_investor_flow_summary_ka10059`.
  - [src/engine/scalping/ai_market_snapshot.py:377 enrich_investor_source](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/scalping/ai_market_snapshot.py:377) → `get_investor_daily_ka10059_df`.
  - [src/engine/scalping/ai_market_snapshot.py:381 enrich_investor_source](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/scalping/ai_market_snapshot.py:381) → `get_investor_flow_summary_ka10059`.
  - [src/engine/sniper_analysis.py:196 analyze_stock_now](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_analysis.py:196) → `get_investor_daily_ka10059_df`.
  - [src/engine/sniper_overnight_gatekeeper.py:273 _build_scalping_overnight_ctx](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_overnight_gatekeeper.py:273) → `build_realtime_analysis_context`.
  - [src/engine/sniper_state_handlers.py:64885 _handle_watching_strategy_branch](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:64885) → `build_realtime_analysis_context`.
  - [src/scanners/kosdaq_scanner.py:186 run_kosdaq_scanner](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/scanners/kosdaq_scanner.py:186) → `get_investor_daily_ka10059_df`.
  - [src/utils/update_kospi.py:393 process_and_save_stock](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/update_kospi.py:393) → `get_investor_daily_ka10059_df`.

### ka10061 — 종목별투자자기관별합계요청(ka10061)

- 공식 path: `/api/dostk/stkinfo`.
- 공통 헬퍼: `get_investor_period_total_ka10061`.
- API 상수 참조:
  - [src/engine/institutional_flow_context.py:188 normalize_institutional_flow_context](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/institutional_flow_context.py:188).
  - [src/engine/institutional_flow_context.py:205 normalize_institutional_flow_context](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/institutional_flow_context.py:205).
  - [src/utils/kiwoom_utils.py:54 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:54).
  - [src/utils/kiwoom_utils.py:5940 get_investor_period_total_ka10061](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:5940).
  - [src/utils/kiwoom_utils.py:5948 get_investor_period_total_ka10061](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:5948).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/engine/institutional_flow_context.py:257 resolve_institutional_flow_context](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/institutional_flow_context.py:257) → `get_investor_period_total_ka10061`.

### ka10063 — 장중투자자별매매요청(ka10063)

- 공식 path: `/api/dostk/mrkcond`.
- 공통 헬퍼: `get_intraday_investor_trade_ka10063`.
- API 상수 참조:
  - [src/utils/kiwoom_utils.py:55 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:55).
  - [src/utils/kiwoom_utils.py:6001 get_intraday_investor_trade_ka10063](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:6001).
  - [src/utils/kiwoom_utils.py:6012 get_intraday_investor_trade_ka10063](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:6012).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - AST에서 미발견. 실행 여부 0의 완전한 증명으로 사용하지 않음.

### ka10064 — 장중투자자별매매차트요청(ka10064)

- 공식 path: `/api/dostk/chart`.
- 공통 헬퍼: `get_intraday_investor_chart_ka10064`.
- API 상수 참조:
  - [src/engine/institutional_flow_context.py:190 normalize_institutional_flow_context](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/institutional_flow_context.py:190).
  - [src/utils/kiwoom_utils.py:56 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:56).
  - [src/utils/kiwoom_utils.py:6052 get_intraday_investor_chart_ka10064](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:6052).
  - [src/utils/kiwoom_utils.py:6061 get_intraday_investor_chart_ka10064](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:6061).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/engine/institutional_flow_context.py:263 resolve_institutional_flow_context](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/institutional_flow_context.py:263) → `get_intraday_investor_chart_ka10064`.
  - [src/engine/institutional_flow_context.py:266 resolve_institutional_flow_context](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/institutional_flow_context.py:266) → `get_intraday_investor_chart_ka10064`.

### ka10066 — 장마감후투자자별매매요청(ka10066)

- 공식 path: `/api/dostk/mrkcond`.
- 공통 헬퍼: `get_postclose_investor_trade_ka10066`.
- API 상수 참조:
  - [src/utils/kiwoom_utils.py:57 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:57).
  - [src/utils/kiwoom_utils.py:6094 get_postclose_investor_trade_ka10066](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:6094).
  - [src/utils/kiwoom_utils.py:6106 get_postclose_investor_trade_ka10066](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:6106).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - AST에서 미발견. 실행 여부 0의 완전한 증명으로 사용하지 않음.

### ka10073 — 일자별종목별실현손익요청_기간(ka10073)

- 공식 path: `/api/dostk/acnt`.
- 공통 헬퍼: 별도 직접 producer/adapter.
- API 상수 참조:
  - [src/engine/monitoring/low_price_two_leg_tuning.py:411 load_realized_pnl_ka10073](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/monitoring/low_price_two_leg_tuning.py:411).
  - [src/engine/monitoring/low_price_two_leg_tuning.py:447 load_realized_pnl_ka10073](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/monitoring/low_price_two_leg_tuning.py:447).
  - [src/engine/monitoring/low_price_two_leg_tuning.py:645 _apply_broker_realized_economics](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/monitoring/low_price_two_leg_tuning.py:645).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - AST에서 미발견. 실행 여부 0의 완전한 증명으로 사용하지 않음.

### ka10075 — 미체결요청(ka10075)

- 공식 path: `/api/dostk/acnt`.
- 공통 헬퍼: `get_unfilled_order_snapshot_ka10075`, `get_unfilled_order_snapshot_ka10075_with_meta`.
- API 상수 참조:
  - [src/engine/scalping/initial_quantity_terminal.py:108 prove_initial_buy_leg_open](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/scalping/initial_quantity_terminal.py:108).
  - [src/engine/sniper_trade_utils.py:395 resolve_pending_sell_order_no](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_trade_utils.py:395).
  - [src/trading/low_price_two_leg/gateway.py:81 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/low_price_two_leg/gateway.py:81).
  - [src/trading/order/adaptive_exit/broker.py:300 RegisteredSellAdapter._snapshot](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/adaptive_exit/broker.py:300).
  - [src/trading/order/aftermarket_reconciliation.py:18 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/aftermarket_reconciliation.py:18).
  - [src/trading/order/kiwoom_episode_read_control.py:29 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/kiwoom_episode_read_control.py:29).
  - [src/trading/order/owner_custody_registry.py:75 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/owner_custody_registry.py:75).
  - [src/trading/order/target_amend.py:51 reconcile_amendment](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/target_amend.py:51).
  - [src/utils/kiwoom_utils.py:1450 _normalize_order_history_rows](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:1450).
  - [src/utils/kiwoom_utils.py:1598 _order_snapshot_contract_meta](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:1598).
  - [src/utils/kiwoom_utils.py:1824 get_unfilled_order_snapshot_ka10075](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:1824).
  - [src/utils/kiwoom_utils.py:1828 get_unfilled_order_snapshot_ka10075](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:1828).
  - [src/utils/kiwoom_utils.py:1858 get_unfilled_order_snapshot_ka10075_with_meta](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:1858).
  - [src/utils/kiwoom_utils.py:1862 get_unfilled_order_snapshot_ka10075_with_meta](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:1862).
  - [src/utils/kiwoom_utils.py:1867 get_unfilled_order_snapshot_ka10075_with_meta](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:1867).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/engine/scalping/initial_quantity_terminal.py:153 read_initial_buy_leg_open](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/scalping/initial_quantity_terminal.py:153) → `get_unfilled_order_snapshot_ka10075_with_meta`.
  - [src/engine/scalping/initial_quantity_terminal.py:191 read_initial_buy_leg_terminal_discover](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/scalping/initial_quantity_terminal.py:191) → `get_unfilled_order_snapshot_ka10075_with_meta`.
  - [src/engine/scalping/initial_quantity_terminal.py:366 read_initial_buy_leg_terminal](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/scalping/initial_quantity_terminal.py:366) → `get_unfilled_order_snapshot_ka10075_with_meta`.
  - [src/engine/sniper_s15_fast_track.py:510 _s15_inventory_and_orders](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_s15_fast_track.py:510) → `get_unfilled_order_snapshot_ka10075_with_meta`.
  - [src/engine/sniper_state_handlers.py:76964 _resolve_entry_cancel_exchange_from_unfilled_snapshot](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:76964) → `get_unfilled_order_snapshot_ka10075`.
  - [src/engine/sniper_state_handlers.py:77095 _order_terminal_inventory_reconciliation](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:77095) → `get_unfilled_order_snapshot_ka10075_with_meta`.
  - [src/engine/sniper_state_handlers.py:89477 _pending_add_blocks_sell_dispatch](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:89477) → `get_unfilled_order_snapshot_ka10075_with_meta`.
  - [src/engine/sniper_state_handlers.py:93022 _sell_order_terminal_absence_confirmed](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:93022) → `get_unfilled_order_snapshot_ka10075_with_meta`.
  - [src/engine/sniper_sync.py:1486 sync_balance_with_db](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_sync.py:1486) → `get_unfilled_order_snapshot_ka10075_with_meta`.
  - [src/engine/sniper_sync.py:2369 refresh_broker_account_snapshot_read_only](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_sync.py:2369) → `get_unfilled_order_snapshot_ka10075_with_meta`.
  - [src/engine/sniper_sync.py:2597 periodic_account_sync](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_sync.py:2597) → `get_unfilled_order_snapshot_ka10075_with_meta`.
  - [src/engine/sniper_trade_utils.py:331 resolve_pending_sell_order_no](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_trade_utils.py:331) → `get_unfilled_order_snapshot_ka10075_with_meta`.
  - [src/engine/sniper_trade_utils.py:648 _resolve_cancel_exchange_from_unfilled_snapshot](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_trade_utils.py:648) → `get_unfilled_order_snapshot_ka10075`.
  - [src/engine/sniper_trade_utils.py:728 _cancelled_sell_order_absence_confirmed](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_trade_utils.py:728) → `get_unfilled_order_snapshot_ka10075_with_meta`.
  - [src/trading/order/symbol_owner_policy_apply.py:338 collect_broker_snapshot](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/symbol_owner_policy_apply.py:338) → `get_unfilled_order_snapshot_ka10075_with_meta`.

### ka10076 — 체결요청(ka10076)

- 공식 path: `/api/dostk/acnt`.
- 공통 헬퍼: `get_order_reference_snapshot_2nd_pass`, `get_order_reference_snapshot_ka10076`.
- API 상수 참조:
  - [src/utils/kiwoom_utils.py:1788 get_order_reference_snapshot_ka10076](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:1788).
  - [src/utils/kiwoom_utils.py:1792 get_order_reference_snapshot_ka10076](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:1792).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/engine/sniper_sync.py:761 _recover_missing_broker_holdings](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_sync.py:761) → `get_order_reference_snapshot_2nd_pass`.

### ka10080 — 주식분봉차트조회요청(ka10080)

- 공식 path: `/api/dostk/chart`.
- 공통 헬퍼: `build_realtime_analysis_context`, `get_minute_candles_ka10080`, `get_minute_candles_ka10080_with_meta`.
- API 상수 참조:
  - [src/engine/monitoring/low_price_two_leg_entry_spot_research.py:387 fetch_sor_history](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/monitoring/low_price_two_leg_entry_spot_research.py:387).
  - [src/engine/monitoring/low_price_two_leg_entry_spot_research.py:412 fetch_sor_history](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/monitoring/low_price_two_leg_entry_spot_research.py:412).
  - [src/engine/monitoring/low_price_two_leg_entry_spot_research.py:434 fetch_sor_history](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/monitoring/low_price_two_leg_entry_spot_research.py:434).
  - [src/engine/monitoring/low_price_two_leg_entry_spot_research.py:522 fetch_sor_history](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/monitoring/low_price_two_leg_entry_spot_research.py:522).
  - [src/engine/monitoring/low_price_two_leg_expanded_candidate_research.py:3037 _source_cache_contract](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/monitoring/low_price_two_leg_expanded_candidate_research.py:3037).
  - [src/engine/monitoring/pure_market_kiwoom_backfill.py:280 _normalize_row](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/monitoring/pure_market_kiwoom_backfill.py:280).
  - [src/engine/monitoring/pure_market_kiwoom_backfill.py:401 fetch_ka10080_history](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/monitoring/pure_market_kiwoom_backfill.py:401).
  - [src/engine/monitoring/pure_market_kiwoom_backfill.py:411 fetch_ka10080_history](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/monitoring/pure_market_kiwoom_backfill.py:411).
  - [src/engine/monitoring/pure_market_kiwoom_backfill.py:425 fetch_ka10080_history](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/monitoring/pure_market_kiwoom_backfill.py:425).
  - [src/engine/monitoring/pure_market_kiwoom_backfill.py:432 fetch_ka10080_history](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/monitoring/pure_market_kiwoom_backfill.py:432).
  - [src/engine/monitoring/pure_market_kiwoom_backfill.py:437 fetch_ka10080_history](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/monitoring/pure_market_kiwoom_backfill.py:437).
  - [src/engine/scalping/ai_action_outcome_calibration.py:4603 _machine_completed_price_rows_locked](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/scalping/ai_action_outcome_calibration.py:4603).
  - [src/engine/scalping/ai_action_outcome_calibration.py:4658 _machine_completed_price_rows_locked.verified_fetcher](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/scalping/ai_action_outcome_calibration.py:4658).
  - [src/engine/scalping/ai_action_outcome_calibration.py:4695 _machine_completed_price_rows_locked](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/scalping/ai_action_outcome_calibration.py:4695).
  - [src/engine/scalping/ai_decision_quality.py:4084 load_kiwoom_completed_minute_price_rows](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/scalping/ai_decision_quality.py:4084).
  - [src/engine/scalping/ai_decision_quality.py:4156 load_kiwoom_completed_minute_price_rows](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/scalping/ai_decision_quality.py:4156).
  - [src/engine/scalping/ai_decision_quality.py:4170 load_kiwoom_completed_minute_price_rows](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/scalping/ai_decision_quality.py:4170).
  - [src/engine/scalping/ai_decision_quality.py:4211 _postclose_ai_completed_fetcher.fetch](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/scalping/ai_decision_quality.py:4211).
  - [src/engine/scalping/entry_candle_context.py:1312 build_session_candle_source](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/scalping/entry_candle_context.py:1312).
  - [src/engine/scalping/initial_quantity_following_bars.py:140 build_following_bar_source](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/scalping/initial_quantity_following_bars.py:140).
  - [src/engine/scalping/initial_quantity_following_bars.py:145 build_following_bar_source](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/scalping/initial_quantity_following_bars.py:145).
  - [src/engine/scalping/market_context_observation.py:536 derive_scalping_market_features](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/scalping/market_context_observation.py:536).
  - [src/engine/sniper_missed_entry_counterfactual.py:243 _minute_candle_meta](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_missed_entry_counterfactual.py:243).
  - [src/engine/sniper_post_sell_feedback.py:164 _minute_candle_meta](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_post_sell_feedback.py:164).
  - [src/engine/wait6579_ev_cohort_report.py:119 _minute_candle_meta](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/wait6579_ev_cohort_report.py:119).
  - [src/trading/low_price_two_leg/gateway.py:62 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/low_price_two_leg/gateway.py:62).
  - [src/trading/low_price_two_leg/gateway.py:396 KiwoomLowPriceTwoLegGateway.completed_sor_minute_bars.seed_fetch](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/low_price_two_leg/gateway.py:396).
  - [src/trading/low_price_two_leg/gateway.py:420 KiwoomLowPriceTwoLegGateway.completed_sor_minute_bars](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/low_price_two_leg/gateway.py:420).
  - [src/trading/order/kiwoom_episode_read_control.py:28 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/kiwoom_episode_read_control.py:28).
  - [src/trading/samsung_afternoon_one_share/gateway.py:59 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_afternoon_one_share/gateway.py:59).
  - [src/trading/samsung_afternoon_one_share/gateway.py:299 KiwoomAfternoonOneShareGateway.completed_sor_minute_bars.seed_fetch](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_afternoon_one_share/gateway.py:299).
  - [src/trading/samsung_afternoon_one_share/gateway.py:323 KiwoomAfternoonOneShareGateway.completed_sor_minute_bars](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_afternoon_one_share/gateway.py:323).
  - [src/trading/samsung_midday_one_share/gateway.py:59 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_midday_one_share/gateway.py:59).
  - [src/trading/samsung_midday_one_share/gateway.py:297 KiwoomMiddayOneShareGateway.completed_sor_minute_bars.seed_fetch](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_midday_one_share/gateway.py:297).
  - [src/trading/samsung_midday_one_share/gateway.py:321 KiwoomMiddayOneShareGateway.completed_sor_minute_bars](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_midday_one_share/gateway.py:321).
  - [src/trading/samsung_morning_one_share/gateway.py:64 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_morning_one_share/gateway.py:64).
  - [src/trading/samsung_morning_one_share/gateway.py:325 KiwoomOneShareGateway.opening_price](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_morning_one_share/gateway.py:325).
  - [src/trading/samsung_morning_one_share/gateway.py:364 KiwoomOneShareGateway.completed_sor_minute_bars.seed_fetch](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_morning_one_share/gateway.py:364).
  - [src/trading/samsung_morning_one_share/gateway.py:388 KiwoomOneShareGateway.completed_sor_minute_bars](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_morning_one_share/gateway.py:388).
  - [src/utils/kiwoom_read_request_control.py:71 WidgetMarketResponseCache._complete](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_read_request_control.py:71).
  - [src/utils/kiwoom_read_request_control.py:86 WidgetMarketResponseCache.run](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_read_request_control.py:86).
  - [src/utils/kiwoom_read_request_control.py:203 SharedCandleRead._valid](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_read_request_control.py:203).
  - [src/utils/kiwoom_read_request_control.py:204 SharedCandleRead._valid](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_read_request_control.py:204).
  - [src/utils/kiwoom_utils.py:58 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:58).
  - [src/utils/kiwoom_utils.py:163 _cache_get](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:163).
  - [src/utils/kiwoom_utils.py:5037 get_minute_candles_ka10080_with_meta](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:5037).
  - [src/utils/kiwoom_utils.py:5044 get_minute_candles_ka10080_with_meta](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:5044).
  - [src/utils/kiwoom_utils.py:5232 fetch_kiwoom_api_continuous.fetch_market_read](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:5232).
  - [src/utils/kiwoom_utils.py:5241 fetch_kiwoom_api_continuous.fetch_market_read](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:5241).
  - [src/utils/kiwoom_utils.py:5262 fetch_kiwoom_api_continuous.scoped_market_read](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:5262).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/engine/scalping/ai_action_outcome_calibration.py:4761 _postclose_machine_completed_fetcher.fetcher](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/scalping/ai_action_outcome_calibration.py:4761) → `get_minute_candles_ka10080_with_meta`.
  - [src/engine/scalping/ai_decision_quality.py:4204 _postclose_ai_completed_fetcher.fetch](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/scalping/ai_decision_quality.py:4204) → `get_minute_candles_ka10080_with_meta`.
  - [src/engine/scalping/ai_input_external_validation.py:1423 build_live_report._route_minutes](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/scalping/ai_input_external_validation.py:1423) → `get_minute_candles_ka10080_with_meta`.
  - [src/engine/scalping/entry_candle_context.py:362 fetch_entry_candles_with_meta](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/scalping/entry_candle_context.py:362) → `get_minute_candles_ka10080_with_meta`.
  - [src/engine/scalping/initial_quantity_following_bars.py:360 main.fetch](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/scalping/initial_quantity_following_bars.py:360) → `get_minute_candles_ka10080_with_meta`.
  - [src/engine/scalping/initial_quantity_policy.py:2772 main.fetch](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/scalping/initial_quantity_policy.py:2772) → `get_minute_candles_ka10080_with_meta`.
  - [src/engine/sniper_condition_handlers.py:358 _get_latest_price](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_condition_handlers.py:358) → `get_minute_candles_ka10080`.
  - [src/engine/sniper_condition_handlers.py:378 _get_latest_open_and_vwap](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_condition_handlers.py:378) → `get_minute_candles_ka10080`.
  - [src/engine/sniper_condition_handlers.py:473 _is_3min_ma20_broken](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_condition_handlers.py:473) → `get_minute_candles_ka10080`.
  - [src/engine/sniper_missed_entry_counterfactual.py:264 _fetch_minute_candles_with_meta](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_missed_entry_counterfactual.py:264) → `get_minute_candles_ka10080_with_meta`.
  - [src/engine/sniper_missed_entry_counterfactual.py:269 _fetch_minute_candles_with_meta](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_missed_entry_counterfactual.py:269) → `get_minute_candles_ka10080`.
  - [src/engine/sniper_overnight_gatekeeper.py:273 _build_scalping_overnight_ctx](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_overnight_gatekeeper.py:273) → `build_realtime_analysis_context`.
  - [src/engine/sniper_overnight_gatekeeper.py:341 _build_overnight_holding_context](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_overnight_gatekeeper.py:341) → `get_minute_candles_ka10080_with_meta`.
  - [src/engine/sniper_overnight_gatekeeper.py:822 _apply_overnight_flow_override](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_overnight_gatekeeper.py:822) → `get_minute_candles_ka10080`.
  - [src/engine/sniper_post_sell_feedback.py:185 _fetch_minute_candles_with_meta](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_post_sell_feedback.py:185) → `get_minute_candles_ka10080_with_meta`.
  - [src/engine/sniper_post_sell_feedback.py:190 _fetch_minute_candles_with_meta](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_post_sell_feedback.py:190) → `get_minute_candles_ka10080`.
  - [src/engine/sniper_state_handlers.py:25828 _get_holding_minute_candles_with_meta](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:25828) → `get_minute_candles_ka10080`.
  - [src/engine/sniper_state_handlers.py:25844 _get_holding_minute_candles_with_meta](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:25844) → `get_minute_candles_ka10080_with_meta`.
  - [src/engine/sniper_state_handlers.py:32846 _refresh_scale_in_reversal_features_if_needed](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:32846) → `get_minute_candles_ka10080`.
  - [src/engine/sniper_state_handlers.py:41844 _refresh_pre_submit_micro_context_before_block](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:41844) → `get_minute_candles_ka10080`.
  - [src/engine/sniper_state_handlers.py:59541 _fetch_opening_rotation_candles_bounded._worker](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:59541) → `get_minute_candles_ka10080`.
  - [src/engine/sniper_state_handlers.py:59895 _opening_rotation_feature_packet](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:59895) → `get_minute_candles_ka10080`.
  - [src/engine/sniper_state_handlers.py:64885 _handle_watching_strategy_branch](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:64885) → `build_realtime_analysis_context`.
  - [src/engine/sniper_strength_shadow_feedback.py:274 evaluate_shadow_candidates](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_strength_shadow_feedback.py:274) → `get_minute_candles_ka10080`.
  - [src/engine/wait6579_ev_cohort_report.py:140 _fetch_minute_candles_with_meta](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/wait6579_ev_cohort_report.py:140) → `get_minute_candles_ka10080_with_meta`.
  - [src/engine/wait6579_ev_cohort_report.py:145 _fetch_minute_candles_with_meta](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/wait6579_ev_cohort_report.py:145) → `get_minute_candles_ka10080`.
  - [src/scanners/scalping_scanner.py:6353 _build_low_rebound_rising_missed_targets](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/scanners/scalping_scanner.py:6353) → `get_minute_candles_ka10080`.

### ka10081 — 주식일봉차트조회요청(ka10081)

- 공식 path: `/api/dostk/chart`.
- 공통 헬퍼: `build_realtime_analysis_context`, `get_daily_ohlcv_ka10081_df`.
- API 상수 참조:
  - [src/utils/kiwoom_utils.py:59 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:59).
  - [src/utils/kiwoom_utils.py:2508 get_daily_ohlcv_ka10081_df](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:2508).
  - [src/utils/kiwoom_utils.py:2513 get_daily_ohlcv_ka10081_df](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:2513).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/engine/sniper_overnight_gatekeeper.py:273 _build_scalping_overnight_ctx](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_overnight_gatekeeper.py:273) → `build_realtime_analysis_context`.
  - [src/engine/sniper_state_handlers.py:64885 _handle_watching_strategy_branch](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:64885) → `build_realtime_analysis_context`.
  - [src/scanners/kosdaq_scanner.py:179 run_kosdaq_scanner](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/scanners/kosdaq_scanner.py:179) → `get_daily_ohlcv_ka10081_df`.
  - [src/utils/update_kospi.py:387 process_and_save_stock](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/update_kospi.py:387) → `get_daily_ohlcv_ka10081_df`.

### ka10084 — 당일전일체결요청(ka10084)

- 공식 path: `/api/dostk/stkinfo`.
- 공통 헬퍼: `get_recent_signed_trades_ka10084`.
- API 상수 참조:
  - [src/engine/scalping/market_data_enrichment.py:612 build_market_data_enrichment](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/scalping/market_data_enrichment.py:612).
  - [src/engine/sniper_entry_latency.py:1812 _latency_signed_tape_fields](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_entry_latency.py:1812).
  - [src/engine/sniper_state_handlers.py:40006 _rising_missed_quality_guard_pre_envelope](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:40006).
  - [src/engine/sniper_state_handlers.py:40007 _rising_missed_quality_guard_pre_envelope](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:40007).
  - [src/utils/kiwoom_utils.py:60 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:60).
  - [src/utils/kiwoom_utils.py:4888 get_recent_signed_trades_ka10084](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:4888).
  - [src/utils/kiwoom_utils.py:4907 get_recent_signed_trades_ka10084](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:4907).
  - [src/utils/kiwoom_utils.py:4915 get_recent_signed_trades_ka10084](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:4915).
  - [src/utils/kiwoom_utils.py:4946 get_recent_signed_trades_ka10084](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:4946).
  - [src/utils/kiwoom_utils.py:4955 get_recent_signed_trades_ka10084](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:4955).
  - [src/utils/kiwoom_utils.py:4965 get_recent_signed_trades_ka10084](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:4965).
  - [src/utils/kiwoom_utils.py:5654 _fetch_kiwoom_api_continuous_transport](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:5654).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/engine/scalping/holding_decision_context.py:480 _bounded_rest_signed_tape](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/scalping/holding_decision_context.py:480) → `get_recent_signed_trades_ka10084`.
  - [src/engine/sniper_state_handlers.py:39636 _fetch_rising_missed_signed_tape_bounded._worker](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:39636) → `get_recent_signed_trades_ka10084`.

### ka10099 — 종목정보 리스트(ka10099)

- 공식 path: `/api/dostk/stkinfo`.
- 공통 헬퍼: `get_nxt_enabled_codes_ka10099`, `get_nxt_flag_map_ka10099`, `get_stock_eligibility_map_ka10099`.
- API 상수 참조:
  - [src/utils/kiwoom_utils.py:2034 get_nxt_enabled_codes_ka10099](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:2034).
  - [src/utils/kiwoom_utils.py:2112 get_stock_eligibility_map_ka10099](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:2112).
  - [src/utils/kiwoom_utils.py:2131 get_stock_eligibility_map_ka10099](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:2131).
  - [src/utils/kiwoom_utils.py:2228 get_stock_eligibility_map_ka10099](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:2228).
  - [src/utils/kiwoom_utils.py:2277 get_stock_eligibility_map_ka10099](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:2277).
  - [src/utils/kiwoom_utils.py:2303 get_stock_eligibility_map_ka10099](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:2303).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/utils/update_kospi.py:355 _collect_and_store_market_eligibility](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/update_kospi.py:355) → `get_stock_eligibility_map_ka10099`.

### ka10100 — 종목정보 조회(ka10100)

- 공식 path: `/api/dostk/stkinfo`.
- 공통 헬퍼: `get_item_info_ka10100`.
- API 상수 참조:
  - [src/utils/kiwoom_utils.py:2600 get_item_info_ka10100](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:2600).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - AST에서 미발견. 실행 여부 0의 완전한 증명으로 사용하지 않음.

### ka10101 — 업종코드 리스트(ka10101)

- 공식 path: `/api/dostk/stkinfo`.
- 공통 헬퍼: `get_industry_list_ka10101`.
- API 상수 참조:
  - [src/utils/kiwoom_utils.py:1955 get_industry_list_ka10101](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:1955).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - AST에서 미발견. 실행 여부 0의 완전한 증명으로 사용하지 않음.

### ka20003 — 전업종지수요청(ka20003)

- 공식 path: `/api/dostk/sect`.
- 공통 헬퍼: 별도 직접 producer/adapter.
- API 상수 참조:
  - [src/engine/market_panic_breadth_collector.py:1241 fetch_kiwoom_market_breadth](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/market_panic_breadth_collector.py:1241).
  - [src/engine/market_panic_breadth_collector.py:1318 fetch_kiwoom_market_breadth](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/market_panic_breadth_collector.py:1318).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - AST에서 미발견. 실행 여부 0의 완전한 증명으로 사용하지 않음.

### ka20005 — 업종분봉조회요청(ka20005)

- 공식 path: `/api/dostk/chart`.
- 공통 헬퍼: `get_index_minute_candles_ka20005_with_meta`.
- API 상수 참조:
  - [src/engine/monitoring/pure_market_kiwoom_backfill.py:330 _normalize_index_row](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/monitoring/pure_market_kiwoom_backfill.py:330).
  - [src/engine/monitoring/pure_market_kiwoom_backfill.py:576 fetch_ka20005_history](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/monitoring/pure_market_kiwoom_backfill.py:576).
  - [src/engine/monitoring/pure_market_kiwoom_backfill.py:586 fetch_ka20005_history](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/monitoring/pure_market_kiwoom_backfill.py:586).
  - [src/engine/monitoring/pure_market_kiwoom_backfill.py:596 fetch_ka20005_history](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/monitoring/pure_market_kiwoom_backfill.py:596).
  - [src/engine/monitoring/pure_market_kiwoom_backfill.py:603 fetch_ka20005_history](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/monitoring/pure_market_kiwoom_backfill.py:603).
  - [src/engine/monitoring/pure_market_kiwoom_backfill.py:608 fetch_ka20005_history](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/monitoring/pure_market_kiwoom_backfill.py:608).
  - [src/engine/monitoring/pure_market_kiwoom_backfill.py:659 fetch_ka20005_history](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/monitoring/pure_market_kiwoom_backfill.py:659).
  - [src/engine/monitoring/pure_market_regime_replay.py:380 load_kospi_bars](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/monitoring/pure_market_regime_replay.py:380).
  - [src/utils/kiwoom_utils.py:61 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:61).
  - [src/utils/kiwoom_utils.py:2652 get_index_minute_candles_ka20005_with_meta](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:2652).
  - [src/utils/kiwoom_utils.py:2658 get_index_minute_candles_ka20005_with_meta](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:2658).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/engine/scalping/multi_timeframe_context.py:513 _index_context_source](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/scalping/multi_timeframe_context.py:513) → `get_index_minute_candles_ka20005_with_meta`.

### ka20006 — 업종일봉조회요청(ka20006)

- 공식 path: `/api/dostk/chart`.
- 공통 헬퍼: `get_index_daily_ka20006`.
- API 상수 참조:
  - [src/engine/signal_radar.py:451 SniperRadar.get_market_regime](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/signal_radar.py:451).
  - [src/utils/kiwoom_utils.py:2621 get_index_daily_ka20006](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:2621).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/scanners/final_ensemble_scanner.py:180 run_integrated_scanner](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/scanners/final_ensemble_scanner.py:180) → `get_index_daily_ka20006`.

### ka90001 — 테마그룹별요청(ka90001)

- 공식 path: `/api/dostk/thme`.
- 공통 헬퍼: `get_stock_theme_groups_ka90001`, `get_theme_group_list_ka90001`.
- API 상수 참조:
  - [src/utils/kiwoom_utils.py:1988 get_theme_group_list_ka90001](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:1988).
  - [src/utils/kiwoom_utils.py:2014 get_stock_theme_groups_ka90001](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:2014).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/engine/swing_sector_theme_source.py:296 fetch_kiwoom_sector_theme_map](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/swing_sector_theme_source.py:296) → `get_theme_group_list_ka90001`.

### ka90008 — 종목시간별프로그램매매추이요청(ka90008)

- 공식 path: `/api/dostk/mrkcond`.
- 공통 헬퍼: `build_realtime_analysis_context`, `check_program_buying_ka90008`, `get_program_flow_realtime`.
- API 상수 참조:
  - [src/utils/kiwoom_utils.py:62 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:62).
  - [src/utils/kiwoom_utils.py:4285 check_program_buying_ka90008](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:4285).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/engine/signal_radar.py:123 SniperRadar.find_supernova_targets](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/signal_radar.py:123) → `check_program_buying_ka90008`.
  - [src/engine/sniper_analysis.py:190 analyze_stock_now](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_analysis.py:190) → `get_program_flow_realtime`.
  - [src/engine/sniper_overnight_gatekeeper.py:273 _build_scalping_overnight_ctx](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_overnight_gatekeeper.py:273) → `build_realtime_analysis_context`.
  - [src/engine/sniper_state_handlers.py:64885 _handle_watching_strategy_branch](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:64885) → `build_realtime_analysis_context`.
  - [src/scanners/kosdaq_scanner.py:167 run_kosdaq_scanner](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/scanners/kosdaq_scanner.py:167) → `check_program_buying_ka90008`.

### kt00001 — 예수금상세현황요청(kt00001)

- 공식 path: `/api/dostk/acnt`.
- 공통 헬퍼: `_get_deposit_real`, `get_deposit`.
- API 상수 참조:
  - [src/engine/kiwoom_orders.py:763 _post_kiwoom_with_auth_retry](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/kiwoom_orders.py:763).
  - [src/engine/kiwoom_orders.py:1232 _get_deposit_real](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/kiwoom_orders.py:1232).
  - [src/engine/kiwoom_orders.py:1243 _get_deposit_real](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/kiwoom_orders.py:1243).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/engine/kiwoom_sniper_v2.py:1679 check_watching_conditions](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/kiwoom_sniper_v2.py:1679) → `get_deposit`.
  - [src/engine/sniper_state_handlers.py:44868 _probe_residual_account_guard_fields](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:44868) → `get_deposit`.
  - [src/engine/sniper_state_handlers.py:65996 _submit_watching_triggered_entry](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:65996) → `get_deposit`.
  - [src/engine/sniper_state_handlers.py:90859 execute_scale_in_order](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:90859) → `get_deposit`.

### kt00005 — 체결잔고요청(kt00005)

- 공식 path: `/api/dostk/acnt`.
- 공통 헬퍼: `get_account_balance_kt00005`, `get_account_balance_kt00005_with_meta`.
- API 상수 참조:
  - [src/utils/kiwoom_utils.py:857 get_account_balance_kt00005](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:857).
  - [src/utils/kiwoom_utils.py:951 get_account_balance_kt00005_with_meta](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:951).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/engine/sniper_s15_fast_track.py:553 _s15_inventory_and_orders](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_s15_fast_track.py:553) → `get_account_balance_kt00005_with_meta`.
  - [src/engine/sniper_sync.py:2103 sync_state_with_broker](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_sync.py:2103) → `get_account_balance_kt00005`.
  - [src/engine/sniper_sync.py:2111 sync_state_with_broker](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_sync.py:2111) → `get_account_balance_kt00005`.
  - [src/engine/sniper_sync.py:2340 refresh_broker_account_snapshot_read_only](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_sync.py:2340) → `get_account_balance_kt00005`.
  - [src/engine/sniper_sync.py:2491 periodic_account_sync](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_sync.py:2491) → `get_account_balance_kt00005`.
  - [src/engine/sniper_sync.py:2511 periodic_account_sync](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_sync.py:2511) → `get_account_balance_kt00005`.

### kt00007 — 계좌별주문체결내역상세요청(kt00007)

- 공식 path: `/api/dostk/acnt`.
- 공통 헬퍼: `get_order_reference_snapshot_2nd_pass`, `get_order_reference_snapshot_kt00007`, `get_order_reference_snapshot_kt00007_with_meta`.
- API 상수 참조:
  - [src/engine/monitoring/low_price_two_leg_tuning.py:807 reconcile_manual_exit_history](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/monitoring/low_price_two_leg_tuning.py:807).
  - [src/engine/monitoring/machine_microstructure_attribution.py:871 _verified_target_timestamp_loss](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/monitoring/machine_microstructure_attribution.py:871).
  - [src/engine/monitoring/machine_microstructure_attribution.py:1014 _verified_manual_timestamp_loss](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/monitoring/machine_microstructure_attribution.py:1014).
  - [src/engine/scalping/initial_quantity_terminal.py:276 prove_initial_buy_leg_terminal.identity](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/scalping/initial_quantity_terminal.py:276).
  - [src/engine/sniper_sync.py:2233 _unique_sell_execution_reconciliation](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_sync.py:2233).
  - [src/engine/sniper_sync.py:2926 periodic_account_sync](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_sync.py:2926).
  - [src/engine/sniper_trade_review_report.py:2235 _sell_balance_reconciliation_generation_status](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_trade_review_report.py:2235).
  - [src/engine/sniper_trade_utils.py:407 resolve_pending_sell_order_no](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_trade_utils.py:407).
  - [src/trading/low_price_two_leg/gateway.py:62 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/low_price_two_leg/gateway.py:62).
  - [src/trading/low_price_two_leg/gateway.py:81 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/low_price_two_leg/gateway.py:81).
  - [src/trading/low_price_two_leg/gateway.py:641 KiwoomLowPriceTwoLegGateway.execution_snapshot](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/low_price_two_leg/gateway.py:641).
  - [src/trading/order/adaptive_exit/broker.py:287 RegisteredSellAdapter._snapshot](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/adaptive_exit/broker.py:287).
  - [src/trading/order/aftermarket_reconciliation.py:17 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/aftermarket_reconciliation.py:17).
  - [src/trading/order/kiwoom_episode_read_control.py:30 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/kiwoom_episode_read_control.py:30).
  - [src/trading/order/manual_episode_exit_reconciliation.py:42 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/manual_episode_exit_reconciliation.py:42).
  - [src/trading/order/manual_episode_exit_reconciliation.py:229 _verified_receipts](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/manual_episode_exit_reconciliation.py:229).
  - [src/trading/order/manual_episode_exit_reconciliation.py:273 _verified_prior_day_unfilled_target](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/manual_episode_exit_reconciliation.py:273).
  - [src/trading/order/manual_episode_exit_reconciliation.py:385 reconcile_manual_exit](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/manual_episode_exit_reconciliation.py:385).
  - [src/trading/order/owner_custody_registry.py:74 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/owner_custody_registry.py:74).
  - [src/trading/order/regular_two_leg_machine.py:1693 SamsungRegularTwoLegMachine._reconcile_target](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/regular_two_leg_machine.py:1693).
  - [src/trading/order/target_amend.py:38 reconcile_amendment](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/target_amend.py:38).
  - [src/trading/samsung_afternoon_one_share/gateway.py:59 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_afternoon_one_share/gateway.py:59).
  - [src/trading/samsung_afternoon_one_share/gateway.py:511 KiwoomAfternoonOneShareGateway.execution_snapshot](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_afternoon_one_share/gateway.py:511).
  - [src/trading/samsung_midday_one_share/gateway.py:59 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_midday_one_share/gateway.py:59).
  - [src/trading/samsung_midday_one_share/gateway.py:509 KiwoomMiddayOneShareGateway.execution_snapshot](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_midday_one_share/gateway.py:509).
  - [src/trading/samsung_morning_one_share/gateway.py:64 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_morning_one_share/gateway.py:64).
  - [src/trading/samsung_morning_one_share/gateway.py:608 KiwoomOneShareGateway._execution_snapshot_for_quantity](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_morning_one_share/gateway.py:608).
  - [src/utils/kiwoom_utils.py:1465 _normalize_order_history_rows](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:1465).
  - [src/utils/kiwoom_utils.py:1599 _order_snapshot_contract_meta](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:1599).
  - [src/utils/kiwoom_utils.py:1700 get_order_reference_snapshot_kt00007](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:1700).
  - [src/utils/kiwoom_utils.py:1706 get_order_reference_snapshot_kt00007](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:1706).
  - [src/utils/kiwoom_utils.py:1743 get_order_reference_snapshot_kt00007_with_meta](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:1743).
  - [src/utils/kiwoom_utils.py:1749 get_order_reference_snapshot_kt00007_with_meta](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:1749).
  - [src/utils/kiwoom_utils.py:1756 get_order_reference_snapshot_kt00007_with_meta](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:1756).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/engine/scalping/initial_quantity_terminal.py:187 read_initial_buy_leg_terminal_discover](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/scalping/initial_quantity_terminal.py:187) → `get_order_reference_snapshot_kt00007_with_meta`.
  - [src/engine/scalping/initial_quantity_terminal.py:362 read_initial_buy_leg_terminal](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/scalping/initial_quantity_terminal.py:362) → `get_order_reference_snapshot_kt00007_with_meta`.
  - [src/engine/sniper_sync.py:761 _recover_missing_broker_holdings](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_sync.py:761) → `get_order_reference_snapshot_2nd_pass`.
  - [src/engine/sniper_sync.py:2562 periodic_account_sync._sell_execution_snapshot](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_sync.py:2562) → `get_order_reference_snapshot_kt00007_with_meta`.
  - [src/engine/sniper_trade_utils.py:321 resolve_pending_sell_order_no](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_trade_utils.py:321) → `get_order_reference_snapshot_kt00007_with_meta`.
  - [src/trading/order/manual_episode_exit_reconciliation.py:137 load_manual_sell_receipts](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/manual_episode_exit_reconciliation.py:137) → `get_order_reference_snapshot_kt00007`.
  - [src/trading/order/symbol_owner_policy_apply.py:387 collect_broker_snapshot](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/symbol_owner_policy_apply.py:387) → `get_order_reference_snapshot_kt00007_with_meta`.

### kt00008 — 계좌별익일결제예정내역요청(kt00008)

- 공식 path: `/api/dostk/acnt`.
- 공통 헬퍼: `get_account_execution_snapshot_kt00008`.
- API 상수 참조:
  - [src/utils/kiwoom_utils.py:1033 get_account_execution_snapshot_kt00008](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:1033).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/engine/sniper_sync.py:739 _recover_missing_broker_holdings](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_sync.py:739) → `get_account_execution_snapshot_kt00008`.

### kt00011 — 증거금율별주문가능수량조회요청(kt00011)

- 공식 path: `/api/dostk/acnt`.
- 공통 헬퍼: `get_orderable_by_margin_kt00011`.
- API 상수 참조:
  - [src/utils/kiwoom_utils.py:1103 get_orderable_by_margin_kt00011](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:1103).
  - [src/utils/kiwoom_utils.py:5371 _fetch_kiwoom_api_continuous_transport](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:5371).
  - [src/utils/kiwoom_utils.py:5433 _fetch_kiwoom_api_continuous_transport](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:5433).
  - [src/utils/kiwoom_utils.py:5449 _fetch_kiwoom_api_continuous_transport](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:5449).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/engine/sniper_state_handlers.py:3061 _read_entry_capacity_snapshot.fetch](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:3061) → `get_orderable_by_margin_kt00011`.

### kt00018 — 계좌평가잔고내역요청(kt00018)

- 공식 path: `/api/dostk/acnt`.
- 공통 헬퍼: `get_my_inventory`.
- API 상수 참조:
  - [src/engine/kiwoom_orders.py:763 _post_kiwoom_with_auth_retry](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/kiwoom_orders.py:763).
  - [src/engine/kiwoom_orders.py:1393 get_my_inventory](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/kiwoom_orders.py:1393).
  - [src/engine/kiwoom_orders.py:1407 get_my_inventory](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/kiwoom_orders.py:1407).
  - [src/trading/order/owner_custody_registry.py:73 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/owner_custody_registry.py:73).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/engine/sniper_state_handlers.py:77119 _order_terminal_inventory_reconciliation](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:77119) → `get_my_inventory`.
  - [src/engine/sniper_state_handlers.py:87614 handle_holding_state](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:87614) → `get_my_inventory`.
  - [src/engine/sniper_state_handlers.py:89503 _pending_add_blocks_sell_dispatch](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:89503) → `get_my_inventory`.
  - [src/engine/sniper_state_handlers.py:92983 _broker_position_qty_for_sell_reconciliation](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:92983) → `get_my_inventory`.
  - [src/engine/sniper_sync.py:1457 sync_balance_with_db](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_sync.py:1457) → `get_my_inventory`.
  - [src/engine/sniper_sync.py:1469 sync_balance_with_db](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_sync.py:1469) → `get_my_inventory`.
  - [src/engine/sniper_trade_utils.py:956 confirm_cancel_or_reload_remaining](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_trade_utils.py:956) → `get_my_inventory`.
  - [src/trading/order/symbol_owner_policy_apply.py:333 collect_broker_snapshot](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/symbol_owner_policy_apply.py:333) → `get_my_inventory`.

### kt10000 — 주식 매수주문(kt10000)

- 공식 path: `/api/dostk/ordr`.
- 공통 헬퍼: `reserve_buy_order_ai`, `send_buy_order`, `send_buy_order_market`.
- API 상수 참조:
  - [src/engine/kiwoom_orders.py:2102 send_buy_order_market](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/kiwoom_orders.py:2102).
  - [src/engine/kiwoom_orders.py:2194 send_buy_order_market](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/kiwoom_orders.py:2194).
  - [src/engine/scalping/opening_rotation_tuning.py:290 _merge_episode](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/scalping/opening_rotation_tuning.py:290).
  - [src/engine/sniper_state_handlers.py:3452 _apply_scalping_margin_one_share_authority](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:3452).
  - [src/engine/sniper_state_handlers.py:3543 _opening_rotation_margin_budget_log_fields](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:3543).
  - [src/engine/sniper_state_handlers.py:3589 _general_entry_margin_budget_log_fields](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:3589).
  - [src/trading/low_price_two_leg/gateway.py:62 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/low_price_two_leg/gateway.py:62).
  - [src/trading/low_price_two_leg/gateway.py:549 KiwoomLowPriceTwoLegGateway.submit_limit_buy](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/low_price_two_leg/gateway.py:549).
  - [src/trading/order/entry_adverse_guard.py:53 before_transport](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/entry_adverse_guard.py:53).
  - [src/trading/order/owner_custody_registry.py:76 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/owner_custody_registry.py:76).
  - [src/trading/samsung_afternoon_one_share/gateway.py:59 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_afternoon_one_share/gateway.py:59).
  - [src/trading/samsung_midday_one_share/gateway.py:59 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_midday_one_share/gateway.py:59).
  - [src/trading/samsung_morning_one_share/gateway.py:64 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_morning_one_share/gateway.py:64).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/engine/ipo_listing_day_runner.py:821 IpoListingDayEngine._send_entry_order](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/ipo_listing_day_runner.py:821) → `send_buy_order`.
  - [src/engine/sniper_state_handlers.py:71160 _submit_watching_triggered_entry](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:71160) → `send_buy_order`.
  - [src/engine/sniper_state_handlers.py:78018 _initial_quantity_submit_successor_leg](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:78018) → `send_buy_order`.
  - [src/engine/sniper_state_handlers.py:80252 _maybe_reprice_pending_entry_order](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:80252) → `send_buy_order`.
  - [src/engine/sniper_state_handlers.py:84199 _submit_entry_split_probe_residual_locked](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:84199) → `send_buy_order`.
  - [src/engine/sniper_state_handlers.py:92037 execute_scale_in_order](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:92037) → `send_buy_order`.

### kt10001 — 주식 매도주문(kt10001)

- 공식 path: `/api/dostk/ordr`.
- 공통 헬퍼: `send_sell_order_market`, `send_smart_sell_order`.
- API 상수 참조:
  - [src/engine/kiwoom_orders.py:2339 send_sell_order_market](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/kiwoom_orders.py:2339).
  - [src/engine/kiwoom_orders.py:2417 send_sell_order_market](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/kiwoom_orders.py:2417).
  - [src/trading/low_price_two_leg/gateway.py:62 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/low_price_two_leg/gateway.py:62).
  - [src/trading/low_price_two_leg/gateway.py:578 KiwoomLowPriceTwoLegGateway.submit_limit_sell](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/low_price_two_leg/gateway.py:578).
  - [src/trading/order/adaptive_exit/broker.py:862 RegisteredSellAdapter.submit_closed_group_residual](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/adaptive_exit/broker.py:862).
  - [src/trading/order/adaptive_exit/broker.py:1016 RegisteredSellAdapter.submit_owned_sell](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/adaptive_exit/broker.py:1016).
  - [src/trading/order/adaptive_exit/broker.py:1084 RegisteredSellAdapter.submit_partial_cancel_residual](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/adaptive_exit/broker.py:1084).
  - [src/trading/order/owner_custody_registry.py:77 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/owner_custody_registry.py:77).
  - [src/trading/samsung_afternoon_one_share/gateway.py:59 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_afternoon_one_share/gateway.py:59).
  - [src/trading/samsung_afternoon_one_share/gateway.py:447 KiwoomAfternoonOneShareGateway.submit_limit_sell](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_afternoon_one_share/gateway.py:447).
  - [src/trading/samsung_midday_one_share/gateway.py:59 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_midday_one_share/gateway.py:59).
  - [src/trading/samsung_midday_one_share/gateway.py:445 KiwoomMiddayOneShareGateway.submit_limit_sell](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_midday_one_share/gateway.py:445).
  - [src/trading/samsung_morning_one_share/gateway.py:64 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_morning_one_share/gateway.py:64).
  - [src/trading/samsung_morning_one_share/gateway.py:524 KiwoomOneShareGateway.submit_limit_sell](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_morning_one_share/gateway.py:524).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/engine/ipo_listing_day_runner.py:925 IpoListingDayEngine._send_exit_order](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/ipo_listing_day_runner.py:925) → `send_smart_sell_order`.
  - [src/engine/sniper_execution_receipts.py:9840 _submit_opening_rotation_profit_order](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_execution_receipts.py:9840) → `send_sell_order_market`.
  - [src/engine/sniper_s15_fast_track.py:1559 _send_s15_limit_sell](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_s15_fast_track.py:1559) → `send_sell_order_market`.
  - [src/engine/sniper_s15_fast_track.py:1572 _send_s15_market_sell](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_s15_fast_track.py:1572) → `send_sell_order_market`.
  - [src/engine/sniper_s15_fast_track.py:1585 _send_exit_best_ioc](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_s15_fast_track.py:1585) → `send_sell_order_market`.
  - [src/engine/sniper_state_handlers.py:81426 _reconcile_pending_entry_orders](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:81426) → `send_sell_order_market`.
  - [src/engine/sniper_state_handlers.py:88445 handle_holding_state](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:88445) → `send_smart_sell_order`.
  - [src/engine/sniper_trade_utils.py:485 send_market_exit_now](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_trade_utils.py:485) → `send_sell_order_market`.
  - [src/engine/sniper_trade_utils.py:535 send_exit_best_ioc](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_trade_utils.py:535) → `send_sell_order_market`.

### kt10002 — 주식 정정주문(kt10002)

- 공식 path: `/api/dostk/ordr`.
- 공통 헬퍼: 별도 직접 producer/adapter.
- API 상수 참조:
  - [src/trading/order/adaptive_exit/broker.py:993 RegisteredSellAdapter.amend_owned_sell](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/adaptive_exit/broker.py:993).
  - [src/trading/order/owner_custody_registry.py:78 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/owner_custody_registry.py:78).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - AST에서 미발견. 실행 여부 0의 완전한 증명으로 사용하지 않음.

### kt10003 — 주식 취소주문(kt10003)

- 공식 path: `/api/dostk/ordr`.
- 공통 헬퍼: `send_cancel_order`.
- API 상수 참조:
  - [src/engine/kiwoom_orders.py:2502 send_cancel_order](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/kiwoom_orders.py:2502).
  - [src/engine/kiwoom_orders.py:2545 send_cancel_order.response_with_request_provenance](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/kiwoom_orders.py:2545).
  - [src/engine/kiwoom_orders.py:2557 send_cancel_order](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/kiwoom_orders.py:2557).
  - [src/engine/sniper_execution_receipts.py:4684 persist_pending_sell_cancel_ack_custody](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_execution_receipts.py:4684).
  - [src/engine/sniper_trade_utils.py:586 cancel_response_ack_exact](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_trade_utils.py:586).
  - [src/trading/low_price_two_leg/gateway.py:62 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/low_price_two_leg/gateway.py:62).
  - [src/trading/low_price_two_leg/gateway.py:597 KiwoomLowPriceTwoLegGateway.cancel_buy](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/low_price_two_leg/gateway.py:597).
  - [src/trading/order/adaptive_exit/broker.py:963 RegisteredSellAdapter.cancel_owned_sell](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/adaptive_exit/broker.py:963).
  - [src/trading/order/adaptive_exit/broker.py:1100 RegisteredSellAdapter._write](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/adaptive_exit/broker.py:1100).
  - [src/trading/order/adaptive_exit/buy_cancel.py:345 RegisteredBuyCancelAdapter.cancel_owned_buy](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/adaptive_exit/buy_cancel.py:345).
  - [src/trading/order/owner_custody_registry.py:79 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/order/owner_custody_registry.py:79).
  - [src/trading/samsung_afternoon_one_share/gateway.py:59 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_afternoon_one_share/gateway.py:59).
  - [src/trading/samsung_afternoon_one_share/gateway.py:466 KiwoomAfternoonOneShareGateway.cancel_buy](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_afternoon_one_share/gateway.py:466).
  - [src/trading/samsung_midday_one_share/gateway.py:59 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_midday_one_share/gateway.py:59).
  - [src/trading/samsung_midday_one_share/gateway.py:464 KiwoomMiddayOneShareGateway.cancel_buy](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_midday_one_share/gateway.py:464).
  - [src/trading/samsung_morning_one_share/gateway.py:64 <module>](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_morning_one_share/gateway.py:64).
  - [src/trading/samsung_morning_one_share/gateway.py:544 KiwoomOneShareGateway.cancel](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_morning_one_share/gateway.py:544).
  - [src/trading/samsung_morning_one_share/gateway.py:566 KiwoomOneShareGateway.cancel_manual_addon_remaining](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/trading/samsung_morning_one_share/gateway.py:566).
- 공통 헬퍼 외부 호출·함수 전달 참조:
  - [src/engine/sniper_execution_receipts.py:5368 _cancel_replacement_sell_once](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_execution_receipts.py:5368) → `send_cancel_order`.
  - [src/engine/sniper_execution_receipts.py:7203 _cancel_replacement_buys_after_late_parent_fill](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_execution_receipts.py:7203) → `send_cancel_order`.
  - [src/engine/sniper_s15_fast_track.py:1064 _submit_s15_stop_cancel](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_s15_fast_track.py:1064) → `send_cancel_order`.
  - [src/engine/sniper_s15_fast_track.py:1259 _recover_s15_custody](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_s15_fast_track.py:1259) → `send_cancel_order`.
  - [src/engine/sniper_state_handlers.py:78306 _cancel_pending_entry_orders](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:78306) → `send_cancel_order`.
  - [src/engine/sniper_state_handlers.py:78407 _cancel_pending_entry_orders](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:78407) → `send_cancel_order`.
  - [src/engine/sniper_state_handlers.py:80095 _maybe_reprice_pending_entry_order](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:80095) → `send_cancel_order`.
  - [src/engine/sniper_state_handlers.py:93935 process_sell_cancellation](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_state_handlers.py:93935) → `send_cancel_order`.
  - [src/engine/sniper_trade_utils.py:675 send_cancel_order_with_exchange_retry](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_trade_utils.py:675) → `send_cancel_order`.
  - [src/engine/sniper_trade_utils.py:710 send_cancel_order_with_exchange_retry](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_trade_utils.py:710) → `send_cancel_order`.
  - [src/engine/sniper_trade_utils.py:888 confirm_cancel_or_reload_remaining](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/engine/sniper_trade_utils.py:888) → `send_cancel_order`.

### au10001 — token 발급

- API ID literal은 없으며 `/oauth2/token` HTTP route로 발견.
- [_request_new_kiwoom_token](/home/ubuntu/KORStockScan-runtime-releases/probe-original-source-20261006-fd222e31/src/utils/kiwoom_utils.py:739).
- WS LOGIN 이전 REST 인증 유지. au10002 revoke 호출 구현은 미발견.

## 2. 선택 릴리스 source SHA256

| 파일 | SHA256 |
|---|---|
| `src/engine/institutional_flow_context.py` | `03ff3c34ae05ab0e11da50c81dd3b468094d864fdb17726b5ebb842f85317fa6` |
| `src/engine/ipo_listing_day_runner.py` | `3310b83306ba5e5f1e2abc4256a7f76ddcdd5b56c7558026fd236a60fbf0df9b` |
| `src/engine/kiwoom_orders.py` | `e5b07a67dff070a39b0f34b0d3dfd85843da1ccab3767a9c3ebf0c85eaf108b2` |
| `src/engine/kiwoom_sniper_v2.py` | `f082860859769d3d918b1a26c0b790aef9f0a4b5531863a64ce2881392cebde9` |
| `src/engine/kiwoom_websocket.py` | `7a9f16c3364e46d22c30fb0cc9efdccc3d62a4f4d6562a747d06bf80a7e9f794` |
| `src/engine/market_panic_breadth_collector.py` | `aa9186c311e6f8ba9f3f08cded897f8820053e33783f5ba290860a4b306d63ac` |
| `src/engine/monitoring/low_price_two_leg_entry_spot_research.py` | `df5337d5a91bf57302a8c5509544d124a01fec6d2b91390ab4c6a58205a2a35f` |
| `src/engine/monitoring/low_price_two_leg_expanded_candidate_research.py` | `d529d0fb5472341426bc54a05c97e0fc024005fe9b049f92c209b3d753e25f62` |
| `src/engine/monitoring/low_price_two_leg_tuning.py` | `ca98ee05d8ba143c50913854408c79f4ee62db207b9a2adb6d5276ad215328f3` |
| `src/engine/monitoring/machine_microstructure_attribution.py` | `74687644db6d1b0f010aedbfd733307c2f7e923125710a26b132affc343953d3` |
| `src/engine/monitoring/market_opportunity_census.py` | `a10b115094b6218cfeb31611a2f4b08f3318358225a4ed1077353882a86f0ced` |
| `src/engine/monitoring/pruned_candidate_bbo_collector.py` | `9cb43425b0e819b905e5a251fd001ca036313155319c80c09e40bcdb9c28eb8e` |
| `src/engine/monitoring/pure_market_kiwoom_backfill.py` | `4b4f6b99564e5b2d7ad417a002b8fde10785056b831762894954d03059f362bd` |
| `src/engine/monitoring/pure_market_regime_replay.py` | `320b9b75ad22ba029a7611a18f5334aecd007a38cfa7921bc2cec1c1c6260578` |
| `src/engine/scalping/ai_action_outcome_calibration.py` | `32cf3ef523841baf2bf040e73f890a73d248f19c73b1874b2bed6ab05c57ed7f` |
| `src/engine/scalping/ai_decision_quality.py` | `218b2d1ed9133ed11894d729d27afdef4288b712262811d6c13e6a1fa013e34f` |
| `src/engine/scalping/ai_input_external_validation.py` | `61c75f07f411d2a9ef5fffbf461e6fe84a90a5121bbbe04a717ef9192e57db02` |
| `src/engine/scalping/ai_market_snapshot.py` | `dfa1c14cdaf7d1779310aa13561a412927adbf1414f832c39f31cca8a7d0e72b` |
| `src/engine/scalping/entry_candle_context.py` | `7f6a92a7d08019532e7a182d316769d83343c1955d152e761f8ac8a0c0de1c0f` |
| `src/engine/scalping/entry_strategy_policy.py` | `664cac6b0bc1706af850517544cd2124e6e301c722e318bb5e8969b3789bfa3a` |
| `src/engine/scalping/holding_decision_context.py` | `e3590eebd7d40c295730f3579ec87ea57737d7ed5022ec32aea357c38bf57c44` |
| `src/engine/scalping/initial_quantity_following_bars.py` | `73b3d7f2db4eade5faf01a8a6bff69c60741a167302e99dbda76c3c08a808b14` |
| `src/engine/scalping/initial_quantity_policy.py` | `f5f8d8e0220a9f3f75eb53920887e7881160156bdcd5b119df822ea7365f597d` |
| `src/engine/scalping/initial_quantity_terminal.py` | `513c18997cb7cb28f2b10c5c7c2fdf5076177298cca8a7391be0e0a245b87fc0` |
| `src/engine/scalping/market_context_observation.py` | `ac2568416d24be868cbe14049a3803ab6cd4647b8105fb9e03b59c3583199dd3` |
| `src/engine/scalping/market_data_enrichment.py` | `093d78b5450f95bab6dbed9edd6699ab17e20f5c4d86198dcd0282a7c975f18a` |
| `src/engine/scalping/multi_timeframe_context.py` | `8d532e9f5b419012c95c941c38ddabfaec9855b56921080a45ba40fbb027eba4` |
| `src/engine/scalping/opening_rotation_tuning.py` | `332a5f6ac32819e4f983dbb185b905c0b380699695e51feef58633189b09fa07` |
| `src/engine/scalping/zero_base_probe.py` | `f597195bd1beb2c0a456a587d75badece1202ece73b8e3a453c4f66310a12aa6` |
| `src/engine/signal_radar.py` | `1206b09397224f93c1138ad4750ab744e9849e20be679ec1ab1cd3ae6fe6828f` |
| `src/engine/sniper_analysis.py` | `729b8869089c070b15519fecc04bbfffa25ed7c846663e8f0a86ca61ae0f1798` |
| `src/engine/sniper_condition_handlers.py` | `c405cb33d19f9d9f857efd122f9175e1c0cc8f6614c53b574ab6aaa466bd7b6b` |
| `src/engine/sniper_entry_latency.py` | `31c585d92d7414b4be11ac79d3f411b042436ccd396f32834e9eafbbc905b856` |
| `src/engine/sniper_execution_receipts.py` | `f20c3d6c45b8e82bba0d7f0a7042f7a15e75502796010198a155b2c31dcf5734` |
| `src/engine/sniper_missed_entry_counterfactual.py` | `68b06da6cf36f422ca029bf89a49c5134446ab83002ef2725aa91cd41b0a3c36` |
| `src/engine/sniper_overnight_gatekeeper.py` | `2f06ee2f1d4df333e06ef721d0a43f040f3f95d511b2699de59799718338a5e6` |
| `src/engine/sniper_post_sell_feedback.py` | `8b6d50ce6c5693338942fcbfeeb397d8ac13f244188cc6a8ec50229c19efe501` |
| `src/engine/sniper_s15_fast_track.py` | `238126df824442db957a024b5773f193a288e60701778b884b3fee17bf84a496` |
| `src/engine/sniper_state_handlers.py` | `79de19d4bca3d509998a0e5c06a89c8972ed7dc860416a71aaf3d108991cbf4a` |
| `src/engine/sniper_strength_shadow_feedback.py` | `28a7d369eaed37efaac960f33a452f22824d6a7f39d5135ed711b973a9d6b972` |
| `src/engine/sniper_sync.py` | `6ba44542a45ff24454b6a4071af127f0252cdb0a39e1136722ef4a40d919c091` |
| `src/engine/sniper_trade_review_report.py` | `f0d118d09ce426fb3fd6a865168ef8cf43fcddbbad0fe23e8e17ff5ec5dbd62c` |
| `src/engine/sniper_trade_utils.py` | `c816ae517e1557d9b79dd9338658458f3fde5929467b7a7879c64c70a42611ac` |
| `src/engine/swing_sector_theme_source.py` | `2e189c50209896204c4c044d9965c239c9307a15113cbb64ef97d111066fa630` |
| `src/engine/wait6579_ev_cohort_report.py` | `e7954c09c1c688c63b7452ba9ac5c675f41cee4a1264fcc7f6bf4a5d9289ca52` |
| `src/notify/telegram_manager.py` | `bf08fc039abce6d22cdc234423f070149bd8ac9ce8da216c8639af421cc2cc7d` |
| `src/scanners/final_ensemble_scanner.py` | `2b98595df0f4b637b0e21d00a96156ae236e9f63a9b9d8166c420d6d62307fb7` |
| `src/scanners/kosdaq_scanner.py` | `a761023884adaac3eb76ceadccf73a1acddb11ffd3bc03fcc67409da13e4c7a7` |
| `src/scanners/scalping_scanner.py` | `fc99564b01b6c581387e4fb9bff6fa218d7f2af0827b2b47b3b9c30c0dc81903` |
| `src/scanners/zero_base_discovery_source.py` | `15dc8686c303e359833f185c013f82cd22097f7cc4567f2fbd02579a63931ff9` |
| `src/trading/low_price_two_leg/gateway.py` | `30291da023b458c2d1bbd1c14aeab09c126a4a77b90f90613231890b895686e0` |
| `src/trading/market/quote_consistency.py` | `12431c0b9ad2abcb999d9f0f81ce7c321306507cf2b1c439047651ff758def18` |
| `src/trading/order/adaptive_exit/broker.py` | `feff2664a60b9b9584b31b036a4300337e3eb67ec1a05707c0d47d8fee52aa51` |
| `src/trading/order/adaptive_exit/buy_cancel.py` | `6f93144e68b93d859bc6f398a5ffa660cf21e4907b62ff6dfaf676fd7951f43f` |
| `src/trading/order/aftermarket_reconciliation.py` | `0b17cc4d90e62201967ff51e19ce6ef939d686673f683b76b970b139887f4868` |
| `src/trading/order/entry_adverse_guard.py` | `113d92b7ed0ee820db54e1cd650f74cdc049d1e6a3055794c0e7f49c7e8a9f0f` |
| `src/trading/order/entry_liquidity_guard.py` | `7d1e927576ef366cc78d5e7b0f7b6bbc2deb352c33b6f9c9af8bb610014d535a` |
| `src/trading/order/kiwoom_episode_read_control.py` | `cc76b6a6bbed0cbcb5865312bf70dfa7880eea08744e4b74f8dc3b0f9d835d20` |
| `src/trading/order/manual_episode_exit_reconciliation.py` | `117d818589750d8ca527018a2181209ec482c69f7a41cdbe02c0caa8a6f0d946` |
| `src/trading/order/owner_custody_registry.py` | `73d55f3db418bdf030d2ef7712d5ad700e415ee36a5c91ecd8e86b63580fef56` |
| `src/trading/order/regular_two_leg_machine.py` | `008090ad61d4d2ed63af74b1ba65ed50ecf1d994847af7fbcad3d03f57e5ab65` |
| `src/trading/order/symbol_owner_policy_apply.py` | `5791eb9220b69e215d79dd656cdfc4f09b2154e7f858277ff6b6b28b8d611ffe` |
| `src/trading/order/target_amend.py` | `0b6593a7e1bd20f3ea46a74376648fb07dd7c8fbb82e4396b3f2b3533e323fea` |
| `src/trading/samsung_afternoon_one_share/gateway.py` | `c6871518c1dade34fc949cadd67b3b3315097b5d824556804d1e563751b5b94c` |
| `src/trading/samsung_midday_one_share/gateway.py` | `b0b8f0df0f80a47a80a90281a1be3a5083ac614a3b0445a5ed2818bf43706586` |
| `src/trading/samsung_morning_one_share/gateway.py` | `9e19e2c12f4529536a54e40e55ff1a7b8b6cb058e7c4016a6fc74a74af738863` |
| `src/utils/kiwoom_read_request_control.py` | `6fa7c1bf306f6e9bc32e7a04b203bb489999e98b3dbe2f66066983b62bafbec9` |
| `src/utils/kiwoom_utils.py` | `da3b0b82a0221b4cf40fbcf46f0edde5efd7a975547c2bc2e8e76b032bd1146b` |
| `src/utils/update_kospi.py` | `1796bc1d76794dc9b2dd40ca1d67f898e15f74eb4e2b4550d841ca94c860a13e` |

## 3. 공식 참조 SHA256

- upstream `953e5dbff123f437ab4d11a78a95191a685eb51f`, 확인·hash 기록 `2026-10-06T17:09:34.475390+09:00`.
- kiwoom_docs 부재; 비용 누적/귀속·04 Extra Item·WS historical replay 의미 결손은 본문에 기록.

| 공식 경로 | SHA256 |
|---|---|
| `kiwoom/_data/kiwoom_api_spec.json` | `42a7b3912c9d9588c83bdc2db7779c8d2e038703a2b5562e54ef46ae905cba79` |
| `kiwoom/specs.py` | `954a962e0b25e892e972c13b837c6da60c47479d29ab235b608fb6f5565d00e2` |
| `kiwoom/core/client.py` | `6fcdb4d465984444baf36ec654be320c8a9938accf31df996d139de8394a1e67` |
| `kiwoom/core/ws_client.py` | `0f01e51654730a2b608983b21a3b78ae8a489cbb8d4902855c19bb24925d09c3` |
| `kiwoom/core/errors.py` | `79dd67bb7f5c8109fe250c9bc6772e2f33f791d5878275ef2cedc6ed48319110` |
| `kiwoom/core/auth.py` | `3c85981d0ff6b0c7e16a030a58c374146ec585f46eaf6097b4ed20af9ba15ad0` |
| `kiwoom/realtime/schemas.py` | `c5e5b95b0e9c0c5b7dd0ab84302ab8b0b6e01e353735e7edc2e307c2408ddcd1` |
| `kiwoom/realtime/decoders.py` | `893ea87eeea035c1ed3d0a43aa9b4bbe069c54e2d8de2bd7b88aa058d658a9ac` |
| `kiwoom/realtime/packets.py` | `a2422a5b14c1a3c62b6e3b6434bb744caa6d9d81e410bc38407c458ebd52e6bc` |
| `kiwoom/realtime/stream.py` | `50b49242ea41d1764f2f718609bb74160a872571630764381ad80194ab95db99` |
| `postman/kiwoom-openapi.postman_collection.json` | `566da2ab27e1838645c821f7a8ced521096863d441db0142cdb8800db18c83c2` |

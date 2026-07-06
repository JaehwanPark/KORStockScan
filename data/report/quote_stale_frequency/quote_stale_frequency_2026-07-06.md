# Quote Stale Frequency Report 2026-07-06

## Contract

- metric_role: `source_quality_gate`
- decision_authority: `quote_stale_frequency_report_only`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- broker_order_forbidden: `True`
- stale_threshold_ms: `3000.0`
- primary_source: `pipeline_events`

## Summary

- rows_with_quote_age: `23511`
- stale_count: `12364`
- stale_rate_pct: `52.5882`
- quote_age_source_missing_count: `15278`
- quote_age_ms: `{'avg': 19952.6349, 'p50': 3327.0, 'p75': 11843.155, 'p90': 49426.505, 'p95': 70886.82, 'p99': 352988.973, 'max': 1452303.125}`

## Verifier Findings

- `warning` `scanner_watch_stale_rate_high`
- `warning` `holding_scale_stale_rate_high`
- `warning` `scale_in_feature_refresh_recovery_rate_low`
- `warning` `persistent_ws_no_tick_cooldown_observed`

## Kiwoom Freshness Operating Assumptions

- `subscription_item_limit` status=official_number_not_documented policy=Treat each websocket item as consuming quota. Count KRX/NXT alternate-route items separately until Kiwoom confirms otherwise.
- `idle_no_event_unsubscribe` status=exact_idle_timeout_and_cancel_notice_not_documented policy=Use client last-receive timestamps to detect no-tick/stale symbols and recover with bounded REMOVE/REG or reconnect logic.
- `reg_refresh_semantics` status=refresh_1_append_refresh_0_replace policy=For NXT-to-KRX route changes, REMOVE the old NXT item before KRX REG; do not rely on refresh=1 as a full replacement.
- `rereg_cooldown` status=official_cooldown_not_documented policy=Start with bounded retry and backoff to avoid request-throttle errors; keep repair actions observable in logs.
- `server_timestamp_sequence` status=millisecond_server_timestamp_and_global_sequence_not_documented policy=Stamp websocket receives on the client, maintain local counters, and compare against ka10003/ka10004 snapshots for source-quality recovery.
- `ka10004_bid_req_base_tm` status=format_and_authority_ambiguous policy=Use bid_req_base_tm as raw snapshot reference-time provenance only; freshness authority remains the client receive timestamp or measured refresh age.

## Kiwoom Support Questions

- What is the current websocket concurrent subscription limit per session, and are KRX/NXT alternate-route items counted separately?
- Can the server automatically cancel or stop idle/low-liquidity realtime subscriptions, and if so what timeout and notice payload should clients expect?
- Is REMOVE plus REG the official required procedure for NXT-to-KRX route transition, and is refresh=1 append-only for all realtime types?
- What retry cooldown and per-second/per-minute REG or REST snapshot limits should clients use to avoid 105110-style throttling?
- Is there any realtime millisecond server-send timestamp, sequence number, or gap-detection API not shown in the public payload docs?
- What exact format and clock basis does ka10004 bid_req_base_tm use in production, and can it ever be used as freshness authority?

## By Class

- `scanner_watch` total=15197 stale=9042 rate=59.4986% p50=5363.173 p90=63545.364 max=1452303.125
- `holding_scale_input` total=4016 stale=1888 rate=47.012% p50=2891.0 p90=6068.0 max=33683.0
- `other` total=2559 stale=854 rate=33.3724% p50=1320.0 p90=7442.0 max=41045.0
- `entry_submit_input` total=1608 stale=512 rate=31.8408% p50=524.975 p90=9398.0 max=27832.0
- `quote_consistency` total=71 stale=67 rate=94.3662% p50=10919.0 p90=15853.0 max=27403.0
- `actual_submit` total=42 stale=1 rate=2.381% p50=1631.0 p90=2413.0 max=3620.0
- `sell_execution_or_exit` total=18 stale=0 rate=0.0% p50=0.0 p90=0.0 max=0.0

## By Time Bucket

- `nxt_after_1605_1950` total=5797 stale=2972 rate=51.2679% p50=3125.0 p90=54345.428 max=1452303.125
- `pre_0900` total=5453 stale=2287 rate=41.9402% p50=2168.894 p90=19777.573 max=46632.156
- `regular_1200_1500` total=4964 stale=2799 rate=56.386% p50=3718.0 p90=44440.134 max=106030.345
- `regular_0900_1200` total=3651 stale=1859 rate=50.9176% p50=3239.0 p90=59547.438 max=186906.601
- `post_1530_1605` total=2393 stale=1671 rate=69.8287% p50=9362.228 p90=282691.891 max=579042.479
- `regular_1500_1520` total=685 stale=375 rate=54.7445% p50=3535.73 p90=55959.392 max=106800.004
- `closing_1520_1530` total=568 stale=401 rate=70.5986% p50=4716.217 p90=13873.097 max=94725.038

## By Stage

- `scalping_scanner_fast_precheck` total=14183 stale=8839 rate=62.3211% p50=6575.906 p90=65545.389 max=1452303.125
- `stat_action_decision_snapshot` total=1613 stale=1079 rate=66.894% p50=3437.0 p90=6878.0 max=33683.0
- `ai_holding_reuse_bypass` total=1323 stale=124 rate=9.3726% p50=270.0 p90=2850.0 max=30100.0
- `ai_holding_review` total=1313 stale=161 rate=12.262% p50=1087.0 p90=3402.0 max=31090.0
- `reversal_add_blocked_reason` total=923 stale=585 rate=63.3803% p50=3364.0 p90=6638.0 max=24211.0
- `blocked_strength_momentum` total=823 stale=69 rate=8.384% p50=449.103 p90=2736.474 max=33991.686
- `scalp_entry_action_decision_snapshot` total=719 stale=375 rate=52.1558% p50=3390.0 p90=9550.0 max=27832.0
- `latency_block` total=603 stale=0 rate=0.0% p50=87.067 p90=205.371 max=929.726
- `ai_confirmed_terminal_no_budget` total=259 stale=207 rate=79.9228% p50=5349.0 p90=10727.0 max=27832.0
- `ai_confirmed` total=228 stale=181 rate=79.386% p50=5256.0 p90=11136.0 max=27832.0
- `blocked_vpw` total=191 stale=134 rate=70.1571% p50=4045.973 p90=6964.255 max=11501.447
- `blocked_ai_score` total=178 stale=139 rate=78.0899% p50=5256.0 p90=10727.0 max=27832.0
- `blocked_liquidity` total=165 stale=85 rate=51.5152% p50=3127.596 p90=6463.256 max=11502.758
- `blocked_overbought` total=133 stale=6 rate=4.5113% p50=95.319 p90=2548.063 max=15958.579
- `pyramid_blocked_reason` total=131 stale=59 rate=45.0382% p50=2948.0 p90=5036.0 max=11708.0
- `score65_74_recovery_probe_blocked` total=97 stale=83 rate=85.567% p50=5397.0 p90=9055.0 max=24849.0
- `entry_ai_price_canary_applied` total=94 stale=2 rate=2.1277% p50=1627.0 p90=2269.0 max=4165.0
- `scalp_sim_buy_order_virtual_pending` total=69 stale=67 rate=97.1014% p50=11028.0 p90=15853.0 max=27403.0
- `scalp_sim_pre_submit_overbought_guard_would_pass` total=69 stale=67 rate=97.1014% p50=11028.0 p90=15853.0 max=27403.0
- `strength_momentum_stability_recheck_pending` total=61 stale=0 rate=0.0% p50=632.002 p90=2179.008 max=2877.311

## By Age Source

- `quote_age_ms` total=25717 stale=14735 rate=57.2967% p50=3592.0 p90=46185.952 max=1452303.125
- `pre_submit_ws_snapshot_refresh_age_ms` total=1989 stale=0 rate=0.0% p50=86.124 p90=200.165 max=929.726
- `ws_age_sec` total=1355 stale=142 rate=10.4797% p50=280.0 p90=3120.0 max=30100.0
- `quote_age_at_submit_ms` total=701 stale=414 rate=59.0585% p50=6429.0 p90=14269.0 max=27403.0
- `price_decision_context_age_ms` total=188 stale=4 rate=2.1277% p50=1631.0 p90=2269.0 max=4165.0
- `quote_consistency_ws_age_ms` total=133 stale=12 rate=9.0226% p50=1500.293 p90=2900.201 max=7243.718
- `holding_ws_age_sec` total=46 stale=8 rate=17.3913% p50=535.0 p90=15373.0 max=41045.0
- `quote_consistency_age_ms` total=4 stale=0 rate=0.0% p50=0.0 p90=0.0 max=0.0

## Top Stale Streaks

- `금호건설` `002990` class=scanner_watch stage=scalping_scanner_fast_precheck total=358 stale=337 rate=94.1341% max_run=163 max_age_ms=1215592.992
- `남광토건` `001260` class=scanner_watch stage=scalping_scanner_fast_precheck total=276 stale=262 rate=94.9275% max_run=159 max_age_ms=1260364.316
- `피델릭스` `032580` class=scanner_watch stage=scalping_scanner_fast_precheck total=333 stale=273 rate=81.982% max_run=158 max_age_ms=1452303.125
- `마키나락스` `477850` class=scanner_watch stage=scalping_scanner_fast_precheck total=493 stale=375 rate=76.0649% max_run=145 max_age_ms=529447.524
- `삼성공조` `006660` class=scanner_watch stage=scalping_scanner_fast_precheck total=381 stale=257 rate=67.4541% max_run=90 max_age_ms=515456.396
- `KBI메탈` `024840` class=holding_scale_input stage=stat_action_decision_snapshot total=101 stale=98 rate=97.0297% max_run=86 max_age_ms=15704.0
- `삼성전자` `005930` class=scanner_watch stage=scalping_scanner_fast_precheck total=398 stale=263 rate=66.0804% max_run=86 max_age_ms=71836.9
- `두산에너빌리티` `034020` class=scanner_watch stage=scalping_scanner_fast_precheck total=278 stale=140 rate=50.3597% max_run=84 max_age_ms=151205.725
- `스트라드비젼` `475040` class=scanner_watch stage=scalping_scanner_fast_precheck total=257 stale=185 rate=71.9844% max_run=80 max_age_ms=579042.479
- `테크윙` `089030` class=scanner_watch stage=scalping_scanner_fast_precheck total=254 stale=179 rate=70.4724% max_run=77 max_age_ms=571746.729
- `SK하이닉스` `000660` class=scanner_watch stage=scalping_scanner_fast_precheck total=257 stale=119 rate=46.3035% max_run=77 max_age_ms=44417.078
- `SK이노베이션` `096770` class=holding_scale_input stage=stat_action_decision_snapshot total=74 stale=74 rate=100.0% max_run=74 max_age_ms=12368.0
- `한일홀딩스` `003300` class=scanner_watch stage=scalping_scanner_fast_precheck total=117 stale=114 rate=97.4359% max_run=68 max_age_ms=428967.834
- `한화시스템` `272210` class=scanner_watch stage=scalping_scanner_fast_precheck total=91 stale=86 rate=94.5055% max_run=68 max_age_ms=112420.691
- `와이지-원` `019210` class=scanner_watch stage=scalping_scanner_fast_precheck total=568 stale=347 rate=61.0915% max_run=65 max_age_ms=513040.057

## Scale-In Feature Refresh

- counts: `{'total': 1058, 'attempted_True': 1058, 'applied_False': 899, 'applied_True': 159}`
- applied_true_rate_pct: `15.0284`
- reasons: `[{'key': 'refreshed_feature_still_stale', 'count': 816}, {'key': 'feature_context_refreshed', 'count': 159}, {'key': 'tick_history_missing', 'count': 79}, {'key': 'quote_unusable_after_refresh', 'count': 4}]`
- stale_reason_tokens: `[{'key': 'quote_stale', 'count': 1660}, {'key': 'quote_age_gt_max', 'count': 1660}, {'key': 'tick_aggressor_pressure_unusable', 'count': 834}, {'key': 'tick_context_stale', 'count': 439}, {'key': 'tick_age_gt_max', 'count': 439}, {'key': 'micro_vwap_unavailable', 'count': 30}, {'key': 'features_missing', 'count': 12}, {'key': 'tick_context_unusable', 'count': 1}]`

## WS Repair Log Summary

- path: `/home/ubuntu/KORStockScan/logs/bot_history.log`
- counts: `{'recent_reg_skip': 178, 'first_ws_data': 748, 'persistent_rebuild': 310, 'scanner_cap': 317, 'alternate_limit': 8, 'persistent_no_tick_cooldown': 46, 'persistent_stuck_cooldown': 84, 'persistent_limit': 84}`
- top_codes: `{'persistent_limit': [{'stock_code': '002990', 'count': 79}, {'stock_code': '003300', 'count': 55}, {'stock_code': '031430', 'count': 54}, {'stock_code': '001260', 'count': 48}, {'stock_code': '032580', 'count': 44}, {'stock_code': '028260', 'count': 24}, {'stock_code': '012330', 'count': 22}, {'stock_code': '183190', 'count': 21}, {'stock_code': '477850', 'count': 9}, {'stock_code': '382900', 'count': 9}], 'persistent_no_tick_cooldown': [{'stock_code': '002990', 'count': 22}, {'stock_code': '001260', 'count': 13}, {'stock_code': '032580', 'count': 10}, {'stock_code': '222040', 'count': 1}], 'persistent_rebuild': [{'stock_code': '298000', 'count': 85}, {'stock_code': '002990', 'count': 82}, {'stock_code': '003300', 'count': 76}, {'stock_code': '031430', 'count': 76}, {'stock_code': '001260', 'count': 67}, {'stock_code': '032580', 'count': 61}, {'stock_code': '052420', 'count': 43}, {'stock_code': '183190', 'count': 43}, {'stock_code': '477850', 'count': 37}, {'stock_code': '136150', 'count': 35}], 'persistent_stuck_cooldown': [{'stock_code': '002990', 'count': 71}, {'stock_code': '001260', 'count': 41}, {'stock_code': '032580', 'count': 41}, {'stock_code': '222040', 'count': 1}]}`

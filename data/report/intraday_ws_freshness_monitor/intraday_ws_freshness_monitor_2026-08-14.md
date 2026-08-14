# Intraday WS Freshness Monitor - 2026-08-14

## Decision

- postclose_workorder_required: `3` source-only directives
- runtime_effect: `false`
- allowed_runtime_apply: `false`

## Evidence

- pipeline_event_count: `220584`
- input_processing: `{'mode': 'incremental_streaming_aggregation', 'memory_bounded_streaming': True, 'full_event_list_materialized': False, 'aggregated_event_count': 220584, 'appended_event_count': 8424, 'invalid_json_line_count': 0, 'incremental_state_reason': 'state_reused', 'incremental_state_path': '/home/ubuntu/KORStockScan/data/runtime/intraday_ws_freshness_monitor/intraday_ws_freshness_monitor_2026-08-14.json', 'incremental_state_persisted': True, 'source_offsets': {'pipeline_events': {'path': '/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-08-14.jsonl', 'exists': True, 'cacheable': True, 'device': 66305, 'inode': 1315328, 'size_bytes': 1627512871, 'offset': 1627512871, 'start_offset': 1570823998, 'appended_event_count': 8195, 'source_identity_stable_during_scan': True}, 'threshold_events': {'path': '/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-08-14.jsonl', 'exists': True, 'cacheable': True, 'device': 66305, 'inode': 538150, 'size_bytes': 125028570, 'offset': 125028570, 'start_offset': 123493437, 'appended_event_count': 229, 'source_identity_stable_during_scan': True}}}`
- pipeline_counts: `{'both_ws_stale': 1437, 'decision_stage_stale_backoff': 17166, 'fresh_0d_stale_0b': 1449, 'scout_related': 149130, 'submit_related': 3139, 'trade_tick_quiet': 2405, 'ws_age_observed': 53227}`
- pipeline_rates: `{'trade_tick_quiet_rate_pct': 1.0903, 'subscription_stale_rate_pct': 0.0, 'decision_stage_stale_backoff_rate_pct': 7.7821, 'both_ws_stale_rate_pct': 0.6515, 'provider_none_rate_pct': 0.0}`
- subscription_snapshot_path: `/home/ubuntu/KORStockScan/data/runtime/kiwoom_ws_snapshot/latest.json`
- subscription_snapshot_provenance: `{'source': 'same_day_live_dashboard_snapshot_fallback', 'selected': True, 'selection_reason': 'same_day_schema_match', 'schema_version': 'kiwoom_ws_dashboard_snapshot_v1', 'generated_at': '2026-08-14T16:45:03+09:00', 'subscription_state_available': False}`
- snapshot_summary: `{'row_count': 24, 'freshness_state_counts': {'fresh': 22, 'stale': 1, 'no_tick': 1}, 'repair_reason_counts': {'dashboard_snapshot_subscription_state_unavailable': 24}, 'subscription_stale_like_count': 0, 'subscription_stale_like_rate_pct': 0.0, 'observed_stale_like_count': 2, 'observed_stale_like_rate_pct': 8.3333, 'trade_tick_quiet_count': 3, 'trade_tick_quiet_rate_pct': 12.5, 'repair_recommended_count': 0, 'registered_item_quota_units': 0, 'registered_route_counts': {}, 'registered_market_suffix_counts': {}, 'observed_market_route_counts': {'krx_nxt_integrated': 23, 'unknown': 1}, 'observed_market_suffix_counts': {'_AL': 23, 'KRX': 1}, 'multi_route_registered_count': 0, 'multi_route_registered_rate_pct': 0.0, 'route_repair_policy': 'remove_then_reg_required_for_route_transition', 'top_trade_tick_quiet_symbols': [{'stock_code': '441270', 'last_0b_age_sec': 156.006, 'last_0d_age_sec': 21.796, 'last_trade_cum_volume': None}, {'stock_code': '458870', 'last_0b_age_sec': 143.088, 'last_0d_age_sec': 5.575, 'last_trade_cum_volume': None}, {'stock_code': '161580', 'last_0b_age_sec': 117.805, 'last_0d_age_sec': 28.781, 'last_trade_cum_volume': None}], 'top_repair_symbols': [], 'top_multi_route_symbols': []}`
- source_missing: `[]`

## Metric Contract

- metric_role: `source_quality_gate`
- decision_authority: `ws_freshness_intraday_monitor_source_only`
- primary_decision_metric: `subscription_stale_rate_pct`
- forbidden_uses: `EV,rolling_tuning,MTD_tuning,cumulative_tuning,live_auto_promotion,runtime_apply_bridge,intraday_threshold_mutation,stale_submit_bypass,broker_guard_bypass,provider_route_change,order_price_change,quantity_cap_change,position_cap_release,bot_restart,real_execution_quality_approval`

## Workorder Directives

- `order_ws_decision_stage_stale_backoff_attribution` priority=1 runtime_effect=False title=WS decision-stage stale backoff attribution
- `order_ws_total_stale_escalation` priority=1 runtime_effect=False title=WS total stale escalation
- `order_ws_trade_tick_quiet_low_liquidity_classification` priority=2 runtime_effect=False title=WS trade tick quiet low-liquidity classification

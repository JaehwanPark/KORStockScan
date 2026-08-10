# Intraday WS Freshness Monitor - 2026-08-10

## Decision

- postclose_workorder_required: `3` source-only directives
- runtime_effect: `false`
- allowed_runtime_apply: `false`

## Evidence

- pipeline_event_count: `314701`
- input_processing: `{'mode': 'incremental_streaming_aggregation', 'memory_bounded_streaming': True, 'full_event_list_materialized': False, 'aggregated_event_count': 314701, 'appended_event_count': 6698, 'invalid_json_line_count': 0, 'incremental_state_reason': 'state_reused', 'incremental_state_path': '/home/ubuntu/KORStockScan/data/runtime/intraday_ws_freshness_monitor/intraday_ws_freshness_monitor_2026-08-10.json', 'incremental_state_persisted': True, 'source_offsets': {'pipeline_events': {'path': '/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-08-10.jsonl', 'exists': True, 'cacheable': True, 'device': 66305, 'inode': 1317320, 'size_bytes': 2160673777, 'offset': 2160673777, 'start_offset': 2115206702, 'appended_event_count': 6501, 'source_identity_stable_during_scan': True}, 'threshold_events': {'path': '/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-08-10.jsonl', 'exists': True, 'cacheable': True, 'device': 66305, 'inode': 536241, 'size_bytes': 75950320, 'offset': 75950320, 'start_offset': 74778859, 'appended_event_count': 197, 'source_identity_stable_during_scan': True}}}`
- pipeline_counts: `{'both_ws_stale': 900, 'decision_stage_stale_backoff': 21528, 'fresh_0d_stale_0b': 3767, 'scout_related': 206015, 'submit_related': 2816, 'trade_tick_quiet': 5177, 'ws_age_observed': 88143}`
- pipeline_rates: `{'trade_tick_quiet_rate_pct': 1.6451, 'subscription_stale_rate_pct': 0.0, 'decision_stage_stale_backoff_rate_pct': 6.8408, 'both_ws_stale_rate_pct': 0.286, 'provider_none_rate_pct': 0.0}`
- subscription_snapshot_path: `/home/ubuntu/KORStockScan/data/runtime/kiwoom_ws_snapshot/latest.json`
- subscription_snapshot_provenance: `{'source': 'same_day_live_dashboard_snapshot_fallback', 'selected': True, 'selection_reason': 'same_day_schema_match', 'schema_version': 'kiwoom_ws_dashboard_snapshot_v1', 'generated_at': '2026-08-10T19:14:56+09:00', 'subscription_state_available': False}`
- snapshot_summary: `{'row_count': 13, 'freshness_state_counts': {'fresh': 13}, 'repair_reason_counts': {'dashboard_snapshot_subscription_state_unavailable': 13}, 'subscription_stale_like_count': 0, 'subscription_stale_like_rate_pct': 0.0, 'observed_stale_like_count': 0, 'observed_stale_like_rate_pct': 0.0, 'trade_tick_quiet_count': 2, 'trade_tick_quiet_rate_pct': 15.3846, 'repair_recommended_count': 0, 'registered_item_quota_units': 0, 'registered_route_counts': {}, 'registered_market_suffix_counts': {}, 'observed_market_route_counts': {'krx_nxt_integrated': 13}, 'observed_market_suffix_counts': {'_AL': 13}, 'multi_route_registered_count': 0, 'multi_route_registered_rate_pct': 0.0, 'route_repair_policy': 'remove_then_reg_required_for_route_transition', 'top_trade_tick_quiet_symbols': [{'stock_code': '458870', 'last_0b_age_sec': 39.203, 'last_0d_age_sec': 7.597, 'last_trade_cum_volume': None}, {'stock_code': '092730', 'last_0b_age_sec': 55.508, 'last_0d_age_sec': 8.002, 'last_trade_cum_volume': None}], 'top_repair_symbols': [], 'top_multi_route_symbols': []}`
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

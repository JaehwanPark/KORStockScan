# Intraday WS Freshness Monitor - 2026-08-04

## Decision

- postclose_workorder_required: `3` source-only directives
- runtime_effect: `false`
- allowed_runtime_apply: `false`

## Evidence

- pipeline_event_count: `539150`
- input_processing: `{'mode': 'incremental_streaming_aggregation', 'memory_bounded_streaming': True, 'full_event_list_materialized': False, 'aggregated_event_count': 539150, 'appended_event_count': 18989, 'invalid_json_line_count': 0, 'incremental_state_reason': 'state_reused', 'incremental_state_path': '/home/ubuntu/KORStockScan/data/runtime/intraday_ws_freshness_monitor/intraday_ws_freshness_monitor_2026-08-04.json', 'incremental_state_persisted': True, 'source_offsets': {'pipeline_events': {'path': '/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-08-04.jsonl', 'exists': True, 'cacheable': True, 'device': 66305, 'inode': 1317383, 'size_bytes': 3332650821, 'offset': 3332650821, 'start_offset': 3216087194, 'appended_event_count': 17204, 'source_identity_stable_during_scan': True}, 'threshold_events': {'path': '/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-08-04.jsonl', 'exists': True, 'cacheable': True, 'device': 66305, 'inode': 527069, 'size_bytes': 273937406, 'offset': 273937406, 'start_offset': 266082996, 'appended_event_count': 1785, 'source_identity_stable_during_scan': True}}}`
- pipeline_counts: `{'both_ws_stale': 602, 'decision_stage_stale_backoff': 26817, 'fresh_0d_stale_0b': 2730, 'scout_related': 420763, 'submit_related': 29715, 'trade_tick_quiet': 4906, 'ws_age_observed': 83578}`
- pipeline_rates: `{'trade_tick_quiet_rate_pct': 0.91, 'subscription_stale_rate_pct': 0.0, 'decision_stage_stale_backoff_rate_pct': 4.9739, 'both_ws_stale_rate_pct': 0.1117, 'provider_none_rate_pct': 0.0}`
- subscription_snapshot_path: `/home/ubuntu/KORStockScan/data/runtime/kiwoom_ws_snapshot/latest.json`
- subscription_snapshot_provenance: `{'source': 'same_day_live_dashboard_snapshot_fallback', 'selected': True, 'selection_reason': 'same_day_schema_match', 'schema_version': 'kiwoom_ws_dashboard_snapshot_v1', 'generated_at': '2026-08-04T19:15:01+09:00', 'subscription_state_available': False}`
- snapshot_summary: `{'row_count': 17, 'freshness_state_counts': {'fresh': 17}, 'repair_reason_counts': {'dashboard_snapshot_subscription_state_unavailable': 17}, 'subscription_stale_like_count': 0, 'subscription_stale_like_rate_pct': 0.0, 'observed_stale_like_count': 0, 'observed_stale_like_rate_pct': 0.0, 'trade_tick_quiet_count': 2, 'trade_tick_quiet_rate_pct': 11.7647, 'repair_recommended_count': 0, 'registered_item_quota_units': 0, 'registered_route_counts': {}, 'registered_market_suffix_counts': {}, 'observed_market_route_counts': {'krx_nxt_integrated': 17}, 'observed_market_suffix_counts': {'_AL': 17}, 'multi_route_registered_count': 0, 'multi_route_registered_rate_pct': 0.0, 'route_repair_policy': 'remove_then_reg_required_for_route_transition', 'top_trade_tick_quiet_symbols': [{'stock_code': '081660', 'last_0b_age_sec': 72.102, 'last_0d_age_sec': 23.182, 'last_trade_cum_volume': None}, {'stock_code': '032830', 'last_0b_age_sec': 48.787, 'last_0d_age_sec': 3.001, 'last_trade_cum_volume': None}], 'top_repair_symbols': [], 'top_multi_route_symbols': []}`
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

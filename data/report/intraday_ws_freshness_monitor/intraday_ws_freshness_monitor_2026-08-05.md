# Intraday WS Freshness Monitor - 2026-08-05

## Decision

- postclose_workorder_required: `3` source-only directives
- runtime_effect: `false`
- allowed_runtime_apply: `false`

## Evidence

- pipeline_event_count: `578604`
- input_processing: `{'mode': 'incremental_streaming_aggregation', 'memory_bounded_streaming': True, 'full_event_list_materialized': False, 'aggregated_event_count': 578604, 'appended_event_count': 13957, 'invalid_json_line_count': 0, 'incremental_state_reason': 'state_reused', 'incremental_state_path': '/home/ubuntu/KORStockScan/data/runtime/intraday_ws_freshness_monitor/intraday_ws_freshness_monitor_2026-08-05.json', 'incremental_state_persisted': True, 'source_offsets': {'pipeline_events': {'path': '/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-08-05.jsonl', 'exists': True, 'cacheable': True, 'device': 66305, 'inode': 1324625, 'size_bytes': 3265141813, 'offset': 3265141813, 'start_offset': 3186760516, 'appended_event_count': 13392, 'source_identity_stable_during_scan': True}, 'threshold_events': {'path': '/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-08-05.jsonl', 'exists': True, 'cacheable': True, 'device': 66305, 'inode': 529499, 'size_bytes': 90720882, 'offset': 90720882, 'start_offset': 87984609, 'appended_event_count': 565, 'source_identity_stable_during_scan': True}}}`
- pipeline_counts: `{'both_ws_stale': 1082, 'decision_stage_stale_backoff': 25137, 'fresh_0d_stale_0b': 1945, 'scout_related': 457100, 'submit_related': 8022, 'trade_tick_quiet': 4143, 'ws_age_observed': 83636}`
- pipeline_rates: `{'trade_tick_quiet_rate_pct': 0.716, 'subscription_stale_rate_pct': 0.0, 'decision_stage_stale_backoff_rate_pct': 4.3444, 'both_ws_stale_rate_pct': 0.187, 'provider_none_rate_pct': 0.0}`
- subscription_snapshot_path: `/home/ubuntu/KORStockScan/data/runtime/kiwoom_ws_snapshot/latest.json`
- subscription_snapshot_provenance: `{'source': 'same_day_live_dashboard_snapshot_fallback', 'selected': True, 'selection_reason': 'same_day_schema_match', 'schema_version': 'kiwoom_ws_dashboard_snapshot_v1', 'generated_at': '2026-08-05T19:15:02+09:00', 'subscription_state_available': False}`
- snapshot_summary: `{'row_count': 17, 'freshness_state_counts': {'fresh': 15, 'stale': 1, 'no_tick': 1}, 'repair_reason_counts': {'dashboard_snapshot_subscription_state_unavailable': 17}, 'subscription_stale_like_count': 0, 'subscription_stale_like_rate_pct': 0.0, 'observed_stale_like_count': 2, 'observed_stale_like_rate_pct': 11.7647, 'trade_tick_quiet_count': 3, 'trade_tick_quiet_rate_pct': 17.6471, 'repair_recommended_count': 0, 'registered_item_quota_units': 0, 'registered_route_counts': {}, 'registered_market_suffix_counts': {}, 'observed_market_route_counts': {'krx_nxt_integrated': 16, 'unknown': 1}, 'observed_market_suffix_counts': {'_AL': 16, 'KRX': 1}, 'multi_route_registered_count': 0, 'multi_route_registered_rate_pct': 0.0, 'route_repair_policy': 'remove_then_reg_required_for_route_transition', 'top_trade_tick_quiet_symbols': [{'stock_code': '002380', 'last_0b_age_sec': None, 'last_0d_age_sec': 3.402, 'last_trade_cum_volume': None}, {'stock_code': '094170', 'last_0b_age_sec': None, 'last_0d_age_sec': None, 'last_trade_cum_volume': None}, {'stock_code': '041830', 'last_0b_age_sec': None, 'last_0d_age_sec': 2.998, 'last_trade_cum_volume': None}], 'top_repair_symbols': [], 'top_multi_route_symbols': []}`
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

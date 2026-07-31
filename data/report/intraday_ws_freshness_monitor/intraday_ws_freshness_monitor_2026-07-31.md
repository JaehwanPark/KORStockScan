# Intraday WS Freshness Monitor - 2026-07-31

## Decision

- postclose_workorder_required: `3` source-only directives
- runtime_effect: `false`
- allowed_runtime_apply: `false`

## Evidence

- pipeline_event_count: `406281`
- input_processing: `{'mode': 'full_streaming_rebuild', 'memory_bounded_streaming': True, 'full_event_list_materialized': False, 'aggregated_event_count': 406281, 'appended_event_count': 406281, 'invalid_json_line_count': 0, 'incremental_state_reason': 'state_missing', 'incremental_state_path': None, 'incremental_state_persisted': False, 'source_offsets': {'pipeline_events': {'path': '/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-31.jsonl', 'exists': True, 'cacheable': True, 'device': 66305, 'inode': 1314120, 'size_bytes': 4370652507, 'offset': 4370652507, 'start_offset': 0, 'appended_event_count': 406281, 'source_identity_stable_during_scan': True}, 'threshold_events': {'path': '/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-07-31.jsonl', 'exists': False, 'cacheable': False, 'device': None, 'inode': None, 'size_bytes': 0, 'offset': 0, 'start_offset': 0, 'appended_event_count': 0, 'source_identity_stable_during_scan': True}}}`
- pipeline_counts: `{'scout_related': 296576, 'ws_age_observed': 91296, 'decision_stage_stale_backoff': 32195, 'submit_related': 7396, 'trade_tick_quiet': 2460, 'fresh_0d_stale_0b': 1679, 'both_ws_stale': 849}`
- pipeline_rates: `{'trade_tick_quiet_rate_pct': 0.6055, 'subscription_stale_rate_pct': 0.0, 'decision_stage_stale_backoff_rate_pct': 7.9243, 'both_ws_stale_rate_pct': 0.209, 'provider_none_rate_pct': 0.0}`
- subscription_snapshot_path: `/home/ubuntu/KORStockScan/data/runtime/kiwoom_ws_snapshot/latest.json`
- subscription_snapshot_provenance: `{'source': 'same_day_live_dashboard_snapshot_fallback', 'selected': True, 'selection_reason': 'same_day_schema_match', 'schema_version': 'kiwoom_ws_dashboard_snapshot_v1', 'generated_at': '2026-07-31T20:09:31+09:00', 'subscription_state_available': False}`
- snapshot_summary: `{'row_count': 1, 'freshness_state_counts': {'fresh': 1}, 'repair_reason_counts': {'dashboard_snapshot_subscription_state_unavailable': 1}, 'subscription_stale_like_count': 0, 'subscription_stale_like_rate_pct': 0.0, 'observed_stale_like_count': 0, 'observed_stale_like_rate_pct': 0.0, 'trade_tick_quiet_count': 0, 'trade_tick_quiet_rate_pct': 0.0, 'repair_recommended_count': 0, 'registered_item_quota_units': 0, 'registered_route_counts': {}, 'registered_market_suffix_counts': {}, 'observed_market_route_counts': {'krx_nxt_integrated': 1}, 'observed_market_suffix_counts': {'_AL': 1}, 'multi_route_registered_count': 0, 'multi_route_registered_rate_pct': 0.0, 'route_repair_policy': 'remove_then_reg_required_for_route_transition', 'top_trade_tick_quiet_symbols': [], 'top_repair_symbols': [], 'top_multi_route_symbols': []}`
- source_missing: `['threshold_events']`

## Metric Contract

- metric_role: `source_quality_gate`
- decision_authority: `ws_freshness_intraday_monitor_source_only`
- primary_decision_metric: `subscription_stale_rate_pct`
- forbidden_uses: `EV,rolling_tuning,MTD_tuning,cumulative_tuning,live_auto_promotion,runtime_apply_bridge,intraday_threshold_mutation,stale_submit_bypass,broker_guard_bypass,provider_route_change,order_price_change,quantity_cap_change,position_cap_release,bot_restart,real_execution_quality_approval`

## Workorder Directives

- `order_ws_decision_stage_stale_backoff_attribution` priority=1 runtime_effect=False title=WS decision-stage stale backoff attribution
- `order_ws_total_stale_escalation` priority=1 runtime_effect=False title=WS total stale escalation
- `order_ws_trade_tick_quiet_low_liquidity_classification` priority=2 runtime_effect=False title=WS trade tick quiet low-liquidity classification

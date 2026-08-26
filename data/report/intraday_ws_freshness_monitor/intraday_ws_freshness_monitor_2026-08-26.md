# Intraday WS Freshness Monitor - 2026-08-26

## Decision

- postclose_workorder_required: `3` source-only directives
- runtime_effect: `false`
- allowed_runtime_apply: `false`

## Evidence

- pipeline_event_count: `208489`
- input_processing: `{'mode': 'incremental_streaming_aggregation', 'memory_bounded_streaming': True, 'full_event_list_materialized': False, 'aggregated_event_count': 208489, 'appended_event_count': 5818, 'invalid_json_line_count': 0, 'incremental_state_reason': 'state_reused', 'incremental_state_path': '/home/ubuntu/KORStockScan/data/runtime/intraday_ws_freshness_monitor/intraday_ws_freshness_monitor_2026-08-26.json', 'incremental_state_persisted': True, 'source_offsets': {'pipeline_events': {'path': '/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-08-26.jsonl', 'exists': True, 'cacheable': True, 'device': 66305, 'inode': 1325023, 'size_bytes': 1633552875, 'offset': 1633552875, 'start_offset': 1591353923, 'appended_event_count': 5540, 'source_identity_stable_during_scan': True}, 'threshold_events': {'path': '/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-08-26.jsonl', 'exists': True, 'cacheable': True, 'device': 66305, 'inode': 531497, 'size_bytes': 154962157, 'offset': 154962157, 'start_offset': 153325583, 'appended_event_count': 278, 'source_identity_stable_during_scan': True}}}`
- pipeline_counts: `{'both_ws_stale': 835, 'decision_stage_stale_backoff': 17287, 'fresh_0d_stale_0b': 2343, 'scout_related': 141998, 'submit_related': 4332, 'trade_tick_quiet': 2949, 'ws_age_observed': 43819}`
- pipeline_rates: `{'trade_tick_quiet_rate_pct': 1.4145, 'subscription_stale_rate_pct': 0.0, 'decision_stage_stale_backoff_rate_pct': 8.2916, 'both_ws_stale_rate_pct': 0.4005, 'provider_none_rate_pct': 0.0}`
- causal_attribution: `{'decision_stage_stale_backoff': {'sample_count': 17287, 'reason_counts': {'persistent_ws_gap': 5561, 'scanner_ws_stale_backoff_active': 4796, 'stale_ws_snapshot': 5548, 'ws_snapshot_missing_or_zero': 1382}, 'repair_cycle_state_counts': {'not_observed': 12814, 'persistent_ws_gap': 3114, 'ws_reg_reissued_waiting_snapshot': 1320, 'ws_repair_cycle_waiting_snapshot': 39}, 'recheck_reason_counts': {'not_applicable_active_backoff': 4453, 'not_applicable_ws_stale_backoff_recheck': 5133, 'not_observed': 7701}, 'watchlist_outcome_counts': {'decision_stage_only': 15805, 'evicted': 765, 'retained': 717}}, 'both_ws_stale': {'sample_count': 835, 'repair_cycle_state_counts': {'not_observed': 802, 'persistent_ws_gap': 33}, 'repair_required_counts': {'not_observed': 802, 'required': 33}}, 'trade_tick_quiet': {'sample_count': 2949, 'cumulative_volume_provenance_counts': {'cumulative_volume_missing': 2135, 'signed_tape_only_cumulative_volume_missing': 814}}}`
- subscription_snapshot_path: `/home/ubuntu/KORStockScan/data/runtime/kiwoom_ws_snapshot/latest.json`
- subscription_snapshot_provenance: `{'source': 'same_day_live_dashboard_snapshot_fallback', 'selected': True, 'selection_reason': 'same_day_schema_match', 'schema_version': 'kiwoom_ws_dashboard_snapshot_v1', 'generated_at': '2026-08-26T17:00:03+09:00', 'subscription_state_available': False}`
- snapshot_summary: `{'row_count': 12, 'freshness_state_counts': {'fresh': 8, 'stale': 4}, 'repair_reason_counts': {'dashboard_snapshot_subscription_state_unavailable': 12}, 'subscription_stale_like_count': 0, 'subscription_stale_like_rate_pct': 0.0, 'observed_stale_like_count': 4, 'observed_stale_like_rate_pct': 33.3333, 'trade_tick_quiet_count': 2, 'trade_tick_quiet_rate_pct': 16.6667, 'trade_tick_quiet_cumulative_volume_provenance_counts': {'cumulative_volume_missing': 2}, 'repair_recommended_count': 0, 'registered_item_quota_units': 0, 'registered_route_counts': {}, 'registered_market_suffix_counts': {}, 'observed_market_route_counts': {'krx_nxt_integrated': 12}, 'observed_market_suffix_counts': {'_AL': 12}, 'multi_route_registered_count': 0, 'multi_route_registered_rate_pct': 0.0, 'route_repair_policy': 'remove_then_reg_required_for_route_transition', 'top_trade_tick_quiet_symbols': [{'stock_code': '051600', 'last_0b_age_sec': 33.407, 'last_0d_age_sec': 7.199, 'last_trade_cum_volume': None}, {'stock_code': '078160', 'last_0b_age_sec': None, 'last_0d_age_sec': 3.8, 'last_trade_cum_volume': None}], 'top_repair_symbols': [], 'top_multi_route_symbols': []}`
- source_missing: `[]`

## Metric Contract

- metric_role: `source_quality_gate`
- decision_authority: `ws_freshness_intraday_monitor_source_only`
- primary_decision_metric: `subscription_stale_rate_pct`
- forbidden_uses: `EV,rolling_tuning,MTD_tuning,cumulative_tuning,live_auto_promotion,runtime_apply_bridge,intraday_threshold_mutation,stale_submit_bypass,broker_guard_bypass,provider_route_change,order_price_change,quantity_cap_change,position_cap_release,bot_restart,real_execution_quality_approval`

## Workorder Directives

- `order_ws_decision_stage_stale_backoff_attribution` priority=1 decision=defer_evidence runtime_effect=False title=WS decision-stage stale backoff attribution
- `order_ws_total_stale_escalation` priority=1 decision=defer_evidence runtime_effect=False title=WS total stale escalation
- `order_ws_trade_tick_quiet_low_liquidity_classification` priority=2 decision=defer_evidence runtime_effect=False title=WS trade tick quiet low-liquidity classification

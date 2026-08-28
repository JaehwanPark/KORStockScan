# Intraday WS Freshness Monitor - 2026-08-28

## Decision

- postclose_workorder_required: `3` source-only directives
- runtime_effect: `false`
- allowed_runtime_apply: `false`

## Evidence

- pipeline_event_count: `240066`
- input_processing: `{'mode': 'incremental_streaming_aggregation', 'memory_bounded_streaming': True, 'full_event_list_materialized': False, 'aggregated_event_count': 240066, 'appended_event_count': 5872, 'invalid_json_line_count': 0, 'incremental_state_reason': 'state_reused', 'incremental_state_path': '/home/ubuntu/KORStockScan/data/runtime/intraday_ws_freshness_monitor/intraday_ws_freshness_monitor_2026-08-28.json', 'incremental_state_persisted': True, 'source_offsets': {'pipeline_events': {'path': '/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-08-28.jsonl', 'exists': True, 'cacheable': True, 'device': 66305, 'inode': 1328299, 'size_bytes': 1909412333, 'offset': 1909412333, 'start_offset': 1862139252, 'appended_event_count': 5759, 'source_identity_stable_during_scan': True}, 'threshold_events': {'path': '/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-08-28.jsonl', 'exists': True, 'cacheable': True, 'device': 66305, 'inode': 565256, 'size_bytes': 135717416, 'offset': 135717416, 'start_offset': 134708035, 'appended_event_count': 113, 'source_identity_stable_during_scan': True}}}`
- pipeline_counts: `{'both_ws_stale': 1708, 'decision_stage_stale_backoff': 36283, 'fresh_0d_stale_0b': 3349, 'scout_related': 170304, 'submit_related': 4888, 'trade_tick_quiet': 4225, 'ws_age_observed': 63416}`
- pipeline_rates: `{'trade_tick_quiet_rate_pct': 1.7599, 'subscription_stale_rate_pct': 0.0, 'decision_stage_stale_backoff_rate_pct': 15.1138, 'both_ws_stale_rate_pct': 0.7115, 'provider_none_rate_pct': 0.0}`
- causal_attribution: `{'decision_stage_stale_backoff': {'sample_count': 36283, 'reason_counts': {'persistent_ws_gap': 12885, 'scanner_ws_stale_backoff_active': 10217, 'stale_ws_snapshot': 10723, 'ws_snapshot_missing_or_zero': 2458}, 'repair_cycle_state_counts': {'not_observed': 26903, 'persistent_ws_gap': 6919, 'ws_reg_reissued_waiting_snapshot': 2321, 'ws_repair_cycle_waiting_snapshot': 140}, 'recheck_reason_counts': {'not_applicable_active_backoff': 9317, 'not_applicable_ws_stale_backoff_recheck': 11085, 'not_observed': 15879, 'strong_promotion_fresh_or_rest_recheck': 2}, 'watchlist_outcome_counts': {'decision_stage_only': 33687, 'evicted': 1317, 'retained': 1279}}, 'both_ws_stale': {'sample_count': 1708, 'repair_cycle_state_counts': {'not_observed': 1663, 'persistent_ws_gap': 44, 'ws_reg_reissued_waiting_snapshot': 1}, 'repair_required_counts': {'not_observed': 1663, 'not_required': 1, 'required': 44}}, 'trade_tick_quiet': {'sample_count': 4225, 'cumulative_volume_provenance_counts': {'cumulative_volume_missing': 2573, 'signed_tape_only_cumulative_volume_missing': 1652}}}`
- subscription_snapshot_path: `/home/ubuntu/KORStockScan/data/runtime/kiwoom_ws_snapshot/latest.json`
- subscription_snapshot_provenance: `{'source': 'same_day_live_dashboard_snapshot_fallback', 'selected': True, 'selection_reason': 'same_day_schema_match', 'schema_version': 'kiwoom_ws_dashboard_snapshot_v1', 'generated_at': '2026-08-28T19:15:01+09:00', 'subscription_state_available': False}`
- snapshot_summary: `{'row_count': 33, 'freshness_state_counts': {'fresh': 17, 'stale': 10, 'no_tick': 6}, 'repair_reason_counts': {'dashboard_snapshot_subscription_state_unavailable': 33}, 'subscription_stale_like_count': 0, 'subscription_stale_like_rate_pct': 0.0, 'observed_stale_like_count': 16, 'observed_stale_like_rate_pct': 48.4848, 'trade_tick_quiet_count': 2, 'trade_tick_quiet_rate_pct': 6.0606, 'trade_tick_quiet_cumulative_volume_provenance_counts': {'cumulative_volume_positive': 1, 'cumulative_volume_missing': 1}, 'repair_recommended_count': 0, 'registered_item_quota_units': 0, 'registered_route_counts': {}, 'registered_market_suffix_counts': {}, 'observed_market_route_counts': {'krx_nxt_integrated': 27, 'unknown': 6}, 'observed_market_suffix_counts': {'_AL': 27, 'KRX': 6}, 'multi_route_registered_count': 0, 'multi_route_registered_rate_pct': 0.0, 'route_repair_policy': 'remove_then_reg_required_for_route_transition', 'top_trade_tick_quiet_symbols': [{'stock_code': '124500', 'last_0b_age_sec': 33.701, 'last_0d_age_sec': 0.775, 'last_trade_cum_volume': 1446717.0}, {'stock_code': '237880', 'last_0b_age_sec': None, 'last_0d_age_sec': 0.988, 'last_trade_cum_volume': None}], 'top_repair_symbols': [], 'top_multi_route_symbols': []}`
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

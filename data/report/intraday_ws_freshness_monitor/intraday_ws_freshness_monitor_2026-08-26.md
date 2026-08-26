# Intraday WS Freshness Monitor - 2026-08-26

## Decision

- postclose_workorder_required: `3` source-only directives
- runtime_effect: `false`
- allowed_runtime_apply: `false`

## Evidence

- pipeline_event_count: `259098`
- input_processing: `{'mode': 'incremental_streaming_aggregation', 'memory_bounded_streaming': True, 'full_event_list_materialized': False, 'aggregated_event_count': 259098, 'appended_event_count': 5260, 'invalid_json_line_count': 0, 'incremental_state_reason': 'state_reused', 'incremental_state_path': '/home/ubuntu/KORStockScan/data/runtime/intraday_ws_freshness_monitor/intraday_ws_freshness_monitor_2026-08-26.json', 'incremental_state_persisted': True, 'source_offsets': {'pipeline_events': {'path': '/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-08-26.jsonl', 'exists': True, 'cacheable': True, 'device': 66305, 'inode': 1325023, 'size_bytes': 1979260127, 'offset': 1979260127, 'start_offset': 1943718228, 'appended_event_count': 4895, 'source_identity_stable_during_scan': True}, 'threshold_events': {'path': '/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-08-26.jsonl', 'exists': True, 'cacheable': True, 'device': 66305, 'inode': 531497, 'size_bytes': 173605741, 'offset': 173605741, 'start_offset': 171696908, 'appended_event_count': 365, 'source_identity_stable_during_scan': True}}}`
- pipeline_counts: `{'both_ws_stale': 982, 'decision_stage_stale_backoff': 23465, 'fresh_0d_stale_0b': 2916, 'scout_related': 178717, 'submit_related': 5498, 'trade_tick_quiet': 3696, 'ws_age_observed': 57515}`
- pipeline_rates: `{'trade_tick_quiet_rate_pct': 1.4265, 'subscription_stale_rate_pct': 0.0, 'decision_stage_stale_backoff_rate_pct': 9.0564, 'both_ws_stale_rate_pct': 0.379, 'provider_none_rate_pct': 0.0}`
- causal_attribution: `{'decision_stage_stale_backoff': {'sample_count': 23465, 'reason_counts': {'persistent_ws_gap': 7938, 'scanner_ws_stale_backoff_active': 6410, 'stale_ws_snapshot': 7387, 'ws_snapshot_missing_or_zero': 1730}, 'repair_cycle_state_counts': {'not_observed': 17273, 'persistent_ws_gap': 4454, 'ws_reg_reissued_waiting_snapshot': 1664, 'ws_repair_cycle_waiting_snapshot': 74}, 'recheck_reason_counts': {'not_applicable_active_backoff': 6170, 'not_applicable_ws_stale_backoff_recheck': 7035, 'not_observed': 10260}, 'watchlist_outcome_counts': {'decision_stage_only': 21662, 'evicted': 929, 'retained': 874}}, 'both_ws_stale': {'sample_count': 982, 'repair_cycle_state_counts': {'not_observed': 946, 'persistent_ws_gap': 35, 'ws_reg_reissued_waiting_snapshot': 1}, 'repair_required_counts': {'not_observed': 946, 'not_required': 1, 'required': 35}}, 'trade_tick_quiet': {'sample_count': 3696, 'cumulative_volume_provenance_counts': {'cumulative_volume_missing': 2507, 'signed_tape_only_cumulative_volume_missing': 1189}}}`
- subscription_snapshot_path: `/home/ubuntu/KORStockScan/data/runtime/kiwoom_ws_snapshot/latest.json`
- subscription_snapshot_provenance: `{'source': 'same_day_live_dashboard_snapshot_fallback', 'selected': True, 'selection_reason': 'same_day_schema_match', 'schema_version': 'kiwoom_ws_dashboard_snapshot_v1', 'generated_at': '2026-08-26T19:15:02+09:00', 'subscription_state_available': False}`
- snapshot_summary: `{'row_count': 20, 'freshness_state_counts': {'fresh': 16, 'stale': 3, 'no_tick': 1}, 'repair_reason_counts': {'dashboard_snapshot_subscription_state_unavailable': 20}, 'subscription_stale_like_count': 0, 'subscription_stale_like_rate_pct': 0.0, 'observed_stale_like_count': 4, 'observed_stale_like_rate_pct': 20.0, 'trade_tick_quiet_count': 3, 'trade_tick_quiet_rate_pct': 15.0, 'trade_tick_quiet_cumulative_volume_provenance_counts': {'cumulative_volume_missing': 3}, 'repair_recommended_count': 0, 'registered_item_quota_units': 0, 'registered_route_counts': {}, 'registered_market_suffix_counts': {}, 'observed_market_route_counts': {'krx_nxt_integrated': 19, 'unknown': 1}, 'observed_market_suffix_counts': {'_AL': 19, 'KRX': 1}, 'multi_route_registered_count': 0, 'multi_route_registered_rate_pct': 0.0, 'route_repair_policy': 'remove_then_reg_required_for_route_transition', 'top_trade_tick_quiet_symbols': [{'stock_code': '111770', 'last_0b_age_sec': 315.795, 'last_0d_age_sec': 3.394, 'last_trade_cum_volume': None}, {'stock_code': '031980', 'last_0b_age_sec': 227.506, 'last_0d_age_sec': 26.2, 'last_trade_cum_volume': None}, {'stock_code': '023530', 'last_0b_age_sec': None, 'last_0d_age_sec': 5.998, 'last_trade_cum_volume': None}], 'top_repair_symbols': [], 'top_multi_route_symbols': []}`
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

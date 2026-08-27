# Intraday WS Freshness Monitor - 2026-08-27

## Decision

- postclose_workorder_required: `3` source-only directives
- runtime_effect: `false`
- allowed_runtime_apply: `false`

## Evidence

- pipeline_event_count: `273456`
- input_processing: `{'mode': 'incremental_streaming_aggregation', 'memory_bounded_streaming': True, 'full_event_list_materialized': False, 'aggregated_event_count': 273456, 'appended_event_count': 6715, 'invalid_json_line_count': 0, 'incremental_state_reason': 'state_reused', 'incremental_state_path': '/home/ubuntu/KORStockScan/data/runtime/intraday_ws_freshness_monitor/intraday_ws_freshness_monitor_2026-08-27.json', 'incremental_state_persisted': True, 'source_offsets': {'pipeline_events': {'path': '/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-08-27.jsonl', 'exists': True, 'cacheable': True, 'device': 66305, 'inode': 1328160, 'size_bytes': 2138965358, 'offset': 2138965358, 'start_offset': 2090282994, 'appended_event_count': 6337, 'source_identity_stable_during_scan': True}, 'threshold_events': {'path': '/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-08-27.jsonl', 'exists': True, 'cacheable': True, 'device': 66305, 'inode': 527202, 'size_bytes': 171174216, 'offset': 171174216, 'start_offset': 169006724, 'appended_event_count': 378, 'source_identity_stable_during_scan': True}}}`
- pipeline_counts: `{'both_ws_stale': 526, 'decision_stage_stale_backoff': 22081, 'fresh_0d_stale_0b': 3017, 'scout_related': 196781, 'submit_related': 8024, 'trade_tick_quiet': 3873, 'ws_age_observed': 67756}`
- pipeline_rates: `{'trade_tick_quiet_rate_pct': 1.4163, 'subscription_stale_rate_pct': 0.0, 'decision_stage_stale_backoff_rate_pct': 8.0748, 'both_ws_stale_rate_pct': 0.1924, 'provider_none_rate_pct': 0.0}`
- causal_attribution: `{'decision_stage_stale_backoff': {'sample_count': 22081, 'reason_counts': {'persistent_ws_gap': 7303, 'scanner_ws_stale_backoff_active': 5275, 'stale_ws_snapshot': 7985, 'ws_snapshot_missing_or_zero': 1518}, 'repair_cycle_state_counts': {'not_observed': 16040, 'persistent_ws_gap': 4415, 'ws_reg_reissued_waiting_snapshot': 1527, 'ws_repair_cycle_waiting_snapshot': 99}, 'recheck_reason_counts': {'not_applicable_active_backoff': 6004, 'not_applicable_ws_stale_backoff_recheck': 6608, 'not_observed': 9468, 'strong_promotion_fresh_or_rest_recheck': 1}, 'watchlist_outcome_counts': {'decision_stage_only': 20595, 'evicted': 789, 'retained': 697}}, 'both_ws_stale': {'sample_count': 526, 'repair_cycle_state_counts': {'not_observed': 508, 'persistent_ws_gap': 17, 'ws_reg_reissued_waiting_snapshot': 1}, 'repair_required_counts': {'not_observed': 508, 'not_required': 1, 'required': 17}}, 'trade_tick_quiet': {'sample_count': 3873, 'cumulative_volume_provenance_counts': {'cumulative_volume_missing': 2741, 'signed_tape_only_cumulative_volume_missing': 1132}}}`
- subscription_snapshot_path: `/home/ubuntu/KORStockScan/data/runtime/kiwoom_ws_snapshot/latest.json`
- subscription_snapshot_provenance: `{'source': 'same_day_live_dashboard_snapshot_fallback', 'selected': True, 'selection_reason': 'same_day_schema_match', 'schema_version': 'kiwoom_ws_dashboard_snapshot_v1', 'generated_at': '2026-08-27T19:15:01+09:00', 'subscription_state_available': False}`
- snapshot_summary: `{'row_count': 19, 'freshness_state_counts': {'fresh': 14, 'stale': 4, 'no_tick': 1}, 'repair_reason_counts': {'dashboard_snapshot_subscription_state_unavailable': 19}, 'subscription_stale_like_count': 0, 'subscription_stale_like_rate_pct': 0.0, 'observed_stale_like_count': 5, 'observed_stale_like_rate_pct': 26.3158, 'trade_tick_quiet_count': 3, 'trade_tick_quiet_rate_pct': 15.7895, 'trade_tick_quiet_cumulative_volume_provenance_counts': {'cumulative_volume_positive': 1, 'cumulative_volume_missing': 2}, 'repair_recommended_count': 0, 'registered_item_quota_units': 0, 'registered_route_counts': {}, 'registered_market_suffix_counts': {}, 'observed_market_route_counts': {'krx_nxt_integrated': 18, 'unknown': 1}, 'observed_market_suffix_counts': {'_AL': 18, 'KRX': 1}, 'multi_route_registered_count': 0, 'multi_route_registered_rate_pct': 0.0, 'route_repair_policy': 'remove_then_reg_required_for_route_transition', 'top_trade_tick_quiet_symbols': [{'stock_code': '460860', 'last_0b_age_sec': 68.797, 'last_0d_age_sec': 6.19, 'last_trade_cum_volume': 1524696.0}, {'stock_code': '000500', 'last_0b_age_sec': None, 'last_0d_age_sec': 0.0, 'last_trade_cum_volume': None}, {'stock_code': '298040', 'last_0b_age_sec': None, 'last_0d_age_sec': 1.982, 'last_trade_cum_volume': None}], 'top_repair_symbols': [], 'top_multi_route_symbols': []}`
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

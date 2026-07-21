# Intraday WS Freshness Monitor - 2026-07-20

## Decision

- postclose_workorder_required: `2` source-only directives
- runtime_effect: `false`
- allowed_runtime_apply: `false`

## Evidence

- pipeline_event_count: `166830`
- pipeline_counts: `{'scout_related': 142092, 'ws_age_observed': 12940, 'submit_related': 316, 'trade_tick_quiet': 1136, 'fresh_0d_stale_0b': 1136, 'both_ws_stale': 1094}`
- pipeline_rates: `{'trade_tick_quiet_rate_pct': 0.6809, 'subscription_stale_rate_pct': 0.0, 'both_ws_stale_rate_pct': 0.6558, 'provider_none_rate_pct': 0.0}`
- snapshot_summary: `{'row_count': 0, 'freshness_state_counts': {}, 'repair_reason_counts': {}, 'subscription_stale_like_count': 0, 'subscription_stale_like_rate_pct': 0.0, 'trade_tick_quiet_count': 0, 'trade_tick_quiet_rate_pct': 0.0, 'repair_recommended_count': 0, 'registered_item_quota_units': 0, 'registered_route_counts': {}, 'registered_market_suffix_counts': {}, 'multi_route_registered_count': 0, 'multi_route_registered_rate_pct': 0.0, 'route_repair_policy': 'remove_then_reg_required_for_route_transition', 'top_trade_tick_quiet_symbols': [], 'top_repair_symbols': [], 'top_multi_route_symbols': []}`
- source_missing: `['threshold_events']`

## Metric Contract

- metric_role: `source_quality_gate`
- decision_authority: `ws_freshness_intraday_monitor_source_only`
- primary_decision_metric: `subscription_stale_rate_pct`
- forbidden_uses: `EV,rolling_tuning,MTD_tuning,cumulative_tuning,live_auto_promotion,runtime_apply_bridge,intraday_threshold_mutation,stale_submit_bypass,broker_guard_bypass,provider_route_change,order_price_change,quantity_cap_change,position_cap_release,bot_restart,real_execution_quality_approval`

## Workorder Directives

- `order_ws_total_stale_escalation` priority=1 runtime_effect=False title=WS total stale escalation
- `order_ws_trade_tick_quiet_low_liquidity_classification` priority=2 runtime_effect=False title=WS trade tick quiet low-liquidity classification

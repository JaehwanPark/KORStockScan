# Codebase Performance Workorder Source - 2026-07-20

## Policy
- authority: `ops_performance_workorder_source`
- runtime_effect: `false`
- strategy_effect: `false`
- data_quality_effect: `false`
- tuning_axis_effect: `false`
- implementation requires explicit user instruction

## Summary
- source_doc: `/home/ubuntu/KORStockScan/docs/codebase-performance-bottleneck-analysis.md`
- source_doc_hash: `ffb2c2b9d6b8bf251d4f5665f1ea4ead0f680864428241fdcd6119d57f20722f`
- accepted/implemented/pending/deferred/rejected: `8` / `8` / `0` / `2` / `2`

## Accepted Candidates
- `order_perf_buy_funnel_json_scan` priority=`1` risk=`low` subsystem=`buy_funnel_sentinel` implementation_status=`implemented`
- `order_perf_daily_report_bulk_history` priority=`2` risk=`medium` subsystem=`daily_report` implementation_status=`implemented`
- `order_perf_daily_report_engine_singleton` priority=`3` risk=`low` subsystem=`daily_report` implementation_status=`implemented`
- `order_perf_recommend_update_vectorization` priority=`4` risk=`low` subsystem=`swing_daily_recommendation` implementation_status=`implemented`
- `order_perf_swing_simulation_iteration` priority=`5` risk=`medium` subsystem=`swing_daily_simulation` implementation_status=`implemented`
- `order_perf_monitor_snapshot_stream_tail` priority=`6` risk=`low` subsystem=`monitor_snapshot` implementation_status=`implemented`
- `order_perf_final_ensemble_records` priority=`7` risk=`low` subsystem=`final_ensemble_scanner` implementation_status=`implemented`
- `order_perf_sentinel_event_cache_incremental_review` priority=`8` risk=`medium` subsystem=`sentinel_event_cache` implementation_status=`implemented`

## Deferred Candidates
- `order_perf_kiwoom_orders_http_session_review` reason=`broker request lifecycle may change; requires manual review before implementation`
- `order_perf_config_cache_scope_review` reason=`runtime config reload semantics are not yet bounded`

## Rejected Candidates
- `order_perf_kiwoom_ws_tick_parse_fastpath` reason=`quote/data-quality semantics can change; requires separate data-quality approval owner`
- `order_perf_raw_event_suppression_out_of_scope` reason=`raw suppression is governed by pipeline event V2 suppress guard`

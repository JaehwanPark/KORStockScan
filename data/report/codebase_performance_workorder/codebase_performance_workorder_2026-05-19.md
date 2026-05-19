# Codebase Performance Workorder Source - 2026-05-19

## Policy
- authority: `ops_performance_workorder_source`
- runtime_effect: `false`
- strategy_effect: `false`
- data_quality_effect: `false`
- tuning_axis_effect: `false`
- implementation requires explicit user instruction

## Summary
- source_doc: `/home/ubuntu/KORStockScan/docs/codebase-performance-bottleneck-analysis.md`
- source_doc_hash: `6bc37e5b3d13f356392d83e4ec1ecdcd2f57a05a0f9bc58f6329a1ea20fbed88`
- accepted/implemented/pending/deferred/rejected: `7` / `7` / `0` / `3` / `2`

## Accepted Candidates
- `order_perf_buy_funnel_json_scan` priority=`1` risk=`low` subsystem=`buy_funnel_sentinel` implementation_status=`implemented`
- `order_perf_daily_report_bulk_history` priority=`2` risk=`medium` subsystem=`daily_report` implementation_status=`implemented`
- `order_perf_daily_report_engine_singleton` priority=`3` risk=`low` subsystem=`daily_report` implementation_status=`implemented`
- `order_perf_recommend_update_vectorization` priority=`4` risk=`low` subsystem=`swing_daily_recommendation` implementation_status=`implemented`
- `order_perf_swing_simulation_iteration` priority=`5` risk=`medium` subsystem=`swing_daily_simulation` implementation_status=`implemented`
- `order_perf_monitor_snapshot_stream_tail` priority=`6` risk=`low` subsystem=`monitor_snapshot` implementation_status=`implemented`
- `order_perf_final_ensemble_records` priority=`7` risk=`low` subsystem=`final_ensemble_scanner` implementation_status=`implemented`

## Deferred Candidates
- `order_perf_kiwoom_orders_http_session_review` reason=`broker request lifecycle may change; requires manual review before implementation`
- `order_perf_config_cache_scope_review` reason=`runtime config reload semantics are not yet bounded`
- `order_perf_dashboard_db_pool_review` reason=`legacy DB write is opt-in and pool lifetime risk needs separate review`

## Rejected Candidates
- `order_perf_kiwoom_ws_tick_parse_fastpath` reason=`quote/data-quality semantics can change; requires separate data-quality approval owner`
- `order_perf_raw_event_suppression_out_of_scope` reason=`raw suppression is governed by pipeline event V2 suppress guard`

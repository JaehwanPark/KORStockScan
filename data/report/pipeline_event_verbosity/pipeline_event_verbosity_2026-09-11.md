# Pipeline Event Verbosity 2026-09-11

## 판정

- state: `v2_shadow_parity_fail`
- recommended_workorder_state: `block_suppress_and_fix_shadow`
- runtime_effect: `False`
- raw_suppression_enabled: `False`

## 근거

- raw_size_bytes: `5626182346`
- raw_storage_size_bytes: `5626182346`
- raw_line_count: `344412`
- high_volume_line_count: `155243`
- high_volume_byte_share_pct: `21.65`
- potential_suppressible_event_count: `0`
- potential_suppressible_bytes (not realized savings): `0`
- identity_ok: `False`
- flush_deadline / expired: `2026-09-11T20:01:59.167890+09:00` / `True`
- optimization: `no_suppressible_events`; raw reduction 0; runtime/economic benefit unmeasured
- producer timing (measured, not improvement): `{"schema_version": 1, "timing_contract": "producer_publish_and_submit_v1", "target_date": "2026-09-11", "writer_pid": 553860, "manifest_sha256": "523fd137d9c28240ade52e469f11e12deb0661805f8d002df5775032f4b96f53", "last_flush_duration_ms": 1.554, "duration_scope": "summary_and_canonical_manifest_publish_excludes_health_receipt", "submit_sample_window": "last_2048_process_calls", "submit_duration_scope": "summary_submit_only_excludes_raw_writer_and_orders", "submit_sample_count": 2048, "submit_count": 156870, "rejected_summary_count": 0, "submit_p95_ms": 1.343, "submit_p99_ms": 5.502, "submit_max_ms": 35.467, "runtime_effect": false, "allowed_runtime_apply": false, "status": "observed_no_comparable_baseline", "path": "/home/ubuntu/KORStockScan/data/pipeline_event_summaries/pipeline_event_producer_health_2026-09-11_553860.json", "runtime_latency_improvement": null}`
- producer_summary_exists: `True`
- producer_manifest_mode: `shadow`
- parity_ok: `False`
- raw_derived_event_count: `155243`
- producer_event_count: `154793`
- producer_start_complete: `True`
- producer_pending_flush: `False`
- common_watermark_ok: `False`
- comparison_watermark: `2026-09-11T19:59:00+09:00`
- raw_tail_excluded_event_count: `359`
- coverage raw/producer: `2026-09-11T08:23:40.529544` / `2026-09-11T08:23:40.529544`
- previous_parity_pass_count: `0`

## 금지선

- 이 report는 diagnostic aggregation이며 threshold/provider/order/bot restart 권한이 없다.
- 원본 생략 경로는 소비자 보존 계약 미구현으로 비활성이다. 양수 EV/실체결/2일 대기를 진단 수리 조건으로 붙이지 않는다.

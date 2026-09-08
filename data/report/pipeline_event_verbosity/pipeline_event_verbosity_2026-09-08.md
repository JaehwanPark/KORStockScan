# Pipeline Event Verbosity 2026-09-08

## 판정

- state: `v2_shadow_parity_fail`
- recommended_workorder_state: `block_suppress_and_fix_shadow`
- runtime_effect: `False`
- raw_suppression_enabled: `False`

## 근거

- raw_size_bytes: `5682160544`
- raw_storage_size_bytes: `5682160544`
- raw_line_count: `379029`
- high_volume_line_count: `204673`
- high_volume_byte_share_pct: `28.05`
- potential_suppressible_event_count: `0`
- potential_suppressible_bytes (not realized savings): `0`
- identity_ok: `False`
- flush_deadline / expired: `2026-09-08T20:01:59.831224+09:00` / `True`
- optimization: `no_suppressible_events`; raw reduction 0; runtime/economic benefit unmeasured
- producer timing (measured, not improvement): `{"schema_version": 1, "timing_contract": "producer_publish_and_submit_v1", "target_date": "2026-09-08", "writer_pid": 992430, "manifest_sha256": "2fd47c01d3024c751e83551324caf2e25c991e2d9e6e10d14bbfdd9e6aa6d528", "last_flush_duration_ms": 0.861, "duration_scope": "summary_and_canonical_manifest_publish_excludes_health_receipt", "submit_sample_window": "last_2048_process_calls", "submit_duration_scope": "summary_submit_only_excludes_raw_writer_and_orders", "submit_sample_count": 2048, "submit_count": 139353, "rejected_summary_count": 0, "submit_p95_ms": 0.882, "submit_p99_ms": 1.339, "submit_max_ms": 5.567, "runtime_effect": false, "allowed_runtime_apply": false, "status": "observed_no_comparable_baseline", "path": "/home/ubuntu/KORStockScan/data/pipeline_event_summaries/pipeline_event_producer_health_2026-09-08_992430.json", "runtime_latency_improvement": null}`
- producer_summary_exists: `True`
- producer_manifest_mode: `shadow`
- parity_ok: `False`
- raw_derived_event_count: `204673`
- producer_event_count: `204524`
- producer_start_complete: `True`
- producer_pending_flush: `False`
- common_watermark_ok: `False`
- comparison_watermark: `2026-09-08T19:59:00+09:00`
- raw_tail_excluded_event_count: `146`
- coverage raw/producer: `2026-09-08T08:03:19.776987` / `2026-09-08T08:03:19`
- previous_parity_pass_count: `0`

## 금지선

- 이 report는 diagnostic aggregation이며 threshold/provider/order/bot restart 권한이 없다.
- 원본 생략 경로는 소비자 보존 계약 미구현으로 비활성이다. 양수 EV/실체결/2일 대기를 진단 수리 조건으로 붙이지 않는다.

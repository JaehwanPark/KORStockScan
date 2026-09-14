# Pipeline Event Verbosity 2026-09-14

## 판정

- state: `v2_shadow_parity_fail`
- recommended_workorder_state: `block_suppress_and_fix_shadow`
- runtime_effect: `False`
- raw_suppression_enabled: `False`

## 근거

- raw_size_bytes: `6324380621`
- raw_storage_size_bytes: `6324380621`
- raw_line_count: `377361`
- high_volume_line_count: `173836`
- high_volume_byte_share_pct: `20.74`
- potential_suppressible_event_count: `0`
- potential_suppressible_bytes (not realized savings): `0`
- identity_ok: `False`
- flush_deadline / expired: `2026-09-14T20:01:59.779488+09:00` / `True`
- optimization: `no_suppressible_events`; raw reduction 0; runtime/economic benefit unmeasured
- producer timing (measured, not improvement): `{"schema_version": 1, "timing_contract": "producer_publish_and_submit_v1", "target_date": "2026-09-14", "writer_pid": 6832, "manifest_sha256": "b8b571bb63597a276bbffe67b7d8161d599c2a0d17782748a64f78461dbb4452", "last_flush_duration_ms": 0.65, "duration_scope": "summary_and_canonical_manifest_publish_excludes_health_receipt", "submit_sample_window": "last_2048_process_calls", "submit_duration_scope": "summary_submit_only_excludes_raw_writer_and_orders", "submit_sample_count": 2048, "submit_count": 45247, "rejected_summary_count": 0, "submit_p95_ms": 13.057, "submit_p99_ms": 23.834, "submit_max_ms": 263.793, "runtime_effect": false, "allowed_runtime_apply": false, "status": "observed_no_comparable_baseline", "path": "/home/ubuntu/KORStockScan/data/pipeline_event_summaries/pipeline_event_producer_health_2026-09-14_6832.json", "runtime_latency_improvement": null}`
- producer_summary_exists: `True`
- producer_manifest_mode: `shadow`
- parity_ok: `False`
- raw_derived_event_count: `173836`
- producer_event_count: `172117`
- producer_start_complete: `True`
- producer_pending_flush: `False`
- common_watermark_ok: `False`
- comparison_watermark: `2026-09-14T19:59:00+09:00`
- raw_tail_excluded_event_count: `148`
- coverage raw/producer: `2026-09-14T07:55:23.030006` / `2026-09-14T07:55:23.030006`
- previous_parity_pass_count: `0`

## 금지선

- 이 report는 diagnostic aggregation이며 threshold/provider/order/bot restart 권한이 없다.
- 원본 생략 경로는 소비자 보존 계약 미구현으로 비활성이다. 양수 EV/실체결/2일 대기를 진단 수리 조건으로 붙이지 않는다.

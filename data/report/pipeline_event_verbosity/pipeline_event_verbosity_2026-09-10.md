# Pipeline Event Verbosity 2026-09-10

## 판정

- state: `v2_shadow_parity_fail`
- recommended_workorder_state: `block_suppress_and_fix_shadow`
- runtime_effect: `False`
- raw_suppression_enabled: `False`

## 근거

- raw_size_bytes: `5987403448`
- raw_storage_size_bytes: `5987403448`
- raw_line_count: `385928`
- high_volume_line_count: `179568`
- high_volume_byte_share_pct: `23.29`
- potential_suppressible_event_count: `0`
- potential_suppressible_bytes (not realized savings): `0`
- identity_ok: `False`
- flush_deadline / expired: `2026-09-10T20:01:59.809962+09:00` / `True`
- optimization: `no_suppressible_events`; raw reduction 0; runtime/economic benefit unmeasured
- producer timing (measured, not improvement): `{"schema_version": 1, "timing_contract": "producer_publish_and_submit_v1", "target_date": "2026-09-10", "writer_pid": 1048327, "manifest_sha256": "5d4d7deb67cb2b5c601e25078dfcfd52cfdaa2b18f2b86ea174281f479185f8a", "last_flush_duration_ms": 3.836, "duration_scope": "summary_and_canonical_manifest_publish_excludes_health_receipt", "submit_sample_window": "last_2048_process_calls", "submit_duration_scope": "summary_submit_only_excludes_raw_writer_and_orders", "submit_sample_count": 2048, "submit_count": 84283, "rejected_summary_count": 0, "submit_p95_ms": 0.928, "submit_p99_ms": 5.294, "submit_max_ms": 43.737, "runtime_effect": false, "allowed_runtime_apply": false, "status": "observed_no_comparable_baseline", "path": "/home/ubuntu/KORStockScan/data/pipeline_event_summaries/pipeline_event_producer_health_2026-09-10_1048327.json", "runtime_latency_improvement": null}`
- producer_summary_exists: `True`
- producer_manifest_mode: `shadow`
- parity_ok: `False`
- raw_derived_event_count: `179568`
- producer_event_count: `178681`
- producer_start_complete: `True`
- producer_pending_flush: `False`
- common_watermark_ok: `False`
- comparison_watermark: `2026-09-10T19:59:00+09:00`
- raw_tail_excluded_event_count: `118`
- coverage raw/producer: `2026-09-10T08:03:18.376597` / `2026-09-10T08:03:18.376597`
- previous_parity_pass_count: `0`

## 금지선

- 이 report는 diagnostic aggregation이며 threshold/provider/order/bot restart 권한이 없다.
- 원본 생략 경로는 소비자 보존 계약 미구현으로 비활성이다. 양수 EV/실체결/2일 대기를 진단 수리 조건으로 붙이지 않는다.

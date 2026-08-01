# Pipeline Event Verbosity 2026-07-31

## 판정

- state: `v2_shadow_partial_coverage`
- recommended_workorder_state: `observe_next_full_coverage_day`
- runtime_effect: `False`
- raw_suppression_enabled: `False`

## 근거

- raw_size_bytes: `4370652507`
- raw_storage_size_bytes: `386104760`
- raw_line_count: `406281`
- high_volume_line_count: `364634`
- high_volume_byte_share_pct: `90.26`
- producer_summary_exists: `True`
- producer_manifest_mode: `shadow`
- parity_ok: `False`
- raw_derived_event_count: `364634`
- producer_event_count: `31078`
- producer_start_complete: `False`
- producer_pending_flush: `True`
- coverage raw/producer: `2026-07-31T07:55:20.089457` / `2026-07-31T08:10:09`
- previous_parity_pass_count: `0`

## 금지선

- 이 report는 diagnostic aggregation이며 threshold/provider/order/bot restart 권한이 없다.
- `suppress_candidate`도 기본 OFF 설계 후보일 뿐 즉시 raw suppression 적용 근거가 아니다.

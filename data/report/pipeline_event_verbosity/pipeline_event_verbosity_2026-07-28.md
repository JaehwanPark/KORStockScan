# Pipeline Event Verbosity 2026-07-28

## 판정

- state: `v2_shadow_no_eligible_events`
- recommended_workorder_state: `observe_no_eligible_events`
- runtime_effect: `False`
- raw_suppression_enabled: `False`

## 근거

- raw_size_bytes: `3133672029`
- raw_storage_size_bytes: `3133672029`
- raw_line_count: `500734`
- high_volume_line_count: `0`
- high_volume_byte_share_pct: `0.0`
- producer_summary_exists: `False`
- producer_manifest_mode: `-`
- parity_ok: `True`
- raw_derived_event_count: `0`
- producer_event_count: `0`
- previous_parity_pass_count: `0`

## 금지선

- 이 report는 diagnostic aggregation이며 threshold/provider/order/bot restart 권한이 없다.
- `suppress_candidate`도 기본 OFF 설계 후보일 뿐 즉시 raw suppression 적용 근거가 아니다.

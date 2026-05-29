# Pipeline Event Verbosity 2026-05-29

## 판정

- state: `v2_shadow_pending_flush`
- recommended_workorder_state: `observe_pending_next_flush`
- runtime_effect: `False`
- raw_suppression_enabled: `False`

## 근거

- raw_size_bytes: `1182161146`
- raw_storage_size_bytes: `1182161146`
- raw_line_count: `273229`
- high_volume_line_count: `78324`
- high_volume_byte_share_pct: `12.14`
- producer_summary_exists: `True`
- producer_manifest_mode: `shadow`
- parity_ok: `False`
- raw_derived_event_count: `78324`
- producer_event_count: `78200`
- previous_parity_pass_count: `0`

## 금지선

- 이 report는 diagnostic aggregation이며 threshold/provider/order/bot restart 권한이 없다.
- `suppress_candidate`도 기본 OFF 설계 후보일 뿐 즉시 raw suppression 적용 근거가 아니다.

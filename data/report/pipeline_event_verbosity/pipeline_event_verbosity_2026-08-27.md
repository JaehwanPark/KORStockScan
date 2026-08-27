# Pipeline Event Verbosity 2026-08-27

## 판정

- state: `v2_shadow_pending_flush`
- recommended_workorder_state: `observe_pending_next_flush`
- runtime_effect: `False`
- raw_suppression_enabled: `False`

## 근거

- raw_size_bytes: `2370312463`
- raw_storage_size_bytes: `2370312463`
- raw_line_count: `283384`
- high_volume_line_count: `250472`
- high_volume_byte_share_pct: `78.94`
- producer_summary_exists: `True`
- producer_manifest_mode: `shadow`
- parity_ok: `False`
- raw_derived_event_count: `250472`
- producer_event_count: `249858`
- producer_start_complete: `True`
- producer_pending_flush: `True`
- common_watermark_ok: `False`
- comparison_watermark: `2026-08-27T19:59:00`
- raw_tail_excluded_event_count: `415`
- coverage raw/producer: `2026-08-27T08:03:15.521273` / `2026-08-27T08:03:15`
- previous_parity_pass_count: `0`

## 금지선

- 이 report는 diagnostic aggregation이며 threshold/provider/order/bot restart 권한이 없다.
- `suppress_candidate`도 기본 OFF 설계 후보일 뿐 즉시 raw suppression 적용 근거가 아니다.

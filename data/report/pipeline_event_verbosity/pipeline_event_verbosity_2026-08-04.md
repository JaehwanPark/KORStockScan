# Pipeline Event Verbosity 2026-08-04

## 판정

- state: `v2_shadow_pending_flush`
- recommended_workorder_state: `observe_pending_next_flush`
- runtime_effect: `False`
- raw_suppression_enabled: `False`

## 근거

- raw_size_bytes: `3677299443`
- raw_storage_size_bytes: `3677299443`
- raw_line_count: `540745`
- high_volume_line_count: `496144`
- high_volume_byte_share_pct: `85.35`
- producer_summary_exists: `True`
- producer_manifest_mode: `shadow`
- parity_ok: `False`
- raw_derived_event_count: `496144`
- producer_event_count: `495028`
- producer_start_complete: `True`
- producer_pending_flush: `True`
- coverage raw/producer: `2026-08-04T07:55:22.029981` / `2026-08-04T07:55:22`
- previous_parity_pass_count: `0`

## 금지선

- 이 report는 diagnostic aggregation이며 threshold/provider/order/bot restart 권한이 없다.
- `suppress_candidate`도 기본 OFF 설계 후보일 뿐 즉시 raw suppression 적용 근거가 아니다.

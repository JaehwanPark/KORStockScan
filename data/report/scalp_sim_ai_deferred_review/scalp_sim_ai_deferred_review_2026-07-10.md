# Scalp Sim AI Deferred Review 2026-07-10

- generated_at: `2026-07-11T12:58:21`
- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-10.jsonl`
- artifact_role: `postclose_source_packet_for_sim_ai_quality_review`
- runtime_effect: `false`
- decision_authority: `sim_observation_only`
- deferred_count: `4`

## Defer Reasons

- `sim_ai_budget_exhausted`: `4`

## Critical Classes

- `soft_critical`: `4`

## Critical Reasons

- `feature_signature_changed`: `4`
- `legacy_critical_zone`: `4`
- `near_safe_profit_band`: `1`
- `soft_loss`: `3`

## Deferred Rows

| time | stock | reason | critical_class | critical_reason | profit | peak | drawdown | held_sec |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| 2026-07-10T09:45:05.142270 | LG씨엔에스(064400) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.37 | -0.23 | 0.14 | 291 |
| 2026-07-10T09:48:52.179535 | LG씨엔에스(064400) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.37 | -0.23 | 0.14 | 518 |
| 2026-07-10T12:13:18.391759 | 비에이치아이(083650) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.13 | +0.07 | 0.2 | 2869 |
| 2026-07-10T12:13:19.139499 | LS머트리얼즈(417200) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.87 | +0.87 | 0.0 | 2679 |

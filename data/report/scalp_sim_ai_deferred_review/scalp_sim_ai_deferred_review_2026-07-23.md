# Scalp Sim AI Deferred Review 2026-07-23

- generated_at: `2026-07-23T20:25:57`
- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-23.jsonl`
- artifact_role: `postclose_source_packet_for_sim_ai_quality_review`
- runtime_effect: `false`
- decision_authority: `sim_observation_only`
- deferred_count: `2`

## Defer Reasons

- `sim_ai_budget_exhausted`: `2`

## Critical Classes

- `soft_critical`: `2`

## Critical Reasons

- `feature_signature_changed`: `2`
- `legacy_critical_zone`: `2`
- `soft_loss`: `2`

## Deferred Rows

| time | stock | reason | critical_class | critical_reason | profit | peak | drawdown | held_sec |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| 2026-07-23T11:34:20.414092 | 카카오(035720) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | -0.23 | 0.0 | 1299 |
| 2026-07-23T11:42:30.283168 | 실리콘투(257720) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.37 | -0.37 | 0.0 | 962 |

# Scalp Sim AI Deferred Review 2026-06-29

- generated_at: `2026-06-29T20:15:23`
- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-29.jsonl`
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
- `legacy_critical_zone`: `1`

## Deferred Rows

| time | stock | reason | critical_class | critical_reason | profit | peak | drawdown | held_sec |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| 2026-06-29T08:06:10.581904 | 일신방직(003200) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.69 | +0.77 | 0.08 | 182 |
| 2026-06-29T09:08:30.161399 | 파라다이스(034230) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.37 | +2.37 | 0.0 | 327 |

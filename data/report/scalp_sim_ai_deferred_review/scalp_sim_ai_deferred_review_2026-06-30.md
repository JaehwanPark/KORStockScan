# Scalp Sim AI Deferred Review 2026-06-30

- generated_at: `2026-06-30T20:17:17`
- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-30.jsonl`
- artifact_role: `postclose_source_packet_for_sim_ai_quality_review`
- runtime_effect: `false`
- decision_authority: `sim_observation_only`
- deferred_count: `1`

## Defer Reasons

- `sim_ai_budget_exhausted`: `1`

## Critical Classes

- `soft_critical`: `1`

## Critical Reasons

- `feature_signature_changed`: `1`
- `legacy_critical_zone`: `1`

## Deferred Rows

| time | stock | reason | critical_class | critical_reason | profit | peak | drawdown | held_sec |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| 2026-06-30T10:54:35.273951 | 주성엔지니어링(036930) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.57 | +1.99 | 0.42 | 414 |

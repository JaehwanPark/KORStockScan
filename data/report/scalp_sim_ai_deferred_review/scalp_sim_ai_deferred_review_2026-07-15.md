# Scalp Sim AI Deferred Review 2026-07-15

- generated_at: `2026-07-15T20:25:47`
- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-15.jsonl`
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
- `soft_loss`: `1`

## Deferred Rows

| time | stock | reason | critical_class | critical_reason | profit | peak | drawdown | held_sec |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| 2026-07-15T11:00:18.292240 | SKC(011790) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.34 | -0.23 | 0.11 | 275 |

# Scalp Sim AI Deferred Review 2026-07-16

- generated_at: `2026-07-16T20:28:25`
- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-16.jsonl`
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
| 2026-07-16T13:22:21.049262 | 지엔씨에너지(119850) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | -0.23 | 0.0 | 5315 |

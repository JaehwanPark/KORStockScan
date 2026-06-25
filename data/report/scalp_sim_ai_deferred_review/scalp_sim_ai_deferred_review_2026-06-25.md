# Scalp Sim AI Deferred Review 2026-06-25

- generated_at: `2026-06-25T20:17:53`
- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-25.jsonl`
- artifact_role: `postclose_source_packet_for_sim_ai_quality_review`
- runtime_effect: `false`
- decision_authority: `sim_observation_only`
- deferred_count: `5`

## Defer Reasons

- `sim_ai_budget_exhausted`: `5`

## Critical Classes

- `soft_critical`: `5`

## Critical Reasons

- `feature_signature_changed`: `4`
- `legacy_critical_zone`: `5`
- `near_safe_profit_band`: `3`
- `soft_loss`: `1`

## Deferred Rows

| time | stock | reason | critical_class | critical_reason | profit | peak | drawdown | held_sec |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| 2026-06-25T08:30:28.394925 | 로킷헬스케어(376900) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.35 | +1.35 | 0.0 | 580 |
| 2026-06-25T09:40:35.169142 | SK(034730) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +1.09 | +1.09 | 0.0 | 2254 |
| 2026-06-25T09:51:47.036133 | SK(034730) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +1.09 | +1.09 | 0.0 | 2926 |
| 2026-06-25T15:40:19.260631 | 마녀공장(439090) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | -0.23 | 0.0 | 1307 |
| 2026-06-25T15:57:52.579942 | 마녀공장(439090) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +1.15 | +1.15 | 0.0 | 2360 |

# Scalp Sim AI Deferred Review 2026-07-08

- generated_at: `2026-07-08T20:17:16`
- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-08.jsonl`
- artifact_role: `postclose_source_packet_for_sim_ai_quality_review`
- runtime_effect: `false`
- decision_authority: `sim_observation_only`
- deferred_count: `10`

## Defer Reasons

- `sim_ai_budget_exhausted`: `10`

## Critical Classes

- `soft_critical`: `10`

## Critical Reasons

- `feature_signature_changed`: `10`
- `legacy_critical_zone`: `8`
- `near_safe_profit_band`: `1`
- `soft_loss`: `5`

## Deferred Rows

| time | stock | reason | critical_class | critical_reason | profit | peak | drawdown | held_sec |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| 2026-07-08T08:10:16.798778 | 한화오션(042660) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.31 | +1.31 | 0.0 | 285 |
| 2026-07-08T08:14:31.431525 | 한국콜마(161890) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | +0.58 | 0.81 | 506 |
| 2026-07-08T08:30:34.107504 | 광주신세계(037710) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | -0.23 | 0.0 | 271 |
| 2026-07-08T11:53:57.937427 | SK하이닉스(000660) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.14 | -0.14 | 0.0 | 2610 |
| 2026-07-08T11:56:43.829766 | SK하이닉스(000660) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.04 | +0.13 | 0.09 | 2776 |
| 2026-07-08T13:32:36.829768 | 흥구석유(024060) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.96 | +0.96 | 0.0 | 492 |
| 2026-07-08T14:30:47.426018 | 동국제약(086450) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.28 | -0.23 | 0.05 | 227 |
| 2026-07-08T14:34:38.017141 | 동국제약(086450) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.15 | +0.15 | 0.0 | 458 |
| 2026-07-08T16:55:13.721612 | LG전자(066570) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.43 | -0.23 | 0.2 | 835 |
| 2026-07-08T16:56:40.950842 | 큐로셀(372320) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.49 | +1.49 | 0.0 | 2075 |

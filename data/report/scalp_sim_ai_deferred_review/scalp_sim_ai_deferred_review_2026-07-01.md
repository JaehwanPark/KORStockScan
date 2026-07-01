# Scalp Sim AI Deferred Review 2026-07-01

- generated_at: `2026-07-01T20:17:48`
- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-01.jsonl`
- artifact_role: `postclose_source_packet_for_sim_ai_quality_review`
- runtime_effect: `false`
- decision_authority: `sim_observation_only`
- deferred_count: `2`

## Defer Reasons

- `sim_ai_budget_exhausted`: `2`

## Critical Classes

- `soft_critical`: `2`

## Critical Reasons

- `feature_signature_changed`: `1`
- `legacy_critical_zone`: `2`
- `near_safe_profit_band`: `1`
- `soft_loss`: `1`

## Deferred Rows

| time | stock | reason | critical_class | critical_reason | profit | peak | drawdown | held_sec |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| 2026-07-01T12:51:14.324325 | 스피어(347700) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,legacy_critical_zone` | +1.01 | +1.01 | 0.0 | 1076 |
| 2026-07-01T18:29:42.143357 | 삼성SDI(006400) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.43 | -0.23 | 0.2 | 7001 |

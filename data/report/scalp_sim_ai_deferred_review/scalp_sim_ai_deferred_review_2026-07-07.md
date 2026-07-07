# Scalp Sim AI Deferred Review 2026-07-07

- generated_at: `2026-07-07T20:15:53`
- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-07.jsonl`
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
- `soft_loss`: `2`

## Deferred Rows

| time | stock | reason | critical_class | critical_reason | profit | peak | drawdown | held_sec |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| 2026-07-07T08:20:21.660813 | 광주신세계(037710) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.03 | +0.38 | 0.41 | 147 |
| 2026-07-07T10:17:56.598145 | 글로벌텍스프리(204620) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.95 | +0.95 | 0.0 | 4049 |
| 2026-07-07T10:17:56.623774 | 금호타이어(073240) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.59 | +2.59 | 0.0 | 487 |
| 2026-07-07T15:06:09.842190 | SK오션플랜트(100090) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.37 | -0.16 | 0.21 | 1402 |

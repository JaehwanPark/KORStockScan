# Scalp Sim AI Deferred Review 2026-07-02

- generated_at: `2026-07-02T20:16:23`
- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-02.jsonl`
- artifact_role: `postclose_source_packet_for_sim_ai_quality_review`
- runtime_effect: `false`
- decision_authority: `sim_observation_only`
- deferred_count: `4`

## Defer Reasons

- `sim_ai_budget_exhausted`: `4`

## Critical Classes

- `non_critical`: `1`
- `soft_critical`: `3`

## Critical Reasons

- `feature_signature_changed`: `3`
- `legacy_critical_zone`: `3`
- `near_safe_profit_band`: `2`
- `normal_review`: `1`

## Deferred Rows

| time | stock | reason | critical_class | critical_reason | profit | peak | drawdown | held_sec |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| 2026-07-02T10:43:48.080426 | 삼성에스디에스(018260) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.70 | +1.70 | 0.0 | 9304 |
| 2026-07-02T10:43:54.184743 | NAVER(035420) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.97 | +0.97 | 0.0 | 9385 |
| 2026-07-02T14:08:12.813800 | 한화에어로스페이스(012450) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +1.06 | +1.15 | 0.09 | 1615 |
| 2026-07-02T19:47:44.896996 | NAVER(035420) | `sim_ai_budget_exhausted` | `non_critical` | `normal_review` | +0.22 | +0.22 | 0.0 | 9624 |

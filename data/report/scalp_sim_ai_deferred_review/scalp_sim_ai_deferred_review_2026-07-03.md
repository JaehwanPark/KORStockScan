# Scalp Sim AI Deferred Review 2026-07-03

- generated_at: `2026-07-03T20:17:54`
- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-03.jsonl`
- artifact_role: `postclose_source_packet_for_sim_ai_quality_review`
- runtime_effect: `false`
- decision_authority: `sim_observation_only`
- deferred_count: `11`

## Defer Reasons

- `sim_ai_budget_exhausted`: `11`

## Critical Classes

- `non_critical`: `1`
- `soft_critical`: `10`

## Critical Reasons

- `feature_signature_changed`: `9`
- `legacy_critical_zone`: `7`
- `normal_review`: `1`
- `soft_loss`: `6`

## Deferred Rows

| time | stock | reason | critical_class | critical_reason | profit | peak | drawdown | held_sec |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| 2026-07-03T11:20:12.726650 | 마키나락스(477850) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.47 | +0.01 | 0.48 | 530 |
| 2026-07-03T11:20:34.484015 | 이수화학(005950) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.16 | -0.16 | 0.0 | 242 |
| 2026-07-03T11:24:29.353777 | 이수화학(005950) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.16 | +0.12 | 0.28 | 477 |
| 2026-07-03T11:26:33.104739 | 이수화학(005950) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.69 | +0.76 | 0.07 | 601 |
| 2026-07-03T11:30:24.391451 | 이수화학(005950) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.02 | +0.76 | 0.78 | 832 |
| 2026-07-03T11:30:53.765233 | 이수화학(005950) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,legacy_critical_zone` | -0.02 | +0.76 | 0.78 | 861 |
| 2026-07-03T11:36:27.632338 | 마키나락스(477850) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.23 | +0.01 | 0.24 | 1504 |
| 2026-07-03T11:37:02.213237 | 이수화학(005950) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.34 | +0.76 | 0.42 | 1230 |
| 2026-07-03T11:53:50.007162 | 이수화학(005950) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.40 | +1.40 | 0.0 | 2238 |
| 2026-07-03T14:45:57.815377 | 미래에셋증권(006800) | `sim_ai_budget_exhausted` | `non_critical` | `normal_review` | +0.36 | +0.36 | 0.0 | 3486 |
| 2026-07-03T15:06:41.969059 | 미래에셋증권(006800) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed` | +0.01 | +0.36 | 0.35 | 4730 |
